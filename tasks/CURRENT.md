# CURRENT TASK

## TASK-003 — User / Account / Email Verification Foundation

**Status:** DONE

### 1. Goal
Xây dựng tầng Service (Business Logic Layer) cốt lõi để quản lý vòng đời tài khoản người dùng, băm mật khẩu (password hashing), và sinh/xác thực mã an toàn (Security Tokens) dùng cho việc xác nhận email và đặt lại mật khẩu.

### 2. Source-of-truth documents
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/02_USER_ACCOUNT_LIFECYCLE.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/authentication/04_EMAIL_VERIFICATION.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/authentication/05_PASSWORD_AND_REAUTHENTICATION.md`
- Bảng DB liên quan: `User`, `Role`, `UserRole`, `UserSecurityToken` (trong `src/pwd301/models/identity.py`).

### 3. In scope
Tạo các module tại `src/pwd301/services/` (bao gồm `exceptions.py`, `user_service.py`, `auth_token_service.py` và `__init__.py`):
1. **User Registration & Management:** 
   - Khởi tạo user mới (mặc định chưa verify email, băm mật khẩu bằng `werkzeug.security.generate_password_hash`).
   - Chuẩn hóa (normalize) email trước khi query/insert.
   - Cập nhật thông tin profile cơ bản.
   - Thay đổi mật khẩu (phải tự động tăng `auth_version` của User lên 1 để sau này dùng cho việc revoke session).
2. **Security Token Lifecycle (`UserSecurityToken`):**
   - Sinh token ngẫu nhiên an toàn (ví dụ: dùng `secrets.token_urlsafe()`).
   - Lưu trữ bản băm của token (`token_hash`) vào cơ sở dữ liệu để chống lộ lọt nếu DB bị dump. Hàm trả về raw token cho caller.
   - Xử lý các `purpose`: `EMAIL_VERIFY` (thường hạn 24h), `PASSWORD_RESET` (thường hạn 1h), `EMAIL_CHANGE` (hạn 24h).
   - Hàm verify token: Kiểm tra hash, kiểm tra hạn (expires_at), và đánh dấu đã sử dụng (`consumed_at`).
3. **Unit Tests:**
   - Viết test suite tại `tests/unit/test_user_service.py`.

### 4. Out of scope
- **KHÔNG** làm chức năng Login/Session/JWT (Đó là nhiệm vụ của TASK-004).
- **KHÔNG** tích hợp SMTP hay gửi email thật (Đó là nhiệm vụ của TASK-021). Hàm tạo token chỉ cần trả về raw token string hoặc log ra console.
- **KHÔNG** làm Web UI/Forms.

### 5. Security & Invariants
- **Bất biến 1:** Email là định danh duy nhất (Unique Login Identifier) và phải được chuyển thành in thường (lowercase).
- **Bất biến 2:** Không bao giờ lưu raw password hay raw security token vào CSDL.
- **Bất biến 3:** Xử lý ngoại lệ (Exception) chuẩn xác khi tạo user bị trùng email (bắt lỗi IntegrityError và check trước).
- **Bất biến 4:** Giao dịch DB phải an toàn (sử dụng `db.session.commit()` hợp lý, rollback nếu xảy ra lỗi).

### 6. Acceptance Criteria & Kiểm thử (Checklist)
Coding Agent đã hoàn thành và tự verify các tiêu chí sau:
- [x] Hàm tạo User hoạt động tốt, từ chối tạo nếu email đã tồn tại.
- [x] Mật khẩu được mã hóa an toàn, hàm kiểm tra mật khẩu (`check_password_hash`) hoạt động chính xác.
- [x] Đổi mật khẩu thành công thì cột `auth_version` của User phải được cộng thêm 1.
- [x] Hàm tạo Security Token sinh ra được token, DB lưu bản hash SHA-256 (hoặc tương đương) của token đó.
- [x] Token hết hạn (`expires_at < utc_now()`) hoặc đã dùng (`consumed_at IS NOT NULL`) sẽ bị từ chối xác thực.
- [x] Xác thực email thành công thì cập nhật cột `email_verified_at` của User.

### 7. Verification commands
1. `pytest tests/unit/ -v` (59 tests pass 100%).
2. `mypy src/pwd301/services/` (Success: no issues found in 4 source files).
3. `./scripts/verify.ps1` (Toàn bộ pipeline: ruff format, lint, mypy, 71 tests pass).

---

## Completion Report

### A. Scope and sources consulted
- Operating contract: `AGENTS.md`
- Database Architecture: `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/001_identity.sql` (`users`, `roles`, `user_roles`, `user_security_tokens`)
- User lifecycle specification: `docs/system/PWD301_SYSTEM_SPECIFICATION/business/02_USER_ACCOUNT_LIFECYCLE.md`
- Email verification specification: `docs/system/PWD301_SYSTEM_SPECIFICATION/authentication/04_EMAIL_VERIFICATION.md`
- Password specification: `docs/system/PWD301_SYSTEM_SPECIFICATION/authentication/05_PASSWORD_AND_REAUTHENTICATION.md`
- Workflows specification: `docs/system/PWD301_SYSTEM_SPECIFICATION/workflows/01_USER_ACCOUNT_WORKFLOWS.md`
- Non-negotiable invariants: `docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md`

### B. Reuse decisions
- Reused `werkzeug.security` (`generate_password_hash`, `check_password_hash`) for adaptive, secure password hashing.
- Reused Python standard library `secrets.token_urlsafe(32)` for cryptographically secure token generation.
- Reused standard library `hashlib.sha256` for generating 32-byte binary digests mapping directly to `Binary32` / MSSQL `BINARY(32)`.
- Reused `pwd301.models.identity` (`User`, `Role`, `UserSecurityToken`) and `pwd301.models.types` (`utc_now`).
- Maintained clean separation of concerns: exceptions module, user management service, and auth token service.

### C. Per-file changes
- `src/pwd301/services/exceptions.py` (NEW): Defined 10 domain exceptions (`ServiceError`, `UserAlreadyExistsError`, `UserNotFoundError`, `InvalidEmailError`, `InvalidPasswordError`, `AccountNotActiveError`, `InvalidTokenError`, `TokenExpiredError`, `TokenAlreadyConsumedError`, `TokenPurposeMismatchError`).
- `src/pwd301/services/user_service.py` (NEW): Core user business logic (`normalize_email`, `validate_password`, `register_user`, `get_user_by_id`, `get_user_by_public_id`, `get_user_by_email`, `verify_password`, `change_password`, `set_password`, `update_profile`, `mark_email_verified`).
- `src/pwd301/services/auth_token_service.py` (NEW): Security token lifecycle service (`SecurityTokenPurpose`, `hash_token`, `generate_raw_token`, `create_security_token`, `verify_security_token`, `consume_security_token`, `verify_email_with_token`, `reset_password_with_token`, `apply_email_change_with_token`).
- `src/pwd301/services/__init__.py` (NEW): Package exports for services layer.
- `tests/unit/test_user_service.py` (NEW): 28 comprehensive unit tests covering all user management and token lifecycle paths.

### D. Deletion and simplification list
| Candidate | Classification | Reason | Action |
|---|---|---|---|
| Direct SMTP calls | KEEP (DEFERRED) | Out of scope for TASK-003, scheduled for TASK-021 | Kept token service focused on token lifecycle and returning raw token string |
| Login / Session / JWT routes | KEEP (DEFERRED) | Out of scope for TASK-003, scheduled for TASK-004 | Service layer foundation ready for consumption by auth endpoints |
| Offset-naive vs aware date comparison | SIMPLIFY NOW | SQLite default driver strips timezone offsets | Added `_ensure_utc` helper to guarantee UTC-aware datetime comparisons across all DB backends |

### E. Ponytails / deferred debt
- None. All requirements for TASK-003 are fully fulfilled without technical shortcuts.

### F. Verification actually run and results
1. `mypy src/pwd301/services/`:
   ```
   Success: no issues found in 4 source files
   ```
2. `pytest tests/unit/ -v`:
   ```
   59 passed in 7.85s (28 tests in test_user_service.py, 31 tests across existing unit suites)
   ```
3. `./scripts/verify.ps1`:
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
   34 files already formatted
   Success: no issues found in 24 source files
   == Tests ==
   ============================= 71 passed in 9.62s ==============================
   PWD301 verification PASS
   ```

### G. Remaining risks / next step
- Next scheduled task: **TASK-004 — Authentication & Identity Workflows (Web Session + JWT REST)**.

---

## Historical Tasks

### TASK-002 — Domain Models & Initial SQL Server Migrations
**Status:** DONE  
*Translated canonical database architecture (71 tables across `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/*.sql`) into SQLAlchemy domain models in Flask. Generated baseline Alembic / Flask-Migrate migration script compatible with Microsoft SQL Server, provided idempotent baseline seed script (`flask seed-baseline`) for foundational roles and root administrator, and verified all invariants and checks via `./scripts/verify.ps1`.*

### TASK-001 — Project Foundation & Flask Bootstrap
**Status:** DONE  
*Completed foundation bootstrap including Flask application factory, configuration classes, extension shells, `/health` and `/` routes, error handlers, and smoke test suite.*
