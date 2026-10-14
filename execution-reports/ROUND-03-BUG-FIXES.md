# VÒNG 3: SỬA LỖI & HOÀN THIỆN NỀN TẢNG (BUG FIXING & GAP CLOSURE)
## Dự án PWD301 LMS — Nâng cấp Toàn diện 6 Hạng mục

---

### 1. Mục tiêu Vòng 3
Sử dụng 100% kết quả rà soát từ Vòng 2 để phân tích nguyên nhân gốc (Root Cause Analysis), tiến hành sửa chữa triệt để các lỗi từ P0 đến P3, loại bỏ hoàn toàn các lỗ hổng bảo mật và hoàn thiện các điểm thiếu sót logic giữa Backend và Frontend.

---

### 2. Các Bản Sửa Lỗi Chi Tiết Thực Hiện

#### A. Sửa Lỗi Khóa Bài thi Cuối kỳ (BUG-04 - Mức độ P0)
- **Tệp tin sửa đổi**:
  - [`src/pwd301/services/attempt_service.py`](file:///e:/PWD301/src/pwd301/services/attempt_service.py)
  - [`src/pwd301/blueprints/student/routes.py`](file:///e:/PWD301/src/pwd301/blueprints/student/routes.py)
  - [`frontend/assets/js/views/student.js`](file:///e:/PWD301/frontend/assets/js/views/student.js)
- **Giải pháp**:
  - Tại `attempt_service.py`: Trong `start_assessment_attempt`, thêm logic đếm tổng số bài học `PUBLISHED` trong khóa học so với số bài học học viên đã hoàn thành (`LessonProgress.completed_at IS NOT NULL`). Nếu chưa đạt 100%, chặn ngay lập tức và ném ra `AttemptValidationError` (HTTP 403) với thông báo: *"Bạn cần hoàn thành tất cả các bài học trong khóa học (x/y bài) trước khi tham gia bài thi cuối kỳ (Final Exam)."*
  - Tại `student/routes.py`: Endpoint `/assessments` và `/assessments/<id>` tính toán cờ `is_locked`, `lock_reason` và `can_start` gửi về cho client.
  - Tại `student.js`: Khi `a.is_locked || a.can_start === false`, nút "Vào thi" bị vô hiệu hóa với màu xám `cursor-not-allowed` kèm badge `Chưa đủ điều kiện thi` và tooltip hiển thị số bài học còn thiếu. Waiting Room chuyển sang trạng thái `LOCKED_PREREQUISITE`.

#### B. Sửa Lỗi Điều hướng Bài học (BUG-02 & BUG-03 - Mức độ P1)
- **Tệp tin sửa đổi**:
  - [`frontend/assets/js/views/student.js`](file:///e:/PWD301/frontend/assets/js/views/student.js)
- **Giải pháp**:
  - **Sửa BUG-02**: Trong `_ciscoSelectItem`, bổ sung cờ phát hiện hướng di chuyển:
    ```javascript
    const isGoingBack = curIdx !== -1 && targetIdx !== -1 && targetIdx < curIdx;
    if (isGoingBack) {
        // Cho phép chuyển bài học lùi về trước mà không áp đặt kiểm tra isUnlocked
    }
    ```
  - **Sửa BUG-03**: Trong `renderActiveContent`, đánh giá trạng thái hoàn thành kết hợp cả bộ nhớ cache và tiến độ:
    ```javascript
    const isCompleted = Boolean(
        cachedLes?.is_completed ||
        (lesson.progress && lesson.progress.is_completed) ||
        activeItem.isCompleted
    );
    ```
    Một khi bài học đã hoàn thành thì trạng thái mở khóa xanh lá được bảo toàn vĩnh viễn, không bị reset dwell timer khi quay lại.

#### C. Sửa Lỗi Báo động Giả VideoArmor (BUG-01 - Mức độ P1)
- **Tệp tin sửa đổi**:
  - [`frontend/assets/js/components/video-armor.js`](file:///e:/PWD301/frontend/assets/js/components/video-armor.js)
- **Giải pháp**:
  - Thu hẹp phạm vi giám sát của `MutationObserver` vào `this.container` thay vì toàn bộ `document.body`.
  - Thêm điều kiện kiểm tra `this.container.isConnected` trước khi phát tín hiệu `DOM_TAMPER`, ngăn chặn kích hoạt sai khi cửa sổ trình duyệt thay đổi kích thước hoặc chuyển tab.

#### D. Sửa Lỗi Định dạng PDF LaTeX (BUG-05 - Mức độ P1)
- **Tệp tin sửa đổi**:
  - [`src/pwd301/services/result_pdf_service.py`](file:///e:/PWD301/src/pwd301/services/result_pdf_service.py)
- **Giải pháp**:
  - Xây dựng hàm `_render_math_and_plain()` phân tích cú pháp LaTeX với ngăn xếp cặp ngoặc nhọn `{...}`, chuyển đổi chính xác phân số `\frac{a}{b} -> (a)/(b)`, căn bậc hai `\sqrt{x} -> √(x)`, lũy thừa `x^2 -> x<sup>2</sup>`, chỉ số dưới `y_1 -> y<sub>1</sub>`, tích phân `\int -> ∫`, và các ký tự Hy Lạp.
  - Sử dụng regex tách các thẻ `(</?(?:sup|sub)>)` để bảo toàn định dạng khi escape XML trong ReportLab.

#### E. Sửa Lỗi Bảo vệ Dữ liệu Bài thi Ẩn Kết quả (BUG-06 - Mức độ P1)
- **Tệp tin sửa đổi**:
  - [`src/pwd301/services/attempt_service.py`](file:///e:/PWD301/src/pwd301/services/attempt_service.py)
  - [`src/pwd301/services/result_pdf_service.py`](file:///e:/PWD301/src/pwd301/services/result_pdf_service.py)
- **Giải pháp**:
  - Trong `get_attempt_result_for_student`, khi `allow_student_view_results == False`, che giấu toàn bộ `points_assigned = None`, `awarded_points = None`, `is_correct = None`, `selected_choice_keys = []` và gán `score_status = "RESULTS_HIDDEN"`.
  - Trong tệp PDF, điền `-` vào 3 cột: "Đáp án đã chọn", "Kết quả", "Điểm", ẩn tổng điểm và hiển thị badge `ĐÃ GHI NHẬN BÀI NỘP`.

#### F. Dọn dẹp Class Màu Xung đột (BUG-09 - Mức độ P3)
- **Tệp tin sửa đổi**:
  - [`frontend/assets/js/views/instructor-exams.js`](file:///e:/PWD301/frontend/assets/js/views/instructor-exams.js)
- **Giải pháp**:
  - Thay thế toàn bộ các class `teal` bằng `emerald` và `rose` trong preview câu hỏi tương tác.

---

### 3. Kết luận Vòng 3
Toàn bộ 7 lỗi phát hiện ở Vòng 2 đã được sửa chữa tận gốc. Chuyển ngay sang **Vòng 4: Second Independent Audit + Real-World Revalidation**.
