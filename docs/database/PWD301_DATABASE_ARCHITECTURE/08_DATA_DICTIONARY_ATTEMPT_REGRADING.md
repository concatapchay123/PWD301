# 08 DATA DICTIONARY ATTEMPT REGRADING

Database engine: **Microsoft SQL Server**. Timestamps are UTC `DATETIME2(3)` unless noted.

## `assessment_attempts`

**Purpose**

Một lượt làm bài cụ thể của Student, chứa timer authoritative, lease tab, submit idempotency và lifecycle.

**Lifecycle**

CREATED → IN_PROGRESS → SUBMITTED/EXPIRED → PENDING_GRADING/GRADED; Assessment cancel có thể → CANCELLED.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `public_id` | `UNIQUEIDENTIFIER` | No | `NEWSEQUENTIALID()` | ID công khai dùng trong URL/API; không thay thế kiểm tra quyền |
| `assessment_id` | `BIGINT` | No |  | Assessment |
| `enrollment_period_id` | `BIGINT` | No |  | Period học hiện hành |
| `student_user_id` | `BIGINT` | No |  | Student |
| `attempt_number` | `INT` | No |  | Lần làm 1..N |
| `status` | `VARCHAR(28)` | No |  | CREATED/IN_PROGRESS/SUBMITTED/EXPIRED/CANCELLED/PENDING_GRADING/GRADED |
| `started_at` | `DATETIME2(3)` | Yes |  | Server start |
| `deadline_at` | `DATETIME2(3)` | Yes |  | min(start+time_limit, close_at) |
| `submitted_at` | `DATETIME2(3)` | Yes |  | Submit client/server |
| `finalized_at` | `DATETIME2(3)` | Yes |  | Server finalize |
| `graded_at` | `DATETIME2(3)` | Yes |  | Final grading complete |
| `submission_idempotency_key` | `UNIQUEIDENTIFIER` | Yes |  | Key lần submit đầu; retry trả same result |
| `editor_session_id` | `BIGINT` | Yes |  | Auth session đang giữ quyền edit |
| `lease_token_hash` | `BINARY(32)` | Yes |  | Hash lease token, không lưu raw |
| `lease_acquired_at` | `DATETIME2(3)` | Yes |  | UTC |
| `lease_expires_at` | `DATETIME2(3)` | Yes |  | UTC |
| `last_heartbeat_at` | `DATETIME2(3)` | Yes |  | UTC |
| `lease_epoch` | `INT` | No | `1` | Lease epoch fencing cho multi-tab takeover & autosave sequence collision prevention |
| `is_detail_purged` | `BIT` | No | `0` | Cờ skeleton tombstone: chi tiết bài thi đã purge sau 30 ngày |
| `detail_purged_at` | `DATETIME2(3)` | Yes |  | Thời điểm thực hiện skeleton tombstone purge (UTC) |
| `cancel_reason` | `NVARCHAR(1000)` | Yes |  | Nếu cancelled |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `updated_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm cập nhật cuối (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `assessment_id` | `assessments(id)` | `NO ACTION` |  |
| `enrollment_period_id` | `enrollment_periods(id)` | `NO ACTION` |  |
| `student_user_id` | `users(id)` | `NO ACTION` |  |
| `editor_session_id` | `auth_sessions(id)` | `SET NULL` |  |

### Unique Constraints

- `UNIQUE (public_id)`
- `UNIQUE (assessment_id, student_user_id, attempt_number)`

### Check Constraints

- `attempt_number > 0`
- `status IN ('CREATED','IN_PROGRESS','SUBMITTED','EXPIRED','CANCELLED','PENDING_GRADING','GRADED')`
- `deadline_at IS NULL OR started_at IS NULL OR deadline_at >= started_at`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_attempts_student_assessment` | `student_user_id, assessment_id, attempt_number` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_attempts_assessment_status` | `assessment_id, status, started_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_attempts_period_status` | `enrollment_period_id, status` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_attempts_lease_expiry` | `lease_expires_at, status` | No | `status='IN_PROGRESS'` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ux_attempt_submit_key` | `submission_idempotency_key` | Yes | `submission_idempotency_key IS NOT NULL` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Detailed attempt có thể purge sau Enrollment period retention >30 ngày; nếu còn trong retention/history thì không cascade-delete. Assessment itself vẫn giữ historical integrity.

### Audit behavior

Không audit mọi autosave; submit/manual grade/regrade/cancel quan trọng được lưu domain history.

### Concurrency

row_version + short transaction. Lease dùng expiry/heartbeat, không giữ DB row lock dài hạn.

### Security / PII classification

Student-sensitive; ownership phải khớp authenticated user.

### Important invariants

- Server time authoritative
- Attempt count/limit transaction-safe
- Only one active editor lease
- submit idempotent
- deadline never extended by client clock

---

## `attempt_questions`

**Purpose**

Snapshot đầy đủ của câu mà Student thực sự thấy; không đổi khi QuestionRevision tương lai thay đổi.

**Lifecycle**

Insert atomic khi start Attempt; immutable ngoại trừ marker correction metadata.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `attempt_id` | `BIGINT` | No |  | Attempt |
| `source_question_id` | `BIGINT` | No |  | Question identity |
| `source_question_revision_id` | `BIGINT` | No |  | Revision hiển thị ban đầu |
| `section_id` | `BIGINT` | Yes |  | Section source |
| `position` | `INT` | No |  | Thứ tự thật trong Attempt |
| `question_type_snapshot` | `VARCHAR(24)` | No |  | Type student saw |
| `content_snapshot` | `NVARCHAR(MAX)` | No |  | Question text snapshot |
| `explanation_snapshot` | `NVARCHAR(MAX)` | Yes |  | Explanation snapshot để reveal đúng historical content |
| `points_assigned` | `DECIMAL(9,4)` | No |  | Điểm cố định trong Attempt |
| `choice_shuffle_applied` | `BIT` | No | `0` | Có shuffle choices |
| `question_changed_after_start_at` | `DATETIME2(3)` | Yes |  | Mốc content correction gây full credit |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `attempt_id` | `assessment_attempts(id)` | `NO ACTION` |  |
| `source_question_id` | `questions(id)` | `NO ACTION` |  |
| `source_question_revision_id` | `question_revisions(id)` | `NO ACTION` |  |
| `section_id` | `assessment_sections(id)` | `SET NULL` |  |

### Unique Constraints

- `UNIQUE (attempt_id, position)`
- `UNIQUE (attempt_id, source_question_id)`

### Check Constraints

- `position > 0`
- `points_assigned > 0`
- `question_type_snapshot IN ('SINGLE_CHOICE','MULTIPLE_CHOICE','TRUE_FALSE','SHORT_ANSWER','ESSAY')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_attempt_questions_attempt` | `attempt_id, position` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_attempt_questions_source` | `source_question_id, attempt_id` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_attempt_questions_revision` | `source_question_revision_id, attempt_id` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Theo retention của Attempt; source QuestionRevision vẫn có marker was_student_exposed để giữ lịch sử ngay cả sau purge.

### Audit behavior

Snapshot itself là evidence; không update content/order.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Không chứa correct answer flag; explanation chỉ API reveal khi policy cho phép.

### Important invariants

- Snapshot order/content/points không đổi
- source revision marked was_student_exposed=1 trong same transaction

---

## `attempt_choice_snapshots`

**Purpose**

Snapshot lựa chọn đúng thứ tự Student thấy, không lưu is_correct.

**Lifecycle**

Insert cùng Attempt snapshot; immutable.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `attempt_question_id` | `BIGINT` | No |  | AttemptQuestion |
| `source_choice_id` | `BIGINT` | Yes |  | Choice revision source |
| `choice_key_snapshot` | `UNIQUEIDENTIFIER` | No |  | Key choice snapshot |
| `content_snapshot` | `NVARCHAR(MAX)` | No |  | Choice text |
| `position` | `INT` | No |  | Thứ tự Student thấy |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `attempt_question_id` | `attempt_questions(id)` | `NO ACTION` |  |
| `source_choice_id` | `question_revision_choices(id)` | `SET NULL` |  |

### Unique Constraints

- `UNIQUE (attempt_question_id, position)`
- `UNIQUE (attempt_question_id, choice_key_snapshot)`

### Check Constraints

- `position > 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_attempt_choice_question` | `attempt_question_id, position` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Theo Attempt retention.

### Audit behavior

Historical evidence; no mutation.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Không lưu correct flag để giảm nguy cơ leak.

### Important invariants

- Choice order không đổi khi resume

---

## `attempt_answers`

**Purpose**

Trạng thái answer hiện hành của từng AttemptQuestion; source of truth để resume nhanh.

**Lifecycle**

Upsert khi autosave; final state giữ đến purge.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `attempt_question_id` | `BIGINT` | No |  | Question |
| `answer_text` | `NVARCHAR(MAX)` | Yes |  | Short answer/essay hiện hành |
| `answer_version` | `BIGINT` | No | `0` | Server version tăng mỗi accepted save |
| `last_client_sequence` | `BIGINT` | No | `0` | Sequence client cuối được áp dụng |
| `last_change_id` | `UNIQUEIDENTIFIER` | Yes |  | Change UUID cuối để dedupe |
| `saved_at` | `DATETIME2(3)` | Yes |  | Server ACK time |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `attempt_question_id` | `attempt_questions(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (attempt_question_id)`

### Check Constraints

- `answer_version >= 0`
- `last_client_sequence >= 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_attempt_answers_saved` | `saved_at, attempt_question_id` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Purge theo Attempt retention.

### Audit behavior

Chi tiết save history ở attempt_answer_events; không AuditEvent từng lần.

### Concurrency

Conditional update theo row_version + client_sequence + lease validation.

### Security / PII classification

Student answer sensitive.

### Important invariants

- Old offline change có sequence <= current không được overwrite newer answer
- Server ACK trước deadline mới hợp lệ để grading

---

## `attempt_answer_choices`

**Purpose**

Lựa chọn hiện hành cho câu choice; junction AttemptAnswer ↔ AttemptChoiceSnapshot.

**Lifecycle**

Replace atomically cùng answer save.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `attempt_answer_id` | `BIGINT` | No |  | AttemptAnswer |
| `attempt_choice_snapshot_id` | `BIGINT` | No |  | Selected snapshot |

### Primary Key

`attempt_answer_id, attempt_choice_snapshot_id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `attempt_answer_id` | `attempt_answers(id)` | `NO ACTION` |  |
| `attempt_choice_snapshot_id` | `attempt_choice_snapshots(id)` | `NO ACTION` |  |

### Unique Constraints

_None._

### Check Constraints

_None._

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_attempt_answer_choices_choice` | `attempt_choice_snapshot_id, attempt_answer_id` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

CASCADE only when answer detail purge.

### Audit behavior

Event payload giữ historical selection changes trong retention.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Student answer sensitive.

### Important invariants

- Selected choice phải thuộc cùng AttemptQuestion (service/transaction check)

---

## `attempt_answer_events`

**Purpose**

Log chi tiết từng thay đổi answer đã gửi/được chấp nhận, phục vụ resume/debug và retention 30 ngày.

**Lifecycle**

Append; cleanup theo detailed retention/autosave policy.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `attempt_question_id` | `BIGINT` | No |  | Question |
| `change_id` | `UNIQUEIDENTIFIER` | No |  | Client idempotency UUID |
| `client_sequence` | `BIGINT` | No |  | Monotonic per question/client synced state |
| `server_answer_version` | `BIGINT` | Yes |  | Version nếu accepted |
| `payload_json` | `NVARCHAR(MAX)` | No |  | Snapshot selection/text của change; detail retention |
| `received_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Server receive |
| `accepted` | `BIT` | No | `0` | Có áp dụng vào current answer |
| `rejection_reason` | `VARCHAR(40)` | Yes |  | STALE/LEASE_INVALID/AFTER_DEADLINE/INVALID_PAYLOAD |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `attempt_question_id` | `attempt_questions(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (attempt_question_id, change_id)`

### Check Constraints

- `client_sequence >= 0`
- `payload_json IS NOT NULL AND ISJSON(payload_json)=1`
- `rejection_reason IS NULL OR rejection_reason IN ('STALE','LEASE_INVALID','AFTER_DEADLINE','INVALID_PAYLOAD')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_answer_events_question_time` | `attempt_question_id, received_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_answer_events_cleanup` | `received_at, accepted` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Có thể hard-delete sau retention; current final answer/result giữ theo policy.

### Audit behavior

Không thay AuditEvent; high-volume technical history.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Có thể chứa raw answer text, nên retention ngắn và quyền xem hạn chế.

### Important invariants

- Retry same change_id không double apply
- Rejected event không update current answer

---

## `attempt_question_grades`

**Purpose**

Điểm hiện hành của từng AttemptQuestion, gồm auto/manual/full-credit correction.

**Lifecycle**

PENDING → graded; regrade/manual revise update current row và append history.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `attempt_question_id` | `BIGINT` | No |  | PK/FK |
| `awarded_points` | `DECIMAL(9,4)` | No | `0` | Điểm hiện tại |
| `grading_status` | `VARCHAR(20)` | No |  | PENDING/AUTO_GRADED/MANUAL_GRADED/FULL_CREDIT |
| `grading_rule` | `VARCHAR(32)` | No |  | ORIGINAL/ANSWER_CORRECTION/CONTENT_FULL_CREDIT/MANUAL |
| `graded_against_revision_id` | `BIGINT` | Yes |  | Revision answer key dùng để grading |
| `graded_by_user_id` | `BIGINT` | Yes |  | Instructor cho manual |
| `graded_at` | `DATETIME2(3)` | Yes |  | UTC |
| `manual_reason` | `NVARCHAR(1000)` | Yes |  | Lý do chỉnh manual |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`attempt_question_id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `attempt_question_id` | `attempt_questions(id)` | `NO ACTION` |  |
| `graded_against_revision_id` | `question_revisions(id)` | `SET NULL` |  |
| `graded_by_user_id` | `users(id)` | `SET NULL` |  |

### Unique Constraints

_None._

### Check Constraints

- `awarded_points >= 0`
- `grading_status IN ('PENDING','AUTO_GRADED','MANUAL_GRADED','FULL_CREDIT')`
- `grading_rule IN ('ORIGINAL','ANSWER_CORRECTION','CONTENT_FULL_CREDIT','MANUAL')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_question_grades_pending` | `grading_status, graded_at` | No | `grading_status='PENDING'` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Theo Attempt retention.

### Audit behavior

Mọi post-result grade change append history; manual changes reason required.

### Concurrency

row_version; manual/regrade update conditional để không mất change.

### Security / PII classification

Sensitive grade data.

### Important invariants

- awarded_points <= attempt_questions.points_assigned (service/check via join)
- Essay pending đến Instructor grade

---

## `attempt_question_grade_history`

**Purpose**

Append-only lịch sử thay đổi điểm từng câu.

**Lifecycle**

Append-only.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `attempt_question_id` | `BIGINT` | No |  | Question |
| `old_points` | `DECIMAL(9,4)` | Yes |  | Điểm trước |
| `new_points` | `DECIMAL(9,4)` | No |  | Điểm sau |
| `reason_code` | `VARCHAR(32)` | No |  | INITIAL/AUTO_REGRADE/FULL_CREDIT/MANUAL_REVISION |
| `reason` | `NVARCHAR(1000)` | Yes |  | Lý do chi tiết |
| `actor_user_id` | `BIGINT` | Yes |  | Actor nếu human |
| `question_correction_id` | `BIGINT` | Yes |  | Correction nguồn; FK deferred |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `attempt_question_id` | `attempt_questions(id)` | `NO ACTION` |  |
| `actor_user_id` | `users(id)` | `SET NULL` |  |
| `question_correction_id` | `question_corrections(id)` | `SET NULL` | Deferred cross-domain FK created in `010_cross_domain_constraints.sql`. |

### Unique Constraints

_None._

### Check Constraints

- `new_points >= 0`
- `reason_code IN ('INITIAL','AUTO_REGRADE','FULL_CREDIT','MANUAL_REVISION')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_grade_history_question` | `attempt_question_id, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Theo Attempt detailed retention, trừ khi cần giữ score history lâu hơn; aggregate result history có thể giữ compact.

### Audit behavior

Domain-specific grade audit; AuditEvent thêm cho admin/instructor sensitive manual action.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Sensitive score history.

### Important invariants

- Không update/delete entries trong active retention

---

## `assessment_results`

**Purpose**

Kết quả hiện hành của một Attempt; final score pending nếu còn Essay chưa chấm.

**Lifecycle**

PENDING → FINAL → RELEASED (release có thể đồng thời final nếu immediate). Regrade update current score + history.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `attempt_id` | `BIGINT` | No |  | PK/FK |
| `raw_score` | `DECIMAL(12,4)` | No | `0` | Tổng điểm hiện hành |
| `max_score` | `DECIMAL(12,4)` | No |  | Tổng điểm tối đa snapshot |
| `percent_score` | `DECIMAL(7,4)` | Yes |  | 0..100 |
| `passed` | `BIT` | Yes |  | Đạt ngưỡng |
| `status` | `VARCHAR(20)` | No | `'PENDING'` | PENDING/FINAL/RELEASED |
| `released_at` | `DATETIME2(3)` | Yes |  | Student được xem |
| `graded_at` | `DATETIME2(3)` | Yes |  | Final grade time |
| `updated_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm cập nhật cuối (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`attempt_id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `attempt_id` | `assessment_attempts(id)` | `NO ACTION` |  |

### Unique Constraints

_None._

### Check Constraints

- `raw_score >= 0`
- `max_score > 0`
- `percent_score IS NULL OR (percent_score >= 0 AND percent_score <= 100)`
- `status IN ('PENDING','FINAL','RELEASED')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_results_status` | `status, released_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_results_percent` | `percent_score, attempt_id` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Theo Attempt retention; compact Course summary giữ nếu detail purge.

### Audit behavior

Mọi post-result score change append result history.

### Concurrency

row_version; recompute aggregate trong same transaction với grade change item.

### Security / PII classification

Student grade sensitive.

### Important invariants

- Không FINAL nếu còn required manual grading pending
- Release policy service-enforced

---

## `assessment_result_history`

**Purpose**

Append-only lịch sử điểm tổng cũ/mới để Student xem lý do thay đổi.

**Lifecycle**

Append-only.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `attempt_id` | `BIGINT` | No |  | Attempt |
| `old_score` | `DECIMAL(12,4)` | Yes |  | Trước |
| `new_score` | `DECIMAL(12,4)` | No |  | Sau |
| `old_percent` | `DECIMAL(7,4)` | Yes |  | Trước % |
| `new_percent` | `DECIMAL(7,4)` | Yes |  | Sau % |
| `reason_code` | `VARCHAR(32)` | No |  | INITIAL/REGRADE/MANUAL/CORRECTION |
| `reason` | `NVARCHAR(1000)` | No |  | Lý do hiển thị phù hợp |
| `actor_user_id` | `BIGINT` | Yes |  | Actor human nếu có |
| `regrade_job_id` | `BIGINT` | Yes |  | Job nguồn; FK deferred |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `attempt_id` | `assessment_attempts(id)` | `NO ACTION` |  |
| `actor_user_id` | `users(id)` | `SET NULL` |  |
| `regrade_job_id` | `regrade_jobs(id)` | `SET NULL` | Deferred cross-domain FK created in `010_cross_domain_constraints.sql`. |

### Unique Constraints

_None._

### Check Constraints

- `new_score >= 0`
- `reason_code IN ('INITIAL','REGRADE','MANUAL','CORRECTION')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_result_history_attempt` | `attempt_id, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Có thể purge cùng detailed Attempt theo final retention rule; compact summary giữ tổng cần thiết.

### Audit behavior

Student có thể xem reason; admin/instructor action đồng thời AuditEvent.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Sensitive score history.

### Important invariants

- Không rewrite old history

---

## `question_corrections`

**Purpose**

Business event khi Question đã dùng được chỉnh; phân biệt answer-only và content/choices để worker áp dụng policy đúng.

**Lifecycle**

PENDING → RUNNING → APPLIED/FAILED; correction mới có thể supersede older pending job theo service.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `question_id` | `BIGINT` | No |  | Question |
| `from_revision_id` | `BIGINT` | No |  | Revision cũ |
| `to_revision_id` | `BIGINT` | No |  | Revision mới |
| `correction_type` | `VARCHAR(24)` | No |  | ANSWER_ONLY/CONTENT_OR_CHOICES |
| `effective_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm Instructor Save |
| `reason` | `NVARCHAR(1000)` | No |  | Lý do bắt buộc |
| `actor_user_id` | `BIGINT` | No |  | Instructor/Admin |
| `status` | `VARCHAR(20)` | No | `'PENDING'` | PENDING/RUNNING/APPLIED/FAILED/SUPERSEDED |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `question_id` | `questions(id)` | `NO ACTION` |  |
| `from_revision_id` | `question_revisions(id)` | `NO ACTION` |  |
| `to_revision_id` | `question_revisions(id)` | `NO ACTION` |  |
| `actor_user_id` | `users(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (to_revision_id)`

### Check Constraints

- `correction_type IN ('ANSWER_ONLY','CONTENT_OR_CHOICES')`
- `status IN ('PENDING','RUNNING','APPLIED','FAILED','SUPERSEDED')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_question_corrections_question_time` | `question_id, effective_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_question_corrections_status` | `status, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Giữ lâu dài cùng revision history.

### Audit behavior

Reason/actor/time bắt buộc; AuditEvent.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Instructor/Admin only.

### Important invariants

- ANSWER_ONLY không đổi content/choices
- CONTENT_OR_CHOICES full-credit cho eligible attempts started trước effective_at
- Historical snapshot không rewrite

---

## `regrade_jobs`

**Purpose**

Job chấm lại lớn, resumable/idempotent cho một correction.

**Lifecycle**

QUEUED → RUNNING/PARTIAL → COMPLETED; retry từ PARTIAL/FAILED.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `question_correction_id` | `BIGINT` | No |  | Correction |
| `background_job_id` | `BIGINT` | Yes |  | Optional link tới generic job; nullable để domain history sống lâu hơn operational job |
| `status` | `VARCHAR(20)` | No | `'QUEUED'` | QUEUED/RUNNING/PARTIAL/COMPLETED/FAILED/CANCELLED |
| `total_items` | `INT` | No | `0` | Số attempts mục tiêu |
| `processed_items` | `INT` | No | `0` | Đã xử lý |
| `changed_results` | `INT` | No | `0` | Số result đổi |
| `started_at` | `DATETIME2(3)` | Yes |  | UTC |
| `completed_at` | `DATETIME2(3)` | Yes |  | UTC |
| `last_error` | `NVARCHAR(2000)` | Yes |  | Lỗi cuối |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `question_correction_id` | `question_corrections(id)` | `NO ACTION` |  |
| `background_job_id` | `background_jobs(id)` | `SET NULL` | Deferred cross-domain FK created in `010_cross_domain_constraints.sql`. |

### Unique Constraints

- `UNIQUE (question_correction_id)`

### Check Constraints

- `status IN ('QUEUED','RUNNING','PARTIAL','COMPLETED','FAILED','CANCELLED')`
- `total_items >= 0`
- `processed_items >= 0`
- `changed_results >= 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_regrade_jobs_status` | `status, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Giữ cùng correction trong historical retention; có thể archive.

### Audit behavior

Job lifecycle operational; correction actor audited.

### Concurrency

row_version; worker claim bằng conditional update.

### Security / PII classification

Không expose arbitrary Student details ngoài authorized admin/instructor views.

### Important invariants

- Một correction tối đa một logical regrade job
- Eligible attempts exclude enrollment periods detail_purged_at != NULL

---

## `regrade_items`

**Purpose**

Per-attempt progress/idempotency cho regrade job.

**Lifecycle**

PENDING → PROCESSING → COMPLETED/SKIPPED/FAILED; retry FAILED/expired PROCESSING.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `regrade_job_id` | `BIGINT` | No |  | Job |
| `attempt_id` | `BIGINT` | No |  | Attempt |
| `status` | `VARCHAR(16)` | No | `'PENDING'` | PENDING/PROCESSING/COMPLETED/SKIPPED/FAILED |
| `old_score` | `DECIMAL(12,4)` | Yes |  | Score trước |
| `new_score` | `DECIMAL(12,4)` | Yes |  | Score sau |
| `skip_reason` | `VARCHAR(40)` | Yes |  | DETAIL_PURGED/NOT_AFFECTED/CANCELLED |
| `attempt_count` | `INT` | No | `0` | Retry count |
| `processed_at` | `DATETIME2(3)` | Yes |  | UTC |
| `last_error` | `NVARCHAR(2000)` | Yes |  | Lỗi |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `regrade_job_id` | `regrade_jobs(id)` | `NO ACTION` |  |
| `attempt_id` | `assessment_attempts(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (regrade_job_id, attempt_id)`

### Check Constraints

- `status IN ('PENDING','PROCESSING','COMPLETED','SKIPPED','FAILED')`
- `skip_reason IS NULL OR skip_reason IN ('DETAIL_PURGED','NOT_AFFECTED','CANCELLED')`
- `attempt_count >= 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_regrade_items_claim` | `regrade_job_id, status, id` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_regrade_items_attempt` | `attempt_id, regrade_job_id` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Theo regrade job retention; không là source of truth của final grade.

### Audit behavior

Operational; score history tables là business history.

### Concurrency

row_version/claim token prevents double processing.

### Security / PII classification

Sensitive because links Student attempt; limited access.

### Important invariants

- Unique job+attempt makes regrade idempotent
- Worker writes score/history atomically per item

---
