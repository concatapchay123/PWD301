# SQL Server skipped-gate reconciliation - 2026-10-12

The SQLite aggregate completed with 1879 passed and 66 skipped. All 66 skipped cases were collected by exact node ID and rerun on a newly created, guarded SQL Server target. This report preserves the original skipped result; it does not relabel SQLite skips as passes.

## Authoritative result

- Runner: `output/sync-remediation-2026-10-11/run_all_skipped_sql_gates.py`.
- Fresh log: `sql-skipped-gates-current.log`: **66 passed, 0 failed, 0 skipped in 307.83 seconds**, process exit 0.
- Selection and exact passed-node comparison: `sql-skipped-gates-selection.json`, `sql-skipped-gates-reconciliation.json`. Expected and passed sets are identical; missing and extra sets are empty.
- Target: `pwd301_test_complete_sql_gates_20261012`; new database creation refused an existing target. `PWD301_TEST_DB_DISPOSABLE=1`, disposable-prefix guard and independent `SELECT DB_NAME()` checks preceded execution.
- Final fresh SQL inspection: migration head `syncprogress20261011`, 77 business tables. Migration upgrade/downgrade/upgrade ran first against this owned target. No live database was migrated, deleted or restored.

| Test module | Actual passed cases |
| --- | --- |
| `tests/integration/test_sqlserver_migration_roundtrip.py` | 1 |
| `tests/integration/test_approval_sqlserver.py` | 3 |
| `tests/integration/test_playback_sqlserver.py` | 1 |
| `tests/integration/test_sqlserver_assessment_sync_concurrency.py` | 6 |
| `tests/integration/test_sqlserver_authoring_publish_cas.py` | 20 |
| `tests/integration/test_sqlserver_grade_concurrency.py` | 1 |
| `tests/integration/test_sqlserver_ops_ai_sync_concurrency.py` | 5 |
| `tests/integration/test_sqlserver_question_revision.py` | 2 |
| `tests/integration/test_sqlserver_regrade_submission_concurrency.py` | 18 |
| `tests/integration/test_sqlserver_sync_concurrency.py` | 9 |

These cases exercise actual SQL Server DDL, row versions, immutable revisions, approval/playback locks, submission/autosave/publication/legacy freeze interleavings, worker lease fencing, progress dedup, appeal admission, token consumption and regrade lock ordering. The worker test crosses a real scheduling interval and purges more than 100 raw conversations. The generated AI branch retains its explicit provider-response fixture; SQL/clock/worker/provider-independent scope checks are real. This does not prove real Gemini, SMTP, B2, ClamAV, YouTube or sustained deployment load.

The later account-state retry repair adds its own three SQL concurrency cases and is verified separately; those cases did not exist in the aggregate's original 66 skipped selection. Source timing and overlap are disclosed rather than adding unrelated suite counts as independent feature coverage.
