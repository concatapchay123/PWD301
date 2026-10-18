# Iteration 11: Concurrency, Race Conditions, Single Active Editing Lease & Submissions

## 1. Objectives & Scope
Verify system behavior under concurrent access, race conditions, single active editing lease fencing (Algorithm 07), heartbeat lease renewal, tab takeover, idempotent submission replays, optimistic concurrency guards on course staging reviews, and row-locked course enrollment capacity enforcement across Microsoft SQL Server, Flask REST API, and Vanilla SPA Client.

## 2. Invariants Under Test
1. **Single Active Editing Lease Acquisition & Heartbeat (Algorithm 07 / Invariant 4.1):** When a student begins an assessment attempt, the server generates a cryptographically random 32-byte hex lease token, stores its SHA-256 digest in `attempt.lease_token_hash`, sets initial `lease_epoch = 1`, and binds `lease_expires_at` (~60s into the future). Periodic heartbeats extend the lease timestamp safely.
2. **Tab Takeover & Lease Fencing (Algorithm 07 / ADR-005):** When an attempt is opened in a second tab/window or after lease release, takeover increments `lease_epoch` and issues a new lease token. Any subsequent answer persistence or heartbeat from the stale tab is strictly rejected with HTTP 409 Conflict (`LEASE_CONFLICT` / `STALE_LEASE_EPOCH`), preventing split-brain overwrites.
3. **Submission Idempotency Under Concurrent Double-Submit (Algorithm 07 / Invariant 4.2):** Firing concurrent submit requests with the same idempotency key for an in-progress attempt succeeds idempotently without duplicate grading, deadlock, or score corruption. Exactly one request transitions status to `SUBMITTED`; concurrent replays receive the identical submission payload with HTTP 200.
4. **Optimistic Concurrency & Course Changeset Fingerprint Guard:** When multiple reviewers or administrators review course staging drafts, mutations submitted with a stale `review_version` or mismatched fingerprint are rejected with HTTP 409 Conflict (`Bản xét duyệt đã thay đổi. Hãy tải lại và kiểm tra phiên bản mới trước khi duyệt.`).
5. **Row-Locked Enrollment Capacity Enforcement:** When a course reaches maximum capacity, concurrent enrollment transactions serialize via database row locks (`WITH (UPDLOCK, HOLDLOCK)` in SQL Server). Over-enrollment is strictly impossible; requests exceeding capacity are rejected with HTTP 409 `CAPACITY_EXCEEDED`.
6. **Active Editing Lease Revocation on Submit:** Finalizing an attempt atomically revokes the editing lease (`lease_token_hash = None`, `lease_expires_at = None`). Subsequent answer modifications or lease renewals are strictly rejected.

## 3. Test Cases
- `TC-IT11-001`: Single Active Editing Lease Acquisition & Heartbeat Renewal (Algorithm 07): Student begins attempt, receives lease token, and heartbeat extends lease expiration.
- `TC-IT11-002`: Concurrent Window/Tab Takeover & Lease Fencing: Stale window answer persistence is rejected with HTTP 409 Conflict after lease takeover.
- `TC-IT11-003`: Submission Idempotency Under Concurrent Double-Submit: Simultaneous duplicate submit requests return consistent HTTP 200 without duplicate grading.
- `TC-IT11-004`: Optimistic Concurrency & Course Changeset Fingerprint Guard: Stale review version during approval is rejected with HTTP 409 Conflict.
- `TC-IT11-005`: Concurrent Enrollment Capacity Enforcement: Row-level locks prevent over-enrollment on capacity-limited courses.
- `TC-IT11-006`: Active Editing Lease Revocation on Submit: Attempt submission revokes editing lease and blocks further answer persistence.

## 4. Execution Methodology
- Real Google Chrome browser automation via Playwright (`channel="chrome"`).
- Dual-persisted annotated screenshots (`qa-audit/screenshots/` and `qa-audit/iterations/iteration-11/evidence/`).
- Direct SQL Server database inspection inside `pwd301_web` container via SQLAlchemy to verify lease tokens, hashes, epochs, rows, and constraints.
