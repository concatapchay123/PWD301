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

---

# TASK-032 — Student Self-Nomination & Administrative Review Workflow for Instructor Role

**Status:** DONE  
**Assignee:** Principal Software Architect & Lead Fullstack Engineer  
**Started Date:** 2026-09-12  
**Completed Date:** 2026-09-12  

## Goal
Implement an end-to-end self-nomination and onboarding workflow allowing standard users (`STUDENT`) to apply to become an `INSTRUCTOR` by providing required professional credentials and evidence (teaching experience/certificates, salary/compensation proof, educational institutional email, current teaching schedule, employment contract, Google Drive/Cloud scan folder URL, statement of purpose), coupled with an administrative review queue for Quản trị viên (`ADMIN`) to inspect, approve (granting `INSTRUCTOR` role per `AUTH-002`), or reject with justification.

## Source-of-Truth Documents
- `docs/system/PWD301_SYSTEM_SPECIFICATION/security/01_AUTHENTICATION_AUTHORIZATION.md` (AUTH-002 cumulative role hierarchy)
- `docs/system/PWD301_SYSTEM_SPECIFICATION/audit/01_AUDIT_LOG_SPECIFICATION.md` (Append-only audit trail)
- `docs/database/PWD301_DATABASE_ARCHITECTURE/` (SQL Server reference DDL, table `instructor_applications`)
- `frontend-preview/` (Functional Minimalism UI layout, tokens, typography, and styling)
- `AGENTS.md` (Strict verification, fail-closed security, role authorization)

## Key Changes
1. **Model Enhancements (`src/pwd301/models/identity.py`)**:
   - Reused canonical `InstructorApplication` schema without breaking DDL changes.
   - Added `parsed_details` property with JSON deserialization and error resilience.
   - Added Vietnamese user-friendly status labels (`status_label_vi`) and badge styling classes (`status_badge_class`).
2. **Service Layer (`src/pwd301/services/user_service.py`)**:
   - `submit_instructor_application`: Validates input, prevents duplicate pending submissions or re-application by existing instructors/admins, serializes structured evidence payload into `application_note` (capped at 2000 chars), and persists an `AuditEvent`.
   - `cancel_instructor_application`: Allows students to cancel their own `PENDING` application and records `AuditEvent`.
   - `get_user_active_application`, `get_instructor_application`, `list_instructor_applications`: Provides filtered queries.
   - `review_instructor_application`: Validates admin authorization, enforces required rejection reasons, approves via `assign_role_to_user(..., 'INSTRUCTOR')`, updates status, records append-only `AuditEvent`, and dispatches in-app notification.
3. **Web Blueprints & Routes**:
   - `src/pwd301/blueprints/student/routes.py`:
     - `GET /student/become-instructor`: Renders nomination form or current application status.
     - `POST /student/become-instructor`: Handles CSRF-protected nomination form submission.
     - `POST /student/become-instructor/cancel`: Cancels pending application.
   - `src/pwd301/blueprints/admin/routes.py`:
     - `GET /admin/instructor-applications`: Applications review queue with status tabs (`PENDING`, `APPROVED`, `REJECTED`, `ALL`).
     - `GET /admin/instructor-applications/<app_id>`: Detailed inspection view.
     - `POST /admin/instructor-applications/<app_id>/review`: Handles approve or reject actions.
4. **REST API Endpoints**:
   - `src/pwd301/blueprints/api_student/routes.py`:
     - `GET /api/student/instructor-application` (JWT Bearer)
     - `POST /api/student/instructor-application` (JWT Bearer)
     - `POST /api/student/instructor-application/cancel` (JWT Bearer)
   - `src/pwd301/blueprints/api_admin/routes.py`:
     - `GET /api/admin/instructor-applications` (Admin JWT Bearer)
     - `GET /api/admin/instructor-applications/<app_id>` (Admin JWT Bearer)
     - `POST /api/admin/instructor-applications/<app_id>/review` (Admin JWT Bearer)
5. **Functional Minimalism UI Templates**:
   - `src/pwd301/templates/student/become_instructor.html`: Multi-state view (Application form, Pending timeline, Rejection feedback banner, and Already-instructor banner).
   - `src/pwd301/templates/admin/instructor_applications.html`: Admin queue with KPI counters, filter pills, detailed candidate cards, and review modals.
   - Updated `src/pwd301/templates/base.html`: Added nomination links in desktop sidebar and mobile drawer for students and admins.
   - Updated `src/pwd301/templates/student/dashboard.html`: Added invitation card prompting students to apply as instructors.
   - Updated `frontend-preview/`: Synced preview mockup and interactions.

## Verification Record
- **Unit Tests (`tests/unit/test_instructor_application_service.py`)**: 7/7 passed.
- **Web UI & API Integration Tests (`tests/api/test_instructor_application_web_flow.py`)**: 7/7 passed.
- **Full Unit & Flow Test Suite**: 391 passed in 231.69s.
- **Ruff Linter**: 0 errors on modified files and tests.

---

# TASK-033 — Docker Container Auto-Reload & AI Assistance Resilience Overhaul

**Status:** DONE  
**Assignee:** Principal Software Architect & Lead Fullstack Engineer  
**Started Date:** 2026-09-12  
**Completed Date:** 2026-09-12  

## Goal
Investigate and resolve whole-project runtime failures preventing Docker web execution (HTTP 500 BuildError in Jinja) and AI Assistance failures (read timeouts on `gemini-3.6-flash`, broken fallback circuit in `RealGeminiClient`), ensuring full system health, type-checking compliance, and live conversational AI assistant integration.

## Root Cause Analysis
1. **Docker Jinja BuildError (Stale Gunicorn Memory)**:
   - Volume `./src:/app/src` updated on host with newly introduced endpoints (`student.become_instructor`), but the existing Gunicorn process in container `pwd301_web` retained old route definitions in memory.
   - When Jinja rendered `base.html`, `url_for('student.become_instructor')` threw `BuildError` resulting in a 500 Internal Server Error.
   - `docker-entrypoint.sh` lacked an auto-reload flag (`--reload`) when running in development (`APP_ENV=development` / `FLASK_DEBUG=1`).
2. **AI Assistance Failure & Defective Fallback Logic**:
   - `gemini-3.6-flash` consistently times out on socket read (>15s) or returns 503 Unavailable on Google's API, whereas `gemini-3.8-flash` responds in ~1.49s.
   - `RealGeminiClient._call_gemini_api` in `src/pwd301/services/gemini_service.py` immediately raised `AIServiceUnavailableError` upon timeout or 5xx error instead of continuing the `candidate_models` loop, preventing fallback models (`gemini-3.8-flash`) from ever executing.
   - The student chat route caught the exception and returned static canned responses.

## Key Changes
1. **Multi-Model Fallback Resiliency & Gemini 3.8 Flash Default**:
   - Updated `RealGeminiClient.FALLBACK_MODELS = ("gemini-3.8-flash", "gemini-3.6-flash", "gemini-flash-latest")`.
   - Updated default model to `gemini-3.8-flash` in `gemini_service.py`, `config.py`, `.env`, and `docker-compose.yml`.
   - Fixed `_call_gemini_api` to catch `TimeoutError`, `URLError`, and HTTP 5xx errors, log warnings, and seamlessly try the next model candidate.
2. **Gunicorn Development Auto-Reload**:
   - Updated `scripts/docker-entrypoint.sh` to automatically add `--reload` when `APP_ENV=development` or `FLASK_DEBUG=1`.
   - Recreated `pwd301_web` container via `docker compose up -d`.
3. **UI Formatting & Clean Formatting**:
   - Added `style="white-space: pre-wrap; line-height: 1.6;"` to the floating AI assistant in `src/pwd301/static/js/app_shell.js` for clean paragraph and list rendering.
   - Fixed all Mypy static typing issues (83 source files checked, 0 errors).
   - Fixed all Ruff linting and formatting issues (192 files checked, 0 errors).

## Verification Record
- **Full Verification Suite (`scripts/verify.ps1`)**: 858 passed in 488.93s (100% PASS).
- **Unit Tests (`tests/unit/test_ai_service.py`)**: 12/12 passed (including new `test_real_gemini_client_fallback_to_next_model`).
- **Mypy**: 0 errors across 83 source files.
- **Ruff**: 0 lint errors, 192 files formatted.
- **Live Container Verification on `http://localhost:5000`**:
  - `GET /health`: HTTP 200 OK.
  - `POST /auth/login`: HTTP 302 -> `/student/dashboard`.
  - `GET /student/dashboard`: HTTP 200 OK (Clean layout, zero 500 errors).
  - `POST /student/ai/chat`: HTTP 200 OK (Returns rich, intelligent Vietnamese answer from Gemini 3.8 Flash in < 2 seconds).

---

# TASK-034 — Real Server Hardware Telemetry Integration for System Operations & Governance Center

**Status:** DONE  
**Assignee:** Principal Software Architect & Lead Fullstack Engineer  
**Started Date:** 2026-09-12  
**Completed Date:** 2026-09-12  

## Goal
Resolve the bug where the section **"Trung tâm Điều hành & Quản trị Hệ thống"** (Admin System Operations & Governance Center) failed to retrieve actual physical/server hardware data, displaying 0% CPU, 0.0/0.0 GB RAM, 0 B network traffic, and missing hardware specs. Ensure robust cross-platform inspection (Linux container `/proc` filesystem and Windows `ctypes`/`winreg`), live dynamic telemetry polling, and synchronization between Jinja templates and the frontend preview prototype.

## Root Cause Analysis
1. **Missing `psutil` Dependency in Docker & Runtime**:
   - `psutil` was imported conditionally in `src/pwd301/services/operations_service.py`, but it was omitted from `requirements.txt` and docker wheels.
   - When running in production inside Docker on Linux, `psutil` import failed with `ModuleNotFoundError`.
2. **Platform-Restricted Fallback Mechanism**:
   - The zero-dependency fallback logic was previously guarded by `if sys.platform == "win32"`.
   - On Linux containers lacking `psutil`, RAM was returned as `0.0 / 0.0 GB (0.0%)`, CPU utilization as `0.0%`, Network as `0 B`, and uptime as empty.
3. **Zero CPU Sampling on Instantaneous Calls**:
   - `psutil.cpu_percent(interval=None)` without a calibration call or with `interval=0.05` returned `0.0%` on fast multi-core systems (e.g. 32-thread Intel i9-14900HX).
4. **Missing Hardware Model and Node Identification**:
   - The telemetry engine only reported generic logical core counts without resolving the host CPU brand model or distinguishing host vs Docker container environments.
5. **Static UI Lacking Live Telemetry Refresh**:
   - `src/pwd301/templates/admin/dashboard.html` rendered server health with hardcoded placeholders, lacking DOM IDs, dynamic JavaScript fetching, or auto-polling.
   - `frontend-preview/assets/js/views/admin.js` used simulated static numbers and did not attempt to query backend telemetry APIs.

## Key Changes
1. **Cross-Platform Telemetry Engine (`src/pwd301/services/operations_service.py`)**:
   - Added `psutil>=6.0.0,<8` to `requirements.txt` and `pyproject.toml` (mypy overrides).
   - Enhanced `get_real_system_telemetry()` to read CPU model:
     - Linux: `/proc/cpuinfo` (`model name`).
     - Windows: Registry `HARDWARE\DESCRIPTION\System\CentralProcessor\0` (`ProcessorNameString`).
   - Improved CPU percent calculation with calibrated sample interval (`0.1s`) and load average normalization fallback (`getattr(os, "getloadavg", None)`).
   - Added zero-dependency Linux stdlib fallbacks:
     - Memory: `/proc/meminfo` (`MemTotal`, `MemAvailable`, `Buffers`, `Cached`).
     - Uptime: `/proc/uptime`.
     - Network I/O: `/proc/net/dev`.
   - Added node environment detection (`node_label` = `Docker (<container_id>)` vs host).
2. **Analytics Service Key Compatibility (`src/pwd301/services/analytics_service.py`)**:
   - Added dual dictionary key support (`total`, `active`, `completed`, `clean_files`, `quarantined_files` alongside existing canonical keys) ensuring seamless Jinja template and API contract compatibility.
3. **Live Interactive Admin Dashboard (`src/pwd301/templates/admin/dashboard.html`)**:
   - Assigned dedicated DOM IDs to all hardware telemetry metrics (`telem-node-label`, `telem-cpu-percent`, `telem-ram-label`, `telem-disk-free`, `telem-net-traffic`, etc.).
   - Added "Làm mới phần cứng" action button with spin animation.
   - Integrated client-side asynchronous JavaScript `refreshServerTelemetry()` with 15-second background auto-polling.
4. **Frontend Preview Prototype (`frontend-preview/assets/js/views/admin.js`)**:
   - Updated section title to include "Trung tâm Điều hành & Quản trị Hệ thống — Tài nguyên Máy chủ".
   - Converted `refreshDashboardData()` to query live `/admin/telemetry` or `/api/admin/telemetry` when running against a live backend, falling back gracefully to mock simulation when offline.

## Verification Record
- **Unit Tests (`tests/unit/test_operations_service.py`)**: 15/15 passed (including `test_get_real_system_telemetry_keys`, `node_label`, `cpu.model`, `uptime`).
- **API Tests (`tests/api/test_analytics_api.py`, `tests/api/test_operations_api.py`)**: 10/10 passed (including `test_admin_telemetry_endpoints` and `test_admin_dashboard_web_renders_hardware_telemetry`).
- **Regression Suite (`tests/api/test_web_ui_flow_fixes.py`)**: 21/21 passed.
- **Ruff & Mypy**: 0 lint errors, 0 type errors across all touched files.
- **Live Docker Container Verification (`http://localhost:5000`)**:
  - `GET /admin/telemetry`: HTTP 200 OK returning real hardware metrics:
    - CPU: `32 vCPU • Intel(R) Core(TM) i9-14900HX`
    - RAM: `3.9 / 15.5 GB (25.0%)`, `11.6 GB khả dụng`
    - Disk: `5.4 GB / 1006.9 GB (0.6%)`, `950.2 GB còn trống`
    - Network: `Gửi: 180 KB • Nhận: 148 KB`
    - Node: `Docker (d799e6b0f3f6)`
    - OS: `Linux 6.18.33.2-microsoft-standard-WSL2`
  - `GET /admin/dashboard`: HTTP 200 OK with server telemetry wired to DOM and auto-refreshing.
