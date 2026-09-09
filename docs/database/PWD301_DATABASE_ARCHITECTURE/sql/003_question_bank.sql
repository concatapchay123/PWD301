/*
PWD301 Database Architecture — Reference DDL
Engine: Microsoft SQL Server
All DATETIME2 values are UTC by application convention.
This is reference architecture, not evidence that migrations have been executed.
*/
SET XACT_ABORT ON;
GO

CREATE TABLE questions (
    id BIGINT IDENTITY(1,1) NOT NULL,
    public_id UNIQUEIDENTIFIER NOT NULL DEFAULT (NEWSEQUENTIALID()),
    course_id BIGINT NOT NULL,
    lesson_id BIGINT NULL,
    creator_user_id BIGINT NULL,
    difficulty VARCHAR(20) NOT NULL,
    learning_objective NVARCHAR(500) NULL,
    status VARCHAR(20) NOT NULL DEFAULT ('DRAFT'),
    current_revision_id BIGINT NULL,
    first_used_at DATETIME2(3) NULL,
    first_answered_at DATETIME2(3) NULL,
    usage_count BIGINT NOT NULL DEFAULT (0),
    last_used_at DATETIME2(3) NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    updated_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    row_version ROWVERSION,
    deleted_at DATETIME2(3) NULL,
    restore_until DATETIME2(3) NULL,
    deleted_by_user_id BIGINT NULL,
    CONSTRAINT pk_questions PRIMARY KEY (id),
    CONSTRAINT uq_questions_public_id_1 UNIQUE (public_id),
    CONSTRAINT ck_questions_1 CHECK (difficulty IN ('REMEMBER','UNDERSTAND','APPLY')),
    CONSTRAINT ck_questions_2 CHECK (status IN ('DRAFT','ACTIVE','RETIRED','TRASH')),
    CONSTRAINT ck_questions_3 CHECK (usage_count >= 0),
    CONSTRAINT fk_questions_course_id FOREIGN KEY (course_id) REFERENCES courses (id),
    CONSTRAINT fk_questions_lesson_id FOREIGN KEY (lesson_id) REFERENCES lessons (id) ON DELETE SET NULL,
    CONSTRAINT fk_questions_creator_user_id FOREIGN KEY (creator_user_id) REFERENCES users (id),
    CONSTRAINT fk_questions_deleted_by_user_id FOREIGN KEY (deleted_by_user_id) REFERENCES users (id)
);
GO

CREATE TABLE question_revisions (
    id BIGINT IDENTITY(1,1) NOT NULL,
    question_id BIGINT NOT NULL,
    revision_no INT NOT NULL,
    question_type VARCHAR(24) NOT NULL,
    content NVARCHAR(MAX) NOT NULL,
    explanation NVARCHAR(MAX) NULL,
    short_answer_match_mode VARCHAR(16) NULL,
    change_type VARCHAR(24) NOT NULL DEFAULT ('EDIT'),
    change_reason NVARCHAR(1000) NULL,
    created_by_user_id BIGINT NULL,
    approved_by_user_id BIGINT NULL,
    approved_at DATETIME2(3) NULL,
    was_student_exposed BIT NOT NULL DEFAULT (0),
    was_used_for_grading BIT NOT NULL DEFAULT (0),
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT pk_question_revisions PRIMARY KEY (id),
    CONSTRAINT uq_question_revisions_question_id_revision_no_1 UNIQUE (question_id, revision_no),
    CONSTRAINT ck_question_revisions_1 CHECK (revision_no > 0),
    CONSTRAINT ck_question_revisions_2 CHECK (question_type IN ('SINGLE_CHOICE','MULTIPLE_CHOICE','TRUE_FALSE','SHORT_ANSWER','ESSAY')),
    CONSTRAINT ck_question_revisions_3 CHECK (short_answer_match_mode IS NULL OR short_answer_match_mode IN ('NORMALIZED','EXACT')),
    CONSTRAINT ck_question_revisions_4 CHECK (change_type IN ('INITIAL','EDIT','ANSWER_ONLY','CONTENT_OR_CHOICES','TYPO_FIX','ANSWER_CHANGE','CONTENT_CHANGE','REVOCATION')),
    CONSTRAINT fk_question_revisions_question_id FOREIGN KEY (question_id) REFERENCES questions (id),
    CONSTRAINT fk_question_revisions_created_by_user_id FOREIGN KEY (created_by_user_id) REFERENCES users (id),
    CONSTRAINT fk_question_revisions_approved_by_user_id FOREIGN KEY (approved_by_user_id) REFERENCES users (id)
);
GO

CREATE TABLE question_revision_choices (
    id BIGINT IDENTITY(1,1) NOT NULL,
    question_revision_id BIGINT NOT NULL,
    choice_key UNIQUEIDENTIFIER NOT NULL DEFAULT (NEWID()),
    content NVARCHAR(MAX) NOT NULL,
    is_correct BIT NOT NULL DEFAULT (0),
    position INT NOT NULL,
    is_fixed_position BIT NOT NULL DEFAULT (0),
    CONSTRAINT pk_question_revision_choices PRIMARY KEY (id),
    CONSTRAINT uq_question_revision_choices_question_revision_id_choice_key_1 UNIQUE (question_revision_id, choice_key),
    CONSTRAINT uq_question_revision_choices_question_revision_id_position_2 UNIQUE (question_revision_id, position),
    CONSTRAINT ck_question_revision_choices_1 CHECK (position > 0),
    CONSTRAINT fk_question_revision_choices_question_revision_id FOREIGN KEY (question_revision_id) REFERENCES question_revisions (id)
);
GO

CREATE TABLE question_revision_accepted_answers (
    id BIGINT IDENTITY(1,1) NOT NULL,
    question_revision_id BIGINT NOT NULL,
    answer_text NVARCHAR(1000) NOT NULL,
    answer_normalized NVARCHAR(1000) NOT NULL,
    position INT NOT NULL DEFAULT (1),
    CONSTRAINT pk_question_revision_accepted_answers PRIMARY KEY (id),
    CONSTRAINT uq_question_revision_accepted_answers_question_revision_id_answer_normalized_1 UNIQUE (question_revision_id, answer_normalized),
    CONSTRAINT ck_question_revision_accepted_answers_1 CHECK (position > 0),
    CONSTRAINT fk_question_revision_accepted_answers_question_revision_id FOREIGN KEY (question_revision_id) REFERENCES question_revisions (id)
);
GO

CREATE TABLE question_provenance (
    id BIGINT IDENTITY(1,1) NOT NULL,
    question_id BIGINT NOT NULL,
    question_revision_id BIGINT NULL,
    source_type VARCHAR(24) NOT NULL,
    source_ref_type VARCHAR(32) NULL,
    source_ref_id BIGINT NULL,
    source_question_id BIGINT NULL,
    ai_model NVARCHAR(100) NULL,
    generated_at DATETIME2(3) NULL,
    approved_by_user_id BIGINT NULL,
    approved_at DATETIME2(3) NULL,
    notes NVARCHAR(1000) NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT pk_question_provenance PRIMARY KEY (id),
    CONSTRAINT ck_question_provenance_1 CHECK (source_type IN ('MANUAL','IMPORT','AI_GENERATED','DUPLICATED')),
    CONSTRAINT fk_question_provenance_question_id FOREIGN KEY (question_id) REFERENCES questions (id),
    CONSTRAINT fk_question_provenance_question_revision_id FOREIGN KEY (question_revision_id) REFERENCES question_revisions (id) ON DELETE SET NULL,
    CONSTRAINT fk_question_provenance_source_question_id FOREIGN KEY (source_question_id) REFERENCES questions (id) ON DELETE SET NULL,
    CONSTRAINT fk_question_provenance_approved_by_user_id FOREIGN KEY (approved_by_user_id) REFERENCES users (id) ON DELETE SET NULL
);
GO
