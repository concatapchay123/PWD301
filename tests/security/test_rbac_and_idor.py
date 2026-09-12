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
from pwd301.models.assessment import Assessment
from pwd301.models.attempt_regrade import AssessmentAttempt
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
    """Unauthenticated Web HTML request redirects to login with relative next URL."""
    resp = client.get("/instructor/dashboard", headers={"Accept": "text/html"})
    assert resp.status_code == 302
    location = resp.headers["Location"]
    assert "/auth/login" in location
    # Requirement 4.3: next URL must be a valid safe relative URL to pass _is_safe_redirect_url
    assert "next=/instructor/dashboard" in location


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


def test_instructor_and_admin_cannot_call_api_to_submit_student_attempt(
    client: FlaskClient,
    student_user: User,
    instructor_a: User,
    admin_user: User,
    course_of_instructor_a: Course,
) -> None:
    """IDOR TEST: Neither Instructor nor Admin may call the API to submit on behalf of a student."""
    sess: Session = db.session

    # Create assessment and student attempt
    assessment = Assessment(
        course_id=course_of_instructor_a.id,
        title="Security Test Exam",
        assessment_type="QUIZ",
    )
    sess.add(assessment)
    sess.flush()

    attempt = AssessmentAttempt(
        assessment_id=assessment.id,
        enrollment_period_id=1,
        student_user_id=student_user.id,
        attempt_number=1,
        status="IN_PROGRESS",
    )
    sess.add(attempt)
    sess.commit()

    attempt_uuid = str(attempt.public_id)

    # 1. Instructor attempts to submit student's attempt via REST API -> 403
    inst_tokens = create_token_pair(instructor_a)
    inst_headers = {
        "Authorization": f"Bearer {inst_tokens['access_token']}",
        "Accept": "application/json",
    }
    resp = client.post(
        f"/api/attempts/{attempt_uuid}/submit",
        json={"submission_idempotency_key": "11111111-1111-1111-1111-111111111111"},
        headers=inst_headers,
    )
    assert resp.status_code == 403
    assert resp.get_json()["error"]["code"] == "FORBIDDEN"

    # 2. Admin attempts to submit student's attempt via REST API -> 403
    admin_tokens = create_token_pair(admin_user)
    admin_headers = {
        "Authorization": f"Bearer {admin_tokens['access_token']}",
        "Accept": "application/json",
    }
    resp = client.post(
        f"/api/attempts/{attempt_uuid}/submit",
        json={"submission_idempotency_key": "22222222-2222-2222-2222-222222222222"},
        headers=admin_headers,
    )
    assert resp.status_code == 403
    assert resp.get_json()["error"]["code"] == "FORBIDDEN"


def test_dual_auth_header_fail_closed_and_no_cookie_fallback(
    client: FlaskClient,
    student_user: User,
) -> None:
    """If an Authorization header is provided, it must fail-closed and not fall back to cookie."""
    # Log in student via Web session
    login_as(client, student_user.email)

    # Valid Web session can view student page
    resp_ok = client.get("/student/dashboard", headers={"Accept": "application/json"})
    assert resp_ok.status_code == 200

    # Request with invalid Bearer token must fail-closed (401 Unauthorized), NOT fall back to cookie
    resp_bad_jwt = client.get(
        "/student/dashboard",
        headers={
            "Authorization": "Bearer invalid_or_expired_jwt_token_here",
            "Accept": "application/json",
        },
    )
    assert resp_bad_jwt.status_code == 401
    assert resp_bad_jwt.get_json()["error"]["code"] == "UNAUTHORIZED"

    # Malformed authorization header also fails closed
    resp_malformed = client.get(
        "/student/dashboard",
        headers={
            "Authorization": "Basic not_bearer_token",
            "Accept": "application/json",
        },
    )
    assert resp_malformed.status_code == 401


def test_web_session_cookie_cannot_access_api_endpoints(
    client: FlaskClient,
    student_user: User,
) -> None:
    """CSRF invariant: Web session cookies alone must NOT authenticate /api/* endpoints."""
    login_as(client, student_user.email)

    # Attempt to access API endpoint using only session cookie (no Bearer header)
    resp = client.get("/api/student/enrollments", headers={"Accept": "application/json"})
    assert resp.status_code == 401
    assert resp.get_json()["error"]["code"] == "UNAUTHORIZED"


def test_web_session_cookie_cannot_access_api_bare_route(
    client: FlaskClient,
    student_user: User,
) -> None:
    """CSRF invariant: Web session cookies alone must NOT authenticate bare /api route."""
    from pwd301.services.authorization_service import get_authenticated_actor

    login_as(client, student_user.email)

    with client.application.test_request_context("/api", method="GET"):
        actor = get_authenticated_actor()
        assert actor is None


def test_post_login_redirect_preserves_intended_destination(
    client: FlaskClient,
    instructor_a: User,
) -> None:
    """Post-login redirect flow must preserve destination when using relative next URL."""
    # 1. Unauthenticated hit on instructor dashboard
    resp = client.get("/instructor/dashboard", headers={"Accept": "text/html"})
    assert resp.status_code == 302
    login_url = resp.headers["Location"]
    assert "next=/instructor/dashboard" in login_url

    # 2. Complete login with next parameter
    login_resp = client.post(
        login_url,
        data={
            "email": instructor_a.email,
            "password": "Password@123",
            "next": "/instructor/dashboard",
        },
        follow_redirects=False,
    )
    assert login_resp.status_code == 302
    # Must redirect to the requested target, NOT default landing
    assert login_resp.headers["Location"] == "/instructor/dashboard"


def test_demoted_former_instructor_cannot_access_or_grade_attempts(
    course_of_instructor_a: Course,
    instructor_a: User,
    student_user: User,
) -> None:
    """Layer 1 RBAC + Layer 2: Demoted instructor without role cannot view or grade attempts."""
    from pwd301.services.authorization_service import can_access_attempt, can_grade_attempt
    from pwd301.services.user_service import remove_role_from_user

    sess: Session = db.session
    assessment = Assessment(
        course_id=course_of_instructor_a.id,
        title="Exam",
        assessment_type="QUIZ",
    )
    sess.add(assessment)
    sess.flush()

    attempt = AssessmentAttempt(
        assessment_id=assessment.id,
        enrollment_period_id=1,
        student_user_id=student_user.id,
        attempt_number=1,
        status="IN_PROGRESS",
    )
    sess.add(attempt)
    sess.commit()

    # While still an instructor, can access and grade
    assert can_access_attempt(instructor_a, attempt) is True
    assert can_grade_attempt(instructor_a, attempt) is True

    # Demote instructor_a: remove INSTRUCTOR role
    remove_role_from_user(instructor_a.id, "INSTRUCTOR")
    sess.refresh(instructor_a)
    assert "INSTRUCTOR" not in instructor_a.role_codes

    # Demoted user (despite course.owner_instructor_id == instructor_a.id) must be denied
    assert can_access_attempt(instructor_a, attempt) is False
    assert can_grade_attempt(instructor_a, attempt) is False


def test_role_changes_dispatch_in_app_notification(
    student_user: User,
    admin_user: User,
) -> None:
    """Requirement 4.1: assign and remove role must dispatch notifications."""
    from pwd301.models.notification_audit import Notification
    from pwd301.services.user_service import assign_role_to_user, remove_role_from_user

    sess: Session = db.session
    initial_count = sess.query(Notification).filter_by(recipient_user_id=student_user.id).count()

    # Assign INSTRUCTOR role
    assign_role_to_user(
        student_user.id,
        "INSTRUCTOR",
        assigned_by_user_id=admin_user.id,
        reason="Promoted to instructor",
    )

    notifs_after_assign = (
        sess.query(Notification)
        .filter_by(recipient_user_id=student_user.id)
        .order_by(Notification.id.desc())
        .first()
    )
    assert notifs_after_assign is not None
    assert (
        sess.query(Notification).filter_by(recipient_user_id=student_user.id).count()
        == initial_count + 1
    )
    assert "INSTRUCTOR" in notifs_after_assign.body

    # Remove INSTRUCTOR role
    remove_role_from_user(
        student_user.id,
        "INSTRUCTOR",
        removed_by_user_id=admin_user.id,
        reason="Role revoked",
    )
    assert (
        sess.query(Notification).filter_by(recipient_user_id=student_user.id).count()
        == initial_count + 2
    )
