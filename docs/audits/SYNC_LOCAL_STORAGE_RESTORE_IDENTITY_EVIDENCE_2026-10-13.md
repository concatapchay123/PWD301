# Local storage, restore guards and web database identity — 2026-10-13

Status: named local acceptance passed for SYNC-001, SYNC-048 safeguards and SYNC-065 transport contract. Final aggregate is running separately. Actual B2 delivery and destructive live restoration are not certified.

## A. Scope and authority

Original synchronization audit, canonical database architecture, existing storage adapter and import authorization, session/JWT administrative mirrors and repository operating contract. The user explicitly directed: skip email testing until server configuration and run locally now. SMTP configuration and delivery are therefore deferred by request, not failed acceptance gates. No email was sent, no pending delivery was processed and no provider settings were changed.

## B. Reuse

Reuse current Gunicorn health endpoint and SQL session catalogs for read-only identity, existing boto3 S3 adapter for local HTTP, existing import parser and authorization, and both public restore routes. Local storage HTTP fixture uses the standard library; no installed dependency, production object service or infrastructure was added.

## C. Changes and observations

- `tests/unit/test_sync_course_remediation.py`: three actual boto3 HTTP cases against an explicitly simulated loopback S3 endpoint, with signed HEAD/GET, pruned local source, complete download and DOCX parsing, same-size corrupt content, and HTTP503. Unauthenticated access produces zero object requests. Failure leaves a durable FAILED job, no parsed questions, no usable cache and no partial download. This endpoint does not validate credentials or represent Backblaze infrastructure.
- `tests/api/test_operations_api.py`: six session/JWT cases reject missing/empty/short restore reasons with HTTP400. An immediate valid-reason retry reaches the deliberate HTTP403 live-restore guard, with no leaked lock and no DATABASE_RESTORE_COMPLETED event. No backup fixture or restore command is executed by these tests. This extends coverage of an existing repair; no new product change or new failing-product regression is claimed.
- Read-only live web probe matched actual Gunicorn workers 339/340 to SQL sessions using database PWD301. Migration head is `syncprogress20261011`, with 77 business tables and durable progress receipts. Required prerequisite columns and expanded revision CHECK are present. Four probed application source hashes match the current checkout. This establishes current identity; it does not claim that this work applied the live migration.

## D. Simplification

No new endpoint, schema, application abstraction or package. The original audit is preserved. Failed attempts to obtain MinIO images from Docker Hub and Quay were registry access failures; neither created a container or produced provider acceptance. Local HTTP coverage is labeled as a protocol fixture.

## E. Deferred gates

SMTP: explicitly deferred until deployment configuration. Existing UnconfiguredMailClient and 14 pending deliveries are retained. Deep health returns503 because mail_queue is DEGRADED, while database/storage/ClamAV/web/workers report healthy. Cloud storage is disabled; a healthy local storage check must not be read as B2 readiness. Actual B2 account/credentials/object delivery remains a server/provider gate. Owner: project maintainer; review: before release. Live restore remains unavailable, consistent with fail-closed safeguards; the separate isolated physical recovery drill is documented in SYNC_SQLSERVER_RECOVERY_EVIDENCE_2026-10-12.md.

## F. Actual verification

- Focused SQLite: restore6 passed, local S3 HTTP3 passed, zero skips. Initial restore coverage import used the wrong model module and failed during setup; corrected to notification_audit. This was a harness error, not product RED.
- Fresh disposable SQL target `pwd301_test_local_final_contract_20261013`: identity/head checked before fixtures, explicit disposable guard, all migrations applied to that target; nine selected tests passed, zero failures/skips in28.41s, runner exit0. Log: `output/sync-remediation-2026-10-11/sqlserver-local-final-contract-20261013.log`.
- Read-only evidence: `live-web-db-identity-20261013.json`, `live-web-public-health-20261013.json`, `live-web-schema-provider-state-20261013.json` under the same ignored evidence directory. No live writes, schema change or container restart.
- Fresh Ruff and format checks passed for both test files. OCR delegate preview/rules retrieved; host review checked local-only transport, authorization before bytes, rejected cache cleanup, lock release and retained restore guard.

## G. Limits

The S3 endpoint is simulated although actual boto3 networking and application services execute. Existing file fixture scan verdicts are test fixtures; real scanner/worker evidence is separate. Flask test-client HTTP does not prove native restore-modal entry; the live-restore button remains disabled. No SMTP, B2, Gemini or server deployment claim follows from these checks.

Đã dùng 5 skill gồm: superpowers (verification-before-completion), ponytail, task-observer, full-output-enforcement, open-code-review-delegate.
