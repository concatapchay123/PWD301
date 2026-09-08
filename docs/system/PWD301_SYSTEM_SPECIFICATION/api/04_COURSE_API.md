# Course Api

This file expands the relevant entries from the endpoint catalog. Authorization is object-level and all mutations re-check current state inside the service transaction.

### `GET /api/courses`
- **Purpose:** Course catalog
- **Authentication:** Optional/JWT
- **Authorization:** Published/discoverable
- **Request:** q, filters, page, sort
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 200 paginated list
- **Errors:** VALIDATION_ERROR; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** Safe GET
- **Side effects:** —

### `POST /api/courses`
- **Purpose:** Create Course
- **Authentication:** JWT
- **Authorization:** Instructor/Admin
- **Request:** course_code,title,description,capacity,...
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 201 Course
- **Errors:** VALIDATION_ERROR / CONFLICT; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** client request key optional
- **Side effects:** audit as policy

### `PATCH /api/courses/{course_id}`
- **Purpose:** Update Course
- **Authentication:** JWT
- **Authorization:** Current owner or Admin override
- **Request:** allowed mutable fields + row_version
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 200 Course
- **Errors:** AUTHORIZATION_DENIED / CONFLICT / STATE_VIOLATION; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** conditional rowversion
- **Side effects:** material-change review/audit

### `POST /api/courses/{course_id}/publish-request`
- **Purpose:** Submit Course for review/publish
- **Authentication:** JWT
- **Authorization:** Current owner
- **Request:** reason/change metadata if applicable
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 202/200
- **Errors:** STATE_VIOLATION; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** State-idempotent
- **Side effects:** audit/notification

### `POST /api/courses/{course_id}/archive`
- **Purpose:** Archive Course
- **Authentication:** JWT
- **Authorization:** Owner/Admin per policy
- **Request:** reason
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 200
- **Errors:** PREREQUISITE_DEPENDENCY / CONFLICT; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** State-idempotent
- **Side effects:** audit/RAG invalidation

### `POST /api/courses/{course_id}/enroll`
- **Purpose:** Enroll current Student
- **Authentication:** JWT
- **Authorization:** Self as Student
- **Request:** —
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 201/200 Enrollment
- **Errors:** PREREQUISITE_NOT_MET / COURSE_FULL / CONFLICT; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** Idempotent for already-active enrollment
- **Side effects:** enrollment event

### `POST /api/courses/{course_id}/leave`
- **Purpose:** Leave Course
- **Authentication:** JWT
- **Authorization:** Active enrollment owner
- **Request:** confirmation
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 200
- **Errors:** STATE_VIOLATION; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** State-idempotent
- **Side effects:** start retention window

### `GET /api/courses/{course_id}/progress`
- **Purpose:** Read own/authorized progress
- **Authentication:** JWT
- **Authorization:** Self or current manager/Admin-with-reason
- **Request:** —
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 200 progress
- **Errors:** AUTHORIZATION_DENIED; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** Safe GET
- **Side effects:** —

### `POST /api/lessons/{lesson_id}/activity`
- **Purpose:** Record bounded learning activity
- **Authentication:** Session/JWT
- **Authorization:** Authorized enrolled Student
- **Request:** view evidence/time delta/client event id
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 200 progress
- **Errors:** VALIDATION_ERROR / AUTHORIZATION_DENIED; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** event/delta dedupe
- **Side effects:** may recompute completion

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
