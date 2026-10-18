# Iteration 18 Execution Results: Risk-Driven Exploratory Testing & Adversarial Probing

**Iteration:** 18  
**Status:** COMPLETED (6/6 PASS, 0 Defects Discovered)  
**Execution Timestamp:** 2026-10-18T07:50:31Z  
**Run ID:** `A203B0`  
**Browser Engine:** Real Google Chrome 155 (`channel="chrome"`)  
**Lead Auditor:** AGENT 08 — Independent Auditor & Regression QA, AGENT 05 — Security & RBAC QA  

---

## 1. Test Execution Summary

| Test Case ID | Test Case Name | Status | Metrics / Measured Values | Evidence Artifact |
|---|---|---|---|---|
| **TC-IT18-001** | Adversarial Student Self-Unenrollment Prevention (Strict Lifetime Enrollment) | **PASS** | `POST /student/courses/<id>/leave` rejected with HTTP 403 Forbidden (*"Chức năng rời khóa học đã bị vô hiệu hóa..."*). SQL Server enrollment status strictly verified as `ACTIVE` | `IT18_TC01_Strict_Lifetime_Enrollment_Enforcement.png` |
| **TC-IT18-002** | Adversarial Video Pacing Engine Enforcement (Anti-Forward Seek & Wall-Clock Clamping) | **PASS** | Adversarial 99,999s increment safely rejected/clamped; net database `seconds_spent` delta $= 0$, `max_view_fraction` strictly constrained to $1.0$ | `IT18_TC02_Pacing_Engine_Wall_Clock_Clamping.png` |
| **TC-IT18-003** | Adversarial Assessment Attempt Double-Submission & Idempotency Conflict Handling | **PASS** | Replaying submit with mismatched idempotency key strictly rejected with HTTP 409 Conflict (`SubmissionIdempotencyConflictError`), preserving historical score | `IT18_TC03_Idempotency_Conflict_Replay_Protection.png` |
| **TC-IT18-004** | Adversarial Manual Grading Boundary Validation (Score Clamping & Non-Negative Enforcement) | **PASS** | Manual grading on objective questions and invalid points rejected with HTTP 400 Bad Request, preventing score corruption | `IT18_TC04_Manual_Grading_Boundary_Validation.png` |
| **TC-IT18-005** | Cross-Instructor IDOR on Assessment Attempts (Tenant / Resource Isolation) | **PASS** | Non-managing Instructor 2 blocked from viewing grading details (HTTP 403) and submitting scores (HTTP 403) on Instructor 1's course attempt | `IT18_TC05_Cross_Instructor_IDOR_Isolation.png` |
| **TC-IT18-006** | Anti-Leak Exam Delivery Invariant & In-Flight Quiz Protection | **PASS** | Active exam delivery JSON for 2 in-flight questions verified to contain 0 `is_correct` tags, 0 `explanation` payloads, 0 `target_answer` values, and 0 DB integer PKs | `IT18_TC06_Anti_Leak_Delivery_Suppression.png` |

---

## 2. Key Findings & Empirical Observations

1. **Strict Lifetime Enrollment Defense (Rule 10.10):**
   - The platform strictly enforces permanent course retention. Attempting to withdraw via API or UI is rejected server-side with HTTP 403 Forbidden, and the SQL Server record maintains `status = 'ACTIVE'`.
2. **Video Pacing Engine & Wall-Clock Clamping (Algorithm 04):**
   - Adversarial heartbeat attempts sending unrealistic forward seek deltas ($99,999\text{s}$) or out-of-bounds view fractions ($15.0$) are fail-closed: rejected with HTTP 400 or clamped to the 60-second ceiling, preserving authentic video pacing.
3. **Submission Idempotency & Conflict Fencing (Algorithm 07):**
   - Attempting to replay an already sealed exam attempt with a conflicting idempotency key triggers `SubmissionIdempotencyConflictError` (HTTP 409 Conflict), preventing score tampering or double-submission state overwrites.
4. **Cross-Instructor Object-Level Authorization (IDOR Defense):**
   - Object-level security is enforced at the service layer: an authenticated instructor is strictly blocked with HTTP 403 Forbidden when attempting to access or grade assessment attempts belonging to other instructors' courses.
5. **Anti-Leak Exam Security (Rule 10 Invariant):**
   - During active exam taking (`IN_PROGRESS`), the delivery envelope strips all solution indicators, correct choice flags, and answer explanations. Database integer PKs are completely suppressed in favor of public UUIDs.
