# ITERATION 07 TEST PLAN

**Iteration Focus:** Backend API Contracts, Standard JSON Envelopes, HTTP Status Codes & Error Localization  
**Responsible Agents:** AGENT 03 (Backend & API QA), AGENT 05 (Security & RBAC QA), AGENT 08 (Independent Auditor)  
**Target Environment:** Local Live Stack (`http://localhost:5000`)  
**Browser Engine:** Google Chrome 155 via Playwright & Direct HTTP Contract Inspector  
**Viewport:** 1366 x 768  

---

## 1. Objectives
1. Verify the Pure Headless Backend Contract: All blueprints (`auth`, `student`, `instructor`, `admin`, `api_*`) serve standardized machine-readable JSON envelopes.
2. Verify Envelope Schema Structure:
   - Success: `{"success": true, "data": ..., "error": null}`
   - Error: `{"success": false, "data": null, "error": {"code": "...", "message": "...", "correlation_id": "...", "field_errors": {...}}}`
3. Verify HTTP Status Codes: 200, 201, 400, 401, 403, 404, 409.
4. Verify Error Message Localization: Vietnamese user-facing error strings without leaking internal server stack traces.
5. Verify Correlation ID presence in error envelopes for audit traceability.
6. Verify Pure Headless Invariant: API endpoints never return HTML or Jinja templates.

---

## 2. Test Cases Overview
- `TC-IT07-001`: Standard JSON Success Envelope Verification
- `TC-IT07-002`: Standard JSON Error Envelope Structure & Correlation ID
- `TC-IT07-003`: HTTP 400 Bad Request & Field Errors Schema
- `TC-IT07-004`: HTTP 401 Unauthorized Authentication Boundary
- `TC-IT07-005`: HTTP 403 Forbidden on Cross-Role Access
- `TC-IT07-006`: Pure Headless Invariant (Application/JSON Content-Type, Zero HTML Leakage)
