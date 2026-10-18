# STLC Phase 1: Test Plan — ITERATION-03
## Title: RBAC & Permission Boundaries Audit

### 1. Objectives & Scope
- **Iteration ID:** ITERATION-03 (Iteration #3)
- **Focus Area:** Role-Based Access Control enforcement across Student, Instructor, and Admin roles. Verification of horizontal and vertical privilege escalation boundaries (BOLA/IDOR).
- **Environment:** http://127.0.0.1:5000 (Pure Headless + Single Page Application)
- **Browser Automation:** Real Google Chrome (Playwright sync API)

### 2. Entrance & Exit Criteria
- **Entrance Criteria:** Target server operational, MSSQL 2022 database responsive, test accounts provisioned.
- **Exit Criteria:** All defined test cases executed on real browser, visual screenshots captured and annotated, network and console logs inspected, database verified.

### 3. Test Tools & Infrastructure
- Browser: Google Chrome v155.0.0 via Playwright
- Image Processing: Pillow (PIL) for test execution banner annotation
- Backend Engine: Python 3.12, Flask 3.0, Gunicorn, MSSQL Express 2022
