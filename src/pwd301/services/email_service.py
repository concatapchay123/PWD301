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
import json
import logging
import os
import re
import smtplib
import ssl
import urllib.error
import urllib.request
import uuid
from email.message import EmailMessage
from typing import Any

import sqlalchemy as sa
from flask import current_app, has_app_context
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


class UnconfiguredMailClient(BaseMailClient):
    """Fail-closed transport used when production SMTP settings are absent."""

    def __init__(self, reason: str) -> None:
        self.reason = reason

    def send(
        self,
        recipient_email: str,
        subject: str,
        body_text: str,
        body_html: str | None = None,
    ) -> None:
        raise EmailDeliveryError(f"Email transport is not configured: {self.reason}")


class SmtpMailClient(BaseMailClient):
    """Small standard-library SMTP adapter for the durable email worker."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str | None,
        password: str | None,
        use_tls: bool,
        from_email: str,
        timeout_seconds: float = 10.0,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.from_email = from_email
        self.timeout_seconds = timeout_seconds

    def send(
        self,
        recipient_email: str,
        subject: str,
        body_text: str,
        body_html: str | None = None,
    ) -> None:
        message = EmailMessage()
        message["From"] = self.from_email
        message["To"] = recipient_email
        message["Subject"] = subject
        message.set_content(body_text)
        if body_html:
            message.add_alternative(body_html, subtype="html")

        with smtplib.SMTP(self.host, self.port, timeout=self.timeout_seconds) as smtp:
            if self.use_tls:
                smtp.starttls(context=ssl.create_default_context())
            if self.username:
                smtp.login(self.username, self.password or "")
            smtp.send_message(message)


class ResendMailClient(BaseMailClient):
    """Direct HTTPS client for Resend REST API (faster, bypasses SMTP port blocking)."""

    def __init__(
        self,
        api_key: str,
        from_email: str,
        timeout_seconds: float = 10.0,
    ) -> None:
        self.api_key = api_key
        self.from_email = from_email
        self.timeout_seconds = timeout_seconds

    def send(
        self,
        recipient_email: str,
        subject: str,
        body_text: str,
        body_html: str | None = None,
    ) -> None:
        payload: dict[str, Any] = {
            "from": self.from_email,
            "to": [recipient_email],
            "subject": subject,
            "text": body_text,
        }
        if body_html:
            payload["html"] = body_html

        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "resend-python/2.0.0",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                if resp.status not in (200, 201):
                    raise EmailDeliveryError(f"Resend API returned unexpected status {resp.status}")
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="ignore")
            logger.error("Resend API HTTP error: %s %s", exc.code, err_body)
            raise EmailDeliveryError(f"Resend API error: {exc.code} {err_body}") from exc
        except Exception as exc:
            logger.error("Resend API network error: %s", exc)
            raise EmailDeliveryError(f"Resend network error: {exc}") from exc


_default_mail_client: BaseMailClient | None = None


def _mail_setting(name: str, default: Any = None) -> Any:
    """Read an optional mail setting from Flask config, then the environment."""
    if has_app_context():
        configured = current_app.config.get(name)
        if configured not in (None, ""):
            return configured
    return os.environ.get(name, default)


def _mail_bool(value: Any, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def get_default_mail_client() -> BaseMailClient:
    """Get the configured mail transport, using a mock only in testing."""
    if _default_mail_client is not None:
        return _default_mail_client

    if has_app_context() and current_app.config.get("TESTING", False):
        return MockMailClient()

    from_email = (
        str(_mail_setting("MAIL_FROM", "")).strip() or "Hệ thống PPTQ <noreply@pptq.id.vn>"
    )

    # Prioritize Resend API Key if present
    resend_api_key = str(_mail_setting("RESEND_API_KEY", "")).strip() or None
    if resend_api_key:
        return ResendMailClient(
            api_key=resend_api_key,
            from_email=from_email,
        )

    host = str(_mail_setting("MAIL_HOST", "")).strip()
    username = str(_mail_setting("MAIL_USERNAME", "")).strip() or None
    password = _mail_setting("MAIL_PASSWORD")
    if not host or not from_email:
        return UnconfiguredMailClient("MAIL_HOST and MAIL_FROM (or RESEND_API_KEY) are required")

    try:
        port = int(_mail_setting("MAIL_PORT", 587))
    except (TypeError, ValueError):
        return UnconfiguredMailClient("MAIL_PORT must be an integer")

    return SmtpMailClient(
        host=host,
        port=port,
        username=username,
        password=str(password) if password is not None else None,
        use_tls=_mail_bool(_mail_setting("MAIL_USE_TLS", True), default=True),
        from_email=from_email,
    )


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
    from pwd301.services.rate_limit_service import check_email_rate_limit

    check_email_rate_limit(clean_email)

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
        subject=subject[:250] if subject else None,
        body_text=body_text,
        dedupe_key=dedupe_key,
        status="PENDING",
        attempt_count=0,
        next_attempt_at=utc_now(),
        created_at=utc_now(),
    )
    s.add(delivery)
    try:
        with s.begin_nested():
            s.flush()
    except sa.exc.IntegrityError:
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

    sub = subject or delivery.subject or f"PWD301 Notification: {delivery.template_code}"
    body = (
        body_text or delivery.body_text or f"You have a notification for {delivery.template_code}."
    )

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
        delivery.last_error = str(exc)[:1900]

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


def send_verification_email(
    user: User,
    token: str,
    frontend_url: str | None = None,
    session: Session | scoped_session | None = None,
) -> EmailDelivery:
    """Compose and send account verification email with branded HTML template.

    Enqueues to durable outbox and dispatches immediately for instant delivery.
    """
    s = session or db.session
    base_url = (frontend_url or str(_mail_setting("FRONTEND_URL", "https://pptq.id.vn"))).rstrip("/")
    verify_url = f"{base_url}/#/auth/verify-email?token={token}"

    display_name = getattr(user, "display_name", "") or (user.email.split("@")[0] if user.email else "Học viên")
    subject = "Xác thực tài khoản PPTQ"

    body_text = f"""Xin chào {display_name},

Cảm ơn bạn đã đăng ký tài khoản trên Hệ thống Đào tạo & Khảo thí Trực tuyến PPTQ.

Để kích hoạt và bắt đầu sử dụng tài khoản của bạn, vui lòng truy cập liên kết xác thực sau (có hiệu lực trong vòng 24 giờ):
{verify_url}

Nếu bạn không thực hiện yêu cầu này, vui lòng bỏ qua email này.

Trân trọng,
Ban Quản trị PPTQ
https://pptq.id.vn
"""

    body_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{subject}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f4f5f7; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f5f7; padding: 36px 12px;">
    <tr>
      <td align="center">
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 540px; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06); border: 1px solid #e2e8f0;">
          <!-- Header -->
          <tr>
            <td style="background-color: #047857; padding: 28px 32px; text-align: center;">
              <h1 style="margin: 0; color: #ffffff; font-size: 22px; font-weight: 700; letter-spacing: 0.5px;">HỆ THỐNG ĐÀO TẠO PPTQ</h1>
              <p style="margin: 4px 0 0 0; color: #a7f3d0; font-size: 13px;">Xác thực tài khoản học viên</p>
            </td>
          </tr>
          <!-- Content -->
          <tr>
            <td style="padding: 32px 32px 24px 32px;">
              <p style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">
                Xin chào <strong>{display_name}</strong>,
              </p>
              <p style="margin: 0 0 20px 0; font-size: 14px; line-height: 1.6; color: #475569;">
                Cảm ơn bạn đã đăng ký tài khoản trên nền tảng PPTQ. Để bảo mật thông tin và hoàn tất quá trình đăng ký, vui lòng nhấn vào nút bên dưới để xác thực địa chỉ email của bạn:
              </p>
              <div style="text-align: center; margin: 30px 0;">
                <a href="{verify_url}" target="_blank" style="display: inline-block; background-color: #059669; color: #ffffff; text-decoration: none; font-size: 15px; font-weight: 600; padding: 14px 32px; border-radius: 8px; box-shadow: 0 2px 8px rgba(5, 150, 105, 0.35);">
                  Xác nhận kích hoạt tài khoản
                </a>
              </div>
              <p style="margin: 24px 0 8px 0; font-size: 13px; line-height: 1.5; color: #64748b;">
                Liên kết này có hiệu lực trong vòng <strong>24 giờ</strong>. Nếu nút bấm trên không hoạt động, bạn có thể sao chép liên kết sau và dán vào thanh địa chỉ trình duyệt:
              </p>
              <p style="margin: 0 0 20px 0; font-size: 12px; line-height: 1.5; word-break: break-all; color: #0284c7; background: #f8fafc; padding: 10px; border-radius: 6px; border: 1px dashed #cbd5e1;">
                {verify_url}
              </p>
              <p style="margin: 0; font-size: 12px; line-height: 1.5; color: #94a3b8;">
                Nếu bạn không thực hiện đăng ký trên hệ thống PPTQ, bạn hoàn toàn có thể bỏ qua thư này một cách an toàn.
              </p>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="background-color: #f8fafc; padding: 20px 32px; border-top: 1px solid #e2e8f0; text-align: center;">
              <p style="margin: 0; font-size: 12px; color: #94a3b8;">
                © 2026 PPTQ Educational Platform. Mọi quyền được bảo lưu.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    delivery = enqueue_email(
        recipient_email=user.email,
        subject=subject,
        body_text=body_text,
        template_code="EMAIL_VERIFY",
        recipient_user_id=user.id,
        session=s,
    )

    # Attempt immediate synchronous dispatch with fail-safe fallback
    try:
        send_single_email(
            delivery=delivery,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            session=s,
        )
    except Exception as exc:
        logger.warning(
            "Immediate email dispatch failed for user %s: %s (will be retried by worker)",
            user.id,
            exc,
        )

    return delivery
