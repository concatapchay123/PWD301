# ITERATION 28 TEST CASES

| Test ID | Requirement | Target Role | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| `TC-EXAM-001` | REQ-EXAM-01 | `STUDENT` | Trả về kết quả chấm ban đầu, không tạo bản ghi chấm trùng lặp | Submit là idempotent, cùng điểm số và cùng mã kết quả | **PASS** |
| `TC-EXAM-002` | REQ-EXAM-02 | `STUDENT` | Máy chủ từ chối nhận câu trả lời nộp muộn | Thời gian do server quyết định, từ chối nộp quá hạn | **PASS** |
| `TC-EXAM-003` | REQ-EXAM-03 | `STUDENT` | Autosave gói tin cũ không ghi đè gói tin mới | Sequence number bảo đảm thứ tự cập nhật chính xác | **PASS** |
