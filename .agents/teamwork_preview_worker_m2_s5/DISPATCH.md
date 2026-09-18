## 2026-09-16T05:36:38Z

You are teamwork_preview_worker_m2_s5.
Your working directory is: E:\PWD301\.agents\teamwork_preview_worker_m2_s5
Your parent is: teamwork_preview_orchestrator_5 (Conversation ID: 4946890a-b666-4014-a18b-0a588b75fb4e).

MANDATORY CONSTRAINTS:
- Read E:\PWD301\.agents\ORIGINAL_REQUEST.md (header ## 2026-09-16T05:16:14Z).
- Read E:\PWD301\.agents\PROJECT.md.
- Read E:\PWD301\.agents\teamwork_preview_explorer_survey5_2\handoff.md for complete screen-by-screen mappings, Jinja variable bindings, form contracts, and test assertions.
- Apply mandatory skills: Superpowers (TDD, verification-before-completion), Task Observer, Ponytail, Full Output Enforcement, Impeccable. Remember completion reporting syntax: "Đã dùng x skill gồm: ...".

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

EXCLUSIVELY OWNED FILES:
You own and may edit the following templates in src/pwd301/templates/student/:
- src/pwd301/templates/student/dashboard.html
- src/pwd301/templates/student/my_learning.html
- src/pwd301/templates/student/course_detail.html
- src/pwd301/templates/student/lesson.html
- src/pwd301/templates/student/assessment_detail.html
- src/pwd301/templates/student/attempt.html
- src/pwd301/templates/student/result.html
- src/pwd301/templates/student/ai_assistant.html
- src/pwd301/templates/student/become_instructor.html
- src/pwd301/templates/student/assessments.html

TASK OBJECTIVE (Milestone 2 — Student Portal Integration):
Migrate each Student Portal template to the modern Productive Clarity / Carbon design system based on frontend-preview/ stitch screens while binding all backend context variables and preserving test assertions:
1. `student/dashboard.html`:
   - Map from `pwd301_student_dashboard_variant_1_action_centric_master_flyout_notification_hub`.
   - Bind `overview` stats: active courses, completed courses, progress percent, active courses list, upcoming assessments, recent results. Provide action links (`student.course_progress`, `student.my_learning`, `student.assessments_view`, `student.attempt_view`, `student.assessment_detail_view`).
2. `student/my_learning.html`:
   - Map from `pwd301_student_course_hub_variant_1_integrated_master_workspace_contextual_tabs`.
   - Bind `overview.enrollments`, status filters, leave course action (`POST /student/courses/<id>/leave`), re-enroll action, continue learning button.
3. `student/course_detail.html`:
   - Map from `pwd301_public_catalog_detail_variant_2_full_page_academic_dossier` and `variant_1`.
   - Bind `course`, `enrollment`, `prereq_items`, `is_eligible`, `missing_titles`, `active_count`, `is_full`, `lessons`.
   - DEFENSIVE UX (TEST REQUIRED): When `is_eligible == False`, disable enroll button with text "Chưa đủ điều kiện", and show alert "Ghi danh bị chặn do chưa đạt điều kiện tiên quyết". Form must submit to `student.enroll` with CSRF token.
4. `student/lesson.html`:
   - Map from `pwd301_lesson_reader_variant_1_3_column_academic_console_resource_vault` + Zen reader tab.
   - Bind `course`, `lesson`, `progress`, `all_lessons`, `lesson_resources`, `video_resource`, `doc_resource`.
   - Preserve `lesson-progress-badge`, curriculum drawer, video/doc stream, and progress heartbeat AJAX endpoint (`POST /student/lessons/<id>/progress`).
5. `student/assessment_detail.html` (Waiting Room):
   - Map from `pwd301_assessment_hub_waiting_room_variant_2_dedicated_focus_waiting_room`.
   - Real-time UTC server synchronized countdown clock, examination rules checklist, enter/start exam button.
6. `student/attempt.html`:
   - Map from `pwd301_assessment_attempt_variant_1_master_exam_console_contextual_navigator`.
   - TEST REQUIREMENT: Ensure `leaseToken = "..."` literal pattern is present for lease test regex matching.
   - Single-tab editing lease anti-cheat, monotonic autosave with `client_sequence`, contextual question navigator, submit confirmation modal with CSRF.
7. `student/result.html`:
   - Map from `pwd301_midterm_assessment_results` and `pwd301_quiz_mini_test_results`.
   - Detailed question-by-question breakdown, awarded points, feedback, status badges.
8. `student/ai_assistant.html`:
   - Map from `pwd301_student_contextual_ai_clean_minimalist_academic_workspace`.
   - Contextual chat interface bound to `student_ai_chat`, chat history, quick prompts.
9. `student/become_instructor.html`:
   - Application profile card for becoming instructor, submission form (`POST /student/become-instructor` with CSRF), cancel form, status banner.
10. `student/assessments.html`:
    - Assessment hub list, filtering by status, upcoming vs completed.

VERIFICATION COMMANDS:
- `python scripts/repo_check.py`
- `python -m pytest tests/api/test_student_portal_ui.py -v`
- `python -m pytest tests/api/test_web_ui_flow_fixes.py -v`
- `python -m pytest tests/e2e/test_student_lifecycle_e2e.py -v`
- `ruff check src tests`
