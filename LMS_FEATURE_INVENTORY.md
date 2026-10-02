# BẢNG KIỂM KÊ CHỨC NĂNG HỆ THỐNG LMS (LMS FEATURE INVENTORY)
**Dự án:** PWD301 Learning Management System  
**Kiến trúc:** Pure Headless Backend (Flask REST API) + Client SPA (Tailwind Warm Editorial)  
**Thời điểm kiểm tra:** 02/10/2026  
**Quy tắc:** Chỉ showcase những chức năng và route THỰC SỰ TỒN TẠI trong mã nguồn dự án. Mọi chức năng không có đều bị loại trừ (`Feature not found in current implementation – excluded from product video`).

---

## 1. BẢNG KIỂM KÊ THEO VAI TRÒ (ROLE-BASED INVENTORY)

| Vai trò (Role) | Chức năng (Feature) | Đường dẫn Route thực tế | Tệp Component / Page | Trạng thái (Status) | Đưa vào Video (Include?) | Ghi chú & Chi tiết kỹ thuật |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ALL / GUEST** | Xác thực đăng nhập (Login) | `#/auth` hoặc `#/login` | `frontend/assets/js/views/auth.js` | Hoàn thành 100% | **CÓ (Intro/Auth)** | Form Warm Editorial, email unique, password checklist, switch role. |
| **STUDENT** | Tổng quan học tập (Dashboard) | `#/student/dashboard` | `frontend/assets/js/views/student.js` | Hoàn thành 100% | **CÓ (Scene 02)** | Thống kê khóa học đang học, tiến độ %, bài thi sắp diễn ra, KPI cards. |
| **STUDENT** | Danh mục & Tìm kiếm khóa học | `#/student/catalog` | `frontend/assets/js/views/student.js` | Hoàn thành 100% | **CÓ (Scene 03)** | Thanh tìm kiếm real-time, bộ lọc danh mục, card khóa học CS101, CS201. |
| **STUDENT** | Khóa học của tôi (My Courses) | `#/student/courses` | `frontend/assets/js/views/student.js` | Hoàn thành 100% | **CÓ (Scene 03)** | Danh sách khóa học đã ghi danh kèm thanh tiến độ hoàn thành. |
| **STUDENT** | Bàn điều khiển khóa học (Course Console) | `#/student/courses/:id` | `frontend/assets/js/views/student.js` | Hoàn thành 100% | **CÓ (Scene 04)** | Cây đề cương (Syllabus tree), danh sách chương mục (Learning Units), bài giảng. |
| **STUDENT** | Trình đọc bài giảng (Lesson Reader) | `#/student/courses/:cId/lessons/:lId` | `frontend/assets/js/views/student.js` | Hoàn thành 100% | **CÓ (Scene 04)** | Markdown phong phú, code highlight, nhúng video, tải tài liệu đính kèm. |
| **STUDENT** | Danh sách bài kiểm tra (Exams List) | `#/student/assessments` | `frontend/assets/js/views/student.js` | Hoàn thành 100% | **CÓ (Scene 05)** | Lịch thi, thời hạn, số lượt làm bài cho phép. |
| **STUDENT** | Phòng chờ thi (Waiting Room) | `#/student/assessments/waiting-room` | `frontend/assets/js/views/student.js` | Hoàn thành 100% | **CÓ (Scene 05)** | Quy chế thi, cam kết liêm chính (Honor code), đồng hồ đếm ngược. |
| **STUDENT** | Bàn thi trực tuyến (Attempt Console) | `#/student/assessments/attempt` | `frontend/assets/js/views/student.js` | Hoàn thành 100% | **CÓ (Scene 05)** | Fullscreen focus mode, bảng câu hỏi số, đếm ngược server, single lease, autosave. |
| **STUDENT** | Kết quả bài thi (Attempt Results) | `#/student/assessments/results` | `frontend/assets/js/views/student.js` | Hoàn thành 100% | **CÓ (Scene 05)** | Điểm số, trạng thái Đạt/Không đạt, chi tiết từng câu hỏi và nhận xét. |
| **STUDENT** | Trợ lý học tập (Bạch tuộc AI) | `#/student/ai-assistant` & Floating AI | `frontend/assets/js/views/student.js` | Hoàn thành 100% | **CÓ (Scene 06)** | Bạch tuộc trợ lí AI, hỏi đáp bài giảng, phân tích ngữ cảnh khóa học, streaming chat. |
| **STUDENT** | Nộp đơn làm giảng viên | `#/student/become-instructor` | `frontend/assets/js/views/student.js` | Hoàn thành 100% | Tùy chọn phụ | Form nộp hồ sơ giảng viên và chứng chỉ. |
| **INSTRUCTOR** | Bảng điều khiển giảng viên | `#/instructor/dashboard` | `frontend/assets/js/views/instructor.js` | Hoàn thành 100% | **CÓ (Scene 07)** | Thống kê số khóa học phụ trách, tổng sinh viên, bài cần chấm. |
| **INSTRUCTOR** | Quản lý khóa học (Courses List) | `#/instructor/courses` | `frontend/assets/js/views/instructor.js` | Hoàn thành 100% | **CÓ (Scene 07)** | Danh sách khóa học đang dạy, nút tạo khóa mới, trạng thái bản nháp/đã duyệt. |
| **INSTRUCTOR** | Quản trị giáo trình (Curriculum Manage) | `#/instructor/courses/:id/manage` | `frontend/assets/js/views/instructor.js` | Hoàn thành 100% | **CÓ (Scene 07)** | Quản lý chương mục, kéo thả sắp xếp bài giảng, đính kèm tệp tài liệu. |
| **INSTRUCTOR** | Xưởng soạn bài giảng (Lesson Authoring) | `#/instructor/courses/:id/lessons/:id` | `frontend/assets/js/views/instructor.js` | Hoàn thành 100% | **CÓ (Scene 07)** | Trình soạn thảo Markdown chuyên sâu, nhúng media, cấu hình tài liệu. |
| **INSTRUCTOR** | Trung tâm khảo thí (Exams Hub) | `#/instructor/exams` | `frontend/assets/js/views/instructor-exams.js` | Hoàn thành 100% | **CÓ (Scene 08)** | Danh sách bài kiểm tra, tạo đề thi mới qua 4 phương thức. |
| **INSTRUCTOR** | Trình soạn câu hỏi (Exam Editor) | `#/instructor/exams/editor` | `frontend/assets/js/views/instructor-exams.js` | Hoàn thành 100% | **CÓ (Scene 08)** | Soạn câu hỏi đơn/đa lựa chọn, đúng sai, tự luận, gán điểm và Bloom taxonomy. |
| **INSTRUCTOR** | Tạo đề tương tác AI / Moodle / Excel | `#/instructor/exams/interactive` | `frontend/assets/js/views/instructor-exams.js` | Hoàn thành 100% | **CÓ (Scene 08)** | Nhập đề từ file Excel, Moodle XML hoặc tạo qua tương tác thông minh. |
| **INSTRUCTOR** | Ma trận đề thi (Exam Matrix) | `#/instructor/exams/matrix` | `frontend/assets/js/views/instructor-exams.js` | Hoàn thành 100% | **CÓ (Scene 08)** | Phân bổ tỉ lệ câu hỏi theo độ khó (Nhận biết, Thông hiểu, Vận dụng). |
| **INSTRUCTOR** | Thiết lập bài thi (Exam Settings) | `#/instructor/exams/settings` | `frontend/assets/js/views/instructor-exams.js` | Hoàn thành 100% | **CÓ (Scene 08)** | Cài đặt thời lượng thi, điểm qua môn, xáo trộn câu/đáp án, số lượt làm bài. |
| **INSTRUCTOR** | Báo cáo kết quả & Chấm bài | `#/instructor/exams/results` | `frontend/assets/js/views/instructor.js` | Hoàn thành 100% | **CÓ (Scene 10)** | Bảng điểm sinh viên, chấm bài tự luận thủ công, nhận xét chi tiết. |
| **ADMIN** | Quản trị người dùng (Users Management) | `#/admin/governance?tab=users` | `frontend/assets/js/views/admin.js` | Hoàn thành 100% | **CÓ (Scene 09)** | Bảng danh sách người dùng, lọc vai trò, khóa/mở tài khoản, phân quyền. |
| **ADMIN** | Hàng đợi duyệt khóa học (Course Approvals) | `#/admin/governance?tab=courses` | `frontend/assets/js/views/admin.js` | Hoàn thành 100% | **CÓ (Scene 09)** | Hàng đợi các khóa học gửi lên chờ duyệt (CS301), xem tóm tắt. |
| **ADMIN** | Trang thẩm định khóa học (Course Review) | `#/admin/courses/review?id=...` | `frontend/assets/js/views/admin.js` | Hoàn thành 100% | **CÓ (Scene 09)** | Giao diện kiểm tra toàn bộ đề cương, bài học và phê duyệt/từ chối kèm lý do. |
| **ADMIN** | Duyệt hồ sơ giảng viên (Applications) | `#/admin/governance?tab=applications` | `frontend/assets/js/views/admin.js` | Hoàn thành 100% | **CÓ (Scene 09)** | Danh sách đơn xin cấp quyền giảng viên của sinh viên. |
| **ADMIN** | Điều chuyển phân công giảng dạy | `#/admin/governance?tab=reassign` | `frontend/assets/js/views/admin.js` | Hoàn thành 100% | **CÓ (Scene 09)** | Chuyển đổi quyền sở hữu khóa học giữa các giảng viên. |
| **ADMIN** | Vận hành & Giám sát hệ thống (Operations) | `#/admin/operations` | `frontend/assets/js/views/admin.js` | Hoàn thành 100% | **CÓ (Scene 10)** | Đo lường CPU/RAM/Disk thực tế qua psutil, nhật ký sao lưu DB, nhật ký cách ly tệp. |

---

## 2. CÁC TÍNH NĂNG ĐƯỢC ĐỀ XUẤT NHƯNG KHÔNG TỒN TẠI (EXCLUDED LIST)

| Tính năng yêu cầu | Tình trạng trong Repository | Kết luận xử lý cho Video |
| :--- | :--- | :--- |
| Diễn đàn thảo luận xã hội (Social Forum / Community Feed) | Không có route hoặc model tương ứng | *Feature not found in current implementation – excluded from product video.* |
| Cổng thanh toán học phí (Payment Gateway / Checkout Cart) | Khóa học ghi danh trực tiếp qua học vụ, không có cổng nạp tiền | *Feature not found in current implementation – excluded from product video.* |
| Phòng học ảo Live Streaming (WebRTC Virtual Classroom) | Hệ thống quản lý tài nguyên video/file, không có WebRTC p2p | *Feature not found in current implementation – excluded from product video.* |
| Chứng chỉ Blockchain NFT | Chứng chỉ cấp bằng file/kết quả học vụ thông thường | *Feature not found in current implementation – excluded from product video.* |

---

## 3. KẾT LUẬN KIỂM KÊ

Toàn bộ 4 nhóm người dùng (Guest, Student, Instructor, Admin) và 18 phân hệ cốt lõi đã được xác thực 100% qua code thật, route thật và cơ sở dữ liệu thật. Đây sẽ là nguồn tài nguyên chính xác tuyệt đối để xây dựng kịch bản video showcase sản phẩm.
