# Concurrency and Transaction Design

## 1. General strategy

- Use normal `READ COMMITTED` for most requests.
- Use `ROWVERSION`/conditional update for human edits.
- Use short `UPDLOCK`/`HOLDLOCK` only around race-sensitive counters/eligibility checks.
- Never hold a DB row lock for the whole Assessment duration.
- Background jobs claim with expiring leases.
- Use deterministic idempotency keys for retries.
- Return conflict (`409`) for stale human editor state instead of last-write-wins.

`ROWVERSION` is not Question business versioning.

## 2. Enroll Course

```text
BEGIN TRANSACTION
  load Course WITH (UPDLOCK, HOLDLOCK)
  require Course published/enrollable and not archived/trash
  require authenticated Student
  verify every CoursePrerequisite against CourseCompletionSummary.prerequisite_eligible
  if capacity != NULL:
      count active enrollment_periods for Course
      require count < capacity

  upsert logical Enrollment by UNIQUE(student_user_id, course_id)

  if no current ACTIVE period:
      next_period_no = max(period_no)+1
      insert EnrollmentPeriod(status=ACTIVE, started_at=server_now)
      update Enrollment.current_period_id, status=ACTIVE,
             current_progress_percent=0, enrolled_at=server_now, left_at=NULL
      insert EnrollmentEvent(ENROLLED or REENROLLED)

  if first ever enrollment:
      set courses.first_student_enrolled_at if NULL
COMMIT
```

Race protection:
- Course row serialization protects capacity.
- unique Enrollment and filtered unique active period protect duplicate requests.

## 3. Leave Course

**ASSUMPTION:** leaving is blocked while the current period has an `IN_PROGRESS` Attempt. This prevents losing authorization in the middle of a timed assessment.

```text
BEGIN
  lock Enrollment + current EnrollmentPeriod
  authorize Student owns Enrollment
  if IN_PROGRESS Attempt exists -> reject
  update period status=LEFT, left_at=now, retention_due_at=now+30d
  update Enrollment status=RETENTION_PENDING, left_at=now,
         detail_retention_due_at=...
  insert EnrollmentEvent(LEFT)
COMMIT
```

## 4. Re-enroll

```text
BEGIN
  run the same prerequisite/capacity checks as enroll
  lock Enrollment
  close any stale ACTIVE period if inconsistent -> error/repair path
  insert new period_no (do not copy old LessonProgress/Attempts)
  set Enrollment current_period_id=new period
  reset current_progress_percent=0
  status=ACTIVE
  insert EnrollmentEvent(REENROLLED)
COMMIT
```

Prior `CourseCompletionSummary` is not reset.

## 5. Mark Lesson progress/completion

Browser sends bounded heartbeat/view information, not `completed=true`.

```text
BEGIN
  authorize EnrollmentPeriod ACTIVE and Lesson accessible
  load LessonProgress WITH rowversion
  accepted_delta_seconds = min(server_elapsed_since_last_heartbeat, configured_cap)
  max_view_fraction = max(existing, sanitized_client_fraction)
  update progress atomically
  if completed_at is NULL
     and seconds_spent >= Lesson.minimum_completion_seconds
     and max_view_fraction >= Lesson.viewed_fraction_required:
         set completed_at=server_now
  recompute Enrollment.current_progress_percent from required Lessons/Assessments
  if Course completion rule now satisfied:
         mark current period completed
         upsert CourseCompletionSummary ever_completed=1/prerequisite_eligible=1
COMMIT
```

## 6. Publish Assessment

```text
BEGIN
  lock Assessment row
  require DRAFT and rowversion matches
  preflight:
     >=1 effective question
     answer keys valid
     points > 0
     timing valid
     blueprint has enough eligible candidates
     AI/import questions approved
     referenced files SAFE
  materialize/refresh assessment_question_pool if blueprint/random pool used
  set status=PUBLISHED, published_at=server_now
COMMIT
```

Timing is now trigger-protected.

## 7. Start AssessmentAttempt

```text
BEGIN
  lock Assessment WITH (UPDLOCK)
  require status=PUBLISHED
  require server_now inside open/close window
  require EnrollmentPeriod ACTIVE and authorized
  enforce attempt_limit under lock

  allocate attempt_number
  insert AssessmentAttempt(CREATED)

  if Assessment.first_attempt_started_at is NULL:
      set it = server_now
      freeze blueprint/pool semantics

  select fixed questions + random pool questions using frozen structure
  for each selected Question:
      read questions.current_revision_id
      read current QuestionRevision + choices
      insert AttemptQuestion snapshot
      insert AttemptChoiceSnapshot in randomized/fixed order
      mark revision.was_student_exposed=1
      increment Question usage cache

  compute deadline_at = min(
      start + time_limit if configured,
      close_at if configured
  )
  status=IN_PROGRESS, started_at=server_now
COMMIT
```

Important race: Instructor correction concurrent with start. The transaction reads the current revision under an isolation/locking strategy that results in either old or new revision atomically. Correction `effective_at` determines full-credit eligibility if the old content was assigned before the save.

## 8. Random question selection

Selection occurs inside Attempt start. Candidate pool is already structure-frozen after the first start.

For each blueprint rule:
- query pool rows for the rule;
- include fixed candidates;
- choose remaining count using application RNG;
- prefer lower recent usage when configured, with randomization inside a bounded least-used candidate set;
- validate no duplicate Question across rules/sections;
- store final set in AttemptQuestion.

Never regenerate on reload.

## 9. Acquire first-tab editing lease

No long DB lock.

```text
BEGIN
  load Attempt
  require IN_PROGRESS and before deadline
  if editor_session_id IS NULL OR lease_expires_at <= now:
      conditional UPDATE
         editor_session_id = current auth_session
         lease_token_hash = hash(new random token)
         lease_acquired_at = now
         lease_expires_at = now + lease_window
         last_heartbeat_at = now
      WHERE id=? AND row_version=expected
  else if editor_session_id == current auth_session:
      renew / return current ownership
  else:
      reject second tab as read-only
COMMIT
```

A lease token is returned once; only its hash is stored.

## 10. Heartbeat

```text
UPDATE assessment_attempts
SET last_heartbeat_at=now,
    lease_expires_at=now+lease_window
WHERE id=?
  AND editor_session_id=?
  AND lease_token_hash=hash(token)
  AND status='IN_PROGRESS'
  AND lease_expires_at > now-safety_grace;
```

No row found = lease lost.

## 11. Stale owner / takeover

```text
BEGIN
  lock Attempt briefly
  if status != IN_PROGRESS -> reject
  if lease_expires_at > now and owner != caller -> reject
  replace owner session + token + timestamps
COMMIT
```

The same Attempt, deadline, snapshots and saved answers continue.

## 12. Autosave answer

Request carries:
- attempt public ID;
- AttemptQuestion ID/public handle;
- lease token;
- `change_id` UUID;
- `client_sequence`;
- answer payload.

```text
BEGIN
  load Attempt and validate active lease
  require server_now <= deadline_at
  if AnswerEvent(change_id) exists:
      return prior accepted/rejected outcome

  validate payload belongs to AttemptQuestion/ChoiceSnapshots

  load current AttemptAnswer WITH rowversion
  if client_sequence <= last_client_sequence:
      append/reuse rejected STALE event
      return current server answer

  replace normalized current answer:
      text OR selected choice rows
  increment answer_version
  set last_client_sequence/change_id/saved_at
  insert accepted AnswerEvent
COMMIT
```

This prevents an old offline event arriving after a newer answer from overwriting it.

## 13. Submit Attempt

```text
BEGIN
  lock Attempt
  if terminal:
      return existing AssessmentResult (idempotent)
  validate current Student/attempt
  if first submission:
      persist submission_idempotency_key
  accept only Answer state saved before deadline
  set submitted_at=server_now
  grade auto-gradeable questions using correction policy/latest approved answer
  create/update current AttemptQuestionGrade + histories
  if any Essay pending:
      status=PENDING_GRADING
      result.status=PENDING
  else:
      status=GRADED
      finalize result
  set finalized_at
COMMIT
```

Two concurrent submits serialize on the Attempt row and return the same final result.

## 14. Server expiration

Worker/query finds `IN_PROGRESS` Attempts where `deadline_at <= server_now`.

```text
BEGIN
  conditional lock Attempt
  if already terminal -> no-op
  status=EXPIRED
  grade current server-saved answers
  finalize exactly like submit
COMMIT
```

Offline client changes arriving later are rejected `AFTER_DEADLINE`.

## 15. Manual Essay grading

```text
BEGIN
  authorize current Course Instructor/Admin
  load AttemptQuestionGrade + AttemptQuestion points with rowversion
  validate 0 <= new_score <= assigned_points
  if current grade exists and changes:
      require reason
      insert AttemptQuestionGradeHistory(old,new,MANUAL_REVISION)
  update current grade
  recompute AssessmentResult + append ResultHistory if post-result score changed
  if all pending manual questions finished:
      set Attempt=GRADED, Result=FINAL/RELEASED by release policy
COMMIT
```

## 16. Update correct answer only

```text
BEGIN
  authorize current owner/Admin
  lock Question
  require used Question -> create new revision_no
  copy unchanged content/choices; change only correct flags/accepted answer
  insert QuestionCorrection(type=ANSWER_ONLY, from,to,effective_at,reason)
  set Question.current_revision_id=new revision
  insert required AuditEvent
COMMIT

AFTER COMMIT
  enqueue idempotent RegradeJob(correction_id)
```

The HTTP request does not synchronously regrade thousands of attempts.

## 17. Update Question content/choices

```text
BEGIN
  authorize
  lock Question
  create new revision with new content/choices
  classify as CONTENT_OR_CHOICES
  insert correction with effective_at=server_now
  switch current revision
  audit
COMMIT

AFTER COMMIT
  enqueue regrade/full-credit job
```

Worker applies full credit to eligible AttemptQuestions where:
- `source_question_id` matches;
- Attempt started before correction effective time;
- EnrollmentPeriod detail not purged.

Active Student UI is not changed.

## 18. Start/apply Regrade

Creation:

```text
insert one RegradeJob per QuestionCorrection (unique)
populate RegradeItem for eligible attempts in batches
```

Per item:

```text
BEGIN
  claim RegradeItem conditionally PENDING/FAILED -> PROCESSING
  re-check EnrollmentPeriod.detail_purged_at
  if purged -> SKIPPED
  lock affected AttemptQuestionGrade/Result
  apply ANSWER_ONLY or CONTENT_FULL_CREDIT rule
  append grade/result histories if value changes
  commit current grade/result
  mark item COMPLETED with old/new
COMMIT
```

After all items complete, update job counters/status and issue score-change notifications. Retry cannot create a duplicate item because of unique `(regrade_job_id, attempt_id)`.

## 19. Two corrections in quick succession

Corrections have immutable sequence via revision and `effective_at`.

- Never rewrite correction 1.
- Job 2 computes from current grade state and latest approved revision.
- Pending older job may be marked SUPERSEDED only when its effects are fully subsumed and no history would be lost; otherwise it completes in order.
- Recommended worker policy: serialize regrade jobs per `question_id` to make reasoning deterministic.

## 20. Delete Question

```text
BEGIN
  lock Question
  if never used:
      move TRASH; later hard-delete after restore window
  else if used but no Student attempt and all Assessment refs removable:
      remove refs explicitly, trash, later hard-delete
  else:
      status=TRASH/RETIRED
      keep identity + exposed/graded revisions
  audit if important
COMMIT
```

## 21. Delete Assessment

```text
BEGIN
  lock Assessment
  if no attempts:
      TRASH, recoverable -> hard-delete later
  else:
      TRASH/ARCHIVED historical
      do not cascade attempts
  audit
COMMIT
```

Former Enrollment detail purge is separately allowed to delete old Attempt detail after 30 days.

## 22. Replace File

```text
BEGIN
  create new FileRevision(status=QUARANTINED) under same FileAsset
COMMIT
upload bytes to quarantine
enqueue validation/scan
```

On all checks PASS:

```text
BEGIN
  lock FileAsset
  promote/deduplicate bytes to FileBlob
  set new revision SAFE
  verify required scans PASS
  old current revision -> RECOVERY with recovery_until≈30d
  new revision -> ACTIVE
  FileAsset.current_revision_id = new
  update blob references
COMMIT
```

If scan fails, old current remains unchanged.

## 23. Activate scanned file

Activation repeats required scan checks inside the transaction. The DB trigger additionally rejects a current pointer unless it belongs to the same FileAsset and is already `ACTIVE`; a newly created asset remains `PENDING` with `current_revision_id = NULL` until this transaction succeeds.

## 24. Archive Course

```text
BEGIN
  lock Course
  require no active CoursePrerequisite references where this Course is prerequisite
  set ARCHIVED
  invalidate KnowledgeDocuments for RAG in same DB transaction
  audit
COMMIT
AFTER COMMIT
  enqueue vector invalidation
```

Already enrolled Students keep LMS read access per business rule; RAG does not.

## 25. Purge Enrollment detail

See Retention Matrix. Key race rule:
- lock/mark period;
- cancel/skip outstanding RegradeItems targeting it;
- verify no active Attempt;
- write compact summary first;
- delete detail explicitly;
- set `detail_purged_at` and EnrollmentEvent.

## 26. Anonymize User

```text
BEGIN
  lock User
  revoke auth + increment auth_version
  delete/revoke optional authentication artifacts
  replace email/display PII with unique tombstone values
  clear avatar
  status=ANONYMIZED
  preserve PK
  audit using redacted before/after
COMMIT
```

## 27. Instructor role revoke during edit

Role revoke transaction does not need to delete Course. It removes the role, notifies User, and may set owned Courses to owner NULL/reassign per Admin flow. Every subsequent write request rechecks current authorization, so a stale browser cannot save even if its rowversion is current.

## 28. Account suspended during active Attempt

Suspend immediately revokes web/API access. The Attempt timer remains server-side. No new answer save is accepted without authenticated active session. If deadline occurs, server finalizes using already saved answers.

## 29. Enrollment capacity race test pattern

Two concurrent enrollment transactions must both lock the same Course row before counting capacity. Without that lock, `count < capacity` in both requests could overbook. This case is mandatory in the test plan.
