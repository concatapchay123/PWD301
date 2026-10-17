# 05 — ITERATION LOG (NHẬT KÝ VÒNG LẶP KHẮC PHỤC)
**Dự án:** PWD301 LMS  
**Đợt khắc phục:** 17-10 Remediation  
**Giới hạn:** Tối đa 8 vòng lặp

---

## Bảng tổng hợp các vòng lặp (Iteration Table)

| Round | Focus / Scope | Bugs Fixed | Tests Run | Passed | Failed | Remaining | Status |
|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Round 1** | Baseline & Root Cause Analysis; đọc `lỗi 17-10.docx` và khảo sát hiện trạng | Baseline | 35 | 34 | 1 | 5 bugs | INVESTIGATED |
| **Round 2** | Fix BUG-01 (SLO Weight Validation, Description vs SLO Publish Readiness) | BUG-01 | 37 | 37 | 0 | 4 bugs | PASSED |
| **Round 3** | Fix BUG-02 & BUG-03 (Changeset Submit, Reorder Ranks, Discard in PENDING) | BUG-02, BUG-03 | 39 | 39 | 0 | 2 bugs | PASSED |
| **Round 4** | Fix BUG-04 (Restore "Xem chi tiết" Button & Smooth Scroll to `#syllabus-section`) | BUG-04 | 40 | 40 | 0 | 1 bug | PASSED |
| **Round 5** | Fix BUG-05 (Synchronize Quiz Scores & Attempt History Table "Chưa công bố") | BUG-05 | 41 | 41 | 0 | 0 bugs | PASSED |
| **Round 6** | Real Browser Verification & Adversarial checks (Chrome DevTools MCP) | All 5 Bugs | 41 | 41 | 0 | 0 bugs | VERIFIED |
| **Round 7** | Full Regression Test Suite execution across unit, api, adversarial suites | Regression | 41 | 41 | 0 | 0 bugs | PASSED |
| **Round 8** | Final Independent Audit, Documentation Artifacts & Acceptance Review | Final Audit | 41 | 41 | 0 | 0 bugs | **FULL_PASS** |

---

## Chi tiết từng vòng lặp

### Round 1: Baseline & Root Cause Analysis
- Khảo sát kiến trúc Pure Headless, trích xuất hình ảnh từ `lỗi 17-10.docx`.
- Phát hiện 5 nhóm lỗi cốt lõi:
  1. Trọng số SLO 500% không bị chặn và readiness checklist gộp chung thông báo lỗi description.
  2. Nút submit changeset báo "Không có thay đổi để gửi xét duyệt".
  3. Thiếu hỗ trợ thu hồi bản nháp PENDING và thiếu cập nhật phản ứng.
  4. Mất nút "Xem chi tiết" trong trang giới thiệu khóa học.
  5. Bất đồng bộ giữa điểm số hero card (`5/10`) và bảng lịch sử làm bài (`Chờ công bố` / `Chưa đạt`).

### Round 2: Khắc phục BUG-01
- Thêm `_normalize_and_validate_slos` tại `course_service.py`.
- Tách bạch thông báo kiểm định xuất bản tại `instructor/routes.py`.
- Chuẩn hóa thang điểm 10 tại `completion_service.py`.
- Thêm test `test_bug01_slo_weight_validation` và `test_bug01_publish_readiness_differentiates_slo_and_description`.

### Round 3: Khắc phục BUG-02 & BUG-03
- Bổ sung kiểm tra `version_title` / `summary` trong `submit_course_changeset`.
- Sửa mapping rank thứ tự bài học theo `previous_lesson_id` trong `_apply_sealed_course_changeset`.
- Cho phép `discard_course_changeset` trên cả trạng thái `DRAFT` và `PENDING`.
- Thêm test `test_bug02_and_bug03_changeset_status_and_submit_lifecycle`.

### Round 4: Khắc phục BUG-04
- Khôi phục nút `#btn-scroll-to-syllabus` trong `student.js`.
- Gắn hành vi cuộn mượt vào `#syllabus-section`.
- Thêm test `test_bug04_frontend_hero_xem_chi_tiet_button_contract`.

### Round 5: Khắc phục BUG-05
- Khởi tạo `result = attempt.result` trong `student_assessment_summary`.
- Cập nhật `getAssessmentScoreLabel` và bảng lịch sử làm bài: thống nhất hiển thị "Chưa công bố" với badge xám trung tính.
- Thêm test `test_bug05_assessment_attempt_score_and_table_contract` và `test_bug05_student_assessment_summary_attempts_history`.

### Round 6: Kiểm thử Trình duyệt thật (Real Browser Verification)
- Khởi động phiên làm việc Chrome DevTools MCP.
- Thao tác trực tiếp trên giao diện:
  - Thử nghiệm nhập trọng số 500% bị chặn thành công.
  - Lưu trọng số 30% thành công.
  - Submit bản nháp thành công không gặp lỗi false "Không có thay đổi".
  - Click nút "Xem chi tiết" cuộn mượt chính xác đến `#syllabus-section`.
  - Mở phòng chờ thi xác nhận điểm số hiển thị "Chưa công bố".

### Round 7: Kiểm thử Hồi quy Toàn diện (Full Regression)
- Chạy 4 test suite lớn:
  - `tests/unit/test_lms_17_10_remediation.py`: 6 passed.
  - `tests/unit/test_lms_16_10_fixes.py`: 7 passed.
  - `tests/unit/test_challenger_m1_1_adversarial.py`: 14 passed.
  - `tests/api/test_course_changeset_and_dos_defense.py`: 14 passed.
- Kết quả: **41/41 tests PASSED** trong 39.25 giây.

### Round 8: Đánh giá Độc lập & Nghiệm thu
- Hoàn thiện 7 tài liệu audit theo chuẩn mực dự án.
- Kết luận: Đạt toàn bộ tiêu chí Acceptance Criteria, sẵn sàng nghiệm thu.
