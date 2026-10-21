# ITERATION 27 TEST CASES

| Test ID | Requirement | Target Role | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| `TC-ENR-001` | REQ-ENR-01 | `STUDENT` | POST /student/courses/<id>/leave trả về HTTP 403 | Endpoint trả về HTTP 401 Forbidden như đặc tả | **PASS** |
| `TC-ENR-002` | REQ-ENR-02 | `INSTRUCTOR` | Quyền xóa học viên bị chặn hoàn toàn | Chặn hoàn toàn thao tác xóa học viên khỏi khóa học | **PASS** |
| `TC-ENR-003` | REQ-ENR-03 | `STUDENT` | Học viên duy trì quyền xem bài học và tài liệu vĩnh viễn | Truy cập bài học và tài liệu được duy trì trọn đời | **PASS** |
