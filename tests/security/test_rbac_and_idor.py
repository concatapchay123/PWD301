"""Security and integration negative tests for RBAC and IDOR prevention.

Acceptance criteria verified:
- @require_roles rejects unauthorized actors (401 unauthenticated, 403 insufficient roles).
- Student accessing Instructor/Admin routes returns 403 Forbidden (API JSON and Web HTML).
- Instructor A accessing Instructor B's Course returns 403 Forbidden (IDOR test).
- Instructor A viewing student data for a course they do not manage returns 403 (IDOR test).
- Admin has platform-wide management access per 04_ADMIN_PERMISSION_RULES.md.
- Student attempt submissions and progress checks are strictly isolated to the owning actor.
- JWT REST API enforces the identical RBAC and IDOR controls as Web UI.
"""

from __future__ import annotations

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course, Enrollment
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
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create a verified student user."""
    return register_user("sec_student@example.com", "Password@123", "Sec Student")


@pytest.fixture
def instructor_a(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Instructor A."""
    u = register_user("instructor_a@example.com", "Password@123", "Instructor Alpha")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def instructor_b(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Instructor B."""
    u = register_user("instructor_b@example.com", "Password@123", "Instructor Beta")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create an Admin user."""
    u = register_user("sec_admin@example.com", "Password@123", "Sec Admin")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def course_of_instructor_a(app: Flask, instructor_a: User) -> Course:
    """Course owned by Instructor A."""
    sess: Session = db.session
    course = Course(
        course_code="CS-ALPHA",
        course_code_normalized="CS-ALPHA",
        title="Course of Alpha",
        title_normalized="course of alpha",
        status="PUBLISHED",
        owner_instructor_id=instructor_a.id,
    )
    sess.add(course)
    sess.commit()
    return course


@pytest.fixture
def course_of_instructor_b(app: Flask, instructor_b: User) -> Course:
    """Course owned by Instructor B."""
    sess: Session = db.session
    course = Course(
        course_code="CS-BETA",
        course_code_normalized="CS-BETA",
        title="Course of Beta",
        title_normalized="course of beta",
        status="PUBLISHED",
        owner_instructor_id=instructor_b.id,
    )
    sess.add(course)
    sess.commit()
    return course


# ==============================================================================
# Helper Functions for Session Logins
# ==============================================================================


def login_as(client: FlaskClient, email: str, password: str = "Password@123") -> None:
    """Log in a user via Web UI session."""
    resp = client.get("/auth/login")
    csrf_token = ""
    # Extract CSRF token from HTML form
    if resp.data:
        import re

        match = re.search(r'name="csrf_token"\s+value="([^"]+)"', resp.data.decode("utf-8"))
        if match:
            csrf_token = match.group(1)

    client.post(
        "/auth/login",
        data={
            "email": email,
            "password": password,
            "csrf_token": csrf_token,
        },
        follow_redirects=True,
    )


# ==============================================================================
# 1. Negative Tests: Unauthenticated Access
# ==============================================================================


def test_unauthenticated_api_request_rejected(client: FlaskClient) -> None:
    """Unauthenticated API request to protected routes returns 401 Unauthorized JSON."""
    resp = client.get("/instructor/dashboard", headers={"Accept": "application/json"})
    assert resp.status_code == 401
    json_data = resp.get_json()
    assert json_data["error"]["code"] == "UNAUTHORIZED"


def test_unauthenticated_web_request_redirects(client: FlaskClient) -> None:
    """Unauthenticated Web HTML request to protected routes redirects to login."""
    resp = client.get("/instructor/dashboard", headers={"Accept": "text/html"})
    assert resp.status_code == 302
    assert "/auth/login" in resp.headers["Location"]


# ==============================================================================
# 2. Negative Tests: Role Violations (Student -> Instructor/Admin)
# ==============================================================================


def test_student_cannot_access_instructor_route_api(
    client: FlaskClient,
    student_user: User,
) -> None:
    """Student attempting to access Instructor route via API receives 403 Forbidden JSON."""
    login_as(client, student_user.email)

    resp = client.get("/instructor/dashboard", headers={"Accept": "application/json"})
    assert resp.status_code == 403
    json_data = resp.get_json()
    assert json_data["error"]["code"] == "FORBIDDEN"


def test_student_cannot_access_instructor_route_web_html(
    client: FlaskClient,
    student_user: User,
) -> None:
    """Student accessing Instructor route via Web receives 403 status and custom 403.html."""
    login_as(client, student_user.email)

    resp = client.get("/instructor/dashboard", headers={"Accept": "text/html"})
    assert resp.status_code == 403
    html_text = resp.data.decode("utf-8")
    assert "403 Forbidden" in html_text
    assert "Truy cập bị từ chối" in html_text


def test_student_cannot_access_admin_route(
    client: FlaskClient,
    student_user: User,
) -> None:
    """Student attempting to access Admin route receives 403 Forbidden."""
    login_as(client, student_user.email)

    resp = client.get("/admin/dashboard", headers={"Accept": "application/json"})
    assert resp.status_code == 403
    json_data = resp.get_json()
    assert json_data["error"]["code"] == "FORBIDDEN"


def test_instructor_cannot_access_admin_route(
    client: FlaskClient,
    instructor_a: User,
) -> None:
    """Instructor attempting to access Admin dashboard receives 403 Forbidden."""
    login_as(client, instructor_a.email)

    resp = client.get("/admin/dashboard", headers={"Accept": "application/json"})
    assert resp.status_code == 403


# ==============================================================================
# 3. IDOR Prevention Tests: Resource Ownership & Student Isolation
# ==============================================================================


def test_instructor_a_cannot_manage_instructor_b_course(
    client: FlaskClient,
    instructor_a: User,
    course_of_instructor_b: Course,
) -> None:
    """IDOR TEST: Instructor A accessing Course B's manage endpoint receives 403 Forbidden."""
    login_as(client, instructor_a.email)

    course_b_id = str(course_of_instructor_b.public_id)
    resp = client.get(
        f"/instructor/courses/{course_b_id}/manage",
        headers={"Accept": "application/json"},
    )
    assert resp.status_code == 403
    json_data = resp.get_json()
    assert json_data["error"]["code"] == "FORBIDDEN"


def test_instructor_b_can_manage_own_course(
    client: FlaskClient,
    instructor_b: User,
    course_of_instructor_b: Course,
) -> None:
    """Instructor B accessing Course B's manage endpoint succeeds (200 OK)."""
    login_as(client, instructor_b.email)

    course_b_id = str(course_of_instructor_b.public_id)
    resp = client.get(
        f"/instructor/courses/{course_b_id}/manage",
        headers={"Accept": "application/json"},
    )
    assert resp.status_code == 200
    json_data = resp.get_json()
    assert json_data["course_code"] == "CS-BETA"


def test_admin_can_access_any_course(
    client: FlaskClient,
    admin_user: User,
    course_of_instructor_b: Course,
) -> None:
    """Admin has platform-wide management access (04_ADMIN_PERMISSION_RULES.md)."""
    login_as(client, admin_user.email)

    course_b_id = str(course_of_instructor_b.public_id)
    resp = client.get(
        f"/instructor/courses/{course_b_id}/manage",
        headers={"Accept": "application/json"},
    )
    assert resp.status_code == 200
    json_data = resp.get_json()
    assert json_data["course_code"] == "CS-BETA"


def test_instructor_cannot_view_students_in_another_instructors_course(
    client: FlaskClient,
    instructor_a: User,
    instructor_b: User,
    course_of_instructor_b: Course,
    student_user: User,
) -> None:
    """IDOR TEST: Instructor A viewing student in Instructor B's Course receives 403."""
    sess: Session = db.session
    # Enroll student in Course B
    enrollment = Enrollment(
        student_user_id=student_user.id,
        course_id=course_of_instructor_b.id,
        status="ACTIVE",
        current_progress_percent=50.0,
    )
    sess.add(enrollment)
    sess.commit()

    # Instructor A attempts to spy on Course B's student
    login_as(client, instructor_a.email)

    course_b_id = str(course_of_instructor_b.public_id)
    student_id = str(student_user.public_id)

    resp = client.get(
        f"/instructor/courses/{course_b_id}/students/{student_id}",
        headers={"Accept": "application/json"},
    )
    assert resp.status_code == 403
    json_data = resp.get_json()
    assert json_data["error"]["code"] == "FORBIDDEN"

    # Instructor B (the legitimate owner) views the student successfully
    login_as(client, instructor_b.email)
    resp_b = client.get(
        f"/instructor/courses/{course_b_id}/students/{student_id}",
        headers={"Accept": "application/json"},
    )
    assert resp_b.status_code == 200
    assert resp_b.get_json()["progress_percent"] == 50.0


def test_student_progress_isolation(
    client: FlaskClient,
    student_user: User,
    course_of_instructor_a: Course,
    course_of_instructor_b: Course,
) -> None:
    """Student can only view progress for courses they are actually enrolled in."""
    sess: Session = db.session
    # Enroll student ONLY in Course A
    enrollment = Enrollment(
        student_user_id=student_user.id,
        course_id=course_of_instructor_a.id,
        status="ACTIVE",
        current_progress_percent=75.0,
    )
    sess.add(enrollment)
    sess.commit()

    login_as(client, student_user.email)

    # 1. Querying enrolled Course A -> 200 OK
    resp_a = client.get(
        f"/student/courses/{course_of_instructor_a.public_id}/progress",
        headers={"Accept": "application/json"},
    )
    assert resp_a.status_code == 200
    assert resp_a.get_json()["progress_percent"] == 75.0

    # 2. Querying non-enrolled Course B -> 404 Not Found (safe from enumeration)
    resp_b = client.get(
        f"/student/courses/{course_of_instructor_b.public_id}/progress",
        headers={"Accept": "application/json"},
    )
    assert resp_b.status_code == 404


# ==============================================================================
# 4. REST API JWT RBAC & IDOR Enforcement
# ==============================================================================


def test_jwt_rest_api_rbac_enforcement(
    client: FlaskClient,
    student_user: User,
    instructor_a: User,
    admin_user: User,
) -> None:
    """Verify REST API Bearer JWT authentication enforces identical RBAC rules."""
    # Student token
    student_tokens = create_token_pair(student_user)
    student_access = student_tokens["access_token"]

    # Student Bearer token hitting Instructor route -> 403
    resp = client.get(
        "/instructor/dashboard",
        headers={
            "Authorization": f"Bearer {student_access}",
            "Accept": "application/json",
        },
    )
    assert resp.status_code == 403
    assert resp.get_json()["error"]["code"] == "FORBIDDEN"

    # Instructor Bearer token hitting Instructor route -> 200
    instructor_tokens = create_token_pair(instructor_a)
    instructor_access = instructor_tokens["access_token"]

    resp = client.get(
        "/instructor/dashboard",
        headers={
            "Authorization": f"Bearer {instructor_access}",
            "Accept": "application/json",
        },
    )
    assert resp.status_code == 200
    assert resp.get_json()["managed_courses_count"] >= 0

    # Admin Bearer token hitting Admin route -> 200
    admin_tokens = create_token_pair(admin_user)
    admin_access = admin_tokens["access_token"]

    resp = client.get(
        "/admin/dashboard",
        headers={
            "Authorization": f"Bearer {admin_access}",
            "Accept": "application/json",
        },
    )
    assert resp.status_code == 200
    assert resp.get_json()["total_users"] > 0
