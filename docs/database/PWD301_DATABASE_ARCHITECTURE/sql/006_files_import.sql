/*
PWD301 Database Architecture — Reference DDL
Engine: Microsoft SQL Server
All DATETIME2 values are UTC by application convention.
This is reference architecture, not evidence that migrations have been executed.
*/
SET XACT_ABORT ON;
GO

CREATE TABLE file_blobs (
    id BIGINT IDENTITY(1,1) NOT NULL,
    sha256 BINARY(32) NOT NULL,
    size_bytes BIGINT NOT NULL,
    detected_mime_type NVARCHAR(150) NOT NULL,
    storage_key NVARCHAR(500) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT ('PRESENT'),
    reference_count INT NOT NULL DEFAULT (0),
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    deleted_at DATETIME2(3) NULL,
    CONSTRAINT pk_file_blobs PRIMARY KEY (id),
    CONSTRAINT uq_file_blobs_sha256_1 UNIQUE (sha256),
    CONSTRAINT uq_file_blobs_storage_key_2 UNIQUE (storage_key),
    CONSTRAINT ck_file_blobs_1 CHECK (size_bytes > 0),
    CONSTRAINT ck_file_blobs_2 CHECK (status IN ('PRESENT','DELETING','DELETED')),
    CONSTRAINT ck_file_blobs_3 CHECK (reference_count >= 0)
);
GO

CREATE TABLE file_assets (
    id BIGINT IDENTITY(1,1) NOT NULL,
    public_id UNIQUEIDENTIFIER NOT NULL DEFAULT (NEWSEQUENTIALID()),
    course_id BIGINT NOT NULL,
    created_by_user_id BIGINT NOT NULL,
    asset_type VARCHAR(24) NOT NULL,
    display_name NVARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT ('PENDING'),
    retention_until DATETIME2(3) NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    updated_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    row_version ROWVERSION,
    deleted_at DATETIME2(3) NULL,
    restore_until DATETIME2(3) NULL,
    deleted_by_user_id BIGINT NULL,
    CONSTRAINT pk_file_assets PRIMARY KEY (id),
    CONSTRAINT uq_file_assets_public_id_1 UNIQUE (public_id),
    CONSTRAINT ck_file_assets_1 CHECK (asset_type IN ('RESOURCE','QUESTION_IMAGE','COURSE_IMAGE','IMPORT_SOURCE','EXPORT','OTHER')),
    CONSTRAINT ck_file_assets_2 CHECK (status IN ('PENDING','ACTIVE','REPLACED','TRASH','HISTORICAL')),
    CONSTRAINT fk_file_assets_course_id FOREIGN KEY (course_id) REFERENCES courses (id),
    CONSTRAINT fk_file_assets_created_by_user_id FOREIGN KEY (created_by_user_id) REFERENCES users (id),
    CONSTRAINT fk_file_assets_deleted_by_user_id FOREIGN KEY (deleted_by_user_id) REFERENCES users (id) ON DELETE SET NULL
);
GO

CREATE TABLE file_revisions (
    id BIGINT IDENTITY(1,1) NOT NULL,
    file_asset_id BIGINT NOT NULL,
    revision_no INT NOT NULL,
    is_current BIT NOT NULL DEFAULT (0),
    blob_id BIGINT NULL,
    original_filename NVARCHAR(255) NOT NULL,
    declared_mime_type NVARCHAR(150) NULL,
    detected_mime_type NVARCHAR(150) NULL,
    size_bytes BIGINT NOT NULL,
    status VARCHAR(24) NOT NULL DEFAULT ('QUARANTINED'),
    uploaded_by_user_id BIGINT NOT NULL,
    quarantine_key NVARCHAR(500) NULL,
    security_checks_completed_at DATETIME2(3) NULL,
    activated_at DATETIME2(3) NULL,
    replaced_at DATETIME2(3) NULL,
    recovery_until DATETIME2(3) NULL,
    rejection_reason NVARCHAR(1000) NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    row_version ROWVERSION,
    CONSTRAINT pk_file_revisions PRIMARY KEY (id),
    CONSTRAINT uq_file_revisions_file_asset_id_revision_no_1 UNIQUE (file_asset_id, revision_no),
    CONSTRAINT ck_file_revisions_1 CHECK (revision_no > 0),
    CONSTRAINT ck_file_revisions_2 CHECK (size_bytes > 0),
    CONSTRAINT ck_file_revisions_3 CHECK (status IN ('QUARANTINED','VALIDATING','SCANNING','SAFE','ACTIVE','REJECTED','REPLACED','RECOVERY','DELETED')),
    CONSTRAINT fk_file_revisions_file_asset_id FOREIGN KEY (file_asset_id) REFERENCES file_assets (id),
    CONSTRAINT fk_file_revisions_blob_id FOREIGN KEY (blob_id) REFERENCES file_blobs (id) ON DELETE SET NULL,
    CONSTRAINT fk_file_revisions_uploaded_by_user_id FOREIGN KEY (uploaded_by_user_id) REFERENCES users (id)
);
GO

CREATE TABLE file_scan_results (
    id BIGINT IDENTITY(1,1) NOT NULL,
    file_revision_id BIGINT NOT NULL,
    scan_type VARCHAR(24) NOT NULL,
    engine NVARCHAR(100) NOT NULL,
    engine_version NVARCHAR(100) NULL,
    status VARCHAR(16) NOT NULL,
    details_json NVARCHAR(MAX) NULL,
    started_at DATETIME2(3) NULL,
    completed_at DATETIME2(3) NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT pk_file_scan_results PRIMARY KEY (id),
    CONSTRAINT ck_file_scan_results_1 CHECK (scan_type IN ('FILE_VALIDATION','MALWARE','STRUCTURE','RESOURCE_LIMIT','CONTENT_SECURITY')),
    CONSTRAINT ck_file_scan_results_2 CHECK (status IN ('PASS','FAIL','ERROR')),
    CONSTRAINT ck_file_scan_results_3 CHECK (details_json IS NULL OR ISJSON(details_json)=1),
    CONSTRAINT fk_file_scan_results_file_revision_id FOREIGN KEY (file_revision_id) REFERENCES file_revisions (id)
);
GO

CREATE TABLE lesson_resources (
    id BIGINT IDENTITY(1,1) NOT NULL,
    lesson_id BIGINT NOT NULL,
    file_asset_id BIGINT NOT NULL,
    position INT NOT NULL DEFAULT (1),
    label NVARCHAR(255) NULL,
    is_required BIT NOT NULL DEFAULT (0),
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT pk_lesson_resources PRIMARY KEY (id),
    CONSTRAINT uq_lesson_resources_lesson_id_file_asset_id_1 UNIQUE (lesson_id, file_asset_id),
    CONSTRAINT uq_lesson_resources_lesson_id_position_2 UNIQUE (lesson_id, position),
    CONSTRAINT ck_lesson_resources_1 CHECK (position > 0),
    CONSTRAINT fk_lesson_resources_lesson_id FOREIGN KEY (lesson_id) REFERENCES lessons (id),
    CONSTRAINT fk_lesson_resources_file_asset_id FOREIGN KEY (file_asset_id) REFERENCES file_assets (id)
);
GO

CREATE TABLE question_revision_resources (
    id BIGINT IDENTITY(1,1) NOT NULL,
    question_revision_id BIGINT NOT NULL,
    file_asset_id BIGINT NOT NULL,
    position INT NOT NULL DEFAULT (1),
    resource_role VARCHAR(20) NOT NULL DEFAULT ('IMAGE'),
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT pk_question_revision_resources PRIMARY KEY (id),
    CONSTRAINT uq_question_revision_resources_question_revision_id_file_asset_id_1 UNIQUE (question_revision_id, file_asset_id),
    CONSTRAINT ck_question_revision_resources_1 CHECK (position > 0),
    CONSTRAINT ck_question_revision_resources_2 CHECK (resource_role IN ('IMAGE','ATTACHMENT')),
    CONSTRAINT fk_question_revision_resources_question_revision_id FOREIGN KEY (question_revision_id) REFERENCES question_revisions (id),
    CONSTRAINT fk_question_revision_resources_file_asset_id FOREIGN KEY (file_asset_id) REFERENCES file_assets (id)
);
GO

CREATE TABLE document_import_jobs (
    id BIGINT IDENTITY(1,1) NOT NULL,
    public_id UNIQUEIDENTIFIER NOT NULL DEFAULT (NEWSEQUENTIALID()),
    course_id BIGINT NOT NULL,
    source_file_asset_id BIGINT NOT NULL,
    requested_by_user_id BIGINT NOT NULL,
    draft_assessment_id BIGINT NULL,
    background_job_id BIGINT NULL,
    document_type VARCHAR(8) NOT NULL,
    status VARCHAR(24) NOT NULL DEFAULT ('QUEUED'),
    parser_version NVARCHAR(100) NOT NULL,
    question_count INT NOT NULL DEFAULT (0),
    review_required_count INT NOT NULL DEFAULT (0),
    started_at DATETIME2(3) NULL,
    completed_at DATETIME2(3) NULL,
    last_error NVARCHAR(2000) NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    row_version ROWVERSION,
    CONSTRAINT pk_document_import_jobs PRIMARY KEY (id),
    CONSTRAINT uq_document_import_jobs_public_id_1 UNIQUE (public_id),
    CONSTRAINT ck_document_import_jobs_1 CHECK (document_type IN ('DOCX','PDF')),
    CONSTRAINT ck_document_import_jobs_2 CHECK (status IN ('QUEUED','PROCESSING','REVIEW_REQUIRED','COMPLETED','FAILED','CANCELLED')),
    CONSTRAINT ck_document_import_jobs_3 CHECK (question_count >= 0),
    CONSTRAINT ck_document_import_jobs_4 CHECK (review_required_count >= 0),
    CONSTRAINT fk_document_import_jobs_course_id FOREIGN KEY (course_id) REFERENCES courses (id),
    CONSTRAINT fk_document_import_jobs_source_file_asset_id FOREIGN KEY (source_file_asset_id) REFERENCES file_assets (id),
    CONSTRAINT fk_document_import_jobs_requested_by_user_id FOREIGN KEY (requested_by_user_id) REFERENCES users (id),
    CONSTRAINT fk_document_import_jobs_draft_assessment_id FOREIGN KEY (draft_assessment_id) REFERENCES assessments (id) ON DELETE SET NULL
);
GO

CREATE TABLE import_questions (
    id BIGINT IDENTITY(1,1) NOT NULL,
    import_job_id BIGINT NOT NULL,
    ordinal INT NOT NULL,
    detected_type VARCHAR(24) NULL,
    content_text NVARCHAR(MAX) NOT NULL,
    choices_json NVARCHAR(MAX) NULL,
    detected_answer_json NVARCHAR(MAX) NULL,
    explanation_text NVARCHAR(MAX) NULL,
    confidence_score DECIMAL(5,4) NOT NULL,
    diagnostics_json NVARCHAR(MAX) NULL,
    review_state VARCHAR(20) NOT NULL DEFAULT ('READY'),
    has_broken_resource BIT NOT NULL DEFAULT (0),
    ai_suggested_answer_json NVARCHAR(MAX) NULL,
    ai_suggestion_model NVARCHAR(100) NULL,
    ai_suggestion_confirmed_at DATETIME2(3) NULL,
    ai_suggestion_confirmed_by BIGINT NULL,
    approved_question_id BIGINT NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    updated_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    row_version ROWVERSION,
    CONSTRAINT pk_import_questions PRIMARY KEY (id),
    CONSTRAINT uq_import_questions_import_job_id_ordinal_1 UNIQUE (import_job_id, ordinal),
    CONSTRAINT ck_import_questions_1 CHECK (ordinal > 0),
    CONSTRAINT ck_import_questions_2 CHECK (confidence_score >= 0 AND confidence_score <= 1),
    CONSTRAINT ck_import_questions_3 CHECK (review_state IN ('READY','NEEDS_REVIEW','INVALID','ACCEPTED','REJECTED','EDITED')),
    CONSTRAINT ck_import_questions_4 CHECK (choices_json IS NULL OR ISJSON(choices_json)=1),
    CONSTRAINT ck_import_questions_5 CHECK (detected_answer_json IS NULL OR ISJSON(detected_answer_json)=1),
    CONSTRAINT ck_import_questions_6 CHECK (diagnostics_json IS NULL OR ISJSON(diagnostics_json)=1),
    CONSTRAINT ck_import_questions_7 CHECK (ai_suggested_answer_json IS NULL OR ISJSON(ai_suggested_answer_json)=1),
    CONSTRAINT fk_import_questions_import_job_id FOREIGN KEY (import_job_id) REFERENCES document_import_jobs (id),
    CONSTRAINT fk_import_questions_ai_suggestion_confirmed_by FOREIGN KEY (ai_suggestion_confirmed_by) REFERENCES users (id) ON DELETE SET NULL,
    CONSTRAINT fk_import_questions_approved_question_id FOREIGN KEY (approved_question_id) REFERENCES questions (id) ON DELETE SET NULL
);
GO

CREATE TABLE import_duplicate_candidates (
    id BIGINT IDENTITY(1,1) NOT NULL,
    import_question_id BIGINT NOT NULL,
    candidate_import_question_id BIGINT NULL,
    candidate_question_id BIGINT NULL,
    similarity_score DECIMAL(5,4) NOT NULL,
    decision VARCHAR(16) NOT NULL DEFAULT ('PENDING'),
    decided_by_user_id BIGINT NULL,
    decided_at DATETIME2(3) NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT pk_import_duplicate_candidates PRIMARY KEY (id),
    CONSTRAINT ck_import_duplicate_candidates_1 CHECK (similarity_score >= 0 AND similarity_score <= 1),
    CONSTRAINT ck_import_duplicate_candidates_2 CHECK (decision IN ('PENDING','KEEP','IGNORE','REJECT')),
    CONSTRAINT ck_import_duplicate_candidates_3 CHECK ((candidate_import_question_id IS NOT NULL OR candidate_question_id IS NOT NULL)),
    CONSTRAINT fk_import_duplicate_candidates_import_question_id FOREIGN KEY (import_question_id) REFERENCES import_questions (id),
    CONSTRAINT fk_import_duplicate_candidates_candidate_import_question_id FOREIGN KEY (candidate_import_question_id) REFERENCES import_questions (id) ON DELETE SET NULL,
    CONSTRAINT fk_import_duplicate_candidates_candidate_question_id FOREIGN KEY (candidate_question_id) REFERENCES questions (id) ON DELETE SET NULL,
    CONSTRAINT fk_import_duplicate_candidates_decided_by_user_id FOREIGN KEY (decided_by_user_id) REFERENCES users (id) ON DELETE SET NULL
);
GO

CREATE TABLE import_question_resources (
    id BIGINT IDENTITY(1,1) NOT NULL,
    import_question_id BIGINT NOT NULL,
    file_asset_id BIGINT NOT NULL,
    position INT NOT NULL DEFAULT (1),
    status VARCHAR(16) NOT NULL DEFAULT ('READY'),
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT pk_import_question_resources PRIMARY KEY (id),
    CONSTRAINT uq_import_question_resources_import_question_id_file_asset_id_1 UNIQUE (import_question_id, file_asset_id),
    CONSTRAINT ck_import_question_resources_1 CHECK (position > 0),
    CONSTRAINT ck_import_question_resources_2 CHECK (status IN ('READY','BROKEN','REJECTED')),
    CONSTRAINT fk_import_question_resources_import_question_id FOREIGN KEY (import_question_id) REFERENCES import_questions (id),
    CONSTRAINT fk_import_question_resources_file_asset_id FOREIGN KEY (file_asset_id) REFERENCES file_assets (id)
);
GO
