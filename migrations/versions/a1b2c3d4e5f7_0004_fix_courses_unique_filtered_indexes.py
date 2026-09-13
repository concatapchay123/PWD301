"""0004_fix_courses_unique_filtered_indexes

Revision ID: a1b2c3d4e5f7
Revises: f1a2b3c4d5e6
Create Date: 2026-09-13 10:00:00.000000

Aligns courses table unique constraints with canonical architecture (sql/002_course_learning.sql):
- Drops unconditional table-level unique constraints on course_code_normalized and title_normalized.
- Creates filtered unique indexes ux_courses_course_code_active and ux_courses_title_active
  with predicate (deleted_at IS NULL).
- Allows soft-deleted courses (TRASH) to release code/title for reuse by active courses.
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f7"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    if dialect_name == "mssql":
        # 1. Drop any table-level unique constraints on course_code_normalized and title_normalized
        op.execute(
            sa.text(
                """
            DECLARE @drop_constraints_sql NVARCHAR(MAX) = N'';
            SELECT @drop_constraints_sql +=
                N'ALTER TABLE courses DROP CONSTRAINT [' + kc.name + N']; '
            FROM sys.key_constraints kc
            JOIN sys.index_columns ic
                ON kc.parent_object_id = ic.object_id AND kc.unique_index_id = ic.index_id
            JOIN sys.columns c
                ON ic.object_id = c.object_id AND ic.column_id = c.column_id
            WHERE kc.parent_object_id = OBJECT_ID('courses')
              AND c.name IN ('course_code_normalized', 'title_normalized')
              AND kc.type = 'UQ';

            IF LEN(@drop_constraints_sql) > 0
                EXEC sp_executesql @drop_constraints_sql;
        """
            )
        )

        # 2. Drop any unconditional unique indexes on course_code_normalized and title_normalized
        op.execute(
            sa.text(
                """
            DECLARE @drop_indexes_sql NVARCHAR(MAX) = N'';
            SELECT @drop_indexes_sql += N'DROP INDEX [' + i.name + N'] ON courses; '
            FROM sys.indexes i
            JOIN sys.index_columns ic
                ON i.object_id = ic.object_id AND i.index_id = ic.index_id
            JOIN sys.columns c
                ON ic.object_id = c.object_id AND ic.column_id = c.column_id
            WHERE i.object_id = OBJECT_ID('courses')
              AND c.name IN ('course_code_normalized', 'title_normalized')
              AND i.is_unique = 1
              AND i.has_filter = 0
              AND i.is_primary_key = 0;

            IF LEN(@drop_indexes_sql) > 0
                EXEC sp_executesql @drop_indexes_sql;
        """
            )
        )

        # 3. Create canonical filtered unique indexes
        op.execute(
            sa.text(
                """
            IF NOT EXISTS (
                SELECT 1 FROM sys.indexes
                WHERE object_id = OBJECT_ID('courses')
                  AND name = 'ux_courses_course_code_active'
            )
            BEGIN
                CREATE UNIQUE NONCLUSTERED INDEX ux_courses_course_code_active
                ON courses (course_code_normalized)
                WHERE deleted_at IS NULL;
            END;

            IF NOT EXISTS (
                SELECT 1 FROM sys.indexes
                WHERE object_id = OBJECT_ID('courses')
                  AND name = 'ux_courses_title_active'
            )
            BEGIN
                CREATE UNIQUE NONCLUSTERED INDEX ux_courses_title_active
                ON courses (title_normalized)
                WHERE deleted_at IS NULL;
            END;
        """
            )
        )
    else:
        # SQLite / other dialects
        with op.batch_alter_table("courses", schema=None) as batch_op:
            batch_op.create_index(
                "ux_courses_course_code_active",
                ["course_code_normalized"],
                unique=True,
                sqlite_where=sa.text("deleted_at IS NULL"),
            )
            batch_op.create_index(
                "ux_courses_title_active",
                ["title_normalized"],
                unique=True,
                sqlite_where=sa.text("deleted_at IS NULL"),
            )


def downgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    if dialect_name == "mssql":
        op.execute(
            sa.text(
                """
            IF EXISTS (
                SELECT 1 FROM sys.indexes
                WHERE object_id = OBJECT_ID('courses') AND name = 'ux_courses_course_code_active'
            )
                DROP INDEX ux_courses_course_code_active ON courses;

            IF EXISTS (
                SELECT 1 FROM sys.indexes
                WHERE object_id = OBJECT_ID('courses') AND name = 'ux_courses_title_active'
            )
                DROP INDEX ux_courses_title_active ON courses;

            ALTER TABLE courses
                ADD CONSTRAINT uq_courses_course_code_normalized
                UNIQUE (course_code_normalized);
            ALTER TABLE courses
                ADD CONSTRAINT uq_courses_title_normalized
                UNIQUE (title_normalized);
        """
            )
        )
    else:
        with op.batch_alter_table("courses", schema=None) as batch_op:
            batch_op.drop_index("ux_courses_course_code_active")
            batch_op.drop_index("ux_courses_title_active")
