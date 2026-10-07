# 04_NOTIFICATION_STANDARD

## Moderation completion and error ownership invariant

The new flag reproduction proves why success copy must follow durable business state, not merely a planned dispatch. Required audit must capture actual actor roles, redacted after-state and correlation through the existing audit mechanism; audit failure must leave no persisted flag. A claim that the owner was notified requires durable notification evidence. Optional outbound email remains a distinct delivery result and must not be fabricated.

Reject non-object JSON before field access, retain resource/COURSE_REVIEW guards, and map stable VALIDATION_ERROR/PERMISSION/INTERNAL_ERROR codes to contextual Vietnamese UI copy. The flag page catch remains the single foreground toast owner; a raw safe-but-English global message is not sufficient localized guidance. Never expose the constructor exception or internal model fields to the end user. This is a proposed invariant applied to RCA-040/F-024/F-025, not an assertion that those fixes shipped.

For Admin sub-roles, a role-assignment notification is complete only when the notice is persisted for the assigned user, the body names the actual scope, the detail/mark-as-read flow is usable, and the CTA lands on that scope's route. Permission denial for an unrelated moderation action must remain an explicit 403 with no moderation mutation. The course-review sub-role may proceed to the flag workflow, but its exact-five-character 500 remains a dependent RCA-040 failure; it must not be represented as a successful notification outcome.

Post-fix evidence satisfies this invariant for the lesson-flag path: successful Browser/REST outcomes now follow durable flag, canonical audit and owner notice persistence; malformed payloads return a safe 400; notification failure rolls back the moderation state. This is a verified scoped result, not a claim that all notification producers or duplicate delivery behavior are complete.

## Checkpoint kiểm thử không skip và an toàn môi trường (2026-10-05)

Checkpoint này có ưu tiên hơn các số liệu 1572/1578 và các trạng thái lịch sử bên dưới. Lượt chạy ban đầu có 1576 passed, 2 failed, 0 skipped; hai test upload tài nguyên và lease bài thi trả 503. Chạy riêng cho 2 passed; chạy lại toàn nhóm API trước sửa fixture cho 375 passed. Probe có restore marker trên thư mục audit riêng tái hiện đúng cả hai phản hồi MAINTENANCE_MODE_ACTIVE/503. Việc nhóm test dùng chung storage/quarantine/backups với workspace là lỗi cô lập đã được chứng minh; không quy kết chắc chắn nguyên nhân của lượt lỗi ban đầu khi chưa lưu response của lượt đó.

Fixture app nay dùng ba thư mục con riêng trong tmp_path. Regression mới thất bại với các root E:/PWD301/storage, quarantine, backups trước sửa. Sau sửa, probe vẫn giữ marker bên ngoài và 27 test upload/lease/backup/restore/maintenance đạt; không tắt maintenance hay fail-closed. Marker probe đã xóa. Test mới dùng nhầm một route không tồn tại lúc đầu; lỗi harness 404 đó đã sửa, không tính là lỗi sản phẩm.

Cô lập filesystem lộ thêm lỗi rescan: kiểm tra substring “infected” trên toàn đường dẫn nhầm thư mục cha với vùng chứa tệp nhiễm. Regression hiện hữu thất bại hai lần trước sửa; nay so sánh parent đã resolve với get_file_infected_root(), kiểm tra tệp được chuyển, key infected/hash và Student vẫn bị từ chối 403. Focused stress/file/isolation: 27 passed. Lượt split cuối sau sửa cho **1579 passed, 0 failed, 0 skipped**, khớp **1579 tests collected**: root298 + unit632 + API375 + security233 + concurrency13 + E2E12 + integration16. Frontend độc lập: **101 passed, 0 failed, 0 skipped**. Không cộng các lượt focused trùng vào tổng. Đây là kết quả các nhóm chạy đủ, không phải một aggregate verifier được tuyên bố pass; lượt aggregate lịch sử bị stall vẫn không được tính.

SQL-gated integration hiện tại: 16 passed, 0 failed, 0 skipped, gồm migration, ROWVERSION race và hai loại revision trên SQL Server thật. Hai DB migration/race tạm đã xóa, remaining=0. Browser Student4 đã đăng xuất về form login; server audit 5105 dừng; DB grading tạm cũng đã xóa, remaining=0. Không migrate/restart DB/runtime chính; fixture có thể dựng lại bằng prepare.

Audit notification vẫn PARTIAL, không phải release sign-off. Những đoạn dưới nói “chưa sửa”, “pending replay”, “1572 current” là snapshot lịch sử, không được dùng thay checkpoint mới.

## Verification boundaries and rescan outcome

Test workers must isolate both database and filesystem state; a 503 caused by maintenance is not an upload-validation error or an assessment-lease error. Preserve the stable error code and safe user guidance instead of bypassing restore protection. Filesystem isolation is a test harness responsibility, not a new production exemption.

A completed rescan is not equivalent to a clean file: HTTP 200 must be interpreted together with asset/revision status and virus_scan_status. Rejected/infected/unscanned files remain unavailable. The current Instructor endpoint's English `Rescan completed` copy was inspected in source; actual Browser presentation and translation are not accepted as verified.

## Released-result producer invariant (2026-10-05)

- The first transition into RELEASED emits ASSESSMENT_GRADED, regardless of whether scoring was automated or manual.
- A changed already-released score emits SCORE_CHANGED_AFTER_REGRADE; an unchanged retry emits no new grading notice.
- Attempt aggregation and both regrade paths share notify_assessment_result_change; target_role is STUDENT and the CTA uses the attempt public UUID.
- Hidden/PENDING/FINAL scores must not be disclosed through a grading notice. The helper checks RELEASED before constructing or dispatching copy.
- SQL Server constraints/triggers remain enabled. A persistence failure cannot be reclassified as a successful correction merely to complete a test.

The current notifier retains the existing warning/savepoint failure policy; guaranteed delivery, transactional email and historical replay are not claimed solved. The current canonical enum is reconciled by migration c4d5e6f7a8b0, not by editing an applied migration.

## Mục tiêu chuẩn hóa

Notification phải được xem là một business contract có event identity, recipient, policy và outcome; popup chỉ là một presentation channel. Không dùng popup để thay thế audit, authorization hoặc trạng thái nghiệp vụ.

## Contract đề xuất để review trước khi triển khai

### Event registry

Mỗi event được khai báo một lần với các trường bắt buộc:

| Field | Quy tắc |
|---|---|
| `code` | stable uppercase code; không dùng title làm identity |
| `category` | một trong `SECURITY`, `COURSE`, `ASSESSMENT`, `GRADE`, `SYSTEM` theo canonical DB |
| `audience` | recipient rule rõ ràng; không tin role do client gửi |
| `severity` | `info`, `success`, `warning`, `error`, `security` |
| `title_key`, `body_key` | message catalog key, không truyền prose tùy ý từ producer |
| `action_policy` | action URL/type được allow-list và resource-check |
| `idempotency_rule` | business key + recipient; retry không tạo record mới |
| `retention` | expiry policy; mandatory security/audit không bị xóa sai |
| `email_policy` | mandatory/security hoặc preference-aware |
| `schema_version` | version payload nếu client cần migrate |

### API envelope

Mọi success response dùng:

```json
{
  "success": true,
  "data": {},
  "error": null
}
```

Mọi error response dùng:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "NOTIFICATION_NOT_FOUND",
    "message": "Không tìm thấy thông báo.",
    "field_errors": {},
    "correlation_id": "..."
  }
}
```

`message` là user-safe, catalog-controlled; chi tiết exception chỉ ở server log. Giữ tương thích có chủ đích cho client cũ, không để mỗi route tự chọn shape.

### UI channel rules

- `success`: hành động nghiệp vụ đã commit thành công.
- `info`: trạng thái hoặc hướng dẫn, không khẳng định commit.
- `warning`: hành động bị giới hạn, cần người dùng xử lý.
- `error`: thao tác thất bại; luôn nêu bước tiếp theo.
- `security`: không dùng nội dung nhạy cảm; ưu tiên trang bảo mật/audit.
- Một hành động chỉ có một primary feedback; không vừa native `alert` vừa toast cho cùng outcome.
- Duration phải theo loại message và accessibility; không để producer tùy ý quyết định duration.
- Notification center phải phân biệt unread/read, expired và actionable; không coi toast đã hiển thị là đã đọc.
- Error khi refresh nền phải có degraded state hoặc retry affordance, không chỉ `console.warn`.
- CTA phải resource-authorized ở backend; action URL không được tự tạo từ ID client mà chưa load/check resource.

### Language and content

- UI user-facing PWD301 dùng tiếng Việt nhất quán; thuật ngữ kỹ thuật chỉ khi cần và có giải thích.
- Không hiển thị raw exception, SQL, path, token, IP, key hoặc stack trace.
- Title ngắn, body nêu outcome và next step; không dùng dấu chấm than hàng loạt.
- Trạng thái chưa biết phải ghi rõ `Chưa thể tải...` và cách thử lại; không giả lập dữ liệu.

## Canonical event catalog baseline

Các event đã có trong business specification cần được giữ làm baseline: `ACCOUNT_SUSPENDED`, `ROLE_CHANGED`, `ASSESSMENT_REMINDER`, `ASSESSMENT_GRADED`, `SCORE_CHANGED_AFTER_REGRADE`, `COURSE_ADMIN_EDITED`, `FILE_REJECTED`, `SYSTEM_SECURITY_ALERT`. Các event khác trong inventory cần mapping hoặc được phê duyệt là domain extension, không tự đổi tên trong migration.

## Retry and idempotency invariant

- Every retryable mutation that fans out notifications must accept a stable UUID `X-Idempotency-Key`.
- The key is owned by the business operation and is persisted as the event key; it is not regenerated for a network retry.
- An exact replay returns the original outcome and must not create a second event, recipient row or success toast.
- Reusing a key with changed business data returns a conflict and performs no new fan-out.
- The UI disables the primary submit action while the request is in flight and retains the key for a user retry after a transient failure.

## Dismiss/read semantics

- Mark read là state transition idempotent và trả outcome ổn định.
- Dismiss public response giữ `status: dismissed` theo test/spec hiện hành cho đến khi có decision thay đổi contract.
- Persistence cleanup dùng `expires_at` theo canonical schema; không phát hành `deleted_at` nếu database không có field đó.
- Important/security records không được mất khỏi audit chỉ vì UI dismiss.

## Current shared modal contract (2026-10-05)

`UI.openModal` is the single shared modal owner. `UI.alert` accepts the existing caller order `UI.alert(title, message, type)`, escapes the message body and preserves line breaks; producers must not invert title and body or add a competing native alert for the same outcome. The contract has a Node regression test, while the seeded Browser replay did not expose the pending-appeal or score-scale trigger.

## Retry/idempotency standard addition (2026-10-06)

For Admin lesson flags, a client that may retry the same mutation must send a UUID X-Idempotency-Key. The server must persist that key on the business notification event, compare the complete normalized payload on reuse, and return the same logical outcome without re-emitting audit, in-app or email side effects. Reuse with different data or a different operation is 409 CONFLICT; a missing key retains the existing non-keyed compatibility path and is not evidence of retry safety. The response exposes idempotent_replay so the UI/API caller can distinguish first execution from replay.

## Durable-event visibility standard addition (2026-10-06)

The recipient list must not infer idempotency from presentation text. If two non-expired Notification rows reference different NotificationEvent records, both are visible even when title, body and target role match. Idempotency is an explicit producer contract using a stable key and payload comparison; any legacy coalescing policy must be named and tested separately rather than implemented as a global title/body heuristic.
## Generic event-key conflict standard (2026-10-06)

An event key is a semantic idempotency key, not merely a row lookup. Exact replay requires equal event type, actor, target and sanitized payload; any mismatch must return a conflict and must not silently reuse the old event. The same rule applies before fan-out or email dispatch.
## Seed idempotency standard addition (2026-10-06)

The demo seed must be safe to rerun on the target SQL Server fixture: existing logical identities are reused, no durable notification or audit side effect is duplicated, and all model counts remain unchanged. This standard applies to disposable verification; live data repair still requires explicit approval.

## Shared dispatch key standard addition (2026-10-06)

The shared `dispatch_notification()` boundary accepts an optional UUID `event_key` and forwards it to the semantic event-idempotency check. Producers must own and reuse that key for retryable business mutations; the helper must not invent a stable key from presentation text or silently claim retry safety for unkeyed callers.

## Keyed dispatch content standard addition (2026-10-06)

When a producer supplies `event_key`, the semantic idempotency contract includes the sanitized notification title, body, category, target role and email-forcing choice in addition to the business payload, target and event type. A changed copy is a conflict, not an exact retry. Unkeyed callers remain explicitly outside retry guarantees until their business operation supplies a stable identifier.

## Enrollment fan-out key standard addition (2026-10-06)

For enrollment notifications, the stable key is derived from the durable enrollment identity, canonical event type and recipient role. Instructor and Student fan-out rows must use different keys so one recipient retry cannot suppress or alias the other recipient's event.

## Password security key standard addition (2026-10-06)

## Course lifecycle key standard addition (2026-10-06)

Course lifecycle notifications must derive their stable key from the persisted lifecycle AuditEvent, the canonical audit action and the recipient user ID. The audit row must be flushed before fan-out so a retry boundary cannot depend on an unpersisted or presentation-derived value. Multi-recipient review fan-out must use a distinct recipient-scoped key for each reviewer.

## Course-owner reassignment key standard addition (2026-10-06)

An owner-reassignment notification must use the same durable transition identity but a distinct recipient-scoped key for the former and new owner. An unassigned destination produces no new-owner notification; no presentation text or course public ID alone is a sufficient retry key.

## Password-reset token key standard addition (2026-10-06)

Password-reset token completion is a password mutation for retry purposes. Its mandatory SECURITY_PASSWORD_CHANGED notification must use the post-mutation auth_version key, regardless of whether the mutation entered through a normal password form, an administrative set-password path or a consumed reset token.

## Account-suspension key standard addition (2026-10-06)

ACCOUNT_SUSPENDED is a post-auth-version security mutation. Its mandatory in-app and email fan-out must use a key derived from the durable user ID and the new auth_version, so a later suspension version cannot alias an earlier one.

For password mutation security notices, the stable key must include the durable user identity and post-mutation `auth_version`. This keeps retries of one committed mutation idempotent while preserving separate events for later password changes; mandatory email remains one outbox row per keyed event and recipient.

## Durable mutation producer standard addition (2026-10-06)

Role mutations must include the target user ID, post-mutation `auth_version` and mutation kind. Course and lesson review notices must include the persisted change-request or audit ID, event type and recipient ID. File rejection notices must include the persisted rejected revision ID and recipient ID. Presentation copy is not a substitute for any of these durable identities.

## Complete direct-producer standard check (2026-10-06)

Every direct `dispatch_notification()` call must now provide either an explicit deterministic `event_key` or a prebuilt semantically validated event. The AST inventory reports 34 explicit keys and one prebuilt event across 35 calls; zero direct calls remain without an idempotency identity. Runtime SQL, Browser and external delivery evidence are separate gates and remain required.

## N-168 verification checkpoint (2026-10-06)

The standard was exercised by the full verifier with disposable SQL Server databases: **1607 passed, 0 failed, 0 skipped**, including all four SQL Server opt-in cases. The standard is source- and regression-verified; Browser/CUA visual retry, external inbox delivery, file/quarantine and historical disposition remain unverified gates.

## N-169 delivery standard extension (2026-10-06)

Email notification correctness now includes a mandatory operational consumer: durable `email_deliveries` must be claimed through a deduplicated EMAIL background job, production must use configured SMTP or fail closed, and a pending row older than 15 minutes must make health `DEGRADED`. This prevents both silent backlog and false `SENT` results from a mock transport. Live activation still requires approved SMTP configuration.

## N-170 acceptance boundary (2026-10-06)

The standard was rechecked against the current Computer Use surface. `getState()` returned no apps/browsers and direct IAB creation returned `Browser is not available: iab`; consequently visual, keyboard, file-chooser and rapid-retry requirements are not marked PASS. The current SQL-enabled full verifier completed **1612 passed, 0 failed, 0 skipped**, but the overall audit remains PARTIAL until Browser and external-delivery gates are available.

## N-171 historical-data preservation rule (2026-10-06)

The live duplicate disposition rule is now evidence-backed: repeated presentation copy must not be treated as a duplicate without a stable business identity. Current SQL has zero repeated event keys, zero unlinked events, no repeated `change_request_id` groups, and legacy groups with missing or generic payload identity. Historical notification/event rows remain append-only until an owner-approved mapping and disposable repair rehearsal prove a safe disposition.

## N-172 envelope standard enforcement (2026-10-06)

Session/Web notification success responses now follow the same `success/data` standard already used by the REST notification blueprint. Legacy top-level aliases are explicitly compatibility-only and do not replace `data`. The correction is focused-test verified; non-notification API families and Browser visual acceptance remain outside this checkpoint.

## N-173 standard regression result (2026-10-06)

The complete post-patch verifier passed **1613 tests with 0 failures and 0 skips**, including the session notification envelope regression, 108 frontend tests and all SQL Server opt-in cases. Browser/CUA and external delivery remain operational acceptance gates, not automated-test claims.

## N-174 acceptance-scope decision (2026-10-06)

SMTP/inbox is explicitly out of scope for this acceptance cycle because it has not been deployed. The notification standard is therefore not being used to claim external email delivery. Browser/CUA interaction and file/quarantine UI behavior remain mandatory and unverified while no Browser surface is available.

## N-175 Browser standard evidence (2026-10-06)

The Browser run exercised the role-facing notification standard: Vietnamese login/logout/success/permission toasts rendered, unread state was visibly updated after mark-all-read, and Admin Operations presented a degraded operational state rather than a fabricated healthy queue. Legacy mixed-language records remain visible as historical content findings.

## N-176 file standard boundary (2026-10-06)

Clean file download passed through Browser Use. Unsafe-file denial cannot yet be classified as a UI-standard pass because no current PENDING/QUARANTINED row exists and Edge extension file-URL permission prevents setting the upload fixture; the rejected URL was blocked client-side before application response.

## N-177 Student notification standard evidence (2026-10-06)


Student UI correctly exposes category filters and an explicit zero-unread state, but the visible message catalog is not language-consistent: Vietnamese product messages appear beside English/mixed-language system text. The standard remains unmet for those historical messages until their producer and translation ownership are mapped.
## N-178 file-standard revalidation (2026-10-06)

The clean file standard passed for the Instructor course-image workflow: Browser chooser assignment, crop confirmation and success toast all rendered, and SQL Server recorded `ACTIVE` asset/revision state plus `FILE_VALIDATION=PASS` and `MALWARE=PASS`. The unsafe-file denial standard remains unverified because Browser blocked the rejected-file URL before the app response; this evidence does not claim a 403 or quarantine-screen pass.
## N-179 unsafe-file standard boundary (2026-10-06)

The unsafe-file standard remains **UNVERIFIED**. A second, course-scoped inline URL was blocked before the application could render a denial envelope, and the rejected asset is not attached to a Student-visible resource. No 403, quarantine card or unsafe-file success is inferred from this transport error.
## N-180 authenticated unsafe-file standard boundary (2026-10-06)

The authenticated Instructor route still cannot render the unsafe-file denial standard because Edge blocks it before the application response. This confirms the result is **UNVERIFIED**, not an authorization failure that can be counted as a pass.
## N-181 system-category standard evidence (2026-10-06)

The `Hệ thống` filter rendered a focused two-item result and the explicit zero-unread state, satisfying the structural category behavior. The content standard remains open because one visible message is legacy mixed-language text.
## N-182 assessment empty-state standard evidence (2026-10-06)

The `Khảo thí` filter satisfies the explicit empty/unknown-state behavior: it shows a clear message and keeps the unread count at zero. No conclusion is made about missing backend producers.
## N-183 course-category standard evidence (2026-10-06)

The `Khóa học` category filter rendered its 16-item result and retained the explicit zero-unread state. Category behavior passes structurally; the visible repeated and mixed historical content means the language/identity standard remains open.

## N-184 broadcast validation standard evidence (2026-10-06)

The Admin broadcast form satisfies the required-field standard for the two tested invalid states: an empty submission identifies the missing title, and a title-only submission identifies the missing body. Canceling the modal leaves the Admin page available and the SQL Server notification/outbox counts unchanged in the observed snapshot. No claim is made for valid broadcast delivery; SMTP/inbox is out of scope by owner decision.

## N-185 fail-closed file evidence boundary (2026-10-06)

The fail-closed standard cannot be marked Browser-passed from the current dataset: all seven rejected revisions are unattached to lessons/resources, and the direct download attempt is intercepted before the app can expose its denial response. No unsafe file is made visible, but a verified 403 or quarantine UI denial is still missing.

## N-186 fail-closed API standard evidence (2026-10-06)

The sampled rejected download satisfies the backend standard: authenticated access receives `403`, `success:false`, `FILE_INFECTED`, and a safe user-facing message without content bytes. The Browser/UI denial standard remains open because Edge blocks the request before the response can render.

## N-187 email acceptance scope (2026-10-06)

The notification standard treats external SMTP and inbox receipt as **scope-excluded** for this cycle because the deployment is not configured. No `SENT` or inbox claim is derived from pending outbox rows; any future release gate must provision an approved sink/provider separately.

## N-188 historical duplicate standard (2026-10-06)

Historical duplicate classification now requires a durable business identity or a documented one-to-one event-to-revision/request correlation before a repeated copy is classified as duplicate. Correlation is evidence for classification, not permission to mutate append-only history.

## N-189 quarantine-override acceptance standard (2026-10-06)

The Browser acceptance standard now records the empty-form guard as a scoped pass: a primary admin must provide the asset identity, justification and re-authentication secret before an override can be attempted. A successful release remains a separate gate and must prove fail-closed state transition plus append-only audit persistence.

## N-190 focused quarantine regression standard (2026-10-06)

The focused backend standard is met for the exercised guards: override-specific authorization/validation tests and the quarantined/infected fail-closed test passed. A credentialed live release is intentionally not inferred from these results.

## N-191 Browser console standard (2026-10-06)

For the inspected acceptance paths, the Browser console must remain free of application errors; that condition was observed. The Tailwind CDN production warning remains a non-gating hygiene observation.

## N-192 legacy identity standard (2026-10-06)

Recipient identity alone is insufficient for historical duplicate repair. A release-grade classification requires a durable business target or an approved external mapping; NULL correlation/actor fields and a generic action URL must remain unresolved evidence.

## N-194 Browser denial evidence standard (2026-10-06)

`ERR_BLOCKED_BY_CLIENT` is an environment result, not an application pass. A Browser fail-closed gate is accepted only when the app response/UI is observed, or when a documented Browser-provider limitation explicitly leaves the gate open.

## N-195 route-family evidence standard (2026-10-06)

Testing more than one file-response route can establish the scope of a Browser client block, but it still cannot substitute for an app-level response. Both tested routes remain environment-blocked and unverified at the UI denial layer.
## N-196 exact business-window recheck (2026-10-06)

A further read-only SQL Server check searched `course_change_requests` in the exact event windows for the 13 unresolved `LESSON_CHANGE_REQUEST` copies (2026-09-28 03:10:04-03:16:28 UTC) and the four unresolved `COURSE_CHANGE_APPROVED` copies (2026-09-28 05:44:15-05:44:22 UTC and 2026-09-29 02:09:31 UTC). It returned no rows in those windows. Current CS101 change-request rows exist at other times, but none can be safely joined to these notifications from the stored recipient-only target, NULL correlation/actor fields and generic action URLs. This is additional evidence for an owner-approved mapping/rehearsal hold; no append-only history was mutated. Final status remains **PARTIAL - not release-accepted**.
## N-197 Browser fail-closed resource-visibility proof (2026-10-06)

Using the enrolled Student Browser session, a temporary, explicitly labeled `lesson_resources` row `120002` was attached to published SEXGAY lesson `130025` and pointed at existing asset `3EB32DEA-150D-4724-B42C-2FEBB53BAD16`. SQL identified the asset as `PENDING` with current revision `REJECTED`, reason `Infected: ZIP-Embedded-Executable`. The real Student `Tài liệu` panel still rendered only the four ACTIVE files and exposed no link, preview or download CTA for the rejected resource. A direct Student-scoped URL was separately attempted and Edge returned `net::ERR_BLOCKED_BY_CLIENT` before an application response, so the UI omission is the verified Browser fail-closed result and the direct response remains environment-blocked. The temporary resource row was then deleted by exact ID and label; SQL verified the lesson returned to four resource links, the rejected asset remained `PENDING`, its revision remained `REJECTED`, and it had zero resource links. No file revision, quarantine state, notification row or audit record was mutated. Final status remains **PARTIAL - not release-accepted** because direct Browser response observation and historical owner-approved notification disposition remain open.
## N-198 acceptance checkpoint after temporary Browser fixture (2026-10-06)

The temporary Browser fixture proves the Student-facing file-visibility branch: a linked `PENDING/REJECTED` asset was omitted from the real Student resource panel, while the four `ACTIVE` files remained visible. Exact cleanup restored the lesson to four resource links and left the asset/revision unchanged. Therefore Student UI fail-closed visibility is **PASS for this sampled asset**; the direct download response remains **BLOCKED ENVIRONMENT / UNVERIFIED** because Edge intercepts the URL before the application response. SMTP/inbox remains **OUT OF SCOPE** by owner decision. Historical notification disposition remains open for the two unkeyed groups/17 rows, so the overall audit remains **PARTIAL - not release-accepted**.
## N-199 historical outbox identity recheck (2026-10-06)

Read-only SQL Server inspection found one `email_deliveries` row for each of the 17 unresolved notification events. Those rows preserve recipient email, template code, random dedupe UUID and `PENDING` status, but have NULL subject/body and no `course_change_request_id`, target resource or correlation field. This provides no additional safe business identity for historical repair. SMTP/inbox remains owner-authorized **OUT OF SCOPE**; no delivery was attempted and no outbox/history row was mutated. Final status remains **PARTIAL - not release-accepted**.
## N-243 dispatcher identity acceptance boundary (2026-10-06)

| Gate | Result | Evidence boundary |
|---|---|---|
| Every direct dispatcher call has an identity mechanism | PASS, static | 35 calls: 34 `event_key`, 1 prebuilt `event`, 0 missing, zero parse errors |
| Correct durable identity semantics and race convergence | UNVERIFIED | Static presence does not prove the key derivation or SQL concurrency behavior for every producer |

## N-242 producer-heavy service acceptance boundary (2026-10-06)

| Gate | Result | Evidence boundary |
|---|---|---|
| Authorization/notification/email/completion/application service regression | PASS, scoped | 64 passed, 0 skipped in the fresh producer-heavy unit group |
| All producer semantic/runtime coverage | UNVERIFIED | Fixture tests do not prove every callsite, role, retry/race or Browser/user-result chain |

## N-241 Admin lesson-flag acceptance boundary (2026-10-06)

| Gate | Result | Evidence boundary |
|---|---|---|
| Current Admin lesson-flag REST/Web contract | PASS, scoped | Dedicated current test group: 9 passed, 0 skipped |
| Historical RCA-040/RCA-027 as current defect | SUPERSEDED | Current source and focused tests no longer reproduce the described constructor/type-guard failure |

## N-240 fresh API/frontend acceptance boundary (2026-10-06)

| Gate | Result | Evidence boundary |
|---|---|---|
| Notification API/IDOR regression | PASS, scoped | 23 passed, 0 skipped in the fresh API plus IDOR command |
| Frontend notification/UI regression | PASS, scoped | 108 passed, 0 failed, 0 skipped, todo 0 in the full Node frontend suite |
| Full producer and Browser business flow | UNVERIFIED | These suites do not replace live producer-by-producer and file/quarantine Browser checks |

## N-239 Admin notification filter acceptance boundary (2026-10-06)

| Gate | Result | Evidence boundary |
|---|---|---|
| Admin `Tất cả` filter | PASS, scoped | Fresh Edge replay rendered 15 records |
| Admin category partition | PASS, scoped | `Khảo thí=1`, `Khóa học=11`, `Hệ thống=3`, `Chưa đọc=0`; no mutation |
| Admin producer completeness | UNVERIFIED | Existing persisted records were read; no new producer event was created |

## N-237 Admin notification acceptance boundary (2026-10-06)

| Gate | Result | Evidence boundary |
|---|---|---|
| Admin notification center renders persisted records | PASS, scoped | Fresh Edge replay showed 0 unread, Admin role label and 3 system/security records without mutation |
| Admin producer and broadcast semantics | UNVERIFIED | No new Admin notification was created in this read-only replay |

## N-238 Guest notification boundary (2026-10-06)

| Gate | Result | Evidence boundary |
|---|---|---|
| Guest protected notification route | PASS, scoped | Browser redirected `#/student/notifications` to `/auth`; no authenticated topbar control rendered |
| Guest API status and all protected notification paths | PARTIAL | API `401` is covered separately; this Browser replay covers one client route only |

## N-250 YouTube Browser/UI ownership checkpoint (2026-10-06)

| Gate | Result | Evidence boundary |
|---|---|---|
| Lesson Studio invalid-link validation | PASS, Browser scoped | Real Instructor UI showed Vietnamese validation toast and no saved mutation |
| Course-wide broken-video scan visible control | OPEN GAP | No control appeared in real course management; `scanCourseVideos` has no frontend caller |
| Producer notification ownership | PARTIAL | Service/API owner is present; visible UI owner or scheduler contract is not established |

## N-249 YouTube route/API runtime checkpoint (2026-10-06)

| Gate | Result | Evidence boundary |
|---|---|---|
| Unauthenticated scan route | PASS, disposable scope | `POST /instructor/courses/{public_id}/scan-videos` returned 401 |
| Authorized owner scan route | PASS, disposable scope | Instructor owner received 200, `success=true`, `broken_count=1` |
| Route replay durable convergence | PASS, disposable scope | One event and one notification remained after repeated route/service scans |
| Browser control and visible result | UNVERIFIED | No Browser click-through for this scan control in this probe |

## N-248 YouTube producer runtime checkpoint (2026-10-06)

| Gate | Result | Evidence boundary |
|---|---|---|
| Valid oEmbed branch | PASS, disposable service scope | Mocked valid response returned 0 broken reports and no notification |
| Network-error branch | PASS, disposable service scope | Mocked `network_error=true` returned 0 reports and no notification |
| Broken video owner notification | PASS, disposable service/DB scope | One event + one owner notification; target/recipient and `COURSE` category asserted |
| Exact retry convergence | PASS, disposable service/DB scope | Second identical scan preserved event/notification counts at 1/1 |
| Authenticated route/API/Browser result | UNVERIFIED | Probe called service directly; no live route/UI replay |

## N-247 YouTube producer standard checkpoint (2026-10-06)

| Gate | Result | Evidence boundary |
|---|---|---|
| YouTube broken-video producer exists with deterministic key | PASS, source-scoped | UUIDv5 includes course, lesson, video ID and instructor ID |
| Valid/broken/network-error scan behavior and notification result | UNVERIFIED | No current test file or live API/DB/Browser replay covers this producer |

## N-246 producer-key standard checkpoint (2026-10-06)

| Gate | Result | Evidence boundary |
|---|---|---|
| Direct producer key shape | PASS, static scoped | 34 explicit keys; all classified as durable-identity candidates; no random/clock/constant/unclassified expression |
| Prebuilt event path | PASS, scoped | One `event` path at `course_service.py:286`; construction semantics still require runtime proof |
| Complete semantic idempotency and recipient correctness | UNVERIFIED | Static shape does not prove business transition, role, retry race or user-visible result |

## N-245 Student Browser content/taxonomy checkpoint (2026-10-06)

| Gate | Result | Evidence boundary |
|---|---|---|
| Student filter counts and unread state | PASS, scoped | Browser rendered `Tất cả=13`, `Khảo thí=7`, `Khóa học=2`, `Hệ thống=4`, `Chưa đọc (0)` |
| Vietnamese copy quality and semantic usefulness | FAIL, sampled | Visible unaccented system copy and low-value seeded strings; sample is not a global count |
| Category/message taxonomy consistency | PARTIAL | `ĐIỂM SỐ` appears inside the `Khảo thí` result set; complete catalog ownership remains open |

## N-244 grading/regrade producer-service regression (2026-10-06)

| Gate | Result | Evidence boundary |
|---|---|---|
| Grading/regrade producer regression | PASS, scoped | `test_grading_service.py` + `test_regrade_service.py`: 25 passed, 0 failed, 0 skipped, exit 0 |
| Complete notification standard across all producers/roles/retries | UNVERIFIED | This group is fixture/service-side only; Browser file/quarantine and SMTP/inbox remain outside or open |

## N-200 stale identity/content recheck (2026-10-06)

The unresolved notification bodies do contain coarse labels: all 13 `LESSON_CHANGE_REQUEST` copies name CS101 and Lesson `Bài 1: Tổng quan về Kiến trúc Web & HTTP Protocol`, but none stores a change-request ID, durable target ID or correlation. The four `COURSE_CHANGE_APPROVED` copies name the same Lesson but their CTA points to course UUID `cf547469-d8b8-43ef-882c-721048826232`, which is absent from the current `courses` table; the current CS101 row has a different public UUID. Current CS101 change-request rows exist, including multiple historical candidates for the same lesson, but none matches the notification event windows. This confirms stale/missing business identity rather than an unresolved title-only query; no historical row was reassigned, deleted or merged. Final status remains **PARTIAL - not release-accepted**.

## N-251 frontend mechanism standard checkpoint (2026-10-06)

| Gate | Result | Evidence boundary |
|---|---|---|
| Shared toast invocation inventory | PASS, static | 383 invocations across 7 files; 214 quoted, 73 template, 96 dynamic |
| Non-toast message surfaces | PARTIAL | `UI.alert` 2, `UI.confirm` 30, `UI.prompt` 8 and direct `window.confirm` 1 require separate semantic ownership checks |
| Native/accessibility surface inventory | PASS, static | No native alert/prompt or `<dialog>`; 6 `aria-live` and 4 `role="alert"` attributes found |
| Complete message catalog/language/status mapping | UNVERIFIED | Static inventory does not connect every producer, HTTP outcome, role and rendered message |

SMTP/inbox delivery remains **OUT OF SCOPE** because no mail provider is deployed.
## N-252 producer execution standard checkpoint (2026-10-06)

| Gate | Result | Evidence boundary |
|---|---|---|
| Direct producer callsite execution | PASS, scoped | 35/35 `dispatch_notification()` callsites covered by selected tests/probes; 0 failed, 0 skipped |
| Rejection producer branches | PASS, disposable | Prerequisite rejection and rejected file revision each produced one durable event/notification with expected recipient/state |
| YouTube broken-video replay | PASS, disposable | Valid/network-error suppression, broken report, route 401/200 and exact one-event/one-notification replay passed |
| Complete semantic role/async/retry standard | UNVERIFIED | Line coverage does not prove every role, timeout/cancel/unmount, rapid retry or Browser rendering |
## N-253 Browser error-surface standard checkpoint (2026-10-06)

| Gate | Result | Evidence boundary |
|---|---|---|
| Invalid-login message owner | PASS, sampled | One inline `#auth-error-alert`; no duplicate toast observed |
| Invalid-login persistence | OBSERVED | Error remained visible after approximately 6.45 seconds; timeout policy is not defined by this sample |
| Dynamic error announcement semantics | OPEN | DOM lacks explicit `role` and `aria-live` |
## N-254 file-chooser standard checkpoint (2026-10-06)

| Gate | Result | Evidence boundary |
|---|---|---|
| Visible chooser control | PASS, sampled | Instructor Lesson Studio exposed the document chooser control |
| Supported filechooser event | BLOCKED ENVIRONMENT | No event before timeout; debugger detached |
| Upload/rejection/quarantine acceptance | UNVERIFIED | No file was selected or transmitted; no HTTP response was observable |
## N-255 producer role standard checkpoint (2026-10-06)

| Gate | Result | Evidence boundary |
|---|---|---|
| Producer identity presence | PASS, static/runtime-scoped | 34 explicit keys plus 1 prebuilt event; none missing both |
| Category inventory | PASS, static | COURSE 20, SECURITY 6, SYSTEM 8 and one dynamic category |
| Explicit role ownership | PARTIAL | 17 concrete target roles; 18 missing/`None` and require business-role verification |
| Complete role/multi-role recipient semantics | UNVERIFIED | The shared dispatcher permits unscoped delivery; per-producer recipient assertions remain incomplete |
## N-256 focused role/retry standard checkpoint (2026-10-06)

| Gate | Result | Evidence boundary |
|---|---|---|
| Keyed retry no fan-out duplicate | PASS, focused | Exact replay and changed-payload conflict tests passed |
| Multi-role recipient isolation | PASS, focused | Target-role and enrollment Student/Instructor tests passed |
| Recipient-scoped reassignment | PASS, focused | Old/new owner key assertions passed |
| Complete producer semantic standard | UNVERIFIED | Focused group covers representative paths only |
## N-257 historical-data disposition control (2026-10-06)

The standard now has a concrete approval boundary for the 17-row historical
case: identical title/body is insufficient to classify duplicate delivery;
event key, durable business target and owner approval are required before any
merge, delete or reassignment. The [approval packet](09_HISTORICAL_NOTIFICATION_APPROVAL_PACKET.md)
contains the read-only row inventory and minimum approval fields. SMTP/inbox is
**OUT OF SCOPE** for this cycle.
## N-258 Browser upload evidence rule (2026-10-06)

The second live chooser attempt again produced no `filechooser` event and no
selected file. The standard therefore continues to require a captured chooser,
known fixture assignment, application response and SQL cleanup before upload or
quarantine is marked passed. This attempt is **BLOCKED ENVIRONMENT /
UNVERIFIED**, not skipped.
## N-259 Browser content acceptance checkpoint (2026-10-06)

The live category check confirms that acceptance must inspect title, body,
reason, identity and language together: repeated copy with distinct reasons is
not automatically duplicate delivery, and an unaccented system message is a
catalog defect even when filtering works. The 16-card `Khóa học` and two-card
`Hệ thống` samples are direct evidence only, not global totals.
## N-260 role-scope standard clarification (2026-10-06)

The standard distinguishes recipient identity from role-view scope. A concrete
recipient prevents cross-user fan-out, but NULL `target_role` is still broad
within that account's role filters. Account-wide security/role notices may use
NULL intentionally; route-specific producers require an explicit role or a
tested account-wide contract plus a compatible CTA.
## N-261 role-filter acceptance failure (2026-10-06)

Role-filter acceptance must reject a NULL target-role row whose CTA is scoped to
another active role. Live evidence showed an Admin review CTA in all three
role-filter responses for one multi-role account. Recipient ownership remained
correct, but role-view/CTA compatibility failed.
## N-262 schema source-of-truth requirement (2026-10-06)

The notification standard must document every runtime role-scope field and its
constraints. `target_role`, `ix_notifications_user_role_unread` and
`ck_notifications_target_role` currently exist in migration/model/SQL Server
but not in the canonical data dictionary. Contract review is incomplete until
the documentation is reconciled with the applied migration.
## N-263 test-oracle requirement (2026-10-06)

Passing role isolation tests are insufficient unless the assertion also checks
CTA route compatibility. A NULL role may be global only for account-wide
messages; route-specific notifications need an explicit role or a tested
route-ownership contract.
## N-264 isolation standard result (2026-10-06)

The sampled cross-user boundary passes: a Student account cannot see the Admin
review CTA, and cannot request role filters it does not hold. This pass does not
close the separate same-user multi-role CTA requirement.
## N-265 route-compatibility acceptance rule (2026-10-06)

An accepted notification CTA must be compatible with the active role view before
navigation. A route guard warning/redirect is a containment result, not a pass
for notification correctness. Fresh Edge showed the Instructor-only warning on
the Admin review target; acceptance therefore remains open until the producer,
role filter and CTA contract agree for both single-role and multi-role accounts.
