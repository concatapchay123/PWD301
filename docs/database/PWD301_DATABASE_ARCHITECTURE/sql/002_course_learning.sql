/*
PWD301 Database Architecture — Reference DDL
Engine: Microsoft SQL Server
All DATETIME2 values are UTC by application convention.
This is reference architecture, not evidence that migrations have been executed.
*/
SET XACT_ABORT ON;
GO

CREATE TABLE courses (
    id BIGINT IDENTITY(1,1) NOT NULL,
    public_id UNIQUEIDENTIFIER NOT NULL DEFAULT (NEWSEQUENTIALID()),
    course_code NVARCHAR(50) NOT NULL,
    course_code_normalized AS UPPER(LTRIM(RTRIM([course_code]))) PERSISTED,
    title NVARCHAR(200) NOT NULL,
    title_normalized AS LOWER(LTRIM(RTRIM([title]))) PERSISTED,
    description NVARCHAR(MAX) NULL,
    category NVARCHAR(100) NULL,
    difficulty VARCHAR(20) NULL,
    owner_instructor_id BIGINT NULL,
    thumbnail_file_asset_id BIGINT NULL,
    status VARCHAR(32) NOT NULL DEFAULT ('DRAFT'),
    capacity INT NULL,
    storage_quota_bytes BIGINT NULL,
    published_at DATETIME2(3) NULL,
    approved_at DATETIME2(3) NULL,
    approved_by_user_id BIGINT NULL,
    first_student_enrolled_at DATETIME2(3) NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    updated_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    row_version ROWVERSION,
    deleted_at DATETIME2(3) NULL,
    restore_until DATETIME2(3) NULL,
    deleted_by_user_id BIGINT NULL,
    CONSTRAINT pk_courses PRIMARY KEY (id),
    CONSTRAINT uq_courses_public_id_1 UNIQUE (public_id),
    CONSTRAINT uq_courses_course_code_normalized_2 UNIQUE (course_code_normalized),
    CONSTRAINT uq_courses_title_normalized_3 UNIQUE (title_normalized),
    CONSTRAINT ck_courses_1 CHECK (status IN ('DRAFT','SUBMITTED_FOR_REVIEW','APPROVED','PUBLISHED','ARCHIVED','TRASH')),
    CONSTRAINT ck_courses_2 CHECK (difficulty IS NULL OR difficulty IN ('BEGINNER','INTERMEDIATE','ADVANCED')),
    CONSTRAINT ck_courses_3 CHECK (capacity IS NULL OR capacity > 0),
    CONSTRAINT ck_courses_4 CHECK (storage_quota_bytes IS NULL OR storage_quota_bytes > 0),
    CONSTRAINT fk_courses_owner_instructor_id FOREIGN KEY (owner_instructor_id) REFERENCES users (id),
    CONSTRAINT fk_courses_approved_by_user_id FOREIGN KEY (approved_by_user_id) REFERENCES users (id),
    CONSTRAINT fk_courses_deleted_by_user_id FOREIGN KEY (deleted_by_user_id) REFERENCES users (id)
);
GO

CREATE TABLE course_prerequisites (
    course_id BIGINT NOT NULL,
    prerequisite_course_id BIGINT NOT NULL,
    created_by_user_id BIGINT NOT NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT pk_course_prerequisites PRIMARY KEY (course_id, prerequisite_course_id),
    CONSTRAINT ck_course_prerequisites_1 CHECK (course_id <> prerequisite_course_id),
    CONSTRAINT fk_course_prerequisites_course_id FOREIGN KEY (course_id) REFERENCES courses (id),
    CONSTRAINT fk_course_prerequisites_prerequisite_course_id FOREIGN KEY (prerequisite_course_id) REFERENCES courses (id),
    CONSTRAINT fk_course_prerequisites_created_by_user_id FOREIGN KEY (created_by_user_id) REFERENCES users (id)
);
GO

CREATE TABLE course_completion_rules (
    course_id BIGINT NOT NULL,
    require_all_required_lessons BIT NOT NULL DEFAULT (1),
    require_required_assessments BIT NOT NULL DEFAULT (1),
    minimum_progress_percent DECIMAL(5,2) NULL,
    updated_by_user_id BIGINT NULL,
    updated_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    row_version ROWVERSION,
    CONSTRAINT pk_course_completion_rules PRIMARY KEY (course_id),
    CONSTRAINT ck_course_completion_rules_1 CHECK (minimum_progress_percent IS NULL OR (minimum_progress_percent >= 0 AND minimum_progress_percent <= 100)),
    CONSTRAINT fk_course_completion_rules_course_id FOREIGN KEY (course_id) REFERENCES courses (id),
    CONSTRAINT fk_course_completion_rules_updated_by_user_id FOREIGN KEY (updated_by_user_id) REFERENCES users (id) ON DELETE SET NULL
);
GO

CREATE TABLE course_change_requests (
    id BIGINT IDENTITY(1,1) NOT NULL,
    course_id BIGINT NOT NULL,
    requested_by_user_id BIGINT NOT NULL,
    change_type VARCHAR(32) NOT NULL,
    target_type VARCHAR(32) NOT NULL,
    target_id BIGINT NULL,
    proposed_payload_json NVARCHAR(MAX) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT ('PENDING'),
    reviewed_by_user_id BIGINT NULL,
    review_reason NVARCHAR(1000) NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    reviewed_at DATETIME2(3) NULL,
    applied_at DATETIME2(3) NULL,
    row_version ROWVERSION,
    CONSTRAINT pk_course_change_requests PRIMARY KEY (id),
    CONSTRAINT ck_course_change_requests_1 CHECK (change_type IN ('COURSE_METADATA','LESSON_STRUCTURE','LESSON_CONTENT','COMPLETION_RULE','PREREQUISITE','OTHER')),
    CONSTRAINT ck_course_change_requests_2 CHECK (target_type IN ('COURSE','LESSON','RULE','PREREQUISITE')),
    CONSTRAINT ck_course_change_requests_3 CHECK (status IN ('PENDING','APPROVED','REJECTED','CANCELLED','APPLIED')),
    CONSTRAINT ck_course_change_requests_4 CHECK (ISJSON(proposed_payload_json)=1),
    CONSTRAINT fk_course_change_requests_course_id FOREIGN KEY (course_id) REFERENCES courses (id),
    CONSTRAINT fk_course_change_requests_requested_by_user_id FOREIGN KEY (requested_by_user_id) REFERENCES users (id),
    CONSTRAINT fk_course_change_requests_reviewed_by_user_id FOREIGN KEY (reviewed_by_user_id) REFERENCES users (id) ON DELETE SET NULL
);
GO

CREATE TABLE lessons (
    id BIGINT IDENTITY(1,1) NOT NULL,
    public_id UNIQUEIDENTIFIER NOT NULL DEFAULT (NEWSEQUENTIALID()),
    course_id BIGINT NOT NULL,
    title NVARCHAR(200) NOT NULL,
    summary NVARCHAR(1000) NULL,
    markdown_content NVARCHAR(MAX) NOT NULL,
    position INT NOT NULL,
    estimated_duration_minutes INT NULL,
    minimum_completion_seconds INT NOT NULL DEFAULT (30),
    viewed_fraction_required DECIMAL(5,4) NOT NULL DEFAULT (0.8000),
    required_for_periods_starting_at DATETIME2(3) NULL,
    status VARCHAR(20) NOT NULL DEFAULT ('DRAFT'),
    published_at DATETIME2(3) NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    updated_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    row_version ROWVERSION,
    deleted_at DATETIME2(3) NULL,
    restore_until DATETIME2(3) NULL,
    deleted_by_user_id BIGINT NULL,
    CONSTRAINT pk_lessons PRIMARY KEY (id),
    CONSTRAINT uq_lessons_public_id_1 UNIQUE (public_id),
    CONSTRAINT uq_lessons_course_id_position_2 UNIQUE (course_id, position),
    CONSTRAINT ck_lessons_1 CHECK (position > 0),
    CONSTRAINT ck_lessons_2 CHECK (estimated_duration_minutes IS NULL OR estimated_duration_minutes > 0),
    CONSTRAINT ck_lessons_3 CHECK (minimum_completion_seconds >= 0),
    CONSTRAINT ck_lessons_4 CHECK (viewed_fraction_required >= 0 AND viewed_fraction_required <= 1),
    CONSTRAINT ck_lessons_5 CHECK (status IN ('DRAFT','PUBLISHED','HIDDEN','TRASH','HISTORICAL')),
    CONSTRAINT fk_lessons_course_id FOREIGN KEY (course_id) REFERENCES courses (id),
    CONSTRAINT fk_lessons_deleted_by_user_id FOREIGN KEY (deleted_by_user_id) REFERENCES users (id) ON DELETE SET NULL
);
GO

CREATE TABLE enrollments (
    id BIGINT IDENTITY(1,1) NOT NULL,
    public_id UNIQUEIDENTIFIER NOT NULL DEFAULT (NEWSEQUENTIALID()),
    student_user_id BIGINT NOT NULL,
    course_id BIGINT NOT NULL,
    status VARCHAR(24) NOT NULL DEFAULT ('ACTIVE'),
    current_period_id BIGINT NULL,
    current_progress_percent DECIMAL(5,2) NOT NULL DEFAULT (0),
    enrolled_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    left_at DATETIME2(3) NULL,
    completed_at DATETIME2(3) NULL,
    detail_retention_due_at DATETIME2(3) NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    updated_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    row_version ROWVERSION,
    CONSTRAINT pk_enrollments PRIMARY KEY (id),
    CONSTRAINT uq_enrollments_public_id_1 UNIQUE (public_id),
    CONSTRAINT uq_enrollments_student_user_id_course_id_2 UNIQUE (student_user_id, course_id),
    CONSTRAINT ck_enrollments_1 CHECK (status IN ('ACTIVE','LEFT','COMPLETED','RETENTION_PENDING','DETAIL_PURGED')),
    CONSTRAINT ck_enrollments_2 CHECK (current_progress_percent >= 0 AND current_progress_percent <= 100),
    CONSTRAINT fk_enrollments_student_user_id FOREIGN KEY (student_user_id) REFERENCES users (id),
    CONSTRAINT fk_enrollments_course_id FOREIGN KEY (course_id) REFERENCES courses (id)
);
GO

CREATE TABLE enrollment_periods (
    id BIGINT IDENTITY(1,1) NOT NULL,
    enrollment_id BIGINT NOT NULL,
    period_no INT NOT NULL,
    started_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    left_at DATETIME2(3) NULL,
    completed_at DATETIME2(3) NULL,
    retention_due_at DATETIME2(3) NULL,
    detail_purged_at DATETIME2(3) NULL,
    status VARCHAR(20) NOT NULL DEFAULT ('ACTIVE'),
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT pk_enrollment_periods PRIMARY KEY (id),
    CONSTRAINT uq_enrollment_periods_enrollment_id_period_no_1 UNIQUE (enrollment_id, period_no),
    CONSTRAINT ck_enrollment_periods_1 CHECK (period_no > 0),
    CONSTRAINT ck_enrollment_periods_2 CHECK (status IN ('ACTIVE','LEFT','COMPLETED','PURGED')),
    CONSTRAINT fk_enrollment_periods_enrollment_id FOREIGN KEY (enrollment_id) REFERENCES enrollments (id)
);
GO

CREATE TABLE enrollment_events (
    id BIGINT IDENTITY(1,1) NOT NULL,
    enrollment_id BIGINT NOT NULL,
    period_id BIGINT NULL,
    event_type VARCHAR(24) NOT NULL,
    actor_user_id BIGINT NULL,
    reason NVARCHAR(500) NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT pk_enrollment_events PRIMARY KEY (id),
    CONSTRAINT ck_enrollment_events_1 CHECK (event_type IN ('ENROLLED','LEFT','REENROLLED','COMPLETED','DETAIL_PURGED')),
    CONSTRAINT fk_enrollment_events_enrollment_id FOREIGN KEY (enrollment_id) REFERENCES enrollments (id),
    CONSTRAINT fk_enrollment_events_period_id FOREIGN KEY (period_id) REFERENCES enrollment_periods (id) ON DELETE SET NULL,
    CONSTRAINT fk_enrollment_events_actor_user_id FOREIGN KEY (actor_user_id) REFERENCES users (id) ON DELETE SET NULL
);
GO

CREATE TABLE lesson_progress (
    id BIGINT IDENTITY(1,1) NOT NULL,
    enrollment_period_id BIGINT NOT NULL,
    lesson_id BIGINT NOT NULL,
    seconds_spent INT NOT NULL DEFAULT (0),
    max_view_fraction DECIMAL(5,4) NOT NULL DEFAULT (0),
    last_activity_at DATETIME2(3) NULL,
    completed_at DATETIME2(3) NULL,
    completion_rule_snapshot_json NVARCHAR(MAX) NULL,
    updated_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    row_version ROWVERSION,
    CONSTRAINT pk_lesson_progress PRIMARY KEY (id),
    CONSTRAINT uq_lesson_progress_enrollment_period_id_lesson_id_1 UNIQUE (enrollment_period_id, lesson_id),
    CONSTRAINT ck_lesson_progress_1 CHECK (seconds_spent >= 0),
    CONSTRAINT ck_lesson_progress_2 CHECK (max_view_fraction >= 0 AND max_view_fraction <= 1),
    CONSTRAINT ck_lesson_progress_3 CHECK (completion_rule_snapshot_json IS NULL OR ISJSON(completion_rule_snapshot_json)=1),
    CONSTRAINT fk_lesson_progress_enrollment_period_id FOREIGN KEY (enrollment_period_id) REFERENCES enrollment_periods (id),
    CONSTRAINT fk_lesson_progress_lesson_id FOREIGN KEY (lesson_id) REFERENCES lessons (id)
);
GO

CREATE TABLE course_completion_summaries (
    id BIGINT IDENTITY(1,1) NOT NULL,
    student_user_id BIGINT NOT NULL,
    course_id BIGINT NOT NULL,
    ever_completed BIT NOT NULL DEFAULT (0),
    first_completed_at DATETIME2(3) NULL,
    latest_completed_at DATETIME2(3) NULL,
    final_aggregate_score DECIMAL(9,4) NULL,
    prerequisite_eligible BIT NOT NULL DEFAULT (0),
    source_period_id BIGINT NULL,
    updated_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    row_version ROWVERSION,
    CONSTRAINT pk_course_completion_summaries PRIMARY KEY (id),
    CONSTRAINT uq_course_completion_summaries_student_user_id_course_id_1 UNIQUE (student_user_id, course_id),
    CONSTRAINT ck_course_completion_summaries_1 CHECK (final_aggregate_score IS NULL OR final_aggregate_score >= 0),
    CONSTRAINT fk_course_completion_summaries_student_user_id FOREIGN KEY (student_user_id) REFERENCES users (id),
    CONSTRAINT fk_course_completion_summaries_course_id FOREIGN KEY (course_id) REFERENCES courses (id),
    CONSTRAINT fk_course_completion_summaries_source_period_id FOREIGN KEY (source_period_id) REFERENCES enrollment_periods (id) ON DELETE SET NULL
);
GO
