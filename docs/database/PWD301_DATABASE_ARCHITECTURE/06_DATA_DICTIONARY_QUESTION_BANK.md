# 06 DATA DICTIONARY QUESTION BANK

Database engine: **Microsoft SQL Server**. Timestamps are UTC `DATETIME2(3)` unless noted.

## `questions`

**Purpose**

Identity ổn định của một Question trong đúng một Course; nội dung nằm ở revision.

**Lifecycle**

DRAFT → ACTIVE; có thể RETIRED/TRASH. Unused có thể hard-delete sau recovery.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `public_id` | `UNIQUEIDENTIFIER` | No | `NEWSEQUENTIALID()` | ID công khai dùng trong URL/API; không thay thế kiểm tra quyền |
| `course_id` | `BIGINT` | No |  | Course |
| `lesson_id` | `BIGINT` | Yes |  | Lesson tùy chọn |
| `creator_user_id` | `BIGINT` | Yes |  | Người tạo |
| `difficulty` | `VARCHAR(20)` | No |  | REMEMBER/UNDERSTAND/APPLY hoặc mức tương đương |
| `learning_objective` | `NVARCHAR(500)` | Yes |  | Mục tiêu học tập |
| `status` | `VARCHAR(20)` | No | `'DRAFT'` | DRAFT/ACTIVE/RETIRED/TRASH |
| `first_used_at` | `DATETIME2(3)` | Yes |  | Lần đầu được đưa vào Assessment/pool |
| `first_answered_at` | `DATETIME2(3)` | Yes |  | Lần đầu Student trả lời; từ đây type không được đổi |
| `usage_count` | `BIGINT` | No | `0` | Cache số lần được gán vào Attempt |
| `last_used_at` | `DATETIME2(3)` | Yes |  | Cache phục vụ ưu tiên ít dùng |
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
| `lesson_id` | `lessons(id)` | `SET NULL` |  |
| `creator_user_id` | `users(id)` | `NO ACTION` | Preserve creator linkage; User is anonymized in place when required. |
| `deleted_by_user_id` | `users(id)` | `NO ACTION` | Preserve deletion actor linkage. |

### Unique Constraints

- `UNIQUE (public_id)`

### Check Constraints

- `difficulty IN ('REMEMBER','UNDERSTAND','APPLY')`
- `status IN ('DRAFT','ACTIVE','RETIRED','TRASH')`
- `usage_count >= 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_questions_bank_filter` | `course_id, lesson_id, difficulty, status, id` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_questions_usage` | `course_id, last_used_at, usage_count` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Đã có Student answer: không hard-delete source identity/revisions cần grading/audit; chỉ RETIRED sau recovery.

### Audit behavior

Important edit/delete/provenance changes audit.

### Concurrency

row_version; revision creation transaction khóa Question.

### Security / PII classification

Instructor owner Course/Admin.

### Important invariants

- Thuộc đúng một Course
- lesson nếu có phải thuộc cùng course (service)
- is_current = 1 trỏ revision active duy nhất của question (qua filtered unique index uq_question_revisions_current)
- type không đổi sau first_answered_at

---

## `question_revisions`

**Purpose**

Phiên bản nội dung/loại/đáp án semantics của Question. Choices/accepted answers thuộc revision.

**Lifecycle**

Unused Question có thể edit current revision in-place theo service; sau first_used_at, important edit tạo revision_no mới. Revision exposed/graded giữ vô thời hạn.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `question_id` | `BIGINT` | No |  | Question |
| `revision_no` | `INT` | No |  | Tăng tuần tự |
| `is_current` | `BIT` | No | `0` | Cờ đánh dấu revision active/current (kết hợp filtered unique index) |
| `question_type` | `VARCHAR(24)` | No |  | SINGLE_CHOICE/MULTIPLE_CHOICE/TRUE_FALSE/SHORT_ANSWER/ESSAY |
| `content` | `NVARCHAR(MAX)` | No |  | Nội dung câu hỏi |
| `explanation` | `NVARCHAR(MAX)` | Yes |  | Lời giải/giải thích |
| `short_answer_match_mode` | `VARCHAR(16)` | Yes |  | NORMALIZED/EXACT |
| `change_type` | `VARCHAR(24)` | No | `'EDIT'` | INITIAL/EDIT/ANSWER_ONLY/CONTENT_OR_CHOICES |
| `change_reason` | `NVARCHAR(1000)` | Yes |  | Lý do chỉnh sửa/correction |
| `created_by_user_id` | `BIGINT` | Yes |  | Người tạo revision |
| `approved_by_user_id` | `BIGINT` | Yes |  | Người xác nhận nếu từ AI/import |
| `approved_at` | `DATETIME2(3)` | Yes |  | UTC |
| `was_student_exposed` | `BIT` | No | `0` | Đã từng Student thấy |
| `was_used_for_grading` | `BIT` | No | `0` | Đã dùng để grading |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `question_id` | `questions(id)` | `NO ACTION` |  |
| `created_by_user_id` | `users(id)` | `NO ACTION` | Preserve revision provenance. |
| `approved_by_user_id` | `users(id)` | `NO ACTION` | Preserve approval provenance. |

### Unique Constraints

- `UNIQUE (question_id, revision_no)`

### Check Constraints

- `revision_no > 0`
- `question_type IN ('SINGLE_CHOICE','MULTIPLE_CHOICE','TRUE_FALSE','SHORT_ANSWER','ESSAY')`
- `short_answer_match_mode IS NULL OR short_answer_match_mode IN ('NORMALIZED','EXACT')`
- `change_type IN ('INITIAL','EDIT','ANSWER_ONLY','CONTENT_OR_CHOICES')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_question_revisions_question` | `question_id, revision_no` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_question_revisions_exposure` | `was_student_exposed, was_used_for_grading` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `uq_question_revisions_current` | `question_id` | Yes | `is_current = 1` | Đảm bảo duy nhất 1 revision active tại một thời điểm. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Chỉ cleanup revision chưa từng exposed/graded và không current sau policy. Exposed/graded không hard-delete.

### Audit behavior

Correction reason/actor/time là business history; AuditEvent cho sensitive admin/instructor corrections.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Correct answer data không serialize cho Student trước policy release.

### Important invariants

- revision_no monotonic per question
- Type change bị chặn nếu questions.first_answered_at không NULL
- ANSWER_ONLY chỉ thay answer key, không content/choice text

---

## `question_revision_choices`

**Purpose**

Choices immutable theo từng QuestionRevision; correct flag không bao giờ gửi trong Student attempt payload.

**Lifecycle**

Tạo cùng revision; không mutate khi revision đã exposed/graded.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `question_revision_id` | `BIGINT` | No |  | Revision |
| `choice_key` | `UNIQUEIDENTIFIER` | No | `NEWID()` | ID ổn định trong revision |
| `content` | `NVARCHAR(MAX)` | No |  | Nội dung lựa chọn |
| `is_correct` | `BIT` | No | `0` | Thuộc đáp án đúng |
| `position` | `INT` | No |  | Thứ tự chuẩn |
| `is_fixed_position` | `BIT` | No | `0` | Không shuffle nếu bật |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `question_revision_id` | `question_revisions(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (question_revision_id, choice_key)`
- `UNIQUE (question_revision_id, position)`

### Check Constraints

- `position > 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_question_choices_revision` | `question_revision_id, position` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

CASCADE chỉ khi revision được phép hard-delete; exposed revision thì giữ.

### Audit behavior

Thông qua QuestionRevision/AuditEvent.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

is_correct rất nhạy cảm trong exam context.

### Important invariants

- Choice thuộc đúng revision
- Single-choice/TF phải có đúng 1 correct; multiple-choice >=1 correct (service preflight)

---

## `question_revision_accepted_answers`

**Purpose**

Đáp án chấp nhận cho SHORT_ANSWER theo revision.

**Lifecycle**

Theo revision.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `question_revision_id` | `BIGINT` | No |  | Revision |
| `answer_text` | `NVARCHAR(1000)` | No |  | Đáp án gốc |
| `answer_normalized` | `NVARCHAR(1000)` | No |  | Trim + lowercase cho NORMALIZED; service tính |
| `position` | `INT` | No | `1` | Thứ tự hiển thị/quản trị |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `question_revision_id` | `question_revisions(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (question_revision_id, answer_normalized)`

### Check Constraints

- `position > 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_accepted_answers_revision` | `question_revision_id, position` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Theo revision retention.

### Audit behavior

Thông qua revision.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Answer key; không expose trước policy.

### Important invariants

- Chỉ dùng cho SHORT_ANSWER
- EXACT mode so sánh answer_text; NORMALIZED dùng answer_normalized

---

## `question_provenance`

**Purpose**

Nguồn gốc Question/Revision: manual, import, AI-generated, duplicate; giữ traceability không phụ thuộc source record sống mãi.

**Lifecycle**

Append thêm provenance khi cần; không rewrite AI origin dù Instructor sửa mạnh.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `question_id` | `BIGINT` | No |  | Question |
| `question_revision_id` | `BIGINT` | Yes |  | Revision cụ thể |
| `source_type` | `VARCHAR(24)` | No |  | MANUAL/IMPORT/AI_GENERATED/DUPLICATED |
| `source_ref_type` | `VARCHAR(32)` | Yes |  | Tên loại nguồn |
| `source_ref_id` | `BIGINT` | Yes |  | ID nguồn nếu còn |
| `source_question_id` | `BIGINT` | Yes |  | Question gốc nếu DUPLICATED |
| `ai_model` | `NVARCHAR(100)` | Yes |  | Model tạo/gợi ý |
| `generated_at` | `DATETIME2(3)` | Yes |  | UTC |
| `approved_by_user_id` | `BIGINT` | Yes |  | Instructor approve |
| `approved_at` | `DATETIME2(3)` | Yes |  | UTC |
| `notes` | `NVARCHAR(1000)` | Yes |  | Metadata provenance ngắn |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `question_id` | `questions(id)` | `NO ACTION` |  |
| `question_revision_id` | `question_revisions(id)` | `SET NULL` |  |
| `source_question_id` | `questions(id)` | `SET NULL` |  |
| `approved_by_user_id` | `users(id)` | `SET NULL` |  |

### Unique Constraints

_None._

### Check Constraints

- `source_type IN ('MANUAL','IMPORT','AI_GENERATED','DUPLICATED')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_question_provenance_question` | `question_id, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_question_provenance_source` | `source_type, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Giữ cùng historical Question; source_ref có thể orphan hợp lệ.

### Audit behavior

Approval AI/import audit riêng khi quan trọng.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Không chứa raw prompt; chỉ metadata nguồn.

### Important invariants

- AI-generated draft chỉ tạo Question sau explicit Instructor approval

---
