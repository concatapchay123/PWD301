"""Unit test suite for Audit Logging Engine & Sensitive Admin Actions (TASK-022).

Validates:
- Append-only audit record creation and metadata verification (ADR-010).
- Recursive credential, token, and secret redaction into '[REDACTED]'.
- Fail-closed error handling: DB persistence failure rolls back mutations
  and raises AuditPersistenceError.
- Audit querying with multi-criteria filtering (action, actor, target, date, correlation).
- Pagination and ADR-002 Zero Internal PK Leakage in serialized dicts.
- Detailed audit record retrieval and non-admin access rejection.
- Account suspension, unsuspension, self-suspension guard, and session revocation workflows.
"""

from __future__ import annotations

import datetime
import json
import unittest.mock
import uuid

import pytest
from flask import Flask
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.identity import Role, User
from pwd301.models.notification_audit import AuditEvent
from pwd301.models.types import utc_now
from pwd301.services.audit_service import (
    force_revoke_user_sessions,
    get_audit_log_detail,
    query_audit_logs,
    record_audit_event,
    redact_sensitive_data,
    suspend_user_account,
    unsuspend_user_account,
)
from pwd301.services.exceptions import (
    AdminActionForbiddenError,
    AuditNotFoundError,
    AuditPersistenceError,
    ValidationError,
)
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.session_auth_service import create_auth_session
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
    """Create test admin user."""
    u = register_user(f"admin_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Admin Tester")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test student user."""
    u = register_user(
        f"student_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Student Tester"
    )
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test instructor user."""
    u = register_user(
        f"instructor_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Instructor Tester"
    )
    return assign_role_to_user(u.id, "INSTRUCTOR")


def test_record_audit_event_success(app: Flask, admin_user: User) -> None:
    """Validate successful audit log recording with actor context, timestamp, and metadata."""
    sess: Session = db.session
    corr_id = uuid.uuid4()

    event = record_audit_event(
        actor=admin_user,
        action="COURSE_ARCHIVE",
        target_type="COURSE",
        target_id=101,
        reason="Course term ended.",
        details={"status": "ARCHIVED", "reason": "End of semester"},
        correlation_id=corr_id,
        session=sess,
        commit=True,
    )

    assert event.id is not None
    assert event.event_id is not None
    assert event.action == "COURSE_ARCHIVE"
    assert event.target_type == "COURSE"
    assert event.target_id == 101
    assert event.actor_user_id == admin_user.id
    assert "ADMIN" in event.actor_roles_snapshot
    assert event.performed_as_admin is True
    assert event.request_id == corr_id
    assert event.reason == "Course term ended."
    assert event.created_at is not None

    # Verify JSON structure
    assert event.after_json is not None
    data = json.loads(event.after_json)
    assert data["status"] == "ARCHIVED"


def test_redact_sensitive_data_recursive() -> None:
    """Validate deep recursive redaction of credentials, API keys, and tokens."""
    payload = {
        "user_email": "test@example.com",
        "password": "SuperSecretPassword123!",
        "auth_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "gemini_api_key": "AIzaSyD-1234567890",
        "nested_details": {
            "sub_token": "secret-token-xyz",
            "session_key": "session-val",
            "safe_counter": 42,
            "raw_cookie": "session=abc",
        },
        "token_list": [
            {"access_token": "tok1", "name": "device_1"},
            {"public_info": "safe_data"},
        ],
    }

    redacted = redact_sensitive_data(payload)

    assert redacted["user_email"] == "test@example.com"
    assert redacted["password"] == "[REDACTED]"
    assert redacted["auth_token"] == "[REDACTED]"
    assert redacted["gemini_api_key"] == "[REDACTED]"

    nested = redacted["nested_details"]
    assert nested["sub_token"] == "[REDACTED]"
    assert nested["session_key"] == "[REDACTED]"
    assert nested["safe_counter"] == 42
    assert nested["raw_cookie"] == "[REDACTED]"

    assert redacted["token_list"][0]["access_token"] == "[REDACTED]"
    assert redacted["token_list"][0]["name"] == "device_1"
    assert redacted["token_list"][1]["public_info"] == "safe_data"


def test_record_audit_event_redaction_integration(app: Flask, admin_user: User) -> None:
    """Verify that record_audit_event sanitizes before_state and after_state before DB insert."""
    sess: Session = db.session

    before = {"password_hash": "argon2id$v=19$...", "email": "admin@example.com"}
    after = {"password": "NewPlainPassword!", "email": "admin@example.com", "auth_token": "abc"}

    event = record_audit_event(
        actor=admin_user,
        action="USER_PASSWORD_RESET",
        target_type="USER",
        target_id=admin_user.id,
        before_state=before,
        after_state=after,
        session=sess,
        commit=True,
    )

    clean_before = json.loads(event.before_json or "{}")
    clean_after = json.loads(event.after_json or "{}")

    assert clean_before["password_hash"] == "[REDACTED]"
    assert clean_before["email"] == "admin@example.com"
    assert clean_after["password"] == "[REDACTED]"
    assert clean_after["auth_token"] == "[REDACTED]"
    assert clean_after["email"] == "admin@example.com"


def test_record_audit_event_fail_closed_on_db_error(app: Flask, admin_user: User) -> None:
    """Simulate persistence failure; verify rollback and raise of AuditPersistenceError."""
    sess: Session = db.session

    with unittest.mock.patch.object(sess, "flush", side_effect=Exception("DB Connection Dropped")):
        with pytest.raises(AuditPersistenceError) as exc_info:
            record_audit_event(
                actor=admin_user,
                action="SENSITIVE_ACTION",
                target_type="SYSTEM",
                session=sess,
            )
        assert "Failed to persist mandatory audit log" in str(exc_info.value)


def test_suspend_user_account_fail_closed(app: Flask, admin_user: User, student_user: User) -> None:
    """Simulate commit failure in suspend_user_account; verify full rollback."""
    sess: Session = db.session

    with (
        unittest.mock.patch.object(sess, "commit", side_effect=Exception("Disk Full / I/O Error")),
        pytest.raises(AuditPersistenceError),
    ):
        suspend_user_account(
            admin_actor=admin_user,
            target_user_id=student_user.public_id,
            reason="Policy violation",
            session=sess,
        )

    # Verify student account state was rolled back and remained ACTIVE
    sess.expire_all()
    reloaded_student = sess.get(User, student_user.id)
    assert reloaded_student is not None
    assert reloaded_student.status == "ACTIVE"
    assert reloaded_student.suspended_at is None


def test_query_audit_logs_filters_and_pagination(
    app: Flask, admin_user: User, student_user: User, instructor_user: User
) -> None:
    """Validate query_audit_logs filtering by action, actor, target, date, and pagination."""
    sess: Session = db.session
    sess.query(AuditEvent).delete()
    sess.commit()

    t0 = utc_now() - datetime.timedelta(hours=2)
    t1 = utc_now() - datetime.timedelta(hours=1)
    t2 = utc_now()

    # Create 3 audit records
    e1 = record_audit_event(
        actor=admin_user,
        action="USER_SUSPEND",
        target_type="USER",
        target_id=student_user.public_id,
        reason="Suspension 1",
        session=sess,
    )
    e1.created_at = t0

    e2 = record_audit_event(
        actor=admin_user,
        action="COURSE_REASSIGN",
        target_type="COURSE",
        target_id=200,
        reason="Reassigned to instructor",
        session=sess,
    )
    e2.created_at = t1

    e3 = record_audit_event(
        actor=instructor_user,
        action="ASSESSMENT_PUBLISH",
        target_type="ASSESSMENT",
        target_id=300,
        reason="Published quiz",
        session=sess,
    )
    e3.created_at = t2
    sess.commit()

    # 1. Filter by Action
    items, total, page, per_page, pages = query_audit_logs(
        actor=admin_user, filters={"action": "USER_SUSPEND"}, session=sess
    )
    assert total == 1
    assert items[0]["action"] == "USER_SUSPEND"

    # 2. Filter by Actor ID
    items, total, page, per_page, pages = query_audit_logs(
        actor=admin_user, filters={"actor_id": str(admin_user.public_id)}, session=sess
    )
    assert total == 2

    # 3. Filter by Target Type
    items, total, page, per_page, pages = query_audit_logs(
        actor=admin_user, filters={"target_type": "ASSESSMENT"}, session=sess
    )
    assert total == 1
    assert items[0]["action"] == "ASSESSMENT_PUBLISH"

    # 4. Filter by Date range
    date_from = (t0 + datetime.timedelta(minutes=30)).isoformat()
    items, total, page, per_page, pages = query_audit_logs(
        actor=admin_user, filters={"date_from": date_from}, session=sess
    )
    assert total == 2

    # 5. Pagination
    items_p1, total_p, p, pp, total_pages = query_audit_logs(
        actor=admin_user, page=1, per_page=2, session=sess
    )
    assert total_p >= 3
    assert len(items_p1) == 2
    assert p == 1
    assert pp == 2
    assert total_pages >= 2

    items_p2, _, p2, _, _ = query_audit_logs(actor=admin_user, page=2, per_page=2, session=sess)
    assert len(items_p2) >= 1
    assert p2 == 2


def test_query_audit_logs_forbidden_for_non_admin(app: Flask, student_user: User) -> None:
    """Non-admin actors must be forbidden from querying audit logs."""
    with pytest.raises(AdminActionForbiddenError):
        query_audit_logs(actor=student_user)


def test_get_audit_log_detail(app: Flask, admin_user: User, student_user: User) -> None:
    """Retrieve audit log detail by public event_id and verify zero PK leakage."""
    sess: Session = db.session

    event = record_audit_event(
        actor=admin_user,
        action="USER_SUSPEND",
        target_type="USER",
        target_id=student_user.public_id,
        reason="Violation",
        details={"status": "SUSPENDED"},
        session=sess,
        commit=True,
    )

    detail = get_audit_log_detail(actor=admin_user, audit_id=event.event_id, session=sess)

    assert detail["id"] == str(event.event_id)
    assert detail["event_id"] == str(event.event_id)
    assert detail["action"] == "USER_SUSPEND"
    assert detail["actor_id"] == str(admin_user.public_id)
    assert detail["actor_name"] == admin_user.display_name
    assert detail["target_type"] == "USER"
    assert detail["target_id"] == str(student_user.public_id)
    assert detail["reason"] == "Violation"
    assert detail["after"]["status"] == "SUSPENDED"

    # Nonexistent UUID raises AuditNotFoundError
    with pytest.raises(AuditNotFoundError):
        get_audit_log_detail(actor=admin_user, audit_id=uuid.uuid4(), session=sess)

    # Malformed UUID raises AuditNotFoundError
    with pytest.raises(AuditNotFoundError):
        get_audit_log_detail(actor=admin_user, audit_id="not-a-uuid", session=sess)

    # Non-admin access raises AdminActionForbiddenError
    with pytest.raises(AdminActionForbiddenError):
        get_audit_log_detail(actor=student_user, audit_id=event.event_id, session=sess)


def test_suspend_and_unsuspend_user_workflow(
    app: Flask, admin_user: User, student_user: User
) -> None:
    """Validate full suspend -> audit -> unsuspend -> audit lifecycle."""
    sess: Session = db.session

    # 1. Establish session & tokens for student
    auth_sess, _ = create_auth_session(student_user, session=sess)
    _ = create_token_pair(student_user, session=sess)
    sess.commit()

    initial_auth_version = student_user.auth_version

    # 2. Suspend account
    suspended_u = suspend_user_account(
        admin_actor=admin_user,
        target_user_id=student_user.public_id,
        reason="Terms of service violation",
        session=sess,
    )

    assert suspended_u.status == "SUSPENDED"
    assert suspended_u.suspended_at is not None
    assert suspended_u.suspension_reason == "Terms of service violation"
    assert suspended_u.auth_version == initial_auth_version + 1
    assert not suspended_u.is_active

    # Check session was revoked
    sess.refresh(auth_sess)
    assert auth_sess.revoked_at is not None

    # Check audit log exists
    audit_record = (
        sess.query(AuditEvent)
        .filter(
            AuditEvent.action == "USER_SUSPEND",
            AuditEvent.target_id == student_user.id,
        )
        .order_by(AuditEvent.id.desc())
        .first()
    )
    assert audit_record is not None
    assert audit_record.reason == "Terms of service violation"

    # 3. Unsuspend account
    unsuspended_u = unsuspend_user_account(
        admin_actor=admin_user,
        target_user_id=student_user.public_id,
        reason="Appeal accepted",
        session=sess,
    )

    assert unsuspended_u.status == "ACTIVE"
    assert unsuspended_u.suspended_at is None
    assert unsuspended_u.suspension_reason is None
    assert unsuspended_u.auth_version == initial_auth_version + 2
    assert unsuspended_u.is_active

    # Check unsuspend audit log exists
    audit_unsuspend = (
        sess.query(AuditEvent)
        .filter(
            AuditEvent.action == "USER_UNSUSPEND",
            AuditEvent.target_id == student_user.id,
        )
        .order_by(AuditEvent.id.desc())
        .first()
    )
    assert audit_unsuspend is not None
    assert audit_unsuspend.reason == "Appeal accepted"


def test_suspend_guards(app: Flask, admin_user: User, student_user: User) -> None:
    """Validate validation rules: reason required and cannot suspend own account."""
    # Empty reason
    with pytest.raises(ValidationError) as exc:
        suspend_user_account(
            admin_actor=admin_user,
            target_user_id=student_user.public_id,
            reason="   ",
        )
    assert "Reason is required" in str(exc.value)

    # Self-suspension
    with pytest.raises(ValidationError) as exc:
        suspend_user_account(
            admin_actor=admin_user,
            target_user_id=admin_user.public_id,
            reason="I want to suspend myself",
        )
    assert "Administrators cannot suspend their own account" in str(exc.value)


def test_force_revoke_user_sessions(app: Flask, admin_user: User, student_user: User) -> None:
    """Validate force_revoke_user_sessions increments auth_version and invalidates sessions."""
    sess: Session = db.session

    # Establish 2 sessions
    s1, _ = create_auth_session(student_user, session=sess)
    s2, _ = create_auth_session(student_user, session=sess)
    sess.commit()

    initial_version = student_user.auth_version

    updated_u = force_revoke_user_sessions(
        admin_actor=admin_user,
        target_user_id=student_user.public_id,
        reason="Device lost",
        session=sess,
    )

    assert updated_u.auth_version == initial_version + 1

    sess.refresh(s1)
    sess.refresh(s2)
    assert s1.revoked_at is not None
    assert s2.revoked_at is not None

    # Check audit log
    event = (
        sess.query(AuditEvent)
        .filter(
            AuditEvent.action == "USER_REVOKE_SESSIONS",
            AuditEvent.target_id == student_user.id,
        )
        .first()
    )
    assert event is not None
    assert event.reason == "Device lost"
