# ITERATION 05 — DEFECT REPORT

## 1. Discovered Defects & Observations in Iteration 05
- **Confirmed Critical/High Defects:** 0
- **Technical Observations & Architecture Notes:**
  - *Observation OBS-08 (Dual-Layer Length Enforcement):* Display name input has a client-side restriction of `maxlength="100"` while the backend schema allows up to 150 characters (`Tên hiển thị phải từ 2 đến 150 ký tự.`). This ensures that normal UI input never triggers backend boundary rejection, while direct API calls exceeding 150 chars are safely rejected with HTTP 400 without crashing the database or application layer.
  - *Observation OBS-09 (UI-Level Double-Submit Guard):* Button locking (`btn.disabled = true`) is synchronously executed prior to the asynchronous API request promise dispatch, effectively serializing mutations and eliminating rapid click double-submit race conditions.

## 2. Defect Totals
- **Open Defects:** 0
- **Reopened Defects:** 0
- **Closed Defects:** 0
