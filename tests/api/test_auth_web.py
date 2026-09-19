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
        """GET /auth/login returns 200 with JSON endpoint info in headless mode."""
        resp = client.get("/auth/login")
        assert resp.status_code == 200
        assert resp.is_json
        data = resp.get_json()
        assert data["status"] == "ok"

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
        assert resp.status_code == 200
        assert resp.is_json
        data = resp.get_json()
        assert data["status"] == "ok"

        # Verify AuthSession record in DB
        auth_sess = db.session.query(AuthSession).filter(AuthSession.user_id == web_user.id).first()
        assert auth_sess is not None
        assert auth_sess.auth_version == web_user.auth_version
        assert auth_sess.revoked_at is None

        # Verify authenticated access using the session cookie via protected student route
        dash_resp = client.get("/student/dashboard")
        assert dash_resp.status_code == 200
        assert dash_resp.is_json

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
        dash_resp = client.get("/student/dashboard")
        assert dash_resp.status_code == 401

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
        resp1 = client.get("/student/dashboard")
        assert resp1.status_code == 200

        # User changes password
        change_password(
            user_id=web_user.id,
            current_password="Password123!",
            new_password="NewSecurePassword456!",
        )

        # Next request using the same session cookie must be rejected
        resp2 = client.get("/student/dashboard")
        assert resp2.status_code == 401

    def test_session_invalidated_on_user_suspend(self, client: FlaskClient, web_user: User) -> None:
        """Account suspension immediately invalidates active web session."""
        # Log in
        client.post(
            "/auth/login",
            json={"email": "student@demo.local", "password": "Password123!"},
        )

        # Confirm authenticated
        resp1 = client.get("/student/dashboard")
        assert resp1.status_code == 200

        # Suspend account
        suspend_user(web_user.id, reason="Account under audit")

        # Next request must be treated as unauthenticated
        resp2 = client.get("/student/dashboard")
        assert resp2.status_code == 401

    def test_register_page_and_submit(self, client: FlaskClient) -> None:
        """GET and POST /auth/register creates new User with STUDENT role."""
        seed_baseline(db.session)

        get_resp = client.get("/auth/register")
        assert get_resp.status_code == 200
        assert get_resp.is_json
        assert get_resp.get_json()["status"] == "ok"

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

    def test_session_missing_keys_fails_closed(self, client: FlaskClient, web_user: User) -> None:
        """Tampered session cookie missing auth_session_key or auth_version fails closed."""
        # Log in to get valid session
        client.post(
            "/auth/login",
            json={"email": "student@demo.local", "password": "Password123!"},
        )
        resp1 = client.get("/student/dashboard")
        assert resp1.status_code == 200

        # Tamper: remove auth_session_key from session
        with client.session_transaction() as sess:
            sess.pop("auth_session_key", None)

        resp2 = client.get("/student/dashboard")
        assert resp2.status_code == 401

        # Tamper: remove auth_version from session
        with client.session_transaction() as sess:
            sess["auth_session_key"] = "some-key"
            sess.pop("auth_version", None)

        resp3 = client.get("/student/dashboard")
        assert resp3.status_code == 401

    def test_login_open_redirect_defense(self, client: FlaskClient, web_user: User) -> None:
        """Verify login next parameter blocks open redirect attacks (e.g. /\\attacker.com)."""
        malicious_urls = [
            "/\\attacker.com",
            "/\\evil.com/phish",
            "//attacker.com",
            "//attacker.com/steal",
            "https://attacker.com",
            "http://evil.com/login",
            "javascript:alert(1)",
        ]
        for bad_url in malicious_urls:
            resp = client.post(
                f"/auth/login?next={bad_url}",
                data={
                    "email": "student@demo.local",
                    "password": "Password123!",
                },
                follow_redirects=False,
            )
            assert resp.status_code == 200
            data = resp.get_json()
            redirect_target = data.get("redirect_url", "")
            # Must NOT redirect to the attacker host or scheme
            assert not redirect_target.startswith("//")
            assert not redirect_target.startswith("/\\")
            assert "attacker.com" not in redirect_target
            assert "evil.com" not in redirect_target
            assert redirect_target in ("/", "/student/dashboard")

        # Legitimate relative next URL must be preserved
        good_resp = client.post(
            "/auth/login?next=/courses/my-course-123",
            data={
                "email": "student@demo.local",
                "password": "Password123!",
            },
            follow_redirects=False,
        )
        assert good_resp.status_code == 200
        assert good_resp.get_json().get("redirect_url") == "/courses/my-course-123"

    def test_login_preserves_and_returns_csrf_token(
        self, client: FlaskClient, web_user: User
    ) -> None:
        """Login must regenerate and return a fresh CSRF token, and populate session."""
        resp = client.post(
            "/auth/login",
            json={
                "email": "student@demo.local",
                "password": "Password123!",
            },
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "csrf_token" in data
        assert len(data["csrf_token"]) > 20
        with client.session_transaction() as sess:
            assert "csrf_token" in sess
            assert sess["csrf_token"] is not None

    def test_login_with_active_csrf_and_subsequent_post_request(
        self, app: Flask, client: FlaskClient, web_user: User
    ) -> None:
        """With WTF_CSRF_ENABLED active, login replaces CSRF session token cleanly."""
        app.config["WTF_CSRF_ENABLED"] = True
        try:
            # 1. Fetch pre-login CSRF token
            csrf_resp = client.get("/auth/login")
            assert csrf_resp.status_code == 200
            pre_token = csrf_resp.get_json()["csrf_token"]

            # 2. Log in with the CSRF token
            login_resp = client.post(
                "/auth/login",
                json={
                    "email": "student@demo.local",
                    "password": "Password123!",
                },
                headers={"X-CSRF-Token": pre_token},
            )
            assert login_resp.status_code == 200
            login_data = login_resp.get_json()
            assert login_data["status"] == "ok"
            new_token = login_data["csrf_token"]
            assert new_token != pre_token

            # Verify session has the new token stored
            with client.session_transaction() as sess:
                assert sess.get("csrf_token") is not None

            # 3. Perform subsequent authenticated POST with the new CSRF token (e.g. logout)
            post_resp = client.post(
                "/auth/logout",
                json={},
                headers={"X-CSRF-Token": new_token},
            )
            assert post_resp.status_code == 200
            assert post_resp.get_json()["status"] == "ok"
        finally:
            app.config["WTF_CSRF_ENABLED"] = False

    def test_login_text_plain_json_body_fallback(
        self, client: FlaskClient, web_user: User
    ) -> None:
        """POST /auth/login with JSON body under text/plain content-type succeeds defensively."""
        import json

        resp = client.post(
            "/auth/login",
            data=json.dumps({
                "email": "student@demo.local",
                "password": "Password123!",
            }),
            content_type="text/plain;charset=UTF-8",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"
        assert data["user"]["email"] == "student@demo.local"

    def test_get_login_sets_csrf_cookie(self, client: FlaskClient) -> None:
        """GET /auth/login sets csrf_token cookie in addition to returning it in JSON."""
        resp = client.get("/auth/login")
        assert resp.status_code == 200
        set_cookies = resp.headers.getlist("Set-Cookie")
        assert any("csrf_token=" in c for c in set_cookies)

    def test_logout_clears_csrf_cookie(self, client: FlaskClient, web_user: User) -> None:
        """POST /auth/logout deletes csrf_token cookie to prevent stale tokens."""
        # Log in first
        client.post(
            "/auth/login",
            json={"email": "student@demo.local", "password": "Password123!"},
        )
        resp = client.post("/auth/logout", json={})
        assert resp.status_code == 200
        set_cookies = resp.headers.getlist("Set-Cookie")
        assert any("csrf_token=" in c and ("Max-Age=0" in c or "Expires=" in c) for c in set_cookies)

