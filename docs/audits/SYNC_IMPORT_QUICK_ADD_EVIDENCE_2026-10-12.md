# SYNC-004 import and Quick Add evidence — 2026-10-12

Scope: atomic commit, truthful acknowledgement, failure rollback and retry for the import commit endpoints and direct assessment Quick Add. Original audit is preserved. This report does not certify document parsing or external cloud/scanner providers.

## Import commit

`tests/integration/test_sqlserver_import_atomic_retry.py`: **3 passed, no skips in 9.14 seconds** on guarded `pwd301_test_import_retry_20261012`, migration head `syncprogress20261011`. Evidence: `output/sync-remediation-2026-10-11/sqlserver-import-atomic-retry.log` and its runner terminal exit 0.

Both JWT `/api/imports/{id}/commit` and session `/instructor/imports/{id}/commit` were exercised through real loopback HTTP. A foreign manager receives 403. An invalid second reviewed question returns 400; independent SQL observes no earlier canonical question, revision, provenance or assignment. Correcting the question through PATCH and retrying commits exactly two questions and assignments. Repeating the completed commit returns the documented 409; fresh GET reports COMPLETED and independent SQL retains the same identities. Two cached SQL sessions with distinct `@@SPID` race the same REVIEW_REQUIRED job: one completes, one conflicts, no duplicate promotion.

This is new coverage of the already repaired transaction; its first production run was green. No new import source change or fabricated RED phase is claimed. Reviewed ImportQuestion fixtures and test authentication were used; these cases do not establish parser UI, CSRF or external malware-scanner behavior.

## Quick Add runtime repairs

New API RED reproduced duplicate creation on retry and reuse of one request identity in another assessment. The create route now reuses the existing assessment parent lock, public question UUID strategy, serializers and canonical transaction. Initial creation returns 201; matching saved semantics in the same assessment returns 200 without mutation. Changed intent or another assessment returns 409. Matching acknowledgement replay remains readable after structural freeze; new creation remains forbidden. Question/revision/provenance/assignment failures roll back together.

Actual Edge RED also found native form validation rejecting the default 1.0 points because the step base was 0.1 with a 0.25 increment. `step=any` retains the existing minimum and permits the default. The form retains one `client_question_id` until acknowledgement and blocks concurrent clicks. A dropped response after real server commit then exposed the old duplicate creation. After repair, `browser_quick_add_verify.py` passes **3 actual checks**: lost ACK/retry returns 200 with one SQL assignment; F5 reads one question; separate password login reads the same question. JSON/log evidence is under the task output directory.

Permanent API regressions cover essay, accepted-answer normalization/dedup, single/multiple choices, changed intent, cross-assessment reuse, frozen acknowledgement versus new creation, and injected assignment failure. Two permanent Node callback regressions cover stable retry identity and admission of one pending request. Current full frontend: **251 passed, zero failures/skips**.

## Precision and validation follow-up

Actual SQL RED: **2 failed, 32 passed in 123.47 seconds**. SQL DECIMAL(9,4) rounds points such as 1.234567 and 1.23445, while the first replay comparison used the unrounded float. Replay now compares the persisted decimal with the incoming value quantized to SQL precision using half-up rounding. API RED additionally reproduced zero becoming the default 1.0 and non-finite values failing outside validation. Explicit zero, negatives, NaN and Infinity now return 400 without canonical writes. Fresh SQLite Quick Add selection: **10 passed in 10.81 seconds**.

Final actual SQL gate: **38 passed, zero failures/skips in 138.66 seconds**, runner exit 0, guarded `pwd301_test_quick_add_retry_20261012`, migrated head `syncprogress20261011`. Five dedicated SQL cases cover frozen new creation, fault injection immediately before real assignment with complete rollback, two precision values, and concurrent same-key HTTP requests from distinct SQL sessions (201 + 200, one question/assignment). The full 33-case affected Instructor API module also passed in that run. The injected freeze is explicitly a rollback fault fixture; actual first-attempt admission races are evidenced in the separate assessment race suite. Fresh global Ruff/format 336 files and mypy 96 sources passed after an explicit None narrowing guard; that guard preserves the route's existing 400 outcome for invalid point input.

Per-file changes: instructor/routes.py, instructor-exams.js, test_instructor_backend_remediation.py, new SQL import/Quick Add files, quick_add_retry.test.js and canonical assessment API. No new schema, dependency, infrastructure or duplicate service. No deletion or speculative abstraction. No live database migration, commit, push or deployment.
