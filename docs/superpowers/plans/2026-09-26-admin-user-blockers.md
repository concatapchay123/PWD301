# TASK-072 Admin and User Blockers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development for independent tasks with review between tasks.

**Goal:** Fix the reported Admin and User access, review, audit, queue, avatar, and password issues while preserving the in-progress TASK-071 changes.

**Architecture:** Keep Flask services and routes authoritative for authorization and state transitions. Reuse the existing JavaScript SPA, Markdown renderer, audit pagination API, and role model. Split work into backend authorization, admin review UI, and user settings UI, each with focused regressions.

**Tech Stack:** Flask, SQLAlchemy, pytest, Vanilla JavaScript SPA, existing frontend test harness.

**Spec:** `tasks/TASK-072.md`

## Global Constraints

- PWD301 remains a headless REST API plus the existing SPA; do not add Jinja templates or preview UI.
- `ADMIN_PRIMARY` cannot be granted through the ordinary role UI/API.
- Authorization is enforced server-side and resource-scoped.
- Important audit events remain append-only and attributed to the actual actor.
- Password policy must be enforced server-side and surfaced in the client checklist.
- Preserve TASK-071 worktree modifications and avoid unrelated refactors/dependencies/migrations.

---

### Task 1: Backend Role Boundaries, Instructor Approval, Password Complexity, and Audit Scoping

**Files:**
- Modify: `src/pwd301/blueprints/admin/routes.py`
- Modify: `src/pwd301/services/user_service.py`
- Modify: `src/pwd301/services/audit_service.py`
- Test: `tests/api/test_admin_subroles_and_enhancements.py`
- Test: `tests/api/test_admin_audit_api.py`
- Test: `tests/unit/test_audit_service.py`
- Test: `tests/unit/test_instructor_application_service.py`
- Test: `tests/unit/test_user_service.py`

**Interfaces:**
- Use `User.has_admin_permission(...)` to define categories.
- Keep existing `query_audit_logs(actor, filters, page, per_page, session)` return shape.
- Add/reuse a single role scope mapping consumed by both audit list and detail paths.

- [ ] Add failing tests for admin-users access, no primary role grant, scoped audit list/detail, instructor-review approval, and password complexity.
- [ ] Run focused tests and confirm each fails because the current behavior violates the acceptance criteria.
- [ ] Implement route/service guards and narrowly permit the application-approved INSTRUCTOR grant for authorized reviewers.
- [ ] Re-run focused tests and inspect the audit actor and status transitions.

### Task 2: Admin Queue, Notification Routing, Markdown Preview, and Audit Pagination

**Files:**
- Modify: `frontend/assets/js/views/admin.js`
- Modify: `frontend/assets/js/router.js` only if notification links fail to preserve tab routing
- Test: existing/new tests under `tests/frontend/`
- Test: `tests/api/test_admin_backend_completion.py` only if route target notifications need correction

**Interfaces:**
- Continue using `ApiClient.getAdminAuditLogs({ page, per_page, ...filters })`.
- Use `UI.renderMarkdown` for the review preview and preserve its HTML sanitization behavior.
- Keep review route hashes `#/admin/governance?tab=courses` and `#/admin/governance?tab=applications`.

- [ ] Add failing frontend coverage for page changes/filter retention, notification tab routing, markdown output, and role-focused primary summaries.
- [ ] Run frontend test cases to confirm the current missing behavior.
- [ ] Add visible previous/next and page count controls; use fixed/minimum column widths and a wider scroll container; render sanitized Markdown.
- [ ] Re-run frontend cases and use a browser view to inspect the updated queue if available.

### Task 3: User Avatar and Password Feedback

**Files:**
- Modify: `frontend/assets/js/views/student.js`
- Test: existing/new tests under `tests/frontend/`

**Interfaces:**
- Preserve profile update endpoint payload shape, supplying only generated avatar URLs from the preset action.
- Match the server special-character rule exactly; do not duplicate a different client-side policy.

- [ ] Add failing frontend coverage for absent avatar URL editor, functional preset generation/save, and special-character checklist/submit feedback.
- [ ] Run frontend tests to confirm current missing behavior.
- [ ] Remove the URL editor and free-text preview handler; add the special-character requirement to the checklist and client submit guard.
- [ ] Re-run frontend cases and inspect profile/password panes in a browser if available.

### Final review and completion

- [ ] Review all changed files against TASK-072, inspect `git diff` without touching unrelated TASK-071 hunks, and run the listed focused checks.
- [ ] Record pass/fail/skip output and unavailable browser/database limits in `tasks/TASK-072.md` and `tasks/CURRENT.md`.
