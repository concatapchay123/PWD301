# ITERATION 01 TEST CASES

| Test ID | Requirement | Target Role | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| `TC-SMOKE-001` | REQ-AUTH-01 | `ANONYMOUS` | Landing page renders PPTQ logo, auth tabs, form inputs and floating AI pill | Page loaded with 200 OK, full PPTQ branding, inputs visible and active | **PASS** |
| `TC-SMOKE-002` | REQ-AUTH-01 | `STUDENT` | Authenticate successfully and display student dashboard with stats | Authenticated as student1@pwd301.local; dashboard rendered enrolled courses and progress | **PASS** |
| `TC-SMOKE-003` | REQ-CRS-01 | `INSTRUCTOR` | Render list of instructor managed courses with action buttons | Rendered course catalog studio; course management affordances operational | **PASS** |
| `TC-SMOKE-004` | REQ-OPS-01 | `ADMIN` | Admin dashboard displays system health and telemetry | Dashboard loaded; real hardware metrics displayed cleanly | **PASS** |
| `TC-SMOKE-005` | REQ-OPS-01 | `ADMIN` | Return authentic CPU/RAM measurements from psutil | Status 200; authentic hardware payload returned | **PASS** |
