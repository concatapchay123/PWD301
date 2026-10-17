# 02 — IMPLEMENTATION LOG (NHẬT KÝ TRIỂN KHAI MÃ NGUỒN)
**Dự án:** PWD301 LMS  
**Đợt khắc phục:** 17-10 Remediation  
**Tiêu chuẩn:** Pure Headless REST API, Anti-Hallucination, Zero-Regression

---

## 1. Danh sách tệp tin đã chỉnh sửa (Modified Files)

### Backend Services & Models
1. **`src/pwd301/services/course_service.py`**
   - Triển khai hàm `_normalize_and_validate_slos(slos: Any) -> list[dict[str, Any]]`:
     - Kiểm tra kiểu dữ liệu đầu vào.
     - Ép kiểu trọng số `weight` sang `float`.
     - Giới hạn cứng trong khoảng `[0.0, 100.0]`. Từ chối số âm hoặc số lớn hơn 100.
     - Kiểm tra chuỗi tiêu đề `title` không được rỗng sau khi trim whitespace.
   - Tích hợp `_normalize_and_validate_slos` vào cả `create_course` và `update_course`.

2. **`src/pwd301/blueprints/instructor/routes.py`**
   - Trong `validate_course_publish_readiness`:
     - Tách rẽ nhánh kiểm tra: `course.description` (tối thiểu 20 ký tự thực tế) và `course.learning_outcomes` (tối thiểu 1 mục chuẩn đầu ra hợp lệ).
     - Trả về thông báo chi tiết độc lập:
       - `info_detail = "Mô tả khóa học chưa đạt yêu cầu (cần tối thiểu 20 ký tự thực tế, không dùng nội dung mẫu)."`
       - `info_detail = "Khóa học cần có ít nhất một chuẩn đầu ra (SLO) được xác định."`
   - Bổ sung rate limiting kiểm soát tần suất gọi endpoint sắp xếp lại bài học (`reorder_curriculum`).

3. **`src/pwd301/services/lesson_service.py`**
   - Trong `submit_course_changeset`:
     - Bổ sung kiểm tra `version_title` hoặc `summary` do giảng viên nhập vào metadata đợt duyệt. Nếu có thông tin này hoặc có bài học nháp, công nhận `has_changes = True`.
     - Ngăn chặn triệt để ngoại lệ sai `CourseValidationError("Không có thay đổi để gửi xét duyệt")`.
   - Trong `_apply_sealed_course_changeset`:
     - Thêm cơ chế tra cứu `previous_lesson_id` để ánh xạ chính xác vị trí bài học kế thừa khi admin phê duyệt đợt cập nhật.
   - Trong `discard_course_changeset`:
     - Cho phép hủy và xóa bản nháp ở cả 2 trạng thái `DRAFT` và `PENDING`.
   - Thêm dispatch notifications:
     - `COURSE_CHANGE_REQUESTED` (gửi Admin khi giảng viên submit).
     - `COURSE_CHANGE_APPROVED` (gửi Giảng viên khi Admin duyệt).
     - `COURSE_CHANGE_REJECTED` (gửi Giảng viên kèm lý do khi Admin từ chối).

4. **`src/pwd301/services/completion_service.py`**
   - Trong `_normalize_completion_criteria`:
     - Tự động chuẩn hóa `minimum_grade_score` sang thang điểm 10 chuẩn mực nếu dữ liệu gốc truyền vào nằm trong khoảng `(10.0, 100.0]`.

5. **`src/pwd301/services/assessment_student_service.py`**
   - Trong `student_assessment_summary`:
     - Khởi tạo `result = attempt.result` ngay đầu vòng lặp duyệt `attempts`.
     - Trả về đồng bộ thuộc tính `score`, `raw_score`, `max_score`, `passed`, `is_score_released` cho từng phần tử lịch sử.

### Frontend SPA Views
6. **`frontend/assets/js/views/instructor.js`**
   - Trong `renderSLOs`:
     - Thêm sự kiện `oninput` trên ô nhập trọng số: nếu nhập `< 0` hoặc `> 100`, lập tức viền đỏ ô input và hiển thị text cảnh báo dưới trường.
   - Thêm phương thức `InstructorView.refreshChangesetStatus(courseId, container)`:
     - Tự động gọi API `/instructor/courses/<id>/changeset/status` sau mỗi mutation.
     - Cập nhật DOM thanh tác vụ changeset (Working Draft Action Bar) trực tiếp, không yêu cầu F5.

7. **`frontend/assets/js/views/student.js`**
   - Trong `renderCourseIntro`:
     - Thêm nút `#btn-scroll-to-syllabus` ("Xem chi tiết") với thiết kế cân đối cạnh `#btn-enroll-course`.
     - Gắn sự kiện `onclick` kích hoạt `scrollIntoView({ behavior: 'smooth', block: 'start' })` đến `#syllabus-section`.
   - Trong `getAssessmentScoreLabel`:
     - Hỗ trợ cả `data.display_score` và `data.score`.
     - Hiển thị thống nhất `'Chưa công bố'` khi `score.is_released === false`.
   - Trong bảng lịch sử làm bài (`attemptsHistory`):
     - Gán cột "Điểm số": `${attemptScore} / ${maxScore}` khi đã công bố, và `'Chưa công bố'` khi chưa công bố.
     - Gán cột "Kết quả": Badge xám trung tính `'Chưa công bố'` (`bg-slate-100 text-slate-600`) khi chưa công bố, triệt tiêu badge đỏ 'Chưa đạt'.

---

## 2. API Contract & Architectural Invariants Preserved
- **Pure Headless:** Không thêm bất kỳ template Jinja (`.html`) hay static asset ngoài nào.
- **REST JSON Envelopes:** Toàn bộ API trả về cấu trúc chuẩn:
  ```json
  {
    "success": true,
    "data": { ... },
    "error": null
  }
  ```
- **Single Active Editing Lease (Algorithm 07):** Giữ nguyên quy chế độc quyền phiên làm bài thi.
- **Wall-Clock Zero-Trust:** Giữ nguyên quy chế tích lũy thời gian thực qua heartbeat.
