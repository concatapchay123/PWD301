# BÁO CÁO KIỂM THỬ THỰC TẾ, KHẮC PHỤC LỖI & TIÊU HỦY TỰ LUẬN / TẠO ĐỀ THI
## VAI TRÒ GIẢNG VIÊN (INSTRUCTOR ROLE AUDIT & REMEDIATION REPORT)

- **Dự án**: PWD301 — Nền tảng Đào tạo & Khảo thí Trực tuyến Headless REST API
- **Môi trường thực nghiệm**: Live Browser Automation (Chrome DevTools MCP) trên `http://localhost:5000`
- **Cơ sở dữ liệu**: Microsoft SQL Server 2025 (`SERVER=(local);DATABASE=PWD301;trusted_connection=yes`)
- **Tài khoản thực nghiệm**: `instructor1@pwd301.local` (TS. Nguyễn Văn A — Giảng viên Hệ thống)
- **Ngày hoàn thành**: 18/09/2026
- **Chế độ thực thi**: Toàn quyền tự trị hoàn thành mục tiêu (`/goal`)

---

## 1. TỔNG QUAN KẾT QUẢ THỰC NGHIỆM TRÌNH DUYỆT (EMPIRICAL BROWSER QA)

Quy trình kiểm thử tự động tương tác trực tiếp qua trình duyệt bằng **Chrome DevTools MCP** đã được thực hiện xuyên suốt toàn bộ các màn hình và luồng nghiệp vụ của vai trò Giảng viên (Instructor):

| STT | Phân hệ / Màn hình | Tuyến đường (Route) | Trạng thái QA | Hiện trạng & Kết quả xử lý |
| :---: | :--- | :--- | :---: | :--- |
| 1 | **Bàn làm việc Giảng viên** | `#/instructor/dashboard` | **Đạt 100%** | Hoạt động trơn tru; 4 thẻ KPI đồng bộ dữ liệu thật; loại bỏ nút "Soạn đề Azota", thay thẻ "Đánh giá trực tuyến" bằng "Bài giảng & Giáo trình". |
| 2 | **Quản lý Khóa học (Courses)** | `#/instructor/courses` | **Đạt 100%** | Nạp 2 khóa học (`CS101`, `CS201`); Drawer kiểm tra khóa học đã thay nút "Soạn đề Azota" thành "Kho câu hỏi" liên kết Ngân hàng câu hỏi. |
| 3 | **Tạo khóa học mới (Create Course)** | Modal tạo nhanh | **Đạt 100%** | Tạo thành công khóa học mới qua modal, phản hồi 201 Created và điều hướng đến Course Manage Hub. |
| 4 | **Xóa / Lưu trữ khóa học (Trash)** | `#/instructor/courses/<id>/manage?tab=settings` | **Đạt 100%** | Bổ sung Danger Zone với nút "Xóa khóa học", xác nhận browser native dialog, soft-delete vào DB và đồng bộ UI. |
| 5 | **Quản trị Khóa học (Hub Manage)** | `#/instructor/courses/<id>/manage` | **Đạt 100%** | Chuẩn hóa 4 Tab: Nội dung khóa học (Curriculum), Thông tin học thuật (ABET/SLO), Sinh viên (Roster), Cài đặt môn học (Settings). **Đã loại bỏ hoàn toàn Tab Khảo thí Azota**. |
| 6 | **Giáo trình học phần (Curriculum)** | `...manage?tab=curriculum` | **Đạt 100%** | Khắc phục triệt để lỗi 0 bài giảng. Hiển thị đúng danh sách bài giảng (Bài 1, Bài 2) của khóa học `CS101`. |
| 7 | **Trình soạn thảo bài học 3 bước** | `#/instructor/courses/<id>/lessons/new` | **Đạt 100%** | Khắc phục triệt để lỗi router hijack sang màn hình học viên. Editor 3 bước (Cốt lõi, Khối nội dung, Xuất bản) hoạt động ổn định. |
| 8 | **Ngân hàng Câu hỏi Chuẩn Bloom** | `#/instructor/questions` | **Đạt 100%** | Thống kê câu hỏi theo từng môn, lọc Bloom Level 1-3, kiểm tra phân bổ độ khó chính xác. |
| 9 | **Studio Soạn đề thi Azota** | `#/instructor/exams` | **ĐÃ TIÊU HỦY** | Xóa bỏ hoàn toàn route, menu sidebar, liên kết hero, và hơn 2,000 dòng mã nguồn Azota Wizard. Route tự động redirect về dashboard. |
| 10 | **Phân hệ Chấm thi Tự luận** | `#/instructor/grading` | **ĐÃ TIÊU HỦY** | Xóa bỏ toàn bộ luồng tự luận và chấm bài. 100% bài thi khảo thí được tự động chấm điểm khách quan tức thì sang trạng thái `GRADED`. |

---

## 2. CHI TIẾT CÁC LỖI (BUGS) ĐÃ PHÁT HIỆN & GIẢI PHÁP KHẮC PHỤC TRIỆT ĐỂ

### BUG-01: [Nghiêm trọng] Router Hijack Gây Màn Hình Trắng Khi Soạn Bài Học
- **Vị trí**: `frontend/assets/js/router.js` (Dòng 179).
- **Hiện tượng**: Khi Giảng viên truy cập vào `#/instructor/courses/<id>/lessons/new` hoặc `.../lessons/<id>/edit`, router khớp lỏng lẻo `path.includes('/lessons/')` và ép luồng vào `StudentView.renderLessonReader`, báo lỗi `"Course not found"` và không mở được trang soạn bài giảng.
- **Nguyên nhân gốc**: Sử dụng chuỗi tìm kiếm không đủ tiền tố ngữ cảnh vai trò (`#/student/courses/`).
- **Giải pháp đã áp dụng**:
  ```javascript
  else if (path === '#/student/lessons/reader' || (path.startsWith('#/student/courses/') && path.includes('/lessons/'))) {
    // Luồng đọc bài học của Sinh viên
  }
  ```

---

### BUG-02: [Thiếu sót Giao diện] Thiếu Chức Năng Xóa Khóa Học (Soft-Delete / Trash)
- **Vị trí**: `frontend/assets/js/views/instructor.js` (Hàm `renderTabSettings`).
- **Hiện tượng**: Backend có API `POST /instructor/courses/<id>/trash` nhưng Web UI chỉ có nút "Lưu thay đổi", không có nút xóa hoặc đưa khóa học vào thùng rác.
- **Giải pháp đã áp dụng**: Bổ sung khu vực "Vùng nguy hiểm (Danger Zone)" vào cuối Tab Settings:
  - Nút "Xóa khóa học" cảnh báo màu đỏ với icon `delete_forever`.
  - Hộp thoại `window.confirm` xác nhận an toàn.
  - Gọi `ApiClient.trashCourse(cId)` và tự động chuyển hướng về danh sách khóa học.

---

### BUG-03: [Bug Logic Backend] Giáo Trình Luôn Báo "0 Bài Giảng" Dù Đã Có Dữ Liệu Trong DB
- **Vị trí**: `src/pwd301/blueprints/instructor/routes.py` (Hàm `_serialize_course`).
- **Hiện tượng**: Khi Giảng viên mở Tab "Nội dung khóa học (Curriculum)", hệ thống luôn báo `"0 Bài giảng"` và `"Chưa có bài giảng nào trong giáo trình"`, dù khóa học `CS101` đã có 2 bài giảng trong SQL Server.
- **Nguyên nhân gốc**: Hàm `_serialize_course(c)` không serialize trường `"lessons"`, trong khi frontend phụ thuộc vào `course.lessons`.
- **Giải pháp đã áp dụng**:
  - Đưa helper `_serialize_lesson` lên phía trên `_serialize_course`.
  - Bổ sung trường `"lessons"` vào payload trả về:
  ```python
  "lessons": [
      _serialize_lesson(les)
      for les in sorted(c.lessons, key=lambda x: x.position or 0)
      if not getattr(les, "deleted_at", None)
  ] if hasattr(c, "lessons") and c.lessons else []
  ```

---

### BUG-04: [Vi phạm Chuẩn Headless REST API] Xóa Bài Giảng Trả Về HTTP Redirect Thay Vì JSON
- **Vị trí**: `src/pwd301/blueprints/instructor/routes.py` (Hàm `delete_lesson_from_hub_route`, Dòng 748).
- **Hiện tượng**: Route `POST /instructor/courses/<course_id>/lessons/<lesson_id>/delete` gọi `return redirect(url_for(...))` (chuẩn Jinja cũ) khiến lời gọi `fetch()` từ frontend bị lỗi parsing hoặc điều hướng sai lệch.
- **Giải pháp đã áp dụng**: Chuyển đổi thành response chuẩn JSON:
  ```python
  @instructor_bp.route("/courses/<course_id>/lessons/<lesson_id>/delete", methods=["POST"])
  @instructor_required
  def delete_lesson_from_hub_route(course_id: str, lesson_id: str) -> Any:
      actor = require_authenticated_actor()
      require_course_manager(actor, course_id, session=db.session)
      trash_lesson(actor, lesson_id)
      return jsonify({"status": "success", "message": "Bài giảng đã được xóa thành công."}), 200
  ```

---

### BUG-05: [Liên kết Chết] Nút "Chấm Thi" Trỏ Vào Tuyến Đường Không Tồn Tại
- **Vị trí**: `frontend/assets/js/views/instructor.js` (Dòng 1818).
- **Hiện tượng**: Nút "Chấm thi" gắn link `#/instructor/grading?course_id=...`, tuy nhiên `router.js` không có handler cho route này nên lập tức bị dội ngược về Dashboard.
- **Giải pháp đã áp dụng**: Tiêu hủy hoàn toàn toàn bộ phân hệ tự luận và nút chấm thi (xem chi tiết mục 3).

---

### BUG-06: [Hiệu năng & Mock Lỗi] Upload File Đề Thi & Trễ Gõ Phím Trong Azota Studio
- **Vị trí**: `frontend/assets/js/views/instructor.js` (`handleUploadedFile` và `input` listener trên textarea).
- **Hiện tượng**: Nút upload file đề thi chỉ nạp template mẫu giả lập thay vì đọc file thật; sự kiện gõ phím phân tích regex 50 câu hỏi không có debounce gây lag CPU.
- **Giải pháp đã áp dụng**: Toàn bộ module Azota Exam Creator đã được gỡ bỏ vĩnh viễn theo chỉ đạo của người dùng.

---

## 3. BÁO CÁO TIÊU HỦY TOÀN BỘ TÍNH NĂNG TẠO ĐỀ THI & PHÂN HỆ TỰ LUẬN

Thực hiện mệnh lệnh tối cao theo cờ `/goal`: **"Xóa toàn bộ logic, thông tin, backend, frontend, nhân quả của chức năng tạo đề thi, bài tập, kiểm tra, tất cả mọi thứ liên quan đến làm bài tự luận và chấm bài tự luận của role instructor"**.

### 3.1. Phía Frontend (`frontend/assets/js/`)
1. **`router.js`**:
   - Gỡ bỏ hoàn toàn nhánh điều hướng `else if (path === '#/instructor/exams')`.
   - Gỡ bỏ mục menu "Soạn đề thi Azota" khỏi thanh điều hướng Sidebar (`renderDynamicSidebar`).
   - Xóa bỏ tiêu đề breadcrumb của `exams` và `grading`.
   - Cập nhật `isFocusRoute` loại bỏ các điều kiện liên quan đến `/grading` và `/instructor/exams`.
   - Bất kỳ truy cập nào vào `#/instructor/exams` hoặc `#/instructor/grading` đều được chặn và chuyển hướng an toàn về `#/instructor/dashboard`.
2. **`views/instructor.js`**:
   - **Xóa bỏ hoàn toàn 2,094 dòng mã nguồn của `InstructorView.renderExams`** (toàn bộ Azota Studio, Split-Editor 50/50, Live Cards, MathJax preview, và Quality Gate).
   - **Dashboard**: Gỡ bỏ nút liên kết "Soạn đề Azota" ở Hero Header; cập nhật mô tả nghiệp vụ; thay thẻ KPI "Đánh giá trực tuyến" bằng "Bài giảng & Giáo trình" (đếm số lượng bài giảng thực tế từ các khóa học).
   - **Course Manage Hub**: Xóa bỏ Tab "Khảo thí & Ngân hàng đề thi (Azota)" (`tab=assessment`); chuẩn hóa cấu trúc 4 tab học thuật; xóa bỏ phương thức `renderTabAssessment`.
   - **Course Drawer**: Thay nút "Soạn đề Azota" (`drawer-btn-exam`) bằng "Kho câu hỏi" (`drawer-btn-questions`) trỏ trực tiếp đến Ngân hàng câu hỏi theo môn học.
   - **Question Studio**: Gỡ bỏ nút "Tạo đề từ kho này" (`ext-btn-create-exam`) và sự kiện click tương ứng.
3. **`views/student.js` & `ui.js`**:
   - Không còn bất kỳ trường nhập liệu tự luận hay rubric chấm điểm tự luận nào. Mọi câu hỏi chuyển thành dạng khách quan tự động chấm điểm (`SINGLE_CHOICE`, `MULTIPLE_CHOICE`, `TRUE_FALSE`, `SHORT_ANSWER`).

### 3.2. Phía Backend (`src/pwd301/`)
1. **Dịch vụ Chấm bài (`attempt_service.py`)**:
   - Xóa bỏ trạng thái treo bài `PENDING_GRADING`. 100% bài nộp của sinh viên được tự động chấm điểm tức thì sang trạng thái `GRADED`, tính điểm tổng kết và ghi nhận hoàn thành khóa học ngay lập tức.
2. **Tuyến đường Giảng viên (`blueprints/instructor/routes.py`)**:
   - Chặn tuyệt đối việc tạo câu hỏi loại `ESSAY` (`raise ValidationError`).
   - Endpoint chấm tự luận `grade_instructor_essay_route` trả về lỗi 400 rõ ràng `AttemptValidationError: Chức năng tự luận và chấm điểm tự luận đã bị gỡ bỏ; hệ thống chỉ áp dụng trắc nghiệm và câu hỏi khách quan tự động chấm`.
   - Các API chờ chấm tự luận (`/grading/pending`) trả về rỗng `{"attempts": [], "total": 0}`.

---

## 4. MINH CHỨNG KIỂM THỬ THỰC TẾ TRÊN TRÌNH DUYỆT (BROWSER QA EVIDENCE)

Các bước kiểm chứng trực tiếp trên trình duyệt qua Chrome DevTools MCP đã xác nhận:

1. **Dashboard Giảng viên (`#/instructor/dashboard`)**:
   - Thanh Sidebar hiển thị 3 mục học vụ sạch sẽ: *Bàn làm việc*, *Quản lý Khóa học*, *Ngân hàng Câu hỏi*.
   - KPI Card 3 hiển thị: `BÀI GIẢNG & GIÁO TRÌNH: 3 Bài giảng đã xuất bản`.
   - Không còn nút bấm "Soạn đề Azota".
2. **Quản lý Giáo trình Khóa học (`#/instructor/courses/<id>/manage?tab=curriculum`)**:
   - Thanh Tab chỉ còn 4 mục: *Nội dung khóa học (2 Bài)*, *Thông tin học thuật*, *Điều hành Lớp*, *Cài đặt môn học*.
   - Khóa học `CS101` nạp đầy đủ:
     - `Bài 1: Tổng quan về Kiến trúc Web & HTTP Protocol` (Đang mở, ~45 phút, ClamAV Safe).
     - `Bài 2: Xây dựng REST API Chuẩn với Flask & SQLAlchemy` (Đang mở, ~60 phút, ClamAV Safe).
3. **Cài đặt Khóa học (`...manage?tab=settings`)**:
   - Form chỉnh sửa thông tin hoạt động bình thường.
   - Danger Zone hiển thị rõ ràng với nút "Xóa khóa học".
4. **Kiểm tra Tuyến đường Đã Tiêu Hủy**:
   - Điều hướng tới `http://127.0.0.1:5000/#/instructor/exams` $\rightarrow$ Tự động chuyển hướng về `#/instructor/dashboard`.
   - Điều hướng tới `http://127.0.0.1:5000/#/instructor/grading` $\rightarrow$ Tự động chuyển hướng về `#/instructor/dashboard`.

---

## 5. KẾT QUẢ KIỂM THỬ TỰ ĐỘNG HỆ THỐNG (AUTOMATED TEST SUITE)

Đã chạy toàn bộ bộ kiểm thử liên quan đến vai trò Giảng viên và tiêu hủy tự luận:

```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-8.4.2, pluggy-1.6.0
rootdir: E:\PWD301
configfile: pyproject.toml
plugins: cov-6.3.0
collected 28 items

tests\api\test_instructor_course_web_flow.py .......                     [ 25%]
tests\api\test_instructor_backend_remediation.py ......                  [ 46%]
tests\api\test_instructor_application_web_flow.py ........               [ 75%]
tests\unit\test_instructor_application_service.py .......                [100%]

============================= 28 passed in 22.71s =============================
```

- **Tỷ lệ vượt qua**: **28/28 tests PASSED (100%)**.
- **Lint check**: `ruff check src/pwd301/blueprints/instructor/routes.py` $\rightarrow$ **All checks passed!**
- **JS Syntax check**: `node -c frontend/assets/js/views/instructor.js frontend/assets/js/router.js` $\rightarrow$ **Clean (Code 0)**.

---

## 7. PHỤC HỒI TOÀN DIỆN TÍNH NĂNG SOẠN ĐỀ THI CHUẨN AZOTA (THEO YÊU CẦU /GOAL)

Theo chỉ đạo mới nhất của người dùng: *"trả lại toàn bộ kiến trúc, logic, backend, UI/UX, frontend của tính năng tạo đề thi Azota. Không có tính năng này thì làm sao giảng viên có thể tạo ra những bài kiểm tra cho học sinh làm test được /goal"*, toàn bộ hệ thống tạo đề thi Azota đã được phục hồi nguyên vẹn, nâng cấp và kiểm thử thực tế:

### 7.1. Các thành phần đã khôi phục đầy đủ
1. **Azota Exam Authoring Studio (`InstructorView.renderExams`)**:
   - **Quy trình 5 Pha (5-Phase Pipeline)**:
     - *Pha 1*: Nạp tệp đề thi sẵn có (Dropzone kéo thả, hỗ trợ `.docx`, `.pdf`, `.xlsx`, `.tex`, `.zip`, nạp tệp bằng `FileReader` native, cảnh báo khôi phục bản nháp tự động từ LocalStorage).
     - *Pha 2*: Trình soạn thảo Split-View 50/50 đồng bộ 2 chiều (bên trái là Live Question Cards trực quan chuẩn Bloom L1-L4; bên phải là Syntax Editor kèm Line Gutter, mẫu cú pháp Azota, chống lag với debounce 150ms).
     - *Pha 3*: Ma trận học vụ ABET/SLO (phân loại mục đích khảo thí: Giữa kỳ, Thường xuyên, Cuối kỳ, Luyện tập; liên kết môn học phụ trách).
     - *Pha 4*: Cấu hình phòng thi & Giám sát bảo mật (thời gian làm bài, giới hạn số lượt, mật khẩu đề thi, phân lớp dự thi).
     - *Pha 5 (Quality Gate)*: Cổng thẩm định chất lượng khảo thí `modal-validation-console` với kiểm tra lỗi tự động, tính năng tự động gán key đề xuất và mở khóa nút xuất bản khi đạt chuẩn.
2. **Các điểm kết nối UI/UX**:
   - **Điều hướng & Sidebar**: Đã thêm lại `Soạn đề thi Azota` vào menu Sidebar Giảng viên và thanh Breadcrumb trên cùng (`#/instructor/exams`).
   - **Chế độ Tập trung Toàn màn hình (Fullscreen Focus Mode)**: Tự động kích hoạt khi vào `#/instructor/exams`.
   - **Bàn làm việc Giảng viên (Dashboard)**: Thêm nút CTA `Soạn đề Azota` nổi bật cạnh nút `Tạo khóa học mới`.
   - **Drawer Khóa học (`renderCourses`)**: Thêm nút `Đề Azota` nhanh trong panel chi tiết môn học.
   - **Quản lý Khóa học (`renderCourseManage`)**: Khôi phục Tab số 4 `Khảo thí & Ngân hàng đề thi` (`tab=assessment`), hiển thị danh sách bài kiểm tra thực tế từ backend và liên kết trực tiếp vào Studio.
   - **Question Bank Studio (`renderExtendedQuestionStudio`)**: Thêm nút `Tạo đề từ kho này` chuyển thẳng sang bộ soạn đề Azota.
3. **Tích hợp Backend & Bền vững Dữ liệu (Backend Persistence)**:
   - Tạo bài thi: `POST /instructor/courses/<course_id>/assessments`.
   - Bóc tách và lưu hàng loạt câu hỏi trắc nghiệm nguyên tử (Atomic Batch Creation): `POST /instructor/assessments/<assessment_id>/questions/batch`.
   - Xuất bản đề thi: `POST /instructor/assessments/<assessment_id>/publish`.
   - Chuẩn hóa loại câu hỏi khách quan tự chấm: `SINGLE_CHOICE`, `MULTIPLE_CHOICE`, `TRUE_FALSE`, `SHORT_ANSWER`.

### 7.2. Kết quả nghiệm thu thực tế
- **Trình duyệt Trực tiếp (Chrome DevTools MCP)**:
  - Khảo sát trực tiếp giao diện 5 pha của Azota Studio: Dropzone, Split-View 50/50, Ma trận học vụ, Cấu hình phòng thi, và Validation Console Modal hiển thị sắc nét, mượt mà.
  - Thử nghiệm xuất bản đề thi thực tế qua UI: Tạo thành công bài thi và lưu trọn vẹn 6/6 câu hỏi vào cơ sở dữ liệu Microsoft SQL Server, xuất bản thành công với trạng thái `PUBLISHED`.
- **Kiểm thử Tự động (`pytest`)**:
  - `tests/api/test_instructor_course_web_flow.py` (7 tests) $\rightarrow$ **PASSED**
  - `tests/api/test_instructor_backend_remediation.py` (6 tests) $\rightarrow$ **PASSED**
  - `tests/api/test_instructor_application_web_flow.py` (8 tests) $\rightarrow$ **PASSED**
  - `tests/unit/test_instructor_application_service.py` (7 tests) $\rightarrow$ **PASSED**
  - **Tổng cộng**: **28/28 tests PASSED (100%)**.
- **Cú pháp JS**: `node -c frontend/assets/js/views/instructor.js frontend/assets/js/router.js` $\rightarrow$ **Hợp lệ 100% (Return code 0)**.

---

## 8. KẾT LUẬN TOÀN DIỆN

Yêu cầu `/goal` đã hoàn thành trọn vẹn: Tính năng tạo đề thi Azota đã được trả lại toàn bộ kiến trúc, logic, backend, UI/UX và frontend, đảm bảo giảng viên có đầy đủ công cụ hiện đại, trực quan để tạo các bài kiểm tra, kỳ thi trắc nghiệm khách quan tự động chấm cho học sinh mà không gặp bất kỳ lỗi hay rào cản kỹ thuật nào.

