"""Unit test suite for Notification Service (TASK-021).

Tests:
- Event emission and payload sanitization (passwords/secrets redacted).
- Idempotency using event_key.
- In-app notification creation with category mapping.
- Preference handling for optional categories (disabling skips email).
- Mandatory security invariant (SECURITY events cannot be disabled).
- Rejection of security opt-out with MandatoryNotificationOptOutError.
- Read tracking, bulk mark read, unread count accuracy.
- Dismissal semantics.
- Admin system broadcasting with role targeting.
"""

from __future__ import annotations

import json
import uuid

import pytest
from flask import Flask
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.identity import Role, User
from pwd301.services.exceptions import (
    ForbiddenError,
    MandatoryNotificationOptOutError,
    NotificationPreferenceError,
)
from pwd301.services.notification_service import (
    broadcast_system_notification,
    dismiss_notification,
    dispatch_notification,
    emit_event,
    get_unread_count,
    list_user_notifications,
    mark_all_as_read,
    mark_notification_as_read,
    update_user_preferences,
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
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test student user."""
    u = register_user(
        f"notif_student_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Student One"
    )
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test admin user."""
    u = register_user(
        f"notif_admin_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Admin One"
    )
    return assign_role_to_user(u.id, "ADMIN")


def test_emit_event_sanitizes_payload(app: Flask, student_user: User) -> None:
    """Test that emit_event redacts passwords, tokens, and secrets."""
    payload = {
        "user_email": student_user.email,
        "password": "SuperSecretPassword123!",
        "access_token": "eyJhbGciOi...",
        "course_title": "Web Development 101",
    }
    event = emit_event(
        event_type="TEST_EVENT",
        payload=payload,
        actor_user_id=student_user.id,
        session=db.session,
    )
    db.session.commit()

    assert event.id is not None
    assert event.payload_json is not None
    stored_payload = json.loads(event.payload_json)
    assert stored_payload["password"] == "[REDACTED]"
    assert stored_payload["access_token"] == "[REDACTED]"
    assert stored_payload["course_title"] == "Web Development 101"


def test_emit_event_idempotency(app: Flask, student_user: User) -> None:
    """Test that reusing the same event_key returns existing event."""
    fixed_key = uuid.uuid4()
    ev1 = emit_event(
        event_type="SCORE_CHANGED",
        payload={"score": 9.5},
        event_key=fixed_key,
        session=db.session,
    )
    db.session.commit()

    ev2 = emit_event(
        event_type="SCORE_CHANGED",
        payload={"score": 9.5},
        event_key=fixed_key,
        session=db.session,
    )
    assert ev1.id == ev2.id
    assert ev1.event_key == ev2.event_key


def test_dispatch_notification_in_app_and_email(app: Flask, student_user: User) -> None:
    """Test dispatch creates in-app notification and queues email when preference enabled."""
    notif, email = dispatch_notification(
        recipient_user=student_user,
        event_type="COURSE_ANNOUNCEMENT",
        title="Welcome to the course",
        body="Class starts next Monday at 8 AM.",
        session=db.session,
    )
    db.session.commit()

    assert notif is not None
    assert notif.recipient_user_id == student_user.id
    assert notif.category == "COURSE"
    assert notif.title == "Welcome to the course"
    assert not notif.is_read

    assert email is not None
    assert email.recipient_email_snapshot == student_user.email
    assert email.status == "PENDING"


def test_dispatch_notification_respects_preferences(app: Flask, student_user: User) -> None:
    """Test that disabling optional category preference stops email from being queued."""
    # Explicitly disable COURSE emails
    update_user_preferences(
        actor=student_user,
        preferences_payload=[{"category": "COURSE", "email_enabled": False}],
        session=db.session,
    )
    db.session.commit()

    notif, email = dispatch_notification(
        recipient_user=student_user,
        event_type="COURSE_ANNOUNCEMENT",
        title="Course update",
        body="New lesson uploaded.",
        session=db.session,
    )
    db.session.commit()

    assert notif is not None
    # Email should be None because user opted out of COURSE emails
    assert email is None


def test_dispatch_mandatory_security_notification_forces_email(
    app: Flask, student_user: User
) -> None:
    """Test that security notifications cannot be suppressed and always queue an email."""
    notif, email = dispatch_notification(
        recipient_user=student_user,
        event_type="SECURITY_PASSWORD_CHANGED",
        title="Your password was changed",
        body="If you did not make this change, contact support immediately.",
        session=db.session,
    )
    db.session.commit()

    assert notif is not None
    assert notif.category == "SECURITY"
    assert email is not None
    assert email.status == "PENDING"


def test_update_user_preferences_rejects_security_opt_out(app: Flask, student_user: User) -> None:
    """Test that attempting to disable SECURITY category raises MandatoryNotificationOptOutError."""
    with pytest.raises(MandatoryNotificationOptOutError) as exc_info:
        update_user_preferences(
            actor=student_user,
            preferences_payload=[{"category": "SECURITY", "email_enabled": False}],
            session=db.session,
        )
    assert "cannot be disabled" in str(exc_info.value).lower()


def test_update_user_preferences_invalid_category(app: Flask, student_user: User) -> None:
    """Test that updating invalid category raises NotificationPreferenceError."""
    with pytest.raises(NotificationPreferenceError):
        update_user_preferences(
            actor=student_user,
            preferences_payload=[{"category": "INVALID_CATEGORY", "email_enabled": True}],
            session=db.session,
        )


def test_read_tracking_and_unread_count(app: Flask, student_user: User) -> None:
    """Test unread count, marking single notification read, and marking all read."""
    assert get_unread_count(student_user, session=db.session) == 0

    # Create 3 notifications
    n1, _ = dispatch_notification(
        student_user, "COURSE_ANNOUNCEMENT", "Notice 1", "Body 1", session=db.session
    )
    n2, _ = dispatch_notification(
        student_user, "COURSE_ANNOUNCEMENT", "Notice 2", "Body 2", session=db.session
    )
    n3, _ = dispatch_notification(
        student_user, "ASSESSMENT_DUE", "Notice 3", "Body 3", session=db.session
    )
    db.session.commit()

    assert get_unread_count(student_user, session=db.session) == 3

    # Mark n1 as read
    res1 = mark_notification_as_read(student_user, n1.public_id, session=db.session)
    db.session.commit()
    assert res1["read"] is True
    assert get_unread_count(student_user, session=db.session) == 2

    # Mark all read
    marked_count = mark_all_as_read(student_user, session=db.session)
    db.session.commit()
    assert marked_count == 2
    assert get_unread_count(student_user, session=db.session) == 0


def test_dismiss_notification(app: Flask, student_user: User) -> None:
    """Test dismissing notification removes it from list."""
    n, _ = dispatch_notification(
        student_user, "COURSE_ANNOUNCEMENT", "To be dismissed", "Body", session=db.session
    )
    db.session.commit()

    items_before, total_before = list_user_notifications(student_user, session=db.session)
    assert total_before == 1

    dismiss_res = dismiss_notification(student_user, n.public_id, session=db.session)
    db.session.commit()
    assert dismiss_res["status"] == "dismissed"

    items_after, total_after = list_user_notifications(student_user, session=db.session)
    assert total_after == 0


def test_broadcast_system_notification(
    app: Flask, admin_user: User, student_user: User, setup_roles: dict[str, Role]
) -> None:
    """Test admin broadcasting notifications to all active users and role-targeted."""
    # Create another student
    s2 = register_user(
        f"student2_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Student Two"
    )
    assign_role_to_user(s2.id, "STUDENT")
    db.session.commit()

    # Non-admin cannot broadcast
    with pytest.raises(ForbiddenError):
        broadcast_system_notification(
            actor=student_user,
            title="Unauthorized Broadcast",
            body="Should fail",
            session=db.session,
        )

    # Admin broadcast to STUDENTS only
    count = broadcast_system_notification(
        actor=admin_user,
        title="Maintenance Tomorrow",
        body="Platform will undergo maintenance from 2am to 3am UTC.",
        target_role="STUDENT",
        session=db.session,
    )
    db.session.commit()

    assert count >= 2
    items_s1, _ = list_user_notifications(student_user, session=db.session)
    assert any(item["title"] == "Maintenance Tomorrow" for item in items_s1)
