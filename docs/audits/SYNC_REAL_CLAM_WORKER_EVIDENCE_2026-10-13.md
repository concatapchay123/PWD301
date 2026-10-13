# Real ClamAV worker ownership and recoverable scan bytes — 2026-10-13

Status: named SYNC-066/067 boundaries verified; whole-system IN_PROGRESS.

## A. Scope and authority

Original audit requires post-commit dispatch, valid current claim and denial of expired/replaced executors. File access must remain fail-closed and retries must retain recoverable source data. Inspected existing durable queue, conditional claim/renewal/domain commit/completion fence, scanner TCP protocol, rescan promotion/dedup/rejection and Student download policy.

## B. Reuse

Keep existing SQL queue, claims, commit fence, ClamAVScanner and file lifecycle. Add one small private atomic-copy operation reused by scan promotion and isolated rejection. Use existing storage reservation, shutil, UUID temporary filenames and atomic replace; no new dependency, queue, schema or migration.

## C. Per-file changes

- `src/pwd301/services/file_service.py`: rescan prepares complete content-addressed bytes through an owned temporary copy and atomic replace, retaining the source until successful domain commit. Deduplicated isolated source removal also waits for commit. Rejection of an isolated source retains that source until commit. Failed/lost-claim commits leave original quarantined bytes available for the rightful retry. Existing immediate removal of an infected shared live blob remains fail-closed; it is not replaced with a copy that would leave other authorized readers accessing infected bytes.
- `tests/unit/test_file_service.py`: three actual-session commit-failure regressions cover promotion to new blob, deduplication and isolated rejection; each asserts SQL rollback, unchanged source bytes and successful subsequent retry/cleanup. Import formatting corrected only in this scoped file.
- Evidence report, closure ledger, progress and change manifest updated. Ignored guarded real-runtime helper/fixtures/logs retained.

## D. Simplification

Remove destructive pre-commit removal of pending scan source in these three paths. Share the complete-copy preparation primitive; do not change queue architecture or manufacture another worker identity. Temporary prepared files are removed on copy failure. Content-addressed output is retained conservatively on DB rollback because another transaction may reference it; the original source is also retained so retry can finish.

## E. Debt and boundaries

No optional infrastructure debt added. Temporary duplication requires actual reserved disk capacity. Existing conservative unreferenced-artifact reconciliation remains necessary; rollback must not blindly delete shared content-addressed output. Retain existing shared-live-infected removal behavior for security. These checks do not certify B2, SMTP, YouTube or all deployment conditions.

## F. Actual verification

Fresh Docker/SQL/ClamAV state inspected. Each runtime run creates a new unique `pwd301_test_scan_worker_20261013_*` database, refuses existing targets, checks actual DB_NAME/head and disposable guard. Current source mounted in an owned --rm helper. Unique storage/quarantine under ignored output; no live records/container services changed. Published Course status is a fixture setup choice, not native publication acceptance.

Initial **five real runtime checks passed**. Extending to actual ownership loss during a scan exposed a defect: SQL rollback succeeded but `os.replace` had already consumed the quarantined source. Genuine held-daemon-response RED then failed source-byte preservation. Three permanent unit regressions independently failed before product repair (`scan-byte-preservation-red-20261013.log`). An initial helper script escaping error was setup evidence, not product RED.

Final runtime **six checks pass**, terminal exit0 (`real-clam-worker-20261013.log`, `real-clam-worker-evidence-20261013.json`):

1. Real ClamAV TCP INSTREAM returns PASS for harmless text and FAIL for standard harmless EICAR antivirus test data; no scanner substitution.
2. Actual refused scanner connection during upload leaves PENDING/QUARANTINED, rejects Student download and commits durable FILE_SCAN retry.
3. Independent SQL worker session attempts claim while a producer's FILE_SCAN row is uncommitted. No claim/scan before explicit commit; QUEUED direct dispatch denied. Commit then makes that exact row claimable. SQL blocking before commit is expected isolation behavior.
4. Actual one-second lease expires; independent claim API reclaims the same job and increments attempt. Old executor denied, replacement ownership preserved; rightful executor performs real scan, commits ACTIVE/SUCCEEDED and Student download bytes match original.
5. Actual uploaded EICAR test data is REJECTED and Student download remains denied.
6. TCP proxy forwards the real command/chunks and holds one genuine clean daemon reply. During that scan, actual lease expires and actual claim API replaces owner. Old domain commit is denied; after repair original quarantine bytes remain exact. Rightful executor retries through the same real daemon and commits ACTIVE/SUCCEEDED.

Proxy supplies no fabricated scanner response. All provider bytes and verdicts are real; the controlled delay only establishes the interleaving. Old-worker ownership-loss exception diagnostics are expected caught denials, not successful old commits or unhandled test failures. No authentication/claim token printed.

Fresh affected SQLite selection **43 passed** in20.00s, zero failed/skipped: file unit module, existing M1 scan/lifecycle stress/recheck modules and quarantine fail-closed security (`scan-byte-security-green-20261013.log`). Fresh guarded SQL file module **12 passed** in26.03s, zero failed/skipped (`sqlserver-scan-byte-preservation-20261013.log`). Counts overlap; no full aggregate implied. Ruff passes; format342files, mypy96source and compileall pass.

Fresh OCR delegate preview/rules retrieved. Host review checks atomic file preparation, source/destination isolation, complete-copy publication, post-commit cleanup, preserved source after fence failure, dedup/shared-output retention, actual storage reservation and unchanged authorization/fail-closed behavior. Original audit/diff/repository checks run after documentation.

Owned helper exits automatically and is absent from running containers. Test databases/artifacts retained for review. Existing SQL/ClamAV/web/worker containers remain running.

## G. Remaining gates

Latest Python repair supersedes the prior aggregate snapshot; a future full current-source aggregate remains required. Live web-process identity/schema, restore guard and B2/provider requirements remain separate. No commit, push, deployment, live migration or live restore performed.
