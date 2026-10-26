/*
PWD301 Database Architecture — Reference DDL
Engine: Microsoft SQL Server
All DATETIME2 values are UTC by application convention.
This is reference architecture, not evidence that migrations have been executed.
*/
SET XACT_ABORT ON;
GO

CREATE TABLE notification_events (
    id BIGINT IDENTITY(1,1) NOT NULL,
    event_key UNIQUEIDENTIFIER NOT NULL DEFAULT (NEWID()),
    event_type VARCHAR(64) NOT NULL,
    actor_user_id BIGINT NULL,
    target_type VARCHAR(32) NULL,
    target_id BIGINT NULL,
    correlation_id UNIQUEIDENTIFIER NULL,
    payload_json NVARCHAR(MAX) NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT pk_notification_events PRIMARY KEY (id),
    CONSTRAINT uq_notification_events_event_key_1 UNIQUE (event_key),
    CONSTRAINT ck_notification_events_1 CHECK (payload_json IS NULL OR ISJSON(payload_json)=1),
    CONSTRAINT fk_notification_events_actor_user_id FOREIGN KEY (actor_user_id) REFERENCES users (id) ON DELETE SET NULL
);
GO

CREATE TABLE notifications (
    id BIGINT IDENTITY(1,1) NOT NULL,
    public_id UNIQUEIDENTIFIER NOT NULL DEFAULT (NEWSEQUENTIALID()),
    notification_event_id BIGINT NOT NULL,
    recipient_user_id BIGINT NOT NULL,
    category VARCHAR(32) NOT NULL,
    title NVARCHAR(250) NOT NULL,
    body NVARCHAR(2000) NOT NULL,
    read_at DATETIME2(3) NULL,
    expires_at DATETIME2(3) NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    row_version ROWVERSION,
    CONSTRAINT pk_notifications PRIMARY KEY (id),
    CONSTRAINT uq_notifications_notification_event_id_recipient_user_id_1 UNIQUE (notification_event_id, recipient_user_id),
    CONSTRAINT ck_notifications_1 CHECK (category IN ('SECURITY','COURSE','ASSESSMENT','GRADE','SYSTEM')),
    CONSTRAINT fk_notifications_notification_event_id FOREIGN KEY (notification_event_id) REFERENCES notification_events (id),
    CONSTRAINT fk_notifications_recipient_user_id FOREIGN KEY (recipient_user_id) REFERENCES users (id)
);
GO

CREATE TABLE notification_preferences (
    user_id BIGINT NOT NULL,
    category VARCHAR(32) NOT NULL,
    email_enabled BIT NOT NULL,
    updated_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    row_version ROWVERSION,
    CONSTRAINT pk_notification_preferences PRIMARY KEY (user_id, category),
    CONSTRAINT ck_notification_preferences_1 CHECK (category IN ('COURSE','ASSESSMENT','GRADE','MARKETING','SECURITY')),
    CONSTRAINT ck_notification_preferences_2 CHECK (category <> 'SECURITY' OR email_enabled = 1),
    CONSTRAINT fk_notification_preferences_user_id FOREIGN KEY (user_id) REFERENCES users (id)
);
GO

CREATE TABLE email_deliveries (
    id BIGINT IDENTITY(1,1) NOT NULL,
    notification_event_id BIGINT NOT NULL,
    recipient_user_id BIGINT NULL,
    recipient_email_snapshot NVARCHAR(320) NOT NULL,
    template_code VARCHAR(64) NOT NULL,
    dedupe_key UNIQUEIDENTIFIER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT ('PENDING'),
    attempt_count INT NOT NULL DEFAULT (0),
    next_attempt_at DATETIME2(3) NULL,
    sent_at DATETIME2(3) NULL,
    last_error NVARCHAR(2000) NULL,
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    row_version ROWVERSION,
    CONSTRAINT pk_email_deliveries PRIMARY KEY (id),
    CONSTRAINT uq_email_deliveries_dedupe_key_1 UNIQUE (dedupe_key),
    CONSTRAINT uq_email_deliveries_notification_event_id_recipient_email_snapshot_template_code_2 UNIQUE (notification_event_id, recipient_email_snapshot, template_code),
    CONSTRAINT ck_email_deliveries_1 CHECK (status IN ('PENDING','SENDING','SENT','FAILED','CANCELLED')),
    CONSTRAINT ck_email_deliveries_2 CHECK (attempt_count >= 0),
    CONSTRAINT fk_email_deliveries_notification_event_id FOREIGN KEY (notification_event_id) REFERENCES notification_events (id),
    CONSTRAINT fk_email_deliveries_recipient_user_id FOREIGN KEY (recipient_user_id) REFERENCES users (id) ON DELETE SET NULL
);
GO

CREATE TABLE audit_events (
    id BIGINT IDENTITY(1,1) NOT NULL,
    event_id UNIQUEIDENTIFIER NOT NULL DEFAULT (NEWID()),
    actor_user_id BIGINT NULL,
    actor_roles_snapshot NVARCHAR(200) NOT NULL,
    action VARCHAR(80) NOT NULL,
    target_type VARCHAR(40) NOT NULL,
    target_id BIGINT NULL,
    reason NVARCHAR(1000) NULL,
    before_json NVARCHAR(MAX) NULL,
    after_json NVARCHAR(MAX) NULL,
    request_id UNIQUEIDENTIFIER NULL,
    ip_address VARCHAR(45) NULL,
    performed_as_admin BIT NOT NULL DEFAULT (0),
    created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT pk_audit_events PRIMARY KEY (id),
    CONSTRAINT uq_audit_events_event_id_1 UNIQUE (event_id),
    CONSTRAINT ck_audit_events_1 CHECK (before_json IS NULL OR ISJSON(before_json)=1),
    CONSTRAINT ck_audit_events_2 CHECK (after_json IS NULL OR ISJSON(after_json)=1),
    CONSTRAINT fk_audit_events_actor_user_id FOREIGN KEY (actor_user_id) REFERENCES users (id) ON DELETE SET NULL
);
GO
