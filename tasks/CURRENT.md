# CURRENT TASK

## TASK-007 — Lesson Management, Reordering & Completion Tracking

**Status:** DONE

### 1. Goal
Triển khai toàn diện tầng nghiệp vụ (`lesson_service.py`), các ngoại lệ miền (`exceptions.py`), bộ điều khiển route (Web UI & REST API), giải thuật ghi nhận tiến độ (`02_LESSON_COMPLETION_ALGORITHM.md`) và cơ chế tái sắp xếp thứ tự bài học (Lesson Reordering) an toàn với ràng buộc CSDL. Tất cả thao tác tuân thủ nghiêm ngặt ma trận phân quyền (RBAC), phòng chống lỗ hổng IDOR, và ghi nhận Append-only Audit Log cho các hành vi thay đổi cấu trúc hoặc xóa bài học.

### 2. Source-of-truth documents
- `AGENTS.md` (Quy tắc bất biến, phân quyền, Source-of-Truth Hierarchy).
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/04_LESSON_AND_PROGRESS.md` (Đặc tả nghiệp vụ bài học & tiến độ).
- `docs/system/PWD301_SYSTEM_SPECIFICATION/algorithms/02_LESSON_COMPLETION_ALGORITHM.md` (Giải thuật hoàn thành bài học).
- `docs/system/PWD301_SYSTEM_SPECIFICATION/api/04_COURSE_API.md` & `05_ENROLLMENT_PROGRESS_API.md`.
- `docs/database/PWD301_DATABASE_ARCHITECTURE/05_DATA_DICTIONARY_COURSE.md` (Chi tiết bảng `lessons`, `lesson_progress`).
- `src/pwd301/models/course.py` (Domain models: `Lesson`, `LessonProgress`, `Course`, `Enrollment`, `EnrollmentPeriod`).
- `src/pwd301/services/authorization_service.py` (`require_course_manager`, `can_manage_lesson`, `can_view_course`).

### 3. In scope
1. **Tầng Ngoại lệ (Domain Exceptions) — `src/pwd301/services/exceptions.py`:**
   - `LessonError(ServiceError)`
   - `LessonNotFoundError(ResourceNotFoundError, LessonError)`
   - `LessonStateViolationError(LessonError)`
   - `LessonPositionConflictError(LessonError)`
   - `LessonValidationError(LessonError)`
   - `LessonProgressError(LessonError)`
2. **Tầng Dịch vụ (Service Layer) — `src/pwd301/services/lesson_service.py`:**
   - `create_lesson(actor, course_id, data)`: Kiểm tra quyền qua `require_course_manager`. Tự động gán `position` liên tục hoặc dịch chuyển bài học an toàn (kỹ thuật temporary positive offset `+ 1_000_000` tránh vi phạm `CheckConstraint("position > 0")` và `UniqueConstraint(course_id, position)`). Giá trị mặc định chuẩn: `status = 'DRAFT'`, `minimum_completion_seconds = 30`, `viewed_fraction_required = 0.8000`. Ghi `AuditEvent` khi khóa học đã ở trạng thái `PUBLISHED`.
   - `update_lesson(actor, lesson_id, data)`: Kiểm tra quyền sở hữu. Chống Mass-Assignment qua whitelist fields (`title`, `summary`, `markdown_content`, `estimated_duration_minutes`, `minimum_completion_seconds`, `viewed_fraction_required`, `status`). Cấm sửa `position` trực tiếp. Cấm chuyển sang `PUBLISHED` nếu khóa học đang ở `TRASH` hoặc `ARCHIVED`.
   - `reorder_lessons(actor, course_id, ordered_lesson_ids)`: Đổi thứ tự 1..N an toàn qua 2 pha trong 1 transaction duy nhất (Phase 1: temporary positive offset, Phase 2: contiguous 1..N). Kiểm tra tính toàn vẹn tuyệt đối (không thừa, thiếu, trùng lặp). Ghi `AuditEvent`.
   - `trash_lesson(actor, lesson_id, reason)`: Soft-delete (`deleted_at = utc_now()`, `deleted_by_user_id = actor.id`, `status = 'TRASH'`). Đưa vị trí bài học đã xóa ra ngoài dải hoạt động (`10_000_000 + id`) và tự động co lại thứ tự các bài học còn lại thành 1..(N-1). Ghi nhật ký bắt buộc vào `AuditEvent`.
   - `change_lesson_status(actor, lesson_id, new_status, reason)`: Quản lý chuyển đổi trạng thái (`DRAFT`, `PUBLISHED`, `HIDDEN`). Ghi `AuditEvent`.
   - `get_lesson_detail(actor, lesson_id)`: Phân quyền theo vai trò: Instructor/Admin đọc được mọi trạng thái bài học thuộc khóa học quản lý. Student chỉ đọc được bài học `PUBLISHED` và phải có `Enrollment` trạng thái `ACTIVE` trong khóa học đó.
   - `get_course_lessons(actor, course_id)`: Liệt kê danh sách bài học sắp xếp theo position, lọc theo quyền truy cập.
   - `record_lesson_progress(actor, lesson_id, seconds_increment, view_fraction)`: Thuật toán 02 ghi nhận tiến độ học tập: Xác thực sinh viên có `Enrollment` và `EnrollmentPeriod` trạng thái `ACTIVE`. Chống gian lận (1 <= `seconds_increment` <= 60, 0.0 <= `view_fraction` <= 1.0). Tăng `seconds_spent`, cập nhật `max_view_fraction`. Đánh giá hoàn thành một chiều (Monotonic Completion): khi `seconds_spent >= minimum_completion_seconds` và `max_view_fraction >= viewed_fraction_required`, thiết lập `completed_at = utc_now()`, lưu `completion_rule_snapshot_json`, cập nhật cache `enrollment.current_progress_percent`. Trạng thái hoàn thành có tính bất biến và idempotent.
3. **Tầng Blueprints & Route Handlers:**
   - Instructor Blueprint (`src/pwd301/blueprints/instructor/routes.py`):
     - `POST /instructor/courses/<course_id>/lessons`
     - `GET /instructor/lessons/<lesson_id>`
     - `PATCH /instructor/lessons/<lesson_id>`
     - `POST /instructor/courses/<course_id>/lessons/reorder`
     - `POST /instructor/lessons/<lesson_id>/status`
     - `POST /instructor/lessons/<lesson_id>/trash`
   - Student Blueprint (`src/pwd301/blueprints/student/routes.py`):
     - `GET /student/courses/<course_id>/lessons/<lesson_id>`
     - `POST /student/lessons/<lesson_id>/progress`
   - REST API Blueprint (`api_courses` & `api_lessons`):
     - `GET /api/courses/<course_id>/lessons`
     - `GET /api/lessons/<lesson_id>`
     - `POST /api/lessons/<lesson_id>/progress` & alias `POST /api/lessons/<lesson_id>/activity`
4. **Error Handling & App Factory (`src/pwd301/__init__.py`):**
   - Đăng ký map các Exception của Lesson sang mã HTTP chuẩn:
     - `LessonNotFoundError` -> 404 RESOURCE_NOT_FOUND
     - `LessonPositionConflictError` -> 409 CONFLICT
     - `LessonStateViolationError` -> 409 STATE_VIOLATION
     - `LessonValidationError` -> 400 VALIDATION_ERROR
     - `LessonProgressError` -> 400 VALIDATION_ERROR
   - Đăng ký `api_lesson_bp` và miễn trừ CSRF cho REST API clients.

### 4. Out of scope
- Tải lên file đa phương tiện, video streaming hoặc asset đính kèm (`lesson_resources`) -> Đợi **TASK-018** & **TASK-019**.
- Quá trình đăng ký ghi danh (`enrollment_service.py`) -> Đợi **TASK-008**.
- Đánh giá tổng thể hoàn thành khóa học (`CourseCompletionSummary`) -> Đợi **TASK-009**.

### 5. Security & Invariants
- **Bất biến 1 (IDOR & Resource Isolation):** Giảng viên chỉ được tạo, xem, cập nhật, reorder hoặc trash bài học của khóa học do mình trực tiếp quản lý (`owner_instructor_id == actor.id`).
- **Bất biến 2 (Student Access Guard):** Sinh viên không được xem bài học `DRAFT`, `HIDDEN` hoặc `TRASH`, và không thể ghi nhận tiến độ nếu chưa có `Enrollment` và `EnrollmentPeriod` trạng thái `ACTIVE`.
- **Bất biến 3 (Unique Contiguous Positions):** Tại mỗi khóa học, giá trị `position` của các bài học hoạt động phải là một dãy số nguyên dương liên tục bắt đầu từ 1, không được trùng lặp. Khi soft-delete, bài học bị trash được đưa ra ngoài dải (`10_000_000 + id`) và các bài học còn lại tự động co về `1..(N-1)`.
- **Bất biến 4 (Monotonic & Idempotent Completion):** Sinh viên không thể gửi trực tiếp `completed=true`. Server đánh giá dựa trên `seconds_spent` và `max_view_fraction`. Khi đã hoàn thành (`completed_at IS NOT NULL`), trạng thái không bị đảo ngược khi tiếp tục ping.
- **Bất biến 5 (Append-Only Audit):** Mọi thao tác soft-delete (`trash_lesson`), thay đổi cấu trúc (`reorder_lessons`), hoặc thay đổi bài học trên khóa học đã `PUBLISHED` đều ghi `AuditEvent` trong cùng transaction.

### 6. Acceptance Criteria (Checklist)
- [x] `exceptions.py` bổ sung đầy đủ các domain exceptions cho bài học.
- [x] `lesson_service.py` triển khai đầy đủ các hàm xử lý logic với type hints và docstrings.
- [x] Tạo bài học thành công với `position` tự tăng bắt đầu từ 1.
- [x] Tạo bài học tại vị trí chỉ định tự động dịch chuyển các bài học phía sau an toàn.
- [x] Cập nhật bài học với whitelist fields (chống mass-assignment) và cấm sửa `position` trực tiếp.
- [x] Reorder bài học thành công không bị vi phạm UniqueConstraint `(course_id, position)`.
- [x] Reorder thất bại khi danh sách ID bài học không hợp lệ, thiếu, hoặc trùng lặp.
- [x] Soft-delete bài học và tự co lại thứ tự các bài học còn lại thành dãy liên tục 1..(N-1).
- [x] Ghi nhận tiến độ học (`seconds_spent`, `max_view_fraction`) có kiểm tra anti-tampering.
- [x] Đánh dấu hoàn thành đúng lúc khi đủ thời gian và tỷ lệ xem, lưu snapshot cấu hình hoàn thành.
- [x] Tính bất biến và idempotent của trạng thái hoàn thành.
- [x] IDOR: Giảng viên A không thể can thiệp vào bài học của Giảng viên B (HTTP 403).
- [x] Sinh viên chưa ghi danh hoặc truy cập bài học DRAFT bị từ chối (HTTP 403).
- [x] Blueprints Instructor, Student, REST API (`api_courses`, `api_lessons`) hoạt động đầy đủ.

### 7. Verification commands
1. `mypy src/pwd301/services/lesson_service.py tests/unit/test_lesson_service.py` -> Success: no issues found in 2 source files.
2. `ruff check src tests scripts` -> All checks passed!
3. `ruff format --check src tests scripts` -> 61 files already formatted.
4. `pytest tests/unit/test_lesson_service.py tests/security/test_lesson_idor.py tests/api/test_lesson_api.py -v` -> 26 passed in 8.95s.
5. `./scripts/verify.ps1` -> 183 passed in 46.21s (100% PASS, 0 failures).

---

## Completion Report

### A. Scope and sources consulted
- Operating contract: `AGENTS.md`
- Lesson & progress business rules: `docs/system/PWD301_SYSTEM_SPECIFICATION/business/04_LESSON_AND_PROGRESS.md`
- Lesson completion algorithm: `docs/system/PWD301_SYSTEM_SPECIFICATION/algorithms/02_LESSON_COMPLETION_ALGORITHM.md`
- Course & progress API contracts: `docs/system/PWD301_SYSTEM_SPECIFICATION/api/04_COURSE_API.md` & `05_ENROLLMENT_PROGRESS_API.md`
- Course data dictionary: `docs/database/PWD301_DATABASE_ARCHITECTURE/05_DATA_DICTIONARY_COURSE.md`
- Non-negotiable invariants: `docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md`
- Domain models: `src/pwd301/models/course.py`
- Authorization service: `src/pwd301/services/authorization_service.py`

### B. Reuse decisions
- Reused `Lesson`, `LessonProgress`, `Course`, `Enrollment`, `EnrollmentPeriod` models from `src/pwd301/models/course.py`.
- Reused `require_course_manager`, `can_manage_lesson`, `can_view_course`, `_resolve_course`, `_resolve_lesson`, `_resolve_user` from `src/pwd301/services/authorization_service.py`.
- Reused `AuditEvent` model from `src/pwd301/models/notification_audit.py` for append-only audit logging.
- Reused `_format_error_response` and centralized error handling architecture in `src/pwd301/__init__.py`.
- Reused `student_required`, `instructor_required`, `get_authenticated_actor` decorators for route protection.

### C. Per-file changes
- `src/pwd301/services/exceptions.py` (MODIFY): Added domain exceptions `LessonError`, `LessonNotFoundError`, `LessonStateViolationError`, `LessonPositionConflictError`, `LessonValidationError`, `LessonProgressError`.
- `src/pwd301/services/lesson_service.py` (NEW): Implemented complete lesson service layer: `create_lesson`, `update_lesson`, `reorder_lessons`, `trash_lesson`, `change_lesson_status`, `get_lesson_detail`, `get_course_lessons`, `record_lesson_progress`, `get_lesson_progress`, along with audit event logging and safe 2-phase reordering.
- `src/pwd301/services/__init__.py` (MODIFY): Exported all lesson service functions and domain exceptions.
- `src/pwd301/__init__.py` (MODIFY): Registered error handlers for lesson domain exceptions (mapping to 404 RESOURCE_NOT_FOUND, 409 CONFLICT, 409 STATE_VIOLATION, 400 VALIDATION_ERROR), registered `api_lesson_bp`, and exempted it from CSRF.
- `src/pwd301/blueprints/instructor/routes.py` (MODIFY): Added instructor lesson routes for creation, viewing, updating, reordering, status change, and trashing.
- `src/pwd301/blueprints/student/routes.py` (MODIFY): Added student lesson routes for studying a lesson with enrollment verification and heartbeat progress recording.
- `src/pwd301/blueprints/api_courses/routes.py` (MODIFY): Added `GET /api/courses/<course_id>/lessons` with role-based scoping.
- `src/pwd301/blueprints/api_lessons/__init__.py` (NEW): Initialized `api_lessons` blueprint with `/api/lessons` url prefix.
- `src/pwd301/blueprints/api_lessons/routes.py` (NEW): Implemented REST API endpoints `GET /api/lessons/<id>`, `POST /api/lessons/<id>/progress`, and `POST /api/lessons/<id>/activity`.
- `tests/unit/test_lesson_service.py` (NEW): Implemented 14 comprehensive unit tests covering auto-increment positioning, shifting, validation rules, course status blocks, update whitelist, reordering, unique collision prevention, soft-delete compaction, status transitions, access rules, Algorithm 02 monotonic progress, idempotency, anti-tampering, and audit logging.
- `tests/security/test_lesson_idor.py` (NEW): Implemented 7 security and IDOR tests verifying cross-instructor edit/reorder/trash denial, student draft access denial, non-enrolled progress denial, anonymous access rejection, and admin oversight.
- `tests/api/test_lesson_api.py` (NEW): Implemented 5 integration tests for REST API endpoints `/api/courses/<id>/lessons` and `/api/lessons/<id>/...`.
- `tasks/CURRENT.md` (MODIFY): Recorded TASK-007 completion and moved TASK-006 to Historical Tasks.

### D. Deletion and simplification list
| Candidate | Classification | Reason | Action |
|---|---|---|---|
| Hard SQL DELETE on lessons table | REMOVE NOW | Invariant DELETE-001 & DATA_DICTIONARY prohibit destroying learning history | Implemented application-level soft-delete (`deleted_at`, `status='TRASH'`) and repositioning to `10_000_000 + id` |
| Negative temporary positions during reorder | REMOVE NOW | Violates check constraint `ck_lessons_1 (position > 0)` | Replaced with positive offset (`position + 1_000_000`) in 2-phase update |
| Client-provided `completed` flag in progress ping | REMOVE NOW | Anti-tampering / Invariant PROGRESS-001 prohibits client asserting completion | Enforced server-authoritative evaluation: `seconds_spent >= minimum_completion_seconds` and `max_view_fraction >= viewed_fraction_required` |
| Unrestricted position editing via `update_lesson` | SIMPLIFY NOW | Avoid position gaps and collision bugs | Blocked position changes in `update_lesson`; isolated into dedicated `reorder_lessons` |

### E. Ponytails / deferred debt
- None. Complete business logic, anti-tampering bounds, safe 2-phase reordering, monotonic completion, and IDOR protection are verified and tested.

### F. Verification actually run and results
1. `mypy src/pwd301/services/lesson_service.py tests/unit/test_lesson_service.py`:
   ```
   Success: no issues found in 2 source files
   ```
2. `mypy src`:
   ```
   Success: no issues found in 43 source files
   ```
3. `ruff check src tests scripts`:
   ```
   All checks passed!
   ```
4. `ruff format --check src tests scripts`:
   ```
   61 files already formatted
   ```
5. `pytest tests/unit/test_lesson_service.py tests/security/test_lesson_idor.py tests/api/test_lesson_api.py -v`:
   ```
   ============================= 26 passed in 8.95s ==============================
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
   61 files already formatted
   Success: no issues found in 43 source files
   == Tests ==
   ============================ 183 passed in 46.21s =============================
   PWD301 verification PASS
   ```

### G. Remaining risks / next step
- Next scheduled task on roadmap: **TASK-008 — Student Enrollment Lifecycle & Period Management (`enrollment_service.py`)**.

---

## Historical Tasks

### TASK-006 — Course Management, Lifecycle & Ownership/Reassignment
**Status:** DONE  
*Triển khai tầng nghiệp vụ (`course_service.py`), Course State Machine (`DRAFT -> SUBMITTED_FOR_REVIEW -> APPROVED -> PUBLISHED -> ARCHIVED -> TRASH`), soft-delete an toàn với dependency checks, chuyển nhượng quyền sở hữu bởi Admin với Append-only AuditEvent, và hệ thống test toàn diện.*

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
