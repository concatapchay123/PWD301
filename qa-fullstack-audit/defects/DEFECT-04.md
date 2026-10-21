# DEFECT-04 — Malformed 409 Conflict Response Envelope (Missing data: null)

**Severity:** Low  
**Priority:** P3  
**Status:** RESOLVED & VERIFIED  
**Category:** API Contract  
**First detected iteration:** Iteration 02  
**Detected by Agent:** AGENT C  
**Remediated by:** Senior Backend Engineer  
**Affected module:** Auth Blueprint  
**Affected routes:** `#/auth`  
**Affected APIs:** `POST /auth/login`  
**Affected roles:** ALL ROLES  

### 1. Bug Description
When concurrent login was detected, `POST /auth/login` returned:
`{"error": {"code": "CONCURRENT_LOGIN_DETECTED", ...}, "success": false}`
omitting `"data": null`.

### 2. Remediation Applied
In `src/pwd301/blueprints/auth/routes.py`:
Updated the 409 Conflict response payload to strictly include `"data": None`:
```python
return (
    jsonify({
        "success": False,
        "data": None,
        "error": {
            "code": "CONCURRENT_LOGIN_DETECTED",
            "message": "Tài khoản đã bị đăng xuất trên toàn bộ thiết bị do phát hiện đăng nhập đồng thời từ thiết bị khác để bảo vệ an toàn.",
        },
    }),
    409,
)
```

### 3. Verification Evidence
- Verified in Iteration 02 (`TC-AUTH-002`): Multi-device concurrent login returns HTTP 409 with exact schema `{"success": false, "data": null, "error": {...}}`.
- 100% PASS in 20-Iteration Playwright test suite.
