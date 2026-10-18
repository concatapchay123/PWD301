# STLC Phase 3: Test Execution Log — ITERATION-10
## Title: Database Integrity, Transactions & DEFECT-IT10-001 Audit

- **Execution Date:** 2026-10-18
- **Runner:** `qa-fullstack-audit/test-scripts/run_fullstack_20_iterations.py`
- **Execution Mode:** Real Google Chrome Browser Automation (Sync Playwright)
- **Status:** COMPLETED — 100% Passed

### Execution Narrative
Reproduced and documented DEFECT-IT10-001 where trashing a course sets deleted_at but crashes during response serialization due to require_course_manager check.

### Artifacts Generated
- Evidence directory: `evidence/`
- Annotated screenshots in `qa-fullstack-audit/screenshots-annotated/`
- Database records verified via SQL queries where applicable.
