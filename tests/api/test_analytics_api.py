"""Integration tests for Analytics REST API & Web Endpoints (TASK-025).

Verifies:
- GET /api/admin/analytics/overview with Admin Bearer JWT -> 200 OK & valid schema.
- GET /instructor/courses/<course_id>/analytics with Web session or token -> 200 OK & schema.
- GET /api/courses/<course_id>/analytics with Instructor Bearer token -> 200 OK & valid schema.
- GET /api/student/analytics/overview with Student Bearer JWT -> 200 OK & valid schema.
"""

from __future__ import annotations

import uuid

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
from tests.conftest import login_web_user


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
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test admin user."""
    u = register_user(f"api_admin_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "API Admin")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test instructor user."""
    u = register_user(
        f"api_inst_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "API Instructor"
    )
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test student user."""
    return register_user(
        f"api_student_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "API Student"
    )


@pytest.fixture
def managed_course(app: Flask, instructor_user: User) -> Course:
    """Create course managed by instructor_user."""
    sess: Session = db.session
    course = create_course(
        actor=instructor_user,
        data={
            "course_code": f"API-CRS-{uuid.uuid4().hex[:4]}",
            "title": "API Analytics Test Course",
        },
        session=sess,
    )
    course.status = "PUBLISHED"
    sess.commit()
    return course


def test_admin_analytics_overview_api(
    client: FlaskClient,
    admin_user: User,
) -> None:
    """Test GET /api/admin/analytics/overview with Admin Bearer JWT returns 200 OK."""
    tokens = create_token_pair(admin_user)
    headers = {
        "Authorization": f"Bearer {tokens['access_token']}",
        "Accept": "application/json",
    }

    resp = client.get("/api/admin/analytics/overview", headers=headers)
    assert resp.status_code == 200

    data = resp.get_json()
    assert "admin_id" in data
    assert "total_users" in data
    assert "total_courses" in data

    # Users structure
    assert "users" in data
    assert "by_role" in data["users"]
    assert "STUDENT" in data["users"]["by_role"]
    assert "INSTRUCTOR" in data["users"]["by_role"]
    assert "ADMIN" in data["users"]["by_role"]
    assert "by_status" in data["users"]
    assert "ACTIVE" in data["users"]["by_status"]
    assert "SUSPENDED" in data["users"]["by_status"]
    assert "PENDING_VERIFICATION" in data["users"]["by_status"]

    # Courses structure
    assert "courses" in data
    assert "by_status" in data["courses"]
    assert "DRAFT" in data["courses"]["by_status"]
    assert "PUBLISHED" in data["courses"]["by_status"]

    # Enrollments structure
    assert "enrollments" in data
    assert "total_enrollments" in data["enrollments"]
    assert "active_enrollments" in data["enrollments"]
    assert "completed_enrollments" in data["enrollments"]

    # Assessments structure
    assert "assessments" in data
    assert "total_submissions" in data["assessments"]
    assert "needs_grading_count" in data["assessments"]

    # Storage structure
    assert "storage" in data
    assert "total_bytes" in data["storage"]
    assert "clean_files_count" in data["storage"]
    assert "quarantined_files_count" in data["storage"]


def test_instructor_course_analytics_web_and_api(
    client: FlaskClient,
    instructor_user: User,
    student_user: User,
    managed_course: Course,
) -> None:
    """Test course analytics retrieval via both Web session and JWT REST API."""
    sess: Session = db.session
    enroll_student(actor=student_user, course_id=managed_course.id, session=sess)
    sess.commit()

    course_id = str(managed_course.public_id)

    # 1. Test via REST API with Bearer JWT
    tokens = create_token_pair(instructor_user)
    headers = {
        "Authorization": f"Bearer {tokens['access_token']}",
        "Accept": "application/json",
    }
    resp_api = client.get(f"/api/courses/{course_id}/analytics", headers=headers)
    assert resp_api.status_code == 200

    api_data = resp_api.get_json()
    assert api_data["course_id"] == course_id
    assert api_data["enrolled_students_count"] >= 1
    assert "completion_rate_percent" in api_data
    assert "average_progress_percent" in api_data
    assert "progress_distribution" in api_data
    assert "0-25" in api_data["progress_distribution"]
    assert "25-50" in api_data["progress_distribution"]
    assert "50-75" in api_data["progress_distribution"]
    assert "75-100" in api_data["progress_distribution"]
    assert "assessment_performance" in api_data

    # 2. Test via Web Session route /instructor/courses/<course_id>/analytics
    login_web_user(client, instructor_user)
    resp_web = client.get(
        f"/instructor/courses/{course_id}/analytics",
        headers={"Accept": "application/json"},
    )
    assert resp_web.status_code == 200
    web_data = resp_web.get_json()
    assert web_data["course_id"] == course_id


def test_student_analytics_overview_api(
    client: FlaskClient,
    student_user: User,
    managed_course: Course,
) -> None:
    """Test GET /api/student/analytics/overview with Student Bearer JWT returns 200 OK."""
    sess: Session = db.session
    enroll_student(actor=student_user, course_id=managed_course.id, session=sess)
    sess.commit()

    tokens = create_token_pair(student_user)
    headers = {
        "Authorization": f"Bearer {tokens['access_token']}",
        "Accept": "application/json",
    }

    resp = client.get("/api/student/analytics/overview", headers=headers)
    assert resp.status_code == 200

    data = resp.get_json()
    assert data["student_id"] == str(student_user.public_id)
    assert data["enrolled_courses_count"] >= 1
    assert data["active_courses_count"] >= 1
    assert "completed_courses_count" in data
    assert "overall_average_progress_percent" in data
    assert "server_time" in data
    assert "upcoming_assessments" in data
    assert "recent_results" in data
    assert "enrollments" in data


def test_admin_telemetry_endpoints(
    client: FlaskClient,
    admin_user: User,
    student_user: User,
) -> None:
    """Test GET /admin/telemetry and GET /api/admin/telemetry return real hardware metrics."""
    # 1. Admin Web session to /admin/telemetry
    login_web_user(client, admin_user)
    resp_web = client.get("/admin/telemetry")
    assert resp_web.status_code == 200
    web_data = resp_web.get_json()
    assert isinstance(web_data, dict)
    assert "cpu" in web_data and "memory" in web_data and "disk" in web_data
    assert web_data["cpu"]["cores"] >= 1
    assert "model" in web_data["cpu"]
    assert web_data["memory"]["total_gb"] > 0
    assert web_data["disk"]["total_gb"] > 0
    assert "node_label" in web_data

    # 2. Admin Bearer JWT to /api/admin/telemetry
    tokens = create_token_pair(admin_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp_api = client.get("/api/admin/telemetry", headers=headers)
    assert resp_api.status_code == 200
    api_data = resp_api.get_json()
    assert api_data["hostname"] == web_data["hostname"]
    assert api_data["cpu"]["cores"] == web_data["cpu"]["cores"]

    # 3. Student forbidden on telemetry
    login_web_user(client, student_user)
    resp_forbidden = client.get("/admin/telemetry")
    assert resp_forbidden.status_code == 403


def test_admin_dashboard_web_renders_hardware_telemetry(
    client: FlaskClient,
    admin_user: User,
) -> None:
    """Admin dashboard /admin/dashboard renders HTML with real hardware telemetry."""
    import re
    login_web_user(client, admin_user)
    resp = client.get("/admin/dashboard")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    assert (
        "Trung tâm Điều hành &amp; Quản trị Hệ thống" in html
        or "Trung tâm Điều hành & Quản trị Hệ thống" in html
    )
    assert "Vi xử lý CPU" in html
    assert "Bộ nhớ RAM" in html
    assert "Lưu trữ Ổ đĩa" in html
    assert "Lưu lượng Mạng" in html
    assert "btn-refresh-telemetry" in html
    assert "refreshServerTelemetry" in html

    # Deep verification: Assert DOM elements contain real hardware values, not nulls
    cores_match = re.search(r'id="telem-cpu-cores"[^>]*>(\d+)\s*Cores<', html)
    assert cores_match and int(cores_match.group(1)) >= 1

    ram_match = re.search(r'id="telem-ram-label"[^>]*>([^<]+)<', html)
    assert ram_match and "GB" in ram_match.group(1)
    assert ram_match.group(1) != "0 / 0 GB"

    disk_match = re.search(r'id="telem-disk-label"[^>]*>([^<]+)<', html)
    assert disk_match and "GB" in disk_match.group(1)

    node_match = re.search(r'id="telem-node-label"[^>]*>([^<]+)<', html)
    assert node_match and (
        "Docker" in node_match.group(1)
        or "Host" in node_match.group(1)
        or "Node" in node_match.group(1)
    )


def test_admin_dashboard_resilient_when_telemetry_throws_exception(
    client: FlaskClient,
    admin_user: User,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify admin dashboard degrades safely without HTTP 500 when telemetry fails."""
    import pwd301.services.operations_service

    def _failing_telemetry() -> None:
        raise RuntimeError("Hardware telemetry probe hardware sensor bus failure.")

    monkeypatch.setattr(
        pwd301.services.operations_service,
        "get_real_system_telemetry",
        _failing_telemetry,
    )

    login_web_user(client, admin_user)
    resp = client.get("/admin/dashboard")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Trung tâm Điều hành" in html
    assert "Vi xử lý CPU" in html

