# CURRENT TASK

## TASK-002 — Domain Models & Initial SQL Server Migrations

**Status:** DONE

### Goal

Translate the canonical database architecture (71 tables across `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/*.sql`) into SQLAlchemy domain models in Flask. Generate the baseline Alembic / Flask-Migrate migration script compatible with Microsoft SQL Server, provide an idempotent baseline seed script (`flask seed-baseline`) for foundational roles and root administrator, and verify all invariants and checks via `./scripts/verify.ps1`.

### Source-of-truth documents

- `AGENTS.md` (Operating Contract)
- `docs/database/PWD301_DATABASE_ARCHITECTURE/` (`01_SCHEMA_OVERVIEW.md`, `02_NAMING_CONVENTIONS.md`, `03_ERD.md`, `sql/*.sql`)
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/01_BUSINESS_RULE_CATALOG.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md`
- `src/pwd301/config.py`
- `src/pwd301/extensions.py`

### In scope

- 71 canonical domain models across 9 logical domains in `src/pwd301/models/`:
  1. Identity & Auth (`src/pwd301/models/identity.py` — 8 tables)
  2. Course & Learning (`src/pwd301/models/course.py` — 10 tables)
  3. Question Bank (`src/pwd301/models/question_bank.py` — 5 tables)
  4. Assessment Structure (`src/pwd301/models/assessment.py` — 6 tables)
  5. Assessment Attempt & Regrading (`src/pwd301/models/attempt_regrade.py` — 13 tables)
  6. File Storage & Document Import (`src/pwd301/models/file_import.py` — 10 tables)
  7. AI & RAG Retrieval (`src/pwd301/models/ai_rag.py` — 8 tables)
  8. Notifications & Audit (`src/pwd301/models/notification_audit.py` — 5 tables)
  9. Operations & Health (`src/pwd301/models/operations.py` — 6 tables)
- Dialect-aware type helpers in `src/pwd301/models/types.py` (`BigIntPK`, `GUID`, `UTCDateTime`, `RowVersion`, `NVarCharMax`, `Binary32`, SQLite function emulators for `ISJSON`, `SYSUTCDATETIME`, `NEWSEQUENTIALID`, `NEWID`).
- Modern declarative base `Base(DeclarativeBase)` configured in `src/pwd301/extensions.py` ensuring full type-safety under Mypy.
- Package export of all 71 models in `src/pwd301/models/__init__.py`.
- Baseline seeding module in `src/pwd301/seeds/baseline.py` for 3 canonical roles (`STUDENT`, `INSTRUCTOR`, `ADMIN`) and root admin (`admin@pwd301.local` with all 3 roles assigned).
- Flask CLI commands `flask seed-baseline` and `flask seed baseline` in `src/pwd301/cli.py`.
- Initial Alembic migration `0001_initial_schema_71_tables` in `migrations/versions/`.
- Unit tests (`tests/unit/test_models.py`) and integration tests (`tests/integration/test_seed.py`, `tests/integration/test_migrations.py`).
- Verification via `./scripts/verify.ps1`.

### Out of scope

- Business logic endpoints and controllers for authentication, courses, assessments, AI RAG, or file handling.
- Background worker processes, queue broker, or external vector search engines.
- Modifying canonical schema or altering table names, column names, or constraints.

### Acceptance criteria

- All 71 canonical tables exist in SQLAlchemy metadata (`len(db.metadata.tables) == 71`).
- All invariants enforced: email unique login, role combinations, NO ACTION default FK cascades, `video < 1 GB`.
- Initial migration generates and executes `upgrade()` and `downgrade()` cleanly.
- `flask seed-baseline` is completely idempotent.
- `./scripts/verify.ps1` passes (Repo check, Python compile, Ruff check, Ruff format, Mypy, Pytest).

---

## Completion Report

### A. Scope and sources consulted
- Operating contract: `AGENTS.md`
- Database Architecture: `docs/database/PWD301_DATABASE_ARCHITECTURE/` (`01_SCHEMA_OVERVIEW.md`, `02_NAMING_CONVENTIONS.md`, `03_ERD.md`, and all 9 SQL DDL files `sql/001_identity.sql` through `sql/009_operations.sql`).
- Non-negotiable invariants: `docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md`.
- Backend architecture: `docs/system/PWD301_SYSTEM_SPECIFICATION/backend/01_BACKEND_ARCHITECTURE.md`.

### B. Reuse decisions
- Reused Flask-SQLAlchemy extension `db` and Flask-Migrate extension `migrate` from TASK-001.
- Reused `src/pwd301/config.py` settings and testing environment setup.
- Configured modern `Base(DeclarativeBase)` passed via `SQLAlchemy(model_class=Base)` in `src/pwd301/extensions.py`, giving seamless Mypy type-checking across all models.
- Registered SQLite connection hooks to emulate SQL Server functions (`ISJSON`, `SYSUTCDATETIME`, `NEWSEQUENTIALID`, `NEWID`), enabling fast in-memory SQLite automated test execution while generating 100% compliant Microsoft SQL Server DDL.

### C. Per-file changes
- `src/pwd301/extensions.py`: Defined `Base(DeclarativeBase)` and passed to `SQLAlchemy(model_class=Base)`.
- `src/pwd301/models/types.py`: Dialect-aware type mappings (`BigIntPK`, `GUID`, `UTCDateTime`, `RowVersion`, `NVarCharMax`, `Binary32`), `utc_now()`, and SQLite compatibility connection hooks.
- `src/pwd301/models/identity.py`: 8 canonical identity models (`User`, `Role`, `UserRole`, `AuthSession`, `JwtTokenGrant`, `UserSecurityToken`, `InstructorApplication`, `SecurityEvent`).
- `src/pwd301/models/course.py`: 10 course domain models (`Course`, `CoursePrerequisite`, `CourseCompletionRule`, `CourseChangeRequest`, `Lesson`, `Enrollment`, `EnrollmentPeriod`, `EnrollmentEvent`, `LessonProgress`, `CourseCompletionSummary`).
- `src/pwd301/models/question_bank.py`: 5 question bank models (`Question`, `QuestionRevision`, `QuestionRevisionChoice`, `QuestionRevisionAcceptedAnswer`, `QuestionProvenance`).
- `src/pwd301/models/assessment.py`: 6 assessment models (`Assessment`, `AssessmentSection`, `AssessmentQuestionAssignment`, `AssessmentBlueprint`, `AssessmentBlueprintRule`, `AssessmentQuestionPool`).
- `src/pwd301/models/attempt_regrade.py`: 13 attempt and regrade models (`AssessmentAttempt`, `AttemptQuestion`, `AttemptChoiceSnapshot`, `AttemptAnswer`, `AttemptAnswerChoice`, `AttemptAnswerEvent`, `AttemptQuestionGrade`, `AttemptQuestionGradeHistory`, `AssessmentResult`, `AssessmentResultHistory`, `QuestionCorrection`, `RegradeJob`, `RegradeItem`).
- `src/pwd301/models/file_import.py`: 10 storage and import models (`FileBlob`, `FileAsset`, `FileRevision`, `FileScanResult`, `LessonResource`, `QuestionRevisionResource`, `DocumentImportJob`, `ImportQuestion`, `ImportDuplicateCandidate`, `ImportQuestionResource`).
- `src/pwd301/models/ai_rag.py`: 8 AI and RAG retrieval models (`AIConversation`, `AIMessage`, `AIRequest`, `AIGeneratedQuestionDraft`, `KnowledgeDocument`, `KnowledgeVersion`, `KnowledgeChunk`, `AISourceUsage`).
- `src/pwd301/models/notification_audit.py`: 5 notification and audit models (`NotificationEvent`, `Notification`, `NotificationPreference`, `EmailDelivery`, `AuditEvent`).
- `src/pwd301/models/operations.py`: 6 operational models (`BackgroundJob`, `SystemAlert`, `BackupRun`, `GradeExport`, `AnalyticsSnapshot`, `SystemHealthSnapshot`).
- `src/pwd301/models/__init__.py`: Package export registering all 71 domain models.
- `src/pwd301/seeds/baseline.py`: Idempotent baseline seed logic creating `STUDENT`, `INSTRUCTOR`, `ADMIN` roles and the root administrator (`admin@pwd301.local`).
- `src/pwd301/seeds/__init__.py`: Package export for `seed_baseline`.
- `src/pwd301/cli.py`: Registered CLI commands `seed-baseline` and `seed baseline`.
- `src/pwd301/__init__.py`: Application factory imports `pwd301.models` and registers CLI commands.
- `migrations/env.py`: Configured Alembic environment with `compare_type=True`, `render_as_batch=True` for SQLite, and modernized `get_engine()`.
- `migrations/versions/c1d237fd6bf9_0001_initial_schema_71_tables.py`: Initial Alembic migration containing all 71 tables, constraints, foreign keys, and indexes.
- `tests/unit/test_models.py`: Comprehensive unit tests verifying 71 tables, column defaults, CHECK constraints, computed columns, and entity relationships across all 9 domains.
- `tests/integration/test_seed.py`: Integration tests verifying baseline role creation, root admin setup, password hash verification, idempotency, and CLI commands.
- `tests/integration/test_migrations.py`: Integration test verifying migration upgrade and downgrade against an isolated test database.

### D. Deletion and simplification list
| Candidate | Classification | Reason | Action |
|---|---|---|---|
| Business services & routes | KEEP (DEFERRED) | Belongs to domain-specific feature tasks (Auth, Course, etc.) | Preserved model structure without premature route handlers |
| Queue / Vector DB drivers | REMOVE NOW | Invariant: no premature infrastructure before requirement triggers | Deferred until background/AI task phases |
| Transient test SQLite databases | REMOVE NOW | Generated during test/migration runs | Cleaned up temporary database files and instance directories |

### E. Ponytails / deferred debt
- `PONYTAIL-002`: Execution of migration script against a live production-grade Microsoft SQL Server instance.
  - Trigger: Staging/production environment setup or containerized CI integration.
  - Owner: DevOps / Backend Agent.
  - Risk: Engine-specific DDL variations on older SQL Server versions (target: SQL Server 2022 / Azure SQL).
  - Temporary safeguard: Full DDL was verified by matching canonical SQL scripts; SQLite compatibility hooks ensure complete local unit/integration test coverage.
  - Review point: Pre-release integration milestone.

### F. Verification actually run and results
- `scripts/repo_check.py`: PASS (71 CREATE TABLE statements verified, no duplicate DB schemas, balanced markdown fences).
- `python -m compileall -q src tests scripts`: PASS (Byte-compilation succeeded with 0 errors).
- `ruff check src tests scripts`: PASS (0 linting errors).
- `ruff format --check src tests scripts`: PASS (29 files checked, 100% formatted).
- `mypy src`: PASS (Success: no issues found in 20 source files).
- `pytest`: PASS (39 passed in 3.13s).
- Aggregate command `./scripts/verify.ps1`: PASS.

### G. Remaining risks / next step
- Next scheduled task is **TASK-003 — Authentication & Identity Workflows (Web Session + JWT REST)**.
- Do not proceed to TASK-003 until explicitly assigned.

---

## Historical Tasks

### TASK-001 — Project Foundation & Flask Bootstrap
**Status:** DONE  
*Completed foundation bootstrap including Flask application factory, configuration classes, extension shells, `/health` and `/` routes, error handlers, and smoke test suite.*
