## 2026-09-16T05:17:04Z

# Project Orchestrator 5 Dispatch

Working Directory: E:\PWD301\.agents\teamwork_preview_orchestrator_5
Original Request File: E:\PWD301\.agents\ORIGINAL_REQUEST.md (header ## 2026-09-16T05:16:14Z)

Mission:
Tích hợp và chuyển đổi toàn diện hệ thống frontend mới từ 33 màn hình Stitch (frontend-preview/) vào hệ thống Flask Web (src/pwd301/templates, src/pwd301/static), bốc tách data binding và backend context từ frontend cũ, bảo toàn 100% logic xác thực (Flask session, CSRF, RBAC, Timezone, i18n) và đảm bảo các luồng nghiệp vụ Học viên, Giảng viên, Quản trị viên hoạt động trơn tru, vượt qua toàn bộ test suite.

Key Objectives:
R1. Hợp nhất Kiến trúc Giao diện & Core App Shell (Tailwind & Design Tokens)
R2. Tích hợp Chi tiết Cổng Học viên (Student Portal)
R3. Tích hợp Chi tiết Cổng Giảng viên (Instructor Portal)
R4. Tích hợp Chi tiết Cổng Quản trị & Xác thực (Admin & Auth)
R5. Bảo toàn Invariants, An ninh & Tương thích Backend

Acceptance Criteria:
- Tất cả các route web của Student, Instructor, Admin, Auth render thành công với giao diện mới, không lỗi Jinja syntax (UndefinedError, BuildError).
- Tailwind CSS nạp chuẩn xác, không bị xung đột với các logic JavaScript của hệ thống (app_shell.js, theme.js, motion.js).
- Đầy đủ các tương tác thời gian thực: Đồng hồ đếm ngược phòng thi UTC, tự động lưu câu trả lời bài thi (autosave), lọc câu hỏi ngân hàng đề, chấm bài tự luận 50/50 canvas.
- Toàn bộ bộ kiểm thử tự động của dự án (pytest) chạy vượt qua 100%.
- ruff check và ruff format --check đạt 0 cảnh báo.
- mypy src đạt 0 lỗi.
- python scripts/repo_check.py vượt qua tất cả bài kiểm tra.
