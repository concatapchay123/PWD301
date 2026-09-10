"""Security and access control tests for Operations, Backup & Recovery Engine (TASK-026).

Verifies:
- Role-Based Access Control (RBAC): Students and Instructors receive HTTP 403 FORBIDDEN.
- Authentication enforcement: Anonymous callers receive HTTP 401 UNAUTHORIZED.
- Live database protection: Missing confirmation phrase or wrong password fails closed.
- Fail-closed audit logging: Mutations abort and roll back if audit log fails.
- ADR-002: Zero internal BIGINT PK leakage across all operational JSON responses.
"""

from __future__ import annotations

import unittest.mock as mock
import uuid
from pathlib import Path

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.identity import Role, User
from pwd301.models.operations import BackupRun
from pwd301.services.exceptions import AuditPersistenceError
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.operations_service import create_database_backup
from pwd301.services.user_service import assign_role_to_user, register_user


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
        email="admin_sec@example.com",
        password="Password123!",
        display_name="Admin Security",
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
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create a verified Instructor user."""
    sess: Session = db.session
    user = register_user(
        email="inst_sec@example.com",
        password="Password123!",
        display_name="Instructor Security",
        session=sess,
    )
    assign_role_to_user(
        user_id=user.id,
        role_code="INSTRUCTOR",
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
        email="student_sec@example.com",
        password="Password123!",
        display_name="Student Security",
        session=sess,
    )
    user.is_email_verified = True
    sess.commit()
    return user


# =====================================================================
# 1. RBAC & IDOR Isolation Tests
# =====================================================================


def test_student_forbidden_on_all_operations_endpoints(
    client: FlaskClient, student_user: User
) -> None:
    """Student attempting to access admin operations endpoints receives HTTP 403 FORBIDDEN."""
    tokens = create_token_pair(student_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    dummy_id = str(uuid.uuid4())

    endpoints = [
        ("GET", "/api/admin/health", None),
        ("GET", "/api/admin/backups", None),
        ("POST", "/api/admin/backups", {"backup_type": "MANUAL"}),
        ("GET", f"/api/admin/backups/{dummy_id}", None),
        ("POST", f"/api/admin/backups/{dummy_id}/verify", None),
        ("POST", f"/api/admin/backups/{dummy_id}/restore/dry-run", None),
        (
            "POST",
            f"/api/admin/backups/{dummy_id}/restore",
            {"confirmation_phrase": "CONFIRM_DATABASE_RESTORE", "password": "Password123!"},
        ),
        ("POST", "/api/admin/maintenance/start", {"reason": "Test"}),
        ("POST", "/api/admin/maintenance/end", {}),
        ("GET", "/api/admin/maintenance/status", None),
    ]

    for method, path, body in endpoints:
        if method == "GET":
            resp = client.get(path, headers=headers)
        else:
            resp = client.post(path, json=body or {}, headers=headers)

        assert resp.status_code == 403, (
            f"Expected 403 FORBIDDEN for student on {method} {path}, got {resp.status_code}"
        )
        data = resp.get_json()
        assert data.get("error", {}).get("code") == "FORBIDDEN"


def test_instructor_forbidden_on_all_operations_endpoints(
    client: FlaskClient, instructor_user: User
) -> None:
    """Instructor attempting to access admin operations endpoints receives HTTP 403 FORBIDDEN."""
    tokens = create_token_pair(instructor_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    dummy_id = str(uuid.uuid4())

    endpoints = [
        ("GET", "/api/admin/health"),
        ("GET", "/api/admin/backups"),
        ("POST", "/api/admin/backups"),
        ("GET", f"/api/admin/backups/{dummy_id}"),
        ("POST", "/api/admin/maintenance/start"),
    ]

    for method, path in endpoints:
        if method == "GET":
            resp = client.get(path, headers=headers)
        else:
            resp = client.post(path, json={}, headers=headers)
        assert resp.status_code == 403, (
            f"Expected 403 FORBIDDEN for instructor on {method} {path}, got {resp.status_code}"
        )


def test_unauthenticated_rejected_with_401(client: FlaskClient) -> None:
    """Anonymous client accessing protected operations endpoints receives HTTP 401 UNAUTHORIZED."""
    endpoints = [
        ("GET", "/api/admin/health"),
        ("GET", "/api/admin/backups"),
        ("POST", "/api/admin/backups"),
        ("POST", "/api/admin/maintenance/start"),
        ("GET", "/api/admin/maintenance/status"),
    ]

    for method, path in endpoints:
        resp = client.get(path) if method == "GET" else client.post(path, json={})
        assert resp.status_code == 401, (
            f"Expected 401 UNAUTHORIZED on {method} {path}, got {resp.status_code}"
        )


# =====================================================================
# 2. Database Anti-Overwrite & Safeguards Verification
# =====================================================================


def test_restore_database_missing_phrase_rejected(client: FlaskClient, admin_user: User) -> None:
    """Restore call without confirmation phrase is rejected with HTTP 403 FORBIDDEN."""
    tokens = create_token_pair(admin_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    backup = create_database_backup(actor=admin_user, session=db.session)
    backup_id = str(backup.public_id)

    # Omit confirmation_phrase
    resp = client.post(
        f"/api/admin/backups/{backup_id}/restore",
        json={"password": "Password123!"},
        headers=headers,
    )
    assert resp.status_code == 403
    data = resp.get_json()
    assert data.get("error", {}).get("code") == "FORBIDDEN"
    assert "confirmation phrase" in data.get("error", {}).get("message", "").lower()

    # Cleanup
    Path(backup.storage_location).unlink(missing_ok=True)
    p = Path(backup.storage_location)
    (p.parent / (p.name + ".manifest.json")).unlink(missing_ok=True)


def test_restore_database_wrong_password_rejected(client: FlaskClient, admin_user: User) -> None:
    """Restore call with incorrect admin password is rejected with HTTP 403 FORBIDDEN."""
    tokens = create_token_pair(admin_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    backup = create_database_backup(actor=admin_user, session=db.session)
    backup_id = str(backup.public_id)

    resp = client.post(
        f"/api/admin/backups/{backup_id}/restore",
        json={
            "confirmation_phrase": "CONFIRM_DATABASE_RESTORE",
            "password": "WrongPassword666!",
        },
        headers=headers,
    )
    assert resp.status_code == 403
    data = resp.get_json()
    assert data.get("error", {}).get("code") == "FORBIDDEN"

    # Cleanup
    Path(backup.storage_location).unlink(missing_ok=True)
    p = Path(backup.storage_location)
    (p.parent / (p.name + ".manifest.json")).unlink(missing_ok=True)


# =====================================================================
# 3. Fail-Closed Audit Logging Enforcement
# =====================================================================


def test_fail_closed_on_audit_persistence_failure(app: Flask, admin_user: User) -> None:
    """If audit log persistence fails, sensitive operations abort and roll back."""
    with app.app_context():
        with (
            mock.patch(
                "pwd301.services.operations_service.record_audit_event",
                side_effect=AuditPersistenceError("Database disk full or audit trigger aborted"),
            ),
            pytest.raises(AuditPersistenceError),
        ):
            create_database_backup(actor=admin_user, session=db.session)

        # Confirm that no backup record was committed to the database
        count = db.session.query(BackupRun).count()
        assert count == 0


# =====================================================================
# 4. ADR-002 Zero Internal PK Leakage
# =====================================================================


def test_adr002_zero_internal_pk_leakage(client: FlaskClient, admin_user: User) -> None:
    """Verify that all JSON responses strictly use public UUIDs and never leak internal PKs."""
    tokens = create_token_pair(admin_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # 1. Create backup via API
    resp_create = client.post(
        "/api/admin/backups",
        json={"backup_type": "MANUAL", "notes": "ADR-002 Verification"},
        headers=headers,
    )
    assert resp_create.status_code == 201
    create_data = resp_create.get_json()
    backup_item = create_data["backup"]

    assert "backup_id" in backup_item
    # Must be valid UUID
    u = uuid.UUID(backup_item["backup_id"])
    assert str(u) == backup_item["backup_id"]
    # Internal primary key must NOT be present
    assert "id" not in backup_item

    backup_id = backup_item["backup_id"]

    # 2. Get backup details
    resp_get = client.get(f"/api/admin/backups/{backup_id}", headers=headers)
    assert resp_get.status_code == 200
    get_item = resp_get.get_json()["backup"]
    assert "id" not in get_item
    assert get_item["backup_id"] == backup_id

    # 3. Maintenance start
    resp_maint = client.post(
        "/api/admin/maintenance/start",
        json={"reason": "ADR-002 check", "estimated_duration_minutes": 30},
        headers=headers,
    )
    assert resp_maint.status_code == 201
    maint_item = resp_maint.get_json()["maintenance_window"]
    assert "window_id" in maint_item
    u_win = uuid.UUID(maint_item["window_id"])
    assert str(u_win) == maint_item["window_id"]
    assert "id" not in maint_item

    # End maintenance
    client.post("/api/admin/maintenance/end", json={}, headers=headers)

    # Cleanup backup files
    loc = backup_item.get("storage_location")
    if loc:
        Path(loc).unlink(missing_ok=True)
        p = Path(loc)
        (p.parent / (p.name + ".manifest.json")).unlink(missing_ok=True)
