# Kế hoạch Triển khai Toàn diện: Hệ thống Cấu hình Xem lại Khảo thí, Xuất bản PDF Học vụ, Giao diện Xem trước & Xét duyệt Khóa học

> **Tài liệu Kế hoạch:** `docs/superpowers/plans/2026-10-09-comprehensive-assessment-review-pdf-and-course-approval-system.md`  
> **Mục tiêu:** Xóa sạch toàn bộ logic, tài liệu và bộ nhớ cũ của các luồng workflow trước; đồng thời thiết lập hệ thống chuẩn mực mới bao gồm: (1) Cấu hình 3 chế độ xem lại bài thi của Giảng viên & UI học viên đánh dấu Đúng/Sai/Thiếu trực tiếp (bỏ cụm A/B/C/D); (2) Tái thiết kế 2 mẫu PDF Bảng điểm cá nhân & Tổng hợp lớp theo ReportLab cao cấp; (3) Giao diện xem trước 2 cột chuẩn NetAcad với Cây thư mục bài học; (4) Khắc phục lỗi phát Video upload và (5) Khắc phục triệt để lỗi 500 khi Admin xét duyệt thay đổi & khóa học.  
> **Trạng thái:** Chờ Chủ dự án duyệt (`/plan`) trước khi thực thi mã nguồn.  
> **Ngày lập:** 09/10/2026  

---

## 1. Mục tiêu Cốt lõi & Cam kết Bãi bỏ Cũ (Legacy Purge Contract)

### 1.1. Cam kết Bãi bỏ Vĩnh viễn (Permanent Purge Statement)
Trước khi viết mã tính năng mới, hệ thống sẽ tiến hành xóa sạch và thay thế toàn bộ mô tả, tài liệu, bộ nhớ và logic cũ liên quan đến các luồng này:
1. **Bãi bỏ hoàn toàn logic hiển thị nút A/B/C/D rời rạc**: Xóa bỏ vĩnh viễn cụm nút A/B/C/D ở chân card câu hỏi; chuyển 100% sang hiển thị trạng thái Đúng/Sai/Thiếu trực tiếp trên từng phương án.
2. **Bãi bỏ cơ chế in mã định danh UUID trong PDF**: Bảng điểm cá nhân và tổng hợp tuyệt đối không in chuỗi UUID thay cho nội dung câu trả lời, tên khóa học hay mã bài thi.
3. **Bãi bỏ định dạng số thập phân cồng kềnh**: Bãi bỏ kiểu format cứng `.2f` (như `100.00`, `0.00`), thay thế bằng quy chuẩn số chẵn bỏ thập phân (`100`, `0`), số lẻ làm tròn 2 chữ số (`50.5`, `33.33`).
4. **Bãi bỏ giao diện xem trước dạng pills/tabs ngang**: Xóa bỏ layout xem trước manh mún; thay thế bằng bố cục 2 cột chuẩn Student Lesson Reader (Cây thư mục bên trái, Nội dung học tập bên phải).
5. **Bãi bỏ cách truyền video upload qua route download sinh viên**: Xóa bỏ việc trỏ thẻ `<video>` vào route `/student/files/<id>/download` (vốn bị chặn bởi DRM và phân quyền); thiết lập endpoint streaming an toàn chuyên biệt cho Giảng viên & Admin.
6. **Bãi bỏ các giả định lỗi trong luồng xét duyệt Change Request**: Xóa bỏ các nhánh code gây 500 khi thiếu trường dữ liệu, xử lý nhất quán mọi dạng yêu cầu thay đổi (Metadata, Lesson, Resources, Changeset, Prerequisite).

---

## 2. Global Constraints & Review Focus

### 2.1. Global Constraints
- **Pure Headless Backend**: Mọi endpoint backend chỉ phục vụ JSON REST API theo phong bì chuẩn `{"success": true/false, "data": ..., "error": ...}`.
- **Fail-Closed DRM Protection**: Không bao giờ cung cấp link tải trực tiếp video bài giảng gốc cho sinh viên; video tải lên của giảng viên chỉ phát trong trình phát bảo mật hoặc endpoint xem trước có xác thực quyền.
- **ReportLab Typography**: Mọi tệp PDF xuất ra phải dùng font Unicode hợp lệ (Arial / DejaVuSans), hỗ trợ đầy đủ tiếng Việt có dấu, không bị vỡ bố cục trên trang A4.
- **TDD Iron Law**: Mọi sửa đổi backend phải đi kèm unit/integration test viết trước, kiểm chứng fail và pass thực nghiệm.

### 2.2. Review Focus
1. **Ẩn đáp án đúng ở chế độ "Chỉ xem đúng/sai"**: Khi giảng viên cấu hình chỉ cho xem đúng/sai, backend tuyệt đối không trả về `is_correct` của các phương án mà học sinh không chọn hoặc giải thích câu hỏi.
2. **Đánh dấu đáp án "Thiếu" cho câu hỏi nhiều lựa chọn (MULTI)**: Ở chế độ "Xem đầy đủ", phương án đúng mà học sinh bỏ sót phải được đánh dấu rõ là "Thiếu/Bỏ sót" (màu vàng/cam) để học sinh biết mình đã chọn thiếu phương án.
3. **Thẩm mỹ và căn lề PDF**: Kiểm tra các trường hợp tên khóa học hoặc nội dung đáp án rất dài không làm tràn ô hoặc vỡ khung bảng điểm.
4. **Range-Request Streaming cho Video**: Video upload dung lượng lớn có thể tua (seek) mượt mà đến mọi giây trên trình duyệt mà không cần tải toàn bộ tệp về bộ nhớ RAM.
5. **Idempotent Approval**: Duyệt lại hoặc từ chối lại một yêu cầu đã xử lý không được gây crash hệ thống (trả về thông báo trạng thái rõ ràng).

---

## 3. Kế hoạch Triển khai Từng Bước (Task Breakdown)

### Task 0: Dọn sạch Toàn diện Logic & Mô tả Cũ (System-Wide Legacy Purge & Spec Reset)
**Mục tiêu:** Cập nhật các file tài liệu đặc tả, task list và xóa bỏ các đoạn mã/ghi chú cũ lỗi thời để toàn bộ hệ thống chỉ có một nguồn chân lý mới (Single Source of Truth).
- **Files:**
  - Cập nhật: `tasks/CURRENT.md`
  - Cập nhật: `docs/system/PWD301_SYSTEM_SPECIFICATION/business/08_ASSESSMENT_ENGINE.md`
  - Cập nhật: `docs/system/PWD301_SYSTEM_SPECIFICATION/frontend/04_ADMIN_UI_FLOWS.md`
  - Cập nhật: `docs/features/admin.md`
- **Các bước thực hiện:**
  1. [ ] Ghi rõ định nghĩa mới về 3 chế độ xem lại bài thi (`review_mode`: `HIDDEN`, `SCORE_ONLY`, `FULL_ANSWERS`) vào tài liệu đặc tả khảo thí.
  2. [ ] Ghi rõ quy chuẩn định dạng số điểm và tiêu chuẩn xuất bản PDF (Thành phố Hồ Chí Minh, Có giám sát nâng cao).
  3. [ ] Cập nhật tài liệu luồng xem trước của Giảng viên & Admin sang mô hình Cây thư mục 2 cột.
  4. [ ] Khóa các bất biến này vào `tasks/CURRENT.md` để các lượt làm việc tiếp theo không bao giờ bị quay về thiết kế cũ.

---

### Task 1: Backend - Nâng cấp Mô hình & Cấu hình Xem lại Bài thi (Assessment Review Policy Engine)
**Mục tiêu:** Hỗ trợ Giảng viên chọn chính sách xem lại bài thi và đảm bảo Backend chỉ trả về dữ liệu tương ứng với chính sách đó.
- **Files:**
  - Sửa đổi: `src/pwd301/models/assessment.py` (Mở rộng hoặc ánh xạ `answer_visibility_policy` thành 3 chế độ: `NEVER` / `HIDDEN` = Không xem, `CORRECT_WRONG_ONLY` = Chỉ xem đúng/sai từng câu, `IMMEDIATE` / `FULL` = Xem đầy đủ).
  - Sửa đổi: `src/pwd301/services/assessment_service.py` (Validation và lưu cấu hình).
  - Sửa đổi: `src/pwd301/services/attempt_service.py` (Xử lý ẩn/hiện đáp án đúng, nhãn phương án, giải thích dựa trên chính sách đã cấu hình).
  - Test: `tests/api/test_assessment_review_policy.py`
- **Các bước thực hiện:**
  1. [ ] Viết test fail: Kiểm tra khi `answer_visibility_policy` là `CORRECT_WRONG_ONLY`, endpoint `GET /student/assessments/attempts/<id>/result` chỉ trả về `is_correct` của câu hỏi và câu học viên đã chọn, hoàn toàn KHÔNG trả về đáp án đúng của các phương án khác và KHÔNG trả về giải thích.
  2. [ ] Viết test fail: Kiểm tra khi `answer_visibility_policy` là `NEVER`, endpoint kết quả chỉ trả về tổng điểm, ẩn danh sách chi tiết câu hỏi.
  3. [ ] Viết test fail: Kiểm tra khi `answer_visibility_policy` là `IMMEDIATE` hoặc `FULL`, trả về đầy đủ đáp án đúng, phương án học viên chọn và giải thích.
  4. [ ] Cập nhật `attempt_service.py` để thực thi logic phân loại 3 mức trên và bảo đảm an toàn dữ liệu.
  5. [ ] Chạy `pytest tests/api/test_assessment_review_policy.py` xác nhận 100% tests PASS.

---

### Task 2: Frontend - Thêm Cấu hình Bài thi cho Giảng viên & Thiết kế lại Giao diện Xem lại của Học viên
**Mục tiêu:** Giảng viên có dropdown chọn chính sách xem lại; học viên xem bài thi thấy rõ nhãn Đúng/Sai/Thiếu trên từng phương án và xóa sạch cụm UI A/B/C/D cũ.
- **Files:**
  - Sửa đổi: `frontend/assets/js/views/instructor-exams.js` (Thêm mục chọn "Chính sách xem lại kết quả bài thi" trong trang Settings và Edit Studio).
  - Sửa đổi: `frontend/assets/js/views/student.js` (Cải tiến `renderExamResultPage`: highlight Đúng (xanh), Sai (đỏ), Thiếu (vàng/cam) trực tiếp lên phương án; xóa sạch hoàn toàn đoạn render `<!-- MC indicators [A][B][C][D] style matching mockup -->`).
- **Các bước thực hiện:**
  1. [ ] Thêm dropdown trong `instructor-exams.js`:
     - Tùy chọn 1: Xem đầy đủ (Đáp án đúng, câu đã chọn & giải thích học vụ)
     - Tùy chọn 2: Chỉ xem đúng/sai (Biết câu làm đúng hoặc sai, không hiển thị đáp án đúng)
     - Tùy chọn 3: Không cho xem chi tiết (Chỉ xem điểm tổng kết)
  2. [ ] Cập nhật logic render các phương án câu hỏi trong `student.js`:
     - Nếu học viên chọn và phương án đó đúng: Hiển thị viền xanh, icon checkmark xanh, nhãn "Đúng (Bạn đã chọn)".
     - Nếu học viên chọn và phương án đó sai: Hiển thị viền đỏ, icon chéo đỏ, nhãn "Sai (Bạn đã chọn)".
     - Nếu học viên không chọn nhưng phương án đó là đáp án đúng (trong chế độ Xem đầy đủ): Hiển thị viền nét đứt màu cam/vàng, nhãn "Đáp án đúng (Bị bỏ sót)".
     - Trong chế độ "Chỉ xem đúng/sai": Ẩn toàn bộ dấu vết của đáp án đúng, chỉ báo trạng thái câu hỏi đạt hay không.
  3. [ ] Xóa bỏ 100% block mã render thanh nút `[A] [B] [C] [D]` ở góc dưới card câu hỏi.
  4. [ ] Viết frontend test kiểm chứng việc loại bỏ cụm A/B/C/D và kiểm tra hiển thị nhãn Đúng/Sai/Thiếu.

---

### Task 3: Backend - Tái thiết kế 2 Mẫu PDF Xuất Bảng điểm (Bảng điểm Cá nhân & Bảng điểm Tổng hợp Lớp)
**Mục tiêu:** Nâng cấp `result_pdf_service.py` khớp hoàn hảo với 2 ảnh mẫu của người dùng.
- **Files:**
  - Sửa đổi: `src/pwd301/services/result_pdf_service.py`
  - Sửa đổi: `src/pwd301/blueprints/student/routes.py` (Bổ sung mapping text đáp án đã chọn thay vì UUID).
  - Sửa đổi: `src/pwd301/blueprints/instructor/routes.py` & `admin/routes.py` (Cung cấp dữ liệu chuẩn hóa cho bảng điểm tổng hợp).
  - Test: `tests/test_admin_diff_and_gradebook_pdf.py`
- **Các bước thực hiện:**
  1. [ ] Xây dựng hàm định dạng điểm học vụ `_format_score_human(val)`:
     - Số chẵn: `100.0` $\rightarrow$ `"100"`, `0.0` $\rightarrow$ `"0"`, `50.0` $\rightarrow$ `"50"`.
     - Số thập phân: `50.5` $\rightarrow$ `"50.5"`, `33.3333` $\rightarrow$ `"33.33"`, `7.25` $\rightarrow$ `"7.25"`.
  2. [ ] **Mẫu 1 - PDF Bảng điểm Cá nhân (ảnh 2)**:
     - Cột "Đáp án đã chọn": Trích xuất nội dung văn bản (hoặc text/label) của lựa chọn học viên đã chọn, thay vì in chuỗi UUID `56a7d14f-7102-4ec4-...`.
     - Áp dụng `_format_score_human` cho Tổng điểm đạt được và Điểm chi tiết từng câu.
  3. [ ] **Mẫu 2 - PDF Bảng điểm Tổng hợp Lớp (ảnh 3)**:
     - Ô Khóa học: Chỉ hiển thị tên khóa học thuần túy (loại bỏ mã `#50028` hoặc tiền tố mã môn bị lặp).
     - Ô Bài kiểm tra: Chỉ ghi loại kiểm tra và tên bài kiểm tra (bỏ chuỗi UUID phía sau).
     - Tiêu chuẩn khảo thí: Luôn ghi cố định là `"Có giám sát nâng cao"`.
     - Dòng chữ ký đổi thành: `"Thành phố Hồ Chí Minh, ngày ... tháng ... năm ..."`.
     - Cột Mã SV trong bảng: Hiển thị mã sinh viên thực tế (`student_code` hoặc username), không in chuỗi UUID dài.
     - Áp dụng `_format_score_human` cho toàn bộ các điểm số trong bảng thống kê và danh sách thí sinh.
  4. [ ] Chạy test `pytest tests/test_admin_diff_and_gradebook_pdf.py` xác nhận PDF sinh ra chuẩn xác và không lỗi font tiếng Việt.

---

### Task 4: Frontend & Backend - Giao diện Xem trước Chuẩn 2 Cột Giảng viên & Admin (Course Tree Preview)
**Mục tiêu:** Thay thế thanh pills ngang bằng giao diện 2 cột chuẩn Student Lesson Reader.
- **Files:**
  - Sửa đổi: `frontend/assets/js/views/admin.js` (Tái cấu trúc tab "Xem trước" trong trang Thẩm định yêu cầu thay đổi).
  - Sửa đổi: `frontend/assets/js/views/instructor.js` (Tích hợp modal/view xem trước bài học cho Giảng viên).
- **Các bước thực hiện:**
  1. [ ] Xây dựng component Cây thư mục giáo trình (Sidebar Curriculum Tree) bên trái: Liệt kê các Chương mục (Learning Units) và các Bài học con bên trong kèm biểu tượng loại bài học (Video, Văn bản, Quiz).
  2. [ ] Bên phải: Khung hiển thị nội dung bài học đang chọn (Video player, Tiêu đề, Tóm tắt, Nội dung Markdown, Tài liệu đính kèm, Quiz tương tác làm thử).
  3. [ ] Hỗ trợ click chuyển bài học tức thì từ Cây thư mục sang Khung nội dung mà không cần reload trang.
  4. [ ] Chế độ Preview không áp đặt ràng buộc thời gian xem tối thiểu hay nhịp tim để Giảng viên/Admin thẩm định nhanh chóng.

---

### Task 5: Backend & Frontend - Khắc phục Triệt để Lỗi Phát Video Tải lên (Uploaded Video Streaming)
**Mục tiêu:** Cho phép phát mượt mà mọi video mp4/webm đã tải lên từ máy tính cho Giảng viên và Admin.
- **Files:**
  - Sửa đổi: `src/pwd301/blueprints/api_files/routes.py` (Bổ sung endpoint `/api/files/<asset_id>/stream` hoặc cấp quyền xem trước inline có hỗ trợ HTTP Range headers `206 Partial Content`).
  - Sửa đổi: `src/pwd301/blueprints/admin/routes.py` (Cấp quyền preview video cho Admin reviewer).
  - Sửa đổi: `frontend/assets/js/views/admin.js` (Trỏ URL video upload sang endpoint stream preview có xác thực).
  - Test: `tests/api/test_video_preview_stream.py`
- **Các bước thực hiện:**
  1. [ ] Viết test fail: Yêu cầu GET `/api/files/<asset_id>/stream` với quyền Admin/Instructor trả về video với HTTP header `Accept-Ranges: bytes` và `Content-Type: video/mp4`.
  2. [ ] Triển khai handler streaming hỗ trợ byte range để trình duyệt có thể tua (seek) video trực tiếp trên thẻ `<video>`.
  3. [ ] Cập nhật frontend để sử dụng endpoint stream này cho video upload trong tab xem trước.
  4. [ ] Chạy test xác nhận video phát mượt mà và không bị ném 403 Forbidden.

---

### Task 6: Backend & Frontend - Sửa Triệt để Lỗi Xét duyệt Khóa học & Thay đổi (Fix 500 Approval Errors)
**Mục tiêu:** Chấm dứt 7 lỗi 500 khi mở trang review ID và đảm bảo nút Phê duyệt / Từ chối hoạt động 100%.
- **Files:**
  - Sửa đổi: `src/pwd301/blueprints/admin/routes.py` (`admin_review_change_request`, `get_course_changeset_diff_route`, `review_course`).
  - Sửa đổi: `src/pwd301/services/lesson_service.py` & `course_service.py`.
  - Sửa đổi: `frontend/assets/js/views/admin.js` (Bảo đảm gọi đúng tham số API và bắt lỗi an toàn).
  - Test: `tests/api/test_admin_change_requests_review.py`
- **Các bước thực hiện:**
  1. [ ] Viết integration test tái hiện lỗi 500 khi mở review ID và khi phê duyệt các loại change request khác nhau (thay đổi bài học, thay đổi tài liệu đính kèm, cập nhật giáo trình).
  2. [ ] Sửa lỗi crash trong `get_course_changeset_diff` khi change request thuộc loại đơn lẻ (không phải changeset đầy đủ).
  3. [ ] Sửa lỗi crash trong `admin_review_change_request` khi cập nhật tài liệu hoặc khi duyệt khóa học từ trạng thái `SUBMITTED_FOR_REVIEW` $\rightarrow$ `APPROVED`.
  4. [ ] Chạy `pytest tests/api/test_admin_change_requests_review.py` chứng minh toàn bộ các luồng phê duyệt và từ chối chạy thành công 100%.

---

### Task 7: Kiểm thử Tổng thể Toàn diện (End-to-End Verification & Verification Report)
**Mục tiêu:** Chạy trọn bộ suite kiểm thử và kiểm tra thực nghiệm trước khi công bố hoàn thành.
- **Commands:**
  - `pytest tests/api/test_assessment_review_policy.py tests/test_admin_diff_and_gradebook_pdf.py tests/api/test_video_preview_stream.py tests/api/test_admin_change_requests_review.py`
  - `npm test` hoặc các frontend test suites liên quan.
  - `./scripts/verify.ps1`
- **Báo cáo:** Xuất báo cáo hoàn thành theo chuẩn contract, có bằng chứng thực tế từ terminal.
