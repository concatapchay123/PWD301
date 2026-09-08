# Index and Performance Strategy

## 1. Principles

1. Primary keys are clustered by default unless migration profiling shows a better choice.
2. Foreign keys that are frequent join/filter paths receive explicit nonclustered indexes when not already covered.
3. Filtered indexes are used for small active queues: unread notifications, active sessions, pending retention, job queues.
4. Pagination is server/database-backed. No route should load an unbounded Question Bank, Course Catalog, Attempt list, Audit Log or Notification list into the browser.
5. Avoid indexing large `NVARCHAR(MAX)`/JSON bodies. Search text requiring richer full-text behavior can later use SQL Server Full-Text Search; MVP filters rely on metadata + bounded text search.
6. Every extra index adds write cost. High-write tables such as `attempt_answer_events` and `background_jobs` intentionally have only the indexes needed for resume/cleanup/claim.
7. `ROWVERSION` is for conflict detection, not search.

## 2. Pagination patterns

### Course Catalog

Prefer stable keyset pagination for large data:

```sql
WHERE status = 'PUBLISHED'
  AND (title > @after_title OR (title = @after_title AND id > @after_id))
ORDER BY title, id
```

Offset pagination is acceptable for normal admin pages at project scale, but queries must always have a deterministic secondary order by PK.

### Question Bank

Core filters:
- `course_id`;
- optional `lesson_id`;
- `difficulty`;
- current status;
- provenance;
- used/unused via `first_used_at`/usage metadata;
- current type by join to `current_revision_id`.

If free-text content search becomes a bottleneck, add SQL Server Full-Text Search to current revision content rather than an unbounded `%LIKE%` scan.

### Attempts / pending grading

Query by Assessment/Course + status + started/graded time. Pending essay grading uses the filtered `attempt_question_grades` index.

### Audit

Append volume is write-heavy. Use composite indexes only for:
- chronological Admin page;
- actor history;
- target history;
- action type/time.

Old audit rows may move to archive storage; do not add dozens of ad-hoc audit indexes.

## 3. Regrade target lookup

The worker starts from `attempt_questions.source_question_id`, joins Attempt → EnrollmentPeriod, and excludes `detail_purged_at IS NOT NULL`.

Expected shape:

```sql
SELECT aq.id, a.id
FROM attempt_questions aq
JOIN assessment_attempts a ON a.id = aq.attempt_id
JOIN enrollment_periods ep ON ep.id = a.enrollment_period_id
WHERE aq.source_question_id = @question_id
  AND ep.detail_purged_at IS NULL
  AND a.status IN ('SUBMITTED','EXPIRED','PENDING_GRADING','GRADED');
```

`ix_attempt_questions_source`, attempt status indexes and period status/retention indexes support this path.

## 4. Analytics

Dashboard queries that scan many answers/attempts should not run synchronously on every page load. `analytics_snapshots` stores recomputable aggregates.

Invalidation strategy:
- enrollment/completion event → mark Course metrics stale or queue refresh;
- grading/regrade completion → refresh Assessment/Course metrics;
- Question correction → refresh difficult-question metrics after regrade;
- nightly reconciliation can repair missed invalidations.

## 5. Progress cache

`enrollments.current_progress_percent` is a derived value.

Source of truth:
- `lesson_progress`;
- required `assessment_results`;
- `course_completion_rules`;
- Lesson effective-required timestamp.

Update after relevant transaction, but provide a recompute service. Never accept the percentage directly from browser input.

## 6. Question usage counters

`questions.usage_count` and `last_used_at` are selection hints for “prefer less recently used questions.”

Source of truth: `attempt_questions`.

The Attempt start transaction increments these counters after successful snapshot generation. A maintenance query can recompute them, therefore a crash cannot corrupt grading.

## 7. File dedup performance

`file_blobs.sha256` unique allows hash lookup before physical copy promotion. The application must still verify that the hash corresponds to the fully received bytes; never trust client-supplied hash alone.

## 8. Queue performance

Worker queries use narrow indexes:
- status;
- `available_at` / `next_attempt_at`;
- priority;
- numeric PK.

Claim small batches, never `SELECT` the whole queue.

## 9. Index inventory

| Table | Index | Columns | Type | Query supported | Reason |
|---|---|---|---|---|---|
| `users` | `ix_users_status` | `status, id` | NONCLUSTERED | status queues/lists | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `user_roles` | `ix_user_roles_role` | `role_id, user_id` | NONCLUSTERED | user-scoped lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `auth_sessions` | `ix_auth_sessions_user_active` | `user_id, expires_at` | FILTERED | user-scoped lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. Filter keeps index small and write cost lower. |
| `jwt_token_grants` | `ix_jwt_user_active` | `user_id, expires_at` | FILTERED | user-scoped lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. Filter keeps index small and write cost lower. |
| `jwt_token_grants` | `ix_jwt_family` | `session_family_id, issued_at` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `user_security_tokens` | `ix_security_tokens_user_purpose` | `user_id, purpose, expires_at` | NONCLUSTERED | user-scoped lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `instructor_applications` | `ix_instructor_app_status` | `status, created_at` | NONCLUSTERED | status queues/lists | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `security_events` | `ix_security_events_type_time` | `event_type, created_at` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `security_events` | `ix_security_events_user_time` | `user_id, created_at` | NONCLUSTERED | user-scoped lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `courses` | `ix_courses_catalog` | `status, category, difficulty, title` | NONCLUSTERED | Course Catalog | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `courses` | `ix_courses_owner` | `owner_instructor_id, status` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `course_prerequisites` | `ix_course_prereq_reverse` | `prerequisite_course_id, course_id` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `course_change_requests` | `ix_course_changes_pending` | `status, created_at` | FILTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. Filter keeps index small and write cost lower. |
| `course_change_requests` | `ix_course_changes_course` | `course_id, created_at` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `lessons` | `ix_lessons_course_status_position` | `course_id, status, position` | NONCLUSTERED | status queues/lists | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `enrollments` | `ix_enrollments_course_status` | `course_id, status, student_user_id` | NONCLUSTERED | status queues/lists | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `enrollments` | `ix_enrollments_student_status` | `student_user_id, status, course_id` | NONCLUSTERED | status queues/lists | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `enrollments` | `ix_enrollments_retention` | `detail_retention_due_at, status` | FILTERED | retention/cleanup batch | Matches leading filter/order columns; avoids full scans on expected high-volume path. Filter keeps index small and write cost lower. |
| `enrollment_periods` | `ix_enrollment_periods_retention` | `retention_due_at, status` | FILTERED | retention/cleanup batch | Matches leading filter/order columns; avoids full scans on expected high-volume path. Filter keeps index small and write cost lower. |
| `enrollment_periods` | `ix_enrollment_periods_enrollment` | `enrollment_id, period_no` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `enrollment_periods` | `ux_enrollment_period_active` | `enrollment_id` | UNIQUE FILTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. Filter keeps index small and write cost lower. |
| `enrollment_events` | `ix_enrollment_events_enrollment` | `enrollment_id, created_at` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `lesson_progress` | `ix_lesson_progress_period_complete` | `enrollment_period_id, completed_at` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `course_completion_summaries` | `ix_completion_summary_student` | `student_user_id, prerequisite_eligible, course_id` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `questions` | `ix_questions_bank_filter` | `course_id, lesson_id, difficulty, status, id` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `questions` | `ix_questions_usage` | `course_id, last_used_at, usage_count` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `question_revisions` | `ix_question_revisions_question` | `question_id, revision_no` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `question_revisions` | `ix_question_revisions_exposure` | `was_student_exposed, was_used_for_grading` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `question_revision_choices` | `ix_question_choices_revision` | `question_revision_id, position` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `question_revision_accepted_answers` | `ix_accepted_answers_revision` | `question_revision_id, position` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `question_provenance` | `ix_question_provenance_question` | `question_id, created_at` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `question_provenance` | `ix_question_provenance_source` | `source_type, created_at` | NONCLUSTERED | source/provenance lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `assessments` | `ix_assessments_course_status` | `course_id, status, open_at, close_at` | NONCLUSTERED | status queues/lists | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `assessments` | `ix_assessments_pending_window` | `status, open_at, close_at` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `assessment_sections` | `ix_assessment_sections` | `assessment_id, position` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `assessment_question_assignments` | `ix_assessment_assignments_position` | `assessment_id, position` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `assessment_blueprints` | `ix_blueprints_assessment` | `assessment_id, status` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `assessment_blueprint_rules` | `ix_blueprint_rules_filter` | `blueprint_id, lesson_id, difficulty, question_type` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `assessment_question_pool` | `ix_assessment_pool_rule` | `assessment_id, blueprint_rule_id, is_fixed, question_id` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `assessment_attempts` | `ix_attempts_student_assessment` | `student_user_id, assessment_id, attempt_number` | NONCLUSTERED | attempt lookup/history | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `assessment_attempts` | `ix_attempts_assessment_status` | `assessment_id, status, started_at` | NONCLUSTERED | attempt lookup/history | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `assessment_attempts` | `ix_attempts_period_status` | `enrollment_period_id, status` | NONCLUSTERED | attempt lookup/history | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `assessment_attempts` | `ix_attempts_lease_expiry` | `lease_expires_at, status` | FILTERED | retention/cleanup batch | Matches leading filter/order columns; avoids full scans on expected high-volume path. Filter keeps index small and write cost lower. |
| `assessment_attempts` | `ux_attempt_submit_key` | `submission_idempotency_key` | UNIQUE FILTERED | attempt lookup/history | Matches leading filter/order columns; avoids full scans on expected high-volume path. Filter keeps index small and write cost lower. |
| `attempt_questions` | `ix_attempt_questions_attempt` | `attempt_id, position` | NONCLUSTERED | attempt lookup/history | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `attempt_questions` | `ix_attempt_questions_source` | `source_question_id, attempt_id` | NONCLUSTERED | attempt lookup/history | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `attempt_questions` | `ix_attempt_questions_revision` | `source_question_revision_id, attempt_id` | NONCLUSTERED | attempt lookup/history | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `attempt_choice_snapshots` | `ix_attempt_choice_question` | `attempt_question_id, position` | NONCLUSTERED | attempt lookup/history | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `attempt_answers` | `ix_attempt_answers_saved` | `saved_at, attempt_question_id` | NONCLUSTERED | attempt lookup/history | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `attempt_answer_choices` | `ix_attempt_answer_choices_choice` | `attempt_choice_snapshot_id, attempt_answer_id` | NONCLUSTERED | attempt lookup/history | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `attempt_answer_events` | `ix_answer_events_question_time` | `attempt_question_id, received_at` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `attempt_answer_events` | `ix_answer_events_cleanup` | `received_at, accepted` | NONCLUSTERED | retention/cleanup batch | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `attempt_question_grades` | `ix_question_grades_pending` | `grading_status, graded_at` | FILTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. Filter keeps index small and write cost lower. |
| `attempt_question_grade_history` | `ix_grade_history_question` | `attempt_question_id, created_at` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `assessment_results` | `ix_results_status` | `status, released_at` | NONCLUSTERED | status queues/lists | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `assessment_results` | `ix_results_percent` | `percent_score, attempt_id` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `assessment_result_history` | `ix_result_history_attempt` | `attempt_id, created_at` | NONCLUSTERED | attempt lookup/history | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `question_corrections` | `ix_question_corrections_question_time` | `question_id, effective_at` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `question_corrections` | `ix_question_corrections_status` | `status, created_at` | NONCLUSTERED | status queues/lists | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `regrade_jobs` | `ix_regrade_jobs_status` | `status, created_at` | NONCLUSTERED | regrade target/progress | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `regrade_items` | `ix_regrade_items_claim` | `regrade_job_id, status, id` | NONCLUSTERED | worker claim queue | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `regrade_items` | `ix_regrade_items_attempt` | `attempt_id, regrade_job_id` | NONCLUSTERED | regrade target/progress | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `file_blobs` | `ix_file_blobs_status_ref` | `status, reference_count, created_at` | NONCLUSTERED | status queues/lists | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `file_assets` | `ix_file_assets_course_status` | `course_id, status, asset_type` | NONCLUSTERED | status queues/lists | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `file_revisions` | `ux_file_revisions_active` | `file_asset_id` | Filtered unique | current revision activation | Enforces one ACTIVE logical file revision per asset. |
| `file_revisions` | `ix_file_revisions_asset` | `file_asset_id, revision_no` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `file_revisions` | `ix_file_revisions_processing` | `status, created_at` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `file_revisions` | `ix_file_revisions_recovery` | `recovery_until, status` | FILTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. Filter keeps index small and write cost lower. |
| `file_scan_results` | `ix_file_scan_revision_type` | `file_revision_id, scan_type, created_at` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `file_scan_results` | `ix_file_scan_failures` | `status, created_at` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `lesson_resources` | `ix_lesson_resources_lesson` | `lesson_id, position` | NONCLUSTERED | source/provenance lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `question_revision_resources` | `ix_question_resources_revision` | `question_revision_id, position` | NONCLUSTERED | source/provenance lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `document_import_jobs` | `ix_import_jobs_course_status` | `course_id, status, created_at` | NONCLUSTERED | status queues/lists | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `document_import_jobs` | `ix_import_jobs_status` | `status, created_at` | NONCLUSTERED | status queues/lists | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `import_questions` | `ix_import_questions_review` | `import_job_id, review_state, ordinal` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `import_duplicate_candidates` | `ix_import_duplicates_question` | `import_question_id, decision` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `import_question_resources` | `ix_import_question_resources` | `import_question_id, position` | NONCLUSTERED | source/provenance lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `ai_conversations` | `ix_ai_conversations_expiry` | `expires_at, status` | NONCLUSTERED | retention/cleanup batch | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `ai_conversations` | `ix_ai_conversations_user` | `user_id, status, last_activity_at` | NONCLUSTERED | user-scoped lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `ai_messages` | `ix_ai_messages_conversation` | `conversation_id, sequence_no` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `ai_requests` | `ix_ai_requests_user_time` | `user_id, created_at` | NONCLUSTERED | user-scoped lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `ai_requests` | `ix_ai_requests_status_time` | `status, created_at` | NONCLUSTERED | status queues/lists | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `ai_generated_question_drafts` | `ix_ai_drafts_review` | `course_id, review_state, created_at` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `knowledge_documents` | `ix_knowledge_docs_course_status` | `course_id, status, source_type` | NONCLUSTERED | status queues/lists | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `knowledge_versions` | `ux_knowledge_versions_active` | `knowledge_document_id` | Filtered unique | RAG version activation | Enforces one ACTIVE searchable version per knowledge document. |
| `knowledge_versions` | `ix_knowledge_versions_doc` | `knowledge_document_id, version_no` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `knowledge_versions` | `ix_knowledge_versions_status` | `status, created_at` | NONCLUSTERED | status queues/lists | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `knowledge_chunks` | `ix_knowledge_chunks_version` | `knowledge_version_id, chunk_no` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `ai_source_usages` | `ix_ai_source_request` | `ai_request_id, rank_no` | NONCLUSTERED | source/provenance lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `ai_source_usages` | `ix_ai_source_version` | `knowledge_version_id, created_at` | NONCLUSTERED | source/provenance lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `notification_events` | `ix_notification_events_type_time` | `event_type, created_at` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `notifications` | `ix_notifications_user_unread` | `recipient_user_id, created_at` | FILTERED | recipient unread notifications | Matches leading filter/order columns; avoids full scans on expected high-volume path. Filter keeps index small and write cost lower. |
| `notifications` | `ix_notifications_expiry` | `expires_at, id` | FILTERED | retention/cleanup batch | Matches leading filter/order columns; avoids full scans on expected high-volume path. Filter keeps index small and write cost lower. |
| `email_deliveries` | `ix_email_delivery_queue` | `status, next_attempt_at, id` | NONCLUSTERED | worker claim queue | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `email_deliveries` | `ix_email_delivery_event` | `notification_event_id, status` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `audit_events` | `ix_audit_time` | `created_at, id` | NONCLUSTERED | Audit Log pagination/filter | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `audit_events` | `ix_audit_actor_time` | `actor_user_id, created_at` | NONCLUSTERED | Audit Log pagination/filter | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `audit_events` | `ix_audit_target` | `target_type, target_id, created_at` | NONCLUSTERED | Audit Log pagination/filter | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `audit_events` | `ix_audit_action_time` | `action, created_at` | NONCLUSTERED | Audit Log pagination/filter | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `background_jobs` | `ix_jobs_claim` | `status, available_at, priority, id` | NONCLUSTERED | worker claim queue | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `background_jobs` | `ux_jobs_dedupe` | `job_type, dedupe_key` | UNIQUE FILTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. Filter keeps index small and write cost lower. |
| `system_alerts` | `ix_system_alerts_open` | `status, severity, created_at` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `system_alerts` | `ix_system_alerts_type` | `alert_type, created_at` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `backup_runs` | `ix_backup_runs_time` | `started_at, status` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `grade_exports` | `ix_grade_exports_user` | `requested_by_user_id, status, created_at` | NONCLUSTERED | user-scoped lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `grade_exports` | `ix_grade_exports_expiry` | `expires_at, status` | NONCLUSTERED | retention/cleanup batch | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `analytics_snapshots` | `ix_analytics_scope_metric` | `scope_type, scope_id, metric_code, as_of_at` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |
| `system_health_snapshots` | `ix_health_component_time` | `component, created_at` | NONCLUSTERED | filter/pagination/lookup | Matches leading filter/order columns; avoids full scans on expected high-volume path. |

## 10. Write-cost review

### High-write tables

- `attempt_answers`;
- `attempt_answer_events`;
- `auth_sessions.last_seen_at`;
- `background_jobs`;
- `email_deliveries`;
- `lesson_progress`.

For these tables:
- avoid redundant single-column indexes already covered by composites;
- batch/limit session last-seen writes rather than writing every HTTP request;
- cleanup short-retention event rows in bounded batches;
- keep JSON payload small.

### Moderate-write tables

Question revisions, attempts, grade histories and audit are append-heavy but not autosave-frequency. Indexes prioritize traceability and regrade queries.

### Low-write/read-heavy tables

Courses, Lessons, Assessments, roles and completion rules can afford richer filter indexes.

## 11. Query-review gate

Before adding a new index, capture:
1. the exact query;
2. estimated/actual plan;
3. rows read vs returned;
4. current index coverage;
5. write frequency of the table.

Do not create an index solely because a column “might be searched someday.”
