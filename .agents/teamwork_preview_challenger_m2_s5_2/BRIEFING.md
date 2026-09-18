# BRIEFING — 2026-09-16T12:45:00+07:00

## Mission
Adversarially challenge Milestone 2 (Course Prerequisite Gating, Lesson Media & Student Lifecycle), stress-test student templates and lifecycle flows, execute verification suites, and deliver an empirical challenge report with explicit verdict.

## 🔒 My Identity
- Archetype: empirical challenger
- Roles: critic, specialist
- Working directory: E:\PWD301\.agents\teamwork_preview_challenger_m2_s5_2
- Original parent: teamwork_preview_orchestrator_5 (Conversation ID: 4946890a-b666-4014-a18b-0a588b75fb4e)
- Milestone: M2 (Student Portal Integration)
- Instance: 2 of 2 (s5_2)

## 🔒 Key Constraints
- Review-only — do NOT modify implementation code unless creating test harnesses / generators outside `.agents/` or running verification scripts.
- Do NOT trust worker claims or logs; execute verification commands and stress harnesses directly.
- Report explicit VERDICT: APPROVE or REQUEST_CHANGES in handoff.md.
- Follow 5-component handoff report protocol: Observation, Logic Chain, Caveats, Conclusion, Verification Method.
- Mandatory skill reporting syntax: "Đã dùng x skill gồm: ...".

## Current Parent
- Conversation ID: 4946890a-b666-4014-a18b-0a588b75fb4e
- Updated: 2026-09-16T12:45:00+07:00

## Review Scope
- **Files to review**:
  - `src/pwd301/templates/student/course_detail.html`
  - `src/pwd301/templates/student/lesson.html`
  - `src/pwd301/templates/student/my_learning.html`
  - `src/pwd301/templates/student/become_instructor.html`
- **Verification Suites**:
  - `python scripts/repo_check.py`
  - `python -m pytest tests/api/test_student_portal_ui.py tests/e2e/test_student_lifecycle_e2e.py -v`
  - Custom stress tests & adversarial checks for prerequisite gating, lesson streaming, and lifecycle flows.
- **Interface contracts**: `PROJECT.md`, `AGENTS.md`, `ORIGINAL_REQUEST.md`, System Specification invariants.

## Attack Surface
- **Hypotheses tested**:
  - H1: Prerequisite gating bypass: Can an uneligible student submit enrollment or does UI disable button + render exact warning "Ghi danh bị chặn do chưa đạt điều kiện tiên quyết"?
  - H2: Course capacity limit: Does is_full properly block enrollment?
  - H3: Lesson reader layout & components: Are lesson links, video stream, doc stream, resource vault, and `lesson-progress-badge` present and functional?
  - H4: My learning workspace: Do status filtering, leave/re-enroll CSRF actions work as expected?
  - H5: Become instructor dossier: Are pending status, application form, cancellation CSRF token intact?
  - H6: Student lifecycle e2e flow: Does full register -> browse -> prerequisite check -> enroll -> study lesson -> complete lesson work end-to-end?
- **Vulnerabilities found**: TBD
- **Untested angles**: TBD

## Loaded Skills
- **Superpowers (verification-before-completion)**:
  - Source: `C:\Users\LENOVO\.gemini\config\skills\verification-before-completion\SKILL.md`
  - Core methodology: Evidence before claims; execute full commands and check real exit codes and outputs.
- **Task Observer**:
  - Source: `C:\Users\LENOVO\.gemini\config\skills\task-observer\SKILL.md`
  - Core methodology: Monitor execution for skill discovery and capture friction/patterns.
- **Ponytail**:
  - Source: `C:\Users\LENOVO\.gemini\config\skills\ponytail\SKILL.md`
  - Core methodology: Minimal viable solution, eliminate overengineering and bloat.
- **Full Output Enforcement**:
  - Source: `C:\Users\LENOVO\.gemini\config\skills\output-skill\SKILL.md`
  - Core methodology: Never truncate or use placeholders in code or deliverables.
- **Impeccable**:
  - Source: `C:\Users\LENOVO\.gemini\config\skills\impeccable\SKILL.md`
  - Core methodology: Productive Clarity, design craft, responsiveness, and accessibility review.

## Key Decisions Made
- [2026-09-16] Initialized challenger workspace. Will run baseline verification scripts first, then inspect template code, create adversarial test cases, and verify results.

## Artifact Index
- `E:\PWD301\.agents\teamwork_preview_challenger_m2_s5_2\DISPATCH.md` — Incoming dispatch instructions
- `E:\PWD301\.agents\teamwork_preview_challenger_m2_s5_2\BRIEFING.md` — Agent state and memory
- `E:\PWD301\.agents\teamwork_preview_challenger_m2_s5_2\progress.md` — Heartbeat & execution log
- `E:\PWD301\.agents\teamwork_preview_challenger_m2_s5_2\handoff.md` — Final challenge report
