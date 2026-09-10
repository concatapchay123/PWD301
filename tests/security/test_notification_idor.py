"""Security and IDOR negative tests for Notification & Email Engine (TASK-021).

Tests:
- IDOR prevention: Student A cannot mark read or dismiss Student B's notifications
  (403 Forbidden / 404).
- User isolation: Actor always views and updates their own notification preferences.
- Unauthenticated rejection: Anonymous requests receive 401 Unauthorized.
- XSS injection prevention: Malicious script tags in title/body are HTML-sanitized.
- Zero PK Leakage (ADR-002): No internal BIGINT keys (id, user_id, event_id) in JSON responses.
- Security alert invariant: Opt-out for SECURITY category rejected with 400.
- Privileged endpoints: Non-admins receive 403 on broadcast and retry endpoints.
"""

from __future__ import annotations

import uuid

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.identity import Role, User
from pwd301.services.authorization_service import ForbiddenError
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.notification_service import (
    dismiss_notification,
    dispatch_notification,
    mark_notification_as_read,
)
from pwd301.services.user_service import assign_role_to_user, register_user


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
def student_a(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Student A."""
    u = register_user(
        f"idor_student_a_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Student A"
    )
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def student_b(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Student B."""
    u = register_user(
        f"idor_student_b_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Student B"
    )
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Admin."""
    u = register_user(
        f"idor_admin_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Admin User"
    )
    return assign_role_to_user(u.id, "ADMIN")


def test_idor_student_cannot_modify_other_student_notification(
    app: Flask, student_a: User, student_b: User
) -> None:
    """Student A cannot mark read or dismiss Student B's notification via service."""
    # Create notification for Student B
    notif_b, _ = dispatch_notification(
        recipient_user=student_b,
        event_type="COURSE_ANNOUNCEMENT",
        title="Student B Notice",
        body="Private notification for B",
        session=db.session,
    )
    db.session.commit()

    # Student A attempts to mark read B's notification -> ForbiddenError
    with pytest.raises(ForbiddenError):
        mark_notification_as_read(
            actor=student_a, notification_id=notif_b.public_id, session=db.session
        )

    # Student A attempts to dismiss B's notification -> ForbiddenError
    with pytest.raises(ForbiddenError):
        dismiss_notification(actor=student_a, notification_id=notif_b.public_id, session=db.session)


def test_idor_student_cannot_modify_other_student_notification_via_api(
    app: Flask, client: FlaskClient, student_a: User, student_b: User
) -> None:
    """Student A cannot mark read or dismiss Student B's notification via REST API."""
    notif_b, _ = dispatch_notification(
        recipient_user=student_b,
        event_type="COURSE_ANNOUNCEMENT",
        title="Student B Notice",
        body="Private notification for B",
        session=db.session,
    )
    db.session.commit()

    tokens_a = create_token_pair(student_a)
    headers_a = {"Authorization": f"Bearer {tokens_a['access_token']}"}

    # PATCH /api/notifications/<id>/read
    resp_patch = client.patch(f"/api/notifications/{notif_b.public_id}/read", headers=headers_a)
    assert resp_patch.status_code == 403

    # DELETE /api/notifications/<id>
    resp_del = client.delete(f"/api/notifications/{notif_b.public_id}", headers=headers_a)
    assert resp_del.status_code == 403


def test_anonymous_cannot_access_notification_endpoints(app: Flask, client: FlaskClient) -> None:
    """Anonymous requests must be rejected with 401 Unauthorized."""
    endpoints = [
        ("GET", "/api/notifications"),
        ("GET", "/api/notifications/unread-count"),
        ("GET", "/api/notifications/preferences"),
        ("PUT", "/api/notifications/preferences"),
        ("POST", "/api/notifications/mark-all-read"),
    ]
    for method, path in endpoints:
        if method == "GET":
            resp = client.get(path)
        elif method == "POST":
            resp = client.post(path, json={})
        elif method == "PUT":
            resp = client.put(path, json={})
        assert resp.status_code == 401, f"Expected 401 for {method} {path}, got {resp.status_code}"


def test_xss_sanitization_in_notifications(app: Flask, student_a: User) -> None:
    """XSS payloads in notification title and body must be safely escaped."""
    xss_title = "<script>alert('xss')</script> Hello"
    xss_body = "<img src=x onerror=alert('pwned')> Important update"

    notif, _ = dispatch_notification(
        recipient_user=student_a,
        event_type="COURSE_ANNOUNCEMENT",
        title=xss_title,
        body=xss_body,
        session=db.session,
    )
    db.session.commit()

    assert "<script>" not in notif.title
    assert "&lt;script&gt;" in notif.title
    assert "<img" not in notif.body
    assert "&lt;img" in notif.body


def test_zero_pk_leakage_adr002(app: Flask, client: FlaskClient, student_a: User) -> None:
    """All notification API responses must conform to ADR-002 Zero PK Leakage."""
    notif, _ = dispatch_notification(
        recipient_user=student_a,
        event_type="COURSE_ANNOUNCEMENT",
        title="ADR-002 Test",
        body="Checking for leaked IDs",
        session=db.session,
    )
    db.session.commit()

    tokens = create_token_pair(student_a)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # 1. GET /api/notifications
    resp = client.get("/api/notifications", headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert "items" in data
    assert len(data["items"]) >= 1
    item = data["items"][0]

    # Verify ID is UUID format
    assert uuid.UUID(item["id"])
    # Verify no BIGINT internal keys
    forbidden_keys = {"internal_id", "recipient_user_id", "notification_event_id", "user_id"}
    assert not any(fk in item for fk in forbidden_keys)

    # 2. GET /api/notifications/preferences
    pref_resp = client.get("/api/notifications/preferences", headers=headers)
    assert pref_resp.status_code == 200
    pref_data = pref_resp.get_json()
    for pref in pref_data["preferences"]:
        assert "user_id" not in pref
        assert "category" in pref
        assert "email_enabled" in pref


def test_mandatory_security_opt_out_blocked_via_api(
    app: Flask, client: FlaskClient, student_a: User
) -> None:
    """Client attempting to opt out of SECURITY notifications receives 400 VALIDATION_ERROR."""
    tokens = create_token_pair(student_a)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    payload = {
        "preferences": [
            {"category": "COURSE", "email_enabled": False},
            {"category": "SECURITY", "email_enabled": False},
        ]
    }
    resp = client.put("/api/notifications/preferences", json=payload, headers=headers)
    assert resp.status_code == 400
    err_data = resp.get_json()
    err_obj = err_data.get("error", err_data)
    assert err_obj["code"] == "VALIDATION_ERROR"
    assert "cannot be disabled" in err_obj["message"].lower()


def test_non_admin_cannot_broadcast_or_retry(
    app: Flask, client: FlaskClient, student_a: User
) -> None:
    """Student caller must receive 403 Forbidden on admin broadcast and retry endpoints."""
    tokens = create_token_pair(student_a)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # Broadcast
    resp_bc = client.post(
        "/api/notifications/broadcast",
        json={"title": "Hacked", "body": "Exploit"},
        headers=headers,
    )
    assert resp_bc.status_code == 403

    # Retry failed emails
    resp_rt = client.post("/api/notifications/emails/retry-failed", json={}, headers=headers)
    assert resp_rt.status_code == 403

    # Admin route paths
    resp_admin_bc = client.post(
        "/api/admin/notifications/broadcast",
        json={"title": "Hacked", "body": "Exploit"},
        headers=headers,
    )
    assert resp_admin_bc.status_code == 403

    resp_admin_rt = client.post("/api/admin/emails/retry-failed", json={}, headers=headers)
    assert resp_admin_rt.status_code == 403
