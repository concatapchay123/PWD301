# Retention, Delete and Restore Matrix

## Principles

- **Trash/recovery** is not the same as archive.
- **Hard delete** is allowed only when the entity is disposable and has no historical dependency.
- **Historical retention** can preserve a minimal tombstone rather than full operational detail.
- Enrollment detail purge is the explicit exception that allows old former-student Attempt detail to disappear after 30 days.
- Audit records are not user-deletable.
- Physical file bytes and relational metadata have separate retention.
- Cleanup workers operate in small idempotent batches.

| Entity | Active retention | Soft delete / archive | Recovery | Hard delete | Historical retention | Anonymization | Notes |
|---|---|---|---|---|---|---|---|
| User | while account exists | deactivate/suspend first | account policy | normally no if history exists | identity tombstone | PII can anonymize | attempts/audit FK remain |
| UserRole | active role | remove row on revoke | no | yes junction row | AuditEvent records change | n/a | role history via audit |
| AuthSession | until expiry/revoke | revoke | no | after short security retention | SecurityEvent only | n/a | raw session key never stored |
| JWT grant | until expiry/revoke | revoke | no | after expiry retention | SecurityEvent where needed | n/a | auth_version also revokes globally |
| Security token | until consume/expire | n/a | no | short cleanup | action audit only | n/a | token stored hashed |
| InstructorApplication | through decision | status | no | rejected old record may archive | reviewed decision retained reasonably | user may anonymize | approval changes role |
| Course no Student history | active/trash | TRASH | ~30d | yes if no dependencies | optional audit only | n/a | prerequisite FK may block |
| Course with Student history | active → archive/trash | TRASH then ARCHIVED historical | ~30d restore | not in way that breaks history | retain minimal Course identity | owner user may anonymize | disappears from discovery |
| CoursePrerequisite | active relation | remove explicitly | n/a | yes relation | audit if material | n/a | active dependency blocks archive |
| CourseChangeRequest | until reviewed/applied | status | n/a | cleanup old staging | audit + applied source data remain | actor may anonymize | proposed JSON not permanent content source |
| Lesson unused | active/trash | TRASH | ~30d | yes | none required | n/a | only if no learning history |
| Lesson learned | active/hidden/trash | HIDDEN/TRASH→HISTORICAL | ~30d | keep minimal record | completion links/history | n/a | removed from new learners |
| Enrollment | long-lived User-Course identity | status LEFT/DETAIL_PURGED | re-enroll uses same row | generally no | keep logical relation + summary | user anonymization | unique User-Course |
| EnrollmentPeriod | active learning period | LEFT/PURGED | rejoin creates new period | header may retain compact | lifecycle dates | user via parent | period detail can purge |
| LessonProgress | while period active + 30d after leave | n/a | available during retention | yes after due when period purged | CourseCompletionSummary survives | user via parent | old detail no future regrade |
| CourseCompletionSummary | indefinite while prerequisite/history needed | n/a | n/a | only with complete user/history erasure policy | retain compact | user can anonymize | prerequisite proof |
| Question unused | active/trash | TRASH | ~30d | yes | none | n/a | if no refs |
| Question used no Student attempt | active/trash | TRASH | ~30d | yes after references removed | optional audit | n/a | remove from Assessment first |
| Question answered by Student | active/retired | RETIRED/TRASH | ~30d UI recovery | no destructive hard delete | minimal Question identity indefinitely | creator may anonymize | enables revision history |
| QuestionRevision never exposed/graded | draft/current | cleanup candidate | policy-defined | yes if not current/ref | none | n/a | cleanup only when safe |
| QuestionRevision exposed/graded | historical | no user delete | n/a | no | retain indefinitely | creator may anonymize | marker survives attempt purge |
| Question choices/accepted answers | with revision | n/a | n/a | only with deletable revision | same as parent revision | n/a | immutable historical answer structures |
| Assessment no attempts | active/trash | TRASH | ~30d | yes | audit | n/a | delete children safely |
| Assessment with attempts | active/archive/trash | ARCHIVED/TRASH | ~30d | no destructive hard delete | retain definition/tombstone | creator may anonymize | individual former-enrollment attempt detail may still purge |
| AssessmentAttempt active/retained | current period + former period retention | terminal status | no | after former period >30d purge rule | compact Course summary + revision exposure remains | Student can anonymize if record retained | purged attempt not regraded |
| AttemptQuestion/Choice snapshot | with Attempt | n/a | n/a | with eligible Attempt purge | QuestionRevision exposure marker remains | n/a | do not rewrite before purge |
| AttemptAnswer current | with Attempt | n/a | n/a | with eligible Attempt purge | aggregate summary only | n/a | final answer detail can disappear |
| AttemptAnswerEvent | short/detail retention | n/a | n/a | yes; high-volume cleanup | current answer/result before overall purge | n/a | debug/autosave only |
| Attempt grades/result | while detailed Attempt retained | n/a | n/a | can purge with old former period per final rule | compact final aggregate summary | Student can anonymize | post-result histories follow same detail policy |
| QuestionCorrection | long-term | status | n/a | normally no | revision/correction history | actor may anonymize | source of regrade policy |
| RegradeJob/Item | operational + audit horizon | completed/archive | retry | items may archive/cleanup after stable | correction + grade history remain if detail retained | n/a | purged periods skipped |
| FileBlob | while refs/recovery exist | DELETING | no content restore after physical delete | yes bytes when zero refs + recovery expired | minimal hash/size metadata if important | n/a | shared blob not deleted on one link removal |
| FileAsset | logical lifecycle | TRASH/HISTORICAL | ~30d where applicable | if no history/ref | metadata if historical | uploader may anonymize | current revision pointer |
| FileRevision active | active/replaced/recovery | RECOVERY | target ~30d | yes bytes/ref after safe cleanup | scan/minimal metadata if needed | uploader may anonymize | new replacement must be safe before swap |
| FileScanResult | security/operational horizon | n/a | n/a | low-value old detail may archive | malware/security fact survives SecurityEvent | n/a | fail-closed |
| DocumentImportJob/ImportQuestion | through review/promotion | terminal | no | diagnostics can cleanup | QuestionProvenance survives | reviewer may anonymize | never source of published question after promotion |
| AIConversation/AIMessage | active chat only | expire | no | **after 5 min inactivity** | none raw | user may anonymize metadata | raw content not audit |
| AIRequest | usage/security horizon | n/a | n/a | policy cleanup/aggregate | minimal metadata possible | user may anonymize | no raw prompt required |
| KnowledgeDocument/Version | while source valid | INVALIDATED | source restore may re-index | old chunks can delete | version/source trace metadata | n/a | archived Course never retrieve |
| KnowledgeChunk | active version | invalidated via parent | no | yes when old version cleanup | source version usage can remain | n/a | vector store deletion too |
| Notification ordinary | until read/expiry | n/a | no | yes after expiry | durable fact only if AuditEvent exists | recipient may anonymize | read/unread |
| EmailDelivery | retry + operational horizon | terminal | retry | cleanup after retention | event/audit remains | email snapshot PII cleanup | send failure no rollback |
| AuditEvent | indefinite/archival | archive storage only | n/a | not by application | retain indefinitely according to policy | actor User may be anonymized | append-only |
| BackgroundJob | through completion/retry | terminal | retry | cleanup after domain stable | domain job/history survives if needed | n/a | generic queue state only |
| SystemAlert | until resolved + operational horizon | resolved | no | old resolved can cleanup | critical source Security/Audit remains | n/a | Admin dashboard |
| BackupRun | backup retention horizon | terminal | n/a | metadata according to backup policy | enough to prove backup/restore drills | actor may anonymize | backup bytes external |
| GradeExport | until expiry | EXPIRED | regenerate | delete generated file promptly | export audit event retained | requester may anonymize | sensitive, no public URL |
| AnalyticsSnapshot | until stale | overwrite/cleanup | recompute | yes | none | aggregate | cache only |
| HealthSnapshot | short operational | cleanup | recompute | yes | alerts retain important failure | none | never store secrets |

## 30-day Enrollment purge algorithm

Eligibility:
1. period status is LEFT;
2. `retention_due_at <= server_now`;
3. no active re-enrollment period needs to reuse old detail;
4. no in-flight business transaction is editing that period;
5. regrade items targeting the period are either complete/cancelled or will be marked `SKIPPED: DETAIL_PURGED`.

Within a controlled cleanup job:
- mark period as being purged/lock it;
- ensure `course_completion_summaries` contains required compact facts;
- delete answer events, current answers, answer choices, Attempt snapshots, grade histories/results and Attempts that policy allows;
- do **not** clear `question_revisions.was_student_exposed`;
- set `detail_purged_at`;
- append `EnrollmentEvent(DETAIL_PURGED)`;
- update logical Enrollment status if appropriate.

## Trash recovery

For Course/Lesson/Question/Assessment:
- deletion creates `deleted_at`, `restore_until`, actor and TRASH status;
- discovery/API default scopes exclude TRASH;
- Admin can restore before `restore_until`;
- after recovery:
  - unused record may hard-delete;
  - historically referenced record transitions to archival/historical state.

## User anonymization

Recommended transformation:
- set status `ANONYMIZED`;
- replace email with non-routable unique tombstone value;
- replace display name with anonymous label;
- clear avatar and optional profile PII;
- increment auth_version/revoke auth;
- preserve same User PK so attempts/results/audit remain referentially valid.

Never store a reusable original email in an audit JSON during anonymization.
