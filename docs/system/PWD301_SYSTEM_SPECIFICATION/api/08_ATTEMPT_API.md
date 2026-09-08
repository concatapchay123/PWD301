# Attempt Api

This file expands the relevant entries from the endpoint catalog. Authorization is object-level and all mutations re-check current state inside the service transaction.

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

### `GET /api/attempts/{attempt_id}`
- **Purpose:** Resume Attempt
- **Authentication:** JWT
- **Authorization:** Attempt owner/current authorized viewer
- **Request:** —
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 200 snapshot/current answers
- **Errors:** AUTHORIZATION_DENIED; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** Safe GET
- **Side effects:** —

### `POST /api/attempts/{attempt_id}/lease`
- **Purpose:** Acquire/take over edit lease
- **Authentication:** JWT
- **Authorization:** Attempt owner
- **Request:** tab_session_id
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 200 lease token/expiry
- **Errors:** LEASE_CONFLICT / TERMINAL_STATE; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** conditional lease
- **Side effects:** —

### `POST /api/attempts/{attempt_id}/heartbeat`
- **Purpose:** Renew lease
- **Authentication:** JWT
- **Authorization:** Attempt owner + current lease
- **Request:** lease_token
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 200 new expiry
- **Errors:** LEASE_CONFLICT / DEADLINE_EXPIRED; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** Retry-safe for same lease
- **Side effects:** —

### `PUT /api/attempts/{attempt_id}/answers/{attempt_question_id}`
- **Purpose:** Save answer
- **Authentication:** JWT
- **Authorization:** Attempt owner + valid lease
- **Request:** lease_token,client_change_id,client_sequence,answer
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 200 saved version/timestamp
- **Errors:** LEASE_CONFLICT / DEADLINE_EXPIRED / STALE_ANSWER; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** client_change_id idempotent
- **Side effects:** answer event

### `POST /api/attempts/{attempt_id}/submit`
- **Purpose:** Submit/finalize Attempt
- **Authentication:** JWT
- **Authorization:** Attempt owner
- **Request:** idempotency_key, lease token if still required
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 200 result/pending status
- **Errors:** DEADLINE_EXPIRED handled by finalization / CONFLICT; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** Required idempotency
- **Side effects:** grade objective answers; result

### `POST /api/attempts/{attempt_id}/grades/{attempt_question_id}`
- **Purpose:** Grade/revise essay
- **Authentication:** JWT
- **Authorization:** Current Course Instructor/Admin override
- **Request:** score,feedback,reason,row_version
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 200 grade/result
- **Errors:** VALIDATION_ERROR / CONFLICT; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** conditional version
- **Side effects:** history + audit + notification when result changes

### `GET /api/regrade-jobs/{job_id}`
- **Purpose:** Read regrade status
- **Authentication:** JWT
- **Authorization:** Current Course manager/Admin
- **Request:** —
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 200 progress
- **Errors:** AUTHORIZATION_DENIED; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** Safe GET
- **Side effects:** —
