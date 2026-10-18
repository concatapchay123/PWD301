# Iteration 11: Test Cases Specification

## TC-IT11-001: Single Active Editing Lease Acquisition & Heartbeat Renewal (Algorithm 07)
- **Objective:** Verify that starting an assessment attempt issues a single active editing lease with a 32-byte hex token, SHA-256 hash in SQL Server, initial epoch 1, and that heartbeat renewal safely extends the expiration timestamp.
- **Preconditions:** Student `student1@pwd301.local` is enrolled in course 110007 (Assessment 90008).
- **Execution Steps:**
  1. Student initiates assessment attempt via `POST /student/assessments/90008/start`.
  2. Inspect response envelope: assert `attempt_id`, `lease_token`, and status `IN_PROGRESS`.
  3. Query SQL Server: verify `lease_token_hash == SHA256(lease_token)`, `lease_epoch == 1`, and `lease_expires_at > now`.
  4. Record current `lease_expires_at`.
  5. Wait 1 second, then invoke heartbeat `POST /student/attempt/{attempt_id}/lease/renew` with `lease_token`.
  6. Assert HTTP 200, status `IN_PROGRESS`, and new `lease_expires_at > old_lease_expires_at`.
  7. Navigate student to exam taking console (`#/student/assessments/attempt`) in real Chrome.
  8. Capture annotated screenshot `IT11_TC01_Lease_Acquisition_Heartbeat.png`.
- **Expected Result:** PASS. Editing lease issued, SHA-256 digest verified in DB, and heartbeat renews lease expiration.

---

## TC-IT11-002: Concurrent Window/Tab Takeover & Lease Fencing (Algorithm 07)
- **Objective:** Verify that when an editing lease is released or expired and taken over by Tab 2, `lease_epoch` increments, and any stale autosave from Tab 1 is strictly rejected with HTTP 409 Conflict.
- **Preconditions:** In-progress attempt from TC-IT11-001 with active lease token `token_tab1` and epoch 1.
- **Execution Steps:**
  1. Student releases or expires lease, then invokes takeover `POST /student/attempt/{attempt_id}/lease/takeover`.
  2. Assert response issues new `lease_token` (`token_tab2`), and SQL Server reflects `lease_epoch == 2` and new `lease_token_hash`.
  3. Simulate Tab 1 attempting to save an answer using stale `token_tab1` and `lease_epoch: 1` via `POST /student/attempt/{attempt_id}/answer`.
  4. Assert server rejects the stale request with HTTP 409 Conflict (`LEASE_CONFLICT` or `STALE_LEASE_EPOCH`).
  5. Assert database attempt answer is NOT updated with the stale answer.
  6. Capture annotated screenshot `IT11_TC02_Lease_Takeover_Fencing.png`.
- **Expected Result:** PASS. Tab takeover succeeds, epoch increments, and stale tab write is strictly fenced with HTTP 409.

---

## TC-IT11-003: Submission Idempotency Under Concurrent Double-Submit
- **Objective:** Verify that firing concurrent submit requests with the same idempotency key succeeds idempotently without duplicate grading, race corruption, or deadlock.
- **Preconditions:** Active in-progress attempt with valid answer saved.
- **Execution Steps:**
  1. Prepare submission payload with shared `idempotency_key` (UUID v4) and current valid lease token.
  2. Dispatch two simultaneous submit requests (`POST /student/attempt/{attempt_id}/submit`) via asynchronous fetch in browser context.
  3. Assert both requests resolve successfully with HTTP 200.
  4. Verify response payloads contain matching `attempt_id`, `score`, and finalized status.
  5. Query SQL Server: assert attempt status is `SUBMITTED`, exactly 1 `AssessmentResult` record exists, and 0 duplicate attempts or grades created.
  6. Capture annotated screenshot `IT11_TC03_Concurrent_Submit_Idempotency.png`.
- **Expected Result:** PASS. Double-submit is completely idempotent, returning HTTP 200 with 0 duplicate grading records.

---

## TC-IT11-004: Optimistic Concurrency & Course Changeset Fingerprint Guard
- **Objective:** Verify that approving a course staging changeset with a stale `review_version` is rejected with HTTP 409 Conflict to prevent concurrent admin overwrites.
- **Preconditions:** Course staging draft or review in status `SUBMITTED_FOR_REVIEW` or `PENDING`.
- **Execution Steps:**
  1. Create or identify a course submitted for review.
  2. Obtain current valid `review_version`.
  3. Send an approval request `POST /admin/courses/{course_id}/approve` with an intentionally stale/modified `review_version` ("stale_review_ver_9999").
  4. Assert server rejects the mutation with HTTP 409 Conflict (`Bản xét duyệt đã thay đổi. Hãy tải lại và kiểm tra phiên bản mới trước khi duyệt.`).
  5. Send approval request with the authentic `review_version`.
  6. Assert server accepts the approval with HTTP 200.
  7. Capture annotated screenshot `IT11_TC04_Optimistic_Concurrency_Review_Version.png`.
- **Expected Result:** PASS. Stale review version is rejected with HTTP 409 Conflict; matching review version succeeds.

---

## TC-IT11-005: Concurrent Enrollment Capacity Enforcement
- **Objective:** Verify that course capacity limits are strictly enforced under concurrency via SQL Server row locks (`WITH (UPDLOCK, HOLDLOCK)`), preventing over-enrollment.
- **Preconditions:** Course configured with `capacity = 1`.
- **Execution Steps:**
  1. Instructor creates a new course with `capacity: 1`, publishes it, and registers 1 active seat.
  2. First student (`student1@pwd301.local`) enrolls via `POST /student/courses/{course_id}/enroll`. Assert HTTP 200/201, status `ACTIVE`.
  3. Second student attempt or concurrent enrollment request executes against the full course.
  4. Assert server rejects the second enrollment with HTTP 409 Conflict (`CAPACITY_EXCEEDED`: `Course capacity of 1 has been reached.`).
  5. Query SQL Server: assert active enrollments count in `enrollments` table is exactly 1.
  6. Capture annotated screenshot `IT11_TC05_Capacity_Enforcement_Row_Lock.png`.
- **Expected Result:** PASS. Over-enrollment is blocked, active enrollment count strictly matches capacity limit.

---

## TC-IT11-006: Active Editing Lease Revocation on Submit
- **Objective:** Verify that submitting an assessment attempt atomically revokes the editing lease (`lease_token_hash = None`), blocking any subsequent answer modifications or heartbeats.
- **Preconditions:** Assessment attempt submitted in TC-IT11-003.
- **Execution Steps:**
  1. Query SQL Server: verify `lease_token_hash IS NULL` and `lease_expires_at IS NULL` on the submitted attempt.
  2. Attempt to invoke heartbeat `POST /student/attempt/{attempt_id}/lease/renew`. Assert server rejects with HTTP 409/400 (`Assessment attempt is not in progress`).
  3. Attempt to save an answer `POST /student/attempt/{attempt_id}/answer`. Assert server rejects with HTTP 409 `STATE_VIOLATION` (`Assessment attempt has already been submitted`).
  4. Student views submitted exam in browser (`#/student/assessments/results` or attempt view).
  5. Capture annotated screenshot `IT11_TC06_Lease_Revocation_On_Submit.png`.
- **Expected Result:** PASS. Editing lease is revoked in DB, preventing post-submission modifications.
