"""Security & IDOR Negative Tests for Assessment Grading Engine & Manual Essay Evaluation.

TASK-016 Validates:
- Fail-closed Zero-Trust IDOR protection on attempt results and grading endpoints.
- Peer students in the same course receive ForbiddenError (403) accessing each other's results.
- Non-course instructors receive ForbiddenError (403) accessing grading detail, pending lists,
  or submitting grades.
- Students receive ForbiddenError (403) when attempting to call instructor grading endpoints.
- Non-course instructors receive ForbiddenError (403) when calling score release endpoints.
- Score release policies (AFTER_CLOSE, INSTRUCTOR_RELEASE) enforce score hiding for students.
- Answer visibility policies (NEVER, AFTER_CLOSE) enforce explanation / feedback hiding.
- ADR-002: Zero leakage of internal BIGINT PK/FK identifiers across all grading and result payloads.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course
from pwd301.models.identity import Role, User
from pwd301.services.assessment_service import (
    assign_question,
    create_assessment,
    create_section,
    publish_assessment,
    release_assessment_scores,
)
from pwd301.services.attempt_service import (
    get_attempt_result_for_student,
    grade_essay_question,
    save_attempt_answer,
    start_assessment_attempt,
    submit_assessment_attempt,
)
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.exceptions import ForbiddenError
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.question_bank_service import create_question
from pwd301.services.user_service import assign_role_to_user, register_user


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
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create administrator user."""
    u = register_user("admin_grading_idor@example.com", "Password@123", "Admin Grading")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def instructor_one(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create primary course instructor."""
    u = register_user("inst1_grading_idor@example.com", "Password@123", "Instructor One")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def instructor_two(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create separate instructor (no course rights)."""
    u = register_user("inst2_grading_idor@example.com", "Password@123", "Instructor Two")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_one(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create primary student who takes attempts."""
    u = register_user("student1_grading_idor@example.com", "Password@123", "Student One")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def student_two(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create peer student in same course."""
    u = register_user("student2_grading_idor@example.com", "Password@123", "Student Two")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def test_course(app: Flask, instructor_one: User, admin_user: User) -> Course:
    """Create and publish course managed by instructor_one."""
    c = create_course(
        instructor_one,
        {
            "course_code": "SEC-GRADE-101",
            "title": "Grading Security Course",
            "level": "BEGINNER",
        },
    )
    change_course_status(instructor_one, c.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin_user, c.id, "APPROVED")
    change_course_status(admin_user, c.id, "PUBLISHED")
    db.session.commit()
    return c


@pytest.fixture
def enrolled_students(
    app: Flask,
    test_course: Course,
    student_one: User,
    student_two: User,
) -> None:
    """Enroll both students into test_course."""
    enroll_student(student_one, test_course.id)
    enroll_student(student_two, test_course.id)


def _auth_headers(user: User) -> dict[str, str]:
    """Generate Bearer Authorization header for user."""
    tokens = create_token_pair(user)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def _assert_no_internal_bigints(obj: Any, path: str = "") -> None:
    """ADR-002: Recursively ensure no internal integer PKs are exposed."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            current_path = f"{path}.{k}" if path else k
            if k == "id" or k.endswith("_id"):
                assert not isinstance(v, int), (
                    f"ADR-002 Violation at '{current_path}': integer ID '{v}' exposed."
                )
                if v is not None:
                    try:
                        uuid.UUID(str(v))
                    except ValueError:
                        pytest.fail(
                            f"ADR-002 Violation at '{current_path}': "
                            f"ID '{v}' is not a valid UUIDv4."
                        )
            _assert_no_internal_bigints(v, current_path)
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            _assert_no_internal_bigints(item, f"{path}[{idx}]")


# ============================================================================
# 1. PEER STUDENT IDOR
# ============================================================================


def test_peer_student_cannot_view_attempt_result(
    app: Flask,
    client: FlaskClient,
    test_course: Course,
    instructor_one: User,
    student_one: User,
    student_two: User,
    enrolled_students: None,
) -> None:
    """Student two cannot view Student one's attempt results (service and API 403)."""
    sess: Session = db.session
    now = datetime.now(UTC)

    assessment = create_assessment(
        instructor_one,
        test_course.id,
        {
            "title": "Peer IDOR Quiz",
            "assessment_type": "QUIZ",
            "time_limit_minutes": 30,
            "open_at": (now - timedelta(hours=1)).isoformat(),
            "close_at": (now + timedelta(hours=24)).isoformat(),
            "passing_score": 50.0,
        },
        session=sess,
    )
    sec = create_section(instructor_one, assessment.id, {"title": "S1"}, session=sess)
    q = create_question(
        instructor_one,
        test_course.id,
        {
            "question_type": "TRUE_FALSE",
            "difficulty": "REMEMBER",
            "content": "Is security vital?",
            "default_points": 10.0,
            "choices": [
                {"content": "True", "is_correct": True, "position": 1},
                {"content": "False", "is_correct": False, "position": 2},
            ],
        },
        session=sess,
    )
    assign_question(
        instructor_one,
        assessment.id,
        {"question_id": q.id, "points": 10.0, "section_id": sec.id},
        session=sess,
    )
    publish_assessment(instructor_one, assessment.id, session=sess)
    sess.commit()

    # Student 1 takes and submits
    attempt, token = start_assessment_attempt(student_one, assessment.id, session=sess)
    submit_assessment_attempt(
        actor=student_one,
        attempt_id=attempt.id,
        idempotency_key=uuid.uuid4(),
        raw_lease_token=token,
        session=sess,
    )

    # 1. Service Level: Student 2 calling get_attempt_result_for_student -> ForbiddenError
    with pytest.raises(ForbiddenError):
        get_attempt_result_for_student(student_two, attempt.id, session=sess)

    # 2. API Level: Student 2 calling GET /api/attempts/<id>/result -> 403
    resp = client.get(
        f"/api/attempts/{attempt.public_id}/result",
        headers=_auth_headers(student_two),
    )
    assert resp.status_code == 403
    assert resp.json["error"]["code"] in ("FORBIDDEN", "AUTHORIZATION_ERROR")


# ============================================================================
# 2. NON-OWNER INSTRUCTOR IDOR
# ============================================================================


def test_non_owner_instructor_cannot_grade_or_view_attempt(
    app: Flask,
    client: FlaskClient,
    test_course: Course,
    instructor_one: User,
    instructor_two: User,
    student_one: User,
    enrolled_students: None,
) -> None:
    """Instructor two (not managing test_course) cannot view or grade attempts."""
    sess: Session = db.session
    now = datetime.now(UTC)

    assessment = create_assessment(
        instructor_one,
        test_course.id,
        {
            "title": "Essay Evaluation",
            "assessment_type": "PRACTICE",
            "time_limit_minutes": 60,
            "open_at": (now - timedelta(hours=1)).isoformat(),
            "close_at": (now + timedelta(hours=24)).isoformat(),
        },
        session=sess,
    )
    sec = create_section(instructor_one, assessment.id, {"title": "S1"}, session=sess)
    q = create_question(
        instructor_one,
        test_course.id,
        {
            "question_type": "ESSAY",
            "difficulty": "APPLY",
            "content": "Explain zero-trust architecture.",
            "default_points": 20.0,
            "rubric": "Principle of least privilege.",
        },
        session=sess,
    )
    assign_question(
        instructor_one,
        assessment.id,
        {"question_id": q.id, "points": 20.0, "section_id": sec.id},
        session=sess,
    )
    publish_assessment(instructor_one, assessment.id, session=sess)
    sess.commit()

    attempt, token = start_assessment_attempt(student_one, assessment.id, session=sess)
    aq = attempt.attempt_questions[0]
    submit_assessment_attempt(
        actor=student_one,
        attempt_id=attempt.id,
        idempotency_key=uuid.uuid4(),
        raw_lease_token=token,
        session=sess,
    )

    # 1. Service Level: Instructor two cannot grade essay
    with pytest.raises(ForbiddenError):
        grade_essay_question(
            actor=instructor_two,
            attempt_id=attempt.id,
            attempt_question_id=aq.id,
            awarded_points=15.0,
            session=sess,
        )

    # 2. API Level: Instructor two cannot call POST /api/attempts/<id>/grades/<qid> -> 403
    resp = client.post(
        f"/api/attempts/{attempt.public_id}/grades/{aq.public_id}",
        json={"awarded_points": 15.0, "reason": "Unauthorized grading attempt"},
        headers=_auth_headers(instructor_two),
    )
    assert resp.status_code == 403

    # 3. API Level: Instructor two cannot view pending grading list
    resp_pending = client.get(
        f"/instructor/assessments/{assessment.public_id}/grading/pending",
        headers=_auth_headers(instructor_two),
    )
    assert resp_pending.status_code == 403

    # 4. API Level: Instructor two cannot view attempt grading detail
    resp_detail = client.get(
        f"/instructor/attempts/{attempt.public_id}/grading",
        headers=_auth_headers(instructor_two),
    )
    assert resp_detail.status_code == 403


# ============================================================================
# 3. STUDENT CALLING GRADING ENDPOINT
# ============================================================================


def test_student_cannot_call_manual_grading_endpoints(
    app: Flask,
    client: FlaskClient,
    test_course: Course,
    instructor_one: User,
    student_one: User,
    enrolled_students: None,
) -> None:
    """Student attempting to grade an essay receives 403 Forbidden."""
    sess: Session = db.session
    now = datetime.now(UTC)

    assessment = create_assessment(
        instructor_one,
        test_course.id,
        {
            "title": "Student Grading Attempt",
            "assessment_type": "PRACTICE",
            "time_limit_minutes": 60,
            "open_at": (now - timedelta(hours=1)).isoformat(),
            "close_at": (now + timedelta(hours=24)).isoformat(),
        },
        session=sess,
    )
    sec = create_section(instructor_one, assessment.id, {"title": "S1"}, session=sess)
    q = create_question(
        instructor_one,
        test_course.id,
        {
            "question_type": "ESSAY",
            "difficulty": "APPLY",
            "content": "Discuss security principles.",
            "default_points": 10.0,
        },
        session=sess,
    )
    assign_question(
        instructor_one,
        assessment.id,
        {"question_id": q.id, "points": 10.0, "section_id": sec.id},
        session=sess,
    )
    publish_assessment(instructor_one, assessment.id, session=sess)
    sess.commit()

    attempt, token = start_assessment_attempt(student_one, assessment.id, session=sess)
    aq = attempt.attempt_questions[0]
    submit_assessment_attempt(
        actor=student_one,
        attempt_id=attempt.id,
        idempotency_key=uuid.uuid4(),
        raw_lease_token=token,
        session=sess,
    )

    # Student attempts self-grading via API
    resp = client.post(
        f"/api/attempts/{attempt.public_id}/grades/{aq.public_id}",
        json={"awarded_points": 10.0, "reason": "Awarding myself full credit"},
        headers=_auth_headers(student_one),
    )
    assert resp.status_code == 403


# ============================================================================
# 4. NON-OWNER INSTRUCTOR SCORE RELEASE IDOR
# ============================================================================


def test_non_owner_instructor_cannot_release_scores(
    app: Flask,
    client: FlaskClient,
    test_course: Course,
    instructor_one: User,
    instructor_two: User,
) -> None:
    """Non-managing instructor cannot trigger score release."""
    sess: Session = db.session
    now = datetime.now(UTC)

    assessment = create_assessment(
        instructor_one,
        test_course.id,
        {
            "title": "Release Scores Quiz",
            "assessment_type": "QUIZ",
            "score_release_policy": "INSTRUCTOR_RELEASE",
            "time_limit_minutes": 30,
            "open_at": (now - timedelta(hours=1)).isoformat(),
            "close_at": (now + timedelta(hours=24)).isoformat(),
        },
        session=sess,
    )
    sec = create_section(instructor_one, assessment.id, {"title": "S1"}, session=sess)
    q = create_question(
        instructor_one,
        test_course.id,
        {
            "question_type": "TRUE_FALSE",
            "difficulty": "REMEMBER",
            "content": "Is release score tested?",
            "default_points": 10.0,
            "choices": [
                {"content": "True", "is_correct": True, "position": 1},
                {"content": "False", "is_correct": False, "position": 2},
            ],
        },
        session=sess,
    )
    assign_question(
        instructor_one,
        assessment.id,
        {"question_id": q.id, "points": 10.0, "section_id": sec.id},
        session=sess,
    )
    publish_assessment(instructor_one, assessment.id, session=sess)
    sess.commit()

    # Service Level: ForbiddenError
    with pytest.raises(ForbiddenError):
        release_assessment_scores(instructor_two, assessment.id, session=sess)

    # API Level: 403 Forbidden
    resp = client.post(
        f"/api/assessments/{assessment.public_id}/release-scores",
        headers=_auth_headers(instructor_two),
    )
    assert resp.status_code == 403


# ============================================================================
# 5. SCORE RELEASE POLICY (AFTER_CLOSE)
# ============================================================================


def test_score_release_policy_after_close(
    app: Flask,
    client: FlaskClient,
    test_course: Course,
    instructor_one: User,
    student_one: User,
    enrolled_students: None,
) -> None:
    """AFTER_CLOSE hides score before close_at and reveals after close_at."""
    sess: Session = db.session
    now = datetime.now(UTC)

    assessment = create_assessment(
        instructor_one,
        test_course.id,
        {
            "title": "After Close Quiz",
            "assessment_type": "QUIZ",
            "score_release_policy": "AFTER_CLOSE",
            "time_limit_minutes": 30,
            "open_at": (now - timedelta(hours=2)).isoformat(),
            "close_at": (now + timedelta(hours=2)).isoformat(),
            "passing_percent": 50.0,
        },
        session=sess,
    )
    sec = create_section(instructor_one, assessment.id, {"title": "S1"}, session=sess)
    q = create_question(
        instructor_one,
        test_course.id,
        {
            "question_type": "TRUE_FALSE",
            "difficulty": "REMEMBER",
            "content": "Is 10 > 5?",
            "default_points": 10.0,
            "choices": [
                {"content": "True", "is_correct": True, "position": 1},
                {"content": "False", "is_correct": False, "position": 2},
            ],
        },
        session=sess,
    )
    assign_question(
        instructor_one,
        assessment.id,
        {"question_id": q.id, "points": 10.0, "section_id": sec.id},
        session=sess,
    )
    publish_assessment(instructor_one, assessment.id, session=sess)
    sess.commit()

    attempt, token = start_assessment_attempt(student_one, assessment.id, session=sess)
    aq = attempt.attempt_questions[0]
    c_true = [c for c in aq.choice_snapshots if c.content_snapshot == "True"][0]

    save_attempt_answer(
        actor=student_one,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        payload={"client_sequence": 1, "selected_choice_keys": [str(c_true.choice_key_snapshot)]},
        raw_lease_token=token,
        session=sess,
    )
    submit_assessment_attempt(
        actor=student_one,
        attempt_id=attempt.id,
        idempotency_key=uuid.uuid4(),
        raw_lease_token=token,
        session=sess,
    )

    # 1. Before close_at: student gets SCORE_HIDDEN
    resp = client.get(
        f"/api/attempts/{attempt.public_id}/result",
        headers=_auth_headers(student_one),
    )
    assert resp.status_code == 200
    data = resp.json
    assert data["score_status"] == "SCORE_HIDDEN"
    assert data["raw_score"] is None
    assert data["percent_score"] is None
    assert data["passed"] is None
    assert data["questions"] is None

    # 2. Advance close_at to the past
    assessment.close_at = now - timedelta(minutes=5)
    sess.commit()

    # Student queries again: score is now released
    resp_after = client.get(
        f"/api/attempts/{attempt.public_id}/result",
        headers=_auth_headers(student_one),
    )
    assert resp_after.status_code == 200
    data_after = resp_after.json
    assert data_after["score_status"] == "RELEASED"
    assert data_after["raw_score"] == 10.0
    assert data_after["percent_score"] == 100.0
    assert data_after["passed"] is True


# ============================================================================
# 6. SCORE RELEASE POLICY (INSTRUCTOR_RELEASE)
# ============================================================================


def test_score_release_policy_instructor_release(
    app: Flask,
    client: FlaskClient,
    test_course: Course,
    instructor_one: User,
    student_one: User,
    enrolled_students: None,
) -> None:
    """INSTRUCTOR_RELEASE hides score until instructor calls release endpoint."""
    sess: Session = db.session
    now = datetime.now(UTC)

    assessment = create_assessment(
        instructor_one,
        test_course.id,
        {
            "title": "Manual Release Quiz",
            "assessment_type": "QUIZ",
            "score_release_policy": "INSTRUCTOR_RELEASE",
            "time_limit_minutes": 30,
            "open_at": (now - timedelta(hours=1)).isoformat(),
            "close_at": (now + timedelta(hours=24)).isoformat(),
            "passing_percent": 50.0,
        },
        session=sess,
    )
    sec = create_section(instructor_one, assessment.id, {"title": "S1"}, session=sess)
    q = create_question(
        instructor_one,
        test_course.id,
        {
            "question_type": "TRUE_FALSE",
            "difficulty": "REMEMBER",
            "content": "Is Python interpreted?",
            "default_points": 10.0,
            "choices": [
                {"content": "True", "is_correct": True, "position": 1},
                {"content": "False", "is_correct": False, "position": 2},
            ],
        },
        session=sess,
    )
    assign_question(
        instructor_one,
        assessment.id,
        {"question_id": q.id, "points": 10.0, "section_id": sec.id},
        session=sess,
    )
    publish_assessment(instructor_one, assessment.id, session=sess)
    sess.commit()

    attempt, token = start_assessment_attempt(student_one, assessment.id, session=sess)
    aq = attempt.attempt_questions[0]
    c_true = [c for c in aq.choice_snapshots if c.content_snapshot == "True"][0]

    save_attempt_answer(
        actor=student_one,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        payload={"client_sequence": 1, "selected_choice_keys": [str(c_true.choice_key_snapshot)]},
        raw_lease_token=token,
        session=sess,
    )
    submit_assessment_attempt(
        actor=student_one,
        attempt_id=attempt.id,
        idempotency_key=uuid.uuid4(),
        raw_lease_token=token,
        session=sess,
    )

    # Advance close_at to past
    assessment.close_at = now - timedelta(minutes=5)
    sess.commit()

    # 1. Initially hidden even though assessment closed
    resp = client.get(
        f"/api/attempts/{attempt.public_id}/result",
        headers=_auth_headers(student_one),
    )
    assert resp.status_code == 200
    assert resp.json["score_status"] == "SCORE_HIDDEN"

    # 2. Instructor releases scores
    rel_resp = client.post(
        f"/api/assessments/{assessment.public_id}/release-scores",
        headers=_auth_headers(instructor_one),
    )
    assert rel_resp.status_code == 200
    assert rel_resp.json["released_count"] == 1

    # 3. Student can now see scores
    resp_after = client.get(
        f"/api/attempts/{attempt.public_id}/result",
        headers=_auth_headers(student_one),
    )
    assert resp_after.status_code == 200
    assert resp_after.json["score_status"] == "RELEASED"
    assert resp_after.json["raw_score"] == 10.0


# ============================================================================
# 7. ANSWER VISIBILITY POLICY (NEVER)
# ============================================================================


def test_answer_visibility_policy_never(
    app: Flask,
    client: FlaskClient,
    test_course: Course,
    instructor_one: User,
    student_one: User,
    enrolled_students: None,
) -> None:
    """NEVER policy strips question breakdowns and explanations completely."""
    sess: Session = db.session
    now = datetime.now(UTC)

    assessment = create_assessment(
        instructor_one,
        test_course.id,
        {
            "title": "Secret Answers Quiz",
            "assessment_type": "QUIZ",
            "score_release_policy": "IMMEDIATE",
            "answer_visibility_policy": "NEVER",
            "time_limit_minutes": 30,
            "open_at": (now - timedelta(hours=1)).isoformat(),
            "close_at": (now + timedelta(hours=24)).isoformat(),
        },
        session=sess,
    )
    sec = create_section(instructor_one, assessment.id, {"title": "S1"}, session=sess)
    q = create_question(
        instructor_one,
        test_course.id,
        {
            "question_type": "TRUE_FALSE",
            "difficulty": "REMEMBER",
            "content": "Classified question.",
            "default_points": 10.0,
            "explanation": "Top secret explanation text.",
            "choices": [
                {"content": "True", "is_correct": True, "position": 1},
                {"content": "False", "is_correct": False, "position": 2},
            ],
        },
        session=sess,
    )
    assign_question(
        instructor_one,
        assessment.id,
        {"question_id": q.id, "points": 10.0, "section_id": sec.id},
        session=sess,
    )
    publish_assessment(instructor_one, assessment.id, session=sess)
    sess.commit()

    attempt, token = start_assessment_attempt(student_one, assessment.id, session=sess)
    submit_assessment_attempt(
        actor=student_one,
        attempt_id=attempt.id,
        idempotency_key=uuid.uuid4(),
        raw_lease_token=token,
        session=sess,
    )

    resp = client.get(
        f"/api/attempts/{attempt.public_id}/result",
        headers=_auth_headers(student_one),
    )
    assert resp.status_code == 200
    data = resp.json
    assert data["score_status"] == "RELEASED"
    assert data["answer_visibility_policy"] == "NEVER"
    for q in data["questions"]:
        assert "explanation" not in q
        assert "selected_choice_keys" not in q
        assert "feedback" not in q


def test_answer_visibility_policy_after_close(
    app: Flask,
    client: FlaskClient,
    test_course: Course,
    instructor_one: User,
    student_one: User,
    enrolled_students: None,
) -> None:
    """AFTER_CLOSE policy hides explanations before close_at, reveals after close_at."""
    sess: Session = db.session
    now = datetime.now(UTC)

    assessment = create_assessment(
        instructor_one,
        test_course.id,
        {
            "title": "Visibility After Close Quiz",
            "assessment_type": "QUIZ",
            "score_release_policy": "IMMEDIATE",
            "answer_visibility_policy": "AFTER_CLOSE",
            "time_limit_minutes": 30,
            "open_at": (now - timedelta(hours=1)).isoformat(),
            "close_at": (now + timedelta(hours=24)).isoformat(),
        },
        session=sess,
    )
    sec = create_section(instructor_one, assessment.id, {"title": "S1"}, session=sess)
    q = create_question(
        instructor_one,
        test_course.id,
        {
            "question_type": "TRUE_FALSE",
            "difficulty": "REMEMBER",
            "content": "Water is H2O.",
            "default_points": 10.0,
            "explanation": "Chemical formula for water is H2O.",
            "choices": [
                {"content": "True", "is_correct": True, "position": 1},
                {"content": "False", "is_correct": False, "position": 2},
            ],
        },
        session=sess,
    )
    assign_question(
        instructor_one,
        assessment.id,
        {"question_id": q.id, "points": 10.0, "section_id": sec.id},
        session=sess,
    )
    publish_assessment(instructor_one, assessment.id, session=sess)
    sess.commit()

    attempt, token = start_assessment_attempt(student_one, assessment.id, session=sess)
    aq = attempt.attempt_questions[0]
    choice_true = [c for c in aq.choice_snapshots if c.content_snapshot == "True"][0]
    save_attempt_answer(
        actor=student_one,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        payload={
            "client_sequence": 1,
            "client_change_id": str(uuid.uuid4()),
            "selected_choice_keys": [str(choice_true.choice_key_snapshot)],
        },
        raw_lease_token=token,
        session=sess,
    )
    submit_assessment_attempt(
        actor=student_one,
        attempt_id=attempt.id,
        idempotency_key=uuid.uuid4(),
        raw_lease_token=token,
        session=sess,
    )

    # 1. Before close_at: score is released, but answers/explanations are hidden
    resp1 = client.get(
        f"/api/attempts/{attempt.public_id}/result",
        headers=_auth_headers(student_one),
    )
    assert resp1.status_code == 200
    data1 = resp1.json
    assert data1["score_status"] == "RELEASED"
    for q_data in data1["questions"]:
        assert "explanation" not in q_data
        assert "selected_choice_keys" not in q_data

    # 2. Advance past close_at: explanations and selected choices are visible
    assessment.close_at = now - timedelta(minutes=5)
    sess.commit()

    resp2 = client.get(
        f"/api/attempts/{attempt.public_id}/result",
        headers=_auth_headers(student_one),
    )
    assert resp2.status_code == 200
    data2 = resp2.json
    assert data2["score_status"] == "RELEASED"
    for q_data in data2["questions"]:
        assert "explanation" in q_data
        assert q_data["explanation"] == "Chemical formula for water is H2O."
        assert "selected_choice_keys" in q_data


# ============================================================================
# 8. ADR-002 BIGINT MASKING COMPLIANCE
# ============================================================================


def test_adr002_bigint_masking_in_grading_and_results(
    app: Flask,
    client: FlaskClient,
    test_course: Course,
    instructor_one: User,
    student_one: User,
    enrolled_students: None,
) -> None:
    """ADR-002 verification: All grading and result endpoints must not expose BIGINT PKs."""
    sess: Session = db.session
    now = datetime.now(UTC)

    assessment = create_assessment(
        instructor_one,
        test_course.id,
        {
            "title": "ADR-002 Compliance Test",
            "assessment_type": "PRACTICE",
            "score_release_policy": "IMMEDIATE",
            "time_limit_minutes": 60,
            "open_at": (now - timedelta(hours=1)).isoformat(),
            "close_at": (now + timedelta(hours=24)).isoformat(),
        },
        session=sess,
    )
    sec = create_section(instructor_one, assessment.id, {"title": "S1"}, session=sess)
    q = create_question(
        instructor_one,
        test_course.id,
        {
            "question_type": "ESSAY",
            "difficulty": "APPLY",
            "content": "Explain ADR-002 BigInt Masking.",
            "default_points": 10.0,
        },
        session=sess,
    )
    assign_question(
        instructor_one,
        assessment.id,
        {"question_id": q.id, "points": 10.0, "section_id": sec.id},
        session=sess,
    )
    publish_assessment(instructor_one, assessment.id, session=sess)
    sess.commit()

    attempt, token = start_assessment_attempt(student_one, assessment.id, session=sess)
    aq = attempt.attempt_questions[0]
    submit_assessment_attempt(
        actor=student_one,
        attempt_id=attempt.id,
        idempotency_key=uuid.uuid4(),
        raw_lease_token=token,
        session=sess,
    )

    # 1. Check Pending Grading Queue Response
    resp_pending = client.get(
        f"/instructor/assessments/{assessment.public_id}/grading/pending",
        headers=_auth_headers(instructor_one),
    )
    assert resp_pending.status_code == 200
    _assert_no_internal_bigints(resp_pending.json)

    # 2. Check Attempt Grading Detail Response
    resp_detail = client.get(
        f"/instructor/attempts/{attempt.public_id}/grading",
        headers=_auth_headers(instructor_one),
    )
    assert resp_detail.status_code == 200
    _assert_no_internal_bigints(resp_detail.json)

    # 3. Check Manual Grade Submission Response
    resp_grade = client.post(
        f"/api/attempts/{attempt.public_id}/grades/{aq.public_id}",
        json={"awarded_points": 9.5, "reason": "Accurate ADR-002 explanation"},
        headers=_auth_headers(instructor_one),
    )
    assert resp_grade.status_code == 200
    _assert_no_internal_bigints(resp_grade.json)

    # 4. Check Student Attempt Result Response
    resp_result = client.get(
        f"/api/attempts/{attempt.public_id}/result",
        headers=_auth_headers(student_one),
    )
    assert resp_result.status_code == 200
    _assert_no_internal_bigints(resp_result.json)
