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
- **Request:** empty body remains supported; optional JSON `expected_authoring_token` from the managing Instructor's assessment detail or atomic authoring acknowledgement.
- **Validation:** schema + domain state + object relationship; reject unknown privileged fields (mass-assignment safe).
- **Success:** 200 Assessment
- **Errors:** BLUEPRINT_SHORTAGE / VALIDATION_ERROR / CONFLICT; a stale authoring token returns 409 before publication. JSON error includes stable code, message, optional field errors, correlation ID.
- **Idempotency:** State-idempotent
- **Side effects:** audit + schedule reminders

The optional token represents editable settings, assigned question order/points/revisions, fixed pool entries and their question semantics, and blueprint rule intent. Generated nonfixed pool rows are derived from that intent using Algorithm 05; their random selection and regenerated row identifiers do not change the token. The unselected eligible question bank remains dynamic. The server compares the token while holding the assessment and relevant authoring row locks; candidate selection, publication and mandatory audit share the same transaction. Publish and attempt-start telemetry do not change this token, so matching retries remain state-idempotent. Session-authenticated Instructor publication uses the same optional condition. Tokens are exposed only to managers receiving authoring details; they are not included in Student delivery.

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

### `POST /instructor/assessments/{assessment_id}/authoring`
- **Purpose:** Atomically save assessment settings and the complete ordered question manifest.
- **Authentication:** Same-origin session + CSRF; current Course manager authorization.
- **Request:** Optional `assessment` settings object and required `questions` array. Existing questions use public `question_id`; new questions use stable public `client_question_id` UUIDs for retry. Omitted assignments are removed; order and assigned points are saved together.
- **Success:** 200 standard `{"success":true,"data":...,"error":null}` envelope. `data` contains `assessment_id`, acknowledged `questions` with public `question_id`, `question_assignments`, and `authoring_token` derived inside the transaction.
- **Freeze:** The parent Assessment is locked and refreshed before checking the first-attempt marker. Structure cannot change after a Student starts, including through legacy section/assignment/blueprint writers.
- **Atomicity/retry:** Any question/settings/assignment failure rolls back the complete request. The client checkpoints acknowledged identities and submits the token to conditional publication. Lost publication acknowledgement is recovered by reading matching published state rather than writing frozen authoring again.

### `POST /instructor/assessments/{assessment_id}/questions/create`
- **Purpose:** Create one bank question and its assessment assignment in one transaction.
- **Authentication:** Session + CSRF; current Course manager authorization.
- **Retry:** Optional `client_question_id` public UUID identifies one creation intent. The Quick Add form retains it until acknowledgement. A retry for the same assessment and saved question semantics returns 200 with the existing question and assignment; initial creation returns 201. Assigned points are compared at canonical SQL DECIMAL(9,4) precision. Reusing the UUID for another assessment or changed content, type, difficulty, stored points, explanation or answers returns 409 without writes. Non-finite, zero and negative points are rejected before writes.
- **Freeze/atomicity:** Parent locking serializes creation with first-attempt admission and retries. New creation is forbidden after the first attempt. A matching retry may read the existing acknowledgement after freeze. Question/revision/provenance/assignment failure rolls back together.
