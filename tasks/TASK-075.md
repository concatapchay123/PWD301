# TASK-075 — Unified Course & Lesson Staging Approval Pipeline & Secure Anti-Seek Video Player Remediation

**Status:** DONE  
**Assignee:** Principal Systems Architect & Senior Full-Stack Engineer  
**Started Date:** 2026-09-29  
**Completed Date:** 2026-09-30  

---

## 1. Goal & Architectural Resolution Summary

Khắc phục triệt để và toàn diện toàn bộ các khiếm khuyết nghiêm trọng liên quan đến cơ chế xét duyệt khóa học của Admin, quy trình soạn thảo/sửa/xóa bài học của Giảng viên, và bảo mật trình phát video tự tải lên theo đúng kế hoạch `master_remediation_plan.md`:
1. **Bất biến Xét duyệt Thay đổi Toàn hệ thống (Universal Course & Lesson Staging Approval)**: Mọi thay đổi dù nhỏ nhất đối với khóa học đã xuất bản (`PUBLISHED`) hoặc lưu trữ (`ARCHIVED`) — bao gồm sửa metadata khóa học, sửa bài học, thêm bài học mới, xóa bài học, đổi thứ tự chương mục, gán/gỡ tiên quyết — đều bắt buộc phải đi qua hàng đợi xét duyệt `CourseChangeRequest` và chỉ có hiệu lực vào cơ sở dữ liệu thật sau khi Admin bấm phê duyệt.
2. **Loại bỏ Hoàn toàn Lỗi Va chạm Index CSDL Khi Thêm Bài Học Mới**: Xử lý triệt để lỗi va chạm index duy nhất `uq_lessons_course_position_active` (SQLite / SQL Server) bằng thuật toán dịch chuyển vị trí 2 pha (`+10000` rồi `-10000 + 1`), không làm mất hay xóa nhầm bài học của giảng viên.
3. **Admin Diff Modal Trực quan & Đầy đủ Dữ liệu Gốc**: Admin xem xét yêu cầu thay đổi nhìn thấy đầy đủ dữ liệu gốc (`original_data`) và dữ liệu đề xuất (`proposed_data`) đặt cạnh nhau (side-by-side) không bị `undefined` hay thiếu trường.
4. **Trình phát Video Bảo mật Tự tải lên Chống Tua (Secure HTML5 Custom Video Player & Anti-Seek)**: Loại bỏ thẻ `<video controls>` mặc định của trình duyệt; xây dựng custom control bar với cơ chế chặn tua tiến (`seekingBlocked`), cho phép tua lùi (`rewindAllowed`), kiểm soát tốc độ xem và tỉ lệ hoàn thành nghiêm ngặt ($\ge 90\%$ thời lượng thực tế và đạt giây cuối cùng), mở khóa tua tự do khi hoàn thành.
5. **Khắc phục Triệt để Lỗi Frontend**:
   - `discardLessonDraft`: Sửa lỗi dùng `change_request_id` thay vì `targetId`.
   - Phản hồi xóa/sắp xếp bài học: Hiển thị thông báo "Yêu cầu đã gửi tới Quản trị viên" khi nhận HTTP 202 `pending_approval`, không hiển thị thông báo giả "Xóa thành công".
   - Đảm bảo tính đẳng công khi ghé thăm trang `/new`, không tự ý bắn `POST` tạo bản ghi nháp rác.

---

## 2. Chi tiết Thay đổi Kỹ thuật

### 2.1. Backend Architecture & Services
1. `src/pwd301/services/course_service.py`:
   - Bổ sung `CourseChangeRequest` model import.
   - Thêm phương thức `queue_course_metadata_review(course, data, actor_id)`: Tự động gom cụm và cập nhật (upsert) yêu cầu sửa đổi đang chờ duyệt, chống spam bản ghi `CourseChangeRequest`.
   - Cập nhật `update_course(course_id, data, actor_id, ...)`: Bắt các khóa học ở trạng thái `PUBLISHED` hoặc `ARCHIVED`, chuyển hướng cập nhật vào hàng đợi phê duyệt và trả về `{"pending_approval": True, "change_request": ...}`.
2. `src/pwd301/services/lesson_service.py`:
   - Cập nhật `create_lesson_change_request()`: Chuẩn hóa `target_id` sang kiểu số nguyên ID bài học gốc (xử lý cả kiểu UUID/chuỗi/số), gán `req.target_id` bảo đảm truy vết chính xác bài học cần sửa/xóa. Tự động deduplicate các yêu cầu autosave liên tiếp đang ở trạng thái `PENDING`.
   - Nâng cấp `approve_course_change_request()`:
     * Dùng kỹ thuật dịch chuyển vị trí 2 pha (`two-phase position shift`) khi duyệt thêm bài học mới: dịch các bài học hiện tại sang dải tạm thời `pos + 10000`, sau đó chuyển về `pos + 1` để triệt tiêu hoàn toàn race condition và xung đột ràng buộc duy nhất `uq_lessons_course_position_active`.
     * Tạo bài học mới và kích hoạt revision đầu tiên trong một transaction an toàn.
   - Nâng cấp `discard_lesson_working_draft()`: Hỗ trợ tìm kiếm theo cả ID bản nháp hoặc ID bài học gốc (`target_id`), cập nhật trạng thái `CANCELLED` và lý do `Discarded by instructor`.
3. `src/pwd301/blueprints/instructor/routes.py`:
   - Chặn trực tiếp tại các routes: `update_course_route`, `learning_units_route`, `reorder_learning_units_route`, `add_course_prerequisite_route`, `remove_course_prerequisite_route`.
   - Đối với khóa học `PUBLISHED` hoặc `ARCHIVED`: Đưa mọi sửa đổi cấu trúc chương mục vào hàng đợi `CourseChangeRequest`, trả về HTTP 202 với `pending_approval: true`.
   - Cho phép khóa học `DRAFT` và `APPROVED` thao tác trực tiếp để giảng viên hoàn thiện đề cương trước khi xuất bản.
4. `src/pwd301/blueprints/admin/routes.py`:
   - `admin_list_change_requests`: Trích xuất và định hình `original_data` cho mọi loại yêu cầu (`COURSE_METADATA`, `LESSON`, `MODULE`, `PREREQUISITE`), trả về cả alias `items` và `change_requests` đảm bảo tương thích ngược 100%.
   - `admin_review_change_request`: Chuẩn hóa hành động duyệt (`approve`/`approved` $\rightarrow$ `approve`, `reject`/`rejected` $\rightarrow$ `reject`), hỗ trợ xử lý đầy đủ các action `COURSE_METADATA`, `CREATE_LEARNING_UNIT`, `REORDER_LEARNING_UNITS`, `REMOVE_PREREQUISITE`.
5. `src/pwd301/blueprints/api_courses/routes.py` & `src/pwd301/blueprints/api_lessons/routes.py`:
   - Đồng bộ hóa logic kiểm soát phê duyệt trên cả REST API JWT endpoints.

### 2.2. Frontend UI/UX & Player Protection
1. `frontend/assets/js/views/student.js`:
   - Xóa bỏ thẻ `<video controls>` mặc định.
   - Xây dựng giao diện trình phát tùy chỉnh: Thanh tiến trình scrubber có thanh đệm (`buffer bar`), huy hiệu chống tua (`Anti-Seek`), các nút phát/tạm dừng, âm lượng, thời gian thực và toàn màn hình.
   - Hiện thực hóa `StudentView.setupCustomVideoPlayer`:
     * Ngăn chặn hành vi nhảy cóc thời gian: Khi người dùng kéo tua vượt quá thời lượng đã xem tối đa (`maxWatched`), tự động trả con trỏ phát về `maxWatched` và hiển thị toast cảnh báo.
     * Cho phép tự do tua lùi lại để xem lại kiến thức (`rewindAllowed`).
     * Khi hoàn thành tối thiểu 90% thời lượng và đến giây cuối: Kích hoạt hoàn thành bài học và tự động mở khóa tua tự do (`unlockSeeking()`).
2. `frontend/assets/js/views/instructor.js`:
   - Sửa hàm `discardLessonDraft` sử dụng `lesson.id` làm `targetId`.
   - Cập nhật thông báo phản hồi khi xóa/sắp xếp bài học hoặc sửa metadata khóa học: Hiển thị toast thông tin phê duyệt khi nhận HTTP 202 `pending_approval`.

---

## 3. Verification & Evidence

1. **Automated Integration & Regression Tests**:
   - Đã chạy trọn vẹn test suite kiểm thử toàn diện:
     * `tests/api/test_course_metadata_and_lesson_approval_remediation.py`: 6/6 tests PASSED.
     * `tests/test_courses.py`: 19/19 tests PASSED.
     * `tests/test_lesson_revision_lifecycle.py`: 4/4 tests PASSED.
     * `tests/test_m2_course_customization.py`: 6/6 tests PASSED.
     * `tests/api/test_course_api.py`: 6/6 tests PASSED.
     * `tests/api/test_lesson_api.py`: 7/7 tests PASSED.
     * `tests/api/test_lesson_change_request_flow.py`: 8/8 tests PASSED.
     * `tests/unit/test_course_service.py`: 13/13 tests PASSED.
   - **Tổng cộng: 69/69 tests PASSED (100% Green)**.
2. **Kiểm thử Thực tế bằng `chrome-devtools-mcp` trên Trình duyệt Thật**:
   - Khởi động backend test server tại `http://127.0.0.1:5055/`.
   - Kết nối trình duyệt thật qua MCP:
     * **Kiểm thử Chống tua Video**: Phát tuần tự đến 5s, sau đó giả lập kéo tua lên 80s $\rightarrow$ Con trỏ bị chặn và ép về 5s (`seekingBlocked: true`, `timeupdateBlocked: true`). Kéo tua lùi về 2s $\rightarrow$ Chấp nhận (`rewindAllowed: true`). Kích hoạt mở khóa $\rightarrow$ Cho phép tua tới 99s (`unlockedSeekAllowed: true`).
     * **Kiểm thử Admin Diff Modal**: Gọi `AdminView.renderChangeRequestReviewDetail` trong DOM $\rightarrow$ Cột Dữ liệu Hiện tại và Dữ liệu Đề xuất hiển thị đầy đủ tiêu đề, mô tả không có lỗi `undefined` (`titleRenderedAccurate: true`, `descRenderedAccurate: true`).
     * **Kiểm thử Thao tác Giảng viên**: Xác nhận nút "Hủy bản nháp" truyền `targetId` chuẩn xác và nhận toast "Yêu cầu đã gửi tới Quản trị viên" khi thao tác trên khóa học đã xuất bản.
   - Chụp ảnh viewport minh chứng tại `media_0.png`.
