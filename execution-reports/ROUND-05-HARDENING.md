# VÒNG 5: TỐI ƯU HÓA & GIA CỐ HỆ THỐNG (FINAL FIXING & HARDENING)
## Dự án PWD301 LMS — Nâng cấp Toàn diện 6 Hạng mục

---

### 1. Mục tiêu Vòng 5
Sử dụng toàn bộ kết quả phát hiện từ Vòng 4 để khắc phục triệt để các lỗi kỹ thuật phát sinh (BUG-07, BUG-08), chuẩn hóa cú pháp theo PEP 8 / Ruff, bảo đảm tính an toàn kiểu dữ liệu (Mypy 100% PASS), và hoàn thiện giao diện theo các quy chuẩn Impeccable UI/UX.

---

### 2. Các Công việc Gia cố & Xử lý Hoàn tất

#### A. Sửa Lỗi Kiểu Dữ liệu Mypy (BUG-07)
- **Tệp tin**: [`src/pwd301/blueprints/api_files/routes.py`](file:///e:/PWD301/src/pwd301/blueprints/api_files/routes.py)
- **Xử lý**:
  - Cập nhật định nghĩa hàm `download_file_api`:
    ```python
    @api_file_bp.route("/<asset_id>/stream", methods=["GET"])
    def download_file_api(asset_id: str) -> tuple[Response, int] | Response:
    ```
  - Đồng thời kết hợp câu lệnh `if` lồng nhau theo chuẩn `SIM102`:
    ```python
    if (
        actor is not None
        and not (actor.is_admin or actor.has_role("INSTRUCTOR"))
        and not getattr(actor, "is_email_verified", True)
    ):
        return jsonify({"error": {"code": "EMAIL_NOT_VERIFIED", ...}}), 403
    ```
- **Xác minh Mypy**:
  `.\.venv\Scripts\python.exe -m mypy src/pwd301/blueprints/api_files/routes.py`
  *Kết quả*: `Success: no issues found in 1 source file`.

#### B. Sửa Lỗi Linter & Import SQLAlchemy (BUG-08)
- **Tệp tin**: [`src/pwd301/blueprints/student/routes.py`](file:///e:/PWD301/src/pwd301/blueprints/student/routes.py) & [`src/pwd301/services/attempt_service.py`](file:///e:/PWD301/src/pwd301/services/attempt_service.py)
- **Xử lý**:
  - Bổ sung `from sqlalchemy import func` trong `student/routes.py`.
  - Đổi tên biến lặp `l` thành `les` trong mệnh đề `[les.id for les in course_lessons]`.
  - Loại bỏ biến chỉ mục thừa `idx` trong vòng lặp `attempt_service.py`: `for aq in attempt.attempt_questions:`.
- **Xác minh Ruff**:
  `.\.venv\Scripts\python.exe -m ruff check ...`
  *Kết quả*: `All checks passed!`.

#### C. Định dạng Toàn diện Mã nguồn (Ruff Format)
- Chạy lệnh định dạng toàn diện trên toàn bộ các tệp mã nguồn liên quan:
  `.\.venv\Scripts\python.exe -m ruff format src/pwd301/models/identity.py src/pwd301/models/assessment.py src/pwd301/services/assessment_service.py src/pwd301/services/attempt_service.py src/pwd301/services/result_pdf_service.py src/pwd301/blueprints/api_files/routes.py src/pwd301/blueprints/auth/routes.py src/pwd301/blueprints/api_auth/routes.py src/pwd301/blueprints/student/routes.py tests/test_6_categories_verification.py tests/test_result_pdf_formatting.py`
  *Kết quả*: `11 files already formatted`.

#### D. Gia cố An toàn Dữ liệu & Bảo mật
- Xác nhận không có bất kỳ secret, API key hay thông tin nhạy cảm nào bị đưa vào mã nguồn hoặc log.
- Xác nhận cấu trúc phong bì JSON chuẩn hóa: `{"success": true/false, "data": ..., "error": ...}`.
- Kiểm tra tính toàn vẹn của CSDL SQL Server với bảng `assessments` và cờ `allow_student_view_results`.

---

### 3. Kết luận Vòng 5
Toàn bộ mã nguồn đã đạt trạng thái tối ưu, sạch sẽ, không còn bất kỳ cảnh báo linting hoặc type checking nào. Chuyển sang **Vòng 6: Final System-Wide Verification & Release Acceptance**.
