# CURRENT TASK

## TASK-001 — Project Foundation & Flask Bootstrap

**Status:** READY

### Goal

Turn the documentation-only repository into a minimal runnable/testable Flask project foundation **without implementing major business features yet**.

### Required sources

- `AGENTS.md`
- root `README.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/04_SYSTEM_ARCHITECTURE.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/backend/01_BACKEND_ARCHITECTURE.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/01_PROJECT_STRUCTURE.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/operations/01_DOCKER_AND_ENVIRONMENT.md`
- `docs/database/PWD301_DATABASE_ARCHITECTURE/README.md`

### In scope

- inspect repository and reuse this bootstrap;
- establish Flask application factory / package structure appropriate to the documented architecture;
- configuration loading for development/test/production modes;
- extension initialization shells for SQLAlchemy, Flask-Migrate, Flask-WTF/CSRF and Flask-Login;
- health/root smoke endpoint/page with no protected business data;
- baseline logging/error handling foundation;
- test configuration and at least a Flask app smoke test;
- Dockerfile/docker-compose only if implementation can be validated coherently in this task;
- update setup/verify scripts if actual bootstrap needs it;
- document exact install/run/test commands.

### Out of scope

- full User/Auth workflows;
- JWT implementation details beyond safe extension/interface preparation;
- 71 SQLAlchemy models and migrations (TASK-002);
- Course/Assessment/AI/File feature implementation;
- selecting background queue or vector database technology without need.

### Acceptance criteria

- a fresh developer can create the environment from documented commands;
- application imports/starts successfully in development and test configuration;
- tests execute successfully;
- lint/type checks execute successfully or any justified limitation is documented;
- no business rule is invented or weakened;
- no duplicate database architecture/DDL source is created;
- `scripts/verify.*` passes for the implemented bootstrap.

### Completion

Move a concise result to `DONE.md`; do not automatically start TASK-002.
