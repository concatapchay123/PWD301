# Iteration 12: Coverage Analysis

**Iteration:** 12  
**Domain:** Boundary Values, Negative Tests, Invalid States & Prerequisite Cycles  
**Execution Timestamp:** 2026-10-18T07:12:04Z  

---

## 1. Endpoints Exercised & Verified

| HTTP Method | Route | Category | Status Codes Verified |
|---|---|---|---|
| `POST` | `/instructor/courses/<course_id>/prerequisites` | Prerequisite Dependency & DAG | 400 (Self-ref), 409 (Cycle) |
| `POST` | `/student/assessments/<assessment_id>/start` | Assessment Attempt Lifecycle | 200 / 201 (Start/Resume) |
| `GET` | `/student/attempt/<attempt_id>` | Assessment Attempt Delivery | 200 (Delivery schema) |
| `POST` | `/student/attempt/<attempt_id>/answers/<attempt_question_id>` | Autosave & Client Sequencing | 200 (Valid), 409 (Expired/Tampered/Stale) |
| `POST` | `/student/attempt/<attempt_id>/lease/renew` | Lease Heartbeat Renewal | 409 (Corrupt token) |
| `POST` | `/admin/courses/<course_id>/publish` | Course State Machine | 409 (Direct draft publish) |
| `POST` | `/instructor/courses/<course_id>/completion-rules` | Course Completion Rules | 400 (Out-of-bounds percentage & grade) |
| `PUT` | `/instructor/courses/<course_id>` | Course Metadata Modification | 400 (Negative capacity) |
| `POST` | `/instructor/courses` | Course Creation Boundary | 400 (Oversized title > 200 chars) |

---

## 2. Database Models & Tables Verified

| Model | Table Name | Columns & Constraints Inspected |
|---|---|---|
| `Course` | `courses` | `status` ('DRAFT'), `capacity`, `title`, `owner_instructor_id` |
| `CoursePrerequisite` | `course_prerequisites` | `course_id`, `prerequisite_course_id`, `approval_status`, DAG cycle constraint |
| `AssessmentAttempt` | `assessment_attempts` | `lease_token_hash`, `lease_expires_at`, `lease_epoch`, `status` |
| `AttemptQuestion` | `attempt_questions` | `attempt_id`, `question_id` |
| `AttemptAnswer` | `attempt_answers` | `last_client_sequence`, `answer_version` |
| `AttemptAnswerEvent` | `attempt_answer_events` | `client_sequence`, `accepted = 0`, `rejection_reason = 'STALE'` |
| `CourseCompletionRule` | `course_completion_rules` | `minimum_progress_percent` bounded between 0.00 and 100.00 |

---

## 3. Invariants & Business Logic Audited

1. **Algorithm 03: Prerequisite Cycle Detection (DAG Invariant):**
   - Verified that reflexive edges ($A \rightarrow A$) are blocked fail-closed before graph traversal.
   - Verified that transitive circular dependencies ($A \rightarrow B \rightarrow A$) are detected via iterative DFS and rejected with HTTP 409 Conflict.
2. **Algorithm 07: Single Active Editing Lease & Heartbeat Fencing:**
   - Verified that requests with timestamps past `lease_expires_at` are rejected with HTTP 409 `LEASE_CONFLICT`.
   - Verified that tampered or forged lease tokens are rejected with HTTP 409 `LEASE_CONFLICT`.
3. **Client Sequencing Fencing & Event Audit Trail:**
   - Verified that client sequence numbers $\le$ `last_client_sequence` are rejected with HTTP 409 `STALE_ANSWER`.
   - Verified that every rejected answer mutation is recorded in `attempt_answer_events` with `accepted = False` and `rejection_reason = 'STALE'`.
4. **Course State Machine Integrity:**
   - Verified that courses in `DRAFT` status cannot jump directly to `PUBLISHED` status via admin publish endpoint, enforcing the mandatory review workflow (`DRAFT` $\rightarrow$ `SUBMITTED_FOR_REVIEW` $\rightarrow$ `APPROVED` $\rightarrow$ `PUBLISHED`).
5. **Boundary & Negative Value Defenses:**
   - Verified input validation against malicious/ill-formed payloads including numeric bounds ($> 100\%$, $< 0$) and string lengths ($> 200$ chars).
