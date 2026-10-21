# DEFECT-05 — Malformed 429 Rate Limit Response Envelope

**Severity:** Low  
**Priority:** P3  
**Status:** RESOLVED & VERIFIED  
**Category:** API Contract  
**First detected iteration:** Iteration 02 / Brute Force Testing  
**Detected by Agent:** AGENT C  
**Remediated by:** Senior Backend Engineer  
**Affected module:** Rate Limiting Service & Blueprints  
**Affected routes:** All rate-limited endpoints  
**Affected APIs:** `POST /auth/login`, `POST /api/auth/login`, `/student/ai/chat`  
**Affected roles:** ALL ROLES  

### 1. Bug Description
When rate limiting triggered HTTP 429, the response payload was:
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Quá nhiều lần đăng nhập thất bại. Vui lòng thử lại sau 34 giây."
  }
}
```
Missing the standard top-level `"success": false` and `"data": null` properties.

### 2. Remediation Applied
In `src/pwd301/blueprints/auth/routes.py`, `src/pwd301/blueprints/api_auth/routes.py`, and `src/pwd301/blueprints/student/routes.py`:
Updated all rate limit rejection returns to conform to canonical envelope:
```python
return (
    jsonify({
        "success": False,
        "data": None,
        "error": {
            "code": "RATE_LIMIT_EXCEEDED",
            "message": f"Quá nhiều lần đăng nhập thất bại. Vui lòng thử lại sau {retry_after} giây.",
        },
    }),
    429,
    {"Retry-After": str(retry_after)},
)
```

### 3. Verification Evidence
- Live probe via simulated brute force triggers HTTP 429 with compliant envelope:
  `{"success": false, "data": null, "error": {"code": "RATE_LIMIT_EXCEEDED", ...}}`.
- Verified in 20-Iteration Playwright run:
  Iteration 02 and Iteration 13 executed with 100% PASS rate.
