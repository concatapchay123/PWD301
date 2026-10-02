# BÁO CÁO AUDIT & KHẮC PHỤC TOÀN DIỆN: HỆ THỐNG GIÁM SÁT KHẢO THÍ & PHÒNG CHỜ THI TRỰC TUYẾN (PWD301)

- **Mã tài liệu**: `AUDIT-04-EXAM-PROCTORING-OVERHAUL`
- **Phiên bản**: `1.0.0 (Release-Ready)`
- **Ngày hoàn thành**: 02/10/2026
- **Trạng thái**: **ĐÃ KHẮC PHỤC HOÀN TOÀN (100% PASS)**
- **Phạm vi tác động**: Role Student & Role Instructor (Backend Services, CSDL MSSQL, Pure Headless REST API, Frontend Single Page Application).

---

## I. TỔNG QUAN YÊU CẦU & BỐI CẢNH
Hệ thống khảo thí PWD301 được yêu cầu bảo đảm tính công bằng, nghiêm túc và an toàn học vụ tuyệt đối. Yêu cầu của Chủ dự án:
1. **Khảo thí mặc định 100% được giám sát**: Mọi bài kiểm tra sinh viên tham gia bắt buộc phải kích hoạt chế độ toàn màn hình, đếm số lần rời màn hình, đo đếm chính xác thời gian vắng mặt (giây), và ngăn chặn mọi hành vi gian lận (chuột phải, copy/cut đề thi, phím tắt F12/DevTools).
2. **Quy chế Giảng viên**: Thay đổi từ cấu hình tùy chọn (cho phép bật/tắt) sang **Mặc định Luôn luôn Bật 100% (Khóa cố định)**; tuy nhiên phải có bảng hiển thị trang trọng, chi tiết trong Soạn đề thi (Exam Studio) để giảng viên nắm rõ các cơ chế an toàn đang bảo vệ bài thi.
3. **Tái thiết kế Toàn diện Phòng chờ Thi (Waiting Room)**: Thay thế giao diện đơn điệu cũ bằng Phòng chờ thi khảo thí thực thụ chuẩn Impeccable Design:
   - Thẻ Định danh Thí sinh (Candidate Identity Card).
   - 4 Thẻ Chỉ số Khảo thí cốt lõi.
   - Bảng Quy chế Giám sát Khảo thí Chính thức.
   - Kiểm tra Tự động Điều kiện Thiết bị (Pre-Exam System Readiness Checklist: mạng, Fullscreen API, cảm biến tab, độ phân giải màn hình).
   - Cam kết Trung thực Khảo thí (Honor Code Pledge Checkbox) buộc phải tích chọn mới được vào thi.
   - Kích hoạt Toàn màn hình ngay trong cử chỉ click của thí sinh.

---

## II. MA TRẬN LỖ HỔNG AUDIT ĐƯỢC (ROOT CAUSE ANALYSIS)

| STT | Vị trí Tệp tin | Loại Lỗ hổng | Mô tả Hiện trạng Gốc | Hậu quả Nghiêm trọng |
|---|---|---|---|---|
| 1 | `src/pwd301/models/assessment.py` | CSDL / Model | `monitoring_enabled = False`, `request_fullscreen = False` | Các đề thi tạo mới mặc định không bật giám sát, cho phép sinh viên thoát tab tự do. |
| 2 | `src/pwd301/services/assessment_service.py` | Nghiệp vụ Server | `_exam_policy_bool` fallback về `False` | Payload tạo bài thi nếu không gửi cờ thì server tắt hoàn toàn chế độ giám sát. |
| 3 | `src/pwd301/services/attempt_service.py` | Nghiệp vụ Server | `record_attempt_focus_event` ném lỗi HTTP 400 nếu `not monitoring_enabled` | Frontend gửi sự kiện thí sinh rời tab thì backend từ chối, gây lỗi ứng dụng và mất dấu vết. |
| 4 | `src/pwd301/services/attempt_service.py` | Thống kê Biên bản | `get_instructor_attempt_focus_events` thiếu `total_away_seconds` | Giảng viên chỉ thấy số lần rời tab, không biết sinh viên rời đi 2 giây hay 15 phút. |
| 5 | `src/pwd301/blueprints/student/routes.py` | REST API | `assessment_detail_view` thiếu thông tin thí sinh & proctoring config | Phòng chờ thi không hiển thị được danh tính thí sinh và cấu hình giám sát. |
| 6 | `frontend/assets/js/views/instructor-exams.js` | UI Giảng viên | Dùng checkbox tùy chọn có thể bị tắt | Giảng viên vô tình bỏ tích khiến bài thi mất toàn bộ cơ chế bảo vệ. |
| 7 | `frontend/assets/js/ui.js` | Frontend Utility | `ExamAntiCheatManager` chỉ đếm số lần, không tính thời gian | Không đo được thời gian vắng mặt; không có bộ chặn chuột phải, copy/cut, phím tắt F12. |
| 8 | `frontend/assets/js/views/student.js` | UI Phòng chờ | `renderWaitingRoom` quá đơn giản, sơ sài | Không có thẻ thí sinh, không kiểm tra thiết bị, không cam kết trung thực, không tự động fullscreen. |
| 9 | `frontend/assets/js/views/student.js` | UI Bàn thi | `renderAttemptConsole` thiếu màn hình khóa khẩn cấp | Khi thoát fullscreen, không có màn hình khóa cảnh báo thí sinh quay lại chế độ thi. |

---

## III. GIẢI PHÁP & THỰC THI CHI TIẾT

### 1. Backend & Cơ sở dữ liệu CSDL
- **Model `Assessment`**: Cập nhật giá trị mặc định của `monitoring_enabled` và `request_fullscreen` thành `True` (`server_default=sa.text("1")`).
- **Nghiệp vụ Tạo & Cập nhật**: `_exam_policy_bool` đặt mặc định `True` cho cả `monitoring_enabled` và `request_fullscreen`.
- **Ghi nhận Sự kiện Tập trung (Focus Events)**: `record_attempt_focus_event` tự động bảo đảm `monitoring_enabled = True` cho bài thi; chấp nhận đầy đủ các sự kiện `TAB_HIDDEN`, `WINDOW_BLUR`, `FULLSCREEN_EXIT`.
- **Biên bản Vi phạm Giảng viên**: `get_instructor_attempt_focus_events` tính toán chính xác `total_away_seconds` từ các cặp sự kiện START/END và trả về trực tiếp trong phong bì JSON.
- **Dữ liệu Giao bài**: `get_attempt_delivery` bảo đảm trả về `monitoring_enabled: True` và `request_fullscreen: True`.

### 2. Frontend Giảng viên: Bảng Điều Khiển Giám Sát Khảo Thí
- Loại bỏ hoàn toàn các checkbox bật/tắt tùy chọn.
- Bổ sung **Bảng Điều Khiển Giám Sát Khảo Thí Mặc Định 100% (Proctoring Policy Banner)** tại Bước 4 Soạn đề thi và Modal Chỉnh sửa:
  - Huy hiệu: `[MẶC ĐỊNH BẬT 100% - KHÔNG THỂ TẮT]`.
  - Hiển thị 4 quy tắc: Chế độ Toàn màn hình bắt buộc, Đo đếm thời gian vắng mặt, Vô hiệu hóa chuột phải & phím tắt gian lận (F12, DevTools), Lưu bài tự động từng câu & Khóa đơn phiên.

### 3. Nâng cấp Bộ Giám Sát `ExamAntiCheatManager` (`ui.js`)
- Tự động lưu `startTime` và tính toán `durationSeconds` khi kết thúc sự kiện.
- Tích lũy `totalAwaySeconds` và gửi liên tục qua `onObservation(count, type, durationSeconds, totalAwaySeconds)`.
- Chặn hành vi gian lận:
  - `_handleContextMenu`: Vô hiệu hóa chuột phải trên toàn trang thi.
  - `_handleCopyCut`: Chặn sao chép, cắt nội dung câu hỏi.
  - `_handleKeyDown`: Chặn F12, Ctrl+Shift+I/J/C (DevTools), Ctrl+U (mã nguồn), Ctrl+S (lưu trang), Ctrl+P (in).
- Hỗ trợ callback `onFullscreenExit` và `onFullscreenEnter`.

### 4. Tái thiết kế Toàn diện Phòng Chờ Thi (`renderWaitingRoom`)
- **Header Khảo thí**: Tiêu đề bài thi, Môn học, Mã môn, Giảng viên, Huy hiệu `[Giám sát khảo thí bắt buộc 100%]`.
- **4 Thẻ Chỉ số**: Thời lượng làm bài, Số lượng câu hỏi, Điểm đạt yêu cầu, Số lượt thi được phép.
- **Thẻ Định danh Thí sinh (Candidate Identity Card)**: Avatar viết tắt, Tên đầy đủ, Email, Trạng thái hồ sơ hợp lệ, Phiên đăng nhập an toàn.
- **Quy chế Giám sát Khảo thí Chính thức**: Cảnh báo 4 điểm bắt buộc trước giờ làm bài.
- **Kiểm tra Điều kiện Thiết bị (Pre-Exam System Readiness Checklist)**: Kiểm tra thời gian thực 4/4 tiêu chí: Đường truyền mạng, Toàn màn hình, Cảm biến tiêu điểm tab, Độ phân giải màn hình.
- **Cam kết Trung thực (Honor Code Pledge)**: Checkbox bắt buộc tích chọn thì nút **"BẮT ĐẦU LÀM BÀI THI"** mới khả dụng.
- **Kích hoạt Toàn Màn hình Tức thì**: Gọi `requestFullscreen()` trực tiếp trong cử chỉ nhấp chuột của thí sinh.

### 5. Bàn Làm Bài Thi Khảo Thí (`renderAttemptConsole`)
- **Topbar Thường trực**: Huy hiệu `[👁️ Giám sát trực tiếp (0 vi phạm)]` tự động đổi sang màu cảnh báo `[⚠️ Rời màn hình: N lần (Xs)]` khi có vi phạm.
- **Màn hình Khóa Khẩn cấp Toàn màn hình (Emergency Fullscreen Lockdown Overlay)**:
  - Tự động kích hoạt khóa mờ màn hình khi thí sinh thoát toàn màn hình (phím `Esc` hoặc Alt+Tab).
  - Hiển thị thống kê vi phạm trực tiếp: Số lần vi phạm & Tổng thời gian rời màn hình.
  - Nút **"QUAY LẠI TOÀN MÀN HÌNH NGAY"** kích hoạt lại Fullscreen qua tương tác trực tiếp của thí sinh.
- **Cảnh báo Vắng mặt**: Thông báo Toast chi tiết thời gian vắng mặt khi thí sinh quay lại tab thi.
- **Thoát Fullscreen Tự động**: Tự động thoát toàn màn hình khi nộp bài thi thành công.

---

## IV. BẰNG CHỨNG XÁC MINH THỰC NGHIỆM

### 1. Kiểm thử Frontend (`node --test tests/frontend/*.test.js`)
- Kết quả: **80/80 tests PASSED 100% (0 fail, 0 cancel, 0 skip)**.
- Các bài test proctoring mới:
  - `focus monitoring reports a start and end without submitting the attempt`: PASSED.
  - `focus monitoring tracks away duration and invokes fullscreen callbacks`: PASSED.
  - `exam policy settings use browser-observable monitoring without webcam claims`: PASSED.
  - `exam policy enforces monitoring and fullscreen defaults even without form controls`: PASSED.
  - `waiting room prioritizes resuming an active attempt over exhausted count`: PASSED.
  - `waiting room prevents starting when closed or attempt limit reached`: PASSED.

### 2. Kiểm thử Backend (`pytest tests/api/test_default_exam_proctoring_api.py tests/api/test_student_exam_backend_remediation.py`)
- Kết quả: **9/9 tests PASSED 100%**.
- Các ca kiểm thử:
  - `test_create_assessment_defaults_monitoring_enabled_to_true`: PASSED.
  - `test_default_proctoring_lifecycle_and_focus_events`: PASSED.
  - 7 ca kiểm thử hồi quy khảo thí trong `test_student_exam_backend_remediation.py`: PASSED.

### 3. Kiểm tra Hợp đồng Repository (`python scripts/repo_check.py`)
- Kết quả: **100% PASS** (Cấu trúc bảng MSSQL, không rò rỉ Jinja template, Markdown code fences cân bằng).

---

## V. KẾT LUẬN
Toàn bộ các lỗi nghiêm trọng về cấu hình giám sát mặc định cho role Student và Giảng viên, cùng với giao diện phòng chờ thi trực tuyến đã được giải quyết triệt để, đúng chuẩn kiến trúc **Pure Headless Backend & REST API**, đáp ứng tuyệt đối các quy định học vụ và kỷ luật kỹ thuật của dự án.
