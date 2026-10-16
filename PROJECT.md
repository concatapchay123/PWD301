# PWD301 — current workflow authority

SUPERSEDED: the former TASK-091 execution blueprint is replaced by the [approved workflow contract](docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/WORKFLOW_SUPERSESSION.md) and [TASK-095 execution ledger](docs/tasks/TASK-095_WORKFLOW_REPLACEMENT.md). Its implementation steps and historical completion assumptions have been removed; the original remains in Git.

The platform retains its pure headless Flask REST API, existing Vanilla JS SPA, SQL Server, session/JWT separation, fail-closed files, immutable attempt history and existing resource authorization. Business rules belong in the System Specification; the sole editable database architecture remains `docs/database/PWD301_DATABASE_ARCHITECTURE/`. Agent startup follows AGENTS.md and tasks/CURRENT.md.
