## 2026-09-16T05:29:49Z

You are teamwork_preview_challenger_m1_s5_1.
Your working directory is: E:\PWD301\.agents\teamwork_preview_challenger_m1_s5_1
Your parent is: teamwork_preview_orchestrator_5 (Conversation ID: 4946890a-b666-4014-a18b-0a588b75fb4e).

CRITICAL CONSTRAINTS:
- Read E:\PWD301\.agents\ORIGINAL_REQUEST.md (header ## 2026-09-16T05:16:14Z).
- Read E:\PWD301\.agents\PROJECT.md.
- Read E:\PWD301\.agents\teamwork_preview_worker_m1\handoff.md.
- Write your report to E:\PWD301\.agents\teamwork_preview_challenger_m1_s5_1\handoff.md.
- Apply mandatory skills: Superpowers, Task Observer, Ponytail, Full Output Enforcement, Impeccable. Remember completion report syntax: "Đã dùng x skill gồm: ...".

TASK OBJECTIVE:
Adversarially challenge Milestone 1 (HTML/Jinja Rendering, FOUC, and Navigation DOM assertions):
1. Verify rendering across all user contexts:
   - Anonymous/guest user (`/auth/login`, `/auth/register`)
   - Student session (`/student/dashboard`)
   - Instructor session (`/instructor/dashboard`)
   - Admin session (`/admin/dashboard`)
2. Stress test DOM structure against Jinja crashes:
   - Test rendering when unread notifications count is 0, >0, or service raises an exception.
   - Test role switching form markup: verify CSRF input is present and valid.
   - Test sidebar collapsed toggle class and cookie/localStorage synchronization.
   - Check that no unescaped variables or syntax errors occur in base.html.
3. Run automated tests and targeted client rendering checks via pytest:
   - `python -m pytest tests/api/test_student_portal_ui.py tests/api/test_toast_notifications.py tests/api/test_web_ui_flow_fixes.py -v`
4. State your explicit VERDICT in handoff.md: APPROVE or REQUEST_CHANGES.
Send a message to your parent when done.
