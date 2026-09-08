# CURRENT TASK

## TASK-008 — Student Enrollment Lifecycle, Capacity, Prerequisites & Re-Enrollment

**Status:** DONE

### 1. Goal
Triển khai toàn diện tầng nghiệp vụ quản lý đăng ký khóa học (`src/pwd301/services/enrollment_service.py`), quản lý chu kỳ học tập (`EnrollmentPeriod`), kiểm soát sĩ số khóa học chống race condition (`capacity`), thẩm định điều kiện tiên quyết và phòng chống chu kỳ đồ thị phụ thuộc (`CoursePrerequisite` DAG validation theo Algorithm 03), xử lý hủy khóa học (`LEFT`) với chính sách lưu trữ chi tiết 30 ngày, tái ghi danh (`REENROLLED`) tái sử dụng bản ghi `Enrollment` và mở `EnrollmentPeriod` mới, ghi nhận nhật ký sự kiện (`EnrollmentEvent`) và nhật ký kiểm toán hệ thống (`AuditEvent`), cùng toàn bộ route điều khiển (Web UI + REST API) và bộ kiểm thử tự động.

### 2. Source-of-truth documents
- `AGENTS.md` (Hợp đồng vận hành kỹ thuật, quy tắc bất biến, phân quyền và Source-of-Truth Hierarchy).
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/05_ENROLLMENT_AND_PREREQUISITES.md` (Đặc tả nghiệp vụ chu kỳ ghi danh, sức chứa và tiên quyết).
- `docs/system/PWD301_SYSTEM_SPECIFICATION/algorithms/03_PREREQUISITE_GRAPH_VALIDATION_ALGORITHM.md` (Giải thuật kiểm tra đồ thị phụ thuộc và phát hiện chu trình).
- `docs/system/PWD301_SYSTEM_SPECIFICATION/api/05_ENROLLMENT_PROGRESS_API.md` (Đặc tả REST API ghi danh, rút lui, tái ghi danh và quản lý môn tiên quyết).
- `docs/database/PWD301_DATABASE_ARCHITECTURE/05_DATA_DICTIONARY_COURSE.md` (Chi tiết bảng `enrollments`, `enrollment_periods`, `enrollment_events`, `course_prerequisites`).
- `src/pwd301/models/course.py` (Domain models: `Course`, `Enrollment`, `EnrollmentPeriod`, `EnrollmentEvent`, `CoursePrerequisite`).
- `src/pwd301/services/authorization_service.py` (`require_course_manager`, `can_manage_course`, `can_view_course`).

### 3. In scope
1. **Tầng Ngoại lệ (Domain Exceptions) — `src/pwd301/services/exceptions.py`:**
   - `EnrollmentError(ServiceError)`
   - `EnrollmentNotFoundError(ResourceNotFoundError, EnrollmentError)`
   - `EnrollmentCapacityExceededError(EnrollmentError)`
   - `EnrollmentPrerequisiteError(EnrollmentError)`
   - `EnrollmentStateViolationError(EnrollmentError)`
   - `PrerequisiteCycleError(EnrollmentError)`
   - `CourseNotAvailableError(EnrollmentError)`
2. **Tầng Dịch vụ (Service Layer) — `src/pwd301/services/enrollment_service.py`:**
   - `enroll_student(actor, course_id, student_user_id)`: Ghi danh khóa học cho sinh viên. Khóa dòng dữ liệu `Course` (`with_for_update`) để kiểm tra `capacity` chống race condition. Kiểm tra trạng thái khóa học phải là `PUBLISHED`. Kiểm tra thỏa mãn điều kiện tiên quyết. Idempotent nếu sinh viên đã có `Enrollment` trạng thái `ACTIVE`. Tạo `Enrollment` và `EnrollmentPeriod` (chu kỳ 1, trạng thái `ACTIVE`). Ghi `EnrollmentEvent` (`ENROLLED`) và `AuditEvent`.
   - `leave_course(actor, course_id, student_user_id, reason)`: Sinh viên rút khỏi khóa học. Chuyển trạng thái `Enrollment` thành `LEFT`. Đóng `EnrollmentPeriod` hiện tại (`ended_at = utc_now()`). Thiết lập `detail_retention_due_at = utc_now() + 30 days`. Không xóa cứng dữ liệu học tập. Ghi `EnrollmentEvent` (`LEFT`) và `AuditEvent`. Idempotent nếu đã ở trạng thái `LEFT`.
   - `re_enroll_student(actor, course_id, student_user_id)`: Tái ghi danh khóa học. Kiểm tra trạng thái hiện tại phải là `LEFT` hoặc `SUSPENDED`. Tái sử dụng bản ghi `Enrollment` (duy trì tính toàn vẹn 1 Enrollment duy nhất trên cặp `student_user_id, course_id`), chuyển trạng thái thành `REENROLLED` hoặc `ACTIVE`, tăng `period_no` và tạo bản ghi `EnrollmentPeriod` mới (trạng thái `ACTIVE`). Kiểm tra lại `capacity` và điều kiện tiên quyết. Ghi `EnrollmentEvent` (`REENROLLED`) và `AuditEvent`.
   - `check_prerequisites_met(student_user_id, course_id, session)`: Kiểm tra tất cả các khóa học tiên quyết bắt buộc đã được sinh viên hoàn thành (`is_completed = True`) hay chưa.
   - `add_course_prerequisite(actor, course_id, prerequisite_course_id)`: Thêm điều kiện tiên quyết. Kiểm tra quyền giảng viên quản lý khóa học. Kiểm tra khóa học không tự phụ thuộc chính nó (`course_id != prerequisite_course_id`). Kiểm tra chu trình đồ thị (Algorithm 03 DFS/Cycle Detection) — ngăn chặn triệt để chu trình trực tiếp hoặc gián tiếp. Ghi `AuditEvent`.
   - `remove_course_prerequisite(actor, course_id, prerequisite_course_id)`: Giảng viên xóa điều kiện tiên quyết. Kiểm tra quyền sở hữu. Ghi `AuditEvent`.
   - `get_course_prerequisites(course_id, session)`: Truy vấn danh sách môn tiên quyết của khóa học.
   - `get_student_enrollments(student_user_id, status_filter, page, per_page, session)`: Lấy danh sách khóa học sinh viên đã ghi danh (phân trang và lọc theo trạng thái).
   - `get_course_enrollments(actor, course_id, status_filter, page, per_page, session)`: Giảng viên/Admin xem danh sách sinh viên đã ghi danh vào khóa học quản lý.
3. **Tầng Blueprints & Route Handlers:**
   - **Student Blueprint (`src/pwd301/blueprints/student/routes.py`):**
     - `POST /student/courses/<course_id>/enroll`
     - `POST /student/courses/<course_id>/leave`
     - `POST /student/courses/<course_id>/re-enroll`
     - `GET /student/enrollments`
   - **Instructor Blueprint (`src/pwd301/blueprints/instructor/routes.py`):**
     - `GET /instructor/courses/<course_id>/students`
     - `GET /instructor/courses/<course_id>/prerequisites`
     - `POST /instructor/courses/<course_id>/prerequisites`
     - `DELETE /instructor/courses/<course_id>/prerequisites/<prereq_id>`
   - **REST API Blueprints (`api_courses` & `api_student`):**
     - `POST /api/courses/<course_id>/enroll`
     - `POST /api/courses/<course_id>/leave`
     - `POST /api/courses/<course_id>/re-enroll`
     - `GET /api/courses/<course_id>/prerequisites`
     - `POST /api/courses/<course_id>/prerequisites`
     - `DELETE /api/courses/<course_id>/prerequisites/<prereq_id>`
     - `GET /api/courses/<course_id>/enrollments`
     - `GET /api/student/enrollments` (`src/pwd301/blueprints/api_student/routes.py`)
4. **Error Handling & App Factory (`src/pwd301/__init__.py`):**
   - Đăng ký map Exception sang mã HTTP chuẩn:
     - `EnrollmentNotFoundError` -> 404 RESOURCE_NOT_FOUND
     - `EnrollmentCapacityExceededError` -> 409 CAPACITY_EXCEEDED
     - `EnrollmentPrerequisiteError` -> 409 PREREQUISITE_NOT_MET
     - `EnrollmentStateViolationError` -> 409 STATE_VIOLATION
     - `PrerequisiteCycleError` -> 409 PREREQUISITE_CYCLE
     - `CourseNotAvailableError` -> 400 COURSE_NOT_AVAILABLE
   - Đăng ký blueprint `api_student_bp` và miễn trừ CSRF cho REST API clients.

### 4. Out of scope
- Thanh toán / cổng thanh toán học phí (hệ thống hiện tại xử lý đăng ký trực tiếp).
- Đánh giá hoàn thành tổng thể khóa học và cấp chứng chỉ (`CourseCompletionSummary`) -> Đợi **TASK-009**.
- Quản lý bài tập, bài kiểm tra và chấm điểm (`assessment_service.py`) -> Đợi **TASK-010** & **TASK-011**.

### 5. Security & Invariants
- **Bất biến 1 (Single Logical Enrollment):** Một sinh viên chỉ có tối đa 1 bản ghi `Enrollment` duy nhất cho mỗi khóa học (`uq_enrollment_student_course`). Khi tái ghi danh (`re_enroll`), hệ thống cập nhật `Enrollment` hiện có và mở thêm `EnrollmentPeriod` mới với `period_no` tăng dần.
- **Bất biến 2 (Course Availability):** Chỉ khóa học đang ở trạng thái `PUBLISHED` và chưa bị xóa mềm mới được phép tiếp nhận đăng ký mới hoặc tái ghi danh.
- **Bất biến 3 (Capacity & Concurrency Guard):** Kiểm soát sĩ số khóa học với row lock `with_for_update` trên bản ghi `Course`, đếm số lượng sinh viên đang `ACTIVE` / `PENDING`. Khi đã đạt `capacity`, từ chối đăng ký mới (`EnrollmentCapacityExceededError`). Việc sinh viên rút khỏi khóa học (`LEFT`) giải phóng vị trí ngay lập tức.
- **Bất biến 4 (DAG Prerequisite Cycle Prevention):** Cấm tuyệt đối việc tạo chu trình phụ thuộc trong đồ thị môn tiên quyết (cả trực tiếp `A -> B -> A` và gián tiếp `A -> B -> C -> A`) theo Algorithm 03 (DFS).
- **Bất biến 5 (No Hard Delete & 30-Day Retention):** Khi sinh viên hủy môn (`leave`), hệ thống chuyển `status = 'LEFT'`, ghi nhận `detail_retention_due_at = utc_now() + 30 days`, giữ nguyên toàn bộ lịch sử học tập, nộp bài và tiến độ, không bao giờ xóa cứng dữ liệu.
- **Bất biến 6 (Append-Only Event & Audit):** Mọi thao tác ghi danh, rút lui, tái ghi danh, thêm/xóa môn tiên quyết đều được ghi vào `EnrollmentEvent` và `AuditEvent` trong cùng transaction.
- **Bất biến 7 (Resource-Based Authorization & IDOR Guard):** Giảng viên chỉ được quản lý môn tiên quyết và xem danh sách sinh viên của khóa học do mình trực tiếp phụ trách. Sinh viên chỉ được thao tác trên bản ghi ghi danh của chính mình.

### 6. Acceptance Criteria (Checklist)
- [x] `exceptions.py` bổ sung đầy đủ domain exceptions cho enrollment và prerequisites.
- [x] `enrollment_service.py` triển khai đầy đủ 9 hàm nghiệp vụ với docstrings và type hints chuẩn mực.
- [x] Đăng ký khóa học thành công tạo bản ghi `Enrollment` và `EnrollmentPeriod` chu kỳ 1.
- [x] Đăng ký bị từ chối khi khóa học chưa `PUBLISHED` hoặc đã bị xóa mềm (`CourseNotAvailableError`).
- [x] Đăng ký bị từ chối khi vượt quá sĩ số tối đa (`EnrollmentCapacityExceededError`).
- [x] Đăng ký bị từ chối khi sinh viên chưa hoàn thành môn tiên quyết bắt buộc (`EnrollmentPrerequisiteError`).
- [x] Thêm môn tiên quyết phát hiện và ngăn chặn chu trình trực tiếp và gián tiếp theo Algorithm 03 (`PrerequisiteCycleError`).
- [x] Thêm môn tiên quyết từ chối tự phụ thuộc chính nó.
- [x] Rút lui khỏi khóa học (`leave_course`) chuyển `status = 'LEFT'`, đóng `EnrollmentPeriod`, đặt thời hạn lưu trữ 30 ngày (`detail_retention_due_at`), giải phóng sĩ số và không xóa cứng dữ liệu.
- [x] Tái ghi danh (`re_enroll_student`) tái sử dụng bản ghi `Enrollment`, tăng `period_no` trên `EnrollmentPeriod` mới, kiểm tra lại sĩ số và môn tiên quyết.
- [x] Thao tác đăng ký và rút lui có tính idempotent an toàn.
- [x] IDOR: Giảng viên A không thể xem sinh viên hoặc thêm môn tiên quyết cho khóa học của Giảng viên B (HTTP 403).
- [x] IDOR: Sinh viên A không thể rút lui hay thao tác trên ghi danh của Sinh viên B (HTTP 403).
- [x] Mọi thay đổi trạng thái ghi danh đều phát sinh bản ghi append-only `EnrollmentEvent` và `AuditEvent`.
- [x] Toàn bộ route Web UI (`/student/...`, `/instructor/...`) và REST API (`/api/courses/...`, `/api/student/...`) hoạt động đầy đủ, hỗ trợ JSON serialization chuẩn.
- [x] Hệ thống kiểm thử toàn diện vượt qua 100% không có lỗi hồi quy (208/208 tests passed).

### 7. Verification commands
1. `mypy src/pwd301/services/enrollment_service.py tests/unit/test_enrollment_service.py` -> Success: no issues found in 2 source files.
2. `mypy src` -> Success: no issues found in 46 source files.
3. `ruff check src tests scripts` -> All checks passed!
4. `ruff format --check src tests scripts` -> 67 files already formatted.
5. `pytest tests/unit/test_enrollment_service.py tests/security/test_enrollment_idor.py tests/concurrency/test_enrollment_capacity.py tests/api/test_enrollment_api.py -v` -> 25 passed in 9.15s.
6. `./scripts/verify.ps1` -> 208 passed in 75.23s (100% PASS, 0 failures).

---

## Completion Report

### A. Scope and sources consulted
- Operating contract: `AGENTS.md` (quy tắc bất biến, phân quyền, Source-of-Truth Hierarchy).
- Enrollment & prerequisite business rules: `docs/system/PWD301_SYSTEM_SPECIFICATION/business/05_ENROLLMENT_AND_PREREQUISITES.md`.
- Prerequisite DAG validation algorithm: `docs/system/PWD301_SYSTEM_SPECIFICATION/algorithms/03_PREREQUISITE_GRAPH_VALIDATION_ALGORITHM.md`.
- Enrollment and progress REST API contracts: `docs/system/PWD301_SYSTEM_SPECIFICATION/api/05_ENROLLMENT_PROGRESS_API.md`.
- Course & enrollment data dictionary: `docs/database/PWD301_DATABASE_ARCHITECTURE/05_DATA_DICTIONARY_COURSE.md`.
- Non-negotiable invariants: `docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md`.
- Domain models: `src/pwd301/models/course.py`.
- Authorization service: `src/pwd301/services/authorization_service.py`.

### B. Reuse decisions
- Reused `Course`, `Enrollment`, `EnrollmentPeriod`, `EnrollmentEvent`, `CoursePrerequisite` models from `src/pwd301/models/course.py`.
- Reused `require_course_manager`, `can_manage_course`, `can_view_course`, `_resolve_course`, `_resolve_user` from `src/pwd301/services/authorization_service.py`.
- Reused `AuditEvent` model from `src/pwd301/models/notification_audit.py` for append-only audit logging.
- Reused `_format_error_response` and centralized error handling architecture in `src/pwd301/__init__.py`.
- Reused `student_required`, `instructor_required`, `get_authenticated_actor` decorators for route protection across session web and JWT REST environments.

### C. Per-file changes
- `src/pwd301/services/exceptions.py` (MODIFY): Added domain exceptions `EnrollmentError`, `EnrollmentNotFoundError`, `EnrollmentCapacityExceededError`, `EnrollmentPrerequisiteError`, `EnrollmentStateViolationError`, `PrerequisiteCycleError`, `CourseNotAvailableError`.
- `src/pwd301/services/enrollment_service.py` (NEW): Implemented complete enrollment service layer: `enroll_student`, `leave_course`, `re_enroll_student`, `check_prerequisites_met`, `add_course_prerequisite`, `remove_course_prerequisite`, `get_course_prerequisites`, `get_student_enrollments`, `get_course_enrollments`, DAG cycle detection (Algorithm 03 DFS), and append-only event/audit logging.
- `src/pwd301/services/__init__.py` (MODIFY): Exported all enrollment service functions and domain exceptions.
- `src/pwd301/__init__.py` (MODIFY): Registered error handlers for enrollment domain exceptions (mapping to 400 COURSE_NOT_AVAILABLE, 404 RESOURCE_NOT_FOUND, 409 CAPACITY_EXCEEDED, 409 PREREQUISITE_NOT_MET, 409 PREREQUISITE_CYCLE, 409 STATE_VIOLATION), registered `api_student_bp`, and exempted it from CSRF.
- `src/pwd301/blueprints/student/routes.py` (MODIFY): Added student enrollment routes: `POST /student/courses/<course_id>/enroll`, `POST /student/courses/<course_id>/leave`, `POST /student/courses/<course_id>/re-enroll`, and `GET /student/enrollments` with pagination and status filtering.
- `src/pwd301/blueprints/instructor/routes.py` (MODIFY): Added instructor routes: `GET /instructor/courses/<course_id>/students` (paginated roster), `GET /instructor/courses/<course_id>/prerequisites`, `POST /instructor/courses/<course_id>/prerequisites`, and `DELETE /instructor/courses/<course_id>/prerequisites/<prereq_id>`.
- `src/pwd301/blueprints/api_courses/routes.py` (MODIFY): Added REST API endpoints: `POST /api/courses/<id>/enroll`, `POST /api/courses/<id>/leave`, `POST /api/courses/<id>/re-enroll`, `GET/POST/DELETE /api/courses/<id>/prerequisites`, and `GET /api/courses/<id>/enrollments`.
- `src/pwd301/blueprints/api_student/__init__.py` (NEW): Initialized `api_student` blueprint with `/api/student` url prefix.
- `src/pwd301/blueprints/api_student/routes.py` (NEW): Implemented REST API endpoint `GET /api/student/enrollments` with pagination and status filtering.
- `tests/unit/test_enrollment_service.py` (NEW): Implemented 12 comprehensive unit tests covering standard enrollment, capacity limits, uncompleted prerequisite rejection, completed prerequisite acceptance, self-prerequisite rejection, direct and indirect DAG cycle prevention (Algorithm 03), soft withdrawal with 30-day retention and slot freeing, idempotent leave, re-enrollment period increment, and append-only event logging.
- `tests/security/test_enrollment_idor.py` (NEW): Implemented 7 security and IDOR tests verifying cross-student leave/re-enroll denial, cross-instructor student roster viewing denial, cross-instructor prerequisite addition/deletion denial, unauthenticated access denial, and student prerequisite tampering denial.
- `tests/concurrency/test_enrollment_capacity.py` (NEW): Implemented 3 concurrency and capacity tests verifying sequential capacity exhaustion, strict rejection on overflow, slot reclamation upon student leave, and re-enrollment capacity enforcement.
- `tests/api/test_enrollment_api.py` (NEW): Implemented 3 REST API integration tests for enrollment lifecycle, prerequisite management, and student enrollments query.
- `tasks/CURRENT.md` (MODIFY): Recorded TASK-008 completion and moved TASK-007 to Historical Tasks.

### D. Deletion and simplification list
| Candidate | Classification | Reason | Action |
|---|---|---|---|
| Hard SQL DELETE on `enrollments` or `enrollment_periods` | REMOVE NOW | Invariant DELETE-001 & DATA_DICTIONARY prohibit destroying learning history | Implemented application-level soft leave (`status='LEFT'`, `detail_retention_due_at = utc_now() + 30 days`) |
| Creating duplicate `Enrollment` rows on re-enroll | REMOVE NOW | Violates database unique constraint `uq_enrollment_student_course` | Reused original `Enrollment` record and incremented `period_no` on new `EnrollmentPeriod` |
| Client-supplied enrollment status updates | REMOVE NOW | Invariant ENROLL-001 & RBAC require server-authoritative state transitions | State machine strictly controlled via explicit service methods (`enroll_student`, `leave_course`, `re_enroll_student`) |
| Client-side prerequisite cycle detection | SIMPLIFY NOW | Security and graph integrity must be verified on backend | Enforced server-side DFS cycle detection (Algorithm 03) inside database transaction |

### E. Ponytails / deferred debt
- None. Complete business logic, concurrency guards, DAG cycle detection, 30-day retention policy, IDOR protection, and append-only audit/event logs are verified and tested.

### F. Verification actually run and results
1. `mypy src/pwd301/services/enrollment_service.py tests/unit/test_enrollment_service.py`:
   ```
   Success: no issues found in 2 source files
   ```
2. `mypy src`:
   ```
   Success: no issues found in 46 source files
   ```
3. `ruff check src tests scripts`:
   ```
   All checks passed!
   ```
4. `ruff format --check src tests scripts`:
   ```
   73 files already formatted
   ```
5. `pytest tests/unit/test_enrollment_service.py tests/security/test_enrollment_idor.py tests/concurrency/test_enrollment_capacity.py tests/api/test_enrollment_api.py -v`:
   ```
   ============================= 25 passed in 9.15s ==============================
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
   73 files already formatted
   Success: no issues found in 46 source files
   == Tests ==
   ======================= 208 passed in 72.25s (0:01:12) ========================
   PWD301 verification PASS
   ```

### G. Remaining risks / next step
- Next scheduled task on roadmap: **TASK-009 — Course Completion Summary, Metrics & Aggregate Progress Tracking (`completion_service.py`)**.

---

## Historical Tasks

### TASK-007 — Lesson Management, Reordering & Completion Tracking
**Status:** DONE  
*Triển khai toàn diện tầng nghiệp vụ (`lesson_service.py`), các ngoại lệ miền (`exceptions.py`), bộ điều khiển route (Web UI & REST API), giải thuật ghi nhận tiến độ (`02_LESSON_COMPLETION_ALGORITHM.md`) và cơ chế tái sắp xếp thứ tự bài học (Lesson Reordering) an toàn với kỹ thuật temporary positive offset `+ 1_000_000`. Tuân thủ nghiêm ngặt ma trận phân quyền (RBAC), phòng chống lỗ hổng IDOR, và ghi nhận Append-only Audit Log.*

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
