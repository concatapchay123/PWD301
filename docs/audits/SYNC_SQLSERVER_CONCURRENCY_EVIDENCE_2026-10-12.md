# Synchronization SQL Server concurrency evidence

Test source: `tests/integration/test_sqlserver_sync_concurrency.py`.

Environment: newly provisioned, separately named SQL Server database
`pwd301_test_sync_concurrency_20261012`, migrated through `syncprogress20261011`.
Every destructive fixture executed with `PWD301_TEST_DB_DISPOSABLE=1` and the
repository disposable-database guard. The configured live database was not used
for test cleanup. Database credentials and connection URLs were not printed.

## Coverage

| Actual operation | Evidence asserted |
| --- | --- |
| Two simultaneous background-job claims | Exactly one owner; persisted attempt count is one |
| Reclaimed job with a detached previous claim | Previous owner cannot renew or complete; replacement remains RUNNING at attempt two |
| Duplicate generic heartbeat on two connections | Five credited seconds and one durable receipt |
| Progress mutation with a stale identity map | Separately committed nine seconds survives a five-second addition |
| Two simultaneous authenticated appeal HTTP requests | One 201, one 409 and one durable appeal audit record |
| JWT refresh CAS on two independent connections | One pair minted, one conflict, four persisted grants total |
| Password-reset token CAS on two independent connections | One winner, one conflict and one consumed token row |
| Retention candidate followed by independent committed renewal | Active conversation and existing message survive cleanup |
| Two simultaneous expired editing-lease takeovers | One winner, one conflict and exactly one epoch increment |

Thread barriers schedule real operations; they do not supply fabricated database
responses. Token tests align connections immediately before their SQL UPDATE so
both have actually read and verified the same persisted token. The retention
test schedules a real candidate SELECT, then renews the parent from an independent
connection using the existing sender row-lock helper before cleanup resumes.

## Red / green evidence

Before the appeal fix, simultaneous requests both returned 201. The same test
passed after serialization on the attempt parent.

Before the retention fix, cleanup deleted the independently renewed conversation's
message and reported one purged conversation. The same test passed after the
conditional parent update and eligibility recheck. RED output is preserved at
`output/sync-remediation-2026-10-11/sqlserver-retention-race-red.log`.

Suite output: `output/sync-remediation-2026-10-11/sqlserver-sync-concurrency.log`.
The final complete nine-case rerun after the latest worker changes passed in
24.14 seconds, with zero failures or skips.

Ruff lint and format checks were executed successfully for this test file.
These nine checks do not prove every finding in the system-wide audit. In
particular, empty-answer clearing, autosave versus submit, assessment-authoring
versus first-attempt creation, and AI retention scheduling need their own evidence.
