# PWD301 ROLE-BASED ACCESS CONTROL (RBAC) & PERMISSION MATRIX

## 1. System Roles Hierarchy & Definitions
- **ANONYMOUS (Public):** Unauthenticated guest; permitted only to view public routes (`#/auth`, `#/login`, `GET /auth/login`, public course discovery).
- **STUDENT:** Authenticated learner; access to enrolled courses, lesson reader, assessments, exam waiting room/attempt console, AI assistant, profile settings. Locked from instructor/admin areas and course unenrollment (`POST /student/courses/<id>/leave` -> 403).
- **INSTRUCTOR:** Authenticated course creator; manages owned courses, single-page studio, curriculum authoring, staging drafts, question banks, exam generation (manual, excel, moodle), assessment grading. Cannot edit courses owned by other instructors without admin reassignment.
- **ADMIN (Multi-Tier Governance):**
  - **ADMIN_PRIMARY (Root Admin):** Full system privileges across users, courses, applications, reassignments, security audits, backups, and global broadcast notifications.
  - **ADMIN_COURSE_REVIEW:** Dedicated sub-admin locked to Course Submission review and Staging Draft approval/rejection.
  - **ADMIN_INSTRUCTOR_REVIEW:** Dedicated sub-admin locked to Instructor Application verification.
  - **ADMIN_TEACHING_ASSIGNMENT:** Dedicated sub-admin locked to course ownership transfer and faculty workload reassignment.
  - **ADMIN_SYSTEM_MONITORING:** Dedicated sub-admin locked to telemetry, operations, backups, and SYSTEM broadcast notifications only.

---

## 2. Granular Route & Endpoint Access Matrix

| Route / Resource Endpoint | Anonymous | Student | Instructor | Sub-Admin (Review) | Primary Admin | Expected Status / Behavior |
|---|---|---|---|---|---|---|
| `#/auth`, `GET /auth/login` | ALLOW (200) | REDIRECT (Home) | REDIRECT (Home) | REDIRECT (Home) | REDIRECT (Home) | Public entry point |
| `POST /auth/login` | ALLOW (200) | ALLOW (200) | ALLOW (200) | ALLOW (200) | ALLOW (200) | Session authentication |
| `POST /auth/logout` | ALLOW (200) | ALLOW (200) | ALLOW (200) | ALLOW (200) | ALLOW (200) | Session revocation |
| `#/student/dashboard` | DENY (Redirect) | ALLOW (200) | AUTO-SWITCH | AUTO-SWITCH | AUTO-SWITCH | Student Learning View |
| `#/student/courses/:id` | DENY (Redirect) | ALLOW (Enrolled)| AUTO-SWITCH | AUTO-SWITCH | AUTO-SWITCH | Course Study Console |
| `POST /student/courses/:id/leave`| DENY (401) | DENY (403) | DENY (403) | DENY (403) | DENY (403) | **Lifetime Enrollment Invariant** |
| `#/instructor/dashboard` | DENY (Redirect) | DENY (Toast) | ALLOW (200) | AUTO-SWITCH | ALLOW (200) | Instructor Studio |
| `#/instructor/courses/:id/manage`| DENY (Redirect) | DENY (Toast) | ALLOW (Owned) | DENY (Toast)| ALLOW (Admin Override) | Curriculum & Staging Draft |
| `POST /instructor/courses/:id/submit`| DENY (401) | DENY (403) | ALLOW (Owned) | DENY (403)| DENY (400 - Instructor only) | Submit Staging Draft |
| `#/admin/governance` | DENY (Redirect) | DENY (Toast) | DENY (Toast) | ALLOW (Tab-locked) | ALLOW (All tabs) | Admin Governance |
| `#/admin/operations` | DENY (Redirect) | DENY (Toast) | DENY (Toast) | DENY (Toast)| ALLOW (200) | System Telemetry & Backups |
| `POST /admin/courses/:id/changeset/approve`| DENY (401) | DENY (403) | DENY (403) | ALLOW (Reviewer) | ALLOW (200) | Atomic Staging Approval |
| `GET /admin/health` | DENY (401) | DENY (403) | DENY (403) | DENY (403) | ALLOW (200) | Real psutil Telemetry |
| `GET /api/notifications` | DENY (401) | ALLOW (Owned)| ALLOW (Owned)| ALLOW (Owned)| ALLOW (Owned) | Notification Feed |
| `POST /api/notifications/broadcast` | DENY (401) | DENY (403) | DENY (403) | DENY (403)| ALLOW (200) | Two-Tier Broadcast RBAC |
