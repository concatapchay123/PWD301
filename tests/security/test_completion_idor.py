"""Security and IDOR prevention tests for Course Completion and Progress Engine (TASK-009)."""

from __future__ import annotations

import pytest
from flask import Flask
from flask.testing import FlaskClient

from pwd301.extensions import db
from pwd301.models.course import Course
from pwd301.models.identity import Role, User
from pwd301.services.completion_service import (
    get_course_completion_summary,
    set_course_completion_rule,
)
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.exceptions import ForbiddenError
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
    """Ensure canonical roles exist in test database."""
    sess = db.session
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
    """Create Instructor Alpha."""
    u = register_user("idor_inst_a@example.com", "Password@123", "Instructor Alpha")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def instructor_b(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Instructor Beta."""
    u = register_user("idor_inst_b@example.com", "Password@123", "Instructor Beta")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_a(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Student Alpha."""
    return register_user("idor_stud_a@example.com", "Password@123", "Student Alpha")


@pytest.fixture
def student_b(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Student Beta."""
    return register_user("idor_stud_b@example.com", "Password@123", "Student Beta")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create administrator user."""
    u = register_user("idor_admin@example.com", "Password@123", "IDOR Admin")
    return assign_role_to_user(u.id, "ADMIN")


def _create_course(instructor: User, admin: User, code: str) -> Course:
    """Helper to create published course."""
    c = create_course(
        instructor,
        {
            "course_code": code,
            "title": f"Course {code}",
            "description": "Desc",
            "category": "Testing",
            "difficulty": "BEGINNER",
        },
    )
    c = change_course_status(instructor, c.id, "SUBMITTED_FOR_REVIEW")
    c = change_course_status(admin, c.id, "APPROVED")
    c = change_course_status(instructor, c.id, "PUBLISHED")
    db.session.commit()
    return c


def test_instructor_cannot_modify_other_course_rules(
    app: Flask,
    client: FlaskClient,
    instructor_a: User,
    instructor_b: User,
    admin_user: User,
) -> None:
    """Verify Instructor B cannot view or update completion rules for Instructor A's course."""
    course_a = _create_course(instructor_a, admin_user, "SEC101")

    # Service layer IDOR check
    with pytest.raises(ForbiddenError, match="permission to manage this course"):
        set_course_completion_rule(
            instructor_b,
            course_a.id,
            {"minimum_progress_percent": 50.0},
        )

    # Web UI IDOR check
    from tests.conftest import login_web_user

    login_web_user(client, instructor_b)

    resp = client.get(
        f"/instructor/courses/{course_a.public_id}/completion-rules",
        headers={"Accept": "application/json"},
    )
    assert resp.status_code == 403

    resp_post = client.post(
        f"/instructor/courses/{course_a.public_id}/completion-rules",
        json={"minimum_progress_percent": 50.0},
        headers={"Accept": "application/json"},
    )
    assert resp_post.status_code == 403

    # REST API IDOR check
    tokens_b = create_token_pair(instructor_b)
    resp_api = client.put(
        f"/api/courses/{course_a.public_id}/completion-rules",
        json={"minimum_progress_percent": 50.0},
        headers={"Authorization": f"Bearer {tokens_b['access_token']}"},
    )
    assert resp_api.status_code == 403


def test_student_cannot_modify_rules(
    app: Flask,
    client: FlaskClient,
    instructor_a: User,
    student_a: User,
    admin_user: User,
) -> None:
    """Verify students cannot view or modify completion rules."""
    course = _create_course(instructor_a, admin_user, "SEC102")

    # Service layer guard
    with pytest.raises(ForbiddenError):
        set_course_completion_rule(student_a, course.id, {"minimum_progress_percent": 50.0})

    # REST API guard
    tokens = create_token_pair(student_a)
    resp = client.put(
        f"/api/courses/{course.public_id}/completion-rules",
        json={"minimum_progress_percent": 50.0},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert resp.status_code == 403


def test_student_cannot_view_other_student_summary(
    app: Flask,
    client: FlaskClient,
    instructor_a: User,
    student_a: User,
    student_b: User,
    admin_user: User,
) -> None:
    """Verify Student A cannot access Student B's completion summary or progress."""
    course = _create_course(instructor_a, admin_user, "SEC103")

    # Service layer IDOR check
    with pytest.raises(ForbiddenError, match="permission to view this completion summary"):
        get_course_completion_summary(
            actor=student_a,
            course_id=course.id,
            student_user_id=student_b.id,
        )

    # REST API progress check: Student A queries Student B's progress -> 403 Forbidden
    tokens_a = create_token_pair(student_a)
    resp = client.get(
        f"/api/courses/{course.public_id}/progress?student_id={student_b.public_id}",
        headers={"Authorization": f"Bearer {tokens_a['access_token']}"},
    )
    assert resp.status_code == 403


def test_unauthenticated_cannot_access_rules_or_progress(
    app: Flask,
    client: FlaskClient,
    instructor_a: User,
    admin_user: User,
) -> None:
    """Verify unauthenticated requests are denied access to completion rules and progress."""
    course = _create_course(instructor_a, admin_user, "SEC104")

    # REST API without token
    resp_api = client.get(f"/api/courses/{course.public_id}/progress")
    assert resp_api.status_code in (401, 403)

    resp_rules = client.get(f"/api/courses/{course.public_id}/completion-rules")
    assert resp_rules.status_code in (401, 403)
