# Hướng khắc phục và kiểm thử toàn diện PWD301

**Ngày:** 03/10/2026, Asia/Bangkok.  
**Trạng thái:** kế hoạch xử lý dựa trên audit; chưa sửa sản phẩm.  
**Danh mục lỗi và bằng chứng:** [Báo cáo lỗi](BAO_CAO_TOAN_BO_LOI_PWD301_2026-10-03.md).

**Mục tiêu:** sửa nguyên nhân gốc của từng lỗi được xác nhận, bảo toàn điểm/lịch sử/quyền/kiểm duyệt, nghiệm thu cả API và thao tác người dùng. Không dùng kết quả một nhóm test để chứng nhận toàn bộ nghiệp vụ.

**Kiến trúc:** giữ Flask headless REST/session API, SPA hiện hành, SQL Server và các service có sẵn. Resolve resource một lần, authorize theo action trước mọi nhánh, mutation trong transaction có kiểm tra trạng thái/version. Frontend trình bày dữ liệu và trạng thái từ backend, không tự tạo điểm/quyết định học vụ.

**Công nghệ:** Python/Flask/SQLAlchemy/Alembic, SQL Server DATETIME2/ROWVERSION, JavaScript SPA, pytest và Node test runner; browser Edge để nghiệm thu. Không cần thêm infrastructure cho các sửa lỗi đã xác định.

**Nguồn chuẩn:** mục 2 báo cáo danh mục; đặc biệt GRADE-001/002, ATTEMPT-003..007, REGRADE-003/004, FILE-001/005, AUDIT-002/003, OPS-001 và permission matrix. Người triển khai đọc source/spec cùng nhau trước sửa.

## 1. Ràng buộc và điều kiện bắt đầu

1. Snapshot HEAD, diff và trạng thái database/runtime trước sửa. Workspace có nhiều thay đổi chưa commit; không reset/checkout đè để lấy baseline. Nếu tách worktree, phải có cách mang đúng thay đổi liên quan để không audit một phiên bản nhưng sửa phiên bản khác.
2. TDD: mỗi lỗi viết test bảo vệ hành vi mong muốn, chạy fail trên source hiện tại, sửa nhỏ nhất, chạy xanh test đó và tests vùng ảnh hưởng. Script repro audit là bằng chứng khởi đầu, chưa thay regression tests chính thức.
3. Session web giữ CSRF; REST giữ JWT; suspended/deactivated bị chặn. Không lưu JWT vào localStorage hoặc giả phiên người dùng thật.
4. Resource authorization trước no-op, đọc private, ghi và retry; không sửa theo dạng UUID/numeric hoặc chỉ ẩn nút UI.
5. Không thay snapshot câu hỏi/đáp án lịch sử. Grade/result/history và required audit cùng transaction; revision/regrade giữ dấu old/new/reason/actor.
6. Server quyết định thời gian/deadline, lease, thứ tự autosave và submit idempotent. Không sửa bảng điểm bằng thay đổi cách chấm hoặc deadline ngoài phạm vi.
7. Không mở quyền Admin vô điều kiện; can_manage broad predicate không thay guard theo action. Chi tiết kết quả cá nhân và content override cần quy trình có lý do/audit/thông báo đúng spec.
8. File PENDING/QUARANTINED/ERROR không được student xem/tải; video `<1 GB`; reauth giải phóng cách ly vẫn giữ nguyên.
9. Không phục hồi standalone Question Bank/AI draft routes đã gỡ ở TASK-078; giữ exam authoring và lịch sử revision còn phục vụ bài thi.
10. Không sửa migration đã áp dụng hoặc tạo schema copy ngoài Database Architecture. Nếu cần migration mới, kiểm thử trong database thử có backup/restore; không tự downgrade live.
11. Route `/new` không ghi dữ liệu chỉ vì ghé thăm; tạo lười khi hành động rõ ràng, chuyển new→edit dùng replaceState; kiểm thử Back/Forward/Reload.
12. UI tiếng Việt, một primary action/cụm, chuẩn spacing/tokens, skeleton, inline validation, label rõ, Esc/focus cho modal; không sinh dữ liệu học vụ trang trí.

**Năm tình huống review ưu tiên:** route prefix sai; hidden/pending khác điểm0; giảng viên mất quyền sau chuyển người quản lý; hai writer cùng sửa điểm; API thành công nhưng thiếu audit/notification hoặc UI nuốt lỗi. Mỗi tình huống có test rõ bên dưới.

## 2. Thứ tự xử lý và đơn vị bàn giao

| Đợt | Phạm vi | Điều kiện bàn giao |
|---|---|---|
| A — Mở đúng bảng điểm | N01, N17, N21 | Ba route giảng viên dispatch đúng; API đúng; browser vào/Back/Reload được; card đúng count |
| B — Toàn vẹn danh sách/trạng thái | N02, N03, N04, N13, N18 | Bài pending không biến mất; stats đúng; hidden không hiện điểm0; thời gian đúng UTC |
| C — Sửa điểm và phân quyền | N05..N12 | Validation/type/reason/version/transaction; Admin safeguards; no-op authorization; governance ID parity |
| D — Nguồn học vụ và khả dụng | N14..N16, N19, N20, N22 | Không còn dữ liệu dựng; history nguồn thật; pagination; modal/error/partial-load rõ |
| E — Gate và hồi quy toàn hệ thống | N23/N24, toàn bộ 15 mục cũ, R01..R04 | Suites static/frontend/backend; SQL Server; browser role matrix; evidence và rollback plan |

Có thể bàn giao A trước để người dùng đọc bảng điểm, nhưng **chưa đóng toàn bộ task** khi các lỗi điểm/quyền/dữ liệu sai còn mở. Các đợt sửa security/grade integrity nên thành commit review riêng để dễ rollback.

## 3. Kế hoạch kỹ thuật từng nhóm với test chấp nhận

### A1. Route bảng điểm, card và phục hồi lỗi — N01/N17/N21

**File:** `frontend/assets/js/router.js`, `api.js`, `views/instructor.js`, `views/student.js`; tests frontend router và contract integration có sẵn.

**Tái sử dụng:** `InstructorView.renderAssessmentResultsPage(container, assessmentId, courseId)`, `ApiClient.getAssessmentAttempts`, `getInstructorAttemptResult`; backend `/instructor/assessments/{id}/attempts` và `/instructor/attempts/{id}/results` đã tồn tại. Không tạo endpoint `/assessments/{id}/results` chỉ để phù hợp báo cáo cũ.

- [ ] Viết regression gọi `dispatchRoute` nguyên bản cho cả ba route giảng viên và hai route sinh viên trong `router-reproduction.cjs`. Assert tên renderer và ID chính xác; instructor không được gọi student renderer. Test hiện phải fail ở ba route giảng viên.
- [ ] Giới hạn nhánh student bằng namespace/shape đầy đủ; đảm bảo instructor routes không bị generic suffix bắt trước. Parse assessment và attempt bằng đúng ngữ nghĩa, không đoán ID từ tiêu đề.
- [ ] Assert request giảng viên đúng `/instructor/assessments/{assessment_uuid}/attempts`; không có request `/student/attempt/`, `undefined`, `null`, `#` hoặc full route trong ID. Check ID hợp lệ tại API wrapper liên quan và trả validation cục bộ trước fetch.
- [ ] Card lấy `questions_count` chuẩn; test payload `{questions_count:16}` hiển thị16, zero thật hiển thị0, fixed/pool/mixed đúng số backend.
- [ ] Error state giữ backlink; lỗi có text tiếng Việt, Thử lại, Quay lại; 401 đi flow session, 403 không retry vô hạn, 404 không hiện như “chưa có bài”, 500 có mã hỗ trợ đã sanitize.
- [ ] Browser: bấm bảng điểm từ card, route trực tiếp, refresh, Back/Forward, lặp click nhanh, đổi course rồi mở bài khác. Assert đúng tiêu đề/course/assessment; route cũ chậm không đè route mới.

**Nguy cơ hồi quy:** student results, waiting room/focus mode, exam wizard guard, staging viewport và nhiều route refresh. Chạy `router_navigation`, `ui_route_refresh`, `exam_progression`, `waiting_room_state`, frontend integration và browser student result.

### B1. Danh sách bài, chờ chấm và thống kê — N02/N03/N04

**File:** `src/pwd301/services/attempt_service.py`, `blueprints/instructor/routes.py`, `frontend/assets/js/views/instructor.js`.

**Hợp đồng dữ liệu cần thống nhất:** trạng thái attempt và result riêng; score chưa có dùng null; bài pending không phải failed; “bài nộp” khác “lượt đang làm”; stats lấy các kết quả đã finalized theo policy, không lấy kết quả giả bằng0. Nếu đưa pagination, stats toàn assessment do backend tính cùng scope/filter, không chỉ từ trang đang xem.

- [ ] Fixture mixed quiz+essay submit → status PENDING_GRADING. Assert bài còn trong gradebook, endpoint pending có cùng attempt, điểm tổng chưa final, UI “Chờ chấm”. Repro hiện gradebook0/pending1 phải fail.
- [ ] Fixture objective-only → GRADED; essay-only và mixed → pending tới khi chấm đủ; grading overview query tất cả courses đang quản lý có pending. Chuyển owner phải thay scope lập tức.
- [ ] Fixture một bài finalized80% pass + một IN_PROGRESS + một PENDING_GRADING: thống kê finalized phải80% avg và100% pass trong tập một bài finalized, số đang làm/chờ chấm hiển thị riêng. Nếu chính sách chọn mẫu khác được spec xác nhận, ghi rõ mẫu số và test tương ứng.
- [ ] Điểm thật0 finalized → failed0; raw_score=null → trạng thái chưa có điểm, không được tự đổi thành0. Những trạng thái terminal khác, canceled/expired, phải được đưa/ẩn có chủ đích theo hợp đồng, không vô tình mất bài đã submit.
- [ ] Retake một student nhiều attempts: list đủ lịch sử; tổng attempts và số student không lẫn; course completion dùng policy thực, không vô tình thay đổi do stats UI.
- [ ] Xác nhận pending endpoint /grading overview /gradebook /attempt detail không mâu thuẫn về trạng thái hoặc quyền.

### B2. Công bố điểm và UTC — N13/N18

**File:** serializer result/list trong `attempt_service.py`, timestamp serializers được dùng chung, student/instructor views, helper UI hiện có.

- [ ] SCORE_HIDDEN và PENDING_GRADING render “Chưa công bố”/“Chờ chấm”; không total/pass/fail/GPA/letter/percentile/appeal-approved banner. Payload null không phải lỗi dữ liệu.
- [ ] INSTRUCTOR_RELEASE trước/sau release; AFTER_CLOSE trước/đúng/sau close; IMMEDIATE; answer_visibility độc lập score_release. Test backend JSON và frontend DOM cùng fixture.
- [ ] RELEASED0 hiển thị điểm0 thật; RELEASED hợp lệ dùng aliases đã có, không tạo serializer trùng. max_score khác10, pass_percent khác50 và điểm lẻ Decimal có test.
- [ ] Chuẩn hóa timestamp DB UTC thành ISO8601 có `Z` hoặc `+00:00` ở API. DB DATETIME2 lưu UTC; timezone display dùng locale/IANA timezone, không cộng7 cứng.
- [ ] Test cùng payload ở UTC, Asia/Bangkok, timezone âm; submitted/started/released/graded/focus-event cùng quy ước. Test sát ngày/tháng, deadline không đổi vì UI formatter.
- [ ] Với dữ liệu legacy naive, phương án chuyển đổi phải rõ rằng giá trị DB là UTC; không double-convert chuỗi đã có offset.

### C1. Chấm/sửa điểm hợp lệ, nguyên tử và đồng thời — N05/N06/N07/N08

**File:** `attempt_service.grade_essay_question`, instructor grading route, models version mapping đang có, grade/result/history/audit helpers và grading tests hiện có.

**Input contract:** points phải finite Decimal, đúng precision, `0 <= awarded_points <= assigned_points`; question type từ immutable snapshot phải ESSAY. Revision có lý do thực. Request chứa expected row_version đúng resource/version đang được sửa. Invalid/conflict không tạo history hay sửa aggregate.

- [ ] Parameterized validation: null, blank, string bất kỳ, bool, list/object, NaN, infinities, âm, quá max, exact0/max, decimal hợp lệ. Assert400 ổn định và DB trước/sau giống nhau cho input sai; hiện bogus/NaN phải fail500.
- [ ] Mỗi objective type SINGLE_CHOICE/MULTIPLE_CHOICE/fill/matching hiện hành bị từ chối qua essay endpoint. Assert grade/result/snapshot/history không đổi. Câu ESSAY hợp lệ vẫn chấm đúng.
- [ ] Initial essay grading theo quy tắc đã xác nhận; revising score cần reason nonblank. Assert history old/new/actor/time/reason; sửa nhiều lần không overwrite history.
- [ ] Dùng version column và conditional update/lock phù hợp SQL Server; backend không chỉ nhận row_version rồi bỏ qua. Không làm dựa vào `updated_at` UI hoặc Python mutex toàn process.
- [ ] Hai writer cùng version: một thành công, một409; refresh sau409 rồi thao tác quyết định mới. Test manual/manual, manual/regrade, double-click/retry và ownership change khi đang mở form.
- [ ] Transaction failure injection sau grade update/trước history/audit/result: mọi bảng rollback cùng nhau; không notification nói điểm đã sửa khi transaction thất bại. Notification outbox theo cơ chế hiện có; delivery failure retry idempotent theo NOTIF-002.
- [ ] Sau chấm đủ essay: finalize/result/pass đúng, learning completion/prerequisite/certificate được cập nhật theo policy; grading pending giảm đúng. Khi regrade, snapshot/answer cũ bất biến và worker retry không duplicate logical history.

**Nghiệm thu UI:** điểm invalid hiển thị inline không xóa text đã nhập; đang gửi disable action chống double-click;409 giải thích dữ liệu đã đổi và tải bản mới; không báo thành công trước response thành công. Chấm xong quay bảng không nhầm bài khác, refresh thấy số chính thức.

### C2. Phân quyền theo action và idempotency — N09/N10/N12

**File:** `authorization_service.py`, `course_service.py`, attempt result/grading services, API routes tương ứng; reuse reason/audit/notification helper có sẵn.

- [ ] Lập matrix action: aggregate view, individual result view, essay grade/revise, course edit/publish/trash/restore, governance review. Role ADMIN không thay object/action policy.
- [ ] Admin individual detail thiếu/rỗng reason bị từ chối; valid reason được audit với actor thật, target và action rõ; required audit failure fail-closed. Instructor current owner vẫn đọc đúng mà không bị áp requirement dành riêng Admin.
- [ ] Admin direct content edit thiếu reason bị từ chối; có reason ghi audit và notify owner đúng policy. Hạn chế từng sub-admin theo quyền chức năng đã chốt; không gọi blanket can_manage thay tất cả guards.
- [ ] Auth+object check trước `current_status == target_status`. Nonowner submit môn đã submitted, archive môn đã archived, trash/restore no-op đều403 hoặc privacy-safe404 theo contract; response không trả private metadata.
- [ ] Owner retry cùng transition giữ idempotent, không audit/notification duplicate ngoài policy. Empty reason khi action bắt buộc không được bypass nhờ no-op.
- [ ] Chuyển owner/suspension/role revoke sau mở view: request tiếp theo được authorize lại, không dựa cache UI. Client mass assignment owner/admin/performed_as_admin bị chặn.
- [ ] Bootstrap Admin qua flow tin cậy hiện hành; web/JWT tự cấp ADMIN vẫn bị chặn dù hệ thống chưa có primary. Không tạo ngoại lệ chung “chưa có primary” trong service public.

**Lưu ý chốt nghiệp vụ:** canonical matrix cho phép Admin override có quy trình, TASK-072 chia sub-role. Phải làm rõ mức allowed/read/override cho từng action trước thay security; báo cáo này không tự quyết biến mọi Admin thành owner hay cấm toàn bộ quyền Admin.

### C3. Kiểm duyệt chương mục không phụ thuộc dạng ID — N11

**File:** learning-units route và service staging (`instructor/routes.py`, `lesson_service.py`, course changeset/change request helpers hiện có).

- [ ] Cùng resource dùng public UUID/numeric nếu còn hỗ trợ: DRAFT/REJECTED cho ghi trực tiếp theo spec; APPROVED/PUBLISHED/ARCHIVED áp workflow thay đổi đã xác nhận, không nhánh dựa `isdigit()`.
- [ ] Request pending trả status/envelope đúng và frontend hiện “Chờ duyệt”; nội dung student đang học chưa bị thay ngay. Nếu Lazy Draft cho phép giữ nháp độc lập, assert student không thấy và nháp không được nhầm với change đã apply.
- [ ] Admin approve/reject: sau approve áp đúng thứ tự/structure/version; sau reject nội dung published giữ nguyên; duplicate approve/retry không nhân đôi unit.
- [ ] Two pending edits trên cùng structure, course archived/owner changed khi đang duyệt, snapshot changed: conflict/reconcile theo workflow, không âm thầm ghi đè.
- [ ] UI thêm/rename/reorder/delete lesson/unit cùng dùng trạng thái đúng; test không chỉ create route numeric. Bảo toàn published revision đang có student, resources/video/quiz và prerequisites.

### D1. Học vụ/phúc khảo/history/giám sát có nguồn thật — N14/N15/N16

**File:** student result view/drawer, result serializer, appeal/history/focus-event API clients hiện có. Backend `/api/attempts/{id}/grade-history` là điểm reuse cần kiểm tra quyền/auth phù hợp SPA; không đưa JWT vào localStorage để gọi nó. Có thể cần session alias chuẩn, dùng cùng service thay duplicate history store.

- [ ] Bỏ original_score=`score-1.5`, committee approvals/rubrics/integrity dựng sẵn. Mỗi timeline event map từ persisted record: type, old/new, actor, time, reason; thiếu record hiện chưa có lịch sử.
- [ ] Appeal none/pending/rejected/approved: banner đúng trạng thái; approved chỉ khi decision thật; title không gắn bộ môn/học phần giả. Thông báo điểm chính thức tách appeal workflow.
- [ ] Grade history initial/manual revision/regrade: số hiển thị khớp history API và final result, không thay audit record thành lời kể giả. Nếu privacy policy cần ẩn actor identity, hiển thị role phù hợp theo contract.
- [ ] Percentile chỉ tính khi có cohort xác định, số người/mẫu số/time snapshot và permission; không suy top15/top35 từ ngưỡng điểm. Nếu không có tính năng được spec yêu cầu, bỏ claim thay vì thêm analytics engine.
- [ ] Proctoring không đồng nghĩa absence of focus events. Không trả verified=true mặc định; distinction: không có dữ liệu, có event, đã review, kết luận có thẩm quyền. Browser blur/screenshot-attempt là tín hiệu, không tự kết luận gian lận.
- [ ] Rubric/GPA/letter-grade chỉ khi có quy chế/assignment thật; không tự chuẩn hóa mọi kỳ thi thành rubric ABET/bộ môn Python. Thang điểm thật và pass policy backend là nguồn.
- [ ] API không có hoặc lỗi không biến thành lời xác nhận “không vi phạm/phúc khảo đã duyệt”. Test field absence/null/unknown và network errors.

### D2. Pagination, modal và partial error — N19/N20/N22

- [ ] List attempts filter/status/student/sort/page có limit; authorize trước query. Eager load result/student theo pattern SQLAlchemy có sẵn; count/statistics cùng scope và không lẫn trang. Test nhiều pages, cùng timestamp, page boundary, new submissions khi đang xem.
- [ ] Benchmark fixture lớp lớn và capture query count/latency/memory trước/sau. Không thêm cache trước đo; không để frontend chỉ thống kê trang hiện tại như tổng assessment.
- [ ] Modal dùng shared UI lifecycle, role=dialog/aria-modal, accessible name, initial focus, trap, Esc, X, restore focus; scroll body không trôi; đóng/reroute xóa listeners/overlay.
- [ ] Detail request chậm lúc đổi attempt/close modal không được ghi vào modal mới của bài khác; hủy hoặc guard response theo request identity.
- [ ] Appeal404 không có record được empty;403/500/timeout hiện lỗi cục bộ với retry. Main result tải được vẫn xem được khi appeal/focus partial failure; không gán success cho phần lỗi.
- [ ] Light/dark/mobile320/390/768/desktop/zoom200%, contrast đo≥4.5:1, touch targets và table scroll; loading skeleton thay spinner trung tâm. Không khẳng định WCAG AA nếu chỉ đọc class.

## 4. Ma trận tác động chéo để tránh hồi quy

| Điểm thay đổi | Thành phần có thể bị ảnh hưởng | Kiểm thử bảo vệ bắt buộc |
|---|---|---|
| Route result namespace | Student result/waiting room/focus, instructor wizard, cached route reload | Dispatch table; render thực; Back/Reload; no foreign ID in request; stale render |
| can_manage/action authorization | Course, lesson, question revision/exam authoring, file, analytics, AI, grading | Owner/other/current-owner-transfer; each admin sub-role; reason/audit/notification fail |
| Transition no-op | submit/approve/archive/trash/restore, API/web retry | Nonowner no-op deny; owner repeat idempotent; private metadata absent |
| Result list/status | Instructor gradebook, pending tasks, retake/history, export | PENDING_GRADING included; null≠0; terminal status decisions; stats denominator |
| Essay grade/version | Result aggregate, histories, regrade worker, completion/certificates | type/points/reason/version; atomic rollback; manual/regrade interleave |
| Hidden/release render | Student result, appeal eligibility, answer visibility | SCORE_HIDDEN; AFTER_CLOSE; NEVER; releasedzero; objective breakdown masking R01 |
| Timestamp contract | Date sorting, deadline display, focus events, grade/appeal history | UTC explicit offset; timezone/DST; no changed authoritative deadline |
| Governance unit staging | Student curriculum, lesson resources/video/quiz, Admin queue | UUID parity; pending invisibility; approve/reject/retry/concurrent changes |
| File cleanup/scanner | Lesson/quiz/import/evidence/avatar, active revision inheritance | PENDING/QUARANTINED denied; outage; oversized/stream failure; old revision remains safe |
| Academic claims/history | Student official grade, appeal/regrade, monitoring | Persisted source consistency; missing/error state; no invented events/percentiles |
| List pagination | Global stats, export, filters/ownership, load time | Full counts vs pages; bounded query; scope-permission; export definition |
| Modal shared UI | Other stacked modals/drawers/notifications | Esc/focus/close stack; event cleanup; async stale response; zoom/mobile |

## 5. Ma trận thao tác nghiệp vụ end-to-end

Mỗi kịch bản phải ghi **tiền điều kiện → hành động UI → request/status → trạng thái DB → UI sau reload**. Chỉ button click thành công hoặc API200 chưa đủ. Dùng identities/dữ liệu thử, không điểm/dữ liệu thật.

| Kịch bản | Người thao tác và chuỗi bước | Kết quả cần chứng minh |
|---|---|---|
| E01 — xem bảng điểm | Instructor owner mở course, bấm bảng điểm, chọn bài, đóng, Back, Reload | Đúng course/assessment/student; list/detail đúng API; không404; no write khi đọc |
| E02 — chưa có bài | Owner mở assessment không attempts | Empty state thật có backlink; không gọi lỗi là empty |
| E03 — làm/submit objective | Student enroll đủ điều kiện → waiting room → start → answer/autosave → submit | Lease/deadline/server score đúng; submit retry một result; instructor thấy bài và counts đúng |
| E04 — tự luận/mixed | Student nộp mixed → Instructor xem pending → chấm từng essay → finalize | Bài luôn hiện; chưa chấm khôngfailed; final điểm/history đúng; pending overview cập nhật |
| E05 — sửa điểm | Instructor mở bài đã chấm, nhập score/reason, gửi → reload history | Reason bắt buộc; old/new/actor/time thật; completion policy cập nhật đúng |
| E06 — hai người chấm | Hai phiên cùng version, lần lượt gửi hoặc barrier concurrent | Một success/một409; không lost update; không duplicated history/outbox |
| E07 — release policy | Student xem trước release, sau release, trước/đúng/sau close | Hidden khônghiện0; release/answer visibility đúng, không suy từ thông tin khác |
| E08 — retake | Student làm nhiều attempts, leave/rejoin theo rules | Danh sách giữ số lần, completion dùng policy; không reset trái retention/history |
| E09 — phúc khảo | Student gửi đơn, Instructor pending/reject/approve, Student reload | Decision thật, banner/timeline đúng; chưa có đơn không claim đãduyệt; history nhất quán |
| E10 — regrade | Correction hợp lệ → job → retry/resume → student/instructor/history | Snapshot/answer cũ bất biến; điểm chính thức và history thay đúng; job idempotent |
| E11 — ownership/IDOR | Instructor B đổi URL/API; Admin chuyển course manager; A gọi tiếp | Unrelated denied; old manager mất quyền dữ liệu hiện tại; new manager đủ quyền theo rules |
| E12 — từng Admin | PRIMARY và từng4 sub-role xem aggregate/detail, edit/review với/không reason | Đúng action matrix; audit true actor; notify owner; không impersonation |
| E13 — course changes | Owner thêm/rename/reorder published unit, gửiduyệt, Admin reject/approve | Draft/pending không visible student; UUID/numeric parity; approved structure/resource đúng |
| E14 — authored exams | Manual/interactive/Excel/Moodle/images/AI luồng còn hỗ trợ → publish → first start | Questions/points count đúng; timing freeze/publish; structure freeze sau start; image file safe |
| E15 — lease/offline | Hai tab student, stale takeover, reordered/retried autosave, networklost, close deadline | Một writer; retry không overwrite newer; deadline reject; takeover same attempt |
| E16 — file fail-closed | Upload nhỏ/sátlimit/≥1GB, scanner ERROR/outage, trash/restore/revision | Temp cleanup; student cannot view/downloadunsafe; current active safe; not leak storage path |
| E17 — auth/settings | Student/Instructor/Admin account profile, toggle password, role switch, suspend session | Toggle không submit; token/session revoke; CSRF; route UI cập nhật sau failure đúng |
| E18 — AI/RAG | Student hỏi nguồn course authorized/draft/archive, injection xin account/DB | Scope enforced trước retrieve; nguồn thật; tên Bạch tuộc trợ lí AI; raw chat retention |
| E19 — lỗi từng dependency | API401/403/404/409/500, timeout, partial appeal/focus, emailretry | Error đúng nghĩa; không success giả; rollback mutation; required audit failsclosed |
| E20 — UI thiết bị/keyboard | Desktop+mobile viewport, light/dark, zoom200%, Tab/Esc/Enter, browser history | Label/primary/touch/contrast/focus/scroll; modal khôngtrap; read/new routes khôngsideeffect |
| E21 — operations | Admin monitoring đọc health/telemetry, backups chỉ trên sandbox | psutil thật; service states có evidence; no fabricated hardware; restore cần explicit confirmation |

Các flows password/restore/permission thay đổi dùng tài khoản thử và approval đúng cơ chế khi thật. Lượt audit hiện tại không đã chạy E03–E21; bảng này là kế hoạch nghiệm thu, không biên bản PASS.

## 6. Pipeline lệnh kiểm thử và evidence

### 6.1. Baseline và static

```powershell
git status --short
git rev-parse HEAD
.venv/Scripts/python.exe scripts/repo_check.py
.venv/Scripts/python.exe -m compileall -q src tests scripts
.venv/Scripts/python.exe -m ruff check src tests scripts
.venv/Scripts/python.exe -m ruff format --check src tests scripts
.venv/Scripts/python.exe -m mypy src
$frontendTests = @(Get-ChildItem tests/frontend/*.test.js | ForEach-Object FullName)
node --test @frontendTests
```

Capture command, environment, exit code, output file cho từng gate. Tránh shell wrapper che `$LASTEXITCODE`. PowerShell wildcard phải expand rõ khi Node không tự expand. Nếu có RTK cài sẵn dùng RTK; lượt audit không thấy `rtk`, nên dùng native commands. Không cài dependency mới chỉ để nén output.

### 6.2. Backend cô lập và regression phạm vi

```powershell
$env:TEST_DATABASE_URL = 'sqlite:///:memory:'
$env:PYTHONDONTWRITEBYTECODE = '1'
.venv/Scripts/python.exe -m pytest -p no:cacheprovider tests/unit/test_grading_service.py tests/api/test_grading_api.py tests/security/test_grading_idor.py tests/unit/test_assessment_regrading_traceability.py -q
.venv/Scripts/python.exe -m pytest -p no:cacheprovider tests/security/test_course_idor.py tests/security/test_rbac_and_idor.py tests/api/test_lesson_authoring_remediation.py tests/api/test_scan_api.py tests/api/test_operations_api.py tests/security/test_operations_security.py tests/unit/test_user_service.py tests/unit/test_file_service.py -q
.venv/Scripts/python.exe -m pytest -p no:cacheprovider tests/api/test_attempt_api.py tests/api/test_attempt_submission_api.py tests/api/test_attempt_lease_api.py tests/security/test_attempt_idor.py tests/security/test_attempt_submission_idor.py tests/security/test_attempt_lease_idor.py tests/security/test_assessment_idor.py -q
.venv/Scripts/python.exe -m pytest -p no:cacheprovider tests/api/test_appeal_workflow.py tests/api/test_backend_frontend_parity.py tests/api/test_frontend_integration.py tests/api/test_frontend_e2e_flow.py -q
.venv/Scripts/python.exe -m pytest -p no:cacheprovider tests/test_m1_file_access.py tests/unit/test_malware_scan_service.py tests/api/test_file_api.py -q
.venv/Scripts/python.exe -m pytest -p no:cacheprovider -q
```

Thêm tests mới N01–N24 vào module phù hợp trước sửa. Chạy lệnh chọn lọc và suite đầy đủ sau final changes; không pin số test “1540” làm tiêu chí. Mọi failure/skipped/collection error phải ghi đúng. Suites đọc/ghi bằng app fixture MSSQL có cleanup xóa dữ liệu: **chỉ dùng database test riêng**, không trỏ TEST_DATABASE_URL vào PWD301 đang chạy.

### 6.3. SQL Server và migration/runtime

Lệnh đọc runtime hiện hành:

```powershell
docker ps --format '{{.Names}} {{.Status}}'
docker exec pwd301_web flask db current
docker exec pwd301_web flask db heads
```

Trên **database test SQL Server riêng** mới chạy upgrade/downgrade, row-version/concurrency và trigger enforcement. Kiểm tra schema/model drift không chỉ head; xét columns/indexes/constraints/triggers liên quan. Upgrade từ schema trước migration mới, verify dữ liệu backfill; downgrade/restore trên sandbox. Không auto-upgrade live trong script “verify”; verify phát hiện mismatch phải fail rõ và deployment có migration step được kiểm soát.

Concurrency tests phải mở nhiều connection/process thực và dùng barrier để cùng bắt đầu, tránh test tuần tự giả concurrent. Capture winner/loser, versions, final grade, history count, audit/outbox. SQLite không mô phỏng đúng ROWVERSION/locking/SQL Server triggers.

### 6.4. Browser và security review

Browser kiểm tra E01–E21 theo role/viewport matrix; capture screenshot và network được sanitize, HTTP assertions, DB trước/sau trong sandbox. Test request thật bằng client có auth đúng; không dùng source substring assertion thay scenario.

OCR với provider đã được cấu hình: review diff có business context và lưu full result. Lượt này OCR thiếu LLM endpoint nên chưa có kết quả công cụ; review thủ công không được báo là OCR PASS. Không gửi token/key/config lên báo cáo. Trước ship/release, security pentest độc lập trên sandbox theo giao thức Strix của dự án; chưa thực hiện pentest trong tác vụ lập báo cáo này.

## 7. Gate nghiệm thu và rollback

| Gate | Điều kiện pass | Điều kiện dừng |
|---|---|---|
| Correctness regression | Test từng N được red trước và green sau; expected DB/UI/HTTP đồng nhất | Test chỉ assert200, falseempty, fake values hoặc workaround route |
| Authorization | Resource+action+state+role matrix, Admin reason/audit, suspension và CSRF/JWT | Self-escalation, nonowner no-op200, leak private detail hoặc required audit missing |
| Grade integrity | Type/points/reason/version, atomic history/result, deterministic retry | Objective bị chấm qua essay; lostupdate; history/result mismatch |
| Governance/file | Published staging đúng mọi ID, fileunsafe inaccessible | Direct write published bypass; file PENDING/ERROR downloadable |
| Runtime/DB | Schema phù hợp image/source; SQL tests; workers/dependencies thật | SQL errors, drift, chỉ báo healthy giả hoặc chạy fixture destructive lên live |
| Frontend/browser | All supported paths, role and state, E2E interactions, responsive keyboard | 81 source tests xanh nhưng click route fail; hidden điểm0; review claims dựng |
| Report/delivery | SHA/env/commands/logs/limitations rõ, no secrets, scoped diff review | Chứng nhận100% vượt scope, skipped thànhpass, mất thay đổi người dùng |

Mỗi đợt có điểm rollback trước deploy: code phiên trước; backup/schema compatibility; feature changes reversible. Với grade/history append-only, **không rollback bằng xóa audit/history hoặc sửa snapshot**: dùng correction/regrade bù đúng quy trình và giữ dấu. Notification/email phát ra không thu hồi như DB rollback, nên business commit/outbox phải đúng thứ tự. Migration destructive phải có restore drill trên sandbox; không auto restore live.

Sau deploy: smoke E01/E03/E04/E07/E11/E13 bằng dữ liệu thử được phép; so sánh API/UI/DB; theo dõi 404/403/500/conflict/queue lag và phản ánh người dùng. Nếu phát hiện sai điểm/quyền: dừng mutation chịu ảnh hưởng theo biện pháp đã thiết kế, bảo toàn evidence và rollback code tương thích; không vá bằng mở quyền/gỡ validation.

## 8. Đơn giản hóa và phần hoãn có trách nhiệm

| Hạng mục | Phân loại | Hướng làm |
|---|---|---|
| Fabricated timeline/committee/rubric/proctoring/percentile | REMOVE NOW khi triển khai | Xóa dữ liệu/tuyên bố khôngnguồn; dùng persisted source hoặc empty state |
| Generic results suffix + heuristic ID | SIMPLIFY NOW | Namespace/shape rõ, contract ID riêng course/assessment/attempt |
| Raw self-built attempt modal | SIMPLIFY NOW | Shared modal lifecycle hiện có, không framework dialog mới |
| Session/JWT/CSRF, audit/history, scan pipeline | KEEP | Giữ invariants, mở coverage; không bỏ guard để test xanh |
| Cache gradebook/materialized analytics | PONYTAIL | Chưa thêm; trigger benchmark chứng minh cần; owner backend; risk dữ liệu stale; safeguard pagination/eagerload; review trước scale release |
| SQL concurrency/outage verification | Verification debt, bắt buộc trước release | Owner backend+QA; risk sai điểm/file exposure; safeguard không release-ready; review sau sửa C và trước deploy |
| R01 visibility/R02 sub-admin rule clarification | Business decision dependency | Owner product/domain/security; risk policy thay ngầm; giữ trạng thái cónguồn và leastprivilege trong phương án; chốt trước code guard |

Không có ponytail code mới vì lượt này không sửa sản phẩm. Không đo hoặc tuyên bố tiết kiệm LOC/phụ thuộc nếu chưa có diff thực.

## 9. Biên bản phạm vi của tài liệu này — A–G

**A.** Dựa trên các nguồn và 15 lỗi lịch sử +24 phát hiện trong báo cáo danh mục. **B.** Reuse backend attempts/pending/history, auth/audit/notification, modal và fixtures hiện có. **C.** Chỉ tạo báo cáo và evidence. **D.** Đơn giản hóa là đề nghị triển khai, chưa xóa sản phẩm. **E.** Concurrency SQL/outage/browser roles vẫn là phần chưa kiểm chứng được giao rõ owner/gate. **F.** Kết quả chạy thật ở báo cáo danh mục/evidence; các checklist trên chưa thực hiện sửa/red-green. **G.** Thực hiện theo đợt A–E; không tuyên bố hết bug hoặc bảo đảm không hồi quy chỉ từ test counts.

Đã dùng 7 skill gồm: superpowers (using-superpowers, systematic-debugging, writing-plans, dispatching-parallel-agents, verification-before-completion), ponytail, task-observer, full-output-enforcement, open-code-review (CLI thiếu endpoint; review thủ công), impeccable, computer-use.

## 10. Phụ lục thi hành và xác minh — 2026-10-03

Phần mục 1–9 ở trên là snapshot lập kế hoạch/audit tại thời điểm tạo báo cáo. Phụ lục này ghi nhận các thay đổi sản phẩm đã thực hiện sau đó, không sửa ngược lịch sử của báo cáo.

### A. Phạm vi và nguồn chuẩn đã đối chiếu

- `tasks/CURRENT.md`, `README.md`, `AGENTS.md`.
- `docs/system/PWD301_SYSTEM_SPECIFICATION/CODING_AGENT_START_HERE.md`.
- Business rules, non-negotiable invariants, grading/regrading, assessment attempts, file management, audit/admin actions, permission matrix và E2E test scenarios.
- Báo cáo lỗi tổng hợp `BAO_CAO_TOAN_BO_LOI_PWD301_2026-10-03.md` và các reproduction artifacts trong `docs/audits/PWD301_AUDIT_2026-10-03_EVIDENCE/`.

### B. Quyết định tái sử dụng

Đã tái sử dụng service attempt/grade/history hiện có, authorization/audit/notification pipeline, pagination/query helpers, session/JWT boundaries và modal/drawer lifecycle hiện có. Không thêm dependency, queue, microservice hay bản sao schema mới.

### C. Thay đổi theo nhóm file

- Backend: validation số điểm fail-closed; chặn chấm essay trên snapshot objective; bắt buộc reason khi sửa điểm hoặc Admin xem detail; optimistic row-version update; giữ `PENDING_GRADING`; overview `/instructor/grading`; pagination/filter/count; timestamp UTC có offset; grade-history route; staged approval nhất quán theo UUID; authorization trước idempotent course no-op; Admin course edit có reason/audit/notification.
- Frontend: namespace route instructor/student; kết quả ẩn điểm không tự sinh 0/10/fail; chỉ hiển thị appeal/history persisted; pagination và trạng thái `Chờ chấm`; qCount đúng field backend; lỗi/retry tiếng Việt; modal có dialog semantics, Escape, focus trap/restore; Admin detail có form reason/retry thay vì hiển thị raw backend error; xóa toàn bộ drawer dữ liệu fabricated (timeline/committee/rubric/proctoring/score delta giả).
- Database: thêm migration forward-only `b3c4d5e6f7a9` tháo 9 SQL Server default constraints cản rollback, chuyển các giá trị mặc định tương ứng về Python-side defaults; sửa thứ tự rollback của ba vòng FK legacy theo dialect MSSQL để `downgrade base` an toàn.
- Verification: thêm regression tests frontend/backend, migration round-trip SQL Server và row-version race đa connection; `scripts/verify.ps1` có gate Node frontend với glob được expand rõ ràng và đưa `migrations` vào compile/lint/format.

### D. Deletion/simplification

Đã xóa các dữ liệu trình bày không có nguồn persisted trong student result drawer; không thay thế bằng số liệu giả mới. Đã thay heuristic route suffix chung bằng namespace route rõ ràng. Không chỉnh sửa hoặc xóa các thay đổi không thuộc phạm vi đang có sẵn trong worktree.

### E. Ponytails và giới hạn còn lại

- Browser: đã smoke test trực tiếp route instructor results, modal reason/retry, tải detail và Escape ở desktop; đã kiểm tra viewport mobile `390x844` với mobile navigation; chưa hoàn tất role × viewport matrix E01–E21.
- OCR/Open Code Review CLI: không có LLM endpoint; review line-level thủ công, không báo cáo OCR PASS.
- ClamAV outage, restore drill, R01 answer visibility và R02 sub-admin policy vẫn là giới hạn/decision dependency như phần audit gốc.

### F. Xác minh thực tế đã chạy

- `python scripts/repo_check.py`: PASS.
- `python -m compileall -q src tests scripts`: PASS.
- `ruff check src tests scripts`: PASS.
- `ruff format --check src tests scripts migrations`: PASS — 268 files already formatted trong phạm vi toàn repo hiện tại.
- `mypy src`: PASS — 88 source files.
- Frontend: JS syntax PASS — 10 files; `node --test tests/frontend/*.test.js`: **85 passed, 0 failed**.
- Focused backend regression: **115 passed**; compatibility follow-up: **3 passed**.
- File access isolation: `tests/test_m1_file_access.py`: **12 passed in 8.14s**.
- First aggregate pytest after implementation: **1548 passed, 2 failed**; both failures were compatibility regressions (SHORT_ANSWER lifecycle and an existing Admin test thiếu reason) and were fixed; the three focused follow-up tests passed.
- SQLite migration suite: **2 passed** với upgrade → downgrade base → upgrade.
- SQL Server migration sandbox thật: **1 passed** với upgrade → downgrade base → upgrade; head sandbox `b3c4d5e6f7a9`, 74 tables và không còn default constraint trên 9 cột mục tiêu. Ba CSDL sandbox đã được xóa sau kiểm tra; không nâng cấp database runtime.
- SQL Server row-version concurrency sandbox thật: **1 passed**; barrier trên hai session cho đúng 1 winner/1 conflict, final grade thuộc winner và history count là 2.
- Aggregate pytest mới sau thay đổi migration/model: **1550 passed, 1 deselected in 1019.72s (0:16:59)**; test SQL Server opt-in được chạy riêng, không biến deselected thành pass.
- Runtime read-only: `pwd301_web`, `pwd301_db`, `pwd301_clamav` healthy; `/health` và `/health/deep` trả 200; unauthenticated `/admin/health` và `/api/admin/health` trả 401; Alembic runtime current `a1b2c3d4e5f8`, repository head `b3c4d5e6f7a9`.
- Browser smoke: route instructor results rendered 2 submissions; hidden row rendered `Chờ chấm` instead of `0/fail`; Admin detail first required localized reason, then loaded persisted detail after a reason; Escape removed modal; viewport mobile 390x844 chuyển topbar sang mobile menu và đã reset về viewport mặc định.

### G. Kết luận trung thực

Các defect N01–N22 và hai defect migration SQL Server phát hiện trong quá trình xác minh đã được xử lý trong code/test ở phạm vi có bằng chứng: full SQLite aggregate, migration round-trip SQL Server thật, SQL Server row-version race, static gates, frontend Node và browser smoke. Release vẫn chưa được gọi là đã verify toàn diện trên production vì chưa chạy đủ role × viewport matrix E01–E21, ClamAV outage/restore drill, pentest độc lập, OCR có LLM endpoint và các quyết định R01/R02. Worktree còn nhiều thay đổi có sẵn của người dùng; chưa stage/commit/push.

### H. Cleanup và biên giới dữ liệu

- Chỉ ba database tên `PWD301_AUDIT_20261003`, `PWD301_AUDIT_MIGRATIONS_20261003` và `PWD301_AUDIT_CONCURRENCY_20261003` được tạo cho verification; sau cùng đã xác nhận và drop đúng ba database này.
- Database ứng dụng `PWD301` không bị drop hoặc auto-upgrade; runtime vẫn ở `a1b2c3d4e5f8` cho tới khi có bước deploy migration được kiểm soát.

## 11. Phụ lục tiếp tục xác minh mới nhất — 2026-10-03

Phụ lục này ghi nhận phần tiếp tục thực hiện sau Phụ lục 10, không thay thế các giới hạn lịch sử ở trên.

### A. Sửa lỗi operations/telemetry phát hiện khi browser review

- Khu vực Admin Operations không còn render các claim không có nguồn như số daemon cố định, mã regrade giả, staging host giả, số liệu Qdrant/MinIO/Redis tĩnh, SHA-256 giả hoặc kích thước backup mặc định.
- Health cards chỉ render dữ liệu từ `GET /admin/health`; dùng tên service backend (`name`) và trạng thái/độ trễ thật. Background jobs dùng `GET /admin/operations/jobs`, hiển thị summary persisted và empty state khi không có job.
- Backup thiếu checksum/kích thước trong API hiển thị “Chưa ghi nhận”/“Chưa có dữ liệu”, không tự bịa giá trị.
- Khi telemetry probe lỗi trong admin analytics, payload giữ `status=DEGRADED`, `available=false`, error và timestamp; không trả CPU/RAM/disk/hostname giả.

### B. RED → GREEN mới

- Frontend regression trong `tests/frontend/operations_without_hardware.test.js`: RED bắt được các claim giả; sau sửa GREEN.
- Backend regression `test_admin_dashboard_resilient_when_telemetry_throws_exception`: RED bắt được fallback CPU/RAM/disk giả; sau sửa GREEN.
- Regression label health dùng `s.name || s.service_name || k`: RED trước sửa, GREEN sau sửa.

### C. Kết quả xác minh fresh

- Root tests: `295 passed`.
- API: `360 passed`.
- Security: `233 passed`.
- Unit: `626 passed`.
- Concurrency: `13 passed`.
- Integration: `11 passed, 2 deselected`; hai test SQL Server opt-in không tính vào aggregate và đã chạy riêng trên database tạm.
- E2E: `12 passed`.
- Không cộng trùng nhóm: backend aggregate tương đương `1550 passed`; frontend Node: `86 passed, 0 failed, 0 skipped`.
- SQL Server migration round-trip: `1 passed`; SQL Server row-version race: `1 passed`, kết quả một winner/một conflict và history count bằng 2. Ba database sandbox đã được drop; database runtime không bị upgrade.
- Static gates: repository check PASS; Ruff check PASS; Ruff format `268 files already formatted`; compileall PASS; mypy `88 source files` PASS; JavaScript syntax `10 files` PASS; `git diff --check` không có lỗi whitespace.

### D. Browser/runtime evidence mới

- Runtime containers `pwd301_web`, `pwd301_db`, `pwd301_clamav` healthy; `/health` và `/health/deep` trả 200; unauthenticated Admin health/telemetry vẫn bị chặn 401.
- Browser role switch: Học viên và Quản trị viên chuyển đúng route/navigation ở desktop; cả hai đã được kiểm tra viewport `390x844` với mobile menu rồi reset viewport.
- Admin Operations desktop và `390x844`: health matrix hiển thị tên thật như Microsoft SQL Server 2022, ClamAV Anti-Malware Daemon, Email Outbox Delivery Queue, Background Job Workers; job empty state và backup metadata thiếu đều hiển thị trung thực, không còn claim giả.

### E. Giới hạn còn lại

Đây là bằng chứng triển khai và kiểm thử trong workspace/sandbox, không phải chứng nhận production. Chưa có đủ role × viewport matrix E01–E21, ClamAV outage/restore drill, pentest độc lập Strix, OCR có LLM endpoint và quyết định nghiệp vụ R01/R02. Worktree vẫn có nhiều thay đổi có sẵn của người dùng; chưa stage/commit/push.
