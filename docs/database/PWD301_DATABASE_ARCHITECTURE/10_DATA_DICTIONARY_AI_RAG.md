# 10 DATA DICTIONARY AI RAG

Database engine: **Microsoft SQL Server**. Timestamps are UTC `DATETIME2(3)` unless noted.

## `ai_conversations`

**Purpose**

Phiên chat ngắn hạn; raw conversation tự xóa sau 5 phút inactivity.

**Lifecycle**

ACTIVE; mỗi user message reset expiry; >5 phút → EXPIRED → raw message cleanup/DELETED.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `public_id` | `UNIQUEIDENTIFIER` | No | `NEWSEQUENTIALID()` | ID công khai dùng trong URL/API; không thay thế kiểm tra quyền |
| `user_id` | `BIGINT` | No |  | User |
| `context_type` | `VARCHAR(16)` | No |  | GLOBAL/COURSE/LESSON |
| `course_id` | `BIGINT` | Yes |  | Context Course |
| `lesson_id` | `BIGINT` | Yes |  | Context Lesson |
| `last_activity_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Tin nhắn user gần nhất |
| `expires_at` | `DATETIME2(3)` | No |  | last user activity + 5 phút |
| `status` | `VARCHAR(16)` | No | `'ACTIVE'` | ACTIVE/EXPIRED/DELETED |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `user_id` | `users(id)` | `NO ACTION` |  |
| `course_id` | `courses(id)` | `SET NULL` |  |
| `lesson_id` | `lessons(id)` | `SET NULL` |  |

### Unique Constraints

- `UNIQUE (public_id)`

### Check Constraints

- `context_type IN ('GLOBAL','COURSE','LESSON')`
- `status IN ('ACTIVE','EXPIRED','DELETED')`
- `expires_at > created_at`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_ai_conversations_expiry` | `expires_at, status` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_ai_conversations_user` | `user_id, status, last_activity_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Raw conversation hard-delete/clear sau 5 phút; security metadata tách ai_requests/security_events.

### Audit behavior

Không giữ raw content để audit.

### Concurrency

row_version; update expiry conditional.

### Security / PII classification

Raw chat may contain PII; strict short retention.

### Important invariants

- 5-minute inactivity based on user messages
- No raw chat retention beyond policy except brief cleanup latency

---

## `ai_messages`

**Purpose**

Raw user/assistant messages tạm thời trong conversation 5 phút.

**Lifecycle**

Tồn tại tối đa conversation retention.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `conversation_id` | `BIGINT` | No |  | Conversation |
| `sender` | `VARCHAR(12)` | No |  | USER/ASSISTANT |
| `content` | `NVARCHAR(MAX)` | No |  | Raw content temporary |
| `sequence_no` | `INT` | No |  | Order |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `conversation_id` | `ai_conversations(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (conversation_id, sequence_no)`

### Check Constraints

- `sender IN ('USER','ASSISTANT')`
- `sequence_no > 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_ai_messages_conversation` | `conversation_id, sequence_no` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Hard-delete khi conversation expires.

### Audit behavior

Không dùng làm audit.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Sensitive; minimum access.

### Important invariants

- Cleanup worker must remove raw content after 5-minute inactivity

---

## `ai_requests`

**Purpose**

Metadata mỗi AI/backend routing request; giữ usage/security mà không cần raw prompt lâu dài.

**Lifecycle**

Append metadata; aggregate/archive later.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `request_id` | `UNIQUEIDENTIFIER` | No | `NEWID()` | Correlation public |
| `conversation_id` | `BIGINT` | Yes |  | Conversation nếu chat |
| `user_id` | `BIGINT` | No |  | Caller |
| `route_type` | `VARCHAR(24)` | No |  | BACKEND_ONLY/GEMINI/RAG/CLASSIFIER |
| `model_name` | `NVARCHAR(100)` | Yes |  | Model nếu external |
| `prompt_hash` | `BINARY(32)` | Yes |  | Hash normalized prompt |
| `scope_decision` | `VARCHAR(16)` | Yes |  | IN_SCOPE/OUT_OF_SCOPE/MIXED/AMBIGUOUS |
| `authorization_scope_hash` | `BINARY(32)` | Yes |  | Hash access envelope để debug/cache safety |
| `input_token_count` | `INT` | Yes |  | Usage |
| `output_token_count` | `INT` | Yes |  | Usage |
| `latency_ms` | `INT` | Yes |  | Latency |
| `status` | `VARCHAR(20)` | No |  | SUCCEEDED/REFUSED/FAILED/TIMEOUT/BYPASSED |
| `error_code` | `VARCHAR(64)` | Yes |  | Sanitized |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `conversation_id` | `ai_conversations(id)` | `SET NULL` |  |
| `user_id` | `users(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (request_id)`

### Check Constraints

- `route_type IN ('BACKEND_ONLY','GEMINI','RAG','CLASSIFIER')`
- `scope_decision IS NULL OR scope_decision IN ('IN_SCOPE','OUT_OF_SCOPE','MIXED','AMBIGUOUS')`
- `status IN ('SUCCEEDED','REFUSED','FAILED','TIMEOUT','BYPASSED')`
- `input_token_count IS NULL OR input_token_count >= 0`
- `output_token_count IS NULL OR output_token_count >= 0`
- `latency_ms IS NULL OR latency_ms >= 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_ai_requests_user_time` | `user_id, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_ai_requests_status_time` | `status, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

May retain longer than raw chat because no raw text; follow privacy policy.

### Audit behavior

Security events link by correlation/hash, not raw content.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

May be sensitive metadata; no full prompt/response stored.

### Important invariants

- Backend-computable request may be BYPASSED without Gemini
- Personalized response never enters shared cache

---

## `ai_generated_question_drafts`

**Purpose**

Draft câu hỏi do AI tạo; không vào Question Bank trước Instructor review.

**Lifecycle**

PENDING → keep/edit/reject/approve. APPROVED creates Question+Revision+Provenance.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `course_id` | `BIGINT` | No |  | Course |
| `lesson_id` | `BIGINT` | Yes |  | Lesson source |
| `requested_by_user_id` | `BIGINT` | No |  | Instructor |
| `ai_request_id` | `BIGINT` | Yes |  | Request metadata |
| `ordinal` | `INT` | No |  | Order |
| `question_type` | `VARCHAR(24)` | No |  | Requested/generated type |
| `difficulty` | `VARCHAR(20)` | No |  | REMEMBER/UNDERSTAND/APPLY |
| `content` | `NVARCHAR(MAX)` | No |  | Draft |
| `choices_json` | `NVARCHAR(MAX)` | Yes |  | Draft choices |
| `answer_json` | `NVARCHAR(MAX)` | Yes |  | Draft answer |
| `explanation` | `NVARCHAR(MAX)` | Yes |  | Draft explanation |
| `review_state` | `VARCHAR(16)` | No | `'PENDING'` | PENDING/KEPT/EDITED/REJECTED/APPROVED |
| `approved_question_id` | `BIGINT` | Yes |  | Question sau approve |
| `reviewed_by_user_id` | `BIGINT` | Yes |  | Instructor |
| `reviewed_at` | `DATETIME2(3)` | Yes |  | UTC |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `updated_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm cập nhật cuối (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `course_id` | `courses(id)` | `NO ACTION` |  |
| `lesson_id` | `lessons(id)` | `SET NULL` |  |
| `requested_by_user_id` | `users(id)` | `NO ACTION` |  |
| `ai_request_id` | `ai_requests(id)` | `SET NULL` |  |
| `approved_question_id` | `questions(id)` | `SET NULL` |  |
| `reviewed_by_user_id` | `users(id)` | `SET NULL` |  |

### Unique Constraints

_None._

### Check Constraints

- `ordinal > 0`
- `question_type IN ('SINGLE_CHOICE','MULTIPLE_CHOICE','TRUE_FALSE','SHORT_ANSWER','ESSAY')`
- `difficulty IN ('REMEMBER','UNDERSTAND','APPLY')`
- `review_state IN ('PENDING','KEPT','EDITED','REJECTED','APPROVED')`
- `choices_json IS NULL OR ISJSON(choices_json)=1`
- `answer_json IS NULL OR ISJSON(answer_json)=1`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_ai_drafts_review` | `course_id, review_state, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Rejected drafts may cleanup after short retention; provenance retained for approved question.

### Audit behavior

Approval/AI origin captured by question_provenance.

### Concurrency

row_version.

### Security / PII classification

Educational content draft, not Student-visible.

### Important invariants

- Never auto-insert to Question Bank

---

## `knowledge_documents`

**Purpose**

Logical source eligible for RAG metadata; authorization remains LMS source entity, not vector index.

**Lifecycle**

ACTIVE; source edit creates new version and invalidates old searchable version; source delete/archive disables retrieval immediately.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `public_id` | `UNIQUEIDENTIFIER` | No | `NEWSEQUENTIALID()` | ID công khai dùng trong URL/API; không thay thế kiểm tra quyền |
| `course_id` | `BIGINT` | No |  | Course |
| `lesson_id` | `BIGINT` | Yes |  | Lesson source |
| `source_type` | `VARCHAR(24)` | No |  | LESSON/FILE/FAQ/POLICY |
| `source_entity_id` | `BIGINT` | No |  | ID source entity |
| `status` | `VARCHAR(20)` | No | `'ACTIVE'` | ACTIVE/INVALIDATED/DELETED |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `updated_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm cập nhật cuối (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `course_id` | `courses(id)` | `NO ACTION` |  |
| `lesson_id` | `lessons(id)` | `SET NULL` |  |

### Unique Constraints

- `UNIQUE (public_id)`
- `UNIQUE (source_type, source_entity_id)`

### Check Constraints

- `source_type IN ('LESSON','FILE','FAQ','POLICY')`
- `status IN ('ACTIVE','INVALIDATED','DELETED')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_knowledge_docs_course_status` | `course_id, status, source_type` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Logical metadata may remain tombstoned; vector entries must be removed/disabled.

### Audit behavior

Index invalidation operational; source content edit audit at source.

### Concurrency

row_version; activation compare current version.

### Security / PII classification

RAG retrieval must prefilter by published/authorized Course/Lesson + active status.

### Important invariants

- Archived Course excluded from retrieval
- Deleted source stops retrieval immediately even if physical file recovery exists

---

## `knowledge_versions`

**Purpose**

Process/activation state cho một version RAG; old version chỉ dùng nếu still valid/authorized.

**Lifecycle**

PENDING → PROCESSING → ACTIVE; previous ACTIVE → INVALIDATED. FAILED không active.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `knowledge_document_id` | `BIGINT` | No |  | Document |
| `version_no` | `INT` | No |  | Sequence |
| `is_current` | `BIT` | No | `0` | Cờ đánh dấu phiên bản active/current (kết hợp filtered unique index) |
| `source_revision_type` | `VARCHAR(32)` | Yes |  | LESSON_VERSION/FILE_REVISION/QUESTION_REVISION/OTHER |
| `source_revision_id` | `BIGINT` | Yes |  | Source revision id |
| `content_hash` | `BINARY(32)` | No |  | Hash extracted text |
| `status` | `VARCHAR(20)` | No | `'PENDING'` | PENDING/PROCESSING/ACTIVE/INVALIDATED/FAILED |
| `vector_namespace` | `NVARCHAR(200)` | Yes |  | Vector store namespace |
| `background_job_id` | `BIGINT` | Yes |  | Generic job; FK deferred |
| `activated_at` | `DATETIME2(3)` | Yes |  | UTC |
| `invalidated_at` | `DATETIME2(3)` | Yes |  | UTC |
| `last_error` | `NVARCHAR(2000)` | Yes |  | Sanitized |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `knowledge_document_id` | `knowledge_documents(id)` | `NO ACTION` |  |
| `background_job_id` | `background_jobs(id)` | `SET NULL` | Deferred cross-domain FK created in `010_cross_domain_constraints.sql`. |

### Unique Constraints

- `UNIQUE (knowledge_document_id, version_no)`

### Check Constraints

- `version_no > 0`
- `status IN ('PENDING','PROCESSING','ACTIVE','INVALIDATED','FAILED')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ux_knowledge_versions_active` | `knowledge_document_id` | Yes | `status = 'ACTIVE'` | DB-enforce tối đa một knowledge version ACTIVE cho mỗi document. |
| `uq_knowledge_versions_current` | `knowledge_document_id` | Yes | `is_current = 1` | Đảm bảo duy nhất 1 version active tại một thời điểm. |
| `ix_knowledge_versions_doc` | `knowledge_document_id, version_no` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_knowledge_versions_status` | `status, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Old invalidated metadata may archive; source version linkage retained enough for answer provenance.

### Audit behavior

Operational.

### Concurrency

row_version; filtered unique index chỉ cho tối đa một ACTIVE version/document; activation transaction đổi current pointer atomically.

### Security / PII classification

No raw secret; extracted content may be sensitive only within course authorization.

### Important invariants

- New version active only after successful processing
- If fail, last valid version may stay active only if source still authorized/not archived/deleted

---

## `knowledge_chunks`

**Purpose**

Metadata chunk; embedding/vector payload nằm vector store riêng để không phụ thuộc SQL Server vector feature.

**Lifecycle**

Created during indexing; invalidated logically with version; vector key deleted/disabled on invalidation.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `knowledge_version_id` | `BIGINT` | No |  | Version |
| `chunk_no` | `INT` | No |  | Order |
| `text_hash` | `BINARY(32)` | No |  | Hash chunk |
| `vector_key` | `NVARCHAR(300)` | No |  | ID trong vector store |
| `token_count` | `INT` | Yes |  | Approx tokens |
| `metadata_json` | `NVARCHAR(MAX)` | Yes |  | Metadata retrieval không chứa unauthorized PII |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `knowledge_version_id` | `knowledge_versions(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (knowledge_version_id, chunk_no)`
- `UNIQUE (vector_key)`

### Check Constraints

- `chunk_no > 0`
- `token_count IS NULL OR token_count >= 0`
- `metadata_json IS NULL OR ISJSON(metadata_json)=1`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_knowledge_chunks_version` | `knowledge_version_id, chunk_no` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Can hard-delete chunks when version historical metadata no longer needs chunk-level detail; source usage may keep version id.

### Audit behavior

No.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Chunk retrieval requires authorization before/vector filter; retrieved content treated as data, never instruction.

### Important invariants

- Vector result must map back to ACTIVE authorized knowledge version

---

## `ai_source_usages`

**Purpose**

Records source version/chunk metadata used by an AI answer/request without retaining raw conversation.

**Lifecycle**

Append metadata per request; may outlive raw chat.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `ai_request_id` | `BIGINT` | No |  | AI request |
| `knowledge_version_id` | `BIGINT` | No |  | Source version |
| `knowledge_chunk_id` | `BIGINT` | Yes |  | Chunk |
| `rank_no` | `INT` | Yes |  | Retrieval rank |
| `relevance_score` | `DECIMAL(8,6)` | Yes |  | Similarity/relevance |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `ai_request_id` | `ai_requests(id)` | `NO ACTION` |  |
| `knowledge_version_id` | `knowledge_versions(id)` | `NO ACTION` |  |
| `knowledge_chunk_id` | `knowledge_chunks(id)` | `SET NULL` |  |

### Unique Constraints

- `UNIQUE (ai_request_id, knowledge_version_id, knowledge_chunk_id)`

### Check Constraints

- `rank_no IS NULL OR rank_no > 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_ai_source_request` | `ai_request_id, rank_no` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_ai_source_version` | `knowledge_version_id, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Retain as debug/audit metadata per privacy policy; no raw source text duplicated.

### Audit behavior

Supports traceability of AI answer source.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Can reveal what course source was used; Admin/debug access limited.

### Important invariants

- Only sources authorized for caller may be recorded/used

---
