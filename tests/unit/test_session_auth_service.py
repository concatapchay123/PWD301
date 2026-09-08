"""Unit tests for session authentication service (AuthSession lifecycle)."""

from __future__ import annotations

import datetime

from flask import Flask
import pytest

from pwd301.extensions import db
from pwd301.models.identity import User
from pwd301.models.types import utc_now
from pwd301.services.exceptions import (
    AccountNotActiveError,
    AuthVersionMismatchError,
    InvalidCredentialsError,
    SessionExpiredError,
    SessionRevokedError,
)
from pwd301.services.session_auth_service import (
    create_auth_session,
    hash_session_key,
    hash_user_agent,
    revoke_all_user_sessions,
    revoke_auth_session,
    validate_auth_session,
    verify_auth_session_or_raise,
)
from pwd301.services.user_service import register_user


@pytest.fixture
def test_user(app: Flask) -> User:
    """Create a persistent active test user."""
    return register_user(
        email="session_user@example.com",
        password="SecurePassword123!",
        display_name="Session User",
    )


class TestSessionAuthService:
    """Unit test cases covering session_auth_service business logic."""

    def test_hash_session_key(self) -> None:
        """Test SHA-256 session key hashing producing 32-byte digest."""
        key = "test_session_key_secret_123"
        digest1 = hash_session_key(key)
        digest2 = hash_session_key(key)

        assert isinstance(digest1, bytes)
        assert len(digest1) == 32
        assert digest1 == digest2
        assert digest1 != hash_session_key("different_key")

    def test_hash_user_agent(self) -> None:
        """Test User-Agent hashing."""
        assert hash_user_agent(None) is None
        assert hash_user_agent("") is None

        ua_hash = hash_user_agent("Mozilla/5.0 Chrome/120.0")
        assert ua_hash is not None
        assert len(ua_hash) == 32

    def test_create_auth_session_success(self, test_user: User) -> None:
        """Test creating a valid AuthSession record."""
        auth_sess, raw_key = create_auth_session(
            user=test_user,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
        )

        assert auth_sess.id is not None
        assert auth_sess.user_id == test_user.id
        assert auth_sess.auth_version == test_user.auth_version
        assert auth_sess.ip_address == "192.168.1.100"
        assert auth_sess.user_agent_hash is not None
        assert auth_sess.revoked_at is None
        assert auth_sess.expires_at > auth_sess.created_at
        assert raw_key is not None
        assert len(raw_key) > 20

    def test_create_auth_session_inactive_user_fails(self, test_user: User) -> None:
        """Test that inactive or suspended user cannot create a session."""
        test_user.status = "SUSPENDED"
        test_user.suspended_at = utc_now()
        db.session.commit()

        with pytest.raises(AccountNotActiveError):
            create_auth_session(user=test_user)

    def test_validate_auth_session_valid(self, test_user: User) -> None:
        """Test validating an active, non-expired session."""
        auth_sess, raw_key = create_auth_session(user=test_user)
        initial_seen = auth_sess.last_seen_at

        validated = validate_auth_session(raw_key, update_last_seen=True)
        assert validated is not None
        assert validated.id == auth_sess.id
        assert validated.last_seen_at >= initial_seen

    def test_validate_auth_session_nonexistent(self, app: Flask) -> None:
        """Test validating a non-existent session key returns None."""
        assert validate_auth_session("completely_bogus_key") is None
        assert validate_auth_session("") is None

    def test_validate_auth_session_revoked(self, test_user: User) -> None:
        """Test that explicitly revoked session returns None."""
        auth_sess, raw_key = create_auth_session(user=test_user)
        auth_sess.revoked_at = utc_now()
        db.session.commit()

        assert validate_auth_session(raw_key) is None

    def test_validate_auth_session_expired(self, test_user: User) -> None:
        """Test that expired session returns None."""
        auth_sess, raw_key = create_auth_session(user=test_user)
        auth_sess.created_at = utc_now() - datetime.timedelta(days=2)
        auth_sess.expires_at = utc_now() - datetime.timedelta(days=1)
        db.session.commit()

        assert validate_auth_session(raw_key) is None

    def test_validate_auth_session_auth_version_mismatch(self, test_user: User) -> None:
        """Test that user password change (auth_version increment) invalidates session."""
        _, raw_key = create_auth_session(user=test_user)

        # Increment user's auth_version simulating password change
        test_user.auth_version += 1
        db.session.commit()

        assert validate_auth_session(raw_key) is None

    def test_verify_auth_session_or_raise(self, app: Flask, test_user: User) -> None:
        """Test verify_auth_session_or_raise raises appropriate domain exceptions."""
        with pytest.raises(InvalidCredentialsError):
            verify_auth_session_or_raise("")

        with pytest.raises(InvalidCredentialsError):
            verify_auth_session_or_raise("nonexistent_session_key")

        # Test revoked
        auth_sess, raw_key = create_auth_session(user=test_user)
        auth_sess.revoked_at = utc_now()
        db.session.commit()
        with pytest.raises(SessionRevokedError):
            verify_auth_session_or_raise(raw_key)

        # Test expired (created_at < expires_at < utc_now())
        auth_sess2, raw_key2 = create_auth_session(user=test_user)
        auth_sess2.created_at = utc_now() - datetime.timedelta(days=2)
        auth_sess2.expires_at = utc_now() - datetime.timedelta(days=1)
        db.session.commit()
        with pytest.raises(SessionExpiredError):
            verify_auth_session_or_raise(raw_key2)

        # Test auth_version mismatch
        _, raw_key3 = create_auth_session(user=test_user)
        test_user.auth_version += 1
        db.session.commit()
        with pytest.raises(AuthVersionMismatchError):
            verify_auth_session_or_raise(raw_key3)

    def test_revoke_auth_session(self, test_user: User) -> None:
        """Test single session revocation."""
        auth_sess, raw_key = create_auth_session(user=test_user)

        assert revoke_auth_session(raw_key) is True
        db.session.refresh(auth_sess)
        assert auth_sess.revoked_at is not None

        # Revoking already revoked session returns False
        assert revoke_auth_session(raw_key) is False

        # Revoking nonexistent key returns False
        assert revoke_auth_session("unknown_key") is False

    def test_revoke_all_user_sessions(self, test_user: User) -> None:
        """Test revoking all active sessions for a user."""
        _, key1 = create_auth_session(user=test_user)
        _, key2 = create_auth_session(user=test_user)

        # Create session for another user to verify isolation
        other_user = register_user(
            email="other_session@example.com",
            password="SecurePassword123!",
            display_name="Other User",
        )
        _, other_key = create_auth_session(user=other_user)

        revoked_count = revoke_all_user_sessions(test_user.id)
        assert revoked_count == 2

        # Both sessions of test_user should be invalid
        assert validate_auth_session(key1) is None
        assert validate_auth_session(key2) is None

        # other_user session must remain untouched
        assert validate_auth_session(other_key) is not None
