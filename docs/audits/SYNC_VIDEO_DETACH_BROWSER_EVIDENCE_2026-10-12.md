# Video confirmation, delayed detach and review — 2026-10-12

## A. Scope

Remaining video boundary of SYNC-026 and historical SYNC-015: capture original lesson/file, preserve UI on failure/pending review, apply only the acknowledged owner. Read current detach route/service, canonical draft/published lesson rules and prior per-ID residual. Original audit is unchanged.

## B. Reuse and C. Files

No production source change was required. Existing ownsCard/immutable target guards, shared confirmation cleanup and real detach/review endpoints were exercised. The browser fixture uses legal course/lesson/storage/attachment services and separate Instructor/Admin sessions with CSRF enabled. It creates a unique SYNC-VID course on the already guarded disposable browser database; no test-wide cleanup.

New evidence document; closure ledger, progress and manifest updated. Ignored runner `browser_video_detach_verify.py`, JSON evidence and logs are retained in the task output directory.

## D. Simplification and E. Deferred scope

No abstraction, dependency, code duplication or new shortcut. Reused installed FFmpeg to generate an actual one-second MP4 (1871 bytes), then stored it through the real file service into isolated task storage/quarantine directories. No scan result was manually changed. Existing testing configuration disables ClamAV; fixture CLEAN therefore does not certify a real malware provider or production scanner availability.

## F. Fresh verification

Actual Edge/Flask/independent SQL: **five checks passed**, runner exit 0. Log `browser-video-detach-current.log`; evidence `browser-video-detach-evidence.json`.

1. Open video delete confirmation on A, then navigate to B. The original dialog is cancelled; no DELETE request occurs; both SQL links remain.
2. Confirm A deletion with transport failure. Error notice is present; live video control and SQL resource remain.
3. Real draft DELETE commits A; ACK is held. Navigate to B, then release A response. B video remains in UI and SQL through F5.
4. Published-lesson DELETE returns 202 pending review. SQL resource and video control survive F5.
5. A separately authenticated Admin approves the original request. SQL resource is removed; Instructor F5 agrees.

Target `pwd301_test_browser_sync_20261012`, actual DB_NAME, migration head `syncprogress20261011` and owned baseline identity verified before fixture creation. This is local authorized HTTP backed by real SQL, not a substituted API implementation.

Current full frontend gate: **258 passed, zero failures/skips**, exit 0; `frontend-video-detach-current.log`. This includes the existing wrong-generation confirmation and pending/failure Node cases.

Initial fixture corrections are disclosed: the first error probe assumed a fixed toast phrase instead of the actual request error. Another probe expected immediate DELETE after publishing the course, but the legitimate publish service auto-publishes existing drafts. Creating the two draft fixtures after course publication gives the intended direct-delete case; the published third lesson independently verifies 202/review. Neither mistake is a production RED/GREEN claim. The supplied source already handled all five actual cases.

## G. Limits

This proves video attachment/removal persistence and callback ownership. It does not certify playback/HLS processing, real ClamAV, external storage/YouTube, sustained load or deployment readiness. No commit, push, deployment or live database mutation. Other ledger requirements remain IN_PROGRESS.
