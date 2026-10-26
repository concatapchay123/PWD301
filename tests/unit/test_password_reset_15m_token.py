"""Unit and Integration Tests for 15-Minute Timed Password Reset & Identity Binding."""

from __future__ import annotations

import datetime
import pytest
from flask import Flask

from backend import create_app
from backend.extensions import db
from backend.models.identity import User, UserSecurityToken
from backend.models.types import utc_now
from backend.services.auth_token_service import (
    DEFAULT_EXPIRATION_SECONDS,
    SecurityTokenPurpose,
    TokenAlreadyConsumedError,
    TokenExpiredError,
    create_security_token,
    reset_password_with_token,
    verify_security_token,
)
from backend.services.email_service import send_password_reset_email
from backend.services.user_service import PPTQ_HASH_PREFIX, register_user, verify_password


@pytest.fixture(scope="module")
def app():
    app = create_app("development")
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.app_context():
        yield app


@pytest.fixture(autouse=True)
def clean_db_session(app):
    with app.app_context():
        db.session.rollback()
        yield
        db.session.rollback()


@pytest.fixture
def test_user(app):
    user = db.session.query(User).filter(User.email == "test_reset_15m@pptq.local").first()
    if not user:
        user = register_user(
            email="test_reset_15m@pptq.local",
            password="OldPassword123!",
            display_name="Sinh Viên Reset 15M",
        )
    return user


def test_password_reset_default_expiration_is_15_minutes():
    """Verify that password reset token expiration is strictly set to 15 minutes (900 seconds)."""
    assert DEFAULT_EXPIRATION_SECONDS[SecurityTokenPurpose.PASSWORD_RESET] == 900


def test_password_reset_email_reflects_15_minutes(monkeypatch, test_user):
    """Verify that the password reset email explicitly informs the user of 15 minutes expiration."""
    sent_emails = []

    def mock_send_single_email(**kwargs):
        sent_emails.append(kwargs)
        return True

    from backend.services import email_service
    monkeypatch.setattr(email_service, "send_single_email", mock_send_single_email)

    send_password_reset_email(test_user, "dummy_token_123")
    assert len(sent_emails) == 1
    email = sent_emails[0]
    assert "15 phút" in email["body_html"]
    assert "1 giờ" not in email["body_html"]


def test_password_reset_verification_endpoint_success(app, test_user):
    """Verify GET /auth/reset-password/<token> returns 200 with user identity details."""
    _, raw_token = create_security_token(test_user.id, SecurityTokenPurpose.PASSWORD_RESET)
    db.session.commit()

    with app.test_client() as client:
        res = client.get(f"/auth/reset-password/{raw_token}")
        assert res.status_code == 200
        data = res.get_json()
        assert data["valid"] is True
        assert data["email"] == test_user.email
        assert data["display_name"] == test_user.display_name
        assert data["user_id"] == test_user.id


def test_password_reset_expired_token_rejected(app, test_user):
    """Verify that tokens older than 15 minutes are rejected with TOKEN_EXPIRED."""
    record, raw_token = create_security_token(test_user.id, SecurityTokenPurpose.PASSWORD_RESET)
    # Move both created_at and expires_at back to respect ck_user_security_tokens_2 (expires_at > created_at)
    record.created_at = utc_now() - datetime.timedelta(minutes=30)
    record.expires_at = utc_now() - datetime.timedelta(minutes=15)
    db.session.commit()

    with app.test_client() as client:
        res = client.get(f"/auth/reset-password/{raw_token}")
        assert res.status_code == 400
        data = res.get_json()
        assert data["error"]["code"] == "TOKEN_EXPIRED"
        assert "15 phút" in data["error"]["message"]


def test_password_reset_execution_consumes_token_and_hashes_pptq_argon2(app, test_user):
    """Verify POST /auth/reset-password/<token> resets password, enforces PPTQ Argon2id, and consumes token."""
    _, raw_token = create_security_token(test_user.id, SecurityTokenPurpose.PASSWORD_RESET)
    db.session.commit()

    with app.test_client() as client:
        res = client.post(
            f"/auth/reset-password/{raw_token}",
            json={
                "password": "NewStrongPassword456!",
                "confirm_password": "NewStrongPassword456!",
            },
        )
        assert res.status_code == 200
        data = res.get_json()
        assert data["status"] == "ok"

    # Verify user record updated in database
    db.session.expire_all()
    user = db.session.get(User, test_user.id)
    assert user.password_hash.startswith(PPTQ_HASH_PREFIX)
    assert verify_password(user, "NewStrongPassword456!") is True

    # Verify token is now consumed and cannot be reused
    with app.test_client() as client:
        # Re-check via GET
        get_res = client.get(f"/auth/reset-password/{raw_token}")
        assert get_res.status_code == 400
        assert get_res.get_json()["error"]["code"] == "TOKEN_ALREADY_USED"

        # Re-check via POST
        post_res = client.post(
            f"/auth/reset-password/{raw_token}",
            json={
                "password": "AnotherPassword789!",
                "confirm_password": "AnotherPassword789!",
            },
        )
        assert post_res.status_code == 400
        assert post_res.get_json()["error"]["code"] == "TOKEN_ALREADY_USED"
