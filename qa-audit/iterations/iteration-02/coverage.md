# ITERATION 02 — COVERAGE METRICS & TRACEABILITY

## 1. Metric Breakdown
- **Frontend Routes Covered:** 2 / 30 routes (Cumulative: 5 / 30, 16.7%)
  - `#/auth` (Login & Registration forms)
  - `#/student/dashboard` (Protected route guard validation)
- **Backend Endpoints Exercised:** 3 endpoints (Cumulative: 7 / 432, 1.6%)
  - `POST /auth/register` (Registration validation & conflict handling)
  - `POST /auth/login` (Positive, negative & injection payloads)
  - `POST /auth/logout` (Server session invalidation)
- **Roles Tested:**
  - ANONYMOUS
  - STUDENT
- **Executed Test Cases:** 6
- **Passed Test Cases:** 6 (100%)
- **Failed Test Cases:** 0
- **Blocked Test Cases:** 0
