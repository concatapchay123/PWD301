# 08_NOTIFICATION_FINAL_AUDIT

## Authoritative current checkpoint (2026-10-06)

The current worktree contains the eight required audit reports and current inventory/evidence updates through **N-265**. Fresh Browser evidence covers Student, Instructor, Admin and the Guest boundary. The latest disjoint automated verification is **1,613 passed, 0 failed, 0 skipped**: the aggregate run contributed 1,609 non-SQL results and the opt-in SQL Server helper contributed four additional SQL-gated cases, with 13 overlapping non-SQL integration cases not double-counted. Later isolated producer-service regression groups added **90 + 38 + 64 + 25 passed, 0 failed, 0 skipped** without being folded into that disjoint total because their overlap with the aggregate is not fully audited. Frontend Node is **108 passed, 0 failed, 0 skipped, todo 0**. The disposable SQL databases used for the opt-in checks were removed with `audit_database_remaining=0`. N-257 adds the read-only approval packet for the exact 17 historical rows; N-258 rechecks the Edge file chooser and reproduces the environment timeout without selecting a file; N-259 adds fresh category/content evidence; N-260 refines role-scope semantics; N-261 confirms a same-user multi-role CTA mismatch in live REST filters; N-262 records the applied-role-schema versus canonical-dictionary drift; N-263 records that existing role tests do not cover CTA compatibility; N-264 confirms the issue is not cross-user IDOR; N-265 confirms the Browser route guard is only downstream containment and does not repair the upstream incompatible CTA.

The package remains **PARTIAL**, not release-accepted. Current open gates are Browser file chooser/upload permission and direct rejected-file response coverage under the Edge policy, owner mapping/approval plus a disposable repair rehearsal for 17 historical duplicate/orphan rows, and complete semantic notification producer/role/rapid-retry coverage. The application contract has no notification-specific `422` or `502` path; N-230 records this as **not applicable at the Flask boundary**, while any reverse-proxy/upstream `502` remains outside this audit. The sampled notification `404`, `500`, `429`, maintenance `503` and `Retry-After` paths are now evidenced by N-227 through N-229. SMTP/inbox delivery is explicitly **OUT OF SCOPE** because the deployment has no configured mail provider; it is neither a pass nor a failed product gate. Exact global correctness/duplicate/message-language totals also remain unclaimed until the remaining per-case runtime matrix is completed. The latest split result supersedes older 1572/1579/1587/1593 snapshots below; those historical sections remain for traceability only.

## N-250 YouTube Browser/UI ownership checkpoint (2026-10-06)

Fresh Edge Instructor verification opened the real OPS401 course-management page and Lesson Studio. Course management rendered no course-wide scan-video control; read-only source search found `ApiClient.scanCourseVideos()` only in `frontend/assets/js/api.js` with no frontend caller. Lesson Studio's invalid YouTube/Vimeo input rendered `Chỉ chấp nhận liên kết YouTube hoặc Vimeo hợp lệ.` and was cleared without saving. Therefore the YouTube service/API producer is verified in disposable scope, but Browser ownership and user-triggered scan integration remain **OPEN**, keeping the overall audit **PARTIAL - not release-accepted**.

## N-249 disposable YouTube route/API extension checkpoint (2026-10-06)

The same deterministic in-memory probe now covered the route boundary: unauthenticated `POST /instructor/courses/{public_id}/scan-videos` returned **401**; authenticated Instructor owner returned **200**, `success=true`, `broken_count=1`; repeated route/service scans preserved one event and one owner notification. This closes the disposable YouTube service/API path only. A real Browser click-through of the scan control and visible user result remains unverified, so overall status remains **PARTIAL - not release-accepted**.

## N-248 disposable YouTube producer service/DB checkpoint (2026-10-06)

The new `youtube-runtime-probe.py` executed with exit code `0` against an in-memory SQLite database and asserted: valid oEmbed → 0 reports; network error → 0 reports and no notification; broken video → 1 report, 1 `COURSE_LESSON_VIDEO_BROKEN` event and 1 owner notification; exact replay → event count 1 → 1 and notification count 1 → 1. Target/recipient matched the course owner and category was `COURSE`. The probe dropped its disposable schema and did not change live data. This closes the YouTube producer's service/DB branch only; authenticated Instructor route/API and Browser presentation remain unverified. Overall status remains **PARTIAL - not release-accepted**.

## N-247 YouTube broken-video producer coverage checkpoint (2026-10-06)

Read-only source/test inspection confirms the live `COURSE_LESSON_VIDEO_BROKEN` producer in `src/pwd301/services/youtube_validator_service.py` and the Instructor `POST /courses/<course_id>/scan-videos` route. Its UUIDv5 key uses durable course, lesson, video and instructor identity, but no current test file or live API/DB/Browser replay covers valid oEmbed, broken-video notification persistence, network-error suppression, exact retry or user-visible result. This remains **UNVERIFIED**, so overall status remains **PARTIAL - not release-accepted**.

## N-246 producer-key semantic-shape checkpoint (2026-10-06)

An independent AST scan over current Python source classified all **35** direct `dispatch_notification()` calls: **34** explicit `event_key` expressions were durable-identity candidates, **0** contained random/clock markers, **0** were constant or unclassified expressions, and **1** used a prebuilt `event` at `src/pwd301/services/course_service.py:286`. Helper source uses persisted audit, change-request, file-revision, enrollment, attempt or user `auth_version` identity. This closes the static key-shape checkpoint only; it does not prove correct recipient/message semantics, concurrent retry convergence, Browser user result or historical repair. Overall status remains **PARTIAL - not release-accepted**.

## N-245 fresh Student notification-center content/filter checkpoint (2026-10-06)

Fresh Edge Computer Use verification used the visible Student demo login, opened the notification center immediately after the login-success toast, and exercised the read-only category filters. The Browser rendered `Tất cả=13`, `Khảo thí=7`, `Khóa học=2`, `Hệ thống=4` and `Chưa đọc (0)`. It also visibly reproduced sampled content-quality defects: the unaccented system text `Thong bao bao tri dinh ky He thong PWD301 hoat dong on dinh tren tat ca cac module.`, plus low-value seeded strings `heo peppa caccaccac` and `bucutaodi thật là bá khí`. No delete, mark-read, refresh, upload or other business mutation was performed; the session was logged out. This strengthens real UI/content evidence but does not establish global counts or close producer/API/DB correlation. Overall status remains **PARTIAL - not release-accepted**.

## N-244 grading/regrade producer-service regression checkpoint (2026-10-06)

The fresh isolated command `PYTHONPATH=src python -m pytest -q tests/unit/test_grading_service.py tests/unit/test_regrade_service.py` returned **25 passed in 26.49s**, exit code `0`, with no skipped tests. This strengthens fixture-level grading/regrade producer evidence only; it does not close complete semantic producer/role/rapid-retry coverage, Browser file/quarantine verification, historical owner-approved disposition or SMTP/inbox scope. Overall status remains **PARTIAL - not release-accepted**.

## Latest moderation checkpoint — overall goal still PARTIAL

Inventory now records **139 distinct case IDs** (not 139 distinct delivered events). Fifteen new full-field rows include the actual Admin Browser flag workflow, ten REST branches and four sub-admin notification/permission paths, with all required core/additional fields and fresh SQL correlation. Existing older rows still require full-field enrichment and unsampled runtime verification.

New **P1 RCA-040**: valid Admin lesson flag fails on both web and REST because the duplicated routes construct AuditEvent with an unsupported payload_json argument and omit required actor-role metadata. Browser displays an English 500 message; SQL persists no flag/audit/event/notice. Malformed string/list bodies on the REST flag route additionally prove the remaining **P1 RCA-027** type-guard gap. F-024/F-025 are proposed minimal corrections, not implemented. Sampled Guest/Instructor/Student denial and empty/4-char/missing-target guards passed without mutation.

The ten-case audit probe reports **6 expected status matches, 4 failed expectations, 0 skipped; exit 1**. The separate sub-admin probe reports **8 checks, 1 failed expectation, 0 skipped; exit 1**. These new known failures are separate from the earlier **1579 Python + 101 Node passed, zero skipped** suite snapshot. Green existing tests do not prove complete business coverage. [Exact evidence](flag-runtime-evidence.md) distinguishes Browser, HTTP, SQL and source-only transaction risks. No product code, live database, permissions or main runtime was modified for this checkpoint.

The owned grading DB/server were deliberately recreated after the previous cleanup for this new probe. Their later cleanup must be verified explicitly; the historical remaining=0 paragraph below does not describe a currently running fixture. Release/whole-goal completion remains unclaimed.

## Latest post-fix moderation checkpoint — 2026-10-05

The lesson-flag defect is now repaired and independently verified. Both web and REST routes use the canonical audit service, validate malformed JSON before field access, and commit the flag/audit/owner-notice chain atomically. Focused TDD coverage is **6 passed, 0 failed, 0 skipped**.

Fresh SQL Server replay: the ten-case flag probe returned **10/10 expected statuses, 0 failed, 0 skipped, exit 0**. Exact `abcde` returned 200 and persisted the lesson flag, audit, notification event and owner notice. Visible Browser replay of the same exact boundary returned HTTP 200 and the Vietnamese success toast; SQL immediately afterward showed one of each durable record. The sub-admin probe returned **8/8 expected checks, 0 failed, 0 skipped**: the course-review sub-role succeeded and the other three scopes were denied without moderation mutation.

This closes the previously reported lesson-flag RCA-040/RCA-027 path, but it does not constitute whole notification release sign-off. Duplicate/retry idempotency, outbound email, upload/download Browser acceptance, legacy repair and complete producer/role coverage remain open as listed below.

## Sub-admin Browser/SQL/REST continuation

Four disposable sub-admin identities were exercised in Browser with the visible login form. Each had one SQL-persisted `USER_ROLE_ASSIGNED` audit and one `ROLE_CHANGED` notice, saw the role-specific body, marked the notice read and followed the correct CTA route. REST list replay confirmed one own item and `unread_count=0` for each identity. The three non-course-review sub-roles correctly received 403 with no moderation-state mutation. The course-review sub-role was authorized to reach the flag flow but exact five-character input returned the already confirmed RCA-040 500, so the allowed moderation outcome remains failed. No duplicate notice, rapid-repeat behavior or outbound delivery was inferred from this run.

Cleanup is now verified: audit server port 5105 has zero listeners and the exact disposable database cleanup returned `audit_database_remaining=0`. The main runtime/database and user data were not touched.

## Checkpoint kiểm thử không skip và an toàn môi trường (2026-10-05)

Checkpoint này có ưu tiên hơn các số liệu 1572/1578 và các trạng thái lịch sử bên dưới. Lượt chạy ban đầu có 1576 passed, 2 failed, 0 skipped; hai test upload tài nguyên và lease bài thi trả 503. Chạy riêng cho 2 passed; chạy lại toàn nhóm API trước sửa fixture cho 375 passed. Probe có restore marker trên thư mục audit riêng tái hiện đúng cả hai phản hồi MAINTENANCE_MODE_ACTIVE/503. Việc nhóm test dùng chung storage/quarantine/backups với workspace là lỗi cô lập đã được chứng minh; không quy kết chắc chắn nguyên nhân của lượt lỗi ban đầu khi chưa lưu response của lượt đó.

Fixture app nay dùng ba thư mục con riêng trong tmp_path. Regression mới thất bại với các root E:/PWD301/storage, quarantine, backups trước sửa. Sau sửa, probe vẫn giữ marker bên ngoài và 27 test upload/lease/backup/restore/maintenance đạt; không tắt maintenance hay fail-closed. Marker probe đã xóa. Test mới dùng nhầm một route không tồn tại lúc đầu; lỗi harness 404 đó đã sửa, không tính là lỗi sản phẩm.

Cô lập filesystem lộ thêm lỗi rescan: kiểm tra substring “infected” trên toàn đường dẫn nhầm thư mục cha với vùng chứa tệp nhiễm. Regression hiện hữu thất bại hai lần trước sửa; nay so sánh parent đã resolve với get_file_infected_root(), kiểm tra tệp được chuyển, key infected/hash và Student vẫn bị từ chối 403. Focused stress/file/isolation: 27 passed. Lượt split cuối sau sửa cho **1579 passed, 0 failed, 0 skipped**, khớp **1579 tests collected**: root298 + unit632 + API375 + security233 + concurrency13 + E2E12 + integration16. Frontend độc lập: **101 passed, 0 failed, 0 skipped**. Không cộng các lượt focused trùng vào tổng. Đây là kết quả các nhóm chạy đủ, không phải một aggregate verifier được tuyên bố pass; lượt aggregate lịch sử bị stall vẫn không được tính.

SQL-gated integration hiện tại: 16 passed, 0 failed, 0 skipped, gồm migration, ROWVERSION race và hai loại revision trên SQL Server thật. Hai DB migration/race tạm đã xóa, remaining=0. Browser Student4 đã đăng xuất về form login; server audit 5105 dừng; DB grading tạm cũng đã xóa, remaining=0. Không migrate/restart DB/runtime chính; fixture có thể dựng lại bằng prepare.

Audit notification vẫn PARTIAL, không phải release sign-off. Những đoạn dưới nói “chưa sửa”, “pending replay”, “1572 current” là snapshot lịch sử, không được dùng thay checkpoint mới.

## Current acceptance boundary and handoff

The automated non-skip requirement is satisfied for the collected current worktree: the latest disjoint verification is **1,613 Python/SQL cases passed, 0 failed, 0 skipped**, and the frontend Node suite is **108 passed, 0 failed, 0 skipped, todo 0**. The aggregate wrapper itself reported 1,609 pytest passes plus four SQL integration skips before the separate opt-in SQL helper ran; those four cases are included only through the helper, not counted as wrapper passes. Report07 records commands, group counts, actual timings and the preceding failures/replays. The grading-chain changes are verified by a real disposable SQL Server and Browser replay, not by SQLite alone.

The overall notification goal remains active/PARTIAL. Required remaining gates include:

- Reconcile legacy ESSAY attempts with the current four-type authoring contract; correct false answer/point presentation and determine the supported Instructor manual-grading UI.
- Verify/fix durable broadcast idempotency without hiding duplicate rows at read time; complete timeout/out-of-order and rapid-action coverage.
- Normalize envelopes/message ownership only after consumer impact review; fill the inventory's required fields and run unverified producer/role boundaries.
- Complete Browser upload/download under supported browser permissions; canceled transfer/chooser denial are not passes and must not be bypassed.
- SMTP/inbox delivery and retry are **OUT OF SCOPE** for this deployment because no mail provider is configured; no real external mail was sent by this audit.
- Decide explicit historical OPS401 orphan-notification repair/replay and deploy the new migration through the normal approval process; no automatic live repair/migration was done.

Owned grading Browser session was logged out, audit server5105 stopped and three exact disposable audit DBs removed. These fixtures are reproducible through the supplied script; live user data was not removed. Manual review/static checks passed within the stated scope, but OCR automation remains unavailable without its configured provider. No release, full WCAG, mobile or complete system-notification coverage is claimed.

## Latest verified grading continuation (2026-10-05)

Current grading delivery/CTA evidence is stronger than the historical B-007 paragraph below: real disposable SQL Server manual grade18/30 now emits one first-release notice; unchanged retry emits no duplicate. Corrected answer regrade changes18→28/30 and emits one change notice. Duplicate job trigger preserves job/history and exactly two grading notices. Browser Student4 saw both notices and followed the change CTA to the correct28/30 result.

This required three backend-chain corrections in addition to the earlier continuation: a shared result-change notifier used by the worker, a new canonical-enum migration and inactive revision construction before child insert. Applied migrations and protective triggers were not weakened.143 focused backend and16 integration tests passed with zero skips; final full split verification is1579 passed,0 failed,0 skipped, so historical1572 is not the current-code total.

Status remains PARTIAL. A pending ESSAY still has no grading action in the Instructor modal, and the Student detail renders a stored/graded essay as unanswered0 points despite the correct total. These are confirmed defects/contract discrepancies, not skipped tests. Upload/download, actual email delivery, broadcast duplicate persistence, envelope consistency and complete inventory/workflow coverage remain open. No main-runtime migration or historical data repair was performed.

## Current continuation correction — enrollment transaction and aggregate (2026-10-05)

A red regression demonstrated that `enroll_student()` could commit the ACTIVE enrollment before dispatching notifications, leaving staged `STUDENT_ENROLLED` event/recipient rows absent after session close. The service now dispatches both intended recipients before its final commit. The focused enrollment scope reports **20 passed, 0 failed**. Completed split pytest verification across all collected groups reports **1572 passed, 0 failed, 0 skipped**; the two SQL Server gates ran against disposable databases and both database pairs were removed. A later aggregate attempt stalled at 49% and is not counted as a pass.

The historical live OPS401 rows with events but no linked notifications remain a confirmed persisted-data gap and require an explicit repair/replay plan. A fresh Student4 → DSA201 live replay now passed: Browser showed enrollment success, Instructor2 showed the owner notice, and SQL Server correlated ACTIVE enrollment `110003`, events `140010/140011` and linked notifications `150083/150084`. Browser download remains unverified: CDP saw download initiation but the transfer ended canceled with an incomplete `.crdownload`; backend HTTP download success is not equivalent to Browser acceptance. The audit therefore remains partial and is not a release sign-off.

Live course-review correction: Instructor1 submitted CS201, Admin approved it in the current live runtime, and Instructor1 received the approval notification. SQL Server confirmed CS201 `APPROVED`, `approved_by_user_id=1`, one `COURSE_APPROVED` event and one linked owner notification. A second live staged update (`#60002`) was rejected through the real Admin review page with a non-empty reason; SQL Server confirmed `REJECTED`, event `140009` (`COURSE_CHANGE_REJECTED`) and linked notification `150082`, while the owner Browser rendered the exact reason. This supersedes the historical live Admin-authorization blocker for both current approve and reject branches. The fresh enrollment replay also closes the current Browser/API/DB recipient correlation, while the historical OPS401 orphan rows, file, email and duplicate gates remain independently assessed.

## Final status

**PARTIAL – CHƯA ĐỦ ĐIỀU KIỆN NGHIỆM THU**

Không được đánh dấu hệ thống notification đã đạt vì các gate cross-role, API/DB correlation, duplicate/rapid behavior và một số browser/file/email paths vẫn chưa được chứng minh đầy đủ. SQL Server migration/concurrency đã pass trên database tạm, nhưng các bằng chứng runtime khác vẫn cho thấy lỗi hoặc khoảng trống nghiệm thu.

RCA-023 preserves historical modal-leakage evidence. Current source has overlay teardown; the latest Browser replay passes modal Escape and logout/Back auth stability, but exhaustive logout with each overlay still mounted remains unverified. Current and historical evidence are distinguished below.

## What is established by direct evidence

## Current post-fix evidence (2026-10-05)

Completed split pytest verification is **1572 passed, 0 failed, 0 skipped** across root-level, unit, API, security, concurrency, E2E and integration groups. The latest frontend suite is **101 passed, 0 failed, 0 skipped**, including notification loading/degraded states and three real auth-route regressions. The three-role Browser outage/retry recovery also passed. These do not close the remaining notification DoD gates.

Continuation scope covers seven unique product files listed in the fix plan. The newest correction is in `router.js`: unauthenticated auth/login routes render auth before the role-home fallback. Three regressions failed before the guard and passed after it. The speculative `frontend/index.html` BFCache change and its two mock-only tests were removed. The latest focused results are **101 frontend tests passed, 0 failed, 0 skipped**, **20 enrollment tests passed, 0 failed**, and a passing malformed-payload API regression. The completed SQL-gated split runs cover backend changes; the final auth correction is frontend-only.

The dirty worktree contains earlier user remediation plus the scoped audit-continuation fixes; none were committed. Focused verification returned `28 passed, 0 failed` for notification unit/API/IDOR tests and `53 passed, 0 failed` for the combined seed/auth/notification scope. A local HTTP matrix logged in all seven demo accounts with HTTP 200 and the expected primary role. Edge form login passed for Student (`#/student/dashboard`), Instructor (`#/instructor/dashboard`) and Admin (`#/admin/governance`); the Admin UI showed `ADMIN CHÍNH`.

The current live Admin session also reports `is_primary_admin=true`, `admin_sub_role=ADMIN_PRIMARY`; `/admin/users` and `/admin/courses/pending` returned HTTP 200. This supersedes the historical live Admin-primary authorization blocker in the pre-fix evidence. The historical dismiss failures are likewise baseline-only after the focused 28/28 retest.

Fresh live JWT malformed-payload probes also supersede the pre-fix notification mutation behavior: broadcast JSON string, mark-all JSON list and preferences JSON string each returned HTTP 400 `VALIDATION_ERROR`, with no valid mutation. The remaining issue is envelope consistency, not an observed current 500 for these three type boundaries.

Fresh Browser replay: Instructor1 opened CS201 settings, closed the modal with Escape, then logged out through the account menu. Logout and Back settled at `#/auth`; CDP confirmed a real router, `currentUser=null`, `_isRouting=false`, login visible and no visible course/topbar/modal. The earlier account-menu click while the modal was open may have closed its backdrop first, so it does not independently prove teardown with a mounted overlay. Full overlay-at-logout coverage remains open.

The BFCache conclusion is withdrawn: the earlier read-only DOM evaluation could not determine page-global runtime state. Actual CDP inspection showed the router existed. Source and failing actual-router regressions established that unauthenticated auth routes reached the role-home fallback. The guard correction is verified by the 101/101 frontend run and the live logout/Back replay; no BFCache-specific fix or acceptance claim remains.

The latest completed split verification reports `1572 passed, 0 failed, 0 skipped`; both SQL Server gates executed and passed in the integration group against disposable databases, and both disposable databases were cleaned up. A later aggregate attempt stalled at 49% and was terminated, so it is not counted as a pass. The scoped staged-lesson upload, notification degraded-state, graded-result CTA, enrollment CTA, enrollment transaction persistence and malformed-payload fixes were covered by the split suite. Persisted broadcast duplicate rows/events, historical enrollment-notification gaps, canonical envelope drift, upload/download, email delivery and complete Browser mutation coverage remain unresolved or unverified, so the notification audit is still not a release acceptance.

The three quick-demo shortcuts were replayed after the auth-route correction in clean sessions. Instructor1 reached `#/instructor/dashboard`, Student1 reached `#/student/dashboard` with `HỌC VIÊN`, and Admin reached `#/admin/governance` with `ADMIN CHÍNH`; actual CDP runtime confirmed Student/Admin roles and idle routing. This closes the current three-shortcut gate, while earlier ambiguous/stalled observations remain historical. Sessions were logged out afterward.

- Local app responds at `/` and `/health`.
- Login UI exposes Student, Instructor and Admin demo paths.
- A valid Admin-only broadcast was submitted in the browser; the UI showed delivery to 1 user, the unread badge increased 2 -> 3, and the exact notification appeared in the dropdown.
- A double-click on a second Admin-only broadcast produced two identical success toasts; the API exposed one item (`total=7`, `unread_count=4`), but direct SQL Server correlation found 2 notification rows and 2 distinct event IDs for the same title. Duplicate persistence is therefore confirmed and was masked by API/UI dedupe.
- Static inventory found 37 backend notification producer callsites and 384 frontend toast callsites.
- Unauthenticated probes across the sampled REST notification list/action families correctly returned HTTP 401, but the error body was not the required full `{success:false,data:null,error}` envelope. The separate web-session unread-count endpoint returned HTTP 200/0 while unauthenticated, so this statement does not cover every notification surface.
- Browser login was authorized and executed for Student, Instructor and Admin demo accounts. Notification center behavior was observed across all three roles.
- Student mark-one, mark-all, category filters, delete/refresh, role switch, logout/revisit, catalog search, notification-center `Esc` close, Instructor empty create-course validation/cancel and Admin empty-broadcast validation were exercised. The mark-one assessment notification changed to `Đã đọc` in Browser and its live SQL Server row `id=27` had `read_at=2026-10-04T11:43:08.566000`. A fresh Student browser session showed 6 notification items and no pagination controls; a second semantic refresh attempt hit a detached DOM node and a coordinate retry produced no new UI signal, so rapid/idempotency and network-failure behavior remain unverified. Fresh logout evidence confirmed Back cannot reveal protected content, but the stale protected hash remains in the URL.
- Historical logout retest: a fresh Instructor2 session opened DSA201 `Cài đặt & Học vụ` / `Chuẩn đầu ra & Học vụ`, then logged out. The login form appeared behind the still-mounted modal, which continued to expose SLO text and a prerequisite request until manual close. This remains pre-fix traceability evidence; the current modal-cleanup pass and the still-open stale-hash/back boundary are recorded in the current correction below.
- Instructor valid course/unit/lesson authoring, course review submission, sample exam publication, Student waiting-room start, autosave, submit and result rendering were exercised.
- The Student result page showed 100/100 and 2/2 correct after an explicit submit confirmation; fullscreen lockdown simultaneously recorded 1 violation.
- Current B-007 evidence is PARTIAL: Instructor2 reached DSA201 gradebook through course-management, saw 1 submission at `100 / 100`, and opened a detail modal with only 2 `SINGLE_CHOICE` questions and no manual-grade/regrade control. Fresh host DB showed 2 `GRADED` auto-graded attempts, 0 pending grade rows and empty `question_corrections`; the isolated regrade API suite returned 4 passed tests. Manual-grade/regrade notification remains unverified, and the earlier pending-ESSAY snapshot is not reproducible.
- The prerequisite workflow was initially captured while still pending; that snapshot is superseded by the continuation correction below. The continuation confirmed approval in Browser plus API/DB correlation, and confirmed rejection state/reason plus the outbound notification through a renewed CSRF-authenticated HTTP session. Browser completion of the native rejection prompt remains partial.
- B-013 is a confirmed persisted business-notification failure: Instructor1 Browser showed OPS401 with 2 students and 3 unread notifications but no enrollment notice; host DB showed active OPS401 enrollments plus four `STUDENT_ENROLLED` events targeted to owners 2/3, while every event had zero linked `Notification` rows. A fresh rollback-only service reproduction succeeded, so the current triggering exception remains unverified.
- File/media rejection is backend-proven only: invalid Student evidence `.exe` and invalid Instructor course-image bytes both returned safe HTTP 400 validation responses; focused fail-closed tests returned `20 passed, 16 deselected`, media-limit tests returned `77 passed`, and live DB had no non-clean asset. Edge file selection and pending/quarantine download coverage remain blocked/unverified.
- Authorization boundaries also have backend evidence: Student attempts to call Admin lesson-flag, user-suspend and role-assignment routes returned HTTP 403 `FORBIDDEN`. That sentence is a pre-fix baseline; the current live Admin login now reports `ADMIN_PRIMARY` and the Admin queue/user endpoints return HTTP 200, while successful notification-producing Admin mutations still need their business/DB correlation rerun.
- Enrollment boundary evidence is negative: the valid OPS401 enrollment path succeeded, but the focused enrollment suite returned `16 passed, 1 failed` because a capacity-1 second enrollment did not raise `EnrollmentCapacityExceededError`. Source inspection confirms the service explicitly follows an unlimited-capacity policy and has no `locked_course.capacity` guard, conflicting with the test/business contract; success/notice semantics are therefore not complete.
- Student enrollment of OPS401 showed a confirmation toast, `Đã ghi danh` card state and dashboard growth from 2 to 3 enrolled courses; duplicate/capacity boundaries remain open.
- The course resource PDF download was retried from the visible DSA201 `Tải về` link; the Browser stayed on the lesson page and no recent file appeared in the local Downloads folder. The authenticated backend still returns HTTP 200/application-pdf/1,213 bytes, but Browser delivery remains blocked/unverified.
- The authenticated backend download itself returned HTTP 200 with `application/pdf`, 1,213 bytes and attachment disposition; only browser-delivery acceptance remains blocked.
- Historical pre-fix Admin review evidence showed `0 Khóa học chờ duyệt` after Instructor saw `Chờ duyệt`; the authenticated `/admin/courses/pending` call returned HTTP 403 and `/auth/login` reported `is_primary_admin:false`. This was an authorization failure rendered as an empty state, not proof of zero data. The current post-fix recheck is recorded above.
- Historical pre-fix source plus SQL Server inspection resolved the Admin drift: the seed source expected `SUB_ROLE:ADMIN_PRIMARY`, but the old live `ADMIN` role link stored `Baseline root administrator initialization`. The current runtime now reports `admin_sub_role=ADMIN_PRIMARY` and `is_primary_admin=true`.
- A disposable SQL Server runtime (`PWD301_AUDIT_ADMIN_20261004`) was migrated and seeded from the current source. Browser login showed `ADMIN CHÍNH`, the queue showed 1 pending `CS301`, approval produced the success toast and queue count 0, and direct DB inspection showed `status=APPROVED` with `approved_by_user_id=1`. After resetting only that disposable fixture, the browser request-edit/reject path produced the expected feedback and direct DB inspection showed `status=DRAFT` with no remaining change request. This validates the corrected seed/authorization path, not the live `PWD301` database.
- A second fresh Admin session reproduced the same empty queue and primary-admin-only denial; direct `/auth/me` navigation was blocked by Edge, so the identity payload remains unverified.
- Result PDF export was attempted from the visible 100/100 result page, but the Browser download watcher timed out after 8 seconds without verifiable download evidence.
- Runtime evidence shows near-duplicate notification messages, an ambiguous Student demo default role, English RBAC error copy with repeated background warnings, and an IP-like value rendered in a security notification. Source tracing confirms the Student demo button supplies credentials only, while login landing follows the highest assigned role; the live account currently has `STUDENT,INSTRUCTOR`. The IP-like value is confirmed in the demo seed payload (`src/pwd301/seeds/demo.py:1224-1240`), so a fresh request-IP producer remains unproven; the RBAC copy is constructed at `src/pwd301/blueprints/admin/routes.py:230-236` and `:288-294` and forwarded by `frontend/assets/js/api.js:98-108`.
- Authenticated API capture for all three roles confirms HTTP 200, but also confirms the web payload lacks `data`, mixes `preferences` into the list response, emits `deleted_at:null`, and contains role-specific duplicate event identities. Source tracing confirms the REST and web routes serialize separately. The frontend fallback chain was corrected in this continuation to throw `NOTIFICATIONS_UNAVAILABLE` and render an explicit degraded/retry state after all notification routes fail.
- Historical targeted notification baseline: 26 passed, 2 failed in 16.54s; current post-fix rerun: 28 passed, 0 failed in 15.94s.
- The two notification failures are deterministic dismiss contract regressions: current `deleted`, expected `dismissed`; a fresh direct rerun of the two failing tests reproduced both failures in 1.24s.
- Latest frontend suite: **101 passed, 0 failed, 0 skipped**. Regression coverage verifies degraded, loading, retry and stable unauthenticated auth-route behavior; speculative BFCache tests were removed.
- Historical aggregate verification ran to completion via the repository verifier with a process-scoped PowerShell execution-policy bypass: **1546 passed, 17 failed, 2 skipped in 811.82s**. Direct unsigned-script invocation was blocked by local policy. The latest completed split verification is recorded below; the historical result is retained for traceability only.
- The valid broadcast was correlated across browser and HTTP: `event_type=SYSTEM_BROADCAST`, `category=SYSTEM`, matching body, `is_read=false`, `total=6`, and `unread_count=3`. This is one Admin-only path, not proof of retry/idempotency or all-audience correctness.
- An authenticated Student pagination probe returned two non-overlapping pages, while a tampered `role=ADMIN` query returned Student-owned items and no Admin audit broadcast; no cross-user leak was observed, but the role parameter's intended semantics remain unclear.
- Admin email retry authorization was exercised through `POST /admin/emails/retry-failed` with `max_emails=50`; it returned HTTP 200 and `retried_count=0`. This proves the empty-queue response path, not email delivery.
- Fresh direct API duplicate-submit evidence strengthened the boundary matrix: Student1 replayed existing GRADED attempt `2c6ef2d5-f15f-4a36-b132-649facecc94f` with its stored idempotency key and received HTTP 200 with `is_idempotent_replay=true`; a different key returned HTTP 409 `SUBMISSION_CONFLICT`. This proves assessment-submit idempotency only, not notification broadcast idempotency.
- Authenticated Admin server validation for a broadcast missing `title` returned HTTP 400 with `VALIDATION_ERROR` and no write; its error envelope still lacks `success:false,data:null`.
- The course-cover upload UI exposed an enabled image file input after the audit course was returned to DRAFT, but Edge blocked `fileChooser.setFiles` with `Not allowed`; extension file-URL permission was not changed, so upload remains unverified.

- Accessibility partial observation: the live notification center exposed named filter buttons, per-item `Xóa thông báo` controls and `Làm mới` in the accessibility tree; `Escape` closed the open center. A fresh Student DSA201 keyboard retest moved `Tất cả` -> `Chưa đọc` -> `Tất cả`, skipping `Khảo thí`, `Khóa học` and `Hệ thống`, so full keyboard focus order or screen-reader conformance is not established.
- Fresh direct API probe: JWT Student login returned 200; unauthenticated list/count/preferences/mark-all calls returned structured 401 `UNAUTHORIZED`; authenticated list returned 200 with `success`, `items`, pagination and counts but no `data`; preferences returned only `preferences`; invalid read/dismiss/delete returned structured 404, wrong-method GET returned 405, and empty preference update returned 400. Student attempts at broadcast/email-retry returned 403 without mutation. `role=ADMIN` returned 5 Student-owned/non-admin items versus 6 unfiltered items, leaving role-filter semantics ambiguous but showing no cross-user leak in this sample.
- The web-session boundary is inconsistent with the REST boundary: unauthenticated `/auth/notifications` returned 401, but `/auth/notifications/unread-count` returned 200 with `success=true,unread_count=0`; `/auth/notifications/preferences` returned 405 because no such route is exposed.
- Cross-role JWT read-only probe: Student and Instructor logins returned 200 with API roles `STUDENT,INSTRUCTOR`; Admin returned 200 with `STUDENT,INSTRUCTOR,ADMIN`. The pre-read-probe notification snapshot was Student 6/unread 0, Instructor 5/unread 3 and Admin 7/unread 4. This is role-specific read evidence only, not complete producer/recipient proof.
- Fresh read-only SQL Server recheck: OPS401 had 2 ACTIVE enrollments; 4 `STUDENT_ENROLLED` events targeted users 2/3 and each had zero linked `Notification` rows. The double-click broadcast title still grouped to 2 notification rows and 2 distinct event IDs for one recipient. These business-data findings remain confirmed.
- Enrollment root-cause qualification: a rollback-only SQL Server run of the real enrollment path with commit-simulation (`flush()` + `expire_all()`) for PY301/student3 returned `ACTIVE`, created 2 linked `STUDENT_ENROLLED` notifications in-transaction, emitted no warning, and rolled back; follow-up DB counts remained at 4 persisted events and 0 linked notifications. The OPS401 gap is confirmed in persisted data, but the current triggering exception is not reproduced.

## Current continuation correction — Student-view mark-all

A fresh Browser Student-view session for the dual-role Instructor2 account showed 4 unread notifications. One `Đã đọc tất cả` action changed the badge to 0 and displayed the success toast. A UI double-click attempt hit a detached DOM node before a second request could be established; two immediate JWT mark-all POSTs both returned `success=true, marked_count=0`. This adds scoped API no-op evidence but leaves Browser rapid-click behavior unverified.

## Current continuation correction — prerequisite approve/reject

The prerequisite workflow is now stronger but still not a full Browser acceptance pass. Instructor2 Browser approved request id `1` from DSA201 academic settings and showed `Đã phê duyệt yêu cầu môn tiên quyết!`. Authenticated follow-up confirmed `APPROVED`, an `OPS401 -> DSA201` prerequisite link, and an Instructor1 `COURSE_PREREQUISITE_APPROVED` notification. Instructor1 then created request id `2` for `PY301 -> DSA201`; Instructor2 Browser displayed it and opened the native rejection prompt. The prompt could not be completed reliably in the Browser automation session, so a fresh authenticated CSRF session completed the reject and returned `REJECTED`; Instructor1 received `COURSE_PREREQUISITE_REJECTED`. The API/DB business outcomes pass, while the final Browser prompt-submission step remains partial.

## Fresh Browser evidence update

The fresh Admin Browser retest adds direct role/filter evidence: login succeeded and the notification center showed 7 items with 4 unread. `Khảo thí` rendered 1 item, `Khóa học` rendered 2 CS301 approval items with different titles, and `Hệ thống` rendered 4 items including both audit broadcasts plus the IP-like security alert. The Admin governance page still showed the English primary-administrator authorization error. This strengthens the duplicate/copy and RBAC findings; it does not repair live data or establish primary-admin access.

A subsequent three-account Browser retest confirmed the login boundary again: `student1@pwd301.local` logged in successfully but landed in the Instructor dashboard because the dual-role account defaults to Instructor; `instructor1@pwd301.local` logged in successfully and rendered the Instructor dashboard plus the existing prerequisite-rejection toast; `admin@pwd301.local` logged in successfully and rendered the Admin governance route but still showed the primary-administrator authorization error. Each session was logged out before the next login, and the final Admin session was closed cleanly. This proves account authentication, not complete role authorization or notification correctness.

Static discovery plus a read-only Node VM load found two result/appeal callsites (`student.js:5722,5830`) invoking `UI.alert(...)` while the loaded `ui.js` reports `UI.alert=undefined`, `UI.openModal=function` and `UI.confirm=function`. The fresh result page did not expose the scale or pending-appeal trigger, so this is recorded as an unverified P2 static gap rather than a confirmed Browser failure; native `window.alert(...)` fallbacks remain in `controllers.js:30,184`.

Fresh direct Admin JWT boundary evidence now covers category/status/pagination: unfiltered total 7/unread 4, SYSTEM 3, COURSE 2, ASSESSMENT 1, unread-only/status-unread 4, per-page clamping and an empty page-999 result. The unread badge is global rather than category-scoped; this is recorded as current contract semantics, not counted as a delivery failure.

Fresh validation-boundary evidence also passed the fail-closed SECURITY preference rule: disabling `SECURITY` email returned HTTP 400 `VALIDATION_ERROR` with an actionable mandatory-security message; before/after reads showed `email_enabled=true,is_mandatory=true` unchanged and unread count stayed at 2. Unknown preference category, empty preference payload, and missing broadcast title/body were rejected with HTTP 400; an unknown `mark-all-read` category returned a 200 no-op with `marked_count=0`. These checks strengthen input/error coverage but do not repair the canonical envelope or delivery gaps.

Fresh keyboard evidence adds **RCA-026**: the notification center's visible category filters are skipped by the observed keyboard tab sequence, while `Escape` remains functional. This is tracked as a confirmed P2 accessibility/UX finding.

Fresh malformed-payload evidence adds **RCA-027**: Admin broadcast with a JSON string and mark-all with a JSON list both returned HTTP 500 `INTERNAL_ERROR` with correlation IDs; before/after notification data stayed total 7/unread 2 with identical IDs. Preferences with a JSON string correctly returned HTTP 400. This confirms a mutation-route type-validation defect without a successful business-data mutation.

Current remediation correction for **RCA-027**: the historical malformed-payload 500s remain recorded above, while the new focused API regression now returns HTTP 400 for the broadcast JSON string and mark-all JSON list after explicit top-level object validation. No malformed business mutation is accepted. The canonical error envelope remains open.

Current remediation correction for **RCA-030**: the historical transient empty-state Browser observation remains valid, while the new deterministic Node regression now keeps the skeleton visible during empty-cache revalidation and renders the notification only after a successful response. A post-fix live Browser timing replay is not claimed.

Fresh read-only Node VM evidence originally confirmed **RCA-006**: forcing all three notification route fallbacks to reject returned `{items:[],total:0,unread_count:0}`. The current continuation fix now throws `NOTIFICATIONS_UNAVAILABLE`, preserves the distinction between empty and unavailable data, and renders a retry state in the router; the new Node tests pass and no product/runtime data was mutated by the probes.

Fresh Admin invalid-filter evidence also returned the same 7 actor-owned items for `role=STUDENT|INSTRUCTOR|ADMIN`; unknown `status` and non-boolean `unread_only` values were silently ignored, while an unknown category returned an empty set. This is a P2 contract ambiguity, not a demonstrated IDOR.
The previously open HTTP 429 gate is now directly evidenced: a unique synthetic login email with a wrong password returned five `401` responses, then `429` with `Retry-After: 60`. This did not target a demo account or create business data; the temporary limiter state is not a notification result.
Rapid mark-one-read is also now directly evidenced for Admin: repeated PATCH on the same already-read item returned `is_read=true` with an identical `read_at`, and unread count remained 2. This is a scoped idempotency pass and does not generalize to dismiss or broadcast.
The earlier Admin filter totals of 4 unread are explicitly a pre-read-probe snapshot; the audit's subsequent two read-transition probes changed two seeded notifications to read, so later current unread counts are 2. Historical counts are retained with their time scope rather than presented as one invariant total.

Audit-side state disclosure: the two seeded Admin notification rows changed by the read-transition probes are not the only live-fixture mutations anymore. This continuation intentionally approved request id `1` (creating the `OPS401 -> DSA201` prerequisite link and approval notification) and created/rejected request id `2` (creating the rejection notification). No schema was changed by these fixture probes; the scoped instructor staged-lesson upload source fix is documented in the current retest. The remaining SQL checks were read-only, rollback-only, or executed against disposable fixtures; these business-fixture changes are disclosed and are not a release baseline.

The Student-view mark-all probe also changed four Instructor2 notification rows from unread to read. The second UI dispatch was not proven because the Browser node detached; the two JWT no-op calls did not add further state changes.

## Current Browser network-failure correction

On `http://localhost:5000`, clean logout/login sessions for Admin, Instructor and Student were each followed by temporary CDP blocking of all notification endpoints. In all three roles, opening the center showed `Không thể tải thông báo`, the explanatory status and `Thử lại`, and did not show `Không có thông báo nào`. After removing the block and using retry, reopening the center rendered the real notification list for each role. No business mutation was submitted; the temporary block was removed. This closes the representative-role Browser outage path and confirms the no-fabricated-empty-state fix, but it does not establish full retry/idempotency breadth.

## What is not established

- The historical live runtime had no accepted cross-role approve/reject flow because the Admin role link lacked `ADMIN_PRIMARY`; that blocker is superseded by the current live recheck (`is_primary_admin=true`, Admin queue/user endpoints HTTP 200). The current live approve and request-edit/reject branches are now correlated end-to-end for CS201/requests `#60002` and `#60003`; empty-reason validation also passed with the inline minimum-length warning.
- Upload remains unverified because Edge blocked file selection; result-PDF browser export timed out. Backend course-resource download passed HTTP, but browser delivery was blocked by Edge.
- Delete, rapid retry, stale-session and broad cross-role isolation proof remain incomplete beyond the exercised samples; pagination and one Student role-tampering probe now have direct partial evidence.
- The double-click sample confirmed duplicate notification rows/events in SQL Server. Current source tracing confirms the mechanism: no broadcast idempotency key, a fresh random event per request, uniqueness only by event/recipient, and read-time same-title/body hiding; timeout/retry and broader idempotency behavior remain unverified.
- Historical requests `#60002/#60003` exposed internal numeric course ID `70014` in the title, action URL and event payload. RCA-032/F-017 is resolved in the current worktree: live request `#60004` rendered `CS201`, navigated by public UUID, and correlated SQL event `140017` plus notification `150090` to `06a1a28d-667a-4d31-b5c9-edefc2885d91`; the historical rows remain unchanged evidence.
- Direct read-only SQL Server correlation ran against database `PWD301`: MSSQL dialect, 30 notification rows, 31 event rows; the valid broadcast had one row and the double-click title had two rows/two event IDs for one recipient.
- Fresh disposable SQL Server migration round-trip and row-version concurrency checks both passed; this does not replace release-environment verification after future schema/product changes.
- No email delivery proof; the retry endpoint had zero eligible failed-email records.
- No proof that each notification CTA leads to the correct final business state.

## Release/audit counters

These counters describe this audit evidence, not production telemetry:

| Counter | Value |
|---|---:|
| Required reports produced | 8 |
| Product changes from audit | Scoped changes across 7 unique product files: instructor staged-lesson upload, Admin broadcast/retry payload guards, notification mark-all payload guard, graded-result CTA, enrollment CTA/transaction ordering, notification transport client, and router degraded/loading/auth-route handling; tests listed separately in the dirty worktree |
| Backend producer callsites inventoried | 37 |
| Frontend `UI.showToast` occurrences | 384 |
| Targeted notification tests | Baseline: 28 collected; 26 passed; 2 failed. Current post-fix: 28 passed; 0 failed |
| Frontend tests | 101 passed, 0 failed, 0 skipped; degraded/loading/transport failure and auth-route behavior covered |
| Pytest coverage | Pre-fix baseline: 1546 passed; 17 failed; 2 skipped. Current split post-fix verification: **1572 passed; 0 failed; 0 skipped** across all groups; both SQL Server gates executed |
| Browser demo logins exercised | 3 current live standard-form role paths; API matrix 7/7 demo accounts; 1 disposable Admin session |
| Browser notification/workflow flows exercised | 36 live flows; 4 additional disposable Admin queue/decision flows |
| Disposable corrected Admin review retest | browser approve PASS; browser request-edit/reject PASS; DB post-conditions verified |
| Browser acceptance status | PARTIAL; duplicate/security/error findings remain |
| SQL Server migration/concurrency checks accepted | 2 disposable integration checks passed |
| SQL Server read-only notification correlation | 1 direct query set; not a migration/concurrency pass |

## Required final metrics snapshot

Các số liệu dưới đây có scope cụ thể; không phải production totals. Mục nào chưa có cách đếm authoritative được ghi rõ thay vì suy đoán.

| Metric yêu cầu | Giá trị hiện biết | Scope / trạng thái |
|---|---:|---|
| 1. Tổng notification phát hiện | 37 producer callsites; latest direct SQL Server snapshot: 30 `notifications` rows and 31 `notification_events` rows; authenticated Admin API showed `total=6` before the double-click probe | point-in-time local audit DB snapshot, not production telemetry |
| 2. Tổng notification đúng | Chưa thiết lập | chưa có business post-condition/DB row cho mọi item |
| 3. Tổng notification sai | 8 confirmed notification/failure groups | current audit triage after resolving RCA-032/F-017; not a per-row production count |
| 4. Tổng duplicate | 3 runtime duplicate groups | Instructor MIDTERM + Admin CS301 near-duplicates, plus Admin double-click persisted as 2 DB rows/2 event IDs; API/UI can hide the latter |
| 5. Tổng hard-code | 384 `UI.showToast` occurrences | exact hard-coded-message subset not normalized/countable yet |
| 6. Tổng message EN | Chưa thiết lập đầy đủ | direct examples confirmed in Instructor/Admin code and RBAC UI |
| 7. Tổng message VI | Chưa thiết lập đầy đủ | direct runtime examples confirmed |
| 8. Tổng message mixed language | Chưa thiết lập đầy đủ | mixed runtime/source examples confirmed |
| 9. Tổng lỗi Frontend | 5 confirmed groups | raw error propagation, silent background fetch, stale logout hash/view, default-role ambiguity and current frontend focus/contract impacts |
| 10. Tổng lỗi Backend | 3 confirmed groups | dismiss status regression; producer/idempotency ambiguity; malformed mutation payload type handling |
| 11. Tổng lỗi API Contract | 5 confirmed groups | envelope divergence, dismiss status, web/REST shape split, deleted-field/semantic drift and malformed-payload status handling |
| 12. Tổng lỗi Business Logic | 1 confirmed group + open gaps | double-click duplicate rows/events confirmed in SQL Server; logout and other business meanings still need correlation |
| 13. Tổng lỗi UX | 7 confirmed groups | mixed language, duplicate copy, raw IP-like value, stale hash, background noise and keyboard/filter discoverability |
| 14. P0/P1/P2/P3 | P0: 0; P1: 15 proposed product-risk groups; P2: 5 tracked groups; P3: 0 | latest RCA triage includes RCA-023/RCA-027 at P1 and RCA-024–RCA-026 at P2; severity is audit triage, not release sign-off |
| 15. Vấn đề cần sửa ngay | 8 groups | dismiss contract, envelope, persisted rapid duplicate, duplicate identity, raw errors, IP-like security value, logout cleanup and malformed mutation input handling |
| 16. Cải thiện sau | 2 groups | cross-tab realtime and extended localization/channel policy |
| 17. Regression risk | Cao | product worktree remains dirty; latest controlled full suite is green with zero skips, but unresolved notification contract/browser/email/file evidence remains and persistent CI SQL provisioning is still an operational follow-up |
| 18. Kết luận | Chưa đạt nghiệm thu | partial evidence package, not release-ready |

### Metric correction from fresh Browser retest

The earlier metric rows that counted logout as one stale-hash/view group are superseded by the fresh Instructor2 modal-leak evidence. After the live F-017 correction, current audit triage is: **8 confirmed notification/failure groups**, **5 confirmed frontend groups**, **7 confirmed UX groups**, and **8 immediate-fix groups**. P1 triage is **15 proposed product-risk groups**; the current stale-hash/back-navigation boundary remains tracked with **RCA-023**, while the modal-overlay portion is fixed in the current source and retained as historical evidence. These are audit severities, not a release sign-off or a per-row production count.

### Latest metric correction from static and filter-boundary evidence

The pre-correction snapshot had `P2: 2`; the metrics table above is now synchronized to the current register of **5 P2 groups**: **RCA-024** is an unverified static `UI.alert` gap, **RCA-025** is a confirmed current role/status-filter contract ambiguity, and **RCA-026** is a confirmed keyboard-focus accessibility gap, in addition to the two pre-existing proposed P2 groups. The scoped mark-one-read idempotency pass is not counted as a defect.

## Traceability

| Requirement | Evidence |
|---|---|
| backend/API/frontend/UI discovery | `01_NOTIFICATION_DISCOVERY.md`, `02_NOTIFICATION_INVENTORY.md` |
| root cause, not isolated patches | `03_NOTIFICATION_ROOT_CAUSE_ANALYSIS.md` |
| one standard/catalog | `04_NOTIFICATION_STANDARD.md` |
| systematic remediation plan | `05_NOTIFICATION_FIX_PLAN.md` |
| role/valid/invalid/boundary matrix | `06_NOTIFICATION_TEST_MATRIX.md` |
| executed regression and limits | `07_NOTIFICATION_REGRESSION_REPORT.md` |
| final gate and exact blockers | this report |

## Required next gate

1. Execute the remaining B-005, B-007–B-009, B-011–B-013, B-015–B-017, B-020–B-022 and B-033–B-034 cases by role, recording API response, UI feedback and business post-condition.
2. Repair/re-seed the live/deployment runtime with the missing `ADMIN_PRIMARY` role-link metadata, then re-run `/auth/login`, `/admin/courses/pending`, approve and request-edit/reject there. The disposable corrected-runtime retest is already recorded above and is not a live-release pass.
3. Make the contract decision for `dismissed`, envelope and `deleted_at` before product remediation.
4. Resolve duplicate event identities, security telemetry exposure, raw English RBAC error copy, retry noise, and logout route cleanup.
5. Fix only after writing failing regression tests; rerun focused tests and the relevant aggregate gates.
6. Re-run the disposable SQL Server migration/concurrency checks after any schema/product change and before a release claim.

## Current continuation - fresh browser and producer-route evidence (2026-10-05)

Fresh Edge sessions authenticated as Student, Instructor and Admin through the standard login flow, reached the expected role surfaces, and were logged out. The Student notification CTA replay exposed a 404 caused by the producer using the assessment UUID; the canonical attempt-result route rendered the real scored result. A red regression was captured before the fix, then `test_attempt_service.py` passed **14 passed, 0 failed** after emitting `#/student/assessments/results?id=<attempt.public_id>`.

The same source/UI comparison found enrollment notification CTAs bypassing the SPA hash contract. The red regression captured both recipient URLs before the fix; after the source and transaction-order fixes, `test_enrollment_service.py` passed **20 passed, 0 failed** after switching to the existing Instructor and Student hash routes. A fresh live replay then opened both recipient CTAs: Student4 reached the DSA201 Student course detail and Instructor2 reached the DSA201 Instructor management page, with SQL Server action URLs matching both Browser destinations. This closes the fresh enrollment recipient + CTA gate; historical OPS401 orphan rows and a newly emitted graded-result event replay remain separate acceptance gaps.

The Instructor notification center still has a timing risk: a cold open briefly showed an empty state while the badge reported 14, then revalidation exposed the 14 notifications. This is recorded as a partial browser finding; no deterministic loading-state regression or remediation has been claimed.

## Completion statement

The eight audit artifacts are a **partial evidence package**, not an accepted end-to-end audit. Current Admin approve/reject and fresh enrollment have live Browser/SQL correlation; split verification executed all 1572 pytest items with zero skips/failures, and the latest frontend suite is 101 passed with zero skips/failures. Media, producer-route, loading-state, malformed-payload, enrollment-transaction and auth-route corrections have scoped regression evidence. Login/logout/Back auth stability also passed live. Upload/download, rapid/idempotency breadth, email delivery, overlay-at-logout breadth and complete API/DB correlation remain incomplete, so no end-to-end notification release claim is made.

### Latest broadcast idempotency correction (2026-10-05)

The previously confirmed B-021 duplicate broadcast path is now fixed in the scoped Admin flow. The shared service accepts a UUID `X-Idempotency-Key`, exact replays return the original fan-out count without new event/recipient rows, and changed payloads return `409`. The Admin modal holds the same key across retry and disables its primary submit action while in flight. RED/GREEN API and service regressions passed; a fresh disposable Browser double-click produced one POST and one Vietnamese success toast, while SQL Server showed one matching event and seven recipient rows. A separate two-client concurrent HTTP replay returned `200/200` with first-send/replay markers and produced the same one-event/seven-recipient SQL result. The disposable database was cleaned with `audit_database_remaining=0`, and port 5105 had zero listeners.

This closes B-021/RCA-032 for Admin broadcast only. It does not prove idempotency for every notification producer, enrollment retry, dismiss/delete retry, email retry, or cross-tab race.

### Metric correction after B-021

The audit register still records **3 observed duplicate groups** for traceability, including the historical Admin double-click rows. The current remediation status is **1 group fixed in the Admin broadcast path** and **2 groups still open or requiring separate producer evidence**. Historical rows are retained; no live data was deleted or rewritten.

### Latest split verification checkpoint (2026-10-05)

The current worktree now has **1585 pytest passes, 0 failures and 0 skips** across non-overlapping partitions: root **298**, unit **632**, API **381**, security/concurrency/e2e **258** (233 + 13 + 12), and real SQL Server integration **16**. `pytest --collect-only -q` reported **1585 tests collected**. The frontend suite remains **101 pass, 0 fail, 0 skipped, todo 0**. The lesson-flag TDD regression, disposable SQL Server REST replay, sub-admin scope replay and Browser exact-five-character replay are separately recorded as green scoped evidence. Disposable SQL Server cleanup returned zero remaining audit databases and the dedicated audit server port was stopped.

This checkpoint closes the previously failing lesson-flag moderation path, including malformed JSON type handling and atomic flag/audit/notification persistence. It does **not** close the broader notification audit: duplicate/idempotency breadth, contract normalization, email delivery, file upload/download and several Browser/API/DB correlation gates remain open. The historical aggregate verifier stall is still not counted as a pass.

### Latest complete split checkpoint after B-021 (2026-10-05)

The current worktree now reports **1586 pytest passes, 0 failures and 0 skips** across root **298**, unit **632**, API **382**, security/concurrency/e2e **258**, and real SQL Server integration **16**; collection reported **1586 tests**. Frontend remains **101 pass, 0 fail, 0 skipped, todo 0**. The root FILE_SCAN teardown lock was reproduced and resolved with a testing-only queue guard; production async dispatch remains unchanged. Ruff, format, repository contract, diff, disposable SQL cleanup and port checks also passed.

This is the latest execution checkpoint, not whole-audit acceptance. Open gates remain email delivery, Browser file chooser/download, canonical response-envelope normalization, historical notification repair, complete producer/role coverage and non-Admin retryable-producer idempotency.

### Latest shared REST validation correction (2026-10-05)

The shared notification blueprint no longer dereferences malformed list payloads. RED coverage reproduced HTTP 500 on `/api/notifications/broadcast` and `/api/notifications/emails/retry-failed`; the fixed routes return HTTP 400 `VALIDATION_ERROR` in a live disposable SQL Server replay. Valid same-key shared REST broadcast returned `200` first-send/replay responses, and SQL Server contained one event with seven recipient rows. The historical 500 observations remain clearly labeled as pre-fix evidence; canonical `{success,data,error}` envelope normalization is still open.

### Latest scoped notification envelope correction (2026-10-05)

The canonical envelope gap is now fixed for the scoped notification REST/Admin handlers. A RED regression first reproduced missing `success/data` members on list, count, read, mark-all and dismiss responses; the corrected paths return `success=true,data=...`, and errors return `success=false,data=null,error=...` while retaining legacy top-level fields for compatibility. Notification API **12**, Admin broadcast **1**, notification IDOR **7**, and full API **383** passed. The current non-overlapping verification is **1587 passed, 0 fail, 0 skipped** (root **298**, unit **632**, API **383**, security/concurrency/e2e **258**, real SQL Server integration **16**), with **1587 tests collected**; frontend remains **101 pass, 0 fail, 0 skipped, todo 0**.

This closes the scoped notification envelope checkpoint only. Other API/web-auth response families, email delivery, Browser upload/download, historical notification repair, complete producer/role coverage and non-Admin idempotency remain open, so the eight-report package remains **PARTIAL** and is not a release acceptance claim.

### Latest email outbox/retry correction (2026-10-05)

The controlled email gate is split by evidence scope. A fresh disposable SQL Server probe forced one real outbox delivery to `FAILED`, called the Admin retry API (`200`, `success=true`, `data.retried_count=1`), and processed it to `SENT` through real `smtplib` wire transport to an ephemeral loopback SMTP sink. The sink captured exactly recipient `student4@pwd301.local` and subject `PWD301 audit email`; the audit database was removed with `0` remaining. This closes the application outbox, retry authorization, recipient-boundary and local SMTP protocol checks. It does **not** prove approved external-provider delivery or inbox receipt, so the overall email acceptance gate remains open.

### Latest Browser file I/O correction (2026-10-05)

The live Browser verification reached both file workflows. Instructor1 saw the CS201 cover-upload input with the correct image MIME allowlist, but Edge rejected file assignment with `Not allowed` and no native chooser appeared; upload validation and post-condition remain unverified. Student1 clicked an authorized DSA201 PDF link, but Downloads retained only a 1169-byte `.crdownload` after five seconds, with no finalized file. The same authenticated direct response returned `200`, `Content-Type: application/pdf`, `Content-Disposition: attachment`, `Content-Length: 1169`, `%PDF-1.4` and `%%EOF`. Upload is **BLOCKED ENVIRONMENT**; download is **BACKEND PASS / BROWSER FINALIZATION PARTIAL**. No success notification or release claim is made for the Browser finalization step.

### Latest Browser PDF download finalization correction (2026-10-05)

The earlier `.crdownload` observation is narrowed rather than fully superseded: Student1 has a readable same-name DSA201 file at **1,169 bytes** with `%PDF-1.4` and `%%EOF`, but it pre-existed the replay. A distinct-resource replay below eventually finalized at 1,145 bytes with the same PDF markers after a delayed `.crdownload` period. Authorized DSA201 resource download is therefore a **PASS after delayed completion**, while upload/file-selection, quarantine-access, timing feedback and other file producers remain open.

### Latest Student rapid mark-all correction (2026-10-05)

The earlier detached-node observation is superseded for a controlled disposable Student1 fixture. The exact `Đã đọc tất cả` control was double-clicked once; Browser settled at `Chưa đọc (0)`, retained the fixture as read and rendered one success toast. SQL Server showed exactly one fixture notification row/event with one `read_at` and no duplicate persistence; cleanup returned zero targeted rows. This closes a **scoped Student Browser + SQL Server rapid mark-all state checkpoint**, not dismiss/delete, timeout/out-of-order retry, or complete producer/role coverage.

### Latest Browser upload permission blocker confirmation (2026-10-05)

The live CS201 upload controls were retried through Computer Use's native accessibility path. `Tải ảnh bìa ngay` and `Đổi Ảnh Đại Diện Khóa Học` both remained visible, but neither opened a native file picker; the input stayed empty and no request/DB mutation was produced. This confirms an environment-level Browser boundary, not a successful product upload path.

Instructor1 reached the CS201 cover-upload control and the audit attempted a disposable invalid fixture. Edge rejected `fileChooser.setFiles` with `Not allowed`; the input remained empty (`files=null`, `value=''`) and no API/DB mutation occurred. The session logged out and the fixture was removed. Upload, server-side rejection and quarantine-access acceptance remain **BLOCKED ENVIRONMENT** and are not counted as passes; the package remains **PARTIAL**.

### Latest Student result alert correction (2026-10-05)

The historical static `UI.alert` concern is superseded by current source evidence: the helper exists, but its argument order was inverted against both Student result callers. A RED test reproduced the swapped title; the minimal shared-helper fix now preserves title-first semantics and multiline body content. Full frontend verification is **102 passed, 0 failed, 0 skipped**. This closes the static/helper contract issue, while Browser exposure of the pending-appeal and score-scale actions remains open.

### Latest security-notification telemetry correction (2026-10-05)

The Admin Browser replay exposed the seeded raw IP `192.168.1.105` in a `SYSTEM_SECURITY_ALERT`. A failing regression was added before the fix. The demo seed now uses safe actionable Vietnamese copy, and the exact matching live SQL Server row was repaired transactionally. Verification: `remaining_raw_ip=0`; Browser reload showed `Phát hiện hoạt động đăng nhập quản trị bất thường...` with no IP. This closes the seeded security-copy disclosure case only; dynamic security-event producers and other open audit gates remain unverified, so the overall package is still **PARTIAL**.

### Latest complete no-skip verification (2026-10-05)

After the security-copy correction, all current non-overlapping partitions completed with **1,588 passed, 0 failed, 0 skipped**: top-level 298, unit 632, API 383, security/concurrency/e2e 258, and integration 17. The SQL Server integration helper created two disposable databases, ran migration and row-version coverage, and removed both with `audit_database_remaining=0`. This closes the current no-skip execution gate; it does not close the Browser upload/download, external SMTP, final Student Browser ESSAY replay, or complete producer/role acceptance gates.

Review limitation for the latest auth-route correction: the scoped `ocr review --audience agent` command failed before review because no valid LLM endpoint was configured. It is not a review pass. Manual diff inspection and the RED/GREEN/full-suite/live Browser checks are the available evidence; no provider credentials were added.

### Latest manual ESSAY grading and result correction (2026-10-05)

The earlier manual-ESSAY acceptance gap is now closed for the scoped Instructor/API/DB path. The minimal fix adds the missing grade rowversion to the evaluation payload, reuses the existing grading endpoint from a pending/manual-graded ESSAY card, validates score/reason in the UI, and renders Student ESSAY answer text, awarded points, manual status and feedback through the existing result card.

Evidence is current and directly executed: focused frontend **3 passed, 0 failed, 0 skipped**; full frontend **105 passed, 0 failed, 0 skipped**; full API **383 passed**; full non-overlapping Python split **1,588 passed, 0 failed, 0 skipped**. In Browser, a disposable pending ESSAY fixture was opened by Instructor, scored `3.5`, saved with a reason, and reopened at `3.5 / 20` with `3.5 / 4` on the ESSAY card. SQL Server confirmed `GRADED`, `MANUAL_GRADED`, `awarded_points=3.5`, the persisted reason and rowversion `0000000000112d3c`. Cleanup removed the fixture and returned zero related orphan rows.

The Student result renderer is covered by source-level regression, the full frontend suite, and a direct Browser replay of an existing released ESSAY result showing the persisted answer, `4 / 4 đ`, manual feedback and no choice labels. The fullscreen limitation applies only to starting a new controlled exam attempt. Therefore the overall eight-report package remains **PARTIAL**, with Browser upload permission/download finalization, external SMTP/inbox receipt, dynamic producer/role breadth and historical data-repair scope still open.

## Latest dismiss contract correction (2026-10-05)

The current source/API contract now returns `status=dismissed` for soft-dismiss and hides the notification by `expires_at`. Focused unit + API notification verification passed **25 passed, 0 failed, 0 skipped**. This closes the stale service/API mismatch; the newer Admin Browser dismiss replay below closes the single-item UI/DB gate.

## Current metric checkpoint (2026-10-05)

The following values are the current audit-register view; older metric tables remain historical traceability and are not silently rewritten.

| Metric required by the audit brief | Current evidence-backed value | Boundary |
|---|---|---|
| 1. Total notification cases found | **153 distinct inventory cases**; static map also records **37 backend producer callsites** and **384 frontend `UI.showToast` occurrences** | Callsite count is not a delivered-event count; exact hard-coded message deduplication is separate |
| 2. Total correct | **Not established as a global count** | Every case lacks a complete live FE→API→BE→DB→UI post-condition replay |
| 3. Total incorrect | **8 confirmed notification/failure groups in the audit register** | Includes historical groups whose scoped fixes are recorded separately; not a claim of 8 current production rows |
| 4. Duplicate groups | **3 observed groups**; **1 scoped Admin broadcast group fixed**, 2 require separate producer evidence | Historical duplicate rows are retained |
| 5. Hard-coded messages | **384 toast callsites inventoried**; exact hard-coded-message subset **not fully normalized/countable** | Static occurrence count must not be mislabeled as unique messages |
| 6. English messages | **Not fully established**; direct English examples remain in sampled RBAC/error paths | Requires complete catalog extraction and role replay |
| 7. Vietnamese messages | **Not fully established**; Vietnamese runtime paths are the dominant sampled language | Same catalog boundary as English count |
| 8. Mixed-language messages | **Confirmed in sampled source/runtime paths; global count not established** | Encoding/mojibake snapshots are retained as evidence, not counted as unique messages |
| 9. Frontend error groups | **5 confirmed historical groups** in the register; scoped corrections are appended with newer IDs | Current full frontend regression is 105/105; this is a defect-register count, not failed tests |
| 10. Backend error groups | **3 confirmed historical groups** in the register | Scoped remediation and remaining producer gaps are separated in RCA |
| 11. API contract groups | **5 confirmed historical groups**; scoped notification envelopes are corrected | Wider non-notification response families remain outside the closed scope |
| 12. Business-logic groups | **1 confirmed persisted duplicate group plus open correlation gaps** | Enrollment/course-review/grading scoped paths now have fresh evidence |
| 13. UX groups | **7 confirmed groups** in the register | Accessibility, language, raw-copy and timing findings remain separately labeled |
| 14. Severity | **P0: 0; P1: 15 proposed risk groups; P2: 5 tracked groups; P3: 0** | Severity is audit triage, not release acceptance |
| 15. Immediate work | Browser file chooser/upload and quarantine access, external SMTP/inbox, historical orphan decision, producer/role breadth and remaining duplicate/rapid boundaries | No environment blocker is counted as a product pass |
| 16. Later improvements | Full message catalog normalization, cross-tab delivery, full accessibility/mobile coverage and non-Admin idempotency breadth | Requires a separate scoped plan |
| 17. Regression risk | **High** for notification producer/recipient/DB correlation; **controlled** for the 1,589-test split and current frontend suite | Aggregate `verify.ps1` stall remains excluded |
| 18. Current conclusion | **PARTIAL — not release accepted** | Browser and external-service gates are still incomplete |

## Resume blocked-audit recheck

After the goal was resumed, the current environment was rechecked on 2026-10-05. The default process still lacks persistent `SQLSERVER_CONCURRENCY_URL` and `SQLSERVER_MIGRATION_URL` as well as `DATABASE_RUNTIME_URL`, `MAIL_SERVER` and `SMTP_HOST`; a child process was nevertheless provisioned with disposable SQL Server databases, and the completed split pytest verification ran all 1572 items with zero skips. Both database pairs were removed after the integration run. A separate aggregate attempt stalled at 49% and was terminated. The worktree still contains user dirty entries and the eight audit reports remain present. Edge is reachable, all seven demo accounts authenticate through the local HTTP boundary, and the current live Admin role metadata is repaired (`is_primary_admin=true`). Email service and Browser file-URL permission remain unavailable, while unresolved notification business/contract findings remain.

### Exact unblock criteria

1. The completed split verification has evidence of zero skips when run with disposable SQL Server URLs. For repeatable CI/release runs, provision equivalent disposable databases and inject `SQLSERVER_MIGRATION_URL` and `SQLSERVER_CONCURRENCY_URL` into the verifier child process; do not point migration tests at the live PWD301 database. Investigate the nondeterministic aggregate stall before treating `verify.ps1` itself as a release gate.
2. Repeat Admin queue visibility, approve, request-edit/reject and owner-notification correlation on the current live runtime now that `ADMIN_PRIMARY` is present; retain the disposable-runtime result as separate evidence.
3. Provide a configured test email sink/provider, then create a controlled failed-email record and verify retry, delivery outcome and recipient boundary without exposing credentials.
4. Provide an approved Browser file-selection path (manual user selection or an allowed automation permission), then rerun upload rejection and pending/quarantine access denial; the authorized Student PDF download path now has finalized-file evidence.
5. After any further product remediation, rerun the focused notification tests and Browser/API/DB matrix; the staged-lesson media failures and SQL Server skip gate are already resolved in the latest controlled run.

## Latest shared SECURITY telemetry redaction and final no-skip checkpoint (2026-10-05)

The shared notification service now redacts raw IPv4 values from SECURITY title, body and CTA URL payloads. RED/GREEN coverage exercised all three fields; the current focused notification unit/API/demo/security scope passed **37 passed, 0 failed, 0 skipped**. After this product change, the complete non-overlapping verification was rerun on the current source: root **298**, unit **633**, API **383**, security/concurrency/e2e **258**, and real SQL Server integration **17**, totaling **1,589 passed, 0 failed, 0 skipped**. `pytest --collect-only -q` remains **1,589 tests collected**; frontend remains **105 passed, 0 failed, 0 skipped, todo 0**. Both disposable SQL Server databases returned `audit_database_remaining=0`.

The authoritative inventory is now **153 distinct audited cases**. This closes the shared SECURITY dispatch boundary and the authorized DSA201 resource download checkpoint after delayed completion, but the package remains **PARTIAL** because Browser file selection/upload, quarantine-access breadth, download timing feedback, external SMTP/inbox receipt, complete producer/role breadth, historical notification-data disposition and broader non-Admin retry/idempotency remain open.

## Current handoff clarification (2026-10-05)

The preceding checkpoint paragraphs intentionally preserve historical snapshots. The current handoff state is the newer evidence recorded above:

- The complete non-overlapping verification is **1,589 passed, 0 failed, 0 skipped**; collection reports **1,589 tests**, and the frontend suite is **105 passed, 0 failed, 0 skipped, todo 0**.
- The real SQL Server gate ran against disposable databases, including migration and row-version/concurrency coverage, and cleanup returned `audit_database_remaining=0` for both databases.
- The scoped manual-ESSAY Instructor/API/DB flow and the released Student ESSAY result Browser replay are closed with direct evidence.
- The audit package remains **PARTIAL**, not release accepted. Remaining gates are Browser file selection/upload, quarantine-access breadth, download timing feedback and other file producers, external SMTP/inbox receipt, complete producer/role breadth, historical notification-data disposition, and broader non-Admin retry/idempotency coverage.
- The aggregate verifier stall and the unavailable OCR provider remain explicitly unpassed; neither is counted as a successful gate.

### Latest REST role-filter validation correction (2026-10-05)

Student-authenticated REST notification list, unread-count and mark-all-read requests previously accepted unsupported or actor-ineligible `role`/`target_role` values as successful no-ops. TDD RED reproduced HTTP `200` for `ADMIN` and `BOGUS`; the minimal fix now normalizes the canonical roles and requires the authenticated actor to hold the requested role.

GREEN evidence: both invalid values return HTTP `400` with `success=false`, `data=null` and `error.code=VALIDATION_ERROR` across all three routes; valid lower-case `student` remains `200`. The role-filter regression passed **2/2**, the current notification API/service/IDOR scope passed **34, 0 failed, 0 skipped**, and current pytest collection reports **1,591 tests, exit 0**. Ruff and `git diff --check` passed; no database schema or data migration was performed.

This closes the scoped REST filter-validation defect only. The final audit remains **PARTIAL**: Browser upload/file selection and quarantine-access breadth, external SMTP/inbox receipt, complete producer/role coverage, historical notification-data disposition, and broader retry/idempotency remain open. The previous complete split checkpoint of **1,589 passed, 0 failed, 0 skipped** is retained as the last full-run evidence before this small route/test correction; the current source change is covered by the focused scope above and has not been folded into a new full split.

### Latest complete no-skip verification after role-filter correction (2026-10-05)

The full current source was then verified in non-overlapping partitions: root **298**, unit **633**, API **385**, security/concurrency/e2e **258**, and real SQL Server integration **17**, totaling **1,591 passed, 0 failed, 0 skipped**. `pytest --collect-only -q` reported **1,591 tests collected**. Frontend independently passed **105, 0 failed, 0 skipped, todo 0**. Both disposable SQL Server databases returned `audit_database_remaining=0` after cleanup.

This supersedes the earlier 1,589 execution checkpoint. It still does not turn the audit into release acceptance: Browser upload/file-selection and quarantine-access breadth, external SMTP/inbox receipt, complete producer/role coverage, historical notification-data disposition and broader retry/idempotency remain open.

### Latest Student result-PDF Browser replay (2026-10-05)

Student1 opened the scored result page for attempt `db76cdce-bef6-470d-be11-7d35cc9ab96b`; the visible `Xuất bảng điểm (PDF)` action delegates to `window.print()` at `frontend/assets/js/views/student.js:5375`. The semantic Browser click timed out during input dispatch, and a coordinate retry left the page/accessibility tree unchanged. No new tab, toast, download event or new Downloads file appeared; only earlier resource PDFs were present. The result-PDF acceptance gate remains **NOT VERIFIED**, and this is not counted as a product or database failure beyond the missing Browser-verifiable post-condition.

### Latest Admin mark-all role-scope replay (2026-10-05)

### Latest Admin single-item dismiss replay (2026-10-05)

The exact `delete` control for disposable Browser fixture `AUDIT_DISMISS_FIXTURE_601B33526EBB` was clicked once after action-time confirmation. The notification disappeared from the Admin center and the UI rendered `Đã xóa thông báo.`. SQL Server retained public id `3697da94-27a4-472e-b970-d7078e047c5a` with the original title, `expires_at=2026-10-05 14:50:30.184000` and `read_at=NULL`, proving soft-dismiss persistence rather than hard deletion. The Admin session then logged out and the temporary Browser tab was closed.

This is a **PASS scoped to one Admin single-item Browser/API/DB dismiss outcome**. It supersedes the immediately preceding statement that graphical dismiss was unverified, but does not close bulk delete, rapid double-click, timeout retry, or non-Admin idempotency. The eight-report package remains **PARTIAL**, with Browser file I/O, external SMTP/inbox, producer/role breadth, historical data disposition and broader retry/idempotency gates still open.

The Admin Browser notification center was freshly opened with badge `2`; `Đã đọc tất cả` changed the badge and `Chưa đọc` filter to `0` while preserving the visible notification items. SQL Server verification for the active Admin view of `admin@pwd301.local` returned `total=20`, `unread=0`, `read=20`. This is a scoped PASS for the Admin single-action mark-all UI/API/DB post-condition, not a claim that Browser rapid double-click, other role contexts, or dismiss/delete are complete.
### Latest Student result-PDF Browser verification after remediation (2026-10-05)

The Student result action now renders as a real download link with `ID=download-student-result-pdf-btn` and `/student/attempt/<attempt_id>/result.pdf`; the frontend source no longer calls `window.print()`. Student1 clicked the link on the released result and Edge created `CS101-bang-diem.pdf` in Downloads (1,713 bytes). `%PDF-`, terminal `%%EOF`, one readable `pypdf` page and persisted score text `Score: 1.00 / 16.00` were verified. The backend test also proves a released result returns an attachment and an unreleased result returns `403`.

This is a **PASS scoped to the Student released-result PDF download path** and supersedes the immediately preceding print-only replay. It does not close unrelated file upload/quarantine/resource-producer gates.

## Latest fresh graded-result notification replay (2026-10-06)

The disposable SQL Server grading fixture was recreated and exercised through manual grading, answer correction, regrade worker, duplicate regrade request and status correlation. It persisted exactly one `ASSESSMENT_GRADED` notice at 18/30 and one `SCORE_CHANGED_AFTER_REGRADE` notice at 18→28/30 for Student4; the duplicate regrade reused the same completed job and left grade history unchanged. A fresh Browser session showed both notices, opened the regrade notice detail, and followed `Mở Trang Liên Quan` to the canonical attempt-result route, which visibly rendered the released 28/30 result. Logout returned to `/auth`; the disposable server and database were removed, with `audit_database_remaining=0`.

This is a **PASS for the fresh emitted graded-result notification CTA (N-109/F-012)**. The historical assessment-UUID/404 reproduction remains preserved, while ESSAY question-level presentation and the wider producer/role/retry matrix remain open. The eight-report audit package remains **PARTIAL**, not release accepted.

## Latest answer-visibility correction (2026-10-06)

The grading result chain exposed a narrower UI truthfulness defect: when `answer_visibility_policy=AFTER_CLOSE` intentionally omits a Student ESSAY answer, the renderer previously displayed `Không trả lời`. The backend policy remains unchanged; the frontend now displays `Câu trả lời đang được ẩn theo chính sách khảo thí` for policy-hidden ESSAY answers and reserves `Không trả lời` for a genuinely visible empty answer.

TDD RED/GREEN passed, the answer-visibility security test and mixed manual-grading API test passed, Ruff passed, and the full frontend suite passed **107 passed, 0 failed, 0 skipped**. The post-fix Browser visual acceptance could not be completed because the CUA Browser inventory returned `browsers=[]`; this is recorded as pending rather than a pass. The exact disposable grading database was removed with `audit_database_remaining=0`. The overall audit remains **PARTIAL**, with Browser acceptance for this correction and the previously listed upload, external email, producer breadth and historical-data gates still open.

## Latest result truthfulness correction (2026-10-06)

The Student result page no longer fabricates a signature-like hash, instructor name or 45-minute duration. It now renders `signature_hash`, `instructor_name` and `duration_minutes` only when supplied by the API, otherwise showing `Chưa có dữ liệu`. TDD RED/GREEN passed, the full frontend suite passed **108 passed, 0 failed, 0 skipped**, and Ruff passed. Browser visual acceptance remains pending because the CUA Browser inventory is currently empty; the audit does not count this source-level result as a Browser pass.

## Latest keyed lesson-flag retry correction (2026-10-06)

The Admin lesson-flag notification chain now has an explicit retry contract. Both Admin routes forward a UUID X-Idempotency-Key to the shared service; the first request emits one durable audit/event/notice, an exact retry returns idempotent_replay=true without another side effect, and a changed payload returns 409 CONFLICT. The TDD regression suite passed **9, 0 failed, 0 skipped**. A disposable SQL Server HTTP replay passed **3/3, 0 failed, 0 skipped** and verified SQL delta **1 audit + 1 event + 1 notice**; cleanup returned audit_database_remaining=0.

This closes the keyed REST/Web lesson-flag retry defect only. Browser rapid retry, unkeyed-client behavior, other notification producers, external SMTP/inbox delivery, upload/quarantine access and historical data disposition remain open. The overall audit is still **PARTIAL - not release accepted**.
The N-154 keyed lesson-flag replay is the latest added inventory case; the current authoritative register is **154 distinct audited cases**. Historical metric tables retain their prior 152/153 snapshots for traceability.

## Latest durable-event visibility correction (2026-10-06)

The notification list no longer hides older durable rows by matching recipient/title/body/role. Distinct NotificationEvent records with identical copy now remain visible, while retry safety is handled explicitly by producer idempotency keys. RED/GREEN evidence is current: the combined notification/flag scope passed **37, 0 failed, 0 skipped**, and Ruff plus diff check passed.

This closes the scoped duplicate-hiding defect at the backend/API layer only. It does not approve historical duplicate deletion, prove every producer's idempotency, or close Browser visual acceptance, external SMTP/inbox, upload/quarantine and other audit gates. The overall package remains **PARTIAL - not release accepted**.
The current SQL Server evidence strengthens this conclusion: a disposable fixture persisted two same-copy event rows and authenticated REST returned both, with **1 case, 0 failed, 0 skipped** and database cleanup remaining 0. Browser visual acceptance is still pending because CUA exposes no Browser.
The latest N-155 correction brings the authoritative inventory register to **155 distinct audited cases**; prior metric tables remain historical snapshots.
## Latest generic event-key conflict correction (2026-10-06)

The notification event idempotency boundary now rejects semantic conflicts instead of silently returning the first row. Exact replays remain safe, while changed event type, actor, target or payload produce ConflictError before fan-out. Current evidence is **38 passed, 0 failed, 0 skipped** plus a disposable SQL Server probe with **2 cases, 0 failed, 0 skipped** and cleanup remaining 0.

This closes the scoped generic event-key defect, not the entire audit. Browser visual acceptance, stable-key adoption across all producers, external SMTP/inbox, upload/quarantine and historical disposition remain open; the package stays **PARTIAL - not release accepted**.
The N-156 correction brings the latest authoritative inventory register to **156 distinct audited cases**; older metric tables are retained as historical snapshots.
## Latest SQL Server seed-idempotency evidence (2026-10-06)

The current disposable SQL Server fixture now has direct seed-idempotency evidence: the second demo seed produced no new users/courses/questions/attempts/resources/notifications/audits and all counts stayed unchanged. The probe passed **1 case, 0 failed, 0 skipped**, and cleanup returned audit_database_remaining=0. This closes the disposable seed gate only; it is not a live-database reseed.
N-157 brings the latest authoritative inventory register to **157 distinct audited cases**; prior metric tables remain historical snapshots.

## Latest shared notification-dispatch key correction (2026-10-06)

The common `dispatch_notification()` helper now accepts an optional UUID `event_key` and forwards it to the semantic `emit_event()` idempotency boundary. TDD RED reproduced the missing parameter; GREEN verified an exact retry reused one event and one recipient row. The current focused notification/flag scope passed **39 passed, 0 failed, 0 skipped**; Ruff, Python compile and diff check passed.

This closes only the shared helper capability. The final audit remains **PARTIAL - not release accepted**: stable-key adoption across every producer, Browser rapid retry/visual acceptance, external SMTP/inbox, file selection/upload/quarantine and historical data disposition remain open. N-158 brings the latest authoritative inventory register to **158 distinct audited cases**; earlier metric tables remain historical snapshots.

## Latest keyed-dispatch semantic conflict correction (2026-10-06)

The shared helper initially accepted `event_key` but still omitted notification presentation semantics from the event payload. A changed body could therefore be silently treated as an exact retry. The current keyed contract persists sanitized title/body/category/target-role/force-email metadata, so exact retries reuse one event, one in-app notification and one email outbox row, while changed content raises `ConflictError` before fan-out.

Current focused evidence is **39 passed, 0 failed, 0 skipped**; Ruff and Python compile passed. An AST inventory found **35 direct unkeyed `dispatch_notification()` callsites**, so stable-key adoption is not complete. The final audit remains **PARTIAL - not release accepted**: producer-by-producer keys, Browser/CUA retry and visual acceptance, external SMTP/inbox, file selection/upload/quarantine and historical data disposition remain open. N-159 brings the latest authoritative inventory register to **159 distinct audited cases**; earlier metric tables remain historical snapshots.

## Latest enrollment notification producer correction (2026-10-06)

The `STUDENT_ENROLLED` fan-out now uses deterministic UUIDv5 keys derived from the durable enrollment ID and recipient role. Unit evidence confirmed separate Instructor/Student keys. The real disposable SQL Server probe created an enrollment, verified both keys, replayed both exact notifications and observed event/notification counts unchanged at `2 -> 2`; it reported **3 cases, 0 failed, 0 skipped**, cleanup `audit_database_remaining=0`, and no remaining port-5105 listener.

This closes the enrollment producer boundary only. The current AST inventory still has **32 direct dispatch callsites with neither an explicit key nor a prebuilt event**. The final audit remains **PARTIAL - not release accepted**: complete producer adoption, Browser/CUA operations, external SMTP/inbox, file selection/upload/quarantine and historical data disposition remain open. N-160 brings the latest authoritative inventory register to **160 distinct audited cases**; earlier metric tables remain historical snapshots.

## Latest password-security producer key correction (2026-10-06)

## Latest course lifecycle producer-key correction (2026-10-06)

Course submission, Admin approval and Admin rejection notifications now use recipient-scoped UUIDv5 keys derived from the persisted lifecycle AuditEvent. The service flushes the audit row before fan-out, so the key is based on a durable transition rather than a generated event or presentation copy. TDD RED/GREEN passed the lifecycle key test; course/notification regression scope passed 22 selected tests, notification API/service passed 30 tests, Ruff passed, and the disposable SQL Server replay kept event/notification rows at 1 -> 1 (4 cases, 0 failed, 0 skipped). Enrollment and password SQL probes also passed in the same disposable run; cleanup returned zero audit databases.

The current AST inventory is 35 direct dispatch calls / 7 explicit keys / 1 prebuilt event / 27 neither. This closes only the course lifecycle producer boundary. The audit package remains PARTIAL - not release accepted because 27 producers still require operation-specific key decisions, CUA has no Browser for visual/rapid-retry acceptance, approved external SMTP/inbox evidence is unavailable, and upload/quarantine plus historical disposition gates remain open. N-162 brings the latest authoritative inventory register to 162 distinct audited cases; prior counts remain historical checkpoints.

## Latest course-owner reassignment producer correction (2026-10-06)

Admin course-owner reassignment notifications now use separate UUIDv5 keys for the former and new owner, both derived from the flushed COURSE_OWNER_REASSIGNED AuditEvent. TDD RED/GREEN passed the two-recipient unit regression. This increment has no dedicated SQL Server replay or Browser acceptance, so those gates remain open.

The current AST inventory is 35 direct dispatch calls / 9 explicit keys / 1 prebuilt event / 25 neither. The audit package remains PARTIAL - not release accepted: 25 producers still need operation-specific key decisions, CUA has no Browser for visual/rapid-retry acceptance, external SMTP/inbox evidence is unavailable, and upload/quarantine plus historical disposition gates remain open. N-163 brings the latest authoritative inventory register to 163 distinct audited cases; prior counts remain historical checkpoints.

## Latest password-reset token producer correction (2026-10-06)

Password-reset token completion now passes the same UUIDv5 mutation key used by normal password changes and direct set-password operations: durable user ID plus post-mutation auth_version. TDD RED/GREEN passed the reset-token unit test and the current AST inventory is 35 direct dispatch calls / 10 explicit keys / 1 prebuilt event / 24 neither.

The disposable SQL Server probe exercised both normal and reset-token mutations and replayed both exact events with event/notification/email rows unchanged at 1 -> 1; it reported 6 cases, 0 failed, 0 skipped, and cleanup returned zero audit databases. Browser retry/visual acceptance and approved external inbox evidence remain open. The audit package remains PARTIAL - not release accepted; 24 producers still require operation-specific key decisions and the upload/quarantine, external delivery and historical disposition gates remain open. N-164 brings the latest authoritative inventory register to 164 distinct audited cases; prior counts remain historical checkpoints.

## Latest account-suspension producer correction (2026-10-06)

ACCOUNT_SUSPENDED now uses a UUIDv5 key derived from the durable user ID and post-suspension auth_version. TDD RED/GREEN passed the unit regression. The SQL Server disposable security probe exercised normal password change, password-reset token and account suspension, replayed each exact event and kept event/notification/email rows at 1 -> 1; it reported 9 cases, 0 failed, 0 skipped, and cleanup returned zero audit databases.

The current AST inventory is 35 direct dispatch calls / 11 explicit keys / 1 prebuilt event / 23 neither. The audit package remains PARTIAL - not release accepted: 23 producers still require operation-specific key decisions, CUA has no Browser for visual/rapid-retry acceptance, approved external SMTP/inbox evidence is unavailable, and upload/quarantine plus historical disposition gates remain open. N-165 brings the latest authoritative inventory register to 165 distinct audited cases; prior counts remain historical checkpoints.

Password mutation security notices now use UUIDv5 keys derived from user ID and post-mutation `auth_version` in both `change_password()` and `set_password()`. Unit evidence passed, and the real disposable SQL Server probe verified `auth_version=2`, one keyed event, one notification and one email outbox before/after exact replay; **3 cases, 0 failed, 0 skipped**, cleanup `audit_database_remaining=0`, and no remaining port-5105 listener.

This closes the password security producer boundary only. The current AST inventory still has **30 direct dispatch callsites with neither an explicit key nor a prebuilt event**. The final audit remains **PARTIAL - not release accepted**: complete producer adoption, Browser/CUA operations, external SMTP/inbox, file selection/upload/quarantine and historical data disposition remain open. N-161 brings the latest authoritative inventory register to **161 distinct audited cases**; earlier metric tables remain historical snapshots.

## Latest durable producer expansion (2026-10-06)

Role mutations now use post-mutation auth-version keys; Admin course edits use flushed audit IDs; lesson/course change requests use persisted change-request IDs; and malware rejection uses persisted file-revision IDs. Targeted TDD/API evidence is GREEN and Ruff passes. The current AST inventory is **35 direct calls / 25 explicit keys / 1 prebuilt event / 9 neither**.

This is a scoped producer improvement, not release acceptance. The four newly covered boundaries have no dedicated SQL Server replay in this increment; Browser/CUA visual and rapid-retry acceptance is unavailable because no Browser is exposed; approved external inbox evidence is unavailable; and nine producer callsites still need operation-specific decisions. The audit remains **PARTIAL - not release accepted**. N-166 is the latest case-register increment; earlier counts remain historical snapshots.

## Latest complete direct-producer coverage (2026-10-06)

The final direct producer gaps are now closed at source level. Assessment-result notifications use deterministic attempt/result transition keys; YouTube health alerts use course/lesson/video/recipient keys; Admin and instructor route notifications use persisted request/event/recipient keys. Focused tests passed 13 attempt tests, 28 change-request/prerequisite API tests and 79 affected service tests, with zero failures and zero skipped tests; Ruff and compile passed. AST reports **35 direct calls / 34 explicit keys / 1 prebuilt event / 0 neither**.

This does not convert the audit to release acceptance. Dedicated SQL Server exact-replay probes for this final sweep were not run, CUA still exposes no Browser for visual/rapid-retry acceptance, approved external inbox evidence is unavailable, and historical duplicate disposition plus file/upload access gates remain open. The audit remains **PARTIAL - not release accepted**. N-167 is the latest producer-coverage increment; earlier counts remain historical snapshots.

## N-168 - aggregate verification with SQL Server enabled (2026-10-06)

`scripts/verify.ps1` was rerun with fresh disposable SQL Server URLs. The complete gate passed with exit code 0: **1607 passed, 0 failed, 0 skipped** in 1291.34 seconds, including migration round-trip, ROWVERSION grading race and both immutable-question-revision cases. Contract/static checks, format/lint, mypy and 108 frontend tests also passed. The disposable databases were removed; the live `PWD301` database was not modified. Current producer AST: **35 direct calls / 34 explicit keys / 1 prebuilt event / 0 neither**.

The overall audit remains **PARTIAL - not release accepted** because CUA still has no Browser for visual and rapid-retry acceptance, approved external SMTP/inbox evidence is unavailable, and file chooser/quarantine plus historical duplicate disposition gates remain open. N-168 is the latest verification checkpoint; older counts and open-gate statements remain historical context.

## N-169 - live email queue root cause and remediation (2026-10-06)

Current live SQL evidence found **115 PENDING** `email_deliveries`, oldest `2026-09-19 07:47:38.210`, all at `attempt_count=0`, with **0 `background_jobs`**. The source-level root cause was a missing worker deployment plus a non-testing `MockMailClient` default. Remediation is now implemented and tested: due outbox rows create a deduplicated EMAIL job; `scripts/run_worker.py` and a Compose `worker` service poll the queue; production uses configured SMTP or fails closed; stale backlog makes health `DEGRADED`. The scoped regression set passed **41**, and `docker compose config`, Ruff, mypy and compile passed.

The live worker was not started because `MAIL_HOST` and `MAIL_FROM` are absent; draining the real backlog without an approved provider would be unsafe and could change durable delivery state. The audit remains **PARTIAL - not release accepted**: Browser/CUA still exposes no Browser, approved external inbox evidence is unavailable, and file chooser/quarantine plus historical duplicate disposition gates remain open. N-169 is the latest current-state checkpoint.

## N-170 - current acceptance boundary and final verifier (2026-10-06)

Fresh Computer Use revalidation returned `apps=[]` and `browsers=[]`; direct `createBrowserTab("iab", "http://127.0.0.1:5000")` returned `Browser is not available: iab`. This confirms the required Browser acceptance environment is still unavailable; no UI login, visual notification, rapid-retry, file-chooser or download-finalization claim is made from automated evidence. The current SQL-enabled full verifier completed **1612 passed, 0 failed, 0 skipped** and removed both disposable SQL Server databases. `docker compose build worker` passed, while the live worker remains stopped because `MAIL_HOST` and `MAIL_FROM` are absent. Final status is **PARTIAL - not release accepted** until Browser/CUA, approved SMTP/inbox, file/quarantine and historical notification-data disposition gates are evidenced.

## N-171 - live historical duplicate disposition evidence (2026-10-06)

Read-only SQL Server classification of the current `PWD301` database found **143 notification events**, **168 notifications**, **115 PENDING email deliveries**, zero events without a linked notification, and zero repeated `notification_events.event_key` values. Presentation-copy grouping nevertheless found **14 recipient/title/body/role groups** with repeated rows; the largest groups contain 13, 7 and 6 rows. A payload-level `change_request_id` grouping found no repeated business transition, while nine repeated action-URL groups and one six-row `FILE_REJECTED` group lack sufficient historical business identity in the payload to prove whether rows are legitimate transitions or duplicate delivery. No live row was deleted or hidden. Disposition remains open and requires owner-approved business mapping plus a disposable repair rehearsal; preserving these append-only records is the safe current outcome.

## N-172 - session notification envelope correction (2026-10-06)

The web-session notification routes now expose the canonical `{"success": true, "data": ...}` envelope for list, unread-count, read, mark-all-read, dismiss, clear and Student notification endpoints. Existing top-level fields remain as compatibility aliases for the current frontend. TDD RED reproduced `KeyError: data`; GREEN passed **16 notification API tests**, Ruff and compile passed, and the focused frontend notification/PDF regression set passed **7 tests**. The prior SQL-enabled aggregate count of 1612 is not being reused as post-patch full-suite evidence; Browser/CUA, SMTP/inbox and file/quarantine gates remain open.

## N-173 - final post-patch aggregate verification (2026-10-06)

With correctly formed disposable SQL Server URLs, `scripts/verify.ps1` completed with exit code 0: **1613 passed, 0 failed, 0 skipped** in 1246.07 seconds. This includes the corrected session-envelope regression, all 108 frontend tests, SQL Server migration/concurrency/question-revision gates and the full repository test collection. Databases `PWD301_AGENT_POST172B_MIG_1006061204` and `PWD301_AGENT_POST172B_RACE_1006061204` were removed in cleanup. The worker image build passed separately, but live Browser/CUA, approved SMTP/inbox, file chooser/quarantine and historical disposition remain open; final audit status remains PARTIAL, not release-accepted.

## N-174 - owner scope decision and Browser revalidation (2026-10-06)

The owner confirmed that SMTP/inbox is not deployed and may be excluded from this acceptance cycle. No external email-delivery claim is required for this cycle, and the live worker remains stopped. A fresh Computer Use discovery still returns `apps=[]`, `browsers=[]`; `getBrowser({url: "http://127.0.0.1:5000"})` returns `No browser is available`. Therefore the final audit remains **PARTIAL - not release-accepted** solely with respect to the still-required Browser/CUA, file chooser/quarantine and historical notification-data disposition gates; no UI behavior is marked passed without Browser evidence.

## N-175 - Browser role and notification verification (2026-10-06)

Edge Browser Use became available and executed Student, Instructor and Admin demo flows. Login/logout toasts rendered; Instructor notification UI showed 15 unread records, repeated `#70014` presentation copies and mixed-language legacy text. Mark-all-read changed the visible unread count to 0 and showed `Đã đánh dấu tất cả thông báo là đã đọc.` Admin Operations showed `Email Outbox Delivery Queue DEGRADED`, `5/6 Node Hoạt Động` and zero queued/running/failed/succeeded jobs. Student access to `/admin/operations` returned to the dashboard with `Bạn không có quyền truy cập khu vực Quản trị viên.`

## N-176 - Browser file/quarantine boundary (2026-10-06)

The Student resource panel exposed four files and a clean PDF download completed with Browser Use. Live SQL currently has 123 `ACTIVE` and 7 `REJECTED` revisions, with no `PENDING` or `QUARANTINED` row. A direct Browser attempt against a rejected file URL returned `ERR_BLOCKED_BY_CLIENT` before an application response, so it is not counted as a verified 403. The upload file chooser event was captured, but Edge returned `Not allowed` when assigning the test file; Browser guidance identifies disabled Edge extension `Allow access to file URLs` as the cause. Final status remains **PARTIAL - not release-accepted**: SMTP/inbox is out of scope by owner decision, while upload/quarantine acceptance and historical disposition remain open, and no unsafe-file denial UI is marked passed.

## N-177 - Student notification verification (2026-10-06)


The Student Browser notification dropdown rendered `0 mới`, category filters and the `Học viên` role label. It exposed exam/course/system records, including Vietnamese business messages alongside legacy mixed-language text such as `Thong bao bao tri dinh ky` and opaque short messages. This confirms the role-facing UI and unread state, while message-language/catalog consistency remains an open finding. Final status remains **PARTIAL - not release-accepted**.
## N-178 - Browser upload revalidation (2026-10-06)

Immediately after the upload, the live revision summary was `ACTIVE=124`, `REJECTED=7`, and `PENDING/QUARANTINED=0`; the new accepted course-image revision is included in that snapshot.

The Browser file-chooser gate partially recovered. In the Instructor course-management UI, Edge accepted the clean fixture `E:\PWD301\frontend\assets\img\octopus_ai_icon.png`; the crop dialog was applied and the UI rendered `Đã cập nhật ảnh đại diện khóa học.` Read-only SQL Server verification found asset public ID `22F39CA6-09A9-478A-BB73-8E250FEAE622`, revision `150036`, `COURSE_IMAGE`, current revision `1`, asset/revision `ACTIVE`, detected MIME `image/jpeg`, and `FILE_VALIDATION=PASS` plus `MALWARE=PASS` from the built-in validators. No malicious fixture was uploaded.

The quarantine/unsafe-denial gate is still **UNVERIFIED**: the rejected-file URL continued to return Browser `net::ERR_BLOCKED_BY_CLIENT` before an application response, so this is not evidence of a verified 403 or a verified quarantine UI denial. SMTP/inbox remains **OUT OF SCOPE** by owner decision. Final audit status therefore remains **PARTIAL - not release-accepted**, with unsafe-file Browser evidence and historical notification-data disposition still open.
## N-179 - rejected-file route classification (2026-10-06)

A second, course-scoped inline Browser attempt also returned `net::ERR_BLOCKED_BY_CLIENT` before the application response. Read-only SQL classifies the sample `3EB32DEA-150D-4724-B42C-2FEBB53BAD16` as an asset in `PENDING` with a `REJECTED` revision and reason `Infected: ZIP-Embedded-Executable`, under published course `SEXGAY`, with no `lesson_resources` attachment. This explains why the Student resource UI has no historical quarantine card to render, but it does not prove a 403 or quarantine denial. Quarantine override was not run because it would release the rejected asset rather than test fail-closed access. Final status remains **PARTIAL - not release-accepted**.
## N-180 - authenticated rejected-file recheck (2026-10-06)

The rejected-file download was retried from the already authenticated Instructor tab through `/instructor/files/<asset>/download?disposition=inline`; Edge still returned `net::ERR_BLOCKED_BY_CLIENT` before an application response. The course-management tab was restored afterward. This rules out missing login/session context, but it still does not prove a 403 or a quarantine denial. The gate remains **UNVERIFIED** and the final audit remains **PARTIAL - not release-accepted**.
## N-181 - Instructor system-category verification (2026-10-06)

The authenticated Instructor notification dropdown was filtered to `Hệ thống` and rendered exactly two records: the legacy mixed-language maintenance message and the Vietnamese malware-rejection message. The UI retained `0` unread and closed back to the course page without mutation. This closes the structural category-filter check, not the language/ownership finding; final status remains **PARTIAL - not release-accepted**.
## N-182 - Instructor assessment-category empty state (2026-10-06)

The authenticated Instructor notification dropdown was filtered to `Khảo thí` and rendered the explicit empty state `Không có thông báo nào` / `Bạn đã xem hết các thông báo trong mục này.`, with `0` unread and no fabricated assessment item. This closes the scoped empty-state check only; it does not prove global assessment-producer coverage. Final status remains **PARTIAL - not release-accepted**.
## N-183 - Instructor course-category verification (2026-10-06)

The authenticated Instructor `Khóa học` filter rendered 16 records, including course/lesson lifecycle notifications and three related `#70014` rejection copies with different reasons. The dropdown was closed without mutation. This strengthens the direct Browser evidence for the historical duplicate family, but no historical row is deleted or merged without business identity and owner approval. Final status remains **PARTIAL - not release-accepted**.

## N-184 - Admin broadcast client-validation and no-write evidence (2026-10-06)

The authenticated Admin Browser flow opened the real `Phát thông báo` form. An empty submit showed `Vui lòng nhập tiêu đề thông báo.`; after entering only a title, submit showed `Vui lòng nhập nội dung thông báo.`. The modal was canceled. Read-only SQL Server verification from `pwd301_web` observed `143` notification events, `168` notifications, `115` `PENDING` email deliveries and `0` background jobs; the newest event was timestamped before the validation probe, so no broadcast/outbox write was observed. This closes only the invalid-form/no-write Browser branch. SMTP/inbox is **OUT OF SCOPE** by owner decision; valid broadcast delivery, file/quarantine denial and historical duplicate disposition remain open. Final status remains **PARTIAL - not release-accepted**.

## N-185 - rejected-file resource-path boundary (2026-10-06)

Read-only SQL Server inspection found all seven current `REJECTED` revisions have `resource_links=0` in `lesson_resources`; their parent assets remain `PENDING` with malware rejection reasons. The current Student resource panel therefore has no rejected/quarantined attachment to exercise. The direct rejected-file Browser route is still intercepted as `ERR_BLOCKED_BY_CLIENT` before an application response, so fail-closed denial remains **UNVERIFIED**, not a pass. No malicious fixture was uploaded and no quarantine override was run. Final status remains **PARTIAL - not release-accepted**.

## N-186 - authenticated rejected-file API gate (2026-10-06)

An authenticated Instructor HTTP session requested the existing rejected asset and received `403` JSON with `success:false`, `error.code=FILE_INFECTED`, and `File revision is rejected due to malware detection.`; no file bytes were returned. This closes the backend/API fail-closed boundary for the sampled asset. The Browser UI denial remains **UNVERIFIED** because Edge intercepts the direct route before the application response, and no rejected revision is attached to a user-facing resource. Final status remains **PARTIAL - not release-accepted**.

## N-187 - SMTP/inbox owner scope (2026-10-06)

The owner confirmed SMTP/inbox is not deployed and may be excluded from this acceptance cycle. External-provider delivery and inbox receipt are therefore **OUT OF SCOPE**, not passed and not counted as a skipped test. The live outbox backlog and degraded health state remain operational observations only; no external email was sent. Final status remains **PARTIAL - not release-accepted** because the Browser quarantine/UI gate, historical duplicate disposition and other explicitly open workflow coverage remain unresolved.

## N-188 historical duplicate disposition (2026-10-06)

This update materially narrows the historical disposition gate: 12 of 14 repeated presentation groups have direct business correlation, including exact 7/7 `FILE_REJECTED`-to-revision mapping; 2 groups/17 rows remain unkeyed legacy history. This is not a deletion/repair pass. Owner mapping and disposable repair rehearsal remain required. Final status remains **PARTIAL - not release-accepted**.

## N-189 Browser quarantine-override evidence (2026-10-06)

The primary-admin Browser session opened the real quarantine-override dialog and verified its required File Asset ID, security-reason and Super Admin password fields. Empty submission was rejected with `Vui lòng nhập File Asset ID.` and the dialog was canceled. This closes only the UI-validation subgate; no quarantined file was released, so the privileged release/audit-transition gate remains open. Final status remains **PARTIAL - not release-accepted**.

## N-190 focused quarantine backend verification (2026-10-06)

Focused backend evidence is green: 2 quarantine-override tests passed and 1 quarantined/infected fail-closed authorization test passed. This strengthens the UI evidence but does not close the credentialed live-release gate; no password, release action or live audit mutation was performed. Final status remains **PARTIAL - not release-accepted**.

## N-191 Browser console observation (2026-10-06)

The current Browser capture showed no application-level console error during the inspected flows. One existing Tailwind CDN production warning was observed; it is not treated as a notification pass or as closure of the remaining release gates.

## N-192 final legacy identity disposition (2026-10-06)

The deeper read-only check confirms that the 17 unresolved rows contain recipient-only `target_id` values, NULL `correlation_id`/`actor_user_id`, generic action URLs and no matching audit events. This strengthens the conclusion that owner mapping is required before any append-only repair. Final status remains **PARTIAL - not release-accepted**.

## N-193 authoritative continuation checkpoint (2026-10-06)

This section is the current continuation summary; earlier metric tables and checkpoint paragraphs remain historical traceability snapshots.

| Metric | Current evidence and scope |
|---|---|
| Notification inventory | 153 distinct audit cases in the register; live SQL currently has 143 `notification_events` and 168 `notifications` |
| Correct / incorrect total | No authoritative per-row total; the report preserves confirmed groups and marks unproven cases instead of estimating |
| Duplicate disposition | 14 presentation-copy groups; 12 have business correlation, 2 legacy groups (17 rows) remain unkeyed. The 14 groups are not all classified as duplicate delivery. Event-key duplicate query: 0; orphan event query: 0 |
| File rejection correlation | 7/7 `FILE_REJECTED` events map uniquely to rejected revisions; 0 ambiguous extras; maximum timestamp delta 10ms |
| Hard-code / language totals | Static snapshot: 384 `UI.showToast` occurrences; complete EN/VI/mixed-language totals remain unestablished and are reported as such |
| Confirmed defect groups | Frontend 5; Backend 3; API contract 5; business logic 1 plus open gaps; UX 7; severity triage P0: 0, P1: 15, P2: 5, P3: 0 |
| Current runtime state | 115 `PENDING` email deliveries, 0 background jobs, 254 audit events; SMTP/inbox is owner-authorized OUT OF SCOPE |
| Verification | Fresh full controlled verifier: 1613 passed, 0 failed, 0 skipped in 1260.83s; exit 0; disposable SQL Server migration/concurrency databases both cleaned with REMAINING=0; focused quarantine regression: 3 passed, 45 deselected |
| Browser gate | Edge Browser is available; role/UI flows and quarantine-override empty validation are evidenced. Rejected-file Browser denial and credentialed release transition remain unverified |
| Regression risk / conclusion | HIGH; final status remains **PARTIAL - not release-accepted** |

The eight required audit artifacts exist and the current Browser/SQL evidence is recorded. The Definition of Done is intentionally not marked complete because the rejected-file Browser denial gate and historical owner mapping/repair gate are still open; no live quarantine release or append-only history mutation was performed.

## N-194 rejected-file Browser client boundary (2026-10-06)

The fresh Edge attempt produced the browser-owned `ERR_BLOCKED_BY_CLIENT` page for the rejected-file URL; IAB was unavailable. This confirms an environment/client interception before the application response, not a 403 pass. The final audit therefore keeps Browser denial **BLOCKED ENVIRONMENT / UNVERIFIED**, while retaining the separately proven authenticated HTTP `403 FILE_INFECTED` backend boundary. Final status remains **PARTIAL - not release-accepted**.

## N-195 route-family Browser boundary (2026-10-06)

The API download route reproduces the same Edge `ERR_BLOCKED_BY_CLIENT` result as the Instructor route. This broadens the environment evidence without changing the conclusion: Browser UI/response-level denial remains unverified, and the final status remains **PARTIAL - not release-accepted**.
## N-196 exact business-window recheck (2026-10-06)

A further read-only SQL Server check searched `course_change_requests` in the exact event windows for the 13 unresolved `LESSON_CHANGE_REQUEST` copies (2026-09-28 03:10:04-03:16:28 UTC) and the four unresolved `COURSE_CHANGE_APPROVED` copies (2026-09-28 05:44:15-05:44:22 UTC and 2026-09-29 02:09:31 UTC). It returned no rows in those windows. Current CS101 change-request rows exist at other times, but none can be safely joined to these notifications from the stored recipient-only target, NULL correlation/actor fields and generic action URLs. This is additional evidence for an owner-approved mapping/rehearsal hold; no append-only history was mutated. Final status remains **PARTIAL - not release-accepted**.
## N-197 Browser fail-closed resource-visibility proof (2026-10-06)

Using the enrolled Student Browser session, a temporary, explicitly labeled `lesson_resources` row `120002` was attached to published SEXGAY lesson `130025` and pointed at existing asset `3EB32DEA-150D-4724-B42C-2FEBB53BAD16`. SQL identified the asset as `PENDING` with current revision `REJECTED`, reason `Infected: ZIP-Embedded-Executable`. The real Student `Tài liệu` panel still rendered only the four ACTIVE files and exposed no link, preview or download CTA for the rejected resource. A direct Student-scoped URL was separately attempted and Edge returned `net::ERR_BLOCKED_BY_CLIENT` before an application response, so the UI omission is the verified Browser fail-closed result and the direct response remains environment-blocked. The temporary resource row was then deleted by exact ID and label; SQL verified the lesson returned to four resource links, the rejected asset remained `PENDING`, its revision remained `REJECTED`, and it had zero resource links. No file revision, quarantine state, notification row or audit record was mutated. Final status remains **PARTIAL - not release-accepted** because direct Browser response observation and historical owner-approved notification disposition remain open.
## N-198 acceptance checkpoint after temporary Browser fixture (2026-10-06)

The temporary Browser fixture proves the Student-facing file-visibility branch: a linked `PENDING/REJECTED` asset was omitted from the real Student resource panel, while the four `ACTIVE` files remained visible. Exact cleanup restored the lesson to four resource links and left the asset/revision unchanged. Therefore Student UI fail-closed visibility is **PASS for this sampled asset**; the direct download response remains **BLOCKED ENVIRONMENT / UNVERIFIED** because Edge intercepts the URL before the application response. SMTP/inbox remains **OUT OF SCOPE** by owner decision. Historical notification disposition remains open for the two unkeyed groups/17 rows, so the overall audit remains **PARTIAL - not release-accepted**.
## N-199 historical outbox identity recheck (2026-10-06)

Read-only SQL Server inspection found one `email_deliveries` row for each of the 17 unresolved notification events. Those rows preserve recipient email, template code, random dedupe UUID and `PENDING` status, but have NULL subject/body and no `course_change_request_id`, target resource or correlation field. This provides no additional safe business identity for historical repair. SMTP/inbox remains owner-authorized **OUT OF SCOPE**; no delivery was attempted and no outbox/history row was mutated. Final status remains **PARTIAL - not release-accepted**.
## N-200 stale identity/content recheck (2026-10-06)

The unresolved notification bodies do contain coarse labels: all 13 `LESSON_CHANGE_REQUEST` copies name CS101 and Lesson `Bài 1: Tổng quan về Kiến trúc Web & HTTP Protocol`, but none stores a change-request ID, durable target ID or correlation. The four `COURSE_CHANGE_APPROVED` copies name the same Lesson but their CTA points to course UUID `cf547469-d8b8-43ef-882c-721048826232`, which is absent from the current `courses` table; the current CS101 row has a different public UUID. Current CS101 change-request rows exist, including multiple historical candidates for the same lesson, but none matches the notification event windows. This confirms stale/missing business identity rather than an unresolved title-only query; no historical row was reassigned, deleted or merged. Final status remains **PARTIAL - not release-accepted**.
## N-201 current Definition-of-Done checkpoint (2026-10-06)

This is the current requirement-level checkpoint against the pasted task, not a claim that every row is release-passed.

| Requirement group | Current status | Evidence boundary |
|---|---|---|
| Frontend, Backend, API, notification UI discovery | PARTIAL/PASS scoped | Static inventory plus live Browser/API/SQL samples exist; not every producer has a fresh end-to-end replay |
| Validation and business correctness | PARTIAL | Valid/invalid/permission/empty branches are evidenced for sampled flows; open producer and historical-data gaps remain |
| Language and message consistency | OPEN finding | Vietnamese paths pass in sampled flows, but legacy EN/mixed rows remain and complete unique-message counts are not normalized |
| Role and permission behavior | PASS scoped / PARTIAL breadth | Student, Instructor and Admin Browser/API boundaries were exercised; uncovered producer/role combinations remain |
| Database correlation | PASS scoped / PARTIAL breadth | Current lifecycle/file/grading samples correlate to SQL; 17 historical rows lack durable identity |
| Inventory, RCA, standard, fix plan, test matrix, regression plan | PASS as artefacts | Reports 02–07 contain the master inventory, root causes, standard, roadmap, matrices and regression evidence |
| Browser verification | PASS scoped / BLOCKED boundary | Edge login, role flows, filters, validation and Student fail-closed resource visibility passed; direct rejected-file response is blocked by Edge before app response |
| Success and failure cases | PARTIAL | Multiple real success/failure branches are recorded; unresolved valid flag, some course/prerequisite/regrade and download-finalization branches remain |
| Edge, duplicate, async and race coverage | PARTIAL | Targeted SQL/HTTP/Browser race/idempotency checks passed; broad timeout/cancel/unmount/retry and historical duplicate disposition remain open |
| Final audit and traceability | PASS as report / NOT release accepted | Eight reports and traceability are present; the conclusion correctly remains PARTIAL |

The exact global totals for “correct”, “incorrect”, unique hard-coded messages, and EN/VI/mixed messages remain **NOT ESTABLISHED** because the required proof is a per-case end-to-end replay and normalized message catalog, not a safe inference from callsite counts. SMTP/inbox is explicitly **OUT OF SCOPE** by owner decision. No historical append-only row was mutated.

## N-202 current static `UI.showToast` and message-language recheck (2026-10-06)

A read-only parser over the current `frontend/**/*.js` found 382 `UI.showToast(` callsites across seven files: 213 direct quoted literals, 73 template-literal calls and 96 other dynamic expressions; 201 unique direct literal messages. Under a deterministic heuristic (Vietnamese Unicode code points; common English UX-word co-occurrence marks mixed; otherwise EN-or-technical), the 213 literal callsites classify as VI 181, mixed 25, EN-or-technical 7; unique literals classify as VI 172, mixed 24, EN-or-technical 5. These are static callsite figures only, not a complete backend/API/inline/modal message catalog or proof that every dynamic value is localized. The current 382 supersedes the older 384 historical snapshot for this worktree. Hard-coded-message normalization remains open; final status remains **PARTIAL - not release-accepted**.

## N-203 fresh Student result CTA and stale-session boundary (2026-10-06)

A real Browser logout/login was performed with the Student demo account. Before the clean re-login, the already-open tab showed the Peppa Pig identity and a Dashboard grade CTA for attempt `790fe335-df86-418b-bd08-a6d39390b514`; navigation rendered the application permission error. Live `pwd301_web` SQL confirms that attempt belongs to `admin@pwd301.local` (user `1`), not `student1@pwd301.local` (user `4`). After logout/login, the header, Dashboard CTA (`db76cdce-bef6-470d-be11-7d35cc9ab96b`), SQL ownership and result page aligned; the Student result visibly rendered `1 / 16` and the real `download-student-result-pdf-btn` link. This is evidence of a stale-session/current-user boundary that recovered after explicit logout/login, not a claim that the stale state is acceptable or that every auth transition is covered. No business data was mutated.

## N-204 fresh Student notification-center language/data hygiene (2026-10-06)

The clean Student session opened the real notification center with `13` visible records and `0` unread. The `Khảo thí` filter rendered `7` records with Vietnamese score/reminder messages. The unfiltered view also exposed one unaccented ASCII maintenance message (`Thong bao bao tri dinh ky...`) and two test-like messages (`heo peppa caccaccac`, `bucutaodi thật là bá khí`), so the live catalog still contains legacy/test data and is not language-normalized. No delete or other notification mutation was submitted; final status remains **PARTIAL - not release-accepted**.

## N-205 focused regression checkpoint after fresh Browser replay (2026-10-06)

Current focused verification completed without skips: `pytest -q tests/api/test_student_backend_completion.py` returned **18 passed**, and `node --test tests/frontend/essay_grading_ui.test.js tests/frontend/notification_ui_contract.test.js` returned **5 passed, 0 failed, 0 skipped, 0 todo**. These checks cover the released-result PDF contract, answer-visibility wording, essay grading UI capability and notification UI contracts; they do not close the broader producer/role, file chooser/quarantine or historical append-only disposition gates. Final status remains **PARTIAL - not release-accepted**.

## N-206 current backend producer-key inventory (2026-10-06)

A fresh AST read-only inventory of `src/pwd301` found **35** direct `dispatch_notification()` callsites: **34** with an explicit `event_key`, **1** using a prebuilt event, and **0** with neither. This closes the static “unkeyed producer” count for the current worktree only; it does not prove every key is semantically correct under every retry/race path or replace SQL/Browser workflow replay. Final status remains **PARTIAL - not release-accepted**.

## N-207 current live SQL residue checkpoint (2026-10-06)

Read-only SQL Server verification inside the live `pwd301_web` environment reports `143` notification events, `168` notifications, `115` `PENDING` email deliveries, `0` background jobs and `254` audit events. The temporary rejected-resource fixture label has `0` rows and rejected asset `140012` has `0` lesson-resource links. No new notification, audit or file row was created by the latest Browser checks.

## N-208 Edge file-chooser permission boundary (2026-10-06)

The allowed Computer Use surface can operate the PWD301 tab, but Edge rejected opening `edge://extensions` with its Browser URL policy. Therefore the `Allow access to file URLs` extension permission could not be changed through this audit, and no workaround/CDP/policy bypass was attempted. File chooser/upload acceptance remains **BLOCKED ENVIRONMENT**, not a pass or skipped test.

## N-209 fresh full verification checkpoint (2026-10-06)

The current controlled verifier completed with **1613 passed, 0 failed, 0 skipped** in `1260.83s` and returned `VERIFY_EXIT_CODE=0`. The run included the repository checks, Python compile, Ruff, format, mypy, frontend Node tests and the full pytest suite against disposable SQL Server migration/concurrency databases. The wrapper then dropped `PWD301_AGENT_CUR_MIG_20261006A` and `PWD301_AGENT_CUR_RACE_20261006A`; both reported `REMAINING=0`. This strengthens the automated regression result but does not close the separately scoped Browser file-chooser/direct-response environment boundary, the 17-row historical append-only identity/owner-approval hold, or SMTP/inbox, which remains owner-authorized **OUT OF SCOPE**. Overall status remains **PARTIAL - not release-accepted**.

## N-210 fresh Student notification filter coverage (2026-10-06)

The live Student Browser notification dropdown was reopened and exercised without submitting a mutation. `Khóa học` rendered **2** records; `Hệ thống` rendered **4** records and exposed the already-recorded legacy ASCII maintenance message plus test-like rows; `Chưa đọc (0)` rendered the explicit empty state `Không có thông báo nào` and `Bạn đã xem hết các thông báo trong mục này.`. This adds real Browser coverage for category and empty-state branches, but does not resolve the language/data-normalization finding. Overall status remains **PARTIAL - not release-accepted**.

## N-211 Instructor file-chooser boundary (2026-10-06)

After a real Instructor demo login, the course-authoring page exposed both `Tải ảnh bìa ngay` and `Đổi Ảnh Đại Diện Khóa Học`. Clicking each visible upload control left the Browser page unchanged; no native file dialog appeared in the Computer Use surface and no file was selected, transmitted or persisted. This is an additional **BLOCKED ENVIRONMENT / UNVERIFIED** file-chooser observation, not an upload pass. The session was then logged out and restored to the Student demo account; no course, file, notification or audit data was mutated. Overall status remains **PARTIAL - not release-accepted**.

## N-212 Admin role notification coverage (2026-10-06)

A real Admin demo login exercised the live notification center. The default `Chưa đọc (0)` view showed the explicit empty state; `Tất cả` showed **15** records, `Khóa học` **10**, and `Hệ thống` **3**. The system subset included the legacy ASCII maintenance message, backup-completed notification and security-login-warning notification. No notification mutation was submitted; the Admin session was logged out and the Student demo account was restored. This closes a scoped Admin role/filter observation, while the legacy/data-quality finding and overall audit status remain **PARTIAL - not release-accepted**.

## N-213 Instructor role notification coverage (2026-10-06)

A real Instructor demo login exercised the live notification center. `Tất cả` showed **18** records, `Khóa học` **16**, and `Hệ thống` **2**; both `Khảo thí` and `Chưa đọc (0)` showed the explicit empty state. The system subset included the legacy ASCII maintenance record and the rejected-malware upload notification. No notification mutation was submitted; the Instructor session was logged out and the Student demo account was restored. This closes a scoped Instructor role/filter observation, while language/data normalization and the overall audit status remain **PARTIAL - not release-accepted**.

## N-214 current notification API regression (2026-10-06)

The focused current-worktree command `python -m pytest -q tests/api/test_notification_api.py` completed with **16 passed in 10.59s**, exit code `0`. This strengthens the backend/API evidence for the covered lifecycle, filtering, dismissal, preferences, broadcast/idempotency and envelope cases; it does not convert the unrun outage/status-code branches, complete producer breadth, Browser rendering or external SMTP/inbox into passes. Overall status remains **PARTIAL - not release-accepted**.

## N-215 current Admin lesson-flag notification regression (2026-10-06)

The focused command `python -m pytest -q tests/api/test_admin_lesson_flag_notification.py` completed with **9 passed**, exit code `0`. Durable audit/owner notification, REST/Web idempotency replay, changed-payload rejection and rollback when notification dispatch fails all passed in the isolated API/DB suite. This strengthens the business-flow evidence but does not close live Browser producer breadth, file/quarantine response, historical identity or SMTP/inbox; overall status remains **PARTIAL - not release-accepted**.

## N-216 current notification service/security/frontend regression (2026-10-06)

Fresh focused checks completed without skips: notification service unit **15 passed in 8.68s**; notification IDOR/security **7 passed in 4.06s**; and the combined frontend notification/router/topbar command **18 passed, 0 failed, 0 skipped**. These results strengthen the named backend/security/frontend contracts but do not close full producer/role breadth, Browser file/quarantine behavior, historical identity or external SMTP/inbox; overall status remains **PARTIAL - not release-accepted**.

## N-217 current producer/business-flow regression (2026-10-06)

Fresh focused checks completed without skipped tests: Admin backend **16 passed in 11.25s**; Admin sub-role/RBAC **5 passed in 4.12s**; selected course-changeset cases **2 passed, 10 deselected in 1.98s**; and selected lesson-change cases **5 passed, 3 deselected in 4.37s**. Deselected cases are not counted as passes. This strengthens approval/rejection, reassignment, broadcast, sub-role/RBAC, changeset and lesson-review evidence but does not close every producer, live Browser, historical-identity or external SMTP/inbox gate; overall status remains **PARTIAL - not release-accepted**.

## N-218 current Browser timing replay (2026-10-06)

Fresh Edge Computer Use verification began from a clean logged-out boundary and used the visible Instructor demo login. The login reached the correct Instructor dashboard; the captured transition showed the login-success toast and the subsequent settled dashboard. The notification center initially exposed the legitimate `Chưa đọc (0)` empty state. Selecting `Tất cả` rendered **18** Instructor notifications (**16** course and **2** system/security); `Khảo thí` remained empty. No mutation was performed, and the session was logged out before restoring Student1. This is **PASS for the captured Instructor login/filter timing scope**, not proof of sub-render timing before observation, all-role timing, file/quarantine UI or SMTP/inbox delivery; final status remains **PARTIAL - not release-accepted**.

## N-219 current Guest notification boundary (2026-10-06)

Fresh Edge logout returned to `#/auth` and showed no notification control. Direct navigation to `/auth/notifications` was intercepted with `net::ERR_BLOCKED_BY_CLIENT` before the application response. Therefore the API-level unauthenticated 401 is evidenced by the focused session test, but the Guest Browser error mapping remains **UNVERIFIED**, not a pass. Student1 was restored afterward with the correct dashboard identity and no notification/business mutation. Final status remains **PARTIAL - not release-accepted**.

## N-220 focused notification API rerun (2026-10-06)

Fresh command `python -m pytest -q tests/api/test_notification_api.py` completed with **16 passed in 10.15s**, exit code `0`, with no skipped tests. This strengthens the covered notification lifecycle/API/session regression only; unrun 422/429/502/503 branches, complete producer and Browser Guest presentation remain open, while SMTP/inbox remains explicitly **OUT OF SCOPE**. Final status remains **PARTIAL - not release-accepted**.

## N-221 current disjoint no-skip verification checkpoint (2026-10-06)

The current `verify.ps1` run exited `0` and completed the repository, lint/type, frontend and pytest phases, but its pytest phase reported **1609 passed, 4 skipped** because SQL Server opt-in URLs were absent; the wrapper does not enforce a zero-skip policy. The exact disposable SQL helper then executed all integration cases with SQL URLs injected and returned **17 passed in 24.58s**. Both created databases reported `audit_database_remaining=0` after cleanup. Removing the 13 overlapping non-SQL integration cases yields the current disjoint automated result **1613 passed, 0 failed, 0 skipped**. This closes the automated no-skip verification gate only; Browser file/Guest interception, historical append-only identity/approval and SMTP/inbox scope remain unresolved or out of scope. Final status remains **PARTIAL - not release-accepted**.

## N-222 disposable producer/idempotency replay checkpoint (2026-10-06)

The exact disposable SQL Server fixture passed all named producer/replay probes with zero skips: copy visibility/event-key conflict **2 cases**; seed idempotency **1**; enrollment keys **3**; course lifecycle key replay **4**; and password-change, reset-token and suspension security-key replays **9**. All reported `failed_expectations=0`; durable event/notification/email rows remained stable on exact replay, and cleanup returned `audit_database_remaining=0`. This strengthens the SQL/API idempotency boundary only; Browser rapid retry, complete semantic producer coverage, historical owner-approved disposition and SMTP/inbox remain unresolved or out of scope. Final status remains **PARTIAL - not release-accepted**.

## N-223 disposable lesson-flag idempotency checkpoint (2026-10-06)

The isolated Admin lesson-flag REST replay passed **3 cases, 0 failed, 0 skipped**: first request `200` with `idempotent_replay=false`, exact retry `200` with `idempotent_replay=true`, and changed payload with the same key `409 CONFLICT`. SQL confirmed exactly one audit, one event and one owner notification; the audit database cleanup returned `audit_database_remaining=0`. This closes the named moderation producer retry scope only; Browser rapid-click visuals, other producers, historical disposition and SMTP/inbox remain open or out of scope. Final status remains **PARTIAL - not release-accepted**.

## N-224 notification HTTP status applicability checkpoint (2026-10-06)

The notification blueprint currently returns `200` for all logical success operations. The exercised exception families are `400/401/403/404/409`; source inspection confirms no notification-specific `201`, `204`, `422` or `502` path. Global `429` and `503` handlers belong to unrelated rate-limit or AI/maintenance classes and were not shown on a notification route. Unexpected `500`, outage/maintenance injection and retry-after behavior remain unrun, so this narrows but does not close the HTTP-status gate. Final status remains **PARTIAL - not release-accepted**.

## N-225 focused notification HTTP status regression checkpoint (2026-10-06)

The fresh command `PYTHONPATH=src python -m pytest -q tests/api/test_notification_api.py tests/security/test_notification_idor.py` returned **23 passed in 9.89s**, exit code `0`, with no skipped tests. The assertions cover notification `200` success/lifecycle responses, `400` malformed or invalid mutation input, `401` anonymous access, `403` IDOR/non-admin denial and `409` changed idempotency payload. This adds no notification-specific `404`, `422`, `429`, `500`, `502` or `503` injection; those status cases remain unverified and the overall audit remains **PARTIAL - not release-accepted**.

## N-226 current Student Browser notification-surface checkpoint (2026-10-06)

The live Edge Computer Use tab remained available at the authenticated Student dashboard for `Lê Hoàng Long`. The real notification popover visibly rendered `Thông báo 0 mới`, `Chưa đọc (0)`, the role label `Học viên` and **13** notification records across the category filters. It was closed through the visible control without read, dismiss, delete, upload or other business mutation. This confirms the current Student Browser surface, but not all-role timing, keyboard accessibility, file chooser behavior or SMTP/inbox delivery; the overall audit remains **PARTIAL - not release-accepted**.

## N-227 isolated notification 404 contract checkpoint (2026-10-06)

An isolated Flask test-client probe on in-memory SQLite authenticated a disposable Student and exercised missing and malformed notification IDs for mark-read and delete. All three responses returned **404** with `success=false`, `data=null` and `error.code=RESOURCE_NOT_FOUND`; no live database or notification history was touched. This closes the sampled notification `404` mapping only; `422/429/500/502` fault-injection cases remain unverified.

## N-228 notification maintenance 503 and retry-after checkpoint (2026-10-06)

The existing E2E command `PYTHONPATH=src python -m pytest -q tests/e2e/test_admin_ops_lifecycle_e2e.py` returned **5 passed in 4.37s**, exit code `0`, with no skipped tests. Its disposable maintenance window asserted Student `GET /api/notifications/unread-count` returns **503**, `MAINTENANCE_MODE_ACTIVE` and `Retry-After: 1200`, then returns `200` after maintenance ends. This closes the sampled notification maintenance/`503`/`Retry-After` path, while unexpected `500` and notification-specific `422/429/502` injections remain unverified; the overall audit remains **PARTIAL - not release-accepted**.

## N-229 isolated notification 500 and 429 fault-injection checkpoint (2026-10-06)

An isolated Flask test-client probe on in-memory SQLite patched the notification list dependency to raise a generic runtime fault and observed **500** with `success=false`, `data=null`, `error.code=INTERNAL_ERROR` and a user-safe message. A patched failed-email retry dependency raised `EmailRateLimitExceededError` and observed **429** with `error.code=RATE_LIMIT_EXCEEDED` and `Retry-After: 60`. No live database or notification history was touched. This closes the sampled notification `500/429` contract; notification-specific `422/502` remains source-level absent/uninjected and the overall audit remains **PARTIAL - not release-accepted**.

## N-230 notification 422/502 applicability boundary checkpoint (2026-10-06)

The read-only source check confirms notification validation uses the shared `ValidationError` mapped to `400`; no notification route returns `422` or `502`, and the global domain-handler table has no notification mapping for either status. These statuses are **not applicable at the Flask notification boundary**, not skipped notification cases. Any reverse-proxy or external-upstream `502` is a separate infrastructure contract outside this audit; the overall notification audit remains **PARTIAL - not release-accepted**.

## N-231 corrected AST producer inventory checkpoint (2026-10-06)

A corrected read-only AST pass over `src/pwd301` classified the actual dispatcher keywords and found **35** direct calls: **34** explicit deterministic `event_key` calls, **1** prebuilt `event` at `src/pwd301/services/course_service.py:286`, and **0** without either identity. The earlier local probe searched for an obsolete `notification_event_id` keyword and was rejected as an audit-harness classification error; no product source changed. This confirms static producer-count accuracy only; semantic correctness and runtime retry/race coverage remain open, so the overall audit remains **PARTIAL - not release-accepted**.

## N-232 fresh Student Browser category-filter checkpoint (2026-10-06)

The authenticated Edge Computer Use Student session opened the real notification popover and rendered `Thông báo 0 mới`, `Chưa đọc (0)`, and the role label `Học viên`. Read-only filter selection showed **13** records in `Tất cả`, **7** in `Khảo thí`, **2** in `Khóa học` and **4** in `Hệ thống`; no delete, dismiss, mark-read, refresh, upload or other business mutation was invoked. This is a current Student Browser rendering pass only. The overall audit remains **PARTIAL - not release-accepted** because all-role semantic producer/retry coverage, keyboard coverage, Browser file chooser/direct rejected-file verification and owner-approved historical repair remain open. SMTP/inbox delivery remains explicitly **OUT OF SCOPE** because no mail provider is deployed.

## N-233 repeated Instructor file-chooser boundary checkpoint (2026-10-06)

The live Edge session logged in as the demo Instructor, opened the OPS401 lesson studio and activated the real document chooser control. No native chooser or separate file surface appeared; `cua.getState({emit:false})` still reported `apps=[]` and only the Edge Browser. The AX tree retained the pre-existing clean attachment and no upload placeholder, so no product or live business data changed. File selection, rejected-file response and quarantine-release acceptance remain **BLOCKED ENVIRONMENT / UNVERIFIED**, and the overall audit remains **PARTIAL - not release-accepted**. SMTP/inbox delivery remains explicitly **OUT OF SCOPE**.

## N-234 broader producer-service regression checkpoint (2026-10-06)

The fresh isolated unit command over course, enrollment, user/role and lesson services returned **90 passed in 59.65s**, exit code `0`, with no skipped tests. This strengthens fixture-level service evidence but does not claim that all 35 dispatcher callsites, every role, every rapid retry/race branch or the full Browser/API/DB/user-result chain is complete. The overall audit remains **PARTIAL - not release-accepted**.

## N-235 assessment/file producer-service regression checkpoint (2026-10-06)

The fresh isolated unit command over attempt service, attempt submission service, file service and malware scan service returned **38 passed in 26.90s**, exit code `0`, with no skipped tests. This adds fixture-level assessment/file/security regression evidence, but all-producer semantic coverage, Browser file chooser/rejected-file/quarantine acceptance, and the remaining role/retry matrix are still open. The overall audit remains **PARTIAL - not release-accepted**.

## N-243 current dispatcher identity checkpoint (2026-10-06)

An independent AST scan over current Python source found **35** direct `dispatch_notification()` calls: **34** explicit `event_key`, **1** prebuilt `event`, **0** missing identity and zero parse errors. This closes the static identity-presence checkpoint only; correct durable key derivation, all-role semantics and runtime retry/race convergence remain open. Overall status remains **PARTIAL - not release-accepted**.

## N-242 producer-heavy service regression checkpoint (2026-10-06)

The fresh producer-heavy command over authorization, notification core, email/outbox, completion and instructor-application services returned **64 passed in 53.59s**, exit code `0`, with no skipped tests. This strengthens fixture-level producer coverage, but does not close complete semantic producer/role/rapid-retry coverage or the Browser file/quarantine gate. Overall status remains **PARTIAL - not release-accepted**.

## N-241 current Admin lesson-flag reconciliation checkpoint (2026-10-06)

The current Admin lesson-flag routes and service signature were rechecked after the historical RCA-040/RCA-027 entries. The dedicated command returned **9 passed in 7.28s**, exit code `0`, with no skipped tests, including current REST/Web delivery, malformed-body guards, idempotency/conflict and rollback. RCA-040/RCA-027 are therefore **historical/superseded for the current worktree**, not current open defects. This does not close the separate complete producer/role/retry, Browser file/quarantine or historical identity gates. Overall status remains **PARTIAL - not release-accepted**.

## N-240 fresh API/frontend notification checkpoint (2026-10-06)

Fresh verification completed without skips: `PYTHONPATH=src python -m pytest -q tests/api/test_notification_api.py tests/security/test_notification_idor.py` returned **23 passed in 15.20s**, exit code `0`; `node --test tests/frontend/*.test.js` returned **108 passed, 0 failed, 0 skipped, todo 0**, exit code `0`. These results strengthen the API/IDOR/frontend regression gate only. They do not close complete producer/role/retry-race coverage, Browser file chooser/quarantine response coverage, historical owner approval or SMTP/inbox scope. Overall status remains **PARTIAL - not release-accepted**.

## N-239 fresh Admin notification-filter checkpoint (2026-10-06)

The follow-up Edge Admin replay exercised all visible read-only filters and rendered `Tất cả=15`, `Chưa đọc (0)`, `Khảo thí=1`, `Khóa học=11` and `Hệ thống=3`. No delete, dismiss, mark-read or refresh mutation was invoked. This corrects the interpretation of N-237: its initial 3-record result was the already-selected system category, not the Admin total. It strengthens current Admin UI/filter evidence only; producer completeness and runtime retry coverage remain open. Overall status remains **PARTIAL - not release-accepted**.

## N-237 fresh Admin notification-center checkpoint (2026-10-06)

After a fresh demo Admin login, the authenticated Edge session opened the real notification center and rendered `Thông báo 0 mới`, `Chưa đọc (0)`, role `Quản trị viên` and **3** persisted records: maintenance, completed backup and abnormal administrator-login security warning. The list was inspected without delete, dismiss, mark-read or refresh mutation. This is a scoped Admin UI/rendering pass and does not claim complete Admin producer or broadcast coverage. Overall status remains **PARTIAL - not release-accepted**.

## N-238 fresh Guest protected-route checkpoint (2026-10-06)

After Admin logout, Edge navigation to `#/student/notifications` redirected to `/auth`; the Guest AX tree rendered the login surface and no authenticated topbar notification control. This closes one client route-boundary observation only; API unauthenticated `401` evidence remains separate. SMTP/inbox delivery remains explicitly **OUT OF SCOPE** because no mail provider is deployed, and is neither a pass nor a failed product gate. Overall status remains **PARTIAL - not release-accepted**.

## N-236 fresh Instructor notification-center checkpoint (2026-10-06)

The authenticated Edge Instructor session on the OPS401 lesson studio opened the notification center and rendered `Thông báo 0 mới`, `Chưa đọc (0)`, role `Giảng viên` and **2** records, including the persisted security notification for rejected/quarantined `X_SENTINEL_VIBECODE_BASELINE_V2.zip`. No notification mutation was invoked. This closes only the current Instructor rendering observation; the upload-trigger, rejected-file response and quarantine-release chain remain **BLOCKED ENVIRONMENT / UNVERIFIED**, and the overall audit remains **PARTIAL - not release-accepted**. SMTP/inbox remains explicitly **OUT OF SCOPE**.

## N-251 frontend mechanism inventory checkpoint (2026-10-06)

The current static parser scanned 10 frontend JavaScript files and counted 383 actual `UI.showToast` invocations: 214 quoted literals, 73 template literals, 96 dynamic expressions and 202 unique quoted literal payloads. It also found `UI.alert` 2, `UI.confirm` 30, `UI.prompt` 8 and direct `window.confirm` 1; native `window.alert`, native `window.prompt` and `<dialog>` were 0. Accessibility markers were 6 `aria-live` and 4 `role="alert"`; the shared toast layer contains one `toast_` id marker. Five additional `UI.showToast` references are guards/type checks and are excluded from invocation totals. This is static evidence only and does not close the per-producer language, HTTP-status, role, duplicate, retry or Browser result matrix. No product code or live business data changed. Overall status remains **PARTIAL - not release-accepted**; SMTP/inbox remains explicitly **OUT OF SCOPE**.
## N-252 producer execution coverage checkpoint (2026-10-06)

The focused coverage run executed 312 backend/API tests and 6 targeted follow-up tests; all 318 passed with zero failures and zero skips. Three disposable SQLite/temp-storage probes also passed: prerequisite rejection returned 202 for staging and 200 for review, persisted one `COURSE_PREREQUISITE_REJECTED` event/notification and created no link; rejected file revision persisted one `FILE_REJECTED` SECURITY event/notification with no blob; and the YouTube probe covered valid/network-error suppression, broken-video delivery, route 401/200 and exact one-event/one-notification replay. AST-to-coverage correlation shows **35/35 direct `dispatch_notification()` callsites covered, 0 uncovered**. This closes producer line-execution evidence only; complete role/message ownership, timeout/cancel/unmount, rapid-retry race, Browser result and historical-data gates remain open. No product code or live business data changed. Overall status remains **PARTIAL - not release-accepted**; SMTP/inbox remains explicitly **OUT OF SCOPE**.
## N-253 Browser auth-error accessibility checkpoint (2026-10-06)

Fresh Edge submitted invalid credentials through the real login form. The page remained at `/auth` and showed exactly one visible inline `#auth-error-alert` with `Email hoặc mật khẩu không chính xác.`; no shared toast was observed. The element remained visible after the approximately 6.45-second interaction/observation sequence, but its live DOM had no explicit `role` or `aria-live`. This adds RCA-068 as an open P2 accessibility/ownership finding. No account or business data changed. Overall status remains **PARTIAL - not release-accepted**; SMTP/inbox remains explicitly **OUT OF SCOPE**.
## N-254 Browser file-chooser boundary checkpoint (2026-10-06)

The real Instructor Lesson Studio exposed `#btn-choose-doc-file` and hidden file inputs. The supported Computer Use upload flow waited for `filechooser` before clicking the control, but no chooser event arrived before timeout; the Browser debugger detached afterward. A post-failure inventory showed `apps=[]` and only Edge. No file was selected, no upload request was confirmed and no live business data was changed. This strengthens the existing environment blocker for file selection, rejected-file response and quarantine-release acceptance; it is **not** a pass and not counted as skipped. Overall status remains **PARTIAL - not release-accepted**; SMTP/inbox remains explicitly **OUT OF SCOPE**.
## N-255 producer semantic role checkpoint (2026-10-06)

The current AST semantic inventory mapped all 35 direct producers: 34 use explicit deterministic `event_key` values and one passes a prebuilt event; zero lack both identity forms. Literal categories are COURSE 20, SECURITY 6 and SYSTEM 8, with one dynamic category. Only 17 callsites explicitly declare `target_role` (INSTRUCTOR 13, STUDENT 2, ADMIN 2); 18 omit the role or pass `None`, so the shared dispatcher treats them as broad/unscoped. One assessment event type is dynamic. This strengthens the producer contract inventory but does not prove that every broad path is correct for each role, multi-role account, message language or retry ordering. Overall status remains **PARTIAL - not release-accepted**; SMTP/inbox remains explicitly **OUT OF SCOPE**.
## N-256 focused role/retry runtime checkpoint (2026-10-06)

The focused semantic command returned **8 passed, 0 failed, 0 skipped in 5.63s**. It proved keyed replay without fan-out duplication, changed-payload conflict rejection, target-role isolation, Student/Instructor enrollment fan-out and persistence, audit-scoped course lifecycle keys, and recipient-scoped reassignment keys. This strengthens representative producer semantics only; the 18 broad/unscoped producer paths, full async timeout/cancel/unmount/retry matrix, Browser file boundary and historical owner-approved disposition remain open. Overall status remains **PARTIAL - not release-accepted**; SMTP/inbox remains explicitly **OUT OF SCOPE**.
## N-257 — historical notification approval packet (2026-10-06)

The final audit now links the exact read-only disposition packet for the open
historical gate. SQL Server returned 13 unresolved `LESSON_CHANGE_REQUEST`
events (`50002–50014`) and four unresolved `COURSE_CHANGE_APPROVED` events
(`60002–60004`, `90006`). Each has one notification and one email-delivery row;
all event keys are unique, so the repeated copy is not by itself proof of
duplicate delivery. Missing durable request/target/correlation identity and a
stale approval CTA UUID prevent safe reassignment. Owner mapping, approval and a
disposable repair rehearsal remain required; all 17 rows are preserved
unchanged. See [`09_HISTORICAL_NOTIFICATION_APPROVAL_PACKET.md`](09_HISTORICAL_NOTIFICATION_APPROVAL_PACKET.md).
SMTP/inbox remains **OUT OF SCOPE** by owner decision. Overall status remains
**PARTIAL — not release-accepted**.
## N-258 — second Browser file-chooser recheck (2026-10-06)

Edge was available again and the real Lesson Studio document chooser was
visible. The supported `filechooser` wait/click flow timed out after 5 seconds a
second time and reset the Browser session. The harmless fixture was not
selected, no upload request was confirmed and no durable data changed. This
remains **BLOCKED ENVIRONMENT / UNVERIFIED**, not a pass or skipped test;
SMTP/inbox remains **OUT OF SCOPE**.
## N-259 — fresh Browser category/content evidence (2026-10-06)

Fresh Edge Instructor evidence opened the real notification popover, filtered
`Khóa học` and counted 16 visible cards, then filtered `Hệ thống` and observed
the unaccented legacy maintenance message beside the Vietnamese malware notice.
The course sample included two `#70014` copies with different rejection
reasons, current `CS201` content and historical lesson/course copies. The
popover was closed without read/delete mutation. This confirms the sampled
historical-copy and message-catalog findings but does not establish global
language/producer totals. Overall status remains **PARTIAL — not
release-accepted**.
## N-260 — producer role-view refinement (2026-10-06)

The follow-up AST inspection refines the earlier 18-callsite boundary: every
callsite supplies a concrete recipient user, so no blanket cross-user fan-out
defect is claimed. The open issue is same-user role-view breadth: NULL
`target_role` is visible in any selected role filter, while prerequisite,
review, intervention, instructor-application and YouTube notifications can
carry route-specific CTAs. Account-level security/role messages may be
intentionally broad. This producer-by-producer multi-role/CTA matrix remains
open; overall status remains **PARTIAL — not release-accepted**.
## N-261 — confirmed multi-role role-filter/CTA defect (2026-10-06)

The Admin demo account has ADMIN, INSTRUCTOR and STUDENT roles. A fresh
read-only JWT replay returned the same public notification
`d553d1ec-547c-4ebc-889d-7c91e274229e`, with `target_role=null` and the Admin
review CTA `#/admin/change-requests/review?id=50002`, for all three role
filters; each response was HTTP 200. This confirms same-user role-view
contamination and CTA mismatch, while not showing cross-user leakage. No
mutation was performed. Overall status remains **PARTIAL — not
release-accepted**.
## N-262 — notification schema-contract drift (2026-10-06)

Live SQL Server at migration revision `b3c4d5e6f7a9` confirms
`notifications.target_role`, `ix_notifications_user_role_unread` and
`ck_notifications_target_role`, all introduced by the runtime migration/model.
The canonical notification data dictionary omits them. This documentation and
schema-contract gap directly obscures the NULL-role behavior behind N-261; no
live schema/data was changed. Overall status remains **PARTIAL — not
release-accepted**.
## N-263 — role-test coverage boundary (2026-10-06)

The focused existing role command returned **3 passed, 0 failed, 0 skipped in
1.58s**. It correctly covers explicit target-role isolation and invalid role
filters, but its oracle intentionally allows NULL-target rows in both roles and
does not validate CTA route ownership. Therefore it does not contradict N-261;
the live multi-role Admin CTA mismatch remains an uncovered business contract
case. Overall status remains **PARTIAL — not release-accepted**.
## N-264 — cross-user isolation recheck (2026-10-06)

Student1's valid STUDENT notification list returned HTTP 200 with zero matches
for the Admin-review CTA; INSTRUCTOR and ADMIN filters returned HTTP 400 because
the account lacks those roles. This scoped negative case confirms N-261 is not
cross-user IDOR. Same-user multi-role CTA mismatch remains open, so overall
status remains **PARTIAL — not release-accepted**.
## N-265 — Browser route-guard refinement (2026-10-06)

Static source tracing shows notification item/modal handlers pass the stored
`action_url` directly to `AppRouter.navigate()` (`router.js:1615-1649, 1713`)
without checking `target_role`. The Admin route guard (`router.js:299-323`)
auto-switches a multi-role account to ADMIN, while an Instructor-only session
receives `Bạn không có quyền truy cập khu vực Quản trị viên.` and is redirected
to `#/instructor/dashboard`. Fresh Edge verification opened the exact target
`#/admin/change-requests/review?id=50002` in a temporary tab and visibly
recorded that warning plus the Instructor dashboard; the tab was then closed,
and no notification/business mutation occurred. This confirms late route
containment, not CTA correctness: N-261 remains open for upstream role-view
selection and explicit CTA ownership. Overall status remains **PARTIAL — not
release-accepted**.
