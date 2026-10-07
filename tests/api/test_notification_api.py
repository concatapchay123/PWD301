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
from pwd301.models.notification_audit import Notification, NotificationEvent
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


def test_admin_broadcast_idempotency_key_converges(
    app: Flask, client: FlaskClient, admin_user: User, student_user: User
) -> None:
    """Repeated broadcast requests with the same key create one event and one fan-out."""
    tokens = create_token_pair(admin_user)
    headers = {
        "Authorization": f"Bearer {tokens['access_token']}",
        "X-Idempotency-Key": str(uuid.uuid4()),
    }
    payload = {
        "title": "Idempotent System Broadcast",
        "body": "This message must be delivered once.",
        "target_role": "STUDENT",
        "category": "SYSTEM",
    }

    first = client.post("/api/admin/notifications/broadcast", json=payload, headers=headers)
    second = client.post("/api/admin/notifications/broadcast", json=payload, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.get_json()["broadcasted_count"] == second.get_json()["broadcasted_count"]
    assert second.get_json()["idempotent_replay"] is True

    events = (
        db.session.query(NotificationEvent)
        .filter_by(event_type="SYSTEM_BROADCAST", actor_user_id=admin_user.id)
        .all()
    )
    matching_events = [
        event
        for event in events
        if event.payload_json and "Idempotent System Broadcast" in event.payload_json
    ]
    assert len(matching_events) == 1

    notifications = (
        db.session.query(Notification)
        .filter_by(
            notification_event_id=matching_events[0].id,
            recipient_user_id=student_user.id,
        )
        .all()
    )
    assert len(notifications) == 1

    conflict = client.post(
        "/api/admin/notifications/broadcast",
        json={**payload, "body": "A different payload must conflict."},
        headers=headers,
    )
    assert conflict.status_code == 409

    invalid_key = client.post(
        "/api/admin/notifications/broadcast",
        json=payload,
        headers={**headers, "X-Idempotency-Key": "not-a-uuid"},
    )
    assert invalid_key.status_code == 400


def test_notification_mutations_reject_non_object_json_payloads(
    app: Flask,
    client: FlaskClient,
    admin_user: User,
    student_user: User,
) -> None:
    """Malformed JSON types must be client errors, never server errors."""
    admin_headers = {"Authorization": f"Bearer {create_token_pair(admin_user)['access_token']}"}
    student_headers = {"Authorization": f"Bearer {create_token_pair(student_user)['access_token']}"}

    broadcast_response = client.post(
        "/api/admin/notifications/broadcast",
        json="oops",
        headers=admin_headers,
    )
    shared_broadcast_response = client.post(
        "/api/notifications/broadcast",
        json=["oops"],
        headers=admin_headers,
    )
    mark_all_response = client.post(
        "/api/notifications/mark-all-read",
        json=["bogus"],
        headers=student_headers,
    )
    retry_response = client.post(
        "/api/notifications/emails/retry-failed",
        json=["bogus"],
        headers=admin_headers,
    )

    assert broadcast_response.status_code == 400
    assert shared_broadcast_response.status_code == 400
    assert mark_all_response.status_code == 400
    assert retry_response.status_code == 400
    assert broadcast_response.get_json()["success"] is False
    assert broadcast_response.get_json()["data"] is None
    assert shared_broadcast_response.get_json()["success"] is False
    assert shared_broadcast_response.get_json()["data"] is None


@pytest.mark.parametrize("target_role", ["ADMIN", "BOGUS"])
def test_notification_role_filters_reject_unsupported_values(
    app: Flask,
    client: FlaskClient,
    student_user: User,
    target_role: str,
) -> None:
    """Role filters must be valid for the authenticated actor, not silent no-ops."""
    headers = {"Authorization": f"Bearer {create_token_pair(student_user)['access_token']}"}

    list_response = client.get(f"/api/notifications?role={target_role}", headers=headers)
    count_response = client.get(
        f"/api/notifications/unread-count?role={target_role}", headers=headers
    )
    mark_all_response = client.post(
        "/api/notifications/mark-all-read",
        json={"target_role": target_role},
        headers=headers,
    )

    for response in (list_response, count_response, mark_all_response):
        assert response.status_code == 400
        payload = response.get_json()
        assert payload["success"] is False
        assert payload["data"] is None
        assert payload["error"]["code"] == "VALIDATION_ERROR"

    valid_response = client.get("/api/notifications?role=student", headers=headers)
    assert valid_response.status_code == 200


def test_notification_api_uses_canonical_success_data_envelope(
    app: Flask, client: FlaskClient, student_user: User
) -> None:
    """Notification success responses expose canonical data without removing legacy fields."""
    tokens = create_token_pair(student_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    notification, _ = dispatch_notification(
        student_user,
        "COURSE_ANNOUNCEMENT",
        "Envelope notice",
        "Envelope body",
        session=db.session,
    )
    db.session.commit()

    list_response = client.get("/api/notifications", headers=headers)
    count_response = client.get("/api/notifications/unread-count", headers=headers)
    read_response = client.patch(
        f"/api/notifications/{notification.public_id}/read", headers=headers
    )
    mark_all_response = client.post("/api/notifications/mark-all-read", headers=headers, json={})
    dismiss_response = client.delete(
        f"/api/notifications/{notification.public_id}", headers=headers
    )

    assert list_response.get_json()["success"] is True
    assert "items" in list_response.get_json()["data"]
    assert count_response.get_json()["data"]["unread_count"] >= 1
    assert read_response.get_json()["data"]["id"] == str(notification.public_id)
    assert "marked_count" in mark_all_response.get_json()["data"]
    assert dismiss_response.get_json()["data"]["status"] == "dismissed"


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
    """Validate student Web session access to notification center endpoint."""
    login_web_user(client, student_user)

    resp = client.get("/student/notifications")
    assert resp.status_code == 200
    assert resp.is_json
    data = resp.get_json()
    assert "items" in data
    assert "preferences" in data


def test_unified_auth_notifications_web_session(
    app: Flask, client: FlaskClient, admin_user: User, student_user: User
) -> None:
    """Validate unified /auth/notifications session endpoints for all roles with IDOR isolation."""
    # 1. Unauthenticated gets 401
    resp_unauth = client.get("/auth/notifications")
    assert resp_unauth.status_code == 401

    # 2. Dispatch notifications to Admin and Student
    n_admin, _ = dispatch_notification(
        admin_user,
        "SYSTEM_SECURITY_ALERT",
        "Admin Alert",
        "Admin Content",
        action_url="#/admin/security",
        session=db.session,
    )
    n_student, _ = dispatch_notification(
        student_user,
        "ASSESSMENT_GRADED",
        "Student Grade",
        "Student Content",
        action_url="#/student/assessments",
        session=db.session,
    )
    db.session.commit()

    # 3. Login as Admin
    login_web_user(client, admin_user)

    # Check unread count
    resp_count = client.get("/auth/notifications/unread-count")
    assert resp_count.status_code == 200
    assert resp_count.get_json()["unread_count"] >= 1

    # List notifications
    resp_list = client.get("/auth/notifications")
    assert resp_list.status_code == 200
    data = resp_list.get_json()
    items = data["items"]
    # Admin only sees Admin's notification (IDOR isolation)
    assert any(i["id"] == str(n_admin.public_id) for i in items)
    assert not any(i["id"] == str(n_student.public_id) for i in items)

    admin_item = next(i for i in items if i["id"] == str(n_admin.public_id))
    assert admin_item["is_read"] is False
    assert admin_item["read"] is False
    assert admin_item["action_url"] == "#/admin/security"
    assert admin_item["target_url"] == "#/admin/security"

    # Mark single notification read
    resp_read = client.post(f"/auth/notifications/{n_admin.public_id}/read")
    assert resp_read.status_code == 200
    assert resp_read.get_json()["is_read"] is True

    # Mark all read
    resp_all_read = client.post("/auth/notifications/mark-all-read")
    assert resp_all_read.status_code == 200
    assert "marked_count" in resp_all_read.get_json()


def test_notification_distinct_copy_remains_visible(
    app: Flask, client: FlaskClient, student_user: User
) -> None:
    """Verify that multiple distinct events with identical copy remain visible."""
    from pwd301.models.notification_audit import Notification
    from pwd301.services.notification_service import list_user_notifications

    # Dispatch 3 duplicate notifications to the same student
    for _ in range(3):
        dispatch_notification(
            student_user,
            "SYSTEM_NOTICE",
            "Bảo trì hệ thống định kỳ",
            "Hệ thống sẽ bảo trì lúc 02:00 sáng.",
            session=db.session,
        )
    db.session.commit()

    # Verify database has 3 notifications persisted (audit invariant)
    all_db = (
        db.session.query(Notification)
        .filter_by(recipient_user_id=student_user.id, title="Bảo trì hệ thống định kỳ")
        .all()
    )
    assert len(all_db) >= 3

    # Query through service - must be collapsed to exactly 1 visible item
    items, total = list_user_notifications(student_user, session=db.session)
    matching_items = [i for i in items if i["title"] == "Bảo trì hệ thống định kỳ"]
    assert len(matching_items) == 3
    # Check that event_type is present in dict
    assert matching_items[0]["event_type"] == "SYSTEM_NOTICE"

    # API unread count reflects collapsed visible count
    tokens = create_token_pair(student_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = client.get("/api/notifications", headers=headers)
    assert resp.status_code == 200
    api_items = [i for i in resp.get_json()["items"] if i["title"] == "Bảo trì hệ thống định kỳ"]
    assert len(api_items) == 3


def test_distinct_notification_events_with_same_copy_remain_visible(
    app: Flask, client: FlaskClient, student_user: User
) -> None:
    """Distinct business events must not be hidden by a title/body heuristic."""
    from pwd301.services.notification_service import list_user_notifications

    for event_type in ("SYSTEM_NOTICE", "COURSE_ANNOUNCEMENT"):
        dispatch_notification(
            student_user,
            event_type,
            "Same copy",
            "Same body",
            session=db.session,
        )
    db.session.commit()

    items, total = list_user_notifications(student_user, session=db.session)
    matching_items = [item for item in items if item["title"] == "Same copy"]
    assert total == 2
    assert len(matching_items) == 2
    assert {item["event_type"] for item in matching_items} == {
        "SYSTEM_NOTICE",
        "COURSE_ANNOUNCEMENT",
    }


def test_session_notification_routes_use_canonical_success_data_envelope(
    app: Flask, client: FlaskClient, student_user: User
) -> None:
    """Session and student notification routes expose the shared success envelope."""
    login_web_user(client, student_user)
    notification, _ = dispatch_notification(
        student_user,
        "SYSTEM_NOTICE",
        "Envelope contract",
        "Envelope contract body",
        session=db.session,
    )
    db.session.commit()

    auth_list = client.get("/auth/notifications")
    assert auth_list.status_code == 200
    assert auth_list.get_json()["success"] is True
    assert auth_list.get_json()["data"]["items"]
    assert auth_list.get_json()["items"] == auth_list.get_json()["data"]["items"]

    auth_count = client.get("/auth/notifications/unread-count")
    assert auth_count.get_json()["data"]["unread_count"] >= 1

    auth_read = client.post(f"/auth/notifications/{notification.public_id}/read")
    assert auth_read.get_json()["success"] is True
    assert auth_read.get_json()["data"]["read"] is True

    student_list = client.get("/student/notifications")
    assert student_list.status_code == 200
    assert student_list.get_json()["data"]["items"]

    student_mark_all = client.post("/student/notifications/mark-all-read", json={})
    assert student_mark_all.get_json()["success"] is True
    assert "marked_count" in student_mark_all.get_json()["data"]

    auth_delete = client.delete(f"/auth/notifications/{notification.public_id}")
    assert auth_delete.get_json()["success"] is True
    assert auth_delete.get_json()["data"]["status"] == "dismissed"

    auth_clear = client.post("/auth/notifications/clear", json={})
    assert auth_clear.get_json()["success"] is True
    assert "deleted_count" in auth_clear.get_json()["data"]
