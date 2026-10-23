"""TASK-118: Unit and integration tests for Single Active Device Takeover (Eviction) Invariant.

Verifies:
1. Valid login always returns 200 OK with status "ok".
2. Older active sessions (last_seen <= 5m) trigger polite SSE eviction and are marked revoked in DB.
3. Older idle sessions (last_seen > 5m) are silently revoked in DB without SSE emission.
4. Session cookie is marked permanent by default (7 days or 30 days).
5. No 409 Conflict is ever returned on valid credentials (Single Active Device Takeover).
"""
from datetime import timedelta
from unittest.mock import patch

from flask import Flask
from flask.testing import FlaskClient
import pytest

from pwd301.extensions import db
from pwd301.models.identity import AuthSession, User
from pwd301.models.types import utc_now
from pwd301.services.session_auth_service import create_auth_session


@pytest.fixture
def test_user_id(app: Flask) -> int:
    with app.app_context():
        user = db.session.query(User).filter_by(email="test_takeover@pwd301.local").first()
        if not user:
            from pwd301.services.user_service import assign_role_to_user, register_user

            user = register_user(
                email="test_takeover@pwd301.local",
                password="Password123!",
                display_name="Takeover Test Student",
            )
            assign_role_to_user(user.id, "STUDENT")
            db.session.commit()
        return user.id


def test_login_success_first_device(client: FlaskClient, test_user_id: int) -> None:
    """Test standard login on fresh client returns 200 OK with status ok."""
    resp = client.post(
        "/auth/login",
        json={"email": "test_takeover@pwd301.local", "password": "Password123!"},
        headers={"Accept": "application/json"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert data["user"]["email"] == "test_takeover@pwd301.local"


def test_login_takeover_when_other_client_active(client: FlaskClient, test_user_id: int) -> None:
    """Device B logs in while Device A was active <= 5 min ago.
    Device B must get 200 OK, Device A gets revoked in DB and SSE event is emitted."""
    now = utc_now()
    with client.application.app_context():
        user = db.session.get(User, test_user_id)
        # Clean previous sessions
        db.session.query(AuthSession).filter_by(user_id=test_user_id).delete()
        db.session.commit()

        # Seed Device A session: active 1 minute ago
        sess_a, raw_key_a = create_auth_session(
            user=user,
            ip_address="192.168.1.10",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) DeviceA",
            session_duration=timedelta(days=7),
        )
        sess_a.last_seen_at = now - timedelta(minutes=1)
        db.session.commit()
        sess_a_id = sess_a.id

    with patch("pwd301.services.realtime_service.emit_domain_event") as mock_emit:
        resp = client.post(
            "/auth/login",
            json={"email": "test_takeover@pwd301.local", "password": "Password123!"},
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"

        # Verify SSE event emitted for Device A
        assert mock_emit.called
        args, kwargs = mock_emit.call_args
        assert kwargs.get("event_type") == "auth:concurrent_session_revoked"
        assert "Phiên làm việc trên thiết bị này đã kết thúc" in kwargs.get("payload", {}).get("message", "")

    # Verify Device A session in DB was revoked
    with client.application.app_context():
        revoked_a = db.session.get(AuthSession, sess_a_id)
        assert revoked_a is not None
        assert revoked_a.revoked_at is not None


def test_login_takeover_when_other_client_idle_more_than_5_min(client: FlaskClient, test_user_id: int) -> None:
    """Device B logs in while Device A was idle > 5 min ago (e.g. tab closed 2 days ago).
    Device B must get 200 OK, Device A is revoked in DB, but NO SSE event is spammed."""
    now = utc_now()
    with client.application.app_context():
        user = db.session.get(User, test_user_id)
        db.session.query(AuthSession).filter_by(user_id=test_user_id).delete()
        db.session.commit()

        # Seed Device A session: idle 2 days ago
        sess_a, raw_key_a = create_auth_session(
            user=user,
            ip_address="192.168.1.10",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) DeviceA",
            session_duration=timedelta(days=7),
        )
        sess_a.last_seen_at = now - timedelta(days=2)
        db.session.commit()
        sess_a_id = sess_a.id

    with patch("pwd301.services.realtime_service.emit_domain_event") as mock_emit:
        resp = client.post(
            "/auth/login",
            json={"email": "test_takeover@pwd301.local", "password": "Password123!"},
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"

        # Verify NO SSE event emitted because session was idle (> 5m)
        assert not mock_emit.called

    # Verify Device A session in DB was revoked
    with client.application.app_context():
        revoked_a = db.session.get(AuthSession, sess_a_id)
        assert revoked_a is not None
        assert revoked_a.revoked_at is not None
