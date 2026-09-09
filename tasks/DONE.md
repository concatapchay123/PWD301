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


