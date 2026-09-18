# Execution Plan — Orchestrator 6

## Phase 1: Finalize Milestone 2 Verification Gate
1. Create directories and dispatch gate evaluation team for M2:
   - 2 Reviewers: `teamwork_preview_reviewer_m2_6_1`, `teamwork_preview_reviewer_m2_6_2`
   - 2 Challengers: `teamwork_preview_challenger_m2_6_1`, `teamwork_preview_challenger_m2_6_2`
   - 1 Forensic Auditor: `teamwork_preview_auditor_m2_6`
2. Aggregate reports into `GATE_STATUS.md`.
3. If all pass (APPROVE, CLEAN, build/tests pass), mark M2 DONE in `PROJECT.md` and `progress.md`.

## Phase 2: Milestone 3 — Instructor Portal Integration (R3)
Scope: 6 instructor templates (`dashboard.html`, `courses.html`, `course_manage.html`, `question_bank.html`, `assessment_builder.html` [5-screen Azota standard], `grading.html` & `grade_attempt.html` [50/50 canvas]).
1. Dispatch Explorers / Spec Miner for M3 to map Stitch screens, view routes, and context variables.
2. Dispatch Worker for M3 to implement templates and run tests.
3. Dispatch Reviewers, Challengers, and Forensic Auditor for M3 gate.
4. If gate passes, mark M3 DONE.

## Phase 3: Milestone 4 — Admin & Auth Portal Integration (R4)
Scope: Admin telemetry dashboard, operations/audit/backups, instructor applications, and auth lifecycle (`login.html`, `register.html`, `forgot_password.html`).
1. Dispatch Explorers / Spec Miner for M4.
2. Dispatch Worker for M4.
3. Dispatch Reviewers, Challengers, and Forensic Auditor for M4 gate.
4. If gate passes, mark M4 DONE.

## Phase 4: Milestone 5 — Full Verification & Hardening (R5)
Scope: Run full pytest test suite (100% pass), ruff check & format, mypy, and scripts/repo_check.py.
1. Dispatch Worker / Challengers / Auditor for final systemic verification.
2. Compile AUDIT_REPORT and prepare final victory handoff to Sentinel.
