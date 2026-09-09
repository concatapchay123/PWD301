# CURRENT TASK

## TASK-009 — Course Progress Engine, Completion Rules & Durable Completion Summaries

**Status:** DONE

### 1. Goal
Triển khai toàn diện Tầng dịch vụ tính toán tiến độ khóa học và động cơ thẩm định hoàn thành (`src/pwd301/services/completion_service.py`), bao gồm:
1. **Thuật toán tính toán tiến độ khóa học (Algorithm 01)** dựa trên tỷ lệ bài học bắt buộc đã hoàn thành trong chu kỳ ghi danh hiện tại (`EnrollmentPeriod`).
2. **Cấu hình tiêu chí hoàn thành khóa học (`CourseCompletionRule`)**: Quản trị cấu hình hoàn thành (bắt buộc học hết bài học, hoàn thành bài kiểm tra, ngưỡng % tiến độ tối thiểu).
3. **Động cơ thẩm định và cấp chứng nhận hoàn thành (`evaluate_course_completion`)**: Đánh giá điều kiện, cập nhật trạng thái `Enrollment.status = 'COMPLETED'`, `EnrollmentPeriod.status = 'COMPLETED'`, khởi tạo/cập nhật bản ghi bền vững `CourseCompletionSummary` (`ever_completed=True`, `prerequisite_eligible=True`), ghi nhận sự kiện `EnrollmentEvent` (`COMPLETED`) và `AuditEvent` (`COURSE_COMPLETED`).
4. **Bảo toàn điều kiện tiên quyết bền vững (Durable Prerequisite Eligibility)**: Cập nhật `check_prerequisites_met` trong `enrollment_service.py` đọc từ `CourseCompletionSummary.prerequisite_eligible.is_(True)` thay vì chỉ đọc `Enrollment.status == 'COMPLETED'`.
5. **Tích hợp Hook tự động thẩm định**: Kết nối tự động trong `lesson_service.py` (`record_lesson_progress`) kích hoạt `evaluate_course_completion` khi bài học hoàn thành giúp tiến độ đạt điều kiện.
6. **Web UI & REST API Endpoints**: Đầy đủ route cho Giảng viên (xem/cập nhật tiêu chí hoàn thành) và Học viên (truy vấn tiến độ và chứng nhận hoàn thành), tuân thủ kiểm soát IDOR và ADR-002 che giấu `BIGINT PK`.

### 2. Source-of-truth documents
- `AGENTS.md` (Hợp đồng vận hành kỹ thuật, quy tắc bất biến, phân quyền và Source-of-Truth Hierarchy).
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/01_BUSINESS_RULE_CATALOG.md` (Quy tắc nghiệp vụ hoàn thành khóa học và điều kiện tiên quyết).
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/05_ENROLLMENT_AND_PREREQUISITES.md` (Đặc tả nghiệp vụ chu kỳ ghi danh, điều kiện tiên quyết bền vững).
- `docs/system/PWD301_SYSTEM_SPECIFICATION/algorithms/01_COURSE_PROGRESS_CALCULATION_ALGORITHM.md` (Giải thuật tính toán tiến độ khóa học).
- `docs/system/PWD301_SYSTEM_SPECIFICATION/api/05_ENROLLMENT_PROGRESS_API.md` (Đặc tả REST API tiến độ, cấu hình tiêu chí và hoàn thành).
- `docs/database/PWD301_DATABASE_ARCHITECTURE/05_DATA_DICTIONARY_COURSE.md` (Chi tiết bảng `course_completion_rules`, `course_completion_summaries`, `enrollments`, `enrollment_periods`).
- `docs/database/PWD301_DATABASE_ARCHITECTURE/12_STATE_MACHINES.md` (Máy trạng thái Enrollment và EnrollmentPeriod).
- `docs/database/PWD301_DATABASE_ARCHITECTURE/16_CONCURRENCY_AND_TRANSACTIONS.md` (Xử lý giao dịch và concurrency khi thẩm định hoàn thành).
- `src/pwd301/models/course.py` (Domain models: `CourseCompletionRule`, `CourseCompletionSummary`, `Enrollment`, `EnrollmentPeriod`, `LessonProgress`).

### 3. In scope
1. **Tầng Ngoại lệ (Domain Exceptions) — `src/pwd301/services/exceptions.py`:**
   - `ValidationError` (trả về 400 Bad Request cho các lỗi dữ liệu đầu vào không hợp lệ)
   - `CompletionRuleError(ServiceError)`
   - `CompletionRuleNotFoundError(ResourceNotFoundError, CompletionRuleError)`
   - `CompletionRuleValidationError(CompletionRuleError)`
2. **Tầng Dịch vụ (Service Layer) — `src/pwd301/services/completion_service.py`:**
   - `get_or_create_default_completion_rule(course_id, session)`: Đọc hoặc khởi tạo quy tắc mặc định (100% progress, require_all_required_lessons=True).
   - `set_course_completion_rule(actor, course_id, payload, session)`: Giảng viên phụ trách cấu hình tiêu chí hoàn thành, xác thực dữ liệu chặt chẽ và ghi append-only `AuditEvent`.
   - `calculate_course_progress(enrollment_id, session)`: Triển khai chuẩn xác Algorithm 01, tổng hợp tiến độ bài học trong `EnrollmentPeriod` hiện tại, cập nhật cache `enrollment.current_progress_percent`.
   - `evaluate_course_completion(enrollment_id, session)`: Thẩm định hoàn thành khóa học, cập nhật trạng thái `COMPLETED` cho enrollment và period, upsert bản ghi bền vững `CourseCompletionSummary`, ghi append-only `EnrollmentEvent` và `AuditEvent`, bảo đảm tính Idempotent tuyệt đối.
   - `get_course_completion_summary(actor, course_id, student_id, session)`: Truy vấn chứng nhận hoàn thành an toàn IDOR (học viên chỉ xem của chính mình, giảng viên xem của học viên trong khóa phụ trách, admin xem tất cả).
3. **Tích hợp Hooks & Prerequisite Engine:**
   - `lesson_service.py`: Tích hợp tự động gọi `calculate_course_progress` và `evaluate_course_completion` khi hoàn thành bài học, cho phép học viên đã hoàn thành tiếp tục tương tác bài học mà không bị chặn 403.
   - `enrollment_service.py`: Cập nhật `check_prerequisites_met` đọc từ `CourseCompletionSummary.prerequisite_eligible.is_(True)`, bảo đảm học viên dù sau này rời môn hoặc tái ghi danh vẫn giữ quyền tiên quyết vĩnh viễn.
4. **Blueprints & Route Handlers:**
   - **Instructor Blueprint (`src/pwd301/blueprints/instructor/routes.py`):**
     - `GET /instructor/courses/<course_id>/completion-rules`
     - `POST/PUT /instructor/courses/<course_id>/completion-rules`
   - **Student Blueprint (`src/pwd301/blueprints/student/routes.py`):**
     - `GET /student/courses/<course_id>/completion`
   - **REST API Blueprints (`api_courses` & `api_student`):**
     - `GET /api/courses/<course_id>/completion-rules`
     - `PUT /api/courses/<course_id>/completion-rules`
     - `GET /api/courses/<course_id>/progress`
     - `GET /api/student/courses/<course_id>/completion`
5. **Kiểm thử tự động toàn diện:**
   - Unit tests (`tests/unit/test_completion_service.py`): 14 test cases.
   - Security / IDOR tests (`tests/security/test_completion_idor.py`): 4 test cases.
   - REST API integration tests (`tests/api/test_completion_api.py`): 3 test cases.
   - Bảo toàn 100% test suite sẵn có (234/234 tests pass).

### 4. Out of scope
- Quản lý bài tập, ngân hàng câu hỏi, bài kiểm tra và chấm điểm tự động (`assessment_service.py`) -> Đợi **TASK-010** & **TASK-011**.
- Tích hợp mô hình AI sinh bài kiểm tra và trợ giảng RAG -> Đợi **TASK-012** & **TASK-013**.

### 5. Security & Invariants
- **Bất biến 1 (Server-Authoritative Progress):** Tuyệt đối không cho phép client gửi trực tiếp % tiến độ hoặc cờ hoàn thành; toàn bộ tiến độ và trạng thái hoàn thành do backend tính toán từ bằng chứng học tập thực tế.
- **Bất biến 2 (ADR-002 Internal PK Masking):** Tuyệt đối không để lộ khóa chính nội bộ `BIGINT` (`id`, `student_user_id`, `course_id`) ra Web/REST JSON; sử dụng `public_id` (UUIDv4/UUIDv7) và các thuộc tính nghiệp vụ.
- **Bất biến 3 (Durable Prerequisite Eligibility):** Bản ghi `CourseCompletionSummary` là vĩnh viễn; cờ `prerequisite_eligible` và `ever_completed` không bao giờ bị xóa hoặc hạ cờ khi học viên rời khóa học (`LEFT`), tái ghi danh (`REENROLLED`) hay khi giảng viên nâng tiêu chí hoàn thành sau đó.
- **Bất biến 4 (Evaluation Idempotency):** Gọi `evaluate_course_completion` nhiều lần trên một enrollment đã hoàn thành không phát sinh trùng lặp sự kiện `EnrollmentEvent` hay `AuditEvent`.
- **Bất biến 5 (IDOR & Object-Level Authorization):** Giảng viên chỉ được xem và cấu hình tiêu chí cho khóa học mình quản lý. Học viên chỉ được xem chứng nhận tiến độ và hoàn thành của bản thân.
- **Bất biến 6 (Append-Only Event & Audit Log):** Mọi sự kiện hoàn thành khóa học và cập nhật quy tắc hoàn thành đều được ghi nhận vào `EnrollmentEvent` và `AuditEvent` trong cùng một transaction.

### 6. Acceptance Criteria (Checklist)
- [x] `exceptions.py` bổ sung đầy đủ domain exceptions `CompletionRuleError`, `CompletionRuleNotFoundError`, `CompletionRuleValidationError`, `ValidationError`.
- [x] `completion_service.py` triển khai đầy đủ `calculate_course_progress` (Algorithm 01), `get_or_create_default_completion_rule`, `set_course_completion_rule`, `evaluate_course_completion`, `get_course_completion_summary`.
- [x] `lesson_service.py` tích hợp tự động thẩm định hoàn thành khi hoàn tất bài học và cho phép học viên đã hoàn thành tiếp tục ôn tập/tương tác.
- [x] `enrollment_service.py` cập nhật `check_prerequisites_met` dựa trên `CourseCompletionSummary.prerequisite_eligible.is_(True)` bền vững.
- [x] Cấu hình tiêu chí kiểm tra dữ liệu chặt chẽ (ngưỡng 0-100%, ghi AuditEvent với before/after snapshot).
- [x] Thẩm định hoàn thành tạo bản ghi bền vững `CourseCompletionSummary` và ghi append-only `EnrollmentEvent('COMPLETED')`, `AuditEvent('COURSE_COMPLETED')`.
- [x] Toàn bộ route Web UI (`/instructor/...`, `/student/...`) và REST API (`/api/courses/...`, `/api/student/...`) hoạt động chuẩn xác, tuân thủ ADR-002.
- [x] Bộ kiểm thử bảo mật IDOR ngăn chặn triệt để truy cập chéo giữa giảng viên và giữa học viên.
- [x] Hệ thống kiểm thử toàn diện vượt qua 100% không có lỗi hồi quy (234/234 tests passed).

### 7. Verification commands
1. `mypy src` -> Success: no issues found in 47 source files.
2. `ruff check src tests scripts` -> All checks passed!
3. `ruff format --check src tests scripts` -> 77 files already formatted.
4. `pytest tests/unit/test_completion_service.py tests/security/test_completion_idor.py tests/api/test_completion_api.py -v` -> 21 passed.
5. `./scripts/verify.ps1` -> 234 passed in 99.22s (100% PASS, 0 failures).

---

## Completion Report

### A. Scope and sources consulted
- Operating contract: `AGENTS.md` (quy tắc bất biến, phân quyền, Source-of-Truth Hierarchy).
- Course completion & prerequisite business rules: `docs/system/PWD301_SYSTEM_SPECIFICATION/business/01_BUSINESS_RULE_CATALOG.md` & `05_ENROLLMENT_AND_PREREQUISITES.md`.
- Progress calculation algorithm: `docs/system/PWD301_SYSTEM_SPECIFICATION/algorithms/01_COURSE_PROGRESS_CALCULATION_ALGORITHM.md`.
- Course completion & progress REST API contracts: `docs/system/PWD301_SYSTEM_SPECIFICATION/api/05_ENROLLMENT_PROGRESS_API.md`.
- Course data dictionary & schema constraints: `docs/database/PWD301_DATABASE_ARCHITECTURE/05_DATA_DICTIONARY_COURSE.md`.
- State machines & concurrency guidelines: `docs/database/PWD301_DATABASE_ARCHITECTURE/12_STATE_MACHINES.md` & `16_CONCURRENCY_AND_TRANSACTIONS.md`.
- Domain models: `src/pwd301/models/course.py`.
- Authorization service: `src/pwd301/services/authorization_service.py`.

### B. Reuse decisions
- Reused `CourseCompletionRule`, `CourseCompletionSummary`, `Enrollment`, `EnrollmentPeriod`, `Lesson`, `LessonProgress` models from `src/pwd301/models/course.py`.
- Reused `require_course_manager`, `can_manage_course`, `can_view_course`, `_resolve_course`, `_resolve_user` from `src/pwd301/services/authorization_service.py`.
- Reused `AuditEvent` model from `src/pwd301/models/notification_audit.py` for append-only audit logging with before/after state snapshots.
- Reused `_format_error_response` and centralized error handling architecture in `src/pwd301/__init__.py`.
- Reused `student_required`, `instructor_required`, `get_authenticated_actor` decorators for route protection across session web and JWT REST environments.

### C. Per-file changes
- `src/pwd301/services/exceptions.py` (MODIFY): Added domain exceptions `ValidationError`, `CompletionRuleError`, `CompletionRuleNotFoundError`, `CompletionRuleValidationError`.
- `src/pwd301/__init__.py` (MODIFY): Registered error handlers mapping `CompletionRuleNotFoundError` to 404 RESOURCE_NOT_FOUND, and `CompletionRuleValidationError`, `ValidationError` to 400 BAD_REQUEST.
- `src/pwd301/services/completion_service.py` (NEW): Implemented complete course progress and completion engine (`get_or_create_default_completion_rule`, `set_course_completion_rule`, `calculate_course_progress` Algorithm 01, `evaluate_course_completion`, `get_course_completion_summary`, IDOR resolution, append-only events, and durable summary upsert).
- `src/pwd301/services/__init__.py` (MODIFY): Exported all completion service functions and domain exceptions.
- `src/pwd301/services/lesson_service.py` (MODIFY): Connected lesson progress calculation to `calculate_course_progress`, added automatic course completion evaluation hook when lesson is completed, and allowed active or completed students to record progress.
- `src/pwd301/services/enrollment_service.py` (MODIFY): Updated `check_prerequisites_met` to strictly verify `CourseCompletionSummary.prerequisite_eligible.is_(True)` and restored strict `status == 'ACTIVE'` check for `leave_course`.
- `src/pwd301/services/course_service.py` (MODIFY): Initialized default `CourseCompletionRule` with `minimum_progress_percent=Decimal("100.00")` on course creation.
- `src/pwd301/blueprints/instructor/routes.py` (MODIFY): Implemented Web UI endpoints `GET /instructor/courses/<course_id>/completion-rules` and `POST/PUT /instructor/courses/<course_id>/completion-rules`.
- `src/pwd301/blueprints/student/routes.py` (MODIFY): Implemented Web UI endpoint `GET /student/courses/<course_id>/completion`.
- `src/pwd301/blueprints/api_courses/routes.py` (MODIFY): Implemented REST API endpoints `GET /api/courses/<course_id>/completion-rules`, `PUT /api/courses/<course_id>/completion-rules`, and `GET /api/courses/<course_id>/progress`.
- `src/pwd301/blueprints/api_student/routes.py` (MODIFY): Implemented REST API endpoint `GET /api/student/courses/<course_id>/completion`.
- `tests/unit/test_completion_service.py` (NEW): Implemented 14 comprehensive unit tests for Algorithm 01, rule configuration, audit logging, completion evaluation, idempotency, durable prerequisite eligibility across re-enrollment and leave, and Web UI routes.
- `tests/security/test_completion_idor.py` (NEW): Implemented 4 security tests verifying cross-instructor rule mutation denial, cross-student completion status leak denial, student rule tampering denial, and unauthenticated access denial.
- `tests/api/test_completion_api.py` (NEW): Implemented 3 REST API tests for rule configuration via PUT, course progress query, student completion summary query, and ADR-002 BIGINT masking verification.
- `tasks/CURRENT.md` (MODIFY): Updated with TASK-009 completion report and promoted TASK-008 to Historical Tasks.

### D. Deletion and simplification list
| Candidate | Classification | Reason | Action |
|---|---|---|---|
| Inline progress calculation in `lesson_service.py` | REMOVE NOW | Inconsistent duplicated logic with Algorithm 01 | Replaced with authoritative call to `calculate_course_progress` in `completion_service.py` |
| Client-supplied course completion status | REMOVE NOW | Invariant: progress and completion are strictly server-authoritative | Enforced server evaluation via `evaluate_course_completion` |
| Resetting `prerequisite_eligible` on student leave | REMOVE NOW | Invariant COURSE-010: completion proof is durable and irrevocable | Verified and preserved `CourseCompletionSummary.prerequisite_eligible` across withdrawal and re-enrollment |
| `BIGINT PK` in completion responses | REMOVE NOW | ADR-002: no internal database BIGINT IDs in public payloads | Mapped all JSON responses to public UUIDs (`course_id`, `student_id`, `rule_id`, `summary_id`) |
| Duplicate `EnrollmentEvent('COMPLETED')` on repeated evaluation | REMOVE NOW | State machine and event logs must be idempotent | Short-circuited evaluation if enrollment already `COMPLETED` |

### E. Ponytails / deferred debt
- None. Full progress engine, completion rule CRUD with AuditEvents, durable summaries, prerequisite integration, Web/REST routes, IDOR protection, and 100% regression testing are fully verified.

### F. Verification actually run and results
1. `mypy src`:
   ```
   Success: no issues found in 47 source files
   ```
2. `ruff check src tests scripts`:
   ```
   All checks passed!
   ```
3. `ruff format --check src tests scripts`:
   ```
   77 files already formatted
   ```
4. `pytest tests/unit/test_completion_service.py tests/security/test_completion_idor.py tests/api/test_completion_api.py -v`:
   ```
   ============================= 21 passed in 7.82s =============================
   ```
5. `./scripts/verify.ps1`:
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
   77 files already formatted
   Success: no issues found in 47 source files
   == Tests ==
   ======================= 234 passed in 99.22s (0:01:39) ========================
   PWD301 verification PASS
   ```

### G. Remaining risks / next step
- Next scheduled task on roadmap: **TASK-010 — Assessment Authoring, Question Banking & Lifecycle Management (`assessment_service.py`)**.

---

## Historical Tasks

### TASK-008 — Student Enrollment Lifecycle, Capacity, Prerequisites & Re-Enrollment
**Status:** DONE  
*Triển khai toàn diện tầng nghiệp vụ quản lý đăng ký khóa học (`enrollment_service.py`), quản lý chu kỳ học tập (`EnrollmentPeriod`), kiểm soát sĩ số chống race condition (`capacity`), thẩm định điều kiện tiên quyết và phát hiện chu trình đồ thị (Algorithm 03 DFS), xử lý rút lui (`LEFT`) với chính sách lưu trữ chi tiết 30 ngày, tái ghi danh (`re_enroll_student`), tự động chuyển đổi tái ghi danh (Seamless Re-enrollment), bảo đảm tính idempotent, che giấu `BIGINT PK` theo ADR-002, ghi nhận `EnrollmentEvent` và `AuditEvent` append-only, cùng toàn bộ route Web UI, REST API và bộ test tự động.*

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
