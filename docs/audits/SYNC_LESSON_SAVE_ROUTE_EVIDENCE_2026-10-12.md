# Delayed lesson save and selected-route persistence — 2026-10-12

## A. Scope

SYNC-026 captured save title/lesson identity and SYNC-019 preservation of unsaved edits. Source-of-truth: original synchronization audit and existing lesson revision/editor contract, including idempotent route loading and replaceState navigation. This does not close the separate video-delete confirmation/provider boundary.

## B. Reuse and C. Changes

Actual delayed HTTP/SQL checks confirmed the existing captured-save safeguards. They also exposed a route defect: selecting lesson B in the tree changed the editor but left lesson A in the URL. F5 therefore reopened A. A new Node test reproduced A != B before the product repair.

`frontend/assets/js/views/instructor.js`: capture the route's previous lesson identity when selection is admitted. After a successful, generation-checked GET, call the existing `replaceLessonEditorRoute`. That helper uses native replaceState and keeps the existing departure guard aligned. Cancelled, failed and stale selections do not change the last successful URL. No endpoint, backend service, dependency or new route abstraction.

`tests/frontend/sync_course_editor_20261011.test.js`: successful tree selection replaces URL without growing history; dirty cancellation/failure retains prior URL; reversed GET completion cannot replace the newest selected editor/route.

Evidence/ledger/manifest documents updated. Guarded browser runner and private logs stay in the ignored task output directory.

## D. Simplification and E. Deferred scope

Reused the existing route helper rather than adding a hash-triggered render or another history entry. No removed safeguards, speculative abstraction or new shortcut. Video detach/confirmation still has named Node regression coverage but its real browser boundary remains pending.

## F. Actual verification

- Node RED: new selected-route test fails before the repair because URL retains A after selecting B. Current full frontend GREEN: **258 passed, zero failures/skips**, exit 0; `frontend-lesson-selection-final.log`.
- Actual Edge/Flask/SQL runner: **three checks passed**, exit 0; `browser-lesson-save-race-final.log` and `browser-lesson-save-race-evidence.json`.
  1. Real PATCH commits submitted title/content; ACK is held while live inputs are edited again. Releasing ACK leaves SQL/tree at the submitted values and inputs at later unsaved values. Switching lesson prompts; cancellation preserves those edits.
  2. A second real PATCH saves A while ACK is held. User confirms switching to B; releasing A's response cannot overwrite B's editor or SQL. URL names B and native history length is unchanged.
  3. F5 still loads B after the delayed A response. The first save remains independently committed.
- SQL fixture target: `pwd301_test_browser_sync_20261012`; actual DB_NAME, migration head `syncprogress20261011` and owned baseline course identity verified before fixture creation. New uniquely named SYNC-SAVE course uses legal existing services and real session/CSRF requests. No test-wide database cleanup.
- Global Ruff check/format **340 Python files**, mypy **96 source files**, compileall, repository and diff checks pass. OCR delegate preview/rules generated; host review checked generation admission, course/previous-route identity fencing, unchanged dirty cancellation and replaceState history behavior.

The initial actual browser run passed both delayed-save checks but failed F5. This was a real product route defect, not a corrected probe expectation; both browser and Node evidence preceded the fix. No backend production code changed in this follow-up.

## G. Limits

This verifies save/selection/reload behavior, not every video upload/delete race or external media provider. Other audit findings, external gates and the final aggregate across all current repairs remain separately tracked. Original audit preserved; no commit, push, deployment or live database change. Whole-system goal remains IN_PROGRESS.
