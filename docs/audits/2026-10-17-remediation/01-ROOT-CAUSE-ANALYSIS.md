# 01 — ROOT CAUSE ANALYSIS (PHÂN TÍCH NGUYÊN NHÂN GỐC)
**Dự án:** PWD301 LMS  
**Đợt khắc phục:** 17-10 Remediation  
**Tài liệu tham chiếu:** `lỗi 17-10.docx`

---

## 1. BUG-01: Giảng viên đã chỉnh sửa chuẩn đầu ra nhưng vẫn không thể gửi xét duyệt

### Triệu chứng (Symptoms)
- Trong giao diện "Biên tập Trang Giới thiệu & Học vụ", giảng viên thay đổi SLO và lưu thành công, nhưng hệ thống kiểm tra xuất bản (readiness checklist) vẫn báo `4/5 tiêu chuẩn`, mục "Thông tin khóa học & Chuẩn đầu ra (SLOs)" chưa đạt.
- Thông báo checklist hiển thị dòng gây hiểu nhầm: *"Mô tả khóa học chưa đạt yêu cầu (cần tối thiểu 20 ký tự thực tế, không dùng nội dung mẫu)"*.
- Trong giao diện SLO xuất hiện các trọng số dị thường như `500%`, `50%`.

### Nguyên nhân gốc đã xác minh (Verified Root Cause)
1. **Thiếu kiểm tra độc lập và thông báo gộp trong Publish Readiness Validator:**
   - Trong `src/pwd301/blueprints/instructor/routes.py` (hàm `validate_course_publish_readiness`), điều kiện kiểm tra mô tả khóa học (`len(course.description) >= 20`) và điều kiện có tối thiểu 1 SLO (`len(course.learning_outcomes) > 0`) bị gộp vào chung một tiêu chí `"info"`. Khi tiêu chí này thất bại, hệ thống luôn gán `info_detail = "Mô tả khóa học chưa đạt yêu cầu (cần tối thiểu 20 ký tự thực tế, không dùng nội dung mẫu)"` ngay cả khi lỗi thực sự nằm ở việc chưa có SLO hoặc ngược lại.
2. **Thiếu Validation chặn biên trọng số SLO (0% - 100%):**
   - Ở tầng backend (`src/pwd301/services/course_service.py`), hàm `create_course` và `update_course` chỉ kiểm tra kiểu `list[dict]` cơ bản, không có bước normalize và validate biên độ `0 <= weight <= 100` (hoặc `0.0 <= weight <= 1.0`). Dữ liệu nhập `500%` được lưu nguyên trạng vào JSON field `learning_outcomes`.
   - Ở tầng frontend (`frontend/assets/js/views/instructor.js`), hàm `renderSLOs` cho phép nhập bất kỳ số nào mà không kiểm tra validation ngay khi nhập (oninput) và khi bấm lưu.
3. **Lệch thang điểm điều kiện hoàn thành (Completion Criteria Scale Inconsistency):**
   - Trong dữ liệu mẫu/seed data cũ, `minimum_grade_score` của khóa học được nhập là `80` (mang nghĩa 80%), nhưng quy tắc khảo thí PWD301 áp dụng thang điểm 10 (`0 <= score <= 10`), dẫn đến validation của `completion_service.py` trả về lỗi khi kiểm tra điều kiện xuất bản.

### Biện pháp xử lý (Remediation)
- Bổ sung `_normalize_and_validate_slos` tại `course_service.py` chặn triệt để trọng số ngoài khoảng [0, 100].
- Bổ sung validation real-time trên giao diện `instructor.js`.
- Phân rã thông báo lỗi trong `validate_course_publish_readiness`: chỉ ra chính xác trường nào không đạt (`info_detail` cho description riêng, `slo_detail` cho SLO riêng).
- Tự động chuẩn hóa thang điểm 10 trong `completion_service.py` (`score / 10` nếu giá trị `> 10 and <= 100`).

---

## 2. BUG-02: Có thay đổi nhưng hệ thống báo “Không có thay đổi để gửi xét duyệt”

### Triệu chứng (Symptoms)
- Giảng viên sửa đổi giáo trình, thêm bài học mới hoặc cập nhật nội dung bài học, lưu thành công.
- Khi mở modal "Gửi duyệt đợt cập nhật", nhập tiêu đề đợt duyệt và bấm "Gửi Quản trị viên", hệ thống bật toast thông báo: *"Không có thay đổi để gửi xét duyệt"*.

### Nguyên nhân gốc đã xác minh (Verified Root Cause)
1. **Tiêu chí phát hiện thay đổi (`has_meaningful_changes`) bỏ qua metadata đợt cập nhật:**
   - Trong `src/pwd301/services/lesson_service.py` (hàm `submit_course_changeset`), phương thức kiểm tra `changeset.change_summary` chỉ đếm các mục trong bảng con `CourseChangeRequestItem`. Khi giảng viên chuẩn bị một đợt cập nhật lớn có ghi chú `version_title` và `summary`, nếu các bài học nháp đã tồn tại trong changeset nhưng chưa liên kết snapshot đầy đủ, diff engine trả về mảng rỗng và throw `CourseValidationError("Không có thay đổi để gửi xét duyệt")`.
2. **Lỗi mapping thứ tự bài học (Curriculum Reordering Rank Mapping):**
   - Khi bài học được sửa trong bản nháp, một bản ghi revision mới được tạo ra với `public_id` mới và bản ghi cũ bị đánh dấu `HISTORICAL`. Trong hàm `_apply_sealed_course_changeset`, thuật toán sắp xếp lại vị trí (`ranks`) chỉ tìm theo `public_id` cũ, khiến việc áp dụng thứ tự mới bị trượt hoặc không tính là thay đổi hợp lệ.
3. **Trạng thái bản nháp không phản ứng cục bộ (Lack of Reactive Invalidation):**
   - Sau khi lưu bài học hoặc metadata, frontend không gọi hàm làm mới trạng thái changeset, khiến client giữ trạng thái `has_changes = false` đã nạp từ trước.

### Biện pháp xử lý (Remediation)
- Cập nhật `submit_course_changeset`: công nhận đợt cập nhật có `version_title` hoặc `summary` hoặc bài học nháp hợp lệ.
- Bổ sung logic ánh xạ `previous_lesson_id` trong `_apply_sealed_course_changeset` để kế thừa thứ tự chính xác.
- Bổ sung `refreshChangesetStatus` trên frontend để tự động cập nhật UI sau mỗi thao tác lưu.

---

## 3. BUG-03: Thống nhất cơ chế bản nháp khóa học (Unified Course Draft)

### Triệu chứng (Symptoms)
- Các chỉnh sửa phân mảnh của giảng viên có nguy cơ tạo ra nhiều yêu cầu xét duyệt riêng lẻ hoặc không thể gửi duyệt đồng nhất.
- Nút "Hủy bỏ bản nháp" (Discard Changeset) bị chặn khi changeset ở trạng thái `PENDING`.
- Cần F5 để thấy thay đổi mới nhất của bản nháp trên giao diện.

### Nguyên nhân gốc đã xác minh (Verified Root Cause)
1. **Thiếu hỗ trợ trạng thái PENDING trong `discard_course_changeset`:**
   - Service `lesson_service.py` ban đầu chỉ cho phép hủy khi trạng thái là `DRAFT`. Nếu giảng viên đã bấm gửi duyệt (`PENDING`) nhưng phát hiện sai sót cần thu hồi để sửa tiếp, hệ thống ném ngoại lệ 400.
2. **Thiếu cơ chế đồng bộ DOM tức thì sau Mutation:**
   - Client không lắng nghe hoặc phát tín hiệu cập nhật sau khi các API `/instructor/courses/<id>/changeset/*` hoàn tất thành công.

### Biện pháp xử lý (Remediation)
- Mở rộng `discard_course_changeset` cho phép thu hồi cả trạng thái `DRAFT` và `PENDING`.
- Khóa chặt mọi chỉnh sửa của khóa học đã xuất bản vào duy nhất 01 bản nháp `COURSE_VERSION_CHANGESET`.
- Tích hợp thông báo hệ thống tự động `COURSE_CHANGE_REQUESTED`, `COURSE_CHANGE_APPROVED`, `COURSE_CHANGE_REJECTED`.

---

## 4. BUG-04: Khôi phục nút "Xem chi tiết" và Smooth Scrolling

### Triệu chứng (Symptoms)
- Trong trang chi tiết khóa học của học viên (`#/student/courses/intro?id=...`), khu vực hero card giới thiệu khóa học bị thiếu mất nút **"Xem chi tiết"** cạnh nút "Ghi danh khóa học".
- Học viên không có lối tắt điều hướng nhanh xuống phần khung chương trình đào tạo.

### Nguyên nhân gốc đã xác minh (Verified Root Cause)
- Trong template literal của `frontend/assets/js/views/student.js` (hàm `renderCourseIntro`), khối markup nút hành động hero card chỉ hiển thị duy nhất nút `#btn-enroll-course`, nút `#btn-scroll-to-syllabus` bị bỏ quên sau các đợt tái cấu trúc giao diện headless.

### Biện pháp xử lý (Remediation)
- Bổ sung nút `id="btn-scroll-to-syllabus"` ("Xem chi tiết") với icon `menu_book`, bố cục cân đối cạnh nút ghi danh.
- Gắn sự kiện `onclick` gọi `target.scrollIntoView({ behavior: 'smooth', block: 'start' })` nhắm vào `#syllabus-section`.

---

## 5. BUG-05: Bất đồng bộ điểm và trạng thái bài kiểm tra

### Triệu chứng (Symptoms)
- Thẻ tổng quan (Hero card) và bảng lịch sử làm bài (Attempt history table) hiển thị thông tin bất đồng bộ: Thẻ điểm hiển thị `5/10` nhưng bảng lịch sử cột "Điểm số" ghi `Chờ công bố`, cột "Kết quả" lại ghi `Chưa đạt`.
- Khi điểm thi chưa đến thời điểm công bố, học viên bị lộ trạng thái rớt (`Chưa đạt`) qua màu badge đỏ.

### Nguyên nhân gốc đã xác minh (Verified Root Cause)
1. **Lỗi logic biến nội bộ trong `student_assessment_summary`:**
   - Trong `src/pwd301/services/assessment_student_service.py`, vòng lặp `for attempt in attempts:` kiểm tra thuộc tính `result.raw_score` nhưng quên khởi tạo `result = attempt.result`, gây nguy cơ `UnboundLocalError` khi bài thi có lượt nạp.
2. **Bất đồng bộ chuỗi hiển thị trên Frontend:**
   - Trong `frontend/assets/js/views/student.js`, hàm `getAssessmentScoreLabel` trả về `'Chưa công bố'` nhưng bảng lịch sử lại gán tĩnh `'Chờ công bố'` cho cột điểm số, và gán `'Chưa đạt'` (badge đỏ) cho cột kết quả ngay cả khi `!isReleased`.

### Biện pháp xử lý (Remediation)
- Sửa `assessment_student_service.py`: gán `result = attempt.result` ngay đầu vòng lặp.
- Đồng bộ hóa toàn bộ trạng thái hiển thị: Khi chưa công bố điểm (`!is_score_released`), cả hero card, cột điểm số và cột kết quả đều hiển thị thống nhất là **"Chưa công bố"** với huy hiệu xám trung tính (`bg-slate-100 text-slate-600`), triệt tiêu việc rò rỉ kết quả và mâu thuẫn giao diện.
