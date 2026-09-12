# TASK-030 — Student Web Portal Modernization, Functional Minimalism UI Integration & SQL Server Compatibility

**Status:** DONE  
**Assignee:** Principal Software Architect & Lead Fullstack Engineer  
**Started Date:** 2026-09-12  
**Completed Date:** 2026-09-12  

---

## Goal
Resolve the student dashboard 500 Internal Server Error, modernize the student and application shell user interface using the functional minimalism reference from `frontend-preview/`, and wire all interactive controls (navigation, notifications, lesson reader, attempt interface, AI assistant, course enrollment) to backend endpoints with server-authoritative Flask session authentication and CSRF protection.

---

## Source-of-Truth Documents
- `AGENTS.md` (Operational contract, Fail-closed invariants, Zero Internal PK Leakage, session auth)
- `frontend-preview/` (Canonical UI layout, typography, components, and styling)
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/01_BUSINESS_RULE_CATALOG.md` (BR-020–BR-024, BR-028–BR-035, BR-040–BR-049)
- `docs/database/PWD301_DATABASE_ARCHITECTURE/` (SQL Server reference dialect, T-SQL ordering compatibility)

---

## Root Cause Analysis
1. **MSSQL T-SQL Syntax Incompatibility in Analytics Queries**:
   - `analytics_service.get_student_learning_overview` utilized `.nullslast()` on `Assessment.close_at.asc()` and `AssessmentAttempt.graded_at.desc()`.
   - SQLite and Postgres support `NULLS LAST`, but Microsoft SQL Server (T-SQL) throws `42000 [Microsoft][ODBC Driver 18 for SQL Server][SQL Server]Incorrect syntax near 'NULLS' (102)`.
   - When a student or administrator accessed `/student/dashboard` against SQL Server, the unhandled SQL syntax error triggered a 500 Internal Server Error with a Correlation ID.
2. **Jinja BuildError on Role Sidebar / Navigation in `base.html`**:
   - Incomplete route name guessing for Instructor and Admin endpoints (`instructor.question_bank_page`, `admin.users_page`) crashed rendering when users with multiple roles accessed the page.
3. **Dead Links and Missing Defensive UX in Course Catalog & Detail**:
   - Course cards lacked wired routes to course details with prerequisite inspection.
   - Enrollment form POST did not catch domain errors gracefully for HTML clients.
4. **Hardcoded First Lesson Progress Resumption**:
   - Resumption always sent students to Lesson 1 instead of the first uncompleted lesson.

---

## Key Changes
1. **SQL Server Compatible Ordering**:
   - Replaced `.nullslast()` in `src/pwd301/services/analytics_service.py` with cross-dialect `case((column.is_(None), 1), else_=0), column.asc()/desc()`.
2. **Functional Minimalism UI Shell & Templates**:
   - Overhauled `src/pwd301/templates/base.html` with role-aware desktop sidebar, mobile offcanvas drawer, theme switcher, notifications popover, demo role switcher, and floating AI assistant launcher.
   - Designed and integrated `src/pwd301/templates/student/dashboard.html` with KPI metric counters, active courses, upcoming assessment deadlines, and AI study cards.
   - Added `src/pwd301/templates/student/my_learning.html`, `course_detail.html`, `assessments.html`, `assessment_detail.html`, `result.html`, `ai_assistant.html`.
   - Created client controllers `src/pwd301/static/js/app_shell.js` and `src/pwd301/static/js/components.js`.
3. **Defensive Enrollment & Smart Resumption**:
   - In `student_course_detail`: Computed prerequisite badges and capacity status; disabled enroll button when prerequisites are unmet or class is full.
   - In `student_enroll_course`: Added `try...except` handling for HTML form posts to flash friendly alerts and redirect safely.
   - In `course_progress`: Resumes at the first uncompleted lesson based on `LessonProgress.completed_at`.
4. **Docker Production Container Update**:
   - Rebuilt `pwd301_web` container with latest wheel dependencies, templates, and static assets.

---

## Verification Record
- **Pytest Full Suite**: 829 passed, 0 failed across unit, API, and E2E suites.
- **Student Portal Integration Tests (`tests/api/test_student_portal_ui.py`)**: 14 passed in 11.38s.
- **Ruff Linter**: `ruff check src tests` passed with 0 errors.
- **Live Container Verification**: Tested live container on `http://localhost:5000`:
  - `GET /`: HTTP 200 (Course catalog rendered with Functional Minimalism cards).
  - `POST /auth/login` (Student & Admin): HTTP 302 -> `/student/dashboard`.
  - `GET /student/dashboard`: HTTP 200 (Clean, 0 errors, no 500 crash).
  - `GET /student/courses/<course_id>`: HTTP 200.
  - `GET /student/assessments`: HTTP 200.
  - `GET /student/ai-assistant`: HTTP 200.

---

# TASK-031 — Web Role Persistence, Multi-Role Portal Navigation & Safe Role Switching

**Status:** DONE  
**Assignee:** Principal Software Architect & Lead Fullstack Engineer  
**Started Date:** 2026-09-12  
**Completed Date:** 2026-09-12  

## Goal
Resolve the critical issue where any user logging in with an elevated role (Admin, Instructor) was downgraded and permanently locked into the Student role (`active_role = 'STUDENT'`), with sidebars rendering only student navigation links and no way to operate their administrative or teaching functions.

## Root Cause Analysis
1. **Unordered Relationship Extraction in Auth Login**:
   - In `src/pwd301/blueprints/auth/routes.py`, login set `session["active_role"] = user.roles[0].code`.
   - Because canonical roles in the database are seeded as STUDENT (ID 1), INSTRUCTOR (ID 2), and ADMIN (ID 3), `user.roles[0]` was invariably `Role(code='STUDENT')` for all users (including Admins and Instructors who cumulative-inherit Student).
   - As a result, every login immediately forced `session["active_role"] = "STUDENT"`.
2. **Hardcoded Fallback in Base Template**:
   - `src/pwd301/templates/base.html` evaluated `active_r = session.get('active_role', '')` with a fallback `or (current_user.is_authenticated and not active_r)`, hardcoding `STUDENT` if missing or defaulting.
   - The topbar role displayed `STUDENT`, and the desktop and mobile sidebars rendered the Student navigation links only.
3. **Missing Role Synchronization and Switching Mechanisms**:
   - When an Admin navigated to `/admin/...` or an Instructor to `/instructor/...`, `active_role` in session remained `STUDENT`, causing the sidebar to remain stuck in student view.
   - The platform lacked a dedicated CSRF-protected `POST /auth/switch-role` endpoint to enable authorized multi-role users to switch between their legitimate perspectives.

## Key Changes
1. **Canonical `primary_role` Resolution on User Model**:
   - Added `primary_role` property to `User` and `AnonymousUser` (`ADMIN` > `INSTRUCTOR` > `STUDENT`), strictly observing AUTH-002 cumulative hierarchy.
2. **Login Role Resolution**:
   - In `auth/routes.py`, login sets `session["active_role"] = user.primary_role` and redirects to the appropriate role dashboard.
3. **Portal Auto-Synchronization in `before_request`**:
   - In `src/pwd301/__init__.py`, `before_request` dynamically synchronizes `session["active_role"]` to `ADMIN` when an admin accesses `/admin/...`, and to `INSTRUCTOR` when an instructor accesses `/instructor/...`.
4. **Safe, CSRF-Protected Role Switch Endpoint & Authorization Hierarchy**:
   - Implemented `POST /auth/switch-role` with strict role entitlement validation:
     - Admin: allowed targets = `ADMIN`, `INSTRUCTOR`, `STUDENT`.
     - Instructor: allowed targets = `INSTRUCTOR`, `STUDENT`.
     - Student: cannot switch roles (strictly rejected with HTTP 403 Forbidden).
5. **Modernized Topbar User Dropdown in `base.html`**:
   - Added `VAI TRÒ (CHUYỂN ĐỔI)` dropdown section:
     - Admin sees options: Quản trị viên (Admin), Giảng viên (Instructor), Học viên (Student).
     - Instructor sees options: Giảng viên (Instructor), Học viên (Student).
     - Student sees NO role switcher section.
   - Updated topbar role title and badge to display `QUẢN TRỊ VIÊN (ADMIN)`, `GIẢNG VIÊN (INSTRUCTOR)`, `HỌC VIÊN (STUDENT)`.
6. **Docker Environment Live Reflection**:
   - Updated `docker-compose.yml` to mount `./src:/app/src` into `pwd301_web` container.
   - Rebuilt `pwd301-web:latest` image and recreated container.

## Verification Record
- **Full Pytest Suite**: 834 passed, 0 failed across unit, API, and E2E suites.
- **Web UI & Role Switching Tests (`tests/api/test_web_ui_flow_fixes.py`)**: 21 passed in 16.64s.
- **Student Portal Tests (`tests/api/test_student_portal_ui.py`)**: 16 passed in 10.51s.
- **Ruff & Mypy**: All checks passed (83 source files checked, 0 errors).
- **Live Container Verification on `http://localhost:5000` (`test_live_roles.py`)**:
  - Admin login: shows `QUẢN TRỊ VIÊN (ADMIN)` in topbar, dropdown displays all 3 role switch options.
  - Admin switches to `INSTRUCTOR` -> lands on `/instructor/dashboard`, topbar shows `GIẢNG VIÊN (INSTRUCTOR)`.
  - Admin switches to `STUDENT` -> lands on `/student/dashboard`, topbar shows `HỌC VIÊN (STUDENT)`, role switcher remains accessible.
  - Admin switches back to `ADMIN` -> lands on `/admin/dashboard`, topbar shows `QUẢN TRỊ VIÊN (ADMIN)`.
  - Instructor login: shows `GIẢNG VIÊN (INSTRUCTOR)` in topbar, dropdown displays only Instructor and Student options.
  - Instructor switches to `STUDENT` and back to `INSTRUCTOR` smoothly.
  - Instructor attempt to switch to `ADMIN` is rejected with HTTP 403.
  - Student login: shows `HỌC VIÊN (STUDENT)`, dropdown has NO role switcher section.
  - Student attempt to call `switch-role` is rejected with HTTP 403.


