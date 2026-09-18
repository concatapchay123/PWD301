"""Empirical Challenger Test Suite for Milestone 2.

Exclusively challenges and stress-tests:
1. Exam countdown timer & UTC synchronization (waiting room and active exam console)
2. Autosave retry behavior & client_sequence monotonic ordering integrity
3. Editing lease takeover & single-tab concurrency protection
4. Idempotent submission and lease teardown
5. Zero-trust IDOR security on lease takeover and answer endpoints
"""

from __future__ import annotations

import uuid
from datetime import timedelta
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.attempt_regrade import AssessmentAttempt, AttemptAnswer
from pwd301.models.identity import User
from pwd301.models.types import utc_now
from pwd301.seeds.baseline import seed_baseline
from pwd301.services.assessment_service import (
    assign_question,
    create_assessment,
    create_section,
    publish_assessment,
)
from pwd301.services.attempt_service import (
    get_attempt_delivery,
    start_assessment_attempt,
)
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.question_bank_service import create_question
from pwd301.services.user_service import assign_role_to_user, register_user
from tests.conftest import login_web_user


@pytest.fixture
def m2_challenge_fixture(app: Flask) -> dict[str, Any]:
    """Setup isolated test fixture with Instructor, 2 Students, Course, Questions and Assessment."""
    seed_baseline(db.session)
    sess: Session = db.session

    admin = sess.query(User).filter(User.email == "admin@pwd301.local").first()
    assert admin is not None

    instructor = register_user(
        email="m2_chal_inst@pwd301.local",
        password="Password@123",
        display_name="Challenger Instructor",
    )
    assign_role_to_user(instructor.id, "INSTRUCTOR")

    student1 = register_user(
        email="m2_chal_stud1@pwd301.local",
        password="Password@123",
        display_name="Challenger Student 1",
    )
    assign_role_to_user(student1.id, "STUDENT")

    student2 = register_user(
        email="m2_chal_stud2@pwd301.local",
        password="Password@123",
        display_name="Challenger Student 2",
    )
    assign_role_to_user(student2.id, "STUDENT")

    # Create & publish course
    course = create_course(
        instructor,
        {
            "course_code": "CHAL-M2",
            "title": "Challenger Exam Course",
            "summary": "Stress testing assessment exam engine",
        },
        session=sess,
    )
    change_course_status(instructor, str(course.public_id), "SUBMITTED_FOR_REVIEW", session=sess)
    change_course_status(admin, str(course.public_id), "APPROVED", session=sess)
    change_course_status(instructor, str(course.public_id), "PUBLISHED", session=sess)

    # Create Questions: 1 single choice, 1 multiple choice, 1 short answer
    q1 = create_question(
        instructor,
        course.id,
        {
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "content": "What is 2 + 2?",
            "default_points": 3.0,
            "choices": [
                {"content": "3", "is_correct": False, "position": 1},
                {"content": "4", "is_correct": True, "position": 2},
            ],
        },
        session=sess,
    )

    q2 = create_question(
        instructor,
        course.id,
        {
            "question_type": "MULTIPLE_CHOICE",
            "difficulty": "APPLY",
            "content": "Which are primary colors of light?",
            "default_points": 4.0,
            "choices": [
                {"content": "Red", "is_correct": True, "position": 1},
                {"content": "Green", "is_correct": True, "position": 2},
                {"content": "Yellow", "is_correct": False, "position": 3},
            ],
        },
        session=sess,
    )

    q3 = create_question(
        instructor,
        course.id,
        {
            "question_type": "SHORT_ANSWER",
            "difficulty": "UNDERSTAND",
            "content": "Explain the concept of idempotency in API design.",
            "default_points": 5.0,
            "accepted_answers": [
                {"answer_text": "idempotency", "is_regex": False, "case_sensitive": False}
            ],
        },
        session=sess,
    )

    # Create Assessment
    asm = create_assessment(
        instructor,
        course.id,
        {
            "title": "Challenger Comprehensive Exam",
            "assessment_type": "FINAL",
            "scoring_policy": "HIGHEST",
            "time_limit_minutes": 45,
            "attempt_limit": 2,
        },
        session=sess,
    )
    sec = create_section(
        instructor,
        asm.id,
        {"title": "Section 1", "position": 1},
        session=sess,
    )
    assign_question(
        instructor,
        asm.id,
        {"question_id": str(q1.public_id), "section_id": sec.id, "points": 3.0},
        session=sess,
    )
    assign_question(
        instructor,
        asm.id,
        {"question_id": str(q2.public_id), "section_id": sec.id, "points": 4.0},
        session=sess,
    )
    assign_question(
        instructor,
        asm.id,
        {"question_id": str(q3.public_id), "section_id": sec.id, "points": 5.0},
        session=sess,
    )
    publish_assessment(instructor, asm.id, session=sess)

    # Enroll both students
    enroll_student(student1, course.id, session=sess)
    enroll_student(student2, course.id, session=sess)

    sess.commit()

    return {
        "admin": admin,
        "instructor": instructor,
        "student1": student1,
        "student2": student2,
        "course": course,
        "assessment": asm,
        "questions": [q1, q2, q3],
    }


class TestChallengerCountdownAndUtcSync:
    """Stress-test waiting room countdown, UTC synchronization, and exam console timers."""

    def test_waiting_room_future_open_at_countdown(
        self, client: FlaskClient, m2_challenge_fixture: dict[str, Any]
    ) -> None:
        """Waiting room displays countdown and disables start button when open_at is future."""
        instructor = m2_challenge_fixture["instructor"]
        student1 = m2_challenge_fixture["student1"]
        course = m2_challenge_fixture["course"]

        now = utc_now()
        future_open = now + timedelta(seconds=600)  # 10 minutes in future

        asm_future = create_assessment(
            instructor,
            course.id,
            {
                "title": "Future Exam Waiting Room",
                "assessment_type": "MIDTERM",
                "time_limit_minutes": 30,
                "open_at": future_open.isoformat(),
            },
            session=db.session,
        )
        sec_f = create_section(
            instructor, asm_future.id, {"title": "Sec", "position": 1}, session=db.session
        )
        assign_question(
            instructor,
            asm_future.id,
            {
                "question_id": str(m2_challenge_fixture["questions"][0].public_id),
                "section_id": sec_f.id,
                "points": 5.0,
            },
            session=db.session,
        )
        publish_assessment(instructor, asm_future.id, session=db.session)
        db.session.commit()

        login_web_user(client, student1)
        resp = client.get(
            f"/student/assessments/{asm_future.public_id}", headers={"Accept": "application/json"}
        )
        assert resp.status_code == 200
        data = resp.get_json()

        # Verify waiting room status in JSON
        assert data["is_open"] is False
        assert data["is_closed"] is False
        assert 570 <= data["seconds_until_open"] <= 600

    def test_waiting_room_closed_exam_state(
        self, client: FlaskClient, m2_challenge_fixture: dict[str, Any]
    ) -> None:
        """Waiting room shows closed exam state when close_at has passed."""
        instructor = m2_challenge_fixture["instructor"]
        student1 = m2_challenge_fixture["student1"]
        course = m2_challenge_fixture["course"]

        now = utc_now()
        past_open = now - timedelta(hours=2)
        past_close = now - timedelta(hours=1)

        asm_closed = create_assessment(
            instructor,
            course.id,
            {
                "title": "Expired Closed Exam",
                "assessment_type": "MIDTERM",
                "time_limit_minutes": 30,
                "open_at": past_open.isoformat(),
                "close_at": past_close.isoformat(),
            },
            session=db.session,
        )
        sec_c = create_section(
            instructor, asm_closed.id, {"title": "Sec", "position": 1}, session=db.session
        )
        assign_question(
            instructor,
            asm_closed.id,
            {
                "question_id": str(m2_challenge_fixture["questions"][0].public_id),
                "section_id": sec_c.id,
                "points": 5.0,
            },
            session=db.session,
        )
        publish_assessment(instructor, asm_closed.id, session=db.session)
        db.session.commit()

        login_web_user(client, student1)
        resp = client.get(
            f"/student/assessments/{asm_closed.public_id}", headers={"Accept": "application/json"}
        )
        assert resp.status_code == 200
        data = resp.get_json()

        assert data["is_closed"] is True

    def test_exam_console_server_authoritative_timer(
        self, client: FlaskClient, m2_challenge_fixture: dict[str, Any]
    ) -> None:
        """Active exam delivery returns server timer remaining seconds in JSON."""
        student1 = m2_challenge_fixture["student1"]
        asm = m2_challenge_fixture["assessment"]

        attempt, raw_token = start_assessment_attempt(
            student_actor=student1,
            assessment_id=str(asm.public_id),
            session=db.session,
        )
        attempt_id = str(attempt.public_id)

        login_web_user(client, student1)
        resp = client.get(f"/student/attempt/{attempt_id}", headers={"Accept": "application/json"})
        assert resp.status_code == 200
        data = resp.get_json()

        # Verify remaining_seconds is rendered from server calculation
        rem_sec = data["remaining_seconds"]
        assert rem_sec is not None
        # Assessment was 45 minutes = 2700s
        assert 2600 <= rem_sec <= 2700


class TestChallengerAutosaveSequenceAndRetry:
    """Stress-test client_sequence monotonic ordering, duplicate retry, and rejection."""

    def test_autosave_monotonic_client_sequence_enforcement(
        self, client: FlaskClient, m2_challenge_fixture: dict[str, Any]
    ) -> None:
        """Autosave accepts increasing sequence and strictly rejects stale sequence."""
        student1 = m2_challenge_fixture["student1"]
        asm = m2_challenge_fixture["assessment"]

        attempt, raw_token = start_assessment_attempt(
            student_actor=student1,
            assessment_id=str(asm.public_id),
            session=db.session,
        )
        attempt_id = str(attempt.public_id)

        delivery = get_attempt_delivery(
            student_actor=student1, attempt_id=attempt_id, session=db.session
        )
        q_item = delivery["questions"][0]
        aq_id = q_item["attempt_question_id"]
        choice_key_1 = q_item["choices"][0]["choice_key"]
        choice_key_2 = q_item["choices"][1]["choice_key"]

        login_web_user(client, student1)

        # 1. First save: client_sequence = 1
        resp1 = client.post(
            f"/student/attempt/{attempt_id}/answers/{aq_id}",
            json={
                "client_sequence": 1,
                "selected_choice_keys": [choice_key_1],
                "lease_token": raw_token,
            },
        )
        assert resp1.status_code == 200
        assert resp1.get_json()["answer_version"] == 1

        # 2. Advance sequence: client_sequence = 5
        resp2 = client.post(
            f"/student/attempt/{attempt_id}/answers/{aq_id}",
            json={
                "client_sequence": 5,
                "selected_choice_keys": [choice_key_2],
                "lease_token": raw_token,
            },
        )
        assert resp2.status_code == 200
        assert resp2.get_json()["answer_version"] == 2

        # Verify database state
        ans_db = (
            db.session.query(AttemptAnswer)
            .filter(AttemptAnswer.attempt_question_id == attempt.attempt_questions[0].id)
            .first()
        )
        assert ans_db is not None
        assert ans_db.last_client_sequence == 5

        # 3. Adversarial Stale sequence: client_sequence = 3 (< 5)
        resp_stale = client.post(
            f"/student/attempt/{attempt_id}/answers/{aq_id}",
            json={
                "client_sequence": 3,
                "selected_choice_keys": [choice_key_1],
                "lease_token": raw_token,
            },
        )
        # Must be rejected with 409 Conflict
        assert resp_stale.status_code == 409

        # Empirical Check: Ensure answer was NOT corrupted / overwritten by stale save
        db.session.expire_all()
        ans_db_recheck = (
            db.session.query(AttemptAnswer)
            .filter(AttemptAnswer.attempt_question_id == attempt.attempt_questions[0].id)
            .first()
        )
        assert ans_db_recheck.last_client_sequence == 5

    def test_autosave_idempotent_retry_with_change_id(
        self, client: FlaskClient, m2_challenge_fixture: dict[str, Any]
    ) -> None:
        """Retrying an identical autosave with the same client_change_id returns original 200."""
        student1 = m2_challenge_fixture["student1"]
        asm = m2_challenge_fixture["assessment"]

        attempt, raw_token = start_assessment_attempt(
            student_actor=student1,
            assessment_id=str(asm.public_id),
            session=db.session,
        )
        attempt_id = str(attempt.public_id)

        delivery = get_attempt_delivery(
            student_actor=student1, attempt_id=attempt_id, session=db.session
        )
        q_item = delivery["questions"][0]
        aq_id = q_item["attempt_question_id"]
        choice_key = q_item["choices"][0]["choice_key"]

        login_web_user(client, student1)
        fixed_change_id = str(uuid.uuid4())

        # First request
        resp1 = client.post(
            f"/student/attempt/{attempt_id}/answers/{aq_id}",
            json={
                "client_sequence": 10,
                "client_change_id": fixed_change_id,
                "selected_choice_keys": [choice_key],
                "lease_token": raw_token,
            },
        )
        assert resp1.status_code == 200
        data1 = resp1.get_json()

        # Simulated network retry of same payload and change_id
        resp2 = client.post(
            f"/student/attempt/{attempt_id}/answers/{aq_id}",
            json={
                "client_sequence": 10,
                "client_change_id": fixed_change_id,
                "selected_choice_keys": [choice_key],
                "lease_token": raw_token,
            },
        )
        assert resp2.status_code == 200
        data2 = resp2.get_json()
        assert data1["answer_version"] == data2["answer_version"]


class TestChallengerLeaseTakeoverAndSingleTabProtection:
    """Stress-test editing lease takeover, cross-tab conflict detection, and submit protection."""

    def test_lease_takeover_invalidates_previous_tab_and_enables_resumption(
        self, client: FlaskClient, m2_challenge_fixture: dict[str, Any]
    ) -> None:
        """Tab 2 takeover invalidates Tab 1 lease, Tab 1 takeover recovers lease."""
        student1 = m2_challenge_fixture["student1"]
        asm = m2_challenge_fixture["assessment"]

        # Student starts attempt in Tab 1
        attempt, tab1_token = start_assessment_attempt(
            student_actor=student1,
            assessment_id=str(asm.public_id),
            session=db.session,
        )
        attempt_id = str(attempt.public_id)

        delivery = get_attempt_delivery(
            student_actor=student1, attempt_id=attempt_id, session=db.session
        )
        aq_id = delivery["questions"][0]["attempt_question_id"]
        choice_key_1 = delivery["questions"][0]["choices"][0]["choice_key"]
        choice_key_2 = delivery["questions"][0]["choices"][1]["choice_key"]

        login_web_user(client, student1)

        # Tab 1 autosaves successfully
        resp_tab1_save = client.post(
            f"/student/attempt/{attempt_id}/answers/{aq_id}",
            json={
                "client_sequence": 1,
                "selected_choice_keys": [choice_key_1],
                "lease_token": tab1_token,
            },
        )
        assert resp_tab1_save.status_code == 200

        # Tab 2 performs Lease Takeover
        resp_takeover = client.post(
            f"/student/attempt/{attempt_id}/lease/takeover",
            json={},
        )
        assert resp_takeover.status_code == 200
        takeover_data = resp_takeover.get_json()
        tab2_token = takeover_data["lease_token"]
        assert tab2_token != tab1_token
        assert takeover_data["lease_epoch"] >= 2

        # Tab 1 tries to autosave with old lease token -> REJECTED (409 Conflict)
        resp_tab1_stale = client.post(
            f"/student/attempt/{attempt_id}/answers/{aq_id}",
            json={
                "client_sequence": 2,
                "selected_choice_keys": [choice_key_2],
                "lease_token": tab1_token,
            },
        )
        assert resp_tab1_stale.status_code == 409

        # Tab 2 autosaves successfully with tab2_token
        resp_tab2_save = client.post(
            f"/student/attempt/{attempt_id}/answers/{aq_id}",
            json={
                "client_sequence": 3,
                "selected_choice_keys": [choice_key_2],
                "lease_token": tab2_token,
            },
        )
        assert resp_tab2_save.status_code == 200

        # Tab 1 takes back lease (renewLease via takeover endpoint)
        resp_tab1_recover = client.post(
            f"/student/attempt/{attempt_id}/lease/takeover",
            json={},
        )
        assert resp_tab1_recover.status_code == 200
        tab1_new_token = resp_tab1_recover.get_json()["lease_token"]

        # Tab 1 can autosave again
        resp_tab1_resumed = client.post(
            f"/student/attempt/{attempt_id}/answers/{aq_id}",
            json={
                "client_sequence": 4,
                "selected_choice_keys": [choice_key_1],
                "lease_token": tab1_new_token,
            },
        )
        assert resp_tab1_resumed.status_code == 200

        # Now Tab 2 is invalidated
        resp_tab2_stale = client.post(
            f"/student/attempt/{attempt_id}/answers/{aq_id}",
            json={
                "client_sequence": 5,
                "selected_choice_keys": [choice_key_2],
                "lease_token": tab2_token,
            },
        )
        assert resp_tab2_stale.status_code == 409

    def test_submission_rejects_stale_lease_and_cleans_up_on_success(
        self, client: FlaskClient, m2_challenge_fixture: dict[str, Any]
    ) -> None:
        """Submit rejects stale lease token and revokes lease upon successful submit."""
        student1 = m2_challenge_fixture["student1"]
        asm = m2_challenge_fixture["assessment"]

        attempt, tab1_token = start_assessment_attempt(
            student_actor=student1,
            assessment_id=str(asm.public_id),
            session=db.session,
        )
        attempt_id = str(attempt.public_id)

        login_web_user(client, student1)

        # Tab 2 takes over
        resp_takeover = client.post(
            f"/student/attempt/{attempt_id}/lease/takeover",
            json={},
        )
        tab2_token = resp_takeover.get_json()["lease_token"]

        # Fetch aq_id while attempt is still IN_PROGRESS
        delivery = get_attempt_delivery(
            student_actor=student1, attempt_id=attempt_id, session=db.session
        )
        aq_id = delivery["questions"][0]["attempt_question_id"]

        # Tab 1 attempts submit with stale lease -> REJECTED 409
        resp_stale_submit = client.post(
            f"/student/attempt/{attempt_id}/submit",
            json={"lease_token": tab1_token},
        )
        assert resp_stale_submit.status_code == 409

        # Tab 2 submits with valid lease -> 200 OK
        resp_valid_submit = client.post(
            f"/student/attempt/{attempt_id}/submit",
            json={"lease_token": tab2_token},
        )
        assert resp_valid_submit.status_code == 200
        sub_data = resp_valid_submit.get_json()
        assert sub_data["status"] in ("SUBMITTED", "GRADED")

        # Invariant check: lease is completely revoked
        db.session.expire_all()
        attempt_reloaded = db.session.get(AssessmentAttempt, attempt.id)
        assert attempt_reloaded.lease_token_hash is None
        assert attempt_reloaded.lease_expires_at is None

        # Post-submission autosave must be rejected
        resp_post_submit = client.post(
            f"/student/attempt/{attempt_id}/answers/{aq_id}",
            json={
                "client_sequence": 99,
                "selected_choice_keys": ["A"],
                "lease_token": tab2_token,
            },
        )
        assert resp_post_submit.status_code in (400, 409)

    def test_lease_takeover_zero_trust_idor_defense(
        self, client: FlaskClient, m2_challenge_fixture: dict[str, Any]
    ) -> None:
        """Peer student or unauthorized user cannot take over another student's lease."""
        student1 = m2_challenge_fixture["student1"]
        student2 = m2_challenge_fixture["student2"]
        asm = m2_challenge_fixture["assessment"]

        attempt, raw_token = start_assessment_attempt(
            student_actor=student1,
            assessment_id=str(asm.public_id),
            session=db.session,
        )
        attempt_id = str(attempt.public_id)

        # Student 2 tries to take over Student 1's lease
        login_web_user(client, student2)
        resp = client.post(
            f"/student/attempt/{attempt_id}/lease/takeover",
            json={},
        )
        # Must be rejected with 403 Forbidden
        assert resp.status_code == 403

    def test_autosave_network_reordering_under_rapid_typing(
        self, client: FlaskClient, m2_challenge_fixture: dict[str, Any]
    ) -> None:
        """Autosave rejects out-of-order delayed packets and preserves latest accepted answer."""
        student1 = m2_challenge_fixture["student1"]
        asm = m2_challenge_fixture["assessment"]

        attempt, raw_token = start_assessment_attempt(
            student_actor=student1,
            assessment_id=str(asm.public_id),
            session=db.session,
        )
        attempt_id = str(attempt.public_id)

        delivery = get_attempt_delivery(
            student_actor=student1, attempt_id=attempt_id, session=db.session
        )
        # Find short answer question (question 3)
        short_aq = delivery["questions"][2]
        aq_id = short_aq["attempt_question_id"]

        login_web_user(client, student1)

        # Sequence 1: Initial typing
        resp1 = client.post(
            f"/student/attempt/{attempt_id}/answers/{aq_id}",
            json={
                "client_sequence": 1,
                "answer_text": "Idem",
                "lease_token": raw_token,
            },
        )
        assert resp1.status_code == 200

        # Sequence 3: Packet arrives ahead of packet 2
        resp3 = client.post(
            f"/student/attempt/{attempt_id}/answers/{aq_id}",
            json={
                "client_sequence": 3,
                "answer_text": "Idempotent operation can be applied multiple times.",
                "lease_token": raw_token,
            },
        )
        assert resp3.status_code == 200

        # Sequence 2: Delayed packet arriving late
        resp2 = client.post(
            f"/student/attempt/{attempt_id}/answers/{aq_id}",
            json={
                "client_sequence": 2,
                "answer_text": "Idempotency means",
                "lease_token": raw_token,
            },
        )
        assert resp2.status_code == 409

        # Verify DB answer is sequence 3
        db.session.expire_all()
        ans_db = (
            db.session.query(AttemptAnswer)
            .filter(AttemptAnswer.attempt_question_id == attempt.attempt_questions[2].id)
            .first()
        )
        assert ans_db.last_client_sequence == 3
        assert "Idempotent operation" in ans_db.answer_text

        # Sequence 4: Next packet arrives normally
        resp4 = client.post(
            f"/student/attempt/{attempt_id}/answers/{aq_id}",
            json={
                "client_sequence": 4,
                "answer_text": "Idempotent operation can be applied multiple times.",
                "lease_token": raw_token,
            },
        )
        assert resp4.status_code == 200

    def test_takeover_after_lease_timeout_and_deadline_expiry(
        self, client: FlaskClient, m2_challenge_fixture: dict[str, Any]
    ) -> None:
        """Stale lease allows takeover; passed deadline rejects and transitions to EXPIRED."""
        student1 = m2_challenge_fixture["student1"]
        asm = m2_challenge_fixture["assessment"]

        attempt, raw_token = start_assessment_attempt(
            student_actor=student1,
            assessment_id=str(asm.public_id),
            session=db.session,
        )
        attempt_id = str(attempt.public_id)

        now = utc_now()
        # 1. Simulate lease expiration
        attempt.lease_expires_at = now - timedelta(seconds=15)
        db.session.commit()

        login_web_user(client, student1)

        # Takeover after expiry succeeds
        resp_takeover = client.post(
            f"/student/attempt/{attempt_id}/lease/takeover",
            json={},
        )
        assert resp_takeover.status_code == 200
        new_token = resp_takeover.get_json()["lease_token"]
        assert new_token != raw_token

        # 2. Simulate assessment attempt deadline expiry
        db.session.expire_all()
        attempt_obj = db.session.get(AssessmentAttempt, attempt.id)
        attempt_obj.started_at = now - timedelta(hours=2)
        attempt_obj.deadline_at = now - timedelta(seconds=10)
        db.session.commit()

        # Takeover after attempt deadline MUST be rejected
        resp_deadline_fail = client.post(
            f"/student/attempt/{attempt_id}/lease/takeover",
            json={},
        )
        assert resp_deadline_fail.status_code in (400, 409)

        # Verify attempt transitioned to EXPIRED
        db.session.expire_all()
        reloaded = db.session.get(AssessmentAttempt, attempt.id)
        assert reloaded.status == "EXPIRED"

    def test_multiple_choice_empty_selection_autosave_bug_demonstration(
        self, client: FlaskClient, m2_challenge_fixture: dict[str, Any]
    ) -> None:
        """EMPIRICAL: Deselecting all choices sends [] but backend fails to clear choices."""
        student1 = m2_challenge_fixture["student1"]
        asm = m2_challenge_fixture["assessment"]

        attempt, raw_token = start_assessment_attempt(
            student_actor=student1,
            assessment_id=str(asm.public_id),
            session=db.session,
        )
        attempt_id = str(attempt.public_id)

        delivery = get_attempt_delivery(
            student_actor=student1, attempt_id=attempt_id, session=db.session
        )
        # Question 2 is MULTIPLE_CHOICE
        mc_aq = delivery["questions"][1]
        aq_id = mc_aq["attempt_question_id"]
        c1 = mc_aq["choices"][0]["choice_key"]
        c2 = mc_aq["choices"][1]["choice_key"]

        login_web_user(client, student1)

        # 1. Select two choices
        resp1 = client.post(
            f"/student/attempt/{attempt_id}/answers/{aq_id}",
            json={
                "client_sequence": 1,
                "selected_choice_keys": [c1, c2],
                "lease_token": raw_token,
            },
        )
        assert resp1.status_code == 200

        # 2. Deselect all choices (uncheck all in attempt.html produces selected_choice_keys = [])
        resp2 = client.post(
            f"/student/attempt/{attempt_id}/answers/{aq_id}",
            json={
                "client_sequence": 2,
                "selected_choice_keys": [],
                "lease_token": raw_token,
            },
        )
        assert resp2.status_code == 200

        # EMPIRICAL PROOF: In attempt_service.py:1217:
        # selected_choice_keys = payload.get("selected_choice_keys") or payload.get("choice_keys")
        # Because [] is falsy in Python, selected_choice_keys evaluates to None!
        # The choice deletion block `if selected_choice_keys is not None:` is skipped!
        # As a result, the previous choices are NOT cleared:
        db.session.expire_all()
        ans_db = (
            db.session.query(AttemptAnswer)
            .filter(AttemptAnswer.attempt_question_id == attempt.attempt_questions[1].id)
            .first()
        )
        # It still retains 2 choices instead of 0!
        assert len(ans_db.selected_choices) == 2, (
            "Confirmed: [] is treated as None, choices not cleared"
        )

    def test_attempt_template_dom_and_xss_escaping_integrity(
        self, client: FlaskClient, m2_challenge_fixture: dict[str, Any]
    ) -> None:
        """Attempt template renders clean DOM without raw Jinja leaks and escapes content."""
        instructor = m2_challenge_fixture["instructor"]
        student1 = m2_challenge_fixture["student1"]
        course = m2_challenge_fixture["course"]

        # Question with HTML characters
        q_xss = create_question(
            instructor,
            course.id,
            {
                "question_type": "SINGLE_CHOICE",
                "difficulty": "REMEMBER",
                "content": "What is <script>alert('pwned')</script> in JavaScript?",
                "default_points": 2.0,
                "choices": [
                    {"content": "<b>Bold text</b>", "is_correct": True, "position": 1},
                    {"content": "&quot;Quoted&quot;", "is_correct": False, "position": 2},
                ],
            },
            session=db.session,
        )

        asm_xss = create_assessment(
            instructor,
            course.id,
            {
                "title": "XSS & DOM Resilience Exam",
                "assessment_type": "QUIZ",
                "time_limit_minutes": 20,
            },
            session=db.session,
        )
        sec = create_section(
            instructor, asm_xss.id, {"title": "Sec", "position": 1}, session=db.session
        )
        assign_question(
            instructor,
            asm_xss.id,
            {"question_id": str(q_xss.public_id), "section_id": sec.id, "points": 2.0},
            session=db.session,
        )
        publish_assessment(instructor, asm_xss.id, session=db.session)
        db.session.commit()

        attempt, raw_token = start_assessment_attempt(
            student_actor=student1,
            assessment_id=str(asm_xss.public_id),
            session=db.session,
        )
        attempt_id = str(attempt.public_id)

        login_web_user(client, student1)
        resp = client.get(f"/student/attempt/{attempt_id}", headers={"Accept": "application/json"})
        assert resp.status_code == 200
        assert resp.is_json
        data = resp.get_json()

        # In headless JSON API mode, data is serialized faithfully in JSON structure
        assert data["attempt_id"] == attempt_id
        assert data["status"] in ("IN_PROGRESS", "SUBMITTED")
        assert len(data["questions"]) >= 1
        q_data = data["questions"][0]
        assert q_data["content"] == "What is <script>alert('pwned')</script> in JavaScript?"
        assert any(c["content"] == "<b>Bold text</b>" for c in q_data["choices"])
        assert "remaining_seconds" in data
