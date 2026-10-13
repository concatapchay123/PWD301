# Attempt heartbeat and configurable lease evidence — 2026-10-13

Status: targeted repair verified; whole-system remediation remains IN_PROGRESS.

## A. Scope and authority

SYNC-028 and its historical lease lifecycle. Consulted the current task, existing Attempt admission report, Algorithm 07, non-negotiable invariants, session delivery/renew endpoints and existing lease tests. Algorithm 07 requires a configurable lease independent of the exam deadline. This report supersedes the OPEN_HEARTBEAT conclusion in the preceding UI report; that report remains historical evidence.

## B. Reuse

Reuse the existing authenticated renew endpoint, token header, database conditional update, deadline clamp, retained console root and route departure cleanup. No new dependency, queue, migration, storage or UI asset layer. Renewals serialize; the captured root/account/role fences late callbacks.

## C. Per-file changes

- `frontend/assets/js/api.js`: explicit lease renew POST wrapper.
- `frontend/assets/js/views/student.js`: periodic renewal; disconnect/owner/role/submit/deadline cleanup; transient failures freeze controls while retaining input values and offer retry; terminal authorization/lease failures stop polling. Restored renewal restores the original control states. Manual submit requires verified lease authority.
- `src/pwd301/blueprints/student/routes.py`: deliver a heartbeat interval of one third of the configured lease, capped at ten seconds.
- `src/pwd301/services/attempt_service.py`: initial acquisition, renewal and takeover use the configured lease duration, minimum one second and default sixty seconds, retaining the independent exam deadline clamp. Previously all three used exam duration, leaving the owner lease valid for an entire exam after departure.
- `tests/frontend/attempt_lease_heartbeat.test.js`: serialized renewal, temporary failure/recovery, terminal failure, detached/changed owner/role late ACK and exact endpoint/header regressions.
- `tests/api/test_attempt_lease_api.py`: four session-delivery interval configurations.
- `tests/unit/test_attempt_lease_service.py`: three acquisition/renewal/takeover duration regressions.
- Evidence, closure ledger, manifest and progress updated; original audit unchanged.

## D. Simplification

Removed three exam-duration lease overrides. Existing deadline authority remains; no separate client lease or force takeover mechanism.

## E. Deferred work

No optional debt introduced for this repair. External provider certification and the final current-source aggregate remain separate unfinished gates. Do not sum overlapping selections as unique coverage.

## F. Actual verification

RED before source changes: four Node heartbeat/wrapper failures and four API missing-interval failures. The API probe initially expected 200 for a start endpoint whose canonical status is 201; corrected before obtaining product RED. Actual browser acceptance then failed its prior-expiry assertion because the backend used exam duration. Three independent service duration tests reproduced the defect before repair (approximately 3600 seconds versus configured nine seconds).

GREEN after repair:

- Full frontend: **264 passed, zero failures/skips**, exit 0; `heartbeat-final-frontend-20261013.log`.
- Lease unit/API SQLite: **30 passed**, exit 0, 25.23 seconds; `heartbeat-duration-green-20261013.log`.
- Guarded SQL Server final selection: **46 passed, zero skips**, exit 0, 156.38 seconds; `sqlserver-attempt-heartbeat-duration-20261013.log`. Includes session/JWT HTTP admission/ownership/submit recovery, submission unit tests, lease API and lease unit tests, including all three configured-duration regressions. Earlier SQL31 passed before the duration repair and is superseded by this selection.
- Actual Edge/Flask/SQL: **eight checks**, exit 0; `browser-attempt-heartbeat-green-20261013.log` and `browser-attempt-heartbeat-evidence.json`. Two actual password contexts, CSRF enabled, configured thirty-second lease. Actual wall-clock expiry, native HTTP and independent SQL; no forced expiry timestamps in this browser acceptance.
  1. Second session cannot edit an active owner lease.
  2. Its retry cannot steal that lease.
  3. Held committed answer ACK plus another failed save preserves truthful pending/unsaved status.
  4. Restored save recovers the header and SQL answer.
  5. Periodic renewal keeps the same owner/epoch alive beyond its previous SQL expiry.
  6. Transport loss freezes editing without losing unsaved input; explicit renewal restores controls and subsequent real save succeeds.
  7. SPA departure stops requests and SQL expiry extensions beyond a heartbeat interval.
  8. Actual expiry admits the second session with a new epoch/token on the same Attempt and hydrates its saved answer.
- Ruff checks/format, mypy (96 source files), repository contract and diff whitespace checks pass. Aggregate repository check confirms 77 canonical tables.
- OCR delegate preview/rules generated for this increment. Host review of the seven changed source/test files covers CAS/deadline retention, owner fencing, serial polling, error handling, cleanup, safe constant warning markup and state restoration; no unresolved finding in this increment. This is not a fresh review claim for every earlier scoped file.

SQL gates use verified disposable targets only: `pwd301_test_attempt_admission_sync_20261013` and browser `pwd301_test_browser_sync_20261012`. Actual DB_NAME and migration head `syncprogress20261011` verified before use; browser baseline course ownership verified and new fixtures created through services.

## G. Limits

These checks prove the named local lease lifecycle. They do not certify external providers, every browser environment, suspended/background browser scheduling or deployment. A delayed heartbeat beyond expiry fails closed rather than reviving ownership. No live migration, commit, push or deployment. Whole-system completion is not claimed.
