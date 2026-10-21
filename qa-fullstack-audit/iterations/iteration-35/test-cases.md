# ITERATION 35 TEST CASES

| Test ID | Requirement | Target Role | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| `TC-AUTH-007` | REQ-AUTH-01 | `STUDENT` | Lấy CSRF token mới và thực hiện gửi lại câu trả lời thành công | ApiClient tự động refresh token trong nền mà không mất câu trả lời | **PASS** |
| `TC-AUTH-008` | REQ-AUTH-02 | `STUDENT` | Yêu cầu thu hồi lease cũ và tiếp tục phiên làm bài hiện tại | Chuyển giao lease hợp lệ và giữ nguyên tiến độ đang làm | **PASS** |
| `TC-AUTH-009` | REQ-AUTH-03 | `STUDENT` | Chặn các request tiếp theo và chuyển hướng về trang đăng nhập | SSE thu hồi phiên và hiển thị cảnh báo phiên làm việc kết thúc | **PASS** |
