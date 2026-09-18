"""0005_add_course_customization_fields

Revision ID: b2c3d4e5f6a8
Revises: a1b2c3d4e5f7
Create Date: 2026-09-14 06:00:00.000000

Adds customization fields to courses table:
- learning_objectives: NVARCHAR(MAX) NULL
- target_audience: NVARCHAR(MAX) NULL
- completion_requirements: NVARCHAR(MAX) NULL
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b2c3d4e5f6a8"
down_revision = "a1b2c3d4e5f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("courses", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("learning_objectives", sa.UnicodeText(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("target_audience", sa.UnicodeText(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("completion_requirements", sa.UnicodeText(), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("courses", schema=None) as batch_op:
        batch_op.drop_column("completion_requirements")
        batch_op.drop_column("target_audience")
        batch_op.drop_column("learning_objectives")
