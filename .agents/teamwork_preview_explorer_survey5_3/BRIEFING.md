# BRIEFING — 2026-09-16T05:21:45Z

## Mission
Analyze and map Objectives R3 (Instructor Portal) & R4 (Admin & Auth Portals) integration from frontend-preview Stitch screens to Flask Jinja templates with data bindings, form contracts, and test preservation.

## 🔒 My Identity
- Archetype: explorer
- Roles: investigation, synthesis
- Working directory: E:\PWD301\.agents\teamwork_preview_explorer_survey5_3
- Original parent: 4946890a-b666-4014-a18b-0a588b75fb4e (teamwork_preview_orchestrator_5)
- Milestone: Survey & Mapping (R3 & R4: Instructor, Admin, Auth)

## 🔒 Key Constraints
- Read-only investigation — do NOT implement or write source code files.
- Write only to working directory: E:\PWD301\.agents\teamwork_preview_explorer_survey5_3\
- Mandated skills: Superpowers, Task Observer, Ponytail, Full Output Enforcement, Impeccable.
- Mandatory completion syntax: "Đã dùng x skill gồm: ..."

## Current Parent
- Conversation ID: 4946890a-b666-4014-a18b-0a588b75fb4e
- Updated: 2026-09-16T05:18:05Z

## Investigation State
- **Explored paths**:
  - `frontend-preview/stitch_pwd301_course_management_platform/` and `frontend-preview/stitch_pwd301_course_management_platform (1)/`
  - `src/pwd301/templates/instructor/` (7 templates)
  - `src/pwd301/templates/admin/` (7 templates)
  - `src/pwd301/templates/auth/` (5 templates)
  - `src/pwd301/blueprints/instructor/routes.py` (2,771 lines)
  - `src/pwd301/blueprints/admin/routes.py` (999 lines)
  - `src/pwd301/blueprints/auth/routes.py` (681 lines)
  - Tests: `tests/api/test_instructor_course_web_flow.py`, `tests/api/test_instructor_application_web_flow.py`, `tests/api/test_auth_web.py`, `tests/api/test_admin_audit_api.py`, `tests/test_m3_assessment_authoring.py`
- **Key findings**:
  - Full screen-to-template mapping established for all 10+ target views.
  - Crucial test string assertions identified: `Đăng nhập PWD301`, `Đăng ký tài khoản`, `Khóa học mới đã được tạo thành công`, `Cập nhật thông tin khóa học thành công`.
  - Form actions and CSRF requirements cataloged.
  - 32/32 baseline test cases passing in 26.77s.
  - Special interactive patterns (Azota 50/50 raw syntax & validation, 50/50 essay grading canvas, live hardware telemetry) documented with exact data-binding contracts.
- **Unexplored areas**: None. Full scope of R3 & R4 surveyed.

## Key Decisions Made
- Confirmed template-by-template mapping, data models, and form contracts.
- Prepared comprehensive handoff report for Milestones 3 & 4 implementation.

## Artifact Index
- E:\PWD301\.agents\teamwork_preview_explorer_survey5_3\DISPATCH.md — incoming dispatch records
- E:\PWD301\.agents\teamwork_preview_explorer_survey5_3\BRIEFING.md — situational awareness index
- E:\PWD301\.agents\teamwork_preview_explorer_survey5_3\progress.md — heartbeat progress tracker
- E:\PWD301\.agents\teamwork_preview_explorer_survey5_3\handoff.md — 5-component handoff report (deliverable)
