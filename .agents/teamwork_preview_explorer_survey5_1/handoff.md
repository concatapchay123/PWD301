# SURVEY REPORT: OBJECTIVE R1 — CORE APP SHELL & DESIGN SYSTEM INTEGRATION

**Agent**: `teamwork_preview_explorer_survey5_1`  
**Parent**: `teamwork_preview_orchestrator_5` (`4946890a-b666-4014-a18b-0a588b75fb4e`)  
**Scope**: Objective R1 (Core App Shell, Tailwind CDN, Design Tokens, Topbar, 276px Sidebar, Toasts, Modals, Script Harmony)  
**Date**: 2026-09-16  

---

## 1. OBSERVATION

### 1.1 Stitch Design System & Preview Assets
- **Design Tokens Source**: `frontend-preview/stitch_pwd301_course_management_platform/stitch_pwd301_course_management_platform/productive_clarity/DESIGN.md` defines the north-star design system *"Productive Clarity"*:
  - **Colors**: Primary Brand `#4F46E5` / `#6366F1`, Canvas `#F8FAFC`, Surface/Card `#FFFFFF`, Border `#E2E8F0`, Text Primary `#0F172A` (Slate-900), Text Secondary `#1E293B` (Slate-800), Text Muted `#64748B` (Slate-500).
  - **Semantics**: Success Emerald `#059669`, Warning Amber `#D97706`, Danger Rose `#E11D48`, Info Sky `#0284C7`.
  - **Typography**: Primary font `Plus Jakarta Sans` for headlines (H1 28px bold, H2 20px semibold, H3 16px semibold), `Inter` for body (14px regular, line-height 1.5), `JetBrains Mono` for codes and counters.
  - **Metrics**: 74px Topbar height, 276px Sidebar width (collapsible to 74px mini-rail), 44px–46px touch/click targets, 10px control radius, 14px–16px card/modal radius.
- **Preview Screens**: 33 HTML screens located in `frontend-preview/` (e.g., `pwd301_student_dashboard_variant_1_action_centric_master_flyout_notification_hub/code.html`, `pwd301_instructor_dashboard_clean_minimalist_focus/code.html`, `pwd301_admin_governance_variant_3_modular_tabbed_command_center_academic/code.html`).
- **CDN Loading in Stitch Previews**:
  - Google Fonts preconnect: `https://fonts.googleapis.com` & `https://fonts.gstatic.com`.
  - Fonts: `Plus Jakarta Sans:wght@400;500;600;700;800`, `Inter:wght@400;500;600;700`, `JetBrains Mono:wght@400;500;600`.
  - Icons: `Material Symbols Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200`.
  - Tailwind CDN: `<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>`.
  - Tailwind Config Script: `<script id="tailwind-config">` setting `darkMode: "class"` and theme extensions.

### 1.2 Existing Flask Layout & Static Assets
- **Layout Template**: `src/pwd301/templates/base.html` (567 lines):
  - Line 5-19: Pre-paint FOUC script reading `pwd301_theme` and `pwd301_sidebar_collapsed` from `localStorage`.
  - Line 28-30: Loads `bootstrap.min.css` and `css/app.css?v=1.3.2`.
  - Line 36-60: `#toast-container` with Jinja `get_flashed_messages(with_categories=true)` loop rendering `.app-toast.toast-{{ t_type }}`.
  - Line 63-258: `.app-topbar` containing mobile toggle, brandmark `P3 PWD301 LMS`, `#sidebar-toggle-btn`, timezone dropdown (`#timezoneDropdownButton`), language dropdown (`#langDropdownButton`), theme toggle (`#theme-toggle-btn`), notification bell (`#topbar-notif-btn`, `#notif-dropdown`), authenticated user menu with role switcher form (`/auth/switch-role`) and logout form (`/auth/logout`).
  - Line 261-425: `.app-body-container` with desktop `.app-sidebar` (276px fixed) segmented by `session.get('active_role')`: `STUDENT`, `INSTRUCTOR`, `ADMIN`, Guest.
  - Line 428-472: `#mobile-offcanvas` drawer for mobile screens (<992px).
  - Line 475-539: `#floating-ai-container` with octopus mascot FAB launcher (`#ai-fab-launcher`), collapsible/expandable chat window (`#ai-chat-window`), quick prompt chips, and message stream.
  - Line 557-563: Script loading order: `bootstrap.bundle.min.js`, `gsap.min.js`, `ScrollTrigger.min.js`, `motion.js`, `theme.js`, `components.js`, `app_shell.js`.
- **CSS System**: `src/pwd301/static/css/app.css` (5,617 lines):
  - Lines 6-133: Defines CSS root variables for light mode (`--topbar-height: 74px;`, `--sidebar-width: 276px;`, `--sidebar-collapsed-width: 74px;`, `--btn-height: 46px;`).
  - Lines 138-203: Dark mode token mappings under `[data-theme="dark"]`.
  - Lines 405-546: TikTok-style collapsed sidebar brand swap animation and hover tooltips.
  - Lines 664-809: Fixed viewport sidebar navigation, `.sidebar-link.active` gradient highlight.
  - Lines 848-950: Collapsed mini-rail mode rules (`.sidebar-collapsed .app-sidebar { width: 74px; }`).
  - Lines 1848-1940: `#toast-container` fixed top-right (24px, 24px, z-index 999999), `.app-toast` styling with colored left accent borders.
- **JavaScript System**:
  - `src/pwd301/static/js/app_shell.js` (486 lines): Controls `initSidebarToggle()`, `syncActiveSidebarLink()`, `initNotificationBell()`, `initAIChat()`, `initTimezoneAutoDetect()`, `switchTimezone(tz)`, `switchLanguage(lang)`, `markAllNotificationsRead(event)`.
  - `src/pwd301/static/js/theme.js` (78 lines): Manages `data-theme` and `data-bs-theme` attributes on `document.documentElement` and listens to `[data-action="toggle-theme"]`.
  - `src/pwd301/static/js/motion.js` (637 lines): GSAP 3 + ScrollTrigger engine. Enforces strict once-per-session page entrance animation (`pwd301_initial_entrance_done` in `sessionStorage`), 3D card tilts, elastic button presses, toast slide-in/out, and AI mascot floating animations.
  - `src/pwd301/static/js/components.js` (718 lines): UI primitives, SVG icons, `showToast(msg, type, duration)`, `openConfirmModal(opts)`, `openSensitiveActionModal(opts)`.

### 1.3 Backend Context & Route Binding
- **Flask Context Processor**: `src/pwd301/__init__.py:537-594` (`inject_auth_helpers()`):
  - Injects `has_role`, `has_any_role`, `is_admin`, `is_instructor`, `is_student`, `can_manage_course`, `user_roles`.
  - Injects i18n & timezone: `_`, `t`, `current_lang` (`get_current_locale()`), `current_timezone` (`get_current_timezone()`), `supported_timezones` (`STANDARD_TIMEZONES`), `format_tz_datetime`.
  - Filter: `tz_datetime`.
- **Role Switching**: `src/pwd301/blueprints/auth/routes.py:207-304`:
  - `POST /auth/switch-role`: Validates allowed transitions (Admin -> ADMIN/INSTRUCTOR/STUDENT; Instructor -> INSTRUCTOR/STUDENT). Sets `session["active_role"] = target_role` and redirects to `admin.dashboard`, `instructor.dashboard`, or `student.dashboard`.
- **Notification Endpoints**:
  - `src/pwd301/blueprints/student/routes.py:554-630`: `GET /student/notifications` (renders `notifications/index.html` or returns JSON with `unread_count`), `POST /student/notifications/<id>/read`, `POST /student/notifications/mark-all-read`.
  - `src/pwd301/blueprints/api_notifications/routes.py:74-81`: `GET /api/notifications/unread-count`.
- **Automated Verification State**:
  - `python scripts/repo_check.py` exited with 0 errors (all repository contracts pass).
  - `python -m pytest tests/api/test_toast_notifications.py tests/api/test_student_portal_ui.py`: 19 passed in 16.76s.
  - `python -m pytest tests/api/test_web_ui_flow_fixes.py`: 21 passed in 23.06s.
  - `python -m pytest tests/api/test_instructor_course_web_flow.py`: 7 passed in 3.80s.
  - Total: 47 passed, 0 failures.

---

## 2. LOGIC CHAIN

### 2.1 Preserving Test Assertions While Modernizing the Shell
From our analysis of existing tests (`test_toast_notifications.py`, `test_student_portal_ui.py`, `test_web_ui_flow_fixes.py`), the test assertions verify exact DOM markers:
1. `test_student_portal_ui.py:52-70`:
   - `assert "app-sidebar" in html`
   - `assert "app-topbar" in html`
   - `assert "sidebar-toggle-btn" in html`
   - `assert "sidebar-collapse-btn" in html`
   - `assert 'title="Tổng quan"' in html`
   - `assert 'data-nav-label="Tổng quan"' in html`
   - `assert 'data-nav-label="Khóa học của tôi"' in html`
   - `assert 'data-nav-label="Bài kiểm tra"' in html`
   - `assert "sidebar-collapsed" in html`
2. `test_web_ui_flow_fixes.py:216-231`:
   - Admin view: `assert "Quản trị & Vận hành" in html`, `assert "Quản lý người dùng" in html`, `assert "QUẢN TRỊ VIÊN" in html`
   - Instructor view: `assert "Giảng dạy" in html`, `assert "Chấm thi tự luận" in html`, `assert "GIẢNG VIÊN" in html`
3. `test_toast_notifications.py:68-123`:
   - `assert 'id="toast-container"' in html`
   - `assert "Flash Messages Container" not in html`
   - `assert "app-toast toast-success" in html`
   - `assert "toast-progress" in html`
   - `assert "toast-close-btn" in html`

**Deduction**: The upgraded `base.html` must co-locate Tailwind classes alongside these semantic selectors and label strings. Rather than discarding existing element structures, we enrich them with Tailwind's utility classes and design tokens (`bg-surface-canvas font-sans text-text-primary`, `w-[276px]`, `h-[74px]`, etc.).

### 2.2 Eliminating FOUC (Flash of Unstyled Content) & Dark Mode Flash
Tailwind CDN runtime compiler injects styles after parsing the script. If theme classes (`dark`) or font declarations are applied asynchronously, visual flickering will occur.
**Solution**:
1. Keep the pre-paint script inside `<head>` prior to stylesheet rendering.
2. Synchronize both data attributes and the `.dark` class:
   ```javascript
   var savedTheme = localStorage.getItem('pwd301_theme');
   var prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
   var theme = savedTheme || (prefersDark ? 'dark' : 'light');
   document.documentElement.setAttribute('data-theme', theme);
   document.documentElement.setAttribute('data-bs-theme', theme);
   if (theme === 'dark') {
     document.documentElement.classList.add('dark');
   } else {
     document.documentElement.classList.remove('dark');
   }
   if (localStorage.getItem('pwd301_sidebar_collapsed') === 'true') {
     document.documentElement.classList.add('sidebar-collapsed');
   }
   ```
3. Load Google Fonts (`Plus Jakarta Sans`, `Inter`, `JetBrains Mono`) with `rel="preconnect"` and `font-display: swap`.
4. Define standard CSS ligature rules for `.material-symbols-outlined` so icon names do not flicker as raw text.

### 2.3 Script Harmony & Event Bridge
- `theme.js`: Update `applyTheme(theme)` to call `document.documentElement.classList.toggle('dark', theme === 'dark')`. This seamlessly drives Tailwind's `dark:` classes everywhere.
- `app_shell.js`: All element IDs (`#sidebar-toggle-btn`, `#sidebar-collapse-btn`, `#topbar-notif-btn`, `#notif-dropdown`, `#ai-fab-launcher`, `#ai-chat-window`, `#ai-floating-input`, `#ai-floating-messages`) are strictly preserved.
- `motion.js`: The GSAP engine checks `hasEntered()` to only animate the initial entrance once per browser session. All subsequent navigations remain fast, crisp, and native.
- `components.js`: Continues to provide `showToast()`, `openConfirmModal()`, and `openSensitiveActionModal()`. Add utility functions for UTC time formatting.

### 2.4 Topbar & Dynamic Sidebar Data Integration
- **Topbar**:
  - Live UTC/NTP clock display (`UTC+7 (Hà Nội)`).
  - Language toggle switches between `VI` and `EN`, preserving current route and session.
  - Notification counter: reads from `unread_notifications_count` injected by context processor, backed by AJAX auto-refresh.
  - Switch Role Dropdown: dynamically populated from `allowed_roles`, submitting to `auth.switch_role` via POST with CSRF protection.
- **Sidebar (276px Width)**:
  - Three role modes (`STUDENT`, `INSTRUCTOR`, `ADMIN`) driven by `session.get('active_role') or current_user.primary_role`.
  - Active state highlighting: Server-rendered active classes based on `request.endpoint` combined with client-side path matching via `app_shell.js`.
  - Smooth collapse to 74px mini-rail with hover tooltips and `Ctrl+B` toggle.
  - Mobile drawer offcanvas for screen widths <992px.

---

## 3. CAVEATS & RISKS

1. **Bootstrap vs Tailwind Utility Collision**:
   - Both Bootstrap and Tailwind define `.d-none` / `.hidden`, `.d-flex` / `.flex`, `.text-muted`, `.badge`, `.btn`.
   - *Risk*: Style conflicts or unexpected specificity overrides.
   - *Remedy*: In `base.html`, load Tailwind CDN after Bootstrap. In `app.css`, maintain component-specific styling (`.app-toast`, `.app-sidebar`, `.app-topbar`). Use Tailwind utility classes primarily for layout, spacing, and modern color tokens (`bg-surface-canvas`, `bg-surface-card`, `border-border-subtle`, `text-primary`).
2. **Material Symbols Text Glitch**:
   - If Google Fonts CDN experiences network latency, icons like `<span class="material-symbols-outlined">dashboard</span>` could briefly display the word "dashboard".
   - *Remedy*: Set `font-display: block` or define CSS ligature defaults with fixed width/height (e.g. `w-5 h-5 inline-flex overflow-hidden`) to avoid layout disruption.
3. **Role Context Desynchronization**:
   - If a multi-role user has `active_role = INSTRUCTOR` in Flask session but directly visits `/admin/dashboard`, the system's `@admin_required` decorator will check whether `actor.is_admin` is true. If true, it automatically permits access or synchronizes the active role.
   - *Remedy*: Maintain `session['active_role']` synchronization in decorators and base context.

---

## 4. CONCRETE IMPLEMENTATION PLAN FOR MILESTONE 1

### Phase 1: Context Processor & Backend Helpers
**Target File**: `src/pwd301/__init__.py`
- In `inject_auth_helpers()`:
  - Add `unread_notifications_count`:
    ```python
    def get_unread_count_safe() -> int:
        if actor and hasattr(actor, "id") and actor.id:
            try:
                from pwd301.services.notification_service import get_unread_count
                return get_unread_count(actor=actor, session=db.session)
            except Exception:
                return 0
        return 0

    ...
    "unread_notifications_count": get_unread_count_safe(),
    ```

### Phase 2: Theme & Component Script Hardening
**Target Files**: `src/pwd301/static/js/theme.js`, `src/pwd301/static/js/components.js`
1. In `theme.js`:
   - In `applyTheme(theme)`: add `document.documentElement.classList.toggle('dark', theme === 'dark');`.
2. In `components.js`:
   - Ensure `showToast()` produces toasts matching the Productive Clarity styling while preserving `.app-toast toast-{{ type }}` and `.toast-progress`.

### Phase 3: Upgrading `src/pwd301/templates/base.html`
- **Head Section**:
  - Add Google Fonts preconnect and links for `Plus Jakarta Sans`, `Inter`, `JetBrains Mono`.
  - Add Google Fonts link for `Material Symbols Outlined`.
  - Add Tailwind CSS CDN script with `plugins=forms,container-queries`.
  - Add `<script id="tailwind-config">` with Productive Clarity color tokens, font families, and border radii.
  - Update pre-paint inline script to toggle `dark` class on `<html>`.
- **Top Toast Container**:
  - Preserve `<div id="toast-container" aria-live="polite" aria-atomic="true">` with the exact flash messages loop and classes expected by `test_toast_notifications.py`.
- **Topbar (`.app-topbar`)**:
  - Restructure with Tailwind classes: `sticky top-0 h-[74px] bg-surface-card/95 backdrop-blur-md border-b border-border-subtle z-40 flex items-center justify-between px-6 shadow-xs`.
  - Include breadcrumbs block, live UTC time indicator, language toggle, timezone selector, notification bell with `#notif-badge`, user avatar profile summary, and switch-role dropdown with CSRF-protected forms.
- **Sidebar (`.app-sidebar`)**:
  - Restructure with Tailwind classes: `fixed left-0 top-[74px] h-[calc(100vh-74px)] w-[276px] bg-surface-card z-30 flex flex-col justify-between border-r border-border-subtle shadow-sm transition-all duration-200`.
  - Implement the 3 role profiles & navigation menus:
    - **Student**: Tổng quan, Khóa học của tôi, Khám phá khóa học, Bài kiểm tra, Trợ lý AI, Thông báo, Đề cử Giảng viên.
    - **Instructor**: Bàn làm việc, Khóa học, Ngân hàng câu hỏi, Lịch dạy & Coi thi, Chấm điểm & SLA.
    - **Admin**: Chỉ Huy Quản Trị (Governance Matrix, Quản lý người dùng, Duyệt khóa học, Duyệt giảng viên), Bảo mật & Kiểm toán (Audit Log, Sao lưu & Phục hồi, Sức khỏe dịch vụ).
  - Preserve all labels (`"Quản trị & Vận hành"`, `"Giảng dạy"`, `"QUẢN TRỊ VIÊN"`, `"GIẢNG VIÊN"`, `data-nav-label="Tổng quan"`, etc.) to maintain 100% test compatibility.
- **Main Workspace (`#main-content`)**:
  - Container with `pl-[276px] min-h-[calc(100vh-74px)] flex-1 bg-surface-canvas flex flex-col`.
- **Floating AI Chatbot**:
  - Preserve `#floating-ai-container`, `#ai-fab-launcher`, `#ai-chat-window`, `#ai-floating-input`, `#ai-floating-messages`.

---

## 5. VERIFICATION PLAN

Execute the following automated verification suite to validate that Milestone 1 introduces 0 regressions:

```bash
# 1. Contract & Repository Integrity
python scripts/repo_check.py

# 2. Toast & Layout Integration Tests
python -m pytest tests/api/test_toast_notifications.py -v

# 3. Student Portal UI & Sidebar Sticky/Collapse Tests
python -m pytest tests/api/test_student_portal_ui.py -v

# 4. Web UI Flows & Role Switching Tests
python -m pytest tests/api/test_web_ui_flow_fixes.py -v

# 5. Instructor Course Web Flow
python -m pytest tests/api/test_instructor_course_web_flow.py -v

# 6. Full Test Suite Verification
python -m pytest tests/ -q
```

**Pass Criteria**:
- 100% pass on all 47+ web UI tests.
- Zero Jinja syntax errors (`UndefinedError`, `BuildError`).
- Zero console errors or layout shifting in browser preview.
