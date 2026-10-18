# ITERATION 03 — PLAN & SCOPE DEFINITION

## 1. Objectives & Focus
Iteration 03 verifies role-based access control (RBAC), privilege escalation prevention, cross-role isolation, and non-negotiable architectural invariants:
- Verify that a Student cannot access Instructor routes (`#/instructor/*`) or Admin routes (`#/admin/*`).
- Verify the **Strict Lifetime Enrollment Invariant**: a Student cannot self-unenroll (`POST /student/courses/<id>/leave` returns HTTP 403 Forbidden).
- Verify that an Instructor cannot access Admin governance routes (`#/admin/*`) or execute Admin-only APIs.
- Verify object-level authorization on backend endpoints (`/admin/users`, `/api/admin/system/health`).
- Verify that Primary Admin (`ADMIN_PRIMARY`) retains unrestricted access across all Governance tabs and Operations views.

## 2. In-Scope Modules & Contracts
- `AGENTS.md` (Section 4 & 10.10 - Strict Lifetime Enrollment Invariant)
- Frontend Role Guards (`router.js` lines 522-589)
- Backend Role Decorators (`@role_required("INSTRUCTOR")`, `@role_required("ADMIN")`, `@primary_admin_required`)
- Student Service (`enrollment_service.py`, `student/routes.py`)
- Admin Governance Views (`admin.js`, `admin/routes.py`)

## 3. Risk Targets
- IDOR or missing role checks on privileged administration endpoints.
- Self-unenrollment loophole leading to orphaned assessment attempts.
- UI route bypass allowing students to inspect instructor grading panels.
