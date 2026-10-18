# ITERATION 03 — EXECUTION RESULTS

**Execution Date:** 2026-10-18  
**Iteration Focus:** Authorization, Role-Based Access Control (RBAC), Sub-Role Isolation & Strict Lifetime Enrollment Invariant  
**Browser Engine:** Google Chrome 155.0.4283.60 (Playwright sync API)  
**Viewport:** 1366 x 768  
**Live Target:** `http://localhost:5000`  

---

## 1. Test Execution Summary

| Test Case ID | Test Case Name | Status | Evidence Artifact | Empirical Notes |
|---|---|---|---|---|
| **TC-IT03-001** | Student Restricted from Instructor Studio | **PASS** | `IT03_TC01_student_blocked_from_instructor.png` | Student attempting to navigate to `#/instructor/dashboard` safely redirected to `#/student/dashboard` |
| **TC-IT03-002** | Student Restricted from Admin Governance | **PASS** | `IT03_TC02_student_blocked_from_admin.png` | Student attempting to navigate to `#/admin/governance` safely redirected to `#/student/dashboard` |
| **TC-IT03-003** | Strict Lifetime Enrollment Invariant | **PASS** | `IT03_TC03_lifetime_enrollment_locked.png` | `POST /student/courses/<id>/leave` strictly returns HTTP 403 Forbidden with invariant notice |
| **TC-IT03-004** | Backend RBAC API Barrier for Student | **PASS** | `IT03_TC04_api_rbac_barrier.png` | Direct API call to `/admin/users` blocked with HTTP 403 Forbidden |
| **TC-IT03-005** | Instructor Restricted from Admin Governance | **PASS** | `IT03_TC05_instructor_blocked_from_admin.png` | Instructor attempting to navigate to `#/admin/governance` safely redirected to `#/instructor/dashboard` |
| **TC-IT03-006** | Primary Admin Governance Access | **PASS** | `IT03_TC06_primary_admin_operations.png` | Primary Admin successfully granted full access to `#/admin/operations` and governance tabs |

---

## 2. Invariant & Security Verification

### 2.1. Strict Lifetime Enrollment Policy (AGENTS.md Section 10.10)
- **Endpoint:** `POST /student/courses/<course_id>/leave`
- **Response Code:** `403 Forbidden`
- **Error Code:** `FORBIDDEN`
- **Localized Message:** `"Chức năng rời khóa học đã bị vô hiệu hóa. Khóa học được ghi danh sẽ gắn liền với tài khoản học viên trọn đời."`
- **Verification:** Verified that self-unenrollment is permanently locked. Enrollment records in database remain immutable and cannot be deleted or abandoned by students.

### 2.2. Role-Based Route Guarding (Frontend & Backend Alignment)
- SPA Router actively checks `currentUser.role` on route change. Unauthorized attempts to load higher-privilege routes immediately trigger safe redirection to the actor's authorized home without rendering sensitive DOM elements.
- Backend `@student_required`, `@instructor_required`, and `@admin_required` decorators independently enforce fail-closed barriers, returning HTTP 403 if session cookies lack required claims.

---

## 3. Evidence Gallery (Iteration 03)
1. `qa-audit/iterations/iteration-03/evidence/IT03_TC01_student_blocked_from_instructor.png`
2. `qa-audit/iterations/iteration-03/evidence/IT03_TC02_student_blocked_from_admin.png`
3. `qa-audit/iterations/iteration-03/evidence/IT03_TC03_lifetime_enrollment_locked.png`
4. `qa-audit/iterations/iteration-03/evidence/IT03_TC04_api_rbac_barrier.png`
5. `qa-audit/iterations/iteration-03/evidence/IT03_TC05_instructor_blocked_from_admin.png`
6. `qa-audit/iterations/iteration-03/evidence/IT03_TC06_primary_admin_operations.png`
