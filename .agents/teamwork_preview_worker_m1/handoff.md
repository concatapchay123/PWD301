# HANDOFF REPORT: MILESTONE 1 — CORE APP SHELL & DESIGN SYSTEM INTEGRATION

**Agent**: `teamwork_preview_worker_m1`  
**Parent**: `teamwork_preview_orchestrator_5` (`4946890a-b666-4014-a18b-0a588b75fb4e`)  
**Scope**: Milestone 1 (App Shell, Tailwind CDN, Design Tokens, Anti-FOUC, Topbar, 276px Sidebar, Toasts, Modals, Script Harmony)  
**Date**: 2026-09-16  

---

## 1. OBSERVATION

### 1.1 Files Modified
1. `src/pwd301/__init__.py` (Lines 576–598):
   - Injected safe notification counter `unread_notifications_count` inside `inject_auth_helpers()`:
     ```python
     def get_unread_count_safe() -> int:
         if actor is not None and hasattr(actor, "id") and actor.id:
             try:
                 from pwd301.services.notification_service import get_unread_count
                 return get_unread_count(actor=actor, session=db.session)
             except Exception:
                 return 0
         return 0
     ```
2. `src/pwd301/static/js/theme.js` (Lines 19, 67):
   - Added `document.documentElement.classList.toggle('dark', theme === 'dark')` in `applyTheme(theme)`.
   - Added `document.documentElement.classList.toggle('dark', initialTheme === 'dark')` in pre-DOM execution to ensure immediate Tailwind `dark:` variant activation alongside data attributes.
3. `src/pwd301/static/js/components.js` (Lines 570–670):
   - Upgraded `openConfirmModal` and `openSensitiveActionModal` HTML to use Productive Clarity / Tailwind utility classes (`rounded-2xl`, `border border-slate-200 dark:border-slate-800`, `bg-white dark:bg-slate-900`, `shadow-2xl`) while preserving all test-required button classes and IDs.
   - Preserved `app-toast toast-${normalizedType}`, `toast-progress`, and `toast-close-btn` for toast notifications.
4. `src/pwd301/templates/base.html`:
   - Added preconnect links and Google Fonts for `Plus Jakarta Sans`, `Inter`, `JetBrains Mono`, and `Material Symbols Outlined`.
   - Injected Tailwind CSS CDN (`<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>`) and Productive Clarity token configuration (`darkMode: "class"`).
   - Updated pre-paint anti-FOUC inline script to synchronously toggle `document.documentElement.classList.toggle('dark', theme === 'dark')`.
   - Retained `#toast-container` with exact flash loop and classes expected by `test_toast_notifications.py`.
   - Modernized Topbar with live UTC clock (`#topbar-live-clock`, `#topbar-clock-time`) ticking every 1s, `#notif-badge` notification count badge on `#topbar-notif-btn`, timezone switcher (`/auth/set-timezone`), language switcher (`/auth/set-language`), and switch-role dropdown (`/auth/switch-role`) with CSRF tokens.
   - Preserved exact test contract markers and strings in 276px dynamic Sidebar: `app-sidebar`, `sidebar-toggle-btn`, `sidebar-collapse-btn`, `data-nav-label="Tổng quan"`, `data-nav-label="Khóa học của tôi"`, `data-nav-label="Bài kiểm tra"`, `"Quản trị & Vận hành"`, `"Giảng dạy"`, `"QUẢN TRỊ VIÊN"`, `"GIẢNG VIÊN"`.
   - Retained complete floating AI assistant structure: `#floating-ai-container`, `#ai-fab-launcher`, `#ai-chat-window`, `#ai-floating-input`, `#ai-floating-messages`, `#ai-chat-expand-btn`, `#ai-expand-icon`, `#ai-compress-icon`, `data-user-initials`, `data-user-name`.

---

## 2. LOGIC CHAIN

1. **Test Selector & Attribute Conformance**:
   - `tests/api/test_toast_notifications.py` requires `#toast-container`, `app-toast toast-success`, `toast-progress`, and `toast-close-btn`. These elements and class patterns are retained 100%.
   - `tests/api/test_student_portal_ui.py` requires `app-sidebar`, `app-topbar`, `sidebar-toggle-btn`, `sidebar-collapse-btn`, `title="Tổng quan"`, `data-nav-label="Tổng quan"`, `data-nav-label="Khóa học của tôi"`, `data-nav-label="Bài kiểm tra"`, `sidebar-collapsed`, and all AI widget IDs. These elements were kept intact with enhanced styling.
   - `tests/api/test_web_ui_flow_fixes.py` checks for role-specific strings: `"Quản trị & Vận hành"`, `"Quản lý người dùng"`, `"QUẢN TRỊ VIÊN"`, `"Giảng dạy"`, `"Chấm thi tự luận"`, `"GIẢNG VIÊN"`. The desktop and mobile sidebars and user profile dropdowns render these exact tokens.
2. **Eliminating FOUC**:
   - Inline script runs in `<head>` prior to HTML body rendering. Both `data-theme` and the class `dark` are applied synchronously to `<html>`, preventing dark mode flashing when Tailwind CDN styles initialize.
3. **Fail-Closed Security & CSRF Retention**:
   - Role-switching forms in Topbar strictly use `POST` to `{{ url_for('auth.switch_role') }}` with `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`, protecting against CSRF attacks.

---

## 3. CAVEATS

- No caveats. All 47 existing UI flow tests pass with zero regressions.
- No modifications were made outside of exclusively owned files.

---

## 4. CONCLUSION

Milestone 1 (Core App Shell & Design System Integration) is complete. The application shell now loads the Productive Clarity design tokens, Google Fonts, Material Symbols, and Tailwind CDN with zero FOUC, while maintaining 100% backward compatibility and test compliance with the PWD301 test suite.

---

## 5. VERIFICATION METHOD

Independently reproducible commands:

```bash
# 1. Repository integrity check
.venv\Scripts\python.exe scripts/repo_check.py
# Result: [PASS] Repository contract check complete

# 2. Automated test suite for App Shell, Student Portal UI, and Web UI flows
.venv\Scripts\python.exe -m pytest tests/api/test_toast_notifications.py tests/api/test_student_portal_ui.py tests/api/test_web_ui_flow_fixes.py tests/api/test_instructor_course_web_flow.py -v
# Result: 47 passed in 46.92s

# 3. Linter verification
.venv\Scripts\python.exe -m ruff check src tests
# Result: All checks passed!
```
