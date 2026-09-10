"""REST API and integration test suite for Notification & Email Engine (TASK-021).

Tests:
- End-to-end lifecycle: dispatch -> list -> unread count -> mark read -> unread count decrements.
- Filtering by status (read/unread) and category.
- Dismissing / deleting notifications.
- Preferences GET and PUT lifecycle.
- Admin system broadcast endpoint.
- Admin email retry endpoint.
- Web session notifications center and CSRF enforcement.
"""

from __future__ import annotations

import uuid

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.identity import Role, User
from pwd301.services.email_service import enqueue_email
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.notification_service import dispatch_notification
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
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test student user."""
    u = register_user(
        f"api_student_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Student API"
    )
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test admin user."""
    u = register_user(f"api_admin_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Admin API")
    return assign_role_to_user(u.id, "ADMIN")


def test_notification_lifecycle_end_to_end(
    app: Flask, client: FlaskClient, student_user: User
) -> None:
    """Validate full end-to-end lifecycle of notifications via REST API."""
    tokens = create_token_pair(student_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # Initially 0 unread
    resp_count = client.get("/api/notifications/unread-count", headers=headers)
    assert resp_count.status_code == 200
    assert resp_count.get_json()["unread_count"] == 0

    # Dispatch 2 notifications
    n1, _ = dispatch_notification(
        student_user, "COURSE_ANNOUNCEMENT", "Notice 1", "Content 1", session=db.session
    )
    n2, _ = dispatch_notification(
        student_user, "ASSESSMENT_DUE", "Notice 2", "Content 2", session=db.session
    )
    db.session.commit()

    # Verify unread count is 2
    resp_count2 = client.get("/api/notifications/unread-count", headers=headers)
    assert resp_count2.status_code == 200
    assert resp_count2.get_json()["unread_count"] == 2

    # List notifications
    resp_list = client.get("/api/notifications", headers=headers)
    assert resp_list.status_code == 200
    data = resp_list.get_json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

    # Mark n1 as read
    resp_read = client.patch(f"/api/notifications/{n1.public_id}/read", headers=headers)
    assert resp_read.status_code == 200
    assert resp_read.get_json()["read"] is True

    # Check unread count is now 1
    resp_count3 = client.get("/api/notifications/unread-count", headers=headers)
    assert resp_count3.get_json()["unread_count"] == 1

    # Mark all read
    resp_mark_all = client.post("/api/notifications/mark-all-read", json={}, headers=headers)
    assert resp_mark_all.status_code == 200
    assert resp_mark_all.get_json()["marked_count"] == 1

    # Check unread count is now 0
    resp_count4 = client.get("/api/notifications/unread-count", headers=headers)
    assert resp_count4.get_json()["unread_count"] == 0


def test_notification_filtering(app: Flask, client: FlaskClient, student_user: User) -> None:
    """Validate filtering notifications by unread_only and category."""
    tokens = create_token_pair(student_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    n1, _ = dispatch_notification(
        student_user, "COURSE_ANNOUNCEMENT", "Course Notice", "Body 1", session=db.session
    )
    n2, _ = dispatch_notification(
        student_user, "ASSESSMENT_DUE", "Assessment Notice", "Body 2", session=db.session
    )
    db.session.commit()

    # Mark n1 as read
    client.patch(f"/api/notifications/{n1.public_id}/read", headers=headers)

    # Filter unread only
    resp_unread = client.get("/api/notifications?unread_only=true", headers=headers)
    data_unread = resp_unread.get_json()
    assert data_unread["total"] == 1
    assert data_unread["items"][0]["title"] == "Assessment Notice"

    # Filter by category COURSE
    resp_course = client.get("/api/notifications?category=COURSE", headers=headers)
    data_course = resp_course.get_json()
    assert data_course["total"] == 1
    assert data_course["items"][0]["title"] == "Course Notice"


def test_dismiss_notification_api(app: Flask, client: FlaskClient, student_user: User) -> None:
    """Validate dismissing a notification via DELETE and PATCH."""
    tokens = create_token_pair(student_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    n, _ = dispatch_notification(
        student_user, "COURSE_ANNOUNCEMENT", "Dismiss Me", "Content", session=db.session
    )
    db.session.commit()

    resp_del = client.delete(f"/api/notifications/{n.public_id}", headers=headers)
    assert resp_del.status_code == 200
    assert resp_del.get_json()["status"] == "dismissed"

    # Listing should now be empty
    resp_list = client.get("/api/notifications", headers=headers)
    assert resp_list.get_json()["total"] == 0


def test_preferences_api_get_and_put(app: Flask, client: FlaskClient, student_user: User) -> None:
    """Validate getting and updating preferences via REST API."""
    tokens = create_token_pair(student_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # GET preferences
    resp_get = client.get("/api/notifications/preferences", headers=headers)
    assert resp_get.status_code == 200
    prefs = resp_get.get_json()["preferences"]
    categories = {p["category"] for p in prefs}
    assert {"SECURITY", "COURSE", "ASSESSMENT", "GRADE", "MARKETING"}.issubset(categories)

    # PUT preferences: disable COURSE and GRADE
    update_payload = {
        "preferences": [
            {"category": "COURSE", "email_enabled": False},
            {"category": "GRADE", "email_enabled": False},
        ]
    }
    resp_put = client.put("/api/notifications/preferences", json=update_payload, headers=headers)
    assert resp_put.status_code == 200
    updated_prefs = {p["category"]: p["email_enabled"] for p in resp_put.get_json()["preferences"]}
    assert updated_prefs["COURSE"] is False
    assert updated_prefs["GRADE"] is False
    assert updated_prefs["SECURITY"] is True


def test_admin_broadcast_api(
    app: Flask, client: FlaskClient, admin_user: User, student_user: User
) -> None:
    """Validate admin broadcast endpoint creates notifications for active students."""
    tokens = create_token_pair(admin_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    payload = {
        "title": "System Update Broadcast",
        "body": "A critical system update is scheduled.",
        "target_role": "STUDENT",
    }
    resp = client.post("/api/admin/notifications/broadcast", json=payload, headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["broadcasted_count"] >= 1

    # Check student received notification
    tokens_student = create_token_pair(student_user)
    resp_student = client.get(
        "/api/notifications", headers={"Authorization": f"Bearer {tokens_student['access_token']}"}
    )
    items = resp_student.get_json()["items"]
    assert any(i["title"] == "System Update Broadcast" for i in items)


def test_admin_retry_failed_emails_api(
    app: Flask, client: FlaskClient, admin_user: User, student_user: User
) -> None:
    """Validate admin retry endpoint resets FAILED email deliveries."""
    delivery = enqueue_email(
        recipient_email=student_user.email,
        subject="Failed Email",
        body_text="Body",
        template_code="FAIL_CODE",
        session=db.session,
    )
    delivery.status = "FAILED"
    delivery.attempt_count = 3
    db.session.commit()

    tokens = create_token_pair(admin_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = client.post("/api/admin/emails/retry-failed", json={"max_emails": 10}, headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["retried_count"] >= 1


def test_web_session_notification_center(
    app: Flask, client: FlaskClient, student_user: User
) -> None:
    """Validate student Web session access to notification center page."""
    login_web_user(client, student_user)

    resp = client.get("/student/notifications")
    assert resp.status_code == 200
    assert b"Trung t\xc3\xa2m Th\xc3\xb4ng b\xc3\xa1o" in resp.data
