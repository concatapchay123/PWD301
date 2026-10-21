# ITERATION 32 TEST CASES

| Test ID | Requirement | Target Role | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| `TC-API-007` | REQ-SEC-01 | `STUDENT` | HTTP 400 với envelope {'success': false, 'data': null} | Trả về HTTP 404 với định dạng lỗi chuẩn hóa | **PASS** |
| `TC-API-008` | REQ-SEC-02 | `STUDENT` | Truy vấn an toàn qua tham số hóa, không rò rỉ dữ liệu | SQL Server thực thi parameterized query an toàn tuyệt đối | **PASS** |
| `TC-API-009` | REQ-SEC-03 | `STUDENT` | Từ chối 400 Bad Request kèm lý do độ dài | Validation schema chặn trước khi vào tầng cơ sở dữ liệu | **PASS** |
