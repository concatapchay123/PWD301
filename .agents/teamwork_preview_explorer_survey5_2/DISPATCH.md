## 2026-09-16T05:18:05Z

You are teamwork_preview_explorer_survey5_2.
Your working directory is: E:\PWD301\.agents\teamwork_preview_explorer_survey5_2
Your parent is: teamwork_preview_orchestrator_5 (Conversation ID: 4946890a-b666-4014-a18b-0a588b75fb4e).

CRITICAL CONSTRAINTS:
- Read E:\PWD301\.agents\ORIGINAL_REQUEST.md (specifically the master prompt at header ## 2026-09-16T05:16:14Z).
- You are a READ-ONLY explorer. Do NOT modify or write source code files. Write only to your working directory (.agents/teamwork_preview_explorer_survey5_2/).
- Apply mandatory skills: Superpowers, Task Observer, Ponytail, Full Output Enforcement, Impeccable. Remember the completion reporting syntax: "Đã dùng x skill gồm: ...".

TASK OBJECTIVE:
Map and analyze Objective R2 (Student Portal Integration):
1. Map each of the 9 Student Portal Stitch screens in frontend-preview/views/ to current Flask templates in src/pwd301/templates/student/:
   - student/dashboard.html ← pwd301_student_dashboard_variant_1_action_centric_master_flyout_notification_hub
   - student/my_learning.html ← pwd301_student_course_hub_variant_1_integrated_master_workspace_contextual_tabs
   - student/course_detail.html ← pwd301_public_catalog_detail_variant_1_split_master_detail / variant_2
   - student/lesson.html ← pwd301_lesson_reader_variant_1_3_column_academic_console_resource_vault (kèm Zen reader tab)
   - student/assessment_detail.html (Waiting Room) ← pwd301_assessment_hub_waiting_room_variant_1 / variant_2 (kèm đồng hồ đếm ngược server UTC chuẩn phòng thi)
   - student/attempt.html ← pwd301_assessment_attempt_variant_1_master_exam_console_contextual_navigator (kèm autosave, lease anti-cheat)
   - student/result.html ← pwd301_midterm_assessment_results & pwd301_quiz_mini_test_results
   - student/ai_assistant.html ← pwd301_student_contextual_ai_clean_minimalist_academic_workspace
   - student/become_instructor.html ← card quy chuẩn hồ sơ ứng tuyển giảng viên.
2. For each screen:
   - Identify the existing Flask routes, blueprints, and view functions serving it.
   - Catalog all context variables currently passed to the Jinja templates and all form actions / POST endpoints / CSRF tokens needed.
   - Detail real-time interactive requirements: UTC server countdown for Waiting Room, autosave & lease anti-cheat for Attempt, Zen reader tab for Lesson, AI chat context binding for AI assistant.
3. Review existing tests covering Student Portal (e.g. tests/api/test_student_portal_ui.py, tests/api/test_web_ui_flow_fixes.py, etc.) to ensure zero regressions and perfect contract compatibility.
4. Document concrete template-by-template migration blueprint, data bindings, form contracts, and risk mitigations.

Deliverable:
Write a comprehensive report to E:\PWD301\.agents\teamwork_preview_explorer_survey5_2\handoff.md with:
- Observation (verified facts, mappings, variables, route signatures)
- Logic Chain (data binding & UI architecture)
- Caveats & Risks
- Concrete Implementation Plan for Milestone 2
- Verification Plan
When finished, send a message to your parent with your summary and handoff path.
