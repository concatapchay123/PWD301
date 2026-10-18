# Iteration 12: Test Cases Specification

## TC-IT12-001: Prerequisite Cycle Prevention (DAG Invariant Algorithm 03)
- **Objective:** Verify that adding a prerequisite course that forms a circular dependency is detected via Algorithm 03 cycle traversal and rejected with HTTP 409 Conflict.
- **Preconditions:** Instructor owns two courses: Course A and Course B.
- **Execution Steps:**
  1. Add prerequisite edge: Course B requires Course A (`POST /instructor/courses/{course_b}/prerequisites` with `prerequisite_course_id: course_a`). Assert HTTP 200/201.
  2. Attempt to add reciprocal edge: Course A requires Course B (`POST /instructor/courses/{course_a}/prerequisites` with `prerequisite_course_id: course_b`).
  3. Assert server rejects the cyclic mutation with HTTP 409 Conflict (`code: "CYCLE_DETECTED"`, message: *"creates a cyclic dependency in the prerequisite graph"*).
  4. Query SQL Server: verify `course_prerequisites` table contains only the edge `B -> A`, and `A -> B` was never inserted.
  5. Capture annotated screenshot `IT12_TC01_Prerequisite_Cycle_Prevention.png`.
- **Expected Result:** PASS. Cycle is detected and rejected with HTTP 409 Conflict; DAG invariant is preserved.

---

## TC-IT12-002: Expired Editing Lease Autosave Fencing (Algorithm 07)
- **Objective:** Verify that when a student's active editing lease expires, subsequent autosaves are rejected with HTTP 409 Conflict without modifying database answer state.
- **Preconditions:** Student starts assessment attempt, receiving valid lease token.
- **Execution Steps:**
  1. Student initiates assessment attempt, obtaining `attempt_id` and `raw_lease_token`.
  2. Fast-forward SQL Server `lease_expires_at` to 5 seconds in the past (`now - 5s`).
  3. Student dispatches autosave request `POST /student/attempt/{attempt_id}/answers/{aq_id}` with the expired lease token.
  4. Assert server rejects the autosave with HTTP 409 Conflict (`code: "LEASE_CONFLICT"`, message: *"Editing lease has expired"*).
  5. Query SQL Server: verify `attempt_answers` table does not contain the uncommitted answer.
  6. Capture annotated screenshot `IT12_TC02_Expired_Lease_Autosave_Fencing.png`.
- **Expected Result:** PASS. Expired lease is fenced with HTTP 409 Conflict; answer is not persisted.

---

## TC-IT12-003: Corrupt & Tampered Lease Token Defense
- **Objective:** Verify that submitting corrupted, malformed, or tampered lease tokens is rejected fail-closed with HTTP 409 Conflict.
- **Preconditions:** In-progress assessment attempt with valid lease token in SQL Server.
- **Execution Steps:**
  1. Student dispatches autosave request `POST /student/attempt/{attempt_id}/answers/{aq_id}` with a corrupted token `"deadbeef_tampered_token_invalid_hash"`.
  2. Assert server rejects the request with HTTP 409 Conflict (`code: "LEASE_CONFLICT"`, message: *"Editing lease was lost or taken over by another window"*).
  3. Student dispatches heartbeat request `POST /student/attempt/{attempt_id}/lease/renew` with the corrupted token.
  4. Assert server rejects heartbeat with HTTP 409 Conflict.
  5. Query SQL Server: verify `lease_token_hash` in `assessment_attempts` remains untouched.
  6. Capture annotated screenshot `IT12_TC03_Corrupt_Lease_Token_Defense.png`.
- **Expected Result:** PASS. Corrupted and tampered tokens are rejected with HTTP 409 Conflict.

---

## TC-IT12-004: Out-of-Bounds Sequence Number Fencing (Client Sequencing)
- **Objective:** Verify that client sequence numbers must be strictly monotonic ($N_{new} > N_{last}$), and that replayed or stale sequence numbers are rejected and logged in `attempt_answer_events`.
- **Preconditions:** In-progress attempt with active valid lease.
- **Execution Steps:**
  1. Student submits valid answer with `client_sequence: 5`. Assert HTTP 200 OK (`last_client_sequence == 5`).
  2. Student submits another answer with a stale sequence `client_sequence: 3` (simulating out-of-order packet or replay).
  3. Assert server rejects the stale packet with HTTP 409 Conflict (`code: "STALE_ANSWER"`, message: *"Stale answer sequence (3 <= 5)"*).
  4. Query SQL Server: verify `attempt_answer_events` recorded a row with `accepted = 0`, `rejection_reason = 'STALE'`, and `client_sequence = 3`.
  5. Capture annotated screenshot `IT12_TC04_Client_Sequencing_Fencing.png`.
- **Expected Result:** PASS. Stale sequence is rejected with HTTP 409 Conflict and audit event is recorded.

---

## TC-IT12-005: Invalid State Transition Rejection
- **Objective:** Verify that invalid lifecycle state transitions are strictly blocked by state machine guards.
- **Preconditions:** Course created in `DRAFT` status; Administrator authenticated.
- **Execution Steps:**
  1. Administrator attempts to publish the course directly from `DRAFT` status via `POST /admin/courses/{course_id}/publish` without prior submission or approval.
  2. Assert server rejects the invalid transition with HTTP 409 Conflict (`code: "STATE_VIOLATION"`).
  3. Query SQL Server: verify `courses.status` remains `DRAFT`.
  4. Capture annotated screenshot `IT12_TC05_Invalid_State_Transition_Rejection.png`.
- **Expected Result:** PASS. Direct transition DRAFT -> PUBLISHED is blocked with HTTP 409 Conflict.

---

## TC-IT12-006: Boundary & Negative Value Validation
- **Objective:** Verify that negative values, percentages exceeding 100%, and oversized string boundaries are rejected with HTTP 400 Bad Request.
- **Preconditions:** Instructor authenticated.
- **Execution Steps:**
  1. Negative/Oversized Completion Rule: Send `minimum_progress_percent: 150.0` or `-10.0` to `POST /instructor/courses/{course_id}/completion-rules`. Assert HTTP 400 Bad Request (`VALIDATION_ERROR`).
  2. Negative Course Capacity: Send `capacity: -5` or `capacity: 0` to `PUT /instructor/courses/{course_id}`. Assert HTTP 400 Bad Request (`VALIDATION_ERROR`).
  3. Oversized Title Boundary: Send title of 255 characters (> 200 character limit) to `POST /instructor/courses`. Assert HTTP 400 Bad Request (`VALIDATION_ERROR`).
  4. Capture annotated screenshot `IT12_TC06_Boundary_Negative_Value_Validation.png`.
- **Expected Result:** PASS. All out-of-bounds boundary values are rejected with HTTP 400 Bad Request.
