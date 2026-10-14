# BUG TRACKER — PWD301 LMS
## Nhật ký Quản lý & Theo dõi Lỗi qua 6 Vòng Triển khai

| Bug ID | Mức độ | Hạng mục | Requirement | Tiêu đề lỗi / Hiện tượng | Môi trường | Trạng thái | Vòng phát hiện | Vòng khắc phục | File liên quan |
|---|---|---|---|---|---|---|---|---|---|
| **BUG-01** | P1 | HM1: Video | REQ-05 | VideoArmor báo động sai `DOM_TAMPER` khi resize hoặc đổi tab | Frontend / Browser | **RESOLVED** | Vòng 2 | Vòng 3 | `frontend/assets/js/components/video-armor.js` |
| **BUG-02** | P1 | HM4: Nav | REQ-17 | Nút "Quay lại" bị khóa cứng hoặc không chuyển về bài trước | Frontend / Student UI | **RESOLVED** | Vòng 2 | Vòng 3 | `frontend/assets/js/views/student.js` |
| **BUG-03** | P1 | HM4: Nav | REQ-18 | Bài 1 đã học xong khi quay lại bị khóa nút "Tiếp theo" | Frontend / State Sync | **RESOLVED** | Vòng 2 | Vòng 3 | `frontend/assets/js/views/student.js` |
| **BUG-04** | P0 | HM5: Final | REQ-21, REQ-22 | Final Exam mở cổng cho thi ở trang "Bài kiểm tra" dù chưa hoàn thành bài học | Fullstack / API & UI | **RESOLVED** | Vòng 2 | Vòng 3 | `src/pwd301/services/attempt_service.py`, `src/pwd301/blueprints/student/routes.py`, `frontend/assets/js/views/student.js` |
| **BUG-05** | P1 | HM2: PDF | REQ-06 | Công thức toán LaTeX xuất hiện ký tự rác hoặc raw `$` trong file PDF ReportLab | Backend / ReportLab | **RESOLVED** | Vòng 2 | Vòng 3 | `src/pwd301/services/result_pdf_service.py` |
| **BUG-06** | P1 | HM2: PDF | REQ-09 | Điểm số và đáp án vẫn lộ trong PDF và API khi giảng viên tắt quyền xem kết quả | Fullstack / Security | **RESOLVED** | Vòng 2 | Vòng 3 | `src/pwd301/services/attempt_service.py`, `src/pwd301/services/result_pdf_service.py`, `frontend/assets/js/views/student.js` |
| **BUG-07** | P2 | HM1: Video | REQ-02 | Incompatible return type annotation `tuple[Response, int] | Response` trong `download_file_api` | Backend / Mypy Typecheck | **RESOLVED** | Vòng 4 | Vòng 5 | `src/pwd301/blueprints/api_files/routes.py` |
| **BUG-08** | P2 | HM5: Final | REQ-21 | Thiếu `from sqlalchemy import func` và đặt tên biến mơ hồ `l` trong student routes | Backend / Ruff & SQLAlchemy | **RESOLVED** | Vòng 4 | Vòng 5 | `src/pwd301/blueprints/student/routes.py`, `src/pwd301/services/attempt_service.py` |
| **BUG-09** | P3 | HM3: UI | REQ-11 | Xung đột CSS class `teal` ghi đè màu xanh lá / đỏ trong xem trước câu hỏi tương tác | Frontend / CSS | **RESOLVED** | Vòng 2 | Vòng 3 | `frontend/assets/js/views/instructor-exams.js` |

---

### Chi tiết Phân tích Nguyên nhân Gốc & Giải pháp Khắc phục

#### BUG-01: VideoArmor báo động sai `DOM_TAMPER` khi resize hoặc đổi tab
- **Mô tả**: Khi người dùng thay đổi kích thước cửa sổ hoặc chuyển tab trình duyệt, `MutationObserver` gắn trên `document.body` phát hiện thay đổi class/style toàn cục và ngắt video học viên.
- **Root Cause**: Scope giám sát của MutationObserver quá rộng (bao trùm toàn trang thay vì chỉ player container).
- **Giải pháp**: Thu hẹp đối tượng quan sát vào `this.container` và thêm điều kiện bảo vệ `this.container.isConnected`.
- **Xác minh**: Thử nghiệm resize cửa sổ và chuyển tab trong browser; video tiếp tục phát bình thường, không xuất hiện popup vi phạm giả.

#### BUG-02: Nút "Quay lại" bị khóa khi điều hướng lùi
- **Mô tả**: Đã học qua Bài 2 nhưng khi bấm "Quay lại" Bài 1 thì hệ thống ngăn chặn hoặc hiển thị trạng thái khóa.
- **Root Cause**: Hàm điều hướng `_ciscoSelectItem` áp đặt logic `target.isUnlocked` cơ học mà không kiểm tra thứ tự bài học.
- **Giải pháp**: Bổ sung `isGoingBack = curIdx !== -1 && targetIdx !== -1 && targetIdx < curIdx;`. Nếu là di chuyển lùi thì luôn cho phép chuyển bài.
- **Xác minh**: Thao tác chuyển từ Bài 2 về Bài 1, từ Bài 3 về Bài 2 diễn ra trơn tru.

#### BUG-03: Bài 1 đã hoàn thành bị khóa lại nút "Tiếp theo" khi quay lại xem
- **Mô tả**: Sinh viên đã hoàn thành Bài 1, tiến sang Bài 2, rồi quay lại Bài 1 thì nút "Tiếp theo" chuyển sang màu xám và yêu cầu học lại.
- **Root Cause**: `renderActiveContent` chỉ đọc `lesson.progress.is_completed`. Nếu network chưa đồng bộ xong hoặc session cache chưa tải kịp, `is_completed` bị gán `false`, kích hoạt lại dwell timer từ đầu.
- **Giải pháp**: Đánh giá `isCompleted` qua bộ nhớ cache cục bộ `cachedLes.is_completed` và `activeItem.isCompleted`. Một khi đã hoàn thành thì trạng thái mở khóa xanh lá được bảo toàn vĩnh viễn.
- **Xác minh**: Kiểm thử quay lại Bài 1 sau khi học xong; nút "Tiếp theo" giữ nguyên màu xanh `bg-emerald-600` và cho phép bấm ngay lập tức.

#### BUG-04: Final Exam không có phòng thủ ở trang "Bài kiểm tra" và API
- **Mô tả**: Sinh viên truy cập trực tiếp trang danh sách bài thi hoặc gọi API `start_assessment_attempt` có thể vào thi Final Exam mà không cần học bài nào.
- **Root Cause**: Logic kiểm tra tiên quyết bị bỏ sót ở route `/assessments` và controller tạo lượt thi của backend.
- **Giải pháp**: Thêm barrier kiểm tra 100% bài học `PUBLISHED` hoàn thành trong `start_assessment_attempt` (trả `AttemptValidationError 403`), đồng thời tính toán `is_locked` và `lock_reason` trả về cho Frontend trang "Bài kiểm tra" để vô hiệu hóa nút "Vào thi" (màu xám disabled).
- **Xác minh**: `tests/test_6_categories_verification.py::test_final_exam_requires_all_lessons_completed` PASS.

#### BUG-05: Ký tự rác và raw LaTeX trong kết quả PDF
- **Mô tả**: Các công thức toán như $x^2$, $\frac{a}{b}$, $\sqrt{x}$ hiển thị nguyên văn dạng code thô hoặc lỗi ký tự trong file PDF xuất ra.
- **Root Cause**: Thiếu bộ parser chuyển đổi ký hiệu toán học sang thẻ XML định dạng của ReportLab.
- **Giải pháp**: Viết hàm `_render_math_and_plain` duyệt ngoặc cân bằng (balanced braces), chuyển đổi các lệnh LaTeX phổ biến sang `<sup>`, `<sub>`, căn bậc hai `√`, tích phân `∫`, phân số `(a)/(b)`.
- **Xác minh**: `tests/test_6_categories_verification.py::test_latex_math_clean_rendering` PASS; `tests/test_result_pdf_formatting.py` 10/10 PASS.

#### BUG-06: Lộ điểm số và đáp án khi tắt quyền xem kết quả
- **Mô tả**: Cấu hình `allow_student_view_results = False` nhưng sinh viên vẫn xem được đáp án qua API và PDF.
- **Root Cause**: Backend trả về nguyên vẹn `AttemptQuestion` và điểm số mà không lọc theo vai trò người dùng.
- **Giải pháp**: Tại `get_attempt_result_for_student`, gán `score_status = "RESULTS_HIDDEN"`, ẩn toàn bộ điểm và đáp án. Trong PDF, đặt 3 cột thành `-` và hiển thị badge `ĐÃ GHI NHẬN BÀI NỘP`.
- **Xác minh**: `tests/test_6_categories_verification.py::test_pdf_with_allow_student_view_results_false` PASS.

#### BUG-07: Incompatible return type trong download_file_api
- **Mô tả**: Mypy báo lỗi `Incompatible return value type (got "tuple[Response, int]", expected "Response")`.
- **Root Cause**: Định nghĩa hàm route trả về `Response` nhưng nhánh kiểm tra email trả về `jsonify(...), 403`.
- **Giải pháp**: Cập nhật type annotation thành `def download_file_api(...) -> tuple[Response, int] | Response:`.
- **Xác minh**: Mypy kiểm tra `src/pwd301/blueprints/api_files/routes.py` không còn lỗi nào (`Success: no issues found`).

#### BUG-08: Undefined `func` và ambiguous variable `l`
- **Mô tả**: Ruff báo lỗi `F821 Undefined name func` và `E741 Ambiguous variable name: l`.
- **Root Cause**: Thiếu import `from sqlalchemy import func` trong `student/routes.py` và dùng biến 1 chữ cái `l`.
- **Giải pháp**: Bổ sung import chuẩn và đổi biến thành `les`.
- **Xác minh**: Ruff linter và formatter kiểm tra toàn bộ file modified đạt 100% PASS.
