"""Durable video pacing, per-media frontiers and heartbeat receipts."""

import uuid

import sqlalchemy as sa

from pwd301.extensions import Base, db
from pwd301.models.types import GUID, BigIntPK, NVarCharMax, RowVersion, UTCDateTime, utc_now


class PlaybackSession(Base):
    __tablename__ = "playback_sessions"
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    public_id = db.Column(GUID, nullable=False, unique=True, default=uuid.uuid4)
    enrollment_period_id = db.Column(
        sa.BigInteger, sa.ForeignKey("enrollment_periods.id"), nullable=False
    )
    lesson_id = db.Column(sa.BigInteger, sa.ForeignKey("lessons.id"), nullable=False)
    media_id = db.Column(sa.String(128), nullable=False)
    next_sequence = db.Column(sa.Integer, nullable=False, default=1)
    state = db.Column(sa.String(16), nullable=False, default="paused")
    last_heartbeat_at = db.Column(UTCDateTime, nullable=True)
    last_position = db.Column(sa.Float, nullable=False, default=0)
    last_rate = db.Column(sa.Float, nullable=False, default=1)
    fractional_seconds = db.Column(sa.Float, nullable=False, default=0)
    updated_at = db.Column(UTCDateTime, nullable=False, default=utc_now)
    row_version = db.Column(RowVersion, nullable=True)
    __table_args__ = (
        sa.UniqueConstraint("enrollment_period_id", "lesson_id", name="uq_playback_period_lesson"),
        sa.CheckConstraint("next_sequence > 0", name="ck_playback_sequence"),
        sa.CheckConstraint(
            "state IN ('playing','paused','buffering','hidden','blackout','error')",
            name="ck_playback_state",
        ),
    )


class MediaProgress(Base):
    __tablename__ = "lesson_media_progress"
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    enrollment_period_id = db.Column(
        sa.BigInteger, sa.ForeignKey("enrollment_periods.id"), nullable=False
    )
    lesson_id = db.Column(sa.BigInteger, sa.ForeignKey("lessons.id"), nullable=False)
    media_id = db.Column(sa.String(128), nullable=False)
    duration_seconds = db.Column(sa.Float, nullable=False)
    frontier_seconds = db.Column(sa.Float, nullable=False, default=0)
    updated_at = db.Column(UTCDateTime, nullable=False, default=utc_now)
    row_version = db.Column(RowVersion, nullable=True)
    __table_args__ = (
        sa.UniqueConstraint(
            "enrollment_period_id", "lesson_id", "media_id", name="uq_media_period_lesson_media"
        ),
        sa.CheckConstraint(
            "duration_seconds > 0 AND frontier_seconds >= 0 AND frontier_seconds <= duration_seconds",
            name="ck_media_frontier",
        ),
    )


class PlaybackReceipt(Base):
    __tablename__ = "playback_receipts"
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    session_id = db.Column(sa.BigInteger, sa.ForeignKey("playback_sessions.id"), nullable=False)
    lease_id = db.Column(GUID, nullable=False)
    sequence = db.Column(sa.Integer, nullable=False)
    response_json = db.Column(NVarCharMax, nullable=False)
    created_at = db.Column(UTCDateTime, nullable=False, default=utc_now)
    __table_args__ = (
        sa.UniqueConstraint("lease_id", "sequence", name="uq_playback_receipt_lease_sequence"),
        sa.CheckConstraint("sequence > 0", name="ck_playback_receipt_sequence"),
        sa.Index("ix_playback_receipts_created_at", "created_at"),
    )
