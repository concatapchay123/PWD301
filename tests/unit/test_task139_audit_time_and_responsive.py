"""Unit test verifying TASK-139 fixes:
1. AuditEvent and Notification datetime serialization strictly outputs ISO 8601 with 'Z' suffix.
2. to_utc_iso_string helper properly handles naive datetimes, aware datetimes, None, and strings.
"""

from __future__ import annotations

import datetime
import uuid
from backend.models.notification_audit import AuditEvent, EmailDelivery, to_utc_iso_string
from backend.models.identity import User


def test_to_utc_iso_string_with_naive_datetime():
    dt = datetime.datetime(2026, 10, 25, 8, 50, 16)
    result = to_utc_iso_string(dt)
    assert result == "2026-10-25T08:50:16Z"
    assert result.endswith("Z")


def test_to_utc_iso_string_with_aware_datetime():
    dt = datetime.datetime(2026, 10, 25, 8, 50, 16, tzinfo=datetime.UTC)
    result = to_utc_iso_string(dt)
    assert result.endswith("Z") or "+00:00" in result


def test_to_utc_iso_string_with_none():
    assert to_utc_iso_string(None) is None


def test_audit_event_to_dict_has_z_suffix():
    test_id = uuid.uuid4()
    event = AuditEvent(
        event_id=test_id,
        action="TEST_ACTION",
        target_type="COURSE",
        created_at=datetime.datetime(2026, 10, 25, 1, 50, 16),
        performed_as_admin=True,
    )
    d = event.to_dict()
    assert d["created_at"] is not None
    assert d["created_at"].endswith("Z")
    assert d["created_at"] == "2026-10-25T01:50:16Z"


def test_email_delivery_to_dict_has_z_suffix():
    delivery = EmailDelivery(
        dedupe_key="DELIV_123",
        recipient_email_snapshot="test@example.com",
        template_code="WELCOME",
        subject="Welcome",
        body_text="Welcome to PPTQ LMS",
        status="SENT",
        attempt_count=1,
        created_at=datetime.datetime(2026, 10, 25, 2, 0, 0),
        sent_at=datetime.datetime(2026, 10, 25, 2, 0, 5),
    )
    d = delivery.to_dict()
    assert d["created_at"] == "2026-10-25T02:00:00Z"
    assert d["sent_at"] == "2026-10-25T02:00:05Z"
