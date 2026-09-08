# State Machines

The state column is not used when the state can be safely derived. Assessment `OPEN/CLOSED` is the main example: it is derived from `status='PUBLISHED'`, server time and `open_at/close_at`.

## User

```mermaid
stateDiagram-v2
    [*] --> ACTIVE
    ACTIVE --> SUSPENDED: Admin suspend
    SUSPENDED --> ACTIVE: Admin unsuspend
    ACTIVE --> DEACTIVATED: delete/deactivate request
    SUSPENDED --> DEACTIVATED: deactivate
    DEACTIVATED --> ANONYMIZED: PII anonymization
    ANONYMIZED --> [*]
```

Rules:
- SUSPENDED/DEACTIVATED/ANONYMIZED cannot authenticate.
- Suspend increments `auth_version` and revokes current session/JWT grants.
- Role state is independent of User status.

## Course

```mermaid
stateDiagram-v2
    [*] --> DRAFT
    DRAFT --> SUBMITTED_FOR_REVIEW
    SUBMITTED_FOR_REVIEW --> DRAFT: rejected
    SUBMITTED_FOR_REVIEW --> APPROVED: Admin approve
    APPROVED --> PUBLISHED: publish
    PUBLISHED --> ARCHIVED: archive
    DRAFT --> TRASH: delete
    PUBLISHED --> TRASH: delete request
    ARCHIVED --> TRASH: delete request
    TRASH --> DRAFT: restore unused draft
    TRASH --> PUBLISHED: restore published course in recovery
    TRASH --> ARCHIVED: recovery expires with history
```

Notes:
- A Course with Student history is not hard-deleted after trash; it becomes historical/archived.
- Course cannot archive/delete while it is an active prerequisite for another Course.
- Material published changes stage in `course_change_requests`.

## Lesson

```mermaid
stateDiagram-v2
    [*] --> DRAFT
    DRAFT --> PUBLISHED
    PUBLISHED --> HIDDEN: remove from active curriculum
    DRAFT --> TRASH
    PUBLISHED --> TRASH: delete request
    TRASH --> PUBLISHED: restore
    TRASH --> HISTORICAL: recovery expires and learning history exists
    TRASH --> [*]: hard delete if unused
```

A material rewrite does not clear existing `lesson_progress.completed_at`.

## Enrollment / EnrollmentPeriod

Logical Enrollment:

```mermaid
stateDiagram-v2
    [*] --> ACTIVE
    ACTIVE --> COMPLETED: current period completes
    ACTIVE --> LEFT: student leaves
    COMPLETED --> LEFT: student leaves
    LEFT --> ACTIVE: re-enroll / new period
    LEFT --> RETENTION_PENDING: detailed retention waiting
    RETENTION_PENDING --> ACTIVE: re-enroll
    RETENTION_PENDING --> DETAIL_PURGED: >30d no rejoin
    DETAIL_PURGED --> ACTIVE: future re-enroll
```

Period:

```mermaid
stateDiagram-v2
    [*] --> ACTIVE
    ACTIVE --> COMPLETED
    ACTIVE --> LEFT
    COMPLETED --> LEFT
    LEFT --> PURGED: retention due
```

Important:
- re-enroll opens a **new `enrollment_periods` row**, but keeps the same `enrollments` identity;
- new period starts progress from zero;
- `course_completion_summaries.ever_completed` does not reset;
- purged period is excluded from later regrade jobs.

## Question

```mermaid
stateDiagram-v2
    [*] --> DRAFT
    DRAFT --> ACTIVE
    ACTIVE --> RETIRED: delete after historical use
    DRAFT --> TRASH: delete
    ACTIVE --> TRASH: recoverable delete
    TRASH --> ACTIVE: restore
    TRASH --> RETIRED: recovery expires with student history
    TRASH --> [*]: hard delete only if safe/unused
```

QuestionRevision does not need a status enum. Exposure/grading flags determine historical retention.

## Assessment

```mermaid
stateDiagram-v2
    [*] --> DRAFT
    DRAFT --> PUBLISHED: publish/preflight success
    PUBLISHED --> CANCELLED: serious issue
    PUBLISHED --> ARCHIVED: lifecycle end
    DRAFT --> TRASH
    PUBLISHED --> TRASH: recoverable delete
    CANCELLED --> ARCHIVED
    TRASH --> PUBLISHED: restore in recovery
    TRASH --> ARCHIVED: recovery expires with attempts
    TRASH --> [*]: hard delete if no attempts
```

Derived availability:
- **Not yet open**: PUBLISHED and `server_now < open_at`.
- **Open**: PUBLISHED, `open_at IS NULL OR server_now >= open_at`, and `close_at IS NULL OR server_now < close_at`.
- **Closed**: PUBLISHED and `server_now >= close_at`.
- `open_at`, `close_at`, `time_limit_minutes` are immutable after publish.

## AssessmentAttempt

```mermaid
stateDiagram-v2
    [*] --> CREATED
    CREATED --> IN_PROGRESS: start transaction
    IN_PROGRESS --> SUBMITTED: student submit
    IN_PROGRESS --> EXPIRED: server deadline
    IN_PROGRESS --> CANCELLED: assessment cancelled
    SUBMITTED --> PENDING_GRADING: essay/manual work pending
    EXPIRED --> PENDING_GRADING: essay/manual work pending
    SUBMITTED --> GRADED: all auto grade
    EXPIRED --> GRADED: all auto grade
    PENDING_GRADING --> GRADED: manual grading complete
```

- Deadline = minimum of `started_at + time_limit` and Assessment `close_at`.
- Submit/expire finalizes only server-ACKed answers.
- `GRADED` does not mean score has been released to Student; release is `assessment_results.released_at`.

## FileRevision / FileAsset

```mermaid
stateDiagram-v2
    [*] --> QUARANTINED
    QUARANTINED --> VALIDATING
    VALIDATING --> SCANNING
    SCANNING --> SAFE: all required checks pass
    SCANNING --> REJECTED: fail/error
    SAFE --> ACTIVE: activate as asset current revision
    ACTIVE --> RECOVERY: replacement succeeds
    RECOVERY --> ACTIVE: restore old version
    RECOVERY --> DELETED: recovery expires and no required reference
    REJECTED --> DELETED: cleanup
```

Scanner unavailable/error is fail-closed.

## DocumentImportJob

```mermaid
stateDiagram-v2
    [*] --> QUEUED
    QUEUED --> PROCESSING
    PROCESSING --> REVIEW_REQUIRED: ambiguous/broken items
    PROCESSING --> COMPLETED: parse complete
    PROCESSING --> FAILED
    REVIEW_REQUIRED --> COMPLETED: Instructor finishes review
    QUEUED --> CANCELLED
    REVIEW_REQUIRED --> CANCELLED
```

`COMPLETED` means import processing/review is complete, not that an Assessment was automatically published.

## KnowledgeVersion

```mermaid
stateDiagram-v2
    [*] --> PENDING
    PENDING --> PROCESSING
    PROCESSING --> ACTIVE
    PROCESSING --> FAILED
    ACTIVE --> INVALIDATED: new active version/source delete/archive
```

Activation is atomic: set new version ACTIVE, set Document current pointer, invalidate prior active version. A FAILED candidate never becomes current.

## RegradeJob

```mermaid
stateDiagram-v2
    [*] --> QUEUED
    QUEUED --> RUNNING
    RUNNING --> PARTIAL: interrupted/retryable
    PARTIAL --> RUNNING
    RUNNING --> COMPLETED
    RUNNING --> FAILED
    FAILED --> RUNNING: retry
    QUEUED --> CANCELLED: superseded/cancelled
```

Per-attempt `regrade_items` provide idempotent completion tracking.

## BackgroundJob

```mermaid
stateDiagram-v2
    [*] --> QUEUED
    QUEUED --> RUNNING: claim lease
    RUNNING --> SUCCEEDED
    RUNNING --> QUEUED: retry/backoff
    RUNNING --> FAILED: max attempts
    QUEUED --> CANCELLED
```

A crashed worker leaves an expiring claim; the job may be reclaimed only when the domain handler is idempotent.

## Notification / Email

Notification:
- created unread;
- `read_at` set once/read idempotently;
- low-value notification may be deleted after `expires_at`.

Email delivery:

```mermaid
stateDiagram-v2
    [*] --> PENDING
    PENDING --> SENDING
    SENDING --> SENT
    SENDING --> PENDING: retryable failure
    SENDING --> FAILED: retries exhausted
    PENDING --> CANCELLED
```

A unique delivery key prevents retry duplication.
