"""Repair the reverse migration path for SQL Server blob-location defaults.

Current head keeps the canonical local default. A downgrade through this revision
removes only that constraint before the older immutable migration drops its column.
Do not stop at the intermediate revision on production; re-upgrade restores default.
"""

import sqlalchemy as sa
from alembic import op

revision = "blobdefaultrepair20261009"
down_revision = "receiptretention20261009"
branch_labels = None
depends_on = None

DEFAULT_QUERY = """
SELECT dc.definition FROM sys.default_constraints dc
JOIN sys.columns c ON c.object_id = dc.parent_object_id AND c.column_id = dc.parent_column_id
WHERE dc.parent_object_id = OBJECT_ID(N'file_blobs') AND c.name = N'storage_backend'
"""


def upgrade():
    connection = op.get_bind()
    if connection.dialect.name != "mssql":
        return
    definition = connection.execute(sa.text(DEFAULT_QUERY)).scalar()
    if definition is None:
        connection.execute(
            sa.text(
                "ALTER TABLE file_blobs ADD CONSTRAINT DF_file_blobs_storage_backend_vps DEFAULT ('local') FOR storage_backend"
            )
        )
    elif str(definition).replace("(", "").replace(")", "").replace(" ", "").lower() not in (
        "'local'",
        "n'local'",
    ):
        raise RuntimeError(
            "Unexpected blob storage default; migration stopped without modifying it."
        )
    for column in ("requested_by_user_id", "reviewed_by_user_id"):
        name = "fk_course_prerequisites_" + column
        if (
            connection.execute(sa.text("SELECT OBJECT_ID(:name, 'F')"), {"name": name}).scalar()
            is None
        ):
            connection.exec_driver_sql(
                f"ALTER TABLE course_prerequisites ADD CONSTRAINT [{name}] FOREIGN KEY ([{column}]) REFERENCES users(id)"
            )
    approval_default = connection.execute(
        sa.text(
            DEFAULT_QUERY.replace("file_blobs", "course_prerequisites").replace(
                "storage_backend", "approval_status"
            )
        )
    ).scalar()
    if approval_default is None:
        connection.exec_driver_sql(
            "ALTER TABLE course_prerequisites ADD CONSTRAINT DF_course_prerequisites_approval_vps DEFAULT ('APPROVED') FOR approval_status"
        )


def downgrade():
    connection = op.get_bind()
    if connection.dialect.name == "mssql":
        connection.execute(
            sa.text("""
DECLARE @constraint sysname;
SELECT @constraint = dc.name FROM sys.default_constraints dc
JOIN sys.columns c ON c.object_id = dc.parent_object_id AND c.column_id = dc.parent_column_id
WHERE dc.parent_object_id = OBJECT_ID(N'file_blobs') AND c.name = N'storage_backend';
IF @constraint IS NOT NULL
BEGIN
    DECLARE @statement nvarchar(512) = N'ALTER TABLE file_blobs DROP CONSTRAINT ' + QUOTENAME(@constraint);
    EXEC sys.sp_executesql @statement;
END;
""")
        )
        # The immutable predecessor also omits these SQL Server dependency drops.
        for column in ("requested_by_user_id", "reviewed_by_user_id"):
            name = "fk_course_prerequisites_" + column
            connection.exec_driver_sql(
                f"IF OBJECT_ID(N'{name}', 'F') IS NOT NULL ALTER TABLE course_prerequisites DROP CONSTRAINT [{name}]"
            )
        connection.execute(
            sa.text("""
DECLARE @constraint sysname, @statement nvarchar(512);
SELECT @constraint = dc.name FROM sys.default_constraints dc
JOIN sys.columns c ON c.object_id = dc.parent_object_id AND c.column_id = dc.parent_column_id
WHERE dc.parent_object_id = OBJECT_ID(N'course_prerequisites') AND c.name = N'approval_status';
IF @constraint IS NOT NULL
BEGIN
    SET @statement = N'ALTER TABLE course_prerequisites DROP CONSTRAINT ' + QUOTENAME(@constraint);
    EXEC sys.sp_executesql @statement;
END;
""")
        )
