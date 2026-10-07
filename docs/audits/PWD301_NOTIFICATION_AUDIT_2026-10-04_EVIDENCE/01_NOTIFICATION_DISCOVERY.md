# 01_NOTIFICATION_DISCOVERY

## Fresh moderation discovery checkpoint (2026-10-05)

The actual Admin review → published lesson → flag prompt flow exposed a previously source-only producer failure. Empty input was rejected locally; valid input returned Browser HTTP 500 with an English error, and SQL retained no flag/audit/event/notice. JWT replay confirmed the same valid-input failure plus two malformed-type 500s; Guest/Instructor/Student rejection and empty/short/missing-target guards worked in the sampled REST cases. See [flag-runtime-evidence.md](flag-runtime-evidence.md), inventory N-125–N-134 and RCA-040/RCA-027 continuation. This is a business-flow finding, not just a message grep.

The same continuation exercised all four Admin sub-role notification paths in Browser and SQL: each role assignment persisted one audit plus one role-specific notice, each CTA reached the expected scoped route, and each notice was read-confirmed through the center. REST replay confirmed the three unrelated sub-roles were denied lesson-flag mutation without state change; the course-review sub-role reached the known exact-five-character RCA-040 failure. Inventory rows N-136–N-139 preserve this evidence; duplicate/rapid-repeat and outbound delivery remain open.

Post-fix discovery closed that specific producer chain: a fresh SQL Server flag replay returned 10/10 expected statuses with zero skips, and the Browser exact-five-character path visibly produced the success toast with one flag, audit, event and owner notice in SQL. The corrected sub-admin replay returned 8/8 expected checks with zero skips. The broader notification audit remains active for the independent gates below.

Graphify was used as an auxiliary backend map with local AST only: `graphify src/pwd301 --no-viz` generated 3053 nodes/10275 edges/125 communities under src/pwd301/graphify-out. No configured LLM was available for semantic community labels; structural mapping is not a substitute for the Browser/SQL proof and does not establish full FE/external-service relationships. Product source was not changed by this checkpoint.

## Checkpoint kiểm thử không skip và an toàn môi trường (2026-10-05)

Checkpoint này có ưu tiên hơn các số liệu 1572/1578 và các trạng thái lịch sử bên dưới. Lượt chạy ban đầu có 1576 passed, 2 failed, 0 skipped; hai test upload tài nguyên và lease bài thi trả 503. Chạy riêng cho 2 passed; chạy lại toàn nhóm API trước sửa fixture cho 375 passed. Probe có restore marker trên thư mục audit riêng tái hiện đúng cả hai phản hồi MAINTENANCE_MODE_ACTIVE/503. Việc nhóm test dùng chung storage/quarantine/backups với workspace là lỗi cô lập đã được chứng minh; không quy kết chắc chắn nguyên nhân của lượt lỗi ban đầu khi chưa lưu response của lượt đó.

Fixture app nay dùng ba thư mục con riêng trong tmp_path. Regression mới thất bại với các root E:/PWD301/storage, quarantine, backups trước sửa. Sau sửa, probe vẫn giữ marker bên ngoài và 27 test upload/lease/backup/restore/maintenance đạt; không tắt maintenance hay fail-closed. Marker probe đã xóa. Test mới dùng nhầm một route không tồn tại lúc đầu; lỗi harness 404 đó đã sửa, không tính là lỗi sản phẩm.

Cô lập filesystem lộ thêm lỗi rescan: kiểm tra substring “infected” trên toàn đường dẫn nhầm thư mục cha với vùng chứa tệp nhiễm. Regression hiện hữu thất bại hai lần trước sửa; nay so sánh parent đã resolve với get_file_infected_root(), kiểm tra tệp được chuyển, key infected/hash và Student vẫn bị từ chối 403. Focused stress/file/isolation: 27 passed. Lượt split cuối sau sửa cho **1579 passed, 0 failed, 0 skipped**, khớp **1579 tests collected**: root298 + unit632 + API375 + security233 + concurrency13 + E2E12 + integration16. Frontend độc lập: **101 passed, 0 failed, 0 skipped**. Không cộng các lượt focused trùng vào tổng. Đây là kết quả các nhóm chạy đủ, không phải một aggregate verifier được tuyên bố pass; lượt aggregate lịch sử bị stall vẫn không được tính.

SQL-gated integration hiện tại: 16 passed, 0 failed, 0 skipped, gồm migration, ROWVERSION race và hai loại revision trên SQL Server thật. Hai DB migration/race tạm đã xóa, remaining=0. Browser Student4 đã đăng xuất về form login; server audit 5105 dừng; DB grading tạm cũng đã xóa, remaining=0. Không migrate/restart DB/runtime chính; fixture có thể dựng lại bằng prepare.

Audit notification vẫn PARTIAL, không phải release sign-off. Những đoạn dưới nói “chưa sửa”, “pending replay”, “1572 current” là snapshot lịch sử, không được dùng thay checkpoint mới.

## Latest SQL Server continuation (2026-10-05)

The isolated grading fixture exposed three producer-chain defects not established by the earlier aggregate: missing manual-release notice, migration CHECK drift preventing ANSWER_CHANGE, and premature revision activation rejected by the SQL Server immutable-child trigger. After those corrections, the real regrade worker changed 18→28 but still emitted no notice because it bypassed the attempt aggregation dispatcher. Both aggregation paths now reuse one result-change notifier; no trigger is disabled. See RCA-033 through RCA-036 and the reproducible script.

Fresh evidence: 143 focused backend tests and 16 integration tests passed with zero skips. The integration run includes both existing SQL gates and two new real SQL Server revision-trigger cases. Browser Student4 saw both persisted notices and followed the change notice to 28/30. The result detail still falsely shows the answered/graded ESSAY as unanswered/0 points (RCA-037). The final split verification is1579 passed,0 failed,0 skipped as detailed in the top checkpoint; historical1572 is not the current total. The main runtime/database was not migrated or restarted.

Current continuation correction: the original discovery snapshot was read-only, but this resumed goal added scoped fixes across seven unique product files, as recorded in the fix plan. The latest completed split pytest verification is `297 + 629 + 375 + 233 + 13 + 12 + 13 = 1572 passed, 0 failed, 0 skipped` across root-level, unit, API, security, concurrency, E2E and integration groups; the two SQL Server gates ran against disposable databases and those databases were removed. A subsequent aggregate attempt stalled at 49% and was terminated, so it is not counted as a pass. The notification audit remains partial because Browser/API/DB business coverage is incomplete.

Latest auth correction: actual CDP runtime inspection invalidated the earlier BFCache inference. Three real-router regressions reproduced the unauthenticated auth fallback, then passed after an auth guard correction; the frontend suite is 101 passed, 0 failed, 0 skipped. Live modal Escape and logout/Back settled at auth without private surfaces. All three demo shortcuts now reached their intended Student/Instructor/Admin routes in clean sessions. Only agent-owned speculative bootstrap code/tests were removed; unrelated user changes remain preserved. A fresh SQL Server read-only check reported `DISPOSABLE_AUDIT_DATABASES_REMAINING=0`.

## Fresh Browser continuation (2026-10-05)

Student, Instructor and Admin demo login paths were exercised in Edge with the visible quick-login controls. Student login reached `#/student/dashboard`, Instructor reached `#/instructor/dashboard`, and Admin reached `#/admin/governance`; each session showed the success toast and was logged out cleanly. Student notification detail exposed a broken result CTA: the persisted notification opened a modal, but `Mở Trang Liên Quan` navigated to `#/student/assessments/<assessment-id>/results` and rendered a 404. The canonical attempt-result route `#/student/assessments/results?id=<attempt-id>` rendered the real result page. Source tracing found the producer defect in `attempt_service.py`; the current source/test fix now emits the canonical attempt route.

The same source audit found `STUDENT_ENROLLED` notifications using server paths without the SPA hash. A failing unit regression reproduced both malformed role-specific URLs; the current source now emits `#/instructor/courses/manage?id=...` and `#/student/courses/detail?id=...`. This fixes route construction in source, while a fresh live enrollment notification/DB correlation is still not claimed.

## Trạng thái

- Ngày audit: 2026-10-04.
- Phạm vi: hệ thống notification từ producer Backend, database model, API, ApiClient, router, toast/modal/alert UI đến hành vi người dùng.
- Product code đã sửa trong lượt audit này: **Có**, gồm các scoped continuation fixes được liệt kê trong các báo cáo regression/fix-plan; các thay đổi vẫn dirty và chưa commit.
- Kết luận nghiệm thu hiện tại: **PARTIAL – CHƯA ĐỦ ĐIỀU KIỆN NGHIỆM THU**.

Browser login sau đó đã được cho phép và thực hiện với Student, Instructor và Admin; blocker browser ban đầu không còn hiệu lực. SQL Server migration/concurrency đã được chạy trên một database tạm và pass; aggregate verifier ban đầu vẫn skip vì các URL opt-in chưa được cấu hình. Không được suy diễn các phần chưa chứng minh từ grep hoặc test fixture.

## Current continuation - manual ESSAY grading (2026-10-05)

The former ESSAY UI gap was rechecked with a controlled disposable attempt. Instructor Browser -> existing grading API -> service -> SQL Server now passes for a pending ESSAY: score `3.5`, required reason, success toast, refreshed `3.5 / 20` result and `MANUAL_GRADED` grade row. The Student renderer correction is covered by a focused regression, the full frontend suite and a direct Browser replay of an existing released result; the fullscreen limitation applies only to starting a new controlled attempt. The fixture was removed and orphan verification returned zero rows. After the shared SECURITY redaction correction, the complete split is **1,589 passed, 0 failed, 0 skipped** and frontend is **105 passed, 0 failed, 0 skipped**. Overall audit status remains PARTIAL because the independent Browser file, external mail and producer/role breadth gates remain open.

## Nguồn sự thật đã đối chiếu

1. `docs/system/PWD301_SYSTEM_SPECIFICATION/api/11_NOTIFICATION_API.md`
2. `docs/system/PWD301_SYSTEM_SPECIFICATION/business/14_NOTIFICATION_AND_EMAIL.md`
3. `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/008_notification_audit.sql`
4. `docs/database/PWD301_DATABASE_ARCHITECTURE/11_DATA_DICTIONARY_NOTIFICATION_AUDIT_OPERATIONS.md`
5. `tasks/CURRENT.md`, `README.md`, `docs/system/PWD301_SYSTEM_SPECIFICATION/CODING_AGENT_START_HERE.md`
6. Source hiện hành và test hiện hành trong worktree. Worktree đã dirty từ trước; không ghi đè hoặc hoàn nguyên các thay đổi đó.

## Bản đồ hệ thống được phát hiện

```text
business service / blueprint
        |
        v
notification_service.dispatch_notification()
        |
        +--> notification_events + notifications + email delivery path
        |
        v
/api/notifications and web-auth notification routes
        |
        v
frontend/assets/js/api.js -> router.js -> UI.showToast / modal / alert
        |
        v
user-visible result and subsequent business action
```

### Runtime evidence đã chạy

| Probe | Kết quả thực tế | Ý nghĩa |
|---|---:|---|
| `GET http://127.0.0.1:5000/` | HTTP 200, `PWD301 LMS - Học Tập Và Bài Thi` | SPA login page reachable |
| `GET http://127.0.0.1:5000/health` | HTTP 200, `status: ok`, `probe: liveness` | local process responds |
| `GET http://127.0.0.1:5000/api/health` | HTTP 404 | không có endpoint này ở runtime hiện tại |
| Browser AX tree | login form + demo Student/Instructor/Admin buttons; ba session demo sau đó đã được kiểm thử | UI reachable; login gate đã pass, các workflow còn thiếu được ghi bên dưới |
| unauthenticated notification API probes | GET/list, unread count, mark, dismiss, preferences, broadcast, retry trả HTTP 401 | auth gate hoạt động; response chỉ có `error`, chưa có `success:false` và `data:null` |
| `docker compose ps` / `docker ps` | initial discovery had no Docker connection; latest check shows Docker 29.6.2 with `pwd301_db`, `pwd301_web` and `pwd301_clamav` healthy | direct read-only SQL Server correlation passed, and fresh disposable migration/concurrency gates also passed; the normal aggregate still needs opt-in URL configuration |

## Static discovery counts

Các số dưới đây là kết quả lệnh trong lượt audit, không phải số lượng notification đã phát sinh trong database:

- 37 callsite `dispatch_notification(...)` trong product source; 38 occurrence nếu tính cả định nghĩa hàm.
- 384 occurrence `UI.showToast` trong `frontend/assets/js`.
- 39 occurrence theo regex `alert|confirm` trong frontend; cần browser phân biệt native/control wrapper và path thực thi.
- 108 occurrence thuộc nhóm frontend truyền `err.message`, `error.message` hoặc `res.message` ra UI theo static search.

## Phát hiện kiến trúc chính

1. Backend dispatch nhận `event_type`, title, body, URL và category tự do; chưa có message catalog/code bắt buộc ở model/API.
2. API notification có nhiều response shape: có route dùng `success`, có route trả object raw, có route trả `preferences` hoặc counter ở top-level.
3. Global error formatter hiện trả `error` nhưng không luôn trả đồng thời `success: false` và `data: null`, trong khi operating contract yêu cầu envelope thống nhất.
4. `ApiClient` truyền message backend/raw HTTP vào `Error`; nhiều view truyền tiếp message đó vào toast.
5. Router có xử lý notification nền, nhưng lỗi `fetchNotifications` bị bắt và chỉ ghi `console.warn`; frontend test sandbox đã phát hiện `ApiClient.getNotifications is not a function` vì mock không khai báo method dù production `api.js` có method này. Đây là test-harness gap; production degraded-state gap được chứng minh riêng bằng fallback network-failure probe.
6. Dismiss hiện trả `status: deleted`, trong khi test và contract hiện hành yêu cầu `status: dismissed`; lỗi này đã fail trực tiếp ở cả unit và API test.
7. Model serializer vẫn phát `deleted_at: None` dù canonical notification schema không có cột `deleted_at`; cần quyết định contract trước khi sửa.
8. Có nhiều producer dùng cùng event name cho các ngữ nghĩa khác nhau, cùng với heuristic ẩn duplicate theo title/body thay vì business idempotency key.

## Giới hạn của discovery

Vẫn chưa thể kết luận đầy đủ duplicate ở mọi retry path, approve/reject cross-role, upload/download, email delivery hoặc API/DB correlation sau mọi CTA. SQL Server migration/row-version gate đã pass trên database tạm, nhưng không thay thế release-environment verification. Các mục còn thiếu được ghi rõ là `NOT RUN`, `PARTIAL`, `FAIL` hoặc `UNVERIFIED` trong test matrix và final report.

## Browser runtime evidence đã thu được sau khi được cấp quyền login

| Role/account | Action | Kết quả quan sát được | Đánh giá |
|---|---|---|---|
| Student demo `student1@pwd301.local` | Login | Nút ghi Student nhưng route mặc định là `#/instructor/dashboard`, topbar là GIẢNG VIÊN; account có cả INSTRUCTOR và STUDENT | PARTIAL / role-default ambiguity |
| Student demo | Role switch Instructor → Student | Route đổi sang `#/student/dashboard`, topbar HỌC VIÊN, toast chuyển góc nhìn thành công | PASS |
| Student demo | Notification center | Badge ban đầu 5 mới, danh sách 6; mark-all đổi badge về 0 và hiện toast thành công | PASS; unread count khác total là hợp lý |
| Student demo | Category filter | `Khảo thí` lọc còn nhóm điểm/quiz; `Tất cả` khôi phục course/system items | PASS |
| Student demo | Delete + refresh | Delete hiện toast `Đã xóa thông báo.`; refresh không đưa item đã xóa trở lại | PASS UI; public API status vẫn có regression trong test |
| Student/Instructor/Admin demo | Logout | UI bỏ topbar; sau reload hiển thị login, không còn protected content; hash route cũ còn trong URL | PARTIAL; fail-closed sau reload, history/hash UX cần sửa |
| Instructor demo `instructor1@pwd301.local` | Login + notification center | Route instructor, đúng tên/role; badge 3 mới, 5 item; có hai item gần trùng về bài MIDTERM cần chấm | PASS login; DUPLICATE OBSERVED |
| Admin demo `admin@pwd301.local` | Login + notification center | Route admin; badge 2 mới, 5 item; filter Hệ thống còn maintenance/backup và security alert | PASS login/filter |
| Admin demo | Broadcast modal với title/body rỗng | Không gửi request; toast `Vui lòng nhập tiêu đề thông báo.` | PASS validation |
| Admin demo | Broadcast hợp lệ chỉ tới Admin | Toast báo gửi tới 1 người; badge tăng 2 → 3; dropdown hiển thị đúng title/body; HTTP trả `SYSTEM_BROADCAST` và `is_read=false` | PASS cho một audience path; retry/audience khác chưa chạy |
| Admin demo | Double-click broadcast | Hai success toast xuất hiện; HTTP list chỉ hiển thị một item (`total=7`, `unread_count=4`), nhưng SQL Server trực tiếp có 2 notification rows và 2 event IDs cho cùng title | FAIL/P1 duplicate bị API/UI che bởi dedupe |
| Admin demo | Governance background load | UI hiện lỗi tiếng Anh `Only the primary administrator...`; console ghi warning lặp lại mỗi chu kỳ | FAIL/DEGRADED UX |
| Student demo | Catalog search | Nhập `OPS401` thu hẹp danh sách còn khóa DevOps và banner đề xuất tương ứng | PASS search; category selection chưa chạy |
| Instructor demo | Create-course form | Submit rỗng hiện `Vui lòng nhập đầy đủ Tên khóa học và Mã khóa học.`; Hủy bỏ đóng modal không ghi dữ liệu | PASS validation/cancel |

### Authenticated API capture

CDP network capture ban đầu trong ba session ghi nhận `GET /auth/notifications?role=STUDENT|INSTRUCTOR|ADMIN` đều trả **HTTP 200**. Response khi đó có `success: true`, `items`, `total: 5`, unread lần lượt `0`, `3`, `2`, `page`, `per_page`, và `preferences` ở cùng top-level; không có `data` wrapper. Mọi item mẫu serialize `deleted_at: null`. Student có `COURSE_ANNOUNCEMENT` nhưng category `ASSESSMENT`; Instructor có cùng nội dung MIDTERM dưới `ASSESSMENT_SUBMITTED` và `COURSE_ANNOUNCEMENT`; Admin có cùng nội dung CS301 dưới `COURSE_APPROVAL_REQUEST` và `COURSE_ANNOUNCEMENT`. Đây là semantic/identity drift không thể phát hiện chỉ bằng việc popup hiển thị được. Probe sau đó xác nhận thêm broadcast mới và double-click behavior trong phần continuation.

## Current live enrollment replay (2026-10-05)

Student4 logged in through the real Student catalog, selected DSA201, confirmed `Xác nhận ghi danh môn học`, and saw the `Đã ghi danh thành công` feedback plus the catalog state `Đã ghi danh`. The Student notification center showed the new `Đăng ký khóa học thành công` item. Instructor2 then logged in through the real Instructor dashboard; the dashboard count changed to 3 students and the notification center showed `Học viên mới tham gia khóa học` with the student/course details.

SQL Server correlation found fresh enrollment `110003` for `student4@pwd301.local` / DSA201 with `status=ACTIVE`. New `STUDENT_ENROLLED` events `140010` and `140011` each had a linked Notification: `150083` to `instructor2@pwd301.local` with action URL `#/instructor/courses/manage?id=...`, and `150084` to `student4@pwd301.local` with action URL `#/student/courses/detail?id=...`. This closes the fresh live Browser + SQL Server enrollment recipient correlation. Historical OPS401 rows with zero linked notifications remain a persisted repair gap and are not retroactively treated as fixed.

## Current live course-change rejection correction (2026-10-05)

The live Browser workflow now covers both sides of the course-review family. Instructor1 edited the approved CS201 lesson, published the staged description update, submitted change request `#60002`, and saw the pending state lock. Admin opened the real review page, entered the rejection reason `Vui lòng bổ sung ví dụ minh họa trước khi áp dụng.`, and completed `Từ Chối Bản Sửa`. The Admin queue returned with no pending change request. Instructor1 then logged in again and the notification center showed `Đợt cập nhật khóa học #70014 cần chỉnh sửa lại` with the exact reason.

Read-only SQL Server correlation for request `60002` returned `status=REJECTED`, `requested_by_user_id=2`, `reviewed_by_user_id=1`, the exact review reason and a review timestamp. Event `140009` was `COURSE_CHANGE_REJECTED`, targeted user `2`, and linked to notification `150082` for `instructor1@pwd301.local`. This is a current live Browser + SQL Server rejection/owner-notification pass; historical enrollment orphan rows, upload/download, email, duplicate/idempotency and logout-modal gates remain separate.

The `#60002/#60003` live rejection runs exposed a contract defect: the pre-fix notification title/body and event payload used internal numeric course ID `70014` (`#70014` and `#/instructor/courses/manage?id=70014`) instead of the course public UUID. The CTA still resolved to CS201 because the route resolver accepted the internal ID, but the user-visible technical identifier violated the privacy/UX invariant. Source tracing identified `src/pwd301/blueprints/admin/routes.py:2337-2346` as the changeset-specific producer that formatted `target_req.course_id`; the neighboring service producer already used `course.public_id`.

The current-worktree fix was then verified live: Instructor1 resubmitted request `#60004`, Admin rejected it through the real Browser review page, and the owner notification rendered `Đợt cập nhật khóa học CS201 cần chỉnh sửa lại` with the exact reason. The Browser CTA opened `#/instructor/courses/manage?id=06a1a28d-667a-4d31-b5c9-edefc2885d91`. SQL Server returned request `60004` as `REJECTED`, event `140017`, notification `150090`, and the matching public UUID/action URL. The identifier-leakage gate is fixed in the current source; the older `70014` rows remain historical evidence.

## Current continuation evidence — prerequisite decision workflow

The live Browser workflow was continued with the explicitly enabled demo accounts. `instructor2@pwd301.local` logged in successfully through the Browser, opened DSA201 academic settings, and approved request id `1` for `OPS401` to use DSA201 as a prerequisite. The Browser showed the success toast; authenticated API/DB follow-up showed `APPROVED`, the `OPS401 -> DSA201` prerequisite link, and an Instructor1 `COURSE_PREREQUISITE_APPROVED` notification.

For the rejection branch, Instructor1 created request id `2` from the Browser for `PY301` to use DSA201. Instructor2 Browser displayed the request and opened the native rejection prompt. The prompt could not be completed reliably by the Browser automation session, so the final rejection was executed through a separate authenticated session with a fresh CSRF token and verified as `REJECTED`; Instructor1 received `COURSE_PREREQUISITE_REJECTED`. The Browser prompt/submission path remains partial, not a full Browser PASS.

## Additional browser workflow evidence (continuation)

The login permission was subsequently exercised for the demo accounts, so the earlier browser gate is no longer the current blocker. The following flows were observed in the same local runtime:

| Role | Workflow | Direct result | Audit status |
|---|---|---|---|
| Instructor view of Student demo | Create valid course `AUDIT1004` | Course created and route changed to manage page; success toast shown | PASS for create path; test data side effect |
| Instructor view | Create learning unit and lesson draft | Empty unit name was rejected; valid unit was created; lesson draft saved | PASS for validation/save path |
| Instructor view | Submit course for review | Confirmation dialog appeared; after confirmation course status became `Chờ duyệt` and editing was frozen | PASS for sender-side state |
| Instructor view | Rút lại xét duyệt để mở khóa upload | Confirmation appeared; after confirmation `AUDIT1004` returned to `Bản thảo` and edit/upload controls reappeared | PASS for cancel/unlock path; changes local audit state |
| Admin demo | Review submitted course on live runtime | Admin course queue displayed `0 Khóa học chờ duyệt` and no approve/reject control | FAIL/UNVERIFIED live cross-role visibility; no live approval post-condition |
| Disposable corrected Admin runtime | Login, queue, approve, reset fixture, request-edit/reject | Browser showed `ADMIN CHÍNH`, 1 pending `CS301`, approval toast and queue 0; after fixture reset, request-edit/reject toast and queue 0; DB showed `APPROVED` then `DRAFT` | PASS for corrected disposable authorization/decision paths; not a live-runtime repair |
| Instructor demo | Load sample exam and publish | Sample loaded with 4 questions; publish confirmation appeared; success toast said 4 questions were saved and published | PASS for publish path |
| Student demo | Waiting room and start exam | Pledge checkbox enabled start; attempt route opened, but fullscreen lockdown immediately recorded 1 violation | PARTIAL; browser fullscreen capability not accepted |
| Student demo | Autosave and submit | Two answers showed `Đã lưu tự động`; submit confirmation appeared; result page showed 100/100 and 2/2 correct | PASS for submit/result path |
| Student demo | Export result PDF | Click did not yield a verifiable download/result; CDP input dispatch timed out and page remained unchanged | NOT VERIFIED; not counted as pass |
| Student demo | Enrollment | Confirmed OPS401 enrollment; success toast appeared; dashboard/course list increased to 3 enrolled courses | PASS for enrollment state; duplicate/capacity path not run |
| Student demo | Course resource download | Authenticated HTTP session returned HTTP 200, `application/pdf`, 1,213 bytes and attachment disposition; browser click produced no file and Edge blocked direct navigation with `ERR_BLOCKED_BY_CLIENT` | BACKEND PASS; browser UI NOT VERIFIED |
| Instructor view | Course cover upload | Real `input[type=file]` accepted image MIME types and was enabled, but Edge file chooser rejected `setFiles` with `Not allowed`; extension file-URL permission was not changed | BLOCKED BY BROWSER PERMISSION; product upload result unverified |
| Student demo | Notification pagination and role query | Page 1/page 2 (`per_page=2`) có zero ID overlap; query `role=ADMIN` vẫn trả notification của Student và không lộ broadcast Admin | PARTIAL; không thấy cross-user leak, nhưng semantics của role parameter chưa rõ |

These mutations are test data, not product-code changes: course `AUDIT1004`, one learning unit/lesson, one published sample assessment, một broadcast Admin-only hợp lệ và một broadcast double-click đã được tạo trong local runtime. The course was later returned from `SUBMITTED_FOR_REVIEW` to `DRAFT` to expose upload controls. A separate disposable database `PWD301_AUDIT_ADMIN_20261004` was created, migrated, seeded, approved/rejected through Browser, and removed after evidence capture. Earlier notification mark-read/delete probes cũng thay đổi seeded demo notification state.

## Latest security-notification correction (2026-10-05)

The Admin Browser replay exposed a seeded `SYSTEM_SECURITY_ALERT` containing the raw internal IP `192.168.1.105`. The seed message was changed to describe anomalous administrative login activity without network telemetry. The matching live SQL Server notification was updated in a scoped transaction, and a reload of the Admin notification center showed the safe Vietnamese copy with no raw IP. The regression test and SQL query both report zero remaining matches in the current runtime.

## N-158 - keyed dispatch boundary (2026-10-06)

`dispatch_notification()` now accepts an optional UUID `event_key` and forwards it to `emit_event()`. The focused RED test first failed with an unexpected keyword error; after the minimal service change, an exact retry reused one `NotificationEvent` and one recipient row. The focused notification/flag scope passed **39 passed, 0 failed, 0 skipped**. This closes the shared dispatch API capability only; producer adoption, Browser retry, email and upload gates remain open.

## N-159 - keyed dispatch content-conflict protection (2026-10-06)

The first keyed-dispatch regression exposed a second gap: changing the notification body with the same event key did not conflict because title/body/category were outside the event payload. The shared helper now records a private `_dispatch_contract` in keyed event payloads. Exact retries preserve one event, one in-app row and one email outbox row; changed content raises `ConflictError` before fan-out. Current focused scope remains **39 passed, 0 failed, 0 skipped**. Direct producer adoption and Browser acceptance remain open.

## N-160 - enrollment notification producer keys (2026-10-06)

The `STUDENT_ENROLLED` producer now derives deterministic UUIDv5 keys from the durable enrollment ID and recipient role. Unit verification captured distinct Instructor/Student keys; the disposable SQL Server probe created the real enrollment, replayed both notices through the shared service, and observed unchanged counts of **2 events / 2 notifications** (`3 cases, 0 failed, 0 skipped`). Cleanup returned zero audit databases. The remaining producer catalog and Browser acceptance stay open.

## N-161 - password-change security producer key (2026-10-06)

## N-162 - course lifecycle notification producer keys (2026-10-06)

change_course_status() now flushes the append-only AuditEvent before notification fan-out and derives UUIDv5 keys from audit ID, event action and recipient user ID for course submission, approval and rejection notices. TDD RED reproduced the missing key and GREEN passed the lifecycle key assertions. The disposable SQL Server probe replayed the persisted approval notice and kept event/notification rows at 1 -> 1 (4 cases, 0 failed, 0 skipped); enrollment and password probes also remained green, and cleanup returned zero audit databases. The AST inventory is now 35 calls / 7 explicit keys / 1 prebuilt event / 27 neither. Browser/CUA retry, external delivery and the remaining unkeyed producers stay open.

## N-163 - course-owner reassignment notification keys (2026-10-06)

The owner-reassignment fan-out now derives one UUIDv5 key per former/new owner from the durable COURSE_OWNER_REASSIGNED AuditEvent. TDD RED reproduced missing event_key values; GREEN passed distinct recipient-scoped keys. The current AST inventory is 35 calls / 9 explicit keys / 1 prebuilt event / 25 neither. This producer has unit evidence only in this increment; a dedicated SQL Server replay and Browser acceptance remain open.

## N-164 - password-reset token notification key (2026-10-06)

reset_password_with_token() now passes the same user ID plus post-mutation auth_version UUIDv5 key used by other password mutation entry points. TDD RED found no NotificationEvent for the expected key; GREEN passed the reset-token test. The SQL Server disposable probe exercised both normal and reset-token mutations and kept event/notification/email rows at 1 -> 1, reporting 6 cases, 0 failed, 0 skipped; cleanup returned zero audit databases. The AST inventory is now 35 calls / 10 explicit keys / 1 prebuilt event / 24 neither. Browser acceptance and external email receipt remain open.

## N-165 - account-suspension security notification key (2026-10-06)

suspend_user() now keys ACCOUNT_SUSPENDED with a UUIDv5 derived from user ID and post-suspension auth_version. TDD RED found no event for the expected key; GREEN passed the suspension unit test. The SQL Server disposable probe exercised suspension and exact replay, keeping event/notification/email rows at 1 -> 1 in the combined 9-case probe with zero failures/skips; cleanup returned zero audit databases. The AST inventory is now 35 calls / 11 explicit keys / 1 prebuilt event / 23 neither. Browser and external inbox acceptance remain open.

`change_password()` and `set_password()` now derive a UUIDv5 key from the user ID and post-mutation `auth_version`. Unit RED/GREEN captured the key, and the SQL Server disposable probe verified a real password mutation plus exact notification replay kept **1 event / 1 notification / 1 email outbox** unchanged (`3 cases, 0 failed, 0 skipped`). The disposable database and server were cleaned; other producers and Browser acceptance remain open.

## N-166 - durable producer key expansion (2026-10-06)

Role mutations now use post-mutation `auth_version` keys; Admin course edits and lesson/course change requests use durable audit/change-request IDs; malware rejection notices use persisted file-revision IDs. TDD RED/GREEN evidence passed for the sampled boundaries and Ruff passed. The AST inventory is now **35 direct calls / 25 explicit keys / 1 prebuilt event / 9 neither**. These four boundaries have unit/API evidence only in this increment; dedicated SQL replay, Browser/CUA acceptance, external inbox delivery and the remaining nine producer decisions remain open.

## N-167 - complete producer key coverage (2026-10-06)

The remaining assessment-result, YouTube-health, Admin change-request and instructor prerequisite/lesson route producers now use deterministic UUIDv5 keys. Focused regression groups passed: attempt service 13, change-request/prerequisite API group 28, and the combined service group 79; all reported zero failures and zero skipped tests. Ruff and compile checks passed. AST now reports **35 direct calls / 34 explicit keys / 1 prebuilt event / 0 neither**. SQL Server exact replay for this final producer sweep, Browser/CUA acceptance and external inbox delivery remain open.

## N-168 - full verification with disposable SQL Server (2026-10-06)

The aggregate `scripts/verify.ps1` completed with fresh disposable SQL Server databases: repository contract, compile, Ruff format/lint, mypy, frontend and pytest all passed; pytest reported **1607 passed, 0 failed, 0 skipped** in 1291.34 seconds, including the four SQL Server migration/concurrency/revision cases. The disposable databases were dropped and the live `PWD301` database was not targeted. `git diff --check` passed with only existing LF/CRLF warnings, and the current AST inventory is **35 direct calls / 34 explicit keys / 1 prebuilt event / 0 neither**. Browser/CUA visual acceptance, external inbox delivery, file chooser/quarantine and historical duplicate disposition remain open; the audit remains PARTIAL.

## N-169 - live email outbox and worker boundary (2026-10-06)

Read-only SQL Server inspection of the live `PWD301` database found **115 PENDING** rows in `dbo.email_deliveries`, oldest `2026-09-19 07:47:38.210`, all with `attempt_count=0`; `dbo.background_jobs` had **0 rows**. Source tracing found `enqueue_email()` persisted the outbox but no worker deployment existed in Compose, and the non-testing default transport was `MockMailClient`. The remediation adds due-outbox job bridging, a dedicated `scripts/run_worker.py` plus Compose worker service, a fail-closed SMTP adapter, and stale-queue health reporting. Scoped tests passed **41**, Ruff/mypy/compile and Compose config passed. Live worker activation remains pending because `MAIL_HOST`/`MAIL_FROM` are not configured; current `/health/deep` truthfully reports mail queue `DEGRADED`.

## N-170 - current Computer Use and final verification boundary (2026-10-06)

Fresh Computer Use revalidation returned `apps=[]` and `browsers=[]`; a direct `createBrowserTab("iab", "http://127.0.0.1:5000")` attempt returned `Browser is not available: iab`. This is an environment blocker, not a Browser PASS, so live UI login, file chooser, visual toast/modal, rapid retry and download-finalization evidence remain unverified in the current environment. The current full verifier nevertheless completed with **1612 passed, 0 failed, 0 skipped**; both disposable SQL Server databases were removed. `docker compose build worker` passed, but `pwd301_worker` was not started without approved SMTP configuration. The audit remains PARTIAL and is not release-accepted.

## N-171 current live-data classification (2026-10-06)

Read-only SQL classification found 143 events, 168 linked notifications, 115 pending email rows, zero repeated event keys and zero orphan events. Fourteen repeated presentation-copy groups remain; known `change_request_id` values do not repeat, but legacy action-URL/NULL-payload rows lack enough identity for safe historical deletion. The live database was left unchanged; disposition requires owner-approved mapping and a disposable repair rehearsal.

## N-172 current API envelope correction (2026-10-06)

Source and focused runtime verification closed the sampled web-session envelope drift: `/auth/notifications` and its mutation routes plus `/student/notifications` now return canonical `success/data` while preserving compatibility aliases. RED/GREEN evidence is current: **16 notification API tests**, Ruff and compile passed; the focused frontend notification/PDF set passed **7 tests**. This is scoped API evidence, not Browser acceptance or a full post-patch aggregate claim.

## N-173 final post-patch verification (2026-10-06)

The correctly provisioned SQL-enabled aggregate completed **1613 passed, 0 failed, 0 skipped** with exit code 0 in 1246.07 seconds; all four SQL Server opt-in cases ran and the two disposable databases were removed. This is the current automated baseline after N-172. Browser/CUA and external delivery evidence remain separate gates.

## N-174 acceptance-scope decision (2026-10-06)

The owner confirmed that SMTP/inbox is not deployed and may be excluded from this acceptance cycle. No SMTP/inbox claim is made and the worker remains stopped. This does not waive the mandatory Browser/CUA gate: the current revalidation still returns `apps=[]`, `browsers=[]`, so UI login, file chooser and quarantine behavior remain unverified.

## N-175 Browser role discovery evidence (2026-10-06)

Edge Browser Use became available and real demo UI flows were executed for Student, Instructor and Admin. Login and logout toasts rendered in Vietnamese. Instructor notifications showed 15 unread items, repeated `#70014` presentation copies and mixed-language legacy text; marking all read changed the visible count to 0 and showed a success toast. Admin Operations rendered live `5/6 Node Hoạt Động`, `Email Outbox Delivery Queue DEGRADED` and zero queued/running/failed/succeeded background jobs. Student navigation to `/admin/operations` returned to the dashboard with a permission warning.

## N-176 file and quarantine Browser boundary (2026-10-06)

Student Browser UI listed four course resources and `downloadMedia` completed for a clean PDF. Read-only live SQL showed file revisions only in `ACTIVE` (123) and `REJECTED` (7), with no current `PENDING` or `QUARANTINED` row. A rejected-file URL attempt returned Browser `ERR_BLOCKED_BY_CLIENT` before an application response, so it is not counted as a verified 403. The file chooser event was captured, but Edge `setFiles` returned `Not allowed`; the extension requires `Allow access to file URLs`. Upload/quarantine acceptance remains open.

## N-177 Student notification Browser evidence (2026-10-06)


The Student notification dropdown rendered `0 mới`, category filters and the role label `Học viên`. It showed Vietnamese exam/course messages alongside legacy English/mixed-language strings such as `Thong bao bao tri dinh ky` and user-entered short messages. This is direct UI evidence of language/content inconsistency, not a source-only inference.
## N-178 Browser upload revalidation and quarantine boundary (2026-10-06)

The Edge file chooser now accepted the clean fixture `E:\PWD301\frontend\assets\img\octopus_ai_icon.png`. The Instructor course-management UI opened the crop dialog; applying it produced the toast `Đã cập nhật ảnh đại diện khóa học.` Read-only SQL Server verification found the new `COURSE_IMAGE` asset `22F39CA6-09A9-478A-BB73-8E250FEAE622` with revision `150036` in `ACTIVE`, current revision `1`, detected MIME `image/jpeg`, and both `FILE_VALIDATION` and `MALWARE` scan results `PASS` from the built-in validators. No malicious fixture was uploaded. A direct rejected-file URL still returned Browser `net::ERR_BLOCKED_BY_CLIENT` before the application response, so unsafe-file denial remains unverified.
## N-179 rejected-file route classification (2026-10-06)

The course-scoped inline route was also blocked by Edge with `net::ERR_BLOCKED_BY_CLIENT` before an application response. SQL Server shows the sampled rejected asset `3EB32DEA-150D-4724-B42C-2FEBB53BAD16` as asset `PENDING` with revision `REJECTED` (`Infected: ZIP-Embedded-Executable`), belonging to published course `SEXGAY`, but with no `lesson_resources` attachment. Consequently there is no Student resource card to observe for this historical row; no HTTP 403 or quarantine UI pass is claimed.
## N-180 authenticated rejected-file recheck (2026-10-06)

The rejected-file route was retried from the already authenticated Instructor tab, using the Instructor download path and `disposition=inline`; Edge still returned `net::ERR_BLOCKED_BY_CLIENT` before the application response. The tab was restored to the course-management page afterward. This rules out missing session authentication as the explanation for the Browser evidence gap.
## N-181 Instructor system-category Browser evidence (2026-10-06)

The authenticated Instructor dropdown was filtered to `Hệ thống`. The UI narrowed the list to exactly two records: the legacy mixed-language maintenance message and the Vietnamese malware-rejection message. The filter was then closed without mutating notification state; this is direct category-rendering evidence, not a correctness approval for either historical message.
## N-182 Instructor assessment-category empty state (2026-10-06)

The authenticated Instructor dropdown was filtered to `Khảo thí`; the UI rendered the explicit empty state `Không có thông báo nào` and `Bạn đã xem hết các thông báo trong mục này.` No fabricated assessment notification appeared.
## N-183 Instructor course-category Browser evidence (2026-10-06)

The authenticated Instructor `Khóa học` filter rendered 16 records. The visible set includes course/lesson approval and rejection messages plus three closely related `#70014` rejection copies with different reasons. The dropdown was closed without mutation.

## N-184 Admin broadcast validation and no-write check (2026-10-06)

The authenticated Admin Browser flow opened `#/admin/governance` and the `Phát thông báo` modal. Submitting an empty form rendered `Vui lòng nhập tiêu đề thông báo.`; filling only the title and submitting rendered `Vui lòng nhập nội dung thông báo.`. The modal was then canceled. A read-only query inside the running web container observed `143` notification events, `168` notifications, `115` `PENDING` email deliveries and `0` background jobs; the newest event was `2026-10-05 14:45:45.532 UTC`, before the validation probe. This is a client-validation/no-write pass only; valid broadcast delivery and SMTP/inbox remain out of scope by owner decision.

## N-185 rejected-file resource availability (2026-10-06)

Read-only SQL Server inspection found all seven current `REJECTED` file revisions have `resource_links=0` in `lesson_resources`; each asset remains `PENDING` with a recorded malware rejection reason. Therefore no rejected/quarantined file is reachable from the Student resource panel in the current dataset. The Browser fail-closed denial remains unverified without a safe attached fixture; no quarantine override or malicious upload was performed.

## N-186 authenticated HTTP fail-closed evidence (2026-10-06)

A real authenticated `instructor1@pwd301.local` HTTP session requested the rejected asset route and received `403` JSON with `success:false`, `error.code=FILE_INFECTED`, and the safe message `File revision is rejected due to malware detection.`. This closes the backend/API fail-closed boundary for the sampled asset; the Browser UI route remains blocked by Edge before the application response.

## N-187 owner scope correction for SMTP/inbox (2026-10-06)

The owner confirmed SMTP/inbox is not deployed and may be excluded from this acceptance cycle. Email delivery is therefore recorded as **scope-excluded**, not as a passed delivery test; the live outbox health/backlog remains an operational observation only.

## N-188 historical duplicate reclassification (2026-10-06)

Read-only SQL reclassification kept 14 exact presentation-copy groups but correlated 12 groups to distinct durable business transitions: course-change request/review timestamps or one-to-one `FILE_REJECTED` to `REJECTED` revision matches. The file correlation is exact: 7 `FILE_REJECTED` events, 7 rejected revisions, 7 unique matches, 0 ambiguous extras, with a maximum timestamp delta of 10ms. The only fully unkeyed groups are 13 legacy `LESSON_CHANGE_REQUEST` rows (60002-60014) and four older Lesson-approval rows (70002/70003/70004/100006). No live row was deleted, hidden or merged; the remaining 17 rows require owner mapping before repair.

## N-189 Browser quarantine-override form validation (2026-10-06)

The authenticated primary-admin Browser session opened the real `Bảo mật & Nhật ký` page and displayed the `Giải phóng Tệp Cách ly` control. The modal required a File Asset ID, a security justification and the Super Admin password. Submitting the empty form returned `Vui lòng nhập File Asset ID.`; the modal was then canceled. No password was entered, no override was submitted and no file or audit row was mutated. This proves the UI validation branch only; it does not prove a quarantined-file release.

## N-190 focused quarantine backend regression (2026-10-06)

The focused backend checks passed: `tests/api/test_admin_backend_completion.py` plus `tests/test_admin_security_remediation.py -k quarantine_override` returned `2 passed, 34 deselected`; `tests/security/test_file_authorization_idor.py -k fail_closed_on_quarantined_or_infected_file` returned `1 passed, 11 deselected`. These are focused regression results, not a replacement for the full suite or a live release operation.

## N-191 Browser console observation (2026-10-06)

After the current Browser flows, the captured console contained no application error; the only warning was the existing Tailwind CDN production-use warning. This is an observation, not a notification acceptance gate.

## N-192 legacy identity deep check (2026-10-06)

The 17 unkeyed legacy notifications were checked at event level. Their `target_id` is only the recipient user, `correlation_id` is NULL, `actor_user_id` is NULL, and the payload contains only a generic action URL. A read-only `audit_events` query over the exact event window returned no corresponding audit record. This adds evidence for the safety hold but does not create a business identity.

## N-194 rejected-file Browser client boundary (2026-10-06)

A fresh Edge tab targeting the existing rejected-file URL rendered the browser-owned error page `This page has been blocked by Microsoft Edge` with `ERR_BLOCKED_BY_CLIENT`, before an application response. The IAB fallback returned `Browser is not available`. This is environment evidence and must not be reported as an application HTTP 403 or a Browser UI denial pass.

## N-195 download-route family recheck (2026-10-06)

The same Edge client block reproduced on the API download route `/api/files/<asset>/download`, not only the Instructor route. Both file-response paths are therefore blocked before application handling in this Browser surface.
## N-196 exact business-window recheck (2026-10-06)

A further read-only SQL Server check searched `course_change_requests` in the exact event windows for the 13 unresolved `LESSON_CHANGE_REQUEST` copies (2026-09-28 03:10:04-03:16:28 UTC) and the four unresolved `COURSE_CHANGE_APPROVED` copies (2026-09-28 05:44:15-05:44:22 UTC and 2026-09-29 02:09:31 UTC). It returned no rows in those windows. Current CS101 change-request rows exist at other times, but none can be safely joined to these notifications from the stored recipient-only target, NULL correlation/actor fields and generic action URLs. This is additional evidence for an owner-approved mapping/rehearsal hold; no append-only history was mutated. Final status remains **PARTIAL - not release-accepted**.
## N-197 Browser fail-closed resource-visibility proof (2026-10-06)

Using the enrolled Student Browser session, a temporary, explicitly labeled `lesson_resources` row `120002` was attached to published SEXGAY lesson `130025` and pointed at existing asset `3EB32DEA-150D-4724-B42C-2FEBB53BAD16`. SQL identified the asset as `PENDING` with current revision `REJECTED`, reason `Infected: ZIP-Embedded-Executable`. The real Student `Tài liệu` panel still rendered only the four ACTIVE files and exposed no link, preview or download CTA for the rejected resource. A direct Student-scoped URL was separately attempted and Edge returned `net::ERR_BLOCKED_BY_CLIENT` before an application response, so the UI omission is the verified Browser fail-closed result and the direct response remains environment-blocked. The temporary resource row was then deleted by exact ID and label; SQL verified the lesson returned to four resource links, the rejected asset remained `PENDING`, its revision remained `REJECTED`, and it had zero resource links. No file revision, quarantine state, notification row or audit record was mutated. Final status remains **PARTIAL - not release-accepted** because direct Browser response observation and historical owner-approved notification disposition remain open.
## N-198 acceptance checkpoint after temporary Browser fixture (2026-10-06)

The temporary Browser fixture proves the Student-facing file-visibility branch: a linked `PENDING/REJECTED` asset was omitted from the real Student resource panel, while the four `ACTIVE` files remained visible. Exact cleanup restored the lesson to four resource links and left the asset/revision unchanged. Therefore Student UI fail-closed visibility is **PASS for this sampled asset**; the direct download response remains **BLOCKED ENVIRONMENT / UNVERIFIED** because Edge intercepts the URL before the application response. SMTP/inbox remains **OUT OF SCOPE** by owner decision. Historical notification disposition remains open for the two unkeyed groups/17 rows, so the overall audit remains **PARTIAL - not release-accepted**.
## N-199 historical outbox identity recheck (2026-10-06)

Read-only SQL Server inspection found one `email_deliveries` row for each of the 17 unresolved notification events. Those rows preserve recipient email, template code, random dedupe UUID and `PENDING` status, but have NULL subject/body and no `course_change_request_id`, target resource or correlation field. This provides no additional safe business identity for historical repair. SMTP/inbox remains owner-authorized **OUT OF SCOPE**; no delivery was attempted and no outbox/history row was mutated. Final status remains **PARTIAL - not release-accepted**.
## N-243 current dispatcher identity inventory (2026-10-06)

An independent AST scan over current `src/pwd301` Python source (excluding graphify cache artifacts) found **35** direct `dispatch_notification()` calls: **34** with `event_key`, **1** with a prebuilt `event`, **0** missing identity, and no parse errors. This confirms static identity adoption only; semantic correctness and runtime retry/race behavior remain separate gates.

## N-242 producer-heavy service regression group (2026-10-06)

The fresh command `PYTHONPATH=src python -m pytest -q tests/unit/test_authorization_service.py tests/unit/test_notification_service.py tests/unit/test_email_service.py tests/unit/test_completion_service.py tests/unit/test_instructor_application_service.py` returned **64 passed in 53.59s**, exit code `0`, with no skipped tests. This adds fixture-level evidence for authorization, notification core, email/outbox, completion and instructor-application producers; it does not claim complete runtime producer/role/retry coverage.

## N-241 current Admin lesson-flag reconciliation (2026-10-06)

The current source inspection found both Admin lesson-flag routes calling the shared `flag_lesson_content()` service with the supported arguments; no current `payload_json` constructor defect was found. The fresh command `PYTHONPATH=src python -m pytest -q tests/api/test_admin_lesson_flag_notification.py` returned **9 passed in 7.28s**, exit code `0`, with no skipped tests. The older P1 RCA-040/RCA-027 text remains historical traceability, not a current open defect.

## N-240 fresh API and frontend notification regression (2026-10-06)

The fresh command `PYTHONPATH=src python -m pytest -q tests/api/test_notification_api.py tests/security/test_notification_idor.py` returned **23 passed in 15.20s**, exit code `0`, with no skipped tests. The fresh command `node --test tests/frontend/*.test.js` returned **108 passed, 0 failed, 0 skipped, todo 0**, exit code `0`. These are current API/IDOR/UI regression results, not complete semantic producer, Browser file/quarantine or SMTP/inbox coverage.

## N-239 fresh Admin notification filter matrix (2026-10-06)

The follow-up Edge replay selected each visible Admin notification filter with a stable locator. The observed counts were `Tất cả=15`, `Chưa đọc (0)`, `Khảo thí=1`, `Khóa học=11` and `Hệ thống=3`. The first N-237 observation had opened the existing `Hệ thống` view, so its 3-record observation was a scoped category view rather than the Admin total. No delete, dismiss, mark-read or refresh mutation was invoked.

## N-237 fresh Admin notification-center replay (2026-10-06)

After a fresh demo Admin login in Edge, the real notification center rendered `Thông báo 0 mới`, `Chưa đọc (0)`, role `Quản trị viên`, and three persisted records: two system items (maintenance and completed backup) plus one security item about an abnormal administrator login. The popover was inspected without delete, dismiss, mark-read or refresh mutation. This confirms the Admin role can render persisted notifications; it does not prove every Admin producer or broadcast workflow.

## N-238 fresh Guest protected-route boundary (2026-10-06)

After Admin logout, a direct Browser navigation to `#/student/notifications` ended at `/auth` and rendered only the login surface; no authenticated topbar notification control was present. This is a Guest route-boundary observation, while unauthenticated API `401` behavior remains covered by the automated/API evidence. SMTP/inbox delivery remains explicitly out of scope by owner decision.

## N-250 YouTube Browser/UI ownership gap (2026-10-06)

Fresh Edge Instructor verification opened real course management and Lesson Studio. Course management exposed no scan-video control; source search found `scanCourseVideos()` only in `frontend/assets/js/api.js` with no frontend caller. Lesson Studio did expose the YouTube/Vimeo link input, and an invalid URL produced the Vietnamese validation toast `Chỉ chấp nhận liên kết YouTube hoặc Vimeo hợp lệ.` without saving data. The route/API producer is therefore verified separately but has no demonstrated Browser action owner; the UI ownership gap remains open.

## N-249 disposable YouTube route/API extension (2026-10-06)

The same in-memory probe now exercised the route boundary: unauthenticated `POST /instructor/courses/{public_id}/scan-videos` returned **401**, while an authenticated Instructor owner received **200**, `success=true` and `broken_count=1`. Replaying the route and service left one durable event and one owner notification. This closes the disposable service/API path only; Browser UI presentation remains separate.

## N-248 disposable YouTube producer service/DB replay (2026-10-06)

The new disposable probe `youtube-runtime-probe.py` ran against an in-memory SQLite database and completed with exit code `0`: valid oEmbed produced 0 reports, network-error suppression produced 0 reports, a mocked broken video produced 1 report, and an exact replay still left **1** `COURSE_LESSON_VIDEO_BROKEN` event and **1** owner notification. SQLAlchemy assertions confirmed the event target and notification recipient were the course owner and category `COURSE`. The probe dropped its schema; no live data changed. Route/API/Browser UI coverage remains open.

## N-247 YouTube broken-video producer coverage gap (2026-10-06)

Read-only source/test inventory found the live `COURSE_LESSON_VIDEO_BROKEN` producer in `src/pwd301/services/youtube_validator_service.py` and the Instructor scan route, but no test file currently covers `scan_and_notify_broken_youtube_videos`, `/courses/<course_id>/scan-videos` or the resulting recipient notification. The UUIDv5 key has durable course/lesson/video/instructor inputs, but valid/broken/network-error behavior and DB/user-result correlation remain **UNVERIFIED**.

## N-246 producer-key semantic-shape AST inventory (2026-10-06)

An independent AST scan of current Python source classified all **35** direct `dispatch_notification()` calls: **34** explicit `event_key` expressions contained durable-identity candidates, **0** contained random/clock markers, **0** were constant or unclassified expressions, and **1** used a prebuilt `event` in `src/pwd301/services/course_service.py:286`. This is static key-shape evidence only; it does not prove recipient semantics, message ownership, concurrent convergence or historical-row repair.

## N-245 fresh Student notification-center content/filter replay (2026-10-06)

After a fresh demo Student login in Edge, the login-success toast rendered in Vietnamese and the notification center opened immediately from the dashboard. The visible read-only filters yielded `Tất cả=13`, `Khảo thí=7`, `Khóa học=2`, `Hệ thống=4`, with `Chưa đọc (0)`. The Browser also exposed current user-facing content such as the unaccented `Thong bao bao tri dinh ky He thong PWD301 hoat dong on dinh tren tat ca cac module.`, plus seeded low-value strings `heo peppa caccaccac` and `bucutaodi thật là bá khí`. No delete, mark-read, refresh, upload or other business mutation was invoked; Student was logged out afterward. This is fresh Browser evidence of content-quality/taxonomy defects and filter behavior, not proof of the full backend/DB chain for each row.

## N-244 grading/regrade producer-service regression (2026-10-06)

The fresh isolated command `PYTHONPATH=src python -m pytest -q tests/unit/test_grading_service.py tests/unit/test_regrade_service.py` returned **25 passed in 26.49s**, exit code `0`, with no skipped tests. This strengthens grading and regrade producer-side regression evidence only; it does not close complete semantic producer/role/retry coverage, Browser file/quarantine verification, historical owner approval or SMTP/inbox scope. Overall status remains **PARTIAL - not release-accepted**.

## N-200 stale identity/content recheck (2026-10-06)

The unresolved notification bodies do contain coarse labels: all 13 `LESSON_CHANGE_REQUEST` copies name CS101 and Lesson `Bài 1: Tổng quan về Kiến trúc Web & HTTP Protocol`, but none stores a change-request ID, durable target ID or correlation. The four `COURSE_CHANGE_APPROVED` copies name the same Lesson but their CTA points to course UUID `cf547469-d8b8-43ef-882c-721048826232`, which is absent from the current `courses` table; the current CS101 row has a different public UUID. Current CS101 change-request rows exist, including multiple historical candidates for the same lesson, but none matches the notification event windows. This confirms stale/missing business identity rather than an unresolved title-only query; no historical row was reassigned, deleted or merged. Final status remains **PARTIAL - not release-accepted**.

## N-251 frontend notification mechanism inventory (2026-10-06)

A read-only deterministic parser scanned 10 current `frontend/assets/js/**/*.js` files. It found 383 actual `UI.showToast` invocations (214 quoted literals, 73 template literals, 96 other dynamic expressions, 202 unique quoted literal payloads), 2 `UI.alert`, 30 `UI.confirm`, 8 `UI.prompt`, and 1 legacy `window.confirm`. There were no native `window.alert`, native `window.prompt`, or `<dialog>` usages. Accessibility-related markup included 6 `aria-live` attributes and 4 `role="alert"` attributes. The toast implementation also contains one `toast_` DOM-id marker. Five additional `UI.showToast` references are guard/type checks rather than calls. This is a static mechanism inventory only; it does not prove message ownership, API status handling, role coverage, duplicate convergence, or Browser rendering for every path. Overall status remains **PARTIAL - not release-accepted**.
## N-252 producer execution coverage checkpoint (2026-10-06)

A focused backend/API coverage run executed 312 tests and then 6 additional prerequisite/revision tests; all returned passed with zero failures and zero skips. Three disposable in-memory probes also passed: prerequisite rejection produced one `COURSE_PREREQUISITE_REJECTED` event/notification with no prerequisite link; rejected file revision produced one `FILE_REJECTED` security event/notification with no blob; and the YouTube probe produced one broken-video event/notification while exact replay stayed at one event/notification. AST-to-coverage correlation now shows **35/35 direct `dispatch_notification()` producer callsites executed**, with zero uncovered callsites. This closes producer line-execution evidence only; it does not prove every role, timeout/cancel/unmount, rapid-retry race or live Browser result. Overall status remains **PARTIAL - not release-accepted**.
## N-253 Browser auth-error surface checkpoint (2026-10-06)

Fresh Edge interaction on `#/auth` submitted an invalid email/password pair through the real login form. The page stayed on `/auth` and rendered exactly one visible `#auth-error-alert` with `Email hoặc mật khẩu không chính xác.` after the 6.45-second interaction/observation sequence. It was an inline error, not a shared toast; its DOM markup had no `role` and no `aria-live`. No account or business data was changed. This adds a concrete accessibility/ownership gap to the sampled error surface; it does not generalize to every auth or API error.
## N-254 Browser file-chooser boundary checkpoint (2026-10-06)

The real Instructor Lesson Studio exposed `#btn-choose-doc-file` and two hidden file inputs. A disposable text fixture was prepared, then the supported Computer Use file-chooser flow started its event wait before clicking the visible chooser control. No `filechooser` event arrived; the wait timed out after approximately 3 seconds and the Browser debugger detached. A subsequent inventory still showed `apps=[]` and only Edge. No file selection or upload request was confirmed. This strengthens RCA-042 as an environment/surface blocker, not a product upload pass; the disposable fixture contains no personal data.
## N-255 producer semantic inventory checkpoint (2026-10-06)

The AST semantic pass mapped all 35 direct producers beyond line execution: 34 carry an explicit `event_key` and one passes a prebuilt event; none lacks both. Literal category distribution is COURSE 20, SECURITY 6 and SYSTEM 8, with one dynamic category. Only 17 callsites declare a concrete `target_role` (INSTRUCTOR 13, STUDENT 2, ADMIN 2); the other 18 omit it or pass `None`, relying on broad/unscoped dispatch semantics. Event types are mostly literal, with one dynamic assessment-result path. This is a semantic ownership inventory, not proof that the 18 broad paths are correct for every recipient role or that dynamic messages are localized. Overall status remains **PARTIAL - not release-accepted**.
## N-256 focused role/retry runtime checkpoint (2026-10-06)

The focused semantic group returned **8 passed, 0 failed, 0 skipped in 5.63s**. It covered event-key replay without fan-out duplication, changed-payload conflict rejection, target-role isolation, Student/Instructor enrollment fan-out and persistence, audit-scoped course lifecycle keys, and recipient-scoped owner reassignment keys. This is representative runtime evidence only; the broad/unscoped producer set and full Browser/async matrix remain open.
## N-257 — historical notification approval packet (2026-10-06)

Read-only SQL Server recheck isolated the exact 17 unresolved historical rows:
13 `LESSON_CHANGE_REQUEST` events (`50002–50014`) and four
`COURSE_CHANGE_APPROVED` events (`60002–60004`, `90006`). Each has one linked
notification and one email-delivery row; event keys are unique. The repeated
copy is therefore not proven duplicate delivery. Neither group has a
deterministic request/target/correlation identity, so all rows remain unchanged
pending owner mapping and disposable repair rehearsal. The approval packet is
[`09_HISTORICAL_NOTIFICATION_APPROVAL_PACKET.md`](09_HISTORICAL_NOTIFICATION_APPROVAL_PACKET.md).
SMTP/inbox remains **OUT OF SCOPE**.
## N-258 — second Browser file-chooser recheck (2026-10-06)

Edge was available and the real Instructor Lesson Studio control was visible,
but waiting for `filechooser` before clicking `btn-choose-doc-file` timed out
again after 5 seconds and reset the Browser session. No file was selected or
transmitted. This remains **BLOCKED ENVIRONMENT / UNVERIFIED**, not a pass.
## N-259 — fresh Browser category/content evidence (2026-10-06)

The live Instructor notification popover was opened and closed without mutation.
The `Khóa học` filter rendered 16 cards, including two `#70014` copies with
different rejection reasons, current `CS201` content and older lesson/course
copies. The `Hệ thống` filter rendered the unaccented legacy message
`Thong bao bao tri dinh ky` alongside the Vietnamese malware-rejection notice.
This is direct content/language evidence; it does not prove global catalog
coverage.
## N-260 — refinement of unscoped-role producer semantics (2026-10-06)

The AST follow-up inspected all 18 producers that omit `target_role` or pass
`None`. Every one still supplies an explicit `recipient_user`; this does not
prove a fan-out leak. The actual open boundary is role-view semantics: a NULL
`Notification.target_role` is included when the same account filters by any
role, while several action URLs are Instructor/Admin-specific. Account-level
security and role-change messages may intentionally be broad; prerequisite,
lesson-review, admin-intervention, instructor-application and YouTube paths
need producer-by-producer role/CTA confirmation. This refines N-255 and remains
an evidence gap, not a blanket defect finding.
## N-261 — live multi-role role-filter leakage (2026-10-06)

Read-only HTTP replay logged in as `admin@pwd301.local`, which currently holds
ADMIN, INSTRUCTOR and STUDENT roles. The same public notification
`d553d1ec-547c-4ebc-889d-7c91e274229e` (`LESSON_CHANGE_REQUEST`,
`target_role=null`, CTA `#/admin/change-requests/review?id=50002`) appeared in
all three GET filters: `role=ADMIN`, `role=INSTRUCTOR` and `role=STUDENT`.
Each response was HTTP 200. This confirms a same-user role-view/CTA isolation
defect, not cross-user leakage; no mutation was performed.
## N-262 — notification role-schema contract drift (2026-10-06)

The runtime model and migration `f6a7b8c0d1e2_0009` define nullable
`notifications.target_role`, its role/unread index and a three-role CHECK
constraint. Live SQL Server revision `b3c4d5e6f7a9` confirms all three runtime
objects. The canonical notification data dictionary does not list
`target_role`, that index or the constraint. This is documentation/schema
contract drift that obscures the N-261 role-view semantics; no database object
was changed.
## N-263 — existing role tests do not cover CTA compatibility (2026-10-06)

The focused existing role tests returned **3 passed, 0 failed, 0 skipped in
1.58s**. They prove explicit `INSTRUCTOR`/`STUDENT` rows are isolated and
unsupported role values are rejected, while intentionally treating
`target_role=NULL` as visible to both roles. They do not assert that a NULL-role
row's action URL is compatible with the requested role; live N-261 therefore
remains a real uncovered contract case.
## N-264 — cross-user isolation control recheck (2026-10-06)

Read-only JWT replay for `student1@pwd301.local` returned zero matches for the
Admin-review CTA `#/admin/change-requests/review?id=50002` under the valid
STUDENT filter. INSTRUCTOR and ADMIN filters were correctly rejected with HTTP
400 because this account lacks those roles. This confirms N-261 is same-user
role-view contamination, not cross-user IDOR.
## N-265 — Browser route-guard refinement (2026-10-06)

Source tracing found that notification item/modal handlers pass `action_url`
directly to `AppRouter.navigate()` (`router.js:1615-1649, 1713`). The Admin
route guard then either auto-switches a multi-role account to ADMIN or shows
`Bạn không có quyền truy cập khu vực Quản trị viên.` and redirects to the
current role home (`router.js:299-323`). A fresh Edge tab opened the exact
Admin review target while the current Instructor-only session was active and
visibly showed that warning before landing on `#/instructor/dashboard`; no
business mutation occurred. This confirms the UI does not pre-filter or label
the incompatible CTA. Multi-role auto-switch success remains source/HTTP
scoped, not a fresh Browser pass.
