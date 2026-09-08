"""API tests for REST API JWT authentication endpoints."""

from __future__ import annotations

import datetime

import jwt
import pytest
from flask import Flask
from flask.testing import FlaskClient

from pwd301.extensions import db
from pwd301.models.identity import JwtTokenGrant, User
from pwd301.models.types import utc_now
from pwd301.seeds.baseline import seed_baseline
from pwd301.services.jwt_auth_service import JWT_ALGORITHM, JWT_ISSUER
from pwd301.services.user_service import change_password, register_user, suspend_user


@pytest.fixture
def api_user(app: Flask) -> User:
    """Create a user for API testing with baseline roles."""
    seed_baseline(db.session)
    return register_user(
        email="api_student@demo.local",
        password="ApiPassword123!",
        display_name="API Student",
    )


class TestJwtAuthApi:
    """Test suite covering REST API JWT endpoints."""

    def test_token_endpoint_success(self, client: FlaskClient, api_user: User) -> None:
        """POST /api/v1/auth/token returns access and refresh tokens and records grants."""
        resp = client.post(
            "/api/v1/auth/token",
            json={
                "email": "api_student@demo.local",
                "password": "ApiPassword123!",
            },
        )
        assert resp.status_code == 200
        data = resp.get_json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "Bearer"
        assert data["expires_in"] == 900

        # Check DB grants
        grants = db.session.query(JwtTokenGrant).filter(JwtTokenGrant.user_id == api_user.id).all()
        assert len(grants) == 2

    def test_token_endpoint_invalid_credentials(self, client: FlaskClient, api_user: User) -> None:
        """POST /api/v1/auth/token with bad password returns 401."""
        resp = client.post(
            "/api/v1/auth/token",
            json={
                "email": "api_student@demo.local",
                "password": "WrongPassword!",
            },
        )
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["error"]["code"] == "INVALID_CREDENTIALS"

    def test_token_endpoint_suspended_account(self, client: FlaskClient, api_user: User) -> None:
        """POST /api/v1/auth/token with suspended user returns 403."""
        suspend_user(api_user.id, reason="Security review")

        resp = client.post(
            "/api/v1/auth/token",
            json={
                "email": "api_student@demo.local",
                "password": "ApiPassword123!",
            },
        )
        assert resp.status_code == 403
        data = resp.get_json()
        assert data["error"]["code"] == "ACCOUNT_INACTIVE"

    def test_me_endpoint_with_valid_token(self, client: FlaskClient, api_user: User) -> None:
        """GET /api/v1/auth/me with valid Bearer token returns 200 and user data."""
        login_resp = client.post(
            "/api/v1/auth/token",
            json={
                "email": "api_student@demo.local",
                "password": "ApiPassword123!",
            },
        )
        access_token = login_resp.get_json()["access_token"]

        me_resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert me_resp.status_code == 200
        data = me_resp.get_json()
        assert data["user"]["id"] == api_user.id
        assert data["user"]["email"] == "api_student@demo.local"
        assert data["user"]["display_name"] == "API Student"
        assert "STUDENT" in data["user"]["roles"]

    def test_me_endpoint_missing_auth_header(self, client: FlaskClient) -> None:
        """GET /api/v1/auth/me without header returns 401."""
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["error"]["code"] == "UNAUTHORIZED"

    def test_me_endpoint_expired_token(
        self, app: Flask, client: FlaskClient, api_user: User
    ) -> None:
        """GET /api/v1/auth/me with expired token returns 401 TOKEN_EXPIRED."""
        # Create an expired token
        secret = app.config["JWT_SECRET_KEY"]
        token_jti = "00000000-0000-0000-0000-000000000001"
        expired_time = int((utc_now() - datetime.timedelta(minutes=5)).timestamp())

        expired_payload = {
            "iss": JWT_ISSUER,
            "sub": str(api_user.public_id),
            "user_id": api_user.id,
            "jti": token_jti,
            "token_type": "ACCESS",
            "auth_version": api_user.auth_version,
            "iat": expired_time - 900,
            "exp": expired_time,
        }
        expired_token = jwt.encode(expired_payload, secret, algorithm=JWT_ALGORITHM)

        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["error"]["code"] == "TOKEN_EXPIRED"

    def test_revoke_endpoint_and_subsequent_access(
        self, client: FlaskClient, api_user: User
    ) -> None:
        """POST /api/v1/auth/revoke revokes token, subsequent /me request returns 401."""
        login_resp = client.post(
            "/api/v1/auth/token",
            json={
                "email": "api_student@demo.local",
                "password": "ApiPassword123!",
            },
        )
        access_token = login_resp.get_json()["access_token"]

        # Token works initially
        assert (
            client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {access_token}"},
            ).status_code
            == 200
        )

        # Revoke token
        revoke_resp = client.post(
            "/api/v1/auth/revoke",
            json={"token": access_token},
        )
        assert revoke_resp.status_code == 200
        assert revoke_resp.get_json()["revoked"] is True

        # Now token returns 401
        after_resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert after_resp.status_code == 401
        assert after_resp.get_json()["error"]["code"] == "TOKEN_REVOKED"

    def test_jwt_invalidated_on_password_change(self, client: FlaskClient, api_user: User) -> None:
        """Password change increments auth_version and invalidates existing JWT."""
        login_resp = client.post(
            "/api/v1/auth/token",
            json={
                "email": "api_student@demo.local",
                "password": "ApiPassword123!",
            },
        )
        access_token = login_resp.get_json()["access_token"]

        assert (
            client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {access_token}"},
            ).status_code
            == 200
        )

        # Password change
        change_password(
            user_id=api_user.id,
            current_password="ApiPassword123!",
            new_password="BrandNewPassword999!",
        )

        # Token must now be rejected
        after_resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert after_resp.status_code == 401
        # It may report TOKEN_REVOKED (due to grant revocation) or AUTH_VERSION_MISMATCH
        assert after_resp.get_json()["error"]["code"] in (
            "AUTH_VERSION_MISMATCH",
            "TOKEN_REVOKED",
        )

    def test_refresh_token_rotation_flow(self, client: FlaskClient, api_user: User) -> None:
        """POST /api/v1/auth/refresh rotates token pair and revokes previous refresh."""
        login_resp = client.post(
            "/api/v1/auth/token",
            json={
                "email": "api_student@demo.local",
                "password": "ApiPassword123!",
            },
        )
        old_refresh = login_resp.get_json()["refresh_token"]

        refresh_resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh},
        )
        assert refresh_resp.status_code == 200
        new_tokens = refresh_resp.get_json()

        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
        assert new_tokens["refresh_token"] != old_refresh

        # New access token works
        me_resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {new_tokens['access_token']}"},
        )
        assert me_resp.status_code == 200

        # Old refresh token is revoked
        replay_resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh},
        )
        assert replay_resp.status_code == 401
        assert replay_resp.get_json()["error"]["code"] == "TOKEN_REVOKED"
