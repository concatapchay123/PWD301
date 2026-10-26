"""Align revision change types with the canonical question-bank DDL.

Revision ID: c4d5e6f7a8b0
Revises: b3c4d5e6f7a9
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "c4d5e6f7a8b0"
down_revision = "b3c4d5e6f7a9"
branch_labels = None
depends_on = None

LEGACY_TYPES = "'INITIAL','EDIT','ANSWER_ONLY','CONTENT_OR_CHOICES'"
ADDITIONAL_TYPES = "'TYPO_FIX','ANSWER_CHANGE','CONTENT_CHANGE','REVOCATION'"


def _replace_constraint(allowed_types: str) -> None:
    with op.batch_alter_table("question_revisions") as table:
        table.drop_constraint("ck_question_revisions_4", type_="check")
        table.create_check_constraint(
            "ck_question_revisions_4", f"change_type IN ({allowed_types})"
        )


def upgrade() -> None:
    """Widen the constraint without rewriting revision content or history."""
    _replace_constraint(f"{LEGACY_TYPES},{ADDITIONAL_TYPES}")


def downgrade() -> None:
    """Refuse a lossy rollback once expanded revision types have been used."""
    count = (
        op.get_bind()
        .execute(
            sa.text(
                f"SELECT COUNT(*) FROM question_revisions WHERE change_type IN ({ADDITIONAL_TYPES})"
            )
        )
        .scalar_one()
    )
    if count:
        raise RuntimeError(
            "Cannot downgrade question revision change types while expanded values exist; "
            "retain history and use a forward fix."
        )
    _replace_constraint(LEGACY_TYPES)
