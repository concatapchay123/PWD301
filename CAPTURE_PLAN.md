# KẾ HOẠCH THU THẬP & CHỤP MÀN HÌNH THỰC TẾ (CAPTURE PLAN)
**Dự án:** PWD301 Learning Management System  
**Tiêu chuẩn:** 100% Giao diện thực tế từ trình duyệt Chromium chạy trên máy chủ nội bộ (`http://127.0.0.1:5000/`)  
**Công cụ tự động hóa:** Node.js + Playwright Chromium (`C:\Program Files\Google\Chrome\Application\chrome.exe`)  
**Độ phân giải chụp:** 1920 × 1080 (Pixel-Perfect 16:9, High-DPI crisp rendering)  

---

## 1. MA TRẬN KỸ THUẬT CHỤP & HIỂN THỊ (CAPTURE MATRIX)

| Mã màn hình | Tên màn hình | Phương thức thể hiện | Thao tác tương tác (Interactions) | Dữ liệu kiểm thử (Demo Data) | Tệp lưu trữ |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **SCR-01** | Cổng đăng nhập Warm Editorial | Browser Capture + Animated DOM | Form đăng nhập, checklist mật khẩu, chọn vai trò | Tài khoản mặc định `student1@pwd301.local` | `showcase/assets/screens/scr_01_auth.png` |
| **SCR-02** | Student Command Center | Browser Capture + Animated Counters | 3 thẻ KPI nhảy số theo beat, thẻ khóa học CS101 phát sáng | Tiến độ CS101: 75%, 3 khóa học, 2 hoàn thành | `showcase/assets/screens/scr_02_student_dash.png` |
| **SCR-03** | Course Catalog & Search | Browser Capture + Simulated Typing | Con trỏ SVG click search bar, gõ "Python", lọc card | Danh mục khóa học thực tế CS101, CS201, CS301 | `showcase/assets/screens/scr_03_catalog.png` |
| **SCR-04** | Course Console & Syllabus | Browser Capture + Animated Accordion | Cụm chương mở bung, bài giảng hiển thị danh sách | Khóa học CS101, Chương 1: Kiến trúc Flask | `showcase/assets/screens/scr_04_course_console.png` |
| **SCR-05** | Distraction-Free Lesson Reader | Browser Capture + Scroll Parallax | Đọc nội dung Markdown, khối mã nguồn, nút tick hoàn thành | Bài 1: Tổng quan kiến trúc Flask, tệp đính kèm | `showcase/assets/screens/scr_05_lesson_reader.png` |
| **SCR-06** | Exam Waiting Room | Browser Capture + Countdown Clock | Đồng hồ đếm ngược server đập nhịp, nút bắt đầu thi | Bài kiểm tra giữa kỳ CS101, 10 câu hỏi, 30 phút | `showcase/assets/screens/scr_06_waiting_room.png` |
| **SCR-07** | Live Attempt Console | Browser Capture + Simulated Click | Chế độ Fullscreen Focus, chọn đáp án trắc nghiệm, Autosave | Đề thi thực tế, lựa chọn phương án B | `showcase/assets/screens/scr_07_exam_attempt.png` |
| **SCR-08** | Attempt Scorecard | Browser Capture + Animated Dial | Vòng tròn điểm số quay từ 0 lên 9.5, huy hiệu "ĐẠT" | Kết quả bài thi student1 (Điểm: 9.5/10) | `showcase/assets/screens/scr_08_exam_results.png` |
| **SCR-09** | Bạch tuộc trợ lí AI | Browser Capture + 3D Particles | Bong bóng mở chat, gõ câu hỏi, AI streaming phản hồi | Ngữ cảnh CS101, câu hỏi về Session Flask | `showcase/assets/screens/scr_09_ai_assistant.png` |
| **SCR-10** | Instructor Dashboard | Browser Capture + Metric Scale-up | 4 chỉ số KPI giảng dạy phóng to nhẹ bắt nhịp | Giảng viên TS. Nguyễn Văn A, 2 khóa học, 48 sinh viên | `showcase/assets/screens/scr_10_instructor_dash.png` |
| **SCR-11** | Curriculum Tree Manager | Browser Capture + Drag & Drop | Cây đề cương, kéo thả sắp xếp bài học, biểu tượng tệp | Khóa học CS101 curriculum tree | `showcase/assets/screens/scr_11_curriculum.png` |
| **SCR-12** | Lesson Authoring Studio | Browser Capture + Live Markdown | Trình soạn thảo 2 ngăn, gõ bài giảng mới, xem trước | Khóa học CS101 / Bài giảng mới | `showcase/assets/screens/scr_12_lesson_studio.png` |
| **SCR-13** | Multi-Method Exam Hub | Browser Capture + Hover Spotlight | 4 thẻ phương thức tạo đề (Thủ công, AI, Excel, Moodle) | Ngân hàng câu hỏi và trung tâm khảo thí | `showcase/assets/screens/scr_13_exam_hub.png` |
| **SCR-14** | Visual Exam Matrix | Browser Capture + Recalculate Numbers | Lưới Bloom taxonomy, điều chỉnh thanh trượt, tổng 100% | Phân bổ câu hỏi theo độ khó | `showcase/assets/screens/scr_14_exam_matrix.png` |
| **SCR-15** | Institutional User Governance | Browser Capture + Table Filter | Lọc người dùng theo vai trò "GIẢNG VIÊN", khóa/mở quyền | Bảng 7 tài khoản thực tế trong cơ sở dữ liệu | `showcase/assets/screens/scr_15_admin_users.png` |
| **SCR-16** | Course Review & Approval | Browser Capture + Approval Ping | Trang thẩm định đề cương CS301, bấm nút Phê duyệt | Khóa CS301 "Kiến Trúc Phần Mềm & Thiết Kế Hệ Thống" | `showcase/assets/screens/scr_16_course_review.png` |
| **SCR-17** | Authentic Telemetry & Ops | Browser Capture + Realtime Wave | Đồ thị CPU/RAM/Disk vẽ sóng thực từ psutil | Thông số thực của máy chủ hệ thống | `showcase/assets/screens/scr_17_telemetry.png` |

---

## 2. KỊCH BẢN TỰ ĐỘNG HÓA CHỤP MÀN HÌNH (AUTOMATION SCRIPT PLAN)

1. **Khởi tạo:**
   - Script chạy bằng Node.js: `scripts/capture_screens.mjs`.
   - Kết nối trình duyệt Chromium thật: `C:\Program Files\Google\Chrome\Application\chrome.exe`.
   - Thiết lập Viewport: `1920 × 1080`, Device Scale Factor: `1.0`.

2. **Luồng xác thực 1: Vai trò Sinh viên (`student1@pwd301.local` / `Password123!`):**
   - Mở `http://127.0.0.1:5000/#/auth` $\rightarrow$ Chụp `scr_01_auth.png`.
   - Đăng nhập tài khoản sinh viên $\rightarrow$ Chờ `#/student/dashboard` hoàn tất $\rightarrow$ Chụp `scr_02_student_dash.png`.
   - Điều hướng `#/student/catalog` $\rightarrow$ Chờ danh sách khóa nạp xong $\rightarrow$ Chụp `scr_03_catalog.png`.
   - Điều hướng `#/student/courses/detail?id=1` $\rightarrow$ Chờ cây đề cương bung mở $\rightarrow$ Chụp `scr_04_course_console.png`.
   - Điều hướng `#/student/courses/1/lessons/1` $\rightarrow$ Chờ bài giảng render $\rightarrow$ Chụp `scr_05_lesson_reader.png`.
   - Điều hướng `#/student/assessments/waiting-room?id=1` $\rightarrow$ Chụp `scr_06_waiting_room.png`.
   - Điều hướng `#/student/assessments/attempt?id=1` $\rightarrow$ Chụp `scr_07_exam_attempt.png`.
   - Điều hướng `#/student/assessments/results?id=1` $\rightarrow$ Chụp `scr_08_exam_results.png`.
   - Điều hướng `#/student/ai-assistant` $\rightarrow$ Chụp `scr_09_ai_assistant.png`.

3. **Luồng xác thực 2: Vai trò Giảng viên (`instructor1@pwd301.local` / `Password123!`):**
   - Đăng nhập giảng viên $\rightarrow$ `#/instructor/dashboard` $\rightarrow$ Chụp `scr_10_instructor_dash.png`.
   - Điều hướng `#/instructor/courses/manage?id=1` $\rightarrow$ Chụp `scr_11_curriculum.png`.
   - Điều hướng `#/instructor/courses/1/lessons/new` $\rightarrow$ Chụp `scr_12_lesson_studio.png`.
   - Điều hướng `#/instructor/exams/hub` $\rightarrow$ Chụp `scr_13_exam_hub.png`.
   - Điều hướng `#/instructor/exams/matrix` $\rightarrow$ Chụp `scr_14_exam_matrix.png`.

4. **Luồng xác thực 3: Vai trò Quản trị viên (`admin@pwd301.local` / `Password123!`):**
   - Đăng nhập quản trị viên $\rightarrow$ `#/admin/governance?tab=users` $\rightarrow$ Chụp `scr_15_admin_users.png`.
   - Điều hướng `#/admin/courses/review?id=3` $\rightarrow$ Chụp `scr_16_course_review.png`.
   - Điều hướng `#/admin/operations` $\rightarrow$ Chụp `scr_17_telemetry.png`.

5. **Xác minh đầu ra:**
   - Toàn bộ 17 tệp PNG được lưu trong thư mục `showcase/assets/screens/`.
   - Kiểm tra dung lượng và tính toàn vẹn của từng ảnh trước khi lắp ghép vào HyperFrames composition.
