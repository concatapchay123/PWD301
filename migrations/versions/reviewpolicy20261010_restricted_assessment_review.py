"""Allow restricted assessment review without rewriting applied migrations."""

import sqlalchemy as sa
from alembic import op

revision = "reviewpolicy20261010"
down_revision = "blobdefaultrepair20261009"
branch_labels = None
depends_on = None

LEGACY_POLICIES = "'IMMEDIATE','AFTER_CLOSE','AFTER_ALL_ATTEMPTS','NEVER'"


def upgrade():
    with op.batch_alter_table("assessments") as batch:
        batch.drop_constraint("ck_assessments_8", type_="check")
        batch.create_check_constraint(
            "ck_assessments_8",
            f"answer_visibility_policy IN ({LEGACY_POLICIES},'CORRECT_WRONG_ONLY')",
        )


def downgrade():
    count = (
        op.get_bind()
        .execute(
            sa.text(
                "SELECT COUNT(*) FROM assessments WHERE answer_visibility_policy='CORRECT_WRONG_ONLY'"
            )
        )
        .scalar()
    )
    if count:
        raise RuntimeError(
            "Cannot downgrade while assessments use CORRECT_WRONG_ONLY. "
            "An authorized owner must explicitly select a legacy policy first."
        )
    with op.batch_alter_table("assessments") as batch:
        batch.drop_constraint("ck_assessments_8", type_="check")
        batch.create_check_constraint(
            "ck_assessments_8", f"answer_visibility_policy IN ({LEGACY_POLICIES})"
        )
