# BRIEFING — 2026-09-16T05:29:15Z

## Mission
Implement Milestone 1: Core App Shell & Design System Integration (base.html, theme.js, components.js, app.css, __init__.py).

## 🔒 My Identity
- Archetype: implementer, qa, specialist
- Roles: implementer, qa, specialist
- Working directory: E:\PWD301\.agents\teamwork_preview_worker_m1
- Original parent: 4946890a-b666-4014-a18b-0a588b75fb4e
- Milestone: Milestone 1 — Core App Shell & Design System Integration

## 🔒 Key Constraints
- Exclusively owned files: src/pwd301/templates/base.html, src/pwd301/static/js/theme.js, src/pwd301/static/js/components.js, src/pwd301/static/css/app.css, src/pwd301/__init__.py
- DO NOT CHEAT: Genuine implementation, no hardcoding test strings in app logic.
- Must preserve all existing test contract selectors, markers, flash messages loop, modal, toast classes.
- Verification commands: python scripts/repo_check.py, pytest tests/api/test_toast_notifications.py tests/api/test_student_portal_ui.py tests/api/test_web_ui_flow_fixes.py tests/api/test_instructor_course_web_flow.py -v, ruff check src tests.
- Final completion report rule: "Đã dùng x skill gồm: ..."

## Current Parent
- Conversation ID: 4946890a-b666-4014-a18b-0a588b75fb4e
- Updated: 2026-09-16T05:29:15Z

## Task Summary
- **What to build**: Core App Shell with Tailwind CDN + Productive Clarity tokens, anti-FOUC script, 74px Topbar, 276px dynamic role-segmented Sidebar, Toast & Modal components, Theme switcher with .dark class, floating AI assistant container, unread notifications helper.
- **Success criteria**: 100% test pass on existing test suites, repo_check.py clean, ruff clean, perfect UI alignment with frontend-preview design system.
- **Interface contracts**: `docs/system/PWD301_SYSTEM_SPECIFICATION/` and `E:\PWD301\.agents\teamwork_preview_explorer_survey5_1\handoff.md`

## Change Tracker
- **Files modified**:
  - `src/pwd301/__init__.py`: Injected `unread_notifications_count` helper in `inject_auth_helpers()`
  - `src/pwd301/static/js/theme.js`: Added `.dark` class toggle to `document.documentElement`
  - `src/pwd301/static/js/components.js`: Aligned modal markup with Tailwind/Productive Clarity tokens
  - `src/pwd301/templates/base.html`: Loaded Google Fonts, Material Symbols, Tailwind CDN & config, anti-FOUC script, live UTC clock, notification badge `#notif-badge`, exact sidebar test labels
- **Build status**: PASS (47/47 tests passed, repo_check passed, ruff passed)
- **Pending issues**: None

## Quality Status
- **Build/test result**: 47/47 pytest passed in 46.92s
- **Lint status**: 0 errors on ruff check src tests
- **Tests added/modified**: Verified against tests/api/test_toast_notifications.py, tests/api/test_student_portal_ui.py, tests/api/test_web_ui_flow_fixes.py, tests/api/test_instructor_course_web_flow.py

## Loaded Skills
- **Source**: superpowers, task-observer, ponytail, full-output-enforcement, impeccable
- **Core methodology**: Strict software engineering & verification, minimal change & no overengineering, exhaustive code generation, design system fidelity.
