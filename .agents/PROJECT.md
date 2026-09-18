# Project: PWD301 Full Frontend Migration & Stitch Integration

## Architecture
PWD301 is a full-featured enterprise LMS built on Flask and Microsoft SQL Server architecture, supporting three distinct user personas: Students, Instructors, and System Administrators.
The system is migrating from legacy Bootstrap-centric templates to the modern, high-craft **Productive Clarity / Carbon** design system derived from 33 Stitch UI screens (`frontend-preview/`).

### Core Architecture & Invariants
1. **Server-Authoritative Sessions**: All Web UI interactions rely on HTTP-only, secure Flask sessions with strict CSRF tokens on all mutating requests. No JWT tokens are placed in localStorage.
2. **Design Tokens & Tailwind CDN**: Clean integration of Tailwind CSS CDN (with forms and container queries plugins), Google Fonts (`Plus Jakarta Sans`, `Inter`, `JetBrains Mono`), and `Material Symbols Outlined`, with zero FOUC via pre-paint inline scripts.
3. **Role-Based Navigation**: Dynamic 276px Sidebar switching between Student, Instructor, and Admin views with responsive collapse (74px mini-rail) and mobile offcanvas drawer.
4. **Interactive Reliability**: Real-time UTC exam countdowns, monotonic autosave with client-sequence numbers, single-editing lease anti-cheat, and split-view 50/50 canvas for grading and Azota assessment authoring.
5. **Fail-Closed Security & Clean Contracts**: Retention of UUID masking for internal BigInt primary keys (ADR-002), strict ClamAV file quarantine checks, and zero breakage of existing backend routes or pytest assertions.

---

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | F1: Design Tokens & Typography CDN | Integrate Tailwind CSS CDN, Plus Jakarta Sans, Inter, JetBrains Mono, Material Symbols Outlined into base.html | M1 | Survey 5.1 / R1 |
| 2 | F2: Anti-FOUC & Dark Mode Sync | Implement pre-paint script to toggle `.dark` class, sync data attributes, and restore sidebar state | M1 | Survey 5.1 / R1 |
| 3 | F3: Modernized Topbar | Topbar with live UTC time clock, language switcher (VI/EN), unread notification badge, switch-role dropdown | M1 | Survey 5.1 / R1 |
| 4 | F4: Dynamic 276px Role Sidebar | Dynamic sidebar for Student, Instructor, Admin with active state tracking, label preservation, 74px collapse | M1 | Survey 5.1 / R1 |
| 5 | F5: Toast & Modal Engine | Toast container (`#toast-container`) and modal popup framework preserving all test selectors | M1 | Survey 5.1 / R1 |
| 6 | F6: Script Harmony & Context Helpers | Harmonize theme.js, components.js, motion.js, app_shell.js and add unread notification context helper | M1 | Survey 5.1 / R1 |
| 7 | F7: Student Dashboard | Modern action-centric dashboard with learning stats, active courses, upcoming exams, recent results | M2 | Survey 5.2 / R2 |
| 8 | F8: Student My Learning Hub | Course workspace with status tabs, enrollment cards, leave/re-enroll actions, progress resumption | M2 | Survey 5.2 / R2 |
| 9 | F9: Student Course Detail | Split master-detail course page with prerequisite DAG validation, capacity alerts, syllabus overview | M2 | Survey 5.2 / R2 |
| 10 | F10: Student Lesson Reader & Zen Mode | 3-column academic console with curriculum drawer, video/doc stream, and focus Zen reader tab | M2 | Survey 5.2 / R2 |
| 11 | F11: Assessment Waiting Room | Dedicated pre-exam waiting room with server UTC synchronized countdown clock and rules checklist | M2 | Survey 5.2 / R2 |
| 12 | F12: Assessment Attempt Console | Master exam console with contextual navigator, monotonic autosave (`client_sequence`), lease anti-cheat | M2 | Survey 5.2 / R2 |
| 13 | F13: Assessment Results View | Clean review drawer with question-by-question review, score breakdowns, correct answer comparisons | M2 | Survey 5.2 / R2 |
| 14 | F14: Student AI Workspace | Contextual AI chat workspace with active course/lesson scoping and grounded citations | M2 | Survey 5.2 / R2 |
| 15 | F15: Become Instructor Card | Application profile card for students applying to become instructors with status feedback | M2 | Survey 5.2 / R2 |
| 16 | F16: Instructor Dashboard | Minimalist instructor dashboard with course KPIs, SLA trackers, and quick action cards | M3 | Survey 5.3 / R3 |
| 17 | F17: Instructor Courses Table | Master operations table for instructor courses with modal for creation (category, difficulty, capacity) | M3 | Survey 5.3 / R3 |
| 18 | F18: Instructor Course Manage Hub | 5-tab course management cockpit and low-tech visual lesson authoring studio | M3 | Survey 5.3 / R3 |
| 19 | F19: Instructor Question Bank Studio | Comprehensive question bank operations table with Bloom levels, difficulty, versioning | M3 | Survey 5.3 / R3 |
| 20 | F20: Azota Assessment Builder | 5-screen Azota exam builder wizard (method selector, config, 50/50 raw syntax editor, validation) | M3 | Survey 5.3 / R3 |
| 21 | F21: Instructor 50/50 Grading Studio | Split-canvas 50/50 essay grading studio (frozen snapshot on left, rubric/points on right) | M3 | Survey 5.3 / R3 |
| 22 | F22: Admin Governance Dashboard | Academic command center with live AJAX hardware telemetry (CPU, RAM, Disk, Network) | M4 | Survey 5.3 / R4 |
| 23 | F23: Admin Operations & Security Cockpit | Split operations cockpit for system health, audit log inspection, and database backup/restore | M4 | Survey 5.3 / R4 |
| 24 | F24: Admin Instructor Applications | Application evaluation queue with modal for approval/rejection and rationale recording | M4 | Survey 5.3 / R4 |
| 25 | F25: Auth Account Lifecycle Screens | Focused card interactive inspector for Login, Register, Forgot Password, Reset Password | M4 | Survey 5.3 / R4 |
| 26 | F26: End-to-End Test Suite Passing | 100% pass on pytest test suite, zero template syntax or runtime errors | M5 | Acceptance / R5 |
| 27 | F27: Code Quality & Static Typing | Zero warnings on ruff check, ruff format --check, mypy src, and repo_check.py | M5 | Acceptance / R5 |
| 28 | F28: Forensic Integrity Audit | Independent verification of zero cheating, genuine implementation, and security invariants | M5 | Acceptance / R5 |

---

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Core App Shell & Design System | F1, F2, F3, F4, F5, F6: base.html, Tailwind CDN, tokens, topbar, sidebar, toasts, modals, theme/script harmony | none | DONE |
| M2 | Student Portal Integration | F7, F8, F9, F10, F11, F12, F13, F14, F15: 9 student templates, UTC exam countdown, autosave, lease anti-cheat | M1 | DONE |
| M3 | Instructor Portal Integration | F16, F17, F18, F19, F20, F21: 6 instructor templates, Azota 5-screen builder, 50/50 essay grading studio | M1 | PLANNED |
| M4 | Admin & Auth Portal Integration | F22, F23, F24, F25: admin telemetry dashboard, operations/audit/backups, instructor apps, auth lifecycle | M1 | PLANNED |
| M5 | Full Verification & Hardening | F26, F27, F28: pytest 100% pass, ruff, mypy, repo_check.py, adversarial verification, forensic audit | M1, M2, M3, M4 | PLANNED |

---

## Code Layout & Ownership Boundaries
- **App Shell & Static Assets (M1)**:
  - `src/pwd301/templates/base.html`
  - `src/pwd301/static/js/theme.js`
  - `src/pwd301/static/js/components.js`
  - `src/pwd301/static/js/app_shell.js`
  - `src/pwd301/static/css/app.css`
  - `src/pwd301/__init__.py`
- **Student Portal Templates (M2)**:
  - `src/pwd301/templates/student/dashboard.html`
  - `src/pwd301/templates/student/my_learning.html`
  - `src/pwd301/templates/student/course_detail.html`
  - `src/pwd301/templates/student/lesson.html`
  - `src/pwd301/templates/student/assessment_detail.html`
  - `src/pwd301/templates/student/attempt.html`
  - `src/pwd301/templates/student/result.html`
  - `src/pwd301/templates/student/ai_assistant.html`
  - `src/pwd301/templates/student/become_instructor.html`
- **Instructor Portal Templates (M3)**:
  - `src/pwd301/templates/instructor/dashboard.html`
  - `src/pwd301/templates/instructor/courses.html`
  - `src/pwd301/templates/instructor/course_manage.html`
  - `src/pwd301/templates/instructor/question_bank.html`
  - `src/pwd301/templates/instructor/assessment_builder.html`
  - `src/pwd301/templates/instructor/grading.html`
  - `src/pwd301/templates/instructor/grade_attempt.html`
- **Admin & Auth Templates (M4)**:
  - `src/pwd301/templates/admin/dashboard.html`
  - `src/pwd301/templates/admin/operations.html`
  - `src/pwd301/templates/admin/audit_logs.html`
  - `src/pwd301/templates/admin/backups.html`
  - `src/pwd301/templates/admin/instructor_applications.html`
  - `src/pwd301/templates/auth/login.html`
  - `src/pwd301/templates/auth/register.html`
  - `src/pwd301/templates/auth/forgot_password.html`
