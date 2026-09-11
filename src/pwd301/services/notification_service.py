"""Notification management and event fan-out service for PWD301.

Implements:
- Event emission with sanitized payload logging ('notification_events').
- Decoupled in-app notification dispatch and email queueing ('notifications', 'email_deliveries').
- Strict user-level isolation and IDOR prevention per ADR-002 (Zero PK Leakage).
- Mandatory security notification invariant (SECURITY events cannot be disabled).
- Fast unread counter for topbar badge polling.
- User notification preferences matrix with defaults.
- Admin system broadcast.
"""

from __future__ import annotations

import datetime
import html
import json
import logging
import uuid
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Session, scoped_session

from pwd301.extensions import db
from pwd301.models.identity import Role, User
from pwd301.models.notification_audit import (
    EmailDelivery,
    Notification,
    NotificationEvent,
    NotificationPreference,
)
from pwd301.models.types import utc_now
from pwd301.services.email_service import enqueue_email
from pwd301.services.exceptions import (
    ForbiddenError,
    MandatoryNotificationOptOutError,
    NotificationNotFoundError,
    NotificationPreferenceError,
    UserNotFoundError,
    ValidationError,
)

logger = logging.getLogger(__name__)

MANDATORY_SECURITY_EVENTS: set[str] = {
    "SECURITY_PASSWORD_CHANGED",
    "SECURITY_ACCOUNT_SUSPENDED",
    "SECURITY_LOGIN_ANOMALY",
    "ACCOUNT_SUSPENDED",
    "SYSTEM_SECURITY_ALERT",
}

VALID_NOTIFICATION_CATEGORIES: set[str] = {
    "SECURITY",
    "COURSE",
    "ASSESSMENT",
    "GRADE",
    "SYSTEM",
}

VALID_PREFERENCE_CATEGORIES: set[str] = {
    "COURSE",
    "ASSESSMENT",
    "GRADE",
    "MARKETING",
    "SECURITY",
}

DEFAULT_PREFERENCES: dict[str, bool] = {
    "SECURITY": True,
    "COURSE": True,
    "ASSESSMENT": True,
    "GRADE": True,
    "MARKETING": False,
}


def sanitize_text(text: str, max_length: int = 2000) -> str:
    """Sanitize user-provided text by HTML-escaping and trimming."""
    if not text:
        return ""
    escaped = html.escape(text.strip())
    return escaped[:max_length]


def sanitize_payload(payload: dict[str, Any] | None) -> str | None:
    """Sanitize and serialize event payload, redacting passwords/secrets."""
    if payload is None:
        return None
    sanitized: dict[str, Any] = {}
    forbidden_keys = {"password", "token", "secret", "raw_key", "password_hash", "access_token"}
    for k, v in payload.items():
        if any(fk in k.lower() for fk in forbidden_keys):
            sanitized[k] = "[REDACTED]"
        else:
            sanitized[k] = v
    return json.dumps(sanitized)


def determine_event_category(event_type: str) -> str:
    """Map event type to canonical notification category."""
    upper_event = event_type.upper()
    if upper_event.startswith("SECURITY_") or upper_event in MANDATORY_SECURITY_EVENTS:
        return "SECURITY"
    if upper_event.startswith("ASSESSMENT_"):
        return "ASSESSMENT"
    if upper_event in {
        "SCORE_CHANGED_AFTER_REGRADE",
        "ASSESSMENT_GRADED",
    } or upper_event.startswith("GRADE_"):
        return "GRADE"
    if upper_event.startswith("COURSE_") or upper_event in {"ROLE_CHANGED", "FILE_REJECTED"}:
        return "COURSE"
    if upper_event.startswith("MARKETING_"):
        return "MARKETING"
    return "SYSTEM"


def emit_event(
    event_type: str,
    payload: dict[str, Any] | None = None,
    actor_user_id: int | None = None,
    target_type: str | None = None,
    target_id: int | None = None,
    correlation_id: uuid.UUID | None = None,
    event_key: uuid.UUID | None = None,
    session: Session | scoped_session | None = None,
) -> NotificationEvent:
    """Persist a business notification event in 'notification_events'."""
    s = session or db.session
    if not event_type or not isinstance(event_type, str):
        raise ValidationError("Field 'event_type' is required.")

    if event_key is None:
        event_key = uuid.uuid4()
    else:
        existing = s.query(NotificationEvent).filter_by(event_key=event_key).first()
        if existing is not None:
            return existing

    payload_str = sanitize_payload(payload)
    event = NotificationEvent(
        event_key=event_key,
        event_type=event_type,
        actor_user_id=actor_user_id,
        target_type=target_type,
        target_id=target_id,
        correlation_id=correlation_id,
        payload_json=payload_str,
        created_at=utc_now(),
    )
    s.add(event)
    s.flush()
    return event


def dispatch_notification(
    recipient_user: User | int,
    event_type: str,
    title: str,
    body: str,
    action_url: str | None = None,
    category: str | None = None,
    force_email: bool = False,
    payload: dict[str, Any] | None = None,
    event: NotificationEvent | None = None,
    expires_at: datetime.datetime | None = None,
    session: Session | scoped_session | None = None,
) -> tuple[Notification, EmailDelivery | None]:
    """Dispatch in-app notification and outbox email for a recipient.

    - Verifies user exists.
    - Honors user preferences for optional categories.
    - Enforces mandatory email dispatch for SECURITY events.
    - Preserves outbox pattern: email enqueue failure does not rollback in-app notification.
    """
    s = session or db.session

    if isinstance(recipient_user, int):
        user = s.get(User, recipient_user)
        if user is None:
            raise UserNotFoundError(f"Recipient user with ID {recipient_user} not found.")
    elif isinstance(recipient_user, User):
        user = recipient_user
    else:
        raise ValidationError("Invalid recipient_user parameter.")

    clean_title = sanitize_text(title, max_length=250)
    clean_body = sanitize_text(body, max_length=2000)

    # Determine canonical category
    cat = (category or determine_event_category(event_type)).upper()
    # In-app notifications table accepts: SECURITY, COURSE, ASSESSMENT, GRADE, SYSTEM
    in_app_cat = cat if cat in VALID_NOTIFICATION_CATEGORIES else "SYSTEM"

    is_mandatory = (in_app_cat == "SECURITY") or (event_type in MANDATORY_SECURITY_EVENTS)

    # Ensure event exists
    if event is None:
        event = emit_event(
            event_type=event_type,
            payload=payload,
            target_type="USER",
            target_id=user.id,
            session=s,
        )

    # In-app notification creation (deduplicated by notification_event_id + recipient_user_id)
    existing_notif = (
        s.query(Notification)
        .filter_by(notification_event_id=event.id, recipient_user_id=user.id)
        .first()
    )
    if existing_notif is not None:
        notification = existing_notif
    else:
        notification = Notification(
            notification_event_id=event.id,
            recipient_user_id=user.id,
            category=in_app_cat,
            title=clean_title,
            body=clean_body,
            expires_at=expires_at,
            created_at=utc_now(),
        )
        s.add(notification)
        s.flush()

    # Determine email dispatch eligibility
    should_email = False
    if is_mandatory or force_email:
        should_email = True
    else:
        # Check user preferences
        pref_cat = cat if cat in VALID_PREFERENCE_CATEGORIES else "COURSE"
        pref = s.query(NotificationPreference).filter_by(user_id=user.id, category=pref_cat).first()
        if pref is not None:
            should_email = pref.email_enabled
        else:
            should_email = DEFAULT_PREFERENCES.get(pref_cat, True)

    email_delivery: EmailDelivery | None = None
    if should_email and user.email:
        try:
            email_delivery = enqueue_email(
                recipient_email=user.email,
                subject=clean_title,
                body_text=clean_body,
                template_code=event_type,
                notification_event_id=event.id,
                recipient_user_id=user.id,
                session=s,
            )
        except Exception as exc:
            logger.warning(
                "Email queueing failed for event %s, recipient %s: %s",
                event.id,
                user.email,
                exc,
            )

    return notification, email_delivery


def list_user_notifications(
    actor: User,
    status: str | None = None,
    unread_only: bool = False,
    category: str | None = None,
    page: int = 1,
    per_page: int = 20,
    session: Session | scoped_session | None = None,
) -> tuple[list[dict[str, Any]], int]:
    """Retrieve paginated notifications for the authenticated user only (IDOR-safe)."""
    s = session or db.session
    if not actor:
        raise ForbiddenError("Actor context required.")

    query = s.query(Notification).filter(Notification.recipient_user_id == actor.id)

    if unread_only or (status and status.lower() == "unread"):
        query = query.filter(Notification.read_at.is_(None))
    elif status and status.lower() == "read":
        query = query.filter(Notification.read_at.is_not(None))

    if category:
        query = query.filter(Notification.category == category.upper())

    total = query.count()

    safe_page = max(1, page)
    safe_per_page = min(max(1, per_page), 100)
    offset = (safe_page - 1) * safe_per_page

    items = (
        query.order_by(Notification.created_at.desc(), Notification.id.desc())
        .offset(offset)
        .limit(safe_per_page)
        .all()
    )

    return [item.to_dict() for item in items], total


def get_unread_count(
    actor: User,
    session: Session | scoped_session | None = None,
) -> int:
    """Get count of unread notifications for fast topbar badge polling."""
    s = session or db.session
    if not actor:
        return 0

    count = (
        s.query(sa.func.count(Notification.id))
        .filter(
            Notification.recipient_user_id == actor.id,
            Notification.read_at.is_(None),
        )
        .scalar()
    )
    return count or 0


def mark_notification_as_read(
    actor: User,
    notification_id: str | uuid.UUID,
    session: Session | scoped_session | None = None,
) -> dict[str, Any]:
    """Mark a single notification as read, enforcing strict ownership."""
    s = session or db.session
    if not actor:
        raise ForbiddenError("Actor context required.")

    try:
        pub_id = uuid.UUID(str(notification_id))
    except ValueError:
        raise NotificationNotFoundError(f"Notification '{notification_id}' not found.") from None

    notification = s.query(Notification).filter_by(public_id=pub_id).first()
    if notification is None:
        raise NotificationNotFoundError(f"Notification '{notification_id}' not found.")

    if notification.recipient_user_id != actor.id:
        raise ForbiddenError("You are not authorized to modify this notification.")

    if notification.read_at is None:
        notification.read_at = utc_now()
        try:
            s.commit()
        except Exception:
            s.rollback()
            raise

    return notification.to_dict()


def mark_all_as_read(
    actor: User,
    category: str | None = None,
    session: Session | scoped_session | None = None,
) -> int:
    """Mark all unread notifications of the current actor as read."""
    s = session or db.session
    if not actor:
        raise ForbiddenError("Actor context required.")

    query = s.query(Notification).filter(
        Notification.recipient_user_id == actor.id,
        Notification.read_at.is_(None),
    )
    if category:
        query = query.filter(Notification.category == category.upper())

    unread_notifications = query.all()
    now = utc_now()
    count = 0
    for notif in unread_notifications:
        notif.read_at = now
        count += 1

    try:
        s.commit()
    except Exception:
        s.rollback()
        raise
    return count


def dismiss_notification(
    actor: User,
    notification_id: str | uuid.UUID,
    session: Session | scoped_session | None = None,
) -> dict[str, Any]:
    """Dismiss or delete a notification, enforcing strict ownership."""
    s = session or db.session
    if not actor:
        raise ForbiddenError("Actor context required.")

    try:
        pub_id = uuid.UUID(str(notification_id))
    except ValueError:
        raise NotificationNotFoundError(f"Notification '{notification_id}' not found.") from None

    notification = s.query(Notification).filter_by(public_id=pub_id).first()
    if notification is None:
        raise NotificationNotFoundError(f"Notification '{notification_id}' not found.")

    if notification.recipient_user_id != actor.id:
        raise ForbiddenError("You are not authorized to modify this notification.")

    s.delete(notification)
    try:
        s.commit()
    except Exception:
        s.rollback()
        raise
    return {"id": str(pub_id), "status": "dismissed"}


def get_user_preferences(
    actor: User,
    session: Session | scoped_session | None = None,
) -> list[dict[str, Any]]:
    """Retrieve full notification preferences matrix for user with defaults."""
    s = session or db.session
    if not actor:
        raise ForbiddenError("Actor context required.")

    user_prefs = {
        p.category: p.email_enabled
        for p in s.query(NotificationPreference).filter_by(user_id=actor.id).all()
    }

    result: list[dict[str, Any]] = []
    # Standard order of categories
    for cat in ["SECURITY", "COURSE", "ASSESSMENT", "GRADE", "MARKETING"]:
        enabled = user_prefs.get(cat, DEFAULT_PREFERENCES.get(cat, True))
        if cat == "SECURITY":
            enabled = True  # Invariant: Security cannot be disabled
        result.append(
            {
                "category": cat,
                "email_enabled": enabled,
                "is_mandatory": (cat == "SECURITY"),
            }
        )

    return result


def update_user_preferences(
    actor: User,
    preferences_payload: list[dict[str, Any]] | dict[str, Any],
    session: Session | scoped_session | None = None,
) -> list[dict[str, Any]]:
    """Update notification preferences, strictly rejecting opt-out for SECURITY alerts."""
    s = session or db.session
    if not actor:
        raise ForbiddenError("Actor context required.")

    items: list[dict[str, Any]] = []
    if isinstance(preferences_payload, dict):
        # Format: {"COURSE": True, "ASSESSMENT": False} or {"preferences": [...]}
        prefs_list = preferences_payload.get("preferences")
        if isinstance(prefs_list, list):
            items = prefs_list
        else:
            items = [{"category": k, "email_enabled": v} for k, v in preferences_payload.items()]
    elif isinstance(preferences_payload, list):
        items = preferences_payload
    else:
        raise NotificationPreferenceError("Preferences payload must be a list or object.")

    now = utc_now()
    for item in items:
        cat = item.get("category")
        if not cat or not isinstance(cat, str):
            raise NotificationPreferenceError("Field 'category' is required.")
        cat_upper = cat.upper()

        if cat_upper not in VALID_PREFERENCE_CATEGORIES:
            raise NotificationPreferenceError(
                f"Invalid category '{cat}'. Allowed: {sorted(VALID_PREFERENCE_CATEGORIES)}"
            )

        enabled = item.get("email_enabled")
        if enabled is None:
            raise NotificationPreferenceError(
                f"Field 'email_enabled' required for category '{cat}'."
            )
        bool_enabled = bool(enabled)

        # Mandatory security invariant
        if cat_upper == "SECURITY" and not bool_enabled:
            raise MandatoryNotificationOptOutError(
                "Security notifications are mandatory and cannot be disabled."
            )

        pref = (
            s.query(NotificationPreference).filter_by(user_id=actor.id, category=cat_upper).first()
        )
        if pref is None:
            pref = NotificationPreference(
                user_id=actor.id,
                category=cat_upper,
                email_enabled=bool_enabled,
                updated_at=now,
            )
            s.add(pref)
        else:
            pref.email_enabled = bool_enabled
            pref.updated_at = now

    try:
        s.commit()
    except Exception:
        s.rollback()
        raise
    return get_user_preferences(actor, session=s)


def broadcast_system_notification(
    actor: User,
    title: str,
    body: str,
    target_role: str | None = None,
    category: str = "SYSTEM",
    session: Session | scoped_session | None = None,
) -> int:
    """Privileged action: Admin broadcasts system notifications to all or role-targeted users."""
    s = session or db.session
    if not actor or not actor.is_admin:
        raise ForbiddenError("Only administrators can broadcast system notifications.")

    clean_title = sanitize_text(title, max_length=250)
    clean_body = sanitize_text(body, max_length=2000)
    cat = category.upper() if category.upper() in VALID_NOTIFICATION_CATEGORIES else "SYSTEM"

    event = emit_event(
        event_type="SYSTEM_BROADCAST",
        payload={"title": clean_title, "target_role": target_role},
        actor_user_id=actor.id,
        target_type="SYSTEM",
        session=s,
    )

    query = s.query(User).filter(User.status == "ACTIVE", User.suspended_at.is_(None))
    if target_role:
        query = query.join(User.roles).filter(Role.code == target_role.upper())

    target_users = query.all()
    count = 0
    now = utc_now()
    for user in target_users:
        notif = Notification(
            notification_event_id=event.id,
            recipient_user_id=user.id,
            category=cat,
            title=clean_title,
            body=clean_body,
            created_at=now,
        )
        s.add(notif)
        count += 1

    try:
        s.commit()
    except Exception:
        s.rollback()
        raise
    return count
