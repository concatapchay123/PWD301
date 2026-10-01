# Role Switching and Navigation Performance — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This document is planning only; the current request expressly forbids implementation.

**Goal:** Loại bỏ thời gian chờ không cần thiết khi chuyển role/topbar; giảm SQL/payload; bảo toàn authorization, dữ liệu và lifecycle.

**Architecture:** Giữ Flask modular monolith, SQL Server và frontend hiện có. Route/view có mounted root, generation, read cancellation và disposal; auth mutations authoritative. Summary queries bounded, optional AI và notification/KPI không nằm trên đường tải bắt buộc.

**Tech Stack:** Flask, Flask-Login, SQLAlchemy, SQL Server2022, JavaScript/DOM/AbortController, Node test runner, pytest, browser thật.

**Spec:** [Báo cáo baseline/inventory](../../audits/PERFORMANCE_ROLE_NAVIGATION_AUDIT_2026-10-01.md), `docs/system/PWD301_SYSTEM_SPECIFICATION/`, `docs/database/PWD301_DATABASE_ARCHITECTURE/14_INDEX_AND_PERFORMANCE_STRATEGY.md`, AGENTS.md. System/DB canonical contracts có ưu tiên cao hơn implementation hiện tại.

## Global constraints

- Lượt khảo sát hiện tại không sửa code; chỉ thực hiện plan khi có yêu cầu triển khai mới.
- Không tạo backend Jinja/static/prototype layers, schema copy hay infrastructure mới để chữa latency.
- Browser session+CSRF; không JWT localStorage. Suspend/revoke/auth_version/expiry vẫn có hiệu lực ngay; cache không được trả quyền cũ giữa requests.
- Role switch thay perspective của chính user, không grant/revoke role hoặc impersonate.
- File pending/quarantined/scanner unavailable vẫn fail-closed; video strictly <1GB.
- Server exam deadline, active editing lease, autosave sequence, submit idempotency và lịch sử giữ nguyên. Không tự retry/cancel mutations theo chính sách GET.
- Route `/new` thuần đọc; tạo draft chỉ khi hành động chủ động, dùng replaceState khi new→edit.
- Mandatory audit không được chuyển sang best-effort để nhanh hơn. Recommendation telemetry không được làm hỏng pending domain transaction.
- Query/payload contracts phải giữ frontend hiện tại hoạt động hoặc chuyển callers có test và version/summary semantics rõ. Detail/editor không bị rút dữ liệu cần thiết.
- Không tắt expire_on_commit toàn cục, dùng NOLOCK, bật RCSI hoặc tăng pool/workers trước đo/tranh luận tradeoff.
- Thay substantial auth transaction design phải được review/chốt rõ trước Task7; kế hoạch hiện tại chưa thay đổi auth.

## Review focus

1. B đang được yêu cầu khi A treo hoặc reject: B phải chạy, không render hoặc ghi dữ liệu từ A.
2. Đổi account/role hoặc quay lại cùng hash: response/cache của context cũ không được nhận vào context mới.
3. Callback sau mount hoặc route exit: root còn đúng; timer/listener không giữ view cũ, mutation của item A không mang ID B.
4. Gemini/notifications/health chậm hoặc lỗi: primary view vẫn tải; error không giả thành empty success.
5. Batching/summary/heartbeat: giữ object scope, file scan, score release và revocation concurrency; query ít hơn không bỏ kiểm tra.

## Delivery order and gates

Task2/3/4 trực tiếp xử lý những ca đã đo nhiều giây. Task5/6 giảm chi phí mỗi request và scaling risk. Task7/8 kiểm tra shared auth/runtime/cold boot. Có thể review các query-only phần độc lập sau khi baseline và contract rõ; tránh merge đồng thời nhiều tối ưu mà không đo riêng.

### Task 1: Baseline, ownership and query-budget harness

**Files:**
- Create: `tests/frontend/navigation_request_lifecycle.test.js`.
- Modify: `tests/frontend/router_navigation.test.js` (fake DOM phải mô phỏng adoption/remove parent đúng).
- Create: `tests/api/test_navigation_query_budgets.py`.
- Create: `scripts/probe_navigation_performance.py` (chẩn đoán GET, sanitized outputs, không seeding/mutations mặc định).
- Consult: existing auth/analytics/recommendation/security tests và baseline report.

**Interfaces:** Route context đề xuất ở Task2 là `{generation, userId, role, signal, isCurrent(), onDispose(fn)}`; scope chỉ navigation GET/view ownership, không auth permission source. Harness đếm SQL bằng `before_cursor_execute`, warm/cold identity map tách rõ, output duration/query count/body bytes; không logs binds/secrets.

- [ ] Viết tests đỏ: pending recommendation không giữ dashboard; B dispatch trước A resolve; A reject vẫn dispatch B; callback query root sau mount; owner A không persist vào B.
- [ ] Viết query-budget fixtures trên isolated test DB với1/10/50 courses, lessons/resources/attempts; `expire_all` trước đo. Assert cardinality/query behavior thay flaky millisecond assertion trên SQLite.
- [ ] Chạy từng test, xác minh fail đúng cơ chế trong report; không fail do thiếu harness/global sandbox.
- [ ] Chốt baseline fixture/version/card-summary contracts và budgets. Ghi role/account/dataset/cache condition và API/SQL timing riêng.
- [ ] Chạy read-only SQL Server probes và browser matrix; lưu sanitized output. Không tái dùng pass counts cũ như proof mới.

**Acceptance:** Tests đỏ nhận diện đúng lỗi; probe có thể lặp; DB test không trỏ vào live để seed; query counter không bị identity map che N+1.

### Task 2: Latest-route lifecycle and stable mounted roots

**Files:** Modify `frontend/assets/js/router.js`, `api.js`, `ui.js`, `views/student.js`, `views/admin.js`, `views/instructor.js`, `views/instructor-exams.js`; tests Task1 và existing frontend lifecycle tests.

**Interfaces:** `AppRouter.handleRoute()` tạo context mới, hủy reads/dispose view cũ, dispatch ngay latest hash. `dispatchRoute(path, query, root, context)` truyền persistent mounted root/context. `ApiClient.request(endpoint, options)` nhận optional signal/deadline với GET semantics; wrappers giữ compatibility và forward context. Context chỉ sử dụng identity public hoặc existing stable key phù hợp, không expose technical identifiers trong UI.

- [ ] Thêm test đỏ cho hash A→B→A, same hash different account, aborted A failure và B success; no duplicate latest dispatch.
- [ ] Thêm real-DOM/browser tests cho mounted callbacks: waiting room countdown, result filter, empty-password visibility, settings preferences read đúng controls; không submit live credentials/exam.
- [ ] Thêm tests đỏ A→B lesson reordered responses: content/quiz/progress/timer đều gắn captured item; repeated lesson exit không còn iframe intervals/message listeners.
- [ ] Implement generation/read abort/error containment; preserve view root và disposal. Stage có thể giữ anti-flicker nhưng không chuyển children khỏi owning root rồi giữ callbacks trỏ vào stage.
- [ ] Dùng root-scoped queries và context guard ở async admin tabs, question inspector/search/scope loaders. Dispose cả stage bị discard.
- [ ] Cancel/token-check micro-loader timers. Mount destination loading feedback ngay, không chờ optional APIs.
- [ ] Chạy frontend suite và browser ca pending10s/reject/out-of-order; xác minh latest dispatch≤50ms theo proposed budget và primary UI không đứng sau obsolete read.

**Acceptance:** FE-02/03/04/08/13/14/15/19/20/21/22 covered. Aborting navigation không gửi thêm fallback, không tự retry writes. Uncommitted assessment/autosave vẫn tuân guards/lease rules.

### Task 3: Authoritative role switch and notification ownership

**Files:** Modify `frontend/assets/js/router.js`, `api.js`, `views/auth.js`; add/extend `tests/frontend/topbar_navigation.test.js`, Task1 tests; backend auth tests nếu cần contract assertion.

**Interfaces:** `switchRole(target)` vẫn POST có CSRF và server authorization. Client nhận role từ authoritative response; current user/profile refresh chỉ trong phạm vi cần reconcile. Notifications coalesce theo captured account/perspective/generation; cached read không là nguồn auth. Badge count và list refresh có semantics riêng.

- [ ] Tests đỏ delayed notifications không giữ redirect; pending switch disable role actions; failed401/403/network switch không đổi local role.
- [ ] Tests đỏ reverse response order, logout/login B trong request A, stale cache persist; startup/bell/poll có request budget rõ.
- [ ] Implement single in-flight mutation, pending feedback/close menu, accepted role rồi navigate; refresh optional notifications độc lập.
- [ ] Capture identity cho notification fetch/persist; discard stale response, clear appropriate caches ở auth transitions.
- [ ] Dedupe same-context reads, count when bell closed, pause hidden-tab polling; fallback chỉ documented compatibility errors. Không biến lỗi thành empty success.
- [ ] Align login sync `primary_role`/`active_role` với contract hiện có; endpoint chọn perspective từ caller/context thay live hash.
- [ ] Chạy tất cả6 chiều role trên3-role Admin, Instructor-only, Student-only và từng Admin sub-role; test slow/failing notification và switch.

**Acceptance:** FE-05/06/07/09/12/26 covered; rolehome bắt đầu sau switch acceptance dù notifications còn pending; không cache lẫn account/perspective; backend quyền không thay đổi.

### Task 4: Recommendations outside the primary route, with total deadline

**Files:** Modify `frontend/assets/js/views/student.js`, `api.js`, `src/pwd301/services/recommendation_service.py`, `gemini_service.py`, `blueprints/student/routes.py`, `blueprints/api_ai/routes.py`; test `tests/unit/test_recommendation_service.py`, `tests/api/test_student_backend_completion.py`, Task1 frontend tests.

**Interfaces:** Primary dashboard/catalog contracts không phụ thuộc AI explanation. `generate_course_recommendations(actor, limit, session)` vẫn authorization/prerequisite/ranking đúng; deterministic explanation hiện có là fallback. AI enrichment và total request budget cần interface explicit (separate request/optional mode theo contract review), limit capped consistent cho session/JWT routes. Không mặc định thêm queue/service.

- [ ] Test đỏ provider pending10s nhưng dashboard/catalog primary mounted; optional recommendation component có loading/error và route guard.
- [ ] Test đỏ maximum limit/deadline across candidates/model fallback; giữ ranking/prerequisites/archived exclusion/public UUID.
- [ ] Test đỏ DB connection không checked-out trong outbound enrichment sau facts được materialize; telemetry không commit unrelated pending work.
- [ ] Resolve failing `test_zero_internal_pk_leakage_in_recommendations` bằng đối chiếu canonical API alias: assert public UUID/absence internal fields nếu alias hợp lệ; đổi response nếu contract cấm. Không xóa test để tăng pass count.
- [ ] Implement nonblocking-to-primary load, rule-based response và bounded enrichment; release transaction before network, batch telemetry đúng transaction ownership.
- [ ] Measure same fixture before/after: slow Gemini không làm primary route chậm>100ms so với khôngAI; không gọi redundant second endpoint trên auth/abort.
- [ ] Chạy recommendation/AI/API regression, security grounding tests; real provider sample và fake timeout được ghi riêng.

**Acceptance:** FE-01 và BE-06 covered; route không chờ8–16s vì recommendations; deadline tổng có test; telemetry/ranking/security nguyên vẹn.

### Task 5: Bounded course summaries and student/instructor query work

**Files:** Modify `src/pwd301/blueprints/instructor/routes.py`, `blueprints/student/routes.py`, `services/analytics_service.py`, `course_service.py`, `assessment_service.py`, `file_service.py` chỉ phần affected query/summary; frontend `views/instructor.js`, `views/student.js`, `api.js`; Task1 query budgets và existing API/security tests.

**Interfaces:** Course list summary fields chính: public IDs hiện có, title/code/status/category/difficulty/description excerpt/owner summary/thumbnail/số bài/số học viên/scope totals. Summary không mang full markdown, revisions, student roster hay duplicate flat+unit lesson graph. Detail APIs vẫn đầy đủ. Query grouped theo authorized current-page IDs, không ID toàn platform ngoài scope.

- [ ] Test đỏ course-list page query/card bytes bounded khi thêm nhiều lessons/files/students; detail/editor không mất dữ liệu.
- [ ] Test đỏ my-learning không tính upcoming/recent; assessments dùng một batch attempts/results; preserve attempt limit/release policy/IDOR.
- [ ] Test đỏ assigned Admin dashboard dùng COUNT all-school, không materialize all Course; assessment aggregates/faculty workload grouped, không per-row queries.
- [ ] Test đỏ student syllabus safe current revision/scan, single grouping; files pending/quarantined/unavailable scanner không accessible.
- [ ] Implement projections/grouped counts/bounded eager loading và selective overview. Giữ grouped query/pagination đang tốt.
- [ ] Fix frontend question hub duplicate summary, fake-empty roster, sequential read loops; independent studio reads reuse/parallel; page/filter at backend.
- [ ] Compare query counters và bytes tại1/10/50 fixtures; live SQL Server profile cùng role/dataset; xem plan/reads khi cần index, không add speculative indexes.
- [ ] Chạy API/security/student/instructor/assessment suites; không count skipped live SQL thành pass.

**Acceptance:** BE-03/04/05/07/13/14/15, FE-16/17/18/25 covered. Proposed course-list page20≤50KB/≤12 SQL phải được chốt Task1; quan trọng hơn, queries không tăng theo hidden lesson/file/student graph.

### Task 6: Independent Admin tabs and compact authorized queues/counts

**Files:** Modify `frontend/assets/js/views/admin.js`, `router.js`, `api.js`; `src/pwd301/blueprints/admin/routes.py`, `services/user_service.py`, `notification_service.py`; Task1 query/request tests; `tests/api/test_admin_backend_completion.py`, `test_admin_subroles_and_enhancements.py`, `test_notification_api.py`.

**Interfaces:** Selected tab data independent from KPI reads. Reuse existing count/page contract nếu đủ; nếu thiếu, authorized summary counts phải có schema/endpoint and sub-role tests trước implement. Queue summary và detail diff tách; total/pending counters server-authoritative; list/unread notifications có cùng visibility semantics.

- [ ] Test đỏ pending KPI treo nhưng Users/Audit/Reassign mount và request tab bắt đầu; old tab response không cập nhật root mới.
- [ ] Test đỏ burst role/Admin route request dedupe và invalidation sau approve/reject; chỉ một in-flight request cho mỗi same-context queue/summary.
- [ ] Test đỏ page users eager roles/links, applications grouped counters, change requests latest dedupe và detail diff đầy đủ; all sub-role/object permissions.
- [ ] Test notification duplicates/target_role null/expiry/read state; count/list agree. Lấy actual plan/logical reads với history lớn trước thay dedupe/index.
- [ ] Implement bounded summaries/pages/detail-on-demand, batch staged lookups, selected-tab-first và shared summary reuse.
- [ ] Giữ audit logs pagination50 đang có; không giảm append-only audit hoặc history preservation.
- [ ] Verify Admin topbar requests≤documented unique dependency budget, không lặp9 queue calls khi role transition; SQL count/payload giảm với fixture không đổi.

**Acceptance:** FE-10/11/15, BE-09/10/11/12 covered; loader phân biệt core shell và secondary widget, error có retry.

### Task 7: Short auth heartbeat transactions and runtime concurrency

**Files:** Modify only after auth-design review: `src/pwd301/__init__.py`, `services/session_auth_service.py`, `authorization_service.py`, `operations_service.py`; relevant config only if measurements justify; `tests/unit/test_session_auth_service.py`, `tests/security/test_rbac_and_idor.py`, Task1 budgets/live concurrency tests.

**Interfaces:** Auth validation luôn fresh mỗi request; throttled last_seen là observational heartbeat, không permission cache. Request-local JWT memoization scoped đúng token. Public asset bypass phải explicit whitelist phù hợp actual asset/screen/maintenance contract. Health snapshot nếu dùng phải là số thực có timestamp/deadline, không fabricated telemetry.

- [ ] Trình bày transaction/heartbeat design và chốt trước sửa substantial auth; xem canonical auth/session expiry semantics, không tự chọn TTL làm thay đổi security.
- [ ] Test đỏ burst10 safe requests không UPDATE/COMMIT10 lần; revoke/suspend/auth_version/expiry chặn ngay, hai request concurrent không mất heartbeat hoặc commit pending domain write.
- [ ] Test đỏ `/frontend/` public reads không resolve/ghi session; protected downloads vẫn authorize/scan. JWT decorator+view verify đúng một lần trong request, malformed header vẫn fail-closed.
- [ ] Implement conditional bounded heartbeat transaction và public fast path trước current_user; keep fresh authorization checks.
- [ ] Test ClamAV delay/failure không giữ main Operations view; health/telemetry thật, failure status truthful.
- [ ] Đo pool checkout/wait, worker occupancy, SQL waits/locks cùng session burst và AI timeout; Query Store actual plans/reads ở dataset đại diện.
- [ ] Chỉ đề xuất pool/worker/RCSI/index tuning nếu evidence sau code fixes còn cần; RCSI change phải qua lease/enrollment/audit concurrency và tempdb cost review. Không NOLOCK.
- [ ] Run live SQL concurrency probes, auth/security suites và compare before/after cùng request count.

**Acceptance:** BE-01/02/16/17 covered; request reads không kéo thừa transaction writes; session revocation tuyệt đối không regression. Chưa có infrastructure change được quyết định trước bước đo.

### Task 8: Cold startup and full delivery gates

**Files:** Khi có cold evidence: `frontend/index.html`, existing frontend styling/dependency assets/build configuration, router script-loading path; `src/pwd301/blueprints/frontend/routes.py`, `services/analytics_service.py` phụ trợ nếu caller thực cần; tests và diagnostic probe/report.

- [ ] Đo cold cache scripts transfer/compression/parse/longtasks/CDN outages trên desktop/mobile; route warm và cold tách biệt.
- [ ] Test đỏ role/studio script chỉ tải khi cần và đúng dependency order; offline/CDN failure không mất sanitizer hoặc shell.
- [ ] Implement minimal lazy scripts/local pinned sanitizer/compiled styling khi số đo chứng minh; giữ frontend hiện có, không backend templates/prototype.
- [ ] Conditional public screens nếu caller còn dùng; dashboard aggregate/snapshot chỉ theo nhu cầu caller và measured cost. Snapshot có generated_at/invalidation.
- [ ] Test6 role directions cho3-role Admin, Instructor-only, Student-only, từng Admin sub-role; all topbar steady/rapid, network error/reordered responses, multiple user sessions. Browser real-DOM lifecycle tests bắt buộc.
- [ ] Lặp≥30 samples mỗi warm scenario, báo median/p95/sample count; simulate RTT0/50/100/200ms; concurrent normal users và slowAI. Định nghĩa RTT emulator/client điều kiện rõ, không nhầm network tool overhead với application time.
- [ ] Run `./scripts/verify.ps1`, focused frontend suite, SQL Server query/concurrency/migration gates nếu có migration; OCR review nếu LLM endpoint cấu hình. Ghi errors/skips/unrun đầy đủ, không ship bằng hidden fail.
- [ ] Review44 inventory rows: mỗi ID fixed/verified/deferred with owner/trigger/safeguard; update report theo final scope. Measure each optimization separately, revert neutral regressions.

**Acceptance:** FE-23/24 và BE-08/18 evaluated; independent warm performance/security contracts pass. Chưa thể tuyên bố deploy-ready nếu live SQL/auth/role matrix gates còn unrun.

## Verification commands for execution

```powershell
$frontendTests = @(Get-ChildItem tests/frontend/*.test.js | ForEach-Object FullName)
node --test $frontendTests
.venv\Scripts\python.exe -B -m pytest tests/unit/test_session_auth_service.py tests/unit/test_recommendation_service.py tests/unit/test_analytics_service.py tests/security/test_analytics_idor.py -q -p no:cacheprovider
.venv\Scripts\python.exe -B -m pytest tests/api/test_navigation_query_budgets.py -q -p no:cacheprovider
./scripts/verify.ps1
```

Task1 tạo query-budget test file trước command tương ứng. New live probe không có command giả ở đây: interface/flags được chốt khi implementation Task1, sử dụng DB test/live-readonly đúng scope. Tests isolated và actual SQL Server evidence ghi riêng. Git publication không nằm trong kế hoạch này trừ khi người dùng yêu cầu.

## Self-review and deferred decisions

| Task | Explicit finding coverage |
|---|---|
| 2 | FE-02, FE-03, FE-04, FE-08, FE-13, FE-14, FE-15, FE-19, FE-20, FE-21, FE-22 |
| 3 | FE-05, FE-06, FE-07, FE-09, FE-12, FE-26 |
| 4 | FE-01, FE-26, BE-06 |
| 5 | FE-16, FE-17, FE-18, FE-19, FE-25, BE-03, BE-04, BE-05, BE-07, BE-13, BE-14, BE-15 |
| 6 | FE-10, FE-11, FE-15, BE-09, BE-10, BE-11, BE-12 |
| 7 | BE-01, BE-02, BE-16, BE-17 |
| 8 | FE-23, FE-24, BE-08, BE-18 |

- Inventory44 được map qua8 tasks; FE-19 nằm Task2, FE-26 Task3/4, BE-09 Task5/6. Review Focus5 có tests trong các task tương ứng.
- Response aliases/summary endpoints, heartbeat interval và performance budgets phải đối chiếu source-of-truth/fixture trước commit. Đây là các quyết định được đặt đúng gate, không giao việc mơ hồ kiểu "tối ưu CSDL".
- Bắt đầu critical path và root ownership; giữ full required capabilities. Không giải quyết bằng bỏ recommendations, health, telemetry, notifications, audit hoặc exam safeguards.
- Report/plan này được review chỉ đọc; tất cả implementation checkboxes đang unchecked vì user chưa yêu cầu sửa code.

Đã dùng 10 skill gồm: superpowers (systematic-debugging, writing-plans, verification-before-completion, dispatching-parallel-agents), ponytail, task-observer, full-output-enforcement, open-code-review, graphify, performance-optimization, impeccable, computer-use, doubt-driven-development.
