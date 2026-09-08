/*
PWD301 Database Architecture — Reference DDL
Engine: Microsoft SQL Server
All DATETIME2 values are UTC by application convention.
This is reference architecture, not evidence that migrations have been executed.
*/
SET XACT_ABORT ON;
GO

CREATE TABLE users (
    id BIGINT IDENTITY(1,1) NOT NULL,
    public_id UNIQUEIDENTIFIER NOT NULL DEFAULT (NEWSEQUENTIALID()),
    email NVARCHAR(320) NOT NULL,
    email_normalized AS LOWER(LTRIM(RTRIM([email]))) PERSISTED,
    password_hash NVARCHAR(255) NOT NULL,
    display_name NVARCHAR(150) NOT NULL,
    avatar_file_asset_id BIGINT NULL,
    status VARCHAR(24) NOT NULL DEFAULT ('ACTIVE'),
    auth_version INT NOT NULL DEFAULT (1),
    email_verified_at DATETIME2(3) NULL,
    suspended_at DATETIME2(3) NULL,
    suspension_reason NVARCHAR(500) NULL,
    anonymized_at DATETIME2(3) NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    updated_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    row_version ROWVERSION,
    CONSTRAINT pk_users PRIMARY KEY (id),
    CONSTRAINT uq_users_public_id_1 UNIQUE (public_id),
    CONSTRAINT uq_users_email_normalized_2 UNIQUE (email_normalized),
    CONSTRAINT ck_users_1 CHECK (status IN ('ACTIVE','SUSPENDED','DEACTIVATED','ANONYMIZED')),
    CONSTRAINT ck_users_2 CHECK (auth_version >= 1)
);
GO

CREATE TABLE roles (
    id BIGINT IDENTITY(1,1) NOT NULL,
    code VARCHAR(32) NOT NULL,
    name NVARCHAR(100) NOT NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT pk_roles PRIMARY KEY (id),
    CONSTRAINT uq_roles_code_1 UNIQUE (code),
    CONSTRAINT ck_roles_1 CHECK (code IN ('STUDENT','INSTRUCTOR','ADMIN'))
);
GO

CREATE TABLE user_roles (
    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    assigned_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    assigned_by_user_id BIGINT NULL,
    assignment_reason NVARCHAR(500) NULL,
    CONSTRAINT pk_user_roles PRIMARY KEY (user_id, role_id),
    CONSTRAINT fk_user_roles_user_id FOREIGN KEY (user_id) REFERENCES users (id),
    CONSTRAINT fk_user_roles_role_id FOREIGN KEY (role_id) REFERENCES roles (id),
    CONSTRAINT fk_user_roles_assigned_by_user_id FOREIGN KEY (assigned_by_user_id) REFERENCES users (id) ON DELETE SET NULL
);
GO

CREATE TABLE auth_sessions (
    id BIGINT IDENTITY(1,1) NOT NULL,
    session_key_hash BINARY(32) NOT NULL,
    user_id BIGINT NOT NULL,
    auth_version INT NOT NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    last_seen_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    expires_at DATETIME2(3) NOT NULL,
    revoked_at DATETIME2(3) NULL,
    reauthenticated_at DATETIME2(3) NULL,
    ip_address VARCHAR(45) NULL,
    user_agent_hash BINARY(32) NULL,
    row_version ROWVERSION,
    CONSTRAINT pk_auth_sessions PRIMARY KEY (id),
    CONSTRAINT uq_auth_sessions_session_key_hash_1 UNIQUE (session_key_hash),
    CONSTRAINT ck_auth_sessions_1 CHECK (expires_at > created_at),
    CONSTRAINT fk_auth_sessions_user_id FOREIGN KEY (user_id) REFERENCES users (id)
);
GO

CREATE TABLE jwt_token_grants (
    id BIGINT IDENTITY(1,1) NOT NULL,
    jti UNIQUEIDENTIFIER NOT NULL,
    user_id BIGINT NOT NULL,
    session_family_id UNIQUEIDENTIFIER NOT NULL DEFAULT (NEWID()),
    auth_version INT NOT NULL,
    token_type VARCHAR(16) NOT NULL,
    issued_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    expires_at DATETIME2(3) NOT NULL,
    revoked_at DATETIME2(3) NULL,
    replaced_by_jti UNIQUEIDENTIFIER NULL,
    token_hash BINARY(32) NULL,
    CONSTRAINT pk_jwt_token_grants PRIMARY KEY (id),
    CONSTRAINT uq_jwt_token_grants_jti_1 UNIQUE (jti),
    CONSTRAINT ck_jwt_token_grants_1 CHECK (token_type IN ('ACCESS','REFRESH')),
    CONSTRAINT ck_jwt_token_grants_2 CHECK (expires_at > issued_at),
    CONSTRAINT fk_jwt_token_grants_user_id FOREIGN KEY (user_id) REFERENCES users (id)
);
GO

CREATE TABLE user_security_tokens (
    id BIGINT IDENTITY(1,1) NOT NULL,
    user_id BIGINT NOT NULL,
    purpose VARCHAR(32) NOT NULL,
    token_hash BINARY(32) NOT NULL,
    pending_email NVARCHAR(320) NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    expires_at DATETIME2(3) NOT NULL,
    consumed_at DATETIME2(3) NULL,
    CONSTRAINT pk_user_security_tokens PRIMARY KEY (id),
    CONSTRAINT uq_user_security_tokens_token_hash_1 UNIQUE (token_hash),
    CONSTRAINT ck_user_security_tokens_1 CHECK (purpose IN ('EMAIL_VERIFY','EMAIL_CHANGE','PASSWORD_RESET')),
    CONSTRAINT ck_user_security_tokens_2 CHECK (expires_at > created_at),
    CONSTRAINT fk_user_security_tokens_user_id FOREIGN KEY (user_id) REFERENCES users (id)
);
GO

CREATE TABLE instructor_applications (
    id BIGINT IDENTITY(1,1) NOT NULL,
    applicant_user_id BIGINT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT ('PENDING'),
    application_note NVARCHAR(2000) NULL,
    reviewed_by_user_id BIGINT NULL,
    review_reason NVARCHAR(1000) NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    reviewed_at DATETIME2(3) NULL,
    row_version ROWVERSION,
    CONSTRAINT pk_instructor_applications PRIMARY KEY (id),
    CONSTRAINT ck_instructor_applications_1 CHECK (status IN ('PENDING','APPROVED','REJECTED','CANCELLED')),
    CONSTRAINT fk_instructor_applications_applicant_user_id FOREIGN KEY (applicant_user_id) REFERENCES users (id),
    CONSTRAINT fk_instructor_applications_reviewed_by_user_id FOREIGN KEY (reviewed_by_user_id) REFERENCES users (id) ON DELETE SET NULL
);
GO

CREATE TABLE security_events (
    id BIGINT IDENTITY(1,1) NOT NULL,
    user_id BIGINT NULL,
    event_type VARCHAR(64) NOT NULL,
    severity VARCHAR(16) NOT NULL,
    action_taken VARCHAR(64) NOT NULL,
    risk_score DECIMAL(5,2) NULL,
    input_hash BINARY(32) NULL,
    ip_address VARCHAR(45) NULL,
    correlation_id UNIQUEIDENTIFIER NOT NULL DEFAULT (NEWID()),
    metadata_json NVARCHAR(MAX) NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT pk_security_events PRIMARY KEY (id),
    CONSTRAINT ck_security_events_1 CHECK (severity IN ('INFO','WARN','HIGH','CRITICAL')),
    CONSTRAINT ck_security_events_2 CHECK (action_taken IN ('ALLOW','BLOCK','REVOKE','QUARANTINE','ALERT')),
    CONSTRAINT ck_security_events_3 CHECK (risk_score IS NULL OR (risk_score >= 0 AND risk_score <= 100)),
    CONSTRAINT ck_security_events_4 CHECK (metadata_json IS NULL OR ISJSON(metadata_json)=1),
    CONSTRAINT fk_security_events_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
);
GO
