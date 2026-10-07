# 05_NOTIFICATION_FIX_PLAN

## New lesson-flag corrections proposed after Browser/SQL evidence

| Fix ID | Issue | Root Cause | Proposed Fix | FE | BE | DB | Risk | Dependencies | Test Required | Priority |
|---|---|---|---|---|---|---|---|---|---|---|
| F-024 | Valid moderation returns 500; no flag/audit/owner notice | RCA-040 duplicated invalid AuditEvent constructor, omitted roles snapshot | Reuse record_audit_event; align both surfaces; prove flag/audit/notice transaction before truthful success | Keep page owner; contextual Vietnamese code mapping | Web + REST flag handlers; existing audit/notification services | Existing schema only; no migration proposed | Audit fail-closed, transaction rollback, double-submit | Canonical audit contract; existing owner authorization | RED valid case; audit metadata; forced audit failure rollback; SQL durability; owner Browser notice/CTA; repeat action | P1 |
| F-025 | String/list body becomes system 500 | RCA-027 on flag endpoints | Reuse object-type guard and safe 400 error, before field access | No new library or global architecture | Validate both web and JWT payloads | No schema change | Form compatibility and CSRF must stay intact | Existing malformed-mutation validation pattern | String/nonempty list/null/empty object; empty/4/5-char reason; Guest/Student/Instructor/Sub-Admin permission | P1 |
| F-026 | Exact five-character valid reason still returns 500 | RCA-040 at AuditEvent construction | Add an explicit exact-boundary regression and repair the canonical audit call before dispatch | Keep prompt and page catch ownership | Reuse `record_audit_event` and current owner-notice dispatcher | Existing schema only | Preserve fail-closed audit and rollback | Canonical AuditEvent fields and actor role snapshot | `abcde`, whitespace trim, durable flag/audit/event/notice, retry | P1 |
| F-027 | Sub-admin scope and role notice coverage | RCA-041 continuation | Keep one role-specific ROLE_CHANGED notice and scoped CTA; add four role fixtures and three denied-flag regressions | Preserve role-specific CTA copy | Existing role assignment, notification list and permission services | No schema change | Avoid role escalation or duplicate notices | Existing admin permission matrix | Four Browser logins, four SQL notices, four REST list reads, 1 allowed/3 denied flag calls | P2 |

The table above is the **pre-fix proposal snapshot**. It was not converted to a pass by accepting the observed 500; the implementation and green replay are recorded below. Historical pre-fix probe results remain preserved for audit traceability.

## Post-fix implementation and replay (2026-10-05)

| Fix ID | Implemented change | Verification | Remaining boundary |
|---|---|---|---|
| F-024 | Added `flag_lesson_content` service using `record_audit_event`, canonical owner action URL and one commit for lesson/audit/notice; both web and REST routes reuse it | TDD regression 6 passed; Browser exact-5 success; SQL flag/audit/event/notice; REST flag probe 10/10, 0 skipped | Repeat/idempotency and outbound email remain open |
| F-025 | Added object-type validation before `.get()` on both web and REST flag routes | String/list REST cases 400 with unchanged SQL; web malformed-body regression passed; full flag probe 10/10 | Null/empty object keeps normal reason validation; broader malformed media types remain open |
| F-026 | Added exact-five-character and notification-failure rollback regressions | `abcde` REST/Browser success; forced notification failure leaves no durable state; 6 focused tests passed | SQL Server forced-failure replay not separately repeated after unit/in-process proof |
| F-027 | Corrected sub-admin probe state accounting and retained role-specific notice/CTA evidence | Fresh SQL REST sub-admin probe 8/8, 0 skipped; earlier Browser detail/CTA PASS | Rapid repeat and email delivery remain open |

## Checkpoint kiểm thử không skip và an toàn môi trường (2026-10-05)

Checkpoint này có ưu tiên hơn các số liệu 1572/1578 và các trạng thái lịch sử bên dưới. Lượt chạy ban đầu có 1576 passed, 2 failed, 0 skipped; hai test upload tài nguyên và lease bài thi trả 503. Chạy riêng cho 2 passed; chạy lại toàn nhóm API trước sửa fixture cho 375 passed. Probe có restore marker trên thư mục audit riêng tái hiện đúng cả hai phản hồi MAINTENANCE_MODE_ACTIVE/503. Việc nhóm test dùng chung storage/quarantine/backups với workspace là lỗi cô lập đã được chứng minh; không quy kết chắc chắn nguyên nhân của lượt lỗi ban đầu khi chưa lưu response của lượt đó.

Fixture app nay dùng ba thư mục con riêng trong tmp_path. Regression mới thất bại với các root E:/PWD301/storage, quarantine, backups trước sửa. Sau sửa, probe vẫn giữ marker bên ngoài và 27 test upload/lease/backup/restore/maintenance đạt; không tắt maintenance hay fail-closed. Marker probe đã xóa. Test mới dùng nhầm một route không tồn tại lúc đầu; lỗi harness 404 đó đã sửa, không tính là lỗi sản phẩm.

Cô lập filesystem lộ thêm lỗi rescan: kiểm tra substring “infected” trên toàn đường dẫn nhầm thư mục cha với vùng chứa tệp nhiễm. Regression hiện hữu thất bại hai lần trước sửa; nay so sánh parent đã resolve với get_file_infected_root(), kiểm tra tệp được chuyển, key infected/hash và Student vẫn bị từ chối 403. Focused stress/file/isolation: 27 passed. Lượt split cuối sau sửa cho **1579 passed, 0 failed, 0 skipped**, khớp **1579 tests collected**: root298 + unit632 + API375 + security233 + concurrency13 + E2E12 + integration16. Frontend độc lập: **101 passed, 0 failed, 0 skipped**. Không cộng các lượt focused trùng vào tổng. Đây là kết quả các nhóm chạy đủ, không phải một aggregate verifier được tuyên bố pass; lượt aggregate lịch sử bị stall vẫn không được tính.

SQL-gated integration hiện tại: 16 passed, 0 failed, 0 skipped, gồm migration, ROWVERSION race và hai loại revision trên SQL Server thật. Hai DB migration/race tạm đã xóa, remaining=0. Browser Student4 đã đăng xuất về form login; server audit 5105 dừng; DB grading tạm cũng đã xóa, remaining=0. Không migrate/restart DB/runtime chính; fixture có thể dựng lại bằng prepare.

Audit notification vẫn PARTIAL, không phải release sign-off. Những đoạn dưới nói “chưa sửa”, “pending replay”, “1572 current” là snapshot lịch sử, không được dùng thay checkpoint mới.

## Verification-support changes (2026-10-05)

| Fix | File / minimal change | Review classification | Evidence / limits |
|---|---|---|---|
| F-022 | tests/conftest.py: isolate storage/quarantine/backups under tmp_path; new tests/test_test_environment.py; add JSON failure details to the two API assertions | SIMPLIFY NOW: reuse pytest fixture; no runtime bypass | RED workspace-root failure; external-restore-marker probe GREEN 27 tests; retain original 503 failures in history |
| F-023 | src/pwd301/services/file_service.py: compare resolved parent to configured infected root; tests/test_m1_challenger_stress.py: verify move/key as well as fail-closed download | SIMPLIFY NOW: remove substring heuristic, reuse existing path resolver | Genuine RED infected-file relocation failure; GREEN focused 27; no existing user edits in this service were overwritten |

No product content, file limit, scanner verdict policy or notification API contract was changed by these two supporting fixes. Test-only setup remains in tests. Other legacy path heuristics were not swept into this change; they require their own evidence if pursued.

## Latest implemented grading corrections (2026-10-05)

| Fix | Scope / reuse | Verification / remaining risk |
|---|---|---|
| F-018 | attempt_service.py: extract the existing result-copy/dispatch into one shared notifier keyed to first release or changed score; regrade_worker.py calls it from job and direct regrade paths | Durable manual and worker notification regressions; real SQL/HTTP/Browser 18→28 result CTA; existing swallowed dispatch failures remain |
| F-019 | New migration c4d5e6f7a8b0 widens only ck_question_revisions_4 to match model/reference DDL; data dictionary reconciled; old migrations untouched | SQLite and real SQL migration round trips; downgrade refuses expanded historical values rather than rewriting history; main runtime not migrated |
| F-020 | question_bank_service.py creates the new revision inactive, flushes all children, then activates it inside the existing transaction | Two failing trigger regressions become green; actual SQL Server choice/accepted-answer insertion and historical mutation rejection verified |
| F-021 | Investigate result ESSAY misrender and Instructor manual-grade UI against current product specification | SUPERSEDED BY F-033: current worktree restores the existing persisted ESSAY grading/result path without adding a new authoring type |

New product scope beyond the prior seven files: two service files and one migration, plus focused tests, canonical dictionary and the reproducible audit script. Changes remain uncommitted; no application schema/data was changed outside exact disposable audit databases. Historical repair, broadcast idempotency, envelope, upload/download and email gates remain independently open.

## Current continuation correction — enrollment transaction and SQL-gated aggregate (2026-10-05)

The enrollment producer now dispatches owner and student notifications before its final commit. A red persistence regression failed before this ordering fix because closing the session left `0` linked `Notification` rows; `tests/unit/test_enrollment_service.py` now reports `20 passed, 0 failed`. Completed split pytest verification reports `1572 passed, 0 failed, 0 skipped` across all collected groups, including two SQL Server disposable gates; both disposable database pairs were removed. A later aggregate attempt stalled at 49% and is not counted as a pass. A fresh live Student4 → DSA201 enrollment replay now correlated ACTIVE enrollment, both recipient events/notifications and the owner Browser notice. Historical OPS401 orphan rows still need a repair/replay decision.

The live course-review gate is now evidenced on both branches: Instructor1 submitted CS201, Admin approved it, Instructor1 received the approval notification, and SQL Server confirmed the APPROVED course plus one linked owner notification. A second live staged update was rejected through the review page with a supplied reason; SQL Server confirmed request `60002` as REJECTED and the owner received the linked rejection notification. Fresh enrollment recipient replay also passes; upload/download and email delivery remain open.

## Current-worktree implementation status (2026-10-04)

The worktree contains earlier user remediation touching notification dismiss semantics, demo-role selection, logout cleanup and Admin seed metadata, plus scoped audit continuation changes across seven unique product files: `src/pwd301/blueprints/instructor/routes.py`, `src/pwd301/blueprints/api_admin/routes.py`, `src/pwd301/blueprints/api_notifications/routes.py`, `src/pwd301/services/attempt_service.py`, `src/pwd301/services/enrollment_service.py`, `frontend/assets/js/api.js` and `frontend/assets/js/router.js`. The latest router correction renders unauthenticated auth routes directly instead of entering the role-home fallback. The speculative `frontend/index.html` bootstrap change and its mock-only test were removed. All retained changes remain dirty/uncommitted. The latest completed split verification is `1572 passed, 0 failed, 0 skipped` across all pytest groups; the SQL Server migration and concurrency gates passed in their disposable integration group. Notification Browser mutation paths and complete API/DB correlation remain open.

The continuation closes the F-004/F-005 transport-failure gap: total notification-route failure raises `NOTIFICATIONS_UNAVAILABLE`, the router exposes a degraded/retry state, and the three representative-role Browser outage/retry replay passed. The current frontend suite is `101 passed, 0 failed, 0 skipped`, including three red/green auth-route regressions. BFCache was not established as the root cause; the prior bootstrap claim is withdrawn.

The preceding sentence is the pre-Browser-continuation status. The current sampled Admin Browser replay is documented below and passed: endpoint blocking showed the explicit unavailable/retry state without a fabricated empty state, and removing the block plus retry restored the real notification list.

## Nguyên tắc

Đây là kế hoạch remediation, chưa triển khai trong audit này. Product code hiện có các thay đổi của người dùng; mọi implementation sau đó phải bắt đầu bằng test fail cho từng contract và phải kiểm tra lại diff theo scope.

## Phases

### Phase 0 — contract lock

1. Chốt `dismissed` và expiry semantics với product/system owner.
2. Chốt envelope `{success,data,error}` cho API notification và web-auth routes.
3. Chốt event catalog baseline, event ownership và recipient matrix.
4. Chốt backward compatibility cho `deleted_at` output và client parser.

### Phase 1 — smallest correctness fixes

| Item | Change | Classification | Acceptance |
|---|---|---|---|
| F-001 | Restore dismiss public status to `dismissed`; add API/unit regression | SIMPLIFY NOW | focused two tests pass; DELETE/PATCH idempotency verified |
| F-002 | Normalize notification action routes through one serializer | SIMPLIFY NOW | all list/read/read-all/dismiss/preferences shapes documented and tested |
| F-003 | Preserve stable error code and user-safe fallback in `ApiClient` | KEEP | no raw exception reaches user toast in static and browser checks |
| F-004 | Fix/strengthen `ApiClient.getNotifications` test/runtime contract | REMOVE NOW | cold load/refresh/role switch test has no background TypeError |
| F-005 | Surface notification refresh degraded state and retry | KEEP | simulated 401/5xx/network failure visible without false success |

### Phase 2 — catalog and idempotency

| Item | Change | Classification | Acceptance |
|---|---|---|---|
| F-006 | Add event registry and message keys, reusing current notification service | KEEP | all 37 producers map to an approved event code |
| F-007 | Require business idempotency key for retryable producers | KEEP | rapid double click and HTTP retry create one business notification |
| F-008 | Remove title/body heuristic duplicate hiding or narrow it to explicit coalescing policy | SIMPLIFY NOW | legitimate same-copy events remain visible; retry is deduplicated |
| F-009 | Separate `ROLE_CHANGED`, application result and security events where semantics differ | SIMPLIFY NOW | recipient/title/body/category/action are unambiguous |
| F-010 | Decide and test `deleted_at` output compatibility | REMOVE NOW | serializer matches canonical schema and client contract |
| F-011 | Align baseline/demo Admin `user_roles.assignment_reason` with the required `ADMIN_PRIMARY` sub-role and add seed-idempotence coverage | FIX BEFORE LIVE CROSS-ROLE ACCEPTANCE | Corrected disposable runtime plus the current live runtime now report `is_primary_admin:true`; live approve/reject branches and empty-reason validation were re-tested with real queue/owner-notification post-conditions. Seed-idempotence remains open |

### Phase 3 — browser and operational acceptance

1. Login each demo role in isolated sessions.
2. Run notification center cold load, unread count, mark one, mark all, dismiss, refresh, pagination, role switch and logout.
3. Trigger real business actions: course submit/approve/reject, lesson/resource request, enrollment, assessment grade/regrade, file rejection, password/role/security changes.
4. Capture request/response/UI/result and verify the resulting entity state, not only toast text.
5. Run SQL Server migration/concurrency probes when the SQL Server URL/engine is available.

## Reuse and anti-overengineering decisions

### F-004/F-005 Browser acceptance correction

The three representative-role Browser acceptance now passes: on `http://localhost:5000`, clean Admin, Instructor and Student sessions were each tested with temporary blocking of all notification endpoints; each role showed the explicit unavailable message and `Thử lại` action without the false empty state, and removing the block plus retry restored the real notification list. No business mutation was submitted. This closes the representative-role Browser outage path, while rapid retry/idempotency, email delivery and full business-event coverage remain open.

### New scoped fixes from the 2026-10-05 Browser continuation

| Fix ID | Change | Classification | Acceptance |
|---|---|---|---|
| F-012 | Normalize graded-result notification CTAs to the Student attempt-result route | SIMPLIFY NOW | focused attempt-service regression passes; the 2026-10-06 disposable SQL/HTTP/Browser replay opened a newly emitted regrade event and rendered the canonical released attempt result; broader producer/role coverage remains separate |
| F-013 | Normalize enrollment notification CTAs to existing role-specific SPA course routes | SIMPLIFY NOW | focused enrollment regression captures both recipient URLs; correlate one fresh live enrollment with UI/API/DB |
| F-014 | Distinguish notification loading/revalidation from a legitimate empty state | KEEP | Node delayed-fetch regression shows skeleton until a successful response; Browser still has a transient empty-state observation during cold revalidation, so live timing acceptance remains open |
| F-015 | Reject non-object JSON before notification mutation field access | COMPLETED / SIMPLIFY NOW | focused API regression and fresh live JWT probes return HTTP 400 for broadcast string, mark-all list and preferences string; canonical outer envelope remains a separate contract check |
| F-016 | Commit enrollment and `STUDENT_ENROLLED` recipient rows in one service transaction | SIMPLIFY NOW | red persistence regression failed before the ordering fix; focused enrollment scope reports 20 passed, split pytest verification reports 1572 passed with zero skips, and fresh live DSA201 replay correlates ACTIVE enrollment plus both recipient notifications; historical OPS401 orphan rows remain a data-repair concern |
| F-017 | Normalize course-change rejection notification identifiers | COMPLETED / SIMPLIFY NOW | `admin/routes.py` now uses course code for the title and the course public UUID in the audit/event payload and action URL; the red regression became green, the changeset suite reports 12 passed, and live request `#60004` correlated Browser CTA with SQL event `140017` and notification `150090`. Historical `70014` rows are retained and not rewritten |

- Reuse `notification_service.py`, existing API client, router and current canonical event tables.
- Do not add a new queue, microservice, frontend framework or duplicate schema for this problem.
- Do not fix 37 callsites one-by-one with custom prose; move prose to a catalog and pass structured facts.
- Do not use a second notification table or a UI-only dedupe cache.

### F-018 - make Admin broadcast retry-safe

| Change | Classification | Acceptance |
|---|---|---|
| Add UUID `X-Idempotency-Key` handling to the shared broadcast service and all Admin broadcast routes; return replay metadata, reject changed payloads, and retain one key across the Browser modal retry while disabling concurrent submit. | COMPLETED / SIMPLIFY NOW | RED API regression failed before the change; API/service/frontend tests pass, a disposable Browser double-click produced one POST/one success toast, and SQL Server showed one event plus seven recipient rows. |

### F-020 - guard shared REST notification mutation payloads

| Change | Classification | Acceptance |
|---|---|---|
| Apply the existing object-payload guard to shared broadcast, email-retry and preferences routes before any `.get()` or service call. | COMPLETED / SIMPLIFY NOW | RED regression reproduced 500 for list payloads; focused API tests and disposable live HTTP returned 400 `VALIDATION_ERROR`, with no SQL business mutation. |

### F-021 - normalize the scoped notification response envelope

| Change | Classification | Acceptance |
|---|---|---|
| Return `success=true,data=...` for scoped notification successes and `success=false,data=null,error=...` for scoped notification errors, while retaining existing top-level compatibility fields during migration. | COMPLETED / SIMPLIFY NOW | RED contract regression reproduced missing `success/data`; notification API **12**, Admin broadcast **1**, notification IDOR **7**, full API **383**, and the current **1587-test** split passed with zero skips. Wider API/web-auth envelope drift remains a separate follow-up. |

### F-031 - provide a deterministic email delivery sink for acceptance

| Change | Classification | Acceptance |
|---|---|---|
| Configure a disposable SMTP sink/provider for the audit/release environment and verify `FAILED → retry API → SENT` against a captured message and exact recipient. | PARTIAL / KEEP | Fresh SQL Server probe now uses real `smtplib` wire transport to an ephemeral loopback SMTP sink and captured `student4@pwd301.local` with subject `PWD301 audit email`; retry returned `200` with `retried_count=1`, final state was `SENT`, and cleanup was `0`. Approved external provider response and inbox receipt remain open. |

### F-028 - unblock Browser-controlled file selection without weakening file safety

| Change | Classification | Acceptance |
|---|---|---|
| Provide a narrowly scoped Browser file-chooser permission or one manual fixture selection for the local audit; rerun valid image upload, wrong MIME/size, pending/quarantine denial and notification/DB post-condition checks. | OPEN / KEEP | Current live input is present with the correct allowlist, but Edge returns `Not allowed` before the API. No backend bypass or fabricated upload success is acceptable. |

### F-029 - prove resource download stream completion

| Change | Classification | Acceptance |
|---|---|---|
| Trace the authenticated resource response through Browser download completion, content length and file readability; fix only the owner layer if the `.crdownload` reproduction is application/proxy-owned. | OPEN / SIMPLIFY NOW | Current Browser click produced a persistent 1169-byte `.crdownload`; acceptance requires a finalized readable PDF and no misleading success notification. |

### F-030 - keep Student result alert title/message ownership consistent

| Change | Classification | Acceptance |
|---|---|---|
| Align the shared `UI.alert` signature with the existing title-first callers, escape multiline body content and preserve line breaks through the existing modal system. | COMPLETED / SIMPLIFY NOW | RED regression reproduced the inverted title; focused GREEN plus full frontend **102 passed, 0 failed, 0 skipped**. Browser trigger replay remains a separate acceptance gate. |

### F-032 - remove raw network telemetry from security notification copy

| Change | Classification | Acceptance |
|---|---|---|
| Keep security alerts actionable but omit concrete IP/path telemetry from user-facing copy; update the demo seed and repair the matching live seeded row. | COMPLETED / SIMPLIFY NOW | RED regression reproduced the seeded IP leak; GREEN passed, live SQL Server returned zero raw-IP matches, and Admin Browser reload showed safe Vietnamese copy. |

### F-034 - redact raw network telemetry at the shared SECURITY dispatch boundary

| Change | Classification | Acceptance |
|---|---|---|
| Add one shared IPv4 redaction helper for mandatory SECURITY notifications and apply it to title, body and user-facing action/target URLs before persistence and delivery. | COMPLETED / SIMPLIFY NOW | RED regression reproduced the leak in all three fields; current focused notification unit/API/demo/security scope passed **37**, the full non-overlapping split passed **1,589**, and SQL Server disposable gates passed **17** with zero audit databases remaining. |

### F-033 - restore server-authoritative manual ESSAY grading and truthful result detail

| Change | Classification | Acceptance |
|---|---|---|
| Reuse the existing grading route and result cards: expose grade `row_version`, add score/reason controls only for pending/manual ESSAY rows, call the existing grading API, and render persisted essay text/awarded points/status/feedback without choice-only labels. | COMPLETED / SIMPLIFY NOW | RED/GREEN frontend regression passed; full frontend **105 passed, 0 failed, 0 skipped**; full API **383 passed**; live Browser save showed `3.5 / 20` and `3.5 / 4`, SQL Server showed `MANUAL_GRADED`, fixture cleanup returned zero attempts/orphans, and Student Browser result replay showed the persisted answer, `4 / 4 đ`, feedback and no choice labels. |

### F-035 - distinguish policy-hidden ESSAY answers from empty answers

| Change | Classification | Acceptance |
|---|---|---|
| Keep the backend `answer_visibility_policy` boundary and make the Student result renderer show explicit policy-hidden copy when an ESSAY answer is intentionally omitted; retain “Không trả lời” only for a visible empty answer. | COMPLETED SOURCE / BROWSER PENDING | TDD RED/GREEN passed; answer-visibility security and mixed-grading API tests passed; full frontend **107 passed, 0 failed, 0 skipped**. Post-fix Browser visual replay remains pending because the CUA Browser binding was unavailable, and no bypass was used. |

### F-036 - remove fabricated Student result metadata

| Change | Classification | Acceptance |
|---|---|---|
| Remove the fixed signature-like value and false instructor/duration defaults from the result page; render API-provided values or explicit unknown state. | COMPLETED SOURCE / BROWSER PENDING | TDD RED/GREEN passed; the focused remediation scope and full frontend now pass **108**, Ruff passes, and no fixed signature remains. Browser visual acceptance remains pending because the CUA Browser binding is unavailable. |

## Latest scoped remediation (2026-10-05)

| Change | Classification | Acceptance |
|---|---|---|
| Validate REST notification `role`/`target_role` filters against the canonical role set and the authenticated actor's active roles for list, unread-count and mark-all-read. | COMPLETED / SIMPLIFY NOW | TDD RED reproduced two invalid-role cases returning `200`; GREEN returned `400 VALIDATION_ERROR` for `ADMIN` and `BOGUS` under Student auth while valid lower-case `student` remained `200`. Current notification API/service/IDOR scope: **34 passed, 0 failed, 0 skipped**. No schema/data migration. |

This is a scoped contract correction, not a release sign-off. The refreshed non-overlapping Python split now reports **1,591 passed, 0 failed, 0 skipped** (`298 + 633 + 385 + 258 + 17`), with the two disposable SQL Server databases cleaned. Full producer/role breadth, external SMTP/inbox evidence, Browser file selection/quarantine access and broader retry/idempotency remain separate gates.

## Deferred ponytails

| Ponytail | Trigger | Owner | Risk | Temporary safeguard | Review point |
|---|---|---|---|---|---|
| P-001 | email/template localization beyond in-app catalog | product + backend | channels diverge | keep mandatory event list and user-safe text | after Phase 2 catalog |
| P-002 | cross-tab realtime delivery | frontend/platform | stale center between refreshes | explicit refresh/retry and unread count | after browser acceptance |
| P-003 | SQL Server rowversion concurrency for notification read/dismiss | backend/DBA | SQLite does not prove race behavior | run disposable SQL Server probes before release | before release gate |

## Newly observed acceptance gates

- Keep course review submission and Admin queue visibility as one cross-role acceptance test; a sender-side `Chờ duyệt` toast is not enough.
- Keep exam publish, waiting-room start, autosave, fullscreen violation, submit, result and PDF export as separate evidence rows. Do not collapse them into one “exam passed” result.
- Treat the local test records (`AUDIT1004` and the published sample assessment) as disposable audit data and do not use them as production metrics.

## F-037 - keyed lesson-flag retry safety (2026-10-06)

| Fix | Implementation | Evidence | Remaining boundary |
|---|---|---|---|
| Add request idempotency to Admin lesson flags | Both routes forward X-Idempotency-Key; flag_lesson_content validates UUID, reuses the canonical event on exact replay, rejects changed payloads, and reports idempotent_replay | TDD RED/GREEN: **9 passed**; SQL Server disposable replay: **3/3, 0 failed, 0 skipped**; SQL delta 1 audit/1 event/1 notice; cleanup remaining 0 | Browser rapid-retry visual acceptance and other notification producers remain open |

## F-038 - remove title/body duplicate hiding (2026-10-06)

| Fix | Implementation | Evidence | Remaining boundary |
|---|---|---|---|
| Make durable notification visibility truthful | Removed the newer-row title/body heuristic from _visible_notification_query; exact retries use producer idempotency keys | RED reproduced 1 visible item for 2 distinct events; GREEN combined scope **37 passed, 0 failed, 0 skipped**; Ruff and diff check passed | Historical duplicate disposition, Browser visual replay and full producer catalog remain open |
The F-038 SQL Server gate is now also closed for the scoped API path: the disposable HTTP probe observed 2 SQL rows and 2 REST items for the same-copy distinct events, with **1 case, 0 failed, 0 skipped** and cleanup remaining 0. This does not imply that historical duplicate rows should be deleted.
## F-039 - validate generic event-key replay semantics (2026-10-06)

| Fix | Implementation | Evidence | Remaining boundary |
|---|---|---|---|
| Prevent silent event-key semantic changes | emit_event compares event type, actor, target and sanitized payload; exact replay remains allowed, mismatch raises ConflictError | RED/GREEN scope **38 passed, 0 failed, 0 skipped**; SQL Server probe **2 cases, 0 failed, 0 skipped**, cleanup 0 | Stable-key adoption across every producer and Browser replay remain open |
## F-040 - SQL Server seed-idempotency evidence (2026-10-06)

| Fix/gate | Implementation | Evidence | Remaining boundary |
|---|---|---|---|
| Prove demo seed idempotency on SQL Server | Added a guarded disposable probe that runs seed_demo twice and compares logical counts plus created summaries | **1 case, 0 failed, 0 skipped**; all counts unchanged; cleanup remaining 0 | Live database reseed and full Browser role breadth remain outside this probe |

## F-041 - expose stable event keys at shared dispatch boundary (2026-10-06)

| Fix | Implementation | Evidence | Remaining boundary |
|---|---|---|---|
| Allow retryable producers to pass their business idempotency key through the common notification helper | Added optional trailing `event_key` to `dispatch_notification()` and forwarded it to `emit_event()`; existing callers remain compatible | RED TypeError then GREEN exact-replay test; focused notification/flag scope **39 passed, 0 failed, 0 skipped**; Ruff, compile and diff check passed | Stable-key adoption in every producer, Browser rapid retry, external SMTP/inbox, upload/quarantine and historical disposition remain open |

## F-042 - include dispatch presentation semantics in keyed conflict checks (2026-10-06)

| Fix | Implementation | Evidence | Remaining boundary |
|---|---|---|---|
| Prevent a changed title/body from silently reusing a keyed notification event | Add `_dispatch_contract` only for keyed dispatch, containing sanitized title/body/category/target role/force-email semantics; `emit_event()` performs the existing comparison | RED changed-body assertion failed; GREEN verified exact replay keeps one event/notice/email outbox and changed content raises `ConflictError`; focused scope **39 passed, 0 failed, 0 skipped** | 32 direct dispatch callsites have neither an explicit key nor a prebuilt event; Browser retry, external SMTP/inbox and file gates remain open |

## F-043 - key enrollment notification fan-out by durable enrollment (2026-10-06)

| Fix | Implementation | Evidence | Remaining boundary |
|---|---|---|---|
| Make `STUDENT_ENROLLED` retry-safe for both recipients | Pass UUIDv5 keys derived from `enrollment.id`, event type and `INSTRUCTOR`/`STUDENT` role to the common dispatcher | RED/GREEN unit capture; SQL Server disposable probe **3 cases, 0 failed, 0 skipped**, exact replay kept event/notification rows at `2 -> 2`, cleanup 0 | 32 direct dispatch callsites have neither an explicit key nor a prebuilt event; Browser rapid retry, external SMTP/inbox, upload/quarantine and historical disposition remain open |

## F-044 - key password security notifications by auth version (2026-10-06)

## F-045 - key course lifecycle notification fan-out by durable audit transition

## F-046 - key course-owner reassignment notification fan-out

| Fix | Implementation | Evidence | Remaining boundary |
|---|---|---|---|
| Make former/new owner notices retry-safe | Retain and flush COURSE_OWNER_REASSIGNED AuditEvent; pass one UUIDv5 key per recipient | TDD RED/GREEN unit test; former/new keys are distinct; no SQL Server probe yet | Dedicated SQL replay, Browser retry/visual acceptance, external inbox and 25 remaining unkeyed calls |

## F-047 - key password-reset token security notification

| Fix | Implementation | Evidence | Remaining boundary |
|---|---|---|---|
| Make reset-token security fan-out retry-safe | Reuse the password mutation key helper with user ID and post-reset auth_version | TDD RED/GREEN reset-token unit test; SQL Server disposable probe kept event/notification/email rows at 1 -> 1, 6 cases, 0 failed, 0 skipped, cleanup 0 | Browser retry/visual acceptance, external inbox and 24 remaining unkeyed calls |

## F-048 - key account-suspension security notification

| Fix | Implementation | Evidence | Remaining boundary |
|---|---|---|---|
| Make suspension security fan-out retry-safe | Derive UUIDv5 from user ID and post-suspension auth_version and pass it to the shared dispatcher | TDD RED/GREEN unit test; SQL Server combined security probe kept event/notification/email rows at 1 -> 1, 9 cases, 0 failed, 0 skipped, cleanup 0 | Browser retry/visual acceptance, external inbox and 23 remaining unkeyed calls |

| Fix | Implementation | Evidence | Remaining boundary |
|---|---|---|---|
| Make course submission/approval/rejection notices retry-safe | Retain and flush the lifecycle AuditEvent; pass UUIDv5 keys derived from audit ID, action and recipient ID to all three notification branches | TDD RED/GREEN lifecycle test; SQL Server disposable exact replay kept event/notification rows at 1 -> 1, 4 cases, 0 failed, 0 skipped; enrollment/password probes remained green; cleanup 0 | Current AST inventory: 27 direct calls have neither explicit key nor prebuilt event; Browser retry/visual acceptance, external SMTP/inbox and historical disposition remain open |

| Fix | Implementation | Evidence | Remaining boundary |
|---|---|---|---|
| Make committed password-change security fan-out retry-safe | UUIDv5 over `user.id` and post-mutation `auth_version` in both `change_password()` and `set_password()` | RED/GREEN unit key assertion; SQL Server disposable probe **3 cases, 0 failed, 0 skipped**, exact replay kept event/notification/email rows at `1 -> 1`, cleanup 0 | 30 direct dispatch callsites have neither explicit key nor prebuilt event; Browser retry, approved inbox, upload/quarantine and historical disposition remain open |

| Make role, course-review and malware-rejection producers retry-safe | Use post-mutation auth-version keys for role changes, flushed audit/change-request IDs for course review, and persisted revision IDs for rejected files | TDD/API RED-GREEN passed for the four sampled boundaries; Ruff passed; AST now 35 calls / 25 explicit keys / 1 prebuilt event / 9 neither | Dedicated SQL replay, Browser/CUA, external inbox, and the remaining nine producer decisions remain open |

| Close the remaining direct producer inventory | Add deterministic keys to assessment-result, YouTube-health, Admin route and instructor prerequisite/lesson route notifications | Focused attempt 13, API 28 and service 79 test groups passed; Ruff/compile passed; AST now 35 calls / 34 explicit keys / 1 prebuilt event / 0 neither | SQL Server exact replay, Browser/CUA visual/rapid retry, external inbox and historical disposition remain open |

## N-168 verification checkpoint (2026-10-06)

| Full verification gate | Run `scripts/verify.ps1` with fresh disposable SQL Server migration and concurrency URLs | **PASS: 1607 passed, 0 failed, 0 skipped; exit 0**; SQL Server opt-in cases executed; disposable databases removed | Browser/CUA, external inbox, file chooser/quarantine and historical duplicate disposition remain open |

## N-169 live email backlog remediation (2026-10-06)

| Fix | Root cause | Evidence | Remaining gate |
|---|---|---|---|
| Add durable EMAIL worker bridge and deployment | 115 live outbox rows had no consumer; Compose had no worker | RED reproduced `run_worker_once() == False`; GREEN passed worker/outbox test; Compose contract and `docker compose config` pass | Do not activate live worker until approved SMTP is configured |
| Remove false production success path | Non-testing default used `MockMailClient` | RED/GREEN fail-closed and SMTP TLS adapter tests; 10 email tests pass | External provider and inbox receipt remain open |
| Make health honest | 115 stale rows were reported as healthy | RED/GREEN stale queue health test; live `/health/deep` reports `DEGRADED` | Browser/CUA and external delivery evidence remain open |

## N-170 current gate status (2026-10-06)

| Gate | Evidence | Status | Next required evidence |
|---|---|---|---|
| Computer Use Browser | `getState()` returned no apps/browsers; direct IAB creation returned `Browser is not available: iab` | BLOCKED ENVIRONMENT | Expose an approved Browser surface and rerun real login/workflow checks |
| Full regression | SQL-enabled `scripts/verify.ps1` reported 1612 passed, 0 failed, 0 skipped; disposable DBs removed | PASS | Preserve as current automated baseline |
| Worker deployment | `docker compose build worker` passed; live worker intentionally not started | PARTIAL | Configure approved SMTP, then run worker and verify inbox delivery |

## N-171 historical notification disposition (2026-10-06)

| Fix | Current evidence | Status | Required safe next step |
|---|---|---|---|
| Classify historical repeated copy | 143 events, 168 notifications, 0 duplicate event keys, 14 repeated presentation-copy groups | PARTIAL | Map each group to a durable business transition in a disposable SQL fixture |
| Repair or delete history | Several legacy payloads have no transition identity; no live mutation performed | DEFERRED / SAFETY HOLD | Obtain owner approval and prove notification, email and audit referential effects before any repair |

## N-172 API envelope correction (2026-10-06)

| Fix | Evidence | Status | Remaining scope |
|---|---|---|---|
| Normalize Web notification success payloads | TDD RED/GREEN; 16 API tests, Ruff, compile and 7 focused frontend tests passed | PASS scoped | Run the full post-patch verifier and Browser acceptance when the environment is available |
| Preserve current clients | Top-level aliases remain alongside canonical `data` | PASS compatibility boundary | Remove aliases only after client migration evidence |

## N-173 aggregate verification (2026-10-06)

| Gate | Result | Evidence boundary |
|---|---|---|
| Full repository verification after N-172 | PASS | 1613 passed, 0 failed, 0 skipped; exit 0; disposable SQL Server databases removed |
| Browser and external delivery | OPEN | CUA has no Browser surface; SMTP/inbox is not configured |

## N-174 acceptance-scope decision (2026-10-06)

The owner explicitly removed SMTP/inbox from this acceptance cycle because it is not deployed. The fix-plan gate is consequently split: external delivery is **OUT OF SCOPE**, while Browser/CUA and file chooser/quarantine remain **OPEN** and still require real Browser evidence.

## N-175 Browser verification checkpoint (2026-10-06)

| Flow | Result | Evidence boundary |
|---|---|---|
| Student/Instructor/Admin login and logout | PASS | Real Edge UI toasts observed for demo accounts |
| Instructor notification dropdown and mark-all-read | PASS | 15 unread changed to 0; success toast observed; repeated/mixed-language content recorded |
| Admin operations and Student permission denial | PASS | Live degraded queue and Vietnamese permission warning rendered |

## N-176 file/quarantine checkpoint (2026-10-06)

| Flow | Result | Evidence boundary |
|---|---|---|
| Clean Student resource download | PASS | Browser `downloadMedia` completed for a visible PDF link |
| Upload chooser assignment | BLOCKED | Edge extension returned `Not allowed`; file-URL access permission is disabled |
| PENDING/QUARANTINED Student denial | UNVERIFIED | Live SQL has no current rows; rejected URL was blocked by client before app response |

## N-177 Student notification checkpoint (2026-10-06)


| Flow | Result | Evidence boundary |
|---|---|---|
| Student notification panel and filters | PASS | Browser rendered 0 unread, five category controls and role label |
| Student notification language consistency | OPEN | Mixed-language legacy content is visible; producer/catalog ownership still needs mapping |
## N-178 upload/quarantine checkpoint (2026-10-06)

| Flow | Result | Evidence boundary |
|---|---|---|
| Clean Instructor course-image upload | PASS | Edge chooser accepted the clean image, crop/apply completed, success toast rendered; SQL Server shows current `ACTIVE` revision and two `PASS` scan results |
| Rejected/PENDING/QUARANTINED denial through Browser | UNVERIFIED | Rejected-file URL remains `ERR_BLOCKED_BY_CLIENT` before application response; no malicious fixture was uploaded |
| SMTP/inbox delivery | OUT OF SCOPE | Owner confirmed the service is not deployed |
## N-179 rejected-file checkpoint (2026-10-06)

| Flow | Result | Evidence boundary |
|---|---|---|
| Course-scoped inline request for historical rejected asset | UNVERIFIED | Edge returned `ERR_BLOCKED_BY_CLIENT` before application response; SQL shows no lesson/resource attachment |
| Quarantine override | NOT RUN | Would release a rejected asset and would not be a valid denial test |
## N-180 authenticated route checkpoint (2026-10-06)

| Flow | Result | Evidence boundary |
|---|---|---|
| Rejected file from authenticated Instructor tab | UNVERIFIED | Edge still returned `ERR_BLOCKED_BY_CLIENT` before application response; session was restored afterward |
## N-181 system-category checkpoint (2026-10-06)

| Flow | Result | Evidence boundary |
|---|---|---|
| Instructor filters notifications by `Hệ thống` | PASS | Browser rendered exactly two system-category records and preserved `0` unread |
| System message language/ownership | OPEN | Legacy mixed-language maintenance copy remains visible beside Vietnamese security copy |
## N-182 assessment-category checkpoint (2026-10-06)

| Flow | Result | Evidence boundary |
|---|---|---|
| Instructor filters notifications by `Khảo thí` with no rows | PASS | Browser rendered explicit empty state and no fabricated item |
| Global assessment producer coverage | OPEN | One role/category empty state cannot prove all assessment producers are wired |
## N-183 course-category checkpoint (2026-10-06)

| Flow | Result | Evidence boundary |
|---|---|---|
| Instructor filters notifications by `Khóa học` | PASS | Browser rendered 16 records and preserved `0` unread |
| Historical `#70014` duplicate identity | OPEN | Three related copies are visible, but business identity is insufficient for deletion/merge |

## N-184 Admin broadcast validation checkpoint (2026-10-06)

| Flow | Result | Evidence boundary |
|---|---|---|
| Admin submits broadcast with empty required fields | PASS | Browser showed the title validation message, then the body validation message for title-only input |
| Validation leaves no durable notification/outbox write | PASS, scoped | Container SQL snapshot remained `143` events, `168` notifications, `115` pending emails and `0` jobs; newest event predated the probe |
| Valid broadcast delivery and SMTP/inbox | OUT OF SCOPE | Owner confirmed SMTP/inbox is not deployed and may be skipped in this cycle |

## N-185 quarantine test-target checkpoint (2026-10-06)

| Gate | Result | Evidence boundary |
|---|---|---|
| Rejected revisions attached to a user-facing lesson resource | OPEN / unavailable | SQL Server found 7 `REJECTED` revisions and 0 `lesson_resources` links |
| Browser quarantine denial / HTTP 403 | UNVERIFIED | Direct route is intercepted by Browser client before application response; no safe attached fixture exists |
| Malicious upload or quarantine override | NOT RUN | Would create/release unsafe data and is not needed to establish the current data limitation |

## N-186 fail-closed API checkpoint (2026-10-06)

| Gate | Result | Evidence boundary |
|---|---|---|
| Authenticated rejected-file API denial | PASS | Instructor HTTP session received `403`, `success:false`, `FILE_INFECTED`, and no file bytes |
| Browser/UI denial message | UNVERIFIED | Edge intercepted the direct request before the application response; no rejected revision is attached to a resource |

## N-187 SMTP/inbox scope checkpoint (2026-10-06)

| Gate | Result | Evidence boundary |
|---|---|---|
| External SMTP provider and inbox receipt | OUT OF SCOPE | Owner confirmed SMTP/inbox is not deployed for this cycle |
| Local outbox/health truthfulness | OBSERVED ONLY | Pending rows and degraded health remain operational evidence; they are not delivery proof |

## N-188 historical duplicate remediation boundary (2026-10-06)

| Gate | Result | Evidence boundary |
|---|---|---|
| Historical copy groups with business correlation | PASS, scoped | 12/14 groups mapped; 7/7 `FILE_REJECTED` to revision exact matches and request/review timing evidence |
| Unkeyed legacy rows | SAFETY HOLD | 17 rows across 2 groups lack durable business identity; obtain owner mapping and rehearse repair in disposable DB |

## N-189 Browser quarantine-override validation (2026-10-06)

| Gate | Result | Evidence boundary |
|---|---|---|
| Primary-admin quarantine override form | PASS, scoped | Real Browser modal opened; empty submit was rejected with the required File Asset ID message; no mutation occurred |
| Successful quarantine release and audit transition | OPEN | No password or release action was attempted; prove only in an approved disposable/rehearsal path before live mutation |

## N-190 focused quarantine regression (2026-10-06)

| Gate | Result | Evidence boundary |
|---|---|---|
| Override authorization/validation regression | PASS, focused | 2 override tests passed; 34 tests in the selected modules were deselected |
| Quarantined/infected access remains fail-closed | PASS, focused | 1 security test passed; 11 tests in the selected module were deselected |
| Credentialed live release | OPEN | Not attempted; live state and audit history remain unchanged by this check |

## N-191 Browser runtime observation (2026-10-06)

| Gate | Result | Evidence boundary |
|---|---|---|
| Application console errors in inspected flows | OBSERVED CLEAR | No application error was captured; one Tailwind CDN production warning remains |

## N-192 legacy identity safety hold (2026-10-06)

| Gate | Result | Evidence boundary |
|---|---|---|
| Durable mapping for the 17 legacy rows | SAFETY HOLD | Recipient-only `target_id`, NULL correlation/actor, generic action URL and no matching audit event; obtain owner mapping before any repair |

## N-194 rejected-file Browser environment gate (2026-10-06)

| Gate | Result | Evidence boundary |
|---|---|---|
| Browser app-level denial for rejected file | BLOCKED ENVIRONMENT | Edge owns the response and shows `ERR_BLOCKED_BY_CLIENT`; IAB is unavailable, so no app 403/UI denial claim is made |
| Backend/API fail-closed denial | PASS, scoped | Authenticated HTTP returned `403`, `FILE_INFECTED`, safe message and no file bytes for the sampled rejected asset |

## N-195 download-route family environment gate (2026-10-06)

| Gate | Result | Evidence boundary |
|---|---|---|
| Edge handling of Instructor and API file-download paths | BLOCKED ENVIRONMENT | Both routes return the browser-owned `ERR_BLOCKED_BY_CLIENT` page before Flask; IAB is unavailable |
## N-196 exact business-window recheck (2026-10-06)

A further read-only SQL Server check searched `course_change_requests` in the exact event windows for the 13 unresolved `LESSON_CHANGE_REQUEST` copies (2026-09-28 03:10:04-03:16:28 UTC) and the four unresolved `COURSE_CHANGE_APPROVED` copies (2026-09-28 05:44:15-05:44:22 UTC and 2026-09-29 02:09:31 UTC). It returned no rows in those windows. Current CS101 change-request rows exist at other times, but none can be safely joined to these notifications from the stored recipient-only target, NULL correlation/actor fields and generic action URLs. This is additional evidence for an owner-approved mapping/rehearsal hold; no append-only history was mutated. Final status remains **PARTIAL - not release-accepted**.
## N-197 Browser fail-closed resource-visibility proof (2026-10-06)

Using the enrolled Student Browser session, a temporary, explicitly labeled `lesson_resources` row `120002` was attached to published SEXGAY lesson `130025` and pointed at existing asset `3EB32DEA-150D-4724-B42C-2FEBB53BAD16`. SQL identified the asset as `PENDING` with current revision `REJECTED`, reason `Infected: ZIP-Embedded-Executable`. The real Student `Tài liệu` panel still rendered only the four ACTIVE files and exposed no link, preview or download CTA for the rejected resource. A direct Student-scoped URL was separately attempted and Edge returned `net::ERR_BLOCKED_BY_CLIENT` before an application response, so the UI omission is the verified Browser fail-closed result and the direct response remains environment-blocked. The temporary resource row was then deleted by exact ID and label; SQL verified the lesson returned to four resource links, the rejected asset remained `PENDING`, its revision remained `REJECTED`, and it had zero resource links. No file revision, quarantine state, notification row or audit record was mutated. Final status remains **PARTIAL - not release-accepted** because direct Browser response observation and historical owner-approved notification disposition remain open.
## N-198 acceptance checkpoint after temporary Browser fixture (2026-10-06)

The temporary Browser fixture proves the Student-facing file-visibility branch: a linked `PENDING/REJECTED` asset was omitted from the real Student resource panel, while the four `ACTIVE` files remained visible. Exact cleanup restored the lesson to four resource links and left the asset/revision unchanged. Therefore Student UI fail-closed visibility is **PASS for this sampled asset**; the direct download response remains **BLOCKED ENVIRONMENT / UNVERIFIED** because Edge intercepts the URL before the application response. SMTP/inbox remains **OUT OF SCOPE** by owner decision. Historical notification disposition remains open for the two unkeyed groups/17 rows, so the overall audit remains **PARTIAL - not release-accepted**.
## N-199 historical outbox identity recheck (2026-10-06)

Read-only SQL Server inspection found one `email_deliveries` row for each of the 17 unresolved notification events. Those rows preserve recipient email, template code, random dedupe UUID and `PENDING` status, but have NULL subject/body and no `course_change_request_id`, target resource or correlation field. This provides no additional safe business identity for historical repair. SMTP/inbox remains owner-authorized **OUT OF SCOPE**; no delivery was attempted and no outbox/history row was mutated. Final status remains **PARTIAL - not release-accepted**.
## N-243 dispatcher identity follow-up (2026-10-06)

No source change is proposed from this inventory. Keep the static check as a release guard and focus further work on producer-specific key derivation, durable transition mapping and concurrency replay rather than adding a generic wrapper around already-keyed callsites.

## N-242 producer-heavy follow-up (2026-10-06)

No product fix is proposed from this green regression group. Keep the 64-case group in the regression gate and use the remaining producer/role/retry matrix to target only concrete semantic gaps; do not convert fixture coverage into a global completion claim.

## N-241 lesson-flag follow-up (2026-10-06)

No lesson-flag product fix is proposed from the current reconciliation. Keep the nine-case regression in the release gate and retain RCA-040/RCA-027 as historical traceability only; do not spend remediation effort on the stale constructor diagnosis unless a future source change reproduces it.

## N-240 API/frontend follow-up (2026-10-06)

No product change is proposed from the fresh green suites. Keep the API/IDOR and frontend checks in the regression gate, while adding producer-specific tests only where a missing event identity, role mapping or retry/race branch is demonstrated; do not treat the aggregate green result as producer completeness.

## N-239 Admin filter follow-up (2026-10-06)

No UI fix is proposed from the corrected matrix: the visible filters partitioned the current Admin records as 11 course, 1 assessment and 3 system/security, totaling 15 with zero unread. Retain a regression assertion for these counts only if the fixture contract intentionally seeds this exact dataset; otherwise assert category consistency rather than hard-coded production totals.

## N-237 Admin role follow-up (2026-10-06)

No immediate UI fix is proposed: the Admin notification center rendered its persisted records correctly in the fresh replay. The remaining action is to add a deterministic Admin producer/broadcast fixture and assert event key, recipient, category, language and retry behavior end to end.

## N-238 Guest boundary follow-up (2026-10-06)

No product change is proposed from this observation: the protected client route redirected to `/auth` and exposed no notification control. Keep the existing API `401` contract test and add a Browser assertion for each protected notification entry point if the Browser surface becomes available for multi-tab coverage.

## N-250 YouTube UI ownership follow-up (2026-10-06)

Choose and document one owner for course-wide scans: expose a visible Instructor action with truthful loading/result notification, or document and test the background scheduler/maintenance trigger. If the route remains API-only, remove the misleading assumption that the Browser can trigger it and add an explicit API/operations contract. Keep the existing Lesson Studio invalid-link validation path separate.

## N-249 YouTube Browser follow-up after route replay (2026-10-06)

The route/API and service/DB fixture are now covered. The remaining minimal step is a real Instructor Browser action for the scan control, with visible response/notification observation and no live external-network dependency. Keep that UI check read-only with a disposable course fixture if the control is exposed.

## N-248 YouTube producer follow-up after service replay (2026-10-06)

Keep the service-level probe as a regression artifact. The next smallest missing test is an authenticated Instructor route/API replay using the same mocked oEmbed branches, asserting response envelope, permission/resource scope and Browser-visible owner outcome. A live external YouTube call and SMTP/inbox are not required for this deterministic audit gate.

## N-247 YouTube producer follow-up (2026-10-06)

Add a focused fixture-backed matrix for `COURSE_LESSON_VIDEO_BROKEN`: valid oEmbed, 404/403 broken video, network error without notification, owner missing, exact retry/concurrent retry, durable event/notice counts, and the Instructor route response. Mock the external oEmbed dependency rather than depending on live YouTube availability.

## N-246 producer-key follow-up (2026-10-06)

No key-generation refactor is justified by this static result. Keep the current durable-key helpers and prioritize operation-specific runtime assertions: expected event type, actor, recipient role, payload, exact replay and concurrent replay must all converge to one durable event/notification where the business rule requires it.

## N-245 Student Browser content-quality follow-up (2026-10-06)

Add a catalog/data-quality remediation item before any visual redesign: map the four current category filters to canonical notification types, replace non-user-facing seed copy with approved Vietnamese messages, and add a producer-to-row assertion so score notifications have an explicit taxonomy. Verify the change through API payload, SQL row and Browser rendering. Do not delete or rewrite append-only history without owner approval.

## N-244 grading/regrade producer-service regression (2026-10-06)

No product fix is proposed from this green regression group. Preserve the existing grading/regrade tests and add only the missing semantic producer matrix: deterministic event-key derivation, recipient-role assertions, exact retry and rapid-concurrency convergence, then Browser/API/DB correlation. Do not broaden the scope into SMTP/inbox until a mail provider is deployed.

## N-200 stale identity/content recheck (2026-10-06)

The unresolved notification bodies do contain coarse labels: all 13 `LESSON_CHANGE_REQUEST` copies name CS101 and Lesson `Bài 1: Tổng quan về Kiến trúc Web & HTTP Protocol`, but none stores a change-request ID, durable target ID or correlation. The four `COURSE_CHANGE_APPROVED` copies name the same Lesson but their CTA points to course UUID `cf547469-d8b8-43ef-882c-721048826232`, which is absent from the current `courses` table; the current CS101 row has a different public UUID. Current CS101 change-request rows exist, including multiple historical candidates for the same lesson, but none matches the notification event windows. This confirms stale/missing business identity rather than an unresolved title-only query; no historical row was reassigned, deleted or merged. Final status remains **PARTIAL - not release-accepted**.

## N-251 frontend mechanism follow-up (2026-10-06)

The minimal follow-up is to keep one message contract/catalog behind the existing UI surfaces, then map each producer and HTTP outcome to the correct surface without silently converting failures to success toasts. Add focused checks for `UI.alert`, `UI.confirm`, `UI.prompt` and the remaining direct `window.confirm`, plus screen-reader announcement timing for the six `aria-live`/four `role="alert"` elements. Do not replace the current 383 callsites wholesale or add a new notification framework without a measured defect; this checkpoint is inventory-only. SMTP/inbox remains out of scope until a provider is deployed.
## N-252 producer coverage follow-up (2026-10-06)

No product fix is proposed from the 35/35 line-execution result. Preserve the three disposable probes as audit evidence, then extend the test matrix by producer semantics: recipient-role assertions, error/success message ownership, duplicate request convergence and concurrent retry ordering. Do not treat 100% dispatcher-line coverage as permission to close the remaining Browser, historical-data or async/race gates.
## N-253 auth-error accessibility follow-up (2026-10-06)

Keep the inline auth error as the single owner for this field/business failure, but give it an explicit live-region contract and a focused regression for announcement and cleanup. Do not add a second toast for the same failed login. Verify both persistence and successful-login replacement in Browser; the current observation is evidence of an open accessibility gate, not a product fix.
## N-254 file-chooser follow-up (2026-10-06)

Keep the existing Browser boundary explicitly blocked. The next valid acceptance step requires a functioning filechooser/native-app surface or a separately authorized test harness that exposes the same upload response; do not bypass Edge policy or alter extension permissions during this audit. Once available, replay clean, rejected and scanner-unavailable files and correlate UI, HTTP and DB outcomes.
## N-255 producer role-semantic follow-up (2026-10-06)

Do not mechanically add `target_role` to all 18 broad/unscoped producers. For each one, document whether the business owner is a specific role, a user-specific notification, or an intentional multi-role/global event; then add recipient assertions and multi-role tests. Resolve the one dynamic assessment event type and its language/catalog mapping in the same matrix. This is a contract clarification step, not a broad refactor.
## N-256 focused role/retry follow-up (2026-10-06)

Keep the passing focused tests as the minimum regression contract. Extend the same assertions to the remaining 18 broad/unscoped producers before changing shared dispatch behavior; specifically require recipient identity, target role, event key and durable-row counts after exact retry and changed-payload retry. Do not treat the focused green group as a full semantic pass.
## N-257 historical repair gate (2026-10-06)

The historical disposition work is now packaged as a read-only approval packet,
not a data mutation. It lists 13 `LESSON_CHANGE_REQUEST` rows (`50002–50014`)
and four `COURSE_CHANGE_APPROVED` rows (`60002–60004`, `90006`), with one
notification/outbox row per event and unique event keys. The safe fix sequence
is owner mapping -> disposable rehearsal -> explicit approval -> exact
post-change verification. Until then, retain all 17 rows unchanged. See
[`09_HISTORICAL_NOTIFICATION_APPROVAL_PACKET.md`](09_HISTORICAL_NOTIFICATION_APPROVAL_PACKET.md).
SMTP/inbox remains **OUT OF SCOPE**.
## N-258 file chooser blocker (2026-10-06)

The second Edge recheck reproduced the no-chooser timeout and Browser-session
reset. No product upload fix is inferred from this environment failure. Keep
the file fixture and quarantine acceptance gate open until Edge permits the
chooser or an equivalent authorized Browser surface produces a real response.
## N-259 message-catalog and historical-copy evidence (2026-10-06)

Fresh Browser content strengthens the minimal fix direction: preserve distinct
business events, normalize legacy `#70014`/reason presentation through durable
identity, and route user-facing text through one catalog. The live sample is 16
course cards plus two system cards; no global language count is inferred and no
product code was changed by this audit step.
## N-260 role-view semantics fix boundary (2026-10-06)

Do not bulk-fill `target_role` on the 18 callsites. First classify account-wide
security/role messages versus route-specific prerequisite, review,
intervention, application and YouTube messages. Then add the smallest
producer-specific role/CTA contract and multi-role regression; preserve direct
recipient authorization and avoid inventing a fan-out key.
## N-261 minimal fix direction (2026-10-06)

Do not solve this with a frontend filter. Preserve the recipient-user boundary,
then make role-view inclusion explicit: either persist the intended target role
for route-specific producers or make the serializer/action contract reject a
role-incompatible NULL-target CTA. Add a multi-role REST plus Browser regression
for the Admin review notification before changing historical rows.
## N-262 schema-contract repair (2026-10-06)

Add the existing applied `target_role` column, index and CHECK constraint to the
canonical notification data dictionary and ERD/DDL references, then add a
contract check that compares documented notification columns with the applied
migration. This is documentation/verification work; do not create a second
schema or alter the live database.
## N-263 regression-test gap (2026-10-06)

Extend the existing role test with a multi-role Admin fixture and a route-
specific Admin-review notification. Assert the intended role filter only, the
absence from incompatible role views, and the unchanged cross-user boundary.
Keep the existing global-security assertion so the fix does not over-scope
account-wide notices.
## N-264 fix-scope guardrail (2026-10-06)

The remediation must preserve the existing recipient/actor authorization
boundary. Student1 isolation passed; the fix should target role-view inclusion
and CTA compatibility only, without broadening or rewriting cross-user access
rules.
## N-265 UI containment clarification (2026-10-06)

Do not treat the current Admin route warning/redirect as the fix. Keep the
router guard as defense-in-depth, but correct notification visibility or
producer `target_role`/CTA ownership before the click reaches the guard. Add a
Browser regression for an Instructor-only account and a multi-role account;
assert the former never receives an Admin-only item in its role view and the
latter does not silently switch perspective without an explicit, understandable
user action.
