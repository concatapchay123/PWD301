# PROJECT DISCOVERY REPORT — PHASE 1 AUDIT & INVENTORY

**Project Name:** PWD301 — Intelligent Enterprise Learning & Assessment Management Platform  
**Audit Phase:** Phase 1 — Project Discovery & Inventory  
**Auditor Mode:** Read-Only Analysis & Deep System Mapping  
**Date of Audit:** 2026-10-02  
**Operating Contract:** AGENTS.md / System Specification Precedence / Non-Negotiable Invariants  

---

## 1. Discovery Scope

The Phase 1 Discovery audit covers the entire codebase of repository `e:\PWD301`. In strict adherence to the **READ-ONLY RULE**, no production code, configuration files, environment variables, or database schemas have been altered, formatted, patched, or deployed.

### Inspected Surfaces
1. **Frontend Presentation Tier:**
   - Single-DOM Web Single Page Application (SPA) located at `frontend/index.html`.
   - Client scripts: `frontend/assets/js/` (`api.js`, `router.js`, `ui.js`, `exam-store.js`, `controllers.js`, `views/*.js`).
   - UI Design System specifications: `frontend/alexandria/DESIGN.md`, `frontend/carbon/DESIGN.md`, `frontend/productive_clarity/DESIGN.md`.
2. **Backend Application Tier:**
   - Flask Modular Monolith application factory at `src/pwd301/__init__.py`.
   - Configuration registry at `src/pwd301/config.py` and CLI management at `src/pwd301/cli.py`.
   - 17 Flask blueprints across role-based Web routing (`auth`, `student`, `instructor`, `admin`, `frontend`, `core`) and headless REST API routing (`api_auth`, `api_admin`, `api_courses`, `api_lessons`, `api_student`, `api_assessments`, `api_attempts`, `api_files`, `api_import`, `api_notifications`, `api_ai`).
   - 33 Service layer modules in `src/pwd301/services/`.
3. **Database & Persistence Tier:**
   - Canonical MS SQL Server 2022 Architecture at `docs/database/PWD301_DATABASE_ARCHITECTURE/` (73 DDL tables in `sql/`, 22 architecture specifications).
   - SQLAlchemy ORM models across 9 domain modules in `src/pwd301/models/` (73 entity tables).
   - Alembic database migration scripts at `migrations/versions/` (9 migration revisions).
   - Database bootstrap seeds at `src/pwd301/seeds/` (`baseline.py`, `demo.py`).
4. **Testing Tier:**
   - 163 Python test files in `tests/` (`unit/`, `api/`, `security/`, `concurrency/`, `integration/`, `e2e/`, and root suites) collecting **1,530 automated test cases**.
   - 26 JavaScript frontend test suites in `tests/frontend/`.
5. **Infrastructure & Operations Tier:**
   - Container configuration: `Dockerfile` (multi-stage build), `docker-compose.yml` (orchestrating Flask Web Engine, MS SQL Server 2022, and ClamAV Antivirus Daemon).
   - Continuous Integration: `.github/workflows/ci.yml`.
   - Operational automation scripts in `scripts/` (database waits, telemetry bridge, verification hooks).

---

## 2. Sources Reviewed

| Category | Primary Source Files | Purpose & Authority |
|---|---|---|
| **Root Governance** | `AGENTS.md`, `README.md`, `CONTRIBUTING.md` | Master operating contract, source-of-truth hierarchy, rubric compliance overview. |
| **Current Tasks** | `tasks/CURRENT.md`, `tasks/BACKLOG.md`, `tasks/DONE.md`, `tasks/TASK-071.md`..`TASK-078.md` | Active scope boundaries, historical bugfixes (TASK-060 to TASK-078), question bank decommissioning context. |
| **System Specification** | `docs/system/PWD301_SYSTEM_SPECIFICATION/` (`00_MASTER_SYSTEM_SPEC.md`, `01_PRODUCT_SCOPE_AND_GOALS.md`, `04_SYSTEM_ARCHITECTURE.md`, `CODING_AGENT_START_HERE.md`) | Canonical business rules, non-negotiable invariants, domain state machines, threat models. |
| **Business Rules** | `docs/system/PWD301_SYSTEM_SPECIFICATION/business/01_BUSINESS_RULE_CATALOG.md` | 82 normative business rules across Identity, Course, Assessment, Attempt, File, AI, Audit, and Operations. |
| **Database Architecture** | `docs/database/PWD301_DATABASE_ARCHITECTURE/` (`01_ARCHITECTURE_OVERVIEW.md` through `21_ASSUMPTIONS_AND_DECISIONS.md`, `sql/001_identity.sql`..`012_critical_invariant_triggers.sql`) | Sole canonical database contract, 73 MS SQL Server reference DDLs, ERD models. |
| **Decisions (ADRs)** | `docs/decisions/` (`ADR-001` through `ADR-010`) | Architectural Decision Records: Session/JWT split, DB UUIDs, Question revisions, Attempt lease, RAG scoping. |
| **API Catalog** | `docs/system/PWD301_SYSTEM_SPECIFICATION/api/02_ENDPOINT_CATALOG.md` | Authoritative REST API endpoint specifications and JSON contracts. |
| **Backend Implementation** | `src/pwd301/__init__.py`, `config.py`, `models/*.py`, `services/*.py`, `blueprints/*/routes.py` | Executable reality of domain logic, security checks, and routing. |
| **Frontend Implementation** | `frontend/index.html`, `frontend/assets/js/api.js`, `router.js`, `ui.js`, `exam-store.js`, `views/*.js` | Executable reality of single-DOM SPA presentation, state management, and user interaction. |
| **Test Suites** | `tests/conftest.py`, `tests/unit/`, `tests/api/`, `tests/security/`, `tests/frontend/` | Executable regression baselines and empirical verification evidence. |

---

## 3. Project Structure

```
PWD301/
├── .github/
│   └── workflows/ci.yml             # GitHub Actions CI workflow (contract, ruff, mypy, pytest)
├── api/
│   └── api_key.md                   # External API keys document (Security finding: plaintext keys)
├── docs/
│   ├── archive/                     # Historical monolithic READMEs and superseded documents
│   ├── audits/                      # Prior technical audit records (performance, navigation)
│   ├── database/
│   │   └── PWD301_DATABASE_ARCHITECTURE/ # Canonical Database Contract (22 specs + 12 SQL DDL files)
│   ├── decisions/                   # Architectural Decision Records (ADR-001 to ADR-010)
│   ├── diagrams/                    # Standalone interactive HTML workflow diagrams
│   ├── features/                    # Feature domain guides (courses, assessments, users, ai-rag)
│   └── system/
│       └── PWD301_SYSTEM_SPECIFICATION/  # Canonical System Specification (15 subdirectories)
├── frontend/                        # Web Presentation Tier (Pure Headless Client)
│   ├── index.html                   # Single-DOM SPA Shell (Tailwind CDN, Warm Editorial tokens)
│   ├── assets/
│   │   ├── img/                     # Static graphics (octopus_ai_icon.png, etc.)
│   │   └── js/
│   │       ├── api.js               # ApiClient: centralized HTTP communication with CSRF retry
│   │       ├── router.js            # AppRouter: hash-based routing, dynamic topbar, sub-role guards
│   │       ├── ui.js                # UI helpers: toasts, stacked modals, confirm dialogs, YouTube parser
│   │       ├── exam-store.js        # ExamStore: multi-step exam wizard draft persistence (localStorage)
│   │       ├── controllers.js       # Unreferenced legacy screen controller classes (vibe artifact)
│   │       └── views/
│   │           ├── auth.js          # AuthView: login, register, password reset forms
│   │           ├── student.js       # StudentView: Cisco NetAcad 3-col console, anti-seek player, exam console
│   │           ├── instructor.js    # InstructorView: course management, lesson studio, grading overview
│   │           ├── instructor-exams.js # InstructorExamsView: Exam Studio Word/Azota/Excel/Moodle split-view
│   │           └── admin.js         # AdminView: Governance cockpit, 5 sub-roles, telemetry, audit logs
│   ├── alexandria/DESIGN.md         # Alexandria design system specification
│   ├── carbon/DESIGN.md             # Carbon governance design system specification
│   └── productive_clarity/DESIGN.md # Productive clarity design system specification
├── migrations/                      # Alembic Database Migration Tier
│   ├── env.py                       # Alembic environment runner
│   ├── script.py.mako               # Migration template
│   └── versions/                    # 9 migration scripts (0001 initial 71 tables to 0009 notification outbox)
├── scripts/                         # Operational & Verification Scripts
│   ├── docker-entrypoint.sh         # Container startup script (migrations, baseline, gunicorn)
│   ├── repo_check.py                # Static repository contract validator
│   ├── verify.ps1 / verify.sh       # Full verification suite (lint, typecheck, pytest)
│   └── test_live_fixes.py           # Verification scripts for production hotfixes
├── src/
│   └── pwd301/                      # Backend Application Package (Python 3.11+ / Flask)
│       ├── __init__.py              # Application factory `create_app()`, error handlers, CSP, middleware
│       ├── config.py                # Environment configuration classes (BaseConfig, Dev, Test, Prod)
│       ├── extensions.py            # Extension singletons (SQLAlchemy, Migrate, CSRFProtect, LoginManager)
│       ├── cli.py                   # Flask CLI commands (`seed-baseline`, `seed-demo`, `db-restore`)
│       ├── blueprints/              # 17 Modular Flask Blueprints (Web + Headless REST API)
│       ├── models/                  # 73 SQLAlchemy ORM Models mapping directly to canonical SQL DDL
│       ├── services/                # 33 Domain Services executing business rules and transactions
│       └── seeds/                   # System baseline and demo seed definitions
├── tasks/                           # Task Governance & Execution Records
│   ├── CURRENT.md                   # Current and recently finished execution scopes (TASK-078 latest)
│   ├── BACKLOG.md                   # Engineering backlog
│   └── TASK-*.md                    # Detailed completion reports for tasks 070 through 077
├── tests/                           # Automated Verification Suite (1,530 pytest tests)
│   ├── api/                         # 58 integration test files for Web & REST API endpoints
│   ├── concurrency/                 # 4 concurrency stress tests (lease race, enrollment capacity)
│   ├── e2e/                         # 4 end-to-end lifecycle simulation tests
│   ├── frontend/                    # 26 JavaScript frontend test suites
│   ├── integration/                 # 3 database migration and seeding integration tests
│   ├── security/                    # 28 security & penetration test suites (IDOR, CSRF, AI guardrails)
│   └── unit/                        # 44 domain service and model unit test suites
├── Dockerfile                       # Multi-stage production container build (Debian 12 + ODBC 18)
├── docker-compose.yml               # Multi-service stack (Flask Web, MS SQL Server 2022, ClamAV)
├── pyproject.toml                   # Project metadata and tool configuration (Ruff, Mypy, Pytest)
├── requirements.txt                 # Runtime production dependencies
└── requirements-dev.txt             # Development and test dependencies
```

---

## 4. Requirement Inventory

### 4.1. Academic Topic 9 Baseline Requirements (`PWD301_Project.docx` / `README.md`)

| ID | Requirement Description | Source | Code & Documentation Evidence |
|---|---|---|---|
| `REQ-001` | Framework Flask (Python 3.11+) with Microsoft SQL Server as primary relational database | Topic 9 Rubric Item 1 | `src/pwd301/__init__.py`, `docker-compose.yml` (`mcr.microsoft.com/mssql/server:2022-latest`) |
| `REQ-002` | Flask-SQLAlchemy ORM with minimum 4 tables and at least one Many-to-Many relationship | Topic 9 Rubric Item 2 | `src/pwd301/models/` (73 tables), `user_roles`, `course_prerequisites`, `attempt_answer_choices` |
| `REQ-003` | Flask-WTF forms with CSRF protection and server-side validation | Topic 9 Rubric Item 3 | `src/pwd301/extensions.py` (`CSRFProtect`), `src/pwd301/__init__.py:505`, cookie `csrf_token` |
| `REQ-004` | Flask-Login authentication and RBAC with minimum 3 roles (`STUDENT`, `INSTRUCTOR`, `ADMIN`) | Topic 9 Rubric Item 4 | `src/pwd301/models/identity.py`, `src/pwd301/services/authorization_service.py` |
| `REQ-005` | Minimum 3 REST API endpoints returning JSON format authenticated via JWT | Topic 9 Rubric Item 5 | `src/pwd301/blueprints/api_courses/`, `api_auth/`, `api_assessments/` (150+ REST endpoints with Bearer JWT) |
| `REQ-006` | AJAX / Fetch API for at least one dynamic feature without full page reload | Topic 9 Rubric Item 6 | Entire platform transformed into Single-DOM SPA (`frontend/index.html`, `frontend/assets/js/api.js`) |
| `REQ-007` | Responsive design across devices | Topic 9 Rubric Item 7 | Tailwind CSS Warm Editorial, mobile navigation drawer, collapsible panels |
| `REQ-008` | Database schema migrations via Flask-Migrate / Alembic with reproducible seed data | Topic 9 Rubric Item 8 | `migrations/versions/` (9 scripts), `src/pwd301/seeds/baseline.py`, `demo.py` |
| `REQ-009` | Containerization with Docker (`Dockerfile` and `docker-compose.yml`) | Topic 9 Rubric Item 9 | Multi-stage `Dockerfile`, `docker-compose.yml` orchestrating Web, DB, and ClamAV |
| `REQ-010` | AI tool integration and AI usage logging | Topic 9 Rubric Item 10 | Gemini AI Assistant ("Bạch tuộc trợ lí AI"), `src/pwd301/services/gemini_service.py`, `ai_requests` table |
| `REQ-011` | Git repository management with installation and operations `README.md` | Topic 9 Rubric Item 11 | Root `README.md` (429 lines), `CONTRIBUTING.md`, `LICENSE` (MIT) |
| `REQ-012` | Project presentation defense preparedness (Slide + Live Demo + Q&A) | Topic 9 Rubric Item 12 | Seeded demo accounts (`admin@example.com`, `instructor@example.com`, `student@example.com`) |
| `REQ-013` | Topic 9 Feature 1: User Management & Authentication (Registration, login, role assignment) | Topic 9 Key Feature 1 | `src/pwd301/services/user_service.py`, `frontend/assets/js/views/auth.js` |
| `REQ-014` | Topic 9 Feature 2: Course Management (Creation, syllabus, categories, enrollment capacity) | Topic 9 Key Feature 2 | `src/pwd301/services/course_service.py`, `frontend/assets/js/views/instructor.js` |
| `REQ-015` | Topic 9 Feature 3: Enrollment & Progress Tracking (Enroll in courses, lesson completion) | Topic 9 Key Feature 3 | `src/pwd301/services/enrollment_service.py`, `completion_service.py` |
| `REQ-016` | Topic 9 Feature 4: Online Assessment / Quiz (Multiple choice quizzes, timed exams, automated grading) | Topic 9 Key Feature 4 | `src/pwd301/services/assessment_service.py`, `attempt_service.py` |
| `REQ-017` | Topic 9 Feature 5: Content & Resource Management (Lesson authoring, video embedding, attachments) | Topic 9 Key Feature 5 | `src/pwd301/services/lesson_service.py`, `file_service.py` |
| `REQ-018` | Topic 9 Feature 6: Administrative Governance & Reporting (Course approval, system monitoring) | Topic 9 Key Feature 6 | `src/pwd301/services/operations_service.py`, `frontend/assets/js/views/admin.js` |

### 4.2. Canonical System Specification Business Rules (`01_BUSINESS_RULE_CATALOG.md`)

| ID | Requirement Description | Source | Code & Evidence |
|---|---|---|---|
| `REQ-019` | `AUTH-001`: Email is unique login identifier; normalization required | `01_BUSINESS_RULE_CATALOG.md` | `models/identity.py:59` (`email_normalized`), `user_service.py:normalize_email` |
| `REQ-020` | `AUTH-002`: User roles are cumulative (`STUDENT` → `INSTRUCTOR` → `ADMIN`) | `01_BUSINESS_RULE_CATALOG.md` | `models/identity.py:101`, `authorization_service.py:require_roles` |
| `REQ-021` | `AUTH-003`: User suspension immediately revokes all active Web sessions and JWT tokens | `01_BUSINESS_RULE_CATALOG.md` | `user_service.py:suspend_user` (`auth_version += 1`), `auth_sessions.is_revoked` |
| `REQ-022` | `AUTH-004`: Dual auth separation: Web UI uses session cookie; REST API uses Bearer JWT | `01_BUSINESS_RULE_CATALOG.md` | `ADR-001`, `session_auth_service.py`, `jwt_auth_service.py` |
| `REQ-023` | `AUTH-005`: Sensitive Admin actions require reauth + confirmation phrase + reason | `01_BUSINESS_RULE_CATALOG.md` | `authorization_service.py:verify_admin_sensitive_reauth`, `admin.js` |
| `REQ-024` | `AUTH-006`: Admin cannot silently impersonate Users; true actor logged in audit trail | `01_BUSINESS_RULE_CATALOG.md` | `audit_service.py:record_audit_event`, `models/notification_audit.py` |
| `REQ-025` | `COURSE-001`: Course code is unique across all courses | `01_BUSINESS_RULE_CATALOG.md` | `models/course.py:65` (`course_code_normalized`), unique index |
| `REQ-026` | `COURSE-002`: Course title is unique across active courses | `01_BUSINESS_RULE_CATALOG.md` | `models/course.py:73` (`title_normalized`), unique index |
| `REQ-027` | `COURSE-003`: Course has 0 or 1 owner Instructor | `01_BUSINESS_RULE_CATALOG.md` | `models/course.py:58` (`owner_instructor_id`), FK to `users.id` |
| `REQ-028` | `COURSE-004`: Revoking Instructor role does not delete owned Courses | `01_BUSINESS_RULE_CATALOG.md` | `user_service.py:remove_role`, `courses.owner_instructor_id` set to null or kept |
| `REQ-029` | `COURSE-005`: Prerequisite graph validation forbids cycles (DAG enforcement) | `01_BUSINESS_RULE_CATALOG.md` | `course_service.py:validate_no_prerequisite_cycles`, DFS cycle check |
| `REQ-030` | `COURSE-006`: Active prerequisite dependency blocks course archiving or deletion | `01_BUSINESS_RULE_CATALOG.md` | `course_service.py:archive_course`, dependency check |
| `REQ-031` | `COURSE-007`: Course enrollment capacity cannot be overbooked under concurrency | `01_BUSINESS_RULE_CATALOG.md` | `enrollment_service.py:enroll_student`, row-level locking on `courses` |
| `REQ-032` | `ENROLL-001`: Exactly one logical active Enrollment per Student per Course | `01_BUSINESS_RULE_CATALOG.md` | `models/course.py:348` (`uq_enrollments_student_course`), unique constraint |
| `REQ-033` | `ENROLL-002`: Re-enrollment creates new period while keeping prior completion summary | `01_BUSINESS_RULE_CATALOG.md` | `enrollment_service.py:re_enroll_student`, `enrollment_periods` table |
| `REQ-034` | `ENROLL-003`: Prior completed Course permanently satisfies prerequisite requirements | `01_BUSINESS_RULE_CATALOG.md` | `course_service.py:is_prerequisite_satisfied`, `course_completion_summaries` |
| `REQ-035` | `ENROLL-004`: Student leave >30 days purges detailed period data; stops regrading | `01_BUSINESS_RULE_CATALOG.md` | `retention_service.py:purge_expired_enrollments` |
| `REQ-036` | `LESSON-001`: Lesson reordering preserves student completion records | `01_BUSINESS_RULE_CATALOG.md` | `lesson_service.py:reorder_lessons`, `lesson_progress` table intact |
| `REQ-037` | `LESSON-002`: Lesson completion requires minimum viewing time and fraction viewed | `01_BUSINESS_RULE_CATALOG.md` | `lesson_service.py:record_progress`, anti-seek timer verification |
| `REQ-038` | `LESSON-003`: Lessons added after enrollment period start do not retroactively break progress | `01_BUSINESS_RULE_CATALOG.md` | `completion_service.py:compute_course_completion` |
| `REQ-039` | `LESSON-004`: Material rewrite does not force already-completed students to retake | `01_BUSINESS_RULE_CATALOG.md` | `lesson_progress.completed_at` persisted permanently |
| `REQ-040` | `QBANK-001`: Question belongs to exactly one Course; Lesson link is optional | `01_BUSINESS_RULE_CATALOG.md` | `models/question_bank.py:46`, FK to `courses.id` |
| `REQ-041` | `QBANK-002`: Unused questions edit in-place; used questions create new QuestionRevision | `01_BUSINESS_RULE_CATALOG.md` | `question_bank_service.py:update_question`, `question_revisions` |
| `REQ-042` | `QBANK-003`: Question choices and accepted answers versioned with revision | `01_BUSINESS_RULE_CATALOG.md` | `models/question_bank.py:180` (`question_revision_choices`) |
| `REQ-043` | `QBANK-004`: Question type cannot mutate after any Student has submitted an answer | `01_BUSINESS_RULE_CATALOG.md` | `question_bank_service.py:update_question`, `QuestionImmutableError` |
| `REQ-044` | `QBANK-005`: Exposed or graded question revisions are retained indefinitely | `01_BUSINESS_RULE_CATALOG.md` | `retention_service.py`, tombstone retention |
| `REQ-045` | `QBANK-006`: Multiple-choice grading requires exact set match (no partial credit) | `01_BUSINESS_RULE_CATALOG.md` | `attempt_service.py:grade_question`, set comparison |
| `REQ-046` | `QBANK-007`: Short answer question supports multiple accepted strings and normalization | `01_BUSINESS_RULE_CATALOG.md` | `models/question_bank.py:230` (`question_revision_accepted_answers`) |
| `REQ-047` | `ASSESS-001`: Assessment timing configuration is locked after publication | `01_BUSINESS_RULE_CATALOG.md` | `assessment_service.py:update_assessment`, trigger check |
| `REQ-048` | `ASSESS-002`: Assessment structure (questions, sections) locked after first student starts | `01_BUSINESS_RULE_CATALOG.md` | `assessment_service.py:publish_assessment`, `first_started_at` flag |
| `REQ-049` | `ASSESS-003`: Assessment assigned points are locked after first student starts | `01_BUSINESS_RULE_CATALOG.md` | `assessment_service.py:update_assigned_points`, `AssessmentLockedError` |
| `REQ-050` | `ASSESS-004`: Assessment blueprint with insufficient pool candidates blocks publish | `01_BUSINESS_RULE_CATALOG.md` | `assessment_service.py:publish_assessment`, preflight validation |
| `REQ-051` | `ASSESS-005`: Student starting an assessment gets the latest approved question revisions | `01_BUSINESS_RULE_CATALOG.md` | `attempt_service.py:start_attempt`, revision resolution |
| `REQ-052` | `ASSESS-006`: Randomized attempt persists exact presentation order snapshot | `01_BUSINESS_RULE_CATALOG.md` | `models/attempt_regrade.py:160` (`attempt_choice_snapshots`) |
| `REQ-053` | `ATTEMPT-001`: Attempt limit per enrollment period is configurable (1..N) | `01_BUSINESS_RULE_CATALOG.md` | `models/assessment.py:72` (`max_attempts`), `attempt_service.py` |
| `REQ-054` | `ATTEMPT-002`: Server-authoritative timer deadline; client clock cannot extend | `01_BUSINESS_RULE_CATALOG.md` | `attempt_service.py:save_answer`, `ADR-006` |
| `REQ-055` | `ATTEMPT-003`: Single Active Tab lease fencing (`lease_token`, `lease_epoch`) | `01_BUSINESS_RULE_CATALOG.md` | `attempt_service.py:acquire_lease`, `renew_lease`, `ADR-005` |
| `REQ-056` | `ATTEMPT-004`: Autosave saves MCQ immediately; text debounce ~1.5s; resume recovers state | `01_BUSINESS_RULE_CATALOG.md` | `attempt_service.py:save_answer`, `models/attempt_regrade.py:220` |
| `REQ-057` | `ATTEMPT-005`: Out-of-order offline autosave events cannot overwrite newer answers | `01_BUSINESS_RULE_CATALOG.md` | `attempt_service.py:save_answer`, `client_seq` ordering |
| `REQ-058` | `ATTEMPT-006`: Answers received after server deadline are strictly rejected | `01_BUSINESS_RULE_CATALOG.md` | `attempt_service.py:save_answer`, `AttemptExpiredError` |
| `REQ-059` | `ATTEMPT-007`: Assessment submission is idempotent; duplicate submits return same result | `01_BUSINESS_RULE_CATALOG.md` | `attempt_service.py:submit_attempt`, `idempotency_key` unique check |
| `REQ-060` | `GRADE-001`: Essay questions require manual grading; result is pending until finalized | `01_BUSINESS_RULE_CATALOG.md` | `attempt_service.py:grade_attempt`, `is_finalized` flag |
| `REQ-061` | `GRADE-002`: Essay grade adjustments keep immutable history (old, new, reason, actor) | `01_BUSINESS_RULE_CATALOG.md` | `models/attempt_regrade.py:440` (`attempt_question_grade_histories`) |
| `REQ-062` | `REGRADE-001`: Correct-answer corrections trigger automatic background regrading | `01_BUSINESS_RULE_CATALOG.md` | `regrade_worker.py:execute_regrade_job`, `question_corrections` |
| `REQ-063` | `REGRADE-002`: Content/choice flaw corrections award full credit to prior affected attempts | `01_BUSINESS_RULE_CATALOG.md` | `regrade_worker.py:regrade_attempt`, full credit policy |
| `REQ-064` | `REGRADE-003`: Historical answer snapshots are never mutated during regrading | `01_BUSINESS_RULE_CATALOG.md` | `regrade_worker.py`, updates `attempt_question_grades` only |
| `REQ-065` | `REGRADE-004`: Regrading worker is resumable and idempotent | `01_BUSINESS_RULE_CATALOG.md` | `models/attempt_regrade.py:640` (`regrade_items`), status tracking |
| `REQ-066` | `FILE-001`: File uploads placed in quarantine; fail-closed ClamAV antivirus scanning | `01_BUSINESS_RULE_CATALOG.md` | `services/scanner_service.py`, `file_service.py:upload_file` |
| `REQ-067` | `FILE-002`: Macro-enabled Office files forbidden; strict format validation | `01_BUSINESS_RULE_CATALOG.md` | `file_service.py:validate_upload`, magic byte validation |
| `REQ-068` | `FILE-003`: Physical storage deduplication by SHA-256 hash | `01_BUSINESS_RULE_CATALOG.md` | `models/file_import.py:45` (`file_blobs.sha256`), unique constraint |
| `REQ-069` | `FILE-004`: File replacement activates only after scan pass; old version recoverable ~30d | `01_BUSINESS_RULE_CATALOG.md` | `models/file_import.py:120` (`file_revisions`) |
| `REQ-070` | `FILE-005`: File downloads served only through authorized application routes | `01_BUSINESS_RULE_CATALOG.md` | `file_service.py:get_download_response`, no raw storage URL exposure |
| `REQ-071` | `IMPORT-001`: Exam import parses Word/Azota/Excel/Moodle into draft state for review | `01_BUSINESS_RULE_CATALOG.md` | `import_service.py`, `excel_exam_service.py`, `moodle_exam_service.py` |
| `REQ-072` | `IMPORT-002`: Ambiguous questions require explicit Instructor confirmation before commit | `01_BUSINESS_RULE_CATALOG.md` | `models/file_import.py:320` (`import_questions`), status `PENDING_REVIEW` |
| `REQ-073` | `IMPORT-003`: Duplicate questions flagged for review; never silently merged | `01_BUSINESS_RULE_CATALOG.md` | `models/file_import.py:370` (`import_duplicate_candidates`) |
| `REQ-074` | `AI-001`: Student AI RAG retrieves only authorized, published course materials | `01_BUSINESS_RULE_CATALOG.md` | `services/rag_service.py:retrieve_context`, course enrollment prefilter |
| `REQ-075` | `AI-002`: Archived or deleted course content is immediately evicted from RAG index | `01_BUSINESS_RULE_CATALOG.md` | `rag_service.py:invalidate_course_index` |
| `REQ-076` | `AI-003`: Raw AI chat messages purged after 5 minutes of inactivity | `01_BUSINESS_RULE_CATALOG.md` | `services/ai_service.py:cleanup_expired_conversations`, 300s TTL |
| `REQ-077` | `AI-004`: Minimal metadata retention; students access only their own conversation | `01_BUSINESS_RULE_CATALOG.md` | `models/ai_rag.py:45` (`ai_conversations`), object-level auth |
| `REQ-078` | `AI-005`: Course recommendations computed by backend algorithm; AI only explains | `01_BUSINESS_RULE_CATALOG.md` | `services/recommendation_service.py:get_recommendations` |
| `REQ-079` | `AI-006`: AI responses record provenance citations (document version, chunk ID) | `01_BUSINESS_RULE_CATALOG.md` | `models/ai_rag.py:320` (`ai_source_usages`) |
| `REQ-080` | `NOTIF-001`: In-app notification with read/unread tracking; asynchronous email delivery | `01_BUSINESS_RULE_CATALOG.md` | `services/notification_service.py`, `models/notification_audit.py` |
| `REQ-081` | `NOTIF-002`: Email provider failure does not roll back business transaction; retried via outbox | `01_BUSINESS_RULE_CATALOG.md` | `models/notification_audit.py:160` (`email_deliveries`), outbox pattern |
| `REQ-082` | `NOTIF-003`: Mandatory security notifications cannot be disabled by user preferences | `01_BUSINESS_RULE_CATALOG.md` | `models/notification_audit.py:120` (`notification_preferences`) |
| `REQ-083` | `AUDIT-001`: Important audit logs are append-only with SHA-256 cryptographic chaining | `01_BUSINESS_RULE_CATALOG.md` | `models/notification_audit.py:220` (`audit_events`), `prev_hash_sha256` |
| `REQ-084` | `AUDIT-002`: Sensitive mutations fail if the audit record cannot be persisted | `01_BUSINESS_RULE_CATALOG.md` | `services/audit_service.py:record_audit_event`, same transaction |
| `REQ-085` | `AUDIT-003`: Admin modification of Instructor content requires reason and triggers notification | `01_BUSINESS_RULE_CATALOG.md` | `audit_service.py`, `notification_service.py` |
| `REQ-086` | `DELETE-001`: Foreign key graph enforces `NO ACTION` default; no broad cascade deletes | `01_BUSINESS_RULE_CATALOG.md` | `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/` (73 DDLs) |
| `REQ-087` | `DELETE-002`: Deletion of used Assessments or Questions preserves historical tombstones | `01_BUSINESS_RULE_CATALOG.md` | Soft-delete flags (`is_deleted`, `deleted_at`) across domain models |
| `REQ-088` | `OPS-001`: Large dataset queries enforce server pagination, filtering, and sorting | `01_BUSINESS_RULE_CATALOG.md` | Repository query contracts across all domain services |
| `REQ-089` | `OPS-002`: Heavy analytics and progress counters are derived and cached | `01_BUSINESS_RULE_CATALOG.md` | `models/operations.py:220` (`analytics_snapshots`) |
| `REQ-090` | `OPS-003`: Background jobs enforce timeouts, retries, and deduplication leases | `01_BUSINESS_RULE_CATALOG.md` | `models/operations.py:45` (`background_jobs`) |
| `REQ-091` | `OPS-004`: Database restore requires 4-step controlled Admin drill; never auto-overwrites | `01_BUSINESS_RULE_CATALOG.md` | `operations_service.py:restore_database`, `CONFIRM_LIVE_DATABASE_RESTORE` |

### 4.3. Operational Guardrails & Disciplinary Invariants (`AGENTS.md`)

| ID | Invariant Description | Source | Code & Evidence |
|---|---|---|---|
| `REQ-092` | Pure Headless Backend: Zero Jinja HTML templates, zero legacy preview dirs | `AGENTS.md` Sec 1 & 10.1 | All blueprints return JSON envelopes; `src/pwd301/templates` removed |
| `REQ-093` | Anti-Hallucination Contract: Verification commands must be executed live | `AGENTS.md` Sec 7 & 10.2 | Tests verified via live `pytest` run in environment |
| `REQ-094` | Video Upload Limit is strictly `< 1 GB` (replacing historical ~2 GB references) | `AGENTS.md` Sec 4 & 10.3 | `config.py:75` (`MAX_VIDEO_BYTES_EXCLUSIVE = 1_000_000_000`) |
| `REQ-095` | AI Assistant Identity: Strictly named **"Bạch tuộc trợ lí AI"**; anti-reconnaissance | `AGENTS.md` Sec 10.4 | `frontend/index.html:666`, `scope_classifier.py` (CONFIDENTIAL_SYSTEM) |
| `REQ-096` | Authentic Telemetry: CPU, RAM, Disk measured via `psutil` from real physical host | `AGENTS.md` Sec 10.5 | `services/operations_service.py:get_real_system_telemetry` |
| `REQ-097` | Design Philosophy: "Backend complex, Frontend simple"; hide technical UUIDs | `AGENTS.md` Sec 10.6 | Student UI hides raw question UUIDs; Warm Editorial aesthetic |
| `REQ-098` | Idempotent Navigation & Lazy Creation: Routes do not create DB records on visit | `AGENTS.md` Sec 10.7 | `/new` routes only render editor; create triggers only on save/publish |
| `REQ-099` | Clean History Stack: `window.history.replaceState` used when transitioning `/new` to `/edit` | `AGENTS.md` Sec 10.7 | `frontend/assets/js/router.js:navigate(..., replace=true)` |
| `REQ-100` | Admin Sub-role Delegation: 5 specialized sub-roles under `ADMIN_PRIMARY` | `tasks/TASK-070.md` | `models/identity.py:VALID_ADMIN_SUB_ROLES`, `UserRole.assignment_reason` |
| `REQ-101` | Exam Studio 50/50 Split Live-Card Parser (Word docx, Azota, Excel, Moodle) | `tasks/TASK-071.md` | `frontend/assets/js/views/instructor-exams.js`, `import_service.py` |

---

## 5. Frontend Inventory

The frontend is implemented as a high-performance **Single-DOM Single Page Application (SPA)** built with Vanilla JavaScript, Tailwind CSS (via browser CDN), and Google Material Symbols.

| ID | Feature Name | Hash Route | Main Implementation Files | Backend API Dependencies | Role / Scope |
|---|---|---|---|---|---|
| `FE-001` | Auth Form (Login / Register) | `#/auth` | `views/auth.js`, `api.js` | `POST /auth/login`, `POST /auth/register` | Public |
| `FE-002` | User Profile & Settings | `#/student/settings` | `views/student.js`, `api.js` | `GET/PATCH /auth/profile`, `POST /auth/change-password`, `GET/PATCH /auth/preferences` | Authenticated |
| `FE-003` | Role Switcher & Dynamic Navigation | Global Topbar | `router.js`, `ui.js` | `POST /auth/switch-role`, `GET /auth/status` | Authenticated |
| `FE-004` | Notifications Center & Bell | Topbar Popover | `router.js`, `api.js` | `GET /auth/notifications`, `POST /auth/notifications/<id>/read`, `mark-all-read` | Authenticated |
| `FE-005` | Student Learning Dashboard | `#/student/dashboard` | `views/student.js`, `api.js` | `GET /student/dashboard`, `GET /student/recommendations` | Student |
| `FE-006` | Public Course Catalog | `#/student/catalog` | `views/student.js`, `api.js` | `GET /student/courses` | Student / Public |
| `FE-007` | Course Syllabus & Details | `#/student/courses/detail` | `views/student.js`, `api.js` | `GET /student/courses/<id>`, `POST /student/courses/<id>/enroll` | Student |
| `FE-008` | My Learning Workspace | `#/student/courses` | `views/student.js`, `api.js` | `GET /student/my-learning`, `GET /student/enrollments` | Student |
| `FE-009` | Cisco NetAcad 3-Col Console | `#/student/courses/:id` | `views/student.js`, `ui.js` | `GET /student/courses/<id>`, `GET /student/courses/<id>/progress` | Student |
| `FE-010` | Notion-Style Lesson Reader | `#/student/lessons/reader` | `views/student.js`, `ui.js` | `GET /student/courses/<id>/lessons/<id>`, `GET /student/files/<id>/download` | Student |
| `FE-011` | Anti-Seek Video Player Gate | In Lesson Reader | `views/student.js`, `ui.js` | `POST /student/lessons/<id>/progress` | Student |
| `FE-012` | 4-Type Interactive Mini-Quiz | In Lesson Reader | `views/student.js`, `ui.js` | `POST /student/lessons/<id>/quiz-completion` | Student |
| `FE-013` | Smart Waiting Room | `#/student/assessments/waiting-room` | `views/student.js`, `api.js` | `GET /student/assessments/<id>`, `POST /student/assessments/<id>/start` | Student |
| `FE-014` | Anti-Cheat Exam Console | `#/student/assessments/attempt` | `views/student.js`, `ui.js` | `GET /student/attempt/<id>`, `POST/PUT /student/attempt/<id>/answers/<qid>`, `lease/renew`, `takeover`, `focus-events` | Student |
| `FE-015` | Exam Submission & Auto-Grading | In Exam Console | `views/student.js`, `api.js` | `POST /student/attempt/<id>/submit` | Student |
| `FE-016` | Exam Scorecard & Results Review | `#/student/assessments/results` | `views/student.js`, `api.js` | `GET /student/attempt/<id>/result` | Student |
| `FE-017` | Student Attempt Appeal Form | In Results View | `views/student.js`, `api.js` | `POST/GET /student/attempts/<id>/appeal` | Student |
| `FE-018` | Course Certificate & Completion | In Course Console | `views/student.js`, `api.js` | `GET /student/courses/<id>/completion`, `certificate` | Student |
| `FE-019` | Instructor Application Form | `#/student/become-instructor` | `views/student.js`, `api.js` | `GET/POST /student/become-instructor`, `POST /become-instructor/cancel` | Student |
| `FE-020` | Floating Octopus AI Tutor Widget | Global `#floating-ai-container` | `index.html`, `router.js` | `POST /student/ai/chat` | Student |
| `FE-021` | Contextual AI Academic Assistant | `#/student/ai-assistant` | `views/student.js`, `api.js` | `GET /student/ai-assistant`, `POST /student/ai/chat` | Student |
| `FE-022` | Intelligent Recommendations | In Dashboard/Catalog | `views/student.js`, `api.js` | `GET /student/recommendations` | Student |
| `FE-023` | Instructor Dashboard | `#/instructor/dashboard` | `views/instructor.js`, `api.js` | `GET /instructor/dashboard` | Instructor |
| `FE-024` | Instructor Course Management Hub | `#/instructor/courses` | `views/instructor.js`, `api.js` | `GET/POST /instructor/courses` | Instructor |
| `FE-025` | Course Settings & ABET SLO Matrix | `#/instructor/courses/manage` | `views/instructor.js`, `api.js` | `GET /instructor/courses/<id>/manage`, `PATCH /courses/<id>`, `completion-rules` | Instructor |
| `FE-026` | Curriculum & Learning Units Studio | In Course Manage | `views/instructor.js`, `api.js` | `GET/POST /courses/<id>/learning-units`, `PATCH/DELETE /learning-units/<id>`, `reorder` | Instructor |
| `FE-027` | Single-Page Lesson Authoring Studio | `#/instructor/courses/:id/lessons/:id` | `views/instructor.js`, `ui.js` | `POST /courses/<id>/lessons`, `GET/PATCH /lessons/<id>`, `resources`, `check-youtube-link` | Instructor |
| `FE-028` | Instructor Course File Vault | In Course Manage | `views/instructor.js`, `api.js` | `GET/POST /courses/<id>/files`, `POST /files/<id>/trash`, `restore`, `rescan` | Instructor |
| `FE-029` | Prerequisite Governance & Requests | In Course Manage | `views/instructor.js`, `api.js` | `GET/POST/DELETE /courses/<id>/prerequisites`, `prerequisite-requests/review` | Instructor |
| `FE-030` | Exam Studio Hub & Method Selector | `#/instructor/exams/hub` | `views/instructor-exams.js` | `GET /instructor/courses`, `exam-store.js` | Instructor |
| `FE-031` | Exam Studio Word/Azota 50/50 Split | `#/instructor/exams/editor` | `views/instructor-exams.js`, `exam-store.js` | `POST /instructor/exams/parse-file` | Instructor |
| `FE-032` | Exam Studio Interactive Authoring | `#/instructor/exams/interactive` | `views/instructor-exams.js`, `exam-store.js` | Local state binding in `ExamStore` | Instructor |
| `FE-033` | Exam Studio Excel Parser | `#/instructor/exams/excel` | `views/instructor-exams.js`, `exam-store.js` | `GET /exams/excel-template`, `POST /exams/parse-excel` | Instructor |
| `FE-034` | Exam Studio Moodle XML/JSON Parser | `#/instructor/exams/moodle` | `views/instructor-exams.js`, `exam-store.js` | `POST /exams/parse-moodle-xml`, `POST /exams/parse-json` | Instructor |
| `FE-035` | Assessment Matrix (100/N Auto-Split) | `#/instructor/exams/matrix` | `views/instructor-exams.js`, `exam-store.js` | Local calculation + LaTeX picker modal | Instructor |
| `FE-036` | Assessment Settings & Publication | `#/instructor/exams/settings` | `views/instructor-exams.js`, `api.js` | `POST /courses/<id>/assessments`, `POST /assessments/<id>/questions/batch`, `publish` | Instructor |
| `FE-037` | Instructor Submissions & Gradebook | In Exam Hub / Results | `views/instructor.js`, `api.js` | `GET /instructor/assessments/<id>/results`, `GET /attempts/<id>/results` | Instructor |
| `FE-038` | Essay Manual Grading Studio | In Assessment Results | `views/instructor.js`, `api.js` | `GET /attempts/<id>/grading`, `POST /attempts/<id>/grades/<qid>`, `regrade` | Instructor |
| `FE-039` | Admin Governance Cockpit (Tabs) | `#/admin/governance` | `views/admin.js`, `api.js` | `GET /admin/dashboard`, `GET /admin/users` | Admin |
| `FE-040` | Admin Course Review & Diff Inspector | `#/admin/courses/review` | `views/admin.js`, `api.js` | `GET /admin/courses/pending`, `POST /courses/<id>/review`, `change-requests/review` | Admin (Course Review) |
| `FE-041` | Admin Instructor Application Review | In Governance (tab=applications) | `views/admin.js`, `api.js` | `GET /admin/instructor-applications`, `review`, `evidence/<filename>?preview=1` | Admin (Instructor Review) |
| `FE-042` | Admin Faculty Teaching Assignment | In Governance (tab=reassign) | `views/admin.js`, `api.js` | `GET /admin/faculty/workload`, `POST /admin/courses/<id>/reassign` | Admin (Teaching Assign) |
| `FE-043` | Admin User Role & Sub-role Delegation | In Governance (tab=users) | `views/admin.js`, `api.js` | `GET /admin/users`, `POST /admin/users/<id>/roles` | Admin (Primary Admin) |
| `FE-044` | Admin User Suspension & Revocation | In Governance (tab=users) | `views/admin.js`, `api.js` | `POST /admin/users/<id>/suspend`, `unsuspend`, `revoke-sessions` | Admin (Primary Admin) |
| `FE-045` | Admin Physical Host Telemetry | `#/admin/operations` | `views/admin.js`, `api.js` | `GET /admin/telemetry`, `GET /admin/health` | Admin (System Monitor) |
| `FE-046` | Admin Immutable Audit Trail Inspector | In Governance (tab=security) | `views/admin.js`, `api.js` | `GET /admin/audit-logs`, `GET /admin/audit-logs/<id>` | Admin (System Monitor) |
| `FE-047` | Admin 4-Step Live Database Restore | In Operations | `views/admin.js`, `api.js` | `GET/POST /admin/backups`, `verify`, `restore/dry-run`, `restore` | Admin (Primary Admin) |
| `FE-048` | Admin Maintenance Mode Controller | In Operations | `views/admin.js`, `api.js` | `GET /admin/maintenance/status`, `POST /maintenance/start`, `maintenance/end` | Admin (Primary Admin) |
| `FE-049` | Admin Background Jobs & Quarantine | In Operations | `views/admin.js`, `api.js` | `GET /admin/operations/jobs`, `jobs/<id>/retry`, `files/<id>/quarantine-override` | Admin (System Monitor) |
| `FE-050` | Admin Notification Broadcast & Email | In Governance / Operations | `views/admin.js`, `api.js` | `POST /admin/notifications/broadcast`, `POST /admin/emails/retry-failed` | Admin |

---

## 6. Backend API Inventory

The Flask backend exposes 378 routes across 19 blueprints (including `api_auth_unversioned`). Below is the inventory of major functional endpoint groups:

| ID | HTTP Method | Endpoint Pattern | Blueprint / Controller | Service Layer | DB Entities Involved | Authentication & Authz |
|---|---|---|---|---|---|---|
| `API-001` | `POST` | `/auth/login` | `auth.login` | `session_auth_service.py` | `users`, `auth_sessions` | Public (Rate Limited) |
| `API-002` | `POST` | `/auth/register` | `auth.register` | `user_service.py` | `users`, `roles`, `user_roles` | Public (Creates `STUDENT`) |
| `API-003` | `POST` | `/auth/logout` | `auth.logout` | `session_auth_service.py` | `auth_sessions` | Session Authenticated |
| `API-004` | `POST` | `/auth/switch-role` | `auth.switch_role` | `user_service.py` | `users`, `user_roles` | Session Authenticated (Role Check) |
| `API-005` | `GET/PATCH` | `/auth/profile` | `auth.profile` | `user_service.py` | `users` | Session Authenticated |
| `API-006` | `POST` | `/auth/change-password` | `auth.change_password` | `user_service.py` | `users` (`auth_version += 1`) | Session Authenticated |
| `API-007` | `GET/PATCH` | `/auth/preferences` | `auth.preferences` | `notification_service.py` | `notification_preferences` | Session Authenticated |
| `API-008` | `GET` | `/auth/notifications` | `auth.notifications` | `notification_service.py` | `notifications` | Session Authenticated |
| `API-009` | `POST` | `/api/v1/auth/login` | `api_auth.api_login` | `jwt_auth_service.py` | `users`, `jwt_token_grants` | Public (Returns Bearer JWT) |
| `API-010` | `POST` | `/api/v1/auth/refresh` | `api_auth.api_refresh` | `jwt_auth_service.py` | `jwt_token_grants` | Bearer JWT (Refresh Grant) |
| `API-011` | `POST` | `/api/v1/auth/email-change` | `api_auth.api_email_change` | `user_service.py` | `user_security_tokens` | Bearer JWT Authenticated |
| `API-012` | `GET` | `/student/dashboard` | `student.dashboard` | `analytics_service.py` | `enrollments`, `courses`, `assessments` | Session (`STUDENT`) |
| `API-013` | `GET` | `/student/my-learning` | `student.my_learning` | `enrollment_service.py` | `enrollments`, `courses` | Session (`STUDENT`) |
| `API-014` | `GET` | `/student/courses/<id>` | `student.student_course_detail` | `course_service.py` | `courses`, `learning_units`, `lessons` | Session (`STUDENT`) |
| `API-015` | `POST` | `/student/courses/<id>/enroll` | `student.student_enroll_course` | `enrollment_service.py` | `enrollments`, `enrollment_periods` | Session (`STUDENT`, DAG Check) |
| `API-016` | `POST` | `/student/courses/<id>/leave` | `student.student_leave_course` | `enrollment_service.py` | `enrollment_periods` | Session (`STUDENT`, Own Enroll) |
| `API-017` | `POST` | `/student/courses/<id>/re-enroll`| `student.student_re_enroll_course` | `enrollment_service.py` | `enrollment_periods` | Session (`STUDENT`, Retention) |
| `API-018` | `GET` | `/student/courses/<id>/progress` | `student.course_progress` | `completion_service.py` | `lesson_progress`, `courses` | Session (`STUDENT`, Own Progress) |
| `API-019` | `GET` | `/student/courses/<id>/lessons/<id>` | `student.get_student_lesson_route` | `lesson_service.py` | `lessons`, `lesson_resources` | Session (`STUDENT`, Enrolled) |
| `API-020` | `POST` | `/student/lessons/<id>/progress` | `student.record_student_progress_route` | `lesson_service.py` | `lesson_progress` | Session (`STUDENT`, Anti-Seek) |
| `API-021` | `POST` | `/student/lessons/<id>/quiz-completion` | `student.complete_student_lesson_quiz` | `lesson_service.py` | `lesson_progress` | Session (`STUDENT`, 4-Type Mini-Quiz) |
| `API-022` | `POST` | `/student/lessons/<id>/opt-in` | `student.opt_in_student_lesson_revision` | `lesson_service.py` | `lesson_progress` | Session (`STUDENT`) |
| `API-023` | `GET` | `/student/courses/<id>/completion` | `student.get_student_course_completion_route` | `completion_service.py` | `course_completion_summaries` | Session (`STUDENT`) |
| `API-024` | `GET` | `/student/courses/<id>/certificate` | `student.get_student_course_certificate_route` | `completion_service.py` | `course_completion_summaries` | Session (`STUDENT`, Eligible) |
| `API-025` | `GET` | `/student/assessments` | `student.assessments_view` | `assessment_service.py` | `assessments`, `assessment_attempts` | Session (`STUDENT`) |
| `API-026` | `GET` | `/student/assessments/<id>` | `student.assessment_detail_view` | `assessment_service.py` | `assessments`, `assessment_attempts` | Session (`STUDENT`, Waiting Room) |
| `API-027` | `POST` | `/student/assessments/<id>/start` | `student.student_start_assessment` | `attempt_service.py` | `assessment_attempts`, `attempt_questions` | Session (`STUDENT`, Lease Init) |
| `API-028` | `GET` | `/student/attempt/<id>` | `student.attempt_view` | `attempt_service.py` | `assessment_attempts`, `choice_snapshots` | Session (`STUDENT`, Own Attempt) |
| `API-029` | `POST/PUT` | `/student/attempt/<id>/answers/<qid>` | `student.save_student_attempt_answer` | `attempt_service.py` | `attempt_answers`, `answer_events` | Session (`STUDENT`, Lease Token) |
| `API-030` | `POST` | `/student/attempt/<id>/lease/renew` | `student.renew_student_attempt_lease` | `attempt_service.py` | `assessment_attempts` | Session (`STUDENT`, Heartbeat) |
| `API-031` | `POST` | `/student/attempt/<id>/lease/takeover` | `student.takeover_student_attempt_lease` | `attempt_service.py` | `assessment_attempts` | Session (`STUDENT`, Expired Lease) |
| `API-032` | `POST` | `/student/attempt/<id>/focus-events` | `student.record_student_attempt_focus_event` | `attempt_service.py` | `attempt_focus_events` | Session (`STUDENT`, Anti-Cheat) |
| `API-033` | `POST` | `/student/attempt/<id>/submit` | `student.submit_student_attempt` | `attempt_service.py` | `assessment_attempts`, `results` | Session (`STUDENT`, Idempotent) |
| `API-034` | `GET` | `/student/attempt/<id>/result` | `student.attempt_result_view` | `attempt_service.py` | `assessment_results`, `score_policy` | Session (`STUDENT`, Score Release) |
| `API-035` | `POST` | `/student/attempts/<id>/appeal` | `student.submit_attempt_appeal_route` | `attempt_service.py` | `assessment_results` | Session (`STUDENT`, Own Result) |
| `API-036` | `POST` | `/student/ai/chat` | `student.student_ai_chat` | `ai_service.py`, `gemini_service.py` | `ai_conversations`, `ai_messages` | Session (`STUDENT`, Guardrails) |
| `API-037` | `GET` | `/student/recommendations` | `student.student_recommendations` | `recommendation_service.py` | `courses`, `enrollments` | Session (`STUDENT`) |
| `API-038` | `POST` | `/student/become-instructor` | `student.submit_become_instructor` | `user_service.py` | `instructor_applications` | Session (`STUDENT`, File Upload) |
| `API-039` | `GET` | `/student/files/<id>/download` | `student.download_student_course_file_route` | `file_service.py` | `file_assets`, `file_revisions` | Session (`STUDENT`, Clean Only) |
| `API-040` | `GET` | `/instructor/dashboard` | `instructor.dashboard` | `analytics_service.py` | `courses`, `assessments`, `results` | Session (`INSTRUCTOR`) |
| `API-041` | `GET/POST` | `/instructor/courses` | `instructor.instructor_courses_route` | `course_service.py` | `courses` | Session (`INSTRUCTOR`) |
| `API-042` | `GET` | `/instructor/courses/<id>/manage`| `instructor.manage_course_hub` | `course_service.py` | `courses`, `learning_units` | Session (`INSTRUCTOR`, Course Owner)|
| `API-043` | `PATCH` | `/instructor/courses/<id>` | `instructor.update_course_route` | `course_service.py` | `courses` | Session (`INSTRUCTOR`, Owner) |
| `API-044` | `POST` | `/instructor/courses/<id>/submit` | `instructor.submit_course_route` | `course_service.py` | `courses`, `course_change_requests` | Session (`INSTRUCTOR`, Owner) |
| `API-045` | `POST` | `/instructor/courses/<id>/publish`| `instructor.publish_course_route` | `course_service.py` | `courses` | Session (`INSTRUCTOR` or `ADMIN`) |
| `API-046` | `POST` | `/instructor/courses/<id>/trash` | `instructor.trash_course_route` | `course_service.py` | `courses` (`is_deleted = 1`) | Session (`INSTRUCTOR`, Owner) |
| `API-047` | `GET/POST` | `/instructor/courses/<id>/learning-units` | `instructor.learning_units_route` | `course_service.py` | `learning_units` | Session (`INSTRUCTOR`, Owner) |
| `API-048` | `PATCH/DELETE` | `/instructor/learning-units/<id>` | `instructor.update/delete_learning_unit_route` | `course_service.py` | `learning_units` | Session (`INSTRUCTOR`, Owner) |
| `API-049` | `POST` | `/instructor/courses/<id>/learning-units/reorder` | `instructor.reorder_learning_units_route` | `course_service.py` | `learning_units` | Session (`INSTRUCTOR`, Owner) |
| `API-050` | `POST` | `/instructor/courses/<id>/lessons`| `instructor.create_lesson_route` | `lesson_service.py` | `lessons` | Session (`INSTRUCTOR`, Owner) |
| `API-051` | `GET` | `/instructor/lessons/<id>` | `instructor.get_lesson_route` | `lesson_service.py` | `lessons`, `lesson_resources` | Session (`INSTRUCTOR`, Owner) |
| `API-052` | `PATCH/PUT` | `/instructor/lessons/<id>` | `instructor.update_lesson_route` | `lesson_service.py` | `lessons` | Session (`INSTRUCTOR`, Owner) |
| `API-053` | `POST` | `/instructor/lessons/<id>/draft/discard` | `instructor.discard_lesson_draft_route` | `lesson_service.py` | `lessons` | Session (`INSTRUCTOR`, Owner) |
| `API-054` | `POST` | `/instructor/courses/<id>/lessons/reorder` | `instructor.reorder_lessons_route` | `lesson_service.py` | `lessons` | Session (`INSTRUCTOR`, Owner) |
| `API-055` | `POST` | `/instructor/courses/<id>/lessons/<id>/resources` | `instructor.attach_lesson_resource_route` | `file_service.py` | `lesson_resources`, `file_assets` | Session (`INSTRUCTOR`, Owner) |
| `API-056` | `POST` | `/instructor/check-youtube-link` | `instructor.check_youtube_link_route` | `youtube_validator_service.py` | — (External oEmbed / URL check) | Session (`INSTRUCTOR`) |
| `API-057` | `GET/POST` | `/instructor/courses/<id>/prerequisites` | `instructor.prerequisites_route` | `course_service.py` | `course_prerequisites` | Session (`INSTRUCTOR`, DAG Check) |
| `API-058` | `GET/PUT` | `/instructor/courses/<id>/completion-rules` | `instructor.completion_rules_route` | `completion_service.py` | `course_completion_rules` | Session (`INSTRUCTOR`, Owner) |
| `API-059` | `GET/POST` | `/instructor/courses/<id>/assessments` | `instructor.course_assessments_route` | `assessment_service.py` | `assessments` | Session (`INSTRUCTOR`, Owner) |
| `API-060` | `GET/PATCH` | `/instructor/assessments/<id>` | `instructor.assessment_detail_route` | `assessment_service.py` | `assessments` | Session (`INSTRUCTOR`, Owner) |
| `API-061` | `POST` | `/instructor/assessments/<id>/publish` | `instructor.publish_assessment_route` | `assessment_service.py` | `assessments` (Structure Locked) | Session (`INSTRUCTOR`, Owner) |
| `API-062` | `POST` | `/instructor/assessments/<id>/questions/batch` | `instructor.batch_create_questions_route` | `assessment_service.py` | `assessment_question_assignments` | Session (`INSTRUCTOR`, Owner) |
| `API-063` | `POST` | `/instructor/exams/parse-file` | `instructor.instructor_parse_exam_file_route` | `import_service.py` | `document_import_jobs` (Word Docx) | Session (`INSTRUCTOR`, 50/50 View)|
| `API-064` | `POST` | `/instructor/exams/parse-excel` | `instructor.instructor_parse_excel_exam_route` | `excel_exam_service.py` | OpenPyXL parsing | Session (`INSTRUCTOR`) |
| `API-065` | `POST` | `/instructor/exams/parse-moodle-xml` | `instructor.instructor_parse_moodle_xml_route` | `moodle_exam_service.py` | DefusedXML parsing | Session (`INSTRUCTOR`) |
| `API-066` | `POST` | `/instructor/exams/parse-json` | `instructor.instructor_parse_exam_json_route` | `moodle_exam_service.py` | JSON validation | Session (`INSTRUCTOR`) |
| `API-067` | `GET` | `/instructor/assessments/<id>/results` | `instructor.assessment_results_route` | `attempt_service.py` | `assessment_results` | Session (`INSTRUCTOR`, Owner) |
| `API-068` | `GET` | `/instructor/attempts/<id>/grading` | `instructor.get_attempt_grading_route` | `attempt_service.py` | `attempt_question_grades` | Session (`INSTRUCTOR`, Owner) |
| `API-069` | `POST` | `/instructor/attempts/<id>/grades/<qid>` | `instructor.grade_attempt_question_route` | `attempt_service.py` | `attempt_question_grades` | Session (`INSTRUCTOR`, Owner) |
| `API-070` | `POST` | `/instructor/assessments/<id>/regrade` | `instructor.trigger_assessment_regrade_route`| `regrade_worker.py` | `regrade_jobs`, `regrade_items` | Session (`INSTRUCTOR`, Owner) |
| `API-071` | `GET` | `/admin/dashboard` | `admin.dashboard` | `analytics_service.py` | `users`, `courses`, `audit_events` | Session (`ADMIN`) |
| `API-072` | `GET` | `/admin/users` | `admin.admin_list_users` | `user_service.py` | `users`, `user_roles` | Session (`ADMIN`) |
| `API-073` | `POST` | `/admin/users/<id>/roles` | `admin.admin_manage_user_roles` | `user_service.py` | `user_roles` (Sub-role format) | Session (`ADMIN_PRIMARY` only) |
| `API-074` | `POST` | `/admin/users/<id>/suspend` | `admin.admin_suspend_user` | `user_service.py` | `users`, `auth_sessions` (Revoked) | Session (`ADMIN_PRIMARY`, Reauth)|
| `API-075` | `POST` | `/admin/users/<id>/unsuspend` | `admin.admin_unsuspend_user` | `user_service.py` | `users` (`is_active = 1`) | Session (`ADMIN_PRIMARY`) |
| `API-076` | `POST` | `/admin/users/<id>/revoke-sessions` | `admin.admin_revoke_user_sessions` | `session_auth_service.py` | `auth_sessions`, `users.auth_version`| Session (`ADMIN_PRIMARY`, Reauth)|
| `API-077` | `GET` | `/admin/courses/pending` | `admin.admin_list_pending_courses` | `course_service.py` | `courses` (`PENDING_REVIEW`) | Session (`ADMIN_COURSE_REVIEW`) |
| `API-078` | `POST` | `/admin/courses/<id>/review` | `admin.admin_review_course` | `course_service.py` | `courses`, `audit_events` | Session (`ADMIN_COURSE_REVIEW`) |
| `API-079` | `GET` | `/admin/change-requests` | `admin.admin_list_change_requests` | `course_service.py` | `course_change_requests` | Session (`ADMIN_COURSE_REVIEW`) |
| `API-080` | `POST` | `/admin/change-requests/<id>/review` | `admin.admin_review_change_request` | `course_service.py` | `course_change_requests`, `courses` | Session (`ADMIN_COURSE_REVIEW`) |
| `API-081` | `POST` | `/admin/courses/<id>/reassign` | `admin.admin_reassign_course_instructor` | `course_service.py` | `courses.owner_instructor_id` | Session (`ADMIN_TEACHING_ASSIGN`)|
| `API-082` | `GET` | `/admin/faculty/workload` | `admin.admin_get_faculty_workload` | `course_service.py` | `courses`, `user_roles` | Session (`ADMIN_TEACHING_ASSIGN`)|
| `API-083` | `GET` | `/admin/instructor-applications` | `admin.admin_list_instructor_applications` | `user_service.py` | `instructor_applications` | Session (`ADMIN_INSTRUCTOR_REV`) |
| `API-084` | `POST` | `/admin/instructor-applications/<id>/review`| `admin.admin_review_instructor_application` | `user_service.py` | `instructor_applications`, `roles` | Session (`ADMIN_INSTRUCTOR_REV`) |
| `API-085` | `GET` | `/admin/instructor-applications/<id>/evidence/<f>`| `admin.admin_download_application_evidence`| `file_service.py` | Physical storage (inline preview) | Session (`ADMIN_INSTRUCTOR_REV`) |
| `API-086` | `GET` | `/admin/telemetry` | `admin.admin_telemetry` | `operations_service.py` | `psutil` Real Host Hardware | Session (`ADMIN_SYSTEM_MONITOR`) |
| `API-087` | `GET` | `/admin/audit-logs` | `admin.admin_list_audit_logs` | `audit_service.py` | `audit_events` (SHA-256 Chain) | Session (`ADMIN_SYSTEM_MONITOR`) |
| `API-088` | `GET/POST` | `/admin/backups` | `admin.admin_backups` | `operations_service.py` | `backup_runs` | Session (`ADMIN_PRIMARY`) |
| `API-089` | `POST` | `/admin/backups/<id>/verify` | `admin.admin_verify_backup` | `operations_service.py` | `backup_runs` (Checksum verify) | Session (`ADMIN_PRIMARY`) |
| `API-090` | `POST` | `/admin/backups/<id>/restore/dry-run` | `admin.admin_restore_dry_run` | `operations_service.py` | Schema & size validation | Session (`ADMIN_PRIMARY`) |
| `API-091` | `POST` | `/admin/backups/<id>/restore` | `admin.admin_restore_database` | `operations_service.py` | Live DB overwrite (4-Step Guard) | Session (`ADMIN_PRIMARY`, Phrase)|
| `API-092` | `GET` | `/admin/maintenance/status` | `admin.admin_maintenance_status` | `operations_service.py` | `system_health_snapshots` | Session (`ADMIN`) |
| `API-093` | `POST` | `/admin/maintenance/start` | `admin.admin_start_maintenance` | `operations_service.py` | In-memory cache + DB window | Session (`ADMIN_PRIMARY`, Reauth)|
| `API-094` | `POST` | `/admin/maintenance/end` | `admin.admin_end_maintenance` | `operations_service.py` | In-memory cache + DB window | Session (`ADMIN_PRIMARY`) |
| `API-095` | `GET` | `/health` / `/health/deep` | `core.health_check` / `deep_health_check` | `operations_service.py` | MS SQL, ClamAV, Disk Probes | Public Health Check |

---

## 7. Database Inventory

The platform is persisted across **73 normalized relational tables** in Microsoft SQL Server 2022. All tables follow strict enterprise constraints:
- **Internal Primary Key:** `BIGINT IDENTITY(1,1)` for ultra-fast B-tree clustering and joins.
- **External Public ID:** RFC 4122 `UNIQUEIDENTIFIER` (`public_id`) default `NEWSEQUENTIALID()` for safe client exposure without ID enumeration.
- **Concurrency Control:** `ROWVERSION` (`row_version`) column on mutable entities for Optimistic Concurrency Control (OCC).
- **Time Representation:** `DATETIME2(3)` in Coordinated Universal Time (UTC) default `SYSUTCDATETIME()`.
- **Integrity Semantics:** `NO ACTION` default on Foreign Keys to prevent accidental cascading data loss of historical learning or grading records.

| Entity ID | Table Name | SQLAlchemy Model | Domain Module | Primary Purpose & Key Fields |
|---|---|---|---|---|
| `DB-001` | `users` | `User` | `identity.py` | Account credentials (`email_normalized`, `password_hash`, `auth_version`, `is_active`) |
| `DB-002` | `roles` | `Role` | `identity.py` | Core role definitions (`STUDENT`, `INSTRUCTOR`, `ADMIN`) |
| `DB-003` | `user_roles` | `UserRole` | `identity.py` | Role memberships with sub-role encoding in `assignment_reason` |
| `DB-004` | `auth_sessions` | `AuthSession` | `identity.py` | Web session state tracking (`session_token_hash`, `user_agent_hash`, `is_revoked`) |
| `DB-005` | `jwt_token_grants` | `JwtTokenGrant` | `identity.py` | REST API JWT grants (`grant_id`, `refresh_token_hash`, `expires_at`) |
| `DB-006` | `user_security_tokens` | `UserSecurityToken` | `identity.py` | Email verification & password reset tokens (`token_hash`, `purpose`, `consumed_at`) |
| `DB-007` | `instructor_applications` | `InstructorApplication` | `identity.py` | Instructor candidate applications (`status`, `evidence_files`, `reviewed_by`) |
| `DB-008` | `security_events` | `SecurityEvent` | `identity.py` | High-priority security audit logging (`event_type`, `severity`, `ip_address`) |
| `DB-009` | `courses` | `Course` | `course.py` | Course catalog (`course_code_normalized`, `title_normalized`, `status`, `owner_instructor_id`) |
| `DB-010` | `course_prerequisites` | `CoursePrerequisite` | `course.py` | Directed acyclic graph prerequisite links (`course_id`, `prerequisite_course_id`) |
| `DB-011` | `course_completion_rules`| `CourseCompletionRule` | `course.py` | Requirements for passing a course (`min_progress_percent`, `min_grade_score`) |
| `DB-012` | `course_change_requests` | `CourseChangeRequest` | `course.py` | Staging approval queue for course/lesson updates post-publish |
| `DB-013` | `learning_units` | `LearningUnit` | `course.py` | Hierarchical course sections/modules (`course_id`, `title`, `position`) |
| `DB-014` | `lessons` | `Lesson` | `course.py` | Lesson content (`unit_id`, `title`, `video_url`, `content_markdown`, `is_published`) |
| `DB-015` | `enrollments` | `Enrollment` | `course.py` | Unique logical user enrollment per course (`student_id`, `course_id`) |
| `DB-016` | `enrollment_periods` | `EnrollmentPeriod` | `course.py` | Discrete learning attempt window (`enrollment_id`, `started_at`, `status`) |
| `DB-017` | `enrollment_events` | `EnrollmentEvent` | `course.py` | Immutable lifecycle events (`ENROLLED`, `PAUSED`, `LEFT`, `COMPLETED`) |
| `DB-018` | `lesson_progress` | `LessonProgress` | `course.py` | Student lesson tracking (`seconds_spent`, `fraction_viewed`, `completed_at`) |
| `DB-019` | `course_completion_summaries` | `CourseCompletionSummary` | `course.py` | Final course grades and certificate metadata (`final_grade`, `completed_at`) |
| `DB-020` | `questions` | `Question` | `question_bank.py` | Canonical question root entity (`course_id`, `question_type`, `is_deleted`) |
| `DB-021` | `question_revisions` | `QuestionRevision` | `question_bank.py` | Immutable question versions (`question_id`, `revision_no`, `prompt_markdown`) |
| `DB-022` | `question_revision_choices` | `QuestionRevisionChoice` | `question_bank.py` | Multiple-choice options per revision (`choice_key`, `content`, `is_correct`) |
| `DB-023` | `question_revision_accepted_answers` | `QuestionRevisionAcceptedAnswer` | `question_bank.py` | Normalized string keys for short answer grading |
| `DB-024` | `question_provenances` | `QuestionProvenance` | `question_bank.py` | Origin trace (author, import job ID, AI prompt session ID) |
| `DB-025` | `assessments` | `Assessment` | `assessment.py` | Exam definition (`course_id`, `title`, `duration_minutes`, `max_attempts`, `is_published`) |
| `DB-026` | `assessment_sections` | `AssessmentSection` | `assessment.py` | Sub-sections/parts within an exam (`assessment_id`, `title`, `position`) |
| `DB-027` | `assessment_question_assignments` | `AssessmentQuestionAssignment` | `assessment.py` | Static question bindings (`assessment_id`, `question_id`, `assigned_points`) |
| `DB-028` | `assessment_blueprints` | `AssessmentBlueprint` | `assessment.py` | Dynamic exam rules (`assessment_id`, `total_points`, `selection_mode`) |
| `DB-029` | `assessment_blueprint_rules` | `AssessmentBlueprintRule` | `assessment.py` | Filtering logic for dynamic pool sampling (`topic_tag`, `difficulty`, `count`) |
| `DB-030` | `assessment_question_pools` | `AssessmentQuestionPool` | `assessment.py` | Eligible questions pool for blueprint sampling |
| `DB-031` | `assessment_attempts` | `AssessmentAttempt` | `attempt_regrade.py` | Student exam session (`student_id`, `assessment_id`, `lease_token`, `deadline_at`) |
| `DB-032` | `attempt_focus_events` | `AttemptFocusEvent` | `attempt_regrade.py` | Anti-cheat tracking (`attempt_id`, `event_type`, `blur_count`, `fullscreen_lost`) |
| `DB-033` | `attempt_questions` | `AttemptQuestion` | `attempt_regrade.py` | Frozen question snapshot assigned to attempt (`display_position`, `assigned_points`) |
| `DB-034` | `attempt_choice_snapshots` | `AttemptChoiceSnapshot` | `attempt_regrade.py` | Frozen choices shuffled order presented to student |
| `DB-035` | `attempt_answers` | `AttemptAnswer` | `attempt_regrade.py` | Current student answer state (`selected_choice_keys`, `text_answer`, `updated_at`) |
| `DB-036` | `attempt_answer_choices` | `AttemptAnswerChoice` | `attempt_regrade.py` | Normalized choice mapping for multi-choice response verification |
| `DB-037` | `attempt_answer_events` | `AttemptAnswerEvent` | `attempt_regrade.py` | Immutable autosave event log (`client_seq`, `delta_payload`, `received_at`) |
| `DB-038` | `attempt_question_grades` | `AttemptQuestionGrade` | `attempt_regrade.py` | Objective / manual score per question (`awarded_points`, `is_correct`, `feedback`) |
| `DB-039` | `attempt_question_grade_histories` | `AttemptQuestionGradeHistory` | `attempt_regrade.py` | Audit log of regrading and essay corrections |
| `DB-040` | `assessment_results` | `AssessmentResult` | `attempt_regrade.py` | Final attempt grade calculation (`total_score`, `percentage`, `passed`, `appeal_status`) |
| `DB-041` | `assessment_result_histories` | `AssessmentResultHistory` | `attempt_regrade.py` | History of score adjustments following regrade runs |
| `DB-042` | `question_corrections` | `QuestionCorrection` | `attempt_regrade.py` | Flawed question correction ledger triggering automatic regrade |
| `DB-043` | `regrade_jobs` | `RegradeJob` | `attempt_regrade.py` | Background regrading batch task (`assessment_id`, `status`, `progress_percent`) |
| `DB-044` | `regrade_items` | `RegradeItem` | `attempt_regrade.py` | Individual attempt task item within a regrade job |
| `DB-045` | `file_blobs` | `FileBlob` | `file_import.py` | Physical deduplicated storage blobs (`sha256`, `byte_size`, `storage_path`) |
| `DB-046` | `file_assets` | `FileAsset` | `file_import.py` | Logical asset handle (`course_id`, `original_filename`, `is_deleted`) |
| `DB-047` | `file_revisions` | `FileRevision` | `file_import.py` | Scanned revisions of an asset (`scan_status`, `clamav_signature`, `is_active`) |
| `DB-048` | `file_scan_results` | `FileScanResult` | `file_import.py` | Historical ClamAV scan audit records (`engine_version`, `result`, `scanned_at`) |
| `DB-049` | `lesson_resources` | `LessonResource` | `file_import.py` | File attachments bound to lessons (`lesson_id`, `asset_id`, `position`) |
| `DB-050` | `question_revision_resources` | `QuestionRevisionResource` | `file_import.py` | Media assets attached to question revisions |
| `DB-051` | `document_import_jobs` | `DocumentImportJob` | `file_import.py` | File parser session (`import_type`, `file_asset_id`, `status`, `confidence_score`) |
| `DB-052` | `import_questions` | `ImportQuestion` | `file_import.py` | Draft questions parsed from Word/Excel/Moodle before confirmation |
| `DB-053` | `import_duplicate_candidates` | `ImportDuplicateCandidate` | `file_import.py` | Duplicate question candidates flagged for instructor review |
| `DB-054` | `import_question_resources` | `ImportQuestionResource` | `file_import.py` | Embedded media extracted from parsed exam files |
| `DB-055` | `ai_conversations` | `AIConversation` | `ai_rag.py` | AI chat session header (`user_id`, `course_id`, `expires_at`, `is_active`) |
| `DB-056` | `ai_messages` | `AIMessage` | `ai_rag.py` | Individual chat turns (`role`, `content`, `tokens_used`, `created_at`) |
| `DB-057` | `ai_requests` | `AIRequest` | `ai_rag.py` | Telemetry & quota ledger for Gemini calls (`model_name`, `latency_ms`, `status`) |
| `DB-058` | `ai_generated_question_drafts`| `AIGeneratedQuestionDraft` | `ai_rag.py` | AI-assisted question drafts pending approval |
| `DB-059` | `knowledge_documents` | `KnowledgeDocument` | `ai_rag.py` | RAG indexed document handles (`source_type`, `source_id`, `is_archived`) |
| `DB-060` | `knowledge_versions` | `KnowledgeVersion` | `ai_rag.py` | Versioned content snapshots ingested into vector/chunk store |
| `DB-061` | `knowledge_chunks` | `KnowledgeChunk` | `ai_rag.py` | Semantically bounded text segments with token boundaries |
| `DB-062` | `ai_source_usages` | `AISourceUsage` | `ai_rag.py` | Provenance citations linking AI answer turns to specific chunk IDs |
| `DB-063` | `notification_events` | `NotificationEvent` | `notification_audit.py` | System-wide event notifications (`event_type`, `payload_json`, `created_at`) |
| `DB-064` | `notifications` | `Notification` | `notification_audit.py` | User-targeted notifications (`recipient_user_id`, `is_read`, `action_url`) |
| `DB-065` | `notification_preferences` | `NotificationPreference` | `notification_audit.py` | User channel opt-in/opt-out settings |
| `DB-066` | `email_deliveries` | `EmailDelivery` | `notification_audit.py` | Asynchronous email outbox queue (`recipient_email`, `status`, `retry_count`) |
| `DB-067` | `audit_events` | `AuditEvent` | `notification_audit.py` | Cryptographically chained audit log (`action`, `actor_id`, `sha256_hash`, `prev_hash`) |
| `DB-068` | `background_jobs` | `BackgroundJob` | `operations.py` | Asynchronous task queue (`job_type`, `payload_json`, `status`, `leased_until`) |
| `DB-069` | `system_alerts` | `SystemAlert` | `operations.py` | System-level health and failure warnings (`alert_type`, `message`, `resolved_at`) |
| `DB-070` | `backup_runs` | `BackupRun` | `operations.py` | Database backup metadata (`backup_type`, `file_path`, `checksum_sha256`, `verified`) |
| `DB-071` | `grade_exports` | `GradeExport` | `operations.py` | Asynchronous CSV/Excel gradebook export tracking |
| `DB-072` | `analytics_snapshots` | `AnalyticsSnapshot` | `operations.py` | Pre-calculated course, student, and system performance metrics |
| `DB-073` | `system_health_snapshots` | `SystemHealthSnapshot` | `operations.py` | Physical CPU, RAM, disk, and database latency telemetry logs |

---

## 8. Authentication Architecture

PWD301 implements a **Dual-Mode Authentication Architecture** (governed by `ADR-001`):

```
┌────────────────────────────────────────────────────────────────────────┐
│                        AUTHENTICATION GATEWAY                          │
├──────────────────────────────────┬─────────────────────────────────────┤
│      WEB SPA / BROWSER CLIENT    │       REST API / EXTERNAL CLIENT    │
├──────────────────────────────────┼─────────────────────────────────────┤
│  • Flask Session Cookie          │  • RFC 6750 Bearer JWT              │
│  • HttpOnly, SameSite=Lax        │  • Header: Authorization            │
│  • Double-Submit CSRF Token      │  • Signed with HS256 secret         │
│  • In-Memory `auth_version` sync │  • Short-lived access token (15m)   │
│  • Handled by Flask-Login        │  • `jwt_token_grants` in DB         │
│  • Target: `/auth/*`, `/student/*`│  • Target: `/api/*` (CSRF Exempt)   │
└──────────────────────────────────┴─────────────────────────────────────┘
```

### Security & Lifecycle Mechanisms
1. **Login & Identifier Normalization:**
   - Email is the sole login identifier, normalized via `LOWER(LTRIM(RTRIM(email)))`.
   - Password hashing uses Werkzeug `scrypt` / `pbkdf2:sha256` with strong salt.
2. **Session Revocation & Auth Versioning:**
   - Every user possesses an integer `auth_version` in `users`.
   - When a user changes their password, or an Admin triggers **Suspend** or **Revoke Sessions**, `auth_version` is atomically incremented.
   - Any session cookie or JWT holding an obsolete `auth_version` is immediately rejected (HTTP 401).
3. **CSRF Protection:**
   - All state-changing Web session requests (`POST`, `PUT`, `PATCH`, `DELETE`) require header `X-CSRFToken` matching cookie `csrf_token`.
   - `frontend/assets/js/api.js` provides automatic CSRF token fetching and retry handling on HTTP 400 CSRF mismatches.

### Role × Permission Matrix

The platform supports 3 primary roles (`STUDENT`, `INSTRUCTOR`, `ADMIN`) and 5 specialized Admin sub-roles:

| Capability / Resource Action | Public | STUDENT | INSTRUCTOR | ADMIN_PRIMARY | ADMIN_COURSE_REVIEW | ADMIN_INSTRUCTOR_REV | ADMIN_TEACHING_ASSIGN | ADMIN_SYSTEM_MONITOR |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| View Public Catalog & Courses | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Enroll in Courses (DAG Checked) | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Learn Lessons & Play Anti-Seek | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Take Exams & Submit Answers | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Access Octopus AI Assistant | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Apply to Become Instructor | ❌ | ✅ | — | — | — | — | — | — |
| Create / Edit Owned Courses | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Author Lessons & Attached Media | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Author Exams (Word/Azota/Excel) | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Grade Student Submissions | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Trigger Idempotent Regrade | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Review New Courses & Change Reqs| ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Review Instructor Applications | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ |
| Reassign Course Instructors | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ | ❌ |
| Inspect Host Hardware Telemetry | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| View Cryptographic Audit Trail | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| Suspend Users & Delegate Roles | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Execute Live DB Restore (4-step)| ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Toggle Maintenance Mode | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |

---

## 9. Authorization Architecture

Authorization is enforced at both the **Route level (RBAC)** and **Resource / Object level (IDOR Defense)** via `src/pwd301/services/authorization_service.py`:

### 1. Unified Actor Context Resolution
`get_authenticated_actor()` resolves the active caller:
- Priority 1: Bearer token from `Authorization: Bearer <JWT>` header (validated fail-closed).
- Priority 2: Web session cookie via Flask-Login `current_user`.
- Priority 3: Fails closed to `None` if unauthenticated.
- **CSRF Isolation Boundary:** Web session cookies are strictly forbidden from authenticating `/api/*` endpoints (except safe `GET /api/files/.../download`).

### 2. Route Decorators
- `@require_roles(*roles)`: Enforces role hierarchy (`ADMIN` > `INSTRUCTOR` > `STUDENT`).
- `@admin_required`: Restricts route to users with role `ADMIN`.
- `@instructor_required`: Restricts route to users with role `INSTRUCTOR` or `ADMIN`.

### 3. Object-Level Access Control (IDOR Prevention)
- `can_manage_course(actor, course)`: Instructors can only modify courses where `course.owner_instructor_id == actor.id`. Admins with course management scope can manage all courses.
- `can_access_attempt(actor, attempt)`: Students can only view and mutate their own `assessment_attempts`. Instructors can inspect attempts for courses they own.
- `can_view_assessment_results(actor, attempt)`: Checks `score_release_policy` (`IMMEDIATE`, `AFTER_CLOSE`, `MANUAL`) before showing points to students.
- `can_download_file(actor, asset)`: Verifies student enrollment in the course owning the file, and guarantees file status is `CLEAN` / `ACTIVE` before streaming bytes.

---

## 10. Frontend → Backend Mapping

| Frontend View / Action | `ApiClient` Method | HTTP & Request URL | Backend Route Endpoint | Service Layer Method |
|---|---|---|---|---|
| User Login | `ApiClient.login` | `POST /auth/login` | `auth.login` | `session_auth_service.py:create_auth_session` |
| User Register | `ApiClient.register` | `POST /auth/register` | `auth.register` | `user_service.py:register_user` |
| Switch Active Role | `ApiClient.switchRole` | `POST /auth/switch-role` | `auth.switch_role` | `user_service.py` (`session['active_role']`) |
| Fetch Dashboard | `ApiClient.getStudentDashboard` | `GET /student/dashboard` | `student.dashboard` | `analytics_service.py:get_student_learning_overview` |
| Browse Catalog | `ApiClient.getCatalogCourses` | `GET /student/courses` | `student.student_course_detail` | `course_service.py:list_published_courses` |
| Enroll in Course | `ApiClient.enrollCourse` | `POST /student/courses/<id>/enroll` | `student.student_enroll_course` | `enrollment_service.py:enroll_student` |
| Read Lesson Content | `ApiClient.getStudentLesson` | `GET /student/courses/<cId>/lessons/<lId>` | `student.get_student_lesson_route` | `lesson_service.py:get_lesson_for_student` |
| Heartbeat Video Progress | `ApiClient.recordLessonProgress` | `POST /student/lessons/<id>/progress` | `student.record_student_progress_route` | `lesson_service.py:record_progress` |
| Submit Mini-Quiz | `ApiClient.completeLessonMiniQuiz` | `POST /student/lessons/<id>/quiz-completion` | `student.complete_student_lesson_quiz` | `lesson_service.py:verify_and_grade_mini_quiz` |
| Enter Exam Waiting Room | `ApiClient.getStudentAssessmentDetail` | `GET /student/assessments/<id>` | `student.assessment_detail_view` | `assessment_service.py:get_assessment_waiting_room_info`|
| Start Exam Attempt | `ApiClient.startAssessmentAttempt` | `POST /student/assessments/<id>/start` | `student.student_start_assessment` | `attempt_service.py:start_attempt` |
| Autosave Exam Answer | `ApiClient.saveAttemptAnswer` | `POST /student/attempt/<id>/answers/<qid>` | `student.save_student_attempt_answer` | `attempt_service.py:save_answer` |
| Renew Tab Lease | `ApiClient.request` | `POST /student/attempt/<id>/lease/renew` | `student.renew_student_attempt_lease` | `attempt_service.py:renew_lease` |
| Takeover Stale Lease | `ApiClient.request` | `POST /student/attempt/<id>/lease/takeover` | `student.takeover_student_attempt_lease` | `attempt_service.py:takeover_lease` |
| Submit Exam Attempt | `ApiClient.submitAttempt` | `POST /student/attempt/<id>/submit` | `student.submit_student_attempt` | `attempt_service.py:submit_attempt` |
| View Exam Scorecard | `ApiClient.getAttemptResult` | `GET /student/attempt/<id>/result` | `student.attempt_result_view` | `attempt_service.py:get_attempt_result` |
| Ask Octopus AI | `ApiClient.sendAIChat` | `POST /student/ai/chat` | `student.student_ai_chat` | `ai_service.py:process_student_query` |
| Course Recommendations | `ApiClient.getRecommendations` | `GET /student/recommendations` | `student.student_recommendations` | `recommendation_service.py:get_recommendations` |
| Instructor Dashboard | `ApiClient.getInstructorDashboard` | `GET /instructor/dashboard` | `instructor.dashboard` | `analytics_service.py:get_instructor_dashboard_metrics`|
| Create Course | `ApiClient.createCourse` | `POST /instructor/courses` | `instructor.create_course_route` | `course_service.py:create_course` |
| Update Course SLOs | `ApiClient.updateCourse` | `PATCH /instructor/courses/<id>` | `instructor.update_course_route` | `course_service.py:update_course` |
| Create Learning Unit | `ApiClient.createLearningUnit` | `POST /instructor/courses/<id>/learning-units`| `instructor.learning_units_route` | `course_service.py:create_learning_unit` |
| Save Lesson Content | `ApiClient.updateLesson` | `PATCH /instructor/lessons/<id>` | `instructor.update_lesson_route` | `lesson_service.py:update_lesson` |
| Check YouTube URL | `ApiClient.checkYouTubeLink` | `POST /instructor/check-youtube-link` | `instructor.check_youtube_link_route` | `youtube_validator_service.py:validate_youtube_url` |
| Parse Word Exam Docx | `ApiClient.parseExamFile` | `POST /instructor/exams/parse-file` | `instructor.instructor_parse_exam_file_route` | `import_service.py:parse_word_docx_exam` |
| Parse Excel Exam | `ApiClient.parseExcelExam` | `POST /instructor/exams/parse-excel` | `instructor.instructor_parse_excel_exam_route` | `excel_exam_service.py:parse_excel_exam` |
| Parse Moodle XML | `ApiClient.parseMoodleXml` | `POST /instructor/exams/parse-moodle-xml` | `instructor.instructor_parse_moodle_xml_route` | `moodle_exam_service.py:parse_moodle_xml` |
| Create Exam from Wizard | `ApiClient.createAssessment` | `POST /instructor/courses/<id>/assessments` | `instructor.create_assessment_route` | `assessment_service.py:create_assessment` |
| Batch Create Questions | `ApiClient.createAssessmentQuestionsBatch`| `POST /instructor/assessments/<id>/questions/batch`| `instructor.batch_create_questions_route` | `assessment_service.py:batch_assign_questions` |
| Publish Assessment | `ApiClient.publishAssessment` | `POST /instructor/assessments/<id>/publish` | `instructor.publish_assessment_route` | `assessment_service.py:publish_assessment` |
| Manual Essay Grading | `ApiClient.request` | `POST /instructor/attempts/<id>/grades/<qid>` | `instructor.grade_attempt_question_route` | `attempt_service.py:grade_manual_question` |
| Admin Review Course | `ApiClient.reviewCourse` | `POST /admin/courses/<id>/review` | `admin.admin_review_course` | `course_service.py:review_course` |
| Admin Review Change Req | `ApiClient.reviewAdminChangeRequest` | `POST /admin/change-requests/<id>/review` | `admin.admin_review_change_request` | `course_service.py:review_change_request` |
| Admin Review Candidate | `ApiClient.reviewInstructorApplication` | `POST /admin/instructor-applications/<id>/review` | `admin.admin_review_instructor_application` | `user_service.py:review_instructor_application` |
| Admin Reassign Course | `ApiClient.reassignCourse` | `POST /admin/courses/<id>/reassign` | `admin.admin_reassign_course_instructor` | `course_service.py:reassign_course_owner` |
| Admin Delegate Roles | `ApiClient.assignRole` | `POST /admin/users/<id>/roles` | `admin.admin_manage_user_roles` | `user_service.py:assign_user_role` |
| Admin Suspend User | `ApiClient.suspendUser` | `POST /admin/users/<id>/suspend` | `admin.admin_suspend_user` | `user_service.py:suspend_user` |
| Admin Host Telemetry | `ApiClient.getAdminTelemetry` | `GET /admin/telemetry` | `admin.admin_telemetry` | `operations_service.py:get_real_system_telemetry` |
| Admin Audit Logs | `ApiClient.getAdminAuditLogs` | `GET /admin/audit-logs` | `admin.admin_list_audit_logs` | `audit_service.py:list_audit_events` |
| Admin Backup Database | `ApiClient.createAdminBackup` | `POST /admin/backups` | `admin.admin_backups` | `operations_service.py:create_database_backup` |
| Admin Restore Database | `ApiClient.restoreAdminBackup` | `POST /admin/backups/<id>/restore` | `admin.admin_restore_database` | `operations_service.py:restore_database` |

---

## 11. Backend APIs Without Known Frontend Consumer

In adherence to Phase 1 Discovery guidelines, backend routes that exist in the codebase but have no direct caller in `frontend/assets/js/api.js` or `frontend/assets/js/views/` are documented below as `NO FRONTEND CONSUMER FOUND`. These endpoints serve external API clients (RFC 6750 Bearer JWT), background maintenance jobs, or CLI administrative scripts:

| API ID | Method & Route Pattern | Backend Controller | Intended Purpose / Category | Status |
|---|---|---|---|---|
| `UNF-001` | `POST /api/v1/auth/refresh` | `api_auth.api_refresh` | External REST API clients token refresh | `NO FRONTEND CONSUMER FOUND` |
| `UNF-002` | `POST /api/v1/auth/email-change` | `api_auth.api_email_change` | External REST API client email change request | `NO FRONTEND CONSUMER FOUND` |
| `UNF-003` | `POST /api/v1/auth/email-change/verify` | `api_auth.api_email_change_verify` | External REST API client email verification | `NO FRONTEND CONSUMER FOUND` |
| `UNF-004` | `POST /api/v1/auth/password-reset` | `api_auth.api_password_reset` | External REST API password reset trigger | `NO FRONTEND CONSUMER FOUND` |
| `UNF-005` | `POST /api/v1/auth/password-reset/verify` | `api_auth.api_password_reset_verify` | External REST API password reset completion | `NO FRONTEND CONSUMER FOUND` |
| `UNF-006` | `GET /api/v1/courses` | `api_courses.api_list_courses` | External REST API course discovery | `NO FRONTEND CONSUMER FOUND` |
| `UNF-007` | `POST /api/v1/courses` | `api_courses.api_create_course` | External REST API course creation | `NO FRONTEND CONSUMER FOUND` |
| `UNF-008` | `PATCH /api/v1/courses/<id>` | `api_courses.api_update_course` | External REST API course update | `NO FRONTEND CONSUMER FOUND` |
| `UNF-009` | `POST /api/v1/courses/<id>/archive` | `api_courses.api_archive_course` | External REST API course archiving | `NO FRONTEND CONSUMER FOUND` |
| `UNF-010` | `POST /api/v1/courses/<id>/enroll` | `api_courses.api_enroll_course` | External REST API student enrollment | `NO FRONTEND CONSUMER FOUND` |
| `UNF-011` | `GET /api/v1/lessons/<id>` | `api_lessons.api_get_lesson` | External REST API lesson retrieval | `NO FRONTEND CONSUMER FOUND` |
| `UNF-012` | `POST /api/v1/lessons/<id>/activity` | `api_lessons.api_record_activity` | External REST API bounded progress sync | `NO FRONTEND CONSUMER FOUND` |
| `UNF-013` | `GET /api/v1/assessments` | `api_assessments.api_list_assessments` | External REST API assessment listing | `NO FRONTEND CONSUMER FOUND` |
| `UNF-014` | `POST /api/v1/assessments/<id>/start` | `api_attempts.api_start_attempt` | External REST API assessment attempt start | `NO FRONTEND CONSUMER FOUND` |
| `UNF-015` | `POST /api/v1/attempts/<id>/answers` | `api_attempts.api_save_answer` | External REST API autosave batch | `NO FRONTEND CONSUMER FOUND` |
| `UNF-016` | `POST /api/v1/attempts/<id>/submit` | `api_attempts.api_submit_attempt` | External REST API attempt submission | `NO FRONTEND CONSUMER FOUND` |
| `UNF-017` | `POST /api/v1/regrades` | `api_regrades.api_create_regrade_job` | External REST API trigger regrading | `NO FRONTEND CONSUMER FOUND` |
| `UNF-018` | `POST /api/v1/files/upload` | `api_files.api_upload_file` | External REST API direct file upload | `NO FRONTEND CONSUMER FOUND` |
| `UNF-019` | `GET /api/v1/ai/conversations` | `api_ai.api_list_conversations` | External REST API AI conversation list | `NO FRONTEND CONSUMER FOUND` |
| `UNF-020` | `POST /api/v1/ai/rag/query` | `api_ai.api_rag_query` | External REST API RAG search endpoint | `NO FRONTEND CONSUMER FOUND` |
| `UNF-021` | `GET /api/ui/screens` | `frontend.list_screens` | Prototype screen discovery endpoint | `NO FRONTEND CONSUMER FOUND` |
| `UNF-022` | `GET /api/ui/screen/<folder_name>` | `frontend.get_screen_html` | Prototype HTML loader (returns 404) | `NO FRONTEND CONSUMER FOUND` |

---

## 12. Workflow Inventory

### WF-001: User Authentication & Dual Session Establishment
- **Expected Execution Chain:**
  1. **UI:** User fills email and password on `#/auth` (`views/auth.js`).
  2. **API:** `ApiClient.login()` sends `POST /auth/login` with credentials and CSRF cookie.
  3. **Auth:** `session_auth_service.py` validates `users.password_hash`, checks `users.is_active`.
  4. **Authz:** Rotates session ID, initializes `AuthSession`, sets `auth_version`, writes `user_roles`.
  5. **DB:** Inserts row into `auth_sessions`; commits transaction.
  6. **Response:** Returns JSON envelope with `user` profile and `csrf_token`.
  7. **UI:** `AppRouter` updates `window.app.currentUser`, switches topbar menu, and routes to role home.

### WF-002: Instructor Application & Multi-Admin Credential Review
- **Expected Execution Chain:**
  1. **UI:** Student submits CV, degree evidence (`.pdf`, `.png`), and bio at `#/student/become-instructor`.
  2. **API:** `ApiClient.submitInstructorApplication()` sends `POST /student/become-instructor` (multipart/form-data).
  3. **Auth/Authz:** Enforces student role; `file_service.py` places uploads into `/storage/evidence`.
  4. **BL:** `user_service.py` creates `InstructorApplication` in `PENDING` state and emits `INSTRUCTOR_APPLICATION_SUBMITTED` notification.
  5. **Admin UI:** Admin with `ADMIN_INSTRUCTOR_REVIEW` clicks bell or visits `#/admin/governance?tab=applications`.
  6. **API:** Admin clicks "Xem trước" (`GET /admin/instructor-applications/<id>/evidence/<f>?preview=1`), modal loads inline PDF/image via `X-Frame-Options: SAMEORIGIN`.
  7. **Decision:** Admin approves; `user_service.py` assigns `INSTRUCTOR` role in `user_roles`, logs `AuditEvent`.

### WF-003: Course Lifecycle, ABET SLOs & Side-by-Side Change Approval
- **Expected Execution Chain:**
  1. **UI:** Instructor creates course at `#/instructor/courses`, inputs ABET SLOs and passing threshold.
  2. **API:** `POST /instructor/courses`, `PATCH /instructor/courses/<id>`.
  3. **BL:** `CourseService` stores course in `DRAFT`; writes SLO criteria into JSON fields.
  4. **Submit:** Instructor clicks "Gửi duyệt"; course state transitions `DRAFT` → `PENDING_REVIEW`.
  5. **Admin Review:** Admin with `ADMIN_COURSE_REVIEW` opens `#/admin/courses/review?id=<cId>`, audits curriculum tree.
  6. **Publish:** Admin approves; status transitions to `PUBLISHED`; Course becomes discoverable in public catalog.
  7. **Change Request:** When Instructor edits published lessons, a `CourseChangeRequest` is created; Admin inspects side-by-side diff before merging.

### WF-004: DAG Prerequisite Validation & Concurrency-Safe Enrollment
- **Expected Execution Chain:**
  1. **UI:** Student browses `#/student/catalog` and clicks "Ghi danh" for Course B.
  2. **API:** `POST /student/courses/<bId>/enroll`.
  3. **Authz:** Checks student authentication and active enrollment capacity.
  4. **BL (DAG Check):** `CourseService` inspects `course_prerequisites`; verifies student possesses `COMPLETED` summary in `course_completion_summaries` for prerequisite Course A without cycles.
  5. **DB Locking:** Acquires row-level lock on `courses` row to prevent overbooking capacity.
  6. **Persistence:** Inserts `Enrollment` and active `EnrollmentPeriod`; records `EnrollmentEvent(ENROLLED)`.
  7. **UI:** Transitions student immediately to `#/student/courses/<bId>`.

### WF-005: Notion-Style Lesson Authoring & Anti-Seek Video Binding
- **Expected Execution Chain:**
  1. **UI:** Instructor enters `#/instructor/courses/:id/lessons/:id`.
  2. **Video Setup:** Dastes YouTube URL (`UI.parseYouTubeId`) or uploads `.mp4` file (< 1 GB).
  3. **Content Setup:** Writes Markdown content and configures 4-type mini-quiz (MCQ, Fill-in-blank, Matching, True/False).
  4. **API:** `PATCH /instructor/lessons/<lId>`.
  5. **Scan Hook:** If file uploaded, ClamAV scans file in background; status set to `PENDING` → `CLEAN`.
  6. **Student Delivery:** In `StudentView`, video player embeds anti-seek watcher; `recordLessonProgress` ensures student watches required percentage before completion is marked.

### WF-006: Exam Studio 50/50 Split Live Parser & 100/N Point Distribution
- **Expected Execution Chain:**
  1. **UI:** Instructor navigates to `#/instructor/exams/editor`.
  2. **Input:** Drags and drops Word `.docx` or Azota text into the left pane dropzone.
  3. **API:** `POST /instructor/exams/parse-file` passes file to `import_service.py`.
  4. **Parsing:** Regex bóc tách câu hỏi, đáp án A/B/C/D, giải thích, ảnh base64; returns parsed JSON questions.
  5. **Live Cards:** Right pane renders editable interactive question cards with two-way textarea sync.
  6. **Matrix (100/N):** Step 3 auto-calculates $100.0 / N$ points per question, assigning remainder to the final card.
  7. **Publish:** Step 4 freezes assessment timing and question points; transitions to `PUBLISHED`.

### WF-007: Online Assessment Focus Mode & Single-Active-Tab Lease Fencing
- **Expected Execution Chain:**
  1. **Waiting Room:** Student enters `#/student/assessments/waiting-room`; server checks remaining attempts.
  2. **Start Attempt:** Student clicks "Bắt đầu"; `POST /student/assessments/<id>/start` initializes `AssessmentAttempt`, freezes choice shuffle snapshots, generates `lease_token`.
  3. **Focus Mode:** Exam Console switches to distraction-free fullscreen; listens for `blur` events (`AttemptFocusEvent`).
  4. **Lease Heartbeat:** Active tab posts `POST /student/attempt/<id>/lease/renew` every 10 seconds.
  5. **Tab Conflict:** If a second tab attempts to save or submit, server detects lease mismatch and rejects with HTTP 409 (`LEASE_CONFLICT`).
  6. **Submit:** Student submits (or timer expires); `POST /student/attempt/<id>/submit` idempotently evaluates objective questions and renders final score or score policy notice.

### WF-008: Automated Objective Grading & Idempotent Regrading
- **Expected Execution Chain:**
  1. **Submit:** `AttemptService.submit_attempt` compares student choice selections against frozen snapshots.
  2. **Objective Score:** Multiple choice, true/false, fill-in-blank auto-graded; total score tallied.
  3. **Flaw Discovered:** Instructor discovers ambiguous question; creates `QuestionCorrection`.
  4. **Trigger Regrade:** `POST /instructor/assessments/<id>/regrade` schedules `RegradeJob`.
  5. **Worker Execution:** `regrade_worker.py` loops through `regrade_items`; awards full credit or re-scores based on correction type without modifying original answer records; updates `assessment_results` and notifies affected students.

### WF-009: Fail-Closed ClamAV Malware Quarantine & Asset Delivery
- **Expected Execution Chain:**
  1. **Upload:** File uploaded via `POST /instructor/courses/<id>/files` or lesson attachment.
  2. **Storage:** Bytes stored in `/quarantine`; `FileRevision.scan_status` set to `PENDING`.
  3. **Scan Execution:** `ScannerService` contacts ClamAV daemon (`clamdscan` on port 3310).
  4. **Verdict:**
     - Clean: Bytes moved to `/storage`; `scan_status` becomes `PASS`; file becomes downloadable.
     - Infected or Daemon Offline: Status becomes `INFECTED` or remains `PENDING`; file is fail-closed and strictly inaccessible to students (HTTP 403).
  5. **Admin Override:** In emergency, Admin uses `POST /admin/files/<id>/quarantine-override` with password re-auth.

### WF-010: Octopus AI Assistant Context-Grounding & Reconnaissance Defense
- **Expected Execution Chain:**
  1. **Chat Request:** Student submits query via `#floating-ai-drawer` or `#/student/ai-assistant`.
  2. **Stage 1 (0ms):** `ScopeClassifier` runs regex against confidential system patterns (`_CONFIDENTIAL_SYSTEM_PATTERNS`). Questions probing user roles, accounts, or database schema are immediately rejected (`REFUSAL_MESSAGE_CONFIDENTIAL_SYSTEM`).
  3. **Stage 2 (RAG):** For academic queries, `rag_service.py` filters `knowledge_chunks` strictly to courses the student is actively enrolled in.
  4. **Stage 3 (LLM):** `GeminiService` rotates across multi-key pool (`api/api_key.md`), cascading from `gemini-flash-latest` to fallback models; completes response in < 5 seconds.
  5. **Purge:** Background job purges conversation text older than 5 minutes of inactivity (`AI-003`).

### WF-011: Cryptographic Audit Trail Chaining & 4-Step Database Restore
- **Expected Execution Chain:**
  1. **Action:** Sensitive Admin mutation occurs (e.g., user suspension, role delegation, file quarantine override).
  2. **Audit Insert:** `AuditService` loads latest `audit_events` row, extracts `sha256_hash`, computes `SHA-256(prev_hash + actor_id + action + timestamp + payload)`.
  3. **Same Transaction:** `AuditEvent` committed in the same database transaction as the business mutation; if audit fails, mutation rolls back.
  4. **Restore Drill:** Admin initiates restore at `#/admin/operations`:
     - Step 1: Validates backup file existence and SHA-256 checksum.
     - Step 2: Executes dry-run compatibility check.
     - Step 3: Admin enters exact confirmation phrase `CONFIRM_LIVE_DATABASE_RESTORE` + sudo password.
     - Step 4: System enters maintenance mode, restores database, appends recovery audit event, and resumes services.

---

## 13. Test Inventory

The repository possesses a comprehensive automated testing suite consisting of **163 Python test files** (with **1,530 collected pytest cases**) and **26 JavaScript frontend test suites**:

```
TOTAL TESTS COLLECTED: 1,530 tests (pytest)
------------------------------------------------------------
tests/unit/        : 44 files | Service, model, parser, and security unit tests
tests/api/         : 58 files | Web and REST API integration endpoints
tests/security/    : 28 files | Penetration tests, IDOR defenses, CSRF boundaries, AI safety
tests/concurrency/ :  4 files | Multi-tab lease races, enrollment capacity races
tests/e2e/         :  4 files | End-to-end user and operational lifecycles
tests/integration/ :  3 files | Schema migrations and demo seed validation
tests/ (root)      : 22 files | Regression, hotfix, and repository contract tests
tests/frontend/    : 26 files | JavaScript UI, router, and view component tests
```

### Feature / API Suite Mapping

| Feature / Domain Group | Key Test Files | Test Type | Coverage Focus |
|---|---|---|---|
| **Identity & Authentication** | `tests/unit/test_user_service.py`, `test_session_auth_service.py`, `test_jwt_auth_service.py`, `tests/api/test_auth_web.py`, `test_api_auth.py`, `tests/security/test_rbac_and_idor.py` | Unit, API, Security | Password complexity, email normalization, auth_version revocation, CSRF token handling |
| **Course & Learning Units** | `tests/unit/test_course_service.py`, `test_lesson_service.py`, `tests/api/test_courses.py`, `test_lesson_api.py`, `tests/security/test_course_idor.py`, `test_lesson_idor.py` | Unit, API, Security | DAG prerequisites, cycle detection, learning units reorder, lesson status flow |
| **Enrollment & Progress** | `tests/unit/test_enrollment_service.py`, `test_completion_service.py`, `tests/api/test_enrollments.py`, `tests/concurrency/test_enrollment_capacity.py` | Unit, API, Concurrency | Capacity race conditions, re-enrollment periods, progress calculation, completion certificates |
| **Exam Studio & Parsers** | `tests/unit/test_parse_exam_file.py`, `tests/api/test_excel_moodle_exam_import.py`, `test_moodle_and_excel_exam_images.py`, `tests/frontend/exam_parser_images.test.js` | Unit, API, Frontend | Word docx parsing, Azota raw syntax, Excel template, Moodle XML/JSON, image embedding |
| **Assessments & Timing** | `tests/unit/test_assessment_service.py`, `tests/api/test_assessment_api.py`, `tests/security/test_assessment_idor.py`, `test_assessment_timezone_security.py` | Unit, API, Security | Structure lock on start, timing freeze on publish, blueprint candidate validation |
| **Attempts & Lease Fencing** | `tests/unit/test_attempt_service.py`, `test_attempt_lease_service.py`, `test_attempt_autosave_service.py`, `tests/concurrency/test_attempt_lease_race.py`, `test_submission_idempotency_race.py` | Unit, Concurrency | Single active tab lease, heartbeat renewal, takeover, autosave deduplication, idempotent submit |
| **Grading & Regrading** | `tests/unit/test_grading_service.py`, `test_regrade_service.py`, `tests/api/test_regrade_api.py`, `tests/security/test_grading_idor.py`, `test_regrade_idor.py` | Unit, API, Security | Manual essay grading, choice_key regrading, full credit for flawed questions, idempotency |
| **File Storage & ClamAV** | `tests/unit/test_file_service.py`, `test_malware_scan_service.py`, `test_sec01_virus_scan.py`, `tests/security/test_quarantine_fail_closed.py`, `tests/api/test_files.py` | Unit, API, Security | ClamAV fail-closed security, macro blocking, SHA-256 physical deduplication, quarantine override |
| **AI Assistant & RAG** | `tests/unit/test_ai_service.py`, `test_ai_scope_classifier.py`, `test_rag_service.py`, `tests/security/test_ai_scope_enforcement.py`, `test_ai_course_authorization.py` | Unit, Security | Anti-reconnaissance guardrails, multi-key rotation, role-scoped RAG retrieval, chat purge |
| **Admin & Operations** | `tests/unit/test_operations_service.py`, `test_audit_service.py`, `tests/security/test_operations_security.py`, `test_audit_security.py`, `tests/e2e/test_admin_ops_lifecycle_e2e.py` | Unit, Security, E2E | Real psutil host telemetry, 5 sub-roles delegation, 4-step live DB restore, SHA-256 audit chaining |
| **Repository Contract** | `tests/test_repository_contract.py`, `scripts/repo_check.py` | Contract | 73 DDL tables, markdown fences, no raw SQL mutations outside repository contract |

---

## 14. Infrastructure Inventory

### 1. Multi-Stage Docker Build (`Dockerfile`)
- **Stage 1 (Builder):** `python:3.12-slim-bookworm`, installs build essentials, `unixodbc-dev`, pre-compiles wheels.
- **Stage 2 (Runtime):** Minimal Debian 12 bookworm footprint, installs `msodbcsql18` (Microsoft ODBC Driver 18 for SQL Server).
- **Security:** Non-root runtime user `appuser` (UID 10001, GID 10001).
- **Entrypoint:** `scripts/docker-entrypoint.sh` executes database wait loop, runs Alembic migrations (`flask db upgrade`), initializes baseline roles, and launches Gunicorn.

### 2. Docker Compose Orchestration (`docker-compose.yml`)
- **Service 1 (`db`):** `mcr.microsoft.com/mssql/server:2022-latest`, Developer edition, healthcheck on port 1433 via `sqlcmd`.
- **Service 2 (`clamav`):** `clamav/clamav:latest`, ClamAV malware scanning daemon on port 3310, definitions volume `pwd301_clamav_defs`.
- **Service 3 (`web`):** PWD301 Flask Web Engine, depends on healthy `db` and started `clamav`.
- **Persistent Volumes:** `pwd301_sqldata`, `pwd301_clamav_defs`, `pwd301_storage_data`, `pwd301_quarantine_data`, `pwd301_backup_data`, `pwd301_export_data`.
- **Network:** Isolated bridge network `pwd301_network`.

### 3. Production WSGI Server
- **Server:** Gunicorn 22.0.0+ with 4 workers, 2 threads per worker, 120s timeout.
- **Reverse Proxy Protection:** `ProxyFix` middleware active (`USE_PROXY_FIX=true`, 1 proxy depth) for accurate client IP identification.

### 4. Health Checks & Telemetry
- **Liveness & Readiness:**
  - `GET /health`: Fast probe returning HTTP 200 with basic status and version.
  - `GET /health/deep`: Comprehensive probe querying SQL Server `SELECT 1`, pinging ClamAV daemon, and checking disk storage writeability.
- **Physical Host Telemetry:** `GET /admin/telemetry` extracts authentic OS metrics (Host total RAM, CPU core count, disk space) via `psutil`.

---

## 15. Potential Vibe-Code Artifacts

During the deep scan of codebase implementations, the following artifacts, dead code candidates, or remnants were identified for Phase 2 verification:

1. **Unreferenced Controller Module (`frontend/assets/js/controllers.js`):**
   - File length: 518 lines defining `class Controllers`.
   - Contains methods like `initAuth`, `initStudentDashboard`, `initExamEditor`, and several `console.log` statements.
   - **Finding:** The file is **completely absent** from `frontend/index.html` script tags and is never imported or called by `AppRouter` or any view module.
2. **Ghost Prototype Folders in `SCREEN_METADATA` (`src/pwd301/blueprints/frontend/routes.py`):**
   - Lines 48–198 define 22 entries in `SCREEN_METADATA` pointing to folder names like `pwd301_auth_account_lifecycle_variant_1_...`, `pwd301_student_dashboard_variant_1_...`.
   - **Finding:** None of these 22 directories exist in `frontend/`. The route `/api/ui/screen/<folder_name>` will return 404 for all of them, and `/api/ui/screens` returns `has_code: false` for every item.
3. **Plaintext API Keys in Workspace (`api/api_key.md`):**
   - File length: 103 lines containing 72 Google Gemini API keys in plaintext.
   - **Finding:** Violates operational invariant 10.6 ("Tuyệt đối không để lộ API keys..."). Even if `.env` is gitignored, `api/api_key.md` resides in the workspace tree.
4. **Mock Fallback Client in Production Service (`src/pwd301/services/gemini_service.py`):**
   - `gemini_service.py` contains `MockGeminiClient` (lines 293–450) and calls `MockGeminiClient()` when offline or when API keys fail.
   - **Finding:** Useful for unit testing, but needs verification in Phase 2 to ensure production environments do not silently fall back to mock answers during API degradation.
5. **Console Logging in Production Frontend Scripts:**
   - Multiple `console.warn` and `console.error` calls exist across `api.js`, `router.js`, `views/admin.js`, and `views/instructor-exams.js`.
   - Need review in Phase 2 to determine if any log statements leak sensitive metadata or user IDs to the browser console.

---

## 16. Discovery Uncertainties (Unresolved Items)

| ID | Uncertainty Description | Conflicting Evidence / Context | Risk / Impact | Phase 2 Action Required |
|---|---|---|---|---|
| `UNK-001` | Standalone Question Bank Decommissioning residue | `tasks/CURRENT.md` reports complete decommissioning in TASK-078. However, `src/pwd301/models/question_bank.py` (5 tables) and `src/pwd301/services/question_bank_service.py` (1,757 lines) remain intact. | Confusion on whether Question Bank models are permanent fixtures for Exam assignments or planned for deletion. | Phase 2 to inspect all call sites of `question_bank_service.py` in `assessment_service.py`. |
| `UNK-002` | `SCREEN_METADATA` and `/api/ui/screens` endpoints validity | `src/pwd301/blueprints/frontend/routes.py` retains 22 prototype definitions for non-existent directories. | Dead endpoints returning 404; unnecessary code surface. | Phase 2 to confirm if `/api/ui/screens` is needed or should be pruned. |
| `UNK-003` | Status of `frontend/assets/js/controllers.js` | 518 lines of code not linked in `frontend/index.html` and not referenced by `router.js`. | Redundant code footprint; potential confusion regarding actual event handlers. | Phase 2 to verify if any logic in `controllers.js` is missing from `views/*.js`. |
| `UNK-004` | Plaintext Gemini API Key storage in `api/api_key.md` | `api/api_key.md` exists with 72 raw API keys. | Security exposure risk; potential secret leak. | Phase 2 security audit to verify `.gitignore` rules and key rotation mechanism. |
| `UNK-005` | Dual Route API Parity Governance (Web SPA vs REST API) | Web SPA uses `/student/*`, `/instructor/*`, `/admin/*`. Headless REST clients use `/api/v1/*`. Both implement business logic. | Risk of behavioral divergence if a service method is updated in one route group but not the other. | Phase 2 to run parity checks across all pairs of Web and REST routes. |
| `UNK-006` | Execution environment for Frontend JavaScript tests | `tests/frontend/` contains 26 `.js` test files, but no root `package.json` or Jest runner script is present. | Frontend unit tests may not be running automatically in CI (`ci.yml` runs only pytest). | Phase 2 to test running frontend tests via Node/Jest and assess CI integration. |

---

## 17. Verification Checklist for Phase 2

Phase 2 Audit MUST empirically verify the following checklist items with live command outputs:

- [ ] **VC-01 (DB Schema Authority):** Verify that all 73 tables defined in `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/` match `src/pwd301/models/*.py` attributes, types, and constraints byte-for-byte.
- [ ] **VC-02 (Dual-Auth Isolation):** Empirically test that Web session cookies are rejected on `/api/v1/*` endpoints, and that Bearer JWT tokens are properly validated on REST routes.
- [ ] **VC-03 (Single Active Tab Lease):** Run concurrency simulation test (`tests/concurrency/test_attempt_lease_race.py`) to verify that simultaneous writes from a second browser tab receive HTTP 409 `LEASE_CONFLICT`.
- [ ] **VC-04 (Autosave Idempotency):** Verify that duplicate and out-of-order autosave answer packets cannot overwrite newer student answer sequences.
- [ ] **VC-05 (ClamAV Fail-Closed Quarantine):** Stop the ClamAV container or mock an offline scanner to verify that student file download is blocked (HTTP 403) and status remains `PENDING`.
- [ ] **VC-06 (Video Limit Hard Boundary):** Verify that uploading a video $\ge 1\text{ GB}$ (1,000,000,000 bytes) returns HTTP 413 `PAYLOAD_TOO_LARGE` at the application gate.
- [ ] **VC-07 (AI Anti-Reconnaissance Defense):** Send probes asking for user roles, system passwords, and database structure to `/student/ai/chat` to verify that `_CONFIDENTIAL_SYSTEM_PATTERNS` blocks 100% of queries with HTTP 400.
- [ ] **VC-08 (Authentic Host Telemetry):** Call `/admin/telemetry` on live container and verify returned RAM, CPU model, and disk metrics reflect the physical host machine rather than container cgroups.
- [ ] **VC-09 (Cryptographic Audit Chaining):** Query `audit_events` table and verify that `sha256_hash` of each record matches `SHA-256(prev_hash + ...)`.
- [ ] **VC-10 (Controlled DB Restore Drill):** Execute backup verification and dry-run restore endpoints to verify that live database restore strictly requires `CONFIRM_LIVE_DATABASE_RESTORE` and Admin password.
- [ ] **VC-11 (Orphan Code Verification):** Confirm whether `frontend/assets/js/controllers.js` and `routes.py:SCREEN_METADATA` can be cleanly retired without breaking any user flows.
- [ ] **VC-12 (Frontend Test Automation):** Verify setup for running the 26 JavaScript unit tests in `tests/frontend/` using Node.js.
