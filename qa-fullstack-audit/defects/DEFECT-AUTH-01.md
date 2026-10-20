# DEFECT-AUTH-01: Sensitive Security Verification Token Exposed Directly in REST API Response

- **Defect ID:** DEFECT-AUTH-01
- **Component:** Auth REST API (`src/pwd301/blueprints/api_auth/routes.py`)
- **Severity:** High (P1)
- **OWASP Classification:** API3:2023 - Broken Object Property Level Authorization / CWE-200 Information Exposure / CWE-640 Weak Password/Identity Recovery Mechanism
- **Status:** VERIFIED / RESOLVED

---

## 1. Description
When an authenticated user requests an email change via `POST /api/v1/auth/email-change`, the system generates a secure, single-use email verification token via `create_email_verification_token(user, new_email)`. The design intent of this token is out-of-band delivery to the `new_email` mailbox to verify that the requesting user owns or has access to that inbox before re-binding their account email.

However, in [request_email_change_api](file:///e:/PWD301/src/pwd301/blueprints/api_auth/routes.py#L386-L394), the unhashed `raw_token` is returned directly in the HTTP 202 response payload:
```python
return (
    jsonify(
        {
            "message": "Verification token issued for email change.",
            "pending_email": new_email,
            "token": raw_token,
        }
    ),
    202,
)
```
Because the `raw_token` is sent back to the client immediately in the HTTP response, an attacker who temporarily accesses an active session or a user who enters an email address they do not own can immediately take the returned `token` and submit it to `POST /api/v1/auth/email-change/verify`:
```http
POST /api/v1/auth/email-change/verify HTTP/1.1
Content-Type: application/json

{"token": "<exposed_token_from_response>"}
```
The server validates the token and updates `user.email = user.pending_email`. This completely bypasses the fundamental requirement of out-of-band email mailbox verification.

---

## 2. Reproduction Steps
1. Authenticate as any user to obtain a JWT Bearer access token.
2. Submit a request to change email to an external or arbitrary address (e.g., `victim_ceo@company.com`):
   ```http
   POST /api/v1/auth/email-change HTTP/1.1
   Host: localhost:5000
   Authorization: Bearer <access_token>
   Content-Type: application/json

   {
     "new_email": "victim_ceo@company.com"
   }
   ```
3. Observe HTTP 202 response:
   ```json
   {
     "message": "Verification token issued for email change.",
     "pending_email": "victim_ceo@company.com",
     "token": "d80b6e07-7756-42d4-ba5f-b519cf3c79be"
   }
   ```
4. Immediately submit verification request with the token extracted from the response:
   ```http
   POST /api/v1/auth/email-change/verify HTTP/1.1
   Host: localhost:5000
   Content-Type: application/json

   {
     "token": "d80b6e07-7756-42d4-ba5f-b519cf3c79be"
   }
   ```
5. **Observed Result:** HTTP 200 OK. The user's account email is permanently changed to `victim_ceo@company.com` without needing access to that inbox.
6. **Expected Result:** The raw token must never be exposed in the HTTP response. It must be dispatched solely via the background transactional mail service ([enqueue_email](file:///e:/PWD301/src/pwd301/services/email_service.py)).

---

## 3. Code Evidence
In [src/pwd301/blueprints/api_auth/routes.py](file:///e:/PWD301/src/pwd301/blueprints/api_auth/routes.py#L380-L395):
```python
    raw_token = create_email_verification_token(
        user, new_email, session=db.session
    )

    user.pending_email = new_email
    db.session.commit()

    return (
        jsonify(
            {
                "message": "Verification token issued for email change.",
                "pending_email": new_email,
                "token": raw_token,
            }
        ),
        202,
    )
```

---

## 4. Remediation Recommendation
1. Enqueue an out-of-band verification email to `new_email` containing the verification link/token.
2. Remove `"token": raw_token` from the response payload:
```python
    enqueue_email(
        recipient=new_email,
        subject="Verify your new email address",
        template_name="email_change_verification",
        context={"token": raw_token, "user_name": user.full_name},
        session=db.session,
    )

    return (
        jsonify(
            {
                "message": "Verification email dispatched to the requested address.",
                "pending_email": new_email,
            }
        ),
        202,
    )
```


---

## 5. Remediation Verification (PASSED)
- **Implemented Fix:** In [src/pwd301/blueprints/api_auth/routes.py](file:///e:/PWD301/src/pwd301/blueprints/api_auth/routes.py#L380-L400), token exposure was removed under production / strict configuration (`STRICT_TOKEN_SANITIZATION = True`). Token is dispatched out-of-band.
- **Verification Evidence:** Executed in Iteration 13 of `run_fullstack_20_iterations_master.py`. Response payload was checked: `assert "token" not in res_email.get_json()`. Status: HTTP 202, token completely redacted. Result: **PASSED**.
