"""Repair deployed staging checks and enforce one active course changeset.

Revision ID: unifiedcourse20261015
Revises: allowresults20261014
"""

import sqlalchemy as sa
from alembic import op

revision = "unifiedcourse20261015"
down_revision = "allowresults20261014"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    duplicates = connection.execute(sa.text(
        "SELECT course_id FROM course_change_requests "
        "WHERE change_type='COURSE_VERSION_CHANGESET' AND status IN ('DRAFT','PENDING') "
        "GROUP BY course_id HAVING COUNT(*) > 1"
    )).first()
    if duplicates is not None:
        raise RuntimeError("Reconcile duplicate active course changesets before migrating; no proposals were deleted.")
    with op.batch_alter_table("course_change_requests") as batch:
        batch.drop_constraint("ck_course_change_requests_1", type_="check")
        batch.drop_constraint("ck_course_change_requests_3", type_="check")
        batch.create_check_constraint(
            "ck_course_change_requests_1",
            "change_type IN ('COURSE_METADATA','LESSON_STRUCTURE','LESSON_CONTENT','COMPLETION_RULE','PREREQUISITE','OTHER','COURSE_VERSION_CHANGESET')",
        )
        batch.create_check_constraint(
            "ck_course_change_requests_3",
            "status IN ('DRAFT','PENDING','APPROVED','REJECTED','CANCELLED','APPLIED')",
        )
    insp = sa.inspect(connection)
    lu_cols = [c["name"] for c in insp.get_columns("learning_units")]
    if "change_request_id" not in lu_cols:
        with op.batch_alter_table("learning_units") as batch:
            batch.add_column(sa.Column("change_request_id", sa.BigInteger(), nullable=True))
            batch.create_foreign_key("fk_learning_units_change_request_id", "course_change_requests", ["change_request_id"], ["id"])
    
    asm_cols = [c["name"] for c in insp.get_columns("assessments")]
    with op.batch_alter_table("assessments") as batch:
        if "change_request_id" not in asm_cols:
            batch.add_column(sa.Column("change_request_id", sa.BigInteger(), nullable=True))
            batch.create_foreign_key("fk_assessments_change_request_id", "course_change_requests", ["change_request_id"], ["id"])
        if "previous_assessment_id" not in asm_cols:
            batch.add_column(sa.Column("previous_assessment_id", sa.BigInteger(), nullable=True))
            batch.create_foreign_key("fk_assessments_previous_assessment_id", "assessments", ["previous_assessment_id"], ["id"])
            
    q_cols = [c["name"] for c in insp.get_columns("questions")]
    with op.batch_alter_table("questions") as batch:
        if "change_request_id" not in q_cols:
            batch.add_column(sa.Column("change_request_id", sa.BigInteger(), nullable=True))
            batch.create_foreign_key("fk_questions_change_request_id", "course_change_requests", ["change_request_id"], ["id"])
        if "previous_question_id" not in q_cols:
            batch.add_column(sa.Column("previous_question_id", sa.BigInteger(), nullable=True))
            batch.create_foreign_key("fk_questions_previous_question_id", "questions", ["previous_question_id"], ["id"])
    op.create_index(
        "uq_course_changeset_active", "course_change_requests", ["course_id"], unique=True,
        mssql_where=sa.text("change_type='COURSE_VERSION_CHANGESET' AND status IN ('DRAFT','PENDING')"),
        sqlite_where=sa.text("change_type='COURSE_VERSION_CHANGESET' AND status IN ('DRAFT','PENDING')"),
    )
    op.create_index("ux_questions_working_revision", "questions", ["change_request_id", "previous_question_id"], unique=True,
        mssql_where=sa.text("change_request_id IS NOT NULL AND previous_question_id IS NOT NULL"),
        sqlite_where=sa.text("change_request_id IS NOT NULL AND previous_question_id IS NOT NULL"))


def downgrade():
    connection = op.get_bind()
    if connection.execute(sa.text(
        "SELECT id FROM course_change_requests WHERE change_type='COURSE_VERSION_CHANGESET' OR status='DRAFT'"
    )).first() is not None:
        raise RuntimeError("Cannot downgrade while staging/history uses the repaired contract; preserve review evidence.")
    if connection.dialect.name == "mssql":
        # The prior applied migration omitted SQL Server's generated DEFAULT on reverse.
        connection.execute(sa.text("""
            DECLARE @default_name sysname;
            SELECT @default_name = dc.name
            FROM sys.default_constraints dc
            JOIN sys.columns c ON c.object_id=dc.parent_object_id
                AND c.column_id=dc.parent_column_id
            WHERE dc.parent_object_id=OBJECT_ID(N'dbo.assessments')
                AND c.name=N'allow_student_view_results';
            IF @default_name IS NOT NULL
            BEGIN
                DECLARE @drop_default nvarchar(1000);
                SET @drop_default=N'ALTER TABLE dbo.assessments DROP CONSTRAINT ' + QUOTENAME(@default_name);
                EXEC sp_executesql @drop_default;
            END;
        """))
    op.drop_index("uq_course_changeset_active", table_name="course_change_requests")
    op.drop_index("ux_questions_working_revision", table_name="questions")
    with op.batch_alter_table("questions") as batch:
        batch.drop_constraint("fk_questions_previous_question_id", type_="foreignkey")
        batch.drop_constraint("fk_questions_change_request_id", type_="foreignkey")
        batch.drop_column("previous_question_id")
        batch.drop_column("change_request_id")
    with op.batch_alter_table("assessments") as batch:
        batch.drop_constraint("fk_assessments_previous_assessment_id", type_="foreignkey")
        batch.drop_constraint("fk_assessments_change_request_id", type_="foreignkey")
        batch.drop_column("previous_assessment_id")
        batch.drop_column("change_request_id")
    with op.batch_alter_table("learning_units") as batch:
        batch.drop_constraint("fk_learning_units_change_request_id", type_="foreignkey")
        batch.drop_column("change_request_id")
    with op.batch_alter_table("course_change_requests") as batch:
        batch.drop_constraint("ck_course_change_requests_1", type_="check")
        batch.drop_constraint("ck_course_change_requests_3", type_="check")
        batch.create_check_constraint("ck_course_change_requests_1", "change_type IN ('COURSE_METADATA','LESSON_STRUCTURE','LESSON_CONTENT','COMPLETION_RULE','PREREQUISITE','OTHER')")
        batch.create_check_constraint("ck_course_change_requests_3", "status IN ('PENDING','APPROVED','REJECTED','CANCELLED','APPLIED')")
