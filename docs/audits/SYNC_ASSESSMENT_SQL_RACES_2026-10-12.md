# Assessment SQL Server synchronization evidence

Verified on 2026-10-12 against the current remediation worktree. These are new verification tests; this task made no production-code changes.

## Isolation and execution

- Dedicated database: `pwd301_test_assessment_sync_20261012`.
- Connection derived privately from `.env`; credentials were not printed.
- `PWD301_TEST_DB_DISPOSABLE=1` and `scripts.test_database_guard.require_disposable_database` validated the target before migrations or fixture cleanup.
- Migrations reached `syncprogress20261011`. Fixture cleanup only targeted this independently provisioned test database.
- Runner: `output/sync-remediation-2026-10-11/run_assessment_sql_races.py`.
- Tests: `tests/integration/test_sqlserver_assessment_sync_concurrency.py`.
- Final log: `output/sync-remediation-2026-10-11/sqlserver-assessment-sync-concurrency.log`.
- Final execution: **6 passed in 25.19 seconds, 0 failed, 0 skipped**. Ruff check and Ruff format check passed for the new test module.

## What the evidence proves

| Finding | Actual scenario | Persisted assertions |
| --- | --- | --- |
| SYNC-058 | One SQL connection selects an MCQ choice; another clears it using an explicit empty array; a third submits. | The junction table is empty, client sequence is 2, and awarded points are zero. |
| SYNC-059 | One session caches an IN_PROGRESS attempt, another commits submission, then the stale session tries to save. | The late save is rejected, no accepted answer event exists, terminal status persists, and the grade remains zero. |
| SYNC-059 | Independent save and submit transactions start through a two-thread barrier, repeated in three separately cleaned fixtures. | Either save wins and the persisted grade is 5 with exactly one accepted event, or submit wins and the grade is zero with no accepted event. The editing lease is revoked in both outcomes. |
| SYNC-079 | An authenticated HTTP authoring request loads the assessment before the first attempt. A SQL scheduling hook pauses it immediately before acquiring its row lock. An independent student transaction commits the first attempt, then authoring resumes. | Authoring returns HTTP 409; the title and both assignments remain unchanged; the student's two question snapshots and the structural-freeze timestamp persist. |

The scheduling hook only controls the execution order before an actual SQL statement. It does not mock persistence, authorization, service results, or assessment state. Concurrent service tests use separate SQLAlchemy Sessions and real SQL Server connections.

## Limits

No RED production defect was observed in these additional tests: they verify the remediation already present. The first five-test run passed in 17.39 seconds; adding the authoring race yielded six passing tests in 21.14 seconds. A final rerun after making fixture imports module-local passed all six in 25.19 seconds.

This evidence covers the listed answer/submission/freeze races. It does not claim browser coverage, arbitrary throughput, all assessment authoring routes, or recovery/deployment readiness. The disposable database was retained for traceability; the live database was not migrated or cleaned.
