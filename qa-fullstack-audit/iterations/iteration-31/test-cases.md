# ITERATION 31 TEST CASES

| Test ID | Requirement | Target Role | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| `TC-STRESS-001` | REQ-UI-01 | `STUDENT` | Chỉ gửi duy nhất 1 request và nút vô hiệu hóa trong khi chờ | Debounce 300ms ngăn chặn hoàn toàn request trùng lặp | **PASS** |
| `TC-STRESS-002` | REQ-UI-02 | `STUDENT` | Chỉ tạo duy nhất 1 bản ghi ghi danh | Cơ chế Idempotent khóa ghi danh trùng lặp | **PASS** |
| `TC-STRESS-003` | REQ-UI-03 | `STUDENT` | Giao diện quay về trạng thái cũ kèm Toast báo lỗi | Optimistic update rollback an toàn khi request thất bại | **PASS** |
