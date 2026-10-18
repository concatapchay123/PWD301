# QA MASTER DEFECT REGISTRY & SECURITY AUDIT LEDGER

- **Scope:** Full-Stack API, Authentication & Access Control Audit (Phases 1 - 3)
- **Target System:** PWD301 LMS Pure Headless REST API & Web Platform
- **Lead Auditors:** AGENT C & E (Senior Backend, API & Security QA Specialists)
- **Status Date:** 2026-10-18T22:30:00Z

---

## 1. Master Defect Ledger

| Defect ID | Defect Title | Severity | Priority | OWASP / Security Category | Status | Affected Files | Remediation Status |
|---|---|---|---|---|---|---|---|
| [DEFECT-AUTH-01](file:///e:/PWD301/qa-fullstack-audit/defects/DEFECT-AUTH-01.md) | Sensitive Security Verification Token Exposed Directly in REST Response | High | P1 | OWASP API3:2023 - Broken Object Property / Insecure Token Leakage | **OPEN** | [api_auth/routes.py](file:///e:/PWD301/src/pwd301/blueprints/api_auth/routes.py#L386-L394) | Proposed: Dispatch via transactional email only; redact from response body |
| [DEFECT-IT10-001](file:///e:/PWD301/qa-fullstack-audit/defects/DEFECT-IT10-001.md) | Course Soft-Delete Route Raises HTTP 403 on Post-Trash Serialization | High | P1 | Business Logic / Circular Access Denial | **OPEN** | [instructor/routes.py](file:///e:/PWD301/src/pwd301/blueprints/instructor/routes.py#L1120), [lesson_service.py](file:///e:/PWD301/src/pwd301/services/lesson_service.py#L205) | Proposed: Return compact JSON envelope instead of calling `_serialize_course` |
| [DEFECT-BOLA-01](file:///e:/PWD301/qa-fullstack-audit/defects/DEFECT-BOLA-01.md) | Information Disclosure / BOLA on Draft Course Lessons Outline | Medium | P2 | OWASP API1:2023 - Broken Object Level Authorization (BOLA) | **OPEN** | [api_courses/routes.py](file:///e:/PWD301/src/pwd301/blueprints/api_courses/routes.py#L276), [lesson_service.py](file:///e:/PWD301/src/pwd301/services/lesson_service.py#L1947) | Proposed: Pass `actor` into `get_course_lessons` and verify `can_view_course` |
| [DEFECT-ROUTE-01](file:///e:/PWD301/qa-fullstack-audit/defects/DEFECT-ROUTE-01.md) | Duplicate Route Registration and Handler Shadowing on Admin Course Inspection | Medium | P2 | OWASP API5:2023 - Broken Function Level Authorization / Route Shadowing | **OPEN** | [admin/routes.py](file:///e:/PWD301/src/pwd301/blueprints/admin/routes.py#L155), [admin/routes.py](file:///e:/PWD301/src/pwd301/blueprints/admin/routes.py#L514) | Proposed: Unify route handlers and harmonize permission checks |
| [DEFECT-AUTH-02](file:///e:/PWD301/qa-fullstack-audit/defects/DEFECT-AUTH-02.md) | Missing `/auth/session` and `/api/auth/session` Specification Gap | Low | P3 | API Specification & Architecture Inconsistency | **OPEN** | [auth/routes.py](file:///e:/PWD301/src/pwd301/blueprints/auth/routes.py), [api_auth/routes.py](file:///e:/PWD301/src/pwd301/blueprints/api_auth/routes.py) | Proposed: Implement dedicated `@auth_bp.route("/session")` |

---

## 2. Summary by Severity & Category

- **Critical (P0) Blockers:** **0** (No remote code execution, unauthenticated database drops, or complete auth bypass).
- **High (P1):** **2** (`DEFECT-AUTH-01`, `DEFECT-IT10-001`)
- **Medium (P2):** **2** (`DEFECT-BOLA-01`, `DEFECT-ROUTE-01`)
- **Low (P3):** **1** (`DEFECT-AUTH-02`)
- **Total Open Defects:** **5**

---

## 3. Verification & Compliance Matrix

- **OWASP API1:2023 (BOLA):** Tested across courses, learning units, lessons, assessments, attempts, regrade jobs, and files. 1 defect identified (`DEFECT-BOLA-01`).
- **OWASP API2:2023 (Broken Authentication):** Verified JWT Bearer signing, secret rotation, session cookie flags (`HttpOnly`, `SameSite=Lax`, `Secure`), and `auth_version` invalidation. No session hijacking vulnerabilities detected.
- **OWASP API3:2023 (Broken Object Property Level Auth):** Verified response filtering. 1 defect identified (`DEFECT-AUTH-01` leaking email change token).
- **OWASP API4:2023 (Unrestricted Resource Consumption):** Rate limits verified on AI endpoints, login attempts (`is_login_locked`), and max upload limit (1 GB enforced in stream chunks).
- **OWASP API5:2023 (BFLA):** Verified role checks (`@admin_required`, `@instructor_required`, `@student_required`) across 428 endpoints. 1 route collision identified (`DEFECT-ROUTE-01`).
- **OWASP API6:2023 (Server-Side Request Forgery - SSRF):** Safe URL redirect validation verified in `_is_safe_redirect_url` (`auth/routes.py`).
- **OWASP API7:2023 (Security Misconfiguration):** Security headers verified (`X-Content-Type-Options: nosniff`, `Content-Security-Policy`, `X-Frame-Options: SAMEORIGIN/DENY`, `Cache-Control: private, no-store` on sensitive routes).
- **OWASP API8:2023 (Lack of Protection from Automated Threats):** Anti-tamper shields and blackout trigger verified.
- **OWASP API9:2023 (Improper Inventory Management):** All 17 blueprints inventoried and audited.
- **OWASP API10:2023 (Unsafe Consumption of APIs):** ClamAV daemon antivirus stream scanning with fail-closed security verified.
