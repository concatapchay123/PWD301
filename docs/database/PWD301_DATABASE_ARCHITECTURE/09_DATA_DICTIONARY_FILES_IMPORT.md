# 09 DATA DICTIONARY FILES IMPORT

Database engine: **Microsoft SQL Server**. Timestamps are UTC `DATETIME2(3)` unless noted.

## `file_blobs`

**Purpose**

Đại diện file vật lý deduplicated theo SHA-256; nhiều logical assets/revisions có thể dùng chung.

**Lifecycle**

PRESENT → DELETING → DELETED khi refcount 0 + recovery expired + history permits.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `sha256` | `BINARY(32)` | No |  | SHA-256 content |
| `size_bytes` | `BIGINT` | No |  | Dung lượng vật lý |
| `detected_mime_type` | `NVARCHAR(150)` | No |  | MIME server detect |
| `storage_key` | `NVARCHAR(500)` | No |  | Key/path private trong storage |
| `status` | `VARCHAR(20)` | No | `'PRESENT'` | PRESENT/DELETING/DELETED |
| `reference_count` | `INT` | No | `0` | Cache số FileRevision đang reference |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `deleted_at` | `DATETIME2(3)` | Yes |  | Physical delete time |

### Primary Key

`id`

### Foreign Keys

_None._

### Unique Constraints

- `UNIQUE (sha256)`
- `UNIQUE (storage_key)`

### Check Constraints

- `size_bytes > 0`
- `status IN ('PRESENT','DELETING','DELETED')`
- `reference_count >= 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_file_blobs_status_ref` | `status, reference_count, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Physical bytes xóa; minimal metadata row có thể giữ nếu historically important.

### Audit behavior

Physical cleanup operational; suspicious hash/malware event security log.

### Concurrency

Dedup insert dùng unique sha256 + retry; reference_count cập nhật transactionally hoặc recompute.

### Security / PII classification

storage_key không public; không dựa vào key để authorize.

### Important invariants

- Không xóa physical blob khi còn FileRevision reference active/recovery
- Same sha256 dùng chung blob

---

## `file_assets`

**Purpose**

Logical file identity trong LMS; lifecycle độc lập với blob vật lý, hỗ trợ replacement/recovery.

**Lifecycle**

PENDING asset → activate security-cleared revision → ACTIVE; replace giữ same asset/current_revision thay; trash/recovery.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `public_id` | `UNIQUEIDENTIFIER` | No | `NEWSEQUENTIALID()` | ID công khai dùng trong URL/API; không thay thế kiểm tra quyền |
| `course_id` | `BIGINT` | No |  | Course boundary |
| `created_by_user_id` | `BIGINT` | No |  | Uploader |
| `asset_type` | `VARCHAR(24)` | No |  | RESOURCE/QUESTION_IMAGE/COURSE_IMAGE/IMPORT_SOURCE/EXPORT/OTHER |
| `display_name` | `NVARCHAR(255)` | No |  | Tên hiển thị |
| `status` | `VARCHAR(20)` | No | `'PENDING'` | PENDING/ACTIVE/REPLACED/TRASH/HISTORICAL |
| `retention_until` | `DATETIME2(3)` | Yes |  | Mốc cleanup logical asset |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `updated_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm cập nhật cuối (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |
| `deleted_at` | `DATETIME2(3)` | Yes |  | Thời điểm đưa vào thùng rác |
| `restore_until` | `DATETIME2(3)` | Yes |  | Hạn khôi phục trước khi cleanup/historical transition |
| `deleted_by_user_id` | `BIGINT` | Yes |  | Người thực hiện xóa |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `course_id` | `courses(id)` | `NO ACTION` |  |
| `created_by_user_id` | `users(id)` | `NO ACTION` |  |
| `deleted_by_user_id` | `users(id)` | `SET NULL` |  |

### Unique Constraints

- `UNIQUE (public_id)`

### Check Constraints

- `asset_type IN ('RESOURCE','QUESTION_IMAGE','COURSE_IMAGE','IMPORT_SOURCE','EXPORT','OTHER')`
- `status IN ('PENDING','ACTIVE','REPLACED','TRASH','HISTORICAL')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_file_assets_course_status` | `course_id, status, asset_type` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Logical ref remove không xóa blob nếu asset khác dùng. Historical metadata giữ khi cần.

### Audit behavior

Replace/delete/admin restore audit khi important.

### Concurrency

row_version; replacement activation compare expected current_revision.

### Security / PII classification

Authorization theo Course + logical references; direct storage path không public.

### Important invariants

- `is_current = 1` chỉ áp dụng cho revision cùng asset có status `ACTIVE` (qua filtered unique index `uq_file_revisions_current`)
- Quota tính logical usage theo policy, physical dedup không thay authorization

---

## `file_revisions`

**Purpose**

Một lần upload/replacement của FileAsset; luôn quarantine trước khi active.

**Lifecycle**

QUARANTINED → VALIDATING → SCANNING → SAFE → ACTIVE; fail → REJECTED. Replacement: old ACTIVE → RECOVERY/REPLACED → DELETED.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `file_asset_id` | `BIGINT` | No |  | Asset |
| `revision_no` | `INT` | No |  | Tăng tuần tự |
| `is_current` | `BIT` | No | `0` | Cờ đánh dấu revision active/current (kết hợp filtered unique index) |
| `blob_id` | `BIGINT` | Yes |  | Physical blob sau validation/dedup |
| `original_filename` | `NVARCHAR(255)` | No |  | Tên file người dùng gửi |
| `declared_mime_type` | `NVARCHAR(150)` | Yes |  | Client MIME |
| `detected_mime_type` | `NVARCHAR(150)` | Yes |  | Server detect |
| `size_bytes` | `BIGINT` | No |  | Upload size |
| `status` | `VARCHAR(24)` | No | `'QUARANTINED'` | QUARANTINED/VALIDATING/SCANNING/SAFE/ACTIVE/REJECTED/REPLACED/RECOVERY/DELETED |
| `uploaded_by_user_id` | `BIGINT` | No |  | Uploader |
| `quarantine_key` | `NVARCHAR(500)` | Yes |  | Vị trí private tạm |
| `security_checks_completed_at` | `DATETIME2(3)` | Yes |  | UTC |
| `activated_at` | `DATETIME2(3)` | Yes |  | UTC |
| `replaced_at` | `DATETIME2(3)` | Yes |  | UTC |
| `recovery_until` | `DATETIME2(3)` | Yes |  | Giữ bản cũ ~30 ngày |
| `rejection_reason` | `NVARCHAR(1000)` | Yes |  | Lý do reject |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `file_asset_id` | `file_assets(id)` | `NO ACTION` |  |
| `blob_id` | `file_blobs(id)` | `SET NULL` |  |
| `uploaded_by_user_id` | `users(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (file_asset_id, revision_no)`

### Check Constraints

- `revision_no > 0`
- `size_bytes > 0`
- `status IN ('QUARANTINED','VALIDATING','SCANNING','SAFE','ACTIVE','REJECTED','REPLACED','RECOVERY','DELETED')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ux_file_revisions_active` | `file_asset_id` | Yes | `status = 'ACTIVE'` | DB-enforce tối đa một revision ACTIVE cho mỗi logical file asset. |
| `uq_file_revisions_current` | `file_asset_id` | Yes | `is_current = 1` | Đảm bảo duy nhất 1 revision active tại một thời điểm. |
| `ix_file_revisions_asset` | `file_asset_id, revision_no` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_file_revisions_processing` | `status, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_file_revisions_recovery` | `recovery_until, status` | No | `recovery_until IS NOT NULL` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Quarantine rejected cleaned quickly; old safe revision kept recovery then blob ref removed.

### Audit behavior

Replacement/reject/malware significant events audit/security event.

### Concurrency

row_version; filtered unique index chỉ cho tối đa một ACTIVE revision/asset; service transaction đổi current pointer atomically.

### Security / PII classification

Untrusted until all checks pass; macro-enabled Office rejected; parser resource limits.

### Important invariants

- Scan unavailable/fail không được ACTIVE
- Video <1GB; image~10MB PDF/DOCX~50MB PPTX~100MB enforced service before processing

---

## `file_scan_results`

**Purpose**

Kết quả từng bước validation/malware/parser security cho FileRevision.

**Lifecycle**

Append result per scan attempt; latest/required PASS set controls activation.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `file_revision_id` | `BIGINT` | No |  | Revision |
| `scan_type` | `VARCHAR(24)` | No |  | FILE_VALIDATION/MALWARE/STRUCTURE/RESOURCE_LIMIT/CONTENT_SECURITY |
| `engine` | `NVARCHAR(100)` | No |  | ClamAV/parser/... |
| `engine_version` | `NVARCHAR(100)` | Yes |  | Version/signature |
| `status` | `VARCHAR(16)` | No |  | PASS/FAIL/ERROR |
| `details_json` | `NVARCHAR(MAX)` | Yes |  | Diagnostics sanitized |
| `started_at` | `DATETIME2(3)` | Yes |  | UTC |
| `completed_at` | `DATETIME2(3)` | Yes |  | UTC |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `file_revision_id` | `file_revisions(id)` | `NO ACTION` |  |

### Unique Constraints

_None._

### Check Constraints

- `scan_type IN ('FILE_VALIDATION','MALWARE','STRUCTURE','RESOURCE_LIMIT','CONTENT_SECURITY')`
- `status IN ('PASS','FAIL','ERROR')`
- `details_json IS NULL OR ISJSON(details_json)=1`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_file_scan_revision_type` | `file_revision_id, scan_type, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_file_scan_failures` | `status, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Giữ đủ cho file security audit; old low-value detail có thể archive.

### Audit behavior

Malware/high-risk result tạo security_event.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Không lưu raw malicious content.

### Important invariants

- Required scan ERROR được coi fail-closed, không safe

---

## `lesson_resources`

**Purpose**

Liên kết Lesson với logical FileAsset; quyền truy cập đi qua Lesson/Course.

**Lifecycle**

Active while Lesson references asset.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `lesson_id` | `BIGINT` | No |  | Lesson |
| `file_asset_id` | `BIGINT` | No |  | Asset |
| `position` | `INT` | No | `1` | Thứ tự |
| `label` | `NVARCHAR(255)` | Yes |  | Nhãn |
| `is_required` | `BIT` | No | `0` | Resource bắt buộc |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `lesson_id` | `lessons(id)` | `NO ACTION` |  |
| `file_asset_id` | `file_assets(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (lesson_id, file_asset_id)`
- `UNIQUE (lesson_id, position)`

### Check Constraints

- `position > 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_lesson_resources_lesson` | `lesson_id, position` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Remove link only; asset/blob cleanup separate.

### Audit behavior

Resource replace/remove significant edit audit.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Download service verifies enrollment/lesson authorization + asset safe status.

### Important invariants

- file_asset.course_id phải cùng lesson.course_id (service)

---

## `question_revision_resources`

**Purpose**

Ảnh/tệp đính kèm QuestionRevision, đặc biệt image extracted từ DOCX.

**Lifecycle**

Theo revision retention.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `question_revision_id` | `BIGINT` | No |  | Revision |
| `file_asset_id` | `BIGINT` | No |  | Asset |
| `position` | `INT` | No | `1` | Thứ tự |
| `resource_role` | `VARCHAR(20)` | No | `'IMAGE'` | IMAGE/ATTACHMENT |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `question_revision_id` | `question_revisions(id)` | `NO ACTION` |  |
| `file_asset_id` | `file_assets(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (question_revision_id, file_asset_id)`

### Check Constraints

- `position > 0`
- `resource_role IN ('IMAGE','ATTACHMENT')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_question_resources_revision` | `question_revision_id, position` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Link giữ nếu revision historical; blob dedup cleanup độc lập.

### Audit behavior

Import provenance handles source.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Student chỉ access asset khi attempt/course authorizes.

### Important invariants

- Asset phải safe/active trước Question draft được approve/publish

---

## `document_import_jobs`

**Purpose**

Import DOCX/PDF → draft Assessment với confidence/review; không auto publish.

**Lifecycle**

QUEUED → PROCESSING → REVIEW_REQUIRED/COMPLETED; fail safe. Instructor review required before publish.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `public_id` | `UNIQUEIDENTIFIER` | No | `NEWSEQUENTIALID()` | ID công khai dùng trong URL/API; không thay thế kiểm tra quyền |
| `course_id` | `BIGINT` | No |  | Course |
| `source_file_asset_id` | `BIGINT` | No |  | DOCX/PDF source |
| `requested_by_user_id` | `BIGINT` | No |  | Instructor |
| `draft_assessment_id` | `BIGINT` | Yes |  | Assessment draft tạo ra |
| `background_job_id` | `BIGINT` | Yes |  | Optional link tới generic job; nullable để import history không phụ thuộc retention của operational queue |
| `document_type` | `VARCHAR(8)` | No |  | DOCX/PDF |
| `status` | `VARCHAR(24)` | No | `'QUEUED'` | QUEUED/PROCESSING/REVIEW_REQUIRED/COMPLETED/FAILED/CANCELLED |
| `parser_version` | `NVARCHAR(100)` | No |  | Parser version |
| `question_count` | `INT` | No | `0` | Detected |
| `review_required_count` | `INT` | No | `0` | Ambiguous |
| `started_at` | `DATETIME2(3)` | Yes |  | UTC |
| `completed_at` | `DATETIME2(3)` | Yes |  | UTC |
| `last_error` | `NVARCHAR(2000)` | Yes |  | Lỗi |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `course_id` | `courses(id)` | `NO ACTION` |  |
| `source_file_asset_id` | `file_assets(id)` | `NO ACTION` |  |
| `requested_by_user_id` | `users(id)` | `NO ACTION` |  |
| `draft_assessment_id` | `assessments(id)` | `SET NULL` |  |
| `background_job_id` | `background_jobs(id)` | `SET NULL` | Deferred cross-domain FK created in `010_cross_domain_constraints.sql`. |

### Unique Constraints

- `UNIQUE (public_id)`

### Check Constraints

- `document_type IN ('DOCX','PDF')`
- `status IN ('QUEUED','PROCESSING','REVIEW_REQUIRED','COMPLETED','FAILED','CANCELLED')`
- `question_count >= 0`
- `review_required_count >= 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_import_jobs_course_status` | `course_id, status, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_import_jobs_status` | `status, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Import diagnostics có thể cleanup sau accepted content stabilized; provenance on Question remains.

### Audit behavior

Approve imported content provenance; import execution operational.

### Concurrency

row_version; worker claim via generic job.

### Security / PII classification

Source file phải SAFE trước parse; parser timeout/resource limits.

### Important invariants

- Scanned PDF OCR không MVP
- Import chỉ tạo draft
- Broken image flags related question review

---

## `import_questions`

**Purpose**

Intermediate parsed question record, chưa là Question Bank cho tới Instructor approve.

**Lifecycle**

Parsed → review → ACCEPTED/REJECTED/EDITED. ACCEPTED creates Question/Revision/Provenance.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `import_job_id` | `BIGINT` | No |  | Job |
| `ordinal` | `INT` | No |  | Vị trí trong doc |
| `detected_type` | `VARCHAR(24)` | Yes |  | Type |
| `content_text` | `NVARCHAR(MAX)` | No |  | Parsed content |
| `choices_json` | `NVARCHAR(MAX)` | Yes |  | Choices draft |
| `detected_answer_json` | `NVARCHAR(MAX)` | Yes |  | Answer from document |
| `explanation_text` | `NVARCHAR(MAX)` | Yes |  | Explanation |
| `confidence_score` | `DECIMAL(5,4)` | No |  | 0..1 |
| `diagnostics_json` | `NVARCHAR(MAX)` | Yes |  | Parser diagnostics |
| `review_state` | `VARCHAR(20)` | No | `'READY'` | READY/NEEDS_REVIEW/INVALID/ACCEPTED/REJECTED/EDITED |
| `has_broken_resource` | `BIT` | No | `0` | Image/resource lỗi |
| `ai_suggested_answer_json` | `NVARCHAR(MAX)` | Yes |  | Optional AI suggestion; không official |
| `ai_suggestion_model` | `NVARCHAR(100)` | Yes |  | Model |
| `ai_suggestion_confirmed_at` | `DATETIME2(3)` | Yes |  | Instructor accept suggestion |
| `ai_suggestion_confirmed_by` | `BIGINT` | Yes |  | Instructor |
| `approved_question_id` | `BIGINT` | Yes |  | Question tạo sau review |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `updated_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm cập nhật cuối (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `import_job_id` | `document_import_jobs(id)` | `NO ACTION` |  |
| `ai_suggestion_confirmed_by` | `users(id)` | `SET NULL` |  |
| `approved_question_id` | `questions(id)` | `SET NULL` |  |

### Unique Constraints

- `UNIQUE (import_job_id, ordinal)`

### Check Constraints

- `ordinal > 0`
- `confidence_score >= 0 AND confidence_score <= 1`
- `review_state IN ('READY','NEEDS_REVIEW','INVALID','ACCEPTED','REJECTED','EDITED')`
- `choices_json IS NULL OR ISJSON(choices_json)=1`
- `detected_answer_json IS NULL OR ISJSON(detected_answer_json)=1`
- `diagnostics_json IS NULL OR ISJSON(diagnostics_json)=1`
- `ai_suggested_answer_json IS NULL OR ISJSON(ai_suggested_answer_json)=1`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_import_questions_review` | `import_job_id, review_state, ordinal` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Có thể cleanup sau provenance retained and recovery window.

### Audit behavior

AI suggestion confirmation and approval trace via provenance/AuditEvent.

### Concurrency

row_version để tránh concurrent review overwrite.

### Security / PII classification

AI suggestion never official until explicit confirm; content untrusted until sanitized/validated.

### Important invariants

- No answer key => official answer remains unknown until Instructor input/confirmation
- Broken resource cannot READY publish

---

## `import_duplicate_candidates`

**Purpose**

Cảnh báo duplicate/near-duplicate trong import hoặc Question Bank; không auto merge.

**Lifecycle**

PENDING → decision. Advisory only.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `import_question_id` | `BIGINT` | No |  | Parsed question |
| `candidate_import_question_id` | `BIGINT` | Yes |  | Duplicate trong cùng import |
| `candidate_question_id` | `BIGINT` | Yes |  | Question Bank candidate |
| `similarity_score` | `DECIMAL(5,4)` | No |  | 0..1 |
| `decision` | `VARCHAR(16)` | No | `'PENDING'` | PENDING/KEEP/IGNORE/REJECT |
| `decided_by_user_id` | `BIGINT` | Yes |  | Instructor |
| `decided_at` | `DATETIME2(3)` | Yes |  | UTC |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `import_question_id` | `import_questions(id)` | `NO ACTION` |  |
| `candidate_import_question_id` | `import_questions(id)` | `SET NULL` |  |
| `candidate_question_id` | `questions(id)` | `SET NULL` |  |
| `decided_by_user_id` | `users(id)` | `SET NULL` |  |

### Unique Constraints

_None._

### Check Constraints

- `similarity_score >= 0 AND similarity_score <= 1`
- `decision IN ('PENDING','KEEP','IGNORE','REJECT')`
- `(candidate_import_question_id IS NOT NULL OR candidate_question_id IS NOT NULL)`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_import_duplicates_question` | `import_question_id, decision` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Cleanup với import diagnostics.

### Audit behavior

Không cần full AuditEvent trừ admin override; decision trace trong row.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

No sensitive data beyond question linkage.

### Important invariants

- Không tự merge

---

## `import_question_resources`

**Purpose**

Ảnh extracted gắn với parsed question trước approval.

**Lifecycle**

Extracted → scan → READY/BROKEN. Khi approve tạo question_revision_resources.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `import_question_id` | `BIGINT` | No |  | Parsed question |
| `file_asset_id` | `BIGINT` | No |  | Extracted image asset |
| `position` | `INT` | No | `1` | Thứ tự |
| `status` | `VARCHAR(16)` | No | `'READY'` | READY/BROKEN/REJECTED |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `import_question_id` | `import_questions(id)` | `NO ACTION` |  |
| `file_asset_id` | `file_assets(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (import_question_id, file_asset_id)`

### Check Constraints

- `position > 0`
- `status IN ('READY','BROKEN','REJECTED')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_import_question_resources` | `import_question_id, position` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Cleanup sau promotion/rejection nếu không còn logical ref.

### Audit behavior

Security scan separate.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Asset phải safe trước READY.

### Important invariants

- BROKEN forces import_question NEEDS_REVIEW

---
