# 05 DATA DICTIONARY COURSE

Database engine: **Microsoft SQL Server**. Timestamps are UTC `DATETIME2(3)` unless noted.

## `courses`

**Purpose**

Course chính; có thể tạm không có Instructor owner; code và title đều unique.

**Lifecycle**

DRAFT → SUBMITTED_FOR_REVIEW → APPROVED → PUBLISHED; có thể ARCHIVED hoặc TRASH. Material change trên bản published đi qua course_change_requests.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `public_id` | `UNIQUEIDENTIFIER` | No | `NEWSEQUENTIALID()` | ID công khai dùng trong URL/API; không thay thế kiểm tra quyền |
| `course_code` | `NVARCHAR(50)` | No |  | Mã Course |
| `course_code_normalized` | `NVARCHAR(50)` | No | `UPPER(LTRIM(RTRIM([course_code]))) PERSISTED` | Mã chuẩn hóa |
| `title` | `NVARCHAR(200)` | No |  | Tên Course |
| `title_normalized` | `NVARCHAR(200)` | No | `LOWER(LTRIM(RTRIM([title]))) PERSISTED` | Tên chuẩn hóa |
| `description` | `NVARCHAR(MAX)` | Yes |  | Mô tả |
| `category` | `NVARCHAR(100)` | Yes |  | Danh mục |
| `difficulty` | `VARCHAR(20)` | Yes |  | BEGINNER/INTERMEDIATE/ADVANCED |
| `owner_instructor_id` | `BIGINT` | Yes |  | Instructor hiện quản lý; có thể NULL tạm thời |
| `thumbnail_file_asset_id` | `BIGINT` | Yes |  | Ảnh Course; FK thêm sau khi file_assets tồn tại |
| `status` | `VARCHAR(32)` | No | `'DRAFT'` | DRAFT/SUBMITTED_FOR_REVIEW/APPROVED/PUBLISHED/ARCHIVED/TRASH |
| `capacity` | `INT` | Yes |  | Số Student tối đa; NULL = không giới hạn |
| `storage_quota_bytes` | `BIGINT` | Yes |  | Quota override per Course; NULL dùng mặc định |
| `published_at` | `DATETIME2(3)` | Yes |  | Lần publish hiện hành/đầu tiên tùy service |
| `approved_at` | `DATETIME2(3)` | Yes |  | Lần approve gần nhất |
| `approved_by_user_id` | `BIGINT` | Yes |  | Admin approve |
| `first_student_enrolled_at` | `DATETIME2(3)` | Yes |  | Marker lịch sử giúp delete policy |
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
| `owner_instructor_id` | `users(id)` | `NO ACTION` | User records with history are deactivated/anonymized rather than hard-deleted; reassignment/nulling is service-managed. |
| `approved_by_user_id` | `users(id)` | `NO ACTION` | Preserve approval actor history; anonymize User in place. |
| `deleted_by_user_id` | `users(id)` | `NO ACTION` | Preserve deletion actor history; anonymize User in place. |
| `thumbnail_file_asset_id` | `file_assets(id)` | `SET NULL` | Deferred cross-domain FK created in `010_cross_domain_constraints.sql`. |

### Unique Constraints

- `UNIQUE (public_id)`
- `UNIQUE (course_code_normalized)`
- `UNIQUE (title_normalized)`

### Check Constraints

- `status IN ('DRAFT','SUBMITTED_FOR_REVIEW','APPROVED','PUBLISHED','ARCHIVED','TRASH')`
- `difficulty IS NULL OR difficulty IN ('BEGINNER','INTERMEDIATE','ADVANCED')`
- `capacity IS NULL OR capacity > 0`
- `storage_quota_bytes IS NULL OR storage_quota_bytes > 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_courses_catalog` | `status, category, difficulty, title` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_courses_owner` | `owner_instructor_id, status` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Course chưa có lịch sử có thể hard-delete sau recovery. Course đã có Student: TRASH/ARCHIVED historical, không cascade attempts/progress.

### Audit behavior

Publish/approve/archive/delete/reassign/material admin edit phải audit.

### Concurrency

row_version; reorder/structural operations dùng transaction.

### Security / PII classification

Authorization boundary theo owner_instructor_id + Admin override có reason/audit.

### Important invariants

- Course code unique
- Course title unique
- owner nếu có phải đang có role INSTRUCTOR (service-enforced)
- Course làm prerequisite cho active course khác không được archive/delete

---

## `course_prerequisites`

**Purpose**

Quan hệ N-N Course yêu cầu Course khác hoàn thành trước.

**Lifecycle**

Thêm/xóa khi Course chưa bị dependency lock.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `course_id` | `BIGINT` | No |  | Course đích |
| `prerequisite_course_id` | `BIGINT` | No |  | Course bắt buộc hoàn thành |
| `created_by_user_id` | `BIGINT` | No |  | Người tạo |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`course_id, prerequisite_course_id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `course_id` | `courses(id)` | `NO ACTION` |  |
| `prerequisite_course_id` | `courses(id)` | `NO ACTION` |  |
| `created_by_user_id` | `users(id)` | `NO ACTION` | Column is required; historical actor is preserved through User anonymization. |

### Unique Constraints

_None._

### Check Constraints

- `course_id <> prerequisite_course_id`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_course_prereq_reverse` | `prerequisite_course_id, course_id` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

NO ACTION; hard delete Course bị chặn nếu còn dependency.

### Audit behavior

Thay đổi prerequisite là material change và audit/reapproval.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Instructor owner/Admin.

### Important invariants

- Không self-reference
- Không cycle; cycle detection service trong transaction
- Không archive/delete prerequisite đang phục vụ active Course

---

## `course_completion_rules`

**Purpose**

Cấu hình điều kiện hoàn thành Course theo mô hình đơn giản, không EAV.

**Lifecycle**

Một row per Course; material change cần approval trên Course published.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `course_id` | `BIGINT` | No |  | PK/FK Course |
| `require_all_required_lessons` | `BIT` | No | `1` | Phải hoàn thành tất cả Lesson bắt buộc |
| `require_required_assessments` | `BIT` | No | `1` | Phải đạt các Assessment đánh dấu required |
| `minimum_progress_percent` | `DECIMAL(5,2)` | Yes |  | Ngưỡng progress nếu cần |
| `updated_by_user_id` | `BIGINT` | Yes |  | Người chỉnh |
| `updated_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm cập nhật cuối (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`course_id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `course_id` | `courses(id)` | `NO ACTION` |  |
| `updated_by_user_id` | `users(id)` | `SET NULL` |  |

### Unique Constraints

_None._

### Check Constraints

- `minimum_progress_percent IS NULL OR (minimum_progress_percent >= 0 AND minimum_progress_percent <= 100)`

### Indexes

_None._

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

CASCADE chỉ khi Course chưa có lịch sử và hard-delete hợp lệ; lịch sử completion summary độc lập.

### Audit behavior

Mọi material rule change audit.

### Concurrency

row_version.

### Security / PII classification

Instructor owner/Admin.

### Important invariants

- Completed status trước đây không bị đảo ngược khi rule nghiêm hơn; summary là historical proof

---

## `course_change_requests`

**Purpose**

Staging tối thiểu cho thay đổi material của Course đã published để Admin duyệt trước khi áp dụng.

**Lifecycle**

PENDING → APPROVED/REJECTED/CANCELLED; APPROVED → APPLIED trong transaction.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `course_id` | `BIGINT` | No |  | Course |
| `requested_by_user_id` | `BIGINT` | No |  | Instructor/Admin tạo |
| `change_type` | `VARCHAR(32)` | No |  | COURSE_METADATA/LESSON_STRUCTURE/LESSON_CONTENT/COMPLETION_RULE/PREREQUISITE/OTHER |
| `target_type` | `VARCHAR(32)` | No |  | COURSE/LESSON/RULE/PREREQUISITE |
| `target_id` | `BIGINT` | Yes |  | ID target nếu có |
| `proposed_payload_json` | `NVARCHAR(MAX)` | No |  | Patch/proposed data; chỉ dùng staging, source of truth vẫn ở bảng chuẩn hóa |
| `status` | `VARCHAR(20)` | No | `'PENDING'` | PENDING/APPROVED/REJECTED/CANCELLED/APPLIED |
| `reviewed_by_user_id` | `BIGINT` | Yes |  | Admin |
| `review_reason` | `NVARCHAR(1000)` | Yes |  | Lý do |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `reviewed_at` | `DATETIME2(3)` | Yes |  | UTC |
| `applied_at` | `DATETIME2(3)` | Yes |  | UTC |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `course_id` | `courses(id)` | `NO ACTION` |  |
| `requested_by_user_id` | `users(id)` | `NO ACTION` |  |
| `reviewed_by_user_id` | `users(id)` | `SET NULL` |  |

### Unique Constraints

_None._

### Check Constraints

- `change_type IN ('COURSE_METADATA','LESSON_STRUCTURE','LESSON_CONTENT','COMPLETION_RULE','PREREQUISITE','OTHER')`
- `target_type IN ('COURSE','LESSON','RULE','PREREQUISITE')`
- `status IN ('PENDING','APPROVED','REJECTED','CANCELLED','APPLIED')`
- `ISJSON(proposed_payload_json)=1`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_course_changes_pending` | `status, created_at` | No | `status='PENDING'` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_course_changes_course` | `course_id, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Giữ tối thiểu trong audit retention; không dùng làm historical content snapshot dài hạn.

### Audit behavior

Review/apply bắt buộc audit.

### Concurrency

row_version + conditional transition.

### Security / PII classification

Payload có thể chứa nội dung học liệu; chỉ owner/Admin.

### Important invariants

- Không áp dụng material change vào published data trước APPROVED
- Minor edit không cần row này nhưng vẫn audit khi quan trọng

---

## `lessons`

**Purpose**

Lesson thuộc Course, có thứ tự, nội dung Markdown và ngưỡng hoàn thành tự động.

**Lifecycle**

DRAFT → PUBLISHED; có thể HIDDEN/TRASH; Lesson có học sử sau recovery trở thành HISTORICAL thay vì hard delete.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `public_id` | `UNIQUEIDENTIFIER` | No | `NEWSEQUENTIALID()` | ID công khai dùng trong URL/API; không thay thế kiểm tra quyền |
| `course_id` | `BIGINT` | No |  | Course |
| `title` | `NVARCHAR(200)` | No |  | Tên Lesson |
| `summary` | `NVARCHAR(1000)` | Yes |  | Tóm tắt |
| `markdown_content` | `NVARCHAR(MAX)` | No |  | Markdown source; render phải sanitize |
| `position` | `INT` | No |  | Thứ tự trong Course |
| `estimated_duration_minutes` | `INT` | Yes |  | Ước lượng |
| `minimum_completion_seconds` | `INT` | No | `30` | Thời gian tối thiểu để được complete |
| `viewed_fraction_required` | `DECIMAL(5,4)` | No | `0.8000` | Tỷ lệ nội dung cần xem, 0..1 |
| `required_for_periods_starting_at` | `DATETIME2(3)` | Yes |  | Enrollment period bắt đầu trước mốc này xem Lesson mới như 'Xem thêm' |
| `status` | `VARCHAR(20)` | No | `'DRAFT'` | DRAFT/PUBLISHED/HIDDEN/TRASH/HISTORICAL |
| `published_at` | `DATETIME2(3)` | Yes |  | UTC |
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
| `deleted_by_user_id` | `users(id)` | `SET NULL` |  |

### Unique Constraints

- `UNIQUE (public_id)`
- `UNIQUE (course_id, position)`

### Check Constraints

- `position > 0`
- `estimated_duration_minutes IS NULL OR estimated_duration_minutes > 0`
- `minimum_completion_seconds >= 0`
- `viewed_fraction_required >= 0 AND viewed_fraction_required <= 1`
- `status IN ('DRAFT','PUBLISHED','HIDDEN','TRASH','HISTORICAL')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_lessons_course_status_position` | `course_id, status, position` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Không cascade LessonProgress lịch sử. Unused Lesson có thể hard-delete sau recovery.

### Audit behavior

Reorder/material edit/delete audit; material edit của published Course qua approval.

### Concurrency

row_version; reorder toàn Course trong transaction với temporary positions/locking.

### Security / PII classification

Markdown untrusted; output phải sanitize + CSP.

### Important invariants

- Completed Student không bị uncomplete do rewrite
- Lesson mới không làm existing period tụt progress: required_for_periods_starting_at quyết định eligibility

---

## `enrollments`

**Purpose**

Một logical Enrollment duy nhất cho mỗi Student-Course; re-enroll tái sử dụng row và mở period mới.

**Lifecycle**

ACTIVE ↔ LEFT qua re-enroll; COMPLETED là current cycle; RETENTION_PENDING/DETAIL_PURGED phản ánh cleanup chi tiết của period cũ.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `public_id` | `UNIQUEIDENTIFIER` | No | `NEWSEQUENTIALID()` | ID công khai dùng trong URL/API; không thay thế kiểm tra quyền |
| `student_user_id` | `BIGINT` | No |  | Student |
| `course_id` | `BIGINT` | No |  | Course |
| `status` | `VARCHAR(24)` | No | `'ACTIVE'` | ACTIVE/LEFT/COMPLETED/RETENTION_PENDING/DETAIL_PURGED |
| `current_period_id` | `BIGINT` | Yes |  | Period hiện hành; FK deferred sau enrollment_periods |
| `current_progress_percent` | `DECIMAL(5,2)` | No | `0` | Cache derived; không phải source of truth |
| `enrolled_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Lần enroll/re-enroll hiện hành |
| `left_at` | `DATETIME2(3)` | Yes |  | Lần rời gần nhất |
| `completed_at` | `DATETIME2(3)` | Yes |  | Lần current cycle hoàn thành |
| `detail_retention_due_at` | `DATETIME2(3)` | Yes |  | Mốc cleanup detail của period đã rời |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `updated_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm cập nhật cuối (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `student_user_id` | `users(id)` | `NO ACTION` |  |
| `course_id` | `courses(id)` | `NO ACTION` |  |
| `current_period_id` | `enrollment_periods(id)` | `SET NULL` | Deferred cross-domain FK created in `010_cross_domain_constraints.sql`. |

### Unique Constraints

- `UNIQUE (public_id)`
- `UNIQUE (student_user_id, course_id)`

### Check Constraints

- `status IN ('ACTIVE','LEFT','COMPLETED','RETENTION_PENDING','DETAIL_PURGED')`
- `current_progress_percent >= 0 AND current_progress_percent <= 100`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_enrollments_course_status` | `course_id, status, student_user_id` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_enrollments_student_status` | `student_user_id, status, course_id` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_enrollments_retention` | `detail_retention_due_at, status` | No | `detail_retention_due_at IS NOT NULL` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Không hard-delete logical Enrollment nếu có compact summary/history.

### Audit behavior

Enroll/leave/re-enroll/completion chủ yếu qua enrollment_events; admin changes audit.

### Concurrency

row_version; enroll/re-enroll/capacity trong transaction khóa Course row.

### Security / PII classification

Student data; Instructor chỉ Course mình quản lý.

### Important invariants

- Unique Student-Course
- Chỉ một active period
- current_progress_percent là cache, recompute từ LessonProgress/AssessmentResult

---

## `enrollment_periods`

**Purpose**

Phân đoạn các lần học bên dưới cùng logical Enrollment để reset khi re-enroll và purge đúng period.

**Lifecycle**

ACTIVE → LEFT/COMPLETED; LEFT → PURGED sau 30 ngày nếu không cần giữ detail. Re-enroll tạo period_no mới nhưng cùng Enrollment.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `enrollment_id` | `BIGINT` | No |  | Logical Enrollment |
| `period_no` | `INT` | No |  | 1,2,3... |
| `started_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Bắt đầu period |
| `left_at` | `DATETIME2(3)` | Yes |  | Rời period |
| `completed_at` | `DATETIME2(3)` | Yes |  | Hoàn thành trong period |
| `retention_due_at` | `DATETIME2(3)` | Yes |  | left_at + 30 ngày nếu không rejoin |
| `detail_purged_at` | `DATETIME2(3)` | Yes |  | Đã xóa dữ liệu chi tiết |
| `status` | `VARCHAR(20)` | No | `'ACTIVE'` | ACTIVE/LEFT/COMPLETED/PURGED |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `enrollment_id` | `enrollments(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (enrollment_id, period_no)`

### Check Constraints

- `period_no > 0`
- `status IN ('ACTIVE','LEFT','COMPLETED','PURGED')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_enrollment_periods_retention` | `retention_due_at, status` | No | `retention_due_at IS NOT NULL` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_enrollment_periods_enrollment` | `enrollment_id, period_no` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ux_enrollment_period_active` | `enrollment_id` | Yes | `status='ACTIVE'` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Period header có thể giữ lâu dài hoặc compact; detail child có thể purge.

### Audit behavior

Lifecycle facts quan trọng phản chiếu trong enrollment_events.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Learning history.

### Important invariants

- Tối đa một ACTIVE period/enrollment (service + filtered unique index đề xuất)
- Re-enroll luôn period mới/reset progress

---

## `enrollment_events`

**Purpose**

Lịch sử nhỏ, append-only cho enroll/leave/re-enroll/completion/purge.

**Lifecycle**

Append-only.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `enrollment_id` | `BIGINT` | No |  | Enrollment |
| `period_id` | `BIGINT` | Yes |  | Period liên quan |
| `event_type` | `VARCHAR(24)` | No |  | ENROLLED/LEFT/REENROLLED/COMPLETED/DETAIL_PURGED |
| `actor_user_id` | `BIGINT` | Yes |  | Ai gây sự kiện |
| `reason` | `NVARCHAR(500)` | Yes |  | Lý do nếu có |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `enrollment_id` | `enrollments(id)` | `NO ACTION` |  |
| `period_id` | `enrollment_periods(id)` | `SET NULL` |  |
| `actor_user_id` | `users(id)` | `SET NULL` |  |

### Unique Constraints

_None._

### Check Constraints

- `event_type IN ('ENROLLED','LEFT','REENROLLED','COMPLETED','DETAIL_PURGED')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_enrollment_events_enrollment` | `enrollment_id, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Giữ compact history; không phụ thuộc detail purge.

### Audit behavior

Business history, không thay AuditEvent cho sensitive admin action.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Learning history.

### Important invariants

- Không update existing event

---

## `lesson_progress`

**Purpose**

Source of truth cho tiến độ Lesson trong từng enrollment period.

**Lifecycle**

Tạo khi bắt đầu học; cộng dần; completed_at một chiều trong period.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `enrollment_period_id` | `BIGINT` | No |  | Period |
| `lesson_id` | `BIGINT` | No |  | Lesson |
| `seconds_spent` | `INT` | No | `0` | Thời gian server chấp nhận |
| `max_view_fraction` | `DECIMAL(5,4)` | No | `0` | Tỷ lệ lớn nhất quan sát được |
| `last_activity_at` | `DATETIME2(3)` | Yes |  | Heartbeat/view gần nhất |
| `completed_at` | `DATETIME2(3)` | Yes |  | Đạt điều kiện completion |
| `completion_rule_snapshot_json` | `NVARCHAR(MAX)` | Yes |  | Ngưỡng tối thiểu tại lúc complete để giải thích lịch sử |
| `updated_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm cập nhật cuối (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `enrollment_period_id` | `enrollment_periods(id)` | `NO ACTION` |  |
| `lesson_id` | `lessons(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (enrollment_period_id, lesson_id)`

### Check Constraints

- `seconds_spent >= 0`
- `max_view_fraction >= 0 AND max_view_fraction <= 1`
- `completion_rule_snapshot_json IS NULL OR ISJSON(completion_rule_snapshot_json)=1`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_lesson_progress_period_complete` | `enrollment_period_id, completed_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Purge theo enrollment period retention; completed Course proof nằm summary.

### Audit behavior

Không audit mỗi heartbeat; completion có event/derived log nếu cần.

### Concurrency

row_version/atomic bounded increments để tránh multi-tab overcount.

### Security / PII classification

Student learning data.

### Important invariants

- Client không được gửi trực tiếp completed=true; server xét seconds_spent + max_view_fraction
- Rewrite Lesson không xóa completed_at

---

## `course_completion_summaries`

**Purpose**

Compact historical summary giữ sau detail purge và làm bằng chứng prerequisite.

**Lifecycle**

Upsert khi completion/result quan trọng; tồn tại sau detail purge.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `student_user_id` | `BIGINT` | No |  | Student |
| `course_id` | `BIGINT` | No |  | Course |
| `ever_completed` | `BIT` | No | `0` | Đã từng complete |
| `first_completed_at` | `DATETIME2(3)` | Yes |  | Lần complete đầu |
| `latest_completed_at` | `DATETIME2(3)` | Yes |  | Lần complete gần nhất |
| `final_aggregate_score` | `DECIMAL(9,4)` | Yes |  | Kết quả tổng hợp cuối cần giữ |
| `prerequisite_eligible` | `BIT` | No | `0` | Có thỏa prerequisite lịch sử |
| `source_period_id` | `BIGINT` | Yes |  | Period tạo summary gần nhất |
| `updated_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | UTC |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `student_user_id` | `users(id)` | `NO ACTION` |  |
| `course_id` | `courses(id)` | `NO ACTION` |  |
| `source_period_id` | `enrollment_periods(id)` | `SET NULL` |  |

### Unique Constraints

- `UNIQUE (student_user_id, course_id)`

### Check Constraints

- `final_aggregate_score IS NULL OR final_aggregate_score >= 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_completion_summary_student` | `student_user_id, prerequisite_eligible, course_id` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Không xóa chỉ vì Student leave; anonymization giữ user FK đã anonymized.

### Audit behavior

Điểm tổng thay đổi do nghiệp vụ quan trọng cần score/audit history ở nguồn.

### Concurrency

row_version.

### Security / PII classification

Historical learning result.

### Important invariants

- ever_completed không tự trở về 0 do rule Course thay đổi hoặc re-enroll
- prerequisite eligibility vẫn giữ nếu prior completion hợp lệ

---
