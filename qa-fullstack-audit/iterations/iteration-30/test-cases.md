# ITERATION 30 TEST CASES

| Test ID | Requirement | Target Role | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| `TC-NOTIF-001` | REQ-NOTIF-01 | `ADMIN` | Cho phép phát thông báo SYSTEM, ACADEMIC, GENERAL | HTTP 200 OK, phát thông báo thành công cho toàn bộ người dùng | **PASS** |
| `TC-NOTIF-002` | REQ-NOTIF-02 | `SYS_ADMIN` | Chỉ được phát thông báo danh mục SYSTEM, từ chối danh mục khác (403) | Backend trả về HTTP 403 Forbidden khi phát danh mục ngoài SYSTEM | **PASS** |
| `TC-NOTIF-003` | REQ-NOTIF-03 | `INSTRUCTOR` | Ẩn giao diện phát thông báo và API trả về 403 | Nút phát thông báo ẩn và API trả 403 Forbidden | **PASS** |
