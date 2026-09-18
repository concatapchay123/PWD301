# BÁO CÁO KHẢO SÁT & BẢN THIẾT KẾ CHUYỂN ĐỔI GIAO DIỆN (HANDOFF REPORT)
## Objectives R3 & R4: Tích hợp Cổng Giảng viên, Cổng Quản trị & Xác thực
**Người thực hiện**: `teamwork_preview_explorer_survey5_3`  
**Đơn vị gửi báo cáo**: Teamwork Preview Survey Subagent  
**Người nhận**: `teamwork_preview_orchestrator_5` (Conversation ID: `4946890a-b666-4014-a18b-0a588b75fb4e`)  
**Thời gian khảo sát**: 2026-09-16T05:22:00Z  

---

## 1. OBSERVATION (Dữ liệu quan sát & Hiện trạng xác thực)

### 1.1. Bản đồ Nguồn Giao diện Stitch (`frontend-preview/`)
Qua kiểm tra cấu trúc thư mục tại `E:\PWD301\frontend-preview`, toàn bộ 33 màn hình Stitch nguyên bản phân bố tại 2 thư mục gốc:
- `frontend-preview/stitch_pwd301_course_management_platform/stitch_pwd301_course_management_platform/` (Folder 1)
- `frontend-preview/stitch_pwd301_course_management_platform (1)/stitch_pwd301_course_management_platform/` (Folder 2)

Dưới đây là ánh xạ thực tế đã được kiểm chứng bằng `find_by_name` và `view_file`:

| STT | Cổng phân hệ | Đường dẫn Template đích (`src/pwd301/templates/`) | Thư mục màn hình Stitch tương ứng (`frontend-preview/`) |
|:---:|:---|:---|:---|
| 1 | Instructor | `instructor/dashboard.html` | `Folder 1/pwd301_instructor_dashboard_clean_minimalist_focus/` & `Folder 1/pwd301_instructor_workspace_variant_3_carbon_governance_centric_academic_console/` |
| 2 | Instructor | `instructor/courses.html` | `Folder 2/pwd301_instructor_courses_variant_2_master_operations_table_detailed_provenance/` |
| 3 | Instructor | `instructor/course_manage.html` | `Folder 2/pwd301_extended_course_detail_variant_2_interactive_module_lesson_studio_bar/` & `Folder 2/pwd301_lesson_authoring_tr_nh_so_n_th_o_b_i_gi_ng_tr_c_quan_th_n_thi_n_low_tech/` |
| 4 | Instructor | `instructor/question_bank.html` | `Folder 2/pwd301_question_bank_hub_variant_2_master_operations_table_subject_inspector/` & `Folder 2/pwd301_extended_question_bank_studio_chi_ti_t_to_n_b_c_u_h_i_m_n_h_c/` |
| 5 | Instructor | `instructor/assessment_builder.html` | Bộ 5 màn hình Azota standard:<br>1. `pwd301_exam_method_selector_variant_1_split_master_selector_smart_dropzone/`<br>2. `pwd301_exam_general_config_bi_n_th_3_modular_wizard_academic_governance_matrix/`<br>3. `pwd301_exam_detailed_config_bi_n_th_1_chu_n_azota_tr_c_quan_d_d_ng_cho_gi_ng_vi/`<br>4. `pwd301_exam_preview_editor_bi_n_th_1_split_view_50_50_chu_n_azota_raw_syntax/`<br>5. `pwd301_exam_validation_bi_n_th_1_modal_th_m_nh_c_ch_kh_a_kh_c_ph_c_l_i_b_t_bu_c/` |
| 6 | Instructor | `instructor/grading.html` & `instructor/grade_attempt.html` | `Folder 2/pwd301_instructor_essay_grading_variant_1_split_canvas_50_50_focus_studio/` |
| 7 | Admin | `admin/dashboard.html` | `Folder 2/pwd301_admin_governance_variant_3_modular_tabbed_command_center_academic/` |
| 8 | Admin | `admin/operations.html`, `admin/health.html`, `admin/audit_logs.html`, `admin/backups.html` | `Folder 2/pwd301_admin_operations_security_variant_2_split_operations_cockpit_active/` |
| 9 | Admin | `admin/instructor_applications.html` | Hàng đợi thẩm định hồ sơ ứng viên với modal duyệt (`action=approve`) và từ chối (`action=reject`) |
| 10 | Auth | `auth/login.html`, `auth/register.html`, `auth/forgot_password.html`, `auth/reset_password.html`, `auth/change_password.html` | `Folder 1/pwd301_auth_account_lifecycle_variant_1_focused_card_interactive_inspector/` |

---

### 1.2. Hiện trạng Mã nguồn & Route Handlers Hiện tại

#### A. Phân hệ Giảng viên (`src/pwd301/blueprints/instructor/routes.py` - 2,771 dòng)
- **`GET /instructor/dashboard`** (`instructor.dashboard`):
  - Quyền hạn: `@instructor_required`
  - Context truyền vào: `overview` (tổng số khóa học `total_courses`, tổng số sinh viên `total_students`, số bài tự luận chờ chấm `pending_essay_grading_count`, tỷ lệ hoàn thành trung bình `average_completion_rate`), `courses` (danh sách thực thể `Course` thuộc sở hữu của `actor.id`).
- **`GET /instructor/courses`** (`instructor.my_courses`):
  - Quyền hạn: `@instructor_required`
  - Context truyền vào: `courses` (danh sách `Course` đang hoạt động, chưa bị xóa).
- **`POST /instructor/courses`** (`instructor.create_course_route`):
  - Form parameters: `course_code` (bắt buộc), `title` (bắt buộc), `description`, `category`, `difficulty`, `capacity` (mặc định 50).
  - CSRF: Bắt buộc `csrf_token`.
  - Kết quả: Redirect về `url_for('instructor.my_courses')` kèm Flash message thành công `Khóa học mới đã được tạo thành công!` hoặc lỗi trùng lặp `danger`.
- **`GET /instructor/courses/<course_id>/manage`** (`instructor.manage_course`):
  - Quyền hạn: `@instructor_required`, kiểm tra `require_course_manager`.
  - Context truyền vào:
    - `course`: Đối tượng khóa học.
    - `lessons`: Danh sách `Lesson` (sắp xếp theo `position`).
    - `file_assets`: Danh sách `FileAsset` của môn học kèm trạng thái quét virus (`CLEAN`, `SAFE`, `QUARANTINED`, `INFECTED`).
    - `assessments`: Danh sách `Assessment` của môn học.
    - `questions_count`: Số lượng câu hỏi thuộc ngân hàng đề môn học (`Question.status != 'TRASH'`).
    - `prerequisites`: Danh sách các môn tiên quyết hiện có.
    - `available_courses`: Danh sách các môn học có thể chọn làm tiên quyết (đã loại trừ môn hiện tại và các môn đã gán để phòng chống vòng lặp - Invariant 8).
    - `completion_rule`: Quy tắc điều kiện hoàn thành khóa học.
    - `active_tab`: Tab đang kích hoạt (`lessons`, `materials`, `assessments`, `questions`, `settings`).
- **`POST /instructor/courses/<course_id>`** (`instructor.update_course_route`):
  - Form parameters: `title`, `description`, `category`, `capacity`, `difficulty`, `learning_objectives`, `target_audience`, `completion_requirements`, `prerequisites`.
  - Chống Mass Assignment: Lọc whitelist nghiêm ngặt tại route.
- **`POST /instructor/courses/<course_id>/submit`** & **`POST /instructor/courses/<course_id>/cancel-submit`**:
  - Chuyển trạng thái khóa học `DRAFT` <-> `SUBMITTED_FOR_REVIEW`.
- **`POST /instructor/courses/<course_id>/publish`**:
  - Xuất bản khóa học (hỗ trợ Admin xuất bản trực tiếp).
- **`GET /instructor/courses/<course_id>/questions`** (`instructor.get_course_questions_route`):
  - Context: `course`, `questions` (danh sách câu hỏi đã serialize kèm `current_revision`).
- **`POST /instructor/courses/<course_id>/questions`** (`instructor.create_course_question_route`):
  - Form/JSON parameters: `content`, `question_type` (`SINGLE_CHOICE`, `MULTIPLE_CHOICE`, `TRUE_FALSE`, `SHORT_ANSWER`, `ESSAY`), `difficulty`, `default_points`, danh sách `choices` hoặc `correct_choice`.
- **`GET /instructor/assessments/<assessment_id>/edit`** (`instructor.get_instructor_assessment_detail_route`):
  - Context: `assessment` (dict chi tiết), `asm_obj` (thực thể Assessment), `course`, `available_questions`.
  - Invariants: `timing_locked` (nếu đã PUBLISHED), `structure_locked` (nếu đã có thí sinh bắt đầu làm bài `first_attempt_started_at is not None`).
- **`POST /instructor/assessments/<assessment_id>/questions`**:
  - Tạo câu hỏi trực tiếp trên trang đề thi.
- **`POST /instructor/assessments/<assessment_id>/import-document`**:
  - Upload tệp Word (.docx) hoặc PDF để tự động bóc tách thành các câu hỏi trong đề thi.
- **`GET /instructor/grading`** (`instructor.instructor_grading_overview`):
  - Context: `pending_attempts` (danh sách bài nộp cần chấm điểm tự luận trên toàn bộ các môn của giảng viên).
- **`GET /instructor/attempts/<attempt_id>/grading`** (`instructor.get_instructor_attempt_grading_route`):
  - Context: `attempt` (dữ liệu chi tiết bài thi, các câu hỏi và câu trả lời của thí sinh).
- **`POST /instructor/attempts/<attempt_id>/grades/<attempt_question_id>`** (`instructor.grade_instructor_essay_route`):
  - Form parameters: `awarded_points` (điểm chấm thực tế), `reason` (nhận xét/phản hồi).
  - CSRF: Bắt buộc. Redirect về trang chấm bài kèm flash `Đã lưu điểm và nhận xét cho câu hỏi thành công.`

#### B. Phân hệ Quản trị viên (`src/pwd301/blueprints/admin/routes.py` - 999 dòng)
- **`GET /admin/dashboard`** (`admin.dashboard`):
  - Context: `overview` bao gồm thống kê người dùng (`users`), thống kê khóa học (`courses`), thống kê bài thi (`assessments`), hồ sơ ứng tuyển giảng viên (`instructor_applications`), tệp cách ly (`quarantine_count`), và phần cứng máy chủ (`telemetry`).
- **`GET /admin/telemetry`** (`admin.admin_telemetry`):
  - Endpoint REST trả về JSON thời gian thực: CPU percent/cores/label, RAM percent/label/available, Disk percent/label/free, Network I/O throughput.
- **`GET /admin/health`** (`admin.admin_health`):
  - Context: `report` (đánh giá dịch vụ Database, Storage, RAG/Gemini, Background Workers), `telemetry`.
- **`GET /admin/audit-logs`** (`admin.list_audit_logs`):
  - Context: `items` (danh sách sự kiện Audit Log), `total`, `page`, `per_page`, `total_pages`, `filters`.
- **`GET /admin/backups`** & **`POST /admin/backups`** (`admin.admin_list_backups`, `admin.admin_create_backup`):
  - Quản lý sao lưu cơ sở dữ liệu và khôi phục (nghiêm cấm tự động ghi đè lên live database - Invariant 20).
- **`GET /admin/instructor-applications`** (`admin.admin_instructor_applications`):
  - Context: `applications`, `current_status` (`PENDING`, `APPROVED`, `REJECTED`, `ALL`), `pending_count`, `approved_count`, `rejected_count`.
- **`POST /admin/instructor-applications/<app_id>/review`** (`admin.admin_review_instructor_application`):
  - Form parameters: `csrf_token`, `action` (`approve` hoặc `reject`), `reason`.
  - Phê duyệt tự động cấp quyền `INSTRUCTOR` cho học viên mà không làm mất quyền `STUDENT` (mô hình vai trò tích lũy AUTH-002).

#### C. Phân hệ Xác thực Web (`src/pwd301/blueprints/auth/routes.py` - 681 dòng)
- **`GET /auth/login`** & **`POST /auth/login`**:
  - Hỗ trợ cả Form submit truyền thống và cùng nguồn AJAX JSON.
  - Chống dò quét brute-force qua `is_login_locked(ip, email)` -> trả về 429 kèm header `Retry-After`.
  - Chống Open Redirect qua `_is_safe_redirect_url(next_url)`.
  - Tạo `AuthSession` lưu phiên máy chủ (Database + HttpOnly Cookie); cấm tuyệt đối lưu JWT trong `localStorage`.
- **`GET /auth/register`** & **`POST /auth/register`**:
  - Tạo tài khoản học viên mới, phân quyền `STUDENT`.
- **`GET /auth/forgot-password`** & **`POST /auth/forgot-password`**:
  - Gửi mã xác nhận đặt lại mật khẩu an toàn.
- **`GET /auth/reset-password`** & **`POST /auth/reset-password`**:
  - Nhận `token` và đặt mật khẩu mới với xác thực độ phức tạp mật khẩu.

---

### 1.3. Kết quả Kiểm thử Cơ sở (Baseline Pytest Verification)
Đã chạy lệnh kiểm thử chính xác bằng môi trường ảo của dự án:
```powershell
E:\PWD301\.venv\Scripts\pytest.exe tests/api/test_instructor_course_web_flow.py tests/api/test_instructor_application_web_flow.py tests/api/test_auth_web.py tests/api/test_admin_audit_api.py -v
```
**Kết quả**: **32/32 tests PASSED 100% trong 26.77s**.
Không có bất kỳ test failure hoặc crash nào trên baseline hiện tại.

Các chuỗi ký tự và selector mà bộ test kiểm tra nghiêm ngặt (Regression Sensitive Strings):
1. `tests/api/test_auth_web.py:33`: `assert "Đăng nhập PWD301".encode() in resp.data`
2. `tests/api/test_auth_web.py:179`: `assert "Đăng ký tài khoản".encode() in get_resp.data`
3. `tests/api/test_instructor_course_web_flow.py:113`: `assert "Khóa học mới đã được tạo thành công" in html`
4. `tests/api/test_instructor_course_web_flow.py:220`: `assert "Cập nhật thông tin khóa học thành công" in html`
5. `tests/api/test_instructor_course_web_flow.py:288`: `assert "đã được xuất bản chính thức thành công" in html`
6. `tests/api/test_instructor_application_web_flow.py:59`: trích xuất regex `name="csrf_token" value="..."` từ hidden input.
7. `tests/api/test_instructor_application_web_flow.py:153`: `assert "Đại học Công nghệ Thông tin" in admin_page.text`

---

## 2. LOGIC CHAIN (Kiến trúc Dữ liệu & UI Data Binding)

### 2.1. Phân tách Kiến trúc Giao diện (App Shell vs View Content)
Trong hệ thống mới, `src/pwd301/templates/base.html` sẽ đảm nhận toàn bộ khung sườn:
- Topbar: Tích hợp thông tin tài khoản, chuông thông báo real-time, bộ chuyển đổi vai trò (Role Switcher: Học viên / Giảng viên / Quản trị viên), bộ chọn Ngôn ngữ (i18n: `vi`/`en`) và múi giờ (`Asia/Ho_Chi_Minh` UTC+7).
- Sidebar động: Tự động render menu theo `current_user.active_role`:
  - Khi vai trò là `INSTRUCTOR`: Render menu Nhóm Điều hành & Giảng dạy (Bàn làm việc, Khóa học, Đề cương, Ngân hàng câu hỏi), Nhóm Khảo thí & Đánh giá (Lịch dạy, Chấm điểm & SLA), Nhóm Cài đặt.
  - Khi vai trò là `ADMIN`: Render menu Chỉ huy Quản trị (Governance Matrix, Thẩm định Đề cương, Điều chuyển môn học, An toàn & Audit Trail).
  - Khi vai trò là `STUDENT`: Render menu Học tập (Khóa học của tôi, Bài tập, Trợ lý AI).
- Toàn bộ các template con (`instructor/*.html`, `admin/*.html`, `auth/*.html`) sẽ kế thừa `{% extends "base.html" %}` và định nghĩa nội dung trong `{% block content %}`.
- Riêng phân hệ `auth/*.html` (Login, Register, Forgot Password): Sử dụng layout tối giản (Centered Card Layout) không cần Sidebar nhưng giữ nguyên nhận diện thương hiệu PWD301.

### 2.2. Cơ chế Data Binding & Form Contracts chi tiết cho từng màn hình

#### A. `instructor/dashboard.html`
- **Màn hình Stitch**: `pwd301_instructor_dashboard_clean_minimalist_focus`
- **Dữ liệu Binding**:
  - Header: `Chào buổi sáng, {{ current_user.display_name }} 👋`
  - 3 Thẻ Chỉ số Hành động (KPI Action Cards):
    1. Chấm bài & SLA: `overview.pending_essay_grading_count` (nếu > 0 hiển thị badge cảnh báo SLA màu đỏ `danger-rose`). Nút hành động dẫn trực tiếp tới `{{ url_for('instructor.instructor_grading_overview') }}`.
    2. Khảo thí & Coi thi: Hiển thị thời gian và phòng thi ca gần nhất.
    3. Lớp học phụ trách: Tổng số khóa học `overview.total_courses`, tổng sinh viên `overview.total_students`, tỷ lệ hoàn thành `overview.average_completion_rate`.
  - Hàng đợi tác vụ ưu tiên (Action Queue): Liệt kê các bài thi chờ duyệt, bài tự luận cần chấm.
  - Bảng danh mục khóa học: Vòng lặp `{% for c in courses %}` hiển thị mã môn `{{ c.course_code }}`, tên môn `{{ c.title }}`, trạng thái badge (`DRAFT`, `SUBMITTED_FOR_REVIEW`, `APPROVED`, `PUBLISHED`), sĩ số, và nút thao tác dẫn tới `manage` và `questions`.

#### B. `instructor/courses.html`
- **Màn hình Stitch**: `pwd301_instructor_courses_variant_2_master_operations_table_detailed_provenance`
- **Kiến trúc Split Layout 7/12 & 5/12**:
  - Cột trái (7/12): Master Table danh sách các khóa học phụ trách với các bộ lọc: Tìm kiếm văn bản, Lọc theo nguồn gốc (Admin phân công / Giảng viên tự biên soạn), Lọc theo trạng thái.
  - Cột phải (5/12): Operations Drawer hiển thị chi tiết môn học đang được chọn (Active Selected Course): tiến độ đề cương, số bài học, liên kết nhanh tới bài giảng và đề thi.
  - Menu 3 chấm (Dropdown Actions): Chứa các thao tác workflow: "Quản lý khóa học", "Gửi Admin duyệt xuất bản" (`/submit`), "Xuất bản ngay" (`/publish` đối với Admin), "Rút lại yêu cầu" (`/cancel-submit`).
  - Modal "+ Tạo khóa học mới":
    - Form action: `{{ url_for('instructor.create_course_route') }}` (POST)
    - Input: `name="course_code"` (text, required), `name="title"` (text, required), `name="category"` (select), `name="difficulty"` (select: `BEGINNER`, `INTERMEDIATE`, `ADVANCED`), `name="capacity"` (number, default 50), `name="description"` (textarea).
    - Hidden: `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`.

#### C. `instructor/course_manage.html`
- **Màn hình Stitch**: `pwd301_extended_course_detail_variant_2` kết hợp `pwd301_lesson_authoring`
- **Tabs điều hướng**:
  1. Tab 1 `lessons` (Bài giảng & Giáo trình): Danh sách các bài học, kéo thả sắp xếp thứ tự, nút thêm bài học mới mở Studio biên soạn thân thiện (`pwd301_lesson_authoring`) với trình soạn thảo Markdown, gắn đính kèm tệp tài liệu (PDF, Word, Slide PPTX, Video bài giảng < 1GB).
  2. Tab 2 `materials` (Tài liệu & Tệp tin): Quản lý `FileAsset`, hiển thị tên tệp gốc, kích thước định dạng chuẩn (KB/MB), MIME type, trạng thái kiểm dịch virus (`CLEAN`, `QUARANTINED`). Hỗ trợ tải xuống an toàn qua route session auth.
  3. Tab 3 `assessments` (Đề thi & Kiểm tra): Danh sách bài thi, trạng thái khóa Invariant 13 & 14, nút tạo bài thi mới.
  4. Tab 4 `questions` (Ngân hàng câu hỏi): Thống kê và lối tắt sang studio ngân hàng đề.
  5. Tab 5 `settings` (Cài đặt & Xuất bản): Cập nhật thông số môn học, Mục tiêu & Kỹ năng (`learning_objectives`), Yêu cầu môn học (`completion_requirements`), Điều kiện tiên quyết (`prerequisites` với danh sách loại trừ môn chu trình - Cycle-Free Prerequisite Tree), Quy tắc hoàn thành (`completion_rule`).

#### D. `instructor/question_bank.html`
- **Màn hình Stitch**: `pwd301_question_bank_hub_variant_2` & `pwd301_extended_question_bank_studio`
- **Kiến trúc**:
  - Bảng tra cứu câu hỏi với bộ lọc theo loại câu hỏi (Trắc nghiệm đơn, Nhiều đáp án, Đúng/Sai, Trả lời ngắn, Tự luận) và mức độ tư duy Bloom (Nhận biết, Thông hiểu, Vận dụng, Phân tích, Đánh giá).
  - Hiển thị phiên bản hiện tại `v{{ (q.current_revision.revision_no if q.current_revision else q.current_revision_no) or 1 }}` và cờ đánh dấu khóa sửa trực tiếp nếu câu hỏi đang được sử dụng trong bài thi đang diễn ra (Question Invariant).
  - Modal tạo câu hỏi với form động: Tự động ẩn/hiện trường nhập đáp án A/B/C/D hoặc Đúng/Sai khi thay đổi `question_type`.
  - Modal nạp câu hỏi từ tệp Word (.docx) / PDF.

#### E. `instructor/assessment_builder.html` (Bộ 5 màn hình Azota Standard)
- **Tích hợp 5 màn hình thành một Studio Thống nhất theo Stepper**:
  - **Bước 1 - Lựa chọn phương thức nạp đề** (`pwd301_exam_method_selector`): Cho phép chọn giữa: (A) Tải tệp PDF/Word qua Smart Dropzone, (B) Chọn câu hỏi từ Ngân hàng đề, (C) Soạn thảo thủ công.
  - **Bước 2 - Soạn thảo & Bóc tách 50/50 Split View** (`pwd301_exam_preview_editor`):
    - Khung trái (50%): Trình soạn thảo văn bản thô theo cú pháp chuẩn Azota:
      ```text
      Câu 1: Hàm nào trong Flask dùng để render template HTML?
      A. render_template
      B. make_response
      C. jsonify
      D. send_file
      *A
      ```
    - Khung phải (50%): Giấy thi số hóa hiển thị thời gian thực theo giao diện đề thi chuẩn, cho phép giảng viên tương tác chọn đáp án, xem trước bảng trả lời trắc nghiệm (Palette navigator).
  - **Bước 3 - Cấu hình khảo thí chi tiết** (`pwd301_exam_general_config` & `pwd301_exam_detailed_config`):
    - Thời lượng thi (`time_limit_minutes`), phần trăm đạt (`passing_percent`), khung giờ mở/đóng thi (`open_at`, `close_at`).
    - Cấu hình đảo câu hỏi, đảo phương án, cấu hình hiển thị đáp án sau thi, cấu hình chống gian lận.
  - **Bước 4 - Thẩm định cấu trúc đề trước khi xuất bản** (`pwd301_exam_validation`):
    - Modal kiểm tra tự động trước khi bấm "Xuất bản đề thi":
      1. Kiểm tra tổng điểm đạt 10.0 / 100%.
      2. Kiểm tra không có câu hỏi nào bị khuyết đáp án đúng.
      3. Cảnh báo Timing Lock (Invariant 13) và Structural Freeze (Invariant 14).

#### F. `instructor/grading.html` & `instructor/grade_attempt.html`
- **Màn hình Stitch**: `pwd301_instructor_essay_grading_variant_1_split_canvas_50_50_focus_studio`
- **Kiến trúc Split Canvas 50/50 Chấm tự luận**:
  - Khung trái (50% - Student Submission Pane):
    - Banner "Frozen Attempt Snapshot" hiển thị thời gian nộp bài, mã hash SHA-256 bảo vệ toàn vẹn bài nộp.
    - Đề bài và bài làm của thí sinh (mã nguồn, bài tự luận) với định dạng khối code sạch sẽ, thụt lề chuẩn xác.
  - Khung phải (50% - Grading & Feedback Studio):
    - Thanh điều hướng thí sinh: `Bài X / Y cần chấm`, chuyển nhanh giữa các bài nộp.
    - Tiêu chí chấm điểm (Rubric) và ô nhập điểm `awarded_points` (ràng buộc `min=0` và `max=points_assigned`).
    - Nhận xét phản hồi `reason`.
    - Nút "Lưu điểm chấm câu này" submit POST tới `url_for('instructor.grade_instructor_essay_route', attempt_id=attempt.attempt_id, attempt_question_id=q.attempt_question_id)`.

#### G. `admin/dashboard.html` & `admin/operations.html`
- **Màn hình Stitch**: `pwd301_admin_governance_variant_3` & `pwd301_admin_operations_security_variant_2`
- **Kiến trúc Modular Tabbed Command Center**:
  - Executive Telemetry Header:
    - Hiển thị thông số phần cứng trực tiếp từ máy chủ vật lý/ảo: CPU cores & %, RAM GB & %, Ổ đĩa Disk GB & %, Network I/O.
    - Tích hợp JS tự động polling `/admin/telemetry` mỗi 15 giây và nút "Làm mới phần cứng" có animation xoay mượt mà.
  - 4 Tab điều hành chuyên sâu:
    - Tab 1: Quản trị Người dùng & Phân quyền RBAC (`tab-users`).
    - Tab 2: Hàng đợi Thẩm định Đề cương, Khóa học & Duyệt Giảng viên (`tab-review`).
    - Tab 3: Điều chuyển & Phân công Giảng dạy (`tab-reassign`).
    - Tab 4: An toàn Học thuật, Nhật ký Kiểm toán & Sao lưu (`tab-security` / Operations Cockpit).

#### H. `admin/instructor_applications.html`
- Hàng đợi thẩm định hồ sơ: Lọc theo 4 trạng thái (`PENDING`, `APPROVED`, `REJECTED`, `ALL`).
- Bảng hiển thị thông tin ứng viên: Họ tên, Email, Cơ sở giáo dục (`institution_name`), Khoa phòng ban, Chuyên môn đào tạo, Năm kinh nghiệm, Minh chứng giảng dạy.
- Modal Duyệt hồ sơ: Submit POST tới `/admin/instructor-applications/<app_id>/review` với `action="approve"` và lý do.
- Modal Từ chối hồ sơ: Submit POST với `action="reject"` và lý do từ chối.
- Bảo toàn CSRF và Flash message phản hồi.

#### I. `auth/login.html`, `auth/register.html`, `auth/forgot_password.html`
- **Màn hình Stitch**: `pwd301_auth_account_lifecycle_variant_1_focused_card_interactive_inspector`
- Thẻ Card thiết kế tập trung, tinh tế, sử dụng Tailwind CSS, typography Plus Jakarta Sans & Inter.
- Tiêu đề bắt buộc:
  - Login: `<h1 class="...">Đăng nhập PWD301</h1>` (Bảo đảm kiểm thử `test_login_page_renders_get` luôn PASS).
  - Register: `<h1 class="...">Đăng ký tài khoản</h1>` (Bảo đảm kiểm thử `test_register_page_and_submit` luôn PASS).
- Form actions và CSRF tokens được giữ nguyên vẹn 100%.

---

## 3. CAVEATS & RISKS (Các rủi ro kỹ thuật & Giải pháp phòng ngừa)

1. **Rủi ro vỡ CSS do xung đột CDN Tailwind với các class cũ**:
   - *Nguy cơ*: Các trang cũ đang dùng một số class Bootstrap 5 (`btn btn-primary`, `d-flex`, `card`, `col-md-3`). Nếu nạp Tailwind mà xóa đột ngột class Bootstrap khi chưa cập nhật đầy đủ, giao diện sẽ bị vỡ layout.
   - *Giải pháp*: Trong quá trình chuyển đổi từng trang, áp dụng Tailwind utilities 100% thay thế hoàn toàn các class Bootstrap, đồng thời duy trì cấu trúc DOM semantic sạch sẽ.
2. **Rủi ro vi phạm Invariant 13 & 14 trong Assessment Builder**:
   - *Nguy cơ*: Khi tích hợp bộ 5 màn hình Azota, nếu vô tình cho phép giảng viên sửa câu hỏi hoặc thời lượng khi đề thi đã có học viên làm bài (`first_attempt_started_at is not None`), hệ thống backend sẽ ném ngoại lệ `AssessmentLockedError` (409) gây crash trang nếu frontend không disable form.
   - *Giải pháp*: Đưa cờ `timing_locked` và `structure_locked` vào tất cả các nút hành động và ô input trong Azota Studio (sử dụng thuộc tính `disabled` và hiển thị Banner cảnh báo Invariant rõ ràng).
3. **Rủi ro rò rỉ Khóa chính nội bộ (BigInt PK Leakage - ADR-002)**:
   - *Nguy cơ*: Hiển thị ID số của cơ sở dữ liệu trên giao diện web hoặc URL thay vì Public UUID.
   - *Giải pháp*: Chỉ sử dụng `public_id` hoặc `course_id` (UUID) trên tất cả các thẻ `<a>`, `<form action>`, và hàm JavaScript; chỉ dùng ID nội bộ trên các route quản trị riêng biệt đã được kiểm toán (như `InstructorApplication.id`).
4. **Rủi ro thất thoát CSRF token trên các Form động**:
   - *Nguy cơ*: Các modal như Tạo khóa học, Thẩm định ứng viên, Chấm bài tự luận nếu được chèn qua JavaScript mà thiếu `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">` sẽ bị lỗi HTTP 400 Bad Request.
   - *Giải pháp*: Mọi form đều phải nhúng sẵn token hoặc nạp từ thẻ meta `<meta name="csrf-token">`.

---

## 4. CONCRETE IMPLEMENTATION PLAN (Kế hoạch Triển khai cho Milestones 3 & 4)

Quá trình chuyển đổi sẽ được chia thành 2 giai đoạn (Milestone 3 và Milestone 4) tương ứng với từng phân hệ:

### Giai đoạn 1: Milestone 3 — Tích hợp Cổng Giảng viên (Instructor Portal)
- **Bước 3.1: Chuyển đổi `instructor/dashboard.html`**
  - Kế thừa `base.html`, tích hợp KPI cards (chấm bài SLA, khảo thí, lớp học).
  - Render bảng khóa học kèm badge trạng thái và drawer thao tác nhanh.
- **Bước 3.2: Chuyển đổi `instructor/courses.html`**
  - Chuyển đổi sang giao diện Split Table 7/12 & Operations Drawer 5/12 (`pwd301_instructor_courses_variant_2`).
  - Tích hợp Modal tạo khóa học mới với đầy đủ trường dữ liệu (`course_code`, `title`, `category`, `difficulty`, `capacity`, `description`).
  - Kiểm tra các test trong `tests/api/test_instructor_course_web_flow.py` chạy qua 100%.
- **Bước 3.3: Chuyển đổi `instructor/course_manage.html`**
  - Tích hợp giao diện `pwd301_extended_course_detail_variant_2`.
  - Tích hợp Studio biên soạn bài giảng `pwd301_lesson_authoring` với vùng upload đa phương tiện (PDF, DOCX, PPTX, Video).
  - Hoàn thiện 5 tab chức năng: Lessons, Materials, Assessments, Questions, Settings.
- **Bước 3.4: Chuyển đổi `instructor/question_bank.html`**
  - Tích hợp `pwd301_question_bank_hub_variant_2` & `pwd301_extended_question_bank_studio`.
  - Cung cấp bộ lọc theo loại câu hỏi, cấp độ Bloom, hiển thị versioning và trạng thái khóa sửa trực tiếp.
- **Bước 3.5: Chuyển đổi `instructor/assessment_builder.html` (Azota Standard 50/50)**
  - Tích hợp luồng Stepper 3 bước: Nạp đề & File -> Soạn thảo & Bóc tách (Split View 50/50 Raw Syntax vs Live Preview) -> Cấu hình khảo thí.
  - Tích hợp Modal thẩm định lỗi bắt buộc trước khi xuất bản (`pwd301_exam_validation`).
  - Bảo đảm các invariant Timing Lock và Structural Freeze.
- **Bước 3.6: Chuyển đổi `instructor/grading.html` & `instructor/grade_attempt.html`**
  - Tích hợp giao diện Split Canvas 50/50 Focus Studio (`pwd301_instructor_essay_grading_variant_1`).
  - Nửa trái: Frozen Attempt Snapshot & bài làm thí sinh.
  - Nửa phải: Tiêu chí chấm điểm Rubric, nhập điểm `awarded_points`, nhận xét `reason`, chuyển bài nộp kế tiếp.

### Giai đoạn 2: Milestone 4 — Tích hợp Cổng Quản trị & Xác thực (Admin & Auth)
- **Bước 4.1: Chuyển đổi `admin/dashboard.html`**
  - Tích hợp giao diện `pwd301_admin_governance_variant_3` với 4 tab chuyên sâu (Users, Review, Reassign, Security).
  - Tích hợp khối Executive Hardware Telemetry kết nối AJAX `/admin/telemetry` (CPU, RAM, Disk, Network) có hiệu ứng xoay làm mới.
- **Bước 4.2: Chuyển đổi `admin/operations.html`, `admin/health.html`, `admin/audit_logs.html`, `admin/backups.html`**
  - Tích hợp giao diện `pwd301_admin_operations_security_variant_2` (Split Operations Cockpit).
- **Bước 4.3: Chuyển đổi `admin/instructor_applications.html`**
  - Bảng thẩm định hồ sơ ứng viên với các tab trạng thái (`PENDING`, `APPROVED`, `REJECTED`, `ALL`).
  - Modal phê duyệt và từ chối với lý do, bảo đảm chạy đỗ bài kiểm thử `test_instructor_application_web_flow.py`.
- **Bước 4.4: Chuyển đổi `auth/login.html`, `auth/register.html`, `auth/forgot_password.html`, `auth/reset_password.html`**
  - Tích hợp thẻ Card sang trọng từ `pwd301_auth_account_lifecycle_variant_1`.
  - Giữ nguyên các chuỗi tiêu đề then chốt: `Đăng nhập PWD301` và `Đăng ký tài khoản`.

---

## 5. VERIFICATION METHOD (Phương thức Xác minh & Kiểm thử Độc lập)

Để xác minh độc lập tính chính xác và không bị hồi quy (Zero Regression), tác nhân triển khai cần chạy các lệnh sau:

1. **Kiểm thử Luồng Web Giảng viên & Khóa học**:
   ```powershell
   E:\PWD301\.venv\Scripts\pytest.exe tests/api/test_instructor_course_web_flow.py -v
   ```
   *Điều kiện pass*: 7/7 bài kiểm tra đạt trạng thái `PASSED`.

2. **Kiểm thử Luồng Ứng tuyển & Duyệt Giảng viên Admin**:
   ```powershell
   E:\PWD301\.venv\Scripts\pytest.exe tests/api/test_instructor_application_web_flow.py -v
   ```
   *Điều kiện pass*: 8/8 bài kiểm tra đạt trạng thái `PASSED`.

3. **Kiểm thử Xác thực Web UI & Session**:
   ```powershell
   E:\PWD301\.venv\Scripts\pytest.exe tests/api/test_auth_web.py -v
   ```
   *Điều kiện pass*: 11/11 bài kiểm tra đạt trạng thái `PASSED`.

4. **Kiểm thử Soạn thảo Đề thi Milestone 3 (Azota Authoring & Import)**:
   ```powershell
   E:\PWD301\.venv\Scripts\pytest.exe tests/test_m3_assessment_authoring.py -v
   ```
   *Điều kiện pass*: Tất cả các bài kiểm tra authoring, direct question, docx/pdf import, timing lock và structural freeze đều đạt `PASSED`.

5. **Kiểm tra cú pháp & Linting toàn diện**:
   ```powershell
   python scripts/repo_check.py
   ruff check src tests
   mypy src
   ```

---
*Báo cáo khảo sát hoàn thành và sẵn sàng bàn giao cho Orchestrator và các Execution Agents.*
