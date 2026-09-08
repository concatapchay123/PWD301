"""Unit tests for REST API JWT authentication service (JwtTokenGrant lifecycle)."""

from __future__ import annotations

import uuid

import jwt
import pytest
from flask import Flask

from pwd301.extensions import db
from pwd301.models.identity import JwtTokenGrant, User
from pwd301.models.types import utc_now
from pwd301.services.exceptions import (
    AccountNotActiveError,
    AuthVersionMismatchError,
    JwtTokenInvalidError,
    JwtTokenRevokedError,
)
from pwd301.services.jwt_auth_service import (
    ACCESS_TOKEN_LIFETIME,
    JWT_ALGORITHM,
    JWT_ISSUER,
    create_token_pair,
    refresh_tokens,
    revoke_all_user_tokens,
    revoke_token,
    verify_access_token,
)
from pwd301.services.user_service import register_user


@pytest.fixture
def jwt_user(app: Flask) -> User:
    """Create a test user for JWT tests."""
    return register_user(
        email="jwt_user@example.com",
        password="SecurePassword123!",
        display_name="JWT User",
    )


class TestJwtAuthService:
    """Unit test suite for jwt_auth_service."""

    def test_create_token_pair_success(self, app: Flask, jwt_user: User) -> None:
        """Test issuing access and refresh token pair and persisting grants."""
        token_data = create_token_pair(jwt_user)

        assert "access_token" in token_data
        assert "refresh_token" in token_data
        assert token_data["token_type"] == "Bearer"
        assert token_data["expires_in"] == int(ACCESS_TOKEN_LIFETIME.total_seconds())

        secret = app.config["JWT_SECRET_KEY"]

        # Decode and verify access token claims
        access_claims = jwt.decode(
            token_data["access_token"],
            secret,
            algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER,
        )
        assert access_claims["sub"] == str(jwt_user.public_id)
        assert access_claims["user_id"] == jwt_user.id
        assert access_claims["auth_version"] == jwt_user.auth_version
        assert access_claims["token_type"] == "ACCESS"

        # Decode and verify refresh token claims
        refresh_claims = jwt.decode(
            token_data["refresh_token"],
            secret,
            algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER,
        )
        assert refresh_claims["sub"] == str(jwt_user.public_id)
        assert refresh_claims["token_type"] == "REFRESH"
        assert access_claims["session_family_id"] == refresh_claims["session_family_id"]

        # Verify DB records
        access_jti = uuid.UUID(access_claims["jti"])
        refresh_jti = uuid.UUID(refresh_claims["jti"])

        access_grant = (
            db.session.query(JwtTokenGrant).filter(JwtTokenGrant.jti == access_jti).first()
        )
        refresh_grant = (
            db.session.query(JwtTokenGrant).filter(JwtTokenGrant.jti == refresh_jti).first()
        )

        assert access_grant is not None
        assert access_grant.token_type == "ACCESS"
        assert access_grant.revoked_at is None

        assert refresh_grant is not None
        assert refresh_grant.token_type == "REFRESH"
        assert refresh_grant.revoked_at is None

    def test_create_token_pair_inactive_user_fails(self, jwt_user: User) -> None:
        """Test that inactive or suspended user cannot obtain tokens."""
        jwt_user.status = "SUSPENDED"
        jwt_user.suspended_at = utc_now()
        db.session.commit()

        with pytest.raises(AccountNotActiveError):
            create_token_pair(jwt_user)

    def test_verify_access_token_success(self, jwt_user: User) -> None:
        """Test successful verification of a valid access token."""
        token_data = create_token_pair(jwt_user)
        user, claims = verify_access_token(token_data["access_token"])

        assert user.id == jwt_user.id
        assert claims["user_id"] == jwt_user.id
        assert claims["token_type"] == "ACCESS"

    def test_verify_access_token_invalid_signature(self, app: Flask, jwt_user: User) -> None:
        """Test that token signed with wrong secret key is rejected."""
        fake_token = jwt.encode(
            {"iss": JWT_ISSUER, "sub": str(jwt_user.public_id), "token_type": "ACCESS"},
            "wrong-secret-key-that-is-at-least-32-bytes-long!",
            algorithm=JWT_ALGORITHM,
        )
        with pytest.raises(JwtTokenInvalidError):
            verify_access_token(fake_token)

    def test_verify_access_token_wrong_type(self, jwt_user: User) -> None:
        """Test that refresh token passed as access token is rejected."""
        token_data = create_token_pair(jwt_user)
        with pytest.raises(JwtTokenInvalidError, match="Token is not an access token"):
            verify_access_token(token_data["refresh_token"])

    def test_verify_access_token_revoked(self, jwt_user: User) -> None:
        """Test that explicitly revoked access token raises JwtTokenRevokedError."""
        token_data = create_token_pair(jwt_user)
        assert revoke_token(token_data["access_token"]) is True

        with pytest.raises(JwtTokenRevokedError):
            verify_access_token(token_data["access_token"])

    def test_verify_access_token_auth_version_mismatch(self, jwt_user: User) -> None:
        """Test that user credential change (auth_version increment) invalidates token."""
        token_data = create_token_pair(jwt_user)

        # Increment user's auth_version simulating password change
        jwt_user.auth_version += 1
        db.session.commit()

        with pytest.raises(AuthVersionMismatchError):
            verify_access_token(token_data["access_token"])

    def test_verify_access_token_suspended_user(self, jwt_user: User) -> None:
        """Test that suspended user's token is rejected."""
        token_data = create_token_pair(jwt_user)

        jwt_user.status = "SUSPENDED"
        jwt_user.suspended_at = utc_now()
        db.session.commit()

        with pytest.raises(AccountNotActiveError):
            verify_access_token(token_data["access_token"])

    def test_refresh_token_rotation_success(self, jwt_user: User) -> None:
        """Test rotating a refresh token issues a new token pair and revokes old refresh."""
        token_data = create_token_pair(jwt_user)
        old_refresh = token_data["refresh_token"]

        new_token_data = refresh_tokens(old_refresh)
        assert "access_token" in new_token_data
        assert "refresh_token" in new_token_data
        assert new_token_data["access_token"] != token_data["access_token"]
        assert new_token_data["refresh_token"] != old_refresh

        # New access token works
        user, _ = verify_access_token(new_token_data["access_token"])
        assert user.id == jwt_user.id

        # Old refresh token is now revoked
        with pytest.raises(JwtTokenRevokedError):
            refresh_tokens(old_refresh)

    def test_refresh_token_replay_attack_revokes_family(self, jwt_user: User) -> None:
        """Test that replaying an already-revoked refresh token revokes the entire family."""
        token_data = create_token_pair(jwt_user)
        refresh1 = token_data["refresh_token"]

        # First rotation: refresh1 is replaced by refresh2
        tokens2 = refresh_tokens(refresh1)
        refresh2 = tokens2["refresh_token"]
        access2 = tokens2["access_token"]

        # Replay attack: malicious actor tries to use refresh1 again!
        with pytest.raises(JwtTokenRevokedError, match="Token family invalidated"):
            refresh_tokens(refresh1)

        # Entire token family must now be revoked: refresh2 and access2 should both fail
        with pytest.raises(JwtTokenRevokedError):
            refresh_tokens(refresh2)

        with pytest.raises(JwtTokenRevokedError):
            verify_access_token(access2)

    def test_revoke_all_user_tokens(self, jwt_user: User) -> None:
        """Test revoking all tokens for a user."""
        tokens1 = create_token_pair(jwt_user)
        tokens2 = create_token_pair(jwt_user)

        revoked_count = revoke_all_user_tokens(jwt_user.id)
        assert revoked_count == 4  # 2 access + 2 refresh grants

        with pytest.raises(JwtTokenRevokedError):
            verify_access_token(tokens1["access_token"])

        with pytest.raises(JwtTokenRevokedError):
            verify_access_token(tokens2["access_token"])
