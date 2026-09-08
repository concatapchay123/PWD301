"""Integration tests for Course REST API endpoints per 04_COURSE_API.md."""

from __future__ import annotations

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
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
    """Create an instructor user."""
    u = register_user("api_instructor@example.com", "Password@123", "API Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create an admin user."""
    u = register_user("api_admin@example.com", "Password@123", "API Admin")
    return assign_role_to_user(u.id, "ADMIN")


def test_api_create_course(client: FlaskClient, instructor_user: User) -> None:
    """Test POST /api/courses creates course in DRAFT."""
    tokens = create_token_pair(instructor_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = client.post(
        "/api/courses",
        headers=headers,
        json={
            "course_code": "API-101",
            "title": "API Design Fundamentals",
            "description": "Learn RESTful API patterns",
            "category": "Engineering",
            "difficulty": "BEGINNER",
            "capacity": 30,
        },
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["course_code"] == "API-101"
    assert data["title"] == "API Design Fundamentals"
    assert data["status"] == "DRAFT"


def test_api_course_catalog_and_filtering(
    client: FlaskClient,
    instructor_user: User,
    admin_user: User,
) -> None:
    """Test GET /api/courses returns published courses with pagination."""
    c1 = create_course(
        instructor_user,
        {"course_code": "PUB-101", "title": "Published Python", "category": "Python"},
    )
    change_course_status(instructor_user, c1.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin_user, c1.id, "APPROVED")
    change_course_status(instructor_user, c1.id, "PUBLISHED")

    # Draft course should not appear for anonymous
    create_course(
        instructor_user,
        {"course_code": "DFT-101", "title": "Draft Secret Course"},
    )

    resp = client.get("/api/courses")
    assert resp.status_code == 200
    res = resp.get_json()
    assert res["pagination"]["total_items"] == 1
    assert res["items"][0]["course_code"] == "PUB-101"


def test_api_update_course(client: FlaskClient, instructor_user: User) -> None:
    """Test PATCH /api/courses/<id>."""
    course = create_course(
        instructor_user,
        {"course_code": "UPD-101", "title": "Initial Title"},
    )
    tokens = create_token_pair(instructor_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = client.patch(
        f"/api/courses/{course.public_id}",
        headers=headers,
        json={"title": "Updated Title", "difficulty": "ADVANCED"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["title"] == "Updated Title"
    assert data["difficulty"] == "ADVANCED"


def test_api_publish_request_and_archive(
    client: FlaskClient,
    instructor_user: User,
    admin_user: User,
) -> None:
    """Test POST /api/courses/<id>/publish-request and POST /api/courses/<id>/archive."""
    course = create_course(
        instructor_user,
        {"course_code": "LIFECYCLE-101", "title": "Lifecycle Course"},
    )
    tokens = create_token_pair(instructor_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # 1. Submit for review
    resp = client.post(
        f"/api/courses/{course.public_id}/publish-request",
        headers=headers,
        json={"reason": "Ready for student enrollment"},
    )
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "SUBMITTED_FOR_REVIEW"

    # 2. Admin approves and publishes
    change_course_status(admin_user, course.id, "APPROVED")
    change_course_status(instructor_user, course.id, "PUBLISHED")

    # 3. Archive
    resp = client.post(
        f"/api/courses/{course.public_id}/archive",
        headers=headers,
        json={"reason": "Course retired"},
    )
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ARCHIVED"
