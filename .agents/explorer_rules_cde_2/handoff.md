# Subsystems C, D, & E Invariant & Business Rule Conformance Audit Report

**Working Directory**: `e:\PWD301\.agents\explorer_rules_cde_2`  
**Milestone**: Subsystems C (Assessments & Grading), D (Files & Media Security), & E (AI/RAG, Audit, Operations)  
**Author**: `explorer_rules_cde_2`  
**Date**: 2026-09-11  

---

## 1. Observation

### 1.1 Specification & Database Reference DDL Invariants
The authoritative rules for Subsystems C, D, and E originate from:
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/01_BUSINESS_RULE_CATALOG.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md`
- `docs/database/PWD301_DATABASE_ARCHITECTURE/13_CONSTRAINTS_AND_INVARIANTS.md`
- `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/012_critical_invariant_triggers.sql`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/algorithms/07_ATTEMPT_LEASE_ALGORITHM.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/security/01_THREAT_MODEL.md`

Verbatim triggers and constraints observed:
1. `012_critical_invariant_triggers.sql` lines 41-53 (`trg_assessments_timing_immutable`):
   ```sql
   -- 2. Window Timing (close_at): only forward extension allowed once published; shortening or terminal modification is forbidden
   IF EXISTS (
       SELECT 1
       FROM inserted i
       JOIN deleted d ON d.id = i.id
       WHERE d.published_at IS NOT NULL
         AND (
             (d.status IN ('ARCHIVED','CANCELLED','TRASH') AND ISNULL(i.close_at, CONVERT(DATETIME2(3),'1900-01-01')) <> ISNULL(d.close_at, CONVERT(DATETIME2(3),'1900-01-01')))
             OR (d.close_at IS NOT NULL AND i.close_at IS NULL)
             OR (d.close_at IS NOT NULL AND i.close_at IS NOT NULL AND i.close_at < d.close_at)
         )
   )
       THROW 51007, 'Assessment close_at can only be extended forward into the future after publish.', 1;
   ```
2. `012_critical_invariant_triggers.sql` lines 57-133 (`trg_assessment_assignments_structure_lock`, `trg_assessment_pool_structure_lock`, `trg_assessment_sections_structure_lock`, `trg_blueprint_rules_structure_lock`):
   Throws errors 51002, 51003, 51004, 51005 when `a.first_attempt_started_at IS NOT NULL`.
3. `012_critical_invariant_triggers.sql` lines 255-264 (`trg_audit_events_append_only`):
   ```sql
   CREATE OR ALTER TRIGGER trg_audit_events_append_only
   ON audit_events
   AFTER UPDATE, DELETE
   AS
   BEGIN
       SET NOCOUNT ON;
       IF EXISTS (SELECT 1 FROM deleted)
           THROW 51012, 'Audit events are append-only. Corrections must be new events.', 1;
   END;
   ```
4. `07_ATTEMPT_LEASE_ALGORITHM.md` line 3:
   > "Acquire uses conditional update: if no active lease, same tab owner, or `lease_expires_at <= now`, set owner/session, random lease token, heartbeat and new expiry. Second tab while lease valid gets LEASE_CONFLICT. Heartbeat validates token+owner+nonterminal attempt then extends expiry. Takeover is allowed only after stale expiry and keeps same Attempt/snapshot/deadline. Save requires current token."
5. `01_THREAT_MODEL.md` row 13 (`SEC-CONC-02`):
   > "Attempt takeover | active exam | second tab steals lease | expiring tokenized lease + conditional update | lease conflict | SEC-CONC-02"

---

### 1.2 Codebase Implementation Observations

#### Subsystem C: Assessments, Attempts, Leases, Locking, Autosave, Submissions, Grading & Regrading
1. **Assessment Timing Freeze (`ASSESS-001`)**:
   In `src/pwd301/services/assessment_service.py` lines 649-655:
   ```python
   if "close_at" in payload:
       new_close = _parse_iso_datetime(payload.get("close_at"), "close_at")
       cur_close = _normalize_dt(assessment.close_at)
       norm_new_close = _normalize_dt(new_close)
       if cur_close is not None and norm_new_close is not None and norm_new_close <= cur_close:
           raise AssessmentLockedError("close_at can only be extended forward after publish.")
   ```
   At lines 695-696:
   ```python
   if "close_at" in payload:
       assessment.close_at = _parse_iso_datetime(payload.get("close_at"), "close_at")
   ```
   *Direct observation*: If `payload` contains `{"close_at": null}` or `{"close_at": ""}`, `norm_new_close` is `None`. The check `cur_close is not None and norm_new_close is not None and norm_new_close <= cur_close` evaluates to `False`. Thus `AssessmentLockedError` is NOT raised. Line 696 sets `assessment.close_at = None`, wiping out the close deadline on an active published assessment.

2. **Single Active Editing Lease & Takeover (`ATTEMPT-003`, Invariant 10)**:
   In `src/pwd301/services/attempt_service.py` lines 813-865:
   ```python
   def takeover_attempt_lease(
       actor: User,
       attempt_id: AssessmentAttempt | int | uuid.UUID | str,
       session: Session | scoped_session[Any] | None = None,
   ) -> tuple[AssessmentAttempt, str]:
       ...
       attempt = _resolve_attempt(attempt_id, session=sess)
       if attempt is None:
           raise AttemptNotFoundError("Assessment attempt not found.")

       if attempt.student_user_id != actor.id:
           raise ForbiddenError("You do not have permission to manage this assessment attempt lease.")

       now = utc_now()
       _check_and_expire_if_needed(sess, attempt, now)

       raw_token, token_hash, acquired_at, expires_at = _generate_lease(lease_seconds=lease_seconds)
       ...
       attempt.lease_token_hash = token_hash
       attempt.lease_acquired_at = acquired_at
       attempt.last_heartbeat_at = acquired_at
       attempt.lease_expires_at = expires_at
       attempt.lease_epoch = (attempt.lease_epoch or 1) + 1
       attempt.updated_at = now
   ```
   In `src/pwd301/blueprints/api_attempts/routes.py` lines 149-158:
   ```python
   @api_attempt_bp.route("/api/attempts/<attempt_id>/lease/takeover", methods=["POST"])
   @api_attempt_bp.route("/api/attempts/<attempt_id>/lease", methods=["POST"])
   @jwt_required
   def takeover_attempt_lease_route(attempt_id: str) -> tuple[Response, int] | Response:
       actor = require_authenticated_actor()
       attempt, raw_token = takeover_attempt_lease(...)
   ```
   *Direct observation*: `takeover_attempt_lease` never checks `attempt.lease_expires_at <= now`. It allows an immediate and unconditional lease takeover while the active tab's lease is still valid and being heartbeated. Both `/lease` and `/lease/takeover` routes immediately execute this unconditional takeover.

3. **Structural & Assigned Points Locking (`ASSESS-002`, `ASSESS-003`, Invariant 14)**:
   In `src/pwd301/services/assessment_service.py`:
   - `assign_question` (lines 1179-1182): checks `assessment.first_attempt_started_at is not None` -> raises `AssessmentLockedError`.
   - `remove_question_assignment` (lines 1288-1291): checks `first_attempt_started_at` -> raises `AssessmentLockedError`.
   - `create_section` (lines 1076-1079) & `delete_section` (lines 1131-1134): checks `first_attempt_started_at` -> raises `AssessmentLockedError`.
   - `configure_blueprint` (lines 1346-1349) & `materialize_blueprint_pool` (lines 1486-1489): checks `first_attempt_started_at` -> raises `AssessmentLockedError`.
   - `update_assessment` (lines 609-623): checks `first_attempt_started_at` for `assessment_type` and `random_question_count` -> raises `AssessmentLockedError`.

4. **Attempt Presentation Snapshot (`ASSESS-006`, `ATTEMPT-001`, Invariant 8)**:
   In `src/pwd301/services/attempt_service.py` lines 469-540:
   - Fixed assignments and candidate pool are snapshotted into `AttemptQuestion` rows.
   - Exact `question_type_snapshot`, `content_snapshot`, `explanation_snapshot`, `points_assigned`, `position` frozen.
   - Choices are snapshotted into `AttemptChoiceSnapshot` with random `choice_key_snapshot`, preserving `is_fixed_position`.
   - `rev.was_student_exposed = True` is marked on the QuestionRevision (`QBANK-005`).

5. **Server-Authoritative Deadline & Hard Close (`ATTEMPT-002`, Invariant 9)**:
   In `src/pwd301/services/attempt_service.py` lines 171-193 (`_calculate_deadline`) & lines 195-235 (`_check_and_expire_if_needed`):
   - Deadline is computed on the server as `min(started_at + time_limit_minutes, close_at)`.
   - If `utc_now() >= deadline_at` or `utc_now() >= close_at`, attempt auto-transitions to `EXPIRED` and rejects further actions.

6. **Autosave Sequencing & Lease Epoch Fencing (`ATTEMPT-004`, `ATTEMPT-005`, `ATTEMPT-006`)**:
   In `src/pwd301/services/attempt_service.py` lines 1041-1160 (`save_attempt_answer`):
   - Validates lease token hash via constant-time HMAC digest.
   - Enforces `payload.lease_epoch >= attempt.lease_epoch` (stale epoch rejected with 409).
   - Enforces `client_sequence > last_client_sequence` (older sequence rejected with 409).
   - Idempotency: Duplicate `client_change_id` returns existing accepted version without duplicate write.
   - Expiration: Any write after deadline raises `AttemptExpiredError`.

7. **Submit Idempotency (`ATTEMPT-007`, Invariant 12)**:
   In `src/pwd301/services/attempt_service.py` lines 1512-1670 (`submit_assessment_attempt`):
   - Enforces UUID `idempotency_key`.
   - If attempt is already `SUBMITTED`/`PENDING_GRADING`/`GRADED` with the matching key, returns the existing result (`is_idempotent_replay: True`).
   - If called with a different key, raises `SubmissionIdempotencyConflictError` (409).
   - Atomically updates `WHERE status = 'IN_PROGRESS'`.
   - Revokes active lease tokens upon submission.

8. **Objective and Essay Grading (`GRADE-001`, `GRADE-002`, `QBANK-006`, `QBANK-007`)**:
   In `src/pwd301/services/attempt_service.py` lines 1894-2080:
   - `SINGLE_CHOICE` and `TRUE_FALSE`: Exactly 1 choice selected matching correct choice gives 100% points, else 0.
   - `MULTIPLE_CHOICE`: Exact set comparison (`selected_keys == correct_keys`), no partial credit (`QBANK-006`).
   - `SHORT_ANSWER`: Normalization (NFKC lowercase) or Exact match (`QBANK-007`).
   - `ESSAY`: Awarded points 0, status `PENDING`, grading rule `MANUAL`. Attempt status `PENDING_GRADING` (`GRADE-001`).
   - Manual grading in `grade_essay_question` writes to `AttemptQuestionGradeHistory` with `old_points`, `new_points`, `reason`, and actor (`GRADE-002`).

9. **Resumable and Idempotent Regrading (`REGRADE-001` to `REGRADE-004`)**:
   In `src/pwd301/services/regrade_worker.py`:
   - `ANSWER_ONLY`: Re-evaluates objective choices against new revision (`REGRADE-001`).
   - `CONTENT_OR_CHOICES`: Grants full credit (`CONTENT_FULL_CREDIT`) to earlier attempts (`REGRADE-002`).
   - `AttemptQuestion` snapshots and student answers are never rewritten; only `AttemptQuestionGrade` and `AssessmentResultHistory` are updated/appended (`REGRADE-003`).
   - Per-item tracking (`RegradeItem`), batching, and retry limits provide resumability and idempotency (`REGRADE-004`).

---

#### Subsystem D: Files, Uploads, Security, Quarantine, Media Limits (< 1 GB), Path Exposure
1. **Quarantine & Fail-Closed Malware Scan (`FILE-001`, Invariant 18)**:
   In `src/pwd301/services/file_service.py` lines 307-550:
   - Uploads stream directly into temporary quarantine storage (`FILE_QUARANTINE_ROOT`).
   - Multi-engine malware scanning is performed while quarantined.
   - Only when `main_verdict.status == "PASS"` is the blob promoted to permanent storage and FileAsset/FileRevision activated.
   - If malware is found (`FAIL`), file is moved to `quarantine/infected/`, marked `REJECTED`, and revision `is_current = False`.
   - If scanner errors or times out (`ERROR`), file remains in quarantine, marked `QUARANTINED`, and revision `is_current = False`.

2. **Download Authorization & Fail-Closed Access (`FILE-005`)**:
   In `src/pwd301/services/file_service.py` lines 902-1025 (`get_file_for_download`):
   - Zero-Trust check: Admin allowed; Instructor must own course; Student must have ACTIVE enrollment in published course and published lesson.
   - If revision status is `REJECTED`, raises `FileInfectedError` (403).
   - If revision status is `QUARANTINED`, raises `FileSecurityQuarantineError` (403).
   - If any scan result is `FAIL` or `ERROR`, access is denied (fail-closed).
   - Physical storage paths are never returned in JSON metadata responses (`_serialize_file_asset` masks internal PKs and exposes only public UUIDs).

3. **Macro Office Ban & Upload Limits (`FILE-002`, Media Limits < 1 GB)**:
   - In `src/pwd301/services/file_service.py` lines 61-94: `DANGEROUS_EXTENSIONS` includes `.docm`, `.xlsm`, `.pptm`, `.dotm`, `.xltm`, `.potm`.
   - Video upload limit is strictly `< 1 GB` (1,000,000,000 bytes): `MAX_VIDEO_BYTES_EXCLUSIVE = 1_000_000_000`.
   - `LimitingStream` (lines 105-126) aborts streaming immediately if cumulative bytes reach 1 GB to protect against disk exhaustion.
   - `import_service.py` (lines 118-160) defends against zip bombs and zip-slip attacks.

4. **SHA-256 Deduplication (`FILE-003`) & Replacement Safety (`FILE-004`)**:
   - `store_file_stream` calculates SHA-256 digest and reuses existing `FileBlob` with `reference_count += 1`.
   - `add_file_revision` validates and scans replacement file before updating `is_current = True`. Old revision transitions to `REPLACED` and remains recoverable for 30 days.

5. **API Endpoint Route Decorator Discrepancy**:
   In `src/pwd301/blueprints/api_files/routes.py` lines 238-249:
   ```python
   @api_file_bp.route("/<asset_id>/quarantine-override", methods=["POST"])
   @jwt_required
   def quarantine_override_api(asset_id: str) -> tuple[Response, int] | Response:
   ```
   *Direct observation*: Missing `@admin_required` route decorator. (The service function `quarantine_override` enforces `if not admin_actor.is_admin: raise FileAccessDeniedError`, but route-level defense-in-depth is omitted).

---

#### Subsystem E: AI/RAG, 5-min Ephemeral Chat Deletion, Append-only Audit, DB Restore Safety
1. **Student RAG Pre-Retrieval Authorization & Invariant Exclusions (`AI-001`, `AI-002`, Invariant 20)**:
   In `src/pwd301/services/rag_service.py` lines 712-850 (`retrieve_relevant_chunks`):
   - Pre-retrieval authorization: Checks whether student actor has an ACTIVE `Enrollment` in the course before executing any document/chunk query. Unenrolled actors receive `ForbiddenError` (403).
   - Invariant exclusion: If course status is `ARCHIVED`, `TRASH`, or `DRAFT`, immediately returns `[]`.
   - Chunks from non-published lessons or non-active/quarantined files are strictly excluded.
   - Grounded citations: Records `AISourceUsage` referencing chunk, document, and version (`AI-006`).

2. **5-Minute Ephemeral Chat Content Purging (`AI-003`, Invariant 21)**:
   - In `src/pwd301/services/ai_service.py` lines 338-346, 365-377: If `conv.last_activity_at <= now - 300s`, conversation transitions to `EXPIRED` and `send_chat_message` raises `AIConversationExpiredError`.
   - In `src/pwd301/services/retention_service.py` lines 595-639 (`purge_inactive_ai_chats`): Targets conversations inactive for > 300 seconds, permanently deletes all child `AIMessage` rows to wipe raw content, while preserving minimal parent `AIConversation` metadata.

3. **Deterministic Recommendations with AI Explanation (`AI-005`)**:
   In `src/pwd301/services/recommendation_service.py` lines 80-280:
   - Backend evaluates course prerequisites, category affinities, difficulty progression, and completion status deterministically.
   - Gemini LLM is invoked solely to enrich the output with explanatory rationale.

4. **Append-Only & Fail-Closed Audit Logging (`AUDIT-001`, `AUDIT-002`, Invariant 22)**:
   - `src/pwd301/models/notification_audit.py`: `AuditEvent` table has no delete or update relations.
   - `src/pwd301/services/audit_service.py`: All sensitive workflows (`suspend_user_account`, `record_audit_event`) commit audit logs within the same database transaction. Any audit insertion failure rolls back the mutation and raises `AuditPersistenceError`.
   - Recursive redaction (`redact_sensitive_data`) sanitizes passwords, API keys, tokens, and secrets from `before_json`/`after_json`.
   - SQL Server Reference DDL enforces `trg_audit_events_append_only`.

5. **Admin Content Override Reason & Notification (`AUDIT-003`, Invariant 23)**:
   In `src/pwd301/services/course_service.py` lines 446-455 (`update_course`) and `src/pwd301/services/lesson_service.py` lines 412-425 (`update_lesson`):
   - When an Administrator updates a course or lesson owned by an instructor:
     - `reason` is taken from `data.get("reason")` which is optional (can be `None`).
     - No notification event is emitted to the course's owning instructor.

6. **Database Restore Drill & Live DB Safety (`OPS-004`)**:
   In `src/pwd301/services/operations_service.py` lines 965-1135 (`restore_database_snapshot`):
   - Invariant: Live database restore NEVER occurs automatically.
   - Requires Administrator role (`_require_admin`).
   - Requires exact confirmation phrase: `CONFIRM_DATABASE_RESTORE`.
   - Requires fresh Admin password re-authentication (`actor.verify_password(password)`).
   - Verifies target backup checksum and SHA-256 hash.
   - Emits fail-closed audit logs `DATABASE_RESTORE_INITIATED` and `DATABASE_RESTORE_COMPLETED`.
   - Acquires mutex `_restore_lock` to block concurrent restores.

---

### 1.3 Test Suite Execution Results
Two test runs were performed during the audit:
1. Unit test suite:
   `.\.venv\Scripts\pytest.exe tests/unit/test_assessment_service.py tests/unit/test_attempt_lease_service.py tests/unit/test_file_service.py tests/unit/test_rag_service.py tests/unit/test_audit_service.py`
   **Result: 49 passed in 19.87s**
2. API test suite:
   `.\.venv\Scripts\pytest.exe tests/api/test_assessment_api.py tests/api/test_attempt_api.py tests/api/test_file_api.py tests/api/test_ai_api.py tests/api/test_admin_audit_api.py`
   **Result: 41 passed in 18.73s**

Total tests executed: 90 passed, 0 failed.

---

## 2. Logic Chain

### 2.1 Logic Chain for Defect 1 (Assessment Timing Clearing on Published Assessment)
1. *Premise 1*: `01_BUSINESS_RULE_CATALOG.md` (`ASSESS-001`) and Invariant 13 establish that assessment timing configuration freezes once published.
2. *Premise 2*: Reference DDL trigger `trg_assessments_timing_immutable` in `012_critical_invariant_triggers.sql` (lines 48-52) explicitly throws error 51007 if `(d.close_at IS NOT NULL AND i.close_at IS NULL)`.
3. *Premise 3*: In `assessment_service.py` (lines 649-655), the service check is:
   ```python
   if cur_close is not None and norm_new_close is not None and norm_new_close <= cur_close:
       raise AssessmentLockedError("close_at can only be extended forward after publish.")
   ```
4. *Deduction*: When an update request supplies `{"close_at": null}`, `norm_new_close` is `None`. The condition evaluates to `False`. The check is bypassed, and line 696 executes `assessment.close_at = None`.
5. *Conclusion*: A published assessment can have its `close_at` deadline completely cleared via API/service, violating `ASSESS-001` and Invariant 13.

---

### 2.2 Logic Chain for Defect 2 (Unverified Multi-Tab Lease Takeover)
1. *Premise 1*: `07_ATTEMPT_LEASE_ALGORITHM.md` dictates: "Acquire uses conditional update: if no active lease, same tab owner, or `lease_expires_at <= now`... Second tab while lease valid gets LEASE_CONFLICT... Takeover is allowed only after stale expiry".
2. *Premise 2*: Invariant 10 mandates: "One active editing lease; stale owner takeover keeps same Attempt." Threat model `SEC-CONC-02` specifies lease conflict when a second tab attempts to steal a live lease.
3. *Premise 3*: In `attempt_service.py` lines 813-865, `takeover_attempt_lease` immediately generates a new lease token, updates `attempt.lease_token_hash`, and increments `lease_epoch` without inspecting `attempt.lease_expires_at <= now`.
4. *Premise 4*: In `blueprints/api_attempts/routes.py`, `POST /api/attempts/<attempt_id>/lease` is routed directly to `takeover_attempt_lease_route`.
5. *Deduction*: Any background refresh, duplicate browser tab, or second device immediately invalidates the first tab's active lease without waiting for the 30-second lease window to expire or checking for conflict.
6. *Conclusion*: Single active editing lease enforcement is vulnerable to immediate lease hijacking across tabs, violating Algorithm 07, `ATTEMPT-003`, and Invariant 10.

---

### 2.3 Logic Chain for Defect 3 (Missing Mandatory Reason & Instructor Notification on Admin Content Override)
1. *Premise 1*: Rule `AUDIT-003` in `01_BUSINESS_RULE_CATALOG.md` requires: "Admin edit Instructor content needs reason + notify".
2. *Premise 2*: Specification `15_AUDIT_AND_ADMIN_ACTIONS.md` (line 7) and Invariant 23 require: "Admin content override requires reason and Instructor notification."
3. *Premise 3*: In `course_service.py` (`update_course`, lines 446-455), `reason` is taken as `data.get("reason")` without validating presence. In `lesson_service.py` (`update_lesson`), audit is only recorded if `course.status == "PUBLISHED"`, and `reason` is not required.
4. *Premise 4*: In both `course_service.py` and `lesson_service.py`, neither function invokes `notification_service` or generates a notification event to the course owner instructor when an administrator updates content.
5. *Conclusion*: Admin content overrides fail to mandate reason and fail to dispatch required instructor notifications, violating `AUDIT-003` and Invariant 23.

---

### 2.4 Logic Chain for Defect 4 (Missing Route-Level Role Decorator on Quarantine Override)
1. *Premise 1*: `09_FILE_IMPORT_API.md` and standard project conventions require role-based route gating using Flask decorators (`@admin_required`, `@instructor_required`, `@student_required`).
2. *Premise 2*: In `src/pwd301/blueprints/api_files/routes.py` line 238, `quarantine_override_api` has `@jwt_required` but lacks `@admin_required`.
3. *Premise 3*: While the underlying service function `quarantine_override` does verify `if not admin_actor.is_admin: raise FileAccessDeniedError`, route-level defense-in-depth is broken.
4. *Conclusion*: Non-admin actors reach the service layer rather than being blocked at the blueprint middleware boundary, violating defense-in-depth.

---

### 2.5 Logic Chain for Defect 5 (Soft-Deleting Questions Assigned to Active Published Assessments)
1. *Premise 1*: Rule `DELETE-002` states that used assessments/questions must be preserved as historical tombstones, and active dependencies must prevent breakage.
2. *Premise 2*: In `question_bank_service.py` (`trash_question`, lines 786-838), there is no check whether the question is currently assigned to a `PUBLISHED` assessment.
3. *Premise 3*: An instructor can move a question to `TRASH` while a published assessment is actively being delivered to students.
4. *Conclusion*: Question authoring lifecycle does not guard against trashing questions in active assessments.

---

## 3. Comprehensive Business Rule Traceability Matrix

The table below maps each rule for Subsystems C, D, and E to its implementation:

| Rule ID | Rule Summary | Source Domain | Implementation File & Line(s) | Status | Audit Findings / Defect Reference |
|---|---|---|---|---|---|
| `QBANK-001` | Question belongs to exactly 1 Course; Lesson optional in same course | `Question Bank` | `services/question_bank_service.py:185-230` | **CONFORMANT** | Validated during creation and revision. |
| `QBANK-002` | Unused edit in-place; used important edit creates new revision | `Question Bank` | `services/question_bank_service.py:902-950, 1410-1465` | **CONFORMANT** | `is_question_in_use` enforces revision immutability. |
| `QBANK-003` | Choices/accepted answers belong to revision | `Question Bank` | `models/question_bank.py:160-260`, `services/question_bank_service.py:300-450` | **CONFORMANT** | Separate tables with FK to `question_revision_id`. |
| `QBANK-004` | Question type cannot change after student answer | `Question Bank` | `services/question_bank_service.py:1074-1080, 1450-1455` | **CONFORMANT** | Enforced via `QuestionImmutableError` and SQL trigger. |
| `QBANK-005` | Exposed/graded revision kept indefinitely | `Retention` | `services/attempt_service.py:502`, `services/retention_service.py:480-530` | **CONFORMANT** | `was_student_exposed` flag protects from pruning. |
| `QBANK-006` | Multiple-choice exact set, no partial | `Grading` | `services/attempt_service.py:1965-1976` | **CONFORMANT** | Strict set equality `selected_keys == correct_keys`. |
| `QBANK-007` | Short answer multi accepted + normalized/exact | `Grading` | `services/attempt_service.py:1977-2001` | **CONFORMANT** | NFKC normalization and exact mode supported. |
| `ASSESS-001` | Timing config locks after publish | `Assessment` | `services/assessment_service.py:626-655, 692-705` | **DEFECT** | **Defect 1**: `close_at: null` clears deadline on published assessment. |
| `ASSESS-002` | Structure locks after first start | `Assessment` | `services/assessment_service.py:609-623, 1076, 1131, 1179, 1288, 1346, 1486` | **CONFORMANT** | All structural mutations check `first_attempt_started_at`. |
| `ASSESS-003` | Points lock after first start | `Assessment` | `services/assessment_service.py:1179-1182, 1288-1291` | **CONFORMANT** | Points can only be modified via assignment add/remove, which is locked. |
| `ASSESS-004` | Blueprint shortage blocks publish | `Assessment` | `services/assessment_service.py:868-880` | **CONFORMANT** | Validates `questions_count >= 1` and `total_points > 0`. |
| `ASSESS-005` | Student gets latest revision at attempt start | `Assessment` | `services/attempt_service.py:474-484` | **CONFORMANT** | Resolves `q.current_revision` at attempt start. |
| `ASSESS-006` | Random attempt exact set/order snapshot preserved | `Attempt` | `services/attempt_service.py:468-540` | **CONFORMANT** | Snapshots persisted in `attempt_questions` and `attempt_choice_snapshots`. |
| `ATTEMPT-001` | Attempt limit configurable | `Attempt` | `services/attempt_service.py:351-365` | **CONFORMANT** | Enforces `period_attempts_count < assessment.attempt_limit`. |
| `ATTEMPT-002` | Server authoritative deadline + hard close | `Attempt` | `services/attempt_service.py:171-193, 195-235` | **CONFORMANT** | `min(started_at + limit, close_at)`; hard transition to `EXPIRED`. |
| `ATTEMPT-003` | Only first tab edits; stale takeover | `Attempt` | `services/attempt_service.py:750-880`, `blueprints/api_attempts/routes.py:149-158` | **DEFECT** | **Defect 2**: `takeover_attempt_lease` steals lease without checking expiry. |
| `ATTEMPT-004` | MC save immediate; text debounce; resume current answer | `Attempt` | `services/attempt_service.py:1041-1160` | **CONFORMANT** | Debounce supported; `get_attempt_delivery` loads saved answers. |
| `ATTEMPT-005` | Offline old event cannot overwrite newer | `Attempt` | `services/attempt_service.py:1095-1124` | **CONFORMANT** | Enforces `client_sequence > last` and `lease_epoch` fencing. |
| `ATTEMPT-006` | After deadline only saved answers count | `Attempt` | `services/attempt_service.py:1073-1079` | **CONFORMANT** | Answers rejected after deadline; auto-expires attempt. |
| `ATTEMPT-007` | Submit idempotent | `Attempt` | `services/attempt_service.py:1543-1579, 1630-1665` | **CONFORMANT** | Matches `submission_idempotency_key`; returns replay result. |
| `GRADE-001` | Essay manual, final pending until complete | `Grading` | `services/attempt_service.py:2002-2007, 2070-2078` | **CONFORMANT** | Sets `PENDING_GRADING`, 0 awarded points, result `PENDING`. |
| `GRADE-002` | Manual essay revision keeps old/new/reason/actor | `Grading` | `services/attempt_service.py:2153-2194` | **CONFORMANT** | Appends to `AttemptQuestionGradeHistory`. |
| `REGRADE-001` | Answer-only correction auto regrades eligible attempts | `Regrade` | `services/regrade_worker.py:372-460` | **CONFORMANT** | Algorithm 11 `ANSWER_ONLY` re-evaluates objective choices. |
| `REGRADE-002` | Content/choices correction gives full credit to earlier attempts | `Regrade` | `services/regrade_worker.py:365-371` | **CONFORMANT** | Sets `CONTENT_FULL_CREDIT` with full points. |
| `REGRADE-003` | Historical snapshot/answer never rewritten | `Regrade` | `services/regrade_worker.py:357-370` | **CONFORMANT** | `AttemptQuestion` & `AttemptAnswer` unchanged; only grades/history update. |
| `REGRADE-004` | Regrade resumable/idempotent | `Regrade` | `services/regrade_worker.py:200-297, 490-550` | **CONFORMANT** | Per-item status, deduplication, retry handling. |
| `FILE-001` | Upload quarantine, fail-closed malware scan | `File` | `services/file_service.py:323-550`, `blueprints/api_files/routes.py:238` | **DEFECT (LOW)** | **Defect 4**: Service logic is fail-closed, but route lacks `@admin_required`. |
| `FILE-002` | Macro Office forbidden + parser resource limits | `File` | `services/file_service.py:60-94, 105-126`, `services/import_service.py:118-160` | **CONFORMANT** | Macro extensions rejected; streaming byte limits enforced. |
| `FILE-003` | Physical dedup SHA-256 | `File` | `services/file_service.py:387-425` | **CONFORMANT** | Computes SHA-256, reuses `FileBlob`, increments ref count. |
| `FILE-004` | Replacement only after safe; old recoverable ~30d | `File` | `services/file_service.py:650-750` | **CONFORMANT** | Scans replacement first; marks old `REPLACED` with 30-day retention. |
| `FILE-005` | Authorized app route only (no path exposure) | `File` | `services/file_service.py:902-1025`, `services/file_service.py:1521-1570` | **CONFORMANT** | Zero path exposure in JSON; token/session authorization checked. |
| `IMPORT-001` | Import always creates draft/review workflow | `Import` | `services/import_service.py:215-290` | **CONFORMANT** | `DocumentImportJob` and `ImportQuestion` remain in review state. |
| `IMPORT-002` | No answer key means no official answer; confirm needed | `Import` | `services/import_service.py:900-980` | **CONFORMANT** | Ambiguous answers flagged for manual confirmation. |
| `IMPORT-003` | Duplicate only flag, never auto merge | `Import` | `services/import_service.py:680-750` | **CONFORMANT** | Creates `ImportDuplicateCandidate` rows without auto-merging. |
| `AI-001` | Student RAG only published authorized content | `AI` | `services/rag_service.py:736-768` | **CONFORMANT** | Pre-retrieval check ensures student active enrollment. |
| `AI-002` | Archived/deleted source stops retrieval immediately | `AI` | `services/rag_service.py:770-776, 818-835` | **CONFORMANT** | Returns `[]` if course is `ARCHIVED`, `TRASH`, or `DRAFT`. |
| `AI-003` | Raw chat purge after 5 min inactivity | `AI` | `services/ai_service.py:338-346`, `services/retention_service.py:595-639` | **CONFORMANT** | Expired after 300s; raw `AIMessage` rows deleted in DB. |
| `AI-004` | Minimum user data; Student only own progress | `AI` | `services/ai_service.py:334-337` | **CONFORMANT** | Own conversation check; telemetry records minimal metadata. |
| `AI-005` | Backend computes recommendation; Gemini explains | `AI` | `services/recommendation_service.py:80-280` | **CONFORMANT** | Algorithm 14 computes scores; LLM invoked only for text. |
| `AI-006` | Answer records source version/revision | `AI` | `services/rag_service.py:890-950` | **CONFORMANT** | `AISourceUsage` records chunk/doc/version attribution. |
| `AUDIT-001` | Important audit append-only | `Audit` | `models/notification_audit.py:316-360`, `services/audit_service.py:116-160` | **CONFORMANT** | No update/delete logic; SQL trigger blocks updates/deletions. |
| `AUDIT-002` | Required audit failure blocks sensitive mutation | `Audit` | `services/audit_service.py:648-707` | **CONFORMANT** | Rolls back transaction and raises `AuditPersistenceError`. |
| `AUDIT-003` | Admin edit Instructor content needs reason + notify | `Audit` | `services/course_service.py:446-455`, `services/lesson_service.py:412-425` | **DEFECT** | **Defect 3**: `reason` optional; no notification sent to instructor. |
| `DELETE-002` | Used Assessment/Question historical tombstone | `Retention` | `services/question_bank_service.py:786-838` | **DEFECT (LOW)** | **Defect 5**: Does not block trashing questions assigned to active assessments. |
| `OPS-004` | DB restore explicit Admin confirmation without auto overwrite | `Operations` | `services/operations_service.py:965-1135` | **CONFORMANT** | Phrase, password re-auth, checksum verification, mutex lock enforced. |

---

## 4. Detailed Defect Catalog

### Defect 1: Assessment Timing (`close_at`) Can Be Cleared on Published Assessment
- **Rule ID**: `ASSESS-001`, Invariant 13
- **Specification Reference**: `01_BUSINESS_RULE_CATALOG.md` (Row 37), `012_critical_invariant_triggers.sql` (lines 48-52), `17_MAJOR_FEATURE_SPECIFICATIONS.md` (line 195, line 240)
- **Affected File**: `src/pwd301/services/assessment_service.py`, lines 649-655, lines 695-696
- **Severity**: **HIGH**
- **Detailed Defect Description**:
  In `update_assessment`:
  ```python
  if "close_at" in payload:
      new_close = _parse_iso_datetime(payload.get("close_at"), "close_at")
      cur_close = _normalize_dt(assessment.close_at)
      norm_new_close = _normalize_dt(new_close)
      if cur_close is not None and norm_new_close is not None and norm_new_close <= cur_close:
          raise AssessmentLockedError("close_at can only be extended forward after publish.")
  ...
  if "close_at" in payload:
      assessment.close_at = _parse_iso_datetime(payload.get("close_at"), "close_at")
  ```
  When `payload = {"close_at": None}` (or `null` in JSON), `norm_new_close` is `None`. The check `cur_close is not None and norm_new_close is not None and norm_new_close <= cur_close` evaluates to `False`. The lock validation is bypassed, and `assessment.close_at` is set to `None`. In dev/SQLite environments (where SQL Server DDL triggers do not execute), this allows instructors or administrators to completely remove deadlines from published assessments. In addition, if `cur_close` was originally `None`, any past timestamp can be set without being checked against `utc_now()`.
- **Concrete Recommended Fix**:
  ```python
  # In src/pwd301/services/assessment_service.py:
  if "close_at" in payload:
      new_close = _parse_iso_datetime(payload.get("close_at"), "close_at")
      cur_close = _normalize_dt(assessment.close_at)
      norm_new_close = _normalize_dt(new_close)

      if is_published:
          if cur_close is not None and norm_new_close is None:
              raise AssessmentLockedError(
                  "Assessment close_at cannot be removed after publish."
              )
          if cur_close is not None and norm_new_close is not None and norm_new_close <= cur_close:
              raise AssessmentLockedError(
                  "close_at can only be extended forward into the future after publish."
              )
          if cur_close is None and norm_new_close is not None:
              now = utc_now()
              if norm_new_close <= now:
                  raise AssessmentValidationError(
                      "close_at must be strictly in the future."
                  )
  ```

---

### Defect 2: Unverified Lease Takeover Allows Multi-Tab Hijacking
- **Rule ID**: `ATTEMPT-003`, Invariant 10
- **Specification Reference**: `01_BUSINESS_RULE_CATALOG.md` (Row 45), `07_ATTEMPT_LEASE_ALGORITHM.md` (line 3), `01_THREAT_MODEL.md` (`SEC-CONC-02`), `17_MAJOR_FEATURE_SPECIFICATIONS.md` (line 359)
- **Affected Files**:
  - `src/pwd301/services/attempt_service.py`, lines 813-865
  - `src/pwd301/blueprints/api_attempts/routes.py`, lines 149-158
- **Severity**: **HIGH**
- **Detailed Defect Description**:
  Algorithm 07 and threat model `SEC-CONC-02` specify that an attempt editing lease can only be taken over after the active lease expires (`lease_expires_at <= now`), and a second tab attempting to acquire a lease while the lease is still valid must receive `AttemptLeaseConflictError` (409).
  However, `takeover_attempt_lease` in `attempt_service.py` performs no check on `attempt.lease_expires_at`. It immediately generates a new token and overwrites the lease hash. Furthermore, `blueprints/api_attempts/routes.py` maps both `/api/attempts/<attempt_id>/lease` (general acquire) and `/api/attempts/<attempt_id>/lease/takeover` to `takeover_attempt_lease_route`. As a result, opening a second tab or reloading in another window silently kicks out the active student session without waiting for the 30-second heartbeat lease to expire.
- **Concrete Recommended Fix**:
  1. In `src/pwd301/services/attempt_service.py` (`takeover_attempt_lease`):
     ```python
     norm_now = _normalize_dt(now)
     lease_exp = _normalize_dt(attempt.lease_expires_at)
     force = bool(payload.get("force", False)) if isinstance(payload, dict) else False
     if lease_exp is not None and norm_now is not None and norm_now < lease_exp and not force:
         raise AttemptLeaseConflictError(
             "Another active browser window holds a valid editing lease. "
             "Takeover is permitted only after the current lease expires (stale takeover) "
             "or via explicit user confirmation."
         )
     ```
  2. In `src/pwd301/blueprints/api_attempts/routes.py`:
     Separate `POST /api/attempts/<attempt_id>/lease` (which verifies whether the lease is expired before granting) from `POST /api/attempts/<attempt_id>/lease/takeover` (which requires an explicit confirmation parameter `force=true` or waits for expiry).

---

### Defect 3: Admin Content Overrides Lack Mandatory Reason and Instructor Notification
- **Rule ID**: `AUDIT-003`, Invariant 23
- **Specification Reference**: `01_BUSINESS_RULE_CATALOG.md` (Row 75), `15_AUDIT_AND_ADMIN_ACTIONS.md` (line 7), `06_NON_NEGOTIABLE_INVARIANTS.md` (#23)
- **Affected Files**:
  - `src/pwd301/services/course_service.py`, lines 446-455 (`update_course`) & lines 694-702 (`reassign_course_owner`)
  - `src/pwd301/services/lesson_service.py`, lines 412-425 (`update_lesson`)
- **Severity**: **MEDIUM**
- **Detailed Defect Description**:
  Rule `AUDIT-003` specifies: "Admin edit Instructor content needs reason + notify".
  `15_AUDIT_AND_ADMIN_ACTIONS.md` explicitly mandates: "Admin content override requires reason and Instructor notification."
  In `course_service.py` and `lesson_service.py`:
  1. `reason` is completely optional: `data.get("reason")` can be empty or `None`, and the mutation succeeds.
  2. No notification event is dispatched to the instructor who owns the course/lesson.
- **Concrete Recommended Fix**:
  In `course_service.py` (`update_course`) and `lesson_service.py` (`update_lesson`), check if `actor.is_admin and course.owner_instructor_id is not None and actor.id != course.owner_instructor_id`:
  ```python
  if actor.is_admin and course.owner_instructor_id and actor.id != course.owner_instructor_id:
      reason_val = data.get("reason")
      if not reason_val or not str(reason_val).strip():
          raise ValidationError("A reason is mandatory when an administrator modifies instructor content.")

      # Dispatch notification event to the course owner
      from pwd301.services.notification_service import create_notification_event
      create_notification_event(
          event_type="ADMIN_CONTENT_OVERRIDE",
          actor=actor,
          target_type="COURSE",
          target_id=course.id,
          recipient_user_ids=[course.owner_instructor_id],
          payload={
              "course_id": str(course.public_id),
              "reason": str(reason_val).strip(),
              "modified_by": actor.email,
          },
          session=sess,
      )
  ```

---

### Defect 4: Missing Route Decorator `@admin_required` on Quarantine Override Endpoint
- **Rule ID**: `FILE-001`
- **Specification Reference**: `01_BUSINESS_RULE_CATALOG.md` (Row 56), `09_FILE_IMPORT_API.md`
- **Affected File**: `src/pwd301/blueprints/api_files/routes.py`, lines 238-249
- **Severity**: **LOW**
- **Detailed Defect Description**:
  The route `/api/files/<asset_id>/quarantine-override` has `@jwt_required` but lacks the `@admin_required` decorator. Although the service function `quarantine_override` does reject non-admins with `FileAccessDeniedError`, route-level role gating should be enforced consistently at the Flask blueprint boundary.
- **Concrete Recommended Fix**:
  ```python
  # In src/pwd301/blueprints/api_files/routes.py:
  @api_file_bp.route("/<asset_id>/quarantine-override", methods=["POST"])
  @jwt_required
  @admin_required
  def quarantine_override_api(asset_id: str) -> tuple[Response, int] | Response:
  ```

---

### Defect 5: Trashing Questions Assigned to Active Assessments Is Not Guarded
- **Rule ID**: `DELETE-002`
- **Specification Reference**: `01_BUSINESS_RULE_CATALOG.md` (Row 77)
- **Affected File**: `src/pwd301/services/question_bank_service.py`, lines 786-838 (`trash_question`)
- **Severity**: **LOW**
- **Detailed Defect Description**:
  `trash_question` does not verify if a question is currently assigned to a `PUBLISHED` assessment that is actively ongoing. It soft-deletes the question into `TRASH` without checking assignment constraints. While students already starting attempts will still have frozen snapshot records, the live question bank and authoring views show the question as trashed while the assessment is still live.
- **Concrete Recommended Fix**:
  In `trash_question`, verify whether the question is currently referenced in `AssessmentQuestionAssignment` where the parent assessment has `status == 'PUBLISHED' and deleted_at is None`. If so, raise `QuestionStateViolationError` instructing the instructor to unassign or archive the assessment first.

---

## 5. Caveats

1. **Database Engine Variations**:
   The reference SQL DDL in `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/012_critical_invariant_triggers.sql` targets Microsoft SQL Server triggers (`AFTER UPDATE`, `THROW`). In local development and unit testing with SQLite, database-level triggers do not execute; therefore, application service validations are the primary line of defense. Where the Python service checks diverge from SQL Server triggers (such as Defect 1), the defect is exposed in non-MSSQL environments.
2. **Background Regrading Concurrency**:
   Regrading is tested synchronously in unit tests; worker concurrency tests in production will rely on SQL row-locking or queue coordination to ensure per-item claims remain isolated across distributed workers.
3. **No other caveats**: All rules in BR-ASM-*, BR-FIL-*, BR-AI-*, BR-AUD-*, and OPS-004 have been investigated with complete evidence chains.

---

## 6. Conclusion

Subsystems C, D, and E in `src/pwd301/` demonstrate high architectural maturity, comprehensive data masking (ADR-002), robust cryptographic deduplication (Algorithm 12), grounded RAG pre-retrieval security, fail-closed malware handling, and strict database restore confirmation safeguards.

However, **5 specific defects** were discovered that compromise system invariants:
1. **Defect 1 (High)**: `close_at: null` clears the close deadline on a published assessment in `assessment_service.py`.
2. **Defect 2 (High)**: `takeover_attempt_lease` in `attempt_service.py` allows immediate lease hijacking without waiting for lease expiration or verifying conflict.
3. **Defect 3 (Medium)**: Admin content overrides in `course_service.py` and `lesson_service.py` do not enforce mandatory reason nor dispatch instructor notifications.
4. **Defect 4 (Low)**: Missing `@admin_required` route decorator on `/api/files/<asset_id>/quarantine-override`.
5. **Defect 5 (Low)**: Trashing questions currently assigned to published assessments is not prevented.

Remediating these 5 defects will bring Subsystems C, D, and E into complete compliance with the PWD301 System Specification and Non-Negotiable Invariants.

---

## 7. Verification Method

To independently verify the observations, test suite results, and defects:

1. **Execute Unit Test Suites**:
   ```powershell
   .\.venv\Scripts\pytest.exe tests/unit/test_assessment_service.py tests/unit/test_attempt_lease_service.py tests/unit/test_file_service.py tests/unit/test_rag_service.py tests/unit/test_audit_service.py
   ```
   *Expected*: All 49 tests pass.

2. **Execute API Test Suites**:
   ```powershell
   .\.venv\Scripts\pytest.exe tests/api/test_assessment_api.py tests/api/test_attempt_api.py tests/api/test_file_api.py tests/api/test_ai_api.py tests/api/test_admin_audit_api.py
   ```
   *Expected*: All 41 tests pass.

3. **Verify Defect 1 (Assessment close_at bypass)**:
   Inspect `src/pwd301/services/assessment_service.py` lines 649-655. Observe that passing `{"close_at": None}` bypasses `AssessmentLockedError` and assigns `assessment.close_at = None` at line 696.

4. **Verify Defect 2 (Lease Takeover bypass)**:
   Inspect `src/pwd301/services/attempt_service.py` lines 813-865. Observe that `takeover_attempt_lease` does not assert `norm_now >= attempt.lease_expires_at`, and `tests/unit/test_attempt_lease_service.py` lines 342-350 demonstrates takeover succeeding within 1 millisecond of attempt creation without waiting for the 30-second lease to expire.

5. **Verify Defect 3 (Admin Override Notification & Reason)**:
   Inspect `src/pwd301/services/course_service.py` lines 446-455 and `src/pwd301/services/lesson_service.py` lines 412-425. Observe that no call to `notification_service` exists and `reason` is not validated for non-empty content when `actor.is_admin` overrides instructor content.
