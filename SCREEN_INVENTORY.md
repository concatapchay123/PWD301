# DANH MỤC MÀN HÌNH HỆ THỐNG LMS (SCREEN INVENTORY)
**Dự án:** PWD301 Learning Management System  
**Độ phân giải chuẩn:** 1920 × 1080 (Full HD 16:9)  
**Tiêu chuẩn hình ảnh:** 100% Giao diện thực tế (Actual Application DOM & Browser Capture)  

---

## BẢNG CHI TIẾT 17 MÀN HÌNH ỨNG DỤNG CHO VIDEO

| ID | Vai trò (Role) | Đường dẫn (Route) | Chức năng (Feature) | Tên màn hình (Screen Name) | Thao tác tương tác (Interaction) | Tiềm năng Video (Video Potential) |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| **SCR-01** | ALL | `#/auth` | Xác thực đăng nhập & chuyển vai | **Cổng đăng nhập Warm Editorial** | Nhập email, password checklist hiển thị 4 tiêu chí xanh, chuyển đổi tài khoản mẫu nhanh. | **Cao (Intro Hook)** |
| **SCR-02** | STUDENT | `#/student/dashboard` | Bảng điều khiển sinh viên | **Student Command Center** | Hero card tiếp tục học CS101 (75%), 3 KPI metrics nhảy số, thẻ thông báo bài thi sắp tới. | **Rất cao (Scene 02)** |
| **SCR-03** | STUDENT | `#/student/catalog` | Danh mục & Tìm kiếm | **Course Discovery & Catalog** | Chuột di chuyển đến thanh tìm kiếm, gõ từ khóa "Python", các card khóa học lọc mượt mà theo beat. | **Rất cao (Scene 03)** |
| **SCR-04** | STUDENT | `#/student/courses/detail` | Bàn điều khiển khóa học | **Course Console & Syllabus Tree** | Tiêu đề khóa học, thanh tiến độ tổng thể, danh sách chương mục Accordion mở bung lộ bài học. | **Cao (Scene 04)** |
| **SCR-05** | STUDENT | `#/student/lessons/reader` | Trình đọc bài giảng | **Distraction-Free Lesson Reader** | Nội dung Markdown chuẩn mực, khối code syntax highlight, khung video nhúng, nút tick hoàn thành. | **Rất cao (Scene 04)** |
| **SCR-06** | STUDENT | `#/student/assessments/waiting-room` | Phòng chờ thi trực tuyến | **Exam Waiting Room** | Quy chế thi, cam kết liêm chính, đồng hồ đếm ngược server nhấp nháy, nút CTA "Bắt đầu làm bài". | **Cao (Scene 05)** |
| **SCR-07** | STUDENT | `#/student/assessments/attempt` | Bàn thi tập trung | **Live Assessment Attempt Console** | Fullscreen focus mode, đồng hồ đếm ngược, palette 10 câu hỏi, click chọn đáp án, autosave thông báo. | **Cực đại (Scene 05)** |
| **SCR-08** | STUDENT | `#/student/assessments/results` | Kết quả bài thi | **Attempt Scorecard & Breakdown** | Vòng tròn điểm số nhảy lên 9.5/10, huy hiệu "ĐẠT" xanh ngọc, bảng nhận xét chi tiết từng câu. | **Cao (Scene 05)** |
| **SCR-09** | STUDENT | `#/student/ai-assistant` | Trợ lý học tập thông minh | **Bạch tuộc trợ lí AI (Octopus AI)** | Bong bóng AI phát sáng, khung chat đa lượt, chọn ngữ cảnh CS101, câu hỏi lập trình và AI phản hồi nhanh. | **Cực đại (Scene 06)** |
| **SCR-10** | INSTRUCTOR | `#/instructor/dashboard` | Bảng điều khiển giảng viên | **Instructor Studio Dashboard** | 4 thẻ KPI (Khóa học: 2, Sinh viên: 48, Bài thi: 1, Chờ chấm: 3), danh sách lớp học phụ trách. | **Cao (Scene 07)** |
| **SCR-11** | INSTRUCTOR | `#/instructor/courses/manage` | Quản trị đề cương khóa học | **Curriculum Tree Builder** | Cấu trúc chương mục, kéo thả thay đổi vị trí bài học, tải tệp bài giảng đính kèm (<1GB). | **Rất cao (Scene 07)** |
| **SCR-12** | INSTRUCTOR | `#/instructor/courses/lessons/new` | Xưởng soạn thảo bài học | **Lesson Authoring Studio** | Trình soạn thảo Markdown chuyên sâu, xem trước trực tiếp (Live preview), nhúng tài liệu học vụ. | **Cao (Scene 07)** |
| **SCR-13** | INSTRUCTOR | `#/instructor/exams/hub` | Trung tâm khảo thí | **Multi-Method Exam Hub** | 4 cổng tạo đề (Soạn thủ công, Tương tác AI, Nhập Excel, Nhập Moodle XML) với icon và mô tả rõ ràng. | **Rất cao (Scene 08)** |
| **SCR-14** | INSTRUCTOR | `#/instructor/exams/matrix` | Ma trận & Ngân hàng câu hỏi | **Visual Exam Matrix** | Phân bổ tỉ lệ độ khó Bloom (Nhận biết, Thông hiểu, Vận dụng), tự động tính tổng điểm 100%. | **Cao (Scene 08)** |
| **SCR-15** | ADMIN | `#/admin/governance?tab=users` | Quản trị người dùng | **Institutional User Governance** | Bảng dữ liệu người dùng, lọc vai trò STUDENT/INSTRUCTOR/ADMIN, nút bật/tắt kích hoạt tài khoản. | **Rất cao (Scene 09)** |
| **SCR-16** | ADMIN | `#/admin/courses/review` | Thẩm định & Phê duyệt | **Course Review & Approval Portal** | Trang kiểm tra toàn bộ đề cương khóa học chờ duyệt (CS301), nút "Phê duyệt" phát sáng xác nhận. | **Cao (Scene 09)** |
| **SCR-17** | ADMIN | `#/admin/operations` | Vận hành & Giám sát hệ thống | **Authentic Infrastructure Telemetry** | Biểu đồ CPU/RAM/Disk lấy dữ liệu thực từ psutil, nhật ký sao lưu CSDL, nhật ký kiểm tra virus tệp tin. | **Cực đại (Scene 10)** |

---

## KẾ HOẠCH BỐ TRÍ MÀN HÌNH THEO HÀNH TRÌNH TRẢI NGHIỆM
- **Hồi 1 (Khởi đầu & Khám phá):** SCR-01 (Auth) $\rightarrow$ SCR-02 (Student Dashboard) $\rightarrow$ SCR-03 (Catalog Search)
- **Hồi 2 (Trải nghiệm Học vụ & Khảo thí):** SCR-04 (Console) $\rightarrow$ SCR-05 (Lesson Reader) $\rightarrow$ SCR-06 (Waiting Room) $\rightarrow$ SCR-07 (Attempt) $\rightarrow$ SCR-08 (Scorecard)
- **Hồi 3 (Trí tuệ Nhân tạo Đỉnh cao):** SCR-09 (Bạch tuộc AI Assistant & 3D Particle Cloud)
- **Hồi 4 (Nền tảng Giảng dạy Chuyên nghiệp):** SCR-10 (Instructor Dash) $\rightarrow$ SCR-11 (Curriculum) $\rightarrow$ SCR-12 (Lesson Studio) $\rightarrow$ SCR-13 (Exam Hub) $\rightarrow$ SCR-14 (Matrix)
- **Hồi 5 (Quản trị Vận hành & Hệ sinh thái):** SCR-15 (User Governance) $\rightarrow$ SCR-16 (Course Review) $\rightarrow$ SCR-17 (Authentic Telemetry)
- **Hồi 6 (Đại kết & Khóa thương hiệu):** Multi-screen 3D Convergence $\rightarrow$ Master Logo & Brand Tagline Lockup.
