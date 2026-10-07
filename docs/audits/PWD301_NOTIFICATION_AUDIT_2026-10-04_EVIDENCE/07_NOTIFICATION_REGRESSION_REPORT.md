# 07_NOTIFICATION_REGRESSION_REPORT

## New executed failing business probe — not hidden by green suites

No product code changed in this checkpoint. A freshly recreated disposable SQL Server + Browser lesson-flag flow returned web HTTP 500 and no durable moderation/notice. The added `flag-probe` audit action ran ten REST cases: **6 expected status matches, 4 failed expectations, 0 skipped, exit 1**. Exact five-character input fails the same AuditEvent constructor; string/list bodies fail missing `.get`. These failures remain open and are not part of the earlier 1579 pytest/101 Node pass totals. Existing green suites lacked these business cases.

| Before / branch | Expected | Actual | After / status |
|---|---|---|---|
| Empty Browser flag reason | Validation; no mutation | Vietnamese warning; prompt remains; DB unchanged | Rejection PASS, inline UX gap |
| Valid Browser + REST flag | Durable flag/audit/owner notice | 500; zero flag/audit/event/notice | CONFIRMED FAIL, fix not implemented |
| String/list REST body | 400, no mutation | 500, no mutation | CONFIRMED FAIL, type guard still missing here |
| Guest/Instructor/Student REST calls | 401/403/403, no mutation | Matching statuses and unchanged DB | Scoped permission PASS; not full Sub-Admin coverage |
| Empty/4-char/missing lesson REST calls | 400/400/404, no mutation | Matching statuses and unchanged DB | Scoped validation/resource PASS |

## Admin sub-role continuation

All four synthetic sub-admin accounts were logged in through the visible Browser form. Each opened its own `ROLE_CHANGED` notification, marked/read-confirmed it and followed the role-specific CTA successfully: course review → `courses`, instructor review → `applications`, teaching assignment → `reassign`, system monitoring → `operations`. SQL correlated one role audit plus one durable notice per account, and REST list replay returned one own read item for each. The course-review sub-admin reached the flag prompt but exact `abcde` returned 500; the other three sub-admins returned 403 from the REST flag endpoint with no moderation mutation. Sub-admin probe result: **8 checks, 1 failed expectation, 0 skipped, exit 1**.

Full response/correlation/SQL evidence is [flag-runtime-evidence.md](flag-runtime-evidence.md). No fabricated owner success or post-commit-loss claim is made; successful notification path is not reached. The helper's wrong guessed import was corrected before this execution; Ruff check passed. This checkpoint changes audit documentation/helper only, preserving product edits.

## Post-fix moderation regression — SQL Server + Browser

The previous failure was repaired with a TDD-first change: both routes now reuse `flag_lesson_content`, which calls the canonical audit service, rejects malformed JSON before field access, attaches the owner's canonical course-management CTA, and commits the flag/audit/notice atomically. A focused rollback test forces the notification sink to fail and confirms no partial moderation state remains.

| Branch | Expected | Current evidence | Status |
|---|---|---|---|
| Browser exact `abcde` | Success toast and durable owner notice | Visible Admin flow returned HTTP 200; toast appeared; SQL showed one flag, audit, event and notice | PASS Browser + SQL |
| REST valid long reason | 200 and durable state | Fresh SQL Server probe returned 200; SQL showed flag/audit/event/notice | PASS |
| REST exact `abcde` | 200 and durable state | Fresh probe returned 200; SQL flag/audit/event/notice persisted | PASS |
| REST string/list | 400, unchanged state | Both returned 400 `VALIDATION_ERROR`; SQL unchanged | PASS |
| Web malformed body | 400, unchanged state | Focused web regression passed | PASS |
| Forced notification failure | 500 without partial state | Focused rollback regression passed | PASS |
| Four Admin sub-roles | Own notice; 200 only for COURSE_REVIEW, 403 for other scopes | Fresh SQL replay 8/8 checks passed; earlier Browser detail/CTA evidence retained | PASS scoped |

The post-fix flag probe is **10 expected matches, 0 failures, 0 skipped, exit 0**. The sub-admin probe is **8 expected checks, 0 failures, 0 skipped, exit 0**. This closes RCA-040/RCA-027 for the lesson-flag path, but does not close global notification duplicate/retry, email, or full producer coverage.

## Checkpoint kiểm thử không skip và an toàn môi trường (2026-10-05)

Checkpoint này có ưu tiên hơn các số liệu 1572/1578 và các trạng thái lịch sử bên dưới. Lượt chạy ban đầu có 1576 passed, 2 failed, 0 skipped; hai test upload tài nguyên và lease bài thi trả 503. Chạy riêng cho 2 passed; chạy lại toàn nhóm API trước sửa fixture cho 375 passed. Probe có restore marker trên thư mục audit riêng tái hiện đúng cả hai phản hồi MAINTENANCE_MODE_ACTIVE/503. Việc nhóm test dùng chung storage/quarantine/backups với workspace là lỗi cô lập đã được chứng minh; không quy kết chắc chắn nguyên nhân của lượt lỗi ban đầu khi chưa lưu response của lượt đó.

Fixture app nay dùng ba thư mục con riêng trong tmp_path. Regression mới thất bại với các root E:/PWD301/storage, quarantine, backups trước sửa. Sau sửa, probe vẫn giữ marker bên ngoài và 27 test upload/lease/backup/restore/maintenance đạt; không tắt maintenance hay fail-closed. Marker probe đã xóa. Test mới dùng nhầm một route không tồn tại lúc đầu; lỗi harness 404 đó đã sửa, không tính là lỗi sản phẩm.

Cô lập filesystem lộ thêm lỗi rescan: kiểm tra substring “infected” trên toàn đường dẫn nhầm thư mục cha với vùng chứa tệp nhiễm. Regression hiện hữu thất bại hai lần trước sửa; nay so sánh parent đã resolve với get_file_infected_root(), kiểm tra tệp được chuyển, key infected/hash và Student vẫn bị từ chối 403. Focused stress/file/isolation: 27 passed. Lượt split cuối sau sửa cho **1579 passed, 0 failed, 0 skipped**, khớp **1579 tests collected**: root298 + unit632 + API375 + security233 + concurrency13 + E2E12 + integration16. Frontend độc lập: **101 passed, 0 failed, 0 skipped**. Không cộng các lượt focused trùng vào tổng. Đây là kết quả các nhóm chạy đủ, không phải một aggregate verifier được tuyên bố pass; lượt aggregate lịch sử bị stall vẫn không được tính.

SQL-gated integration hiện tại: 16 passed, 0 failed, 0 skipped, gồm migration, ROWVERSION race và hai loại revision trên SQL Server thật. Hai DB migration/race tạm đã xóa, remaining=0. Browser Student4 đã đăng xuất về form login; server audit 5105 dừng; DB grading tạm cũng đã xóa, remaining=0. Không migrate/restart DB/runtime chính; fixture có thể dựng lại bằng prepare.

Audit notification vẫn PARTIAL, không phải release sign-off. Những đoạn dưới nói “chưa sửa”, “pending replay”, “1572 current” là snapshot lịch sử, không được dùng thay checkpoint mới.

## Final executed verification ledger (2026-10-05)

| Non-overlapping scope | Actual invocation | Result |
|---|---|---|
| Root-level pytest files | pytest with every tests/test_*.py file | 298 passed, exit0, 114.11s |
| Unit | pytest tests/unit -q --tb=short | 632 passed, exit0, 245.09s |
| API | pytest tests/api -q --tb=short | 375 passed, exit0, 270.51s |
| Security + concurrency + E2E | pytest tests/security tests/concurrency tests/e2e -q --tb=short | 258 passed, exit0, 149.58s; collected partitions233/13/12 |
| Integration with real SQL gates | grading-runtime-probe.py sql-gates → pytest tests/integration | 16 passed, exit0, 20.10s; both SQL URLs provisioned, no opt-in skip |
| Python total / collection | sum above; pytest --collect-only -q | 1579 passed, 0 failed, 0 skipped; 1579 collected |
| Frontend | node --test tests/frontend/*.test.js | 101 passed, 0 failed, 0 skipped, exit0 |
| Ruff check | ruff check src tests migrations | PASS |
| Ruff format | ruff format --check src tests migrations | PASS:261 files already formatted |
| Scoped typing | mypy attempt_service.py regrade_worker.py question_bank_service.py file_service.py | PASS:no issues in4 files; unused-config-section note only |
| Repository contract | python scripts/repo_check.py | PASS; Markdown fences balanced, canonical DDL73 tables |
| Working diff whitespace | git diff --check | PASS; LF/CRLF conversion warnings only |

The integration count includes SQLite/in-process cases and four actual opt-in SQL cases; it is not a claim that every backend test ran on SQL Server. The exact migration/race DBs were removed after the final rerun, each reporting remaining0. All counts above have zero skips; deselected/focused overlaps and stopped runs are not added. No commit/push or main-runtime migration was performed. Inventory ID count was checked directly:124, still not complete required-field/runtime coverage.

## Bounded Impeccable result-surface audit

Implementation-integrity verdict: FAIL for the sampled result detail. The total and freshly delivered notices match SQL, but the ESSAY card fabricates a choice-oriented unanswered/incorrect/0-point presentation (RCA-037). The signature-like value and fixed-looking duration require source/payload reconciliation; they are not cryptographic/performance evidence.

| Dimension | Scoped assessment | Evidence / limit |
|---|---|---|
| Accessibility | Partial, no full WCAG score | Named auth controls, modal Escape and logout/Back were exercised; category filters are skipped by Tab in the earlier live center check; contrast/screen-reader breadth not measured |
| Performance | Not measured | No frame, layout-thrash or bundle measurements in this continuation |
| Responsive | Not measured | Desktop Edge observation is not mobile/touch/zoom proof |
| Theming | Candidate warnings only | One detector run flagged repeated color/border choices; no verified dark-mode or contrast-ratio conclusion |
| Implementation integrity | Confirmed failure | Real stored essay answer/18 points versus unanswered/0; correct total28/30 and correct notification CTA remain positives |

No /20 score is fabricated from unmeasured dimensions. Context ran once against the existing student view with no PRODUCT/DESIGN artifacts; detector ran once and returned source heuristics, not confirmed WCAG failures. No visual redesign, UI edit or repeated polish scan was performed. Positive evidence: Vietnamese first-release/change copy, canonical related-page navigation, honest unknown rank text and settled logout. Prioritize `/impeccable harden` for type-aware result data, `/impeccable clarify` for truthful metadata/copy, then `/impeccable audit` for measured responsive/a11y coverage and `/impeccable polish` only after business truth is corrected. These are recommendations, not commands claimed executed.

## Review and diagnostic limits

Manual line-level review covered shared result notifier/worker callsites, inactive revision construction, enum migration/downgrade safety, test filesystem setup and exact infected-root comparison. Ruff, format, mypy (four affected services) and repository contract checks were executed; their current outcomes are recorded in the final verification table. Automated OCR remains unavailable because no valid LLM endpoint was configured; the earlier failed OCR command is not a review pass and no credentials were added.

The first API run's two 503 failures and the later root rescan failure are retained. One focused command named a nonexistent security-test file and ran zero tests; it is not counted. An in-flight API replay loaded source before the final rescan correction and was intentionally stopped at38%, then restarted; no partial result was counted.

## Latest post-fix SQL/Browser replay (2026-10-05)

The latest fixture at c4d5e6f7a8b0 uses course e03443e6-a528-4fb2-b8b3-1fc8e5bddee9, assessment7e84cd93-7418-475a-9f80-eb1cc8718a3a and attempt ed90cef0-4151-495d-835a-d4696c6b06ff. Manual18 and unchanged18 retry produced exactly one ASSESSMENT_GRADED row (55931f52-e1d6-4c46-bfbf-5d310fa9a301). Answer correction and job6f4db8ef-10ae-5b40-a920-769c86898895 produced RELEASED28/30, one history18→28 and one SCORE_CHANGED_AFTER_REGRADE row (95758e04-25e7-49cc-9e9c-defce9dd13d0). Duplicate regrade returned the same job and unchanged overall history; old source revision key A and presentation snapshots remained unchanged. Both notices belong to Student4, target STUDENT and the same canonical attempt CTA.

Browser Student4 rendered both exact Vietnamese notices. Opening the change notice showed18→28/30 in the detail modal; Mở Trang Liên Quan landed on the correct attempt and rendered28/30 (9.3/10). A preceding fixture already proved the first-release notice CTA at18/30. The ESSAY detail nevertheless shows0/unanswered/incorrect despite real stored answer and18/20 grade; this is a confirmed separate failure, not evidence that the notification failed to deliver.

The replay exposed and corrected CHECK drift (547), premature activation (51007), and the worker's missing dispatcher. New failing regressions were accepted only for those real causes; harness detachment, wrong field names, encoding, Flask-Migrate SystemExit and unsupported SQLAlchemy CHECK reflection were corrected and not counted as product defects.143 focused backend tests and16 integration tests passed with zero skips. SQL integration covers migration roundtrip/ROWVERSION plus real SC/SHORT_ANSWER immutable-child tests; its two disposable databases were removed (remaining0). Final split results are recorded in the executed verification ledger above.

Reproduction uses grading-runtime-probe.py actions prepare, serve, manual-probe, correct-answer, regrade-probe, status, sql-gates and cleanup. Credentials/tokens are not printed or written. Cleanup is guarded by an exact three-database allowlist; only disposable data is removed, recoverable by rerunning prepare. The main runtime5000 and database were neither migrated nor restarted.

## Fresh emitted grading-notice CTA replay (2026-10-06)

The current continuation recreated only `PWD301_AUDIT_GRADE_20261005_1B3A`, ran `prepare`, `manual-probe`, `correct-answer`, `regrade-probe` and `status`, and then used a fresh Edge tab against the disposable server on port 5105. Manual grading returned the expected boundary results (student 403, negative/above-max/NaN 400, stale rowversion 409), released 18/30 and persisted exactly one first-release notice. The correction/regrade probe then completed at 28/30, persisted one `18→28` history change and one `SCORE_CHANGED_AFTER_REGRADE` notice; the repeated regrade returned the same job and did not change history. The SQL status contained exactly the two expected Student4 rows and the canonical attempt-result action URL.

Browser Student4 login succeeded. The notification center showed both freshly emitted notices; opening `Điểm bài thi đã thay đổi: Audit thông báo chấm điểm 2026-10-05` showed the 18→28/30 body, and `Mở Trang Liên Quan` landed at `#/student/assessments/results?id=e8ba2cd1-cd9c-4f56-93e5-709b45b8326f`, where the released result rendered 28/30. Logout returned to `/auth`, the agent tab closed, the server stopped, and cleanup returned `{"database":"PWD301_AUDIT_GRADE_20261005_1B3A","audit_database_remaining":0}`. This closes the fresh emitted-event replay required by N-109/F-012; it does not close the separate ESSAY detail or broader producer/role/idempotency findings.

## Disposable SQL Server manual-grading reproduction (2026-10-05)

`grading-runtime-probe.py prepare` created only `PWD301_AUDIT_GRADE_20261005_1B3A`, migrated to repository head, seeded canonical demo data and used existing authorized services to create AUDN1005 with one SINGLE_CHOICE (10) and one ESSAY (20). No live PWD301 record or runtime setting was changed. A separate server used port 5105 and a distinct session-cookie name.

Pre-fix fixture: course `65eb8ea7-3bd1-4b71-bf6e-daf0d5930add`, assessment `e1c87636-1ff6-4600-a0e9-a70697984b19`, attempt `8d3b8004-b2f2-4597-8f5c-e52476e9e602`. Instructor2 Browser showed one CHỜ CHẤM submission; its detail modal contained the actual ESSAY answer but only a close button, with no grading/regrade control. This establishes a reachable missing-UI workflow, not merely absent demo data.

Real HTTP probes on 5105 returned Student grade 403, negative/above-max/NaN 400, stale ROWVERSION 409, and valid manual grade 200. Student result changed from PENDING_GRADING/SCORE_HIDDEN/null to GRADED/RELEASED/18 of 30. SQL Server persisted INITIAL (0) and MANUAL (18) result histories but zero linked grading notifications. Source excluded MANUAL from both dispatch branches. A focused regression then failed with `len(notifications) == 0` instead of 1; a first harness failure due detached objects was corrected before accepting that RED evidence.

The first-release/change-only correction passed the full focused grading/regrade/attempt/notification/API/IDOR command: **69 passed, 0 failed, 0 skipped**. It verifies durable first-release notification, no duplicate for an unchanged manual score, and a change notice for a revised released score. Post-fix SQL Server/Browser replay remains pending at this checkpoint; the previous 1572-item split run predates this newest backend edit and is not its full-suite proof.

## Current continuation correction — enrollment transaction and SQL gate (2026-10-05)

A new TDD regression first failed because closing the session after `enroll_student()` left the two `STUDENT_ENROLLED` events without linked `Notification` rows. The service now dispatches the owner and student notifications before its final enrollment commit. The focused enrollment scope reports **20 passed, 0 failed**, including the persistence regression. Completed split pytest verification across every collected group totals **1572 passed, 0 failed, 0 skipped**; migration and concurrency probes ran against uniquely named disposable SQL Server databases and both database pairs were removed. A later aggregate attempt stalled at 49% and is not counted as a pass.

This supersedes the earlier aggregate count and source-level uncertainty about enrollment transaction ordering. It does not erase the historical live OPS401 data gap or close the remaining upload/download, email, duplicate/idempotency, envelope and manual-grade gates.

The fresh live enrollment gate was subsequently replayed: Student4 enrolled in DSA201 through Browser, the UI showed `Đã ghi danh thành công`, Instructor2 saw the owner notification, and SQL Server correlated ACTIVE enrollment `110003` with `STUDENT_ENROLLED` events `140010/140011` and linked notifications `150083/150084`. The current replay closes the fresh correlation but not the historical OPS401 orphan-row repair.

Browser download follow-up remains negative: CDP observed `Page.downloadWillBegin`, but the transfer ended in `state: canceled` with an incomplete `.crdownload`; no completed Browser file delivery is claimed. The authenticated backend HTTP 200 PDF evidence remains valid.

## Current live approval correlation (2026-10-05)

Instructor1 submitted CS201 through the real course-management UI and saw the success toast. Admin then logged in through the standard form, saw `1 Khóa học chờ duyệt`, opened CS201 and confirmed `Duyệt Khóa Học`; the queue returned to zero and the UI showed the approval message. A subsequent Instructor1 session displayed the owner notification `Khóa học CS201 đã được phê duyệt`. Direct SQL Server evidence matched the business result: CS201 is `APPROVED` with `approved_by_user_id=1`, event `140006` is `COURSE_APPROVED`, and notification `150079` is linked to `instructor1@pwd301.local`. This is a current live approve-path pass.

## Live rejection correlation and post-fix verification (2026-10-05)

Instructor1 edited the approved CS201 lesson and submitted staged change request `#60002`. Admin opened the live review detail, entered `Vui lòng bổ sung ví dụ minh họa trước khi áp dụng.`, and completed `Từ Chối Bản Sửa`; the queue returned with no pending request. Instructor1 logged in again and saw the pre-fix title `Đợt cập nhật khóa học #70014 cần chỉnh sửa lại` with the exact reason. SQL Server confirmed `course_change_requests.id=60002` as `REJECTED`, reviewer `1`, event `140009` (`COURSE_CHANGE_REJECTED`) and linked notification `150082` to `instructor1@pwd301.local`. The follow-up `#60003` empty-reason attempt stayed in the review modal with the minimum-length warning before a valid-reason rejection completed. This closes the live request-edit/reject plus empty-reason validation gate; the identifier defect is separately fixed and verified below.

The follow-up boundary request `#60003` confirmed the same rejection flow and the empty-reason guard: Browser submission with no reason stayed on the review page and showed `Nội dung bắt buộc tối thiểu 5 ký tự.`; a valid reason then completed rejection. Its `70014` identifier leakage is retained as historical pre-fix evidence.

The post-fix live request `#60004` was resubmitted and rejected through the same real Admin review page after the producer fix. Instructor1 received `Đợt cập nhật khóa học CS201 cần chỉnh sửa lại` with the exact reason; the notification detail CTA opened `#/instructor/courses/manage?id=06a1a28d-667a-4d31-b5c9-edefc2885d91`. SQL Server confirmed `course_change_requests.id=60004` as `REJECTED`, event `140017`, notification `150090`, and the same public UUID/action URL. This closes B-049 in the current source/runtime.

## Current malformed-payload live probe (2026-10-05)

Using fresh JWTs from the live `/api/v1/auth/login` boundary, malformed notification mutations were sent without printing or persisting tokens: broadcast JSON string, mark-all JSON list and preferences JSON string. The three responses were respectively HTTP `400 VALIDATION_ERROR`, `400 VALIDATION_ERROR` and `400 VALIDATION_ERROR`; no business mutation was submitted. This is the current runtime result for B-044/B-022. The prior HTTP 500 rows remain historical pre-fix evidence, and the canonical `{success,data,error}` envelope is still not normalized across notification routes.

## Current logout/modal Browser probe (2026-10-05)

Current replay: Instructor1 logged in through the standard form, opened the live CS201 `Cài đặt & Học vụ` modal, closed it using Escape and logged out through the account menu. Logout displayed the login form and success toast. Browser Back then settled at `#/auth`; actual page-runtime CDP inspection confirmed `window.app` exists, `currentUser=null`, `_isRouting=false`, login visible, and course/topbar/modal not visible. This is a scoped logout/Back and modal-Escape PASS. The earlier account-menu click while a modal was visible may have closed the backdrop before logout; it is not independent evidence of teardown while an overlay remains mounted. Exhaustive overlay-at-logout coverage remains open.

The earlier BFCache conclusion is withdrawn. `playwright.evaluate()` runs in a read-only DOM scope and could not establish absence of page globals; actual CDP `Runtime.evaluate` showed the router existed. Real auth-route behavior was reproduced by three failing regressions: unauthenticated `#/auth`, `#/login` and expired-session navigation entered `dispatchRoute()`'s role-home fallback. The new unauthenticated guard renders auth and returns before dispatch. Focused tests changed from 7 pass/3 fail to 10 pass/0 fail, both with 0 skips; the full frontend suite is 101 pass/0 fail/0 skipped. The speculative bootstrap change and two mock-only bootstrap tests were removed, restoring `frontend/index.html` without reverting unrelated user changes.

## Post-fix retest of the current dirty worktree (2026-10-05)

The current worktree contains earlier user remediation plus the scoped audit-continuation fixes listed in the fix plan; none of the changes have been committed.

| Check | Current result | Scope limit |
|---|---|---|
| Notification unit/API/IDOR | **28 passed, 0 failed** | Focused contract/security scope only |
| Seed/auth/notification regression | **53 passed, 0 failed** | Focused integration/API scope only |
| Live HTTP login matrix | **7/7 demo accounts returned HTTP 200** | Local runtime only; no external identity provider |
| Browser role login | **3/3 representative roles passed** | Student → `#/student/dashboard`; Instructor → `#/instructor/dashboard`; Admin → `#/admin/governance` with `ADMIN CHÍNH` |
| Admin authorization recheck | **PASS for current runtime boundary** | `/auth/login` reported `is_primary_admin=true`; `/admin/users` and `/admin/courses/pending` returned HTTP 200 |
| Quick-demo shortcut post-fix | **PASS for three current role paths** | After the auth-route correction, clean sessions used the visible Instructor1, Student1 and Admin demo selectors and reached the matching instructor dashboard, student dashboard and admin governance with correct role labels. Prior stalled/ambiguous observations remain historical |
| Split pytest verification after remediation | **PASS: 1572 passed, 0 failed, 0 skipped** | Root-level 297, unit 629, API 375, security 233, concurrency 13, E2E 12 and integration 13; the two SQL Server gates executed in the integration group and disposable databases were removed |
| Explicit disposable SQL Server rerun | **PASS: migration 1 passed; ROWVERSION race 1 passed** | Both opt-in SQL tests used correctly formed disposable MSSQL URLs; each disposable database was removed after completion |

The earlier dismiss failures and live Admin-primary metadata blocker are retained below as historical baseline findings. The current evidence does not establish that duplicate broadcast persistence, enrollment notices, canonical notification envelopes, upload/download, email delivery or every Browser mutation flow is fixed.

## Regression scope

The historical scope paragraph below predates the current continuation. The current worktree includes the scoped notification and route fixes listed above; the latest split verification and Browser network-failure regression are the authoritative current evidence. Remaining gaps are explicitly retained rather than treated as release acceptance.

Không có remediation code được áp dụng trong lượt này. Báo cáo này ghi nhận regression baseline của worktree hiện tại và các gate đã chạy; không gọi các kết quả này là kết quả sau sửa.

## Executed results

| Check | Command / scope | Result |
|---|---|---|
| repository contract | `scripts/verify.ps1` contract step | PASS |
| Python compile | verify script | PASS |
| Ruff | verify script | PASS |
| Ruff format | verify script | PASS: 270 files already formatted |
| mypy | verify script | PASS: 88 source files, no issues |
| frontend Node tests | `node --test tests/frontend/*.test.js` | PASS: 101 passed, 0 failed, 0 skipped; includes auth/login and expired-session route regressions; speculative BFCache tests removed |
| targeted notification tests | unit/API/IDOR command | Historical baseline: 26 passed, 2 failed in 16.54s; current post-fix: **28 passed, 0 failed in 15.94s** |
| full pytest baseline | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\verify.ps1`, fresh 2026-10-04 run | FAIL: 1546 passed, 17 failed, 2 skipped in 811.82s; direct invocation was blocked by the local unsigned-script execution policy, so the same script was run with process-scoped bypass |
| split pytest with disposable SQL gates | Separate root/unit/API/security/concurrency/E2E/integration runs, fresh 2026-10-05 | PASS: **1572 passed, 0 failed, 0 skipped**; both SQL Server integration tests executed and passed against disposable databases, and those databases were cleaned up |
| SQL Server migration/concurrency | fresh disposable SQL Server database `PWD301_AUDIT_0A2087F3F619` | PASS: migration round-trip 1 passed in 4.40s; row-version concurrency 1 passed in 1.11s; database was removed after the run |
| SQL Server read-only notification correlation | `create_app('development')` + direct SELECTs against `PWD301` | PASS for DB evidence: MSSQL dialect; 30 notification rows, 31 event rows; double-click title has 2 notification rows and 2 event IDs |

## Browser regression evidence

| Flow | Result | Evidence |
|---|---|---|
| Student demo login | PARTIAL PASS | login succeeded but defaulted to Instructor view despite Student label; explicit role switch worked |
| Instructor demo login | PASS | `#/instructor/dashboard`, correct name/role and notification center |
| Admin demo login | PASS | `#/admin/governance`, correct admin role and notification center |
| mark-all | PASS | badge changed from 5 to 0 and success toast appeared |
| mark-one read | PARTIAL PASS | Student clicked the unread assessment result; the badge disappeared, the item changed to `Đã đọc`, and the dashboard route remained stable. Read-only SQL Server correlation found notification `id=27` with `read_at=2026-10-04T11:43:08.566000`; rapid repeated click was not run |
| notification center Esc + keyboard | PARTIAL/FAIL ACCESSIBILITY | Fresh Student DSA201 center exposed `Tất cả`, `Chưa đọc`, `Khảo thí`, `Khóa học`, `Hệ thống`; `Tab` cycled `Tất cả` -> `Chưa đọc` -> `Tất cả`, skipping the three category filters. `Escape` closed the center; full screen-reader coverage remains open |
| category filtering | PASS | `Khảo thí`, `Hệ thống`, `Tất cả` changed visible items |
| delete + refresh | PARTIAL PASS | item disappeared, success toast, manual refresh did not restore it; API contract tests still fail |
| rapid notification refresh | PARTIAL/FAIL BOUNDARY | two consecutive Browser `Làm mới` clicks repopulated the same six visible items without a visible duplicate; API page 1/page 2 had zero ID overlap. Three-role Browser outage/retry recovery now passes; duplicate action, timeout/retry and broader idempotency behavior remain unverified |
| assessment grading/regrade | PARTIAL | Instructor2 opened DSA201 gradebook from course-management and saw 1 submission at `100 / 100`; the detail modal exposed only 2 `SINGLE_CHOICE` questions and no manual-grade/regrade control. Fresh host DB showed 2 `GRADED` auto-graded attempts, 0 pending grade rows and empty `question_corrections`; `tests/api/test_regrade_api.py -q` returned 4 passed. No live manual-grade/regrade notification was produced; the earlier pending-ESSAY snapshot is not reproducible |
| prerequisite request/review | PARTIAL | At the initial snapshot, Instructor2 Browser showed the exact unread request and the incoming `Phê duyệt`/`Từ chối` actions; that snapshot row is superseded by the continuation correction below. The continuation confirmed approval in Browser plus API/DB correlation, and rejection through a renewed CSRF-authenticated HTTP session with the Browser prompt completion remaining partial. |
| file rejection / fail-closed | PARTIAL BACKEND ONLY | Student multipart submission with `invalid.exe` returned HTTP 400 `INVALID_FILE_TYPE` and a PDF-only message; focused fail-closed file tests returned `20 passed, 16 deselected`; host DB had no non-clean file assets. Browser file selection is still blocked by Edge and no pending/quarantine download path was present |
| content/media validation | PARTIAL BACKEND ONLY | Instructor course-image upload with invalid PNG bytes returned HTTP 400 `VALIDATION_ERROR` and a safe supported-image message; `tests/test_m4_challenger_media_limits.py -q` returned `77 passed`. Browser file selection remains unverified |
| student enrollment notice | FAIL CONFIRMED | Browser Instructor1 showed OPS401 with 2 students and no `Học viên mới` notification. Host DB showed active OPS401 enrollments and four `STUDENT_ENROLLED` events targeted at course owners, but zero linked `Notification` rows for every event |
| enrollment capacity boundary | FAIL CONFIRMED | `tests/unit/test_enrollment_service.py -q` returned `16 passed, 1 failed`; the capacity-1 second enrollment did not raise `EnrollmentCapacityExceededError`. Source inspection confirms the current service explicitly follows an unlimited-capacity policy and contains no `locked_course.capacity` guard, conflicting with the test/business contract |
| content flag authorization boundary | PARTIAL BACKEND ONLY | Authenticated Student POST to the live Admin lesson-flag route returned HTTP 403 `FORBIDDEN`; valid Admin flag and owner notification remain unverified |
| role assignment/suspension authorization boundary | PARTIAL BACKEND ONLY | Authenticated Student POSTs to live Admin suspend and role-assignment routes both returned HTTP 403 `FORBIDDEN`; valid Admin mutation and session revocation remain unverified |
| role switch | PASS | Instructor → Student route, label and dashboard changed |
| invalid broadcast | PASS | empty title blocked with Vietnamese warning; no broadcast submitted |
| valid Admin-only broadcast | PASS for one path | title/body submitted to `Chỉ Quản trị viên (ADMIN)`; toast reported delivery to 1 user, badge changed 2 -> 3, dropdown showed the exact item; authenticated API returned `SYSTEM_BROADCAST`, `SYSTEM`, matching body and `is_read=false` |
| Admin-only broadcast double-click | FAIL CONFIRMED | one UI double-click produced two identical success toasts; API exposed one matching item (`total=7`, `unread_count=4`), but direct SQL Server showed 2 notification rows and 2 distinct event IDs for the same title |
| Admin failed-email retry | PASS for authorization/empty queue | authenticated Admin POST `/admin/emails/retry-failed` with `max_emails=50` returned HTTP 200 and `retried_count=0`; no failed-email delivery was available to verify |
| invalid create-course form | PASS | empty title/code blocked with Vietnamese warning; cancel closed modal without write |
| logout + revisit | PARTIAL PASS | fresh Browser login as `student1@pwd301.local` opened the Instructor dashboard; logout showed `Đã đăng xuất tài khoản an toàn`; Back returned to stale `#/instructor/dashboard` but rendered only the login screen with no protected content; stale hash cleanup remains open |
| duplicate/error hygiene | FAIL OBSERVED | near-duplicate notifications, English RBAC error and repeated background warnings; source tracing ties the RBAC copy to `src/pwd301/blueprints/admin/routes.py:230-236` and `:288-294`, then to direct frontend propagation in `frontend/assets/js/api.js:98-108` |

| Flow | Result | Evidence |
|---|---|---|
| valid course/unit/lesson authoring | PASS/PARTIAL | `AUDIT1004` created; blank unit rejected; valid unit and lesson draft saved |
| course review submission | PASS for current live approve/reject branches; no-reason validation open | Current live Instructor1 submitted CS201, Admin queue showed 1, approval reached `APPROVED`, owner received `COURSE_APPROVED`, and SQL Server matched the course/event/notification. A second live staged update `#60002` was rejected through the real review page; owner received the exact reason and SQL Server matched `REJECTED`, event `140009` and notification `150082` |
| exam sample load and publish | PASS | 4-question sample loaded; confirmation and success toast reported publication |
| student waiting room/start | PARTIAL | pledge/start worked; fullscreen lockdown recorded 1 violation immediately |
| student autosave and submit | PASS | two answers autosaved; confirmation; result page showed 100/100 and 2/2 correct |
| result PDF export | NOT VERIFIED | result page showed 100/100 and the PDF button; a fresh Browser click timed out during input dispatch and showed no visible toast or download confirmation, so no verifiable download event/file |
| student enrollment | PASS for fresh current replay and both notification CTAs; historical repair open | Student4 → DSA201 confirmation changed the catalog card to `Đã ghi danh`; Student4 notification CTA opened the DSA201 Student course detail; Instructor2 saw the owner notice and its CTA opened the DSA201 Instructor management page; SQL Server matched ACTIVE enrollment `110003`, events `140010/140011` and notifications `150083/150084`. Duplicate/capacity path and historical OPS401 orphan repair remain open |
| course resource download | PARTIAL | authenticated HTTP backend returned 200/application-pdf/1,213 bytes; a fresh Browser click on the visible DSA201 `Tải về` link left the lesson page in place and produced no recent file in the local Downloads folder; Browser delivery remains blocked/unverified |
| historical pre-fix Admin queue repeat | BASELINE FAIL | second fresh Admin login showed 0 pending courses and primary-admin-only matrix error; `/auth/login` reported `is_primary_admin:false` and `/admin/courses/pending` returned 403. Current post-fix evidence is recorded at the top of this report |
| corrected disposable Admin queue and decision paths | PASS for disposable retest | `PWD301_AUDIT_ADMIN_20261004` seeded the expected `ADMIN_PRIMARY` metadata; Browser showed 1 pending course, approve produced the success toast and DB `APPROVED`, then request-edit/reject produced the expected feedback and DB `DRAFT` |

Authenticated browser network capture verified `/auth/notifications?role=STUDENT|INSTRUCTOR|ADMIN` at HTTP 200. All captured bodies had `success:true` but no `data`, mixed `preferences` into the list payload, emitted `deleted_at:null`, and showed role-specific duplicate event identities; this is an API/business-contract regression independent of the UI rendering result. Source tracing also found the REST route uses a different list/preferences/read/dismiss serialization. The frontend total-failure fallback was corrected in this continuation to raise `NOTIFICATIONS_UNAVAILABLE` and render a degraded/retry state.

The fresh Admin broadcast probe also correlated the visible UI item with the authenticated API: `total=6`, `unread_count=3`, `event_type=SYSTEM_BROADCAST`, `category=SYSTEM`, matching body, and `is_read=false`. This proves one authorized audience path only; retry/idempotency, non-Admin audiences and a direct DB row were not checked.

The security-copy and RBAC findings are source-traced but not product fixes: `src/pwd301/seeds/demo.py:1224-1240` hard-codes the IP-like value in the seeded `SYSTEM_SECURITY_ALERT` body, so the runtime UI evidence confirms seed-data exposure rather than a newly generated request-IP producer. The primary-admin English denial is constructed in `src/pwd301/blueprints/admin/routes.py:230-236` and `:288-294`; `frontend/assets/js/api.js:98-108` forwards the response message as the user-facing error and logs the failed request, while background loaders repeat forbidden calls.

The subsequent Admin-only double-click probe produced two success toasts. The API list exposed one matching item (`total=7`, `unread_count=4`), but a direct read-only SQL Server query found two notification rows and two distinct event IDs for the same title. Source tracing now explains the mechanism: the Admin route accepts no idempotency key; each service call emits a new random event; the only database uniqueness is `(notification_event_id, recipient_user_id)`; and the list query hides newer same-title/body rows. The API/UI dedupe therefore masked a persisted duplicate rather than proving backend idempotency.

Historical B-009 evidence retained from the earlier partial row: an Instructor2 logout with the DSA201 settings modal open left protected modal content over the login form until manual close. The current source contains overlay teardown, and the auth-route correction plus current logout/Back replay is described above. Full overlay-at-logout replay remains a distinct acceptance gate.

An authenticated Student API probe returned page 1 and page 2 with `per_page=2`, two items per page and zero ID overlap. The same Student session requesting `role=ADMIN` still received the Student's own five-item set and did not receive either Admin audit broadcast; this is a no-leak observation, but the role query parameter appears to be ignored rather than enforcing a role view.

A fresh unauthenticated probe returned HTTP 200 for `/health`, HTTP 401 for `/api/notifications`, `/api/notifications/unread-count` and `/auth/notifications?role=STUDENT`; a Student session requesting `/admin/courses/pending` returned HTTP 403. The 401/403 bodies still use an `error` object without the required `success:false,data:null` envelope.

The Admin retry probe required a fresh CSRF token after login and then returned HTTP 200 with `retried_count=0`; this confirms the session authorization path only, not external email delivery.

An authenticated Admin server-validation probe posted a broadcast body without a title and received HTTP 400 with `VALIDATION_ERROR` / `Field 'title' is required.`; no broadcast was created. The status/message semantics are useful, but the response still lacks the required `success:false,data:null` envelope.

The upload probe reached an enabled course-cover file input with `accept=image/png,image/jpeg,image/webp`. Edge then rejected the browser automation file selection with `Not allowed`; the documented remedy is enabling the ChatGPT extension's “Allow access to file URLs”, which was intentionally not changed. Therefore upload remains an environment-blocked gate, not a product pass or fail.

The direct SQL Server role-link query is historical pre-fix evidence: `admin@pwd301.local` had an `ADMIN` link with assignment reason `Baseline root administrator initialization`, not the `SUB_ROLE:ADMIN_PRIMARY` token required by the then-running source. This explained the observed `is_primary_admin:false` and HTTP 403. The current runtime was later rechecked and now reports `is_primary_admin:true` with HTTP 200 Admin endpoints; a separate disposable runtime was also migrated and seeded from current source and browser-tested through both decision branches.

The targeted notification result above preserves the historical baseline. The post-fix rerun returned **28 passed, 0 failed in 15.94s**, including the two former dismiss assertions. The latest frontend `node --test tests/frontend/*.test.js` run returned **101 passed, 0 failed, 0 skipped**; dedicated tests cover degraded transport, pending revalidation and stable unauthenticated auth navigation. The BFCache claim and speculative bootstrap test are withdrawn.

- Fresh 2026-10-04 JWT boundary probe: unauthenticated list/count/preferences/mark-all returned structured 401 `UNAUTHORIZED`; authenticated list returned 200 with `success`, `items`, counts and pagination but no `data`; preferences returned only `preferences`; invalid read/dismiss/delete returned 404, wrong-method GET returned 405, empty preference update returned 400, and Student Admin-only broadcast/email-retry calls returned 403 without mutation. Network-failure/degraded retry simulation was not available in this pass.
- Unauthenticated web-session probes also diverged: `/auth/notifications` returned 401, `/auth/notifications/unread-count` returned 200 with zero, and `/auth/notifications/preferences` returned 405 because it is not exposed.
- Cross-role JWT read-only probe succeeded for Student, Instructor and Admin. `/api/v1/auth/me` reported role sets `STUDENT,INSTRUCTOR` for the first two demo accounts and `STUDENT,INSTRUCTOR,ADMIN` for Admin; notification totals were 6, 5 and 7 respectively (unread 0, 3 and 4). This confirms current role-specific read surfaces but not full recipient correctness.
- Fresh read-only SQL Server recheck reproduced the two central business findings: 2 ACTIVE OPS401 enrollments were backed by 4 `STUDENT_ENROLLED` events with zero linked notifications, and the double-click broadcast title still had 2 notification rows with 2 distinct event IDs for one recipient.
- A rollback-only SQL Server reproduction of the real enrollment service with commit-simulation (`flush()` + `expire_all()`) for PY301/student3 returned `ACTIVE`, created 2 events and 2 linked notifications in-transaction, emitted no dispatch warning, and rolled back; a follow-up query remained at 4 persisted `STUDENT_ENROLLED` events with 0 linked notifications. Therefore B-013 remains a confirmed persisted live-data defect, but its current triggering exception remains unverified/non-reproducible.

## Current continuation correction — prerequisite approve/reject

The earlier prerequisite row is superseded for current state. Instructor2 Browser approved request id `1`; the UI showed the success toast, and authenticated follow-up confirmed `APPROVED`, the `OPS401 -> DSA201` link, and the Instructor1 `COURSE_PREREQUISITE_APPROVED` notification. Instructor1 then created request id `2` in Browser; Instructor2 Browser displayed the request and opened the native reject prompt. Because the prompt could not be completed reliably in the Browser automation session, the final reject was performed via a fresh authenticated CSRF session and verified as `REJECTED` with reason plus `COURSE_PREREQUISITE_REJECTED` notification. API/DB outcome passes; Browser reject submission remains partial.

## Current continuation correction — Student-view mark-all

Fresh Browser Student-view evidence: Notification Center showed 4 unread items, one `Đã đọc tất cả` click changed the badge to 0 and displayed the success toast. The attempted UI double-click encountered a detached DOM node before a second dispatch could be proven. Two immediate JWT mark-all POSTs both returned `success=true, marked_count=0`; this is a scoped stable no-op, not a Browser rapid-click pass.

## Fresh Admin Browser retest (2026-10-04)

The newly created Edge audit tab inherited the prior session, so it was explicitly logged out and then logged in as `admin@pwd301.local` with the demo password. The Admin route rendered successfully at `#/admin/governance`, the notification center showed 7 items and 4 unread, and the accessibility tree exposed named `Khảo thí`, `Khóa học` and `Hệ thống` filters. `Khảo thí` rendered one item; `Khóa học` rendered two CS301 approval items with different titles; `Hệ thống` rendered four items, including both audit broadcasts and the security message containing `192.168.1.105`. No notification mutation was submitted. The same governance page still rendered `Only the primary administrator can access the user and role matrix.`, so Admin login success does not prove primary-admin authorization.

### Fresh three-account login retest

In a new Edge audit session, the Student quick-login button filled `student1@pwd301.local`; submitting it showed `Đăng nhập thành công! Đang chuyển hướng...` and landed at `#/instructor/dashboard` with `GIẢNG VIÊN`, confirming login success plus the existing dual-role default ambiguity. After logout, the Instructor quick-login button filled `instructor1@pwd301.local`; submitting it showed the success toast and landed at `#/instructor/dashboard` as `TS. Nguyễn Văn A`, with the existing prerequisite-rejection notification also visible. After a second logout, the Admin quick-login button filled `admin@pwd301.local`; submitting it showed the success toast and landed at `#/admin/governance`, where the primary-administrator authorization error remained visible. The audit session was then logged out cleanly. No business mutation was submitted in this retest.

## Notification-specific regressions

Fresh direct Admin JWT list/filter boundary: unfiltered `GET /api/notifications` returned `total=7`, `unread_count=4`; category filters returned `SYSTEM=3`, `COURSE=2`, `ASSESSMENT=1`; both `unread_only=true` and `status=UNREAD` returned 4; `per_page=0` was normalized to 1, `per_page=1000` to 100, and `page=999` returned HTTP 200 with zero items. The global unread badge count is not category-scoped by design/current implementation; the out-of-range-page and clamping behavior remain contract decisions to document.
The same Admin JWT returned the identical 7-item set for `role=STUDENT`, `role=INSTRUCTOR` and `role=ADMIN`; `status=BOGUS` and `unread_only=maybe` were silently ignored, while `category=BOGUS` returned zero. Source tracing confirms the actor ID boundary remains, but role/status validation and global-versus-role-scoped semantics are not explicit.
Auth rate-limit boundary was also executed with one unique synthetic email and an incorrect password: six direct `/api/v1/auth/login` requests returned `401` for attempts 1-5 and `429` with `Retry-After: 60` on attempt 6. A subsequent valid Student1 login returned a token successfully, proving no shared loopback/demo-account lockout. No demo account or business record was targeted by the failed attempts; the temporary synthetic-email limiter state is outside notification persistence.
Rapid mark-one-read was then exercised against an already-read Admin notification. Two consecutive PATCH requests both returned `is_read=true` and the same `read_at`; unread count stayed at 2 before and after. This proves convergence for the read transition only; dismiss, broadcast and timeout-retry idempotency remain separate gates.

Audit-side state disclosure: the preceding mark-one probes changed two seeded Admin notification rows to the read state. This continuation also intentionally changed live audit fixtures: request id `1` was approved, creating the `OPS401 -> DSA201` prerequisite link and an approval notification; request id `2` was created and rejected, creating a rejection notification. No schema was changed by these fixture probes; the scoped instructor staged-lesson upload source fix is documented separately in the current retest. These live business-fixture mutations are retained explicitly and must not be mistaken for a clean production baseline.

The Student-view mark-all probe additionally changed four Instructor2 notification rows to read. The attempted second UI dispatch detached before it could be proven; the two subsequent JWT calls were no-ops with `marked_count=0`.

Fresh validation-boundary probe: authenticated Admin preference opt-out for `SECURITY` returned HTTP 400 `VALIDATION_ERROR` with the mandatory-security explanation; before/after preference reads remained `email_enabled=true,is_mandatory=true`, and unread count remained 2. An unknown preference category and empty preference payload also returned HTTP 400. Admin broadcast requests missing title or body returned HTTP 400 with field-specific messages, while `mark-all-read` with an unknown category returned HTTP 200 and `marked_count=0` without changing the valid notification set. These are validation/no-op checks, not delivery proofs.

Fresh keyboard retest: on the Student DSA201 lesson page, the open notification center exposed all five named filters in the accessibility tree, but keyboard focus moved `Tất cả` -> `Chưa đọc` -> `Tất cả`, skipping `Khảo thí`, `Khóa học` and `Hệ thống`; `Escape` closed the center. This confirms a P2 keyboard-focus finding rather than a general center-open failure.

Fresh malformed-payload boundary: authenticated Admin broadcast with JSON string `"oops"` and mark-all with JSON list `["bogus"]` both returned HTTP 500 `INTERNAL_ERROR` with correlation IDs. A before/after list comparison stayed at total 7/unread 2 with identical item IDs, so no valid notification/read mutation occurred. Preferences JSON string returned HTTP 400 `VALIDATION_ERROR`. This is a confirmed API validation/500 defect, not a delivery failure.

Historical read-only frontend failure probe: a Node VM loaded the pre-fix `frontend/assets/js/api.js`, replaced the request primitive with a deterministic rejection, and observed the three fallback calls before the client returned `{items:[],total:0,unread_count:0}`. The continuation fix now raises `NOTIFICATIONS_UNAVAILABLE`; the new API and router regression tests pass and no Browser/API/DB state was mutated.
The earlier filter probe recorded unread count 4 before these two audit read transitions; the later current snapshot is therefore 2 and is time-scoped evidence, not a contradiction.

1. `test_dismiss_notification` fails because service returns `deleted` instead of `dismissed`.
2. `test_dismiss_notification_api` fails for the same public contract mismatch.
3. The previous frontend test output contained a background `ApiClient.getNotifications is not a function` caused by an incomplete router test mock; the continuation now guards that contract and renders an explicit degraded state. The prior fabricated-empty product path is covered as a fixed regression, while API envelope drift and other notification findings remain open.
4. Notification API route shapes remain inconsistent in source; authenticated browser/API captures now confirm the web payload drift, but compatibility is still not proven.
5. Static source review plus a read-only Node VM load found `student.js:5722,5830` calling `UI.alert(...)` while `ui.js` reports `UI.alert=undefined`, `UI.openModal=function` and `UI.confirm=function`; a fresh result Browser page did not expose the scale/pending-appeal trigger, so this remains an unverified user-facing runtime gap. Native `window.alert(...)` fallbacks remain in `controllers.js:30,184`.

## Additional end-to-end browser evidence

## Current Browser network-failure regression (2026-10-05)

On `http://localhost:5000`, clean logout/login sessions for Admin, Instructor and Student were each followed by temporary CDP blocking of all notification endpoints. In each role, opening the center showed `Không thể tải thông báo`, the explanatory status and `Thử lại`, and did not show `Không có thông báo nào`. After removing the block and using retry, reopening the center rendered the real notification list. No business mutation was submitted; the temporary block was removed. This is a three-role Browser PASS for degraded-state and retry recovery; rapid retry/idempotency breadth remains unverified.

## Current continuation - login and notification CTA route regressions (2026-10-05)

Fresh Edge role-session evidence was rerun against the local runtime. Student, Instructor and Admin standard login flows each showed the success toast and reached their role route; the sessions were logged out afterward. This confirms authentication/session reachability for the three representative roles only and does not erase the known dual-role default-route ambiguity.

The Student notification detail CTA reproduced a concrete route defect: the seeded graded-result notification opened `#/student/assessments/2c435c31-13c0-4892-92e8-0e48ba6474b9/results` and the page reported that the result could not be loaded because the request was a 404. The canonical attempt route `#/student/assessments/results?id=db76cdce-bef6-470d-be11-7d35cc9ab96b` then rendered the scored result page. A failing unit regression first reproduced the producer URL; after the source fix, `tests/unit/test_attempt_service.py` passed **14 passed, 0 failed** in the focused scope. A newly emitted notification replay remains open.

The source audit also found enrollment notifications emitted server paths without the SPA hash. A failing regression first captured both malformed Instructor and Student URLs; after the source and transaction-order fixes, `tests/unit/test_enrollment_service.py` passed **20 passed, 0 failed** in the focused scope. The fresh live replay then opened the Student4 notification CTA to the DSA201 Student course detail and the Instructor2 CTA to the DSA201 Instructor management page; SQL Server action URLs matched both Browser destinations. The enrollment recipient + CTA gate is now closed, while historical OPS401 orphan rows remain a separate repair gap.

The Instructor notification center showed an asynchronous UX risk: immediately after login the badge reported 14 while the center briefly rendered the empty state; after revalidation and filter interaction the same center rendered all 14 items, including the unread view. No persisted deletion was inferred. The historical Browser observation is retained; the deterministic delayed-fetch regression and source fix are recorded in the current continuation below.

The continuation added loading-state, payload-validation and auth-route fixes. A Node test first failed because a cached empty list rendered during a pending fetch; the loading/skeleton fix passes. An API test first failed because a JSON string/list produced HTTP 500; type guards now return HTTP 400. Three actual-router regressions reproduced unauthenticated auth-route fallback and passed after the guard correction. The latest frontend suite reports **101 passed, 0 failed, 0 skipped**. The completed split pytest verification includes the backend/API fixes and reports **1572 passed, 0 failed, 0 skipped**; the final frontend-only correction does not change backend code.

The continuation run exercised real role sessions and business state transitions. It is evidence of observed behavior, not a product fix. It also created local audit data (`AUDIT1004`, one unit/lesson, one published sample assessment, and one Admin-only audit broadcast). The live Admin queue mismatch and the unverified PDF download are retained as failures/gaps; the corrected disposable Admin queue/decision retest is recorded as a scoped pass only.

## Non-notification failures observed in aggregate

An earlier aggregate run also failed in course changeset, enrollment capacity/concurrency, lesson media resources, and lesson position shifting. Those historical failures are preserved as evidence but are not attributed to the notification audit without a separate root-cause investigation; the current split verification completed with zero failures and zero skips, while a later aggregate attempt stalled at 49% and is not counted as a pass.

## Worktree integrity

The worktree was already dirty at the start. Unrelated user changes remain preserved. Scoped product/test edits and the eight audit documents are explicitly recorded in the fix plan; no files were staged or committed. Only the agent-owned speculative bootstrap diff and its mock-only test were removed during the evidence correction.

Fresh integrity retest after the continuation evidence: `git diff --check` returned zero diagnostic lines and `git diff --cached --name-only` returned zero staged paths. The existing modified/deleted product and test paths remain preserved and are not attributed to this audit.

## Current broadcast idempotency regression (2026-10-05)

Before the fix, the new API regression failed because two requests with the same retry key had no replay outcome and the service created a fresh event. The implementation now persists a UUID `X-Idempotency-Key`, returns the original fan-out count with `idempotent_replay=true`, and returns HTTP 409 when the same key carries different business data. The focused API/service scopes passed (**11 API tests**, **12 service tests**, zero failures/skips) and the frontend suite remained **101 pass, 0 fail, 0 skipped**.

A fresh disposable SQL Server Browser replay logged in through the visible Admin form, double-clicked the real broadcast action, showed one success toast, and recorded one POST in the server log. SQL Server found **1** matching `SYSTEM_BROADCAST` event and **7** linked recipient notifications. A separate two-client concurrent HTTP replay with the same key returned `200/200` with `idempotent_replay=false/true`; SQL again found **1** event and **7** recipients. The disposable database was removed afterward (`audit_database_remaining=0`) and port 5105 had zero listeners. This closes B-021/RCA-032 for the scoped Admin broadcast path; other retryable producers still require their own keys and evidence.

## Current split verification after lesson-flag remediation (2026-10-05)

The current worktree was reverified with non-overlapping pytest partitions and the frontend suite. The result is **1585 passed, 0 failed, 0 skipped**: repository-root tests **298**, unit tests **632**, API tests **381**, security/concurrency/e2e tests **258** (233 + 13 + 12), and real SQL Server integration gates **16**. `pytest --collect-only -q` also reported **1585 tests collected**. The frontend Node suite reported **101 pass, 0 fail, 0 skipped, todo 0**.

The lesson-flag path additionally passed the focused TDD regression (**6 passed, 0 failed, 0 skipped**), fresh disposable SQL Server flag replay (**10 cases, 0 failed expectations, 0 skipped**) and sub-admin role/scope replay (**8 cases, 0 failed expectations, 0 skipped**). Both disposable SQL Server databases were cleaned with zero remaining audit databases; the dedicated Browser evidence was also captured and its disposable database was cleaned. This is a split verification result, not a claim that the historical aggregate verifier is healthy; the aggregate run that stalled remains excluded.

## Latest full verification after broadcast idempotency (2026-10-05)

After the broadcast idempotency change and the testing-only FILE_SCAN worker isolation guard, the non-overlapping split was rerun: root **298**, unit **632**, API **382**, security/concurrency/e2e **258**, and SQL Server integration **16**. Total: **1586 passed, 0 failed, 0 skipped**; collection reported **1586 tests**. Frontend remained **101 pass, 0 fail, 0 skipped, todo 0**. Ruff check/format, repository contract checks, `git diff --check`, and port 5105 cleanup all passed.

## Current shared REST validation regression (2026-10-05)

The RED test reproduced `500 AttributeError` for list payloads on the shared notification broadcast and email-retry routes. The routes now reject non-object payloads before field access. Focused notification API tests reported **11 passed, 0 failed, 0 skipped**. A disposable live JWT replay returned `400 VALIDATION_ERROR` for both malformed routes; two valid same-key broadcasts returned `200` with first-send/replay markers and SQL Server showed one event plus seven recipient rows. The historical malformed-payload rows remain labeled as pre-fix evidence.

## Latest canonical envelope checkpoint (2026-10-05)

The notification response contract was tested RED before the change: scoped success responses lacked the required `success/data` members and notification errors lacked the canonical outer envelope. GREEN verification passed notification API **12**, Admin broadcast **1**, notification IDOR **7**, and the full API partition **383**. The current split is **1587 passed, 0 failed, 0 skipped** (root **298**, unit **632**, API **383**, security/concurrency/e2e **258**, SQL Server integration **16**); `pytest --collect-only -q` reported **1587 tests collected**. Frontend remains **101 pass, 0 fail, 0 skipped, todo 0**. Legacy top-level response fields remain intentionally for compatibility; remaining non-notification envelope drift is not claimed fixed.

## Latest email outbox checkpoint (2026-10-05)

The fresh disposable SQL Server email probe seeded one controlled delivery, forced a real queue failure to `FAILED`, called the Admin retry endpoint, and then processed the retried row through real `smtplib` wire transport to an ephemeral loopback SMTP sink. Results: login `200`; retry `200` with `success=true,data.retried_count=1`; final delivery `SENT`; the sink captured recipient exactly `student4@pwd301.local` and subject `PWD301 audit email`; audit database cleanup `0`. This is a PASS for application outbox/retry/recipient behavior plus the local SMTP protocol boundary. Approved external SMTP/provider delivery and inbox receipt remain explicitly unverified.

## Latest Browser file I/O checkpoint (2026-10-05)

Instructor1 reached the live CS201 course-management page and the cover input was confirmed visible with `accept=image/png,image/jpeg,image/webp`. Browser file assignment was rejected as `Not allowed`, and the direct visible click did not open a native chooser; no upload API or success notification occurred. Student4 then reached enrolled DSA201, clicked the visible PDF resource link, and the local Downloads folder contained only a 1169-byte `.crdownload` after five seconds. The bytes begin with `%PDF-1.4` and contain `%%EOF`, but the Browser did not finalize the download. These are honest blocked/partial results, not upload/download passes.

## Latest Student result alert correction (2026-10-05)

The RED frontend regression showed `UI.alert('Tiêu đề', 'Nội dung')` captured the body as the modal title. The shared helper now follows the title-first contract used by both current Student result callers, escapes body text and preserves newlines. Focused GREEN passed and the full Node frontend suite is **102 passed, 0 failed, 0 skipped**. The pending-appeal and score-scale Browser triggers remain unverified because they were not exposed in the seeded result replay.

## Latest security-notification telemetry correction (2026-10-05)

The Admin Browser replay first failed the security-copy boundary because the seeded alert exposed `192.168.1.105`. A TDD regression failed before the change; the demo seed now uses an anomalous-login message without raw telemetry. The one matching live SQL Server row was repaired transactionally, the follow-up query returned zero raw-IP matches, and Browser reload showed the safe Vietnamese copy. This closes the seeded-data disclosure case; dynamic security-alert producers remain a separate open scope.

## Latest complete no-skip verification after security-copy correction (2026-10-05)

The current non-overlapping split reports **1,588 passed, 0 failed, 0 skipped**: top-level **298**, unit **632**, API **383**, security/concurrency/e2e **258**, and integration **17**. The opt-in SQL Server migration and row-version tests ran against two exact disposable databases and both were cleaned with `audit_database_remaining=0`. The aggregate `verify.ps1` stall remains historical and is not counted as a pass.

## Latest dismiss contract correction (2026-10-05)

The historical `deleted`/`dismissed` mismatch is corrected in the current worktree: `dismiss_notification` now expires the row for visibility purposes and returns `status=dismissed`. The focused unit and API notification scope passed **25 tests, 0 failed, 0 skipped**. This is the service/API sub-check; the newer Browser dismiss correction below closes the single-item graphical post-condition.

## Latest Browser dismiss correction (2026-10-05)

The previously open graphical dismiss gate was exercised against one disposable Admin fixture after action-time confirmation. The exact Browser row for `AUDIT_DISMISS_FIXTURE_601B33526EBB` was dismissed once; the item disappeared from the notification dialog and the UI showed `Đã xóa thông báo.`. A direct SQL Server read confirmed soft state rather than hard deletion: the row remained with the same title, `expires_at=2026-10-05 14:50:30.184000`, and `read_at=NULL`. The Admin session logged out cleanly afterward.

This closes the single-item Browser -> API -> SQL Server dismiss post-condition for the current `status=dismissed` contract. It does not establish idempotency for rapid double-click, timeout/retry or bulk delete, and it does not expand role coverage.

## Browser download file-specific evidence (2026-10-05)

The visible authorized DSA201 PDF path has a readable same-name file at 1,169 bytes with `%PDF-1.4` and `%%EOF`, but the file pre-existed this replay. A distinct-resource replay of `Cau_truc_Heap_va_Priority_Queue.pdf` emitted a download event and then remained at a 1,145-byte `.crdownload` for 20 seconds with no finalized PDF. This is file-specific integrity evidence plus a fresh-stream partial, not a general Browser-finalization pass.

## Latest Student rapid mark-all correction (2026-10-05)

The prior detached-node observation is superseded for the controlled Student fixture replay. A disposable unread notification was targeted to Student1; the exact Browser `Đã đọc tất cả` control was double-clicked once. The UI settled at `Chưa đọc (0)` and showed one success toast. SQL Server retained exactly one notification row and one event with a single `read_at` value; the fixture was then removed and both targeted counts returned zero. This is a scoped Browser/DB idempotent-state pass for mark-all, not a general proof for delete, timeout retry or every role/producer.

## Latest fresh-resource download correction (2026-10-05)

The same-name PDF integrity evidence is not sufficient to prove a new transfer because that file already existed before the replay. A different visible DSA201 resource, `Cau_truc_Heap_va_Priority_Queue.pdf`, emitted a Browser download event and stayed as a 1,145-byte `.crdownload` for the first 20 seconds, but then finalized at 1,145 bytes with `%PDF-1.4` and `%%EOF`; no partial remained. This is a **PASS after delayed Browser completion**, with a timing/feedback concern rather than a terminal stream failure.

## Latest REST role-filter regression correction (2026-10-05)

The notification list, unread-count and mark-all-read routes previously treated unsupported or actor-ineligible `role`/`target_role` values as silent no-ops. A parametrized Student-authenticated RED regression confirmed HTTP `200` for both `ADMIN` and `BOGUS` where the contract requires validation failure.

The implementation now uses one canonical role normalizer: only `STUDENT`, `INSTRUCTOR` and `ADMIN` are accepted, and the authenticated actor must hold the requested role. The GREEN regression returned HTTP `400`, `success=false`, `data=null`, `error.code=VALIDATION_ERROR` for all three routes and both invalid values; valid lower-case `student` remained `200`.

Evidence: RED **2 failed**, GREEN **2 passed**, current notification API/service/IDOR scope **34 passed, 0 failed, 0 skipped**, scoped Ruff passed, and `git diff --check` passed. This closes the scoped REST filter-validation defect only; it does not close the Browser upload/quarantine, external SMTP/inbox, complete producer/role, historical-data or broader retry/idempotency gates.

## Latest complete no-skip verification after role-filter correction (2026-10-05)

The current source was rerun in non-overlapping partitions: root **298**, unit **633**, API **385**, security/concurrency/e2e **258**, and real SQL Server integration **17**. Total: **1,591 passed, 0 failed, 0 skipped**; collection reported **1,591 tests**. The frontend suite independently reported **105 passed, 0 failed, 0 skipped, todo 0**. SQL Server integration created and removed the two exact disposable gate databases, each with `audit_database_remaining=0`. This supersedes the prior 1,589 checkpoint for execution evidence but does not close the independent Browser/email/producer-role acceptance gates.

## Latest Student result-PDF Browser replay (2026-10-05)

Student1 opened the visible scored result `#/student/assessments/results?id=db76cdce-bef6-470d-be11-7d35cc9ab96b`. The `Xuất bảng điểm (PDF)` control is implemented as `window.print()` at `frontend/assets/js/views/student.js:5375`; it is not an application download endpoint. A semantic click timed out during input dispatch, and a fresh coordinate retry left the page and accessibility tree unchanged. No new tab, toast, verifiable download event or new file appeared in `C:\Users\LENOVO\Downloads`; the directory contained only the earlier resource PDFs. B-033 remains **NOT VERIFIED**, with no product/database mutation observed.

## Latest Browser upload blocker confirmation (2026-10-05)

The current live CS201 page was retried with Computer Use rather than the rejected direct file-chooser injection. Both visible upload controls were clicked through the accessibility surface, but no native picker appeared and the input stayed unselected. No upload request or SQL mutation was observed. This reproduces the same Browser boundary blocker and does not change the product result to PASS.

Instructor1 reached the real CS201 cover-upload control, but Edge again rejected the disposable fixture at `fileChooser.setFiles` with `Not allowed`. The input stayed empty (`files=null`, `value=''`), so no upload request or database post-condition was produced. The fixture and session were cleaned up. This is an environment blocker and remains explicitly unpassed.

## Current Admin mark-all Browser + SQL Server replay (2026-10-05)

The fresh Admin notification center started with badge `2` and `Chưa đọc (2)`. The visible `Đã đọc tất cả` action completed without removing the list: the Browser then showed badge `0` and `Chưa đọc (0)`. A read-only query in the running SQL Server-backed web container verified the active Admin role scope for `admin@pwd301.local` at `total=20`, `unread=0`, `read=20`. This closes the single-action Admin mark-all UI/API/DB post-condition for the existing mark-all contract. It does not prove rapid Browser double-click behavior, other role contexts, or dismiss/delete semantics.

## Current dynamic SECURITY telemetry redaction correction (2026-10-05)

The RED regression first showed that a shared SECURITY dispatch could preserve a raw IPv4 in notification title, body and action URL even after the seeded security row was corrected. The shared service now redacts IPv4 values in all three user-facing fields. The current focused notification unit/API/demo/security scope passed **37 passed, 0 failed, 0 skipped**. The complete non-overlapping current split passed **1,589 passed, 0 failed, 0 skipped**, including **17** disposable SQL Server gates with `audit_database_remaining=0` for both databases.

This closes the shared SECURITY dispatch boundary, not the complete producer catalog or external SMTP/inbox gate.

## Latest manual ESSAY grading correction (2026-10-05)

The RED frontend regression initially failed because the API client lacked the server-authoritative ESSAY grading method and the Instructor detail had no pending-grade control. The implementation now sends `awarded_points`, a required reason and the grade `row_version` through the existing grading endpoint. Student result rendering now uses the persisted essay answer and manual awarded points/status instead of choice-only fields.

Focused GREEN passed **3 frontend tests, 0 failed, 0 skipped**. The full Node frontend suite passed **105, 0 failed, 0 skipped**. The full API partition passed **383**. In a visible Browser replay using a disposable controlled attempt, Instructor saved `3.5` points with a reason, saw the success toast, and reopened the modal at `3.5 / 20` and `3.5 / 4`; SQL Server confirmed `MANUAL_GRADED`, `GRADED`, the reason and rowversion `0000000000112d3c`. The fixture and all related grade/result/orphan rows were removed afterward.

This is a scoped pass for Instructor UI -> API -> service -> SQL Server and Student result UI. A direct Browser replay of the existing released ESSAY result visibly showed the answer, `4 / 4 đ`, manual feedback and no choice labels. The fullscreen limitation applies only to creating a new controlled attempt, not to the released-result acceptance path.
## Latest Student result-PDF Browser verification after remediation (2026-10-05)

The result action is now an anchor with `ID=download-student-result-pdf-btn`, `download`, and `/student/attempt/<attempt_id>/result.pdf`; source and Node regression checks confirm there is no `window.print()` call. Student1 clicked the visible link on the released result. Edge created `C:\Users\LENOVO\Downloads\CS101-bang-diem.pdf` (1,713 bytes); the file starts `%PDF-`, has terminal `%%EOF`, and `pypdf` extracted one page containing `Score: 1.00 / 16.00`. The route uses session authorization and blocks unreleased scores with `403`.

This closes B-033 for the Student released-result path. It does not close the separate lesson-resource/file-producer timing, upload/quarantine, or external delivery gates.

## Latest answer-visibility correction (2026-10-06)

The prior SQL/Browser replay exposed a truthfulness defect at the `AFTER_CLOSE` boundary: the backend correctly withheld the essay answer, but the Student renderer labeled the omitted field `Không trả lời`. A TDD RED assertion then passed after the minimal frontend change added the explicit policy-hidden copy `Câu trả lời đang được ẩn theo chính sách khảo thí`; visible empty answers retain the unanswered label and no hidden answer/choice is exposed.

The focused frontend file passed **4/4**, the answer-visibility security test passed **1/1**, the mixed manual-grading API test passed **1/1**, the full frontend suite passed **107/107** with zero skips, and Ruff passed. A post-fix Browser visual replay was attempted but the CUA environment currently exposed no browser binding (`browsers=[]`), so Browser acceptance is explicitly pending. The disposable SQL Server fixture was stopped and removed with `audit_database_remaining=0`.

## Latest result truthfulness correction (2026-10-06)

The result surface also contained a fixed signature-like value (`7f8a92b1...10243`), a fabricated instructor fallback and a fabricated 45-minute fallback. A TDD RED regression detected all three; GREEN now renders only API-provided `signature_hash`, `instructor_name` and `duration_minutes`, or the explicit unknown state `Chưa có dữ liệu`. The full frontend suite passed **108/108** with zero skips, and Ruff passed. No Browser visual acceptance is claimed while the CUA Browser inventory remains empty.

## Latest lesson-flag idempotency regression (2026-10-06)

The new RED test first failed because the two Admin lesson-flag routes ignored X-Idempotency-Key: the first response had no replay marker and the changed-payload retry incorrectly returned HTTP 200. The minimal shared-service fix now persists the key on NotificationEvent.event_key, returns the existing notification/audit outcome for an exact retry, and rejects changed data with 409 CONFLICT. REST and Web routes both use the same service and atomic transaction.

Verification: tests/api/test_admin_lesson_flag_notification.py passed **9, 0 failed, 0 skipped**; the notification API/service scope passed **27, 0 failed, 0 skipped**; Ruff and diff check passed. A fresh SQL Server fixture replay reported **3 cases, 0 failed, 0 skipped**, with exactly one audit/event/notice and exact database cleanup audit_database_remaining=0. Browser rapid retry remains pending because CUA currently has no available Browser.

## Latest distinct-event visibility regression (2026-10-06)

The RED test proved that the notification list hid one of two distinct events solely because their title/body matched. The fix removes only that global presentation heuristic; it does not alter durable rows or producer idempotency. Existing repeated-copy tests were updated to assert truthful visibility, while keyed lesson-flag and broadcast retries retain explicit dedupe behavior.

Verification: the combined Admin flag + notification API/service scope passed **37, 0 failed, 0 skipped**. Ruff and diff check passed. No Browser result is claimed because CUA still reports no available Browser.
The fresh SQL Server replay then confirmed the same result over the real HTTP boundary: 2 durable rows and 2 REST items with the two distinct event types; **1 case, 0 failed, 0 skipped**, exact disposable cleanup remaining 0. This is API/SQL evidence, not Browser visual evidence.
## Latest generic event-key regression (2026-10-06)

The new RED regression detected that emit_event silently returned an old row when a caller reused the key with a changed event type and payload. The fix adds semantic comparison after payload sanitization while preserving exact replay behavior. This prevents a mismatched retry from reaching notification fan-out through an unrelated event.

Verification: notification/flag scope **38 passed, 0 failed, 0 skipped**; Ruff and diff check passed. The disposable SQL Server probe reported **2 cases, 0 failed, 0 skipped**, including event_key_conflict=true, and cleanup returned audit_database_remaining=0.
## Latest SQL Server seed-idempotency regression (2026-10-06)

The disposable runtime was seeded by prepare, then seed_demo was run again against the same SQL Server database. No created lists, notification/audit additions or count changes occurred. The probe passed **1 case, 0 failed, 0 skipped** and exact cleanup returned audit_database_remaining=0. This closes the current seed-idempotency regression without mutating live PWD301.

## Latest shared-dispatch idempotency regression (2026-10-06)

The new RED test attempted to pass a stable UUID through `dispatch_notification()` and failed because the helper did not expose that argument. The minimal GREEN change forwards the key to `emit_event()`. An exact retry now returned the same notification and left exactly one event and one recipient row. The focused notification/flag regression scope passed **39 passed, 0 failed, 0 skipped**; Ruff, compile and diff check passed. This is not evidence that every producer is keyed, and Browser rapid-retry acceptance remains pending while CUA has no Browser.

## Latest keyed-dispatch content regression (2026-10-06)

The first RED run found that a changed body with the same `event_key` did not raise a conflict because dispatch presentation fields were not part of the event payload. The fix adds a private keyed `_dispatch_contract`. GREEN verification now proves exact retry reuses one event, one in-app row and one email outbox row; changed body raises `ConflictError` with no new outbox side effect. The focused notification/flag scope passed **39 passed, 0 failed, 0 skipped**. AST inventory separately records **35 unkeyed direct dispatch callsites**, so full producer adoption remains open.

## Latest enrollment-producer key regression (2026-10-06)

The enrollment RED test found that the two `STUDENT_ENROLLED` dispatch calls had no stable key. The producer now derives distinct UUIDv5 keys from the flushed enrollment ID and recipient role. Unit tests passed, and the SQL Server disposable probe created a real enrollment, replayed both exact events, and retained exactly two events/two notifications with **3 cases, 0 failed, 0 skipped**; cleanup returned zero. The current AST inventory now has **32 direct dispatch callsites with neither an explicit key nor a prebuilt event**, so full producer coverage is still open.

## Latest password-security producer key regression (2026-10-06)

## Latest course-lifecycle producer-key regression (2026-10-06)

The RED test reproduced that course submission/approval/rejection dispatches did not include an event_key. The minimal fix retains the lifecycle AuditEvent, flushes it before fan-out and derives a recipient-scoped UUIDv5 from its ID and action. Unit verification passed the three lifecycle branches. On the disposable SQL Server fixture, the persisted approval event replayed through the shared dispatcher with event and notification counts unchanged at 1 -> 1; the probe reported 4 cases, 0 failed, 0 skipped, and cleanup returned zero. The current producer inventory is 35 calls / 7 explicit keys / 1 prebuilt event / 27 neither; Browser and external delivery remain unverified.

## Latest course-owner reassignment producer regression (2026-10-06)

The RED test reproduced missing keys in the former-owner and new-owner notification calls. The fix retains and flushes the COURSE_OWNER_REASSIGNED AuditEvent and derives separate recipient-scoped UUIDv5 keys. GREEN passed the unit regression with both recipients and distinct keys. The current inventory is 35 calls / 9 explicit keys / 1 prebuilt event / 25 neither. No dedicated SQL Server replay or Browser acceptance is claimed for this producer yet.

## Latest password-reset token producer regression (2026-10-06)

The RED test showed that a consumed password-reset token changed auth_version but emitted SECURITY_PASSWORD_CHANGED without the mutation key. The fix reuses the password-change UUIDv5 helper. GREEN passed the reset-token workflow and found the expected durable NotificationEvent. The disposable SQL Server probe then exercised both normal and reset-token mutations, replayed both exact events and kept event/notification/email rows at 1 -> 1; it reported 6 cases, 0 failed, 0 skipped, and cleanup returned zero. The current inventory is 35 calls / 10 explicit keys / 1 prebuilt event / 24 neither. Browser acceptance and external delivery remain unverified.

## Latest account-suspension producer regression (2026-10-06)

The RED test showed that suspend_user() incremented auth_version but emitted ACCOUNT_SUSPENDED without a stable key. The fix derives the UUIDv5 from user ID and post-suspension auth_version. GREEN passed the unit test. The disposable SQL Server probe then replayed normal password, reset-token and suspension security notices and kept each event/notification/email set at 1 -> 1; it reported 9 cases, 0 failed, 0 skipped, and cleanup returned zero. The current inventory is 35 calls / 11 explicit keys / 1 prebuilt event / 23 neither. Browser acceptance and external delivery remain unverified.

The password RED test found that `change_password()` emitted `SECURITY_PASSWORD_CHANGED` without a stable key despite incrementing `auth_version`. The fix derives UUIDv5 from user ID and the post-change version in both password mutation paths. Unit tests passed; the SQL Server disposable probe verified exact replay preserved one event, one notification and one email outbox row with **3 cases, 0 failed, 0 skipped**, then cleanup returned zero. Current AST breadth is 30 calls with neither key nor prebuilt event.

## Latest durable producer expansion regression (2026-10-06)

New RED assertions reproduced missing event keys for role assign/update/revoke, Admin course edit, course-change submission/approval and infected-file quarantine. GREEN passed the targeted unit/API cases; Ruff passed. The current AST inventory is **35 direct calls / 25 explicit keys / 1 prebuilt event / 9 neither**. No skipped test was counted as pass. Dedicated SQL replay, Browser/CUA visual/rapid-retry acceptance and external inbox evidence remain unverified.

## Latest complete producer inventory regression (2026-10-06)

The final nine unkeyed direct calls were covered with deterministic keys: assessment result, YouTube health, Admin course-change aliases, instructor lesson-change alias, and prerequisite request/approval/rejection. Focused attempt tests passed **13**, change-request/prerequisite API tests **28**, and the combined affected service group **79**; all had zero failures and zero skipped tests. Ruff and compile passed. AST now reports **35 direct calls / 34 explicit keys / 1 prebuilt event / 0 neither**. SQL replay, Browser/CUA visual/rapid retry and external inbox evidence remain unverified.

## N-168 aggregate regression (2026-10-06)

The full verifier completed with SQL Server opt-in URLs provisioned against disposable databases: **1607 passed, 0 failed, 0 skipped**, exit code 0. The four SQL Server cases were executed and the databases were removed afterward. No claim is made for unavailable Browser/CUA or external inbox evidence.

## N-169 email backlog regression (2026-10-06)

The live SQL check reproduced the notification delivery gap: 115 pending email rows, oldest 2026-09-19, zero background jobs. Regression coverage now passes the worker bridge, fail-closed production transport, configured SMTP TLS adapter, stale queue health and Compose worker contract; the scoped set is **41 passed**. The live stack was intentionally not restarted without `MAIL_HOST`/`MAIL_FROM`; no claim is made that existing live email rows have been delivered.

## N-170 current regression boundary (2026-10-06)

The current aggregate regression completed with **1612 passed, 0 failed, 0 skipped** and disposable SQL Server databases were removed. Computer Use was revalidated but exposed no browser surface; direct IAB creation returned `Browser is not available: iab`. Thus automated regression is PASS, while Browser visual/interaction, file chooser/quarantine and external inbox regression remain NOT RUN or PARTIAL rather than silently accepted.

## N-171 historical duplicate regression boundary (2026-10-06)

Read-only live SQL regression confirms 143 events have unique event keys and all link to notifications; repeated presentation-copy groups remain because legacy payloads do not consistently carry a business transition identity. No cleanup was executed. This is a data-disposition safety hold, not a regression pass for historical deletion.

## N-172 API envelope regression (2026-10-06)

TDD RED reproduced the missing `data` member on the session notification list. After the route correction, `tests/api/test_notification_api.py` completed **16 passed**, Ruff and compile passed, and the focused frontend notification/PDF suite completed **7 passed**. The 1612-test aggregate remains an earlier pre-patch checkpoint and is not claimed as post-patch verification.

## N-173 final regression (2026-10-06)

The corrected full run completed with **1613 passed, 0 failed, 0 skipped**, exit code 0 and valid SQL Server disposable URLs. The earlier malformed-URL failure run is retained only as harness evidence and is not counted. Current residual gates are Browser/CUA, approved external inbox, file chooser/quarantine and historical disposition.

## N-174 acceptance-scope decision (2026-10-06)

The owner confirmed that SMTP/inbox is not deployed and may be skipped for this acceptance cycle; it is no longer treated as a required regression gate. Browser/CUA and file chooser/quarantine remain residual gates because the runtime exposes no Browser surface.

## N-175 Browser regression (2026-10-06)

Edge Browser regression covered Student, Instructor and Admin demo sessions. Login/logout and permission toasts rendered; Instructor mark-all-read changed 15 to 0 and rendered confirmation; Admin Operations rendered the live degraded outbox state. The run also reproduced visible repeated `#70014` copies and mixed-language legacy messages.

## N-176 file regression boundary (2026-10-06)

The clean resource download path completed. Upload fixture assignment failed with the Edge extension `Not allowed` file-URL permission error. There is no live PENDING/QUARANTINED revision to exercise, and direct rejected-file navigation was blocked by the client before application response; quarantine UI regression is therefore not passed.

## N-177 Student notification regression (2026-10-06)


Student notification UI rendered the expected role scope, category controls and `0 mới` state. Regression evidence also reproduces mixed-language legacy content in the list; it is recorded as an open content/catalog finding rather than a passed message-standard assertion.
## N-178 Browser upload regression (2026-10-06)

The clean upload regression now passes through Edge: `setFiles` accepted the local image fixture, the crop dialog was applied, and the UI showed `Đã cập nhật ảnh đại diện khóa học.` SQL Server confirmed the persisted asset/revision and two passing security scans. The rejected-file regression remains open because the Browser client blocks the URL before the application can expose its denial response; SMTP/inbox remains intentionally out of scope.
## N-179 rejected-file regression boundary (2026-10-06)

The second Browser route variant reproduced `net::ERR_BLOCKED_BY_CLIENT`, so the regression still cannot observe the app’s denial response. The asset’s lack of a lesson/resource attachment is recorded as a data-scope limitation; this does not weaken the fail-closed backend evidence and does not constitute a Browser pass.
## N-180 authenticated rejected-file regression boundary (2026-10-06)

The final route variant was exercised from the logged-in Instructor tab and reproduced the same client-side block. The regression therefore remains unverified at the Browser transport boundary; no bypass or quarantine override was introduced.
## N-181 system-category regression (2026-10-06)

The authenticated Instructor regression rendered the `Hệ thống` category with the expected two records and no state mutation from filtering. The mixed-language maintenance content remains a reproduced content/catalog regression.
## N-182 assessment-category regression (2026-10-06)

The Instructor regression confirms the empty assessment category is rendered explicitly rather than populated with guessed data. Broader assessment producer/role coverage remains outside this single empty-state observation.
## N-183 course-category regression (2026-10-06)

The authenticated Instructor regression rendered all 16 course-category records and reproduced the three `#70014` presentation copies. This confirms the historical duplicate observation remains visible after the current UI changes.

## N-184 Admin broadcast validation regression (2026-10-06)

The authenticated Admin regression opened the real broadcast modal and exercised empty and title-only submissions. Both produced the expected Vietnamese validation warnings, and canceling the modal returned to governance without a durable write. The post-probe live SQL snapshot remained `143` notification events, `168` notifications, `115` pending email deliveries and `0` background jobs. This is not a valid-send or external-email regression result; SMTP/inbox is excluded by owner decision.

## N-185 rejected-file regression boundary (2026-10-06)

The current live data has seven rejected revisions and no lesson-resource attachment for any of them. The regression therefore cannot exercise the user-facing quarantine path without creating a new fixture or changing a rejected asset; neither was done. Browser direct-route denial remains unverified because Edge intercepted the request before the application response.

## N-186 rejected-file API regression (2026-10-06)

An authenticated Instructor HTTP regression against the existing rejected asset returned the expected `403 FILE_INFECTED` JSON envelope and no content bytes. This closes the backend regression boundary while retaining the Browser/UI interception as an explicit unverified gate.

## N-187 SMTP/inbox regression scope (2026-10-06)

External-provider delivery and inbox receipt are **scope-excluded** for this regression cycle by owner decision. No external send was attempted and no delivery result is presented as a pass.

## N-188 historical duplicate regression boundary (2026-10-06)

The new read-only regression narrows the historical duplicate boundary: 12 groups remain explainable and 2 legacy groups remain unresolved. Since no live write occurred, append-only history is unchanged and no repair regression can be claimed.

## N-189 Browser quarantine-override regression boundary (2026-10-06)

The live Browser regression confirms that the primary-admin quarantine tool opens and fails closed on an empty form. The dialog was canceled without credentials or an asset ID, so the privileged release path and its audit transition remain unverified.

## N-190 focused quarantine backend regression (2026-10-06)

The focused backend regression passed with 3 tests: 2 override-specific tests and 1 quarantined/infected fail-closed authorization test. The deselected tests and the unexecuted credentialed release path remain outside this focused result.

## N-191 Browser runtime regression observation (2026-10-06)

The current Browser regression capture had no application console error. The Tailwind CDN production warning remains visible but did not alter the exercised notification/security UI state.

## N-192 legacy identity regression boundary (2026-10-06)

The read-only regression did not find a new durable mapping for the 17 legacy rows. Their recipient-only event fields and absent audit correlation preserve the existing safety hold; no append-only history was changed.

## N-194 rejected-file Browser regression boundary (2026-10-06)

The repeated Browser regression reaches the Edge client block before the application. This preserves the honest boundary: backend/API fail-closed passes for the sampled asset, while Browser denial rendering and response-level regression remain unverified.

## N-195 download-route family regression boundary (2026-10-06)

The same Edge interception reproduced on the API download path, so the current regression result is a Browser-environment block across both tested route families, not a route-specific application regression.
## N-196 exact business-window recheck (2026-10-06)

A further read-only SQL Server check searched `course_change_requests` in the exact event windows for the 13 unresolved `LESSON_CHANGE_REQUEST` copies (2026-09-28 03:10:04-03:16:28 UTC) and the four unresolved `COURSE_CHANGE_APPROVED` copies (2026-09-28 05:44:15-05:44:22 UTC and 2026-09-29 02:09:31 UTC). It returned no rows in those windows. Current CS101 change-request rows exist at other times, but none can be safely joined to these notifications from the stored recipient-only target, NULL correlation/actor fields and generic action URLs. This is additional evidence for an owner-approved mapping/rehearsal hold; no append-only history was mutated. Final status remains **PARTIAL - not release-accepted**.
## N-197 Browser fail-closed resource-visibility proof (2026-10-06)

Using the enrolled Student Browser session, a temporary, explicitly labeled `lesson_resources` row `120002` was attached to published SEXGAY lesson `130025` and pointed at existing asset `3EB32DEA-150D-4724-B42C-2FEBB53BAD16`. SQL identified the asset as `PENDING` with current revision `REJECTED`, reason `Infected: ZIP-Embedded-Executable`. The real Student `Tài liệu` panel still rendered only the four ACTIVE files and exposed no link, preview or download CTA for the rejected resource. A direct Student-scoped URL was separately attempted and Edge returned `net::ERR_BLOCKED_BY_CLIENT` before an application response, so the UI omission is the verified Browser fail-closed result and the direct response remains environment-blocked. The temporary resource row was then deleted by exact ID and label; SQL verified the lesson returned to four resource links, the rejected asset remained `PENDING`, its revision remained `REJECTED`, and it had zero resource links. No file revision, quarantine state, notification row or audit record was mutated. Final status remains **PARTIAL - not release-accepted** because direct Browser response observation and historical owner-approved notification disposition remain open.
## N-198 acceptance checkpoint after temporary Browser fixture (2026-10-06)

The temporary Browser fixture proves the Student-facing file-visibility branch: a linked `PENDING/REJECTED` asset was omitted from the real Student resource panel, while the four `ACTIVE` files remained visible. Exact cleanup restored the lesson to four resource links and left the asset/revision unchanged. Therefore Student UI fail-closed visibility is **PASS for this sampled asset**; the direct download response remains **BLOCKED ENVIRONMENT / UNVERIFIED** because Edge intercepts the URL before the application response. SMTP/inbox remains **OUT OF SCOPE** by owner decision. Historical notification disposition remains open for the two unkeyed groups/17 rows, so the overall audit remains **PARTIAL - not release-accepted**.
## N-199 historical outbox identity recheck (2026-10-06)

Read-only SQL Server inspection found one `email_deliveries` row for each of the 17 unresolved notification events. Those rows preserve recipient email, template code, random dedupe UUID and `PENDING` status, but have NULL subject/body and no `course_change_request_id`, target resource or correlation field. This provides no additional safe business identity for historical repair. SMTP/inbox remains owner-authorized **OUT OF SCOPE**; no delivery was attempted and no outbox/history row was mutated. Final status remains **PARTIAL - not release-accepted**.
## N-200 stale identity/content recheck (2026-10-06)

## N-209 fresh full verification checkpoint (2026-10-06)

The current controlled verifier completed with **1613 passed, 0 failed, 0 skipped** in `1260.83s` and returned `VERIFY_EXIT_CODE=0`. The wrapper dropped the two disposable SQL Server migration/concurrency databases and verified `REMAINING=0` for each. This is a current automated regression pass; it does not convert the Browser file-chooser/direct-response environment block, the unresolved 17-row historical append-only disposition, or the owner-authorized SMTP/inbox scope exclusion into passes.

## N-210 fresh Student filter-branch regression (2026-10-06)

The live Student Browser notification dropdown was reopened and exercised without a mutation: `Khóa học` returned 2 records, `Hệ thống` returned 4 records, and `Chưa đọc (0)` rendered the explicit empty state `Không có thông báo nào` / `Bạn đã xem hết các thông báo trong mục này.`. The system-filter legacy/test-like content remains an active data-quality finding; no delete action was submitted.

## N-211 Instructor file-chooser regression boundary (2026-10-06)

After a real Instructor demo login, both course-authoring cover-upload controls were clicked. The Browser page remained unchanged, no native file dialog appeared in the Computer Use surface, and no file or business data was submitted. The regression result is **BLOCKED ENVIRONMENT / UNVERIFIED**, not a pass; the session was restored to the Student demo account afterward.

## N-212 Admin role notification regression (2026-10-06)

The Admin Browser replay reached the live notification center and reproduced the role-specific states: default `Chưa đọc (0)` empty, `Tất cả` **15**, `Khóa học` **10**, and `Hệ thống` **3**. The system subset contained the legacy ASCII maintenance, backup-completed and security-login-warning records. No delete or other notification mutation was submitted, and the session was restored to Student. This regression confirms the Admin filter branches but leaves the recorded data-quality issue open.

## N-213 Instructor role notification regression (2026-10-06)

The Instructor Browser replay reached the live notification center and reproduced `Tất cả` **18**, `Khóa học` **16**, `Hệ thống` **2**, plus explicit empty states for `Khảo thí` and `Chưa đọc (0)`. The system subset contained the legacy ASCII maintenance and rejected-malware upload notifications. No delete or other notification mutation was submitted, and the session was restored to Student. This regression confirms the Instructor filter branches while leaving language/data normalization open.

## N-214 current notification API regression (2026-10-06)

The focused current-worktree command `python -m pytest -q tests/api/test_notification_api.py` completed with **16 passed in 10.59s**, exit code `0`. This is a fresh backend/API regression result for the covered test file only; the unrun outage/status-code branches, complete producer breadth, Browser rendering and external SMTP/inbox remain separately scoped.

## N-215 current Admin lesson-flag notification regression (2026-10-06)

The focused command `python -m pytest -q tests/api/test_admin_lesson_flag_notification.py` completed with **9 passed**, exit code `0`. Durable audit/owner notification, REST/Web idempotency, changed-payload rejection and notification-sink rollback all passed in the isolated suite. This does not close live Browser producer breadth or the environment/external-service blockers.

## N-216 current notification service/security/frontend regression (2026-10-06)

Fresh focused checks completed without skips: notification service unit **15 passed in 8.68s**; notification IDOR/security **7 passed in 4.06s**; and the combined frontend notification/router/topbar command **18 passed, 0 failed, 0 skipped**. The regression result is limited to these named scopes; full producer/role breadth, Browser file/quarantine behavior and external SMTP/inbox remain open.

## N-217 current producer/business-flow regression (2026-10-06)

Fresh focused checks completed without skipped tests: Admin backend **16 passed in 11.25s**; Admin sub-role/RBAC **5 passed in 4.12s**; selected course-changeset cases **2 passed, 10 deselected in 1.98s**; and selected lesson-change cases **5 passed, 3 deselected in 4.37s**. Deselected cases are explicitly not passes. These results strengthen the named producer/business flows but leave complete producer adoption, live Browser replay breadth and external delivery separately open.

## N-218 current Browser timing replay (2026-10-06)

A fresh Edge Computer Use replay started from a clean logout, selected the visible Instructor demo account, and verified the correct `#/instructor/dashboard` identity. The immediate login transition exposed the success toast; the next captured state was the settled Instructor dashboard. Opening the notification center showed `Thông báo 0 mới` and `Chưa đọc (0)` with an explicit empty state, which is consistent with the unread filter. A fresh semantic click on `Tất cả` then rendered **18** rows: **16** course notifications and **2** system/security notifications. `Khảo thí` was empty. No destructive or business-mutating action was taken; the run logged out and restored Student1. The captured Instructor timing/filter replay passes, while sub-render timing before observation, other-role timing, file/quarantine UI and SMTP/inbox remain unverified or out of scope.

## N-219 current Guest notification boundary regression (2026-10-06)

Real Edge logout returned to `#/auth` with no notification control visible. Direct navigation to `/auth/notifications` from that logged-out state produced `net::ERR_BLOCKED_BY_CLIENT` before an application response. The API/session test still covers the unauthenticated 401, but the Browser Guest error presentation remains **UNVERIFIED** because the client policy intercepted the route. Student1 was then restored and no business or notification data was changed.

## N-220 focused notification API rerun (2026-10-06)

Fresh command `python -m pytest -q tests/api/test_notification_api.py` completed with **16 passed in 10.15s**, exit code `0`, with no skipped tests. This strengthens only the named lifecycle, filtering, dismiss/read, preferences, broadcast/idempotency, malformed-payload, role-filter, canonical-envelope and session/IDOR regression scopes; it does not close unrun 422/429/502/503 branches, complete producer breadth, Browser Guest presentation or SMTP/inbox.

## N-221 current disjoint no-skip regression verification (2026-10-06)

The current wrapper invocation exited `0`, while its pytest phase reported **1609 passed, 4 skipped** because SQL Server URLs are not configured in the parent process. The exact disposable SQL helper then ran `tests/integration` with both SQL URLs injected and returned **17 passed in 24.58s**; both disposable databases were removed with `audit_database_remaining=0`. After removing the 13 overlapping non-SQL integration cases, the current disjoint total is **1613 passed, 0 failed, 0 skipped**. The wrapper's green exit alone is not treated as proof of no skips. Browser environment gates, historical identity and SMTP/inbox remain separate.

## N-222 disposable producer/idempotency regression (2026-10-06)

Five isolated SQL Server probes completed with no failed expectations or skips: identical-copy visibility/event-key conflict **2 cases**; seed replay **1 case**; enrollment key replay **3 cases**; course lifecycle key replay **4 cases**; and password/reset/suspension security-key replays **9 cases**. The expected event, notification and email-row counts remained stable on exact replays, and the disposable audit database was removed with `audit_database_remaining=0`. This closes only the named SQL/API replay scopes; no Browser rapid-action result or external email receipt is inferred.

## N-223 disposable lesson-flag idempotency regression (2026-10-06)

The Admin lesson-flag replay on the isolated SQL Server fixture passed **3 cases, 0 failed, 0 skipped**: first `200`/`idempotent_replay=false`, exact retry `200`/`idempotent_replay=true`, and changed payload with the same key `409 CONFLICT`. SQL recorded one audit, one event and one owner notification, and cleanup returned `audit_database_remaining=0`. This closes the named moderation retry path only; Browser rapid-click visuals and complete producer breadth remain open.

## N-224 notification HTTP status applicability regression note (2026-10-06)

The current notification blueprint has explicit `200` success responses for every logical endpoint. The exercised error families remain `400` validation, `401` unauthenticated, `403` unauthorized, `404` missing resource and `409` idempotency conflict. Static source evidence shows no notification-specific `201`, `204`, `422` or `502` path; global `429`/`503` handlers are defined for other rate-limit or service-maintenance classes. This narrows the status matrix but does not claim unrun unexpected-`500`, outage/maintenance or retry-after behavior as passed.

## N-225 focused notification HTTP status regression (2026-10-06)

The fresh command `PYTHONPATH=src python -m pytest -q tests/api/test_notification_api.py tests/security/test_notification_idor.py` returned **23 passed in 9.89s**, exit code `0`, with no skipped tests. The assertion set covers `200` success/lifecycle responses, `400` malformed or invalid mutation input, `401` anonymous access, `403` IDOR/non-admin denial and `409` changed idempotency payload. It does not inject a notification-specific `404`, `422`, `429`, `500`, `502` or `503`, so those remain unverified and are not counted as passes.

## N-226 current Student Browser notification-surface regression (2026-10-06)

The live Edge Computer Use tab remained available at the authenticated Student dashboard for `Lê Hoàng Long`. The real notification popover rendered `Thông báo 0 mới`, `Chưa đọc (0)`, `Học viên` and **13** notification records across its category filters. It was closed through the visible control with no notification or business mutation. This regression is a current Student Browser rendering pass only; it does not close all-role timing, keyboard accessibility, file chooser or SMTP/inbox gates.

## N-227 isolated notification 404 contract regression (2026-10-06)

An isolated Flask test-client probe on in-memory SQLite authenticated a disposable Student and sent missing and malformed notification IDs to mark-read and delete. All three responses were **404** with `success=false`, `data=null` and `error.code=RESOURCE_NOT_FOUND`; no live database or notification history was touched. The sampled notification `404` contract is therefore evidenced, while `422/429/500/502` fault injection remains unrun.

## N-228 notification maintenance 503 and retry-after regression (2026-10-06)

The existing E2E command `PYTHONPATH=src python -m pytest -q tests/e2e/test_admin_ops_lifecycle_e2e.py` returned **5 passed in 4.37s**, exit code `0`, with no skipped tests. The maintenance scenario asserted the Student notification unread-count route returned `503` with `MAINTENANCE_MODE_ACTIVE` and `Retry-After: 1200`, then returned `200` after maintenance ended. This closes the sampled notification maintenance/`503`/`Retry-After` regression; unexpected `500` and notification-specific `422/429/502` cases remain unverified.

## N-229 isolated notification 500 and 429 fault-injection regression (2026-10-06)

An isolated Flask test-client probe on in-memory SQLite patched the notification list dependency to raise a generic runtime fault and observed **500 `INTERNAL_ERROR`** with a safe user-facing message. It then patched failed-email retry to raise `EmailRateLimitExceededError` and observed **429 `RATE_LIMIT_EXCEEDED`** with `Retry-After: 60`. No live database or notification history was touched; notification-specific `422` and `502` behavior remains absent from the current route mapping.

## N-230 notification 422/502 applicability boundary regression (2026-10-06)

The read-only source check confirms notification validation uses the shared `ValidationError` to produce `400`; there is no notification route response or global domain-handler mapping for `422` or `502`. These statuses are therefore **not applicable at the Flask notification boundary**. Any reverse-proxy or external-upstream `502` would be a separate infrastructure contract, not a missing notification-route regression.

## N-231 corrected AST producer inventory regression (2026-10-06)

A corrected read-only AST pass over `src/pwd301` classified `event_key` and prebuilt `event` correctly and found **35** direct dispatcher calls: **34** explicit deterministic keys, **1** prebuilt event at `src/pwd301/services/course_service.py:286`, and **0** neither. A prior probe that searched for `notification_event_id` was rejected as a harness-classification error; the product source was not modified. Runtime semantic key and retry/race verification remains separate.

## N-232 fresh Student Browser category-filter regression (2026-10-06)

The authenticated Edge Computer Use Student session opened the real notification popover and rendered `Thông báo 0 mới`, `Chưa đọc (0)`, plus **13** `Tất cả`, **7** `Khảo thí`, **2** `Khóa học` and **4** `Hệ thống` records when the visible filters were selected. The replay used only read-only filter actions and left notification/business state unchanged. This regression pass is limited to the Student Browser surface; all-role semantics, rapid retry/race paths, file chooser behavior and SMTP/inbox delivery remain separate scope or gates.

## N-233 repeated Instructor file-chooser regression boundary (2026-10-06)

The authenticated Edge Instructor session opened the OPS401 lesson studio and activated the document chooser control. No native chooser appeared, `apps=[]` remained authoritative for Computer Use, and the AX tree still showed exactly the pre-existing clean attachment without an upload placeholder. The regression result is **UNVERIFIED/BLOCKED ENVIRONMENT**, not a file-upload pass; rejected-file response and quarantine release remain open and no state was mutated.

## N-234 broader producer-service regression group (2026-10-06)

The isolated unit regression command over `test_course_service.py`, `test_enrollment_service.py`, `test_user_service.py` and `test_lesson_service.py` returned **90 passed in 59.65s**, exit code `0`, with no skipped tests. This is a current fixture-backed regression pass for four producer-heavy service areas. It does not generalize to all 35 dispatcher callsites or replace the missing complete Browser/API/DB/user-result replay.

## N-235 assessment/file producer-service regression group (2026-10-06)

The isolated unit regression command over attempt service, attempt submission service, file service and malware scan service returned **38 passed in 26.90s**, exit code `0`, with no skipped tests. This strengthens current fixture-level regression evidence for assessment and file/security paths, but it does not turn the Browser file chooser or quarantine acceptance gate into a pass.

## N-243 current dispatcher identity regression (2026-10-06)

The independent AST regression found 35 direct dispatcher calls with no missing identity mechanism: 34 explicit keys and one prebuilt event. This guards against regression to unkeyed callsites, but it does not replace semantic or live concurrency tests.

## N-242 producer-heavy service regression group (2026-10-06)

The fresh producer-heavy unit group passed 64 cases with zero failures or skips across authorization, notification core, email/outbox, completion and instructor-application services. This strengthens current regression confidence while leaving live all-producer role/retry and Browser chain acceptance open.

## N-241 current Admin lesson-flag regression reconciliation (2026-10-06)

The current Admin lesson-flag regression group passed all 9 cases with no skips, covering the current REST/Web path, malformed-body rejection, idempotent replay, changed-payload conflict and rollback. The earlier RCA-040/RCA-027 failure description is retained as historical evidence but is not reproduced by the current worktree.

## N-240 fresh API/frontend notification regression (2026-10-06)

The fresh API/IDOR command passed 23 cases with no skips, and the full frontend Node suite passed 108 cases with zero failures, skips or todos. This is a current transport/authorization/UI regression pass; complete producer semantics, Browser file/quarantine flows and SMTP/inbox remain separate scope or gates.

## N-239 fresh Admin notification-filter regression (2026-10-06)

The fresh Edge Admin replay exercised all visible read-only notification filters and rendered 15 total records, split as 1 assessment, 11 course and 3 system/security, with 0 unread. No mutation control was activated. This is a scoped filter/rendering regression pass; it does not establish complete producer semantics.

## N-237 fresh Admin notification-center regression (2026-10-06)

The fresh Edge Admin session rendered the notification center with 0 unread, the `Quản trị viên` role label and three persisted system/security records. The replay was read-only and introduced no state change. This is a scoped Admin UI regression pass; producer/broadcast behavior remains outside this replay.

## N-238 fresh Guest protected-route regression (2026-10-06)

After logout, Edge navigation to `#/student/notifications` redirected to `/auth`; the AX tree exposed the login surface and no authenticated notification control. This is a scoped route-boundary regression pass; API `401` coverage remains separate and SMTP/inbox remains out of scope.

## N-250 YouTube Browser/UI regression boundary (2026-10-06)

The real Instructor Browser path passed invalid-link validation with a safe Vietnamese warning and no mutation, but no course-wide scan control was rendered. Static frontend search confirms the scan API method has no caller. This is an open integration/ownership regression item, not a claim that the backend route failed; the session was logged out cleanly.

## N-249 YouTube route/API regression extension (2026-10-06)

The disposable regression now covers both route boundaries: unauthenticated 401 and authorized owner 200 with one broken report. Repeated route/service execution preserved one event and one notification. The isolated schema was dropped and no live data changed; Browser UI regression remains open.

## N-248 YouTube producer service/DB regression (2026-10-06)

`youtube-runtime-probe.py` returned exit code `0` with all assertions passing in an isolated in-memory database. It verified valid/no-op, network-error/no-op, broken-video persistence and exact replay convergence. The probe cleaned its schema and changed no product or live data. Route/API/Browser regression remains open.

## N-247 YouTube producer regression gap (2026-10-06)

No regression result can be claimed for the YouTube broken-video notification family: source and route are present, but no current test covers the scan or notification post-condition. This is recorded as an open regression item, not a failure reproduced by this checkpoint; no product or live data changed.

## N-246 producer-key semantic-shape regression (2026-10-06)

The independent AST regression found no random, clock-derived, constant or unclassified explicit event key among the 34 keyed dispatches; one prebuilt event remains separately scoped. No product code or live business data changed. This narrows the static regression risk but does not replace runtime duplicate/race and user-result checks.

## N-245 fresh Student notification-center content/filter regression (2026-10-06)

The fresh Edge Student replay passed the login-to-center and read-only filter path with counts `13/7/2/4` for all/exam/course/system and zero unread. It also reproduced sampled content-quality defects in the real UI: an unaccented Vietnamese maintenance message and two low-value seeded strings. No product or live business data was changed; Student was logged out cleanly. Overall audit remains PARTIAL because this replay does not establish global message counts or producer/DB ownership.

## N-244 grading/regrade producer-service regression (2026-10-06)

The isolated grading/regrade regression returned **25 passed, 0 failed, 0 skipped** in **26.49s** with exit code `0`. No product code or live business data changed. This is a current service-level regression pass; it does not elevate the overall audit above PARTIAL because complete producer semantics, Browser file/quarantine behavior, historical duplicate disposition and SMTP/inbox remain unresolved or out of scope.

## N-236 fresh Instructor notification-center regression (2026-10-06)

The authenticated Edge Instructor session on the OPS401 lesson studio opened the real notification center and rendered `Thông báo 0 mới`, `Chưa đọc (0)`, `Giảng viên` and **2** records, including the security notification for the rejected/quarantined `X_SENTINEL_VIBECODE_BASELINE_V2.zip`. The observation performed no mutation. It is a role/UI regression pass for an existing persisted notification; the upload-trigger and quarantine-release chain remains unverified.

The unresolved notification bodies do contain coarse labels: all 13 `LESSON_CHANGE_REQUEST` copies name CS101 and Lesson `Bài 1: Tổng quan về Kiến trúc Web & HTTP Protocol`, but none stores a change-request ID, durable target ID or correlation. The four `COURSE_CHANGE_APPROVED` copies name the same Lesson but their CTA points to course UUID `cf547469-d8b8-43ef-882c-721048826232`, which is absent from the current `courses` table; the current CS101 row has a different public UUID. Current CS101 change-request rows exist, including multiple historical candidates for the same lesson, but none matches the notification event windows. This confirms stale/missing business identity rather than an unresolved title-only query; no historical row was reassigned, deleted or merged. Final status remains **PARTIAL - not release-accepted**.

## N-251 frontend mechanism regression boundary (2026-10-06)

The read-only frontend inventory completed without changing product code or live data. It confirms 383 shared-toast invocations and separate alert/confirm/prompt paths, but does not prove that message language, status handling, duplicate suppression or accessibility announcements remain correct for every producer. This is a static regression checkpoint only; the overall audit remains **PARTIAL - not release-accepted** and SMTP/inbox remains out of scope.
## N-252 producer execution regression boundary (2026-10-06)

The focused producer regression set completed with 318 passing tests across the main run and targeted follow-up, zero failures and zero skips. Three disposable probes also passed and cleaned their SQLite/temp-storage fixtures. All 35 direct dispatcher callsites were executed at least once. This is a stronger current regression baseline, not a claim that every producer has complete role, retry-race or Browser end-to-end coverage; the audit remains **PARTIAL - not release-accepted**.
## N-253 Browser auth-error regression boundary (2026-10-06)

The real invalid-login flow still presents one inline error and no duplicate toast, so sampled ownership is stable. The dynamic element lacks explicit `role`/`aria-live`, and the approximately 6.45-second observation showed persistence without a defined timeout contract. This is a new accessibility regression boundary, not a claim that authentication itself failed beyond the expected invalid-credential response.
## N-254 Browser file-chooser regression boundary (2026-10-06)

The real chooser control remains rendered, but the supported Browser event path did not produce a chooser and detached the debugger after timeout. No product or live file data was changed by this attempt. This keeps the upload/rejected-response/quarantine chain outside the regression pass and preserves the environment-blocked classification.
## N-255 producer role regression boundary (2026-10-06)

The semantic inventory confirms identity coverage but leaves a role regression boundary: 18 producers rely on broad/unscoped target-role behavior. Existing tests cover representative role isolation and fan-out, but they do not establish that every broad producer is correct for every multi-role account. Overall regression status remains **PARTIAL - not release-accepted**.
## N-256 focused role/retry regression checkpoint (2026-10-06)

The selected role/retry regression group passed 8/8 with no failures or skips. No product code or live business data changed. It strengthens keyed retry and representative fan-out behavior, while the full producer semantic matrix, Browser file chain and historical-data disposition remain open.
## N-257 historical disposition regression boundary (2026-10-06)

The current SQL Server recheck is read-only and confirms 17 unresolved legacy
rows, each with one linked notification and one outbox row and with unique event
keys. It does not authorize repair and therefore reports no mutation regression
as passed. The [approval packet](09_HISTORICAL_NOTIFICATION_APPROVAL_PACKET.md)
defines the future disposable rehearsal and post-change checks. SMTP/inbox is
**OUT OF SCOPE**.
## N-258 Browser upload regression boundary (2026-10-06)

The repeated Edge attempt did not reach the application upload path. The
chooser event timed out and the Browser session reset; the harmless fixture was
never selected. No regression pass is claimed. Upload/quarantine acceptance
remains **BLOCKED ENVIRONMENT / UNVERIFIED**.
## N-259 Browser notification-content regression boundary (2026-10-06)

The current live sample still renders historical `#70014` copies and a mixed-
language system message, while category filtering remains usable. This is a
confirmed content/catalog regression sample, not a transport or duplicate-event
proof. The popover was closed without mutation; broader language and role
coverage remain open.
## N-260 role-view regression boundary (2026-10-06)

AST evidence confirms all 18 unscoped-role producers identify a concrete user;
no cross-user leakage regression is claimed. The unresolved regression is
same-user multi-role visibility and CTA compatibility when `target_role` is
NULL. Security/role events may be intentionally broad; route-specific paths
remain unverified individually.
## N-261 confirmed same-user role-view regression (2026-10-06)

Live REST replay confirms the same Admin review notification is returned under
ADMIN, INSTRUCTOR and STUDENT filters for a multi-role account. The row remains
owned by the correct user, so this is not an IDOR finding; the regression is
role-view contamination and an incompatible Admin CTA. No write was issued.
## N-262 schema-documentation regression boundary (2026-10-06)

No runtime schema regression was observed: SQL Server reports the applied head,
role column, index and CHECK constraint. The regression is contract visibility:
the canonical data dictionary omits the objects that govern role filtering.
Documentation parity remains unverified until the source-of-truth files are
updated and checked.
## N-263 role regression coverage boundary (2026-10-06)

The current focused role tests remain green, but they do not regress the live
failure because their expected semantics allow NULL-target global visibility and
do not inspect CTA route ownership. No false pass is promoted to N-261.
## N-264 cross-user regression boundary (2026-10-06)

The negative Student1 replay did not expose the Admin-review notification and
rejected ineligible role filters. The remaining regression is isolated to
multi-role users receiving NULL-target rows in incompatible role views.
## N-265 Browser route-guard regression boundary (2026-10-06)

Fresh Edge navigation of the Admin review target from an Instructor-only
session produced the expected access warning and returned to the Instructor
dashboard. This confirms downstream route containment, but it does not repair
the upstream N-261 role-view/CTA defect. No business mutation or notification
state change occurred.
