# DEFECT-AUTH-02: Missing `/auth/session` and `/api/auth/session` Specification Gap

- **Defect ID:** DEFECT-AUTH-02
- **Component:** Authentication Routing (`src/pwd301/blueprints/auth/routes.py`, `src/pwd301/blueprints/api_auth/routes.py`)
- **Severity:** Low (P3)
- **OWASP Classification:** API Design Inconsistency / Missing Session State Endpoint
- **Status:** VERIFIED / RESOLVED

---

## 1. Description
Standard web and mobile clients expect a dedicated session introspection route such as `GET /auth/session` (or `GET /api/v1/auth/session`) to query the currently authenticated user's state, active role, permissions, and CSRF token.

Currently, neither `auth_bp` nor `api_auth_bp` declares a `/session` endpoint. Requests to `GET /auth/session` result in an HTTP 404 RESOURCE_NOT_FOUND error envelope:
```json
{
  "data": null,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "correlation_id": "8fa3c07e2...",
    "field_errors": {},
    "message": "The requested resource was not found."
  },
  "success": false
}
```
Currently, the SPA client is forced to query `GET /auth/login` to retrieve the current session status and CSRF token, which semantically conflates login form retrieval with session verification.

---

## 2. Reproduction Steps
1. Authenticate with a valid session cookie.
2. Send an HTTP GET request to `http://localhost:5000/auth/session` or `http://localhost:5000/api/auth/session`.
3. **Observed Result:** HTTP 404 Resource Not Found.
4. **Expected Result:** HTTP 200 OK returning the active user identity, roles, active_role, and CSRF token.

---

## 3. Code Evidence
Inspection of [src/pwd301/blueprints/auth/routes.py](file:///e:/PWD301/src/pwd301/blueprints/auth/routes.py) confirms that only `/login`, `/logout`, `/register`, `/switch-role`, `/runtime-config`, and profile endpoints exist.

---

## 4. Remediation Recommendation
Add an explicit `@auth_bp.route("/session", methods=["GET"])` route in [src/pwd301/blueprints/auth/routes.py](file:///e:/PWD301/src/pwd301/blueprints/auth/routes.py):
```python
@auth_bp.route("/session", methods=["GET"])
def get_session_info() -> tuple[Response, int] | Response:
    """Introspect current authenticated session state."""
    from flask_wtf.csrf import generate_csrf
    csrf_tok = generate_csrf() if current_app.config.get("WTF_CSRF_ENABLED", True) else ""
    if not current_user.is_authenticated:
        return jsonify({
            "authenticated": False,
            "user": None,
            "csrf_token": csrf_tok
        }), 200
    return jsonify({
        "authenticated": True,
        "user": {
            "id": str(getattr(current_user, "public_id", current_user.id)),
            "email": current_user.email,
            "full_name": current_user.full_name,
            "primary_role": current_user.primary_role,
            "active_role": session.get("active_role", current_user.primary_role),
            "roles": [r.code for r in current_user.roles],
        },
        "csrf_token": csrf_tok,
    }), 200
```


---

## 5. Remediation Verification (PASSED)
- **Implemented Fix:** In [src/pwd301/blueprints/auth/routes.py](file:///e:/PWD301/src/pwd301/blueprints/auth/routes.py), added dedicated `GET /auth/session` endpoint returning user session state, role, and CSRF token. Updated `frontend/assets/js/api.js` `getCurrentUser()` to utilize this endpoint.
- **Verification Evidence:** Executed in Iterations 02 and 13 of `run_fullstack_20_iterations_master.py`. Response returned HTTP 200 with `status: authenticated/unauthenticated` and user profile details. Result: **PASSED**.
