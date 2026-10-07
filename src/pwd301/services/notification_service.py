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
import re
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
    ConflictError,
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
    "SYSTEM",
}

DEFAULT_PREFERENCES: dict[str, bool] = {
    "SECURITY": True,
    "COURSE": True,
    "ASSESSMENT": True,
    "GRADE": True,
    "MARKETING": False,
    "SYSTEM": True,
}


def sanitize_text(text: str, max_length: int = 2000) -> str:
    """Sanitize user-provided text by HTML-escaping and trimming."""
    if not text:
        return ""
    escaped = html.escape(str(text).strip())
    return escaped[:max_length]


_RAW_IPV4_PATTERN = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])")


def redact_network_telemetry(text: str) -> str:
    """Hide raw IPv4 values from user-facing security notifications."""
    return _RAW_IPV4_PATTERN.sub("[REDACTED]", text)


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

    payload_str = sanitize_payload(payload)
    if event_key is None:
        event_key = uuid.uuid4()
    else:
        existing = s.query(NotificationEvent).filter_by(event_key=event_key).first()
        if existing is not None:
            try:
                existing_payload = json.loads(existing.payload_json or "null")
                requested_payload = json.loads(payload_str or "null")
            except (TypeError, ValueError):
                existing_payload = existing.payload_json
                requested_payload = payload_str
            if (
                existing.event_type != event_type
                or existing.actor_user_id != actor_user_id
                or existing.target_type != target_type
                or existing.target_id != target_id
                or existing_payload != requested_payload
            ):
                raise ConflictError("Event idempotency key was already used with different data.")
            return existing

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
    target_role: str | None = None,
    force_email: bool = False,
    payload: dict[str, Any] | None = None,
    event: NotificationEvent | None = None,
    expires_at: datetime.datetime | None = None,
    session: Session | scoped_session | None = None,
    event_key: uuid.UUID | None = None,
) -> tuple[Notification, EmailDelivery | None]:
    """Dispatch in-app notification and outbox email for a recipient.

    - Verifies user exists.
    - Honors user preferences for optional categories.
    - Enforces mandatory email dispatch for SECURITY events.
    - Sets target_role for precise role-scoped delivery.
    - Reuses a supplied event_key across producer retries.
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
    if is_mandatory:
        clean_title = redact_network_telemetry(clean_title)
        clean_body = redact_network_telemetry(clean_body)

    # Ensure event exists
    if event is None:
        event_payload = dict(payload) if payload else {}
        if action_url and "action_url" not in event_payload:
            event_payload["action_url"] = action_url
        if event_key is not None:
            event_payload["_dispatch_contract"] = {
                "title": clean_title,
                "body": clean_body,
                "category": in_app_cat,
                "target_role": target_role.strip().upper() if target_role else None,
                "force_email": bool(force_email),
            }
        if is_mandatory:
            for key in ("action_url", "target_url"):
                value = event_payload.get(key)
                if isinstance(value, str):
                    event_payload[key] = redact_network_telemetry(value)
        event = emit_event(
            event_type=event_type,
            payload=event_payload if event_payload else None,
            target_type="USER",
            target_id=user.id,
            event_key=event_key,
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
        if target_role and not notification.target_role:
            notification.target_role = target_role.strip().upper()
    else:
        notification = Notification(
            notification_event_id=event.id,
            recipient_user_id=user.id,
            target_role=target_role.strip().upper() if target_role else None,
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


def _visible_notification_query(
    session: Session | scoped_session,
    recipient_id: int,
    target_role: str | None = None,
) -> Any:
    """Return every non-expired event for the recipient.

    Distinct business events may legitimately share title/body copy. Retry
    deduplication belongs at the producer's idempotency boundary, not in a
    presentation query that hides durable records from the recipient.
    Optionally scope the result by target_role.
    """
    query = (
        session.query(Notification)
        .join(NotificationEvent, Notification.notification_event_id == NotificationEvent.id)
        .filter(
            Notification.recipient_user_id == recipient_id,
            sa.or_(Notification.expires_at.is_(None), Notification.expires_at > utc_now()),
        )
    )
    if target_role:
        upper_role = target_role.strip().upper()
        query = query.filter(
            sa.or_(Notification.target_role == upper_role, Notification.target_role.is_(None))
        )
    return query


def list_user_notifications(
    actor: User,
    status: str | None = None,
    unread_only: bool = False,
    category: str | None = None,
    target_role: str | None = None,
    page: int = 1,
    per_page: int = 20,
    session: Session | scoped_session | None = None,
) -> tuple[list[dict[str, Any]], int]:
    """Retrieve paginated notifications for the authenticated user only (IDOR-safe)."""
    s = session or db.session
    if not actor:
        raise ForbiddenError("Actor context required.")

    query = _visible_notification_query(s, actor.id, target_role=target_role)

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
        query.options(sa.orm.joinedload(Notification.event))
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .offset(offset)
        .limit(safe_per_page)
        .all()
    )

    return [item.to_dict() for item in items], total


def get_unread_count(
    actor: User,
    target_role: str | None = None,
    session: Session | scoped_session | None = None,
) -> int:
    """Get count of unread notifications for fast topbar badge polling."""
    s = session or db.session
    if not actor:
        return 0

    count = (
        _visible_notification_query(s, actor.id, target_role=target_role)
        .filter(Notification.read_at.is_(None))
        .count()
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

    notification = (
        s.query(Notification)
        .filter(
            Notification.public_id == pub_id,
            sa.or_(Notification.expires_at.is_(None), Notification.expires_at > utc_now()),
        )
        .first()
    )
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
    target_role: str | None = None,
    session: Session | scoped_session | None = None,
) -> int:
    """Mark all unread notifications of the current actor as read."""
    s = session or db.session
    if not actor:
        raise ForbiddenError("Actor context required.")

    query = s.query(Notification).filter(
        Notification.recipient_user_id == actor.id,
        Notification.read_at.is_(None),
        sa.or_(Notification.expires_at.is_(None), Notification.expires_at > utc_now()),
    )
    if target_role:
        upper_role = target_role.strip().upper()
        query = query.filter(
            sa.or_(Notification.target_role == upper_role, Notification.target_role.is_(None))
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
    """Soft delete a notification, enforcing strict ownership."""
    s = session or db.session
    if not actor:
        raise ForbiddenError("Actor context required.")

    try:
        pub_id = uuid.UUID(str(notification_id))
    except ValueError:
        raise NotificationNotFoundError(f"Notification '{notification_id}' not found.") from None

    notification = (
        s.query(Notification)
        .filter(
            Notification.public_id == pub_id,
            sa.or_(Notification.expires_at.is_(None), Notification.expires_at > utc_now()),
        )
        .first()
    )
    if notification is None:
        raise NotificationNotFoundError(f"Notification '{notification_id}' not found.")

    if notification.recipient_user_id != actor.id:
        raise ForbiddenError("You are not authorized to modify this notification.")

    notification.expires_at = utc_now()
    try:
        s.commit()
    except Exception:
        s.rollback()
        raise
    return {"id": str(pub_id), "status": "dismissed"}


def delete_all_notifications(
    actor: User,
    target_role: str | None = None,
    session: Session | scoped_session | None = None,
) -> int:
    """Soft delete all notifications for actor, optionally scoped to a target role."""
    s = session or db.session
    if not actor:
        raise ForbiddenError("Actor context required.")

    query = s.query(Notification).filter(
        Notification.recipient_user_id == actor.id,
        sa.or_(Notification.expires_at.is_(None), Notification.expires_at > utc_now()),
    )
    if target_role:
        upper_role = target_role.strip().upper()
        query = query.filter(
            sa.or_(Notification.target_role == upper_role, Notification.target_role.is_(None))
        )

    now = utc_now()
    count = 0
    for notif in query.all():
        notif.expires_at = now
        count += 1

    try:
        s.commit()
    except Exception:
        s.rollback()
        raise
    return count


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
    idempotency_key: uuid.UUID | str | None = None,
    session: Session | scoped_session | None = None,
) -> tuple[int, bool]:
    """Broadcast once per idempotency key and fan out to the selected audience.

    The key is optional for backward compatibility with internal callers. When supplied,
    an exact replay returns the original fan-out count without creating another event or
    notification row; a changed payload with the same key is a conflict.
    """
    s = session or db.session
    if not actor or not actor.is_admin:
        raise ForbiddenError("Only administrators can broadcast system notifications.")

    clean_title = sanitize_text(title, max_length=250)
    clean_body = sanitize_text(body, max_length=2000)
    cat = category.upper() if category.upper() in VALID_NOTIFICATION_CATEGORIES else "SYSTEM"
    clean_target_role = target_role.strip().upper() if target_role else None

    normalized_key: uuid.UUID | None = None
    if idempotency_key is not None:
        try:
            normalized_key = (
                idempotency_key
                if isinstance(idempotency_key, uuid.UUID)
                else uuid.UUID(str(idempotency_key).strip())
            )
        except (AttributeError, ValueError):
            raise ValidationError("X-Idempotency-Key must be a valid UUID.") from None

    broadcast_payload = {
        "title": clean_title,
        "body": clean_body,
        "target_role": clean_target_role,
        "category": cat,
    }

    def replay_existing_event(existing_event: NotificationEvent) -> tuple[int, bool]:
        if (
            existing_event.event_type != "SYSTEM_BROADCAST"
            or existing_event.actor_user_id != actor.id
        ):
            raise ConflictError("X-Idempotency-Key is already used by another operation.")
        try:
            existing_payload = json.loads(existing_event.payload_json or "{}")
        except (TypeError, ValueError):
            existing_payload = None
        if existing_payload != broadcast_payload:
            raise ConflictError("X-Idempotency-Key was already used with different data.")
        existing_count = (
            s.query(Notification).filter_by(notification_event_id=existing_event.id).count()
        )
        return existing_count, True

    if normalized_key is not None:
        existing_event = s.query(NotificationEvent).filter_by(event_key=normalized_key).first()
        if existing_event is not None:
            return replay_existing_event(existing_event)

    try:
        event = emit_event(
            event_type="SYSTEM_BROADCAST",
            payload=broadcast_payload,
            actor_user_id=actor.id,
            target_type="SYSTEM",
            event_key=normalized_key,
            session=s,
        )
    except sa.exc.IntegrityError:
        if normalized_key is None:
            raise
        s.rollback()
        raced_event = s.query(NotificationEvent).filter_by(event_key=normalized_key).first()
        if raced_event is None:
            raise
        return replay_existing_event(raced_event)

    query = s.query(User).filter(User.status == "ACTIVE", User.suspended_at.is_(None))
    if clean_target_role:
        query = query.join(User.roles).filter(Role.code == clean_target_role)

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
    return count, False
