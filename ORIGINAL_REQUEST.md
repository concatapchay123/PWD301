# Original User Request

## 2026-09-11T15:27:07Z

Audit and identify all bugs, errors, security vulnerabilities, business logic violations, and test failures across the entire PWD301 codebase.

Working directory: e:\PWD301
Integrity mode: development

## Requirements

### R1. Comprehensive Static & Verification Audit
Run repository checks, linters (`ruff`, `mypy`), and the full test suite (`pytest`) to capture any existing crashes, syntax errors, type inconsistencies, or broken test assertions.

### R2. Invariant & Business Rule Conformance Audit
Verify adherence against the 73 business rules in `docs/system/PWD301_SYSTEM_SPECIFICATION/business/01_BUSINESS_RULE_CATALOG.md` and non-negotiable invariants in `AGENTS.md` (e.g. auth splitting, assessment locking, fail-closed file security, cycle-free prerequisites).

### R3. Security & Operational Vulnerability Analysis
Inspect endpoints for authorization checks, mass assignment vulnerabilities, SQL injection, CSRF enforcement on session routes, and secret leakage.

### R4. Actionable Bug Report & Categorization
Deliver a comprehensive categorized report of all detected defects with file locations, severity levels, reproduction steps or evidence, and concrete remediation recommendations.

## Acceptance Criteria

### Automated Verification
- [ ] Pytest suite execution results documented with all failing tests identified (if any).
- [ ] Static analysis tools (`scripts/repo_check.py`, `ruff`, `mypy`) run and all errors/warnings enumerated.

### Deep Logic & Invariant Audit
- [ ] Every major subsystem (Auth, Courses/Lessons, Assessments & Grading, Files/Security, AI/RAG) audited against its specifications.
- [ ] Discrepancies between implementation and `docs/system/` or `docs/database/` explicitly listed.

### Final Deliverable
- [ ] Clear markdown audit report detailing high, medium, and low severity issues found across the codebase.

## 2026-09-13T22:34:29Z

Comprehensive upgrade and bug remediation for the PWD301 LMS platform: resolving file upload and pending scan defects, deeply expanding instructor course customization (learning objectives, requirements, prerequisites, syllabus), enabling direct question authoring & document import (PDF/DOCX) on assessment pages, supporting multi-format lecture media uploads (PDF, DOCX, PPTX, Video), and grounding the AI Assistant with real-time page context, course materials RAG retrieval, and catalog-aware course recommendations.

Working directory: e:\PWD301
Integrity mode: development

---

## Requirements

### R1. File Upload, Virus Scanning & Secure Access Remediation
- Fix file asset rendering in Instructor and Student views: correctly display `display_name`, `original_filename`, file size, MIME type, and malware scan status (`CLEAN`, `SAFE`, `QUARANTINED`, `INFECTED`).
- Eliminate the issue where clean uploaded files remain stuck in `PENDING` status.
- Implement secure, authenticated download endpoints for Web session users (Instructors and actively enrolled Students) without triggering 403 Forbidden on session-authenticated requests, while maintaining fail-closed security invariants (ADR-002, ADR-008).

### R2. Deep Instructor Course Customization & Dynamic Student View
- Provide comprehensive course editing in the Instructor portal:
  - **Mục tiêu và kỹ năng (Learning Objectives & Skills Gained)**.
  - **Mô tả và yêu cầu môn học (Target Audience & Completion Requirements)**.
  - **Điều kiện tiên quyết (Prerequisites)**: Interface to select and manage prerequisite courses using the existing `course_prerequisites` schema, enforcing cycle prevention.
  - **Đề cương chương trình đào tạo (Curriculum & Syllabus Structure)**.
- Dynamically render all customized course data in the Student Course Detail page (`student/course_detail.html`), eliminating all hardcoded placeholder text.

### R3. Assessment Page Question Authoring, Direct Editing & Document Import
- In the Assessment Builder (`instructor/assessment_builder.html`):
  - Allow instructors to create questions directly from the exam page (Single Choice, Multiple Choice, True/False, Short Answer) with custom points, choices, and explanations, without forcing navigation to the separate Question Bank.
  - Allow direct in-place editing of question content, choices, and correct answers.
  - Enable automatic question generation and test creation by uploading PDF and Word (.docx) files directly from the assessment page, integrating with the import service pipeline.
  - Strictly enforce Assessment Timing Lock (BR-031 / Invariant 13) and Structural Freeze (BR-030 / Invariant 14) once student attempts have commenced.

### R4. Multi-Format Lecture Authoring & Media Support
- Upgrade the Lesson authoring interface to allow instructors to upload and attach multi-format course materials (PDF, Word DOCX, PPTX presentation, and MP4/WebM video < 1 GB) instead of requiring manual markdown typing alone.
- Bind uploaded media to `LessonResource` and `FileAsset`.
- Provide student-facing lecture viewers capable of rendering/streaming attached videos, presenting slides/documents, and providing downloadable learning resources.

### R5. Context-Aware, Grounded AI Assistant & Smart Course Recommendation
- **Page & Location Awareness**: The client-side widget (`app_shell.js`) must detect and transmit the active page route, page title, course ID, and lesson ID with every user interaction.
- **Dynamic Conversation Scoping**: Automatically bind the AI conversation to the active course or lesson context rather than defaulting to `GLOBAL`.
- **Grounded Semantic RAG**: In course and lesson contexts, execute RAG retrieval against lesson text and attached file content so the AI answers accurately using course materials with citations `[Ref: <UUID>]`.
- **Course Catalog Knowledge & Recommendation Engine**: Equip the AI Assistant with catalog context (active course titles, codes, descriptions, categories, prerequisites) to accurately answer questions about courses and recommend relevant courses to students based on their learning goals.

---

## Acceptance Criteria

### Verification Mechanisms
- **Automated Test Suite**: Unit and integration tests covering file upload & download authorization, course prerequisite & metadata updates, assessment direct question authoring & import, lesson media attachment, and AI context-aware chat routing.
- **Security & Concurrency Verification**: Verify session auth on downloads, fail-closed quarantine enforcement, zero internal PK leakage (ADR-002), and rate limiting.
- **End-to-End Verification**: Manual and programmatic verification of web portal pages across Instructor and Student roles.

### Checkable Criteria
- [ ] Uploaded files display correct filename, size in MB, MIME type, and `CLEAN (Đã quét an toàn)` status immediately after clean scan.
- [ ] Instructors and enrolled students can successfully download and view active course files from the web UI without 403 errors.
- [ ] Instructor can edit and save Learning Objectives, Target Audience, Completion Requirements, Prerequisites, and Syllabus from Course Settings.
- [ ] Student course details view reflects 100% of instructor-customized metadata with 0 hardcoded placeholder items.
- [ ] Assessment page has "+ Tạo câu hỏi mới" and "Upload PDF/DOCX tạo đề tự động", allowing full question creation and editing directly on the exam.
- [ ] Lesson creation modal allows uploading PDF, DOCX, PPTX, and Video files, which appear in the student lesson viewer.
- [ ] AI Assistant identifies the exact course and lesson when asked "đây là khóa học gì" on a course page and provides accurate course information.
- [ ] AI Assistant answers questions based on course documents using RAG citations and recommends courses from the catalog when asked on the main page.
- [ ] All existing automated tests (`pytest`) pass with 0 regressions.

## 2026-09-14T12:20:16Z

Quota has been reset. Server was restarted. Please resume work on the project orchestrator and milestones M2 through M6 according to e:\PWD301\.agents\PROJECT.md.

## 2026-09-14T13:03:01Z

Quota has been reset. Please resume Sentinel and Orchestrator 3 to complete Milestone 3 and proceed with Milestone 4 (Lecture media), Milestone 5 (AI context/RAG/recommendation), and Milestone 6.

## 2026-09-16T05:16:14Z

# Teamwork Project Prompt

Tích hợp và chuyển đổi toàn diện hệ thống frontend mới từ 33 màn hình Stitch (frontend-preview/) vào hệ thống Flask Web (src/pwd301/templates, src/pwd301/static), bốc tách data binding và backend context từ frontend cũ, bảo toàn 100% logic xác thực (Flask session, CSRF, RBAC, Timezone, i18n) và đảm bảo các luồng nghiệp vụ Học viên, Giảng viên, Quản trị viên hoạt động trơn tru, vượt qua toàn bộ test suite.

Working directory: E:\PWD301
Integrity mode: development

## Requirements

### R1. Hợp nhất Kiến trúc Giao diện & Core App Shell (Tailwind & Design Tokens)
- Hợp nhất src/pwd301/templates/base.html và static assets sang hệ thiết kế mới (Productive Clarity / Carbon): nạp Tailwind CSS CDN, font Plus Jakarta Sans, Inter, JetBrains Mono và bộ icon Material Symbols Outlined.
- Tái cấu trúc thanh điều hướng: Topbar tích hợp bộ đếm thông báo, chuyển đổi múi giờ (timezone), ngôn ngữ (i18n), chuyển đổi vai trò (switch-role), và Sidebar động (276px) co giãn linh hoạt theo 3 vai trò Học viên (Student), Giảng viên (Instructor), Quản trị viên (Admin).
- Tích hợp hệ thống Toast Feedback (toast-container) và Modal popups chuẩn Material/Tailwind với hiệu ứng đóng mở mượt mà, loại bỏ hoàn toàn hiện tượng nhấp nháy FOUC.

### R2. Tích hợp Chi tiết Cổng Học viên (Student Portal)
- Nối các màn hình Stitch tương ứng vào src/pwd301/templates/student/:
  - student/dashboard.html ← pwd301_student_dashboard_variant_1_action_centric_master_flyout_notification_hub
  - student/my_learning.html ← pwd301_student_course_hub_variant_1_integrated_master_workspace_contextual_tabs
  - student/course_detail.html ← pwd301_public_catalog_detail_variant_1_split_master_detail / variant_2
  - student/lesson.html ← pwd301_lesson_reader_variant_1_3_column_academic_console_resource_vault (kèm Zen reader tab)
  - student/assessment_detail.html (Waiting Room) ← pwd301_assessment_hub_waiting_room_variant_1 / variant_2 (kèm đồng hồ đếm ngược server UTC chuẩn phòng thi)
  - student/attempt.html ← pwd301_assessment_attempt_variant_1_master_exam_console_contextual_navigator (kèm autosave, lease anti-cheat)
  - student/result.html ← pwd301_midterm_assessment_results & pwd301_quiz_mini_test_results
  - student/ai_assistant.html ← pwd301_student_contextual_ai_clean_minimalist_academic_workspace
  - student/become_instructor.html ← tích hợp card quy chuẩn hồ sơ ứng tuyển giảng viên.

### R3. Tích hợp Chi tiết Cổng Giảng viên (Instructor Portal)
- Nối các màn hình Stitch tương ứng vào src/pwd301/templates/instructor/:
  - instructor/dashboard.html ← pwd301_instructor_dashboard_clean_minimalist_focus / pwd301_instructor_workspace_variant_3
  - instructor/courses.html ← pwd301_instructor_courses_variant_2_master_operations_table_detailed_provenance (kèm modal tạo khóa học danh mục, độ khó, chỉ tiêu)
  - instructor/course_manage.html ← pwd301_extended_course_detail_variant_2 & pwd301_lesson_authoring (studio biên soạn bài học low-tech)
  - instructor/question_bank.html ← pwd301_question_bank_hub_variant_2 & pwd301_extended_question_bank_studio (quản trị toàn bộ câu hỏi môn học)
  - instructor/assessment_builder.html ← Bộ 5 màn hình Azota standard (exam_method_selector, exam_general_config, exam_detailed_config, exam_preview_editor 50/50 raw syntax, exam_validation)
  - instructor/grading.html & instructor/grade_attempt.html ← pwd301_instructor_essay_grading_variant_1_split_canvas_50_50_focus_studio.

### R4. Tích hợp Chi tiết Cổng Quản trị & Xác thực (Admin & Auth)
- Nối các màn hình Stitch vào src/pwd301/templates/admin/ và auth/:
  - admin/dashboard.html ← pwd301_admin_governance_variant_3_modular_tabbed_command_center_academic (kết nối live hardware telemetry CPU/RAM/Disk/Network)
  - admin/operations.html / admin/audit_logs.html / admin/backups.html ← pwd301_admin_operations_security_variant_2_split_operations_cockpit_active
  - admin/instructor_applications.html ← bảng thẩm định hồ sơ ứng tuyển với modal duyệt/từ chối.
  - auth/login.html, auth/register.html, auth/forgot_password.html ← pwd301_auth_account_lifecycle_variant_1_focused_card_interactive_inspector.

### R5. Bảo toàn Invariants, An ninh & Tương thích Backend
- Duy trì 100% các quy chuẩn bắt buộc của PWD301: xác thực server-authoritative Flask session, CSRF protection trên mọi state-changing request, quyền truy cập tài nguyên RBAC phân cấp, che giấu BigInt PK bằng UUID public, fail-closed an ninh tệp tin và rate limiting.
- Đảm bảo các route backend hiện có không bị đổi tên hay vỡ contract; tái sử dụng các model, route, service hiện hữu.

## Acceptance Criteria

### Tính toàn vẹn Giao diện & Trải nghiệm
- [ ] Tất cả các route web của Student, Instructor, Admin, Auth render thành công với giao diện mới, không lỗi Jinja syntax (UndefinedError, BuildError).
- [ ] Tailwind CSS nạp chuẩn xác, không bị xung đột với các logic JavaScript của hệ thống (app_shell.js, theme.js, motion.js).
- [ ] Đầy đủ các tương tác thời gian thực: Đồng hồ đếm ngược phòng thi UTC, tự động lưu câu trả lời bài thi (autosave), lọc câu hỏi ngân hàng đề, chấm bài tự luận 50/50 canvas.

### Tính tương thích & Kiểm thử Hệ thống
- [ ] Toàn bộ bộ kiểm thử tự động của dự án (pytest) chạy vượt qua 100% (không có test nào bị fail).
- [ ] Linter ruff check và ruff format --check đạt 0 cảnh báo.
- [ ] Trình kiểm tra mypy src đạt 0 lỗi.
- [ ] Script kiểm tra repository python scripts/repo_check.py vượt qua tất cả bài kiểm tra.

## Verification Resources
- Test suite: pytest tests/ -v
- Live verification: http://localhost:5000 via Chrome DevTools.

## 2026-09-16T05:52:39Z

Quota has been reset. Please resume execution of teamwork preview from Milestone 2 verification and proceed through Milestone 3, 4, 5.


