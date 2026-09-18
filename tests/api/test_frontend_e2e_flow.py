"""End-to-end integration test verifying SPA login, CSRF, and screen navigation flow."""

from __future__ import annotations

from flask.testing import FlaskClient

from pwd301.extensions import db
from pwd301.seeds.baseline import seed_baseline
from pwd301.services.user_service import register_user


def test_frontend_spa_full_session_flow(client: FlaskClient) -> None:
    """Verify SPA login flow: GET / (HTML + CSRF), POST /auth/login, GET / (authenticated)."""
    seed_baseline(db.session)
    register_user(
        email="student1@pwd301.local",
        password="StudentPassw0rd!",
        display_name="Nguyen Minh Anh",
    )

    # 1. First visit root / as browser
    res_index = client.get("/", headers={"Accept": "text/html,application/xhtml+xml"})
    assert res_index.status_code == 200
    assert "text/html" in res_index.content_type

    # 2. Get CSRF token from /auth/login
    res_auth_get = client.get("/auth/login")
    assert res_auth_get.status_code == 200
    auth_data = res_auth_get.get_json()
    assert "csrf_token" in auth_data
    csrf_token = auth_data["csrf_token"]

    # 3. Login as student
    res_login = client.post(
        "/auth/login",
        json={
            "email": "student1@pwd301.local",
            "password": "StudentPassw0rd!",
            "remember": False,
        },
        headers={"X-CSRFToken": csrf_token},
    )
    assert res_login.status_code == 200
    login_data = res_login.get_json()
    assert login_data["status"] == "ok"
    assert login_data["user"]["email"] == "student1@pwd301.local"

    # 4. Verify session is recognized
    res_check = client.get("/auth/login")
    assert res_check.status_code == 200
    check_data = res_check.get_json()
    assert check_data["status"] == "authenticated"
    assert check_data["user"]["primary_role"] == "STUDENT"

    # 5. Fetch student dashboard screen HTML
    res_screen = client.get(
        "/api/ui/screen/pwd301_student_dashboard_variant_1_action_centric_master_flyout_notification_hub"
    )
    assert res_screen.status_code == 200
    assert "text/html" in res_screen.content_type

    # 6. Logout
    res_logout = client.post(
        "/auth/logout",
        headers={"X-CSRFToken": check_data["csrf_token"]},
    )
    assert res_logout.status_code == 200
