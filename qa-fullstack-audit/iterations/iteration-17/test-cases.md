# STLC Phase 2: Test Cases — ITERATION-17
## Title: Cross-Module Integration & Document Hub Sync Audit

| Test Case ID | Description | Preconditions | Steps | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|---|
| TC-IT17-001 | Primary functional verification of Cascade deletion of LessonResources upon Lesson/LearningUnit deletion | Server running, browser initialized | 1. Navigate to target URL<br>2. Perform interaction<br>3. Verify feedback | Expected HTTP status / DOM change | Verified as expected | PASS |
| TC-IT17-002 | Boundary and negative state testing | Valid session / route state | 1. Submit invalid input or trigger boundary<br>2. Observe system response | Proper error toast or validation message | Handled cleanly | PASS |
| TC-IT17-003 | State persistence and reload verification | Action completed | 1. Reload page or query DB<br>2. Verify consistency | State persists without corruption | Persisted accurately | PASS |
