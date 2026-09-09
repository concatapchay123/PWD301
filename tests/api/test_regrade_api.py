"""API integration tests for Regrading Engine & Score History (TASK-017).

Validates:
- Complete end-to-end regrading flow via REST API with JWT authentication:
  - Student attempt submission and initial scoring.
  - Question revision creation with ANSWER_ONLY and CONTENT_OR_CHOICES.
  - Regrade trigger endpoint: POST /api/assessments/<id>/regrade.
  - Regrade job polling endpoint: GET /api/regrade-jobs/<job_id>.
  - Regrade job retry endpoint: POST /api/regrade-jobs/<job_id>/retry.
  - Attempt grade history endpoint: GET /api/attempts/<attempt_id>/grade-history.
- Instructor web views session-based routes:
  - POST /instructor/assessments/<id>/regrade
  - GET /instructor/regrade-jobs/<job_id>
  - POST /instructor/regrade-jobs/<job_id>/retry
- Strict adherence to ADR-002 (zero BIGINT PK exposure in all JSON payloads).
"""

from __future__ import annotations

import uuid
from decimal import Decimal
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
)
from pwd301.services.attempt_service import (
    save_attempt_answer,
    start_assessment_attempt,
    submit_assessment_attempt,
)
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.question_bank_service import (
    create_question,
    create_question_revision,
)
from pwd301.services.regrade_worker import (
    create_or_get_regrade_job,
)
from pwd301.services.user_service import assign_role_to_user, register_user
from tests.conftest import login_web_user


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
    u = register_user(
        f"admin_regrade_api_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Admin"
    )
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create instructor user."""
    u = register_user(
        f"inst_regrade_api_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Instructor"
    )
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create student user."""
    u = register_user(
        f"stud_regrade_api_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Student"
    )
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def test_course(app: Flask, instructor_user: User, admin_user: User) -> Course:
    """Create and publish course."""
    c = create_course(
        instructor_user,
        {
            "course_code": f"API-RG-{uuid.uuid4().hex[:4].upper()}",
            "title": "API Regrade Test Course",
            "description": "Course for testing regrading REST and Web APIs",
            "category": "Testing",
            "difficulty": "BEGINNER",
        },
    )
    change_course_status(instructor_user, c.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin_user, c.id, "APPROVED")
    change_course_status(admin_user, c.id, "PUBLISHED")
    db.session.commit()
    return c


def _auth_headers(user: User) -> dict[str, str]:
    """Generate Bearer Authorization header."""
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
# 1. REST API: ANSWER_ONLY REGRADING LIFECYCLE
# ============================================================================


def test_regrade_api_answer_only_lifecycle(
    client: FlaskClient,
    instructor_user: User,
    student_user: User,
    test_course: Course,
) -> None:
    """Test full ANSWER_ONLY regrade lifecycle via REST API endpoints."""
    sess: Session = db.session
    enroll_student(student_user, test_course.id)

    # 1. Create Question with Option A = correct, Option B = incorrect
    q = create_question(
        instructor_user,
        test_course.id,
        {
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "content": "Which is correct?",
            "choices": [
                {"content": "A", "is_correct": True, "position": 1},
                {"content": "B", "is_correct": False, "position": 2},
            ],
        },
    )
    c_a = [c for c in q.current_revision.choices if c.content == "A"][0]
    c_b = [c for c in q.current_revision.choices if c.content == "B"][0]

    # 2. Create Assessment & Publish
    asm = create_assessment(
        instructor_user,
        test_course.id,
        {
            "title": "API Quiz 1",
            "assessment_type": "QUIZ",
            "passing_percent": 50.0,
            "score_release_policy": "IMMEDIATE",
        },
    )
    sec = create_section(instructor_user, asm.id, {"title": "Main", "position": 1})
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": q.id, "section_id": sec.id, "position": 1, "points_assigned": 10.0},
    )
    publish_assessment(instructor_user, asm.id)

    # 3. Student takes test and selects Option B (initially wrong -> 0 pts)
    att, lease = start_assessment_attempt(student_user, asm.id)
    aq = att.attempt_questions[0]
    save_attempt_answer(
        student_user,
        str(att.public_id),
        str(aq.public_id),
        {"client_sequence": 1, "selected_choice_keys": [str(c_b.choice_key)]},
        raw_lease_token=lease,
    )
    submit_assessment_attempt(student_user, str(att.public_id), raw_lease_token=lease)

    # Student initial score is 0
    sess.refresh(att)
    assert att.result.raw_score == Decimal("0.0000")

    # 4. Instructor discovers B is actually correct, creates revision with ANSWER_ONLY
    new_rev, corr = create_question_revision(
        instructor_user,
        q.id,
        {
            "change_type": "ANSWER_CHANGE",
            "correction_type": "ANSWER_ONLY",
            "change_reason": "Answer key fix: B is correct",
            "choices": [
                {
                    "choice_key": str(c_a.choice_key),
                    "content": "A",
                    "is_correct": False,
                    "position": 1,
                },
                {
                    "choice_key": str(c_b.choice_key),
                    "content": "B",
                    "is_correct": True,
                    "position": 2,
                },
            ],
        },
    )

    # 5. Instructor calls POST /api/assessments/<assessment_id>/regrade
    inst_headers = _auth_headers(instructor_user)
    resp_trigger = client.post(
        f"/api/assessments/{asm.public_id}/regrade",
        headers=inst_headers,
        json={"reason": "Manual sync regrade run"},
    )
    assert resp_trigger.status_code == 200
    trigger_data = resp_trigger.get_json()
    assert "jobs" in trigger_data
    assert len(trigger_data["jobs"]) >= 1
    job_id = trigger_data["jobs"][0]["job_id"]
    _assert_no_internal_bigints(trigger_data)

    # 6. Instructor polls GET /api/regrade-jobs/<job_id>
    resp_job = client.get(f"/api/regrade-jobs/{job_id}", headers=inst_headers)
    assert resp_job.status_code == 200
    job_data = resp_job.get_json()
    assert job_data["job_id"] == job_id
    assert job_data["status"] == "COMPLETED"
    assert job_data["processed_items"] == 1
    assert job_data["changed_results"] == 1
    assert len(job_data["items"]) == 1
    _assert_no_internal_bigints(job_data)

    # 7. Student checks GET /api/attempts/<attempt_id>/grade-history
    stud_headers = _auth_headers(student_user)
    resp_hist = client.get(f"/api/attempts/{att.public_id}/grade-history", headers=stud_headers)
    assert resp_hist.status_code == 200
    hist_data = resp_hist.get_json()
    _assert_no_internal_bigints(hist_data)

    assert hist_data["attempt_id"] == str(att.public_id)

    # Verify result history
    assert "overall_history" in hist_data
    regrade_entries = [h for h in hist_data["overall_history"] if h["reason_code"] == "REGRADE"]
    assert len(regrade_entries) == 1
    assert regrade_entries[0]["old_score"] == 0.0
    assert regrade_entries[0]["new_score"] == 10.0

    # Verify question grade history
    assert "question_history" in hist_data
    auto_q_entries = [
        qh for qh in hist_data["question_history"] if qh["reason_code"] == "AUTO_REGRADE"
    ]
    assert len(auto_q_entries) == 1
    assert auto_q_entries[0]["old_points"] == 0.0
    assert auto_q_entries[0]["new_points"] == 10.0


# ============================================================================
# 2. REST API: CONTENT_OR_CHOICES FULL_CREDIT REGRADE
# ============================================================================


def test_regrade_api_content_or_choices_lifecycle(
    client: FlaskClient,
    instructor_user: User,
    student_user: User,
    test_course: Course,
) -> None:
    """Test CONTENT_OR_CHOICES full-credit regrade via REST API endpoints."""
    enroll_student(student_user, test_course.id)

    q = create_question(
        instructor_user,
        test_course.id,
        {
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "content": "Ambiguous stem",
            "choices": [
                {"content": "Alpha", "is_correct": True, "position": 1},
                {"content": "Beta", "is_correct": False, "position": 2},
            ],
        },
    )
    c_b = [c for c in q.current_revision.choices if c.content == "Beta"][0]

    asm = create_assessment(
        instructor_user,
        test_course.id,
        {"title": "API Quiz 2", "assessment_type": "QUIZ", "score_release_policy": "IMMEDIATE"},
    )
    sec = create_section(instructor_user, asm.id, {"title": "Sec", "position": 1})
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": q.id, "section_id": sec.id, "position": 1, "points_assigned": 25.0},
    )
    publish_assessment(instructor_user, asm.id)

    att, lease = start_assessment_attempt(student_user, asm.id)
    aq = att.attempt_questions[0]
    save_attempt_answer(
        student_user,
        str(att.public_id),
        str(aq.public_id),
        {"client_sequence": 1, "selected_choice_keys": [str(c_b.choice_key)]},
        raw_lease_token=lease,
    )
    submit_assessment_attempt(student_user, str(att.public_id), raw_lease_token=lease)

    # Revision with CONTENT_OR_CHOICES
    new_rev, corr = create_question_revision(
        instructor_user,
        q.id,
        {
            "change_type": "CONTENT_CHANGE",
            "correction_type": "CONTENT_OR_CHOICES",
            "change_reason": "Flawed question options",
            "content": "Corrected stem",
        },
    )

    inst_headers = _auth_headers(instructor_user)
    resp_trigger = client.post(
        f"/api/assessments/{asm.public_id}/regrade", headers=inst_headers, json={}
    )
    assert resp_trigger.status_code == 200
    trigger_data = resp_trigger.get_json()
    assert len(trigger_data["jobs"]) >= 1
    job_id = trigger_data["jobs"][0]["job_id"]

    # Read job detail
    resp_job = client.get(f"/api/regrade-jobs/{job_id}", headers=inst_headers)
    assert resp_job.status_code == 200
    job_data = resp_job.get_json()
    assert job_data["status"] == "COMPLETED"
    assert job_data["changed_results"] == 1

    # Student checks history
    resp_hist = client.get(
        f"/api/attempts/{att.public_id}/grade-history",
        headers=_auth_headers(student_user),
    )
    assert resp_hist.status_code == 200
    hist_data = resp_hist.get_json()

    assert "overall_history" in hist_data
    regrade_entries = [h for h in hist_data["overall_history"] if h["reason_code"] == "REGRADE"]
    assert len(regrade_entries) == 1
    assert regrade_entries[0]["new_score"] == 25.0

    assert "question_history" in hist_data
    full_q_entries = [
        qh for qh in hist_data["question_history"] if qh["reason_code"] == "FULL_CREDIT"
    ]
    assert len(full_q_entries) == 1
    assert full_q_entries[0]["new_points"] == 25.0


# ============================================================================
# 3. REST API: RETRY REGRADE JOB
# ============================================================================


def test_regrade_api_job_retry(
    client: FlaskClient,
    instructor_user: User,
    student_user: User,
    test_course: Course,
) -> None:
    """Test POST /api/regrade-jobs/<job_id>/retry endpoint."""
    enroll_student(student_user, test_course.id)

    q = create_question(
        instructor_user,
        test_course.id,
        {
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "content": "Retry test question",
            "choices": [
                {"content": "X", "is_correct": True, "position": 1},
                {"content": "Y", "is_correct": False, "position": 2},
            ],
        },
    )

    asm = create_assessment(
        instructor_user,
        test_course.id,
        {"title": "Retry Quiz", "assessment_type": "QUIZ", "score_release_policy": "IMMEDIATE"},
    )
    sec = create_section(instructor_user, asm.id, {"title": "Sec", "position": 1})
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": q.id, "section_id": sec.id, "position": 1, "points_assigned": 10.0},
    )
    publish_assessment(instructor_user, asm.id)

    att, lease = start_assessment_attempt(student_user, asm.id)
    submit_assessment_attempt(student_user, str(att.public_id), raw_lease_token=lease)

    new_rev, corr = create_question_revision(
        instructor_user,
        q.id,
        {
            "change_type": "CONTENT_CHANGE",
            "correction_type": "CONTENT_OR_CHOICES",
            "change_reason": "Correction reason",
            "content": "Retry test question fixed",
        },
    )
    job = create_or_get_regrade_job(corr.id)

    inst_headers = _auth_headers(instructor_user)

    # Call retry on the job
    resp_retry = client.post(f"/api/regrade-jobs/{job.public_id}/retry", headers=inst_headers)
    assert resp_retry.status_code == 200
    retry_data = resp_retry.get_json()
    assert retry_data["status"] == "COMPLETED"
    assert retry_data["job_id"] == str(job.public_id)
    _assert_no_internal_bigints(retry_data)


# ============================================================================
# 4. INSTRUCTOR BLUEPRINT WEB ROUTES (SESSION AUTH)
# ============================================================================


def test_instructor_web_blueprint_routes(
    client: FlaskClient,
    instructor_user: User,
    student_user: User,
    test_course: Course,
) -> None:
    """Test instructor web view endpoints using session authentication."""
    enroll_student(student_user, test_course.id)

    q = create_question(
        instructor_user,
        test_course.id,
        {
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "content": "Web route question",
            "choices": [
                {"content": "A", "is_correct": True, "position": 1},
                {"content": "B", "is_correct": False, "position": 2},
            ],
        },
    )

    asm = create_assessment(
        instructor_user,
        test_course.id,
        {"title": "Web Route Quiz", "assessment_type": "QUIZ", "score_release_policy": "IMMEDIATE"},
    )
    sec = create_section(instructor_user, asm.id, {"title": "Sec", "position": 1})
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": q.id, "section_id": sec.id, "position": 1, "points_assigned": 10.0},
    )
    publish_assessment(instructor_user, asm.id)

    att, lease = start_assessment_attempt(student_user, asm.id)
    submit_assessment_attempt(student_user, str(att.public_id), raw_lease_token=lease)

    new_rev, corr = create_question_revision(
        instructor_user,
        q.id,
        {
            "change_type": "CONTENT_CHANGE",
            "correction_type": "CONTENT_OR_CHOICES",
            "change_reason": "Web test revision",
            "content": "Web route question fixed",
        },
    )

    # 1. Non-authenticated access to instructor web route is blocked
    resp_unauth = client.post(f"/instructor/assessments/{asm.public_id}/regrade")
    assert resp_unauth.status_code in (302, 401, 403)

    # 2. Establish instructor web session
    login_web_user(client, instructor_user)

    # 3. POST /instructor/assessments/<id>/regrade
    resp_web_regrade = client.post(f"/instructor/assessments/{asm.public_id}/regrade")
    assert resp_web_regrade.status_code == 200
    web_reg_data = resp_web_regrade.get_json()
    assert len(web_reg_data["jobs"]) >= 1
    job_id = web_reg_data["jobs"][0]["job_id"]
    _assert_no_internal_bigints(web_reg_data)

    # 4. GET /instructor/regrade-jobs/<job_id>
    resp_web_job = client.get(f"/instructor/regrade-jobs/{job_id}")
    assert resp_web_job.status_code == 200
    web_job_data = resp_web_job.get_json()
    assert web_job_data["job_id"] == job_id
    _assert_no_internal_bigints(web_job_data)

    # 5. POST /instructor/regrade-jobs/<job_id>/retry
    resp_web_retry = client.post(f"/instructor/regrade-jobs/{job_id}/retry")
    assert resp_web_retry.status_code == 200
    web_retry_data = resp_web_retry.get_json()
    assert web_retry_data["job_id"] == job_id
    _assert_no_internal_bigints(web_retry_data)
