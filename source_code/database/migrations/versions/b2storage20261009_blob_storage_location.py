"""Record verified blob location without moving existing data."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mssql

revision = "b2storage20261009"
down_revision = "d5e6f7a8b0c1"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("file_blobs") as table:
        table.add_column(
            sa.Column(
                "storage_backend", sa.String(10), nullable=False, server_default=sa.text("'local'")
            )
        )
        table.add_column(
            sa.Column(
                "cloud_verified_at",
                sa.DateTime().with_variant(mssql.DATETIME2(3), "mssql"),
                nullable=True,
            )
        )
        table.create_check_constraint(
            "ck_file_blobs_storage_backend", "storage_backend IN ('local','s3')"
        )


def downgrade():
    connection = op.get_bind()
    if connection.execute(
        sa.text("SELECT COUNT(*) FROM file_blobs WHERE storage_backend = 's3'")
    ).scalar():
        raise RuntimeError("Restore verified local copies before downgrading storage metadata.")
    with op.batch_alter_table("file_blobs") as table:
        table.drop_constraint("ck_file_blobs_storage_backend", type_="check")
        table.drop_column("cloud_verified_at")
        table.drop_column("storage_backend")
