# DISPATCH: teamwork_preview_auditor_m2_6

Working Directory: E:\PWD301\.agents\teamwork_preview_auditor_m2_6
Parent: teamwork_preview_orchestrator_6 (ebbe1ae6-5ba3-416c-a025-e0178c543130)
Original Request: E:\PWD301\.agents\ORIGINAL_REQUEST.md
Scope Document: E:\PWD301\.agents\PROJECT.md
Worker Handoff to Audit: E:\PWD301\.agents\teamwork_preview_worker_m2_s5\handoff.md

## Objective
Forensic Integrity Audit of Milestone 2 (Student Portal Integration) across all 10 templates in `src/pwd301/templates/student/`.

## Audit Focus
- Inspect templates for authentic data binding vs hardcoded mocks / cheating strings.
- Verify zero JWT in localStorage (Flask session authentication must be used).
- Verify CSRF token presence on all POST forms and AJAX payloads.
- Verify that internal BigInt primary keys are NOT exposed directly (UUID masking maintained).
- Verify no dummy/facade bypasses designed to pass tests without genuine template logic.
- Run tests:
  - `.venv\Scripts\python.exe -m pytest tests/api/test_student_portal_ui.py -v`
  - `.venv\Scripts\python.exe -m pytest tests/api/test_web_ui_flow_fixes.py -v`
- Deliver verdict in `handoff.md` (CLEAN or INTEGRITY VIOLATION). Use send_message to notify parent.
- End response with Vietnamese completion report: `Đã dùng x skill gồm: ...`

## 2026-09-16T05:54:27Z
You are auditor_m2_6.
Working directory: E:\PWD301\.agents\teamwork_preview_auditor_m2_6
Scope document: E:\PWD301\.agents\PROJECT.md
Original request: E:\PWD301\.agents\ORIGINAL_REQUEST.md
Worker handoff: E:\PWD301\.agents\teamwork_preview_worker_m2_s5\handoff.md
Read DISPATCH.md in your working directory and conduct a forensic integrity audit on Milestone 2 (Student Portal Integration).
Verify authentic data bindings, no dummy facades, no hardcoded answers, no JWT in localStorage, strict CSRF protection, UUID masking, and test pass integrity.
Write your forensic report and verdict (CLEAN or INTEGRITY VIOLATION) in handoff.md in your working directory.
Use send_message to report your completion and verdict to parent (ebbe1ae6-5ba3-416c-a025-e0178c543130).
End with: Đã dùng x skill gồm: ...
