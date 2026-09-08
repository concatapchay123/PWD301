# 04 DATA DICTIONARY IDENTITY

Database engine: **Microsoft SQL Server**. Timestamps are UTC `DATETIME2(3)` unless noted.

## `users`

**Purpose**

Tài khoản duy nhất cho Student/Instructor/Admin; email là định danh đăng nhập duy nhất.

**Lifecycle**

ACTIVE → SUSPENDED/DEACTIVATED; có thể unsuspend về ACTIVE; khi xóa tài khoản theo chính sách thì deactivated trước, sau đó có thể ANONYMIZED.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `public_id` | `UNIQUEIDENTIFIER` | No | `NEWSEQUENTIALID()` | ID công khai dùng trong URL/API; không thay thế kiểm tra quyền |
| `email` | `NVARCHAR(320)` | No |  | Email đăng nhập hiện hành |
| `email_normalized` | `NVARCHAR(320)` | No | `LOWER(LTRIM(RTRIM([email]))) PERSISTED` | Email chuẩn hóa để unique |
| `password_hash` | `NVARCHAR(255)` | No |  | Mật khẩu đã băm bằng thuật toán mạnh; không lưu plaintext |
| `display_name` | `NVARCHAR(150)` | No |  | Tên hiển thị |
| `avatar_file_asset_id` | `BIGINT` | Yes |  | File ảnh đại diện logic; FK được thêm sau khi tạo file_assets |
| `status` | `VARCHAR(24)` | No | `'ACTIVE'` | ACTIVE/SUSPENDED/DEACTIVATED/ANONYMIZED |
| `auth_version` | `INT` | No | `1` | Tăng khi cần vô hiệu hóa toàn bộ session/JWT |
| `email_verified_at` | `DATETIME2(3)` | Yes |  | Thời điểm email hiện tại được xác minh |
| `suspended_at` | `DATETIME2(3)` | Yes |  | Thời điểm suspend |
| `suspension_reason` | `NVARCHAR(500)` | Yes |  | Lý do suspend |
| `anonymized_at` | `DATETIME2(3)` | Yes |  | Thời điểm ẩn danh hóa PII |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `updated_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm cập nhật cuối (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `avatar_file_asset_id` | `file_assets(id)` | `SET NULL` | Deferred cross-domain FK created in `010_cross_domain_constraints.sql`. |

### Unique Constraints

- `UNIQUE (public_id)`
- `UNIQUE (email_normalized)`

### Check Constraints

- `status IN ('ACTIVE','SUSPENDED','DEACTIVATED','ANONYMIZED')`
- `auth_version >= 1`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_users_status` | `status, id` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Không hard-delete nếu đã có lịch sử. PII có thể được ẩn danh; các FK lịch sử vẫn giữ user_id.

### Audit behavior

Role/status/email/security changes phải audit; không ghi password_hash vào payload.

### Concurrency

row_version cho cập nhật profile/trạng thái; suspend + auth_version increment trong một transaction.

### Security / PII classification

PII + authentication-sensitive. Chỉ backend truy cập password_hash.

### Important invariants

- email duy nhất sau normalize
- suspend phải làm auth_version thay đổi và revoke auth_sessions/JWT grants
- ANONYMIZED không được login

---

## `roles`

**Purpose**

Danh mục ba role hệ thống.

**Lifecycle**

Seed cố định; hiếm khi thay đổi.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `code` | `VARCHAR(32)` | No |  | STUDENT/INSTRUCTOR/ADMIN |
| `name` | `NVARCHAR(100)` | No |  | Tên hiển thị |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

_None._

### Unique Constraints

- `UNIQUE (code)`

### Check Constraints

- `code IN ('STUDENT','INSTRUCTOR','ADMIN')`

### Indexes

_None._

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

RESTRICT; không xóa role đang dùng.

### Audit behavior

Thay đổi seed role là hành động quản trị đặc biệt.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Không PII.

### Important invariants

- Chỉ ba role đã chốt trong MVP

---

## `user_roles`

**Purpose**

Quan hệ nhiều-nhiều User ↔ Role và nguồn gán quyền.

**Lifecycle**

Thêm/bỏ role theo service quản trị.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `user_id` | `BIGINT` | No |  | User |
| `role_id` | `BIGINT` | No |  | Role |
| `assigned_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm gán |
| `assigned_by_user_id` | `BIGINT` | Yes |  | Admin/người gán |
| `assignment_reason` | `NVARCHAR(500)` | Yes |  | Lý do gán/approve |

### Primary Key

`user_id, role_id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `user_id` | `users(id)` | `NO ACTION` |  |
| `role_id` | `roles(id)` | `NO ACTION` |  |
| `assigned_by_user_id` | `users(id)` | `SET NULL` |  |

### Unique Constraints

_None._

### Check Constraints

_None._

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_user_roles_role` | `role_id, user_id` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Xóa junction row khi revoke role; lịch sử hành động nằm AuditEvent.

### Audit behavior

Mọi grant/revoke phải audit và notification.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Authorization-critical.

### Important invariants

- Tổ hợp hợp lệ: STUDENT; STUDENT+INSTRUCTOR; STUDENT+INSTRUCTOR+ADMIN
- Service phải tự thêm role cấp thấp khi grant role cấp cao

---

## `auth_sessions`

**Purpose**

Session phía server cho web/Jinja/AJAX; cho phép revoke tức thì và theo dõi re-auth.

**Lifecycle**

Tạo khi login; revoke/logout/suspend; cleanup sau hết hạn.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `session_key_hash` | `BINARY(32)` | No |  | SHA-256 của opaque session key; không lưu raw key |
| `user_id` | `BIGINT` | No |  | User sở hữu session |
| `auth_version` | `INT` | No |  | Bản auth_version tại lúc login |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | UTC |
| `last_seen_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Hoạt động gần nhất |
| `expires_at` | `DATETIME2(3)` | No |  | Hết hạn session |
| `revoked_at` | `DATETIME2(3)` | Yes |  | Thời điểm revoke |
| `reauthenticated_at` | `DATETIME2(3)` | Yes |  | Lần nhập lại password gần nhất cho hành động nhạy cảm |
| `ip_address` | `VARCHAR(45)` | Yes |  | IPv4/IPv6 quan sát được |
| `user_agent_hash` | `BINARY(32)` | Yes |  | Hash UA, giảm lưu PII kỹ thuật |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `user_id` | `users(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (session_key_hash)`

### Check Constraints

- `expires_at > created_at`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_auth_sessions_user_active` | `user_id, expires_at` | No | `revoked_at IS NULL` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Hard-delete sau retention bảo mật ngắn khi expired/revoked; audit quan trọng giữ riêng.

### Audit behavior

Login/logout/revoke bất thường ghi security_event; không audit mọi heartbeat.

### Concurrency

Revoke và reauth cập nhật bằng row_version/transaction.

### Security / PII classification

Authentication-sensitive; raw cookie/session token không bao giờ lưu.

### Important invariants

- Session chỉ hợp lệ nếu user ACTIVE, revoked_at NULL, expires_at > now và auth_version khớp users.auth_version

---

## `jwt_token_grants`

**Purpose**

Theo dõi JWT/refresh grant cho REST API và revoke có kiểm soát.

**Lifecycle**

Issue → rotate/revoke/expire → cleanup.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `jti` | `UNIQUEIDENTIFIER` | No |  | JWT ID |
| `user_id` | `BIGINT` | No |  | User |
| `session_family_id` | `UNIQUEIDENTIFIER` | No | `NEWID()` | Nhóm token/refresh chain |
| `auth_version` | `INT` | No |  | Bản auth_version khi phát hành |
| `token_type` | `VARCHAR(16)` | No |  | ACCESS/REFRESH |
| `issued_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | UTC |
| `expires_at` | `DATETIME2(3)` | No |  | Hạn token |
| `revoked_at` | `DATETIME2(3)` | Yes |  | Revoke |
| `replaced_by_jti` | `UNIQUEIDENTIFIER` | Yes |  | Refresh rotation kế tiếp |
| `token_hash` | `BINARY(32)` | Yes |  | Hash refresh token nếu token opaque/refresh secret cần lưu |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `user_id` | `users(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (jti)`

### Check Constraints

- `token_type IN ('ACCESS','REFRESH')`
- `expires_at > issued_at`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_jwt_user_active` | `user_id, expires_at` | No | `revoked_at IS NULL` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_jwt_family` | `session_family_id, issued_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Cleanup sau expiry + security retention; security events tách riêng.

### Audit behavior

Revoke family hoặc nghi ngờ replay ghi security_event.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Authentication-sensitive; không lưu raw bearer token.

### Important invariants

- JWT hợp lệ cần signature + exp/nbf/iss/aud + grant chưa revoke + auth_version khớp user

---

## `user_security_tokens`

**Purpose**

Token dùng một lần cho verify email, đổi email, reset password.

**Lifecycle**

Tạo → consume/expire → cleanup.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `user_id` | `BIGINT` | No |  | User |
| `purpose` | `VARCHAR(32)` | No |  | EMAIL_VERIFY/EMAIL_CHANGE/PASSWORD_RESET |
| `token_hash` | `BINARY(32)` | No |  | Hash token một lần |
| `pending_email` | `NVARCHAR(320)` | Yes |  | Email mới khi EMAIL_CHANGE |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | UTC |
| `expires_at` | `DATETIME2(3)` | No |  | Hạn token |
| `consumed_at` | `DATETIME2(3)` | Yes |  | Đã dùng |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `user_id` | `users(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (token_hash)`

### Check Constraints

- `purpose IN ('EMAIL_VERIFY','EMAIL_CHANGE','PASSWORD_RESET')`
- `expires_at > created_at`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_security_tokens_user_purpose` | `user_id, purpose, expires_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Hard-delete sau expiry/consume + retention ngắn.

### Audit behavior

Không audit raw token; email/password change thành công phải audit.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Highly sensitive; chỉ hash token.

### Important invariants

- EMAIL_CHANGE chỉ cập nhật users.email sau xác minh token hợp lệ

---

## `instructor_applications`

**Purpose**

Yêu cầu Student trở thành Instructor; Admin duyệt/từ chối.

**Lifecycle**

PENDING → APPROVED/REJECTED/CANCELLED.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `applicant_user_id` | `BIGINT` | No |  | User đăng ký |
| `status` | `VARCHAR(20)` | No | `'PENDING'` | PENDING/APPROVED/REJECTED/CANCELLED |
| `application_note` | `NVARCHAR(2000)` | Yes |  | Thông tin đăng ký |
| `reviewed_by_user_id` | `BIGINT` | Yes |  | Admin duyệt |
| `review_reason` | `NVARCHAR(1000)` | Yes |  | Lý do quyết định |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `reviewed_at` | `DATETIME2(3)` | Yes |  | Thời điểm duyệt |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `applicant_user_id` | `users(id)` | `NO ACTION` |  |
| `reviewed_by_user_id` | `users(id)` | `SET NULL` |  |

### Unique Constraints

_None._

### Check Constraints

- `status IN ('PENDING','APPROVED','REJECTED','CANCELLED')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_instructor_app_status` | `status, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Không hard-delete quyết định đã review trong retention audit.

### Audit behavior

Approve/reject bắt buộc audit.

### Concurrency

row_version tránh hai Admin review chồng nhau.

### Security / PII classification

Chứa dữ liệu hồ sơ nhẹ; Instructor role chỉ được grant qua service.

### Important invariants

- APPROVED transaction phải tạo roles STUDENT+INSTRUCTOR nếu chưa có và notification

---

## `security_events`

**Purpose**

Sự kiện bảo mật/abuse cần giữ dù raw AI chat hoặc session đã cleanup.

**Lifecycle**

Append; archive operationally khi rất cũ.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `user_id` | `BIGINT` | Yes |  | User liên quan |
| `event_type` | `VARCHAR(64)` | No |  | FAILED_LOGIN/PROMPT_INJECTION/MALWARE/RATE_LIMIT/... |
| `severity` | `VARCHAR(16)` | No |  | INFO/WARN/HIGH/CRITICAL |
| `action_taken` | `VARCHAR(64)` | No |  | ALLOW/BLOCK/REVOKE/QUARANTINE/ALERT |
| `risk_score` | `DECIMAL(5,2)` | Yes |  | 0-100 |
| `input_hash` | `BINARY(32)` | Yes |  | Hash input khi cần đối chiếu, không raw content |
| `ip_address` | `VARCHAR(45)` | Yes |  | IP |
| `correlation_id` | `UNIQUEIDENTIFIER` | No | `NEWID()` | Liên kết request |
| `metadata_json` | `NVARCHAR(MAX)` | Yes |  | Metadata không chứa secret/raw sensitive text |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `user_id` | `users(id)` | `SET NULL` |  |

### Unique Constraints

_None._

### Check Constraints

- `severity IN ('INFO','WARN','HIGH','CRITICAL')`
- `action_taken IN ('ALLOW','BLOCK','REVOKE','QUARANTINE','ALERT')`
- `risk_score IS NULL OR (risk_score >= 0 AND risk_score <= 100)`
- `metadata_json IS NULL OR ISJSON(metadata_json)=1`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_security_events_type_time` | `event_type, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_security_events_user_time` | `user_id, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Không user-delete; có thể archive theo policy.

### Audit behavior

Bản thân là security record; không chứa secret.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Security-sensitive; quyền xem Admin hạn chế.

### Important invariants

- Không lưu raw password/JWT/API key/raw AI conversation

---
