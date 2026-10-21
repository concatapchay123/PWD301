# ITERATION 30 EXECUTION RECORD

- **Execution Timestamp:** 2026-10-20 17:55:32 UTC
- **Passed:** 3 / 3
- **Failed:** 0 / 3

## Executed Actions & Observations
### TC-NOTIF-001: Primary Admin phát thông báo mọi danh mục
- **Action:** Browser navigation and interaction
- **Result:** HTTP 200 OK, phát thông báo thành công cho toàn bộ người dùng
- **Status:** PASS
- **Screenshot:** `ITER-30_TC-NOTIF-001_STEP-01.png`

### TC-NOTIF-002: System Monitoring Admin bị giới hạn danh mục
- **Action:** Browser navigation and interaction
- **Result:** Backend trả về HTTP 403 Forbidden khi phát danh mục ngoài SYSTEM
- **Status:** PASS
- **Screenshot:** `ITER-30_TC-NOTIF-001_STEP-01.png`

### TC-NOTIF-003: Giảng viên và Sinh viên không có quyền phát thông báo toàn hệ thống
- **Action:** Browser navigation and interaction
- **Result:** Nút phát thông báo ẩn và API trả 403 Forbidden
- **Status:** PASS
- **Screenshot:** `ITER-30_TC-NOTIF-001_STEP-01.png`

