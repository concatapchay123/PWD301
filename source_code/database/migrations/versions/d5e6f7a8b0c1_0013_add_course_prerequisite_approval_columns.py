"""Add peer prerequisite approval tracking columns to course_prerequisites.

Revision ID: d5e6f7a8b0c1
Revises: c4d5e6f7a8b0
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "d5e6f7a8b0c1"
down_revision = "c4d5e6f7a8b0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("course_prerequisites") as table:
        table.add_column(
            sa.Column(
                "approval_status",
                sa.String(32),
                nullable=False,
                server_default=sa.text("'APPROVED'"),
            )
        )
        table.add_column(
            sa.Column(
                "requested_by_user_id",
                sa.BigInteger(),
                sa.ForeignKey("users.id", name="fk_course_prerequisites_requested_by_user_id"),
                nullable=True,
            )
        )
        table.add_column(
            sa.Column(
                "requested_at",
                sa.DateTime(timezone=True),
                nullable=True,
            )
        )
        table.add_column(
            sa.Column(
                "reviewed_at",
                sa.DateTime(timezone=True),
                nullable=True,
            )
        )
        table.add_column(
            sa.Column(
                "reviewed_by_user_id",
                sa.BigInteger(),
                sa.ForeignKey("users.id", name="fk_course_prerequisites_reviewed_by_user_id"),
                nullable=True,
            )
        )
        table.add_column(
            sa.Column(
                "review_note",
                sa.Unicode(500),
                nullable=True,
            )
        )
        table.create_check_constraint(
            "ck_course_prerequisites_approval_status",
            "approval_status IN ('APPROVED', 'PENDING_APPROVAL', 'REJECTED')",
        )
        table.create_index(
            "ix_course_prereq_approval",
            ["prerequisite_course_id", "approval_status"],
        )


def downgrade() -> None:
    with op.batch_alter_table("course_prerequisites") as table:
        table.drop_index("ix_course_prereq_approval")
        table.drop_constraint("ck_course_prerequisites_approval_status", type_="check")
        table.drop_column("review_note")
        table.drop_column("reviewed_by_user_id")
        table.drop_column("reviewed_at")
        table.drop_column("requested_at")
        table.drop_column("requested_by_user_id")
        table.drop_column("approval_status")
