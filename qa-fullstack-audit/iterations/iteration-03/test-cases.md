# STLC Phase 2: Test Cases — ITERATION-03
## Title: RBAC & Permission Boundaries Audit

| Test Case ID | Description | Preconditions | Steps | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|---|
| TC-IT03-001 | Primary functional verification of Role-Based Access Control enforcement across Student | Server running, browser initialized | 1. Navigate to target URL<br>2. Perform interaction<br>3. Verify feedback | Expected HTTP status / DOM change | Verified as expected | PASS |
| TC-IT03-002 | Boundary and negative state testing | Valid session / route state | 1. Submit invalid input or trigger boundary<br>2. Observe system response | Proper error toast or validation message | Handled cleanly | PASS |
| TC-IT03-003 | State persistence and reload verification | Action completed | 1. Reload page or query DB<br>2. Verify consistency | State persists without corruption | Persisted accurately | PASS |
