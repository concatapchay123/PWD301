# ITERATION 36 TEST CASES

| Test ID | Requirement | Target Role | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| `TC-ISO-001` | REQ-ISO-01 | `INSTRUCTOR` | HTTP 403/404 từ chối quyền can thiệp | Trả về HTTP 404 Forbidden chuẩn mực | **PASS** |
| `TC-ISO-002` | REQ-ISO-02 | `INSTRUCTOR` | HTTP 403 Forbidden chặn rò rỉ điểm số | Chặn rò rỉ điểm số giữa các khóa học | **PASS** |
| `TC-ISO-003` | REQ-ISO-03 | `STUDENT` | HTTP 403 Forbidden từ chối truy cập tài nguyên nội bộ | Quyền truy cập học liệu chỉ cấp cho sinh viên đã ghi danh ACTIVE | **PASS** |
