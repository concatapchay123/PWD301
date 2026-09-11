"""0003_add_critical_invariant_triggers

Revision ID: f1a2b3c4d5e6
Revises: e8f9a1b2c3d4
Create Date: 2026-09-11 00:00:00.000000

Adds the 12 non-negotiable invariant T-SQL triggers from
docs/database/PWD301_DATABASE_ARCHITECTURE/sql/012_critical_invariant_triggers.sql:
1. trg_assessments_timing_immutable
2. trg_assessment_assignments_structure_lock
3. trg_assessment_pool_structure_lock
4. trg_assessment_sections_structure_lock
5. trg_blueprint_rules_structure_lock
6. trg_question_revision_content_immutable_after_use
7. trg_question_choice_revision_lock
8. trg_question_accepted_answer_revision_lock
9. trg_question_type_lock_after_answered
10. trg_file_revisions_current_active
11. trg_knowledge_versions_current_active
12. trg_audit_events_append_only
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "f1a2b3c4d5e6"
down_revision = "e8f9a1b2c3d4"
branch_labels = None
depends_on = None

TRIGGERS_MSSQL: list[tuple[str, str]] = [
    (
        "trg_assessments_timing_immutable",
        """
CREATE OR ALTER TRIGGER trg_assessments_timing_immutable
ON assessments
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    -- 1. Structure Timing is strictly immutable once published or started
    IF EXISTS (
        SELECT 1
        FROM inserted i
        JOIN deleted d ON d.id = i.id
        WHERE (
              d.published_at IS NOT NULL
              AND (
                  i.published_at IS NULL
               OR i.published_at <> d.published_at
               OR ISNULL(i.open_at, CONVERT(DATETIME2(3),'1900-01-01')) <> ISNULL(d.open_at, CONVERT(DATETIME2(3),'1900-01-01'))
               OR ISNULL(i.time_limit_minutes,-1) <> ISNULL(d.time_limit_minutes,-1)
              )
          )
           OR (
              d.first_attempt_started_at IS NOT NULL
              AND (i.first_attempt_started_at IS NULL OR i.first_attempt_started_at <> d.first_attempt_started_at)
          )
    )
        THROW 51001, 'Assessment publish/first-start markers and structure timing (open_at, time_limit) are immutable once set.', 1;

    -- 2. Window Timing (close_at): only forward extension allowed once published; shortening or terminal modification is forbidden
    IF EXISTS (
        SELECT 1
        FROM inserted i
        JOIN deleted d ON d.id = i.id
        WHERE d.published_at IS NOT NULL
          AND (
              (d.status IN ('ARCHIVED','CANCELLED','TRASH') AND ISNULL(i.close_at, CONVERT(DATETIME2(3),'1900-01-01')) <> ISNULL(d.close_at, CONVERT(DATETIME2(3),'1900-01-01')))
              OR (d.close_at IS NOT NULL AND i.close_at IS NULL)
              OR (d.close_at IS NOT NULL AND i.close_at IS NOT NULL AND i.close_at < d.close_at)
          )
    )
        THROW 51007, 'Assessment close_at can only be extended forward into the future after publish.', 1;
END;
        """,
    ),
    (
        "trg_assessment_assignments_structure_lock",
        """
CREATE OR ALTER TRIGGER trg_assessment_assignments_structure_lock
ON assessment_question_assignments
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (
        SELECT 1 FROM (
            SELECT assessment_id FROM inserted
            UNION
            SELECT assessment_id FROM deleted
        ) x
        JOIN assessments a ON a.id = x.assessment_id
        WHERE a.first_attempt_started_at IS NOT NULL
    )
        THROW 51002, 'Assessment question assignments are locked after the first attempt starts.', 1;
END;
        """,
    ),
    (
        "trg_assessment_pool_structure_lock",
        """
CREATE OR ALTER TRIGGER trg_assessment_pool_structure_lock
ON assessment_question_pool
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (
        SELECT 1 FROM (
            SELECT assessment_id FROM inserted
            UNION
            SELECT assessment_id FROM deleted
        ) x
        JOIN assessments a ON a.id = x.assessment_id
        WHERE a.first_attempt_started_at IS NOT NULL
    )
        THROW 51003, 'Assessment question pool is locked after the first attempt starts.', 1;
END;
        """,
    ),
    (
        "trg_assessment_sections_structure_lock",
        """
CREATE OR ALTER TRIGGER trg_assessment_sections_structure_lock
ON assessment_sections
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (
        SELECT 1 FROM (
            SELECT assessment_id FROM inserted
            UNION
            SELECT assessment_id FROM deleted
        ) x
        JOIN assessments a ON a.id = x.assessment_id
        WHERE a.first_attempt_started_at IS NOT NULL
    )
        THROW 51004, 'Assessment sections are locked after the first attempt starts.', 1;
END;
        """,
    ),
    (
        "trg_blueprint_rules_structure_lock",
        """
CREATE OR ALTER TRIGGER trg_blueprint_rules_structure_lock
ON assessment_blueprint_rules
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (
        SELECT 1
        FROM (
            SELECT blueprint_id FROM inserted
            UNION
            SELECT blueprint_id FROM deleted
        ) x
        JOIN assessment_blueprints b ON b.id = x.blueprint_id
        JOIN assessments a ON a.id = b.assessment_id
        WHERE a.first_attempt_started_at IS NOT NULL
    )
        THROW 51005, 'Assessment blueprint rules are locked after the first attempt starts.', 1;
END;
        """,
    ),
    (
        "trg_question_revision_content_immutable_after_use",
        """
CREATE OR ALTER TRIGGER trg_question_revision_content_immutable_after_use
ON question_revisions
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (
        SELECT 1
        FROM inserted i
        JOIN deleted d ON d.id = i.id
        JOIN questions q ON q.id = i.question_id
        WHERE q.first_used_at IS NOT NULL
          AND (
              ISNULL(i.question_type,'') <> ISNULL(d.question_type,'')
           OR ISNULL(i.content,N'') <> ISNULL(d.content,N'')
           OR ISNULL(i.explanation,N'') <> ISNULL(d.explanation,N'')
           OR ISNULL(i.short_answer_match_mode,'') <> ISNULL(d.short_answer_match_mode,'')
          )
    )
        THROW 51006, 'Used question revisions are immutable; create a new revision.', 1;
END;
        """,
    ),
    (
        "trg_question_choice_revision_lock",
        """
CREATE OR ALTER TRIGGER trg_question_choice_revision_lock
ON question_revision_choices
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (
        SELECT 1
        FROM (
            SELECT question_revision_id FROM inserted
            UNION
            SELECT question_revision_id FROM deleted
        ) x
        JOIN question_revisions qr ON qr.id = x.question_revision_id
        JOIN questions q ON q.id = qr.question_id
        WHERE qr.was_student_exposed = 1
           OR qr.was_used_for_grading = 1
           OR (q.first_used_at IS NOT NULL AND qr.is_current = 1)
    )
        THROW 51007, 'Choices of an activated/used revision are immutable; create a new revision.', 1;
END;
        """,
    ),
    (
        "trg_question_accepted_answer_revision_lock",
        """
CREATE OR ALTER TRIGGER trg_question_accepted_answer_revision_lock
ON question_revision_accepted_answers
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (
        SELECT 1
        FROM (
            SELECT question_revision_id FROM inserted
            UNION
            SELECT question_revision_id FROM deleted
        ) x
        JOIN question_revisions qr ON qr.id = x.question_revision_id
        JOIN questions q ON q.id = qr.question_id
        WHERE qr.was_student_exposed = 1
           OR qr.was_used_for_grading = 1
           OR (q.first_used_at IS NOT NULL AND qr.is_current = 1)
    )
        THROW 51008, 'Accepted answers of an activated/used revision are immutable; create a new revision.', 1;
END;
        """,
    ),
    (
        "trg_question_type_lock_after_answered",
        """
CREATE OR ALTER TRIGGER trg_question_type_lock_after_answered
ON question_revisions
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (
        SELECT 1
        FROM inserted i
        JOIN questions q ON q.id = i.question_id
        JOIN question_revisions prior ON prior.question_id = q.id AND prior.id <> i.id
        WHERE q.first_answered_at IS NOT NULL
          AND i.is_current = 1
          AND prior.question_type <> i.question_type
    )
        THROW 51009, 'Question type cannot change after any student has answered it.', 1;
END;
        """,
    ),
    (
        "trg_file_revisions_current_active",
        """
CREATE OR ALTER TRIGGER trg_file_revisions_current_active
ON file_revisions
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (
        SELECT 1
        FROM inserted i
        WHERE i.is_current = 1
          AND i.status <> 'ACTIVE'
    )
        THROW 51010, 'Current file revision must have status ACTIVE.', 1;
END;
        """,
    ),
    (
        "trg_knowledge_versions_current_active",
        """
CREATE OR ALTER TRIGGER trg_knowledge_versions_current_active
ON knowledge_versions
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (
        SELECT 1
        FROM inserted i
        WHERE i.is_current = 1
          AND i.status <> 'ACTIVE'
    )
        THROW 51011, 'Current knowledge version must have status ACTIVE.', 1;
END;
        """,
    ),
    (
        "trg_audit_events_append_only",
        """
CREATE OR ALTER TRIGGER trg_audit_events_append_only
ON audit_events
INSTEAD OF UPDATE, DELETE
AS
BEGIN
    THROW 51012, 'Audit events are append-only. Corrections must be new events.', 1;
END;
        """,
    ),
]


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "mssql":
        for _name, ddl in TRIGGERS_MSSQL:
            op.execute(ddl.strip())


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "mssql":
        for name, _ddl in reversed(TRIGGERS_MSSQL):
            op.execute(f"DROP TRIGGER IF EXISTS {name};")
