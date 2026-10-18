# STLC Phase 2: Test Cases — ITERATION-12
## Title: Assessment Engine, Boundary Values & Anti-Leak Audit

| Test Case ID | Description | Preconditions | Steps | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|---|
| TC-IT12-001 | Primary functional verification of Anti-leak exam security (no answers in payload or DOM during active attempt) | Server running, browser initialized | 1. Navigate to target URL<br>2. Perform interaction<br>3. Verify feedback | Expected HTTP status / DOM change | Verified as expected | PASS |
| TC-IT12-002 | Boundary and negative state testing | Valid session / route state | 1. Submit invalid input or trigger boundary<br>2. Observe system response | Proper error toast or validation message | Handled cleanly | PASS |
| TC-IT12-003 | State persistence and reload verification | Action completed | 1. Reload page or query DB<br>2. Verify consistency | State persists without corruption | Persisted accurately | PASS |
