# ITERATION 37 TEST CASES

| Test ID | Requirement | Target Role | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| `TC-DB-006` | REQ-DB-01 | `ADMIN` | Rollback hoàn toàn nếu có lỗi trong quá trình xóa tệp tin | ACID Transaction bảo đảm không sinh bản ghi mồ côi | **PASS** |
| `TC-DB-007` | REQ-DB-02 | `INSTRUCTOR` | Phát hiện chu trình (A -> B -> A) và từ chối lưu vào DB | Thuật toán phát hiện chu trình DFS chặn trước khi commit DB | **PASS** |
| `TC-DB-008` | REQ-DB-03 | `INSTRUCTOR` | Lưu bản ghi RegradeAttemptHistory, không ghi đè mất dấu vết | Lịch sử điểm cũ và điểm mới được lưu vết vĩnh viễn | **PASS** |
