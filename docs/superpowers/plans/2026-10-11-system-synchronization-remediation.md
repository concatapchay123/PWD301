# System Synchronization Remediation Implementation Plan

**Goal:** Correct all 40 current findings and unresolved residuals in SYSTEM_DATA_SYNCHRONIZATION_AUDIT_2026-10-11.md without weakening canonical security, history, transaction, or pacing invariants.
**Authorization:** User explicitly requested comprehensive implementation based on the completed audit and its proposed fixes; proceed through implementation and verification, without deployment or publication.
**Architecture:** Reuse existing Flask/SQLAlchemy services, caller-owned transactions, conditional SQL locking/updates, durable existing event/job tables, storage adapter, Vanilla JS reconciliation and owner fences. No replacement frontend, new infrastructure, dependency upgrade, or live-database destructive tests.
**Spec:** Existing System Specification, canonical Database Architecture, audit findings and regression matrix. Source and audit claims are revalidated at current baseline 5f0e3b94109ded28a44ce1b8c8def43be2bc414d.

## Global Constraints

- Preserve immutable attempt/revision/grade/audit history, fail-closed scans, <1GB video, session CSRF and resource authorization.
- SQL Server concurrency verification requires a dedicated pwd301_test_* database and PWD301_TEST_DB_DISPOSABLE=1. SQLite in-memory proves service behavior, not SQL locking.
- New behavior must have a regression observed failing before production edits. Do not suppress/remove tests to get green.
- Do not commit, push, deploy, restore the live DB, alter existing application data, or expose credentials.
- Preserve the audit as historical evidence; maintain a separate per-ID remediation ledger.

## Review Focus

1. Missing/empty/false payload semantics, identity after await, and browser unload uncertainty.
2. Cross-course corrections, active-lease takeover, sequence/submit interleavings and deadline authority.
3. Failure after an inner flush/commit, durable dispatch/outbox and retries without duplicated history.
4. Draft attachment manifests, unrelated proposals, two added lessons and cloud documents after pruning.
5. Expired worker ownership, maintenance DB outages, token single consumption and bounded retention progress.

## Task 1: Assessment integrity and corrections

Own attempt_service.py, assessment_service.py, regrade_worker.py, question_bank_service.py, assessment/attempt API handlers, instructor routes assessment section and focused tests. IDs 058,059,028,060,061,062,063,064 and Quick Add portion004; validate residual027/029/036/037.
- [x] Write behavioral regressions; run and record RED.
- [x] Implement atomic/conditional short transactions, object scope, lease admission, recoverable grading, correction dispatch/effective grading and item savepoints.
- [x] Run focused SQLite/API tests; request migration assistance if required rather than editing shared migration heads.
- [x] Review every related public entry point and exception/retry path.

## Task 2: Course/file/import/progress integrity

Own lesson_service.py, import_service.py, file_service.py, course models and nonassessment instructor/lesson routes and focused tests. IDs 004 import,013,014,033,034,065,068,069,082; collaborate on mixed block manifest018 contract and chapter validation080.
- [x] Reproduce each failure with real service/DB behavior and record RED.
- [x] Keep caller-owned commits, authorize/materialize bytes, preserve draft manifests, serialize generic progress and durable event identity.
- [x] Use existing tables where suitable; new schema only through a root-coordinated new migration and canonical DDL update.
- [x] Run focused tests and check all duplicate approval paths.

## Task 3: Auth/Admin/worker/AI integrity

Own jwt_auth_service.py, auth_token_service.py, session_auth_service.py, user_service.py, audit_service.py, background_job_service.py, operations_service.py, ai_service.py, retention_service.py, auth/admin routes, worker CLI and focused tests. IDs047,054,056,057,066,067,070,071,072,073,074,075,076,077 and restore residual048.
- [x] Write and observe regressions for token consumption, commit failures, job ownership, maintenance failures and retention batches.
- [x] Implement atomic security mutation/outbox, phrase validation, conditional job retry/completion and scheduled bounded cleanup.
- [x] Retain restore fail-closed until actual recovery is established; do not enable destructive live restore.
- [x] Run focused tests and inspect normal and fallback public flows.

## Task 4: Frontend authoritative state

Root owns frontend files, tests/frontend and report/plan integration. IDs017,018,024,026,043,050,078,079,080; residual015,019,029,031,039,040,041,052,055 and backup003 wording.
- [x] Write runtime Node VM/DOM regressions and observe RED before edits.
- [x] Preserve owner/entity/generation across success/failure, pending acknowledgement, block representation, question checkpoints, draft failure UI and degraded reads.
- [x] Reconcile canonical responses; do not use reload as repair or add query library.
- [x] Run all frontend tests and syntax checks; use safe isolated browser/API verification where available.

## Task 5: Integrated verification and adversarial review

- [x] Revalidate every40 finding and all57 old dispositions; classify source fixes separately from fresh verification.
- [x] Run scripts/verify.ps1 on memory SQLite with the existing safety guard; count SQL skips separately.
- [x] Provision a disposable SQL Server target if available; apply new migrations only there and exercise affected concurrency/recovery/API gates.
- [x] Run line-level independent review and address all actionable findings; never use stale OCR preview as a completed review.
- [x] Write A–G completion report with per-ID evidence, per-file changes, reused helpers and unrun/remaining gates.

## Execution Ownership

Three independent backend domains may run concurrently under dispatching-parallel-agents; root implements frontend and coordinates shared files/migrations. Agents must not overwrite each other's sections or format shared instructor/routes.py until all edits are complete. No agent commits. All tests run on isolated targets, never the configured live DB.

## Final local acceptance — 2026-10-13

Completed under the user-directed local-only scope. Full Python1944/100 default skips, actual SQL100/0skip with exact observed node-set reconciliation, latest frontend285 and11 syntax checks pass. Per-ID ledger and A–G final report record all81 IDs, prior RED/GREEN/harness failures, source review and named runtime limits. Source review combines earlier independent domain reviews with final host OCR38/38 review; no new independent-agent or release-pentest claim. SMTP deferred by user; actual providers/deployment/full-server recovery remain outside this local acceptance, and destructive live restore stays disabled. See docs/audits/SYSTEM_SYNC_LOCAL_COMPLETION_2026-10-13.md.
