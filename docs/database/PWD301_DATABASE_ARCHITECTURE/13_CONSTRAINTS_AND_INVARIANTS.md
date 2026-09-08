# Constraints and Database Invariants

## Enforcement taxonomy

- **DB-enforced**: FK, PK, unique, check, filtered unique index, critical trigger.
- **Transaction-enforced**: short transaction with locks/conditional updates.
- **Service-enforced**: multi-row/domain rule that SQL CHECK cannot express safely.
- **Worker-enforced**: background retry/idempotency/cleanup.
- **Authorization-enforced**: permission layer; schema only supplies relationships.

| ID | Invariant | DB protection | Transaction protection | Service / worker / authorization |
|---|---|---|---|---|
| AUTH-001 | Email unique | unique `users.email_normalized` | email change conditional update | verified token required |
| AUTH-002 | Valid cumulative role sets | unique UserRole pair | role grant/revoke transaction | service ensures Student ⊂ Instructor ⊂ Admin |
| AUTH-003 | Suspend kills access | user status/check + grant/session rows | increment `auth_version`, revoke rows atomically | every auth request checks user/status/version |
| AUTH-004 | Sensitive Admin action requires re-auth + phrase + reason | audit reason column | audit + mutation same transaction where DB-only | session `reauthenticated_at`, exact phrase check |
| AUTH-005 | No impersonation | actor FK/audit actor | — | preview never replaces authenticated identity |
| COURSE-001 | Course code/title unique | unique normalized constraints | — | normalize/display validation |
| COURSE-002 | Course owner is Instructor if non-null | FK to users | owner reassignment transaction | permission service verifies INSTRUCTOR role |
| COURSE-003 | Prerequisite not self | CHECK | — | cycle detection for multi-node graph |
| COURSE-004 | Prerequisite cycle forbidden | cannot express simple CHECK | serializable/lock affected Course graph where needed | graph traversal before insert |
| COURSE-005 | Active prerequisite blocks archive/delete | FK protects hard delete | archive check + status update transaction | service checks reverse dependency |
| COURSE-006 | Course capacity not exceeded | positive capacity CHECK | lock Course row and count ACTIVE periods before enrollment | enrollment service |
| COURSE-007 | One logical Enrollment/User/Course | UNIQUE student+course | upsert/re-enroll transaction | enrollment service |
| COURSE-008 | At most one ACTIVE period | filtered unique index | close old/open new transaction | service |
| COURSE-009 | Re-enroll restarts progress | period identity | create new period + set current pointer | do not copy LessonProgress |
| COURSE-010 | Completed history satisfies prerequisite | unique completion summary | completion transaction upserts summary | prerequisite query uses summary |
| LESSON-001 | Position unique in Course | UNIQUE course+position | reorder transaction | stale editors rejected |
| LESSON-002 | Completion requires time + view evidence | numeric CHECK bounds | bounded atomic progress update | service compares Lesson thresholds |
| LESSON-003 | New Lesson optional for existing period | timestamp field | — | required if period.started_at >= effective timestamp |
| QBANK-001 | Question belongs one Course | FK | — | optional Lesson must be same Course |
| QBANK-002 | Revision sequence unique | UNIQUE question+revision_no | lock Question when creating new revision | service increments max/current |
| QBANK-003 | Used revision content immutable | critical trigger | revision activation transaction | important edit creates new row |
| QBANK-004 | Choice belongs revision | FK | create revision + choices atomically | no shared mutable choices |
| QBANK-005 | Type cannot change after any Student answer | critical trigger on current revision pointer | activate revision transaction | service pre-check |
| QBANK-006 | Exact MC grading | — | grade transaction | service compares exact selected set |
| QBANK-007 | Exposed/graded revision retained | exposure/grading flags | marker set with Attempt/grading | cleanup worker excludes flagged revisions |
| ASSESS-001 | Timing immutable after publish | critical trigger | publish transaction | UI/service block |
| ASSESS-002 | Structure locked after first start | critical triggers on assignments/pool/sections/rules | first-start marker set before snapshot | service |
| ASSESS-003 | Points locked after first start | same structure triggers | — | service |
| ASSESS-004 | Blueprint shortage blocks publish | — | preflight/publish transaction revalidates | service reports shortage |
| ASSESS-005 | Question identity mapping uses latest revision at start | FK Question identity | resolve current revision inside start transaction | snapshot result |
| ATTEMPT-001 | Attempt limit | UNIQUE attempt number | lock Assessment/Student attempt scope and count | service |
| ATTEMPT-002 | Deadline server authoritative | data types/checks | compute once in start transaction | ignore client clock |
| ATTEMPT-003 | Attempt snapshot immutable | no correct flags stored | insert snapshot atomically | no update APIs for content/order |
| ATTEMPT-004 | One editor tab | lease fields | conditional acquire/takeover update | lease token required on save |
| ATTEMPT-005 | Stale tab cannot save | rowversion/lease state | save validates lease before update | reject 409/423 |
| ATTEMPT-006 | Old offline answer cannot overwrite newer | unique change UUID + sequence | conditional answer update | client syncs sequence on resume |
| ATTEMPT-007 | Submit idempotent | unique submission key | conditional terminal transition | terminal attempt returns same result |
| ATTEMPT-008 | After deadline no new answer accepted | — | compare DB/server time in save transaction | rejected event may be recorded |
| GRADE-001 | Essay manual grade before final result | grade status CHECK | result finalize transaction | pending-grade query |
| GRADE-002 | Post-result changes keep history | history tables | current grade/result + history in same transaction | reason required |
| REGRADE-001 | Answer-only correction regrades eligible attempts | correction/regrade unique constraints | per-item atomic grade update | resumable worker |
| REGRADE-002 | Content/choice correction full credit for earlier starters | correction type | compare attempt.started_at < effective_at | worker/current grading service |
| REGRADE-003 | Purged enrollment period excluded | `detail_purged_at` | target query snapshot | regrade worker skip reason |
| REGRADE-004 | Regrade retry cannot double-apply | UNIQUE job+attempt | item claim/status conditional | idempotent worker |
| FILE-001 | Unsafe file cannot become current | current-revision safe trigger | activation transaction | required scans all PASS |
| FILE-002 | Scanner error is fail-closed | scan status CHECK | — | file service never marks SAFE |
| FILE-003 | Blob dedup | unique SHA-256 | insert-or-select transaction | verify size/hash before reuse |
| FILE-004 | Shared blob not deleted early | FK/refcount metadata | cleanup checks live refs + recovery | cleanup worker |
| FILE-005 | Direct storage key is not authorization | — | — | download route checks authenticated Course/Lesson access |
| IMPORT-001 | Import never auto-publishes | Assessment status | promotion transaction only creates draft | Instructor approval |
| IMPORT-002 | AI suggested answer needs explicit confirm | confirmation metadata | promotion verifies confirmation | UI/service |
| AI-001 | Student RAG only authorized published sources | FK source scope/status | — | permission prefilter before vector retrieval |
| AI-002 | Archived/deleted source not retrievable | knowledge status/current version | invalidate transaction | vector invalidation worker + query filter |
| AI-003 | Raw chat expires after 5 min inactivity | `expires_at` index | new user message updates expiry | cleanup worker |
| AI-004 | Personalized cache not shared | no SQL shared cache | — | runtime cache key/policy; generic only |
| NOTIF-001 | Notification/email retry dedup | unique event+recipient/delivery key | outbox insert in business flow | worker retries |
| NOTIF-002 | Security email cannot disable | CHECK preference | — | service ignores optional preference for mandatory category |
| AUDIT-001 | Audit append-only | trigger + production permissions | — | correction is new event |
| AUDIT-002 | Sensitive action fails if audit fails | — | business mutation + AuditEvent same DB transaction | service |
| DELETE-001 | No broad cascade historical loss | FK NO ACTION by default | service-managed delete | retention policy |
| OPS-001 | Job claim retry safe | job rowversion/dedupe | conditional claim lease | idempotent handler |
| CONCUR-001 | Human stale editor cannot overwrite | ROWVERSION | conditional UPDATE | return conflict and require refresh |

## Critical trigger rationale

Triggers are intentionally limited to invariants where an accidental bypass through a new service path would be dangerous:

1. Assessment timing immutability after publish.
2. Assessment structure/points lock after first start.
3. Used QuestionRevision/answer structures immutability.
4. Question type lock after first Student answer.
5. FileAsset cannot point to unsafe revision.
6. KnowledgeDocument cannot point to inactive version.
7. AuditEvent append-only.

Most business rules remain in explicit services because they require permissions, graph traversal, time, or cross-domain context and would become opaque/fragile if implemented as large triggers.

## Foreign-key delete policy

Default: `NO ACTION`.

`SET NULL` is used only when the historical child remains meaningful without the current actor/optional owner, e.g. deleted/reassigned actor references.

`CASCADE` is intentionally rare. Even when a disposable child could cascade, implementation should still prefer explicit service deletion for high-value domains so recovery/history rules are visible.

## Invariants not safely enforceable by CHECK alone

### Course prerequisite cycle

Requires graph traversal. Service performs cycle test inside a transaction and blocks the edge if it creates a path back to the source Course.

### Owner has Instructor role

FK only confirms that a User exists. Permission/role service verifies role set before assigning `owner_instructor_id`.

### Question Lesson belongs to same Course

Two independent FKs cannot express same-parent equality without extra composite keys. Service validates `lesson.course_id == question.course_id`.

### Attempt selected choice belongs to same AttemptQuestion

Service validates the selected ChoiceSnapshot parent before inserting `attempt_answer_choices`.

### Points awarded <= assigned points

The max lives in another table. Grading transaction loads/locks AttemptQuestion and clamps/rejects out-of-range values.

### Required scan set complete

Which security checks are required depends on file type/configuration. Activation service verifies the required set of PASS rows; a trigger additionally prevents current pointer to non-safe revision.

### RAG authorization

Authorization is user/course/publication state dependent and must be evaluated by the permission/retrieval layer before chunks reach Gemini.
