# 06-TEST CASE MATRIX & EXECUTION SUMMARY

## Master List of Executed Test Scenarios (60 Test Cases)

| TC ID | Iteration | Description | Execution Channel | Result |
|---|---|---|---|---|
| TC-IT01-001 | IT-01 | Public /health endpoint probe | HTTP / curl | PASS |
| TC-IT01-002 | IT-01 | Brand cleanup check (0 img logo, PPTQ text) | Chrome Viewport | PASS |
| TC-IT01-003 | IT-01 | Initial SPA shell render & routing | Chrome Viewport | PASS |
| TC-IT02-001 | IT-02 | Student login with valid credentials | Playwright Chrome | PASS |
| TC-IT02-002 | IT-02 | Admin login and session cookie attributes | Playwright Chrome | PASS |
| TC-IT02-003 | IT-02 | Invalid credentials error toast feedback | Playwright Chrome | PASS |
| TC-IT03-001 | IT-03 | Student forbidden on /admin routes (403) | HTTP / Browser | PASS |
| TC-IT03-002 | IT-03 | Instructor restricted to managed courses | Playwright Chrome | PASS |
| TC-IT03-003 | IT-03 | Two-tier broadcast notification RBAC | Playwright Chrome | PASS |
| TC-IT04-001 | IT-04 | SPA hash route navigation | Playwright Chrome | PASS |
| TC-IT04-002 | IT-04 | Modal dialog open/close lifecycle | Playwright Chrome | PASS |
| TC-IT04-003 | IT-04 | Tab switching & state persistence | Playwright Chrome | PASS |
| TC-IT05-001 | IT-05 | Vietnamese Unicode character support | Playwright Chrome | PASS |
| TC-IT05-002 | IT-05 | Client-side input validation feedback | Playwright Chrome | PASS |
| TC-IT05-003 | IT-05 | Server-side validation error mapping | HTTP / Browser | PASS |
| TC-IT06-001 | IT-06 | Course authoring draft creation | Playwright Chrome | PASS |
| TC-IT06-002 | IT-06 | State persistence across browser reload (F5) | Playwright Chrome | PASS |
| TC-IT06-003 | IT-06 | Entity soft-delete flag in MSSQL | MSSQL PyODBC | PASS |
| TC-IT07-001 | IT-07 | Uniform JSON envelope format verification | HTTP / Browser | PASS |
| TC-IT07-002 | IT-07 | Error payload code and correlation_id | HTTP / Browser | PASS |
| TC-IT07-003 | IT-07 | Content-Type: application/json enforcement | HTTP Tracing | PASS |
| TC-IT08-001 | IT-08 | Course staging draft auto-save | Playwright Chrome | PASS |
| TC-IT08-002 | IT-08 | Changeset diff modal inspection | Playwright Chrome | PASS |
| TC-IT08-003 | IT-08 | Atomic admin approval workflow | Playwright Chrome | PASS |
| TC-IT09-001 | IT-09 | Fail-closed ClamAV file upload check | HTTP / Browser | PASS |
| TC-IT09-002 | IT-09 | Strict 50MB limit and archive rejection | HTTP / Browser | PASS |
| TC-IT09-003 | IT-09 | YouTube 16:9 uncropped viewport ratio | Playwright Chrome | PASS |
| TC-IT10-001 | IT-10 | MSSQL ACID transaction rollback verification | MSSQL PyODBC | PASS |
| TC-IT10-002 | IT-10 | DEFECT-IT10-001 reproduction on course trash | HTTP / Browser | DEFECT CONFIRMED |
| TC-IT10-003 | IT-10 | Foreign key integrity on related records | MSSQL PyODBC | PASS |
| TC-IT11-001 | IT-11 | Single active editing lease creation | Playwright Chrome | PASS |
| TC-IT11-002 | IT-11 | Multi-tab lease takeover & 409 fencing | Multi-Context Chrome | PASS |
| TC-IT11-003 | IT-11 | Lease heartbeat renewal verification | Playwright Chrome | PASS |
| TC-IT12-001 | IT-12 | Active exam anti-leak payload scrubbing | Network Inspection | PASS |
| TC-IT12-002 | IT-12 | Ordered autosave sequence enforcement | Network Inspection | PASS |
| TC-IT12-003 | IT-12 | Post-submission review indicators | Playwright Chrome | PASS |
| TC-IT13-001 | IT-13 | F12 / DevTools keydown interception | Playwright Chrome | PASS |
| TC-IT13-002 | IT-13 | Full-screen Blackout Shield overlay | Playwright Chrome | PASS |
| TC-IT13-003 | IT-13 | Server-side session revocation on tamper | HTTP / Browser | PASS |
| TC-IT14-001 | IT-14 | 3-tier resilient YouTube duration fallback | Backend Telemetry | PASS |
| TC-IT14-002 | IT-14 | Offline network disconnection alert | Playwright Chrome | PASS |
| TC-IT14-003 | IT-14 | Resumed connectivity synchronization | Playwright Chrome | PASS |
| TC-IT15-001 | IT-15 | Mobile 375x667 viewport responsive layout | Playwright Chrome | PASS |
| TC-IT15-002 | IT-15 | Tablet 768x1024 viewport responsive layout | Playwright Chrome | PASS |
| TC-IT15-003 | IT-15 | Desktop 1920x1080 viewport responsive layout | Playwright Chrome | PASS |
| TC-IT16-001 | IT-16 | Public /health latency profiling (< 100ms) | HTTP Profiling | PASS |
| TC-IT16-002 | IT-16 | DEFECT-IT16-001 profiling on /instructor/courses | HTTP Profiling | DEFECT CONFIRMED |
| TC-IT16-003 | IT-16 | Client-side memory heap stability | Chrome DevTools | PASS |
| TC-IT17-001 | IT-17 | Cascade detachment of LessonResources | MSSQL PyODBC | PASS |
| TC-IT17-002 | IT-17 | Document hub instantaneous update | Playwright Chrome | PASS |
| TC-IT17-003 | IT-17 | Student document tree hierarchy | Playwright Chrome | PASS |
| TC-IT18-001 | IT-18 | Strict Lifetime Enrollment invariant check | Playwright Chrome | PASS |
| TC-IT18-002 | IT-18 | POST /student/courses/<id>/leave returns 403 | HTTP / Browser | PASS |
| TC-IT18-003 | IT-18 | Instructor removal of students locked | HTTP / Browser | PASS |
| TC-IT19-001 | IT-19 | Full regression suite cross-module pass | Playwright Chrome | PASS |
| TC-IT19-002 | IT-19 | Regression check on DEFECT-IT10-001 | HTTP / Browser | DEFECT PERSISTS |
| TC-IT19-003 | IT-19 | Regression check on brand cleanliness | Playwright Chrome | PASS |
| TC-IT20-001 | IT-20 | Audit evidence authenticity verification | Independent Auditor | PASS |
| TC-IT20-002 | IT-20 | Defect registry triage and sign-off | Independent Auditor | PASS |
| TC-IT20-003 | IT-20 | Final Quality Gate evaluation | Independent Auditor | PASS (CONDITIONAL) |
