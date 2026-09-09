# TASK-014 — Attempt Lease Management & Multi-Tab Takeover Engine

**Status:** DONE

## Goal
Implement Single Active Editing Lease and Multi-Tab Takeover Engine for student assessment attempts in compliance with **ADR-005**, **Algorithm 07 (Attempt Lease Algorithm)**, **Algorithm 06 (Assessment Deadline Algorithm)**, and **ADR-002 (Internal BIGINT PK Masking)**:
1. **Single Active Editing Lease**: Ensure at any moment exactly one client tab/device holds a valid editing lease (`lease_token_hash` storing Binary32 SHA-256 digest).
2. **Heartbeat Extension (`ATTEMPT_HEARTBEAT_SECONDS = 10s`)**: Provide endpoint to periodically renew the editing lease (`ATTEMPT_LEASE_SECONDS = 30s`), clamped to `deadline_at` per Algorithm 06.
3. **Multi-Tab Takeover**: Allow a new tab/device to acquire the editing lease via takeover API, generating a cryptographically secure 32-byte hex token, immediately invalidating the prior lease, logging a `LEASE_TAKEOVER` AuditEvent, and causing the superseded tab to receive 409 `LEASE_CONFLICT` on subsequent requests.
4. **Explicit Lease Release**: Provide endpoint on tab unload/close to clear the lease token hash and expire the lease, logging a `LEASE_RELEASED` AuditEvent.
5. **Fail-Closed Zero-Trust IDOR Protection**: Confine lease operations strictly to the student owning the attempt. Peers, instructors, and unauthenticated clients receive 401 or 403.
6. **Auto-Transition of Overdue Attempts**: Transitions attempts past server deadline (`now >= deadline_at` or `now >= close_at`) to `EXPIRED` status and returns 409 `DEADLINE_EXPIRED`.
7. **REST API & Aliases**: Expose endpoints `/api/attempts/<id>/lease/heartbeat` (alias `/api/attempts/<id>/heartbeat`), `/api/attempts/<id>/lease/takeover` (alias `/api/attempts/<id>/lease`), and `/api/attempts/<id>/lease/release`.

## Source-of-truth documents
- `AGENTS.md` (Operating contract, source-of-truth hierarchy, non-negotiable invariants).
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/09_ASSESSMENT_ATTEMPT.md` (Business rules for assessment attempt lifecycle).
- `docs/system/PWD301_SYSTEM_SPECIFICATION/algorithms/06_SERVER_TIMER_ALGORITHM.md` (Algorithm 06: Server Timer & Deadline Calculation).
- `docs/system/PWD301_SYSTEM_SPECIFICATION/algorithms/07_ATTEMPT_LEASE_ALGORITHM.md` (Algorithm 07: Single Active Editing Lease).
- `docs/system/PWD301_SYSTEM_SPECIFICATION/api/08_ATTEMPT_API.md` (Attempt API endpoint contracts).
- `docs/system/PWD301_SYSTEM_SPECIFICATION/state-machines/ATTEMPT_STATE_MACHINE.md` (Attempt State Machine).
- `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/008_attempt_regrading.sql` (Canonical DDL for `assessment_attempts`).
- `docs/decisions/ADR-002-public-id-and-primary-keys.md` (ADR-002: Internal BIGINT PK Masking).
- `docs/decisions/ADR-005-editing-lease-and-tab-concurrency.md` (ADR-005: Editing Lease Baseline and Takeover).

## Preconditions
- Student must own the assessment attempt (`attempt.student_user_id == actor.id`).
- Attempt status must be `IN_PROGRESS`.
- Current server time must be strictly before attempt deadline (`now < attempt.deadline_at`) and assessment close time (`now < assessment.close_at`).

## In scope
1. **Domain Exceptions (`src/pwd301/services/exceptions.py`)**:
   - `AttemptLeaseExpiredError` (subclass of `AttemptLeaseError`, mapped to 409 `LEASE_CONFLICT`).
   - `AttemptLeaseConflictError` (subclass of `AttemptLeaseError`, mapped to 409 `LEASE_CONFLICT`).
   - `AttemptExpiredError` (subclass of `ConflictError`, mapped to 409 `DEADLINE_EXPIRED`).
2. **Service Layer (`src/pwd301/services/attempt_service.py`)**:
   - `_check_and_expire_if_needed`: Status and server deadline validation with auto-transition to `EXPIRED`.
   - `renew_attempt_lease`: Heartbeat renewal extending lease by 30s clamped to deadline.
   - `takeover_attempt_lease`: Generating fresh 32-byte hex token, invalidating prior lease, logging `LEASE_TAKEOVER`.
   - `release_attempt_lease`: Explicit lease release on tab close, logging `LEASE_RELEASED`.
   - `verify_attempt_lease`: Predicate helper validating active lease status, hash match, and non-expiry.
3. **App Factory & Centralized Error Handlers (`src/pwd301/__init__.py`)**:
   - Registered `AttemptLeaseConflictError` -> 409 `LEASE_CONFLICT`.
   - Registered `AttemptLeaseExpiredError` -> 409 `LEASE_CONFLICT`.
   - Registered `AttemptExpiredError` -> 409 `DEADLINE_EXPIRED`.
4. **REST API Routes (`src/pwd301/blueprints/api_attempts/routes.py`)**:
   - `POST /api/attempts/<id>/lease/heartbeat` & alias `POST /api/attempts/<id>/heartbeat`
   - `POST /api/attempts/<id>/lease/takeover` & alias `POST /api/attempts/<id>/lease`
   - `POST /api/attempts/<id>/lease/release`
   - Token resolution via `X-Attempt-Lease-Token` header or JSON body `{"lease_token": "..."}` / `{"raw_lease_token": "..."}`.
5. **Re-export (`src/pwd301/services/__init__.py`)**:
   - Re-exported new functions and exceptions in `__all__`.
6. **Automated Testing Suite**:
   - Unit tests (`tests/unit/test_attempt_lease_service.py`): 12 tests.
   - Security & IDOR negative tests (`tests/security/test_attempt_lease_idor.py`): 6 tests.
   - Concurrency & race condition tests (`tests/concurrency/test_attempt_lease_race.py`): 3 tests.
   - REST API integration tests (`tests/api/test_attempt_lease_api.py`): 11 tests.

## Out of scope
- Autosave answer persisting and client change sequence checking (TASK-015).
- Objective grading and manual essay evaluation (TASK-016).
- Regrading jobs and score revision audits (TASK-017).

## Reuse / existing-code inspection
- Reused `AssessmentAttempt` model fields `lease_token_hash`, `lease_acquired_at`, `lease_expires_at`, `last_heartbeat_at`.
- Reused `AuditEvent` model for append-only audit tracking.
- Reused `@jwt_required` and `get_authenticated_actor` for JWT authentication.
- Reused `_normalize_dt` datetime normalization helper.

## Planned changes
- Define new lease exceptions in `src/pwd301/services/exceptions.py`.
- Implement lease functions in `src/pwd301/services/attempt_service.py`.
- Register error handlers in `src/pwd301/__init__.py`.
- Implement lease API routes in `src/pwd301/blueprints/api_attempts/routes.py`.
- Add test suites in `tests/unit/`, `tests/security/`, `tests/concurrency/`, and `tests/api/`.

## Security / authorization impact
- **Fail-Closed IDOR Defense**: Only the student owning the attempt (`attempt.student_user_id == actor.id`) can heartbeat, takeover, or release a lease. Enrolled peers and instructors receive 403 Forbidden.
- **Token Security**: The database only stores the Binary32 SHA-256 digest (`lease_token_hash`). The raw 32-byte hex token is returned only upon initial attempt delivery or explicit takeover.
- **ADR-002 Masking**: Internal integer primary and foreign keys are never exposed in lease endpoint responses (UUIDv4 `attempt_id` only).

## Database / migration impact
- No schema migrations required; tables and lease columns were already defined in reference DDL `008_attempt_regrading.sql` and SQLAlchemy models.

## Concurrency / idempotency impact
- Multi-tab race condition handled via token rotation: when Tab 2 takes over, `lease_token_hash` is atomically updated, immediately invalidating Tab 1's token. On its next heartbeat or autosave, Tab 1 receives 409 `LEASE_CONFLICT`.
- Concurrent takeovers are serialized at the database transaction level.

## Acceptance criteria
- [x] Heartbeat extends lease by 30 seconds (`ATTEMPT_LEASE_SECONDS = 30`).
- [x] Heartbeat renewal clamped to `min(now + 30s, deadline_at)`.
- [x] Expired lease renewal rejected with 409 `LEASE_CONFLICT`.
- [x] Mismatched lease token rejected with 409 `LEASE_CONFLICT`.
- [x] Overdue attempt automatically transitions to `EXPIRED` with 409 `DEADLINE_EXPIRED`.
- [x] Takeover generates fresh 32-byte hex token and updates `lease_token_hash`.
- [x] Takeover invalidates previous tab token and records `LEASE_TAKEOVER` AuditEvent.
- [x] Release clears lease and records `LEASE_RELEASED` AuditEvent.
- [x] Zero-Trust IDOR protection: peers and instructors receive 403 Forbidden.
- [x] ADR-002 compliance: zero internal `BIGINT` PK/FK leakage.
- [x] Static checks and 100% test suite pass without regressions (397/397 passed).

## Required tests
- `tests/unit/test_attempt_lease_service.py`: 12 unit tests.
- `tests/security/test_attempt_lease_idor.py`: 6 security tests.
- `tests/concurrency/test_attempt_lease_race.py`: 3 concurrency tests.
- `tests/api/test_attempt_lease_api.py`: 11 API integration tests.

## Verification commands
- `E:\PWD301\.venv\Scripts\python.exe scripts/repo_check.py`
- `E:\PWD301\.venv\Scripts\python.exe -m ruff check src tests scripts`
- `E:\PWD301\.venv\Scripts\python.exe -m ruff format --check src tests scripts`
- `E:\PWD301\.venv\Scripts\python.exe -m mypy src`
- `E:\PWD301\.venv\Scripts\python.exe -m pytest tests/unit/test_attempt_lease_service.py tests/security/test_attempt_lease_idor.py tests/concurrency/test_attempt_lease_race.py tests/api/test_attempt_lease_api.py -v`

## Deletion and simplification list
| Candidate | Classification | Reason | Action |
|---|---|---|---|
| Redundant lease helper calls in unit tests | REMOVE NOW | Unused imports in lease tests | Cleaned up imports |
| Double lease endpoint routes | KEEP | Both `/lease/heartbeat` and `/heartbeat` needed for spec compatibility | Kept alias decorators |

## Ponytails / deferred debt
None. All components required for TASK-014 are fully implemented without temporary shortcuts.

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
- `docs/decisions/ADR-005-editing-lease-and-tab-concurrency.md`
- `AGENTS.md`

### B. Reuse decisions
- Reused `AssessmentAttempt` model columns `lease_token_hash`, `lease_acquired_at`, `lease_expires_at`, `last_heartbeat_at`.
- Reused `AuditEvent` model for immutable audit trail recording.
- Reused `_normalize_dt` from `assessment_service.py` for consistent naive/aware datetime handling.
- Reused `@jwt_required` and `get_authenticated_actor` for JWT authentication.

### C. Per-file changes
- `src/pwd301/services/exceptions.py`: Added `AttemptLeaseExpiredError`, `AttemptLeaseConflictError`, `AttemptExpiredError`.
- `src/pwd301/services/attempt_service.py`: Added `_check_and_expire_if_needed`, `renew_attempt_lease`, `takeover_attempt_lease`, `release_attempt_lease`, `verify_attempt_lease`.
- `src/pwd301/services/__init__.py`: Re-exported all new functions and exceptions in `__all__`.
- `src/pwd301/__init__.py`: Registered domain exception handlers for `AttemptLeaseConflictError` (409 LEASE_CONFLICT), `AttemptLeaseExpiredError` (409 LEASE_CONFLICT), and `AttemptExpiredError` (409 DEADLINE_EXPIRED).
- `src/pwd301/blueprints/api_attempts/routes.py`: Added `_extract_lease_token`, heartbeat routes, takeover routes, release route.
- `tests/unit/test_attempt_lease_service.py`: Added 12 unit tests covering heartbeat, takeover, release, deadline clamp, and verification matrix.
- `tests/security/test_attempt_lease_idor.py`: Added 6 security tests verifying fail-closed IDOR protection against peers, instructors, admins, unauthenticated requests, and hash storage.
- `tests/concurrency/test_attempt_lease_race.py`: Added 3 concurrency/race condition tests verifying multi-tab takeover eviction and rapid takeover invalidation.
- `tests/api/test_attempt_lease_api.py`: Added 11 REST API integration tests covering status codes, header and body tokens, conflict handling, and ADR-002 masking.

### D. Deletion/simplification list
- Cleaned unused imports and aligned formatting to strict 100 char limit via `ruff format`.

### E. Ponytails
None.

### F. Verification actually run
1. Repository contract check: `python scripts/repo_check.py` -> **PASS**
2. Linter check: `ruff check src tests scripts` -> **PASS** (0 errors)
3. Code formatting check: `ruff format --check src tests scripts` -> **PASS** (102 files verified)
4. Static type check: `mypy src` -> **PASS** (0 issues across 56 files)
5. TASK-014 test suites: 32/32 passed.
6. Full test suite: 397/397 passed (0 failures, 0 errors).

### G. Remaining risks / next step (only if necessary)
- Next sequential task in backlog: **TASK-015** (Autosave, offline reconciliation, and idempotent submission engine).
