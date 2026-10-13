# Attempt lease admission and terminal ownership — 2026-10-13

## A. Scope

SYNC-028 active lease/takeover/submit admission and historical SYNC-036 ownership before terminal response. Consulted original audit, canonical Attempt API 08 and current session/JWT routes and lease/result models. Existing submit fault/retry/legacy repair coverage runs alongside the new cases. Original audit preserved; whole-system goal remains IN_PROGRESS.

## B. Reuse and C. Per-file changes

`tests/integration/test_sqlserver_submit_http_recovery.py`: reuse prepared legal Assessment/Attempt fixtures, actual loopback HTTP, session/password/CSRF login, JWT grants and independent SQL observers. Add four parameterized HTTP cases (two lease chains, two terminal authorization chains). No product source, dependency, endpoint or schema change was necessary.

New evidence document; per-ID ledger, progress and manifest updated. Guarded runner/logs stay in the task's ignored output directory. Test credentials and lease tokens use redacted representations.

## D. Simplification and E. Deferred scope

Reused the existing submission acceptance module instead of another duplicated fixture/service implementation. No deletion, new abstraction or shortcut. Browser UI presentation of multi-tab takeover remains a distinct gate and is not inferred from HTTP success.

## F. Actual gates

Guarded SQL Server selection: **16 passed in 58.50s**, zero failures/skips, runner exit 0. Log `sqlserver-attempt-admission-20261013.log`; target `pwd301_test_attempt_admission_sync_20261013`, actual DB_NAME and head `syncprogress20261011` verified before fixtures. Selection includes eight real HTTP cases and eight submission service cases; overlap with prior submit evidence must not be summed as new features.

New lease HTTP chains both session/CSRF and JWT:

- Second authenticated client sends force:true takeover while the lease is still valid: 409; independent SQL retains original hash/epoch, IN_PROGRESS and no result.
- Submit without a lease returns 409 without making a terminal state/result.
- A controlled server-side expiry fixture changes only lease_expires_at. Actual takeover keeps the same public Attempt identity, rotates token and increments epoch once.
- Old token/epoch autosave returns 409. New token/epoch saves successfully, then submits with one durable result and released lease.

New terminal authorization chains both session/CSRF and JWT:

- Owner submits through real HTTP; fixture contains an essay and reaches PENDING_GRADING.
- A distinct Student, legitimately enrolled in the same Course, cannot GET this terminal Attempt or replay its known submit key: both 403, no questions/result returned.
- Independent SQL retains the same result status/score/update timestamp and unchanged grade-history count.

Initial run: 14 passed/two new-fixture failures because AssessmentResult uses attempt_id as its PK and has no id. Corrected comparison uses its actual key and persisted result fields; no product defect or production RED/GREEN is inferred. Same-course foreign enrollment was added to strengthen object authorization beyond merely checking a role or Course membership.

Global Ruff/format **341 Python files**, mypy **96 sources**, compileall, repository and diff checks pass. OCR delegate preview/rules generated; host review checked real response status, independent SQL observation, identity/token redaction, valid Student role/enrollment and explicit expiry-fixture boundary.

## G. Limits

Controlled lease expiry verifies the server's expiry transition; it is not a claim of waiting through a real wall-clock expiry or proving every browser tab control. Terminal privacy uses a real submitted PENDING_GRADING Attempt; no fabricated grading state is claimed. External providers, browser lease UI and final aggregate across all latest repairs remain separately tracked. No commit, push, deployment or live database mutation.
