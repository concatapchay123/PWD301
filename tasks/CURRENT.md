# CURRENT TASK

## TASK-001 — Project Foundation & Flask Bootstrap

**Status:** DONE

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
- `docs/system/PWD301_SYSTEM_SPECIFICATION/api/14_ERROR_MODEL.md`

### In scope

- inspect repository and reuse this bootstrap;
- establish Flask application factory / package structure appropriate to the documented architecture;
- configuration loading for development/test/production modes;
- extension initialization shells for SQLAlchemy, Flask-Migrate, Flask-WTF/CSRF and Flask-Login;
- health/root smoke endpoint/page with no protected business data;
- baseline logging/error handling foundation;
- test configuration and at least a Flask app smoke test;
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
- lint/type checks execute successfully;
- no business rule is invented or weakened;
- no duplicate database architecture/DDL source is created;
- `scripts/verify.*` passes for the implemented bootstrap.

---

## Completion Report

### A. Scope and sources consulted
- Operating contract: `AGENTS.md`
- System specification: `docs/system/PWD301_SYSTEM_SPECIFICATION/` (04_SYSTEM_ARCHITECTURE, 01_BACKEND_ARCHITECTURE, 01_PROJECT_STRUCTURE, 01_AUTHENTICATION_ARCHITECTURE, 14_ERROR_MODEL)
- Database architecture: `docs/database/PWD301_DATABASE_ARCHITECTURE/` (README.md, sql/*.sql)
- Invariants & business rules: `01_BUSINESS_RULE_CATALOG.md`, `06_NON_NEGOTIABLE_INVARIANTS.md`
- Configuration & templates: `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, `.env.example`

### B. Reuse decisions
- Reused `pyproject.toml` configurations for Ruff, Pytest, Coverage, and Mypy; added `pythonpath = ["src"]` and type stubs override for untyped Flask extension packages.
- Reused `requirements.txt` and `requirements-dev.txt` without injecting premature external queue/vector DB dependencies.
- Reused existing `scripts/setup.ps1`, `scripts/lint.ps1`, `scripts/test.ps1`, `scripts/verify.ps1`, and `scripts/repo_check.py`.

### C. Per-file changes
- `src/pwd301/config.py`: Implemented `BaseConfig`, `DevelopmentConfig`, `TestingConfig`, and `ProductionConfig` with all non-negotiable invariant defaults (video limit < 1 GB, AI chat 300s timeout, session cookie security flags, storage roots).
- `src/pwd301/extensions.py`: Initialized extension shells `db` (`SQLAlchemy`), `migrate` (`Migrate`), `csrf` (`CSRFProtect`), and `login_manager` (`LoginManager`).
- `src/pwd301/blueprints/__init__.py`: Package marker for blueprints.
- `src/pwd301/blueprints/core/__init__.py`: Exported `core_bp`.
- `src/pwd301/blueprints/core/routes.py`: Implemented `GET /health` probe (HTTP 200 JSON with status/env/version) and informative `GET /` root page.
- `src/pwd301/__init__.py`: Application factory `create_app(config_name=None)`, structured UTC console logging, request correlation ID propagation (`X-Correlation-ID`), centralized error handlers conforming to `14_ERROR_MODEL.md` (400, 404, 405, 500, CSRFError).
- `pyproject.toml`: Added `pythonpath = ["src"]` to pytest ini, mypy overrides for `flask_login.*` and `flask_wtf.*`, and per-file-ignores for context generation script.
- `scripts/repo_check.py`: Re-wrapped lines to strictly adhere to 100-character line length limit.
- `tests/conftest.py`: Shared pytest fixtures (`app`, `client`, `runner`).
- `tests/unit/test_config.py`: Comprehensive test suite for configuration classes, environment mapping, and invariant enforcement.
- `tests/unit/test_factory.py`: Unit tests for `create_app`, extension registration, error handlers (JSON vs HTML), correlation ID tracking, and fallback defaults.
- `tests/api/test_smoke.py`: Integration smoke tests verifying `/health` and `/` endpoints.

### D. Deletion and simplification list
| Candidate | Classification | Reason | Action |
|---|---|---|---|
| Business Models & Migrations | KEEP (DEFERRED) | Belongs strictly to TASK-002 | Did not create any premature SQLAlchemy models or migrations |
| JWT implementation & endpoints | KEEP (DEFERRED) | Belongs to Auth domain implementation | Kept configuration parameters; no premature handlers |
| Queue / Vector DB technology | REMOVE NOW | Invariant rule: no premature infrastructure | Kept standard requirements.txt foundation |

### E. Ponytails / deferred debt
- `PONYTAIL-001`: Microsoft SQL Server live connection verification deferred to database/migration task (TASK-002) where SQL Server container and migrations are executed.
  - Trigger: TASK-002 execution.
  - Owner: Backend / DB Agent.
  - Risk: ODBC driver compatibility discrepancies across varied developer machines.
  - Temporary safeguard: `pyodbc` installed and validated; in-memory SQLite used safely for unit and smoke test suites.

### F. Verification actually run and results
- `scripts/repo_check.py`: PASS (71 CREATE TABLE statements verified, no duplicate DB schemas, balanced markdown fences).
- `python -m compileall -q src tests scripts`: PASS (Byte-compilation succeeded with 0 errors).
- `ruff check src tests scripts`: PASS (0 linting errors).
- `ruff format --check src tests scripts`: PASS (13 files checked, 100% formatted).
- `mypy src`: PASS (Success: no issues found in 6 source files).
- `pytest`: PASS (23 passed in 0.12s, 96% coverage on `src`).
- Aggregate command `./scripts/verify.ps1`: PASS.

### G. Remaining risks / next step
- Next scheduled task is **TASK-002 — Domain Models & Initial SQL Server Migrations**.
- Do not proceed to TASK-002 until explicitly assigned.
