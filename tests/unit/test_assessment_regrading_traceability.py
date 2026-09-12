"""Canonical Comprehensive Traceability Test Suite for Assessment & Regrading Engine.

Strictly validates the specification:
- Section 6.1: Data Integrity & Invariants
  (published_at lock, first_attempt lock, student evidence immutability, zero leakage)
- Section 6.2: Concurrency Criteria
  (multi-tab race, takeover race, offline replay race, concurrent submit race)
- Section 6.3: Normative Test Matrix:
  - T-QB-02 to T-QB-05: Question branching, choice scoping, type lock, permanent retention
  - T-ASSESS-01 to T-ASSESS-06: Timing lock, structure lock, points lock, blueprint shortage,
    revision snapshot isolation, shuffle stability
  - T-ATT-01 to T-ATT-07: Attempt limits, deadline clamping, lease conflict, takeover recovery,
    autosave ack, deadline rejection, submit idempotency
  - T-GRADE-01 to T-GRADE-04: Exact-set no partial credit, short answer normalization,
    essay pending status, manual grade history
  - T-REG-01 to T-REG-04: ANSWER_ONLY regrade, CONTENT_OR_CHOICES full credit,
    evidence immutability, resumable crash recovery
"""

from __future__ import annotations

import datetime
import uuid
from decimal import Decimal
from typing import Any

import pytest
from flask import Flask
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.attempt_regrade import (
    AssessmentResult,
    AssessmentResultHistory,
    AttemptAnswer,
    AttemptQuestionGrade,
    AttemptQuestionGradeHistory,
)
from pwd301.models.course import Course
from pwd301.models.identity import Role, User
from pwd301.models.question_bank import (
    Question,
)
from pwd301.models.types import utc_now
from pwd301.services.assessment_service import (
    assign_question,
    configure_blueprint,
    create_assessment,
    create_section,
    publish_assessment,
    remove_question_assignment,
    update_assessment,
    update_question_assignment,
)
from pwd301.services.attempt_service import (
    get_attempt_delivery,
    grade_essay_question,
    save_attempt_answer,
    start_assessment_attempt,
    submit_assessment_attempt,
    takeover_attempt_lease,
)
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.exceptions import (
    AssessmentLockedError,
    AttemptExpiredError,
    AttemptLeaseConflictError,
    AttemptLimitExceededError,
    BlueprintValidationError,
    QuestionImmutableError,
    QuestionStateViolationError,
    StaleAnswerSequenceError,
    SubmissionIdempotencyConflictError,
)
from pwd301.services.question_bank_service import (
    create_question,
    create_question_revision,
    trash_question,
    update_question,
)
from pwd301.services.regrade_worker import (
    create_or_get_regrade_job,
    process_regrade_job,
)
from pwd301.services.user_service import assign_role_to_user, register_user

# ============================================================================
# FIXTURES & TEST DATA SETUP
# ============================================================================


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
    """Ensure standard roles exist in test database."""
    sess: Session = db.session
    role_map: dict[str, Role] = {}
    for code, name in [
        ("STUDENT", "Student"),
        ("INSTRUCTOR", "Instructor"),
        ("ADMIN", "System Administrator"),
    ]:
        role = sess.query(Role).filter(Role.code == code).first()
        if role is None:
            role = Role(code=code, name=name)
            sess.add(role)
            sess.flush()
        role_map[code] = role
    sess.commit()
    return role_map


@pytest.fixture
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create a primary instructor."""
    u = register_user("trace_asm_inst@example.com", "Password@123", "Trace Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create an administrator."""
    u = register_user("trace_asm_admin@example.com", "Password@123", "Trace Admin")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def student_one(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create primary student."""
    return register_user("trace_asm_stud1@example.com", "Password@123", "Trace Student 1")


@pytest.fixture
def student_two(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create secondary student."""
    return register_user("trace_asm_stud2@example.com", "Password@123", "Trace Student 2")


@pytest.fixture
def active_course(app: Flask, instructor_user: User, admin_user: User) -> Course:
    """Create and publish an active course."""
    sess: Session = db.session
    c = create_course(
        instructor_user,
        {
            "course_code": f"ASM-TRC-{int(utc_now().timestamp()) % 100000}",
            "title": "Assessment Architecture Traceability Course",
            "summary": "Full engine traceability",
        },
        session=sess,
    )
    change_course_status(instructor_user, c.id, "SUBMITTED_FOR_REVIEW", session=sess)
    change_course_status(admin_user, c.id, "APPROVED", session=sess)
    change_course_status(instructor_user, c.id, "PUBLISHED", session=sess)
    sess.commit()
    return c


@pytest.fixture
def enrolled_students(
    app: Flask, active_course: Course, student_one: User, student_two: User
) -> tuple[User, User]:
    """Enroll both students in active course."""
    sess: Session = db.session
    enroll_student(student_one, active_course.id, session=sess)
    enroll_student(student_two, active_course.id, session=sess)
    sess.commit()
    return student_one, student_two


# ============================================================================
# 6.1 TIÊU CHÍ ĐÁNH GIÁ TÍNH TOÀN VẸN DỮ LIỆU & BẤT BIẾN (DATA INTEGRITY)
# ============================================================================


def test_6_1_published_at_timing_freeze_marker(
    app: Flask, instructor_user: User, active_course: Course
) -> None:
    """6.1.1: Marker published_at freezes timing configuration.

    Updating open_at, time_limit_minutes, or shortening close_at on a PUBLISHED
    assessment raises AssessmentLockedError.
    """
    sess: Session = db.session
    now = utc_now()

    q = create_question(
        instructor_user,
        active_course.id,
        {
            "content": "Sample Question 1",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "default_points": 2.0,
            "choices": [
                {"content": "A", "is_correct": True, "position": 1},
                {"content": "B", "is_correct": False, "position": 2},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    sess.commit()

    asm = create_assessment(
        instructor_user,
        active_course.id,
        {
            "title": "Timing Lock Assessment",
            "assessment_type": "QUIZ",
            "time_limit_minutes": 30,
            "open_at": (now + datetime.timedelta(hours=1)).isoformat(),
            "close_at": (now + datetime.timedelta(hours=5)).isoformat(),
        },
        session=sess,
    )
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": str(q.public_id), "points": 10.0},
        session=sess,
    )
    publish_assessment(instructor_user, asm.id, session=sess)

    assert asm.status == "PUBLISHED"
    assert asm.published_at is not None

    # Modifying open_at must fail
    with pytest.raises(AssessmentLockedError, match="open_at.*locked"):
        update_assessment(
            instructor_user,
            asm.id,
            {"open_at": (now + datetime.timedelta(hours=2)).isoformat()},
            session=sess,
        )

    # Modifying time_limit_minutes must fail
    with pytest.raises(AssessmentLockedError, match="time_limit_minutes.*locked"):
        update_assessment(
            instructor_user,
            asm.id,
            {"time_limit_minutes": 45},
            session=sess,
        )

    # Shortening close_at must fail
    with pytest.raises(AssessmentLockedError, match="close_at can only be extended forward"):
        update_assessment(
            instructor_user,
            asm.id,
            {"close_at": (now + datetime.timedelta(hours=4)).isoformat()},
            session=sess,
        )

    # Modifying via alias duration_minutes must fail
    with pytest.raises(AssessmentLockedError, match="time_limit_minutes.*locked"):
        update_assessment(
            instructor_user,
            asm.id,
            {"duration_minutes": 45},
            session=sess,
        )

    # Modifying via alias max_attempts must fail
    with pytest.raises(AssessmentLockedError, match="attempt_limit.*locked"):
        update_assessment(
            instructor_user,
            asm.id,
            {"max_attempts": 5},
            session=sess,
        )

    # Nullifying close_at on published assessment must fail
    with pytest.raises(AssessmentLockedError, match="close_at can only be extended forward"):
        update_assessment(
            instructor_user,
            asm.id,
            {"close_at": None},
            session=sess,
        )


def test_6_1_first_attempt_started_at_structure_freeze_marker(
    app: Flask,
    instructor_user: User,
    active_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """6.1.2: Marker first_attempt_started_at freezes structure and point assignments.

    Adding, removing, or re-pointing questions after the first attempt starts
    is rejected with AssessmentLockedError.
    """
    sess: Session = db.session
    student1, _ = enrolled_students

    q1 = create_question(
        instructor_user,
        active_course.id,
        {
            "content": "Freeze Test Question 1",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "default_points": 5.0,
            "choices": [
                {"content": "Yes", "is_correct": True, "position": 1},
                {"content": "No", "is_correct": False, "position": 2},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    q2 = create_question(
        instructor_user,
        active_course.id,
        {
            "content": "Freeze Test Question 2",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "APPLY",
            "default_points": 5.0,
            "choices": [
                {"content": "True", "is_correct": True, "position": 1},
                {"content": "False", "is_correct": False, "position": 2},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    sess.commit()

    asm = create_assessment(
        instructor_user,
        active_course.id,
        {"title": "Structure Freeze Exam", "assessment_type": "MIDTERM", "time_limit_minutes": 60},
        session=sess,
    )
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": str(q1.public_id), "points": 10.0},
        session=sess,
    )
    publish_assessment(instructor_user, asm.id, session=sess)

    # Student 1 starts first attempt
    attempt, _ = start_assessment_attempt(student1, asm.id, session=sess)
    sess.refresh(asm)

    assert asm.first_attempt_started_at is not None

    # 1. Attempting to assign new question after attempt starts must fail
    with pytest.raises(AssessmentLockedError, match="cannot be modified after student attempt"):
        assign_question(
            instructor_user,
            asm.id,
            {"question_id": str(q2.public_id), "points": 5.0},
            session=sess,
        )

    # 2. Attempting to remove assigned question must fail
    with pytest.raises(AssessmentLockedError, match="cannot be removed after student attempt"):
        remove_question_assignment(instructor_user, asm.id, q1.id, session=sess)

    # 3. Attempting to add section must fail
    with pytest.raises(AssessmentLockedError, match="cannot be added after student attempt"):
        create_section(instructor_user, asm.id, {"title": "Part 2"}, session=sess)

    # 4. Attempting to modify points on assigned question must fail (ASSESS-003)
    with pytest.raises(
        AssessmentLockedError, match="points cannot be modified after student attempt"
    ):
        update_question_assignment(
            instructor_user,
            asm.id,
            q1.id,
            {"points": 20.0},
            session=sess,
        )


def test_6_1_student_historical_evidence_immutability(
    app: Flask,
    instructor_user: User,
    active_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """6.1.3: Historical student attempt snapshot and answer evidence is 100% immutable.

    When a question correction is processed via background regrading, AttemptQuestion,
    AttemptChoiceSnapshot, and AttemptAnswer remain identical byte-for-byte.
    """
    sess: Session = db.session
    student1, _ = enrolled_students

    q = create_question(
        instructor_user,
        active_course.id,
        {
            "content": "Evidence Question: What is 5 x 5?",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "default_points": 10.0,
            "choices": [
                {"content": "20", "is_correct": True, "position": 1},  # Initially flawed answer
                {"content": "25", "is_correct": False, "position": 2},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    sess.commit()

    asm = create_assessment(
        instructor_user,
        active_course.id,
        {
            "title": "Evidence Immutability Test",
            "assessment_type": "QUIZ",
            "time_limit_minutes": 30,
        },
        session=sess,
    )
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": str(q.public_id), "points": 10.0},
        session=sess,
    )
    publish_assessment(instructor_user, asm.id, session=sess)

    # Student takes attempt and selects "25" (which was initially marked wrong)
    attempt, raw_token = start_assessment_attempt(student1, asm.id, session=sess)
    aq = attempt.attempt_questions[0]
    choice_25 = next(cs for cs in aq.choice_snapshots if cs.content_snapshot == "25")

    save_attempt_answer(
        actor=student1,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        payload={
            "selected_choice_keys": [str(choice_25.choice_key_snapshot)],
            "client_sequence": 1,
            "lease_epoch": attempt.lease_epoch,
        },
        raw_lease_token=raw_token,
        session=sess,
    )
    submit_assessment_attempt(student1, attempt.id, idempotency_key=uuid.uuid4(), session=sess)

    # Record historical snapshot state before correction
    orig_aq_content = aq.content_snapshot
    orig_aq_points = aq.points_assigned
    orig_choice_contents = [cs.content_snapshot for cs in aq.choice_snapshots]
    orig_answer = sess.query(AttemptAnswer).filter_by(attempt_question_id=aq.id).first()
    orig_answer_version = orig_answer.answer_version if orig_answer else 0

    # Instructor issues correction: change correct answer to "25"
    rev2, correction = create_question_revision(
        instructor_user,
        q.id,
        {
            "content": "Evidence Question: What is 5 x 5?",
            "reason": "Fix math error in answer key",
            "correction_type": "ANSWER_ONLY",
            "choices": [
                {"content": "20", "is_correct": False, "position": 1},
                {"content": "25", "is_correct": True, "position": 2},
            ],
        },
        session=sess,
    )
    sess.commit()

    assert correction is not None
    job = create_or_get_regrade_job(correction.id, session=sess)
    process_regrade_job(job.id, actor=instructor_user, session=sess)

    # Verify attempt snapshot and answers are untouched
    sess.refresh(aq)
    assert aq.content_snapshot == orig_aq_content
    assert aq.points_assigned == orig_aq_points
    refreshed_choices = [cs.content_snapshot for cs in aq.choice_snapshots]
    assert refreshed_choices == orig_choice_contents

    refreshed_answer = sess.query(AttemptAnswer).filter_by(attempt_question_id=aq.id).first()
    assert refreshed_answer is not None
    assert refreshed_answer.answer_version == orig_answer_version

    # Verify score was updated in grades & results, but not raw attempt snapshot
    grade = sess.query(AttemptQuestionGrade).filter_by(attempt_question_id=aq.id).first()
    assert grade is not None
    assert grade.awarded_points == Decimal("10.0000")


def test_6_1_zero_is_correct_flag_leakage_in_delivery(
    app: Flask,
    instructor_user: User,
    active_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """6.1.4: Delivery payload strictly hides is_correct and explanation (Zero Leakage)."""
    sess: Session = db.session
    student1, _ = enrolled_students

    q = create_question(
        instructor_user,
        active_course.id,
        {
            "content": "Secret Question",
            "explanation": "Top secret explanation text that must never leak",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "default_points": 5.0,
            "choices": [
                {"content": "Correct Choice", "is_correct": True, "position": 1},
                {"content": "Wrong Choice", "is_correct": False, "position": 2},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    sess.commit()

    asm = create_assessment(
        instructor_user,
        active_course.id,
        {"title": "Zero Leakage Quiz", "assessment_type": "QUIZ", "time_limit_minutes": 20},
        session=sess,
    )
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": str(q.public_id), "points": 5.0},
        session=sess,
    )
    publish_assessment(instructor_user, asm.id, session=sess)

    attempt, _ = start_assessment_attempt(student1, asm.id, session=sess)
    delivery = get_attempt_delivery(student1, attempt.id, session=sess)

    def _assert_zero_leakage(node: Any) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                assert k != "is_correct", f"Secret flag 'is_correct' leaked in delivery: {node}"
                assert k != "explanation", f"Secret explanation leaked in delivery: {node}"
                assert k != "explanation_snapshot", f"Explanation snapshot leaked: {node}"
                _assert_zero_leakage(v)
        elif isinstance(node, list):
            for item in node:
                _assert_zero_leakage(item)

    _assert_zero_leakage(delivery)
    assert len(delivery["questions"]) == 1
    assert len(delivery["questions"][0]["choices"]) == 2


# ============================================================================
# 6.2 TIÊU CHÍ ĐÁNH GIÁ KIỂM SOÁT TƯƠNG TRANH & TRANH CHẤP KHÓA (CONCURRENCY)
# ============================================================================


def test_6_2_multi_tab_race(
    app: Flask,
    instructor_user: User,
    active_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """6.2.1: Multi-Tab Race.

    Tab A holds valid lease token. Tab B attempts to save an answer with missing
    or invalid lease token. Tab B is rejected with 409 LEASE_CONFLICT. Tab A data is preserved.
    """
    sess: Session = db.session
    student1, _ = enrolled_students

    q = create_question(
        instructor_user,
        active_course.id,
        {
            "content": "Multi-Tab Race Question",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "default_points": 5.0,
            "choices": [
                {"content": "A", "is_correct": True, "position": 1},
                {"content": "B", "is_correct": False, "position": 2},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    sess.commit()

    asm = create_assessment(
        instructor_user,
        active_course.id,
        {"title": "Multi-Tab Race Exam", "assessment_type": "QUIZ", "time_limit_minutes": 30},
        session=sess,
    )
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": str(q.public_id), "points": 5.0},
        session=sess,
    )
    publish_assessment(instructor_user, asm.id, session=sess)

    attempt, tab_a_token = start_assessment_attempt(student1, asm.id, session=sess)
    aq = attempt.attempt_questions[0]
    choice_a = next(cs for cs in aq.choice_snapshots if cs.content_snapshot == "A")

    # Tab B sends an answer with invalid lease token
    with pytest.raises(AttemptLeaseConflictError):
        save_attempt_answer(
            actor=student1,
            attempt_id=attempt.id,
            attempt_question_id=aq.id,
            payload={
                "selected_choice_keys": [str(choice_a.choice_key_snapshot)],
                "client_sequence": 1,
            },
            raw_lease_token="invalid_tab_b_token_hex_12345",
            session=sess,
        )

    # Tab A sends answer with valid token -> success
    resp_a = save_attempt_answer(
        actor=student1,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        payload={
            "selected_choice_keys": [str(choice_a.choice_key_snapshot)],
            "client_sequence": 1,
            "lease_epoch": attempt.lease_epoch,
        },
        raw_lease_token=tab_a_token,
        session=sess,
    )
    assert resp_a["answer_version"] >= 1


def test_6_2_takeover_race(
    app: Flask,
    instructor_user: User,
    active_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """6.2.2: Takeover Race.

    After lease expiration on Tab A, Tab B successfully takes over the lease.
    Lease epoch increments. Tab A's subsequent save packet is rejected due to stale epoch / token.
    """
    sess: Session = db.session
    student1, _ = enrolled_students

    q = create_question(
        instructor_user,
        active_course.id,
        {
            "content": "Takeover Question",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "default_points": 5.0,
            "choices": [
                {"content": "Alpha", "is_correct": True, "position": 1},
                {"content": "Beta", "is_correct": False, "position": 2},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    sess.commit()

    asm = create_assessment(
        instructor_user,
        active_course.id,
        {"title": "Takeover Exam", "assessment_type": "QUIZ", "time_limit_minutes": 30},
        session=sess,
    )
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": str(q.public_id), "points": 5.0},
        session=sess,
    )
    publish_assessment(instructor_user, asm.id, session=sess)

    attempt, tab_a_token = start_assessment_attempt(student1, asm.id, session=sess)
    aq = attempt.attempt_questions[0]
    choice_alpha = next(cs for cs in aq.choice_snapshots if cs.content_snapshot == "Alpha")

    # Simulate Tab A lease expiring
    attempt.lease_expires_at = utc_now() - datetime.timedelta(seconds=1)
    sess.commit()

    # Tab B executes takeover
    _, tab_b_token = takeover_attempt_lease(student1, attempt.id, session=sess)
    sess.refresh(attempt)
    assert attempt.lease_epoch == 2
    assert tab_b_token != tab_a_token

    # Tab A tries to save with old token -> rejected
    with pytest.raises(AttemptLeaseConflictError):
        save_attempt_answer(
            actor=student1,
            attempt_id=attempt.id,
            attempt_question_id=aq.id,
            payload={
                "selected_choice_keys": [str(choice_alpha.choice_key_snapshot)],
                "client_sequence": 1,
                "lease_epoch": 1,
            },
            raw_lease_token=tab_a_token,
            session=sess,
        )

    # Tab B saves with new token -> accepted
    res_b = save_attempt_answer(
        actor=student1,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        payload={
            "selected_choice_keys": [str(choice_alpha.choice_key_snapshot)],
            "client_sequence": 1,
            "lease_epoch": 2,
        },
        raw_lease_token=tab_b_token,
        session=sess,
    )
    assert res_b["lease_epoch"] == 2


def test_6_2_offline_replay_race(
    app: Flask,
    instructor_user: User,
    active_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """6.2.3: Offline Replay Race.

    Client submits sequence 3 first (accepted). Subsequently, sequences 1 and 2 arrive.
    The server rejects sequences 1 and 2 as STALE, keeping sequence 3 intact in the DB.
    """
    sess: Session = db.session
    student1, _ = enrolled_students

    q = create_question(
        instructor_user,
        active_course.id,
        {
            "content": "Type the secret word",
            "question_type": "SHORT_ANSWER",
            "difficulty": "REMEMBER",
            "default_points": 5.0,
            "accepted_answers": [{"answer_text": "Diamond", "is_exact_match": True, "position": 1}],
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    sess.commit()

    asm = create_assessment(
        instructor_user,
        active_course.id,
        {"title": "Offline Replay Quiz", "assessment_type": "QUIZ", "time_limit_minutes": 30},
        session=sess,
    )
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": str(q.public_id), "points": 5.0},
        session=sess,
    )
    publish_assessment(instructor_user, asm.id, session=sess)

    attempt, token = start_assessment_attempt(student1, asm.id, session=sess)
    aq = attempt.attempt_questions[0]

    # Send sequence 3 first
    save_attempt_answer(
        actor=student1,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        payload={
            "answer_text": "Final Sequence 3 Answer",
            "client_sequence": 3,
            "lease_epoch": attempt.lease_epoch,
        },
        raw_lease_token=token,
        session=sess,
    )

    # Now attempt to send sequence 1 and sequence 2
    with pytest.raises(StaleAnswerSequenceError):
        save_attempt_answer(
            actor=student1,
            attempt_id=attempt.id,
            attempt_question_id=aq.id,
            payload={
                "answer_text": "Old Sequence 1 Answer",
                "client_sequence": 1,
                "lease_epoch": attempt.lease_epoch,
            },
            raw_lease_token=token,
            session=sess,
        )

    with pytest.raises(StaleAnswerSequenceError):
        save_attempt_answer(
            actor=student1,
            attempt_id=attempt.id,
            attempt_question_id=aq.id,
            payload={
                "answer_text": "Old Sequence 2 Answer",
                "client_sequence": 2,
                "lease_epoch": attempt.lease_epoch,
            },
            raw_lease_token=token,
            session=sess,
        )

    # Verify DB still contains Sequence 3
    db_ans = sess.query(AttemptAnswer).filter_by(attempt_question_id=aq.id).first()
    assert db_ans is not None
    assert db_ans.answer_text == "Final Sequence 3 Answer"
    assert db_ans.last_client_sequence == 3


def test_6_2_concurrent_submit_race(
    app: Flask,
    instructor_user: User,
    active_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """6.2.4: Concurrent Submit Race.

    Multiple submission calls with the same submission_idempotency_key converge
    on the exact same result without duplicate scoring or deadlocks.
    """
    sess: Session = db.session
    student1, _ = enrolled_students

    q = create_question(
        instructor_user,
        active_course.id,
        {
            "content": "Concurrent Submit Question",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "default_points": 10.0,
            "choices": [
                {"content": "A", "is_correct": True, "position": 1},
                {"content": "B", "is_correct": False, "position": 2},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    sess.commit()

    asm = create_assessment(
        instructor_user,
        active_course.id,
        {"title": "Submit Race Exam", "assessment_type": "QUIZ", "time_limit_minutes": 30},
        session=sess,
    )
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": str(q.public_id), "points": 10.0},
        session=sess,
    )
    publish_assessment(instructor_user, asm.id, session=sess)

    attempt, token = start_assessment_attempt(student1, asm.id, session=sess)
    aq = attempt.attempt_questions[0]
    choice_a = next(cs for cs in aq.choice_snapshots if cs.content_snapshot == "A")

    save_attempt_answer(
        actor=student1,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        payload={
            "selected_choice_keys": [str(choice_a.choice_key_snapshot)],
            "client_sequence": 1,
            "lease_epoch": attempt.lease_epoch,
        },
        raw_lease_token=token,
        session=sess,
    )

    idem_key = uuid.uuid4()

    # First submission
    res1 = submit_assessment_attempt(student1, attempt.id, idempotency_key=idem_key, session=sess)
    assert res1["status"] in ("SUBMITTED", "GRADED")

    # 9 Subsequent submissions with same idempotency key
    for _ in range(9):
        res_sub = submit_assessment_attempt(
            student1, attempt.id, idempotency_key=idem_key, session=sess
        )
        assert res_sub["status"] == res1["status"]
        assert res_sub["is_idempotent_replay"] is True

    # Submission with differing key must raise conflict
    with pytest.raises(SubmissionIdempotencyConflictError):
        submit_assessment_attempt(student1, attempt.id, idempotency_key=uuid.uuid4(), session=sess)


# ============================================================================
# 6.3 MA TRẬN TEST CASE THIẾT KẾ CHUẨN (NORMATIVE ACCEPTANCE MATRIX)
# ============================================================================


def test_T_QB_02_edit_exposed_question_branches_new_revision(
    app: Flask,
    instructor_user: User,
    active_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """T-QB-02: Sửa câu hỏi đã dùng để thi
    -> Tạo QuestionRevision mới; revision cũ giữ nguyên was_student_exposed = 1.
    """
    sess: Session = db.session
    student1, _ = enrolled_students

    q = create_question(
        instructor_user,
        active_course.id,
        {
            "content": "Original Stem V1",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "default_points": 5.0,
            "choices": [
                {"content": "1", "is_correct": True, "position": 1},
                {"content": "2", "is_correct": False, "position": 2},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    sess.commit()

    asm = create_assessment(
        instructor_user,
        active_course.id,
        {"title": "T-QB-02 Exam", "assessment_type": "QUIZ"},
        session=sess,
    )
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": str(q.public_id), "points": 5.0},
        session=sess,
    )
    publish_assessment(instructor_user, asm.id, session=sess)

    # Student 1 starts attempt, exposing Revision 1
    start_assessment_attempt(student1, asm.id, session=sess)
    sess.refresh(q)
    rev1 = q.revisions[0]
    assert rev1.was_student_exposed is True

    # Instructor edits question content
    updated_q = update_question(
        instructor_user,
        q.id,
        {
            "content": "Branched Stem V2",
            "reason": "Updating question content after student exposure",
        },
        session=sess,
    )
    sess.commit()

    assert len(updated_q.revisions) == 2
    assert rev1.was_student_exposed is True
    rev2 = updated_q.current_revision
    assert rev2 is not None
    assert rev2.revision_no == 2
    assert rev2.content == "Branched Stem V2"
    assert rev2.was_student_exposed is False


def test_T_QB_03_choice_updates_scoped_to_new_revision(
    app: Flask,
    instructor_user: User,
    active_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """T-QB-03: Cập nhật danh sách phương án
    -> Phương án mới gắn liền với revision mới; bài thi cũ vẫn trỏ về phương án của revision cũ.
    """
    sess: Session = db.session
    student1, _ = enrolled_students

    q = create_question(
        instructor_user,
        active_course.id,
        {
            "content": "What color is the sky?",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "default_points": 5.0,
            "choices": [
                {"content": "Blue", "is_correct": True, "position": 1},
                {"content": "Green", "is_correct": False, "position": 2},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    sess.commit()

    asm = create_assessment(
        instructor_user,
        active_course.id,
        {"title": "T-QB-03 Exam", "assessment_type": "QUIZ"},
        session=sess,
    )
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": str(q.public_id), "points": 5.0},
        session=sess,
    )
    publish_assessment(instructor_user, asm.id, session=sess)

    attempt, _ = start_assessment_attempt(student1, asm.id, session=sess)
    aq = attempt.attempt_questions[0]
    old_choice_texts = [cs.content_snapshot for cs in aq.choice_snapshots]
    assert "Blue" in old_choice_texts

    # Create new revision with different choices
    create_question_revision(
        instructor_user,
        q.id,
        {
            "content": "What color is the sky?",
            "reason": "Expanding choices",
            "choices": [
                {"content": "Azure", "is_correct": True, "position": 1},
                {"content": "Emerald", "is_correct": False, "position": 2},
                {"content": "Ruby", "is_correct": False, "position": 3},
            ],
        },
        session=sess,
    )
    sess.commit()

    # Verify attempt snapshots still point to original choices
    sess.refresh(aq)
    refreshed_choices = [cs.content_snapshot for cs in aq.choice_snapshots]
    assert refreshed_choices == ["Blue", "Green"]


def test_T_QB_04_question_type_locked_after_attempt(
    app: Flask,
    instructor_user: User,
    active_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """T-QB-04: Cố tình đổi question_type của câu hỏi đã thi
    -> Bị chặn bởi kiểm tra ràng buộc; trả về lỗi trạng thái không thể thay đổi.
    """
    sess: Session = db.session
    student1, _ = enrolled_students

    q = create_question(
        instructor_user,
        active_course.id,
        {
            "content": "Single Choice Lock Question",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "default_points": 5.0,
            "choices": [
                {"content": "A", "is_correct": True, "position": 1},
                {"content": "B", "is_correct": False, "position": 2},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    sess.commit()

    asm = create_assessment(
        instructor_user,
        active_course.id,
        {"title": "T-QB-04 Quiz", "assessment_type": "QUIZ"},
        session=sess,
    )
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": str(q.public_id), "points": 5.0},
        session=sess,
    )
    publish_assessment(instructor_user, asm.id, session=sess)

    # Student starts attempt
    start_assessment_attempt(student1, asm.id, session=sess)

    # Attempting to change question_type on in-use question must fail
    with pytest.raises((QuestionImmutableError, QuestionStateViolationError)):
        update_question(
            instructor_user,
            q.id,
            {
                "question_type": "MULTIPLE_CHOICE",
                "reason": "Attempting illegal type change",
            },
            session=sess,
        )


def test_T_QB_05_exposed_or_graded_revisions_retained_permanently(
    app: Flask,
    instructor_user: User,
    active_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """T-QB-05: Tiến trình dọn dẹp chạy quét dữ liệu
    -> Các revision có was_student_exposed = 1 được giữ lại vĩnh viễn, không bị xóa vật lý.
    """
    sess: Session = db.session
    student1, _ = enrolled_students

    q = create_question(
        instructor_user,
        active_course.id,
        {
            "content": "Permanent Retention Question",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "default_points": 5.0,
            "choices": [
                {"content": "X", "is_correct": True, "position": 1},
                {"content": "Y", "is_correct": False, "position": 2},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    sess.commit()

    asm = create_assessment(
        instructor_user,
        active_course.id,
        {"title": "T-QB-05 Quiz", "assessment_type": "QUIZ"},
        session=sess,
    )
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": str(q.public_id), "points": 5.0},
        session=sess,
    )
    publish_assessment(instructor_user, asm.id, session=sess)

    attempt, token = start_assessment_attempt(student1, asm.id, session=sess)
    submit_assessment_attempt(student1, attempt.id, idempotency_key=uuid.uuid4(), session=sess)

    # Trash the question
    trash_question(instructor_user, q.id, reason="Archiving question", session=sess)
    sess.refresh(q)

    # Must be RETIRED (never physically deleted)
    assert q.status == "RETIRED"
    assert len(q.revisions) == 1
    assert q.revisions[0].was_student_exposed is True


def test_T_ASSESS_01_timing_locked_after_publish(
    app: Flask, instructor_user: User, active_course: Course
) -> None:
    """T-ASSESS-01: Sửa thời gian bài thi sau xuất bản -> Ném ngoại lệ cấu hình bất biến."""
    sess: Session = db.session
    q = create_question(
        instructor_user,
        active_course.id,
        {
            "content": "Q1",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "choices": [
                {"content": "1", "is_correct": True, "position": 1},
                {"content": "2", "is_correct": False, "position": 2},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    sess.commit()

    asm = create_assessment(
        instructor_user,
        active_course.id,
        {"title": "T-ASSESS-01 Quiz", "assessment_type": "QUIZ", "time_limit_minutes": 25},
        session=sess,
    )
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": str(q.public_id), "points": 5.0},
        session=sess,
    )
    publish_assessment(instructor_user, asm.id, session=sess)

    with pytest.raises(AssessmentLockedError):
        update_assessment(
            instructor_user,
            asm.id,
            {"time_limit_minutes": 50},
            session=sess,
        )


def test_T_ASSESS_02_question_list_locked_after_first_attempt(
    app: Flask,
    instructor_user: User,
    active_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """T-ASSESS-02: Sửa danh sách câu hỏi sau khi có sinh viên bắt đầu
    -> Thao tác thêm/xóa câu hỏi bị từ chối.
    """
    sess: Session = db.session
    student1, _ = enrolled_students

    q1 = create_question(
        instructor_user,
        active_course.id,
        {
            "content": "Q1",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "choices": [
                {"content": "A", "is_correct": True, "position": 1},
                {"content": "B", "is_correct": False, "position": 2},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    q2 = create_question(
        instructor_user,
        active_course.id,
        {
            "content": "Q2",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "choices": [
                {"content": "C", "is_correct": True, "position": 1},
                {"content": "D", "is_correct": False, "position": 2},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    sess.commit()

    asm = create_assessment(
        instructor_user,
        active_course.id,
        {"title": "T-ASSESS-02 Quiz", "assessment_type": "QUIZ"},
        session=sess,
    )
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": str(q1.public_id), "points": 5.0},
        session=sess,
    )
    publish_assessment(instructor_user, asm.id, session=sess)

    start_assessment_attempt(student1, asm.id, session=sess)

    with pytest.raises(AssessmentLockedError):
        assign_question(
            instructor_user,
            asm.id,
            {"question_id": str(q2.public_id), "points": 5.0},
            session=sess,
        )


def test_T_ASSESS_03_question_points_locked_after_first_attempt(
    app: Flask,
    instructor_user: User,
    active_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """T-ASSESS-03: Sửa điểm số câu hỏi sau khi có sinh viên bắt đầu
    -> Thao tác sửa thang điểm bị từ chối.
    """
    sess: Session = db.session
    student1, _ = enrolled_students

    q = create_question(
        instructor_user,
        active_course.id,
        {
            "content": "Points Question",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "choices": [
                {"content": "Yes", "is_correct": True, "position": 1},
                {"content": "No", "is_correct": False, "position": 2},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    sess.commit()

    asm = create_assessment(
        instructor_user,
        active_course.id,
        {"title": "T-ASSESS-03 Exam", "assessment_type": "MIDTERM"},
        session=sess,
    )
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": str(q.public_id), "points": 10.0},
        session=sess,
    )
    publish_assessment(instructor_user, asm.id, session=sess)

    # Before first attempt, points and position can be updated via points_assigned alias
    updated_asgn = update_question_assignment(
        instructor_user,
        asm.id,
        q.id,
        {"points_assigned": 12.0, "position": 1},
        session=sess,
    )
    assert updated_asgn.points == Decimal("12.0000")
    assert updated_asgn.position == 1

    attempt, _ = start_assessment_attempt(student1, asm.id, session=sess)
    aq = attempt.attempt_questions[0]
    assert aq.points_assigned == Decimal("12.0000")

    with pytest.raises(AssessmentLockedError):
        update_question_assignment(
            instructor_user,
            asm.id,
            q.id,
            {"points": 25.0},
            session=sess,
        )

    sess.refresh(aq)
    assert aq.points_assigned == Decimal("12.0000")


def test_T_ASSESS_04_blueprint_shortage_blocks_publish(
    app: Flask, instructor_user: User, active_course: Course
) -> None:
    """T-ASSESS-04: Xuất bản bài thi có khung đề thiếu câu hỏi
    -> Chặn xuất bản và nhận báo cáo thiếu hụt.
    """
    sess: Session = db.session

    # Course only has 1 APPLY question
    create_question(
        instructor_user,
        active_course.id,
        {
            "content": "Only available question",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "APPLY",
            "choices": [
                {"content": "1", "is_correct": True, "position": 1},
                {"content": "2", "is_correct": False, "position": 2},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    sess.commit()

    asm = create_assessment(
        instructor_user,
        active_course.id,
        {"title": "Blueprint Shortage Exam", "assessment_type": "FINAL"},
        session=sess,
    )

    # Configure rule requiring 5 APPLY questions
    configure_blueprint(
        instructor_user,
        asm.id,
        {
            "rules": [
                {
                    "difficulty": "APPLY",
                    "question_type": "SINGLE_CHOICE",
                    "question_count": 5,
                    "points_each": 2.0,
                }
            ]
        },
        session=sess,
    )

    with pytest.raises(BlueprintValidationError, match="Blueprint question shortage detected"):
        publish_assessment(instructor_user, asm.id, session=sess)

    assert asm.status == "DRAFT"


def test_T_ASSESS_05_two_students_start_before_and_after_new_revision(
    app: Flask,
    instructor_user: User,
    active_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """T-ASSESS-05: Hai sinh viên bắt đầu thi trước và sau khi có revision mới
    -> SV 1 giữ revision cũ, SV 2 nhận revision mới.
    """
    sess: Session = db.session
    student1, student2 = enrolled_students

    q = create_question(
        instructor_user,
        active_course.id,
        {
            "content": "Stem Revision 1 Text",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "choices": [
                {"content": "Option 1", "is_correct": True, "position": 1},
                {"content": "Option 2", "is_correct": False, "position": 2},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    sess.commit()

    asm = create_assessment(
        instructor_user,
        active_course.id,
        {"title": "Dual Student Revision Exam", "assessment_type": "QUIZ", "attempt_limit": 2},
        session=sess,
    )
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": str(q.public_id), "points": 5.0},
        session=sess,
    )
    publish_assessment(instructor_user, asm.id, session=sess)

    # Student 1 starts before new revision
    attempt1, _ = start_assessment_attempt(student1, asm.id, session=sess)
    aq1 = attempt1.attempt_questions[0]
    assert aq1.content_snapshot == "Stem Revision 1 Text"

    # Instructor creates Revision 2
    create_question_revision(
        instructor_user,
        q.id,
        {
            "content": "Stem Revision 2 Text",
            "reason": "Clarifying phrasing",
            "choices": [
                {"content": "Option 1", "is_correct": True, "position": 1},
                {"content": "Option 2", "is_correct": False, "position": 2},
            ],
        },
        session=sess,
    )
    sess.commit()

    # Student 2 starts after Revision 2
    attempt2, _ = start_assessment_attempt(student2, asm.id, session=sess)
    aq2 = attempt2.attempt_questions[0]
    assert aq2.content_snapshot == "Stem Revision 2 Text"

    # Student 1 snapshot remains Revision 1
    sess.refresh(aq1)
    assert aq1.content_snapshot == "Stem Revision 1 Text"


def test_T_ASSESS_06_shuffled_positions_preserved_on_resume(
    app: Flask,
    instructor_user: User,
    active_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """T-ASSESS-06: Sinh viên tải lại trang (reload/resume) bài thi xáo trộn
    -> Thứ tự câu hỏi và phương án giữ nguyên 100%.
    """
    sess: Session = db.session
    student1, _ = enrolled_students

    for i in range(3):
        create_question(
            instructor_user,
            active_course.id,
            {
                "content": f"Shuffle Question {i + 1}",
                "question_type": "SINGLE_CHOICE",
                "difficulty": "REMEMBER",
                "choices": [
                    {"content": f"Choice {i}-A", "is_correct": True, "position": 1},
                    {"content": f"Choice {i}-B", "is_correct": False, "position": 2},
                    {"content": f"Choice {i}-C", "is_correct": False, "position": 3},
                ],
                "provenance": {"source_type": "MANUAL"},
            },
            session=sess,
        )
    sess.commit()

    asm = create_assessment(
        instructor_user,
        active_course.id,
        {
            "title": "Shuffle Stability Test",
            "assessment_type": "QUIZ",
            "shuffle_questions": True,
            "shuffle_choices": True,
        },
        session=sess,
    )
    for q in sess.query(Question).filter_by(course_id=active_course.id).all():
        assign_question(
            instructor_user,
            asm.id,
            {"question_id": str(q.public_id), "points": 5.0},
            session=sess,
        )
    publish_assessment(instructor_user, asm.id, session=sess)

    attempt, _ = start_assessment_attempt(student1, asm.id, session=sess)

    # First delivery
    deliv1 = get_attempt_delivery(student1, attempt.id, session=sess)
    q_order_1 = [q["content"] for q in deliv1["questions"]]
    choice_order_1 = [[c["content"] for c in q["choices"]] for q in deliv1["questions"]]

    # Second delivery (simulating page reload)
    deliv2 = get_attempt_delivery(student1, attempt.id, session=sess)
    q_order_2 = [q["content"] for q in deliv2["questions"]]
    choice_order_2 = [[c["content"] for c in q["choices"]] for q in deliv2["questions"]]

    assert q_order_1 == q_order_2
    assert choice_order_1 == choice_order_2


def test_T_ATT_01_attempt_limit_exceeded_rejected(
    app: Flask,
    instructor_user: User,
    active_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """T-ATT-01: Sinh viên cố tình thi vượt quá số lượt attempt_limit
    -> Bị chặn ở giao dịch tạo lượt thi mới.
    """
    sess: Session = db.session
    student1, _ = enrolled_students

    q = create_question(
        instructor_user,
        active_course.id,
        {
            "content": "Limit Q",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "choices": [
                {"content": "1", "is_correct": True, "position": 1},
                {"content": "2", "is_correct": False, "position": 2},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    sess.commit()

    asm = create_assessment(
        instructor_user,
        active_course.id,
        {"title": "Attempt Limit Test", "assessment_type": "QUIZ", "attempt_limit": 1},
        session=sess,
    )
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": str(q.public_id), "points": 5.0},
        session=sess,
    )
    publish_assessment(instructor_user, asm.id, session=sess)

    # Attempt 1
    att1, _ = start_assessment_attempt(student1, asm.id, session=sess)
    submit_assessment_attempt(student1, att1.id, idempotency_key=uuid.uuid4(), session=sess)

    # Attempt 2 must fail
    with pytest.raises(AttemptLimitExceededError):
        start_assessment_attempt(student1, asm.id, session=sess)


def test_T_ATT_02_deadline_clamped_to_assessment_close_at(
    app: Flask,
    instructor_user: User,
    active_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """T-ATT-02: Sinh viên bắt đầu thi khi đợt thi chỉ còn 10 phút
    -> deadline_at tự động bị ép cụt bằng close_at.
    """
    sess: Session = db.session
    student1, _ = enrolled_students
    now = utc_now()

    q = create_question(
        instructor_user,
        active_course.id,
        {
            "content": "Clamping Q",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "choices": [
                {"content": "A", "is_correct": True, "position": 1},
                {"content": "B", "is_correct": False, "position": 2},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    sess.commit()

    close_time = now + datetime.timedelta(minutes=10)
    asm = create_assessment(
        instructor_user,
        active_course.id,
        {
            "title": "Clamped Deadline Exam",
            "assessment_type": "QUIZ",
            "time_limit_minutes": 60,  # 60 min limit, but only 10 min left in window
            "close_at": close_time.isoformat(),
        },
        session=sess,
    )
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": str(q.public_id), "points": 5.0},
        session=sess,
    )
    publish_assessment(instructor_user, asm.id, session=sess)

    attempt, _ = start_assessment_attempt(student1, asm.id, session=sess)
    diff = (attempt.deadline_at - attempt.started_at).total_seconds()
    # Must be ~10 minutes (600s), NOT 60 minutes (3600s)
    assert 590 <= diff <= 610


def test_T_ATT_03_concurrent_tabs_second_tab_lease_conflict(
    app: Flask,
    instructor_user: User,
    active_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """T-ATT-03: Hai tab cùng làm bài đồng thời
    -> Tab thứ hai bị từ chối lưu bài với mã lỗi 409 LEASE_CONFLICT.
    """
    sess: Session = db.session
    student1, _ = enrolled_students

    q = create_question(
        instructor_user,
        active_course.id,
        {
            "content": "Lease Tab Question",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "choices": [
                {"content": "X", "is_correct": True, "position": 1},
                {"content": "Y", "is_correct": False, "position": 2},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    sess.commit()

    asm = create_assessment(
        instructor_user,
        active_course.id,
        {"title": "Tab Conflict Quiz", "assessment_type": "QUIZ"},
        session=sess,
    )
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": str(q.public_id), "points": 5.0},
        session=sess,
    )
    publish_assessment(instructor_user, asm.id, session=sess)

    attempt, token1 = start_assessment_attempt(student1, asm.id, session=sess)
    aq = attempt.attempt_questions[0]

    with pytest.raises(AttemptLeaseConflictError):
        save_attempt_answer(
            actor=student1,
            attempt_id=attempt.id,
            attempt_question_id=aq.id,
            payload={"selected_choice_keys": [], "client_sequence": 1},
            raw_lease_token="fake_tab2_token",
            session=sess,
        )


def test_T_ATT_04_takeover_after_lease_expiry_preserves_attempt(
    app: Flask,
    instructor_user: User,
    active_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """T-ATT-04: Đổi máy/đổi tab sau khi lease hết hạn
    -> Tab mới thực hiện takeover thành công, tiếp tục làm bài thi cũ.
    """
    sess: Session = db.session
    student1, _ = enrolled_students

    q = create_question(
        instructor_user,
        active_course.id,
        {
            "content": "Takeover Resume Question",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "choices": [
                {"content": "A", "is_correct": True, "position": 1},
                {"content": "B", "is_correct": False, "position": 2},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    sess.commit()

    asm = create_assessment(
        instructor_user,
        active_course.id,
        {"title": "Takeover Resume Quiz", "assessment_type": "QUIZ"},
        session=sess,
    )
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": str(q.public_id), "points": 5.0},
        session=sess,
    )
    publish_assessment(instructor_user, asm.id, session=sess)

    attempt, token1 = start_assessment_attempt(student1, asm.id, session=sess)
    aq = attempt.attempt_questions[0]
    choice_a = aq.choice_snapshots[0]

    # Save answer on Tab 1
    save_attempt_answer(
        actor=student1,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        payload={
            "selected_choice_keys": [str(choice_a.choice_key_snapshot)],
            "client_sequence": 1,
            "lease_epoch": 1,
        },
        raw_lease_token=token1,
        session=sess,
    )

    # Lease expires
    attempt.lease_expires_at = utc_now() - datetime.timedelta(seconds=1)
    sess.commit()

    # Tab 2 executes takeover
    att_taken, token2 = takeover_attempt_lease(student1, attempt.id, session=sess)
    assert att_taken.id == attempt.id
    assert att_taken.lease_epoch == 2

    # Verify existing answer is preserved
    ans = sess.query(AttemptAnswer).filter_by(attempt_question_id=aq.id).first()
    assert ans is not None
    assert ans.last_client_sequence == 1


def test_T_ATT_05_autosave_acknowledgment_and_timing(
    app: Flask,
    instructor_user: User,
    active_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """T-ATT-05: Lưu bài tự luận có độ trễ khử rung và lưu trắc nghiệm ngay
    -> Nhận phản hồi ACK với answer_version.
    """
    sess: Session = db.session
    student1, _ = enrolled_students

    q_essay = create_question(
        instructor_user,
        active_course.id,
        {
            "content": "Describe recursion",
            "question_type": "ESSAY",
            "difficulty": "UNDERSTAND",
            "default_points": 10.0,
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    sess.commit()

    asm = create_assessment(
        instructor_user,
        active_course.id,
        {"title": "Essay Autosave Quiz", "assessment_type": "QUIZ"},
        session=sess,
    )
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": str(q_essay.public_id), "points": 10.0},
        session=sess,
    )
    publish_assessment(instructor_user, asm.id, session=sess)

    attempt, token = start_assessment_attempt(student1, asm.id, session=sess)
    aq = attempt.attempt_questions[0]

    # Save 1
    ack1 = save_attempt_answer(
        actor=student1,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        payload={
            "answer_text": "Recursion is when a function calls itself.",
            "client_sequence": 1,
            "lease_epoch": attempt.lease_epoch,
        },
        raw_lease_token=token,
        session=sess,
    )
    assert ack1["answer_version"] == 1
    assert ack1["last_client_sequence"] == 1

    # Save 2 after debounce
    ack2 = save_attempt_answer(
        actor=student1,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        payload={
            "answer_text": "Recursion is when a function calls itself with a base case.",
            "client_sequence": 2,
            "lease_epoch": attempt.lease_epoch,
        },
        raw_lease_token=token,
        session=sess,
    )
    assert ack2["answer_version"] == 2
    assert ack2["last_client_sequence"] == 2


def test_T_ATT_06_save_packet_after_deadline_rejected(
    app: Flask,
    instructor_user: User,
    active_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """T-ATT-06: Gói tin lưu bài gửi đến máy chủ sau hạn chót deadline_at
    -> Bị từ chối với lý do AFTER_DEADLINE/EXPIRED.
    """
    sess: Session = db.session
    student1, _ = enrolled_students

    q = create_question(
        instructor_user,
        active_course.id,
        {
            "content": "Timed Question",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "choices": [
                {"content": "A", "is_correct": True, "position": 1},
                {"content": "B", "is_correct": False, "position": 2},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    sess.commit()

    asm = create_assessment(
        instructor_user,
        active_course.id,
        {"title": "Expired Quiz", "assessment_type": "QUIZ", "time_limit_minutes": 10},
        session=sess,
    )
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": str(q.public_id), "points": 5.0},
        session=sess,
    )
    publish_assessment(instructor_user, asm.id, session=sess)

    attempt, token = start_assessment_attempt(student1, asm.id, session=sess)
    aq = attempt.attempt_questions[0]

    # Advance time past deadline (keeping deadline_at >= started_at for check constraint)
    now = utc_now()
    attempt.started_at = now - datetime.timedelta(minutes=15)
    attempt.deadline_at = now - datetime.timedelta(minutes=5)
    sess.commit()

    with pytest.raises(AttemptExpiredError):
        save_attempt_answer(
            actor=student1,
            attempt_id=attempt.id,
            attempt_question_id=aq.id,
            payload={"selected_choice_keys": [], "client_sequence": 1},
            raw_lease_token=token,
            session=sess,
        )

    sess.refresh(attempt)
    assert attempt.status == "EXPIRED"


def test_T_ATT_07_multiple_submissions_idempotent_result(
    app: Flask,
    instructor_user: User,
    active_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """T-ATT-07: Nộp bài nhiều lần do mạng chập chờn
    -> Tất cả các lần gọi đều trả về cùng một mã kết quả và cùng tổng điểm số.
    """
    sess: Session = db.session
    student1, _ = enrolled_students

    q = create_question(
        instructor_user,
        active_course.id,
        {
            "content": "Submit Idempotency Q",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "choices": [
                {"content": "A", "is_correct": True, "position": 1},
                {"content": "B", "is_correct": False, "position": 2},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    sess.commit()

    asm = create_assessment(
        instructor_user,
        active_course.id,
        {"title": "Idempotency Quiz", "assessment_type": "QUIZ"},
        session=sess,
    )
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": str(q.public_id), "points": 10.0},
        session=sess,
    )
    publish_assessment(instructor_user, asm.id, session=sess)

    attempt, _ = start_assessment_attempt(student1, asm.id, session=sess)
    key = uuid.uuid4()

    res1 = submit_assessment_attempt(student1, attempt.id, idempotency_key=key, session=sess)
    res2 = submit_assessment_attempt(student1, attempt.id, idempotency_key=key, session=sess)
    res3 = submit_assessment_attempt(student1, attempt.id, idempotency_key=key, session=sess)

    assert res1["status"] == res2["status"] == res3["status"]
    assert res1["submitted_at"] == res2["submitted_at"] == res3["submitted_at"]


def test_T_GRADE_01_objective_exact_set_no_partial_credit(
    app: Flask,
    instructor_user: User,
    active_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """T-GRADE-01: Chấm câu hỏi trắc nghiệm nhiều lựa chọn chọn thiếu 1 đáp án
    -> Tính 0 điểm tuyệt đối; không chấm điểm một phần.
    """
    sess: Session = db.session
    student1, _ = enrolled_students

    q_mc = create_question(
        instructor_user,
        active_course.id,
        {
            "content": "Select prime numbers under 5",
            "question_type": "MULTIPLE_CHOICE",
            "difficulty": "REMEMBER",
            "default_points": 10.0,
            "choices": [
                {"content": "2", "is_correct": True, "position": 1},
                {"content": "3", "is_correct": True, "position": 2},
                {"content": "4", "is_correct": False, "position": 3},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    sess.commit()

    asm = create_assessment(
        instructor_user,
        active_course.id,
        {"title": "Exact Set Quiz", "assessment_type": "QUIZ"},
        session=sess,
    )
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": str(q_mc.public_id), "points": 10.0},
        session=sess,
    )
    publish_assessment(instructor_user, asm.id, session=sess)

    attempt, token = start_assessment_attempt(student1, asm.id, session=sess)
    aq = attempt.attempt_questions[0]
    # Student selects only choice "2" (missing "3")
    choice_2 = next(cs for cs in aq.choice_snapshots if cs.content_snapshot == "2")

    save_attempt_answer(
        actor=student1,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        payload={
            "selected_choice_keys": [str(choice_2.choice_key_snapshot)],
            "client_sequence": 1,
            "lease_epoch": attempt.lease_epoch,
        },
        raw_lease_token=token,
        session=sess,
    )
    submit_assessment_attempt(student1, attempt.id, idempotency_key=uuid.uuid4(), session=sess)

    grade = sess.query(AttemptQuestionGrade).filter_by(attempt_question_id=aq.id).first()
    assert grade is not None
    assert grade.awarded_points == Decimal("0.0000")


def test_T_GRADE_02_short_answer_string_normalization(
    app: Flask,
    instructor_user: User,
    active_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """T-GRADE-02: Chấm câu hỏi điền từ có khoảng trắng thừa và viết hoa
    -> Tự động chuẩn hóa chuỗi và chấm đúng nếu khớp.
    """
    sess: Session = db.session
    student1, _ = enrolled_students

    q_sa = create_question(
        instructor_user,
        active_course.id,
        {
            "content": "Name the capital of France",
            "question_type": "SHORT_ANSWER",
            "difficulty": "REMEMBER",
            "default_points": 5.0,
            "accepted_answers": [{"answer_text": "Paris", "is_exact_match": False, "position": 1}],
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    sess.commit()

    asm = create_assessment(
        instructor_user,
        active_course.id,
        {"title": "Short Answer Normalization Quiz", "assessment_type": "QUIZ"},
        session=sess,
    )
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": str(q_sa.public_id), "points": 5.0},
        session=sess,
    )
    publish_assessment(instructor_user, asm.id, session=sess)

    attempt, token = start_assessment_attempt(student1, asm.id, session=sess)
    aq = attempt.attempt_questions[0]

    # Student answers with leading/trailing spaces and mixed casing
    save_attempt_answer(
        actor=student1,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        payload={
            "answer_text": "   pArIs   ",
            "client_sequence": 1,
            "lease_epoch": attempt.lease_epoch,
        },
        raw_lease_token=token,
        session=sess,
    )
    submit_assessment_attempt(student1, attempt.id, idempotency_key=uuid.uuid4(), session=sess)

    grade = sess.query(AttemptQuestionGrade).filter_by(attempt_question_id=aq.id).first()
    assert grade is not None
    assert grade.awarded_points == Decimal("5.0000")


def test_T_GRADE_03_submission_with_essay_remains_pending(
    app: Flask,
    instructor_user: User,
    active_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """T-GRADE-03: Nộp bài thi có câu hỏi tự luận
    -> Trạng thái kết quả bài thi là PENDING; điểm số chưa được công bố.
    """
    sess: Session = db.session
    student1, _ = enrolled_students

    q_essay = create_question(
        instructor_user,
        active_course.id,
        {
            "content": "Explain polymorphic inheritance",
            "question_type": "ESSAY",
            "difficulty": "UNDERSTAND",
            "default_points": 20.0,
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    sess.commit()

    asm = create_assessment(
        instructor_user,
        active_course.id,
        {"title": "Essay Exam", "assessment_type": "MIDTERM"},
        session=sess,
    )
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": str(q_essay.public_id), "points": 20.0},
        session=sess,
    )
    publish_assessment(instructor_user, asm.id, session=sess)

    attempt, token = start_assessment_attempt(student1, asm.id, session=sess)
    aq = attempt.attempt_questions[0]

    save_attempt_answer(
        actor=student1,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        payload={
            "answer_text": "Polymorphism allows subclasses to define customized behavior...",
            "client_sequence": 1,
            "lease_epoch": attempt.lease_epoch,
        },
        raw_lease_token=token,
        session=sess,
    )
    submit_assessment_attempt(student1, attempt.id, idempotency_key=uuid.uuid4(), session=sess)

    result = sess.query(AssessmentResult).filter_by(attempt_id=attempt.id).first()
    assert result is not None
    assert result.status == "PENDING"
    assert result.percent_score is None


def test_T_GRADE_04_manual_essay_grading_and_revision_history(
    app: Flask,
    instructor_user: User,
    active_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """T-GRADE-04: Giảng viên chấm câu tự luận và sau đó sửa lại điểm
    -> Lưu vết đầy đủ điểm cũ, điểm mới, lý do giải trình.
    """
    sess: Session = db.session
    student1, _ = enrolled_students

    q_essay = create_question(
        instructor_user,
        active_course.id,
        {
            "content": "Essay Question for Grading",
            "question_type": "ESSAY",
            "difficulty": "UNDERSTAND",
            "default_points": 10.0,
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    sess.commit()

    asm = create_assessment(
        instructor_user,
        active_course.id,
        {"title": "Manual Grade History Quiz", "assessment_type": "QUIZ"},
        session=sess,
    )
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": str(q_essay.public_id), "points": 10.0},
        session=sess,
    )
    publish_assessment(instructor_user, asm.id, session=sess)

    attempt, token = start_assessment_attempt(student1, asm.id, session=sess)
    aq = attempt.attempt_questions[0]

    save_attempt_answer(
        actor=student1,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        payload={
            "answer_text": "Student essay submission",
            "client_sequence": 1,
            "lease_epoch": attempt.lease_epoch,
        },
        raw_lease_token=token,
        session=sess,
    )
    submit_assessment_attempt(student1, attempt.id, idempotency_key=uuid.uuid4(), session=sess)

    # 1. Instructor grades essay initial: 7.0
    grade_essay_question(
        actor=instructor_user,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        awarded_points=7.0,
        reason="Good initial analysis",
        session=sess,
    )

    # 2. Instructor amends grade to 9.0
    grade_essay_question(
        actor=instructor_user,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        awarded_points=9.0,
        reason="Re-read: bonus for exceptional clarity",
        session=sess,
    )

    history = (
        sess.query(AttemptQuestionGradeHistory)
        .filter_by(attempt_question_id=aq.id)
        .order_by(AttemptQuestionGradeHistory.created_at.asc())
        .all()
    )
    assert len(history) >= 2
    latest = history[-1]
    assert latest.old_points == Decimal("7.0000")
    assert latest.new_points == Decimal("9.0000")
    assert latest.reason == "Re-read: bonus for exceptional clarity"


def test_T_REG_01_answer_only_regrade_updates_scores(
    app: Flask,
    instructor_user: User,
    active_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """T-REG-01: Đính chính ANSWER_ONLY trên câu hỏi trắc nghiệm
    -> Tác vụ nền chạy tự động; điểm số cập nhật chính xác.
    """
    sess: Session = db.session
    student1, _ = enrolled_students

    q = create_question(
        instructor_user,
        active_course.id,
        {
            "content": "Which planet is closest to the Sun?",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "default_points": 10.0,
            "choices": [
                {"content": "Venus", "is_correct": True, "position": 1},  # Erroneous answer key
                {"content": "Mercury", "is_correct": False, "position": 2},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    sess.commit()

    asm = create_assessment(
        instructor_user,
        active_course.id,
        {"title": "Planet Exam", "assessment_type": "QUIZ", "score_release_policy": "IMMEDIATE"},
        session=sess,
    )
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": str(q.public_id), "points": 10.0},
        session=sess,
    )
    publish_assessment(instructor_user, asm.id, session=sess)

    # Student selects "Mercury" (incorrect per V1)
    attempt, token = start_assessment_attempt(student1, asm.id, session=sess)
    aq = attempt.attempt_questions[0]
    choice_mercury = next(cs for cs in aq.choice_snapshots if cs.content_snapshot == "Mercury")

    save_attempt_answer(
        actor=student1,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        payload={
            "selected_choice_keys": [str(choice_mercury.choice_key_snapshot)],
            "client_sequence": 1,
            "lease_epoch": attempt.lease_epoch,
        },
        raw_lease_token=token,
        session=sess,
    )
    submit_assessment_attempt(student1, attempt.id, idempotency_key=uuid.uuid4(), session=sess)

    grade_before = sess.query(AttemptQuestionGrade).filter_by(attempt_question_id=aq.id).first()
    assert grade_before is not None
    assert grade_before.awarded_points == Decimal("0.0000")

    # Instructor files ANSWER_ONLY correction
    _, correction = create_question_revision(
        instructor_user,
        q.id,
        {
            "content": "Which planet is closest to the Sun?",
            "reason": "Fix correct planet to Mercury",
            "correction_type": "ANSWER_ONLY",
            "choices": [
                {"content": "Venus", "is_correct": False, "position": 1},
                {"content": "Mercury", "is_correct": True, "position": 2},
            ],
        },
        session=sess,
    )
    sess.commit()

    job = create_or_get_regrade_job(correction.id, session=sess)
    process_regrade_job(job.id, actor=instructor_user, session=sess)

    grade_after = sess.query(AttemptQuestionGrade).filter_by(attempt_question_id=aq.id).first()
    assert grade_after is not None
    assert grade_after.awarded_points == Decimal("10.0000")

    result = sess.query(AssessmentResult).filter_by(attempt_id=attempt.id).first()
    assert result is not None
    assert result.raw_score == Decimal("10.0000")


def test_T_REG_02_content_or_choices_correction_awards_full_credit(
    app: Flask,
    instructor_user: User,
    active_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """T-REG-02: Đính chính CONTENT_OR_CHOICES trên đề bài bị sai sót
    -> Cấp điểm tối đa (FULL_CREDIT) cho các bài thi bắt đầu trước thời điểm đính chính.
    """
    sess: Session = db.session
    student1, student2 = enrolled_students

    q = create_question(
        instructor_user,
        active_course.id,
        {
            "content": "Flawed question with ambiguous choices",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "default_points": 8.0,
            "choices": [
                {"content": "Ambiguous A", "is_correct": True, "position": 1},
                {"content": "Ambiguous B", "is_correct": False, "position": 2},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    sess.commit()

    asm = create_assessment(
        instructor_user,
        active_course.id,
        {"title": "Ambiguous Question Quiz", "assessment_type": "QUIZ"},
        session=sess,
    )
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": str(q.public_id), "points": 8.0},
        session=sess,
    )
    publish_assessment(instructor_user, asm.id, session=sess)

    # Student 1 starts attempt before correction
    attempt, token = start_assessment_attempt(student1, asm.id, session=sess)
    aq = attempt.attempt_questions[0]
    choice_b = next(cs for cs in aq.choice_snapshots if cs.content_snapshot == "Ambiguous B")

    save_attempt_answer(
        actor=student1,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        payload={"selected_choice_keys": [str(choice_b.choice_key_snapshot)], "client_sequence": 1},
        raw_lease_token=token,
        session=sess,
    )
    submit_assessment_attempt(student1, attempt.id, idempotency_key=uuid.uuid4(), session=sess)

    # Instructor files CONTENT_OR_CHOICES correction
    _, correction = create_question_revision(
        instructor_user,
        q.id,
        {
            "content": "Corrected unambiguous question content",
            "reason": "Defective question wording; awarding full credit to past test takers",
            "correction_type": "CONTENT_OR_CHOICES",
            "choices": [
                {"content": "Clear A", "is_correct": True, "position": 1},
                {"content": "Clear B", "is_correct": False, "position": 2},
            ],
        },
        session=sess,
    )
    sess.commit()

    # Student 2 starts attempt AFTER correction is effective (takes corrected question)
    attempt2, token2 = start_assessment_attempt(student2, asm.id, session=sess)
    aq2 = attempt2.attempt_questions[0]
    choice_b2 = next(cs for cs in aq2.choice_snapshots if cs.content_snapshot == "Clear B")

    save_attempt_answer(
        actor=student2,
        attempt_id=attempt2.id,
        attempt_question_id=aq2.id,
        payload={
            "selected_choice_keys": [str(choice_b2.choice_key_snapshot)],
            "client_sequence": 1,
        },
        raw_lease_token=token2,
        session=sess,
    )
    submit_assessment_attempt(student2, attempt2.id, idempotency_key=uuid.uuid4(), session=sess)

    # Student 2 chose incorrect Clear B on corrected question; initial awarded points = 0
    grade2_before = sess.query(AttemptQuestionGrade).filter_by(attempt_question_id=aq2.id).first()
    assert grade2_before is not None
    assert grade2_before.awarded_points == Decimal("0.0000")

    job = create_or_get_regrade_job(correction.id, session=sess)
    process_regrade_job(job.id, actor=instructor_user, session=sess)

    # Student 1 (started before correction) was exposed to flawed question -> FULL_CREDIT
    grade1 = sess.query(AttemptQuestionGrade).filter_by(attempt_question_id=aq.id).first()
    assert grade1 is not None
    assert grade1.awarded_points == Decimal("8.0000")
    assert grade1.grading_status == "FULL_CREDIT"

    # Student 2 (started after correction) took corrected question -> retains score (0.0)
    grade2 = sess.query(AttemptQuestionGrade).filter_by(attempt_question_id=aq2.id).first()
    assert grade2 is not None
    assert grade2.awarded_points == Decimal("0.0000")
    assert grade2.grading_status != "FULL_CREDIT"


def test_T_REG_03_regrade_preserves_attempt_history_immutability(
    app: Flask,
    instructor_user: User,
    active_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """T-REG-03: Kiểm tra tính bất biến của dữ liệu sau khi chấm lại
    -> attempt_questions và attempt_answers nguyên vẹn; chỉ cập nhật grades và results.
    """
    sess: Session = db.session
    student1, _ = enrolled_students

    q = create_question(
        instructor_user,
        active_course.id,
        {
            "content": "Immutability Regrade Q",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "default_points": 10.0,
            "choices": [
                {"content": "Wrong", "is_correct": True, "position": 1},
                {"content": "Right", "is_correct": False, "position": 2},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    sess.commit()

    asm = create_assessment(
        instructor_user,
        active_course.id,
        {"title": "Immutability Regrade Quiz", "assessment_type": "QUIZ"},
        session=sess,
    )
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": str(q.public_id), "points": 10.0},
        session=sess,
    )
    publish_assessment(instructor_user, asm.id, session=sess)

    attempt, token = start_assessment_attempt(student1, asm.id, session=sess)
    aq = attempt.attempt_questions[0]
    choice_right = next(cs for cs in aq.choice_snapshots if cs.content_snapshot == "Right")

    save_attempt_answer(
        actor=student1,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        payload={
            "selected_choice_keys": [str(choice_right.choice_key_snapshot)],
            "client_sequence": 1,
        },
        raw_lease_token=token,
        session=sess,
    )
    submit_assessment_attempt(student1, attempt.id, idempotency_key=uuid.uuid4(), session=sess)

    # Capture snapshot values
    aq_content_before = aq.content_snapshot
    aq_points_before = aq.points_assigned
    cs_keys_before = [cs.choice_key_snapshot for cs in aq.choice_snapshots]
    ans_record = sess.query(AttemptAnswer).filter_by(attempt_question_id=aq.id).first()
    ans_version_before = ans_record.answer_version

    # Issue correction and regrade
    _, correction = create_question_revision(
        instructor_user,
        q.id,
        {
            "content": "Immutability Regrade Q",
            "reason": "Fix right answer",
            "correction_type": "ANSWER_ONLY",
            "choices": [
                {"content": "Wrong", "is_correct": False, "position": 1},
                {"content": "Right", "is_correct": True, "position": 2},
            ],
        },
        session=sess,
    )
    sess.commit()

    job = create_or_get_regrade_job(correction.id, session=sess)
    process_regrade_job(job.id, actor=instructor_user, session=sess)

    sess.refresh(aq)
    assert aq.content_snapshot == aq_content_before
    assert aq.points_assigned == aq_points_before
    cs_keys_after = [cs.choice_key_snapshot for cs in aq.choice_snapshots]
    assert cs_keys_after == cs_keys_before

    sess.refresh(ans_record)
    assert ans_record.answer_version == ans_version_before


def test_T_REG_04_resumable_regrading_recovers_from_interruption(
    app: Flask,
    instructor_user: User,
    active_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """T-REG-04: Ngắt tiến trình chấm lại giữa chừng và khởi động lại
    -> Tự động phục hồi, tiếp tục xử lý các bài còn lại mà không gây trùng lặp.
    """
    sess: Session = db.session
    student1, student2 = enrolled_students

    q = create_question(
        instructor_user,
        active_course.id,
        {
            "content": "Resumable Regrade Question",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "default_points": 10.0,
            "choices": [
                {"content": "Option A", "is_correct": True, "position": 1},
                {"content": "Option B", "is_correct": False, "position": 2},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    sess.commit()

    asm = create_assessment(
        instructor_user,
        active_course.id,
        {"title": "Resumable Quiz", "assessment_type": "QUIZ", "attempt_limit": 1},
        session=sess,
    )
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": str(q.public_id), "points": 10.0},
        session=sess,
    )
    publish_assessment(instructor_user, asm.id, session=sess)

    # Student 1 takes attempt
    att1, tok1 = start_assessment_attempt(student1, asm.id, session=sess)
    aq1 = att1.attempt_questions[0]
    choice_b1 = next(cs for cs in aq1.choice_snapshots if cs.content_snapshot == "Option B")
    save_attempt_answer(
        actor=student1,
        attempt_id=att1.id,
        attempt_question_id=aq1.id,
        payload={
            "selected_choice_keys": [str(choice_b1.choice_key_snapshot)],
            "client_sequence": 1,
        },
        raw_lease_token=tok1,
        session=sess,
    )
    submit_assessment_attempt(student1, att1.id, idempotency_key=uuid.uuid4(), session=sess)

    # Student 2 takes attempt
    att2, tok2 = start_assessment_attempt(student2, asm.id, session=sess)
    aq2 = att2.attempt_questions[0]
    choice_b2 = next(cs for cs in aq2.choice_snapshots if cs.content_snapshot == "Option B")
    save_attempt_answer(
        actor=student2,
        attempt_id=att2.id,
        attempt_question_id=aq2.id,
        payload={
            "selected_choice_keys": [str(choice_b2.choice_key_snapshot)],
            "client_sequence": 1,
        },
        raw_lease_token=tok2,
        session=sess,
    )
    submit_assessment_attempt(student2, att2.id, idempotency_key=uuid.uuid4(), session=sess)

    # File correction
    _, correction = create_question_revision(
        instructor_user,
        q.id,
        {
            "content": "Resumable Regrade Question",
            "reason": "Option B is actually correct",
            "correction_type": "ANSWER_ONLY",
            "choices": [
                {"content": "Option A", "is_correct": False, "position": 1},
                {"content": "Option B", "is_correct": True, "position": 2},
            ],
        },
        session=sess,
    )
    sess.commit()

    job = create_or_get_regrade_job(correction.id, session=sess)
    assert job.total_items == 2

    # Process only 1 item (simulating partial processing before crash/interruption)
    process_regrade_job(job.id, batch_size=1, actor=instructor_user, session=sess)
    sess.refresh(job)
    assert job.processed_items == 1
    assert job.status == "RUNNING"

    # Worker recovers and runs full job
    process_regrade_job(job.id, actor=instructor_user, session=sess)
    sess.refresh(job)
    assert job.status == "COMPLETED"
    assert job.processed_items == 2

    # Both student attempts now have 10.0 points
    grade1 = sess.query(AttemptQuestionGrade).filter_by(attempt_question_id=aq1.id).first()
    grade2 = sess.query(AttemptQuestionGrade).filter_by(attempt_question_id=aq2.id).first()
    assert grade1.awarded_points == Decimal("10.0000")
    assert grade2.awarded_points == Decimal("10.0000")

    # Ensure each attempt has exactly 2 history records (1 initial submission + 1 regrade record)
    h1 = sess.query(AssessmentResultHistory).filter_by(attempt_id=att1.id).count()
    h2 = sess.query(AssessmentResultHistory).filter_by(attempt_id=att2.id).count()
    assert h1 == 2
    assert h2 == 2

    regrade_h1 = (
        sess.query(AssessmentResultHistory)
        .filter_by(attempt_id=att1.id, reason_code="REGRADE")
        .count()
    )
    regrade_h2 = (
        sess.query(AssessmentResultHistory)
        .filter_by(attempt_id=att2.id, reason_code="REGRADE")
        .count()
    )
    assert regrade_h1 == 1
    assert regrade_h2 == 1
