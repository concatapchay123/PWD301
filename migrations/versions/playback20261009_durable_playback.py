"""Durable pacing and per-media progress.

Revision ID: playback20261009
Revises: b2storage20261009
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mssql

revision = "playback20261009"
down_revision = "b2storage20261009"
branch_labels = None
depends_on = None

PK = sa.BigInteger().with_variant(sa.Integer(), "sqlite")
GUID = sa.Uuid().with_variant(mssql.UNIQUEIDENTIFIER(), "mssql")
STAMP = sa.DateTime().with_variant(mssql.DATETIME2(3), "mssql")
VERSION = sa.LargeBinary(8).with_variant(mssql.ROWVERSION(), "mssql")


def upgrade():
    op.create_table("playback_sessions",
        sa.Column("id", PK, primary_key=True, autoincrement=True),
        sa.Column("public_id", GUID, nullable=False),
        sa.Column("enrollment_period_id", sa.BigInteger(), sa.ForeignKey("enrollment_periods.id"), nullable=False),
        sa.Column("lesson_id", sa.BigInteger(), sa.ForeignKey("lessons.id"), nullable=False),
        sa.Column("media_id", sa.String(128), nullable=False),
        sa.Column("next_sequence", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("last_heartbeat_at", STAMP),
        sa.Column("last_position", sa.Float(), nullable=False),
        sa.Column("last_rate", sa.Float(), nullable=False),
        sa.Column("fractional_seconds", sa.Float(), nullable=False),
        sa.Column("updated_at", STAMP, nullable=False),
        sa.Column("row_version", VERSION),
        sa.UniqueConstraint("public_id", name="uq_playback_public_id"),
        sa.UniqueConstraint("enrollment_period_id", "lesson_id", name="uq_playback_period_lesson"),
        sa.CheckConstraint("next_sequence > 0", name="ck_playback_sequence"),
        sa.CheckConstraint("state IN ('playing','paused','buffering','hidden','blackout','error')", name="ck_playback_state"))
    op.create_table("lesson_media_progress",
        sa.Column("id", PK, primary_key=True, autoincrement=True),
        sa.Column("enrollment_period_id", sa.BigInteger(), sa.ForeignKey("enrollment_periods.id"), nullable=False),
        sa.Column("lesson_id", sa.BigInteger(), sa.ForeignKey("lessons.id"), nullable=False),
        sa.Column("media_id", sa.String(128), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=False),
        sa.Column("frontier_seconds", sa.Float(), nullable=False),
        sa.Column("updated_at", STAMP, nullable=False),
        sa.Column("row_version", VERSION),
        sa.UniqueConstraint("enrollment_period_id", "lesson_id", "media_id", name="uq_media_period_lesson_media"),
        sa.CheckConstraint("duration_seconds > 0 AND frontier_seconds >= 0 AND frontier_seconds <= duration_seconds", name="ck_media_frontier"))
    op.create_table("playback_receipts",
        sa.Column("id", PK, primary_key=True, autoincrement=True),
        sa.Column("session_id", sa.BigInteger(), sa.ForeignKey("playback_sessions.id"), nullable=False),
        sa.Column("lease_id", GUID, nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("response_json", sa.UnicodeText().with_variant(mssql.NVARCHAR(None), "mssql"), nullable=False),
        sa.Column("created_at", STAMP, nullable=False),
        sa.UniqueConstraint("lease_id", "sequence", name="uq_playback_receipt_lease_sequence"),
        sa.CheckConstraint("sequence > 0", name="ck_playback_receipt_sequence"))


def downgrade():
    op.drop_table("playback_receipts")
    op.drop_table("lesson_media_progress")
    op.drop_table("playback_sessions")
