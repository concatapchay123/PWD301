/*
PWD301 Database Architecture — Reference DDL
Engine: Microsoft SQL Server
All DATETIME2 values are UTC by application convention.
This is reference architecture, not evidence that migrations have been executed.
*/
SET XACT_ABORT ON;
GO

CREATE TABLE assessments (
    id BIGINT IDENTITY(1,1) NOT NULL,
    public_id UNIQUEIDENTIFIER NOT NULL DEFAULT (NEWSEQUENTIALID()),
    course_id BIGINT NOT NULL,
    creator_user_id BIGINT NULL,
    title NVARCHAR(200) NOT NULL,
    description NVARCHAR(MAX) NULL,
    assessment_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT ('DRAFT'),
    open_at DATETIME2(3) NULL,
    close_at DATETIME2(3) NULL,
    time_limit_minutes INT NULL,
    attempt_limit INT NULL,
    scoring_policy VARCHAR(20) NOT NULL DEFAULT ('HIGHEST'),
    passing_percent DECIMAL(5,2) NULL,
    is_required_for_completion BIT NOT NULL DEFAULT (0),
    shuffle_questions BIT NOT NULL DEFAULT (0),
    shuffle_choices BIT NOT NULL DEFAULT (0),
    score_release_policy VARCHAR(24) NOT NULL DEFAULT ('IMMEDIATE'),
    answer_visibility_policy VARCHAR(32) NOT NULL DEFAULT ('AFTER_CLOSE'),
    random_question_count INT NULL,
    published_at DATETIME2(3) NULL,
    first_attempt_started_at DATETIME2(3) NULL,
    cancelled_at DATETIME2(3) NULL,
    cancel_reason NVARCHAR(1000) NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    updated_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    row_version ROWVERSION,
    deleted_at DATETIME2(3) NULL,
    restore_until DATETIME2(3) NULL,
    deleted_by_user_id BIGINT NULL,
    CONSTRAINT pk_assessments PRIMARY KEY (id),
    CONSTRAINT uq_assessments_public_id_1 UNIQUE (public_id),
    CONSTRAINT ck_assessments_1 CHECK (assessment_type IN ('PRACTICE','QUIZ','MIDTERM','FINAL','PLACEMENT')),
    CONSTRAINT ck_assessments_2 CHECK (status IN ('DRAFT','PUBLISHED','CANCELLED','ARCHIVED','TRASH')),
    CONSTRAINT ck_assessments_3 CHECK (time_limit_minutes IS NULL OR time_limit_minutes > 0),
    CONSTRAINT ck_assessments_4 CHECK (attempt_limit IS NULL OR attempt_limit > 0),
    CONSTRAINT ck_assessments_5 CHECK (scoring_policy IN ('FIRST','LATEST','HIGHEST','AVERAGE')),
    CONSTRAINT ck_assessments_6 CHECK (passing_percent IS NULL OR (passing_percent >= 0 AND passing_percent <= 100)),
    CONSTRAINT ck_assessments_7 CHECK (score_release_policy IN ('IMMEDIATE','AFTER_CLOSE','INSTRUCTOR_RELEASE')),
    CONSTRAINT ck_assessments_8 CHECK (answer_visibility_policy IN ('IMMEDIATE','AFTER_CLOSE','AFTER_ALL_ATTEMPTS','NEVER')),
    CONSTRAINT ck_assessments_9 CHECK (random_question_count IS NULL OR random_question_count > 0),
    CONSTRAINT ck_assessments_10 CHECK (open_at IS NULL OR close_at IS NULL OR open_at < close_at),
    CONSTRAINT fk_assessments_course_id FOREIGN KEY (course_id) REFERENCES courses (id),
    CONSTRAINT fk_assessments_creator_user_id FOREIGN KEY (creator_user_id) REFERENCES users (id),
    CONSTRAINT fk_assessments_deleted_by_user_id FOREIGN KEY (deleted_by_user_id) REFERENCES users (id)
);
GO

CREATE TABLE assessment_sections (
    id BIGINT IDENTITY(1,1) NOT NULL,
    assessment_id BIGINT NOT NULL,
    title NVARCHAR(200) NULL,
    position INT NOT NULL,
    instructions NVARCHAR(MAX) NULL,
    CONSTRAINT pk_assessment_sections PRIMARY KEY (id),
    CONSTRAINT uq_assessment_sections_assessment_id_position_1 UNIQUE (assessment_id, position),
    CONSTRAINT ck_assessment_sections_1 CHECK (position > 0),
    CONSTRAINT fk_assessment_sections_assessment_id FOREIGN KEY (assessment_id) REFERENCES assessments (id)
);
GO

CREATE TABLE assessment_question_assignments (
    id BIGINT IDENTITY(1,1) NOT NULL,
    assessment_id BIGINT NOT NULL,
    section_id BIGINT NULL,
    question_id BIGINT NOT NULL,
    position INT NOT NULL,
    points DECIMAL(9,4) NOT NULL,
    is_mandatory BIT NOT NULL DEFAULT (1),
    shuffle_choices_override BIT NULL,
    source_type VARCHAR(20) NOT NULL DEFAULT ('BANK'),
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT pk_assessment_question_assignments PRIMARY KEY (id),
    CONSTRAINT uq_assessment_question_assignments_assessment_id_question_id_1 UNIQUE (assessment_id, question_id),
    CONSTRAINT ck_assessment_question_assignments_1 CHECK (position > 0),
    CONSTRAINT ck_assessment_question_assignments_2 CHECK (points > 0),
    CONSTRAINT ck_assessment_question_assignments_3 CHECK (source_type IN ('MANUAL','BANK','IMPORT','AI')),
    CONSTRAINT fk_assessment_question_assignments_assessment_id FOREIGN KEY (assessment_id) REFERENCES assessments (id),
    CONSTRAINT fk_assessment_question_assignments_section_id FOREIGN KEY (section_id) REFERENCES assessment_sections (id) ON DELETE SET NULL,
    CONSTRAINT fk_assessment_question_assignments_question_id FOREIGN KEY (question_id) REFERENCES questions (id)
);
GO

CREATE TABLE assessment_blueprints (
    id BIGINT IDENTITY(1,1) NOT NULL,
    assessment_id BIGINT NOT NULL,
    name NVARCHAR(200) NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT ('DRAFT'),
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    updated_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    row_version ROWVERSION,
    CONSTRAINT pk_assessment_blueprints PRIMARY KEY (id),
    CONSTRAINT uq_assessment_blueprints_assessment_id_name_1 UNIQUE (assessment_id, name),
    CONSTRAINT ck_assessment_blueprints_1 CHECK (status IN ('DRAFT','READY','FROZEN')),
    CONSTRAINT fk_assessment_blueprints_assessment_id FOREIGN KEY (assessment_id) REFERENCES assessments (id)
);
GO

CREATE TABLE assessment_blueprint_rules (
    id BIGINT IDENTITY(1,1) NOT NULL,
    blueprint_id BIGINT NOT NULL,
    section_id BIGINT NULL,
    lesson_id BIGINT NULL,
    difficulty VARCHAR(20) NULL,
    question_type VARCHAR(24) NULL,
    question_count INT NOT NULL,
    points_each DECIMAL(9,4) NOT NULL,
    position INT NOT NULL DEFAULT (1),
    CONSTRAINT pk_assessment_blueprint_rules PRIMARY KEY (id),
    CONSTRAINT uq_assessment_blueprint_rules_blueprint_id_position_1 UNIQUE (blueprint_id, position),
    CONSTRAINT ck_assessment_blueprint_rules_1 CHECK (question_count > 0),
    CONSTRAINT ck_assessment_blueprint_rules_2 CHECK (points_each > 0),
    CONSTRAINT ck_assessment_blueprint_rules_3 CHECK (position > 0),
    CONSTRAINT ck_assessment_blueprint_rules_4 CHECK (difficulty IS NULL OR difficulty IN ('REMEMBER','UNDERSTAND','APPLY')),
    CONSTRAINT ck_assessment_blueprint_rules_5 CHECK (question_type IS NULL OR question_type IN ('SINGLE_CHOICE','MULTIPLE_CHOICE','TRUE_FALSE','SHORT_ANSWER','ESSAY')),
    CONSTRAINT fk_assessment_blueprint_rules_blueprint_id FOREIGN KEY (blueprint_id) REFERENCES assessment_blueprints (id),
    CONSTRAINT fk_assessment_blueprint_rules_section_id FOREIGN KEY (section_id) REFERENCES assessment_sections (id) ON DELETE SET NULL,
    CONSTRAINT fk_assessment_blueprint_rules_lesson_id FOREIGN KEY (lesson_id) REFERENCES lessons (id) ON DELETE SET NULL
);
GO

CREATE TABLE assessment_question_pool (
    id BIGINT IDENTITY(1,1) NOT NULL,
    assessment_id BIGINT NOT NULL,
    blueprint_rule_id BIGINT NULL,
    question_id BIGINT NOT NULL,
    points DECIMAL(9,4) NOT NULL,
    is_fixed BIT NOT NULL DEFAULT (0),
    position_hint INT NULL,
    selection_source VARCHAR(20) NOT NULL DEFAULT ('BLUEPRINT'),
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT pk_assessment_question_pool PRIMARY KEY (id),
    CONSTRAINT uq_assessment_question_pool_assessment_id_question_id_1 UNIQUE (assessment_id, question_id),
    CONSTRAINT ck_assessment_question_pool_1 CHECK (points > 0),
    CONSTRAINT ck_assessment_question_pool_2 CHECK (position_hint IS NULL OR position_hint > 0),
    CONSTRAINT ck_assessment_question_pool_3 CHECK (selection_source IN ('BLUEPRINT','MANUAL_POOL','IMPORT','AI')),
    CONSTRAINT fk_assessment_question_pool_assessment_id FOREIGN KEY (assessment_id) REFERENCES assessments (id),
    CONSTRAINT fk_assessment_question_pool_blueprint_rule_id FOREIGN KEY (blueprint_rule_id) REFERENCES assessment_blueprint_rules (id) ON DELETE SET NULL,
    CONSTRAINT fk_assessment_question_pool_question_id FOREIGN KEY (question_id) REFERENCES questions (id)
);
GO
