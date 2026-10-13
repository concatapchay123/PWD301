# Concurrent submission and regrade evidence â€” 2026-10-12

Scope: SYNC-063 correction-at-submission, shared grading-marker concurrency, and durable regrade job counters. This adds a real SQL Server gate to the existing savepoint regressions for SYNC-064.

## Isolation and mechanism

The gate used the separate disposable database `pwd301_test_regrade_sync_20261012`, migrated to `syncprogress20261011`. The runner validates the disposable database guard and actual `DB_NAME()` before pytest can invoke cleanup. It reads connection credentials privately from the local environment; no credentials appear in the report or test source. It does not use the live database or another agent's test database.

The tests create published assessments, enrolled students, active attempts and persisted answers through existing services. Independent SQLAlchemy sessions submit or process regrades through the real services. Thread barriers and bounded scheduling events arrange overlapping transactions; grading, histories, commits, correction evaluation and job counters are not mocked.

## Confirmed defect and repair

Before the repair, the corrected simultaneous submission test failed with SQL Server deadlock error `1205` / SQLSTATE `40001`, at the shared `question_revisions.was_used_for_grading` update in objective grading. Each submit transaction had already written its own Attempt, then attempted to upgrade a shared revision read lock. The RED output is retained in `output/sync-remediation-2026-10-11/sqlserver-regrade-submission-red.log`.

Submission now locks applicable QuestionCorrection parents by ascending ID, then source QuestionRevision parents by ascending ID, before writing its Attempt. SQL Server revision reads use `UPDLOCK, HOLDLOCK`; the SQLAlchemy statement also specifies `with_for_update()`. The verified canonical database target is SQL Server. The correction/job creation and worker paths acquire the same correction parent before job or attempt processing. This prevents the demonstrated marker lock upgrade and keeps correction job population and counters serialized across those paths. It does not serialize all submissions through an assessment-wide lock, rewrite snapshots, weaken leases, or split submit/grading into separate transactions.

Expanded testing confirmed two more concurrency failures. Different correction jobs on the same Attempt produced a `PARTIAL` job instead of both completed jobs; evaluator admission now locks and refreshes the common Attempt before reading/updating grades and the shared result. A worker that had already loaded its job deadlocked with retry after retry had flushed job/item resets. Retry now takes the correction and job locks before resetting those rows. Their RED output is retained in `sqlserver-regrade-joint-result-red.log` and `sqlserver-regrade-retry-lock-red.log` in the same output directory.

Separate legal-service regressions also demonstrated that an older ANSWER_ONLY job could restore a superseded answer key, and that an answer correction could remove the full-credit protection owed for an earlier defective presentation. ANSWER_ONLY evaluation now uses the latest QuestionRevision, while an existing `CONTENT_FULL_CREDIT` grade retains its points, rule and revision. Historical snapshots remain unchanged, and completed-job replay does not append duplicate history. The governing rules are `algorithms/11_REGRADING_ALGORITHM.md`, `REGRADE-001` and `REGRADE-002` in the canonical specification.

## Fresh runtime evidence

Final guarded SQL Server selection: **78 passed, 0 failed, 0 skipped, 273.72 seconds**. The runner exited with pytest status 0; output is retained in `output/sync-remediation-2026-10-11/sqlserver-regrade-final-regression.log`.

`tests/integration/test_sqlserver_regrade_submission_concurrency.py` contributes **18 real SQL race cases**, three repetitions of each scenario:

- Two simultaneous ordinary submissions before the original revision has been marked used for grading.
- Two simultaneous submissions after an ANSWER_ONLY correction made while both attempts were open.
- The same two corrected submissions while the real regrade worker processes their shared job concurrently.
- Different question correction jobs processing the same graded Attempt, preserving their combined 20-point result.
- Retry versus a worker that has already loaded the same job, preserving lock order and exactly one changed result.
- Creation of a second correction/current revision while an older snapshot's submit owns its grading/Attempt locks. Both operations complete; subsequently processing the newest job yields the current correct score. This scenario passed with the revision locks already introduced; no speculative Question-parent lock or question-bank mutation was added.

Fresh observer connections verify both submitted results, corrected scores of 10 points, two completed RegradeItems, and final job `total_items = processed_items = changed_results = 2`, status `COMPLETED`. Ordinary submissions retain the original zero score. The joint-result case verifies 20 points after both independent jobs. Retry verifies one completed item and one changed result.

The same final selection includes **4 latest-answer/full-credit policy regressions** in `tests/unit/test_sync_regrade_latest_revision.py` and **56 affected existing submission, traceability, regrade and API tests**. The latest-answer tests use legal services without score mocking, verify immutable original snapshots, and require completed-job replay to preserve history counts. Both correction processing orders are covered for ANSWER_ONLY and CONTENT_OR_CHOICES followed by ANSWER_ONLY.

An earlier affected-test run reported 54 passed and 2 failed. The SQL blueprint predicate was reconciled by the assessment service owner (SQL Server rejects `IS 1`), and the existing valid manual-essay grading fixture now supplies a freshly read ROWVERSION on each write. Optimistic conflict checks remain enforced. The final selection above freshly verifies both corrections.

Ruff check and format passed for the production files and affected test files. Mypy passed for the two production files. OCR delegation rules were retrieved and applied to review locking, authorization, histories, error paths and resource lifetime. These gates establish the tested behavior; they do not constitute a sustained load or deployment-readiness claim.
