# Hồ Sơ Tài Liệu Hệ Thống PWD301 LMS

Thư mục này lưu trữ toàn bộ hệ thống tài liệu đặc tả, kiến trúc kỹ thuật và báo cáo nghiệm thu của Dự án Nền tảng Quản trị & Khảo thí Khóa học Trực tuyến PPTQ LMS.

---

## 1. Tài liệu Đặc tả & Kiến trúc Cốt lõi (Canonical Specifications)

- **Đặc tả Hệ thống Toàn diện**: [`system/PWD301_SYSTEM_SPECIFICATION/`](system/PWD301_SYSTEM_SPECIFICATION/README.md)
  - Hồ sơ yêu cầu nghiệp vụ (Business Rules Catalog).
  - Kiến trúc phân quyền RBAC đa vai trò (Admin, Giảng viên, Học viên).
  - Cơ chế mã hóa truyền tải Hybrid (RSA-OAEP 2048 + AES-GCM 256) và băm mật khẩu Argon2id.
  - Động cơ bảo vệ bản quyền bài giảng HLS DRM và chống gian lận thi cử thời gian thực.
  - Tích hợp Trợ lý Trí tuệ Nhân tạo Bạch tuộc (Octopus AI) và Cổng thanh toán VietQR / PayOS.
- **Kiến trúc & Lược đồ Cơ sở Dữ liệu**: [`database/PWD301_DATABASE_ARCHITECTURE/`](database/PWD301_DATABASE_ARCHITECTURE/README.md)
  - Biểu đồ thực thể liên kết (Entity Relationship Diagram - ERD) 71 bảng CSDL.
  - Hợp đồng DDL SQL Server chuẩn hóa và quy tắc toàn vẹn dữ liệu cross-domain.
- **Biểu đồ Kiến trúc & Luồng Dữ liệu**: [`diagrams/`](diagrams/)
  - Sơ đồ kiến trúc tầng ứng dụng, luồng bảo mật và biểu đồ trạng thái bài thi.

---

## 2. Báo Cáo Nghiệm Thu & Thuyết Trình Đồ Án (Deliverables)

- **Thư mục Báo cáo Nghiệm thu**: [`deliverables/`](deliverables/)
  - `PPTQ_LMS_FINAL_REPORT.md` / `PPTQ_LMS_FINAL_REPORT.docx`: Báo cáo tổng kết đồ án toàn diện nộp Hội đồng.
  - `thuyet_trinh.docx`: Đề cương nội dung thuyết minh bảo vệ đồ án.
  - `DEMO_PRESENTATION_SCRIPT.md`: Kịch bản demo thực chiến các tính năng nổi bật và phòng thủ an ninh.

---

## 3. Hướng Dẫn Vận Hành & Tiêu Chuẩn Kỹ Thuật

- **Hướng dẫn Triển khai Hệ thống**: [`DEPLOYMENT.md`](DEPLOYMENT.md)
  - Cấu hình đóng gói Docker Multi-stage, Caddy Reverse Proxy, SQL Server 2022 và ClamAV daemon.
- **Quy chuẩn Lập trình & An toàn Mã nguồn**: [`CODING_STANDARDS.md`](CODING_STANDARDS.md)
  - Quy chuẩn Clean Architecture, chuẩn REST API JSON và kiểm soát an ninh OWASP.
