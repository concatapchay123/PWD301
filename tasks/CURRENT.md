# TASK-027 — Comprehensive Architecture, Security & Production Hardening

**Status:** DONE  
**Assignee:** Principal Security Architect & Lead Backend Engineer  
**Completed Date:** 2026-09-11  

---

## Goal
Resolve all critical security vulnerabilities, abuse vectors, and test blind spots identified during the production and security hardening audit across authentication, RBAC authorization, IDOR protection, brute-force login lockout, AI chat and email rate limiting, CSRF boundary defense, file upload DoS mitigation, RFC 6266 filename encoding, progress percent null safety, database restore concurrency control, and standard HTTP security headers.

---

## Source-of-Truth Documents
- `AGENTS.md` (Operational contract, Fail-closed invariants, Zero PK Leakage, CSRF protection)
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/01_BUSINESS_RULE_CATALOG.md` (73 Business Rules)
- `docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/security/01_THREAT_MODEL.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/security/02_AUTHENTICATION_AND_PASSWORDS.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/security/03_AUTHORIZATION_AND_ROLES.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/security/04_SESSION_AND_TOKEN_MANAGEMENT.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/operations/04_DATABASE_BACKUP_RESTORE.md`
- `docs/decisions/ADR-001-session-cookie-vs-bearer-jwt.md`
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
2. Eliminate IDOR & privilege escalation in attempt essay grading and regrading retry routes (restricted to managing instructor and admin).
3. Restrict AI question drafting/generation and knowledge ingestion to instructors.
4. Eliminate ADR-002 internal `BIGINT` PK leakage in course prerequisite routes.
5. Decouple dual registration of `admin_bp` by introducing a dedicated, pure-JSON, JWT-only `api_admin_bp` under `/api/admin`.
6. Enforce file upload DoS check (`Content-Length >= 1 GB`) before disk streaming.
7. Encode `Content-Disposition` using RFC 6266 (`filename*=UTF-8''...`) to support Vietnamese diacritics without `UnicodeEncodeError`.
8. Guard all `current_progress_percent` float conversions with `or 0.0` for null safety.
9. Harden database restore with process concurrency lock (`_restore_lock`) and in-memory fast-path 503 handling during restore.
10. Restrict `/auth/logout` to POST-only to prevent GET-based CSRF logout attacks.
11. Implement thread-safe sliding-window rate limiting & lockout engine (`rate_limit_service.py`):
    - Brute-force login lockout: max 5 failed attempts per minute per IP or email (returns 429 `RATE_LIMIT_EXCEEDED` with `Retry-After`).
    - AI chat rate limiting: max 20 requests/minute per authenticated user (returns 429 `RATE_LIMIT_EXCEEDED`).
    - Email dispatch rate limiting: max 30 emails/minute per recipient (raises `EmailRateLimitExceededError` -> 429 `RATE_LIMIT_EXCEEDED`).
12. Add standard HTTP security headers middleware (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, `Content-Security-Policy`).
13. Add negative security tests in `tests/security/test_security_hardening.py` covering AC-SEC-01 through AC-SEC-07.

---

## Out of Scope
- Major database schema alterations or changing SQL Server data types.
- Introducing distributed infrastructure (Redis, Celery, Kafka).

---

## Reuse / Existing-Code Inspection
- Reused `pwd301.services.authorization_service.require_course_manager` and `@instructor_required`.
- Reused `pwd301.services.jwt_auth_service.jwt_required` and token validation logic.
- Reused `pwd301.extensions.csrf.exempt` to exempt pure REST API blueprints cleanly without mutating private attributes.
- Reused existing domain error handlers and error response envelope.
- Reused `EmailRateLimitExceededError` and `AIQuotaExceededError` mapped to HTTP 429.

---

## Planned Changes
1. `src/pwd301/services/rate_limit_service.py`: [NEW] Sliding window rate limiter & lockout manager.
2. `src/pwd301/blueprints/auth/routes.py`: Add login lockout check & failure recording; change `/logout` to POST only.
3. `src/pwd301/blueprints/api_auth/routes.py`: Add REST login lockout check & failure recording.
4. `src/pwd301/blueprints/api_ai/routes.py`: Add AI chat quota rate limiting; add role decorators.
5. `src/pwd301/services/email_service.py`: Add recipient dispatch rate limiting to `enqueue_email`.
6. `src/pwd301/__init__.py`: Add standard HTTP security headers in `after_request`; register and exempt `api_admin_bp`.
7. `src/pwd301/services/operations_service.py`: Add non-blocking restore lock and in-memory fast-path 503 check.
8. `src/pwd301/blueprints/api_lessons/routes.py`: Add `@jwt_required`, `@student_required`, `@instructor_required`.
9. `src/pwd301/blueprints/api_attempts/routes.py`: Add `@instructor_required` to grading and regrading endpoints.
10. `src/pwd301/blueprints/instructor/routes.py`: Enforce ADR-002 UUID in prerequisites.
11. `src/pwd301/blueprints/api_courses/routes.py` & `api_files/routes.py`: Early Content-Length check; RFC 6266 `filename*` encoding.
12. `tests/security/test_security_hardening.py`: Add 22 comprehensive negative security tests.

---

## Security / Authorization Impact
- Closes privilege escalation allowing students to grade exams or ingest RAG data.
- Closes ambient cookie CSRF on admin routes by enforcing Bearer JWT on all `/api/admin/*` endpoints.
- Closes image/link CSRF logout via GET `/auth/logout`.
- Prevents brute-force credential stuffing via local IP/email lockout.
- Prevents resource exhaustion / disk fill DoS from oversized multipart uploads.
- Prevents database connection deadlocks during physical restore operations.
- Enforces strict HTTP security headers across all responses.

---

## Database / Migration Impact
- Zero schema changes required. All database tables and columns remain untouched.

---

## Concurrency / Idempotency Impact
- Single-threaded database restore execution enforced via `_restore_lock.acquire(blocking=False)`.
- In-memory fast-path returns 503 immediately to incoming non-admin requests while restore executes.
- Thread-safe sliding window tracking under `threading.Lock` for all rate limiting operations.

---

## Deletion and Simplification List

| Candidate | Classification | Reason | Action |
|---|---|---|---|
| Dual registration of `admin_bp` as `/api/admin` | REMOVE NOW | Allowed cookie auth on CSRF-exempt API endpoints, creating CSRF privilege escalation risk | Replaced with dedicated `api_admin_bp` requiring `@jwt_required` and `@admin_required` |
| `csrf._exempt_blueprints.add("api_admin")` hack | REMOVE NOW | Manipulated private internals of Flask-WTF CSRF extension | Replaced with official `csrf.exempt(api_admin_bp)` |
| Fallback internal integer PK in course prerequisites | REMOVE NOW | Violated ADR-002 zero internal PK leakage | Resolved prerequisite course to return public UUID |
| `GET` method on `/auth/logout` | REMOVE NOW | Vulnerable to cross-site image/link CSRF logout attacks | Restricted to `methods=["POST"]` only |
| Unbounded failed login attempts | REMOVE NOW | Vulnerable to brute-force credential attacks | Added local sliding-window lockout (5 attempts/min) |

---

## Ponytails / Deferred Debt
None. All security hardening issues and abuse controls have been fully implemented in code without deferred debt.

---

## Completion Report

### A. Scope and Sources Consulted
- `AGENTS.md` (Operational contract, Fail-closed invariants, Zero PK Leakage, CSRF protection)
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/01_BUSINESS_RULE_CATALOG.md` (73 Business Rules)
- `docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/security/` (SEC-001 through SEC-009)
- `docs/decisions/` (ADR-001, ADR-002, ADR-008, ADR-010)

### B. Reuse Decisions
- Reused existing domain exceptions `EmailRateLimitExceededError`, `AIQuotaExceededError`, and `ConflictError`.
- Reused Flask `after_request` middleware hook for zero-overhead security headers.
- Reused `threading.Lock` for thread-safe local in-memory sliding windows.

### C. Per-File Changes
- `src/pwd301/services/rate_limit_service.py`: Implemented thread-safe sliding window lockout, AI chat rate limit, email rate limit, and test isolation flush.
- `src/pwd301/blueprints/auth/routes.py`: Enforced login lockout (429) and failed attempt tracking; POST-only logout.
- `src/pwd301/blueprints/api_auth/routes.py`: Enforced REST login lockout (429) and failed attempt tracking.
- `src/pwd301/blueprints/api_ai/routes.py`: Enforced per-user chat quota rate limiting (429).
- `src/pwd301/services/email_service.py`: Enforced per-recipient outbound email dispatch rate limiting (429).
- `src/pwd301/__init__.py`: Configured standard HTTP security headers in `after_request`; registered `api_admin_bp`; exempt from CSRF.
- `src/pwd301/services/operations_service.py`: Added non-blocking restore lock and fast-path 503 handling.
- `src/pwd301/blueprints/api_admin/`: Dedicated pure-JSON JWT admin endpoints.
- `tests/security/test_security_hardening.py`: Added 22 comprehensive negative security tests.

### D. Deletion/Simplification List
- Removed dual blueprint registration and private CSRF set manipulation.
- Removed GET handler from logout route.
- Removed unrestricted login failure processing.

### E. Ponytails
None.

### F. Verification Actually Run
- `scripts/repo_check.py`: Passed (0 errors).
- `python -m compileall -q src tests scripts`: Passed (0 errors).
- `ruff check src tests scripts`: Passed (All checks passed).
- `ruff format --check src tests scripts`: Passed (170 files verified).
- `mypy src`: Passed (0 issues found in 82 source files).
- `pytest tests/security/test_security_hardening.py -v`: 22/22 passed in 11.41s.
- `pytest tests/security/ -v`: 193/193 passed in 138.89s.
- `pytest -q`: 728/728 passed in 474.60s (100% pass across entire test suite).

### G. Remaining Risks / Next Step
All AC-SEC-01 through AC-SEC-07 requirements and core invariants are strictly verified. Ready for TASK-028.
