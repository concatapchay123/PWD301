# Question Bank Api

This file expands the relevant entries from the endpoint catalog. Authorization is object-level and all mutations re-check current state inside the service transaction.

### `POST /api/courses/{course_id}/questions`
- **Purpose:** Create Question
- **Authentication:** JWT
- **Authorization:** Current Course manager
- **Request:** type, content, choices/answers, provenance
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 201 Question
- **Errors:** VALIDATION_ERROR; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** request key optional
- **Side effects:** —

### `PATCH /api/questions/{question_id}`
- **Purpose:** Edit Question/revision
- **Authentication:** JWT
- **Authorization:** Current Course manager/Admin override
- **Request:** content/answers + row_version + reason if correction
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 200 Question/revision
- **Errors:** TYPE_LOCKED / CONFLICT; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** conditional rowversion
- **Side effects:** correction/regrade if used

### `DELETE /api/questions/{question_id}`
- **Purpose:** Trash/delete Question
- **Authentication:** JWT
- **Authorization:** Current manager/Admin
- **Request:** reason
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 204/200
- **Errors:** HISTORY_REQUIRES_TOMBSTONE; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** State-idempotent
- **Side effects:** audit/cleanup policy

### `POST /api/questions/{question_id}/corrections`
- **Purpose:** Approve correction
- **Authentication:** JWT
- **Authorization:** Current Course manager/Admin override
- **Request:** new revision,correction_type,reason
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 202 correction/job
- **Errors:** VALIDATION_ERROR / CONFLICT; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** correction id unique
- **Side effects:** audit + regrade job

### `PATCH /api/imports/{import_id}/questions/{item_id}`
- **Purpose:** Review imported item
- **Authentication:** JWT
- **Authorization:** Current Course manager
- **Request:** keep/edit/reject, official answer confirmation
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 200 item
- **Errors:** VALIDATION_ERROR; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** conditional state
- **Side effects:** provenance

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
