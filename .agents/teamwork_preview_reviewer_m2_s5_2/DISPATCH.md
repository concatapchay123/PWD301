## 2026-09-16T05:44:55Z
You are teamwork_preview_reviewer_m2_s5_2.
Your working directory is: E:\PWD301\.agents\teamwork_preview_reviewer_m2_s5_2
Your parent is: teamwork_preview_orchestrator_5 (Conversation ID: 4946890a-b666-4014-a18b-0a588b75fb4e).

CRITICAL CONSTRAINTS:
- Read E:\PWD301\.agents\ORIGINAL_REQUEST.md (header ## 2026-09-16T05:16:14Z).
- Read E:\PWD301\.agents\PROJECT.md.
- Read E:\PWD301\.agents\teamwork_preview_worker_m2_s5\handoff.md.
- You are a review agent. Write your report to E:\PWD301\.agents\teamwork_preview_reviewer_m2_s5_2\handoff.md.
- Apply mandatory skills: Superpowers, Task Observer, Ponytail, Full Output Enforcement, Impeccable. Remember completion report syntax: "Đã dùng x skill gồm: ...".

TASK OBJECTIVE:
Review Milestone 2 (Student Portal Lifecycle, Interactivity & Security):
1. Inspect templates in `src/pwd301/templates/student/`:
   - Focus on `dashboard.html`, `my_learning.html`, `result.html`, `ai_assistant.html`, `become_instructor.html`.
2. Verify:
   - Dashboard learning stats (`overview`), active courses, upcoming assessments, and recent results links.
   - My learning hub: leave course modal & CSRF, re-enroll modal, status filter pills.
   - Result view: breakdown of score, answers, passing badge, feedback.
   - Become instructor: application form with CSRF, status banners.
   - AI assistant view: 302 redirect compatibility and active course/lesson context binding.
3. Run verification:
   - `python scripts/repo_check.py`
   - `python -m pytest tests/api/test_student_portal_ui.py tests/e2e/test_student_lifecycle_e2e.py -v`
   - `ruff check src tests`
4. State your explicit VERDICT in handoff.md: APPROVE or REQUEST_CHANGES.
Send a message to your parent when done.
