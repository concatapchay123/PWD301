# BRIEFING — 2026-09-16T12:45:00+07:00

## Mission
Tích hợp và chuyển đổi toàn diện hệ thống frontend mới từ 33 màn hình Stitch (frontend-preview/) vào hệ thống Flask Web (src/pwd301/templates, src/pwd301/static), bốc tách data binding và backend context từ frontend cũ, bảo toàn 100% logic xác thực (Flask session, CSRF, RBAC, Timezone, i18n) và đảm bảo các luồng nghiệp vụ Học viên, Giảng viên, Quản trị viên hoạt động trơn tru, vượt qua toàn bộ test suite.

## 🔒 My Identity
- Archetype: teamwork_preview_orchestrator
- Roles: orchestrator, user_liaison, human_reporter, successor
- Working directory: E:\PWD301\.agents\teamwork_preview_orchestrator_5
- Original parent: parent
- Original parent conversation ID: 760cc20a-07cb-4547-9962-ea5f525f9c7f

## 🔒 My Workflow
- **Pattern**: Project Pattern
- **Scope document**: E:\PWD301\.agents\PROJECT.md
1. **Decompose**: Survey full scope (Survey Phase completed) and maintain PROJECT.md feature inventory and milestones M1-M5.
2. **Dispatch & Execute**: Direct iteration loop per milestone: Explorer(s) -> Worker -> Reviewer(s) -> Challenger(s) -> Forensic Auditor -> Gate.
3. **On failure**: Retry -> Replace -> Skip -> Redistribute -> Redesign -> Escalate.
4. **Succession**: Self-succeed at 16 spawns.
- **Work items**:
  1. Survey: Map 33 Stitch screens, current Flask templates, backend route bindings, and test requirements [done]
  2. M1: Core App Shell, Tailwind, Design Tokens, Navigation, Modals & Toasts (R1) [done]
  3. M2: Student Portal Integration & Real-Time Exam/Waiting Room Interactions (R2) [in-progress - verification running]
  4. M3: Instructor Portal Integration, Azota Assessment Builder & 50/50 Grading (R3) [pending]
  5. M4: Admin & Auth Portal Integration, Hardware Telemetry & Account Lifecycle (R4) [pending]
  6. M5: Full Verification, Anti-Regression, Invariants & Security Hardening (R5) [pending]
- **Current phase**: 2 (Milestone 2 Verification Gate)
- **Current focus**: Milestone 2 verification by 2 Reviewers, 2 Challengers, and 1 Forensic Auditor

## 🔒 Key Constraints
- Strictly DISPATCH-ONLY orchestrator: NEVER write source code or run build/test commands directly.
- Delegate all technical exploration, implementation, review, challenge, and audit to subagents via invoke_subagent.
- Never reuse a subagent after it has delivered its handoff.
- Mandatory audit gating: Forensic auditor INTEGRITY VIOLATION is a hard binary veto.
- Adhere strictly to AGENTS.md, docs/system, docs/database, and Mandatory Agent Skills.
- User Rules: Superpowers, Task Observer, Ponytail, Full Output Enforcement, Impeccable, and completion reporting syntax.

## Current Parent
- Conversation ID: 760cc20a-07cb-4547-9962-ea5f525f9c7f
- Updated: 2026-09-16T12:17:35+07:00

## Key Decisions Made
- Milestone 1 Gate PASSED (all 5 verification agents approved, CLEAN forensic audit).
- Milestone 1 marked DONE in PROJECT.md.
- Milestone 2 implementation completed by `teamwork_preview_worker_m2_s5` (16/16 student portal tests, 21/21 web flow tests, 1/1 lifecycle e2e pass).
- Dispatched 5 verification agents for M2 Gate:
  1. `teamwork_preview_reviewer_m2_s5_1` (c4364994)
  2. `teamwork_preview_reviewer_m2_s5_2` (2f2f3311)
  3. `teamwork_preview_challenger_m2_s5_1` (144c34b1)
  4. `teamwork_preview_challenger_m2_s5_2` (edbe375e)
  5. `teamwork_preview_auditor_m2_s5` (f672d3ec)

## Team Roster
| Agent | Type | Work Item | Status | Conv ID |
|-------|------|-----------|--------|---------|
| explorer_survey5_1 | teamwork_preview_explorer | App Shell Survey (R1) | completed | a4e80ca9-0398-426f-8b15-dcde074408cd |
| explorer_survey5_2 | teamwork_preview_explorer | Student Portal Survey (R2) | completed | 2c8d8b1e-9ffe-4093-9e39-e0ee6d3b252e |
| explorer_survey5_3 | teamwork_preview_explorer | Instructor/Admin Survey (R3/R4) | completed | 62e60c5f-e7d9-493d-b66c-ec664045a051 |
| worker_m1 | teamwork_preview_worker | Implement Milestone 1 App Shell | completed | e77038af-bcbb-4c94-adce-7e41c681ddd4 |
| reviewer_m1_s5_1 | teamwork_preview_reviewer | Review App Shell M1 | completed (APPROVE) | 9bb11657-66a4-4aab-a265-5c7ea89cf575 |
| reviewer_m1_s5_2 | teamwork_preview_reviewer | Review Tokens M1 | completed (APPROVE) | dea2db68-37a1-4948-ba83-a759c9872c27 |
| challenger_m1_s5_1 | teamwork_preview_challenger | Challenge DOM M1 | completed (APPROVE) | 3e19e056-4297-434b-90bd-a32271395583 |
| challenger_m1_s5_2 | teamwork_preview_challenger | Challenge CSS M1 | completed (APPROVE) | 5fd9bd16-8d70-4870-9b84-d7521946dffa |
| auditor_m1_s5 | teamwork_preview_auditor | Forensic Integrity Audit M1 | completed (CLEAN) | 4ee7fea2-f9fa-4f45-b2d1-a8b2409fa336 |
| worker_m2_s5 | teamwork_preview_worker | Implement Milestone 2 Student Portal | completed | c36ad144-f3cf-4755-b6fb-c581e7487942 |
| reviewer_m2_s5_1 | teamwork_preview_reviewer | Review Student Portal Templates M2 | in-progress | c4364994-f94f-4b27-8d83-d61575351c15 |
| reviewer_m2_s5_2 | teamwork_preview_reviewer | Review Student Lifecycle & Forms M2 | in-progress | 2f2f3311-ee09-40d6-9e9c-783ec531bb80 |
| challenger_m2_s5_1 | teamwork_preview_challenger | Challenge Exam Console & Lease M2 | in-progress | 144c34b1-81f5-446c-94da-055f43d0e932 |
| challenger_m2_s5_2 | teamwork_preview_challenger | Challenge Prerequisites & Lesson M2 | in-progress | edbe375e-3ae5-45bf-83d9-6facd6b745cd |
| auditor_m2_s5 | teamwork_preview_auditor | Forensic Integrity Audit M2 | in-progress | f672d3ec-66b1-45f7-a878-d9cdb377565f |

## Succession Status
- Succession required: no
- Spawn count: 15 / 16
- Pending subagents: c4364994, 2f2f3311, 144c34b1, edbe375e, f672d3ec
- Predecessor: teamwork_preview_orchestrator_4
- Successor: not yet spawned

## Active Timers
- Heartbeat cron: 4946890a-b666-4014-a18b-0a588b75fb4e/task-26
- Safety timer: none

## Artifact Index
- E:\PWD301\.agents\ORIGINAL_REQUEST.md — Original User Request
- E:\PWD301\.agents\PROJECT.md — Master Project Specification & Decomposition
- E:\PWD301\.agents\teamwork_preview_worker_m1\handoff.md — Worker M1 report
- E:\PWD301\.agents\teamwork_preview_worker_m2_s5\handoff.md — Worker M2 report
- E:\PWD301\.agents\teamwork_preview_orchestrator_5\GATE_STATUS.md — Gate tracker (M1: PASS, M2: IN_PROGRESS)
- E:\PWD301\.agents\teamwork_preview_orchestrator_5\BRIEFING.md — Persistent working memory
- E:\PWD301\.agents\teamwork_preview_orchestrator_5\progress.md — Liveness & progress tracker
