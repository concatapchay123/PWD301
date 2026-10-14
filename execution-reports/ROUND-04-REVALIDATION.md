# VÒNG 4: TÁI KIỂM TOÁN ĐỘC LẬP & TÁI XÁC MINH (REVALIDATION)
## Dự án PWD301 LMS — Nâng cấp Toàn diện 6 Hạng mục

---

### 1. Mục tiêu Vòng 4
Thực hiện một chu trình kiểm toán độc lập lần thứ hai với độ khắt khe cao hơn Vòng 2 nhằm kiểm chứng xem các bản sửa lỗi ở Vòng 3 đã thực sự giải quyết triệt để vấn đề hay chưa, đồng thời sử dụng các công cụ phân tích tĩnh nghiêm ngặt (Ruff, Mypy) để tìm kiếm lỗi mới phát sinh từ bản sửa lỗi.

---

### 2. Các Hoạt động Tái Kiểm toán Thực hiện

#### A. Kiểm chứng Lại Từng Bug của Vòng 2
1. **Kiểm chứng BUG-01 (VideoArmor)**:
   - Thao tác: Chuyển đổi tab trình duyệt 10 lần liên tục, thu nhỏ và phóng to cửa sổ trình duyệt khi đang phát video.
   - Kết quả: Video tiếp tục phát bình thường, không xuất hiện popup cảnh báo sai `DOM_TAMPER`. -> **PASS (ĐÃ GIẢI QUYẾT)**.
2. **Kiểm chứng BUG-02 & BUG-03 (Điều hướng bài học)**:
   - Thao tác: Học hoàn thành Bài 1 (30s đọc) -> Chuyển sang Bài 2 -> Bấm "Quay lại" Bài 1 -> Bấm "Tiếp theo" để sang lại Bài 2.
   - Kết quả: Nút "Quay lại" luôn hoạt động trơn tru; khi về lại Bài 1, nút "Tiếp theo" giữ nguyên màu xanh `bg-emerald-600` và cho phép chuyển tiếp tức thì. -> **PASS (ĐÃ GIẢI QUYẾT)**.
3. **Kiểm chứng BUG-04 (Bảo vệ Final Exam)**:
   - Thao tác: Học sinh mới ghi danh khóa học (chưa học bài nào) mở trang "Bài kiểm tra" và thử bấm "Vào thi" của Final Exam.
   - Kết quả: Nút "Vào thi" bị vô hiệu hóa với màu xám `cursor-not-allowed`, tooltip hiển thị số bài học cần hoàn thành. Khi dùng script gọi trực tiếp API `start_assessment_attempt`, hệ thống trả về HTTP 403 `AttemptValidationError`. -> **PASS (ĐÃ GIẢI QUYẾT)**.
4. **Kiểm chứng BUG-05 & BUG-06 (PDF LaTeX & Kết quả)**:
   - Thao tác: Tạo bài thi chứa công thức toán $x^2 + y_1$, $\frac{a+b}{c}$, $\sqrt{16}$, nộp bài với cấu hình `allow_student_view_results = False`, tải tệp PDF kết quả.
   - Kết quả: Các công thức toán hiển thị sắc nét; điểm số và đáp án của học sinh được thay thế bằng `-`, thẻ tổng điểm hiển thị badge `ĐÃ GHI NHẬN BÀI NỘP`. -> **PASS (ĐÃ GIẢI QUYẾT)**.

#### B. Kiểm tra Tĩnh Bằng Công cụ Tự động & Phát hiện Bug Mới
Trong quá trình chạy Ruff và Mypy rà soát toàn bộ các tệp mã nguồn vừa sửa đổi:
- **Phát hiện Lỗi BUG-07 (Mức độ P2 - Mypy Typecheck)**:
  - Lệnh: `.\.venv\Scripts\python.exe -m mypy src/pwd301/blueprints/api_files/routes.py`
  - Hiện tượng: Mypy báo lỗi `Incompatible return value type (got "tuple[Response, int]", expected "Response")` tại hàm `download_file_api`.
  - Nguyên nhân: Route streaming được khai báo kiểu trả về là `Response`, nhưng nhánh chặn xác thực email trả về `jsonify(...), 403`.
- **Phát hiện Lỗi BUG-08 (Mức độ P2 - Ruff Linter)**:
  - Lệnh: `.\.venv\Scripts\python.exe -m ruff check src/pwd301/blueprints/student/routes.py`
  - Hiện tượng: Ruff báo lỗi `F821 Undefined name func` do thiếu import `from sqlalchemy import func`, và lỗi `E741 Ambiguous variable name: l` do dùng biến 1 ký tự `l`.

---

### 3. Đánh giá Mức độ Sẵn sàng sau Vòng 4
- Các lỗi nghiệp vụ và UI/UX chính từ Vòng 2 đã được khắc phục hoàn toàn.
- Phát hiện thêm 2 lỗi kỹ thuật phát sinh (BUG-07, BUG-08) về chuẩn kiểu dữ liệu và cú pháp linter.
- Chuyển ngay sang **Vòng 5: Final Fixing + Hardening + Completeness** để xử lý dứt điểm 2 lỗi này.
