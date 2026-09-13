# TASK-031 — AI Assistance Subsystem Hardening, Semantic RAG Fusion & Bloom Question Authoring Lifecycle

**Status:** DONE  
**Assignee:** Principal AI Systems Architect & Lead Software Engineer  
**Started Date:** 2026-09-12  
**Completed Date:** 2026-09-12  

---

## Goal
Implement, harden, and verify the distributed **AI Assistance Subsystem** for the PWD301 academic platform adhering strictly to the canonical 10-section specification:
1. **Philosophical Principles & Invariants**: Fail-Closed, ADR-002 Zero Internal PK Leakage, pre-retrieval authorization scoping, grounded citations.
2. **Gemini Integration & Reliability Fortress**: Primary model `gemini-3.8-flash`, cascading fallback (`gemini-3.8-flash` -> `gemini-3.6-flash` -> `gemini-flash-latest`), 15s timeout clamp, fail-fast on 4xx client errors without fallback.
3. **Adaptive Chunking & Deduplication**: Target chunk size 300–500 tokens (max 450), 50–100 tokens overlap (75 tokens), SHA-256 binary hash deduplication.
4. **Semantic Retrieval Engine**: Sparse BM25 + Dense Cosine Semantic fusion ($0.5 \cdot \text{BM25} + 0.5 \cdot \text{Cosine}$) with relevance confidence threshold (0.05).
5. **Question Authoring & Review Workflow**: 6-level Bloom's Taxonomy (`REMEMBER`, `UNDERSTAND`, `APPLY`, `ANALYZE`, `EVALUATE`, `CREATE`), higher-order mapping to DB check constraint while preserving taxonomy metadata, draft approval/rejection lifecycle producing immutable `QuestionRevision` (Revision 1) and `QuestionProvenance(source_type="AI_GENERATED")`.
6. **AI Conversation Lifecycle**: 5-minute inactivity session expiration (AI-003) with minimal metadata retention (purging raw message content).
7. **Abuse Defense & Tiered Rate Limiting**: Role quotas (STUDENT: 20/min, INSTRUCTOR: 60/min, ADMIN: 120/min, ANONYMOUS: 10/min) with `Retry-After` header injection on HTTP 429.
8. **Automated Verification**: Complete test suite with 100% pass rate across unit, API, and security tests.

---

## Source-of-Truth Documents
- `docs/system/PWD301_SYSTEM_SPECIFICATION/` (Canonical system & AI assistant specification)
- `docs/database/PWD301_DATABASE_ARCHITECTURE/` (DDL & check constraints: `ck_ai_generated_question_drafts_3`, `ck_ai_generated_question_drafts_4`)
- `AGENTS.md` (Operational contract, Fail-closed invariants, Zero Internal PK Leakage, session auth)
- `frontend-preview/` (Canonical UI styling and functional minimalism controls)

---

## Key Changes
1. **Gemini Client Engine (`src/pwd301/services/gemini_service.py`)**:
   - Configured primary default to `gemini-3.8-flash` with cascading fallback models `("gemini-3.8-flash", "gemini-3.6-flash", "gemini-flash-latest")`.
   - Clamped API call timeout to 15–30 seconds (default 15s).
   - Added fail-fast logic for HTTP 4xx client errors (disables cascading fallback on bad client input).
   - Enhanced `MockGeminiClient.draft_questions` and `RealGeminiClient.draft_questions` to accept all 6 Bloom taxonomy levels.
2. **Semantic RAG Knowledge Pipeline (`src/pwd301/services/rag_service.py`)**:
   - Configured `DEFAULT_MAX_CHUNK_TOKENS = 450` (target 300–500 tokens) and `DEFAULT_OVERLAP_TOKENS = 75` (target 50–100 tokens, ~16.7% overlap).
   - Implemented `_compute_bm25_score(query_tokens, chunk_text, doc_frequencies, total_docs, avg_doc_len)` with IDF and document length normalization.
   - Implemented `_compute_cosine_semantic_score(query, chunk_text)` with term vector space projection and exact substring match bonus.
   - Integrated BM25 + Cosine fusion into `retrieve_relevant_chunks()` with `RELEVANCE_CONFIDENCE_THRESHOLD = 0.05`.
3. **Question Authoring & Review Lifecycle (`src/pwd301/services/ai_service.py`)**:
   - Defined `BLOOM_TAXONOMY_LEVELS` supporting `REMEMBER`, `UNDERSTAND`, `APPLY`, `ANALYZE`, `EVALUATE`, `CREATE`.
   - Added `_map_bloom_to_db_difficulty` to map higher-order levels to `APPLY` for database check constraints while prefixing `[Bloom: <LEVEL>]` in the explanation.
   - Implemented `approve_question_draft`: creates formal `Question`, immutable `QuestionRevision` (Revision 1), `QuestionProvenance(source_type="AI_GENERATED")`, and marks draft as `APPROVED`.
   - Implemented `reject_question_draft`: marks draft as `REJECTED`, preventing approval.
4. **REST API & Web Route Handlers (`src/pwd301/blueprints/api_ai/routes.py`, `student/routes.py`)**:
   - Exposed `POST /api/ai/questions/drafts/<draft_id>/approve` and `POST /api/ai/questions/drafts/<draft_id>/reject`.
   - Wired `check_ai_rate_limit(actor, role=actor.primary_role, client_ip=request.remote_addr)` across all AI endpoints.
   - Injected `Retry-After: <retry_after>` header on HTTP 429 rate limit responses.
5. **Multi-Worker Rate Limiting & Test Isolation (`src/pwd301/services/rate_limit_service.py`, `tests/conftest.py`)**:
   - Configured `AI_ROLE_LIMITS = {"ADMIN": 120, "INSTRUCTOR": 60, "STUDENT": 20, "ANONYMOUS": 10}`.
   - Added `reset_all_rate_limits()` and autouse test isolation fixture in `tests/conftest.py`.

---

## Verification Record
- **Pytest Suite (`tests/api/test_ai_api.py`, `tests/security/test_ai_security.py`, `tests/unit/test_ai_service.py`, `tests/unit/test_ai_session_recovery.py`)**: **34 passed, 0 failed** in 11.54s.
- **Ruff Linter**: `ruff check` passed with 0 errors across all modified files.
  - `POST /auth/login` (Student & Admin): HTTP 302 -> `/student/dashboard`.
  - `GET /student/dashboard`: HTTP 200 (Clean, 0 errors, no 500 crash).
  - `GET /student/courses/<course_id>`: HTTP 200.
  - `GET /student/assessments`: HTTP 200.
  - `GET /student/ai-assistant`: HTTP 200.

---

# TASK-031 — Web Role Persistence, Multi-Role Portal Navigation & Safe Role Switching

**Status:** DONE  
**Assignee:** Principal Software Architect & Lead Fullstack Engineer  
**Started Date:** 2026-09-12  
**Completed Date:** 2026-09-12  

## Goal
Resolve the critical issue where any user logging in with an elevated role (Admin, Instructor) was downgraded and permanently locked into the Student role (`active_role = 'STUDENT'`), with sidebars rendering only student navigation links and no way to operate their administrative or teaching functions.

## Root Cause Analysis
1. **Unordered Relationship Extraction in Auth Login**:
   - In `src/pwd301/blueprints/auth/routes.py`, login set `session["active_role"] = user.roles[0].code`.
   - Because canonical roles in the database are seeded as STUDENT (ID 1), INSTRUCTOR (ID 2), and ADMIN (ID 3), `user.roles[0]` was invariably `Role(code='STUDENT')` for all users (including Admins and Instructors who cumulative-inherit Student).
   - As a result, every login immediately forced `session["active_role"] = "STUDENT"`.
2. **Hardcoded Fallback in Base Template**:
   - `src/pwd301/templates/base.html` evaluated `active_r = session.get('active_role', '')` with a fallback `or (current_user.is_authenticated and not active_r)`, hardcoding `STUDENT` if missing or defaulting.
   - The topbar role displayed `STUDENT`, and the desktop and mobile sidebars rendered the Student navigation links only.
3. **Missing Role Synchronization and Switching Mechanisms**:
   - When an Admin navigated to `/admin/...` or an Instructor to `/instructor/...`, `active_role` in session remained `STUDENT`, causing the sidebar to remain stuck in student view.
   - The platform lacked a dedicated CSRF-protected `POST /auth/switch-role` endpoint to enable authorized multi-role users to switch between their legitimate perspectives.

## Key Changes
1. **Canonical `primary_role` Resolution on User Model**:
   - Added `primary_role` property to `User` and `AnonymousUser` (`ADMIN` > `INSTRUCTOR` > `STUDENT`), strictly observing AUTH-002 cumulative hierarchy.
2. **Login Role Resolution**:
   - In `auth/routes.py`, login sets `session["active_role"] = user.primary_role` and redirects to the appropriate role dashboard.
3. **Portal Auto-Synchronization in `before_request`**:
   - In `src/pwd301/__init__.py`, `before_request` dynamically synchronizes `session["active_role"]` to `ADMIN` when an admin accesses `/admin/...`, and to `INSTRUCTOR` when an instructor accesses `/instructor/...`.
4. **Safe, CSRF-Protected Role Switch Endpoint & Authorization Hierarchy**:
   - Implemented `POST /auth/switch-role` with strict role entitlement validation:
     - Admin: allowed targets = `ADMIN`, `INSTRUCTOR`, `STUDENT`.
     - Instructor: allowed targets = `INSTRUCTOR`, `STUDENT`.
     - Student: cannot switch roles (strictly rejected with HTTP 403 Forbidden).
5. **Modernized Topbar User Dropdown in `base.html`**:
   - Added `VAI TRÒ (CHUYỂN ĐỔI)` dropdown section:
     - Admin sees options: Quản trị viên (Admin), Giảng viên (Instructor), Học viên (Student).
     - Instructor sees options: Giảng viên (Instructor), Học viên (Student).
     - Student sees NO role switcher section.
   - Updated topbar role title and badge to display `QUẢN TRỊ VIÊN (ADMIN)`, `GIẢNG VIÊN (INSTRUCTOR)`, `HỌC VIÊN (STUDENT)`.
6. **Docker Environment Live Reflection**:
   - Updated `docker-compose.yml` to mount `./src:/app/src` into `pwd301_web` container.
   - Rebuilt `pwd301-web:latest` image and recreated container.

## Verification Record
- **Full Pytest Suite**: 834 passed, 0 failed across unit, API, and E2E suites.
- **Web UI & Role Switching Tests (`tests/api/test_web_ui_flow_fixes.py`)**: 21 passed in 16.64s.
- **Student Portal Tests (`tests/api/test_student_portal_ui.py`)**: 16 passed in 10.51s.
- **Ruff & Mypy**: All checks passed (83 source files checked, 0 errors).
- **Live Container Verification on `http://localhost:5000` (`test_live_roles.py`)**:
  - Admin login: shows `QUẢN TRỊ VIÊN (ADMIN)` in topbar, dropdown displays all 3 role switch options.
  - Admin switches to `INSTRUCTOR` -> lands on `/instructor/dashboard`, topbar shows `GIẢNG VIÊN (INSTRUCTOR)`.
  - Admin switches to `STUDENT` -> lands on `/student/dashboard`, topbar shows `HỌC VIÊN (STUDENT)`, role switcher remains accessible.
  - Admin switches back to `ADMIN` -> lands on `/admin/dashboard`, topbar shows `QUẢN TRỊ VIÊN (ADMIN)`.
  - Instructor login: shows `GIẢNG VIÊN (INSTRUCTOR)` in topbar, dropdown displays only Instructor and Student options.
  - Instructor switches to `STUDENT` and back to `INSTRUCTOR` smoothly.
  - Instructor attempt to switch to `ADMIN` is rejected with HTTP 403.
  - Student login: shows `HỌC VIÊN (STUDENT)`, dropdown has NO role switcher section.
  - Student attempt to call `switch-role` is rejected with HTTP 403.

---

# TASK-032 — Student Self-Nomination & Administrative Review Workflow for Instructor Role

**Status:** DONE  
**Assignee:** Principal Software Architect & Lead Fullstack Engineer  
**Started Date:** 2026-09-12  
**Completed Date:** 2026-09-12  

## Goal
Implement an end-to-end self-nomination and onboarding workflow allowing standard users (`STUDENT`) to apply to become an `INSTRUCTOR` by providing required professional credentials and evidence (teaching experience/certificates, salary/compensation proof, educational institutional email, current teaching schedule, employment contract, Google Drive/Cloud scan folder URL, statement of purpose), coupled with an administrative review queue for Quản trị viên (`ADMIN`) to inspect, approve (granting `INSTRUCTOR` role per `AUTH-002`), or reject with justification.

## Source-of-Truth Documents
- `docs/system/PWD301_SYSTEM_SPECIFICATION/security/01_AUTHENTICATION_AUTHORIZATION.md` (AUTH-002 cumulative role hierarchy)
- `docs/system/PWD301_SYSTEM_SPECIFICATION/audit/01_AUDIT_LOG_SPECIFICATION.md` (Append-only audit trail)
- `docs/database/PWD301_DATABASE_ARCHITECTURE/` (SQL Server reference DDL, table `instructor_applications`)
- `frontend-preview/` (Functional Minimalism UI layout, tokens, typography, and styling)
- `AGENTS.md` (Strict verification, fail-closed security, role authorization)

## Key Changes
1. **Model Enhancements (`src/pwd301/models/identity.py`)**:
   - Reused canonical `InstructorApplication` schema without breaking DDL changes.
   - Added `parsed_details` property with JSON deserialization and error resilience.
   - Added Vietnamese user-friendly status labels (`status_label_vi`) and badge styling classes (`status_badge_class`).
2. **Service Layer (`src/pwd301/services/user_service.py`)**:
   - `submit_instructor_application`: Validates input, prevents duplicate pending submissions or re-application by existing instructors/admins, serializes structured evidence payload into `application_note` (capped at 2000 chars), and persists an `AuditEvent`.
   - `cancel_instructor_application`: Allows students to cancel their own `PENDING` application and records `AuditEvent`.
   - `get_user_active_application`, `get_instructor_application`, `list_instructor_applications`: Provides filtered queries.
   - `review_instructor_application`: Validates admin authorization, enforces required rejection reasons, approves via `assign_role_to_user(..., 'INSTRUCTOR')`, updates status, records append-only `AuditEvent`, and dispatches in-app notification.
3. **Web Blueprints & Routes**:
   - `src/pwd301/blueprints/student/routes.py`:
     - `GET /student/become-instructor`: Renders nomination form or current application status.
     - `POST /student/become-instructor`: Handles CSRF-protected nomination form submission.
     - `POST /student/become-instructor/cancel`: Cancels pending application.
   - `src/pwd301/blueprints/admin/routes.py`:
     - `GET /admin/instructor-applications`: Applications review queue with status tabs (`PENDING`, `APPROVED`, `REJECTED`, `ALL`).
     - `GET /admin/instructor-applications/<app_id>`: Detailed inspection view.
     - `POST /admin/instructor-applications/<app_id>/review`: Handles approve or reject actions.
4. **REST API Endpoints**:
   - `src/pwd301/blueprints/api_student/routes.py`:
     - `GET /api/student/instructor-application` (JWT Bearer)
     - `POST /api/student/instructor-application` (JWT Bearer)
     - `POST /api/student/instructor-application/cancel` (JWT Bearer)
   - `src/pwd301/blueprints/api_admin/routes.py`:
     - `GET /api/admin/instructor-applications` (Admin JWT Bearer)
     - `GET /api/admin/instructor-applications/<app_id>` (Admin JWT Bearer)
     - `POST /api/admin/instructor-applications/<app_id>/review` (Admin JWT Bearer)
5. **Functional Minimalism UI Templates**:
   - `src/pwd301/templates/student/become_instructor.html`: Multi-state view (Application form, Pending timeline, Rejection feedback banner, and Already-instructor banner).
   - `src/pwd301/templates/admin/instructor_applications.html`: Admin queue with KPI counters, filter pills, detailed candidate cards, and review modals.
   - Updated `src/pwd301/templates/base.html`: Added nomination links in desktop sidebar and mobile drawer for students and admins.
   - Updated `src/pwd301/templates/student/dashboard.html`: Added invitation card prompting students to apply as instructors.
   - Updated `frontend-preview/`: Synced preview mockup and interactions.

## Verification Record
- **Unit Tests (`tests/unit/test_instructor_application_service.py`)**: 7/7 passed.
- **Web UI & API Integration Tests (`tests/api/test_instructor_application_web_flow.py`)**: 7/7 passed.
- **Full Unit & Flow Test Suite**: 391 passed in 231.69s.
- **Ruff Linter**: 0 errors on modified files and tests.

---

# TASK-033 — Docker Container Auto-Reload & AI Assistance Resilience Overhaul

**Status:** DONE  
**Assignee:** Principal Software Architect & Lead Fullstack Engineer  
**Started Date:** 2026-09-12  
**Completed Date:** 2026-09-12  

## Goal
Investigate and resolve whole-project runtime failures preventing Docker web execution (HTTP 500 BuildError in Jinja) and AI Assistance failures (read timeouts on `gemini-3.6-flash`, broken fallback circuit in `RealGeminiClient`), ensuring full system health, type-checking compliance, and live conversational AI assistant integration.

## Root Cause Analysis
1. **Docker Jinja BuildError (Stale Gunicorn Memory)**:
   - Volume `./src:/app/src` updated on host with newly introduced endpoints (`student.become_instructor`), but the existing Gunicorn process in container `pwd301_web` retained old route definitions in memory.
   - When Jinja rendered `base.html`, `url_for('student.become_instructor')` threw `BuildError` resulting in a 500 Internal Server Error.
   - `docker-entrypoint.sh` lacked an auto-reload flag (`--reload`) when running in development (`APP_ENV=development` / `FLASK_DEBUG=1`).
2. **AI Assistance Failure & Defective Fallback Logic**:
   - `gemini-3.6-flash` consistently times out on socket read (>15s) or returns 503 Unavailable on Google's API, whereas `gemini-3.8-flash` responds in ~1.49s.
   - `RealGeminiClient._call_gemini_api` in `src/pwd301/services/gemini_service.py` immediately raised `AIServiceUnavailableError` upon timeout or 5xx error instead of continuing the `candidate_models` loop, preventing fallback models (`gemini-3.8-flash`) from ever executing.
   - The student chat route caught the exception and returned static canned responses.

## Key Changes
1. **Multi-Model Fallback Resiliency & Gemini 3.8 Flash Default**:
   - Updated `RealGeminiClient.FALLBACK_MODELS = ("gemini-3.8-flash", "gemini-3.6-flash", "gemini-flash-latest")`.
   - Updated default model to `gemini-3.8-flash` in `gemini_service.py`, `config.py`, `.env`, and `docker-compose.yml`.
   - Fixed `_call_gemini_api` to catch `TimeoutError`, `URLError`, and HTTP 5xx errors, log warnings, and seamlessly try the next model candidate.
2. **Gunicorn Development Auto-Reload**:
   - Updated `scripts/docker-entrypoint.sh` to automatically add `--reload` when `APP_ENV=development` or `FLASK_DEBUG=1`.
   - Recreated `pwd301_web` container via `docker compose up -d`.
3. **UI Formatting & Clean Formatting**:
   - Added `style="white-space: pre-wrap; line-height: 1.6;"` to the floating AI assistant in `src/pwd301/static/js/app_shell.js` for clean paragraph and list rendering.
   - Fixed all Mypy static typing issues (83 source files checked, 0 errors).
   - Fixed all Ruff linting and formatting issues (192 files checked, 0 errors).

## Verification Record
- **Full Verification Suite (`scripts/verify.ps1`)**: 858 passed in 488.93s (100% PASS).
- **Unit Tests (`tests/unit/test_ai_service.py`)**: 12/12 passed (including new `test_real_gemini_client_fallback_to_next_model`).
- **Mypy**: 0 errors across 83 source files.
- **Ruff**: 0 lint errors, 192 files formatted.
- **Live Container Verification on `http://localhost:5000`**:
  - `GET /health`: HTTP 200 OK.
  - `POST /auth/login`: HTTP 302 -> `/student/dashboard`.
  - `GET /student/dashboard`: HTTP 200 OK (Clean layout, zero 500 errors).
  - `POST /student/ai/chat`: HTTP 200 OK (Returns rich, intelligent Vietnamese answer from Gemini 3.8 Flash in < 2 seconds).

---

# TASK-034 — Real Server Hardware Telemetry Integration for System Operations & Governance Center

**Status:** DONE  
**Assignee:** Principal Software Architect & Lead Fullstack Engineer  
**Started Date:** 2026-09-12  
**Completed Date:** 2026-09-12  

## Goal
Resolve the bug where the section **"Trung tâm Điều hành & Quản trị Hệ thống"** (Admin System Operations & Governance Center) failed to retrieve actual physical/server hardware data, displaying 0% CPU, 0.0/0.0 GB RAM, 0 B network traffic, and missing hardware specs. Ensure robust cross-platform inspection (Linux container `/proc` filesystem and Windows `ctypes`/`winreg`), live dynamic telemetry polling, and synchronization between Jinja templates and the frontend preview prototype.

## Root Cause Analysis
1. **Missing `psutil` Dependency in Docker & Runtime**:
   - `psutil` was imported conditionally in `src/pwd301/services/operations_service.py`, but it was omitted from `requirements.txt` and docker wheels.
   - When running in production inside Docker on Linux, `psutil` import failed with `ModuleNotFoundError`.
2. **Platform-Restricted Fallback Mechanism**:
   - The zero-dependency fallback logic was previously guarded by `if sys.platform == "win32"`.
   - On Linux containers lacking `psutil`, RAM was returned as `0.0 / 0.0 GB (0.0%)`, CPU utilization as `0.0%`, Network as `0 B`, and uptime as empty.
3. **Zero CPU Sampling on Instantaneous Calls**:
   - `psutil.cpu_percent(interval=None)` without a calibration call or with `interval=0.05` returned `0.0%` on fast multi-core systems (e.g. 32-thread Intel i9-14900HX).
4. **Missing Hardware Model and Node Identification**:
   - The telemetry engine only reported generic logical core counts without resolving the host CPU brand model or distinguishing host vs Docker container environments.
5. **Static UI Lacking Live Telemetry Refresh**:
   - `src/pwd301/templates/admin/dashboard.html` rendered server health with hardcoded placeholders, lacking DOM IDs, dynamic JavaScript fetching, or auto-polling.
   - `frontend-preview/assets/js/views/admin.js` used simulated static numbers and did not attempt to query backend telemetry APIs.

## Key Changes
1. **Cross-Platform Telemetry Engine (`src/pwd301/services/operations_service.py`)**:
   - Added `psutil>=6.0.0,<8` to `requirements.txt` and `pyproject.toml` (mypy overrides).
   - Enhanced `get_real_system_telemetry()` to read CPU model:
     - Linux: `/proc/cpuinfo` (`model name`).
     - Windows: Registry `HARDWARE\DESCRIPTION\System\CentralProcessor\0` (`ProcessorNameString`).
   - Improved CPU percent calculation with calibrated sample interval (`0.1s`) and load average normalization fallback (`getattr(os, "getloadavg", None)`).
   - Added zero-dependency Linux stdlib fallbacks:
     - Memory: `/proc/meminfo` (`MemTotal`, `MemAvailable`, `Buffers`, `Cached`).
     - Uptime: `/proc/uptime`.
     - Network I/O: `/proc/net/dev`.
   - Added node environment detection (`node_label` = `Docker (<container_id>)` vs host).
2. **Analytics Service Key Compatibility (`src/pwd301/services/analytics_service.py`)**:
   - Added dual dictionary key support (`total`, `active`, `completed`, `clean_files`, `quarantined_files` alongside existing canonical keys) ensuring seamless Jinja template and API contract compatibility.
3. **Live Interactive Admin Dashboard (`src/pwd301/templates/admin/dashboard.html`)**:
   - Assigned dedicated DOM IDs to all hardware telemetry metrics (`telem-node-label`, `telem-cpu-percent`, `telem-ram-label`, `telem-disk-free`, `telem-net-traffic`, etc.).
   - Added "Làm mới phần cứng" action button with spin animation.
   - Integrated client-side asynchronous JavaScript `refreshServerTelemetry()` with 15-second background auto-polling.
4. **Frontend Preview Prototype (`frontend-preview/assets/js/views/admin.js`)**:
   - Updated section title to include "Trung tâm Điều hành & Quản trị Hệ thống — Tài nguyên Máy chủ".
   - Converted `refreshDashboardData()` to query live `/admin/telemetry` or `/api/admin/telemetry` when running against a live backend, falling back gracefully to mock simulation when offline.

## Verification Record
- **Unit Tests (`tests/unit/test_operations_service.py`)**: 15/15 passed (including `test_get_real_system_telemetry_keys`, `node_label`, `cpu.model`, `uptime`).
- **API Tests (`tests/api/test_analytics_api.py`, `tests/api/test_operations_api.py`)**: 10/10 passed (including `test_admin_telemetry_endpoints` and `test_admin_dashboard_web_renders_hardware_telemetry`).
- **Regression Suite (`tests/api/test_web_ui_flow_fixes.py`)**: 21/21 passed.
- **Ruff & Mypy**: 0 lint errors, 0 type errors across all touched files.
- **Live Docker Container Verification (`http://localhost:5000`)**:
  - `GET /admin/telemetry`: HTTP 200 OK returning real hardware metrics:
    - CPU: `32 vCPU • Intel(R) Core(TM) i9-14900HX`
    - RAM: `3.9 / 15.5 GB (25.0%)`, `11.6 GB khả dụng`
    - Disk: `5.4 GB / 1006.9 GB (0.6%)`, `950.2 GB còn trống`
    - Network: `Gửi: 180 KB • Nhận: 148 KB`
    - Node: `Docker (d799e6b0f3f6)`
    - OS: `Linux 6.18.33.2-microsoft-standard-WSL2`
  - `GET /admin/dashboard`: HTTP 200 OK with server telemetry wired to DOM and auto-refreshing.

---

# TASK-035 — AI Assistant LMS Scope Enforcement & Security Fortress

**Status:** DONE  
**Assignee:** Principal AI Architect & Security Engineer  
**Started Date:** 2026-09-12  
**Completed Date:** 2026-09-12  

## Goal
Resolve the critical vulnerability where the AI Assistant answered any arbitrary user prompt regardless of whether the question was within the academic LMS scope (Web development, Python, SQL, course material, computer science) or out-of-scope (cooking, entertainment, politics, horoscopes), and failed to proactively block malicious prompts (SQL injection payloads, DDoS attacks, server exploit instructions, prompt injection, DAN jailbreak, database/secret extraction).

## Root Cause Analysis
1. **Unbounded Prompt Pass-Through**:
   - In `src/pwd301/services/ai_service.py` and `gemini_service.py`, user prompts were passed directly to Gemini without deterministic boundary classification or pre-execution scope verification.
2. **Missing Out-of-Scope Domain Exception & Telemetry**:
   - The platform lacked a dedicated `AIOutOfScopeError` and domain classification logic to differentiate pedagogical refusals from security exploits.
   - Database telemetry table `ai_requests` check constraints (`ck_ai_requests_2`: `scope_decision IN ('IN_SCOPE','OUT_OF_SCOPE','MIXED','AMBIGUOUS')` and `ck_ai_requests_3`: `status IN ('SUCCEEDED','REFUSED','FAILED','TIMEOUT','BYPASSED')`) were not being utilized to record refusal metrics.
3. **Absence of Unified Pedagogical Refusal vs Security Defense**:
   - Web chat (`/student/ai/chat`) and REST API (`/api/ai/chat`) lacked defensive boundaries to return helpful pedagogical redirections for harmless out-of-scope queries while strictly blocking and raising security alerts (`PROMPT_INJECTION_DETECTED`, `SECURITY_VIOLATION`) for adversarial jailbreak attempts.

## Key Changes
1. **High-Performance Scope Classifier (`src/pwd301/services/scope_classifier.py`)**:
   - Engineered dual-tiered classifier with zero external dependency regex heuristics and semantic token classification:
     - `MALICIOUS` / `SECURITY_VIOLATION`: Detects SQL injection exploit vectors, DDoS tool crafting, reverse shells, password harvesting, prompt extraction/DAN mode, and privilege escalation.
     - `OUT_OF_SCOPE`: Flags cooking recipes, gossip, astrology, poetry/creative non-academic writing, cryptocurrency trading, betting/gambling, politics.
     - `IN_SCOPE_ACADEMIC`: Approves LMS-related topics (Python, SQL, HTML/CSS/JS, algorithms, Big-O, database architecture, defensive web security concepts, study methodologies) and courteous greetings.
   - Distinct classification between offensive exploits (malicious) vs defensive security learning (academic in-scope).
2. **Domain Exceptions & Error Handler Mapping (`src/pwd301/services/exceptions.py`, `src/pwd301/__init__.py`)**:
   - Added `AIOutOfScopeError(AIValidationError)` (`code="OUT_OF_SCOPE"`).
   - Added `AISecurityViolationError(AIPromptInjectionError)` (`code="SECURITY_VIOLATION"`).
   - Mapped exceptions to HTTP 400 with standardized JSON envelopes per `10_AI_API.md`.
3. **Gemini Engine Hardening (`src/pwd301/services/gemini_service.py`)**:
   - Embedded deterministic scope classifier check into `detect_prompt_injection()`.
   - Updated `MockGeminiClient` and `RealGeminiClient` to reject out-of-scope and malicious queries before executing network calls.
   - Enhanced `systemInstruction` with strict LMS boundary constraints, pedagogical framing, and Vietnamese pedagogical refusal templates.
4. **AI Service Orchestration & Telemetry Compliance (`src/pwd301/services/ai_service.py`)**:
   - Intercepted prompts at entry of `send_chat_message()`:
     - `ScopeDecision.MALICIOUS`: Records `ai_requests` (`route_type='CLASSIFIER'`, `scope_decision='OUT_OF_SCOPE'`, `status='REFUSED'`, `error_code='PROMPT_INJECTION_DETECTED'`) and raises `AIPromptInjectionError`.
     - `ScopeDecision.OUT_OF_SCOPE`: Records `ai_requests` (`route_type='CLASSIFIER'`, `scope_decision='OUT_OF_SCOPE'`, `status='REFUSED'`, `error_code='OUT_OF_SCOPE'`). If `raise_out_of_scope=True`, raises `AIOutOfScopeError`; otherwise returns pedagogical redirect guidance message.
5. **Route Handlers (`src/pwd301/blueprints/student/routes.py`, `src/pwd301/blueprints/api_ai/routes.py`)**:
   - `student_ai_chat`: Gracefully handles `AIPromptInjectionError` and `AIOutOfScopeError` returning structured pedagogical responses with `status='refused'`.
   - `unified_chat_api` & `send_message_api`: Passes `raise_out_of_scope=True` for REST API clients to enforce HTTP 400 `OUT_OF_SCOPE` errors adhering to `10_AI_API.md`.

## Verification Record
- **Scope Classifier Tests (`tests/unit/test_ai_scope_classifier.py`)**: 44/44 passed.
- **Scope Enforcement & Telemetry Tests (`tests/security/test_ai_scope_enforcement.py`)**: 8/8 passed.
- **AI Security Tests (`tests/security/test_ai_security.py`)**: 8/8 passed.
- **AI API Tests (`tests/api/test_ai_api.py`)**: 8/8 passed.
- **AI Service Unit Tests (`tests/unit/test_ai_service.py`)**: 17/17 passed.
- **Linter & Type Checker**: `ruff check`, `ruff format --check`, and `mypy src` (84 source files) passed with 0 errors.

---

# TASK-036 — Session-Persistent Web Entrance Motion & Defensive UI Flicker Elimination

**Status:** DONE  
**Assignee:** Principal Frontend Architect & UI/UX Design Systems Engineer  
**Started Date:** 2026-09-13  
**Completed Date:** 2026-09-13  

## Goal
Resolve the UI defect where navigation back and forth across routes, views, tabs, or components caused the entire user interface (topbar, sidebar, page headers, metric cards, main cards, tables) to repeatedly flash (`autoAlpha: 0`) and pop/rise up (`y: 20 -> 0`). Enforce the strict product design requirement that the entrance motion occurs strictly ONCE upon initial entrance to the web platform in a user session, with all subsequent navigations and component interactions rendering clean, instant, and flicker-free.

## Root Cause Analysis
1. **Unconditional Re-Execution on Page Load & View Routing**:
   - `PWDMotion.animatePageEntrance()` in `src/pwd301/static/js/motion.js` and `frontend-preview/assets/js/motion.js` created a GSAP timeline that animated `.app-topbar`, `.app-sidebar .sidebar-item`, `.page-header`, `.hero-welcome-card`, `.metric-card`, and `.app-main-workspace .card` from `autoAlpha: 0, y: 20`.
   - In Flask multi-page navigation (`base.html`), every page change reloaded `motion.js` and re-triggered `PWDMotion.init()` -> `animatePageEntrance()`, causing elements to flash invisible and float up on every click.
   - In `frontend-preview/assets/js/router.js`, `router.handleRouting()` explicitly called `animatePageEntrance()` on every `hashchange`, repeatedly triggering the entrance timeline on every view switch.
2. **Missing Initialization Idempotency Guard**:
   - `PWDMotion.init()` was called both by `motion.js` on `DOMContentLoaded` and by `app_shell.js`, executing `animatePageEntrance()` twice concurrently on initial load.
3. **ScrollTrigger Batch Reveal Flicker**:
   - `initScrollTriggers()` used `ScrollTrigger.batch` on `.syllabus-row, .course-card, .app-table tbody tr` with `{ autoAlpha: 0, y: 16 }`, hiding and popping up table rows and course cards during scroll and view switches.

## Key Changes
1. **Session-Persistent Entrance State Tracking (`src/pwd301/static/js/motion.js`, `frontend-preview/assets/js/motion.js`)**:
   - Added `ENTRANCE_STORAGE_KEY = 'pwd301_initial_entrance_done'`.
   - Added `hasEntered()`: checks `sessionStorage.getItem(ENTRANCE_STORAGE_KEY) === 'true'` with in-memory `_entranceCompleted` fallback.
   - Added `markEntered()`: persists entrance state to `sessionStorage` and in-memory flag.
   - Added `resetEntrance()`: clears the session key for testing and re-entrance scenarios.
2. **Strict Single-Entrance Execution & Clean Subsequent Display (`animatePageEntrance()`)**:
   - If `this.hasEntered() || prefersReduced`: skips timeline creation and immediately invokes `window.gsap.set(entranceTargets, { autoAlpha: 1, x: 0, y: 0, scale: 1, clearProps: 'transform,opacity,visibility' })` ensuring instant, un-animated, flicker-free rendering.
   - If not yet entered: marks entrance immediately and plays timeline once. On timeline `onComplete`, clears inline transform/opacity properties via `clearProps` so native CSS layout and hover states remain clean.
3. **Idempotent Initialization Guard (`init()`)**:
   - Added `if (this.initialized) return;` at the beginning of `PWDMotion.init()`, preventing redundant duplicate timeline triggers from multiple callers.
4. **ScrollTrigger Batch Reveal Optimization (`initScrollTriggers()`)**:
   - When `this.hasEntered()` is true, immediately clears inline properties and returns without registering redundant batch triggers.
5. **Head Pre-Paint Theme & Sidebar Restoration (`base.html`, `frontend-preview/index.html`)**:
   - Injected synchronous inline JavaScript in `<head>` before stylesheets, restoring `data-theme`, `data-bs-theme`, and `sidebar-collapsed` prior to first paint.
   - Completely eliminated the white flash (FOUC) when navigating pages in Dark Mode.
6. **Full Retention of Rich Hover Micro-Interactions (`motion.js`, `app.css`)**:
   - Overrode `.tab-pane.fade { transition: none !important; }` in CSS to make tab switching instant and flicker-free.
   - Preserved and verified all rich hover micro-interactions across graphic areas:
     - Card floating elevation (`y: -5`) and smooth 3D tilt (`rotationX`, `rotationY`) on mouseenter / mousemove.
     - Button elastic press feedback (`scale: 0.95 -> 1, back.out(2)`).
     - Table rows luminous hover transition (`x: 5`).
     - Ambient floating and interactive rotation for the AI octopus mascot launcher.
7. **Cache-Busting Version Bump**:
   - Incremented script query strings to `motion.js?v=2.3.0`, `theme.js?v=2.2.0`, and CSS to `app.css?v=1.3.2` / `app.css?v=1.2.0`.

## Verification Record
- **Live Chrome DevTools E2E Verification (`http://localhost:5000`)**:
  - Initial visit: `hasEntered()` is recorded as `true`, `sessionStorage` updated to `'true'`.
  - Page Transitions (Navigation between `/student/dashboard` -> `/student/my-learning` -> `/admin/instructor-applications` in Dark Mode):
    - Zero white flash (FOUC eliminated via head pre-paint script).
    - Zero graphic entrance re-loading on subsequent navigations (`isTopbarTweening: false`, `isFirstCardTweening: false`, `cardTransform: "none"`, `cardOpacity: "1"`).
  - Hover & Graphical Micro-Interactions:
    - Card hover verified: `cardHoverTweensActive: 3` (`y: -5`, `rotationX`, `rotationY` active on mouseenter / mousemove).
    - Button click verified: `btnTweenCount: 2` (elastic press feedback active).
    - Table row hover verified: `rowTweenCount: 1` (`x: 5` slide hover active).
  - Tab switching on `/admin/instructor-applications` (`Chờ duyệt`, `Đã duyệt`, `Đã từ chối`, `Tất cả hồ sơ`):
    - Completely clean, instant, zero fade delay or flickering.
- **Frontend Preview Prototype Verification (`file:///E:/PWD301/frontend-preview/index.html`)**:
  - Pre-paint `<head>` script active.
  - Hover on prototype cards verified: `prototypeCardHoverTweens: 3` (`y`, `rotationX`, `rotationY`).
  - Rapid route transitions across `#/student/my-learning`, `#/instructor/dashboard`, `#/instructor/courses`:
    - Zero graphic entrance re-loading on subsequent routes, instant clean view renders.
- **Repository Checks**:
  - `python scripts/repo_check.py`: PASS.
  - `.\.venv\Scripts\ruff.exe check src tests scripts`: PASS (0 errors).
  - `.\.venv\Scripts\ruff.exe format --check src tests scripts`: PASS (200 files formatted).
  - `python -m compileall -q src tests scripts`: PASS (0 errors).
  - `tests/api/test_web_ui_flow_fixes.py` & `tests/api/test_student_portal_ui.py`: 37/37 passed (100%) in 24.86s.

---

# TASK-037 — Instructor Course Creation Web Flow Hardening, Filtered Unique Constraints & Graceful Error Handling

**Status:** DONE  
**Assignee:** Principal Fullstack & Database Architect  
**Started Date:** 2026-09-13  
**Completed Date:** 2026-09-13  

## Goal
Resolve the critical `500 INTERNAL_ERROR` bug preventing instructors from creating courses at `POST /instructor/courses`. Reconcile database constraints with the canonical Database Architecture (`002_course_learning.sql`) to support soft-delete friendly filtered unique indexes (`WHERE deleted_at IS NULL`), implement robust exception handling in the web route and service layers, and upgrade the course creation modal with professional academic fields (`category`, `difficulty`, `capacity`) aligned with `frontend-preview/`.

## Root Cause Analysis
1. **Unconditional Database Constraints Conflicting with Soft-Deletes**:
   - Initial Alembic migration `0001` declared `sa.UniqueConstraint` on `(course_code_normalized)` and `(title_normalized)` on table `courses`, generating auto-named SQL Server unique constraints (e.g., `UQ__courses__A0CC57B6FB74DC88`).
   - Canonical architecture `002_course_learning.sql` explicitly requires filtered unique indexes:
     `CREATE UNIQUE NONCLUSTERED INDEX ux_courses_course_code_active ON courses(course_code_normalized) WHERE deleted_at IS NULL;` and `ux_courses_title_active ON courses(title_normalized) WHERE deleted_at IS NULL;`.
   - Because a previous course (ID 10002, "Khóa học làm người", code HUM101) was in soft-deleted state (`lifecycle_state = 'TRASH'`, `deleted_at IS NOT NULL`), creating a course with the same title or code triggered a database constraint violation.
2. **Missing Route-Level Exception Handling in Web Blueprint**:
   - `create_course_route` in `src/pwd301/blueprints/instructor/routes.py` called `create_course(...)` without a `try...except` block.
   - Any validation error, state violation, or database integrity error bubbled unhandled to Flask's global 500 error handler, displaying a generic crash screen to instructors.
3. **Missing Category, Difficulty & Capacity Fields in Creation Modal**:
   - The instructor courses view modal only included title, course code, and summary, missing key academic attributes present in the canonical UI prototype (`frontend-preview/`).

## Key Changes
1. **Database Migration (`migrations/versions/a1b2c3d4e5f7_0004_fix_courses_unique_filtered_indexes.py`)**:
   - Created dynamic T-SQL inspection to locate and drop any unconditional unique constraints on `courses` columns `course_code_normalized` and `title_normalized`.
   - Dropped legacy unconditional unique indexes if present.
   - Created canonical filtered unique indexes `ux_courses_course_code_active` and `ux_courses_title_active` with `WHERE deleted_at IS NULL`.
   - Upgraded SQL Server via `flask db upgrade` to revision `a1b2c3d4e5f7`.
2. **Container Configuration (`docker-compose.yml`)**:
   - Added `./migrations:/app/migrations` volume mount to `pwd301_web` container to ensure immediate migration visibility.
3. **Service Layer Hardening (`src/pwd301/services/course_service.py`)**:
   - Wrapped `sess.flush()` and `sess.commit()` inside `create_course` and `update_course` in a `try...except sa.exc.IntegrityError` block.
   - Converts SQL Server unique constraint violations into domain-level `CourseAlreadyExistsError` with descriptive error messages.
4. **Web Blueprint Resilience (`src/pwd301/blueprints/instructor/routes.py`)**:
   - Wrapped `create_course_route` and `update_course_route` in comprehensive exception handlers catching:
     - `CourseValidationError`: flashes warning with validation requirements.
     - `CourseAlreadyExistsError`: flashes error notifying user of duplicate code or active title.
     - `CourseStateViolationError` & `ForbiddenError`: flashes permission or lifecycle notice.
     - `sa.exc.IntegrityError`: catches unexpected DB constraints gracefully.
   - Automatically returns redirect to `/instructor/courses` with flash message for web forms, or structured JSON for AJAX callers.
5. **UI Creation Modal Upgrade (`src/pwd301/templates/instructor/courses.html`)**:
   - Added `category` select dropdown (Computer Science, Artificial Intelligence, Cybersecurity, Software Engineering, etc.).
   - Added `difficulty` radio group (`BEGINNER`, `INTERMEDIATE`, `ADVANCED`).
   - Added `capacity` number input (default 50 students).
   - Preserved dark-mode and light-mode tokens and cohesive card styling.
6. **Automated TDD Test Suite (`tests/api/test_instructor_course_web_flow.py`)**:
   - `test_create_course_reusing_soft_deleted_title`: verifies reusing code/title of soft-deleted courses succeeds.
   - `test_instructor_web_create_course_success`: verifies full form submission with category, difficulty, capacity.
   - `test_instructor_web_create_course_duplicate_active_title_graceful_flash`: verifies duplicate active title flashes warning without 500 error.
   - `test_instructor_web_create_course_db_integrity_error_graceful_flash`: verifies DB integrity exceptions result in clean flash messages.

## Verification Record
- **Pytest Verification**:
  - `tests/api/test_instructor_course_web_flow.py`: 4 passed in 2.12s.
  - `tests/api/test_instructor_application_web_flow.py`: 8 passed in 5.20s.
  - Total: 12 passed, 0 failed.
- **Static Analysis & Formatting**:
  - `.\.venv\Scripts\ruff.exe check src tests migrations`: All checks passed (0 errors).
  - `.\.venv\Scripts\ruff.exe format --check src tests migrations`: 195 files formatted cleanly.
  - `.\.venv\Scripts\mypy.exe src`: Success: no issues found in 84 source files.
  - `python scripts/repo_check.py`: All checks PASSED.
- **Docker Container & MS SQL Server Verification**:
  - `docker exec pwd301_web flask db current`: Current revision is `a1b2c3d4e5f7 (head)`.
  - Filtered indexes verified directly in SQL Server sys catalogs.
- **Live Browser & DevTools Verification (`http://localhost:5000`)**:
  - Instructor login (`instructor1@pwd301.local`): HTTP 302 -> `/instructor/courses`.
  - Created course `AI401` ("Trí Tuệ Nhân Tạo & Deep Learning Thực Chiến") with category "Trí tuệ nhân tạo", difficulty "Nâng cao", capacity 60: successfully created, badge rendered, card added to grid.
  - Re-created course "Khóa Học Làm Người" (HUM101): successfully created, proving soft-delete filtered index resolution.
  - Zero 500 errors observed.

---

# TASK-038 — Course Settings Form 405 Method Not Allowed Resolution & Publishing Workflow Direct Actions

**Status:** DONE  
**Assignee:** Principal Fullstack & Systems Architect  
**Started Date:** 2026-09-13  
**Completed Date:** 2026-09-13  

## Goal
Resolve the `405 METHOD_NOT_ALLOWED` error encountered when instructors/admins update course settings or trigger publishing operations from `http://localhost:5000/instructor/courses/<course_id>/manage?tab=settings`. Enable seamless end-to-end course publishing transitions (`DRAFT -> SUBMITTED_FOR_REVIEW -> APPROVED -> PUBLISHED`) with Admin fast-track support and informative guidance for draft courses.

## Root Cause Analysis
1. **HTTP Method Mismatch on Course Update Route**:
   - `update_course_route` in `src/pwd301/blueprints/instructor/routes.py` had `@instructor_bp.route("/courses/<course_id>", methods=["PATCH", "PUT"])`, omitting `"POST"`.
   - The settings tab form in `src/pwd301/templates/instructor/course_manage.html` submitted via standard browser HTML `<form method="POST" action="/instructor/courses/{{ course.public_id }}">`.
   - Submitting the form sent `POST /instructor/courses/<course_id>`, which Flask immediately rejected with `405 METHOD_NOT_ALLOWED`.
2. **Missing Form Field Mapping for Capacity**:
   - The settings form had `name="max_enrollments"` whereas the domain model and service layer expect `capacity`.
   - Empty input strings (e.g. `""` for optional numeric fields) caused value conversion issues.
3. **Workflow Friction in Course Publishing**:
   - The "Quy trình xuất bản khóa học" card in the settings tab only displayed informative text, lacking direct action buttons to trigger review submission or publishing.
   - Calling `/publish` on a `DRAFT` course raised state machine violations instead of providing clear guidance or Admin fast-track execution.

## Key Changes
1. **Web Route Layer (`src/pwd301/blueprints/instructor/routes.py`)**:
   - Updated `update_course_route` decorator to `@instructor_bp.route("/courses/<course_id>", methods=["POST", "PATCH", "PUT"])`.
   - Added automatic field mapping from `max_enrollments` to `capacity` and normalized empty string values to `None`.
   - Enhanced `publish_course_route`:
     - If actor has `ADMIN` privileges and course is in `DRAFT` or `SUBMITTED_FOR_REVIEW`: automatically executes valid audit-logged state machine transitions (`DRAFT -> SUBMITTED_FOR_REVIEW -> APPROVED -> PUBLISHED`) without error.
     - If actor is an instructor and course is `DRAFT`: returns a user-friendly flash warning ("Khóa học đang ở trạng thái Bản thảo. Bạn cần bấm 'Gửi Admin xét duyệt' trước khi xuất bản.") and redirects cleanly to the course hub without crashing.
2. **Templates & UI (`src/pwd301/templates/instructor/course_manage.html` & `courses.html`)**:
   - Aligned settings form fields with `capacity` and added `difficulty` selection (`BEGINNER`, `INTERMEDIATE`, `ADVANCED`).
   - Added an interactive "Thao tác xuất bản" workflow action box directly inside the "Quy trình xuất bản khóa học" timeline card:
     - `DRAFT`: Primary button "Gửi Admin xét duyệt" + Admin quick-publish button.
     - `SUBMITTED_FOR_REVIEW`: Button "Hủy gửi duyệt" + Admin approve & publish button.
     - `APPROVED`: Button "Xuất bản khóa học ngay".
     - `PUBLISHED`: Status banner "Khóa học đã xuất bản & đang hoạt động".
   - Added Admin quick-publish actions in the courses list (`courses.html`) dropdown menu.

## Verification Record
- **Pytest Suite (`tests/api/test_instructor_course_web_flow.py`)**:
  - `test_post_course_settings_update_route_success`: PASS (reproduced 405 before fix, passed 200 after fix).
  - `test_instructor_publish_draft_course_warning`: PASS (clean warning flash, no 405/500).
  - `test_admin_publish_draft_course_direct_success`: PASS (transitions to PUBLISHED cleanly).
  - Total instructor test suite: **15 passed, 0 failed** in 6.30s.
- **Static Analysis & Formatting**:
  - `.\.venv\Scripts\ruff.exe check src tests`: PASS (0 errors).
  - `.\.venv\Scripts\ruff.exe format --check src tests`: PASS (194 files already formatted).
  - `.\.venv\Scripts\mypy.exe src`: PASS (0 errors in 84 source files).
  - `python scripts/repo_check.py`: PASS.
- **Live Docker & Chrome DevTools Verification (`http://localhost:5000`)**:
  - Navigated to `manage?tab=settings` of course `HUM101` (`c30f8478-5c1b-4fe8-84c9-1c641e8fe561`).
  - Clicked "Lưu thay đổi": Saved successfully, returned toast "Cập nhật thông tin khóa học thành công", zero 405 errors.
  - Clicked "Xuất bản ngay (Admin)": Successfully published course, updated badge to `HUM101 Đang mở (PUBLISHED)`.
  - Checked `/instructor/courses` grid: Course card renders with green `Đang mở` badge and full functional controls.

