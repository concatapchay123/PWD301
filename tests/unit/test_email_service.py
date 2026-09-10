"""Unit test suite for Email Delivery and Retry Service (TASK-021).

Tests:
- Email queueing with outbox pattern ('PENDING' state).
- Deduplication and idempotency on duplicate enqueue.
- Send success transitions to 'SENT' with sent_at timestamp.
- Transient failure with exponential backoff delay calculation.
- Terminal failure transitions to 'FAILED' when max_retries exceeded.
- Batch queue processing.
- Admin retry of failed deliveries.
"""

from __future__ import annotations

import datetime
import uuid

import pytest
from flask import Flask
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.identity import Role, User
from pwd301.models.types import utc_now
from pwd301.services.email_service import (
    MockMailClient,
    enqueue_email,
    process_email_queue,
    retry_failed_emails,
    send_single_email,
)
from pwd301.services.exceptions import ForbiddenError, InvalidEmailError
from pwd301.services.notification_service import emit_event
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
    """Ensure standard roles exist."""
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
def test_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test student user."""
    u = register_user(
        f"email_test_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Email Tester"
    )
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test admin user."""
    u = register_user(
        f"email_admin_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Email Admin"
    )
    return assign_role_to_user(u.id, "ADMIN")


def test_enqueue_email_basic(app: Flask, test_user: User) -> None:
    """Test basic email enqueueing into PENDING status."""
    delivery = enqueue_email(
        recipient_email=test_user.email,
        subject="Test Subject",
        body_text="Test Body",
        template_code="TEST_TEMPLATE",
        recipient_user_id=test_user.id,
        session=db.session,
    )
    db.session.commit()

    assert delivery.id is not None
    assert delivery.status == "PENDING"
    assert delivery.attempt_count == 0
    assert delivery.recipient_email_snapshot == test_user.email
    assert delivery.template_code == "TEST_TEMPLATE"
    assert delivery.next_attempt_at is not None


def test_enqueue_email_invalid_syntax(app: Flask) -> None:
    """Test that invalid email syntax raises InvalidEmailError."""
    with pytest.raises(InvalidEmailError):
        enqueue_email(
            recipient_email="not-an-email",
            subject="Test",
            body_text="Body",
            session=db.session,
        )


def test_enqueue_email_deduplication(app: Flask, test_user: User) -> None:
    """Test that multiple enqueues with identical event and recipient reuse the same delivery."""
    event = emit_event(event_type="DEDUPE_TEST", session=db.session)
    db.session.commit()

    d1 = enqueue_email(
        recipient_email=test_user.email,
        subject="Notice",
        body_text="Content",
        template_code="DEDUPE_TEMPLATE",
        notification_event_id=event.id,
        session=db.session,
    )
    db.session.commit()

    d2 = enqueue_email(
        recipient_email=test_user.email,
        subject="Notice",
        body_text="Content",
        template_code="DEDUPE_TEMPLATE",
        notification_event_id=event.id,
        session=db.session,
    )
    assert d1.id == d2.id


def test_send_single_email_success(app: Flask, test_user: User) -> None:
    """Test successful send updates status to SENT and sets sent_at."""
    delivery = enqueue_email(
        recipient_email=test_user.email,
        subject="Success Test",
        body_text="Body text",
        template_code="SUCCESS_TEMPLATE",
        session=db.session,
    )
    db.session.commit()

    mock_client = MockMailClient(should_fail=False)
    success = send_single_email(
        delivery=delivery,
        mail_client=mock_client,
        session=db.session,
    )
    db.session.commit()

    assert success is True
    assert delivery.status == "SENT"
    assert delivery.sent_at is not None
    assert delivery.last_error is None
    assert len(mock_client.sent_messages) == 1
    assert mock_client.sent_messages[0]["recipient_email"] == test_user.email


def test_send_single_email_transient_failure_and_backoff(app: Flask, test_user: User) -> None:
    """Test that transient send failure increments attempt_count and schedules backoff."""
    delivery = enqueue_email(
        recipient_email=test_user.email,
        subject="Retry Test",
        body_text="Body text",
        template_code="RETRY_TEMPLATE",
        session=db.session,
    )
    db.session.commit()

    mock_client = MockMailClient(should_fail=True, fail_message="Temporary SMTP failure")
    success = send_single_email(
        delivery=delivery,
        mail_client=mock_client,
        max_retries=3,
        session=db.session,
    )
    db.session.commit()

    assert success is False
    assert delivery.status == "PENDING"
    assert delivery.attempt_count == 1
    assert "Temporary SMTP failure" in (delivery.last_error or "")
    # Check backoff delay is approximately 2^1 * 60 = 120 seconds into the future
    assert delivery.next_attempt_at is not None
    next_at = delivery.next_attempt_at
    if next_at.tzinfo is None:
        next_at = next_at.replace(tzinfo=datetime.UTC)
    expected_delay = utc_now() + datetime.timedelta(seconds=120)
    # Allow 5 seconds of clock delta
    diff = abs((next_at - expected_delay).total_seconds())
    assert diff < 5


def test_send_single_email_terminal_failure(app: Flask, test_user: User) -> None:
    """Test that exceeding max_retries marks delivery as FAILED."""
    delivery = enqueue_email(
        recipient_email=test_user.email,
        subject="Terminal Fail Test",
        body_text="Body text",
        template_code="TERMINAL_TEMPLATE",
        session=db.session,
    )
    delivery.attempt_count = 2  # Already failed twice
    db.session.commit()

    mock_client = MockMailClient(should_fail=True, fail_message="Permanent SMTP error")
    success = send_single_email(
        delivery=delivery,
        mail_client=mock_client,
        max_retries=3,
        session=db.session,
    )
    db.session.commit()

    assert success is False
    assert delivery.attempt_count == 3
    assert delivery.status == "FAILED"
    assert delivery.next_attempt_at is None


def test_process_email_queue_batch(app: Flask, test_user: User) -> None:
    """Test batch queue processing of due email deliveries."""
    # Create 3 deliveries
    for i in range(3):
        enqueue_email(
            recipient_email=f"recipient_{i}_{test_user.email}",
            subject=f"Subject {i}",
            body_text=f"Body {i}",
            template_code="BATCH_TEMPLATE",
            session=db.session,
        )
    db.session.commit()

    mock_client = MockMailClient(should_fail=False)
    results = process_email_queue(
        batch_size=10,
        mail_client=mock_client,
        session=db.session,
    )
    db.session.commit()

    assert results["processed"] >= 3
    assert results["succeeded"] >= 3
    assert results["failed"] == 0


def test_retry_failed_emails_by_admin(app: Flask, test_user: User, admin_user: User) -> None:
    """Test that admin can reset FAILED email deliveries back to PENDING."""
    # Create a failed delivery
    delivery = enqueue_email(
        recipient_email=test_user.email,
        subject="Will Fail",
        body_text="Body",
        template_code="FAILED_TEMPLATE",
        session=db.session,
    )
    delivery.status = "FAILED"
    delivery.attempt_count = 3
    delivery.last_error = "Permanent failure"
    db.session.commit()

    # Non-admin cannot retry
    with pytest.raises(ForbiddenError):
        retry_failed_emails(actor=test_user, session=db.session)

    # Admin retries
    count = retry_failed_emails(actor=admin_user, session=db.session)
    db.session.commit()

    assert count >= 1
    assert delivery.status == "PENDING"
    assert delivery.attempt_count == 0
    assert delivery.last_error is None
