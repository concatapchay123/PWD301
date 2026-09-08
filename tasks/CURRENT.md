# CURRENT TASK

## TASK-006 — Course Management, Lifecycle & Ownership/Reassignment

**Status:** DONE

### 1. Goal
Implement the core business logic, service layer (`course_service.py`), error definitions, and route handlers for Course Management. This includes CRUD operations, strict enforcement of the Course State Machine (`DRAFT -> SUBMITTED_FOR_REVIEW -> APPROVED -> PUBLISHED -> ARCHIVED -> TRASH`), application-level soft-delete (`trash_course`), and secure Administrator Ownership Reassignment with mandatory append-only `AuditEvent` logging. All operations adhere to the RBAC and resource ownership authorization foundation (TASK-005) and prevent Insecure Direct Object Reference (IDOR) vulnerabilities.

### 2. Source-of-truth documents
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/03_COURSE_MANAGEMENT.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/api/04_COURSE_API.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/state-machines/COURSE_STATE_MACHINE.md`
- `docs/database/PWD301_DATABASE_ARCHITECTURE/05_DATA_DICTIONARY_COURSE.md`
- `src/pwd301/models/course.py`
- `AGENTS.md` (Strict rules on IDOR prevention and Append-only Audit Logs).

### 3. In scope
1. **Course Service (`src/pwd301/services/course_service.py`):**
   - `create_course(actor, data)`: Enforces INSTRUCTOR or ADMIN role, default status `DRAFT`, validates uniqueness of `course_code_normalized` and `title_normalized`, constraints on `difficulty`, `capacity`, `storage_quota_bytes`, creates default `CourseCompletionRule`, and records `AuditEvent`.
   - `update_course(actor, course_id, data)`: Validates ownership with `require_course_manager`, enforces mass-assignment protection on immutable/privileged fields (`course_code`, `status`, `owner_instructor_id`), verifies title uniqueness if changed, and records `AuditEvent` if published.
   - `get_course_detail(actor, course_id)`: Resolves course and enforces visibility rules per `03_RESOURCE_AUTHORIZATION_RULES.md`.
   - `change_course_status(actor, course_id, new_status, reason)`: Enforces the exact Course State Machine transition graph. Only ADMIN can transition `SUBMITTED_FOR_REVIEW -> APPROVED`. Transition to `ARCHIVED` or `TRASH` validates active prerequisite dependencies (COURSE-005, COURSE-006). Records append-only `AuditEvent` for critical lifecycle transitions (`APPROVED`, `PUBLISHED`, `TRASH`, `ARCHIVED`).
   - `reassign_course_owner(admin_actor, course_id, new_instructor_id, reason)`: Admin-only operation. Verifies target instructor exists and has `INSTRUCTOR` role (supports `None` for unassigned course). Records mandatory append-only `AuditEvent`.
   - `trash_course(actor, course_id, reason)`: Soft-deletes course by setting `deleted_at = utc_now()`, `deleted_by_user_id = actor.id`, and `status = 'TRASH'`. Verifies prerequisite dependencies without running SQL DELETE.
   - `list_courses(...)`: Paginated course catalog filtering out soft-deleted courses by default, with role-based scoping (students see published courses, instructors see published + own courses, admin sees all).
2. **API and Web Routes:**
   - Instructor Blueprint (`src/pwd301/blueprints/instructor/routes.py`):
     - `POST /instructor/courses`: Create course (DRAFT).
     - `GET /instructor/courses/<course_id>`: View managed course details.
     - `PATCH /instructor/courses/<course_id>`: Update course metadata with mass-assignment defense.
     - `POST /instructor/courses/<course_id>/submit`: Submit course for admin review.
     - `POST /instructor/courses/<course_id>/trash`: Soft-delete course.
   - Admin Blueprint (`src/pwd301/blueprints/admin/routes.py`):
     - `GET /admin/courses/pending`: List courses in `SUBMITTED_FOR_REVIEW`.
     - `POST /admin/courses/<course_id>/review`: Approve (`APPROVED`) or Reject (`DRAFT`) course review.
     - `POST /admin/courses/<course_id>/reassign`: Reassign course owner with reason.
     - `POST /admin/courses/<course_id>/publish`: Publish approved course.
     - `POST /admin/courses/<course_id>/trash`: Soft-delete course.
     - `POST /admin/courses/<course_id>/restore`: Restore course from TRASH to ARCHIVED.
   - REST API Blueprint (`src/pwd301/blueprints/api_courses/`):
     - Endpoints under `/api/courses` per `04_COURSE_API.md` (`GET /api/courses`, `POST /api/courses`, `GET /api/courses/<id>`, `PATCH /api/courses/<id>`, `POST /api/courses/<id>/publish-request`, `POST /api/courses/<id>/archive`), CSRF-exempt for Bearer JWT clients.
3. **Audit Logging:**
   - All critical actions (creation, approval, publish, status change, ownership reassignment, and trashing) record immutable entries in `AuditEvent`.
4. **Testing:**
   - Unit tests in `tests/unit/test_course_service.py` (11 tests).
   - Security negative and IDOR tests in `tests/security/test_course_idor.py` (8 tests).
   - REST API integration tests in `tests/api/test_course_api.py` (4 tests).

### 4. Out of scope
- Lesson and Module management (Deferred to TASK-007).
- Student Enrollment logic (Deferred to TASK-008).
- File/Thumbnail uploading (Deferred to TASK-018).

### 5. Security & Invariants
- **Bất biến 1 (IDOR Prevention):** Giảng viên chỉ được quản lý, nộp duyệt, hoặc đưa vào thùng rác các khóa học mà mình đang trực tiếp sở hữu (`owner_instructor_id == actor.id`).
- **Bất biến 2 (Admin Authority):** Chỉ Quản trị viên (ADMIN) mới có quyền duyệt khóa học (`SUBMITTED_FOR_REVIEW -> APPROVED`) và đổi quyền sở hữu (`owner_instructor_id`). Giảng viên không thể tự duyệt hoặc chuyển nhượng khóa học.
- **Bất biến 3 (Prerequisite Safety):** Khóa học đang được làm điều kiện tiên quyết (prerequisite) cho bất kỳ khóa học đang hoạt động (active) nào khác không được phép lưu trữ (`ARCHIVED`) hoặc xóa (`TRASH`).
- **Bất biến 4 (Soft-Delete):** Xóa khóa học thực hiện qua soft-delete (`deleted_at`, `deleted_by_user_id`, `status='TRASH'`), không chạy SQL DELETE cứng, bảo toàn toàn bộ dữ liệu lịch sử.
- **Bất biến 5 (Append-only Audit):** Mọi thao tác thay đổi quyền sở hữu hoặc trạng thái quan trọng bắt buộc ghi nhận vào bảng `AuditEvent` trong cùng transaction.

### 6. Acceptance Criteria (Checklist)
- [x] `course_service.py` is fully implemented with type hints and docstrings.
- [x] Instructor can create a course (default status `DRAFT`).
- [x] Instructor can transition their course from `DRAFT` to `SUBMITTED_FOR_REVIEW`.
- [x] Instructor CANNOT transition course directly to `PUBLISHED` without ADMIN approval.
- [x] Admin can approve a course (transition to `APPROVED`) and reassign the `owner_instructor_id`.
- [x] `AuditEvent` is correctly appended when ownership is reassigned.
- [x] Soft-delete sets `deleted_at` instead of executing a hard SQL DELETE.
- [x] Attempting to edit another instructor's course raises `ForbiddenError` (HTTP 403).

### 7. Verification commands
1. `mypy src/pwd301/services/course_service.py` (Success: no issues found).
2. `ruff check src/pwd301/services/course_service.py tests/unit/test_course_service.py` (All checks passed).
3. `pytest tests/unit/test_course_service.py tests/security/test_course_idor.py -v` (19 passed).
4. `./scripts/verify.ps1` (157 passed, repository contracts, compilation, lint, format, type checks pass).

---

## Completion Report

### A. Scope and sources consulted
- Operating contract: `AGENTS.md`
- Course business specifications: `docs/system/PWD301_SYSTEM_SPECIFICATION/business/03_COURSE_MANAGEMENT.md`
- Course API specifications: `docs/system/PWD301_SYSTEM_SPECIFICATION/api/04_COURSE_API.md`
- Course state machine: `docs/system/PWD301_SYSTEM_SPECIFICATION/state-machines/COURSE_STATE_MACHINE.md`
- Course data dictionary: `docs/database/PWD301_DATABASE_ARCHITECTURE/05_DATA_DICTIONARY_COURSE.md`
- Non-negotiable invariants: `docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md`
- Existing authorization service: `src/pwd301/services/authorization_service.py`

### B. Reuse decisions
- Reused `Course`, `CourseCompletionRule`, and `CoursePrerequisite` models from `src/pwd301/models/course.py`.
- Reused `require_course_manager`, `can_view_course`, `can_manage_course`, `_resolve_course`, `_resolve_user` from `src/pwd301/services/authorization_service.py`.
- Reused `AuditEvent` from `src/pwd301/models/notification_audit.py` for immutable audit trails.
- Reused `_format_error_response` and Flask application factory error-handling patterns in `src/pwd301/__init__.py`.

### C. Per-file changes
- `src/pwd301/services/exceptions.py` (MODIFY): Added course domain exceptions `CourseError`, `CourseAlreadyExistsError`, `CourseNotFoundError`, `CourseStateViolationError`, `CourseDependencyError`, `CourseValidationError`.
- `src/pwd301/services/course_service.py` (NEW): Implemented complete course service layer: `create_course`, `update_course`, `get_course_detail`, `change_course_status`, `reassign_course_owner`, `trash_course`, `list_courses`, along with prerequisite validation and audit recording helpers.
- `src/pwd301/services/__init__.py` (MODIFY): Exported course service functions and exceptions.
- `src/pwd301/__init__.py` (MODIFY): Registered error handlers for course domain exceptions (mapping to 409 CONFLICT, 409 STATE_VIOLATION, 409 PREREQUISITE_DEPENDENCY, 400 VALIDATION_ERROR), registered `api_course_bp`, and exempted it from CSRF.
- `src/pwd301/blueprints/instructor/routes.py` (MODIFY): Added instructor course endpoints for `POST /instructor/courses`, `GET /instructor/courses/<id>`, `PATCH /instructor/courses/<id>`, `POST /instructor/courses/<id>/submit`, `POST /instructor/courses/<id>/trash`.
- `src/pwd301/blueprints/admin/routes.py` (MODIFY): Added admin review and lifecycle endpoints for `GET /admin/courses/pending`, `POST /admin/courses/<id>/review`, `POST /admin/courses/<id>/reassign`, `POST /admin/courses/<id>/publish`, `POST /admin/courses/<id>/trash`, `POST /admin/courses/<id>/restore`.
- `src/pwd301/blueprints/api_courses/__init__.py` (NEW): Initialized `api_courses` blueprint with `/api/courses` url prefix.
- `src/pwd301/blueprints/api_courses/routes.py` (NEW): Implemented REST API endpoints per `04_COURSE_API.md`.
- `tests/unit/test_course_service.py` (NEW): Added 11 unit test functions covering creation, validation, duplicates, owner overrides, metadata updates, visibility scoping, state transitions, illegal transitions, prerequisite blocks, owner reassignment, and catalog pagination.
- `tests/security/test_course_idor.py` (NEW): Added 8 security tests validating cross-instructor IDOR protection on edit, submit, trash; instructor approval denial; instructor reassignment denial; student access denial; and unauthenticated rejection.
- `tests/api/test_course_api.py` (NEW): Added 4 integration tests for REST API endpoints `/api/courses`.

### D. Deletion and simplification list
| Candidate | Classification | Reason | Action |
|---|---|---|---|
| Hard SQL DELETE on courses table | REMOVE NOW | Invariant DELETE-001 & COURSE_MANAGEMENT.md prohibit destructive cascade | Used soft-delete (`deleted_at`, `status='TRASH'`) with application-level prerequisite safety check |
| Direct instructor transition to PUBLISHED | REMOVE NOW | Violates state machine approval requirement | Enforced mandatory ADMIN approval before transition to PUBLISHED |
| Client-provided owner ID for instructors | REMOVE NOW | IDOR vulnerability | Forced `owner_instructor_id = actor.id` for instructors; only admin can override owner |
| Unrestricted course updates | SIMPLIFY NOW | Mass assignment risk on privileged fields | Whitelisted writable fields (`title`, `description`, `category`, `difficulty`, `capacity`, `storage_quota_bytes`, `thumbnail_file_asset_id`) |

### E. Ponytails / deferred debt
- None. Complete business logic, validation, state machine transitions, ownership reassignment, and IDOR protection are verified and tested.

### F. Verification actually run and results
1. `mypy src/pwd301/services/course_service.py`:
   ```
   Success: no issues found in 1 source file
   ```
2. `mypy src`:
   ```
   Success: no issues found in 40 source files
   ```
3. `ruff check src tests scripts`:
   ```
   All checks passed!
   ```
4. `ruff format --check src tests scripts`:
   ```
   56 files already formatted
   ```
5. `pytest tests/unit/test_course_service.py tests/security/test_course_idor.py -v`:
   ```
   ============================= 19 passed in 7.32s ==============================
   ```
6. `./scripts/verify.ps1`:
   ```
   == Repository contract ==
   PWD301 repository check: E:\PWD301
   [PASS] Required repository contract files exist
   [PASS] No duplicate database architecture/SQL copy under System Specification
   [PASS] Canonical SQL Server DDL contains 71 CREATE TABLE statements
   [PASS] Markdown code fences are balanced
   [NOTE] .env exists locally; ensure it remains ignored by Git
   [PASS] Environment template exists
   [PASS] Repository contract check complete
   == Python compile ==
   == Lint / format / types ==
   All checks passed!
   56 files already formatted
   Success: no issues found in 40 source files
   == Tests ==
   ============================ 157 passed in 36.87s =============================
   PWD301 verification PASS
   ```

### G. Remaining risks / next step
- Next scheduled task on roadmap: **TASK-007 — Lesson and Module Content Management**.

---

## Historical Tasks

### TASK-005 — Authorization & Role-Based Access Control (RBAC & Resource Ownership)
**Status:** DONE  
*Xây dựng hệ thống phân quyền (Authorization) toàn diện kết hợp RBAC và Resource/Object-level Authorization ngăn chặn IDOR, decorators `@require_roles`, `@instructor_required`, `@admin_required`, và context resolvers cho cả Web session và JWT.*

### TASK-004 — Authentication & Identity Workflows (Web Session + JWT REST)
**Status:** DONE  
*Xây dựng hệ thống xác thực kép (Dual Authentication): Web UI session cookies với HttpOnly/CSRF protection và REST API JWT Bearer token theo RFC 7519, cùng cơ chế thu hồi phiên và Refresh Token Rotation.*

### TASK-003 — User / Account / Email Verification Foundation
**Status:** DONE  
*Core user account management, password hashing, and secure token lifecycle for email verification and password reset.*

### TASK-002 — Domain Models & Initial SQL Server Migrations
**Status:** DONE  
*Translated canonical database architecture into SQLAlchemy domain models in Flask. Generated baseline Alembic migration script compatible with Microsoft SQL Server, provided idempotent baseline seed script (`flask seed-baseline`), and verified all invariants.*

### TASK-001 — Project Foundation & Flask Bootstrap
**Status:** DONE  
*Completed foundation bootstrap including Flask application factory, configuration classes, extension shells, `/health` and `/` routes, error handlers, and smoke test suite.*
