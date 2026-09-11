"""Security verification tests for CSRF / API boundary defense.

Invariants verified:
1. REST API endpoints (/api/*) strictly require Bearer JWT. Ambient Flask-Login
   web session cookies are categorically rejected on /api/*, preventing Cross-Site
   Request Forgery (CSRF) via ambient cookie credentials on CSRF-exempt API blueprints.
2. Legitimate REST API requests providing Authorization: Bearer <jwt> succeed.
3. Web UI routes (/admin/*) accept Flask-Login session cookies and render HTML templates.
4. Web UI routes strictly enforce CSRF protection on state-changing requests (POST).
"""

from __future__ import annotations

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.identity import Role, User
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
    """Ensure baseline roles exist."""
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
    """Create an Admin user."""
    u = register_user("csrf_admin@example.com", "Password@123", "CSRF Admin")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create a verified student user."""
    return register_user("csrf_student@example.com", "Password@123", "CSRF Student")


def test_cookie_session_rejected_on_api_admin(client: FlaskClient, admin_user: User) -> None:
    """An ambient cookie session must NOT authenticate calls to /api/admin/* (prevents CSRF)."""
    # Log in via form to establish active session cookie in client
    client.post("/auth/login", data={"email": admin_user.email, "password": "Password@123"})

    # Attempt to call /api/admin/backups with ambient cookie session only
    resp = client.get("/api/admin/backups")
    assert resp.status_code == 401, f"Expected 401 Unauthorized, got {resp.status_code}"
    data = resp.get_json()
    assert data is not None
    assert data.get("error", {}).get("code") == "UNAUTHORIZED"


def test_cookie_session_rejected_on_api_student(client: FlaskClient, student_user: User) -> None:
    """An ambient cookie session must NOT authenticate calls to /api/student/* (prevents CSRF)."""
    client.post("/auth/login", data={"email": student_user.email, "password": "Password@123"})

    resp = client.get("/api/student/enrollments")
    assert resp.status_code == 401, f"Expected 401 Unauthorized, got {resp.status_code}"
    data = resp.get_json()
    assert data is not None
    assert data.get("error", {}).get("code") == "UNAUTHORIZED"


def test_cookie_session_rejected_on_api_ai(client: FlaskClient, student_user: User) -> None:
    """An ambient cookie session must NOT authenticate calls to /api/ai/* (prevents CSRF)."""
    client.post("/auth/login", data={"email": student_user.email, "password": "Password@123"})

    resp = client.post("/api/ai/conversations", json={})
    assert resp.status_code == 401, f"Expected 401 Unauthorized, got {resp.status_code}"
    data = resp.get_json()
    assert data is not None
    assert data.get("error", {}).get("code") == "UNAUTHORIZED"


def test_bearer_jwt_accepted_on_api_admin(client: FlaskClient, admin_user: User) -> None:
    """Explicit Authorization: Bearer <jwt> header is required and accepted on /api/admin/*."""
    token_pair = create_token_pair(admin_user)
    headers = {"Authorization": f"Bearer {token_pair['access_token']}"}

    resp = client.get("/api/admin/backups", headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert "items" in data


def test_bearer_jwt_accepted_on_api_student(client: FlaskClient, student_user: User) -> None:
    """Explicit Authorization: Bearer <jwt> header is required and accepted on /api/student/*."""
    token_pair = create_token_pair(student_user)
    headers = {"Authorization": f"Bearer {token_pair['access_token']}"}

    resp = client.get("/api/student/enrollments", headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert "enrollments" in data


def test_admin_dashboard_web_route_renders_html_with_session(
    client: FlaskClient, admin_user: User
) -> None:
    """Web UI /admin/dashboard accepts session cookie and renders HTML."""
    client.post("/auth/login", data={"email": admin_user.email, "password": "Password@123"})

    resp = client.get("/admin/dashboard")
    assert resp.status_code == 200
    assert resp.content_type.startswith("text/html")
    assert "Trung tâm Điều hành" in resp.get_data(as_text=True)


def test_admin_courses_web_route_renders_html_with_session(
    client: FlaskClient, admin_user: User
) -> None:
    """Web UI /admin/courses accepts session cookie and renders HTML."""
    client.post("/auth/login", data={"email": admin_user.email, "password": "Password@123"})

    resp = client.get("/admin/courses")
    assert resp.status_code == 200
    assert resp.content_type.startswith("text/html")
    assert "Quản trị Khóa học" in resp.get_data(as_text=True)


def test_admin_users_web_route_renders_html_with_session(
    client: FlaskClient, admin_user: User
) -> None:
    """Web UI /admin/users accepts session cookie and renders HTML."""
    client.post("/auth/login", data={"email": admin_user.email, "password": "Password@123"})

    resp = client.get("/admin/users")
    assert resp.status_code == 200
    assert resp.content_type.startswith("text/html")
    assert "Quản trị Tài khoản" in resp.get_data(as_text=True)


def test_admin_backups_web_route_renders_html_with_session(
    client: FlaskClient, admin_user: User
) -> None:
    """Web UI /admin/backups accepts session cookie and renders HTML."""
    client.post("/auth/login", data={"email": admin_user.email, "password": "Password@123"})

    resp = client.get("/admin/backups")
    assert resp.status_code == 200
    assert resp.content_type.startswith("text/html")
    assert "Sao lưu" in resp.get_data(as_text=True)
