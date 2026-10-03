"""Remove the SQL Server default that prevents lesson revision downgrades.

Revision ID: b3c4d5e6f7a9
Revises: a1b2c3d4e5f8
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "b3c4d5e6f7a9"
down_revision = "a1b2c3d4e5f8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Drop defaults blocking legacy SQL Server column downgrades.

    The historical migrations used ``server_default`` while adding several
    non-null columns. SQL Server materializes each one as a named default
    constraint, and ``ALTER TABLE ... DROP COLUMN`` cannot remove a column
    until that constraint is dropped. This forward-only repair removes only
    those generated constraints; the Python-side defaults remain authoritative
    for new writes.
    """
    bind = op.get_bind()
    if bind.dialect.name != "mssql":
        return

    op.execute(
        sa.text(
            """
            DECLARE @table_name sysname;
            DECLARE @column_name sysname;
            DECLARE @constraint_name sysname;
            DECLARE @statement nvarchar(512);

            DECLARE defaults_cursor CURSOR LOCAL FAST_FORWARD FOR
                SELECT defaults_to_remove.table_name, defaults_to_remove.column_name
                FROM (VALUES
                    (N'lessons', N'revision_no'),
                    (N'assessments', N'exam_layout'),
                    (N'assessments', N'monitoring_enabled'),
                    (N'assessments', N'request_fullscreen'),
                    (N'question_revisions', N'is_current'),
                    (N'file_revisions', N'is_current'),
                    (N'knowledge_versions', N'is_current'),
                    (N'assessment_attempts', N'lease_epoch'),
                    (N'assessment_attempts', N'is_detail_purged')
                ) AS defaults_to_remove(table_name, column_name);

            OPEN defaults_cursor;
            FETCH NEXT FROM defaults_cursor INTO @table_name, @column_name;

            WHILE @@FETCH_STATUS = 0
            BEGIN
                SET @constraint_name = NULL;
                SELECT TOP (1) @constraint_name = dc.name
                FROM sys.default_constraints AS dc
                INNER JOIN sys.columns AS c
                    ON c.object_id = dc.parent_object_id
                    AND c.column_id = dc.parent_column_id
                INNER JOIN sys.tables AS t
                    ON t.object_id = dc.parent_object_id
                INNER JOIN sys.schemas AS s
                    ON s.schema_id = t.schema_id
                WHERE s.name = N'dbo'
                  AND t.name = @table_name
                  AND c.name = @column_name;

                IF @constraint_name IS NOT NULL
                BEGIN
                    SET @statement =
                        N'ALTER TABLE dbo.' + QUOTENAME(@table_name)
                        + N' DROP CONSTRAINT ' + QUOTENAME(@constraint_name);
                    EXEC sys.sp_executesql @statement;
                END;

                FETCH NEXT FROM defaults_cursor INTO @table_name, @column_name;
            END;

            CLOSE defaults_cursor;
            DEALLOCATE defaults_cursor;
            """
        )
    )


def downgrade() -> None:
    """Keep the repair one-way so the legacy downgrade can drop the column."""
