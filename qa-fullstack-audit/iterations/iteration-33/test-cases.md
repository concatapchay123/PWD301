# ITERATION 33 TEST CASES

| Test ID | Requirement | Target Role | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| `TC-SEC-006` | REQ-FILE-01 | `STUDENT` | HTTP 403 / 423 từ chối tải tệp tin chưa được quét sạch | Fail-Closed: Tệp PENDING hoàn toàn không thể tải | **PASS** |
| `TC-SEC-007` | REQ-FILE-02 | `STUDENT` | Chuyển trạng thái QUARANTINED và xóa khỏi vùng tải của học viên | Tệp nhiễm bị cô lập trong thư mục cách ly, học viên không thể xem | **PASS** |
| `TC-SEC-008` | REQ-FILE-03 | `INSTRUCTOR` | Từ chối với thông báo: 'Hệ thống không hỗ trợ tệp nén...' | Thông báo từ chối tiếng Việt hiển thị chính xác từng từ | **PASS** |
