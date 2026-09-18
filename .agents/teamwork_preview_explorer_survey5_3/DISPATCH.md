## 2026-09-16T05:18:05Z

You are teamwork_preview_explorer_survey5_3.
Your working directory is: E:\PWD301\.agents\teamwork_preview_explorer_survey5_3
Your parent is: teamwork_preview_orchestrator_5 (Conversation ID: 4946890a-b666-4014-a18b-0a588b75fb4e).

CRITICAL CONSTRAINTS:
- Read E:\PWD301\.agents\ORIGINAL_REQUEST.md (specifically the master prompt at header ## 2026-09-16T05:16:14Z).
- You are a READ-ONLY explorer. Do NOT modify or write source code files. Write only to your working directory (.agents/teamwork_preview_explorer_survey5_3/).
- Apply mandatory skills: Superpowers, Task Observer, Ponytail, Full Output Enforcement, Impeccable. Remember the completion reporting syntax: "Đã dùng x skill gồm: ...".

TASK OBJECTIVE:
Map and analyze Objectives R3 & R4 (Instructor, Admin & Auth Portals Integration):
1. Map Instructor Portal Stitch screens in frontend-preview/views/ to src/pwd301/templates/instructor/:
   - instructor/dashboard.html ← pwd301_instructor_dashboard_clean_minimalist_focus / pwd301_instructor_workspace_variant_3
   - instructor/courses.html ← pwd301_instructor_courses_variant_2_master_operations_table_detailed_provenance (kèm modal tạo khóa học danh mục, độ khó, chỉ tiêu)
   - instructor/course_manage.html ← pwd301_extended_course_detail_variant_2 & pwd301_lesson_authoring (studio biên soạn bài học low-tech)
   - instructor/question_bank.html ← pwd301_question_bank_hub_variant_2 & pwd301_extended_question_bank_studio (quản trị toàn bộ câu hỏi môn học)
   - instructor/assessment_builder.html ← Bộ 5 màn hình Azota standard (exam_method_selector, exam_general_config, exam_detailed_config, exam_preview_editor 50/50 raw syntax, exam_validation)
   - instructor/grading.html & instructor/grade_attempt.html ← pwd301_instructor_essay_grading_variant_1_split_canvas_50_50_focus_studio.
2. Map Admin & Auth Stitch screens in frontend-preview/views/ to src/pwd301/templates/admin/ and auth/:
   - admin/dashboard.html ← pwd301_admin_governance_variant_3_modular_tabbed_command_center_academic (kết nối live hardware telemetry CPU/RAM/Disk/Network)
   - admin/operations.html / admin/audit_logs.html / admin/backups.html ← pwd301_admin_operations_security_variant_2_split_operations_cockpit_active
   - admin/instructor_applications.html ← bảng thẩm định hồ sơ ứng tuyển với modal duyệt/từ chối.
   - auth/login.html, auth/register.html, auth/forgot_password.html ← pwd301_auth_account_lifecycle_variant_1_focused_card_interactive_inspector.
3. For each screen:
   - Identify existing Flask routes, blueprints, context variables, form actions, and CSRF requirements.
   - Highlight special interactive patterns: Azota 50/50 raw syntax editor & validation, 50/50 essay grading canvas, live hardware telemetry API endpoints in admin.
4. Review existing instructor & admin tests (e.g. tests/api/test_instructor_course_web_flow.py, admin tests, auth tests) to ensure zero regression.
5. Document concrete template-by-template migration blueprint, data bindings, form contracts, and risk mitigations.

Deliverable:
Write a comprehensive report to E:\PWD301\.agents\teamwork_preview_explorer_survey5_3\handoff.md with:
- Observation (verified facts, mappings, variables, route signatures)
- Logic Chain (data binding & UI architecture)
- Caveats & Risks
- Concrete Implementation Plan for Milestones 3 & 4
- Verification Plan
When finished, send a message to your parent with your summary and handoff path.
