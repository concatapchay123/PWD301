# ITERATION 03 — TEST CASE INVENTORY

| Test ID | Category | Title & Purpose | Role & Route | Expected Outcome | Verification |
|---|---|---|---|---|---|
| **TC-IT03-001** | RBAC / Boundary | Student blocked from Instructor Studio | Student -> `#/instructor/dashboard` | Warning toast displayed, redirected to `#/student/dashboard` | Real Chrome Playwright |
| **TC-IT03-002** | RBAC / Boundary | Student blocked from Admin Governance | Student -> `#/admin/governance` | Warning toast displayed, redirected to `#/student/dashboard` | Real Chrome Playwright |
| **TC-IT03-003** | Invariant / Policy | Strict Lifetime Enrollment Invariant | Student -> `POST /student/courses/<id>/leave` | HTTP 403 Forbidden, leave locked permanently | Real Chrome API Call |
| **TC-IT03-004** | API Security / RBAC| Backend API barrier for Student role | Student -> `/admin/users`, `/api/admin/system/health` | HTTP 403 Forbidden, access denied | Real Chrome API Call |
| **TC-IT03-005** | RBAC / Boundary | Instructor blocked from Admin Governance | Instructor -> `#/admin/governance` | Warning toast displayed, redirected to `#/instructor/dashboard` | Real Chrome Playwright |
| **TC-IT03-006** | RBAC / Governance | Primary Admin Multi-Tab Access | Admin -> `#/admin/governance`, `#/admin/operations` | Full unrestricted access to all tabs | Real Chrome Playwright |
