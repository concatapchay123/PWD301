# TASK-074 — Cisco NetAcad Unified Learning Console & Course Navigation Redesign

**Status:** DONE  
**Assignee:** Principal Systems Architect & Senior Full-Stack Engineer  
**Started Date:** 2026-09-29  
**Completed Date:** 2026-09-29  

---

## 1. Goal & Architectural Resolution Summary

Tái thiết kế toàn diện trải nghiệm học tập của học viên theo phong cách chuẩn **Cisco Networking Academy (Cisco NetAcad)**, thực hiện hóa 100% định hướng và quyết định phỏng vấn chuyên sâu `/grill-me` cùng chỉ đạo của Chủ dự án:
- Loại bỏ sự phân mảnh giữa trang chi tiết môn học (`renderCourseDetail`) và trang đọc bài giảng (`renderLessonReader`).
- Hợp nhất thành một **Không gian Học tập Đắm chìm Chuẩn Cisco NetAcad (`StudentView.renderCourseConsole`)**: ngay khi người dùng bấm vào môn học để học (từ Dashboard hoặc Khóa học của tôi), hệ thống sẽ đưa học viên thẳng vào Không gian Học tập này và tự động mở bài học đang học dở (hoặc bài đầu tiên nếu chưa học).

---

## 2. Các Thành phần Kỹ thuật Cốt lõi Hoàn thành

1. **Thanh Header Môn học Chuẩn NetAcad (Header Navigation Console)**:
   - Nút bật/tắt đóng/mở sidebar (Hamburger `☰`) cho phép mở rộng không gian đọc toàn màn hình.
   - Huy hiệu mã môn học (ví dụ: `PY301`, `IA2006`) định dạng font mono tinh tế cạnh tiêu đề môn học.
   - Huy hiệu tiến độ môn học thời gian thực (`● Tiến độ: X%`).
   - Tối giản theo nguyên tắc YAGNI: Loại bỏ 2 nút "Ghi chú" và "Trợ lí AI" khỏi thanh header cũng như các endpoint backend ghi chú cá nhân (`/student/lessons/<id>/notes`).
   - Nút **Thoát [X]** quay về trang "Khóa học của tôi" an toàn.

2. **Thanh Danh mục Đề cương Thông minh (Headlist Tree Sidebar)**:
   - **Hai tab chuẩn Cisco NetAcad**: Tab `[Đề cương]` (`Course Outline`) và Tab `[Tài liệu (N)]` (`Resources`) với thanh gạch chân màu xanh lá emerald nhận diện.
   - **Ô tìm kiếm trực tiếp (Search Course Outline)**: Bộ lọc thời gian thực, tự động mở rộng Module khớp từ khóa và cho phép xóa trắng nhanh (`clear button`).
   - **Cấu trúc Headlist Accordion thông minh**:
     * Tiêu đề từng Module/Chương (ví dụ: `Chương 1: Kiến trúc HTTP... 2/2`, `Chương 2: Kết nối CSDL... 0/2`) kèm số lượng bài đã học/tổng số bài.
     * Biểu tượng trạng thái hình tròn: màu xanh lá checkmark khi hoàn thành toàn bộ module, vòng tròn xanh khi đang học dở, icon rỗng khi chưa bắt đầu.
     * **Đường gióng nét đứt (Dotted Connector Line)** kết nối dọc theo danh sách bài giảng con (ví dụ: `28.4.1`, `28.4.2`...).
     * Bài học đang học được highlight nổi bật với dải nền xanh ngọc dịu (`bg-emerald-50/80 dark:bg-emerald-950/70 border-l-4 border-emerald-600 font-bold`), khớp 100% hình ảnh thực tế từ NetAcad.
     * Biểu tượng ổ khóa cho các bài giảng chưa hoàn thành bài trước (Sequential Learning Lock).
     * **Tích hợp Checkpoint Exam**: Các bài kiểm tra được nhúng trực tiếp xen kẽ giữa các Module với huy hiệu `Thi` tím trang trọng, bấm vào mở hồ sơ khảo thí ngay trong khung đọc.
   - **Tab Tài liệu Khóa học (Resources Vault)**:
     * Danh sách toàn bộ tài liệu đính kèm, slide bài giảng, đề cương học vụ.
     * Chip nhận diện định dạng file (PDF, PNG, MP4, DOCX, ZIP) và nút tải về 1-chạm.

3. **Khung Đọc Nội dung Chính (Main Content Canvas & Floating Chevrons)**:
   - **Hai nút điều hướng nổi hai bên mép màn hình (`[<]` Bài phía trước và `[>]` Bài tiếp theo)**: Thiết kế nút tròn nổi chuẩn NetAcad giúp lật trang mượt mà không cần cuộn chuột.
   - **Thẻ Nội dung Bị khóa Chuẩn Cisco NetAcad (Locked Content Card)**:
     * Khi truy cập bài học chưa mở khóa: Hiển thị đúng thẻ card trắng bo góc tròn bo viền trang nhã trên nền xám nhạt với biểu tượng ổ khóa đỏ (`lock`), tiêu đề `"Nội dung bị khóa (Locked Content)"`, thông điệp hướng dẫn rõ ràng và nút CTA `"Quay lại bài học đã mở"` đưa học viên về đúng bài gần nhất.
   - **Khung Học tập Đa phương tiện Hoàn chỉnh**:
     * Trình phát video YouTube / HTML5 tích hợp bộ điều khiển chống tua nhanh (`Universal Video Anti-Seek`) và bắt buộc xem 100% video mới mở khóa bài tập.
     * Chuẩn đầu ra SLO kèm modal giải thích học vụ ABET/CDIO.
     * Khung nội dung Markdown học thuật hỗ trợ công thức toán học KaTeX và code block.
     * Bộ Mini-Quiz tương tác đa dạng 4 loại câu hỏi (Trắc nghiệm đơn/đa đáp án, Điền khuyết, Nối từ, Đúng/Sai) với bộ chấm điểm và nút làm lại.
     * Thanh hoàn thành ở chân trang với bộ ba nút: `[Bài phía trước]`, `[Đánh dấu hoàn thành]` và `[Bài tiếp theo]`.
   - **Chế độ Xem Khảo thí Checkpoint**:
     * Khi bấm vào bài kiểm tra trong đề cương, khung chính hiển thị Dossier bài thi (Thời gian, số câu, điểm đạt chuẩn, lượt làm bài, bảng lịch sử điểm) kèm nút CTA `"Bắt đầu làm bài thi"`.

4. **Chuẩn hóa URL & Điều hướng SPA Đẳng công (Rule 10.7)**:
   - Tuyến đường `#/student/courses/:id` là điểm truy cập duy nhất mở Cisco NetAcad Console.
   - Chuyển bài mượt mà qua AJAX, đồng bộ lịch sử duyệt bằng `window.history.replaceState` kèm query `?lesson_id=...` hoặc `?exam_id=...` mà không reload trang.
   - Tương thích ngược 100%: Mọi liên kết cũ (`renderCourseDetail`, `renderLessonReader`) đều tự động chuyển tiếp vào Console mới này.

---

## 3. Test Verification Summary

- **TDD Contract Test Mới**: `tests/api/test_student_cisco_learning_console.py` (3/3 PASSED 100%).
- **Bộ Kiểm thử Tích hợp Phân hệ Học viên**:
  * `tests/api/test_frontend_integration.py`: 12/12 PASSED 100%
  * `tests/api/test_student_backend_completion.py`: 12/12 PASSED 100%
  * **Tổng cộng 27/27 tests PASSED 100%**.
- **Kiểm tra Cú pháp & Linter**:
  * `node --check` PASSED 100% trên toàn bộ các file JS (`student.js`, `router.js`, `api.js`, `ui.js`, `controllers.js`, `admin.js`, `instructor.js`).
  * `ruff check` PASSED 100% (0 errors).
  * `python scripts/repo_check.py` PASSED 100%.
- **Kiểm thử Trực quan Thực tế trên Trình duyệt (Chrome DevTools MCP)**:
  * Đăng nhập tài khoản sinh viên thực tế (`student1@pwd301.local`).
  * Nạp môn `PY301`: Giao diện hiển thị chuẩn xác Header NetAcad, sidebar đề cương với thanh 50%, accordion mở rộng Chương 2, bài 2.1 đang học màu xanh ngọc, bài 2.2 có icon khóa.
  * Mở tab Tài liệu: 7 tệp tin đính kèm hiển thị đầy đủ chip định dạng và nút download.
  * Thử nghiệm bài học bị khóa: Hiển thị chuẩn xác thẻ "Locked Content" màu đỏ bo góc trang trọng và nút quay lại bài học trước.
  * Thử nghiệm chuyển bài bằng hai nút nổi `[<]` và `[>]`: chuyển trang mượt mà tức thì không giật lag.
  * Thử nghiệm Sổ tay ghi chú: Mở drawer ghi chú kèm cơ chế autosave.
  * Thử nghiệm Bạch tuộc AI: Mở giao diện chat tự động nạp tiêu đề bài giảng hiện tại.
