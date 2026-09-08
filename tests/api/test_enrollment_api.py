"""Integration tests for Enrollment and Prerequisite REST API endpoints."""

from __future__ import annotations

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course
from pwd301.models.identity import Role, User
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
    """Ensure canonical roles exist."""
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
    """Create Instructor User."""
    u = register_user("api_enr_inst@example.com", "Password@123", "API Enrollment Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Admin User."""
    u = register_user("api_enr_adm@example.com", "Password@123", "API Enrollment Admin")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Student User."""
    u = register_user("api_enr_stu@example.com", "Password@123", "API Enrollment Student")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def published_courses(app: Flask, instructor_user: User, admin_user: User) -> tuple[Course, Course]:
    """Create and publish two courses."""
    c1 = create_course(
        instructor_user,
        {"course_code": "API-CS1", "title": "API Course 1", "capacity": 10},
    )
    c1 = change_course_status(instructor_user, c1.id, "SUBMITTED_FOR_REVIEW")
    c1 = change_course_status(admin_user, c1.id, "APPROVED")
    c1 = change_course_status(instructor_user, c1.id, "PUBLISHED")

    c2 = create_course(
        instructor_user,
        {"course_code": "API-CS2", "title": "API Course 2", "capacity": 10},
    )
    c2 = change_course_status(instructor_user, c2.id, "SUBMITTED_FOR_REVIEW")
    c2 = change_course_status(admin_user, c2.id, "APPROVED")
    c2 = change_course_status(instructor_user, c2.id, "PUBLISHED")

    db.session.commit()
    return c1, c2


def test_api_enroll_and_leave_workflow(
    client: FlaskClient,
    student_user: User,
    published_courses: tuple[Course, Course],
) -> None:
    """Test POST /api/courses/<id>/enroll, idempotent re-enroll, and leave."""
    c1, _ = published_courses
    tokens = create_token_pair(student_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # 1. Enroll
    resp = client.post(f"/api/courses/{c1.public_id}/enroll", headers=headers)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["status"] == "ACTIVE"
    assert data["course_id"] == str(c1.public_id)

    # 2. Idempotent enrollment returns 200
    resp2 = client.post(f"/api/courses/{c1.public_id}/enroll", headers=headers)
    assert resp2.status_code == 200
    assert resp2.get_json()["status"] == "ACTIVE"

    # 3. Read own enrollments
    resp3 = client.get("/api/student/enrollments", headers=headers)
    assert resp3.status_code == 200
    enrollments = resp3.get_json()["enrollments"]
    assert len(enrollments) == 1
    assert enrollments[0]["course_id"] == str(c1.public_id)

    # 4. Leave course
    resp4 = client.post(
        f"/api/courses/{c1.public_id}/leave",
        headers=headers,
        json={"reason": "Completed study goals"},
    )
    assert resp4.status_code == 200
    assert resp4.get_json()["status"] == "LEFT"

    # 5. State-idempotent leave returns 200
    resp5 = client.post(
        f"/api/courses/{c1.public_id}/leave",
        headers=headers,
    )
    assert resp5.status_code == 200
    assert resp5.get_json()["status"] == "LEFT"

    # 6. Re-enroll
    resp6 = client.post(f"/api/courses/{c1.public_id}/re-enroll", headers=headers)
    assert resp6.status_code == 200
    assert resp6.get_json()["status"] == "ACTIVE"


def test_api_prerequisites_management(
    client: FlaskClient,
    instructor_user: User,
    published_courses: tuple[Course, Course],
) -> None:
    """Test GET, POST, DELETE /api/courses/<id>/prerequisites."""
    c1, c2 = published_courses
    tokens = create_token_pair(instructor_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # 1. Add prerequisite (c1 requires c2)
    resp = client.post(
        f"/api/courses/{c1.public_id}/prerequisites",
        headers=headers,
        json={"prerequisite_course_id": str(c2.public_id)},
    )
    assert resp.status_code == 201

    # 2. List prerequisites
    resp2 = client.get(f"/api/courses/{c1.public_id}/prerequisites")
    assert resp2.status_code == 200
    prereqs = resp2.get_json()["prerequisites"]
    assert len(prereqs) == 1
    assert prereqs[0]["course_id"] == str(c2.public_id)

    # 3. Remove prerequisite
    resp3 = client.delete(
        f"/api/courses/{c1.public_id}/prerequisites/{c2.public_id}",
        headers=headers,
    )
    assert resp3.status_code == 200
    assert resp3.get_json()["removed"] is True

    # 4. List prerequisites after removal
    resp4 = client.get(f"/api/courses/{c1.public_id}/prerequisites")
    assert resp4.status_code == 200
    assert len(resp4.get_json()["prerequisites"]) == 0


def test_api_course_enrollments_roster(
    client: FlaskClient,
    instructor_user: User,
    student_user: User,
    published_courses: tuple[Course, Course],
) -> None:
    """Test GET /api/courses/<id>/enrollments."""
    c1, _ = published_courses
    tokens_stud = create_token_pair(student_user)
    tokens_inst = create_token_pair(instructor_user)

    # Student enrolls
    client.post(
        f"/api/courses/{c1.public_id}/enroll",
        headers={"Authorization": f"Bearer {tokens_stud['access_token']}"},
    )

    # Instructor views enrollments
    resp = client.get(
        f"/api/courses/{c1.public_id}/enrollments",
        headers={"Authorization": f"Bearer {tokens_inst['access_token']}"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["pagination"]["total_items"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["student_id"] == str(student_user.public_id)
