# Security & Operational Vulnerability Analysis — Handoff Report

**Agent**: `explorer_security_2`  
**Milestone**: Security & Operational Vulnerability Analysis  
**Date**: 2026-09-11  
**Target Repository**: PWD301 (`e:\PWD301`)  
**Scope**: All blueprints (`admin`, `instructor`, `student`, `auth`, `api_*`, `files`, `ai`, `import`), domain services, models, authorization decorators, and templates.

---

## 1. Observation

### 1.1 Automated Test Execution & Static Verification
The following test suites and static checks were executed against the codebase:
- **Command**: `.venv\Scripts\pytest tests/security -v`
  - **Result**: `225 passed in 111.83s`
  - **Coverage**: 27 security test modules including `test_rbac_and_idor.py`, `test_csrf_api_boundary.py`, `test_quarantine_fail_closed.py`, `test_file_authorization_idor.py`, `test_attempt_idor.py`, `test_analytics_idor.py`, `test_operations_security.py`, `test_paranoid_audit_hardening.py`.
- **Command**: `python scripts/repo_check.py`
  - **Result**: `[SUCCESS] Repository contract checks passed.`
- **Command**: `ruff check src/`
  - **Result**: `All checks passed!` (0 lint errors across all source files).

---

### 1.2 Vulnerability Findings

#### Finding SEC-01: Potential `NoneType` Dereference / Unhandled HTTP 500 in Course Import Listing
- **Category**: Error Handling & Availability / Robustness
- **Severity**: Medium
- **Locations**:
  1. `src/pwd301/blueprints/instructor/routes.py:1244-1245`:
     ```python
     1244:     course = _resolve_course(course_id, session=db.session)
     1245:     require_course_manager(actor, course.id, session=db.session)
     ```
  2. `src/pwd301/blueprints/api_courses/routes.py:757-758`:
     ```python
     757:     course = _resolve_course(course_id, session=db.session)
     758:     require_course_manager(actor, course.id, session=db.session)
     ```
  3. `src/pwd301/services/import_service.py:846-847`:
     ```python
     846:     course = _resolve_course(course_id, session=sess)
     847:     require_course_manager(actor, course.id, session=sess)
     ```
- **Observed Behavior**:
  `require_course_manager` (`src/pwd301/services/authorization_service.py:626-649`) is designed to accept `course_or_id: Course | int | uuid.UUID | str`, resolve the entity internally, and raise a clean `ResourceNotFoundError("Course not found.")` (HTTP 404) if non-existent.
  However, in the three routes above, the code calls `course = _resolve_course(course_id)` first and immediately accesses `course.id` on line 1245 / 758 / 847. If an attacker or client supplies an invalid or non-existent course ID, `_resolve_course` may return `None` (in `authorization_service.py:233`), causing an uncaught `AttributeError: 'NoneType' object has no attribute 'id'`, which crashes the worker with an unhandled HTTP 500 internal server error instead of a clean, audited HTTP 404.

#### Finding SEC-02: Missing `@instructor_required` RBAC Route Decorator on API Question Endpoints
- **Category**: Defense-in-Depth / RBAC Decorator Consistency
- **Severity**: Low (Informational)
- **Locations**:
  `src/pwd301/blueprints/api_questions/routes.py`:
  - Line 41-43: `patch_question_route`
  - Line 56-58: `trash_question_route`
  - Line 78-80: `delete_question_route`
  - Line 100-102: `restore_question_route`
- **Observed Behavior**:
  The endpoints are decorated with `@jwt_required` but omit `@instructor_required` or `@require_roles("INSTRUCTOR", "ADMIN")`.
  Downstream service logic (`question_bank_service.py` -> `require_question_manager`) enforces ownership and denies unauthorized actors with HTTP 403 `ForbiddenError`. However, lacking the route-level decorator allows authenticated students with valid JWT tokens to pass initial route routing and payload ingestion before being rejected at the service layer, violating the project's layered defense-in-depth practice.

---

### 1.3 Architectural Invariant Observations

#### A. Object-Level Authorization (BOLA / IDOR)
- **Service Layer Guard**: All resource access paths (courses, modules, lessons, questions, assessments, attempts, files, analytics, notifications) are guarded by fail-closed assertion helpers in `src/pwd301/services/authorization_service.py`:
  - `require_course_manager(user, course)`
  - `require_question_manager(user, question)`
  - `require_attempt_owner_or_manager(user, attempt)`
  - `can_access_student_data(instructor, student, course)`
  - `require_file_access(user, file_asset)`
- **Tenant Isolation**: Instructors can only view/modify their assigned courses (`course.instructor_id == user.id` or co-instructor association). Students can only view their own enrollments, attempts, submissions, and feedback.
- **Cross-Course Isolation**: Inquiries to student analytics, gradebooks, and enrollments verify that the target student is actively enrolled in a course managed by the requesting instructor (`src/pwd301/services/authorization_service.py:461-512`).

#### B. Mass Assignment Protections
- **Field Whitelisting**: Every service update function explicitly whitelists mutable fields:
  - `update_course`: Allows only `title`, `description`, `code`, `syllabus`, `is_published` (`src/pwd301/services/course_service.py`).
  - `update_lesson`: Allows only `title`, `content`, `order_index`, `is_published` (`src/pwd301/services/lesson_service.py`).
  - `update_question`: Restricts changes on published questions; forces creation of immutable `QuestionRevision` records (`src/pwd301/services/question_bank_service.py`).
  - `update_profile`: Prohibits role modification or active status tampering (`src/pwd301/services/session_auth_service.py`).
- **Role Elevation Barrier**: Roles can only be updated via Admin endpoints (`/api/admin/users/<id>/roles`), which strictly enforce `VALID_ROLE_COMBINATIONS` (`src/pwd301/services/authorization_service.py:126-140`).

#### C. Injection Protections
- **SQL Injection**: No string interpolation or unsanitized concatenation in SQL statements. All database access uses SQLAlchemy ORM query constructs or parameterized queries. Dialect identifier quoting (`dialect.identifier_preparer.quote_identifier`) is enforced on dynamic database operations.
- **Command Injection**: Zero instances of `subprocess.Popen`, `os.system`, `subprocess.run`, or shell execution in `src/`.
- **Server-Side Template Injection (SSTI)**: Zero calls to `render_template_string`. Jinja2 templates are strictly static files loaded from `src/pwd301/templates/`. Autoescaping is active by default.
- **XML External Entity (XXE) & Zip Bombs**: `src/pwd301/services/import_service.py` uses `defusedxml.ElementTree` and `defusedxml.minidom` for parsing QTI/GIFT and Word/XML files, mitigating Billion Laughs and XXE attacks. Zip compression limits (max 50 MB uncompressed size, max 100 entries) prevent zip bomb decompression denial of service.

#### D. Authentication & CSRF
- **Boundary Invariant (CSRF-Exempt API vs Session Boundary)**: `get_authenticated_actor()` (`src/pwd301/services/authorization_service.py:160-198`) inspects `request.path.startswith("/api/")`. If a request hits `/api/*` with session cookies but without a valid `Bearer` JWT, it is explicitly rejected with HTTP 401. This completely eliminates ambient cookie CSRF vulnerabilities on CSRF-exempt API routes.
- **Web UI CSRF**: All state-changing web UI routes (`POST`, `PUT`, `PATCH`, `DELETE`) enforce CSRF tokens via Flask-WTF (`csrf_token()` hidden inputs or `X-CSRFToken` request headers).
- **Safe Logout**: The `/auth/logout` route strictly requires `POST` (`src/pwd301/blueprints/auth/routes.py:136`), preventing browser pre-fetching or `<img>` tag logout attacks.
- **Token Security**: JWT tokens are signed with HMAC-SHA256 using `JWT_SECRET_KEY` (minimum 32 bytes enforced in production `src/pwd301/config.py:279-284`). Token rotation, refresh family revocation, and `auth_version` invalidation are fully implemented (`src/pwd301/services/jwt_auth_service.py`). Frontend inspection confirms tokens are never stored in `localStorage` (only `pwd301_theme` is stored).

#### E. Secret & Sensitive Data Leakage
- **Audit Masking**: `redact_sensitive_data` (`src/pwd301/services/audit_service.py:46-75`) automatically sanitizes passwords, secrets, JWT tokens, session IDs, and API keys before persisting to `audit_logs`.
- **XSS Prevention in Errors**: Custom error handlers in `src/pwd301/__init__.py:126-155` apply `markupsafe.escape` to error descriptions before HTML rendering.
- **Storage Path Traversal**: `FileService` stores uploaded blobs using SHA-256 hash-derived filenames and validates directory containment using `path.is_relative_to(storage_root)`. Quarantined or unscanned files fail-closed with HTTP 403.
- **Zero PK Leakage (ADR-002)**: External APIs, templates, and routes expose opaque public UUIDs (`public_id`), completely hiding internal `BigInt` auto-incrementing primary keys.

---

## 2. Logic Chain

1. **Premise 1 (SEC-01 Logic)**:
   - `_resolve_course(course_id)` in `src/pwd301/services/authorization_service.py` returns `None` if the provided identifier does not match any existing course.
   - Calling `course.id` on a variable that can be `None` without a prior existence check guarantees an `AttributeError`.
   - In `src/pwd301/blueprints/instructor/routes.py:1244-1245` and `src/pwd301/blueprints/api_courses/routes.py:757-758`, this call chain occurs unconditionally before `require_course_manager` can execute.
   - Therefore, querying an invalid course ID on these routes triggers an uncaught HTTP 500 error instead of the required HTTP 404 `ResourceNotFoundError`.

2. **Premise 2 (SEC-02 Logic)**:
   - Route decorators define the primary security perimeter for incoming HTTP requests.
   - `src/pwd301/blueprints/api_questions/routes.py` lines 41, 56, 78, 100 apply `@jwt_required` but omit `@instructor_required`.
   - While service-level checks in `question_bank_service.py` prevent unauthorized data modification by raising `ForbiddenError`, relying solely on downstream logic creates an inconsistency in API gateway authorization and exposes downstream services to unnecessary invocation overhead from unauthorized student tokens.
   - Therefore, adding `@instructor_required` establishes standard multi-layered defense-in-depth.

3. **Premise 3 (Systemic Security Architecture Logic)**:
   - The 225 security tests covering BOLA, CSRF, quarantine, attempt leasing, and RBAC passed with zero errors.
   - Static analysis confirmed zero raw SQL string concatenation, zero shell commands, zero SSTI templates, and strict `defusedxml` parser containment.
   - The API session rejection guard in `get_authenticated_actor` prevents ambient cookie CSRF across all `/api/*` endpoints.
   - Therefore, the overall security posture of the PWD301 application is mature, resilient, and adheres strictly to the non-negotiable invariants defined in `AGENTS.md` and the System Specification.

---

## 3. Caveats

1. **Database Dialect Parity in Test Environment**:
   - Automated tests were executed using SQLite in-memory/file storage with SQL Server dialect mocks.
   - Production Microsoft SQL Server features—such as physical backup restore locking (`RESTORE DATABASE ... WITH REPLACE`) and rowversion concurrency tokens—rely on mock verifications in unit tests. Live validation requires a running Microsoft SQL Server instance.
2. **External Service Dependencies**:
   - The Gemini AI integration (`src/pwd301/services/ai_service.py`) relies on external Google API endpoints. When `GEMINI_API_KEY` is not provided or network is unreachable, fallback error paths are taken.
   - ClamAV daemon antivirus scanning (`src/pwd301/services/file_service.py`) defaults to fail-closed behavior when the scanner is unreachable, which ensures security but can impact upload availability in environments without a running antivirus daemon.

---

## 4. Conclusion

The PWD301 codebase demonstrates an exceptionally high standard of security engineering, with comprehensive defenses against OWASP Top 10 vulnerabilities (BOLA/IDOR, Mass Assignment, SQL Injection, SSTI, XXE, CSRF, and Secret Leakage).

Two actionable improvements were identified:
1. **Fix SEC-01**: Replace `course = _resolve_course(course_id); require_course_manager(actor, course.id)` with direct resolution: `course = require_course_manager(actor, course_id, session=db.session)` in `instructor/routes.py:1244`, `api_courses/routes.py:757`, and `import_service.py:846`.
2. **Fix SEC-02**: Decorate mutating question endpoints in `api_questions/routes.py` (lines 41, 56, 78, 100) with `@instructor_required` to maintain defense-in-depth consistency.

### Proposed Code Remediation Snippets

#### Remediation for SEC-01:
In `src/pwd301/blueprints/instructor/routes.py`:
```python
# Before (lines 1244-1245):
course = _resolve_course(course_id, session=db.session)
require_course_manager(actor, course.id, session=db.session)

# After:
course = require_course_manager(actor, course_id, session=db.session)
```

In `src/pwd301/blueprints/api_courses/routes.py`:
```python
# Before (lines 757-758):
course = _resolve_course(course_id, session=db.session)
require_course_manager(actor, course.id, session=db.session)

# After:
course = require_course_manager(actor, course_id, session=db.session)
```

In `src/pwd301/services/import_service.py`:
```python
# Before (lines 846-847):
course = _resolve_course(course_id, session=sess)
require_course_manager(actor, course.id, session=sess)

# After:
course = require_course_manager(actor, course_id, session=sess)
```

#### Remediation for SEC-02:
In `src/pwd301/blueprints/api_questions/routes.py`:
```python
# Add @instructor_required decorator to mutating routes:
@api_question_bp.route("/<question_id>", methods=["PATCH"])
@jwt_required
@instructor_required
def patch_question_route(question_id: str): ...

@api_question_bp.route("/<question_id>/trash", methods=["POST"])
@jwt_required
@instructor_required
def trash_question_route(question_id: str): ...

@api_question_bp.route("/<question_id>", methods=["DELETE"])
@jwt_required
@instructor_required
def delete_question_route(question_id: str): ...

@api_question_bp.route("/<question_id>/restore", methods=["POST"])
@jwt_required
@instructor_required
def restore_question_route(question_id: str): ...
```

---

## 5. Verification Method

To independently verify the findings, security properties, and proposed remediations:

1. **Run Full Security Test Suite**:
   ```powershell
   .venv\Scripts\pytest tests/security -v
   ```
   *Expected Output*: 225 passed tests with zero failures.

2. **Verify BOLA / IDOR Protections**:
   ```powershell
   .venv\Scripts\pytest tests/security/test_rbac_and_idor.py tests/security/test_course_idor.py tests/security/test_attempt_idor.py tests/security/test_file_authorization_idor.py -v
   ```
   *Expected Output*: All IDOR and object-level authorization tests pass.

3. **Verify CSRF & API Cookie Boundary**:
   ```powershell
   .venv\Scripts\pytest tests/security/test_csrf_api_boundary.py -v
   ```
   *Expected Output*: Verification that session cookies sent to `/api/*` are rejected with HTTP 401 and web forms enforce CSRF tokens.

4. **Verify File Quarantine & Fail-Closed Behavior**:
   ```powershell
   .venv\Scripts\pytest tests/security/test_quarantine_fail_closed.py -v
   ```
   *Expected Output*: Unscanned/quarantined files cannot be accessed or downloaded by students.

5. **Verify Repository Contract & Linting**:
   ```powershell
   python scripts/repo_check.py
   ruff check src/
   ```
   *Expected Output*: Clean pass, 0 violations.
