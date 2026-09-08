/*
PWD301 Database Architecture — Reference DDL
Engine: Microsoft SQL Server
All DATETIME2 values are UTC by application convention.
This is reference architecture, not evidence that migrations have been executed.
*/
SET XACT_ABORT ON;
GO

CREATE TABLE ai_conversations (
    id BIGINT IDENTITY(1,1) NOT NULL,
    public_id UNIQUEIDENTIFIER NOT NULL DEFAULT (NEWSEQUENTIALID()),
    user_id BIGINT NOT NULL,
    context_type VARCHAR(16) NOT NULL,
    course_id BIGINT NULL,
    lesson_id BIGINT NULL,
    last_activity_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    expires_at DATETIME2(3) NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT ('ACTIVE'),
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    row_version ROWVERSION,
    CONSTRAINT pk_ai_conversations PRIMARY KEY (id),
    CONSTRAINT uq_ai_conversations_public_id_1 UNIQUE (public_id),
    CONSTRAINT ck_ai_conversations_1 CHECK (context_type IN ('GLOBAL','COURSE','LESSON')),
    CONSTRAINT ck_ai_conversations_2 CHECK (status IN ('ACTIVE','EXPIRED','DELETED')),
    CONSTRAINT ck_ai_conversations_3 CHECK (expires_at > created_at),
    CONSTRAINT fk_ai_conversations_user_id FOREIGN KEY (user_id) REFERENCES users (id),
    CONSTRAINT fk_ai_conversations_course_id FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE SET NULL,
    CONSTRAINT fk_ai_conversations_lesson_id FOREIGN KEY (lesson_id) REFERENCES lessons (id) ON DELETE SET NULL
);
GO

CREATE TABLE ai_messages (
    id BIGINT IDENTITY(1,1) NOT NULL,
    conversation_id BIGINT NOT NULL,
    sender VARCHAR(12) NOT NULL,
    content NVARCHAR(MAX) NOT NULL,
    sequence_no INT NOT NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT pk_ai_messages PRIMARY KEY (id),
    CONSTRAINT uq_ai_messages_conversation_id_sequence_no_1 UNIQUE (conversation_id, sequence_no),
    CONSTRAINT ck_ai_messages_1 CHECK (sender IN ('USER','ASSISTANT')),
    CONSTRAINT ck_ai_messages_2 CHECK (sequence_no > 0),
    CONSTRAINT fk_ai_messages_conversation_id FOREIGN KEY (conversation_id) REFERENCES ai_conversations (id)
);
GO

CREATE TABLE ai_requests (
    id BIGINT IDENTITY(1,1) NOT NULL,
    request_id UNIQUEIDENTIFIER NOT NULL DEFAULT (NEWID()),
    conversation_id BIGINT NULL,
    user_id BIGINT NOT NULL,
    route_type VARCHAR(24) NOT NULL,
    model_name NVARCHAR(100) NULL,
    prompt_hash BINARY(32) NULL,
    scope_decision VARCHAR(16) NULL,
    authorization_scope_hash BINARY(32) NULL,
    input_token_count INT NULL,
    output_token_count INT NULL,
    latency_ms INT NULL,
    status VARCHAR(20) NOT NULL,
    error_code VARCHAR(64) NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT pk_ai_requests PRIMARY KEY (id),
    CONSTRAINT uq_ai_requests_request_id_1 UNIQUE (request_id),
    CONSTRAINT ck_ai_requests_1 CHECK (route_type IN ('BACKEND_ONLY','GEMINI','RAG','CLASSIFIER')),
    CONSTRAINT ck_ai_requests_2 CHECK (scope_decision IS NULL OR scope_decision IN ('IN_SCOPE','OUT_OF_SCOPE','MIXED','AMBIGUOUS')),
    CONSTRAINT ck_ai_requests_3 CHECK (status IN ('SUCCEEDED','REFUSED','FAILED','TIMEOUT','BYPASSED')),
    CONSTRAINT ck_ai_requests_4 CHECK (input_token_count IS NULL OR input_token_count >= 0),
    CONSTRAINT ck_ai_requests_5 CHECK (output_token_count IS NULL OR output_token_count >= 0),
    CONSTRAINT ck_ai_requests_6 CHECK (latency_ms IS NULL OR latency_ms >= 0),
    CONSTRAINT fk_ai_requests_conversation_id FOREIGN KEY (conversation_id) REFERENCES ai_conversations (id) ON DELETE SET NULL,
    CONSTRAINT fk_ai_requests_user_id FOREIGN KEY (user_id) REFERENCES users (id)
);
GO

CREATE TABLE ai_generated_question_drafts (
    id BIGINT IDENTITY(1,1) NOT NULL,
    course_id BIGINT NOT NULL,
    lesson_id BIGINT NULL,
    requested_by_user_id BIGINT NOT NULL,
    ai_request_id BIGINT NULL,
    ordinal INT NOT NULL,
    question_type VARCHAR(24) NOT NULL,
    difficulty VARCHAR(20) NOT NULL,
    content NVARCHAR(MAX) NOT NULL,
    choices_json NVARCHAR(MAX) NULL,
    answer_json NVARCHAR(MAX) NULL,
    explanation NVARCHAR(MAX) NULL,
    review_state VARCHAR(16) NOT NULL DEFAULT ('PENDING'),
    approved_question_id BIGINT NULL,
    reviewed_by_user_id BIGINT NULL,
    reviewed_at DATETIME2(3) NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    updated_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    row_version ROWVERSION,
    CONSTRAINT pk_ai_generated_question_drafts PRIMARY KEY (id),
    CONSTRAINT ck_ai_generated_question_drafts_1 CHECK (ordinal > 0),
    CONSTRAINT ck_ai_generated_question_drafts_2 CHECK (question_type IN ('SINGLE_CHOICE','MULTIPLE_CHOICE','TRUE_FALSE','SHORT_ANSWER','ESSAY')),
    CONSTRAINT ck_ai_generated_question_drafts_3 CHECK (difficulty IN ('REMEMBER','UNDERSTAND','APPLY')),
    CONSTRAINT ck_ai_generated_question_drafts_4 CHECK (review_state IN ('PENDING','KEPT','EDITED','REJECTED','APPROVED')),
    CONSTRAINT ck_ai_generated_question_drafts_5 CHECK (choices_json IS NULL OR ISJSON(choices_json)=1),
    CONSTRAINT ck_ai_generated_question_drafts_6 CHECK (answer_json IS NULL OR ISJSON(answer_json)=1),
    CONSTRAINT fk_ai_generated_question_drafts_course_id FOREIGN KEY (course_id) REFERENCES courses (id),
    CONSTRAINT fk_ai_generated_question_drafts_lesson_id FOREIGN KEY (lesson_id) REFERENCES lessons (id) ON DELETE SET NULL,
    CONSTRAINT fk_ai_generated_question_drafts_requested_by_user_id FOREIGN KEY (requested_by_user_id) REFERENCES users (id),
    CONSTRAINT fk_ai_generated_question_drafts_ai_request_id FOREIGN KEY (ai_request_id) REFERENCES ai_requests (id) ON DELETE SET NULL,
    CONSTRAINT fk_ai_generated_question_drafts_approved_question_id FOREIGN KEY (approved_question_id) REFERENCES questions (id) ON DELETE SET NULL,
    CONSTRAINT fk_ai_generated_question_drafts_reviewed_by_user_id FOREIGN KEY (reviewed_by_user_id) REFERENCES users (id) ON DELETE SET NULL
);
GO

CREATE TABLE knowledge_documents (
    id BIGINT IDENTITY(1,1) NOT NULL,
    public_id UNIQUEIDENTIFIER NOT NULL DEFAULT (NEWSEQUENTIALID()),
    course_id BIGINT NOT NULL,
    lesson_id BIGINT NULL,
    source_type VARCHAR(24) NOT NULL,
    source_entity_id BIGINT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT ('ACTIVE'),
    current_version_id BIGINT NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    updated_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    row_version ROWVERSION,
    CONSTRAINT pk_knowledge_documents PRIMARY KEY (id),
    CONSTRAINT uq_knowledge_documents_public_id_1 UNIQUE (public_id),
    CONSTRAINT uq_knowledge_documents_source_type_source_entity_id_2 UNIQUE (source_type, source_entity_id),
    CONSTRAINT ck_knowledge_documents_1 CHECK (source_type IN ('LESSON','FILE','FAQ','POLICY')),
    CONSTRAINT ck_knowledge_documents_2 CHECK (status IN ('ACTIVE','INVALIDATED','DELETED')),
    CONSTRAINT fk_knowledge_documents_course_id FOREIGN KEY (course_id) REFERENCES courses (id),
    CONSTRAINT fk_knowledge_documents_lesson_id FOREIGN KEY (lesson_id) REFERENCES lessons (id) ON DELETE SET NULL
);
GO

CREATE TABLE knowledge_versions (
    id BIGINT IDENTITY(1,1) NOT NULL,
    knowledge_document_id BIGINT NOT NULL,
    version_no INT NOT NULL,
    source_revision_type VARCHAR(32) NULL,
    source_revision_id BIGINT NULL,
    content_hash BINARY(32) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT ('PENDING'),
    vector_namespace NVARCHAR(200) NULL,
    background_job_id BIGINT NULL,
    activated_at DATETIME2(3) NULL,
    invalidated_at DATETIME2(3) NULL,
    last_error NVARCHAR(2000) NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    row_version ROWVERSION,
    CONSTRAINT pk_knowledge_versions PRIMARY KEY (id),
    CONSTRAINT uq_knowledge_versions_knowledge_document_id_version_no_1 UNIQUE (knowledge_document_id, version_no),
    CONSTRAINT ck_knowledge_versions_1 CHECK (version_no > 0),
    CONSTRAINT ck_knowledge_versions_2 CHECK (status IN ('PENDING','PROCESSING','ACTIVE','INVALIDATED','FAILED')),
    CONSTRAINT fk_knowledge_versions_knowledge_document_id FOREIGN KEY (knowledge_document_id) REFERENCES knowledge_documents (id)
);
GO

CREATE TABLE knowledge_chunks (
    id BIGINT IDENTITY(1,1) NOT NULL,
    knowledge_version_id BIGINT NOT NULL,
    chunk_no INT NOT NULL,
    text_hash BINARY(32) NOT NULL,
    vector_key NVARCHAR(300) NOT NULL,
    token_count INT NULL,
    metadata_json NVARCHAR(MAX) NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT pk_knowledge_chunks PRIMARY KEY (id),
    CONSTRAINT uq_knowledge_chunks_knowledge_version_id_chunk_no_1 UNIQUE (knowledge_version_id, chunk_no),
    CONSTRAINT uq_knowledge_chunks_vector_key_2 UNIQUE (vector_key),
    CONSTRAINT ck_knowledge_chunks_1 CHECK (chunk_no > 0),
    CONSTRAINT ck_knowledge_chunks_2 CHECK (token_count IS NULL OR token_count >= 0),
    CONSTRAINT ck_knowledge_chunks_3 CHECK (metadata_json IS NULL OR ISJSON(metadata_json)=1),
    CONSTRAINT fk_knowledge_chunks_knowledge_version_id FOREIGN KEY (knowledge_version_id) REFERENCES knowledge_versions (id)
);
GO

CREATE TABLE ai_source_usages (
    id BIGINT IDENTITY(1,1) NOT NULL,
    ai_request_id BIGINT NOT NULL,
    knowledge_version_id BIGINT NOT NULL,
    knowledge_chunk_id BIGINT NULL,
    rank_no INT NULL,
    relevance_score DECIMAL(8,6) NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT pk_ai_source_usages PRIMARY KEY (id),
    CONSTRAINT uq_ai_source_usages_ai_request_id_knowledge_version_id_knowledge_chunk_id_1 UNIQUE (ai_request_id, knowledge_version_id, knowledge_chunk_id),
    CONSTRAINT ck_ai_source_usages_1 CHECK (rank_no IS NULL OR rank_no > 0),
    CONSTRAINT fk_ai_source_usages_ai_request_id FOREIGN KEY (ai_request_id) REFERENCES ai_requests (id),
    CONSTRAINT fk_ai_source_usages_knowledge_version_id FOREIGN KEY (knowledge_version_id) REFERENCES knowledge_versions (id),
    CONSTRAINT fk_ai_source_usages_knowledge_chunk_id FOREIGN KEY (knowledge_chunk_id) REFERENCES knowledge_chunks (id) ON DELETE SET NULL
);
GO
