# TASK-076 — Comprehensive Remediation: Lesson Video Delivery, Revision Lifecycle Resource Inheritance, Approval Race-Condition Hardening & Frontend Multi-Tier Fallback

**Status:** DONE  
**Assignee:** Principal Systems Architect & Senior Full-Stack Engineer  
**Started Date:** 2026-09-30  
**Completed Date:** 2026-09-30  

---

## 1. Goal & Architectural Resolution Summary

Khắc phục triệt để và toàn diện sự cố: Bài giảng của Giảng viên có video đã được Quản trị viên (Admin) xét duyệt nhưng phía Học viên (Student) lại không hiển thị trình phát video (hoàn toàn biến mất):
1. **Bảo toàn Tài nguyên qua Vòng đời Phiên bản Bài giảng (Revision Lifecycle Resource Inheritance)**: Khi một bài giảng được chỉnh sửa tạo bản nháp `PENDING_APPROVAL`, hoặc khi Quản trị viên phê duyệt yêu cầu thay đổi bài giảng và đôn phiên bản (`revision_no += 1`, bài cũ chuyển `HISTORICAL`, bản nháp chuyển `PUBLISHED`), toàn bộ các tệp tài nguyên đính kèm (`LessonResource`: video, tài liệu bài giảng) từ phiên bản tiền nhiệm được kế thừa và sao chép tự động sang phiên bản mới.
2. **Khắc phục Triệt để Lỗi Bất đồng bộ & Race Condition trong Duyệt Đổi Tài nguyên (Admin Approval Race Condition Hardening)**: Khi Giảng viên gửi yêu cầu sửa nội dung và tải video lên gần như đồng thời, nếu yêu cầu sửa nội dung được Admin duyệt trước (khiến bài học gốc chuyển sang `HISTORICAL`), yêu cầu gắn video `RESOURCE_CHANGES` sau đó tự động phát hiện và gắn video vào phiên bản `PUBLISHED`/`ACTIVE` mới nhất của bài học, thay vì gắn vào bài học lịch sử đã chết.
3. **Lọc Sạch Bài học Lưu trữ Lịch sử Khỏi Giáo án Giảng viên (Clean Curriculum Filtering)**: Các phương thức tuần tự hóa chương mục giáo trình (`_serialize_learning_unit`, `_serialize_course`, `get_course_lessons`) tự động loại bỏ các bài học `HISTORICAL` đã bị thay thế, triệt tiêu hoàn toàn hiện tượng hiển thị trùng lặp nhiều bài số 1 trong danh mục và ngăn giảng viên vô tình vào nhầm bản lưu trữ cũ.
4. **Cảnh báo Thông minh & Chuyển đổi 1-Click trong Lesson Authoring Studio**: Khi Giảng viên truy cập trực tiếp vào một bài học lịch sử, hệ thống hiển thị banner cảnh báo trực quan kèm nút bấm 1-click chuyển ngay sang phiên bản hiện hành.
5. **Cơ chế Dự phòng Đa tầng Phía Phục vụ Học viên (Backend & Frontend Multi-Tier Fallbacks)**:
   - *Backend*: Tự động đối soát và kế thừa tài nguyên từ phiên bản tiền nhiệm gần nhất (`previous_lesson`) nếu bản ghi phiên bản mới bị khuyết tài nguyên do dữ liệu cũ.
   - *Frontend*: Hàm dựng `StudentView.renderCourseConsole` kiểm tra đa tầng `lesson.video_url || lesson.video_urls?.[0] || lesson.resources?.find(r => r.file_asset?.is_video || r.resource_type === 'VIDEO')`, đảm bảo không bao giờ bị mất trình phát video nếu có ít nhất 1 nguồn video hợp lệ.
6. **Đồng bộ & Khắc phục Dữ liệu CSDL Trực tiếp (Live Database Reconciliation)**: Tạo và thực thi script `scripts/reconcile_lesson_resources.py` liên kết lại video `2026-08-25 09-05-13.mp4` và tài liệu PDF với bài học hiện hành `90018` trên hệ CSDL MSSQL của hệ thống.

---

## 2. Chi tiết Thay đổi Kỹ thuật

### 2.1. Backend Architecture & Services
1. `src/pwd301/services/lesson_service.py`:
   - Hiện thực hóa hàm trợ năng `_copy_lesson_resources(source_lesson_id, target_lesson_id, session=sess)`.
   - Cập nhật `create_lesson_change_request()`: Tự động sao chép các tài nguyên hiện hữu của bài giảng gốc sang bài giảng nháp đang chờ duyệt.
   - Cập nhật `approve_course_change_request()`: Kế thừa và sao chép toàn bộ tài nguyên từ bài giảng tiền nhiệm (`previous_lesson`) sang bài giảng xuất bản mới.
   - Cập nhật `get_course_lessons()`: Lọc bỏ các bài học `HISTORICAL` khi truy vấn danh sách bài giảng hoạt động.
2. `src/pwd301/blueprints/admin/routes.py`:
   - Nâng cấp `admin_review_change_request()`: Đối với `RESOURCE_CHANGES`, nếu bài học mục tiêu đã chuyển sang `HISTORICAL`, tự động truy vết bản ghi `PUBLISHED`/`ACTIVE` mới nhất trong cùng vị trí/chương mục để gắn hoặc gỡ tài nguyên, loại bỏ triệt để lỗi race condition.
3. `src/pwd301/blueprints/instructor/routes.py`:
   - Nâng cấp `_serialize_learning_unit()` và `_serialize_course()`: Chỉ tuần tự hóa các bài học có trạng thái hoạt động hợp lệ (`PUBLISHED`, `ACTIVE`, `DRAFT`, `PENDING_APPROVAL`), loại trừ `HISTORICAL` và `TRASH`.
   - Cập nhật `get_lesson_route()`: Bổ sung cờ `is_historical` và trường `latest_lesson_id` khi giảng viên xem một bài học lịch sử.
4. `src/pwd301/blueprints/student/routes.py`:
   - Nâng cấp `_serialize_student_lesson()`: Kích hoạt fallback tự động kế thừa `video_url`, `video_urls` và `resources` từ `les.previous_lesson` nếu bài học hiện hành bị thiếu tài nguyên do lỗi lịch sử.

### 2.2. Frontend UI/UX & Player Continuity
1. `frontend/assets/js/views/student.js`:
   - Cải tiến `renderCourseConsole()`: Nhận diện video đa tầng (`video_url`, `video_urls`, `resources.filter(is_video)`), tự động gán `lesson.video_url` bằng nguồn video hợp lệ đầu tiên và kích hoạt bộ điều khiển Anti-Seek player tùy chỉnh.
2. `frontend/assets/js/views/instructor.js`:
   - Nâng cấp `renderLessonAuthoringStudio()`: Tích hợp banner cảnh báo màu vàng đồng cam với icon `history_toggle_off` khi `lesson.is_historical` là true, kèm nút chuyển sang phiên bản hiện hành `latest_lesson_id`.

### 2.3. Dữ liệu Cơ sở Dữ liệu & Script Đồng bộ
1. `scripts/reconcile_lesson_resources.py`:
   - Quét toàn bộ bài học `PUBLISHED`/`ACTIVE` trong hệ CSDL MSSQL Docker, đối soát chuỗi phiên bản tiền nhiệm (`previous_lesson_id`) và tự động gắn bù các tài nguyên bị thất lạc.
   - Kết quả: Đã khôi phục thành công 2 tài nguyên (video `2026-08-25 09-05-13.mp4` và PDF) cho Bài học `90018` (`8c3f2364-5793-40ca-be24-5c1b30138027`).

---

## 3. Xác minh Thực nghiệm (Empirical Verification)

### 3.1. Kiểm thử Tự động (Unit & Integration Tests)
1. Tạo bộ kiểm thử TDD mới: `tests/api/test_lesson_video_delivery_remediation.py`:
   - `test_approved_lesson_revision_inherits_resources`: Kiểm tra bản nháp và bản duyệt kế thừa tài nguyên đầy đủ từ bản cũ.
   - `test_resource_change_request_attaches_to_active_published_lesson_when_target_historical`: Kiểm tra xử lý race condition Admin duyệt yêu cầu thay đổi tài nguyên sau khi bài học đã đôn phiên bản.
   - `test_instructor_curriculum_serialization_filters_historical_lessons`: Kiểm tra lọc bài học `HISTORICAL` khỏi giáo án giảng viên.
   - **Kết quả: 3/3 tests PASSED (100%)**.
2. Kiểm tra hồi quy toàn diện liên quan (32 tests):
   - `tests/test_lesson_revision_lifecycle.py` (4 tests) — PASSED.
   - `tests/api/test_lesson_change_request_flow.py` (8 tests) — PASSED.
   - `tests/test_m4_lecture_media.py` (14 tests) — PASSED.
   - `tests/api/test_course_metadata_and_lesson_approval_remediation.py` (6 tests) — PASSED.
   - **Kết quả tổng hợp: 32/32 tests PASSED (100%)**.

### 3.2. Kiểm thử Thực tế trên Trình duyệt với `chrome-devtools-mcp`
1. **Phía Học viên (Student View)**:
   - Điều hướng tới `http://127.0.0.1:5000/#/student/courses/detail?id=5da5cfbc-28a5-4db8-a478-f634676f2c67`.
   - Kết quả snapshot: Trình phát video tùy chỉnh hiển thị đầy đủ, thanh Anti-Seek hiển thị `Khóa tua nhanh đang bật: Cần xem tuần tự bài giảng để ghi nhận tiến độ`.
   - Đánh giá JS: `readyState: 4`, `duration: 150.95`, `videoWidth: 1724`, `videoHeight: 1080`.
   - Kiểm tra phát video: Video stream mượt mà, `currentTime` tăng từ `0.00` lên `2.86s` rồi `7.13s`.
   - Chụp ảnh màn hình lưu trữ: `media_0.png` hiển thị khung hình thật của video `2026-08-25 09-05-13.mp4`.
2. **Phía Giảng viên (Instructor View)**:
   - Điều hướng tới `http://127.0.0.1:5000/#/instructor/courses/5da5cfbc-28a5-4db8-a478-f634676f2c67/manage`.
   - Kết quả: Chỉ có duy nhất 1 bài học số 1 trong danh mục (không còn trùng lặp bài cũ), hiển thị đúng chỉ số `1/7 video`.
   - Lesson Authoring Studio cho bài hiện hành `8c3f2364-5793-40ca-be24-5c1b30138027`: Hiển thị đầy đủ video và tài liệu PDF đính kèm.
   - Lesson Authoring Studio cho bài cũ `23ae2252-a5f9-4290-8be9-12e3ef9d4dfc`: Hiển thị chính xác banner cảnh báo phiên bản lưu trữ lịch sử kèm nút bấm chuyển sang bản hiện hành.
