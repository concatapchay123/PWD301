# TASK-015 — Autosave, Offline Reconciliation & Idempotent Submission Engine

**Status:** DONE  
**Assignee:** Principal Software Architect & Lead Fullstack Python/Flask Engineer  
**Depends on:** TASK-013, TASK-014  

---

## 1. Goal / Problem Statement
Implement the autosave, offline reconciliation, and idempotent submission engine for student assessment attempts in compliance with **ADR-002 (Internal BIGINT Masking)**, **ADR-004 (Attempt Snapshot Preservation)**, **ADR-005 (Editing Lease & Epoch Fencing)**, **ADR-006 (Server-Authoritative Timer)**, **Algorithm 08 (Autosave & Offline Reconciliation)**, and **Algorithm 09 (Submission Idempotency)**:
1. **Autosave & Event Sourcing**: Direct answer saving for MCQ and text answers with immutable event log generation (`AttemptAnswerEvent`) tracking every change state, client sequence, and client timestamp.
2. **Offline Reconciliation & Monotonic Sequencing**: Enforce strictly increasing monotonic sequence numbers (`client_sequence > last_client_sequence`) per question; detect network race conditions, reject stale writes with 409 `STALE_ANSWER` while persisting rejected audit events, and support bulk offline synchronization (`POST /api/attempts/<id>/answers/sync`).
3. **Lease & Epoch Fencing**: Validate active 30s editing lease and match `lease_epoch` to block stale tabs/devices (409 `STALE_LEASE_EPOCH`).
4. **Server-Authoritative Timer Clamping**: Validate current server time strictly before `deadline_at` and assessment `close_at`. Automatically transition overdue attempts to `EXPIRED` status (409 `DEADLINE_EXPIRED`).
5. **Idempotent Submission Engine**: Atomic state transition from `IN_PROGRESS` to `SUBMITTED` with `submission_idempotency_key` (UUIDv4). Repeated submissions with the same key return cached original results (200 OK, `is_idempotent_replay: true`), whereas mismatched keys for an already submitted attempt raise 409 `SUBMISSION_CONFLICT`.
6. **Lease Revocation & Audit Logging**: Atomically clear editing lease (`lease_token_hash`, `lease_expires_at`, `editor_session_id`) on submission and record append-only audit event (`ATTEMPT_SUBMITTED`).
7. **Fail-Closed Zero-Trust IDOR & ADR-002 Invariants**: Confine all autosave, sync, and submit operations strictly to the student owning the attempt (403 Forbidden for peers/instructors/admins, 401 for unauthenticated). Ensure zero internal `BIGINT` PK/FK IDs leak in JSON responses.

---

## 2. Key Architecture Decisions & Invariants
- **Algorithm 08 (Autosave & Offline Reconciliation)**:
  - Validates active lease and deadline. Checks `change_id` (UUIDv4) deduplication: duplicate `change_id` with identical content is treated idempotently without bumping sequence or erroring.
  - Stale sequence check: If `client_sequence <= last_client_sequence`, an immutable `AttemptAnswerEvent` is recorded with `rejection_reason = 'STALE'`, and `StaleAnswerSequenceError` (409 `STALE_ANSWER`) is raised.
  - Batch offline sync: Validates batch inputs, orders items by `client_sequence` ascending, reconciles valid items, skips stale items without aborting valid ones, and returns granular reconciliation summary (`synced_count`, `skipped_count`, `synced`, `skipped`).
- **Algorithm 09 & Atomic Submission Idempotency**:
  - High-concurrency race protection uses conditional SQL execution:
    ```sql
    UPDATE assessment_attempts
    SET status = 'SUBMITTED', submitted_at = :now, finalized_at = :now,
        submission_idempotency_key = :key, lease_token_hash = NULL,
        lease_expires_at = NULL, editor_session_id = NULL
    WHERE id = :attempt_id AND status = 'IN_PROGRESS'
    ```
  - Exactly one concurrent thread/process succeeds. Concurrent losers re-query the row: if the stored `submission_idempotency_key` matches the requester's key, an idempotent replay response is returned; if keys mismatch, 409 `SUBMISSION_CONFLICT` is raised.
- **ADR-002 Strict Exposure**:
  - All public APIs accept and return public UUIDs (`attempt_id`, `attempt_question_id`, `choice_id`). Zero internal database integer PKs/FKs are exposed in JSON payloads.
- **ADR-005 Lease Revocation**:
  - Submitting immediately revokes any editing lease, preventing further autosave modifications or lease takeovers.

---

## 3. Files Changed / Created
- `src/pwd301/services/exceptions.py`:
  - Added `SubmissionIdempotencyConflictError(ConflictError, AttemptError)` (maps to 409 `SUBMISSION_CONFLICT`).
  - Added `AttemptAlreadySubmittedError(StateViolationError, AttemptError)` (maps to 409 `STATE_VIOLATION`).
  - Re-used `StaleAnswerSequenceError` (409 `STALE_ANSWER`), `StaleLeaseEpochError` (409 `STALE_LEASE_EPOCH`), `AttemptExpiredError` (409 `DEADLINE_EXPIRED`).
- `src/pwd301/__init__.py`:
  - Registered centralized Flask exception handlers for `SubmissionIdempotencyConflictError` and `AttemptAlreadySubmittedError`.
- `src/pwd301/services/attempt_service.py`:
  - Implemented `save_attempt_answer`: single question autosave with lease validation, epoch fencing, change-id idempotency, monotonic sequence check, `AttemptAnswer` upsert, `AttemptAnswerChoice` persistence, and `AttemptAnswerEvent` audit log.
  - Implemented `sync_offline_answers`: batch offline reconciliation with ascending sequence ordering, item-level validation, stale filtering, and summary statistics.
  - Implemented `submit_assessment_attempt`: atomic state transition to `SUBMITTED`, idempotency key validation/caching, conflict detection, lease revocation, and `ATTEMPT_SUBMITTED` audit logging.
- `src/pwd301/blueprints/api_attempts/routes.py`:
  - Added `PUT /api/attempts/<attempt_id>/answers/<attempt_question_id>` (Autosave answer).
  - Added `POST /api/attempts/<attempt_id>/answers/sync` (Batch offline sync).
  - Added `POST /api/attempts/<attempt_id>/submit` (Idempotent submission via header or body key).
- `src/pwd301/services/__init__.py`:
  - Exported new functions and domain exceptions in `__all__`.
- `pyproject.toml`:
  - Configured `pythonpath = ["src", "."]` to allow running pytest cleanly in all execution environments.
- `tests/unit/test_attempt_autosave_service.py`:
  - 9 unit tests covering text & MCQ autosave, sequence rejection, duplicate `change_id` idempotency, epoch fencing, invalid lease token rejection, submitted attempt rejection, expired deadline rejection, and batch offline sync.
- `tests/unit/test_attempt_submission_service.py`:
  - 5 unit tests covering normal submission transition, idempotent replay, idempotency key mismatch conflict (409), expired deadline rejection, and invalid idempotency key UUID format validation.
- `tests/security/test_attempt_submission_idor.py`:
  - 6 security & IDOR negative tests verifying fail-closed Zero-Trust isolation for peer students, instructors, and admins on autosave, sync, and submit endpoints, along with unauthenticated 401 checks and ADR-002 zero BIGINT leakage validation.
- `tests/concurrency/test_submission_idempotency_race.py`:
  - 2 multithreaded concurrency tests verifying convergence under concurrent submissions with identical keys and conflict resolution (1 success, 1 conflict) with differing keys.
- `tests/api/test_attempt_submission_api.py`:
  - 3 end-to-end REST API integration tests verifying full attempt lifecycle (Start -> Autosave -> Sync -> Submit), JSON body idempotency key submission, and overdue attempt 409 rejection.

---

## 4. Verification Commands & Results

| Verification Gate | Command | Result |
|---|---|---|
| **1. Repository Contract** | `.venv/Scripts/python scripts/repo_check.py` | **PASS** (all structural contracts and DDL valid) |
| **2. Code Linting** | `.venv/Scripts/ruff check src/pwd301 tests/api tests/concurrency tests/security tests/unit` | **PASS** (0 errors, all imports sorted) |
| **3. Code Formatting** | `.venv/Scripts/ruff format --check src/pwd301 tests/api tests/concurrency tests/security tests/unit` | **PASS** (all files formatted cleanly) |
| **4. Type Checking** | `.venv/Scripts/mypy src` | **PASS** (Success: no issues found in 58 source files) |
| **5. Task-015 Test Suite** | `.venv/Scripts/pytest tests/unit/test_attempt_autosave_service.py tests/unit/test_attempt_submission_service.py tests/security/test_attempt_submission_idor.py tests/concurrency/test_submission_idempotency_race.py tests/api/test_attempt_submission_api.py -v` | **PASS** (25/25 passed in 20.23s) |
| **6. Full Regression Suite** | `.venv/Scripts/python -m pytest` | **PASS** (428/428 passed in 228.35s) |

---

## 5. Security & Invariant Verification Summary
- **Fail-Closed Zero-Trust IDOR**: Only the enrolled student who owns the attempt can autosave answers, sync offline batches, or submit the attempt. Peers receive 403 Forbidden. Instructors and administrators are also forbidden from altering student answers or submitting attempts.
- **ADR-002 Compliance**: Verified across all 25 TASK-015 tests and explicitly asserted in `test_adr002_zero_bigint_leakage_in_responses` that zero internal integer database PKs/FKs (`id`, `student_user_id`, `assessment_id`, etc.) leak in API JSON responses.
- **Monotonic Sequence Enforcement**: Verified rejected events are recorded with `rejection_reason = 'STALE'` in the append-only `AttemptAnswerEvent` table and return 409 `STALE_ANSWER`.
- **Atomic Concurrency Protection**: Verified with 10 concurrent threads that multiple simultaneous submissions with the same idempotency key converge to 200 OK without race conditions or duplicate audit records, and concurrent submissions with different keys cleanly resolve to exactly one winner and one 409 `SUBMISSION_CONFLICT`.

---

## 6. Known Limitations & Deferred Work
- **Objective Auto-Grading & Manual Essay Grading**: Grading computation and scoring logic are strictly decoupled and deferred to **TASK-016 (Grading + Manual Essay Grading)**.
- **Regrading Engine & Score History**: Recalculating attempt grades upon question revisions/corrections is deferred to **TASK-017 (Regrading + Score History)**.

---

## 7. Recommended Next Action
- Proceed to **TASK-016 — Grading + Manual Essay Grading Engine**:
  - Implement objective auto-grading for SINGLE_CHOICE, MULTIPLE_CHOICE, TRUE_FALSE questions against question snapshots.
  - Implement instructor manual grading workflow and rubric-based scoring for ESSAY questions.
  - Implement attempt final grade aggregation and course completion trigger integration.
