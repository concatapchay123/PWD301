"""API Integration Tests for Assessment Grading Engine & Manual Essay Evaluation (TASK-016).

Verifies end-to-end API workflows:
1. Pure objective quiz: start attempt -> save answers -> submit -> immediate GRADED
   -> GET /api/attempts/<id>/result.
2. Mixed assessment with essay: start attempt -> submit -> PENDING_GRADING ->
   instructor views pending list -> instructor views grading detail ->
   instructor submits manual grade -> attempt finalizes to GRADED -> student views finalized result.
3. Bounds checks on manual grading (negative points, points exceeding assigned max points).
4. Dual HTML/JSON support on instructor grading routes:
   (/instructor/assessments/<id>/grading/pending, /instructor/attempts/<id>/grading).
5. Regrade audit trail appending AttemptQuestionGradeHistory.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.attempt_regrade import (
    AttemptQuestionGradeHistory,
)
from pwd301.models.course import Course
from pwd301.models.identity import Role, User
from pwd301.services.assessment_service import (
    assign_question,
    create_assessment,
    create_section,
    publish_assessment,
)
from pwd301.services.attempt_service import (
    start_assessment_attempt,
)
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.enrollment_service import enroll_student
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
    u = register_user("admin_grading_api@example.com", "Password@123", "Admin User")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create instructor user."""
    u = register_user("inst_grading_api@example.com", "Password@123", "Course Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create student user."""
    u = register_user("student_grading_api@example.com", "Password@123", "Enrolled Student")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def published_course(
    app: Flask,
    instructor_user: User,
    admin_user: User,
) -> Course:
    """Create and publish a course owned by instructor."""
    c = create_course(
        instructor_user,
        {
            "course_code": "GRADE-API-101",
            "title": "Grading API Integration Course",
            "level": "INTERMEDIATE",
        },
    )
    change_course_status(instructor_user, c.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin_user, c.id, "APPROVED")
    change_course_status(admin_user, c.id, "PUBLISHED")
    db.session.commit()
    return c


@pytest.fixture
def enrolled_student(
    app: Flask,
    published_course: Course,
    student_user: User,
) -> None:
    """Enroll student into the published course."""
    enroll_student(student_user, published_course.id)


def _auth_headers(user: User) -> dict[str, str]:
    """Generate Bearer Authorization header for user."""
    tokens = create_token_pair(user)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


# ============================================================================
# 1. PURE OBJECTIVE QUIZ END-TO-END FLOW
# ============================================================================


def test_pure_objective_quiz_auto_grading_flow(
    app: Flask,
    client: FlaskClient,
    instructor_user: User,
    student_user: User,
    published_course: Course,
    enrolled_student: None,
) -> None:
    """End-to-end API test: Pure objective quiz auto-grades to GRADED and returns correct result."""
    sess: Session = db.session
    now = datetime.now(UTC)

    # 1. Instructor creates and publishes quiz
    assessment = create_assessment(
        instructor_user,
        published_course.id,
        {
            "title": "Objective Mastery Quiz",
            "assessment_type": "QUIZ",
            "score_release_policy": "IMMEDIATE",
            "time_limit_minutes": 45,
            "open_at": (now - timedelta(hours=1)).isoformat(),
            "close_at": (now + timedelta(hours=24)).isoformat(),
            "passing_percent": 60.0,
        },
        session=sess,
    )
    sec = create_section(instructor_user, assessment.id, {"title": "Section 1"}, session=sess)

    # Q1: Single Choice (10 pts)
    q1 = create_question(
        instructor_user,
        published_course.id,
        {
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "content": "What is 3 * 3?",
            "default_points": 10.0,
            "choices": [
                {"content": "6", "is_correct": False, "position": 1},
                {"content": "9", "is_correct": True, "position": 2},
            ],
        },
        session=sess,
    )
    assign_question(
        instructor_user,
        assessment.id,
        {"question_id": q1.id, "points": 10.0, "section_id": sec.id},
        session=sess,
    )

    # Q2: Short Answer (10 pts)
    q2 = create_question(
        instructor_user,
        published_course.id,
        {
            "question_type": "SHORT_ANSWER",
            "difficulty": "REMEMBER",
            "content": "Capital of Vietnam?",
            "default_points": 10.0,
            "accepted_answers": ["Hanoi", "Ha Noi"],
        },
        session=sess,
    )
    assign_question(
        instructor_user,
        assessment.id,
        {"question_id": q2.id, "points": 10.0, "section_id": sec.id},
        session=sess,
    )

    publish_assessment(instructor_user, assessment.id, session=sess)
    sess.commit()

    # 2. Student starts attempt via API
    start_resp = client.post(
        f"/api/assessments/{assessment.public_id}/attempts",
        headers=_auth_headers(student_user),
    )
    assert start_resp.status_code == 201
    start_data = start_resp.json
    attempt_id = start_data["attempt_id"]
    lease_token = start_data["lease_token"]

    # 3. Retrieve deliverable questions
    delivery_resp = client.get(
        f"/api/attempts/{attempt_id}",
        headers={**_auth_headers(student_user), "X-Lease-Token": lease_token},
    )
    assert delivery_resp.status_code == 200
    questions = delivery_resp.json["questions"]
    assert len(questions) == 2

    # Find questions
    sc_q = [q for q in questions if q["question_type"] == "SINGLE_CHOICE"][0]
    sa_q = [q for q in questions if q["question_type"] == "SHORT_ANSWER"][0]

    choice_9 = [c for c in sc_q["choices"] if c["content"] == "9"][0]

    # 4. Save answer for Single Choice Q
    ans1_resp = client.put(
        f"/api/attempts/{attempt_id}/answers/{sc_q['attempt_question_id']}",
        json={
            "client_sequence": 1,
            "selected_choice_keys": [choice_9["choice_key"]],
        },
        headers={**_auth_headers(student_user), "X-Lease-Token": lease_token},
    )
    assert ans1_resp.status_code == 200

    # 5. Save answer for Short Answer Q
    ans2_resp = client.put(
        f"/api/attempts/{attempt_id}/answers/{sa_q['attempt_question_id']}",
        json={
            "client_sequence": 2,
            "answer_text": "  ha noi  ",  # Normalized match
        },
        headers={**_auth_headers(student_user), "X-Lease-Token": lease_token},
    )
    assert ans2_resp.status_code == 200

    # 6. Submit attempt via API
    submit_key = str(uuid.uuid4())
    sub_resp = client.post(
        f"/api/attempts/{attempt_id}/submit",
        json={"submission_idempotency_key": submit_key},
        headers={**_auth_headers(student_user), "X-Lease-Token": lease_token},
    )
    assert sub_resp.status_code == 200
    sub_data = sub_resp.json
    assert sub_data["status"] == "GRADED"
    assert sub_data["is_idempotent_replay"] is False

    # 7. Student retrieves attempt result
    result_resp = client.get(
        f"/api/attempts/{attempt_id}/result",
        headers=_auth_headers(student_user),
    )
    assert result_resp.status_code == 200
    res = result_resp.json
    assert res["status"] == "GRADED"
    assert res["score_status"] == "RELEASED"
    assert res["raw_score"] == 20.0
    assert res["max_score"] == 20.0
    assert res["percent_score"] == 100.0
    assert res["passed"] is True
    assert len(res["questions"]) == 2


# ============================================================================
# 2. MIXED ASSESSMENT & MANUAL ESSAY EVALUATION FLOW
# ============================================================================


def test_mixed_quiz_essay_pending_manual_grading_flow(
    app: Flask,
    client: FlaskClient,
    instructor_user: User,
    student_user: User,
    published_course: Course,
    enrolled_student: None,
) -> None:
    """End-to-end API test: Mixed quiz enters PENDING_GRADING, instructor grades essay,
    transitions to GRADED.
    """
    sess: Session = db.session
    now = datetime.now(UTC)

    # 1. Instructor creates mixed quiz (1 Objective Q 10 pts, 1 Essay Q 20 pts)
    assessment = create_assessment(
        instructor_user,
        published_course.id,
        {
            "title": "Comprehensive Architecture Exam",
            "assessment_type": "FINAL",
            "score_release_policy": "IMMEDIATE",
            "time_limit_minutes": 60,
            "open_at": (now - timedelta(hours=1)).isoformat(),
            "close_at": (now + timedelta(hours=24)).isoformat(),
            "passing_percent": 70.0,
        },
        session=sess,
    )
    sec = create_section(instructor_user, assessment.id, {"title": "Main"}, session=sess)

    q1 = create_question(
        instructor_user,
        published_course.id,
        {
            "question_type": "TRUE_FALSE",
            "difficulty": "REMEMBER",
            "content": "Is SQL Server the primary DBMS?",
            "default_points": 10.0,
            "choices": [
                {"content": "True", "is_correct": True, "position": 1},
                {"content": "False", "is_correct": False, "position": 2},
            ],
        },
        session=sess,
    )
    assign_question(
        instructor_user,
        assessment.id,
        {"question_id": q1.id, "points": 10.0, "section_id": sec.id},
        session=sess,
    )

    q2 = create_question(
        instructor_user,
        published_course.id,
        {
            "question_type": "ESSAY",
            "difficulty": "APPLY",
            "content": "Explain idempotent API design under concurrent distributed requests.",
            "default_points": 20.0,
            "rubric": "Concurrency handling (10), Unique keys (5), Deterministic outcomes (5)",
        },
        session=sess,
    )
    assign_question(
        instructor_user,
        assessment.id,
        {"question_id": q2.id, "points": 20.0, "section_id": sec.id},
        session=sess,
    )

    publish_assessment(instructor_user, assessment.id, session=sess)
    sess.commit()

    # 2. Student starts and answers
    attempt, token = start_assessment_attempt(student_user, assessment.id, session=sess)
    aq_tf = [aq for aq in attempt.attempt_questions if aq.question_type_snapshot == "TRUE_FALSE"][0]
    aq_essay = [aq for aq in attempt.attempt_questions if aq.question_type_snapshot == "ESSAY"][0]

    c_true = [c for c in aq_tf.choice_snapshots if c.content_snapshot == "True"][0]

    # Save TF answer
    client.put(
        f"/api/attempts/{attempt.public_id}/answers/{aq_tf.public_id}",
        json={"client_sequence": 1, "selected_choice_keys": [str(c_true.choice_key_snapshot)]},
        headers={**_auth_headers(student_user), "X-Lease-Token": token},
    )

    # Save Essay answer
    essay_content = (
        "Idempotency keys ensure operations are executed at most once. Concurrent requests with "
        "the same idempotency key race on an atomic conditional lock."
    )
    client.put(
        f"/api/attempts/{attempt.public_id}/answers/{aq_essay.public_id}",
        json={"client_sequence": 2, "answer_text": essay_content},
        headers={**_auth_headers(student_user), "X-Lease-Token": token},
    )

    # 3. Student submits attempt
    sub_resp = client.post(
        f"/api/attempts/{attempt.public_id}/submit",
        json={"submission_idempotency_key": str(uuid.uuid4())},
        headers={**_auth_headers(student_user), "X-Lease-Token": token},
    )
    assert sub_resp.status_code == 200
    assert sub_resp.json["status"] == "PENDING_GRADING"

    # 4. Student result is initially SCORE_HIDDEN
    res_resp = client.get(
        f"/api/attempts/{attempt.public_id}/result",
        headers=_auth_headers(student_user),
    )
    assert res_resp.status_code == 200
    assert res_resp.json["score_status"] == "SCORE_HIDDEN"
    assert res_resp.json["status"] == "PENDING_GRADING"

    # 5. Instructor views pending grading list
    pending_resp = client.get(
        f"/instructor/assessments/{assessment.public_id}/grading/pending",
        headers=_auth_headers(instructor_user),
    )
    assert pending_resp.status_code == 200
    pending_list = pending_resp.json["attempts"]
    assert len(pending_list) == 1
    assert pending_list[0]["attempt_id"] == str(attempt.public_id)
    assert pending_list[0]["pending_essay_count"] == 1

    # 6. Instructor views attempt grading detail
    detail_resp = client.get(
        f"/instructor/attempts/{attempt.public_id}/grading",
        headers=_auth_headers(instructor_user),
    )
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json
    assert detail_data["attempt_id"] == str(attempt.public_id)
    assert len(detail_data["questions"]) == 2

    essay_item = [q for q in detail_data["questions"] if q["question_type"] == "ESSAY"][0]
    assert essay_item["student_answer_text"] == essay_content
    assert essay_item["grading_status"] == "PENDING"
    assert essay_item["points_assigned"] == 20.0

    # 7. Instructor submits manual essay grade: 18.0 / 20.0
    grade_resp = client.post(
        f"/api/attempts/{attempt.public_id}/grades/{aq_essay.public_id}",
        json={
            "awarded_points": 18.0,
            "feedback": "Comprehensive explanation of atomic locks and unique keys.",
        },
        headers=_auth_headers(instructor_user),
    )
    assert grade_resp.status_code == 200
    grade_data = grade_resp.json
    assert grade_data["awarded_points"] == 18.0
    assert grade_data["grading_status"] == "MANUAL_GRADED"
    assert grade_data["attempt_status"] == "GRADED"
    assert grade_data["is_finalized"] is True

    # 8. Instructor checks pending queue: now empty
    pending_after = client.get(
        f"/instructor/assessments/{assessment.public_id}/grading/pending",
        headers=_auth_headers(instructor_user),
    )
    assert pending_after.status_code == 200
    assert len(pending_after.json["attempts"]) == 0

    # 9. Student retrieves result: finalized score is visible
    final_resp = client.get(
        f"/api/attempts/{attempt.public_id}/result",
        headers=_auth_headers(student_user),
    )
    assert final_resp.status_code == 200
    final_data = final_resp.json
    assert final_data["status"] == "GRADED"
    assert final_data["score_status"] == "RELEASED"
    assert final_data["raw_score"] == 28.0  # 10 (objective) + 18 (essay)
    assert final_data["max_score"] == 30.0
    assert final_data["percent_score"] == pytest.approx(93.3333, abs=0.01)
    assert final_data["passed"] is True


# ============================================================================
# 3. MANUAL ESSAY GRADING BOUNDS CHECKS
# ============================================================================


def test_manual_essay_grading_invalid_score_bounds(
    app: Flask,
    client: FlaskClient,
    instructor_user: User,
    student_user: User,
    published_course: Course,
    enrolled_student: None,
) -> None:
    """Manual essay grading validates bounds (0 <= awarded_points <= points_assigned)."""
    sess: Session = db.session
    now = datetime.now(UTC)

    assessment = create_assessment(
        instructor_user,
        published_course.id,
        {
            "title": "Essay Bounds Assessment",
            "assessment_type": "PRACTICE",
            "time_limit_minutes": 60,
            "open_at": (now - timedelta(hours=1)).isoformat(),
            "close_at": (now + timedelta(hours=24)).isoformat(),
        },
        session=sess,
    )
    sec = create_section(instructor_user, assessment.id, {"title": "S1"}, session=sess)
    q = create_question(
        instructor_user,
        published_course.id,
        {
            "question_type": "ESSAY",
            "difficulty": "APPLY",
            "content": "Write an essay.",
            "default_points": 15.0,
        },
        session=sess,
    )
    assign_question(
        instructor_user,
        assessment.id,
        {"question_id": q.id, "points": 15.0, "section_id": sec.id},
        session=sess,
    )
    publish_assessment(instructor_user, assessment.id, session=sess)
    sess.commit()

    attempt, token = start_assessment_attempt(student_user, assessment.id, session=sess)
    aq = attempt.attempt_questions[0]

    # Cannot grade before submission
    resp_early = client.post(
        f"/api/attempts/{attempt.public_id}/grades/{aq.public_id}",
        json={"awarded_points": 10.0},
        headers=_auth_headers(instructor_user),
    )
    assert resp_early.status_code == 409

    # Submit attempt
    client.post(
        f"/api/attempts/{attempt.public_id}/submit",
        json={"submission_idempotency_key": str(uuid.uuid4())},
        headers={**_auth_headers(student_user), "X-Lease-Token": token},
    )

    # 1. Negative score rejected
    resp_neg = client.post(
        f"/api/attempts/{attempt.public_id}/grades/{aq.public_id}",
        json={"awarded_points": -5.0},
        headers=_auth_headers(instructor_user),
    )
    assert resp_neg.status_code in (400, 422)
    assert "negative" in str(resp_neg.json).lower()

    # 2. Exceeding max points (15.0) rejected
    resp_over = client.post(
        f"/api/attempts/{attempt.public_id}/grades/{aq.public_id}",
        json={"awarded_points": 20.0},
        headers=_auth_headers(instructor_user),
    )
    assert resp_over.status_code in (400, 422)
    assert "exceed" in str(resp_over.json).lower()


# ============================================================================
# 4. INSTRUCTOR ROUTES HTML AND JSON SUPPORT
# ============================================================================


def test_instructor_routes_html_and_json_support(
    app: Flask,
    client: FlaskClient,
    instructor_user: User,
    student_user: User,
    published_course: Course,
    enrolled_student: None,
) -> None:
    """Instructor routes return JSON when Accept: application/json is sent, or HTML otherwise."""
    sess: Session = db.session
    now = datetime.now(UTC)

    assessment = create_assessment(
        instructor_user,
        published_course.id,
        {
            "title": "Dual Representation Exam",
            "assessment_type": "PRACTICE",
            "time_limit_minutes": 60,
            "open_at": (now - timedelta(hours=1)).isoformat(),
            "close_at": (now + timedelta(hours=24)).isoformat(),
        },
        session=sess,
    )
    sec = create_section(instructor_user, assessment.id, {"title": "S1"}, session=sess)
    q = create_question(
        instructor_user,
        published_course.id,
        {
            "question_type": "ESSAY",
            "difficulty": "APPLY",
            "content": "Essay for HTML test.",
            "default_points": 10.0,
        },
        session=sess,
    )
    assign_question(
        instructor_user,
        assessment.id,
        {"question_id": q.id, "points": 10.0, "section_id": sec.id},
        session=sess,
    )
    publish_assessment(instructor_user, assessment.id, session=sess)
    sess.commit()

    attempt, token = start_assessment_attempt(student_user, assessment.id, session=sess)
    client.post(
        f"/api/attempts/{attempt.public_id}/submit",
        json={"submission_idempotency_key": str(uuid.uuid4())},
        headers={**_auth_headers(student_user), "X-Lease-Token": token},
    )

    # 1. JSON Request for Pending List
    resp_json = client.get(
        f"/instructor/assessments/{assessment.public_id}/grading/pending",
        headers={**_auth_headers(instructor_user), "Accept": "application/json"},
    )
    assert resp_json.status_code == 200
    assert "attempts" in resp_json.json

    # 2. HTML Request for Pending List (renders template or fallback)
    resp_html = client.get(
        f"/instructor/assessments/{assessment.public_id}/grading/pending",
        headers={**_auth_headers(instructor_user), "Accept": "text/html"},
    )
    assert resp_html.status_code == 200

    # 3. JSON Request for Attempt Grading Detail
    resp_detail_json = client.get(
        f"/instructor/attempts/{attempt.public_id}/grading",
        headers={**_auth_headers(instructor_user), "Accept": "application/json"},
    )
    assert resp_detail_json.status_code == 200
    assert "questions" in resp_detail_json.json

    # 4. HTML Request for Attempt Grading Detail
    resp_detail_html = client.get(
        f"/instructor/attempts/{attempt.public_id}/grading",
        headers={**_auth_headers(instructor_user), "Accept": "text/html"},
    )
    assert resp_detail_html.status_code == 200


# ============================================================================
# 5. REGRADE AUDIT TRAIL TRACKING
# ============================================================================


def test_multiple_regrade_history_tracking(
    app: Flask,
    client: FlaskClient,
    instructor_user: User,
    student_user: User,
    published_course: Course,
    enrolled_student: None,
) -> None:
    """Subsequent grade edits append history entries with reason_code='MANUAL_REVISION'."""
    sess: Session = db.session
    now = datetime.now(UTC)

    assessment = create_assessment(
        instructor_user,
        published_course.id,
        {
            "title": "History Tracking Exam",
            "assessment_type": "PRACTICE",
            "time_limit_minutes": 60,
            "open_at": (now - timedelta(hours=1)).isoformat(),
            "close_at": (now + timedelta(hours=24)).isoformat(),
        },
        session=sess,
    )
    sec = create_section(instructor_user, assessment.id, {"title": "S1"}, session=sess)
    q = create_question(
        instructor_user,
        published_course.id,
        {
            "question_type": "ESSAY",
            "difficulty": "APPLY",
            "content": "Essay for regrade test.",
            "default_points": 20.0,
        },
        session=sess,
    )
    assign_question(
        instructor_user,
        assessment.id,
        {"question_id": q.id, "points": 20.0, "section_id": sec.id},
        session=sess,
    )
    publish_assessment(instructor_user, assessment.id, session=sess)
    sess.commit()

    attempt, token = start_assessment_attempt(student_user, assessment.id, session=sess)
    aq = attempt.attempt_questions[0]
    client.post(
        f"/api/attempts/{attempt.public_id}/submit",
        json={"submission_idempotency_key": str(uuid.uuid4())},
        headers={**_auth_headers(student_user), "X-Lease-Token": token},
    )

    # Initial Grade: 12.0
    r1 = client.post(
        f"/api/attempts/{attempt.public_id}/grades/{aq.public_id}",
        json={"awarded_points": 12.0, "reason": "First review"},
        headers=_auth_headers(instructor_user),
    )
    assert r1.status_code == 200

    # Revision Grade: 16.5
    r2 = client.post(
        f"/api/attempts/{attempt.public_id}/grades/{aq.public_id}",
        json={"awarded_points": 16.5, "reason": "Second review after student appeal"},
        headers=_auth_headers(instructor_user),
    )
    assert r2.status_code == 200

    # Check Database Audit History
    sess.expire_all()
    history_records = (
        sess.query(AttemptQuestionGradeHistory)
        .filter(AttemptQuestionGradeHistory.attempt_question_id == aq.id)
        .order_by(AttemptQuestionGradeHistory.id.asc())
        .all()
    )

    # Initial automated grade was recorded upon submission + 2 manual revisions
    assert len(history_records) >= 3
    revisions = [h for h in history_records if h.reason_code == "MANUAL_REVISION"]
    assert len(revisions) == 2
    assert float(revisions[0].new_points) == 12.0
    assert float(revisions[1].new_points) == 16.5
    assert float(revisions[1].old_points) == 12.0
