# Attempt lease UI admission and aggregate autosave — 2026-10-13

## A. Scope and observed product failure

SYNC-028 browser lease admission and historical SYNC-038 truthful aggregate autosave. Canonical Algorithm 07 requires one active editing lease and heartbeat; Algorithm 08 requires ordered saves and truthful outcomes. The current backend denies invalid leases, but actual browser acceptance showed that a separate password session still received editable answer inputs when its GET returned no lease.

The actual two-session browser assertion failed before the product repair. An initial probe setup used an invalid Playwright new_page viewport argument; that setup error was corrected before obtaining the genuine product RED.

## B. Reuse and C. Per-file changes

`frontend/assets/js/views/student.js`: after terminal-result routing, an active Attempt without a lease now renders a noneditable unavailable view with one primary retry action and a secondary assessment-list link. Reuse existing route refresh instead of force takeover or duplicate lease logic. No technical IDs or lease tokens are displayed.

`tests/frontend/attempt_lease_availability.test.js`: no-lease console admission/retry and terminal-result precedence. The no-lease assertion failed before the repair; its minimal VM did not emulate full console formatting, so the real two-session browser RED is the direct integration proof.

Evidence, ledger, progress and manifest updated. Ignored browser runner reuses existing legal course/enrollment/assessment/question services on guarded SQL. No endpoint, dependency, migration, backend source change or new UI asset layer.

## D. Simplification and E. Required work still open

Reused existing backend authority and retry route; do not manufacture a client lease or weaken token validation. No speculative abstraction.

**OPEN: periodic lease heartbeat is still missing from the Attempt frontend.** Existing renew endpoints commit durable extensions, but no periodic call currently keeps a quiet editor alive. This acceptance run does not prove behavior beyond lease expiry. Implement the heartbeat with owner/root fencing, no overlapping renewals, cleanup and truthful failure handling before closing all of SYNC-028. This is required unfinished work, not an optional deferred feature.

## F. Fresh verification

- Actual two-session browser RED: second password session still had `.assessment-short-answer` without a lease; `browser-attempt-tabs-product-red-20261013.log`.
- Current full frontend: **260 passed, zero failures/skips**, exit 0; `frontend-lease-ui-green-20261013.log`.
- Actual Edge/Flask/SQL: **four checks passed**, exit 0; `browser-attempt-tabs-autosave-green-20261013.log`, JSON `browser-attempt-tabs-evidence.json`.
  1. Separate session shows unavailable/retry and no editable answers while owner remains active.
  2. Actual retry GET cannot steal the owner's valid lease and remains noneditable.
  3. One short-answer POST commits but ACK is held; another question's save is transport-aborted. Header remains pending until outstanding saves complete, then reports one unsaved question.
  4. Restored HTTP retry clears failed state; only then the header reports saved. Independent SQL retains the submitted short answer.
- Guarded target `pwd301_test_browser_sync_20261012`; actual DB_NAME, migration head `syncprogress20261011` and baseline fixture ownership verified. Unique assessment fixtures are created through services. CSRF enabled; two isolated browser contexts use actual password sessions. The browser test config uses a 30-second lease, and these checks complete while it is valid.
- Repository/diff checks pass. OCR delegate preview/rules generated; host review checked early terminal handling, unavailable-view admission, one primary action, no answer rendering without a token and reuse of route refresh.

The autosave probe initially held every repeated short-answer ACK, including an extra blur save queued behind the first. Holding only the first while allowing subsequent requests to reach the real server corrected that harness condition. It is not a product RED/GREEN claim. SQL-backed short-answer content, native fetch, queues and DOM outcomes remain real.

## G. Limits

The UI admission failure is repaired and aggregate autosave has actual browser evidence. Heartbeat/idle-owner expiry and eventual lost-owner recovery are not achieved by these checks and remain OPEN. External providers and the final aggregate also remain separate. Original audit preserved; no commit, push, deployment or live database mutation. Whole-system goal remains IN_PROGRESS.
