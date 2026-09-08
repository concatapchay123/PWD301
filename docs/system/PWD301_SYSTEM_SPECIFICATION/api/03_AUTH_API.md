# Auth Api

This file expands the relevant entries from the endpoint catalog. Authorization is object-level and all mutations re-check current state inside the service transaction.

### `POST /api/auth/login`
- **Purpose:** Create API authentication grant/token
- **Authentication:** Public
- **Authorization:** Valid active User
- **Request:** email, password
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 200 token metadata
- **Errors:** AUTHENTICATION_FAILED / ACCOUNT_SUSPENDED; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** Request not retried blindly
- **Side effects:** security event on repeated failure

### `POST /api/auth/logout`
- **Purpose:** Revoke current API grant
- **Authentication:** JWT
- **Authorization:** Current token owner
- **Request:** current token
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 204
- **Errors:** AUTHENTICATION_REQUIRED; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** Idempotent
- **Side effects:** revoke token grant

### `POST /api/auth/email-change`
- **Purpose:** Start new-email verification
- **Authentication:** JWT
- **Authorization:** Self
- **Request:** new_email
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 202
- **Errors:** VALIDATION_ERROR / CONFLICT; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** Dedupe active request
- **Side effects:** verification email

### `POST /api/auth/email-change/verify`
- **Purpose:** Verify and activate pending email
- **Authentication:** Public/signed token
- **Authorization:** Token owner/purpose
- **Request:** verification token
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 200
- **Errors:** TOKEN_INVALID/EXPIRED / CONFLICT; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** Single-use
- **Side effects:** audit + notification; optional auth revocation
