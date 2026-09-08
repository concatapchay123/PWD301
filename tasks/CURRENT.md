# CURRENT TASK

## TASK-005 — Authorization & Role-Based Access Control (RBAC & Resource Ownership)

**Status:** DONE

### 1. Goal
Xây dựng hệ thống phân quyền (Authorization) toàn diện cho dự án PWD301 kết hợp giữa Role-Based Access Control (RBAC) để kiểm soát các nhóm tính năng, và Resource/Object-level Authorization để kiểm soát quyền sở hữu dữ liệu (Ownership) nhằm ngăn chặn tuyệt đối các lỗ hổng IDOR (Insecure Direct Object Reference).

### 2. Source-of-truth documents
- `docs/system/PWD301_SYSTEM_SPECIFICATION/authorization/01_RBAC_MODEL.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/authorization/02_PERMISSION_MATRIX.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/authorization/03_RESOURCE_AUTHORIZATION_RULES.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/authorization/04_ADMIN_PERMISSION_RULES.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/authorization/05_IDOR_PREVENTION.md`
- `AGENTS.md` (Role blueprints, session vs JWT auth, invariants, verification rules)

### 3. In scope
1. **RBAC Model & Role Hierarchy (`User` model & `user_service.py`):**
   - Hỗ trợ mô hình tích lũy quyền (Cumulative Capability): `{"STUDENT"}`, `{"STUDENT", "INSTRUCTOR"}`, `{"STUDENT", "INSTRUCTOR", "ADMIN"}`.
   - Thêm phương thức kiểm tra role: `has_role`, `has_any_role`, `has_all_roles`, `is_admin`, `is_instructor`, `is_student`.
   - `AnonymousUser` an toàn trả về `False` cho mọi kiểm tra role.
   - Gán/hủy role với kiểm soát đóng bao tích lũy (`assign_role_to_user`, `remove_role_from_user`), ghi nhật ký append-only vào `AuditEvent`, tăng `auth_version` làm mới token/session.
2. **Authorization Service (`src/pwd301/services/authorization_service.py`):**
   - Bộ giải quyết ngữ cảnh actor (`get_authenticated_actor`): Hỗ trợ đồng bộ cả Web Session (Flask-Login `current_user`) và REST API JWT Bearer token (`request.headers` Authoritative resolution & `g.current_user`).
   - Route decorators: `@require_roles(*role_codes)`, `@admin_required`, `@instructor_required`, `@student_required`. Xử lý phân biệt request Web (chuyển hướng login hoặc abort 403) và REST API/JSON (trả về JSON 401 hoặc 403).
   - Resource-level authorization & IDOR prevention helpers: `can_view_course`, `can_manage_course`, `can_access_student_data`, `can_manage_lesson`, `can_manage_question`, `can_manage_assessment`, `can_access_attempt`, `can_submit_attempt`, `can_grade_attempt`.
   - Assertion wrappers: `require_course_manager`, `require_student_data_access`, `require_attempt_access`, `require_attempt_submission_owner`.
3. **Exceptions & HTTP 403 Error Handling:**
   - Định nghĩa `ForbiddenError`, `ResourceNotFoundError`, `InvalidRoleAssignmentError`, `AuthorizationError`.
   - Template giao diện chuẩn `src/pwd301/templates/errors/403.html` tương thích thiết kế `frontend-preview/`.
   - Đăng ký error handlers tập trung tại application factory (`src/pwd301/__init__.py`).
4. **Role-Based Blueprints:**
   - Blueprint `student` (`/student`): Dashboard và xem tiến độ học tập khóa học theo đúng quyền sở hữu của học viên.
   - Blueprint `instructor` (`/instructor`): Dashboard quản lý khóa học, trang quản lý chi tiết khóa học sở hữu (`/courses/<id>/manage`), và xem chi tiết học viên trong khóa học (`/courses/<id>/students/<student_id>`).
   - Blueprint `admin` (`/admin`): Dashboard tổng quan hệ thống và endpoint phân quyền tài khoản người dùng (`/users/<user_id>/roles`).
5. **Jinja Context Processors:**
   - Expose các hàm kiểm tra quyền vào Jinja templates: `has_role`, `has_any_role`, `is_admin`, `is_instructor`, `is_student`, `can_manage_course`, `user_roles`.
6. **Testing & Security Verification:**
   - Unit tests: `tests/unit/test_authorization_service.py` (10 tests, 22 assertions bao phủ đầy đủ logic).
   - Security negative & IDOR integration tests: `tests/security/test_rbac_and_idor.py` (12 tests).

### 4. Out of scope
- Course content editing UI / rich text editor (Scheduled for TASK-007).
- Real-time Assessment taking engine & autosave WebSockets (Scheduled for TASK-012/013).
- Automated AI grading / RAG ingestion (Scheduled for TASK-017/018).

### 5. Security & Invariants
- **Bất biến 1:** Fail-closed authorization — Mọi kiểm tra quyền mặc định từ chối (`return False` hoặc ném `ForbiddenError`) nếu thông tin actor không xác định hoặc không hợp lệ.
- **Bất biến 2:** IDOR Prevention — Không bao giờ tin cậy ID do client gửi lên; luôn nạp thực thể từ CSDL và kiểm tra quyền sở hữu tương ứng.
- **Bất biến 3:** Giảng viên chỉ được quản lý khóa học và xem dữ liệu học viên của các khóa học mà mình đang trực tiếp phụ trách (`owner_instructor_id == actor.id`).
- **Bất biến 4:** Nộp bài kiểm tra (`can_submit_attempt`) là bất biến "Own only": Chỉ chính sinh viên sở hữu bài làm (`attempt.student_user_id == actor.id`) mới có quyền nộp bài; Giảng viên và Quản trị viên bị cấm tuyệt đối nộp bài thay sinh viên.
- **Bất biến 5:** Quản trị viên (Admin) có quyền quản trị toàn hệ thống theo `04_ADMIN_PERMISSION_RULES.md`, các thao tác nhạy cảm yêu cầu lý do/nhật ký kiểm toán (`AuditEvent`).
- **Bất biến 6:** Bearer token trong header `Authorization` có tính chất server-authoritative cho REST API, không bị rò rỉ hoặc nhầm lẫn với session cookies của Web UI.

### 6. Acceptance Criteria (Checklist)
- [x] Decorator `@require_roles` từ chối người dùng chưa xác thực (401 cho API, chuyển hướng Login cho Web UI).
- [x] Decorator `@require_roles` từ chối người dùng không đủ quyền (403 Forbidden dạng JSON cho API, hiển thị `403.html` cho Web UI).
- [x] Giảng viên A truy cập vào trang quản lý khóa học của Giảng viên B bị chặn với HTTP 403 (IDOR test).
- [x] Giảng viên A truy vấn dữ liệu học viên của một khóa học mà mình không quản lý bị chặn với HTTP 403 (IDOR test).
- [x] Học viên chỉ có thể xem tiến độ các khóa học mà mình thực sự đăng ký.
- [x] Bất biến "Own only" trong việc nộp bài thi được bảo vệ tuyệt đối.
- [x] REST API xác thực qua Bearer JWT tuân thủ đồng nhất 100% các quy tắc RBAC & IDOR như Web UI.
- [x] Toàn bộ test suite (134 tests) vượt qua kiểm thử thành công, 0 lỗi linter/formatting/typing.

### 7. Verification commands
1. `pytest tests/unit/test_authorization_service.py tests/security/test_rbac_and_idor.py -v` (22 passed).
2. `mypy src/` (Success: no issues found in 37 source files).
3. `ruff check src tests` (All checks passed).
4. `ruff format --check src tests` (51 files already formatted).
5. `./scripts/verify.ps1` (Toàn bộ pipeline: repository contract, lint, format, types, 134 tests pass).

---

## Completion Report

### A. Scope and sources consulted
- Operating contract: `AGENTS.md`
- RBAC cumulative model: `docs/system/PWD301_SYSTEM_SPECIFICATION/authorization/01_RBAC_MODEL.md`
- Permission matrix: `docs/system/PWD301_SYSTEM_SPECIFICATION/authorization/02_PERMISSION_MATRIX.md`
- Resource authorization rules: `docs/system/PWD301_SYSTEM_SPECIFICATION/authorization/03_RESOURCE_AUTHORIZATION_RULES.md`
- Admin permission rules: `docs/system/PWD301_SYSTEM_SPECIFICATION/authorization/04_ADMIN_PERMISSION_RULES.md`
- IDOR prevention specification: `docs/system/PWD301_SYSTEM_SPECIFICATION/authorization/05_IDOR_PREVENTION.md`
- Frontend reference: `frontend-preview/` (`views/`, `app.css`)

### B. Reuse decisions
- Tái sử dụng quan hệ `User.roles` (`secondary="user_roles"`) và các model có sẵn trong `src/pwd301/models/`.
- Tái sử dụng `AuditEvent` từ `src/pwd301/models/notification_audit.py` để ghi log kiểm toán phân quyền.
- Tái sử dụng `verify_access_token` từ `src/pwd301/services/jwt_auth_service.py` để xử lý xác thực Bearer token cho REST API trong `get_authenticated_actor`.
- Tái sử dụng cấu trúc giao diện chuẩn của `frontend-preview/` để xây dựng `403.html`.

### C. Per-file changes
- `src/pwd301/services/exceptions.py` (MODIFY): Bổ sung các ngoại lệ phân quyền `AuthorizationError`, `ForbiddenError`, `InvalidRoleAssignmentError`, `ResourceNotFoundError`.
- `src/pwd301/models/identity.py` (MODIFY): Bổ sung `has_role`, `has_any_role`, `has_all_roles`, `is_admin`, `is_instructor`, `is_student`, `role_codes` cho `User`. Bổ sung lớp `AnonymousUser` kế thừa `AnonymousUserMixin`.
- `src/pwd301/models/__init__.py` (MODIFY): Xuất khẩu `AnonymousUser`.
- `src/pwd301/services/user_service.py` (MODIFY): Bổ sung `VALID_ROLE_COMBINATIONS`, `validate_role_combination`, `assign_role_to_user`, và `remove_role_from_user` đảm bảo bao đóng tích lũy, tăng `auth_version`, và ghi log `AuditEvent`.
- `src/pwd301/services/authorization_service.py` (NEW): Cung cấp bộ giải quyết actor đồng bộ (`get_authenticated_actor`), decorators (`@require_roles`, `@admin_required`, `@instructor_required`, `@student_required`), các hàm vị từ kiểm tra quyền tài nguyên (`can_view_course`, `can_manage_course`, `can_access_student_data`, `can_submit_attempt`, ...), và các hàm `require_*`.
- `src/pwd301/services/__init__.py` (MODIFY): Xuất khẩu các hàm và exception của `authorization_service`.
- `src/pwd301/templates/errors/403.html` (NEW): Trang thông báo lỗi 403 Forbidden tương thích `frontend-preview/`.
- `src/pwd301/__init__.py` (MODIFY): Cấu hình `login_manager.anonymous_user = AnonymousUser`, đăng ký error handlers cho 403, `ForbiddenError`, `ResourceNotFoundError`, cấu hình context processor phân quyền cho Jinja, và đăng ký các blueprint `student_bp`, `instructor_bp`, `admin_bp`.
- `src/pwd301/blueprints/student/` (NEW): Khởi tạo blueprint student và các route `/dashboard`, `/courses/<id>/progress`.
- `src/pwd301/blueprints/instructor/` (NEW): Khởi tạo blueprint instructor và các route `/dashboard`, `/courses/<id>/manage`, `/courses/<id>/students/<id>`.
- `src/pwd301/blueprints/admin/` (NEW): Khởi tạo blueprint admin và các route `/dashboard`, `/users/<id>/roles`.
- `tests/unit/test_authorization_service.py` (NEW): 10 test functions kiểm thử logic RBAC, gán role tích lũy, predicates tài nguyên, và invariants nộp bài thi.
- `tests/security/test_rbac_and_idor.py` (NEW): 12 security integration tests kiểm thử 401 unauth, 403 role violation, IDOR phòng ngừa xâm nhập chéo giữa giảng viên, phân lập tiến độ học viên, và kiểm soát Bearer JWT.

### D. Deletion and simplification list
| Candidate | Classification | Reason | Action |
|---|---|---|---|
| Complex dynamic permission registry tables | SIMPLIFY NOW | Theo RBAC model 01_RBAC_MODEL.md, hệ thống PWD301 sử dụng 3 vai trò tích lũy cố định: STUDENT, INSTRUCTOR, ADMIN | Sử dụng cumulative capability model trực tiếp trên bảng `roles` và `user_roles` |
| Client-supplied user ID in attempt submission | REMOVE NOW | Nguy cơ IDOR nghiêm trọng | Luôn đối chiếu `attempt.student_user_id == actor.id` bất kể role |
| Session fallback when invalid Bearer token is provided | REMOVE NOW | Nguy cơ rò rỉ ngữ cảnh bảo mật giữa REST API và Web cookies | Nếu request gửi header Authorization Bearer, việc xác thực token là authoritative, fail-closed khi token lỗi |

### E. Ponytails / deferred debt
- None. Toàn bộ kiến trúc phân quyền RBAC và Object-level authorization đã được cài đặt chặt chẽ, đầy đủ test bao phủ các ca âm tính bảo mật.

### F. Verification actually run and results
1. `mypy src/`:
   ```
   Success: no issues found in 37 source files
   ```
2. `ruff check src tests`:
   ```
   All checks passed!
   ```
3. `ruff format --check src tests`:
   ```
   51 files already formatted
   ```
4. `./scripts/verify.ps1`:
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
   51 files already formatted
   Success: no issues found in 37 source files
   == Tests ==
   ============================ 134 passed in 28.71s =============================
   PWD301 verification PASS
   ```

### G. Remaining risks / next step
- Hệ thống authorization đã sẵn sàng bảo vệ toàn bộ các tính năng nghiệp vụ tiếp theo.
- Kế hoạch tiếp theo theo roadmap: **TASK-006 — Course Management & Lifecycle Foundation**.

---

## Historical Tasks

### TASK-004 — Authentication & Identity Workflows (Web Session + JWT REST)
**Status:** DONE  
*Xây dựng hệ thống xác thực kép (Dual Authentication): Web UI session cookies với HttpOnly/CSRF protection và REST API JWT Bearer token theo RFC 7519, cùng cơ chế thu hồi phiên và Refresh Token Rotation.*

### TASK-003 — User / Account / Email Verification Foundation
**Status:** DONE  
*Core user account management, password hashing, and secure token lifecycle for email verification and password reset.*

### TASK-002 — Domain Models & Initial SQL Server Migrations
**Status:** DONE  
*Translated canonical database architecture (71 tables across `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/*.sql`) into SQLAlchemy domain models in Flask. Generated baseline Alembic / Flask-Migrate migration script compatible with Microsoft SQL Server, provided idempotent baseline seed script (`flask seed-baseline`) for foundational roles and root administrator, and verified all invariants and checks via `./scripts/verify.ps1`.*

### TASK-001 — Project Foundation & Flask Bootstrap
**Status:** DONE  
*Completed foundation bootstrap including Flask application factory, configuration classes, extension shells, `/health` and `/` routes, error handlers, and smoke test suite.*
