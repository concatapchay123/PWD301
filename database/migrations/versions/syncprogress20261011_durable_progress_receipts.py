"""Persist generic lesson heartbeat identities with credited progress."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mssql

revision = "syncprogress20261011"
down_revision = "reviewpolicy20261010"
branch_labels = None
depends_on = None


def upgrade():
    stamp_default = (
        "SYSUTCDATETIME()" if op.get_bind().dialect.name == "mssql" else "CURRENT_TIMESTAMP"
    )
    op.create_table(
        "lesson_progress_receipts",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "enrollment_period_id",
            sa.BigInteger(),
            sa.ForeignKey("enrollment_periods.id", name="fk_progress_receipts_period"),
            nullable=False,
        ),
        sa.Column(
            "lesson_id",
            sa.BigInteger(),
            sa.ForeignKey("lessons.id", name="fk_progress_receipts_lesson"),
            nullable=False,
        ),
        sa.Column("client_event_id", sa.String(128), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime().with_variant(mssql.DATETIME2(3), "mssql"),
            nullable=False,
            server_default=sa.text(stamp_default),
        ),
        sa.UniqueConstraint(
            "enrollment_period_id",
            "lesson_id",
            "client_event_id",
            name="uq_progress_receipts_event",
        ),
    )


def downgrade():
    op.drop_table("lesson_progress_receipts")
