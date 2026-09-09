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


