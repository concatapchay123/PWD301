# ITERATION 03 TEST CASES

| Test ID | Requirement | Target Role | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| `TC-RBAC-001` | REQ-RBAC-01 | `STUDENT` | Prevent access, redirect to authorized route or display 403 Forbidden | Access blocked; student redirected to safe student dashboard | **PASS** |
| `TC-RBAC-002` | REQ-RBAC-01 | `STUDENT` | Prevent access and redirect to safe route | Access blocked; admin console hidden from student | **PASS** |
| `TC-RBAC-003` | REQ-RBAC-01 | `INSTRUCTOR` | Prevent access and deny route resolution | Access blocked; instructor confined to instructor studio | **PASS** |
| `TC-RBAC-004` | REQ-RBAC-01 | `INSTRUCTOR` | Return 403 Forbidden or 404 Not Found | Status 404; unauthorized mutation denied | **PASS** |
| `TC-RBAC-005` | REQ-RBAC-01 | `ANONYMOUS` | Redirect to #/auth with return URL | Redirected cleanly to #/auth login form | **PASS** |
| `TC-RBAC-006` | REQ-RBAC-01 | `ALL ROLES` | Strict RBAC matrix enforced with zero unauthorized bypasses | All 449 endpoints protected by permission decorators | **PASS** |
