# GOAL-CLEAN-WIPE-REDEPLOY: XÓA SẠCH DỰ ÁN CŨ, PURGE DATABASE & ĐỒNG BỘ TOÀN DIỆN PHIÊN BẢN HIỆN TẠI LÊN VPS

> Workflow authority: [WORKFLOW_SUPERSESSION.md](../docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/WORKFLOW_SUPERSESSION.md). Historical task completion is not proof of current implementation.

**Status:** COMPLETED  
**Goal Mode:** FINISHED (/goal)  
**Target VPS:** `103.28.33.20` (Ubuntu 24.04 LTS, 4 vCPU, 8GB RAM)  
**Completed At:** 2026-10-21 11:16 (Asia/Ho_Chi_Minh)  

---

## 1. Mục Tiêu Thực Hiện (Scope & Deliverables)
1. **Xóa sạch toàn bộ dự án cũ và cơ sở dữ liệu trên VPS**:
   - Dừng và xóa toàn bộ container Docker (`pwd301-production-*`).
   - Xóa bỏ triệt để toàn bộ volume dữ liệu MSSQL (`pwd301-production_sql`), file lưu trữ (`pwd301-production_storage`), backups, quarantine, certs.
   - Xóa sạch thư mục mã nguồn `/opt/apps/pwd301`.
   - Prune toàn bộ docker volume và network. Xác nhận VPS sạch 100%.
2. **Đóng gói và truyền tải phiên bản hiện tại (TASK-112)**:
   - Đóng gói toàn bộ mã nguồn sạch từ `e:\PWD301`.
   - Tải lên VPS tại `/opt/apps/` và giải nén vào `/opt/apps/pwd301`.
3. **Cấu hình môi trường Production sạch mới**:
   - Thiết lập `.env.production` với các secrets và chuỗi kết nối MSSQL mới (tách biệt tài khoản `sa`, `pwd301_migrator`, `pwd301_app`).
   - Cấu hình `deploy/Caddyfile` hỗ trợ cả HTTP (`:80`) và HTTPS (`:443`) với `default_sni 103.28.33.20`.
4. **Biên dịch & Khởi tạo CSDL mới (Fresh Database Bootstrap)**:
   - Build image `pwd301:release` từ mã nguồn mới.
   - Khởi tạo database mới `PWD301`, thực thi 100% migrations Alembic (21 migrations), khởi tạo roles và admin.
   - Nạp khóa học an ninh mạng BHE501 (5 chương, 60 bài học, miniquiz, file assets PDF, bài thi).
5. **Khởi chạy và Xác minh Thực nghiệm (Anti-Hallucination Verification)**:
   - Khởi chạy toàn bộ cụm container (`web`, `worker`, `db`, `clamav`, `proxy`).
   - Xác minh liveness probe, course catalog, student login, UI assets, RAM/CPU telemetry.

---

## 2. Danh mục Công việc (Checklist)
- [x] 1. Dừng toàn bộ container và xóa sạch volume CSDL, volume lưu trữ, thư mục `/opt/apps/pwd301`.
- [x] 2. Xác minh VPS sạch sẽ hoàn toàn (0 containers, 0 volumes, `/opt/apps` trống).
- [x] 3. Đóng gói mã nguồn phiên bản hiện tại từ `e:\PWD301` và tải lên VPS.
- [x] 4. Giải nén vào `/opt/apps/pwd301` và thiết lập `.env.production`, `Caddyfile`.
- [x] 5. Rebuild Docker image `pwd301:release` và thực thi release bootstrap CSDL mới.
- [x] 6. Nạp dữ liệu khóa học BHE501 vào CSDL mới (60 bài học, 5 chương, miniquiz, ebooks PDF).
- [x] 7. Khởi động toàn bộ cụm 5 container production (`docker compose up -d`).
- [x] 8. Xác minh thực nghiệm toàn bộ endpoints (HTTP, HTTPS, UI, API, Login, Telemetry).
- [x] 9. Hoàn thành mục tiêu `/goal` và công bố báo cáo nghiệm thu.

---

## 3. Bằng chứng Thực nghiệm (Empirical Verification Evidence)
- **Container Health**:
  - `pwd301-production-clamav-1`: `Up (healthy)`
  - `pwd301-production-db-1`: `Up (healthy)` (MSSQL 2022)
  - `pwd301-production-proxy-1`: `Up` (Caddy Cổng 80 và 443)
  - `pwd301-production-web-1`: `Up (healthy)` (Gunicorn 5000)
  - `pwd301-production-worker-1`: `Up (healthy)`
- **Liveness Probe**: `GET http://103.28.33.20/health` & `GET https://103.28.33.20/health` -> HTTP 200 `{"status": "ok", "probe": "liveness", "env": "production"}`
- **Web UI Single-Page Application**: `GET http://103.28.33.20/` -> HTTP 200, HTML Title: `PPTQ LMS - Học Tập Và Bài Thi`
- **Course Catalog**: `GET http://103.28.33.20/api/courses` -> HTTP 200, Course `BHE501` ("Kỹ Thuật An Ninh Mạng Mũ Đen: Tor, Dark Web, Lập Trình Khai Thác Rust & Pentest GraphQL")
- **Authentication**: `POST https://103.28.33.20/auth/login` -> HTTP 200, `Học Viên Trần Minh Quân` (`student1@pwd301.local`)
- **Student Dashboard**: `GET https://103.28.33.20/student/courses` -> HTTP 200, Enrollment active cho BHE501 (1 enrollment)
- **VPS Telemetry**: RAM Available: 5.1 GiB / 7.8 GiB, Swap: 1.4 MiB / 11 GiB, Ổ cứng còn trống 22 GB (46% used), CPU < 2%.
