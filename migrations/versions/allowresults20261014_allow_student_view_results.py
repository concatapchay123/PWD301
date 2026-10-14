"""Add allow_student_view_results configuration column to assessments.

Revision ID: allowresults20261014
Revises: syncprogress20261011
"""

import sqlalchemy as sa
from alembic import op

revision = "allowresults20261014"
down_revision = "syncprogress20261011"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("assessments") as batch:
        batch.add_column(
            sa.Column(
                "allow_student_view_results",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("1"),
            )
        )


def downgrade():
    with op.batch_alter_table("assessments") as batch:
        batch.drop_column("allow_student_view_results")
