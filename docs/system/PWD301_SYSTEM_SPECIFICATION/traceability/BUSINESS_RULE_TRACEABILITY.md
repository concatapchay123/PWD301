# Business Rule → Database Traceability

This matrix is the implementation bridge. A backend change that touches a rule should update its listed service/tests if behavior changes.

| Rule ID | Business rule | Source/domain | Tables | Constraints | Service logic | Background job | Audit | Test cases |
|---|---|---|---|---|---|---|---|---|
| `AUTH-001` | Email là login identifier duy nhất và unique | `Identity` | users; user_security_tokens | UNIQUE email_normalized | verify token trước đổi email | — | email change audit | `T-AUTH-01..03` |
| `AUTH-002` | User role cumulative theo Student→Instructor→Admin | `Identity` | roles; user_roles | PK/UNIQUE pair | role service add/remove valid closure | — | role grant/revoke | `T-AUTH-04` |
| `AUTH-003` | Suspend revoke tất cả session/JWT ngay | `Auth` | users; auth_sessions; jwt_token_grants | status/auth_version | single transaction increment+revoke | — | security + audit + notification | `T-AUTH-05` |
| `AUTH-004` | Browser session, REST JWT | `Auth` | auth_sessions; jwt_token_grants | token/session uniqueness | separate middleware | — | security events | `T-AUTH-06` |
| `AUTH-005` | Sensitive Admin action reauth + phrase + reason | `Admin` | auth_sessions; audit_events | audit reason available | reauth freshness + exact phrase | — | mandatory audit | `T-AUTH-07` |
| `AUTH-006` | Admin không impersonate User | `Admin` | audit_events | actor stored true identity | preview mode preserves actor | — | audit | `T-AUTH-08` |
| `COURSE-001` | Course code unique | `Course` | courses | UNIQUE course_code_normalized | validation | — | create/update audit if sensitive | `T-COURSE-01` |
| `COURSE-002` | Course title unique | `Course` | courses | UNIQUE title_normalized | validation | — | — | `T-COURSE-02` |
| `COURSE-003` | Course có 0/1 owner Instructor | `Course` | courses; user_roles | FK owner | verify Instructor role | — | reassign audit | `T-COURSE-03` |
| `COURSE-004` | Instructor mất role không xóa Course | `Course` | courses; user_roles | owner nullable | revoke/reassign service | — | audit+notification | `T-COURSE-04` |
| `COURSE-005` | Prerequisite bắt buộc và không cycle | `Course` | course_prerequisites; course_completion_summaries | PK + self CHECK + FK | graph cycle/prerequisite eligibility | — | material change audit | `T-COURSE-05..07` |
| `COURSE-006` | Course prerequisite active block archive/delete | `Course` | course_prerequisites; courses | reverse FK | archive precheck transaction | — | audit | `T-COURSE-08` |
| `COURSE-007` | Optional capacity không overbook | `Enrollment` | courses; enrollments; enrollment_periods | capacity CHECK + active-period unique | lock Course then count | — | — | `T-ENROLL-01` |
| `ENROLL-001` | Một logical Enrollment User-Course | `Enrollment` | enrollments | UNIQUE student+course | upsert transaction | — | EnrollmentEvent | `T-ENROLL-02` |
| `ENROLL-002` | Re-enroll restart từ đầu nhưng cùng Enrollment | `Enrollment` | enrollments; enrollment_periods; enrollment_events | period unique/active filtered index | create new period, reset cache | — | event | `T-ENROLL-03` |
| `ENROLL-003` | Prior completed Course vẫn thỏa prerequisite | `Enrollment` | course_completion_summaries | UNIQUE user+course | prereq service reads summary | — | — | `T-ENROLL-04` |
| `ENROLL-004` | Leave >30d purge detail và ngừng future regrade | `Retention` | enrollment_periods; attempts; completion summaries | retention index | purge transaction | cleanup | EnrollmentEvent | `T-RET-01..03` |
| `LESSON-001` | Lesson reorder không mất completion | `Lesson` | lessons; lesson_progress | UNIQUE course+position | reorder transaction | — | audit | `T-LESSON-01` |
| `LESSON-002` | Lesson completion cần min time + viewed most | `Lesson` | lessons; lesson_progress | range CHECK | bounded heartbeat + compute | — | — | `T-LESSON-02` |
| `LESSON-003` | Lesson mới là Xem thêm cho existing period | `Lesson` | lessons; enrollment_periods | effective timestamp | progress computation compares start time | — | — | `T-LESSON-03` |
| `LESSON-004` | Material rewrite không bắt completed Student học lại | `Lesson` | lesson_progress | completed_at persisted | do not clear completion | — | audit material change | `T-LESSON-04` |
| `QBANK-001` | Question thuộc đúng một Course, Lesson optional | `Question` | questions; courses; lessons | FK | same-course lesson validation | — | — | `T-QB-01` |
| `QBANK-002` | Unused edit in-place; used important edit new revision | `Question` | questions; question_revisions | revision unique + immutability trigger | revision creation transaction | — | audit correction/edit | `T-QB-02` |
| `QBANK-003` | Choices/accepted answers versioned with revision | `Question` | question_revision_choices; question_revision_accepted_answers | FK/unique | revision activation | — | — | `T-QB-03` |
| `QBANK-004` | Type không đổi sau Student answer | `Question` | questions; question_revisions | critical trigger | service precheck | — | audit | `T-QB-04` |
| `QBANK-005` | Exposed/graded revision giữ indefinite | `Retention` | question_revisions | exposure flags | mark in attempt/grading transaction | cleanup excludes | — | `T-QB-05` |
| `QBANK-006` | Multiple-choice exact set, no partial | `Grading` | attempt_answer_choices; revision choices | — | grading exact set comparison | — | grade history if changed | `T-GRADE-01` |
| `QBANK-007` | Short answer multi accepted + normalized/exact mode | `Grading` | accepted answers; revision | UNIQUE normalized answer | grading normalization | — | — | `T-GRADE-02` |
| `ASSESS-001` | Timing config khóa sau publish | `Assessment` | assessments | critical trigger | publish service | — | audit | `T-ASSESS-01` |
| `ASSESS-002` | Structure khóa sau first start | `Assessment` | assessments; assignments; pool; sections; rules | critical triggers | first-start marker transaction | — | audit | `T-ASSESS-02` |
| `ASSESS-003` | Points khóa sau first start | `Assessment` | assignments; pool; rules | critical triggers | service | — | audit | `T-ASSESS-03` |
| `ASSESS-004` | Blueprint thiếu candidate block publish | `Assessment` | blueprints; rules; pool | positive checks | preflight revalidate | — | — | `T-ASSESS-04` |
| `ASSESS-005` | Student chưa start nhận latest revision | `Assessment` | questions; attempt_questions | current revision FK | resolve inside start transaction | — | — | `T-ASSESS-05` |
| `ASSESS-006` | Random attempt exact set/order được giữ | `Attempt` | attempt_questions; choice snapshots | unique positions | snapshot transaction | — | — | `T-ASSESS-06` |
| `ATTEMPT-001` | Attempt limit configurable | `Attempt` | assessment_attempts; assessments | unique attempt no | locked start count | — | — | `T-ATT-01` |
| `ATTEMPT-002` | Server authoritative deadline + hard close | `Attempt` | assessment_attempts | deadline/start CHECK | compute min(time limit, close) | expiry worker | — | `T-ATT-02` |
| `ATTEMPT-003` | Only first tab edits; stale takeover | `Attempt` | assessment_attempts; auth_sessions | lease fields | conditional lease acquire/heartbeat | — | security event optional | `T-ATT-03..05` |
| `ATTEMPT-004` | MC save immediate; text debounce; resume current answer | `Attempt` | attempt_answers; answer events | unique per question | autosave transaction | — | — | `T-ATT-06` |
| `ATTEMPT-005` | Offline old event cannot overwrite newer | `Attempt` | attempt_answer_events; attempt_answers | unique change ID | client sequence conditional update | — | — | `T-ATT-07` |
| `ATTEMPT-006` | After deadline only saved answers count | `Attempt` | attempts; answers | — | save checks deadline | expiry finalizer | — | `T-ATT-08` |
| `ATTEMPT-007` | Submit idempotent | `Attempt` | assessment_attempts; assessment_results | unique idempotency key / terminal row | serialized terminal transition | — | — | `T-ATT-09` |
| `GRADE-001` | Essay manual, final pending until complete | `Grading` | attempt_question_grades; results | status checks | manual grade/finalize transaction | — | grade history | `T-GRADE-03` |
| `GRADE-002` | Manual essay revision keeps old/new/reason/actor | `Grading` | grade history; result history | append PK | current+history transaction | — | AuditEvent | `T-GRADE-04` |
| `REGRADE-001` | Answer-only correction auto regrade eligible attempts | `Regrade` | corrections; regrade jobs/items; grades/results | unique correction/job/item | create correction atomically | regrade worker | score audit+notification | `T-REG-01` |
| `REGRADE-002` | Content/choices correction gives full credit to earlier attempts | `Regrade` | question_corrections; attempt_questions; grades | correction type | compare started_at/effective_at | regrade worker | history+notification | `T-REG-02` |
| `REGRADE-003` | Historical snapshot/answer never rewritten | `Regrade` | attempt_questions; answers; histories | snapshot design | grade only current grade rows | worker | history | `T-REG-03` |
| `REGRADE-004` | Regrade resumable/idempotent | `Regrade` | regrade_items | UNIQUE job+attempt | conditional claim | worker retry | job history | `T-REG-04` |
| `FILE-001` | Upload quarantine, fail-closed malware scan | `File` | file_revisions; scan_results | status CHECK/current-safe trigger | activation requires PASS set | file scan worker | security event | `T-FILE-01` |
| `FILE-002` | Macro Office forbidden + parser resource limits | `File` | file revision metadata | — | allowlist/size checks | isolated parser job | security event on suspicious | `T-FILE-02` |
| `FILE-003` | Physical dedup SHA-256 | `File` | file_blobs; file_revisions | UNIQUE sha256 | hash verify + insert/select | cleanup | — | `T-FILE-03` |
| `FILE-004` | Replacement only after safe; old recoverable ~30d | `File` | file_assets; file_revisions | current-safe trigger | atomic current swap | cleanup | audit | `T-FILE-04` |
| `FILE-005` | Authorized app route only | `File` | lesson/question resource links | FK | object permission check | — | security event on denied abuse | `T-FILE-05` |
| `IMPORT-001` | Import draft + ambiguous review | `Import` | document_import_jobs; import_questions | status/confidence checks | promotion only after review | import worker | provenance | `T-IMP-01` |
| `IMPORT-002` | No answer key remains unknown; AI suggestion needs confirm | `Import` | import_questions | confirmation fields | approval check | AI request | provenance/audit | `T-IMP-02` |
| `IMPORT-003` | Duplicate only flag, never auto merge | `Import` | import_duplicate_candidates | candidate CHECK | Instructor decision | parser/similarity job | — | `T-IMP-03` |
| `AI-001` | Student RAG only published authorized content | `AI` | knowledge_documents; versions | status/FK | permission prefilter | index worker | source usage | `T-AI-01` |
| `AI-002` | Archived/deleted source stops retrieval immediately | `AI` | knowledge_documents; versions | status/current pointer | archive/delete invalidation transaction | vector invalidation | source/audit | `T-AI-02` |
| `AI-003` | Raw chat purge after 5 min inactivity | `AI` | ai_conversations; messages | expiry index | user message resets expiry | cleanup worker | security metadata separate | `T-AI-03` |
| `AI-004` | Minimum user data; Student only own progress | `AI` | ai_requests metadata only | — | tool/policy permission envelope | — | security events | `T-AI-04` |
| `AI-005` | Backend computes recommendation; Gemini only explains | `AI` | course/progress sources | — | recommendation service | — | AIRequest metadata | `T-AI-05` |
| `AI-006` | Answer records source version/revision | `AI` | ai_source_usages; knowledge_versions | FK | retrieval pipeline | — | metadata trace | `T-AI-06` |
| `NOTIF-001` | In-app read/unread + important email | `Notification` | notification events; notifications; deliveries | unique dedupe | event fan-out | email worker | — | `T-NOTIF-01` |
| `NOTIF-002` | Email failure no rollback, retry idempotently | `Notification` | email_deliveries | unique delivery | business commit creates outbox | email worker | — | `T-NOTIF-02` |
| `NOTIF-003` | Mandatory security email cannot disable | `Notification` | notification_preferences | CHECK | preference service | — | — | `T-NOTIF-03` |
| `AUDIT-001` | Important audit append-only | `Audit` | audit_events | append-only trigger | — | archive maintenance only | self | `T-AUDIT-01` |
| `AUDIT-002` | Required audit failure blocks sensitive mutation | `Audit` | audit_events + domain table | — | same SQL transaction | — | audit | `T-AUDIT-02` |
| `AUDIT-003` | Admin edit Instructor content needs reason + notify | `Audit` | audit; notification events | — | admin override service | email/notification | AuditEvent | `T-AUDIT-03` |
| `DELETE-001` | No broad historical cascade | `Retention` | FK graph | NO ACTION default | explicit delete service | cleanup | audit | `T-DEL-01` |
| `DELETE-002` | Used Assessment/Question historical tombstone | `Retention` | status/deleted fields/revisions | FK prevents breakage | trash/archive rules | cleanup | audit | `T-DEL-02` |
| `OPS-001` | Large list server pagination/filter/sort | `Performance` | indexes across domain | indexes | repository query contracts | — | — | `T-PERF-01` |
| `OPS-002` | Heavy analytics/progress are derived caches | `Performance` | analytics snapshots; enrollment cache | — | recompute/invalidate | analytics worker | — | `T-PERF-02` |
| `OPS-003` | Large jobs timeout/retry/idempotent | `Operations` | background_jobs | unique/dedupe/status | claim lease | worker | system alerts | `T-OPS-01` |
| `OPS-004` | Daily backup + restore drill, restore explicit Admin | `Operations` | backup_runs | status checks | restore authorization | backup job | audit | `T-OPS-02` |

## Traceability rule

A rule may require multiple enforcement layers. A blank SQL CHECK does not mean the rule is optional; it means the rule depends on transaction/authorization/worker context that ordinary relational constraints cannot safely express.


## System-spec chain
Each Rule ID should be read together with domain business file, API catalog, algorithm/workflow and test matrix. The DB traceability is preserved verbatim as the persistence/enforcement bridge.
