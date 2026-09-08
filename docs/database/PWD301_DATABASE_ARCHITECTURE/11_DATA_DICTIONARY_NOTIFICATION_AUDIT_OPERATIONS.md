# 11 DATA DICTIONARY NOTIFICATION AUDIT OPERATIONS

Database engine: **Microsoft SQL Server**. Timestamps are UTC `DATETIME2(3)` unless noted.

## `notification_events`

**Purpose**

Business event fan-out source for in-app notification/email; dedupe retries via event_key.

**Lifecycle**

Append; fan-out to notifications/email deliveries.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `event_key` | `UNIQUEIDENTIFIER` | No | `NEWID()` | Stable idempotency event key |
| `event_type` | `VARCHAR(64)` | No |  | SCORE_CHANGED/ROLE_CHANGED/ASSESSMENT_REMINDER/... |
| `actor_user_id` | `BIGINT` | Yes |  | Actor nếu có |
| `target_type` | `VARCHAR(32)` | Yes |  | COURSE/ASSESSMENT/ATTEMPT/USER/QUESTION/SYSTEM |
| `target_id` | `BIGINT` | Yes |  | Target id |
| `correlation_id` | `UNIQUEIDENTIFIER` | Yes |  | Request/job correlation |
| `payload_json` | `NVARCHAR(MAX)` | Yes |  | Template data sanitized |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `actor_user_id` | `users(id)` | `SET NULL` |  |

### Unique Constraints

- `UNIQUE (event_key)`

### Check Constraints

- `payload_json IS NULL OR ISJSON(payload_json)=1`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_notification_events_type_time` | `event_type, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Operational cleanup allowed after child deliveries aged out if AuditEvent retains durable security facts.

### Audit behavior

Not equivalent to AuditEvent.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Payload must not include password/token/raw sensitive answer.

### Important invariants

- Producer reuses same event_key on retry to avoid duplicate fan-out

---

## `notifications`

**Purpose**

In-app notification per recipient với read/unread và retention.

**Lifecycle**

Unread → read; cleanup ordinary notifications after expiry.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `public_id` | `UNIQUEIDENTIFIER` | No | `NEWSEQUENTIALID()` | ID công khai dùng trong URL/API; không thay thế kiểm tra quyền |
| `notification_event_id` | `BIGINT` | No |  | Event |
| `recipient_user_id` | `BIGINT` | No |  | Recipient |
| `category` | `VARCHAR(32)` | No |  | SECURITY/COURSE/ASSESSMENT/GRADE/SYSTEM |
| `title` | `NVARCHAR(250)` | No |  | Title |
| `body` | `NVARCHAR(2000)` | No |  | Body |
| `read_at` | `DATETIME2(3)` | Yes |  | Read time |
| `expires_at` | `DATETIME2(3)` | Yes |  | Cleanup low-value |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `notification_event_id` | `notification_events(id)` | `NO ACTION` |  |
| `recipient_user_id` | `users(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (notification_event_id, recipient_user_id)`

### Check Constraints

- `category IN ('SECURITY','COURSE','ASSESSMENT','GRADE','SYSTEM')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_notifications_user_unread` | `recipient_user_id, created_at` | No | `read_at IS NULL` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_notifications_expiry` | `expires_at, id` | No | `expires_at IS NOT NULL` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Low-value hard-delete after expiry; security fact remains Audit/SecurityEvent.

### Audit behavior

No audit for marking read.

### Concurrency

row_version for read update; idempotent event+recipient unique.

### Security / PII classification

Recipient-only; Admin cannot browse arbitrary content without reason where sensitive.

### Important invariants

- Score/role/suspension notifications created when required

---

## `notification_preferences`

**Purpose**

User preferences cho optional email categories; mandatory security email không disable.

**Lifecycle**

Upsert preferences.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `user_id` | `BIGINT` | No |  | User |
| `category` | `VARCHAR(32)` | No |  | COURSE/ASSESSMENT/GRADE/MARKETING/SECURITY |
| `email_enabled` | `BIT` | No |  | Enable email |
| `updated_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | UTC |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`user_id, category`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `user_id` | `users(id)` | `NO ACTION` |  |

### Unique Constraints

_None._

### Check Constraints

- `category IN ('COURSE','ASSESSMENT','GRADE','MARKETING','SECURITY')`
- `category <> 'SECURITY' OR email_enabled = 1`

### Indexes

_None._

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Can delete with account anonymization if no need.

### Audit behavior

Security category change attempt may log if blocked.

### Concurrency

row_version.

### Security / PII classification

Preference data low sensitivity.

### Important invariants

- SECURITY.email_enabled must remain 1 (DB check via composite logic/service; DDL trigger/check where possible)

---

## `email_deliveries`

**Purpose**

Outbox/retry record cho email; primary business transaction không rollback do external send fail.

**Lifecycle**

PENDING → SENDING → SENT; fail → retry/FAILED.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `notification_event_id` | `BIGINT` | No |  | Event |
| `recipient_user_id` | `BIGINT` | Yes |  | User |
| `recipient_email_snapshot` | `NVARCHAR(320)` | No |  | Email destination snapshot |
| `template_code` | `VARCHAR(64)` | No |  | Template |
| `dedupe_key` | `UNIQUEIDENTIFIER` | No |  | Stable delivery idempotency key |
| `status` | `VARCHAR(20)` | No | `'PENDING'` | PENDING/SENDING/SENT/FAILED/CANCELLED |
| `attempt_count` | `INT` | No | `0` | Retries |
| `next_attempt_at` | `DATETIME2(3)` | Yes |  | Retry time |
| `sent_at` | `DATETIME2(3)` | Yes |  | UTC |
| `last_error` | `NVARCHAR(2000)` | Yes |  | Sanitized |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `notification_event_id` | `notification_events(id)` | `NO ACTION` |  |
| `recipient_user_id` | `users(id)` | `SET NULL` |  |

### Unique Constraints

- `UNIQUE (dedupe_key)`
- `UNIQUE (notification_event_id, recipient_email_snapshot, template_code)`

### Check Constraints

- `status IN ('PENDING','SENDING','SENT','FAILED','CANCELLED')`
- `attempt_count >= 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_email_delivery_queue` | `status, next_attempt_at, id` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_email_delivery_event` | `notification_event_id, status` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Operational retention after delivery; security event remains audit if needed.

### Audit behavior

Email send failure not business rollback.

### Concurrency

row_version + worker claim conditional.

### Security / PII classification

Email address PII; no sensitive body stored here.

### Important invariants

- Retry cannot duplicate logical email
- Mandatory security email ignores optional preference

---

## `audit_events`

**Purpose**

Append-only authoritative audit cho hành động Admin/Instructor quan trọng và score/security-sensitive actions.

**Lifecycle**

Append-only; very old data may move to archival storage.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `event_id` | `UNIQUEIDENTIFIER` | No | `NEWID()` | Public/correlation id |
| `actor_user_id` | `BIGINT` | Yes |  | Actor |
| `actor_roles_snapshot` | `NVARCHAR(200)` | No |  | Roles at action time |
| `action` | `VARCHAR(80)` | No |  | Action code |
| `target_type` | `VARCHAR(40)` | No |  | Target type |
| `target_id` | `BIGINT` | Yes |  | Target internal id |
| `reason` | `NVARCHAR(1000)` | Yes |  | Reason; required for sensitive actions |
| `before_json` | `NVARCHAR(MAX)` | Yes |  | Redacted before metadata |
| `after_json` | `NVARCHAR(MAX)` | Yes |  | Redacted after metadata |
| `request_id` | `UNIQUEIDENTIFIER` | Yes |  | Request correlation |
| `ip_address` | `VARCHAR(45)` | Yes |  | IP |
| `performed_as_admin` | `BIT` | No | `0` | Admin override/edit context |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `actor_user_id` | `users(id)` | `SET NULL` |  |

### Unique Constraints

- `UNIQUE (event_id)`

### Check Constraints

- `before_json IS NULL OR ISJSON(before_json)=1`
- `after_json IS NULL OR ISJSON(after_json)=1`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_audit_time` | `created_at, id` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_audit_actor_time` | `actor_user_id, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_audit_target` | `target_type, target_id, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_audit_action_time` | `action, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

App principal không có UPDATE/DELETE. Archive chỉ bằng privileged maintenance path.

### Audit behavior

Self-auditing; correction tạo new event.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Sensitive; redaction mandatory. Never password_hash/token/API key/raw answer bodies unless explicit minimal evidence.

### Important invariants

- Sensitive/destructive action must fail if required audit insert cannot commit
- No impersonation; actor is true authenticated admin/instructor

---

## `background_jobs`

**Purpose**

Generic persistence cho queue/retry common mechanics; complex domain progress stays in regrade/import/version tables.

**Lifecycle**

QUEUED → RUNNING → SUCCEEDED; failures retry by available_at until FAILED.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `job_key` | `UNIQUEIDENTIFIER` | No | `NEWID()` | Public job key |
| `job_type` | `VARCHAR(48)` | No |  | FILE_SCAN/IMPORT/REGRADE/KNOWLEDGE_INDEX/EMAIL/CLEANUP/ANALYTICS/BACKUP/EXPORT |
| `dedupe_key` | `NVARCHAR(200)` | Yes |  | Optional business idempotency key |
| `status` | `VARCHAR(20)` | No | `'QUEUED'` | QUEUED/RUNNING/SUCCEEDED/FAILED/CANCELLED |
| `priority` | `INT` | No | `100` | Queue priority |
| `attempt_count` | `INT` | No | `0` | Retries |
| `max_attempts` | `INT` | No | `5` | Max retries |
| `available_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Earliest run |
| `claimed_at` | `DATETIME2(3)` | Yes |  | Worker claim |
| `lease_expires_at` | `DATETIME2(3)` | Yes |  | Worker claim lease |
| `completed_at` | `DATETIME2(3)` | Yes |  | UTC |
| `payload_json` | `NVARCHAR(MAX)` | Yes |  | Small sanitized args; no giant document/raw secret |
| `last_error` | `NVARCHAR(2000)` | Yes |  | Sanitized |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

_None._

### Unique Constraints

- `UNIQUE (job_key)`

### Check Constraints

- `job_type IN ('FILE_SCAN','IMPORT','REGRADE','KNOWLEDGE_INDEX','EMAIL','CLEANUP','ANALYTICS','BACKUP','EXPORT')`
- `status IN ('QUEUED','RUNNING','SUCCEEDED','FAILED','CANCELLED')`
- `priority >= 0`
- `attempt_count >= 0`
- `max_attempts > 0`
- `payload_json IS NULL OR ISJSON(payload_json)=1`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_jobs_claim` | `status, available_at, priority, id` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ux_jobs_dedupe` | `job_type, dedupe_key` | Yes | `dedupe_key IS NOT NULL` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Operational history cleanup allowed; domain history remains.

### Audit behavior

Operational, not AuditEvent.

### Concurrency

row_version + claimed lease; stale RUNNING can be reclaimed safely by idempotent handler.

### Security / PII classification

Payload minimal/no secrets.

### Important invariants

- Handlers idempotent
- Generic table handles queue mechanics only; domain-specific state stays normalized

---

## `system_alerts`

**Purpose**

Admin-facing alerts for suspicious/operational conditions.

**Lifecycle**

OPEN → ACKNOWLEDGED → RESOLVED.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `alert_type` | `VARCHAR(48)` | No |  | LOW_STORAGE/BACKUP_FAILED/MALWARE/PROMPT_INJECTION/SERVICE_DOWN/... |
| `severity` | `VARCHAR(16)` | No |  | INFO/WARN/HIGH/CRITICAL |
| `status` | `VARCHAR(16)` | No | `'OPEN'` | OPEN/ACKNOWLEDGED/RESOLVED |
| `source_type` | `VARCHAR(32)` | Yes |  | SECURITY_EVENT/JOB/HEALTH/FILE/OTHER |
| `source_id` | `BIGINT` | Yes |  | Source id |
| `message` | `NVARCHAR(2000)` | No |  | Safe admin message |
| `acknowledged_by_user_id` | `BIGINT` | Yes |  | Admin |
| `acknowledged_at` | `DATETIME2(3)` | Yes |  | UTC |
| `resolved_at` | `DATETIME2(3)` | Yes |  | UTC |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `acknowledged_by_user_id` | `users(id)` | `SET NULL` |  |

### Unique Constraints

_None._

### Check Constraints

- `severity IN ('INFO','WARN','HIGH','CRITICAL')`
- `status IN ('OPEN','ACKNOWLEDGED','RESOLVED')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_system_alerts_open` | `status, severity, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_system_alerts_type` | `alert_type, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Operational cleanup after retention; underlying audit/security facts keep as needed.

### Audit behavior

Ack/resolution not necessarily security audit unless critical.

### Concurrency

row_version.

### Security / PII classification

Admin-only.

### Important invariants

- Low disk may block upload via service independent of UI alert acknowledgment

---

## `backup_runs`

**Purpose**

Metadata của backup tự động hằng ngày/manual và restore drills; không chứa backup bytes.

**Lifecycle**

RUNNING → SUCCEEDED/FAILED; verification/drill update metadata.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `backup_type` | `VARCHAR(20)` | No |  | AUTOMATIC/MANUAL/RESTORE_DRILL |
| `status` | `VARCHAR(20)` | No | `'RUNNING'` | RUNNING/SUCCEEDED/FAILED |
| `started_by_user_id` | `BIGINT` | Yes |  | Admin nếu manual |
| `storage_location` | `NVARCHAR(500)` | No |  | Logical backup destination, no secret |
| `database_backup_name` | `NVARCHAR(255)` | Yes |  | DB backup artifact |
| `file_manifest_name` | `NVARCHAR(255)` | Yes |  | Files manifest |
| `started_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | UTC |
| `completed_at` | `DATETIME2(3)` | Yes |  | UTC |
| `verified_at` | `DATETIME2(3)` | Yes |  | Integrity check |
| `restore_tested_at` | `DATETIME2(3)` | Yes |  | Restore drill |
| `last_error` | `NVARCHAR(2000)` | Yes |  | Sanitized |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `started_by_user_id` | `users(id)` | `SET NULL` |  |

### Unique Constraints

_None._

### Check Constraints

- `backup_type IN ('AUTOMATIC','MANUAL','RESTORE_DRILL')`
- `status IN ('RUNNING','SUCCEEDED','FAILED')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_backup_runs_time` | `started_at, status` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Retain operationally according to backup policy; never treat Docker volume as backup.

### Audit behavior

Manual backup/restore action audit. Restore database requires explicit Admin confirmation and separate audit.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Location metadata only; credentials/secrets not stored.

### Important invariants

- No automatic live DB restore from backup
- Daily automatic schedule tracked

---

## `grade_exports`

**Purpose**

Sensitive CSV/Excel export request/file lifecycle với giới hạn kích thước và expiry.

**Lifecycle**

QUEUED → PROCESSING → READY → EXPIRED; failed retry as controlled job.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `public_id` | `UNIQUEIDENTIFIER` | No | `NEWSEQUENTIALID()` | ID công khai dùng trong URL/API; không thay thế kiểm tra quyền |
| `course_id` | `BIGINT` | No |  | Course |
| `requested_by_user_id` | `BIGINT` | No |  | Instructor/Admin |
| `background_job_id` | `BIGINT` | Yes |  | Job; FK deferred |
| `file_asset_id` | `BIGINT` | Yes |  | Generated sensitive asset |
| `filters_json` | `NVARCHAR(MAX)` | No |  | Applied filters |
| `status` | `VARCHAR(20)` | No | `'QUEUED'` | QUEUED/PROCESSING/READY/FAILED/EXPIRED |
| `row_count` | `INT` | Yes |  | Rows exported |
| `expires_at` | `DATETIME2(3)` | No |  | Auto-delete generated file |
| `completed_at` | `DATETIME2(3)` | Yes |  | UTC |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `course_id` | `courses(id)` | `NO ACTION` |  |
| `requested_by_user_id` | `users(id)` | `NO ACTION` |  |
| `file_asset_id` | `file_assets(id)` | `SET NULL` |  |
| `background_job_id` | `background_jobs(id)` | `SET NULL` | Deferred cross-domain FK created in `010_cross_domain_constraints.sql`. |

### Unique Constraints

- `UNIQUE (public_id)`

### Check Constraints

- `filters_json IS NOT NULL AND ISJSON(filters_json)=1`
- `status IN ('QUEUED','PROCESSING','READY','FAILED','EXPIRED')`
- `row_count IS NULL OR row_count >= 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_grade_exports_user` | `requested_by_user_id, status, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_grade_exports_expiry` | `expires_at, status` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Generated file deleted at expires_at; export metadata short retention.

### Audit behavior

Export request is sensitive action; audit who exported which Course/filter scope.

### Concurrency

row_version.

### Security / PII classification

Sensitive; download authorized requester/admin; never public URL.

### Important invariants

- Size/row limits enforced before/while build

---

## `analytics_snapshots`

**Purpose**

Derived/cache metrics cho Dashboard; source of truth vẫn normalized learning/assessment data.

**Lifecycle**

Recomputed/replace cache; not historical truth unless specifically retained.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `scope_type` | `VARCHAR(16)` | No |  | SYSTEM/COURSE/ASSESSMENT |
| `scope_id` | `BIGINT` | Yes |  | Course/Assessment id |
| `metric_code` | `VARCHAR(64)` | No |  | Metric |
| `value_number` | `DECIMAL(18,6)` | Yes |  | Numeric metric |
| `value_json` | `NVARCHAR(MAX)` | Yes |  | Structured aggregate |
| `as_of_at` | `DATETIME2(3)` | No |  | Data timestamp |
| `expires_at` | `DATETIME2(3)` | Yes |  | Refresh deadline |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

_None._

### Unique Constraints

_None._

### Check Constraints

- `scope_type IN ('SYSTEM','COURSE','ASSESSMENT')`
- `value_json IS NULL OR ISJSON(value_json)=1`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_analytics_scope_metric` | `scope_type, scope_id, metric_code, as_of_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Safe to cleanup/recompute.

### Audit behavior

No.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Aggregates; individual details not stored here by default.

### Important invariants

- Derived values must be recomputable

---

## `system_health_snapshots`

**Purpose**

Short-retention health metadata cho Admin Dashboard (DB/worker/ClamAV/Gemini/storage).

**Lifecycle**

Append periodic snapshots; short retention.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `component` | `VARCHAR(32)` | No |  | WEB/DB/WORKER/CLAMAV/GEMINI/STORAGE/BACKUP |
| `status` | `VARCHAR(16)` | No |  | HEALTHY/DEGRADED/DOWN/UNKNOWN |
| `latency_ms` | `INT` | Yes |  | Observed latency |
| `details_json` | `NVARCHAR(MAX)` | Yes |  | Sanitized health metadata |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

_None._

### Unique Constraints

_None._

### Check Constraints

- `component IN ('WEB','DB','WORKER','CLAMAV','GEMINI','STORAGE','BACKUP')`
- `status IN ('HEALTHY','DEGRADED','DOWN','UNKNOWN')`
- `latency_ms IS NULL OR latency_ms >= 0`
- `details_json IS NULL OR ISJSON(details_json)=1`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_health_component_time` | `component, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Cleanup old snapshots; durable failures create system_alert/security/audit as appropriate.

### Audit behavior

No.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Admin-only; details must not expose secrets.

### Important invariants

- Operational telemetry is not business source of truth

---
