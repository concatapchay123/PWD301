"""Email delivery and retry service for PWD301.

Implements:
- Outbox pattern: Email deliveries persisted to 'email_deliveries' with status='PENDING'.
- Decoupled dispatch: Business transactions do not rollback on external mail transport failures.
- Delivery idempotency: Deduplication via unique constraints and dedupe_key.
- Exponential backoff: Retry delay calculated as 2^(attempt_count) * 60 seconds.
- Terminal failure handling: Transitions to status='FAILED' when max_retries exceeded.
- Queue processing: Batch scanning and worker dispatch.
- Admin retry: Privileged reset of failed email deliveries.
"""

from __future__ import annotations

import datetime
import logging
import re
import uuid
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Session, scoped_session

from pwd301.extensions import db
from pwd301.models.identity import User
from pwd301.models.notification_audit import EmailDelivery
from pwd301.models.types import utc_now
from pwd301.services.exceptions import (
    EmailDeliveryError,
    ForbiddenError,
    InvalidEmailError,
)

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class BaseMailClient:
    """Base interface for email transport clients."""

    def send(
        self,
        recipient_email: str,
        subject: str,
        body_text: str,
        body_html: str | None = None,
    ) -> None:
        """Send an email message. Raise an exception on failure."""
        raise NotImplementedError


class MockMailClient(BaseMailClient):
    """In-memory mail transport client for testing and local development."""

    def __init__(
        self,
        should_fail: bool = False,
        fail_message: str = "SMTP Connection Refused",
    ) -> None:
        self.sent_messages: list[dict[str, Any]] = []
        self.should_fail = should_fail
        self.fail_message = fail_message

    def send(
        self,
        recipient_email: str,
        subject: str,
        body_text: str,
        body_html: str | None = None,
    ) -> None:
        if self.should_fail:
            raise RuntimeError(self.fail_message)
        self.sent_messages.append(
            {
                "recipient_email": recipient_email,
                "subject": subject,
                "body_text": body_text,
                "body_html": body_html,
                "sent_at": utc_now(),
            }
        )


_default_mail_client: BaseMailClient = MockMailClient()


def get_default_mail_client() -> BaseMailClient:
    """Get the active mail transport client."""
    return _default_mail_client


def set_default_mail_client(client: BaseMailClient) -> None:
    """Set the active mail transport client (useful in testing)."""
    global _default_mail_client
    _default_mail_client = client


def validate_email_syntax(email: str) -> str:
    """Validate recipient email address syntax."""
    if not email or not isinstance(email, str):
        raise InvalidEmailError("Email address cannot be empty.")
    normalized = email.strip().lower()
    if not EMAIL_REGEX.match(normalized):
        raise InvalidEmailError(f"Invalid email address syntax: '{email}'.")
    return normalized


def enqueue_email(
    recipient_email: str,
    subject: str,
    body_text: str,
    body_html: str | None = None,
    template_code: str = "GENERIC",
    notification_event_id: int | None = None,
    recipient_user_id: int | None = None,
    dedupe_key: uuid.UUID | None = None,
    session: Session | scoped_session | None = None,
) -> EmailDelivery:
    """Enqueue an outbound email record to 'email_deliveries' in PENDING status.

    Conforms to the outbox pattern so primary business actions are decoupled from
    mail delivery failures.
    """
    s = session or db.session
    clean_email = validate_email_syntax(recipient_email)

    if dedupe_key is None:
        dedupe_key = uuid.uuid4()

    # Ensure notification_event_id is populated (satisfies NOT NULL foreign key constraint)
    if notification_event_id is None:
        from pwd301.services.notification_service import emit_event

        event = emit_event(
            event_type=template_code,
            payload={"subject": subject},
            actor_user_id=recipient_user_id,
            target_type="EMAIL",
            session=s,
        )
        notification_event_id = event.id

    # If notification_event_id is provided, check for existing delivery to ensure idempotency
    existing = (
        s.query(EmailDelivery)
        .filter_by(
            notification_event_id=notification_event_id,
            recipient_email_snapshot=clean_email,
            template_code=template_code,
        )
        .first()
    )
    if existing is not None:
        return existing

    # Check dedupe_key uniqueness
    existing_dedupe = s.query(EmailDelivery).filter_by(dedupe_key=dedupe_key).first()
    if existing_dedupe is not None:
        return existing_dedupe

    delivery = EmailDelivery(
        notification_event_id=notification_event_id,
        recipient_user_id=recipient_user_id,
        recipient_email_snapshot=clean_email,
        template_code=template_code,
        dedupe_key=dedupe_key,
        status="PENDING",
        attempt_count=0,
        next_attempt_at=utc_now(),
        created_at=utc_now(),
    )
    s.add(delivery)
    try:
        s.flush()
    except sa.exc.IntegrityError:
        s.rollback()
        # Retrieve already persisted row if concurrent insert raced
        fallback = s.query(EmailDelivery).filter_by(dedupe_key=dedupe_key).first()
        if fallback is not None:
            return fallback
        raise EmailDeliveryError("Failed to enqueue email due to integrity conflict.") from None

    return delivery


def send_single_email(
    delivery: EmailDelivery,
    mail_client: BaseMailClient | None = None,
    max_retries: int = 3,
    subject: str | None = None,
    body_text: str | None = None,
    body_html: str | None = None,
    session: Session | scoped_session | None = None,
) -> bool:
    """Attempt to send a single email delivery.

    On success: status='SENT', sent_at=utc_now().
    On failure: increments attempt_count, calculates exponential backoff:
      next_attempt_at = utc_now() + 2^(attempt_count) * 60 seconds.
      If attempt_count >= max_retries, transitions status to 'FAILED'.
    """
    s = session or db.session
    client = mail_client or get_default_mail_client()

    delivery.status = "SENDING"
    s.flush()

    sub = subject or f"PWD301 Notification: {delivery.template_code}"
    body = body_text or f"You have a notification for {delivery.template_code}."

    try:
        client.send(
            recipient_email=delivery.recipient_email_snapshot,
            subject=sub,
            body_text=body,
            body_html=body_html,
        )
        delivery.status = "SENT"
        delivery.sent_at = utc_now()
        delivery.last_error = None
        delivery.next_attempt_at = None
        s.flush()
        return True
    except Exception as exc:
        delivery.attempt_count += 1
        delivery.last_error = str(exc)[:2000]

        if delivery.attempt_count >= max_retries:
            delivery.status = "FAILED"
            delivery.next_attempt_at = None
            logger.warning(
                "Email delivery %s reached max retries (%d). Marked FAILED. Error: %s",
                delivery.public_id,
                max_retries,
                delivery.last_error,
            )
        else:
            delivery.status = "PENDING"
            # Exponential backoff: 2^(attempt_count) * 60 seconds
            delay_seconds = (2**delivery.attempt_count) * 60
            delivery.next_attempt_at = utc_now() + datetime.timedelta(seconds=delay_seconds)
            logger.info(
                "Email delivery %s failed attempt %d. Next retry in %d seconds.",
                delivery.public_id,
                delivery.attempt_count,
                delay_seconds,
            )

        s.flush()
        return False


def process_email_queue(
    batch_size: int = 50,
    max_retries: int = 3,
    mail_client: BaseMailClient | None = None,
    session: Session | scoped_session | None = None,
) -> dict[str, int]:
    """Scan for due PENDING email deliveries and attempt sending them."""
    s = session or db.session
    now = utc_now()

    # Query pending deliveries where next_attempt_at is due
    due_deliveries = (
        s.query(EmailDelivery)
        .filter(
            EmailDelivery.status == "PENDING",
            sa.or_(
                EmailDelivery.next_attempt_at.is_(None),
                EmailDelivery.next_attempt_at <= now,
            ),
        )
        .order_by(EmailDelivery.created_at.asc(), EmailDelivery.id.asc())
        .limit(batch_size)
        .all()
    )

    processed = 0
    succeeded = 0
    failed = 0

    for delivery in due_deliveries:
        processed += 1
        success = send_single_email(
            delivery=delivery,
            mail_client=mail_client,
            max_retries=max_retries,
            session=s,
        )
        if success:
            succeeded += 1
        else:
            failed += 1

    return {
        "processed": processed,
        "succeeded": succeeded,
        "failed": failed,
    }


def retry_failed_emails(
    actor: User,
    max_emails: int = 50,
    session: Session | scoped_session | None = None,
) -> int:
    """Privileged action: Admin resets failed email deliveries back to PENDING status."""
    if not actor or not actor.is_admin:
        raise ForbiddenError("Only administrators can retry failed emails.")

    s = session or db.session

    failed_deliveries = (
        s.query(EmailDelivery)
        .filter(EmailDelivery.status == "FAILED")
        .order_by(EmailDelivery.created_at.desc(), EmailDelivery.id.desc())
        .limit(max_emails)
        .all()
    )

    now = utc_now()
    count = 0
    for delivery in failed_deliveries:
        delivery.status = "PENDING"
        delivery.attempt_count = 0
        delivery.next_attempt_at = now
        delivery.last_error = None
        count += 1

    s.flush()
    try:
        s.commit()
    except Exception:
        s.rollback()
        raise
    return count
