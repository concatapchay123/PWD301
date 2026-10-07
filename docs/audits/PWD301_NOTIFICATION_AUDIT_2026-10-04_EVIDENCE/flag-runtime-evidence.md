# Admin lesson flag — executed evidence, 2026-10-05

Scope: freshly recreated, owned SQL Server database `PWD301_AUDIT_GRADE_20261005_1B3A`, migration head `c4d5e6f7a8b0`, audit server port 5105. This is not evidence that the main database/runtime was migrated or repaired. No product code was changed for this reproduction.

## Browser action and outcome

Admin logged in through the visible form, opened the pending CS301 course review, expanded “Bài 1: Nguyên lý LLM & Vector Database”, and clicked “Gắn cờ vi phạm bài học”.

- Empty confirmation displayed `Nội dung bắt buộc tối thiểu 5 ký tự.` and kept the prompt open. SQL remained `lesson_flag=null, audits=0, events=0, notices=0`.
- Entering `Audit 2026-10-05: bổ sung nguồn trích dẫn cho nội dung LLM.` and confirming displayed the English error `An internal server error occurred. Please contact support.`. No success toast was observed.
- Browser network observation captured POST `/admin/courses/9c91eae7-cefa-45a1-9ecf-d022377b60ed/lessons/df0b0e0e-f362-472b-8683-7bbeb864febe/flag`, HTTP 500:

```json
{"error":{"code":"INTERNAL_ERROR","correlation_id":"354ef34d2fe84cb09c715af79abdb43c","field_errors":{},"message":"An internal server error occurred. Please contact support."}}
```

SQL after the valid Browser submission still returned `lesson_flag=null, audits=0, events=0, notices=0`. The owner is Instructor2. The pending course status remained `SUBMITTED_FOR_REVIEW`; the published lesson was not flagged durably.

## REST and SQL replay

Command: `.venv\Scripts\python.exe docs/audits/PWD301_NOTIFICATION_AUDIT_2026-10-04_EVIDENCE/grading-runtime-probe.py flag-probe`.

The script uses the exact disposable database boundary, ordinary demo JWT logins, HTTP calls and fresh SQL queries after every request. It does not drive or replace Browser actions. Tokens/passwords are not printed. Output: **10 cases, 6 matching expected status, 4 failed expectations, 0 skipped; exit 1**. This is an intentionally failing audit reproduction, not a green test run and not part of the 1579 pytest total.

| Case | Actor / input | Expected | Actual code / message | Durable result |
|---|---|---|---|---|
| guest_denied | No token, valid reason | 401 | 401 UNAUTHORIZED / `Missing Authorization header with Bearer token.` | Unchanged |
| instructor_denied | Instructor2, valid reason | 403 | 403 FORBIDDEN / `Access denied: insufficient role permissions.` | Unchanged |
| student_denied | Student4, valid reason | 403 | 403 FORBIDDEN / same English permission message | Unchanged |
| empty_reason | Admin, empty reason | 400 | 400 VALIDATION_ERROR / `Lý do gắn cờ bắt buộc tối thiểu 5 ký tự.` | Unchanged |
| four_character_reason | Admin, `abcd` | 400 | 400 VALIDATION_ERROR / same Vietnamese validation message | Unchanged |
| missing_lesson | Admin, nonexistent public lesson UUID | 404 | 404 RESOURCE_NOT_FOUND / `Bài học không tồn tại trong khóa học này.` | Unchanged |
| five_character_reason | Admin, exact reason `abcde` | 200 | 500 INTERNAL_ERROR / English system error | Unchanged |
| json_string | Admin, JSON `"invalid"` | 400 | 500 INTERNAL_ERROR / English system error | Unchanged |
| json_nonempty_list | Admin, JSON `["invalid"]` | 400 | 500 INTERNAL_ERROR / English system error | Unchanged |
| valid_reason | Admin, valid object/reason | 200 | 500 INTERNAL_ERROR / English system error | Unchanged |

After all nine requests the fresh SQL snapshot was:

```json
{"phase":"after_valid_reason","database":"PWD301_AUDIT_GRADE_20261005_1B3A","course_id":"9c91eae7-cefa-45a1-9ecf-d022377b60ed","lesson_id":"df0b0e0e-f362-472b-8683-7bbeb864febe","lesson_flag":null,"audits":0,"events":0,"notices":0}
```

REST failure correlation IDs: exact five-character reason `d511260d59a44a2d955a1b97987a2800`; JSON string `2aa6d6f7c7df48a48dbccb7b2ed5e066`; list `39b195020b2f4b8785b93f8aedddbc6f`; valid object `de63462dc889403dad51ed399e07a106`.

## Admin sub-role continuation

Four synthetic Admin sub-role identities were created only in the disposable database through the existing role-assignment service. Browser login, notification-center detail, mark-as-read state and CTA were exercised for each identity; SQL showed one `USER_ROLE_ASSIGNED` audit and one durable `ROLE_CHANGED` notice per identity. The CTA destinations matched the assigned scopes: `courses`, `applications`, `reassign` and `operations` respectively. A fresh REST list for each identity returned HTTP 200, one own item, `unread_count=0` and `is_read=true` after the Browser action.

The course-review sub-admin then reached the lesson-flag prompt in Browser; the exact five-character reason `abcde` reproduced HTTP 500 and no durable flag/audit/event/notice. The other three sub-admins received HTTP 403 from the same REST flag endpoint, with no moderation-state mutation. The sub-admin probe reported **8 checks, 1 failed expectation, 0 skipped; exit 1**: four notification-list checks passed, three scope-denial checks passed, and the one allowed course-review flag failed because of RCA-040.

## Earlier cleanup verification

The owned audit server on port 5105 was stopped. The exact cleanup command dropped only `PWD301_AUDIT_GRADE_20261005_1B3A` and returned `audit_database_remaining: 0`; a separate listener check returned `port5105_listeners=0`. Main runtime/database data was not removed.

## Post-fix SQL Server and Browser continuation — 2026-10-05

The two flag routes were changed to use the existing `record_audit_event` contract, reject non-object JSON before field access, and commit lesson state, audit and owner notification as one transaction. The focused TDD regression then reported **6 passed, 0 failed, 0 skipped**.

On a freshly recreated SQL Server fixture, the REST probe was rerun with the same ten cases. Result: **10 matching expected statuses, 0 failed expectations, 0 skipped; exit 0**. Guest/Instructor/Student, empty/4-character/missing-lesson and string/list boundaries remained safe; the valid long reason and exact `abcde` both returned 200. SQL after the valid calls contained the expected flagged lesson, audit rows, `COURSE_CONTENT_FLAGGED` events and owner notices.

Before that clean REST replay, the visible Browser flow was executed on a disposable fixture: Admin opened CS301 review, expanded the published lesson, entered exact `abcde`, and observed the success toast `Đã gắn cờ vi phạm bài học ... và gửi thông báo tới giảng viên.` SQL immediately after returned `lesson_flag=[FLAGGED]: abcde`, `audits=1`, `events=1`, `notices=1`. The Browser fixture was later dropped by the exact cleanup command.

The post-fix sub-admin replay reported **8 checks, 0 failed expectations, 0 skipped**: four own `ROLE_CHANGED` list checks, one authorized course-review flag (200), and three unrelated-scope denials (403) with no moderation mutation. A fresh REST-only fixture correctly shows those new notices unread; the earlier Browser continuation separately proved detail, mark-as-read and scoped CTA behavior.

The post-fix fixture remains owned and disposable until the final cleanup checkpoint below; no main database/runtime data was used.

## Final post-fix cleanup checkpoint

After the full current verification split, the audit server was stopped, the Browser fixture tab was closed, and exact cleanup returned `{"database":"PWD301_AUDIT_GRADE_20261005_1B3A","audit_database_remaining":0}`. The SQL-gated migration/race databases also each reported remaining `0`; the main SQL Server database was not dropped.

## Proven causes and limits

- Valid object: server trace identifies `AuditEvent(...)` in web handler `admin/routes.py:2393` and REST handler `api_admin/routes.py:1281`; SQLAlchemy raises `'payload_json' is an invalid keyword argument for AuditEvent`. Both paths fail before audit insert/commit, not because SQL Server permission is denied.
- Wrong JSON types: REST trace identifies `.get(...)` at `api_admin/routes.py:1272`; exceptions are `'str' object has no attribute 'get'` and `'list' object has no attribute 'get'`.
- Canonical audit model/dictionary uses required `actor_roles_snapshot` and `before_json` / `after_json`, not `payload_json`. Existing `record_audit_event()` captures/redacts this metadata and fails closed. Renaming only one argument without supplying required actor metadata is not a complete correction.
- Source also commits the lesson/audit before notification dispatch, suppresses all dispatch exceptions and does not show a later commit. This is a transaction/delivery risk requiring a separate successful-path regression. The current 500 cannot prove post-commit notification loss because it never reaches that path.
- REST has both Admin role and `COURSE_REVIEW` permission decorators. The three denied requests prove only the sampled Guest/Instructor/Student boundaries; no Sub-Admin permission matrix or cross-course mismatch was executed.
- UI default toast duration is 3500 ms in source. Actual elapsed duration, mobile layout and screen-reader announcement were not measured here. No duplicate appeared in the sampled Browser action; rapid-submit/idempotency remains untested.

Harness history: the first run failed to import a wrongly guessed `models.learning` module. It was corrected to the existing `models.course.Lesson` before the nine requests. This is a probe setup error, not a product defect. Ruff check then passed. No tests were disabled or reclassified as skipped.
