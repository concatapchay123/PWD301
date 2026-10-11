"""Index the 24-hour receipt cleanup, preserving the applied playback migration."""
from alembic import op

revision = "receiptretention20261009"
down_revision = "playback20261009"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("ix_playback_receipts_created_at", "playback_receipts", ["created_at"])


def downgrade():
    op.drop_index("ix_playback_receipts_created_at", table_name="playback_receipts")
