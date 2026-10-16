# TASK-095 — Kế hoạch bàn giao triển khai và nghiệm thu cho Antigravity

> **For agentic workers:** REQUIRED SUB-SKILL: dùng `subagent-driven-development` hoặc `executing-plans`; làm từng nhiệm vụ với test fail → sửa → test pass → review độc lập. Không bắt đầu viết lại hệ thống từ đầu.

**Ngày chốt bàn giao:** 16/10/2026, Asia/Bangkok. **Trạng thái:** triển khai dở dang, CHƯA NGHIỆM THU.

**Goal:** hoàn tất toàn bộ yêu cầu sửa lỗi của chủ dự án, giữ công việc hiện có, chứng minh bằng API, SQL Server, trình duyệt thật và PDF production; bàn giao lại Codex để kiểm chứng độc lập.

**Architecture:** Flask REST API thuần headless và SPA Vanilla JavaScript hiện có. Tái sử dụng `CourseChangeRequest` tổng hợp, các khóa giao dịch, snapshot bài thi, bộ dựng matching và ReportLab. Không tạo hệ thống duyệt thứ hai.

**Tech Stack:** Python/Flask/SQLAlchemy/Alembic, Microsoft SQL Server, JavaScript SPA, Node tests, FFmpeg/HLS, MathJax offline/SVG/svglib/ReportLab.

**Spec:** `docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/WORKFLOW_SUPERSESSION.md`. Tài liệu này là kế hoạch thực hiện/kiểm chứng, không thay thế hợp đồng nghiệp vụ đó.

## 1. Chỉ thị đầu tiên dành cho Antigravity

Bạn đang tiếp quản thay đổi CHƯA COMMIT trong `E:\PWD301`. Không reset, clean, stash, checkout đè, xóa file mới hoặc viết lại các phần đã sửa chỉ vì chưa hiểu. Chủ dự án giao phần triển khai cho bạn; Codex sẽ kiểm chứng sau. Không tự đánh dấu nghiệm thu thay Codex.

Đọc hết tài liệu trước khi sửa. Không được báo hoàn tất chỉ vì đọc source thấy có logic, test Node xanh, hoặc một nhóm pytest xanh. Không dùng ảnh chụp cũ làm bằng chứng cho mã mới. Số lượng agent hoặc số lượt review không thay thế bằng chứng chạy thật.

Những đường dẫn tương đối bên dưới đều tính từ `E:\PWD301`. Báo cáo bàn giao phải dùng đường dẫn tuyệt đối khi liên kết file.

### 1.1. Bất biến bắt buộc

- Trước lần Admin duyệt đầu tiên: soạn trực tiếp; gửi lần đầu thì khóa sửa, phải thu hồi để sửa.
- Sau khi từng được duyệt: tất cả thay đổi hợp lệ vào DUY NHẤT một aggregate `CourseChangeRequest(change_type=COURSE_VERSION_CHANGESET, status=DRAFT)`; không phụ thuộc `as_draft`.
- Khóa từng công khai nhưng thiếu `approved_at` vẫn phải staging; không tạo ngày duyệt giả.
- Bản chờ duyệt đóng băng; duyệt đúng snapshot đã xem, nguyên tử, có audit; tab cũ phải nhận 409.
- Thu hồi/từ chối giữ lịch sử và đầy đủ đề xuất để sửa tiếp.
- Học sinh chỉ thấy nội dung đã duyệt; giảng viên thấy nháp hiệu lực; Admin thấy bản gửi đã niêm phong.
- Không bắt xác thực email để xem video; giữ đăng nhập, quyền đối tượng, ghi danh, đình chỉ, quét fail-closed, HLS và tiến độ máy chủ.
- Khi tắt chi tiết: vẫn thấy tổng điểm/đạt-trượt NẾU đã công bố; ba cột chi tiết PDF rỗng thật. Chính sách NEVER và thời điểm công bố vẫn có hiệu lực.
- Không rò đáp án, giải thích hoặc màu đúng/sai trong bài thi đang làm.
- Không thay đổi snapshot lượt thi, lịch sử điểm, audit hoặc migration đã áp dụng để làm test xanh.
- Không tạo Jinja/static backend/mock frontend; sửa SPA thật hiện có.
- Không commit, push, triển khai, migration/reset database hoạt động trong kế hoạch này.
- Chỉ thử SQL phá hủy dữ liệu trên target xác minh riêng, tên `pwd301_test_*`, có `PWD301_TEST_DB_DISPOSABLE=1`.
- Bảo vệ trình duyệt chỉ ở mức khả thi; không hứa chặn tuyệt đối chụp/quay màn hình, DevTools hay extension.

### 1.2. Những tài liệu phải đọc

1. `AGENTS.md`, `tasks/CURRENT.md`, các phần liên quan của `README.md`.
2. `docs/system/PWD301_SYSTEM_SPECIFICATION/CODING_AGENT_START_HERE.md`.
3. `business/01_BUSINESS_RULE_CATALOG.md`, `implementation/06_NON_NEGOTIABLE_INVARIANTS.md` dưới System Specification.
4. `implementation/WORKFLOW_SUPERSESSION.md`, `business/03_COURSE_MANAGEMENT.md`, `business/08_ASSESSMENT_ENGINE.md`.
5. Course lifecycle/state machine, API04/API12 và instructor/admin UI flows tương ứng.
6. `docs/database/PWD301_DATABASE_ARCHITECTURE/` cùng DDL course/question/assessment/index liên quan.
7. `docs/tasks/TASK-095_WORKFLOW_REPLACEMENT.md` và kế hoạch bàn giao này.

Tài liệu lịch sử chứa hướng dẫn duyệt từng bài hoặc staging tùy chọn đã bị thay thế. Không phục hồi nó từ Git, graphify, bộ nhớ hoặc báo cáo cũ. Không suy luận nhãn COMPLETED của task cũ là TASK-095 đã đạt.

## 2. Snapshot tiếp quản và cách đọc mức độ hoàn thành

Branch được kiểm tra khi viết bàn giao: `codex/workflow-remediation-20261015`.
HEAD: `838e8b5eee09f8c485102d6d2eba0a325765951d`. Nhiều file tracked đã sửa và nhiều file untracked; chúng là sản phẩm cần giữ. HEAD chưa chứa các thay đổi đó.

Các trạng thái sau không được đánh đồng:

| Trạng thái | Ý nghĩa |
|---|---|
| Đã triển khai | Có thay đổi source; chưa khẳng định chạy đúng mọi đường |
| Đã kiểm chứng tại checkpoint | Có kết quả thật trên phiên bản lúc chạy; phải chạy lại nếu source/fixture đổi |
| Còn lỗi/chưa kiểm chứng | Chưa có bằng chứng đạt hoặc đã có test fail |
| Nghiệm thu | TẤT CẢ gate ở phần 11 đạt trên cùng bản mã cuối cùng |

Ước lượng 70% từng trao đổi chỉ là ước lượng khối lượng, KHÔNG phải 70% test hoặc nghiệm thu. Không dùng phần trăm đó trong báo cáo chất lượng.

### 2.1. Những gì đã làm và còn thiếu theo từng yêu cầu

| Yêu cầu ban đầu | Thay đổi đã có | Bằng chứng hiện có | Việc phải hoàn tất |
|---|---|---|---|
| Dọn workflow cũ | Hợp đồng mới, pointer AGENTS/README/start-here; thay 6 kế hoạch và 9 báo cáo cũ bằng superseded; gate tài liệu | 4 test tài liệu và repo_check đạt tại checkpoint | Quét mâu thuẫn cuối, cập nhật graph sinh sau source freeze; không khẳng định xóa toàn bộ ký ức |
| Một nháp/một lần duyệt | Shared service, ever-approved boundary, sealed review version, successor draft, migration và COW thành viên | Các test lifecycle riêng; SQL concurrency 5 test; migration roundtrip 1 test | Lỗi marker bài học sau duyệt, graph lock ordering, blueprint câu hỏi nháp, full regression |
| Môn tiên quyết | Picker Cài đặt & Học vụ; lưu landing atomic; bỏ min_grade UI không có quy tắc lưu thật | Modal desktop/mobile có lựa chọn, không tràn; API mục tiêu có test | Chọn/lưu/reload thật và hoàn tất ma trận chu trình/concurrency |
| Video | Gỡ email gate, chặn raw video, HLS/quyền/Range, retry; sửa armor nhận nhầm route staging là tamper | HTTP matrix 25; Edge decode thật 320×180, time >1, readyState4, không media error | Chạy lại mã cuối; test server pacing; YouTube thật; container cuối có FFmpeg |
| PDF/toán | Offline MathJax SVG → svglib/ReportLab, font Linux, giới hạn tài nguyên; bỏ regex renderer | PDF Linux đã render và xem công thức; bản ẩn vẫn có 8.5/10/pass và ba cột trống | Tạo lại bằng image/source cuối, kiểm tra đủ ma trận chính sách/phân trang |
| Công tắc chi tiết | Gate dùng chung API/UI/PDF/lịch sử; tổng điểm theo release policy | Test chính sách riêng; đã phát hiện/sửa leak explanation qua serializers | Rà mọi endpoint, bài đang làm, NEVER, grade history; full regression |
| Nối từ | Renderer/controller dùng chung, SVG, phím, xóa nối, stable keys | DOM thật học sinh chọn 2 cặp trung tính, xóa, bàn phím desktop/mobile | Thi thật autosave/reload/reassign/group trùng; so preview và học sinh |
| Final test | Backend summary/lượt/resume/reason/count/display_score; nhãn Điểm, giữ điểm0 | Waiting room thật HIGHEST10 active3/3, LATEST0 exhausted2/2, 3 câu, không khóa tiên quyết giả | FIRST/AVERAGE/release/timing đầy đủ; chạy lại toàn bộ nhóm attempt/lease/autosave |
| Gửi cập nhật/hàng đợi | API mutation commit, alias cùng workflow, version token; bỏ dedup mất hàng | Test JWT lưu/reload và các vòng đời; Admin DOM history có hàng đã từ chối | Gửi nhiều loại thay đổi thật, nhiều khóa chờ, stale tab, lỗi rollback và history cuối |
| Ảnh bìa | Shared auth ảnh RESOURCE/COURSE_IMAGE, current/proposed, crop1280×720/16:9 | Public cover API6 test; Admin desktop/mobile ảnh loaded và không overflow | Khám phá/My courses/editor/crop cùng ảnh cuối, removal và broken asset |
| File của nháp | Ledger upload riêng, không lộ học sinh; scan/refreeze/manifest; retention giữ bytes lịch sử | Nhóm unit chuyên biệt xanh tại checkpoint | Chạy SQL batch, kiểm chứng attach→duyệt→detach→duyệt lần2, retention dài hạn |

### 2.2. Kết quả test có thật và giới hạn

- Full backend snapshot trước các sửa tiếp theo: **1660 passed, 389 failed, 47 errors, 100 skipped**, 1606.18 giây. Artifact `.superpowers/task095/backend-full.xml` và `.txt`. Đây là lần chạy THẤT BẠI.
- Một số fixture cũ tạo course PUBLISHED rồi dùng instructor service để xây baseline; workflow mới làm chúng staging đúng. Phải sửa setup fixture theo vòng đời hợp lệ, không tắt staging toàn cục.
- Có cả lỗi thật ngoài fixture; không được quy toàn bộ 389 failure cho fixture.
- Frontend toàn bộ từng đạt **314 pass**, trước những bổ sung sau đó. Cần đếm lại từ lần chạy cuối.
- SQL Server riêng từng đạt migration upgrade→downgrade→upgrade và 5 test concurrency. Không suy ra toàn bộ SQL đã xanh.
- Checkpoint mypy từng đạt 101 source files; lint/repo check từng đạt. Không còn giá trị chứng nhận sau khi source đổi.
- File `.superpowers/task095/file-governance-final.txt` hiện ghi 30 pass; tên chứa “final” không chứng minh toàn bộ nhiệm vụ đã final.
- File `assessment-regression.txt` còn ghi **25 failed,17 passed**, dừng sớm. Phải tái hiện/phân loại lại.
- Agent từng báo các nhóm 58 test asset/file/assessment lock, 52 ops, 6 cover, 7 armor xanh. Nếu thiếu log gắn mã cuối, chỉ là đầu mối để chạy lại.
- Batch SQL file/cover cuối chưa có xác nhận kết quả trong bàn giao này: coi CHƯA KIỂM CHỨNG, không suy đoán từ việc agent đã khởi chạy.
- Browser fixture có seed hoàn thành bài trước để mở video. Nó chứng minh playback, KHÔNG chứng minh chống tua hoặc server pacing.
- Live web/database chưa áp dụng thay đổi. Image live từng thiếu FFmpeg; database live từng thiếu CHECK mới. Không tuyên bố hệ thống hoạt động đã được sửa.

## 3. Bản đồ file để không sửa nhầm

| Nhóm | File source chủ yếu | Test/fixture cần đọc |
|---|---|---|
| Aggregate/lifecycle | `src/pwd301/services/course_workflow_service.py`, `course_service.py`, `lesson_service.py`, `completion_service.py`, `enrollment_service.py` | `tests/unit/test_unified_course_workflow.py`, `test_course_staging_draft.py`; API course changeset/prerequisite |
| COW đề/câu hỏi | `course_assessment_workflow.py`, `course_question_workflow.py`, `assessment_service.py`, `question_bank_service.py` | `test_course_assessment_review_lock.py`, `test_course_question_workflow.py` |
| File/bảo toàn | `file_service.py`, `retention_service.py`, `blueprints/api_files/routes.py` | `test_file_unified_authoring.py`, `test_course_review_assets.py`, API file/cover/video |
| Exam/kết quả | `assessment_student_service.py`, `attempt_service.py`, `blueprints/student/routes.py` | API assessment review/student exam; unit attempt/grading/autosave/lease/regrading |
| PDF | `result_pdf_service.py`, `pdf_math_service.py`, `tools/` MathJax; requirements/lock/Dockerfile | `tests/test_result_pdf_formatting.py`, policy tests và output PDF |
| Session/JWT aliases | `blueprints/instructor/routes.py`, `api_courses/routes.py`, `api_lessons/routes.py`, `admin/routes.py` | Unit unified workflow; API changeset và security |
| UI | `frontend/assets/js/views/{instructor,instructor-exams,student,admin}.js`, `api.js`, `ui.js`, `components/video-armor.js` | `tests/frontend/academic_settings_atomic.test.js`, `workflow_presentation.test.js`, `admin_review_identity_and_covers.test.js`, armor/preview/assessment tests |
| DB | models course/question_bank/assessment; `migrations/versions/unifiedcourse20261015_course_review_lifecycle.py` | SQL migration tests; `tests/integration/test_sqlserver_unified_course_workflow.py` |
| Hợp đồng | canonical docs, `scripts/repo_check.py` | `tests/unit/test_workflow_document_contract.py` |

Đọc function/caller hiện tại trước khi sửa; đường dẫn trong bảng là phạm vi tra cứu, không phải lệnh xóa hay quyền thay toàn file.

## 4. Tổ chức agent con và quy trình kiểm tra nhiều vòng

Yêu cầu “gấp 10 lần” được chuyển thành **10 vòng có mục tiêu và bằng chứng**, không tạo agent vô hạn hoặc yêu cầu chạy lại cùng test vô ích. Tuân thủ giới hạn concurrency môi trường. Nếu không hỗ trợ agent con, báo thiếu khả năng, không giả lập báo cáo agent độc lập bằng chính một agent.

### 4.1. Vai trò và ownership

- **Coordinator:** giữ hợp đồng, phân việc, tích hợp, không tự ký duyệt sản phẩm của mình.
- **Worker-Course:** lifecycle/lesson/graph/DB; sở hữu file core đã phân công.
- **Worker-Assessment:** question/blueprint/attempt/disclosure/PDF; chỉ sửa vùng diff backend đã thống nhất nếu dùng chung course_service.
- **Worker-Media-UI:** file/retention/video/cover và giao diện; chia nhỏ lại nếu môi trường cho phép.
- **Reviewer độc lập:** đọc source/diff/test, tìm bypass; không sửa file của worker trong lúc review.
- **Browser QA độc lập:** thao tác qua UI thật, quan sát network/console, không gọi thẳng service để giả kết quả thao tác.
- **SQL QA:** độc quyền target SQL khi chạy; không chạy hai pytest cùng database.

Worker giữ file riêng. Thay đổi file chung phải được coordinator phân vùng và chờ bên kia dừng. Mỗi thông điệp bàn giao ghi file/function, test RED, thay đổi, test GREEN, rủi ro. Không yêu cầu tất cả worker sửa cùng `course_service.py` đồng thời.

### 4.2. Mười vòng bắt buộc

| Vòng | Người thực hiện | Đầu ra/gate |
|---|---|---|
| 1 | Coordinator + agent đọc mới | Snapshot branch/HEAD/dirty/target; bảng từng yêu cầu → code → test → bằng chứng |
| 2 | Agent mapping | Call graph session/JWT/legacy/background; mọi cửa ghi/đọc và bypass được liệt kê |
| 3 | Worker theo domain | Test tái hiện từng lỗi còn mở, output RED đúng nguyên nhân |
| 4 | Worker theo domain | Sửa nhỏ nhất tại shared root cause; GREEN có log |
| 5 | Reviewer nghiệp vụ | Đối chiếu hợp đồng, state machine, release policy; reject nếu sai dù test xanh |
| 6 | Reviewer security/concurrency | IDOR/leak/scan/lease/race/stale tabs/transaction rollback; test phản ví dụ |
| 7 | SQL QA | Migration roundtrip + concurrency thật, dữ liệu/index/CHECK/audit đúng |
| 8 | Browser QA | Desktop/mobile, 3 vai trò, thao tác lưu/reload/vòng duyệt/video/thi/PDF thật |
| 9 | Reviewer fresh context + coordinator | Source freeze, OCR mọi file, full verifier; sửa finding thì quay lại vòng liên quan |
| 10 | Antigravity bàn giao; Codex kiểm chứng sau | Manifest/artifact/diff/hash đầy đủ; Codex tự chọn lại test và thử bypass, chưa triển khai |

Một vòng FAIL không được bỏ qua bằng cách đổi người review hoặc ghi “expected”. Reviewer phải có thể từ chối. Chỉ quay lại các gate bị ảnh hưởng, rồi chạy full cuối trên source ổn định.

## 5. P0 — Bảo toàn và lập lại baseline

- [ ] Ghi `Get-Location`, `git branch --show-current`, `git rev-parse HEAD`, `git status --short`, `git diff --stat` vào artifact mới, không sửa source.
- [ ] Liệt kê tracked và untracked; tạo manifest SHA256 các file thay đổi và fixture scripts. Backup chứa secret phải ở vùng private, không commit.
- [ ] Kiểm tra tiến trình đang chạy và command line trước khi dừng; không kill toàn bộ Python/Edge/Docker của người dùng.
- [ ] Xác nhận không còn agent/pytest cũ đang ghi file hoặc chiếm SQL target. Nếu thiếu thông tin, không khởi chạy một bộ purge song song.
- [ ] Đọc `tests/conftest.py` và `scripts/test_database_guard.py`: fixture SQL thực sự DELETE bảng và có thể KILL session. Đây là lý do target riêng là bắt buộc.
- [ ] Đọc baseline XML, nhóm theo root cause và owner; không dùng `.pytest_cache/lastfailed` làm nguồn duy nhất vì các lần chạy song song có thể ghi đè.
- [ ] Chọn một output directory mới, ví dụ `output/task095-antigravity/`; không ghi đè artifact cũ để tránh mất chứng cứ.
- [ ] Chạy tập regression ngắn để xác nhận môi trường; ghi lỗi setup riêng với assertion lỗi sản phẩm.

**Đạt:** có inventory và target an toàn, giữ nguyên thay đổi hiện hữu; coordinator biết từng failure thuộc ai. **Không đạt:** bắt đầu sửa mà không biết đang trên DB nào hoặc xóa source chưa commit.

## 6. P1 — Hoàn tất core workflow trước giao diện phụ thuộc

### 6.1. Lỗi marker bài học sau approval — ưu tiên cao nhất

Hiện có finding: bài học PUBLISHED sau apply có thể còn `change_request_id` trỏ aggregate đã terminal. Điều này làm clone/detach lần sau sai và baseline fingerprint bỏ sót bài vì lọc marker NULL. Phải tái hiện trên source hiện tại, không giả định chưa được sửa.

- [ ] Viết test: course đã duyệt → sửa lesson/attach file → gửi → Admin duyệt → fresh session đọc lesson PUBLISHED.
- [ ] Tiếp tục sửa content/detach → phải tạo hoặc dùng DRAFT aggregate mới, học sinh vẫn thấy bản trước; gửi/duyệt lần hai thành công.
- [ ] Assert marker của thành viên live không còn làm nó bị hiểu là draft; lịch sử reviewed IDs vẫn tồn tại trong submitted snapshot/audit.
- [ ] Test baseline review fingerprint thay đổi khi thành viên live hợp lệ thay đổi; không bị omission vì terminal marker.
- [ ] Sửa tại nhánh promotion/apply chung cho mọi thành viên liên quan; kiểm tra LearningUnit/Assessment/Question, không gán NULL hàng loạt vào proposal lịch sử.
- [ ] Chạy test file attach/detach thực sự đang fail trong `tests/api/test_file_api.py` cùng lifecycle/asset review tests.

**Đạt:** hai vòng duyệt liên tiếp không mất dữ liệu, không edit live trái phép và không phá snapshot lịch sử.

### 6.2. Ranh giới duyệt lần đầu và snapshot

- [ ] Tái hiện course APPROVED nhưng chưa PUBLISHED: instructor sửa phải staging; publish không được vô tình promote nháp chưa duyệt.
- [ ] Course cũ PUBLISHED thiếu approved_at vẫn staging và không backfill ngày giả.
- [ ] Initial pending khóa mọi mutation session/JWT/legacy/upload/status/order/question; GET không tạo nháp.
- [ ] Bản gửi chỉ apply thành viên snapshot; một draft không thuộc phiên bản gửi không được promote.
- [ ] Baseline fingerprint không thay đổi giả vì draft ngoài snapshot; nhưng phải đổi nếu nội dung live/asset identity thật đổi.
- [ ] Withdraw/reject lưu complete successor: metadata, units, lessons, resources, question revisions, assessment, rules, prerequisites và private asset ledger.

### 6.3. Lock ordering, graph và review token

- [ ] Đọc mọi caller khóa course/graph: author save, submit, approve, archive/trash, prerequisite mutation và các alias.
- [ ] Chốt cùng thứ tự khóa, kể cả route đã load/lock course trước khi gọi service. Không để đường graph→course và course→graph đối nghịch.
- [ ] SQL thật: 2 author sửa đồng thời không mất một field; chỉ một active aggregate; 2 reviewer chỉ một winner.
- [ ] SQL thật: 2 thay đổi prerequisite đối nghịch không tạo chu trình; deadlock không thành lỗi500 không xử lý.
- [ ] Admin approve/reject/withdraw gửi đúng request ID + review_version của bản đang xem; tab cũ409 và UI tải lại, không tự approve bản mới.
- [ ] Alias prerequisite cũ không được tạo approved edge bằng đường riêng; hoặc cùng aggregate hoặc lỗi rõ ràng sau kiểm tra quyền.
- [ ] Inject lỗi giữa apply: toàn bộ metadata/member/rules/graph/audit rollback, không có nửa khóa học đã công khai.

### 6.4. COW ngân hàng câu hỏi và blueprint

Finding cần tái hiện: câu hỏi ACTIVE mới trong draft có thể không được truy vấn blueprint nhận diện, làm publish báo available0 dù required1.

- [ ] Course đã duyệt → tạo câu hỏi ACTIVE trong draft → tạo assessment blueprint dùng đúng câu đó → publish trong draft.
- [ ] Preflight và materialize phải dùng effective instructor projection; không query live ACTIVE đơn thuần làm mất câu nháp.
- [ ] Seal IDs và map promotion đúng; sau approval assessment trỏ revision hợp lệ, học sinh nhận đủ câu.
- [ ] Trước approval học sinh không đọc được câu/choices/explanation/file nháp qua tìm kiếm, detail, API alias.
- [ ] Sửa/retire câu đã có lịch sử không phá attempt snapshot; regrade chỉ theo quyền/quy tắc được duyệt.
- [ ] Pending khóa đủ mọi mutator câu hỏi/revision/resources/status; test session và JWT.

### 6.5. Admin phải xem được tất cả nội dung mình duyệt

Finding: diff có thể chưa hiển thị QUESTION_REVISION, standalone accepted files, prerequisite tên dễ hiểu và metadata trước/sau. Không được có nút Duyệt nhưng màn hình báo0thayđổi khi snapshot có thay đổi.

- [ ] Truy từ `get_course_changeset_diff` tới `UI.renderCategorizedDiffHtml` và Admin caller, lập contract JSON thật.
- [ ] Test backend payload chứa đủ current/proposed của metadata, question stem/choices/explanation/status, file/version, prerequisite course code/title, rules, units/lessons/assessment.
- [ ] Dùng submitted snapshot làm nguồn proposal; không dùng live draft của tác giả thay bản đã gửi.
- [ ] Có thể bổ sung `question_changes`, `file_changes`, `current_course_metadata`, `prerequisite_changes`; đây là tên đề xuất, phải thống nhất producer/consumer/test trước khi dùng.
- [ ] Test UI không bịa giá trị mặc định80%/minGPA5, giữ giá trị0/false/null có ý nghĩa; escaped text và safe math, không innerHTML dữ liệu chưa sanitize.
- [ ] Actual Admin DOM: gửi một draft chỉ đổi câu hỏi, một draft chỉ đổi file, một draft chỉ đổi tiên quyết; cả ba phải có diff đọc hiểu được trước khi duyệt.
- [ ] Ảnh bìa trước/sau có nhãn, kể cả đề xuất bỏ ảnh; missing/unsafe asset có lỗi có nghĩa, không giả như đã tải.

## 7. P2 — File, video và ảnh bìa

### 7.1. File nháp và lịch sử

- [ ] Kiểm tra `uploaded_file_assets` giữ private provenance và `new_file_assets` là tập accepted sạch; background scan PASS không tự công khai file chưa duyệt.
- [ ] Học sinh không thấy/tải standalone upload của draft ở list, detail, download, stream, thumbnail hoặc link đoán UUID.
- [ ] Pending không upload thay revision/trash/restore/attach/detach qua đường phụ.
- [ ] Approved referenced bytes không sửa tại chỗ: upload replacement và đổi reference qua draft.
- [ ] Khi approval: recheck revision/blob/hash/scan identity; scan ERROR/QUARANTINED/PENDING hoặc revision mới trả conflict phù hợp và rollback.
- [ ] Retention không xóa bytes/scan/version/blob được retained sealed manifest hoặc accepted history tham chiếu; reject/withdraw không mất file.
- [ ] Có positive test file rác hết hạn không được tham chiếu vẫn prune; không giải quyết bằng việc tắt retention toàn bộ.
- [ ] Chạy SQL thật các nhóm file/cover sau khi SQL owner trước đã release slot.

### 7.2. Video

- [ ] Tài khoản chưa xác thực email, đã ghi danh, chưa đình chỉ, file CLEAN: mở bài và play thành công.
- [ ] Tài khoản ngoài khóa/đình chỉ, file unsafe: bị chặn đúng; không gỡ security để chữa playback.
- [ ] Learner raw download và raw `/api/files/<id>/stream` bị chặn, kể cả Range; instructor/Admin có quyền vẫn Range206.
- [ ] FFmpeg có trong image/runtime cuối; thử asset mới/cache rỗng, không chỉ asset đã convert sẵn.
- [ ] HLS manifest/key/segment có auth, token ngắn hạn và replay/expired behavior; không xuất direct storage path.
- [ ] Player route staging không bị armor blackout; sau commit xóa/ẩn watermark thật vẫn thực thi bảo vệ đã thiết kế.
- [ ] Fatal HLS, init exception, retry, đổi lesson, dispose có cleanup; không duplicate heartbeat/listener/timer.
- [ ] YouTube dùng IFrame API thật; có play/time/state, lỗi153 hoặc chặn embedding hiện thông báo và thao tác phù hợp. Nếu môi trường không cho chạy thật, đánh dấu gate chưa đạt, không mock PASS.
- [ ] Pacing: đo thời gian thực máy chủ, gửi view_fraction1/seconds giả hoặc tua nhanh không hoàn thành tức thì; chỉ đủ heartbeat hợp lệ mới đạt. Seed completion trước đó không tính là bằng chứng.

### 7.3. Ảnh bìa

- [ ] Upload/crop ảnh có chi tiết ở bốn góc, chọn vùng1280×720 và lưu.
- [ ] So cùng asset/crop tại Khám phá, Khóa học của tôi, editor, crop, Admin initial và Admin update.
- [ ] Đo bounding box16:9 sai số làm tròn tối đa2px; object-fit/position nhất quán, không fixed-height làm méo.
- [ ] Test desktop1440×900 và mobile390×844; không horizontal overflow, tải ảnh thực có naturalWidth/Height, không chỉ backgroundplaceholder.
- [ ] RESOURCE và COURSE_IMAGE hợp lệ được phục vụ cùng shared thumbnail policy; ảnh của khóa khác/unsafe không được lách quyền.

## 8. P3 — Thi, matching và kết quả/PDF

### 8.1. Đồng bộ trạng thái final test

- [ ] Backend là nguồn duy nhất cho attempts_used/limit, active attempt, can_resume, can_start, start_block_reason, actual question count và display_score.
- [ ] Course lesson card, exam list, waiting room, history cùng giá trị sau submit/reload; không default0/1 hoặc30câu.
- [ ] Active attempt ở lượt cuối vẫn tiếp tục được; exhausted không biến thành thiếu tiên quyết; quá hạn, chưa mở, đang làm, đã nộp/chấm/đạt/trượt phân biệt rõ.
- [ ] Final prerequisite không tính chính final vào tập bài cần hoàn thành; hết lượt không tự đánh dấu hoàn thành.
- [ ] Fixture điểm FIRST2/LATEST0/HIGHEST8/AVERAGE(2+8+0)/3: hiển thị đúng chính sách và precision của hệ thống, giữ0.
- [ ] Loại lượt chưa chấm/không hợp lệ theo contract; lịch thi/current period/release policy không bị bỏ qua. best_attempt_id vẫn mang nghĩa lượt cao nhất.
- [ ] Actual browser: làm/nộp từ UI rồi quay lại card/list/waiting/history, không sửa DB để giả số lượt đã đồng bộ.

### 8.2. Matching dùng chung

- [ ] Preview và học sinh dùng cùng renderer/controller, cùng key semantics; khác duy nhất quyền và chế độ phản hồi.
- [ ] Hai group có text lựa chọn trùng nhau; nối bằng stable key không lẫn group.
- [ ] Chuột/touch/bàn phím chọn trái→phải, đổi cặp, gỡ một cặp, xóa hết; line SVG nằm đúng anchor sau resize/scroll.
- [ ] Làm bài thi thật: nối2cặp → chờ autosave response thành công → reload → acquire/resume lease hợp lệ → thấy đúng2cặp.
- [ ] Mở tab thứ2: không có hai lease cùng ghi; packet cũ/retry sai thứ tự không ghi đè câu trả lời mới.
- [ ] Active exam DOM và API không có answer key/correctness/explanation; giữ màu trung tính. Sau nộp chỉ có feedback nếu policy cho phép.
- [ ] Preview read-only không ghi attempt/progress học sinh; exit/reopen không leak event handler.

### 8.3. Ma trận quyền kết quả

Chạy mọi tổ hợp `allow_student_view_results` bật/tắt × release ngay/chưa đến hạn/đã đến hạn/NEVER theo policy có thật. Kiểm tra course card, exam list/detail, attempt delivery/review, history, grade history, PDF và URL truy cập trực tiếp bằng session/JWT.

| Điều kiện | Tổng điểm/đạt-trượt | Đáp án chọn/đúng-sai/điểm câu/giải thích |
|---|---|---|
| Tắt chi tiết + đã công bố | Hiện theo policy | Ẩn hoàn toàn; PDF ba cột rỗng |
| Tắt chi tiết + chưa công bố | Chưa được lộ | Ẩn |
| Bật chi tiết + được policy cho phép | Hiện | Hiện phần được phép |
| NEVER + đã công bố | Hiện tổng điểm/đạt-trượt đã công bố | Result API trả danh sách câu hỏi rỗng; UI/history không có chi tiết; PDF không tái tạo chi tiết câu hỏi/đáp án từ đường khác |
| NEVER + chưa công bố | Tổng điểm và đạt-trượt chưa được lộ | Không có chi tiết; export phải tôn trọng gate công bố, không tạo PDF lộ điểm |
| Đang làm bài | Chỉ dữ liệu phục vụ làm bài được phép | Không đáp án chuẩn, correctness, explanation hoặc change_reason tiết lộ đáp án |

Không chỉ CSS display:none: response không được gửi trường nhạy cảm cho học sinh không có quyền. Instructor/Admin có quyền xem độc lập; không vô tình ẩn công cụ chấm của họ.

**Nghiệm thu chính công tắc cấu hình:** Instructor mở editor kiểm tra, tìm nhãn cho phép xem chi tiết kết quả, tắt → Lưu → reload → xác nhận vẫn tắt. Với khóa đã duyệt, learner vẫn dùng cấu hình được duyệt cũ trong khi thay đổi nằm ở draft. Gửi duyệt → thử toggle khi pending phải bị khóa cả UI/API → Admin duyệt → learner UI/API/PDF chuyển sang chính sách mới. Sau đó bật lại và lặp vòng lưu/reload/duyệt. Không được chỉ seed cờ database rồi tuyên bố chức năng cấu hình hoạt động. Nếu đề đã có lượt làm khóa các field khác, công tắc này chỉ được thay đổi theo đúng danh sách field hợp lệ của hợp đồng, không mở khóa cấu trúc đề.

### 8.4. PDF và math production

- [ ] Dùng phân số lồng, căn, mũ/chỉ số, tích phân có cận, giới hạn, vector, ma trận, matrix trộn tiếng Việt, `\text{nếu}`, stem+selected-answer nhiều dòng.
- [ ] Render offline trong Linux image cuối với font production, không dựa font Windows hoặc network CDN.
- [ ] Kiểm tra PDF trực quan từng trang bằng Poppler/screenshot; text extraction chỉ bổ sung, không thay thế.
- [ ] Công thức không thành raw TeX/rác, không mất ký hiệu, không đè cột, không bị cắt ở page break; bảng/header/footer đọc được.
- [ ] Tắt chi tiết: ba cột selected/result/points thực sự rỗng, không dấu gạch, không hidden text; tổng điểm/đạt-trượt đã công bố vẫn đúng.
- [ ] TeX lỗi/quá dài, SVG external references hoặc renderer timeout có xử lý an toàn, hữu hạn; không crash worker/SSRF/đọc file máy chủ.
- [ ] Dependency khóa phiên bản; renderer regex cũ không còn đường chạy sau chuyển đổi; không fallback làm hỏng toán rồi báo thành công.

## 9. Runbook trình duyệt thật — thao tác bắt buộc

### 9.1. Chuẩn bị môi trường riêng

Tái sử dụng `.superpowers/task095/browser_server.py`, seed scripts và manifest sau khi đọc chúng. Server cũ có thể đang nạp source cũ; phải xác minh PID/commandline rồi restart đúng tiến trình riêng. `--reset` chỉ được chạy sau khi kiểm tra script trỏ `pwd301_test_browser.sqlite`, không phải live.

Tạo tài khoản riêng: Admin được quyền duyệt, hai instructor, learner chưa xác thực email có ghi danh, learner ngoài khóa, learner đình chỉ. Password/token giữ private; không đưa credentials/HAR nhạy cảm vào artifact công khai.

Tạo ít nhất: course mới chưa duyệt; course đã duyệt; course legacy approved marker NULL;3course gửi lần đầu;3course gửi cập nhật; prerequisite A/B/C; final exam nhiều chính sách; MC/matching/toán; ảnh crop; file sạch/chờ/quarantine và video mới. Dữ liệu setup được seed để tạo tình huống, nhưng hành vi đang nghiệm thu phải thao tác thật.

Nếu fixture attempt cũ quá hạn, tạo fixture mới qua đường hợp lệ. Không sửa deadline production hoặc tắt lease/fullscreen để làm test chạy được.

**Chuỗi lệnh hiện có, chỉ dùng sau khi đọc và xác nhận guard:** chạy ở PowerShell riêng. Trước tiên xác minh không có process đang dùng port51095/database fixture. Nếu có, đọc CommandLine bằng Get-CimInstance Win32_Process và dừng chỉ PID đã xác minh là browser_server.py của workspace này; không dừng process lạ.

```powershell
Set-Location E:\PWD301
$env:PYTHONPATH = 'src;.'
$env:PYTHONUTF8 = '1'
.venv/Scripts/python.exe -c "import runpy,sys; sys.argv=['browser_fixture','--reset']; runpy.run_path('.superpowers/task095/browser_server.py',run_name='browser_fixture')"
.venv/Scripts/python.exe .superpowers/task095/browser_seed_quiz.py
```

Lệnh đầu phải in `DISPOSABLE_BROWSER_READY http://127.0.0.1:51095`, chỉ reset SQLite fixture; run_name khác __main__ nên chưa chạy server. Lệnh seed quiz phải in thông báo cập nhật hai lesson. Kiểm tra exit code mỗi bước trước khi tiếp tục. Fixture reset làm đổi password/IDs, phải dùng manifest mới.

Nếu chưa có `.superpowers/task095/storage/generated.mp4`, cần FFmpeg thật có trong PATH và tạo asset riêng:

```powershell
ffmpeg -y -f lavfi -i testsrc=size=320x180:rate=24 -t 6 -c:v libx264 -pix_fmt yuv420p .superpowers/task095/storage/generated.mp4
.venv/Scripts/python.exe .superpowers/task095/browser_seed_native.py
.venv/Scripts/python.exe -c "import runpy; from pathlib import Path; r=runpy.run_path('.superpowers/task095/browser_server.py',run_name='browser_fixture'); s=runpy.run_path('.superpowers/task095/seed_assessments.py'); ctx=r['app'].app_context(); ctx.push(); s['seed'](Path('.superpowers/task095')); ctx.pop()"
```

Native seed phải in `NATIVE_FIXTURE_READY`; assessment seed phải không có assertion/error và manifest có HIGHEST/LATEST. Không chạy seed hai lần vào cùng fixture nếu script chưa idempotent. Các script hiện chỉ tạo bộ tối thiểu; phải bổ sung tài khoản/case còn thiếu ở mục9.1. Chạy seed khi server đã dừng tránh source/session cũ giữ dữ liệu.

Khởi chạy server trong terminal riêng để dễ quản lý, giữ terminal đó:

```powershell
.venv/Scripts/python.exe .superpowers/task095/browser_server.py
```

Mở `http://127.0.0.1:51095`, dùng credentials riêng trong fixture. Chạy từng script browser hiện có sau khi xác nhận chúng đọc manifest mới. Kết thúc dùng Ctrl+C tại đúng terminal server; xác minh port51095 không còn listener. Không reset để cleanup nếu chưa lưu evidence và chưa chắc target.

### 9.2. Kịch bản B01 — toàn vòng đời khóa học

1. Instructor mở trang tạo mới rồi rời đi, reload: không có course/draft mới vì chỉ điều hướng.
2. Tạo/lưu course mới; sửa title/cover/outcome/prerequisite/chapter/lesson/file/question/quiz/rules. Chưa sinh yêu cầu duyệt lẻ.
3. Gửi lần đầu. Thử sửa qua UI, session và JWT: bị khóa; Admin thấy đúng snapshot.
4. Thu hồi, sửa một trường, gửi lại; Admin duyệt. Learner thấy bản này.
5. Instructor sửa tất cả nhóm trên; reload: đề xuất còn đủ, learner vẫn thấy bản đã duyệt, duy nhất1aggregate DRAFT.
6. Gửi một lần; mở Admin tabA và tabB. Instructor không sửa được khi pending.
7. Admin tabA từ chối; lý do và history còn; instructor có đầy đủ nháp để sửa/gửi lại.
8. Admin tabB dùng token cũ:409, không áp dụng phiên bản khác.
9. Gửi lại và duyệt toàn bộ; learner refresh thấy đúng đồng bộ mọi thành phần.
10. Sửa lesson và detach file sau approval lần này; gửi/duyệt lần tiếp. Không lỗi marker cũ, không lộ trước approval.

Chụp mỗi mốc chính, ghi network action/status, request/version đã che ID khi trình bày cho học sinh, DB assertion trước/sau và audit. Một mốc fail khiến B01 FAIL.

### 9.3. Kịch bản B02 — tiên quyết và hàng đợi

1. Mở Intro → Cài đặt & Học vụ → chọn course tiên quyết → Thêm → Lưu thay đổi.
2. Reload và mở lại modal: lựa chọn còn đúng; xóa/lưu/reload cũng đúng.
3. Course đã duyệt: learner chưa thấy tiên quyết mới trước approval; sau approval mới áp dụng.
4. Thử A→B→C→A và hai tab thêm A→B/B→A: không có cycle persisted.
5. Admin có ít nhất3course ban đầu và3update đang pending: xem được tất cả qua list/pagination đúng, badge phản ánh tổng chính xác.
6. Duyệt một/từ chối một/thu hồi một: pending giảm đúng, history tăng đúng; history không có nút thực thi sai trạng thái.

### 9.4. Kịch bản B03 — video và ảnh bìa

1. Learner chưa verified đăng nhập, mở lesson có video mới, play; chờ hình chuyển động và time tăng, kiểm tra audio nếu fixture có.
2. Network có HLS manifest/key/segment hợp lệ; videoWidth/Height>0, media.error=null. HTTP200 một mình chưa đạt.
3. Pause/resume/chuyển lesson/retry lỗi có kiểm soát; không phát chồng, không leak listener.
4. Thử raw video, ngoài khóa, unsafe file, token hết hạn; đúng deny. Thực hiện pacing ở mục7.2.
5. Kiểm tra YouTube thật và crop tại tất cả bề mặt mục7.3, trên2viewport.

### 9.5. Kịch bản B04 — thi và matching

1. Learner hoàn thành prerequisite bằng luồng hợp lệ, mở final: count đúng đề thật và chưa có điểm nếu chưa làm.
2. Bắt đầu qua pledge/fullscreen UI thật; nối cặp, đổi cặp, xóa, chọn lại; quan sát autosave response.
3. Reload/resume, thử tab thứ2 và packet cũ; chỉ một lease có quyền ghi.
4. Nộp bài; bấm lại/retry không tạo lượt hoặc điểm kép.
5. So card/list/waiting/history/PDF; “Điểm” là điểm đạt được theo policy, không phải ngưỡng đạt.
6. Active ở lượt cuối vẫn resume được; hết lượt không nút bắt đầu mới hoặc thông báo thiếu prerequisite giả.
7. Làm đủ FIRST/LATEST/HIGHEST/AVERAGE và điểm0, lịch chưa mở/quá hạn, chính sách kết quả ở mục8.3.

### 9.6. Kịch bản B05 — Admin xem đủ rồi duyệt

1. Gửi draft chỉ có sửa câu hỏi; Admin đọc thấy stem/choices/explanation trước/sau phù hợp quyền.
2. Gửi draft chỉ có standalone file; Admin mở đúng phiên bản an toàn, thấy tên/kích thước/version thay đổi.
3. Gửi draft chỉ có tiên quyết/rules; Admin thấy tên course và giá trị thật, không UUID trần hoặc giá trị bịa.
4. Gửi draft hỗn hợp và thay ảnh: tổng thay đổi đúng, không nhóm bị bỏ; approve áp dụng chính nội dung đã xem.
5. Thay asset scan/revision sau khi gửi trong fixture kiểm thử: approve conflict/rollback, UI giải thích và tải lại.

### 9.7. Bằng chứng browser bắt buộc

Mỗi case lưu: mã test, thời gian/timezone, source manifest hash, browser/version, viewport, tài khoản/role không có password, fixture IDs private, bước thực tế, expected/actual, screenshot trước/sau, console errors, network assertion đã redacted và PASS/FAIL/BLOCKED. BLOCKED không được tính PASS.

Các script có sẵn `browser_root.cjs`, `browser_matching.cjs`, `browser_learning.cjs`, `browser_media_proof.py` là điểm bắt đầu. Phải đọc/sửa assert để cover các bước thiếu; không chỉ chạy rồi sao số cũ. Thi thật autosave/reload và tiên quyết chọn/lưu/reload chưa có bằng chứng hoàn chỉnh ở bàn giao này.

## 10. Lệnh kiểm tra và quản lý artifact

### 10.1. SQLite memory an toàn

Đọc guard và testing config trước khi chạy. Trong PowerShell riêng tại root:

```powershell
$env:PYTHONPATH = 'src;.'
$env:TEST_DATABASE_URL = 'sqlite:///:memory:'
$env:DATABASE_URL = 'sqlite:///:memory:'
$env:SEED_DEMO_DATA = '0'
$env:PYTHONUTF8 = '1'
.venv/Scripts/python.exe -c "import os; from scripts.test_database_guard import require_disposable_database; require_disposable_database(os.environ['TEST_DATABASE_URL'])"
.venv/Scripts/python.exe -m pytest tests/unit/test_unified_course_workflow.py tests/unit/test_course_question_workflow.py tests/unit/test_course_review_assets.py tests/unit/test_course_assessment_review_lock.py tests/unit/test_file_unified_authoring.py -q
```

Mỗi lệnh phải kiểm `$LASTEXITCODE`; dừng và sửa khi khác0, không coi PowerShell chạy đến dòng sau là đạt. Test RED phải fail bởi assertion mong muốn, không import error/thiếu dependency.

### 10.2. SQL Server riêng — chỉ một owner

Đọc `.superpowers/task095/sql_target.py` trước. Wrapper hiện cố định `pwd301_test_task095_20261016`, lấy cấu hình kết nối private rồi đổi database/host, không in password. Nếu môi trường khác, xây target guard tương đương; không copy URL live vào log.

```powershell
$env:PYTHONPATH = 'src;.'
.venv/Scripts/python.exe .superpowers/task095/sql_target.py -m pytest tests/integration/test_sqlserver_unified_course_workflow.py -q
.venv/Scripts/python.exe .superpowers/task095/sql_target.py -m pytest tests/unit/test_file_unified_authoring.py tests/api/test_course_cover_media_authorization.py -q
```

Migration roundtrip hiện có lệnh dưới đây; đọc `tests/integration/test_sqlserver_migration_roundtrip.py` trước, vì nó thực hiện upgrade/downgrade trên target. Chỉ chạy khi target riêng an toàn và SQL slot rảnh:

```powershell
.venv/Scripts/python.exe .superpowers/task095/sql_target.py -m pytest tests/integration/test_sqlserver_migration_roundtrip.py::test_sqlserver_migrations_upgrade_downgrade_upgrade_roundtrip -q
```

Expected:1passed,0failed,0errors,0skipped; skipped do thiếu URL là chưa chạy. Kiểm tra upgrade head, downgrade base, upgrade head, constraints/index/nullable/FK/default và dữ liệu đại diện. Không chạy downgrade live. Không sửa migration cũ để tránh DEFAULT constraint error; migration mới hiện đã có xử lý riêng, phải kiểm chứng lại. Sau SQL run đóng connection/process của đúng target; không drop database khác hoặc kill session toàn server.

### 10.3. Verifier cuối và frontend

Sau source freeze, ghi output cả stdout/stderr và exit code. Preferred aggregate:

```powershell
./scripts/verify.ps1
```

Nếu chạy tách để lưu JUnit/resource control, phải cover đủ chính các bước script: repo_check, compileall, ruff check, ruff format --check, mypy, toàn bộ frontend Node, toàn bộ pytest. Không bỏ một bước rồi gọi “verify toàn bộ”.

```powershell
$FrontendTests = @(Get-ChildItem tests/frontend -Filter '*.test.js' -File | Sort-Object FullName | Select-Object -ExpandProperty FullName)
node --test --test-concurrency=2 --test-reporter=junit --test-reporter-destination=output/task095-antigravity/frontend-final.xml $FrontendTests
.venv/Scripts/python.exe -m pytest --junitxml=output/task095-antigravity/backend-final.xml
```

Tạo thư mục artifact trước. Đọc XML để đếm pass/fail/error/skip thật. 100skip cũ không được tính pass; phân loại lý do từng nhóm, gate SQL bắt buộc phải được chạy riêng dù SQLite skip nó. Không dùng `--maxfail` cho bằng chứng full cuối.

### 10.4. Sửa fixture đúng cách

- Test đang kiểm nghiệp vụ khác cần baseline published: dựng baseline qua quy trình Admin hợp lệ hoặc helper fixture rõ ràng mô phỏng thiết lập lịch sử; sau đó mới bắt đầu hành vi instructor đang test.
- Không monkeypatch `should_stage` luôn false, không tắt scan/release/lease, không đổi expected sang hành vi sai chỉ để xanh.
- Fixture `is_email_verified` readonly phải dùng dữ liệu chuẩn như email_verified_at khi phù hợp model; không thêm setter sản phẩm chỉ chữa fixture.
- Mỗi nhóm sửa fixture phải có reviewer xác nhận assertion nghiệp vụ cũ vẫn mạnh và test workflow mới vẫn bắt được bypass.
- Chạy failure selection từ XML để phản hồi nhanh, sau đó full suite mới chứng nhận.

### 10.5. Review cuối và nguồn hướng dẫn

- OCR delegate preview/rule trên danh sách file thật, đọc mọi diff/untracked mới; lưu coverage từng file. Không truyền tất cả paths thành một chuỗi làm OCR bỏ file.
- Không để reviewer tự xóa finding vì worker nói “đã sửa”; reviewer tự chạy counterexample.
- Graphify là dữ liệu sinh: chỉ sau source freeze mới tái tạo/index; nếu xóa cache thì xác minh absolute target nằm trong `E:\PWD301\graphify-out`, không xóa code/source hoặc directory tính sai.
- Nếu graphify không parse SQL, ghi rõ giới hạn; SQL phải được review canonicalDDL/test thật, không tuyên bố graph bao phủ hết.
- Note Codex liên quan đã được gửi và một số quy tắc mới đã hiện trong registry. Không có bằng chứng “xóa sạch bộ nhớ”. Antigravity không sửa trực tiếp memory registry của Codex; phần ghi nhớ tiếp theo để Codex xử lý theo cơ chế note được phép.
- Quét secret trong changed/untracked files và artifact; browser_credentials không đưa vào tài liệu chia sẻ. Không dùng token thật trong screenshot/HAR.

## 11. Definition of Done — điều kiện thành công

Chỉ ghi “sẵn sàng để Codex verify” khi tất cả mục sau có link bằng chứng:

- [ ] Mỗi yêu cầu gốc có traceability: rule → file/function → regression test → browser/API/SQL evidence → reviewer.
- [ ] Không còn blocker ở phần6; repeat approval cycle, blueprint draft và Admin full diff đạt.
- [ ] Full verifier source cuối: zero failed, zero errors; skip được nêu riêng và mọi gate bắt buộc đã chạy ở môi trường tương ứng.
- [ ] SQL migration/concurrency/file/graph/rollback thật đạt, target được xác minh và live không bị đụng.
- [ ] Browser B01–B05 desktop/mobile đạt, không console exception liên quan, không UI thao tác giả/API mocked.
- [ ] Matching exam autosave/reload/lease; final state/score0/count; result disclosure matrix đạt.
- [ ] HLS decode cache rỗng, no-email learner, raw deny, server pacing và YouTube thật có bằng chứng riêng.
- [ ] PDF Linux production visual toàn bộ trang đạt; chi tiết ẩn rỗng thật; công thức đủ nhóm.
- [ ] Học sinh không đọc/tải proposal qua bất kỳ đường đã map; lịch sử và tệp tham chiếu được giữ.
- [ ] OCR review mọi file source cuối; không finding nghiêm trọng chưa xử lý hoặc bỏ qua không được chấp thuận.
- [ ] Canonical docs và index không còn chỉ dẫn trái hợp đồng; WF01–WF10 chỉ được chuyển VERIFIED theo đúng bằng chứng.
- [ ] Source hash trước/sau verification không đổi; nếu sửa sau test, chạy lại gate bị ảnh hưởng và full cuối.
- [ ] Không commit/push/deploy/live migrate/reset; ghi chính xác thao tác môi trường đã làm.

Nếu bất kỳ checkbox còn trống, trạng thái là IN_PROGRESS/BLOCKED theo lý do thật. Không ghi “hoàn tất100%” hoặc đánh dấu test chưa chạy là “dự kiến pass”.

## 12. Bộ bàn giao bắt buộc để Codex verify độc lập

Tạo `docs/tasks/TASK-095_ANTIGRAVITY_HANDOFF_REPORT.md`, cùng artifact mới. Báo cáo phải có:

1. **A — Scope/sources:** yêu cầu đã xử lý, hợp đồng dùng, branch/HEAD và dirty manifest; phạm vi không làm.
2. **B — Reuse:** helper/service/component đã tái sử dụng; lý do dependency mới nếu có.
3. **C — Per-file:** file/function thay gì và vì sao; phân biệt code có trước bàn giao và code Antigravity bổ sung.
4. **D — Removal:** logic/endpoint/fallback/tài liệu cũ đã gỡ; chứng cứ không còn đường chạy.
5. **E — Debt:** limitation thật, owner, trigger, safeguard, review point; không tự chấp nhận thiếu yêu cầu bắt buộc.
6. **F — Verification:** command chính xác, target/môi trường, timestamp, source hash, exit code, pass/fail/error/skip, artifact link và ai chạy.
7. **G — Remaining:** lỗi chưa sửa/test chưa chạy, môi trường bị chặn, ảnh hưởng và bước kế tiếp.
8. Danh sách agent/vòng review, finding, test RED/GREEN, phản biện và resolution; không ghi agent không tồn tại.
9. Browser case matrix + screenshots/console/network đã redacted; PDF và ảnh render từng trang; migration/concurrency logs.
10. Xác nhận thay đổi source cuối sau full test là không có, hoặc liệt kê và chạy lại đúng gate.

Các artifact cũ `.superpowers/task095/` và `output/pdf/task095/` chỉ là tài liệu đối chiếu. Giữ bản cũ và đặt bản mới riêng. Không đóng gói secret hoặc raw answer của học sinh thật.

### 12.1. Quy trình Codex kiểm chứng khi nhận lại

Codex sẽ không chỉ đọc báo cáo. Codex sẽ xác minh branch/dirty/hash, đọc diff và canonical contract, chạy lại regression chọn độc lập cùng full gate thích hợp, dùng trình duyệt thực kiểm B01–B05, thử bypass session/JWT/legacy, kiểm SQL concurrency và PDF production. Nếu tìm thấy lỗi, mở lại đúng nhóm, yêu cầu Antigravity sửa rồi kiểm lại. Chỉ sau nghiệm thu riêng mới bàn đến triển khai môi trường hoạt động.

### 12.2. Prompt gửi Antigravity

> Tiếp quản TASK-095 trong E:\PWD301 theo `docs/superpowers/plans/2026-10-16-task095-antigravity-handoff.md` và hợp đồng WORKFLOW_SUPERSESSION được dẫn trong đó. Đọc toàn bộ trước khi sửa. Giữ mọi thay đổi chưa commit. Thực hiện10vòng với agent con độc lập, ownership file rõ ràng và SQL độc quyền. Ưu tiên blocker lifecycle lần duyệt2, blueprint draft và Admin full diff, rồi hoàn tất các gate. Không nới test/security để xanh; không dùng bằng chứng cũ làm nghiệm thu source mới. Chạy UI thật desktop/mobile/API/SQL/PDF như runbook. Không commit, push, deploy hoặc đụng DB live. Bàn giao báo cáo A–G, traceability, source hashes, toàn bộ log/test counts và artifact cho Codex verify; còn thiếu bất kỳ gate nào phải ghi rõ chưa hoàn thành.

