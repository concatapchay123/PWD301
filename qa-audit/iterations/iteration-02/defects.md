# ITERATION 02 — DEFECT REPORT

## 1. Discovered Defects & Observations in Iteration 02
- **Confirmed Critical/High Defects:** 0
- **Technical Observations:**
  - *Observation OBS-02 (CSRF Session Rotation on Login):* Backend `POST /auth/login` rotates CSRF tokens upon login to prevent session fixation. Frontend `ApiClient` properly updates `_cachedCsrf` and the `csrf_token` cookie from response headers, enabling seamless subsequent `POST /auth/logout` and state-changing API operations.
  - *Observation OBS-03 (SPA Hash Routing Guard):* When an unauthenticated user force-navigates to a protected route (e.g. `#/student/dashboard`), the SPA router invokes `history.replaceState(null, '', '#/auth')` and asynchronously redirects the client to the login interface while ensuring no protected content is leaked into the DOM.

## 2. Defect Totals
- **Open Defects:** 0
- **Reopened Defects:** 0
- **Closed Defects:** 0
