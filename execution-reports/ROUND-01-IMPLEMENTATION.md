# VÒNG 1: TRIỂN KHAI & TÍCH HỢP HỆ THỐNG (FULL IMPLEMENTATION)
## Dự án PWD301 LMS — Nâng cấp Toàn diện 6 Hạng mục

---

### 1. Mục tiêu Vòng 1
Triển khai toàn bộ các yêu cầu của kế hoạch nâng cấp vào source code thực tế của dự án PWD301 LMS, bao gồm Backend (Models, Services, Blueprints), Cơ sở dữ liệu SQL Server (Migrations, DDL Backfill), và Frontend Web Client (Views, Components). Tuyệt đối không sử dụng code placeholder hay mock tạm thời.

---

### 2. Công việc Thực tế Đã Thực hiện

#### Hạng mục 1: Bảo vệ Video & Cổng Kiểm soát Xác thực Email
- **Database & Model**:
  - Tại [`src/pwd301/models/identity.py`](file:///e:/PWD301/src/pwd301/models/identity.py): Thêm `@property def is_email_verified(self) -> bool` dựa trên giá trị `self.email_verified_at is not None`.
  - Backfill CSDL: Chạy lệnh SQL Server cập nhật `email_verified_at = SYSUTCDATETIME()` cho toàn bộ tài khoản học viên hiện hữu.
- **Backend API**:
  - Tại [`src/pwd301/blueprints/auth/routes.py`](file:///e:/PWD301/src/pwd301/blueprints/auth/routes.py) và [`src/pwd301/blueprints/api_auth/routes.py`](file:///e:/PWD301/src/pwd301/blueprints/api_auth/routes.py): Bổ sung trường `"is_email_verified"` vào payload phản hồi phiên đăng nhập và endpoint `/auth/me`.
  - Tại [`src/pwd301/blueprints/api_files/routes.py`](file:///e:/PWD301/src/pwd301/blueprints/api_files/routes.py): Thêm lớp phòng thủ Fail-Closed tại `download_file_api` (endpoint `/api/files/<asset_id>/stream`). Nếu người dùng có vai trò học sinh và chưa xác thực email (`is_email_verified == False`), hệ thống chặn ngay lập tức với mã HTTP 403 `EMAIL_NOT_VERIFIED`.
- **Frontend Client**:
  - Tại [`frontend/assets/js/views/student.js`](file:///e:/PWD301/frontend/assets/js/views/student.js): Bổ sung kiểm tra `isEmailVerified`. Khi học sinh chưa xác thực, giao diện hiển thị thẻ thông báo Amber (WCAG AA compliant) hướng dẫn kiểm tra hòm thư, hoàn toàn không khởi tạo Video Player hay VideoArmor.

#### Hạng mục 2: Xuất PDF Kết quả, LaTeX & Cấu hình Ẩn Kết quả
- **Database Migration**:
  - Tạo tệp di chuyển [`migrations/versions/allowresults20261014_allow_student_view_results.py`](file:///e:/PWD301/migrations/versions/allowresults20261014_allow_student_view_results.py) bổ sung cột `allow_student_view_results BIT NOT NULL DEFAULT 1` vào bảng `assessments`.
- **Backend Services**:
  - Tại [`src/pwd301/models/assessment.py`](file:///e:/PWD301/src/pwd301/models/assessment.py) & [`src/pwd301/services/assessment_service.py`](file:///e:/PWD301/src/pwd301/services/assessment_service.py): Bổ sung trường `allow_student_view_results`, ánh xạ dữ liệu khi tạo và cập nhật bài thi.
  - Tại [`src/pwd301/services/attempt_service.py`](file:///e:/PWD301/src/pwd301/services/attempt_service.py): Tại `get_attempt_result_for_student`, khi `allow_student_view_results == False`, hệ thống gán `score_status = "RESULTS_HIDDEN"`, ẩn toàn bộ điểm số, xếp loại và che giấu toàn bộ đáp án của từng câu hỏi.
  - Tại [`src/pwd301/services/result_pdf_service.py`](file:///e:/PWD301/src/pwd301/services/result_pdf_service.py):
    - Xây dựng parser toán học `_render_math_and_plain()` duyệt cặp ngoặc cân bằng (balanced braces), chuyển đổi các biểu thức LaTeX phổ biến (`\frac{a}{b}`, `\sqrt{x}`, `x^2`, `y_1`, `\int`, `\sum`, ký hiệu Hy Lạp) thành thẻ XML hợp lệ của ReportLab (`<sup>`, `<sub>`) và ký tự Unicode sắc nét.
    - Xử lý che giấu thông tin khi `allow_student_view_results == False`: Điền ký tự gạch ngang `-` vào 3 cột "Đáp án đã chọn", "Kết quả", "Điểm", ẩn điểm tổng và hiển thị badge `ĐÃ GHI NHẬN BÀI NỘP`.
- **Frontend Client**:
  - Tại [`frontend/assets/js/views/instructor-exams.js`](file:///e:/PWD301/frontend/assets/js/views/instructor-exams.js): Bổ sung checkbox "Cho phép học sinh xem chi tiết kết quả" trong modal tạo/sửa bài thi.
  - Tại [`frontend/assets/js/views/student.js`](file:///e:/PWD301/frontend/assets/js/views/student.js): Render thiệp thông báo nộp bài thành công khi `score_status === 'RESULTS_HIDDEN'`.

#### Hạng mục 3: UI Màu sắc Đúng/Sai trong Câu hỏi Tương tác
- **Frontend Client**:
  - Loại bỏ các class màu xanh mòng két (`teal`) xung đột trong live preview của giảng viên và xem lại kết quả thi của học sinh.
  - Áp dụng bảng màu phân định rõ nét: Xanh lục bảo (`border-emerald-500`, `bg-emerald-50 dark:bg-emerald-950/30`) cho đáp án đúng; Đỏ hoa hồng (`border-rose-500`, `bg-rose-50 dark:bg-rose-950/30`) cho đáp án sai.
  - Tuân thủ nghiêm ngặt Invariant 10.12: Phòng thi chính thức giữ các ô màu trung tính (`#f8fafc` / `#1e293b`) trong suốt thời gian làm bài, chỉ hiển thị đúng/sai sau khi nộp bài.

#### Hạng mục 4: Điều hướng Bài học và Quy tắc Hoàn thành
- **Frontend Client ([`student.js`](file:///e:/PWD301/frontend/assets/js/views/student.js))**:
  - Chuẩn hóa toàn bộ nhãn nút điều hướng thành "Tiếp theo" và "Quay lại" trong mọi ngữ cảnh (`renderBottomNextButton`, `renderBottomNav`, floating navigation).
  - Loại bỏ hoàn toàn icon ổ khóa và chú thích `(Đang khóa)`.
  - Thống nhất màu sắc trạng thái: Mở khóa = Xanh lục bảo (`bg-emerald-600`); Bị khóa = Xám trung tính (`bg-slate-200 dark:bg-slate-800`).
  - Thiết lập cơ chế dwell time 30s cho bài đọc và đồng bộ tiến độ học tập đa thành phần (video, quiz) bền vững với Backend.

#### Hạng mục 5: Phòng thủ Đa tầng Bài thi Cuối kỳ (Final Exam)
- **Backend Enforcement**:
  - Tại [`src/pwd301/services/attempt_service.py`](file:///e:/PWD301/src/pwd301/services/attempt_service.py#L650): Trong `start_assessment_attempt`, nếu bài thi thuộc diện `FINAL` hoặc `FINAL_EXAM`, hệ thống truy vấn tổng số bài học `PUBLISHED` trong khóa học so với số bài học học viên đã hoàn thành. Nếu chưa đạt 100%, từ chối ngay lập tức với `AttemptValidationError` (HTTP 403 Forbidden).
  - Tại [`src/pwd301/blueprints/student/routes.py`](file:///e:/PWD301/src/pwd301/blueprints/student/routes.py): Endpoint `/assessments` và `/assessments/<id>` tính toán `is_locked`, `lock_reason` và `can_start` gửi kèm cho client.
- **Frontend Client ([`student.js`](file:///e:/PWD301/frontend/assets/js/views/student.js))**:
  - Trang "Bài kiểm tra": Nút "Vào thi" chuyển sang màu xám vô hiệu hóa (`bg-slate-100 text-slate-400 cursor-not-allowed`) kèm huy hiệu `Chưa đủ điều kiện thi` và tooltip thông báo chi tiết số bài cần hoàn thành (`x/y bài`).
  - Waiting Room: Render trạng thái `LOCKED_PREREQUISITE` ngăn chặn bấm nút bắt đầu thi.

#### Hạng mục 6: Vòng đời Khóa học DRAFT và PUBLISHED / STAGING_DRAFT
- **Frontend Client ([`instructor.js`](file:///e:/PWD301/frontend/assets/js/views/instructor.js))**:
  - Khóa học `DRAFT`: Giảng viên chỉnh sửa trực tiếp, hiển thị duy nhất 01 nút "Gửi xét duyệt khóa học" tới Admin.
  - Khóa học `PUBLISHED`: Toàn bộ các thay đổi mới được tích lũy vào 01 bản nháp hợp nhất (`STAGING_DRAFT`), hiển thị duy nhất 01 nút "Gửi xét duyệt bản nháp" để Admin phê duyệt All-or-Nothing.

---

### 3. Danh sách File Thay đổi trong Vòng 1
- `src/pwd301/models/identity.py`
- `src/pwd301/models/assessment.py`
- `migrations/versions/allowresults20261014_allow_student_view_results.py`
- `src/pwd301/services/assessment_service.py`
- `src/pwd301/services/attempt_service.py`
- `src/pwd301/services/result_pdf_service.py`
- `src/pwd301/blueprints/api_files/routes.py`
- `src/pwd301/blueprints/auth/routes.py`
- `src/pwd301/blueprints/api_auth/routes.py`
- `src/pwd301/blueprints/student/routes.py`
- `frontend/assets/js/components/video-armor.js`
- `frontend/assets/js/views/instructor-exams.js`
- `frontend/assets/js/views/instructor.js`
- `frontend/assets/js/views/student.js`

---

### 4. Kết luận Vòng 1
Toàn bộ mã nguồn cốt lõi của cả 6 hạng mục đã được triển khai hoàn tất và kết nối đồng bộ giữa Backend, Database và Frontend. Chuyển ngay sang **Vòng 2: Deep Audit + Real-World Testing**.
