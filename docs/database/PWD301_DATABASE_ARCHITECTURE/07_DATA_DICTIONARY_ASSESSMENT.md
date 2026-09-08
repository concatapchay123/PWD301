# 07 DATA DICTIONARY ASSESSMENT

Database engine: **Microsoft SQL Server**. Timestamps are UTC `DATETIME2(3)` unless noted.

## `assessments`

**Purpose**

Định nghĩa bài đánh giá dùng chung engine; timing khóa ngay sau publish, structure/points khóa khi Student đầu tiên start.

**Lifecycle**

DRAFT → PUBLISHED; open/closed được derive từ server time + open_at/close_at; có thể CANCELLED/ARCHIVED/TRASH.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `public_id` | `UNIQUEIDENTIFIER` | No | `NEWSEQUENTIALID()` | ID công khai dùng trong URL/API; không thay thế kiểm tra quyền |
| `course_id` | `BIGINT` | No |  | Course |
| `creator_user_id` | `BIGINT` | Yes |  | Instructor/Admin |
| `title` | `NVARCHAR(200)` | No |  | Tên Assessment |
| `description` | `NVARCHAR(MAX)` | Yes |  | Mô tả |
| `assessment_type` | `VARCHAR(20)` | No |  | PRACTICE/QUIZ/MIDTERM/FINAL/PLACEMENT |
| `status` | `VARCHAR(20)` | No | `'DRAFT'` | DRAFT/PUBLISHED/CANCELLED/ARCHIVED/TRASH |
| `open_at` | `DATETIME2(3)` | Yes |  | Giờ mở |
| `close_at` | `DATETIME2(3)` | Yes |  | Giờ đóng cứng |
| `time_limit_minutes` | `INT` | Yes |  | Giới hạn thời gian |
| `attempt_limit` | `INT` | Yes |  | NULL = không giới hạn |
| `scoring_policy` | `VARCHAR(20)` | No | `'HIGHEST'` | FIRST/LATEST/HIGHEST/AVERAGE |
| `passing_percent` | `DECIMAL(5,2)` | Yes |  | Ngưỡng đạt |
| `is_required_for_completion` | `BIT` | No | `0` | Có ảnh hưởng Course completion |
| `shuffle_questions` | `BIT` | No | `0` | Trộn câu |
| `shuffle_choices` | `BIT` | No | `0` | Trộn choice mặc định |
| `score_release_policy` | `VARCHAR(24)` | No | `'IMMEDIATE'` | IMMEDIATE/AFTER_CLOSE/INSTRUCTOR_RELEASE |
| `answer_visibility_policy` | `VARCHAR(32)` | No | `'AFTER_CLOSE'` | IMMEDIATE/AFTER_CLOSE/AFTER_ALL_ATTEMPTS/NEVER |
| `random_question_count` | `INT` | Yes |  | Tổng số câu chọn ngẫu nhiên nếu dùng pool |
| `published_at` | `DATETIME2(3)` | Yes |  | Mốc publish đầu tiên; một khi đã set thì không được clear/đổi, và timing immutable từ mốc này |
| `first_attempt_started_at` | `DATETIME2(3)` | Yes |  | Marker khóa structure/points |
| `cancelled_at` | `DATETIME2(3)` | Yes |  | UTC |
| `cancel_reason` | `NVARCHAR(1000)` | Yes |  | Lý do hủy |
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
| `creator_user_id` | `users(id)` | `NO ACTION` | Preserve creator history; User is anonymized in place when required. |
| `deleted_by_user_id` | `users(id)` | `NO ACTION` | Preserve deletion actor history. |

### Unique Constraints

- `UNIQUE (public_id)`

### Check Constraints

- `assessment_type IN ('PRACTICE','QUIZ','MIDTERM','FINAL','PLACEMENT')`
- `status IN ('DRAFT','PUBLISHED','CANCELLED','ARCHIVED','TRASH')`
- `time_limit_minutes IS NULL OR time_limit_minutes > 0`
- `attempt_limit IS NULL OR attempt_limit > 0`
- `scoring_policy IN ('FIRST','LATEST','HIGHEST','AVERAGE')`
- `passing_percent IS NULL OR (passing_percent >= 0 AND passing_percent <= 100)`
- `score_release_policy IN ('IMMEDIATE','AFTER_CLOSE','INSTRUCTOR_RELEASE')`
- `answer_visibility_policy IN ('IMMEDIATE','AFTER_CLOSE','AFTER_ALL_ATTEMPTS','NEVER')`
- `random_question_count IS NULL OR random_question_count > 0`
- `open_at IS NULL OR close_at IS NULL OR open_at < close_at`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_assessments_course_status` | `course_id, status, open_at, close_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_assessments_pending_window` | `status, open_at, close_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

No-attempt có thể hard-delete sau recovery. Có attempts: archive/historical, không cascade.

### Audit behavior

Publish/cancel/delete/timing config before publish/material edits audit.

### Concurrency

row_version; publish/start dùng transaction; critical locks enforced by triggers + service.

### Security / PII classification

Instructor owner Course/Admin. Student chỉ thấy published + authorized fields.

### Important invariants

- `published_at` là write-once marker; sau khi set không được clear/đổi và không update open_at/close_at/time_limit
- `first_attempt_started_at` là write-once marker; sau khi set không được clear/đổi và không thay structure/points
- Close là hard boundary

---

## `assessment_sections`

**Purpose**

Nhóm câu tùy chọn trong Assessment; hỗ trợ structure rõ nhưng không bắt buộc.

**Lifecycle**

Editable trước first start; sau đó structure locked.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `assessment_id` | `BIGINT` | No |  | Assessment |
| `title` | `NVARCHAR(200)` | Yes |  | Tên section |
| `position` | `INT` | No |  | Thứ tự |
| `instructions` | `NVARCHAR(MAX)` | Yes |  | Hướng dẫn |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `assessment_id` | `assessments(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (assessment_id, position)`

### Check Constraints

- `position > 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_assessment_sections` | `assessment_id, position` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

CASCADE chỉ khi Assessment chưa có attempt và được hard-delete; service chặn thay đổi sau first start.

### Audit behavior

Structural change audit khi published/pre-start.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Instructor/Admin.

### Important invariants

- Không insert/delete/reorder sau assessments.first_attempt_started_at

---

## `assessment_question_assignments`

**Purpose**

Câu tĩnh được đưa trực tiếp vào Assessment; thường luôn xuất hiện.

**Lifecycle**

Editable đến first start; sau đó immutable structure/points.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `assessment_id` | `BIGINT` | No |  | Assessment |
| `section_id` | `BIGINT` | Yes |  | Section |
| `question_id` | `BIGINT` | No |  | Question identity; Attempt sẽ resolve latest current revision tại start |
| `position` | `INT` | No |  | Vị trí chuẩn |
| `points` | `DECIMAL(9,4)` | No |  | Điểm của câu trong Assessment |
| `is_mandatory` | `BIT` | No | `1` | Bắt buộc xuất hiện |
| `shuffle_choices_override` | `BIT` | Yes |  | NULL dùng Assessment default |
| `source_type` | `VARCHAR(20)` | No | `'BANK'` | MANUAL/BANK/IMPORT/AI |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `assessment_id` | `assessments(id)` | `NO ACTION` |  |
| `section_id` | `assessment_sections(id)` | `SET NULL` |  |
| `question_id` | `questions(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (assessment_id, question_id)`

### Check Constraints

- `position > 0`
- `points > 0`
- `source_type IN ('MANUAL','BANK','IMPORT','AI')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_assessment_assignments_position` | `assessment_id, position` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Không xóa sau first start; trước đó application-managed.

### Audit behavior

Add/remove/points change sau publish-prestart audit.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Instructor owner/Admin.

### Important invariants

- Question phải thuộc same Course
- Question revision không pin ở đây theo latest-revision rule
- points locked after first start

---

## `assessment_blueprints`

**Purpose**

Ma trận chọn câu tự động cho Assessment.

**Lifecycle**

DRAFT → READY; FROZEN khi first attempt start/materialization locked.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `assessment_id` | `BIGINT` | No |  | Assessment |
| `name` | `NVARCHAR(200)` | No |  | Tên blueprint |
| `status` | `VARCHAR(16)` | No | `'DRAFT'` | DRAFT/READY/FROZEN |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `updated_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm cập nhật cuối (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `assessment_id` | `assessments(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (assessment_id, name)`

### Check Constraints

- `status IN ('DRAFT','READY','FROZEN')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_blueprints_assessment` | `assessment_id, status` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Editable/delete trước first start; giữ khi attempts tồn tại.

### Audit behavior

Blueprint structural changes audit.

### Concurrency

row_version.

### Security / PII classification

Instructor/Admin.

### Important invariants

- Không thay rule sau first start

---

## `assessment_blueprint_rules`

**Purpose**

Một dòng điều kiện ma trận: lesson/difficulty/type/count/points.

**Lifecycle**

Theo blueprint; frozen sau first start.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `blueprint_id` | `BIGINT` | No |  | Blueprint |
| `section_id` | `BIGINT` | Yes |  | Section |
| `lesson_id` | `BIGINT` | Yes |  | Lesson filter |
| `difficulty` | `VARCHAR(20)` | Yes |  | Difficulty filter |
| `question_type` | `VARCHAR(24)` | Yes |  | Type filter |
| `question_count` | `INT` | No |  | Số cần lấy |
| `points_each` | `DECIMAL(9,4)` | No |  | Điểm mỗi câu |
| `position` | `INT` | No | `1` | Thứ tự rule |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `blueprint_id` | `assessment_blueprints(id)` | `NO ACTION` |  |
| `section_id` | `assessment_sections(id)` | `SET NULL` |  |
| `lesson_id` | `lessons(id)` | `SET NULL` |  |

### Unique Constraints

- `UNIQUE (blueprint_id, position)`

### Check Constraints

- `question_count > 0`
- `points_each > 0`
- `position > 0`
- `difficulty IS NULL OR difficulty IN ('REMEMBER','UNDERSTAND','APPLY')`
- `question_type IS NULL OR question_type IN ('SINGLE_CHOICE','MULTIPLE_CHOICE','TRUE_FALSE','SHORT_ANSWER','ESSAY')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_blueprint_rules_filter` | `blueprint_id, lesson_id, difficulty, question_type` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

CASCADE khi blueprint disposable; historical attempts không reference rule trực tiếp bắt buộc.

### Audit behavior

Structural changes audit.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Instructor/Admin.

### Important invariants

- Preflight phải chứng minh đủ candidate trước publish
- points/count locked after first start

---

## `assessment_question_pool`

**Purpose**

Pool candidate đã materialize/curate để randomize ổn định; ngăn pool tự thay đổi âm thầm sau first start.

**Lifecycle**

Materialize/refresh trước first start; frozen sau first start.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `assessment_id` | `BIGINT` | No |  | Assessment |
| `blueprint_rule_id` | `BIGINT` | Yes |  | Rule nguồn |
| `question_id` | `BIGINT` | No |  | Question identity |
| `points` | `DECIMAL(9,4)` | No |  | Điểm nếu được chọn |
| `is_fixed` | `BIT` | No | `0` | Nếu 1 thì luôn chọn |
| `position_hint` | `INT` | Yes |  | Gợi ý order nếu không shuffle |
| `selection_source` | `VARCHAR(20)` | No | `'BLUEPRINT'` | BLUEPRINT/MANUAL_POOL/IMPORT/AI |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `assessment_id` | `assessments(id)` | `NO ACTION` |  |
| `blueprint_rule_id` | `assessment_blueprint_rules(id)` | `SET NULL` |  |
| `question_id` | `questions(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (assessment_id, question_id)`

### Check Constraints

- `points > 0`
- `position_hint IS NULL OR position_hint > 0`
- `selection_source IN ('BLUEPRINT','MANUAL_POOL','IMPORT','AI')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_assessment_pool_rule` | `assessment_id, blueprint_rule_id, is_fixed, question_id` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Không add/remove/points change sau first start.

### Audit behavior

Pool refresh/add/remove audit khi published.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Instructor/Admin.

### Important invariants

- Question phải thuộc same Course
- Pool shortage block publish/finalization
- Future Attempt chọn trong frozen pool nhưng resolve latest valid QuestionRevision

---
