# ITERATION 25 TEST CASES

| Test ID | Requirement | Target Role | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| `TC-CONC-006` | REQ-CONC-01 | `INSTRUCTOR` | Cập nhật metadata khóa học thành công, không xung đột khóa | HTTP 200 OK, Outline đồng bộ realtime | **PASS** |
| `TC-CONC-007` | REQ-CONC-02 | `STUDENT` | Duy trì duy nhất 01 bản ghi Enrollment ACTIVE | Database ghi nhận chính xác 1 bản ghi Enrollment duy nhất | **PASS** |
| `TC-CONC-008` | REQ-CONC-03 | `STUDENT` | Mỗi sinh viên sở hữu snapshot câu hỏi và editing lease độc lập | Tách biệt hoàn toàn snapshot câu hỏi và lease kiểm tra | **PASS** |
