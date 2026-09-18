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

import pwd301
from pwd301.blueprints.frontend import frontend_bp


def _get_frontend_dir() -> str:
    """Resolve the absolute path to the repository frontend directory."""
    configured = current_app.config.get("FRONTEND_DIR")
    if configured and os.path.isdir(configured):
        return os.path.abspath(configured)

    env_dir = os.environ.get("FRONTEND_DIR")
    if env_dir and os.path.isdir(env_dir):
        return os.path.abspath(env_dir)

    # Relative to this file: src/pwd301/blueprints/frontend/routes.py -> repo_root/frontend
    base_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "frontend")
    )
    if os.path.isdir(base_dir):
        return base_dir

    # Fallback if running inside Docker container with /app/frontend
    docker_dir = "/app/frontend"
    if os.path.isdir(docker_dir):
        return docker_dir

    return base_dir


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
    "pwd301_question_bank_hub_variant_2_master_operations_table_subject_inspector": {
        "title": "Ngân hàng Câu hỏi & Thanh tra Môn học",
        "role": "INSTRUCTOR",
        "route": "#/instructor/questions",
        "category": "Question Bank",
    },
    "pwd301_extended_question_bank_studio_chi_ti_t_to_n_b_c_u_h_i_m_n_h_c": {
        "title": "Studio Chi tiết Toàn bộ Câu hỏi Môn học",
        "role": "INSTRUCTOR",
        "route": "#/instructor/questions/studio",
        "category": "Question Bank",
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


@frontend_bp.route("/", methods=["GET"])
def index() -> Response:
    """Serve the SPA Web application index or return JSON for automated API clients."""
    accept = request.headers.get("Accept", "")
    wants_json = "application/json" in accept and "text/html" not in accept

    if wants_json:
        return jsonify(
            {
                "name": "PWD301 Online Course Management Platform",
                "status": "running",
                "version": pwd301.__version__,
                "web_ui": "/",
                "api_docs": "/api",
            }
        )

    frontend_dir = _get_frontend_dir()
    index_path = os.path.join(frontend_dir, "index.html")

    if not os.path.isfile(index_path):
        return jsonify(
            {
                "name": "PWD301 Online Course Management Platform",
                "status": "running",
                "version": pwd301.__version__,
                "notice": "Frontend index.html is being initialized.",
            }
        )

    from flask_wtf.csrf import generate_csrf

    token = generate_csrf()
    resp = make_response(send_file(index_path, mimetype="text/html"))
    resp.set_cookie("csrf_token", token, samesite="Lax")
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

    if not os.path.isfile(code_path):
        abort(404)

    with open(code_path, encoding="utf-8") as f:
        content = f.read()

    resp = make_response(content)
    resp.mimetype = "text/html; charset=utf-8"
    return resp
