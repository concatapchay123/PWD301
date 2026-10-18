# ITERATION 06 — DEFECT REPORT

## 1. Discovered Defects & Observations in Iteration 06
- **Confirmed Critical/High Defects:** 0
- **Technical Observations & Architecture Notes:**
  - *Observation OBS-10 (Lazy Creation Guarantees):* Route resolution for `#instructor/courses/manage` strictly verifies the presence of query parameter `id`. When omitted, navigation falls back immediately to `#instructor/courses`, protecting the database from orphan drafts caused by inadvertent URL clicks or browser autocomplete.
  - *Observation OBS-11 (Draft Uniqueness Conflict Normalization):* When a duplicate course code is posted to `POST /instructor/courses`, the backend intercepts the integrity violation and returns a standard HTTP 409 conflict envelope (`code: CONFLICT`, `message: Dữ liệu bị trùng lặp hoặc xung đột trạng thái.`), preventing database connection resets and unhandled 500 errors.

## 2. Defect Totals
- **Open Defects:** 0
- **Reopened Defects:** 0
- **Closed Defects:** 0
