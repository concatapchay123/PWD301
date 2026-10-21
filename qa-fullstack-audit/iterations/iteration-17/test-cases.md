# ITERATION 17 TEST CASES

| Test ID | Requirement | Target Role | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| `TC-CASC-001` | REQ-CRS-03 | `STUDENT` | Core workflow executes without exception | Workflow executed smoothly; 200 OK responses | **PASS** |
| `TC-CASC-002` | REQ-CRS-03 | `STUDENT` | Edge inputs conform to business constraints | Boundary check satisfied; validation confirmed | **PASS** |
| `TC-CASC-003` | REQ-CRS-03 | `STUDENT` | Data updates persist reliably to MSSQL | State transition persisted and verified across reloads | **PASS** |
| `TC-CASC-004` | REQ-CRS-03 | `STUDENT` | System handles exceptions with structured envelope | Graceful recovery; no unhandled server crash | **PASS** |
| `TC-CASC-005` | REQ-CRS-03 | `STUDENT` | No data leakage or permission bypass | Zero authorization leaks detected; access contained | **PASS** |
| `TC-CASC-006` | REQ-CRS-03 | `STUDENT` | Subsystems remain synchronized | Cohesion confirmed across API, UI, and Database | **PASS** |
