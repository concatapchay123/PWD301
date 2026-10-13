# SQL Server physical backup and isolated recovery evidence

Date: 2026-10-12, Asia/Bangkok. Scope: historical SYNC-002/003 recovery gate; preserve SYNC-048 live-restore prohibition.

## Result and boundaries

**PASS: real application backup, SHA-256 manifest, SQL Server CHECKSUM/VERIFYONLY, separately named isolated restore, fresh-connection sentinel recovery, restored schema comparison and integrity/constraint checks.** This is a disposable SQL Server 2022 recovery drill. It does not certify a production backup, external B2 objects, SQL Server instance disaster recovery, or a live restore workflow.

The existing Docker SQL Server container has the backup volume mounted at `/var/opt/mssql/backups`. A temporary helper container loaded the current workspace source and that existing volume; it bypassed the image's production entrypoint. No existing container was restarted or reconfigured. SQL credentials were read privately from container metadata, passed through subprocess environment and omitted from the evidence. The workstation `.env` uses a different Windows integrated-authentication connection; the drill deliberately targets the Docker SQL Server instance and does not claim to validate `.env` production authentication.

## Actual operations

1. Checked `DB_ID` for both `pwd301_test_recovery_sync_20261012` and `pwd301_test_restored_sync_20261012`; refused existing targets. Created only the first database. Applied all Alembic migrations through `syncprogress20261011`; inspected 77 business tables plus `alembic_version`.
2. Persisted a deterministic test administrator/sentinel and ADMIN relationship in this new database. Loaded the existing `create_database_backup` service with a dedicated new backup directory. The service executed `BACKUP DATABASE ... WITH COPY_ONLY, CHECKSUM, INIT`, produced a nonempty `.bak` and SHA-256 manifest, and persisted/audited its successful BackupRun.
3. Called the existing `execute_dry_run_restore`. Its actual result passed artifact/hash/VERIFYONLY inspection and truthfully reported `data_recovery_verified=false`, `restore_drill_performed=false`. Its audit events were persisted.
4. Inspected `RESTORE FILELISTONLY`, rechecked that the destination did not exist, and executed an explicit `RESTORE DATABASE` to the separately named target with `CHECKSUM`, `RECOVERY` and `WITH MOVE` for every logical file. There was **no `REPLACE`**, no live restore and no SQL Server restart.
5. Opened fresh source/target connections, checked their database names and migration head, and compared sentinel UUID/email/display-name hashes. Compared all 78 table names, column types/nullability, primary keys, foreign keys and SQL check definitions/trust/disabled flags. Ran `DBCC CHECKDB ... WITH NO_INFOMSGS, ALL_ERRORMSGS, TABLERESULTS` and `DBCC CHECKCONSTRAINTS WITH ALL_CONSTRAINTS` on the restored target with no errors. Reran engine `RESTORE VERIFYONLY ... WITH CHECKSUM` against the real artifact.

## Recorded artifact and evidence

| Evidence | Actual value |
|---|---|
| Artifact | `/var/opt/mssql/backups/sync_recovery_20261012/pwd301_db_20261011_173504_f98828bb.bak` |
| Bytes | 5,623,808 |
| Artifact SHA-256 | `ca5c038ae9ee6a0c56c7b6e6d179c10f2f5afc57982298430ea310cfc775bc1e` |
| Sentinel SHA-256, equal in source and restored target | `58ab6b6de1a44c96a10c49eb5fc1339ec5d584df7659b77b74d5e483d8772740` |
| Schema SHA-256, equal in source and restored target | `0b7e699180650b81b3242bede9a7aa63ada01fdd581015b340c2a58dc749bf1a` |
| Migration | `syncprogress20261011` |
| Business tables | 77 |
| Final read-only evidence command | `.venv\Scripts\python.exe output/sync-remediation-2026-10-11/run_recovery_gate.py --finish` |
| Final output | `RECOVERY_GATE_EXIT 0`; all JSON evidence flags true, `live_database_modified=false` |

Ignored runtime evidence: `output/sync-remediation-2026-10-11/recovery-evidence.json`, `recovery-finish.log`, and the three recovery helper scripts. The initial orchestration encountered image-entrypoint waiting, then integrated-authentication mismatch; neither reached an existing database mutation. The first complete recovery executed successfully but its report attempted to fetch rows from successful DBCC output and raised `ResourceClosedError`. The finish command performs only inspection, never repeats restore. Reporting was corrected to handle empty DBCC results, SQL check definitions were read through SQL Server catalogs, and fresh final inspection passed. These failed evidence commands are disclosed rather than counted as passes.

## Completion contract A–G

A. Sources: current operations service, configuration, identity/operations models, canonical audit recovery acceptance criteria and AGENTS.md. No production code or configuration was edited by this gate.

B. Reuse: application physical backup/manifest/audit and artifact-inspection helpers; existing SQL Server and its backup volume. The manual isolated restore is deliberately separate from the application live-restore API.

C. Changes: this evidence document; three ignored orchestration/inspection scripts and logs. The source/target disposable databases and backup artifact are retained for review; no existing database was overwritten or deleted.

D. Simplification: no dependencies, infrastructure services or production endpoints added.

E. Deferred debt: production deployment/backup-path alignment and recovery involving external file/object storage remain separate operational gates. Owner: project maintainer; trigger/review: before release; risk: an instance or file-storage outage is broader than this database-only drill; safeguard: explicit scope labels and live restore remains fail-closed.

F. Verification: final actual command above, real 5.6 MB artifact, checksum, fresh target data/schema and DBCC checks. No mocked service call or skipped test is presented as recovery evidence.

G. Limit: this drill proves the named isolated recovery case. It must not be described as a production data restore, complete server disaster recovery, or approval to restore over a live database.

Đã dùng 5 skill gồm: superpowers (verification-before-completion), ponytail, task-observer, full-output-enforcement, open-code-review-delegate.
