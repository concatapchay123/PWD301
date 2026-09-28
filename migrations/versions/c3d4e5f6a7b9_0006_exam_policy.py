"""Add browser-supported exam presentation and monitoring policy.

Revision ID: c3d4e5f6a7b9
Revises: b2c3d4e5f6a8
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mssql

revision = "c3d4e5f6a7b9"
down_revision = "b2c3d4e5f6a8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("assessments") as batch_op:
        batch_op.add_column(
            sa.Column("exam_layout", sa.String(16), nullable=False, server_default="STANDARD")
        )
        batch_op.add_column(
            sa.Column(
                "monitoring_enabled", sa.Boolean(), nullable=False, server_default=sa.text("0")
            )
        )
        batch_op.add_column(
            sa.Column(
                "request_fullscreen", sa.Boolean(), nullable=False, server_default=sa.text("0")
            )
        )
        batch_op.create_check_constraint(
            "ck_assessments_exam_layout", "exam_layout IN ('STANDARD','FOCUS')"
        )
    op.create_table(
        "attempt_focus_events",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column("public_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column(
            "attempt_id",
            sa.BigInteger(),
            sa.ForeignKey("assessment_attempts.id", name="fk_attempt_focus_events_attempt_id"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(24), nullable=False),
        sa.Column(
            "started_at", sa.DateTime().with_variant(mssql.DATETIME2(3), "mssql"), nullable=False
        ),
        sa.Column(
            "ended_at", sa.DateTime().with_variant(mssql.DATETIME2(3), "mssql"), nullable=True
        ),
        sa.CheckConstraint(
            "event_type IN ('TAB_HIDDEN','WINDOW_BLUR','FULLSCREEN_EXIT')",
            name="ck_attempt_focus_events_type",
        ),
        sa.UniqueConstraint("public_id", name="uq_attempt_focus_events_public_id"),
    )
    op.create_index(
        "ix_attempt_focus_events_attempt", "attempt_focus_events", ["attempt_id", "started_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_attempt_focus_events_attempt", table_name="attempt_focus_events")
    op.drop_table("attempt_focus_events")
    with op.batch_alter_table("assessments") as batch_op:
        batch_op.drop_constraint("ck_assessments_exam_layout", type_="check")
        batch_op.drop_column("request_fullscreen")
        batch_op.drop_column("monitoring_enabled")
        batch_op.drop_column("exam_layout")
