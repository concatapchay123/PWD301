# 02_NOTIFICATION_INVENTORY

## Current full-field lesson-flag inventory (2026-10-05)

These rows supersede source-only N-032/N-033 for the specifically executed branches. `FLAG-WEB` means POST `/admin/courses/{course_uuid}/lessons/{lesson_uuid}/flag`; `FLAG-REST` means POST `/api/admin/courses/{course_uuid}/lessons/{lesson_uuid}/flag`. Exact public IDs, bodies, correlation IDs, SQL snapshots and the nonzero probe exit are retained in [flag-runtime-evidence.md](flag-runtime-evidence.md). No product remediation was performed in this checkpoint.

| ID | Module | Page | Role | User Action | Trigger | Condition | FE Function | API | HTTP Method | BE Handler | Business Rule | Success Condition | Error Condition | Current Message | Language | Notification Type | Duration | Expected Message | Severity | Root Cause | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| N-125 | Course review / local validation | Admin CS301 review | Admin | Confirm an empty flag reason | Prompt confirm click | Reason length 0 | AdminView.renderCourseReviewPage → UI.prompt | None dispatched by prompt | N/A | Not reached | Require at least 5 trimmed characters | Prompt stays open; no durable write | Input missing | Nội dung bắt buộc tối thiểu 5 ký tự. | VI | VALIDATION / warning toast | 3500 ms coded; not timed | Enter a reason of at least 5 characters, beside the input | P2 presentation; rejection correct | Shared prompt uses toast rather than inline field error | BROWSER + SQL rejection PASS; inline UX gap |
| N-126 | Course review / flag persistence | Admin CS301 review; REST | Admin → Instructor2 intended recipient | Confirm a valid lesson flag | Await flagLessonContent; REST POST | Owned published lesson, authorized Admin, valid reason | AdminView.renderCourseReviewPage → ApiClient.flagLessonContent → catch → UI.showToast | FLAG-WEB; FLAG-REST | POST | flag_course_lesson; api_flag_course_lesson | Persist flag and required audit before reporting completion; notify actual owner | Durable lesson flag/audit and owner notification match response | Audit constructor fails before commit | An internal server error occurred. Please contact support. | EN | SYSTEM / error toast | 3500 ms coded; not timed | Không thể gắn cờ bài học. Vui lòng thử lại sau. | P1 | RCA-040 invalid AuditEvent constructor | BROWSER + REST + SQL CONFIRMED FAIL; 0 durable flag/audit/event/notice |
| N-127 | Course review / JSON validation | REST only | Admin | Send JSON string | HTTP probe | Body is a nonempty string | N/A: probe, no Browser trigger | FLAG-REST | POST | api_flag_course_lesson → payload.get | Reject wrong object type with 4xx and no writes | Safe 400 validation envelope | str has no get | An internal server error occurred. Please contact support. | EN | SYSTEM response; no UI observed | N/A | Dữ liệu yêu cầu không hợp lệ. | P1 | RCA-027 continuing type-guard gap | HTTP + SQL CONFIRMED FAIL: 500, unchanged DB |
| N-128 | Course review / JSON validation | REST only | Admin | Send JSON nonempty list | HTTP probe | Body is [invalid] rather than an object | N/A: probe, no Browser trigger | FLAG-REST | POST | api_flag_course_lesson → payload.get | Reject wrong object type with 4xx and no writes | Safe 400 validation envelope | list has no get | An internal server error occurred. Please contact support. | EN | SYSTEM response; no UI observed | N/A | Dữ liệu yêu cầu không hợp lệ. | P1 | RCA-027 continuing type-guard gap | HTTP + SQL CONFIRMED FAIL: 500, unchanged DB |
| N-129 | Course review / authentication | REST only | Guest | POST a valid flag without a token | HTTP probe | No Authorization header | N/A: probe | FLAG-REST | POST | jwt_required before api_flag_course_lesson | Unauthenticated writes prohibited | 401 and no mutation | Missing token | Missing Authorization header with Bearer token. | EN | PERMISSION response; no UI observed | N/A | Vui lòng đăng nhập để tiếp tục. | P2 copy; boundary correct | Existing auth copy / RCA-003 | HTTP + SQL boundary PASS; Browser mapping NOT RUN |
| N-130 | Course review / authorization | REST only | Instructor2 | Attempt Admin flag action | HTTP probe | JWT has no ADMIN role | N/A: probe | FLAG-REST | POST | admin_required before api_flag_course_lesson | Instructor cannot perform Admin moderation | 403 and no mutation | Insufficient role | Access denied: insufficient role permissions. | EN | PERMISSION response; no UI observed | N/A | Bạn không có quyền gắn cờ nội dung khóa học. | P2 copy; boundary correct | Existing permission copy / RCA-013 | HTTP + SQL boundary PASS; Sub-Admin matrix N-136–N-139 |
| N-131 | Course review / authorization | REST only | Student4 | Attempt Admin flag action | HTTP probe | JWT has only STUDENT role | N/A: probe | FLAG-REST | POST | admin_required before api_flag_course_lesson | Student cannot perform Admin moderation | 403 and no mutation | Insufficient role | Access denied: insufficient role permissions. | EN | PERMISSION response; no UI observed | N/A | Bạn không có quyền gắn cờ nội dung khóa học. | P2 copy; boundary correct | Existing permission copy / RCA-013 | HTTP + SQL boundary PASS; Browser mapping NOT RUN |
| N-132 | Course review / server validation | REST only | Admin | Submit empty reason directly | HTTP probe | Reason length 0 | N/A: probe; N-125 is separate Browser case | FLAG-REST | POST | api_flag_course_lesson reason validation | Server must enforce reason independently of FE | 400 and no mutation | Empty reason | Lý do gắn cờ bắt buộc tối thiểu 5 ký tự. | VI | VALIDATION response | N/A | Same Vietnamese validation explanation | None for tested rejection | Correct server guard | HTTP + SQL PASS for empty reason |
| N-133 | Course review / server validation | REST only | Admin | Submit reason abcd | HTTP probe | Trimmed length 4 | N/A: probe | FLAG-REST | POST | api_flag_course_lesson reason validation | Minimum 5 characters | 400 and no mutation | Below minimum | Lý do gắn cờ bắt buộc tối thiểu 5 ký tự. | VI | VALIDATION response | N/A | Same Vietnamese validation explanation | None for tested rejection | Correct server guard | HTTP + SQL PASS; exact length 5 covered by N-135 |
| N-134 | Course review / object existence | REST only | Admin | Flag a nonexistent public lesson | HTTP probe | Known course; nonexistent lesson UUID | N/A: probe | FLAG-REST | POST | _resolve_lesson then api_flag_course_lesson guard | Resource must exist within the selected course | 404 and no mutation | Missing lesson | Bài học không tồn tại trong khóa học này. | VI | ERROR response | N/A | Same resource-safe error | None for tested rejection | Correct existence guard | HTTP + SQL PASS; cross-course mismatch NOT RUN |
| N-135 | Course review / server boundary | REST only | Admin | Submit exact five-character reason | HTTP probe | Reason is exactly `abcde` | N/A: probe | FLAG-REST | POST | api_flag_course_lesson → AuditEvent construction | Minimum is five trimmed characters; valid input must persist before success | 200 plus durable flag/audit/event/notice | Internal constructor failure | An internal server error occurred. Please contact support. | EN | SYSTEM response; no UI success | N/A | Truthful success only after durable moderation and owner notice | P1 | RCA-040 | HTTP + SQL CONFIRMED FAIL; exact boundary executed |
| N-136 | Admin sub-role notification / authorization | Admin governance / courses | Admin course-review sub-role | Login, open own ROLE_CHANGED notice, follow CTA, flag lesson | Browser notification center + REST replay | `ADMIN_COURSE_REVIEW`, one assigned role audit and notice | Auth login → NotificationCenter detail → CTA → AdminView.renderCourseReviewPage | `/api/notifications?role=ADMIN`; FLAG-REST | GET / POST | assign_role_to_user; list_user_notifications; api_flag_course_lesson | Role notice durable and CTA scoped; only course-review may flag | One read own notice, correct courses route, flag authorized | Valid exact-5 flag returns 500 | `Admin phụ: Kiểm duyệt Khóa học & Bài giảng`; then English 500 | VI / EN error | ROLE_CHANGED; SYSTEM error on failed flag | N/A | Readable role notice and truthful moderation result | P1 | RCA-040 for allowed flag path | BROWSER + SQL + REST: notice/CTA PASS; flag FAIL |
| N-137 | Admin sub-role notification / authorization | Admin governance / applications | Admin instructor-review sub-role | Login, open own ROLE_CHANGED notice, follow CTA, attempt flag | Browser notification center + REST replay | `ADMIN_INSTRUCTOR_REVIEW`, one assigned role audit and notice | Auth login → NotificationCenter detail → CTA → governance applications | `/api/notifications?role=ADMIN`; FLAG-REST | GET / POST | assign_role_to_user; list_user_notifications; admin permission guard | Role notice/CTA scoped; instructor-review cannot course-flag | One read own notice, applications route, flag denied | 403 and no moderation mutation | `Admin phụ: Xét duyệt Giảng viên`; permission denial from API | VI / EN response | ROLE_CHANGED; PERMISSION response | N/A | Keep sub-role boundary explicit | P2 | Expected permission boundary | BROWSER + SQL notice/CTA PASS; REST 403 PASS |
| N-138 | Admin sub-role notification / authorization | Admin governance / reassignment | Admin teaching-assignment sub-role | Login, open own ROLE_CHANGED notice, follow CTA, attempt flag | Browser notification center + REST replay | `ADMIN_TEACHING_ASSIGNMENT`, one assigned role audit and notice | Auth login → NotificationCenter detail → CTA → governance reassign | `/api/notifications?role=ADMIN`; FLAG-REST | GET / POST | assign_role_to_user; list_user_notifications; admin permission guard | Role notice/CTA scoped; teaching-assignment cannot course-flag | One read own notice, reassign route, flag denied | 403 and no moderation mutation | `Admin phụ: Phân công Giảng dạy`; permission denial from API | VI / EN response | ROLE_CHANGED; PERMISSION response | N/A | Keep sub-role boundary explicit | P2 | Expected permission boundary | BROWSER + SQL notice/CTA PASS; REST 403 PASS |
| N-139 | Admin sub-role notification / authorization | Admin operations | Admin system-monitoring sub-role | Login, open own ROLE_CHANGED notice, follow CTA, attempt flag | Browser notification center + REST replay | `ADMIN_SYSTEM_MONITORING`, one assigned role audit and notice | Auth login → NotificationCenter detail → CTA → AdminView.operations | `/api/notifications?role=ADMIN`; FLAG-REST | GET / POST | assign_role_to_user; list_user_notifications; admin permission guard | Role notice/CTA scoped; system-monitoring cannot course-flag | One read own notice, operations route, flag denied | 403 and no moderation mutation | `Admin phụ: Giám sát Hệ thống & Vận hành`; permission denial from API | VI / EN response | ROLE_CHANGED; PERMISSION response | N/A | Keep sub-role boundary explicit | P2 | Expected permission boundary | BROWSER + SQL notice/CTA PASS; REST 403 PASS |
| N-140 | Course review / flag persistence post-fix | REST only | Admin → Instructor2 | Confirm a valid lesson flag after remediation | HTTP probe | Owned published lesson, valid object/reason | N/A: probe | FLAG-REST | POST | api_flag_course_lesson → flag_lesson_content | Persist lesson flag, canonical audit and owner notice atomically | 200 with durable flag/audit/event/notice | None in executed case | Đã gắn cờ vi phạm nội dung ... và gửi thông báo cho giảng viên thành công. | VI | COURSE_CONTENT_FLAGGED | N/A | Success only after all durable writes | P1 | RCA-040 corrected; F-024 implemented | SQL REST PASS; 10/10 probe cases, 0 skipped |
| N-141 | Course review / Browser persistence post-fix | Admin CS301 review | Admin → Instructor2 | Confirm exact five-character lesson flag | Visible Browser flow | Exact reason `abcde`, authorized published lesson | AdminView.renderCourseReviewPage → ApiClient.flagLessonContent → UI.showToast | FLAG-WEB | POST | flag_course_lesson → flag_lesson_content | Same atomic durable outcome as REST | Success toast plus SQL flag/audit/event/notice | None in executed case | Đã gắn cờ vi phạm bài học ... và gửi thông báo tới giảng viên. | VI | COURSE_CONTENT_FLAGGED | 3500 ms coded; observed | Same Vietnamese success copy, no fabricated success | P1 | RCA-040 corrected; F-024 implemented | BROWSER + SQL PASS |
| N-142 | Course review / JSON validation post-fix | REST and web guard | Admin | Send JSON string/list | HTTP probe; web guard covered by regression | Payload is not an object | N/A: validation boundary | FLAG-REST; FLAG-WEB | POST | payload type guard before `flag_lesson_content` | Reject malformed body without touching lesson/audit/notice | 400 VALIDATION_ERROR and unchanged SQL | Wrong JSON type | Dữ liệu yêu cầu không hợp lệ. | VI | VALIDATION response | N/A | Stable 4xx safe error | P1 | RCA-027 corrected; F-025 implemented | REST + web regression PASS; 0 skipped |
| N-143 | Admin sub-role post-fix authorization | Governance / operations | Four Admin sub-roles | List own role notice, then flag or deny by scope | Fresh REST replay plus earlier Browser CTA | One role notice each; course-review allowed, others denied | NotificationCenter/CTA evidence plus REST permission guard | `/api/notifications?role=ADMIN`; FLAG-REST | GET / POST | assign_role_to_user; list_user_notifications; flag_lesson_content; permission guard | Preserve role-scoped notice and moderation permission boundaries | 8 checks all expected; 200/403 as scoped; rejected paths unchanged | None in executed boundary | Role-specific ROLE_CHANGED body; success/permission messages | VI | ROLE_CHANGED; COURSE_CONTENT_FLAGGED; PERMISSION | N/A | No escalation or false success | P1/P2 | RCA-041 dependent path corrected | REST + SQL PASS; Browser notice/CTA evidence retained |

### Additional required fields

| ID | File Frontend | Line / Function | File Backend | API response thực tế | Notification hiện tại | Notification mong muốn | Duplicate? | Hard-code? | Message owner | Need next action? | User next action |
|---|---|---|---|---|---|---|---|---|---|---|---|
| N-125 | frontend/assets/js/views/admin.js; ui.js | admin:3207–3220; UI.prompt:449–450 | Not reached | No request from the rejected prompt; SQL unchanged | Vietnamese warning toast; dialog retained | Inline reason error, retain input | None observed; rapid click NOT RUN | Yes, shared prompt template | FE UI.prompt | Yes | Enter ≥5 trimmed characters |
| N-126 | frontend/assets/js/views/admin.js; api.js; ui.js | admin:3223–3227; flagLessonContent:915; showToast:54 | src/pwd301/blueprints/admin/routes.py; api_admin/routes.py; models/notification_audit.py | Web/REST 500 INTERNAL_ERROR, English message, correlation ID, no success/data | One English error toast in Browser; no owner notice persisted | Vietnamese contextual error until persistence works; only then truthful success + owner notice | No duplicate in sampled single click; retries NOT RUN | BE error string and FE fallback/success are coded | BE owns error text; page catch owns this toast | Yes | Retry only after correction; support can correlate error without exposing internals |
| N-127 | N/A: HTTP probe | grading-runtime-probe.py flag_probe | src/pwd301/blueprints/api_admin/routes.py:1272 | 500 INTERNAL_ERROR; correlation 97d6c93007914defa56c6cad6df7e4b4 | HTTP error only; no Browser render observed | 400 VALIDATION_ERROR; no state change | No event/notice persisted | Yes, BE generic error | BE exception handler | Yes | Send a JSON object |
| N-128 | N/A: HTTP probe | grading-runtime-probe.py flag_probe | src/pwd301/blueprints/api_admin/routes.py:1272 | 500 INTERNAL_ERROR; correlation 2fe665f758df429da5b4bc01d38bbe7b | HTTP error only; no Browser render observed | 400 VALIDATION_ERROR; no state change | No event/notice persisted | Yes, BE generic error | BE exception handler | Yes | Send a JSON object |
| N-129 | N/A: HTTP probe | grading-runtime-probe.py flag_probe | services/jwt_auth_service.py; api_admin/routes.py | 401 UNAUTHORIZED; exact body in evidence | HTTP error only | Vietnamese login guidance in UI | No state/event change | Yes | BE auth guard; UI owner NOT RUN | Yes | Sign in normally |
| N-130 | N/A: HTTP probe | grading-runtime-probe.py flag_probe | services/authorization_service.py; api_admin/routes.py | 403 FORBIDDEN; exact body in evidence | HTTP error only | Vietnamese permission guidance | No state/event change | Yes | BE role guard; UI owner NOT RUN | No within this role | Use allowed Instructor workflow; no role bypass |
| N-131 | N/A: HTTP probe | grading-runtime-probe.py flag_probe | services/authorization_service.py; api_admin/routes.py | 403 FORBIDDEN; exact body in evidence | HTTP error only | Vietnamese permission guidance | No state/event change | Yes | BE role guard; UI owner NOT RUN | No within this role | Use allowed Student workflow; no role bypass |
| N-132 | N/A: HTTP probe | grading-runtime-probe.py flag_probe | api_admin/routes.py:1276–1277 | 400 VALIDATION_ERROR, field_errors empty | HTTP error only | Same server rejection; UI inline mapping separately assessed | No state/event change | Yes | BE validation guard | Yes | Provide a reason |
| N-133 | N/A: HTTP probe | grading-runtime-probe.py flag_probe | api_admin/routes.py:1276–1277 | 400 VALIDATION_ERROR, field_errors empty | HTTP error only | Same server rejection | No state/event change | Yes | BE validation guard | Yes | Use ≥5 trimmed characters |
| N-134 | N/A: HTTP probe | grading-runtime-probe.py flag_probe | api_admin/routes.py:1266–1269 | 404 RESOURCE_NOT_FOUND, field_errors empty | HTTP error only | Same resource-safe rejection | No state/event change | Yes | BE resource guard | Yes | Reload current course contents; do not guess IDs |
| N-135 | N/A: HTTP probe | grading-runtime-probe.py flag_probe | api_admin/routes.py:1276–1277; audit construction | 500 INTERNAL_ERROR, correlation `d511260d59a44a2d955a1b97987a2800` | HTTP error only | 200 only after durable state and notice | No event/notice persisted | No | BE route/model contract | Yes | Repair AuditEvent construction and replay |
| N-136 | auth.js; notification center; admin.js | login, detail, CTA, flag prompt | auth/notifications; api_admin/routes.py | GET 200; one own ROLE_CHANGED, read true; flag 500 | Role-specific body and correct courses CTA; error toast after flag | Durable notice and truthful flag result | No duplicate observed; rapid repeat NOT RUN | Role assignment body service-generated | BE role/notification service; FE CTA | Yes | Repair valid moderation path |
| N-137 | auth.js; notification center; admin.js | login, detail, CTA | auth/notifications; api_admin/routes.py | GET 200; one own ROLE_CHANGED, read true; flag 403 | Role-specific body and applications CTA | Same plus explicit scope denial | No duplicate observed; rapid repeat NOT RUN | Role assignment body service-generated | BE role/permission guard | No for tested boundary | Keep role scope regression test |
| N-138 | auth.js; notification center; admin.js | login, detail, CTA | auth/notifications; api_admin/routes.py | GET 200; one own ROLE_CHANGED, read true; flag 403 | Role-specific body and reassign CTA | Same plus explicit scope denial | No duplicate observed; rapid repeat NOT RUN | Role assignment body service-generated | BE role/permission guard | No for tested boundary | Keep role scope regression test |
| N-139 | auth.js; notification center; admin.js | login, detail, CTA | auth/notifications; api_admin/routes.py | GET 200; one own ROLE_CHANGED, read true; flag 403 | Role-specific body and operations CTA | Same plus explicit scope denial | No duplicate observed; rapid repeat NOT RUN | Role assignment body service-generated | BE role/permission guard | No for tested boundary | Keep role scope regression test |
| N-140 | admin.js; api.js | Admin review → REST flag | api_admin/routes.py; course_service.py | 200 success with durable SQL correlation | Owner receives one in-app event/notice after atomic commit | Notification after durable moderation | Two success calls create two events; idempotency not yet proven | No new hard-code; canonical service | BE service owns transaction | Yes | Add duplicate/retry proof |
| N-141 | admin.js; api.js; ui.js | Prompt → Browser flag | admin/routes.py; course_service.py | 200 success toast; SQL one flag/audit/event/notice | Vietnamese success toast visible | Same after durable commit | One Browser click sampled; rapid repeat NOT RUN | UI copy remains page-owned | BE status + FE toast | Yes | Verify repeat behavior |
| N-142 | N/A plus admin.js | malformed REST/web body | api_admin/routes.py; admin/routes.py | 400 VALIDATION_ERROR; SQL unchanged | No notification; Browser mapping not separately rerun for malformed body | Safe local validation message | No event/notice persisted | No | BE validation guard | No for tested boundary | Keep both-surface regression |
| N-143 | auth.js; notification center; admin.js | sub-admin login/detail/CTA and flag scope | user_service.py; notification_service.py; admin permission routes | Notice list 200; allowed flag 200; three denied 403 | Role-specific bodies; Browser CTA routes from earlier continuation | Durable role notice and scoped action result | One per role in fresh fixture; rapid repeat NOT RUN | Role service generates notice | BE role service + FE CTA | Yes | Complete duplicate/outbound delivery coverage |

Inventory now has **143 distinct case IDs**, not 143 uniquely emitted durable notifications. These nineteen new rows have all 22 core and 11 additional requested fields; older rows retain their original evidence and are not falsely upgraded to full-field/runtime coverage. Remaining inventory/schema completeness is still an acceptance gate. The post-fix flag reproducer is 10 REST cases / 10 matching / 0 failed expectations / 0 skipped; the post-fix sub-admin probe is 8 checks / 0 failed expectations / 0 skipped. Historical pre-fix failures remain preserved in N-126–N-139 and the runtime evidence.

## Checkpoint kiểm thử không skip và an toàn môi trường (2026-10-05)

Checkpoint này có ưu tiên hơn các số liệu 1572/1578 và các trạng thái lịch sử bên dưới. Lượt chạy ban đầu có 1576 passed, 2 failed, 0 skipped; hai test upload tài nguyên và lease bài thi trả 503. Chạy riêng cho 2 passed; chạy lại toàn nhóm API trước sửa fixture cho 375 passed. Probe có restore marker trên thư mục audit riêng tái hiện đúng cả hai phản hồi MAINTENANCE_MODE_ACTIVE/503. Việc nhóm test dùng chung storage/quarantine/backups với workspace là lỗi cô lập đã được chứng minh; không quy kết chắc chắn nguyên nhân của lượt lỗi ban đầu khi chưa lưu response của lượt đó.

Fixture app nay dùng ba thư mục con riêng trong tmp_path. Regression mới thất bại với các root E:/PWD301/storage, quarantine, backups trước sửa. Sau sửa, probe vẫn giữ marker bên ngoài và 27 test upload/lease/backup/restore/maintenance đạt; không tắt maintenance hay fail-closed. Marker probe đã xóa. Test mới dùng nhầm một route không tồn tại lúc đầu; lỗi harness 404 đó đã sửa, không tính là lỗi sản phẩm.

Cô lập filesystem lộ thêm lỗi rescan: kiểm tra substring “infected” trên toàn đường dẫn nhầm thư mục cha với vùng chứa tệp nhiễm. Regression hiện hữu thất bại hai lần trước sửa; nay so sánh parent đã resolve với get_file_infected_root(), kiểm tra tệp được chuyển, key infected/hash và Student vẫn bị từ chối 403. Focused stress/file/isolation: 27 passed. Lượt split cuối sau sửa cho **1579 passed, 0 failed, 0 skipped**, khớp **1579 tests collected**: root298 + unit632 + API375 + security233 + concurrency13 + E2E12 + integration16. Frontend độc lập: **101 passed, 0 failed, 0 skipped**. Không cộng các lượt focused trùng vào tổng. Đây là kết quả các nhóm chạy đủ, không phải một aggregate verifier được tuyên bố pass; lượt aggregate lịch sử bị stall vẫn không được tính.

SQL-gated integration hiện tại: 16 passed, 0 failed, 0 skipped, gồm migration, ROWVERSION race và hai loại revision trên SQL Server thật. Hai DB migration/race tạm đã xóa, remaining=0. Browser Student4 đã đăng xuất về form login; server audit 5105 dừng; DB grading tạm cũng đã xóa, remaining=0. Không migrate/restart DB/runtime chính; fixture có thể dựng lại bằng prepare.

Audit notification vẫn PARTIAL, không phải release sign-off. Những đoạn dưới nói “chưa sửa”, “pending replay”, “1572 current” là snapshot lịch sử, không được dùng thay checkpoint mới.

## Latest grading notification evidence (2026-10-05)

| ID | Workflow / role | Trigger and persistence | Actual / expected | Status |
|---|---|---|---|---|
| N-121 | Instructor2 manual grade → Student4 | POST /api/attempts/<attempt>/grades/<essay>; pending hidden result → RELEASED 18/30; one durable ASSESSMENT_GRADED row | Vietnamese first-release message with 18/30; unchanged 18 retry keeps one notice; Browser detail CTA opens the correct attempt result | CURRENT SQL/HTTP/BROWSER PASS; grading UI capability remains RCA-020 |
| N-122 | Correction/regrade job → Student4 | POST /api/assessments/<assessment>/regrade; completed one-item job, history 18→28; SCORE_CHANGED_AFTER_REGRADE row | Vietnamese 18→28/30 message and attempt CTA; duplicate request returns same job and identical overall history, with exactly two grading notices total | CURRENT SQL/HTTP/BROWSER PASS after worker notifier fix |
| N-123 | Instructor used-question correction error | create_question_revision → SQL Server CHECK 547, then immutable-child trigger 51007; old data retained by rollback | No success should be reported when persistence fails; migration widened to canonical enum and service builds children before activation | SQL SERVICE RED/GREEN; no HTTP/browser error text is inferred from this service probe |
| N-124 | Student result detail after grade notice CTA | Historical Browser replay showed 28/30 and 18/20, but `AFTER_CLOSE` intentionally omitted the answer text from the Student payload; the renderer fell back to “Không trả lời” | A hidden answer must be labeled as hidden by exam policy, while a genuinely empty visible answer may say “Không trả lời”; no answer or choice data may be leaked before policy release | PRE-FIX CONFIRMED; source correction GREEN; post-fix Browser replay pending because the CUA Browser binding is currently unavailable |

N-001/N-002/N-109 source-only labels below are historical discovery snapshots. N-121/N-122 supersede them for the freshly emitted events only. Inventory now contains 124 distinct IDs; static-only producer coverage and incomplete required-field coverage remain explicit audit limitations, not passes.

## Current continuation correction — enrollment notification transaction (2026-10-05)

| ID | Surface / workflow | Current evidence | Status |
|---|---|---|---|
| N-112 | Enrollment notification persistence with the enrollment commit | A new regression first failed after `enroll_student()` returned ACTIVE and the session was closed: `0` persisted `Notification` rows were found for the two `STUDENT_ENROLLED` events. The producer now dispatches both recipient notifications before the service's final commit, so enrollment and notification rows commit together. Focused `tests/unit/test_enrollment_service.py` now reports `20 passed, 0 failed`; completed split pytest verification reports `1572 passed, 0 failed, 0 skipped` across all collected groups. | SOURCE FIX / FOCUSED + SPLIT VERIFICATION; historical live OPS401 rows still require a fresh live replay/correlation |

| N-113 | Live Instructor submit → Admin approve → owner notification | Instructor submitted CS201 from the real course-management page and saw `Đã gửi yêu cầu xét duyệt thành công`. A fresh Admin session showed `1 Khóa học chờ duyệt`; Browser approval returned `Đã duyệt khóa học`. The owner Instructor session then showed `Khóa học CS201 đã được phê duyệt`. Direct SQL Server correlation showed course `CS201` status `APPROVED`, `approved_by_user_id=1`, `COURSE_APPROVED` event `140006`, and notification `150079` to `instructor1@pwd301.local`. | CONFIRMED LIVE BROWSER + SQL SERVER / APPROVE PATH PASS; request-edit/reject owner correlation remains separate |

| N-114 | Historical live staged course-change rejection → owner notification (pre-fix) | Instructor1 edited the approved CS201 lesson, submitted change request `#60002`; Admin opened the real review page, entered the reason `Vui lòng bổ sung ví dụ minh họa trước khi áp dụng.`, and completed `Từ Chối Bản Sửa`; Instructor1 then saw the pre-fix title `Đợt cập nhật khóa học #70014 cần chỉnh sửa lại`. SQL Server returned request `60002` as `REJECTED`, reviewer `1`, event `140009` (`COURSE_CHANGE_REJECTED`) and linked notification `150082` to `instructor1@pwd301.local`. | HISTORICAL BROWSER + SQL SERVER EVIDENCE / PRE-FIX |

| N-115 | Fresh live enrollment recipient correlation and CTA | Student4 enrolled in DSA201 through the real catalog and saw the success state/notification; opening the Student notification detail and `Mở Trang Liên Quan` landed on `#/student/courses/detail?id=da4d939c-4ba9-46f7-8b53-972cf76a7989`. Instructor2 dashboard showed 3 students and the owner notification `Học viên mới tham gia khóa học`; its detail CTA landed on `#/instructor/courses/manage?id=da4d939c-4ba9-46f7-8b53-972cf76a7989`. SQL Server found ACTIVE enrollment `110003`, events `140010/140011`, and linked notifications `150083` (Instructor2) and `150084` (Student4), with matching role-specific SPA action URLs. | CONFIRMED LIVE BROWSER + SQL SERVER / RECIPIENT + CTA PASS; historical OPS401 orphan rows remain a repair gap |

| N-116 | Historical live course-change rejection CTA technical-ID leakage | Request `#60003` rejection produced the pre-fix Browser notification title `Đợt cập nhật khóa học #70014 cần chỉnh sửa lại`; SQL Server event `140014` payload and action URL also used internal course ID `70014`, even though course `CS201` has public UUID `06a1a28d-667a-4d31-b5c9-edefc2885d91`. Clicking `Xem Khóa Học` still opened the correct CS201 management page because route resolution accepted the internal ID. | HISTORICAL CONFIRMED BROWSER + SQL SERVER / FIXED IN CURRENT WORKTREE |

| N-117 | Current live course-change rejection CTA after public-ID fix | Request `#60004` was resubmitted and rejected through the real Admin Browser review page. Instructor1 saw `Đợt cập nhật khóa học CS201 cần chỉnh sửa lại` with the exact reason; the detail CTA opened `#/instructor/courses/manage?id=06a1a28d-667a-4d31-b5c9-edefc2885d91`. SQL Server returned `REJECTED`, event `140017`, notification `150090`, `course_id=06a1a28d-667a-4d31-b5c9-edefc2885d91` and the same action URL. | CONFIRMED LIVE BROWSER + SQL SERVER / PUBLIC-ID + CTA PASS |

The historical N-093 live-data finding remains valid for the existing deployment snapshot. The new evidence verifies the current transaction ordering and regression behavior; it does not retroactively repair or recreate historical notification rows in the live database.

| N-118 | Current malformed notification mutation boundary | Fresh live JWT probes against `/api/admin/notifications/broadcast`, `/api/notifications/mark-all-read` and `/api/notifications/preferences` sent a JSON string/list instead of an object/list contract. All three returned HTTP `400 VALIDATION_ERROR` with Vietnamese-safe structured messages; no notification/read/preference mutation was created. | CONFIRMED CURRENT HTTP / PRE-FIX 500 REGRESSION RESOLVED; canonical outer envelope remains a contract gap |

| N-119 | Current logout, modal close and history Back | Instructor1 opened CS201 settings, closed it with Escape, then used the account-menu logout. Back settled at `#/auth`; CDP confirmed an existing router, `currentUser=null`, `_isRouting=false`, visible login form and no visible course, topbar or modal. The earlier account-menu click while the modal was open may have closed its backdrop first, so it does not independently prove logout with an overlay still mounted. | CURRENT BROWSER PASS for modal Escape and logout/Back auth stability; exhaustive overlay-at-logout coverage remains open |

| N-120 | Current three-role quick-demo login | After the auth-route correction, clean logout/login sessions used the visible demo selector for Instructor1, Student1 and Admin. Each reached `#/instructor/dashboard`, `#/student/dashboard` and `#/admin/governance` respectively, with matching role labels; CDP confirmed STUDENT/ADMIN routing idle and Admin primary status. | CURRENT BROWSER PASS for all three demo shortcuts; prior ambiguous/stalled observations are historical |

## Trạng thái inventory

Đây là master inventory tạo từ source hiện hành. Các cột runtime như message cuối cùng trên browser, duration thật, số popup sau refresh, response thực tế theo role và kết quả business chỉ được đánh dấu `CONFIRMED` khi có browser/API evidence tương ứng; các producer chưa được chạy vẫn là `UNVERIFIED_STATIC`.

## Current continuation correction

### Current continuation addendum (2026-10-05)

### Current Browser network-failure correction

On `http://localhost:5000`, clean logout/login sessions for Admin, Instructor and Student were each followed by temporary CDP blocking of all notification endpoints. In all three roles, opening the center showed `Không thể tải thông báo`, the explanatory status and `Thử lại`, and did not show `Không có thông báo nào`. After removing the block and using retry, reopening the center rendered the real notification list for each role. No business mutation was submitted; the temporary block was removed. This closes the three representative-role Browser outage path; broader retry/idempotency coverage remains open.

| ID | Surface / workflow | Current evidence | Status |
|---|---|---|---|
| N-109 | Student graded-result notification CTA | Historical seeded notice used an assessment UUID and rendered a 404; the canonical attempt-result route and producer regression are now corrected. A fresh 2026-10-06 disposable SQL/HTTP/Browser replay opened a newly emitted regrade notice and its related-page CTA rendered the released attempt result | CURRENT SQL/HTTP/BROWSER PASS; historical 404 retained for traceability |
| N-110 | STUDENT_ENROLLED CTA route construction | enrollment_service.py emitted server paths without the SPA hash for both instructor and student recipients. A failing unit regression captured both malformed URLs; current source emits the canonical role-specific hash routes, and the fresh live replay opened both role-specific CTAs successfully | FIXED SOURCE + LIVE BROWSER/SQL VERIFIED |
| N-111 | Instructor cold notification open | Instructor login showed a badge of 14; the first immediate center snapshot briefly rendered the empty state before revalidation, then the ALL and UNREAD filters displayed the 14 items | CONFIRMED BROWSER / ASYNC UX RISK |

The pre-fix N-046/N-048/N-105 observations remain in the inventory for traceability. Current source and Node evidence supersede their runtime state: `ApiClient.getNotifications()` raises `NOTIFICATIONS_UNAVAILABLE` after all route fallbacks fail, and the router exposes degraded/loading/retry states. Frontend regression coverage is 101 passed, 0 failed, 0 skipped; the three-role Browser outage/retry replay described above also passed.

## Backend producer master table

| ID | Module / path:line | Event type | Flow/role suy ra từ source | Message/action/duplicate note | Status |
|---|---|---|---|---|---|
| N-001 | `services/attempt_service.py:2315` | `ASSESSMENT_GRADED` | Student grading result | score/result payload; cần runtime verify | UNVERIFIED_STATIC |
| N-002 | `services/attempt_service.py:2335` | `SCORE_CHANGED_AFTER_REGRADE` | Student regrade | score-change payload; cần idempotency verify | UNVERIFIED_STATIC |
| N-003 | `services/authorization_service.py:1138` | `SYSTEM_ADMIN_INTERVENTION` | affected user/admin action | same event family reused by course service | UNVERIFIED_STATIC |
| N-004 | `services/auth_token_service.py:341` | `SECURITY_PASSWORD_CHANGED` | account owner | security event; email/notification path chưa browser verify | UNVERIFIED_STATIC |
| N-005 | `services/course_service.py:576` | `SYSTEM_ADMIN_INTERVENTION` | course/admin operation | same event type khác ngữ nghĩa | UNVERIFIED_STATIC |
| N-006 | `services/course_service.py:1050` | `COURSE_APPROVED` | course owner | dynamic title/body + action URL | UNVERIFIED_STATIC |
| N-007 | `services/course_service.py:1081` | `COURSE_REJECTED` | course owner | dynamic reason; raw message path cần verify | UNVERIFIED_STATIC |
| N-008 | `services/course_service.py:1117` | `COURSE_SUBMITTED_FOR_REVIEW` | admin/reviewer | submission event | UNVERIFIED_STATIC |
| N-009 | `services/course_service.py:1236` | `COURSE_OWNER_REASSIGNED` | old/new owner | same event appears twice in service | UNVERIFIED_STATIC |
| N-010 | `services/course_service.py:1261` | `COURSE_OWNER_REASSIGNED` | old/new owner | second producer path; duplicate boundary untested | UNVERIFIED_STATIC |
| N-011 | `services/enrollment_service.py:372` | `STUDENT_ENROLLED` | instructor/course owner | instructor-facing wording | UNVERIFIED_STATIC |
| N-012 | `services/enrollment_service.py:383` | `STUDENT_ENROLLED` | enrolled student | student-facing wording; same event name, separate recipient | UNVERIFIED_STATIC |
| N-013 | `services/file_service.py:563` | `FILE_REJECTED` | uploader/student/instructor | SECURITY category; scan rejection | UNVERIFIED_STATIC |
| N-014 | `services/file_service.py:852` | `FILE_REJECTED` | uploader | second rejection path; duplicate boundary untested | UNVERIFIED_STATIC |
| N-015 | `services/lesson_service.py:1865` | `LESSON_CHANGE_REQUEST` | instructor/admin review | change request flow | UNVERIFIED_STATIC |
| N-016 | `services/lesson_service.py:2381` | `COURSE_CHANGE_APPROVED` | instructor/course owner | admin approval; dynamic copy | UNVERIFIED_STATIC |
| N-017 | `services/lesson_service.py:2559` | `COURSE_CHANGE_REJECTED` | instructor/course owner | rejection reason | UNVERIFIED_STATIC |
| N-018 | `services/lesson_service.py:3031` | `COURSE_CHANGE_REQUESTED` | reviewer/owner | separate event from `LESSON_CHANGE_REQUEST` | UNVERIFIED_STATIC |
| N-019 | `services/user_service.py:311` | `SECURITY_PASSWORD_CHANGED` | account owner | password/security flow | UNVERIFIED_STATIC |
| N-020 | `services/user_service.py:374` | `SECURITY_PASSWORD_CHANGED` | account owner | second producer path | UNVERIFIED_STATIC |
| N-021 | `services/user_service.py:449` | `ACCOUNT_SUSPENDED` | suspended user/admin | mandatory security event | UNVERIFIED_STATIC |
| N-022 | `services/user_service.py:756` | `ROLE_CHANGED` | user/admin | role assignment path | UNVERIFIED_STATIC |
| N-023 | `services/user_service.py:990` | `ROLE_CHANGED` | user/admin | another role path with same event name | UNVERIFIED_STATIC |
| N-024 | `services/user_service.py:1143` | `ROLE_CHANGED` | instructor application | application result encoded as role event | UNVERIFIED_STATIC |
| N-025 | `services/user_service.py:1422` | `INSTRUCTOR_APPLICATION_SUBMITTED` | admin reviewer | application submitted | UNVERIFIED_STATIC |
| N-026 | `services/user_service.py:1607` | `ROLE_CHANGED` | instructor application | same event family, different business meaning | UNVERIFIED_STATIC |
| N-027 | `services/user_service.py:1653` | `ROLE_CHANGED` | instructor application | same event family, different business meaning | UNVERIFIED_STATIC |
| N-028 | `services/youtube_validator_service.py:183` | `COURSE_LESSON_VIDEO_BROKEN` | instructor/course owner | broken video validation | UNVERIFIED_STATIC |
| N-029 | `blueprints/admin/routes.py:2116` | `COURSE_CHANGE_APPROVED` | admin approval | route-level producer overlaps service-level producer | UNVERIFIED_STATIC |
| N-030 | `blueprints/admin/routes.py:2144` | `COURSE_CHANGE_REJECTED` | admin rejection | route-level producer overlaps service-level producer | UNVERIFIED_STATIC |
| N-031 | `blueprints/admin/routes.py:2330` | `COURSE_CHANGE_REJECTED` | admin rejection | second admin rejection path | UNVERIFIED_STATIC |
| N-032 | `blueprints/admin/routes.py:2405` | `COURSE_CONTENT_FLAGGED` | admin/content owner | dynamic lesson title/reason | UNVERIFIED_STATIC |
| N-033 | `blueprints/api_admin/routes.py:1295` | `COURSE_CONTENT_FLAGGED` | API admin/content owner | duplicate producer family across admin surfaces | UNVERIFIED_STATIC |
| N-034 | `blueprints/instructor/routes.py:1160` | `LESSON_CHANGE_REQUEST` | instructor/admin review | route-level producer overlaps service | UNVERIFIED_STATIC |
| N-035 | `blueprints/instructor/routes.py:2626` | `COURSE_PREREQUISITE_REQUEST` | instructor/admin | prerequisite request | UNVERIFIED_STATIC |
| N-036 | `blueprints/instructor/routes.py:2906` | `COURSE_PREREQUISITE_APPROVED` | instructor/course owner | approval | UNVERIFIED_STATIC |
| N-037 | `blueprints/instructor/routes.py:2930` | `COURSE_PREREQUISITE_REJECTED` | instructor/course owner | rejection reason | UNVERIFIED_STATIC |

## API and frontend inventory

| ID | Surface | Current behavior | Risk / expected contract | Status |
|---|---|---|---|---|
| N-038 | `GET /api/notifications` | list response has top-level `success`, `items`, counters and pagination | must be normalized under `data` while preserving documented fields | STATIC |
| N-039 | `GET /api/notifications/unread-count` | top-level `success` and `unread_count` | contract consistency with envelope | STATIC |
| N-040 | `POST /api/notifications/{id}/read` | returns raw service result | missing stable success/data shape | STATIC |
| N-041 | `POST /api/notifications/read-all` | top-level success/count | shape differs from mark-one | STATIC |
| N-042 | `DELETE /api/notifications/{id}` | returns raw result; current status is `deleted` | tests/spec expect `dismissed`; no browser proof yet | CONFIRMED TEST FAILURE |
| N-043 | notification preferences | GET/PUT use top-level `preferences` | shape differs from list/action routes | STATIC |
| N-044 | broadcast/retry admin routes | top-level counters | Admin-only broadcast and authenticated email-retry route now verified; retry returned zero eligible records, so delivery and audience-boundary coverage remain open | PARTIAL: CONFIRMED BROWSER + HTTP |
| N-045 | `frontend/assets/js/api.js:90-100` | converts backend error message into `Error.message` | raw backend/technical text leaks to UI | STATIC |
| N-046 | `frontend/assets/js/api.js:1117` | generic `getNotifications` exists in production source | frontend router test sandbox uses `ApiClient: {}` and omits the method, so the suite logs `getNotifications is not a function`; this is a test-harness contract gap, not proof that production `ApiClient` lacks the method | CONFIRMED TEST-HARNESS LOG |
| N-047 | `frontend/assets/js/router.js:1539` | optimistic delete then success toast; catch only warns | failure can leave UI state inconsistent and silent | STATIC |
| N-048 | `frontend/assets/js/router.js:1674-1720` | background fetch and newest toast | background failure is swallowed to console | STATIC |
| N-049 | `frontend/assets/js/ui.js:54` | arbitrary message/type/duration per call | no catalog, owner, code, dedupe or locale policy | STATIC |
| N-050 | frontend views | 384 `UI.showToast` calls; Vietnamese/English mixed | inconsistent language/type/copy | STATIC |
| N-051 | `frontend/assets/js/controllers.js:30,184` | native `alert` used | bypasses shared notification contract | STATIC |
| N-052 | runtime unauthenticated probe | notification endpoints return `401` with `{error:{code,message,correlation_id}}` only | direct evidence of envelope divergence from `{success,data,error}` requirement | CONFIRMED RUNTIME |
| N-053 | Student demo login | label Student but default route `#/instructor/dashboard` | account has both roles; default view is not communicated by demo label | CONFIRMED BROWSER |
| N-054 | Student notification center | mark-all 5 unread -> 0, success toast, items remain | read transition and total/unread distinction work in UI | CONFIRMED BROWSER |
| N-055 | Student notification center | category filter and `Tất cả` change visible list | filtering works; exact category mapping needs API capture | CONFIRMED BROWSER |
| N-056 | Student notification center | delete item shows `Đã xóa thông báo.`, item stays absent after refresh | UI outcome works; service/API public status still fails focused tests | PARTIAL |
| N-057 | Instructor notification center | two near-identical MIDTERM grading notifications appear together | likely duplicate producer/copy; business idempotency unproven | DUPLICATE OBSERVED |
| N-058 | Admin notification center | two near-identical CS301 approval requests appear together | duplicate event/copy or intentional channels not distinguished in UI | DUPLICATE OBSERVED |
| N-059 | Admin notification center | Hệ thống filter exposes security text containing `192.168.1.105` | IP-like value is user-visible; classify whether seed/sample or sensitive telemetry | SECURITY REVIEW |
| N-060 | Admin broadcast modal | empty required title blocked by Vietnamese warning; no broadcast submitted | local validation works | CONFIRMED BROWSER |
| N-061 | Admin governance | English permission error rendered and console warnings repeat during background loads | raw error propagation + noisy retry/background behavior | CONFIRMED BROWSER |
| N-062 | logout + reload | logout removes session; reload returns login, but stale hash remains `#/student/dashboard` | fail-closed data access passes; URL/history cleanup incomplete | PARTIAL |
| N-063 | authenticated `GET /auth/notifications?role=STUDENT` | HTTP 200; top-level `success/items/total/unread_count/page/per_page/preferences` | web-auth API shape differs from canonical `{success,data,error}` and from `/api/notifications` | CONFIRMED NETWORK |
| N-064 | same authenticated response | item `COURSE_ANNOUNCEMENT` has category `ASSESSMENT` | event/catalog/category mapping is not authoritative | CONFIRMED NETWORK |
| N-065 | same authenticated response | every sampled item contains `deleted_at: null` | serializer exposes non-canonical field | CONFIRMED NETWORK |
| N-066 | authenticated `/auth/notifications?role=INSTRUCTOR` | HTTP 200, `total=5`, `unread_count=3`; duplicate MIDTERM bodies use `ASSESSMENT_SUBMITTED` and `COURSE_ANNOUNCEMENT` | event identity/action URL differs for same business fact | CONFIRMED NETWORK |
| N-067 | authenticated `/auth/notifications?role=ADMIN` | HTTP 200, `total=5`, `unread_count=2`; duplicate CS301 bodies use `COURSE_APPROVAL_REQUEST` and `COURSE_ANNOUNCEMENT` | duplicate producer/legacy event path | CONFIRMED NETWORK |
| N-068 | role API comparison | Student/Instructor/Admin all return same top-level shape and shared preferences list | role-specific contract is not separately versioned; recipient/target_role is null in sampled items | CONFIRMED NETWORK |

| N-089 | Fresh JWT notification boundary probe | Student JWT login returned 200; unauthenticated list/count/preferences/mark-all returned structured 401; authenticated list returned 200 with `success/items/total/unread_count/page/per_page` but no `data`; preferences returned only `preferences` | REST notification envelope and preferences shape are inconsistent with the project canonical envelope | CONFIRMED CURRENT HTTP / CONTRACT PARTIAL |
| N-090 | Fresh invalid notification operations | Authenticated invalid read/dismiss/delete returned 404 `RESOURCE_NOT_FOUND`; wrong-method GET returned 405 `METHOD_NOT_ALLOWED`; empty preferences update returned 400 `VALIDATION_ERROR` | error codes are structured, but the canonical outer envelope is still absent | CONFIRMED CURRENT HTTP / CONTRACT PARTIAL |
| N-091 | Web-session unauthenticated boundary | `/auth/notifications` returned 401, `/auth/notifications/unread-count` returned 200 with `success=true,unread_count=0`, and `/auth/notifications/preferences` returned 405 | session endpoints do not share one authentication and route contract | CONFIRMED CURRENT HTTP / CONTRACT DRIFT |
| N-092 | Cross-role JWT read-only comparison | Student/Instructor/Admin logins returned 200; API roles were `STUDENT,INSTRUCTOR`, `STUDENT,INSTRUCTOR`, and `STUDENT,INSTRUCTOR,ADMIN`; notification totals were 6, 5 and 7 | role-specific read surfaces exist, but this does not prove every producer recipient rule | CONFIRMED CURRENT HTTP / BUSINESS COVERAGE PARTIAL |
| N-093 | SQL Server enrollment correlation and reproduction | OPS401 had 2 ACTIVE enrollments (`student3`, `student1`); four persisted `STUDENT_ENROLLED` events targeted users 2/3 and every event had zero linked `Notification` rows. A rollback-only real-service reproduction with commit-simulation (`flush()` + `expire_all()`) for PY301/student3 returned ACTIVE with 2 events and 2 linked notifications, then rolled back | persisted live-data gap is confirmed, but the current triggering exception is not reproducible | CONFIRMED PERSISTED GAP / REPRODUCTION OPEN |
| N-094 | Fresh SQL Server duplicate grouping | the double-click broadcast title grouped to 2 notification rows and 2 distinct event IDs for one recipient | persisted duplicate is confirmed independently of API/UI collapse | CONFIRMED CURRENT DB / P1 |
| N-095 | Fresh Browser Admin category filters | Admin login succeeded and notification center showed 7 items with 4 unread; `Khảo thí` showed 1 item, `Khóa học` showed 2 CS301 approval items with different titles, and `Hệ thống` showed 4 items including the two audit broadcasts and the IP-like security message | category filters work at UI level, but the two CS301 titles represent one apparent business request through different event/copy identities; the governance pane still showed the missing-primary-admin error | CONFIRMED FRESH BROWSER / DUPLICATE + RBAC |
| N-096 | Static result/appeal alert calls | `frontend/assets/js/views/student.js:5722,5830` calls `UI.alert(...)`, but `frontend/assets/js/ui.js` defines `showToast`, `openModal`, `confirm` and `closeModal` without a `static alert` method; two fallback `window.alert(...)` calls also remain in `controllers.js:30,184` | result/appeal alert paths can fail with a missing shared helper or bypass the notification contract; no visible trigger for the two `UI.alert` paths was present in the fresh result page, so runtime impact remains unverified | UNVERIFIED STATIC / P2 GAP |
| N-097 | Fresh Admin JWT list/filter boundary | unfiltered list returned `total=7, unread_count=4`; `SYSTEM=3`, `COURSE=2`, `ASSESSMENT=1`; `unread_only=true` and `status=UNREAD` returned 4; `per_page=0` clamped to 1, `per_page=1000` to 100, and `page=999` returned 200 with 0 items | category/status/pagination semantics are now directly evidenced; `unread_count` is a global badge count even when category filtering is applied, and out-of-range page is a successful empty result rather than a validation error | CONFIRMED CURRENT HTTP / CONTRACT SEMANTICS |
| N-098 | Fresh Admin role/invalid-filter boundary | `role=STUDENT`, `role=INSTRUCTOR` and `role=ADMIN` each returned the same 7 Admin-owned items; `status=BOGUS` and `unread_only=maybe` were ignored; `category=BOGUS` returned 0 | actor ID filtering remains present and no cross-user leak was observed, but role/status query parameters are permissive and can imply a role-scoped view without changing the result; source allows `target_role=NULL` rows for every requested role and silently ignores unknown status values | CONFIRMED CURRENT HTTP + SOURCE / P2 CONTRACT |
| N-099 | Login rate-limit boundary | six direct POSTs to `/api/v1/auth/login` using one unique synthetic email and a wrong password returned `401,401,401,401,401,429`; the sixth response included `Retry-After: 60` | brute-force throttling is directly proven without targeting a demo account; 429 was not previously covered by the notification matrix and is now recorded as an auth/system boundary, not a notification delivery result | CONFIRMED CURRENT HTTP / AUTH BOUNDARY |
| N-100 | Rapid mark-one-read idempotency | two consecutive PATCH requests for the same already-read Admin notification both returned `is_read=true` and the same `read_at`; unread count stayed unchanged at 2 | repeated read actions converge to one persisted state and do not decrement the unread counter twice; this is a scoped pass for mark-read, not proof for dismiss/broadcast idempotency | CONFIRMED CURRENT HTTP / IDEMPOTENT READ |
| N-101 | Mandatory SECURITY preference boundary | authenticated Admin `PUT /api/notifications/preferences` with `SECURITY.email_enabled=false` returned HTTP 400 `VALIDATION_ERROR` with the mandatory-security explanation; a before/after GET showed `email_enabled=true,is_mandatory=true` unchanged | the opt-out was rejected without a preference mutation; security notification delivery remains mandatory | CONFIRMED CURRENT HTTP / FAIL-CLOSED PASS |
| N-102 | Preference and broadcast required-field validation | unknown preference category returned HTTP 400 `VALIDATION_ERROR`; empty preferences returned HTTP 400; Admin broadcast missing title/body returned HTTP 400 with field-specific messages; `mark-all-read` with unknown category returned HTTP 200 and `marked_count=0` | invalid writes are rejected with structured validation errors and the unknown mark-all category is a no-op; canonical outer envelope remains inconsistent | CONFIRMED CURRENT HTTP / VALIDATION BOUNDARY |
| N-103 | Fresh notification-center keyboard focus order | Student DSA201 Browser center opened with named `Tất cả`, `Chưa đọc`, `Khảo thí`, `Khóa học`, `Hệ thống` buttons; `Tab` moved `Tất cả` -> `Chưa đọc` -> back to `Tất cả`, skipping the three category filters; `Escape` closed the center | visible category controls are not all reachable in the observed keyboard tab order; full keyboard/screen-reader conformance is not established | CONFIRMED FRESH BROWSER / P2 ACCESSIBILITY |
| N-104 | Wrong JSON type on notification mutations | authenticated Admin broadcast with JSON string and mark-all with JSON list both returned HTTP 500 `INTERNAL_ERROR` with correlation IDs; before/after list stayed at total 7/unread 2 and item IDs were unchanged; preferences JSON string returned HTTP 400 `VALIDATION_ERROR` | two mutation routes crash to a generic 500 instead of rejecting malformed input as 4xx; no business notification mutation occurred in the probe | CONFIRMED CURRENT HTTP / P1 API VALIDATION |
| N-105 | Frontend notification network-failure fallback (pre-fix) | historical read-only Node VM loaded the pre-fix `api.js`, forced all three notification route attempts to reject, and observed `{items:[],total:0,unread_count:0}` | preserved as the RCA-006 baseline; current source now raises `NOTIFICATIONS_UNAVAILABLE` and the router renders degraded/retry guidance | HISTORICAL BASELINE; superseded by current continuation correction |

| N-106 | Live prerequisite approval outcome | Instructor2 Browser approved request id `1` from DSA201 academic settings; UI toast confirmed success; Instructor1 API outgoing request returned `APPROVED`; `OPS401` prerequisite API returned DSA201; Instructor1 notification was `COURSE_PREREQUISITE_APPROVED` | approval business state, recipient notification and prerequisite link correlate across Browser/API/DB; this is separate from the live Admin-primary authorization failure | CONFIRMED BROWSER + HTTP/DB / PASS FOR APPROVE |
| N-107 | Live prerequisite rejection outcome | Instructor1 Browser created request id `2` for PY301→DSA201; Instructor2 Browser displayed it and opened the rejection prompt. Native prompt completion was unreliable, so the final request review used a fresh authenticated CSRF session; request returned `REJECTED` with the supplied reason and Instructor1 received `COURSE_PREREQUISITE_REJECTED` | rejection state and notification are proven through authenticated HTTP, but the final prompt submission is not a Browser PASS | PARTIAL BROWSER + CONFIRMED HTTP / REJECT OUTCOME |

| N-108 | Student-view mark-all and repeated no-op | In a fresh Browser Student-view session for the dual-role Instructor2 account, Notification Center showed 4 unread items; one `Đã đọc tất cả` action changed the badge to 0 and showed the success toast. The attempted Browser double-click hit a detached DOM node before a second request could be proven. Two immediate JWT `POST /api/notifications/mark-all-read` calls then both returned `success=true, marked_count=0` | mark-all converges to a stable read state and repeated API no-op does not double-decrement; Browser rapid-click behavior remains unverified because the second UI dispatch did not reach a live node | PARTIAL BROWSER + CONFIRMED HTTP / SCOPED IDEMPOTENCY |

## N-144 - broadcast retry idempotency (current correction)

| Field | Evidence |
|---|---|
| ID / Module / Page / Role | N-144 / Admin notifications / Governance broadcast modal / Admin |
| User Action / Trigger / Condition | Admin double-clicks or retries the same broadcast / `POST /admin/notifications/broadcast` (also `/api/admin/notifications/broadcast`) / valid UUID `X-Idempotency-Key` with unchanged payload |
| FE Function / API / Method | `AdminView.openBroadcastModal`, `ApiClient.broadcastNotification` / session web route and JWT admin route / POST |
| BE Handler / Business Rule | `broadcast_system_notification` / one `SYSTEM_BROADCAST` event and one fan-out per key; changed payload with the same key is a conflict |
| Success / Error Condition | 200 with `broadcasted_count` and `idempotent_replay`; 409 for changed payload; 400 for malformed key |
| Current / Expected Message | Current Browser toast: `Đã phát thông báo thành công tới 7 người dùng!`; expected: one Vietnamese success toast after one business outcome |
| Language / Type / Duration / Severity | VI / SUCCESS / existing toast duration / P1 duplicate-risk, now fixed in the scoped path |
| Root Cause / Status | no request key plus no in-flight UI guard; **FIXED / Browser + SQL Server + API regression verified** |
| Source / Runtime / DB / Duplicate | `frontend/assets/js/api.js`, `frontend/assets/js/views/admin.js`, `src/pwd301/services/notification_service.py`, route files / disposable `127.0.0.1:5105` / one matching event and 7 recipient rows / no duplicate |
| Owner / Next action | backend service + Admin UI / keep key on retry and extend the same contract to any future retryable broadcast client |

The Browser replay logged in through the visible Admin form, double-clicked the real broadcast button, showed one success toast, and the server log recorded one POST. SQL Server then found one matching `SYSTEM_BROADCAST` event and seven recipient notification rows. The API regression separately sent the same key twice and verified one event/recipient fan-out plus a 409 payload conflict. Inventory count is now **144 distinct audited cases**; prior duplicate rows remain historical evidence, not deleted data.

## N-145 - shared REST mutation validation and replay

| Field | Evidence |
|---|---|
| ID / Module / Page / Role | N-145 / Notification REST API / `/api/notifications/*` mutation routes / Admin JWT |
| User Action / Trigger / Condition | send malformed list or valid retry / broadcast, email-retry and preference mutation endpoints / payload must be a JSON object; valid broadcast repeats with the same UUID key |
| FE Function / API / Method | REST client contract (the current Browser Admin uses the session route) / `/api/notifications/broadcast`, `/api/notifications/emails/retry-failed`, `/api/notifications/preferences` / POST or PUT/PATCH |
| BE Handler / Business Rule | `broadcast_notification_api`, `retry_failed_emails_api`, `update_preferences_api` / reject malformed top-level types before field access; exact broadcast key replay is idempotent |
| Success / Error Condition | valid broadcast returned `200` with `broadcasted_count=7` and replay marker; malformed broadcast/retry returned `400 VALIDATION_ERROR` with no mutation |
| Current / Expected Message | `Notification payload must be a JSON object.` and `Retry payload must be a JSON object.` / actionable Vietnamese-facing client error without raw exception |
| Language / Type / Duration / Severity | VI contract target / VALIDATION or SUCCESS / API response, not toast / P1 API crash fixed |
| Root Cause / Status | `.get()` executed on list payloads before type guard; **FIXED / focused tests + live HTTP + SQL Server verified** |
| Source / Runtime / DB / Duplicate | `src/pwd301/blueprints/api_notifications/routes.py` / disposable `127.0.0.1:5105` / one REST broadcast event and seven rows / no duplicate on same key |
| Owner / Next action | REST route + notification service / complete canonical envelope normalization and test other producers |

Live disposable HTTP evidence: Admin JWT login succeeded; malformed shared broadcast and failed-email retry each returned HTTP 400, while two valid same-key broadcasts returned `200` with `idempotent_replay=false/true`. SQL Server found one matching event and seven recipient rows. Inventory count is now **145 distinct audited cases**.

## N-146 - canonical notification response envelope (current correction)

| Field | Evidence |
|---|---|
| ID / Module / Page / Role | N-146 / Notification REST contract / list, read, dismiss, preferences and mutation routes / authenticated clients |
| User Action / Trigger / Condition | Read notification data or submit a valid/invalid notification mutation / all current notification API branches |
| FE Function / API / Method | `ApiClient` notification methods and Admin broadcast client / `/api/notifications/*`, `/api/admin/notifications/broadcast`, Admin web broadcast/retry / GET, POST, PUT/PATCH |
| BE Handler / Business Rule | notification route serializers plus `_format_error_response` / every scoped success returns `success=true,data=...`; every scoped error returns `success=false,data=null,error=...` |
| Success / Error Condition | list/count/read/all-read/dismiss/preferences/broadcast/retry expose `data`; malformed payloads and auth/resource errors expose the canonical error envelope while legacy top-level fields remain for compatibility |
| Current / Expected Message | Structured `error.code`, `error.message`, optional field errors/correlation ID / no raw exception and no fabricated success |
| Language / Type / Duration / Severity | API contract / SUCCESS or VALIDATION / response body / P1 contract drift, fixed for the scoped notification handlers |
| Root Cause / Status | notification handlers returned legacy top-level payloads and the shared error formatter omitted `success/data`; **FIXED for notification REST/Admin notification handlers; wider API/web-auth contract drift remains separately audited** |
| Source / Runtime / DB / Duplicate | `src/pwd301/__init__.py`, `src/pwd301/blueprints/api_notifications/routes.py`, Admin route files / focused tests plus disposable SQL Server HTTP / no new notification rows on malformed requests |
| Owner / Next action | API contract owner / preserve compatibility fields while migrating remaining endpoint families and re-run cross-role Browser/API correlation |

Focused notification API tests passed **12**, Admin broadcast **1**, and notification IDOR tests **7**; the full API partition passed **383**. The current non-overlapping collection is **1587 tests**, all executed with zero skips in the controlled split. This closes the scoped notification envelope gate, not every API response-envelope discrepancy in the application.

## N-147 - failed email retry and delivery boundary (current correction)

| Field | Evidence |
|---|---|
| ID / Module / Page / Role | N-147 / Email outbox / Admin email retry / Admin → Student4 |
| User Action / Trigger / Condition | An email delivery fails, then an Admin retries failed deliveries / controlled disposable SQL Server fixture with one `FAILED` row |
| FE Function / API / Method | Admin retry action / `/api/admin/emails/retry-failed` / POST |
| BE Handler / Business Rule | `retry_failed_emails` → `process_email_queue` → `send_single_email` / failed rows reset to `PENDING`, then become `SENT` only after the transport reports success |
| Success / Error Condition | API returned `200`, `success=true`, `data.retried_count=1`; queue ended `SENT` and delivered to the exact recipient snapshot |
| Current / Expected Message | API `retried_count=1`; expected UI copy must say retry queued/completed only after the corresponding server response, not claim external inbox delivery |
| Language / Type / Duration / Severity | API contract / SUCCESS or SYSTEM failure / response body / P1 operational evidence gap, scoped outbox path passes |
| Root Cause / Status | live runtime has no configured external SMTP sink and had no eligible failed row; **PASS for outbox/retry/recipient boundary with capture transport; external SMTP delivery remains UNVERIFIED** |
| Source / Runtime / DB / Duplicate | `src/pwd301/services/email_service.py`, `src/pwd301/blueprints/api_admin/routes.py` / disposable SQL Server / one delivery transitioned `FAILED → PENDING → SENT`, no duplicate |
| Owner / Next action | platform/email owner / configure an approved local SMTP sink/provider and repeat with a real transport receipt without exposing credentials |

The disposable probe produced `FAILED` with one forced transport failure, Admin retry returned `200` with `retried_count=1`, and the queue returned `SENT` to `student4@pwd301.local`. No external message was sent. Inventory count is now **147 distinct audited cases**.

## N-148 - Browser cover-image upload chooser boundary (current correction)

| Field | Evidence |
|---|---|
| ID / Module / Page / Role | N-148 / Course authoring / Instructor course manage / Instructor1 |
| User Action / Trigger / Condition | Click `Đổi Ảnh Đại Diện Khóa Học` on CS201 / visible `#course-thumbnail-input` accepts `image/png,image/jpeg,image/webp` |
| FE Function / API / Method | course-manage cover upload control / file chooser then course update request / Browser click |
| BE Handler / Business Rule | not reached; no file was supplied by the Browser automation layer / upload cannot be graded from an unsubmitted chooser |
| Success / Error Condition | no API request, no success/error toast, no database mutation observed |
| Current / Expected Message | none / actionable chooser or validation feedback after a real file is selected |
| Language / Type / Duration / Severity | N/A / NOT VERIFIED / N/A / P1 acceptance blocker |
| Root Cause / Status | Edge extension refused automation file assignment and the native chooser did not appear after the visible click; **BLOCKED ENVIRONMENT, application validation not graded** |
| Source / Runtime / DB / Duplicate | live course-manage DOM and `#course-thumbnail-input` / local Edge / no new row / no duplicate |
| Owner / Next action | Browser environment owner / grant an approved file-selection path or perform one manual selection, then rerun valid/invalid/quarantine cases |

The input was visible and enabled with the expected image MIME allowlist. `fileChooser.setFiles` returned `Not allowed`; a direct visible click also produced no chooser window. Inventory count is now **148 distinct audited cases**.

## N-149 - Browser resource download completion boundary (current correction)

| Field | Evidence |
|---|---|
| ID / Module / Page / Role | N-149 / Student lesson resources / DSA201 lesson reader / Student4 |
| User Action / Trigger / Condition | Click visible `Tải về` for `Tong_hop_Do_phuc_tap_Thuat_toan_BigO.pdf` / authenticated enrolled Student4 |
| FE Function / API / Method | lesson-resource download anchor / `GET /student/files/c766a3ad-dcb0-4658-9dcf-57095e595ea5/download` / GET |
| BE Handler / Business Rule | authenticated file-download path / only accessible clean/authorized resources may stream |
| Success / Error Condition | Browser URL stayed on the lesson and a download was initiated, but no finalized PDF appeared |
| Current / Expected Message | no toast / a completed readable PDF in Downloads or explicit error/retry guidance |
| Language / Type / Duration / Severity | N/A / SYSTEM or SUCCESS / download duration / P1 file-evidence gap |
| Root Cause / Status | Browser produced `Tong_hop_Do_phuc_tap_Thuat_toan_BigO.pdf.crdownload` at **1169 bytes** and it remained incomplete after 5 seconds; **PARTIAL/FAIL, stream completion unverified** |
| Source / Runtime / DB / Duplicate | lesson-reader visible anchor and local Downloads folder / local Browser + authenticated runtime / no DB mutation / no duplicate |
| Owner / Next action | file-delivery + Browser environment owner / inspect response length/stream closure and rerun until a readable finalized file is verified |

The link and recipient authorization were visibly present, but the file was not accepted as a successful download. Inventory count is now **149 distinct audited cases**.

Additional local-byte check: the `.crdownload` payload is 1,169 bytes, begins with `%PDF-1.4` and contains `%%EOF`. The content appears structurally complete, but the Browser did not finalize/rename it, so this remains a Browser completion/response-closure gap rather than a confirmed unreadable-PDF defect.

## N-150 - result alert title/message contract (current correction)

| Field | Evidence |
|---|---|
| ID / Module / Page / Role | N-150 / Assessment result / appeal status and score scale dialogs / Student |
| User Action / Trigger / Condition | Open a pending appeal notice or score-scale dialog / result view calls `UI.alert(title, message)` |
| FE Function / API / Method | `StudentView` result actions / no new API request for the display-only dialog / UI helper |
| BE Handler / Business Rule | source data already loaded from the attempt/result API / dialog must present the backend-derived facts without changing them |
| Success / Error Condition | title and body render in the positions supplied by the caller; multiline details remain readable and escaped |
| Current / Expected Message | Vietnamese caller title followed by Vietnamese detail body / no swapped heading or collapsed newline text |
| Language / Type / Duration / Severity | VI / INFO or WARNING / modal until dismissed / P2 UX/contract, fixed in shared helper |
| Root Cause / Status | `UI.alert` accepted `(message,title)` while every current caller supplied `(title,message)`; **FIXED with RED/GREEN frontend regression** |
| Source / Runtime / DB / Duplicate | `frontend/assets/js/ui.js`, `frontend/assets/js/views/student.js` / Node contract test / no DB mutation / one modal owner |
| Owner / Next action | frontend UI owner / exercise the pending-appeal and score-scale triggers in Browser once a current seeded result exposes them |

The focused regression failed before the change because the captured modal title was the caller body. After the change it passed; the full frontend suite is now **102 passed, 0 failed, 0 skipped**. Browser trigger coverage remains separate because the current result page did not expose both controls in the prior replay. Inventory count is now **150 distinct audited cases**.

## Field completeness and evidence rule

- `event_type`, source path and line: extracted statically.
- title/body, recipient, action URL and condition: source inspection only; dynamic branches require runtime request capture.
- API method/status/body: source plus targeted tests; live role behavior remains unverified.
- response/duplicate/hardcode/owner/next action: classified in RCA and fix plan, not inferred as passed behavior.
- No inventory row is marked `PASS` without browser or direct API evidence.

## Runtime traceability matrix

| Requirement / user action | FE | API | BE | DB | Notification/result | Test evidence | Result |
|---|---|---|---|---|---|---|---|
| Student login + role view | `auth.js`, `router.js` | login endpoint | session/role resolution | user roles/session | Student label initially routed Instructor; explicit switch succeeded | Browser PASS with anomaly | PARTIAL: authentication passes; default-role UX ambiguous |
| Student mark all read | `router.js` mark-all handler | mark-all notification route | `mark_all_as_read` | `read_at` updates | badge 5 -> 0, items remain | Browser PASS; focused tests pass | PASS for single action; rapid Browser dispatch unverified |
| Student dismiss | router delete handler | DELETE/PATCH notification route | `dismiss_notification` | expiry semantics | item removed + success toast; service status is `deleted` | Browser partial + unit/API FAIL | FAIL contract / PARTIAL UI |
| Notification category filter | notification dropdown | list query params | `list_user_notifications` | category/event joins | `Khảo thí` and `Hệ thống` visibly filter lists | Browser PASS; authorized API capture not run | PARTIAL: UI pass, API semantics incomplete |
| Instructor grading notices | notification dropdown | list route | attempt/grading producers | event + recipient rows | two near-identical MIDTERM notices visible | Browser duplicate observation; DB row IDs not captured | FAIL/UNVERIFIED duplicate identity |
| Admin approval notices | notification dropdown | list route | admin/API/service producers | event + recipient rows | two near-identical CS301 approval notices visible | Browser duplicate observation; DB row IDs not captured | FAIL/UNVERIFIED duplicate identity |
| Admin empty broadcast | broadcast modal | no request submitted | client required-field validation | no write | Vietnamese warning, no broadcast | Browser PASS validation | PASS validation only |
| Admin valid broadcast | broadcast modal | admin broadcast route | `SYSTEM_BROADCAST` creation and recipient fan-out | one Admin recipient row | success toast, badge 2 -> 3, new item visible | Browser + authenticated HTTP PASS for one Admin-only path; retry and other audiences not run | PARTIAL: one audience path |
| Admin RBAC failure | governance view/error state | admin endpoints | permission checks | no notification write proven | English permission error + repeated warnings | Browser console/UI; DB not queried | FAIL/UNVERIFIED valid Admin path |
| Logout + reload | router/session cleanup | logout endpoint/session clear | session revocation | session state | login page after reload; stale hash before reload | Browser partial PASS | PARTIAL: protected content hidden, modal/hash cleanup incomplete |

## Additional end-to-end inventory rows

| ID | Surface / workflow | Observed behavior | Notification or business implication | Status |
|---|---|---|---|---|
| N-069 | Instructor valid course create | `AUDIT1004` was created and management route opened with success toast | creates a business object that should later be traceable to review notifications | CONFIRMED BROWSER |
| N-070 | Instructor learning-unit create | blank name rejected; valid `Unit AUDIT1004` created | draft creation path gives local success feedback | CONFIRMED BROWSER |
| N-071 | Instructor lesson draft | lesson draft saved and edit route assigned an ID | save-draft result is not correlated to notification/API event in this audit | CONFIRMED BROWSER / CORRELATION MISSING |
| N-072 | Instructor course review submission | confirmation then `Chờ duyệt`; edit controls became frozen | review request should produce one admin-visible event and one owner-visible state | CONFIRMED BROWSER |
| N-073 | Admin course review queue on live runtime | `0 Khóa học chờ duyệt` despite sender-side `Chờ duyệt` | live approve/reject workflow cannot be proven; authorization failure is confirmed | CONFIRMED BROWSER / LIVE FAIL |
| N-074 | Instructor exam publish | sample exam publish toast reported 4 questions persisted and published | publication/result notification ownership was not captured | CONFIRMED BROWSER |
| N-075 | Student waiting room/start | pledge enabled start; attempt created; fullscreen violation overlay appeared | proctoring state changes before answers and must be included in audit/result trail | CONFIRMED BROWSER / PARTIAL |
| N-076 | Student autosave/submit/result | autosave confirmed twice; submit result was 100/100, 2/2 correct | business result displayed, but notification/DB row correlation not captured | CONFIRMED BROWSER |
| N-077 | Student result PDF | UI action timed out without verifiable download | download contract remains unverified | UNVERIFIED BROWSER |
| N-078 | Student enrollment | OPS401 confirmation changed catalog card to `Đã ghi danh`; dashboard showed 3 enrolled courses | enrollment success should correlate with one active Enrollment and any notification | CONFIRMED BROWSER / DB CORRELATION MISSING |
| N-079 | Student course resource download | authenticated HTTP session returned HTTP 200, `application/pdf`, 1,213 bytes and `attachment` disposition; browser click/direct navigation was blocked by Edge `ERR_BLOCKED_BY_CLIENT` | backend file access passes; browser download acceptance remains unverified | PARTIAL: BACKEND PASS / BROWSER BLOCKED |
| N-080 | Demo Admin identity | `src/pwd301/seeds/demo.py` assigns the Admin link reason `SUB_ROLE:ADMIN_PRIMARY`, but direct SQL Server inspection found the live `ADMIN` link reason `Baseline root administrator initialization` with no sub-role token | stale baseline role-link metadata explains the seed/runtime authorization drift | CONFIRMED SQL SERVER ROOT CAUSE |
| N-081 | Admin identity and pending queue API on live runtime | supported `GET /auth/login` after login returned HTTP 200 with `admin_sub_role` empty and `is_primary_admin:false`; `GET /admin/courses/pending` returned HTTP 403; `/auth/me` is not a registered route (terminal 404), and browser navigation was also blocked | live runtime authorization failure and persisted missing `ADMIN_PRIMARY` metadata are confirmed; product/live DB repair was not applied in read-only audit | CONFIRMED HTTP + DB / LIVE REPAIR PENDING |
| N-082 | Admin valid broadcast | Admin selected `Chỉ Quản trị viên (ADMIN)`, submitted a non-empty Vietnamese title/body, received `Đã phát thông báo thành công tới 1 người dùng!`; the notification dropdown showed the same item and badge 2 -> 3; authenticated HTTP returned `event_type=SYSTEM_BROADCAST`, `category=SYSTEM`, matching `body`, `is_read=false`, `total=6`, `unread_count=3`; SQL Server showed one matching notification row | one authorized audience and UI/API/DB correlation pass; recipient-boundary and retry/idempotency coverage remain open | PARTIAL: CONFIRMED BROWSER + HTTP + DB |
| N-083 | Student pagination and role query isolation | authenticated Student API page 1 and page 2 with `per_page=2` returned HTTP 200, two items per page, total 6 and zero ID overlap; requesting `role=ADMIN` still returned the Student's own five-item set and did not expose either Admin audit broadcast | pagination sample is consistent and no cross-user leak was observed; `role` query parameter appears ignored rather than an authorization switch, so contract semantics remain ambiguous | PARTIAL: HTTP PASS / CONTRACT REVIEW |
| N-084 | Admin failed-email retry | authenticated Admin session refreshed CSRF, then `POST /admin/emails/retry-failed` with `max_emails=50` returned HTTP 200 and `retried_count=0` | authorization and empty-queue response pass; no failed email existed, so actual delivery/retry side effect is unverified | PARTIAL: HTTP PASS / DELIVERY UNVERIFIED |
| N-085 | Admin broadcast server validation | authenticated Admin `POST /admin/notifications/broadcast` with body but no title returned HTTP 400, `VALIDATION_ERROR`, `Field 'title' is required.`, and no broadcast count | server validation is correct for this field, but error envelope still lacks canonical `success:false,data:null` | CONFIRMED HTTP / CONTRACT PARTIAL |
| N-086 | Instructor course-cover upload input | after canceling review, enabled `input[type=file]#course-thumbnail-input` advertised `image/png,image/jpeg,image/webp`; Edge file chooser `setFiles` returned `Not allowed` before the app could process the file | upload UI/input is present, but browser extension file-URL permission blocks acceptance; no product success/error result is claimed | BLOCKED ENVIRONMENT / UNVERIFIED PRODUCT PATH |
| N-087 | SQL Server duplicate correlation | direct read-only query against database `PWD301` found one valid audit broadcast row, but the double-click title had 2 notification rows, 2 distinct notification event IDs and 1 recipient; API list exposed only one matching item | duplicate is persisted in DB and then hidden/collapsed by API/UI presentation; this is a confirmed idempotency/business-data defect | CONFIRMED SQL SERVER / P1 |
| N-088 | Corrected disposable Admin review retest | `PWD301_AUDIT_ADMIN_20261004` was migrated and seeded from current source; Browser login showed `ADMIN CHÍNH`, queue 1, approve reached `APPROVED`, and reset-fixture request-edit/reject reached `DRAFT`; DB post-conditions were verified | corrected seed/authorization path works in isolation; live `PWD301` remains unauthorized and owner-notification correlation remains open | CONFIRMED BROWSER + DB / DISPOSABLE ONLY |

| N-151 | Admin security alert copy | Browser showed seeded `SYSTEM_SECURITY_ALERT` with raw internal IP `192.168.1.105`; source seed and live notification row were then corrected | event remains actionable while raw network telemetry is kept out of the user-facing notification | FIXED: TDD + live SQL Server + Browser reload; zero remaining raw-IP matches |

## N-152 - manual ESSAY grading and result presentation (current correction)

| Field | Evidence |
|---|---|
| ID / Module / Page / Role | N-152 / assessment grading and result detail / Instructor and Student |
| User Action / Trigger / Condition | Instructor opens a pending ESSAY submission, enters an awarded score and required reason, then saves; Student result rendering receives the persisted essay answer and manual grade |
| FE Function / API / Method | `InstructorView.openAttemptDetailModal`, Student result renderer, `ApiClient.gradeInstructorAttemptQuestion` / `POST /instructor/attempts/{attempt_id}/grades/{attempt_question_id}` |
| BE Handler / Business Rule | `get_instructor_attempt_evaluation` exposes `row_version`; the grading service remains server-authoritative and requires a valid score, reason and concurrency token |
| Success / Error Condition | Pending card exposes the manual-grade control; save shows a success toast and refreshes the modal; result detail shows the essay text, awarded points, manual status and feedback rather than choice labels or invented zero points |
| Current / Expected Message | Browser showed `Đã lưu điểm tự luận và cập nhật kết quả.` and refreshed to `3.5 / 20`; the ESSAY card showed `3.5 / 4 điểm` and the reason was retained |
| Language / Type / Duration / Severity | VI / SUCCESS or validation error / until modal refresh / P1 grading truthfulness |
| Root Cause / Status | API evaluation omitted `row_version`, Instructor rendered choice-only detail, and Student rendered ESSAY through choice fields; **FIXED for the scoped Instructor live flow and Student Browser result flow** |
| Source / Runtime / DB / Duplicate | `instructor.js`, `student.js`, `api.js`, `attempt_service.py` / live Browser controlled fixture / SQL Server grade `MANUAL_GRADED`, attempt `GRADED`, awarded `3.5`, rowversion `0000000000112d3c` / fixture deleted and orphan counts returned zero |
| Owner / Next action | grading + frontend owners / retain the existing Browser/API/DB regression and monitor other ESSAY producers; no fullscreen bypass is required for the result-view acceptance path |

## Latest dismiss contract correction (2026-10-05)

The current source soft-dismisses by setting `expires_at` and returns the canonical public status `dismissed`; it no longer returns the historical `deleted` value. The focused notification service plus API scope was rerun after the current worktree state: **25 passed, 0 failed, 0 skipped**. This closes the service/API contract regression. The subsequent Browser delete/dismiss replay is recorded in the newer fixture section below.

## N-153 - dynamic SECURITY notification telemetry redaction (current correction)

| ID / Module / Page / Role | N-153 / shared notification service / all security notification recipients |
|---|---|
| User Action / Trigger / Condition | A SECURITY event is dispatched with an IPv4 in title, body or CTA URL |
| FE / API / BE / DB | Existing notification center/API path / `dispatch_notification` / shared security sanitization before `notifications` and event action payload are persisted |
| Observed pre-fix | RED regression preserved `192.168.1.105` in title/body and `/admin/security?ip=192.168.1.105` |
| Current result | IPv4 values become `[REDACTED]` in title, body and action URL; the security event and actionable route remain present |
| Verification | Focused security/seed checks and current notification unit/API/demo/security scope passed **37 passed, 0 failed, 0 skipped**; the complete current split passed **1,589 passed, 0 failed, 0 skipped** |
| Status | **FIXED for shared SECURITY dispatch; dynamic producer catalog completeness remains open** |

The current authoritative inventory count is now **153 distinct audited cases**. Historical 152-case snapshots remain traceability only.

## Latest Browser dismiss fixture replay (2026-10-05)

A disposable Admin notification titled `AUDIT_DISMISS_FIXTURE_601B33526EBB` was opened in the real notification center. The exact row-level `delete` control was clicked once after action-time confirmation. The Browser removed the fixture from the open notification dialog and rendered the success feedback `Đã xóa thông báo.`; the Admin session was then logged out and the temporary tab was closed.

The live SQL Server row was retained by public id `3697da94-27a4-472e-b970-d7078e047c5a` with title unchanged, `expires_at=2026-10-05 14:50:30.184000` and `read_at=NULL`. This is direct Browser -> API -> SQL evidence for one soft-dismiss/delete action and is consistent with the current `status=dismissed` service/API contract. It does not close bulk delete, rapid double-click, timeout retry, or non-Admin dismiss coverage.

## Latest Browser download finalization replay (2026-10-05)

Student1 opened the authorized DSA201 resource `Tong_hop_Do_phuc_tap_Thuat_toan_BigO.pdf` and clicked the visible `Tải về` link. Edge emitted a download event and a readable file at `C:\Users\LENOVO\Downloads\Tong_hop_Do_phuc_tap_Thuat_toan_BigO.pdf` was present at **1,169 bytes**, with header `%PDF-1.4` and trailing `%%EOF`. Because that same-name file pre-existed from an earlier replay, this is file-specific integrity evidence, not proof that this click newly finalized the stream; the distinct-resource replay below remained `.crdownload`. Upload/file-selection, quarantine-access and download-stream breadth remain separate.

## Latest Student rapid mark-all replay (2026-10-05)

A disposable `AUDIT_MARKALL_RAPID_FIXTURE_601B33526EBB` notification was created for Student1. In the real Student notification center, the exact `Đã đọc tất cả` control was double-clicked; the UI settled at `Chưa đọc (0)`, retained the fixture in the list as read, and rendered one `Đã đánh dấu tất cả thông báo là đã đọc.` toast. SQL Server showed exactly one fixture notification/event row with one `read_at` timestamp and no duplicate row/event. The fixture was removed afterward with zero remaining targeted rows.

This closes the Student Browser rapid mark-all single-fixture/idempotent-state checkpoint. It does not generalize to dismiss/delete, every producer, timeout/out-of-order retry, or every role combination.

## Fresh-resource download stream correction (2026-10-05)

To remove the same-name ambiguity, Student1 opened the DSA201 resource `Cau_truc_Heap_va_Priority_Queue.pdf`. Edge emitted the download event, but `Cau_truc_Heap_va_Priority_Queue.pdf.crdownload` remained at **1,145 bytes** after two polls over 20 seconds; no finalized `.pdf` appeared. The partial file was a disposable replay artifact and was not treated as success. The authorized download gate is therefore **PARTIAL**: one existing readable PDF is validated, while fresh stream finalization is not generally proven.

### Late Browser download completion correction (2026-10-05)

The same resource subsequently finalized after the delayed stream: `Cau_truc_Heap_va_Priority_Queue.pdf` appeared at **1,145 bytes**, began `%PDF-1.4` and ended with `%%EOF`; no `.crdownload` remained. The final result is **PASS for the authorized DSA201 resource download after eventual completion**, with a remaining UX/timing concern because the Browser had no finalized file within the first 20-second observation window.

## Latest Browser upload permission replay (2026-10-05)

Instructor1 opened the current CS201 cover-upload control. A disposable invalid upload fixture was prepared locally, but Edge rejected `fileChooser.setFiles` with `Not allowed`; the input remained empty (`files=null`, `value=''`) and no upload success/error request or database mutation could be observed. The fixture was removed and the Instructor session logged out. Upload acceptance/rejection and quarantine access therefore remain **BLOCKED ENVIRONMENT**, not product PASS.

A fresh Computer Use retry on the same live page clicked both visible upload controls (`Tải ảnh bìa ngay` and `Đổi Ảnh Đại Diện Khóa Học`) through the accessibility surface. Neither opened a native picker, so the input remained unselected and the backend was still not reached. This strengthens the environment blocker but does not count as a Browser upload pass.

## Current Admin-view mark-all replay (2026-10-05)

This is supplemental role coverage for the existing mark-all cases `N-054`/`N-108`; it is not a new inventory shape. In a fresh Admin Browser session, the notification center showed badge **2** and `Chưa đọc (2)`. Clicking `Đã đọc tất cả` left the notification items visible, changed the badge to **0**, and changed the unread filter to `Chưa đọc (0)`. A read-only SQL Server check for `admin@pwd301.local` in the active Admin view (`target_role='ADMIN'` or `NULL`) returned `total=20`, `unread=0`, `read=20`.

Result: **PASS for one Admin mark-all action and its UI/DB post-condition**. Browser rapid double-dispatch remains unproven, and this action did not exercise dismiss/delete.

The scoped live fixture was `e491c028-bfd6-4d84-9b44-9c5652e5f748`; it was removed after verification and no production test fixture remains. A separate Browser replay then opened the existing released ESSAY result for Student1 and visibly showed the persisted answer, `4 / 4 đ`, manual feedback and no A/B/C/D choice labels. This correction increases the authoritative inventory count to **152 distinct audited cases** and closes the Student result-view Browser gate; the fullscreen limitation applies only to starting a new controlled exam attempt.

## N-154 - lesson-flag retry idempotency (2026-10-06)

| Field | Evidence |
|---|---|
| ID / Module / Page / Role | N-154 / Admin course review flag / REST and Web admin routes / Admin -> Instructor |
| User Action / Trigger / Condition | Admin submits a valid lesson flag with `X-Idempotency-Key`, then retries the same request or reuses the key with a changed reason |
| FE / API / BE / DB | Existing Admin flag action -> `POST /api/admin/courses/{course}/lessons/{lesson}/flag` and Web equivalent -> `flag_lesson_content` -> `NotificationEvent.event_key`, `AuditEvent`, `Notification` |
| Expected / Observed | First request `200` with `idempotent_replay=false`; exact retry `200` with `true`; changed payload `409 CONFLICT`; SQL delta exactly one audit, one event and one owner notice |
| Verification | TDD RED/GREEN focused API suite **9 passed, 0 failed, 0 skipped**; disposable SQL Server probe **3 cases, 0 failed, 0 skipped**; exact audit database cleanup returned `audit_database_remaining=0`; Ruff and diff check passed |
| Status / Boundary | **FIXED for keyed REST/Web retry semantics and SQL persistence**; Browser double-click/retry visual replay remains unverified because CUA currently exposes no Browser |
The new N-154 row brings the latest authoritative inventory count to **154 distinct audited cases**. Earlier 152/153 counts remain historical checkpoints and are not silently rewritten.

## N-155 - distinct notification-copy visibility correction (2026-10-06)

| Field | Evidence |
|---|---|
| ID / Module / Trigger | N-155 / notification list and unread count / two distinct events share title/body |
| Previous behavior | The presentation query used recipient + title + body + role and hid every older matching row, even when the events had different event types and durable event IDs |
| Current behavior | Every non-expired durable event remains visible; producer-level idempotency handles actual retries |
| Verification | TDD RED failed with total 1 for two distinct events; GREEN notification API/service scope passed **37 passed, 0 failed, 0 skipped**; Ruff and diff check passed |
| Boundary | Backend/API contract is fixed; Browser notification-center visual replay remains pending because CUA currently has no Browser |
The SQL Server replay strengthened N-155: a fresh disposable fixture persisted 2 rows with event types COURSE_ANNOUNCEMENT and SYSTEM_NOTICE, and authenticated REST returned 2 matching items. The probe reported **1 case, 0 failed, 0 skipped**; cleanup returned audit_database_remaining=0.
N-155 is the latest addition; the authoritative inventory is now **155 distinct audited cases**. Earlier 152/153/154 counts remain historical checkpoints.
## N-156 - generic event-key conflict protection (2026-10-06)

| Field | Evidence |
|---|---|
| Trigger | A producer reuses one NotificationEvent.event_key with changed type/payload/target semantics |
| Previous behavior | emit_event returned the existing row without comparing semantics |
| Current behavior | Mismatched reuse raises ConflictError; exact same semantics still replay the original event |
| Verification | RED/GREEN notification/flag scope **38 passed, 0 failed, 0 skipped**; SQL Server probe covered same-copy visibility plus event-key conflict in **2 cases, 0 failed, 0 skipped**; cleanup remaining 0 |
| Boundary | Generic service/API behavior is verified; Browser and complete producer catalog remain open |
N-156 is the latest addition; the authoritative inventory is now **156 distinct audited cases**. Prior 152-155 counts remain historical checkpoints.
## N-157 - SQL Server demo-seed idempotency (2026-10-06)

| Field | Evidence |
|---|---|
| Trigger | Run the canonical demo seed a second time on the same disposable SQL Server database |
| Expected / Observed | No created lists, no new notifications/audits, and unchanged counts for users, courses, questions, attempts and resources |
| Verification | Counts before/after: users 7/7, courses 4/4, questions 7/7, attempts 3/3, resources 1/1, notifications 22/22, audits 13/13; **1 case, 0 failed, 0 skipped**; cleanup remaining 0 |
| Boundary | SQL seed idempotency is closed for the current fixture; live database seed and Browser breadth remain separate |
N-157 is the latest addition; the authoritative inventory is now **157 distinct audited cases**. Earlier counts remain historical checkpoints.

## N-158 - shared dispatch idempotency input

| Field | Evidence |
|---|---|
| Trigger | A notification producer needs to reuse a stable event key through the shared dispatch helper |
| Previous behavior | `dispatch_notification()` had no `event_key` input, so callers could only rely on a generated event key or prebuilt event |
| Current behavior | Optional UUID `event_key` is forwarded to `emit_event()`; exact retries reuse the event and recipient notification |
| Verification | RED TypeError then GREEN; focused notification/flag suite **39 passed, 0 failed, 0 skipped**; Ruff, compile and diff check passed |
| Boundary | This is a shared capability correction, not proof that every producer supplies a stable key; Browser and external delivery remain open |

The latest authoritative inventory is **158 distinct audited cases**. Prior 157 and earlier counts remain historical checkpoints.

## N-159 - keyed dispatch content contract

| Field | Evidence |
|---|---|
| Trigger | Same event key is retried with a changed notification body |
| Previous behavior | `dispatch_notification()` omitted title/body/category/target role from the event payload, so `emit_event()` could not detect the semantic change |
| Current behavior | Keyed dispatch persists `_dispatch_contract`; exact replay reuses event/notification/email outbox, changed content raises `ConflictError` before fan-out |
| Verification | RED reproduced no conflict; GREEN passed exact replay and conflict assertions; focused notification/flag scope **39 passed, 0 failed, 0 skipped** |
| Boundary | Only callers supplying a stable key or prebuilt event receive this contract; the current AST inventory has 32 direct calls with neither `event_key` nor an `event` argument |

The latest authoritative inventory is **159 distinct audited cases**. Prior counts remain historical checkpoints.

## N-160 - `STUDENT_ENROLLED` producer keys

| Field | Evidence |
|---|---|
| Trigger | A Student enrollment fans out one notice to the Instructor and one to the Student |
| Key derivation | UUIDv5 over durable `enrollment.id`, event type and recipient role; the two recipients intentionally use different keys |
| Verification | Unit capture passed; SQL Server disposable enrollment replay reported expected keys present, event rows `2 -> 2`, notification rows `2 -> 2`, **3 cases, 0 failed, 0 skipped** |
| Cleanup | Disposable SQL Server database removed; `audit_database_remaining=0`; port 5105 had zero listeners |
| Boundary | 32 direct dispatch callsites have neither an explicit key nor a prebuilt event in the current AST inventory; Browser and external delivery gates remain open |

The latest authoritative inventory is **160 distinct audited cases**. Prior counts remain historical checkpoints.

## N-161 - password security notification key

## N-162 - course lifecycle producer key adoption (2026-10-06)

| Field | Evidence |
|---|---|
| Trigger | Course submission, Admin approval and Admin rejection each fan out an owner/reviewer notice |
| Key derivation | UUIDv5 over the durable course AuditEvent.id, canonical audit action and recipient user ID |
| Verification | RED missing-key assertion then GREEN lifecycle test; SQL Server approval replay kept event/notification rows at 1 -> 1, 4 cases, 0 failed, 0 skipped |
| Current AST inventory | 35 direct calls; 7 explicit event_key; 1 prebuilt event; 27 neither |
| Boundary | Remaining unkeyed producers, Browser rapid retry/visual acceptance and external SMTP/inbox remain open |

The latest authoritative inventory is 162 distinct audited cases. Prior counts remain historical checkpoints.

## N-163 - course-owner reassignment producer key adoption (2026-10-06)

| Field | Evidence |
|---|---|
| Trigger | Admin reassigns a course from one Instructor to another or leaves it unassigned |
| Key derivation | UUIDv5 over the durable COURSE_OWNER_REASSIGNED AuditEvent and each recipient user ID |
| Verification | RED missing-key assertion then GREEN unit test; former and new owner keys are distinct |
| Current AST inventory | 35 direct calls; 9 explicit event_key; 1 prebuilt event; 25 neither |
| Boundary | Dedicated SQL Server replay, Browser retry/visual acceptance and external SMTP/inbox remain open |

The latest authoritative inventory is 163 distinct audited cases. Prior counts remain historical checkpoints.

## N-164 - password-reset token producer key adoption (2026-10-06)

| Field | Evidence |
|---|---|
| Trigger | A consumed PASSWORD_RESET token changes the user's password and auth_version |
| Key derivation | UUIDv5 over durable user ID and post-mutation auth_version |
| Verification | RED expected-key lookup failed; GREEN reset-token unit test found the persisted NotificationEvent |
| Current AST inventory | 35 direct calls; 10 explicit event_key; 1 prebuilt event; 24 neither |
| Verification | SQL Server disposable probe exercised normal and reset-token mutations; event/notification/email rows stayed 1 -> 1, 6 cases, 0 failed, 0 skipped; cleanup 0 |
| Boundary | Browser retry/visual acceptance and approved external inbox evidence remain open |

The latest authoritative inventory is 164 distinct audited cases. Prior counts remain historical checkpoints.

## N-165 - account-suspension security producer key adoption (2026-10-06)

| Field | Evidence |
|---|---|
| Trigger | Admin suspends an account and auth_version increments |
| Key derivation | UUIDv5 over durable user ID and post-suspension auth_version |
| Verification | RED expected-key lookup failed; GREEN unit test passed; SQL Server combined security probe replay kept event/notification/email rows at 1 -> 1, 9 cases, 0 failed, 0 skipped |
| Current AST inventory | 35 direct calls; 11 explicit event_key; 1 prebuilt event; 23 neither |
| Boundary | Browser retry/visual acceptance and approved external inbox evidence remain open |

The latest authoritative inventory is 165 distinct audited cases. Prior counts remain historical checkpoints.

| Field | Evidence |
|---|---|
| Trigger | User password mutation emits mandatory `SECURITY_PASSWORD_CHANGED` notification and email |
| Key derivation | UUIDv5 over durable user ID and post-mutation `auth_version`; each password mutation version is distinct |
| Verification | Unit key assertion passed; SQL Server probe reported `auth_version=2`, key present, event/notification/email rows `1 -> 1`, **3 cases, 0 failed, 0 skipped** |
| Cleanup | Disposable database removed; `audit_database_remaining=0`; port 5105 listener count 0 |
| Boundary | Current AST inventory has 30 direct calls with neither explicit `event_key` nor prebuilt event; Browser and approved external inbox remain open |

The latest authoritative inventory is **161 distinct audited cases**. Prior counts remain historical checkpoints.

## N-166 inventory update (2026-10-06)

| Producer boundary | Key basis | Evidence | Boundary |
|---|---|---|---|
| Role mutation | User ID + post-mutation `auth_version` + mutation kind | Unit GREEN for assign/update/revoke | No dedicated SQL replay in this increment |
| Admin course edit | Flushed `COURSE_ADMIN_EDIT` audit ID + recipient | Unit GREEN | No dedicated SQL replay in this increment |
| Lesson/course change requests | Persisted change-request ID + event type + recipient | API GREEN for submit/approve | Rejection and lesson-specific paths need broader replay |
| Malware rejection | Persisted file-revision ID + recipient | Unit GREEN for infected quarantine | New-revision and SQL/email replay remain open |

The latest authoritative producer inventory is **35 direct calls / 25 explicit keys / 1 prebuilt event / 9 neither**. The case register remains historical at 166 entries; this producer expansion does not close Browser, external delivery or remaining unkeyed boundaries.

## N-167 inventory update (2026-10-06)

The remaining producer branches are now covered: assessment-result notices use attempt/result transition identity; YouTube health notices use course/lesson/video/recipient identity; and Admin/instructor change-request routes use request/event/recipient identity. The latest AST inventory is **35 direct calls / 34 explicit keys / 1 prebuilt event / 0 neither**. This is source and focused-test evidence; SQL replay, Browser/CUA and external inbox evidence remain open.

## N-168 verification checkpoint (2026-10-06)

The full verifier ran with disposable SQL Server URLs and completed **1607 passed, 0 failed, 0 skipped**; the four SQL Server opt-in cases were executed rather than skipped. The database fixtures were removed after the run. This confirms the inventory and regression gate, but does not close Browser/CUA, external inbox, file/quarantine or historical disposition evidence.

## N-169 live delivery inventory update (2026-10-06)

The live SQL boundary currently contains **115 PENDING email deliveries** with no `FAILED` rows and no `background_jobs` rows; the oldest pending record is from `2026-09-19`. The notification event/in-app persistence path is present, but the deployment had no active worker and production defaulted to a mock transport. The corrected source now creates/claims an EMAIL job for due outbox rows, exposes a real SMTP adapter only when configured, fails closed otherwise, and marks stale pending backlog as `DEGRADED`. Live backlog was not drained because no approved SMTP destination exists.

## N-170 current verification boundary (2026-10-06)

Computer Use was revalidated against the live URL: no browser surface was exposed and direct IAB creation returned `Browser is not available: iab`. Therefore inventory rows requiring live UI interaction remain explicitly unverified. The current SQL-enabled aggregate completed **1612 passed, 0 failed, 0 skipped**, while the worker image built successfully but the live worker remained stopped because `MAIL_HOST` and `MAIL_FROM` are absent.

## N-171 historical duplicate disposition update (2026-10-06)

Read-only live SQL found 143 events, 168 notifications and 115 pending email deliveries. All events have a linked notification and all 143 `event_key` values are unique. Fourteen presentation-copy groups repeat recipient/title/body/role; no repeated `change_request_id` was found where that identity exists. Older action-URL and malware-rejection rows lack enough durable business identity to classify safely, so they remain preserved historical evidence rather than being deleted or collapsed.

## N-172 inventory update (2026-10-06)

The sampled Web notification inventory now maps `/auth/notifications` and `/student/notifications` success paths to the shared `success/data` contract, with legacy aliases retained for compatibility. Read, mark-all-read, dismiss and clear are covered in the same envelope correction. Focused API evidence is **16 passed** and focused frontend evidence is **7 passed**; broader Browser and cross-blueprint envelope coverage remains separate.

## N-173 verification update (2026-10-06)

The current source and inventory were included in a valid full run: **1613 passed, 0 failed, 0 skipped**, including 108 frontend tests and the SQL Server integration gates. No live database was used for the disposable migration/race databases; both were removed after verification.

## N-174 acceptance-scope decision (2026-10-06)

The owner confirmed that SMTP/inbox is not deployed and may be excluded from this acceptance cycle. Email-delivery rows remain an operational follow-up, not a Browser acceptance claim. The mandatory Browser/CUA gate remains open because no Browser surface is exposed; file chooser/quarantine cases therefore remain unverified.

## N-175 Browser role inventory evidence (2026-10-06)

Edge Browser execution covered Student, Instructor and Admin demo sessions. Student and Instructor login/logout success toasts rendered; Instructor notification inventory exposed 15 unread records, repeated `#70014` copies and mixed-language legacy text. Mark-all-read changed the UI to 0 unread with a success toast. Admin Operations showed live degraded email queue status and zero background-job counters; Student access to the Admin route returned a Vietnamese permission warning.

## N-176 file inventory boundary (2026-10-06)

The Student resource panel exposed four files and a clean PDF download completed through Browser Use. Live SQL has no current `PENDING` or `QUARANTINED` revision, only 123 `ACTIVE` and 7 `REJECTED`; a rejected-file URL was blocked by the Edge client before application response. The upload chooser was captured but file assignment was denied by Edge extension permission, so no upload/quarantine row is added to the Browser-passed inventory.

## N-177 Student notification inventory evidence (2026-10-06)


Student Browser inventory showed the notification panel with `0 mới`, filters for Tất cả/Chưa đọc/Khảo thí/Khóa học/Hệ thống, and exam-result/course/system records. The panel contains mixed-language legacy content and short hard-coded-looking messages; these remain inventory findings pending ownership/source mapping.
## N-178 Browser upload inventory evidence (2026-10-06)

The Instructor upload inventory now includes one clean, accepted course-image workflow: the chooser assigned `octopus_ai_icon.png`, the crop dialog was applied, and the UI confirmed the update. Live SQL recorded asset public ID `22F39CA6-09A9-478A-BB73-8E250FEAE622`, revision `150036`, `ACTIVE`/current, with `FILE_VALIDATION=PASS` and `MALWARE=PASS`. The rejected-file Browser path remains client-blocked before an application response; no PENDING/QUARANTINED denial row was created or claimed.
## N-179 rejected-file inventory classification (2026-10-06)

The sampled rejected asset is not present in the Student resource inventory: SQL Server links it to published course `SEXGAY` but to no lesson/resource row. Both the direct and course-scoped inline Browser routes were blocked with `net::ERR_BLOCKED_BY_CLIENT` before the application response, so its denial status cannot be added as a Browser-observed inventory result.
## N-180 authenticated rejected-file inventory boundary (2026-10-06)

The authenticated Instructor session could not add a rejected-file response to the Browser inventory: the Instructor download route with inline disposition was client-blocked before the app response. The session was restored to the course-management UI; no file data was exposed or released.
## N-181 Instructor system-category inventory evidence (2026-10-06)

The Browser inventory for the Instructor `Hệ thống` filter contains two visible records: one legacy `Thong bao bao tri dinh ky...` message and one Vietnamese malware-rejection message. Category filtering is working, while language consistency and historical producer ownership remain findings.
## N-182 Instructor assessment-category inventory boundary (2026-10-06)

The `Khảo thí` category currently has no visible records for Instructor1, and the UI reports that state explicitly. This is an honest empty inventory result, not evidence that all assessment producers are globally covered.
## N-183 Instructor course-category inventory evidence (2026-10-06)

The `Khóa học` filter contains 16 visible Instructor records. It includes course and lesson lifecycle notifications and the repeated `#70014` presentation family; this is direct UI inventory evidence supporting the historical duplicate/content findings.

## N-184 Admin broadcast validation inventory (2026-10-06)

The Admin governance page exposes the broadcast action and a form with required title/body fields, role audience options and notification categories. The empty and title-only submissions were rejected in the Browser before a durable write; the live SQL snapshot after the probe remained `143` events, `168` notifications, `115` pending email deliveries and `0` jobs. This inventories the validation surface, not the valid-broadcast recipient inventory.

## N-185 rejected-file inventory boundary (2026-10-06)

The live database contains seven `REJECTED` revisions, and a read-only join shows zero `lesson_resources` links for every one. The current inventory therefore has no user-facing resource entry through which Browser quarantine denial can be exercised. This is a data-availability limitation, not a pass for unsafe-file access control.

## N-186 rejected-file API inventory evidence (2026-10-06)

The sampled rejected asset is now correlated through an authenticated Instructor HTTP session: the download endpoint returns `403`, canonical `success:false`, code `FILE_INFECTED` and a non-technical rejection message. The Browser-facing inventory path is still unavailable because Edge intercepts the direct route.

## N-187 SMTP/inbox inventory scope (2026-10-06)

External SMTP delivery and inbox receipt are marked **scope-excluded by owner decision** for this cycle. The inventory retains outbox rows and health state as observed runtime data, but does not claim external delivery coverage.

## N-188 historical duplicate reclassification (2026-10-06)

The duplicate inventory is now split into 12 business-correlated repeated-copy groups and 2 unkeyed legacy groups (17 rows). “Repeated presentation copy” is not synonymous with duplicate delivery; known course/file transitions have distinct request/revision identities. The two unkeyed groups remain **OPEN**.

## N-189 Browser quarantine-override inventory (2026-10-06)

The primary-admin security page exposes a quarantine-override tool with three required inputs: File Asset ID, security justification and Super Admin password. The empty-submit path returned the expected client validation message and the dialog was canceled. No successful override, release or new audit record is included in this inventory.

## N-190 focused quarantine backend inventory (2026-10-06)

The focused regression inventory covers two override-specific backend tests and one fail-closed authorization test: 3 passed in total, with 45 unrelated tests deselected. The result confirms the tested guardrails only; it does not inventory a successful release.

## N-191 Browser console inventory (2026-10-06)

The current Browser session produced no application-level console error during the inspected flows. One existing Tailwind CDN production warning was observed and is tracked as an environment/frontend hygiene observation, not as proof of notification delivery.

## N-192 legacy identity inventory (2026-10-06)

For the two unresolved groups, the stored identity fields are limited to recipient/role/title/body plus a generic action URL. The event-level business fields are absent: `correlation_id` and `actor_user_id` are NULL, while `target_id` identifies the recipient rather than a course, lesson or request. No matching audit event was found in the event window.

## N-194 rejected-file Browser inventory boundary (2026-10-06)

The rejected-file access case remains **BLOCKED ENVIRONMENT** in Browser: Edge intercepted the URL with `ERR_BLOCKED_BY_CLIENT`, and IAB was unavailable. No application status, response body or file bytes were inferred from this observation.

## N-195 download-route family inventory (2026-10-06)

The block is route-family wide in the tested surface: both `/instructor/files/.../download` and `/api/files/.../download` were intercepted by Edge before application response. No Browser response-level denial is counted.
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

## N-202 current static message inventory correction (2026-10-06)

A read-only parser over the current `frontend/**/*.js` found 382 `UI.showToast(` callsites across seven files: 213 direct quoted literals, 73 template-literal calls and 96 other dynamic expressions; 201 unique direct literal messages. The heuristic language split is VI 181 / mixed 25 / EN-or-technical 7 for literal callsites and VI 172 / mixed 24 / EN-or-technical 5 for unique literals. These are static callsite figures, not a complete backend/API/inline/modal catalog.

## N-203 current Student result-CTA identity check (2026-10-06)

After a real Browser logout/login with the Student demo account, the Dashboard grade CTA pointed to attempt `db76cdce-bef6-470d-be11-7d35cc9ab96b`; the result page rendered `1 / 16`, and live SQL mapped the attempt to `student1@pwd301.local`. A preceding stale tab displayed a different identity and an incompatible attempt CTA until the session was explicitly reset; this remains an auth/navigation boundary, not a release pass.

## N-204 current Student notification-center inventory (2026-10-06)

The clean Student notification center rendered 13 records and 0 unread; the `Khảo thí` filter rendered 7. The live catalog still contains one unaccented ASCII maintenance message and two test-like messages, so language/data normalization remains open. No notification mutation was submitted.

## N-206 current producer-key inventory (2026-10-06)

## N-210 fresh Student filter-branch inventory (2026-10-06)

The live Student Browser notification dropdown was reopened and exercised without submitting a mutation. `Khóa học` rendered **2** records; `Hệ thống` rendered **4** records, including the legacy ASCII maintenance text `Thong bao bao tri dinh ky...` and test-like entries `heo peppa caccaccac` and `bucutaodi thật là bá khí`; `Chưa đọc (0)` rendered the explicit empty state `Không có thông báo nào` / `Bạn đã xem hết các thông báo trong mục này.`. This confirms filter-specific data and empty-state behavior while preserving the existing language/data-normalization finding.

## N-211 Instructor file-chooser inventory boundary (2026-10-06)

After a real Instructor demo login, the course-authoring page exposed two cover-upload controls. Clicking both left the Browser page unchanged, with no native file dialog visible in the Computer Use surface and no file selected or persisted. This adds an observed upload entry point but leaves chooser acceptance **BLOCKED ENVIRONMENT / UNVERIFIED**; no course, file, notification or audit row was mutated.

The current AST inventory contains 35 direct `dispatch_notification()` callsites: 34 explicit `event_key` calls, 1 prebuilt event and 0 unkeyed calls. This is a static completeness result only; semantic key correctness and every runtime retry/race path remain separate test cases.

## N-212 Admin role notification filter inventory (2026-10-06)

A real Admin demo login opened the live notification center. The default `Chưa đọc (0)` view rendered the explicit empty state; `Tất cả` rendered **15** records, `Khóa học` rendered **10**, and `Hệ thống` rendered **3**. The system-filter records included the legacy ASCII maintenance message, a backup-completed message and a security-login-warning message. No delete or other notification mutation was submitted; the Admin session was logged out and the Student demo account was restored. This adds role-specific filter coverage while preserving the existing legacy/data-quality finding.

## N-213 Instructor role notification filter inventory (2026-10-06)

A real Instructor demo login opened the live notification center. `Tất cả` rendered **18** records, `Khóa học` rendered **16**, `Hệ thống` rendered **2**, and `Khảo thí` rendered the explicit empty state; `Chưa đọc (0)` also rendered the explicit empty state. The system subset contained the legacy ASCII maintenance record and the rejected-malware upload notification. No delete or other notification mutation was submitted; the Instructor session was logged out and the Student demo account was restored. This adds the missing Instructor role/filter catalog while preserving the language/data-quality finding.

## N-214 current notification API regression inventory (2026-10-06)

The focused current-worktree command `python -m pytest -q tests/api/test_notification_api.py` completed with **16 passed in 10.59s**, exit code `0`. This confirms the covered REST/session lifecycle, filtering, dismissal, preferences, broadcast/idempotency and envelope tests in the test file; it does not establish the unrun outage/status-code branches, every producer, Browser rendering or external SMTP/inbox receipt.

## N-215 current Admin lesson-flag notification inventory (2026-10-06)

The focused command `python -m pytest -q tests/api/test_admin_lesson_flag_notification.py` completed with **9 passed**, exit code `0`. The suite covers durable Admin lesson-flag audit plus owner notification, REST/Web idempotency replays, changed-payload rejection and rollback when the notification sink fails. This is isolated API/DB business-flow evidence, not a claim of complete live Admin Browser producer coverage.

## N-216 current notification service/security/frontend regression inventory (2026-10-06)

Fresh focused checks completed without skips: `python -m pytest -q tests/unit/test_notification_service.py` returned **15 passed in 8.68s**; `python -m pytest -q tests/security/test_notification_idor.py` returned **7 passed in 4.06s**; and `node --test tests/frontend/notification_ui_contract.test.js tests/frontend/router_navigation.test.js tests/frontend/topbar_navigation.test.js` returned **18 passed, 0 failed, 0 skipped**. These close the named unit, IDOR and frontend-contract scopes only; they do not establish full producer/business-role or external delivery coverage.

## N-217 current producer/business-flow regression inventory (2026-10-06)

Fresh focused checks completed without skipped tests: `tests/api/test_admin_backend_completion.py` returned **16 passed in 11.25s**; `tests/api/test_admin_subroles_and_enhancements.py` returned **5 passed in 4.12s**; the selected course-changeset cases returned **2 passed, 10 deselected in 1.98s**; and the selected lesson-change cases returned **5 passed, 3 deselected in 4.37s**. The deselected cases are not counted as passes. These results strengthen approval/rejection, reassignment, broadcast, sub-role/RBAC, changeset and lesson-review producer coverage, but do not close every producer, live Browser replay or external delivery gate.

## N-218 current Browser timing replay inventory (2026-10-06)

Fresh Edge Computer Use replay used a clean logged-out boundary, the visible Instructor demo login, and the real Instructor notification popover. Login reached `#/instructor/dashboard` with the correct instructor identity. The first captured transition contained the login-success toast; the following settled dashboard state showed the full Instructor dashboard. No skeleton was visible in the captured post-login accessibility states, so this replay does not prove a sub-render shorter than the observation boundary.

Opening the notification popover initially showed `Thông báo 0 mới`, `Chưa đọc (0)` and the explicit empty-state text. That was treated as a legitimate unread-filter result, not as an all-items false empty state. Selecting `Tất cả` then showed **18** Instructor notifications: **16** `Khóa học` rows and **2** `Hệ thống`/security rows; the `Khảo thí` filter remained legitimately empty. The run performed no delete, upload, broadcast or other business mutation, then logged out and restored the clean Student1 dashboard. This closes the captured Instructor login-to-filter timing scope only; all-role timing breadth, file/quarantine UI and external SMTP/inbox remain open.

## N-219 current Guest notification boundary inventory (2026-10-06)

Fresh Edge logout through the real account menu returned to `#/auth`; the unauthenticated page exposed no topbar notification control. A direct Browser navigation to `/auth/notifications` was blocked by Edge with `net::ERR_BLOCKED_BY_CLIENT` before an application response, so this is an environment boundary rather than a Browser-observed 401. The unauthenticated 401 remains covered by the focused API/session regression, but the Guest UI error mapping is **UNVERIFIED**, not a pass. No data mutation occurred, and Student1 was logged in again with the correct dashboard identity.

## N-220 focused notification API rerun inventory (2026-10-06)

Fresh command `python -m pytest -q tests/api/test_notification_api.py` completed with **16 passed in 10.15s**, exit code `0`, with no skipped tests. This revalidates the covered lifecycle, filtering, dismiss/read, preferences, broadcast/idempotency, malformed-payload, role-filter, canonical-envelope and session/IDOR cases; it does not establish unrun 422/429/502/503 branches, every producer, Browser Guest presentation or SMTP/inbox receipt.

## N-221 current disjoint no-skip verification inventory (2026-10-06)

The full wrapper was run with `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\verify.ps1` and exited `0`, but its embedded pytest section reported **1609 passed, 4 skipped** because the wrapper does not inject the opt-in SQL Server URLs. The exact helper `PYTHONPATH=src python docs/audits/PWD301_NOTIFICATION_AUDIT_2026-10-04_EVIDENCE/grading-runtime-probe.py sql-gates` then ran the complete `tests/integration` partition with the two disposable SQL databases and returned **17 passed in 24.58s**, followed by `audit_database_remaining=0` for both databases. The disjoint union is therefore **1613 passed, 0 failed, 0 skipped** (the 13 non-SQL integration cases from the first run are not double-counted). This is an automated verification result only; Browser file/Guest boundaries, historical disposition and SMTP/inbox remain separately assessed.

## N-222 disposable producer/idempotency replay inventory (2026-10-06)

On the exact disposable SQL Server audit database, with the audit Flask server isolated on port 5105, the notification-copy visibility/event-key conflict probe passed **2 cases**; the second demo-seed idempotency probe passed **1 case** with unchanged counts and zero new notices/audits; enrollment producer key replay passed **3 cases** with event/notice rows remaining `2 -> 2`; course lifecycle key replay passed **4 cases** with rows remaining `1 -> 1`; and password-change, reset-token and suspension security-key replays passed **9 cases**, including email outbox rows remaining `1 -> 1`. All probes reported `failed_expectations=0` and `skipped=0`; the audit database cleanup returned `audit_database_remaining=0`. This strengthens SQL/API producer idempotency only and does not prove Browser rapid-retry visuals, every producer, historical repair or external SMTP/inbox.

## N-223 disposable lesson-flag idempotency inventory (2026-10-06)

The isolated Admin lesson-flag REST replay passed **3 cases** with no skips: first request `200` and `idempotent_replay=false`; exact retry `200` and `idempotent_replay=true`; changed payload under the same key `409 CONFLICT`. SQL deltas were exactly **1 audit, 1 event and 1 owner notification**. The disposable audit database was removed with `audit_database_remaining=0`; no live lesson or notification history was touched. This closes only the named moderation producer replay scope, not Browser rapid-click visuals or every producer.

## N-224 notification HTTP status applicability inventory (2026-10-06)

The current notification REST blueprint has explicit `200` success returns for list, unread-count, read, mark-all, dismiss/delete, preferences, broadcast and failed-email retry. Its reachable exception families map validation to `400`, authentication to `401`, authorization to `403`, missing resources to `404`, and changed idempotency payloads to `409`; the focused API/session evidence covers the named branches. No notification route emits `201` or `204`, and the source has no notification-specific `422` or `502` mapping. Global `429` classes are email/AI/curriculum rate limits and global `503` classes are AI/maintenance, not demonstrated notification-route outcomes. Unexpected `500`, outage/maintenance injection and retry-after behavior remain unrun; this is a contract applicability finding, not a pass for those failure injections.

## N-225 focused notification HTTP status regression inventory (2026-10-06)

The fresh command `PYTHONPATH=src python -m pytest -q tests/api/test_notification_api.py tests/security/test_notification_idor.py` returned **23 passed in 9.89s**, exit code `0`, with no skipped tests. Assertions in this run cover notification success/lifecycle responses (`200`), malformed or invalid mutation input (`400`), anonymous access (`401`), IDOR/non-admin denial (`403`) and changed idempotency payload (`409`). This rerun does not add a notification-specific `404`, `422`, `429`, `500`, `502` or `503` injection; those remain explicitly unverified rather than inferred from the green focused run.

## N-226 current Student Browser notification-surface replay (2026-10-06)

The live Edge Computer Use tab remained available at the authenticated Student dashboard for `Lê Hoàng Long`. Opening the real notification popover showed `Thông báo 0 mới`, `Chưa đọc (0)`, the role label `Học viên`, and **13** visible notification records across the category filters. The popover was then closed through its visible control; no read, dismiss, delete, upload or other business mutation occurred. This is a current Browser-surface and Student rendering observation, not proof of all-role timing, keyboard accessibility, file chooser behavior or SMTP/inbox delivery.

## N-227 isolated notification 404 contract probe (2026-10-06)

An isolated Flask test-client probe on in-memory SQLite authenticated a disposable Student and exercised missing and malformed notification IDs for mark-read and delete. All three requests returned **404** with the same safe envelope shape: `success=false`, `data=null`, `error.code=RESOURCE_NOT_FOUND`; no live database or notification history was touched. This closes the sampled notification `404` mapping only; it does not infer `404` coverage for unrelated resources or unrun `422/429/500/502` injections.

## N-228 notification maintenance 503 and retry-after regression (2026-10-06)

The existing E2E command `PYTHONPATH=src python -m pytest -q tests/e2e/test_admin_ops_lifecycle_e2e.py` returned **5 passed in 4.37s**, exit code `0`, with no skipped tests. Its disposable maintenance window asserted Student `GET /api/notifications/unread-count` returns **503**, error code `MAINTENANCE_MODE_ACTIVE` and `Retry-After: 1200`, then returns `200` after maintenance ends. This closes the sampled notification maintenance/`503`/`Retry-After` path; unexpected `500` and notification-specific `422/429/502` injections remain unrun.

## N-229 isolated notification 500 and 429 fault-injection contract probe (2026-10-06)

In the same isolated Flask test-client pattern on in-memory SQLite, a patched notification list dependency raised a generic runtime fault and the route returned **500** with `success=false`, `data=null`, `error.code=INTERNAL_ERROR` and a user-safe message; a patched failed-email retry dependency raised `EmailRateLimitExceededError` and the admin route returned **429** with `error.code=RATE_LIMIT_EXCEEDED` and `Retry-After: 60`. Both responses were produced without live data access. This closes the sampled notification `500/429` error-envelope contract; no notification-specific `422` or `502` mapping/injection exists in the current route set.

## N-230 notification 422/502 applicability boundary (2026-10-06)

A read-only source/applicability check confirms that notification validation raises the shared `ValidationError` family mapped to `400`; the notification blueprint has no `422` or `502` return, and the global domain-handler table has no notification-specific mapping for either status. Therefore `422` and `502` are **not applicable at the current Flask notification boundary**, rather than skipped notification outcomes. A reverse proxy or external upstream could produce `502` outside this application boundary, but that infrastructure path is not part of the current notification API contract and was not claimed as tested.

## N-231 corrected AST producer inventory (2026-10-06)

A corrected read-only AST pass over `src/pwd301` classified the actual dispatcher keywords (`event_key` and prebuilt `event`) and found **35** direct `dispatch_notification()` callsites: **34** explicit deterministic-key calls, **1** prebuilt-event call at `src/pwd301/services/course_service.py:286`, and **0** without either identity. An earlier local probe looked for the obsolete keyword `notification_event_id` and was rejected as an audit-harness classification error; no product source changed. This closes only static producer-count accuracy; semantic key correctness and runtime retry/race coverage remain separate.

## N-232 fresh Student Browser category-filter replay (2026-10-06)

With the authenticated Edge Computer Use tab still on the Student dashboard, the real notification popover was opened and its read-only category buttons were exercised. The accessibility tree showed `Tất cả` with **13** records and `Chưa đọc (0)`; `Khảo thí` rendered **7** records, `Khóa học` rendered **2**, and `Hệ thống` rendered **4**. No delete, dismiss, mark-read, refresh, upload or other business mutation was invoked. This verifies the current Student filter rendering only; it does not close the broader all-role semantic producer, rapid-retry, keyboard, file-chooser or SMTP/inbox gates.

## N-233 repeated Instructor file-chooser boundary (2026-10-06)

The live Edge Browser was logged in as the demo Instructor, opened the OPS401 lesson studio and clicked the real `btn-choose-doc-file` control. The click returned without a native chooser or a selectable file surface; `cua.getState({emit:false})` still reported `apps=[]` and only the Edge Browser. The accessibility tree remained unchanged with one existing clean attachment and no upload placeholder. This is a repeated environment boundary, so file selection, rejected-file response and quarantine release remain **UNVERIFIED/BLOCKED ENVIRONMENT**, not passes; no product or live business data was changed.

## N-234 broader producer-service regression group (2026-10-06)

The fresh isolated command `PYTHONPATH=src python -m pytest -q tests/unit/test_course_service.py tests/unit/test_enrollment_service.py tests/unit/test_user_service.py tests/unit/test_lesson_service.py` returned **90 passed in 59.65s**, exit code `0`, with no skipped tests. This strengthens fixture-level regression evidence around course, enrollment, user/role and lesson services that contain notification producers. It is not a claim that all 35 dispatcher callsites, every role, or every live Browser/API/DB/user-result chain has been replayed.

## N-235 assessment/file producer-service regression group (2026-10-06)

The fresh isolated command `PYTHONPATH=src python -m pytest -q tests/unit/test_attempt_service.py tests/unit/test_attempt_submission_service.py tests/unit/test_file_service.py tests/unit/test_malware_scan_service.py` returned **38 passed in 26.90s**, exit code `0`, with no skipped tests. This adds fixture-level regression evidence for attempt/assessment and file/security paths that can produce user-facing or persisted notifications. It does not establish complete producer coverage or Browser file-selection/quarantine acceptance.

## N-243 current dispatcher identity inventory (2026-10-06)

The independent current-source AST scan reports 35 direct dispatcher calls, partitioned as 34 explicit `event_key`, 1 prebuilt `event` and 0 missing identity. No Python parse errors were observed. This is a static inventory checkpoint and not a proof of semantic key uniqueness or live fan-out behavior.

## N-242 producer-heavy service regression group (2026-10-06)

Fresh producer-heavy service verification returned **64 passed**, exit code `0`, with no skips across authorization, notification core, email/outbox, completion and instructor-application services. This expands fixture coverage without claiming all dispatcher callsites or live role/result chains.

## N-241 current Admin lesson-flag reconciliation (2026-10-06)

The current Admin lesson-flag producer/API inventory is consistent with the shared service signature. Its dedicated fresh regression returned **9 passed**, exit code `0`, with no skips. This supersedes the historical RCA-040/RCA-027 interpretation for the current source while preserving the earlier observation for audit traceability.

## N-240 fresh API and frontend notification regression (2026-10-06)

Fresh API/IDOR verification returned **23 passed in 15.20s**, exit code `0`, with no skips; the full frontend Node command returned **108 passed, 0 failed, 0 skipped, todo 0**, exit code `0`. This strengthens the current notification transport, authorization and UI contract inventory without claiming all producer chains or external mail delivery.

## N-239 fresh Admin notification filter matrix (2026-10-06)

The fresh Admin Browser session exercised the visible filters without mutation: `Tất cả=15`, `Chưa đọc (0)`, `Khảo thí=1`, `Khóa học=11` and `Hệ thống=3`. The 15-record total includes 11 course, one assessment and three system/security records. This corrects the interpretation boundary of N-237, whose initial 3-record view was the system category.

## N-237 fresh Admin notification-center replay (2026-10-06)

The fresh Edge Admin session rendered `Thông báo 0 mới`, `Chưa đọc (0)`, role `Quản trị viên`, and **3** persisted records: maintenance, completed backup and abnormal administrator-login security warning. The list was read-only; no notification mutation was invoked. This adds current Admin rendering evidence but not complete Admin producer/broadcast coverage.

## N-238 fresh Guest protected-route boundary (2026-10-06)

After Admin logout, Edge navigation to `#/student/notifications` redirected to `/auth`. The Guest AX tree contained the login form and no authenticated topbar notification control. This verifies the client route boundary only; API unauthenticated `401` evidence remains separate. SMTP/inbox delivery is explicitly out of scope.

## N-250 YouTube Browser/UI ownership gap (2026-10-06)

| Surface | Observed | Ownership result |
|---|---|---|
| Instructor course management | No scan-video button/control visible | No demonstrated UI owner for `COURSE_LESSON_VIDEO_BROKEN` scan |
| Lesson Studio link input | Invalid URL toast rendered; input was cleared without save | FE validation owner exists for add-link boundary |
| `ApiClient.scanCourseVideos` | Definition exists, no frontend caller found | API capability is currently orphaned from a visible UI action |

## N-249 disposable YouTube route/API extension (2026-10-06)

The disposable inventory now includes route boundary evidence: Guest/unauthenticated scan was rejected with 401; the authenticated course owner received a 200 success payload with one broken report. Durable counts remained one event and one notification across route/service replays. Browser UI rendering is still not claimed.

## N-248 disposable YouTube producer service/DB replay (2026-10-06)

The disposable service/DB replay now covers the YouTube producer's valid, network-error and broken-video branches. The broken branch created one `COURSE_LESSON_VIDEO_BROKEN` event and one owner notification; exact replay preserved both counts. This adds current scoped runtime evidence, while the Instructor route response and Browser-visible result remain separate fields marked open.

## N-247 YouTube broken-video producer coverage gap (2026-10-06)

| Producer | Source | Route | Recipient | Key shape | Current verification |
|---|---|---|---|---|---|
| `COURSE_LESSON_VIDEO_BROKEN` | `services/youtube_validator_service.py` | Instructor `POST /courses/<course_id>/scan-videos` | Course owner/instructor | UUIDv5(course, lesson, video ID, instructor) | **UNVERIFIED**: no matching test file or live business replay |

## N-246 producer-key semantic-shape AST inventory (2026-10-06)

Static producer inventory result: 35 direct dispatcher calls, 34 explicit keys with durable-identity candidates, no random/clock-derived key expression, no constant/unclassified key expression, and one prebuilt event. Helper examples use persisted audit ID, change-request ID, file-revision ID, enrollment ID, attempt ID or user `auth_version`; runtime semantic correctness remains unverified per producer.

## N-245 fresh Student notification-center content/filter replay (2026-10-06)

Fresh Browser inventory observation: Student notification center showed 13 records in `Tất cả`, split into 7 `Khảo thí`, 2 `Khóa học` and 4 `Hệ thống`; `Chưa đọc (0)` was visible. The same read-only view contained one unaccented Vietnamese system message and two semantically poor seeded messages (`heo peppa caccaccac`, `bucutaodi thật là bá khí`). These are current rendered-content observations; they are not counted as new distinct backend events without row-level SQL correlation.

## N-244 grading/regrade producer-service regression (2026-10-06)

The fresh isolated command `PYTHONPATH=src python -m pytest -q tests/unit/test_grading_service.py tests/unit/test_regrade_service.py` returned **25 passed in 26.49s**, exit code `0`, with no skipped tests. The covered grading/regrade service paths add current fixture-backed producer evidence; all-callsite semantic identity, every role, rapid retry/race behavior and full Browser/API/DB/user-result replay remain separate gates.

## N-236 fresh Instructor notification-center replay (2026-10-06)

The same live Edge session rendered the Instructor lesson studio for `TS. Nguyễn Văn A`. Opening the real notification center showed `Thông báo 0 mới`, `Chưa đọc (0)`, role `Giảng viên`, and **2** persisted records: one system maintenance item and one `BẢO MẬT` item stating that `X_SENTINEL_VIBECODE_BASELINE_V2.zip` was rejected and quarantined as `ZIP-Embedded-Executable`. The popover was inspected and left without delete, dismiss, mark-read or refresh mutation. This verifies Instructor rendering of a persisted security notification, not the blocked native file-selection/upload chain that would create a new one.

## N-251 frontend notification mechanism inventory (2026-10-06)

| Mechanism | Current static count | Scope note |
|---|---:|---|
| `UI.showToast` invocations | 383 | 214 quoted literals, 73 template literals, 96 other dynamic expressions; 202 unique quoted literal payloads |
| `UI.alert` | 2 | Separate alert surface; not included in the toast count |
| `UI.confirm` / `UI.prompt` | 30 / 8 | Confirmation and input surfaces require separate catalog and accessibility checks |
| Native `window.confirm` | 1 | Legacy fallback remains outside the shared UI abstraction |
| Native `window.alert` / `window.prompt` | 0 / 0 | No native alert or prompt callsites found |
| `aria-live` / `role="alert"` | 6 / 4 | Static markup only; announcement timing was not measured |
| `<dialog>` | 0 | No native dialog element found |

The scan covered 10 frontend JavaScript files and excluded five `UI.showToast` guard/type-check references from the invocation count. This is a current static inventory, not proof of complete semantic message ownership, API status mapping, retry convergence or Browser coverage. SMTP/inbox remains explicitly **OUT OF SCOPE**.
## N-252 producer execution inventory correction (2026-10-06)

The focused coverage run mapped all 35 direct `dispatch_notification()` callsites to executed lines: **35 covered, 0 uncovered**. The evidence set consisted of 312 passing tests, 6 additional passing prerequisite/revision tests, and three passing disposable probes for prerequisite rejection, rejected file revision and YouTube broken-video/replay behavior; none skipped or failed. This upgrades the producer inventory from static identity presence to tested line execution, but the inventory still cannot claim complete semantic role/message/retry coverage from coverage alone.
## N-253 Browser auth-error inventory checkpoint (2026-10-06)

| Surface | Browser result | Ownership/accessibility boundary |
|---|---|---|
| Invalid login | One visible `#auth-error-alert`: `Email hoặc mật khẩu không chính xác.`; URL remained `/auth` | Inline auth owner, not shared toast |
| Persistence | Still visible after the approximately 6.45-second interaction/observation sequence | No timeout behavior was observed for this error path |
| Semantics | DOM had no `role` and no `aria-live` | Screen-reader announcement is not established |

This is one real Browser failure-path sample and does not replace the full role/API/error matrix.
## N-254 Browser file-chooser inventory checkpoint (2026-10-06)

| Surface | Observation | Status |
|---|---|---|
| Visible document chooser | `#btn-choose-doc-file` was present and clicked through the supported Browser API | PASS, control discoverability only |
| File chooser event | No event arrived before the approximately 3-second timeout; debugger detached afterward | BLOCKED ENVIRONMENT |
| File selection/upload | No selected file, upload request, or persisted mutation was confirmed | UNVERIFIED, not a pass |
| Browser/native surface | `apps=[]`; only Edge remained in inventory | Environment limitation |
## N-255 producer role/category inventory (2026-10-06)

| Dimension | Current result | Interpretation |
|---|---:|---|
| Direct producer callsites | 35 | All have line-execution evidence from N-252 |
| Explicit deterministic event key | 34 | One additional callsite passes a prebuilt event |
| Missing both key and prebuilt event | 0 | Identity presence is covered, semantics remain separate |
| Literal category | COURSE 20, SECURITY 6, SYSTEM 8 | One category is dynamic |
| Concrete target role | INSTRUCTOR 13, STUDENT 2, ADMIN 2 | 17 callsites explicitly scope a role |
| Missing/`None` target role | 18 | Broad/unscoped behavior must be checked producer by producer |

The inventory also found one dynamic event-type assessment path. It does not infer that a missing target role is wrong; it records the exact boundary for role-semantic verification.
## N-256 focused role/retry inventory checkpoint (2026-10-06)

| Runtime assertion | Result |
|---|---|
| Exact event-key replay and fan-out count | PASS, focused |
| Changed payload under reused key | PASS, conflict rejected |
| Multi-role target isolation | PASS, focused |
| Enrollment Student/Instructor notification identity | PASS, focused |
| Course lifecycle and owner-reassignment recipient keys | PASS, focused |

The command returned 8 passed, 0 failed and 0 skipped. It does not cover every producer or every timeout/cancel/race ordering.
## N-257 historical notification approval packet (2026-10-06)

The read-only SQL Server recheck records 17 exact unresolved rows: 13
`LESSON_CHANGE_REQUEST` events `50002–50014` and four
`COURSE_CHANGE_APPROVED` events `60002–60004`, `90006`. Each event has exactly
one notification and one outbox row, with unique event keys, so the evidence is
repeated presentation copy rather than proven duplicate delivery. Both groups
lack a deterministic durable business identity; the stale approval CTA UUID is
absent from the current course table. No append-only history was mutated. See
the [approval packet](09_HISTORICAL_NOTIFICATION_APPROVAL_PACKET.md); owner
mapping, approval and disposable rehearsal remain open. SMTP/inbox is
**OUT OF SCOPE**.
## N-258 Browser file chooser recheck (2026-10-06)

The Edge surface was present and Lesson Studio rendered the document chooser,
but the supported `filechooser` wait/click flow timed out again after 5 seconds
and reset the Browser session. The harmless fixture was not selected and no
upload request or durable mutation was observed. File chooser, upload,
quarantine and rejected-file Browser response remain **BLOCKED ENVIRONMENT /
UNVERIFIED**.
## N-259 fresh Instructor category inventory (2026-10-06)

The live Instructor popover was filtered read-only. `Khóa học` contained 16
cards, including two `Đợt cập nhật khóa học #70014 cần chỉnh sửa lại` copies
with different reasons, a current `CS201` notice and the historical lesson
approval copy. `Hệ thống` contained the mixed-language maintenance message
`Thong bao bao tri dinh ky` / `He thong PWD301...` and the Vietnamese rejected
file notice. The popover was closed without read/delete mutation. This extends
Browser content evidence but leaves catalog normalization and global producer
coverage open.
## N-260 producer role-view refinement (2026-10-06)

Static follow-up inspected the 18 callsites without a concrete target role. All
18 pass an explicit recipient user, so the inventory does not claim recipient
fan-out leakage. However, the shared query includes NULL `target_role` rows in
any selected role view for that account; Instructor/Admin-specific CTAs in this
set therefore still require individual multi-role verification. Security and
role-change events are plausible account-wide cases, while prerequisite,
review, intervention, application and YouTube producers remain open.
## N-261 live multi-role role-filter evidence (2026-10-06)

The Admin demo account has three active roles. A read-only JWT replay returned
the same public notification `d553d1ec-547c-4ebc-889d-7c91e274229e` with
`target_role=null` and Admin review CTA `#/admin/change-requests/review?id=50002`
for all filters `ADMIN`, `INSTRUCTOR` and `STUDENT`, each HTTP 200. This is
same-user role-view contamination/CTA mismatch; it is not evidence of another
user receiving the row. No notification state changed.
## N-262 notification schema-contract inventory (2026-10-06)

Live SQL Server confirms migration head `b3c4d5e6f7a9`, column
`notifications.target_role`, index `ix_notifications_user_role_unread` and
CHECK `ck_notifications_target_role`. The canonical database dictionary omits
these objects, so the notification role-filter contract is not represented in
the stated schema source of truth. This is a contract/documentation finding,
not a live data mutation.
## N-263 role-test coverage boundary (2026-10-06)

The focused unit/API role command returned **3 passed, 0 failed, 0 skipped**.
Coverage includes explicit target-role isolation and invalid-filter validation,
but the NULL-role case is deliberately modeled as global and has no CTA/route
compatibility assertion. This explains why the live Admin multi-role result in
N-261 is not caught by the current tests.
## N-264 cross-user isolation recheck (2026-10-06)

Student1's valid `role=STUDENT` notification list returned HTTP 200 with zero
matches for the Admin-review CTA; `role=INSTRUCTOR` and `role=ADMIN` were
rejected HTTP 400 as actor-ineligible. No cross-user notification leak was
observed.
## N-265 route-compatibility inventory (2026-10-06)

Notification UI handlers do not inspect `target_role` before routing: the
stored `action_url` is passed to the SPA router. A fresh Edge tab opened
`#/admin/change-requests/review?id=50002` from the current Instructor-only
session and rendered the Vietnamese Admin-access warning before returning to
the Instructor dashboard. This is direct Browser evidence of an incompatible
CTA presentation/guard path, not a cross-user leak or data mutation. The
multi-role auto-switch branch remains a separate source/HTTP boundary.
