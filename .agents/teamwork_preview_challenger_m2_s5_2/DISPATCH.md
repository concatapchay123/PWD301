# Challenger M2.2 Dispatch
Agent: teamwork_preview_challenger_m2_s5_2
Milestone 2: Student Portal Integration

## 2026-09-16T05:44:55Z
You are teamwork_preview_challenger_m2_s5_2.
Your working directory is: E:\PWD301\.agents\teamwork_preview_challenger_m2_s5_2
Your parent is: teamwork_preview_orchestrator_5 (Conversation ID: 4946890a-b666-4014-a18b-0a588b75fb4e).

CRITICAL CONSTRAINTS:
- Read E:\PWD301\.agents\ORIGINAL_REQUEST.md (header ## 2026-09-16T05:16:14Z).
- Read E:\PWD301\.agents\PROJECT.md.
- Read E:\PWD301\.agents\teamwork_preview_worker_m2_s5\handoff.md.
- Write your report to E:\PWD301\.agents\teamwork_preview_challenger_m2_s5_2\handoff.md.
- Apply mandatory skills: Superpowers, Task Observer, Ponytail, Full Output Enforcement, Impeccable. Remember completion report syntax: "Đã dùng x skill gồm: ...".

TASK OBJECTIVE:
Adversarially challenge Milestone 2 (Course Prerequisite Gating, Lesson Media & Student Lifecycle):
1. Adversarially stress-test `student/course_detail.html`, `student/lesson.html`, `student/my_learning.html`, and `student/become_instructor.html`:
   - Verify prerequisite gating: when prerequisites are missing, ensure enrollment form is disabled, button displays "Chưa đủ điều kiện", and alert "Ghi danh bị chặn do chưa đạt điều kiện tiên quyết" renders.
   - Verify lesson viewer: lesson navigation list, video/doc stream, resource list, and `lesson-progress-badge`.
   - Verify student lifecycle e2e flow.
2. Run test suites:
   - `python scripts/repo_check.py`
   - `python -m pytest tests/api/test_student_portal_ui.py tests/e2e/test_student_lifecycle_e2e.py -v`
3. State your explicit VERDICT in handoff.md: APPROVE or REQUEST_CHANGES.
Send a message to your parent when done.
