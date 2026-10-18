# TASK-PRODUCTION-DATABASE-CLEANUP: Làm Sạch & Xóa Cứng Toàn Bộ Dữ Liệu Rác Chuẩn Bị Triển Khai Production
# Historical reference: TASK-CLONE-REMEDIATION, TASK-100

> Workflow authority: [approved replacement contract](../docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/WORKFLOW_SUPERSESSION.md). Historical task completion is not proof of current implementation.

**Status:** COMPLETED  
**Started At:** 2026-10-18  
**Completed At:** 2026-10-18  
**Scope:**
1. **Phân tích Thực địa Dữ liệu Rác (Discovery & Audit)**:
   - Rà soát toàn bộ 78 bảng trong cơ sở dữ liệu Microsoft SQL Server `PWD301`.
   - Rà soát cơ sở dữ liệu SQLite dev (`src/instance/test_sqlite.db`), bộ nhớ cache rate limits (`src/instance/rate_limits`), và tệp rác trong storage (`storage/`, `quarantine/`, `exports/`).
2. **Xây dựng Công cụ Làm sạch Đẳng công (Production Clean Tooling)**:
   - Xây dựng CLI command `flask clean-db` trong `src/pwd301/cli.py` với các cờ điều khiển linh hoạt (`--keep-baseline`, `--clean-storage`, `--yes`).
   - Xây dựng kịch bản độc lập `scripts/clean_database.py` hỗ trợ cả SQL Server và SQLite, xử lý triệt để Foreign Key constraints và IDENTITY reseed.
3. **Thực thi Xóa cứng Dữ liệu Rác Thực tế (Execution)**:
   - Thực hiện vô hiệu hóa tạm thời constraints, xóa cứng 100% dữ liệu thử nghiệm trong toàn bộ 77 bảng nghiệp vụ (Courses, Lessons, Questions, Assessments, Attempts, Enrollments, Audit, Notifications, File Blobs, Test Users, Playback Receipts, AI Chats...).
   - Bảo toàn bảng di trú `alembic_version` (1 bản ghi) để hệ thống giữ nguyên trạng thái schema version.
   - Tái thiết lập dữ liệu nền tảng (Baseline Data) gồm 3 vai trò hệ thống (`STUDENT`, `INSTRUCTOR`, `ADMIN`) và 1 tài khoản Quản trị viên gốc (`admin@pwd301.local`), đảm bảo hệ thống có thể khởi động ngay và sẵn sàng bàn giao cho người quản trị thật.
   - Dọn sạch tệp đệm thử nghiệm trong `storage/blobs/`, `storage/sample_*.mp4`, `quarantine/upload_*.tmp`, `exports/`, và tệp SQLite thử nghiệm cục bộ.
4. **Xác minh Thực nghiệm Toàn diện (Anti-Hallucination Verification)**:
   - Kiểm tra số lượng bản ghi của toàn bộ 78 bảng CSDL, lập bảng đối soát Before vs After.
   - Chạy `repo_check.py` và kiểm thử hệ thống để đảm bảo tính toàn vẹn của mã nguồn.
   - Thử nghiệm đăng nhập tài khoản quản trị và kiểm tra idempotency của `seed-baseline`.

---

## Danh mục Công việc (Checklist)
- [x] 1. Khảo sát chi tiết số lượng bản ghi hiện hữu trên 78 bảng của SQL Server `PWD301` và các thư mục lưu trữ.
- [x] 2. Phát triển module `scripts/clean_database.py` và bổ sung lệnh `flask clean-db` vào `src/pwd301/cli.py`.
- [x] 3. Thực thi làm sạch CSDL SQL Server và dọn dẹp các tệp lưu trữ rác.
- [x] 4. Tái lập Baseline Roles và Root Admin chuẩn mực phục vụ production.
- [x] 5. Kiểm tra đối soát số lượng bản ghi (0 rác, 100% sạch sẽ).
- [x] 6. Chạy kiểm tra tĩnh và regression test (`repo_check.py`, tests).
- [x] 7. Làm sạch toàn diện môi trường Docker (`pwd301_web`, `pwd301_db`), xóa sạch 3,346 bản ghi test và 3,010 tệp lưu trữ volume.
- [x] 8. Drop triệt để toàn bộ 32 cơ sở dữ liệu thử nghiệm `pwd301_test_*` trên cả Windows SQL Server và Docker SQL Server.
- [x] 9. Xác thực trực tiếp qua HTTP endpoint `http://127.0.0.1:5000/api/courses` trả về 0 khóa học (`items: []`).
- [x] 10. Báo cáo hoàn thành và cung cấp hướng dẫn vận hành cho người quản trị.
