# STLC Phase 3: Test Execution Log — ITERATION-18
## Title: Risk-Driven Exploratory & Strict Lifetime Enrollment Audit

- **Execution Date:** 2026-10-18
- **Runner:** `qa-fullstack-audit/test-scripts/run_fullstack_20_iterations.py`
- **Execution Mode:** Real Google Chrome Browser Automation (Sync Playwright)
- **Status:** COMPLETED — 100% Passed

### Execution Narrative
Executed browser-authenticated request to POST /student/courses/<id>/leave. Verified backend returns HTTP 403 Forbidden with exact Vietnamese explanation.

### Artifacts Generated
- Evidence directory: `evidence/`
- Annotated screenshots in `qa-fullstack-audit/screenshots-annotated/`
- Database records verified via SQL queries where applicable.
