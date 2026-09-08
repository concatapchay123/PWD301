/*
PWD301 Database Architecture — Reference DDL
Engine: Microsoft SQL Server
All DATETIME2 values are UTC by application convention.
This is reference architecture, not evidence that migrations have been executed.
*/
SET XACT_ABORT ON;
GO


/* Query-driven indexes; filtered indexes are SQL Server's partial-index equivalent. */

CREATE INDEX ix_users_status ON users (status, id);
GO

CREATE INDEX ix_user_roles_role ON user_roles (role_id, user_id);
GO

CREATE INDEX ix_auth_sessions_user_active ON auth_sessions (user_id, expires_at) WHERE revoked_at IS NULL;
GO

CREATE INDEX ix_jwt_user_active ON jwt_token_grants (user_id, expires_at) WHERE revoked_at IS NULL;
GO

CREATE INDEX ix_jwt_family ON jwt_token_grants (session_family_id, issued_at);
GO

CREATE INDEX ix_security_tokens_user_purpose ON user_security_tokens (user_id, purpose, expires_at);
GO

CREATE INDEX ix_instructor_app_status ON instructor_applications (status, created_at);
GO

CREATE INDEX ix_security_events_type_time ON security_events (event_type, created_at);
GO

CREATE INDEX ix_security_events_user_time ON security_events (user_id, created_at);
GO

CREATE INDEX ix_courses_catalog ON courses (status, category, difficulty, title);
GO

CREATE INDEX ix_courses_owner ON courses (owner_instructor_id, status);
GO

CREATE INDEX ix_course_prereq_reverse ON course_prerequisites (prerequisite_course_id, course_id);
GO

CREATE INDEX ix_course_changes_pending ON course_change_requests (status, created_at) WHERE status='PENDING';
GO

CREATE INDEX ix_course_changes_course ON course_change_requests (course_id, created_at);
GO

CREATE INDEX ix_lessons_course_status_position ON lessons (course_id, status, position);
GO

CREATE INDEX ix_enrollments_course_status ON enrollments (course_id, status, student_user_id);
GO

CREATE INDEX ix_enrollments_student_status ON enrollments (student_user_id, status, course_id);
GO

CREATE INDEX ix_enrollments_retention ON enrollments (detail_retention_due_at, status) WHERE detail_retention_due_at IS NOT NULL;
GO

CREATE INDEX ix_enrollment_periods_retention ON enrollment_periods (retention_due_at, status) WHERE retention_due_at IS NOT NULL;
GO

CREATE INDEX ix_enrollment_periods_enrollment ON enrollment_periods (enrollment_id, period_no);
GO

CREATE UNIQUE INDEX ux_enrollment_period_active ON enrollment_periods (enrollment_id) WHERE status='ACTIVE';
GO

CREATE INDEX ix_enrollment_events_enrollment ON enrollment_events (enrollment_id, created_at);
GO

CREATE INDEX ix_lesson_progress_period_complete ON lesson_progress (enrollment_period_id, completed_at);
GO

CREATE INDEX ix_completion_summary_student ON course_completion_summaries (student_user_id, prerequisite_eligible, course_id);
GO

CREATE INDEX ix_questions_bank_filter ON questions (course_id, lesson_id, difficulty, status, id);
GO

CREATE INDEX ix_questions_usage ON questions (course_id, last_used_at, usage_count);
GO

CREATE INDEX ix_question_revisions_question ON question_revisions (question_id, revision_no);
GO

CREATE INDEX ix_question_revisions_exposure ON question_revisions (was_student_exposed, was_used_for_grading);
GO

CREATE INDEX ix_question_choices_revision ON question_revision_choices (question_revision_id, position);
GO

CREATE INDEX ix_accepted_answers_revision ON question_revision_accepted_answers (question_revision_id, position);
GO

CREATE INDEX ix_question_provenance_question ON question_provenance (question_id, created_at);
GO

CREATE INDEX ix_question_provenance_source ON question_provenance (source_type, created_at);
GO

CREATE INDEX ix_assessments_course_status ON assessments (course_id, status, open_at, close_at);
GO

CREATE INDEX ix_assessments_pending_window ON assessments (status, open_at, close_at);
GO

CREATE INDEX ix_assessment_sections ON assessment_sections (assessment_id, position);
GO

CREATE INDEX ix_assessment_assignments_position ON assessment_question_assignments (assessment_id, position);
GO

CREATE INDEX ix_blueprints_assessment ON assessment_blueprints (assessment_id, status);
GO

CREATE INDEX ix_blueprint_rules_filter ON assessment_blueprint_rules (blueprint_id, lesson_id, difficulty, question_type);
GO

CREATE INDEX ix_assessment_pool_rule ON assessment_question_pool (assessment_id, blueprint_rule_id, is_fixed, question_id);
GO

CREATE INDEX ix_attempts_student_assessment ON assessment_attempts (student_user_id, assessment_id, attempt_number);
GO

CREATE INDEX ix_attempts_assessment_status ON assessment_attempts (assessment_id, status, started_at);
GO

CREATE INDEX ix_attempts_period_status ON assessment_attempts (enrollment_period_id, status);
GO

CREATE INDEX ix_attempts_lease_expiry ON assessment_attempts (lease_expires_at, status) WHERE status='IN_PROGRESS';
GO

CREATE UNIQUE INDEX ux_attempt_submit_key ON assessment_attempts (submission_idempotency_key) WHERE submission_idempotency_key IS NOT NULL;
GO

CREATE INDEX ix_attempt_questions_attempt ON attempt_questions (attempt_id, position);
GO

CREATE INDEX ix_attempt_questions_source ON attempt_questions (source_question_id, attempt_id);
GO

CREATE INDEX ix_attempt_questions_revision ON attempt_questions (source_question_revision_id, attempt_id);
GO

CREATE INDEX ix_attempt_choice_question ON attempt_choice_snapshots (attempt_question_id, position);
GO

CREATE INDEX ix_attempt_answers_saved ON attempt_answers (saved_at, attempt_question_id);
GO

CREATE INDEX ix_attempt_answer_choices_choice ON attempt_answer_choices (attempt_choice_snapshot_id, attempt_answer_id);
GO

CREATE INDEX ix_answer_events_question_time ON attempt_answer_events (attempt_question_id, received_at);
GO

CREATE INDEX ix_answer_events_cleanup ON attempt_answer_events (received_at, accepted);
GO

CREATE INDEX ix_question_grades_pending ON attempt_question_grades (grading_status, graded_at) WHERE grading_status='PENDING';
GO

CREATE INDEX ix_grade_history_question ON attempt_question_grade_history (attempt_question_id, created_at);
GO

CREATE INDEX ix_results_status ON assessment_results (status, released_at);
GO

CREATE INDEX ix_results_percent ON assessment_results (percent_score, attempt_id);
GO

CREATE INDEX ix_result_history_attempt ON assessment_result_history (attempt_id, created_at);
GO

CREATE INDEX ix_question_corrections_question_time ON question_corrections (question_id, effective_at);
GO

CREATE INDEX ix_question_corrections_status ON question_corrections (status, created_at);
GO

CREATE INDEX ix_regrade_jobs_status ON regrade_jobs (status, created_at);
GO

CREATE INDEX ix_regrade_items_claim ON regrade_items (regrade_job_id, status, id);
GO

CREATE INDEX ix_regrade_items_attempt ON regrade_items (attempt_id, regrade_job_id);
GO

CREATE INDEX ix_file_blobs_status_ref ON file_blobs (status, reference_count, created_at);
GO

CREATE INDEX ix_file_assets_course_status ON file_assets (course_id, status, asset_type);
GO

CREATE UNIQUE INDEX ux_file_revisions_active ON file_revisions (file_asset_id) WHERE status = 'ACTIVE';
GO

CREATE INDEX ix_file_revisions_asset ON file_revisions (file_asset_id, revision_no);
GO

CREATE INDEX ix_file_revisions_processing ON file_revisions (status, created_at);
GO

CREATE INDEX ix_file_revisions_recovery ON file_revisions (recovery_until, status) WHERE recovery_until IS NOT NULL;
GO

CREATE INDEX ix_file_scan_revision_type ON file_scan_results (file_revision_id, scan_type, created_at);
GO

CREATE INDEX ix_file_scan_failures ON file_scan_results (status, created_at);
GO

CREATE INDEX ix_lesson_resources_lesson ON lesson_resources (lesson_id, position);
GO

CREATE INDEX ix_question_resources_revision ON question_revision_resources (question_revision_id, position);
GO

CREATE INDEX ix_import_jobs_course_status ON document_import_jobs (course_id, status, created_at);
GO

CREATE INDEX ix_import_jobs_status ON document_import_jobs (status, created_at);
GO

CREATE INDEX ix_import_questions_review ON import_questions (import_job_id, review_state, ordinal);
GO

CREATE INDEX ix_import_duplicates_question ON import_duplicate_candidates (import_question_id, decision);
GO

CREATE INDEX ix_import_question_resources ON import_question_resources (import_question_id, position);
GO

CREATE INDEX ix_ai_conversations_expiry ON ai_conversations (expires_at, status);
GO

CREATE INDEX ix_ai_conversations_user ON ai_conversations (user_id, status, last_activity_at);
GO

CREATE INDEX ix_ai_messages_conversation ON ai_messages (conversation_id, sequence_no);
GO

CREATE INDEX ix_ai_requests_user_time ON ai_requests (user_id, created_at);
GO

CREATE INDEX ix_ai_requests_status_time ON ai_requests (status, created_at);
GO

CREATE INDEX ix_ai_drafts_review ON ai_generated_question_drafts (course_id, review_state, created_at);
GO

CREATE INDEX ix_knowledge_docs_course_status ON knowledge_documents (course_id, status, source_type);
GO

CREATE UNIQUE INDEX ux_knowledge_versions_active ON knowledge_versions (knowledge_document_id) WHERE status = 'ACTIVE';
GO

CREATE INDEX ix_knowledge_versions_doc ON knowledge_versions (knowledge_document_id, version_no);
GO

CREATE INDEX ix_knowledge_versions_status ON knowledge_versions (status, created_at);
GO

CREATE INDEX ix_knowledge_chunks_version ON knowledge_chunks (knowledge_version_id, chunk_no);
GO

CREATE INDEX ix_ai_source_request ON ai_source_usages (ai_request_id, rank_no);
GO

CREATE INDEX ix_ai_source_version ON ai_source_usages (knowledge_version_id, created_at);
GO

CREATE INDEX ix_notification_events_type_time ON notification_events (event_type, created_at);
GO

CREATE INDEX ix_notifications_user_unread ON notifications (recipient_user_id, created_at) WHERE read_at IS NULL;
GO

CREATE INDEX ix_notifications_expiry ON notifications (expires_at, id) WHERE expires_at IS NOT NULL;
GO

CREATE INDEX ix_email_delivery_queue ON email_deliveries (status, next_attempt_at, id);
GO

CREATE INDEX ix_email_delivery_event ON email_deliveries (notification_event_id, status);
GO

CREATE INDEX ix_audit_time ON audit_events (created_at, id);
GO

CREATE INDEX ix_audit_actor_time ON audit_events (actor_user_id, created_at);
GO

CREATE INDEX ix_audit_target ON audit_events (target_type, target_id, created_at);
GO

CREATE INDEX ix_audit_action_time ON audit_events (action, created_at);
GO

CREATE INDEX ix_jobs_claim ON background_jobs (status, available_at, priority, id);
GO

CREATE UNIQUE INDEX ux_jobs_dedupe ON background_jobs (job_type, dedupe_key) WHERE dedupe_key IS NOT NULL;
GO

CREATE INDEX ix_system_alerts_open ON system_alerts (status, severity, created_at);
GO

CREATE INDEX ix_system_alerts_type ON system_alerts (alert_type, created_at);
GO

CREATE INDEX ix_backup_runs_time ON backup_runs (started_at, status);
GO

CREATE INDEX ix_grade_exports_user ON grade_exports (requested_by_user_id, status, created_at);
GO

CREATE INDEX ix_grade_exports_expiry ON grade_exports (expires_at, status);
GO

CREATE INDEX ix_analytics_scope_metric ON analytics_snapshots (scope_type, scope_id, metric_code, as_of_at);
GO

CREATE INDEX ix_health_component_time ON system_health_snapshots (component, created_at);
GO
