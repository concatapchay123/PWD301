# ITERATION 01 — TEST CASE INVENTORY

| Test ID | Test Category | Title & Purpose | Preconditions | Expected Outcome | Verification Method |
|---|---|---|---|---|---|
| **TC-IT01-001** | Environment & Reliability | Live server HTTP root & backend container health | Port 5000 reachable | HTTP 200 OK, Content-Type text/html | Python urllib HTTP GET |
| **TC-IT01-002** | Frontend & Branding | Landing Page (`#/auth`) & PPTQ Logo Render | Browser launched | Login card visible, PPTQ Logo (dark/light) rendered | Real Chrome Playwright |
| **TC-IT01-003** | E2E Workflow & Auth | Student Authentication (`student1@pwd301.local`) | Landing page open | Redirects to `#/student/dashboard`, topbar mounted | Real Chrome Playwright |
| **TC-IT01-004** | Frontend UI & Navigation | Course Catalog (`#/student/catalog`) & Search | Enrolled session active | Catalog cards loaded, search input functional | Real Chrome Playwright |
| **TC-IT01-005** | RBAC & Admin Governance | Admin Authentication (`admin@pwd301.local`) | Logged out from student | Redirects to `#/admin/governance`, tabs loaded | Real Chrome Playwright |
