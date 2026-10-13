# Admin Api

This file expands the relevant entries from the endpoint catalog. Authorization is object-level and all mutations re-check current state inside the service transaction.

### `POST /api/admin/users/{user_id}/suspend`
- **Purpose:** Suspend account
- **Authentication:** JWT/session
- **Authorization:** Admin + reauth + reason/phrase policy
- **Request:** reason,confirmation
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 200
- **Errors:** REAUTH_REQUIRED / CONFIRMATION_MISMATCH; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** State-idempotent
- **Side effects:** revoke all auth + audit + notify

### `POST /api/admin/courses/{course_id}/reassign`
- **Purpose:** Reassign Course
- **Authentication:** JWT/session
- **Authorization:** Admin + reason
- **Request:** new_instructor_id,reason
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 200
- **Errors:** INVALID_ROLE / CONFLICT; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** conditional rowversion
- **Side effects:** audit + notifications

### `POST /api/admin/backups`
- **Purpose:** Trigger manual backup
- **Authentication:** JWT/session
- **Authorization:** Admin + sensitive policy
- **Request:** reason
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 202 BackupRun
- **Errors:** REAUTH_REQUIRED; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** request id
- **Side effects:** audit/job

### `POST /api/admin/backups/{backup_id}/restore`
- **Purpose:** Explicit restore workflow
- **Authentication:** Session preferred
- **Authorization:** Admin + fresh password + exact phrase + reason
- **Request:** reason,confirmation
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 202/accepted controlled workflow
- **Errors:** REAUTH_REQUIRED / CONFIRMATION_MISMATCH; JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** dedupe operation id
- **Side effects:** mandatory audit; never automatic overwrite

### Session course changeset approval routing

`POST /admin/course-changes/{change_request_id}/approve` and `POST /admin/courses/{course_id}/changeset/approve` apply consolidated course version changesets. The request must have `change_type=COURSE_VERSION_CHANGESET` or a JSON object with `action=COURSE_VERSION_CHANGESET`. The endpoint locks and refreshes the request before validating its pending state and type. Other request types return `400 VALIDATION_ERROR` and retain their pending state; no successful decision or audit may be recorded without applying their intended action.

Resource attachment/detachment and other individual change requests use `POST /admin/change-requests/{change_request_id}/review` with `action=approve` or `action=reject` plus `reason`. They must not be submitted to the dedicated course version approval endpoint.

### Exact session change-request detail

`GET /admin/change-requests?request_id={id}` requires an authenticated Admin with `COURSE_REVIEW`. It returns the named request independently of its current review status, including completed requests. Invalid identifiers return 400; a missing request returns 404. The exact identifier takes precedence over queue status filtering. The aggregate queue retains its pending-only behavior, including `status=ALL`; completed requests remain available through their authorized exact detail URL.
