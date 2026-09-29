"""Add lesson revisions, draft continuity and acknowledged revision tracking.

Revision ID: e5f6a7b8c0d1
Revises: d4e5f6a7b8c0
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "e5f6a7b8c0d1"
down_revision = "d4e5f6a7b8c0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("lessons") as batch_op:
        batch_op.add_column(
            sa.Column(
                "revision_no",
                sa.Integer(),
                nullable=False,
                server_default=sa.text("1"),
            )
        )
        batch_op.add_column(
            sa.Column(
                "previous_lesson_id",
                sa.BigInteger(),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "material_change_summary",
                sa.Unicode(500),
                nullable=True,
            )
        )
        batch_op.create_foreign_key(
            "fk_lessons_previous_lesson_id",
            "lessons",
            ["previous_lesson_id"],
            ["id"],
        )

    with op.batch_alter_table("lesson_progress") as batch_op:
        batch_op.add_column(
            sa.Column(
                "acknowledged_revision_no",
                sa.Integer(),
                nullable=True,
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("lesson_progress") as batch_op:
        batch_op.drop_column("acknowledged_revision_no")

    with op.batch_alter_table("lessons") as batch_op:
        batch_op.drop_constraint("fk_lessons_previous_lesson_id", type_="foreignkey")
        batch_op.drop_column("material_change_summary")
        batch_op.drop_column("previous_lesson_id")
        batch_op.drop_column("revision_no")
