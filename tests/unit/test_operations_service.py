"""Unit tests for Operations, Backup & Recovery Engine (TASK-026).

Verifies:
- Operational health checking across DB, storage, workers, and mail queue.
- Backup creation with SHA-256 cryptographic verification and manifest.
- ADR-002 Zero PK Leakage for backups, snapshots, and maintenance windows.
- Cryptographic integrity verification (clean vs tampered file detection).
- Dry-run restore drill: compatibility verification without altering live DB.
- Two-step fail-safe database restore (mandatory admin password + exact confirmation phrase).
- Fail-closed audit logging on sensitive mutations.
- Maintenance window lifecycle management.
- Lifecycle retention policy pruning.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import uuid
from pathlib import Path

import pytest
from flask import Flask
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.identity import Role, User
from pwd301.models.notification_audit import AuditEvent
from pwd301.models.operations import (
    BackgroundJob,
    BackupRun,
    MaintenanceWindow,
    SystemBackup,
)
from pwd301.models.types import utc_now
from pwd301.services.exceptions import (
    BackupIntegrityError,
    ForbiddenError,
    RestoreForbiddenError,
    ValidationError,
)
from pwd301.services.operations_service import (
    _prune_expired_backups,
    check_system_health,
    create_database_backup,
    end_maintenance_window,
    execute_dry_run_restore,
    is_maintenance_active,
    list_backups,
    restore_database_snapshot,
    start_maintenance_window,
    verify_backup_integrity,
)
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
        email="admin_ops@example.com",
        password="Password123!",
        display_name="Admin Ops",
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
        email="student_ops@example.com",
        password="Password123!",
        display_name="Student Ops",
        session=sess,
    )
    user.is_email_verified = True
    sess.commit()
    return user


# =====================================================================
# 1. Operational Health Monitoring Tests
# =====================================================================


def test_check_system_health_summary(app: Flask, admin_user: User) -> None:
    """System health check returns valid high-level summary."""
    with app.app_context():
        report = check_system_health(include_details=False, session=db.session)
        assert report["status"] in ("HEALTHY", "DEGRADED")
        assert "database" in report
        assert report["database"]["status"] == "HEALTHY"
        assert report["database"]["latency_ms"] >= 0
        assert "storage" in report
        assert "timestamp" in report


def test_check_system_health_deep_details(app: Flask, admin_user: User) -> None:
    """Deep system health inspection includes all component diagnostics."""
    with app.app_context():
        # Enqueue a dummy background job to verify worker queue reporting
        job = BackgroundJob(
            job_type="BACKUP",
            status="QUEUED",
            priority=100,
        )
        db.session.add(job)
        db.session.commit()

        report = check_system_health(include_details=True, session=db.session)
        assert "components" in report
        components = report["components"]

        assert "database" in components
        assert components["database"]["status"] == "HEALTHY"

        assert "storage" in components
        assert "directories" in components["storage"]

        assert "clamav" in components
        assert components["clamav"]["status"] in ("HEALTHY", "DEGRADED")

        assert "workers" in components
        assert components["workers"]["queued_jobs"] >= 1

        assert "mail_queue" in components
        assert "backup" in components


# =====================================================================
# 2. Database Backup Engine Tests
# =====================================================================


def test_create_database_backup_flow(app: Flask, admin_user: User) -> None:
    """Admin initiates manual backup: creates file, manifest, DB record, and audit log."""
    with app.app_context():
        backup = create_database_backup(
            actor=admin_user,
            backup_type="MANUAL",
            notes="Pre-upgrade operational snapshot",
            session=db.session,
        )

        assert isinstance(backup, BackupRun)
        assert isinstance(backup, SystemBackup)
        assert backup.status == "SUCCEEDED"
        assert backup.backup_type == "MANUAL"
        assert backup.started_by_user_id == admin_user.id
        assert backup.completed_at is not None

        # Verify physical file existence
        backup_path = Path(backup.storage_location)
        assert backup_path.is_file()
        content = backup_path.read_bytes()
        computed_hash = hashlib.sha256(content).hexdigest()

        # Verify manifest
        manifest_path = backup_path.parent / (backup_path.name + ".manifest.json")
        assert manifest_path.is_file()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["sha256"] == computed_hash
        assert manifest["database_backup_name"] == backup.database_backup_name

        # Verify Audit Log entry
        audit = (
            db.session.query(AuditEvent)
            .filter(
                AuditEvent.action == "DATABASE_BACKUP_CREATED",
                AuditEvent.actor_user_id == admin_user.id,
            )
            .order_by(AuditEvent.created_at.desc())
            .first()
        )
        assert audit is not None
        assert audit.performed_as_admin is True

        # Clean up files created
        backup_path.unlink(missing_ok=True)
        manifest_path.unlink(missing_ok=True)


def test_create_backup_non_admin_forbidden(app: Flask, student_user: User) -> None:
    """Non-admin student attempting backup creation is rejected with ForbiddenError."""
    with app.app_context(), pytest.raises(ForbiddenError):
        create_database_backup(actor=student_user, session=db.session)


def test_list_backups_adr002_compliance(app: Flask, admin_user: User) -> None:
    """List backups returns historical records adhering strictly to ADR-002."""
    with app.app_context():
        b1 = create_database_backup(actor=admin_user, backup_type="MANUAL", session=db.session)
        b2 = create_database_backup(actor=admin_user, backup_type="AUTOMATIC", session=db.session)

        items = list_backups(actor=admin_user, session=db.session)
        assert len(items) >= 2

        for item in items:
            assert "backup_id" in item
            # Valid UUID representation
            u = uuid.UUID(item["backup_id"])
            assert str(u) == item["backup_id"]
            # Zero internal BIGINT PK leakage
            assert "id" not in item
            assert item["status"] == "SUCCEEDED"

        # Cleanup physical files
        for b in (b1, b2):
            Path(b.storage_location).unlink(missing_ok=True)
            p = Path(b.storage_location)
            (p.parent / (p.name + ".manifest.json")).unlink(missing_ok=True)


# =====================================================================
# 3. Cryptographic Integrity & Tamper Detection Tests
# =====================================================================


def test_verify_backup_integrity_clean(app: Flask, admin_user: User) -> None:
    """Clean backup passes cryptographic verification and updates verified_at timestamp."""
    with app.app_context():
        backup = create_database_backup(actor=admin_user, session=db.session)
        backup_id = str(backup.public_id)

        assert backup.verified_at is None
        result = verify_backup_integrity(actor=admin_user, backup_id=backup_id, session=db.session)

        assert result["status"] == "VERIFIED"
        assert result["verified"] is True
        assert "checksum" in result

        db.session.refresh(backup)
        assert backup.verified_at is not None
        assert backup.last_error is None

        # Verify audit log
        audit = (
            db.session.query(AuditEvent)
            .filter(AuditEvent.action == "DATABASE_BACKUP_VERIFIED")
            .order_by(AuditEvent.created_at.desc())
            .first()
        )
        assert audit is not None

        # Cleanup
        Path(backup.storage_location).unlink(missing_ok=True)
        p = Path(backup.storage_location)
        (p.parent / (p.name + ".manifest.json")).unlink(missing_ok=True)


def test_verify_backup_integrity_tampered_content(app: Flask, admin_user: User) -> None:
    """Tampered backup file causes checksum mismatch and raises BackupIntegrityError."""
    with app.app_context():
        backup = create_database_backup(actor=admin_user, session=db.session)
        backup_id = str(backup.public_id)
        backup_path = Path(backup.storage_location)

        # Tamper with file by injecting arbitrary payload
        backup_path.write_bytes(b'{"malicious_tamper": true, "corrupted": true}')

        with pytest.raises(BackupIntegrityError):
            verify_backup_integrity(actor=admin_user, backup_id=backup_id, session=db.session)

        db.session.refresh(backup)
        assert backup.last_error is not None
        assert "mismatch" in backup.last_error.lower() or "corrupted" in backup.last_error.lower()

        # Cleanup
        backup_path.unlink(missing_ok=True)
        p = Path(backup.storage_location)
        (p.parent / (p.name + ".manifest.json")).unlink(missing_ok=True)


def test_verify_backup_missing_file(app: Flask, admin_user: User) -> None:
    """Missing backup file triggers BackupIntegrityError."""
    with app.app_context():
        backup = create_database_backup(actor=admin_user, session=db.session)
        backup_id = str(backup.public_id)
        backup_path = Path(backup.storage_location)
        backup_path.unlink(missing_ok=True)

        with pytest.raises(BackupIntegrityError):
            verify_backup_integrity(actor=admin_user, backup_id=backup_id, session=db.session)


# =====================================================================
# 4. Fail-Safe Restore & Dry-Run Engine Tests
# =====================================================================


def test_execute_dry_run_restore(app: Flask, admin_user: User) -> None:
    """Dry-run restore drill tests compatibility without altering live database."""
    with app.app_context():
        backup = create_database_backup(actor=admin_user, session=db.session)
        backup_id = str(backup.public_id)

        user_count_before = db.session.query(User).count()

        result = execute_dry_run_restore(actor=admin_user, backup_id=backup_id, session=db.session)

        assert result["dry_run"] is True
        assert result["status"] == "COMPATIBLE"
        assert result["live_database_modified"] is False
        assert "tables_detected" in result

        # Ensure live data was untouched
        user_count_after = db.session.query(User).count()
        assert user_count_before == user_count_after

        # Verify Audit Log
        audit = (
            db.session.query(AuditEvent)
            .filter(AuditEvent.action == "DATABASE_RESTORE_DRY_RUN")
            .order_by(AuditEvent.created_at.desc())
            .first()
        )
        assert audit is not None

        # Cleanup
        Path(backup.storage_location).unlink(missing_ok=True)
        p = Path(backup.storage_location)
        (p.parent / (p.name + ".manifest.json")).unlink(missing_ok=True)


def test_restore_database_snapshot_safeguards(app: Flask, admin_user: User) -> None:
    """Restore enforces exact confirmation phrase and admin password re-authentication."""
    with app.app_context():
        backup = create_database_backup(actor=admin_user, session=db.session)
        backup_id = str(backup.public_id)

        # 1. Missing confirmation phrase
        with pytest.raises(RestoreForbiddenError) as exc_info:
            restore_database_snapshot(
                actor=admin_user,
                backup_id=backup_id,
                confirmation_phrase=None,
                password="Password123!",
                session=db.session,
            )
        assert "confirmation phrase" in str(exc_info.value).lower()

        # 2. Incorrect confirmation phrase
        with pytest.raises(RestoreForbiddenError) as exc_info:
            restore_database_snapshot(
                actor=admin_user,
                backup_id=backup_id,
                confirmation_phrase="YES_PLEASE_RESTORE",
                password="Password123!",
                session=db.session,
            )
        assert "CONFIRM_DATABASE_RESTORE" in str(exc_info.value)

        # 3. Wrong admin password
        with pytest.raises(RestoreForbiddenError) as exc_info:
            restore_database_snapshot(
                actor=admin_user,
                backup_id=backup_id,
                confirmation_phrase="CONFIRM_DATABASE_RESTORE",
                password="WrongPassword999!",
                session=db.session,
            )
        assert "password" in str(exc_info.value).lower()

        # 4. Successful restore under valid phrase & correct password
        result = restore_database_snapshot(
            actor=admin_user,
            backup_id=backup_id,
            confirmation_phrase="CONFIRM_DATABASE_RESTORE",
            password="Password123!",
            session=db.session,
        )
        assert result["status"] == "RESTORED"

        # Verify both INITIATED and COMPLETED audit events were written
        actions = [
            e.action
            for e in db.session.query(AuditEvent)
            .filter(
                AuditEvent.action.in_(["DATABASE_RESTORE_INITIATED", "DATABASE_RESTORE_COMPLETED"])
            )
            .all()
        ]
        assert "DATABASE_RESTORE_INITIATED" in actions
        assert "DATABASE_RESTORE_COMPLETED" in actions

        # Cleanup
        Path(backup.storage_location).unlink(missing_ok=True)
        p = Path(backup.storage_location)
        (p.parent / (p.name + ".manifest.json")).unlink(missing_ok=True)


# =====================================================================
# 5. Maintenance Window Engine Tests
# =====================================================================


def test_maintenance_window_lifecycle(app: Flask, admin_user: User) -> None:
    """Maintenance window activation, status check, and conclusion lifecycle."""
    with app.app_context():
        # Initially inactive
        is_active, win = is_maintenance_active(session=db.session)
        assert is_active is False
        assert win is None

        # Start maintenance
        window = start_maintenance_window(
            actor=admin_user,
            reason="Database index migration & vacuuming",
            estimated_duration_minutes=45,
            session=db.session,
        )
        assert isinstance(window, MaintenanceWindow)
        assert window.status == "ACTIVE"
        assert window.reason == "Database index migration & vacuuming"
        assert window.estimated_duration_minutes == 45
        assert window.started_by_user_id == admin_user.id

        # Now active
        is_active, current_win = is_maintenance_active(session=db.session)
        assert is_active is True
        assert current_win is not None
        assert current_win.id == window.id

        # Conclude maintenance
        ended_win = end_maintenance_window(
            actor=admin_user,
            window_id=str(window.public_id),
            session=db.session,
        )
        assert ended_win.status == "COMPLETED"
        assert ended_win.ended_at is not None

        # Now inactive again
        is_active, win_after = is_maintenance_active(session=db.session)
        assert is_active is False
        assert win_after is None


def test_start_maintenance_validation(app: Flask, admin_user: User) -> None:
    """Starting maintenance with empty reason or invalid duration raises ValidationError."""
    with app.app_context():
        with pytest.raises(ValidationError):
            start_maintenance_window(actor=admin_user, reason="", session=db.session)

        with pytest.raises(ValidationError):
            start_maintenance_window(
                actor=admin_user,
                reason="Valid",
                estimated_duration_minutes=0,
                session=db.session,
            )


# =====================================================================
# 6. Retention Policy Pruning Tests
# =====================================================================


def test_backup_retention_pruning(app: Flask, admin_user: User) -> None:
    """Expired backups exceeding retention policy are pruned."""
    with app.app_context():
        old_backup = create_database_backup(actor=admin_user, session=db.session)
        # Artificially age the backup record
        old_backup.started_at = utc_now() - datetime.timedelta(days=45)
        db.session.commit()

        pruned = _prune_expired_backups(db.session, retention_days=30)
        assert pruned >= 1

        # File is unlinked
        assert not Path(old_backup.storage_location).is_file()
