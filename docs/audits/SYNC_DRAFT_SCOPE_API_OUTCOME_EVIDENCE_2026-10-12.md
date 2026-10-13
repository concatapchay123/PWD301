# Account draft scope and browser HTTP outcomes — 2026-10-12

## A. Scope

Historical SYNC-042 account/role RAM/storage isolation and memory-only password; SYNC-046 rejection of HTML and success:false API responses. These were still marked runtime pending in the per-ID ledger. Consulted original audit, current ExamStore scope/storage code, API request/error contract and actual role/logout workflows.

## B. Reuse and C. Files

No production code change was needed. Existing account-keyed native localStorage, role-aware memory, password serialization/hydration safeguards and ApiClient outcome checks passed actual browser acceptance.

New evidence document; ledger/progress/manifest updated. Ignored runners `browser_draft_scope_verify.py` and `browser_api_outcome_verify.py` reuse the guarded real Flask/SQL server and native Edge session. A second unique Instructor is created through existing registration/role services on the disposable database. No extra abstraction, dependency, migration, endpoint or test-wide cleanup.

## D. Simplification and E. Deferred scope

Reused actual login/role/logout controls, native storage and existing services instead of substituting the app state or ApiClient implementation. No new shortcut or deferred implementation debt. Other audit scope stays separately tracked.

## F. Fresh executed evidence

`browser-draft-scope.log`: **six checks passed**, runner exit 0, same browser context/storage throughout:

1. A scoped draft contains the test password only in memory. Native durable JSON stores an empty password. Actual Instructor settings F5 restores its title with an empty password.
2. Actual Student role switch hides author draft RAM/storage access; A durable author entry remains intact.
3. Actual Instructor role recovery restores A title without its password.
4. Actual acknowledged logout, then second Instructor password login, uses another storage key and inherits neither A nor an unowned legacy global key.
5. B draft survives F5 while A durable entry retains A title.
6. Returning to A through actual logout/password login/settings restores A; B storage remains separate, password remains empty.

`browser-api-outcome.log`: **three checks passed**, runner exit 0:

- Controlled HTTP200 HTML response at the real users refresh fetch is rejected; unavailable/retry appears and no synchronization success toast.
- Controlled HTTP200 `{success:false}` response is likewise rejected.
- Removing the fault restores an actual authenticated SQL-backed GET, and only then synchronization success is acknowledged.

The two malformed HTTP responses are deliberate transport-boundary fault injection through Playwright routing, not a claim that the server generated those responses in normal operation. Native fetch, ApiClient, refresh control and DOM handling remain real. Recovery reads use the unmodified server. The draft's memory-only test value and unowned legacy key are deliberately seeded fixture inputs, not real production secrets.

Target `pwd301_test_browser_sync_20261012`; actual DB_NAME, head `syncprogress20261011` and owned baseline course verified before use. Session authentication and CSRF are enabled. JSON evidence: `browser-draft-scope-evidence.json`, `browser-api-outcome-evidence.json`.

Fresh full frontend: **258 passed, zero failures/skips**, exit 0; `frontend-draft-outcome-current.log`. Repository and diff checks pass. Existing named Node regressions are included in that gate. No product failure or new product RED/GREEN cycle was inferred: these are acceptance checks of existing repairs.

## G. Limits

Browser-local persistence is intentionally account-scoped device storage; this does not claim cross-device draft synchronization. This evidence covers the stated account/role/password and HTTP outcome boundaries, not all parser/network endpoints, provider availability, sustained load or deployment readiness. Original audit preserved; no commit, push, deployment or live database mutation. Whole-system goal remains IN_PROGRESS.
