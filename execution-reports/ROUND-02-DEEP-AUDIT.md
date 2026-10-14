# VÒNG 2: KIỂM TOÁN CHUYÊN SÂU & PHÁT HIỆN LỖI (DEEP AUDIT)
## Dự án PWD301 LMS — Nâng cấp Toàn diện 6 Hạng mục

---

### 1. Mục tiêu Vòng 2
Đóng vai trò một Senior QA / Security Auditor độc lập, tiến hành rà soát tĩnh (Static Code Review), kiểm tra tính an toàn thông tin (Fail-Closed, Zero-Trust), thử nghiệm thao tác thực tế và chủ động tìm kiếm các điểm nghẽn, lỗ hổng logic hoặc hiện tượng hồi quy phát sinh từ Vòng 1.

---

### 2. Hoạt động Kiểm toán Thực hiện

#### A. Rà soát Mã nguồn Tĩnh (Alibaba OCR Ruleset)
- **Null Pointer / Undefined Dereference**:
  - Phát hiện tại `frontend/assets/js/views/student.js`: Phương thức `AuthState.getUser()` có nguy cơ trả về `undefined` hoặc `null` trong một số luồng khởi tạo ứng dụng, dẫn đến ngoại lệ `TypeError: Cannot read properties of undefined (reading 'is_email_verified')`.
- **Phạm vi Giám sát DOM & Memory Leak**:
  - Phát hiện tại `frontend/assets/js/components/video-armor.js`: `MutationObserver` gắn trên `document.body` giám sát toàn bộ các thay đổi DOM trên trang. Khi người dùng chuyển tab, mở inspect hoặc resize màn hình, observer kích hoạt sự kiện vi phạm `DOM_TAMPER` giả mạo.
- **Tính An toàn Luồng Streaming**:
  - Tại `src/pwd301/blueprints/api_files/routes.py`: Xác nhận cơ chế Fail-Closed hoạt động tốt, chặn học viên chưa xác thực email với HTTP 403 `EMAIL_NOT_VERIFIED`.

#### B. Thử nghiệm Thao tác Thực tế & Giao diện (Manual / Real-World UI Testing)
- **Thử nghiệm Điều hướng Bài học (Category 4)**:
  - *Hiện tượng phát hiện*: 
    1. Khi học sinh học xong Bài 1 và chuyển sang Bài 2, bấm nút "Quay lại" thì nút bị khóa cứng hoặc không phản hồi.
    2. Khi chuyển từ Bài 2 lùi về Bài 1, nút "Tiếp theo" của Bài 1 bị chuyển sang màu xám và yêu cầu học lại từ đầu.
- **Thử nghiệm Bài thi Cuối kỳ (Category 5)**:
  - *Hiện tượng phát hiện*: Mặc dù trên cây thư mục bài học có hiển thị điều kiện tiên quyết, nhưng nếu học sinh bấm vào menu "Bài kiểm tra" trên thanh điều hướng chính, danh sách bài thi vẫn hiển thị nút "Vào thi" và cho phép mở phòng thi Final Exam dù chưa học bất kỳ bài giảng nào.
- **Thử nghiệm Định dạng Báo cáo PDF (Category 2)**:
  - *Hiện tượng phát hiện*: Khi bài thi chứa các công thức toán LaTeX phức tạp như $\frac{a+b}{c}$, $x^2$, $\sqrt{16}$, tệp PDF ReportLab hiển thị mã thô hoặc các ký tự rác.

#### C. Thử nghiệm Phủ định (Negative Testing & Boundary Edge Cases)
- Thử nghiệm gọi trực tiếp API `POST /assessments/<final_id>/start_attempt` bằng script không thông qua giao diện: Phát hiện backend chưa kiểm tra tỷ lệ hoàn thành bài học tiên quyết của khóa học đối với bài thi cuối kỳ.
- Thử nghiệm tắt quyền xem kết quả `allow_student_view_results = False`: Phát hiện API `get_attempt_result_for_student` vẫn trả về điểm số chi tiết và danh sách đáp án đã chọn.

---

### 3. Danh sách Lỗi Phát hiện trong Vòng 2

1. **BUG-01 (Mức độ P1)**: VideoArmor báo động sai `DOM_TAMPER` khi resize hoặc đổi tab.
2. **BUG-02 (Mức độ P1)**: Nút "Quay lại" bị khóa cứng hoặc không chuyển về bài trước.
3. **BUG-03 (Mức độ P1)**: Bài 1 đã hoàn thành bị khóa lại nút "Tiếp theo" khi quay lại xem.
4. **BUG-04 (Mức độ P0)**: Final Exam mở cổng cho thi ở trang "Bài kiểm tra" và API dù chưa hoàn thành bài học.
5. **BUG-05 (Mức độ P1)**: Công thức toán LaTeX xuất hiện ký tự rác hoặc raw `$` trong file PDF ReportLab.
6. **BUG-06 (Mức độ P1)**: Điểm số và đáp án vẫn lộ trong PDF và API khi giảng viên tắt quyền xem kết quả.
7. **BUG-09 (Mức độ P3)**: Xung đột CSS class `teal` ghi đè màu xanh lá / đỏ trong xem trước câu hỏi tương tác.

---

### 4. Kết luận Vòng 2
Giai đoạn kiểm toán Vòng 2 đã phát hiện 7 lỗi quan trọng (trong đó có 1 lỗi P0 về bảo mật phòng thi Final Exam và 3 lỗi P1 về trải nghiệm điều hướng và bảo vệ video). Toàn bộ danh mục lỗi đã được ghi nhận vào `BUG-TRACKER.md`. Chuyển ngay sang **Vòng 3: Full Bug Fixing & Gap Closure**.
