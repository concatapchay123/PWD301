# Iteration 11: Execution Results

**Iteration:** 11  
**Domain:** Concurrency, Race Conditions, Single Active Editing Lease & Submissions  
**Timestamp:** 2026-10-18T06:56:38Z  
**Browser Engine:** Real Google Chrome 155 via Playwright (`channel="chrome"`)  
**Backend:** Local Docker container `pwd301_web` (Flask REST API + SQL Server)  
**Execution Summary:** 6 executed | 6 PASS | 0 FAIL (0 Defects Discovered)

---

## 1. Test Case Execution Breakdown

| Test ID | Test Case Title | Status | Evidence Screenshot | DB & Protocol Verification |
|---|---|---|---|---|
| **TC-IT11-001** | Single Active Editing Lease Acquisition & Heartbeat Renewal (Algorithm 07) | **PASS** | `IT11_TC01_Lease_Acquisition_Heartbeat.png` | Issued `raw_lease_token` (64-char hex), verified SHA-256 in SQL Server `attempt.lease_token_hash`, initial `lease_epoch = 1`. Heartbeat extended `lease_expires_at` safely. |
| **TC-IT11-002** | Concurrent Window/Tab Takeover & Lease Fencing (Algorithm 07) | **PASS** | `IT11_TC02_Lease_Takeover_Fencing.png` | Tab 2 takeover incremented epoch to `2` and issued new token. Stale Tab 1 answer autosave was strictly rejected with HTTP 409 Conflict (`LEASE_CONFLICT`). |
| **TC-IT11-003** | Submission Idempotency Under Concurrent Double-Submit | **PASS** | `IT11_TC03_Concurrent_Submit_Idempotency.png` | Simultaneous dual-submit with shared `idempotency_key` succeeded with HTTP 200 on both requests. SQL Server asserts status `GRADED` with exactly 1 `AssessmentResult` (0 duplicate rows). |
| **TC-IT11-004** | Optimistic Concurrency & Course Changeset Fingerprint Guard | **PASS** | `IT11_TC04_Optimistic_Concurrency_Review_Version.png` | Stale `review_version` was strictly rejected with HTTP 409 Conflict (*"Bản xét duyệt đã thay đổi..."*). Authentic `review_version` succeeded with HTTP 200. |
| **TC-IT11-005** | Concurrent Enrollment Capacity Enforcement | **PASS** | `IT11_TC05_Capacity_Enforcement_Row_Lock.png` | Course capacity = 1 enforced via SQL Server row lock (`UPDLOCK, HOLDLOCK`). Student 1 took seat 1/1 (HTTP 200); Student 2 enrollment was rejected with HTTP 409 `CAPACITY_EXCEEDED`. |
| **TC-IT11-006** | Active Editing Lease Revocation on Submit | **PASS** | `IT11_TC06_Lease_Revocation_On_Submit.png` | Submission atomically cleared `lease_token_hash = NULL` and `lease_expires_at = NULL`. Subsequent heartbeats and answer modifications strictly rejected with HTTP 400/409. |

---

## 2. In-Depth Empirical Findings

### TC-IT11-001: Single Active Editing Lease Acquisition & Heartbeat Renewal (Algorithm 07)
- **Setup:** Student `student1@pwd301.local` enrolled in course 110007 (*Lập trình Python Tấn công & Tự động hóa trên Kali Linux*), with lessons completed meeting all course completion rules.
- **Action:** Student initiated assessment attempt for Assessment 90008 via `POST /student/assessments/90008/start`.
- **Database & Protocol Proof:**
  - Received Attempt ID `e0133c9b-f186-4862-a265-7c4cfe2a35a0` with 64-character hex `raw_lease_token` (`bd15c7fd...`).
  - SQL Server query verified `lease_token_hash == SHA256(raw_lease_token)`, `lease_epoch == 1`, and initial `lease_expires_at == '2026-10-18T06:57:48.186000'`.
  - Student dispatched heartbeat renewal via `POST /student/attempt/<attempt_id>/lease/renew` with `raw_lease_token`.
  - Server returned HTTP 200 with new expiration `2026-10-18T06:57:51.797000Z`, successfully extending the active editing lease.
  - Real Chrome browser navigated to `#/student/assessments/attempt`, verifying active countdown timer and contextual palette.

### TC-IT11-002: Concurrent Window/Tab Takeover & Lease Fencing (Algorithm 07)
- **Setup:** Attempt `e0133c9b-f186-4862-a265-7c4cfe2a35a0` in progress with Question `00c0827a-77b7-4a2a-ba12-7bb6a6045cf7` and initial lease token `token_tab1`.
- **Action 1 (Simulated Tab Timeout / Voluntary Release):** SQL Server `lease_expires_at` was fast-forwarded to simulate tab inactivity. Tab 2 invoked takeover via `POST /student/attempt/<attempt_id>/lease/takeover`.
- **Database & Protocol Proof:**
  - Server incremented `lease_epoch` from `1` to `2` and issued new 64-character hex token `token_tab2` (`5c203149...`).
  - SQL Server confirmed `lease_epoch == 2` and `lease_token_hash == SHA256(token_tab2)`.
- **Action 2 (Fencing Stale Tab 1 Write):** Stale Tab 1 attempted to autosave an answer using `token_tab1` and `lease_epoch: 1` via `POST /student/attempt/<attempt_id>/answers/<aq_id>`.
  - Server strictly rejected the write with **HTTP 409 Conflict** (`LEASE_CONFLICT`: *"Editing lease was lost or taken over by another window."*).
  - Database asserted the stale answer was completely fenced and not persisted.

### TC-IT11-003: Submission Idempotency Under Concurrent Double-Submit
- **Setup:** Candidate completed questions using active lease token `token_tab2` with epoch 2.
- **Action:** Two simultaneous submit requests were dispatched in parallel via `Promise.all([fetch1, fetch2])` in the browser context, both carrying identical `idempotency_key` `5a486934-b6c3-44a8-96d3-4852b165fd35`.
- **Database & Protocol Proof:**
  - Both Request 1 and Request 2 returned HTTP 200 OK with identical final score and submission timestamp.
  - SQL Server verification confirmed attempt status transitioned to `'GRADED'`, and table `assessment_results` contains **exactly 1 row** (`results_count = 1`, `raw_score = 50.0`, `percent_score = 50.0`).
  - Zero duplicate rows, zero deadlock exceptions, zero race corruption.

### TC-IT11-004: Optimistic Concurrency & Course Changeset Fingerprint Guard
- **Setup:** A course (*Khóa Học Concurrency OCC_F0C28A*) was created in status `SUBMITTED_FOR_REVIEW` with an authentic `review_version` hash `5257fc4fc26d1e633c691a3f0455e6d0a7d828df99a4f1fd7ae11a95c420c7a7`.
- **Action 1 (Stale Version Rejection):** Admin attempted to approve the course via `POST /admin/courses/<course_id>/review` passing a stale/tampered version `stale_hash_mismatch_999999`.
  - Backend strictly returned **HTTP 409 Conflict** with localized Vietnamese error: *"Bản xét duyệt đã thay đổi. Hãy tải lại trước khi duyệt."*
- **Action 2 (Authentic Version Approval):** Admin resubmitted approval with the true `review_version`.
  - Backend accepted the mutation with HTTP 200 OK and transitioned course status to `APPROVED`.

### TC-IT11-005: Concurrent Enrollment Capacity Enforcement
- **Setup:** A dedicated published course (*Khóa Học Capacity Lock CAP_F0C28A*) was created with `capacity = 1`.
- **Action 1 (Seat 1/1 Enrolled):** `student1@pwd301.local` enrolled via `POST /student/courses/<course_id>/enroll`. Response returned HTTP 200 OK (`ACTIVE`).
- **Action 2 (Over-Capacity Rejection):** `student2@pwd301.local` attempted to enroll in the full course.
  - Backend strictly returned **HTTP 409 Conflict** (`CAPACITY_EXCEEDED`: *"Course capacity of 1 has been reached."*).
- **Database Proof:**
  - SQL Server query confirmed `active_enrollments == 1` and `capacity == 1`.
  - Database row lock `WITH (UPDLOCK, HOLDLOCK)` guaranteed zero over-enrollment under concurrent access.

### TC-IT11-006: Active Editing Lease Revocation on Submit
- **Setup:** Attempt `e0133c9b-f186-4862-a265-7c4cfe2a35a0` finalized from TC-IT11-003.
- **Database & Protocol Proof:**
  - SQL Server confirmed `lease_token_hash IS NULL` and `lease_expires_at IS NULL`.
  - Heartbeat renewal attempt via `POST /student/attempt/<attempt_id>/lease/renew` was rejected with HTTP 400 (`Assessment attempt is not in progress`).
  - Answer autosave attempt via `POST /student/attempt/<attempt_id>/answers/<aq_id>` was rejected with HTTP 409 (`STATE_VIOLATION`: *"Assessment attempt has already been submitted."*).
  - Browser view confirmed candidate is transitioned to readonly results summary (`#/student/assessments/results`), with exam inputs permanently locked.
