/*
PWD301 Database Architecture — Reference DDL
Engine: Microsoft SQL Server
All DATETIME2 values are UTC by application convention.
This is reference architecture, not evidence that migrations have been executed.
*/
SET XACT_ABORT ON;
GO

CREATE TABLE assessment_attempts (
    id BIGINT IDENTITY(1,1) NOT NULL,
    public_id UNIQUEIDENTIFIER NOT NULL DEFAULT (NEWSEQUENTIALID()),
    assessment_id BIGINT NOT NULL,
    enrollment_period_id BIGINT NOT NULL,
    student_user_id BIGINT NOT NULL,
    attempt_number INT NOT NULL,
    status VARCHAR(28) NOT NULL,
    started_at DATETIME2(3) NULL,
    deadline_at DATETIME2(3) NULL,
    submitted_at DATETIME2(3) NULL,
    finalized_at DATETIME2(3) NULL,
    graded_at DATETIME2(3) NULL,
    submission_idempotency_key UNIQUEIDENTIFIER NULL,
    editor_session_id BIGINT NULL,
    lease_token_hash BINARY(32) NULL,
    lease_acquired_at DATETIME2(3) NULL,
    lease_expires_at DATETIME2(3) NULL,
    last_heartbeat_at DATETIME2(3) NULL,
    cancel_reason NVARCHAR(1000) NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    updated_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    row_version ROWVERSION,
    CONSTRAINT pk_assessment_attempts PRIMARY KEY (id),
    CONSTRAINT uq_assessment_attempts_public_id_1 UNIQUE (public_id),
    CONSTRAINT uq_assessment_attempts_assessment_id_student_user_id_attempt_number_2 UNIQUE (assessment_id, student_user_id, attempt_number),
    CONSTRAINT ck_assessment_attempts_1 CHECK (attempt_number > 0),
    CONSTRAINT ck_assessment_attempts_2 CHECK (status IN ('CREATED','IN_PROGRESS','SUBMITTED','EXPIRED','CANCELLED','PENDING_GRADING','GRADED')),
    CONSTRAINT ck_assessment_attempts_3 CHECK (deadline_at IS NULL OR started_at IS NULL OR deadline_at >= started_at),
    CONSTRAINT fk_assessment_attempts_assessment_id FOREIGN KEY (assessment_id) REFERENCES assessments (id),
    CONSTRAINT fk_assessment_attempts_enrollment_period_id FOREIGN KEY (enrollment_period_id) REFERENCES enrollment_periods (id),
    CONSTRAINT fk_assessment_attempts_student_user_id FOREIGN KEY (student_user_id) REFERENCES users (id),
    CONSTRAINT fk_assessment_attempts_editor_session_id FOREIGN KEY (editor_session_id) REFERENCES auth_sessions (id) ON DELETE SET NULL
);
GO

CREATE TABLE attempt_questions (
    id BIGINT IDENTITY(1,1) NOT NULL,
    attempt_id BIGINT NOT NULL,
    source_question_id BIGINT NOT NULL,
    source_question_revision_id BIGINT NOT NULL,
    section_id BIGINT NULL,
    position INT NOT NULL,
    question_type_snapshot VARCHAR(24) NOT NULL,
    content_snapshot NVARCHAR(MAX) NOT NULL,
    explanation_snapshot NVARCHAR(MAX) NULL,
    points_assigned DECIMAL(9,4) NOT NULL,
    choice_shuffle_applied BIT NOT NULL DEFAULT (0),
    question_changed_after_start_at DATETIME2(3) NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT pk_attempt_questions PRIMARY KEY (id),
    CONSTRAINT uq_attempt_questions_attempt_id_position_1 UNIQUE (attempt_id, position),
    CONSTRAINT uq_attempt_questions_attempt_id_source_question_id_2 UNIQUE (attempt_id, source_question_id),
    CONSTRAINT ck_attempt_questions_1 CHECK (position > 0),
    CONSTRAINT ck_attempt_questions_2 CHECK (points_assigned > 0),
    CONSTRAINT ck_attempt_questions_3 CHECK (question_type_snapshot IN ('SINGLE_CHOICE','MULTIPLE_CHOICE','TRUE_FALSE','SHORT_ANSWER','ESSAY')),
    CONSTRAINT fk_attempt_questions_attempt_id FOREIGN KEY (attempt_id) REFERENCES assessment_attempts (id),
    CONSTRAINT fk_attempt_questions_source_question_id FOREIGN KEY (source_question_id) REFERENCES questions (id),
    CONSTRAINT fk_attempt_questions_source_question_revision_id FOREIGN KEY (source_question_revision_id) REFERENCES question_revisions (id),
    CONSTRAINT fk_attempt_questions_section_id FOREIGN KEY (section_id) REFERENCES assessment_sections (id) ON DELETE SET NULL
);
GO

CREATE TABLE attempt_choice_snapshots (
    id BIGINT IDENTITY(1,1) NOT NULL,
    attempt_question_id BIGINT NOT NULL,
    source_choice_id BIGINT NULL,
    choice_key_snapshot UNIQUEIDENTIFIER NOT NULL,
    content_snapshot NVARCHAR(MAX) NOT NULL,
    position INT NOT NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT pk_attempt_choice_snapshots PRIMARY KEY (id),
    CONSTRAINT uq_attempt_choice_snapshots_attempt_question_id_position_1 UNIQUE (attempt_question_id, position),
    CONSTRAINT uq_attempt_choice_snapshots_attempt_question_id_choice_key_snapshot_2 UNIQUE (attempt_question_id, choice_key_snapshot),
    CONSTRAINT ck_attempt_choice_snapshots_1 CHECK (position > 0),
    CONSTRAINT fk_attempt_choice_snapshots_attempt_question_id FOREIGN KEY (attempt_question_id) REFERENCES attempt_questions (id),
    CONSTRAINT fk_attempt_choice_snapshots_source_choice_id FOREIGN KEY (source_choice_id) REFERENCES question_revision_choices (id) ON DELETE SET NULL
);
GO

CREATE TABLE attempt_answers (
    id BIGINT IDENTITY(1,1) NOT NULL,
    attempt_question_id BIGINT NOT NULL,
    answer_text NVARCHAR(MAX) NULL,
    answer_version BIGINT NOT NULL DEFAULT (0),
    last_client_sequence BIGINT NOT NULL DEFAULT (0),
    last_change_id UNIQUEIDENTIFIER NULL,
    saved_at DATETIME2(3) NULL,
    row_version ROWVERSION,
    CONSTRAINT pk_attempt_answers PRIMARY KEY (id),
    CONSTRAINT uq_attempt_answers_attempt_question_id_1 UNIQUE (attempt_question_id),
    CONSTRAINT ck_attempt_answers_1 CHECK (answer_version >= 0),
    CONSTRAINT ck_attempt_answers_2 CHECK (last_client_sequence >= 0),
    CONSTRAINT fk_attempt_answers_attempt_question_id FOREIGN KEY (attempt_question_id) REFERENCES attempt_questions (id)
);
GO

CREATE TABLE attempt_answer_choices (
    attempt_answer_id BIGINT NOT NULL,
    attempt_choice_snapshot_id BIGINT NOT NULL,
    CONSTRAINT pk_attempt_answer_choices PRIMARY KEY (attempt_answer_id, attempt_choice_snapshot_id),
    CONSTRAINT fk_attempt_answer_choices_attempt_answer_id FOREIGN KEY (attempt_answer_id) REFERENCES attempt_answers (id),
    CONSTRAINT fk_attempt_answer_choices_attempt_choice_snapshot_id FOREIGN KEY (attempt_choice_snapshot_id) REFERENCES attempt_choice_snapshots (id)
);
GO

CREATE TABLE attempt_answer_events (
    id BIGINT IDENTITY(1,1) NOT NULL,
    attempt_question_id BIGINT NOT NULL,
    change_id UNIQUEIDENTIFIER NOT NULL,
    client_sequence BIGINT NOT NULL,
    server_answer_version BIGINT NULL,
    payload_json NVARCHAR(MAX) NOT NULL,
    received_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    accepted BIT NOT NULL DEFAULT (0),
    rejection_reason VARCHAR(40) NULL,
    CONSTRAINT pk_attempt_answer_events PRIMARY KEY (id),
    CONSTRAINT uq_attempt_answer_events_attempt_question_id_change_id_1 UNIQUE (attempt_question_id, change_id),
    CONSTRAINT ck_attempt_answer_events_1 CHECK (client_sequence >= 0),
    CONSTRAINT ck_attempt_answer_events_2 CHECK (payload_json IS NOT NULL AND ISJSON(payload_json)=1),
    CONSTRAINT ck_attempt_answer_events_3 CHECK (rejection_reason IS NULL OR rejection_reason IN ('STALE','LEASE_INVALID','AFTER_DEADLINE','INVALID_PAYLOAD')),
    CONSTRAINT fk_attempt_answer_events_attempt_question_id FOREIGN KEY (attempt_question_id) REFERENCES attempt_questions (id)
);
GO

CREATE TABLE attempt_question_grades (
    attempt_question_id BIGINT NOT NULL,
    awarded_points DECIMAL(9,4) NOT NULL DEFAULT (0),
    grading_status VARCHAR(20) NOT NULL,
    grading_rule VARCHAR(32) NOT NULL,
    graded_against_revision_id BIGINT NULL,
    graded_by_user_id BIGINT NULL,
    graded_at DATETIME2(3) NULL,
    manual_reason NVARCHAR(1000) NULL,
    row_version ROWVERSION,
    CONSTRAINT pk_attempt_question_grades PRIMARY KEY (attempt_question_id),
    CONSTRAINT ck_attempt_question_grades_1 CHECK (awarded_points >= 0),
    CONSTRAINT ck_attempt_question_grades_2 CHECK (grading_status IN ('PENDING','AUTO_GRADED','MANUAL_GRADED','FULL_CREDIT')),
    CONSTRAINT ck_attempt_question_grades_3 CHECK (grading_rule IN ('ORIGINAL','ANSWER_CORRECTION','CONTENT_FULL_CREDIT','MANUAL')),
    CONSTRAINT fk_attempt_question_grades_attempt_question_id FOREIGN KEY (attempt_question_id) REFERENCES attempt_questions (id),
    CONSTRAINT fk_attempt_question_grades_graded_against_revision_id FOREIGN KEY (graded_against_revision_id) REFERENCES question_revisions (id) ON DELETE SET NULL,
    CONSTRAINT fk_attempt_question_grades_graded_by_user_id FOREIGN KEY (graded_by_user_id) REFERENCES users (id) ON DELETE SET NULL
);
GO

CREATE TABLE attempt_question_grade_history (
    id BIGINT IDENTITY(1,1) NOT NULL,
    attempt_question_id BIGINT NOT NULL,
    old_points DECIMAL(9,4) NULL,
    new_points DECIMAL(9,4) NOT NULL,
    reason_code VARCHAR(32) NOT NULL,
    reason NVARCHAR(1000) NULL,
    actor_user_id BIGINT NULL,
    question_correction_id BIGINT NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT pk_attempt_question_grade_history PRIMARY KEY (id),
    CONSTRAINT ck_attempt_question_grade_history_1 CHECK (new_points >= 0),
    CONSTRAINT ck_attempt_question_grade_history_2 CHECK (reason_code IN ('INITIAL','AUTO_REGRADE','FULL_CREDIT','MANUAL_REVISION')),
    CONSTRAINT fk_attempt_question_grade_history_attempt_question_id FOREIGN KEY (attempt_question_id) REFERENCES attempt_questions (id),
    CONSTRAINT fk_attempt_question_grade_history_actor_user_id FOREIGN KEY (actor_user_id) REFERENCES users (id) ON DELETE SET NULL
);
GO

CREATE TABLE assessment_results (
    attempt_id BIGINT NOT NULL,
    raw_score DECIMAL(12,4) NOT NULL DEFAULT (0),
    max_score DECIMAL(12,4) NOT NULL,
    percent_score DECIMAL(7,4) NULL,
    passed BIT NULL,
    status VARCHAR(20) NOT NULL DEFAULT ('PENDING'),
    released_at DATETIME2(3) NULL,
    graded_at DATETIME2(3) NULL,
    updated_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    row_version ROWVERSION,
    CONSTRAINT pk_assessment_results PRIMARY KEY (attempt_id),
    CONSTRAINT ck_assessment_results_1 CHECK (raw_score >= 0),
    CONSTRAINT ck_assessment_results_2 CHECK (max_score > 0),
    CONSTRAINT ck_assessment_results_3 CHECK (percent_score IS NULL OR (percent_score >= 0 AND percent_score <= 100)),
    CONSTRAINT ck_assessment_results_4 CHECK (status IN ('PENDING','FINAL','RELEASED')),
    CONSTRAINT fk_assessment_results_attempt_id FOREIGN KEY (attempt_id) REFERENCES assessment_attempts (id)
);
GO

CREATE TABLE assessment_result_history (
    id BIGINT IDENTITY(1,1) NOT NULL,
    attempt_id BIGINT NOT NULL,
    old_score DECIMAL(12,4) NULL,
    new_score DECIMAL(12,4) NOT NULL,
    old_percent DECIMAL(7,4) NULL,
    new_percent DECIMAL(7,4) NULL,
    reason_code VARCHAR(32) NOT NULL,
    reason NVARCHAR(1000) NOT NULL,
    actor_user_id BIGINT NULL,
    regrade_job_id BIGINT NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT pk_assessment_result_history PRIMARY KEY (id),
    CONSTRAINT ck_assessment_result_history_1 CHECK (new_score >= 0),
    CONSTRAINT ck_assessment_result_history_2 CHECK (reason_code IN ('INITIAL','REGRADE','MANUAL','CORRECTION')),
    CONSTRAINT fk_assessment_result_history_attempt_id FOREIGN KEY (attempt_id) REFERENCES assessment_attempts (id),
    CONSTRAINT fk_assessment_result_history_actor_user_id FOREIGN KEY (actor_user_id) REFERENCES users (id) ON DELETE SET NULL
);
GO

CREATE TABLE question_corrections (
    id BIGINT IDENTITY(1,1) NOT NULL,
    question_id BIGINT NOT NULL,
    from_revision_id BIGINT NOT NULL,
    to_revision_id BIGINT NOT NULL,
    correction_type VARCHAR(24) NOT NULL,
    effective_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    reason NVARCHAR(1000) NOT NULL,
    actor_user_id BIGINT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT ('PENDING'),
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT pk_question_corrections PRIMARY KEY (id),
    CONSTRAINT uq_question_corrections_to_revision_id_1 UNIQUE (to_revision_id),
    CONSTRAINT ck_question_corrections_1 CHECK (correction_type IN ('ANSWER_ONLY','CONTENT_OR_CHOICES')),
    CONSTRAINT ck_question_corrections_2 CHECK (status IN ('PENDING','RUNNING','APPLIED','FAILED','SUPERSEDED')),
    CONSTRAINT fk_question_corrections_question_id FOREIGN KEY (question_id) REFERENCES questions (id),
    CONSTRAINT fk_question_corrections_from_revision_id FOREIGN KEY (from_revision_id) REFERENCES question_revisions (id),
    CONSTRAINT fk_question_corrections_to_revision_id FOREIGN KEY (to_revision_id) REFERENCES question_revisions (id),
    CONSTRAINT fk_question_corrections_actor_user_id FOREIGN KEY (actor_user_id) REFERENCES users (id)
);
GO

CREATE TABLE regrade_jobs (
    id BIGINT IDENTITY(1,1) NOT NULL,
    question_correction_id BIGINT NOT NULL,
    background_job_id BIGINT NULL,
    status VARCHAR(20) NOT NULL DEFAULT ('QUEUED'),
    total_items INT NOT NULL DEFAULT (0),
    processed_items INT NOT NULL DEFAULT (0),
    changed_results INT NOT NULL DEFAULT (0),
    started_at DATETIME2(3) NULL,
    completed_at DATETIME2(3) NULL,
    last_error NVARCHAR(2000) NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    row_version ROWVERSION,
    CONSTRAINT pk_regrade_jobs PRIMARY KEY (id),
    CONSTRAINT uq_regrade_jobs_question_correction_id_1 UNIQUE (question_correction_id),
    CONSTRAINT ck_regrade_jobs_1 CHECK (status IN ('QUEUED','RUNNING','PARTIAL','COMPLETED','FAILED','CANCELLED')),
    CONSTRAINT ck_regrade_jobs_2 CHECK (total_items >= 0),
    CONSTRAINT ck_regrade_jobs_3 CHECK (processed_items >= 0),
    CONSTRAINT ck_regrade_jobs_4 CHECK (changed_results >= 0),
    CONSTRAINT fk_regrade_jobs_question_correction_id FOREIGN KEY (question_correction_id) REFERENCES question_corrections (id)
);
GO

CREATE TABLE regrade_items (
    id BIGINT IDENTITY(1,1) NOT NULL,
    regrade_job_id BIGINT NOT NULL,
    attempt_id BIGINT NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT ('PENDING'),
    old_score DECIMAL(12,4) NULL,
    new_score DECIMAL(12,4) NULL,
    skip_reason VARCHAR(40) NULL,
    attempt_count INT NOT NULL DEFAULT (0),
    processed_at DATETIME2(3) NULL,
    last_error NVARCHAR(2000) NULL,
    row_version ROWVERSION,
    CONSTRAINT pk_regrade_items PRIMARY KEY (id),
    CONSTRAINT uq_regrade_items_regrade_job_id_attempt_id_1 UNIQUE (regrade_job_id, attempt_id),
    CONSTRAINT ck_regrade_items_1 CHECK (status IN ('PENDING','PROCESSING','COMPLETED','SKIPPED','FAILED')),
    CONSTRAINT ck_regrade_items_2 CHECK (skip_reason IS NULL OR skip_reason IN ('DETAIL_PURGED','NOT_AFFECTED','CANCELLED')),
    CONSTRAINT ck_regrade_items_3 CHECK (attempt_count >= 0),
    CONSTRAINT fk_regrade_items_regrade_job_id FOREIGN KEY (regrade_job_id) REFERENCES regrade_jobs (id),
    CONSTRAINT fk_regrade_items_attempt_id FOREIGN KEY (attempt_id) REFERENCES assessment_attempts (id)
);
GO
