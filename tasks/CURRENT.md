# TASK-029 — Docker, Production Deployment & Demo Readiness

**Status:** COMPLETED  
**Assignee:** Principal Software Architect & Lead Fullstack Engineer  
**Started Date:** 2026-09-11  
**Completed Date:** 2026-09-11  

---

## Goal
Package the complete PWD301 Online Course Management Platform onto Docker with a production-grade multi-container architecture (`web`, `db`, `clamav`), automated database wait/provision/migration loop, a comprehensive realistic demonstration seed engine (`src/pwd301/seeds/demo.py`), and one-command deployment documentation (`docs/10_DEPLOYMENT.md`).

---

## Source-of-Truth Documents
- `AGENTS.md` (Operational contract, Fail-closed invariants, Zero Internal PK Leakage, non-root user)
- `docs/system/PWD301_SYSTEM_SPECIFICATION/operations/01_DOCKER_AND_ENVIRONMENT.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/operations/02_CONFIGURATION.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/operations/04_DATABASE_BACKUP_RESTORE.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/operations/06_SYSTEM_HEALTH.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/01_BUSINESS_RULE_CATALOG.md`
- `docs/database/PWD301_DATABASE_ARCHITECTURE/` (71 canonical tables)
- `tasks/BACKLOG.md` & `tasks/templates/TASK_TEMPLATE.md`

---

## Preconditions
- Virtual environment at `.venv` with Python 3.12.
- Canonical SQL Server schema intact (71 tables).
- TASK-001 through TASK-028 complete (all 811 tests passing).

---

## In Scope
1. **Production Multi-Stage Dockerfile (`Dockerfile`)**:
   - `python:3.12-slim-bookworm` base image.
   - Microsoft ODBC Driver 18 for SQL Server (`msodbcsql18`), `unixodbc`, `curl`, `gnupg`.
   - Multi-stage build with wheel compilation in builder stage.
   - Non-root user `appuser:appgroup` (UID 10001).
   - Dedicated storage volumes: `/app/storage`, `/app/quarantine`, `/app/backups`, `/app/exports`.
   - Gunicorn WSGI server configuration with ProxyFix, timeout >= 120s.
2. **Multi-Container Orchestration (`docker-compose.yml`)**:
   - 3 isolated services in `pwd301_net`:
     - `db`: Microsoft SQL Server 2022 (`mcr.microsoft.com/mssql/server:2022-latest`), persistent `sqldata` volume, sqlcmd healthcheck.
     - `clamav`: Malware scanning daemon (`clamav/clamav:latest`), port 3310.
     - `web`: Flask LMS engine built from `Dockerfile`, dependent on healthy `db` and `clamav`.
   - Entrypoint script (`scripts/docker-entrypoint.sh` & `scripts/wait_for_db.py`):
     - Wait for SQL Server and auto-create target database if missing.
     - Auto-run Alembic migrations (`flask db upgrade`).
     - Auto-seed baseline roles and admin (`flask seed-baseline`).
     - Auto-seed demo dataset if `SEED_DEMO_DATA=true` (`flask seed-demo`).
     - Launch Gunicorn WSGI server.
3. **Demo Data Seed Engine (`src/pwd301/seeds/demo.py` & CLI)**:
   - CLI commands: `flask seed-demo` and `flask seed demo`.
   - 7 canonical accounts (1 Admin, 2 Instructors, 4 Students) with password `Password123!`.
   - 3 Courses in different states: `PUBLISHED`, `DRAFT`, `SUBMITTED_FOR_REVIEW`.
   - Prerequisite dependency (CS101 -> CS201, cycle-free).
   - Lessons with rich Markdown and clean file attachments.
   - Question bank with all 5 types (SINGLE_CHOICE, MULTIPLE_CHOICE, TRUE_FALSE, SHORT_ANSWER, ESSAY) and Bloom taxonomy.
   - Assessment published with blueprint/sections.
   - Sample assessment attempts: 1 fully graded (with essay instructor grade/feedback) and 1 submitted awaiting essay grading.
   - Sample in-app notifications and audit events.
   - Full idempotency across repeated runs.
4. **Deployment & Operational Guide (`docs/10_DEPLOYMENT.md`)**:
   - Step-by-step single-command deployment (`docker compose up --build -d`).
   - Health probes (`/health`, `/health/deep`).
   - Role demo credentials and verification scenarios.
   - In-container test execution guide (`docker compose exec web pytest`).
5. **Testing & Quality Assurance**:
   - Unit and integration tests for `seed-demo` and CLI commands.
   - Verify zero regression across entire repository test suite (814 tests passing).

---

## Out of Scope
- Modifying canonical SQL Server DDL or adding new tables.
- Introducing external message brokers (RabbitMQ/Kafka) or Redis.
- Modifying existing passing tests.

---

## Acceptance Criteria Checklist
- [x] **AC-01**: `Dockerfile` build configuration valid, non-root user `appuser`, ODBC Driver 18, multi-stage.
- [x] **AC-02**: `docker-compose.yml` cleanly defines 3 services (`db`, `clamav`, `web`) with healthchecks and volumes.
- [x] **AC-03**: Entrypoint script implements wait-for-DB retry loop, auto-migration, and auto-seeding.
- [x] **AC-04**: `flask seed-demo` populates comprehensive realistic dataset adhering strictly to 73 business rules and ADRs.
- [x] **AC-05**: Operational documentation `docs/10_DEPLOYMENT.md` covers full lifecycle and demo workflows.
- [x] **AC-06**: Repository contract check `scripts/repo_check.py`, `ruff check`, `ruff format --check`, and `mypy src` pass with 0 errors.
- [x] **AC-07**: Entire test suite passes 100% (814/814 tests).
- [x] **AC-08**: Documentation and workflow status files synchronized.
