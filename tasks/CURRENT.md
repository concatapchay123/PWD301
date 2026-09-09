# TASK-013 — Student Assessment Delivery, Attempt Snapshot & Server Timer Engine

**Status:** DONE

## Goal
Implement the candidate assessment delivery and attempt engine:
1. **Precondition Enforcement**: Student active enrollment validation (`Enrollment.status == 'ACTIVE'`), published assessment status (`status == 'PUBLISHED'`), exam availability window (`open_at <= now < close_at`), attempt limit enforcement (`attempt_limit`), and single in-progress attempt protection (`ActiveAttemptExistsError`).
2. **Structural Freeze Trigger (ASSESS-002 / AC-06)**: Atomically initialize `assessment.first_attempt_started_at = utc_now()` on first student attempt start, permanently freezing assessment structure.
3. **Server-Authoritative Timer (Algorithm 06 / ADR-006)**: Compute nominal deadline `started_at + timedelta(minutes=time_limit_minutes)` and clamp to `min(nominal_deadline, close_at)` as `deadline_at`. Auto-transition overdue attempts (`norm_now >= deadline_at`) to `EXPIRED`.
4. **Candidate Presentation Snapshot (ADR-004)**: Snapshot fixed questions and pooled items into `attempt_questions`; snapshot choices with random UUIDv4 `choice_key_snapshot` into `attempt_choice_snapshots` without answers (`is_correct`) or explanations; support `shuffle_questions` and `shuffle_choices` while respecting `is_fixed_position`.
5. **Editing Lease Baseline (ADR-005 / Algorithm 07)**: Generate cryptographically secure 32-byte hex token, hash with SHA-256 into `lease_token_hash`, set initial 30-second expiry (`lease_expires_at`).
6. **Data Masking & Zero-Trust IDOR Defense (ADR-002)**: Never expose internal `BIGINT` PKs or FKs (use UUIDv4 or deterministic UUIDv5 `pwd301.attempt_question.{id}`); restrict delivery payload strictly to owning student or admin oversight; never leak `is_correct` or `explanation`.
7. **Append-Only Audit Logging**: Persist immutable `AuditEvent` (`target_type="ATTEMPT"`, `action="ATTEMPT_STARTED"`).
8. **REST API Delivery**: Deliver `/api/assessments/<assessment_id>/attempts` (POST start, GET history) and `/api/attempts/<attempt_id>` (GET candidate delivery with live countdown).

## Source-of-truth documents
- `AGENTS.md` (Operating contract, source-of-truth hierarchy, non-negotiable invariants).
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/09_ASSESSMENT_ATTEMPT.md` (Business rules for assessment attempt lifecycle).
- `docs/system/PWD301_SYSTEM_SPECIFICATION/algorithms/06_SERVER_TIMER_ALGORITHM.md` (Algorithm 06: Server Timer & Deadline Calculation).
- `docs/system/PWD301_SYSTEM_SPECIFICATION/algorithms/07_ATTEMPT_LEASE_ALGORITHM.md` (Algorithm 07: Single Active Editing Lease).
- `docs/system/PWD301_SYSTEM_SPECIFICATION/api/08_ATTEMPT_API.md` (Attempt API endpoint contracts).
- `docs/system/PWD301_SYSTEM_SPECIFICATION/state-machines/ATTEMPT_STATE_MACHINE.md` (Attempt State Machine).
- `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/008_attempt_regrading.sql` (Canonical DDL for `assessment_attempts`, `attempt_questions`, `attempt_choice_snapshots`, `attempt_answers`, `attempt_events`).
- `docs/decisions/ADR-002-public-id-and-primary-keys.md` (ADR-002: Internal BIGINT PK Masking).
- `docs/decisions/ADR-004-assessment-presentation-snapshot.md` (ADR-004: Candidate Presentation Snapshot).
- `docs/decisions/ADR-005-editing-lease-and-tab-concurrency.md` (ADR-005: Editing Lease Baseline).
- `docs/decisions/ADR-006-server-authoritative-timing.md` (ADR-006: Server Timer Engine).

## Preconditions
- Course and Assessment must be `PUBLISHED`.
- Student must have an active enrollment (`Enrollment.status == 'ACTIVE'`) with an active enrollment period.
- Candidate questions (fixed assignments or materialized question pool) must exist in the assessment.

## In scope
1. **Domain Exceptions (`src/pwd301/services/exceptions.py`)**:
   - `AttemptError`, `AttemptNotFoundError`, `AttemptValidationError`, `AttemptLimitExceededError`, `AssessmentNotOpenError`, `AssessmentClosedError`, `ActiveAttemptExistsError`, `AttemptLeaseError`.
2. **Service Layer (`src/pwd301/services/attempt_service.py`)**:
   - `start_assessment_attempt`, `get_attempt_delivery`, `list_student_assessment_attempts`.
   - `_calculate_deadline`, `_generate_lease`, `_serialize_attempt`, `_record_attempt_audit`.
3. **Re-export (`src/pwd301/services/__init__.py`)**:
   - Export domain functions and exceptions in `__all__`.
4. **Blueprints & REST Routes (`src/pwd301/blueprints/api_attempts/`)**:
   - `POST /api/assessments/<assessment_id>/attempts`: Start attempt (201 Created).
   - `GET /api/attempts/<attempt_id>`: Candidate delivery payload with live timer (200 OK).
   - `GET /api/assessments/<assessment_id>/attempts`: Attempt history list (200 OK).
5. **App Factory Integration (`src/pwd301/__init__.py`)**:
   - Blueprint registration, CSRF exemption for JWT API, centralized error handler registration.
6. **Automated Testing Suite**:
   - Unit tests (`tests/unit/test_attempt_service.py`): 11 tests.
   - Security & IDOR negative tests (`tests/security/test_attempt_idor.py`): 4 tests.
   - REST API integration tests (`tests/api/test_attempt_api.py`): 11 tests.

## Out of scope
- Answer autosave, heartbeat lease renewals, and client change sequencing (TASK-015).
- Objective grading, manual essay grading, and result finalization (TASK-016).
- Regrading jobs, delta calculations, and score revision histories (TASK-017).

## Reuse / existing-code inspection
- Reused `pwd301.models.attempt_regrade` (`AssessmentAttempt`, `AttemptQuestion`, `AttemptChoiceSnapshot`).
- Reused `pwd301.services.authorization_service.get_authenticated_actor` and `pwd301.services.jwt_auth_service.jwt_required`.
- Reused `pwd301.models.notification_audit.AuditEvent` for audit trail persistence.
- Reused `_normalize_dt` and `require_course_manager` patterns from `assessment_service.py`.

## Planned changes
- Add attempt exceptions to `src/pwd301/services/exceptions.py`.
- Implement `src/pwd301/services/attempt_service.py`.
- Re-export attempt symbols in `src/pwd301/services/__init__.py`.
- Implement `src/pwd301/blueprints/api_attempts/__init__.py` and `routes.py`.
- Wire blueprint and error handlers in `src/pwd301/__init__.py`.
- Add test suites in `tests/unit/test_attempt_service.py`, `tests/security/test_attempt_idor.py`, and `tests/api/test_attempt_api.py`.

## Security / authorization impact
- **Fail-Closed IDOR Defense**: Candidate delivery is strictly confined to the attempt owner (`attempt.student_user_id == student_actor.id`) or Admin oversight. Unrelated instructors and peer students receive 403 Forbidden.
- **Zero Information Leakage**: No `is_correct` flags or secret `explanation` fields are serialized into snapshots or delivery payloads. Choices receive dynamic UUIDv4 `choice_key_snapshot`.
- **ADR-002 Masking**: Internal integer primary and foreign keys (`id`, `creator_user_id`, `student_user_id`, `source_question_id`, `source_choice_id`) are never exposed in JSON responses.
- **Lease Token Security**: Raw lease token is returned only once to the client upon generation; database stores salted/hashed SHA-256 digest (`lease_token_hash`).

## Database / migration impact
- No schema migrations required; tables `assessment_attempts`, `attempt_questions`, `attempt_choice_snapshots`, and `audit_events` were already defined in reference DDL `008_attempt_regrading.sql` and SQLAlchemy models in `attempt_regrade.py`.

## Concurrency / idempotency impact
- Precondition queries check for existing `IN_PROGRESS` attempts before creating a new one, raising `ActiveAttemptExistsError` (409 Conflict).
- Assessment `first_attempt_started_at` is set atomically within the transaction to trigger structural freeze.

## Acceptance criteria
- [x] Student without active enrollment is rejected (`AttemptValidationError`, 400).
- [x] Unpublished assessment is rejected (`AssessmentNotOpenError`, 400).
- [x] Attempts outside `[open_at, close_at)` are rejected (`NOT_OPEN` or `CLOSED`, 400).
- [x] Exceeding `attempt_limit` is rejected (`AttemptLimitExceededError`, 409).
- [x] Concurrent in-progress attempt is rejected (`ActiveAttemptExistsError`, 409).
- [x] Algorithm 06 clamps nominal deadline to `min(nominal, close_at)`.
- [x] Overdue attempts auto-transition from `IN_PROGRESS` to `EXPIRED`.
- [x] Presentation snapshot freezes fixed assignments + pool items and randomizes choice keys.
- [x] Structural freeze sets `first_attempt_started_at = utc_now()`.
- [x] Initial 30s editing lease token generated and hashed with SHA-256.
- [x] ADR-002 enforced across all responses: no `BIGINT` PKs exposed.
- [x] Append-only `AuditEvent` recorded on attempt creation.
- [x] Full test suite passes with zero regressions (357/357 passed).

## Required tests
- `tests/unit/test_attempt_service.py`: 11 unit tests.
- `tests/security/test_attempt_idor.py`: 4 security tests.
- `tests/api/test_attempt_api.py`: 11 integration tests.

## Verification commands
- `./scripts/verify.ps1` (or `./scripts/verify.sh`)
- `.venv\Scripts\python.exe -m ruff check src tests scripts`
- `.venv\Scripts\python.exe -m ruff format --check src tests scripts`
- `.venv\Scripts\python.exe -m mypy src`
- `.venv\Scripts\python.exe -m pytest`

## Deletion and simplification list
| Candidate | Classification | Reason | Action |
|---|---|---|---|
| Redundant lease helper calls in unit tests | REMOVE NOW | Cleaned up unused imports `_generate_lease`, `_serialize_attempt` | Removed from test imports |
| Long lines in security/API tests | SIMPLIFY NOW | Exceeded 100 character limit | Formatted with `ruff format` |
| Unused model imports in test suites | REMOVE NOW | `Lesson`, `QuestionRevisionChoice`, `Question` imported without use | Removed unused imports |

## Ponytails / deferred debt
None. All components required for TASK-013 are fully implemented without temporary shortcuts or hacks.

---

## Completion report

### A. Scope and sources consulted
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/09_ASSESSMENT_ATTEMPT.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/algorithms/06_SERVER_TIMER_ALGORITHM.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/algorithms/07_ATTEMPT_LEASE_ALGORITHM.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/api/08_ATTEMPT_API.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/state-machines/ATTEMPT_STATE_MACHINE.md`
- `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/008_attempt_regrading.sql`
- `docs/decisions/ADR-002-public-id-and-primary-keys.md`
- `docs/decisions/ADR-004-assessment-presentation-snapshot.md`
- `docs/decisions/ADR-005-editing-lease-and-tab-concurrency.md`
- `docs/decisions/ADR-006-server-authoritative-timing.md`
- `AGENTS.md`

### B. Reuse decisions
- Reused existing models from `pwd301.models.attempt_regrade` (`AssessmentAttempt`, `AttemptQuestion`, `AttemptChoiceSnapshot`).
- Reused authentication and authorization decorators (`@jwt_required`, `get_authenticated_actor`).
- Reused audit model `AuditEvent` and database session management conventions.

### C. Per-file changes
- `src/pwd301/services/exceptions.py`: Added `AttemptError`, `AttemptNotFoundError`, `AttemptValidationError`, `AttemptLimitExceededError`, `AssessmentNotOpenError`, `AssessmentClosedError`, `ActiveAttemptExistsError`, `AttemptLeaseError`.
- `src/pwd301/services/attempt_service.py`: Implemented attempt initiation, candidate delivery snapshot generation, deadline calculation (Algorithm 06), editing lease creation (ADR-005 / Algorithm 07), structural freeze triggering, and attempt listing.
- `src/pwd301/services/__init__.py`: Exported all new attempt service functions and domain exceptions.
- `src/pwd301/blueprints/api_attempts/__init__.py`: Declared `api_attempt_bp`.
- `src/pwd301/blueprints/api_attempts/routes.py`: Implemented `POST /api/assessments/<assessment_id>/attempts`, `GET /api/attempts/<attempt_id>`, `GET /api/assessments/<assessment_id>/attempts`.
- `src/pwd301/__init__.py`: Registered `api_attempt_bp`, configured CSRF exemption, registered error handlers for attempt exceptions.
- `tests/unit/test_attempt_service.py`: Added 11 unit tests covering all edge cases, timing clamp, structural freeze, and serialization.
- `tests/security/test_attempt_idor.py`: Added 4 security tests validating IDOR isolation, zero leakage of correct choices/explanations, and admin oversight.
- `tests/api/test_attempt_api.py`: Added 11 REST API integration tests covering authentication, authorization, error statuses, and delivery verification.

### D. Deletion/simplification list
- Removed unused imports across `tests/unit/test_attempt_service.py`, `tests/security/test_attempt_idor.py`, and `tests/api/test_attempt_api.py`.
- Formatted all files with `ruff format` to meet line length requirements.

### E. Ponytails
None.

### F. Verification actually run
1. Repository contract verification: `python scripts/repo_check.py` -> **PASS**
2. Static type checking: `mypy src` -> **PASS** (0 errors across 56 files)
3. Linter: `ruff check src tests scripts` -> **PASS** (0 errors)
4. Code formatting check: `ruff format --check src tests scripts` -> **PASS** (98 files verified)
5. Aggregate full verification suite: `./scripts/verify.ps1` -> **PASS** (357 passed in 123.70s, 0 failed, 0 regressions)

### G. Remaining risks / next step (only if necessary)
- Next sequential task in backlog: **TASK-014** or **TASK-015** (Autosave, tab lease renewal, and answer persistence engine).
