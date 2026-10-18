# ITERATION 02 — TEST CASE INVENTORY

| Test ID | Category | Title & Purpose | Input Data | Expected Result | Verification |
|---|---|---|---|---|---|
| **TC-IT02-001** | Functional / Auth | New student account registration | Random valid email, Name, Pass >= 8 | Registered, redirected or logged in | Real Chrome Playwright |
| **TC-IT02-002** | Boundary / Negative | Duplicate email registration rejection | Same email as TC01 | Rejection alert (409 Conflict), Vietnamese error | Real Chrome Playwright |
| **TC-IT02-003** | Security / Policy | Password policy enforcement (< 8 chars) | Password "short" (5 chars) | Client/Server validation blocks submission | Real Chrome Playwright |
| **TC-IT02-004** | Security / Auth | Negative login with wrong password | `student1@pwd301.local` / wrong pass | HTTP 401 Unauthorized, "Email hoặc mật khẩu không chính xác" | Real Chrome Playwright |
| **TC-IT02-005** | Security / Injection | SQL Injection authentication bypass probe | Email: `admin@pwd301.local' OR '1'='1' --` | Denied, no 500 error, no auth bypass | Real Chrome Playwright |
| **TC-IT02-006** | Security / Session | Session revocation via logout | Student logout -> direct `#/student/dashboard` | Session cookie cleared, route guard blocks to `#/auth` | Real Chrome Playwright |
