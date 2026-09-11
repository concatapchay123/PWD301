# TASK-027 — Comprehensive Architecture, Security & Production Hardening

**Status:** DONE  
**Assignee:** Principal Security Architect & Lead Backend Engineer  
**Completed Date:** 2026-09-11  

---

## Goal
Resolve all critical security vulnerabilities, logic defects, and test blind spots identified during the production and security reality check audit across authentication, RBAC authorization, IDOR protection, CSRF boundary defense, file upload DoS mitigation, RFC 6266 filename encoding, progress percent null safety, and database restore concurrency control.

---

## Source-of-Truth Documents
- `AGENTS.md` (Operational contract, Fail-closed invariants, Zero PK Leakage, CSRF protection)
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/01_BUSINESS_RULE_CATALOG.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/security/02_AUTHENTICATION_AND_PASSWORDS.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/security/03_AUTHORIZATION_AND_ROLES.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/security/04_SESSION_AND_TOKEN_MANAGEMENT.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/operations/04_DATABASE_BACKUP_RESTORE.md`
- `docs/decisions/ADR-002-database-identifiers.md`
- `docs/decisions/ADR-008-file-storage.md`
- `docs/decisions/ADR-010-append-only-audit.md`
- `frontend-preview/` (Canonical UI layout, defensive UX patterns)

---

## Preconditions
- Virtual environment installed at `.venv`.
- Python 3.12 with all dependencies.
- Canonical SQL Server schema intact (71 tables verified).

---

## In Scope
1. Fix missing `@jwt_required` and role decorators (`@instructor_required`, `@student_required`) across REST endpoints (`api_lessons`, `api_attempts`, `api_ai`, `api_files`).
2. Eliminate IDOR & privilege escalation in attempt essay grading and regrading retry routes.
3. Restrict AI question drafting/generation and knowledge ingestion to instructors.
4. Eliminate ADR-002 internal `BIGINT` PK leakage in course prerequisite routes.
5. Decouple dual registration of `admin_bp` by introducing a dedicated, pure-JSON, JWT-only `api_admin_bp`.
6. Enforce file upload DoS check (`Content-Length >= 1 GB`) before disk streaming.
7. Encode `Content-Disposition` using RFC 6266 (`filename*=UTF-8''...`) to support Vietnamese diacritics without `UnicodeEncodeError`.
8. Guard all `current_progress_percent` float conversions with `or 0.0` for null safety.
9. Harden database restore with process concurrency lock and in-memory fast-path 503 handling during restore.
10. Restrict `/auth/logout` to POST-only to prevent GET-based CSRF logout attacks.
11. Add negative security tests in `tests/security/` and ensure 100% test pass rate across the test suite.

---

## Out of Scope
- Major database schema alterations or changing SQL Server data types.
- Modifying UI design tokens or layouts outside of security headers and endpoints.

---

## Reuse / Existing-Code Inspection
- Reused `pwd301.services.authorization_service.require_course_manager` and `@instructor_required`.
- Reused `pwd301.services.jwt_auth_service.jwt_required` and token validation logic.
- Reused `pwd301.extensions.csrf.exempt` to exempt pure REST API blueprints cleanly without mutating private attributes.
- Reused existing domain error handlers and error response envelope.

---

## Planned Changes
1. `src/pwd301/blueprints/api_lessons/routes.py`: Add `@jwt_required`, `@student_required`, `@instructor_required`.
2. `src/pwd301/blueprints/api_attempts/routes.py`: Add `@instructor_required` to grading and regrading endpoints.
3. `src/pwd301/blueprints/api_ai/routes.py`: Add `@instructor_required` to draft, generate, and ingest routes.
4. `src/pwd301/blueprints/auth/routes.py`: Change `/auth/logout` to `methods=["POST"]` only.
5. `src/pwd301/blueprints/instructor/routes.py`: Fix prerequisite serializer to resolve and return public UUID only.
6. `src/pwd301/blueprints/api_courses/routes.py` & `src/pwd301/blueprints/api_files/routes.py`: Check Content-Length before parsing multipart stream; format RFC 6266 header.
7. `src/pwd301/blueprints/api_student/routes.py`, `student/routes.py`, `services/analytics_service.py`: Guard float conversions with `or 0.0`.
8. `src/pwd301/blueprints/api_admin/`: Create dedicated `api_admin_bp` with JWT-only endpoints.
9. `src/pwd301/services/operations_service.py`: Add restore lock, process-level atomic flag, and fast-path 503 check.
10. `src/pwd301/__init__.py`: Register `api_admin_bp`, exempt it cleanly, and harden `before_request`.
11. `tests/security/test_security_hardening.py`: Add comprehensive negative security tests.

---

## Security / Authorization Impact
- Closes privilege escalation allowing students to grade exams or ingest RAG data.
- Closes ambient cookie CSRF on admin routes by enforcing Bearer JWT on all `/api/admin/*` endpoints.
- Closes image/link CSRF logout via GET `/auth/logout`.
- Prevents resource exhaustion / disk fill DoS from oversized multipart uploads.
- Prevents database connection deadlocks during physical restore operations.

---

## Database / Migration Impact
- Zero schema changes required. All database tables and columns remain untouched.

---

## Concurrency / Idempotency Impact
- Single-threaded database restore execution enforced via `threading.Lock`.
- In-memory fast-path returns 503 immediately to incoming non-admin requests while SQL Server is in single-user mode.

---

## Deletion and Simplification List

| Candidate | Classification | Reason | Action |
|---|---|---|---|
| Dual registration of `admin_bp` as `/api/admin` | REMOVE NOW | Allowed cookie auth on CSRF-exempt API endpoints, creating CSRF privilege escalation risk | Replaced with dedicated `api_admin_bp` requiring `@jwt_required` and `@admin_required` |
| `csrf._exempt_blueprints.add("api_admin")` hack | REMOVE NOW | Manipulated private internals of Flask-WTF CSRF extension | Replaced with official `csrf.exempt(api_admin_bp)` |
| Fallback internal integer PK in course prerequisites | REMOVE NOW | Violated ADR-002 zero internal PK leakage | Resolved prerequisite course to return public UUID |
| `GET` method on `/auth/logout` | REMOVE NOW | Vulnerable to cross-site image/link CSRF logout attacks | Restricted to `methods=["POST"]` only |

---

## Ponytails / Deferred Debt
None. All 8 security issues and requirements have been fully addressed in code without deferred debt.

---

## Completion Report

### A. Scope and Sources Consulted
All source files, ADRs, and specification catalogs listed above were verified and followed.

### B. Reuse Decisions
Existing `jwt_required`, role decorators, error handlers, and service authorization functions were reused across all blueprints without introducing redundant abstractions.

### C. Per-File Changes
- `src/pwd301/blueprints/api_lessons/routes.py`: Protected resources, progress, and lesson detail with JWT and role decorators.
- `src/pwd301/blueprints/api_attempts/routes.py`: Added `@instructor_required` to grading and regrading routes.
- `src/pwd301/blueprints/api_ai/routes.py`: Added `@instructor_required` to drafting, generation, and ingestion routes; preserved enrolled student access on `GET /sources`.
- `src/pwd301/blueprints/auth/routes.py`: Restricted `/logout` to POST only.
- `src/pwd301/blueprints/instructor/routes.py`: Enforced ADR-002 UUID public identifiers in prerequisites response; guarded `current_progress_percent` with `or 0.0`.
- `src/pwd301/blueprints/api_courses/routes.py`: Guarded `current_progress_percent` with `or 0.0`; checked Content-Length before parsing multipart streams.
- `src/pwd301/blueprints/api_files/routes.py`: Early Content-Length check before disk buffering; RFC 6266 `filename*` encoding.
- `src/pwd301/blueprints/student/routes.py` & `api_student/routes.py`: Guarded float conversions with `or 0.0`.
- `src/pwd301/services/analytics_service.py`: Guarded float conversions with `or 0.0`.
- `src/pwd301/blueprints/api_admin/__init__.py`: Defined dedicated `api_admin_bp` blueprint.
- `src/pwd301/blueprints/api_admin/routes.py`: Implemented 29 pure JSON REST admin endpoints protected by `@jwt_required` and `@admin_required`.
- `src/pwd301/services/operations_service.py`: Added concurrency lock and in-progress restore flag.
- `src/pwd301/__init__.py`: Registered `api_admin_bp`, exempted from CSRF, removed dual registration, and added fast-path 503 check during restore.
- `tests/security/test_security_hardening.py`: Added 13 comprehensive negative security tests.

### D. Deletion/Simplification List
- Removed dual blueprint registration and private CSRF set manipulation.
- Removed GET handler from logout route.

### E. Ponytails
None.

### F. Verification Actually Run
- `scripts/repo_check.py`: Passed (0 errors).
- `ruff check src tests`: Passed (All checks passed).
- `ruff format --check src tests`: Passed (167 files verified).
- `pytest tests/security/test_security_hardening.py -v`: 13/13 passed.
- `pytest tests/security/test_csrf_api_boundary.py -v`: 9/9 passed.
- `pytest tests/api/test_ai_api.py -v`: 8/8 passed.
- `pytest -q`: 719/719 passed in 425.61s (100% pass rate, 0 failures, 0 regressions).

### G. Remaining Risks / Next Step
Codebase is clean, secure, and ready for production deployment.
