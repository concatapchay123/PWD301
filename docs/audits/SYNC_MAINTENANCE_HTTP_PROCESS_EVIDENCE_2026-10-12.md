# Maintenance admission and independent processes — 2026-10-12

## A. Scope and defect

SYNC-057 durable maintenance state and fail-closed admission. Consulted original audit, existing operations/maintenance lifecycle, request middleware and canonical API error model. Original audit remains unchanged.

The durable reader already returned `(True, None)` on authority-read failure, but middleware only denied traffic when window was non-null. Its own exception branch also set inactive. Two new HTTP tests failed before the product repair (401 instead of maintenance 503), proving service-level fail-closed evidence was insufficient to claim request admission was fixed.

## B. Reuse and C. Per-file changes

- `src/pwd301/__init__.py`: unknown maintenance authority and reader exceptions now return 503 `MAINTENANCE_STATUS_UNAVAILABLE` with Retry-After 60. Reuse existing middleware; confirmed active-window handling and recovery/auth bypasses remain intact.
- `src/pwd301/services/operations_service.py`: correct obsolete cache docstring. Legacy function name/TTL parameter remain compatible; existing implementation reads durable SQL on each call.
- `tests/unit/test_sync_ops_auth_remediation.py`: HTTP admission regression for unknown window and unexpected reader exception; login remains available for recovery.
- `tests/integration/test_sqlserver_maintenance_admission.py`: real loopback HTTP mutation/fault/retry with independent SQL observers; two persistent Python processes observe committed maintenance activation/deactivation without restart or TTL sleep.
- Canonical API error model: document unavailable/active maintenance errors. Ledger, manifest and progress updated with scoped results.

## D. Simplification and E. Deferred scope

No queue, cache layer, dependency, table, migration or duplicate admission abstraction. No new shortcut. Reused existing audited maintenance lifecycle and notification preferences endpoint. Test subprocesses close stdin and terminate after bounded cleanup waits if necessary.

## F. Actually executed gates

- HTTP RED: **2 failed / 16 deselected**, before middleware repair; `maintenance-admission-red.log`.
- Affected SQLite service/HTTP suite: **18 passed in 7.30s**, exit 0; `maintenance-admission-green.log`.
- Guarded SQL integration plus affected service suite: **20 passed in 38.25s**, zero failures/skips, exit 0; `sqlserver-maintenance-sync.log`. Target `pwd301_test_maintenance_sync_20261012`, actual DB_NAME and migration head `syncprogress20261011` verified before destructive fixtures.
- Real HTTP query-fault case uses enabled session CSRF. A targeted SQLAlchemy cursor hook injects failure only for the maintenance SystemAlert read; authentication and preference persistence remain real. PATCH returns 503, independent SQL confirms unchanged preferences. Removing the fault lets the same request persist its intended preference. This is deterministic query-failure injection, not a claim that the SQL service was shut down.
- Two real child processes first read inactive, then both read the same committed active window after the existing service starts it. Their PIDs remain unchanged. Actual non-Admin HTTP mutation is blocked; auth login remains available. After the existing service ends maintenance, both unchanged PIDs read inactive immediately and the mutation resumes. No in-memory-state substitute, worker restart or TTL wait.
- Global Ruff/format **341 Python files**, mypy **96 source files**, compileall, repository and diff checks pass. OCR delegation preview/rules generated; host review checked all unknown/active/inactive admission branches, recovery bypasses, absence of SQL-secret response details and subprocess cleanup.

Counts overlap; SQLite18 and SQL20 are not 38 independent features. The previous full aggregate predates this middleware repair and does not certify final current-source coverage.

## G. Limits

This closes this maintenance admission/cross-process scope. Live restore orchestration, provider availability, sustained traffic under database loss and the final aggregate across all latest source changes remain separate gates. No commit, push, deployment or live database mutation; whole-system goal remains IN_PROGRESS.
