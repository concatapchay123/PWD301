/*
PWD301 Database Architecture — Reference DDL
Engine: Microsoft SQL Server
All DATETIME2 values are UTC by application convention.
This is reference architecture, not evidence that migrations have been executed.
*/
SET XACT_ABORT ON;
GO


/* Critical invariants that cannot be expressed with ordinary CHECK/FK constraints.
   Application services MUST still validate the same rules for friendly errors. */

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
GO

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
GO

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
GO

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
GO

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
GO

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
GO

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
           OR (q.first_used_at IS NOT NULL AND q.current_revision_id = qr.id)
    )
        THROW 51007, 'Choices of an activated/used revision are immutable; create a new revision.', 1;
END;
GO

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
           OR (q.first_used_at IS NOT NULL AND q.current_revision_id = qr.id)
    )
        THROW 51008, 'Accepted answers of an activated/used revision are immutable; create a new revision.', 1;
END;
GO

CREATE OR ALTER TRIGGER trg_question_type_lock_after_answered
ON questions
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (
        SELECT 1
        FROM inserted i
        JOIN deleted d ON d.id = i.id
        JOIN question_revisions oldr ON oldr.id = d.current_revision_id
        JOIN question_revisions newr ON newr.id = i.current_revision_id
        WHERE i.first_answered_at IS NOT NULL
          AND ISNULL(i.current_revision_id,0) <> ISNULL(d.current_revision_id,0)
          AND oldr.question_type <> newr.question_type
    )
        THROW 51009, 'Question type cannot change after any student has answered it.', 1;
END;
GO

CREATE OR ALTER TRIGGER trg_file_asset_current_revision_safe
ON file_assets
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (
        SELECT 1
        FROM inserted i
        JOIN file_revisions fr ON fr.id = i.current_revision_id
        WHERE i.current_revision_id IS NOT NULL
          AND (fr.file_asset_id <> i.id OR fr.status <> 'ACTIVE')
    )
        THROW 51010, 'Current file revision must belong to the asset and be ACTIVE.', 1;
END;
GO

CREATE OR ALTER TRIGGER trg_knowledge_document_current_version_active
ON knowledge_documents
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (
        SELECT 1
        FROM inserted i
        JOIN knowledge_versions kv ON kv.id = i.current_version_id
        WHERE i.current_version_id IS NOT NULL
          AND (kv.knowledge_document_id <> i.id OR kv.status <> 'ACTIVE')
    )
        THROW 51011, 'Current knowledge version must belong to the document and be ACTIVE.', 1;
END;
GO

CREATE OR ALTER TRIGGER trg_audit_events_append_only
ON audit_events
INSTEAD OF UPDATE, DELETE
AS
BEGIN
    THROW 51012, 'Audit events are append-only. Corrections must be new events.', 1;
END;
GO
