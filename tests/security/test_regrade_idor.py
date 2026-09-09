"""Security and IDOR negative tests for Regrading Engine & Score History (TASK-017).

Validates:
- Fail-closed Zero-Trust IDOR protection on regrade trigger, job detail, retry,
  and grade history endpoints.
- Peer students receive 403 (ForbiddenError) accessing each other's attempt grade history.
- Non-managing instructors receive 403 (ForbiddenError) triggering regrades, viewing regrade jobs,
  retrying jobs, or viewing attempt grade histories.
- Students receive 403 (ForbiddenError) triggering regrades, viewing regrade jobs, or retrying jobs.
- Score release policy enforcement: students receive 403 when viewing grade history before release.
- Admins possess privileged access across all regrade endpoints and operations.
- ADR-002: Zero leakage of internal BIGINT PK/FK identifiers across all regrade responses.
"""

from __future__ import annotations

import uuid
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
    trigger_assessment_regrade,
)
from pwd301.services.attempt_service import (
    get_attempt_grade_history,
    save_attempt_answer,
    start_assessment_attempt,
    submit_assessment_attempt,
)
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.exceptions import ForbiddenError, ScoreReleasePolicyError
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.question_bank_service import (
    create_question,
    create_question_revision,
)
from pwd301.services.regrade_worker import (
    create_or_get_regrade_job,
    get_regrade_job_detail,
    process_regrade_job,
    retry_regrade_job,
)
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
    u = register_user(
        f"admin_regrade_sec_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Admin"
    )
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def instructor_one(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create primary course instructor."""
    u = register_user(
        f"inst1_regrade_sec_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Instructor One"
    )
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def instructor_two(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create rival instructor (not managing the course)."""
    u = register_user(
        f"inst2_regrade_sec_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Instructor Two"
    )
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_one(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create primary student who submits attempts."""
    u = register_user(
        f"stud1_regrade_sec_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Student One"
    )
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def student_two(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create peer student in same course."""
    u = register_user(
        f"stud2_regrade_sec_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Student Two"
    )
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def test_course(app: Flask, instructor_one: User, admin_user: User) -> Course:
    """Create and publish course managed by instructor_one."""
    c = create_course(
        instructor_one,
        {
            "course_code": f"SEC-RG-{uuid.uuid4().hex[:4].upper()}",
            "title": "Regrade Security Course",
            "description": "Course for testing regrading security and IDOR",
            "category": "Security",
            "difficulty": "INTERMEDIATE",
        },
    )
    change_course_status(instructor_one, c.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin_user, c.id, "APPROVED")
    change_course_status(admin_user, c.id, "PUBLISHED")
    db.session.commit()
    return c


@pytest.fixture
def enrolled_students(test_course: Course, student_one: User, student_two: User) -> None:
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


def _setup_attempt_and_regrade_job(
    instructor_one: User,
    student_one: User,
    test_course: Course,
    score_release_policy: str = "IMMEDIATE",
) -> tuple[Any, Any, Any]:
    """Helper to set up an assessment, attempt, revision, and regrade job."""
    q = create_question(
        instructor_one,
        test_course.id,
        {
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "content": "What is 2 + 2?",
            "choices": [
                {"content": "3", "is_correct": False, "position": 1},
                {"content": "4", "is_correct": True, "position": 2},
            ],
        },
    )
    c_3 = [c for c in q.current_revision.choices if c.content == "3"][0]

    asm = create_assessment(
        instructor_one,
        test_course.id,
        {
            "title": "Sec Quiz",
            "assessment_type": "QUIZ",
            "passing_percent": 50.0,
            "score_release_policy": score_release_policy,
        },
    )
    sec = create_section(instructor_one, asm.id, {"title": "Sec", "position": 1})
    assign_question(
        instructor_one,
        asm.id,
        {"question_id": q.id, "section_id": sec.id, "position": 1, "points_assigned": 10.0},
    )
    publish_assessment(instructor_one, asm.id)

    att, lease = start_assessment_attempt(student_one, asm.id)
    aq = att.attempt_questions[0]
    save_attempt_answer(
        student_one,
        str(att.public_id),
        str(aq.public_id),
        {"client_sequence": 1, "selected_choice_keys": [str(c_3.choice_key)]},
        raw_lease_token=lease,
    )
    submit_assessment_attempt(student_one, str(att.public_id), raw_lease_token=lease)

    new_rev, corr = create_question_revision(
        instructor_one,
        q.id,
        {
            "change_type": "CONTENT_CHANGE",
            "correction_type": "CONTENT_OR_CHOICES",
            "change_reason": "Flawed question text",
            "content": "Clarified 2 + 2 question",
        },
    )
    job = create_or_get_regrade_job(corr.id)
    return asm, att, job


# ============================================================================
# 1. TRIGGER REGRADE PERMISSIONS & IDOR
# ============================================================================


def test_student_cannot_trigger_assessment_regrade(
    client: FlaskClient,
    instructor_one: User,
    student_one: User,
    test_course: Course,
    enrolled_students: None,
) -> None:
    """Student cannot trigger regrading (API 403 and service ForbiddenError)."""
    asm, att, job = _setup_attempt_and_regrade_job(instructor_one, student_one, test_course)

    # API test
    resp = client.post(
        f"/api/assessments/{asm.public_id}/regrade",
        headers=_auth_headers(student_one),
        json={},
    )
    assert resp.status_code == 403

    # Service test
    with pytest.raises(ForbiddenError):
        trigger_assessment_regrade(student_one, asm.id)


def test_non_managing_instructor_cannot_trigger_regrade(
    client: FlaskClient,
    instructor_one: User,
    instructor_two: User,
    student_one: User,
    test_course: Course,
    enrolled_students: None,
) -> None:
    """Non-managing instructor cannot trigger regrading (API/service 403 ForbiddenError)."""
    asm, att, job = _setup_attempt_and_regrade_job(instructor_one, student_one, test_course)

    resp = client.post(
        f"/api/assessments/{asm.public_id}/regrade",
        headers=_auth_headers(instructor_two),
        json={},
    )
    assert resp.status_code == 403

    with pytest.raises(ForbiddenError):
        trigger_assessment_regrade(instructor_two, asm.id)


# ============================================================================
# 2. REGRADE JOB DETAIL PERMISSIONS & IDOR
# ============================================================================


def test_student_cannot_view_regrade_job(
    client: FlaskClient,
    instructor_one: User,
    student_one: User,
    test_course: Course,
    enrolled_students: None,
) -> None:
    """Student cannot read regrade job status or items (API 403 and service ForbiddenError)."""
    asm, att, job = _setup_attempt_and_regrade_job(instructor_one, student_one, test_course)

    resp = client.get(
        f"/api/regrade-jobs/{job.public_id}",
        headers=_auth_headers(student_one),
    )
    assert resp.status_code == 403

    with pytest.raises(ForbiddenError):
        get_regrade_job_detail(actor=student_one, job_id=job.id)


def test_non_managing_instructor_cannot_view_regrade_job(
    client: FlaskClient,
    instructor_one: User,
    instructor_two: User,
    student_one: User,
    test_course: Course,
    enrolled_students: None,
) -> None:
    """Rival instructor cannot read regrade job (API 403 and service ForbiddenError)."""
    asm, att, job = _setup_attempt_and_regrade_job(instructor_one, student_one, test_course)

    resp = client.get(
        f"/api/regrade-jobs/{job.public_id}",
        headers=_auth_headers(instructor_two),
    )
    assert resp.status_code == 403

    with pytest.raises(ForbiddenError):
        get_regrade_job_detail(actor=instructor_two, job_id=job.id)


# ============================================================================
# 3. RETRY REGRADE JOB PERMISSIONS & IDOR
# ============================================================================


def test_student_cannot_retry_regrade_job(
    client: FlaskClient,
    instructor_one: User,
    student_one: User,
    test_course: Course,
    enrolled_students: None,
) -> None:
    """Student cannot call retry on a regrade job (API 403 and service ForbiddenError)."""
    asm, att, job = _setup_attempt_and_regrade_job(instructor_one, student_one, test_course)

    resp = client.post(
        f"/api/regrade-jobs/{job.public_id}/retry",
        headers=_auth_headers(student_one),
    )
    assert resp.status_code == 403

    with pytest.raises(ForbiddenError):
        retry_regrade_job(job_id=job.id, actor=student_one)


def test_non_managing_instructor_cannot_retry_regrade_job(
    client: FlaskClient,
    instructor_one: User,
    instructor_two: User,
    student_one: User,
    test_course: Course,
    enrolled_students: None,
) -> None:
    """Rival instructor cannot retry regrade job (API 403 and service ForbiddenError)."""
    asm, att, job = _setup_attempt_and_regrade_job(instructor_one, student_one, test_course)

    resp = client.post(
        f"/api/regrade-jobs/{job.public_id}/retry",
        headers=_auth_headers(instructor_two),
    )
    assert resp.status_code == 403

    with pytest.raises(ForbiddenError):
        retry_regrade_job(job_id=job.id, actor=instructor_two)


# ============================================================================
# 4. ATTEMPT GRADE HISTORY PERMISSIONS & IDOR
# ============================================================================


def test_peer_student_cannot_view_attempt_grade_history(
    client: FlaskClient,
    instructor_one: User,
    student_one: User,
    student_two: User,
    test_course: Course,
    enrolled_students: None,
) -> None:
    """Peer student cannot view another student's grade history (API/service 403)."""
    asm, att, job = _setup_attempt_and_regrade_job(instructor_one, student_one, test_course)
    process_regrade_job(job.id, actor=instructor_one)

    resp = client.get(
        f"/api/attempts/{att.public_id}/grade-history",
        headers=_auth_headers(student_two),
    )
    assert resp.status_code == 403

    with pytest.raises(ForbiddenError):
        get_attempt_grade_history(actor=student_two, attempt_id=att.id)


def test_non_managing_instructor_cannot_view_attempt_grade_history(
    client: FlaskClient,
    instructor_one: User,
    instructor_two: User,
    student_one: User,
    test_course: Course,
    enrolled_students: None,
) -> None:
    """Rival instructor cannot view grade history in other courses (API/service 403)."""
    asm, att, job = _setup_attempt_and_regrade_job(instructor_one, student_one, test_course)
    process_regrade_job(job.id, actor=instructor_one)

    resp = client.get(
        f"/api/attempts/{att.public_id}/grade-history",
        headers=_auth_headers(instructor_two),
    )
    assert resp.status_code == 403

    with pytest.raises(ForbiddenError):
        get_attempt_grade_history(actor=instructor_two, attempt_id=att.id)


def test_student_cannot_view_grade_history_before_score_release(
    client: FlaskClient,
    instructor_one: User,
    student_one: User,
    test_course: Course,
    enrolled_students: None,
) -> None:
    """Student cannot view grade history if policy not satisfied (403 ScoreReleasePolicyError)."""
    # Create with INSTRUCTOR_RELEASE policy (scores not released yet)
    asm, att, job = _setup_attempt_and_regrade_job(
        instructor_one, student_one, test_course, score_release_policy="INSTRUCTOR_RELEASE"
    )
    process_regrade_job(job.id, actor=instructor_one)

    # Student access is blocked
    resp = client.get(
        f"/api/attempts/{att.public_id}/grade-history",
        headers=_auth_headers(student_one),
    )
    assert resp.status_code == 403

    with pytest.raises(ScoreReleasePolicyError):
        get_attempt_grade_history(actor=student_one, attempt_id=att.id)

    # But managing instructor CAN view the audit history
    resp_inst = client.get(
        f"/api/attempts/{att.public_id}/grade-history",
        headers=_auth_headers(instructor_one),
    )
    assert resp_inst.status_code == 200
    data = resp_inst.get_json()
    assert data["attempt_id"] == str(att.public_id)


# ============================================================================
# 5. ADMIN PRIVILEGED ACCESS
# ============================================================================


def test_admin_has_full_access_to_regrade_operations(
    client: FlaskClient,
    admin_user: User,
    instructor_one: User,
    student_one: User,
    test_course: Course,
    enrolled_students: None,
) -> None:
    """Admin can trigger regrade, view jobs, retry jobs, and inspect any attempt grade history."""
    asm, att, job = _setup_attempt_and_regrade_job(instructor_one, student_one, test_course)

    # Admin view job
    resp_job = client.get(
        f"/api/regrade-jobs/{job.public_id}",
        headers=_auth_headers(admin_user),
    )
    assert resp_job.status_code == 200
    assert resp_job.get_json()["job_id"] == str(job.public_id)

    # Admin retry job
    resp_retry = client.post(
        f"/api/regrade-jobs/{job.public_id}/retry",
        headers=_auth_headers(admin_user),
    )
    assert resp_retry.status_code == 200

    # Admin view attempt grade history
    resp_hist = client.get(
        f"/api/attempts/{att.public_id}/grade-history",
        headers=_auth_headers(admin_user),
    )
    assert resp_hist.status_code == 200

    # Admin trigger regrade
    resp_regrade = client.post(
        f"/api/assessments/{asm.public_id}/regrade",
        headers=_auth_headers(admin_user),
        json={},
    )
    assert resp_regrade.status_code == 200


# ============================================================================
# 6. ADR-002: ZERO INTERNAL BIGINT PK LEAKAGE
# ============================================================================


def test_regrade_adr002_zero_pk_leakage(
    client: FlaskClient,
    instructor_one: User,
    student_one: User,
    test_course: Course,
    enrolled_students: None,
) -> None:
    """Verify ADR-002 across all regrade endpoints (zero integer PKs exposed in JSON)."""
    asm, att, job = _setup_attempt_and_regrade_job(instructor_one, student_one, test_course)
    process_regrade_job(job.id, actor=instructor_one)

    headers = _auth_headers(instructor_one)

    # 1. Trigger regrade response
    resp_trig = client.post(f"/api/assessments/{asm.public_id}/regrade", headers=headers, json={})
    assert resp_trig.status_code == 200
    _assert_no_internal_bigints(resp_trig.get_json())

    # 2. Get regrade job detail
    resp_job = client.get(f"/api/regrade-jobs/{job.public_id}", headers=headers)
    assert resp_job.status_code == 200
    _assert_no_internal_bigints(resp_job.get_json())

    # 3. Retry regrade job
    resp_retry = client.post(f"/api/regrade-jobs/{job.public_id}/retry", headers=headers)
    assert resp_retry.status_code == 200
    _assert_no_internal_bigints(resp_retry.get_json())

    # 4. Attempt grade history
    resp_hist = client.get(f"/api/attempts/{att.public_id}/grade-history", headers=headers)
    assert resp_hist.status_code == 200
    _assert_no_internal_bigints(resp_hist.get_json())
