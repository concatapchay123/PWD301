# DEFECT-01 — Malformed JSON Envelope on 401 & 403 Authorization Responses

**Severity:** High  
**Priority:** P1  
**Status:** RESOLVED & VERIFIED  
**Category:** API Contract & REST Schema  
**First detected iteration:** Iteration 03 / API Audit  
**Detected by Agent:** AGENT C (Backend & API QA Specialist)  
**Remediated by:** Senior Backend Engineer  
**Affected module:** Authorization Service  
**Affected routes:** All protected routes across `/instructor/*`, `/admin/*`, `/student/*`  
**Affected APIs:** All endpoints protected by `@require_roles`, `@login_required`, `@admin_required`  
**Affected roles:** ALL ROLES  
**Environment:** Live Flask REST API Platform at `http://127.0.0.1:5000`  

### 1. Bug Description
While Flask's centralized `_format_error_response` in `src/pwd301/__init__.py` generates compliant envelopes `{"success": false, "data": null, "error": {...}}`, the role-checking decorator `require_roles` in `src/pwd301/services/authorization_service.py` intercepted JSON requests and returned a malformed envelope containing only `{"error": {...}}`, omitting the mandatory top-level `"success": false` and `"data": null` properties.

### 2. Preconditions
- User authenticated with role `STUDENT` or unauthenticated client.

### 3. Steps to Reproduce
```bash
curl -s -b cookies.txt -H "Accept: application/json" http://127.0.0.1:5000/instructor/courses
```

### 4. Expected Result (Pure Headless Contract)
HTTP 403 with standardized envelope:
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "FORBIDDEN",
    "correlation_id": "...",
    "field_errors": {},
    "message": "Access denied: insufficient role permissions."
  }
}
```

### 5. Actual Result (Before Remediation)
HTTP 403:
```json
{
  "error": {
    "code": "FORBIDDEN",
    "correlation_id": "03210387c0924ae7ba07281a8cc53a5e",
    "field_errors": {},
    "message": "Access denied: insufficient role permissions."
  }
}
```

### 6. Root Cause Analysis
In `src/pwd301/services/authorization_service.py` (lines 183-193 and 203-214), the error response dictionaries were returned directly to `jsonify()` without `"success": False` or `"data": None`.

### 7. Remediation Applied
In `src/pwd301/services/authorization_service.py`:
Updated all authorization error handlers (`require_roles`, `admin_required`, `primary_admin_required`, and `require_admin_permission`) to return canonical envelopes:
```python
return (
    jsonify({
        "success": False,
        "data": None,
        "error": {
            "code": "FORBIDDEN",
            "message": "Access denied: insufficient role permissions.",
            "field_errors": {},
            "correlation_id": correlation_id,
        },
    }),
    403,
)
```

### 8. Verification Evidence
- Live probe via `curl -H "Accept: application/json" http://127.0.0.1:5000/instructor/courses`:
  HTTP 401 returns `{"success": false, "data": null, "error": {"code": "UNAUTHORIZED", ...}}`.
- Tested cross-role unauthorized calls in 20-Iteration Playwright run:
  `TC-RBAC-001`, `TC-RBAC-002`, `TC-RBAC-003`, `TC-RBAC-004` all PASS with 100% compliant envelopes.
