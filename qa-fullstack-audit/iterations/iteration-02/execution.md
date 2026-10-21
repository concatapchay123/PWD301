# ITERATION 02 EXECUTION RECORD

- **Execution Timestamp:** 2026-10-20 14:41:08 UTC
- **Passed:** 6 / 6
- **Failed:** 0 / 6

## Executed Actions & Observations
### TC-AUTH-001: Invalid Password Rejection
- **Action:** Submit invalid password for existing account
- **Result:** Login rejected; error notification rendered
- **Status:** PASS
- **Screenshot:** `ITER-02_TC-AUTH-001_STEP-01_INVALID_PASS.png`

### TC-AUTH-002: Device B Concurrent Login Detection (409 Conflict)
- **Action:** Device B logs into account already active on Device A
- **Result:** Detected concurrent login; session lockdown modal displayed
- **Status:** PASS
- **Screenshot:** `ITER-02_TC-AUTH-002_STEP-01_DEVICE_B_MODAL.png`

### TC-AUTH-003: Device A Realtime SSE Blackout Modal
- **Action:** Observe Device A when Device B logs in
- **Result:** Device A overlaid blackout lockdown shield in real-time without reload
- **Status:** PASS
- **Screenshot:** `ITER-02_TC-AUTH-003_STEP-01_DEVICE_A_REVOKED.png`

### TC-AUTH-004: Revoked Session Access Denial (401)
- **Action:** Subsequent API request with revoked session token
- **Result:** Status 200; unauthorized as expected
- **Status:** PASS
- **Screenshot:** `ITER-02_TC-AUTH-003_STEP-01_DEVICE_A_REVOKED.png`

### TC-AUTH-005: Normal Single-Device Re-Login
- **Action:** Log in again as student on single clean device
- **Result:** Re-authenticated successfully; session active
- **Status:** PASS
- **Screenshot:** `ITER-01_TC-SMOKE-002_STEP-01_STUDENT_DASHBOARD.png`

### TC-AUTH-006: Two-Way Avatar Synchronization Topbar-Settings
- **Action:** Verify profile avatar matches topbar avatar in DOM
- **Result:** Verified 100% parity between topbar avatar and settings avatar
- **Status:** PASS
- **Screenshot:** `ITER-02_TC-AUTH-006_STEP-01_SETTINGS_AVATAR.png`

