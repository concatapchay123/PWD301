# 06_NOTIFICATION_TEST_MATRIX

## Executed lesson-flag matrix (fresh SQL Server fixture, 2026-10-05)

| Test ID | Module | Role | Action | Input | API Result | Expected Notification | Actual Notification | DB Result | Status |
|---|---|---|---|---|---|---|---|---|---|
| B-056 / N-125 | Course review | Admin | Confirm flag prompt | Empty reason | No prompt request completed | Local reason validation; retain prompt | Vietnamese minimum-5 warning toast | No flag/audit/event/notice | PASS rejection; inline UX gap |
| B-057 / N-126 | Course review | Admin → owner | Confirm valid flag in Browser | Valid reason, CS301 lesson | Web POST 500 INTERNAL_ERROR | Durable moderation then truthful success + owner notice | English system error toast; no success | No durable mutation or notice | CONFIRMED FAIL Browser + SQL |
| B-058 / N-126 | Course review | Admin → owner | REST valid flag | Valid object/reason | JWT POST 500 INTERNAL_ERROR | HTTP 200 with durable flag/audit/notice | English response; Browser not used for REST case | No durable mutation or notice | CONFIRMED FAIL HTTP + SQL |
| B-059 / N-127 | Course review | Admin | REST wrong type | JSON string | 500 INTERNAL_ERROR | 400 VALIDATION_ERROR | Generic English response | Unchanged | CONFIRMED FAIL |
| B-060 / N-128 | Course review | Admin | REST wrong type | JSON nonempty list | 500 INTERNAL_ERROR | 400 VALIDATION_ERROR | Generic English response | Unchanged | CONFIRMED FAIL |
| B-061 / N-129 | Course review | Guest | Flag without token | Valid reason | 401 UNAUTHORIZED | Safe login guidance | English auth response; UI NOT RUN | Unchanged | PASS auth boundary |
| B-062 / N-130 | Course review | Instructor2 | Attempt Admin flag | Valid reason | 403 FORBIDDEN | Safe permission denial | English role response; UI NOT RUN | Unchanged | PASS role boundary |
| B-063 / N-131 | Course review | Student4 | Attempt Admin flag | Valid reason | 403 FORBIDDEN | Safe permission denial | English role response; UI NOT RUN | Unchanged | PASS role boundary |
| B-064 / N-132 | Course review | Admin | Direct empty input | Empty reason | 400 VALIDATION_ERROR | Vietnamese minimum-5 rejection | Matching server reason | Unchanged | PASS server validation |
| B-065 / N-133 | Course review | Admin | Below minimum | abcd | 400 VALIDATION_ERROR | Vietnamese minimum-5 rejection | Matching server reason | Unchanged | PASS 4-char boundary; 5-char NOT RUN |
| B-066 / N-134 | Course review | Admin | Missing target | Nonexistent lesson UUID | 404 RESOURCE_NOT_FOUND | Resource-safe failure | Matching Vietnamese response | Unchanged | PASS missing target; mismatch NOT RUN |
| B-067 / N-135 | Course review | Admin | Exact minimum boundary | `abcde` | 500 INTERNAL_ERROR | 200 only after durable success | English system error | Unchanged | CONFIRMED FAIL; exact 5-char boundary |
| B-068 / N-136 | Course review / sub-admin | Admin course-review | Own ROLE_CHANGED notice, CTA, then flag | Browser + exact-5 REST replay | Notice/list PASS; flag 500 | One SQL audit/notice; no flag event | PARTIAL: notice/CTA PASS, allowed flag FAIL |
| B-069 / N-137 | Governance / sub-admin | Admin instructor-review | Own ROLE_CHANGED notice, CTA, then flag | Browser + REST replay | Notice/list PASS; flag 403 | No moderation mutation | PASS scoped denial |
| B-070 / N-138 | Governance / sub-admin | Admin teaching-assignment | Own ROLE_CHANGED notice, CTA, then flag | Browser + REST replay | Notice/list PASS; flag 403 | No moderation mutation | PASS scoped denial |
| B-071 / N-139 | Operations / sub-admin | Admin system-monitoring | Own ROLE_CHANGED notice, CTA, then flag | Browser + REST replay | Notice/list PASS; flag 403 | No moderation mutation | PASS scoped denial |

The table above is the pre-fix matrix. Ten REST cases then reproduced six matches/four failures with zero skips; the historical failure is retained. Browser actions are separate cases, not added to pytest totals. [Evidence](flag-runtime-evidence.md) preserves exact response/correlation and SQL context.

## Post-fix lesson-flag matrix

| Test ID | Module | Role | Action | Input | API Result | Expected Notification | Actual Notification | DB Result | Status |
|---|---|---|---|---|---|---|---|---|---|
| B-072 / N-140 | Course review | Admin → owner | REST valid flag | Valid long reason | 200 success | Durable audit and owner notice before success | Vietnamese success response; notice persisted | Flag/audit/event/notice present | PASS SQL Server |
| B-073 / N-141 | Course review | Admin → owner | Browser exact-minimum flag | `abcde` | Web POST 200 | Durable audit and owner notice | Visible success toast | `lesson_flag`, 1 audit, 1 event, 1 notice | PASS Browser + SQL |
| B-074 / N-142 | Course review | Admin | REST string/list body | Wrong JSON types | 400 VALIDATION_ERROR | No notification | Vietnamese safe validation response | Unchanged | PASS; 0 skipped |
| B-075 / N-143 | Sub-admin scope | Four Admin sub-roles | Own notice list + flag/deny | Fresh SQL REST replay | Notice GET 200; allowed POST 200; three POST 403 | Role-specific notices; no denial mutation | 8/8 expected checks | PASS SQL Server; Browser CTA evidence retained |
| B-076 | Course review transaction | Admin → owner | Force notification failure | `abcde` | 500 fail-closed | No partial success | Safe server failure; no success toast claim | No flag/audit/event/notice after rollback | PASS focused regression |

Post-fix results: flag probe **10/10 expected statuses, 0 failed, 0 skipped, exit 0**; sub-admin probe **8/8 checks, 0 failed, 0 skipped, exit 0**; focused regression **6 passed, 0 failed, 0 skipped**. Duplicate/retry idempotency, cross-course mismatch, outbound email and wider producer matrix remain separate gates.

## Checkpoint kiểm thử không skip và an toàn môi trường (2026-10-05)

Checkpoint này có ưu tiên hơn các số liệu 1572/1578 và các trạng thái lịch sử bên dưới. Lượt chạy ban đầu có 1576 passed, 2 failed, 0 skipped; hai test upload tài nguyên và lease bài thi trả 503. Chạy riêng cho 2 passed; chạy lại toàn nhóm API trước sửa fixture cho 375 passed. Probe có restore marker trên thư mục audit riêng tái hiện đúng cả hai phản hồi MAINTENANCE_MODE_ACTIVE/503. Việc nhóm test dùng chung storage/quarantine/backups với workspace là lỗi cô lập đã được chứng minh; không quy kết chắc chắn nguyên nhân của lượt lỗi ban đầu khi chưa lưu response của lượt đó.

Fixture app nay dùng ba thư mục con riêng trong tmp_path. Regression mới thất bại với các root E:/PWD301/storage, quarantine, backups trước sửa. Sau sửa, probe vẫn giữ marker bên ngoài và 27 test upload/lease/backup/restore/maintenance đạt; không tắt maintenance hay fail-closed. Marker probe đã xóa. Test mới dùng nhầm một route không tồn tại lúc đầu; lỗi harness 404 đó đã sửa, không tính là lỗi sản phẩm.

Cô lập filesystem lộ thêm lỗi rescan: kiểm tra substring “infected” trên toàn đường dẫn nhầm thư mục cha với vùng chứa tệp nhiễm. Regression hiện hữu thất bại hai lần trước sửa; nay so sánh parent đã resolve với get_file_infected_root(), kiểm tra tệp được chuyển, key infected/hash và Student vẫn bị từ chối 403. Focused stress/file/isolation: 27 passed. Lượt split cuối sau sửa cho **1579 passed, 0 failed, 0 skipped**, khớp **1579 tests collected**: root298 + unit632 + API375 + security233 + concurrency13 + E2E12 + integration16. Frontend độc lập: **101 passed, 0 failed, 0 skipped**. Không cộng các lượt focused trùng vào tổng. Đây là kết quả các nhóm chạy đủ, không phải một aggregate verifier được tuyên bố pass; lượt aggregate lịch sử bị stall vẫn không được tính.

SQL-gated integration hiện tại: 16 passed, 0 failed, 0 skipped, gồm migration, ROWVERSION race và hai loại revision trên SQL Server thật. Hai DB migration/race tạm đã xóa, remaining=0. Browser Student4 đã đăng xuất về form login; server audit 5105 dừng; DB grading tạm cũng đã xóa, remaining=0. Không migrate/restart DB/runtime chính; fixture có thể dựng lại bằng prepare.

Audit notification vẫn PARTIAL, không phải release sign-off. Những đoạn dưới nói “chưa sửa”, “pending replay”, “1572 current” là snapshot lịch sử, không được dùng thay checkpoint mới.

## Added non-skipped verification cases

| Case | Real input / expected behavior | Evidence | Status |
|---|---|---|---|
| T-013 | Shared app fixture must use three distinct test-local roots, not runtime directories | New regression RED on workspace roots; GREEN under tmp_path and unrelated marker | PASS; test safety, not Browser acceptance |
| T-014 | External restore marker must not poison a test using a different storage root | Controlled probe: original two API cases return 503 before isolation, then pass alongside operations tests after isolation | PASS: 27 passed; production maintenance tests still enforce 503 |
| T-015 | Ancestor name containing “infected” must not suppress malware-file relocation | Existing rescan test RED twice; exact parent comparison GREEN; destination/key verified, Student still 403 | PASS focused; Browser rescan feedback NOT RUN |

## Latest grading/SQL execution (2026-10-05)

| Case | Input / boundary | Actual result | Status |
|---|---|---|---|
| B-007 manual API/SQL | Pending ESSAY; Student4 tries grade; -1,21,NaN; stale ROWVERSION | Hidden/null before grade; 403,400,400,400,409; valid 18 returns 200/GRADED/RELEASED | PASS API/SQL; Instructor UI has no manual action, so UI workflow remains PARTIAL |
| B-051 first release + unchanged retry | Grade18; refresh ROWVERSION; grade18 again | One ASSESSMENT_GRADED notification, STUDENT recipient, correct attempt CTA | PASS durable SQL + Browser CTA |
| B-052 answer-only regrade + duplicate | A→B current key; old snapshot remains A; one job followed by duplicate trigger | 28/30, one REGRADE history18→28; same job, unchanged history, two total grading notices | PASS SQL/HTTP + Browser change-notice CTA |
| B-053 revision CHECK parity | Expanded change_type values at migration head | RED: old CHECK rejects ANSWER_CHANGE (547); GREEN: c4d5e6f7a8b0 allows canonical values | PASS new migration; no live deployment claim |
| B-054 revision activation/immutability | Used SC and SHORT_ANSWER; clone children; try rewrite old children | RED: trigger51007 rejects new activated children; GREEN: inactive construction works, old edits still rejected51007/51008 | PASS two real SQL Server cases, trigger retained |
| B-055 result ESSAY rendering | Persisted answer and18/20 grade, total28/30 | Browser header28/30 correct, but ESSAY displays0/unanswered/incorrect | CONFIRMED FAIL UI, not skipped |

Completed focused backend command:143 passed,0 failed,0 skipped. Completed integration command with both SQL URLs provisioned:16 passed,0 failed,0 skipped. Final split verification is1579 passed,0 failed,0 skipped; prior1572 totals are historical. Automated pass counts do not close known Browser/notification defects.

## Current continuation corrections (2026-10-05)

- **B-006 capacity boundary:** the stale historical row recorded `16 passed, 1 failed`. The current focused enrollment scope now reports `20 passed, 0 failed`, and completed split pytest verification reports `1572 passed, 0 failed, 0 skipped`; a later aggregate attempt stalled at 49% and is not counted. The current source/test boundary is green; fresh live Student4 → DSA201 Browser/DB notification correlation also passes, while duplicate/capacity and historical OPS401 repair remain separate.
- **B-013 student enrollment notice:** a new red regression proved that notification rows staged after the enrollment commit were lost when the session closed. The service now dispatches before its final commit, and the focused plus full suites pass. A fresh Student4 → DSA201 Browser replay produced ACTIVE enrollment, owner/student UI feedback and two linked SQL Server notifications; the pre-existing live OPS401 event-without-notification rows remain historical persisted evidence.
- **HTTP 500 malformed mutation row:** the historical row records the pre-fix behavior. Current type-guard regressions and the aggregate cover the corrected HTTP 400 behavior; API envelope consistency remains open.
- **B-015 live course-review branches:** Instructor1 submitted CS201 in Browser; Admin saw a live queue count of 1 and approved it; Instructor1 then received `Khóa học CS201 đã được phê duyệt`. SQL Server confirmed CS201 `APPROVED`, approver user 1, one `COURSE_APPROVED` event and one linked notification to the owner. A second live staged update `#60002` was opened in the real review page and rejected with a supplied reason; SQL Server confirmed `REJECTED`, event `140009` (`COURSE_CHANGE_REJECTED`) and linked notification `150082`, and the owner Browser showed the exact reason. Both current approve and reject branches pass; other producer families remain separate gates.

## Post-fix retest of the current dirty worktree (2026-10-04)

| Scope | Command | Result | Interpretation |
|---|---|---|---|
| Notification unit/API/IDOR | `.venv\\Scripts\\pytest.exe tests/unit/test_notification_service.py tests/security/test_notification_idor.py tests/api/test_notification_api.py -q` | **28 passed, 0 failed** | Historical dismiss contract failures no longer reproduce in the current worktree |
| Seed/auth/notification regression | `.venv\\Scripts\\pytest.exe tests/integration/test_seed.py tests/integration/test_demo_seed.py tests/api/test_auth_web.py tests/api/test_notification_api.py tests/unit/test_notification_service.py tests/security/test_notification_idor.py -q` | **53 passed, 0 failed** | Seeded accounts, session auth and notification contract pass this focused scope |
| Live login matrix | Local HTTP session probe for all seven demo accounts | **7/7 HTTP 200** | Correct primary roles returned; Admin reports `is_primary_admin=true` |
| Browser representative roles | Edge form login as Student, Instructor and Admin | **3/3 pass** | Routes rendered as Student dashboard, Instructor dashboard and Admin governance; Admin showed `ADMIN CHÍNH` |
| Split repository pytest verification with disposable SQL gates | Separate root/unit/API/security/concurrency/E2E/integration runs on 2026-10-05 | **1572 passed, 0 failed, 0 skipped** | All collected pytest items were executed by group; both SQL Server integration tests ran and passed; disposable databases were removed after completion |
| Aggregate verifier attempt after scoped media and notification fixes | Same verifier with disposable SQL gates | **STALL at 49%, terminated; not counted as pass** | The split runs above are the authoritative complete test count; no result from the stalled aggregate is treated as a pass |
| Full repository verifier with default environment (prior run) | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\verify.ps1` | **1561 passed, 2 failed, 2 skipped in 1127.89s** | Historical current-worktree run before injecting disposable SQL URLs; the same two lesson-media failures were present |
| Explicit disposable SQL Server gates | Temporary SQL Server database `PWD301_AUDIT_SQL_4A8327A660D1`; both opt-in integration tests | **2 passed in 5.22s** | Migration round-trip and row-version race passed; the disposable database was removed after the run |

These are after-remediation observations against the current dirty worktree. The split runs exercised all 1572 collected pytest items with zero skips and zero failures, but they still do not establish a notification release pass because several notification/browser evidence gates remain incomplete.

## Legend

- `PASS`: directly executed and passed.
- `FAIL`: directly executed and failed.
- `NOT RUN`: no execution in this audit.
- `BLOCKED`: execution requires the missing browser/SQL/credential precondition.
- `STATIC`: source-only evidence, never acceptance evidence.

## Contract and automated matrix

| ID | Area | Scenario | Evidence | Result |
|---|---|---|---|---|
| T-001 | service | create/list own notification | targeted suite | PASS |
| T-002 | service | mark one read | targeted suite | PASS |
| T-003 | service | mark all read | targeted suite | PASS |
| T-004 | service | dismiss status contract | targeted suite | FAIL: `deleted` vs `dismissed` |
| T-005 | API | DELETE dismiss status | targeted suite | FAIL: `deleted` vs `dismissed` |
| T-006 | security | notification IDOR cases | targeted suite | PASS: 7 security tests included |
| T-007 | frontend | node frontend suite | `node --test tests/frontend/*.test.js` | PASS: 101 passed, 0 failed, 0 skipped; includes three red/green regressions for auth/login routes and expired-session navigation; speculative BFCache tests removed |
| T-008 | frontend notification failure state | degraded transport/retry contract | focused Node tests | PASS: `ApiClient` raises `NOTIFICATIONS_UNAVAILABLE`; router renders explicit unavailable state and retry guidance; no background TypeError |
| T-009 | full regression | aggregate pytest | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\verify.ps1` | FAIL: 1546 passed, 17 failed, 2 skipped in 811.82s; two SQL Server integration tests skipped because their URLs were not configured |
| T-010 | SQL Server | migration roundtrip | fresh disposable `PWD301_AUDIT_0A2087F3F619` | PASS: upgrade → downgrade base → upgrade; 1 passed in 4.40s; disposable DB removed |
| T-011 | SQL Server | notification/concurrency runtime | same fresh disposable SQL Server database | PASS: row-version race 1 passed in 1.11s; disposable DB removed |
| T-012 | SQL Server + Browser | corrected Admin seed/queue/decision retest | disposable `PWD301_AUDIT_ADMIN_20261004` | PASS scoped: current seed produced `ADMIN_PRIMARY`; Browser login showed `ADMIN CHÍNH`, queue 1, approve persisted `APPROVED`, reset-fixture request-edit/reject persisted `DRAFT`; disposable DB removed |

## Required browser matrix — current evidence

Latest additional gate B-050: after the auth-route correction, clean sessions used the visible Instructor, Student and Admin quick-demo selectors; all three reached the matching dashboard/governance and role labels. This supersedes the earlier shortcut ambiguity for these three current paths. Sessions were logged out afterward; no business object mutation was submitted.

| ID | Role | Action | Valid path | Invalid/boundary path | Post-condition | Result |
|---|---|---|---|---|---|---|
| B-001 | Student | login and open notification center | center loads own items | wrong password/session expiry | no cross-user data | PARTIAL PASS: login works, but the UI-labelled Student demo account has live roles `STUDENT,INSTRUCTOR` and defaults to Instructor by the canonical primary-role ranking; explicit switch to Học viên is required |
| B-002 | Student | mark one read | unread count decrements | rapid repeated click | one stable state | PARTIAL PASS: clicked unread `Kết quả bài thi...`; badge disappeared and item changed to `Đã đọc` while remaining on the dashboard; live SQL Server row `id=27` then had `read_at=2026-10-04T11:43:08.566000`; rapid repeated path not run |
| B-003 | Student | mark all read | all visible become read | empty list | no false success | PASS: 5 unread -> 0 + success toast |
| B-004 | Student | dismiss notification | item disappears per policy | repeat/refresh/back | status remains consistent | PARTIAL PASS: UI delete + refresh; API status regression remains |
| B-005 | Student | refresh/pagination | same items, no duplicate | rapid refresh/network fail | degraded state/retry | PASS for current refresh/pagination/degraded-state behavior, with rapid-idempotency breadth still open: two consecutive Browser `Làm mới` clicks repopulated the same six visible items with no visible duplicate; page 1/page 2 with `per_page=2` returned two items each with zero ID overlap; current three-role Browser outage simulation rendered explicit retry guidance and recovered the real list after unblocking |
| B-006 | Student | enrollment success | business state ACTIVE + feedback | capacity/prerequisite/duplicate | no success toast on failure | PARTIAL/FAIL boundary: OPS401 valid path showed success toast and appeared in enrolled courses, but `tests/unit/test_enrollment_service.py -q` returned `16 passed, 1 failed`; `test_enroll_student_capacity_limit` expected `EnrollmentCapacityExceededError` for the second student and did not receive it |
| B-007 | Student | assessment grade/regrade | score/result notification | stale/duplicate event | history preserved | PARTIAL: Instructor2 opened DSA201 gradebook through course-management; Browser showed 1 submission at `100 / 100`, and the detail modal contained 2 `SINGLE_CHOICE` questions with no manual-grade/regrade control. Fresh host DB query returned 2 `GRADED` auto-graded attempts, 0 pending grade rows and empty `question_corrections`; `tests/api/test_regrade_api.py -q` passed 4 tests. Manual-grade/regrade notification remains unverified; an earlier pending-ESSAY snapshot is not reproducible |
| B-008 | Student | file rejection | fail-closed file + safe message | pending/quarantine | no download/view | PARTIAL BACKEND ONLY: authenticated multipart `/student/become-instructor` with `invalid.exe` returned HTTP 400 `INVALID_FILE_TYPE` and a safe PDF-only message; focused fail-closed file tests returned `20 passed, 16 deselected`; live DB had 0 `PENDING`/`QUARANTINED`/`REJECTED` assets. Browser file chooser coverage remains environment-blocked |
| B-009 | Student/Instructor | logout and revisit | session revoked | back/refresh/open modal | no private data | PASS scoped for current Instructor1 login → CS201 settings → Escape → logout → Back: real runtime settled at `#/auth`, `currentUser=null`, `_isRouting=false`, with login visible and no visible course/topbar/modal. PARTIAL for exhaustive logout with every overlay still mounted; earlier account-menu click may have backdrop-closed the modal before logout |
| B-010 | Instructor | course/lesson submit | reviewer gets notification | invalid draft/duplicate submit | one request/event | PARTIAL: valid course/unit/lesson path and sender-side `Chờ duyệt` observed; reviewer queue showed 0 |
| B-011 | Instructor | prerequisite request | reviewer receives action and can approve/reject | missing/duplicate prerequisite | no false success | PARTIAL: Instructor1 submission UI did not expose a success/post-condition; corrected host HTTP with a renewed CSRF token created one `PENDING` request (id 1) and one Instructor2 notification/event, while a duplicate POST returned the same pending request. Instructor2 Browser notification center and DSA201 `Chuẩn đầu ra & Học vụ` visibly showed the incoming request with `Phê duyệt`/`Từ chối`; action was left pending, so approve/reject post-condition and resulting notification remain unverified |
| B-012 | Instructor | content/media validation | broken/rejected event | unsupported/too-large file | fail-closed | PARTIAL BACKEND ONLY: authenticated Instructor1 multipart course-image upload with invalid PNG bytes returned HTTP 400 `VALIDATION_ERROR` and the safe message `Choose a PNG, JPEG, or WebP image.`; `tests/test_m4_challenger_media_limits.py -q` returned `77 passed`; Browser chooser remains environment-blocked |
| B-013 | Instructor | student enrollment notice | correct owner recipient | other course isolation | no cross-course leak | PASS for fresh live replay, with historical gap retained: Student4 → DSA201 produced ACTIVE enrollment, two `STUDENT_ENROLLED` events and linked notifications `150083` (Instructor2) / `150084` (Student4); Instructor2 Browser showed the owner notice. Historical OPS401 rows still have four events with zero linked Notification rows and require repair/replay handling |
| B-014 | Instructor | role switch | notification list changes only after server role | rapid switch | no stale FIFO result | PASS: Instructor -> Student route/topbar/toast |
| B-015 | Admin | approve/reject course change | owner sees exact result | reject without reason | state and event match | PASS for current live approve/reject, empty-reason and public-ID branches: CS201 approval, historical requests `#60002/#60003`, and post-fix request `#60004` passed Browser + SQL Server correlation; historical internal-ID rows remain evidence only |
| B-016 | Admin | content flag | owner receives reason/action | duplicate flag | one business event | PARTIAL BACKEND ONLY: authenticated Student POST to the live Admin lesson-flag route returned HTTP 403 `FORBIDDEN`; current Admin primary-role metadata is repaired and Admin endpoints return HTTP 200, but valid flag, duplicate flag and owner notification remain unverified |
| B-017 | Admin | role assignment/suspension | target account changes | unauthorized target/own account | session/token policy holds | PARTIAL BACKEND ONLY: authenticated Student POSTs to live Admin suspend and role-assignment routes both returned HTTP 403 `FORBIDDEN`; current Admin primary-role metadata is repaired, but valid Admin action and suspension/session-revocation post-condition remain unverified |
| B-018 | Admin | broadcast/retry | authorized audience only | invalid role/filter | counts match delivery | PARTIAL PASS: empty title blocked; Admin-only valid broadcast delivered to 1 recipient and matched UI/API/DB (`SYSTEM_BROADCAST`); `/admin/emails/retry-failed` returned HTTP 200 with `retried_count=0`; other audiences and failed-email delivery not run |
| B-019 | Any | language/display | Vietnamese catalog copy | raw backend error | no technical leakage | FAIL OBSERVED: English RBAC error and IP-like security value |
| B-020 | Any | toast/modal accessibility | close/Esc/keyboard/readability | multiple competing notices | one primary feedback | PARTIAL/FAIL ACCESSIBILITY: fresh Student DSA201 center exposed named `Tất cả`, `Chưa đọc`, `Khảo thí`, `Khóa học`, `Hệ thống`; `Tab` cycled `Tất cả` -> `Chưa đọc` -> `Tất cả`, skipping the three category filters. `Escape` closed the center; broader screen-reader coverage remains open |
| B-021 | Admin | rapid broadcast double-click | one idempotent outcome | retry after timeout | no duplicate feedback or rows | FAIL CONFIRMED: two success toasts; API exposed one item but direct SQL Server showed 2 notification rows and 2 distinct event IDs for the same title. Source trace confirms no request idempotency key, fresh random event per request and only `(event_id, recipient)` uniqueness; read-time title/body dedupe masks persistence. Timeout/retry path not run |
| B-022 | Any | API direct contract | stable envelope/code | 401/403/404/409/422/500 | no raw exception | PARTIAL/FAIL contract: notification 401/403/404/405/400 paths were exercised, assessment-submit returned 409 `SUBMISSION_CONFLICT`, and the historical malformed notification mutation payloads returned 500 `INTERNAL_ERROR`; current live malformed broadcast/mark-all/preferences probes now return 400 `VALIDATION_ERROR`, but canonical envelope and notification-specific 409/422/429/5xx breadth remain open |
| B-023 | Admin | system/security filter | category shows intended notices | sensitive telemetry in body | authorized safe detail | FAIL/REVIEW: raw IP-like value visible |
| B-024 | Student | catalog search | search `OPS401` returns matching course/recommendation | empty/non-matching query | no false result or stale card | PASS: matching course and recommendation visible |
| B-025 | Student | catalog category filter | category options visible | unsupported/empty category | result count and copy consistent | PARTIAL PASS: Browser keyboard selected `Khoa học Máy tính`; the course grid changed to the explicit empty state `Không tìm thấy khóa học phù hợp`, then `Home` restored `Tất cả danh mục` and the three catalog cards. Unsupported query and empty search boundary remain unverified |
| B-026 | Instructor | create-course empty submit/cancel | required-field warning | partial/invalid form | no record and modal closes on cancel | PASS: validation warning + cancel; no course created |

| ID | Role | Action | Valid path | Invalid/boundary path | Post-condition | Result |
|---|---|---|---|---|---|---|
| B-027 | Instructor | create valid course | success route and persisted management object | duplicate code/rapid submit | one course and one success result | PASS: `AUDIT1004` created; duplicate/rapid path not run |
| B-028 | Instructor | create unit, save lesson draft, publish draft update | validation and draft success feedback | blank unit/invalid content | draft remains editable and bounded | PASS: blank rejected; valid unit and lesson draft saved |
| B-029 | Instructor/Admin | submit course for review then inspect queue | sender sees `Chờ duyệt`; admin sees one queue row | missing reviewer/duplicate submit | approve/reject action and notification | PASS for current live CS201 approve/reject branches and empty-reason guard: Admin saw the real queue, owner notifications and SQL Server post-conditions matched; duplicate submit remains open |
| B-030 | Instructor | load sample exam and publish | confirmation then published toast with 4 questions | publish without acknowledgment | one assessment and stable result | PASS for UI/result; DB/event correlation not captured |
| B-031 | Student | waiting-room pledge and start | attempt route opens | no pledge/fullscreen loss | lease/proctoring state recorded | PARTIAL: start succeeded; fullscreen overlay recorded 1 violation |
| B-032 | Student | answer, autosave, confirm submit, view result | autosave indicators and result page | duplicate submit/stale session | one final attempt/result | PASS: 2/2, 100/100; rapid duplicate not run |
| B-033 | Student | export result PDF | verifiable download | browser print/download failure | file exists and is readable | NOT VERIFIED: result page showed 100/100 and the PDF button; a fresh Browser click timed out during input dispatch and showed no visible toast or download confirmation, so no verifiable download event/file |
| B-034 | Student | course resource download | visible PDF download link and authenticated backend response | browser/client block or quarantined file | file exists and is readable | PARTIAL: backend HTTP 200/application-pdf/1,213 bytes; fresh Browser click on the visible DSA201 link left the lesson page in place and produced no recent local Downloads file |
| B-035 | Student | notification pagination and role query | stable pages and no cross-user leak | role parameter tampering | only own notifications | PARTIAL PASS: page 1/page 2 had zero ID overlap; `role=ADMIN` still returned Student-owned items and did not expose Admin broadcasts, but role parameter semantics are not explicit |
| B-036 | Instructor | course cover upload | enabled file input accepts image and produces safe result | chooser/permission failure | upload state and notification | BLOCKED ENVIRONMENT: input was present and enabled, but Edge rejected `fileChooser.setFiles` with `Not allowed`; extension file-URL permission was not changed |
| B-037 | Student | result scale / pending appeal alert | shared dialog opens with readable result/action | branch unavailable or helper drift | one modal/error, no uncaught exception | STATIC GAP: `student.js:5722,5830` calls missing `UI.alert`; the fresh result page exposed score/appeal controls but not the scale or pending-appeal trigger, so Browser runtime behavior remains unverified |
| B-038 | Admin | notification API category/status/pagination boundary | filtered items and counters match documented semantics | invalid category/role, unread filter, out-of-range page, per-page bounds | stable 200/error contract and no cross-user data | CONFIRMED HTTP: JWT list total 7/unread 4; `SYSTEM=3`, `COURSE=2`, `ASSESSMENT=1`; `unread_only=true` and `status=UNREAD` each returned 4; `per_page=0`→1, `per_page=1000`→100, `page=999`→200 with 0 items. `unread_count` stays global across category filters |
| B-039 | Admin | invalid role/status notification filters | unsupported values rejected or explicitly normalized | `role=STUDENT|INSTRUCTOR|ADMIN`, `status=BOGUS`, `unread_only=maybe` | no misleading success/filter state or cross-user data | CONFIRMED HTTP + SOURCE: all three roles returned the same 7 Admin items; unknown status/unread values were ignored; no cross-user leak observed. Service source explains null-target fallback and exact-value-only status handling |
| B-040 | Any | login rate-limit boundary | 5 failed attempts return auth failure; next attempt is throttled with retry guidance | unique nonexistent email, wrong password | no demo-account lockout or global loopback lockout | PASS: a unique synthetic email returned HTTP 401 on attempts 1-5, then HTTP 429 with `Retry-After: 60`; a subsequent valid Student1 JWT login succeeded; no demo account or business record was targeted by the failed attempts |
| B-041 | Admin | rapid mark-one-read | one state transition and stable unread count | same notification PATCH twice | no duplicate read event or double decrement | PASS scoped: two consecutive PATCH requests for the same already-read notification both returned `is_read=true` with the same `read_at`; unread count remained 2 before and after |
| B-042 | Admin | mandatory SECURITY preference | opt-out is rejected | `SECURITY.email_enabled=false` | no preference mutation and actionable error | PASS: HTTP 400 `VALIDATION_ERROR`, message states that security notifications are mandatory and cannot be disabled |
| B-043 | Admin | notification validation boundaries | required-field failures are explicit | unknown preference category, empty preferences, missing broadcast title/body, unknown mark-all category | no invalid business write | PASS: invalid preference/broadcast inputs returned HTTP 400 with field/category messages; unknown mark-all category returned HTTP 200 with `marked_count=0` and no-op semantics |
| B-044 | Admin | malformed JSON type boundary | malformed payload is rejected as client error | broadcast JSON string, mark-all JSON list, preferences JSON string | no valid notification/read mutation | PASS current producer boundary / historical failure retained: live JWT probes returned HTTP 400 `VALIDATION_ERROR` for broadcast string, mark-all list and preferences string, with no mutation; the earlier 500 observations remain pre-fix evidence and canonical envelope consistency remains open |
| B-045 | Any | notification network failure | degraded state or retry guidance | all notification route attempts reject | no fabricated empty success state | PASS: API/router contract plus Browser verification for Admin, Instructor and Student; each role rendered explicit unavailable/retry state under blocked endpoints and recovered to the real list after retry |

### B-005/B-045 current-state correction

The earlier B-005/B-045 rows preserve the pre-fix VM observation. Current Node and three-role Browser replays prove that failed notification routes no longer become a fabricated empty list: `ApiClient.getNotifications()` raises `NOTIFICATIONS_UNAVAILABLE`, while the router exposes a degraded state with retry guidance and recovers after unblocking.

| B-046 | Student | open graded-result notification CTA | modal then canonical attempt result | legacy assessment-id CTA | result page loads the scored attempt | PARTIAL: Browser reproduced the legacy CTA 404 and direct canonical attempt route rendered the result; source fix plus focused regression now pass, fresh post-fix notification replay remains open |
| B-047 | Student/Instructor | enrollment success notification CTA | role-specific course page | server-path/non-hash CTA | recipient lands in the SPA course view | PASS: Student4 CTA opened the DSA201 Student course detail and Instructor2 CTA opened the DSA201 Instructor management page; SQL action URLs matched the Browser destinations |
| B-048 | Instructor | notification center immediate open after login | skeleton/ready list/legitimate empty state | delayed revalidation or empty cache | no false empty state | PARTIAL Browser / PASS deterministic frontend contract: Browser showed a transient empty state with badge 14, then 14 items after revalidation; the current Node delayed-fetch regression confirms skeleton/loading behavior until the real response, but a fresh Browser timing replay remains open |
| B-049 | Instructor | course-change rejection notification CTA | owner sees safe course identity and reaches course page | internal numeric ID in title/action URL | public UUID and correct course page | PASS after fix: request `#60004` rendered `CS201` without `#70014`; CTA opened the CS201 management page at public UUID `06a1a28d-667a-4d31-b5c9-edefc2885d91`; SQL event `140017` and notification `150090` matched the same public UUID/action URL. Requests `#60002/#60003` remain historical pre-fix evidence |

### Current remediation corrections for B-044 and B-048

### B-005, B-044 and B-045 current-state correction

On `http://localhost:5000`, clean logout/login sessions for Admin, Instructor and Student were each followed by temporary CDP blocking of all notification endpoints. Each role rendered `Không thể tải thông báo`, explanatory retry guidance and `Thử lại`, without `Không có thông báo nào`; after the block was removed, retry restored the real notification list. No business mutation was submitted. B-045 is therefore a Browser PASS for the three representative roles; broader retry/idempotency coverage remains open.

- **B-005:** The same Browser outage run plus the existing two-click refresh/pagination evidence closes the current refresh/degraded-state path; timeout/retry race breadth and duplicate persistence remain open.
- **B-044:** The historical Browser/API observation remains a valid pre-fix record. A focused API regression first reproduced HTTP 500 for a broadcast JSON string and mark-all JSON list; a fresh live JWT probe now returned HTTP 400 `VALIDATION_ERROR` for broadcast string, mark-all list and preferences string. The 1572-item split verification includes the regression, and the canonical error envelope remains a separate open contract item.
- **B-048:** The historical Browser observation remains a valid pre-fix record. A focused Node delayed-fetch regression first reproduced the cached empty-state render; after the router loading-state fix, it rendered the skeleton until a successful response and then rendered the notification. The 101-test frontend suite includes the regression; post-fix delayed live Browser timing replay is not claimed.

### B-011 current-state correction

The earlier `B-011` row is superseded by the continuation evidence: approval request id `1` was completed in Browser and correlated to `APPROVED`, an `OPS401 -> DSA201` prerequisite link, and an Instructor1 `COURSE_PREREQUISITE_APPROVED` notification. A second request id `2` was created in Browser and ended `REJECTED` with a reason and an Instructor1 `COURSE_PREREQUISITE_REJECTED` notification through a fresh CSRF-authenticated session. The Browser rejection prompt opened but could not be completed reliably by the automation session; therefore B-011 remains `PARTIAL` for Browser coverage, while the approve/reject API and business post-conditions are confirmed.

## Fresh direct API probe (2026-10-04)

- JWT Student login returned HTTP 200 with `access_token`, `refresh_token`, `token_type` and `expires_in`; tokens were not written to the report.
- Unauthenticated `GET /api/notifications`, `/unread-count`, `/preferences` and `POST /mark-all-read` returned HTTP 401 with `error.code=UNAUTHORIZED`; the body still lacks canonical `success:false,data:null`.
- Authenticated Student `GET /api/notifications?page=1&per_page=1` returned HTTP 200 with `success=true`, `items`, `total=6`, `unread_count=0`, `page=1`, `per_page=1`; there is no `data` member. `GET /preferences` returned only `preferences` (no `success` or `data`).
- Authenticated Student invalid notification operations returned HTTP 404 `RESOURCE_NOT_FOUND` for read/dismiss/delete; wrong-method GET returned HTTP 405 `METHOD_NOT_ALLOWED`; empty preferences update returned HTTP 400 `VALIDATION_ERROR`. These responses include structured error keys but still omit the canonical outer envelope.
- Student calls to `/api/notifications/broadcast` and `/emails/retry-failed` returned HTTP 403 `FORBIDDEN` without creating a notification. `role=ADMIN` returned 5 items versus 6 for the unfiltered Student query; the returned items remained Student-owned/non-admin content, so role-filter semantics remain ambiguous rather than a proven cross-user leak.
- Web-session boundary differs again: unauthenticated `/auth/notifications` returned HTTP 401, while unauthenticated `/auth/notifications/unread-count` returned HTTP 200 with `success=true,unread_count=0`; `/auth/notifications/preferences` is not a route and returned HTTP 405. This is observable contract drift, not a notification delivery pass.
- Cross-role JWT read-only probe: Student and Instructor demo logins returned HTTP 200 and `/api/v1/auth/me` reported `STUDENT,INSTRUCTOR`; Admin login returned HTTP 200 and reported `STUDENT,INSTRUCTOR,ADMIN`. Notification list totals were Student 6/unread 0, Instructor 5/unread 3 and Admin 7/unread 4, with no token values recorded. This confirms role-specific data exists, but does not prove every producer/recipient business rule.
- Enrollment reproduction update: a rollback-only SQL Server run of the real `enroll_student()` path with commit-simulation (`flush()` + `expire_all()`) for PY301/student3 returned `ACTIVE`, produced 2 `STUDENT_ENROLLED` events with 2 linked notifications in-transaction, emitted no dispatch warning, and then rolled back. The persisted OPS401 rows remain a confirmed live-data gap, but the current failure is not reproducible from this isolated path.
- Capacity RCA update: `enrollment_service.py` reaches the row-lock section and then explicitly documents an unlimited-capacity policy without checking `locked_course.capacity`, while `test_enroll_student_capacity_limit` requires capacity `1` rejection; this is a confirmed service/test contract conflict.
- Fresh direct API duplicate-submit probe: Student1 login returned HTTP 200; replaying the existing GRADED attempt `2c6ef2d5-f15f-4a36-b132-649facecc94f` with its stored idempotency key returned HTTP 200, `is_idempotent_replay=true`, and no new submission; a different UUID returned HTTP 409 `SUBMISSION_CONFLICT`. This is an assessment boundary proof, not a notification-broadcast idempotency proof.

### B-002 current-state correction

The original B-002 row remains only a single mark-one-read sample. A fresh Student-view Browser session for the dual-role Instructor2 account showed 4 unread items; one `Đã đọc tất cả` click changed the badge to 0 and displayed the success toast. A Browser double-click attempt hit a detached DOM node before a second UI request could be established. Two immediate JWT mark-all POSTs then both returned `success=true, marked_count=0`, proving a scoped repeated no-op at the API boundary but not Browser rapid-click behavior.

## HTTP status and response coverage

| Status | Evidence in this audit | Result |
|---:|---|---|
| 200 | targeted notification API tests; browser mark-all/delete/filter outcomes; CDP captures of `/auth/notifications?role=STUDENT|INSTRUCTOR|ADMIN`; Admin email retry returned `retried_count=0` | PARTIAL PASS: role GETs and retry authorization return 200 but payload/event identity is inconsistent and delivery had no eligible record |
| 201 | no notification-specific create endpoint exercised in browser | NOT RUN |
| 204 | no notification endpoint returned/verified 204 in current scope | NOT RUN |
| 400 | authenticated Admin broadcast with body but missing title returned `VALIDATION_ERROR` and `Field 'title' is required.` | PASS validation semantics; envelope incomplete |
| 401 | fresh unauthenticated `/api/notifications`, `/api/notifications/unread-count` and `/auth/notifications?role=STUDENT` probes | PASS auth gate; bodies contain only `error` and omit canonical `success:false,data:null` |
| 403 | fresh Student session requested `/admin/courses/pending` | CONFIRMED permission gate; body contains `error` with `FORBIDDEN` and still omits canonical envelope |
| 404 | JWT Student POST to `/api/notifications/not-a-real-id/read` and `/dismiss` returned `RESOURCE_NOT_FOUND`; unknown GET method returned 405 | PASS for resource-not-found semantics; canonical envelope still incomplete |
| 409 | duplicate assessment submit with different idempotency key returned `SUBMISSION_CONFLICT` | PASS for assessment boundary; notification-specific 409 not run |
| 422 | notification validation path not run at API layer | NOT RUN |
| 429 | six failed login attempts for one unique synthetic email | PASS: attempts 1-5 returned HTTP 401; attempt 6 returned HTTP 429 with `Retry-After: 60`; loopback IP is trusted and demo accounts were not targeted |
| 500 | malformed authenticated broadcast/mark-all JSON types | PARTIAL/FAIL: both returned HTTP 500 `INTERNAL_ERROR` with correlation IDs; deliberate server-error injection remains NOT RUN |
| 502/503 | upstream/service outage simulation not run | NOT RUN |

## Async, race and ownership coverage

| Scenario | Result |
|---|---|
| double click / rapid mark-all | PARTIAL: Browser double-click hit a detached DOM node before a second request was proven; two immediate JWT mark-all calls returned `success=true, marked_count=0` |
| duplicate delete/retry | NOT RUN; one delete + refresh was run |
| timeout/cancel/out-of-order response | NOT RUN |
| optimistic removal rollback | STATIC finding: router removes before/around API and catch only warns; browser failure injection not run |
| one notification owner | FAIL STATIC: router, view, API catch and native alert paths coexist |

## B-021 current correction - Admin broadcast retry idempotency

The historical B-021 row remains valid as a before-fix failure. After a RED regression, the shared broadcast service and Admin modal now use one UUID `X-Idempotency-Key` per business submission. Exact replays return the original count with `idempotent_replay=true`; changed payloads return 409; the submit button is disabled while in flight. The disposable Browser double-click produced one success toast and one server POST, and SQL Server showed one event with seven recipient rows. A separate concurrent two-client HTTP replay returned first-send/replay markers and the same one-event/seven-recipient SQL result. The scoped Admin broadcast duplicate gate is **PASS**; other notification producers remain separately assessed.

## Latest no-skip verification checkpoint (2026-10-05)

The current dirty worktree was rerun in non-overlapping partitions: root **298**, unit **632**, API **381**, security/concurrency/e2e **258** (233 + 13 + 12), and real SQL Server integration **16**. Total: **1585 passed, 0 failed, 0 skipped**; collection reported **1585 tests**. The frontend Node suite separately reported **101 pass, 0 fail, 0 skipped, todo 0**. The scoped lesson-flag TDD, disposable SQL Server and sub-admin replays also reported zero skipped cases. This closes the test-execution skip gate for this checkpoint, while the notification business/contract rows below remain independently graded.

## B-022 current correction - shared REST mutation type guards

The historical 500 observations remain traceability evidence. A new RED test reproduced HTTP 500 for list payloads on the shared `/api/notifications/broadcast` and `/api/notifications/emails/retry-failed` routes. After the object guards, focused API tests passed and live disposable SQL Server HTTP returned `400 VALIDATION_ERROR` for both malformed payloads. The valid shared REST broadcast replay returned `200/200` with first-send/replay markers and one SQL event plus seven recipient rows. The shared validation boundary is **PASS**; canonical envelope consistency remains a separate contract gate.

## Latest full verification after idempotency and worker-isolation fixes (2026-10-05)

The current split is now **1586 passed, 0 failed, 0 skipped**: root **298**, unit **632**, API **382**, security/concurrency/e2e **258**, and real SQL Server integration **16**; collection also reports **1586 tests**. Frontend remains **101 pass, 0 fail, 0 skipped, todo 0**. The root partition first exposed a SQLite teardown lock from a test FILE_SCAN worker; the focused test reproduced the hang, and the testing-only enqueue guard now leaves the job queued for an external worker. The rerun completed 298/298. This is a test-harness isolation correction, not a claim that production workers are disabled.

## Latest canonical envelope checkpoint (2026-10-05)

The RED contract test reproduced missing `success`/`data` keys on scoped notification list, count, read, mark-all and dismiss responses. The notification handlers now return `success=true,data=...`; scoped errors return `success=false,data=null,error=...`, while compatibility fields remain during client migration. Focused notification API tests passed **12**, Admin broadcast **1**, notification IDOR **7**, and the full API partition passed **383**. The complete non-overlapping current split is **1587 passed, 0 failed, 0 skipped**: root **298**, unit **632**, API **383**, security/concurrency/e2e **258**, and real SQL Server integration **16**; collection also reports **1587 tests**. Frontend remains **101 pass, 0 fail, 0 skipped, todo 0**. This closes the scoped notification envelope gate; broader API/web-auth envelope drift and the remaining Browser/email/file gates stay open.

## B-023 - email outbox retry and recipient boundary (2026-10-05)

| Test ID | Role | Action | Input | API Result | Expected Notification | Actual Notification | DB Result | Status |
|---|---|---|---|---|---|---|---|---|
| B-023 | Admin → Student4 | retry a failed email and process the queue | one disposable `FAILED` delivery, Admin JWT, real `smtplib` loopback SMTP sink | `POST /api/admin/emails/retry-failed` returned `200`, `success=true`, `data.retried_count=1` | retry is accepted only for failed rows; delivery becomes sent to the stored recipient | Queue transitioned `FAILED → PENDING → SENT`; loopback SMTP captured recipient `student4@pwd301.local` and subject `PWD301 audit email` | one delivery, no duplicate; audit DB removed afterward | PASS local wire/outbox/retry; approved external provider/inbox OPEN |

The probe also forced one transport failure before retry, so the positive result was not inferred from a pre-existing row. The loopback sink exercised SMTP protocol delivery without sending to the Internet; approved provider and inbox receipt remain unclaimed.

## B-077/B-078 - Browser file I/O continuation (2026-10-05)

| Test ID | Role | Action | Input | API Result | Expected Notification | Actual Notification | DB Result | Status |
|---|---|---|---|---|---|---|---|---|
| B-077 | Instructor1 | upload CS201 cover image | visible `#course-thumbnail-input`, PNG allowlist | no request reached because file chooser was unavailable | no success until file and server response exist | no toast; `fileChooser.setFiles` returned `Not allowed`; direct click opened no chooser | unchanged | BLOCKED ENVIRONMENT |
| B-078 | Student4 | download DSA201 PDF resource | visible authorized `Tải về` link | authenticated HTTP replay returned `200` with PDF headers/body; Browser click still did not finalize | readable PDF file or explicit failure/retry | Browser Downloads contained `.crdownload` at 1169 bytes after 5 seconds; direct session had `Content-Length: 1169`, `%PDF-1.4` and `%%EOF` | no mutation | BACKEND PASS / BROWSER PARTIAL |

B-077 is a Browser permission gate, not a backend validation result. B-078's `.crdownload` bytes begin with `%PDF-1.4` and contain `%%EOF`, but stream completion/Browser finalization is still not proven, so it cannot be marked PASS.

Current B-078 continuation: the authenticated direct response also returned `Content-Disposition: attachment; filename=Tong_hop_Do_phuc_tap_Thuat_toan_BigO.pdf` and `Content-Length: 1169`. The application/file authorization and response stream are therefore evidenced as complete; only Edge's final rename/acceptance is open.

## B-026 - Student result alert argument contract (2026-10-05)

| Test ID | Role | Action | Input | API Result | Expected Notification | Actual Notification | DB Result | Status |
|---|---|---|---|---|---|---|---|---|
| B-026 | Student | open appeal/scale alert helper | caller title followed by multiline body | no API mutation; shared helper only | title remains heading; body is escaped and readable | RED captured swapped title; GREEN after `UI.alert(title,message)` correction | unchanged | PASS Node regression; Browser trigger OPEN |

The shared modal owner remains `UI.openModal`; no second toast/modal owner was introduced.

## Browser precondition

The local browser was opened and demo login was explicitly authorized and executed for Student, Instructor and Admin. Therefore the earlier “login not performed” gate is retired. Remaining `NOT RUN`, `PARTIAL`, `FAIL` and `UNVERIFIED` rows are still not acceptance passes; disposable SQL Server migration/concurrency gates and corrected disposable Admin approve/request-edit-reject paths pass, but the live Admin authorization repair, API/DB correlation breadth, duplicate/rapid paths, upload/download and email delivery remain open.

## B-079 - Admin security notification telemetry boundary (2026-10-05)

| Test ID | Role | Action | Input | API Result | Expected Notification | Actual Notification | DB Result | Status |
|---|---|---|---|---|---|---|---|---|
| B-079 | Admin | open System notifications after login | seeded `SYSTEM_SECURITY_ALERT` | no mutation; notification center loaded successfully | actionable Vietnamese security copy without raw IP/path telemetry | RED Browser showed `192.168.1.105`; after the seed/data correction, reload showed `Phát hiện hoạt động đăng nhập quản trị bất thường...` and no raw IP | live SQL Server row 20002 updated; zero matching raw-IP rows remain | PASS after remediation; dynamic producer coverage OPEN |

## Latest complete no-skip verification (2026-10-05)

Non-overlapping partitions after the security-copy correction report **1,588 passed, 0 failed, 0 skipped**: top-level 298, unit 632, API 383, security/concurrency/e2e 258, and integration 17. The two opt-in SQL Server databases were provisioned by the disposable gate helper, both SQL tests ran, and both databases were removed with `audit_database_remaining=0`. This is the current split evidence; the historical aggregate verifier stall remains excluded.

## B-080 - live manual ESSAY grading and result contract (2026-10-05)

| ID | Role / surface | Action | Expected | Observed evidence | Result |
|---|---|---|---|---|---|
| B-080 | Instructor / Bảng điểm & Bài nộp | Open a pending ESSAY submission, enter `3.5`, provide a reason, save and reopen | One server-authoritative grade, success feedback, refreshed score and retained reason | Browser showed the pending row and ESSAY answer, rendered the score/reason controls, showed `Đã lưu điểm tự luận và cập nhật kết quả.`, then reopened at `3.5 / 20` and `3.5 / 4`; SQL Server showed `GRADED`, `MANUAL_GRADED`, `awarded_points=3.5` and the reason | PASS scoped Browser + API + SQL Server |
| B-080a | Student / result detail renderer | Open an answered/manual-graded ESSAY result | Show essay text, awarded points, manual status and feedback; do not show A-D choice labels or invented zero | Student Browser opened the existing released result and visibly showed the ESSAY answer, `4 / 4 đ`, `Nhận xét chấm: ...`, `Đã đạt điểm tối đa`; no A/B/C/D labels appeared | PASS Browser + API-rendered result |

The Instructor fixture attempt was deleted after verification. SQL cleanup reported zero remaining targeted attempts and zero orphan attempt questions, answers, grades, grade history, result history or results. The current no-skip split remains **1,588 passed, 0 failed, 0 skipped** and the frontend suite is **105 passed, 0 failed, 0 skipped**. B-080 closes the scoped manual-ESSAY Instructor/API/DB and Student result-view Browser paths; it does not close Browser file chooser/download, external SMTP, or complete producer/role coverage.

## Latest dismiss contract correction (2026-10-05)

| Scope | Expected contract | Current evidence | Status |
|---|---|---|---|
| Unit + API dismiss/delete | Soft-dismiss excludes the item and returns `status=dismissed` | Current service sets `expires_at`; `tests/unit/test_notification_service.py` + `tests/api/test_notification_api.py`: **25 passed, 0 failed, 0 skipped** | **PASS service/API; Browser result is covered by B-050c below** |

## B-050c - Admin single-item soft-dismiss Browser replay (2026-10-05)

| ID | Role | Action | Expected | Observed evidence | Result |
|---|---|---|---|---|---|
| B-050c | Admin | Click the exact `delete` control for disposable fixture `AUDIT_DISMISS_FIXTURE_601B33526EBB` | Item disappears from the center, success feedback is shown, and the DB row is retained as a soft-dismiss | Browser removed the fixture and showed `Đã xóa thông báo.`; SQL Server retained public id `3697da94-27a4-472e-b970-d7078e047c5a` with unchanged title, non-null `expires_at=2026-10-05 14:50:30.184000` and `read_at=NULL`; Admin then logged out | **PASS scoped Browser + API path + SQL Server**; bulk, rapid retry and non-Admin coverage remain open |

## B-050d - Student authorized PDF download finalization (2026-10-05)

| ID | Role | Action | Expected | Observed evidence | Result |
|---|---|---|---|---|---|
| B-050d | Student | Open DSA201 resource `Tong_hop_Do_phuc_tap_Thuat_toan_BigO.pdf` and click `Tải về` | Browser finalizes the authorized file, with no stale partial download | A readable same-name file exists at 1,169 bytes, begins `%PDF-1.4` and ends with `%%EOF`; because it pre-existed, fresh finalization by this click is not proven | **PASS file integrity only / Browser transfer PARTIAL**; upload/file-selection, quarantine-access and fresh stream breadth remain open |

## B-050e - Student rapid mark-all idempotent state (2026-10-05)

| ID | Role | Action | Expected | Observed evidence | Result |
|---|---|---|---|---|---|
| B-050e | Student | Double-click the exact `Đã đọc tất cả` control with one disposable unread fixture | All visible unread items become read, one user-facing success result is shown, and no duplicate business rows are created | Browser settled at `Chưa đọc (0)`, retained the fixture as read, and rendered one `Đã đánh dấu tất cả thông báo là đã đọc.` toast. SQL Server showed one fixture notification row, one event id and one `read_at`; cleanup returned zero targeted rows | **PASS scoped Browser + SQL Server**; timeout/out-of-order, dismiss/delete and complete producer/role breadth remain open |

## B-050g - Student fresh-resource download stream (2026-10-05)

| ID | Role | Action | Expected | Observed evidence | Result |
|---|---|---|---|---|---|
| B-050g | Student | Download DSA201 resource `Cau_truc_Heap_va_Priority_Queue.pdf` | A new readable PDF replaces the temporary partial file | Edge emitted a download event; `.crdownload` stayed at 1,145 bytes through the first 20-second observation, then the final `Cau_truc_Heap_va_Priority_Queue.pdf` appeared at 1,145 bytes with `%PDF-1.4` and `%%EOF`; no partial remained | **PASS after delayed Browser completion**; timing/feedback and other file producers remain open |

## B-050i - REST role-filter validation correction (2026-10-05)

| ID | Role | Action | Expected | Observed evidence | Result |
|---|---|---|---|---|---|
| B-050i | Student | Call notification list, unread-count and mark-all-read with `role`/`target_role=ADMIN` and `BOGUS`; replay valid `student` | Unsupported or actor-ineligible values return HTTP `400`, `success=false`, `data=null`, `error.code=VALIDATION_ERROR`; valid actor role remains `200` | RED parametrized regression first returned `200` for both invalid values; GREEN normalized/validated all three routes and returned the canonical `400` envelope; valid lower-case `student` remained `200` | **PASS focused API contract**; no schema/data change; broader producer/role coverage remains open |

Current role-filter correction evidence: RED **2 failed**, GREEN **2 passed**, notification API/service/IDOR scope **34 passed, 0 failed, 0 skipped**, and current pytest collection **1,591 tests, exit 0**. The new two-case parametrized regression explains the increase from the prior full-run checkpoint of 1,589. This row does not claim Browser coverage for invalid filter values or close external email/retry gates.

## Latest complete no-skip verification after role-filter correction (2026-10-05)

The refreshed non-overlapping partitions completed on the current source with **1,591 passed, 0 failed, 0 skipped**: root **298**, unit **633**, API **385**, security/concurrency/e2e **258**, and real SQL Server integration **17**. `pytest --collect-only -q` reported **1,591 tests collected**. The frontend Node suite separately completed with **105 passed, 0 failed, 0 skipped, todo 0**. The two SQL Server gate databases were removed with `audit_database_remaining=0`. This is the execution checkpoint only; the notification audit remains PARTIAL because Browser file selection/quarantine, external SMTP/inbox and broader producer/role/retry gates remain open.

## B-050f - Instructor upload permission blocker replay (2026-10-05)

| ID | Role | Action | Expected | Observed evidence | Result |
|---|---|---|---|---|---|
| B-050f | Instructor | Open CS201 cover upload and choose disposable invalid fixture | Browser accepts the chooser so server-side file validation can be exercised | Edge `fileChooser.setFiles` returned `Not allowed`; input remained empty (`files=null`, `value=''`), no upload request or DB mutation was observed, and the session logged out | **BLOCKED ENVIRONMENT**; not counted as product pass |

Fresh CUA continuation: clicking both visible CS201 upload controls through the native accessibility path did not open a file-picker window. The file input remained unselected and no HTTP/DB mutation occurred. This is repeated environment evidence for B-050f, not a product PASS.

## B-033a - Student result PDF export replay (2026-10-05)

| ID | Role | Action | Expected | Observed evidence | Result |
|---|---|---|---|---|---|
| B-033a | Student1 | Click `Xuất bảng điểm (PDF)` on the scored result | A finalized readable PDF or explicit print/download completion feedback | Result page visibly rendered attempt `db76cdce-bef6-470d-be11-7d35cc9ab96b`; source action invokes `window.print()` at `student.js:5375`. Semantic click timed out during input dispatch; coordinate retry left the page/tree unchanged. No new tab, toast, download event or new Downloads file was observed | **NOT VERIFIED**; print-dialog/browser boundary remains open |

The Downloads inspection found only earlier resource PDFs (`1145` and `1169` bytes), not a new result export. This is stronger current Browser evidence for the existing B-033 gap, not a PDF-export PASS.

## B-050b - dynamic SECURITY notification telemetry redaction (2026-10-05)

| ID | Role / surface | Action | Expected | Observed evidence | Result |
|---|---|---|---|---|---|
| B-050b | Any / SECURITY notification service | Dispatch SECURITY title, body and CTA URL containing an IPv4 | No raw network telemetry in user-facing fields; event remains actionable | RED first preserved the IP in all three fields; GREEN returned `[REDACTED]` in title/body/action URL. Current full split: **1,589 passed, 0 failed, 0 skipped**; SQL gates: **17 passed**, cleanup `0` | **PASS shared dispatch boundary**; complete producer catalog and external email remain open |

## B-050a - current Admin mark-all role-scope replay (2026-10-05)

| ID | Role | Action | Initial UI | API/UI outcome | SQL Server post-condition | Status |
|---|---|---|---|---|---|---|
| B-050a | Admin | `Đã đọc tất cả` in notification center | Badge `2`; unread filter `Chưa đọc (2)` | Items remained visible; badge and unread filter changed to `0` | Active Admin view (`target_role='ADMIN'` or `NULL`) for `admin@pwd301.local`: `total=20`, `unread=0`, `read=20` | **PASS scoped**; rapid Browser double-dispatch and dismiss/delete remain separate |
## B-033b - Student result PDF download after remediation (2026-10-05)

| ID | Role | Action | Expected | Observed evidence | Result |
|---|---|---|---|---|---|
| B-033b | Student1 | Click the released-result `Xuáº¥t báº£ng Ä‘iá»ƒm (PDF)` link | A finalized readable PDF downloads without opening the print dialog | Browser rendered a real link with `ID=download-student-result-pdf-btn` and `/student/attempt/db76cdce-bef6-470d-be11-7d35cc9ab96b/result.pdf`; Edge created `CS101-bang-diem.pdf` at 1,713 bytes; `%PDF-`, `%%EOF`, one `pypdf` page and `Score: 1.00 / 16.00` were verified | **PASS scoped**; hidden-score API test returns `403`; other file producers remain open |

The earlier B-033a observation is retained for traceability. B-033b is the post-fix acceptance result and supersedes the old print-only outcome for the Student released-result path.

## B-050j - policy-hidden ESSAY result label correction (2026-10-06)

| ID | Role | Action | Expected | Observed evidence | Result |
|---|---|---|---|---|---|
| B-050j | Student | Open a released manual-graded ESSAY result before `close_at` under `AFTER_CLOSE` answer visibility | The answer remains hidden, but the UI says it is hidden by policy rather than claiming no answer was submitted | RED source regression failed; GREEN source regression passed with `answer_visibility_policy` and `Câu trả lời đang được ẩn theo chính sách khảo thí`. Answer-visibility security and mixed-grading API tests passed; full frontend is **107 passed, 0 failed, 0 skipped** | **SOURCE/API PASS; Browser visual acceptance PENDING** because the CUA Browser inventory returned `browsers=[]`; no bypass or fabricated Browser result was used |

## B-050k - Student result fabricated-metadata correction (2026-10-06)

| ID | Role | Action | Expected | Observed evidence | Result |
|---|---|---|---|---|---|
| B-050k | Student | Open a released result whose API omits signature, instructor or duration metadata | The UI renders API values or explicit unknown state; it must not show a fixed hash or invented defaults | RED source regression detected `7f8a92b1...10243`, `ThS. Trần Hoàng Nam` and `data.duration_minutes || 45`; GREEN removed them and added `signature_hash`/unknown-state handling. Full frontend **108 passed, 0 failed, 0 skipped**; Ruff passed | **SOURCE PASS; Browser visual acceptance PENDING** because the CUA Browser inventory returned `browsers=[]` |

## B-050l - lesson-flag idempotency replay (2026-10-06)

| Layer | Case | Result |
|---|---|---|
| API/SQL Server | First keyed flag request | **PASS**: HTTP 200, idempotent_replay=false |
| API/SQL Server | Exact retry with same key and payload | **PASS**: HTTP 200, idempotent_replay=true; no additional durable rows |
| API/SQL Server | Same key with changed reason | **PASS**: HTTP 409, CONFLICT; no additional audit |
| SQL post-condition | Fresh disposable fixture | **PASS**: delta exactly 1 audit, 1 event, 1 notice; **3 cases, 0 failures, 0 skips**; cleanup remaining 0 |
| Browser | Same retry via real UI | **PENDING**: CUA inventory returned no Browser; no Browser pass is claimed |

## B-050m - distinct event visibility (2026-10-06)

| Layer | Case | Result |
|---|---|---|
| API/service | Two different event types with identical title/body | **PASS**: both durable notifications are returned; total and unread count are not silently collapsed |
| Regression | Existing repeated-copy coverage | **PASS**: notification/flag scope **37 passed, 0 failed, 0 skipped** |
| Static | Ruff and diff check | **PASS** |
| Browser | Notification center with same-copy events | **PENDING**: CUA inventory returned no Browser; no visual pass is claimed |
| SQL Server HTTP | Fresh disposable same-copy event replay | **PASS**: 2 SQL rows, 2 REST items, event types COURSE_ANNOUNCEMENT/SYSTEM_NOTICE; **1 case, 0 failed, 0 skipped**; cleanup remaining 0 |
## B-050n - generic event-key conflict (2026-10-06)

| Layer | Case | Result |
|---|---|---|
| Unit/service | Same key, identical semantics | **PASS**: existing event is returned |
| Unit/service | Same key, changed event type/payload | **PASS**: ConflictError; no new event |
| SQL Server | Same-copy visibility plus event-key conflict | **PASS**: 2 cases, 0 failed, 0 skipped; exact cleanup remaining 0 |
## B-050o - SQL Server demo-seed idempotency (2026-10-06)

| Layer | Case | Result |
|---|---|---|
| SQL Server | Second seed_demo run | **PASS**: no created entities, notifications_created=0, audit_events_created=0 |
| SQL Server | Count post-condition | **PASS**: 7 users, 4 courses, 7 questions, 3 attempts, 1 resource, 22 notifications and 13 audits unchanged |
| Cleanup | Disposable database | **PASS**: 1 case, 0 failed, 0 skipped; audit_database_remaining=0 |

## B-050p - shared dispatch event-key replay

| Layer | Case | Result |
|---|---|---|
| Unit/service | `dispatch_notification()` accepts a UUID event key | **PASS**: RED TypeError reproduced before the change; GREEN forwards the key |
| Unit/service | Exact retry with same event key and payload | **PASS**: one `NotificationEvent` and one recipient `Notification` row |
| Regression | Focused notification/flag scope | **PASS**: 39 passed, 0 failed, 0 skipped |
| Static | Ruff, Python compile and diff check | **PASS**; diff check emitted only existing LF-to-CRLF warnings |
| Browser/producer breadth | All producer adoption and visual rapid retry | **PENDING**: no CUA Browser is available; no broader pass is claimed |

## B-050q - keyed dispatch semantic conflict and outbox replay

| Layer | Case | Result |
|---|---|---|
| Unit/service | Exact keyed retry with forced email | **PASS**: one event, one in-app notification and one `EmailDelivery` row |
| Unit/service | Same key with changed body | **PASS**: `ConflictError`; no second event, notification or email outbox row |
| Regression | Focused notification/flag scope | **PASS**: 39 passed, 0 failed, 0 skipped |
| Producer inventory | Direct `dispatch_notification()` callsites | **OPEN**: AST inventory found 35 unkeyed direct callsites; each needs a business-key decision |
| Browser/external | Visual retry and approved inbox | **PENDING**: CUA has no Browser and approved external SMTP/inbox is unavailable |

## B-050r - enrollment notification key replay

| Layer | Case | Result |
|---|---|---|
| Unit/service | Instructor and Student enrollment notices receive distinct stable keys | **PASS**: UUIDv5 keys differ and use version 5 |
| SQL Server | Real enrollment creates both keyed events | **PASS**: expected keys present; 2 event rows and 2 notification rows |
| SQL Server | Exact replay through shared dispatcher | **PASS**: counts remain `2 -> 2`; **3 cases, 0 failed, 0 skipped** |
| Cleanup | Disposable runtime | **PASS**: database remaining 0 and port 5105 listener count 0 |
| Remaining breadth | Other producers and Browser | **OPEN/PENDING**: 32 direct callsites have neither an explicit key nor a prebuilt event, and no CUA Browser is available |

## B-050s - password security notification key replay

| Layer | Case | Result |
|---|---|---|
| Unit/service | Password mutation key | **PASS**: UUIDv5 uses user ID plus post-change auth version |
| SQL Server | Real password mutation | **PASS**: `auth_version=2`, expected event key and one mandatory security notice/email |
| SQL Server | Exact replay through shared dispatcher | **PASS**: event, notification and email rows remain `1 -> 1`; **3 cases, 0 failed, 0 skipped** |
| Cleanup | Disposable runtime | **PASS**: database remaining 0 and port 5105 listener count 0 |
| Remaining breadth | Other producers and Browser | **OPEN/PENDING**: 30 direct calls have neither explicit key nor prebuilt event; no CUA Browser is available |

## N-162 / F-045 current producer verification (2026-10-06)

| Layer | Case | Result |
|---|---|---|
| Unit/service | Course submission, approval and rejection notification keys | PASS: UUIDv5 uses the persisted audit transition and recipient ID |
| SQL Server | Persisted course approval event | PASS: expected key present; event/notification rows remain 1 -> 1; 4 cases, 0 failed, 0 skipped |
| Regression | Course/notification scope | PASS: 22 selected tests passed; notification API/service scope passed 30 tests |
| Inventory | Direct dispatch calls | OPEN: 35 calls total, 7 explicit keys, 1 prebuilt event, 27 neither |
| Browser/external | Visual retry and inbox receipt | PENDING: CUA inventory has no Browser and approved external SMTP/inbox is unavailable |

## N-166 current producer verification (2026-10-06)

| Layer | Case | Result |
|---|---|---|
| Unit | Role assign/update/revoke keys | PASS: one auth-version-scoped UUIDv5 per mutation |
| Unit | Admin course edit key | PASS: key derived from flushed `COURSE_ADMIN_EDIT` audit |
| API | Course-change submit and approval keys | PASS: recipient-scoped change-request keys persisted |
| Unit | Infected-file rejection key | PASS: rejected revision key persisted |
| SQL Server | Four producer exact replays | OPEN: no dedicated disposable probe in this increment |
| Browser/external | Visual retry and inbox receipt | PENDING: CUA has no Browser and approved external SMTP/inbox is unavailable |

## N-167 complete direct-producer inventory verification (2026-10-06)

| Layer | Case | Result |
|---|---|---|
| Unit | Assessment result notification key | PASS: attempt/result transition key captured |
| Unit/service | YouTube broken-video key source | PASS: deterministic course/lesson/video/recipient key added; focused Ruff/compile pass |
| API | Admin and instructor change-request route keys | PASS: focused change-request/prerequisite group 28 passed |
| Regression | Focused service group | PASS: 79 passed, 0 failed, 0 skipped |
| Inventory | Direct dispatch calls | PASS: 35 total, 34 explicit keys, 1 prebuilt event, 0 neither |
| SQL/Browser/external | Exact replay, visual retry, inbox receipt | OPEN/PENDING: not run or CUA has no Browser |

## N-165 / F-048 current producer verification (2026-10-06)

| Layer | Case | Result |
|---|---|---|
| Unit/service | Account suspension security notice | PASS: UUIDv5 uses user ID plus post-suspension auth_version |
| SQL Server | Exact replay for password, reset-token and suspension security notices | PASS: each event/notification/email set remains 1 -> 1; 9 cases, 0 failed, 0 skipped |
| Inventory | Direct dispatch calls | OPEN: 35 calls total, 11 explicit keys, 1 prebuilt event, 23 neither |
| Browser/external | Visual retry and inbox receipt | PENDING: CUA inventory has no Browser and approved external SMTP/inbox is unavailable |

## N-164 / F-047 current producer verification (2026-10-06)

| Layer | Case | Result |
|---|---|---|
| Unit/service | Password reset token security notice | PASS: expected UUIDv5 key is present after auth_version increments |
| SQL Server | Reset-token exact replay | PASS: disposable probe covered normal and reset-token mutations; event/notification/email rows stayed 1 -> 1, 6 cases, 0 failed, 0 skipped |
| Inventory | Direct dispatch calls | OPEN: 35 calls total, 10 explicit keys, 1 prebuilt event, 24 neither |
| Browser/external | Visual retry and inbox receipt | PENDING: CUA inventory has no Browser and approved external SMTP/inbox is unavailable |

## N-163 / F-046 current producer verification (2026-10-06)

| Layer | Case | Result |
|---|---|---|
| Unit/service | Former and new owner notification keys | PASS: two UUIDv5 keys share the audit transition but differ by recipient |
| SQL Server | Owner reassignment replay | OPEN: no dedicated SQL Server probe in this increment |
| Inventory | Direct dispatch calls | OPEN: 35 calls total, 9 explicit keys, 1 prebuilt event, 25 neither |
| Browser/external | Visual retry and inbox receipt | PENDING: CUA inventory has no Browser and approved external SMTP/inbox is unavailable |

## N-168 full verification (2026-10-06)

| Layer | Case | Result |
|---|---|---|
| Aggregate | Repository contract, static checks, frontend and pytest | PASS: verifier exit 0; **1607 passed, 0 failed, 0 skipped** |
| SQL Server | Migration round-trip, ROWVERSION grading race, immutable revision children | PASS: all 4 SQL Server cases ran on disposable databases; cleanup completed |
| Inventory | Direct dispatch calls | PASS: 35 total, 34 explicit keys, 1 prebuilt event, 0 neither |
| Browser/external | Visual retry, file chooser/quarantine and inbox receipt | PENDING: CUA exposes no Browser and approved external SMTP/inbox evidence is unavailable |

## N-169 live email consumer verification (2026-10-06)

| Layer | Case | Result |
|---|---|---|
| SQL Server | Live outbox/backlog query | PASS evidence: 115 PENDING, oldest 2026-09-19, attempt_count 0; background_jobs 0 |
| Worker | Pending outbox without pre-existing job | PASS: RED then GREEN; `run_worker_once()` creates the deduplicated EMAIL job and processes the row in test transport |
| Transport | Production default without SMTP | PASS: fails closed; configured adapter uses TLS/login/from address; no mock success outside testing |
| Health | Stale pending backlog | PASS: stale queue test and live `/health/deep` return DEGRADED |
| Deployment | Worker service | PASS: Compose declares `worker` and `scripts/run_worker.py`; live service not started because SMTP configuration is absent |

## N-170 current execution boundary (2026-10-06)

| Layer | Current evidence | Result |
|---|---|---|
| Computer Use | `getState()` returned no apps/browsers; `createBrowserTab("iab", ...)` returned `Browser is not available: iab` | BLOCKED ENVIRONMENT; no Browser case is counted as PASS |
| Automated regression | SQL-enabled full verifier | **1612 passed, 0 failed, 0 skipped** |
| Worker image | `docker compose build worker` | PASS; container not started without approved SMTP |
| Live health | `/health/deep` | DEGRADED for 115 stale pending email rows |

## N-171 historical duplicate disposition matrix (2026-10-06)

| Test | Evidence | Result |
|---|---|---|
| Event-key uniqueness | 143 live `notification_events`, repeated-key query returned 0 rows | PASS |
| Event-to-notification integrity | 0 events without a linked notification | PASS |
| Business-key duplicate check | Repeated `change_request_id` query returned 0 groups | PASS for known keyed history |
| Legacy copy grouping | 14 repeated recipient/title/body/role groups; generic action URLs and NULL payloads remain | PARTIAL; no safe deletion decision |
| Live repair | No rows deleted or hidden | SAFETY HOLD; owner approval and disposable rehearsal required |

## N-172 API envelope regression matrix (2026-10-06)

| Case | Expected | Actual | Status |
|---|---|---|---|
| Session list/count | `success=true`, payload under `data` | Canonical `data` plus legacy aliases | PASS |
| Session read/mark-all/dismiss/clear | `success=true`, operation result under `data` | Canonical `data` plus legacy aliases | PASS |
| Student list/read/mark-all | Same canonical success envelope | Canonical `data` plus legacy aliases | PASS |
| Existing frontend contract | Existing top-level fields remain readable | Focused frontend/PDF set: 7 passed | PASS |
| Full post-patch aggregate | All repository and SQL gates | Not rerun after this patch | NOT RUN; prior 1612 count is pre-patch evidence |

## N-173 post-patch aggregate correction (2026-10-06)

The prior N-172 row is superseded by a valid rerun: `scripts/verify.ps1` completed **1613 passed, 0 failed, 0 skipped**, including all four SQL Server opt-in cases and 108 frontend tests. Disposable SQL databases were removed. Browser/CUA, file chooser/quarantine and external inbox rows remain explicitly open.

## N-174 acceptance-scope decision (2026-10-06)

SMTP/inbox test rows are excluded from this acceptance cycle by owner decision because the service is not deployed. Browser/CUA, file chooser and quarantine rows remain required and are not passed by API, SQL or automated-suite evidence alone.

## N-175 Browser test results (2026-10-06)

Student, Instructor and Admin demo login/logout flows passed visibly. Instructor notification mark-all-read changed 15 unread to 0 and rendered a success toast; Admin Operations and Student permission-denial flows also rendered expected UI states. Mixed-language and repeated notification records remain captured as defects/evidence, not marked correct.

## N-176 file test results (2026-10-06)

The clean Student PDF resource download passed. The live database currently contains no PENDING/QUARANTINED revision; the rejected-file navigation was blocked by the Edge client before an application response, and the upload file chooser could not assign a fixture because Edge file-URL access is disabled. Unsafe-file UI cases remain unverified.

## N-177 Student notification test result (2026-10-06)


The Student Browser notification panel passed structural rendering of the zero-unread state and category filters. Content assertions remain open for the observed mixed-language and opaque historical messages; no source owner was inferred from text alone.
## N-178 Browser file test result (2026-10-06)

The clean Instructor course-image upload passed: the file chooser accepted the fixture, the crop/apply workflow completed, and the success toast rendered. SQL Server independently recorded the new current `ACTIVE` revision and `FILE_VALIDATION=PASS` plus `MALWARE=PASS`. The rejected/PENDING/QUARANTINED denial row remains **UNVERIFIED** because Browser returned `ERR_BLOCKED_BY_CLIENT` before the app response; no unsafe fixture was uploaded.
## N-179 rejected-file Browser result (2026-10-06)

The direct and course-scoped inline rejected-file routes both remain **UNVERIFIED** because Edge blocks navigation before the application response. SQL Server confirms the selected historical asset is not attached to a Student-visible lesson resource; no quarantine override or unsafe fixture was used.
## N-180 authenticated rejected-file test result (2026-10-06)

The authenticated Instructor route remains **UNVERIFIED**: the Browser client blocks the rejected-file response before the application can expose its denial status. This is distinct from an authentication or authorization failure.
## N-181 system-category Browser test result (2026-10-06)

The Instructor system-category test passed structurally: the filter rendered two records, the unread count stayed at zero, and closing the dropdown restored the course page. Message-language and historical ownership assertions remain open.
## N-182 assessment-category Browser test result (2026-10-06)

The Instructor assessment-category empty-state test passed: the UI displayed the no-notification message, retained `0` unread, and remained on the course page after closing the dropdown.
## N-183 course-category Browser test result (2026-10-06)

The Instructor course-category test passed structurally: 16 rows rendered, including lifecycle messages and the `#70014` repetition family; closing the dropdown returned to the course page without mutation.

## N-184 Admin broadcast validation test result (2026-10-06)

The Admin Browser validation test passed for the two no-write branches: empty form -> missing-title warning; title-only form -> missing-body warning. The form was canceled, and a read-only SQL Server query inside `pwd301_web` found `143` events, `168` notifications, `115` pending email deliveries and `0` background jobs, with the latest event timestamp before the probe. Valid broadcast delivery is not claimed; SMTP/inbox is out of scope by owner decision.

## N-185 rejected-file Browser test result (2026-10-06)

The read-only SQL Server precondition check found seven rejected revisions with zero lesson-resource links. Consequently the intended Student resource/quarantine test could not be reached with an existing safe fixture. The direct rejected-file URL remains `ERR_BLOCKED_BY_CLIENT` before an app response; this case stays **UNVERIFIED**, not skipped-as-pass.

## N-186 authenticated rejected-file API test result (2026-10-06)

The real Instructor HTTP session test passed the backend fail-closed assertion: the rejected asset returned `403` with `success:false`, `FILE_INFECTED`, and the safe malware-rejection message. No file content was returned. Browser UI rendering remains **UNVERIFIED** because Edge blocks the same direct route before the app response.

## N-187 SMTP/inbox test scope (2026-10-06)

External SMTP and inbox receipt were not run because the owner confirmed the service is not deployed. This is an explicit scope exclusion, not a skipped test counted as a pass.

## N-188 historical duplicate reclassification test (2026-10-06)

The reclassification test passed at the read-only evidence level: 14 groups enumerated; 12 groups had full row-to-business correlation; file mapping was 7/7 unique and 0 ambiguous; 2 groups/17 rows remained unverified. No mutation test ran.

## N-189 Browser quarantine-override validation test (2026-10-06)

The primary-admin security UI test passed at the validation level: the real override dialog rendered all three required fields and rejected an empty submission with `Vui lòng nhập File Asset ID.`. The dialog was canceled; no file release, password submission or audit mutation was tested.

## N-190 focused quarantine backend test (2026-10-06)

Focused backend verification passed: 2 override tests and 1 fail-closed quarantine/infected-file test passed; 45 unrelated tests were deselected. The test matrix still marks the credentialed live release transition as unverified.

## N-191 Browser console check (2026-10-06)

The inspected Browser flows emitted no application-level console error. The only captured warning was the existing Tailwind CDN production warning; no notification test is counted from this observation.

## N-192 legacy identity correlation test (2026-10-06)

The read-only correlation test confirmed the unresolved boundary: 17 rows have no durable business target, no correlation ID, no actor and no matching audit event in their timestamp window. The result is **UNVERIFIED**, not a skipped pass; no mutation test ran.

## N-194 rejected-file Browser denial test (2026-10-06)

The fresh Browser attempt is recorded as **BLOCKED ENVIRONMENT**, not skipped and not passed: Edge rendered its own `ERR_BLOCKED_BY_CLIENT` page before an application response, while IAB was unavailable. The separately authenticated HTTP test remains the scoped `403 FILE_INFECTED` backend result.

## N-195 download-route family Browser test (2026-10-06)

The route-family recheck reproduced `ERR_BLOCKED_BY_CLIENT` on both the Instructor and API download paths. This strengthens the environment diagnosis but leaves the Browser response/UI denial test unverified.
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

The current controlled verifier completed with **1613 passed, 0 failed, 0 skipped** in `1260.83s`, exit code `0`. It used disposable SQL Server migration/concurrency databases and verified cleanup with `REMAINING=0` for both database names. This row is a current automated-test result only; Browser file chooser/direct response remains **BLOCKED ENVIRONMENT**, historical 17-row owner-approved mapping remains **UNVERIFIED**, and SMTP/inbox is explicitly **OUT OF SCOPE**.

## N-210 fresh Student filter-branch Browser test (2026-10-06)

The live Student Browser notification dropdown was reopened and exercised without a mutation: `Khóa học` returned 2 records, `Hệ thống` returned 4 records, and `Chưa đọc (0)` rendered the explicit empty state `Không có thông báo nào` / `Bạn đã xem hết các thông báo trong mục này.`. The system filter visibly includes the legacy ASCII maintenance message and test-like message rows already recorded in the inventory. This is a scoped Browser pass for filter/empty-state rendering, not a language-normalization pass.

## N-211 Instructor file-chooser boundary (2026-10-06)

After a real Instructor demo login, the course-authoring page exposed both `Tải ảnh bìa ngay` and `Đổi Ảnh Đại Diện Khóa Học`. Clicking each visible upload control left the Browser page unchanged; no native file dialog appeared in the Computer Use surface and no file was selected, transmitted or persisted. This is an additional **BLOCKED ENVIRONMENT / UNVERIFIED** file-chooser observation, not an upload pass. The session was then logged out and restored to the Student demo account; no course, file, notification or audit data was mutated.

## N-212 Admin role notification filter test (2026-10-06)

Using a real Admin demo login, the live notification center rendered the default `Chưa đọc (0)` empty state, `Tất cả` with **15** records, `Khóa học` with **10**, and `Hệ thống` with **3**. The system filter visibly contained the legacy ASCII maintenance, backup-completed and security-login-warning records. This is a scoped Browser pass for Admin role/filter/empty-state rendering, not a language-normalization pass; no notification mutation was submitted and the session was restored to Student.

## N-213 Instructor role notification filter test (2026-10-06)

Using a real Instructor demo login, the live notification center rendered `Tất cả` with **18** records, `Khóa học` with **16**, `Hệ thống` with **2**, and explicit empty states for both `Khảo thí` and `Chưa đọc (0)`. The system subset visibly contained the legacy ASCII maintenance record and the rejected-malware upload notification. This is a scoped Browser pass for Instructor role/filter/empty-state rendering, not a language-normalization pass; no notification mutation was submitted and the session was restored to Student.

## N-214 current notification API regression (2026-10-06)

The focused current-worktree command `python -m pytest -q tests/api/test_notification_api.py` completed with **16 passed in 10.59s**, exit code `0`. The result covers the test file's REST/session lifecycle, filtering, dismissal, preferences, broadcast/idempotency and canonical-envelope cases. It does not close the separately marked unrun outage/status-code branches, complete producer breadth, Browser rendering or external SMTP/inbox receipt.

## N-215 current Admin lesson-flag notification regression (2026-10-06)

The focused command `python -m pytest -q tests/api/test_admin_lesson_flag_notification.py` completed with **9 passed**, exit code `0`. It covers durable flag audit and owner notification, REST/Web idempotency replay, changed-payload conflict handling and transaction rollback when notification dispatch fails. This closes only the isolated API/DB test scope; live Admin Browser producer breadth and the separate file/SMTP gates remain open.

## N-216 current notification service/security/frontend regression (2026-10-06)

Fresh focused checks completed without skips: notification service unit **15 passed in 8.68s**; notification IDOR/security **7 passed in 4.06s**; and the combined frontend notification/router/topbar command **18 passed, 0 failed, 0 skipped**. These results are scoped to the named files and do not close full producer/role breadth, Browser file/quarantine behavior or external SMTP/inbox.

## N-218 / B-048 current Browser timing correction - 2026-10-06

Fresh Edge replay from a clean logged-out boundary reached the Instructor dashboard with the correct role identity. The captured login transition showed the success toast, followed by the settled dashboard. Opening the notification center initially showed the legitimate `Chưa đọc (0)` empty state; selecting `Tất cả` returned **18** rows (**16** course and **2** system/security), while `Khảo thí` was empty. No false empty state was observed for the explicitly selected all-items view, and the run was read-only before restoring Student1. This is **PASS for the captured Instructor login/filter timing scope**, but it does not prove sub-render timing before the first accessibility observation, all-role timing, file/quarantine behavior or SMTP/inbox receipt.

## N-217 current producer/business-flow regression (2026-10-06)

Fresh focused checks completed without skipped tests: Admin backend **16 passed in 11.25s**; Admin sub-role/RBAC **5 passed in 4.12s**; selected course-changeset cases **2 passed, 10 deselected in 1.98s**; and selected lesson-change cases **5 passed, 3 deselected in 4.37s**. Deselected cases are not counted as passes. These cover named approval/rejection, reassignment, broadcast, sub-role/RBAC, changeset and lesson-review paths only; remaining producer, Browser and external-delivery gates stay open.

The unresolved notification bodies do contain coarse labels: all 13 `LESSON_CHANGE_REQUEST` copies name CS101 and Lesson `Bài 1: Tổng quan về Kiến trúc Web & HTTP Protocol`, but none stores a change-request ID, durable target ID or correlation. The four `COURSE_CHANGE_APPROVED` copies name the same Lesson but their CTA points to course UUID `cf547469-d8b8-43ef-882c-721048826232`, which is absent from the current `courses` table; the current CS101 row has a different public UUID. Current CS101 change-request rows exist, including multiple historical candidates for the same lesson, but none matches the notification event windows. This confirms stale/missing business identity rather than an unresolved title-only query; no historical row was reassigned, deleted or merged. Final status remains **PARTIAL - not release-accepted**.

## N-219 current Guest notification boundary (2026-10-06)

Real Edge logout returned to `#/auth` with no notification control visible. Direct navigation to `/auth/notifications` from the logged-out state was intercepted with `net::ERR_BLOCKED_BY_CLIENT` before an application response. The focused API/session regression covers the unauthenticated 401, but the Browser Guest error mapping remains **UNVERIFIED**, not a pass. Student1 was restored afterward; no notification or business data was changed.

## N-220 focused notification API rerun (2026-10-06)

Fresh command `python -m pytest -q tests/api/test_notification_api.py` completed with **16 passed in 10.15s**, exit code `0`, with no skipped tests. The result covers the named lifecycle, filtering, dismiss/read, preferences, broadcast/idempotency, malformed-payload, role-filter, canonical-envelope and session/IDOR cases only; unrun 422/429/502/503 branches, complete producer breadth, Browser Guest presentation and SMTP/inbox remain open or out of scope.

## N-221 current disjoint no-skip verification (2026-10-06)

`powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\verify.ps1` exited `0`, but its embedded pytest section explicitly reported **1609 passed, 4 skipped** because SQL opt-in URLs were absent; the wrapper itself does not fail on skipped tests. The exact disposable helper `PYTHONPATH=src python docs/audits/PWD301_NOTIFICATION_AUDIT_2026-10-04_EVIDENCE/grading-runtime-probe.py sql-gates` ran all `tests/integration` cases and returned **17 passed in 24.58s**, then cleaned both databases with `audit_database_remaining=0`. Combining the 1609 non-SQL results with the four SQL cases not executed in that run gives **1613 passed, 0 failed, 0 skipped** without double-counting the 13 shared non-SQL integration cases. This closes the automated no-skip gate, not the Browser, historical-identity or SMTP/inbox gates.

## N-222 disposable producer/idempotency replay matrix (2026-10-06)

The exact SQL Server disposable fixture ran five producer/replay probes with no skipped cases: copy visibility plus event-key conflict **2 cases**; second demo seed idempotency **1 case**; enrollment recipient-scoped keys **3 cases**; course lifecycle key replay **4 cases**; and password-change, reset-token and suspension security keys **9 cases**. Every probe returned `failed_expectations=0`, `skipped=0`; durable event/notification/outbox counts stayed at the expected `2 -> 2` or `1 -> 1` values, and cleanup returned `audit_database_remaining=0`. This is PASS for the disposable SQL/API producer scopes only; Browser rapid retry, broader producer semantics, historical identity and SMTP/inbox remain open/out of scope.

## N-223 disposable lesson-flag idempotency regression (2026-10-06)

The isolated Admin lesson-flag REST replay returned first `200` with `idempotent_replay=false`, exact retry `200` with `idempotent_replay=true`, and changed payload under the same key `409 CONFLICT`. The SQL post-condition was exactly one audit, one event and one owner notification; the probe reported **3 cases, 0 failed, 0 skipped** and cleanup returned `audit_database_remaining=0`. This is scoped SQL/API moderation replay evidence; Browser rapid-click rendering and other producers remain separate.

## N-224 notification HTTP status applicability correction (2026-10-06)

Source inspection confirms all current notification blueprint success paths explicitly return `200`: list, unread-count, read, mark-all, dismiss/delete, preferences, broadcast and failed-email retry. Validation/auth/authz/not-found/conflict families map to `400/401/403/404/409`, with the named focused tests covering the exercised branches. `201` and `204` are not emitted by these routes; no notification-specific `422` or `502` mapping exists. Global `429` and `503` classes belong to email/AI/curriculum rate limiting or AI/maintenance handling and were not demonstrated on a notification route. Unexpected `500`, maintenance/outage injection and `Retry-After` remain **NOT RUN**, not passes.

## N-225 focused notification HTTP status regression (2026-10-06)

The fresh command `PYTHONPATH=src python -m pytest -q tests/api/test_notification_api.py tests/security/test_notification_idor.py` returned **23 passed in 9.89s**, exit code `0`, with no skipped tests. The covered assertions exercise `200` success/lifecycle responses, `400` malformed or invalid mutation input, `401` anonymous access, `403` IDOR/non-admin denial and `409` changed idempotency payload. The run does not inject or claim notification-specific `404`, `422`, `429`, `500`, `502` or `503` behavior; those remain open status-matrix cases.

## N-226 current Student Browser notification-surface replay (2026-10-06)

The live Edge Computer Use tab remained available at the authenticated Student dashboard for `Lê Hoàng Long`. Opening the real notification popover showed `Thông báo 0 mới`, `Chưa đọc (0)`, the role label `Học viên`, and **13** visible notification records across the category filters. The popover was closed through its visible control without read, dismiss, delete, upload or other business mutation. This is a current Browser rendering observation only; all-role timing, keyboard accessibility, file chooser behavior and SMTP/inbox delivery remain separate gates.

## N-227 isolated notification 404 contract probe (2026-10-06)

An isolated Flask test-client probe on in-memory SQLite authenticated a disposable Student and exercised missing and malformed notification IDs for mark-read and delete. All three requests returned **404** with `success=false`, `data=null` and `error.code=RESOURCE_NOT_FOUND`; no live database or notification history was touched. This closes only the sampled notification `404` mapping and does not claim unrun `422/429/500/502` injections.

## N-228 notification maintenance 503 and retry-after regression (2026-10-06)

The existing E2E command `PYTHONPATH=src python -m pytest -q tests/e2e/test_admin_ops_lifecycle_e2e.py` returned **5 passed in 4.37s**, exit code `0`, with no skipped tests. Its disposable maintenance window asserted Student `GET /api/notifications/unread-count` returns `503`, `MAINTENANCE_MODE_ACTIVE`, `Retry-After: 1200`, then returns `200` after maintenance ends. This closes the sampled notification maintenance/`503`/`Retry-After` path; unexpected `500` and notification-specific `422/429/502` injections remain open.

## N-229 isolated notification 500 and 429 fault-injection contract probe (2026-10-06)

In an isolated Flask test client on in-memory SQLite, a patched notification list dependency raised a generic runtime fault and returned **500** with `success=false`, `data=null`, `error.code=INTERNAL_ERROR` and a user-safe message. A patched failed-email retry dependency raised `EmailRateLimitExceededError` and returned **429** with `error.code=RATE_LIMIT_EXCEEDED` and `Retry-After: 60`. No live data was accessed; current notification routes have no specific `422` or `502` mapping/injection.

## N-230 notification 422/502 applicability boundary (2026-10-06)

The read-only source check confirms notification validation maps through `ValidationError` to `400`; no notification route returns `422` or `502`, and the global domain-handler table defines no notification mapping for either status. These statuses are therefore **not applicable at the Flask notification boundary**, not skipped notification tests. A reverse-proxy or external-upstream `502` would be outside this application contract and remains outside this audit scope.

## N-231 corrected AST producer inventory (2026-10-06)

A corrected read-only AST pass over `src/pwd301` classified the actual dispatcher keywords (`event_key` and prebuilt `event`) and found **35** direct calls: **34** explicit deterministic-key calls, **1** prebuilt-event call at `src/pwd301/services/course_service.py:286`, and **0** without either identity. The earlier local probe used the obsolete `notification_event_id` keyword and was rejected as a harness-classification error; no product source changed. This is static inventory evidence only, not semantic retry/race proof.

## N-232 fresh Student Browser category-filter replay (2026-10-06)

On the authenticated Edge Computer Use Student tab, the notification popover opened normally with `Thông báo 0 mới` and `Chưa đọc (0)`. Read-only filter actions showed **13** records in `Tất cả`, **7** in `Khảo thí`, **2** in `Khóa học` and **4** in `Hệ thống`. The accessibility tree remained populated after each filter; no mutation control was activated. This is a Browser UI pass for one Student session, not proof of all-role producer semantics, retry/race behavior, file chooser behavior or SMTP/inbox delivery.

## N-233 repeated Instructor file-chooser boundary (2026-10-06)

The live Edge session logged in as the demo Instructor and reached the OPS401 lesson studio. Clicking the real document chooser control returned without a native dialog; the Browser state still had `apps=[]` and no separate file-chooser surface, while the AX tree retained the original clean attachment and no upload placeholder. This test therefore records **BLOCKED ENVIRONMENT / UNVERIFIED** for file selection and rejected-file/quarantine acceptance, with no mutation performed.

## N-234 broader producer-service regression group (2026-10-06)

The fresh isolated command `PYTHONPATH=src python -m pytest -q tests/unit/test_course_service.py tests/unit/test_enrollment_service.py tests/unit/test_user_service.py tests/unit/test_lesson_service.py` returned **90 passed in 59.65s**, exit code `0`, with no skipped tests. The group exercises course, enrollment, user/role and lesson service behavior in fixture-backed runtime tests. It adds regression evidence but does not close all-callsite semantic, role, rapid-retry/race or Browser-chain coverage.

## N-235 assessment/file producer-service regression group (2026-10-06)

The fresh isolated command `PYTHONPATH=src python -m pytest -q tests/unit/test_attempt_service.py tests/unit/test_attempt_submission_service.py tests/unit/test_file_service.py tests/unit/test_malware_scan_service.py` returned **38 passed in 26.90s**, exit code `0`, with no skipped tests. The group covers attempt/submission and file/malware fixture behavior. It adds current regression evidence but does not close all producer semantics or Browser file chooser/quarantine acceptance.

## N-243 current dispatcher identity inventory (2026-10-06)

| Check | Command | Observed result | Classification |
|---|---|---|---|
| Dispatcher identity presence | Independent AST scan over current `src/pwd301` Python source | 35 calls: 34 `event_key`, 1 prebuilt `event`, 0 missing, no parse errors | PASS, static |
| Semantic identity/race correctness | Not established by AST | Runtime producer matrix remains open | UNVERIFIED |

## N-242 producer-heavy service regression group (2026-10-06)

| Case group | Command | Observed result | Classification |
|---|---|---|---|
| Authorization, notification, email, completion, instructor application | `PYTHONPATH=src python -m pytest -q tests/unit/test_authorization_service.py tests/unit/test_notification_service.py tests/unit/test_email_service.py tests/unit/test_completion_service.py tests/unit/test_instructor_application_service.py` | 64 passed in 53.59s, exit code 0, no skips | PASS, scoped |
| Complete producer/role/retry matrix | Not covered by this fixture group | Remains open | UNVERIFIED |

## N-241 current Admin lesson-flag reconciliation (2026-10-06)

| Case | Command | Observed result | Classification |
|---|---|---|---|
| Admin lesson flag | `PYTHONPATH=src python -m pytest -q tests/api/test_admin_lesson_flag_notification.py` | 9 passed in 7.28s, exit code 0, no skips | PASS, scoped |
| Historical RCA-040/RCA-027 | Compare current routes/service signature and focused tests | Not reproduced in current source | SUPERSEDED |

## N-240 fresh API and frontend notification regression (2026-10-06)

| Case | Command | Observed result | Classification |
|---|---|---|---|
| API/IDOR | `PYTHONPATH=src python -m pytest -q tests/api/test_notification_api.py tests/security/test_notification_idor.py` | 23 passed in 15.20s, exit code 0, no skips | PASS, scoped |
| Frontend | `node --test tests/frontend/*.test.js` | 108 passed, 0 failed, 0 skipped, todo 0, exit code 0 | PASS, scoped |
| End-to-end producer breadth | Not covered by these commands | Remains open | UNVERIFIED |

## N-239 fresh Admin notification filter matrix (2026-10-06)

| Case | Action | Observed result | Classification |
|---|---|---|---|
| Admin all | Select `Tất cả` | 15 records | PASS, scoped |
| Admin unread | Select `Chưa đọc` | 0 records | PASS, scoped |
| Admin assessment | Select `Khảo thí` | 1 record | PASS, scoped |
| Admin course | Select `Khóa học` | 11 records | PASS, scoped |
| Admin system | Select `Hệ thống` | 3 records | PASS, scoped |
| Admin mutation safety | Use only category filters | No delete/dismiss/mark-read/refresh mutation | PASS, scoped |

The initial N-237 3-record observation is retained as the initial system-category view, not as the Admin total.

## N-237 fresh Admin notification-center replay (2026-10-06)

| Case | Action | Observed result | Classification |
|---|---|---|---|
| Admin center | Fresh demo Admin login; open notification center | 0 unread, Admin role, 3 persisted system/security records | PASS, scoped |
| Admin mutation safety | No delete/dismiss/mark-read/refresh action | No business mutation | PASS, scoped |
| Admin producer/broadcast | No new event created | Not exercised | UNVERIFIED |

## N-238 fresh Guest protected-route boundary (2026-10-06)

| Case | Action | Observed result | Classification |
|---|---|---|---|
| Guest route | Logout, navigate to `#/student/notifications` | Redirected to `/auth`; login surface only | PASS, scoped |
| Guest notification control | Inspect AX tree after redirect | No authenticated topbar notification control | PASS, scoped |
| Guest API matrix | Browser route only in this replay | API `401` remains covered separately | PARTIAL |

## N-250 YouTube Browser/UI ownership replay

| Case group | Action | Observed result | Classification |
|---|---|---|---|
| Instructor course management | Open real OPS401 management page | No scan-video control visible | OPEN ownership gap |
| Lesson Studio invalid link | Enter `not-a-youtube-url`, click `Thêm link`, clear input | Vietnamese warning toast; no save or business mutation | PASS, validation boundary |
| Frontend caller inventory | Search for `scanCourseVideos` | Definition only in `api.js`; no caller found | OPEN API/UI integration gap |

## N-249 disposable YouTube route/API extension

| Case group | Action | Observed result | Classification |
|---|---|---|---|
| Guest route boundary | POST scan route without auth | HTTP 401 | PASS, disposable route scope |
| Instructor owner route | Authenticated owner POST scan route | HTTP 200, `success=true`, `broken_count=1` | PASS, disposable route scope |
| Route/service replay | Repeat scan after initial broken event | Event and notification counts remain 1/1 | PASS, idempotency scope |
| Browser UI scan control | Find/click real Instructor control and inspect visible result | Not performed in this probe | OPEN |

## N-248 disposable YouTube producer service/DB replay

| Case group | Action | Observed result | Classification |
|---|---|---|---|
| Valid oEmbed | Mock valid external result and scan | 0 reports, 0 notification writes | PASS, disposable service scope |
| Network error | Mock `network_error=true` and scan | 0 reports, no notification | PASS, fail-safe service scope |
| Broken video | Mock 404-like invalid result and scan | 1 report, 1 `COURSE_LESSON_VIDEO_BROKEN` event and 1 owner notification | PASS, service/DB scope |
| Exact retry | Scan identical broken fixture twice | Counts remain event 1 → 1 and notification 1 → 1 | PASS, idempotency scope |
| Instructor route/API/Browser | Submit real route and inspect UI post-condition | Not run in this probe | OPEN |

## N-247 YouTube broken-video producer coverage gap

| Case group | Action | Observed result | Classification |
|---|---|---|---|
| Broken YouTube scan | Inspect source and test inventory | Producer and route exist; no matching test file or runtime replay found | UNVERIFIED, producer-chain gap |
| Key identity | Inspect source expression | UUIDv5 uses course ID, lesson ID, video ID and instructor ID | PASS, static key-shape only |

## N-246 producer-key semantic-shape inventory

| Case group | Action | Observed result | Classification |
|---|---|---|---|
| Direct dispatcher identity scan | Parse current `src/pwd301/**/*.py` and classify 35 direct calls | 34 durable-identity candidates; 0 random/clock; 0 constant/unclassified; 1 prebuilt event | PASS, static inventory only |
| Runtime semantic convergence | Compare every producer's role/payload/business post-condition under retries/races | Not established by AST | OPEN; requires per-producer runtime/API/DB matrix |

## N-245 fresh Student notification-center content/filter replay (2026-10-06)

| Case group | Action | Observed result | Classification |
|---|---|---|---|
| Student login and immediate center open | Login with demo Student, open notification popover | Vietnamese login toast; center rendered 13 records and `Chưa đọc (0)` | PASS, scoped Browser timing/rendering |
| Student category filters | Select `Khảo thí`, `Khóa học`, `Hệ thống`, restore `Tất cả` | 7, 2, 4 and 13 records respectively | PASS, scoped read-only filter behavior |
| Current message quality | Inspect rendered records | Unaccented system copy plus `heo peppa caccaccac` and `bucutaodi thật là bá khí` | FAIL, sampled content quality; no mutation |

## N-244 grading/regrade producer-service regression (2026-10-06)

| Case group | Command | Result | Classification |
|---|---|---|---|
| Grading and regrade services | `PYTHONPATH=src python -m pytest -q tests/unit/test_grading_service.py tests/unit/test_regrade_service.py` | 25 passed, 0 failed, 0 skipped, exit 0 | PASS, scoped service regression; not complete producer/role/retry or Browser-chain coverage |

## N-236 fresh Instructor notification-center replay (2026-10-06)

The live Edge Instructor session on the OPS401 lesson studio opened the notification center and showed `Thông báo 0 mới`, `Chưa đọc (0)`, `Giảng viên` and **2** records. One persisted security record rendered the rejected/quarantined-file message for `X_SENTINEL_VIBECODE_BASELINE_V2.zip`; no notification mutation was invoked. This is a current role/UI rendering pass only and does not claim a successful Browser upload or end-to-end producer replay.

## N-251 frontend mechanism inventory test

| Case group | Static action | Result | Classification |
|---|---|---|---|
| Shared toast calls | Parse 10 `frontend/assets/js/**/*.js` files and include optional-chain calls | 383 invocations: 214 quoted, 73 template, 96 dynamic; 202 unique quoted literals | PASS, static inventory |
| Alternate message surfaces | Count `UI.alert`, `UI.confirm`, `UI.prompt`, direct `window.confirm` | 2, 30, 8 and 1 respectively | PASS, static inventory; semantic replay open |
| Native/accessibility markers | Count native alert/prompt/dialog and live-region markers | 0 / 0 / 0; 6 `aria-live`, 4 `role="alert"` | PASS, static inventory; timing and screen-reader behavior open |

The parser is not a substitute for per-producer Browser/API/DB verification. SMTP/inbox is not executed because the deployment has no mail provider.
## N-252 producer execution coverage matrix

| Case group | Command/evidence | Result | Classification |
|---|---|---|---|
| Broad producer/API tests | Coverage run over selected service/API/security tests | 312 passed, 0 failed, 0 skipped; then 6 additional tests passed, 0 failed, 0 skipped | PASS, scoped |
| Prerequisite rejection probe | Disposable SQLite/temp-storage route replay | 202 staging, 200 review, `REJECTED`, one `COURSE_PREREQUISITE_REJECTED`, zero link | PASS, disposable |
| Rejected file-revision probe | Disposable SQLite/temp-storage upload replay | `REJECTED`, no blob, one `FILE_REJECTED`, one SECURITY notification | PASS, disposable |
| YouTube producer probe | Disposable SQLite route/service/replay | Valid/network-error suppressed; broken one event/notification; exact replay stable | PASS, disposable |
| Dispatcher correlation | AST callsites against coverage data | 35/35 covered, 0 uncovered | PASS, line execution only |

The matrix still requires per-role semantic assertions and temporal duplicate/timeout/cancel/unmount checks beyond line coverage.
## N-253 Browser auth-error test

| Case group | Action | Observed result | Classification |
|---|---|---|---|
| Invalid login | Enter invalid email/password and submit in Edge | `/auth` remained; one visible inline `#auth-error-alert` with `Email hoặc mật khẩu không chính xác.` | PASS, sampled failure owner |
| Duplicate surface | Inspect DOM/AX after response | No shared toast; one inline error surface | PASS, sampled ownership |
| Error duration | Observe through approximately 6.45 seconds | Inline error remained visible | OBSERVED; timeout policy not established |
| Accessibility semantics | Inspect live DOM attributes | No explicit `role` or `aria-live` | OPEN P2 gap |
## N-254 Browser file-chooser test

| Case group | Action | Observed result | Classification |
|---|---|---|---|
| Document chooser control | Inspect and click real `#btn-choose-doc-file` | Control present and clickable | PASS, discoverability only |
| Supported chooser flow | Start `waitForEvent("filechooser")`, click control | No event; timeout; debugger detached | BLOCKED ENVIRONMENT |
| File upload/rejection | Set harmless fixture after chooser | Not reached; no file selected or request observed | UNVERIFIED, not skipped/pass |
## N-255 producer semantic coverage matrix

| Case group | Static result | Classification |
|---|---|---|
| Identity | 34 explicit `event_key`, 1 prebuilt event, 0 missing both | PASS, identity presence |
| Category | COURSE 20, SECURITY 6, SYSTEM 8, one dynamic | PASS, inventory only |
| Target role | 17 explicit roles; 18 missing/`None` | PARTIAL; per-producer role assertions open |
| Dynamic assessment path | Event type/category expressions are not literal at the callsite | OPEN; requires runtime message/recipient/retry assertions |
## N-256 focused role/retry test matrix

| Test family | Result | Scope |
|---|---|---|
| Event idempotency and payload conflict | PASS | 3 notification-service tests |
| Target-role isolation | PASS | 1 notification-service test |
| Enrollment role fan-out/persistence | PASS | 2 enrollment-service tests |
| Course lifecycle/owner reassignment keys | PASS | 2 course-service tests |

Command result: **8 passed, 0 failed, 0 skipped in 5.63s**. This remains a focused representative matrix.
## N-257 historical disposition test gate (2026-10-06)

The 17-row historical case has a separate non-mutating acceptance gate. The
read-only fixture inventory must be approved by business identity, then replayed
on a disposable database before any live repair. Required assertions are exact
row IDs, old/new mapping, append-only preservation, event/notification/outbox
counts, audit trail and rollback. Identical copy alone is not a duplicate-pass
condition. Details are in the [approval packet](09_HISTORICAL_NOTIFICATION_APPROVAL_PACKET.md).
SMTP/inbox is **OUT OF SCOPE**.
## N-258 file chooser test result (2026-10-06)

The live attempt is recorded as **BLOCKED ENVIRONMENT / UNVERIFIED**: the
control was visible, but the supported chooser event timed out twice across
separate attempts, with no file selection, HTTP upload response or SQL mutation.
It is not counted as a skipped or passed test.
## N-259 Browser category/content matrix result (2026-10-06)

The read-only Browser matrix observed `Khóa học=16` visible cards and two
`Hệ thống` cards. It exercised category filtering and content inspection, then
closed the popover without mutation. The result is **PASS for sampled filter
rendering** and **OPEN for global language/catalog correctness**.
## N-260 multi-role target-scope matrix (2026-10-06)

The remaining role test must assert both dimensions: exact recipient user and
visibility under each active role filter. Required cases include account-wide
security/role events and route-specific prerequisite, review, intervention,
application and YouTube events. A unique recipient alone is insufficient to
close `target_role=NULL` semantics.
## N-261 multi-role role-filter regression (2026-10-06)

Required regression: one account with ADMIN, INSTRUCTOR and STUDENT roles; one
Admin-only lesson-review notification with NULL target role; GET filters for
all three roles; assert only the intended role includes the item and that other
role views cannot expose the Admin CTA. Also assert no cross-user rows and no
mutation. The current live replay fails this expected matrix.
## N-262 schema-contract verification matrix (2026-10-06)

Required checks are: canonical dictionary lists `target_role` as nullable;
lists its allowed values; lists the role/unread index and CHECK constraint;
applied migration and SQL Server metadata match; model serializer and API
filter use the same contract. Current runtime metadata passes the latter
database checks, while canonical documentation is missing the field.
## N-263 executed role-test scope (2026-10-06)

Executed command: `test_target_role_isolation_and_unread_count` plus
`test_notification_role_filters_reject_unsupported_values`; result **3 passed,
0 failed, 0 skipped in 1.58s**. Missing case: route-specific CTA compatibility
for a NULL-target notification on a multi-role account, as demonstrated by
N-261.
## N-264 cross-user negative case (2026-10-06)

Executed live negative matrix: Student1 with `role=STUDENT` returned 200 and
zero Admin-review CTA matches; actor-ineligible `INSTRUCTOR`/`ADMIN` filters
returned 400. This is a scoped cross-user/role authorization pass, not a
same-account CTA pass.
## N-265 Browser CTA containment case (2026-10-06)

Executed a fresh Edge read-only navigation to
`#/admin/change-requests/review?id=50002` under the current Instructor-only
session. Observed the Vietnamese Admin-access warning and final URL
`#/instructor/dashboard`; no notification or business row changed. Result:
**PASS for late route denial/redirect**, **FAIL/OPEN for upstream CTA
compatibility**, because the test target was reachable from notification-role
semantics in the earlier N-261 replay.
