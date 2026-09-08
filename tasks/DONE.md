# Completed Tasks

## TASK-001 — Project Foundation & Flask Bootstrap
- **Completion date:** 2026-09-08
- **Important files changed:**
  - `src/pwd301/config.py` (Base, Development, Testing, Production configurations with non-negotiable invariants)
  - `src/pwd301/extensions.py` (SQLAlchemy, Migrate, CSRFProtect, LoginManager shells)
  - `src/pwd301/__init__.py` (create_app factory, structured UTC logging, correlation ID, centralized error handlers)
  - `src/pwd301/blueprints/core/routes.py` (/health JSON probe, / informative root page)
  - `tests/conftest.py`, `tests/unit/test_config.py`, `tests/unit/test_factory.py`, `tests/api/test_smoke.py`
  - `pyproject.toml`, `scripts/repo_check.py`
- **Migrations created:** None (deferred to TASK-002 per specification)
- **Verification commands and results:**
  - `./scripts/verify.ps1`: PASS (repo_check, compileall, ruff check, ruff format --check, mypy src, pytest 23 passed with 96% coverage)
- **Known non-blocking limitations:** Live SQL Server connection and database migrations are scheduled for TASK-002.
