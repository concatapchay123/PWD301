# PWD301 Database Architecture

## Project database baseline

Đây là database/ERD implementation baseline cho PWD301 **Topic 9 — Online Course Management Platform**. Package chuyển các quyết định nghiệp vụ đã khóa thành mô hình quan hệ, constraints, indexes, lifecycle, transaction/concurrency rules, retention, security controls và SQL Server reference DDL.

- Application: Python 3.11+ / Flask / Flask-SQLAlchemy.
- Browser authentication: Flask-Login session + CSRF.
- REST API authentication: JWT.
- Primary database: **Microsoft SQL Server**.
- Migration: Flask-Migrate / Alembic.
- Deployment: Docker.
- File bytes: private storage ngoài SQL Server; SQL lưu metadata/authorization/reference.
- Background work: worker cho scan/import/regrade/RAG/email/cleanup.
- AI: Gemini qua backend; authorization/policy không giao cho LLM.

## Identifier strategy

- Internal relational PK: `BIGINT IDENTITY`.
- Public/external ID cho major resources: `UNIQUEIDENTIFIER`, mặc định `NEWSEQUENTIALID()` khi phù hợp.
- Opaque operational/correlation IDs có thể dùng `NEWID()` vì không nằm trên clustered insertion path.

## Time

- Important timestamps được lưu UTC bằng `DATETIME2(3)`.
- Application chịu trách nhiệm đổi sang timezone hiển thị.
- Assessment deadline dùng server time; browser countdown không phải authority.

## Concurrency

- Mutable business rows dùng SQL Server `ROWVERSION` khi cần optimistic concurrency.
- `QuestionRevision` là **business versioning**, không phải optimistic-lock version.
- AssessmentAttempt dùng expiring editor lease/heartbeat; chỉ một tab được edit, stale lease có thể takeover mà không tạo attempt mới.
- Multi-tab lease takeover & autosave sequence collision protection: sử dụng `lease_epoch INT NOT NULL DEFAULT 1` và monotonic `sequence_no`. Khi takeover, `lease_epoch` tăng lên; request mang stale lease token/epoch hoặc stale sequence bị từ chối với HTTP 409 Conflict (`STALE_LEASE_EPOCH` / `STALE_ANSWER`), triệt tiêu race condition ghi đè giữa các tab.
- Không giữ long-lived DB row lock trong suốt thời gian Student làm bài.

## Major domain map

| Domain | Core tables |
|---|---|
| Identity/Auth | `users`, `roles`, `user_roles`, `auth_sessions`, `jwt_token_grants` |
| Course/Learning | `courses`, `lessons`, `enrollments`, `enrollment_periods`, `lesson_progress`, `course_completion_summaries` |
| Question Bank | `questions`, `question_revisions`, revision choices/accepted answers/provenance |
| Assessment | `assessments`, sections, assignments, blueprint/rules, materialized pool |
| Attempt/Grading | `assessment_attempts`, frozen question/choice snapshots, answers, answer events, grades/results |
| Regrading | `question_corrections`, `regrade_jobs`, `regrade_items`, grade/result histories |
| Files/Import | `file_blobs`, `file_assets`, `file_revisions`, secure processing/import review |
| AI/RAG | short-lived conversations/messages, AI request metadata, knowledge documents/versions/chunks/source usage |
| Notification/Audit | notification event fan-out, in-app delivery, email outbox, immutable audit |
| Operations | background jobs, alerts, backup runs, sensitive exports, analytics/health snapshots |

## Document navigation

| Document | Purpose |
|---|---|
| [ARTIFACT_MANIFEST.md](ARTIFACT_MANIFEST.md) | Final package inventory/status/cross-reference |
| [00_DECISION_INVENTORY_AND_CONSISTENCY.md](00_DECISION_INVENTORY_AND_CONSISTENCY.md) | Decision inventory, consistency pass, superseded rules |
| [01_ARCHITECTURE_OVERVIEW.md](01_ARCHITECTURE_OVERVIEW.md) | Database conventions and architecture overview |
| [02_DOMAIN_MODEL.md](02_DOMAIN_MODEL.md) | Domain/source-of-truth model and table map |
| [03_ERD.md](03_ERD.md) | High-level + domain Mermaid ERDs |
| [04_DATA_DICTIONARY_IDENTITY.md](04_DATA_DICTIONARY_IDENTITY.md) | Identity/Auth Data Dictionary |
| [05_DATA_DICTIONARY_COURSE.md](05_DATA_DICTIONARY_COURSE.md) | Course/Learning Data Dictionary |
| [06_DATA_DICTIONARY_QUESTION_BANK.md](06_DATA_DICTIONARY_QUESTION_BANK.md) | Question Bank Data Dictionary |
| [07_DATA_DICTIONARY_ASSESSMENT.md](07_DATA_DICTIONARY_ASSESSMENT.md) | Assessment Data Dictionary |
| [08_DATA_DICTIONARY_ATTEMPT_REGRADING.md](08_DATA_DICTIONARY_ATTEMPT_REGRADING.md) | Attempt/Grading/Regrade Data Dictionary |
| [09_DATA_DICTIONARY_FILES_IMPORT.md](09_DATA_DICTIONARY_FILES_IMPORT.md) | File/Import Data Dictionary |
| [10_DATA_DICTIONARY_AI_RAG.md](10_DATA_DICTIONARY_AI_RAG.md) | AI/RAG Data Dictionary |
| [11_DATA_DICTIONARY_NOTIFICATION_AUDIT_OPERATIONS.md](11_DATA_DICTIONARY_NOTIFICATION_AUDIT_OPERATIONS.md) | Notification/Audit/Operations Data Dictionary |
| [12_STATE_MACHINES.md](12_STATE_MACHINES.md) | Domain state machines |
| [13_CONSTRAINTS_AND_INVARIANTS.md](13_CONSTRAINTS_AND_INVARIANTS.md) | DB/transaction/service/worker enforcement map |
| [14_INDEX_AND_PERFORMANCE_STRATEGY.md](14_INDEX_AND_PERFORMANCE_STRATEGY.md) | Index/query/performance strategy |
| [15_RETENTION_DELETE_RESTORE_MATRIX.md](15_RETENTION_DELETE_RESTORE_MATRIX.md) | Retention/delete/restore/anonymization matrix |
| [16_CONCURRENCY_AND_TRANSACTIONS.md](16_CONCURRENCY_AND_TRANSACTIONS.md) | Race protection and transaction pseudocode |
| [17_SECURITY_DATABASE_REVIEW.md](17_SECURITY_DATABASE_REVIEW.md) | Database security/threat review |
| [18_BUSINESS_RULE_DATABASE_TRACEABILITY.md](18_BUSINESS_RULE_DATABASE_TRACEABILITY.md) | Business rule → DB/service/worker/audit/test traceability |
| [19_DATABASE_INTEGRITY_TEST_PLAN.md](19_DATABASE_INTEGRITY_TEST_PLAN.md) | Constraint/integrity/race/retention test plan |
| [20_MIGRATION_STRATEGY.md](20_MIGRATION_STRATEGY.md) | SQL Server/Alembic migration + seed strategy |
| [21_ASSUMPTIONS_AND_DECISIONS.md](21_ASSUMPTIONS_AND_DECISIONS.md) | Derived DB ADRs and explicit assumptions |
| [OPEN_ISSUES.md](OPEN_ISSUES.md) | Remaining non-blocking implementation/deployment notes |
| [FINAL_DATABASE_REVIEW.md](FINAL_DATABASE_REVIEW.md) | Final multi-role QA and reconciliation evidence |

## SQL manifest and execution order

Reference DDL: [sql/README.md](sql/README.md). Execute in numeric order:

1. [sql/001_identity.sql](sql/001_identity.sql)
2. [sql/002_course_learning.sql](sql/002_course_learning.sql)
3. [sql/003_question_bank.sql](sql/003_question_bank.sql)
4. [sql/004_assessment.sql](sql/004_assessment.sql)
5. [sql/005_attempt_regrade.sql](sql/005_attempt_regrade.sql)
6. [sql/006_files_import.sql](sql/006_files_import.sql)
7. [sql/007_ai_rag.sql](sql/007_ai_rag.sql)
8. [sql/008_notification_audit.sql](sql/008_notification_audit.sql)
9. [sql/009_operations.sql](sql/009_operations.sql)
10. [sql/010_cross_domain_constraints.sql](sql/010_cross_domain_constraints.sql)
11. [sql/011_indexes.sql](sql/011_indexes.sql)
12. [sql/012_critical_invariant_triggers.sql](sql/012_critical_invariant_triggers.sql)

Reference DDL là architecture contract, không phải bằng chứng migrations đã chạy. Production implementation phải giữ cùng invariants qua Alembic migrations.

## Source of truth vs cache vs snapshot

- `lesson_progress` + assessment results là source of truth; `enrollments.current_progress_percent` là derived cache có thể recompute.
- Current QuestionRevision là source content; `attempt_questions`/`attempt_choice_snapshots` là immutable historical snapshot của đúng nội dung Student đã thấy.
- `assessment_results`/`attempt_question_grades` là current grade state; history tables giữ evidence của score changes.
- `analytics_snapshots` và Question usage counters là derived/recomputable.
- File bytes ở private storage; SQL lưu blob hash/storage key và logical references.
- Vector embeddings/index implementation nằm ngoài SQL Server; SQL giữ authorization/provenance/version metadata authoritative.

## Key invariants — backend developer không được phá

1. Authorization luôn kiểm tra object ownership/resource relationship, không chỉ role.
2. Không trả correct-answer flags/explanations cho active Student attempt trước visibility policy.
3. Không rewrite Attempt snapshot khi Question thay đổi.
4. Assessment duration timing (`open_at`, `time_limit_minutes`) bị đóng băng (immutable) sau publish. Window timing (`close_at`) chỉ được phép nới rộng về tương lai (forward extension only) kèm theo ghi nhận bắt buộc audit event `ASSESSMENT_CLOSE_AT_EXTENDED`; tuyệt đối không cho phép rút ngắn thời gian kết thúc.
5. Assessment structure và assigned points bị khóa sau Student đầu tiên start.
6. Question correction vẫn tạo revision/regrade theo rule; không được biến Assessment thành “immutable hoàn toàn sau publish”.
7. Server time quyết định deadline; save đến sau deadline bị reject/not counted.
8. Answer save yêu cầu lease hợp lệ + `lease_epoch` + deadline + monotonic/offline reconciliation rule.
9. Submit idempotent: retry không tạo duplicate result.
10. Regrade worker đối soát dựa trên `choice_key` bền vững (persistent across revisions) giữa snapshot của Student và active QuestionRevision, tránh chấm lệch 0 điểm khi IDs nội bộ thay đổi. Regrade/full-credit correction ghi history và không sửa những gì Student từng thấy/chọn.
11. Cơ chế Skeleton Tombstone Purging cho AssessmentAttempt (`is_detail_purged = 1`, `detail_purged_at`): sau >30 ngày leave không rejoin, chỉ dọn dẹp các bảng con chi tiết (`attempt_answers`, `attempt_answer_events`, `attempt_choice_snapshots`, `attempt_questions`), giữ nguyên metadata của parent attempt và `assessment_results` để bảo toàn audit trail và lịch sử hoàn thành khóa học mà không vi phạm retention.
12. Unsafe/unscanned file không thể trở thành current/Student-accessible; official video upload limit là **< 1 GB**.
13. Loại bỏ hoàn toàn quan hệ khóa ngoại vòng (Circular Foreign Keys) giữa entities và revisions (`questions`, `file_assets`, `knowledge_documents`). Trạng thái active/current được chuyển sang cờ `is_current BIT NOT NULL DEFAULT 0` tại bảng revision/version con kết hợp Filtered Unique Indexes (`WHERE is_current = 1`), bảo đảm không xảy ra deadlock khi bootstrap và bảo đảm tính toàn vẹn ngữ nghĩa (semantic pointer integrity).
14. RAG prefilter authorization + published/active state trước khi expose chunks cho Gemini; archived/deleted content bị loại.
15. Sensitive mutation cần required audit trong transaction thích hợp; audit important records append-only.
16. Không dùng broad `ON DELETE CASCADE` cho historical learning/assessment data.
17. Stale UI editors phải fail optimistic concurrency thay vì silent overwrite.
18. Relational Staging cho Lessons thông qua `change_request_id`, status `PENDING_APPROVAL` và Filtered Unique Index `uq_lessons_course_position_active` trên `(course_id, position) WHERE status IN ('ACTIVE', 'PUBLISHED')`, cho phép staged reordering an toàn mà không xung đột vị trí với bài học đang hiển thị.

## Implementation starting point

Trước khi implement service:

1. tìm business rule trong [18_BUSINESS_RULE_DATABASE_TRACEABILITY.md](18_BUSINESS_RULE_DATABASE_TRACEABILITY.md);
2. đọc invariant ownership trong [13_CONSTRAINTS_AND_INVARIANTS.md](13_CONSTRAINTS_AND_INVARIANTS.md);
3. đọc transaction/race handling trong [16_CONCURRENCY_AND_TRANSACTIONS.md](16_CONCURRENCY_AND_TRANSACTIONS.md);
4. map sang SQLAlchemy model + service + permission layer + tests;
5. giữ route/controller mỏng.

## Validation status

| Check | Status |
|---|---|
| Actual SQL table count | **71** |
| Markdown structural/static QA | **PASS** |
| ERD ↔ Data Dictionary ↔ DDL reconciliation | **PASS — 71/71 tables** |
| SQL Server static compatibility/constraint/index/FK QA | **PASS** |
| Mermaid static block/entity/reference QA | **PASS** |
| SQL Server runtime execution | **NOT EXECUTED — environment limitation (no SQL Server/sqlcmd/Docker runtime available)** |
| Mermaid render validation | **NOT EXECUTED — Mermaid CLI/render engine unavailable; no render claim made** |
| ZIP integrity | **PASS — final archive integrity-tested after last document update** |

Các runtime/load-dependent items còn lại được phân loại NON-BLOCKING trong [OPEN_ISSUES.md](OPEN_ISSUES.md).
