# Course Api

This file expands the relevant entries from the endpoint catalog. Authorization is object-level and all mutations re-check current state inside the service transaction.

### `POST /instructor/courses/{course_id}/lessons/reorder`
- Session authentication and CSRF; current course manager only. Supply the complete active course order in `ordered_lesson_ids`, including lessons in other chapters.
- Optional `move` object contains `lesson_id` and destination `learning_unit_id`. Placement and order form one transaction and retain the Lesson ID/content. Both objects must belong to this course; reject deleted destinations, historical/trashed lessons, invalid/incomplete orders and destination chapter lesson/media limits.
- Draft-course success is 200 with acknowledged lessons. For an approved/published/archived course, 202 and `pending_approval` mean one structural review intent was queued; current placement/order remain authoritative. Identical pending retries return the same request; a different proposal conflicts409 instead of falsely acknowledging the old proposal.
- The existing Admin change-request review endpoint applies both placement and order in its review transaction. A failed mutation or required audit rolls back placement/order and keeps the request PENDING. Review metadata includes readable lesson/source/destination chapter names; the client displays those names and proposed order, retaining the current tree until approval.

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

### `POST /api/courses/{course_id}/leave` & `POST /student/courses/{course_id}/leave`
- **Purpose:** Voluntary course withdrawal (**PERMANENTLY DISABLED / FORBIDDEN**)
- **Authentication:** Session/JWT
- **Authorization:** Disabled for all students (`ENROLLMENT_LIFETIME_GUARANTEE`).
- **Behavior:** Returns HTTP 403 Forbidden (`FORBIDDEN`). Enrollments are permanent lifetime assets.
- **Errors:** FORBIDDEN ("Chức năng rời khóa học đã bị vô hiệu hóa. Khóa học đã ghi danh sẽ gắn liền với tài khoản học viên trọn đời.")

### `POST /instructor/courses/{course_id}/changeset/submit`
- **Purpose:** Submit Unified Staging Draft (`STAGING_DRAFT`) for single-submission Admin review.
- **Authentication:** Session + CSRF
- **Authorization:** Current Course manager
- **Behavior:** Consolidates all pending course metadata, cover image, curriculum, lessons, quizzes, and resources into 01 `CourseVersionChangeset` with status `PENDING`.
- **Success:** 200 {"success": true, "data": {"change_request_id": ...}}
- **Errors:** STATE_VIOLATION / CONFLICT

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

### `PUT /instructor/courses/{course_id}/academic-settings`
- **Purpose:** Save the complete academic settings edit in one transaction.
- **Authentication:** Same-origin session + CSRF.
- **Authorization:** Current Course manager; prerequisite and approval policies still apply.
- **Request:** `learning_objectives`, required `completion_rules` object, and optional `prerequisites` object containing `add` objects and `remove` public Course UUIDs. At most 100 prerequisite edits per request.
- **Success:** Standard `{"success":true,"data":...,"error":null}` envelope. `data` contains `course`, `completion_rules` and `pending_approval`; 202 means review is pending, 200 means the submitted changes were applied.
- **Atomicity:** Invalid settings or any prerequisite failure rolls back all submitted changes and review/notification intents. Published SLO/removal changes and peer prerequisite requests retain their existing approval workflows.
- **Errors:** Standard validation/authorization/conflict error response; the client retains the submitted draft until acknowledgement.
