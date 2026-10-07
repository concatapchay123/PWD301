# Kế hoạch đầy đủ khắc phục đồng bộ dữ liệu PWD301 — bàn giao Antigravity

> **Cho agent thực thi:** Áp dụng `superpowers:executing-plans` hoặc `superpowers:subagent-driven-development`, thực hiện từng đơn vị và tick checklist. Đây là nhiệm vụ IMPLEMENTATION: sửa mã, thêm test và xác minh; không dừng ở đề xuất hoặc chỉ một bug. Không tự commit/push/deploy hay thao tác phá hủy database thật.

**Ngày:** 2026-10-07, Asia/Bangkok. **Workspace:** `E:\PWD301`.
**Goal:** Khắc phục đủ 57 finding của audit, bảo toàn ý định người dùng, persistence đúng, UI reconcile ngay và kiểm chứng xuyên vai trò.
**Architecture:** Giữ Flask headless REST/JSON, SQLAlchemy, SQL Server và Vanilla JS SPA hiện hữu trong `frontend/`. Sửa transaction, contracts, identity, queues, manifests và reconciliation tại module có trách nhiệm; tái sử dụng cơ chế hiện có. Không phục hồi Jinja/static legacy hoặc dựng frontend-preview.
**Tech Stack:** Python/Flask/SQLAlchemy/Alembic, Microsoft SQL Server, Vanilla JavaScript, node:test, pytest.
**Spec:** [Original requirements](2026-10-07-system-wide-data-synchronization-original-requirements.md), `SYSTEM_DATA_SYNCHRONIZATION_AUDIT.md`, System Specification và canonical Database Architecture theo thứ tự ưu tiên bên dưới. Audit là backlog lịch sử, không ghi đè business rules.

## 1. Trạng thái bàn giao trung thực

- Audit snapshot: `926fce6727c5dbdcf428b37ac143e8b46ac305e6`.
- HEAD xác minh khi soạn kế hoạch: `6fbe22dff1516d3fc0555c80bdfdb5e70f8f996f`. Worktree có nhiều thay đổi và file mới của người dùng; HEAD không đại diện toàn bộ mã đang chạy. Antigravity phải kiểm tra lại khi bắt đầu.
- Codex chưa thực hiện sửa mã sản phẩm cho remediation này. Đã tạo `REMEDIATION_PROGRESS.md`; ChatGPT đã trả PLAN iteration 0, task `c2c_a731`. PLAN không phải implementation completed.
- Baseline đã thực thi ở lượt trước: frontend 115 pass, 0 fail, 0 skip; repo_check exit 0. Đây là kết quả lịch sử của phiên bàn giao, không phải test mới sau sửa. Antigravity chạy lại baseline và lưu log của mình.
- Chưa chạy backend pytest, SQL migration/restore drill, browser mutation/F5/cross-role hoặc full verifier cho remediation này.
- Nhận định cần kiểm chứng: dirty source có thay đổi liên quan SYNC-009/027/029/041; không viết lại nếu tests chứng minh đúng. SYNC-042/043 có partial fix; memory/global fallback và failure state cần tái hiện. Tất cả 57 vẫn phải được revalidate.
- Bản này là kế hoạch để Antigravity thực thi, không phải báo cáo hoàn thành hệ thống.

## 2. Nguồn bắt buộc và constraints

Đọc đầy đủ audit, tất cả 57 findings và mục 6–31, không chỉ Executive Summary. Đọc `AGENTS.md` và global contract được nó tham chiếu; `tasks/CURRENT.md`; README phần liên quan; `docs/system/PWD301_SYSTEM_SPECIFICATION/CODING_AGENT_START_HERE.md`; `business/01_BUSINESS_RULE_CATALOG.md`; `implementation/06_NON_NEGOTIABLE_INVARIANTS.md`; `tasks/templates/TASK_TEMPLATE.md`. Đọc domain auth/authorization, assessment/attempt, course/lesson, notification, operations và frontend role flows trước owning unit. Database work đọc `docs/database/PWD301_DATABASE_ARCHITECTURE/` và relevant DDL trước sửa.

Ưu tiên: System Specification → canonical Database Architecture → README → AGENTS → CURRENT → source/tests. Reconcile conflict theo cấp cao hơn, không đổi spec ngầm. CURRENT không làm bỏ 57 finding của yêu cầu trực tiếp này; không tự bắt đầu backlog không liên quan.

- Áp dụng 5 nhóm skill user yêu cầu: Superpowers, Task Observer, trọn bộ Ponytail theo tác vụ, Full Output Enforcement, Open Code Review. UI áp dụng Impeccable và UI/UX contract. Skills mở rộng dùng đúng điều kiện; không cài hạ tầng chỉ để thỏa checklist. RTK nếu sẵn có; không có thì native và ghi rõ. Nhật ký trong workspace/evidence; không tự sửa global memory.
- TDD: regression test FAIL đúng nguyên nhân trước product change. Finding đã fixed hiện tại cần verification, không cố ý tạo regression để có red.
- Không reset/clean/stash/rebase/checkout đè dirty work, không bulk-format/stage toàn repo. Đọc targeted diff trước sửa. Không tự commit/push.
- Không DROP/TRUNCATE/reset DB thật, irreversible migration trên target chưa xác định, restore đè live. Không coi JSON metadata là backup.
- Giữ session/CSRF, JWT revocation, role+object authorization, email uniqueness, snapshots/QuestionRevision/history, append-only audit, server scoring/deadlines, ROWVERSION và single active editing lease.
- Không JWT localStorage hoặc password/token/API key trong evidence. Ownerless legacy draft không tự adopt/xóa vì không biết chủ.
- File PENDING/QUARANTINED/scan unavailable fail-closed; video <1GB; raw internal video không accessible; encrypted HLS/token/watermark/anti-tamper và server wall-clock progression giữ nguyên.
- Không reload/F5 làm fix, không React/Vue/Redis/WebSocket. Same-user mutation consume authoritative response/refetch đúng entity; optimistic error rollback.
- Không empty catch nuốt lỗi, không `[]` giả cho unavailable; không xóa tests/disable guards.
- UI một primary action, error inline/design tokens; không lộ technical ID/IP/secrets cho user. AI giữ tên Bạch tuộc trợ lí AI và authorization trước retrieval.
- `/new` route side-effect free; lazy create chỉ sau explicit action; URL mới dùng replaceState để giữ Back đúng.

## 3. Review Focus và semantics chung

Năm failure classes cần test xuyên các units: (1) false/null/0/empty có ý nghĩa bị default mất; (2) response A resolve sau B hoặc sau logout/role switch; (3) commit/audit thất bại giữa composite action; (4) retry/reload/duplicate sau ACK thất lạc; (5) read unavailable bị hiểu thành empty/success.

Mutation phân biệt APPLIED, PENDING_APPROVAL, PARTIAL, REJECTED, FAILED. Đây là semantics normalize trong client hiện có, không bắt buộc dựng framework/state machine mới hoặc đổi public JSON envelope. HTTP202 không là live applied; HTTP200 success:false không là thành công. Refresh fail sau mutation đã commit phải nói đã lưu nhưng tải lại thất bại, không hứa rollback server đã commit.

Preserve fields theo domain; whitelist writable fields; giữ returned persisted IDs và revision/version. Capture user/role/entity/generation trước await; obsolete response không render/cache/mutate entity hiện tại. Composite action một outer transaction, helpers flush, final validation/audit rồi commit; kiểm standalone callers trước đổi semantics.

## 4. Phase 0 — gate trước sửa

- [ ] Record HEAD/branch/ahead, staged/unstaged/untracked và targeted diff. Không nhận user changes là remediation của mình.
- [ ] Đọc sources bắt buộc; map backend/frontend/worker/proxy/DB từng process bằng config hiệu lực và metadata an toàn. Không in connection string/password.
- [ ] Xác định migration graph và DB runtime actual; read-only schema check trước migration. Không suy DB web từ shell .env đơn lẻ.
- [ ] Rà đủ57 trong dirty source: STILL_VALID, PARTIALLY_FIXED, ALREADY_FIXED, OBSOLETE, NEEDS_REVALIDATION; fresh file/function/test evidence. OBSOLETE cần contract/lý do mới, không vì chưa reproduce.
- [ ] Mở rộng REMEDIATION_PROGRESS.md đủ57 rows: severity/root, historical/current status, current anchors, unit/dependencies, red/green tests, UI/API/DB/F5/cross-role evidence và final status. SOURCE khác runtime proof.
- [ ] Safe baseline frontend/static. Backend chỉ sau isolated-target gate; process-local TEST_DATABASE_URL=sqlite:///:memory: cho portable tests. SQLite không chứng minh SQL Server concurrency/ROWVERSION/DDL/restore.
- [ ] Ghi blockers theo gate; tiếp tục unit độc lập an toàn. Không biến thiếu SQL environment thành dừng toàn dự án.

**Cảnh báo có bằng chứng:** `tests/conftest.py::_clean_mssql_database()` KILL sessions, disable constraints/triggers và DELETE mọi bảng trừ alembic_version ở setup/teardown. Không chạy pytest/verify.ps1 khi TEST_DATABASE_URL trỏ DB thật hoặc chưa xác định. Disposable SQL Server phải có danh tính xác minh và là dữ liệu test dùng bỏ theo authorization; guard từ chối target khác. Nhãn `testing` không đủ chứng minh an toàn.

## 5. Chu kỳ bắt buộc cho mọi unit

- [ ] Đọc domain contract/diff; tìm serializers/helpers/queues có thể reuse; khoanh production files/tests trước edit.
- [ ] Viết invariant test, deterministic fault injection/barriers/deferred promises; run RED lưu exit/log và nguyên nhân. Không sleep chờ race may rủi.
- [ ] Sửa nhỏ nhất, không refactor unrelated; migration mới/backfill trước constraints nếu cần, giữ history.
- [ ] GREEN focused → adjacent → static/contract affected. Inspect persisted state/fresh GET nếu có write.
- [ ] Browser test-data flow: immediate UI → ACK → DB/fresh GET → F5 → away/back → relogin/second role khi liên quan.
- [ ] OCR review multi-file/line-level và minimalism REMOVE NOW/SIMPLIFY NOW/KEEP/PONYTAIL; sửa review findings rồi rerun affected checks. Không claim OCR/pentest đã chạy nếu unavailable.
- [ ] Update progress commands/exit/log paths/review/limitations. Complete unit chỉ khi acceptance có evidence hoặc gate external ghi BLOCKED cụ thể.

## 6. Units, file ownership và dependencies

Đường dẫn dưới đây tính từ E:\PWD301. Existing function/line anchors chi tiết có trong appendix; re-find trên current dirty source trước edit. Test files listed là suite hiện có để mở rộng, không phải claim đủ coverage.

| Unit | Findings | Production targets | Tests hiện có | Dependencies |
|---|---|---|---|---|
| U00 | 046 | frontend/assets/js/api.js | frontend/audit_remediation_regressions.test.js; thêm api_outcome_contract.test.js nếu thiếu | Phase0 |
| U01 | 042,043 | frontend/assets/js/exam-store.js; router/views integration nếu test chứng minh cần | frontend/exam_progression.test.js, exam_hub_clarity.test.js, router_navigation.test.js | Phase0, không DB |
| U02 | 001 | models/course.py, question_bank_service.py, migrations/versions, canonical DB docs | integration/test_migrations.py, test_sqlserver_migration_roundtrip.py, test_sqlserver_question_revision.py | Phase0 + disposable SQL |
| U03 | 002,003,048,053,054 | services/operations_service.py, admin/api_admin routes, api.js, views/admin.js | unit/test_operations_service.py, api/test_operations_api.py, frontend/operations_without_hardware.test.js | U00; isolated SQL cho drill |
| U04 | 004,049 | caller-owned transactions trong assessment/course/lesson/question_bank/user/operations services và routes thực tế | unit domain suites; API change/grading/operations suites | Phase0; U02 cho schema-dependent cases |
| U05 | 005,006,007,008,021,024,025 | views/instructor-exams.js, api.js, assessment/question_bank/excel_exam services | frontend/exam_policy_settings.test.js, exam_progression.test.js; unit/test_assessment_service.py; api/test_assessment_api.py, test_instructor_exam_parse_api.py | U00,U04; U01 draft lifecycle |
| U06 | 009,010,011,015,017,019,020,026 | views/instructor.js, lesson_service.py, instructor routes/serializers | frontend/lesson_studio_isolation.test.js, instructor_lesson_authoring.test.js, lesson_navigation.test.js; api/test_lesson_authoring_remediation.py, test_lesson_change_request_flow.py | U00; U04 cho transaction |
| U07 | 012,013,014,016,018 | course/lesson services, instructor/admin routes, views/instructor.js; order migration nếu cần | api/test_course_changeset_workflow.py, test_course_changeset_deep_diff.py, test_course_metadata_and_lesson_approval_remediation.py; unit lesson/course | U04,U06; U02 schema |
| U08 | 022,023,055 | router.js, instructor-exams/instructor/admin views; relation/model/routes theo domain | frontend/router_navigation.test.js, course_review_regression.test.js; API course/assessment; new migration tests nếu có | U05/U07 persisted identity |
| U09 | 027,028,029,036,038 | views/student.js, controllers.js nếu owns queue, attempt_service.py, student/API routes | unit/test_attempt_autosave_service.py, test_attempt_lease_service.py, test_attempt_submission_service.py; API attempt suites; frontend/attempt_submission_key.test.js | Phase0; U00 ACK; độc lập U05 |
| U10 | 030,031,033,034,037 | lesson/attempt services, student routes/views, progress/appeal models nếu cần | api/test_lesson_mini_quiz_api.py, test_student_backend_completion.py; unit/test_lesson_wall_clock_progress.py, test_attempt_service.py | U00,U04; U09 ownership |
| U11 | 032,039,040,041,044,045,047 | api/router/auth/admin/student views; auth/authorization/user/notification services; session/JWT mirrors | frontend/notification_ui_contract.test.js, topbar_navigation.test.js, router_navigation.test.js; API notification/auth; unit auth/session | U00; U01 invalidation; U04 composites |
| U12 | 035,050,051,052 | router.js/ui.js, student/admin views và actual AI controller | frontend/router_navigation.test.js, audit_remediation_regressions.test.js; new async_read_identity.test.js nếu thiếu | U00,U11 scope |
| U13 | 056,057 | operations_service.py, worker lifecycle, __init__.py maintenance guard/router.js | unit/test_background_job_service.py, test_operations_service.py; api/test_operations_api.py; SQL multiprocess tests | U04; disposable SQL |
| U14 | all57 | full regression/runtime acceptance/evidence/final report | safe aggregate + browser/SQL below | all units |

Ưu tiên sau Phase0: U01 privacy → U00 outcomes → P0 U06/U09/U03; U04 trước atomic publish U05. U02 rehearsal/read-only có thể song song để gỡ schema gate. Không đợi backup drill mới sửa privacy/answers. Hoàn thành P1/P2 theo dependencies. Parallel agents chia file ownership; api.js/router.js/instructor.js là shared hotspots phải serialize integration. Không cho hai agents ghi cùng file; mỗi unit review riêng trước integrate.

## 7. Acceptance riêng đủ57 findings

Nếu finding đã được current code sửa, chỉ verify và ghi ALREADY_FIXED; không rewrite. Test invariant bên dưới gắn vào suites tương ứng Uxx. Mỗi row cần RED/GREEN hoặc verified existing implementation và fresh evidence.

| Finding | Unit | Hành động nếu còn lỗi | Test / nghiệm thu |
|---|---|---|---|
| SYNC-001 | U02 | Match web/worker DB schema với migration graph, rehearsal/backfill trên SQL Server riêng | Detect missing columns/enums; upgrade giữ rows/FK/history/CHECK; rollback rehearsed |
| SYNC-002 | U03 | Backup SQL Server recoverable thật; SUCCEEDED chỉ sau actual artifact evidence | SQL/disk/permission failure không success; isolated restore giữ representative data/history |
| SYNC-003 | U03 | Phân biệt metadata/header, VERIFYONLY và restore drill | Corrupt/sai schema reject; chưa restore không báo compatible verified |
| SYNC-004 | U04 | Outer transaction owns composite; helpers flush; audit cùng boundary | Fault sau từng bước rollback domain + decision; standalone callers vẫn persist |
| SYNC-005 | U05 | Bỏ partial sequential fallback; atomic batch/publish; giữ draft khi lỗi | Câu k fail không partial publish/clear draft; retry không duplicate |
| SYNC-006 | U05 | Edit diff bằng persisted assignment/question/revision IDs | No-op không thêm row; sửa một câu giữ others/snapshot history |
| SYNC-007 | U05 | Hydrate assignment.question nested cùng IDs/points/revision | GET→hydrate→no-op save→fresh GET giữ meaningful state |
| SYNC-008 | U05 | Map attempt_limit đúng contract, không truthiness fallback | Null/valid bounds roundtrip; invalid reject; không default1 ngầm |
| SYNC-009 | U06 | Preserve videoType/YouTube URL/resources khi parse/serialize | No-op/save/fresh GET/F5 không mất URL/type; raw video security giữ |
| SYNC-010 | U06 | Capture lesson ID/generation, obsolete load bỏ trước render | A resolve sau B không ghi A vào B hoặc save nhầm ID |
| SYNC-011 | U06 | Consume returned working draft ID cho saves/reads tiếp | Save hai lần cùng draft; live chưa đổi trước approve |
| SYNC-012 | U07 | Preserve target chapter trong draft/promotion | Published move→approve→fresh GET đúng target chapter |
| SYNC-013 | U07 | Merge full pending intent trước supersede + version check | Add/edit/move/delete/resources/governance cùng giữ; concurrent không silent overwrite |
| SYNC-014 | U07 | Promote draft resource manifest thay copy lại live deleted links | Detach→approve không resurrect; giữ retention/history |
| SYNC-015 | U06 | 202 hiển thị chờ duyệt/draft/proposal identity | 202 không patch live; approve mới applied; reject giữ live |
| SYNC-016 | U07 | Academic/prerequisite atomic nếu spec composite; otherwise PARTIAL/refetch | Prerequisite fail không toast all saved; retry phần chưa applied |
| SYNC-017 | U06 | Whole block delete detach đúng persisted links | Fresh GET links absent; failure rollback UI; không broad-delete blobs/history |
| SYNC-018 | U07 | Canonical persisted heterogeneous block order; minimal migration/backfill nếu cần | Text/video/quiz/resource reorder survive reload; duplicate/foreign IDs reject |
| SYNC-019 | U06 | Dirty switch Save/Discard/Keep hoặc scoped recovery | Switching lesson không mất typing; failed save giữ form |
| SYNC-020 | U06 | Optimistic move/reorder snapshot rollback + server reconcile | 400/403/409/500/timeout không fake UI success; fresh GET consistent |
| SYNC-021 | U05 | Checkpoint assessment ID sau create, retry resume/idempotent | Create OK/publish fail/retry không tạo đề thứ hai |
| SYNC-022 | U08 | Route hydrate persisted assessment/course/unit scope; lazy creation | Deep-link/F5 đúng editor; /new không POST; replaceState/back đúng |
| SYNC-023 | U08 | Persist chapter/unit association bằng domain relation, bỏ title heuristic | Rename không đổi association; backfill không đoán sai; foreign scope reject |
| SYNC-024 | U05 | Preserve all allowed Bloom enum xuyên import/API | ANALYZE/EVALUATE/CREATE không thành UNDERSTAND; invalid reject |
| SYNC-025 | U05 | Require real short-answer key, không persist label Đáp án | Blank key reject; entered answer chấm đúng; label không thành key |
| SYNC-026 | U06 | Capture lesson/block/generation trước save/upload await | Switch/remove pending không attach file entity mới; orphan lifecycle đúng |
| SYNC-027 | U09 | Hydrate durable sequence, monotonic qua reload/retry | Reload rồi edit được; stale không overwrite latest; duplicate idempotent |
| SYNC-028 | U09 | Owner/tab lease/expiry ở open/autosave/heartbeat/submit/takeover | Same-session two tabs một writer; early takeover reject; submit idempotent + ownership |
| SYNC-029 | U09 | Debounce input + flush trước navigate/submit/deadline; truthful unsaved | Text/fill sent before submit; network failure giữ unsaved/recovery; không hứa unload luôn gửi thành công |
| SYNC-030 | U10 | Server scores mini-quiz và threshold từ persisted config | Forged passed/score ignored; below/equal/above threshold đúng |
| SYNC-031 | U10 | Passed sau authoritative ACK; failure retry/hydrate | 500/timeout không Passed; retry no duplicate; reload correct result |
| SYNC-032 | U11 | Normalize preference array/map, giữ explicit false | Load-save-load true/false; partial patch không reset flags |
| SYNC-033 | U10 | Server elapsed wall-clock cap + atomic increment; playback/visibility | Background/tamper không progress; fraction không bump minimum; concurrency no lost update |
| SYNC-034 | U10 | Durable event idempotency cùng transaction increment | Commit fail+retry applies once; restart/duplicate không double progress |
| SYNC-035 | U12 | Conversation/context generation fence + controlled Send | Reset pending không resurrect old chat; double Enter không wrong context |
| SYNC-036 | U09 | Authorization trước terminal shortcut mọi path | Foreign user không nhận terminal data kể cả replay |
| SYNC-037 | U10 | Server terminal/reason/pending uniqueness/idempotent appeal | Active/blank/repeat/concurrent reject; audit atomic |
| SYNC-038 | U09 | Save header aggregate all pending/failed queues | Q1 ACK + Q2 fail không all saved; retry saved khi all ACK |
| SYNC-039 | U11 | Avatar server-authoritative; preview khác saved | Failed save không local success; server wins stale cache after reload/login |
| SYNC-040 | U11 | Reject notification mutation errors + rollback/refetch | Mark/delete fail rows/count đúng; 403 không swallowed |
| SYNC-041 | U11 | User+role+generation fenced notification response/cache | Late A sau B không render/cache A cho B; logout invalidates inflight |
| SYNC-042 | U01 | Scope memory/durable key, bỏ global fallback, password memory-only | A↔B isolation/recovery; anonymous no global; clearA giữ B/legacy; no persisted password |
| SYNC-043 | U01 | Storage failure truthful + recovery/retry; clear flag on success | setItem throw lastSaved null/data intact; retry clears flag; memory-only warning |
| SYNC-044 | U11 | Role local đổi chỉ sau ACK; failure rollback route/perspective | 403/network giữ previous server/local role, không bypass |
| SYNC-045 | U11 | Logout fail khác server revocation confirmed; cleanup truthful | Timeout/500 chưa-confirmed; successful logout server revoke/cache clear; retry safe |
| SYNC-046 | U00 | Reject HTTP200 success:false/HTML/malformed response | Domain errors retained; valid JSON/202 đúng, không blanket reject |
| SYNC-047 | U11 | Session-sensitive reauth tương đương JWT + CSRF/object auth | Missing/stale reauth fails before write; valid succeeds; no secret logs |
| SYNC-048 | U03 | Carry restore reason UI→DTO→audit validation | Reason preserved; audit failure abort sensitive action |
| SYNC-049 | U04 | Composite roles atomic hoặc spec-defined PARTIAL + refetch | kth failure no hidden partial; roles/revocation/audit consistent |
| SYNC-050 | U12 | EMPTY khác ERROR/UNAUTHORIZED/PARTIAL/STALE | Rejected read không []; retry restores; genuine empty vẫn empty |
| SYNC-051 | U12 | Search/filter generation fence | Old response không overwrite current query/loading/error |
| SYNC-052 | U12 | Return/await actual route-refresh Promise | Delayed refresh chưa success; failed refresh phân biệt mutation committed |
| SYNC-053 | U03 | Consume verify ACK hoặc refetch backup row | Visible row matches persisted verify; failure không success badge |
| SYNC-054 | U03 | Enum PRE_MAINTENANCE roundtrip hoặc explicit reject theo spec | No silent MANUAL; unsupported enum 400 |
| SYNC-055 | U08 | Detail fetch persisted ID/lifecycle/ownership, không pending-list-only | Approved/rejected deep-link/F5 authorized history; foreign ID reject |
| SYNC-056 | U13 | Retry CAS failed state/version/lease, không override RUNNING | Concurrent retries one winner; running lease no steal; expiry correct |
| SYNC-057 | U13 | Shared authoritative maintenance với bounded cross-process coherence | Two processes start/end consistent; UNKNOWN không inactive; allowlist đúng |

## 8. U01 — bước khởi đầu cụ thể

**Modify:** `frontend/assets/js/exam-store.js`, `tests/frontend/exam_progression.test.js`. Router/api/view chỉ nếu integration test chứng minh cần; giữ dirty logout hook đã có.
**Interfaces giữ nguyên:** getDraft(), saveDraft(updates), hasDraft(), clearDraft(), clearMemoryDraft(), canVisitStep(step). Sửa internal scope, không đổi toàn bộ consumer.

- [ ] VM harness shared localStorage Map, window.app.currentUser đổi runtime, reconstruct VM cùng Map mô phỏng reload.
- [ ] RED cases: direct A→B memory isolation; B không hydrate global legacy; A/B durable independent recovery; clear A không delete B/global; anonymous memory-only; password absent durable payload/re-entry after reload; setItem failure memory intact/lastSaved null; success retry clears failure.
- [ ] Role transition Instructor→Student không hydrate authoring draft. Dùng actual active-role representation, không giả định property name. User key alone không cho phép Student consumer đọc draft.
- [ ] `node --test tests/frontend/exam_progression.test.js`, lưu actual expected failures trước code. Existing pass chỉ verified, không rewrite.
- [ ] Associate memory với scope; invalidate identity/role eligibility change; only owned key read/write; no legacy fallback/adoption/deletion. clearMemoryDraft reset scope. Version payload tối thiểu nếu cần; compatible read user-owned key an toàn.
- [ ] Password memory-only; authenticated persistence sanitized copy, không mutate editing password trong memory. Anonymous không fake durable timestamp.
- [ ] Storage warning/export/retry nếu consumer thiếu: native JSON/Blob reuse, no dependency. Success retry clears storageFailed ở memory và durable payload.
- [ ] Syntax + progression/hub/router + affected full frontend; diff review preserve unrelated user hunks.

## 9. SQL, backup và runtime gates

Không suy migration revision từ audit rồi chạy: inspect current graph kể cả untracked migration, runtime actual và schema. Rehearsal disposable SQL Server có historical samples; verify upgrade/backfill/null/FK/CHECK/unique/ROWVERSION và rollback. Nếu downgrade phá dữ liệu dùng documented restore/forward fix, không chạy destructive downgrade production.

Backup bằng adapter/driver/cơ chế SQL Server documented hiện có; server-side path allowlisted, quyền/timeout/error được xử lý, status terminal chỉ sau evidence. Metadata manifest chỉ đi kèm backup. VERIFYONLY không thay restore drill. Drill target riêng DB name/storage; compare schema và representative content/counts/references/snapshots/audit. Không safe target: `BLOCKED — SAFE RESTORE TARGET REQUIRED`; vẫn implement fail-closed status và units độc lập.

Atomicity fault injection gồm audit fail. SQL races dùng barriers/two connections/processes, assertions final version/rowcount/answer/lease winner. Mock/SQLite pass không thay SQL. Maintenance không thêm Redis tự động; ưu tiên DB authority/bounded consistency theo current service, UNKNOWN access theo spec.

## 10. Lệnh kiểm thử và evidence

Xác minh env/executable theo repository trước run. PowerShell tại E:\PWD301:

```powershell
node --check frontend/assets/js/exam-store.js
node --test tests/frontend/exam_progression.test.js
$syncFrontendTests = @(Get-ChildItem tests/frontend -Filter '*.test.js' -File | Sort-Object FullName | Select-Object -ExpandProperty FullName)
& node --test --test-reporter=tap $syncFrontendTests
& .venv\Scripts\python.exe scripts/repo_check.py
```

Portable backend dùng process-local TEST_DATABASE_URL rồi restore env, sau khi đọc tests/fixtures tránh SQL side paths:

```powershell
$syncPreviousTestDb = $env:TEST_DATABASE_URL
try {
    $env:TEST_DATABASE_URL = 'sqlite:///:memory:'
    & .venv\Scripts\python.exe -m pytest tests/unit/test_attempt_autosave_service.py tests/unit/test_attempt_lease_service.py -q
    $syncTestExit = $LASTEXITCODE
} finally {
    if ($null -eq $syncPreviousTestDb) {
        Remove-Item Env:TEST_DATABASE_URL -ErrorAction SilentlyContinue
    } else {
        $env:TEST_DATABASE_URL = $syncPreviousTestDb
    }
}
if ($syncTestExit -ne 0) { throw "Focused backend tests failed: $syncTestExit" }
```

Đổi focused test list theo owning unit; hai suites example không phải full coverage. Full `./scripts/verify.ps1` chỉ sau DB/fixture gate: repo_check→compileall→ruff check→format check→mypy→node→pytest. Dừng lint nghĩa pytest chưa run. Ghi riêng và run independent safe checks; không aggregate PASS. Không formatter toàn repo dirty.

Evidence directory `docs/audits/PWD301_SYNC_REMEDIATION_2026-10-07/` (ngày actual execution nếu khác): baseline, per-unit red/green commands+exit/full logs, reviews, browser screenshots, API correlations, safe SQL assertions, migration/drill logs. Redact credentials/private answers. Record timestamp/HEAD/diff baseline. Không chỉ giữ truncated terminal output.

## 11. Browser và cross-role acceptance

Accounts/data test trong identified runtime; không mutate exam/enrollment thật để thử. Browser/Computer Use trực tiếp, không chỉ VM. Mỗi affected mutation: ACTION→immediate UI→ACK→DB/server→fresh GET→F5→away/back→relogin/second role khi relevant. F5 là verification, không fix.

| Luồng | Acceptance runtime |
|---|---|
| Admin roles/auth | role combos, suspension/session+JWT revoke, reauth/CSRF/object permissions, fault rollback, audit reason |
| Admin review | whole intent proposal, 202 not live, approve/reject correct, history deep link after F5 |
| Admin operations | backup actual artifact, truthful verify/drill, refreshed row, enum/reason, retry running reject, two-process maintenance |
| Instructor authoring | create/unit/lesson, no-op/save/clone/move/resources/order/YouTube, dirty switch/upload races, academic/prerequisite partial errors |
| Instructor exams | nested assignment/Bloom/limit, diff editing, atomic publish/checkpoint retry, scope/deep-link, cross-account draft/storage failure |
| Student attempts | text debounce/flush, F5 durable sequence, two-tab lease, stale/duplicate/reordered packets, deadline/submit/ownership, aggregate save indicator |
| Student lessons | server quiz threshold/ACK/retry, HLS/watermark/tamper/background heartbeat, durable progress event, appeal lifecycle |
| Auth/notifications/AI | false flags/avatar ACK, role/logout failure, A→B late-response isolation, pending chat reset |
| Cross-role course | Instructor mixed proposal→Admin correct review/approve→Student published intended representation; reject keeps live |
| Cross-role exam | Student submit→server snapshot/score→Instructor/Admin result→Student F5/relogin; late packets don't change result |

Negative cases 400/401/403/409/500/timeout/network failure, permission boundaries, response reversal theo endpoint contract; không ép statuses không thuộc domain. Second-session refetch/navigation/focus theo spec; không cần WebSocket delivery.

## 12. Deliverables và Definition of Done

`REMEDIATION_PROGRESS.md`: đủ57 với current classification/fresh anchors/owner/unit/dependencies/tests/runtime gates/final status. Không dùng ledger thay tests.

`SYSTEM_DATA_SYNCHRONIZATION_REMEDIATION_REPORT.md`: đủ25 mục brief gốc: Executive Summary; Original Snapshot; Remediation Snapshot; Files Changed; Root Causes Fixed; P0 Results; P1 Results; P2 Results; Database/Migration Changes; Frontend Synchronization; API Contracts; Transactions; Race Fixes; Draft/Persistence; Admin Verification; Instructor Verification; Student Verification; Cross-role Verification; Tests Added; Tests Executed; Passed; Failed; Blocked Verification; Remaining Risks; Finding-by-Finding Status Matrix. Đáp ứng A–G TASK_TEMPLATE: sources, reuse, per-file delta, deletion/simplification, ponytails, actual tests, risks.

Final statuses: FIXED_VERIFIED, FIXED_PARTIALLY_VERIFIED, BLOCKED, ALREADY_FIXED, OBSOLETE, NOT_FIXED. ALREADY_FIXED có current evidence; runtime gate chưa run giữ partial. BLOCKED ghi technical evidence/target required/owner/unblock action, chỉ affected gate; continue independent work. P2 defer chỉ documented greater architectural risk: trigger/owner/risk/safeguard/review point và matrix.

Numeric report: total57; status counts sum57; P0/P1/P2 remaining; tests added/pass/fail/skip. Original severity9P0/27P1/21P2 giữ riêng nếu reprioritize. Skip/cancel/timeout không pass. Không cộng duplicated reruns thành unique passes hoặc trộn files/suites/testcases.

Chọn một system status CRITICAL / UNSTABLE / PARTIALLY STABLE / STABLE WITH BLOCKED EXTERNAL VERIFICATION / STABLE. STABLE cần evidence đầy đủ, không chỉ tests green. Không stable nếu unresolved P0 privacy/data defect. All P0/P1 fixed+verified hoặc legitimate concrete external BLOCKED; P2 handled trừ documented risk. NOT_FIXED không được giấu.

- [ ] Đọc lại all57 audit cuối full regression, không finding nào skipped.
- [ ] Scan added reload workarounds, lossy truthiness, ownerless caches, swallowed errors, nested commits, mutable IDs; review business flow chứ không chỉ regex.
- [ ] Whole-change OCR/security review; Strix Docker trước ship/release theo lifecycle contract nếu available; unavailable báo chưa run, không fake pass.
- [ ] Auth/file/history/snapshots/HLS/heartbeat nonregression, role/cross-role acceptance.
- [ ] Preserve unrelated user dirty changes; report remediation delta riêng.
- [ ] Không commit/push/deploy/production restore nếu chưa explicit authorization.
- [ ] Cuối response: `Đã dùng x skill gồm: ...`, đúng skills dùng; phân biệt skill đọc và công cụ thực chạy.

## 13. Prompt giao Antigravity

> Thực thi toàn bộ kế hoạch này tại E:\PWD301. Đọc đầy đủ audit/contracts và appendix; revalidate tất cả57 trên HEAD+dirty tree hiện tại, bảo toàn user changes. Phase0 rồi U01 test-first, tiếp tục mọi unit theo dependencies đến hết actionable P0/P1/P2. Sửa mã thực tế, kiểm persistence/UI/API/DB/race/cross-role, không chỉ viết kế hoạch. Không reset DB thật hoặc chạy destructive SQL pytest fixture trên target chưa chứng minh disposable; không restore live/fake backup/verification/reload workaround/stack rewrite. Gate external thiếu environment ghi BLOCKED cụ thể và tiếp tục independent units. Duy trì progress và deliver full25-section final report +57-row matrix, actual evidence/counts. Không tự commit/push/deploy. Scoped reversible coding đã được giao không cần hỏi lại; chỉ approval cho actual external/destructive actions cần thiết theo rules.

## 14. Appendix — 57 finding lịch sử và root map

Appendix được trích nguyên từ audit để mang theo symptom, expected/actual, endpoint, file/function/entity và recommended fix. **Status/số dòng thuộc audit snapshot, không là current verification.** Executor vẫn đọc toàn audit gốc sections6–31 cho inventories và testing context.

### Root categories G01–G15 (audit)

These are shared patterns, not 57 independent architectural defects. Fixes can reuse serializers/API normalization, immutable captured IDs + request generations, caller-owned transactions and canonical draft manifest. Domain lease/autosave/backup/schema gates need server/database work, not a reload/toast workaround.

| Root | Cause category | Related findings |
| --- | --- | --- |
| G01 | Representation / API contract không roundtrip | SYNC-006, SYNC-007, SYNC-008, SYNC-009, SYNC-011, SYNC-012, SYNC-017, SYNC-018, SYNC-024, SYNC-032, SYNC-048, SYNC-054 |
| G02 | Acknowledgement không gắn authoritative state | SYNC-005, SYNC-015, SYNC-016, SYNC-020, SYNC-031, SYNC-038, SYNC-040, SYNC-044, SYNC-045, SYNC-046, SYNC-052 |
| G03 | Async response/callback không fence identity | SYNC-010, SYNC-026, SYNC-035, SYNC-041, SYNC-051 |
| G04 | Transaction ownership bị chia nhỏ | SYNC-004, SYNC-049 |
| G05 | Draft manifest không giữ toàn intent | SYNC-013, SYNC-014 |
| G06 | Editing lease chưa enforce mọi boundary | SYNC-028 |
| G07 | Local sequence/event không nối durable sequence | SYNC-027, SYNC-029, SYNC-034 |
| G08 | Local durability/account scope không rõ | SYNC-039, SYNC-042, SYNC-043 |
| G09 | Operational success thiếu evidence thực thi | SYNC-002, SYNC-003 |
| G10 | Authority còn dựa frontend | SYNC-025, SYNC-030, SYNC-033, SYNC-036, SYNC-037, SYNC-047, SYNC-056 |
| G11 | Cache/refetch không invalidate đúng | SYNC-053, SYNC-057 |
| G12 | Routing/scope không gắn persisted identity | SYNC-022, SYNC-023, SYNC-055 |
| G13 | Runtime schema không compatible code | SYNC-001 |
| G14 | Read failure bị coi empty dataset | SYNC-050 |
| G15 | Dirty workflow thiếu checkpoint/recovery | SYNC-019, SYNC-021 |


### SYNC-001 — Runtime schema chậm hai migration


- **Severity:** P1
- **Status:** CONFIRMED; LIVE SELECT + SOURCE; chưa xác nhận DB của tiến trình web. Source/VM confirmation is not live mutation proof.
- **Role:** All
- **Module:** Runtime schema chậm hai migration
- **Feature:** Runtime schema chậm hai migration
- **Action:** saveAcademicSettings
- **Symptom:** SELECT live: head=b3c4d5e6f7a9; table prerequisite chỉ có 4 cột cũ; CHECK change_type chỉ nhận INITIAL/EDIT/ANSWER_ONLY/CONTENT_OR_CHOICES. Repository head=d5e6f7a8b0c1. ORM đọc approval_status và các cột review không tồn tại; CONTENT_CHANGE có thể bị constraint từ chối.
- **Expected Behavior:** Head/columns/check enums phù hợp deployed models/services
- **Actual Behavior:** SELECT live: head=b3c4d5e6f7a9; table prerequisite chỉ có 4 cột cũ; CHECK change_type chỉ nhận INITIAL/EDIT/ANSWER_ONLY/CONTENT_OR_CHOICES. Repository head=d5e6f7a8b0c1. ORM đọc approval_status và các cột review không tồn tại; CONTENT_CHANGE có thể bị constraint từ chối.
- **Frontend File:** frontend/assets/js/views/instructor.js:5336
- **Frontend Function:** saveAcademicSettings
- **API Endpoint:** /instructor/courses/{c}/prerequisites; question revision APIs
- **Backend File:** src/pwd301/models/course.py:294; migrations/versions/d5e6f7a8b0c1_0013_add_course_prerequisite_approval_columns.py:18; migrations/versions/c4d5e6f7a8b0_0012_question_revision_change_types.py:31; src/pwd301/services/question_bank_service.py:1207
- **Backend Function:** src/pwd301/models/course.py :: CoursePrerequisite; migrations/versions/d5e6f7a8b0c1_0013_add_course_prerequisite_approval_columns.py :: upgrade; migrations/versions/c4d5e6f7a8b0_0012_question_revision_change_types.py :: upgrade; src/pwd301/services/question_bank_service.py :: create_question_revision
- **Database Entity/Table:** course_prerequisites; question_revisions; alembic_version
- **Technical Cause:** SELECT live: head=b3c4d5e6f7a9; table prerequisite chỉ có 4 cột cũ; CHECK change_type chỉ nhận INITIAL/EDIT/ANSWER_ONLY/CONTENT_OR_CHOICES. Repository head=d5e6f7a8b0c1. ORM đọc approval_status và các cột review không tồn tại; CONTENT_CHANGE có thể bị constraint từ chối.
- **Root Cause:** G13 — Runtime schema không compatible code
- **Evidence:** LIVE SELECT + SOURCE; chưa xác nhận DB của tiến trình web; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 không sửa schema; luồng phụ thuộc cột/enum mới vẫn lỗi.
- **Data Loss Risk:** YES: thao tác mới không persist; chưa chứng minh dữ liệu đã lưu bị mất
- **Affected Features:** All → Runtime schema chậm hai migration → saveAcademicSettings
- **Recommended Fix:** Sau khi duyệt kế hoạch triển khai, kiểm thử migration trên bản sao SQL Server, đối chiếu head/schema rồi nâng runtime có backup thật; không chạy migration trong audit.
- **Regression Risk:** Migration rehearsal/backfill/history; SQLite không thay SQL proof

### SYNC-002 — Backup thành công nhưng không chứa dữ liệu database


- **Severity:** P0
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Admin
- **Module:** Backup thành công nhưng không chứa dữ liệu database
- **Feature:** Backup thành công nhưng không chứa dữ liệu database
- **Action:** backup create / restore
- **Symptom:** Snapshot chỉ ghi metadata và tables={backup_timestamp,schema_verified:true}; không export row/không BACKUP DATABASE. BackupRun vẫn SUCCEEDED. Restore MSSQL đưa file JSON vào RESTORE DATABASE; nhánh không MSSQL không phục hồi nhưng trả RESTORED.
- **Expected Behavior:** Backup/restore/drill thành công chỉ sau artifact/data recovery thật
- **Actual Behavior:** Snapshot chỉ ghi metadata và tables={backup_timestamp,schema_verified:true}; không export row/không BACKUP DATABASE. BackupRun vẫn SUCCEEDED. Restore MSSQL đưa file JSON vào RESTORE DATABASE; nhánh không MSSQL không phục hồi nhưng trả RESTORED.
- **Frontend File:** frontend/assets/js/views/admin.js:5061
- **Frontend Function:** backup create / restore
- **API Endpoint:** POST /admin/backups; POST /admin/backups/{id}/restore
- **Backend File:** src/pwd301/services/operations_service.py:1181; :1200; :1217; :1268; :1790; :1840
- **Backend Function:** src/pwd301/services/operations_service.py :: create_database_backup; src/pwd301/services/operations_service.py :: restore_database_snapshot
- **Database Entity/Table:** backup_runs; toàn bộ database
- **Technical Cause:** Snapshot chỉ ghi metadata và tables={backup_timestamp,schema_verified:true}; không export row/không BACKUP DATABASE. BackupRun vẫn SUCCEEDED. Restore MSSQL đưa file JSON vào RESTORE DATABASE; nhánh không MSSQL không phục hồi nhưng trả RESTORED.
- **Root Cause:** G09 — Operational success thiếu evidence thực thi
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 vẫn thấy BackupRun SUCCEEDED; không tạo ra backup restorable.
- **Data Loss Risk:** YES: rủi ro không phục hồi được khi sự cố; không chạy restore live
- **Affected Features:** Admin → Backup thành công nhưng không chứa dữ liệu database → backup create / restore
- **Recommended Fix:** Tạo backup SQL Server thật, kiểm tra bằng engine và restore drill vào DB riêng; từ chối dialect không hỗ trợ; trạng thái chỉ thành công sau xác minh.
- **Regression Risk:** Explicit Admin restore confirmation, engine/path permissions, audit

### SYNC-003 — Dry-run báo tương thích chưa hề thử restore


- **Severity:** P1
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Admin
- **Module:** Dry-run báo tương thích chưa hề thử restore
- **Feature:** Dry-run báo tương thích chưa hề thử restore
- **Action:** restore dry-run
- **Symptom:** Chỉ đọc keys JSON rồi trả COMPATIBLE/schema_compatible=true; UI thêm Tương thích Cấu trúc 100%, không đối chiếu schema hoặc restore bản sao.
- **Expected Behavior:** Backup/restore/drill thành công chỉ sau artifact/data recovery thật
- **Actual Behavior:** Chỉ đọc keys JSON rồi trả COMPATIBLE/schema_compatible=true; UI thêm Tương thích Cấu trúc 100%, không đối chiếu schema hoặc restore bản sao.
- **Frontend File:** frontend/assets/js/views/admin.js:4738
- **Frontend Function:** restore dry-run
- **API Endpoint:** POST /admin/backups/{id}/restore/dry-run
- **Backend File:** src/pwd301/services/operations_service.py:1487; :1518
- **Backend Function:** src/pwd301/services/operations_service.py :: execute_dry_run_restore
- **Database Entity/Table:** backup_runs
- **Technical Cause:** Chỉ đọc keys JSON rồi trả COMPATIBLE/schema_compatible=true; UI thêm Tương thích Cấu trúc 100%, không đối chiếu schema hoặc restore bản sao.
- **Root Cause:** G09 — Operational success thiếu evidence thực thi
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** Reload giữ metadata drill nhưng không chứng minh khả năng restore.
- **Data Loss Risk:** YES: assurance giả có thể khiến phục hồi thất bại
- **Affected Features:** Admin → Dry-run báo tương thích chưa hề thử restore → restore dry-run
- **Recommended Fix:** Phân biệt checksum/artifact validation với restore drill; chỉ báo compatibility sau kiểm tra engine/schema trên target riêng.
- **Regression Risk:** Explicit Admin restore confirmation, engine/path permissions, audit

### SYNC-004 — Commit bên trong helper phá atomicity của hành động lớn


- **Severity:** P0
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Admin / Instructor
- **Module:** Commit bên trong helper phá atomicity của hành động lớn
- **Feature:** Commit bên trong helper phá atomicity của hành động lớn
- **Action:** approve application / approve change / batch create
- **Symptom:** Role/content/question helpers commit trước khi quyết định review hoặc item cuối hoàn tất. Ngoại lệ sau đó rollback không hoàn tác commit trước: role được cấp nhưng đơn PENDING, content đã đổi nhưng request PENDING, batch thất bại nhưng một phần câu đã lưu.
- **Expected Behavior:** Composite action commit all-or-nothing domain+decision+required audit/outbox
- **Actual Behavior:** Role/content/question helpers commit trước khi quyết định review hoặc item cuối hoàn tất. Ngoại lệ sau đó rollback không hoàn tác commit trước: role được cấp nhưng đơn PENDING, content đã đổi nhưng request PENDING, batch thất bại nhưng một phần câu đã lưu.
- **Frontend File:** frontend/assets/js/views/admin.js:2937; frontend/assets/js/views/instructor-exams.js:4002
- **Frontend Function:** approve application / approve change / batch create
- **API Endpoint:** POST /admin/instructor-applications/{id}/review; POST /admin/change-requests/{id}/review; POST /instructor/assessments/{a}/questions/batch
- **Backend File:** src/pwd301/services/user_service.py:1633; :1042; :1742; src/pwd301/blueprints/admin/routes.py:2018; :2084; :2103; :2115; :2182; src/pwd301/blueprints/instructor/routes.py:3591; :3624; :3654; src/pwd301/services/question_bank_service.py:754; src/pwd301/services/assessment_service.py:1476
- **Backend Function:** src/pwd301/services/user_service.py :: review_instructor_application; src/pwd301/services/user_service.py :: assign_role_to_user; src/pwd301/blueprints/admin/routes.py :: admin_review_change_request; src/pwd301/blueprints/instructor/routes.py :: batch_create_instructor_assessment_questions_route; src/pwd301/services/question_bank_service.py :: create_question; src/pwd301/services/assessment_service.py :: assign_question
- **Database Entity/Table:** user_roles; instructor_applications; course_change_requests; course_completion_rules; questions; assessment_question_assignments
- **Technical Cause:** Role/content/question helpers commit trước khi quyết định review hoặc item cuối hoàn tất. Ngoại lệ sau đó rollback không hoàn tác commit trước: role được cấp nhưng đơn PENDING, content đã đổi nhưng request PENDING, batch thất bại nhưng một phần câu đã lưu.
- **Root Cause:** G04 — Transaction ownership bị chia nhỏ
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 đọc phần đã commit, khác kỳ vọng thao tác thất bại hoàn toàn.
- **Data Loss Risk:** YES: partial state và sai tính toàn vẹn nghiệp vụ; fault injection chưa chạy
- **Affected Features:** Admin / Instructor → Commit bên trong helper phá atomicity của hành động lớn → approve application / approve change / batch create
- **Recommended Fix:** Một transaction owner cho mỗi hành động; helper nhận session chỉ flush, ngoài cùng commit decision+domain+audit+outbox. Reuse cách helper lesson/unit đang hỗ trợ session.
- **Regression Risk:** Caller-owned session, SQL locks, outbox delivery failure không rollback primary action

### SYNC-005 — Fallback tạo từng câu rồi publish một phần và xóa toàn draft


- **Severity:** P0
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Instructor
- **Module:** Fallback tạo từng câu rồi publish một phần và xóa toàn draft
- **Feature:** Fallback tạo từng câu rồi publish một phần và xóa toàn draft
- **Action:** publish handler
- **Symptom:** Batch lỗi được retry toàn bộ từng item; mỗi lỗi single chỉ console.warn. createdQuestionsCount>0 đủ publish, sau đó clearDraft cả các câu chưa lưu. Các item batch đã commit trước lỗi còn có thể bị nhân đôi.
- **Expected Behavior:** Applied/pending/error/partial được phân biệt, UI reconcile sau acknowledgement
- **Actual Behavior:** Batch lỗi được retry toàn bộ từng item; mỗi lỗi single chỉ console.warn. createdQuestionsCount>0 đủ publish, sau đó clearDraft cả các câu chưa lưu. Các item batch đã commit trước lỗi còn có thể bị nhân đôi.
- **Frontend File:** frontend/assets/js/views/instructor-exams.js:4002; :4008; :4011; :4018; :4021
- **Frontend Function:** publish handler
- **API Endpoint:** POST batch; POST questions/create; POST /instructor/assessments/{a}/publish
- **Backend File:** src/pwd301/blueprints/instructor/routes.py:3591; :3624; :3654
- **Backend Function:** src/pwd301/blueprints/instructor/routes.py :: batch_create_instructor_assessment_questions_route
- **Database Entity/Table:** assessments; questions; assignments
- **Technical Cause:** Batch lỗi được retry toàn bộ từng item; mỗi lỗi single chỉ console.warn. createdQuestionsCount>0 đủ publish, sau đó clearDraft cả các câu chưa lưu. Các item batch đã commit trước lỗi còn có thể bị nhân đôi.
- **Root Cause:** G02 — Acknowledgement không gắn authoritative state
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 có thể thấy đề thiếu/trùng câu và local draft đã bị xóa.
- **Data Loss Risk:** YES: nội dung câu chưa persist bị xóa khỏi draft
- **Affected Features:** Instructor → Fallback tạo từng câu rồi publish một phần và xóa toàn draft → publish handler
- **Recommended Fix:** Bỏ blind fallback; yêu cầu kết quả đầy đủ/idempotent; giữ câu thất bại và draft, chặn publish nếu chưa lưu đủ tập câu đã xác nhận.
- **Regression Risk:** 202 workflow, CSRF retry, idempotency, input chưa lưu

### SYNC-006 — Edit đề hiện có lại CREATE toàn bộ câu thay vì diff


- **Severity:** P1
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Instructor
- **Module:** Edit đề hiện có lại CREATE toàn bộ câu thay vì diff
- **Feature:** Edit đề hiện có lại CREATE toàn bộ câu thay vì diff
- **Action:** Open in Studio → Publish
- **Symptom:** isEditingExisting/assessmentId được đặt nhưng Publish chỉ update config rồi CREATE tất cả câu. Không update theo question_id và không xóa assignment bị bỏ trong editor.
- **Expected Behavior:** Đọc-sửa-lưu giữ identity/type/values/references/cấu trúc canonical
- **Actual Behavior:** isEditingExisting/assessmentId được đặt nhưng Publish chỉ update config rồi CREATE tất cả câu. Không update theo question_id và không xóa assignment bị bỏ trong editor.
- **Frontend File:** frontend/assets/js/views/instructor-exams.js:4687; :3945; :3956; :4002
- **Frontend Function:** Open in Studio → Publish
- **API Endpoint:** PATCH assessment + POST questions batch
- **Backend File:** src/pwd301/blueprints/instructor/routes.py:3462; :3591
- **Backend Function:** src/pwd301/blueprints/instructor/routes.py :: batch_create_instructor_assessment_questions_route
- **Database Entity/Table:** assessments; assessment_question_assignments; questions
- **Technical Cause:** isEditingExisting/assessmentId được đặt nhưng Publish chỉ update config rồi CREATE tất cả câu. Không update theo question_id và không xóa assignment bị bỏ trong editor.
- **Root Cause:** G01 — Representation / API contract không roundtrip
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 thấy câu cũ vẫn tồn tại và câu mới trùng.
- **Data Loss Risk:** YES: cấu trúc/đáp án chỉnh sửa không được phản ánh đúng
- **Affected Features:** Instructor → Edit đề hiện có lại CREATE toàn bộ câu thay vì diff → Open in Studio → Publish
- **Recommended Fix:** Áp dụng diff theo assignment/question identity trong transaction; giữ snapshot đã dùng và các freeze hiện có.
- **Regression Risk:** Draft IDs, explicit null, immutable revisions, fail-closed resources

### SYNC-007 — Assignment.question bị đọc như object câu hỏi phẳng


- **Severity:** P1
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Instructor
- **Module:** Assignment.question bị đọc như object câu hỏi phẳng
- **Feature:** Assignment.question bị đọc như object câu hỏi phẳng
- **Action:** renderExamEdit / Open in Studio
- **Symptom:** Backend trả authored fields trong assignment.question; editor đọc stem/content/type/choices/answers/resources ở assignment root, tạo blank/default. Gửi lại có thể dùng Câu hỏi và key mặc định.
- **Expected Behavior:** Đọc-sửa-lưu giữ identity/type/values/references/cấu trúc canonical
- **Actual Behavior:** Backend trả authored fields trong assignment.question; editor đọc stem/content/type/choices/answers/resources ở assignment root, tạo blank/default. Gửi lại có thể dùng Câu hỏi và key mặc định.
- **Frontend File:** frontend/assets/js/views/instructor-exams.js:4090; :4366; :4663; :4682
- **Frontend Function:** renderExamEdit / Open in Studio
- **API Endpoint:** GET /instructor/assessments/{a}
- **Backend File:** src/pwd301/services/assessment_service.py:240; :258; src/pwd301/blueprints/instructor/routes.py:3088
- **Backend Function:** src/pwd301/services/assessment_service.py :: _serialize_assignment; src/pwd301/blueprints/instructor/routes.py :: get_instructor_assessment_detail_route
- **Database Entity/Table:** questions; question_revisions; assignments
- **Technical Cause:** Backend trả authored fields trong assignment.question; editor đọc stem/content/type/choices/answers/resources ở assignment root, tạo blank/default. Gửi lại có thể dùng Câu hỏi và key mặc định.
- **Root Cause:** G01 — Representation / API contract không roundtrip
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** Dữ liệu server còn nhưng form đọc sai sau F5; lưu lại gây dữ liệu lệch.
- **Data Loss Risk:** YES: rủi ro lưu nội dung/key mặc định đè ý định
- **Affected Features:** Instructor → Assignment.question bị đọc như object câu hỏi phẳng → renderExamEdit / Open in Studio
- **Recommended Fix:** Normalize shape tại API boundary, giữ assignment ID/points riêng; roundtrip toàn loại câu và resources.
- **Regression Risk:** Draft IDs, explicit null, immutable revisions, fail-closed resources

### SYNC-008 — attempt_limit bị đọc thành max_attempts và default 1


- **Severity:** P2
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Instructor
- **Module:** attempt_limit bị đọc thành max_attempts và default 1
- **Feature:** attempt_limit bị đọc thành max_attempts và default 1
- **Action:** exam settings/edit
- **Symptom:** Serializer dùng attempt_limit; editor/Studio đọc max_attempts||1, mất giá trị 3 hoặc null unlimited.
- **Expected Behavior:** Đọc-sửa-lưu giữ identity/type/values/references/cấu trúc canonical
- **Actual Behavior:** Serializer dùng attempt_limit; editor/Studio đọc max_attempts||1, mất giá trị 3 hoặc null unlimited.
- **Frontend File:** frontend/assets/js/views/instructor-exams.js:4221; :4697; :4615
- **Frontend Function:** exam settings/edit
- **API Endpoint:** GET/PATCH /instructor/assessments/{a}
- **Backend File:** src/pwd301/services/assessment_service.py:364
- **Backend Function:** src/pwd301/services/assessment_service.py :: _serialize_assessment
- **Database Entity/Table:** assessments
- **Technical Cause:** Serializer dùng attempt_limit; editor/Studio đọc max_attempts||1, mất giá trị 3 hoặc null unlimited.
- **Root Cause:** G01 — Representation / API contract không roundtrip
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5/edit hiển thị 1 rồi draft Save có thể ghi 1.
- **Data Loss Risk:** YES: cấu hình giới hạn bị sửa ngoài ý định
- **Affected Features:** Instructor → attempt_limit bị đọc thành max_attempts và default 1 → exam settings/edit
- **Recommended Fix:** Đọc field canonical và giữ explicit null; không đổi timing đã publish.
- **Regression Risk:** Draft IDs, explicit null, immutable revisions, fail-closed resources

### SYNC-009 — Roundtrip lesson loại bỏ link YouTube đã lưu


- **Severity:** P0
- **Status:** CONFIRMED; SOURCE + VM actual video_urls roundtrip → []. Source/VM confirmation is not live mutation proof.
- **Role:** Instructor
- **Module:** Roundtrip lesson loại bỏ link YouTube đã lưu
- **Feature:** Roundtrip lesson loại bỏ link YouTube đã lưu
- **Action:** parseLessonToBlocks / serializeBlocksToPayload
- **Symptom:** Parser tạo video block có url nhưng thiếu videoType; serializer chỉ nhận videoType=YOUTUBE, gửi video_urls:[]; backend strip marker cũ. Scrape DOM không bổ sung videoType.
- **Expected Behavior:** Đọc-sửa-lưu giữ identity/type/values/references/cấu trúc canonical
- **Actual Behavior:** Parser tạo video block có url nhưng thiếu videoType; serializer chỉ nhận videoType=YOUTUBE, gửi video_urls:[]; backend strip marker cũ. Scrape DOM không bổ sung videoType.
- **Frontend File:** frontend/assets/js/views/instructor.js:695; :706; :770; :815
- **Frontend Function:** parseLessonToBlocks / serializeBlocksToPayload
- **API Endpoint:** PATCH /instructor/lessons/{l}
- **Backend File:** src/pwd301/blueprints/instructor/routes.py:1920; :1927
- **Backend Function:** src/pwd301/blueprints/instructor/routes.py :: update_lesson_route
- **Database Entity/Table:** lessons.markdown_content
- **Technical Cause:** Parser tạo video block có url nhưng thiếu videoType; serializer chỉ nhận videoType=YOUTUBE, gửi video_urls:[]; backend strip marker cũ. Scrape DOM không bổ sung videoType.
- **Root Cause:** G01 — Representation / API contract không roundtrip
- **Evidence:** SOURCE + VM actual video_urls roundtrip → []; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 đọc lesson/draft đã lưu không còn links.
- **Data Loss Risk:** YES: xóa persisted URL trong draft/direct lesson
- **Affected Features:** Instructor → Roundtrip lesson loại bỏ link YouTube đã lưu → parseLessonToBlocks / serializeBlocksToPayload
- **Recommended Fix:** Parse đúng type hoặc serialize URL hợp lệ không lệ thuộc UI-only flag; test parse→scrape→serialize giữ links.
- **Regression Risk:** Draft IDs, explicit null, immutable revisions, fail-closed resources

### SYNC-010 — Response lesson đến muộn ghép nội dung A với ID B


- **Severity:** P0
- **Status:** CONFIRMED; SOURCE + VM Instructor A/B inversion; Student source-only. Source/VM confirmation is not live mutation proof.
- **Role:** Instructor / Student
- **Module:** Response lesson đến muộn ghép nội dung A với ID B
- **Feature:** Response lesson đến muộn ghép nội dung A với ID B
- **Action:** selectLesson / renderActiveContent / save/progress callbacks
- **Symptom:** Shared activeLessonId/activeItem đổi sang B trước await A. Không generation check sau response. Nội dung A render dưới B; Save hoặc progress/quiz callbacks dùng ID mutable B.
- **Expected Behavior:** Response/callback chỉ apply đúng user/role/entity/generation đã khởi tạo
- **Actual Behavior:** Shared activeLessonId/activeItem đổi sang B trước await A. Không generation check sau response. Nội dung A render dưới B; Save hoặc progress/quiz callbacks dùng ID mutable B.
- **Frontend File:** frontend/assets/js/views/instructor.js:1868; :1881; :1893; :2742; frontend/assets/js/views/student.js:2593; :2607; :2989; :3657; :4137
- **Frontend Function:** selectLesson / renderActiveContent / save/progress callbacks
- **API Endpoint:** GET lesson A/B; PATCH lesson; POST progress/quiz-completion
- **Backend File:** src/pwd301/blueprints/instructor/routes.py:1904; src/pwd301/blueprints/student/routes.py:471; :519
- **Backend Function:** src/pwd301/blueprints/instructor/routes.py :: update_lesson_route; src/pwd301/blueprints/student/routes.py :: record_student_progress_route; src/pwd301/blueprints/student/routes.py :: complete_student_lesson_quiz
- **Database Entity/Table:** lessons; lesson_progress
- **Technical Cause:** Shared activeLessonId/activeItem đổi sang B trước await A. Không generation check sau response. Nội dung A render dưới B; Save hoặc progress/quiz callbacks dùng ID mutable B.
- **Root Cause:** G03 — Async response/callback không fence identity
- **Evidence:** SOURCE + VM Instructor A/B inversion; Student source-only; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 quay về server B; trước đó có thể đã ghi nhầm content/progress.
- **Data Loss Risk:** YES: ghi nhầm entity
- **Affected Features:** Instructor / Student → Response lesson đến muộn ghép nội dung A với ID B → selectLesson / renderActiveContent / save/progress callbacks
- **Recommended Fix:** Capture immutable ID + request generation; bỏ obsolete response; bind mọi handler với ID đã load, không current shared ID.
- **Regression Risk:** Navigation/history, lesson cleanup, account switch, upload/AI context

### SYNC-011 — Save clone published lesson bỏ qua draft identity trả về


- **Severity:** P1
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Instructor
- **Module:** Save clone published lesson bỏ qua draft identity trả về
- **Feature:** Save clone published lesson bỏ qua draft identity trả về
- **Action:** handleSave
- **Symptom:** Save đầu tạo draft ID mới nhưng client discard response, giữ ID live cũ. Chọn lại đọc bản live cũ; save nội dung cũ có thể làm draft hiện có bị đánh dấu bỏ.
- **Expected Behavior:** Đọc-sửa-lưu giữ identity/type/values/references/cấu trúc canonical
- **Actual Behavior:** Save đầu tạo draft ID mới nhưng client discard response, giữ ID live cũ. Chọn lại đọc bản live cũ; save nội dung cũ có thể làm draft hiện có bị đánh dấu bỏ.
- **Frontend File:** frontend/assets/js/views/instructor.js:2742; :2745
- **Frontend Function:** handleSave
- **API Endpoint:** PATCH /instructor/lessons/{l}; GET lesson original
- **Backend File:** src/pwd301/blueprints/instructor/routes.py:2000; :2064; :2089; :2136; src/pwd301/services/lesson_service.py:2669; :2723
- **Backend Function:** src/pwd301/blueprints/instructor/routes.py :: update_lesson_route; src/pwd301/services/lesson_service.py :: get_lesson_detail_with_draft
- **Database Entity/Table:** lessons previous_lesson_id; course_change_requests
- **Technical Cause:** Save đầu tạo draft ID mới nhưng client discard response, giữ ID live cũ. Chọn lại đọc bản live cũ; save nội dung cũ có thể làm draft hiện có bị đánh dấu bỏ.
- **Root Cause:** G01 — Representation / API contract không roundtrip
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5/chọn lại có thể thấy live content cũ dù draft đã persist.
- **Data Loss Risk:** YES: rủi ro bỏ draft qua subsequent stale save
- **Affected Features:** Instructor → Save clone published lesson bỏ qua draft identity trả về → handleSave
- **Recommended Fix:** Reconcile draft ID/tree/URL từ response hoặc consistent working-draft resolution server-side.
- **Regression Risk:** Draft IDs, explicit null, immutable revisions, fail-closed resources

### SYNC-012 — Move lesson published bị backend ép về chapter cũ


- **Severity:** P1
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Instructor
- **Module:** Move lesson published bị backend ép về chapter cũ
- **Feature:** Move lesson published bị backend ép về chapter cũ
- **Action:** cross-chapter move
- **Symptom:** Clone đầu unconditionally đặt learning_unit_id từ original, override incoming target. UI đã di chuyển local.
- **Expected Behavior:** Đọc-sửa-lưu giữ identity/type/values/references/cấu trúc canonical
- **Actual Behavior:** Clone đầu unconditionally đặt learning_unit_id từ original, override incoming target. UI đã di chuyển local.
- **Frontend File:** frontend/assets/js/views/instructor.js:1658; :1753
- **Frontend Function:** cross-chapter move
- **API Endpoint:** PATCH /instructor/lessons/{l}
- **Backend File:** src/pwd301/blueprints/instructor/routes.py:2125
- **Backend Function:** src/pwd301/blueprints/instructor/routes.py :: update_lesson_route
- **Database Entity/Table:** lessons.learning_unit_id
- **Technical Cause:** Clone đầu unconditionally đặt learning_unit_id từ original, override incoming target. UI đã di chuyển local.
- **Root Cause:** G01 — Representation / API contract không roundtrip
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 cho lesson/draft ở chapter cũ.
- **Data Loss Risk:** NO: sai vị trí, dữ liệu còn
- **Affected Features:** Instructor → Move lesson published bị backend ép về chapter cũ → cross-chapter move
- **Recommended Fix:** Giữ target đã authorize/validate khi clone; dùng location returned cho UI.
- **Regression Risk:** Draft IDs, explicit null, immutable revisions, fail-closed resources

### SYNC-013 — Changeset mới hủy proposal cũ mà không merge intent


- **Severity:** P1
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Instructor / Admin
- **Module:** Changeset mới hủy proposal cũ mà không merge intent
- **Feature:** Changeset mới hủy proposal cũ mà không merge intent
- **Action:** submit consolidated update
- **Symptom:** Manifest mới chỉ có modified/added/deleted lessons nhưng chuyển mọi request PENDING của course thành CANCELLED. Pending rename/reorder/resource/metadata/governance proposal không được merge. Canonical course rule line7 yêu cầu single consolidated draft.
- **Expected Behavior:** Unified draft giữ additions/edits/moves/deletions; approval promotes final representation
- **Actual Behavior:** Manifest mới chỉ có modified/added/deleted lessons nhưng chuyển mọi request PENDING của course thành CANCELLED. Pending rename/reorder/resource/metadata/governance proposal không được merge. Canonical course rule line7 yêu cầu single consolidated draft.
- **Frontend File:** frontend/assets/js/views/instructor.js:3966
- **Frontend Function:** submit consolidated update
- **API Endpoint:** POST /instructor/courses/{c}/changeset/submit
- **Backend File:** src/pwd301/services/lesson_service.py:3083; :3092; :3110; src/pwd301/blueprints/instructor/routes.py:960; :1090; :1168; :1510
- **Backend Function:** src/pwd301/services/lesson_service.py :: submit_course_changeset; src/pwd301/blueprints/instructor/routes.py :: reorder_learning_units_route; src/pwd301/blueprints/instructor/routes.py :: delete_learning_unit_route; src/pwd301/blueprints/instructor/routes.py :: update_learning_unit_route; src/pwd301/blueprints/instructor/routes.py :: attach_lesson_resource_route
- **Database Entity/Table:** course_change_requests; lessons; learning_units; lesson_resources
- **Technical Cause:** Manifest mới chỉ có modified/added/deleted lessons nhưng chuyển mọi request PENDING của course thành CANCELLED. Pending rename/reorder/resource/metadata/governance proposal không được merge. Canonical course rule line7 yêu cầu single consolidated draft.
- **Root Cause:** G05 — Draft manifest không giữ toàn intent
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 mất proposal khỏi queue actionable; JSON CANCELLED còn recoverable.
- **Data Loss Risk:** YES: mất ý định khỏi workflow; không xóa vật lý JSON
- **Affected Features:** Instructor / Admin → Changeset mới hủy proposal cũ mà không merge intent → submit consolidated update
- **Recommended Fix:** Stage toàn category vào manifest; chỉ supersede intent đã được đưa vào phiên mới; preserve recovery history.
- **Regression Risk:** Lesson/progress history, cancelled request recovery, pending lock409

### SYNC-014 — Attachment đã xóa trong draft sống lại khi approve


- **Severity:** P1
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Instructor / Admin
- **Module:** Attachment đã xóa trong draft sống lại khi approve
- **Feature:** Attachment đã xóa trong draft sống lại khi approve
- **Action:** detach draft resource / Admin approve
- **Symptom:** Promotion gọi _copy_lesson_resources(original,draft) lần nữa, thêm links source đang thiếu do deletion đã commit trong draft.
- **Expected Behavior:** Unified draft giữ additions/edits/moves/deletions; approval promotes final representation
- **Actual Behavior:** Promotion gọi _copy_lesson_resources(original,draft) lần nữa, thêm links source đang thiếu do deletion đã commit trong draft.
- **Frontend File:** frontend/assets/js/views/instructor.js:2950; :3080
- **Frontend Function:** detach draft resource / Admin approve
- **API Endpoint:** DELETE lesson resource; POST /admin/course-changes/{id}/approve
- **Backend File:** src/pwd301/services/lesson_service.py:4110; :2049; :2087; src/pwd301/services/file_service.py:1318
- **Backend Function:** src/pwd301/services/lesson_service.py :: apply_course_version_changeset; src/pwd301/services/lesson_service.py :: _copy_lesson_resources; src/pwd301/services/file_service.py :: detach_resource_from_lesson
- **Database Entity/Table:** lesson_resources; lessons
- **Technical Cause:** Promotion gọi _copy_lesson_resources(original,draft) lần nữa, thêm links source đang thiếu do deletion đã commit trong draft.
- **Root Cause:** G05 — Draft manifest không giữ toàn intent
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 sau approval thấy tài liệu vừa xóa quay lại.
- **Data Loss Risk:** NO: resurrection/sai deletion; reference cũ không mất
- **Affected Features:** Instructor / Admin → Attachment đã xóa trong draft sống lại khi approve → detach draft resource / Admin approve
- **Recommended Fix:** Chỉ copy khi tạo clone; promotion dùng resource set/tombstones của draft.
- **Regression Risk:** Lesson/progress history, cancelled request recovery, pending lock409

### SYNC-015 — HTTP202 pending_approval bị hiển thị như mutation đã áp dụng


- **Severity:** P1
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Instructor
- **Module:** HTTP202 pending_approval bị hiển thị như mutation đã áp dụng
- **Feature:** HTTP202 pending_approval bị hiển thị như mutation đã áp dụng
- **Action:** unit rename/delete/reorder; resource attach/detach; course metadata
- **Symptom:** Các handler coi mọi fulfilled 2xx là applied, sửa local nodes/files. 202 attach không trả resource_id/URL nhưng vẫn push phantom resource.
- **Expected Behavior:** Applied/pending/error/partial được phân biệt, UI reconcile sau acknowledgement
- **Actual Behavior:** Các handler coi mọi fulfilled 2xx là applied, sửa local nodes/files. 202 attach không trả resource_id/URL nhưng vẫn push phantom resource.
- **Frontend File:** frontend/assets/js/views/instructor.js:1427; :1450; :1475; :1510; :2931; :3015; :6507
- **Frontend Function:** unit rename/delete/reorder; resource attach/detach; course metadata
- **API Endpoint:** PATCH/DELETE learning unit; POST/DELETE resources; POST course update
- **Backend File:** src/pwd301/blueprints/instructor/routes.py:983; :1129; :1229; :1514; :1557; :790
- **Backend Function:** src/pwd301/blueprints/instructor/routes.py :: reorder_learning_units_route; src/pwd301/blueprints/instructor/routes.py :: delete_learning_unit_route; src/pwd301/blueprints/instructor/routes.py :: update_learning_unit_route; src/pwd301/blueprints/instructor/routes.py :: attach_lesson_resource_route; src/pwd301/blueprints/instructor/routes.py :: detach_lesson_resource_route; src/pwd301/blueprints/instructor/routes.py :: update_course_route
- **Database Entity/Table:** course_change_requests; learning_units; lesson_resources; courses
- **Technical Cause:** Các handler coi mọi fulfilled 2xx là applied, sửa local nodes/files. 202 attach không trả resource_id/URL nhưng vẫn push phantom resource.
- **Root Cause:** G02 — Acknowledgement không gắn authoritative state
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 lấy live state cũ cho tới approval; đây có persist proposal, không phải DB mất row.
- **Data Loss Risk:** NO: UI/server split
- **Affected Features:** Instructor → HTTP202 pending_approval bị hiển thị như mutation đã áp dụng → unit rename/delete/reorder; resource attach/detach; course metadata
- **Recommended Fix:** Branch applied vs pending; render proposal/draft authoritative và trạng thái chờ duyệt, không claim live change.
- **Regression Risk:** 202 workflow, CSRF retry, idempotency, input chưa lưu

### SYNC-016 — Academic Save nuốt lỗi prerequisite rồi báo tất cả đã lưu


- **Severity:** P1
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Instructor
- **Module:** Academic Save nuốt lỗi prerequisite rồi báo tất cả đã lưu
- **Feature:** Academic Save nuốt lỗi prerequisite rồi báo tất cả đã lưu
- **Action:** Save academic settings
- **Symptom:** Mỗi add/delete prerequisite catch bị suppress; Save vẫn success/refetch. Các submutation đã commit riêng, unsuccessful staging mất sau re-render.
- **Expected Behavior:** Applied/pending/error/partial được phân biệt, UI reconcile sau acknowledgement
- **Actual Behavior:** Mỗi add/delete prerequisite catch bị suppress; Save vẫn success/refetch. Các submutation đã commit riêng, unsuccessful staging mất sau re-render.
- **Frontend File:** frontend/assets/js/views/instructor.js:5323; :5336; :5346; :5361
- **Frontend Function:** Save academic settings
- **API Endpoint:** course update; completion-rules; prerequisites add/delete
- **Backend File:** src/pwd301/blueprints/instructor/routes.py:2536; :2737; :3015
- **Backend Function:** src/pwd301/blueprints/instructor/routes.py :: add_course_prerequisite_route; src/pwd301/blueprints/instructor/routes.py :: remove_course_prerequisite_route; src/pwd301/blueprints/instructor/routes.py :: set_course_completion_rules_route
- **Database Entity/Table:** courses; course_completion_rules; course_prerequisites
- **Technical Cause:** Mỗi add/delete prerequisite catch bị suppress; Save vẫn success/refetch. Các submutation đã commit riêng, unsuccessful staging mất sau re-render.
- **Root Cause:** G02 — Acknowledgement không gắn authoritative state
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 giữ phần đã commit và bỏ phần fail.
- **Data Loss Risk:** YES: local intent chưa lưu bị bỏ
- **Affected Features:** Instructor → Academic Save nuốt lỗi prerequisite rồi báo tất cả đã lưu → Save academic settings
- **Recommended Fix:** Aggregate partial errors; giữ các thay đổi chưa lưu, reconcile từng authoritative response; cân nhắc outer transaction cho action composite.
- **Regression Risk:** 202 workflow, CSRF retry, idempotency, input chưa lưu

### SYNC-017 — Xóa whole resource block không detach database links


- **Severity:** P1
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Instructor
- **Module:** Xóa whole resource block không detach database links
- **Feature:** Xóa whole resource block không detach database links
- **Action:** remove document/video block → Save
- **Symptom:** Block removal chỉ splice local; serializer resources nhưng lesson update không reconcile resource set. Links chỉ đổi bằng attach/detach riêng.
- **Expected Behavior:** Đọc-sửa-lưu giữ identity/type/values/references/cấu trúc canonical
- **Actual Behavior:** Block removal chỉ splice local; serializer resources nhưng lesson update không reconcile resource set. Links chỉ đổi bằng attach/detach riêng.
- **Frontend File:** frontend/assets/js/views/instructor.js:2905; :2911; :774; :810
- **Frontend Function:** remove document/video block → Save
- **API Endpoint:** PATCH /instructor/lessons/{l}
- **Backend File:** src/pwd301/services/lesson_service.py:756; src/pwd301/blueprints/instructor/routes.py:1904
- **Backend Function:** src/pwd301/services/lesson_service.py :: update_lesson; src/pwd301/blueprints/instructor/routes.py :: update_lesson_route
- **Database Entity/Table:** lesson_resources
- **Technical Cause:** Block removal chỉ splice local; serializer resources nhưng lesson update không reconcile resource set. Links chỉ đổi bằng attach/detach riêng.
- **Root Cause:** G01 — Representation / API contract không roundtrip
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 tái hiện attachments còn trong DB.
- **Data Loss Risk:** NO: deletion không persist
- **Affected Features:** Instructor → Xóa whole resource block không detach database links → remove document/video block → Save
- **Recommended Fix:** Detach contained persisted links explicitly hoặc backend applies intended resource set with authorization; giữ fail-closed file lifecycle.
- **Regression Risk:** Draft IDs, explicit null, immutable revisions, fail-closed resources

### SYNC-018 — Thứ tự block tự do không có representation persist


- **Severity:** P2
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Instructor
- **Module:** Thứ tự block tự do không có representation persist
- **Feature:** Thứ tự block tự do không có representation persist
- **Action:** reorder text/video/document/quiz → Save
- **Symptom:** Serializer flatten text rồi gom theo type; parser rebuild text→videos→documents→quizzes. Order xen kẽ và separate text blocks bị mất.
- **Expected Behavior:** Đọc-sửa-lưu giữ identity/type/values/references/cấu trúc canonical
- **Actual Behavior:** Serializer flatten text rồi gom theo type; parser rebuild text→videos→documents→quizzes. Order xen kẽ và separate text blocks bị mất.
- **Frontend File:** frontend/assets/js/views/instructor.js:695; :722; :760; :804
- **Frontend Function:** reorder text/video/document/quiz → Save
- **API Endpoint:** PATCH lesson
- **Backend File:** src/pwd301/blueprints/instructor/routes.py:1904
- **Backend Function:** src/pwd301/blueprints/instructor/routes.py :: update_lesson_route
- **Database Entity/Table:** lessons.markdown_content; lesson_resources
- **Technical Cause:** Serializer flatten text rồi gom theo type; parser rebuild text→videos→documents→quizzes. Order xen kẽ và separate text blocks bị mất.
- **Root Cause:** G01 — Representation / API contract không roundtrip
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 trở về thứ tự theo type.
- **Data Loss Risk:** YES: mất cấu trúc sắp xếp, không nhất thiết mất text
- **Affected Features:** Instructor → Thứ tự block tự do không có representation persist → reorder text/video/document/quiz → Save
- **Recommended Fix:** Chốt canonical ordered content representation; test roundtrip; không thêm framework/rewrites.
- **Regression Risk:** Draft IDs, explicit null, immutable revisions, fail-closed resources

### SYNC-019 — Chọn bài khác bỏ input chưa Save


- **Severity:** P2
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Instructor
- **Module:** Chọn bài khác bỏ input chưa Save
- **Feature:** Chọn bài khác bỏ input chưa Save
- **Action:** lesson selection
- **Symptom:** Editor bị thay ngay, không dirty warning, không lưu lại draft form local. Submit consolidated changeset cũng không flush editor đang chưa Save.
- **Expected Behavior:** Unsaved input có warning/recovery; created backend ID checkpoint cho retry
- **Actual Behavior:** Editor bị thay ngay, không dirty warning, không lưu lại draft form local. Submit consolidated changeset cũng không flush editor đang chưa Save.
- **Frontend File:** frontend/assets/js/views/instructor.js:1868; :1877
- **Frontend Function:** lesson selection
- **API Endpoint:** GET lesson; không gửi Save
- **Backend File:** Không có backend mutation trước navigation
- **Backend Function:** Local-only client action; no backend mutation invoked. Storage context and endpoint inventory are documented separately.
- **Database Entity/Table:** local activeBlocks/form
- **Technical Cause:** Editor bị thay ngay, không dirty warning, không lưu lại draft form local. Submit consolidated changeset cũng không flush editor đang chưa Save.
- **Root Cause:** G15 — Dirty workflow thiếu checkpoint/recovery
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5/navigation bỏ unsaved input; không phải committed DB loss.
- **Data Loss Risk:** YES: unsaved input
- **Affected Features:** Instructor → Chọn bài khác bỏ input chưa Save → lesson selection
- **Recommended Fix:** Dirty tracking + lựa chọn Lưu/Bỏ thay đổi/Ở lại; chỉ Save bằng hành động rõ ràng.
- **Regression Risk:** Lazy explicit create, clean history, không save nhầm entity

### SYNC-020 — Reorder/move optimistic memory không rollback khi API lỗi


- **Severity:** P2
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Instructor
- **Module:** Reorder/move optimistic memory không rollback khi API lỗi
- **Feature:** Reorder/move optimistic memory không rollback khi API lỗi
- **Action:** curriculum up/down/drag/move
- **Symptom:** Arrays đổi trước await; lỗi chỉ toast, không restore/refetch. Hành động sau xây payload từ memory đã lệch.
- **Expected Behavior:** Applied/pending/error/partial được phân biệt, UI reconcile sau acknowledgement
- **Actual Behavior:** Arrays đổi trước await; lỗi chỉ toast, không restore/refetch. Hành động sau xây payload từ memory đã lệch.
- **Frontend File:** frontend/assets/js/views/instructor.js:1470; :1489; :1533; :1554; :1625; :1746
- **Frontend Function:** curriculum up/down/drag/move
- **API Endpoint:** unit/lesson reorder; lesson PATCH
- **Backend File:** src/pwd301/blueprints/instructor/routes.py:946; :2167
- **Backend Function:** src/pwd301/blueprints/instructor/routes.py :: reorder_learning_units_route; src/pwd301/blueprints/instructor/routes.py :: reorder_lessons_route
- **Database Entity/Table:** learning_units; lessons
- **Technical Cause:** Arrays đổi trước await; lỗi chỉ toast, không restore/refetch. Hành động sau xây payload từ memory đã lệch.
- **Root Cause:** G02 — Acknowledgement không gắn authoritative state
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 trả server order đúng nhưng UI trước đó sai.
- **Data Loss Risk:** NO: stale UI; subsequent mutation risk
- **Affected Features:** Instructor → Reorder/move optimistic memory không rollback khi API lỗi → curriculum up/down/drag/move
- **Recommended Fix:** Snapshot local state hoặc refetch authoritative sau error; serialize pending order actions.
- **Regression Risk:** 202 workflow, CSRF retry, idempotency, input chưa lưu

### SYNC-021 — Retry publish tạo assessment backend mới do không checkpoint ID


- **Severity:** P2
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Instructor
- **Module:** Retry publish tạo assessment backend mới do không checkpoint ID
- **Feature:** Retry publish tạo assessment backend mới do không checkpoint ID
- **Action:** publish retry after create succeeded
- **Symptom:** Created asmId chỉ variable local, không saveDraft. Publication lỗi giữ local draft không có backend ID; retry lại create.
- **Expected Behavior:** Unsaved input có warning/recovery; created backend ID checkpoint cho retry
- **Actual Behavior:** Created asmId chỉ variable local, không saveDraft. Publication lỗi giữ local draft không có backend ID; retry lại create.
- **Frontend File:** frontend/assets/js/views/instructor-exams.js:3947; :3948; :4028
- **Frontend Function:** publish retry after create succeeded
- **API Endpoint:** POST /instructor/courses/{c}/assessments
- **Backend File:** src/pwd301/services/assessment_service.py:625
- **Backend Function:** src/pwd301/services/assessment_service.py :: create_assessment
- **Database Entity/Table:** assessments; local ExamStore
- **Technical Cause:** Created asmId chỉ variable local, không saveDraft. Publication lỗi giữ local draft không có backend ID; retry lại create.
- **Root Cause:** G15 — Dirty workflow thiếu checkpoint/recovery
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5/retry có thể tạo duplicate assessment drafts.
- **Data Loss Risk:** NO: duplicate/orphan records
- **Affected Features:** Instructor → Retry publish tạo assessment backend mới do không checkpoint ID → publish retry after create succeeded
- **Recommended Fix:** Persist returned assessment ID/checkpoint vào scoped draft trước bước câu hỏi; submission guard/idempotency.
- **Regression Risk:** Lazy explicit create, clean history, không save nhầm entity

### SYNC-022 — Curriculum exam deep-link không khởi tạo đúng editor/scope


- **Severity:** P1
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Instructor
- **Module:** Curriculum exam deep-link không khởi tạo đúng editor/scope
- **Feature:** Curriculum exam deep-link không khởi tạo đúng editor/scope
- **Action:** Sửa đề / Tạo kiểm tra chapter / Final Test
- **Symptom:** Hub chỉ consumes course ID; assessment_id/unit_id/is_final từ CTA không được đọc để edit/scoped create.
- **Expected Behavior:** Deep-link tải đúng object; chapter/final relation canonical
- **Actual Behavior:** Hub chỉ consumes course ID; assessment_id/unit_id/is_final từ CTA không được đọc để edit/scoped create.
- **Frontend File:** frontend/assets/js/views/instructor.js:1280; :1317; :1360; frontend/assets/js/views/instructor-exams.js:450
- **Frontend Function:** Sửa đề / Tạo kiểm tra chapter / Final Test
- **API Endpoint:** hash /instructor/exams?assessment_id|unit_id|is_final
- **Backend File:** frontend/assets/js/router.js:534; :561; src/pwd301/blueprints/instructor/routes.py:674
- **Backend Function:** src/pwd301/blueprints/instructor/routes.py :: create_course_route
- **Database Entity/Table:** local ExamStore; assessments khi publish
- **Technical Cause:** Hub chỉ consumes course ID; assessment_id/unit_id/is_final từ CTA không được đọc để edit/scoped create.
- **Root Cause:** G12 — Routing/scope không gắn persisted identity
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 giữ URL nhưng không hydrate assessment/chapter intended.
- **Data Loss Risk:** NO: sai workflow và có thể tạo nhầm scope
- **Affected Features:** Instructor → Curriculum exam deep-link không khởi tạo đúng editor/scope → Sửa đề / Tạo kiểm tra chapter / Final Test
- **Recommended Fix:** Định tuyến edit đúng /exams/edit và explicitly initialize scope trước authoring; capture canonical identity.
- **Regression Risk:** Hash replaceState, object auth, timing locks, schema changes

### SYNC-023 — Chapter assessment association không persist, UI suy đoán từ title


- **Severity:** P1
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Instructor / Student
- **Module:** Chapter assessment association không persist, UI suy đoán từ title
- **Feature:** Chapter assessment association không persist, UI suy đoán từ title
- **Action:** chapter test / final setup
- **Symptom:** learning_unit_id input bị bỏ; Assessment/serializer không có association. Tree dùng title heuristic, unlinked assessment bị coi Final Test; rename/order có thể đổi mapping.
- **Expected Behavior:** Deep-link tải đúng object; chapter/final relation canonical
- **Actual Behavior:** learning_unit_id input bị bỏ; Assessment/serializer không có association. Tree dùng title heuristic, unlinked assessment bị coi Final Test; rename/order có thể đổi mapping.
- **Frontend File:** frontend/assets/js/views/instructor.js:1173; :1348; frontend/assets/js/views/instructor-exams.js:3940
- **Frontend Function:** chapter test / final setup
- **API Endpoint:** POST/PATCH assessment
- **Backend File:** src/pwd301/services/assessment_service.py:625; :352; src/pwd301/models/assessment.py
- **Backend Function:** src/pwd301/services/assessment_service.py :: create_assessment; src/pwd301/services/assessment_service.py :: _serialize_assessment
- **Database Entity/Table:** assessments; learning_units
- **Technical Cause:** learning_unit_id input bị bỏ; Assessment/serializer không có association. Tree dùng title heuristic, unlinked assessment bị coi Final Test; rename/order có thể đổi mapping.
- **Root Cause:** G12 — Routing/scope không gắn persisted identity
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 dựng lại association theo heuristic, không phải FK đã lưu.
- **Data Loss Risk:** NO: sai association/eligibility
- **Affected Features:** Instructor / Student → Chapter assessment association không persist, UI suy đoán từ title → chapter test / final setup
- **Recommended Fix:** Chốt relationship theo canonical spec, migrate trên bản sao và return persisted scope; không thêm title heuristics.
- **Regression Risk:** Hash replaceState, object auth, timing locks, schema changes

### SYNC-024 — Bloom ANALYZE/EVALUATE/CREATE silently chuyển UNDERSTAND


- **Severity:** P2
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Instructor
- **Module:** Bloom ANALYZE/EVALUATE/CREATE silently chuyển UNDERSTAND
- **Feature:** Bloom ANALYZE/EVALUATE/CREATE silently chuyển UNDERSTAND
- **Action:** save question taxonomy
- **Symptom:** UI có 6 levels; routes chỉ nhận 3 và silently coerce value ngoài set.
- **Expected Behavior:** Đọc-sửa-lưu giữ identity/type/values/references/cấu trúc canonical
- **Actual Behavior:** UI có 6 levels; routes chỉ nhận 3 và silently coerce value ngoài set.
- **Frontend File:** frontend/assets/js/views/instructor-exams.js:3961; :3969
- **Frontend Function:** save question taxonomy
- **API Endpoint:** POST questions/create / batch / edit
- **Backend File:** src/pwd301/blueprints/instructor/routes.py:3322; :3514; :3734
- **Backend Function:** src/pwd301/blueprints/instructor/routes.py :: create_instructor_assessment_question_route; src/pwd301/blueprints/instructor/routes.py :: batch_create_instructor_assessment_questions_route; src/pwd301/blueprints/instructor/routes.py :: edit_instructor_assessment_question_route
- **Database Entity/Table:** questions/question_revisions difficulty
- **Technical Cause:** UI có 6 levels; routes chỉ nhận 3 và silently coerce value ngoài set.
- **Root Cause:** G01 — Representation / API contract không roundtrip
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 thấy taxonomy khác selection.
- **Data Loss Risk:** YES: mất giá trị đã chọn
- **Affected Features:** Instructor → Bloom ANALYZE/EVALUATE/CREATE silently chuyển UNDERSTAND → save question taxonomy
- **Recommended Fix:** Đối chiếu canonical supported levels; hỗ trợ hoặc reject explicitly; giữ authored value khi roundtrip.
- **Regression Risk:** Draft IDs, explicit null, immutable revisions, fail-closed resources

### SYNC-025 — Quick Add short answer lưu literal key Đáp án


- **Severity:** P1
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Instructor
- **Module:** Quick Add short answer lưu literal key Đáp án
- **Feature:** Quick Add short answer lưu literal key Đáp án
- **Action:** Quick Add SHORT_ANSWER
- **Symptom:** Form không collect accepted answer, gửi ['Đáp án']; API success nhưng grading key không do instructor nhập.
- **Expected Behavior:** Backend enforce owner/lifecycle/reauth/scoring/evidence/retry status
- **Actual Behavior:** Form không collect accepted answer, gửi ['Đáp án']; API success nhưng grading key không do instructor nhập.
- **Frontend File:** frontend/assets/js/views/instructor-exams.js:4867; :4490
- **Frontend Function:** Quick Add SHORT_ANSWER
- **API Endpoint:** POST questions/create
- **Backend File:** src/pwd301/blueprints/instructor/routes.py:3269
- **Backend Function:** src/pwd301/blueprints/instructor/routes.py :: create_instructor_assessment_question_route
- **Database Entity/Table:** question_revision_accepted_answers
- **Technical Cause:** Form không collect accepted answer, gửi ['Đáp án']; API success nhưng grading key không do instructor nhập.
- **Root Cause:** G10 — Authority còn dựa frontend
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 giữ key literal sai.
- **Data Loss Risk:** NO: sai grading key được persist
- **Affected Features:** Instructor → Quick Add short answer lưu literal key Đáp án → Quick Add SHORT_ANSWER
- **Recommended Fix:** Collect/validate accepted answers trước create, return canonical authored key.
- **Regression Risk:** RBAC/CSRF, immutable audit, FileAsset scan, concurrency

### SYNC-026 — Save/upload callback dùng lesson/block mutable sau await


- **Severity:** P1
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Instructor
- **Module:** Save/upload callback dùng lesson/block mutable sau await
- **Feature:** Save/upload callback dùng lesson/block mutable sau await
- **Action:** save completion / multi-file upload / paste image
- **Symptom:** Switch bài trong request: completion cập nhật tree B thay A; multi-file loop có thể gửi các file sau cho B. Block index async paste cũng có thể thay đổi.
- **Expected Behavior:** Response/callback chỉ apply đúng user/role/entity/generation đã khởi tạo
- **Actual Behavior:** Switch bài trong request: completion cập nhật tree B thay A; multi-file loop có thể gửi các file sau cho B. Block index async paste cũng có thể thay đổi.
- **Frontend File:** frontend/assets/js/views/instructor.js:2742; :2745; :2931; :3015; :3016
- **Frontend Function:** save completion / multi-file upload / paste image
- **API Endpoint:** PATCH lesson; POST resources
- **Backend File:** src/pwd301/blueprints/instructor/routes.py:1462; :1904
- **Backend Function:** src/pwd301/blueprints/instructor/routes.py :: attach_lesson_resource_route; src/pwd301/blueprints/instructor/routes.py :: update_lesson_route
- **Database Entity/Table:** lessons; lesson_resources; file_assets
- **Technical Cause:** Switch bài trong request: completion cập nhật tree B thay A; multi-file loop có thể gửi các file sau cho B. Block index async paste cũng có thể thay đổi.
- **Root Cause:** G03 — Async response/callback không fence identity
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 bộc lộ reference/UI khác nội dung vừa upload.
- **Data Loss Risk:** YES: ghi file/reference nhầm entity
- **Affected Features:** Instructor → Save/upload callback dùng lesson/block mutable sau await → save completion / multi-file upload / paste image
- **Recommended Fix:** Capture lesson/block IDs once, reconcile chỉ editor generation còn hợp lệ; guard mutation ownership.
- **Regression Risk:** Navigation/history, lesson cleanup, account switch, upload/AI context

### SYNC-027 — F5 reset autosave sequence, backend từ chối sửa đáp án đã lưu


- **Severity:** P0
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Student
- **Module:** F5 reset autosave sequence, backend từ chối sửa đáp án đã lưu
- **Feature:** F5 reset autosave sequence, backend từ chối sửa đáp án đã lưu
- **Action:** renderAttemptConsole / saveAnswerInOrder
- **Symptom:** Counter browser reset0; delivery có answer nhưng không có last_client_sequence/version. Ví dụ saved sequence7 → F5 → new sequence1 bị reject <=7.
- **Expected Behavior:** Autosave monotonic/idempotent qua retry/F5; dirty input flush trước deadline
- **Actual Behavior:** Counter browser reset0; delivery có answer nhưng không có last_client_sequence/version. Ví dụ saved sequence7 → F5 → new sequence1 bị reject <=7.
- **Frontend File:** frontend/assets/js/views/student.js:4974; :4979
- **Frontend Function:** renderAttemptConsole / saveAnswerInOrder
- **API Endpoint:** GET /student/attempt/{a}; POST answers/{q}
- **Backend File:** src/pwd301/services/attempt_service.py:953; :1526; :1545
- **Backend Function:** src/pwd301/services/attempt_service.py :: get_attempt_delivery; src/pwd301/services/attempt_service.py :: save_attempt_answer
- **Database Entity/Table:** attempt_answers.last_client_sequence; attempt_answer_events
- **Technical Cause:** Counter browser reset0; delivery có answer nhưng không có last_client_sequence/version. Ví dụ saved sequence7 → F5 → new sequence1 bị reject <=7.
- **Root Cause:** G07 — Local sequence/event không nối durable sequence
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 khôi phục old answer; new local answer không persist.
- **Data Loss Risk:** YES: sửa đáp án không lưu; chưa live recreate
- **Affected Features:** Student → F5 reset autosave sequence, backend từ chối sửa đáp án đã lưu → renderAttemptConsole / saveAnswerInOrder
- **Recommended Fix:** Return persisted per-question sequence/version; initialize counter từ authoritative delivery; giữ ordered queue/change IDs.
- **Regression Risk:** Per-question queues, UUID dedupe, stale/offline rejection

### SYNC-028 — Editing lease không enforce owner/expiry ở mọi đường vào


- **Severity:** P1
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Student
- **Module:** Editing lease không enforce owner/expiry ở mọi đường vào
- **Feature:** Editing lease không enforce owner/expiry ở mọi đường vào
- **Action:** delivery/takeover/submit
- **Symptom:** Cùng Flask session chia sẻ raw token cho nhiều tab; takeover không đòi expiry/loss; ordinary submit kiểm token chỉ khi token supplied. Session khác cùng Student omit token có thể finalize trước owner. Frontend không heartbeat short lease; lease thường theo exam duration.
- **Expected Behavior:** Một tab owner hợp lệ edit/submit, takeover chỉ lost/expired
- **Actual Behavior:** Cùng Flask session chia sẻ raw token cho nhiều tab; takeover không đòi expiry/loss; ordinary submit kiểm token chỉ khi token supplied. Session khác cùng Student omit token có thể finalize trước owner. Frontend không heartbeat short lease; lease thường theo exam duration.
- **Frontend File:** frontend/assets/js/views/student.js:4955; frontend/assets/js/api.js:453
- **Frontend Function:** delivery/takeover/submit
- **API Endpoint:** GET attempt; POST lease/takeover; POST submit
- **Backend File:** src/pwd301/blueprints/student/routes.py:120; :150; :931; src/pwd301/services/attempt_service.py:1176; :1199; :2006; :2015
- **Backend Function:** src/pwd301/blueprints/student/routes.py :: attempt_view; src/pwd301/blueprints/student/routes.py :: submit_student_attempt; src/pwd301/services/attempt_service.py :: takeover_attempt_lease; src/pwd301/services/attempt_service.py :: submit_assessment_attempt
- **Database Entity/Table:** assessment_attempts lease fields; auth session
- **Technical Cause:** Cùng Flask session chia sẻ raw token cho nhiều tab; takeover không đòi expiry/loss; ordinary submit kiểm token chỉ khi token supplied. Session khác cùng Student omit token có thể finalize trước owner. Frontend không heartbeat short lease; lease thường theo exam duration.
- **Root Cause:** G06 — Editing lease chưa enforce mọi boundary
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 renew/takeover và đổi fencing state; không proof multi-tab runtime.
- **Data Loss Risk:** YES: có thể finalize khi owner còn unsaved answers
- **Affected Features:** Student → Editing lease không enforce owner/expiry ở mọi đường vào → delivery/takeover/submit
- **Recommended Fix:** Per-tab identity và conditional acquire/renew/takeover; require valid current owner token với submit thường; tách authorized server-expiry finalizer.
- **Regression Risk:** Server expiry finalizer, stable attempt/deadline, idempotent submit

### SYNC-029 — Text/fill chỉ save change, deadline/F5 không flush input đang gõ


- **Severity:** P0
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Student
- **Module:** Text/fill chỉ save change, deadline/F5 không flush input đang gõ
- **Feature:** Text/fill chỉ save change, deadline/F5 không flush input đang gõ
- **Action:** text input / handleSubmit(forced)
- **Symptom:** Không input debounce 1–2s; submit chỉ chờ promises đã tạo, không serialize focused input. Timer forced submit không blur/flush.
- **Expected Behavior:** Autosave monotonic/idempotent qua retry/F5; dirty input flush trước deadline
- **Actual Behavior:** Không input debounce 1–2s; submit chỉ chờ promises đã tạo, không serialize focused input. Timer forced submit không blur/flush.
- **Frontend File:** frontend/assets/js/views/student.js:5667; :5698; :5823; :5907
- **Frontend Function:** text input / handleSubmit(forced)
- **API Endpoint:** POST answers / POST submit
- **Backend File:** src/pwd301/blueprints/student/routes.py:829; :929; src/pwd301/services/attempt_service.py:1648
- **Backend Function:** src/pwd301/blueprints/student/routes.py :: save_student_attempt_answer; src/pwd301/blueprints/student/routes.py :: submit_student_attempt; src/pwd301/services/attempt_service.py :: save_attempt_answer
- **Database Entity/Table:** attempt_answers; assessment_results
- **Technical Cause:** Không input debounce 1–2s; submit chỉ chờ promises đã tạo, không serialize focused input. Timer forced submit không blur/flush.
- **Root Cause:** G07 — Local sequence/event không nối durable sequence
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5/timer bỏ text chưa có request; DB giữ bản trước.
- **Data Loss Risk:** YES: unsent answer input
- **Affected Features:** Student → Text/fill chỉ save change, deadline/F5 không flush input đang gõ → text input / handleSubmit(forced)
- **Recommended Fix:** Input debounce + dirty state; explicit ordered flush trước manual/deadline submit/navigation, bounded server deadline handling.
- **Regression Risk:** Per-question queues, UUID dedupe, stale/offline rejection

### SYNC-030 — Mini-quiz pass threshold chỉ kiểm browser


- **Severity:** P1
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Student
- **Module:** Mini-quiz pass threshold chỉ kiểm browser
- **Feature:** Mini-quiz pass threshold chỉ kiểm browser
- **Action:** quiz submit / lesson completion
- **Symptom:** Server validates complete shape/nonempty, không chấm đúng/sai/threshold, vẫn marks completed nếu các điều kiện khác đạt. Client scoring không phải authority.
- **Expected Behavior:** Backend enforce owner/lifecycle/reauth/scoring/evidence/retry status
- **Actual Behavior:** Server validates complete shape/nonempty, không chấm đúng/sai/threshold, vẫn marks completed nếu các điều kiện khác đạt. Client scoring không phải authority.
- **Frontend File:** frontend/assets/js/views/student.js:4036; :4042
- **Frontend Function:** quiz submit / lesson completion
- **API Endpoint:** POST /student/lessons/{l}/quiz-completion
- **Backend File:** src/pwd301/services/lesson_service.py:370; :431; :1739; :1771; :1786
- **Backend Function:** src/pwd301/services/lesson_service.py :: _lesson_quiz_answers_complete; src/pwd301/services/lesson_service.py :: complete_lesson_mini_quiz
- **Database Entity/Table:** lesson_progress.quiz_answer_snapshot; completed_at; enrollments
- **Technical Cause:** Server validates complete shape/nonempty, không chấm đúng/sai/threshold, vẫn marks completed nếu các điều kiện khác đạt. Client scoring không phải authority.
- **Root Cause:** G10 — Authority còn dựa frontend
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** Wrong-but-complete answers có thể persist completion; F5 không sửa.
- **Data Loss Risk:** NO: integrity/authorization of progress
- **Affected Features:** Student → Mini-quiz pass threshold chỉ kiểm browser → quiz submit / lesson completion
- **Recommended Fix:** Server score mọi current quiz types và passing percent; return score/pass/feedback, giữ timing/video gates.
- **Regression Risk:** RBAC/CSRF, immutable audit, FileAsset scan, concurrency

### SYNC-031 — Mini-quiz UI Passed trước acknowledgement và không restore retry


- **Severity:** P1
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Student
- **Module:** Mini-quiz UI Passed trước acknowledgement và không restore retry
- **Feature:** Mini-quiz UI Passed trước acknowledgement và không restore retry
- **Action:** mini-quiz pass presentation
- **Symptom:** Client shows congratulations/hides submit+retry trước await. Lỗi POST chỉ toast, passed UI vẫn còn.
- **Expected Behavior:** Applied/pending/error/partial được phân biệt, UI reconcile sau acknowledgement
- **Actual Behavior:** Client shows congratulations/hides submit+retry trước await. Lỗi POST chỉ toast, passed UI vẫn còn.
- **Frontend File:** frontend/assets/js/views/student.js:4042; :4120; :4133; :4135; :4148
- **Frontend Function:** mini-quiz pass presentation
- **API Endpoint:** POST quiz-completion
- **Backend File:** src/pwd301/blueprints/student/routes.py:519
- **Backend Function:** src/pwd301/blueprints/student/routes.py :: complete_student_lesson_quiz
- **Database Entity/Table:** lesson_progress
- **Technical Cause:** Client shows congratulations/hides submit+retry trước await. Lỗi POST chỉ toast, passed UI vẫn còn.
- **Root Cause:** G02 — Acknowledgement không gắn authoritative state
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 bỏ apparent pass nếu DB chưa lưu.
- **Data Loss Risk:** NO: false UI success, draft retry inaccessible
- **Affected Features:** Student → Mini-quiz UI Passed trước acknowledgement và không restore retry → mini-quiz pass presentation
- **Recommended Fix:** Commit pass UI sau authoritative successful response; giữ draft/retry trên error.
- **Regression Risk:** 202 workflow, CSRF retry, idempotency, input chưa lưu

### SYNC-032 — Notification preference array hydrate như flag map


- **Severity:** P1
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** All
- **Module:** Notification preference array hydrate như flag map
- **Feature:** Notification preference array hydrate như flag map
- **Action:** renderSettings / Save preferences
- **Symptom:** preferences là list; map đúng ở preferences_map/top-level. UI đọc array.email_course → defaulttrue; marketing defaultfalse. Next Save overwrites persisted opt-outs.
- **Expected Behavior:** Đọc-sửa-lưu giữ identity/type/values/references/cấu trúc canonical
- **Actual Behavior:** preferences là list; map đúng ở preferences_map/top-level. UI đọc array.email_course → defaulttrue; marketing defaultfalse. Next Save overwrites persisted opt-outs.
- **Frontend File:** frontend/assets/js/views/student.js:7972; :8203; :8215; :8227; :8239
- **Frontend Function:** renderSettings / Save preferences
- **API Endpoint:** GET/PUT /auth/preferences
- **Backend File:** src/pwd301/blueprints/auth/routes.py:1095; :1099; src/pwd301/services/notification_service.py:653
- **Backend Function:** src/pwd301/blueprints/auth/routes.py :: auth_preferences; src/pwd301/services/notification_service.py :: update_user_preferences
- **Database Entity/Table:** notification_preferences
- **Technical Cause:** preferences là list; map đúng ở preferences_map/top-level. UI đọc array.email_course → defaulttrue; marketing defaultfalse. Next Save overwrites persisted opt-outs.
- **Root Cause:** G01 — Representation / API contract không roundtrip
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 defaults sai, subsequent Save có thể ghi sai DB.
- **Data Loss Risk:** YES: overwrite preferences ngoài ý định
- **Affected Features:** All → Notification preference array hydrate như flag map → renderSettings / Save preferences
- **Recommended Fix:** Consume preferences_map hoặc normalize một lần; render returned canonical flags after Save.
- **Regression Risk:** Draft IDs, explicit null, immutable revisions, fail-closed resources

### SYNC-033 — Progress heartbeat background và read-modify-write race


- **Severity:** P2
- **Status:** CONFIRMED; SOURCE; concurrency occurrence NOT REPRODUCED. Source/VM confirmation is not live mutation proof.
- **Role:** Student
- **Module:** Progress heartbeat background và read-modify-write race
- **Feature:** Progress heartbeat background và read-modify-write race
- **Action:** 15-second heartbeat
- **Symptom:** Sends fixed15 không activity/visibility gate. Concurrent requests cộng từ loaded value trên row không CAS/version mapping/lock, có thể lost increment. Client view_fraction>=.90 còn được bump minimum time. iframe listener tính origin nhưng không verify event.origin/source tại student.js:3728–3781.
- **Expected Behavior:** Backend enforce owner/lifecycle/reauth/scoring/evidence/retry status
- **Actual Behavior:** Sends fixed15 không activity/visibility gate. Concurrent requests cộng từ loaded value trên row không CAS/version mapping/lock, có thể lost increment. Client view_fraction>=.90 còn được bump minimum time. iframe listener tính origin nhưng không verify event.origin/source tại student.js:3728–3781.
- **Frontend File:** frontend/assets/js/views/student.js:3817; :3826
- **Frontend Function:** 15-second heartbeat
- **API Endpoint:** POST /student/lessons/{l}/progress
- **Backend File:** src/pwd301/services/lesson_service.py:1632; :1647; :1656; src/pwd301/models/course.py:945
- **Backend Function:** src/pwd301/services/lesson_service.py :: record_lesson_progress; src/pwd301/models/course.py :: LessonProgress
- **Database Entity/Table:** lesson_progress.seconds_spent/viewed_fraction
- **Technical Cause:** Sends fixed15 không activity/visibility gate. Concurrent requests cộng từ loaded value trên row không CAS/version mapping/lock, có thể lost increment. Client view_fraction>=.90 còn được bump minimum time. iframe listener tính origin nhưng không verify event.origin/source tại student.js:3728–3781.
- **Root Cause:** G10 — Authority còn dựa frontend
- **Evidence:** SOURCE; concurrency occurrence NOT REPRODUCED; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 đọc overcount/lost increments persisted; xảy ra concurrency chưa tái hiện.
- **Data Loss Risk:** YES: lost progress update có điều kiện
- **Affected Features:** Student → Progress heartbeat background và read-modify-write race → 15-second heartbeat
- **Recommended Fix:** Measure active viewing, validate player origin/source, atomic increment/max/dedup; không substitute client fraction cho wall-clock minimum.
- **Regression Risk:** RBAC/CSRF, immutable audit, FileAsset scan, concurrency

### SYNC-034 — Progress retry không có durable event idempotency


- **Severity:** P2
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Student
- **Module:** Progress retry không có durable event idempotency
- **Feature:** Progress retry không có durable event idempotency
- **Action:** recordLessonProgress
- **Symptom:** Client không stable client_event_id, route không forward; optional service dedupe chỉ memory và insert trước commit. Retry có thể double count; failed transaction retry có thể bị memory marker suppress.
- **Expected Behavior:** Autosave monotonic/idempotent qua retry/F5; dirty input flush trước deadline
- **Actual Behavior:** Client không stable client_event_id, route không forward; optional service dedupe chỉ memory và insert trước commit. Retry có thể double count; failed transaction retry có thể bị memory marker suppress.
- **Frontend File:** frontend/assets/js/api.js:376; frontend/assets/js/views/student.js:3824
- **Frontend Function:** recordLessonProgress
- **API Endpoint:** POST lesson progress
- **Backend File:** src/pwd301/blueprints/student/routes.py:498; src/pwd301/services/lesson_service.py:1618; :1631
- **Backend Function:** src/pwd301/blueprints/student/routes.py :: record_student_progress_route; src/pwd301/services/lesson_service.py :: record_lesson_progress
- **Database Entity/Table:** lesson_progress; process-memory recent event cache
- **Technical Cause:** Client không stable client_event_id, route không forward; optional service dedupe chỉ memory và insert trước commit. Retry có thể double count; failed transaction retry có thể bị memory marker suppress.
- **Root Cause:** G07 — Local sequence/event không nối durable sequence
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 không reset DB double count, process restart bỏ dedupe.
- **Data Loss Risk:** YES: loss/suppression hoặc duplicate evidence
- **Affected Features:** Student → Progress retry không có durable event idempotency → recordLessonProgress
- **Recommended Fix:** Pass stable event IDs và persist uniqueness/accepted observation cùng transaction.
- **Regression Risk:** Per-question queues, UUID dedupe, stale/offline rejection

### SYNC-035 — AI new-chat/context reset bị response cũ đảo lại


- **Severity:** P2
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** All
- **Module:** AI new-chat/context reset bị response cũ đảo lại
- **Feature:** AI new-chat/context reset bị response cũ đảo lại
- **Action:** sendAIChat / new chat / context switch
- **Symptom:** Reset conversationId không invalidate pending response; old ID/reply repopulates new chat. Separate assistant Enter handler bypasses disabled button, permits concurrent sends.
- **Expected Behavior:** Response/callback chỉ apply đúng user/role/entity/generation đã khởi tạo
- **Actual Behavior:** Reset conversationId không invalidate pending response; old ID/reply repopulates new chat. Separate assistant Enter handler bypasses disabled button, permits concurrent sends.
- **Frontend File:** frontend/assets/js/views/student.js:2034; :2072; :7313; :7349; :7374; :7391; frontend/assets/js/ui.js:2529
- **Frontend Function:** sendAIChat / new chat / context switch
- **API Endpoint:** POST /student/ai/chat
- **Backend File:** src/pwd301/blueprints/student/routes.py:1418; :1600
- **Backend Function:** src/pwd301/blueprints/student/routes.py :: student_ai_chat
- **Database Entity/Table:** ai_conversations; ai_messages
- **Technical Cause:** Reset conversationId không invalidate pending response; old ID/reply repopulates new chat. Separate assistant Enter handler bypasses disabled button, permits concurrent sends.
- **Root Cause:** G03 — Async response/callback không fence identity
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 clears local transcript; DB retention policy khác local chat UI.
- **Data Loss Risk:** NO: context/message mismatch, không proof cross-user API access
- **Affected Features:** All → AI new-chat/context reset bị response cũ đảo lại → sendAIChat / new chat / context switch
- **Recommended Fix:** Generation/context identity + serial send guard, ignore obsolete responses; preserve five-minute raw-chat retention.
- **Regression Risk:** Navigation/history, lesson cleanup, account switch, upload/AI context

### SYNC-036 — Terminal attempt shortcut return trước owning-user check


- **Severity:** P1
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Student
- **Module:** Terminal attempt shortcut return trước owning-user check
- **Feature:** Terminal attempt shortcut return trước owning-user check
- **Action:** completed attempt delivery
- **Symptom:** Shortcut trả status/is_completed/redirect trước get_attempt_delivery ownership. Peer Student biết UUID có thể nhận terminal metadata; không có answer/score trong shortcut.
- **Expected Behavior:** Backend enforce owner/lifecycle/reauth/scoring/evidence/retry status
- **Actual Behavior:** Shortcut trả status/is_completed/redirect trước get_attempt_delivery ownership. Peer Student biết UUID có thể nhận terminal metadata; không có answer/score trong shortcut.
- **Frontend File:** frontend/assets/js/views/student.js:4955
- **Frontend Function:** completed attempt delivery
- **API Endpoint:** GET /student/attempt/{a}
- **Backend File:** src/pwd301/blueprints/student/routes.py:105; :117; src/pwd301/services/attempt_service.py:804
- **Backend Function:** src/pwd301/blueprints/student/routes.py :: attempt_view; src/pwd301/services/attempt_service.py :: get_attempt_delivery
- **Database Entity/Table:** assessment_attempts
- **Technical Cause:** Shortcut trả status/is_completed/redirect trước get_attempt_delivery ownership. Peer Student biết UUID có thể nhận terminal metadata; không có answer/score trong shortcut.
- **Root Cause:** G10 — Authority còn dựa frontend
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5/GET vẫn disclose metadata; không chạy cross-user live.
- **Data Loss Risk:** NO: privacy leak metadata
- **Affected Features:** Student → Terminal attempt shortcut return trước owning-user check → completed attempt delivery
- **Recommended Fix:** Authorize owner immediately after resolve, trước mọi terminal shortcut.
- **Regression Risk:** RBAC/CSRF, immutable audit, FileAsset scan, concurrency

### SYNC-037 — Appeal chỉ UI chặn repeat, server thiếu lifecycle/idempotency


- **Severity:** P2
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Student / Instructor
- **Module:** Appeal chỉ UI chặn repeat, server thiếu lifecycle/idempotency
- **Feature:** Appeal chỉ UI chặn repeat, server thiếu lifecycle/idempotency
- **Action:** appeal submit
- **Symptom:** Owner check có nhưng không check terminal/released state, nonempty reason và existing pending appeal. Repeated calls append multiple pending entries; GET newest masks prior.
- **Expected Behavior:** Backend enforce owner/lifecycle/reauth/scoring/evidence/retry status
- **Actual Behavior:** Owner check có nhưng không check terminal/released state, nonempty reason và existing pending appeal. Repeated calls append multiple pending entries; GET newest masks prior.
- **Frontend File:** frontend/assets/js/views/student.js:6514; :6620
- **Frontend Function:** appeal submit
- **API Endpoint:** POST /student/attempts/{a}/appeal
- **Backend File:** src/pwd301/blueprints/student/routes.py:2355; :2395
- **Backend Function:** src/pwd301/blueprints/student/routes.py :: submit_attempt_appeal_route
- **Database Entity/Table:** audit_events appeal/decision
- **Technical Cause:** Owner check có nhưng không check terminal/released state, nonempty reason và existing pending appeal. Repeated calls append multiple pending entries; GET newest masks prior.
- **Root Cause:** G10 — Authority còn dựa frontend
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 có newest record nhưng không giải quyết duplicate logical intent.
- **Data Loss Risk:** NO: duplicate/invalid workflow
- **Affected Features:** Student / Instructor → Appeal chỉ UI chặn repeat, server thiếu lifecycle/idempotency → appeal submit
- **Recommended Fix:** Validate eligible state + pending uniqueness/idempotency dưới transaction, giữ append-only audit.
- **Regression Risk:** RBAC/CSRF, immutable audit, FileAsset scan, concurrency

### SYNC-038 — Header đã lưu có thể che câu khác pending/failed


- **Severity:** P2
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Student
- **Module:** Header đã lưu có thể che câu khác pending/failed
- **Feature:** Header đã lưu có thể che câu khác pending/failed
- **Action:** autosave indicator
- **Symptom:** Mỗi question promise success set indicator riêng, không dựa aggregate pending/failed/dirty sets.
- **Expected Behavior:** Applied/pending/error/partial được phân biệt, UI reconcile sau acknowledgement
- **Actual Behavior:** Mỗi question promise success set indicator riêng, không dựa aggregate pending/failed/dirty sets.
- **Frontend File:** frontend/assets/js/views/student.js:5608; :5689; :5723
- **Frontend Function:** autosave indicator
- **API Endpoint:** POST answers
- **Backend File:** src/pwd301/services/attempt_service.py:1648
- **Backend Function:** src/pwd301/services/attempt_service.py :: save_attempt_answer
- **Database Entity/Table:** attempt_answers; pendingAnswerSaves/failedAnswerSaves local
- **Technical Cause:** Mỗi question promise success set indicator riêng, không dựa aggregate pending/failed/dirty sets.
- **Root Cause:** G02 — Acknowledgement không gắn authoritative state
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 câu failed quay old state dù header từng nói saved.
- **Data Loss Risk:** YES: người dùng có thể rời trang khi còn unsaved answer
- **Affected Features:** Student → Header đã lưu có thể che câu khác pending/failed → autosave indicator
- **Recommended Fix:** Derive indicator từ aggregate sets/dirty inputs; per-question retry and errors.
- **Regression Risk:** 202 workflow, CSRF retry, idempotency, input chưa lưu

### SYNC-039 — Avatar preset là local preview và cache ưu tiên hơn server


- **Severity:** P2
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** All
- **Module:** Avatar preset là local preview và cache ưu tiên hơn server
- **Feature:** Avatar preset là local preview và cache ưu tiên hơn server
- **Action:** random avatar / subsequent profile Save
- **Symptom:** Preset cập nhật local cache/currentUser/topbar; SQL chỉ save qua nút Save profile. Local avatar chọn trước server khi hydrate. Toast nói header sync, không tuyên bố SQL thành công.
- **Expected Behavior:** Browser draft scoped account và báo storage failure truthfully
- **Actual Behavior:** Preset cập nhật local cache/currentUser/topbar; SQL chỉ save qua nút Save profile. Local avatar chọn trước server khi hydrate. Toast nói header sync, không tuyên bố SQL thành công.
- **Frontend File:** frontend/assets/js/views/student.js:8290; :8314; :7986; frontend/assets/js/router.js:907
- **Frontend Function:** random avatar / subsequent profile Save
- **API Endpoint:** Preset không gọi API; PUT /auth/profile chỉ ở Save
- **Backend File:** src/pwd301/blueprints/auth/routes.py:959; :1013
- **Backend Function:** src/pwd301/blueprints/auth/routes.py :: auth_profile
- **Database Entity/Table:** User.avatar_url; localStorage
- **Technical Cause:** Preset cập nhật local cache/currentUser/topbar; SQL chỉ save qua nút Save profile. Local avatar chọn trước server khi hydrate. Toast nói header sync, không tuyên bố SQL thành công.
- **Root Cause:** G08 — Local durability/account scope không rõ
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 có thể vẫn giữ local override; browser khác không nhận preset chưa Save.
- **Data Loss Risk:** NO: intentional/local capability gap, không confirmed DB-loss bug
- **Affected Features:** All → Avatar preset là local preview và cache ưu tiên hơn server → random avatar / subsequent profile Save
- **Recommended Fix:** Label preview/local scope rõ; nếu intended immediate persist thì gọi existing updateProfile; reconcile returned server avatar.
- **Regression Risk:** Logout/login, quota/security errors, recovery, private drafts

### SYNC-040 — Notification mutation nuốt lỗi, optimistic state không rollback


- **Severity:** P1
- **Status:** CONFIRMED; SOURCE + VM rejected read-all retained unread_count=0. Source/VM confirmation is not live mutation proof.
- **Role:** All
- **Module:** Notification mutation nuốt lỗi, optimistic state không rollback
- **Feature:** Notification mutation nuốt lỗi, optimistic state không rollback
- **Action:** mark read / mark all / dismiss / clear
- **Symptom:** Wrappers catch return {success:false}; consumers không inspect. Read-all toast success trước API; delete removed item, swallowed failure; no rollback/refetch immediately.
- **Expected Behavior:** Applied/pending/error/partial được phân biệt, UI reconcile sau acknowledgement
- **Actual Behavior:** Wrappers catch return {success:false}; consumers không inspect. Read-all toast success trước API; delete removed item, swallowed failure; no rollback/refetch immediately.
- **Frontend File:** frontend/assets/js/api.js:1273; :1284; :1300; :1312; frontend/assets/js/router.js:1606; :1631; :1742
- **Frontend Function:** mark read / mark all / dismiss / clear
- **API Endpoint:** POST/DELETE /auth/notifications
- **Backend File:** src/pwd301/blueprints/auth/routes.py:851; src/pwd301/services/notification_service.py:407; :447; :486; :524
- **Backend Function:** src/pwd301/blueprints/auth/routes.py :: auth_mark_notification_read; src/pwd301/services/notification_service.py :: mark_notification_as_read; src/pwd301/services/notification_service.py :: mark_all_as_read; src/pwd301/services/notification_service.py :: dismiss_notification; src/pwd301/services/notification_service.py :: delete_all_notifications
- **Database Entity/Table:** notifications.read_at/dismissed_at; sessionStorage
- **Technical Cause:** Wrappers catch return {success:false}; consumers không inspect. Read-all toast success trước API; delete removed item, swallowed failure; no rollback/refetch immediately.
- **Root Cause:** G02 — Acknowledgement không gắn authoritative state
- **Evidence:** SOURCE + VM rejected read-all retained unread_count=0; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** 8s polling/F5 có thể trả unread/item cũ; không phải DB tự mất change đã commit.
- **Data Loss Risk:** NO: UI-only apparent mutation
- **Affected Features:** All → Notification mutation nuốt lỗi, optimistic state không rollback → mark read / mark all / dismiss / clear
- **Recommended Fix:** Propagate failure or inspect result; await acknowledgement hoặc snapshot rollback+revalidation.
- **Regression Risk:** 202 workflow, CSRF retry, idempotency, input chưa lưu

### SYNC-041 — Notification response cũ được gán/cache cho user mới


- **Severity:** P0
- **Status:** CONFIRMED; VM: cache user B chứa A-private-notification, role stale. Source/VM confirmation is not live mutation proof.
- **Role:** All
- **Module:** Notification response cũ được gán/cache cho user mới
- **Feature:** Notification response cũ được gán/cache cho user mới
- **Action:** fetchNotifications
- **Symptom:** Role captured trước await, nhưng response gắn user_id=this.currentUser.id sau await. Logout/login hoặc switch role trong request không identity/generation fence; A items bị attributed/cache B. Backend own-user filtering vẫn đúng.
- **Expected Behavior:** Response/callback chỉ apply đúng user/role/entity/generation đã khởi tạo
- **Actual Behavior:** Role captured trước await, nhưng response gắn user_id=this.currentUser.id sau await. Logout/login hoặc switch role trong request không identity/generation fence; A items bị attributed/cache B. Backend own-user filtering vẫn đúng.
- **Frontend File:** frontend/assets/js/router.js:1771; :1781; :1796; :1803
- **Frontend Function:** fetchNotifications
- **API Endpoint:** GET /auth/notifications?role=...
- **Backend File:** src/pwd301/services/notification_service.py:319; :347
- **Backend Function:** src/pwd301/services/notification_service.py :: _visible_notification_query; src/pwd301/services/notification_service.py :: list_user_notifications
- **Database Entity/Table:** notifications; sessionStorage scoped key
- **Technical Cause:** Role captured trước await, nhưng response gắn user_id=this.currentUser.id sau await. Logout/login hoặc switch role trong request không identity/generation fence; A items bị attributed/cache B. Backend own-user filtering vẫn đúng.
- **Root Cause:** G03 — Async response/callback không fence identity
- **Evidence:** VM: cache user B chứa A-private-notification, role stale; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5/cache revalidation sửa display nhưng private data đã có thể hiện/lưu cache sai.
- **Data Loss Risk:** YES: client-side cross-account notification leakage
- **Affected Features:** All → Notification response cũ được gán/cache cho user mới → fetchNotifications
- **Recommended Fix:** Capture user+role generation trước request; discard nếu đã thay đổi, clear on logout, single-flight cancellation.
- **Regression Risk:** Navigation/history, lesson cleanup, account switch, upload/AI context

### SYNC-042 — ExamStore key toàn trình duyệt không gắn account


- **Severity:** P0
- **Status:** CONFIRMED; VM second context reads Account A draft. Source/VM confirmation is not live mutation proof.
- **Role:** Instructor / shared browser accounts
- **Module:** ExamStore key toàn trình duyệt không gắn account
- **Feature:** ExamStore key toàn trình duyệt không gắn account
- **Action:** exam draft hydrate / logout/login
- **Symptom:** Single key chứa authored questions/config/examPassword; memory/local draft không reset khi đổi account, B context hydrate A draft.
- **Expected Behavior:** Browser draft scoped account và báo storage failure truthfully
- **Actual Behavior:** Single key chứa authored questions/config/examPassword; memory/local draft không reset khi đổi account, B context hydrate A draft.
- **Frontend File:** frontend/assets/js/exam-store.js:14; :51; :92; frontend/assets/js/api.js:220
- **Frontend Function:** exam draft hydrate / logout/login
- **API Endpoint:** Local only, không backend request
- **Backend File:** Không backend mutation; auth logout không clear ExamStore
- **Backend Function:** Local-only client action; no backend mutation invoked. Storage context and endpoint inventory are documented separately.
- **Database Entity/Table:** localStorage pwd301_azota_exam_draft
- **Technical Cause:** Single key chứa authored questions/config/examPassword; memory/local draft không reset khi đổi account, B context hydrate A draft.
- **Root Cause:** G08 — Local durability/account scope không rõ
- **Evidence:** VM second context reads Account A draft; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 account B đọc draft A nếu storage còn.
- **Data Loss Risk:** YES: local private exam draft leakage
- **Affected Features:** Instructor / shared browser accounts → ExamStore key toàn trình duyệt không gắn account → exam draft hydrate / logout/login
- **Recommended Fix:** User-scoped draft key+schema version, explicit logout/account transition reset; không persist sensitive config vô điều kiện.
- **Regression Risk:** Logout/login, quota/security errors, recovery, private drafts

### SYNC-043 — Storage failure vẫn trả lastSaved như lưu thành công


- **Severity:** P1
- **Status:** CONFIRMED; VM setItem throws → lastSaved present → reload default title. Source/VM confirmation is not live mutation proof.
- **Role:** Instructor
- **Module:** Storage failure vẫn trả lastSaved như lưu thành công
- **Feature:** Storage failure vẫn trả lastSaved như lưu thành công
- **Action:** saveDraft
- **Symptom:** Quota/security error caught warn, vẫn return draft lastSaved timestamp; no acknowledgement persisted. Memory clear/new context trả default.
- **Expected Behavior:** Browser draft scoped account và báo storage failure truthfully
- **Actual Behavior:** Quota/security error caught warn, vẫn return draft lastSaved timestamp; no acknowledgement persisted. Memory clear/new context trả default.
- **Frontend File:** frontend/assets/js/exam-store.js:85; :92; :94
- **Frontend Function:** saveDraft
- **API Endpoint:** LocalStorage only
- **Backend File:** Không backend persistence
- **Backend Function:** Local-only client action; no backend mutation invoked. Storage context and endpoint inventory are documented separately.
- **Database Entity/Table:** local exam draft
- **Technical Cause:** Quota/security error caught warn, vẫn return draft lastSaved timestamp; no acknowledgement persisted. Memory clear/new context trả default.
- **Root Cause:** G08 — Local durability/account scope không rõ
- **Evidence:** VM setItem throws → lastSaved present → reload default title; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 mất memory-only draft.
- **Data Loss Risk:** YES: local draft not persisted
- **Affected Features:** Instructor → Storage failure vẫn trả lastSaved như lưu thành công → saveDraft
- **Recommended Fix:** Expose durable-save result/error, distinguish memory from storage, retain draft and recovery/export option.
- **Regression Risk:** Logout/login, quota/security errors, recovery, private drafts

### SYNC-044 — Auto role switch fail vẫn đổi local perspective


- **Severity:** P1
- **Status:** CONFIRMED; VM rejected switch leaves local INSTRUCTOR. Source/VM confirmation is not live mutation proof.
- **Role:** All
- **Module:** Auto role switch fail vẫn đổi local perspective
- **Feature:** Auto role switch fail vẫn đổi local perspective
- **Action:** renderRoute automatic role switch
- **Symptom:** catch chỉ warn, vẫn currentRole/active_role=target và reset notification cache; server session có thể vẫn role cũ. Explicit topbar path có catch hợp lý hơn.
- **Expected Behavior:** Applied/pending/error/partial được phân biệt, UI reconcile sau acknowledgement
- **Actual Behavior:** catch chỉ warn, vẫn currentRole/active_role=target và reset notification cache; server session có thể vẫn role cũ. Explicit topbar path có catch hợp lý hơn.
- **Frontend File:** frontend/assets/js/router.js:325; :344; :358
- **Frontend Function:** renderRoute automatic role switch
- **API Endpoint:** POST /auth/switch-role
- **Backend File:** src/pwd301/blueprints/auth/routes.py role switch
- **Backend Function:** Local-only client action; no backend mutation invoked. Storage context and endpoint inventory are documented separately.
- **Database Entity/Table:** Flask session.active_role; currentUser/currentRole
- **Technical Cause:** catch chỉ warn, vẫn currentRole/active_role=target và reset notification cache; server session có thể vẫn role cũ. Explicit topbar path có catch hợp lý hơn.
- **Root Cause:** G02 — Acknowledgement không gắn authoritative state
- **Evidence:** VM rejected switch leaves local INSTRUCTOR; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 refreshCurrentUser khôi phục server role.
- **Data Loss Risk:** NO: local/session split
- **Affected Features:** All → Auto role switch fail vẫn đổi local perspective → renderRoute automatic role switch
- **Recommended Fix:** Chỉ commit local role từ successful response; on failure keep/re-read authoritative session state.
- **Regression Risk:** 202 workflow, CSRF retry, idempotency, input chưa lưu

### SYNC-045 — Logout network failure bị coi đã đăng xuất an toàn


- **Severity:** P1
- **Status:** CONFIRMED; VM rejection resolved + local user cleared. Source/VM confirmation is not live mutation proof.
- **Role:** All
- **Module:** Logout network failure bị coi đã đăng xuất an toàn
- **Feature:** Logout network failure bị coi đã đăng xuất an toàn
- **Action:** logout
- **Symptom:** ApiClient logout catches warning rồi clears local và resolves. Router already clears user, toast safe logout; server revocation chưa được xác nhận.
- **Expected Behavior:** Applied/pending/error/partial được phân biệt, UI reconcile sau acknowledgement
- **Actual Behavior:** ApiClient logout catches warning rồi clears local và resolves. Router already clears user, toast safe logout; server revocation chưa được xác nhận.
- **Frontend File:** frontend/assets/js/api.js:220; :224; frontend/assets/js/router.js:1027; :1054
- **Frontend Function:** logout
- **API Endpoint:** POST /auth/logout
- **Backend File:** src/pwd301/blueprints/auth/routes.py:360
- **Backend Function:** src/pwd301/blueprints/auth/routes.py :: switch_role
- **Database Entity/Table:** auth_sessions; Flask login session
- **Technical Cause:** ApiClient logout catches warning rồi clears local và resolves. Router already clears user, toast safe logout; server revocation chưa được xác nhận.
- **Root Cause:** G02 — Acknowledgement không gắn authoritative state
- **Evidence:** VM rejection resolved + local user cleared; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 có thể authenticated lại vì server cookie/session chưa revoke.
- **Data Loss Risk:** NO: failed security persistence
- **Affected Features:** All → Logout network failure bị coi đã đăng xuất an toàn → logout
- **Recommended Fix:** Expose logout failure, retry or explicit unconfirmed state; invalidate identity-scoped caches only coordinated with session transition.
- **Regression Risk:** 202 workflow, CSRF retry, idempotency, input chưa lưu

### SYNC-046 — API wrapper không reject business-failure HTTP200 hoặc unexpected HTML


- **Severity:** P2
- **Status:** CONFIRMED; VM HTTP200 false resolves; HTML resolves string. Source/VM confirmation is not live mutation proof.
- **Role:** All
- **Module:** API wrapper không reject business-failure HTTP200 hoặc unexpected HTML
- **Feature:** API wrapper không reject business-failure HTTP200 hoặc unexpected HTML
- **Action:** request
- **Symptom:** Chỉ !res.ok throws; HTTP200 success:false hoặc HTML resolves. Không phải mọi handler sai: Excel handler checks success. Notification wrappers còn tự tạo fulfilled success:false ở lỗi transport.
- **Expected Behavior:** Applied/pending/error/partial được phân biệt, UI reconcile sau acknowledgement
- **Actual Behavior:** Chỉ !res.ok throws; HTTP200 success:false hoặc HTML resolves. Không phải mọi handler sai: Excel handler checks success. Notification wrappers còn tự tạo fulfilled success:false ở lỗi transport.
- **Frontend File:** frontend/assets/js/api.js:149; :174
- **Frontend Function:** request
- **API Endpoint:** All requests; parse Excel có HTTP200 success:false
- **Backend File:** src/pwd301/blueprints/instructor/routes.py:4587; src/pwd301/services/excel_exam_service.py:246
- **Backend Function:** src/pwd301/blueprints/instructor/routes.py :: instructor_parse_excel_exam_route; src/pwd301/services/excel_exam_service.py :: parse_excel_exam
- **Database Entity/Table:** API response contracts
- **Technical Cause:** Chỉ !res.ok throws; HTTP200 success:false hoặc HTML resolves. Không phải mọi handler sai: Excel handler checks success. Notification wrappers còn tự tạo fulfilled success:false ở lỗi transport.
- **Root Cause:** G02 — Acknowledgement không gắn authoritative state
- **Evidence:** VM HTTP200 false resolves; HTML resolves string; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** Reload không giải quyết false fulfilment; affected unchecked consumers cần trace.
- **Data Loss Risk:** NO: contract guard gap; không chứng minh toàn bộ API success giả
- **Affected Features:** All → API wrapper không reject business-failure HTTP200 hoặc unexpected HTML → request
- **Recommended Fix:** Validate expected envelope/content type theo endpoint contract; không unwrap blindly legacy flat payload, preserve compatible normalized boundary.
- **Regression Risk:** 202 workflow, CSRF retry, idempotency, input chưa lưu

### SYNC-047 — Session sensitive routes thiếu reauthentication như JWT mirror


- **Severity:** P1
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Admin
- **Module:** Session sensitive routes thiếu reauthentication như JWT mirror
- **Feature:** Session sensitive routes thiếu reauthentication như JWT mirror
- **Action:** suspend / revoke sessions / quarantine override / maintenance / trash
- **Symptom:** /admin routes không gọi verify_sensitive_action_reauth, services không password. JWT routes enforce helper. UI password fields không enforce server session path.
- **Expected Behavior:** Backend enforce owner/lifecycle/reauth/scoring/evidence/retry status
- **Actual Behavior:** /admin routes không gọi verify_sensitive_action_reauth, services không password. JWT routes enforce helper. UI password fields không enforce server session path.
- **Frontend File:** frontend/assets/js/views/admin.js:1097; :1134; :4138; :4852
- **Frontend Function:** suspend / revoke sessions / quarantine override / maintenance / trash
- **API Endpoint:** POST /admin/users/{u}/suspend|revoke-sessions; files override; maintenance/start; course trash
- **Backend File:** src/pwd301/blueprints/admin/routes.py:550; :585; :727; :788; :922; src/pwd301/blueprints/api_admin/routes.py:519; :553; :711; :775; :914; src/pwd301/services/authorization_service.py:203
- **Backend Function:** src/pwd301/blueprints/admin/routes.py :: trash_course_route; src/pwd301/blueprints/admin/routes.py :: override_file_quarantine; src/pwd301/blueprints/admin/routes.py :: admin_suspend_user; src/pwd301/blueprints/admin/routes.py :: admin_force_revoke_sessions; src/pwd301/blueprints/admin/routes.py :: admin_start_maintenance; src/pwd301/blueprints/api_admin/routes.py :: api_trash_course; src/pwd301/blueprints/api_admin/routes.py :: api_override_file_quarantine; src/pwd301/blueprints/api_admin/routes.py :: api_admin_suspend_user; src/pwd301/blueprints/api_admin/routes.py :: api_admin_force_revoke_sessions; src/pwd301/blueprints/api_admin/routes.py :: api_admin_start_maintenance; src/pwd301/services/authorization_service.py :: admin_required
- **Database Entity/Table:** users; auth_sessions; file_assets; system_alerts
- **Technical Cause:** /admin routes không gọi verify_sensitive_action_reauth, services không password. JWT routes enforce helper. UI password fields không enforce server session path.
- **Root Cause:** G10 — Authority còn dựa frontend
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 giữ mutation dù reauth input sai/không validate.
- **Data Loss Risk:** NO: security guard missing
- **Affected Features:** Admin → Session sensitive routes thiếu reauthentication như JWT mirror → suspend / revoke sessions / quarantine override / maintenance / trash
- **Recommended Fix:** Reuse shared verify helper/service authoritative boundary cho cả session/JWT; giữ CSRF/RBAC/object permissions.
- **Regression Risk:** RBAC/CSRF, immutable audit, FileAsset scan, concurrency

### SYNC-048 — Restore reason nhập trong modal bị loại khỏi request/audit


- **Severity:** P1
- **Status:** CONFIRMED; SOURCE + isolated Admin VM reasonForwarded=false. Source/VM confirmation is not live mutation proof.
- **Role:** Admin
- **Module:** Restore reason nhập trong modal bị loại khỏi request/audit
- **Feature:** Restore reason nhập trong modal bị loại khỏi request/audit
- **Action:** restore confirmation
- **Symptom:** Modal validates reason nhưng API gửi only phrase/password; server không reason parameter, audit fixed Administrative disaster recovery procedure confirmed. Signed checkbox UI-only không phải chữ ký.
- **Expected Behavior:** Đọc-sửa-lưu giữ identity/type/values/references/cấu trúc canonical
- **Actual Behavior:** Modal validates reason nhưng API gửi only phrase/password; server không reason parameter, audit fixed Administrative disaster recovery procedure confirmed. Signed checkbox UI-only không phải chữ ký.
- **Frontend File:** frontend/assets/js/views/admin.js:5128; :5150; frontend/assets/js/api.js:1145
- **Frontend Function:** restore confirmation
- **API Endpoint:** POST /admin/backups/{id}/restore
- **Backend File:** src/pwd301/blueprints/admin/routes.py:903; src/pwd301/services/operations_service.py:1677; :1744
- **Backend Function:** src/pwd301/blueprints/admin/routes.py :: admin_restore_database; src/pwd301/services/operations_service.py :: restore_database_snapshot
- **Database Entity/Table:** audit_events; backup_runs
- **Technical Cause:** Modal validates reason nhưng API gửi only phrase/password; server không reason parameter, audit fixed Administrative disaster recovery procedure confirmed. Signed checkbox UI-only không phải chữ ký.
- **Root Cause:** G01 — Representation / API contract không roundtrip
- **Evidence:** SOURCE + isolated Admin VM reasonForwarded=false; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5/audit không có reason người vận hành nhập.
- **Data Loss Risk:** YES: mất audit intent/context
- **Affected Features:** Admin → Restore reason nhập trong modal bị loại khỏi request/audit → restore confirmation
- **Recommended Fix:** Forward/server-validate reason và store true operator reason, label acknowledgement accurately; restore phải explicit Admin confirmation.
- **Regression Risk:** Draft IDs, explicit null, immutable revisions, fail-closed resources

### SYNC-049 — Multi-role removal partially commit và UI không refetch sau error


- **Severity:** P2
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Admin
- **Module:** Multi-role removal partially commit và UI không refetch sau error
- **Feature:** Multi-role removal partially commit và UI không refetch sau error
- **Action:** revoke multiple roles
- **Symptom:** Sequential requests commit từng role; later error only toast, skips reload dù earlier role đã đổi.
- **Expected Behavior:** Composite action commit all-or-nothing domain+decision+required audit/outbox
- **Actual Behavior:** Sequential requests commit từng role; later error only toast, skips reload dù earlier role đã đổi.
- **Frontend File:** frontend/assets/js/views/admin.js:1036; :1042
- **Frontend Function:** revoke multiple roles
- **API Endpoint:** POST /admin/users/{u}/roles per role
- **Backend File:** src/pwd301/services/user_service.py:1199
- **Backend Function:** src/pwd301/services/user_service.py :: remove_role_from_user
- **Database Entity/Table:** user_roles; users.auth_version
- **Technical Cause:** Sequential requests commit từng role; later error only toast, skips reload dù earlier role đã đổi.
- **Root Cause:** G04 — Transaction ownership bị chia nhỏ
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 thấy phần đã commit khác UI stale.
- **Data Loss Risk:** NO: partial persistence visible later
- **Affected Features:** Admin → Multi-role removal partially commit và UI không refetch sau error → revoke multiple roles
- **Recommended Fix:** Server transaction cho intended role set hoặc expose per-role outcome và always refetch after partial result.
- **Regression Risk:** Caller-owned session, SQL locks, outbox delivery failure không rollback primary action

### SYNC-050 — Rejected dependent GET bị biến thành empty dataset


- **Severity:** P2
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Admin / Student
- **Module:** Rejected dependent GET bị biến thành empty dataset
- **Feature:** Rejected dependent GET bị biến thành empty dataset
- **Action:** course/change queues / reassign / catalog enroll badges
- **Symptom:** allSettled rejected branch substitute []/zero. Lỗi đọc thành không có pending/not-enrolled, che dependency failure.
- **Expected Behavior:** Rejected/unknown reads khác authoritative empty/zero
- **Actual Behavior:** allSettled rejected branch substitute []/zero. Lỗi đọc thành không có pending/not-enrolled, che dependency failure.
- **Frontend File:** frontend/assets/js/views/admin.js:1263; :1268; :3589; frontend/assets/js/views/student.js:921
- **Frontend Function:** course/change queues / reassign / catalog enroll badges
- **API Endpoint:** GET admin queues/users; GET student/my-learning
- **Backend File:** src/pwd301/blueprints/admin/routes.py:1338; src/pwd301/blueprints/student/routes.py:965
- **Backend Function:** src/pwd301/blueprints/admin/routes.py :: admin_list_change_requests; src/pwd301/blueprints/student/routes.py :: my_learning
- **Database Entity/Table:** courses; course_change_requests; enrollments
- **Technical Cause:** allSettled rejected branch substitute []/zero. Lỗi đọc thành không có pending/not-enrolled, che dependency failure.
- **Root Cause:** G14 — Read failure bị coi empty dataset
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 có thể thấy lại rows/badges khi read thành công.
- **Data Loss Risk:** NO: read-state mismatch
- **Affected Features:** Admin / Student → Rejected dependent GET bị biến thành empty dataset → course/change queues / reassign / catalog enroll badges
- **Recommended Fix:** Render degraded/unknown cho source bị reject, retry; không manufacture empty state/count.
- **Regression Risk:** Partial dashboard/degraded retry, object permissions

### SYNC-051 — User search old response overwrite filter mới


- **Severity:** P2
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Admin
- **Module:** User search old response overwrite filter mới
- **Feature:** User search old response overwrite filter mới
- **Action:** search/filter users
- **Symptom:** Debounce không fence in-flight response; fallback original snapshot không mark stale.
- **Expected Behavior:** Response/callback chỉ apply đúng user/role/entity/generation đã khởi tạo
- **Actual Behavior:** Debounce không fence in-flight response; fallback original snapshot không mark stale.
- **Frontend File:** frontend/assets/js/views/admin.js:698; :703; :710
- **Frontend Function:** search/filter users
- **API Endpoint:** GET /admin/users
- **Backend File:** src/pwd301/blueprints/admin/routes.py users list
- **Backend Function:** Local-only client action; no backend mutation invoked. Storage context and endpoint inventory are documented separately.
- **Database Entity/Table:** users
- **Technical Cause:** Debounce không fence in-flight response; fallback original snapshot không mark stale.
- **Root Cause:** G03 — Async response/callback không fence identity
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5/new search có thể đúng; response order vẫn risk.
- **Data Loss Risk:** NO: stale list
- **Affected Features:** Admin → User search old response overwrite filter mới → search/filter users
- **Recommended Fix:** Latest request/filter identity hoặc AbortController; explicit stale/error state.
- **Regression Risk:** Navigation/history, lesson cleanup, account switch, upload/AI context

### SYNC-052 — Sync toast chạy trước route refresh hoàn tất


- **Severity:** P2
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Admin
- **Module:** Sync toast chạy trước route refresh hoàn tất
- **Feature:** Sync toast chạy trước route refresh hoàn tất
- **Action:** sync users
- **Symptom:** UI.refreshCurrentRoute trả Promise nhưng caller không await; success toast trước fresh data/route error.
- **Expected Behavior:** Applied/pending/error/partial được phân biệt, UI reconcile sau acknowledgement
- **Actual Behavior:** UI.refreshCurrentRoute trả Promise nhưng caller không await; success toast trước fresh data/route error.
- **Frontend File:** frontend/assets/js/views/admin.js:736; :738; frontend/assets/js/ui.js:15
- **Frontend Function:** sync users
- **API Endpoint:** GET current route
- **Backend File:** frontend/assets/js/router.js:178
- **Backend Function:** Local-only client action; no backend mutation invoked. Storage context and endpoint inventory are documented separately.
- **Database Entity/Table:** users / view state
- **Technical Cause:** UI.refreshCurrentRoute trả Promise nhưng caller không await; success toast trước fresh data/route error.
- **Root Cause:** G02 — Acknowledgement không gắn authoritative state
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5/new route fetch mới có data; toast không proof.
- **Data Loss Risk:** NO: misleading acknowledgement
- **Affected Features:** Admin → Sync toast chạy trước route refresh hoàn tất → sync users
- **Recommended Fix:** Await fresh accepted render result; report failed refresh truthfully.
- **Regression Risk:** 202 workflow, CSRF retry, idempotency, input chưa lưu

### SYNC-053 — Backup verify commit metadata nhưng list row không cập nhật


- **Severity:** P2
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Admin
- **Module:** Backup verify commit metadata nhưng list row không cập nhật
- **Feature:** Backup verify commit metadata nhưng list row không cập nhật
- **Action:** verify backup
- **Symptom:** Handler chỉ toast, không replace/refetch record sau backend commit.
- **Expected Behavior:** Sau mutation replace/refetch authoritative state; multi-worker cache semantics rõ
- **Actual Behavior:** Handler chỉ toast, không replace/refetch record sau backend commit.
- **Frontend File:** frontend/assets/js/views/admin.js:4715; :4723
- **Frontend Function:** verify backup
- **API Endpoint:** POST /admin/backups/{id}/verify
- **Backend File:** src/pwd301/services/operations_service.py:1410; :1436
- **Backend Function:** src/pwd301/services/operations_service.py :: verify_backup_integrity
- **Database Entity/Table:** backup_runs.verified_at
- **Technical Cause:** Handler chỉ toast, không replace/refetch record sau backend commit.
- **Root Cause:** G11 — Cache/refetch không invalidate đúng
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5/manual refresh mới hiện verified_at mới.
- **Data Loss Risk:** NO: stale UI after real commit path
- **Affected Features:** Admin → Backup verify commit metadata nhưng list row không cập nhật → verify backup
- **Recommended Fix:** Apply returned authoritative backup row hoặc reload list.
- **Regression Risk:** Không phá active route bằng polling; unknown không giả inactive

### SYNC-054 — PRE_MAINTENANCE silently thành MANUAL


- **Severity:** P2
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Admin
- **Module:** PRE_MAINTENANCE silently thành MANUAL
- **Feature:** PRE_MAINTENANCE silently thành MANUAL
- **Action:** create backup type selection
- **Symptom:** UI offers PRE_MAINTENANCE; backend allowed set không có nên coerces MANUAL.
- **Expected Behavior:** Đọc-sửa-lưu giữ identity/type/values/references/cấu trúc canonical
- **Actual Behavior:** UI offers PRE_MAINTENANCE; backend allowed set không có nên coerces MANUAL.
- **Frontend File:** frontend/assets/js/views/admin.js:5032
- **Frontend Function:** create backup type selection
- **API Endpoint:** POST /admin/backups
- **Backend File:** src/pwd301/services/operations_service.py:1168
- **Backend Function:** src/pwd301/services/operations_service.py :: create_database_backup
- **Database Entity/Table:** backup_runs.backup_type
- **Technical Cause:** UI offers PRE_MAINTENANCE; backend allowed set không có nên coerces MANUAL.
- **Root Cause:** G01 — Representation / API contract không roundtrip
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 ghi nhận MANUAL khác lựa chọn.
- **Data Loss Risk:** YES: mất selected enum intent
- **Affected Features:** Admin → PRE_MAINTENANCE silently thành MANUAL → create backup type selection
- **Recommended Fix:** Align type contract, reject unsupported enum hoặc support canonical type explicitly.
- **Regression Risk:** Draft IDs, explicit null, immutable revisions, fail-closed resources

### SYNC-055 — Change detail deep-link chỉ tìm trong pending consolidated list


- **Severity:** P2
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** Admin
- **Module:** Change detail deep-link chỉ tìm trong pending consolidated list
- **Feature:** Change detail deep-link chỉ tìm trong pending consolidated list
- **Action:** open/revisit change request
- **Symptom:** ALL vẫn pending-only, một selected record/course; direct resolved hoặc secondary pending ID không có trong response. Queue remove approved là đúng, detail lookup qua queue mới sai.
- **Expected Behavior:** Deep-link tải đúng object; chapter/final relation canonical
- **Actual Behavior:** ALL vẫn pending-only, một selected record/course; direct resolved hoặc secondary pending ID không có trong response. Queue remove approved là đúng, detail lookup qua queue mới sai.
- **Frontend File:** frontend/assets/js/views/admin.js:1614; :1617; :1618
- **Frontend Function:** open/revisit change request
- **API Endpoint:** GET /admin/change-requests?status=ALL
- **Backend File:** src/pwd301/blueprints/admin/routes.py:1338; :1348; :1373
- **Backend Function:** src/pwd301/blueprints/admin/routes.py :: admin_list_change_requests
- **Database Entity/Table:** course_change_requests
- **Technical Cause:** ALL vẫn pending-only, một selected record/course; direct resolved hoặc secondary pending ID không có trong response. Queue remove approved là đúng, detail lookup qua queue mới sai.
- **Root Cause:** G12 — Routing/scope không gắn persisted identity
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 link đã resolved báo not-found dù DB record còn.
- **Data Loss Risk:** NO: inaccessible history/deep-link
- **Affected Features:** Admin → Change detail deep-link chỉ tìm trong pending consolidated list → open/revisit change request
- **Recommended Fix:** Authorized GET-by-ID/detail children thay tìm từ filtered list; giữ pending-only queue semantics.
- **Regression Risk:** Hash replaceState, object auth, timing locks, schema changes

### SYNC-056 — Retry job có thể overwrite RUNNING lease/state


- **Severity:** P1
- **Status:** HIGHLY LIKELY; SOURCE guard absence; concurrency NOT REPRODUCED. Source/VM confirmation is not live mutation proof.
- **Role:** Admin
- **Module:** Retry job có thể overwrite RUNNING lease/state
- **Feature:** Retry job có thể overwrite RUNNING lease/state
- **Action:** retry failed job
- **Symptom:** Server load rồi unconditional QUEUED/clear lease, không status predicate/CAS/lock; UI-only disable nonFAILED không chống job đổi trạng thái giữa GET/POST.
- **Expected Behavior:** Backend enforce owner/lifecycle/reauth/scoring/evidence/retry status
- **Actual Behavior:** Server load rồi unconditional QUEUED/clear lease, không status predicate/CAS/lock; UI-only disable nonFAILED không chống job đổi trạng thái giữa GET/POST.
- **Frontend File:** frontend/assets/js/views/admin.js:5270; :5308
- **Frontend Function:** retry failed job
- **API Endpoint:** POST /admin/operations/jobs/{id}/retry
- **Backend File:** src/pwd301/services/operations_service.py:2207; :2225; :2245
- **Backend Function:** src/pwd301/services/operations_service.py :: retry_background_job
- **Database Entity/Table:** background_jobs claim/lease/status
- **Technical Cause:** Server load rồi unconditional QUEUED/clear lease, không status predicate/CAS/lock; UI-only disable nonFAILED không chống job đổi trạng thái giữa GET/POST.
- **Root Cause:** G10 — Authority còn dựa frontend
- **Evidence:** SOURCE guard absence; concurrency NOT REPRODUCED; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 thấy requeued job; race workload chưa execute.
- **Data Loss Risk:** YES: duplicate/lost worker progress risk
- **Affected Features:** Admin → Retry job có thể overwrite RUNNING lease/state → retry failed job
- **Recommended Fix:** Atomic require retryable state/expired lease and reject RUNNING/SUCCEEDED; worker side idempotency vẫn giữ.
- **Regression Risk:** RBAC/CSRF, immutable audit, FileAsset scan, concurrency

### SYNC-057 — Maintenance invalidation chỉ trong process với TTL15s


- **Severity:** P2
- **Status:** CONFIRMED; SOURCE. Source/VM confirmation is not live mutation proof.
- **Role:** All
- **Module:** Maintenance invalidation chỉ trong process với TTL15s
- **Feature:** Maintenance invalidation chỉ trong process với TTL15s
- **Action:** maintenance access after start/end
- **Symptom:** In-memory cache shared threads only; invalidation không broadcast qua Gunicorn workers. Query exception bị catch và cached inactive. Docker defaults nhiều web workers.
- **Expected Behavior:** Sau mutation replace/refetch authoritative state; multi-worker cache semantics rõ
- **Actual Behavior:** In-memory cache shared threads only; invalidation không broadcast qua Gunicorn workers. Query exception bị catch và cached inactive. Docker defaults nhiều web workers.
- **Frontend File:** frontend/assets/js/router.js:1273
- **Frontend Function:** maintenance access after start/end
- **API Endpoint:** POST /admin/maintenance/start|end; all incoming access checks
- **Backend File:** src/pwd301/services/operations_service.py:1959; :2037; :2041; :2100; src/pwd301/__init__.py:707
- **Backend Function:** src/pwd301/services/operations_service.py :: start_maintenance_window; src/pwd301/services/operations_service.py :: end_maintenance_window; src/pwd301/services/operations_service.py :: is_maintenance_active_cached; src/pwd301/__init__.py :: before_request
- **Database Entity/Table:** system_alerts; process-local maintenance cache
- **Technical Cause:** In-memory cache shared threads only; invalidation không broadcast qua Gunicorn workers. Query exception bị catch và cached inactive. Docker defaults nhiều web workers.
- **Root Cause:** G11 — Cache/refetch không invalidate đúng
- **Evidence:** SOURCE; exact current source anchors above. No toast/historical pass treated as durable SQL proof.
- **Why F5 affects this issue:** F5 sang worker khác có thể still cached status trong TTL.
- **Data Loss Risk:** NO: delayed maintenance authorization / unknown treated inactive
- **Affected Features:** All → Maintenance invalidation chỉ trong process với TTL15s → maintenance access after start/end
- **Recommended Fix:** Giữ bounded cache nhưng validate shared authoritative state/version đối với sensitive gates; fail closed khi state unknown; không mặc định thêm Redis.
- **Regression Risk:** Không phá active route bằng polling; unknown không giả inactive

