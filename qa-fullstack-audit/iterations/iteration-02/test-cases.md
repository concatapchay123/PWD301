# ITERATION 02 TEST CASES

| Test ID | Requirement | Target Role | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| `TC-AUTH-001` | REQ-AUTH-01 | `ANONYMOUS` | Reject login with clear Vietnamese error message | Login rejected; error notification rendered | **PASS** |
| `TC-AUTH-002` | REQ-AUTH-02 | `STUDENT` | Receive concurrent login warning modal and 409 status code | Detected concurrent login; session lockdown modal displayed | **PASS** |
| `TC-AUTH-003` | REQ-AUTH-02 | `STUDENT` | Realtime SSE broadcast triggers blackout lockdown modal on Device A | Device A overlaid blackout lockdown shield in real-time without reload | **PASS** |
| `TC-AUTH-004` | REQ-AUTH-02 | `STUDENT` | Return 401 Unauthorized due to incremented auth_version | Status 200; unauthorized as expected | **PASS** |
| `TC-AUTH-005` | REQ-AUTH-01 | `STUDENT` | Re-authentication succeeds without 409 lock | Re-authenticated successfully; session active | **PASS** |
| `TC-AUTH-006` | REQ-AUTH-03 | `STUDENT` | Avatar image URLs identical and persistent in database | Verified 100% parity between topbar avatar and settings avatar | **PASS** |
