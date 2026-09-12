"""Integration tests for sliding toast popup notifications.

Verifies:
- Flash messages render inside floating `#toast-container` as `.app-toast` elements.
- The obsolete static inline alert banner in `#main-content` is eliminated.
- `#toast-container` exists on every page for client-side JavaScript `showToast` calls.
- Correct toast classes (`toast-success`, `toast-danger`, `toast-warning`, `toast-info`) and progress bars are rendered.
"""

from __future__ import annotations

from typing import Any
import pytest
from flask.testing import FlaskClient

from pwd301.extensions import db
from pwd301.models.course import Course
from pwd301.models.identity import User
from pwd301.seeds.baseline import seed_baseline
from pwd301.services.user_service import assign_role_to_user, register_user
from pwd301.services.course_service import change_course_status, create_course
from tests.conftest import login_web_user


@pytest.fixture
def toast_test_env(app: Any) -> dict[str, Any]:
    seed_baseline(db.session)
    admin = register_user(
        email="admin.toast@pwd301.local",
        password="Password@123",
        display_name="Admin Toast",
    )
    assign_role_to_user(admin.id, "ADMIN")

    instructor = register_user(
        email="instructor.toast@pwd301.local",
        password="Password@123",
        display_name="Instructor Toast",
    )
    assign_role_to_user(instructor.id, "INSTRUCTOR")

    student = register_user(
        email="student.toast@pwd301.local",
        password="Password@123",
        display_name="Student Toast",
    )
    assign_role_to_user(student.id, "STUDENT")

    course = create_course(
        instructor,
        {
            "course_code": "TOAST101",
            "title": "Toast Notification Testing Course",
            "summary": "Verifying slide-down top popup notifications",
        },
        session=db.session,
    )

    db.session.commit()
    return {
        "admin": admin,
        "instructor": instructor,
        "student": student,
        "course": course,
    }


def test_toast_container_always_present_in_base(client: FlaskClient) -> None:
    """Every page must include #toast-container for floating top slide-down toasts."""
    resp = client.get("/", headers={"Accept": "text/html"})
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    assert 'id="toast-container"' in html
    # Ensure obsolete static alert banner container is removed
    assert "Flash Messages Container" not in html


def test_instructor_submit_review_renders_slide_down_toast(
    client: FlaskClient, toast_test_env: dict[str, Any]
) -> None:
    """When an instructor submits a course for review, the success flash message must

    render as an .app-toast inside #toast-container, NOT an inline static alert.
    """
    instructor = toast_test_env["instructor"]
    course = toast_test_env["course"]
    login_web_user(client, instructor)

    # Submit course for review via POST
    resp = client.post(
        f"/instructor/courses/{course.public_id}/submit",
        headers={"Accept": "text/html"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")

    # Verify toast popup rendering
    assert 'id="toast-container"' in html
    assert "app-toast toast-success" in html
    assert "toast-progress" in html
    assert "toast-close-btn" in html
    assert "Khóa học đã được gửi tới Quản trị viên để xét duyệt xuất bản thành công." in html

    # Verify old inline static alert is NOT present in main content
    assert '<div class="alert alert-success alert-dismissible fade show" role="alert">' not in html


def test_login_success_renders_toast(
    client: FlaskClient, toast_test_env: dict[str, Any]
) -> None:
    """Login success flashes message as toast notification."""
    student = toast_test_env["student"]
    resp = client.post(
        "/auth/login",
        data={"email": student.email, "password": "Password@123"},
        headers={"Accept": "text/html"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    assert 'id="toast-container"' in html
    assert "app-toast toast-success" in html
    assert "Đăng nhập thành công!" in html
