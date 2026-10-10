# Làm lại hai mẫu PDF kết quả thi — 10/10/2026

## A. Phạm vi và nguồn đối chiếu

Chỉnh bộ xuất PDF cho học viên và bảng điểm toàn bài thi của giảng viên theo hai PNG người dùng cung cấp trong Downloads. Đã đọc CURRENT.md, README.md, Coding Agent Start Here, Business Rule Catalog, Non-Negotiable Invariants và business/08_ASSESSMENT_ENGINE.md. Giữ hợp đồng TASK-090: tiếng Việt Unicode, đáp án được phép xem dạng chữ, không in UUID thô, điểm tối đa hai số lẻ, địa điểm Thành phố Hồ Chí Minh và tiêu chuẩn Có giám sát nâng cao.

## B. Quyết định tái sử dụng

Dùng ReportLab, font Unicode và hai hàm build PDF hiện có. Tái sử dụng toàn bộ nguồn dữ liệu, giải mã đáp án, phân quyền và endpoint tải. Không thêm dependency, HTML template, frontend hay migration.

## C. Thay đổi từng file

- `src/pwd301/services/result_pdf_service.py`: bố cục A4, biểu tượng vector, huy hiệu sách/vòng nguyệt quế, dải tiêu đề, thẻ thống kê có màu, hai panel thông tin giảng viên, bảng chi tiết, chữ ký, khung ghi chú và chân trang xanh. Nội dung dài căn trên để tránh ReportLab lặp tiêu đề và tạo vùng bảng rỗng khi tách hàng.
- `tests/test_pdf_reference_layout.py`: kiểm tra các phần hiển thị, bản ngắn một trang, transcript hai câu hỏi, 90 học viên không mất hàng, tiêu đề lặp đúng trang và câu hỏi rất dài không tạo trang bảng rỗng.
- `output/pdf/student-result-preview.pdf` và `output/pdf/instructor-gradebook-preview.pdf`: bản minh họa từ dữ liệu kiểm thử, xuất bằng font DejaVu trong container web Linux thực tế; không phải kết quả thi thực tế được lấy từ SQL Server.

## D. Xóa và đơn giản hóa

SIMPLIFY NOW: thay bảng thống kê liền khối bằng helper thẻ dùng chung cho hai PDF; xóa cấu hình màu/viền huy hiệu không còn sử dụng. KEEP: escape nội dung không tin cậy, font Unicode fail-closed, trạng thái điểm chưa công bố, phân trang danh sách đầy đủ và quyền tải PDF.

## E. Ponytail

Không thêm nợ kỹ thuật hoặc tầng kiến trúc dự phòng.

## F. Xác minh thực chạy

- TDD: thấy kiểm thử thiếu section fail trước sửa; thấy hai kiểm thử lỗi phân trang fail trước khi đổi căn trên; chạy lại đạt sau sửa.
- 41 test đạt trên SQLite trong bộ nhớ: `tests/test_pdf_reference_layout.py`, `tests/test_result_pdf_formatting.py`, `tests/test_admin_diff_and_gradebook_pdf.py`, `tests/api/test_student_backend_completion.py`, `tests/api/test_assessment_review_policy.py`; không có skipped. Output lần cuối lưu ở `output/pdf/verification-tests.txt`.
- Ruff check và Ruff format check cho hai file Python thay đổi: đạt.
- Mypy bộ xuất PDF với `--follow-imports=silent`: đạt; có note cấu hình module không dùng, không có lỗi kiểu.
- `scripts/repo_check.py` và git diff whitespace check cho bộ xuất PDF: đạt.
- Poppler render và xem ảnh: hai bản minh họa một trang; câu hỏi/đáp án rất dài ba trang; 90 học viên năm trang. Đã xem các trang dưới dạng ảnh/contact sheet; không thấy cắt chữ, chồng nội dung, tiêu đề lặp sai hoặc bảng rỗng.
- Xuất lại hai mẫu bằng runtime Linux trong `pwd301_web`: phát hiện font DejaVu rộng hơn Arial khiến ghi chú rơi trang hai. Giảm phần đệm và khoảng cách dư, kiểm tra lại: bản học viên hai câu hỏi và bản giảng viên đều một trang, đã render và xem ảnh cuối.
- Nạp lại Gunicorn bằng HUP trong container web có bind mount `E:/PWD301/src`. Bốn worker mới đã khởi động và bốn worker cũ đã thoát; HTTP `/health` trả 200 sau nạp lại. Không restart container SQL Server hoặc thay dữ liệu.
- Open Code Review delegate: lấy preview và rules Python bằng OCR, host tự rà soát bộ xuất PDF cùng test. Không phát hiện lỗi blocking còn tồn tại trong thay đổi này. Không phải review của mô hình độc lập.
- Đã chạy thử full backend pytest, chủ động ngắt khi tiến trình đến khoảng 23% để kết thúc xác minh theo phạm vi PDF. Không có summary cuối: **không tính full suite là đạt**. Full suite khởi chạy trước các chỉnh typography/phân trang cuối; 41 test liên quan đã chạy lại với code cuối.

## G. Giới hạn

Chưa kiểm tra lại thao tác bấm tải trong phiên trình duyệt thực tế của người dùng; đã kiểm tra endpoint bằng Flask test client. Không chạy SQL Server, migration, full frontend suite hoặc full verifier cho thay đổi trình bày PDF này. Hình đồ họa được dựng vector theo mẫu; không phải bản sao pixel của PNG. Các điều chỉnh nội dung bắt buộc của TASK-090 có ưu tiên hơn những UUID và địa danh cũ trong hình mẫu.
