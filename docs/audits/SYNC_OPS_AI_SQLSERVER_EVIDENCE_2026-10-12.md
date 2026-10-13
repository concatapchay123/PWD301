# Operations and AI synchronization SQL Server evidence

Date: 2026-10-12, Asia/Bangkok. Scope: audit IDs SYNC-056, SYNC-075 and SYNC-077. This document supplements the remediation ledger; it does not declare the full audit complete.

## Environment and result

- New isolated target: `pwd301_test_opsai_sync_20261012`, created from the configured SQL Server host and migrated to `syncprogress20261011`. The runner verifies `SELECT DB_NAME()` before testing; `PWD301_TEST_DB_DISPOSABLE=1` and `require_disposable_database` guard the target. No live database was migrated or cleaned.
- Test artifact: `tests/integration/test_sqlserver_ops_ai_sync_concurrency.py`.
- Runner and log: `output/sync-remediation-2026-10-11/run_ops_ai_sql_races.py` and `sqlserver-ops-ai-sync-concurrency.log`.
- Actual final output: **4 passed, 0 failed, 0 skipped in 7.53 seconds**, `OPS_AI_SQL_RACES_EXIT 0`.
- Ruff lint and format checks both passed for the new test file. No product code changed in this verification task.

## Assertions and practical limits

| ID | Directly exercised behavior | Evidence |
| --- | --- | --- |
| 056 | Administrator retry loads an expired RUNNING candidate, pauses immediately before its actual conditional SQL UPDATE, while a separate SQLAlchemy connection reclaims and commits the job. Retry then executes against the changed database row. | Retry returns ConflictError; authoritative job remains RUNNING with attempt_count 2 and a future lease; no retry audit record is emitted. The synchronization hook pauses execution only, and never changes database values or service outcomes. |
| 077 | Two independent SQL Server sessions preload the same parent and empty message relationship, verify distinct `@@SPID`, synchronize at a barrier, and concurrently call the actual send_chat_message service. Separate cases exercise refusal and the generated-reply branch. | Both commits succeed with pairs (1,2) and (3,4). A fresh SQL query proves four unique ordered USER/ASSISTANT messages and both distinct user bodies retained. For generated replies, actual history construction passes 1 then 3 messages to the provider boundary, proving the second sender sees the first committed pair; both distinct assistant bodies persist. The existing parent lock refreshes stale relationship state before allocation. |
| 075 | Actual bounded worker loop schedules, claims and executes durable retention on an expired ACTIVE conversation containing private raw content. No enqueue, dispatch, worker, retention, or SQL boundary is mocked. | Fresh SQL proves zero raw messages, preserved EXPIRED parent, and the scheduled cleanup job SUCCEEDED with attempt_count 1 and completed_at populated. No pending email or video fixtures were created, so no external email/model/video request was required. |

For 077, only `get_gemini_client` is replaced with a provider fixture whose `chat_response` returns a deterministic body derived from the supplied message history. Known out-of-scope cooking queries use the actual deterministic scope classifier and refusal-message allocation/telemetry/commit branch. Greeting queries use the actual in-scope history construction, provider response handling, telemetry, message allocation and commit branch. This proves SQL parent serialization and sequence allocation for concurrent sends; it **does not prove real Gemini generation or provider integration**, nor the timing of a long generated response. The SQL connection identities and database state are not mocked.

The initial verification run yielded 2 passed and 1 test failure caused by comparing SQL Server's offset-naive DATETIME2 value against an offset-aware UTC test timestamp. Normalizing the assertion to UTC corrected the test; the job claim/retry assertions had already succeeded. No product defect was inferred from that harness failure, and no product repair RED/GREEN claim is made here.

Đã dùng 5 skill gồm: superpowers (verification-before-completion, dispatching-parallel-agents), ponytail, task-observer, full-output-enforcement, open-code-review-delegate.

## Real multi-batch cadence extension

Fresh `sqlserver-ops-ai-worker-batches.log`: **5 passed, 0 failed, 0 skipped in 80.80 seconds**. The added test creates 111 expired raw conversations on the isolated SQL target, runs the actual bounded worker through a real 60-second scheduling period, and verifies two cleanup jobs, zero retained raw messages, and all 111 EXPIRED metadata parents. Actual monotonic clock, sleep, worker claim/dispatch, retention and database were used. No external Gemini or SMTP call was needed.
