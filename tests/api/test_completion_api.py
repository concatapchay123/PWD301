"""Integration tests for Course Completion and Progress REST API endpoints (TASK-009)."""

from __future__ import annotations

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course, Lesson
from pwd301.models.identity import Role, User
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.lesson_service import create_lesson, record_lesson_progress
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
    u = register_user("api_comp_inst@example.com", "Password@123", "API Comp Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Admin User."""
    u = register_user("api_comp_adm@example.com", "Password@123", "API Comp Admin")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Student User."""
    u = register_user("api_comp_stu@example.com", "Password@123", "API Comp Student")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def published_course(app: Flask, instructor_user: User, admin_user: User) -> tuple[Course, Lesson]:
    """Create and publish a course with one lesson."""
    c = create_course(
        instructor_user,
        {"course_code": "API-COMP1", "title": "API Completion Course", "capacity": 20},
    )
    c = change_course_status(instructor_user, c.id, "SUBMITTED_FOR_REVIEW")
    c = change_course_status(admin_user, c.id, "APPROVED")
    c = change_course_status(instructor_user, c.id, "PUBLISHED")

    l1 = create_lesson(
        instructor_user,
        c.id,
        {
            "title": "Intro Lesson",
            "markdown_content": "# Intro Content",
            "position": 1,
            "minimum_completion_seconds": 10,
            "viewed_fraction_required": 0.8,
            "status": "PUBLISHED",
        },
    )
    db.session.commit()
    return c, l1


def test_get_and_put_completion_rules_api(
    client: FlaskClient,
    instructor_user: User,
    published_course: tuple[Course, Lesson],
) -> None:
    """Verify instructor can read and update completion rules via REST API."""
    course, _ = published_course
    tokens = create_token_pair(instructor_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # 1. GET default completion rules
    resp = client.get(
        f"/api/courses/{course.public_id}/completion-rules",
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["course_id"] == str(course.public_id)
    assert data["course_code"] == course.course_code
    assert data["require_all_required_lessons"] is True
    assert data["require_required_assessments"] is True
    assert data["minimum_progress_percent"] == 100.0
    # Internal PKs must not be leaked (ADR-002)
    assert "id" not in data
    assert "updated_by_user_id" not in data

    # 2. PUT updated completion rules
    payload = {
        "require_all_required_lessons": False,
        "require_required_assessments": False,
        "minimum_progress_percent": 80.0,
        "reason": "REST update test",
    }
    resp_put = client.put(
        f"/api/courses/{course.public_id}/completion-rules",
        headers=headers,
        json=payload,
    )
    assert resp_put.status_code == 200
    updated_data = resp_put.get_json()
    assert updated_data["require_all_required_lessons"] is False
    assert updated_data["require_required_assessments"] is False
    assert updated_data["minimum_progress_percent"] == 80.0
    assert updated_data["course_id"] == str(course.public_id)


def test_get_course_progress_api(
    client: FlaskClient,
    instructor_user: User,
    student_user: User,
    published_course: tuple[Course, Lesson],
) -> None:
    """Verify reading progress via GET /api/courses/<id>/progress."""
    course, lesson = published_course
    enroll_student(student_user, course.id)
    db.session.commit()

    student_tokens = create_token_pair(student_user)
    student_headers = {"Authorization": f"Bearer {student_tokens['access_token']}"}

    # Student reads own progress
    resp = client.get(
        f"/api/courses/{course.public_id}/progress",
        headers=student_headers,
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["course_id"] == str(course.public_id)
    assert data["student_id"] == str(student_user.public_id)
    assert data["current_progress_percent"] == 0.0
    assert data["status"] == "ACTIVE"
    assert data["period_no"] == 1
    assert "id" not in data
    assert "current_period_id" not in data

    # Instructor reads student's progress
    inst_tokens = create_token_pair(instructor_user)
    inst_headers = {"Authorization": f"Bearer {inst_tokens['access_token']}"}

    resp_inst = client.get(
        f"/api/courses/{course.public_id}/progress?student_id={student_user.public_id}",
        headers=inst_headers,
    )
    assert resp_inst.status_code == 200
    inst_data = resp_inst.get_json()
    assert inst_data["student_id"] == str(student_user.public_id)


def test_get_student_completion_api(
    client: FlaskClient,
    student_user: User,
    published_course: tuple[Course, Lesson],
) -> None:
    """Verify student reading own completion summary via REST API."""
    course, lesson = published_course
    enroll_student(student_user, course.id)
    db.session.commit()

    tokens = create_token_pair(student_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # Before completion: ever_completed = False
    resp = client.get(
        f"/api/student/courses/{course.public_id}/completion",
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["course_id"] == str(course.public_id)
    assert data["student_id"] == str(student_user.public_id)
    assert data["ever_completed"] is False
    assert data["prerequisite_eligible"] is False
    assert data["current_status"] == "ACTIVE"
    assert data["current_progress_percent"] == 0.0
    assert "id" not in data

    # Student completes the lesson -> auto-triggers completion
    record_lesson_progress(student_user, lesson.id, seconds_increment=15, view_fraction=0.9)
    db.session.commit()

    # After completion: ever_completed = True, prerequisite_eligible = True
    resp_after = client.get(
        f"/api/student/courses/{course.public_id}/completion",
        headers=headers,
    )
    assert resp_after.status_code == 200
    data_after = resp_after.get_json()
    assert data_after["ever_completed"] is True
    assert data_after["prerequisite_eligible"] is True
    assert data_after["current_status"] == "COMPLETED"
    assert data_after["current_progress_percent"] == 100.0
    assert data_after["first_completed_at"] is not None
