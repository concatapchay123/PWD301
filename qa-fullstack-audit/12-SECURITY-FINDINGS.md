# PWD301 SECURITY AUDIT & OWASP API TOP 10 (2023) FINDINGS

- **Document ID:** QA-FULLSTACK-12-SECURITY-FINDINGS
- **Audit Target:** PWD301 LMS Pure Headless Backend & REST API Platform
- **Auditors:** AGENT C & E (Senior Backend, API & Security QA Specialists)
- **Status Date:** 2026-10-18T22:50:00Z
- **Standards Applied:** OWASP API Security Top 10 (2023), NIST SP 800-63B, ADR-002 Zero Internal PK Leakage

---

## 1. Executive Security Assessment & Compliance Scorecard

The security posture of the PWD301 platform was subjected to systematic white-box source code analysis, AST decorator inspection across 428 endpoints, access boundary testing across three role tiers (STUDENT, INSTRUCTOR, ADMIN), cryptographic token auditing, and empirical vulnerability probing.

```mermaid
flowchart LR
    subgraph OWASP_API_Top_10 ["OWASP API Security Top 10 (2023)"]
        API1["API1: BOLA (Medium P2 - DEFECT-BOLA-01)"]
        API2["API2: Broken Authentication (PASS)"]
        API3["API3: Broken Object Property (High P1 - DEFECT-AUTH-01)"]
        API4["API4: Unrestricted Resource (PASS)"]
        API5["API5: Broken Function Level Auth (Medium P2 - DEFECT-ROUTE-01)"]
        API6["API6: Sensitive Business Flows (High P1 - DEFECT-IT10-001)"]
        API7["API7: SSRF (PASS)"]
        API8["API8: Security Misconfiguration (PASS)"]
        API9["API9: Inventory Management (Low P3 - DEFECT-AUTH-02)"]
        API10["API10: Unsafe API Consumption (PASS)"]
    end
```

### Overall Security Posture Summary
- **Critical (P0) Exploits:** **0** (Zero unauthenticated SQL injection, zero remote code execution, zero database bypass).
- **High (P1) Vulnerabilities:** **2** (`DEFECT-AUTH-01`, `DEFECT-IT10-001`).
- **Medium (P2) Vulnerabilities:** **2** (`DEFECT-BOLA-01`, `DEFECT-ROUTE-01`).
- **Low (P3) Discrepancies:** **1** (`DEFECT-AUTH-02`).
- **Core Security Controls In Force:**
  - Strict ADR-002 compliance: Zero internal `BigInt` primary key leakage across all public endpoints (all entities exposed solely via opaque `UUID` public IDs).
  - Dual authentication boundary: Session cookies with CSRF validation for Web SPA; JWT Bearer tokens for headless REST API.
  - Fail-closed ClamAV antivirus scanning on all uploaded assets with quarantine isolation.
  - Client-side anti-tamper security shield with automated session revocation on confirmed inspection attempts.

---

## 2. OWASP API Security Top 10 (2023) Deep-Dive Findings

### 2.1. API1:2023 — Broken Object Level Authorization (BOLA)
**Status:** **DEFECT IDENTIFIED (Medium P2)**  
- **Audit Scope:** Evaluated multi-tenant authorization predicates in [src/pwd301/services/authorization_service.py](file:///e:/PWD301/src/pwd301/services/authorization_service.py): `can_view_course`, `can_manage_course`, `can_access_student_data`, `can_access_attempt`, and `authorize_file_download`.
- **Finding — [DEFECT-BOLA-01](file:///e:/PWD301/qa-fullstack-audit/defects/DEFECT-BOLA-01.md): Information Disclosure on Draft Course Lessons Outline**
  - **Affected Code:** [src/pwd301/blueprints/api_courses/routes.py:276](file:///e:/PWD301/src/pwd301/blueprints/api_courses/routes.py#L276) (`get_course_lessons_api`) and [src/pwd301/services/lesson_service.py:1947](file:///e:/PWD301/src/pwd301/services/lesson_service.py#L1947) (`get_course_lessons`).
  - **Vulnerability Mechanism:** While `GET /api/courses/<course_id>` calls `get_course_detail()` which strictly verifies `can_view_course()` (blocking unpublished `DRAFT` or `SUBMITTED_FOR_REVIEW` courses for students and anonymous users), the sibling route `GET /api/courses/<course_id>/lessons` invokes `get_course_lessons()` which only checks `course.status in ("TRASH", "ARCHIVED")`.
  - **Impact:** An unauthenticated caller or unprivileged student possessing a course's public UUID can retrieve the complete syllabus hierarchy, lesson IDs, positions, and titles of unpublished, confidential courses prior to administrative approval.
  - **Remediation:** Pass the authenticated actor into `get_course_lessons(course_identifier, actor=actor, session=db.session)` and enforce `can_view_course(actor, course)`.

### 2.2. API2:2023 — Broken Authentication
**Status:** **PASS**  
- **Dual Authentication Architecture:**
  - **Web SPA:** Authenticated via Flask-Login session cookies with `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SAMESITE='Lax'`, and `SESSION_COOKIE_SECURE=True` enforced in production. Cryptographic CSRF tokens (`X-CSRFToken`) are mandatory on all state-changing requests.
  - **REST API:** Authenticated via PyJWT Bearer tokens signed with HMAC-SHA256. Access tokens carry a 15-minute expiration (`exp`), subject (`sub`), role claims, and `auth_version`.
- **Global Token Revocation (`auth_version`):**
  - User records in `users` store an `auth_version` integer column.
  - When a user changes their password, logs out globally, or is suspended by an administrator, `user.auth_version` is incremented.
  - The JWT middleware and session validator reject any token or cookie whose embedded `auth_version` is less than the current database value, instantaneously revoking all active sessions across devices.
- **Brute Force Protection:**
  - Enforced via [src/pwd301/services/rate_limit_service.py](file:///e:/PWD301/src/pwd301/services/rate_limit_service.py): 5 consecutive failed login attempts trigger an immediate 15-minute account lockout (`is_login_locked`), mitigating credential stuffing attacks.

### 2.3. API3:2023 — Broken Object Property Level Authorization
**Status:** **DEFECT IDENTIFIED (High P1)**  
- **Audit Scope:** Inspected mass assignment protections, model serializers, and sensitive field filtering across all JSON responses.
- **Finding — [DEFECT-AUTH-01](file:///e:/PWD301/qa-fullstack-audit/defects/DEFECT-AUTH-01.md): Sensitive Security Verification Token Exposed Directly in REST Response**
  - **Affected Code:** [src/pwd301/blueprints/api_auth/routes.py:386-394](file:///e:/PWD301/src/pwd301/blueprints/api_auth/routes.py#L386-L394) (`request_email_change_api`).
  - **Vulnerability Mechanism:** When an authenticated user calls `POST /api/v1/auth/email-change`, the system generates an email verification token:
    ```python
    raw_token = create_email_verification_token(user, new_email, session=db.session)
    user.pending_email = new_email
    db.session.commit()
    return jsonify({
        "message": "Verification token issued for email change.",
        "pending_email": new_email,
        "token": raw_token,  # <--- CRITICAL TOKEN LEAKAGE
    }), 202
    ```
  - **Exploitation Impact:** The unhashed token is returned directly in the HTTP 202 JSON payload. Any caller can take the returned token and immediately invoke `POST /api/v1/auth/email-change/verify`, updating their account email to an arbitrary victim's address without ever possessing or accessing the target email inbox.
  - **Remediation:** Remove `"token": raw_token` from the JSON response and dispatch the token exclusively via out-of-band email using `enqueue_email()`.

### 2.4. API4:2023 — Unrestricted Resource Consumption
**Status:** **PASS**  
- **Upload Clamping:**
  - Strict 50MB non-archive attachment policy (`MAX_ATTACHMENT_BYTES = 50_000_000`).
  - Video stream upload strictly capped below 1GB (`MAX_VIDEO_BYTES_EXCLUSIVE = 1_000_000_000`).
  - Chunked streaming extraction via [LimitingStream](file:///e:/PWD301/src/pwd301/services/file_service.py) prevents memory exhaustion (Denial of Service) by reading request bodies in 64KB chunks directly to disk without loading entire files into RAM.
- **AI Rate Limiting:**
  - In [src/pwd301/blueprints/api_ai/routes.py](file:///e:/PWD301/src/pwd301/blueprints/api_ai/routes.py#L65), `check_ai_rate_limit(actor, role=actor.primary_role)` throttles generative AI requests per role tier to prevent quota depletion and excessive API billing.

### 2.5. API5:2023 — Broken Function Level Authorization (BFLA)
**Status:** **DEFECT IDENTIFIED (Medium P2)**  
- **Audit Scope:** Verified role-enforcing decorators across all 428 endpoint-method combinations:
  - `@admin_required`: Restricts routes to users possessing the `ADMIN` role.
  - Granular admin permission checks: Sub-role permissions (`COURSE_REVIEW`, `TEACHING_ASSIGNMENT`, `SYSTEM_MONITORING`).
  - `@instructor_required`: Restricts routes to `INSTRUCTOR` or `ADMIN`.
  - `@student_required`: Requires active authenticated enrollment.
- **Finding — [DEFECT-ROUTE-01](file:///e:/PWD301/qa-fullstack-audit/defects/DEFECT-ROUTE-01.md): Duplicate Route Registration & Handler Shadowing**
  - **Affected Code:** [src/pwd301/blueprints/admin/routes.py:155](file:///e:/PWD301/src/pwd301/blueprints/admin/routes.py#L155) (`admin_course_detail`) and line 514 (`admin_get_course_detail`).
  - **Vulnerability Mechanism:** Both handlers register `@admin_bp.route("/courses/<course_id>", methods=["GET"])`. The second handler (line 514) requires strictly `COURSE_REVIEW` admin permission and generates signed file stream URLs. However, Flask binds the first handler (line 155), which permits access to administrators with only `TEACHING_ASSIGNMENT` permission and omits file streaming URLs.
  - **Impact:** Inconsistent access boundary enforcement and dead code masking.
  - **Remediation:** Consolidate the two view functions into a single canonical route with unified authorization logic.

### 2.6. API6:2023 — Unrestricted Access to Sensitive Business Flows
**Status:** **DEFECT IDENTIFIED (High P1)**  
- **Audit Scope:** Assessment attempts, single-tab editing leases, and course soft-deletion lifecycles.
- **Single Active Editing Lease (Algorithm 07):**
  - Cryptographically fences out concurrent tabs during assessment attempts using `lease_token_hash` and `lease_epoch`. Stale browser instances are prevented from overwriting active examination answers.
- **Finding — [DEFECT-IT10-001](file:///e:/PWD301/qa-fullstack-audit/defects/DEFECT-IT10-001.md): Post-Trash Course Serialization 403 Forbidden**
  - **Affected Code:** [src/pwd301/blueprints/instructor/routes.py:1120](file:///e:/PWD301/src/pwd301/blueprints/instructor/routes.py#L1120) and [src/pwd301/services/lesson_service.py:205](file:///e:/PWD301/src/pwd301/services/lesson_service.py#L205).
  - **Vulnerability Mechanism:** Trashing an instructor course via `POST /instructor/courses/<id>/trash` sets `course.deleted_at = now()`. The controller subsequently invokes `_serialize_course(course)`, which calls `list_learning_units()`, which enforces `require_course_manager()`. Because `course.deleted_at` is populated, `require_course_manager()` denies access with HTTP 403 Forbidden.
  - **Impact:** Course soft-delete succeeds in the database, but the instructor receives an error response, breaking UI workflows.
  - **Remediation:** Return a standardized success confirmation envelope without re-evaluating active management permissions on the deleted entity.

### 2.7. API7:2023 — Server Side Request Forgery (SSRF)
**Status:** **PASS**  
- **Safe URL Redirect Validation:**
  - In [src/pwd301/blueprints/auth/routes.py](file:///e:/PWD301/src/pwd301/blueprints/auth/routes.py#L64-L78), `_is_safe_redirect_url(target)` strictly sanitizes target redirect URLs:
    ```python
    if "\\" in target: return False  # Block backslash browser normalizations (/\attacker.com)
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc: return False  # Block absolute URLs
    return parsed.path.startswith("/") and not parsed.path.startswith("//")
    ```
- **External Webhooks & Video Streaming:**
  - YouTube player embeds strictly validate video IDs against regex patterns; internal file streams bypass client-provided paths and resolve strictly from vetted `file_assets` records.

### 2.8. API8:2023 — Security Misconfiguration
**Status:** **PASS**  
- **Defensive HTTP Response Headers:** Enforced via `@app.after_request` in [src/pwd301/__init__.py](file:///e:/PWD301/src/pwd301/__init__.py#L780-L836):
  - `X-Content-Type-Options: nosniff`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `X-Frame-Options: SAMEORIGIN` (for authorized preview viewports) or `DENY` (default)
  - `Content-Security-Policy`: Restricts scripts to trusted CDNs, eliminates arbitrary script execution, and disables framing from unauthorized external origins.
- **Fail-Closed Antivirus Scanning:**
  - ClamAV 1.4.3 daemon integration on port 3310.
  - All file uploads are scanned in real-time. If ClamAV detects malware or is unreachable, the upload is quarantined and rejected with `FileInfectedError` or `FileSecurityQuarantineError`.
- **Anti-Tamper Browser Security Shield:**
  - Client-side monitoring intercepts developer shortcuts (F12, Ctrl+Shift+I/J/C, Ctrl+U, PrintScreen, Win+Shift+S).
  - High-confidence inspection attempts trigger the full-screen Blackout Shield ("🛡️ CẢNH BÁO AN NINH HỆ THỐNG"), invoke `POST /auth/logout` to revoke the server session, clear local storage tokens, and redirect to `#/auth`.

### 2.9. API9:2023 — Improper Inventory Management
**Status:** **DEFECT IDENTIFIED (Low P3)**  
- **Audit Scope:** Reviewed all 17 registered blueprints.
- **Finding — [DEFECT-AUTH-02](file:///e:/PWD301/qa-fullstack-audit/defects/DEFECT-AUTH-02.md): Missing `/auth/session` Specification Gap**
  - Neither `auth_bp` nor `api_auth_bp` implements `GET /auth/session`, returning HTTP 404. Clients must awkwardly call `GET /auth/login` to query current session status.

### 2.10. API10:2023 — Unsafe Consumption of APIs
**Status:** **PASS**  
- **Gemini 3.8 AI Assistant:**
  - Prompts are passed through sanitization filters to prevent prompt injection and role leakage.
  - Gemini API timeouts are capped at 8 seconds with graceful degradation on third-party failure.

---

## 3. Master Defect Ledger & Severity Reconciliation

| Defect ID | Defect Title | Severity | Priority | OWASP API 2023 | Status | Affected Files |
|---|---|---|---|---|---|---|
| [DEFECT-AUTH-01](file:///e:/PWD301/qa-fullstack-audit/defects/DEFECT-AUTH-01.md) | Verification Token Exposed in REST Response | **High** | **P1** | API3:2023 | OPEN | [api_auth/routes.py#L386-L394](file:///e:/PWD301/src/pwd301/blueprints/api_auth/routes.py#L386-L394) |
| [DEFECT-IT10-001](file:///e:/PWD301/qa-fullstack-audit/defects/DEFECT-IT10-001.md) | Course Trash Serialization 403 Forbidden | **High** | **P1** | API6:2023 | OPEN | [instructor/routes.py#L1120](file:///e:/PWD301/src/pwd301/blueprints/instructor/routes.py#L1120) |
| [DEFECT-BOLA-01](file:///e:/PWD301/qa-fullstack-audit/defects/DEFECT-BOLA-01.md) | BOLA on Draft Course Lessons Outline | **Medium** | **P2** | API1:2023 | OPEN | [api_courses/routes.py#L276](file:///e:/PWD301/src/pwd301/blueprints/api_courses/routes.py#L276) |
| [DEFECT-ROUTE-01](file:///e:/PWD301/qa-fullstack-audit/defects/DEFECT-ROUTE-01.md) | Duplicate Route Registration & Shadowing | **Medium** | **P2** | API5:2023 | OPEN | [admin/routes.py#L155](file:///e:/PWD301/src/pwd301/blueprints/admin/routes.py#L155) & [L514](file:///e:/PWD301/src/pwd301/blueprints/admin/routes.py#L514) |
| [DEFECT-AUTH-02](file:///e:/PWD301/qa-fullstack-audit/defects/DEFECT-AUTH-02.md) | Missing `/auth/session` Specification Gap | **Low** | **P3** | API9:2023 | OPEN | [auth/routes.py](file:///e:/PWD301/src/pwd301/blueprints/auth/routes.py) |

---

## 4. Final Security Decision & Quality Gate Verdict

- **Zero Critical (P0) Flaws:** The core authentication, database transactions, and ClamAV antivirus pipelines operate reliably.
- **Release Recommendation:** The platform is structurally sound and **READY FOR STAGING DEPLOYMENT** once the High (P1) remediation patches for `DEFECT-AUTH-01` (redacting verification tokens from REST responses) and `DEFECT-IT10-001` (compact course trashing serialization) are applied.
