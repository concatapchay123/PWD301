"""Integration tests for Lesson REST API endpoints."""

from __future__ import annotations

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course, Enrollment, EnrollmentPeriod, Lesson
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
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Instructor User."""
    u = register_user("api_les_inst@example.com", "Password@123", "API Lesson Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Admin User."""
    u = register_user("api_les_adm@example.com", "Password@123", "API Lesson Admin")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Student User."""
    return register_user("api_les_stu@example.com", "Password@123", "API Lesson Student")


@pytest.fixture
def published_course_and_lesson(
    app: Flask,
    instructor_user: User,
    admin_user: User,
) -> tuple[Course, Lesson]:
    """Create and publish a course and lesson."""
    c = create_course(
        instructor_user,
        {"course_code": "API-LES-101", "title": "API Lesson Course"},
    )
    les = create_lesson(
        instructor_user,
        c.id,
        {
            "title": "Published API Lesson",
            "markdown_content": "# Lesson Content for API Test",
            "minimum_completion_seconds": 30,
            "viewed_fraction_required": 0.8000,
        },
    )
    change_course_status(instructor_user, c.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin_user, c.id, "APPROVED")
    change_course_status(instructor_user, c.id, "PUBLISHED")
    change_lesson_status(instructor_user, les.id, "PUBLISHED")
    return c, les


def test_api_get_course_lessons(
    client: FlaskClient,
    published_course_and_lesson: tuple[Course, Lesson],
) -> None:
    """Test GET /api/courses/<id>/lessons returns published lessons list."""
    course, lesson = published_course_and_lesson

    resp = client.get(f"/api/courses/{course.public_id}/lessons")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "lessons" in data
    assert len(data["lessons"]) == 1
    assert data["lessons"][0]["title"] == "Published API Lesson"
    assert data["lessons"][0]["position"] == 1


def test_api_get_lesson_detail_jwt(
    client: FlaskClient,
    student_user: User,
    published_course_and_lesson: tuple[Course, Lesson],
) -> None:
    """Test GET /api/lessons/<id> with Bearer JWT for enrolled student."""
    course, lesson = published_course_and_lesson
    sess: Session = db.session

    # Enroll student
    enrollment = Enrollment(
        student_user_id=student_user.id,
        course_id=course.id,
        status="ACTIVE",
    )
    sess.add(enrollment)
    sess.flush()
    period = EnrollmentPeriod(
        enrollment_id=enrollment.id,
        period_no=1,
        status="ACTIVE",
    )
    sess.add(period)
    sess.flush()
    enrollment.current_period_id = period.id
    sess.commit()

    tokens = create_token_pair(student_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = client.get(f"/api/lessons/{lesson.public_id}", headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["title"] == "Published API Lesson"
    assert data["markdown_content"] == "# Lesson Content for API Test"


def test_api_record_progress_jwt(
    client: FlaskClient,
    student_user: User,
    published_course_and_lesson: tuple[Course, Lesson],
) -> None:
    """Test POST /api/lessons/<id>/progress via Bearer JWT."""
    course, lesson = published_course_and_lesson
    sess: Session = db.session

    enrollment = Enrollment(
        student_user_id=student_user.id,
        course_id=course.id,
        status="ACTIVE",
    )
    sess.add(enrollment)
    sess.flush()
    period = EnrollmentPeriod(
        enrollment_id=enrollment.id,
        period_no=1,
        status="ACTIVE",
    )
    sess.add(period)
    sess.flush()
    enrollment.current_period_id = period.id
    sess.commit()

    tokens = create_token_pair(student_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = client.post(
        f"/api/lessons/{lesson.public_id}/progress",
        headers=headers,
        json={"seconds_increment": 35, "view_fraction": 0.85},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["seconds_spent"] == 35
    assert data["is_completed"] is True
    assert data["completed_at"] is not None


def test_api_record_activity_alias_jwt(
    client: FlaskClient,
    student_user: User,
    published_course_and_lesson: tuple[Course, Lesson],
) -> None:
    """Test POST /api/lessons/<id>/activity alias via Bearer JWT."""
    course, lesson = published_course_and_lesson
    sess: Session = db.session

    enrollment = Enrollment(
        student_user_id=student_user.id,
        course_id=course.id,
        status="ACTIVE",
    )
    sess.add(enrollment)
    sess.flush()
    period = EnrollmentPeriod(
        enrollment_id=enrollment.id,
        period_no=1,
        status="ACTIVE",
    )
    sess.add(period)
    sess.flush()
    enrollment.current_period_id = period.id
    sess.commit()

    tokens = create_token_pair(student_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = client.post(
        f"/api/lessons/{lesson.public_id}/activity",
        headers=headers,
        json={"seconds_increment": 20, "view_fraction": 0.50},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["seconds_spent"] == 20
    assert data["is_completed"] is False


def test_api_record_progress_invalid_payload(
    client: FlaskClient,
    student_user: User,
    published_course_and_lesson: tuple[Course, Lesson],
) -> None:
    """Test POST /api/lessons/<id>/progress with missing payload fields."""
    course, lesson = published_course_and_lesson
    tokens = create_token_pair(student_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = client.post(
        f"/api/lessons/{lesson.public_id}/progress",
        headers=headers,
        json={"view_fraction": 0.50},  # missing seconds_increment
    )
    assert resp.status_code == 400
    assert resp.get_json()["error"]["code"] == "VALIDATION_ERROR"
