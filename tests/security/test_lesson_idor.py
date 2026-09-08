"""Security negative and IDOR prevention tests for Lesson Management."""

from __future__ import annotations

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course, Lesson
from pwd301.models.identity import Role, User
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.lesson_service import change_lesson_status, create_lesson
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
def instructor_a(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Instructor A."""
    u = register_user("idor_inst_a@example.com", "Password@123", "Instructor Alpha")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def instructor_b(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Instructor B."""
    u = register_user("idor_inst_b@example.com", "Password@123", "Instructor Beta")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Student."""
    return register_user("idor_student@example.com", "Password@123", "Student User")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Admin."""
    u = register_user("idor_admin@example.com", "Password@123", "Admin User")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def course_a(app: Flask, instructor_a: User) -> Course:
    """Course owned by Instructor A."""
    return create_course(
        instructor_a,
        {
            "course_code": "SEC-LES-A",
            "title": "Security Course A",
            "description": "Owned by Alpha",
        },
    )


@pytest.fixture
def lesson_a(app: Flask, instructor_a: User, course_a: Course) -> Lesson:
    """Lesson in Course A."""
    return create_lesson(
        instructor_a,
        course_a.id,
        {
            "title": "Alpha Lesson 1",
            "markdown_content": "# Lesson 1 by Alpha",
        },
    )


def test_instructor_b_cannot_edit_instructor_a_lesson(
    client: FlaskClient,
    instructor_b: User,
    lesson_a: Lesson,
) -> None:
    """IDOR: Instructor B cannot edit lesson in Course A."""
    tokens = create_token_pair(instructor_b)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = client.patch(
        f"/instructor/lessons/{lesson_a.public_id}",
        headers=headers,
        json={"title": "Hacked Title"},
    )
    assert resp.status_code == 403
    assert resp.get_json()["error"]["code"] == "FORBIDDEN"


def test_instructor_b_cannot_reorder_instructor_a_lessons(
    client: FlaskClient,
    instructor_b: User,
    course_a: Course,
    lesson_a: Lesson,
) -> None:
    """IDOR: Instructor B cannot reorder lessons in Course A."""
    tokens = create_token_pair(instructor_b)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = client.post(
        f"/instructor/courses/{course_a.public_id}/lessons/reorder",
        headers=headers,
        json={"ordered_lesson_ids": [str(lesson_a.public_id)]},
    )
    assert resp.status_code == 403
    assert resp.get_json()["error"]["code"] == "FORBIDDEN"


def test_instructor_b_cannot_trash_instructor_a_lesson(
    client: FlaskClient,
    instructor_b: User,
    lesson_a: Lesson,
) -> None:
    """IDOR: Instructor B cannot trash lesson in Course A."""
    tokens = create_token_pair(instructor_b)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = client.post(
        f"/instructor/lessons/{lesson_a.public_id}/trash",
        headers=headers,
        json={"reason": "Malicious deletion attempt"},
    )
    assert resp.status_code == 403
    assert resp.get_json()["error"]["code"] == "FORBIDDEN"


def test_student_cannot_access_draft_lesson(
    client: FlaskClient,
    student_user: User,
    course_a: Course,
    lesson_a: Lesson,
) -> None:
    """Student cannot access DRAFT lesson (returns 403)."""
    tokens = create_token_pair(student_user)
    headers = {
        "Authorization": f"Bearer {tokens['access_token']}",
        "Accept": "application/json",
    }

    resp = client.get(
        f"/student/courses/{course_a.public_id}/lessons/{lesson_a.public_id}",
        headers=headers,
    )
    assert resp.status_code == 403
    assert resp.get_json()["error"]["code"] == "FORBIDDEN"


def test_student_not_enrolled_cannot_record_progress(
    client: FlaskClient,
    instructor_a: User,
    admin_user: User,
    student_user: User,
    course_a: Course,
    lesson_a: Lesson,
) -> None:
    """Student not enrolled in Course A cannot record progress on published lesson."""
    # Publish course and lesson
    change_course_status(instructor_a, course_a.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin_user, course_a.id, "APPROVED")
    change_course_status(instructor_a, course_a.id, "PUBLISHED")
    change_lesson_status(instructor_a, lesson_a.id, "PUBLISHED")

    tokens = create_token_pair(student_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = client.post(
        f"/student/lessons/{lesson_a.public_id}/progress",
        headers=headers,
        json={"seconds_increment": 30, "view_fraction": 0.8},
    )
    assert resp.status_code == 403
    assert resp.get_json()["error"]["code"] == "FORBIDDEN"


def test_anonymous_user_progress_rejected(
    client: FlaskClient,
    lesson_a: Lesson,
) -> None:
    """Unauthenticated requests to record progress return HTTP 401."""
    resp = client.post(
        f"/student/lessons/{lesson_a.public_id}/progress",
        json={"seconds_increment": 15, "view_fraction": 0.5},
    )
    assert resp.status_code == 401
    assert resp.get_json()["error"]["code"] == "UNAUTHORIZED"


def test_admin_can_manage_any_lesson(
    client: FlaskClient,
    admin_user: User,
    lesson_a: Lesson,
) -> None:
    """Admin has platform-wide authority to view and update any lesson."""
    tokens = create_token_pair(admin_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = client.patch(
        f"/instructor/lessons/{lesson_a.public_id}",
        headers=headers,
        json={"title": "Admin Updated Title"},
    )
    assert resp.status_code == 200
    assert resp.get_json()["title"] == "Admin Updated Title"
