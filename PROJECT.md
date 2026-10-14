# Project: PWD301 Course Changeset & UI Remediation (TASK-091)

## Architecture
- **Pure Headless Backend**: Flask REST API serving standard JSON `{"success": true/false, "data": ..., "error": ...}`.
- **Client Frontend**: Vanilla JS SPA with component views (`student.js`, `instructor.js`, `instructor-exams.js`, `admin.js`), client-side routing (`router.js`), and centralized API client (`api.js`).
- **Database & Locking**: Microsoft SQL Server Express with SQLAlchemy ORM, table hints `WITH (UPDLOCK, HOLDLOCK)` for concurrency control, UTC `DATETIME2(3)`, and monotonic progress calculation.
- **Security & RBAC**: Session authentication for web SPA, JWT for REST clients, 2-tier sub-role RBAC in `UserRole.assignment_reason`, Fail-Closed virus/file security, Anti-Leak exam preview.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| F01 | Legacy Purge & Spec Updates | Purge old fragmented workflow descriptions in specs, lock `/leave` invariant | M0 | Survey & Plan §2 |
| F02 | Lifetime Enrollment REST Lock | Lock `POST /api/courses/<id>/leave` to HTTP 403 Forbidden | M1 | Survey & Plan §6 |
| F03 | Unified Staging Draft Engine | Consolidate metadata & lessons into single `CourseVersionChangeset`, atomic MSSQL commit | M1 | Survey & Plan §3 |
| F04 | Video Auto-Complete Backend | Accept video completion flag without failing `sec < 1` validation | M1 | Survey & Plan §4 |
| F05 | Drag-and-Drop Quiz Grading | Support token choices and clean text fallback in `attempt_service.py` | M1 | Survey & Plan §8 |
| F06 | 2-Tier Broadcast RBAC Backend | Primary Admin full access, System Monitoring Admin restricted to `SYSTEM`, others 403 | M1 | Survey & Plan §10 |
| F07 | Teaching Assignment Course Access | Allow `ADMIN_TEACHING_ASSIGNMENT` access to `GET /admin/courses` | M1 | Survey & Plan §13 |
| F08 | Video Auto-Complete & Dynamic Progress | Video `onEnded` triggers completion, topbar calculates `(completed/total)*100%` | M2 | Survey & Plan §4 |
| F09 | Universal Matching Board Binding | Bind `.cisco-quiz-matching-board` on initial render with SVG bezier curves | M2 | Survey & Plan §5 |
| F10 | Mini-Quiz NetAcad Dark Retry UI | NetAcad dark slate/emerald retry screen, clean SVG & state reset, fix 1-q pagination | M2 | Survey & Plan §5 |
| F11 | Exam Anti-Leak & Slot Indicators | Keep exam attempt neutral; post-submission review renders slot-by-slot green/red badges | M2 | Survey & Plan §8 |
| F12 | Student Lifetime Enrollment UI | Clean legacy withdrawal calls from `api.js` and student views | M2 | Survey & Plan §6 |
| F13 | Visual Math Palette ($f(x)$ / KaTeX) | Palette toolbar with math symbols and live KaTeX preview in Exam Studio | M3 | Survey & Plan §9 |
| F14 | Instructor Roster Nav & 3-Tab About | Rename to "Danh sách sinh viên" -> roster, reorganize About into 3 standard tabs | M3 | Survey & Plan §7 |
| F15 | Consolidated Changeset Draft UI | Draft bar shows pending metadata & lesson count, single `submitCourseChangeset` call | M3 | Survey & Plan §3 |
| F16 | Admin 16:9 Cover Showcase | 16:9 hero card for `thumbnail_url` with placeholder, unified metadata/curriculum diff | M4 | Survey & Plan §12 |
| F17 | Admin 2-Tier Broadcast UI | Sub-role based hiding/locking of broadcast notification modal | M4 | Survey & Plan §10 |
| F18 | Teaching Assignment Instant Search | Live client-side search input filtering courses in reassign modal | M4 | Survey & Plan §13 |
| F19 | Admin Queue Sync & Persistence | Sync KPI cards, topbar badge, and table rows immediately post-approval | M4 | Survey & Plan §11 |
| F20 | Verification & E2E Testing | Comprehensive Pytest suites, `verify.ps1`, and live browser verification | M5 | Survey & Plan §14 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M0 | Legacy Purge & Specification Updates | F01 | none | PLANNED |
| M1 | Backend Core Workflows & APIs | F02, F03, F04, F05, F06, F07 | M0 | PLANNED |
| M2 | Frontend Student & Quiz Remediation | F08, F09, F10, F11, F12 | M1 | PLANNED |
| M3 | Frontend Instructor Studio & KaTeX | F13, F14, F15 | M1 | PLANNED |
| M4 | Frontend Admin Governance & RBAC | F16, F17, F18, F19 | M1 | PLANNED |
| M5 | Comprehensive Verification & E2E Testing | F20 | M2, M3, M4 | PLANNED |

## Interface Contracts
### Instructor Studio ↔ Backend Changeset API
- `GET /instructor/courses/<id>/changeset/status`: Returns `{"staged_lessons": N, "deleted_staged": N, "has_metadata_changes": bool, "summary": str}`
- `POST /instructor/courses/<id>/changeset/submit`: Bundles metadata diff + curriculum diff into 1 `CourseChangeRequest`
- `POST /instructor/courses/<id>/changeset/discard`: Reverts all staged lesson and metadata changes

### Student Video Player ↔ Backend Progress API
- `POST /student/courses/<cid>/lessons/<lid>/progress`: Accepts `seconds_spent`, `view_fraction`, `completed=true`. Server validates wall-clock pacing or server-verified video end and returns `is_completed: bool`, `current_progress_percent: float`.

### Student Exam Attempts ↔ Grading Engine
- `POST /student/assessments/<id>/attempts/<attempt_id>/submit`: Evaluates answers using choice keys or clean text fallback.
- `GET /student/assessments/results?id=<attempt_id>`: Returns question details with grouped choices and `slot_results: [{"slot": 0, "is_correct": bool, "user_text": str, "expected_text": str}]`.

## Code Layout
- Exclusive Write Boundaries for Workers:
  - **Worker M0**: `tasks/CURRENT.md`, `docs/system/PWD301_SYSTEM_SPECIFICATION/business/01_BUSINESS_RULE_CATALOG.md`, `docs/system/PWD301_SYSTEM_SPECIFICATION/api/04_COURSE_API.md`, `docs/system/PWD301_SYSTEM_SPECIFICATION/api/12_ADMIN_API.md`, `docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md`.
  - **Worker M1**: `src/pwd301/blueprints/api_courses/routes.py`, `src/pwd301/blueprints/admin/routes.py`, `src/pwd301/services/course_service.py`, `src/pwd301/services/lesson_service.py`, `src/pwd301/services/attempt_service.py`, `tests/api/test_course_changeset_workflow.py`, `tests/api/test_enrollment_api.py`.
  - **Worker M2**: `frontend/assets/js/views/student.js`, `frontend/assets/js/api.js`.
  - **Worker M3**: `frontend/assets/js/views/instructor.js`, `frontend/assets/js/views/instructor-exams.js`, `frontend/assets/js/router.js`.
  - **Worker M4**: `frontend/assets/js/views/admin.js`.
  - **Worker M5**: `tests/unit/test_course_staging_draft.py`, `tests/unit/test_lifetime_enrollment.py`, `tests/unit/test_broadcast_notification_rbac.py`, `tests/unit/test_drag_drop_quiz_grading.py`, `tests/unit/test_admin_teaching_assignment_courses.py`.
