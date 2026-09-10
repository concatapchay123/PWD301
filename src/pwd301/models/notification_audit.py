"""Notification and security audit models for PWD301.

Implements canonical schema tables from sql/008_notification_audit.sql:
- notification_events
- notifications
- notification_preferences
- email_deliveries
- audit_events
"""

from __future__ import annotations

import uuid
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from pwd301.extensions import Base, db
from pwd301.models.types import (
    GUID,
    BigIntPK,
    NVarCharMax,
    RowVersion,
    UTCDateTime,
    utc_now,
)


class NotificationEvent(Base):
    """Business event triggering notification fans mapping to 'notification_events'."""

    __tablename__ = "notification_events"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    event_key = db.Column(
        GUID,
        nullable=False,
        unique=True,
        default=uuid.uuid4,
        server_default=sa.text("NEWID()"),
    )
    event_type = db.Column(sa.String(64), nullable=False)
    actor_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "users.id",
            name="fk_notification_events_actor_user_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    target_type = db.Column(sa.String(32), nullable=True)
    target_id = db.Column(sa.BigInteger, nullable=True)
    correlation_id = db.Column(GUID, nullable=True)
    payload_json = db.Column(NVarCharMax, nullable=True)
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )

    __table_args__ = (
        sa.CheckConstraint(
            "payload_json IS NULL OR ISJSON(payload_json)=1",
            name="ck_notification_events_1",
        ),
        sa.Index("ix_notification_events_type", "event_type", "created_at"),
        sa.Index("ix_notification_events_target", "target_type", "target_id", "created_at"),
    )

    actor = relationship("User", foreign_keys=[actor_user_id])
    notifications = relationship(
        "Notification",
        back_populates="event",
        cascade="all, delete-orphan",
    )

    @property
    def public_id(self) -> str:
        """Public identifier matching event_key per ADR-002."""
        return str(self.event_key)


class Notification(Base):
    """User in-app notification mapping to canonical 'notifications' table."""

    __tablename__ = "notifications"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    public_id = db.Column(
        GUID,
        nullable=False,
        unique=True,
        default=uuid.uuid4,
        server_default=sa.text("NEWSEQUENTIALID()"),
    )
    notification_event_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "notification_events.id",
            name="fk_notifications_notification_event_id",
        ),
        nullable=False,
    )
    recipient_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("users.id", name="fk_notifications_recipient_user_id"),
        nullable=False,
    )
    category = db.Column(sa.String(32), nullable=False)
    title = db.Column(sa.Unicode(250), nullable=False)
    body = db.Column(sa.Unicode(2000), nullable=False)
    read_at = db.Column(UTCDateTime, nullable=True)
    expires_at = db.Column(UTCDateTime, nullable=True)
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )
    row_version = db.Column(RowVersion, nullable=True)

    __table_args__ = (
        sa.UniqueConstraint(
            "notification_event_id",
            "recipient_user_id",
            name="uq_notifications_notification_event_id_recipient_user_id_1",
        ),
        sa.CheckConstraint(
            "category IN ('SECURITY','COURSE','ASSESSMENT','GRADE','SYSTEM')",
            name="ck_notifications_1",
        ),
        sa.Index(
            "ix_notifications_recipient",
            "recipient_user_id",
            "read_at",
            "created_at",
        ),
        sa.Index(
            "ix_notifications_user_unread",
            "recipient_user_id",
            "created_at",
            mssql_where=sa.text("read_at IS NULL"),
            sqlite_where=sa.text("read_at IS NULL"),
        ),
        sa.Index(
            "ix_notifications_expiry",
            "expires_at",
            "id",
            mssql_where=sa.text("expires_at IS NOT NULL"),
            sqlite_where=sa.text("expires_at IS NOT NULL"),
        ),
    )

    event = relationship("NotificationEvent", back_populates="notifications")
    recipient = relationship("User", foreign_keys=[recipient_user_id])

    @property
    def is_read(self) -> bool:
        """Return True if notification has been read."""
        return self.read_at is not None

    def to_dict(self) -> dict[str, Any]:
        """Convert notification to dictionary conforming strictly to ADR-002 Zero PK Leakage."""
        return {
            "id": str(self.public_id),
            "category": self.category,
            "title": self.title,
            "body": self.body,
            "read": self.is_read,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class NotificationPreference(Base):
    """User notification opt-in preferences mapping to 'notification_preferences'."""

    __tablename__ = "notification_preferences"

    user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("users.id", name="fk_notification_preferences_user_id"),
        primary_key=True,
    )
    category = db.Column(sa.String(32), primary_key=True)
    email_enabled = db.Column(sa.Boolean, nullable=False)
    updated_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )
    row_version = db.Column(RowVersion, nullable=True)

    __table_args__ = (
        sa.CheckConstraint(
            "category IN ('COURSE','ASSESSMENT','GRADE','MARKETING','SECURITY')",
            name="ck_notification_preferences_1",
        ),
        sa.CheckConstraint(
            "category <> 'SECURITY' OR email_enabled = 1",
            name="ck_notification_preferences_2",
        ),
    )

    user = relationship("User", foreign_keys=[user_id])

    def to_dict(self) -> dict[str, Any]:
        """Convert preference to dictionary conforming strictly to ADR-002 Zero PK Leakage."""
        return {
            "category": self.category,
            "email_enabled": bool(self.email_enabled),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class EmailDelivery(Base):
    """Outbound email delivery attempt mapping to 'email_deliveries' table."""

    __tablename__ = "email_deliveries"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    notification_event_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "notification_events.id",
            name="fk_email_deliveries_notification_event_id",
        ),
        nullable=False,
    )
    recipient_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "users.id",
            name="fk_email_deliveries_recipient_user_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    recipient_email_snapshot = db.Column(sa.Unicode(320), nullable=False)
    template_code = db.Column(sa.String(64), nullable=False)
    dedupe_key = db.Column(GUID, nullable=False, unique=True, default=uuid.uuid4)
    status = db.Column(
        sa.String(20),
        nullable=False,
        default="PENDING",
        server_default=sa.text("'PENDING'"),
    )
    attempt_count = db.Column(
        sa.Integer,
        nullable=False,
        default=0,
        server_default=sa.text("0"),
    )
    next_attempt_at = db.Column(UTCDateTime, nullable=True)
    sent_at = db.Column(UTCDateTime, nullable=True)
    last_error = db.Column(sa.Unicode(2000), nullable=True)
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )
    row_version = db.Column(RowVersion, nullable=True)

    __table_args__ = (
        sa.UniqueConstraint(
            "notification_event_id",
            "recipient_email_snapshot",
            "template_code",
            name="uq_email_deliveries_notification_event_id_recipient_email_snapshot_template_code_2",
        ),
        sa.CheckConstraint(
            "status IN ('PENDING','SENDING','SENT','FAILED','CANCELLED')",
            name="ck_email_deliveries_1",
        ),
        sa.CheckConstraint("attempt_count >= 0", name="ck_email_deliveries_2"),
        sa.Index(
            "ix_email_deliveries_queue",
            "status",
            "next_attempt_at",
            mssql_where=sa.text("status IN ('PENDING','SENDING')"),
            sqlite_where=sa.text("status IN ('PENDING','SENDING')"),
        ),
    )

    event = relationship("NotificationEvent", foreign_keys=[notification_event_id])
    recipient = relationship("User", foreign_keys=[recipient_user_id])

    @property
    def public_id(self) -> str:
        """Public identifier matching dedupe_key per ADR-002."""
        return str(self.dedupe_key)

    def to_dict(self) -> dict[str, Any]:
        """Convert email delivery to dictionary conforming strictly to ADR-002 Zero PK Leakage."""
        return {
            "id": str(self.public_id),
            "recipient_email": self.recipient_email_snapshot,
            "template_code": self.template_code,
            "status": self.status,
            "attempt_count": self.attempt_count,
            "next_attempt_at": self.next_attempt_at.isoformat() if self.next_attempt_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "last_error": self.last_error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AuditEvent(Base):
    """Append-only critical administrative and security audit record mapping to 'audit_events'."""

    __tablename__ = "audit_events"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    event_id = db.Column(
        GUID,
        nullable=False,
        unique=True,
        default=uuid.uuid4,
        server_default=sa.text("NEWID()"),
    )
    actor_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("users.id", name="fk_audit_events_actor_user_id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_roles_snapshot = db.Column(sa.Unicode(200), nullable=False)
    action = db.Column(sa.String(80), nullable=False)
    target_type = db.Column(sa.String(40), nullable=False)
    target_id = db.Column(sa.BigInteger, nullable=True)
    reason = db.Column(sa.Unicode(1000), nullable=True)
    before_json = db.Column(NVarCharMax, nullable=True)
    after_json = db.Column(NVarCharMax, nullable=True)
    request_id = db.Column(GUID, nullable=True)
    ip_address = db.Column(sa.String(45), nullable=True)
    performed_as_admin = db.Column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.text("0"),
    )
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )

    __table_args__ = (
        sa.CheckConstraint(
            "before_json IS NULL OR ISJSON(before_json)=1", name="ck_audit_events_1"
        ),
        sa.CheckConstraint("after_json IS NULL OR ISJSON(after_json)=1", name="ck_audit_events_2"),
        sa.Index("ix_audit_events_action_time", "action", "created_at"),
        sa.Index("ix_audit_events_actor", "actor_user_id", "created_at"),
        sa.Index("ix_audit_events_target", "target_type", "target_id", "created_at"),
    )

    actor = relationship("User", foreign_keys=[actor_user_id])
