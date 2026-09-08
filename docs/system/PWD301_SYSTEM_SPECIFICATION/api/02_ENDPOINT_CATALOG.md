# Endpoint Catalog

Paths are **DERIVED API DESIGN** unless the path is required by rubric/source. Business behavior is normative; route naming may be adjusted consistently before implementation.

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
