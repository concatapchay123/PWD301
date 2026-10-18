# SYSTEM INVENTORY & TEST COVERAGE BASELINE

- **Backend HTTP Endpoints:** 432
- **Database Model Tables:** 77
- **Frontend SPA Routes:** 30
- **Platform Architecture:** Pure Headless REST API + Single-Page Application (SPA)

## 1. Frontend Route Inventory

| Route Path | Minimum Role | Functionality & View Description |
|---|---|---|
| `#/auth` | `ANONYMOUS` | Login / Registration Form (Email, Password, Roles) |
| `#/student/dashboard` | `STUDENT` | Student Learning Dashboard & Enrolled Courses |
| `#/student/catalog` | `STUDENT` | Course Catalog & Discovery |
| `#/student/courses` | `STUDENT` | My Learning View & Course Progress |
| `#/student/courses/:id/intro` | `STUDENT` | Course Overview, Syllabus, Prerequisites |
| `#/student/courses/:id` | `STUDENT` | Course Study Console & Outline |
| `#/student/courses/:id/lessons/:lesson_id` | `STUDENT` | Interactive Lesson Reader, 16:9 Video & DRM |
| `#/student/assessments` | `STUDENT` | Student Assessment Schedule & Exam List |
| `#/student/assessments/:id/waiting-room` | `STUDENT` | Exam Waiting Room & Prerequisite Verification |
| `#/student/assessments/attempts/:id` | `STUDENT` | Fullscreen Exam Focus Mode & Autosave Leases |
| `#/student/assessments/attempts/:id/results` | `STUDENT` | Exam Results, Breakdown & Review |
| `#/student/ai-assistant` | `STUDENT` | Octopus AI Assistant RAG Chat |
| `#/student/become-instructor` | `STUDENT` | Instructor Application Form & File Upload |
| `#/student/settings` | `ALL` | User Profile, Password Change & Preferences |
| `#/instructor/dashboard` | `INSTRUCTOR` | Instructor Overview & Course Workload |
| `#/instructor/courses` | `INSTRUCTOR` | Instructor Managed Courses List |
| `#/instructor/courses/:id/manage` | `INSTRUCTOR` | Single-Page Studio, Curriculum & Staging Draft |
| `#/instructor/prerequisites/requests` | `INSTRUCTOR` | Prerequisite Course Linking Approval |
| `#/instructor/exams/hub` | `INSTRUCTOR` | Question Bank & Exam Management Hub |
| `#/instructor/exams/editor` | `INSTRUCTOR` | Step 2: Manual Question Authoring |
| `#/instructor/exams/interactive` | `INSTRUCTOR` | Step 2: Interactive Question Builder |
| `#/instructor/exams/excel` | `INSTRUCTOR` | Step 2: Excel Bulk Exam Import (.xlsx) |
| `#/instructor/exams/moodle` | `INSTRUCTOR` | Step 2: Moodle XML Exam Import (.xml) |
| `#/instructor/exams/matrix` | `INSTRUCTOR` | Step 3: Bloom Taxonomy Matrix & Grading Spec |
| `#/instructor/exams/settings` | `INSTRUCTOR` | Step 4: Scheduling, Timing & Publish Controls |
| `#/instructor/exams/results` | `INSTRUCTOR` | Assessment Submissions, Grading & PDF Export |
| `#/admin/governance` | `ADMIN` | Admin Governance (Users, Courses, Apps, Security) |
| `#/admin/courses/review` | `ADMIN` | Initial Course Submission Review Pane |
| `#/admin/change-requests/review` | `ADMIN` | Staging Draft Changeset Diff Modal & Approval |
| `#/admin/operations` | `ADMIN` | System Telemetry, Backups, Health & Logs |

## 2. Database Models & Tables Inventory

| Table Name | Column Count | Domain |
|---|---|---|
| `ai_conversations` | 11 cols | AI & RAG |
| `ai_generated_question_drafts` | 19 cols | Assessment & Exams |
| `ai_messages` | 6 cols | AI & RAG |
| `ai_requests` | 15 cols | AI & RAG |
| `ai_source_usages` | 7 cols | AI & RAG |
| `analytics_snapshots` | 9 cols | Operations & Audit |
| `assessment_attempts` | 25 cols | Assessment & Exams |
| `assessment_blueprint_rules` | 9 cols | Assessment & Exams |
| `assessment_blueprints` | 7 cols | Assessment & Exams |
| `assessment_question_assignments` | 10 cols | Assessment & Exams |
| `assessment_question_pool` | 9 cols | Assessment & Exams |
| `assessment_result_history` | 11 cols | Assessment & Exams |
| `assessment_results` | 10 cols | Assessment & Exams |
| `assessment_sections` | 5 cols | Assessment & Exams |
| `assessments` | 36 cols | Assessment & Exams |
| `attempt_answer_choices` | 2 cols | Assessment & Exams |
| `attempt_answer_events` | 9 cols | Assessment & Exams |
| `attempt_answers` | 8 cols | Assessment & Exams |
| `attempt_choice_snapshots` | 7 cols | Assessment & Exams |
| `attempt_focus_events` | 6 cols | Assessment & Exams |
| `attempt_question_grade_history` | 9 cols | Assessment & Exams |
| `attempt_question_grades` | 9 cols | Assessment & Exams |
| `attempt_questions` | 14 cols | Assessment & Exams |
| `audit_events` | 14 cols | Operations & Audit |
| `auth_sessions` | 12 cols | Identity & RBAC |
| `background_jobs` | 16 cols | Operations & Audit |
| `backup_runs` | 12 cols | Operations & Audit |
| `course_change_requests` | 14 cols | Course & Curriculum |
| `course_completion_rules` | 7 cols | Course & Curriculum |
| `course_completion_summaries` | 11 cols | Course & Curriculum |
| `course_prerequisites` | 10 cols | Course & Curriculum |
| `courses` | 27 cols | Course & Curriculum |
| `document_import_jobs` | 17 cols | Operations & Audit |
| `email_deliveries` | 15 cols | AI & RAG |
| `enrollment_events` | 7 cols | Course & Curriculum |
| `enrollment_periods` | 10 cols | Course & Curriculum |
| `enrollments` | 14 cols | Course & Curriculum |
| `file_assets` | 14 cols | File & Streaming |
| `file_blobs` | 11 cols | File & Streaming |
| `file_revisions` | 19 cols | File & Streaming |
| `file_scan_results` | 10 cols | File & Streaming |
| `grade_exports` | 13 cols | Assessment & Exams |
| `import_duplicate_candidates` | 9 cols | Operations & Audit |
| `import_question_resources` | 6 cols | Assessment & Exams |
| `import_questions` | 20 cols | Assessment & Exams |
| `instructor_applications` | 9 cols | Operations & Audit |
| `jwt_token_grants` | 11 cols | Operations & Audit |
| `knowledge_chunks` | 8 cols | Operations & Audit |
| `knowledge_documents` | 10 cols | Operations & Audit |
| `knowledge_versions` | 15 cols | Operations & Audit |
| `learning_units` | 8 cols | Course & Curriculum |
| `lesson_media_progress` | 8 cols | Course & Curriculum |
| `lesson_progress` | 11 cols | Course & Curriculum |
| `lesson_progress_receipts` | 5 cols | Course & Curriculum |
| `lesson_resources` | 7 cols | Course & Curriculum |
| `lessons` | 24 cols | Course & Curriculum |
| `notification_events` | 9 cols | Operations & Audit |
| `notification_preferences` | 5 cols | Operations & Audit |
| `notifications` | 12 cols | Operations & Audit |
| `playback_receipts` | 6 cols | File & Streaming |
| `playback_sessions` | 13 cols | Identity & RBAC |
| `question_corrections` | 10 cols | Assessment & Exams |
| `question_provenance` | 13 cols | Assessment & Exams |
| `question_revision_accepted_answers` | 5 cols | Assessment & Exams |
| `question_revision_choices` | 7 cols | Assessment & Exams |
| `question_revision_resources` | 6 cols | Assessment & Exams |
| `question_revisions` | 16 cols | Assessment & Exams |
| `questions` | 20 cols | Assessment & Exams |
| `regrade_items` | 11 cols | Assessment & Exams |
| `regrade_jobs` | 12 cols | Assessment & Exams |
| `roles` | 4 cols | Identity & RBAC |
| `security_events` | 11 cols | Operations & Audit |
| `system_alerts` | 12 cols | Operations & Audit |
| `system_health_snapshots` | 6 cols | Operations & Audit |
| `user_roles` | 5 cols | Identity & RBAC |
| `user_security_tokens` | 8 cols | Identity & RBAC |
| `users` | 17 cols | Identity & RBAC |

## 3. Backend HTTP API Endpoints Inventory

| Methods | Route Path | Endpoint Name | Blueprint |
|---|---|---|---|
| `GET` | `/` | `core.index` | `core` |
| `GET` | `/` | `frontend.index` | `frontend` |
| `GET` | `/admin/analytics/overview` | `admin.admin_analytics_overview` | `admin` |
| `GET` | `/admin/assessments/<assessment_id>/gradebook.pdf` | `admin.admin_export_assessment_gradebook_pdf_route` | `admin` |
| `GET` | `/admin/audit-logs` | `admin.list_audit_logs` | `admin` |
| `GET` | `/admin/audit-logs/<audit_id>` | `admin.get_audit_log_by_id` | `admin` |
| `POST` | `/admin/backups` | `admin.admin_create_backup` | `admin` |
| `GET` | `/admin/backups` | `admin.admin_list_backups` | `admin` |
| `GET` | `/admin/backups/<backup_id>` | `admin.admin_get_backup_detail` | `admin` |
| `POST` | `/admin/backups/<backup_id>/restore` | `admin.admin_restore_database` | `admin` |
| `POST` | `/admin/backups/<backup_id>/restore/dry-run` | `admin.admin_dry_run_restore` | `admin` |
| `POST` | `/admin/backups/<backup_id>/verify` | `admin.admin_verify_backup` | `admin` |
| `GET` | `/admin/change-requests` | `admin.admin_list_change_requests` | `admin` |
| `GET` | `/admin/change-requests/<int:req_id>/diff` | `admin.get_course_changeset_diff_route` | `admin` |
| `POST` | `/admin/change-requests/<int:req_id>/review` | `admin.admin_review_change_request` | `admin` |
| `POST` | `/admin/course-changes/<int:req_id>/approve` | `admin.approve_course_changeset_route` | `admin` |
| `GET` | `/admin/course-changes/<int:req_id>/diff` | `admin.get_course_changeset_diff_route` | `admin` |
| `POST` | `/admin/course-changes/<int:req_id>/reject` | `admin.reject_course_changeset_route` | `admin` |
| `GET` | `/admin/courses` | `admin.admin_courses` | `admin` |
| `GET` | `/admin/courses/<course_id>` | `admin.admin_course_detail` | `admin` |
| `GET` | `/admin/courses/<course_id>` | `admin.admin_get_course_detail` | `admin` |
| `POST` | `/admin/courses/<course_id>/changeset/approve` | `admin.approve_course_changeset_route` | `admin` |
| `GET` | `/admin/courses/<course_id>/changeset/diff` | `admin.get_course_changeset_diff_route` | `admin` |
| `POST` | `/admin/courses/<course_id>/changeset/reject` | `admin.reject_course_changeset_route` | `admin` |
| `POST` | `/admin/courses/<course_id>/lessons/<lesson_id>/flag` | `admin.flag_course_lesson` | `admin` |
| `POST` | `/admin/courses/<course_id>/publish` | `admin.publish_course` | `admin` |
| `POST` | `/admin/courses/<course_id>/reassign` | `admin.reassign_course` | `admin` |
| `POST` | `/admin/courses/<course_id>/restore` | `admin.restore_course` | `admin` |
| `POST` | `/admin/courses/<course_id>/review` | `admin.review_course` | `admin` |
| `DELETE, POST` | `/admin/courses/<course_id>/trash` | `admin.trash_course_route` | `admin` |
| `GET` | `/admin/courses/pending` | `admin.list_pending_courses` | `admin` |
| `POST` | `/admin/courses/swap` | `admin.swap_courses` | `admin` |
| `GET` | `/admin/dashboard` | `admin.dashboard` | `admin` |
| `POST` | `/admin/emails/retry-failed` | `admin.admin_retry_failed_emails` | `admin` |
| `GET` | `/admin/faculty/workload` | `admin.admin_faculty_workload` | `admin` |
| `POST` | `/admin/files/<asset_id>/quarantine-override` | `admin.override_file_quarantine` | `admin` |
| `GET` | `/admin/health` | `admin.admin_health` | `admin` |
| `GET` | `/admin/instructor-applications` | `admin.admin_instructor_applications` | `admin` |
| `GET` | `/admin/instructor-applications/<app_id>` | `admin.admin_instructor_application_detail` | `admin` |
| `GET` | `/admin/instructor-applications/<app_id>/evidence/<filename>` | `admin.admin_download_application_evidence` | `admin` |
| `POST` | `/admin/instructor-applications/<app_id>/review` | `admin.admin_review_instructor_application` | `admin` |
| `POST` | `/admin/maintenance/end` | `admin.admin_end_maintenance` | `admin` |
| `POST` | `/admin/maintenance/start` | `admin.admin_start_maintenance` | `admin` |
| `GET` | `/admin/maintenance/status` | `admin.admin_maintenance_status` | `admin` |
| `POST` | `/admin/notifications/broadcast` | `admin.admin_broadcast_notifications` | `admin` |
| `GET` | `/admin/operations/jobs` | `admin.admin_operations_jobs` | `admin` |
| `POST` | `/admin/operations/jobs/<job_id>/retry` | `admin.admin_retry_job` | `admin` |
| `GET` | `/admin/telemetry` | `admin.admin_telemetry` | `admin` |
| `GET` | `/admin/users` | `admin.admin_users` | `admin` |
| `GET` | `/admin/users/<user_id>` | `admin.admin_get_user` | `admin` |
| `POST` | `/admin/users/<user_id>/revoke-sessions` | `admin.admin_force_revoke_sessions` | `admin` |
| `POST` | `/admin/users/<user_id>/roles` | `admin.manage_user_roles` | `admin` |
| `POST` | `/admin/users/<user_id>/suspend` | `admin.admin_suspend_user` | `admin` |
| `POST` | `/admin/users/<user_id>/unsuspend` | `admin.admin_unsuspend_user` | `admin` |
| `GET` | `/api/admin/analytics/overview` | `api_admin.api_admin_analytics_overview` | `api_admin` |
| `GET` | `/api/admin/audit-logs` | `api_admin.api_list_audit_logs` | `api_admin` |
| `GET` | `/api/admin/audit-logs/<audit_id>` | `api_admin.api_get_audit_log_by_id` | `api_admin` |
| `POST` | `/api/admin/backups` | `api_admin.api_admin_create_backup` | `api_admin` |
| `GET` | `/api/admin/backups` | `api_admin.api_admin_list_backups` | `api_admin` |
| `GET` | `/api/admin/backups/<backup_id>` | `api_admin.api_admin_get_backup_detail` | `api_admin` |
| `POST` | `/api/admin/backups/<backup_id>/restore` | `api_admin.api_admin_restore_database` | `api_admin` |
| `POST` | `/api/admin/backups/<backup_id>/restore/dry-run` | `api_admin.api_admin_dry_run_restore` | `api_admin` |
| `POST` | `/api/admin/backups/<backup_id>/verify` | `api_admin.api_admin_verify_backup` | `api_admin` |
| `GET` | `/api/admin/courses` | `api_admin.api_admin_courses` | `api_admin` |
| `GET` | `/api/admin/courses/<course_id>` | `api_admin.api_admin_course_detail` | `api_admin` |
| `POST` | `/api/admin/courses/<course_id>/lessons/<lesson_id>/flag` | `api_admin.api_flag_course_lesson` | `api_admin` |
| `POST` | `/api/admin/courses/<course_id>/publish` | `api_admin.api_publish_course` | `api_admin` |
| `POST` | `/api/admin/courses/<course_id>/reassign` | `api_admin.api_reassign_course` | `api_admin` |
| `POST` | `/api/admin/courses/<course_id>/restore` | `api_admin.api_restore_course` | `api_admin` |
| `POST` | `/api/admin/courses/<course_id>/review` | `api_admin.api_review_course` | `api_admin` |
| `DELETE, POST` | `/api/admin/courses/<course_id>/trash` | `api_admin.api_trash_course` | `api_admin` |
| `GET` | `/api/admin/courses/pending` | `api_admin.api_list_pending_courses` | `api_admin` |
| `POST` | `/api/admin/courses/swap` | `api_admin.api_swap_courses` | `api_admin` |
| `GET` | `/api/admin/dashboard` | `api_admin.api_dashboard` | `api_admin` |
| `POST` | `/api/admin/emails/retry-failed` | `api_admin.api_admin_retry_failed_emails` | `api_admin` |
| `GET` | `/api/admin/faculty/workload` | `api_admin.api_admin_faculty_workload` | `api_admin` |
| `POST` | `/api/admin/files/<asset_id>/quarantine-override` | `api_admin.api_override_file_quarantine` | `api_admin` |
| `GET` | `/api/admin/health` | `api_admin.api_admin_health` | `api_admin` |
| `GET` | `/api/admin/instructor-applications` | `api_admin.api_admin_instructor_applications` | `api_admin` |
| `GET` | `/api/admin/instructor-applications/<app_id>` | `api_admin.api_admin_instructor_application_detail` | `api_admin` |
| `GET` | `/api/admin/instructor-applications/<app_id>/evidence/<filename>` | `api_admin.api_admin_download_application_evidence` | `api_admin` |
| `POST` | `/api/admin/instructor-applications/<app_id>/review` | `api_admin.api_admin_review_instructor_application` | `api_admin` |
| `POST` | `/api/admin/maintenance/end` | `api_admin.api_admin_end_maintenance` | `api_admin` |
| `POST` | `/api/admin/maintenance/start` | `api_admin.api_admin_start_maintenance` | `api_admin` |
| `GET` | `/api/admin/maintenance/status` | `api_admin.api_admin_maintenance_status` | `api_admin` |
| `POST` | `/api/admin/notifications/broadcast` | `api_admin.api_admin_broadcast_notifications` | `api_admin` |
| `GET` | `/api/admin/operations/jobs` | `api_admin.api_admin_operations_jobs` | `api_admin` |
| `POST` | `/api/admin/operations/jobs/<job_id>/retry` | `api_admin.api_admin_retry_job` | `api_admin` |
| `GET` | `/api/admin/telemetry` | `api_admin.api_admin_telemetry` | `api_admin` |
| `GET` | `/api/admin/users` | `api_admin.api_admin_users` | `api_admin` |
| `GET` | `/api/admin/users/<user_id>` | `api_admin.api_admin_get_user` | `api_admin` |
| `POST` | `/api/admin/users/<user_id>/revoke-sessions` | `api_admin.api_admin_force_revoke_sessions` | `api_admin` |
| `POST` | `/api/admin/users/<user_id>/roles` | `api_admin.api_manage_user_roles` | `api_admin` |
| `POST` | `/api/admin/users/<user_id>/suspend` | `api_admin.api_admin_suspend_user` | `api_admin` |
| `POST` | `/api/admin/users/<user_id>/unsuspend` | `api_admin.api_admin_unsuspend_user` | `api_admin` |
| `POST` | `/api/ai/chat` | `api_ai.unified_chat_api` | `api_ai` |
| `POST` | `/api/ai/cleanup` | `api_ai.cleanup_conversations_api` | `api_ai` |
| `POST` | `/api/ai/conversations` | `api_ai.create_conversation_api` | `api_ai` |
| `GET` | `/api/ai/conversations/<conversation_id>` | `api_ai.get_conversation_api` | `api_ai` |
| `POST` | `/api/ai/conversations/<conversation_id>/messages` | `api_ai.send_message_api` | `api_ai` |
| `POST` | `/api/ai/conversations/cleanup` | `api_ai.cleanup_conversations_api` | `api_ai` |
| `POST` | `/api/ai/courses/<course_id>/ingest` | `api_ai.ingest_course_knowledge_api` | `api_ai` |
| `POST` | `/api/ai/courses/<course_id>/query` | `api_ai.query_course_rag_api` | `api_ai` |
| `GET` | `/api/ai/courses/<course_id>/sources` | `api_ai.list_course_sources_api` | `api_ai` |
| `POST` | `/api/ai/lessons/<lesson_id>/ingest` | `api_ai.ingest_lesson_knowledge_api` | `api_ai` |
| `POST` | `/api/ai/questions/draft` | `api_ai.draft_questions_api` | `api_ai` |
| `GET` | `/api/ai/questions/drafts` | `api_ai.list_drafts_api` | `api_ai` |
| `POST` | `/api/ai/questions/drafts/<draft_id>/approve` | `api_ai.approve_draft_api` | `api_ai` |
| `POST` | `/api/ai/questions/drafts/<draft_id>/reject` | `api_ai.reject_draft_api` | `api_ai` |
| `POST` | `/api/ai/questions/generate` | `api_ai.draft_questions_api` | `api_ai` |
| `GET` | `/api/ai/recommendations` | `api_ai.get_recommendations_api` | `api_ai` |
| `DELETE` | `/api/ai/sources/<source_id>` | `api_ai.delete_source_api` | `api_ai` |
| `POST` | `/api/assessments` | `api_assessments.create_assessment_route` | `api_assessments` |
| `GET` | `/api/assessments/<assessment_id>` | `api_assessments.get_assessment_route` | `api_assessments` |
| `PATCH` | `/api/assessments/<assessment_id>` | `api_assessments.patch_assessment_route` | `api_assessments` |
| `GET` | `/api/assessments/<assessment_id>/attempts` | `api_assessments.list_student_assessment_attempts_route` | `api_assessments` |
| `POST` | `/api/assessments/<assessment_id>/attempts` | `api_assessments.start_assessment_attempt_route` | `api_assessments` |
| `POST` | `/api/assessments/<assessment_id>/blueprint` | `api_assessments.configure_blueprint_route` | `api_assessments` |
| `POST` | `/api/assessments/<assessment_id>/blueprint/materialize` | `api_assessments.materialize_blueprint_route` | `api_assessments` |
| `POST` | `/api/assessments/<assessment_id>/cancel` | `api_assessments.cancel_assessment_route` | `api_assessments` |
| `POST` | `/api/assessments/<assessment_id>/publish` | `api_assessments.publish_assessment_route` | `api_assessments` |
| `POST` | `/api/assessments/<assessment_id>/questions` | `api_assessments.assign_question_route` | `api_assessments` |
| `DELETE` | `/api/assessments/<assessment_id>/questions/<question_id>` | `api_assessments.remove_question_route` | `api_assessments` |
| `PATCH` | `/api/assessments/<assessment_id>/questions/<question_id>` | `api_assessments.update_question_assignment_route` | `api_assessments` |
| `POST` | `/api/assessments/<assessment_id>/regrade` | `api_assessments.regrade_assessment_route` | `api_assessments` |
| `POST` | `/api/assessments/<assessment_id>/release-scores` | `api_assessments.release_scores_route` | `api_assessments` |
| `POST` | `/api/assessments/<assessment_id>/restore` | `api_assessments.restore_assessment_route` | `api_assessments` |
| `POST` | `/api/assessments/<assessment_id>/sections` | `api_assessments.create_section_route` | `api_assessments` |
| `DELETE` | `/api/assessments/<assessment_id>/sections/<section_id>` | `api_assessments.delete_section_route` | `api_assessments` |
| `POST` | `/api/assessments/<assessment_id>/trash` | `api_assessments.trash_assessment_route` | `api_assessments` |
| `GET` | `/api/attempts/<attempt_id>` | `api_attempts.get_attempt_delivery_route` | `api_attempts` |
| `PUT` | `/api/attempts/<attempt_id>/answers/<attempt_question_id>` | `api_attempts.save_attempt_answer_route` | `api_attempts` |
| `POST` | `/api/attempts/<attempt_id>/answers/sync` | `api_attempts.sync_offline_answers_route` | `api_attempts` |
| `GET` | `/api/attempts/<attempt_id>/grade-history` | `api_attempts.get_attempt_grade_history_route` | `api_attempts` |
| `POST` | `/api/attempts/<attempt_id>/grades/<attempt_question_id>` | `api_attempts.grade_attempt_question_route` | `api_attempts` |
| `POST` | `/api/attempts/<attempt_id>/heartbeat` | `api_attempts.renew_attempt_lease_route` | `api_attempts` |
| `POST` | `/api/attempts/<attempt_id>/lease` | `api_attempts.takeover_attempt_lease_route` | `api_attempts` |
| `POST` | `/api/attempts/<attempt_id>/lease/heartbeat` | `api_attempts.renew_attempt_lease_route` | `api_attempts` |
| `POST` | `/api/attempts/<attempt_id>/lease/release` | `api_attempts.release_attempt_lease_route` | `api_attempts` |
| `POST` | `/api/attempts/<attempt_id>/lease/takeover` | `api_attempts.takeover_attempt_lease_route` | `api_attempts` |
| `GET` | `/api/attempts/<attempt_id>/result` | `api_attempts.get_attempt_result_route` | `api_attempts` |
| `POST` | `/api/attempts/<attempt_id>/submit` | `api_attempts.submit_assessment_attempt_route` | `api_attempts` |
| `POST` | `/api/auth/email-change` | `api_auth_unversioned.request_email_change_api` | `api_auth_unversioned` |
| `POST` | `/api/auth/email-change/verify` | `api_auth_unversioned.verify_email_change_api` | `api_auth_unversioned` |
| `POST` | `/api/auth/login` | `api_auth_unversioned.login_for_token` | `api_auth_unversioned` |
| `POST` | `/api/auth/logout` | `api_auth_unversioned.logout_api` | `api_auth_unversioned` |
| `GET` | `/api/auth/me` | `api_auth_unversioned.get_current_user` | `api_auth_unversioned` |
| `POST` | `/api/auth/refresh` | `api_auth_unversioned.refresh` | `api_auth_unversioned` |
| `POST` | `/api/auth/revoke` | `api_auth_unversioned.revoke` | `api_auth_unversioned` |
| `POST` | `/api/auth/token` | `api_auth_unversioned.login_for_token` | `api_auth_unversioned` |
| `POST` | `/api/courses` | `api_courses.create_course_api` | `api_courses` |
| `GET` | `/api/courses` | `api_courses.list_courses_catalog` | `api_courses` |
| `GET` | `/api/courses/<course_id>` | `api_courses.get_course_detail_api` | `api_courses` |
| `DELETE` | `/api/courses/<course_id>` | `api_courses.trash_course_api` | `api_courses` |
| `PATCH` | `/api/courses/<course_id>` | `api_courses.update_course_api` | `api_courses` |
| `GET` | `/api/courses/<course_id>/analytics` | `api_courses.get_course_analytics_api` | `api_courses` |
| `POST` | `/api/courses/<course_id>/archive` | `api_courses.archive_course_api` | `api_courses` |
| `POST` | `/api/courses/<course_id>/assessments` | `api_courses.create_course_assessment_route` | `api_courses` |
| `GET` | `/api/courses/<course_id>/assessments` | `api_courses.list_course_assessments_route` | `api_courses` |
| `POST` | `/api/courses/<course_id>/changeset/discard` | `api_courses.discard_course_changeset_api` | `api_courses` |
| `POST` | `/api/courses/<course_id>/changeset/retract` | `api_courses.retract_course_changeset_api` | `api_courses` |
| `GET` | `/api/courses/<course_id>/changeset/status` | `api_courses.get_course_changeset_status_api` | `api_courses` |
| `POST` | `/api/courses/<course_id>/changeset/submit` | `api_courses.submit_course_changeset_api` | `api_courses` |
| `GET` | `/api/courses/<course_id>/completion-rules` | `api_courses.get_course_completion_rules_api` | `api_courses` |
| `PUT` | `/api/courses/<course_id>/completion-rules` | `api_courses.set_course_completion_rules_api` | `api_courses` |
| `POST` | `/api/courses/<course_id>/enroll` | `api_courses.enroll_course_api` | `api_courses` |
| `GET` | `/api/courses/<course_id>/enrollments` | `api_courses.get_course_enrollments_api` | `api_courses` |
| `GET` | `/api/courses/<course_id>/files` | `api_courses.list_course_files_api` | `api_courses` |
| `POST` | `/api/courses/<course_id>/files` | `api_courses.upload_course_file_api` | `api_courses` |
| `POST` | `/api/courses/<course_id>/imports` | `api_courses.create_course_import_api` | `api_courses` |
| `GET` | `/api/courses/<course_id>/imports` | `api_courses.list_course_imports_api` | `api_courses` |
| `POST` | `/api/courses/<course_id>/leave` | `api_courses.leave_course_api` | `api_courses` |
| `POST` | `/api/courses/<course_id>/lessons` | `api_courses.create_course_lesson_api` | `api_courses` |
| `GET` | `/api/courses/<course_id>/lessons` | `api_courses.get_course_lessons_api` | `api_courses` |
| `POST` | `/api/courses/<course_id>/lessons/<lesson_id>/progress` | `api_courses.record_course_lesson_progress_api` | `api_courses` |
| `POST` | `/api/courses/<course_id>/lessons/reorder` | `api_courses.reorder_course_lessons_api` | `api_courses` |
| `POST` | `/api/courses/<course_id>/prerequisites` | `api_courses.add_course_prerequisite_api` | `api_courses` |
| `GET` | `/api/courses/<course_id>/prerequisites` | `api_courses.get_course_prerequisites_api` | `api_courses` |
| `DELETE` | `/api/courses/<course_id>/prerequisites/<prereq_id>` | `api_courses.remove_course_prerequisite_api` | `api_courses` |
| `GET` | `/api/courses/<course_id>/progress` | `api_courses.get_course_progress_api` | `api_courses` |
| `POST` | `/api/courses/<course_id>/publish-request` | `api_courses.publish_request_api` | `api_courses` |
| `POST` | `/api/courses/<course_id>/re-enroll` | `api_courses.re_enroll_course_api` | `api_courses` |
| `POST` | `/api/courses/<course_id>/submit` | `api_courses.publish_request_api` | `api_courses` |
| `GET` | `/api/courses/<course_id>/thumbnail` | `api_courses.get_course_thumbnail_api` | `api_courses` |
| `POST` | `/api/courses/<course_id>/trash` | `api_courses.trash_course_api` | `api_courses` |
| `POST` | `/api/files` | `api_files.upload_file_generic_api` | `api_files` |
| `DELETE` | `/api/files/<asset_id>` | `api_files.delete_file_asset_api` | `api_files` |
| `GET` | `/api/files/<asset_id>` | `api_files.get_file_metadata_api` | `api_files` |
| `GET` | `/api/files/<asset_id>/download` | `api_files.download_file_api` | `api_files` |
| `POST` | `/api/files/<asset_id>/download-ticket` | `api_files.download_ticket_api` | `api_files` |
| `POST` | `/api/files/<asset_id>/quarantine-override` | `api_files.quarantine_override_api` | `api_files` |
| `POST` | `/api/files/<asset_id>/rescan` | `api_files.rescan_file_api` | `api_files` |
| `POST` | `/api/files/<asset_id>/restore` | `api_files.restore_file_asset_api` | `api_files` |
| `POST` | `/api/files/<asset_id>/revisions` | `api_files.add_file_revision_api` | `api_files` |
| `GET` | `/api/files/<asset_id>/scan-results` | `api_files.get_file_scans_api` | `api_files` |
| `GET` | `/api/files/<asset_id>/scans` | `api_files.get_file_scans_api` | `api_files` |
| `GET` | `/api/files/<asset_id>/stream` | `api_files.download_file_api` | `api_files` |
| `POST` | `/api/imports` | `api_imports.create_import_api` | `api_imports` |
| `GET` | `/api/imports/<job_id>` | `api_imports.get_import_api` | `api_imports` |
| `POST` | `/api/imports/<job_id>/cancel` | `api_imports.cancel_import_api` | `api_imports` |
| `POST` | `/api/imports/<job_id>/commit` | `api_imports.commit_import_api` | `api_imports` |
| `POST` | `/api/imports/<job_id>/process` | `api_imports.process_import_api` | `api_imports` |
| `PATCH` | `/api/imports/<job_id>/questions/<temp_id>` | `api_imports.update_question_api` | `api_imports` |
| `POST` | `/api/imports/<job_id>/questions/<temp_id>/decision` | `api_imports.set_question_decision_api` | `api_imports` |
| `POST` | `/api/lessons` | `api_lessons.create_lesson_api` | `api_lessons` |
| `GET` | `/api/lessons/<lesson_id>` | `api_lessons.get_lesson_api` | `api_lessons` |
| `DELETE` | `/api/lessons/<lesson_id>` | `api_lessons.trash_lesson_api` | `api_lessons` |
| `PATCH, PUT` | `/api/lessons/<lesson_id>` | `api_lessons.update_lesson_api` | `api_lessons` |
| `POST` | `/api/lessons/<lesson_id>/activity` | `api_lessons.record_activity_api` | `api_lessons` |
| `POST` | `/api/lessons/<lesson_id>/draft/discard` | `api_lessons.discard_lesson_draft_api` | `api_lessons` |
| `POST` | `/api/lessons/<lesson_id>/opt-in` | `api_lessons.opt_in_lesson_revision_api` | `api_lessons` |
| `POST` | `/api/lessons/<lesson_id>/playback-sessions` | `api_lessons.start_playback_api` | `api_lessons` |
| `POST` | `/api/lessons/<lesson_id>/playback/start` | `api_lessons.start_playback_api` | `api_lessons` |
| `POST` | `/api/lessons/<lesson_id>/progress` | `api_lessons.record_progress_api` | `api_lessons` |
| `POST` | `/api/lessons/<lesson_id>/resources` | `api_lessons.attach_lesson_resource_api` | `api_lessons` |
| `DELETE` | `/api/lessons/<lesson_id>/resources/<resource_id>` | `api_lessons.detach_lesson_resource_api` | `api_lessons` |
| `POST` | `/api/lessons/<lesson_id>/status` | `api_lessons.change_lesson_status_api` | `api_lessons` |
| `POST` | `/api/lessons/<lesson_id>/trash` | `api_lessons.trash_lesson_api` | `api_lessons` |
| `GET` | `/api/notifications` | `api_notifications.list_notifications_api` | `api_notifications` |
| `DELETE` | `/api/notifications/<notification_id>` | `api_notifications.dismiss_notification_api` | `api_notifications` |
| `PATCH, POST` | `/api/notifications/<notification_id>/dismiss` | `api_notifications.dismiss_notification_api` | `api_notifications` |
| `PATCH, POST` | `/api/notifications/<notification_id>/read` | `api_notifications.mark_read_api` | `api_notifications` |
| `POST` | `/api/notifications/broadcast` | `api_notifications.broadcast_notification_api` | `api_notifications` |
| `POST` | `/api/notifications/emails/retry-failed` | `api_notifications.retry_failed_emails_api` | `api_notifications` |
| `POST` | `/api/notifications/mark-all-read` | `api_notifications.mark_all_read_api` | `api_notifications` |
| `GET` | `/api/notifications/preferences` | `api_notifications.get_preferences_api` | `api_notifications` |
| `PATCH, PUT` | `/api/notifications/preferences` | `api_notifications.update_preferences_api` | `api_notifications` |
| `GET` | `/api/notifications/unread-count` | `api_notifications.unread_count_api` | `api_notifications` |
| `GET` | `/api/regrade-jobs/<job_id>` | `api_regrades.get_regrade_job_route` | `api_regrades` |
| `POST` | `/api/regrade-jobs/<job_id>/retry` | `api_regrades.retry_regrade_job_route` | `api_regrades` |
| `GET` | `/api/student/analytics/overview` | `api_student.get_student_analytics_overview_api` | `api_student` |
| `GET` | `/api/student/courses/<course_id>/completion` | `api_student.get_student_course_completion_api` | `api_student` |
| `GET` | `/api/student/enrollments` | `api_student.get_student_enrollments_api` | `api_student` |
| `GET` | `/api/student/instructor-application` | `api_student.get_instructor_application_api` | `api_student` |
| `POST` | `/api/student/instructor-application` | `api_student.submit_instructor_application_api` | `api_student` |
| `POST` | `/api/student/instructor-application/cancel` | `api_student.cancel_instructor_application_api` | `api_student` |
| `POST` | `/api/telemetry` | `frontend.post_client_telemetry` | `frontend` |
| `GET` | `/api/ui/screen/<folder_name>` | `frontend.get_screen_html` | `frontend` |
| `GET` | `/api/ui/screens` | `frontend.list_screens` | `frontend` |
| `POST` | `/api/v1/auth/email-change` | `api_auth.request_email_change_api` | `api_auth` |
| `POST` | `/api/v1/auth/email-change/verify` | `api_auth.verify_email_change_api` | `api_auth` |
| `POST` | `/api/v1/auth/login` | `api_auth.login_for_token` | `api_auth` |
| `POST` | `/api/v1/auth/logout` | `api_auth.logout_api` | `api_auth` |
| `GET` | `/api/v1/auth/me` | `api_auth.get_current_user` | `api_auth` |
| `POST` | `/api/v1/auth/refresh` | `api_auth.refresh` | `api_auth` |
| `POST` | `/api/v1/auth/revoke` | `api_auth.revoke` | `api_auth` |
| `POST` | `/api/v1/auth/token` | `api_auth.login_for_token` | `api_auth` |
| `GET, POST` | `/auth/change-password` | `auth.change_password_view` | `auth` |
| `GET, POST` | `/auth/forgot-password` | `auth.forgot_password` | `auth` |
| `GET, POST` | `/auth/login` | `auth.login` | `auth` |
| `POST` | `/auth/logout` | `auth.logout` | `auth` |
| `DELETE` | `/auth/notifications` | `auth.auth_clear_all_notifications` | `auth` |
| `GET` | `/auth/notifications` | `auth.auth_notifications_center` | `auth` |
| `DELETE, POST` | `/auth/notifications/<notification_id>` | `auth.auth_delete_notification` | `auth` |
| `POST` | `/auth/notifications/<notification_id>/delete` | `auth.auth_delete_notification` | `auth` |
| `POST` | `/auth/notifications/<notification_id>/read` | `auth.auth_mark_notification_read` | `auth` |
| `POST` | `/auth/notifications/clear` | `auth.auth_clear_all_notifications` | `auth` |
| `POST` | `/auth/notifications/mark-all-read` | `auth.auth_mark_all_notifications_read` | `auth` |
| `GET` | `/auth/notifications/unread-count` | `auth.auth_notifications_unread_count` | `auth` |
| `GET, PATCH, PUT` | `/auth/preferences` | `auth.auth_preferences` | `auth` |
| `GET, POST, PUT` | `/auth/profile` | `auth.auth_profile` | `auth` |
| `GET, POST` | `/auth/register` | `auth.register` | `auth` |
| `GET, POST` | `/auth/reset-password/<token>` | `auth.reset_password` | `auth` |
| `GET` | `/auth/runtime-config` | `auth.runtime_config` | `auth` |
| `POST` | `/auth/set-language` | `auth.set_language` | `auth` |
| `POST` | `/auth/set-timezone` | `auth.set_timezone` | `auth` |
| `POST` | `/auth/switch-role` | `auth.switch_role` | `auth` |
| `GET` | `/auth/verify-email/<token>` | `auth.verify_email` | `auth` |
| `GET` | `/frontend/<path:filename>` | `frontend.serve_frontend_assets` | `frontend` |
| `GET` | `/health` | `core.health` | `core` |
| `GET` | `/health/deep` | `core.health_deep` | `core` |
| `POST` | `/instructor/ai/questions/draft` | `instructor.instructor_ai_draft_questions` | `instructor` |
| `GET` | `/instructor/assessments/<assessment_id>` | `instructor.get_instructor_assessment_detail_route` | `instructor` |
| `PATCH, POST, PUT` | `/instructor/assessments/<assessment_id>` | `instructor.update_instructor_assessment_route` | `instructor` |
| `GET` | `/instructor/assessments/<assessment_id>/attempts` | `instructor.list_instructor_assessment_attempts_route` | `instructor` |
| `POST` | `/instructor/assessments/<assessment_id>/authoring` | `instructor.save_instructor_assessment_authoring_route` | `instructor` |
| `POST` | `/instructor/assessments/<assessment_id>/blueprint` | `instructor.configure_instructor_blueprint_route` | `instructor` |
| `POST` | `/instructor/assessments/<assessment_id>/blueprint/materialize` | `instructor.materialize_instructor_blueprint_route` | `instructor` |
| `POST` | `/instructor/assessments/<assessment_id>/cancel` | `instructor.cancel_instructor_assessment_route` | `instructor` |
| `GET` | `/instructor/assessments/<assessment_id>/gradebook.pdf` | `instructor.export_instructor_assessment_gradebook_pdf_route` | `instructor` |
| `GET` | `/instructor/assessments/<assessment_id>/grading/pending` | `instructor.list_instructor_pending_grading_route` | `instructor` |
| `POST` | `/instructor/assessments/<assessment_id>/import` | `instructor.import_assessment_document_route` | `instructor` |
| `POST` | `/instructor/assessments/<assessment_id>/publish` | `instructor.publish_instructor_assessment_route` | `instructor` |
| `POST` | `/instructor/assessments/<assessment_id>/questions` | `instructor.assign_instructor_question_route` | `instructor` |
| `DELETE` | `/instructor/assessments/<assessment_id>/questions/<question_id>` | `instructor.remove_instructor_question_route` | `instructor` |
| `POST` | `/instructor/assessments/<assessment_id>/questions/<question_id>/edit` | `instructor.edit_instructor_assessment_question_route` | `instructor` |
| `POST` | `/instructor/assessments/<assessment_id>/questions/<question_id>/remove` | `instructor.remove_instructor_question_route` | `instructor` |
| `POST` | `/instructor/assessments/<assessment_id>/questions/batch` | `instructor.batch_create_instructor_assessment_questions_route` | `instructor` |
| `POST` | `/instructor/assessments/<assessment_id>/questions/create` | `instructor.create_instructor_assessment_question_route` | `instructor` |
| `POST, PUT` | `/instructor/assessments/<assessment_id>/questions/reorder` | `instructor.reorder_instructor_assessment_questions_route` | `instructor` |
| `POST` | `/instructor/assessments/<assessment_id>/regrade` | `instructor.trigger_instructor_regrade_route` | `instructor` |
| `POST` | `/instructor/assessments/<assessment_id>/restore` | `instructor.restore_instructor_assessment_route` | `instructor` |
| `POST` | `/instructor/assessments/<assessment_id>/sections` | `instructor.create_instructor_section_route` | `instructor` |
| `DELETE` | `/instructor/assessments/<assessment_id>/sections/<section_id>` | `instructor.delete_instructor_section_route` | `instructor` |
| `POST` | `/instructor/assessments/<assessment_id>/trash` | `instructor.trash_instructor_assessment_route` | `instructor` |
| `POST` | `/instructor/attempts/<attempt_id>/appeal/review` | `instructor.review_instructor_attempt_appeal_route` | `instructor` |
| `GET` | `/instructor/attempts/<attempt_id>/focus-events` | `instructor.get_instructor_attempt_focus_events_route` | `instructor` |
| `POST` | `/instructor/attempts/<attempt_id>/grades/<attempt_question_id>` | `instructor.grade_instructor_essay_route` | `instructor` |
| `GET` | `/instructor/attempts/<attempt_id>/grading` | `instructor.get_instructor_attempt_grading_route` | `instructor` |
| `GET` | `/instructor/attempts/<attempt_id>/results` | `instructor.get_instructor_attempt_results_route` | `instructor` |
| `POST` | `/instructor/check-youtube-link` | `instructor.check_youtube_link_route` | `instructor` |
| `POST` | `/instructor/courses` | `instructor.create_course_route` | `instructor` |
| `GET` | `/instructor/courses` | `instructor.my_courses` | `instructor` |
| `GET` | `/instructor/courses/<course_id>` | `instructor.get_course_route` | `instructor` |
| `PATCH, POST, PUT` | `/instructor/courses/<course_id>` | `instructor.update_course_route` | `instructor` |
| `PUT` | `/instructor/courses/<course_id>/academic-settings` | `instructor.save_course_academic_settings_route` | `instructor` |
| `GET` | `/instructor/courses/<course_id>/analytics` | `instructor.course_analytics_view` | `instructor` |
| `POST` | `/instructor/courses/<course_id>/assessments` | `instructor.create_course_assessment_route` | `instructor` |
| `GET` | `/instructor/courses/<course_id>/assessments` | `instructor.list_instructor_course_assessments_route` | `instructor` |
| `POST` | `/instructor/courses/<course_id>/assessments/<assessment_id>/publish` | `instructor.publish_instructor_assessment_route` | `instructor` |
| `POST` | `/instructor/courses/<course_id>/cancel-submit` | `instructor.cancel_submit_course_route` | `instructor` |
| `GET` | `/instructor/courses/<course_id>/changeset/diff` | `instructor.get_course_changeset_diff_route` | `instructor` |
| `POST` | `/instructor/courses/<course_id>/changeset/discard` | `instructor.discard_course_changeset_route` | `instructor` |
| `POST` | `/instructor/courses/<course_id>/changeset/retract` | `instructor.retract_course_changeset_route` | `instructor` |
| `GET` | `/instructor/courses/<course_id>/changeset/status` | `instructor.get_course_changeset_status_route` | `instructor` |
| `POST` | `/instructor/courses/<course_id>/changeset/submit` | `instructor.submit_course_changeset_route` | `instructor` |
| `GET` | `/instructor/courses/<course_id>/completion-rules` | `instructor.get_course_completion_rules_route` | `instructor` |
| `POST, PUT` | `/instructor/courses/<course_id>/completion-rules` | `instructor.set_course_completion_rules_route` | `instructor` |
| `GET` | `/instructor/courses/<course_id>/files` | `instructor.instructor_list_course_files` | `instructor` |
| `POST` | `/instructor/courses/<course_id>/files` | `instructor.upload_course_file_route` | `instructor` |
| `GET` | `/instructor/courses/<course_id>/files/<asset_id>/download` | `instructor.download_course_file_route` | `instructor` |
| `POST` | `/instructor/courses/<course_id>/files/<asset_id>/rescan` | `instructor.rescan_course_file_route` | `instructor` |
| `POST` | `/instructor/courses/<course_id>/imports` | `instructor.instructor_create_course_import` | `instructor` |
| `GET` | `/instructor/courses/<course_id>/imports` | `instructor.instructor_list_course_imports` | `instructor` |
| `GET, POST` | `/instructor/courses/<course_id>/learning-units` | `instructor.learning_units_route` | `instructor` |
| `POST` | `/instructor/courses/<course_id>/learning-units/<unit_id>/submit` | `instructor.submit_learning_unit_route` | `instructor` |
| `POST, PUT` | `/instructor/courses/<course_id>/learning-units/reorder` | `instructor.reorder_learning_units_route` | `instructor` |
| `POST` | `/instructor/courses/<course_id>/lessons` | `instructor.create_lesson_route` | `instructor` |
| `POST` | `/instructor/courses/<course_id>/lessons/<lesson_id>/delete` | `instructor.delete_lesson_from_hub_route` | `instructor` |
| `POST` | `/instructor/courses/<course_id>/lessons/<lesson_id>/resources` | `instructor.attach_lesson_resource_route` | `instructor` |
| `DELETE` | `/instructor/courses/<course_id>/lessons/<lesson_id>/resources/<resource_id>` | `instructor.detach_lesson_resource_route` | `instructor` |
| `POST` | `/instructor/courses/<course_id>/lessons/<lesson_id>/resources/<resource_id>/delete` | `instructor.detach_lesson_resource_route` | `instructor` |
| `POST` | `/instructor/courses/<course_id>/lessons/reorder` | `instructor.reorder_lessons_route` | `instructor` |
| `GET` | `/instructor/courses/<course_id>/manage` | `instructor.manage_course_hub` | `instructor` |
| `POST` | `/instructor/courses/<course_id>/prerequisites` | `instructor.add_course_prerequisite_route` | `instructor` |
| `GET` | `/instructor/courses/<course_id>/prerequisites` | `instructor.list_course_prerequisites_route` | `instructor` |
| `DELETE` | `/instructor/courses/<course_id>/prerequisites/<prereq_id>` | `instructor.remove_course_prerequisite_route` | `instructor` |
| `DELETE, POST` | `/instructor/courses/<course_id>/prerequisites/<prereq_id>/delete` | `instructor.remove_course_prerequisite_route` | `instructor` |
| `POST` | `/instructor/courses/<course_id>/publish` | `instructor.publish_course_route` | `instructor` |
| `GET` | `/instructor/courses/<course_id>/publish-checklist` | `instructor.course_publish_checklist_route` | `instructor` |
| `POST` | `/instructor/courses/<course_id>/publish-request` | `instructor.submit_course_route` | `instructor` |
| `POST` | `/instructor/courses/<course_id>/scan-videos` | `instructor.scan_course_videos_route` | `instructor` |
| `GET` | `/instructor/courses/<course_id>/students` | `instructor.list_course_students_route` | `instructor` |
| `GET` | `/instructor/courses/<course_id>/students/<student_id>` | `instructor.get_student_detail` | `instructor` |
| `POST` | `/instructor/courses/<course_id>/submit` | `instructor.submit_course_route` | `instructor` |
| `DELETE, POST` | `/instructor/courses/<course_id>/trash` | `instructor.trash_course_route` | `instructor` |
| `GET` | `/instructor/dashboard` | `instructor.dashboard` | `instructor` |
| `GET` | `/instructor/exams/excel-template` | `instructor.instructor_get_excel_template_route` | `instructor` |
| `POST` | `/instructor/exams/parse-excel` | `instructor.instructor_parse_excel_exam_route` | `instructor` |
| `POST` | `/instructor/exams/parse-file` | `instructor.instructor_parse_exam_file_route` | `instructor` |
| `POST` | `/instructor/exams/parse-json` | `instructor.instructor_parse_exam_json_route` | `instructor` |
| `POST` | `/instructor/exams/parse-moodle-xml` | `instructor.instructor_parse_moodle_xml_route` | `instructor` |
| `GET` | `/instructor/exams/samples/json` | `instructor.instructor_get_json_sample_route` | `instructor` |
| `GET` | `/instructor/exams/samples/moodle-xml` | `instructor.instructor_get_moodle_xml_sample_route` | `instructor` |
| `DELETE` | `/instructor/files/<asset_id>` | `instructor.instructor_trash_file` | `instructor` |
| `GET` | `/instructor/files/<asset_id>/download` | `instructor.download_instructor_file_direct_route` | `instructor` |
| `POST` | `/instructor/files/<asset_id>/restore` | `instructor.instructor_restore_file` | `instructor` |
| `POST` | `/instructor/files/<asset_id>/trash` | `instructor.instructor_trash_file` | `instructor` |
| `GET` | `/instructor/grading` | `instructor.instructor_grading_overview` | `instructor` |
| `GET` | `/instructor/imports/<job_id>` | `instructor.instructor_get_import_detail` | `instructor` |
| `POST` | `/instructor/imports/<job_id>/cancel` | `instructor.instructor_cancel_import` | `instructor` |
| `POST` | `/instructor/imports/<job_id>/commit` | `instructor.instructor_commit_import` | `instructor` |
| `PATCH` | `/instructor/imports/<job_id>/questions/<temp_id>` | `instructor.instructor_update_import_question` | `instructor` |
| `POST` | `/instructor/imports/<job_id>/questions/<temp_id>/decision` | `instructor.instructor_set_import_decision` | `instructor` |
| `DELETE` | `/instructor/learning-units/<unit_id>` | `instructor.delete_learning_unit_route` | `instructor` |
| `PATCH` | `/instructor/learning-units/<unit_id>` | `instructor.update_learning_unit_route` | `instructor` |
| `POST` | `/instructor/learning-units/<unit_id>/submit` | `instructor.submit_learning_unit_route` | `instructor` |
| `GET` | `/instructor/lessons/<lesson_id>` | `instructor.get_lesson_route` | `instructor` |
| `DELETE` | `/instructor/lessons/<lesson_id>` | `instructor.trash_lesson_route` | `instructor` |
| `PATCH, PUT` | `/instructor/lessons/<lesson_id>` | `instructor.update_lesson_route` | `instructor` |
| `POST` | `/instructor/lessons/<lesson_id>/draft/discard` | `instructor.discard_lesson_draft_route` | `instructor` |
| `POST` | `/instructor/lessons/<lesson_id>/status` | `instructor.change_lesson_status_route` | `instructor` |
| `DELETE, POST` | `/instructor/lessons/<lesson_id>/trash` | `instructor.trash_lesson_route` | `instructor` |
| `GET` | `/instructor/prerequisite-requests` | `instructor.list_instructor_prerequisite_requests_route` | `instructor` |
| `POST` | `/instructor/prerequisite-requests/<int:req_id>/review` | `instructor.review_instructor_prerequisite_request_route` | `instructor` |
| `GET` | `/instructor/prerequisites/incoming-requests` | `instructor.list_prerequisite_incoming_requests_route` | `instructor` |
| `POST` | `/instructor/prerequisites/incoming-requests/<course_id>/<prereq_id>/review` | `instructor.review_incoming_prerequisite_request_route` | `instructor` |
| `GET` | `/instructor/prerequisites/incoming-requests/count` | `instructor.count_prerequisite_incoming_requests_route` | `instructor` |
| `GET` | `/instructor/regrade-jobs/<job_id>` | `instructor.get_instructor_regrade_job_route` | `instructor` |
| `POST` | `/instructor/regrade-jobs/<job_id>/retry` | `instructor.retry_instructor_regrade_job_route` | `instructor` |
| `GET` | `/student/ai-assistant` | `student.ai_assistant_view` | `student` |
| `POST` | `/student/ai/chat` | `student.student_ai_chat` | `student` |
| `GET` | `/student/assessments` | `student.assessments_view` | `student` |
| `GET` | `/student/assessments/<assessment_id>` | `student.assessment_detail_view` | `student` |
| `POST` | `/student/assessments/<assessment_id>/start` | `student.student_start_assessment` | `student` |
| `GET` | `/student/attempt/<attempt_id>` | `student.attempt_view` | `student` |
| `POST, PUT` | `/student/attempt/<attempt_id>/answers/<attempt_question_id>` | `student.save_student_attempt_answer` | `student` |
| `POST` | `/student/attempt/<attempt_id>/focus-events` | `student.record_student_attempt_focus_event` | `student` |
| `POST` | `/student/attempt/<attempt_id>/lease/renew` | `student.renew_student_attempt_lease` | `student` |
| `POST` | `/student/attempt/<attempt_id>/lease/takeover` | `student.takeover_student_attempt_lease` | `student` |
| `GET` | `/student/attempt/<attempt_id>/result` | `student.attempt_result_view` | `student` |
| `GET` | `/student/attempt/<attempt_id>/result.pdf` | `student.attempt_result_pdf` | `student` |
| `POST` | `/student/attempt/<attempt_id>/submit` | `student.submit_student_attempt` | `student` |
| `GET` | `/student/attempts/<attempt_id>/appeal` | `student.get_attempt_appeal_route` | `student` |
| `POST` | `/student/attempts/<attempt_id>/appeal` | `student.submit_attempt_appeal_route` | `student` |
| `GET` | `/student/attempts/<attempt_id>/grade-history` | `student.get_student_attempt_grade_history_route` | `student` |
| `GET` | `/student/become-instructor` | `student.become_instructor` | `student` |
| `POST` | `/student/become-instructor` | `student.submit_become_instructor` | `student` |
| `POST` | `/student/become-instructor/cancel` | `student.cancel_become_instructor` | `student` |
| `POST` | `/student/become-instructor/cancel` | `student.cancel_instructor_application` | `student` |
| `GET` | `/student/courses/<course_id>` | `student.student_course_detail` | `student` |
| `GET` | `/student/courses/<course_id>/certificate` | `student.get_student_course_certificate_route` | `student` |
| `GET` | `/student/courses/<course_id>/completion` | `student.get_student_course_completion_route` | `student` |
| `POST` | `/student/courses/<course_id>/enroll` | `student.student_enroll_course` | `student` |
| `GET` | `/student/courses/<course_id>/files/<asset_id>/download` | `student.download_lesson_file` | `student` |
| `GET` | `/student/courses/<course_id>/files/<asset_id>/download` | `student.download_student_course_file_route` | `student` |
| `POST` | `/student/courses/<course_id>/leave` | `student.student_leave_course` | `student` |
| `GET` | `/student/courses/<course_id>/lessons/<lesson_id>` | `student.get_student_lesson_route` | `student` |
| `POST` | `/student/courses/<course_id>/lessons/<lesson_id>/progress` | `student.record_student_progress_route` | `student` |
| `GET` | `/student/courses/<course_id>/lessons/<lesson_id>/video/<asset_id>/<segment_name>` | `student.get_lesson_hls_segment_route` | `student` |
| `GET` | `/student/courses/<course_id>/lessons/<lesson_id>/video/<asset_id>/key` | `student.get_lesson_hls_key_route` | `student` |
| `GET` | `/student/courses/<course_id>/lessons/<lesson_id>/video/<asset_id>/playlist.m3u8` | `student.get_lesson_hls_playlist_route` | `student` |
| `GET` | `/student/courses/<course_id>/lessons/<lesson_id>/video/<segment_name>` | `student.get_lesson_hls_segment_route` | `student` |
| `GET` | `/student/courses/<course_id>/lessons/<lesson_id>/video/key` | `student.get_lesson_hls_key_route` | `student` |
| `GET` | `/student/courses/<course_id>/lessons/<lesson_id>/video/playlist.m3u8` | `student.get_lesson_hls_playlist_route` | `student` |
| `GET` | `/student/courses/<course_id>/lessons/<lesson_id>/video/segments/<segment_name>` | `student.get_lesson_hls_segment_route` | `student` |
| `GET` | `/student/courses/<course_id>/progress` | `student.course_progress` | `student` |
| `POST` | `/student/courses/<course_id>/re-enroll` | `student.student_re_enroll_course` | `student` |
| `GET` | `/student/dashboard` | `student.dashboard` | `student` |
| `GET` | `/student/enrollments` | `student.student_list_enrollments` | `student` |
| `GET` | `/student/files/<asset_id>/download` | `student.download_student_course_file_route` | `student` |
| `GET` | `/student/lessons/<lesson_id>` | `student.get_student_lesson_by_id` | `student` |
| `POST` | `/student/lessons/<lesson_id>/opt-in` | `student.opt_in_student_lesson_revision` | `student` |
| `POST` | `/student/lessons/<lesson_id>/playback-sessions` | `student.start_student_playback_route` | `student` |
| `POST` | `/student/lessons/<lesson_id>/playback/start` | `student.start_student_playback_route` | `student` |
| `POST` | `/student/lessons/<lesson_id>/progress` | `student.record_student_progress_route` | `student` |
| `POST` | `/student/lessons/<lesson_id>/quiz-completion` | `student.complete_student_lesson_quiz` | `student` |
| `GET` | `/student/my-learning` | `student.my_learning` | `student` |
| `GET` | `/student/notifications` | `student.notifications_center` | `student` |
| `POST` | `/student/notifications/<notification_id>/read` | `student.student_mark_notification_read` | `student` |
| `POST` | `/student/notifications/mark-all-read` | `student.student_mark_all_read` | `student` |
| `GET` | `/student/recommendations` | `student.student_recommendations` | `student` |
