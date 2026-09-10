# TASK-021 — Notifications & Email Delivery/Retry Engine

**Status:** DONE  
**Assignee:** Principal Software Architect & Lead Fullstack Python/Flask Engineer  
**Depends on:** TASK-001, TASK-002, TASK-003, TASK-011, TASK-012, TASK-018, TASK-020  

---

## Goal
Triển khai hoàn chỉnh **Động cơ Thông báo Đa kênh & Chuyển phát Email có cơ chế thử lại (Notifications & Email Delivery/Retry Engine)** cho nền tảng PWD301:
1. **Kiến trúc Outbox bất đồng bộ (Decoupled Outbox Pattern)**:
   - Tách rời hoàn toàn giao dịch ghi nhận sự kiện (in-app notification) khỏi quá trình kết nối chuyển phát email ngoại vi (SMTP / Mock Mail Client).
   - Lỗi gửi email không làm ảnh hưởng (rollback) hay gián đoạn giao dịch chính; email được ghi vào hàng đợi `email_deliveries` ở trạng thái `PENDING`.
2. **Cơ chế Backoff hàm mũ & Thử lại an toàn (Exponential Backoff & Retry Engine)**:
   - Khoảng thời gian thử lại lũy thừa theo số lần thất bại: delay = 2^(retry_count) * 60 giây.
   - Thử lại tối đa `max_retries` (mặc định 3 lần); sau đó chuyển trạng thái `FAILED`.
   - Endpoint quản trị viên cho phép kích hoạt thử lại các email thất bại (`retry_failed_emails`).
3. **Quản lý Tùy chọn Thông báo & Bất biến An ninh Bắt buộc (Mandatory Security Invariant)**:
   - Người dùng có thể tùy chỉnh bật/tắt email cho các danh mục thông thường (`COURSE`, `ASSESSMENT`, `SYSTEM`).
   - Các cảnh báo an ninh bảo mật bắt buộc (`SECURITY_PASSWORD_CHANGED`, `SECURITY_ACCOUNT_SUSPENDED`, `SECURITY_LOGIN_ANOMALY`, `ACCOUNT_SUSPENDED`, `SYSTEM_SECURITY_ALERT`) **không thể bị tắt**.
   - Mọi hành vi cố tình tắt thông báo an ninh đều bị chặn đứng ở tầng dịch vụ bằng `MandatoryNotificationOptOutError` (HTTP 400).
4. **Bảo mật tuyệt đối ADR-002 (Zero PK Leakage) & Phòng chống IDOR**:
   - Mọi API trả về public UUIDs; không làm rò rỉ bất kỳ `BIGINT PK/FK` nội bộ nào trong JSON payloads.
   - Kiểm tra quyền sở hữu chặt chẽ: người dùng chỉ được xem, đánh dấu đọc, đóng hoặc cấu hình tùy chọn thông báo của chính mình.
   - Quản trị viên (ADMIN) có quyền phát thông báo toàn hệ thống (`broadcast`) và kích hoạt retry email hàng loạt.
5. **Đồng bộ Đa giao diện (Session Web UI & REST API)**:
   - REST API đầy đủ `@jwt_required` tại `/api/notifications/...`.
   - Giao diện Web Student Jinja2 tại `/student/notifications` với thanh Notification Bell tích hợp badge số lượng tin chưa đọc.

---

## Source-of-Truth Documents Consulted
- `AGENTS.md` (Source-of-truth hierarchy, Fail-closed Invariants, ADR-002 Zero PK Leakage, Session CSRF)
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/14_NOTIFICATION_AND_EMAIL.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/api/11_NOTIFICATION_API.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/workflows/11_NOTIFICATION_WORKFLOW.md`
- `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/008_notification_audit.sql`
- `docs/decisions/ADR-002-database-identifiers.md`
- `frontend-preview/views/student/notifications.html`

---

## Deliverables & Changes
1. **Domain Exceptions (`src/pwd301/services/exceptions.py`)**:
   - `NotificationError`, `NotificationNotFoundError`, `NotificationPreferenceError`, `MandatoryNotificationOptOutError`, `EmailDeliveryError`, `EmailDeliveryNotFoundError`, `EmailRateLimitExceededError`.
2. **Model Enhancements & ADR-002 Compliance (`src/pwd301/models/notification_audit.py`)**:
   - `NotificationEvent`: `public_id` (`event_key`).
   - `Notification`: `public_id`, `is_read` helper, `to_dict()` che giấu hoàn toàn `BIGINT PK/FK`.
   - `NotificationPreference`: `to_dict()`.
   - `EmailDelivery`: `public_id` (`dedupe_key`), `to_dict()`.
3. **Email Delivery & Retry Service (`src/pwd301/services/email_service.py`)**:
   - `MockMailClient` & `validate_email_syntax`.
   - `enqueue_email`: Ghi email vào hàng đợi `email_deliveries` với deduplication và tự động tạo `NotificationEvent` nếu chưa có.
   - `send_single_email`: Chuyển phát email, tính toán exponential backoff khi lỗi.
   - `process_email_queue`: Xử lý theo lô các email đến hạn (`next_attempt_at <= now`).
   - `retry_failed_emails`: Kích hoạt thử lại thủ công bởi Admin.
4. **Notification Service (`src/pwd301/services/notification_service.py`)**:
   - `emit_event`: Ghi nhận sự kiện với payload redaction (loại bỏ mật khẩu/tokens).
   - `determine_event_category`: Phân loại tự động các sự kiện.
   - `dispatch_notification`: Tạo in-app notification và kích hoạt outbox email nếu danh mục được phép hoặc là sự kiện bảo mật bắt buộc.
   - `list_user_notifications`: Liệt kê thông báo phân trang, lọc chưa đọc/danh mục.
   - `get_unread_count`: Đếm số thông báo chưa đọc cho badge.
   - `mark_notification_as_read`, `mark_all_as_read`, `dismiss_notification`: Thao tác trạng thái an toàn chống IDOR.
   - `get_user_preferences`, `update_user_preferences`: Quản lý sở thích nhận email; chặn tắt danh mục bảo mật (`MandatoryNotificationOptOutError`).
   - `broadcast_system_notification`: Phát thông báo toàn hệ thống (Admin only).
5. **REST API (`src/pwd301/blueprints/api_notifications/`)**:
   - `GET /api/notifications`
   - `GET /api/notifications/unread-count`
   - `PATCH /api/notifications/<id>/read`
   - `POST /api/notifications/mark-all-read`
   - `DELETE /api/notifications/<id>/dismiss`
   - `GET /api/notifications/preferences`
   - `PUT /api/notifications/preferences`
   - `POST /api/notifications/broadcast`
   - `POST /api/notifications/emails/retry-failed`
6. **Web UI & Session Integration (`src/pwd301/templates/notifications/`, `src/pwd301/templates/base.html`, `src/pwd301/blueprints/student/routes.py`)**:
   - Template Jinja2 `notifications/index.html` hiển thị bộ lọc, phân trang, hành động đọc/xóa.
   - Header `base.html` bổ sung notification bell liên kết tới trang thông báo và hiển thị badge.
   - Route `GET /student/notifications` được bảo vệ bởi session auth.
7. **Admin Blueprints Integration (`src/pwd301/blueprints/admin/routes.py`)**:
   - Hỗ trợ `/api/admin/notifications/broadcast` và `/api/admin/emails/retry-failed`.
8. **Comprehensive Test Suites (32 tests total — 100% PASS)**:
   - `tests/unit/test_notification_service.py` (10 tests)
   - `tests/unit/test_email_service.py` (8 tests)
   - `tests/security/test_notification_idor.py` (7 tests)
   - `tests/api/test_notification_api.py` (7 tests)

---

## Verification Results
- Gate 1: `python scripts/repo_check.py` — **PASS**
- Gate 2: `python -m compileall -q src tests scripts` — **PASS**
- Gate 3: `ruff check src tests scripts` — **PASS** (0 errors)
- Gate 4: `ruff format --check src tests scripts` — **PASS** (140 files already formatted)
- Gate 5: `mypy src` — **PASS** (0 issues across 69 source files)
- Gate 6: TASK-021 test suites — **PASS** (32/32 passed)
- Gate 7: Full regression pytest — **PASS** (592/592 passed)
- Gate 8: `./scripts/verify.ps1` — **PASS**
