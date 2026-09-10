"""Security and IDOR prevention tests for Analytics and Dashboard Engine (TASK-025).

Verifies:
- Instructor A cannot access course analytics for Course B (HTTP 403 FORBIDDEN).
- Students cannot access instructor course analytics or admin analytics (HTTP 403 FORBIDDEN).
- Unauthenticated requests are rejected fail-closed (HTTP 401 UNAUTHORIZED).
- Student A learning overview contains strictly Student A's personal data.
- ADR-002 Zero Internal PK Leakage: 100% of exposed resource IDs are valid UUIDs.
"""

from __future__ import annotations

import re
import uuid
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course
from pwd301.models.identity import Role, User
from pwd301.services.course_service import create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.user_service import assign_role_to_user, register_user

UUID_REGEX = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)


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
def instructor_a(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Instructor A."""
    u = register_user(
        f"inst_a_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Instructor Alpha"
    )
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def instructor_b(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Instructor B."""
    u = register_user(
        f"inst_b_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Instructor Beta"
    )
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Student user."""
    return register_user(
        f"sec_student_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Security Student"
    )


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Admin user."""
    u = register_user(
        f"sec_admin_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Security Admin"
    )
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def course_of_b(app: Flask, instructor_b: User) -> Course:
    """Create Course owned by Instructor B."""
    sess: Session = db.session
    course = create_course(
        actor=instructor_b,
        data={"course_code": f"SEC-B-{uuid.uuid4().hex[:4]}", "title": "Course of Instructor B"},
        session=sess,
    )
    course.status = "PUBLISHED"
    sess.commit()
    return course


def test_instructor_a_cannot_access_course_b_analytics(
    client: FlaskClient,
    instructor_a: User,
    course_of_b: Course,
) -> None:
    """Instructor A attempting to access course analytics for Course B gets 403 FORBIDDEN."""
    tokens = create_token_pair(instructor_a)
    headers = {
        "Authorization": f"Bearer {tokens['access_token']}",
        "Accept": "application/json",
    }
    course_b_id = str(course_of_b.public_id)

    # 1. Test via REST API endpoint /api/courses/<id>/analytics
    resp_api = client.get(f"/api/courses/{course_b_id}/analytics", headers=headers)
    assert resp_api.status_code == 403
    json_data = resp_api.get_json()
    assert json_data["error"]["code"] == "FORBIDDEN"

    # 2. Test via Web endpoint /instructor/courses/<id>/analytics
    resp_web = client.get(f"/instructor/courses/{course_b_id}/analytics", headers=headers)
    assert resp_web.status_code == 403


def test_admin_can_access_any_course_analytics(
    client: FlaskClient,
    admin_user: User,
    course_of_b: Course,
) -> None:
    """Admin has platform-wide oversight and can access Course B analytics."""
    tokens = create_token_pair(admin_user)
    headers = {
        "Authorization": f"Bearer {tokens['access_token']}",
        "Accept": "application/json",
    }
    course_b_id = str(course_of_b.public_id)

    resp = client.get(f"/api/courses/{course_b_id}/analytics", headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["course_id"] == course_b_id


def test_student_cannot_access_instructor_or_admin_analytics(
    client: FlaskClient,
    student_user: User,
    course_of_b: Course,
) -> None:
    """Student attempting to access instructor or admin analytics must receive 403 FORBIDDEN."""
    tokens = create_token_pair(student_user)
    headers = {
        "Authorization": f"Bearer {tokens['access_token']}",
        "Accept": "application/json",
    }
    course_b_id = str(course_of_b.public_id)

    # Student accessing admin overview
    resp_admin = client.get("/api/admin/analytics/overview", headers=headers)
    assert resp_admin.status_code == 403

    # Student accessing instructor dashboard
    resp_inst_dash = client.get("/instructor/dashboard", headers=headers)
    assert resp_inst_dash.status_code == 403

    # Student accessing instructor course analytics
    resp_course = client.get(f"/api/courses/{course_b_id}/analytics", headers=headers)
    assert resp_course.status_code == 403


def test_unauthenticated_requests_rejected(
    client: FlaskClient,
    course_of_b: Course,
) -> None:
    """Unauthenticated requests must be rejected fail-closed with 401 UNAUTHORIZED."""
    course_b_id = str(course_of_b.public_id)
    headers = {"Accept": "application/json"}

    assert client.get("/api/admin/analytics/overview", headers=headers).status_code == 401
    assert client.get(f"/api/courses/{course_b_id}/analytics", headers=headers).status_code == 401
    assert client.get("/api/student/analytics/overview", headers=headers).status_code == 401
    assert client.get("/admin/dashboard", headers=headers).status_code == 401


def test_student_isolation_in_learning_overview(
    client: FlaskClient,
    instructor_a: User,
    instructor_b: User,
) -> None:
    """Verify Student A cannot see any data or assessment attempts belonging to Student B."""
    sess: Session = db.session

    # Student A & Course A
    student_a = register_user(
        f"stu_iso_a_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Student Iso A"
    )
    course_a = create_course(
        actor=instructor_a,
        data={"course_code": f"ISO-A-{uuid.uuid4().hex[:4]}", "title": "Course Iso A"},
        session=sess,
    )
    course_a.status = "PUBLISHED"
    sess.flush()
    enroll_student(actor=student_a, course_id=course_a.id, session=sess)

    # Student B & Course B
    student_b = register_user(
        f"stu_iso_b_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Student Iso B"
    )
    course_b = create_course(
        actor=instructor_b,
        data={"course_code": f"ISO-B-{uuid.uuid4().hex[:4]}", "title": "Course Iso B"},
        session=sess,
    )
    course_b.status = "PUBLISHED"
    sess.flush()
    enroll_student(actor=student_b, course_id=course_b.id, session=sess)
    sess.commit()

    # Query Student A learning overview
    tokens_a = create_token_pair(student_a)
    headers_a = {"Authorization": f"Bearer {tokens_a['access_token']}"}

    resp = client.get("/api/student/analytics/overview", headers=headers_a)
    assert resp.status_code == 200
    data = resp.get_json()

    # Verify only Course A is visible
    enrolled_courses = [e["course_id"] for e in data["enrollments"]]
    assert str(course_a.public_id) in enrolled_courses
    assert str(course_b.public_id) not in enrolled_courses


def _assert_zero_internal_pk_leakage(data: Any) -> None:
    """Recursively verify that no integer database IDs are exposed."""
    if isinstance(data, dict):
        for k, v in data.items():
            if k.endswith("_id") and v is not None:
                assert isinstance(v, str), (
                    f"Identifier field '{k}' must be string UUID, got {type(v)}"
                )
                assert UUID_REGEX.match(v), (
                    f"Identifier field '{k}'='{v}' is not a valid UUID format"
                )
            elif k == "id":
                raise AssertionError(f"Bare internal 'id' field leaked in payload: {k}={v}")
            _assert_zero_internal_pk_leakage(v)
    elif isinstance(data, list):
        for item in data:
            _assert_zero_internal_pk_leakage(item)


def test_adr002_zero_internal_pk_leakage_across_endpoints(
    client: FlaskClient,
    admin_user: User,
    instructor_a: User,
    student_user: User,
    course_of_b: Course,
) -> None:
    """Verify ADR-002 Zero Internal PK Leakage across all analytics endpoints."""
    # 1. Admin Analytics
    admin_tokens = create_token_pair(admin_user)
    resp_admin = client.get(
        "/api/admin/analytics/overview",
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
    )
    assert resp_admin.status_code == 200
    _assert_zero_internal_pk_leakage(resp_admin.get_json())

    # 2. Instructor Dashboard
    inst_tokens = create_token_pair(instructor_a)
    resp_inst = client.get(
        "/instructor/dashboard",
        headers={"Authorization": f"Bearer {inst_tokens['access_token']}"},
    )
    assert resp_inst.status_code == 200
    _assert_zero_internal_pk_leakage(resp_inst.get_json())

    # 3. Course Analytics
    resp_course = client.get(
        f"/api/courses/{str(course_of_b.public_id)}/analytics",
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
    )
    assert resp_course.status_code == 200
    _assert_zero_internal_pk_leakage(resp_course.get_json())

    # 4. Student Analytics
    student_tokens = create_token_pair(student_user)
    resp_student = client.get(
        "/api/student/analytics/overview",
        headers={"Authorization": f"Bearer {student_tokens['access_token']}"},
    )
    assert resp_student.status_code == 200
    _assert_zero_internal_pk_leakage(resp_student.get_json())
