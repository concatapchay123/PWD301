# PWD301 — ĐẶC TẢ ĐỀ TÀI TOPIC 9 & ĐỘI NGŨ PHÁT TRIỂN
## Online Course Management Platform (Hệ thống Quản lý Khóa học & Khảo thí Trực tuyến)

---

## 👥 1. Đội ngũ Thực hiện Dự án (Project Contributors)

Dự án **PWD301 LMS** được nghiên cứu, thiết kế kiến trúc và phát triển toàn diện bởi nhóm sinh viên thực hiện đồ án tốt nghiệp môn học **PWD301 — Web Application Development with Python & Flask**:

| STT | Họ và Tên Sinh viên | Địa chỉ Email Liên hệ | Vai trò & Phân công Trách nhiệm |
|:---:|---|---|---|
| **1** | **Đặng Lý Quân** | `danglyquan@gmail.com` | **Trưởng nhóm & Kỹ sư Kiến trúc Hệ thống (Lead Architect)**<br>• Thiết kế kiến trúc tổng thể Headless REST API & Modular Monolith.<br>• Xây dựng tầng CSDL 71 bảng quan hệ trên Microsoft SQL Server 2022.<br>• Triển khai cơ chế xác thực kép (Session + JWT) và phân quyền RBAC đa vai trò. |
| **2** | **Lại Vĩnh Phú** | `vinhphu2020.nt@gmail.com` | **Kỹ sư Lập trình Backend & Hạ tầng Dữ liệu (Backend & Database Engineer)**<br>• Hiện thực hóa các dịch vụ nghiệp vụ cốt lõi: Quản lý Khóa học, Bài giảng, Đề cương ABET SLOs.<br>• Thiết lập hệ thống di trú dữ liệu Flask-Migrate / Alembic và bộ dữ liệu mẫu (Seed Data).<br>• Đóng gói môi trường Docker & Docker Compose đa dịch vụ (App, SQL Server, ClamAV). |
| **3** | **Phạm Nguyễn Hoàng Phúc** | `tqtphamnguyenhoangphuc@gmail.com` | **Kỹ sư Khảo thí Trực tuyến & An ninh Mạng (Exam Engine & Security Engineer)**<br>• Xây dựng Động cơ Khảo thí Server-Authoritative 100% tự động chấm khách quan.<br>• Phát triển bộ bóc tách đề thi Azota / Word (`.docx`) thông minh 50/50 live preview studio.<br>• Tích hợp hệ thống quét virus tệp tải lên ClamAV Fail-Closed và hàng rào kiểm soát phiên làm bài Lease Fencing. |
| **4** | **Trần Đặng Hữu Thắng** | `callmewin06@gmail.com` | **Kỹ sư Giao diện Người dùng & Tích hợp AI (Frontend & AI Engineer)**<br>• Thiết kế và phát triển toàn bộ Single-DOM SPA theo phong cách Warm Editorial / Notion Dark.<br>• Tích hợp Trợ lý Gia sư AI Bạch Tuộc với cơ chế Resilient Multi-Key Rotation Pool Google Gemini.<br>• Xây dựng hệ thống bảng điều khiển Cockpit quản trị, đo đạc phần cứng thời gian thực và trải nghiệm học viên. |

---

## 🏫 2. Thông tin Môn học & Quy chế Đánh giá Đồ án

Trích xuất nguyên văn từ tài liệu hướng dẫn đồ án chính thức: **`PWD301_Project.docx`**:

- **Tên môn học**: PWD301 — Web Application Development with Python & Flask  
- **Khung công nghệ bắt buộc**: Framework: **Flask (Python 3.11+)** | CSDL: **SQL Server** | Triển khai: **Docker**  
- **Trọng số điểm**: **20% tổng điểm môn học**  
- **Quy mô nhóm**: **4 – 5 sinh viên / nhóm**  
- **Thời lượng thuyết trình & bảo vệ**: **20 phút / nhóm** (bao gồm slide tổng quan, demo trực tiếp ứng dụng và vấn đáp Q&A)  
- **Thời lượng khóa học**: **10 tuần (60 ca học)**  
- **Thang điểm đánh giá**: **10**  
- **Điều kiện đạt (Passing condition)**: Điểm thành phần đồ án **> 0**  

---

## 🎯 3. Đề tài Chỉ định: Topic 9 — Online Course Management Platform

### 3.1. Mô tả Đề tài (Topic Description)
> **"An online course management platform where instructors create courses with lessons, students enroll, track progress, and take simple quizzes."**  
> *(Một nền tảng quản lý khóa học trực tuyến nơi giảng viên tạo các khóa học gồm các bài giảng, sinh viên đăng ký ghi danh, theo dõi tiến độ học tập và thực hiện các bài kiểm tra trắc nghiệm đánh giá kiến thức).*

### 3.2. Tính năng Trọng tâm theo Yêu cầu (Key Features)
1. **Quản lý Khóa học Giảng viên**: Giảng viên tạo và quản lý khóa học với tên môn, mô tả tổng quan và danh sách bài giảng được sắp xếp có thứ tự logic.
2. **Ghi danh & Theo dõi Tiến độ Học viên**: Học viên duyệt danh mục khóa học, đăng ký ghi danh học tập và theo dõi tiến độ hoàn thành bài học theo tỷ lệ phần trăm trực quan.
3. **Nội dung Bài giảng Chuẩn Markdown**: Nội dung bài học được định dạng phong phú bằng Markdown, hỗ trợ đánh dấu "Đã hoàn thành" (Mark as Completed).
4. **Khảo thí Trắc nghiệm Đánh giá**: Bài kiểm tra ngắn (Quiz) ở cuối mỗi bài học hoặc khóa học với các câu hỏi trắc nghiệm khách quan (Multiple Choice) và cơ chế tự động chấm điểm tức thì (Auto-grading).
5. **Phân quyền Vai trò Người dùng (RBAC)**:
   - **Admin (Quản trị viên)**: Phê duyệt khóa học trước khi phát hành, quản lý người dùng và giám sát an toàn hệ thống.
   - **Instructor (Giảng viên)**: Tạo, cập nhật và quản lý giáo án bài giảng cùng ngân hàng bài thi.
   - **Student (Học viên)**: Đăng ký tài khoản, ghi danh khóa học, học bài và làm bài khảo thí.
6. **Hệ thống REST API**: Cung cấp các endpoint API chuẩn JSON trả về danh sách khóa học và tiến độ học tập của học viên.

### 3.3. Tech Stack Quy chuẩn (Technology Stack)
- **Backend Framework**: Python Flask (Python 3.11+)
- **ORM & CSDL**: Flask-SQLAlchemy, Microsoft SQL Server
- **Biểu mẫu & Bảo mật Form**: Flask-WTF (CSRF Protection, Form Validation, PRG Pattern)
- **Xác thực & Phân quyền**: Flask-Login, RBAC Decorators
- **Trình bày Nội dung**: Markdown Parser, Bootstrap 5 / Modern CSS
- **Tương tác Động không Tải lại trang**: JavaScript Fetch API / AJAX
- **Xác thực API Ngoại vi**: JWT (JSON Web Tokens)
- **Đóng gói Môi trường**: Docker & Docker Compose

### 3.4. Các Bước Triển khai Tiêu chuẩn (Implementation Steps)
1. **Khởi tạo Dự án**: Khởi tạo project Flask với kiến trúc Blueprints phân tầng (`auth`, `courses`, `api`), cấu hình môi trường dựa trên biến `.env` (Dev/Prod), thiết lập virtual environment và danh mục thư viện phụ thuộc.
2. **Xây dựng Mô hình Dữ liệu (ORM Models)**: Thiết kế các thực thể `User`, `Course`, `Lesson`, `Quiz`, `Question`, `Enrollment` (bảng liên kết Nhiều - Nhiều giữa User và Course kèm trường lưu tiến độ `progress`). Thiết lập quan hệ Một - Nhiều (`Course-Lesson`, `Lesson-Quiz`). Cấu hình công cụ di trú Flask-Migrate.
3. **Xây dựng Tuyến đường & Giao diện (Routes & Templates)**: Xây dựng trang chủ danh sách khóa học, chi tiết khóa học, màn hình học bài giảng và trang làm bài thi trắc nghiệm. Áp dụng kế thừa template layout chuẩn mực.
4. **Xây dựng Biểu mẫu Nghiệp vụ**: Xây dựng form tạo/sửa khóa học, form biên soạn bài giảng Markdown, form soạn câu hỏi trắc nghiệm bằng Flask-WTF tích hợp chống CSRF, validation dữ liệu đầu vào và quy tắc PRG (Post/Redirect/Get).
5. **Hiện thực Xác thực & Phân quyền**: Triển khai đăng ký, đăng nhập, bảo vệ mật khẩu băm, phân quyền RBAC (Admin, Instructor, Student) bằng custom decorators kiểm soát quyền sở hữu tài nguyên.
6. **Xây dựng Tầng REST API**: Hiện thực các endpoint chuẩn:
   - `GET /api/courses`: Lấy danh mục khóa học (hỗ trợ phân trang, tìm kiếm).
   - `GET /api/courses/<id>/progress`: Lấy tiến độ học tập chi tiết của học viên đã đăng nhập (yêu cầu JWT).
   - `POST /api/lessons/<id>/complete`: Đánh dấu hoàn thành bài học qua API.
7. **Tích hợp Tương tác Động (AJAX/Fetch)**: Xử lý đánh dấu hoàn thành bài học, nộp bài kiểm tra và cập nhật thanh tiến độ theo thời gian thực mà không cần tải lại toàn bộ trang web.
8. **Kiểm thử, Đóng gói & Tài liệu hóa**: Viết test cases tự động (Unit test, Integration test), đóng gói `Dockerfile` cùng `docker-compose.yml`, hoàn thiện tài liệu hướng dẫn `README.md`.

---

## 📋 4. Toàn bộ 12 Yêu cầu Chung của Môn học (General Requirements for All Topics)

Theo quy định bắt buộc của môn học PWD301 áp dụng cho tất cả các nhóm và mọi đề tài:

1. **Khung công nghệ chính**: Sử dụng Framework **Flask (Python 3.11+)** với **Microsoft SQL Server** là cơ sở dữ liệu quan hệ chính.
2. **Lược đồ CSDL ORM**: Áp dụng Flask-SQLAlchemy ORM với **tối thiểu 4 bảng** thực thể và có **ít nhất 1 quan hệ Nhiều - Nhiều (Many-to-Many)**.
3. **Bảo mật Biểu mẫu**: Sử dụng Flask-WTF cho tất cả các biểu mẫu (forms) với cơ chế phòng chống tấn công CSRF (Cross-Site Request Forgery) và kiểm tra tính hợp lệ dữ liệu nghiêm ngặt phía máy chủ (server-side validation).
4. **Xác thực & Phân quyền RBAC**: Hiện thực hệ thống xác thực người dùng (Flask-Login hoặc tương đương) và phân quyền truy cập theo vai trò RBAC với **tối thiểu 3 vai trò (3 roles)** rõ rệt.
5. **Tầng Giao tiếp REST API**: Xây dựng **tối thiểu 3 endpoint REST API** trả về dữ liệu chuẩn JSON và được bảo vệ bằng cơ chế xác thực **JWT (JSON Web Token)**.
6. **Tương tác Giao diện Động**: Ứng dụng công nghệ **AJAX / Fetch API** cho **tối thiểu 1 tính năng động** thời gian thực, không tải lại trang (no page reload).
7. **Thiết kế Giao diện**: Áp dụng kế thừa bố cục giao diện (Template Inheritance với base layout) và thiết kế đáp ứng đa thiết bị (Responsive Design).
8. **Quản lý Di trú CSDL**: Quản lý lịch sử thay đổi cấu trúc CSDL bằng **Flask-Migrate / Alembic**, kèm bộ dữ liệu khởi tạo mẫu (**Seed Data**) phục vụ trình diễn và chấm điểm.
9. **Đóng gói Containerization**: Đóng gói hoàn chỉnh ứng dụng vào container với **Docker** (bao gồm `Dockerfile` và `docker-compose.yml`).
10. **Nhật ký Ứng dụng AI**: Khuyến khích ứng dụng các công cụ AI hỗ trợ phát triển (GitHub Copilot, Google Gemini...) và duy trì nhật ký sử dụng AI (**AI Usage Log**).
11. **Quản lý Mã nguồn Git**: Toàn bộ mã nguồn dự án được quản lý chặt chẽ trên **Git**, có tệp `README.md` cung cấp đầy đủ hướng dẫn thiết lập, cài đặt và vận hành hệ thống.
12. **Bảo vệ Đồ án Cuối kỳ**: Báo cáo tổng kết đồ án với slide thuyết trình + demo trực tiếp ứng dụng trên máy thật + trả lời câu hỏi vấn đáp Q&A của hội đồng (**20 phút / nhóm**).

---

## 📅 5. Tiến độ 5 Cột mốc Đồ án (Progress Report Milestones)

| Cột mốc (Milestone) | Thời điểm Khóa học | Nội dung Bàn giao & Mục tiêu Cần đạt | Trạng thái Đạt được |
|---|---|---|:---:|
| **Milestone 1** | **Tuần 1 (Buổi 3)** | Thành lập nhóm làm việc, phân công vai trò nhiệm vụ thành viên, đọc hiểu toàn diện yêu cầu đề bài Topic 9, lập kế hoạch tổng thể dự án. | **HOÀN THÀNH 100%** |
| **Milestone 2** | **Tuần 3 (Buổi 9)** | Xác nhận đề tài, hoàn thiện khung dự án Flask Modular Blueprints, định nghĩa SQLAlchemy models, tạo bản migration đầu tiên, xây dựng giao diện cơ bản với kế thừa template. | **HOÀN THÀNH 100%** |
| **Milestone 3** | **Tuần 6 (Buổi 29)** | Hoàn thiện CRUD Khóa học, Bài học, Bài kiểm tra Quiz; toàn bộ form chạy ổn định với CSRF + Server Validation + PRG; phân quyền RBAC hoạt động chuẩn xác. | **HOÀN THÀNH 100%** |
| **Milestone 4** | **Tuần 8 (Buổi 42)** | Hoàn thiện các endpoint REST API với xác thực JWT, tích hợp AJAX tương tác mượt mà không tải lại trang, hoàn thành tính năng ghi danh và thanh tiến độ. | **HOÀN THÀNH 100%** |
| **Milestone 5** | **Tuần 9 (Buổi 51) – Tuần 10** | Hoàn thành toàn bộ kiểm thử tự động, đóng gói Docker hoàn chỉnh, tối ưu hóa hệ thống, khắc phục lỗi triệt để, chuẩn bị slide và demo bảo vệ đồ án trước hội đồng. | **SẴN SÀNG 100%** |

---

## 🏆 6. Bảng Ma trận Đối chiếu Rubric: Chuẩn Đề tài vs Thành tựu Vượt bậc tại PWD301 LMS

Dự án **PWD301 LMS** không dừng lại ở mức hoàn thành yêu cầu cơ bản của Topic 9 mà đã nâng cấp toàn diện thành một **Nền tảng Quản lý Học tập & Khảo thí Doanh nghiệp (Enterprise Academic SaaS)**:

| Tiêu chí Đánh giá Rubric | Yêu cầu Tối thiểu của Topic 9 | Hiện thực hóa tại Hệ thống PWD301 LMS | Đánh giá & Mức độ Vượt bậc |
|---|---|---|:---:|
| **1. Công nghệ & Framework** | Flask, Python 3.11+, SQL Server | Flask Headless REST API chuẩn doanh nghiệp, kiến trúc Modular Monolith phân tầng nghiêm ngặt, kết nối Microsoft SQL Server 2022 qua PyODBC Pooling. | **Vượt xa yêu cầu cơ bản** |
| **2. Quy mô & Chuẩn hóa CSDL** | Tối thiểu 4 bảng, 1 bảng M-M | **71 bảng quan hệ chuẩn hóa 3NF/BCNF** bao quát trọn vẹn Học vụ, Ngân hàng Câu hỏi Bloom, Khảo thí, An ninh Tệp và Trí tuệ Nhân tạo. Khóa chính BigInt nội bộ kết hợp Public UUIDv4/v5 và cờ khóa lạc quan `ROWVERSION`. | **Gấp 17 lần yêu cầu đề bài** |
| **3. Quản lý Khóa học & Bài giảng** | Thêm sửa bài giảng, Markdown | Hệ thống Quản lý Khóa học đa giảng viên, ma trận chuẩn đầu ra ABET SLOs, điều kiện tiên quyết chống vòng lặp (DAG Cycle Detection), trình soạn giáo án Notion-style 1 trang, lưu nháp tự động 30s. | **Đẳng cấp SaaS Hiện đại** |
| **4. Động cơ Khảo thí (Quiz / Exam)** | Bài trắc nghiệm ngắn ở cuối bài | **Studio Soạn đề thi PWD301 Exam Studio**: Bóc tách tự động tệp Word (`.docx`) theo chuẩn Azota với giao diện Split-view 50/50, phân loại 6 bậc tư duy Bloom, tự động chấm 100% trắc nghiệm khách quan, chống gian lận Fullscreen Focus Mode và kiểm soát phiên làm bài độc quyền qua Lease Fencing (`lease_token`, `lease_epoch`). | **Đột phá Công nghệ Khảo thí** |
| **5. Phân quyền & Quản trị RBAC** | Tối thiểu 3 vai trò (Admin, Instructor, Student) | 3 vai trò chuẩn mực với mô hình bảo mật 2 lớp: Role-based kết hợp Object-level IDOR Defense. Phân hệ Admin Governance phê duyệt đề cương so sánh Side-by-Side Diff, luồng học viên nộp hồ sơ xin làm giảng viên và trung tâm điều hành máy chủ Telemetry thời gian thực. | **Bảo mật Chuẩn Doanh nghiệp** |
| **6. Giao diện & Trải nghiệm Người dùng** | Jinja2 Template + Bootstrap 5 | **Single-DOM SPA Warm Editorial**: Giao diện Notion Dark / Warm Charcoal cao cấp, thanh vi mô chuyển trang Sub-100ms Micro-loader, không giật lag, hỗ trợ toàn diện chế độ Sáng / Tối (Light & Dark Mode). | **Trải nghiệm Mượt mà Không tải lại trang** |
| **7. REST API & Chuẩn giao tiếp** | Tối thiểu 3 REST API + JWT | **Hơn 40 REST API Endpoints** chuẩn hóa theo định dạng vỏ bọc máy đọc JSON (`success`, `data`, `meta`, `error`), hỗ trợ xác thực kép: Cookie Session cho Web SPA và Bearer JWT Token cho REST Clients. | **Hoàn chỉnh 100% Headless API** |
| **8. An toàn Thông tin & Bảo mật Tệp** | CSRF Protection cho form | Hệ thống quét mã độc tệp tải lên **ClamAV Antivirus Fail-Closed**: Tệp chỉ được cấp phép lưu hành sau khi xác nhận an toàn (`virus_scan_status == 'CLEAN'`). Cách ly tệp nhiễm độc tức thì, che giấu đường dẫn vật lý cục bộ. | **An ninh Đạt chuẩn Quốc tế** |
| **9. Ứng dụng Trí tuệ Nhân tạo (AI)** | Duy trì nhật ký sử dụng AI | **Trợ lý Gia sư AI Bạch Tuộc (Octopus AI Tutor)**: Tích hợp trực tiếp vào giao diện với bể chứa xoay tua đa khóa API Google Gemini (`GeminiKeyPool`), tự phục hồi 0ms khi gặp lỗi 401/429/503, cơ chế Fallback Cascade đa mô hình, RAG tài liệu khóa học và hàng rào phòng thủ 3 tầng chống trinh sát cấu trúc hệ thống. | **Vượt bậc Tiên phong** |
| **10. Tự động hóa & Kiểm thử (QA)** | Viết test cases cơ bản | **Hơn 535 bài kiểm thử tự động (Pytest)** đạt tỷ lệ **PASS 100%**: Unit test, API Integration test, Security Audit test, E2E Lifecycle test và Static analysis (`ruff check` 0 errors, `node --check` 0 errors). | **Kỷ luật Kỹ thuật Phần mềm Cao nhất** |
| **11. Đóng gói & Vận hành Production** | Dockerfile + docker-compose | Docker Compose đóng gói đồng bộ 3 dịch vụ: Web Backend (Gunicorn), Database MS SQL Server 2022 và ClamAV Daemon; quy trình khôi phục CSDL an toàn có kiểm soát 4 bước (Controlled Live Database Restore). | **Sẵn sàng Vận hành Thực tế** |

---

## 📌 7. Kết luận & Cam kết Chất lượng

Đồ án môn học **PWD301 LMS** là minh chứng cụ thể cho năng lực làm việc nhóm hiệu quả, kỷ luật kỹ thuật phần mềm nghiêm ngặt và tinh thần học hỏi sáng tạo của 4 thành viên: **Đặng Lý Quân**, **Lại Vĩnh Phú**, **Phạm Nguyễn Hoàng Phúc** và **Trần Đặng Hữu Thắng**. Dự án đã sẵn sàng phục vụ cho buổi thuyết trình và bảo vệ đồ án kết thúc môn học.
