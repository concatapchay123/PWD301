# Iteration 11: Test Coverage Analysis

## 1. Domain Coverage: Concurrency, Race Conditions, Single Active Editing Lease & Submissions
- **Tables Audited & Inspected in Microsoft SQL Server:**
  - `assessment_attempts`: Verified `lease_token_hash`, `lease_epoch`, `lease_expires_at`, `submitted_at`, `finalized_at`, `submission_idempotency_key`, `editor_session_id`.
  - `assessment_results`: Verified exactly 1 row generated on concurrent submission, correct calculation of `raw_score` and `percent_score`.
  - `attempt_answers`: Verified lease fencing prevents stale tab writes, client sequence enforcement.
  - `courses`: Verified `capacity` limit, row locks (`WITH (UPDLOCK, HOLDLOCK)`), optimistic concurrency `review_version`.
  - `enrollments`: Verified single active enrollment per student, capacity enforcement under concurrent requests.

## 2. API Endpoints Probed
1. `POST /student/assessments/<assessment_id>/start` (TC-IT11-001)
2. `POST /student/attempt/<attempt_id>/lease/renew` (TC-IT11-001, TC-IT11-006)
3. `POST /student/attempt/<attempt_id>/lease/takeover` (TC-IT11-002)
4. `POST /student/attempt/<attempt_id>/answers/<attempt_question_id>` (TC-IT11-002, TC-IT11-003, TC-IT11-006)
5. `POST /student/attempt/<attempt_id>/submit` (TC-IT11-003)
6. `GET /admin/courses/<course_id>` (TC-IT11-004)
7. `POST /admin/courses/<course_id>/review` (TC-IT11-004)
8. `POST /student/courses/<course_id>/enroll` (TC-IT11-005)

## 3. Invariant Verification Coverage
- **Single Active Editing Lease Acquisition & Heartbeat (Algorithm 07):** 100% verified.
- **Concurrent Window/Tab Takeover & Lease Fencing (ADR-005):** 100% verified.
- **Submission Idempotency Under Concurrent Double-Submit:** 100% verified.
- **Optimistic Concurrency & Course Changeset Fingerprint Guard:** 100% verified.
- **Concurrent Enrollment Capacity Enforcement (UPDLOCK, HOLDLOCK):** 100% verified.
- **Active Editing Lease Revocation on Submit:** 100% verified.
