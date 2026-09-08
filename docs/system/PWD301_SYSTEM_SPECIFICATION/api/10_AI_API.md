# Ai Api

This file expands the relevant entries from the endpoint catalog. Authorization is object-level and all mutations re-check current state inside the service transaction.

### `POST /api/ai/questions/generate`
- **Purpose:** Generate question drafts
- **Authentication:** JWT
- **Authorization:** Current Course manager
- **Request:** authorized sources, distribution, count
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 202/200 drafts
- **Errors:** AI_UNAVAILABLE / RATE_LIMITED; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** request id/dedupe
- **Side effects:** AI usage/provenance

### `POST /api/ai/chat`
- **Purpose:** LMS-scoped AI message
- **Authentication:** Session/JWT
- **Authorization:** Actor resource permissions
- **Request:** conversation_id,message,context target
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 200 answer+sources
- **Errors:** OUT_OF_SCOPE / INSUFFICIENT_EVIDENCE / AI_UNAVAILABLE; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** request id
- **Side effects:** reset 5-min expiry; source usage
