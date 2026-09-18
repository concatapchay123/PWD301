# Orchestration Plan — Stitch Frontend Migration

## Objective
Tích hợp và chuyển đổi toàn diện 33 màn hình Stitch (`frontend-preview/`) vào hệ thống Flask Web (`src/pwd301/templates`, `src/pwd301/static`), bốc tách data binding và backend context, bảo toàn 100% logic xác thực (Flask session, CSRF, RBAC, Timezone, i18n) và đảm bảo các luồng nghiệp vụ Học viên, Giảng viên, Quản trị viên hoạt động trơn tru, vượt qua toàn bộ test suite.

## Execution Pattern: Project Pattern
Orchestrator 5 acts as Project Orchestrator, delegating all investigation, implementation, review, challenge, and audit to subagents.

### Step 0: Survey Phase (Current)
- Dispatch 3 parallel Explorers:
  1. `explorer_survey_shell`: App shell architecture, Tailwind CDN, typography, Material symbols, Topbar (timezone, i18n, switch-role), dynamic 276px Sidebar, modal/toast engine, base.html & static assets.
  2. `explorer_survey_student`: 9 Student Portal Stitch screens vs Flask templates (dashboard, my_learning, course_detail, lesson, assessment_detail/waiting room, attempt, result, ai_assistant, become_instructor).
  3. `explorer_survey_instructor_admin`: Instructor & Admin Stitch screens vs Flask templates (instructor dashboard, courses, course_manage, question_bank, assessment_builder 5 screens, grading 50/50 canvas, admin telemetry dashboard, operations/audit/backups, instructor_applications, auth lifecycle).
- Aggregate reports into `PROJECT.md` Feature Inventory & Architecture.

### Step 1: Milestone 1 — Core App Shell, Tailwind, Design Tokens & Base Templates (R1)
- Implement updated `base.html`, navigation topbar & sidebar, toast & modal mechanics.
- Review -> Challenge -> Audit -> Gate.

### Step 2: Milestone 2 — Student Portal Integration & Real-Time Exam Workflows (R2)
- Implement 9 student portal templates, UTC countdown, autosave, lease anti-cheat, result views, AI assistant, become instructor card.
- Review -> Challenge -> Audit -> Gate.

### Step 3: Milestone 3 — Instructor Portal Integration, Azota Assessment Builder & Grading Studio (R3)
- Implement instructor dashboard, courses table, course manage, question bank studio, Azota 5-step builder, 50/50 essay grading studio.
- Review -> Challenge -> Audit -> Gate.

### Step 4: Milestone 4 — Admin & Auth Portal Integration, Telemetry & Account Lifecycle (R4)
- Implement admin dashboard with live hardware telemetry, operations cockpit, audit logs, backup management, instructor applications review modal, auth screens (login, register, forgot password).
- Review -> Challenge -> Audit -> Gate.

### Step 5: Milestone 5 — Full Test Suite Verification, Anti-Regression & Security Hardening (R5)
- Run complete test suite (pytest, repo_check.py, ruff, mypy), fix any regressions, verify invariants and performance.
- Final Review -> Challenger -> Forensic Auditor -> Gate.
