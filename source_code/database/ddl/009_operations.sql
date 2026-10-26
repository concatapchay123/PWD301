/*
PWD301 Database Architecture — Reference DDL
Engine: Microsoft SQL Server
All DATETIME2 values are UTC by application convention.
This is reference architecture, not evidence that migrations have been executed.
*/
SET XACT_ABORT ON;
GO

CREATE TABLE background_jobs (
    id BIGINT IDENTITY(1,1) NOT NULL,
    job_key UNIQUEIDENTIFIER NOT NULL DEFAULT (NEWID()),
    job_type VARCHAR(48) NOT NULL,
    dedupe_key NVARCHAR(200) NULL,
    status VARCHAR(20) NOT NULL DEFAULT ('QUEUED'),
    priority INT NOT NULL DEFAULT (100),
    attempt_count INT NOT NULL DEFAULT (0),
    max_attempts INT NOT NULL DEFAULT (5),
    available_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    claimed_at DATETIME2(3) NULL,
    lease_expires_at DATETIME2(3) NULL,
    completed_at DATETIME2(3) NULL,
    payload_json NVARCHAR(MAX) NULL,
    last_error NVARCHAR(2000) NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    row_version ROWVERSION,
    CONSTRAINT pk_background_jobs PRIMARY KEY (id),
    CONSTRAINT uq_background_jobs_job_key_1 UNIQUE (job_key),
    CONSTRAINT ck_background_jobs_1 CHECK (job_type IN ('FILE_SCAN','IMPORT','REGRADE','KNOWLEDGE_INDEX','EMAIL','CLEANUP','ANALYTICS','BACKUP','EXPORT')),
    CONSTRAINT ck_background_jobs_2 CHECK (status IN ('QUEUED','RUNNING','SUCCEEDED','FAILED','CANCELLED')),
    CONSTRAINT ck_background_jobs_3 CHECK (priority >= 0),
    CONSTRAINT ck_background_jobs_4 CHECK (attempt_count >= 0),
    CONSTRAINT ck_background_jobs_5 CHECK (max_attempts > 0),
    CONSTRAINT ck_background_jobs_6 CHECK (payload_json IS NULL OR ISJSON(payload_json)=1)
);
GO

CREATE TABLE system_alerts (
    id BIGINT IDENTITY(1,1) NOT NULL,
    alert_type VARCHAR(48) NOT NULL,
    severity VARCHAR(16) NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT ('OPEN'),
    source_type VARCHAR(32) NULL,
    source_id BIGINT NULL,
    message NVARCHAR(2000) NOT NULL,
    acknowledged_by_user_id BIGINT NULL,
    acknowledged_at DATETIME2(3) NULL,
    resolved_at DATETIME2(3) NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    row_version ROWVERSION,
    CONSTRAINT pk_system_alerts PRIMARY KEY (id),
    CONSTRAINT ck_system_alerts_1 CHECK (severity IN ('INFO','WARN','HIGH','CRITICAL')),
    CONSTRAINT ck_system_alerts_2 CHECK (status IN ('OPEN','ACKNOWLEDGED','RESOLVED')),
    CONSTRAINT fk_system_alerts_acknowledged_by_user_id FOREIGN KEY (acknowledged_by_user_id) REFERENCES users (id) ON DELETE SET NULL
);
GO

CREATE TABLE backup_runs (
    id BIGINT IDENTITY(1,1) NOT NULL,
    backup_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT ('RUNNING'),
    started_by_user_id BIGINT NULL,
    storage_location NVARCHAR(500) NOT NULL,
    database_backup_name NVARCHAR(255) NULL,
    file_manifest_name NVARCHAR(255) NULL,
    started_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    completed_at DATETIME2(3) NULL,
    verified_at DATETIME2(3) NULL,
    restore_tested_at DATETIME2(3) NULL,
    last_error NVARCHAR(2000) NULL,
    CONSTRAINT pk_backup_runs PRIMARY KEY (id),
    CONSTRAINT ck_backup_runs_1 CHECK (backup_type IN ('AUTOMATIC','MANUAL','RESTORE_DRILL')),
    CONSTRAINT ck_backup_runs_2 CHECK (status IN ('RUNNING','SUCCEEDED','FAILED')),
    CONSTRAINT fk_backup_runs_started_by_user_id FOREIGN KEY (started_by_user_id) REFERENCES users (id) ON DELETE SET NULL
);
GO

CREATE TABLE grade_exports (
    id BIGINT IDENTITY(1,1) NOT NULL,
    public_id UNIQUEIDENTIFIER NOT NULL DEFAULT (NEWSEQUENTIALID()),
    course_id BIGINT NOT NULL,
    requested_by_user_id BIGINT NOT NULL,
    background_job_id BIGINT NULL,
    file_asset_id BIGINT NULL,
    filters_json NVARCHAR(MAX) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT ('QUEUED'),
    row_count INT NULL,
    expires_at DATETIME2(3) NOT NULL,
    completed_at DATETIME2(3) NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    row_version ROWVERSION,
    CONSTRAINT pk_grade_exports PRIMARY KEY (id),
    CONSTRAINT uq_grade_exports_public_id_1 UNIQUE (public_id),
    CONSTRAINT ck_grade_exports_1 CHECK (filters_json IS NOT NULL AND ISJSON(filters_json)=1),
    CONSTRAINT ck_grade_exports_2 CHECK (status IN ('QUEUED','PROCESSING','READY','FAILED','EXPIRED')),
    CONSTRAINT ck_grade_exports_3 CHECK (row_count IS NULL OR row_count >= 0),
    CONSTRAINT fk_grade_exports_course_id FOREIGN KEY (course_id) REFERENCES courses (id),
    CONSTRAINT fk_grade_exports_requested_by_user_id FOREIGN KEY (requested_by_user_id) REFERENCES users (id),
    CONSTRAINT fk_grade_exports_file_asset_id FOREIGN KEY (file_asset_id) REFERENCES file_assets (id) ON DELETE SET NULL
);
GO

CREATE TABLE analytics_snapshots (
    id BIGINT IDENTITY(1,1) NOT NULL,
    scope_type VARCHAR(16) NOT NULL,
    scope_id BIGINT NULL,
    metric_code VARCHAR(64) NOT NULL,
    value_number DECIMAL(18,6) NULL,
    value_json NVARCHAR(MAX) NULL,
    as_of_at DATETIME2(3) NOT NULL,
    expires_at DATETIME2(3) NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT pk_analytics_snapshots PRIMARY KEY (id),
    CONSTRAINT ck_analytics_snapshots_1 CHECK (scope_type IN ('SYSTEM','COURSE','ASSESSMENT')),
    CONSTRAINT ck_analytics_snapshots_2 CHECK (value_json IS NULL OR ISJSON(value_json)=1)
);
GO

CREATE TABLE system_health_snapshots (
    id BIGINT IDENTITY(1,1) NOT NULL,
    component VARCHAR(32) NOT NULL,
    status VARCHAR(16) NOT NULL,
    latency_ms INT NULL,
    details_json NVARCHAR(MAX) NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT pk_system_health_snapshots PRIMARY KEY (id),
    CONSTRAINT ck_system_health_snapshots_1 CHECK (component IN ('WEB','DB','WORKER','CLAMAV','GEMINI','STORAGE','BACKUP')),
    CONSTRAINT ck_system_health_snapshots_2 CHECK (status IN ('HEALTHY','DEGRADED','DOWN','UNKNOWN')),
    CONSTRAINT ck_system_health_snapshots_3 CHECK (latency_ms IS NULL OR latency_ms >= 0),
    CONSTRAINT ck_system_health_snapshots_4 CHECK (details_json IS NULL OR ISJSON(details_json)=1)
);
GO
