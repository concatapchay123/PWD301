# Iteration 18 Test Plan: Risk-Driven Exploratory Testing, Adversarial Business Logic Probing & Defect Clustering

**Iteration:** 18  
**Scope:** Risk-Driven Exploratory Testing, Adversarial Input Probing, Anti-Tamper Business Logic, and Defect Clustering.  
**Execution Target:** Localhost Docker (`http://localhost:5000`)  
**Browser Engine:** Real Google Chrome 155 (`channel="chrome"`) via Playwright  
**Lead Auditor:** AGENT 08 — Independent Auditor & Regression QA, AGENT 05 — Security & RBAC QA, AGENT 03 — Backend & API QA  

---

## 1. High-Risk Focus Areas & Objectives

1. **Strict Lifetime Enrollment (Rule 10.10):**
   - Probe `/student/courses/<course_id>/leave` to verify self-unenrollment is locked and permanently disabled (HTTP 403 Forbidden).
2. **Video Pacing Engine & Wall-Clock Enforcement (Algorithm 04):**
   - Probe `/student/lessons/<lesson_id>/progress` with adversarial forward-seek time jumps (e.g. 99,999s increment) to verify server-side clamping (`bounded_sec = min(sec_int, 60)`) and wall-clock enforcement.
3. **Assessment Attempt Idempotency & Replay Protection (Algorithm 07):**
   - Probe `/student/attempt/<attempt_id>/submit` with concurrent duplicate submits and mismatched idempotency keys to confirm server-authoritative status locking (`SUBMITTED`) and conflict rejection (HTTP 409 Conflict).
4. **Manual Grading Boundary Enforcement (ADR-003):**
   - Probe `/instructor/attempts/<attempt_id>/grades/<attempt_question_id>` with adversarial scores ($> \text{max\_points}$ and $< 0$) to verify score validation and `MaxPointsExceededError`.
5. **Cross-Instructor Object-Level Authorization (IDOR Defense):**
   - Probe cross-instructor attempt access to verify Instructor B cannot grade or view attempts belonging to Instructor A's courses.
6. **Anti-Leak Exam Delivery Invariant (Rule 10 Anti-Leak):**
   - Probe candidate attempt delivery (`/student/attempt/<attempt_id>`) to confirm total suppression of `is_correct`, explanations, and integer database PKs during active exam execution.

---

## 2. Methodology & Evidence Contract

- All operations will be conducted using authenticated browser contexts in real Google Chrome 155 with dual-persisted visual evidence banners (`annotate()`).
- In-browser evaluation via `ApiClient.request` with automatic CSRF token management.
- Test artifacts dual-persisted in `qa-audit/iterations/iteration-18/evidence/` and `qa-audit/screenshots/`.
