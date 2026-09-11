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
