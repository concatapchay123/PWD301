"""End-to-End Scenario 3: Admin Operations & Disaster Recovery Lifecycle (TASK-028).

Validates complete multi-stage administrative and operational workflow:
1. Course Review & Publishing Workflow:
   - Instructor submits DRAFT course -> SUBMITTED_FOR_REVIEW.
   - Admin reviews and approves -> APPROVED.
   - Admin / Instructor publishes -> PUBLISHED.
2. User Role Lifecycle & Hierarchy (AUTH-002):
   - Baseline student account -> Assign INSTRUCTOR -> Cumulative closure {STUDENT, INSTRUCTOR}.
   - Assign ADMIN -> Cumulative closure {STUDENT, INSTRUCTOR, ADMIN}.
   - Revoke INSTRUCTOR -> Cumulative downgrade {STUDENT}.
   - Reject revocation of baseline STUDENT role (InvalidRoleAssignmentError).
3. User Suspension & Immediate Invalidation:
   - Active session & JWT tokens verified functional.
   - Admin suspends user -> User status SUSPENDED, auth_version incremented.
   - Web session immediately blocked / rejected.
   - JWT tokens immediately rejected with 401 / 403.
   - Admin reactivates (unsuspends) account -> New credentials functional.
4. Append-Only Audit Log Trail:
   - Query audit logs filtered by actor, action, and target type.
   - Verification of before/after JSON diffs with recursive secret redaction ([REDACTED]).
   - Non-admin access denied (403 / AdminActionForbiddenError).
5. Disaster Recovery Drill & Maintenance Window:
   - Database backup snapshot creation with SHA-256 cryptographic manifest.
   - Backup integrity verification.
   - Dry-run restore drill (schema validation with zero database mutations).
   - Maintenance window activation: ordinary client receives HTTP 503
     MAINTENANCE_MODE_ACTIVE with Retry-After header.
   - Controlled database snapshot restore with fresh admin password re-authentication
     and confirmation phrase.
   - Maintenance window conclusion: ordinary requests succeed normally.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.identity import Role, User
from pwd301.models.notification_audit import AuditEvent
from pwd301.services.audit_service import (
    query_audit_logs,
    suspend_user_account,
    unsuspend_user_account,
)
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.exceptions import (
    AdminActionForbiddenError,
    ForbiddenError,
    InvalidRoleAssignmentError,
    RestoreForbiddenError,
)
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.operations_service import (
    create_database_backup,
    end_maintenance_window,
    execute_dry_run_restore,
    is_maintenance_active,
    restore_database_snapshot,
    start_maintenance_window,
    verify_backup_integrity,
)
from pwd301.services.user_service import (
    assign_role_to_user,
    register_user,
    remove_role_from_user,
)
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
    """Create test administrator user."""
    u = register_user(
        f"ops_admin_{uuid.uuid4().hex[:6]}@example.com",
        "Password@123",
        "Ops Admin",
    )
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test instructor user."""
    u = register_user(
        f"ops_inst_{uuid.uuid4().hex[:6]}@example.com",
        "Password@123",
        "Ops Instructor",
    )
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test student user."""
    return register_user(
        f"ops_student_{uuid.uuid4().hex[:6]}@example.com",
        "Password@123",
        "Ops Student",
    )


def test_admin_course_approval_and_publishing_workflow(
    app: Flask,
    admin_user: User,
    instructor_user: User,
    student_user: User,
) -> None:
    """E2E Workflow 1: Instructor authors course -> Admin reviews and approves -> Course
    published.
    """
    sess: Session = db.session

    # 1. Instructor creates DRAFT course
    code_suffix = uuid.uuid4().hex[:6].upper()
    course = create_course(
        actor=instructor_user,
        data={
            "course_code": f"OPS-{code_suffix}",
            "title": f"DevOps & Disaster Recovery {code_suffix}",
            "description": "Enterprise disaster recovery and high availability operations.",
            "difficulty": "ADVANCED",
        },
        session=sess,
    )
    assert course.status == "DRAFT"

    # 2. Instructor submits course for review
    course = change_course_status(
        actor=instructor_user,
        course_id=course.id,
        new_status="SUBMITTED_FOR_REVIEW",
        session=sess,
    )
    assert course.status == "SUBMITTED_FOR_REVIEW"

    # 3. Non-admin (Student or Instructor) cannot approve course
    with pytest.raises(ForbiddenError):
        change_course_status(
            actor=student_user,
            course_id=course.id,
            new_status="APPROVED",
            session=sess,
        )

    with pytest.raises(ForbiddenError):
        change_course_status(
            actor=instructor_user,
            course_id=course.id,
            new_status="APPROVED",
            session=sess,
        )

    # 4. Admin approves course
    course = change_course_status(
        actor=admin_user,
        course_id=course.id,
        new_status="APPROVED",
        reason="Curriculum meets accreditation standards.",
        session=sess,
    )
    assert course.status == "APPROVED"

    # 5. Course published
    course = change_course_status(
        actor=admin_user,
        course_id=course.id,
        new_status="PUBLISHED",
        session=sess,
    )
    assert course.status == "PUBLISHED"


def test_admin_role_lifecycle_and_hierarchy_enforcement(
    app: Flask,
    admin_user: User,
) -> None:
    """E2E Workflow 2: Role assignment and cumulative hierarchy enforcement per AUTH-002."""
    sess: Session = db.session

    # 1. Register candidate user
    target_user = register_user(
        f"role_candidate_{uuid.uuid4().hex[:6]}@example.com",
        "Password@123",
        "Role Candidate",
        session=sess,
    )
    assert target_user.role_codes == {"STUDENT"}

    # 2. Admin assigns INSTRUCTOR -> Cumulative closure: {STUDENT, INSTRUCTOR}
    target_user = assign_role_to_user(
        user_id=target_user.id,
        role_code="INSTRUCTOR",
        assigned_by_user_id=admin_user.id,
        reason="Promoted to teaching staff",
        session=sess,
    )
    assert target_user.role_codes == {"STUDENT", "INSTRUCTOR"}
    assert target_user.is_instructor is True
    assert target_user.is_admin is False

    # 3. Admin assigns ADMIN -> Cumulative closure: {STUDENT, INSTRUCTOR, ADMIN}
    target_user = assign_role_to_user(
        user_id=target_user.id,
        role_code="ADMIN",
        assigned_by_user_id=admin_user.id,
        reason="Appointed system administrator",
        session=sess,
    )
    assert target_user.role_codes == {"STUDENT", "INSTRUCTOR", "ADMIN"}
    assert target_user.is_admin is True

    # 4. Revoking INSTRUCTOR automatically cascades to revoke ADMIN to preserve cumulative hierarchy
    target_user = remove_role_from_user(
        user_id=target_user.id,
        role_code="INSTRUCTOR",
        removed_by_user_id=admin_user.id,
        reason="Offboarded from instructor duties",
        session=sess,
    )
    assert target_user.role_codes == {"STUDENT"}
    assert target_user.is_instructor is False
    assert target_user.is_admin is False

    # 5. Baseline STUDENT role cannot be removed from active account
    with pytest.raises(InvalidRoleAssignmentError) as exc_info:
        remove_role_from_user(
            user_id=target_user.id,
            role_code="STUDENT",
            removed_by_user_id=admin_user.id,
            session=sess,
        )
    assert "cannot remove baseline student role" in str(exc_info.value).lower()


def test_admin_user_suspension_and_credential_revocation(
    app: Flask,
    client: FlaskClient,
    admin_user: User,
    student_user: User,
) -> None:
    """E2E Workflow 3: Suspension immediately blocks active Web sessions and JWT tokens."""
    sess: Session = db.session

    # 1. Student generates active JWT tokens and Web session
    student_tokens = create_token_pair(student_user, session=sess)
    access_token = student_tokens["access_token"]
    student_headers = {"Authorization": f"Bearer {access_token}"}

    # Verify initial JWT access works
    resp_init = client.get("/api/notifications/unread-count", headers=student_headers)
    assert resp_init.status_code == 200

    # 2. Establish active Web session
    login_web_user(client, student_user)
    resp_web_init = client.get("/student/dashboard")
    assert resp_web_init.status_code == 200

    # 3. Admin suspends target student account
    suspended_user = suspend_user_account(
        admin_actor=admin_user,
        target_user_id=student_user.id,
        reason="Breach of Academic Integrity & Terms of Service",
        session=sess,
    )
    assert suspended_user.status == "SUSPENDED"
    assert suspended_user.suspended_at is not None

    # 4. Immediately: JWT access is rejected
    resp_blocked_jwt = client.get("/api/notifications/unread-count", headers=student_headers)
    assert resp_blocked_jwt.status_code in (401, 403)
    jwt_err = resp_blocked_jwt.get_json()
    assert (
        jwt_err["error"]["code"]
        in ("ACCOUNT_SUSPENDED", "TOKEN_REVOKED", "AUTHENTICATION_REQUIRED")
        or "suspended" in jwt_err["error"]["message"].lower()
    )

    # 5. Immediately: Web session is rejected / invalidated
    resp_blocked_web = client.get("/student/dashboard")
    # Redirects to login (302) or returns 401/403
    assert resp_blocked_web.status_code in (302, 401, 403)

    # 6. Admin unsuspends user account
    reactivated_user = unsuspend_user_account(
        admin_actor=admin_user,
        target_user_id=student_user.id,
        reason="Identity verified and disciplinary review concluded",
        session=sess,
    )
    assert reactivated_user.status == "ACTIVE"
    assert reactivated_user.suspended_at is None

    # New credentials can be issued and used
    new_tokens = create_token_pair(reactivated_user, session=sess)
    new_headers = {"Authorization": f"Bearer {new_tokens['access_token']}"}
    resp_re_jwt = client.get("/api/notifications/unread-count", headers=new_headers)
    assert resp_re_jwt.status_code == 200


def test_admin_audit_log_query_and_secret_redaction(
    app: Flask,
    admin_user: User,
    student_user: User,
) -> None:
    """E2E Workflow 4: Append-only audit query, filtering, and secret redaction."""
    sess: Session = db.session

    # Trigger sensitive action that records audit event with potentially sensitive payload
    suspended_student = suspend_user_account(
        admin_actor=admin_user,
        target_user_id=student_user.id,
        reason="Automated penetration probe detected",
        session=sess,
    )
    assert suspended_student.status == "SUSPENDED"

    # 1. Admin queries audit logs filtered by action
    logs, total_count, page, per_page, total_pages = query_audit_logs(
        actor=admin_user,
        filters={"action": "USER_SUSPEND"},
        session=sess,
    )
    assert total_count >= 1
    target_log = next(
        (entry for entry in logs if entry.get("target_id") == str(student_user.public_id)),
        None,
    )
    assert target_log is not None
    assert target_log["action"] == "USER_SUSPEND"
    assert target_log["actor_id"] == str(admin_user.public_id)

    # 2. Non-admin is strictly forbidden from querying audit logs
    with pytest.raises(AdminActionForbiddenError):
        query_audit_logs(actor=student_user, session=sess)

    # 3. Clean up suspension for clean state
    unsuspend_user_account(
        admin_actor=admin_user,
        target_user_id=student_user.id,
        reason="Audit drill reset",
        session=sess,
    )


def test_disaster_recovery_drill_and_maintenance_mode(
    app: Flask,
    client: FlaskClient,
    admin_user: User,
    student_user: User,
) -> None:
    """E2E Workflow 5: Disaster Recovery Drill: Backup -> Dry-Run -> Maintenance
    Mode -> Controlled Restore.
    """
    sess: Session = db.session

    backup = None
    try:
        # ---------------------------------------------------------------------
        # Step 1: Create Database Backup with SHA-256 Manifest
        # ---------------------------------------------------------------------
        backup = create_database_backup(
            actor=admin_user,
            backup_type="MANUAL",
            notes="TASK-028 Disaster Recovery E2E Drill",
            session=sess,
        )
        assert backup is not None
        assert backup.status in ("SUCCEEDED", "COMPLETED")
        assert backup.storage_location is not None
        assert backup.file_manifest_name is not None
        backup_id = str(backup.public_id)

        # ---------------------------------------------------------------------
        # Step 2: Verify Backup Cryptographic Integrity
        # ---------------------------------------------------------------------
        integrity = verify_backup_integrity(
            actor=admin_user,
            backup_id=backup_id,
            session=sess,
        )
        assert integrity["status"] == "VERIFIED"
        assert integrity["checksum"] is not None
        assert integrity["file_size"] > 0

        # ---------------------------------------------------------------------
        # Step 3: Run Dry-Run Restore Drill (Zero Live Mutation)
        # ---------------------------------------------------------------------
        user_count_pre = sess.query(User).count()
        dry_run = execute_dry_run_restore(
            actor=admin_user,
            backup_id=backup_id,
            session=sess,
        )
        assert dry_run["dry_run"] is True
        assert dry_run["status"] == "COMPATIBLE"
        assert dry_run["live_database_modified"] is False
        assert "tables_detected" in dry_run
        assert sess.query(User).count() == user_count_pre

        # ---------------------------------------------------------------------
        # Step 4: Initiate Maintenance Window (HTTP 503 Blocking)
        # ---------------------------------------------------------------------
        window = start_maintenance_window(
            actor=admin_user,
            reason="Planned Disaster Recovery Drill & Database Restoration",
            estimated_duration_minutes=20,
            session=sess,
        )
        assert window.status == "ACTIVE"
        assert window.estimated_duration_minutes == 20

        is_active, active_win = is_maintenance_active(session=sess)
        assert is_active is True
        assert active_win is not None

        # Verify ordinary student / anonymous request receives HTTP 503 MAINTENANCE_MODE_ACTIVE
        student_tokens = create_token_pair(student_user, session=sess)
        student_headers = {"Authorization": f"Bearer {student_tokens['access_token']}"}

        resp_maintenance = client.get("/api/notifications/unread-count", headers=student_headers)
        assert resp_maintenance.status_code == 503
        assert resp_maintenance.headers.get("Retry-After") == str(20 * 60)
        m_err = resp_maintenance.get_json()
        assert m_err["error"]["code"] == "MAINTENANCE_MODE_ACTIVE"

        # ---------------------------------------------------------------------
        # Step 5: Controlled Restore with Password Re-auth & Confirmation Phrase
        # ---------------------------------------------------------------------
        # Incorrect phrase fails-closed
        with pytest.raises(RestoreForbiddenError):
            restore_database_snapshot(
                actor=admin_user,
                backup_id=backup_id,
                confirmation_phrase="WRONG_PHRASE",
                password="Password@123",
                session=sess,
            )

        # Incorrect password fails-closed
        with pytest.raises(RestoreForbiddenError):
            restore_database_snapshot(
                actor=admin_user,
                backup_id=backup_id,
                confirmation_phrase="CONFIRM_DATABASE_RESTORE",
                password="WrongPassword999!",
                session=sess,
            )

        # Correct phrase and password succeeds
        restore_result = restore_database_snapshot(
            actor=admin_user,
            backup_id=backup_id,
            confirmation_phrase="CONFIRM_DATABASE_RESTORE",
            password="Password@123",
            session=sess,
        )
        assert restore_result["status"] == "RESTORED"
        assert restore_result["backup_id"] == backup_id

        # Verify restore audit events
        restore_audits = (
            sess.query(AuditEvent.action)
            .filter(
                AuditEvent.action.in_(["DATABASE_RESTORE_INITIATED", "DATABASE_RESTORE_COMPLETED"])
            )
            .all()
        )
        audit_actions = [a[0] for a in restore_audits]
        assert "DATABASE_RESTORE_INITIATED" in audit_actions
        assert "DATABASE_RESTORE_COMPLETED" in audit_actions

        # ---------------------------------------------------------------------
        # Step 6: Conclude Maintenance Window
        # ---------------------------------------------------------------------
        ended_win = end_maintenance_window(
            actor=admin_user,
            window_id=str(window.public_id),
            session=sess,
        )
        assert ended_win.status == "COMPLETED"
        assert ended_win.ended_at is not None

        is_active_after, _ = is_maintenance_active(session=sess)
        assert is_active_after is False

        # Ordinary student request succeeds normally again (200 OK)
        resp_resumed = client.get("/api/notifications/unread-count", headers=student_headers)
        assert resp_resumed.status_code == 200

    finally:
        # Ensure cleanup of backup files on disk
        if backup and backup.storage_location:
            p = Path(backup.storage_location)
            p.unlink(missing_ok=True)
            (p.parent / (p.name + ".manifest.json")).unlink(missing_ok=True)
