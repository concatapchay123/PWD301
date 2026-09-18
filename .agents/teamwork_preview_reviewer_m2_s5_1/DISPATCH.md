## 2026-09-16T05:44:55Z
You are teamwork_preview_reviewer_m2_s5_1.
Your working directory is: E:\PWD301\.agents\teamwork_preview_reviewer_m2_s5_1
Your parent is: teamwork_preview_orchestrator_5 (Conversation ID: 4946890a-b666-4014-a18b-0a588b75fb4e).

CRITICAL CONSTRAINTS:
- Read E:\PWD301\.agents\ORIGINAL_REQUEST.md (header ## 2026-09-16T05:16:14Z).
- Read E:\PWD301\.agents\PROJECT.md.
- Read E:\PWD301\.agents\teamwork_preview_worker_m2_s5\handoff.md.
- You are a review agent. Write your report to E:\PWD301\.agents\teamwork_preview_reviewer_m2_s5_1\handoff.md.
- Apply mandatory skills: Superpowers, Task Observer, Ponytail, Full Output Enforcement, Impeccable. Remember completion report syntax: "Đã dùng x skill gồm: ...".

TASK OBJECTIVE:
Review Milestone 2 (Student Portal Integration - Core Views & Data Bindings):
1. Inspect all 10 templates modified in `src/pwd301/templates/student/`:
   - `dashboard.html`
   - `my_learning.html`
   - `course_detail.html`
   - `lesson.html`
   - `assessment_detail.html`
   - `attempt.html`
   - `result.html`
   - `ai_assistant.html`
   - `become_instructor.html`
   - `assessments.html`
2. Verify:
   - Data bindings match backend models and views in `src/pwd301/blueprints/student/routes.py`.
   - In `attempt.html`: verify literal pattern `leaseToken = "..."` is preserved for lease anti-cheat test regex matching.
   - In `course_detail.html`: verify defensive prerequisite blocker: "Ghi danh bị chặn do chưa đạt điều kiện tiên quyết" and button "Chưa đủ điều kiện".
   - In `lesson.html`: verify `lesson-progress-badge`, video player, doc viewer, resource downloads, and Zen reader tab.
   - In `assessment_detail.html`: verify UTC countdown timer logic.
   - Form actions and CSRF tokens are present on all state-changing forms.
3. Run verification commands:
   - `python scripts/repo_check.py`
   - `python -m pytest tests/api/test_student_portal_ui.py tests/api/test_web_ui_flow_fixes.py -v`
   - `ruff check src tests`
4. State your explicit VERDICT in handoff.md: APPROVE or REQUEST_CHANGES.
Send a message to your parent when done.
