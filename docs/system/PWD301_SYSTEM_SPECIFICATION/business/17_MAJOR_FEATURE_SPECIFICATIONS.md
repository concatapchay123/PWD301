# Major Feature Specifications

These specs use the common WHAT/WHO/PRECONDITION/AUTH/ALGORITHM/TRANSACTION/DB/API/CONCURRENCY/FAILURE/SECURITY/AC/TEST contract.

## Feature: Enroll in Course

### Purpose
Define the complete implementation contract for Enroll in Course.

### Actors
- Student

### Preconditions
- Course exists and is published/enrollable
- Student account active

### Authorization
- Actor is the Student being enrolled; no enrolling another user through Student endpoint

### Inputs
- course public ID

### Validation
- No active period already
- Course capacity available if set
- All prerequisites satisfied

### Business Rules
- ENROLL-001..004
- COURSE-005..007

### Algorithm
Resolve Course and logical Enrollment. In a transaction serialize capacity decision, re-check prerequisite completion summaries, create/reuse Enrollment, create one new active EnrollmentPeriod, reset active progress cache and append EnrollmentEvent.

### Transaction
Single SQL transaction through EnrollmentService; no email/external call inside.

### Database Reads
- courses
- course_prerequisites
- course_completion_summaries
- enrollments
- enrollment_periods

### Database Writes
- enrollments/enrollment_periods
- enrollment_events

### State Transition
No enrollment → ACTIVE period, or LEFT/DETAIL_PURGED → new ACTIVE period.

### API Contract
POST /api/courses/{course_id}/enroll

### Side Effects
- optional in-app event
- analytics invalidation

### Concurrency
Capacity race must be serialized/locked; unique active-period invariant is final guard.

### Idempotency
Already-active enrollment returns existing success or stable conflict without duplicate period.

### Failure Cases
- prerequisite not met
- course full
- course archived/not enrollable
- concurrent conflict

### Security
- Never trust client progress/prerequisite claims
- Object/course visibility before mutation

### Edge Cases
- One remaining seat with two simultaneous requests
- Prior completion after prior re-enrollment

### Acceptance Criteria
- Exactly one active period
- Progress restarts while durable completion summary remains

### Required Tests
- T-ENROLL-*
- AC-ENROLL-001/002
- E2E-05..07

## Feature: Leave and Re-enroll

### Purpose
Define the complete implementation contract for Leave and Re-enroll.

### Actors
- Student

### Preconditions
- Active EnrollmentPeriod for leave; published/eligible Course for rejoin

### Authorization
- Only own enrollment may be changed

### Inputs
- course/enrollment public ID
- leave confirmation

### Validation
- No already-closed active period
- Rejoin still satisfies capacity/prerequisites

### Business Rules
- ENROLL-002..004

### Algorithm
Leave closes period with `left_at` and retention deadline. Rejoin within or after retention never resumes active progress: create a new period/reset cache. Cleanup after >30 days without rejoin may purge detailed period data but keeps completion summary.

### Transaction
Leave/rejoin each one transaction; cleanup separate idempotent worker.

### Database Reads
- enrollments
- enrollment_periods
- course_completion_summaries

### Database Writes
- enrollment_periods
- enrollment_events
- enrollments cache

### State Transition
ACTIVE → LEFT → ACTIVE new period; LEFT → DETAIL_PURGED via cleanup.

### API Contract
POST leave / POST enroll

### Side Effects
- retention scheduling/eligibility
- event history

### Concurrency
Unique active-period index prevents double rejoin.

### Idempotency
Repeated leave/rejoin command is state-idempotent where semantics match.

### Failure Cases
- no active period
- capacity/prereq fails on rejoin

### Security
- Do not expose deleted detail after purge

### Edge Cases
- Rejoin at day 29 vs cleanup race
- Cleanup queued while rejoin commits

### Acceptance Criteria
- Rejoin wins by transaction eligibility; no active detail is purged accidentally

### Required Tests
- T-RET-*
- AC-RET-001
- E2E-24..27

## Feature: Publish Assessment

### Purpose
Define the complete implementation contract for Publish Assessment.

### Actors
- Instructor
- Admin override

### Preconditions
- Assessment draft or publishable state
- All source Questions belong Course and are valid

### Authorization
- Current Course manager; Admin override requires governed path

### Inputs
- assessment ID
- row_version

### Validation
- Blueprint candidate counts
- No missing official answer where required
- Positive points
- valid timing open<close and limit
- AI/import drafts approved

### Business Rules
- ASSESS-001..004

### Algorithm
Run prepublish validation, materialize/validate selection pool as designed, reject shortages with per-rule counts, then set published timestamps/status. Timing values become immutable at commit.

### Transaction
One transaction for final validation + publish + audit/outbox.

### Database Reads
- assessments
- assignments
- blueprints/rules/pool
- questions/revisions

### Database Writes
- assessments
- audit/notification scheduling

### State Transition
DRAFT → PUBLISHED.

### API Contract
POST /api/assessments/{id}/publish

### Side Effects
- audit
- reminder scheduling

### Concurrency
ROWVERSION prevents stale publish; revalidate blueprint inside transaction.

### Idempotency
Repeated publish of already-published same configuration returns state success or stable conflict without duplicate side effects.

### Failure Cases
- blueprint shortage
- invalid timing
- unapproved/import draft
- stale editor

### Security
- Never expose answer keys to Student because of publish serialization

### Edge Cases
- Publish racing with Question update
- close time already passed

### Acceptance Criteria
- Timing frozen immediately after successful publish
- Shortage blocks publish with explicit counts

### Required Tests
- T-ASSESS-*
- AC-ASSESS-001
- E2E-12

## Feature: Start Assessment Attempt

### Purpose
Define the complete implementation contract for Start Assessment Attempt.

### Actors
- Student

### Preconditions
- Assessment published and currently open
- Student enrolled/eligible
- Attempt limit not exhausted

### Authorization
- Actor starts only own Attempt

### Inputs
- assessment ID
- optional idempotency/start request key

### Validation
- server now within open/close
- attempt policy
- no invalid cancelled state

### Business Rules
- ASSESS-005/006
- ATTEMPT-001/002

### Algorithm
Inside a short transaction count/allocate attempt number, stamp first-start if necessary, compute `deadline_at=min(started_at+limit, close_at)`, resolve latest valid QuestionRevisions, select mandatory/random/blueprint questions, shuffle if configured, and persist immutable question/choice/points order snapshot.

### Transaction
Single controlled transaction; no pre-generation of thousands of attempts.

### Database Reads
- assessment config
- assignments/pool/blueprint
- questions/revisions
- enrollment/attempt count

### Database Writes
- assessment_attempts
- attempt_questions
- attempt_choice_snapshots

### State Transition
None → CREATED/IN_PROGRESS; first start locks assessment structure/points.

### API Contract
POST /api/assessments/{id}/attempts

### Side Effects
- usage counters may update
- first-start lock marker

### Concurrency
Concurrent starts use attempt-number/limit uniqueness and row locks/conditional update.

### Idempotency
Same start request key should not consume two attempts.

### Failure Cases
- not open/closed
- attempt limit
- not enrolled
- blueprint inconsistency

### Security
- Server chooses revisions/order; client cannot request easier questions

### Edge Cases
- Start exactly at close
- Question corrected concurrently with start

### Acceptance Criteria
- Snapshot is complete and stable
- Deadline never exceeds close

### Required Tests
- T-ATT-01/02
- AC-ATTEMPT-001
- E2E-13

## Feature: Acquire/Takeover Attempt Lease

### Purpose
Define the complete implementation contract for Acquire/Takeover Attempt Lease.

### Actors
- Student

### Preconditions
- Attempt IN_PROGRESS and before deadline

### Authorization
- Attempt owner only

### Inputs
- tab_session_id
- existing lease token for heartbeat

### Validation
- Attempt not terminal
- server time
- lease ownership/expiry

### Business Rules
- ATTEMPT-003

### Algorithm
Conditional UPDATE grants lease if no owner, same owner, or existing lease expired. Token is random and rotates on takeover. Heartbeat renews only matching current token. A valid other-tab lease returns conflict.

### Transaction
Each request is a short transaction/conditional UPDATE; never hold a transaction between heartbeats.

### Database Reads
- assessment_attempts

### Database Writes
- lease owner/token/heartbeat/expiry/rowversion

### State Transition
IN_PROGRESS remains; only edit-right metadata changes.

### API Contract
POST lease / heartbeat

### Side Effects
- optional security event for abuse threshold

### Concurrency
The conditional predicate is the race arbiter; simultaneous acquisitions yield at most one winner.

### Idempotency
Heartbeat retry with same valid token is safe.

### Failure Cases
- valid lease held elsewhere
- deadline reached
- terminal state

### Security
- Lease token is secret capability scoped to one Attempt and owner; do not log raw token

### Edge Cases
- Network partition
- browser refresh
- two takeovers after expiry

### Acceptance Criteria
- Second tab cannot edit while valid owner exists
- Expired owner cannot create permanent lock

### Required Tests
- T-ATT-03..05
- AC-ATTEMPT-002/003
- E2E-14/15

## Feature: Autosave Answer and Offline Reconcile

### Purpose
Define the complete implementation contract for Autosave Answer and Offline Reconcile.

### Actors
- Student

### Preconditions
- IN_PROGRESS Attempt
- valid active lease
- server deadline not passed

### Authorization
- Attempt owner and lease token

### Inputs
- attempt question ID
- client_change_id
- client_sequence
- answer payload

### Validation
- Question belongs snapshot
- payload matches question type
- sequence/dedupe/deadline

### Business Rules
- ATTEMPT-004..006

### Algorithm
Insert/dedupe AnswerEvent by client_change_id. If sequence is newer than current accepted sequence, update current AttemptAnswer and selected choices/text. If duplicate, return prior acceptance. If stale, preserve event if desired but never overwrite. Reject anything arriving after deadline.

### Transaction
One transaction per save.

### Database Reads
- assessment_attempts
- attempt_questions
- attempt_answers

### Database Writes
- attempt_answer_events
- attempt_answers
- attempt_answer_choices

### State Transition
Attempt remains IN_PROGRESS.

### API Contract
PUT /api/attempts/{id}/answers/{attempt_question_id}

### Side Effects
- UI saved-state response

### Concurrency
Lease + deadline + monotonic conditional update protect concurrent/offline writes.

### Idempotency
client_change_id is the retry key.

### Failure Cases
- LEASE_CONFLICT
- DEADLINE_EXPIRED
- STALE_ANSWER
- invalid choice

### Security
- Never accept choice IDs outside frozen snapshot

### Edge Cases
- Old offline event arrives after newer event
- same request retry after lost response

### Acceptance Criteria
- Newer answer survives stale arrival
- Accepted save has deterministic server timestamp/version

### Required Tests
- T-ATT-06..08
- AC-AUTOSAVE-001
- AC-TIMER-001
- E2E-16..18

## Feature: Submit Attempt

### Purpose
Define the complete implementation contract for Submit Attempt.

### Actors
- Student

### Preconditions
- Attempt exists for actor; in-progress or expiration finalization path

### Authorization
- Attempt owner

### Inputs
- idempotency_key
- optional current lease token

### Validation
- No inconsistent terminal state
- server deadline handling

### Business Rules
- ATTEMPT-007
- GRADE-001

### Algorithm
Serialize terminal transition. If result exists, return it. Otherwise freeze accepted answer state, grade MCQ/short answer, create per-question/current grades and one AssessmentResult. If manual essays remain, result is PENDING_GRADING; otherwise final/graded. Clear/ignore edit lease.

### Transaction
One transaction for terminal state + grading current rows + result.

### Database Reads
- attempt/answers/snapshots
- current correct answer revisions/policy

### Database Writes
- attempt status/timestamps
- grades
- assessment_results
- histories when applicable

### State Transition
IN_PROGRESS → SUBMITTED/PENDING_GRADING/GRADED or EXPIRED finalization.

### API Contract
POST /api/attempts/{id}/submit

### Side Effects
- notification according to release policy
- analytics invalidation

### Concurrency
Concurrent submits converge through unique result/idempotency/terminal condition.

### Idempotency
Required; retry returns same logical result.

### Failure Cases
- terminal conflict
- invalid idempotency payload
- DB failure rolls back

### Security
- Do not reveal hidden correct answers before visibility policy

### Edge Cases
- Submit at exact deadline
- two simultaneous requests
- response lost after commit

### Acceptance Criteria
- Exactly one logical result
- Retry returns same result

### Required Tests
- T-ATT-09
- AC-SUBMIT-001
- E2E-19

## Feature: Correct Used Question and Regrade

### Purpose
Define the complete implementation contract for Correct Used Question and Regrade.

### Actors
- Instructor
- Admin override

### Preconditions
- Question has historical use
- New correction approved with reason

### Authorization
- Current Course manager; Admin override governed/audited

### Inputs
- new revision content/answer
- correction type
- reason
- row_version

### Validation
- Question type lock
- revision validity
- classify answer-only vs content/choices

### Business Rules
- QBANK-002..005
- REGRADE-001..004

### Algorithm
Atomically create/activate new revision, create QuestionCorrection and RegradeJob. Worker enumerates eligible retained AttemptQuestions. Answer-only recomputes exact grade; content/choices applies full-credit rule to affected earlier attempts. Per item updates current grades/results and appends history; snapshots/answers never change.

### Transaction
Correction creation transaction + independent per-RegradeItem transactions.

### Database Reads
- questions/revisions
- attempt_questions
- enrollment_period eligibility

### Database Writes
- question_corrections
- regrade_jobs/items
- grade/result histories

### State Transition
Question current revision advances; attempts remain historical; grades may change.

### API Contract
POST /api/questions/{id}/corrections

### Side Effects
- required audit
- score-change notifications
- job progress

### Concurrency
ROWVERSION prevents competing edits; unique regrade item ensures retry safety.

### Idempotency
Correction/job ID and job+attempt unique item.

### Failure Cases
- stale question edit
- purged detail excluded
- worker partial failure

### Security
- History/audit contains no secret; authorization based on current Course manager

### Edge Cases
- Two corrections while first regrade running
- Student leaves/purge race

### Acceptance Criteria
- Historical snapshot unchanged
- Old/new score and reason preserved
- Job resumable

### Required Tests
- T-REG-*
- AC-REGRADE-001/002
- E2E-21..23

## Feature: Upload and Activate File

### Purpose
Define the complete implementation contract for Upload and Activate File.

### Actors
- Instructor
- Admin override

### Preconditions
- Authorized Course/resource context

### Authorization
- Current Course manager/Admin policy

### Inputs
- multipart file
- logical resource context

### Validation
- type/size/quota
- macro format block
- storage free space

### Business Rules
- FILE-001..005

### Algorithm
Stream into quarantine, calculate hash, create/reuse physical blob, create logical FileRevision in quarantine. Worker scans and resource-checks. Only PASS/safe processing may atomically activate revision; replacement demotes old active to recovery. Scanner unavailable never activates.

### Transaction
Upload metadata transaction, worker processing transactions, activation transaction.

### Database Reads
- course/quota
- existing blob/assets

### Database Writes
- file_blobs/assets/revisions/scan_results
- background job

### State Transition
QUARANTINED→SCANNING→PROCESSING→SAFE→ACTIVE or BLOCKED/REJECTED.

### API Contract
POST /api/files

### Side Effects
- security event on suspicious/reject
- processing job

### Concurrency
Unique one-active-revision invariant + transactional swap handles replacements/races.

### Idempotency
Hash/job dedupe; repeated activation converges.

### Failure Cases
- quota/size/type reject
- scanner unavailable
- malware
- parser timeout

### Security
- Private storage; generated keys; authorization route only

### Edge Cases
- Same bytes concurrent upload
- replacement fails scan
- shared blob old reference

### Acceptance Criteria
- Unsafe revision never downloadable
- Old active stays available if replacement fails

### Required Tests
- T-FILE-*
- AC-FILE-001/002
- E2E-30/31

## Feature: Import DOCX/PDF to Draft Assessment

### Purpose
Define the complete implementation contract for Import DOCX/PDF to Draft Assessment.

### Actors
- Instructor
- Admin override

### Preconditions
- Input FileRevision SAFE/authorized

### Authorization
- Current Course manager

### Inputs
- file asset/revision
- target Course
- import options

### Validation
- DOCX/PDF type
- resource limits
- same Course/source authorization

### Business Rules
- IMPORT-001..003

### Algorithm
Queue parser, extract text/questions/images under limits, create ImportQuestion items with confidence/answer-key state, flag ambiguity/broken images/duplicates. Instructor reviews keep/edit/reject; optional AI answer suggestion remains unapproved until explicit confirmation. Promote approved items to independent Questions/draft Assessment; never auto-publish.

### Transaction
Job creates review records; each review action transactional; promotion transaction maintains provenance.

### Database Reads
- file revision/course/question bank

### Database Writes
- document_import_jobs
- import_questions
- duplicates/resources
- question provenance

### State Transition
QUEUED→PROCESSING→REVIEW_REQUIRED→COMPLETED/FAILED.

### API Contract
POST /api/imports + review endpoints

### Side Effects
- worker
- AI request if requested

### Concurrency
Job claim/idempotency and optimistic review state prevent duplicate promotion.

### Idempotency
One import job key; promotion item has one accepted outcome.

### Failure Cases
- parser failure
- broken image
- ambiguous item
- AI unavailable

### Security
- Source document is untrusted data; extracted files re-use security pipeline

### Edge Cases
- No answer key
- near duplicate existing Question
- partial parse success

### Acceptance Criteria
- No unreviewed question enters Bank
- No AI suggestion becomes official without explicit confirm

### Required Tests
- T-IMP-*
- AC-IMPORT-001
- E2E-10

## Feature: AI/RAG Chat

### Purpose
Define the complete implementation contract for AI/RAG Chat.

### Actors
- Student
- Instructor
- Admin

### Preconditions
- Active actor; request within LMS scope

### Authorization
- Every retrieval/tool context uses current actor permissions

### Inputs
- message
- conversation ID
- course/lesson context optional

### Validation
- rate limit
- scope classification
- authorized source filter

### Business Rules
- AI-001..006

### Algorithm
Handle backend-answerable request locally when possible. For Gemini flow, build minimum context, prefilter eligible KnowledgeChunks by published/current authorization, wrap documents as untrusted evidence, call Gemini with timeout, validate/format answer, persist source usage and transient conversation, reset five-minute inactivity expiry.

### Transaction
Avoid holding DB transaction across Gemini call; persist request metadata/source usage in bounded transactions.

### Database Reads
- actor/course/progress permissions
- knowledge active versions/chunks

### Database Writes
- ai_requests/source_usages
- short-lived conversation/messages

### State Transition
Conversation expiry moves forward on User message; Knowledge lifecycle independent.

### API Contract
POST /api/ai/chat

### Side Effects
- usage/rate accounting
- security event on abuse threshold

### Concurrency
No shared personalized cache; source version active pointer updated transactionally.

### Idempotency
AI request ID can dedupe accidental retry if configured; backend reads are safe.

### Failure Cases
- out of scope
- insufficient evidence
- Gemini timeout
- no authorized sources

### Security
- Prompt injection defense; minimum data; no direct arbitrary SQL

### Edge Cases
- Course archived during request
- version invalidated during indexing

### Acceptance Criteria
- No unauthorized chunk appears
- Source versions recorded
- Raw chat purges after 5 min inactivity

### Required Tests
- T-AI-*
- AC-AI-001/002
- E2E-32/33

## Feature: Suspend Account

### Purpose
Define the complete implementation contract for Suspend Account.

### Actors
- Admin

### Preconditions
- Target User exists; actor is active Admin

### Authorization
- Fresh password re-auth; exact confirmation/reason according to sensitivity

### Inputs
- target User ID
- reason
- confirmation phrase

### Validation
- Cannot bypass own safety policies
- reason non-empty

### Business Rules
- AUTH-003/005
- AUDIT-002

### Algorithm
Within one transaction set suspended status/auth version, revoke all persisted sessions/JWT grants, insert required AuditEvent and notification event. Commit then email worker delivers mandatory notification. Middleware rejects stale credentials immediately.

### Transaction
Required audit is in same transaction; notification/outbox local record can be included.

### Database Reads
- users
- auth_sessions
- jwt grants

### Database Writes
- user status/version
- session/token revoked_at
- audit_events
- notifications

### State Transition
ACTIVE→SUSPENDED.

### API Contract
POST /api/admin/users/{id}/suspend

### Side Effects
- mandatory security notification
- security event

### Concurrency
ROWVERSION/state condition prevents conflicting user updates.

### Idempotency
Repeated suspend is state-idempotent and must not duplicate mandatory notification logical event.

### Failure Cases
- reauth expired
- confirmation mismatch
- audit insert failure rolls entire mutation back

### Security
- No secret in audit; cannot impersonate target

### Edge Cases
- Target has active assessment; next authenticated call is blocked according to suspension rule

### Acceptance Criteria
- All prior auth rejected after commit
- Audit exists or mutation does not commit

### Required Tests
- T-AUTH-05/07
- AC-AUTH-002
- E2E-34/35

## Feature: Restore Database Backup

### Purpose
Define the complete implementation contract for Restore Database Backup.

### Actors
- Admin

### Preconditions
- Validated backup exists
- Maintenance/restore procedure ready

### Authorization
- Admin + fresh password reauth + exact phrase + mandatory reason

### Inputs
- backup ID
- reason
- confirmation

### Validation
- backup integrity/compatibility
- explicit target/environment

### Business Rules
- OPS-004
- AUTH-005
- AUDIT-002

### Algorithm
Create controlled restore operation record/audit authorization. Stop/coordinate app as deployment procedure requires. Never automatically overwrite live DB. Execute restore only after explicit approved action, then health/integrity verification and record outcome. Prefer restore drill to non-production for routine validation.

### Transaction
Authorization/audit transaction precedes external restore; actual restore is an operational workflow, not a normal web transaction.

### Database Reads
- backup_runs
- audit metadata

### Database Writes
- backup/operation status
- audit_events

### State Transition
BackupRun/restore operation transitions through requested/running/completed/failed operational states.

### API Contract
POST /api/admin/backups/{id}/restore

### Side Effects
- maintenance alert
- post-restore health checks

### Concurrency
One active restore operation per target/environment; operational lock outside request may be needed.

### Idempotency
Operation ID dedupe; do not replay a completed restore blindly.

### Failure Cases
- invalid backup
- reauth/phrase failure
- restore process failure
- verification failure

### Security
- Highest-risk operation; secrets/backup path controlled; mandatory audit

### Edge Cases
- Web process crashes after authorization but before restore
- partial restore handling follows SQL Server runbook

### Acceptance Criteria
- No automatic overwrite
- Explicit confirmation/audit mandatory
- Outcome verified

### Required Tests
- T-OPS-02
- AC-BACKUP-001
- E2E-36
