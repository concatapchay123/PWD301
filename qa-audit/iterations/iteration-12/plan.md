# Iteration 12: Boundary Values, Negative Tests, Invalid States & Prerequisite Cycles

## 1. Objectives & Scope
Verify system resilience against malformed inputs, out-of-bounds boundary values, invalid state transitions, circular prerequisite dependencies (DAG invariant), expired and corrupted editing leases, and stale client sequencing under negative testing across Flask REST API, Microsoft SQL Server, and Vanilla SPA Client.

## 2. Invariants Under Test
1. **DAG Prerequisite Graph Invariant (Algorithm 03 / Invariant 1.2):** Course prerequisite relationships must form a Directed Acyclic Graph (DAG). Any mutation that introduces a circular dependency (e.g., Course A $\rightarrow$ Course B $\rightarrow$ Course A) must be detected via cycle detection and strictly rejected with HTTP 409 Conflict (`CYCLE_DETECTED` / `PrerequisiteCycleError`).
2. **Expired Editing Lease Autosave Fencing (Algorithm 07):** If a student's active editing lease expires (`now > lease_expires_at`), subsequent attempts to persist answers via autosave must be rejected fail-closed with HTTP 409 Conflict (`LEASE_CONFLICT` / `AttemptLeaseExpiredError`).
3. **Corrupt & Tampered Lease Token Defense:** Autosave and heartbeat endpoints must validate that the SHA-256 digest of the client-provided `raw_lease_token` matches `attempt.lease_token_hash`. Malformed, tampered, or mismatched tokens must be rejected with HTTP 409 Conflict (`LEASE_CONFLICT` / `AttemptLeaseConflictError`).
4. **Client Sequencing Fencing (Out-of-Order & Replay Attack Defense):** In `save_attempt_answer`, the client sequence number must be strictly greater than the recorded sequence (`client_sequence > last_client_sequence`). Stale or duplicate sequence packets must be rejected with HTTP 409 Conflict (`STALE_ANSWER` / `StaleAnswerSequenceError`), recording an unaccepted `AttemptAnswerEvent` with reason `STALE`.
5. **State Transition Machine Enforcement:** Invalid state transitions (e.g., publishing a course directly from `DRAFT`, or modifying an already `SUBMITTED`/`GRADED` assessment attempt) must be strictly forbidden with HTTP 409 Conflict (`STATE_VIOLATION`).
6. **Boundary & Negative Value Rejection:** Server-side input validation schemas must strictly enforce field bounds:
   - Completion progress percent and passing grades must be bounded within $[0.0, 100.0]$.
   - Course capacity must be a positive integer ($> 0$).
   - Course and lesson titles must not exceed maximum database column limits (200 characters).
   - Negative or out-of-bounds inputs must be rejected with HTTP 400 Bad Request (`VALIDATION_ERROR`).

## 3. Test Cases
- `TC-IT12-001`: Prerequisite Cycle Prevention (DAG Invariant Algorithm 03): Attempt to create circular prerequisites is rejected with HTTP 409 `CYCLE_DETECTED`.
- `TC-IT12-002`: Expired Editing Lease Autosave Fencing: Answer autosave on an expired lease is rejected with HTTP 409 `LEASE_CONFLICT`.
- `TC-IT12-003`: Corrupt & Tampered Lease Token Defense: Autosave with invalid/corrupt lease token is rejected with HTTP 409 `LEASE_CONFLICT`.
- `TC-IT12-004`: Out-of-Bounds Sequence Number Fencing: Replaying stale or lower sequence numbers is rejected with HTTP 409 `STALE_ANSWER`.
- `TC-IT12-005`: Invalid State Transition Rejection: Direct transition from DRAFT to PUBLISHED is rejected with HTTP 409 `STATE_VIOLATION`.
- `TC-IT12-006`: Boundary & Negative Value Validation: Negative capacity, progress > 100%, and oversized titles are rejected with HTTP 400 `VALIDATION_ERROR`.

## 4. Execution Methodology
- Real Google Chrome browser automation via Playwright (`channel="chrome"`).
- Dual-persisted annotated screenshots (`qa-audit/screenshots/` and `qa-audit/iterations/iteration-12/evidence/`).
- Direct SQL Server database queries inside `pwd301_web` container to inspect prerequisite graph edges, attempt answer events, and course status transitions.
