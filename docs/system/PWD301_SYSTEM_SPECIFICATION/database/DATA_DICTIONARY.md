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
# 05 DATA DICTIONARY COURSE

Database engine: **Microsoft SQL Server**. Timestamps are UTC `DATETIME2(3)` unless noted.

## `courses`

**Purpose**

Course chính; có thể tạm không có Instructor owner; code và title đều unique.

**Lifecycle**

DRAFT → SUBMITTED_FOR_REVIEW → APPROVED → PUBLISHED; có thể ARCHIVED hoặc TRASH. Material change trên bản published đi qua course_change_requests.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `public_id` | `UNIQUEIDENTIFIER` | No | `NEWSEQUENTIALID()` | ID công khai dùng trong URL/API; không thay thế kiểm tra quyền |
| `course_code` | `NVARCHAR(50)` | No |  | Mã Course |
| `course_code_normalized` | `NVARCHAR(50)` | No | `UPPER(LTRIM(RTRIM([course_code]))) PERSISTED` | Mã chuẩn hóa |
| `title` | `NVARCHAR(200)` | No |  | Tên Course |
| `title_normalized` | `NVARCHAR(200)` | No | `LOWER(LTRIM(RTRIM([title]))) PERSISTED` | Tên chuẩn hóa |
| `description` | `NVARCHAR(MAX)` | Yes |  | Mô tả |
| `category` | `NVARCHAR(100)` | Yes |  | Danh mục |
| `difficulty` | `VARCHAR(20)` | Yes |  | BEGINNER/INTERMEDIATE/ADVANCED |
| `owner_instructor_id` | `BIGINT` | Yes |  | Instructor hiện quản lý; có thể NULL tạm thời |
| `thumbnail_file_asset_id` | `BIGINT` | Yes |  | Ảnh Course; FK thêm sau khi file_assets tồn tại |
| `status` | `VARCHAR(32)` | No | `'DRAFT'` | DRAFT/SUBMITTED_FOR_REVIEW/APPROVED/PUBLISHED/ARCHIVED/TRASH |
| `capacity` | `INT` | Yes |  | Số Student tối đa; NULL = không giới hạn |
| `storage_quota_bytes` | `BIGINT` | Yes |  | Quota override per Course; NULL dùng mặc định |
| `published_at` | `DATETIME2(3)` | Yes |  | Lần publish hiện hành/đầu tiên tùy service |
| `approved_at` | `DATETIME2(3)` | Yes |  | Lần approve gần nhất |
| `approved_by_user_id` | `BIGINT` | Yes |  | Admin approve |
| `first_student_enrolled_at` | `DATETIME2(3)` | Yes |  | Marker lịch sử giúp delete policy |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `updated_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm cập nhật cuối (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |
| `deleted_at` | `DATETIME2(3)` | Yes |  | Thời điểm đưa vào thùng rác |
| `restore_until` | `DATETIME2(3)` | Yes |  | Hạn khôi phục trước khi cleanup/historical transition |
| `deleted_by_user_id` | `BIGINT` | Yes |  | Người thực hiện xóa |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `owner_instructor_id` | `users(id)` | `NO ACTION` | User records with history are deactivated/anonymized rather than hard-deleted; reassignment/nulling is service-managed. |
| `approved_by_user_id` | `users(id)` | `NO ACTION` | Preserve approval actor history; anonymize User in place. |
| `deleted_by_user_id` | `users(id)` | `NO ACTION` | Preserve deletion actor history; anonymize User in place. |
| `thumbnail_file_asset_id` | `file_assets(id)` | `SET NULL` | Deferred cross-domain FK created in `010_cross_domain_constraints.sql`. |

### Unique Constraints

- `UNIQUE (public_id)`
- `UNIQUE (course_code_normalized)`
- `UNIQUE (title_normalized)`

### Check Constraints

- `status IN ('DRAFT','SUBMITTED_FOR_REVIEW','APPROVED','PUBLISHED','ARCHIVED','TRASH')`
- `difficulty IS NULL OR difficulty IN ('BEGINNER','INTERMEDIATE','ADVANCED')`
- `capacity IS NULL OR capacity > 0`
- `storage_quota_bytes IS NULL OR storage_quota_bytes > 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_courses_catalog` | `status, category, difficulty, title` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_courses_owner` | `owner_instructor_id, status` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Course chưa có lịch sử có thể hard-delete sau recovery. Course đã có Student: TRASH/ARCHIVED historical, không cascade attempts/progress.

### Audit behavior

Publish/approve/archive/delete/reassign/material admin edit phải audit.

### Concurrency

row_version; reorder/structural operations dùng transaction.

### Security / PII classification

Authorization boundary theo owner_instructor_id + Admin override có reason/audit.

### Important invariants

- Course code unique
- Course title unique
- owner nếu có phải đang có role INSTRUCTOR (service-enforced)
- Course làm prerequisite cho active course khác không được archive/delete

---

## `course_prerequisites`

**Purpose**

Quan hệ N-N Course yêu cầu Course khác hoàn thành trước.

**Lifecycle**

Thêm/xóa khi Course chưa bị dependency lock.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `course_id` | `BIGINT` | No |  | Course đích |
| `prerequisite_course_id` | `BIGINT` | No |  | Course bắt buộc hoàn thành |
| `created_by_user_id` | `BIGINT` | No |  | Người tạo |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`course_id, prerequisite_course_id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `course_id` | `courses(id)` | `NO ACTION` |  |
| `prerequisite_course_id` | `courses(id)` | `NO ACTION` |  |
| `created_by_user_id` | `users(id)` | `NO ACTION` | Column is required; historical actor is preserved through User anonymization. |

### Unique Constraints

_None._

### Check Constraints

- `course_id <> prerequisite_course_id`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_course_prereq_reverse` | `prerequisite_course_id, course_id` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

NO ACTION; hard delete Course bị chặn nếu còn dependency.

### Audit behavior

Thay đổi prerequisite là material change và audit/reapproval.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Instructor owner/Admin.

### Important invariants

- Không self-reference
- Không cycle; cycle detection service trong transaction
- Không archive/delete prerequisite đang phục vụ active Course

---

## `course_completion_rules`

**Purpose**

Cấu hình điều kiện hoàn thành Course theo mô hình đơn giản, không EAV.

**Lifecycle**

Một row per Course; material change cần approval trên Course published.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `course_id` | `BIGINT` | No |  | PK/FK Course |
| `require_all_required_lessons` | `BIT` | No | `1` | Phải hoàn thành tất cả Lesson bắt buộc |
| `require_required_assessments` | `BIT` | No | `1` | Phải đạt các Assessment đánh dấu required |
| `minimum_progress_percent` | `DECIMAL(5,2)` | Yes |  | Ngưỡng progress nếu cần |
| `updated_by_user_id` | `BIGINT` | Yes |  | Người chỉnh |
| `updated_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm cập nhật cuối (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`course_id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `course_id` | `courses(id)` | `NO ACTION` |  |
| `updated_by_user_id` | `users(id)` | `SET NULL` |  |

### Unique Constraints

_None._

### Check Constraints

- `minimum_progress_percent IS NULL OR (minimum_progress_percent >= 0 AND minimum_progress_percent <= 100)`

### Indexes

_None._

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

CASCADE chỉ khi Course chưa có lịch sử và hard-delete hợp lệ; lịch sử completion summary độc lập.

### Audit behavior

Mọi material rule change audit.

### Concurrency

row_version.

### Security / PII classification

Instructor owner/Admin.

### Important invariants

- Completed status trước đây không bị đảo ngược khi rule nghiêm hơn; summary là historical proof

---

## `course_change_requests`

**Purpose**

Staging tối thiểu cho thay đổi material của Course đã published để Admin duyệt trước khi áp dụng.

**Lifecycle**

PENDING → APPROVED/REJECTED/CANCELLED; APPROVED → APPLIED trong transaction.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `course_id` | `BIGINT` | No |  | Course |
| `requested_by_user_id` | `BIGINT` | No |  | Instructor/Admin tạo |
| `change_type` | `VARCHAR(32)` | No |  | COURSE_METADATA/LESSON_STRUCTURE/LESSON_CONTENT/COMPLETION_RULE/PREREQUISITE/OTHER |
| `target_type` | `VARCHAR(32)` | No |  | COURSE/LESSON/RULE/PREREQUISITE |
| `target_id` | `BIGINT` | Yes |  | ID target nếu có |
| `proposed_payload_json` | `NVARCHAR(MAX)` | No |  | Patch/proposed data; chỉ dùng staging, source of truth vẫn ở bảng chuẩn hóa |
| `status` | `VARCHAR(20)` | No | `'PENDING'` | PENDING/APPROVED/REJECTED/CANCELLED/APPLIED |
| `reviewed_by_user_id` | `BIGINT` | Yes |  | Admin |
| `review_reason` | `NVARCHAR(1000)` | Yes |  | Lý do |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `reviewed_at` | `DATETIME2(3)` | Yes |  | UTC |
| `applied_at` | `DATETIME2(3)` | Yes |  | UTC |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `course_id` | `courses(id)` | `NO ACTION` |  |
| `requested_by_user_id` | `users(id)` | `NO ACTION` |  |
| `reviewed_by_user_id` | `users(id)` | `SET NULL` |  |

### Unique Constraints

_None._

### Check Constraints

- `change_type IN ('COURSE_METADATA','LESSON_STRUCTURE','LESSON_CONTENT','COMPLETION_RULE','PREREQUISITE','OTHER')`
- `target_type IN ('COURSE','LESSON','RULE','PREREQUISITE')`
- `status IN ('PENDING','APPROVED','REJECTED','CANCELLED','APPLIED')`
- `ISJSON(proposed_payload_json)=1`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_course_changes_pending` | `status, created_at` | No | `status='PENDING'` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_course_changes_course` | `course_id, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Giữ tối thiểu trong audit retention; không dùng làm historical content snapshot dài hạn.

### Audit behavior

Review/apply bắt buộc audit.

### Concurrency

row_version + conditional transition.

### Security / PII classification

Payload có thể chứa nội dung học liệu; chỉ owner/Admin.

### Important invariants

- Không áp dụng material change vào published data trước APPROVED
- Minor edit không cần row này nhưng vẫn audit khi quan trọng

---

## `lessons`

**Purpose**

Lesson thuộc Course, có thứ tự, nội dung Markdown và ngưỡng hoàn thành tự động.

**Lifecycle**

DRAFT → PUBLISHED; có thể HIDDEN/TRASH; Lesson có học sử sau recovery trở thành HISTORICAL thay vì hard delete.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `public_id` | `UNIQUEIDENTIFIER` | No | `NEWSEQUENTIALID()` | ID công khai dùng trong URL/API; không thay thế kiểm tra quyền |
| `course_id` | `BIGINT` | No |  | Course |
| `title` | `NVARCHAR(200)` | No |  | Tên Lesson |
| `summary` | `NVARCHAR(1000)` | Yes |  | Tóm tắt |
| `markdown_content` | `NVARCHAR(MAX)` | No |  | Markdown source; render phải sanitize |
| `position` | `INT` | No |  | Thứ tự trong Course |
| `estimated_duration_minutes` | `INT` | Yes |  | Ước lượng |
| `minimum_completion_seconds` | `INT` | No | `30` | Thời gian tối thiểu để được complete |
| `viewed_fraction_required` | `DECIMAL(5,4)` | No | `0.8000` | Tỷ lệ nội dung cần xem, 0..1 |
| `required_for_periods_starting_at` | `DATETIME2(3)` | Yes |  | Enrollment period bắt đầu trước mốc này xem Lesson mới như 'Xem thêm' |
| `status` | `VARCHAR(20)` | No | `'DRAFT'` | DRAFT/PUBLISHED/HIDDEN/TRASH/HISTORICAL |
| `published_at` | `DATETIME2(3)` | Yes |  | UTC |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `updated_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm cập nhật cuối (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |
| `deleted_at` | `DATETIME2(3)` | Yes |  | Thời điểm đưa vào thùng rác |
| `restore_until` | `DATETIME2(3)` | Yes |  | Hạn khôi phục trước khi cleanup/historical transition |
| `deleted_by_user_id` | `BIGINT` | Yes |  | Người thực hiện xóa |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `course_id` | `courses(id)` | `NO ACTION` |  |
| `deleted_by_user_id` | `users(id)` | `SET NULL` |  |

### Unique Constraints

- `UNIQUE (public_id)`
- `UNIQUE (course_id, position)`

### Check Constraints

- `position > 0`
- `estimated_duration_minutes IS NULL OR estimated_duration_minutes > 0`
- `minimum_completion_seconds >= 0`
- `viewed_fraction_required >= 0 AND viewed_fraction_required <= 1`
- `status IN ('DRAFT','PUBLISHED','HIDDEN','TRASH','HISTORICAL')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_lessons_course_status_position` | `course_id, status, position` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Không cascade LessonProgress lịch sử. Unused Lesson có thể hard-delete sau recovery.

### Audit behavior

Reorder/material edit/delete audit; material edit của published Course qua approval.

### Concurrency

row_version; reorder toàn Course trong transaction với temporary positions/locking.

### Security / PII classification

Markdown untrusted; output phải sanitize + CSP.

### Important invariants

- Completed Student không bị uncomplete do rewrite
- Lesson mới không làm existing period tụt progress: required_for_periods_starting_at quyết định eligibility

---

## `enrollments`

**Purpose**

Một logical Enrollment duy nhất cho mỗi Student-Course; re-enroll tái sử dụng row và mở period mới.

**Lifecycle**

ACTIVE ↔ LEFT qua re-enroll; COMPLETED là current cycle; RETENTION_PENDING/DETAIL_PURGED phản ánh cleanup chi tiết của period cũ.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `public_id` | `UNIQUEIDENTIFIER` | No | `NEWSEQUENTIALID()` | ID công khai dùng trong URL/API; không thay thế kiểm tra quyền |
| `student_user_id` | `BIGINT` | No |  | Student |
| `course_id` | `BIGINT` | No |  | Course |
| `status` | `VARCHAR(24)` | No | `'ACTIVE'` | ACTIVE/LEFT/COMPLETED/RETENTION_PENDING/DETAIL_PURGED |
| `current_period_id` | `BIGINT` | Yes |  | Period hiện hành; FK deferred sau enrollment_periods |
| `current_progress_percent` | `DECIMAL(5,2)` | No | `0` | Cache derived; không phải source of truth |
| `enrolled_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Lần enroll/re-enroll hiện hành |
| `left_at` | `DATETIME2(3)` | Yes |  | Lần rời gần nhất |
| `completed_at` | `DATETIME2(3)` | Yes |  | Lần current cycle hoàn thành |
| `detail_retention_due_at` | `DATETIME2(3)` | Yes |  | Mốc cleanup detail của period đã rời |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `updated_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm cập nhật cuối (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `student_user_id` | `users(id)` | `NO ACTION` |  |
| `course_id` | `courses(id)` | `NO ACTION` |  |
| `current_period_id` | `enrollment_periods(id)` | `SET NULL` | Deferred cross-domain FK created in `010_cross_domain_constraints.sql`. |

### Unique Constraints

- `UNIQUE (public_id)`
- `UNIQUE (student_user_id, course_id)`

### Check Constraints

- `status IN ('ACTIVE','LEFT','COMPLETED','RETENTION_PENDING','DETAIL_PURGED')`
- `current_progress_percent >= 0 AND current_progress_percent <= 100`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_enrollments_course_status` | `course_id, status, student_user_id` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_enrollments_student_status` | `student_user_id, status, course_id` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_enrollments_retention` | `detail_retention_due_at, status` | No | `detail_retention_due_at IS NOT NULL` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Không hard-delete logical Enrollment nếu có compact summary/history.

### Audit behavior

Enroll/leave/re-enroll/completion chủ yếu qua enrollment_events; admin changes audit.

### Concurrency

row_version; enroll/re-enroll/capacity trong transaction khóa Course row.

### Security / PII classification

Student data; Instructor chỉ Course mình quản lý.

### Important invariants

- Unique Student-Course
- Chỉ một active period
- current_progress_percent là cache, recompute từ LessonProgress/AssessmentResult

---

## `enrollment_periods`

**Purpose**

Phân đoạn các lần học bên dưới cùng logical Enrollment để reset khi re-enroll và purge đúng period.

**Lifecycle**

ACTIVE → LEFT/COMPLETED; LEFT → PURGED sau 30 ngày nếu không cần giữ detail. Re-enroll tạo period_no mới nhưng cùng Enrollment.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `enrollment_id` | `BIGINT` | No |  | Logical Enrollment |
| `period_no` | `INT` | No |  | 1,2,3... |
| `started_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Bắt đầu period |
| `left_at` | `DATETIME2(3)` | Yes |  | Rời period |
| `completed_at` | `DATETIME2(3)` | Yes |  | Hoàn thành trong period |
| `retention_due_at` | `DATETIME2(3)` | Yes |  | left_at + 30 ngày nếu không rejoin |
| `detail_purged_at` | `DATETIME2(3)` | Yes |  | Đã xóa dữ liệu chi tiết |
| `status` | `VARCHAR(20)` | No | `'ACTIVE'` | ACTIVE/LEFT/COMPLETED/PURGED |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `enrollment_id` | `enrollments(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (enrollment_id, period_no)`

### Check Constraints

- `period_no > 0`
- `status IN ('ACTIVE','LEFT','COMPLETED','PURGED')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_enrollment_periods_retention` | `retention_due_at, status` | No | `retention_due_at IS NOT NULL` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_enrollment_periods_enrollment` | `enrollment_id, period_no` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ux_enrollment_period_active` | `enrollment_id` | Yes | `status='ACTIVE'` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Period header có thể giữ lâu dài hoặc compact; detail child có thể purge.

### Audit behavior

Lifecycle facts quan trọng phản chiếu trong enrollment_events.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Learning history.

### Important invariants

- Tối đa một ACTIVE period/enrollment (service + filtered unique index đề xuất)
- Re-enroll luôn period mới/reset progress

---

## `enrollment_events`

**Purpose**

Lịch sử nhỏ, append-only cho enroll/leave/re-enroll/completion/purge.

**Lifecycle**

Append-only.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `enrollment_id` | `BIGINT` | No |  | Enrollment |
| `period_id` | `BIGINT` | Yes |  | Period liên quan |
| `event_type` | `VARCHAR(24)` | No |  | ENROLLED/LEFT/REENROLLED/COMPLETED/DETAIL_PURGED |
| `actor_user_id` | `BIGINT` | Yes |  | Ai gây sự kiện |
| `reason` | `NVARCHAR(500)` | Yes |  | Lý do nếu có |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `enrollment_id` | `enrollments(id)` | `NO ACTION` |  |
| `period_id` | `enrollment_periods(id)` | `SET NULL` |  |
| `actor_user_id` | `users(id)` | `SET NULL` |  |

### Unique Constraints

_None._

### Check Constraints

- `event_type IN ('ENROLLED','LEFT','REENROLLED','COMPLETED','DETAIL_PURGED')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_enrollment_events_enrollment` | `enrollment_id, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Giữ compact history; không phụ thuộc detail purge.

### Audit behavior

Business history, không thay AuditEvent cho sensitive admin action.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Learning history.

### Important invariants

- Không update existing event

---

## `lesson_progress`

**Purpose**

Source of truth cho tiến độ Lesson trong từng enrollment period.

**Lifecycle**

Tạo khi bắt đầu học; cộng dần; completed_at một chiều trong period.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `enrollment_period_id` | `BIGINT` | No |  | Period |
| `lesson_id` | `BIGINT` | No |  | Lesson |
| `seconds_spent` | `INT` | No | `0` | Thời gian server chấp nhận |
| `max_view_fraction` | `DECIMAL(5,4)` | No | `0` | Tỷ lệ lớn nhất quan sát được |
| `last_activity_at` | `DATETIME2(3)` | Yes |  | Heartbeat/view gần nhất |
| `completed_at` | `DATETIME2(3)` | Yes |  | Đạt điều kiện completion |
| `completion_rule_snapshot_json` | `NVARCHAR(MAX)` | Yes |  | Ngưỡng tối thiểu tại lúc complete để giải thích lịch sử |
| `updated_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm cập nhật cuối (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `enrollment_period_id` | `enrollment_periods(id)` | `NO ACTION` |  |
| `lesson_id` | `lessons(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (enrollment_period_id, lesson_id)`

### Check Constraints

- `seconds_spent >= 0`
- `max_view_fraction >= 0 AND max_view_fraction <= 1`
- `completion_rule_snapshot_json IS NULL OR ISJSON(completion_rule_snapshot_json)=1`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_lesson_progress_period_complete` | `enrollment_period_id, completed_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Purge theo enrollment period retention; completed Course proof nằm summary.

### Audit behavior

Không audit mỗi heartbeat; completion có event/derived log nếu cần.

### Concurrency

row_version/atomic bounded increments để tránh multi-tab overcount.

### Security / PII classification

Student learning data.

### Important invariants

- Client không được gửi trực tiếp completed=true; server xét seconds_spent + max_view_fraction
- Rewrite Lesson không xóa completed_at

---

## `course_completion_summaries`

**Purpose**

Compact historical summary giữ sau detail purge và làm bằng chứng prerequisite.

**Lifecycle**

Upsert khi completion/result quan trọng; tồn tại sau detail purge.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `student_user_id` | `BIGINT` | No |  | Student |
| `course_id` | `BIGINT` | No |  | Course |
| `ever_completed` | `BIT` | No | `0` | Đã từng complete |
| `first_completed_at` | `DATETIME2(3)` | Yes |  | Lần complete đầu |
| `latest_completed_at` | `DATETIME2(3)` | Yes |  | Lần complete gần nhất |
| `final_aggregate_score` | `DECIMAL(9,4)` | Yes |  | Kết quả tổng hợp cuối cần giữ |
| `prerequisite_eligible` | `BIT` | No | `0` | Có thỏa prerequisite lịch sử |
| `source_period_id` | `BIGINT` | Yes |  | Period tạo summary gần nhất |
| `updated_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | UTC |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `student_user_id` | `users(id)` | `NO ACTION` |  |
| `course_id` | `courses(id)` | `NO ACTION` |  |
| `source_period_id` | `enrollment_periods(id)` | `SET NULL` |  |

### Unique Constraints

- `UNIQUE (student_user_id, course_id)`

### Check Constraints

- `final_aggregate_score IS NULL OR final_aggregate_score >= 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_completion_summary_student` | `student_user_id, prerequisite_eligible, course_id` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Không xóa chỉ vì Student leave; anonymization giữ user FK đã anonymized.

### Audit behavior

Điểm tổng thay đổi do nghiệp vụ quan trọng cần score/audit history ở nguồn.

### Concurrency

row_version.

### Security / PII classification

Historical learning result.

### Important invariants

- ever_completed không tự trở về 0 do rule Course thay đổi hoặc re-enroll
- prerequisite eligibility vẫn giữ nếu prior completion hợp lệ

---
# 06 DATA DICTIONARY QUESTION BANK

Database engine: **Microsoft SQL Server**. Timestamps are UTC `DATETIME2(3)` unless noted.

## `questions`

**Purpose**

Identity ổn định của một Question trong đúng một Course; nội dung nằm ở revision.

**Lifecycle**

DRAFT → ACTIVE; có thể RETIRED/TRASH. Unused có thể hard-delete sau recovery.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `public_id` | `UNIQUEIDENTIFIER` | No | `NEWSEQUENTIALID()` | ID công khai dùng trong URL/API; không thay thế kiểm tra quyền |
| `course_id` | `BIGINT` | No |  | Course |
| `lesson_id` | `BIGINT` | Yes |  | Lesson tùy chọn |
| `creator_user_id` | `BIGINT` | Yes |  | Người tạo |
| `difficulty` | `VARCHAR(20)` | No |  | REMEMBER/UNDERSTAND/APPLY hoặc mức tương đương |
| `learning_objective` | `NVARCHAR(500)` | Yes |  | Mục tiêu học tập |
| `status` | `VARCHAR(20)` | No | `'DRAFT'` | DRAFT/ACTIVE/RETIRED/TRASH |
| `current_revision_id` | `BIGINT` | Yes |  | Revision active; FK deferred sau question_revisions |
| `first_used_at` | `DATETIME2(3)` | Yes |  | Lần đầu được đưa vào Assessment/pool |
| `first_answered_at` | `DATETIME2(3)` | Yes |  | Lần đầu Student trả lời; từ đây type không được đổi |
| `usage_count` | `BIGINT` | No | `0` | Cache số lần được gán vào Attempt |
| `last_used_at` | `DATETIME2(3)` | Yes |  | Cache phục vụ ưu tiên ít dùng |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `updated_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm cập nhật cuối (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |
| `deleted_at` | `DATETIME2(3)` | Yes |  | Thời điểm đưa vào thùng rác |
| `restore_until` | `DATETIME2(3)` | Yes |  | Hạn khôi phục trước khi cleanup/historical transition |
| `deleted_by_user_id` | `BIGINT` | Yes |  | Người thực hiện xóa |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `course_id` | `courses(id)` | `NO ACTION` |  |
| `lesson_id` | `lessons(id)` | `SET NULL` |  |
| `creator_user_id` | `users(id)` | `NO ACTION` | Preserve creator linkage; User is anonymized in place when required. |
| `deleted_by_user_id` | `users(id)` | `NO ACTION` | Preserve deletion actor linkage. |
| `current_revision_id` | `question_revisions(id)` | `SET NULL` | Deferred cross-domain FK created in `010_cross_domain_constraints.sql`. |

### Unique Constraints

- `UNIQUE (public_id)`

### Check Constraints

- `difficulty IN ('REMEMBER','UNDERSTAND','APPLY')`
- `status IN ('DRAFT','ACTIVE','RETIRED','TRASH')`
- `usage_count >= 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_questions_bank_filter` | `course_id, lesson_id, difficulty, status, id` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_questions_usage` | `course_id, last_used_at, usage_count` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Đã có Student answer: không hard-delete source identity/revisions cần grading/audit; chỉ RETIRED sau recovery.

### Audit behavior

Important edit/delete/provenance changes audit.

### Concurrency

row_version; revision creation transaction khóa Question.

### Security / PII classification

Instructor owner Course/Admin.

### Important invariants

- Thuộc đúng một Course
- lesson nếu có phải thuộc cùng course (service)
- current_revision_id trỏ revision cùng question
- type không đổi sau first_answered_at

---

## `question_revisions`

**Purpose**

Phiên bản nội dung/loại/đáp án semantics của Question. Choices/accepted answers thuộc revision.

**Lifecycle**

Unused Question có thể edit current revision in-place theo service; sau first_used_at, important edit tạo revision_no mới. Revision exposed/graded giữ vô thời hạn.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `question_id` | `BIGINT` | No |  | Question |
| `revision_no` | `INT` | No |  | Tăng tuần tự |
| `question_type` | `VARCHAR(24)` | No |  | SINGLE_CHOICE/MULTIPLE_CHOICE/TRUE_FALSE/SHORT_ANSWER/ESSAY |
| `content` | `NVARCHAR(MAX)` | No |  | Nội dung câu hỏi |
| `explanation` | `NVARCHAR(MAX)` | Yes |  | Lời giải/giải thích |
| `short_answer_match_mode` | `VARCHAR(16)` | Yes |  | NORMALIZED/EXACT |
| `change_type` | `VARCHAR(24)` | No | `'EDIT'` | INITIAL/EDIT/ANSWER_ONLY/CONTENT_OR_CHOICES |
| `change_reason` | `NVARCHAR(1000)` | Yes |  | Lý do chỉnh sửa/correction |
| `created_by_user_id` | `BIGINT` | Yes |  | Người tạo revision |
| `approved_by_user_id` | `BIGINT` | Yes |  | Người xác nhận nếu từ AI/import |
| `approved_at` | `DATETIME2(3)` | Yes |  | UTC |
| `was_student_exposed` | `BIT` | No | `0` | Đã từng Student thấy |
| `was_used_for_grading` | `BIT` | No | `0` | Đã dùng để grading |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `question_id` | `questions(id)` | `NO ACTION` |  |
| `created_by_user_id` | `users(id)` | `NO ACTION` | Preserve revision provenance. |
| `approved_by_user_id` | `users(id)` | `NO ACTION` | Preserve approval provenance. |

### Unique Constraints

- `UNIQUE (question_id, revision_no)`

### Check Constraints

- `revision_no > 0`
- `question_type IN ('SINGLE_CHOICE','MULTIPLE_CHOICE','TRUE_FALSE','SHORT_ANSWER','ESSAY')`
- `short_answer_match_mode IS NULL OR short_answer_match_mode IN ('NORMALIZED','EXACT')`
- `change_type IN ('INITIAL','EDIT','ANSWER_ONLY','CONTENT_OR_CHOICES')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_question_revisions_question` | `question_id, revision_no` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_question_revisions_exposure` | `was_student_exposed, was_used_for_grading` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Chỉ cleanup revision chưa từng exposed/graded và không current sau policy. Exposed/graded không hard-delete.

### Audit behavior

Correction reason/actor/time là business history; AuditEvent cho sensitive admin/instructor corrections.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Correct answer data không serialize cho Student trước policy release.

### Important invariants

- revision_no monotonic per question
- Type change bị chặn nếu questions.first_answered_at không NULL
- ANSWER_ONLY chỉ thay answer key, không content/choice text

---

## `question_revision_choices`

**Purpose**

Choices immutable theo từng QuestionRevision; correct flag không bao giờ gửi trong Student attempt payload.

**Lifecycle**

Tạo cùng revision; không mutate khi revision đã exposed/graded.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `question_revision_id` | `BIGINT` | No |  | Revision |
| `choice_key` | `UNIQUEIDENTIFIER` | No | `NEWID()` | ID ổn định trong revision |
| `content` | `NVARCHAR(MAX)` | No |  | Nội dung lựa chọn |
| `is_correct` | `BIT` | No | `0` | Thuộc đáp án đúng |
| `position` | `INT` | No |  | Thứ tự chuẩn |
| `is_fixed_position` | `BIT` | No | `0` | Không shuffle nếu bật |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `question_revision_id` | `question_revisions(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (question_revision_id, choice_key)`
- `UNIQUE (question_revision_id, position)`

### Check Constraints

- `position > 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_question_choices_revision` | `question_revision_id, position` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

CASCADE chỉ khi revision được phép hard-delete; exposed revision thì giữ.

### Audit behavior

Thông qua QuestionRevision/AuditEvent.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

is_correct rất nhạy cảm trong exam context.

### Important invariants

- Choice thuộc đúng revision
- Single-choice/TF phải có đúng 1 correct; multiple-choice >=1 correct (service preflight)

---

## `question_revision_accepted_answers`

**Purpose**

Đáp án chấp nhận cho SHORT_ANSWER theo revision.

**Lifecycle**

Theo revision.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `question_revision_id` | `BIGINT` | No |  | Revision |
| `answer_text` | `NVARCHAR(1000)` | No |  | Đáp án gốc |
| `answer_normalized` | `NVARCHAR(1000)` | No |  | Trim + lowercase cho NORMALIZED; service tính |
| `position` | `INT` | No | `1` | Thứ tự hiển thị/quản trị |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `question_revision_id` | `question_revisions(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (question_revision_id, answer_normalized)`

### Check Constraints

- `position > 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_accepted_answers_revision` | `question_revision_id, position` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Theo revision retention.

### Audit behavior

Thông qua revision.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Answer key; không expose trước policy.

### Important invariants

- Chỉ dùng cho SHORT_ANSWER
- EXACT mode so sánh answer_text; NORMALIZED dùng answer_normalized

---

## `question_provenance`

**Purpose**

Nguồn gốc Question/Revision: manual, import, AI-generated, duplicate; giữ traceability không phụ thuộc source record sống mãi.

**Lifecycle**

Append thêm provenance khi cần; không rewrite AI origin dù Instructor sửa mạnh.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `question_id` | `BIGINT` | No |  | Question |
| `question_revision_id` | `BIGINT` | Yes |  | Revision cụ thể |
| `source_type` | `VARCHAR(24)` | No |  | MANUAL/IMPORT/AI_GENERATED/DUPLICATED |
| `source_ref_type` | `VARCHAR(32)` | Yes |  | Tên loại nguồn |
| `source_ref_id` | `BIGINT` | Yes |  | ID nguồn nếu còn |
| `source_question_id` | `BIGINT` | Yes |  | Question gốc nếu DUPLICATED |
| `ai_model` | `NVARCHAR(100)` | Yes |  | Model tạo/gợi ý |
| `generated_at` | `DATETIME2(3)` | Yes |  | UTC |
| `approved_by_user_id` | `BIGINT` | Yes |  | Instructor approve |
| `approved_at` | `DATETIME2(3)` | Yes |  | UTC |
| `notes` | `NVARCHAR(1000)` | Yes |  | Metadata provenance ngắn |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `question_id` | `questions(id)` | `NO ACTION` |  |
| `question_revision_id` | `question_revisions(id)` | `SET NULL` |  |
| `source_question_id` | `questions(id)` | `SET NULL` |  |
| `approved_by_user_id` | `users(id)` | `SET NULL` |  |

### Unique Constraints

_None._

### Check Constraints

- `source_type IN ('MANUAL','IMPORT','AI_GENERATED','DUPLICATED')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_question_provenance_question` | `question_id, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_question_provenance_source` | `source_type, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Giữ cùng historical Question; source_ref có thể orphan hợp lệ.

### Audit behavior

Approval AI/import audit riêng khi quan trọng.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Không chứa raw prompt; chỉ metadata nguồn.

### Important invariants

- AI-generated draft chỉ tạo Question sau explicit Instructor approval

---
# 07 DATA DICTIONARY ASSESSMENT

Database engine: **Microsoft SQL Server**. Timestamps are UTC `DATETIME2(3)` unless noted.

## `assessments`

**Purpose**

Định nghĩa bài đánh giá dùng chung engine; timing khóa ngay sau publish, structure/points khóa khi Student đầu tiên start.

**Lifecycle**

DRAFT → PUBLISHED; open/closed được derive từ server time + open_at/close_at; có thể CANCELLED/ARCHIVED/TRASH.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `public_id` | `UNIQUEIDENTIFIER` | No | `NEWSEQUENTIALID()` | ID công khai dùng trong URL/API; không thay thế kiểm tra quyền |
| `course_id` | `BIGINT` | No |  | Course |
| `creator_user_id` | `BIGINT` | Yes |  | Instructor/Admin |
| `title` | `NVARCHAR(200)` | No |  | Tên Assessment |
| `description` | `NVARCHAR(MAX)` | Yes |  | Mô tả |
| `assessment_type` | `VARCHAR(20)` | No |  | PRACTICE/QUIZ/MIDTERM/FINAL/PLACEMENT |
| `status` | `VARCHAR(20)` | No | `'DRAFT'` | DRAFT/PUBLISHED/CANCELLED/ARCHIVED/TRASH |
| `open_at` | `DATETIME2(3)` | Yes |  | Giờ mở |
| `close_at` | `DATETIME2(3)` | Yes |  | Giờ đóng cứng |
| `time_limit_minutes` | `INT` | Yes |  | Giới hạn thời gian |
| `attempt_limit` | `INT` | Yes |  | NULL = không giới hạn |
| `scoring_policy` | `VARCHAR(20)` | No | `'HIGHEST'` | FIRST/LATEST/HIGHEST/AVERAGE |
| `passing_percent` | `DECIMAL(5,2)` | Yes |  | Ngưỡng đạt |
| `is_required_for_completion` | `BIT` | No | `0` | Có ảnh hưởng Course completion |
| `shuffle_questions` | `BIT` | No | `0` | Trộn câu |
| `shuffle_choices` | `BIT` | No | `0` | Trộn choice mặc định |
| `score_release_policy` | `VARCHAR(24)` | No | `'IMMEDIATE'` | IMMEDIATE/AFTER_CLOSE/INSTRUCTOR_RELEASE |
| `answer_visibility_policy` | `VARCHAR(32)` | No | `'AFTER_CLOSE'` | IMMEDIATE/AFTER_CLOSE/AFTER_ALL_ATTEMPTS/NEVER |
| `random_question_count` | `INT` | Yes |  | Tổng số câu chọn ngẫu nhiên nếu dùng pool |
| `published_at` | `DATETIME2(3)` | Yes |  | Mốc publish đầu tiên; một khi đã set thì không được clear/đổi, và timing immutable từ mốc này |
| `first_attempt_started_at` | `DATETIME2(3)` | Yes |  | Marker khóa structure/points |
| `cancelled_at` | `DATETIME2(3)` | Yes |  | UTC |
| `cancel_reason` | `NVARCHAR(1000)` | Yes |  | Lý do hủy |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `updated_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm cập nhật cuối (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |
| `deleted_at` | `DATETIME2(3)` | Yes |  | Thời điểm đưa vào thùng rác |
| `restore_until` | `DATETIME2(3)` | Yes |  | Hạn khôi phục trước khi cleanup/historical transition |
| `deleted_by_user_id` | `BIGINT` | Yes |  | Người thực hiện xóa |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `course_id` | `courses(id)` | `NO ACTION` |  |
| `creator_user_id` | `users(id)` | `NO ACTION` | Preserve creator history; User is anonymized in place when required. |
| `deleted_by_user_id` | `users(id)` | `NO ACTION` | Preserve deletion actor history. |

### Unique Constraints

- `UNIQUE (public_id)`

### Check Constraints

- `assessment_type IN ('PRACTICE','QUIZ','MIDTERM','FINAL','PLACEMENT')`
- `status IN ('DRAFT','PUBLISHED','CANCELLED','ARCHIVED','TRASH')`
- `time_limit_minutes IS NULL OR time_limit_minutes > 0`
- `attempt_limit IS NULL OR attempt_limit > 0`
- `scoring_policy IN ('FIRST','LATEST','HIGHEST','AVERAGE')`
- `passing_percent IS NULL OR (passing_percent >= 0 AND passing_percent <= 100)`
- `score_release_policy IN ('IMMEDIATE','AFTER_CLOSE','INSTRUCTOR_RELEASE')`
- `answer_visibility_policy IN ('IMMEDIATE','AFTER_CLOSE','AFTER_ALL_ATTEMPTS','NEVER')`
- `random_question_count IS NULL OR random_question_count > 0`
- `open_at IS NULL OR close_at IS NULL OR open_at < close_at`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_assessments_course_status` | `course_id, status, open_at, close_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_assessments_pending_window` | `status, open_at, close_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

No-attempt có thể hard-delete sau recovery. Có attempts: archive/historical, không cascade.

### Audit behavior

Publish/cancel/delete/timing config before publish/material edits audit.

### Concurrency

row_version; publish/start dùng transaction; critical locks enforced by triggers + service.

### Security / PII classification

Instructor owner Course/Admin. Student chỉ thấy published + authorized fields.

### Important invariants

- `published_at` là write-once marker; sau khi set không được clear/đổi và không update open_at/close_at/time_limit
- `first_attempt_started_at` là write-once marker; sau khi set không được clear/đổi và không thay structure/points
- Close là hard boundary

---

## `assessment_sections`

**Purpose**

Nhóm câu tùy chọn trong Assessment; hỗ trợ structure rõ nhưng không bắt buộc.

**Lifecycle**

Editable trước first start; sau đó structure locked.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `assessment_id` | `BIGINT` | No |  | Assessment |
| `title` | `NVARCHAR(200)` | Yes |  | Tên section |
| `position` | `INT` | No |  | Thứ tự |
| `instructions` | `NVARCHAR(MAX)` | Yes |  | Hướng dẫn |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `assessment_id` | `assessments(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (assessment_id, position)`

### Check Constraints

- `position > 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_assessment_sections` | `assessment_id, position` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

CASCADE chỉ khi Assessment chưa có attempt và được hard-delete; service chặn thay đổi sau first start.

### Audit behavior

Structural change audit khi published/pre-start.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Instructor/Admin.

### Important invariants

- Không insert/delete/reorder sau assessments.first_attempt_started_at

---

## `assessment_question_assignments`

**Purpose**

Câu tĩnh được đưa trực tiếp vào Assessment; thường luôn xuất hiện.

**Lifecycle**

Editable đến first start; sau đó immutable structure/points.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `assessment_id` | `BIGINT` | No |  | Assessment |
| `section_id` | `BIGINT` | Yes |  | Section |
| `question_id` | `BIGINT` | No |  | Question identity; Attempt sẽ resolve latest current revision tại start |
| `position` | `INT` | No |  | Vị trí chuẩn |
| `points` | `DECIMAL(9,4)` | No |  | Điểm của câu trong Assessment |
| `is_mandatory` | `BIT` | No | `1` | Bắt buộc xuất hiện |
| `shuffle_choices_override` | `BIT` | Yes |  | NULL dùng Assessment default |
| `source_type` | `VARCHAR(20)` | No | `'BANK'` | MANUAL/BANK/IMPORT/AI |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `assessment_id` | `assessments(id)` | `NO ACTION` |  |
| `section_id` | `assessment_sections(id)` | `SET NULL` |  |
| `question_id` | `questions(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (assessment_id, question_id)`

### Check Constraints

- `position > 0`
- `points > 0`
- `source_type IN ('MANUAL','BANK','IMPORT','AI')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_assessment_assignments_position` | `assessment_id, position` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Không xóa sau first start; trước đó application-managed.

### Audit behavior

Add/remove/points change sau publish-prestart audit.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Instructor owner/Admin.

### Important invariants

- Question phải thuộc same Course
- Question revision không pin ở đây theo latest-revision rule
- points locked after first start

---

## `assessment_blueprints`

**Purpose**

Ma trận chọn câu tự động cho Assessment.

**Lifecycle**

DRAFT → READY; FROZEN khi first attempt start/materialization locked.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `assessment_id` | `BIGINT` | No |  | Assessment |
| `name` | `NVARCHAR(200)` | No |  | Tên blueprint |
| `status` | `VARCHAR(16)` | No | `'DRAFT'` | DRAFT/READY/FROZEN |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `updated_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm cập nhật cuối (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `assessment_id` | `assessments(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (assessment_id, name)`

### Check Constraints

- `status IN ('DRAFT','READY','FROZEN')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_blueprints_assessment` | `assessment_id, status` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Editable/delete trước first start; giữ khi attempts tồn tại.

### Audit behavior

Blueprint structural changes audit.

### Concurrency

row_version.

### Security / PII classification

Instructor/Admin.

### Important invariants

- Không thay rule sau first start

---

## `assessment_blueprint_rules`

**Purpose**

Một dòng điều kiện ma trận: lesson/difficulty/type/count/points.

**Lifecycle**

Theo blueprint; frozen sau first start.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `blueprint_id` | `BIGINT` | No |  | Blueprint |
| `section_id` | `BIGINT` | Yes |  | Section |
| `lesson_id` | `BIGINT` | Yes |  | Lesson filter |
| `difficulty` | `VARCHAR(20)` | Yes |  | Difficulty filter |
| `question_type` | `VARCHAR(24)` | Yes |  | Type filter |
| `question_count` | `INT` | No |  | Số cần lấy |
| `points_each` | `DECIMAL(9,4)` | No |  | Điểm mỗi câu |
| `position` | `INT` | No | `1` | Thứ tự rule |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `blueprint_id` | `assessment_blueprints(id)` | `NO ACTION` |  |
| `section_id` | `assessment_sections(id)` | `SET NULL` |  |
| `lesson_id` | `lessons(id)` | `SET NULL` |  |

### Unique Constraints

- `UNIQUE (blueprint_id, position)`

### Check Constraints

- `question_count > 0`
- `points_each > 0`
- `position > 0`
- `difficulty IS NULL OR difficulty IN ('REMEMBER','UNDERSTAND','APPLY')`
- `question_type IS NULL OR question_type IN ('SINGLE_CHOICE','MULTIPLE_CHOICE','TRUE_FALSE','SHORT_ANSWER','ESSAY')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_blueprint_rules_filter` | `blueprint_id, lesson_id, difficulty, question_type` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

CASCADE khi blueprint disposable; historical attempts không reference rule trực tiếp bắt buộc.

### Audit behavior

Structural changes audit.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Instructor/Admin.

### Important invariants

- Preflight phải chứng minh đủ candidate trước publish
- points/count locked after first start

---

## `assessment_question_pool`

**Purpose**

Pool candidate đã materialize/curate để randomize ổn định; ngăn pool tự thay đổi âm thầm sau first start.

**Lifecycle**

Materialize/refresh trước first start; frozen sau first start.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `assessment_id` | `BIGINT` | No |  | Assessment |
| `blueprint_rule_id` | `BIGINT` | Yes |  | Rule nguồn |
| `question_id` | `BIGINT` | No |  | Question identity |
| `points` | `DECIMAL(9,4)` | No |  | Điểm nếu được chọn |
| `is_fixed` | `BIT` | No | `0` | Nếu 1 thì luôn chọn |
| `position_hint` | `INT` | Yes |  | Gợi ý order nếu không shuffle |
| `selection_source` | `VARCHAR(20)` | No | `'BLUEPRINT'` | BLUEPRINT/MANUAL_POOL/IMPORT/AI |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `assessment_id` | `assessments(id)` | `NO ACTION` |  |
| `blueprint_rule_id` | `assessment_blueprint_rules(id)` | `SET NULL` |  |
| `question_id` | `questions(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (assessment_id, question_id)`

### Check Constraints

- `points > 0`
- `position_hint IS NULL OR position_hint > 0`
- `selection_source IN ('BLUEPRINT','MANUAL_POOL','IMPORT','AI')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_assessment_pool_rule` | `assessment_id, blueprint_rule_id, is_fixed, question_id` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Không add/remove/points change sau first start.

### Audit behavior

Pool refresh/add/remove audit khi published.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Instructor/Admin.

### Important invariants

- Question phải thuộc same Course
- Pool shortage block publish/finalization
- Future Attempt chọn trong frozen pool nhưng resolve latest valid QuestionRevision

---
# 08 DATA DICTIONARY ATTEMPT REGRADING

Database engine: **Microsoft SQL Server**. Timestamps are UTC `DATETIME2(3)` unless noted.

## `assessment_attempts`

**Purpose**

Một lượt làm bài cụ thể của Student, chứa timer authoritative, lease tab, submit idempotency và lifecycle.

**Lifecycle**

CREATED → IN_PROGRESS → SUBMITTED/EXPIRED → PENDING_GRADING/GRADED; Assessment cancel có thể → CANCELLED.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `public_id` | `UNIQUEIDENTIFIER` | No | `NEWSEQUENTIALID()` | ID công khai dùng trong URL/API; không thay thế kiểm tra quyền |
| `assessment_id` | `BIGINT` | No |  | Assessment |
| `enrollment_period_id` | `BIGINT` | No |  | Period học hiện hành |
| `student_user_id` | `BIGINT` | No |  | Student |
| `attempt_number` | `INT` | No |  | Lần làm 1..N |
| `status` | `VARCHAR(28)` | No |  | CREATED/IN_PROGRESS/SUBMITTED/EXPIRED/CANCELLED/PENDING_GRADING/GRADED |
| `started_at` | `DATETIME2(3)` | Yes |  | Server start |
| `deadline_at` | `DATETIME2(3)` | Yes |  | min(start+time_limit, close_at) |
| `submitted_at` | `DATETIME2(3)` | Yes |  | Submit client/server |
| `finalized_at` | `DATETIME2(3)` | Yes |  | Server finalize |
| `graded_at` | `DATETIME2(3)` | Yes |  | Final grading complete |
| `submission_idempotency_key` | `UNIQUEIDENTIFIER` | Yes |  | Key lần submit đầu; retry trả same result |
| `editor_session_id` | `BIGINT` | Yes |  | Auth session đang giữ quyền edit |
| `lease_token_hash` | `BINARY(32)` | Yes |  | Hash lease token, không lưu raw |
| `lease_acquired_at` | `DATETIME2(3)` | Yes |  | UTC |
| `lease_expires_at` | `DATETIME2(3)` | Yes |  | UTC |
| `last_heartbeat_at` | `DATETIME2(3)` | Yes |  | UTC |
| `cancel_reason` | `NVARCHAR(1000)` | Yes |  | Nếu cancelled |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `updated_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm cập nhật cuối (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `assessment_id` | `assessments(id)` | `NO ACTION` |  |
| `enrollment_period_id` | `enrollment_periods(id)` | `NO ACTION` |  |
| `student_user_id` | `users(id)` | `NO ACTION` |  |
| `editor_session_id` | `auth_sessions(id)` | `SET NULL` |  |

### Unique Constraints

- `UNIQUE (public_id)`
- `UNIQUE (assessment_id, student_user_id, attempt_number)`

### Check Constraints

- `attempt_number > 0`
- `status IN ('CREATED','IN_PROGRESS','SUBMITTED','EXPIRED','CANCELLED','PENDING_GRADING','GRADED')`
- `deadline_at IS NULL OR started_at IS NULL OR deadline_at >= started_at`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_attempts_student_assessment` | `student_user_id, assessment_id, attempt_number` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_attempts_assessment_status` | `assessment_id, status, started_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_attempts_period_status` | `enrollment_period_id, status` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_attempts_lease_expiry` | `lease_expires_at, status` | No | `status='IN_PROGRESS'` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ux_attempt_submit_key` | `submission_idempotency_key` | Yes | `submission_idempotency_key IS NOT NULL` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Detailed attempt có thể purge sau Enrollment period retention >30 ngày; nếu còn trong retention/history thì không cascade-delete. Assessment itself vẫn giữ historical integrity.

### Audit behavior

Không audit mọi autosave; submit/manual grade/regrade/cancel quan trọng được lưu domain history.

### Concurrency

row_version + short transaction. Lease dùng expiry/heartbeat, không giữ DB row lock dài hạn.

### Security / PII classification

Student-sensitive; ownership phải khớp authenticated user.

### Important invariants

- Server time authoritative
- Attempt count/limit transaction-safe
- Only one active editor lease
- submit idempotent
- deadline never extended by client clock

---

## `attempt_questions`

**Purpose**

Snapshot đầy đủ của câu mà Student thực sự thấy; không đổi khi QuestionRevision tương lai thay đổi.

**Lifecycle**

Insert atomic khi start Attempt; immutable ngoại trừ marker correction metadata.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `attempt_id` | `BIGINT` | No |  | Attempt |
| `source_question_id` | `BIGINT` | No |  | Question identity |
| `source_question_revision_id` | `BIGINT` | No |  | Revision hiển thị ban đầu |
| `section_id` | `BIGINT` | Yes |  | Section source |
| `position` | `INT` | No |  | Thứ tự thật trong Attempt |
| `question_type_snapshot` | `VARCHAR(24)` | No |  | Type student saw |
| `content_snapshot` | `NVARCHAR(MAX)` | No |  | Question text snapshot |
| `explanation_snapshot` | `NVARCHAR(MAX)` | Yes |  | Explanation snapshot để reveal đúng historical content |
| `points_assigned` | `DECIMAL(9,4)` | No |  | Điểm cố định trong Attempt |
| `choice_shuffle_applied` | `BIT` | No | `0` | Có shuffle choices |
| `question_changed_after_start_at` | `DATETIME2(3)` | Yes |  | Mốc content correction gây full credit |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `attempt_id` | `assessment_attempts(id)` | `NO ACTION` |  |
| `source_question_id` | `questions(id)` | `NO ACTION` |  |
| `source_question_revision_id` | `question_revisions(id)` | `NO ACTION` |  |
| `section_id` | `assessment_sections(id)` | `SET NULL` |  |

### Unique Constraints

- `UNIQUE (attempt_id, position)`
- `UNIQUE (attempt_id, source_question_id)`

### Check Constraints

- `position > 0`
- `points_assigned > 0`
- `question_type_snapshot IN ('SINGLE_CHOICE','MULTIPLE_CHOICE','TRUE_FALSE','SHORT_ANSWER','ESSAY')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_attempt_questions_attempt` | `attempt_id, position` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_attempt_questions_source` | `source_question_id, attempt_id` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_attempt_questions_revision` | `source_question_revision_id, attempt_id` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Theo retention của Attempt; source QuestionRevision vẫn có marker was_student_exposed để giữ lịch sử ngay cả sau purge.

### Audit behavior

Snapshot itself là evidence; không update content/order.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Không chứa correct answer flag; explanation chỉ API reveal khi policy cho phép.

### Important invariants

- Snapshot order/content/points không đổi
- source revision marked was_student_exposed=1 trong same transaction

---

## `attempt_choice_snapshots`

**Purpose**

Snapshot lựa chọn đúng thứ tự Student thấy, không lưu is_correct.

**Lifecycle**

Insert cùng Attempt snapshot; immutable.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `attempt_question_id` | `BIGINT` | No |  | AttemptQuestion |
| `source_choice_id` | `BIGINT` | Yes |  | Choice revision source |
| `choice_key_snapshot` | `UNIQUEIDENTIFIER` | No |  | Key choice snapshot |
| `content_snapshot` | `NVARCHAR(MAX)` | No |  | Choice text |
| `position` | `INT` | No |  | Thứ tự Student thấy |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `attempt_question_id` | `attempt_questions(id)` | `NO ACTION` |  |
| `source_choice_id` | `question_revision_choices(id)` | `SET NULL` |  |

### Unique Constraints

- `UNIQUE (attempt_question_id, position)`
- `UNIQUE (attempt_question_id, choice_key_snapshot)`

### Check Constraints

- `position > 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_attempt_choice_question` | `attempt_question_id, position` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Theo Attempt retention.

### Audit behavior

Historical evidence; no mutation.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Không lưu correct flag để giảm nguy cơ leak.

### Important invariants

- Choice order không đổi khi resume

---

## `attempt_answers`

**Purpose**

Trạng thái answer hiện hành của từng AttemptQuestion; source of truth để resume nhanh.

**Lifecycle**

Upsert khi autosave; final state giữ đến purge.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `attempt_question_id` | `BIGINT` | No |  | Question |
| `answer_text` | `NVARCHAR(MAX)` | Yes |  | Short answer/essay hiện hành |
| `answer_version` | `BIGINT` | No | `0` | Server version tăng mỗi accepted save |
| `last_client_sequence` | `BIGINT` | No | `0` | Sequence client cuối được áp dụng |
| `last_change_id` | `UNIQUEIDENTIFIER` | Yes |  | Change UUID cuối để dedupe |
| `saved_at` | `DATETIME2(3)` | Yes |  | Server ACK time |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `attempt_question_id` | `attempt_questions(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (attempt_question_id)`

### Check Constraints

- `answer_version >= 0`
- `last_client_sequence >= 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_attempt_answers_saved` | `saved_at, attempt_question_id` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Purge theo Attempt retention.

### Audit behavior

Chi tiết save history ở attempt_answer_events; không AuditEvent từng lần.

### Concurrency

Conditional update theo row_version + client_sequence + lease validation.

### Security / PII classification

Student answer sensitive.

### Important invariants

- Old offline change có sequence <= current không được overwrite newer answer
- Server ACK trước deadline mới hợp lệ để grading

---

## `attempt_answer_choices`

**Purpose**

Lựa chọn hiện hành cho câu choice; junction AttemptAnswer ↔ AttemptChoiceSnapshot.

**Lifecycle**

Replace atomically cùng answer save.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `attempt_answer_id` | `BIGINT` | No |  | AttemptAnswer |
| `attempt_choice_snapshot_id` | `BIGINT` | No |  | Selected snapshot |

### Primary Key

`attempt_answer_id, attempt_choice_snapshot_id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `attempt_answer_id` | `attempt_answers(id)` | `NO ACTION` |  |
| `attempt_choice_snapshot_id` | `attempt_choice_snapshots(id)` | `NO ACTION` |  |

### Unique Constraints

_None._

### Check Constraints

_None._

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_attempt_answer_choices_choice` | `attempt_choice_snapshot_id, attempt_answer_id` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

CASCADE only when answer detail purge.

### Audit behavior

Event payload giữ historical selection changes trong retention.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Student answer sensitive.

### Important invariants

- Selected choice phải thuộc cùng AttemptQuestion (service/transaction check)

---

## `attempt_answer_events`

**Purpose**

Log chi tiết từng thay đổi answer đã gửi/được chấp nhận, phục vụ resume/debug và retention 30 ngày.

**Lifecycle**

Append; cleanup theo detailed retention/autosave policy.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `attempt_question_id` | `BIGINT` | No |  | Question |
| `change_id` | `UNIQUEIDENTIFIER` | No |  | Client idempotency UUID |
| `client_sequence` | `BIGINT` | No |  | Monotonic per question/client synced state |
| `server_answer_version` | `BIGINT` | Yes |  | Version nếu accepted |
| `payload_json` | `NVARCHAR(MAX)` | No |  | Snapshot selection/text của change; detail retention |
| `received_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Server receive |
| `accepted` | `BIT` | No | `0` | Có áp dụng vào current answer |
| `rejection_reason` | `VARCHAR(40)` | Yes |  | STALE/LEASE_INVALID/AFTER_DEADLINE/INVALID_PAYLOAD |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `attempt_question_id` | `attempt_questions(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (attempt_question_id, change_id)`

### Check Constraints

- `client_sequence >= 0`
- `payload_json IS NOT NULL AND ISJSON(payload_json)=1`
- `rejection_reason IS NULL OR rejection_reason IN ('STALE','LEASE_INVALID','AFTER_DEADLINE','INVALID_PAYLOAD')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_answer_events_question_time` | `attempt_question_id, received_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_answer_events_cleanup` | `received_at, accepted` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Có thể hard-delete sau retention; current final answer/result giữ theo policy.

### Audit behavior

Không thay AuditEvent; high-volume technical history.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Có thể chứa raw answer text, nên retention ngắn và quyền xem hạn chế.

### Important invariants

- Retry same change_id không double apply
- Rejected event không update current answer

---

## `attempt_question_grades`

**Purpose**

Điểm hiện hành của từng AttemptQuestion, gồm auto/manual/full-credit correction.

**Lifecycle**

PENDING → graded; regrade/manual revise update current row và append history.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `attempt_question_id` | `BIGINT` | No |  | PK/FK |
| `awarded_points` | `DECIMAL(9,4)` | No | `0` | Điểm hiện tại |
| `grading_status` | `VARCHAR(20)` | No |  | PENDING/AUTO_GRADED/MANUAL_GRADED/FULL_CREDIT |
| `grading_rule` | `VARCHAR(32)` | No |  | ORIGINAL/ANSWER_CORRECTION/CONTENT_FULL_CREDIT/MANUAL |
| `graded_against_revision_id` | `BIGINT` | Yes |  | Revision answer key dùng để grading |
| `graded_by_user_id` | `BIGINT` | Yes |  | Instructor cho manual |
| `graded_at` | `DATETIME2(3)` | Yes |  | UTC |
| `manual_reason` | `NVARCHAR(1000)` | Yes |  | Lý do chỉnh manual |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`attempt_question_id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `attempt_question_id` | `attempt_questions(id)` | `NO ACTION` |  |
| `graded_against_revision_id` | `question_revisions(id)` | `SET NULL` |  |
| `graded_by_user_id` | `users(id)` | `SET NULL` |  |

### Unique Constraints

_None._

### Check Constraints

- `awarded_points >= 0`
- `grading_status IN ('PENDING','AUTO_GRADED','MANUAL_GRADED','FULL_CREDIT')`
- `grading_rule IN ('ORIGINAL','ANSWER_CORRECTION','CONTENT_FULL_CREDIT','MANUAL')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_question_grades_pending` | `grading_status, graded_at` | No | `grading_status='PENDING'` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Theo Attempt retention.

### Audit behavior

Mọi post-result grade change append history; manual changes reason required.

### Concurrency

row_version; manual/regrade update conditional để không mất change.

### Security / PII classification

Sensitive grade data.

### Important invariants

- awarded_points <= attempt_questions.points_assigned (service/check via join)
- Essay pending đến Instructor grade

---

## `attempt_question_grade_history`

**Purpose**

Append-only lịch sử thay đổi điểm từng câu.

**Lifecycle**

Append-only.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `attempt_question_id` | `BIGINT` | No |  | Question |
| `old_points` | `DECIMAL(9,4)` | Yes |  | Điểm trước |
| `new_points` | `DECIMAL(9,4)` | No |  | Điểm sau |
| `reason_code` | `VARCHAR(32)` | No |  | INITIAL/AUTO_REGRADE/FULL_CREDIT/MANUAL_REVISION |
| `reason` | `NVARCHAR(1000)` | Yes |  | Lý do chi tiết |
| `actor_user_id` | `BIGINT` | Yes |  | Actor nếu human |
| `question_correction_id` | `BIGINT` | Yes |  | Correction nguồn; FK deferred |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `attempt_question_id` | `attempt_questions(id)` | `NO ACTION` |  |
| `actor_user_id` | `users(id)` | `SET NULL` |  |
| `question_correction_id` | `question_corrections(id)` | `SET NULL` | Deferred cross-domain FK created in `010_cross_domain_constraints.sql`. |

### Unique Constraints

_None._

### Check Constraints

- `new_points >= 0`
- `reason_code IN ('INITIAL','AUTO_REGRADE','FULL_CREDIT','MANUAL_REVISION')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_grade_history_question` | `attempt_question_id, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Theo Attempt detailed retention, trừ khi cần giữ score history lâu hơn; aggregate result history có thể giữ compact.

### Audit behavior

Domain-specific grade audit; AuditEvent thêm cho admin/instructor sensitive manual action.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Sensitive score history.

### Important invariants

- Không update/delete entries trong active retention

---

## `assessment_results`

**Purpose**

Kết quả hiện hành của một Attempt; final score pending nếu còn Essay chưa chấm.

**Lifecycle**

PENDING → FINAL → RELEASED (release có thể đồng thời final nếu immediate). Regrade update current score + history.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `attempt_id` | `BIGINT` | No |  | PK/FK |
| `raw_score` | `DECIMAL(12,4)` | No | `0` | Tổng điểm hiện hành |
| `max_score` | `DECIMAL(12,4)` | No |  | Tổng điểm tối đa snapshot |
| `percent_score` | `DECIMAL(7,4)` | Yes |  | 0..100 |
| `passed` | `BIT` | Yes |  | Đạt ngưỡng |
| `status` | `VARCHAR(20)` | No | `'PENDING'` | PENDING/FINAL/RELEASED |
| `released_at` | `DATETIME2(3)` | Yes |  | Student được xem |
| `graded_at` | `DATETIME2(3)` | Yes |  | Final grade time |
| `updated_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm cập nhật cuối (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`attempt_id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `attempt_id` | `assessment_attempts(id)` | `NO ACTION` |  |

### Unique Constraints

_None._

### Check Constraints

- `raw_score >= 0`
- `max_score > 0`
- `percent_score IS NULL OR (percent_score >= 0 AND percent_score <= 100)`
- `status IN ('PENDING','FINAL','RELEASED')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_results_status` | `status, released_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_results_percent` | `percent_score, attempt_id` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Theo Attempt retention; compact Course summary giữ nếu detail purge.

### Audit behavior

Mọi post-result score change append result history.

### Concurrency

row_version; recompute aggregate trong same transaction với grade change item.

### Security / PII classification

Student grade sensitive.

### Important invariants

- Không FINAL nếu còn required manual grading pending
- Release policy service-enforced

---

## `assessment_result_history`

**Purpose**

Append-only lịch sử điểm tổng cũ/mới để Student xem lý do thay đổi.

**Lifecycle**

Append-only.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `attempt_id` | `BIGINT` | No |  | Attempt |
| `old_score` | `DECIMAL(12,4)` | Yes |  | Trước |
| `new_score` | `DECIMAL(12,4)` | No |  | Sau |
| `old_percent` | `DECIMAL(7,4)` | Yes |  | Trước % |
| `new_percent` | `DECIMAL(7,4)` | Yes |  | Sau % |
| `reason_code` | `VARCHAR(32)` | No |  | INITIAL/REGRADE/MANUAL/CORRECTION |
| `reason` | `NVARCHAR(1000)` | No |  | Lý do hiển thị phù hợp |
| `actor_user_id` | `BIGINT` | Yes |  | Actor human nếu có |
| `regrade_job_id` | `BIGINT` | Yes |  | Job nguồn; FK deferred |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `attempt_id` | `assessment_attempts(id)` | `NO ACTION` |  |
| `actor_user_id` | `users(id)` | `SET NULL` |  |
| `regrade_job_id` | `regrade_jobs(id)` | `SET NULL` | Deferred cross-domain FK created in `010_cross_domain_constraints.sql`. |

### Unique Constraints

_None._

### Check Constraints

- `new_score >= 0`
- `reason_code IN ('INITIAL','REGRADE','MANUAL','CORRECTION')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_result_history_attempt` | `attempt_id, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Có thể purge cùng detailed Attempt theo final retention rule; compact summary giữ tổng cần thiết.

### Audit behavior

Student có thể xem reason; admin/instructor action đồng thời AuditEvent.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Sensitive score history.

### Important invariants

- Không rewrite old history

---

## `question_corrections`

**Purpose**

Business event khi Question đã dùng được chỉnh; phân biệt answer-only và content/choices để worker áp dụng policy đúng.

**Lifecycle**

PENDING → RUNNING → APPLIED/FAILED; correction mới có thể supersede older pending job theo service.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `question_id` | `BIGINT` | No |  | Question |
| `from_revision_id` | `BIGINT` | No |  | Revision cũ |
| `to_revision_id` | `BIGINT` | No |  | Revision mới |
| `correction_type` | `VARCHAR(24)` | No |  | ANSWER_ONLY/CONTENT_OR_CHOICES |
| `effective_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm Instructor Save |
| `reason` | `NVARCHAR(1000)` | No |  | Lý do bắt buộc |
| `actor_user_id` | `BIGINT` | No |  | Instructor/Admin |
| `status` | `VARCHAR(20)` | No | `'PENDING'` | PENDING/RUNNING/APPLIED/FAILED/SUPERSEDED |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `question_id` | `questions(id)` | `NO ACTION` |  |
| `from_revision_id` | `question_revisions(id)` | `NO ACTION` |  |
| `to_revision_id` | `question_revisions(id)` | `NO ACTION` |  |
| `actor_user_id` | `users(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (to_revision_id)`

### Check Constraints

- `correction_type IN ('ANSWER_ONLY','CONTENT_OR_CHOICES')`
- `status IN ('PENDING','RUNNING','APPLIED','FAILED','SUPERSEDED')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_question_corrections_question_time` | `question_id, effective_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_question_corrections_status` | `status, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Giữ lâu dài cùng revision history.

### Audit behavior

Reason/actor/time bắt buộc; AuditEvent.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Instructor/Admin only.

### Important invariants

- ANSWER_ONLY không đổi content/choices
- CONTENT_OR_CHOICES full-credit cho eligible attempts started trước effective_at
- Historical snapshot không rewrite

---

## `regrade_jobs`

**Purpose**

Job chấm lại lớn, resumable/idempotent cho một correction.

**Lifecycle**

QUEUED → RUNNING/PARTIAL → COMPLETED; retry từ PARTIAL/FAILED.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `question_correction_id` | `BIGINT` | No |  | Correction |
| `background_job_id` | `BIGINT` | Yes |  | Optional link tới generic job; nullable để domain history sống lâu hơn operational job |
| `status` | `VARCHAR(20)` | No | `'QUEUED'` | QUEUED/RUNNING/PARTIAL/COMPLETED/FAILED/CANCELLED |
| `total_items` | `INT` | No | `0` | Số attempts mục tiêu |
| `processed_items` | `INT` | No | `0` | Đã xử lý |
| `changed_results` | `INT` | No | `0` | Số result đổi |
| `started_at` | `DATETIME2(3)` | Yes |  | UTC |
| `completed_at` | `DATETIME2(3)` | Yes |  | UTC |
| `last_error` | `NVARCHAR(2000)` | Yes |  | Lỗi cuối |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `question_correction_id` | `question_corrections(id)` | `NO ACTION` |  |
| `background_job_id` | `background_jobs(id)` | `SET NULL` | Deferred cross-domain FK created in `010_cross_domain_constraints.sql`. |

### Unique Constraints

- `UNIQUE (question_correction_id)`

### Check Constraints

- `status IN ('QUEUED','RUNNING','PARTIAL','COMPLETED','FAILED','CANCELLED')`
- `total_items >= 0`
- `processed_items >= 0`
- `changed_results >= 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_regrade_jobs_status` | `status, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Giữ cùng correction trong historical retention; có thể archive.

### Audit behavior

Job lifecycle operational; correction actor audited.

### Concurrency

row_version; worker claim bằng conditional update.

### Security / PII classification

Không expose arbitrary Student details ngoài authorized admin/instructor views.

### Important invariants

- Một correction tối đa một logical regrade job
- Eligible attempts exclude enrollment periods detail_purged_at != NULL

---

## `regrade_items`

**Purpose**

Per-attempt progress/idempotency cho regrade job.

**Lifecycle**

PENDING → PROCESSING → COMPLETED/SKIPPED/FAILED; retry FAILED/expired PROCESSING.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `regrade_job_id` | `BIGINT` | No |  | Job |
| `attempt_id` | `BIGINT` | No |  | Attempt |
| `status` | `VARCHAR(16)` | No | `'PENDING'` | PENDING/PROCESSING/COMPLETED/SKIPPED/FAILED |
| `old_score` | `DECIMAL(12,4)` | Yes |  | Score trước |
| `new_score` | `DECIMAL(12,4)` | Yes |  | Score sau |
| `skip_reason` | `VARCHAR(40)` | Yes |  | DETAIL_PURGED/NOT_AFFECTED/CANCELLED |
| `attempt_count` | `INT` | No | `0` | Retry count |
| `processed_at` | `DATETIME2(3)` | Yes |  | UTC |
| `last_error` | `NVARCHAR(2000)` | Yes |  | Lỗi |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `regrade_job_id` | `regrade_jobs(id)` | `NO ACTION` |  |
| `attempt_id` | `assessment_attempts(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (regrade_job_id, attempt_id)`

### Check Constraints

- `status IN ('PENDING','PROCESSING','COMPLETED','SKIPPED','FAILED')`
- `skip_reason IS NULL OR skip_reason IN ('DETAIL_PURGED','NOT_AFFECTED','CANCELLED')`
- `attempt_count >= 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_regrade_items_claim` | `regrade_job_id, status, id` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_regrade_items_attempt` | `attempt_id, regrade_job_id` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Theo regrade job retention; không là source of truth của final grade.

### Audit behavior

Operational; score history tables là business history.

### Concurrency

row_version/claim token prevents double processing.

### Security / PII classification

Sensitive because links Student attempt; limited access.

### Important invariants

- Unique job+attempt makes regrade idempotent
- Worker writes score/history atomically per item

---
# 09 DATA DICTIONARY FILES IMPORT

Database engine: **Microsoft SQL Server**. Timestamps are UTC `DATETIME2(3)` unless noted.

## `file_blobs`

**Purpose**

Đại diện file vật lý deduplicated theo SHA-256; nhiều logical assets/revisions có thể dùng chung.

**Lifecycle**

PRESENT → DELETING → DELETED khi refcount 0 + recovery expired + history permits.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `sha256` | `BINARY(32)` | No |  | SHA-256 content |
| `size_bytes` | `BIGINT` | No |  | Dung lượng vật lý |
| `detected_mime_type` | `NVARCHAR(150)` | No |  | MIME server detect |
| `storage_key` | `NVARCHAR(500)` | No |  | Key/path private trong storage |
| `status` | `VARCHAR(20)` | No | `'PRESENT'` | PRESENT/DELETING/DELETED |
| `reference_count` | `INT` | No | `0` | Cache số FileRevision đang reference |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `deleted_at` | `DATETIME2(3)` | Yes |  | Physical delete time |

### Primary Key

`id`

### Foreign Keys

_None._

### Unique Constraints

- `UNIQUE (sha256)`
- `UNIQUE (storage_key)`

### Check Constraints

- `size_bytes > 0`
- `status IN ('PRESENT','DELETING','DELETED')`
- `reference_count >= 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_file_blobs_status_ref` | `status, reference_count, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Physical bytes xóa; minimal metadata row có thể giữ nếu historically important.

### Audit behavior

Physical cleanup operational; suspicious hash/malware event security log.

### Concurrency

Dedup insert dùng unique sha256 + retry; reference_count cập nhật transactionally hoặc recompute.

### Security / PII classification

storage_key không public; không dựa vào key để authorize.

### Important invariants

- Không xóa physical blob khi còn FileRevision reference active/recovery
- Same sha256 dùng chung blob

---

## `file_assets`

**Purpose**

Logical file identity trong LMS; lifecycle độc lập với blob vật lý, hỗ trợ replacement/recovery.

**Lifecycle**

PENDING asset → activate security-cleared revision → ACTIVE; replace giữ same asset/current_revision thay; trash/recovery.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `public_id` | `UNIQUEIDENTIFIER` | No | `NEWSEQUENTIALID()` | ID công khai dùng trong URL/API; không thay thế kiểm tra quyền |
| `course_id` | `BIGINT` | No |  | Course boundary |
| `created_by_user_id` | `BIGINT` | No |  | Uploader |
| `asset_type` | `VARCHAR(24)` | No |  | RESOURCE/QUESTION_IMAGE/COURSE_IMAGE/IMPORT_SOURCE/EXPORT/OTHER |
| `display_name` | `NVARCHAR(255)` | No |  | Tên hiển thị |
| `current_revision_id` | `BIGINT` | Yes |  | Revision ACTIVE hiện hành; NULL trong lúc asset mới còn PENDING hoặc sau cleanup hợp lệ |
| `status` | `VARCHAR(20)` | No | `'PENDING'` | PENDING/ACTIVE/REPLACED/TRASH/HISTORICAL |
| `retention_until` | `DATETIME2(3)` | Yes |  | Mốc cleanup logical asset |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `updated_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm cập nhật cuối (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |
| `deleted_at` | `DATETIME2(3)` | Yes |  | Thời điểm đưa vào thùng rác |
| `restore_until` | `DATETIME2(3)` | Yes |  | Hạn khôi phục trước khi cleanup/historical transition |
| `deleted_by_user_id` | `BIGINT` | Yes |  | Người thực hiện xóa |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `course_id` | `courses(id)` | `NO ACTION` |  |
| `created_by_user_id` | `users(id)` | `NO ACTION` |  |
| `deleted_by_user_id` | `users(id)` | `SET NULL` |  |
| `current_revision_id` | `file_revisions(id)` | `SET NULL` | Deferred cross-domain FK created in `010_cross_domain_constraints.sql`. |

### Unique Constraints

- `UNIQUE (public_id)`

### Check Constraints

- `asset_type IN ('RESOURCE','QUESTION_IMAGE','COURSE_IMAGE','IMPORT_SOURCE','EXPORT','OTHER')`
- `status IN ('PENDING','ACTIVE','REPLACED','TRASH','HISTORICAL')`
- `status <> 'ACTIVE' OR current_revision_id IS NOT NULL`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_file_assets_course_status` | `course_id, status, asset_type` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Logical ref remove không xóa blob nếu asset khác dùng. Historical metadata giữ khi cần.

### Audit behavior

Replace/delete/admin restore audit khi important.

### Concurrency

row_version; replacement activation compare expected current_revision.

### Security / PII classification

Authorization theo Course + logical references; direct storage path không public.

### Important invariants

- `current_revision_id` chỉ được trỏ revision cùng asset có status `ACTIVE`; asset mới có thể `PENDING` với pointer NULL
- Quota tính logical usage theo policy, physical dedup không thay authorization

---

## `file_revisions`

**Purpose**

Một lần upload/replacement của FileAsset; luôn quarantine trước khi active.

**Lifecycle**

QUARANTINED → VALIDATING → SCANNING → SAFE → ACTIVE; fail → REJECTED. Replacement: old ACTIVE → RECOVERY/REPLACED → DELETED.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `file_asset_id` | `BIGINT` | No |  | Asset |
| `revision_no` | `INT` | No |  | Tăng tuần tự |
| `blob_id` | `BIGINT` | Yes |  | Physical blob sau validation/dedup |
| `original_filename` | `NVARCHAR(255)` | No |  | Tên file người dùng gửi |
| `declared_mime_type` | `NVARCHAR(150)` | Yes |  | Client MIME |
| `detected_mime_type` | `NVARCHAR(150)` | Yes |  | Server detect |
| `size_bytes` | `BIGINT` | No |  | Upload size |
| `status` | `VARCHAR(24)` | No | `'QUARANTINED'` | QUARANTINED/VALIDATING/SCANNING/SAFE/ACTIVE/REJECTED/REPLACED/RECOVERY/DELETED |
| `uploaded_by_user_id` | `BIGINT` | No |  | Uploader |
| `quarantine_key` | `NVARCHAR(500)` | Yes |  | Vị trí private tạm |
| `security_checks_completed_at` | `DATETIME2(3)` | Yes |  | UTC |
| `activated_at` | `DATETIME2(3)` | Yes |  | UTC |
| `replaced_at` | `DATETIME2(3)` | Yes |  | UTC |
| `recovery_until` | `DATETIME2(3)` | Yes |  | Giữ bản cũ ~30 ngày |
| `rejection_reason` | `NVARCHAR(1000)` | Yes |  | Lý do reject |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `file_asset_id` | `file_assets(id)` | `NO ACTION` |  |
| `blob_id` | `file_blobs(id)` | `SET NULL` |  |
| `uploaded_by_user_id` | `users(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (file_asset_id, revision_no)`

### Check Constraints

- `revision_no > 0`
- `size_bytes > 0`
- `status IN ('QUARANTINED','VALIDATING','SCANNING','SAFE','ACTIVE','REJECTED','REPLACED','RECOVERY','DELETED')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ux_file_revisions_active` | `file_asset_id` | Yes | `status = 'ACTIVE'` | DB-enforce tối đa một revision ACTIVE cho mỗi logical file asset. |
| `ix_file_revisions_asset` | `file_asset_id, revision_no` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_file_revisions_processing` | `status, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_file_revisions_recovery` | `recovery_until, status` | No | `recovery_until IS NOT NULL` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Quarantine rejected cleaned quickly; old safe revision kept recovery then blob ref removed.

### Audit behavior

Replacement/reject/malware significant events audit/security event.

### Concurrency

row_version; filtered unique index chỉ cho tối đa một ACTIVE revision/asset; service transaction đổi current pointer atomically.

### Security / PII classification

Untrusted until all checks pass; macro-enabled Office rejected; parser resource limits.

### Important invariants

- Scan unavailable/fail không được ACTIVE
- Video <1GB; image~10MB PDF/DOCX~50MB PPTX~100MB enforced service before processing

---

## `file_scan_results`

**Purpose**

Kết quả từng bước validation/malware/parser security cho FileRevision.

**Lifecycle**

Append result per scan attempt; latest/required PASS set controls activation.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `file_revision_id` | `BIGINT` | No |  | Revision |
| `scan_type` | `VARCHAR(24)` | No |  | FILE_VALIDATION/MALWARE/STRUCTURE/RESOURCE_LIMIT/CONTENT_SECURITY |
| `engine` | `NVARCHAR(100)` | No |  | ClamAV/parser/... |
| `engine_version` | `NVARCHAR(100)` | Yes |  | Version/signature |
| `status` | `VARCHAR(16)` | No |  | PASS/FAIL/ERROR |
| `details_json` | `NVARCHAR(MAX)` | Yes |  | Diagnostics sanitized |
| `started_at` | `DATETIME2(3)` | Yes |  | UTC |
| `completed_at` | `DATETIME2(3)` | Yes |  | UTC |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `file_revision_id` | `file_revisions(id)` | `NO ACTION` |  |

### Unique Constraints

_None._

### Check Constraints

- `scan_type IN ('FILE_VALIDATION','MALWARE','STRUCTURE','RESOURCE_LIMIT','CONTENT_SECURITY')`
- `status IN ('PASS','FAIL','ERROR')`
- `details_json IS NULL OR ISJSON(details_json)=1`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_file_scan_revision_type` | `file_revision_id, scan_type, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_file_scan_failures` | `status, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Giữ đủ cho file security audit; old low-value detail có thể archive.

### Audit behavior

Malware/high-risk result tạo security_event.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Không lưu raw malicious content.

### Important invariants

- Required scan ERROR được coi fail-closed, không safe

---

## `lesson_resources`

**Purpose**

Liên kết Lesson với logical FileAsset; quyền truy cập đi qua Lesson/Course.

**Lifecycle**

Active while Lesson references asset.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `lesson_id` | `BIGINT` | No |  | Lesson |
| `file_asset_id` | `BIGINT` | No |  | Asset |
| `position` | `INT` | No | `1` | Thứ tự |
| `label` | `NVARCHAR(255)` | Yes |  | Nhãn |
| `is_required` | `BIT` | No | `0` | Resource bắt buộc |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `lesson_id` | `lessons(id)` | `NO ACTION` |  |
| `file_asset_id` | `file_assets(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (lesson_id, file_asset_id)`
- `UNIQUE (lesson_id, position)`

### Check Constraints

- `position > 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_lesson_resources_lesson` | `lesson_id, position` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Remove link only; asset/blob cleanup separate.

### Audit behavior

Resource replace/remove significant edit audit.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Download service verifies enrollment/lesson authorization + asset safe status.

### Important invariants

- file_asset.course_id phải cùng lesson.course_id (service)

---

## `question_revision_resources`

**Purpose**

Ảnh/tệp đính kèm QuestionRevision, đặc biệt image extracted từ DOCX.

**Lifecycle**

Theo revision retention.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `question_revision_id` | `BIGINT` | No |  | Revision |
| `file_asset_id` | `BIGINT` | No |  | Asset |
| `position` | `INT` | No | `1` | Thứ tự |
| `resource_role` | `VARCHAR(20)` | No | `'IMAGE'` | IMAGE/ATTACHMENT |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `question_revision_id` | `question_revisions(id)` | `NO ACTION` |  |
| `file_asset_id` | `file_assets(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (question_revision_id, file_asset_id)`

### Check Constraints

- `position > 0`
- `resource_role IN ('IMAGE','ATTACHMENT')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_question_resources_revision` | `question_revision_id, position` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Link giữ nếu revision historical; blob dedup cleanup độc lập.

### Audit behavior

Import provenance handles source.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Student chỉ access asset khi attempt/course authorizes.

### Important invariants

- Asset phải safe/active trước Question draft được approve/publish

---

## `document_import_jobs`

**Purpose**

Import DOCX/PDF → draft Assessment với confidence/review; không auto publish.

**Lifecycle**

QUEUED → PROCESSING → REVIEW_REQUIRED/COMPLETED; fail safe. Instructor review required before publish.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `public_id` | `UNIQUEIDENTIFIER` | No | `NEWSEQUENTIALID()` | ID công khai dùng trong URL/API; không thay thế kiểm tra quyền |
| `course_id` | `BIGINT` | No |  | Course |
| `source_file_asset_id` | `BIGINT` | No |  | DOCX/PDF source |
| `requested_by_user_id` | `BIGINT` | No |  | Instructor |
| `draft_assessment_id` | `BIGINT` | Yes |  | Assessment draft tạo ra |
| `background_job_id` | `BIGINT` | Yes |  | Optional link tới generic job; nullable để import history không phụ thuộc retention của operational queue |
| `document_type` | `VARCHAR(8)` | No |  | DOCX/PDF |
| `status` | `VARCHAR(24)` | No | `'QUEUED'` | QUEUED/PROCESSING/REVIEW_REQUIRED/COMPLETED/FAILED/CANCELLED |
| `parser_version` | `NVARCHAR(100)` | No |  | Parser version |
| `question_count` | `INT` | No | `0` | Detected |
| `review_required_count` | `INT` | No | `0` | Ambiguous |
| `started_at` | `DATETIME2(3)` | Yes |  | UTC |
| `completed_at` | `DATETIME2(3)` | Yes |  | UTC |
| `last_error` | `NVARCHAR(2000)` | Yes |  | Lỗi |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `course_id` | `courses(id)` | `NO ACTION` |  |
| `source_file_asset_id` | `file_assets(id)` | `NO ACTION` |  |
| `requested_by_user_id` | `users(id)` | `NO ACTION` |  |
| `draft_assessment_id` | `assessments(id)` | `SET NULL` |  |
| `background_job_id` | `background_jobs(id)` | `SET NULL` | Deferred cross-domain FK created in `010_cross_domain_constraints.sql`. |

### Unique Constraints

- `UNIQUE (public_id)`

### Check Constraints

- `document_type IN ('DOCX','PDF')`
- `status IN ('QUEUED','PROCESSING','REVIEW_REQUIRED','COMPLETED','FAILED','CANCELLED')`
- `question_count >= 0`
- `review_required_count >= 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_import_jobs_course_status` | `course_id, status, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_import_jobs_status` | `status, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Import diagnostics có thể cleanup sau accepted content stabilized; provenance on Question remains.

### Audit behavior

Approve imported content provenance; import execution operational.

### Concurrency

row_version; worker claim via generic job.

### Security / PII classification

Source file phải SAFE trước parse; parser timeout/resource limits.

### Important invariants

- Scanned PDF OCR không MVP
- Import chỉ tạo draft
- Broken image flags related question review

---

## `import_questions`

**Purpose**

Intermediate parsed question record, chưa là Question Bank cho tới Instructor approve.

**Lifecycle**

Parsed → review → ACCEPTED/REJECTED/EDITED. ACCEPTED creates Question/Revision/Provenance.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `import_job_id` | `BIGINT` | No |  | Job |
| `ordinal` | `INT` | No |  | Vị trí trong doc |
| `detected_type` | `VARCHAR(24)` | Yes |  | Type |
| `content_text` | `NVARCHAR(MAX)` | No |  | Parsed content |
| `choices_json` | `NVARCHAR(MAX)` | Yes |  | Choices draft |
| `detected_answer_json` | `NVARCHAR(MAX)` | Yes |  | Answer from document |
| `explanation_text` | `NVARCHAR(MAX)` | Yes |  | Explanation |
| `confidence_score` | `DECIMAL(5,4)` | No |  | 0..1 |
| `diagnostics_json` | `NVARCHAR(MAX)` | Yes |  | Parser diagnostics |
| `review_state` | `VARCHAR(20)` | No | `'READY'` | READY/NEEDS_REVIEW/INVALID/ACCEPTED/REJECTED/EDITED |
| `has_broken_resource` | `BIT` | No | `0` | Image/resource lỗi |
| `ai_suggested_answer_json` | `NVARCHAR(MAX)` | Yes |  | Optional AI suggestion; không official |
| `ai_suggestion_model` | `NVARCHAR(100)` | Yes |  | Model |
| `ai_suggestion_confirmed_at` | `DATETIME2(3)` | Yes |  | Instructor accept suggestion |
| `ai_suggestion_confirmed_by` | `BIGINT` | Yes |  | Instructor |
| `approved_question_id` | `BIGINT` | Yes |  | Question tạo sau review |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `updated_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm cập nhật cuối (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `import_job_id` | `document_import_jobs(id)` | `NO ACTION` |  |
| `ai_suggestion_confirmed_by` | `users(id)` | `SET NULL` |  |
| `approved_question_id` | `questions(id)` | `SET NULL` |  |

### Unique Constraints

- `UNIQUE (import_job_id, ordinal)`

### Check Constraints

- `ordinal > 0`
- `confidence_score >= 0 AND confidence_score <= 1`
- `review_state IN ('READY','NEEDS_REVIEW','INVALID','ACCEPTED','REJECTED','EDITED')`
- `choices_json IS NULL OR ISJSON(choices_json)=1`
- `detected_answer_json IS NULL OR ISJSON(detected_answer_json)=1`
- `diagnostics_json IS NULL OR ISJSON(diagnostics_json)=1`
- `ai_suggested_answer_json IS NULL OR ISJSON(ai_suggested_answer_json)=1`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_import_questions_review` | `import_job_id, review_state, ordinal` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Có thể cleanup sau provenance retained and recovery window.

### Audit behavior

AI suggestion confirmation and approval trace via provenance/AuditEvent.

### Concurrency

row_version để tránh concurrent review overwrite.

### Security / PII classification

AI suggestion never official until explicit confirm; content untrusted until sanitized/validated.

### Important invariants

- No answer key => official answer remains unknown until Instructor input/confirmation
- Broken resource cannot READY publish

---

## `import_duplicate_candidates`

**Purpose**

Cảnh báo duplicate/near-duplicate trong import hoặc Question Bank; không auto merge.

**Lifecycle**

PENDING → decision. Advisory only.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `import_question_id` | `BIGINT` | No |  | Parsed question |
| `candidate_import_question_id` | `BIGINT` | Yes |  | Duplicate trong cùng import |
| `candidate_question_id` | `BIGINT` | Yes |  | Question Bank candidate |
| `similarity_score` | `DECIMAL(5,4)` | No |  | 0..1 |
| `decision` | `VARCHAR(16)` | No | `'PENDING'` | PENDING/KEEP/IGNORE/REJECT |
| `decided_by_user_id` | `BIGINT` | Yes |  | Instructor |
| `decided_at` | `DATETIME2(3)` | Yes |  | UTC |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `import_question_id` | `import_questions(id)` | `NO ACTION` |  |
| `candidate_import_question_id` | `import_questions(id)` | `SET NULL` |  |
| `candidate_question_id` | `questions(id)` | `SET NULL` |  |
| `decided_by_user_id` | `users(id)` | `SET NULL` |  |

### Unique Constraints

_None._

### Check Constraints

- `similarity_score >= 0 AND similarity_score <= 1`
- `decision IN ('PENDING','KEEP','IGNORE','REJECT')`
- `(candidate_import_question_id IS NOT NULL OR candidate_question_id IS NOT NULL)`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_import_duplicates_question` | `import_question_id, decision` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Cleanup với import diagnostics.

### Audit behavior

Không cần full AuditEvent trừ admin override; decision trace trong row.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

No sensitive data beyond question linkage.

### Important invariants

- Không tự merge

---

## `import_question_resources`

**Purpose**

Ảnh extracted gắn với parsed question trước approval.

**Lifecycle**

Extracted → scan → READY/BROKEN. Khi approve tạo question_revision_resources.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `import_question_id` | `BIGINT` | No |  | Parsed question |
| `file_asset_id` | `BIGINT` | No |  | Extracted image asset |
| `position` | `INT` | No | `1` | Thứ tự |
| `status` | `VARCHAR(16)` | No | `'READY'` | READY/BROKEN/REJECTED |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `import_question_id` | `import_questions(id)` | `NO ACTION` |  |
| `file_asset_id` | `file_assets(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (import_question_id, file_asset_id)`

### Check Constraints

- `position > 0`
- `status IN ('READY','BROKEN','REJECTED')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_import_question_resources` | `import_question_id, position` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Cleanup sau promotion/rejection nếu không còn logical ref.

### Audit behavior

Security scan separate.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Asset phải safe trước READY.

### Important invariants

- BROKEN forces import_question NEEDS_REVIEW

---
# 10 DATA DICTIONARY AI RAG

Database engine: **Microsoft SQL Server**. Timestamps are UTC `DATETIME2(3)` unless noted.

## `ai_conversations`

**Purpose**

Phiên chat ngắn hạn; raw conversation tự xóa sau 5 phút inactivity.

**Lifecycle**

ACTIVE; mỗi user message reset expiry; >5 phút → EXPIRED → raw message cleanup/DELETED.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `public_id` | `UNIQUEIDENTIFIER` | No | `NEWSEQUENTIALID()` | ID công khai dùng trong URL/API; không thay thế kiểm tra quyền |
| `user_id` | `BIGINT` | No |  | User |
| `context_type` | `VARCHAR(16)` | No |  | GLOBAL/COURSE/LESSON |
| `course_id` | `BIGINT` | Yes |  | Context Course |
| `lesson_id` | `BIGINT` | Yes |  | Context Lesson |
| `last_activity_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Tin nhắn user gần nhất |
| `expires_at` | `DATETIME2(3)` | No |  | last user activity + 5 phút |
| `status` | `VARCHAR(16)` | No | `'ACTIVE'` | ACTIVE/EXPIRED/DELETED |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `user_id` | `users(id)` | `NO ACTION` |  |
| `course_id` | `courses(id)` | `SET NULL` |  |
| `lesson_id` | `lessons(id)` | `SET NULL` |  |

### Unique Constraints

- `UNIQUE (public_id)`

### Check Constraints

- `context_type IN ('GLOBAL','COURSE','LESSON')`
- `status IN ('ACTIVE','EXPIRED','DELETED')`
- `expires_at > created_at`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_ai_conversations_expiry` | `expires_at, status` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_ai_conversations_user` | `user_id, status, last_activity_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Raw conversation hard-delete/clear sau 5 phút; security metadata tách ai_requests/security_events.

### Audit behavior

Không giữ raw content để audit.

### Concurrency

row_version; update expiry conditional.

### Security / PII classification

Raw chat may contain PII; strict short retention.

### Important invariants

- 5-minute inactivity based on user messages
- No raw chat retention beyond policy except brief cleanup latency

---

## `ai_messages`

**Purpose**

Raw user/assistant messages tạm thời trong conversation 5 phút.

**Lifecycle**

Tồn tại tối đa conversation retention.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `conversation_id` | `BIGINT` | No |  | Conversation |
| `sender` | `VARCHAR(12)` | No |  | USER/ASSISTANT |
| `content` | `NVARCHAR(MAX)` | No |  | Raw content temporary |
| `sequence_no` | `INT` | No |  | Order |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `conversation_id` | `ai_conversations(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (conversation_id, sequence_no)`

### Check Constraints

- `sender IN ('USER','ASSISTANT')`
- `sequence_no > 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_ai_messages_conversation` | `conversation_id, sequence_no` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Hard-delete khi conversation expires.

### Audit behavior

Không dùng làm audit.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Sensitive; minimum access.

### Important invariants

- Cleanup worker must remove raw content after 5-minute inactivity

---

## `ai_requests`

**Purpose**

Metadata mỗi AI/backend routing request; giữ usage/security mà không cần raw prompt lâu dài.

**Lifecycle**

Append metadata; aggregate/archive later.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `request_id` | `UNIQUEIDENTIFIER` | No | `NEWID()` | Correlation public |
| `conversation_id` | `BIGINT` | Yes |  | Conversation nếu chat |
| `user_id` | `BIGINT` | No |  | Caller |
| `route_type` | `VARCHAR(24)` | No |  | BACKEND_ONLY/GEMINI/RAG/CLASSIFIER |
| `model_name` | `NVARCHAR(100)` | Yes |  | Model nếu external |
| `prompt_hash` | `BINARY(32)` | Yes |  | Hash normalized prompt |
| `scope_decision` | `VARCHAR(16)` | Yes |  | IN_SCOPE/OUT_OF_SCOPE/MIXED/AMBIGUOUS |
| `authorization_scope_hash` | `BINARY(32)` | Yes |  | Hash access envelope để debug/cache safety |
| `input_token_count` | `INT` | Yes |  | Usage |
| `output_token_count` | `INT` | Yes |  | Usage |
| `latency_ms` | `INT` | Yes |  | Latency |
| `status` | `VARCHAR(20)` | No |  | SUCCEEDED/REFUSED/FAILED/TIMEOUT/BYPASSED |
| `error_code` | `VARCHAR(64)` | Yes |  | Sanitized |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `conversation_id` | `ai_conversations(id)` | `SET NULL` |  |
| `user_id` | `users(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (request_id)`

### Check Constraints

- `route_type IN ('BACKEND_ONLY','GEMINI','RAG','CLASSIFIER')`
- `scope_decision IS NULL OR scope_decision IN ('IN_SCOPE','OUT_OF_SCOPE','MIXED','AMBIGUOUS')`
- `status IN ('SUCCEEDED','REFUSED','FAILED','TIMEOUT','BYPASSED')`
- `input_token_count IS NULL OR input_token_count >= 0`
- `output_token_count IS NULL OR output_token_count >= 0`
- `latency_ms IS NULL OR latency_ms >= 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_ai_requests_user_time` | `user_id, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_ai_requests_status_time` | `status, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

May retain longer than raw chat because no raw text; follow privacy policy.

### Audit behavior

Security events link by correlation/hash, not raw content.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

May be sensitive metadata; no full prompt/response stored.

### Important invariants

- Backend-computable request may be BYPASSED without Gemini
- Personalized response never enters shared cache

---

## `ai_generated_question_drafts`

**Purpose**

Draft câu hỏi do AI tạo; không vào Question Bank trước Instructor review.

**Lifecycle**

PENDING → keep/edit/reject/approve. APPROVED creates Question+Revision+Provenance.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `course_id` | `BIGINT` | No |  | Course |
| `lesson_id` | `BIGINT` | Yes |  | Lesson source |
| `requested_by_user_id` | `BIGINT` | No |  | Instructor |
| `ai_request_id` | `BIGINT` | Yes |  | Request metadata |
| `ordinal` | `INT` | No |  | Order |
| `question_type` | `VARCHAR(24)` | No |  | Requested/generated type |
| `difficulty` | `VARCHAR(20)` | No |  | REMEMBER/UNDERSTAND/APPLY |
| `content` | `NVARCHAR(MAX)` | No |  | Draft |
| `choices_json` | `NVARCHAR(MAX)` | Yes |  | Draft choices |
| `answer_json` | `NVARCHAR(MAX)` | Yes |  | Draft answer |
| `explanation` | `NVARCHAR(MAX)` | Yes |  | Draft explanation |
| `review_state` | `VARCHAR(16)` | No | `'PENDING'` | PENDING/KEPT/EDITED/REJECTED/APPROVED |
| `approved_question_id` | `BIGINT` | Yes |  | Question sau approve |
| `reviewed_by_user_id` | `BIGINT` | Yes |  | Instructor |
| `reviewed_at` | `DATETIME2(3)` | Yes |  | UTC |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `updated_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm cập nhật cuối (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `course_id` | `courses(id)` | `NO ACTION` |  |
| `lesson_id` | `lessons(id)` | `SET NULL` |  |
| `requested_by_user_id` | `users(id)` | `NO ACTION` |  |
| `ai_request_id` | `ai_requests(id)` | `SET NULL` |  |
| `approved_question_id` | `questions(id)` | `SET NULL` |  |
| `reviewed_by_user_id` | `users(id)` | `SET NULL` |  |

### Unique Constraints

_None._

### Check Constraints

- `ordinal > 0`
- `question_type IN ('SINGLE_CHOICE','MULTIPLE_CHOICE','TRUE_FALSE','SHORT_ANSWER','ESSAY')`
- `difficulty IN ('REMEMBER','UNDERSTAND','APPLY')`
- `review_state IN ('PENDING','KEPT','EDITED','REJECTED','APPROVED')`
- `choices_json IS NULL OR ISJSON(choices_json)=1`
- `answer_json IS NULL OR ISJSON(answer_json)=1`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_ai_drafts_review` | `course_id, review_state, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Rejected drafts may cleanup after short retention; provenance retained for approved question.

### Audit behavior

Approval/AI origin captured by question_provenance.

### Concurrency

row_version.

### Security / PII classification

Educational content draft, not Student-visible.

### Important invariants

- Never auto-insert to Question Bank

---

## `knowledge_documents`

**Purpose**

Logical source eligible for RAG metadata; authorization remains LMS source entity, not vector index.

**Lifecycle**

ACTIVE; source edit creates new version and invalidates old searchable version; source delete/archive disables retrieval immediately.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `public_id` | `UNIQUEIDENTIFIER` | No | `NEWSEQUENTIALID()` | ID công khai dùng trong URL/API; không thay thế kiểm tra quyền |
| `course_id` | `BIGINT` | No |  | Course |
| `lesson_id` | `BIGINT` | Yes |  | Lesson source |
| `source_type` | `VARCHAR(24)` | No |  | LESSON/FILE/FAQ/POLICY |
| `source_entity_id` | `BIGINT` | No |  | ID source entity |
| `status` | `VARCHAR(20)` | No | `'ACTIVE'` | ACTIVE/INVALIDATED/DELETED |
| `current_version_id` | `BIGINT` | Yes |  | Active KnowledgeVersion; NULL trước lần index thành công đầu tiên hoặc sau invalidation/cleanup hợp lệ |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `updated_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm cập nhật cuối (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `course_id` | `courses(id)` | `NO ACTION` |  |
| `lesson_id` | `lessons(id)` | `SET NULL` |  |
| `current_version_id` | `knowledge_versions(id)` | `SET NULL` | Deferred cross-domain FK created in `010_cross_domain_constraints.sql`. |

### Unique Constraints

- `UNIQUE (public_id)`
- `UNIQUE (source_type, source_entity_id)`

### Check Constraints

- `source_type IN ('LESSON','FILE','FAQ','POLICY')`
- `status IN ('ACTIVE','INVALIDATED','DELETED')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_knowledge_docs_course_status` | `course_id, status, source_type` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Logical metadata may remain tombstoned; vector entries must be removed/disabled.

### Audit behavior

Index invalidation operational; source content edit audit at source.

### Concurrency

row_version; activation compare current version.

### Security / PII classification

RAG retrieval must prefilter by published/authorized Course/Lesson + active status.

### Important invariants

- Archived Course excluded from retrieval
- Deleted source stops retrieval immediately even if physical file recovery exists

---

## `knowledge_versions`

**Purpose**

Process/activation state cho một version RAG; old version chỉ dùng nếu still valid/authorized.

**Lifecycle**

PENDING → PROCESSING → ACTIVE; previous ACTIVE → INVALIDATED. FAILED không active.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `knowledge_document_id` | `BIGINT` | No |  | Document |
| `version_no` | `INT` | No |  | Sequence |
| `source_revision_type` | `VARCHAR(32)` | Yes |  | LESSON_VERSION/FILE_REVISION/QUESTION_REVISION/OTHER |
| `source_revision_id` | `BIGINT` | Yes |  | Source revision id |
| `content_hash` | `BINARY(32)` | No |  | Hash extracted text |
| `status` | `VARCHAR(20)` | No | `'PENDING'` | PENDING/PROCESSING/ACTIVE/INVALIDATED/FAILED |
| `vector_namespace` | `NVARCHAR(200)` | Yes |  | Vector store namespace |
| `background_job_id` | `BIGINT` | Yes |  | Generic job; FK deferred |
| `activated_at` | `DATETIME2(3)` | Yes |  | UTC |
| `invalidated_at` | `DATETIME2(3)` | Yes |  | UTC |
| `last_error` | `NVARCHAR(2000)` | Yes |  | Sanitized |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `knowledge_document_id` | `knowledge_documents(id)` | `NO ACTION` |  |
| `background_job_id` | `background_jobs(id)` | `SET NULL` | Deferred cross-domain FK created in `010_cross_domain_constraints.sql`. |

### Unique Constraints

- `UNIQUE (knowledge_document_id, version_no)`

### Check Constraints

- `version_no > 0`
- `status IN ('PENDING','PROCESSING','ACTIVE','INVALIDATED','FAILED')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ux_knowledge_versions_active` | `knowledge_document_id` | Yes | `status = 'ACTIVE'` | DB-enforce tối đa một knowledge version ACTIVE cho mỗi document. |
| `ix_knowledge_versions_doc` | `knowledge_document_id, version_no` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_knowledge_versions_status` | `status, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Old invalidated metadata may archive; source version linkage retained enough for answer provenance.

### Audit behavior

Operational.

### Concurrency

row_version; filtered unique index chỉ cho tối đa một ACTIVE version/document; activation transaction đổi current pointer atomically.

### Security / PII classification

No raw secret; extracted content may be sensitive only within course authorization.

### Important invariants

- New version active only after successful processing
- If fail, last valid version may stay active only if source still authorized/not archived/deleted

---

## `knowledge_chunks`

**Purpose**

Metadata chunk; embedding/vector payload nằm vector store riêng để không phụ thuộc SQL Server vector feature.

**Lifecycle**

Created during indexing; invalidated logically with version; vector key deleted/disabled on invalidation.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `knowledge_version_id` | `BIGINT` | No |  | Version |
| `chunk_no` | `INT` | No |  | Order |
| `text_hash` | `BINARY(32)` | No |  | Hash chunk |
| `vector_key` | `NVARCHAR(300)` | No |  | ID trong vector store |
| `token_count` | `INT` | Yes |  | Approx tokens |
| `metadata_json` | `NVARCHAR(MAX)` | Yes |  | Metadata retrieval không chứa unauthorized PII |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `knowledge_version_id` | `knowledge_versions(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (knowledge_version_id, chunk_no)`
- `UNIQUE (vector_key)`

### Check Constraints

- `chunk_no > 0`
- `token_count IS NULL OR token_count >= 0`
- `metadata_json IS NULL OR ISJSON(metadata_json)=1`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_knowledge_chunks_version` | `knowledge_version_id, chunk_no` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Can hard-delete chunks when version historical metadata no longer needs chunk-level detail; source usage may keep version id.

### Audit behavior

No.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Chunk retrieval requires authorization before/vector filter; retrieved content treated as data, never instruction.

### Important invariants

- Vector result must map back to ACTIVE authorized knowledge version

---

## `ai_source_usages`

**Purpose**

Records source version/chunk metadata used by an AI answer/request without retaining raw conversation.

**Lifecycle**

Append metadata per request; may outlive raw chat.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `ai_request_id` | `BIGINT` | No |  | AI request |
| `knowledge_version_id` | `BIGINT` | No |  | Source version |
| `knowledge_chunk_id` | `BIGINT` | Yes |  | Chunk |
| `rank_no` | `INT` | Yes |  | Retrieval rank |
| `relevance_score` | `DECIMAL(8,6)` | Yes |  | Similarity/relevance |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `ai_request_id` | `ai_requests(id)` | `NO ACTION` |  |
| `knowledge_version_id` | `knowledge_versions(id)` | `NO ACTION` |  |
| `knowledge_chunk_id` | `knowledge_chunks(id)` | `SET NULL` |  |

### Unique Constraints

- `UNIQUE (ai_request_id, knowledge_version_id, knowledge_chunk_id)`

### Check Constraints

- `rank_no IS NULL OR rank_no > 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_ai_source_request` | `ai_request_id, rank_no` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_ai_source_version` | `knowledge_version_id, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Retain as debug/audit metadata per privacy policy; no raw source text duplicated.

### Audit behavior

Supports traceability of AI answer source.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Can reveal what course source was used; Admin/debug access limited.

### Important invariants

- Only sources authorized for caller may be recorded/used

---
# 11 DATA DICTIONARY NOTIFICATION AUDIT OPERATIONS

Database engine: **Microsoft SQL Server**. Timestamps are UTC `DATETIME2(3)` unless noted.

## `notification_events`

**Purpose**

Business event fan-out source for in-app notification/email; dedupe retries via event_key.

**Lifecycle**

Append; fan-out to notifications/email deliveries.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `event_key` | `UNIQUEIDENTIFIER` | No | `NEWID()` | Stable idempotency event key |
| `event_type` | `VARCHAR(64)` | No |  | SCORE_CHANGED/ROLE_CHANGED/ASSESSMENT_REMINDER/... |
| `actor_user_id` | `BIGINT` | Yes |  | Actor nếu có |
| `target_type` | `VARCHAR(32)` | Yes |  | COURSE/ASSESSMENT/ATTEMPT/USER/QUESTION/SYSTEM |
| `target_id` | `BIGINT` | Yes |  | Target id |
| `correlation_id` | `UNIQUEIDENTIFIER` | Yes |  | Request/job correlation |
| `payload_json` | `NVARCHAR(MAX)` | Yes |  | Template data sanitized |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `actor_user_id` | `users(id)` | `SET NULL` |  |

### Unique Constraints

- `UNIQUE (event_key)`

### Check Constraints

- `payload_json IS NULL OR ISJSON(payload_json)=1`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_notification_events_type_time` | `event_type, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Operational cleanup allowed after child deliveries aged out if AuditEvent retains durable security facts.

### Audit behavior

Not equivalent to AuditEvent.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Payload must not include password/token/raw sensitive answer.

### Important invariants

- Producer reuses same event_key on retry to avoid duplicate fan-out

---

## `notifications`

**Purpose**

In-app notification per recipient với read/unread và retention.

**Lifecycle**

Unread → read; cleanup ordinary notifications after expiry.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `public_id` | `UNIQUEIDENTIFIER` | No | `NEWSEQUENTIALID()` | ID công khai dùng trong URL/API; không thay thế kiểm tra quyền |
| `notification_event_id` | `BIGINT` | No |  | Event |
| `recipient_user_id` | `BIGINT` | No |  | Recipient |
| `category` | `VARCHAR(32)` | No |  | SECURITY/COURSE/ASSESSMENT/GRADE/SYSTEM |
| `title` | `NVARCHAR(250)` | No |  | Title |
| `body` | `NVARCHAR(2000)` | No |  | Body |
| `read_at` | `DATETIME2(3)` | Yes |  | Read time |
| `expires_at` | `DATETIME2(3)` | Yes |  | Cleanup low-value |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `notification_event_id` | `notification_events(id)` | `NO ACTION` |  |
| `recipient_user_id` | `users(id)` | `NO ACTION` |  |

### Unique Constraints

- `UNIQUE (notification_event_id, recipient_user_id)`

### Check Constraints

- `category IN ('SECURITY','COURSE','ASSESSMENT','GRADE','SYSTEM')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_notifications_user_unread` | `recipient_user_id, created_at` | No | `read_at IS NULL` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_notifications_expiry` | `expires_at, id` | No | `expires_at IS NOT NULL` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Low-value hard-delete after expiry; security fact remains Audit/SecurityEvent.

### Audit behavior

No audit for marking read.

### Concurrency

row_version for read update; idempotent event+recipient unique.

### Security / PII classification

Recipient-only; Admin cannot browse arbitrary content without reason where sensitive.

### Important invariants

- Score/role/suspension notifications created when required

---

## `notification_preferences`

**Purpose**

User preferences cho optional email categories; mandatory security email không disable.

**Lifecycle**

Upsert preferences.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `user_id` | `BIGINT` | No |  | User |
| `category` | `VARCHAR(32)` | No |  | COURSE/ASSESSMENT/GRADE/MARKETING/SECURITY |
| `email_enabled` | `BIT` | No |  | Enable email |
| `updated_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | UTC |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`user_id, category`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `user_id` | `users(id)` | `NO ACTION` |  |

### Unique Constraints

_None._

### Check Constraints

- `category IN ('COURSE','ASSESSMENT','GRADE','MARKETING','SECURITY')`
- `category <> 'SECURITY' OR email_enabled = 1`

### Indexes

_None._

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Can delete with account anonymization if no need.

### Audit behavior

Security category change attempt may log if blocked.

### Concurrency

row_version.

### Security / PII classification

Preference data low sensitivity.

### Important invariants

- SECURITY.email_enabled must remain 1 (DB check via composite logic/service; DDL trigger/check where possible)

---

## `email_deliveries`

**Purpose**

Outbox/retry record cho email; primary business transaction không rollback do external send fail.

**Lifecycle**

PENDING → SENDING → SENT; fail → retry/FAILED.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `notification_event_id` | `BIGINT` | No |  | Event |
| `recipient_user_id` | `BIGINT` | Yes |  | User |
| `recipient_email_snapshot` | `NVARCHAR(320)` | No |  | Email destination snapshot |
| `template_code` | `VARCHAR(64)` | No |  | Template |
| `dedupe_key` | `UNIQUEIDENTIFIER` | No |  | Stable delivery idempotency key |
| `status` | `VARCHAR(20)` | No | `'PENDING'` | PENDING/SENDING/SENT/FAILED/CANCELLED |
| `attempt_count` | `INT` | No | `0` | Retries |
| `next_attempt_at` | `DATETIME2(3)` | Yes |  | Retry time |
| `sent_at` | `DATETIME2(3)` | Yes |  | UTC |
| `last_error` | `NVARCHAR(2000)` | Yes |  | Sanitized |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `notification_event_id` | `notification_events(id)` | `NO ACTION` |  |
| `recipient_user_id` | `users(id)` | `SET NULL` |  |

### Unique Constraints

- `UNIQUE (dedupe_key)`
- `UNIQUE (notification_event_id, recipient_email_snapshot, template_code)`

### Check Constraints

- `status IN ('PENDING','SENDING','SENT','FAILED','CANCELLED')`
- `attempt_count >= 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_email_delivery_queue` | `status, next_attempt_at, id` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_email_delivery_event` | `notification_event_id, status` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Operational retention after delivery; security event remains audit if needed.

### Audit behavior

Email send failure not business rollback.

### Concurrency

row_version + worker claim conditional.

### Security / PII classification

Email address PII; no sensitive body stored here.

### Important invariants

- Retry cannot duplicate logical email
- Mandatory security email ignores optional preference

---

## `audit_events`

**Purpose**

Append-only authoritative audit cho hành động Admin/Instructor quan trọng và score/security-sensitive actions.

**Lifecycle**

Append-only; very old data may move to archival storage.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `event_id` | `UNIQUEIDENTIFIER` | No | `NEWID()` | Public/correlation id |
| `actor_user_id` | `BIGINT` | Yes |  | Actor |
| `actor_roles_snapshot` | `NVARCHAR(200)` | No |  | Roles at action time |
| `action` | `VARCHAR(80)` | No |  | Action code |
| `target_type` | `VARCHAR(40)` | No |  | Target type |
| `target_id` | `BIGINT` | Yes |  | Target internal id |
| `reason` | `NVARCHAR(1000)` | Yes |  | Reason; required for sensitive actions |
| `before_json` | `NVARCHAR(MAX)` | Yes |  | Redacted before metadata |
| `after_json` | `NVARCHAR(MAX)` | Yes |  | Redacted after metadata |
| `request_id` | `UNIQUEIDENTIFIER` | Yes |  | Request correlation |
| `ip_address` | `VARCHAR(45)` | Yes |  | IP |
| `performed_as_admin` | `BIT` | No | `0` | Admin override/edit context |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `actor_user_id` | `users(id)` | `SET NULL` |  |

### Unique Constraints

- `UNIQUE (event_id)`

### Check Constraints

- `before_json IS NULL OR ISJSON(before_json)=1`
- `after_json IS NULL OR ISJSON(after_json)=1`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_audit_time` | `created_at, id` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_audit_actor_time` | `actor_user_id, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_audit_target` | `target_type, target_id, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_audit_action_time` | `action, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

App principal không có UPDATE/DELETE. Archive chỉ bằng privileged maintenance path.

### Audit behavior

Self-auditing; correction tạo new event.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Sensitive; redaction mandatory. Never password_hash/token/API key/raw answer bodies unless explicit minimal evidence.

### Important invariants

- Sensitive/destructive action must fail if required audit insert cannot commit
- No impersonation; actor is true authenticated admin/instructor

---

## `background_jobs`

**Purpose**

Generic persistence cho queue/retry common mechanics; complex domain progress stays in regrade/import/version tables.

**Lifecycle**

QUEUED → RUNNING → SUCCEEDED; failures retry by available_at until FAILED.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `job_key` | `UNIQUEIDENTIFIER` | No | `NEWID()` | Public job key |
| `job_type` | `VARCHAR(48)` | No |  | FILE_SCAN/IMPORT/REGRADE/KNOWLEDGE_INDEX/EMAIL/CLEANUP/ANALYTICS/BACKUP/EXPORT |
| `dedupe_key` | `NVARCHAR(200)` | Yes |  | Optional business idempotency key |
| `status` | `VARCHAR(20)` | No | `'QUEUED'` | QUEUED/RUNNING/SUCCEEDED/FAILED/CANCELLED |
| `priority` | `INT` | No | `100` | Queue priority |
| `attempt_count` | `INT` | No | `0` | Retries |
| `max_attempts` | `INT` | No | `5` | Max retries |
| `available_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Earliest run |
| `claimed_at` | `DATETIME2(3)` | Yes |  | Worker claim |
| `lease_expires_at` | `DATETIME2(3)` | Yes |  | Worker claim lease |
| `completed_at` | `DATETIME2(3)` | Yes |  | UTC |
| `payload_json` | `NVARCHAR(MAX)` | Yes |  | Small sanitized args; no giant document/raw secret |
| `last_error` | `NVARCHAR(2000)` | Yes |  | Sanitized |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

_None._

### Unique Constraints

- `UNIQUE (job_key)`

### Check Constraints

- `job_type IN ('FILE_SCAN','IMPORT','REGRADE','KNOWLEDGE_INDEX','EMAIL','CLEANUP','ANALYTICS','BACKUP','EXPORT')`
- `status IN ('QUEUED','RUNNING','SUCCEEDED','FAILED','CANCELLED')`
- `priority >= 0`
- `attempt_count >= 0`
- `max_attempts > 0`
- `payload_json IS NULL OR ISJSON(payload_json)=1`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_jobs_claim` | `status, available_at, priority, id` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ux_jobs_dedupe` | `job_type, dedupe_key` | Yes | `dedupe_key IS NOT NULL` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Operational history cleanup allowed; domain history remains.

### Audit behavior

Operational, not AuditEvent.

### Concurrency

row_version + claimed lease; stale RUNNING can be reclaimed safely by idempotent handler.

### Security / PII classification

Payload minimal/no secrets.

### Important invariants

- Handlers idempotent
- Generic table handles queue mechanics only; domain-specific state stays normalized

---

## `system_alerts`

**Purpose**

Admin-facing alerts for suspicious/operational conditions.

**Lifecycle**

OPEN → ACKNOWLEDGED → RESOLVED.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `alert_type` | `VARCHAR(48)` | No |  | LOW_STORAGE/BACKUP_FAILED/MALWARE/PROMPT_INJECTION/SERVICE_DOWN/... |
| `severity` | `VARCHAR(16)` | No |  | INFO/WARN/HIGH/CRITICAL |
| `status` | `VARCHAR(16)` | No | `'OPEN'` | OPEN/ACKNOWLEDGED/RESOLVED |
| `source_type` | `VARCHAR(32)` | Yes |  | SECURITY_EVENT/JOB/HEALTH/FILE/OTHER |
| `source_id` | `BIGINT` | Yes |  | Source id |
| `message` | `NVARCHAR(2000)` | No |  | Safe admin message |
| `acknowledged_by_user_id` | `BIGINT` | Yes |  | Admin |
| `acknowledged_at` | `DATETIME2(3)` | Yes |  | UTC |
| `resolved_at` | `DATETIME2(3)` | Yes |  | UTC |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `acknowledged_by_user_id` | `users(id)` | `SET NULL` |  |

### Unique Constraints

_None._

### Check Constraints

- `severity IN ('INFO','WARN','HIGH','CRITICAL')`
- `status IN ('OPEN','ACKNOWLEDGED','RESOLVED')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_system_alerts_open` | `status, severity, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_system_alerts_type` | `alert_type, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Operational cleanup after retention; underlying audit/security facts keep as needed.

### Audit behavior

Ack/resolution not necessarily security audit unless critical.

### Concurrency

row_version.

### Security / PII classification

Admin-only.

### Important invariants

- Low disk may block upload via service independent of UI alert acknowledgment

---

## `backup_runs`

**Purpose**

Metadata của backup tự động hằng ngày/manual và restore drills; không chứa backup bytes.

**Lifecycle**

RUNNING → SUCCEEDED/FAILED; verification/drill update metadata.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `backup_type` | `VARCHAR(20)` | No |  | AUTOMATIC/MANUAL/RESTORE_DRILL |
| `status` | `VARCHAR(20)` | No | `'RUNNING'` | RUNNING/SUCCEEDED/FAILED |
| `started_by_user_id` | `BIGINT` | Yes |  | Admin nếu manual |
| `storage_location` | `NVARCHAR(500)` | No |  | Logical backup destination, no secret |
| `database_backup_name` | `NVARCHAR(255)` | Yes |  | DB backup artifact |
| `file_manifest_name` | `NVARCHAR(255)` | Yes |  | Files manifest |
| `started_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | UTC |
| `completed_at` | `DATETIME2(3)` | Yes |  | UTC |
| `verified_at` | `DATETIME2(3)` | Yes |  | Integrity check |
| `restore_tested_at` | `DATETIME2(3)` | Yes |  | Restore drill |
| `last_error` | `NVARCHAR(2000)` | Yes |  | Sanitized |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `started_by_user_id` | `users(id)` | `SET NULL` |  |

### Unique Constraints

_None._

### Check Constraints

- `backup_type IN ('AUTOMATIC','MANUAL','RESTORE_DRILL')`
- `status IN ('RUNNING','SUCCEEDED','FAILED')`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_backup_runs_time` | `started_at, status` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Retain operationally according to backup policy; never treat Docker volume as backup.

### Audit behavior

Manual backup/restore action audit. Restore database requires explicit Admin confirmation and separate audit.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Location metadata only; credentials/secrets not stored.

### Important invariants

- No automatic live DB restore from backup
- Daily automatic schedule tracked

---

## `grade_exports`

**Purpose**

Sensitive CSV/Excel export request/file lifecycle với giới hạn kích thước và expiry.

**Lifecycle**

QUEUED → PROCESSING → READY → EXPIRED; failed retry as controlled job.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `public_id` | `UNIQUEIDENTIFIER` | No | `NEWSEQUENTIALID()` | ID công khai dùng trong URL/API; không thay thế kiểm tra quyền |
| `course_id` | `BIGINT` | No |  | Course |
| `requested_by_user_id` | `BIGINT` | No |  | Instructor/Admin |
| `background_job_id` | `BIGINT` | Yes |  | Job; FK deferred |
| `file_asset_id` | `BIGINT` | Yes |  | Generated sensitive asset |
| `filters_json` | `NVARCHAR(MAX)` | No |  | Applied filters |
| `status` | `VARCHAR(20)` | No | `'QUEUED'` | QUEUED/PROCESSING/READY/FAILED/EXPIRED |
| `row_count` | `INT` | Yes |  | Rows exported |
| `expires_at` | `DATETIME2(3)` | No |  | Auto-delete generated file |
| `completed_at` | `DATETIME2(3)` | Yes |  | UTC |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |
| `row_version` | `ROWVERSION` | No |  | Token lạc quan phát hiện ghi đè đồng thời |

### Primary Key

`id`

### Foreign Keys

| Columns | References | ON DELETE | Notes |
|---|---|---|---|
| `course_id` | `courses(id)` | `NO ACTION` |  |
| `requested_by_user_id` | `users(id)` | `NO ACTION` |  |
| `file_asset_id` | `file_assets(id)` | `SET NULL` |  |
| `background_job_id` | `background_jobs(id)` | `SET NULL` | Deferred cross-domain FK created in `010_cross_domain_constraints.sql`. |

### Unique Constraints

- `UNIQUE (public_id)`

### Check Constraints

- `filters_json IS NOT NULL AND ISJSON(filters_json)=1`
- `status IN ('QUEUED','PROCESSING','READY','FAILED','EXPIRED')`
- `row_count IS NULL OR row_count >= 0`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_grade_exports_user` | `requested_by_user_id, status, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |
| `ix_grade_exports_expiry` | `expires_at, status` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Generated file deleted at expires_at; export metadata short retention.

### Audit behavior

Export request is sensitive action; audit who exported which Course/filter scope.

### Concurrency

row_version.

### Security / PII classification

Sensitive; download authorized requester/admin; never public URL.

### Important invariants

- Size/row limits enforced before/while build

---

## `analytics_snapshots`

**Purpose**

Derived/cache metrics cho Dashboard; source of truth vẫn normalized learning/assessment data.

**Lifecycle**

Recomputed/replace cache; not historical truth unless specifically retained.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `scope_type` | `VARCHAR(16)` | No |  | SYSTEM/COURSE/ASSESSMENT |
| `scope_id` | `BIGINT` | Yes |  | Course/Assessment id |
| `metric_code` | `VARCHAR(64)` | No |  | Metric |
| `value_number` | `DECIMAL(18,6)` | Yes |  | Numeric metric |
| `value_json` | `NVARCHAR(MAX)` | Yes |  | Structured aggregate |
| `as_of_at` | `DATETIME2(3)` | No |  | Data timestamp |
| `expires_at` | `DATETIME2(3)` | Yes |  | Refresh deadline |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

_None._

### Unique Constraints

_None._

### Check Constraints

- `scope_type IN ('SYSTEM','COURSE','ASSESSMENT')`
- `value_json IS NULL OR ISJSON(value_json)=1`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_analytics_scope_metric` | `scope_type, scope_id, metric_code, as_of_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Safe to cleanup/recompute.

### Audit behavior

No.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Aggregates; individual details not stored here by default.

### Important invariants

- Derived values must be recomputable

---

## `system_health_snapshots`

**Purpose**

Short-retention health metadata cho Admin Dashboard (DB/worker/ClamAV/Gemini/storage).

**Lifecycle**

Append periodic snapshots; short retention.

### Columns

| Column | Type | Nullable | Default / Computed | Description |
|---|---|---:|---|---|
| `id` | `BIGINT` | No | IDENTITY(1,1) | Khóa chính nội bộ |
| `component` | `VARCHAR(32)` | No |  | WEB/DB/WORKER/CLAMAV/GEMINI/STORAGE/BACKUP |
| `status` | `VARCHAR(16)` | No |  | HEALTHY/DEGRADED/DOWN/UNKNOWN |
| `latency_ms` | `INT` | Yes |  | Observed latency |
| `details_json` | `NVARCHAR(MAX)` | Yes |  | Sanitized health metadata |
| `created_at` | `DATETIME2(3)` | No | `SYSUTCDATETIME()` | Thời điểm tạo (UTC) |

### Primary Key

`id`

### Foreign Keys

_None._

### Unique Constraints

_None._

### Check Constraints

- `component IN ('WEB','DB','WORKER','CLAMAV','GEMINI','STORAGE','BACKUP')`
- `status IN ('HEALTHY','DEGRADED','DOWN','UNKNOWN')`
- `latency_ms IS NULL OR latency_ms >= 0`
- `details_json IS NULL OR ISJSON(details_json)=1`

### Indexes

| Index | Columns | Unique | Filter | Purpose |
|---|---|---:|---|---|
| `ix_health_component_time` | `component, created_at` | No | `` | Hỗ trợ truy vấn/filter/pagination chính của table. |

### Relationships

- Quan hệ được xác định bởi các FK ở trên; hướng 1-N/N-N xem `03_ERD.md`.
- Các cross-domain pointer được tạo sau bằng DDL riêng để tránh vòng phụ thuộc lúc bootstrap.

### Delete behavior

Cleanup old snapshots; durable failures create system_alert/security/audit as appropriate.

### Audit behavior

No.

### Concurrency

Không cần optimistic lock riêng ngoài transaction thông thường.

### Security / PII classification

Admin-only; details must not expose secrets.

### Important invariants

- Operational telemetry is not business source of truth

---
