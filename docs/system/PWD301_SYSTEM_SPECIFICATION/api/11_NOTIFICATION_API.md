# Notification Api

This file expands the relevant entries from the endpoint catalog. Authorization is object-level and all mutations re-check current state inside the service transaction.

### `GET /api/notifications`
- **Purpose:** List own notifications
- **Authentication:** JWT/session
- **Authorization:** Recipient only
- **Request:** page, unread filter
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 200 list
- **Errors:** —; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** Safe GET
- **Side effects:** —

### `POST /api/notifications/{id}/read`
- **Purpose:** Mark own notification read
- **Authentication:** JWT/session
- **Authorization:** Recipient only
- **Request:** —
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 200/204
- **Errors:** AUTHORIZATION_DENIED; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** State-idempotent
- **Side effects:** —
