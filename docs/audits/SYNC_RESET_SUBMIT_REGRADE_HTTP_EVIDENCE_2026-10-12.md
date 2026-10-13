# Reset, submit and regrade HTTP/SQL evidence — 2026-10-12

Scope: SYNC-060, 061, 062, 072 and 073. These new gates verify existing remediation through actual loopback HTTP and independent SQL observers. No production source change was required in this follow-up; corrected fixture errors are disclosed below rather than called production RED/GREEN.

Source contracts consulted: canonical Auth API 03, Assessment API 07, Attempt API 08, Notification API 11, business Audit/Admin policy 15 and Algorithm 11 regrading. Reused existing service fixtures, stdlib HTTP transport and server fixture. Added no dependency, schema, infrastructure or duplicate business service.

## Password reset

`tests/integration/test_sqlserver_password_reset_atomic.py` and the affected auth/ops modules: **48 passed, zero failures/skips in 95.86 seconds**, runner exit 0. Target `pwd301_test_password_reset_sync_20261012` was guarded and independently verified at migration head `syncprogress20261011` before fixture cleanup. Evidence log: `sqlserver-password-reset-sync.log` in the task output directory.

The actual reset POST uses enabled CSRF. Missing CSRF leaves the token unused and password unchanged. Injected mandatory notification failure returns 400 and independently observed SQL retains the original password hash/auth_version, unconsumed reset token, active session/JWT grants and zero password-change events/email deliveries. The old JWT still authenticates.

Retry commits the new password, consumes the same token, increments auth_version once, revokes prior sessions/JWTs and persists exactly one security event and email delivery. Old JWT/session and old password are rejected; fresh password authentication succeeds for REST and session clients. Repeating the consumed reset leaves auth_version and outbox counts unchanged. This proves durable outbox persistence, not SMTP transport.

The first run had 47 passed and one new-fixture failure: a fresh client reused another client's cached CSRF under pytest's shared app context, so it had no session cookie. An isolated app context for that client's GET corrected the harness. No product reset defect was inferred from this failure. Generated test credentials stay private; raw reset access logging is disabled and test secret representations are redacted.

## Submission and terminal recovery

`tests/integration/test_sqlserver_submit_http_recovery.py` plus existing submission tests: **12 passed in 41.72 seconds**, no failures/skips, runner exit 0. A subsequent focused run after adding explicit ACK-status/replay assertions: **4 passed, 8 deselected in 20.93 seconds**, exit 0. Deselected cases are not additional passes. Target `pwd301_test_submit_http_sync_20261012`, verified migration head `syncprogress20261011`; logs `sqlserver-submit-http-sync.log` and `sqlserver-submit-ack-current.log`.

Both session/CSRF and JWT clients save the objective answer through real HTTP, then exercise two cases:

- A grading fault returns 400. Independent SQL confirms IN_PROGRESS, no submission key/result/grades, and retained editing lease. Removing the fault and retrying creates the durable result and releases the lease.
- An explicitly seeded pre-fix crash state contains SUBMITTED with the matching submission key and no result/lease. Matching HTTP replay repairs the result and grades. Repeating the same key preserves exactly one result and stable grade/history counts; a different key returns 409.

The fixture contains an essay, so truthful ACK and SQL state are PENDING_GRADING after objective grading. The test asserts that state rather than erasing manual grading. Initial fixture failures used the wrong points field and assumed GRADED; both were corrected against the model/fixture before claiming a gate. No product RED phase is claimed for these expectation errors.

## Regrade authorization and durable dispatch

`tests/integration/test_sqlserver_regrade_http_dispatch.py` plus the complete regrade service file: **14 passed, zero failures/skips in 63.00 seconds**, runner exit 0. Target `pwd301_test_regrade_http_sync_20261012`, verified migration head `syncprogress20261011`. Log: `sqlserver-regrade-http-dispatch.log`.

Legal correction services produce exactly one queued REGRADE dispatcher job. Real session/CSRF and JWT requests targeting another Course's owned Assessment return 403; fresh SQL confirms unchanged result/history and the legitimate dispatcher still queued. The real claim/executor path processes the dispatcher: BackgroundJob SUCCEEDED, RegradeJob/Item COMPLETED, counters 1/1/1, corrected score 10 and one appended grade-history record. Re-execution is fenced; authorized HTTP replay preserves one dispatcher and unchanged score/history.

The initial test confused BackgroundJob SUCCEEDED with the RegradeJob COMPLETED enum. This was a fixture assertion error, corrected from the canonical states; it was not a dispatcher production defect. This evidence supplements the separately verified 18 SQL regrade race cases and 78-test regrade selection, without summing overlap as distinct feature coverage.

## Limits and per-file result

Changed files are the three new SQL integration test modules plus evidence/ledger/manifest documents. Existing source and original audit are preserved in this follow-up. No deletion or speculative abstraction. Global Ruff/format **340 Python files** and mypy **96 sources** passed. These HTTP/SQL gates do not prove every browser confirmation flow, SMTP delivery, real cloud/malware/video providers, sustained load or deployment readiness. No commit, push, deployment or live database mutation.
