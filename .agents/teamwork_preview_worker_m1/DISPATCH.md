## 2026-09-16T05:23:09Z
You are teamwork_preview_worker_m1.
Your working directory is: E:\PWD301\.agents\teamwork_preview_worker_m1
Your parent is: teamwork_preview_orchestrator_5 (Conversation ID: 4946890a-b666-4014-a18b-0a588b75fb4e).

MANDATORY CONSTRAINTS:
- Read E:\PWD301\.agents\ORIGINAL_REQUEST.md (header ## 2026-09-16T05:16:14Z).
- Read E:\PWD301\.agents\PROJECT.md.
- Read E:\PWD301\.agents\teamwork_preview_explorer_survey5_1\handoff.md for complete design tokens, code snippets, and implementation blueprint.
- Apply mandatory skills: Superpowers (TDD, verification-before-completion), Task Observer, Ponytail, Full Output Enforcement, Impeccable. Remember the completion reporting syntax: "Đã dùng x skill gồm: ...".

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

EXCLUSIVELY OWNED FILES:
You own and may edit the following files:
- src/pwd301/templates/base.html
- src/pwd301/static/js/theme.js
- src/pwd301/static/js/components.js
- src/pwd301/static/css/app.css
- src/pwd301/__init__.py

TASK OBJECTIVE (Milestone 1 — Core App Shell & Design System Integration):
1. In src/pwd301/__init__.py:
   - In `inject_auth_helpers()`, safely provide `unread_notifications_count` by querying notification service safely (fallback to 0 if unauthenticated or error).
2. In src/pwd301/static/js/theme.js:
   - Ensure `applyTheme(theme)` toggles `document.documentElement.classList.toggle('dark', theme === 'dark')` so Tailwind `dark:` variants activate seamlessly alongside data attributes.
3. In src/pwd301/static/js/components.js:
   - Align modal and toast generation with Tailwind/Productive Clarity styling while preserving `.app-toast`, `.toast-progress`, and `.toast-close-btn`.
4. In src/pwd301/templates/base.html:
   - Head: Preconnect Google Fonts, load Plus Jakarta Sans, Inter, JetBrains Mono, and Material Symbols Outlined. Load Tailwind CSS CDN (`<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>`) and inject Tailwind config matching Productive Clarity tokens (colors, font families, dark mode: 'class').
   - Anti-FOUC inline script in head: Read `pwd301_theme` and `prefers-color-scheme`, apply `data-theme`, `data-bs-theme`, and `.dark` class to `<html>` synchronously before body render. Restore `sidebar-collapsed` class if persisted.
   - Toast container: Retain `<div id="toast-container" ...>` with exact flash messages loop and CSS classes expected by tests (`test_toast_notifications.py`).
   - Topbar: Sticky 74px, live UTC clock, language switcher (`/auth/set-language`), timezone selector (`/auth/set-timezone`), notification bell with `#notif-badge`, switch-role dropdown (`/auth/switch-role`) with CSRF tokens.
   - Dynamic 276px Sidebar: Role-segmented menus for Student, Instructor, Admin, and Guest. Preserve exact test strings and markers (`app-sidebar`, `sidebar-toggle-btn`, `sidebar-collapse-btn`, `data-nav-label="Tổng quan"`, `data-nav-label="Khóa học của tôi"`, `data-nav-label="Bài kiểm tra"`, `"Quản trị & Vận hành"`, `"Giảng dạy"`, `"QUẢN TRỊ VIÊN"`, `"GIẢNG VIÊN"`) so existing tests in `test_student_portal_ui.py` and `test_web_ui_flow_fixes.py` pass 100%.
   - Main content area: Layout with appropriate padding (`pl-[276px]` or `pl-[74px]` when collapsed).
   - Floating AI chat window: Retain `#floating-ai-container`, `#ai-fab-launcher`, `#ai-chat-window`, `#ai-floating-input`, `#ai-floating-messages`.
5. Run full verification suite:
   - python scripts/repo_check.py
   - pytest tests/api/test_toast_notifications.py tests/api/test_student_portal_ui.py tests/api/test_web_ui_flow_fixes.py tests/api/test_instructor_course_web_flow.py -v
   - ruff check src tests
6. Document your work and all test results in `E:\PWD301\.agents\teamwork_preview_worker_m1\handoff.md`. Send completion message when done.
