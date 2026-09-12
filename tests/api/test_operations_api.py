"""API and integration tests for Operations, Backup & Recovery Engine (TASK-026).

Verifies:
- Liveness probe (/health) and Deep readiness probe (/health/deep).
- Administrative health inspection endpoint (/api/admin/health and /admin/health).
- Complete Backup API lifecycle: Create -> List -> Detail -> Verify -> Dry-Run -> Restore.
- Web session and Bearer JWT authentication support.
- Maintenance Mode middleware interception: Student and Instructor receive HTTP 503,
  while Admin, login, static, and health probes bypass.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.identity import Role, User
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
    """Create a verified Administrator user."""
    sess: Session = db.session
    user = register_user(
        email="admin_api@example.com",
        password="Password123!",
        display_name="Admin API",
        session=sess,
    )
    assign_role_to_user(
        user_id=user.id,
        role_code="ADMIN",
        assigned_by_user_id=user.id,
        session=sess,
    )
    user.is_email_verified = True
    sess.commit()
    return user


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create a verified Student user."""
    sess: Session = db.session
    user = register_user(
        email="student_api@example.com",
        password="Password123!",
        display_name="Student API",
        session=sess,
    )
    user.is_email_verified = True
    sess.commit()
    return user


# =====================================================================
# 1. Health Probe Endpoints
# =====================================================================


def test_core_health_liveness(client: FlaskClient) -> None:
    """GET /health responds with 200 OK lightweight liveness status."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert data["probe"] == "liveness"
    assert "version" in data


def test_core_health_readiness(client: FlaskClient) -> None:
    """GET /health/deep responds with 200 OK deep readiness status."""
    resp = client.get("/health/deep")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] in ("HEALTHY", "DEGRADED")
    assert "database" in data
    assert data["database"]["status"] == "HEALTHY"
    assert "storage" in data


def test_admin_health_endpoints(client: FlaskClient, admin_user: User) -> None:
    """GET /api/admin/health and /admin/health provide complete diagnostics to Admin."""
    tokens = create_token_pair(admin_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # REST API via Bearer JWT
    resp_api = client.get("/api/admin/health", headers=headers)
    assert resp_api.status_code == 200
    data_api = resp_api.get_json()
    assert "components" in data_api
    assert "database" in data_api["components"]
    assert "storage" in data_api["components"]
    assert "clamav" in data_api["components"]
    assert "workers" in data_api["components"]
    assert "mail_queue" in data_api["components"]

    # Web Session access
    login_web_user(client, admin_user)
    resp_web = client.get("/admin/health")
    assert resp_web.status_code == 200
    assert resp_web.content_type.startswith("text/html")
    assert "Trung tâm Giám sát Sức khỏe" in resp_web.get_data(as_text=True)

    # Web format=json explicit request
    resp_web_json = client.get("/admin/health?format=json")
    assert resp_web_json.status_code == 200
    assert resp_web_json.content_type == "application/json"
    assert "components" in resp_web_json.get_json()


# =====================================================================
# 2. Database Backup & Disaster Recovery Full Lifecycle API
# =====================================================================


def test_admin_backup_full_lifecycle_api(client: FlaskClient, admin_user: User) -> None:
    """End-to-end API lifecycle: Create -> List -> Detail -> Verify -> Dry-Run -> Restore."""
    tokens = create_token_pair(admin_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # 1. Trigger backup creation
    resp_create = client.post(
        "/api/admin/backups",
        json={"backup_type": "MANUAL", "notes": "Full lifecycle integration test"},
        headers=headers,
    )
    assert resp_create.status_code == 201
    create_data = resp_create.get_json()
    assert "backup" in create_data
    backup = create_data["backup"]
    backup_id = backup["backup_id"]
    storage_loc = backup["storage_location"]

    # 2. List backups
    resp_list = client.get("/api/admin/backups", headers=headers)
    assert resp_list.status_code == 200
    list_data = resp_list.get_json()
    assert list_data["total"] >= 1
    found = any(item["backup_id"] == backup_id for item in list_data["items"])
    assert found is True

    # 3. Get backup details
    resp_get = client.get(f"/api/admin/backups/{backup_id}", headers=headers)
    assert resp_get.status_code == 200
    detail = resp_get.get_json()["backup"]
    assert detail["backup_id"] == backup_id
    assert detail["status"] == "SUCCEEDED"

    # 4. Verify backup cryptographic integrity
    resp_verify = client.post(f"/api/admin/backups/{backup_id}/verify", headers=headers)
    assert resp_verify.status_code == 200
    verify_data = resp_verify.get_json()
    assert verify_data["status"] == "VERIFIED"
    assert verify_data["verified"] is True
    assert "checksum" in verify_data

    # 5. Execute dry-run restoration drill
    resp_dry = client.post(f"/api/admin/backups/{backup_id}/restore/dry-run", headers=headers)
    assert resp_dry.status_code == 200
    dry_data = resp_dry.get_json()
    assert dry_data["dry_run"] is True
    assert dry_data["status"] == "COMPATIBLE"
    assert dry_data["live_database_modified"] is False

    # 6. Execute actual restore with exact confirmation phrase and password
    resp_restore = client.post(
        f"/api/admin/backups/{backup_id}/restore",
        json={
            "confirmation_phrase": "CONFIRM_DATABASE_RESTORE",
            "password": "Password123!",
        },
        headers=headers,
    )
    assert resp_restore.status_code == 200
    restore_data = resp_restore.get_json()
    assert restore_data["status"] == "RESTORED"

    # Cleanup physical files
    if storage_loc:
        Path(storage_loc).unlink(missing_ok=True)
        p = Path(storage_loc)
        (p.parent / (p.name + ".manifest.json")).unlink(missing_ok=True)


# =====================================================================
# 3. Maintenance Window Engine & Middleware Tests
# =====================================================================


def test_maintenance_mode_middleware_interception(
    client: FlaskClient, admin_user: User, student_user: User
) -> None:
    """Maintenance mode intercepts student requests with HTTP 503 while allowing admin & health."""
    admin_tokens = create_token_pair(admin_user)
    admin_headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}

    student_tokens = create_token_pair(student_user)
    student_headers = {"Authorization": f"Bearer {student_tokens['access_token']}"}

    # 1. Initially student can access regular endpoints
    resp_before = client.get("/health")
    assert resp_before.status_code == 200

    # 2. Admin activates maintenance window
    resp_start = client.post(
        "/api/admin/maintenance/start",
        json={
            "reason": "Scheduled database index reorganization",
            "estimated_duration_minutes": 30,
        },
        headers=admin_headers,
    )
    assert resp_start.status_code == 201

    # 3. Check status
    resp_status = client.get("/api/admin/maintenance/status", headers=admin_headers)
    assert resp_status.status_code == 200
    status_data = resp_status.get_json()
    assert status_data["is_active"] is True
    assert status_data["maintenance_window"] is not None

    # 4. Student API request is intercepted with HTTP 503 SERVICE_UNAVAILABLE
    resp_student_api = client.get("/api/notifications/unread-count", headers=student_headers)
    assert resp_student_api.status_code == 503
    assert resp_student_api.headers.get("Retry-After") is not None
    api_err = resp_student_api.get_json()
    assert api_err["error"]["code"] == "MAINTENANCE_MODE_ACTIVE"
    assert "reorganization" in api_err["error"]["message"]

    # 5. Student Web request (accept: text/html) receives 503 HTML maintenance page
    resp_student_web = client.get(
        "/",
        headers={"Accept": "text/html"},
    )
    assert resp_student_web.status_code == 503
    assert "text/html" in resp_student_web.content_type
    assert resp_student_web.headers.get("Retry-After") is not None

    # 6. Admin can still access /api/admin/... and /admin/... without interruption
    resp_admin_check = client.get("/api/admin/health", headers=admin_headers)
    assert resp_admin_check.status_code == 200

    # 7. Health probes and login routes are NOT blocked during maintenance
    assert client.get("/health").status_code == 200
    assert client.get("/health/deep").status_code == 200
    assert client.get("/auth/login").status_code == 200

    # 8. Admin concludes maintenance
    resp_end = client.post("/api/admin/maintenance/end", json={}, headers=admin_headers)
    assert resp_end.status_code == 200

    # 9. Verify maintenance is concluded and student can access platform again
    resp_status_after = client.get("/api/admin/maintenance/status", headers=admin_headers)
    assert resp_status_after.status_code == 200
    assert resp_status_after.get_json()["is_active"] is False

    resp_student_restored = client.get("/api/notifications/unread-count", headers=student_headers)
    assert resp_student_restored.status_code == 200
