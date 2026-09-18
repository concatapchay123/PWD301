# BRIEFING — 2026-09-16T12:53:07+07:00

## Mission
Orchestrate completion of PWD301 full frontend migration across Student, Instructor, and Admin/Auth portals, culminating in full test suite pass and forensic verification.

## 🔒 My Identity
- Archetype: teamwork_preview_orchestrator
- Roles: orchestrator, user_liaison, human_reporter, successor
- Working directory: E:\PWD301\.agents\teamwork_preview_orchestrator_6
- Original parent: parent
- Original parent conversation ID: 760cc20a-07cb-4547-9962-ea5f525f9c7f

## 🔒 My Workflow
- **Pattern**: Project Pattern
- **Scope document**: E:\PWD301\.agents\PROJECT.md
1. **Decompose**: Decompose by module boundaries into milestones (M1-M5).
2. **Dispatch & Execute**: Direct iteration loop: Explorer -> Worker -> Reviewers -> Challengers -> Auditor -> Gate check.
3. **On failure**: Retry -> Replace -> Skip -> Redistribute -> Redesign.
4. **Succession**: Self-succeed at 16 spawns, write handoff.md, spawn successor.
- **Work items**:
  1. Milestone 1: Core App Shell & Design System [DONE]
  2. Milestone 2: Student Portal Integration [DONE]
  3. Milestone 3: Instructor Portal Integration [IN_PROGRESS]
  4. Milestone 4: Admin & Auth Portal Integration [PLANNED]
  5. Milestone 5: Full Verification & Hardening [PLANNED]
- **Current phase**: 2B (Executing Milestone 3: Instructor Portal Integration)
- **Current focus**: Milestone 3: Instructor Portal Integration

## 🔒 Key Constraints
- PURE DISPATCH-ONLY: NEVER write code directly. Delegate ALL work to subagents via invoke_subagent.
- Never reuse a subagent after it has delivered its handoff — always spawn fresh.
- Binary veto on Auditor violation: If Forensic Auditor reports INTEGRITY VIOLATION, fail unconditionally.
- Adhere to Superpowers, Task Observer, Ponytail, Full Output Enforcement, Impeccable, and Vietnamese completion reporting syntax.

## Current Parent
- Conversation ID: 760cc20a-07cb-4547-9962-ea5f525f9c7f
- Updated: not yet

## Key Decisions Made
- M1 verified and complete.
- M2 verified through 2 gate iterations and complete: 100% tests pass, forensic audit CLEAN, all defensive UX & customization requirements satisfied.
- M3 proceeding: Instructor portal templates, Azota 5-screen assessment builder, and 50/50 grading studio.

## Team Roster
| Agent | Type | Work Item | Status | Conv ID |
|-------|------|-----------|--------|---------|
| reviewer_m2_6_1 | teamwork_preview_reviewer | M2 Review (Syntax, Data Bindings, CSRF) | completed (REQUEST_CHANGES) | 1e920f98-fb09-445f-adc7-434126ed47b7 |
| reviewer_m2_6_2 | teamwork_preview_reviewer | M2 Review (Defensive UX, Anti-cheat) | completed (APPROVE) | 76f2ddaf-3abf-48ce-8ef4-44e73ecadea9 |
| challenger_m2_6_1 | teamwork_preview_challenger | M2 Challenge (Exam Countdown, Autosave) | completed (APPROVE) | 05b4b685-ac2e-4c85-8a6b-c333d751cc1f |
| challenger_m2_6_2 | teamwork_preview_challenger | M2 Challenge (Boundary cases, Quarantined) | completed (REQUEST_CHANGES) | 673f22fe-7cfd-424b-bfe2-5f966463be56 |
| auditor_m2_6 | teamwork_preview_auditor | M2 Forensic Integrity Audit | completed (CLEAN) | 63b02ee5-0f7d-4eb7-8fdd-cd4dcdc26a27 |
| worker_m2_it2 | teamwork_preview_worker | M2 Remediation (course_detail, lesson, tests) | completed (DONE) | 0ee8abcd-dc0c-4980-b2f3-f75333cd9724 |
| reviewer_m2_it2 | teamwork_preview_reviewer | M2 It2 Review (Remediation verification) | completed (APPROVE) | cdca8d4c-c608-4ff5-8c1f-72c6f876c65f |
| challenger_m2_it2 | teamwork_preview_challenger | M2 It2 Challenge (Empirical Stress re-check) | completed (APPROVE) | 4cde0e78-3f9f-4b9e-b5d1-0a7f00fcd221 |
| auditor_m2_it2 | teamwork_preview_auditor | M2 It2 Forensic Audit (Integrity verification) | completed (CLEAN) | e9d3e643-6d35-4ec5-9738-985d6b78cbdd |

## Succession Status
- Succession required: no
- Spawn count: 9 / 16
- Pending subagents: none
- Predecessor: teamwork_preview_orchestrator_5
- Successor: not yet spawned

## Active Timers
- Heartbeat cron: ebbe1ae6-5ba3-416c-a025-e0178c543130/task-30
- Safety timer: none

## Artifact Index
- E:\PWD301\.agents\PROJECT.md — Global Project Scope and Feature Inventory
- E:\PWD301\.agents\ORIGINAL_REQUEST.md — Original User Request
