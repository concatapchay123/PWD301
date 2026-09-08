# Assessment Api

This file expands the relevant entries from the endpoint catalog. Authorization is object-level and all mutations re-check current state inside the service transaction.

### `POST /api/assessments`
- **Purpose:** Create draft Assessment
- **Authentication:** JWT
- **Authorization:** Current Course manager
- **Request:** type,title,config
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 201 Assessment
- **Errors:** VALIDATION_ERROR; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** request key optional
- **Side effects:** —

### `PATCH /api/assessments/{assessment_id}`
- **Purpose:** Edit draft/published-allowed config
- **Authentication:** JWT
- **Authorization:** Current Course manager/Admin override
- **Request:** mutable fields + row_version
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 200 Assessment
- **Errors:** TIMING_LOCKED / STRUCTURE_LOCKED / POINTS_LOCKED; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** conditional rowversion
- **Side effects:** audit when sensitive

### `POST /api/assessments/{assessment_id}/publish`
- **Purpose:** Validate and publish
- **Authentication:** JWT
- **Authorization:** Current Course manager
- **Request:** —
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 200 Assessment
- **Errors:** BLUEPRINT_SHORTAGE / VALIDATION_ERROR; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** State-idempotent
- **Side effects:** audit + schedule reminders

### `POST /api/assessments/{assessment_id}/attempts`
- **Purpose:** Start or return eligible Attempt
- **Authentication:** JWT
- **Authorization:** Enrolled eligible Student as self
- **Request:** optional idempotency key
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 201/200 Attempt snapshot metadata
- **Errors:** NOT_OPEN / CLOSED / ATTEMPT_LIMIT / CONFLICT; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** Start key + uniqueness/attempt no
- **Side effects:** materialize snapshot
