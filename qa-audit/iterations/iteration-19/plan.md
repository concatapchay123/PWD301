# Iteration 19 Test Plan: Comprehensive Regression Suite

**Iteration:** 19  
**Scope:** Comprehensive platform-wide regression suite re-verifying all opened defects, boundary invariants, upload policies, concurrency fencing, and RBAC matrix.  
**Execution Target:** Localhost Docker (`http://localhost:5000`)  
**Browser Engine:** Real Google Chrome 155 (`channel="chrome"`) via Playwright  
**Lead Auditor:** AGENT 08 — Independent Auditor & Regression QA  

---

## 1. High-Priority Regression Targets & Objectives

1. **Re-verification of Open Defect `DEFECT-IT10-001`:**
   - Instructor course soft-delete endpoint `POST /instructor/courses/<id>/trash` raises HTTP 403 during response serialization because `_serialize_course(course)` runs `can_manage_course(actor, course)` which checks `course.deleted_at is None`.
2. **Re-verification of Open Defect `DEFECT-IT16-001`:**
   - Latency benchmark on `GET /instructor/courses` across 5 consecutive runs to verify persistent N+1 query overhead exceeding $500\text{ms}$ budget.
3. **Security Invariant Regression: Anti-Tamper Blackout Shield (Rule 10.8):**
   - Verification that DevTools keyboard triggers (`F12`, `Ctrl+Shift+I`) immediately deploy full-screen Blackout Shield overlay and revoke session.
4. **Content Security Regression: 50MB Non-Archive Attachment Policy (Rule 10.3):**
   - Verification that archive uploads (`.zip`, `.rar`) are strictly rejected with standardized Vietnamese explanation.
5. **Concurrency Invariant Regression: Single Active Editing Lease Fencing (Algorithm 07):**
   - Verification that lease takeover increments epoch and fences stale tab autosave writes with HTTP 409 Conflict.
6. **Authorization Matrix Regression: Two-Tier Broadcast RBAC:**
   - Verification that sub-admin category filtering rejects unauthorized broadcasts with HTTP 403 Forbidden.

---

## 2. Methodology & Evidence Contract

- Real browser automation in Google Chrome 155 via Playwright.
- Dual-persisted annotated screenshots (`PASS` / `DEFECT_CONFIRMED`) into `qa-audit/iterations/iteration-19/evidence/` and `qa-audit/screenshots/`.
- Quantitative metrics, response latencies, and error codes captured in `qa-audit/iterations/iteration-19/results.json`.
