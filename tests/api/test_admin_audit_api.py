"""REST API and integration test suite for Audit Logging & Sensitive Admin Actions (TASK-022).

Validates:
- End-to-end suspend flow: Admin suspends student -> student tokens instantly invalidated
  -> audit log verifiable via GET.
- End-to-end unsuspend flow: Admin reactivates account -> status ACTIVE -> new tokens work.
- End-to-end revoke-sessions flow: Admin triggers revoke-sessions -> old tokens fail due
  to auth_version increment.
- Audit log query endpoint with pagination and multi-field filtering.
- Audit log detail endpoint via public UUID.
- Web UI session route /admin/audit-logs renders HTML interface.
- Session CSRF enforcement on state-changing Web session admin operations.
"""

from __future__ import annotations

import uuid

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.identity import Role, User
from pwd301.services.audit_service import record_audit_event
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
    u = register_user(
        f"api_admin_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Admin API Tester"
    )
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test student user."""
    u = register_user(
        f"api_student_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Student API Tester"
    )
    return assign_role_to_user(u.id, "STUDENT")


def test_admin_suspend_user_flow(client: FlaskClient, admin_user: User, student_user: User) -> None:
    """End-to-end: Admin suspends student -> student tokens invalidated -> audit log created."""
    admin_tokens = create_token_pair(admin_user)
    student_tokens = create_token_pair(student_user)

    admin_headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    student_headers = {"Authorization": f"Bearer {student_tokens['access_token']}"}

    # 1. Student can initially access protected API
    resp_init = client.get("/api/notifications/unread-count", headers=student_headers)
    assert resp_init.status_code == 200

    # 2. Admin calls suspend endpoint
    target_id = str(student_user.public_id)
    corr_id = uuid.uuid4().hex
    admin_headers["X-Correlation-ID"] = corr_id

    resp_suspend = client.post(
        f"/api/admin/users/{target_id}/suspend",
        json={"reason": "Security violation: automated scraping detected"},
        headers=admin_headers,
    )
    assert resp_suspend.status_code == 200
    suspend_data = resp_suspend.get_json()
    assert suspend_data["user_id"] == target_id
    assert suspend_data["status"] == "SUSPENDED"
    assert suspend_data["suspended_at"] is not None

    # 3. Student's old token is instantly rejected
    resp_blocked = client.get("/api/notifications/unread-count", headers=student_headers)
    assert resp_blocked.status_code in (401, 403)

    # 4. Admin queries audit logs and finds the USER_SUSPEND event
    resp_logs = client.get(
        f"/api/admin/audit-logs?action=USER_SUSPEND&target_id={target_id}",
        headers=admin_headers,
    )
    assert resp_logs.status_code == 200
    logs_data = resp_logs.get_json()
    assert logs_data["total"] >= 1
    found_entry = logs_data["items"][0]
    assert found_entry["action"] == "USER_SUSPEND"
    assert found_entry["target_type"] == "USER"
    assert found_entry["target_id"] == target_id
    assert "automated scraping" in found_entry["reason"]
    assert found_entry["actor_id"] == str(admin_user.public_id)


def test_admin_unsuspend_user_flow(
    client: FlaskClient, admin_user: User, student_user: User
) -> None:
    """End-to-end: Admin unsuspends account -> account restored to ACTIVE -> audit log created."""
    admin_tokens = create_token_pair(admin_user)
    admin_headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    target_id = str(student_user.public_id)

    # First suspend
    client.post(
        f"/api/admin/users/{target_id}/suspend",
        json={"reason": "Suspended for review"},
        headers=admin_headers,
    )

    # Now unsuspend
    resp_unsuspend = client.post(
        f"/api/admin/users/{target_id}/unsuspend",
        json={"reason": "Review cleared by administrator"},
        headers=admin_headers,
    )
    assert resp_unsuspend.status_code == 200
    data = resp_unsuspend.get_json()
    assert data["status"] == "ACTIVE"
    assert data["user_id"] == target_id

    # Check student can issue fresh tokens and access API
    sess: Session = db.session
    reloaded_student = sess.get(User, student_user.id)
    assert reloaded_student is not None
    assert reloaded_student.is_active

    fresh_tokens = create_token_pair(reloaded_student)
    fresh_headers = {"Authorization": f"Bearer {fresh_tokens['access_token']}"}
    resp_access = client.get("/api/notifications/unread-count", headers=fresh_headers)
    assert resp_access.status_code == 200

    # Verify audit log for USER_UNSUSPEND
    resp_logs = client.get(
        f"/api/admin/audit-logs?action=USER_UNSUSPEND&target_id={target_id}",
        headers=admin_headers,
    )
    assert resp_logs.status_code == 200
    assert resp_logs.get_json()["total"] >= 1


def test_admin_force_revoke_sessions_flow(
    client: FlaskClient, admin_user: User, student_user: User
) -> None:
    """End-to-end: Force revoke sessions -> old tokens rejected -> audit log created."""
    admin_tokens = create_token_pair(admin_user)
    student_tokens = create_token_pair(student_user)

    admin_headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    student_headers = {"Authorization": f"Bearer {student_tokens['access_token']}"}

    # Verify initial access
    assert client.get("/api/notifications/unread-count", headers=student_headers).status_code == 200

    # Admin calls revoke-sessions
    target_id = str(student_user.public_id)
    resp_revoke = client.post(
        f"/api/admin/users/{target_id}/revoke-sessions",
        json={"reason": "User reported compromised credentials"},
        headers=admin_headers,
    )
    assert resp_revoke.status_code == 200
    data = resp_revoke.get_json()
    assert data["user_id"] == target_id
    assert "revoked" in data["message"].lower()

    # Old token fails
    assert client.get("/api/notifications/unread-count", headers=student_headers).status_code in (
        401,
        403,
    )

    # Verify audit log exists
    resp_logs = client.get(
        f"/api/admin/audit-logs?action=USER_REVOKE_SESSIONS&target_id={target_id}",
        headers=admin_headers,
    )
    assert resp_logs.status_code == 200
    assert resp_logs.get_json()["total"] >= 1


def test_admin_audit_log_detail_flow(
    client: FlaskClient, admin_user: User, student_user: User
) -> None:
    """Admin retrieves single audit event detail via GET /api/admin/audit-logs/<id>."""
    sess: Session = db.session
    admin_tokens = create_token_pair(admin_user)
    admin_headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}

    event = record_audit_event(
        actor=admin_user,
        action="TEST_ACTION",
        target_type="USER",
        target_id=student_user.public_id,
        reason="Testing single detail API",
        details={"key": "val"},
        session=sess,
        commit=True,
    )

    resp = client.get(f"/api/admin/audit-logs/{event.event_id}", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["id"] == str(event.event_id)
    assert data["action"] == "TEST_ACTION"
    assert data["target_type"] == "USER"
    assert data["target_id"] == str(student_user.public_id)
    assert data["after"]["key"] == "val"


def test_web_session_audit_logs_interface(client: FlaskClient, admin_user: User) -> None:
    """Web admin session can view audit logs via HTML template at /admin/audit-logs."""
    login_web_user(client, admin_user)

    resp = client.get("/admin/audit-logs")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["Content-Type"]
    html_content = resp.get_data(as_text=True)
    assert "Nhật ký Kiểm toán Hệ thống" in html_content
    assert "APPEND-ONLY AUDIT TRAIL" in html_content


def test_web_session_csrf_protection_on_admin_actions(
    app: Flask, client: FlaskClient, admin_user: User, student_user: User
) -> None:
    """Web session POST requests to /admin/users/<id>/suspend must enforce CSRF protection."""
    login_web_user(client, admin_user)
    target_id = str(student_user.public_id)

    app.config["WTF_CSRF_ENABLED"] = True
    try:
        # POST without CSRF token fails with 400 CSRF_ERROR
        resp_no_csrf = client.post(
            f"/admin/users/{target_id}/suspend",
            data={"reason": "No CSRF test"},
            headers={"Accept": "application/json"},
        )
        assert resp_no_csrf.status_code == 400
        data = resp_no_csrf.get_json()
        assert data["error"]["code"] == "CSRF_ERROR"
    finally:
        app.config["WTF_CSRF_ENABLED"] = False
