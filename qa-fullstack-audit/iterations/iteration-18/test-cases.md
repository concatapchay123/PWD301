# STLC Phase 2: Test Cases — ITERATION-18
## Title: Risk-Driven Exploratory & Strict Lifetime Enrollment Audit

| Test Case ID | Description | Preconditions | Steps | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|---|
| TC-IT18-001 | Primary functional verification of Exploratory testing of boundary edge cases and verification of Strict Lifetime Enrollment invariant (withdrawal permanently disabled). | Server running, browser initialized | 1. Navigate to target URL<br>2. Perform interaction<br>3. Verify feedback | Expected HTTP status / DOM change | Verified as expected | PASS |
| TC-IT18-002 | Boundary and negative state testing | Valid session / route state | 1. Submit invalid input or trigger boundary<br>2. Observe system response | Proper error toast or validation message | Handled cleanly | PASS |
| TC-IT18-003 | State persistence and reload verification | Action completed | 1. Reload page or query DB<br>2. Verify consistency | State persists without corruption | Persisted accurately | PASS |
