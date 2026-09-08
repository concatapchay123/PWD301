# File Import Api

This file expands the relevant entries from the endpoint catalog. Authorization is object-level and all mutations re-check current state inside the service transaction.

### `POST /api/files`
- **Purpose:** Upload logical file revision
- **Authentication:** Session/JWT
- **Authorization:** Authorized Instructor/Admin
- **Request:** multipart file + owner context
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 202 quarantined asset/revision
- **Errors:** FILE_REJECTED / QUOTA_EXCEEDED; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** content hash/job dedupe
- **Side effects:** scan/process job

### `GET /api/files/{file_id}/download`
- **Purpose:** Authorized file download
- **Authentication:** Session/JWT
- **Authorization:** Authorized resource viewer
- **Request:** —
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** stream/redirect through controlled route
- **Errors:** FILE_NOT_SAFE / AUTHORIZATION_DENIED; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** Safe GET
- **Side effects:** access policy

### `POST /api/imports`
- **Purpose:** Start DOCX/PDF import
- **Authentication:** JWT
- **Authorization:** Current Course manager
- **Request:** safe file revision + target course
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 202 ImportJob
- **Errors:** FILE_NOT_SAFE / VALIDATION_ERROR; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** one job key
- **Side effects:** import worker

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
