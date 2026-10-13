# Native physical backup intent and verification — 2026-10-13

Status: named SYNC-003/053/054 acceptance verified; whole-system IN_PROGRESS.

## A. Scope and authority

Original audit requires persistent backup intent, truthful artifact inspection and authoritative verification state after failure/success/refetch/F5. Inspected canonical BackupRun type constraints, manifest/list serialization, actual backup/verification/VERIFYONLY services and native Admin operations. Preserve fail-closed auditing and prohibition of automatic live restore.

## B. Reuse decisions

Keep canonical MANUAL storage type while preserving PRE_MAINTENANCE intent/notes in existing manifest and audit. Existing list API already rehydrates these fields; native card must use the committed trigger. Reuse physical SQL Server backup, cryptographic verification and VERIFYONLY. No new enum, schema, migration, endpoint or dependency.

## C. Per-file changes

- `frontend/assets/js/views/admin.js`: backup card displays escaped `trigger_type`, falling back to canonical `backup_type` or MANUAL. It previously ignored correct list metadata and still displayed MANUAL after F5.
- `tests/frontend/readiness_ui_truthfulness.test.js`: actual card rendering regression supplies persisted PRE_MAINTENANCE plus canonical MANUAL and asserts semantic intent survives list hydration.
- This report, ledger, progress and manifest updated. Ignored fixture/server/native runners and evidence retained. Original audit preserved.

## D. Simplification

Use existing metadata; no second backup kind, mirror schema or UI-only saved value. Escape the displayed trigger. Existing verification finally-refetch and truthful dry-run modal pass without another source repair.

## E. Deferred work

No optional debt introduced. VERIFYONLY remains artifact inspection, not data/schema recovery proof. Live restore remains disabled. Previous isolated physical recovery evidence is separate and not inferred from these checks. No provider/deployment certification.

## F. Actual verification

Docker became available again and its live daemon/container state was inspected. Create one new uniquely named `pwd301_test_backup_ui_20261013_*` database; refuse existing targets; guard disposable flag and actual DB_NAME/head. Use current mounted source in an owned temporary helper with loopback-only port. SQL backup directory is a unique owned subdirectory shared with existing SQL Server. Create only a unique fixture primary administrator with actual password login. No live/source database overwritten. First fixture startup lacked seeded non-STUDENT roles; fixture creation corrected without modifying product code.

RED: actual card renderer test showed MANUAL despite persisted trigger. Native real POST201 then independent SQL/list confirmed the correct manifest/list intent, but card assertion failed (`browser-backup-ui-product-red-20261013.log`). An earlier SQL probe incorrectly assumed a `public_id` column; BackupRun uses the existing deterministic public-ID mapping, so that setup error is not product RED.

GREEN: full frontend **284 passed, zero failed/skipped**, terminal exit0 (`frontend-backup-intent-20261013.log`). Native Edge **four checks passed**, clean terminal exit0 (`browser-backup-ui-verified-20261013.log`, `browser-backup-ui-evidence.json`):

1. Actual native PRE_MAINTENANCE create POST201 writes a nonempty physical SQL Server .bak and SUCCEEDED record. Canonical type remains MANUAL; authoritative list, card and F5 retain PRE_MAINTENANCE and operator notes.
2. Native physical artifact verification POST200 persists verified_at; fresh list/card and F5 show verified SHA metadata.
3. Native dry-run actually executes SQL Server VERIFYONLY. Result is ARTIFACT_VERIFIED with recovery/drill flags false. Modal states isolated restoration was not performed; restore_tested_at stays null and live restore button disabled.
4. Explicit owned missing-artifact fault fixture: real backend rejects verification, persists last_error and no verified_at. Finally-refetch and F5 show an error, not verified success. The missing record is a negative fixture, not a claimed physical backup.

Direct independent artifact/SQL verification also passes (`backup-ui-physical-evidence-20261013.json`): **6,934,528-byte actual .bak**, SHA-256 matches companion manifest, trigger PRE_MAINTENANCE and notes match append-only DATABASE_BACKUP_CREATED audit, canonical MANUAL, verified_at persisted and restore_tested_at null. No service, artifact bytes, successful API response or SQL write mocked.

Earlier extended probe timed out because CSS uppercase changed innerText casing; it was not counted as passing. Another diagnostic print hit Windows cp1252 encoding; final runner reads original text content and succeeds. These harness corrections did not change product verification behavior.

Fresh OCR delegate preview/rules retrieved. Host review covers metadata fallback, safe escaping, committed manifest/list source, no false recovery assertion, real missing-file error/refetch and unchanged API/schema. Repository/diff checks run after documentation; original audit diff empty.

Temporary owned helper stopped after evidence collection; testing databases and artifacts retained for review. Intentional helper termination is separate from successful native/physical check exit codes. No existing SQL/ClamAV/web containers stopped.

## G. Remaining gates

SYNC-048 reason/restore-guard acceptance and scan/provider/runtime gates remain separate. Current Python source still includes the prior mini-quiz repair after the last full aggregate; no new full current-source aggregate claimed here. No commit, push, deployment, live migration or live restore performed.
