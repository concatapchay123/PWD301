# Thiết Kế Chi Tiết Task 1: Quản Trị Khóa Học & Trình Soạn Thảo Bài Giảng Trực Quan (Instructor Course Hub & Low-Tech Lesson Authoring Studio)

**Ngày lập:** 2026-09-17  
**Phân kỳ:** Task 1 / Chuỗi chuẩn hóa 29 màn hình Frontend PWD301  
**Phân hệ:** Cổng Giảng viên (Instructor Portal)  
**Trạng thái:** Chờ phê duyệt  

---

## 1. Bối cảnh & Mục tiêu

Người dùng yêu cầu nâng cấp toàn diện dự án PWD301 từ phiên bản cơ bản hiện tại lên phiên bản hoàn hảo, chuẩn hóa 100% theo bộ thiết kế 29 màn hình (`frontend/`) và tuân thủ các bất biến kiến trúc PWD301.

Theo kết quả phỏng vấn tương tác `/grill-me`, dự án được thống nhất triển khai theo lộ trình **Chia nhỏ theo từng Tính năng độc lập (Feature-by-Feature)**:
- **Task 1 (Hiện tại)**: Bộ công cụ Quản lý Khóa học & Soạn bài giảng Low-Tech trực quan (`Master Operations Table` -> `Course Detail Studio Bar` -> `Visual Lesson Authoring Studio`).
- **Task 2**: Chuỗi quy trình Khảo thí Azota toàn diện 5 màn hình (`Method Selector` -> `Split-View Editor 50/50` -> `Academic Governance Matrix` -> `Detailed Azota Config` -> `Validation Modal`).
- **Task 3**: Ngân hàng câu hỏi Bloom 6 cấp độ & Studio Chấm thi Tự luận Split-Canvas 50/50.
- **Các Task tiếp theo**: Cổng Quản trị viên Admin & Cổng Học viên Student.

---

## 2. Nguồn tham chiếu thiết kế chuẩn (Source of Truth)

1. `frontend/pwd301_instructor_courses_variant_2_master_operations_table_detailed_provenance/code.html`:
   - Bố cục Split Master-Detail: Bảng danh sách khóa học bên trái (7/12) + Ngăn kéo Thao tác Nhanh (Operations Drawer) bên phải (5/12).
   - 4 Metric Chips: Đang quản lý, Phân công đào tạo, Tự biên soạn, Tổng sinh viên.
   - Thanh lọc đa chiều: Tìm kiếm từ khóa, Lọc Nguồn gốc (Admin phân công vs Tự tạo), Lọc Trạng thái, Lọc Chương trình đào tạo.
2. `frontend/pwd301_extended_course_detail_variant_2_interactive_module_lesson_studio_bar/code.html`:
   - Khối Hero học vụ: Danh tính chủ nhiệm, Tín chỉ/Tiết chuẩn, Phân công lớp, Đánh giá môn, Tiến độ kỳ học (Tuần & Chuyên cần).
   - Enterprise 5-Tab Bar (Coursera/Udemy Hybrid):
     - Tab 1: Nội dung khóa học (`Curriculum Studio`) kèm thanh điều hành `Module & Lesson Studio Bar` (Thêm module, thêm bài, sắp xếp thứ tự, nhãn trạng thái và quét an toàn ClamAV).
     - Tab 2: Thông tin học thuật & Chuẩn đầu ra (`ABET SLO Dossier`).
     - Tab 3: Điều hành Lớp & Sinh viên (`Roster Management`).
     - Tab 4: Khảo thí & Ngân hàng đề thi (`Course Assessments`).
     - Tab 5: Đánh giá & Phản hồi (`Reviews & Feedback`).
   - Cột thông số bên phải (4/12): Sức khỏe lớp học, Giới hạn dung lượng lưu trữ, Tóm tắt bảo mật ClamAV.
3. `frontend/pwd301_lesson_authoring_tr_nh_so_n_th_o_b_i_gi_ng_tr_c_quan_th_n_thi_n_low_tech/code.html`:
   - Studio chuyên dụng toàn màn hình (`Fullscreen Focus Mode`) với Stepper 3 bước:
     - Bước 1: Đặt tên bài giảng & Chọn danh mục, Thời lượng dự kiến (45p, 90p, 180p).
     - Bước 2: Viết bài hoặc đính kèm tệp — Chuyển đổi linh hoạt giữa `Chế độ Cơ bản` (Khối trực quan WYSIWYG dạng Notion/Word) và `Chế độ Nâng cao` (Markdown/HTML cho chuyên gia IT).
     - Bước 3: Xem trước (`Student Live Preview`) & Bấm xuất bản.
   - Các khối nội dung trực quan (Block Canvas):
     - Khối Tiêu đề & Đoạn văn (Rich text formatting, H1/H2, Bold/Italic/Underline, Lists).
     - Khối Đa phương tiện (Chèn ảnh, Chèn video < 1GB).
     - Khối Hộp ghi chú nổi bật (`Callout Box` Tip/Warning/Important).
     - Khối Kiểm tra nhanh giữa bài (`Interactive In-Lesson Quiz Check`).
     - Khối Tài nguyên đính kèm có tem kiểm định an toàn ClamAV (`✓ Đã quét sạch ClamAV - An toàn`).
   - Ngăn kéo kiểm định sư phạm & Thao tác: Tự động lưu (`Autosave`) định kỳ vào MS SQL Server qua REST API, Kiểm tra tiêu chuẩn ABET SLO.

---

## 3. Kiến trúc & Giải pháp Kỹ thuật

### 3.1. Routing & State Navigation
- `#/instructor/courses`: Render bảng Split Master-Detail. Khi người dùng bấm vào một dòng môn học, cập nhật trạng thái `selectedCourseId` và đồng bộ nội dung Operations Drawer bên phải tức thì mà không cần tải lại trang.
- `#/instructor/courses/:id/manage`: Render trang Chi tiết Khóa học 5-Tab. Tham số query `?tab=curriculum|academic|students|assessment|reviews` điều khiển tab hoạt động.
- `#/instructor/courses/:id/lessons/new` & `#/instructor/courses/:id/lessons/:lessonId/edit`: Kích hoạt `Fullscreen Focus Mode` ẩn Sidebar, hiển thị Studio Soạn bài giảng 3 bước.

### 3.2. Data Binding & Tương thích Backend (SQL Server & Models)
- Tận dụng triệt để các bảng hiện có: `courses`, `lessons`, `course_change_requests`, `file_assets`, `enrollments`.
- Khối nội dung Block WYSIWYG được tuần tự hóa (serialized) thành định dạng Markdown tiêu chuẩn mở rộng hoặc JSON block cấu trúc lưu trong cột `lessons.markdown_content` (`NVARCHAR(MAX)`), đảm bảo tương thích 100% với `StudentView.renderLessonReader` mà không cần sửa đổi DDL CSDL.
- Tự động lưu bản nháp (`Autosave`) qua API `PUT /api/instructor/lessons/<lesson_id>` hoặc `PUT /instructor/lessons/<lesson_id>`.

---

## 4. Kế hoạch Kiểm thử & Xác minh
1. **Kiểm thử Tự động (Pytest)**:
   - Viết test suite kiểm thử API quản lý khóa học và bài giảng (tạo module, thêm bài, cập nhật block content, autosave).
   - Đảm bảo 100% test suite hiện tại không bị hồi quy (regression).
2. **Kiểm tra Chuẩn Code (Linting & Static Typing)**:
   - `ruff check src tests scripts` (0 errors).
   - `ruff format --check src tests scripts` (100% formatted).
   - `mypy src` (0 type errors).
   - `python scripts/repo_check.py` (PASS).
3. **Kiểm thử Thực tế trên Trình duyệt (Chrome DevTools E2E)**:
   - Đăng nhập Giảng viên (`instructor1@pwd301.local`).
   - Kiểm tra Bảng khóa học Split Master-Detail: Lọc môn, chọn dòng, xem Drawer điều hành 5/12.
   - Kiểm tra Chi tiết Khóa học 5 Tab: Chuyển đổi tab Curriculum, ABET SLO, Roster, Assessments mượt mà, không giật lag.
   - Mở Trình Soạn thảo Bài giảng Low-Tech: Chuyển đổi Cơ bản/Nâng cao, thêm khối đoạn văn, khối ghi chú, khối quiz, kiểm tra autosave và xem trước sinh viên.
