# ITERATION 03 — DEFECT REPORT

## 1. Discovered Defects & Observations in Iteration 03
- **Confirmed Critical/High Defects:** 0
- **Technical Observations & False-Positive Triage:**
  - *Observation OBS-04 (Lifetime Enrollment Endpoint Architecture):* The canonical self-unenrollment locking endpoint is implemented at `POST /student/courses/<course_id>/leave` under `student_bp`, strictly raising `ForbiddenError` with the exact localized message mandated by `AGENTS.md`. Tests must target the blueprint URL rather than legacy/unregistered endpoints to prevent false-negative 404 test harness errors.
  - *Observation OBS-05 (Cross-Role Redirection Integrity):* When cross-role navigation is attempted directly via hash changes (`#/instructor/dashboard` or `#/admin/governance` by a Student; `#/admin/governance` by an Instructor), the client router synchronously checks the cached `currentUser` role and updates the address bar via `window.location.hash` to the authorized home view before any view template lifecycle executes.

## 2. Defect Totals
- **Open Defects:** 0
- **Reopened Defects:** 0
- **Closed Defects:** 0
