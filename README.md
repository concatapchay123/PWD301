# PWD301 — Intelligent Enterprise Learning & Assessment Platform

> Workflow authority: [approved replacement contract](docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/WORKFLOW_SUPERSESSION.md). Historical task completion is not proof of current implementation.

<div align="center">

![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)
![Flask Headless](https://img.shields.io/badge/Backend-Flask%20Headless%20REST%20API-black?logo=flask&logoColor=white)
![MS SQL Server 2022](https://img.shields.io/badge/Database-MS%20SQL%20Server%202022%20(77%20B%E1%BA%A3ng)-CC292B?logo=microsoftsqlserver&logoColor=white)
![Docker Compose](https://img.shields.io/badge/Container-Docker%20Compose-2496ED?logo=docker&logoColor=white)
![ClamAV Antivirus](https://img.shields.io/badge/Security-ClamAV%20Fail--Closed-red)
![Google Gemini AI](https://img.shields.io/badge/AI-Gemini%20Flash%20(Multi--Key%20Pool)-orange?logo=google&logoColor=white)
![Tailwind Warm Editorial](https://img.shields.io/badge/Frontend-Warm%20Editorial%20SPA-38BDF8?logo=tailwindcss&logoColor=white)
![Test Coverage](https://img.shields.io/badge/Tests-1%2C530%2B%20PASSED%20100%25-brightgreen?logo=pytest&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

**Nền tảng Quản lý Khóa học & Khảo thí Trực tuyến Thông minh**  
*Kiến trúc Headless REST API • Single-DOM SPA Warm Editorial • Bàn học Cisco NetAcad • Động cơ Khảo thí Server-Authoritative • Trợ lý AI Bạch Tuộc Đa khóa*

[Tổng quan Nghiệp vụ](#1-hệ-sinh-thái-3-vai-trò--năng-lực-nghiệp-vụ) • [Kiến trúc Kỹ thuật](#2-kiến-trúc-kỹ-thuật--bảng-điều-hướng-sơ-đồ) • [Khởi chạy Nhanh](#3-hướng-dẫn-khởi-tạo--vận-hành-docker) • [Kiểm thử & Chất lượng](#4-chiến-lược-kiểm-thử--đảm-bảo-chất-lượng) • [Ma trận Rubric Topic 9](#5-đối-chiếu-chuẩn-học-thuật--ma-trận-rubric-topic-9) • [Đội ngũ Phát triển](#6-tài-liệu-kỹ-thuật--đội-ngũ-phát-triển)

---

</div>

## Giới thiệu Tổng quan

**PWD301** là nền tảng Quản lý Học tập & Khảo thí Trực tuyến (LMS) hoàn chỉnh, phát triển theo mô hình **Modular Monolith** kết hợp **Headless REST API** và giao diện **Single-DOM SPA (Warm Editorial)**. Nền tảng được thiết kế tập trung vào trải nghiệm học tập liền mạch phong cách Cisco NetAcad, động cơ khảo thí máy chủ toàn quyền (Server-Authoritative), cụm trợ lý AI tự phục hồi xoay vòng đa khóa API (Multi-Key Pool), và hạ tầng dữ liệu Microsoft SQL Server 2022 gồm 77 bảng quan hệ chuẩn hóa được đóng gói toàn diện bằng Docker Compose.

---

## 1. Hệ sinh thái 3 Vai trò & Năng lực Nghiệp vụ

### 1.1. Phân hệ Học viên (Student Experience)
- **Console Học tập Cisco NetAcad 3 Cột**: Điều hướng bài học phân cấp trực quan, không gian đọc tài liệu Markdown Notion-style và tab Trợ lý AI đồng bộ theo ngữ cảnh bài giảng.
- **Trình phát Video Khóa tua (Anti-Seek Player)**: Kiểm soát tiến độ xem thực tế từ 00:00 đến $(Duration - 5s)$; tự động ghi nhận hoàn thành bài học và cho phép tua tự do trong $5\,\text{giây}$ cuối; tự động mở khóa bài học kế tiếp theo thời gian thực (no page reload).
- **Mini-Quiz Tương tác 4 Dạng**: Kiểm tra kiến thức củng cố ngay trong bài học (Trắc nghiệm đơn/đa đáp án, Điền khuyết, Nối từ, Đúng/Sai) với phản hồi giải thích và chấm điểm tức thì.
- **Phòng chờ Thi Thông minh (Smart Waiting Room)**: Tự động nhận diện trạng thái lượt thi ($N/M$), đồng bộ đếm ngược theo thời gian thực UTC máy chủ, tự động hiển thị bảng điểm tổng hợp khi hoàn tất số lượt quy định.
- **Bàn thi Trực tuyến Chống Gian lận (Anti-Cheat Console)**: Ép buộc chế độ Focus toàn màn hình, đếm số lần chuyển tab (`blur_count`), vô hiệu hóa phím kiểm tra mã nguồn (F12, Inspect), và ẩn hoàn toàn trợ lý AI trong suốt thời gian làm bài.
- **Khóa Tab Độc quyền (Single-Active-Tab Lease)**: Bảo vệ bài thi với cặp token `lease_token` và `lease_epoch`, lập tức thu hồi phiên và chặn nộp bài từ các thẻ trình duyệt cũ (HTTP 409).

### 1.2. Phân hệ Giảng viên (Instructor Console)
- **Cấu hình Học vụ Chuẩn ABET SLO**: Thiết lập các chỉ số chuẩn đầu ra khóa học (SLO) và tiêu chí điểm số tối thiểu để cấp chứng chỉ hoàn thành số.
- **Biên soạn Bài giảng Liền mạch (Single-Page Studio)**: Trình soạn thảo trực quan, tự động lưu nháp 30 giây, hỗ trợ nhúng video YouTube tỷ lệ 16:9 nguyên bản hoặc tải lên video nội bộ ($< 1\,\text{GB}$) kèm cơ chế quét mã độc ClamAV Fail-Closed.
- **Studio Soạn Đề thi Chuyên sâu (Exam Studio)**: Tự động bóc tách đề thi từ tệp Word (`.docx`) hoặc cú pháp Azota trên màn hình chia đôi 50/50, tự động phân bổ điểm số $P = \frac{100}{N}$, tích hợp bộ gõ công thức toán học LaTeX 5 chuyên đề.
- **Quản lý Bản nháp & Yêu cầu Thay đổi (Staging Draft & Change Requests)**: Tự động gom các chỉnh sửa sau xuất bản vào một bản nháp hợp nhất (`STAGING_DRAFT`), cho phép đối soát Diff Side-by-Side (Hiện tại vs Đề xuất) trước khi trình Admin duyệt nguyên tử.
- **Sổ điểm & Tái chấm điểm Đẳng công (Idempotent Regrading)**: Quản lý chi tiết từng bài nộp của thí sinh, tự động tái chấm điểm toàn bộ lịch sử thi theo định danh `choice_key` khi giảng viên cập nhật đáp án câu hỏi mà không làm mất điểm số gốc.

### 1.3. Phân hệ Quản trị viên (Admin Command Center)
- **Phân quyền 5 Nhóm Quản trị (Sub-roles Delegation)**:
  - `ADMIN_PRIMARY`: Quản trị viên tối cao toàn quyền hệ thống, cấp và thu hồi quyền, kích hoạt khôi phục CSDL.
  - `ADMIN_COURSE_REVIEW`: Thẩm định đề cương môn học mới và xét duyệt các yêu cầu thay đổi (Change Requests) qua màn hình đối soát Diff.
  - `ADMIN_INSTRUCTOR_REVIEW`: Thẩm định hồ sơ đăng ký giảng viên, xem trước tài liệu minh chứng (CV, Bằng cấp) trực tiếp qua modal inline hoặc tải về.
  - `ADMIN_TEACHING_ASSIGNMENT`: Điều phối, gán và chuyển giao giảng viên phụ trách môn học.
  - `ADMIN_SYSTEM_MONITORING`: Giám sát hạ tầng phần cứng máy chủ thực tế và tra cứu nhật ký kiểm toán.
- **Giám sát Phần cứng Thực tế (Host Telemetry Bridge)**: Đo lường chính xác các chỉ số tải CPU, RAM, Disk từ hệ điều hành máy chủ Host qua thư viện `psutil`, phân định rõ ràng với tài nguyên ảo của container.
- **Quy trình Khôi phục CSDL Live 4 Bước (Controlled Live Restore)**: Bảo vệ dữ liệu với 4 tầng kiểm soát an toàn (Kiểm tra dung lượng tệp $\to$ Nhập mã xác nhận `CONFIRM_LIVE_DATABASE_RESTORE` $\to$ Xác thực mật khẩu cấp cao $\to$ Bút lục kiểm toán hệ thống).
- **Chuỗi Bút lục Toàn vẹn Bất biến (SHA-256 Audit Trail)**: Nhật ký kiểm toán thiết kế theo định hướng Human-Readable First, bảo chứng tính toàn vẹn sự kiện bằng hàm băm mật mã học SHA-256.

### 1.4. Trợ lý AI Bạch Tuộc PPTQ (AI Assistant Ecosystem)
- **Định danh & Chuẩn hóa Phát ngôn**: Trợ lý AI mang danh xưng duy nhất **Bạch Tuột, trợ lí AI của hệ thống PPTQ** với 3 mẫu phát ngôn bất biến chuẩn mực cho chào hỏi mở đầu, phản hồi ngoài phạm vi, và xử lý tương tác tiêu cực.
- **Cụm Đa khóa API Tự phục hồi (Multi-Key Rotation Pool)**: Quản lý danh sách API keys theo cơ chế xoay vòng Thread-Safe, tự động phát hiện lỗi hạn ngạch (Quota 429) để chuyển đổi tức thời sang khóa khả dụng và kích hoạt cascade model dự phòng.
- **RAG Phân quyền & Phòng thủ Zero-Trust**: Trích xuất tri thức tài liệu theo đúng môn học sinh viên đã ghi danh, miễn nhiễm $100\%$ trước các nỗ lực Prompt Injection nhằm khai thác thông tin CSDL hoặc danh sách người dùng.

---

## 2. Kiến trúc Kỹ thuật & Bảng Điều hướng Sơ đồ

Hệ thống triển khai theo mô hình **Modular Monolith** kết hợp nguyên tắc phân tách triệt để giữa tầng xử lý nghiệp vụ backend (Python Flask Headless) và tầng hiển thị giao diện (Single-DOM SPA Vanilla JS).

```
   ┌─────────────────────────────────────────────────────────────────┐
   │                  CLIENT PRESENTATION LAYER                      │
   │      Single-DOM Web SPA (Warm Editorial / Cisco NetAcad)        │
   │               External REST API Clients (JWT)                   │
   └────────────────────────────────┬────────────────────────────────┘
                                    │ HTTP / JSON
   ┌────────────────────────────────▼────────────────────────────────┐
   │                  GATEWAY & SECURITY BOUNDARY                    │
   │      Reverse Proxy (Caddy / HTTPS) • Session Cookie + CSRF      │
   └────────────────────────────────┬────────────────────────────────┘
                                    │
   ┌────────────────────────────────▼────────────────────────────────┐
   │                  FLASK MODULAR MONOLITH CORE                    │
   │  ┌─────────────────────────┐       ┌─────────────────────────┐  │
   │  │   Phân hệ Học vụ (LMS)  │       │  Động cơ Khảo thí Server│  │
   │  ├─────────────────────────┤       ├─────────────────────────┤  │
   │  │   Trợ lý AI Bạch Tuộc   │       │  Vận hành & Phân quyền  │  │
   │  └─────────────────────────┘       └─────────────────────────┘  │
   └────────────────────────────────┬────────────────────────────────┘
                                    │
   ┌────────────────────────────────▼────────────────────────────────┐
   │                  INFRASTRUCTURE & PERSISTENCE                   │
   │      MS SQL Server 2022 (77 Bảng) • ClamAV Fail-Closed          │
   │           Google Gemini Cloud API • Host Telemetry Bridge       │
   └─────────────────────────────────────────────────────────────────┘
```

Bốn sơ đồ luồng dữ liệu chuyên sâu được xây dựng độc lập dạng HTML tương tác, hỗ trợ thu phóng và tra cứu chi tiết:

| Sơ đồ Nghiệp vụ | Trọng tâm Kiến trúc & Luồng Dữ liệu | Tài liệu Trực quan |
|:---|:---|:---:|
| **Kiến trúc Tổng thể** | Mô hình 4 tầng phân tách: Client SPA $\leftrightarrow$ Gateway Proxy $\leftrightarrow$ Flask Modular Monolith $\leftrightarrow$ Docker MSSQL & ClamAV | [docs/diagrams/system-architecture.html](docs/diagrams/system-architecture.html) |
| **Phân quyền Quản trị** | Quy trình phân cấp 5 nhóm quyền Admin phụ, hàng đợi kiểm duyệt học vụ và quy trình khôi phục CSDL live | [docs/diagrams/admin-workflow.html](docs/diagrams/admin-workflow.html) |
| **Soạn giảng & Khảo thí** | Chu trình 4 bước: Thiết lập môn học $\to$ Biên soạn bài giảng / bóc tách Word $\to$ Đệ trình phê duyệt $\to$ Khảo thí & Sổ điểm | [docs/diagrams/instructor-workflow.html](docs/diagrams/instructor-workflow.html) |
| **Học tập & Bàn thi** | Luồng sinh viên: Ghi danh DAG $\to$ Bàn học Cisco 3 cột $\to$ Video Anti-Seek $\to$ Khóa tab Single Lease $\to$ Chứng nhận | [docs/diagrams/student-workflow.html](docs/diagrams/student-workflow.html) |

---

## 3. Hướng dẫn Khởi tạo & Vận hành (Docker)

Toàn bộ hệ thống được đóng gói tiêu chuẩn sản xuất. Cơ sở dữ liệu mặc định và duy nhất của nền tảng là **Microsoft SQL Server 2022** vận hành trong Docker container.

### 3.1. Các bước Khởi chạy Cụm Dịch vụ

```bash
# 1. Tạo tệp cấu hình môi trường từ mẫu chuẩn
cp .env.example .env

# 2. Khởi chạy toàn bộ cụm 5 container (Web, Worker, SQL Server 2022, ClamAV, Caddy Proxy)
docker compose up -d --build

# 3. Kiểm tra trạng thái hoạt động của các container
docker compose ps
```

Sau khi các container đạt trạng thái `healthy`, truy cập giao diện hệ thống tại: **`http://localhost:5000`**

### 3.2. Khởi tạo Dữ liệu Nền tảng (Bootstrap Data)

Thực thi các lệnh sau bên trong container web để nạp dữ liệu phân quyền và tài khoản mẫu:

```bash
# 1. Nạp danh mục quyền chuẩn (STUDENT, INSTRUCTOR, ADMIN) và tài khoản Root Admin
docker compose exec web flask seed-baseline

# 2. (Tùy chọn) Nạp dữ liệu mẫu đầy đủ (Khóa học, Bài giảng, Giảng viên, Sinh viên, Đề thi)
docker compose exec web flask seed-demo
```

### 3.3. Tài khoản Đăng nhập Thử nghiệm

Sau khi nạp dữ liệu mẫu, hệ thống cung cấp sẵn các tài khoản thử nghiệm tương ứng từng vai trò:

| Vai trò | Tài khoản Đăng nhập | Mật khẩu Mặc định | Quyền hạn Chính |
|:---|:---|:---|:---|
| **Tổng Quản trị (Admin)** | `admin@pwd301.local` | `Admin@123456` | Toàn quyền quản trị, phân quyền sub-roles, khôi phục CSDL |
| **Giảng viên (Instructor)** | `instructor1@pwd301.local` | `Admin@123456` | Quản lý khóa học phụ trách, soạn bài giảng, bóc tách đề thi |
| **Học viên (Student)** | `student1@pwd301.local` | `Admin@123456` | Ghi danh môn học, học tập trên console 3 cột, làm bài thi |

### 3.4. Các Lệnh Quản trị & Bảo trì CSDL

- **Làm sạch CSDL về trạng thái rỗng chuẩn (Clean Database)**:
  Xóa sạch toàn bộ dữ liệu thử nghiệm và tệp đính kèm, bảo toàn cấu trúc 77 bảng và nạp lại Baseline Roles:
  ```bash
  docker compose exec web flask clean-db --yes
  ```

- **Đặt lại CSDL và nạp mới dữ liệu Demo (Reset & Re-seed)**:
  ```bash
  docker compose exec web flask reset-db --seed-demo --yes
  ```

---

## 4. Chiến lược Kiểm thử & Đảm bảo Chất lượng

Dự án tuân thủ nghiêm ngặt phương pháp phát triển hướng kiểm thử (TDD) với tỷ lệ bao phủ toàn diện trên toàn bộ các tầng xử lý:

| Hạng mục Kiểm thử | Phạm vi Kiểm tra & Thực thi | Công cụ / Framework | Kết quả Thực tế |
|:---|:---|:---|:---:|
| **Unit Tests** | Logic Khóa học, Exam Studio, Tái chấm điểm, Telemetry, AI Multi-Key Pool | `pytest`, `unittest` | $100\%$ PASS |
| **API Integration** | Kiểm tra toàn trình các Endpoints Auth, Student, Instructor, Admin | `pytest-flask`, `requests` | $100\%$ PASS |
| **Security & Auditing** | Chống rò rỉ dữ liệu AI, chống IDOR, CSRF Token, Fail-Closed ClamAV | `pytest tests/test_security/` | $100\%$ PASS |
| **End-to-End (E2E)** | Mô phỏng toàn trình chu trình Sinh viên, Giảng viên và Khảo thí | `test_student_lifecycle_e2e.py` | $100\%$ PASS |
| **Static Code Quality** | Rà soát chuẩn PEP8, kiểu dữ liệu, lỗ hổng an ninh mã nguồn | `ruff check src tests` | $0\text{ error}$ |
| **Frontend Syntax** | Thẩm định cú pháp toàn bộ các tệp JavaScript giao diện SPA | `node --check` | $0\text{ error}$ |
| **Repo Contract Check** | Thẩm định 77 bảng DDL SQL Server, Markdown fences, file contract | `python scripts/repo_check.py` | $100\%$ PASS |

### Lệnh Thực thi Bộ Kiểm thử Tự động
- **Trên Windows PowerShell**: `./scripts/verify.ps1`
- **Trên Linux / macOS**: `./scripts/verify.sh`
- **Chạy riêng bộ kiểm thử Pytest**: `pytest -v` *(Thu thập và kiểm tra $1\,530+\text{ test cases}$)*

---

## 5. Đối chiếu Chuẩn Học thuật & Ma trận Rubric Topic 9

Hệ thống được phát triển bám sát và hiện thực hóa đầy đủ $100\%$ các yêu cầu của đề tài **Topic 9 — Online Course Management Platform** thuộc học phần **PWD301 (Web Application Development with Python & Flask)**, đáp ứng các tiêu chuẩn kỹ thuật phần mềm doanh nghiệp:

| Tiêu chí Đề tài Topic 9 | Hiện thực hóa Kỹ thuật PWD301 | Trạng thái Tuân thủ |
|:---|:---|:---:|
| **Framework Flask (Python 3.11+)** | Kiến trúc Headless Modular Monolith phân tầng Controller, Service và Model chuẩn hóa | $100\%$ Đạt chuẩn |
| **CSDL Microsoft SQL Server** | Kiến trúc $77 \text{ bảng quan hệ}$ chuẩn hóa trên SQL Server 2022, khóa chính BigInt, Public UUID, `ROWVERSION` OCC | $77 \gg 4 \text{ bảng}$ ($100\%$) |
| **Quản lý Khóa học & Bài giảng** | Cây bài giảng Notion-style, kiểm tra tiên quyết DAG, video Anti-Seek, tài liệu quét ClamAV, duyệt Diff Side-by-Side | $100\%$ Đạt chuẩn |
| **Khảo thí Trắc nghiệm Khách quan** | Exam Studio bóc tách Word (`.docx`), chia điểm tự động $P = \frac{100}{N}$, chống gian lận Fullscreen, khóa tab Single Lease | $100\%$ Đạt chuẩn |
| **Phân quyền Tối thiểu 3 Vai trò** | Hệ thống RBAC 3 vai trò chuẩn (`STUDENT`, `INSTRUCTOR`, `ADMIN`) kèm $5 \text{ nhóm quyền phụ (Sub-roles)}$ kiểm soát cấp đối tượng | $100\%$ Đạt chuẩn |
| **Giao diện Động & AJAX / Fetch** | Nền tảng Single-DOM SPA Warm Editorial, tải vi mô $\le 100\,\text{ms}$, toàn bộ thao tác giao tiếp REST API JSON chuẩn hóa | $100\%$ Đạt chuẩn |
| **Tích hợp Trí tuệ Nhân tạo AI** | Cụm trợ lý Bạch Tuộc AI, Multi-Key Pool xoay vòng khóa API, fallback cascade model, RAG theo môn học, phản hồi $\le 5\,\text{s}$ | $100\%$ Đạt chuẩn |
| **Đóng gói Docker & Vận hành** | Đóng gói toàn bộ cụm container (Web, Worker, SQL Server 2022, ClamAV, Caddy) khởi động đồng bộ bằng Docker Compose | $100\%$ Đạt chuẩn |
| **Kiểm thử & Đảm bảo Chất lượng** | Áp dụng TDD nghiêm ngặt với $1\,530+\text{ automated tests}$, CI contract check tự động, Ruff linter $0\text{ error}$ | $1\,530+\text{ PASS}$ ($100\%$) |

---

## 6. Tài liệu Kỹ thuật & Đội ngũ Phát triển

### 6.1. Tra cứu Tài liệu Kỹ thuật Chuyên sâu

- **Đặc tả Hệ thống Toàn diện**: [`docs/system/PWD301_SYSTEM_SPECIFICATION/`](docs/system/PWD301_SYSTEM_SPECIFICATION/)
  - [Đặc tả Kiến trúc Hệ thống](docs/system/PWD301_SYSTEM_SPECIFICATION/04_SYSTEM_ARCHITECTURE.md)
  - [Danh mục 73 Quy tắc Nghiệp vụ (Business Rules)](docs/system/PWD301_SYSTEM_SPECIFICATION/business/01_BUSINESS_RULE_CATALOG.md)
  - [Mô hình Máy trạng thái (State Machines)](docs/system/PWD301_SYSTEM_SPECIFICATION/state-machines/01_STATE_MACHINE_CATALOG.md)
  - [Danh mục Quy tắc Bất biến Bắt buộc](docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md)
- **Đặc tả Cơ sở Dữ liệu Chuẩn mực**: [`docs/database/PWD301_DATABASE_ARCHITECTURE/`](docs/database/PWD301_DATABASE_ARCHITECTURE/)
  - [Tài liệu Tổng quan CSDL & Sơ đồ ERD](docs/database/PWD301_DATABASE_ARCHITECTURE/03_ERD.md)
  - [Mã nguồn 77 Tệp DDL SQL Server Chuẩn](docs/database/PWD301_DATABASE_ARCHITECTURE/sql/)
- **Kho Sơ đồ Tương tác Độc lập**: [`docs/diagrams/`](docs/diagrams/)
  - [Sơ đồ Kiến trúc Hệ thống (HTML)](docs/diagrams/system-architecture.html)
  - [Sơ đồ Workflow Admin & Sub-admins (HTML)](docs/diagrams/admin-workflow.html)
  - [Sơ đồ Workflow Giảng viên (HTML)](docs/diagrams/instructor-workflow.html)
  - [Sơ đồ Workflow Học viên (HTML)](docs/diagrams/student-workflow.html)

### 6.2. Đội ngũ Phát triển (Project Team)

Dự án **PWD301 LMS** được nghiên cứu và phát triển bởi nhóm sinh viên thực hiện đồ án môn học **PWD301 — Web Application Development with Python & Flask**:

| STT | Họ và Tên | Email Liên hệ | Tài khoản GitHub |
|:---:|:---|:---|:---|
| 1 | **Đặng Lý Quân** | `danglyquan@gmail.com` | — |
| 2 | **Lại Vĩnh Phú** | `vinhphu2020.nt@gmail.com` | — |
| 3 | **Phạm Nguyễn Hoàng Phúc** | `tqtphamnguyenhoangphuc@gmail.com` | [`@concatapchay123`](https://github.com/concatapchay123) |
| 4 | **Trần Đặng Hữu Thắng** | `callmewin06@gmail.com` | [`@callmewin06-create`](https://github.com/callmewin06-create) |

Mã nguồn được phát hành theo giấy phép [MIT License](LICENSE).
