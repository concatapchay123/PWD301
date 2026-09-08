# CURRENT TASK

## TASK-004 — Authentication & Identity Workflows (Web Session + JWT REST)

**Status:** DONE

### 1. Goal
Xây dựng hệ thống xác thực kép (Dual Authentication) cho PWD301:
1. **Web UI / AJAX:** Sử dụng Flask-Login với Session Cookies (HttpOnly) và CSRF protection. Tuyệt đối không dùng/lưu JWT vào localStorage cho client Web.
2. **REST API:** Sử dụng JWT Bearer token theo chuẩn RFC 7519 cho các API clients ngoài Web UI.
3. **Session Revocation:** Quản lý vòng đời phiên đăng nhập thông qua `AuthSession` và `JwtTokenGrant`, hỗ trợ thu hồi toàn cục khi người dùng đổi mật khẩu hoặc bị khóa tài khoản thông qua trường `auth_version` của `User`.

### 2. Source-of-truth documents
- `docs/system/PWD301_SYSTEM_SPECIFICATION/authentication/01_AUTHENTICATION_ARCHITECTURE.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/02_USER_ACCOUNT_LIFECYCLE.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md`
- Canonical DDL: `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/001_identity.sql` (`users`, `auth_sessions`, `jwt_token_grants`).
- Frontend preview reference: `frontend-preview/views/login.html`, `frontend-preview/views/register.html`.

### 3. In scope
1. **Session Authentication Service (`session_auth_service.py`):**
   - Băm session key bằng SHA-256 (`Binary32`) lưu vào bảng `auth_sessions`.
   - Sinh session, kiểm tra session hợp lệ (`is_revoked`, `expires_at`, `auth_version`).
   - Thu hồi phiên đơn lẻ (`revoke_auth_session`) và toàn bộ phiên người dùng (`revoke_all_user_sessions`).
2. **JWT Authentication Service (`jwt_auth_service.py`):**
   - Sinh cặp Access Token (ngắn hạn: 15 phút) và Refresh Token (dài hạn: 7 ngày) ký bằng `JWT_SECRET_KEY` (HS256).
   - Lưu trữ và đối chiếu metadata trong `jwt_token_grants` theo `session_family_id`.
   - Cơ chế xoay vòng Refresh Token (Refresh Token Rotation) và phát hiện tấn công tái sử dụng (Replay Attack) dẫn tới hủy toàn bộ token family.
   - Decorator `@jwt_required` bảo vệ REST API endpoints.
3. **User Service Updates (`user_service.py`):**
   - Khi đổi mật khẩu (`change_password`, `set_password`), tự động tăng `auth_version` và gọi thu hồi toàn bộ session + JWT.
   - Bổ sung hàm `suspend_user` khóa tài khoản và thu hồi toàn bộ phiên đăng nhập.
4. **Web UI Blueprint & Templates (`src/pwd301/blueprints/auth/`):**
   - Routes: `GET /auth/login`, `POST /auth/login`, `POST /auth/logout`, `GET /auth/register`, `POST /auth/register`.
   - Tích hợp Flask-Login (`login_user`, `logout_user`, `@login_required`).
   - Templates: `login.html`, `register.html` dựa trên `frontend-preview/`.
5. **REST API Blueprint (`src/pwd301/blueprints/api_auth/`):**
   - Endpoints: `POST /api/v1/auth/token`, `POST /api/v1/auth/refresh`, `POST /api/v1/auth/revoke`, `GET /api/v1/auth/me`.
   - Miễn trừ CSRF cho blueprint REST API theo đúng chuẩn Bearer Token.
6. **Application Factory Integration (`src/pwd301/__init__.py`):**
   - Cấu hình `login_manager.user_loader` xác thực cả user status, `auth_version` và `AuthSession` trong CSDL.
   - Cấu hình `login_manager.unauthorized_handler` phân biệt Web (redirect) và AJAX/JSON (401).
7. **Comprehensive Unit & Integration Test Suites:**
   - Unit tests: `tests/unit/test_session_auth_service.py`, `tests/unit/test_jwt_auth_service.py`.
   - API tests: `tests/api/test_auth_web.py`, `tests/api/test_auth_jwt.py`.

### 4. Out of scope
- **Role-Based Access Control (RBAC)** — Scheduled for TASK-005.
- **External Caching / In-memory Redis store** — Quản lý token/session dựa hoàn toàn trên database theo System Specification.
- **Email Delivery (SMTP/SendGrid)** — Scheduled for TASK-021.

### 5. Security & Invariants
- **Bất biến 1:** Web UI chỉ dùng Session Cookies (`HttpOnly`, `SameSite=Lax`), CSRF protection enabled. Tuyệt đối không lưu JWT vào localStorage.
- **Bất biến 2:** Khóa bí mật JWT (`JWT_SECRET_KEY`) tách biệt hoàn toàn với Flask `SECRET_KEY`.
- **Bất biến 3:** Mọi thay đổi thông tin xác thực (đổi mật khẩu) hoặc khóa tài khoản (`SUSPENDED`) tăng `auth_version` và thu hồi tức thì toàn bộ phiên đăng nhập (Web & JWT).
- **Bất biến 4:** Refresh token rotation phát hiện replay attack và thu hồi ngay lập tức toàn bộ họ token (`session_family_id`).

### 6. Acceptance Criteria & Kiểm thử (Checklist)
- [x] Tạo session đăng nhập Web lưu bản băm SHA-256 vào `AuthSession`, kiểm tra cookie HttpOnly.
- [x] Đăng xuất Web xóa session cookie và đánh dấu `is_revoked = True` trong CSDL.
- [x] Đăng nhập REST API sinh cặp Access Token (15m) và Refresh Token (7d).
- [x] Xoay vòng Refresh Token thành công, nếu dùng lại token cũ sẽ thu hồi toàn bộ token family.
- [x] Khi đổi mật khẩu hoặc đình chỉ tài khoản, `auth_version` tăng lên và toàn bộ session/JWT cũ bị từ chối xác thực.
- [x] Route `/api/v1/auth/me` yêu cầu Bearer token hợp lệ, trả về thông tin user.
- [x] Bộ test suite đạt 112/112 tests pass, 0 lỗi linter/format/types.

### 7. Verification commands
1. `pytest tests/ -v` (112 passed in 25.03s).
2. `mypy src/` (Success: no issues found in 30 source files).
3. `ruff check src tests scripts` (All checks passed).
4. `ruff format --check src tests scripts` (42 files already formatted).
5. `./scripts/verify.ps1` (Toàn bộ pipeline: repository contract, lint, format, types, 112 tests pass).

---

## Completion Report

### A. Scope and sources consulted
- Operating contract: `AGENTS.md`
- Authentication architecture: `docs/system/PWD301_SYSTEM_SPECIFICATION/authentication/01_AUTHENTICATION_ARCHITECTURE.md`
- User lifecycle specification: `docs/system/PWD301_SYSTEM_SPECIFICATION/business/02_USER_ACCOUNT_LIFECYCLE.md`
- Non-negotiable invariants: `docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md`
- Database Architecture DDL: `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/001_identity.sql`
- Frontend Preview: `frontend-preview/views/login.html`, `frontend-preview/views/register.html`, `frontend-preview/css/app.css`

### B. Reuse decisions
- Reused `flask_login` (`login_user`, `logout_user`, `login_required`, `current_user`) for web session management.
- Reused `PyJWT` (RFC 7519) with `algorithms=["HS256"]` for token creation, verification, and decoding.
- Reused `hashlib.sha256` for database session key hashing to match `BINARY(32)` column specification.
- Reused `src/pwd301/models/identity.py` (`User`, `AuthSession`, `JwtTokenGrant`) and `src/pwd301/services/user_service.py` for user credentials validation.
- Reused `frontend-preview/` visual structure for Jinja templates (`login.html`, `register.html`, navbar in `base.html`).

### C. Per-file changes
- `src/pwd301/services/exceptions.py` (MODIFY): Added authentication domain exceptions (`AuthenticationError`, `InvalidCredentialsError`, `SessionExpiredError`, `SessionRevokedError`, `JwtTokenInvalidError`, `JwtTokenExpiredError`, `JwtTokenRevokedError`, `AuthVersionMismatchError`).
- `src/pwd301/services/session_auth_service.py` (NEW): Implemented session creation, validation, hash calculation, and granular/global revocation.
- `src/pwd301/services/jwt_auth_service.py` (NEW): Implemented token generation, claims verification, token family rotation, replay attack revocation, and `@jwt_required` decorator.
- `src/pwd301/services/user_service.py` (MODIFY): Connected password change and user suspension to `revoke_all_user_sessions()` and `revoke_all_user_tokens()`.
- `src/pwd301/services/__init__.py` (MODIFY): Exported all auth services and exceptions.
- `src/pwd301/blueprints/auth/` (NEW): Web authentication blueprint (`routes.py`) implementing login, logout, and register.
- `src/pwd301/blueprints/api_auth/` (NEW): REST API authentication blueprint (`routes.py`) implementing `/token`, `/refresh`, `/revoke`, `/me`.
- `src/pwd301/templates/auth/login.html` (NEW): Login template with CSRF and error alerts.
- `src/pwd301/templates/auth/register.html` (NEW): Register template.
- `src/pwd301/templates/base.html` (MODIFY): Updated navbar with dynamic auth status and logout form.
- `src/pwd301/__init__.py` (MODIFY): Configured Flask-Login `user_loader` with database `AuthSession` validation, `unauthorized_handler`, blueprint registration, and CSRF exemptions for API.
- `requirements.txt` (MODIFY): Added `PyJWT>=2.8,<3`.
- `tests/unit/test_session_auth_service.py` (NEW): 12 unit tests for session lifecycle.
- `tests/unit/test_jwt_auth_service.py` (NEW): 11 unit tests for JWT lifecycle and rotation.
- `tests/api/test_auth_web.py` (NEW): 9 integration tests for Web UI authentication.
- `tests/api/test_auth_jwt.py` (NEW): 9 integration tests for REST API authentication.

### D. Deletion and simplification list
| Candidate | Classification | Reason | Action |
|---|---|---|---|
| JWT storage in localStorage | REMOVE NOW | Invariant violation (XSS vulnerability) | Web UI strictly relies on Flask-Login HttpOnly session cookies |
| Sharing `SECRET_KEY` for JWT | REMOVE NOW | Key isolation violation | Dedicated `JWT_SECRET_KEY` enforced in config and tests |
| Token family tracking in external cache | SIMPLIFY NOW | Database-backed design mandated by specification | Tracked in `JwtTokenGrant` with `session_family_id` |

### E. Ponytails / deferred debt
- None. Dual authentication is fully implemented, verified, and adheres to all architectural invariants.

### F. Verification actually run and results
1. `mypy src/`:
   ```
   Success: no issues found in 30 source files
   ```
2. `ruff check src tests scripts`:
   ```
   All checks passed!
   ```
3. `ruff format --check src tests scripts`:
   ```
   42 files already formatted
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
   42 files already formatted
   Success: no issues found in 30 source files
   == Tests ==
   ============================ 112 passed in 25.03s =============================
   PWD301 verification PASS
   ```

### G. Remaining risks / next step
- Next scheduled task: **TASK-005 — Authorization & Role-Based Access Control (RBAC & Resource Ownership)**.

---

## Historical Tasks

### TASK-003 — User / Account / Email Verification Foundation
**Status:** DONE  
*Core user account management, password hashing, and secure token lifecycle for email verification and password reset.*

### TASK-002 — Domain Models & Initial SQL Server Migrations
**Status:** DONE  
*Translated canonical database architecture (71 tables across `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/*.sql`) into SQLAlchemy domain models in Flask. Generated baseline Alembic / Flask-Migrate migration script compatible with Microsoft SQL Server, provided idempotent baseline seed script (`flask seed-baseline`) for foundational roles and root administrator, and verified all invariants and checks via `./scripts/verify.ps1`.*

### TASK-001 — Project Foundation & Flask Bootstrap
**Status:** DONE  
*Completed foundation bootstrap including Flask application factory, configuration classes, extension shells, `/health` and `/` routes, error handlers, and smoke test suite.*
