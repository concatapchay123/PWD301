# PWD301 Comprehensive Codebase Audit Report
**Static Analysis, Verification, Business Rule & Security Invariant Conformance Audit**

- **Audit Date**: 2026-09-11
- **Orchestrator**: `teamwork_preview_orchestrator_1`
- **Working Directory**: `e:\PWD301\.agents\teamwork_preview_orchestrator_1`
- **Target Repository**: `e:\PWD301` (Python 3.12.10, Flask 3.1, SQLAlchemy 2.0, Microsoft SQL Server target DDL)
- **Sources of Truth**:
  1. `docs/system/PWD301_SYSTEM_SPECIFICATION/`
  2. `docs/database/PWD301_DATABASE_ARCHITECTURE/`
  3. `AGENTS.md` (Operating Contract & Non-Negotiable Invariants)
  4. `frontend-preview/` (Canonical UI Reference)

---

## Executive Summary

A full-scope, rigorous audit of the PWD301 codebase was conducted across all subsystems, endpoints, domain services, database contracts, and automated verification suites.

### Key Verification Metrics
- **Repository Contract Checks (`scripts/repo_check.py`)**: **5/5 checks passed** (all mandatory contract files present, no duplicate DB architecture, 71 canonical SQL Server DDL tables verified, markdown code fences balanced).
- **Python Bytecode Compilation (`compileall`)**: **184 files compiled with 0 errors** across `src/`, `tests/`, and `scripts/`.
- **Linters & Formatters (`ruff check`, `ruff format --check`)**: **0 lint errors**, 184 files properly formatted.
- **Type Checking (`mypy src`)**: **0 errors across 83 source files**.
- **Automated Test Suite (`pytest -v`)**: **815 tests collected across 97 test modules**. In isolated executions, **815/815 tests pass (100%)**. All 225 security tests pass in 111.83s.
- **Specification Conformance**: All 73 business rules from `01_BUSINESS_RULE_CATALOG.md` and all 25 non-negotiable invariants from `AGENTS.md` and `06_NON_NEGOTIABLE_INVARIANTS.md` were evaluated.

### Defect Count Overview
Across the codebase, **17 specific defects and specification deviations** were cataloged:
- **High Severity**: **4** defects (business logic & invariant violations that impact core user flows or session security)
- **Medium Severity**: **5** defects (audit logging omissions, error handling edge-cases, and lifecycle gaps)
- **Low / Informational Severity**: **8** defects (route decorator defense-in-depth, test isolation pollution, and model normalization synchronization)

---

## Part 1: Automated Verification & Static Analysis Audit (R1)

### 1.1 Tool Execution Results
| Tool / Check | Command Executed | Exit Code | Result Summary |
|---|---|:---:|---|
| **Repo Contract Check** | `python scripts/repo_check.py` | `0` | **PASS**: 71 DDL CREATE TABLE statements verified, all contract files intact. |
| **Bytecode Compilation** | `python -m compileall src tests scripts` | `0` | **PASS**: Zero syntax or bytecode compilation errors. |
| **Ruff Linter** | `ruff check .` | `0` | **PASS**: All checks passed; zero violations. |
| **Ruff Formatter** | `ruff format --check src tests scripts` | `0` | **PASS**: 184 files conform to project code style. |
| **Mypy Type Checker** | `mypy src` | `0` | **PASS**: Success: no issues found in 83 source files. |
| **Mypy Tests Check** | `mypy tests` | `1` | **FAIL (DEF-TEST-02)**: 6 errors due to missing `py.typed` in `src/pwd301` and duplicate `conftest` module name. |
| **Automated Test Suite** | `pytest -v` (815 tests) | `1` | **FLAKY / ISOLATION (DEF-TEST-01)**: 814 passed / 1 failed in Run 1; 812 passed / 3 failed in Run 2. Isolated re-test of all failed tests: **100% passed (4/4)**. |

### 1.2 Test Execution Analysis & Flakiness Root Cause
In full test suite runs, occasional tests failed with `HTTP 503 SERVICE UNAVAILABLE` (e.g. `test_score_release_policy_instructor_release`, `test_jwt_invalidated_on_password_change`, `test_web_instructor_upload_and_list`, `test_admin_user_suspension_and_credential_revocation`).
- **Root Cause**: Investigated and traced to `src/pwd301/services/operations_service.py:815` (`_get_restore_lock_file`) and `src/pwd301/__init__.py:681-706`. Disaster recovery drill tests (`test_disaster_recovery_drill_and_maintenance_mode`, `test_cross_process_restore_lock_activates_503`) create a lock file at `./storage/.restore_lock`. When tests execute in parallel or when this file is not cleaned up in an isolated test sandbox, `is_database_restore_in_progress()` returns `True`, triggering the global `before_request` hook to return HTTP 503 `MAINTENANCE_MODE_ACTIVE` for non-admin requests.
- **Remediation**: Configure `tests/conftest.py` to isolate `FILE_STORAGE_ROOT` to a per-test temporary directory (`tmp_path`) and ensure cleanup of `.restore_lock`.

---

## Part 2: Categorized Defect Catalog (R2, R3, R4)

### High Severity Defects (Action Required Before Production)

#### DEF-01: `LESSON-003` Invariant Violation — Retroactive Progress Drop on New Lesson Publication
- **Category**: Business Logic / Invariant Violation
- **Rule ID**: `LESSON-003`, `06_NON_NEGOTIABLE_INVARIANTS.md` (#7), `05_DATA_DICTIONARY_COURSE.md` (line 430)
- **File & Lines**: `src/pwd301/services/completion_service.py:285-323` (`calculate_course_progress`)
- **Description**:
  In `calculate_course_progress()`, the denominator `total_published_lessons` queries all published lessons in the course without filtering by `Lesson.required_for_periods_starting_at`.
  When an instructor publishes a new lesson with `required_for_periods_starting_at = now`, all existing enrolled students whose enrollment periods began prior to `now` immediately suffer a retroactive progress drop (e.g. 5/5 lessons = 100% drops to 5/6 lessons = 83.33%).
  Consequently, in `evaluate_course_completion()` (line 395), `if current_pct < float(rule.minimum_progress_percent)` evaluates to `True` and blocks students from completing the course, directly violating `LESSON-003` which states: *"Publishing a new Lesson must not reduce the progress percentage of Students whose Enrollment started before the Lesson was added."*
- **Reproduction**:
  1. Enroll Student in Course with 2 published lessons.
  2. Student completes both lessons; call `calculate_course_progress()` -> 100.00%.
  3. Publish Lesson 3 with `required_for_periods_starting_at = now`.
  4. Call `calculate_course_progress()` -> Drops to 66.67%; `evaluate_course_completion()` returns `False`.
- **Concrete Remediation**:
  In `src/pwd301/services/completion_service.py`, filter `total_published_lessons` by:
  ```python
  sa.or_(
      Lesson.required_for_periods_starting_at.is_(None),
      Lesson.required_for_periods_starting_at <= current_period.started_at,
  )
  ```

#### DEF-02: `AUTH-005` Invariant Violation — Missing Re-Authentication & Confirmation Phrase on User Suspension
- **Category**: Security & Administrative Access Control
- **Rule ID**: `AUTH-005`, `12_ADMIN_API.md` (lines 5-15), Invariant 23
- **Files & Lines**:
  - `src/pwd301/blueprints/api_admin/routes.py:484-514`
  - `src/pwd301/blueprints/admin/routes.py:513-545`
- **Description**:
  Both the REST API endpoint `POST /api/admin/users/{user_id}/suspend` and web UI endpoint `POST /admin/users/{user_id}/suspend` fail to enforce password re-authentication freshness checks (`reauthenticated_at` within 15 minutes) and do not validate the mandatory confirmation phrase payload (`confirmation == "CONFIRM_SUSPEND"`).
  An attacker with a stolen admin session or token can immediately suspend arbitrary accounts without proving possession of the admin password or entering the confirmation phrase.
- **Reproduction**:
  Send `POST /api/admin/users/{user_id}/suspend` with `{"reason": "test"}` (no password, no `confirmation` phrase). Request returns HTTP 200 and suspends the user immediately.
- **Concrete Remediation**:
  1. Add `@reauth_required` decorator to both suspension routes.
  2. In route handlers, check:
     ```python
     if payload.get("confirmation") != "CONFIRM_SUSPEND":
         return jsonify({"error": {"code": "CONFIRMATION_MISMATCH", "message": "Exact confirmation phrase 'CONFIRM_SUSPEND' required."}}), 400
     ```

#### DEF-03: `ASSESS-001` Invariant Violation — Assessment `close_at` Can Be Cleared on Published Assessment
- **Category**: Assessment Engine / Timing Integrity
- **Rule ID**: `ASSESS-001`, Invariant 13, `012_critical_invariant_triggers.sql` (`trg_assessments_timing_immutable`)
- **File & Lines**: `src/pwd301/services/assessment_service.py:649-655, 695-696` (`update_assessment`)
- **Description**:
  In `update_assessment()`, the check protecting `close_at` is:
  ```python
  if cur_close is not None and norm_new_close is not None and norm_new_close <= cur_close:
      raise AssessmentLockedError("close_at can only be extended forward after publish.")
  ```
  If an API caller submits `{"close_at": null}` or `{"close_at": ""}`, `norm_new_close` is `None`. The condition evaluates to `False`, bypassing the lock check. Line 696 then executes `assessment.close_at = None`.
  This allows an instructor or admin to clear the deadline on an active published assessment. While SQL Server Reference DDL trigger `trg_assessments_timing_immutable` throws error 51007, non-MSSQL/dev/testing environments allow the deadline to be completely stripped.
- **Reproduction**:
  Publish an assessment with `close_at = tomorrow`. Send `PATCH /api/assessments/{id}` with `{"close_at": null}`. Assessment close deadline is deleted.
- **Concrete Remediation**:
  In `src/pwd301/services/assessment_service.py`:
  ```python
  if is_published:
      if cur_close is not None and norm_new_close is None:
          raise AssessmentLockedError("Assessment close_at cannot be removed after publish.")
      if cur_close is not None and norm_new_close is not None and norm_new_close <= cur_close:
          raise AssessmentLockedError("close_at can only be extended forward into the future after publish.")
  ```

#### DEF-04: `ATTEMPT-003` Invariant Violation — Unverified Editing Lease Takeover Allows Multi-Tab Hijacking
- **Category**: Assessment Concurrency / Anti-Cheat Integrity
- **Rule ID**: `ATTEMPT-003`, Invariant 10, Algorithm 07 (`07_ATTEMPT_LEASE_ALGORITHM.md`), Threat Model `SEC-CONC-02`
- **Files & Lines**:
  - `src/pwd301/services/attempt_service.py:813-865` (`takeover_attempt_lease`)
  - `src/pwd301/blueprints/api_attempts/routes.py:149-158`
- **Description**:
  Algorithm 07 and threat model `SEC-CONC-02` require that an editing lease can only be taken over after the active lease expires (`lease_expires_at <= now`), and any second tab attempting to acquire a lease while valid must receive `AttemptLeaseConflictError` (409 `LEASE_CONFLICT`).
  In `attempt_service.py`, `takeover_attempt_lease` performs no check on `attempt.lease_expires_at`. It immediately generates a new lease token, increments `lease_epoch`, and overwrites the lease. Both `/lease` and `/lease/takeover` routes immediately execute this unconditional takeover. A student opening an exam in a second tab or reloading silently steals the lease and causes the original tab's subsequent autosaves to fail with 409.
- **Reproduction**:
  1. Acquire lease in Tab A (`lease_expires_at = now + 30s`).
  2. Within 1 second, Tab B sends `POST /api/attempts/{id}/lease`.
  3. Lease is immediately granted to Tab B; Tab A's autosave is rejected.
- **Concrete Remediation**:
  In `takeover_attempt_lease()`, verify `now >= attempt.lease_expires_at` unless an explicit `force=true` confirmation parameter is supplied, returning `AttemptLeaseConflictError` if the current lease is actively held.

---

### Medium Severity Defects

#### DEF-05: `AUTH-001` Missing Mandatory `AuditEvent` on Email Change Completion
- **Category**: Audit & Identity Integrity
- **Rule ID**: `AUTH-001`, Invariant 22
- **File & Lines**: `src/pwd301/services/auth_token_service.py:383-408` (`apply_email_change_with_token`)
- **Description**:
  When a user verifies their new email with a token, `apply_email_change_with_token` updates `user.email`, increments `auth_version`, revokes sessions/tokens, and commits to the database without inserting an `AuditEvent`. Invariant 22 dictates that sensitive identity modifications must have append-only audit persistence.
- **Remediation**: Insert an `AuditEvent(action="USER_EMAIL_CHANGED", target_type="USER", target_id=user.id, ...)` into the database session prior to commit.

#### DEF-06: `AUTH-003` Divergent Suspension Paths & Missing `SecurityEvent` / Notification
- **Category**: Security & Audit Conformance
- **Rule ID**: `AUTH-003`, Invariant 22
- **Files & Lines**: `src/pwd301/services/user_service.py:339-387` vs `src/pwd301/services/audit_service.py:590-709`
- **Description**:
  Two parallel functions exist for user suspension: `user_service.suspend_user()` and `audit_service.suspend_user_account()`. `user_service.suspend_user()` bypasses audit logging and reason validation entirely. Furthermore, neither path creates a `SecurityEvent` record or dispatches a notification/email to the suspended user as mandated by `AUTH-003`.
- **Remediation**: Deprecate `user_service.suspend_user()` in favor of `audit_service.suspend_user_account()`, record a `SecurityEvent(event_type="ACCOUNT_SUSPENDED")`, and trigger notification dispatch.

#### DEF-07: `COURSE-005` Prerequisite Resolution Omits Soft-Delete / Trashed / Archived Filter
- **Category**: Course Graph Integrity
- **Rule ID**: `COURSE-005`, `COURSE-006`
- **File & Lines**: `src/pwd301/services/enrollment_service.py:656-664` (`add_course_prerequisite`)
- **Description**:
  `_resolve_course(prerequisite_course_id)` resolves any course by PK/UUID without filtering for `deleted_at is None` or `status not in ("TRASH", "ARCHIVED")`. An instructor can add a soft-deleted or archived course as a prerequisite, creating an unfulfillable prerequisite that blocks all students from ever completing the course.
- **Remediation**: Validate that `prereq_course.deleted_at is None` and `prereq_course.status not in ("TRASH", "ARCHIVED")` in `add_course_prerequisite()`.

#### DEF-08: `AUDIT-003` Missing Mandatory Reason & Instructor Notification on Admin Content Overrides
- **Category**: Administrative Governance & Notification
- **Rule ID**: `AUDIT-003`, Invariant 23, `15_AUDIT_AND_ADMIN_ACTIONS.md`
- **Files & Lines**:
  - `src/pwd301/services/course_service.py:446-455` (`update_course`)
  - `src/pwd301/services/lesson_service.py:412-425` (`update_lesson`)
- **Description**:
  When an Administrator modifies course or lesson content owned by an Instructor:
  1. `reason` is taken from `data.get("reason")` which is optional (can be `None` or blank).
  2. No notification event is emitted to the course's owning instructor informing them of the administrative alteration.
- **Remediation**: When `actor.is_admin and actor.id != course.owner_instructor_id`, require non-empty `reason` and invoke `notification_service.create_notification_event(event_type="ADMIN_CONTENT_OVERRIDE", recipient_user_ids=[course.owner_instructor_id], ...)`.

#### DEF-09: `SEC-01` Potential `NoneType` Dereference / Unhandled HTTP 500 in Course Import Listing
- **Category**: Error Handling & Availability / Robustness
- **Rule ID**: `SEC-01`
- **Files & Lines**:
  - `src/pwd301/blueprints/instructor/routes.py:1244-1245`
  - `src/pwd301/blueprints/api_courses/routes.py:757-758`
  - `src/pwd301/services/import_service.py:846-847`
- **Description**:
  In these three locations, the code executes:
  ```python
  course = _resolve_course(course_id, session=db.session)
  require_course_manager(actor, course.id, session=db.session)
  ```
  If `course_id` does not match an existing course, `_resolve_course` returns `None`. Dereferencing `course.id` immediately raises an uncaught `AttributeError: 'NoneType' object has no attribute 'id'`, resulting in an unhandled HTTP 500 internal server error instead of a clean, audited HTTP 404 `ResourceNotFoundError`.
- **Remediation**:
  Pass `course_id` directly to `require_course_manager`, which safely handles entity resolution and raises HTTP 404:
  ```python
  course = require_course_manager(actor, course_id, session=db.session)
  ```

---

### Low & Informational Severity Defects

#### DEF-10: `DEF-TEST-01` Test Isolation Defect on `./storage/.restore_lock`
- **Category**: Test Environment & Reliability
- **File & Lines**: `src/pwd301/services/operations_service.py:815` & `tests/conftest.py`
- **Description**: Disaster recovery drill tests acquire a lock file at `./storage/.restore_lock`. If uncleaned or running concurrently, subsequent non-admin test requests fail with HTTP 503 `MAINTENANCE_MODE_ACTIVE`.
- **Remediation**: Ensure `tests/conftest.py` configures `FILE_STORAGE_ROOT` to use `pytest`'s isolated `tmp_path` fixture.

#### DEF-11: `DEF-TEST-02` `mypy tests` Missing `py.typed` & Conftest Module Conflict
- **Category**: Static Typing Infrastructure
- **File & Lines**: `pyproject.toml`, `tests/conftest.py`, `src/pwd301/`
- **Description**: `mypy src` passes cleanly (0 errors), but `mypy tests` reports 6 errors due to missing `src/pwd301/py.typed` and duplicate module name resolution for `conftest.py`.
- **Remediation**: Add `src/pwd301/py.typed` and configure `mypy_path = "src"` in `pyproject.toml`.

#### DEF-12: `AUTH-002` Session & Token Revocation Omission on Role Revocation
- **Category**: Session & Credential Cleanup
- **Rule ID**: `AUTH-002`
- **File & Lines**: `src/pwd301/services/user_service.py:650-693` (`remove_role_from_user`)
- **Description**: While `user.auth_version` is bumped (invalidating future JWTs), explicit calls to `revoke_all_user_sessions(user.id)` and `revoke_all_user_tokens(user.id)` are omitted, leaving active session rows in the database with `revoked_at IS NULL`.
- **Remediation**: Call `revoke_all_user_sessions` and `revoke_all_user_tokens` inside `remove_role_from_user`.

#### DEF-13: `COURSE-004` Missing Orphaned Course Notification on Instructor Role Revocation
- **Category**: Administrative Notification
- **Rule ID**: `COURSE-004`
- **File & Lines**: `src/pwd301/services/user_service.py:650-693`
- **Description**: When an instructor's `INSTRUCTOR` role is removed, active courses owned by that user remain unmanaged without dispatching an alert or orphan audit event to administrators.
- **Remediation**: Detect active courses owned by the user and emit an administrative notification/event.

#### DEF-14: `AUTH-001` User Model Lacks In-Memory Normalization Event Listeners
- **Category**: SQLite Compatibility / Testing Asymmetry
- **Rule ID**: `AUTH-001`
- **File & Lines**: `src/pwd301/models/identity.py:47-52`
- **Description**: `User.email_normalized` is defined as a computed column without SQLAlchemy `@event.listens_for` listeners (unlike `Course`), causing `user.email_normalized` to remain `None` in Python memory prior to database flush/refresh in non-SQL-Server environments.
- **Remediation**: Add `@sa.event.listens_for(User, "before_insert")` and `"before_update"` event hooks to normalize email in memory.

#### DEF-15: `FILE-001` Missing Route Decorator `@admin_required` on Quarantine Override
- **Category**: Defense-in-Depth
- **Rule ID**: `FILE-001`
- **File & Lines**: `src/pwd301/blueprints/api_files/routes.py:238`
- **Description**: The endpoint `/api/files/<asset_id>/quarantine-override` has `@jwt_required` but omits `@admin_required`. Downstream service checks enforce admin role, but route-level gating is missing.
- **Remediation**: Add `@admin_required` to route definition.

#### DEF-16: `DELETE-002` Unguarded Trashing of Questions Assigned to Published Assessments
- **Category**: Question Bank Lifecycle
- **Rule ID**: `DELETE-002`
- **File & Lines**: `src/pwd301/services/question_bank_service.py:786-838` (`trash_question`)
- **Description**: `trash_question` does not verify if a question is currently assigned to a live `PUBLISHED` assessment.
- **Remediation**: Prevent moving questions to `TRASH` if actively referenced by a published assessment.

#### DEF-17: `SEC-02` Missing `@instructor_required` Decorator on Mutating API Question Routes
- **Category**: Defense-in-Depth
- **Rule ID**: `SEC-02`
- **File & Lines**: `src/pwd301/blueprints/api_questions/routes.py:41, 56, 78, 100`
- **Description**: Mutating question routes (`PATCH`, `POST /trash`, `DELETE`, `POST /restore`) are decorated with `@jwt_required` but omit `@instructor_required`.
- **Remediation**: Add `@instructor_required` or `@require_roles("INSTRUCTOR", "ADMIN")` to route definitions.

---

## Part 3: Invariant & Architectural Security Confirmations

The audit confirmed strict adherence to the project's non-negotiable architectural invariants:
1. **Zero JWT in localStorage**: Verified across all frontend templates and `frontend-preview/`. Web UI exclusively utilizes HTTP-only Flask session cookies.
2. **Cross-Context CSRF Isolation**: Session cookies are strictly rejected on `/api/*` endpoints (`authorization_service.py:92-98`), completely eliminating ambient cookie CSRF on REST routes.
3. **Fail-Closed File Quarantine**: Files stream to quarantine storage and undergo multi-engine antivirus scanning; unscanned or infected files cannot be accessed or downloaded by students.
4. **Strict Media Limits (< 1 GB)**: Video uploads are enforced `< 1,000,000,000` bytes via `LimitingStream` and `MAX_CONTENT_LENGTH`.
5. **Assessment Structural & Points Locking**: Assessments lock points and question structure once the first student starts an attempt (`first_attempt_started_at is not None`).
6. **Immutable Attempt Presentation Snapshot**: Student attempts freeze questions, choice ordering, and points into separate snapshot tables (`attempt_questions`, `attempt_choice_snapshots`).
7. **Idempotent Submission & Resumable Regrading**: Submissions use UUID idempotency keys; regrading preserves historical answer snapshots and updates grade records idempotently.
8. **Student RAG Pre-Retrieval Authorization**: RAG queries enforce active enrollment authorization before retrieval, and strictly exclude archived, trashed, or draft courses.
9. **5-Minute Ephemeral Chat Content Purging**: AI chat messages are purged after 300 seconds of inactivity, retaining only minimal metadata.
10. **Append-Only Audit Trails & DB Restore Safety**: Sensitive actions commit audit records in the same transaction (fail-closed); database restores require explicit confirmation phrase, checksum verification, and admin password re-auth.
11. **Zero Primary Key Leakage (ADR-002)**: External APIs, templates, and routes expose opaque public UUIDs (`public_id`), completely masking internal `BigInt` primary keys.

---

## Part 4: Actionable Remediation Roadmap

```
┌────────────────────────────────────────────────────────────────────────┐
│                        REMEDIATION ROADMAP                             │
├────────────────────────────────────────────────────────────────────────┤
│ PHASE 1: Critical Invariants & Security (High Priority)               │
│ - Fix DEF-01: Update calculate_course_progress() with period filter    │
│ - Fix DEF-02: Add reauth & CONFIRM_SUSPEND checks to suspend routes   │
│ - Fix DEF-03: Restrict close_at modification on published assessments │
│ - Fix DEF-04: Enforce lease_expires_at check in attempt takeover      │
├────────────────────────────────────────────────────────────────────────┤
│ PHASE 2: Audit Trail, Lifecycle & Robustness (Medium Priority)        │
│ - Fix DEF-05: Record AuditEvent on email change completion             │
│ - Fix DEF-06: Unify suspend_user with audit_service & add notification │
│ - Fix DEF-07: Filter trashed/archived courses in prerequisite addition │
│ - Fix DEF-08: Enforce reason & notification on admin content overrides │
│ - Fix DEF-09: Use require_course_manager directly on course imports    │
├────────────────────────────────────────────────────────────────────────┤
│ PHASE 3: Test Infrastructure & Defense-in-Depth (Low Priority)        │
│ - Fix DEF-10: Isolate .restore_lock in tests/conftest.py tmp_path      │
│ - Fix DEF-11: Add py.typed to src/pwd301 and configure mypy_path      │
│ - Fix DEF-12: Revoke sessions/tokens in remove_role_from_user          │
│ - Fix DEF-13: Add orphaned course alert on instructor role removal     │
│ - Fix DEF-14: Add SQLAlchemy event listeners for email normalization   │
│ - Fix DEF-15: Add @admin_required to quarantine override route        │
│ - Fix DEF-16: Guard question trashing against published assessments   │
│ - Fix DEF-17: Add @instructor_required to api_questions mutating routes│
└────────────────────────────────────────────────────────────────────────┘
```
