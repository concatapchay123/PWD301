"""API / Integration tests for Web UI session-based authentication."""

from __future__ import annotations

import pytest
from flask import Flask
from flask.testing import FlaskClient

from pwd301.extensions import db
from pwd301.models.identity import AuthSession, User
from pwd301.seeds.baseline import seed_baseline
from pwd301.services.user_service import change_password, register_user, suspend_user


@pytest.fixture
def web_user(app: Flask) -> User:
    """Create a standard test user with seeded roles."""
    seed_baseline(db.session)
    return register_user(
        email="student@demo.local",
        password="Password123!",
        display_name="Student Demo",
    )


class TestWebAuth:
    """Test suite for Web UI / Session authentication endpoints."""

    def test_login_page_renders_get(self, client: FlaskClient) -> None:
        """GET /auth/login returns 200 with HTML form."""
        resp = client.get("/auth/login")
        assert resp.status_code == 200
        assert "Đăng nhập PWD301".encode() in resp.data
        assert b"email" in resp.data
        assert b"password" in resp.data

    def test_login_form_success(self, client: FlaskClient, web_user: User) -> None:
        """POST /auth/login with form data creates AuthSession and sets session cookie."""
        resp = client.post(
            "/auth/login",
            data={
                "email": "student@demo.local",
                "password": "Password123!",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302

        # Verify AuthSession record in DB
        auth_sess = db.session.query(AuthSession).filter(AuthSession.user_id == web_user.id).first()
        assert auth_sess is not None
        assert auth_sess.auth_version == web_user.auth_version
        assert auth_sess.revoked_at is None

        # Verify authenticated access using the session cookie via HTML request
        home_resp = client.get("/", headers={"Accept": "text/html"})
        assert home_resp.status_code == 200
        # In base.html, authenticated user shows display_name in user menu
        assert web_user.display_name.encode("utf-8") in home_resp.data

    def test_login_ajax_json_success(self, client: FlaskClient, web_user: User) -> None:
        """POST /auth/login with JSON body returns 200 JSON with user data."""
        resp = client.post(
            "/auth/login",
            json={
                "email": "student@demo.local",
                "password": "Password123!",
            },
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"
        assert data["user"]["email"] == "student@demo.local"

        auth_sess = db.session.query(AuthSession).filter(AuthSession.user_id == web_user.id).first()
        assert auth_sess is not None

    def test_login_invalid_password(self, client: FlaskClient, web_user: User) -> None:
        """POST /auth/login with incorrect password returns 401."""
        resp = client.post(
            "/auth/login",
            json={
                "email": "student@demo.local",
                "password": "WrongPassword!",
            },
        )
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["error"]["code"] == "INVALID_CREDENTIALS"

    def test_login_suspended_account(self, client: FlaskClient, web_user: User) -> None:
        """POST /auth/login with suspended account returns 403."""
        suspend_user(web_user.id, reason="Violation of terms")

        resp = client.post(
            "/auth/login",
            json={
                "email": "student@demo.local",
                "password": "Password123!",
            },
        )
        assert resp.status_code == 403
        data = resp.get_json()
        assert data["error"]["code"] == "ACCOUNT_INACTIVE"

    def test_logout_revokes_session(self, client: FlaskClient, web_user: User) -> None:
        """POST /auth/logout marks AuthSession revoked and clears session."""
        # First log in
        login_resp = client.post(
            "/auth/login",
            json={"email": "student@demo.local", "password": "Password123!"},
        )
        assert login_resp.status_code == 200

        auth_sess = db.session.query(AuthSession).filter(AuthSession.user_id == web_user.id).first()
        assert auth_sess.revoked_at is None

        # Then log out
        logout_resp = client.post("/auth/logout", json={})
        assert logout_resp.status_code == 200

        db.session.refresh(auth_sess)
        assert auth_sess.revoked_at is not None

        # Subsequent request should be guest/anonymous
        home_resp = client.get("/", headers={"Accept": "text/html"})
        assert "Đăng nhập".encode() in home_resp.data

    def test_session_invalidated_on_password_change(
        self, client: FlaskClient, web_user: User
    ) -> None:
        """Password change increments auth_version and invalidates existing web session."""
        # Log in
        client.post(
            "/auth/login",
            json={"email": "student@demo.local", "password": "Password123!"},
        )

        # Confirm authenticated
        resp1 = client.get("/", headers={"Accept": "text/html"})
        assert web_user.display_name.encode("utf-8") in resp1.data

        # User changes password
        change_password(
            user_id=web_user.id,
            current_password="Password123!",
            new_password="NewSecurePassword456!",
        )

        # Next request using the same session cookie must be rejected
        resp2 = client.get("/", headers={"Accept": "text/html"})
        assert web_user.display_name.encode("utf-8") not in resp2.data

    def test_session_invalidated_on_user_suspend(self, client: FlaskClient, web_user: User) -> None:
        """Account suspension immediately invalidates active web session."""
        # Log in
        client.post(
            "/auth/login",
            json={"email": "student@demo.local", "password": "Password123!"},
        )

        # Confirm authenticated
        resp1 = client.get("/", headers={"Accept": "text/html"})
        assert web_user.display_name.encode("utf-8") in resp1.data

        # Suspend account
        suspend_user(web_user.id, reason="Account under audit")

        # Next request must be treated as unauthenticated
        resp2 = client.get("/", headers={"Accept": "text/html"})
        assert web_user.display_name.encode("utf-8") not in resp2.data

    def test_register_page_and_submit(self, client: FlaskClient) -> None:
        """GET and POST /auth/register creates new User with STUDENT role."""
        seed_baseline(db.session)

        get_resp = client.get("/auth/register")
        assert get_resp.status_code == 200
        assert "Đăng ký tài khoản".encode() in get_resp.data

        post_resp = client.post(
            "/auth/register",
            json={
                "name": "New Student",
                "email": "new_student@domain.com",
                "password": "BrandNewPassword123!",
            },
        )
        assert post_resp.status_code == 201
        data = post_resp.get_json()
        assert data["status"] == "ok"

        created = (
            db.session.query(User).filter(User.email_normalized == "new_student@domain.com").first()
        )
        assert created is not None
        assert created.display_name == "New Student"
        assert any(r.code == "STUDENT" for r in created.roles)
