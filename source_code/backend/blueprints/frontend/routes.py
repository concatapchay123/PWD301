"""Route handlers for serving the PWD301 LMS Web SPA and UI assets."""

from __future__ import annotations

import mimetypes
import os

from flask import (
    Response,
    abort,
    current_app,
    jsonify,
    make_response,
    request,
    send_file,
)

import backend
from backend.blueprints.frontend import frontend_bp


def _get_frontend_dir() -> str:
    """Resolve the absolute path to the repository frontend directory."""
    configured = current_app.config.get("FRONTEND_DIR")
    if configured and os.path.isdir(configured):
        return os.path.abspath(configured)

    env_dir = os.environ.get("FRONTEND_DIR")
    if env_dir and os.path.isdir(env_dir):
        return os.path.abspath(env_dir)

    this_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.abspath(os.path.join(this_dir, "..", "..", "..", "frontend")),
        os.path.abspath(os.path.join(this_dir, "..", "..", "..", "source_code", "frontend")),
        os.path.abspath(os.path.join(this_dir, "..", "..", "..", "..", "frontend")),
        "/app/frontend",
        "/app/source_code/frontend",
        "/var/www/frontend",
    ]
    for candidate in candidates:
        if os.path.isdir(candidate):
            return candidate

    return candidates[0]


SCREEN_METADATA: dict[str, dict[str, str]] = {
    "pwd301_auth_account_lifecycle_variant_1_focused_card_interactive_inspector": {
        "title": "Xác thực & Vòng đời Tài khoản",
        "role": "PUBLIC",
        "route": "#/auth",
        "category": "Authentication",
    },
    "pwd301_student_dashboard_variant_1_action_centric_master_flyout_notification_hub": {
        "title": "Bàn làm việc Học viên (Dashboard)",
        "role": "STUDENT",
        "route": "#/student/dashboard",
        "category": "Student Learning",
    },
    "pwd301_public_catalog_detail_variant_1_split_master_detail": {
        "title": "Danh mục Khóa học Công khai",
        "role": "PUBLIC",
        "route": "#/student/catalog",
        "category": "Course Catalog",
    },
    "pwd301_public_catalog_detail_variant_2_full_page_academic_dossier": {
        "title": "Hồ sơ Học thuật Chi tiết Khóa học",
        "role": "PUBLIC",
        "route": "#/student/catalog/detail",
        "category": "Course Catalog",
    },
    "pwd301_student_course_hub_variant_1_integrated_master_workspace_contextual_tabs": {
        "title": "Không gian Học tập & Khóa học của tôi",
        "role": "STUDENT",
        "route": "#/student/courses",
        "category": "Student Learning",
    },
    "pwd301_extended_course_detail_variant_2_interactive_module_lesson_studio_bar": {
        "title": "Đề cương Chi tiết & Tiến độ Bài học",
        "role": "STUDENT",
        "route": "#/student/courses/syllabus",
        "category": "Student Learning",
    },
    "pwd301_lesson_reader_variant_1_3_column_academic_console_resource_vault": {
        "title": "Phòng đọc Bài giảng 3 Cột (Resource Vault)",
        "role": "STUDENT",
        "route": "#/student/lessons/reader",
        "category": "Student Learning",
    },
    "pwd301_assessment_hub_waiting_room_variant_2_dedicated_focus_waiting_room": {
        "title": "Phòng chờ Khảo thí Tập trung (Đếm ngược UTC)",
        "role": "STUDENT",
        "route": "#/student/assessments/waiting-room",
        "category": "Assessment Hub",
    },
    "pwd301_assessment_attempt_variant_1_master_exam_console_contextual_navigator": {
        "title": "Bàn làm bài Khảo thí Trực tuyến (Master Console)",
        "role": "STUDENT",
        "route": "#/student/assessments/attempt",
        "category": "Assessment Hub",
    },
    "pwd301_quiz_mini_test_results_variant_1_chu_n_i_chi_u_1_1_theo_m_u": {
        "title": "Kết quả Khảo thí Mini-Test (Đối chiếu 1:1)",
        "role": "STUDENT",
        "route": "#/student/assessments/quiz-results",
        "category": "Assessment Hub",
    },
    "pwd301_midterm_assessment_results_clean_minimalist_review_detail_drawer_2": {
        "title": "Kết quả Thi Giữa kỳ & Chi tiết Đề mục (Drawer 2)",
        "role": "STUDENT",
        "route": "#/student/assessments/results",
        "category": "Assessment Hub",
    },
    "pwd301_midterm_assessment_results_clean_minimalist_review_detail_drawer_1": {
        "title": "Kết quả Thi Giữa kỳ & Chi tiết Đề mục (Drawer 1)",
        "role": "STUDENT",
        "route": "#/student/assessments/results-alt",
        "category": "Assessment Hub",
    },
    "pwd301_student_contextual_ai_clean_minimalist_academic_workspace": {
        "title": "Trợ lý AI Học vụ (Academic Workspace)",
        "role": "STUDENT",
        "route": "#/student/ai-assistant",
        "category": "AI Learning",
    },
    "pwd301_instructor_dashboard_clean_minimalist_focus": {
        "title": "Bàn làm việc Giảng viên (Focus Dashboard)",
        "role": "INSTRUCTOR",
        "route": "#/instructor/dashboard",
        "category": "Instructor Workspace",
    },
    "pwd301_instructor_courses_variant_2_master_operations_table_detailed_provenance": {
        "title": "Quản lý Khóa học & Bảng vận hành Giảng viên",
        "role": "INSTRUCTOR",
        "route": "#/instructor/courses",
        "category": "Instructor Workspace",
    },
    "pwd301_instructor_workspace_variant_3_carbon_governance_centric_academic_console": {
        "title": "Bàn Điều khiển Học thuật Giảng viên (Carbon Governance)",
        "role": "INSTRUCTOR",
        "route": "#/instructor/workspace",
        "category": "Instructor Workspace",
    },
    "pwd301_lesson_authoring_tr_nh_so_n_th_o_b_i_gi_ng_tr_c_quan_th_n_thi_n_low_tech": {
        "title": "Trình Soạn thảo Bài giảng Trực quan Low-Tech",
        "role": "INSTRUCTOR",
        "route": "#/instructor/lessons/authoring",
        "category": "Curriculum Authoring",
    },
    "pwd301_exam_method_selector_variant_1_split_master_selector_smart_dropzone": {
        "title": "Bộ chọn Phương thức Tạo Đề thi & Smart Dropzone",
        "role": "INSTRUCTOR",
        "route": "#/instructor/exams/method-selector",
        "category": "Exam Authoring",
    },
    "pwd301_exam_general_config_bi_n_th_3_modular_wizard_academic_governance_matrix": {
        "title": "Cấu hình Tổng thể Đề thi (Ma trận Học thuật)",
        "role": "INSTRUCTOR",
        "route": "#/instructor/exams/general-config",
        "category": "Exam Authoring",
    },
    "pwd301_exam_detailed_config_bi_n_th_1_chu_n_azota_tr_c_quan_d_d_ng_cho_gi_ng_vi": {
        "title": "Cấu hình Chi tiết Đề thi (Chuẩn Azota Trực quan)",
        "role": "INSTRUCTOR",
        "route": "#/instructor/exams/detailed-config",
        "category": "Exam Authoring",
    },
    "pwd301_exam_preview_editor_bi_n_th_1_split_view_50_50_chu_n_azota_raw_syntax": {
        "title": "Trình Soạn thảo Split-View 50/50 (Chuẩn Azota Raw Syntax)",
        "role": "INSTRUCTOR",
        "route": "#/instructor/exams/preview-editor",
        "category": "Exam Authoring",
    },
    "pwd301_exam_validation_bi_n_th_1_modal_th_m_nh_c_ch_kh_a_kh_c_ph_c_l_i_b_t_bu_c": {
        "title": "Modal Thẩm định & Khắc phục Lỗi Bắt buộc Đề thi",
        "role": "INSTRUCTOR",
        "route": "#/instructor/exams/validation",
        "category": "Exam Authoring",
    },
    "pwd301_instructor_essay_grading_variant_1_split_canvas_50_50_focus_studio": {
        "title": "Studio Chấm thi Tự luận Split-Canvas 50/50",
        "role": "INSTRUCTOR",
        "route": "#/instructor/grading",
        "category": "Grading Studio",
    },
    "pwd301_admin_governance_variant_3_modular_tabbed_command_center_academic": {
        "title": "Trung tâm Điều hành & Quản trị Học vụ (Admin Command Center)",
        "role": "ADMIN",
        "route": "#/admin/governance",
        "category": "Admin Governance",
    },
    "pwd301_admin_operations_security_variant_2_split_operations_cockpit_active": {
        "title": "Cockpit Vận hành & Giám sát An ninh Máy chủ",
        "role": "ADMIN",
        "route": "#/admin/operations",
        "category": "Admin Operations",
    },
}




def _get_homepage_markdown() -> str:
    """Generate structured markdown representation of the PPTQ LMS platform for AI agents."""
    return (
        "# PPTQ LMS - Nền Tảng Học Trực Tuyến & Đào Tạo Khảo Thí Toàn Diện\n\n"
        "> Hệ thống đào tạo trực tuyến, tổ chức khóa học học thuật, bài thi chống gian lận và cấp chứng chỉ số chuẩn mực PWD301.\n\n"
        "## Giới thiệu Tổng quan\n"
        "PPTQ LMS (https://pptq.id.vn) là nền tảng quản trị học tập (Learning Management System) hiện đại, "
        "kết hợp trải nghiệm học tập đa phương tiện (video 16:9 DRM, tài liệu học tập phong phú), "
        "trung tâm khảo thí trực tuyến bảo mật cao (ngân hàng câu hỏi trắc nghiệm, Matching Board 2 cột, tự luận), "
        "cấp chứng chỉ số PDF xác thực tức thì và trợ lý học vụ thông minh 'Bạch tuộc trợ lí AI'.\n\n"
        "## Tính Năng Nền Tảng\n"
        "- **Không gian Học tập Tương tác**: Bài giảng video tỷ lệ chuẩn 16:9, tài liệu đính kèm phong phú (PDF, DOCX, XLSX, AutoCAD, 3D), ghi nhận tiến độ thời gian thực.\n"
        "- **Khảo thí & Giám sát Chống Gian lận**: Đa dạng câu hỏi thi, chấm điểm tự động và cơ chế Blackout Shield phát hiện mất tiêu điểm màn hình, mở DevTools, chia sẻ màn hình.\n"
        "- **Chứng chỉ Số & Đánh giá Chuẩn mực**: Tự động đánh giá điều kiện tốt nghiệp và phát hành chứng chỉ điện tử PDF có mã định danh xác thực.\n"
        "- **Trợ lý Học thuật Bạch tuộc AI**: Đồng hành giải đáp bài học, tóm tắt nội dung và định hướng học tập 24/7.\n"
        "- **Cổng Thanh toán Tự động**: Thanh toán học phí và nạp ví qua mã VietQR chuẩn xác, kích hoạt quyền học tập vĩnh viễn (Lifetime Enrollment).\n"
        "- **Kiến trúc Pure Headless REST API**: Kết nối linh hoạt cho Web SPA, ứng dụng di động và AI agents với bảo mật RSA-OAEP 2048 + AES-GCM 256.\n\n"
        "## When to Use This (Chỉ Dẫn Cho AI Agents)\n"
        "- **Best-fit Use Cases**: Tra cứu danh mục khóa học, xem đề cương chi tiết, tìm kiếm tài liệu học tập (PDF, Word, Excel, CAD, 3D), làm bài kiểm tra khảo thí bảo mật cao và xác thực chứng chỉ số đào tạo.\n"
        "- **How an Agent Should Call You**: Gửi tiêu đề HTTP Accept: text/markdown để nhận phản hồi Markdown tối ưu cho AI, hoặc gọi REST API /api/courses để lấy dữ liệu JSON có cấu trúc.\n"
        "- **When NOT to Use**: Không dùng cho các truy vấn web mở ngoài phạm vi đào tạo PPTQ LMS; không truy vấn điểm số học viên cá nhân khi chưa xác thực qua JWT/Session.\n"
        "- **Tài liệu hướng dẫn agent**: [llms.txt](https://pptq.id.vn/llms.txt)\n"
        "- **Tài liệu hệ thống đầy đủ**: [llms-full.txt](https://pptq.id.vn/llms-full.txt)\n"
        "- **Sơ đồ trang web**: [sitemap.xml](https://pptq.id.vn/sitemap.xml)\n"
        "- **API Catalog**: [REST API](https://pptq.id.vn/api)\n\n"
        "## Trang Thông Tin & Độ Tin Cậy (Trust Anchors)\n"
        "- [Giới thiệu về chúng tôi (About Us)](https://pptq.id.vn/about)\n"
        "- [Thông tin liên hệ & hỗ trợ (Contact)](https://pptq.id.vn/contact)\n"
        "- [Chính sách bảo mật (Privacy Policy)](https://pptq.id.vn/privacy)\n\n"
        "## Thông Tin Đơn Vị Vận Hành\n"
        "- **Tên đơn vị**: Hệ thống Đào tạo PPTQ LMS\n"
        "- **Hotline**: +84-908-667-141\n"
        "- **Email hỗ trợ**: admin@pptq.id.vn\n"
        "- **Địa chỉ**: Khu Công Nghệ Cao, Thành phố Thủ Đức, TP. Hồ Chí Minh, Việt Nam\n"
    )


def _get_about_markdown() -> str:
    """Generate markdown representation of About Us for AI agents."""
    return (
        "# Giới Thiệu Về Hệ Thống Đào Tạo PPTQ LMS\n\n"
        "> Nền tảng quản lý đào tạo trực tuyến, triết lý sư phạm chuẩn mực và công nghệ khảo thí tiên tiến.\n\n"
        "## 1. Sứ Mệnh & Tầm Nhìn\n"
        "PPTQ LMS ra đời với mục tiêu cung cấp giải pháp đào tạo trực tuyến và khảo thí chuẩn mực, "
        "kết hợp nội dung học thuật chất lượng cao, trải nghiệm người học mượt mà và cơ chế đánh giá khảo thí trung thực. "
        "Hệ thống cho phép học viên tiếp thu kiến thức chủ động theo tốc độ cá nhân, "
        "đồng thời bảo đảm kết quả đánh giá phản ánh chính xác năng lực thực tế.\n\n"
        "## 2. Nền Tảng Công Nghệ & Kiến Trúc\n"
        "- **Kiến trúc Pure Headless REST API**: Phục vụ chuẩn dữ liệu JSON máy đọc được cho Web SPA và AI agents.\n"
        "- **Phòng chống gian lận đa tầng**: Giám sát phòng thi Blackout Shield chống chuyển tab và mở DevTools.\n"
        "- **Bảo vệ bản quyền số DRM**: Luồng video HLS mã hóa với token bảo vệ gắn liền phiên học viên.\n"
        "- **Chứng chỉ số xác thực tức thì**: Phát hành chứng chỉ PDF chính thức có mã định danh xác thực.\n"
        "- **Trợ lý học thuật AI**: Tích hợp 'Bạch tuộc trợ lí AI' hỗ trợ giải đáp học tập 24/7.\n\n"
        "## 3. Cam Kết Đào Tạo & Quyền Lợi\n"
        "Mọi khóa học đều được kiểm duyệt học thuật trước khi công bố. "
        "Quyền lợi học viên được bảo đảm vĩnh viễn (Lifetime Enrollment) sau khi hoàn tất đăng ký khóa học.\n\n"
        "## 4. Thông Tin Tổ Chức\n"
        "- Đơn vị: Hệ thống Đào tạo PPTQ LMS\n"
        "- Địa chỉ: Khu Công Nghệ Cao, Thành phố Thủ Đức, TP. Hồ Chí Minh, Việt Nam\n"
        "- Hotline: +84-908-667-141 | Email: admin@pptq.id.vn\n"
        "- Website: https://pptq.id.vn\n"
    )


def _get_contact_markdown() -> str:
    """Generate markdown representation of Contact info for AI agents."""
    return (
        "# Thông Tin Liên Hệ & Hỗ Trợ Kỹ Thuật PPTQ LMS\n\n"
        "> Kênh tiếp nhận hỗ trợ học vụ, giải đáp kỹ thuật và tiếp nhận phản ánh dịch vụ 24/7.\n\n"
        "## Kênh Liên Hệ Trực Tiếp\n"
        "- **Hotline hỗ trợ**: +84-908-667-141\n"
        "- **Email học vụ**: admin@pptq.id.vn\n"
        "- **Báo cáo an ninh**: security@pptq.id.vn\n"
        "- **Trụ sở chính**: Khu Công Nghệ Cao, Phường Tân Phú, Thành phố Thủ Đức, TP. Hồ Chí Minh, Việt Nam\n\n"
        "## Thời Gian Làm Việc & SLA Cam Kết\n"
        "- Bộ phận hỗ trợ: Thứ Hai - Thứ Bảy: 08:00 - 17:30 (Giờ Việt Nam - UTC+7)\n"
        "- Hệ thống máy chủ & khảo thí: Tự động vận hành 24/7/365\n"
        "- Cam kết phản hồi sự cố phòng thi: Dưới 15 phút\n"
        "- Xử lý phúc khảo điểm thi: 24 - 48 giờ làm việc\n"
    )


def _get_privacy_markdown() -> str:
    """Generate markdown representation of Privacy Policy for AI agents."""
    return (
        "# Chính Sách Bảo Mật & Quyền Riêng Tư Dữ Liệu PPTQ LMS\n\n"
        "> Tiêu chuẩn bảo vệ dữ liệu cá nhân theo Nghị định 13/2023/NĐ-CP của Chính phủ Việt Nam.\n\n"
        "## 1. Dữ Liệu Thu Thập & Mục Đích Xử Lý\n"
        "Hệ thống chỉ thu thập các dữ liệu cần thiết phục vụ quản trị học tập: thông tin tài khoản (email, họ tên, mật khẩu băm Argon2id), tiến độ xem bài giảng, bài nộp khảo thí và mã giao dịch học phí VietQR.\n\n"
        "## 2. Tiêu Chuẩn Bảo Mật Kỹ Thuật\n"
        "- Mã hóa truyền tải HTTPS TLS 1.3 và tải trọng đăng nhập lai RSA-OAEP 2048 + AES-GCM 256.\n"
        "- Khóa phiên làm bài thi đơn lẻ (Single Active Editing Lease) chống thi hộ đồng thời.\n"
        "- Bảng kiểm toán append-only ghi nhận toàn bộ biến động điểm số, tài khoản và giao dịch.\n"
        "- Tệp tin tải lên được cách ly và kiểm dịch tự động trước khi công bố.\n\n"
        "## 3. Quyền Của Học Viên\n"
        "Học viên có quyền tra cứu, trích xuất dữ liệu học tập, yêu cầu chỉnh sửa thông tin sai lệch và khiếu nại bảo mật qua email privacy@pptq.id.vn.\n\n"
        "## 4. Đầu Mối Phụ Trách Dữ Liệu (DPO)\n"
        "- Ban Quản trị An ninh Thông tin PPTQ LMS\n"
        "- Email: privacy@pptq.id.vn | Hotline: +84-908-667-141\n"
        "- Cập nhật lần cuối: 27/10/2026\n"
    )


@frontend_bp.route("/", methods=["GET"])
@frontend_bp.route("/frontend/", methods=["GET"])
@frontend_bp.route("/frontend", methods=["GET"])
def index() -> Response:
    """Serve the SPA Web application index, Markdown for AI agents, or JSON for automated API clients."""
    accept = request.headers.get("Accept", "")
    wants_markdown = "text/markdown" in accept
    wants_json = "application/json" in accept and "text/html" not in accept and not wants_markdown

    if wants_markdown:
        md_content = _get_homepage_markdown()
        resp = make_response(md_content, 200)
        resp.headers["Content-Type"] = "text/markdown; charset=utf-8"
        resp.headers["Vary"] = "Accept"
        return resp

    if wants_json:
        resp = jsonify(
            {
                "name": "PWD301 Online Course Management Platform",
                "status": "running",
                "version": backend.__version__,
                "web_ui": "/",
                "api_docs": "/api",
            }
        )
        resp.headers["Vary"] = "Accept"
        return resp

    frontend_dir = _get_frontend_dir()
    index_path = os.path.join(frontend_dir, "index.html")

    if not os.path.isfile(index_path):
        resp = jsonify(
            {
                "name": "PWD301 Online Course Management Platform",
                "status": "running",
                "version": backend.__version__,
                "notice": "Frontend index.html is being initialized.",
            }
        )
        resp.headers["Vary"] = "Accept"
        return resp

    from flask_wtf.csrf import generate_csrf

    token = generate_csrf()
    resp = make_response(send_file(index_path, mimetype="text/html"))
    resp.set_cookie("csrf_token", token, samesite="Lax")
    resp.headers["Vary"] = "Accept"
    return resp


@frontend_bp.route("/frontend/<path:filename>", methods=["GET"])
def serve_frontend_assets(filename: str) -> Response:
    """Serve static assets, images, and screens from the frontend directory safely."""
    frontend_dir = _get_frontend_dir()
    target_path = os.path.normpath(os.path.join(frontend_dir, filename))

    # Path traversal protection
    if not target_path.startswith(frontend_dir):
        abort(404)

    if not os.path.isfile(target_path):
        abort(404)

    mime, _ = mimetypes.guess_type(target_path)
    return send_file(target_path, mimetype=mime or "application/octet-stream")


@frontend_bp.route("/assets/<path:filename>", methods=["GET"])
def serve_assets_shortcut(filename: str) -> Response:
    """Serve assets requested via root-relative /assets/ URL."""
    return serve_frontend_assets(f"assets/{filename}")


@frontend_bp.route("/api/ui/screens", methods=["GET"])
def list_screens() -> Response:
    """List all registered frontend screens and their routes for SPA discovery."""
    frontend_dir = _get_frontend_dir()
    screens = []

    for folder_name, meta in SCREEN_METADATA.items():
        folder_path = os.path.join(frontend_dir, folder_name)
        code_file = os.path.join(folder_path, "code.html")
        screen_png = os.path.join(folder_path, "screen.png")

        has_code = os.path.isfile(code_file)
        has_png = os.path.isfile(screen_png)

        screens.append(
            {
                "id": folder_name,
                "title": meta["title"],
                "role": meta["role"],
                "route": meta["route"],
                "category": meta["category"],
                "has_code": has_code,
                "has_preview": has_png,
                "code_url": f"/api/ui/screen/{folder_name}",
                "preview_url": f"/frontend/{folder_name}/screen.png" if has_png else None,
            }
        )

    return jsonify({"total": len(screens), "screens": screens})


@frontend_bp.route("/api/ui/screen/<folder_name>", methods=["GET"])
def get_screen_html(folder_name: str) -> Response:
    """Retrieve raw HTML content for a specific screen to inject into the SPA viewport."""
    if folder_name not in SCREEN_METADATA:
        abort(404)

    frontend_dir = _get_frontend_dir()
    code_path = os.path.join(frontend_dir, folder_name, "code.html")

    if os.path.isfile(code_path):
        with open(code_path, encoding="utf-8") as f:
            content = f.read()
    else:
        meta = SCREEN_METADATA[folder_name]
        content = (
            f'<div class="screen-view p-6" data-screen-id="{folder_name}">\n'
            f'  <div class="screen-header mb-4">\n'
            f'    <span class="text-xs font-semibold uppercase tracking-wider text-indigo-600">PWD301 LMS - Học tập</span>\n'
            f'    <h2 class="text-xl font-bold mt-1 mb-2">{meta["title"]}</h2>\n'
            f'    <p class="text-sm text-gray-500">Vai trò: {meta["role"]} | Danh mục: {meta["category"]}</p>\n'
            f"  </div>\n"
            f'  <div class="screen-content bg-white p-4 rounded-lg shadow-sm border border-gray-100">\n'
            f'    <p class="text-gray-700">Giao diện {meta["title"]} kết nối trực tiếp với Pure Headless REST API.</p>\n'
            f"  </div>\n"
            f"</div>"
        )

    resp = make_response(content)
    resp.mimetype = "text/html; charset=utf-8"
    return resp


@frontend_bp.route("/api/telemetry", methods=["POST"])
def post_client_telemetry() -> tuple[Response, int]:
    """Ingest frontend client security and operational telemetry events."""
    data = request.get_json(silent=True) or {}
    return jsonify({"success": True, "event": data.get("event_type")}), 200



@frontend_bp.route("/about", methods=["GET"])
@frontend_bp.route("/about/", methods=["GET"])
def serve_about() -> Response:
    """Serve the About page supporting HTML and Markdown content negotiation."""
    accept = request.headers.get("Accept", "")
    if "text/markdown" in accept:
        resp = make_response(_get_about_markdown(), 200)
        resp.headers["Content-Type"] = "text/markdown; charset=utf-8"
        resp.headers["Vary"] = "Accept"
        return resp

    frontend_dir = _get_frontend_dir()
    page_path = os.path.join(frontend_dir, "about.html")
    if os.path.isfile(page_path):
        resp = make_response(send_file(page_path, mimetype="text/html"))
    else:
        resp = make_response(_get_about_markdown(), 200)
        resp.headers["Content-Type"] = "text/markdown; charset=utf-8"
    resp.headers["Vary"] = "Accept"
    return resp


@frontend_bp.route("/contact", methods=["GET"])
@frontend_bp.route("/contact/", methods=["GET"])
def serve_contact() -> Response:
    """Serve the Contact page supporting HTML and Markdown content negotiation."""
    accept = request.headers.get("Accept", "")
    if "text/markdown" in accept:
        resp = make_response(_get_contact_markdown(), 200)
        resp.headers["Content-Type"] = "text/markdown; charset=utf-8"
        resp.headers["Vary"] = "Accept"
        return resp

    frontend_dir = _get_frontend_dir()
    page_path = os.path.join(frontend_dir, "contact.html")
    if os.path.isfile(page_path):
        resp = make_response(send_file(page_path, mimetype="text/html"))
    else:
        resp = make_response(_get_contact_markdown(), 200)
        resp.headers["Content-Type"] = "text/markdown; charset=utf-8"
    resp.headers["Vary"] = "Accept"
    return resp


@frontend_bp.route("/privacy", methods=["GET"])
@frontend_bp.route("/privacy/", methods=["GET"])
def serve_privacy() -> Response:
    """Serve the Privacy policy page supporting HTML and Markdown content negotiation."""
    accept = request.headers.get("Accept", "")
    if "text/markdown" in accept:
        resp = make_response(_get_privacy_markdown(), 200)
        resp.headers["Content-Type"] = "text/markdown; charset=utf-8"
        resp.headers["Vary"] = "Accept"
        return resp

    frontend_dir = _get_frontend_dir()
    page_path = os.path.join(frontend_dir, "privacy.html")
    if os.path.isfile(page_path):
        resp = make_response(send_file(page_path, mimetype="text/html"))
    else:
        resp = make_response(_get_privacy_markdown(), 200)
        resp.headers["Content-Type"] = "text/markdown; charset=utf-8"
    resp.headers["Vary"] = "Accept"
    return resp


@frontend_bp.route("/llms.txt", methods=["GET"])
@frontend_bp.route("/.well-known/llms.txt", methods=["GET"])
def serve_llms_txt() -> Response:
    """Serve agent instruction file with when-to-use guidance for AI agents."""
    frontend_dir = _get_frontend_dir()
    llms_path = os.path.join(frontend_dir, "llms.txt")
    if os.path.isfile(llms_path):
        resp = make_response(send_file(llms_path, mimetype="text/markdown"))
    else:
        resp = make_response(_get_homepage_markdown(), 200)
    resp.headers["Content-Type"] = "text/markdown; charset=utf-8"
    resp.headers["Vary"] = "Accept"
    return resp


@frontend_bp.route("/llms-full.txt", methods=["GET"])
def serve_llms_full_txt() -> Response:
    """Serve full system documentation file for LLMs."""
    frontend_dir = _get_frontend_dir()
    full_path = os.path.join(frontend_dir, "llms-full.txt")
    if os.path.isfile(full_path):
        resp = make_response(send_file(full_path, mimetype="text/markdown"))
    else:
        resp = make_response(_get_homepage_markdown(), 200)
    resp.headers["Content-Type"] = "text/markdown; charset=utf-8"
    resp.headers["Vary"] = "Accept"
    return resp


@frontend_bp.route("/sitemap.xml", methods=["GET"])
def serve_sitemap() -> Response:
    """Serve XML sitemap for search crawlers and AI agents."""
    frontend_dir = _get_frontend_dir()
    sitemap_path = os.path.join(frontend_dir, "sitemap.xml")
    if os.path.isfile(sitemap_path):
        resp = make_response(send_file(sitemap_path, mimetype="application/xml"))
    else:
        fallback = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://pptq.id.vn/</loc><lastmod>2026-10-27</lastmod></url></urlset>'
        resp = make_response(fallback, 200)
    resp.headers["Content-Type"] = "application/xml; charset=utf-8"
    return resp


@frontend_bp.route("/robots.txt", methods=["GET"])
def serve_robots_txt() -> Response:
    """Serve robots.txt directing crawlers to the XML sitemap."""
    frontend_dir = _get_frontend_dir()
    robots_path = os.path.join(frontend_dir, "robots.txt")
    if os.path.isfile(robots_path):
        resp = make_response(send_file(robots_path, mimetype="text/plain"))
    else:
        fallback = "User-agent: *\nAllow: /\nSitemap: https://pptq.id.vn/sitemap.xml\n"
        resp = make_response(fallback, 200)
    resp.headers["Content-Type"] = "text/plain; charset=utf-8"
    return resp
