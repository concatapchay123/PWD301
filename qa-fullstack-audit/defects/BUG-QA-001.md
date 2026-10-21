# BUG-QA-001 — Unauthenticated Call on /admin/telemetry Returns 401 Without Standardized Envelope

**Severity:** Low / Medium  
**Priority:** P3  
**Status:** RESOLVED & VERIFIED  
**Category:** API / Backend Contract  
**First detected iteration:** Iteration 01  
**Detected by Agent:** Agent A (Master Orchestrator)  
**Remediated by:** Senior Backend Engineer  
**Affected module:** Operations, Telemetry & JWT Auth Service  
**Affected routes:** `#/admin/operations`  
**Affected APIs:** `GET /admin/telemetry`, JWT auth handlers  
**Affected roles:** ANONYMOUS, ADMIN  
**Environment:** Production-grade Docker Container (`pwd301_web`, MSSQL 2022)  

### 1. Bug Description
When `GET /admin/telemetry` was invoked by an unauthenticated client or when a session expired, the backend properly rejected the request with HTTP 401. However, the JSON payload returned contained `{"error": {"code": "UNAUTHORIZED", ...}}` without the top-level `"data": null` standard envelope property.

### 2. Preconditions
- Unauthenticated client session or expired cookie.

### 3. Steps to Reproduce
1. Send `GET /admin/telemetry` without cookie headers.
2. Inspect HTTP status code and response payload.

### 4. Expected Result
Returns HTTP 401 with standard envelope:
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required."
  }
}
```

### 5. Actual Result (Before Remediation)
Returns HTTP 401:
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "correlation_id": "...",
    "field_errors": {},
    "message": "Authentication required to access this resource."
  }
}
```

### 6. Remediation Applied
In `src/pwd301/services/jwt_auth_service.py`:
Updated all JWT and unauthenticated error responders (`_error_response` lines 525–635) to return:
```python
return (
    jsonify({
        "success": False,
        "data": None,
        "error": {
            "code": error_code,
            "message": message,
            "field_errors": {},
            "correlation_id": correlation_id,
        },
    }),
    status_code,
    headers,
)
```

### 7. Verification Evidence
- Live probe via `curl -s http://127.0.0.1:5000/admin/telemetry`:
  Returns HTTP 401: `{"success": false, "data": null, "error": {"code": "UNAUTHORIZED", "message": "Authentication required."}}`.
- Verified in 20-Iteration Playwright run:
  Iteration 01 (`TC-SMOKE-005`) and Iteration 16 (`TC-PERF-001`) executed with 100% PASS rate.
