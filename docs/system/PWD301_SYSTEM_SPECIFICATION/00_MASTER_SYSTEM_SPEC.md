# Master System Specification

## Product
PWD301 is a production-oriented LMS for Admin, Instructor and Student. Instructors build reviewed courses, lessons, question banks and assessments; Students enroll, learn, take resumable timed assessments and receive results/recommendations; Admin governs roles, publication, sensitive interventions, operations and audit.

## Actors
- **Student**: discover/enroll/learn, own progress, assessments, AI assistance within authorization.
- **Instructor**: includes Student abilities; owns/manages assigned Courses, content, questions, assessments, grading and course analytics.
- **Admin**: includes Instructor+Student roles; system governance, course/admin overrides with reason/audit, role/account operations and operational recovery.
- **Worker/System**: executes scans, imports, regrades, indexing, email, cleanup, analytics and backups using narrow service authority.

## Architectural shape
Modular monolithic Flask application with server-rendered web routes, REST API, service layer, SQLAlchemy repositories/models, SQL Server, private file storage and separate background worker process(es). No microservice/CQRS/event-sourcing assumption. Controllers stay thin; transactions and authorization live in explicit services.

## Authentication and authorization
Web uses session auth with CSRF. External/REST API uses JWT. Role membership is cumulative but object-level rules determine which Course/Student/Attempt/File a user can access. Suspension invalidates active auth immediately. Sensitive Admin operations require fresh password re-authentication; highest-risk operations also require exact confirmation phrase and reason.

## Learning lifecycle
Course publication/approval controls discovery. Prerequisites, capacity and one-active-enrollment are enforced transactionally. Re-enrollment restarts active progress but retained completion summary can continue satisfying prerequisites. Lesson completion is system-derived from meaningful time plus viewed-most evidence. Existing completions are stable across lesson reorder/material rewrite/new optional lessons.

## Assessment integrity
Assessment supports type, timing, attempt limits, score policy, blueprint/random/fixed questions, shuffling, score/answer release and pass/completion rules. Timing locks after publish. Structure/points lock after first start. Each Student Attempt freezes the exact QuestionRevision, text, choices, order and assigned points it receives. Server time controls deadline. Answer saves are recoverable, lease-protected and monotonic. Submit is idempotent.

## Correction and regrading
Correct-answer-only correction creates a revision and background regrade for eligible retained attempts, preserving old/new grades and notifying changes. Text/choice correction never rewrites historical snapshots; attempts started before the change retain old content and receive the locked full-credit correction policy. Detailed periods purged after >30 days without rejoin are excluded from future regrade.

## Files/import
Uploads enter quarantine, are validated, scanned and processed fail-closed. Direct storage URLs are not public. Physical bytes may deduplicate by hash while logical assets/revisions preserve ownership/history. DOCX/PDF imports produce reviewable drafts, confidence/ambiguity/duplicate flags and secured extracted images; AI suggestions never become official without Instructor confirmation.

## AI/RAG
Backend policy and authorization precede retrieval. Student RAG only uses published authorized content and own learning data. Archived/deleted/draft sources are excluded. Retrieved documents are untrusted data, not instructions. Backend computes recommendations; Gemini explains. Raw AI chat is transient and purged after five minutes of inactivity.

## Data architecture
SQL Server relational model uses BIGINT internal keys, UUID/GUID public identifiers, UTC DATETIME2(3), and ROWVERSION where optimistic concurrency is needed. Validated schema has 71 tables. Full DDL/ERD/Data Dictionary remain authoritative in `docs/database/PWD301_DATABASE_ARCHITECTURE/` at the repository root.

## API and UI
AJAX from web uses session+CSRF. REST API has standardized JSON errors, pagination/filtering, explicit authorization and idempotency where required. Frontend must represent loading/empty/error/conflict states and preserve accessibility/focus/keyboard behavior.

## Security
Controls cover CSRF, XSS, SQL injection, IDOR, mass assignment, replay, authorization, malicious uploads, path traversal, prompt injection/RAG leakage, audit tampering, secrets, sensitive exports and soft-deleted data leakage. Security invariants are testable and fail closed where required.

## Operations
Daily automatic backups plus explicit Admin manual backup; restore never automatically overwrites live DB. Workers have retry/timeouts/idempotency. System health, storage, backup, scanner/Gemini status and slow failures are observable. Secrets stay outside source/image.

## Definition of implementation correctness
A feature is complete only when its business rule, validation, authorization, transaction/concurrency, persistence, side effects, failure behavior, security, tests and acceptance criteria all pass. See `implementation/05_DEFINITION_OF_DONE.md`.
