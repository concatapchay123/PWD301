# ITERATION 02 — EXECUTION RESULTS

**Execution Date:** 2026-10-18  
**Iteration Focus:** Authentication, Registration, Password Policy & Session Lifecycle  
**Browser Engine:** Google Chrome 155.0.4283.60 (Playwright sync API)  
**Viewport:** 1366 x 768  
**Live Target:** `http://localhost:5000`  

---

## 1. Test Execution Summary

| Test Case ID | Test Case Name | Status | Evidence Artifact | Empirical Notes |
|---|---|---|---|---|
| **TC-IT02-001** | New Student Registration Flow | **PASS** | `IT02_TC01_registration_flow.png` | Successfully registered random student account via UI form |
| **TC-IT02-002** | Duplicate Registration Email Conflict | **PASS** | `IT02_TC02_duplicate_email_error.png` | Duplicate email rejected with 409 Conflict |
| **TC-IT02-003** | Password Policy Enforcement (< 8 chars) | **PASS** | `IT02_TC03_weak_password_error.png` | Weak 5-character password rejected by policy checklist |
| **TC-IT02-004** | Authentication Rejection on Wrong Password | **PASS** | `IT02_TC04_wrong_password_alert.png` | HTTP 401 Unauthorized with normalized Vietnamese alert |
| **TC-IT02-005** | SQL Injection Parameterized Defense | **PASS** | `IT02_TC05_sqli_defense_probe.png` | Payload `' OR '1'='1' --` rejected; no 500 error, zero bypass |
| **TC-IT02-006** | Session Revocation & Protected Guard | **PASS** | `IT02_TC06_session_revocation_guard.png` | UI logout revokes session; direct navigation to dashboard redirected to `#/auth` |

---

## 2. Evidence Gallery (Iteration 02)
1. `qa-audit/iterations/iteration-02/evidence/IT02_TC01_registration_flow.png`
2. `qa-audit/iterations/iteration-02/evidence/IT02_TC02_duplicate_email_error.png`
3. `qa-audit/iterations/iteration-02/evidence/IT02_TC03_weak_password_error.png`
4. `qa-audit/iterations/iteration-02/evidence/IT02_TC04_wrong_password_alert.png`
5. `qa-audit/iterations/iteration-02/evidence/IT02_TC05_sqli_defense_probe.png`
6. `qa-audit/iterations/iteration-02/evidence/IT02_TC06_session_revocation_guard.png`
