# Completed Tasks

## TASK-001 — Project Foundation & Flask Bootstrap
- **Completion date:** 2026-09-08
- **Important files changed:**
  - `src/pwd301/config.py` (Base, Development, Testing, Production configurations with non-negotiable invariants)
  - `src/pwd301/extensions.py` (SQLAlchemy, Migrate, CSRFProtect, LoginManager shells)
  - `src/pwd301/__init__.py` (create_app factory, structured UTC logging, correlation ID, centralized error handlers)
  - `src/pwd301/blueprints/core/routes.py` (/health JSON probe, / informative root page)
  - `tests/conftest.py`, `tests/unit/test_config.py`, `tests/unit/test_factory.py`, `tests/api/test_smoke.py`
  - `pyproject.toml`, `scripts/repo_check.py`
- **Migrations created:** None (deferred to TASK-002 per specification)
- **Verification commands and results:**
  - `./scripts/verify.ps1`: PASS (repo_check, compileall, ruff check, ruff format --check, mypy src, pytest 23 passed with 96% coverage)
- **Known non-blocking limitations:** Live SQL Server connection and database migrations are scheduled for TASK-002.

## TASK-002 — SQLAlchemy Models + Initial Migration + Seed Baseline
- **Completion date:** 2026-09-08
- **Important files changed:**
  - `src/pwd301/models/` (71 tables mapped: identity, course, assessment, question_bank, attempt_regrade, file_storage, notification_audit, ai_rag)
  - `src/pwd301/seeds/baseline.py` (canonical seed data for roles, permissions, sysadmin user)
  - `migrations/versions/` (initial Alembic migration schema)
  - `tests/integration/test_migrations.py`, `tests/integration/test_seed.py`
- **Verification commands and results:**
  - `./scripts/verify.ps1`: PASS (migration upgrade/downgrade check, seed baseline test).

## TASK-003 — User / Account / Email Verification Foundation
- **Completion date:** 2026-09-08
- **Important files changed:**
  - `src/pwd301/services/user_service.py` (register, verify email, change password, suspend/unsuspend, role assignment)
  - `tests/unit/test_user_service.py`
- **Verification commands and results:**
  - `pytest tests/unit/test_user_service.py`: PASS (28 passed).

## TASK-004 — Session Authentication + JWT REST Authentication
- **Completion date:** 2026-09-08
- **Important files changed:**
  - `src/pwd301/services/session_auth_service.py` (server-side session lifecycle, hash validation, revocation)
  - `src/pwd301/services/jwt_auth_service.py` (access/refresh pair, token rotation, family replay detection)
  - `src/pwd301/blueprints/auth/` (Web UI session login/logout/register)
  - `tests/unit/test_jwt_auth_service.py`, `tests/api/test_auth_jwt.py`, `tests/api/test_auth_web.py`
- **Verification commands and results:**
  - `pytest tests/api/test_auth_*.py tests/unit/test_*auth*.py`: PASS.

## TASK-005 — RBAC + Resource/Object Authorization
- **Completion date:** 2026-09-08
- **Important files changed:**
  - `src/pwd301/services/authorization_service.py` (@require_roles, IDOR masking, fail-closed resolution)
  - `tests/unit/test_authorization_service.py`, `tests/security/test_rbac_and_idor.py`
- **Verification commands and results:**
  - `pytest tests/unit/test_authorization_service.py tests/security/test_rbac_and_idor.py`: PASS.

## TASK-006 — Course Management + Ownership/Reassignment
- **Completion date:** 2026-09-08
- **Important files changed:**
  - `src/pwd301/services/course_service.py` (create, update, change status, trash/restore, reassign)
  - `src/pwd301/blueprints/api_courses/routes.py`, `src/pwd301/blueprints/admin/routes.py`
  - `tests/unit/test_course_service.py`, `tests/api/test_course_api.py`, `tests/security/test_course_idor.py`
- **Verification commands and results:**
  - `pytest tests/unit/test_course_service.py tests/api/test_course_api.py tests/security/test_course_idor.py`: PASS.

## TASK-007 — Lessons + Completion Tracking
- **Completion date:** 2026-09-08
- **Important files changed:**
  - `src/pwd301/services/lesson_service.py` (lesson CRUD, position reordering, progress tracking)
  - `src/pwd301/blueprints/api_lessons/`
  - `tests/unit/test_lesson_service.py`, `tests/api/test_lesson_api.py`, `tests/security/test_lesson_idor.py`
- **Verification commands and results:**
  - `pytest tests/unit/test_lesson_service.py tests/api/test_lesson_api.py`: PASS.

## TASK-008 — Enrollment + Capacity + Prerequisites + Re-enrollment
- **Completion date:** 2026-09-08
- **Important files changed:**
  - `src/pwd301/services/enrollment_service.py` (enroll, leave, re-enroll, prerequisite cycle detection, capacity lock)
  - `tests/unit/test_enrollment_service.py`, `tests/api/test_enrollment_api.py`, `tests/concurrency/test_enrollment_capacity.py`
- **Verification commands and results:**
  - `pytest tests/unit/test_enrollment_service.py tests/api/test_enrollment_api.py tests/concurrency/`: PASS.

## TASK-009 — Course Progress + Completion Engine
- **Completion date:** 2026-09-08
- **Important files changed:**
  - `src/pwd301/services/completion_service.py` (Algorithm 01 progress calculation, completion rule criteria, auto-completion)
  - `tests/unit/test_completion_service.py`, `tests/api/test_completion_api.py`, `tests/security/test_completion_idor.py`
- **Verification commands and results:**
  - `pytest tests/unit/test_completion_service.py tests/api/test_completion_api.py`: PASS.

## TASK-010 — Question Bank
- **Completion date:** 2026-09-08
- **Important files changed:**
  - `src/pwd301/services/question_bank_service.py` (question authoring, choices, position handling)
  - `tests/unit/test_question_bank_service.py`, `tests/api/test_question_bank_api.py`, `tests/security/test_question_bank_idor.py`
- **Verification commands and results:**
  - `pytest tests/unit/test_question_bank_service.py tests/api/test_question_bank_api.py`: PASS.

## TASK-011 — QuestionRevision + Correction Rules
- **Completion date:** 2026-09-09
- **Important files changed:**
  - `src/pwd301/services/question_revision_service.py` (immutable revisions, student exposure tracking, correction rules)
  - `tests/unit/test_question_revision_service.py`, `tests/api/test_question_revision_api.py`, `tests/security/test_question_revision_idor.py`
- **Verification commands and results:**
  - `pytest tests/unit/test_question_revision_service.py tests/api/test_question_revision_api.py`: PASS.

## TASK-012 — Assessment Builder / Blueprint / Publish Rules
- **Completion date:** 2026-09-09
- **Important files changed:**
  - `src/pwd301/services/assessment_service.py` (assessment builder, sections, question pools, publish verification, structural freeze)
  - `tests/unit/test_assessment_service.py`, `tests/api/test_assessment_api.py`, `tests/security/test_assessment_idor.py`
- **Verification commands and results:**
  - `pytest tests/unit/test_assessment_service.py tests/api/test_assessment_api.py`: PASS.

## TASK-013 — Student Assessment Delivery, Attempt Snapshot & Server Timer Engine
- **Completion date:** 2026-09-09
- **Important files changed:**
  - `src/pwd301/services/attempt_service.py` (start attempt, delivery snapshot, server timer clamping, editing lease)
  - `src/pwd301/blueprints/api_attempts/routes.py`
  - `tests/unit/test_attempt_service.py`, `tests/api/test_attempt_api.py`, `tests/security/test_attempt_idor.py`
- **Verification commands and results:**
  - `pytest tests/unit/test_attempt_service.py tests/api/test_attempt_api.py tests/security/test_attempt_idor.py`: PASS.

## TASK-014 — Attempt Lease Management & Multi-Tab Takeover Engine
- **Completion date:** 2026-09-09
- **Important files changed:**
  - `src/pwd301/services/exceptions.py` (`AttemptLeaseExpiredError`, `AttemptLeaseConflictError`, `AttemptExpiredError`)
  - `src/pwd301/services/attempt_service.py` (`renew_attempt_lease`, `takeover_attempt_lease`, `release_attempt_lease`, `verify_attempt_lease`)
  - `src/pwd301/__init__.py` (Centralized domain error handlers for 409 LEASE_CONFLICT and DEADLINE_EXPIRED)
  - `src/pwd301/blueprints/api_attempts/routes.py` (Heartbeat, takeover, release endpoints & aliases)
  - `tests/unit/test_attempt_lease_service.py`, `tests/security/test_attempt_lease_idor.py`, `tests/concurrency/test_attempt_lease_race.py`, `tests/api/test_attempt_lease_api.py`
- **Verification commands and results:**
  - `repo_check.py`, `ruff check`, `ruff format --check`, `mypy src`: PASS
  - `pytest tests/unit/test_attempt_lease_service.py tests/security/test_attempt_lease_idor.py tests/concurrency/test_attempt_lease_race.py tests/api/test_attempt_lease_api.py -v`: PASS (32/32 passed)
  - `pytest`: PASS (397/397 passed)

## TASK-015 — Autosave, Offline Reconciliation & Idempotent Submission Engine
- **Completion date:** 2026-09-09
- **Important files changed:**
  - `src/pwd301/services/exceptions.py` (`SubmissionIdempotencyConflictError`, `AttemptAlreadySubmittedError`, `StaleAnswerSequenceError`, `StaleLeaseEpochError`)
  - `src/pwd301/services/attempt_service.py` (`save_attempt_answer`, `sync_offline_answers`, `submit_assessment_attempt`)
  - `src/pwd301/__init__.py` (Centralized domain error handlers for 409 SUBMISSION_CONFLICT and STATE_VIOLATION)
  - `src/pwd301/blueprints/api_attempts/routes.py` (Autosave PUT, batch sync POST, idempotent submit POST)
  - `tests/unit/test_attempt_autosave_service.py`, `tests/unit/test_attempt_submission_service.py`, `tests/security/test_attempt_submission_idor.py`, `tests/concurrency/test_submission_idempotency_race.py`, `tests/api/test_attempt_submission_api.py`
- **Verification commands and results:**
  - `repo_check.py`: PASS
  - `ruff check`: PASS (0 errors)
  - `ruff format --check`: PASS (all formatted)
  - `mypy src`: PASS (0 issues across 58 files)
  - `pytest` TASK-015 suite: PASS (25/25 passed)
  - `python -m pytest`: PASS (428/428 passed)
## TASK-016 — Assessment Grading Engine & Manual Essay Evaluation
- **Completion date:** 2026-09-09
- **Important files changed:**
  - `src/pwd301/services/exceptions.py` (`GradingError`, `ScoreReleasePolicyError`, `MaxPointsExceededError`, `AttemptNotSubmittedError`)
  - `src/pwd301/__init__.py` (Centralized domain error handlers for 400 VALIDATION_ERROR, 403 FORBIDDEN, 409 STATE_VIOLATION)
  - `src/pwd301/services/completion_service.py` (Criterion 3 assessment completion evaluation & `recalculate_course_completion`)
  - `src/pwd301/services/assessment_service.py` (`release_assessment_scores`, passing_score aliases, blueprint queries)
  - `src/pwd301/services/attempt_service.py` (`grade_attempt_objective_questions`, `grade_essay_question`, `calculate_attempt_result`, `get_attempt_result_for_student`, `list_pending_grading_attempts`, `get_attempt_grading_detail`)
  - `src/pwd301/blueprints/api_assessments/routes.py` (`POST /api/assessments/<assessment_id>/release-scores`)
  - `src/pwd301/blueprints/api_attempts/routes.py` (`GET /api/attempts/<attempt_id>/result`, `POST /api/attempts/<attempt_id>/grades/<attempt_question_id>`)
  - `src/pwd301/blueprints/instructor/routes.py` (`GET /instructor/assessments/<assessment_id>/grading/pending`, `GET /instructor/attempts/<attempt_id>/grading`, `POST /instructor/attempts/<attempt_id>/grades/<attempt_question_id>`)
  - `tests/unit/test_grading_service.py`, `tests/security/test_grading_idor.py`, `tests/api/test_grading_api.py`
- **Verification commands and results:**
  - `repo_check.py`: PASS (all 71 DDL tables, markdown fences balanced)
  - `ruff check`: PASS (0 errors across all modified and newly created files)
  - `ruff format --check`: PASS (all 15 files formatted cleanly)
  - `mypy src`: PASS (0 issues found across 58 source files)
  - `pytest` TASK-016 suite: PASS (21/21 passed in 18.48s)
  - `python -m pytest`: PASS (449/449 passed in 250.41s)

## TASK-017 — LMS Database Architecture Refactor & Critical Integrity Defects Fix
- **Completion date:** 2026-09-09
- **Important files changed:**
  - `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/` (002, 003, 005, 006, 007, 010, 011, 012)
  - `docs/database/PWD301_DATABASE_ARCHITECTURE/` (05, 06, 08, 09, 10 data dictionaries)
  - `migrations/versions/e8f9a1b2c3d4_0002_fix_critical_integrity_defects.py`
  - `src/pwd301/models/` (`question_bank.py`, `file_import.py`, `ai_rag.py`, `attempt_regrade.py`, `course.py`)
  - `src/pwd301/services/` (`attempt_service.py`, `question_bank_service.py`, `regrade_worker.py`, `retention_service.py`, `assessment_service.py`, `lesson_service.py`, `exceptions.py`)
  - `src/pwd301/__init__.py` (Error handlers for 409 `STALE_LEASE_EPOCH` and `STALE_ANSWER`)
  - `tests/unit/test_integrity_defects_fix.py` (Dedicated test suite for all 6 integrity defects)
- **Verification commands and results:**
  - `python scripts/repo_check.py`: PASS (71 CREATE TABLE statements confirmed, markdown fences balanced)
  - `ruff check src tests scripts`: PASS (0 errors)
  - `ruff format --check src tests scripts`: PASS (113 files formatted)
  - `mypy src`: PASS (Success: no issues found in 58 source files)
  - `pytest tests/unit/test_integrity_defects_fix.py -v`: PASS (6/6 passed in 3.36s)
  - `pytest tests/integration/test_migrations.py -v`: PASS (1/1 passed)
  - `./scripts/verify.ps1`: PASS (`PWD301 verification PASS`, 449/449 passed in 192.48s)

## TASK-017 (Engine) — Regrading Engine & Score History Implementation
- **Completion date:** 2026-09-09
- **Important files changed:**
  - `src/pwd301/models/attempt_regrade.py` (`public_id` property on `QuestionCorrection`, `RegradeJob`, `RegradeItem`)
  - `src/pwd301/services/regrade_worker.py` (Zero-Trust authorization, choice matching fallback, retry counter reset, course completion recalculation)
  - `src/pwd301/blueprints/instructor/routes.py` (`POST /instructor/regrade-jobs/<job_id>/retry`)
  - `tests/unit/test_regrade_service.py` (7 unit tests for Algorithm 11, skip logic, completion integration, idempotency, batching/retry)
  - `tests/security/test_regrade_idor.py` (11 security, IDOR, score release policy, and ADR-002 tests)
  - `tests/api/test_regrade_api.py` (4 API integration & web view tests)
- **Verification commands and results:**
  - `python scripts/repo_check.py`: PASS (71 CREATE TABLE statements confirmed, markdown fences balanced)
  - `python -m compileall -q src tests scripts`: PASS
  - `ruff check src tests scripts`: PASS (All checks passed!)
  - `ruff format --check src tests scripts`: PASS (116 files already formatted)
  - `mypy src`: PASS (Success: no issues found in 58 source files)
  - `pytest` TASK-017 test suites: PASS (22/22 passed in 17.49s)
  - `python -m pytest`: PASS (471/471 passed in 280.21s)
  - `./scripts/verify.ps1`: PASS (`PWD301 verification PASS`)

## TASK-018 — File Blob/Asset Storage & Authorization Engine
- **Completion date:** 2026-09-09
- **Important files changed:**
  - `src/pwd301/services/exceptions.py` (Added 7 domain exceptions for File Storage and Security)
  - `src/pwd301/__init__.py` (Registered exception handlers and `api_file_bp` with CSRF exemption)
  - `src/pwd301/models/file_import.py` (Added `sha256_hex` property on `FileBlob`, `public_id` UUIDv5 property on `FileRevision` and `LessonResource`)
  - `src/pwd301/services/file_service.py` (Full implementation of Algorithm 12 deduplication, size limits, dangerous extension checks, magic byte detection, revision lifecycle, soft delete/restore, Zero-Trust authorization, and ADR-002 serialization)
  - `src/pwd301/blueprints/api_files/` (`__init__.py`, `routes.py`: REST endpoints for metadata, versioned download, revisions, soft-delete/restore, generic upload)
  - `src/pwd301/blueprints/api_courses/routes.py` (`POST /api/courses/<id>/files`, `GET /api/courses/<id>/files`)
  - `src/pwd301/blueprints/api_lessons/routes.py` (`POST /api/lessons/<id>/resources`, `DELETE /api/lessons/<id>/resources/<resource_id>`)
  - `src/pwd301/blueprints/instructor/routes.py` (Web session endpoints for course files list, upload, trash, and restore)
  - `tests/unit/test_file_service.py` (8 unit tests for Algorithm 12, limits, dangerous extensions, rollback safety, ADR-002)
  - `tests/security/test_file_authorization_idor.py` (12 security and IDOR tests for Zero-Trust matrix, draft states, fail-closed quarantine, path traversal)
  - `tests/api/test_file_api.py` (9 REST API & Web integration tests)
- **Verification commands and results:**
  - `python scripts/repo_check.py`: PASS (71 CREATE TABLE statements confirmed, markdown fences balanced)
  - `python -m compileall -q src tests scripts`: PASS (Clean compilation)
  - `ruff check src tests scripts`: PASS (All checks passed!)
  - `ruff format --check src tests scripts`: PASS (122 files formatted)
  - `mypy src`: PASS (Success: no issues found in 61 source files)
  - `pytest` TASK-018 test suites: PASS (29/29 passed in 9.19s)
  - `python -m pytest`: PASS (500/500 passed in 227.70s)
  - `./scripts/verify.ps1`: PASS (`PWD301 verification PASS`)

## TASK-019 — File Security, Quarantine Isolation & Malware Scanning Engine
- **Completion date:** 2026-09-10
- **Important files changed:**
  - `src/pwd301/services/scanner_service.py` (Multi-tier scanner architecture: `BuiltinHeuristicScanner` with longest-prefix priority for EICAR, deep PDF streams, OOXML macros, embedded binaries, header spoofing; `ClamAVScanner` fail-closed TCP socket communication via `nINSTREAM` protocol; aggregate scanning via `scan_file_all_engines` and `scan_blob_file`)
  - `src/pwd301/services/file_service.py` (Quarantine isolation workflow, clean blob promotion to hierarchical storage `storage/blobs/ab/cd/<sha256>`, threat isolation into `quarantine/infected/<sha256>`, fail-closed download denial with 403 `FileSecurityQuarantineError` and `FileInfectedError`, rescan engine, scan history retrieval, and admin quarantine override with `AuditEvent` audit logging)
  - `src/pwd301/__init__.py` (Registered `admin_bp` alias at `/api/admin` with CSRF exemption for JWT API requests)
  - `src/pwd301/blueprints/api_files/routes.py` (`GET /api/files/<asset_id>/scans`, `GET /api/files/<asset_id>/scan-results`, `POST /api/files/<asset_id>/rescan`, `POST /api/files/<asset_id>/quarantine-override`)
  - `src/pwd301/blueprints/admin/routes.py` (`POST /admin/files/<asset_id>/quarantine-override`)
  - `tests/unit/test_malware_scan_service.py` (11 unit tests for EICAR, clean files, PDF dangerous objects, OOXML macros, zip embedded payloads, header mismatches, ClamAV fail-closed & mock protocol, storage promotion, infected isolation)
  - `tests/security/test_quarantine_fail_closed.py` (11 security tests for student blocked on quarantined/infected, unauthenticated blocked, foreign instructor IDOR blocked, path traversal isolation, admin override authorization and audit logging)
  - `tests/api/test_scan_api.py` (13 REST API integration tests for scan history, scan-results alias, rescan, and quarantine override across `/api/files/`, `/api/admin/files/`, and `/admin/files/`)
- **Verification commands and results:**
  - `python scripts/repo_check.py`: PASS (71 CREATE TABLE statements confirmed, markdown fences balanced)
  - `python -m compileall -q src tests scripts`: PASS (Clean compilation)
  - `ruff check src tests scripts`: PASS (All checks passed!)
  - `ruff format --check src tests scripts`: PASS (126 files formatted)
  - `mypy src`: PASS (Success: no issues found in 62 source files)
  - `pytest` TASK-019 test suites: PASS (35/35 passed in 13.53s)
  - `python -m pytest`: PASS (535/535 passed in 324.76s)
  - `./scripts/verify.ps1`: PASS (`PWD301 verification PASS`, 535/535 passed in 299.47s)

## TASK-020 — DOCX/PDF Assessment & Question Import Engine
- **Completion date:** 2026-09-10
- **Important files changed:**
  - `src/pwd301/services/exceptions.py` (Added `DocumentImportError`, `DocumentParsingError`, `DocumentImportJobNotFoundError`, `DocumentImportStateViolationError`, `ImportQuestionNotFoundError`)
  - `src/pwd301/__init__.py` (Registered exception handlers, registered `api_import_bp`, added CSRF exemption for `/api/imports`)
  - `src/pwd301/models/file_import.py` (Added synthetic UUID `public_id` properties to `ImportQuestion` and `ImportDuplicateCandidate` conforming to ADR-002)
  - `src/pwd301/services/import_service.py` (Full implementation of OpenXML DOCX extraction, PDF resilient extraction with fallback, regex pattern matching across all 5 question types, Bloom taxonomy and points tagging, confidence scoring with diagnostic warnings, exact SHA-256 and SequenceMatcher fuzzy duplicate detection, review and atomic transaction commit into Question Bank, cancellation engine, and ADR-002 serialization)
  - `src/pwd301/blueprints/api_import/` (`__init__.py`, `routes.py`: REST API endpoints for import lifecycle: create, get details, process on-demand, patch question, set decision, commit, and cancel)
  - `src/pwd301/blueprints/api_courses/routes.py` (`POST /api/courses/<course_id>/imports`, `GET /api/courses/<course_id>/imports`)
  - `src/pwd301/blueprints/instructor/routes.py` (Web session endpoints with CSRF protection for instructor import workflows)
  - `tests/unit/test_import_service.py` (8 unit tests for document extraction, pattern matcher, confidence scoring, duplicate detection, lifecycle transitions, and rollback safety)
  - `tests/security/test_import_idor.py` (8 security and IDOR tests for fail-closed quarantine and malware rejection, cross-course file rejection, instructor authorization, student forbidden, admin platform access, and ADR-002 zero PK leakage)
  - `tests/api/test_import_api.py` (9 REST API and web integration tests for full end-to-end import lifecycle, idempotency, direct API, process endpoint, and instructor portal)
- **Verification commands and results:**
  - `python scripts/repo_check.py`: PASS (71 CREATE TABLE statements confirmed, markdown fences balanced)
  - `python -m compileall -q src tests scripts`: PASS (Clean compilation)
  - `ruff check src tests scripts`: PASS (All checks passed!)
  - `ruff format --check src tests scripts`: PASS (132 files already formatted)
  - `mypy src`: PASS (Success: no issues found in 65 source files)
  - `pytest` TASK-020 test suites: PASS (25/25 passed in 7.29s)
  - `python -m pytest`: PASS (560/560 passed in 244.60s)
  - `./scripts/verify.ps1`: PASS (`PWD301 verification PASS`)

## TASK-021 — Notifications & Email Delivery/Retry Engine
- **Completion date:** 2026-09-10
- **Important files changed:**
  - `src/pwd301/services/exceptions.py` (Added `NotificationError`, `NotificationNotFoundError`, `NotificationPreferenceError`, `MandatoryNotificationOptOutError`, `EmailDeliveryError`, `EmailDeliveryNotFoundError`, `EmailRateLimitExceededError`)
  - `src/pwd301/models/notification_audit.py` (`NotificationEvent`, `Notification`, `NotificationPreference`, `EmailDelivery` with ADR-002 `public_id` and zero internal PK leakage)
  - `src/pwd301/services/email_service.py` (Outbox queue, exponential backoff retry engine, MockMailClient, admin manual retry)
  - `src/pwd301/services/notification_service.py` (Decoupled event emitter, automated payload redaction, category resolver, dispatch engine, preference manager with mandatory security invariants, broadcast engine)
  - `src/pwd301/blueprints/api_notifications/` (REST API with `@jwt_required`: list, unread-count, read, mark-all-read, dismiss, preferences, broadcast, email retry)
  - `src/pwd301/templates/notifications/`, `src/pwd301/templates/base.html`, `src/pwd301/blueprints/student/routes.py` (Student notifications Web UI with unread badge and pagination)
  - `src/pwd301/blueprints/admin/routes.py` (Admin broadcast and email retry triggers)
  - `tests/unit/test_notification_service.py` (10 tests)
  - `tests/unit/test_email_service.py` (8 tests)
  - `tests/security/test_notification_idor.py` (7 tests)
  - `tests/api/test_notification_api.py` (7 tests)
- **Verification commands and results:**
  - `python scripts/repo_check.py`: PASS
  - `python -m compileall -q src tests scripts`: PASS
  - `ruff check src tests scripts`: PASS
  - `ruff format --check src tests scripts`: PASS
  - `mypy src`: PASS
  - `pytest` TASK-021 test suites: PASS (32/32 passed)
  - `python -m pytest`: PASS (592/592 passed)
  - `./scripts/verify.ps1`: PASS (`PWD301 verification PASS`)

## TASK-022 — Audit Logging Engine & Sensitive Admin Actions
- **Completion date:** 2026-09-10
- **Important files changed:**
  - `src/pwd301/services/exceptions.py` (Added `AuditError`, `AuditPersistenceError`, `AuditNotFoundError`, `AdminActionForbiddenError`)
  - `src/pwd301/__init__.py` (Centralized error handlers for audit domain exceptions, isolated CSRF exemption for `/api/admin` Bearer JWT requests)
  - `src/pwd301/models/notification_audit.py` (`AuditEvent.public_id`, `actor` joined relationship, `AuditEvent.to_dict()` strictly adhering to ADR-002 zero internal PK leakage)
  - `src/pwd301/services/audit_service.py` (Recursive sensitive data redaction, append-only immutable audit recording, fail-closed persistence guarantees, query engine with multi-field filtering and pagination, atomic user suspension, unsuspension, and forced session revocation)
  - `src/pwd301/blueprints/admin/routes.py` (`GET /audit-logs`, `GET /audit-logs/<audit_id>`, `POST /users/<user_id>/suspend`, `POST /users/<user_id>/unsuspend`, `POST /users/<user_id>/revoke-sessions`)
  - `src/pwd301/templates/admin/audit_logs.html` (Administrative audit trail UI with filter bar, responsive table, expandable before/after state diffs, pagination)
  - `tests/unit/test_audit_service.py` (11 unit tests for redaction, recording, correlation ID, queries, suspension, unsuspension, revocation, fail-closed rollback, self-suspension guard)
  - `tests/security/test_audit_security.py` (5 security and IDOR tests for student/instructor 403, unauthenticated 401, append-only 405 immutability, ADR-002 zero PK leakage)
  - `tests/api/test_admin_audit_api.py` (6 REST API and integration tests for suspend, unsuspend, revoke-sessions, audit log query/detail, web UI rendering, CSRF enforcement)
- **Verification commands and results:**
  - `python scripts/repo_check.py`: PASS (71 CREATE TABLE statements confirmed, markdown fences balanced)
  - `python -m compileall -q src tests scripts`: PASS (Clean compilation)
  - `ruff check src tests scripts`: PASS (All checks passed!)
  - `ruff format --check src tests scripts`: PASS (144 files already formatted)
  - `mypy src`: PASS (Success: no issues found in 70 source files)
  - `pytest` TASK-022 test suites: PASS (22/22 passed in 11.23s)
  - `python -m pytest`: PASS (614/614 passed in 318.62s)
  - `./scripts/verify.ps1`: PASS (`PWD301 verification PASS`, 614/614 passed)

## TASK-023 — Gemini Integration & Backend Rule Recommendation Engine
- **Completion date:** 2026-09-10
- **Important files changed:**
  - `src/pwd301/config.py` (Added `GEMINI_API_KEY`, `GEMINI_MODEL_NAME`, `GEMINI_TIMEOUT_SECONDS`, `AI_CHAT_INACTIVITY_SECONDS`)
  - `src/pwd301/services/exceptions.py` (Added `AIError`, `AIValidationError`, `AIPromptInjectionError`, `AIConversationNotFoundError`, `AIConversationExpiredError`, `AIQuotaExceededError`, `AIServiceUnavailableError`, `AIDraftNotFoundError`)
  - `src/pwd301/models/ai_rag.py` (ADR-002 Zero Internal PK Leakage: `public_id`, `resolve_id_from_public_id`, `is_expired`, deterministic bijective UUID mapping, `to_dict()` methods for `AIConversation`, `AIMessage`, `AIRequest`, `AIGeneratedQuestionDraft`)
  - `src/pwd301/services/gemini_service.py` (Real Gemini API client via stdlib `urllib.request`, deterministic offline `MockGeminiClient`, fault injection, prompt sanitization, adversarial prompt injection defense, token estimation, telemetry logging into `ai_requests` with bounded transactions and zero secrets logging)
  - `src/pwd301/services/recommendation_service.py` (Algorithm 14 hybrid course recommendation: candidate filtering excluding active/completed/archived/unmet prerequisites, scoring with beginner +15/+30, category match +30, progression +20, prerequisites met +25, Gemini explanation enrichment, graceful degradation fallback)
  - `src/pwd301/services/ai_service.py` (AI question drafting with instructor/admin authorization, structured question drafting persisted in `ai_generated_question_drafts` in `PENDING` state, conversation lifecycle with 300s inactivity deadline, message exchange, automated purge engine)
  - `src/pwd301/blueprints/api_ai/__init__.py` & `src/pwd301/blueprints/api_ai/routes.py` (REST API with `@jwt_required`: `/recommendations`, `/questions/draft`, `/questions/generate`, `/questions/drafts`, `/conversations`, `/conversations/<id>`, `/conversations/<id>/messages`, `/chat`, `/conversations/cleanup`)
  - `src/pwd301/__init__.py` (Registered `api_ai_bp`, CSRF exemption for Bearer token AI API endpoints, registered AI domain exceptions in `DOMAIN_EXCEPTION_HANDLERS`)
  - `tests/unit/test_ai_service.py` (11 unit tests)
  - `tests/unit/test_recommendation_service.py` (6 unit tests)
  - `tests/security/test_ai_security.py` (4 security & IDOR tests)
  - `tests/api/test_ai_api.py` (6 API integration tests)
- **Verification commands and results:**
  - `python scripts/repo_check.py`: PASS (71 CREATE TABLE statements confirmed, markdown fences balanced)
  - `python -m compileall -q src tests scripts`: PASS (0 syntax errors)
  - `ruff check src tests scripts`: PASS (All checks passed!)
  - `ruff format --check src tests scripts`: PASS (153 files already formatted)
  - `mypy src`: PASS (Success: no issues found in 75 source files)
  - `pytest` TASK-023 test suites: PASS (27/27 passed in 8.29s)
  - `python -m pytest`: PASS (641/641 passed in 280.48s, 0 regressions)
  - `./scripts/verify.ps1`: PASS (`PWD301 verification PASS`, 641/641 passed)

## TASK-024 — RAG Knowledge Lifecycle, Semantic Retrieval & AI Security Fortress
- **Completion date:** 2026-09-10
- **Important files changed:**
  - `src/pwd301/models/ai_rag.py` (ADR-002 zero internal PK leakage with deterministic UUID prefixes `0xAA...03` for chunks and `0xAA...04` for usages; enhanced `KnowledgeDocument`, `KnowledgeChunk`, `AISourceUsage`, and `KnowledgeEmbedding` with `public_id`, `resolve_id_from_public_id`, and `to_dict()`; added `KnowledgeSource = KnowledgeDocument` alias)
  - `src/pwd301/services/exceptions.py` (Domain exceptions for RAG knowledge lifecycle, fail-closed quarantine enforcement, and pre-retrieval access control)
  - `src/pwd301/services/gemini_service.py` (Added `answer_rag_query` to `GeminiClientBase` and implemented in `MockGeminiClient` with deterministic `[Ref: <UUID>]` citations and in `RealGeminiClient`)
  - `src/pwd301/services/rag_service.py` (Implemented sliding-window token chunking with sentence preservation and SHA-256 hash; lesson content ingestion with state machine lifecycle and version invalidation; fail-closed course file ingestion rejecting unscanned/quarantined files; pre-retrieval authorization scoping for students/instructors; archived/trashed course exclusion; hybrid lexical-semantic retrieval; SEC-006 context boundary formatting `<retrieved_context>` with prompt injection screening; telemetry tracking in `ai_requests` and `ai_source_usages`)
  - `src/pwd301/blueprints/api_ai/routes.py` (Added endpoints: `POST /api/ai/courses/<course_id>/ingest`, `POST /api/ai/lessons/<lesson_id>/ingest`, `POST /api/ai/courses/<course_id>/query`, `GET /api/ai/courses/<course_id>/sources`, `DELETE /api/ai/sources/<source_id>`)
  - `tests/unit/test_rag_service.py` (5 unit tests covering chunking bounds, sentence preservation, SHA-256 hashes, lesson ingestion, fail-closed file quarantine, version invalidation, SEC-006 prompt formatting, citation parsing)
  - `tests/security/test_ai_security.py` (Added 4 security tests: unenrolled student RAG rejection, archived course exclusion, context boundary untrusted data defusing, ADR-002 zero PK leakage across RAG responses)
  - `tests/api/test_ai_api.py` (Added 2 integration tests: full course RAG flow with ingestion and query, instructor course permission enforcement)
- **Verification commands and results:**
  - `python scripts/repo_check.py`: PASS (71 CREATE TABLE statements confirmed, markdown fences balanced)
  - `python -m compileall -q src tests scripts`: PASS (0 syntax errors)
  - `ruff check src tests scripts`: PASS (All checks passed!)
  - `ruff format --check src tests scripts`: PASS (155 files already formatted)
  - `mypy src`: PASS (Success: no issues found in 76 source files)
  - `pytest tests/unit/test_rag_service.py tests/security/test_ai_security.py tests/api/test_ai_api.py`: PASS (21/21 passed in 8.67s)
  - `python -m pytest`: PASS (652/652 passed in 286.40s, 0 regressions)
  - `./scripts/verify.ps1`: PASS (`PWD301 verification PASS`, 652/652 passed)

## TASK-025 — Dashboards, Learning Analytics & Performance Optimization Engine
- **Completion date:** 2026-09-10
- **Important files changed:**
  - `src/pwd301/services/analytics_service.py` (High-performance SQL-level aggregate functions: `get_admin_system_overview`, `get_instructor_overview_analytics`, `get_instructor_course_analytics`, `get_student_learning_overview`; $O(1)$ single query aggregations, zero-division resilience, 4-bucket score distribution, server-authoritative score release enforcement)
  - `src/pwd301/services/__init__.py` (Exported analytics service functions in imports and `__all__`)
  - `src/pwd301/blueprints/admin/routes.py` (Updated `GET /admin/dashboard` and added `GET /api/admin/analytics/overview`)
  - `src/pwd301/blueprints/instructor/routes.py` (Updated `GET /instructor/dashboard` and added `GET /instructor/courses/<course_id>/analytics`)
  - `src/pwd301/blueprints/api_courses/routes.py` (Added `GET /api/courses/<course_id>/analytics` with `@jwt_required` and instructor authorization)
  - `src/pwd301/blueprints/student/routes.py` (Updated `GET /student/dashboard` with `get_student_learning_overview`)
  - `src/pwd301/blueprints/api_student/routes.py` (Added `GET /api/student/analytics/overview` with `@student_required`)
  - `tests/unit/test_analytics_service.py` (6 unit tests: admin overview, zero-division edge cases, 4-bucket distribution, assessment performance, student upcoming deadlines & score release policy)
  - `tests/security/test_analytics_idor.py` (6 security and IDOR tests: cross-instructor 403, student access rejection 403, unauthenticated 401, student data isolation, ADR-002 zero internal PK leakage)
  - `tests/api/test_analytics_api.py` (3 integration tests: admin overview API, instructor course analytics Web/API, student learning overview API)
- **Verification commands and results:**
  - `python scripts/repo_check.py`: PASS (71 CREATE TABLE statements confirmed, markdown fences balanced)
  - `python -m compileall -q src tests scripts`: PASS (0 syntax errors)
  - `ruff check src tests scripts`: PASS (All checks passed!)
  - `ruff format --check src tests scripts`: PASS (159 files already formatted)
  - `mypy src`: PASS (Success: no issues found in 77 source files)
  - `pytest tests/unit/test_analytics_service.py tests/security/test_analytics_idor.py tests/api/test_analytics_api.py`: PASS (15/15 passed)
  - `python -m pytest`: PASS (667/667 passed in 293.83s, 0 regressions)


