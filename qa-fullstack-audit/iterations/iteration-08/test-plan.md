# STLC Phase 1: Test Plan — ITERATION-08
## Title: Course Lifecycle, Staging Drafts & Approval Audit

### 1. Objectives & Scope
- **Iteration ID:** ITERATION-08 (Iteration #8)
- **Focus Area:** Course draft auto-saving, CourseChangeRequest changeset aggregation, single atomic admin review, and transition to published status.
- **Environment:** http://127.0.0.1:5000 (Pure Headless + Single Page Application)
- **Browser Automation:** Real Google Chrome (Playwright sync API)

### 2. Entrance & Exit Criteria
- **Entrance Criteria:** Target server operational, MSSQL 2022 database responsive, test accounts provisioned.
- **Exit Criteria:** All defined test cases executed on real browser, visual screenshots captured and annotated, network and console logs inspected, database verified.

### 3. Test Tools & Infrastructure
- Browser: Google Chrome v155.0.0 via Playwright
- Image Processing: Pillow (PIL) for test execution banner annotation
- Backend Engine: Python 3.12, Flask 3.0, Gunicorn, MSSQL Express 2022
