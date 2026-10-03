"""Add avatar_url column to users table.

Revision ID: a1b2c3d4e5f8
Revises: f6a7b8c0d1e2
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "a1b2c3d4e5f8"
down_revision = "f6a7b8c0d1e2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "avatar_url",
                sa.Unicode(length=500),
                nullable=True,
            )
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name in ("sqlite", "mssql"):
        op.execute(sa.text("ALTER TABLE users DROP COLUMN avatar_url"))
    else:
        with op.batch_alter_table("users", schema=None) as batch_op:
            batch_op.drop_column("avatar_url")
