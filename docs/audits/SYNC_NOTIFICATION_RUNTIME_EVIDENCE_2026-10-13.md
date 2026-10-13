# Notification async scope and deletion persistence — 2026-10-13

Status: named SYNC-040/041/078 paths verified; whole-system IN_PROGRESS.

## A. Scope and authority

Original synchronization audit's historical notification rollback/read scope and current078 owner isolation. Inspected existing router, API fallback behavior, notification ownership, soft deletion and current browser evidence. Preserve recipient/role authorization, server acknowledgement and safe session cache ownership.

## B. Reuse

Keep existing owner/role/generation fencing, notification API fallback, cache and server deletion service. Use one local predicate for both success and failure of an existing read. No new endpoint, schema, dependency or asset layer.

## C. Per-file changes

- `frontend/assets/js/router.js`: `fetchNotifications` captures its existing identity/role/generation. Both success and catch now require that scope to remain current. Explicit non-null user guard preserves original success semantics even when identity hydration is incomplete. Stale failure cannot set the newer account/read to degraded or render unavailable content.
- `tests/frontend/sync_20261011_state.test.js`: five actual-router regressions cover owner, role, logout, superseding generation and incomplete identity before logout.
- Evidence report, closure ledger, progress and manifest updated. Existing deletion source passed native acceptance without another production mutation change.

## D. Simplification

Share the existing read predicate between success/error branches. Remove the unconditional error-state mutation; no cache rollback or extra notification state added.

## E. Deferred work

No optional debt introduced. Native role-switch read failure is covered by actual-handler regression, while browser scenarios below cover same-owner generation and actual logout/new-owner login. Prior mark-all owner-failure evidence remains separate; these browser checks do not certify every notification producer or SMTP delivery.

## F. Actual verification

RED: old failed reads degraded newer state in actual router tests before repair. The initial role test accidentally reassigned its initial INSTRUCTOR role and was corrected to STUDENT; its earlier failure is not evidence of a role change. Owner/logout/generation were genuine initial failures. A separate incomplete-identity/logout case failed during review before the final null guard was retained.

Native RED: initial aborted auth GET recovered through existing Student/API fallbacks and correctly did not reproduce the error. Final fault setup also fails those old read fallback transports; newer auth GET still returns actual backend200. This reproduced degraded state after a newer successful read (`browser-notification-read-product-red-20261013.log`) before repair. No backend error response is fabricated.

GREEN: **283 full frontend tests pass, zero failed/skipped**, terminal exit0 (`frontend-notification-final-20261013.log`). Existing current-request degraded-state regression also passes, so real current failures are not suppressed.

Final native Edge **five checks pass**, terminal exit0 (`browser-notification-final-20261013.log`, `browser-notification-read-evidence.json`):

1. First GET transport/fallback failure after a newer real GET200 cannot change ready state or RAM cache.
2. Native Student logout and Instructor login without page reload: older failed GET/fallbacks leave new owner's ready state, RAM and sessionStorage unchanged.
3. Real Instructor wrapper DELETE of a Student-owned notification rejects; independent SQL expiration stays null.
4. Native delete with controlled invalid CSRF headers yields actual backend400, including existing ApiClient retry. Row remains available for retry and SQL expiration stays null.
5. Real native DELETE commits SQL while its HTTP200 ACK is held; row/cache remain until ACK. Pre-delete real GET200 arriving after ACK cannot resurrect the item. Authoritative re-fetch and F5 retain deletion.

Guarded disposable DB_NAME, migration head and owned baseline course checked. Unique notices dispatched through existing service to existing owned fixture accounts; no broad fixture reset. SQL read independently verifies actual soft-deletion state. Native transport/CSRF faults are applied only at request boundaries. Final browser log is clean.

OCR delegate preview/rules retrieved for source/test files. Host review covers shared null/owner/role/generation predicate, stale success/error behavior, retained current failure rendering, no new cache mutation, safe async completion, real handler tests and recipient authorization. No unresolved scoped defect found. Repository/diff checks run after report updates; original audit preserved.

## G. Remaining gates

No Python change in this increment. Earlier aggregate/SQL reconciliation still predates the preceding mini-quiz Python repair; this notification increment has fresh frontend/browser evidence. Whole-system runtime/provider gates remain active. No commit, push, deployment, live migration or restore performed.
