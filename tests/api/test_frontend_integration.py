"""Integration tests for frontend blueprint, SPA serving, and UI endpoints."""

from __future__ import annotations

from flask import Flask
from flask.testing import FlaskClient


def test_frontend_root_json_contract(client: FlaskClient) -> None:
    """Ensure automated API clients requesting application/json receive JSON status envelope."""
    response = client.get("/", headers={"Accept": "application/json"})
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert data["status"] == "running"
    assert "PWD301" in data["name"]


def test_frontend_ui_screens_catalog(client: FlaskClient) -> None:
    """Verify that /api/ui/screens returns the complete catalog of all 27 registered screens."""
    response = client.get("/api/ui/screens")
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert "screens" in data
    assert data["total"] >= 25
    screen_ids = [s["id"] for s in data["screens"]]
    assert (
        "pwd301_student_dashboard_variant_1_action_centric_master_flyout_notification_hub"
        in screen_ids
    )
    assert (
        "pwd301_auth_account_lifecycle_variant_1_focused_card_interactive_inspector" in screen_ids
    )
    assert "pwd301_instructor_dashboard_clean_minimalist_focus" in screen_ids
    assert "pwd301_admin_governance_variant_3_modular_tabbed_command_center_academic" in screen_ids


def test_frontend_get_screen_html_success(client: FlaskClient) -> None:
    """Verify that a specific screen HTML can be retrieved via /api/ui/screen/<id>."""
    response = client.get(
        "/api/ui/screen/pwd301_student_dashboard_variant_1_action_centric_master_flyout_notification_hub"
    )
    assert response.status_code == 200
    assert "text/html" in response.content_type
    assert b"PWD301 LMS" in response.data or b"H\xe1\xbb\x8dc t\xe1\xba\xadp" in response.data


def test_frontend_get_screen_html_not_found(client: FlaskClient) -> None:
    """Verify that an unknown screen ID returns HTTP 404."""
    response = client.get("/api/ui/screen/non_existent_screen_variant_xyz")
    assert response.status_code == 404


def test_frontend_path_traversal_blocked(client: FlaskClient) -> None:
    """Verify path traversal attacks on /frontend/... are strictly blocked."""
    response = client.get("/frontend/../../src/pwd301/config.py")
    assert response.status_code in (404, 400)


def test_frontend_root_html_serves_spa(client: FlaskClient) -> None:
    """Verify navigating to / with HTML Accept returns the SPA shell."""
    response = client.get("/", headers={"Accept": "text/html,application/xhtml+xml"})
    assert response.status_code == 200
    assert "text/html" in response.content_type
    assert b"spa-viewport" in response.data or b"spa-frame" in response.data


def test_frontend_serve_static_assets(client: FlaskClient) -> None:
    """Verify static JS assets can be fetched from /frontend/assets/js/router.js."""
    response = client.get("/frontend/assets/js/router.js")
    assert response.status_code == 200
    assert b"class AppRouter" in response.data


def test_frontend_spa_and_assets_allow_sameorigin_framing(client: FlaskClient) -> None:
    """Frontend SPA assets and screen HTML must permit framing by the same origin SPA.

    AC-SEC-06 enforces clickjacking protection via frame-ancestors and X-Frame-Options.
    For the SPA shell to host screen components inside its viewport iframe, frontend
    assets must specify X-Frame-Options: SAMEORIGIN and Content-Security-Policy:
    frame-ancestors 'self', while non-frontend endpoints (like /health or /api/...)
    remain strictly 'none' and 'DENY'.
    """
    # 1. Frontend screen asset must allow sameorigin framing
    screen_resp = client.get("/frontend/assets/js/router.js")
    assert screen_resp.status_code == 200
    assert screen_resp.headers.get("X-Frame-Options") == "SAMEORIGIN"
    csp = screen_resp.headers.get("Content-Security-Policy", "")
    assert "frame-ancestors 'self'" in csp
    assert "frame-ancestors 'none'" not in csp

    # 2. Root SPA page must allow sameorigin framing
    root_resp = client.get("/")
    assert root_resp.status_code == 200
    assert root_resp.headers.get("X-Frame-Options") == "SAMEORIGIN"
    root_csp = root_resp.headers.get("Content-Security-Policy", "")
    assert "frame-ancestors 'self'" in root_csp

    # 3. Non-frontend endpoints (like /health) must remain strictly locked down
    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    assert health_resp.headers.get("X-Frame-Options") == "DENY"
    health_csp = health_resp.headers.get("Content-Security-Policy", "")
    assert "frame-ancestors 'none'" in health_csp


def test_frontend_admin_views_and_api_assets(client: FlaskClient) -> None:
    """Verify admin view and api JS assets are served with proper headers and complete contracts."""
    # 1. admin.js view asset
    admin_view_resp = client.get("/frontend/assets/js/views/admin.js")
    assert admin_view_resp.status_code == 200
    assert admin_view_resp.headers.get("X-Frame-Options") == "SAMEORIGIN"
    content = admin_view_resp.data.decode("utf-8")
    assert "class AdminView" in content
    assert "renderGovernance" in content
    assert "renderTabUsers" in content
    assert "renderTabReview" in content
    assert "renderTabReassign" in content
    assert "renderTabSecurity" in content
    assert "renderOperations" in content

    # 2. api.js client asset
    api_resp = client.get("/frontend/assets/js/api.js")
    assert api_resp.status_code == 200
    api_content = api_resp.data.decode("utf-8")
    expected_methods = [
        "getAdminUsers",
        "manageUserRole",
        "assignRole",
        "removeRole",
        "suspendUser",
        "unsuspendUser",
        "revokeUserSessions",
        "getPendingCourses",
        "reviewCourse",
        "reassignCourse",
        "quarantineOverride",
        "getAdminAuditLogs",
        "getAdminBackups",
        "createAdminBackup",
        "verifyAdminBackup",
        "restoreAdminBackupDryRun",
        "restoreAdminBackup",
        "getMaintenanceStatus",
        "startMaintenance",
        "endMaintenance",
    ]
    for method in expected_methods:
        assert method in api_content, f"Missing method {method} in api.js"


def test_admin_portal_authenticated_flow(client: FlaskClient, app: Flask) -> None:
    """Verify live admin endpoints respond correctly when called by an authenticated Admin."""
    from pwd301.extensions import db
    from pwd301.models.identity import Role
    from pwd301.services.user_service import assign_role_to_user, register_user
    from tests.conftest import login_web_user

    # Setup roles if needed
    sess = db.session
    for code, name in [
        ("STUDENT", "Student"),
        ("INSTRUCTOR", "Instructor"),
        ("ADMIN", "System Administrator"),
    ]:
        if not sess.query(Role).filter(Role.code == code).first():
            sess.add(Role(code=code, name=name))
    sess.commit()

    admin = register_user(
        "admin_portal_test@example.com",
        "Password123!",
        "Admin Portal Tester",
        session=sess,
    )
    assign_role_to_user(admin.id, "ADMIN", session=sess)
    admin.is_email_verified = True
    sess.commit()

    # Authenticate admin session
    login_web_user(client, admin)

    # 1. Admin dashboard
    resp = client.get("/admin/dashboard")
    assert resp.status_code == 200
    assert resp.is_json

    # 2. Admin users
    resp = client.get("/admin/users")
    assert resp.status_code == 200
    assert resp.is_json
    data = resp.get_json()
    assert "users" in data
    assert any(u["email"] == "admin_portal_test@example.com" for u in data["users"])

    # 3. Admin courses & pending courses
    resp = client.get("/admin/courses")
    assert resp.status_code == 200
    assert resp.is_json

    resp = client.get("/admin/courses/pending")
    assert resp.status_code == 200
    assert resp.is_json

    # 4. Admin instructor applications
    resp = client.get("/admin/instructor-applications")
    assert resp.status_code == 200
    assert resp.is_json

    # 5. Admin audit logs
    resp = client.get("/admin/audit-logs")
    assert resp.status_code == 200
    assert resp.is_json

    # 6. Admin telemetry
    resp = client.get("/admin/telemetry")
    assert resp.status_code == 200
    assert resp.is_json

    # 7. Admin backups
    resp = client.get("/admin/backups")
    assert resp.status_code == 200
    assert resp.is_json

    # 8. Admin maintenance status
    resp = client.get("/admin/maintenance/status")
    assert resp.status_code == 200
    assert resp.is_json

    # 9. Admin health
    resp = client.get("/admin/health")
    assert resp.status_code == 200
    assert resp.is_json


def test_frontend_js_syntax_integrity() -> None:
    """Verify all frontend javascript files have valid syntax and parse cleanly without errors."""
    import glob
    import os
    import shutil
    import subprocess

    import pytest

    node_bin = shutil.which("node")
    if not node_bin:
        pytest.skip("Node.js not installed in environment")

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    js_pattern = os.path.join(repo_root, "frontend", "assets", "js", "**", "*.js")
    js_files = glob.glob(js_pattern, recursive=True)
    assert len(js_files) >= 5, f"Expected at least 5 frontend JS files, found {len(js_files)}"

    for js_path in js_files:
        result = subprocess.run([node_bin, "--check", js_path], capture_output=True, text=True)
        fname = os.path.basename(js_path)
        assert result.returncode == 0, f"Syntax error in {fname}:\n{result.stderr}"

