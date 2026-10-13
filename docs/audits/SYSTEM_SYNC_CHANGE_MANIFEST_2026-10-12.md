# Synchronization change manifest - 2026-10-12

Status: settled local remediation inventory; server/provider gates deferred. Final A-G report: SYSTEM_SYNC_LOCAL_COMPLETION_2026-10-13.md.

Baseline: `5f0e3b94109ded28a44ce1b8c8def43be2bc414d`; branch `codex/sync-remediation-2026-10-11`. No commit, push or deployment. Original audit is unchanged.

Fresh inventory includes 146 modified or scoped untracked files. Exact behavior, reuse, simplification and executed gates are in `SYSTEM_SYNC_REMEDIATION_PROGRESS_2026-10-11.md`; per-ID requirements are in `SYSTEM_SYNC_CLOSURE_LEDGER_2026-10-12.md`. Local credentials and ignored runtime outputs are excluded.

| File | Change purpose |
| --- | --- |
| `README.md` | Canonical durable progress receipt/schema count contract and repository verification. |
| `docs/audits/SYNC_ASSESSMENT_SQL_RACES_2026-10-12.md` | Plan, requirement ledger or actual verification evidence; original audit is preserved. |
| `docs/audits/SYNC_BROWSER_EVIDENCE_2026-10-12.md` | Plan, requirement ledger or actual verification evidence; original audit is preserved. |
| `docs/audits/SYNC_OPS_AI_SQLSERVER_EVIDENCE_2026-10-12.md` | Plan, requirement ledger or actual verification evidence; original audit is preserved. |
| `docs/audits/SYNC_SQLSERVER_CONCURRENCY_EVIDENCE_2026-10-12.md` | Plan, requirement ledger or actual verification evidence; original audit is preserved. |
| `docs/audits/SYNC_SQLSERVER_RECOVERY_EVIDENCE_2026-10-12.md` | Plan, requirement ledger or actual verification evidence; original audit is preserved. |
| `docs/audits/SYNC_SQLSERVER_REGRADE_SUBMISSION_EVIDENCE_2026-10-12.md` | Plan, requirement ledger or actual verification evidence; original audit is preserved. |
| `docs/audits/SYSTEM_SYNC_CHANGE_MANIFEST_2026-10-12.md` | Requirement-specific remediation or evidence documented in the progress report. |
| `docs/audits/SYSTEM_SYNC_CLOSURE_LEDGER_2026-10-12.md` | Plan, requirement ledger or actual verification evidence; original audit is preserved. |
| `docs/audits/SYSTEM_SYNC_REMEDIATION_PROGRESS_2026-10-11.md` | Plan, requirement ledger or actual verification evidence; original audit is preserved. |
| `docs/database/PWD301_DATABASE_ARCHITECTURE/05_DATA_DICTIONARY_COURSE.md` | Canonical durable progress receipt/schema count contract and repository verification. |
| `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/002_course_learning.sql` | Canonical durable progress receipt/schema count contract and repository verification. |
| `docs/superpowers/plans/2026-10-11-system-synchronization-remediation.md` | Plan, requirement ledger or actual verification evidence; original audit is preserved. |
| `docs/system/PWD301_SYSTEM_SPECIFICATION/api/04_COURSE_API.md` | Document atomic academic-settings manifest, standardized JSON envelope, and pending approval response. |
| `docs/system/PWD301_SYSTEM_SPECIFICATION/api/07_ASSESSMENT_API.md` | Document atomic authoring envelope, stable retry identities, optional publication CAS token and blueprint intent. |
| `frontend/assets/js/api.js` | Authoritative acknowledgement, retry, owner/context fences or lossless editor state; existing client repaired in place. |
| `frontend/assets/js/exam-store.js` | Authoritative acknowledgement, retry, owner/context fences or lossless editor state; existing client repaired in place. |
| `frontend/assets/js/router.js` | Authoritative acknowledgement, retry, owner/context fences or lossless editor state; existing client repaired in place. |
| `frontend/assets/js/ui.js` | Authoritative acknowledgement, retry, owner/context fences or lossless editor state; existing client repaired in place. |
| `frontend/assets/js/views/admin.js` | Authoritative acknowledgement, retry, owner/context fences or lossless editor state; existing client repaired in place. |
| `frontend/assets/js/views/instructor-exams.js` | Authoritative acknowledgement, retry, owner/context fences or lossless editor state; existing client repaired in place. |
| `frontend/assets/js/views/instructor.js` | Ordered lesson block manifest, immutable save/resource callbacks, dirty departure, retained quiz-image owners; video preview preserves controls/footprint and acknowledged draft revision replaces URL history identity. |
| `frontend/assets/js/views/student.js` | Mini-quiz ACK restoration, reliable enrollment errors, server avatar precedence, retained settings checkbox references and connected attempt callbacks/departure with empty-choice retry. |
| `migrations/versions/syncprogress20261011_durable_progress_receipts.py` | Additive durable lesson progress receipt migration; tested only on disposable databases. |
| `scripts/repo_check.py` | Canonical durable progress receipt/schema count contract and repository verification. |
| `src/pwd301/blueprints/admin/routes.py` | Backend transaction, authorization, durable state, concurrency or worker ownership repair; see domain table in progress report. |
| `src/pwd301/blueprints/api_admin/routes.py` | Backend transaction, authorization, durable state, concurrency or worker ownership repair; see domain table in progress report. |
| `src/pwd301/blueprints/api_assessments/routes.py` | Requirement-specific remediation or evidence documented in the progress report. |
| `src/pwd301/blueprints/api_import/routes.py` | Backend transaction, authorization, durable state, concurrency or worker ownership repair; see domain table in progress report. |
| `src/pwd301/blueprints/auth/routes.py` | Backend transaction, authorization, durable state, concurrency or worker ownership repair; see domain table in progress report. |
| `src/pwd301/blueprints/instructor/routes.py` | Backend transaction, authorization, durable state, concurrency or worker ownership repair; see domain table in progress report. |
| `src/pwd301/blueprints/student/routes.py` | Backend transaction, authorization, durable state, concurrency or worker ownership repair; see domain table in progress report. |
| `src/pwd301/models/__init__.py` | Backend transaction, authorization, durable state, concurrency or worker ownership repair; see domain table in progress report. |
| `src/pwd301/models/course.py` | Backend transaction, authorization, durable state, concurrency or worker ownership repair; see domain table in progress report. |
| `src/pwd301/services/ai_service.py` | Backend transaction, authorization, durable state, concurrency or worker ownership repair; see domain table in progress report. |
| `src/pwd301/services/analytics_service.py` | Portable SQL boolean predicates on the affected SQL Server analytics path. |
| `src/pwd301/services/assessment_service.py` | Backend transaction, authorization, durable state, concurrency or worker ownership repair; see domain table in progress report. |
| `src/pwd301/services/attempt_service.py` | Backend transaction, authorization, durable state, concurrency or worker ownership repair; see domain table in progress report. |
| `src/pwd301/services/audit_service.py` | Backend transaction, authorization, durable state, concurrency or worker ownership repair; see domain table in progress report. |
| `src/pwd301/services/auth_token_service.py` | Backend transaction, authorization, durable state, concurrency or worker ownership repair; see domain table in progress report. |
| `src/pwd301/services/background_job_service.py` | Backend transaction, authorization, durable state, concurrency or worker ownership repair; see domain table in progress report. |
| `src/pwd301/services/import_service.py` | Backend transaction, authorization, durable state, concurrency or worker ownership repair; see domain table in progress report. |
| `src/pwd301/services/jwt_auth_service.py` | Backend transaction, authorization, durable state, concurrency or worker ownership repair; see domain table in progress report. |
| `src/pwd301/services/lesson_service.py` | Backend transaction, authorization, durable state, concurrency or worker ownership repair; see domain table in progress report. |
| `src/pwd301/services/operations_service.py` | Backend transaction, authorization, durable state, concurrency or worker ownership repair; see domain table in progress report. |
| `src/pwd301/services/question_bank_service.py` | Backend transaction, authorization, durable state, concurrency or worker ownership repair; see domain table in progress report. |
| `src/pwd301/services/regrade_worker.py` | Backend transaction, authorization, durable state, concurrency or worker ownership repair; see domain table in progress report. |
| `src/pwd301/services/retention_service.py` | Backend transaction, authorization, durable state, concurrency or worker ownership repair; see domain table in progress report. |
| `src/pwd301/services/session_auth_service.py` | Backend transaction, authorization, durable state, concurrency or worker ownership repair; see domain table in progress report. |
| `src/pwd301/services/user_service.py` | Backend transaction, authorization, durable state, concurrency or worker ownership repair; see domain table in progress report. |
| `tests/api/test_admin_audit_api.py` | Regression or contract verification; fresh result is tracked in the progress report. |
| `tests/api/test_admin_backend_completion.py` | Regression or contract verification; fresh result is tracked in the progress report. |
| `tests/api/test_assessment_api.py` | Actual regression/verification evidence; executed results and limitations are tracked in the progress report. |
| `tests/api/test_attempt_lease_api.py` | Regression or contract verification; fresh result is tracked in the progress report. |
| `tests/api/test_instructor_backend_remediation.py` | Regression or contract verification; fresh result is tracked in the progress report. |
| `tests/api/test_m2_6_empirical_challenger.py` | Regression or contract verification; fresh result is tracked in the progress report. |
| `tests/api/test_operations_api.py` | Regression or contract verification; fresh result is tracked in the progress report. |
| `tests/concurrency/test_attempt_lease_race.py` | Regression or contract verification; fresh result is tracked in the progress report. |
| `tests/e2e/test_admin_ops_lifecycle_e2e.py` | Regression or contract verification; fresh result is tracked in the progress report. |
| `tests/frontend/academic_settings_atomic.test.js` | Regression or contract verification; fresh result is tracked in the progress report. |
| `tests/frontend/admin_workflow_enhancements.test.js` | Regression or contract verification; fresh result is tracked in the progress report. |
| `tests/frontend/course_review_regression.test.js` | Regression or contract verification; fresh result is tracked in the progress report. |
| `tests/frontend/exam_authoring_atomic.test.js` | Regression or contract verification; fresh result is tracked in the progress report. |
| `tests/frontend/sync_20261011_state.test.js` | Owner-scoped notification and persistence lifecycle tests, including moved settings inputs and attempt departure retry/drain. |
| `tests/frontend/sync_admin_remediation.test.js` | Regression or contract verification; fresh result is tracked in the progress report. |
| `tests/frontend/sync_course_editor_20261011.test.js` | Lesson callback/dirty/quiz-image regressions plus acknowledged revision route/history guard and retained video preview controls. |
| `tests/integration/test_approval_sqlserver.py` | Actual regression/verification evidence; executed results and limitations are tracked in the progress report. |
| `tests/integration/test_migrations.py` | Regression or contract verification; fresh result is tracked in the progress report. |
| `tests/integration/test_sqlserver_assessment_sync_concurrency.py` | Regression or contract verification; fresh result is tracked in the progress report. |
| `tests/integration/test_sqlserver_authoring_publish_cas.py` | Actual SQL publication CAS interleavings, all legacy freeze guards, blueprint transaction rollback and grading-repair/publication deadlock regressions. |
| `tests/integration/test_sqlserver_ops_ai_sync_concurrency.py` | SQL worker/retry and AI send interleavings, plus 111 raw conversations through actual bounded retention and 60-second cadence. |
| `tests/integration/test_sqlserver_regrade_submission_concurrency.py` | Regression or contract verification; fresh result is tracked in the progress report. |
| `tests/integration/test_sqlserver_sync_concurrency.py` | Regression or contract verification; fresh result is tracked in the progress report. |
| `tests/security/test_security_audit_fixes.py` | Regression or contract verification; fresh result is tracked in the progress report. |
| `tests/test_admin_security_remediation.py` | Regression or contract verification; fresh result is tracked in the progress report. |
| `tests/test_m1_challenger_stress.py` | Regression or contract verification; fresh result is tracked in the progress report. |
| `tests/test_repository_contract.py` | Regression or contract verification; fresh result is tracked in the progress report. |
| `tests/unit/test_assessment_regrading_traceability.py` | Regression or contract verification; fresh result is tracked in the progress report. |
| `tests/unit/test_assessment_service.py` | Regression or contract verification; fresh result is tracked in the progress report. |
| `tests/unit/test_attempt_autosave_service.py` | Regression or contract verification; fresh result is tracked in the progress report. |
| `tests/unit/test_attempt_lease_service.py` | Regression or contract verification; fresh result is tracked in the progress report. |
| `tests/unit/test_attempt_submission_service.py` | Regression or contract verification; fresh result is tracked in the progress report. |
| `tests/unit/test_hotfix_verifications.py` | Regression or contract verification; fresh result is tracked in the progress report. |
| `tests/unit/test_integrity_defects_fix.py` | Regression or contract verification; fresh result is tracked in the progress report. |
| `tests/unit/test_models.py` | Regression or contract verification; fresh result is tracked in the progress report. |
| `tests/unit/test_operations_service.py` | Regression or contract verification; fresh result is tracked in the progress report. |
| `tests/unit/test_regrade_service.py` | Regression or contract verification; fresh result is tracked in the progress report. |
| `tests/unit/test_sync_course_remediation.py` | Regression or contract verification; fresh result is tracked in the progress report. |
| `tests/unit/test_sync_ops_auth_remediation.py` | Regression or contract verification; fresh result is tracked in the progress report. |
| `tests/unit/test_sync_regrade_latest_revision.py` | Actual regression/verification evidence; executed results and limitations are tracked in the progress report. |
| `tests/unit/test_worker_maintenance.py` | Regression or contract verification; fresh result is tracked in the progress report. |
| `tests/unit/test_youtube_retry_job.py` | Regression or contract verification; fresh result is tracked in the progress report. |
| `docs/system/PWD301_SYSTEM_SPECIFICATION/api/12_ADMIN_API.md` | Document dedicated changeset type guard and individual resource review routing. |
| `tests/api/test_course_changeset_and_dos_defense.py` | Two wrong-request-type approval regressions and existing complete changeset workflow gates. |
| `docs/audits/SYNC_SQLSERVER_SKIPPED_GATES_RECONCILIATION_2026-10-12.md` | Exact expected/passed reconciliation of all 66 aggregate SQL skips. |
| `tests/integration/test_sqlserver_account_state_idempotency.py` | Real cached-identity account-state concurrency, protected-role and retry lock-release regressions. |
| `docs/audits/SYNC_IMPORT_QUICK_ADD_EVIDENCE_2026-10-12.md` | Import/Quick Add atomic retry and actual SQL/browser evidence; exact scope and fresh gates in the dedicated report. |
| `tests/frontend/quick_add_retry.test.js` | Import/Quick Add atomic retry and actual SQL/browser evidence; exact scope and fresh gates in the dedicated report. |
| `tests/integration/test_sqlserver_import_atomic_retry.py` | Import/Quick Add atomic retry and actual SQL/browser evidence; exact scope and fresh gates in the dedicated report. |
| `tests/integration/test_sqlserver_quick_add_retry.py` | Import/Quick Add atomic retry and actual SQL/browser evidence; exact scope and fresh gates in the dedicated report. |
| `docs/audits/SYNC_COURSE_REVIEW_DELIVERY_EVIDENCE_2026-10-12.md` | Course review intent/metadata/rollback and current Student resource delivery; exact SQL/browser gates in dedicated report. |
| `tests/api/test_student_backend_completion.py` | Course review intent/metadata/rollback and current Student resource delivery; exact SQL/browser gates in dedicated report. |
| `tests/integration/test_sqlserver_course_changeset_sync.py` | Course review intent/metadata/rollback and current Student resource delivery; exact SQL/browser gates in dedicated report. |
| `docs/audits/SYNC_RESET_SUBMIT_REGRADE_HTTP_EVIDENCE_2026-10-12.md` | Actual reset/submit/regrade HTTP and independent SQL/worker acceptance evidence; scope and fresh gates in dedicated report. |
| `tests/integration/test_sqlserver_password_reset_atomic.py` | Actual reset/submit/regrade HTTP and independent SQL/worker acceptance evidence; scope and fresh gates in dedicated report. |
| `tests/integration/test_sqlserver_regrade_http_dispatch.py` | Actual reset/submit/regrade HTTP and independent SQL/worker acceptance evidence; scope and fresh gates in dedicated report. |
| `tests/integration/test_sqlserver_submit_http_recovery.py` | Actual reset/submit/regrade HTTP and independent SQL/worker acceptance evidence; scope and fresh gates in dedicated report. |
| `docs/audits/SYNC_ADMIN_REVIEW_DETAIL_EVIDENCE_2026-10-12.md` | Exact review-detail/read recovery verification or guarded SQL fixture correction; see SYNC_ADMIN_REVIEW_DETAIL_EVIDENCE_2026-10-12.md. |
| `tests/api/test_admin_change_requests_review.py` | Exact review-detail/read recovery verification or guarded SQL fixture correction; see SYNC_ADMIN_REVIEW_DETAIL_EVIDENCE_2026-10-12.md. |
| `tests/api/test_admin_subroles_and_enhancements.py` | Exact review-detail/read recovery verification or guarded SQL fixture correction; see SYNC_ADMIN_REVIEW_DETAIL_EVIDENCE_2026-10-12.md. |
| `docs/audits/SYNC_BLOOM_AUTHORING_ENVELOPE_EVIDENCE_2026-10-12.md` | Actual Bloom/authoring envelope acceptance and repair evidence; see SYNC_BLOOM_AUTHORING_ENVELOPE_EVIDENCE_2026-10-12.md. |
| `docs/audits/SYNC_LESSON_SAVE_ROUTE_EVIDENCE_2026-10-12.md` | Delayed lesson save and selected route/F5 acceptance; see SYNC_LESSON_SAVE_ROUTE_EVIDENCE_2026-10-12.md. |
| `docs/audits/SYNC_VIDEO_DETACH_BROWSER_EVIDENCE_2026-10-12.md` | Actual video detach/confirmation/late ACK/review evidence; see SYNC_VIDEO_DETACH_BROWSER_EVIDENCE_2026-10-12.md. |
| `docs/audits/SYNC_MAINTENANCE_HTTP_PROCESS_EVIDENCE_2026-10-12.md` | Maintenance unknown-authority admission repair or actual HTTP/SQL/process evidence; see SYNC_MAINTENANCE_HTTP_PROCESS_EVIDENCE_2026-10-12.md. |
| `docs/system/PWD301_SYSTEM_SPECIFICATION/api/14_ERROR_MODEL.md` | Maintenance unknown-authority admission repair or actual HTTP/SQL/process evidence; see SYNC_MAINTENANCE_HTTP_PROCESS_EVIDENCE_2026-10-12.md. |
| `src/pwd301/__init__.py` | Maintenance unknown-authority admission repair or actual HTTP/SQL/process evidence; see SYNC_MAINTENANCE_HTTP_PROCESS_EVIDENCE_2026-10-12.md. |
| `tests/integration/test_sqlserver_maintenance_admission.py` | Maintenance unknown-authority admission repair or actual HTTP/SQL/process evidence; see SYNC_MAINTENANCE_HTTP_PROCESS_EVIDENCE_2026-10-12.md. |
| `docs/audits/SYNC_DRAFT_SCOPE_API_OUTCOME_EVIDENCE_2026-10-12.md` | Actual account/role/localStorage and HTTP outcome acceptance; see SYNC_DRAFT_SCOPE_API_OUTCOME_EVIDENCE_2026-10-12.md. |
| `docs/audits/SYNC_ATTEMPT_ADMISSION_OWNERSHIP_EVIDENCE_2026-10-13.md` | Actual Attempt lease admission and terminal ownership HTTP/SQL evidence; see SYNC_ATTEMPT_ADMISSION_OWNERSHIP_EVIDENCE_2026-10-13.md. |
| `docs/audits/SYNC_ATTEMPT_UI_LEASE_AUTOSAVE_EVIDENCE_2026-10-13.md` | Actual Attempt no-lease admission repair and aggregate autosave browser evidence; see SYNC_ATTEMPT_UI_LEASE_AUTOSAVE_EVIDENCE_2026-10-13.md. |
| `tests/frontend/attempt_lease_availability.test.js` | Actual Attempt no-lease admission repair and aggregate autosave browser evidence; see SYNC_ATTEMPT_UI_LEASE_AUTOSAVE_EVIDENCE_2026-10-13.md. |

| `docs/audits/SYNC_ATTEMPT_HEARTBEAT_EVIDENCE_2026-10-13.md` | Actual heartbeat/configurable lease RED/GREEN and SQL/browser lifecycle evidence. |
| `tests/frontend/attempt_lease_heartbeat.test.js` | Serial renewal, failure/retry, owner/root fencing and endpoint/header regressions. |

| `docs/audits/SYNC_EXAM_EDIT_BROWSER_EVIDENCE_2026-10-13.md` | Actual question/settings/Studio/F5/delete lifecycle evidence for historical007/008/025. |

| `docs/audits/SYNC_LESSON_ORDER_AGGREGATE_FINDINGS_2026-10-13.md` | Within-chapter order repair, current aggregate failures and unresolved atomic cross-unit move evidence. |

| `tests/frontend/lesson_course_order.test.js` | Real move handler regression requiring complete course order. |

| `tests/api/test_student_exam_backend_remediation.py` | Canonical independent configurable lease versus retained exam deadline regression. |

| `tests/security/test_security_remediation.py` | Real ProxyFix request with durable maintenance schema in its separate guarded app. |

| `tests/api/test_atomic_lesson_move.py` | Atomic placement/order, published review, rollback, target/limit validation and readable metadata regressions. |

| `docs/audits/SYNC_ATOMIC_CHAPTER_MOVE_EVIDENCE_2026-10-13.md` | Exact atomic cross-unit RED/GREEN, SQL and browser/review evidence. |

| `tests/frontend/exam_matrix_context.test.js` | Real matrix handler chapter/final context, required chapter/lesson and explicit independent-choice regressions. |

| `docs/audits/SYNC_LESSON_SELECTION_CHAPTER_EXAM_EVIDENCE_2026-10-13.md` | Actual delayed selection and native chapter workflow matrix RED/GREEN, F5 and SQL evidence. |

| `tests/frontend/ai_console_scope.test.js` | Six actual-controller conversation generation, root/owner/context, ordering and stale-finally regressions. |

| `docs/audits/SYNC_AI_CHAT_SCOPE_EVIDENCE_2026-10-13.md` | Exact AI lifecycle RED/GREEN, browser boundaries, terminal aggregate and pending SQL reconciliation. |

| `docs/audits/SYNC_MINI_QUIZ_THRESHOLD_EVIDENCE_2026-10-13.md` | Actual authored-threshold mismatch RED/GREEN, native failure/retry/strict server validation and SQL/F5 evidence. |

| `docs/audits/SYNC_NOTIFICATION_RUNTIME_EVIDENCE_2026-10-13.md` | Actual late read failure RED/GREEN and native owner/delete/ACK/snapshot/SQL/F5 evidence. |

| `docs/audits/SYNC_ADMIN_BATCH_ROLE_EVIDENCE_2026-10-13.md` | Actual native batch/rollback/refresh/SQL/F5 verification and corrected implementation trace. |

| `docs/audits/SYNC_BACKUP_NATIVE_PHYSICAL_EVIDENCE_2026-10-13.md` | Real native physical backup intent/SHA/VERIFYONLY/missing-file/F5 evidence and scoped card repair. |

| `tests/frontend/readiness_ui_truthfulness.test.js` | Actual backup-card render regression preserves persisted semantic trigger through list hydration. |

| `SYSTEM_SYNC_REMEDIATION_PROGRESS_2026-10-11.md` | Chronological remediation evidence and per-increment final gate reconciliation. |

| `src/pwd301/services/file_service.py` | Preserve isolated scan source until valid commit; complete atomic copied output and post-commit dedup/rejection cleanup. |

| `tests/unit/test_file_service.py` | Three real-session commit-failure source-preservation/SQL rollback/retry regressions. |

| `docs/audits/SYNC_REAL_CLAM_WORKER_EVIDENCE_2026-10-13.md` | Genuine ClamAV/SQL interleaving RED/GREEN, worker claim/expiry/retry and file byte recovery evidence. |
| `docs/audits/SYNC_FINAL_NATIVE_AI_APPEAL_EVIDENCE_2026-10-13.md` | Final local acceptance evidence, user-directed provider deferral, source review and A-G completion. |
| `docs/audits/SYNC_LOCAL_STORAGE_RESTORE_IDENTITY_EVIDENCE_2026-10-13.md` | Final local acceptance evidence, user-directed provider deferral, source review and A-G completion. |
| `docs/audits/SYSTEM_SYNC_LOCAL_COMPLETION_2026-10-13.md` | Final local acceptance evidence, user-directed provider deferral, source review and A-G completion. |
