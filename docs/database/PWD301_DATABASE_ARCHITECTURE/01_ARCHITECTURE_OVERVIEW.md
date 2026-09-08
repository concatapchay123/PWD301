# Architecture Overview

## 1. Architectural objective

The schema is designed for a student project that is materially more capable than CRUD, without importing enterprise patterns that are not justified. The selected style is a **normalized relational core with explicit history at boundaries where history is a business requirement**.

The core principles are:

- relational normalization first;
- database-native PK/FK/unique/check where they can express the rule;
- short ACID transactions for cross-row invariants;
- service-layer authorization/business policy;
- optimistic concurrency for human editing;
- background jobs for slow/retryable work;
- snapshots only where historical evidence must not change;
- append-only histories only where the user explicitly requires traceability;
- private file bytes and external vector index separated from SQL relational state.

No global event sourcing, CQRS, EAV schema, distributed ID system, microservice split, or “generic everything table” is introduced.

## 2. Physical database target

**Microsoft SQL Server** is the required primary database.

### Keys

- `BIGINT IDENTITY(1,1)` is the physical PK for joins and clustered access.
- API-facing primary domain entities also have a `public_id UNIQUEIDENTIFIER`.
- UUIDs reduce casual enumeration but **never** replace authorization checks.

### Time

All persisted lifecycle timestamps use `DATETIME2(3)` and are interpreted as UTC. The backend uses server/database time; UI converts to local timezone.

### Optimistic concurrency

SQL Server `ROWVERSION` is used on mutable records such as:

- User status/profile;
- Course/Lesson;
- Enrollment;
- Assessment;
- Attempt;
- current answer;
- current grade/result;
- file asset/revision;
- AI conversation/version;
- notification/read state;
- background jobs.

A business revision number such as `question_revisions.revision_no` is a historical content version and has a completely different purpose.

## 3. Authorization boundaries supported by schema

The DB provides relationships that the permission layer must evaluate:

- Course → owner Instructor;
- Lesson/Assessment/Question → Course;
- Enrollment → Student + Course;
- Attempt → Student + Assessment + EnrollmentPeriod;
- FileAsset → Course + Lesson/Question links;
- KnowledgeDocument → Course/Lesson source;
- Notification → recipient;
- Grade export → Course + requester.

The schema intentionally does **not** pretend that an FK alone is authorization. Every request must still perform deny-by-default permission checks.

## 4. Historical consistency strategy

### Question

`questions` is identity. `question_revisions` is historical content. A used revision is immutable.

### Assessment

Assessment maps to Question identity, not a permanently pinned revision, because the confirmed rule says a Student who has not started receives the latest approved revision.

### Attempt

At start time the system freezes:

- selected Question;
- revision source;
- exact rendered question text;
- exact choice text/order;
- question order;
- assigned points;
- deadline.

That Attempt snapshot is the evidence of what the Student actually experienced.

### Corrections

- answer-only correction → regrade eligible submitted attempts against the new approved answer key;
- content/choice correction → eligible attempts started before the correction effective time receive full credit for that question;
- old answers and snapshots are never rewritten.

## 5. Enrollment retention strategy

One `enrollments` row represents the logical User-Course relationship.

`enrollment_periods` separates each active learning period so re-enroll can restart from zero without overwriting previous detail. A period left for more than 30 days may have its detail purged. `course_completion_summaries` survives and protects:

- ever-completed status;
- prerequisite eligibility;
- final aggregate result if needed;
- completion date.

Purged periods are excluded from future regrading.

## 6. File architecture

The schema intentionally separates:

- `file_blobs`: physical deduplicated bytes by SHA-256;
- `file_assets`: logical application-level file identity;
- `file_revisions`: each upload/replacement;
- `lesson_resources` / `question_revision_resources`: authorized logical references;
- `file_scan_results`: security evidence.

This allows two Lessons to reference identical bytes without coupling their lifecycle.

## 7. AI/RAG architecture

SQL Server stores:

- source identity;
- source version;
- authorization metadata;
- indexing status;
- chunk → vector key mapping;
- AI request usage/security metadata;
- source version used by a response.

It does not need to be the vector store. Embeddings can be held by a replaceable vector component.

Raw AI chat is intentionally short-lived (5 minutes inactivity). Security/audit metadata excludes raw conversation text.

## 8. Background processing

A small `background_jobs` table centralizes mechanics common to retryable work:

- claiming;
- retry count;
- next available time;
- lease expiry;
- dedupe key.

Complex domain workflows keep their own normalized state:

- `regrade_jobs` / `regrade_items`;
- `document_import_jobs` / `import_questions`;
- `knowledge_versions`;
- `email_deliveries`;
- `backup_runs`;
- `grade_exports`.

This is deliberately not a generic workflow engine.

## 9. Derived/cache data

| Derived field/table | Source of truth | Recompute/invalidation |
|---|---|---|
| `enrollments.current_progress_percent` | LessonProgress + required AssessmentResult | recompute after completion/result/rule change |
| `questions.usage_count`, `last_used_at` | AttemptQuestion assignment | update when attempt generated; periodic repair possible |
| `analytics_snapshots` | normalized learning/assessment tables | refresh on event/schedule |
| file `reference_count` | FileRevision references | transactional update + reconciliation job |
| health snapshots | live health probes | short retention; not business truth |

## 10. Delete philosophy

- Broad cascading delete is forbidden for historical learning/assessment data.
- CASCADE is only suitable for disposable children when their parent itself is legally hard-deletable.
- Soft-delete/trash + recovery is used for Course/Lesson/Question/Assessment where applicable.
- Historical tombstones remain for entities that Student activity referenced.
- User deletion begins with disable/deactivate; anonymization preserves foreign-key integrity.

## 11. Availability and failure philosophy

- external email/Gemini/file scan work is not part of the same synchronous commit unless correctness requires it;
- unsafe file cannot be activated if the scanner is unavailable;
- email failure does not rollback the approved business action;
- regrade/import/indexing is resumable and idempotent;
- audit failure **does** block a sensitive action when that audit record is mandatory;
- database restore is always explicit Admin action.

## 12. Table count and scope

The reference model has roughly seventy narrowly scoped relational tables. This number comes from historical, retry, security and import requirements, not from abstract layering. The implementation may omit a table only if the same business invariant is preserved and the decision is documented.
