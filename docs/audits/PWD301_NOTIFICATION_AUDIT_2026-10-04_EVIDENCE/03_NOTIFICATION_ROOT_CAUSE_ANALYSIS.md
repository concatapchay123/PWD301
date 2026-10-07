# 03_NOTIFICATION_ROOT_CAUSE_ANALYSIS

## RCA-040 — authorized lesson flag fails before audit persistence

- Issue / severity: **P1**, valid Admin moderation cannot complete on both web-session and JWT surfaces; Browser displays a generic English system error instead of the requested outcome.
- Evidence: [flag-runtime-evidence.md](flag-runtime-evidence.md), N-126; real Browser web POST 500 and real REST POST 500 on freshly seeded SQL Server. SQL before/after remains no flag, 0 CONTENT_FLAGGED audits, 0 COURSE_CONTENT_FLAGGED events/notifications.
- Frontend flow: AdminView.renderCourseReviewPage binds `.btn-flag-lesson-action` → UI.prompt(minLength 5) → ApiClient.flagLessonContent POST → rejected ApiClient.request → page catch forwards err.message to UI.showToast. The success branch was not observed and must not be claimed.
- Backend flow / API: web flag_course_lesson validates COURSE_REVIEW and lesson/course relationship; REST api_flag_course_lesson has jwt_required, admin_required and require_admin_permission(COURSE_REVIEW). After setting a staged summary, both directly construct AuditEvent with invalid `payload_json`.
- Database / root cause: SQLAlchemy throws `'payload_json' is an invalid keyword argument for AuditEvent` before commit. Canonical audit_events has before_json/after_json and required actor_roles_snapshot; the route also omits that role snapshot. This is a route/model contract defect, not denied SQL Server authority.
- Impact: both duplicated handlers block moderation and owner-notification delivery. Guest/Instructor/Student rejection guards passed in the ten-case REST probe; exact five-character input now reproduces the same failure.
- Recommended fix / reuse: reuse record_audit_event(actor, after_state, session, commit=False) to capture roles/redaction/correlation and retain fail-closed persistence; review transaction ordering so durable notice matches any success claim. No audit schema copy/new payload column or weakened append-only rule is needed.
- Separate risk, not current proven loss: source commits before suppressed notification dispatch and shows no later commit. The current constructor failure prevents reaching dispatch; successful-path rollback/retry/durable-notice tests must establish this independently before treating it as a confirmed post-commit loss.
- Status: CONFIRMED FAIL, not repaired in this checkpoint. Full-suite pass does not cover this missing business case.

## RCA-027 continuation — wrong JSON-type failure remains on lesson-flag routes

N-127/N-128 REST probes sent a string and nonempty list. Both returned 500 INTERNAL_ERROR instead of 400; server trace identifies `payload.get` at api_admin/routes.py:1272 and str/list AttributeError. Fresh SQL remained unchanged after each request. This is the same structural missing object-type guard previously repaired for notification mutations, not a recurrence on those already-fixed endpoints. The web handler has equivalent source logic, but malformed web-session bodies were not replayed. Reuse existing payload validation conventions, test both surfaces and retain CSRF/JWT/COURSE_REVIEW enforcement. Priority P1; F-025 is proposed, not implemented.

## RCA-041 — sub-admin notification and permission-scope continuation

The four assigned sub-admin fixtures produced one durable `ROLE_CHANGED` notice each, with a single role-assignment audit and role-specific Browser CTA. Browser detail/mark-as-read/CTA behavior passed for course review, instructor review, teaching assignment and system monitoring. REST list replay returned one own read item for each identity. The three disallowed sub-roles returned 403 without moderation-state mutation. The allowed course-review sub-role reached the same exact-five-character 500 as RCA-040. This is a scoped authorization/notification pass with one dependent moderation failure, not proof of all Admin producers or duplicate behavior; rapid repeat and outbound delivery remain open.

## Post-fix resolution — RCA-040 / RCA-027 / RCA-041 continuation

The duplicated web and REST routes now delegate to `course_service.flag_lesson_content`, which reuses `record_audit_event` for actor roles, correlation and redacted after-state, validates JSON object shape before field access, dispatches the owner notice with the canonical instructor course route, and commits the lesson/audit/notification transaction together. A notification failure is fail-closed: the targeted rollback regression confirmed no lesson flag, audit, event or notice remains.

Fresh SQL Server evidence resolved the previously failing paths: the ten-case flag probe returned 10/10 expected statuses with zero failures and zero skips; exact `abcde` returned 200; Browser exact-5 returned the success toast and SQL showed one flag/audit/event/notice. The fresh sub-admin probe returned 8/8 expected checks with zero failures and zero skips. Duplicate/retry idempotency and outbound email delivery remain separate open gates.

## Checkpoint kiểm thử không skip và an toàn môi trường (2026-10-05)

Checkpoint này có ưu tiên hơn các số liệu 1572/1578 và các trạng thái lịch sử bên dưới. Lượt chạy ban đầu có 1576 passed, 2 failed, 0 skipped; hai test upload tài nguyên và lease bài thi trả 503. Chạy riêng cho 2 passed; chạy lại toàn nhóm API trước sửa fixture cho 375 passed. Probe có restore marker trên thư mục audit riêng tái hiện đúng cả hai phản hồi MAINTENANCE_MODE_ACTIVE/503. Việc nhóm test dùng chung storage/quarantine/backups với workspace là lỗi cô lập đã được chứng minh; không quy kết chắc chắn nguyên nhân của lượt lỗi ban đầu khi chưa lưu response của lượt đó.

Fixture app nay dùng ba thư mục con riêng trong tmp_path. Regression mới thất bại với các root E:/PWD301/storage, quarantine, backups trước sửa. Sau sửa, probe vẫn giữ marker bên ngoài và 27 test upload/lease/backup/restore/maintenance đạt; không tắt maintenance hay fail-closed. Marker probe đã xóa. Test mới dùng nhầm một route không tồn tại lúc đầu; lỗi harness 404 đó đã sửa, không tính là lỗi sản phẩm.

Cô lập filesystem lộ thêm lỗi rescan: kiểm tra substring “infected” trên toàn đường dẫn nhầm thư mục cha với vùng chứa tệp nhiễm. Regression hiện hữu thất bại hai lần trước sửa; nay so sánh parent đã resolve với get_file_infected_root(), kiểm tra tệp được chuyển, key infected/hash và Student vẫn bị từ chối 403. Focused stress/file/isolation: 27 passed. Lượt split cuối sau sửa cho **1579 passed, 0 failed, 0 skipped**, khớp **1579 tests collected**: root298 + unit632 + API375 + security233 + concurrency13 + E2E12 + integration16. Frontend độc lập: **101 passed, 0 failed, 0 skipped**. Không cộng các lượt focused trùng vào tổng. Đây là kết quả các nhóm chạy đủ, không phải một aggregate verifier được tuyên bố pass; lượt aggregate lịch sử bị stall vẫn không được tính.

SQL-gated integration hiện tại: 16 passed, 0 failed, 0 skipped, gồm migration, ROWVERSION race và hai loại revision trên SQL Server thật. Hai DB migration/race tạm đã xóa, remaining=0. Browser Student4 đã đăng xuất về form login; server audit 5105 dừng; DB grading tạm cũng đã xóa, remaining=0. Không migrate/restart DB/runtime chính; fixture có thể dựng lại bằng prepare.

Audit notification vẫn PARTIAL, không phải release sign-off. Những đoạn dưới nói “chưa sửa”, “pending replay”, “1572 current” là snapshot lịch sử, không được dùng thay checkpoint mới.

## RCA-038 — shared test filesystem can produce unrelated maintenance feedback

- **Observed boundary:** two full-group tests initially returned 503; isolated replay returned 2 passed. A controlled marker in an audit-only storage root reproduced both responses as `MAINTENANCE_MODE_ACTIVE`, “Database restore is currently in progress”. No live restore was initiated by this probe.
- **Verified root:** `tests/conftest.py` isolated the database but inherited workspace storage/quarantine/backup roots. `DatabaseRestoreLock` writes `.restore_lock` to that shared storage root; other worker processes correctly see it and reject non-admin requests. The fixture-isolation regression failed against all three workspace paths.
- **Limit:** the exact original failing response bodies were not retained; cross-worker restore interference is a reproduced mechanism, not conclusive attribution of the original transient failures.
- **Correction:** use pytest `tmp_path` for all three roots in the shared app fixture. Do not disable maintenance, bypass the marker or weaken runtime authorization. API failure assertions now include their JSON body for future diagnostics.
- **Verification:** with the external marker still present, the two original tests, isolation regression and operations/backup/restore tests returned 27 passed, 0 skipped. The one initial 404 in the new test was a wrong test route and was corrected as harness error. P2 test reliability/environment safety; production maintenance policy unchanged.

## RCA-039 — rescan recognizes an infected directory by substring

- **Actual failure:** the existing real rescan regression returned HTTP 200 and persisted REJECTED/INFECTED, but the infected hash file did not exist. Its pytest temporary ancestor contains “infected”; the failure reproduced twice before any product edit.
- **Root:** `file_service.py:1458` tested `"infected" not in str(target_path)` rather than the configured directory identity. A filename or ancestor can therefore suppress relocation even when the file is outside the infected root.
- **Correction/reuse:** resolve and compare the file's parent with existing `get_file_infected_root()`. Preserve scanner verdict, hashing, atomic replacement, status and download authorization; no dependency or new abstraction.
- **Verification:** strengthened regression checks destination bytes exist, old quarantine path is gone and revision key is `infected/<sha256>`; Student download remains 403. Focused stress/file/isolation returned 27 passed. P1 physical quarantine-placement defect fixed; no claim that infected content was previously downloadable, and Browser rescan notification remains unverified.

## RCA-034 — migration CHECK rejects supported question correction types

- **Evidence/API boundary:** on the actual migrated SQL Server fixture, create_question_revision with ANSWER_CHANGE failed with SQL error547 at ck_question_revisions_4. This was a service reproduction, not an observed Browser/API error response.
- **Root cause:** migration0001 permits only INITIAL/EDIT/ANSWER_ONLY/CONTENT_OR_CHOICES; model and canonical reference DDL additionally allow TYPO_FIX/ANSWER_CHANGE/CONTENT_CHANGE/REVOCATION. SQLite model-created tests therefore passed a path that migrated SQL Server rejected.
- **Impact/severity:** P1: answer correction cannot persist, so the score-change notification chain cannot begin.
- **Correction:** new migration c4d5e6f7a8b0 widens only the CHECK and keeps all historical rows. The canonical dictionary was reconciled to the already-existing model/DDL values. Downgrade refuses a lossy restriction when expanded values exist.
- **Verification:** migration parity assertion failed before the fix; SQLite and real SQL Server upgrade/downgrade/upgrade now pass. Main runtime/database was not migrated.

## RCA-035 — revision activation happens before immutable children are written

- **Evidence:** after CHECK repair, SQL Server rejected new-choice INSERT with trigger51007. Two deterministic SQLite regressions mirrored the canonical activated-child guard and failed for SC choices and SHORT_ANSWER accepted answers.
- **Root cause:** create_question_revision persisted is_current=true before inserting/cloning children. For a used question, canonical triggers prohibit INSERT/UPDATE/DELETE of children of an activated revision.
- **Flow:** correction payload → authorized question service → new revision → child INSERT → trigger failure → rollback; no success/notification is justified.
- **Correction:** construct the new revision inactive, flush children/resources, then activate in the existing transaction. No trigger, historical content or permission check is removed.
- **Verification/status:** two RED/GREEN regressions and two real SQL Server cases pass. Original-child edits still fail51007/51008; old content remains unchanged. P1 resolved in current source, not deployed to the main runtime.

## RCA-036 — regrade worker bypasses the grading notification producer

- **Evidence:** real regrade returned COMPLETED, score18→28 and durable REGRADE history, but zero new grading notices. The strengthened two-student worker regression failed with0 SCORE_CHANGED_AFTER_REGRADE rows instead of2.
- **Root cause:** both worker aggregation paths independently mutate AssessmentResult/history and never call the dispatch logic in calculate_attempt_result. Fixing the initial/manual producer alone cannot cover worker execution.
- **Correction/ownership:** one notify_assessment_result_change helper owns first-release/change-only copy and the canonical attempt CTA; normal aggregation, job items and direct regrade call it. Hidden/unreleased results return before dispatch; unchanged released scores return without a duplicate notice.
- **Verification:** latest SQL/HTTP job persists exactly one change notice for Student4; duplicate trigger preserves the job and history. Browser renders18→28/30 and the CTA opens28/30. Shared code retains the existing savepoint/warning failure policy; guaranteed email/notification recovery is not claimed.
- **Severity/status:** P1 resolved for current source and sampled SQL/Browser flows; broader publication policies/retry breadth remain independently gated.

## RCA-037 — result detail mislabels a policy-hidden essay answer

- **Evidence:** Student4 followed both fresh grading CTAs. At 18/30 and 28/30, the total matched SQL and the ESSAY grade was 18/20. The assessment used `answer_visibility_policy=AFTER_CLOSE`, so the backend correctly omitted `student_answer_text` before `close_at`; the frontend nevertheless rendered the fallback “Không trả lời”, which falsely implied that the student had submitted no answer.
- **Root cause:** `get_attempt_result_for_student()` intentionally withholds answer text, explanations, selected choices and feedback while the answer policy is closed. The result renderer had no distinction between an omitted answer because it was hidden and an empty answer that was visible.
- **Correction:** keep the backend fail-closed policy and add a policy-aware frontend fallback. For `NEVER`, `AFTER_CLOSE` and `AFTER_ALL_ATTEMPTS`, an ESSAY with no answer field now renders `Câu trả lời đang được ẩn theo chính sách khảo thí`; a genuinely visible empty answer still renders “Không trả lời”. No answer or choice is fabricated or leaked.
- **Verification:** TDD RED then GREEN in `tests/frontend/essay_grading_ui.test.js`; the answer-visibility security test and mixed manual-grading API test each passed. The full frontend suite now passes 107/107 with zero skips. A post-fix Browser replay could not be completed because the CUA Browser binding returned no available browsers; the SQL fixture was nevertheless disposed with `audit_database_remaining=0`.
- **Status:** source/API/security boundary corrected; Browser post-fix visual acceptance remains open. The historical Browser failure remains preserved as pre-fix evidence, and the separate Instructor grading capability is covered by F-033/RCA-020.

## RCA-033 — manual grading releases a score without a notification

- **Confirmed chain:** disposable SQL Server/HTTP manual grade returned 200, committed GRADED/RELEASED 18/30 and MANUAL result history, but produced zero assessment/score notifications. Exact fixture and validation boundaries are recorded in report 07.
- **Root cause:** `calculate_attempt_result()` dispatched first-grade notices only for reason INITIAL, and changed-score notices only for REGRADE/CORRECTION. Essay finalization calls it with MANUAL, so both conditions were false.
- **Correction:** capture the previous result status. A transition into RELEASED emits ASSESSMENT_GRADED; subsequent changed released scores include MANUAL in SCORE_CHANGED_AFTER_REGRADE. Same-score re-evaluation emits no duplicate; hidden scores remain excluded by the outer RELEASED guard.
- **Current verification:** genuine missing-notification RED, then 143 focused grading/regrade/question/notification/API/security passes with zero skips. Fresh disposable SQL Server manual grade released 18/30 with one durable Student4 notice; an unchanged manual retry did not duplicate it. Browser opened the notice detail and its related-page CTA rendered the correct attempt result. No historical rows were repaired.

### Current fresh emitted-event replay (2026-10-06)

The disposable `PWD301_AUDIT_GRADE_20261005_1B3A` fixture was recreated and exercised in the correct order: manual grade, answer correction, regrade worker, duplicate regrade request, SQL status, then Browser replay. SQL/HTTP produced exactly two Student4 notifications for the attempt: `ASSESSMENT_GRADED` at 18/30 and `SCORE_CHANGED_AFTER_REGRADE` at 18→28/30. The regrade job was `COMPLETED`, the duplicate request returned the same job, and the overall grade history remained unchanged on retry; cleanup dropped the exact audit database with `audit_database_remaining=0`.

Student4 logged in through the real form on the disposable server, opened the notification center, saw both newly emitted Vietnamese notices, opened the regrade notice detail, and selected `Mở Trang Liên Quan`. The Browser landed on `#/student/assessments/results?id=e8ba2cd1-cd9c-4f56-93e5-709b45b8326f` and visibly rendered the released 28/30 result; logout returned to `/auth`. This closes the fresh emitted graded-result CTA replay for N-109/F-012. The separate ESSAY question-level rendering and broader producer/role/idempotency gates remain independently scoped.

## RCA-020 continuation — pending-essay gradebook has no grading action

- **Evidence:** actual Instructor2 Browser on the migrated disposable runtime listed CHỜ CHẤM and opened an ESSAY answer, but the only detail-modal button was close. No manual-grade/regrade action was available.
- **Source:** `InstructorView.openAttemptDetailModal()` renders answer comparison and appeal controls, not an essay grading form. Backend grading endpoints work with bounds, object authorization and ROWVERSION, so the missing Browser workflow is not an API authorization failure.
- **Impact:** Instructor cannot finish a pending essay through this screen; initial grading notification cannot be reached using ordinary UI actions. This remains an open frontend capability gate, not a skipped/passed test. API/SQL grading evidence cannot substitute for it.

## RCA-021 continuation — enrollment notification rows were not committed with the enrollment

- **Issue:** the enrollment service could return a successful ACTIVE enrollment while its newly staged `STUDENT_ENROLLED` event and `Notification` rows were not durable when the caller closed the session.
- **Red evidence:** a new regression called `enroll_student()` without an extra caller commit, removed the session, and then queried the notification/event join; it found `0` rows instead of the expected `2` recipient notifications.
- **Root cause:** the service committed the `Enrollment` first and dispatched notifications afterward. The dispatch used the same session but no subsequent service commit persisted the staged event/notification rows.
- **Fix:** dispatch the owner and student notifications before the service's final commit, so the enrollment, event and recipient rows are committed together. The broad dispatch exception boundary remains a separate resilience risk and is not claimed fixed here.
- **Current evidence:** `tests/unit/test_enrollment_service.py` reports `20 passed, 0 failed`; split pytest verification reports `1572 passed, 0 failed, 0 skipped`, including SQL Server migration and concurrency gates. A later aggregate attempt stalled at 49% and is not counted as a pass. Historical live OPS401 rows with events but no linked notifications remain a data-repair/replay gap.
- **Impact/status:** the source transaction-ordering defect is fixed and regression-verified; fresh live Student4 → DSA201 Browser/API/SQL Server correlation now passes for both recipients. Historical OPS401 orphan rows still require a repair/replay decision before release acceptance.

## Current live correction — course approval notification correlation (2026-10-05)

The historical Admin-primary authorization failure is no longer the current live state. A real Instructor1 Browser session submitted CS201, a real Admin session displayed the pending queue with one course and approved it, and the owner Instructor session then displayed the fresh `COURSE_APPROVED` notification. SQL Server confirmed CS201 `status=APPROVED`, `approved_by_user_id=1`, one `COURSE_APPROVED` event for the course payload and one linked notification to `instructor1@pwd301.local`. This closes the live approval/owner-notification correlation for the approve branch.

## Current live correction — course-change rejection owner notification (2026-10-05)

Instructor1 submitted staged CS201 course changes as request `60002`. Admin used the real review page and completed rejection with a non-empty reason. SQL Server showed `REJECTED`, reviewer user `1`, the exact reason and event `140009` (`COURSE_CHANGE_REJECTED`) targeted to owner user `2`; notification `150082` linked to that event and recipient `instructor1@pwd301.local`. The owner Browser session rendered the matching rejection title/body. This closes the live request-edit/reject notification correlation; it does not imply that every lesson/resource producer or retry path is correct.

## Current live correction — enrollment event/recipient persistence (2026-10-05)

The source transaction-ordering fix was exercised in the live runtime, not only in a unit fixture. Student4 enrolled in DSA201 through Browser and the course became ACTIVE. SQL Server then showed two fresh `STUDENT_ENROLLED` events (`140010`, `140011`) and two linked notifications (`150083` to Instructor2 and `150084` to Student4); both payloads used the expected role-specific SPA routes. The owner Browser also displayed the new-student notice. This closes the fresh live enrollment correlation while preserving the historical OPS401 orphan-notification finding as a separate data-repair issue.

## RCA-032 — course-change rejection notification exposed an internal course ID (resolved)

- **Issue:** the pre-fix rejection notification showed `#70014` and used `#/instructor/courses/manage?id=70014` instead of the course public UUID, although the CTA happened to resolve successfully.
- **Evidence:** Browser request `#60003` showed `Đợt cập nhật khóa học #70014 cần chỉnh sửa lại`; SQL Server event `140014` contained `course_id: "70014"` and the numeric action URL. Direct SQL Server course inspection showed internal `courses.id=70014` and public UUID `06a1a28d-667a-4d31-b5c9-edefc2885d91`. Browser CTA navigation opened CS201, so this was a leakage/contract defect rather than a route-not-found defect.
- **Root cause:** the changeset-specific rejection branch in `src/pwd301/blueprints/admin/routes.py:2337-2346` formats `target_req.course_id` directly. The neighboring `lesson_service.py` rejection producer uses `req.course.public_id`, proving that the producer family is inconsistent.
- **Impact:** P1 privacy/UX/contract defect; users see an internal database identifier and notification consumers receive a non-canonical action URL. The route resolver's permissiveness masks the defect.
- **Resolution:** `src/pwd301/blueprints/admin/routes.py` now resolves the related Course, uses `course.course_code` for the user-facing title, and emits `course.public_id` in the audit payload, notification action URL and event payload. The new regression `test_dedicated_reject_changeset_uses_public_course_identity` first failed against the old producer, then passed after the fix; the full changeset suite reports **12 passed**. Live request `#60004` produced Browser title `Đợt cập nhật khóa học CS201 cần chỉnh sửa lại`, public-UUID CTA navigation, SQL event `140017` and notification `150090`. **Status: RESOLVED CURRENT SOURCE; historical `70014` rows retained as evidence.**

## Current-worktree retest (2026-10-04)

The dirty worktree contains user remediation for the historical dismiss contract. Post-fix verification returned `28 passed, 0 failed` for notification unit/API/IDOR and `53 passed, 0 failed` for seed/auth/notification. Standard Browser login passed for three representative roles and HTTP login passed all seven demo accounts. After the RCA-031 auth correction, all three visible quick-demo selectors also reached their intended role routes in clean sessions. No product commit or release claim is made; complete dismiss-client Browser/API/DB coverage remains open.

## Phân loại nguyên nhân

### RCA-001 — dismiss contract regression

- Evidence: `src/pwd301/services/notification_service.py:456-491` returns `{"status": "deleted"}`.
- Direct verification: `tests/unit/test_notification_service.py:276` and `tests/api/test_notification_api.py:160` require `dismissed`; the targeted suite produced 26 passed, 2 failed, both dismiss failures. A fresh direct two-test rerun on 2026-10-04 reproduced both failures in 1.24s.
- Root cause: dirty implementation changed the public status string without changing the existing tests/spec contract. Canonical DB uses expiry for cleanup; this does not authorize renaming the API status.
- Impact: client code and API consumers cannot rely on the established action result.
- Severity: P1 contract regression.
- Fix direction: restore `dismissed` as the public status, retain expiry semantics only if that is the canonical persistence behavior, then rerun focused API/unit tests.
- Product code changed by this audit: no.

### RCA-002 — response envelope fragmentation

- Evidence: `api_notifications/routes.py:64-76` emits a list as top-level `success/items/total/...`; `:99` returns the read service result directly; `:136` returns the dismiss result directly; and `:139-145` returns preferences as `{preferences}`. The web route `auth/routes.py:809-822` adds `preferences` into the list response, while `:829-830` deliberately returns unauthenticated unread count as HTTP 200/0. Frontend `api.js:1127-1137` tries three route families and finally fabricates an empty list when all fail. `src/pwd301/__init__.py:200` has a global error formatter centered on `error`.
- Direct runtime evidence: REST unauthenticated list/count/preferences/mark-all returned HTTP 401 with an `error` object but no `success: false` or `data: null`; authenticated list returned 200 without `data`, preferences returned a different top-level shape, and invalid read/dismiss/delete returned structured 404. The separate web-session boundary is inconsistent: `/auth/notifications` returned 401 while `/auth/notifications/unread-count` returned 200 with zero.
- Root cause: notification API and web-auth routes evolved independently without one response serializer; the frontend fallback chain then hides route/transport failure as an empty notification state.
- Impact: frontend needs branch-specific parsing; monitoring and clients cannot distinguish payload absence from failure consistently.
- Severity: P1 contract/API consistency.
- Fix direction: define one envelope `{success, data, error}`; keep stable `code`, `message`, `field_errors`, `correlation_id`; migrate one endpoint family at a time with compatibility tests.

### RCA-003 — raw/technical error propagation to user UI

- Evidence: `frontend/assets/js/api.js:98-100` builds `Error` from backend message; static search found 108 direct message propagation sites. Examples include `router.js:989`, `student.js:1077`, `instructor-exams.js:1171`, `student.js:5058`.
- Root cause: UI receives text instead of stable error code and maps it locally, while views concatenate raw exception messages.
- Impact: mixed Vietnamese/English, technical/internal leakage, inconsistent copy and no single localization owner.
- Severity: P1 UX/security hygiene.
- Fix direction: expose code/category/user-safe fallback only; catalog copy by code; log technical detail server-side with correlation ID.

### RCA-004 — no centralized notification message catalog

- Evidence: `dispatch_notification` accepts arbitrary title/body; 37 producers use event names but no required message key or versioned template. `UI.showToast` accepts arbitrary text and duration.
- Root cause: notification creation was coupled to each business branch.
- Impact: same event family has multiple wording, language, category and action semantics; changes require searching many files.
- Severity: P1 maintainability and UX correctness.
- Fix direction: event registry with code, category, audience, title/body keys, action policy, severity, retention and email policy. Producers pass structured facts, not final prose.

### RCA-005 — heuristic duplicate hiding instead of business idempotency

- Evidence: `_visible_notification_query` hides newer records by recipient/title/body/target role. Database uniqueness is event+recipient, while `emit_event` creates a random event when no stable key is supplied.
- Root cause: dedupe was implemented at presentation query level instead of at business event boundary.
- Impact: legitimate repeated events with equal copy can disappear; retries with slightly changed text can duplicate.
- Severity: P1 data/user-trust risk.
- Fix direction: require a stable idempotency key derived from business action and recipient; keep query filtering for expiry only unless catalog explicitly defines coalescing.

### RCA-006 — frontend notification background failures are silent

- Evidence: `router.js:1674-1720` catches notification fetch errors and warns only. The frontend suite logged `ApiClient.getNotifications is not a function` because its router sandbox supplied `ApiClient: {}` even though production `api.js:1117` defines the method. Separately, a read-only Node VM probe of current production `api.js` forced `/auth/notifications`, `/student/notifications` and `/api/notifications` to reject; `ApiClient.getNotifications()` returned `{items:[],total:0,unread_count:0}`.
- Root cause: the production notification refresh path treats failure as non-blocking and converts total transport failure into a valid-looking empty payload; independently, the router test mock contract is incomplete.
- Impact: user can miss notifications without visible degraded state; green suite masks the runtime path.
- Severity: P1 observability/UX.
- Fix direction: make the mock/API contract explicit, stop converting transport failure into a valid empty payload, add a visible non-blocking degraded state, and test cold load, refresh, role switch and retry.

### RCA-007 — serializer exposes a non-canonical deleted field

- Evidence: `Notification.to_dict()` includes `deleted_at: None`; canonical notification SQL and data dictionary define `read_at` and `expires_at`, not `deleted_at`.
- Root cause: prior dismissal model and current expiry model were combined at serialization boundary.
- Impact: clients may build an unsupported deletion state; contract ambiguity remains even after persistence field removal.
- Severity: P2 contract drift.
- Fix direction: decide from canonical spec whether dismissal is represented by expiry/read state; remove unsupported output only with an explicit compatibility decision and tests.

### RCA-008 — browser acceptance gate not executed

- Evidence: local browser page was reachable and demo accounts were visible; login was not submitted because creating a session requires confirmation immediately before the action. No role flow, mutation, upload, download, popup or refresh behavior was therefore observed.
- Root cause: authorization/confirmation gate, not an application defect.
- Impact: final audit cannot claim end-to-end acceptance.
- Severity: release blocker for this audit only.
- Fix direction: obtain direct confirmation, run the role matrix in an isolated local session, capture exact UI/API/result evidence, then update reports.

### RCA-009 — demo label and default role view are ambiguous

- Evidence: clicking the visible Student demo account logged in `student1@pwd301.local` but routed to `#/instructor/dashboard` with topbar `GIẢNG VIÊN`. The role menu showed both Học viên and Giảng viên; switching to Học viên then routed correctly to `#/student/dashboard`. The current live JWT role probe reports `STUDENT,INSTRUCTOR` for this account.
- Root cause: `frontend/assets/js/views/auth.js:225-237` labels the demo button `Học viên (Student)` but only fills credentials; it does not submit a requested role or `next` target. The backend login path sets `session["active_role"] = user.primary_role` and chooses landing from it (`auth/routes.py:218-229`). `User.primary_role` intentionally ranks `ADMIN > INSTRUCTOR > STUDENT` (`models/identity.py:166-175`), so a live account with both STUDENT and INSTRUCTOR deterministically lands in Instructor. The router then consumes `active_role/primary_role` (`router.js:135-145`, `394-406`).
- Impact: a user following the Student demo path sees an apparently wrong role and may trigger the wrong notification scope.
- Severity: P2 UX/acceptance ambiguity.
- Fix direction: either label the demo as multi-role with explicit default, or make the selected demo role the authoritative post-login view.

### RCA-010 — logout depends on reload to remove stale protected view

- Evidence: after Admin logout the topbar disappeared, but the current hash remained `#/admin/governance` and the Admin content/error view remained in the DOM. A fresh Student/Instructor-session probe confirmed that Back returned to stale `#/instructor/dashboard` but rendered only the login screen with no private content; the URL/history was still wrong. A fresh Instructor2 Browser probe found a stronger variant: while the DSA201 `Cài đặt & Học vụ` modal was open, logout rendered the login form behind the still-visible modal, exposing course title, SLO text and a prerequisite request after authentication had ended.
- Root cause: `frontend/assets/js/api.js:150-168` clears client state and assigns `window.location.hash = '#/auth'`, which creates a new history entry instead of replacing the protected entry. `frontend/assets/js/router.js:995-1015` clears the shell/cache and renders auth but never calls `history.replaceState` or removes the prior protected hash.
- Impact: stale protected presentation can remain until reload in the earlier Admin path, and an open global modal can continue exposing protected course data on the login screen. Back can also revisit a protected hash even when the current DOM is correctly unauthenticated; browser history/hash is misleading.
- Severity: P1 session UX/security presentation.
- Fix direction: close every global modal/drawer and clear their stack before clearing auth state; clear the protected viewport and use `history.replaceState`/router root on logout, then verify back/refresh cannot expose private data.

### RCA-011 — runtime duplicate notification copy is visible to users

- Evidence: Instructor center showed two near-identical MIDTERM grading notices for the same student; Admin center showed two near-identical CS301 course approval requests. Student data also contained multiple similar grade-result messages.
- Root cause: multiple producers/event variants and/or presentation dedupe do not share a stable business idempotency key; source inventory already shows overlapping route/service producers.
- Impact: users may perform the same review twice or lose trust in notification count.
- Severity: P1 business workflow clarity.
- Fix direction: trace each pair to request/event keys, collapse only true retries, and preserve intentional distinct outcomes with explicit titles/actions.

### RCA-012 — security notification exposes IP-like telemetry in UI

- Evidence: Admin notification center displayed `Cảnh báo bảo mật: Phiên đăng nhập mới ... (192.168.1.105)`.
- Root cause: the displayed value is present verbatim in the demo notification configuration at `src/pwd301/seeds/demo.py:1224-1240` (`SYSTEM_SECURITY_ALERT` body). The live Browser/SQL capture proves that this seed/runtime payload reaches the UI; it does not yet prove that the current login request path produces the value. The producer of a newly generated security-login event remains unisolated.
- Impact: violates the project guardrail against exposing infrastructure/network details unless explicitly justified; may expose sensitive telemetry to a broad admin audience.
- Severity: P1 security/privacy review.
- Fix direction: classify the value and audience; show a safe masked/location summary in UI and retain exact telemetry only in authorized audit detail.

### RCA-013 — RBAC errors are technically safe but not user-safe and are retried noisily

- Evidence: Admin governance visibly rendered `Only the primary administrator can access the user and role matrix.`; console showed repeated warnings for `/admin/users`, `/admin/courses/pending`, `/admin/instructor-applications` and `/admin/change-requests`.
- Root cause: `src/pwd301/blueprints/admin/routes.py:230-236` and `:288-294` construct the English `ForbiddenError` message, while `frontend/assets/js/api.js:98-108` converts the backend message directly into `Error.message` and logs every failed request. Background loaders then request forbidden Admin resources without a capability map and repeat the same failures.
- Impact: mixed-language technical copy, console noise, wasted requests, and a page that appears degraded even when access denial is expected for that admin subtype.
- Severity: P1 UX/observability; authorization itself was enforced.
- Fix direction: map capabilities before requesting, render a Vietnamese permission state, and suppress repeated retries for stable 403 responses.

### RCA-014 — authenticated web notification payload is structurally and semantically inconsistent

- Evidence: browser CDP captured Student, Instructor and Admin routes with HTTP 200 and the same non-envelope shape; `preferences` is mixed into the list response; items include `deleted_at: null`; Student maps `COURSE_ANNOUNCEMENT` to `ASSESSMENT`.
- Root cause: web-auth and REST notification routes serialize their own payloads (`auth/routes.py:809-822` versus `api_notifications/routes.py:64-76`), preferences are coupled to the web list but split into a separate REST endpoint, and frontend role/dedup presentation logic (`router.js:1142-1161`) performs another semantic transformation after transport.
- Impact: clients cannot use one parser; filtering, analytics, retention and copy ownership can disagree about the same notification.
- Severity: P1 API/business contract.
- Fix direction: define a shared serializer and event registry, reject or migrate invalid event/category combinations, and add response-contract fixtures from real seeded rows.

### RCA-015 — same business fact is emitted as different event identities by role

- Evidence: Instructor API contains two MIDTERM notices with near-identical body; one is `ASSESSMENT_SUBMITTED` with `#/instructor/grading`, the other is `COURSE_ANNOUNCEMENT` with no action URL. Admin API contains two CS301 approval notices; one is `COURSE_APPROVAL_REQUEST` with `#/admin/courses`, the other is `COURSE_ANNOUNCEMENT` with no action URL.
- Root cause: legacy/general announcement producers coexist with domain-specific producers and presentation dedupe does not reconcile them by business key.
- Impact: duplicate count, inconsistent CTA, and possible double work for Instructor/Admin.
- Severity: P1 business workflow.
- Fix direction: trace each pair to producer and event key, retain only the domain-specific event, and add a database-level/idempotent test for the business action.

### RCA-016 — review submission is not visible in the Admin queue during the same live runtime

- Evidence: Instructor-side confirmation changed course `AUDIT1004` to `Chờ duyệt` and froze editing. After login as `admin@pwd301.local`, the course-review queue showed `0 Khóa học chờ duyệt` with no approve/reject control.
- Root cause: the live Admin authorization boundary is confirmed in RCA-018. A corrected disposable runtime seeded from current source showed the same business fixture in the Admin queue, then passed Browser approval and request-edit/reject with DB post-conditions, which narrows the defect to live role-link/provisioning drift rather than the queue UI alone.
- Impact: approval/rejection and the corresponding notification cannot be accepted on live `PWD301`; sender success may be misleading. The disposable result is a scoped environment retest, not release evidence.
- Severity: P1 business workflow / P1 notification correlation.
- Fix direction: repair/reseed the live role metadata, capture request/response and DB identifiers across both sessions, then retain the disposable role-scoped queue test with one submitted course and explicit approve/reject post-conditions.

### RCA-017 — exam/proctoring result path changes state without notification correlation

- Evidence: Student start created an attempt, autosave returned visible `Đã lưu tự động`, fullscreen exit produced a violation overlay, and submit produced a 100/100 result. No matching notification event, API correlation ID, or SQL row was captured for these transitions.
- Root cause: not established; the audit currently observes presentation and business-result surfaces separately.
- Impact: a green result page is insufficient proof that audit/notification ownership, idempotent submit, and proctoring records agree.
- Severity: P1 evidence gap.
- Fix direction: capture the attempt/submit/notification requests and SQL identifiers, then replay duplicate submit and stale-session cases.

### RCA-018 — demo Admin seed identity and live authorization behavior diverge

- Historical pre-fix evidence: `src/pwd301/seeds/demo.py` created the Admin role link with `SUB_ROLE:ADMIN_PRIMARY | Demo environment initialization`, but two live `admin@pwd301.local` sessions displayed the primary-admin-only denial. An authenticated HTTP session returned `admin_sub_role` empty and `is_primary_admin:false` from `GET /auth/login`, while `GET /admin/courses/pending` returned HTTP 403. A direct read-only SQL Server query found the old live `ADMIN` role link assignment reason was `Baseline root administrator initialization`, with no `SUB_ROLE:ADMIN_PRIMARY` token. The current live recheck now returns `admin_sub_role=ADMIN_PRIMARY`, `is_primary_admin=true` and HTTP 200 for the Admin endpoints.
- Root cause: confirmed persisted seed/provisioning drift — the runtime database contains a baseline Admin role link without the sub-role metadata required by `User.admin_sub_role`, while the current demo seed source expects `ADMIN_PRIMARY`.
- Impact: the approval failure is an authorization defect in the current runtime, not evidence that there are zero pending courses. Notification ownership and approve/reject acceptance remain unproven.
- Severity: P1 confirmed environment/authorization defect.
- Fix direction: repair or re-seed the live/deployment runtime role-link metadata, verify `/auth/login` identity fields and `/admin/courses/pending` status there, then add a seed idempotence/regression test before changing product code. The disposable retest is already complete and was removed after capture.
- Disposable retest: current source seed produced `SUB_ROLE:ADMIN_PRIMARY`; Browser identity showed `ADMIN CHÍNH`, pending queue count 1, approval persisted `APPROVED`, and request-edit/reject after fixture reset persisted `DRAFT`. This closes the disposable retest gate only; the live database still has the drift.

### RCA-019 — double-click broadcast persists duplicate events while API/UI collapses them

- Evidence: one Admin-only browser double-click produced two identical success toasts. The authenticated list returned one matching visible item (`total=7`, `unread_count=4`), but a direct read-only SQL Server query against `PWD301` found two `notifications` rows, two distinct `notification_event_id` values and one recipient for the same title; the valid single broadcast had one row.
- Root cause: confirmed in the current source path. `admin/routes.py:591-618` accepts no idempotency key and directly invokes `broadcast_system_notification()`. `notification_service.py:647-653` calls `emit_event()` without an `event_key`, so each request receives a fresh random UUID (`emit_event():137-142`); `:662-671` then creates one row per recipient. The database uniqueness rule is only `(notification_event_id, recipient_user_id)` (`models/notification_audit.py:127-132`), so two rapid requests are two distinct business events and both persist. `_visible_notification_query()` (`notification_service.py:281-298`) suppresses newer same-title/body rows at read time, masking the duplicate in API/UI while leaving audit/DB rows duplicated.
- Impact: an operator can generate multiple in-app deliveries while seeing ambiguous/single feedback; audit counts and user-visible history diverge from stored data.
- Severity: P1 confirmed business-data/idempotency defect.
- Fix direction: add a server-owned idempotency key tied to the business action and recipient fan-out, reject/replay duplicate submissions deterministically, and add a regression test asserting one event/notification row after rapid double-click.

### RCA-020 — live grading notification path is not reachable from the Instructor result UI

- Evidence: a read-only live SQL Server probe found attempt `cad60ac5-c516-4f65-9aa2-a7ad8ff3b360` for `student2@pwd301.local`, assessment `Kiểm tra Giữa kỳ: Kiến thức Web & Flask Core`, with one pending `ESSAY` grade. Browser Instructor login succeeded, but navigating to the assessment-results route rendered `Assessment not found` and no grading control. Live `question_corrections` had zero rows. The isolated `tests/api/test_regrade_api.py -q` run returned 4 passed.
- Root cause: not yet isolated; the current live Browser/API visibility does not resolve the assessment that is present in the live database, so the UI business path cannot be correlated to the grading notification producer.
- Impact: `ASSESSMENT_GRADED`/`SCORE_CHANGED_AFTER_REGRADE` cannot be accepted end-to-end; a pending student grade may remain invisible to the instructor workflow.
- Severity: P1 evidence and business-workflow gap.
- Fix direction: reconcile the runtime assessment identifier/visibility query with the live DB, then run one manual grade or correction/regrade through Browser, API and SQL Server before changing notification code.
- **Current-state correction (fresh 2026-10-04 probe):** The earlier pending-ESSAY snapshot is not reproducible now. Course-management navigation opened the live DSA201 gradebook with one submission at `100 / 100`; the detail modal contained only two `SINGLE_CHOICE` questions and no manual-grade/regrade control. Fresh host DB query returned `0` pending grade rows and `question_corrections` remains empty. The unresolved gap is now the absence of a live manual-grade/regrade path, not a currently observed pending attempt.

## RCA-021 — enrollment succeeds but owner notification rows are missing

- **Issue:** A student can be ACTIVE in OPS401 while the course owner receives no `STUDENT_ENROLLED` in-app notification.
- **Evidence:** Browser Instructor1 showed OPS401 with 2 students and a notification center containing 3 unrelated unread items. Read-only host SQL Server showed active OPS401 enrollments for `student3@pwd301.local` and `student1@pwd301.local`; four `STUDENT_ENROLLED` `NotificationEvent` rows targeted owner users 2/3, but each had zero linked `Notification` rows.
- **Frontend flow:** Instructor dashboard and notification center rendered normally, but no enrollment item was available to render.
- **Backend flow:** `enroll_student()` commits the enrollment and then calls `dispatch_notification()` for the course owner and student. The persisted event-without-notification pattern shows the notification delivery transaction is not producing the required in-app row.
- **API/DB:** Enrollment state and append-only event exist; the owner-facing `Notification` record is absent. The student success notification path was not separately correlated in this live snapshot.
- **Root cause status:** The live SQL Server snapshot contains a confirmed persisted delivery gap, but the exact runtime exception is not isolated and the current path is not presently reproducible.
- **Fresh reproduction:** a transaction-only SQL Server run for an un-enrolled Student/Course pair simulated the service commit with `flush()` plus `expire_all()` (without durable commit), executed the real `enroll_student()` path, observed an ACTIVE return plus 2 new `STUDENT_ENROLLED` events and 2 linked `Notification` rows, then rolled back all changes. The same run emitted no dispatch warning.
- **Contributing source evidence:** both owner and student `dispatch_notification()` calls are inside one broad `try/except`; any first dispatch exception would be logged and suppress the second recipient dispatch while `enroll_student()` still returns the ACTIVE enrollment. This remains a resilience risk and a plausible failure mechanism, not the confirmed current exception.
- **Impact:** P1 — course owners cannot reliably learn that students joined their course; notification and business state diverge.
- **Recommended fix:** instrument and make owner/student notification persistence atomic or explicitly retryable after enrollment commit, then verify one event, one notification per intended recipient and cross-course isolation.

## RCA-025 - notification role/status query parameters are permissive and ambiguous

- **Issue:** the REST list endpoint accepts `role`/`target_role` and `status` values without rejecting unsupported values or guaranteeing a role-specific result set.
- **Evidence:** fresh Admin JWT GETs returned the same 7 items for `role=STUDENT`, `role=INSTRUCTOR` and `role=ADMIN`; `status=BOGUS` and `unread_only=maybe` returned the unfiltered 7 items; `category=BOGUS` returned zero. Source `api_notifications/routes.py:53-57` forwards raw query values, while `notification_service.py:332-338` only applies exact `unread`/`read` semantics and `_visible_notification_query():309-314` includes rows whose `target_role` is `NULL` for every requested role.
- **Frontend/API/DB:** no cross-user leak was observed because the base query still filters `recipient_user_id`; however, a client cannot infer from a successful response whether a role filter was applied. The global unread counter is also calculated without category/status filtering.
- **Root cause:** permissive query parsing and a fallback rule that treats role-less notifications as visible in every role view, without an explicit contract distinguishing global notifications from role-scoped notifications.
- **Impact:** P2 contract/UX ambiguity; consumers may show a seemingly filtered view while actually receiving the same actor-owned set, and invalid status input can silently degrade to “all”.
- **Recommended fix:** validate enum values, document global-vs-role-scoped semantics, return a stable validation error for unsupported filters, and add tests proving both null-target global notifications and role-targeted rows.

## RCA-026 - notification-center category filters are skipped by keyboard focus

- **Issue:** the notification center exposes category filter buttons visually and in the accessibility tree, but the observed keyboard tab order cycles between `Tất cả` and `Chưa đọc` without reaching `Khảo thí`, `Khóa học` or `Hệ thống`.
- **Evidence:** fresh Student Browser on the DSA201 lesson center: after opening the center, `Tab` focused `Tất cả`, the next `Tab` focused `Chưa đọc`, and the following `Tab` returned to `Tất cả`; `Escape` closed the center. The three category controls were present in the same accessibility tree but were skipped by this tab sequence.
- **Frontend flow:** visible filter controls are rendered, but keyboard focus traversal does not expose the same control set; no backend/API defect is inferred from this observation.
- **Root cause status:** confirmed Browser behavior; exact DOM `tabindex`/focus-trap implementation cause still requires source-level focus inspection.
- **Impact:** P2 accessibility and notification discoverability gap; keyboard-only users may be unable to reach category-specific notifications.
- **Recommended fix:** make every visible filter a reachable tab stop or implement an explicit roving-tabindex pattern with arrow-key semantics, then verify focus order and screen-reader names in Browser.

## RCA-027 - wrong JSON types reach notification mutation routes and become HTTP 500

- **Issue:** malformed but syntactically valid JSON reaches Admin notification mutation routes with an unsupported top-level type and produces a generic internal-server response instead of a client validation error.
- **Evidence:** authenticated Admin `POST /api/notifications/broadcast` with JSON string `"oops"` and `POST /api/notifications/mark-all-read` with JSON list `["bogus"]` both returned HTTP 500 `INTERNAL_ERROR` with correlation IDs. A before/after list comparison remained total 7/unread 2 with identical item IDs. Preferences JSON string returned HTTP 400 `VALIDATION_ERROR`.
- **Frontend/API/DB:** no valid notification or read-state mutation occurred in the probe; the 500 response is structured only at the outer error shape, not as a supported validation contract.
- **Root cause:** the Admin broadcast handler in `api_admin/routes.py` and the notification mark-all handler in `api_notifications/routes.py` assumed dictionary payloads and called `.get()` on any truthy JSON value before validating its type.
- **Impact:** P1 API robustness/error-contract defect; malformed clients receive a server-error classification and operators may see a generic failure for recoverable input.
- **Recommended fix:** validate top-level JSON type before field access, return a stable 400/422 validation code, and add string/list/object boundary tests for every notification mutation route.

### RCA-027 current remediation

The two affected handlers now reject non-object JSON with HTTP 400 `ValidationError` before field access. A new API regression first failed with the historical HTTP 500 behavior, then passed after the fix; the focused test also confirms no malformed broadcast or mark-all mutation is accepted. The broader API envelope inconsistency remains a separate open contract issue.

## RCA-024 - result and appeal paths call an undefined UI.alert helper

- **Issue:** two Student result/appeal branches invoke `UI.alert(...)`, but the shared UI class has no `static alert` implementation.
- **Evidence:** source search found `frontend/assets/js/views/student.js:5722` and `:5830`; `frontend/assets/js/ui.js` defines `showToast`, `openModal`, `confirm` and `closeModal`, then exports `window.UI`, with no `alert` method. A read-only Node VM load of the current file returned `UI.alert=undefined`, `UI.openModal=function`, `UI.confirm=function`. Separate native `window.alert(...)` fallbacks remain at `frontend/assets/js/controllers.js:30` and `:184`.
- **Frontend flow:** the current fresh result page rendered the score and appeal controls, but did not render the scale button or a pending-appeal state that would invoke these branches; therefore no browser runtime exception is claimed.
- **Backend/API:** not reached by the static-only finding; no API or DB failure is proven by this row.
- **Root cause:** shared notification/modal API drift: callers reference a removed or never-implemented helper, while fallback paths bypass the project notification standard.
- **Impact:** if the pending-appeal or scale branch becomes reachable, the user may receive no dialog and the branch may throw `TypeError: UI.alert is not a function`; authentication/result correctness is not affected by the evidence currently captured.
- **Severity:** P2 unverified static defect until a reachable Browser branch proves a user-visible failure.
- **Recommended fix:** replace both calls with the existing `UI.openModal`/`UI.confirm` contract or add a deliberately specified shared method, remove native `window.alert` fallbacks, then execute the pending-appeal and scale branches in Browser with console/error capture.

## Current remediation update - RCA-006

### RCA-006 Browser continuation

On `http://localhost:5000`, clean logout/login sessions for Admin, Instructor and Student were each followed by temporary CDP blocking of all notification endpoints. In all three roles, opening the center showed `Không thể tải thông báo`, the explanatory status and `Thử lại`, and did not show `Không có thông báo nào`. After removing the block and using retry, reopening the center rendered the real notification list for each role. No business mutation was submitted; the temporary block was removed. The three representative-role Browser paths therefore confirm the RCA-006 remediation; broader retry/idempotency coverage remains open.

## RCA-028 - graded-result notification points to the wrong identifier

- **Issue:** a Student notification related-page CTA opened a 404 instead of the graded attempt result.
- **Evidence:** fresh Edge Student session opened a graded-result notification detail, but `Mở Trang Liên Quan` navigated to `#/student/assessments/<assessment-id>/results` and rendered a server 404. Direct navigation to `#/student/assessments/results?id=<attempt-id>` rendered the real result page. A new unit test failed before the fix because the service used `assessment.public_id`; after the fix it passed with `attempt.public_id` in the query parameter.
- **Root cause:** `src/pwd301/services/attempt_service.py` constructed the action URL from the assessment public ID, while the Student result view resolves an attempt ID through the `id` query parameter.
- **Impact:** P1 business navigation defect; the notification reports a real score but cannot take the learner to the corresponding result.
- **Fix:** use `#/student/assessments/results?id=<attempt.public_id>` for initial grading and score-change notifications; retain the focused regression test.

## RCA-029 - enrollment notification links bypass the SPA route contract

- **Issue:** owner/student enrollment notifications were emitted with server paths instead of the role-specific hash routes used by the frontend.
- **Evidence:** source inspection found `/instructor/courses/<public_id>` and `/student/courses/<public_id>` in `src/pwd301/services/enrollment_service.py`. A new failing unit test captured both dispatch payloads and expected `#/instructor/courses/manage?id=...` and `#/student/courses/detail?id=...`; it failed before the fix and passed after the fix.
- **Root cause:** the enrollment producer bypassed the existing SPA action URL convention used by course, dashboard and student-card links.
- **Impact:** P1 notification CTA can land outside the SPA or on an unresolved route even when enrollment succeeds.
- **Fix:** emit the existing canonical hash routes; a fresh live enrollment/notification/DB correlation remains an acceptance gap.

## RCA-030 - notification center briefly treats revalidation as empty

- **Issue:** an Instructor center opened immediately after login showed the empty-state copy while the badge already reported 14 unread items; after a short revalidation/filter interaction the same center rendered all 14 items.
- **Evidence:** fresh Edge Instructor login showed `notifications 14`; the first center snapshot showed `0 mới` and `Không có thông báo nào`, while clicking `Tất cả` shortly afterward showed the 14 unread records and clicking `Chưa đọc (14)` retained them.
- **Root cause status:** timing/cache behavior is confirmed, but the precise stale-cache source and fetch ordering require a focused browser/network trace. `openNotificationsDropdown()` renders cached content immediately and performs background `fetchNotifications(false)`; an empty role-filtered cache is indistinguishable from a valid empty response.
- **Impact:** P2 UX/trust issue; users can briefly infer that notifications disappeared or were not delivered.
- **Fix direction:** retain skeleton/loading state until the first role-scoped fetch is ready when the cache is empty or role-mismatched, then render a legitimate empty state only after a successful zero-item response; add a deterministic delayed-fetch Browser/Node regression.

### RCA-030 current remediation

`router.js` now records an explicit `loading` state and renders the existing skeleton when the cache is empty during revalidation. A deterministic Node regression failed against the previous implementation because the cached empty state rendered immediately, then passed after the fix; a successful zero-item response still renders the legitimate empty state. The original Browser observation remains valid as pre-fix evidence, while a delayed live Browser replay is not claimed.

The original RCA-006 evidence remains valid as historical pre-fix evidence. Current `ApiClient.getNotifications()` raises `NOTIFICATIONS_UNAVAILABLE` after all three route attempts fail; the router renders explicit degraded/retry guidance. Node regressions and the later three-role Browser outage/retry recovery passed.

## RCA-023 - logout leaves a protected global modal mounted

Current qualification: the finding below is historical. Source now includes overlay cleanup. The latest Instructor1 replay closed CS201 settings with Escape before account-menu logout; Back settled at `#/auth` without visible private course/topbar/modal content. The earlier account-menu click may have backdrop-closed the overlay before logout, so full mounted-overlay teardown is still not independently Browser-verified.

- **Issue:** logging out while a course-settings modal is open leaves the modal mounted over the login page.
- **Evidence:** fresh Browser session logged in as `instructor2@pwd301.local`, opened DSA201 `Cài đặt & Học vụ` and its `Chuẩn đầu ra & Học vụ` tab, then clicked `Đăng xuất tài khoản`. The accessibility tree and screenshot showed the unauthenticated login form plus the still-visible `Cài đặt & Học vụ DSA201` modal with SLO content and an incoming prerequisite request. Closing the modal manually removed the exposed content.
- **Frontend flow:** `frontend/assets/js/router.js:995-1015` calls `toggleShell(false)`, `ApiClient.logout()` and `renderAuth()`; `renderAuth()` only replaces `#app-viewport`. `frontend/assets/js/api.js:150-168` also clears shell state and changes the hash. Neither logout path calls `UI.closeModal()` or clears `#modal-container`/the modal stack. The generic cleanup at `router.js:251-255` is reached by routed render, but direct logout bypasses it.
- **Backend/API:** the logout request succeeds and client auth state is cleared; the defect is client-side lifecycle cleanup, not proof that the server session remained valid.
- **Root cause:** global modal ownership is separate from auth teardown, and logout has no invariant that all protected overlays are removed before rendering the auth screen.
- **Impact:** P1 privacy/session-boundary defect: protected course data remains visible after logout until the user closes the modal or reloads.
- **Recommended fix:** centralize session teardown so it clears `#modal-container`, `UI._modalStack`, drawers and protected viewport before showing login; use `history.replaceState` for the auth route. Add a Browser regression that logs out with each global overlay open and asserts no protected text remains in the rendered DOM or screenshot.

## RCA-022 — enrollment capacity boundary can accept a second student

- **Issue:** The enrollment success/notification path cannot be trusted at a full course boundary.
- **Evidence:** `tests/unit/test_enrollment_service.py -q` returned `16 passed, 1 failed`; `test_enroll_student_capacity_limit` created a capacity-1 course, enrolled the first student, then expected `EnrollmentCapacityExceededError` for the second student but no exception was raised. The live Browser valid OPS401 path separately showed a success toast and active enrollment.
- **Root cause status:** Confirmed source/test contract conflict. The current service reaches the row-lock section and then explicitly applies an unlimited-capacity policy, with no `locked_course.capacity` guard before creating the new Enrollment; the focused test still requires capacity `1` to reject the second student.
- **Impact:** P1 business/notification risk — an over-capacity enrollment may produce a false success and downstream `STUDENT_ENROLLED` event.
- **Recommended fix:** resolve the canonical capacity decision, then implement or remove the guard consistently across specification, service, API feedback and tests; rerun valid, full-capacity, duplicate and notification post-condition tests before accepting success feedback.

## RCA-031 — unauthenticated auth routes enter the role-home fallback

- **Evidence:** actual page-runtime CDP inspection showed `window.app` and `AppRouter` existed despite the earlier DOM-scope evaluation implying otherwise. Three actual-router tests failed for `#/auth`, `#/login` and an expired session on a protected route, with stack traces reaching `dispatchRoute()` and `redirectToRoleHome()`.
- **Root cause:** auth routes bypassed the initial refresh guard but had no unauthenticated render/return branch. Dispatcher fallback sent them to the Student dashboard; the protected-route guard then sent them back to auth.
- **Fix:** render the existing auth view and hide the shell whenever the post-refresh user is absent, returning before dispatcher fallback. Reuse existing `renderAuth()` and history replacement; add no bootstrap mechanism or dependency.
- **Verification:** focused RED 7 passed/3 failed → GREEN 10 passed/0 failed, both 0 skipped; full frontend 101 passed/0 failed/0 skipped. Live Instructor1 login → CS201 modal → Escape → logout → Back settled at `#/auth` with no private surface visible and routing idle.
- **Evidence correction:** BFCache was not established. The agent-owned speculative bootstrap change and mock-only tests were removed. Full overlay-at-logout testing remains a separate gate.

## RCA-032 - persisted broadcast duplicate on rapid retry

- **Issue:** a rapid Admin broadcast retry persisted two `SYSTEM_BROADCAST` events and two recipient rows for one business action; the list query only hid the duplicate by title/body.
- **Evidence:** the historical SQL Server probe found two event IDs for one recipient. A new RED API regression failed because the second same-key response had no replay marker. After the fix, the API regression passed and a fresh disposable Browser double-click produced one POST, one event and seven recipient rows in SQL Server.
- **Root cause:** the broadcast producer generated a random event key for every request, had no idempotency contract, and the modal allowed concurrent submission.
- **Fix:** accept a UUID `X-Idempotency-Key`, persist it as `NotificationEvent.event_key`, return the original fan-out count on exact replay, reject changed payloads with `409`, and keep the same key across UI retry while disabling the submit action in flight.
- **Impact:** the scoped Admin broadcast duplicate gate is closed. Historical duplicate records remain evidence and are not silently rewritten.

## RCA-033 - shared REST notification mutations dereferenced malformed payloads

- **Issue:** `/api/notifications/broadcast` and `/api/notifications/emails/retry-failed` returned HTTP 500 for JSON list payloads because the route called `.get()` before validating the top-level type.
- **Evidence:** a RED regression returned 500 with `AttributeError: 'list' object has no attribute 'get'`. After the guard, focused notification API tests passed and a live disposable SQL Server HTTP replay returned 400 `VALIDATION_ERROR` for both routes with no business mutation.
- **Root cause:** the shared notification blueprint had a different payload parser from the already-correct Admin blueprint.
- **Fix:** normalize JSON/form input and reject non-object payloads before field access in broadcast, retry and preferences routes.
- **Impact:** the shared REST validation gate is closed; canonical outer response-envelope normalization remains separate.

## RCA-034 - notification response envelope drift

- **Issue:** scoped notification success responses exposed useful fields only at the top level, while errors from the same family omitted the canonical `success=false,data=null` members.
- **Evidence:** a RED regression failed on missing `success`/`data` keys for list, unread-count, mark-read, mark-all and dismiss responses. The same focused run also asserted canonical error members for malformed payloads.
- **Root cause:** notification route handlers predated the project-wide `{success,data,error}` contract, and the shared error formatter returned only the legacy error object.
- **Fix:** wrap scoped notification successes in `success=true,data=...`, update the shared error formatter to emit `success=false,data=null,error=...`, and retain existing top-level fields during client migration.
- **Verification:** notification API **12 passed**, Admin broadcast **1 passed**, notification IDOR **7 passed**, full API **383 passed**, and current split collection **1587** with zero skips. Disposable SQL Server malformed/replay probes preserved the same contract and no invalid mutation.
- **Scope limit:** remaining non-notification API/web-auth handlers and historical Browser observations still require their own contract decision and evidence; this is not a whole-application envelope sign-off.

## RCA-035 - external email delivery evidence is unavailable in the live runtime

- **Issue:** the live Admin retry endpoint had no eligible failed email row and the environment exposes no configured `MAIL_SERVER`/`SMTP_HOST`, so an external inbox delivery could not be asserted.
- **Evidence:** the fresh `email-runtime-probe.py` used real `smtplib` wire transport to an ephemeral loopback SMTP sink. It created one SQL Server outbox row, forced the transport to fail (`FAILED`), called the Admin retry API (`200`, `success=true,data.retried_count=1`), then processed the row to `SENT`; the sink captured exactly recipient `student4@pwd301.local` and subject `PWD301 audit email`. Cleanup reported `audit_database_remaining=0`.
- **Root cause:** the live runtime still has no approved external SMTP provider or inbox sink configured; the loopback sink closes the local SMTP protocol boundary but cannot prove Internet/provider delivery.
- **Impact:** outbox state, retry authorization, recipient boundary and loopback SMTP response handling are verified. Approved-provider delivery, inbox acceptance and production-like delivery timing remain unverified.
- **Recommended fix:** provide an approved disposable SMTP provider/inbox configuration for the release test environment; retain the loopback probe for deterministic local wire coverage; never use a production recipient or print credentials in audit evidence.
- **Status:** application outbox/retry plus loopback SMTP transport PASS; external provider/inbox gate remains OPEN.

## RCA-042 - Browser file chooser cannot supply the upload fixture

- **Issue:** the Instructor course-cover upload input is visible and has the expected image allowlist, but the audit Browser cannot provide a local file.
- **Evidence:** `#course-thumbnail-input` was inspected in the live CS201 course page with `accept=image/png,image/jpeg,image/webp`; `fileChooser.setFiles` returned `Not allowed`, and a visible click did not open a native chooser window.
- **Root cause:** Edge extension/browser file-selection permission is unavailable to the automation session; the backend upload validation path was never reached.
- **Impact:** valid image upload, invalid MIME/size rejection, quarantine access and post-upload notification remain unverified.
- **Recommended fix:** grant a narrowly scoped approved local-file chooser permission or perform one manual file selection, then capture API/DB/UI evidence. Do not weaken backend file safety to bypass the Browser limitation.
- **Status:** environment-blocked, not an application pass/fail.
- **Fresh CUA retry:** on the current CS201 page, both visible upload controls were clicked through the native accessibility path; neither opened a file-picker window, and the input remained without a selected file. The earlier CDP `fileChooser.setFiles` rejection therefore remains reproducible at the Browser boundary, with no upload request or database mutation.

## RCA-043 - Browser resource download remains an incomplete stream

- **Issue:** Student4 clicked a visible authorized PDF download, but Edge left a `.crdownload` file instead of a finalized readable PDF.
- **Evidence:** the live lesson page exposed the expected resource link; after the click, Downloads contained `Tong_hop_Do_phuc_tap_Thuat_toan_BigO.pdf.crdownload` at 1169 bytes, still present after five seconds.
- **Root cause:** not yet isolated between Browser download handling and the application/proxy response stream; response completion, content length and final file readability are still missing.
- **Additional evidence:** the partial file is 1169 bytes, begins with `%PDF-1.4` and contains `%%EOF`; the bytes look complete even though Edge never finalized the `.crdownload` name.
- **Server-side continuation evidence:** the same authenticated download returned HTTP `200`, `Content-Type: application/pdf`, `Content-Disposition: attachment`, `Content-Length: 1169`, a matching PDF body and a terminal `%%EOF` through a direct session replay. This confirms the application response body and headers are complete; Browser finalization remains the unresolved boundary.
- **Impact:** the UI cannot be graded as “download thành công”; a success toast would be misleading until the file closes and can be opened.
- **Recommended fix:** inspect the authenticated response headers/body closure and Browser download completion, then add a regression that requires a finalized readable file rather than merely a click.
- **Status:** PARTIAL/FAIL pending stream-level evidence.
- **Updated status:** BACKEND/HTTP PASS; Browser file-finalization remains PARTIAL/FAIL and requires a permitted Browser download path or manual confirmation.

## RCA-051 - Student result PDF export delegates to an unobservable print dialog

- **Issue:** the visible Student result action is labeled `Xuất bảng điểm (PDF)`, but it does not create an application download; `frontend/assets/js/views/student.js:5375` invokes `window.print()`.
- **Fresh Browser evidence:** Student1 opened the scored result at `#/student/assessments/results?id=db76cdce-bef6-470d-be11-7d35cc9ab96b` and the button was visibly present. The semantic click timed out while dispatching input; a fresh coordinate click left the result page and accessibility tree unchanged. No new Browser tab, toast, verifiable download event or new file appeared in `C:\Users\LENOVO\Downloads`; only earlier resource PDFs were present.
- **Root cause:** export semantics are delegated to the browser/OS print surface, so the application has no completion callback, generated-file post-condition or user-facing failure/retry state that this Browser session can verify.
- **Impact:** the result-PDF requirement remains NOT VERIFIED; calling the print button a successful PDF export would overstate the evidence.
- **Recommended fix:** either expose a server-authoritative PDF download with a completion/error notification or document and Browser-test the supported print-dialog handoff, including a manual save confirmation path.
- **Status:** Browser export NOT VERIFIED; no product or database mutation observed.

## RCA-044 - UI.alert inverted title and message arguments

- **Issue:** the shared `UI.alert` helper rendered the second caller argument as the title, although both Student result callers pass title first and detail second.
- **Evidence:** RED Node regression captured `modalOptions.title` as `Nội dung cần hiển thị` when the caller supplied `Tiêu đề cảnh báo` followed by that body.
- **Root cause:** helper signature was `alert(message, title)` while the result/appeal callsites used `alert(title, message)`; multiline body text was also not converted to readable line breaks.
- **Fix:** make the helper title-first, escape the body and preserve line breaks as `<br>` before passing it to the existing modal owner.
- **Impact:** pending-appeal and score-scale dialogs could show misleading hierarchy/copy; no backend or DB state was changed.
- **Verification:** focused regression GREEN; full frontend suite **102 passed, 0 failed, 0 skipped**.
- **Scope limit:** Browser must still expose the pending-appeal/scale triggers for end-to-end visual acceptance.

## RCA-045 - seeded security notification exposed raw network telemetry

- **Issue:** Admin notification center displayed `192.168.1.105` in a security message.
- **Evidence:** Browser DOM showed the raw IP; a direct query of the live `pwd301_db/PWD301` SQL Server found one matching `SYSTEM_SECURITY_ALERT` row (`notification_id=20002`).
- **Root cause:** demo seed content embedded a concrete IP in user-facing notification prose, and the already-seeded live row was not rewritten when source text changed.
- **Fix:** replace the seed prose with a safe anomalous-login description and update only the matching live security notification row in a transaction.
- **Impact:** reduces telemetry disclosure without removing the security event or its audit action.
- **Verification:** TDD regression passed; live SQL query returned `remaining_raw_ip=0`; Browser reload rendered the safe copy and no raw IP.
- **Scope limit:** dynamic production-generated security alerts still require a separate producer/catalog review.

## RCA-047 - dynamic SECURITY notification text could expose raw IPv4 telemetry

- **Issue:** fixing the seeded security row did not protect a future SECURITY notification producer that supplied an IPv4 in title, body or CTA URL.
- **RED evidence:** the new unit regression first observed `192.168.1.105` unchanged in all three user-facing fields.
- **Root cause:** shared `dispatch_notification` escaped HTML but had no network-telemetry redaction for mandatory SECURITY notifications; only the demo seed had been corrected.
- **Fix:** add one shared IPv4 redaction helper and apply it to SECURITY title/body plus `action_url`/`target_url` event payload values before persistence and delivery.
- **Verification:** focused notification unit/API/demo/security scope passed **37 passed, 0 failed, 0 skipped**; the complete current non-overlapping split passed **1,589 passed, 0 failed, 0 skipped**; SQL Server disposable gates passed **17** and both audit databases were removed.
- **Scope limit:** this protects the shared dispatch boundary; a complete producer/catalog inventory and external email receipt remain open.

## RCA-048 - REST notification role filters silently accepted unsupported values

- **Issue:** the shared REST notification list, unread-count and mark-all-read routes accepted unsupported or actor-ineligible `role`/`target_role` values and returned a successful no-op instead of a validation response.
- **RED evidence:** the new parametrized API regression used Student authentication with `ADMIN` and `BOGUS`; both cases observed HTTP `200` where the contract requires HTTP `400 VALIDATION_ERROR` for list, unread-count and mark-all-read.
- **Root cause:** route query/body values were forwarded into notification service filters without normalizing against the canonical role set and the authenticated actor's active roles.
- **Fix:** add one shared normalizer in the notification blueprint, accept only `STUDENT`, `INSTRUCTOR` or `ADMIN`, require the authenticated actor to hold the requested role, and apply it consistently to list, unread-count and mark-all-read. Lower-case `student` remains a valid normalized value for a Student actor.
- **Verification:** RED `2 failed, 0 passed`; GREEN role-filter regression `2 passed, 0 failed, 0 skipped`; current notification API/service/IDOR scope `34 passed, 0 failed, 0 skipped`; the refreshed non-overlapping Python split is `1,591 passed, 0 failed, 0 skipped`, including `17` SQL Server integration passes with both disposable databases cleaned; frontend is `105 passed, 0 failed, 0 skipped`; scoped Ruff passed and `git diff --check` passed.
- **Impact:** invalid or unauthorized role filters now fail closed with the canonical validation envelope and cannot silently mislead the caller about notification state. No schema or database-data migration was required.
- **Scope limit:** this closes REST filter validation only; complete producer/role coverage, broadcast audience validation, external email receipt, historical repair and broader retry/idempotency remain open.

## RCA-046 - ESSAY grading and result views assumed choice questions

- **Issue:** the live Instructor grading detail exposed a pending ESSAY answer without a server-authoritative manual-grade action, while the Student result renderer could display an answered/manual-graded ESSAY as unanswered, zero points and choice labels.
- **Evidence:** the initial frontend regression was RED for the missing grading API/control assertions. A controlled Browser fixture then showed the pending row, ESSAY answer, score input, required reason field and save action. Saving `3.5` with a reason produced the Vietnamese success toast; the refreshed modal showed `3.5 / 20` and `3.5 / 4` for the ESSAY. SQL Server showed `GRADED`, `MANUAL_GRADED`, `awarded_points=3.5`, the persisted reason and rowversion `0000000000112d3c`.
- **Root cause:** `get_instructor_attempt_evaluation` did not expose the grade rowversion needed by the UI API call; the Instructor modal only rendered choice-oriented detail; and the Student renderer read choice answer fields instead of `student_answer_text`/manual awarded points for ESSAY.
- **Fix:** expose the rowversion, add the existing grading API client call to the pending/manual-graded ESSAY card with score/reason validation, and render Student ESSAY answers, manual status, awarded points and feedback through the existing result card.
- **Verification:** focused frontend regression **3 passed, 0 failed, 0 skipped**; full frontend **105 passed, 0 failed, 0 skipped**; full API partition **383 passed**; Browser/API/SQL fixture flow passed and cleanup returned zero targeted attempts plus zero orphan answer/grade/history/result rows.
- **Scope limit:** a direct Browser replay of the existing released ESSAY result now shows the persisted answer, `4 / 4 đ`, manual feedback and no choice labels. The fullscreen limitation applies only to starting a new controlled exam attempt; other ESSAY producers/roles and Browser proctoring remain separate scope.
## RCA-052 - Student result PDF export now uses a server-generated download

- **Issue:** The result action previously invoked `window.print()` instead of producing a file that the student could download.
- **Fix:** Add the authenticated `GET /student/attempt/<attempt_id>/result.pdf` route, reuse the server-side result authorization and score-release policy, generate a valid PDF attachment from released data, and replace the frontend print button with a download link.
- **Security boundary:** Hidden scores return `403`; the PDF filename uses the assessment/course label and does not expose the attempt UUID; the response is private, `no-store` and `nosniff`.
- **TDD evidence:** RED returned `404` for the new endpoint; GREEN released-result and hidden-score tests passed. The generated bytes were parsed by `pypdf` and contained the persisted score.
- **Fresh Browser evidence:** Student1 opened the scored result, saw a link with `ID=download-student-result-pdf-btn` and URL `/student/attempt/db76cdce-bef6-470d-be11-7d35cc9ab96b/result.pdf`, clicked it, and Edge created `C:\Users\LENOVO\Downloads\CS101-bang-diem.pdf` (1,713 bytes). The file begins `%PDF-`, ends with `%%EOF`, and `pypdf` reads one page containing the persisted `Score: 1.00 / 16.00`.
- **Status:** PASS for the Student released-result PDF download path; other file-producer Browser gates remain separate.

## RCA-053 - result view displayed fabricated integrity metadata

- **Issue:** the Student released-result page displayed a fixed `7f8a92b1...10243` signature-like value, a fallback instructor identity and a fallback 45-minute duration even when the API did not provide those fields.
- **Root cause:** the renderer used hard-coded presentation defaults instead of distinguishing an API value from an unknown value. This could make a user believe an integrity hash or timing value had been verified when it had not.
- **Fix:** the renderer now reads `data.signature_hash`, `data.instructor_name` and `data.duration_minutes`; missing values render `Chưa có dữ liệu`. The fixed signature is removed and user-facing values are escaped.
- **Verification:** TDD RED/GREEN passed in `audit_remediation_regressions.test.js`; the full frontend suite passed **108 passed, 0 failed, 0 skipped** and Ruff passed. Browser visual replay is not claimed because the CUA environment currently has no available Browser binding.
- **Status:** source-level truthfulness correction complete; Browser visual acceptance remains pending and no fake value is treated as evidence.

## RCA-054 - keyed lesson-flag retries could duplicate durable notification side effects (2026-10-06)

- **Root cause:** both Admin flag routes previously called the shared service without a request idempotency key; every retry created a fresh notification event and audit row. API presentation could collapse similar notices, but it did not prevent duplicate database/email side effects.
- **Fix:** flag_lesson_content now accepts and validates X-Idempotency-Key, persists the key on the canonical NotificationEvent, returns the prior durable outcome on an exact replay, and raises 409 CONFLICT for a changed payload or another operation. The existing atomic commit/rollback boundary is preserved.
- **Evidence:** disposable SQL Server replay produced first 200/false, second 200/true, changed payload 409/CONFLICT, and exactly 1 audit + 1 event + 1 notice; probe reported **3 cases, 0 failed, 0 skipped** and cleanup reported audit_database_remaining=0.
- **Residual risk:** this closes only the keyed lesson-flag producer. A Browser rapid retry still needs a real CUA session, and unrelated producers remain outside this fix.

## RCA-055 - title/body duplicate heuristic hid distinct business events (2026-10-06)

- **Root cause:** _visible_notification_query used a newer-row subquery matching only recipient, title, body and target role. It treated identical copy as proof of a retry, despite distinct NotificationEvent rows and potentially different event types.
- **Fix:** remove presentation-layer deduplication. Durable event visibility is now one row per non-expired Notification record; retry deduplication is enforced at the producer with an explicit idempotency key where required.
- **Evidence:** the RED regression created SYSTEM_NOTICE and COURSE_ANNOUNCEMENT events with identical copy and observed total 1. After the minimal query change, both events remain visible and the combined notification/flag scope passed **37 passed, 0 failed, 0 skipped**.
- **Residual risk:** historical duplicate rows remain in SQL by design until a separately approved disposition; Browser rendering and rapid UI replay still require the unavailable CUA Browser.
- **SQL Server replay:** a fresh allowlisted database created two same-copy events, SQL returned 2 durable rows, and the authenticated REST list returned both event types. The probe ended **1 case, 0 failed, 0 skipped** and exact cleanup returned audit_database_remaining=0.
## RCA-056 - generic event-key reuse silently accepted changed semantics (2026-10-06)

- **Root cause:** emit_event treated event_key as a lookup-only dedupe key and returned the existing row without comparing event_type, actor, target or sanitized payload.
- **Fix:** exact semantic replay remains idempotent; any mismatch now raises ConflictError before a new event is persisted.
- **Evidence:** RED reproduced no exception for changed event type/payload. GREEN passed the notification/flag scope with **38 passed, 0 failed, 0 skipped**. SQL Server probe reported same-copy REST/SQL visibility plus event-key conflict, **2 cases, 0 failed, 0 skipped**, and exact cleanup remaining 0.
- **Residual risk:** producers still need stable keys; callers without keys retain their existing non-idempotent behavior.
## RCA-057 - SQL Server seed idempotency was previously only indirectly evidenced (2026-10-06)

- **Gap:** local seed tests existed, but the audit had not directly proven the second demo seed run against SQL Server without duplicate notification/audit rows.
- **Evidence:** the disposable SQL Server fixture was seeded, seeded again, and returned empty created lists, zero new notifications/audits, and unchanged counts (7 users, 4 courses, 7 questions, 3 attempts, 1 resource, 22 notifications, 13 audits). The probe reported **1 case, 0 failed, 0 skipped** and cleanup returned audit_database_remaining=0.
- **Status:** the current SQL Server seed idempotency gate is **PASS**; this does not authorize reseeding the live PWD301 database.

## RCA-058 - shared dispatch could not carry a producer idempotency key (2026-10-06)

- **Root cause:** `dispatch_notification()` generated an event through `emit_event()` without exposing its existing `event_key` capability. A retryable producer using the shared helper therefore could not persist and replay a stable business key.
- **Fix:** add an optional UUID `event_key` parameter at the end of the helper signature and pass it through unchanged to `emit_event()`, preserving existing positional callers.
- **Evidence:** the new RED test failed with `TypeError: unexpected keyword argument 'event_key'`; GREEN reused one event and one notification on exact replay. Current focused notification/flag scope is **39 passed, 0 failed, 0 skipped**; Ruff, compile and diff check passed.
- **Residual risk:** no blanket key was invented for callers whose business operation does not yet expose one. Stable-key adoption across all producers, Browser retry, external SMTP/inbox and file gates remain open.

## RCA-059 - keyed dispatch did not compare notification content (2026-10-06)

- **Root cause:** event idempotency compared only the explicit event payload. `dispatch_notification()` passed title, body, category and target role to the `Notification` row but omitted them from the event payload, allowing the same key with changed copy to be treated as an exact replay.
- **Fix:** when `event_key` is supplied, persist a private `_dispatch_contract` containing sanitized title/body, category, target role and `force_email`. The existing semantic event comparison then rejects changed content before notification or email fan-out.
- **Evidence:** RED `pytest` assertion failed because changed body did not raise `ConflictError`; GREEN exact replay retained one `NotificationEvent`, one `Notification` and one `EmailDelivery`, while changed content raised `ConflictError` and left the outbox count unchanged. Focused scope: **39 passed, 0 failed, 0 skipped**; Ruff and compile passed.
- **Residual risk:** 35 direct `dispatch_notification()` callsites are unkeyed in the current AST inventory. This fix does not invent unsafe keys for operations lacking a stable business identifier; Browser, SMTP/inbox and producer breadth remain open.

## RCA-060 - enrollment fan-out lacked stable recipient keys (2026-10-06)

- **Root cause:** the enrollment transaction created durable enrollment state and two `STUDENT_ENROLLED` notices, but both dispatch calls relied on generated event keys. A retryable enrollment-side fan-out therefore had no durable business-key boundary per recipient.
- **Fix:** derive UUIDv5 keys from `enrollment.id`, `STUDENT_ENROLLED` and the recipient role (`INSTRUCTOR` or `STUDENT`), then pass them through the shared dispatch helper.
- **Evidence:** RED unit assertion found no `event_key`; GREEN captured two distinct UUIDv5 keys. SQL Server disposable probe created a real enrollment, replayed both notifications, and observed key presence plus event/notification counts `2 -> 2`; **3 cases, 0 failed, 0 skipped**, cleanup zero.
- **Residual risk:** the current AST inventory still has 32 direct dispatch callsites with neither an explicit key nor a prebuilt event. Other producers require individual business identifiers; no presentation-derived key was introduced.

## RCA-061 - password security notification lacked a mutation-version key (2026-10-06)

- **Root cause:** password mutation increments `User.auth_version`, but the mandatory security notification was dispatched with a generated event key after commit. A retry of the same post-commit notification had no deterministic boundary.
- **Fix:** add `_password_change_event_key()` using UUIDv5 over `user.id` and the post-change `auth_version`; both `change_password()` and `set_password()` pass it to the shared dispatcher.
- **Evidence:** RED unit assertion found no key; GREEN passed the key assertion. SQL Server disposable probe verified `auth_version=2`, one keyed event, one notification and one email outbox before/after exact replay; **3 cases, 0 failed, 0 skipped**, cleanup zero.
- **Residual risk:** after the course lifecycle correction, 27 direct dispatch callsites still have neither explicit key nor prebuilt event. Other operations need their own durable business identifiers; no shared text-derived fallback was added.

## RCA-062 - course lifecycle fan-out lacked an audit-scoped retry key (2026-10-06)

- Root cause: change_course_status() persisted the lifecycle AuditEvent but discarded its return value before dispatching COURSE_SUBMITTED_FOR_REVIEW, COURSE_APPROVED and COURSE_REJECTED. Those notices therefore relied on generated event keys and could not identify a retry of the same durable transition.
- Fix: retain and flush the AuditEvent, then derive a recipient-scoped UUIDv5 from its durable ID, action and recipient user ID. Submission fan-out uses a different key for each Admin recipient; owner outcomes use the owner ID.
- Evidence: RED raised a missing-key assertion; GREEN passed the lifecycle producer test. SQL Server disposable replay found the persisted approval key and kept one event/one notification before and after exact replay (4 cases, 0 failed, 0 skipped). Current AST breadth is 35 calls, with 7 explicit keys, 1 prebuilt event and 27 without either.
- Residual risk: remaining producers still need operation-specific durable identifiers; Browser retry/visual acceptance, external SMTP/inbox and historical notification disposition remain open.

## RCA-063 - course-owner reassignment fan-out lacked recipient-scoped keys (2026-10-06)

- Root cause: reassign_course_owner() persisted one COURSE_OWNER_REASSIGNED audit row but both former-owner and new-owner notifications relied on generated event keys.
- Fix: flush the audit row and derive separate UUIDv5 keys from the audit ID, canonical action and each recipient ID.
- Evidence: RED captured missing event_key values; GREEN passed the two-recipient unit test and confirmed the keys differ. Current AST breadth is 35 calls, with 9 explicit keys, 1 prebuilt event and 25 without either.
- Residual risk: this increment has no dedicated SQL Server replay or Browser acceptance; the remaining producers still need operation-specific keys.

## RCA-064 - password-reset token fan-out lacked the mutation-version key (2026-10-06)

- Root cause: reset_password_with_token() incremented auth_version and emitted SECURITY_PASSWORD_CHANGED after commit, but did not pass the durable mutation key used by change_password() and set_password().
- Fix: reuse the shared password-mutation UUIDv5 derivation based on user ID and post-mutation auth_version.
- Evidence: RED found no event for the expected key; GREEN passed the reset-token unit test. Current AST breadth is 35 calls, with 10 explicit keys, 1 prebuilt event and 24 without either.
- Residual risk: Browser retry/visual acceptance, external inbox evidence and the remaining unkeyed producers are open; the disposable SQL Server reset replay now passes with 6 cases and zero skips.

## RCA-066 - durable producer identity gaps (2026-10-06)

- Root cause: several mutation producers emitted notifications after creating a durable role/audit/change-request/file-revision record but did not carry that record's identity into the shared idempotency boundary.
- Fix: derive recipient-scoped UUIDv5 keys from post-mutation auth version, flushed audit ID, persisted change-request ID or persisted file-revision ID, depending on the business operation.
- Evidence: TDD/API RED-GREEN passed for role assign/update/revoke, Admin course edit, course-change submit/approve and infected-file rejection; Ruff passed. AST breadth is now 35 calls / 25 explicit keys / 1 prebuilt event / 9 neither.
- Residual risk: dedicated SQL replay for these four groups, Browser/CUA retry and visual acceptance, external inbox evidence, and the remaining nine unkeyed producers are open.

## RCA-067 - final direct producer inventory gaps (2026-10-06)

- Root cause: the last unkeyed calls were route-level aliases and health/result notifications that had stable domain identifiers but did not pass them to the shared dispatcher.
- Fix: use attempt/result transitions for grading, course/lesson/video/recipient identity for YouTube health, and persisted change-request/event/recipient identity for Admin and instructor routes.
- Evidence: focused attempt, change-request/prerequisite API and service regressions passed 13 + 28 + 79 tests with zero failures/skips; Ruff and compile passed. AST now has 0 unkeyed direct calls.
- Residual risk: the zero-unkeyed result is a source inventory, not proof of SQL Server exact replay, Browser/CUA visual/rapid retry, SMTP inbox delivery or historical notification cleanup.

## RCA-065 - account suspension fan-out lacked the auth-version key (2026-10-06)

- Root cause: suspend_user() incremented auth_version and emitted the mandatory ACCOUNT_SUSPENDED notice after commit without a deterministic mutation key.
- Fix: derive a UUIDv5 from the user ID and post-suspension auth_version and pass it through the shared dispatcher.
- Evidence: RED found no event for the expected key; GREEN passed the unit test. SQL Server combined password/reset/suspension replay passed 9 cases with event/notification/email counts unchanged at 1 -> 1 and zero skips; cleanup returned zero.
- Residual risk: Browser retry/visual acceptance, external inbox evidence and 23 remaining unkeyed producers are open.

## N-168 verification checkpoint (2026-10-06)

The latest source state has no remaining unkeyed direct producer: AST is **35 / 34 / 1 / 0** for total, explicit key, prebuilt event and neither. The full verifier passed **1607 tests with 0 skips**, including SQL Server migration, ROWVERSION race and immutable revision coverage on disposable databases. This removes the prior test-environment gap, while Browser/CUA, external inbox, file/quarantine and historical disposition remain separate residual gates.

## N-169 / RCA-066 - live email outbox had no consumer (2026-10-06)

- **Evidence:** live SQL Server query found 115 `PENDING` `email_deliveries` from 2026-09-19 onward, all at attempt 0, while `background_jobs` was empty; `/health/deep` reports `mail_queue.status=DEGRADED` and `stale_pending_emails=true`.
- **Root cause:** `enqueue_email()` persisted outbox rows but no active Compose worker consumed them; the non-testing default was a mock mail client, so enabling a worker without SMTP would have falsely marked mail as sent.
- **Fix:** `run_worker_once()` now bridges due outbox rows into a deduplicated EMAIL job; `scripts/run_worker.py` and the Compose worker deployment provide the consumer; production transport is fail-closed without `MAIL_HOST` and `MAIL_FROM`; stale queue age is exposed by health telemetry.
- **Residual risk:** worker is not activated in the live stack until an approved SMTP provider is configured; external inbox, Browser/CUA, file/quarantine and historical disposition gates remain open.

## N-170 current acceptance boundary (2026-10-06)

Computer Use `getState()` exposed no apps or browsers, and direct IAB creation failed with `Browser is not available: iab`. Root-cause conclusions based on source, SQL and automated tests therefore must not be promoted to live Browser acceptance. The SQL-enabled aggregate currently reports **1612 passed, 0 failed, 0 skipped**; live external-mail, file chooser/quarantine and historical-data disposition remain separate unresolved gates.

## N-171 historical duplicate disposition RCA (2026-10-06)

- **Evidence:** the live read-only query returned 143 events, 168 linked notifications, zero duplicate event keys and 14 repeated presentation-copy groups.
- **Root cause boundary:** repeated copy is not proof of duplicate business delivery; rows with a `change_request_id` did not repeat that identity, while several legacy payloads contain only a generic action URL or no payload.
- **Impact:** an automatic delete/dedupe could remove a legitimate historical transition or audit evidence.
- **Disposition:** do not mutate live history. Require an owner-approved business-key mapping and a disposable SQL repair/reconciliation rehearsal before any historical correction.

## N-172 API envelope RCA (2026-10-06)

- **Issue:** Web-session notification success responses omitted the canonical `data` member or returned service fields directly.
- **Evidence:** TDD RED failed with `KeyError: data` on `/auth/notifications`.
- **Root cause:** separate session/student route serializers had not adopted the already-established REST notification envelope.
- **Fix:** shared response shape was added to list, count, read, mark-all, dismiss and clear success paths; top-level aliases remain for compatibility.
- **Verification:** 16 notification API tests, Ruff, compile and 7 focused frontend regressions passed; no full post-patch aggregate claim is made.

## N-173 final verification boundary (2026-10-06)

The post-fix aggregate now supplies the missing broad evidence: **1613 passed, 0 failed, 0 skipped** with valid disposable SQL Server URLs, exit code 0, and cleanup of both databases. This closes automated regression for the envelope correction; it does not close Browser/CUA or external SMTP/inbox acceptance.

## N-174 acceptance-scope decision (2026-10-06)

The owner confirmed that SMTP/inbox is not deployed and may be excluded from this acceptance cycle. That removes external delivery as a required gate for this cycle, but does not change the root-cause evidence or authorize draining the live outbox. Browser/CUA remains required and unavailable; file chooser/quarantine root-cause validation is still pending.

## N-175 Browser root-cause evidence (2026-10-06)

Browser execution confirms the notification UI is wired to real session state for all three demo roles: success/logout/permission toasts render, the Instructor unread count changes from 15 to 0 after mark-all-read, and Admin Operations renders live degraded queue data. The same UI also exposes legacy mixed-language text and repeated presentation copies; these are observed content/ownership findings, not inferred from source alone.

## N-176 file/quarantine root-cause boundary (2026-10-06)

The clean-resource path is Browser-verifiable, but the unsafe path is not currently classifiable end-to-end: live SQL has no current PENDING/QUARANTINED revision, direct rejected-file navigation was blocked by the Edge client before the app returned a status, and setting the file chooser was denied because Edge extension file-URL access is disabled. No claim is made that the UI displayed the correct quarantine denial.

## N-177 Student notification root-cause evidence (2026-10-06)


The Student panel confirms the same notification surface has a stable unread/category UI but inconsistent message provenance: Vietnamese business messages coexist with `Thong bao bao tri dinh ky` and short opaque content. The Browser observation supports a message-catalog/producer-ownership finding; it does not by itself identify which producer owns each historical row.
## N-178 upload/quarantine root-cause revalidation (2026-10-06)

The clean upload path is now proven through the Browser and database: Edge accepted the chooser file, the crop/apply flow completed, and SQL Server persisted an `ACTIVE` current revision with two passing scan results. The unsafe path is still not end-to-end classifiable because the direct rejected-file URL remains `ERR_BLOCKED_BY_CLIENT` before the application returns a status. Therefore the successful clean path does not convert the quarantine-denial case into a pass, and no unsafe fixture was uploaded.
## N-179 rejected-file route root-cause boundary (2026-10-06)

The additional course-scoped inline attempt reproduces the same client-side block. The database explains why no UI quarantine card was available: the historical rejected asset has no lesson/resource attachment. The remaining uncertainty is therefore Browser transport/extension behavior versus the application denial response, not an inferred application success.
## N-180 authenticated transport recheck (2026-10-06)

Repeating the download through the authenticated Instructor route produced the same `ERR_BLOCKED_BY_CLIENT`. Missing login/session context is therefore not the root cause of the evidence gap; the remaining boundary is the Browser/client handling of the rejected-file response.
## N-181 system-category Browser root-cause evidence (2026-10-06)

The category filter confirms that the mixed-language maintenance copy and the malware-rejection copy share the same role-facing system bucket but have different message provenance. The Browser evidence supports the catalog/producer inconsistency finding; it does not identify a single owner without payload/source correlation.
## N-182 assessment-category empty-state evidence (2026-10-06)

The Browser empty state is rendered by the notification surface when the Instructor assessment filter has no rows. This confirms the frontend does not invent a notification for an empty category; producer coverage remains a separate database/source question.
## N-183 course-category root-cause evidence (2026-10-06)

The course filter shows one role-facing category mixing course approval, course rejection and lesson approval messages, while the same UI exposes three `#70014` copies with distinct reasons. The observation confirms the duplicate presentation family but does not establish which rows are legitimate transitions without business identity.

## N-184 Admin broadcast client-validation evidence (2026-10-06)

The real Admin form rejects missing title and missing body locally before the broadcast request is accepted. The post-probe container query showed no new event or notification after the latest event timestamp and no background job created. This narrows the validation branch to a no-write frontend guard; it does not establish the valid-send path, retry behavior or external email receipt. SMTP/inbox is intentionally excluded from this cycle because it is not deployed.

## N-185 rejected-file UI-path root cause boundary (2026-10-06)

The current SQL Server data explains why the Student resource UI cannot supply a quarantine test target: every one of the seven rejected revisions has zero `lesson_resources` attachments. The direct rejected-file URL is still blocked by the Browser client before an application response, so the remaining gap is an unavailable attached fixture plus the Browser transport boundary, not permission to release or mutate the rejected asset.

## N-186 fail-closed API root-cause boundary (2026-10-06)

The authenticated HTTP replay proves the backend file gate is not relying on the Browser error: the rejected revision returns a structured `403 FILE_INFECTED` response and no file bytes. The unresolved acceptance gap is specifically Browser/UI reachability and an attached safe fixture, not the sampled API authorization or malware-status decision.

## N-187 SMTP/inbox scope boundary (2026-10-06)

Because SMTP/inbox is not deployed, this audit does not attempt to infer external delivery from `email_deliveries` or the health endpoint. The outbox backlog remains evidence of current operational state, while external-provider and inbox acceptance are explicitly outside this cycle.

## N-188 historical duplicate reclassification (2026-10-06)

Root cause is legacy notification payloads that store only recipient/title/body/role and sometimes a generic action URL; they omit `change_request_id`/`file_asset_id` and cannot be safely joined to business transitions. The current query shows 12 groups are explainable by durable transition timing/identity, while 17 rows remain unexplainable. This narrows the repair target; it does not authorize deletion.

## N-189 Browser quarantine-override boundary (2026-10-06)

The Browser evidence adds a UI-level guardrail: the override modal cannot proceed without a File Asset ID, and the empty submission was rejected before any privileged action. Because no rejected asset was released, this evidence cannot establish the backend release path, password verification, audit persistence or post-release scan transition.

## N-190 focused quarantine backend boundary (2026-10-06)

The focused tests confirm the known backend boundary: primary-admin and override validation behavior are covered, and quarantined/infected file access remains fail-closed. They do not prove the end-to-end successful override transition because no credentialed release was attempted.

## N-191 Browser runtime boundary (2026-10-06)

The current console capture showed no application exception for the exercised flows. The sole warning was the pre-existing Tailwind CDN production-use warning, which is unrelated to the unresolved duplicate identity and quarantine-release evidence gaps.

## N-192 legacy identity root cause refinement (2026-10-06)

The remaining ambiguity is structural, not a missing query: legacy `target_id` points to the notification recipient, while no durable business target, correlation ID, actor or audit record links the copy to a request/revision. Therefore the repeated rows cannot be safely classified as duplicate delivery or distinct transitions from current data alone.

## N-194 rejected-file Browser root cause boundary (2026-10-06)

The Browser denial evidence is intercepted by Edge before Flask/SQL Server can answer. Therefore the observed cause is a client policy boundary, not proof of an application authorization branch. The authenticated HTTP/API `403 FILE_INFECTED` evidence remains valid separately; Browser UI denial remains unverified.

## N-195 download-route family root cause refinement (2026-10-06)

Reproducing the same block on the API download route rules out a single Instructor-route implementation as the immediate Browser failure. The remaining causal boundary is Edge/extension handling of these local file-response URLs.
## N-196 exact business-window recheck (2026-10-06)

A further read-only SQL Server check searched `course_change_requests` in the exact event windows for the 13 unresolved `LESSON_CHANGE_REQUEST` copies (2026-09-28 03:10:04-03:16:28 UTC) and the four unresolved `COURSE_CHANGE_APPROVED` copies (2026-09-28 05:44:15-05:44:22 UTC and 2026-09-29 02:09:31 UTC). It returned no rows in those windows. Current CS101 change-request rows exist at other times, but none can be safely joined to these notifications from the stored recipient-only target, NULL correlation/actor fields and generic action URLs. This is additional evidence for an owner-approved mapping/rehearsal hold; no append-only history was mutated. Final status remains **PARTIAL - not release-accepted**.
## N-197 Browser fail-closed resource-visibility proof (2026-10-06)

Using the enrolled Student Browser session, a temporary, explicitly labeled `lesson_resources` row `120002` was attached to published SEXGAY lesson `130025` and pointed at existing asset `3EB32DEA-150D-4724-B42C-2FEBB53BAD16`. SQL identified the asset as `PENDING` with current revision `REJECTED`, reason `Infected: ZIP-Embedded-Executable`. The real Student `Tài liệu` panel still rendered only the four ACTIVE files and exposed no link, preview or download CTA for the rejected resource. A direct Student-scoped URL was separately attempted and Edge returned `net::ERR_BLOCKED_BY_CLIENT` before an application response, so the UI omission is the verified Browser fail-closed result and the direct response remains environment-blocked. The temporary resource row was then deleted by exact ID and label; SQL verified the lesson returned to four resource links, the rejected asset remained `PENDING`, its revision remained `REJECTED`, and it had zero resource links. No file revision, quarantine state, notification row or audit record was mutated. Final status remains **PARTIAL - not release-accepted** because direct Browser response observation and historical owner-approved notification disposition remain open.
## N-198 acceptance checkpoint after temporary Browser fixture (2026-10-06)

The temporary Browser fixture proves the Student-facing file-visibility branch: a linked `PENDING/REJECTED` asset was omitted from the real Student resource panel, while the four `ACTIVE` files remained visible. Exact cleanup restored the lesson to four resource links and left the asset/revision unchanged. Therefore Student UI fail-closed visibility is **PASS for this sampled asset**; the direct download response remains **BLOCKED ENVIRONMENT / UNVERIFIED** because Edge intercepts the URL before the application response. SMTP/inbox remains **OUT OF SCOPE** by owner decision. Historical notification disposition remains open for the two unkeyed groups/17 rows, so the overall audit remains **PARTIAL - not release-accepted**.
## N-199 historical outbox identity recheck (2026-10-06)

Read-only SQL Server inspection found one `email_deliveries` row for each of the 17 unresolved notification events. Those rows preserve recipient email, template code, random dedupe UUID and `PENDING` status, but have NULL subject/body and no `course_change_request_id`, target resource or correlation field. This provides no additional safe business identity for historical repair. SMTP/inbox remains owner-authorized **OUT OF SCOPE**; no delivery was attempted and no outbox/history row was mutated. Final status remains **PARTIAL - not release-accepted**.
## N-243 dispatcher identity root-cause boundary (2026-10-06)

The current source no longer has a callsite that omits both identity mechanisms, so missing-key adoption is not the remaining root cause. Residual uncertainty is semantic: whether each key is derived from the correct durable transition/recipient and whether concurrent/retry behavior converges under the actual database boundary.

## N-242 producer-heavy regression boundary (2026-10-06)

The added 64-case green group reduces uncertainty in the shared authorization, notification, email/outbox, completion and instructor-application producer paths. Because these are fixture-backed service tests, the remaining causal gap is now narrower but still includes live producer-to-role mapping, rapid retry/race behavior and Browser/user-result confirmation.

## N-241 lesson-flag root-cause reconciliation (2026-10-06)

The prior lesson-flag root-cause finding was stale relative to the current worktree. Both current route implementations pass supported service arguments, and the dedicated API regression passes all nine cases, including malformed-body guards, idempotency and rollback. RCA-040/RCA-027 remain historical evidence only; they are not current blockers.

## N-240 API/frontend regression boundary (2026-10-06)

The fresh no-skip API/IDOR and frontend suites support the conclusion that the shared notification transport, authorization and UI contracts are currently regression-covered. They do not remove the root-cause uncertainty for historical identity, unexercised producer semantics, native file chooser behavior or external SMTP/inbox delivery.

## N-239 Admin filter-matrix boundary (2026-10-06)

The complete read-only Admin filter replay establishes that the initial 3-record rendering was a selected `Hệ thống` category, not a missing-record defect. The current UI exposes 15 total records with coherent category partitioning (11 course, 1 assessment, 3 system/security) and zero unread. This strengthens rendering evidence but still cannot prove producer semantics for each historical row.

## N-237 Admin rendering boundary (2026-10-06)

The Admin replay shows that the notification center reads persisted records for the Admin role and presents a zero-unread state with system/security categories. Because the replay did not create a new event, it cannot distinguish producer correctness from existing seeded/history data. The remaining causal gap is semantic producer-to-role coverage, not a missing Admin UI control.

## N-238 Guest route boundary (2026-10-06)

The Guest attempt was redirected to `/auth` before an authenticated notification surface could render. This is consistent with route protection and does not replace the API-level unauthenticated `401` evidence. No SMTP/inbox causal inference is made because mail delivery is outside the deployed test scope.

## N-250 YouTube UI ownership root-cause boundary (2026-10-06)

The Browser/source evidence identifies a frontend ownership gap: the backend scan route and `ApiClient.scanCourseVideos` exist, but no visible course-management control or frontend caller was found. The Lesson Studio validates newly entered links locally/API-checks individual links, which is a different operation from scanning all course videos and notifying the owner. This can leave the broken-video producer without a user-triggered path; whether a background scheduler is intended remains unverified.

## N-249 YouTube route/API boundary correction (2026-10-06)

The disposable route replay removes the earlier API-coverage gap for this producer family: authentication denied the unauthenticated caller and the authorized owner received a truthful success payload after the mocked scan. The remaining boundary is Browser-visible control/result and live external integration, not route authorization or count convergence in this fixture.

## N-248 YouTube producer service/DB replay correction (2026-10-06)

The earlier “no runtime replay” gap is partially superseded: the disposable mocked-oEmbed replay proves service-level detection, owner targeting, persistence and exact-retry convergence. It does not prove the authenticated Instructor route, API response envelope or Browser presentation, and it does not test a live external YouTube dependency. The remaining root-cause boundary is therefore route/UI and external-integration coverage, not the basic service persistence path.

## N-247 YouTube producer verification boundary (2026-10-06)

The gap is missing coverage rather than a reproduced failure: source tracing shows the scan detects a broken oEmbed result, builds a Vietnamese course/lesson warning and dispatches to the course owner, but no current test proves the scan's external-service branches, notification persistence, duplicate retry behavior or user-visible result. This remains an open producer-chain root-cause boundary.

## N-246 producer-key semantic-shape boundary (2026-10-06)

The AST evidence reduces the likelihood of an accidental random/clock key: none of the 34 explicit expressions contains those markers, and all 34 reference either a durable field directly or a helper whose source uses durable IDs/auth-version. The remaining root-cause boundary is semantic, not syntactic: a stable key can still identify the wrong business transition, recipient or message, and only runtime/API/DB replay can prove that.

## N-245 Student content/taxonomy Browser finding (2026-10-06)

The fresh Student Browser replay confirms that the issue is not only a hidden source string: the notification center visibly renders unaccented Vietnamese and low-value seeded copy, while a score notification is grouped under the `Khảo thí` filter even though its visual category label is `ĐIỂM SỐ`. Root-cause classification is currently **content/catalog and taxonomy quality**, with exact producer ownership still requiring row-level API/DB correlation. No historical record was mutated.

## N-244 grading/regrade producer-service regression (2026-10-06)

The current grading/regrade unit group passed **25/25 with zero skips**. This reduces regression uncertainty in score-change and regrade notification producers, but it is not causal proof for every dispatcher callsite, recipient role, duplicate retry or Browser-visible user outcome. The remaining root-cause gap is coverage breadth, not a new failure from this command.

## N-200 stale identity/content recheck (2026-10-06)

The unresolved notification bodies do contain coarse labels: all 13 `LESSON_CHANGE_REQUEST` copies name CS101 and Lesson `Bài 1: Tổng quan về Kiến trúc Web & HTTP Protocol`, but none stores a change-request ID, durable target ID or correlation. The four `COURSE_CHANGE_APPROVED` copies name the same Lesson but their CTA points to course UUID `cf547469-d8b8-43ef-882c-721048826232`, which is absent from the current `courses` table; the current CS101 row has a different public UUID. Current CS101 change-request rows exist, including multiple historical candidates for the same lesson, but none matches the notification event windows. This confirms stale/missing business identity rather than an unresolved title-only query; no historical row was reassigned, deleted or merged. Final status remains **PARTIAL - not release-accepted**.

## N-251 frontend mechanism fragmentation checkpoint (2026-10-06)

The current frontend has multiple user-message owners: 383 shared-toast invocations, separate `UI.alert`/`UI.confirm`/`UI.prompt` surfaces, and one direct `window.confirm` fallback. Four `role="alert"` elements and six `aria-live` attributes are limited to a small subset of the rendered surfaces, while the shared toast id marker is generated by the UI layer. This fragmentation is a root-cause boundary for the still-unclaimed global message catalog and accessibility matrix: static counts can identify surfaces, but cannot establish that every backend error, success, retry or duplicate has one canonical owner and language. No product code was changed from this checkpoint.
## N-252 producer coverage root-cause boundary (2026-10-06)

The earlier producer gap was coverage breadth rather than an uncovered dispatcher callsite. After adding the missing rejection/revision/YouTube fixtures, every direct dispatcher line executed at least once. The remaining risk is therefore semantic and temporal: a covered line may still be reached only for one role, one message branch, one database outcome or one retry ordering. No root-cause claim about duplicate suppression or async state is inferred from 100% callsite line coverage.
## RCA-068 / N-253 - dynamic auth error lacks explicit live-region semantics (2026-10-06)

- **Issue:** The real invalid-login path renders `#auth-error-alert` as an inline error, but the current DOM has neither `role` nor `aria-live`.
- **Evidence:** Fresh Edge submitted invalid credentials; one visible error remained on `/auth` after the approximately 6.45-second interaction/observation sequence. The exact text was `Email hoặc mật khẩu không chính xác.` and the element's `outerHTML` contained only a styled `div` and child spans.
- **Frontend flow:** Auth form submit -> `auth-error-alert` visibility/text update; no shared toast was emitted.
- **Backend/API:** The request returned the login failure presentation; no account or business mutation was observed. This sample does not claim every auth status mapping.
- **Root cause:** The inline error component is not explicitly connected to the accessibility announcement contract used by the four caps-lock warnings.
- **Impact:** P2 accessibility/notification ownership gap; keyboard/screen-reader users may not receive a reliable announcement when the dynamic error appears.
- **Recommended fix:** Add an explicit live-region contract to the dynamic error owner, then add Browser/Node coverage for one visible error, one retry and cleanup on successful login. Do not duplicate it with a toast.
## N-254 RCA-042 continuation - supported chooser API still unavailable (2026-10-06)

The supported file-uploads flow was attempted against the real Instructor Lesson Studio: wait for `filechooser`, click `#btn-choose-doc-file`, then set a harmless absolute-path fixture. The chooser event never arrived and the Computer Use debugger detached after timeout. This rules out the earlier native-picker-only attempt as the sole explanation, but does not distinguish Browser policy from extension/runtime availability. No bypass, CDP policy change or live upload was attempted. The file-selection, rejected-file HTTP response and quarantine-release gates remain **BLOCKED ENVIRONMENT / UNVERIFIED**.
## N-255 producer role-semantic boundary (2026-10-06)

100% direct-callsite execution does not establish correct recipient semantics. The current source explicitly scopes only 17 of 35 producers to a role; 18 rely on a missing or `None` target role, which the shared dispatcher treats as unscoped/broad. That may be intentional for user-specific or admin fan-out paths, but the audit has not yet proven it for each producer, especially the dynamic assessment event and multi-role accounts. This is an evidence gap, not a claim that all 18 paths are defects.
## N-256 focused semantic evidence boundary (2026-10-06)

The selected retry/role tests pass, so the shared dispatcher and several representative fan-outs have no reproduced defect in this group. The unresolved root-cause boundary is coverage breadth: 18 producers still rely on broad/unscoped role semantics, and the focused tests do not prove their recipient correctness, dynamic message ownership or timeout/cancel/unmount behavior.
## N-257 — historical identity boundary and approval packet (2026-10-06)

Read-only SQL Server evidence isolates 17 unresolved historical rows into two
unkeyed copy groups: 13 lesson-request events (`50002–50014`) and four
course-approved events (`60002–60004`, `90006`). One notification and one
email-delivery row exists per event and all event keys are unique; this does not
prove duplicate delivery. The records omit durable request/target/correlation
identity, while the approval CTA carries a stale UUID absent from the current
course table. The root cause is historical identity loss, not permission to
rewrite append-only history. The exact rows and required owner decisions are in
the [approval packet](09_HISTORICAL_NOTIFICATION_APPROVAL_PACKET.md). No
repair, merge, deletion or reassignment occurred; SMTP/inbox remains
**OUT OF SCOPE**.
## N-258 — repeated Edge file-chooser blocker (2026-10-06)

The current Edge tab was controllable and showed the expected Lesson Studio
document input. A second supported file-chooser attempt still emitted no
chooser event within 5 seconds and reset the Browser session. This reproduces an
environment/extension boundary rather than an application upload result; no
file, request or database row was transmitted or changed. The gate remains
**BLOCKED ENVIRONMENT / UNVERIFIED**.
## N-259 — Browser confirms content/catalog symptoms (2026-10-06)

Fresh Instructor Browser evidence shows the `Khóa học` category rendering 16
cards, including repeated `#70014` presentation copies with different reasons,
while `Hệ thống` renders the unaccented maintenance text beside a Vietnamese
security notice. The finding supports the existing root causes around legacy
identity loss and decentralized message catalog ownership; it is not evidence
that all notification producers have been enumerated. No notification state was
mutated.
## N-260 — NULL target-role semantics are a role-view boundary (2026-10-06)

The 18 producer callsites previously described as broad/unscoped all pass a
specific recipient user. The root-cause boundary is therefore not proven
cross-user fan-out; it is that `target_role=NULL` makes a row visible in any
role-filtered view of the same multi-role account. This is appropriate for some
account-level security/role events but needs explicit business confirmation for
route-specific prerequisite, review, intervention, application and YouTube
notifications. The existing tests do not close that producer-by-producer matrix.
## N-261 — confirmed NULL-target-role CTA mismatch (2026-10-06)

The shared query condition `target_role = requested_role OR target_role IS
NULL` is now correlated to live behavior. For the multi-role Admin account,
one NULL-target lesson-review notification with an Admin-only CTA appeared in
ADMIN, INSTRUCTOR and STUDENT REST filters. The root cause is role-view
fallback treating NULL as universally compatible even when the stored action
URL is role-specific. This is a confirmed same-user isolation/UX defect; no
cross-user IDOR or data mutation was observed.
## N-262 — role-filter behavior is hidden by schema documentation drift (2026-10-06)

The runtime role-filter behavior depends on `target_role`, but the canonical
notification data dictionary omits that nullable column and its index/CHECK
constraint even though migration `f6a7b8c0d1e2` and live SQL Server contain
them. This documentation drift weakens review of NULL-role semantics and
contributed to the unresolved N-261 contract boundary. No live schema was
altered.
## N-263 — test oracle is narrower than the business contract (2026-10-06)

The existing three-test role scope passed, but its oracle defines NULL
`target_role` as globally visible and never inspects action URL ownership. The
test suite therefore protects database role filtering for explicit roles while
missing the route-specific CTA mismatch proven by N-261. This is a coverage
gap, not evidence that the live behavior is correct.
## N-264 — N-261 is not an IDOR (2026-10-06)

An independent Student1 JWT replay found no Admin-review CTA under its valid
role filter, and actor-ineligible role filters returned 400. The root cause
remains same-user NULL-target role-view breadth and CTA mismatch, not recipient
authorization failure.
## N-265 — UI route guard is downstream containment, not role filtering (2026-10-06)

The notification click/modal code forwards `action_url` directly to the router;
there is no notification-layer compatibility check. The router's Admin guard
contains the problem only after navigation: a multi-role account can be
auto-switched to ADMIN, while an Instructor-only session receives the warning
`Bạn không có quyền truy cập khu vực Quản trị viên.` and is redirected to the
Instructor dashboard. Fresh Edge reproduced the latter on the exact Admin
review target without mutation. The root cause is therefore upstream role-view
selection/CTA ownership, with the route guard acting only as a late safety net.
