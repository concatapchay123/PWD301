# TASK-072 — Admin Access Boundaries, Review Queues, Audit Logs & User Settings

**Status:** DONE
**Assignee:** Codex

## Goal

Resolve the reported Admin and User workflow defects while preserving TASK-071's uncommitted work and the PWD301 security, audit, and headless API invariants.

## Source-of-truth documents

- `AGENTS.md`
- `README.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/CODING_AGENT_START_HERE.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/01_BUSINESS_RULE_CATALOG.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/15_AUDIT_AND_ADMIN_ACTIONS.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md`
- `tasks/CURRENT.md` (TASK-070 behavior and TASK-071 worktree context)
- `tasks/TASK-071.md`
- `docs/database/PWD301_DATABASE_ARCHITECTURE/`

## Preconditions

- Preserve all pre-existing changes in the worktree; do not reset, stash, or overwrite TASK-071.
- Do not create templates, static UI, or a mock frontend.
- Do not add a migration or dependency unless current schema/contracts prove it necessary.
- `ADMIN_PRIMARY` cannot be granted through the normal UI or API. Existing primary administrators remain unchanged.

## In scope

- Restrict the user and role matrix to primary administrators at both route and UI layers.
- Reject attempts to assign `ADMIN_PRIMARY`; preserve primary admin authority for existing accounts.
- Permit an authorized instructor-review admin to approve an application and grant the `INSTRUCTOR` role in that application workflow, with the real reviewing actor retained in append-only audit.
- Scope audit-log list and detail APIs by admin sub-role: primary/system-monitoring can see all logs; course review, instructor review, and teaching assignment admins can see only relevant action categories. Enforce the scope in the service/API, not only in the UI.
- Add functional audit pagination in the admin UI, backed by the existing paginated API.
- Keep review notifications routed to the correct course or instructor approval tab.
- Improve queue width and column sizing; render lesson Markdown as readable, safely sanitized formatted content in the change preview.
- Keep the primary admin landing surface focused on primary-admin work; sub-admin review queues remain on their role-specific tabs and do not inflate primary-only queue summaries.
- Remove the avatar URL editor and keep random avatar generation.
- Add real-time special-character feedback and enforce the same password complexity at the server boundary for password changes.

## Out of scope

- Redesign of unrelated dashboard surfaces or admin roles.
- Changing the canonical three-role database model or stored audit history.
- Password-reset/bootstrap flows unless shared validation requires a narrowly scoped consistent change.

## Reuse / existing-code inspection

- Reuse `User.is_primary_admin`, `User.has_admin_permission`, `query_audit_logs`, existing audit pagination parameters, `UI.renderMarkdown`, current hash routes, and existing role/application services.
- Reuse existing test fixtures and test files; add focused regressions only for uncovered behavior.
- No new abstraction or UI framework.

## Planned changes

- `src/pwd301/blueprints/admin/routes.py`: enforce primary-only user list and forbidden primary-role assignment; expose role-scoped audit query/detail; preserve JSON errors.
- `src/pwd301/services/user_service.py`: narrowly allow the application approval flow to grant `INSTRUCTOR` to a reviewer with `INSTRUCTOR_REVIEW`; reject `ADMIN_PRIMARY` sub-role assignment; enforce special-character complexity for password change.
- `src/pwd301/services/audit_service.py`: apply sub-role action scopes to both list and detail, while preserving current filters and pagination.
- `frontend/assets/js/views/admin.js`: align role matrix, primary queue summaries, queue table, safe Markdown preview, and audit pagination with backend policy.
- `frontend/assets/js/views/student.js`: remove avatar URL entry and add special-character checklist/submit feedback.
- `tests/api/test_admin_subroles_and_enhancements.py`, `tests/api/test_admin_audit_api.py`, `tests/unit/test_audit_service.py`, `tests/unit/test_instructor_application_service.py`, `tests/unit/test_user_service.py`, and `tests/frontend/`: add regression coverage before production edits.
- `tasks/CURRENT.md`: add TASK-072 status and final evidence after implementation.

## Security / authorization impact

- The server denies user-matrix access to every admin except primary admins.
- The server prevents granting `ADMIN_PRIMARY` via normal role assignment and does not rely on hidden controls.
- Application approval is the only non-primary-admin exception that grants the canonical `INSTRUCTOR` role, gated by reviewer permission and attributed to the reviewer.
- Audit list and detail apply the same role-derived scope so changing IDs or pagination cannot expand access.
- Password complexity is checked on the server; client-side checklist is guidance and immediate feedback only.
- Markdown uses the existing sanitizer/renderer; untrusted stored content must not become executable HTML.

## Database / migration impact

No migration planned. Existing role codes and audit schema remain unchanged.

## Concurrency / idempotency impact

Instructor application approval remains within the existing service transaction and rejects non-pending applications. Audit pagination is read-only.

## Acceptance criteria

- Non-primary admin requests to `GET /admin/users` are forbidden; primary admin succeeds.
- Role assignment cannot create a new primary admin through any supported API/UI path; existing primary remains primary.
- An instructor reviewer can approve a pending application; the applicant gains INSTRUCTOR and the actual reviewer is recorded. Reject still works; unauthorized admins remain forbidden.
- Primary and system-monitoring admins can read all audit pages/details. Other sub-admins see only their permitted action categories; they cannot fetch out-of-scope detail by ID.
- Audit UI can advance/back across pages while retaining the selected action filter and accurate page counts.
- Course and instructor notifications open the corresponding review tab.
- Queue columns remain readable at the intended width; edit previews format Markdown safely and clearly.
- Primary-admin summary excludes subordinate review queues while direct role-specific queues still work.
- Settings has no editable avatar URL; generated avatars remain saveable.
- The password checklist and server both reject a password without a special character and accept a valid password under the chosen policy.
- TASK-071 changes remain present and untouched outside necessary integration points.

## Required tests

- Focused API/service tests for role matrix access, primary-role denial, instructor approval, and scoped audit list/detail.
- Focused service/API tests for password complexity.
- Frontend behavior coverage for queue routing, Markdown rendering, audit pagination/filtering, avatar generator, and special-character feedback.
- No skipped test is reported as passing.

## Verification commands

- `python -m pytest tests/api/test_admin_subroles_and_enhancements.py tests/api/test_admin_audit_api.py tests/unit/test_audit_service.py tests/unit/test_instructor_application_service.py tests/unit/test_user_service.py tests/unit/test_authorization_service.py -q`
- `node --test 'tests/frontend/*.test.js'`
- `node --check frontend/assets/js/views/admin.js`, `frontend/assets/js/router.js`, and `frontend/assets/js/views/student.js`
- `python scripts/repo_check.py`
- `git diff --check`
- Browser verification of the affected admin and user flows if a seeded authenticated app is available.

## Deletion and simplification list

| Candidate | Classification | Reason | Action |
|---|---|---|---|
| Avatar URL field and handlers | REMOVE NOW | User requests only generated avatars | Removed URL input and preview typing logic; retained random generation and account-scoped browser persistence |
| Existing audit pagination backend | KEEP | It already returns page metadata | Add UI controls and role scoping without replacing it |
| New Markdown dependency | REMOVE NOW | `UI.renderMarkdown` is already available | Reuse and verify its sanitizer |
| Frontend-only authorization | REMOVE NOW | Client checks are bypassable | Enforce every access boundary in service/API |

## Ponytails / deferred debt

None identified.

## Completion report

### A. Scope and sources consulted

- Completed TASK-072 without staging or committing. Preserved the existing TASK-071 worktree changes.
- Consulted `AGENTS.md`, `README.md`, `tasks/CURRENT.md`, `tasks/TASK-071.md`, `tasks/templates/TASK_TEMPLATE.md`, `docs/system/PWD301_SYSTEM_SPECIFICATION/CODING_AGENT_START_HERE.md`, `docs/system/PWD301_SYSTEM_SPECIFICATION/business/01_BUSINESS_RULE_CATALOG.md`, `docs/system/PWD301_SYSTEM_SPECIFICATION/business/15_AUDIT_AND_ADMIN_ACTIONS.md`, `docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md`, and the canonical `docs/database/PWD301_DATABASE_ARCHITECTURE/` materials.

### B. Reuse decisions

- Reused server-side `User.is_primary_admin`, `User.has_admin_permission`, the existing role/application services, existing audit pagination and serialization, `UI.renderMarkdown`, current hash routing, and the existing Dicebear avatar service.
- No schema, migration, dependency, API response envelope, or frontend framework was added.

### C. Per-file changes

- `src/pwd301/blueprints/admin/routes.py`: limited user list and detail endpoints to the primary administrator.
- `src/pwd301/services/user_service.py`: denied ordinary `ADMIN_PRIMARY` grants, protected the existing primary role from removal or sub-role downgrade, permitted instructor-review admins to grant `INSTRUCTOR` only through application approval with the real reviewer attributed, and aligned special-character validation so whitespace does not count as a special character.
- `src/pwd301/services/audit_service.py`: filtered audit list and detail by admin sub-role; primary and system-monitoring admins retain full access.
- `frontend/assets/js/views/admin.js`: added server-backed audit pagination with retained action filters; scoped visible audit filters; widened and balanced review table columns; rendered lesson Markdown through the existing renderer; removed `ADMIN_PRIMARY` from selectable grant options; restricted queue summaries by role.
- `frontend/assets/js/router.js`: sends course and instructor review notifications to the correct review tab and queue, chooses a role-appropriate default tab, and requests pending counts only for the matching review role.
- `frontend/assets/js/views/student.js`: removed avatar URL editing, kept random generation with per-account browser persistence, and added live special-character feedback and submit validation.
- `tests/api/test_admin_subroles_and_enhancements.py`, `tests/unit/test_audit_service.py`, `tests/unit/test_authorization_service.py`, `tests/unit/test_instructor_application_service.py`, `tests/unit/test_user_service.py`, `tests/frontend/admin_workflow_enhancements.test.js`, and `tests/frontend/student_settings.test.js`: added regression coverage for the reported authorization and UI flows.
- `tasks/CURRENT.md` and `tasks/TASK-072.md`: recorded current scope, final status, and evidence; `docs/superpowers/plans/2026-09-26-admin-user-blockers.md` records the implementation plan.

### D. Deletion/simplification list

- **REMOVE NOW:** avatar URL editing and associated preview handlers.
- **KEEP:** existing audit pagination API and Markdown renderer; only connected them to the UI.
- **REMOVE NOW:** any reliance on frontend-only user-matrix authorization; route checks enforce the boundary server-side.
- No other abstractions, dependencies, or duplicated schema were added.

### E. Ponytails

- None identified.

### F. Verification actually run

- `python -m pytest tests/api/test_admin_subroles_and_enhancements.py tests/api/test_admin_audit_api.py tests/unit/test_audit_service.py tests/unit/test_instructor_application_service.py tests/unit/test_user_service.py tests/unit/test_authorization_service.py -q` — **81 passed**.
- `node --test 'tests/frontend/*.test.js'` — **22 passed, 0 skipped**.
- `node --check` on `admin.js`, `router.js`, and `student.js` — passed.
- `python scripts/repo_check.py` — passed all repository contract checks; it noted the local `.env` is present and should remain ignored.
- `git diff --check` — passed; Git emitted only LF-to-CRLF notices for the three changed JavaScript files.
- Line-level review found and fixed two gaps before completion: an existing primary admin could be reassigned to a subordinate role, and several audit filter options did not match action identifiers emitted by backend services. Both have regression coverage in the passing suites.
- Impeccable `detect --json` reported gray-on-color and palette warnings in unchanged lines outside the edited flows. No authenticated browser/app surface was available (`cua.getState()` returned no browsers or apps), so live-browser verification could not be performed. No SQL Server/migration check was applicable because schema and migration files were unchanged.

### G. Remaining risks / next step

- Random avatar selections persist in local browser storage per account because the current profile API has no avatar field; they do not sync across browsers/devices. Existing server-provided avatars remain displayable.
- No further code step is required for this scope. Keep the worktree uncommitted for the user to review.
