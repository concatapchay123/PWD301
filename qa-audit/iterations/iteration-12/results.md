# Iteration 12: Execution Results

**Iteration:** 12  
**Domain:** Boundary Values, Negative Tests, Invalid States & Prerequisite Cycles  
**Timestamp:** 2026-10-18T07:12:04Z  
**Browser Engine:** Real Google Chrome 155 via Playwright (`channel="chrome"`)  
**Backend:** Local Docker container `pwd301_web` (Flask REST API + SQL Server)  
**Execution Summary:** 6 executed | 6 PASS | 0 FAIL (0 Defects Discovered)

---

## 1. Test Case Execution Breakdown

| Test ID | Test Case Title | Status | Evidence Screenshot | DB & Protocol Verification |
|---|---|---|---|---|
| **TC-IT12-001** | Prerequisite Cycle Prevention (DAG Invariant Algorithm 03) | **PASS** | `IT12_TC01_Prerequisite_Cycle_Prevention.png` | Valid prerequisite B->A committed in SQL Server (`b_requires_a = 1`). Cyclic edge A->B strictly rejected with HTTP 409 (`CYCLE_DETECTED`). Self-cycle A->A strictly rejected with HTTP 400. Zero invalid edges in SQL Server (`a_requires_b = 0`, `a_requires_a = 0`). |
| **TC-IT12-002** | Expired Editing Lease Autosave Fencing (Algorithm 07) | **PASS** | `IT12_TC02_Expired_Lease_Autosave_Fencing.png` | Autosave with timestamp past expiration strictly rejected with HTTP 409 Conflict (`LEASE_CONFLICT` / `Editing lease has expired.`). |
| **TC-IT12-003** | Corrupt & Tampered Lease Token Defense | **PASS** | `IT12_TC03_Corrupt_Lease_Token_Defense.png` | Tampered token rejected across both answer autosave (`LEASE_CONFLICT`: *"Editing lease was lost..."*) and heartbeat renewal (HTTP 409 Conflict). |
| **TC-IT12-004** | Out-of-Bounds Sequence Number Fencing (Client Sequencing) | **PASS** | `IT12_TC04_Client_Sequencing_Fencing.png` | Valid sequence 10 accepted (HTTP 200). Stale sequence 5 strictly rejected with HTTP 409 Conflict (`STALE_ANSWER`). SQL Server `attempt_answer_events` logged rejected event (`accepted = 0`, `rejection_reason = 'STALE'`, `client_sequence = 5`). |
| **TC-IT12-005** | Invalid State Transition Rejection (State Machine Guard) | **PASS** | `IT12_TC05_Invalid_State_Transition_Rejection.png` | Attempted direct publication DRAFT -> PUBLISHED strictly rejected with HTTP 409 Conflict (`STATE_VIOLATION`: *"Cannot transition course from 'DRAFT' to 'PUBLISHED'."*). SQL Server status unchanged in `DRAFT`. |
| **TC-IT12-006** | Boundary & Negative Value Validation | **PASS** | `IT12_TC06_Boundary_Negative_Value_Validation.png` | Progress > 100% and negative grade rejected with HTTP 400. Negative capacity (-5) rejected with HTTP 400. Oversized title (255 chars) rejected with HTTP 400. |

---

## 2. In-Depth Empirical Findings

### TC-IT12-001: Prerequisite Cycle Prevention (DAG Invariant Algorithm 03)
- **Setup:** Two courses created: Course A (`3847710f-f968-494c-9d43-2f768a72a5f7`, *Môn A DAG_5ED87C*) and Course B (`cda59494-3147-4126-8cbb-e8089b3ba052`, *Môn B DAG_5ED87C*), both in `PUBLISHED` status. Valid prerequisite dependency (Course B requires Course A) was committed in SQL Server (`approval_status = 'APPROVED'`).
- **Action 1 (Direct Cycle A -> B):** Instructor attempted to add Course B as a prerequisite to Course A via `POST /instructor/courses/<ca_id>/prerequisites` with `{"prerequisite_course_id": cb_id}`.
  - Server strictly rejected the cyclic dependency with **HTTP 409 Conflict** (`error: "Môn tiên quyết sẽ tạo chu trình phụ thuộc."`).
- **Action 2 (Self-Reference Cycle A -> A):** Instructor attempted to add Course A as its own prerequisite via `POST /instructor/courses/<ca_id>/prerequisites` with `{"prerequisite_course_id": ca_id}`.
  - Server strictly rejected the self-reference with **HTTP 400 Bad Request** (`error: "A course cannot be a prerequisite of itself."`).
- **SQL Server Verification:** Query confirmed `b_requires_a == 1`, `a_requires_b == 0`, and `a_requires_a == 0`. The database graph remains an acyclic directed graph (DAG).

### TC-IT12-002: Expired Editing Lease Autosave Fencing (Algorithm 07)
- **Setup:** Student `student1@pwd301.local` initiated assessment attempt `14ae8b18-d583-4d01-a0aa-058d83f409f0` for Assessment 90008.
- **Action:** Lease expiration was fast-forwarded in SQL Server to 5 seconds in the past (`lease_expires_at = utc_now() - timedelta(seconds=5)`). Candidate attempted to autosave an answer via `POST /student/attempt/<attempt_id>/answers/<aq_id>` with the expired lease.
- **Protocol Proof:** Server strictly rejected the autosave with **HTTP 409 Conflict** (`error: "Editing lease has expired."`).
- **Browser State:** Candidate redirected to `#/student/assessments/attempt`, verifying fail-closed state where answer inputs are locked and warning banner is presented.

### TC-IT12-003: Corrupt & Tampered Lease Token Defense
- **Setup:** Attempt `14ae8b18-d583-4d01-a0aa-058d83f409f0` with lease expiration restored to valid future timestamp (`utc_now() + timedelta(seconds=120)`).
- **Action 1 (Tampered Autosave):** Candidate dispatched answer autosave using tampered token `"deadbeef_corrupt_tampered_token_9999"`.
  - Server strictly returned **HTTP 409 Conflict** (`LEASE_CONFLICT`: *"Editing lease was lost or taken over by another window."*).
- **Action 2 (Tampered Heartbeat):** Candidate dispatched heartbeat renewal via `POST /student/attempt/<attempt_id>/lease/renew` using the same corrupt token.
  - Server strictly returned **HTTP 409 Conflict**, preventing unauthorized renewal of the active lease.

### TC-IT12-004: Out-of-Bounds Sequence Number Fencing (Client Sequencing)
- **Setup:** Clean lease epoch refreshed for attempt (`lease_epoch = 3`).
- **Action 1 (Baseline Sequence 10):** Candidate saved answer with `client_sequence: 10`.
  - Server accepted the write with **HTTP 200 OK** and recorded `last_client_sequence = 10`.
- **Action 2 (Stale Sequence 5):** Candidate attempted to save an answer with `client_sequence: 5` ($5 \le 10$, simulating out-of-order network arrival or replayed payload).
  - Server strictly rejected the stale sequence with **HTTP 409 Conflict** (`STALE_ANSWER`: *"Stale answer sequence (5 <= 10)."*).
- **Audit & Persistence Proof:** SQL Server query on `attempt_answer_events` confirmed 2 total events, with exactly 1 rejected event:
  - `accepted = 0` (False)
  - `rejection_reason = 'STALE'`
  - `client_sequence = 5`

### TC-IT12-005: Invalid State Transition Rejection (State Machine Guard)
- **Setup:** Course *Khóa Draft State 5ED87C* (`f3d6f232-581e-4b29-971d-8b04371f88c3`) created in `DRAFT` status.
- **Action:** Administrator attempted to directly publish the course via `POST /admin/courses/<course_id>/publish` (violating state machine: `DRAFT` must first transition to `SUBMITTED_FOR_REVIEW` -> `APPROVED` before `PUBLISHED`).
- **Protocol & DB Proof:**
  - Server strictly rejected the illegal transition with **HTTP 409 Conflict** (`STATE_VIOLATION`: *"Cannot transition course from 'DRAFT' to 'PUBLISHED'."*).
  - SQL Server confirmed course status remained unchanged in `'DRAFT'`.

### TC-IT12-006: Boundary & Negative Value Validation
- **Action 1 (Out-of-Bounds Completion Rules):** Instructor attempted to set `minimum_progress_percent: 150.0` and `minimum_grade_score: -10.0` via `POST /instructor/courses/<course_id>/completion-rules`.
  - Server strictly rejected with **HTTP 400 Bad Request** (`CompletionRuleValidationError: "minimum_progress_percent must be between 0.00 and 100.00."`).
- **Action 2 (Negative Course Capacity):** Instructor attempted to update course capacity to `-5` via `PUT /instructor/courses/<course_id>`.
  - Server strictly rejected with **HTTP 400 Bad Request** (`CourseValidationError: "capacity must be a positive integer."`).
- **Action 3 (Oversized Course Title):** Instructor attempted to create a course with a 255-character title via `POST /instructor/courses`.
  - Server strictly rejected with **HTTP 400 Bad Request** (`CourseValidationError: "title cannot exceed 200 characters."`).
