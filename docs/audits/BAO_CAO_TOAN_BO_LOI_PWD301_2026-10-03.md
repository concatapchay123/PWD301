# Báo cáo lỗi PWD301: backend, frontend và thao tác nghiệp vụ

**Ngày kiểm tra:** 03/10/2026, múi giờ Asia/Bangkok.  
**Checkout:** `E:\PWD301`; HEAD `d64ffe4` cộng các thay đổi chưa commit đã có trước cuộc kiểm tra.  
**Loại công việc:** kiểm tra và lập báo cáo; không sửa mã sản phẩm, không chạy migration upgrade, không sửa điểm/dữ liệu thật.  
**Báo cáo giải pháp:** [Hướng khắc phục và kiểm thử](BAO_CAO_HUONG_KHAC_PHUC_KIEM_THU_PWD301_2026-10-03.md).

## 1. Kết luận cần xử lý trước

Lỗi “Bảng điểm & Bài nộp” đã được tái hiện trên Edge với phiên đăng nhập giảng viên đang mở. Nguyên nhân trực tiếp là route kết quả sinh viên bắt quá rộng, chặn route kết quả giảng viên. Ba dạng URL giảng viên đều đi vào renderer sinh viên. Với URL có ID trong đường dẫn, ID sai chứa `#`; phần phía sau bị trình duyệt coi là fragment nên request thực tế trở thành **`GET /student/attempt/` → 404**.

Sửa route chỉ giải quyết lỗi vào màn hình. Các vấn đề dữ liệu phía sau gồm mất bài chờ chấm tự luận, tính bài đang làm như không đạt, API tổng quan chấm bài luôn rỗng, nhập điểm không hợp lệ gây 500, chấm nhầm loại câu và thiếu kiểm soát phiên bản khi hai người cùng sửa điểm. Một số màn hình còn tạo thông tin học vụ/phúc khảo không có nguồn dữ liệu thật.

Danh mục dưới đây bảo toàn **15 mục từ báo cáo cũ**, đối chiếu trạng thái hiện tại, và bổ sung **24 phát hiện hiện tại** ở mã nguồn, thực nghiệm hoặc chất lượng quy trình. Chúng không phải 39 lỗi độc lập đang mở: N10/N11 liên quan SEC-001/ACAD-001; các vấn đề khác có thể cùng nguyên nhân. Phần chưa kiểm chứng được ghi riêng. “Toàn bộ” trong tài liệu này là toàn bộ mục của hai báo cáo đầu vào cộng các lỗi tìm được trong phạm vi kiểm tra; không phải chứng nhận đã phát hiện mọi lỗi có thể tồn tại trong hệ thống.

## 2. Nguồn, bằng chứng và cách phân loại

### 2.1. Hai báo cáo đầu vào đã đọc

1. `C:\Users\LENOVO\.gemini\antigravity\brain\b2558e9a-f0f6-4633-9f1f-e42baf782ce5\BAO_CAO_DANH_MUC_TOAN_BO_LOI_HE_THONG_PWD301.md`.
2. Cùng thư mục: `BAO_CAO_CHI_TIET_HUONG_XU_LY_VA_QUY_TRINH_KIEM_THU_TOAN_DIEN.md`.

Ảnh đầu vào `image-1.png` cho thấy trang kết quả giảng viên báo lỗi URL không tồn tại; thao tác thật trong phiên này đã tái hiện cùng hiện tượng.

### 2.2. Nguồn nghiệp vụ đối chiếu

- `AGENTS.md`, chỉ dẫn toàn cục người dùng cung cấp, `tasks/CURRENT.md` và `tasks/templates/TASK_TEMPLATE.md`.
- `README.md`; System Specification: `CODING_AGENT_START_HERE.md`, `business/01_BUSINESS_RULE_CATALOG.md`, `implementation/06_NON_NEGOTIABLE_INVARIANTS.md`.
- `authorization/02_PERMISSION_MATRIX.md`, `authorization/04_ADMIN_PERMISSION_RULES.md`.
- `business/08_ASSESSMENT_ENGINE.md`, `business/09_ASSESSMENT_ATTEMPT.md`, `api/08_ATTEMPT_API.md`, `workflows/06_ATTEMPT_LIFECYCLE.md`.
- Các tài liệu quản lý môn, tệp và việc ngừng standalone Question Bank trong `business/06_QUESTION_BANK.md`, `api/06_QUESTION_BANK_API.md`, TASK-078.

Các đường dẫn System Specification ở trên thuộc `docs/system/PWD301_SYSTEM_SPECIFICATION/`. Database Architecture vẫn là nguồn schema chuẩn; lượt này chỉ đọc trạng thái SQL Server và cột hiện có, không thiết kế/sửa schema.

### 2.3. Nhãn bằng chứng

| Nhãn | Ý nghĩa |
|---|---|
| LIVE | Tái hiện trên trình duyệt hoặc kiểm tra đọc trực tiếp SQL Server đang chạy |
| REPRO | Thử nghiệm cô lập bằng fixture giả trên SQLite hoặc VM Node; không phải dữ liệu thật |
| SOURCE | Đã đọc luồng mã và hợp đồng liên quan; chưa thực hiện thao tác đó trên hệ thống thật |
| FIXED-SOURCE | Dấu lỗi cũ đã được sửa trong source; chỉ được đóng phạm vi đã kiểm tra |
| RETIRED | Chức năng đã bị loại bỏ có chủ đích theo task/spec hiện hành |
| UNVERIFIED | Chưa đủ bằng chứng để kết luận lỗi hiện tại hoặc để xác nhận đã sửa |

Mức **P0**: nguy cơ sửa sai điểm, vượt quyền/kiểm duyệt hoặc bằng chứng học vụ sai; **P1**: chặn hoặc làm sai nghiệp vụ quan trọng; **P2**: tính đúng đắn, khả năng sử dụng/hiệu năng/quy trình cần sửa. Mức ưu tiên không thay thế mức độ bằng chứng.

Log, script tái hiện và baseline đặt tại [thư mục bằng chứng](PWD301_AUDIT_2026-10-03_EVIDENCE/). Script tái hiện chỉ dùng database `testing` trong bộ nhớ. Không chạy chúng với connection của database thật.

## 3. Đối chiếu toàn bộ 15 mục trong báo cáo cũ

| Mã cũ | Nội dung được báo cáo | Trạng thái hiện tại và bằng chứng | Kết luận xử lý |
|---|---|---|---|
| DB-001 | Thiếu `users.avatar_url`, đăng nhập/trang chủ 500 | LIVE: `flask db current` và `heads` đều `a1b2c3d4e5f8 (head)`; `sys.columns` xác nhận cột tồn tại, count=1. Model `identity.py:75`, migration 0010 có cột | Không tái diễn tại thời điểm kiểm tra. Cần giữ gate kiểm tra drift khi deploy; có head không chứng minh mọi schema đều đúng |
| SEC-001 | Admin bị 403 do `can_manage_course` chỉ cho owner | FIXED-SOURCE: `authorization_service.py:566-567` cho Admin qua. REPRO phát hiện thiếu lý do/thông báo trong sửa môn và xem chi tiết điểm | Không phục hồi quyền toàn Admin vô điều kiện như giải pháp cũ. Xử lý N09/N10 |
| SEC-002 | Chặn tự cấp Admin làm hỏng bootstrap/test | `user_service.py:832-856` cấm cấp primary thông thường và tự cấp ADMIN; các test liên quan đã chạy. Báo cáo giải pháp vừa mở ngoại lệ bootstrap vừa tuyên bố loại bỏ ngoại lệ | Test fixture/cơ chế bootstrap phải phân biệt. Không coi chặn tự nâng quyền là lỗi cần bỏ |
| SEC-003 | Giảng viên khác xóa mềm môn do thụt đầu dòng | FIXED-SOURCE: `course_service.py:858-865` có kiểm tra quản lý; bộ course IDOR đã chạy | Lỗ hổng được mô tả đã sửa ở source. N12 là lỗ hổng khác trong cùng state machine, chưa được test cũ bao phủ |
| ACAD-001 | Tạo chương mục trên môn published không qua duyệt | REPRO: UUID trả 201, tạo unit, không change request; numeric ID trả 202, tạo change request. `instructor/routes.py:852-879`, `lesson_service.py:94-98` | Chỉ sửa một nhánh, lỗi còn tồn tại. N11 |
| SEC-004 | Upload quá giới hạn để lại file tạm | FIXED-SOURCE: `file_service.py:638-646` có cleanup; test file/size/access được chạy | Dấu lỗi cũ đã xử lý. Cần giữ test lỗi stream, disconnect và disk failure; chưa chaos test thật |
| SEC-005 | Scanner ERROR kích hoạt file ACTIVE | FIXED-SOURCE: `file_service.py:581-604` giữ ERROR theo nhánh an toàn; bộ scanner/file access đã chạy | Không xác nhận bypass scanner hiện tại. Chưa thực hiện ClamAV outage thật |
| SEC-006 | Asset TRASH bị revision ACTIVE ghi đè khi serialize | FIXED-SOURCE: `file_service.py:1675-1676` ưu tiên trạng thái logical asset | Giữ kiểm thử danh sách, preview/download và revision cũ khi trash |
| API-001 | Admin giải phóng quarantine bị 401 trong test | `test_scan_api.py:288-290` đã truyền password reauth; suite chạy đạt | Không gỡ reauth để làm test xanh. 401 khi thiếu reauth là bảo vệ có chủ đích |
| API-002 | Health test đòi Redis/Qdrant không tồn tại | `test_admin_backend_completion.py:165-170` đã kiểm tra tập service hiện hành; test chọn lọc đạt | Test cũ đã cập nhật. Tên service có trong JSON chưa chứng minh từng dependency healthy |
| API-003 | Recommendations test đòi `id` nội bộ | `test_student_backend_completion.py:689-690` dùng public `course_id`; test chọn lọc đạt | Bảo toàn public UUID; không thêm BIGINT để chiều test |
| API-004 | Standalone AI question draft session route 404 | RETIRED: TASK-078 và docs Question Bank ngừng API standalone | Không khôi phục endpoint đã gỡ. AI/exam authoring hiện hành phải được test theo luồng còn được hỗ trợ |
| UI-001 | Admin/Instructor settings route thiếu | FIXED-SOURCE: `router.js:471,725,733,950`; phiên giảng viên hiện có link Cài đặt đúng | Link và route đã có; chưa thao tác lưu hồ sơ/đổi mật khẩu ở mọi vai trò |
| UI-002 | Toggle password thiếu button type/chặn submit | FIXED-SOURCE: `student.js:7009,7021,7053,7280-7283`; frontend settings tests đã chạy | Dấu lỗi cũ đã sửa; chưa chứng nhận mọi viewport/keyboard bằng browser |
| ARCH-001 | 22 prototype `/api/ui/screen` trả 404 | SOURCE: `frontend/routes.py:299-315` hiện có HTML fallback khi thiếu file; standalone question screens đã retired | Fallback không chứng minh màn hình thật tồn tại/chạy đúng. Kiểm thử prototype phải tách khỏi SPA sản phẩm |

Các vị trí service/blueprint trong bảng nằm dưới `src/pwd301/`; UI nằm dưới `frontend/assets/js/`; line là snapshot tại lượt này, có thể đổi sau sửa mã.

## 4. Danh mục phát hiện hiện tại

### N01 — P1 — Route kết quả giảng viên bị route sinh viên chặn

**Bằng chứng LIVE + REPRO.** `frontend/assets/js/router.js:464-466` dùng `path.endsWith('/results')`; các nhánh giảng viên ở `526-537` không được tới. `instructor.js:2675-2690` tạo đúng hash nhưng không cứu được dispatcher. `api.js:367-368` ghép attempt ID chứa `#` vào URL.

Luồng thật: mở quản lý môn → bấm **Bảng điểm & Bài nộp** → `/instructor/courses/.../assessments/.../results` → renderer sinh viên → `/student/attempt/` → 404. VM kiểm tra ba route giảng viên: **3 fail**, hai route sinh viên: **2 pass**. Endpoint dùng đúng cho danh sách giảng viên đã tồn tại: `/instructor/assessments/{assessment_id}/attempts` (`api.js:786-788`, `instructor/routes.py:3612-3622`). Đây không phải bằng chứng thiếu backend `/assessments/{id}/results` cần tạo mới.

### N02 — P1 — Bài nộp chờ chấm tự luận biến mất khỏi bảng điểm

**REPRO.** `attempt_service.py:3269-3271` chỉ lọc SUBMITTED/GRADED/IN_PROGRESS, bỏ PENDING_GRADING. Fixture có một bài PENDING_GRADING: danh sách bảng điểm total=0, API danh sách chờ chấm total=1. Người dạy tưởng không có bài nộp; học viên không được chấm đúng hạn.

### N03 — P1 — Bài chưa chấm/đang làm bị coi như 0 điểm, không đạt và kéo sai thống kê

**SOURCE.** `attempt_service.py:3290-3297` thay số liệu chưa có bằng 0/False; `instructor.js:2752-2756,2792-2807` dùng tất cả attempts làm mẫu số tỷ lệ đạt/trung bình và nhãn chỉ có ĐẠT/KHÔNG ĐẠT. IN_PROGRESS xuất hiện trong danh sách nhưng được tính như bài nộp. Cần phân biệt trạng thái làm bài, chấm bài, công bố điểm và điểm thật bằng 0. Quy tắc lấy lần tốt nhất/lần cuối và số học viên khác số attempts cần chốt theo policy đã cấu hình.

### N04 — P1 — Tổng quan chấm bài luôn báo không có bài cần chấm

**REPRO.** `/instructor/grading` ở `instructor/routes.py:3653-3657` trả cứng `{pending_attempts: [], total: 0}`. Với fixture có bài chờ chấm, endpoint vẫn trả 200 và rỗng. Đây là thiếu nghiệp vụ backend, không phải empty state thật.

### N05 — P1 — Nhập điểm `bogus` hoặc `NaN` gây lỗi server 500

**REPRO.** `attempt_service.py:2605-2615` chuyển Decimal/so sánh mà không bắt InvalidOperation hoặc kiểm tra finite. API chấm (`instructor/routes.py:3688-3699`) trả 500 cho hai giá trị trên; Infinity được 400 trong mẫu đã thử. Cần lỗi validation 400 có field error, không thay đổi grade/result/history.

### N06 — P0 — API “chấm tự luận” sửa được điểm câu trắc nghiệm

**REPRO.** `grade_essay_question` ở `attempt_service.py:2554-2643` không kiểm tra question type tại snapshot. Thử nghiệm câu SINGLE_CHOICE đang 10 điểm: gọi hàm chấm tự luận đổi thành 0, MANUAL_GRADED, kết quả finalized. Phải hạn chế đúng ESSAY; sửa đáp án trắc nghiệm cần luồng correction/regrade hợp lệ giữ lịch sử.

### N07 — P1 — Sửa điểm cũ không bắt buộc lý do nghiệp vụ thực

**REPRO.** `attempt_service.py:2660` tự điền “Manual essay grade by instructor”; mẫu N06 tạo history với lý do mặc định. Lịch sử có row nhưng không nói tại sao điểm thay đổi, trái GRADE-002. Phân biệt chấm lần đầu với sửa điểm đã chấm; sửa điểm cần old/new, actor, reason thật và transaction nguyên tử.

### N08 — P0 — Thiếu kiểm soát phiên bản khi chấm/sửa điểm đồng thời

**SOURCE; chưa race test SQL Server.** `api/08_ATTEMPT_API.md:75-79` yêu cầu `row_version` và conditional version. Route `instructor/routes.py:3688-3699` bỏ qua row_version; `attempt_service.py:2554-2560,2618-2643` không có tham số version/conditional update/lock cho thao tác này. Model có row_version (`attempt_regrade.py:639`) nhưng chưa gắn cơ chế version checking vào thao tác. Hai người chấm từ cùng bản cũ có thể ghi đè quyết định nhau; hiện tượng lost update thật trên SQL Server chưa được tái hiện. Test chấp nhận phải chứng minh chỉ một writer thành công, writer còn lại 409.

### N09 — P0 — Admin xem chi tiết bài và thông tin học viên không cần lý do

**REPRO.** `get_instructor_attempt_evaluation` (`attempt_service.py:3348`) và grading detail (`3011`) chỉ dựa vào course manager; `authorization_service.py:566-567` cho mọi Admin qua. Fixture gọi instructor detail bằng Admin không lý do trả 200 và có student email. `authorization/04_ADMIN_PERMISSION_RULES.md:3` yêu cầu lý do khi xem kết quả cá nhân. Không biến quyền xem aggregate thành quyền đọc mọi bài cá nhân vô điều kiện.

### N10 — P0 — Admin sửa nội dung môn người khác thiếu lý do và thông báo

**REPRO.** Admin sửa description môn PUBLISHED thuộc giảng viên khác được chấp nhận; audit reason=null, performed_as_admin=true, notification cho owner tăng 0. `authorization_service.py:566-567`, `course_service.py:560` là các điểm liên quan. Chỉ có audit flag chưa đủ AUDIT-003. Không phục hồi `if is_admin: return True` rồi coi mọi caller đã được bảo vệ.

### N11 — P0 — UUID đi vòng qua kiểm duyệt khi tạo chương mục

**REPRO.** `instructor/routes.py:852-853` giới hạn nhánh staging theo numeric course ID. Với cùng môn PUBLISHED: UUID POST learning-units → 201, unit_count=1, request_count=0; numeric → 202, không thêm unit mới, request_count=1. `lesson_service.py:94-98` commit unit trực tiếp. Cần quyết định bằng resource/status sau resolve ID; UUID và numeric, nếu vẫn được hỗ trợ, phải cho hành vi nghiệp vụ như nhau.

### N12 — P0 — State transition đẳng công trả dữ liệu môn riêng trước khi kiểm tra quyền

**REPRO.** `course_service.py:830-832` return khi current_status=target_status trước authorization. Giảng viên B gửi JWT POST `/api/courses/{uuid-của-A}/submit` khi môn A đã SUBMITTED_FOR_REVIEW: 200, trả metadata private; `api_courses/routes.py:206-222` serialize kết quả. No-op vẫn phải kiểm tra quyền. Đẳng công không cho phép vượt object authorization.

### N13 — P1 — Điểm chưa công bố bị frontend trình bày thành 0/10, không đạt

**SOURCE + payload REPRO.** Hidden result `attempt_service.py:2777-2791` trả SCORE_HIDDEN và score/questions null. `student.js:5072-5075` bỏ score_status, mặc định tổng=0/max=10/isPassed=false. Renderer tiếp tục tạo giao diện điểm chính thức. Payload RELEASED đã có đúng total_score/max_points/is_passed: **không có bằng chứng mismatch điểm của payload RELEASED**, không sửa serializer đúng để chiều kết luận sai.

### N14 — P0 — Banner công bố phúc khảo đã hoàn tất khi chưa có quyết định

**SOURCE.** `student.js:5138-5147` hiển thị hội đồng/bộ môn đã xét duyệt đơn phúc khảo cho mọi formal exam (`MIDTERM`, `FINAL_EXAM` hoặc maxPoints>=10), không phụ thuộc appeal. Sinh viên có thể hiểu nhầm điểm đã qua phúc khảo chính thức. Chỉ render khi có record quyết định tương ứng, thời gian và actor thật.

### N15 — P0 — Lịch sử điểm/rubric/xác nhận liêm chính bị tạo giả trên UI

**SOURCE.** Audit drawer `student.js:5512-5663` chỉ fetch appeal, không lấy grade-history; dòng `5585` tạo điểm ban đầu bằng `Math.max(0,totalScore-1.5)`. Các dòng `5590-5605` tự gán xét duyệt/duyệt cuối; `5620,5628,5636` chia rubric ABET theo tỷ lệ điểm; `5644-5650` gán xác nhận không vi phạm. Nhãn “bất biến” không biến dữ liệu dựng từ phép tính thành audit record. Cần dùng history thật, bỏ tuyên bố/rubric không có nguồn và hiện “Chưa có dữ liệu” khi thích hợp.

### N16 — P0 — Backend tự gán top percentile và proctoring verified

**SOURCE.** `attempt_service.py:2897,2902` suy ra “top 15%/35%” chỉ từ ngưỡng điểm cá nhân; không query phân phối điểm. `2933` trả `proctoring_verified=True` vô điều kiện. Điểm cao không chứng minh thứ hạng quần thể hoặc đã kiểm chứng giám sát. Phải bỏ field/tuyên bố chưa có nguồn hoặc tính bằng dữ liệu và quy trình hợp lệ. GPA/letter-grade quy đổi cần có quy chế chứ không suy thành chuẩn đại học mặc định.

### N17 — P2 — Môn có câu hỏi vẫn hiện “0 câu hỏi”

**LIVE + SOURCE.** Card môn trong browser hiển thị 0 câu. `instructor.js:1070` đọc `questions.length` hoặc singular `question_count`; list serializer `assessment_service.py:364,986` trả plural `questions_count`. Hub exam ở `instructor.js:2601` dùng đúng trường. Đây là mismatch hợp đồng UI, không phải bằng chứng đề thật không có câu hỏi.

### N18 — P1 — Timestamp UTC thiếu offset bị đọc thành giờ địa phương

**SOURCE + REPRO chuyển đổi thời gian.** `attempt_service.py:3309-3310` dùng isoformat của DATETIME2, có thể trả chuỗi naive; `instructor.js:2793` dùng `new Date(...)`. Với payload UTC `2026-10-03T03:57:15.761206`, Node đặt TZ Asia/Bangkok hiển thị 03:57, thêm Z thì 10:57. Bằng chứng payload fixture DB đã có chuỗi naive. SQL Server DATETIME2 không lưu timezone; phải chuẩn hóa UTC có `Z/+00:00` tại API, không cộng 7 giờ cứng trong mỗi view. Chưa kiểm tra mọi serializer/deadline thật.

### N19 — P2 — Danh sách bài làm chưa phân trang, có nguy cơ tải lớn/N+1

**SOURCE.** `attempt_service.py:3265-3275` dùng `.all()` cho toàn assessment; `3290-3325` truy cập result/student mỗi attempt. Không có pagination/count/filter server trong contract danh sách này, trái OPS-001 khi dữ liệu lớn. Tác động latency/RAM chưa benchmark. Dùng pagination và reuse query loader hiện có; không cần queue/cache/hạ tầng mới cho danh sách nhỏ.

### N20 — P2 — Modal chi tiết bài làm thiếu khả năng dùng bàn phím chuẩn

**SOURCE.** `instructor.js:2850-2890` tự tạo overlay, đóng bằng onclick remove; không thấy role=dialog, aria-modal, focus trap/restore hoặc handler Esc của modal này. Không dùng lifecycle modal chung. Đây là nhận xét source; chưa thao tác modal trên browser vì route bảng điểm đang hỏng. Cần kiểm tra lại keyboard sau sửa N01.

### N21 — P2 — Trang lỗi không cung cấp đường phục hồi cho người dạy

**LIVE + SOURCE.** Lỗi hiện thành một dòng tiếng Anh dài; không nút Thử lại/Quay lại, không phân biệt 404, 403, phiên hết hạn hoặc 500. `student.js` renderer sai đường là nguồn màn hình hiện tại; trang giảng viên `instructor.js:2841-2844` cũng chỉ render text khi load thất bại. Cần error state tiếng Việt có hành động, giữ breadcrumb/back và thông tin hỗ trợ không lộ stack/token.

### N22 — P2 — Lỗi tải phúc khảo bị coi như không có đơn

**SOURCE.** `instructor.js:2895-2899` catch request appeal thành `{appeal:null}`; `student.js:5515-5520` nuốt mọi lỗi khi mở drawer. Timeout/403/500 không tương đương “chưa nộp phúc khảo”. Cần empty state chỉ cho phản hồi không có record, còn lỗi phải hiện retry riêng; không làm mất phần bài thi đã tải thành công.

### N23 — P1 — Aggregate verifier bỏ qua frontend và migration/runtime gates

**SOURCE.** `scripts/verify.ps1` chạy repo check, compile, ruff, mypy, pytest; không chạy Node frontend tests, migration drift hoặc browser workflow. Verifier hiện dừng khi gate đã chạy fail, nhưng banner PASS chỉ phủ các gate nó chạy. Lượt này 81 Node tests xanh vẫn bỏ lọt N01; cần thêm test dispatcher/API/DOM thật và môi trường có schema đúng, không chỉ thêm count test.

### N24 — P1 — Báo cáo giải pháp cũ chứa chỉ dẫn mâu thuẫn và chứng nhận quá phạm vi

**DOCUMENT.** Đầu báo cáo mở ngoại lệ tự cấp Admin bootstrap; phần 4.2 lại nói đã bỏ ngoại lệ. Đề xuất assert `course_id in r or id in r` cho phép cả internal ID, trái mục tiêu ADR-002. Đề xuất khôi phục AI Question Bank endpoint đã retired. Sơ đồ ghi 17 frontend test nhưng bảng ghi 81. File cleanup khuyên try/finally nhưng ví dụ chỉ bắt size exception, chưa đủ mọi ngắt stream. Chuyển scanner adapter đơn lẻ chưa chứng minh mọi engine/pipeline fail-closed. Tuyên bố “không còn sửa chỗ này hư chỗ kia”, “100% mọi kết luận” không được các test counts chứng minh: lượt này có repro fail dù nhiều suite xanh. Không suy rằng số test cũ là giả; kết luận đúng là **phạm vi chứng minh không đủ và hiện không phản ánh toàn hệ thống**.

## 5. Rủi ro cần xác minh, chưa nâng thành lỗi chắc chắn

| Mã | Rủi ro | Bằng chứng hiện có | Phần cần làm để kết luận |
|---|---|---|---|
| R01 | AFTER_CLOSE/NEVER vẫn có thể suy ra đáp án qua chấm từng câu | `attempt_service.py:2846,2865-2869` có awarded_points/is_correct/is_selected ngay khi không show_answers; correct choice flags/explanation đã bị ẩn | Đối chiếu nghĩa chính xác của answer_visibility policy; test học viên nhiều lần, không lẫn quyền owner/instructor. Không tuyên bố hiện đã lộ trực tiếp answer key |
| R02 | Rulebook giữa sub-admin tasks và permission matrix chưa đủ rõ | TASK-072 phân tách sub-role; core can_manage cho mọi admin | Chốt action matrix cho PRIMARY/COURSE_REVIEW/INSTRUCTOR_REVIEW/TEACHING_ASSIGNMENT/SYSTEM_MONITORING theo source of truth, rồi test từng role. Không coi canonical Admin override có lý do là quyền cấm hoàn toàn |
| R03 | Prototype fallback che lấp tài nguyên bị thiếu | HTML tổng hợp trả thành công khi template prototype không tồn tại | So sánh screen catalog với sản phẩm được hỗ trợ, bỏ test đòi prototype retired; không dùng HTTP200 fallback làm bằng chứng màn hình nghiệp vụ |
| R04 | File outage/race và SQL Server concurrency chưa được chứng minh | Test SQLite/scanner mock chạy được; Docker ClamAV healthy tại lúc đọc | Test sandbox thật: timeout, failover, concurrent activation, references, đồng thời grading/autosave/submit, triggers và ROWVERSION |

## 6. Kiểm chứng đã chạy và giới hạn

| Kiểm tra | Kết quả lượt này | Giới hạn |
|---|---|---|
| Browser Edge, khóa học đang mở → Bảng điểm & Bài nộp → reload | Tái hiện lỗi; CDP Network xác nhận `/student/attempt/` 404 | Chỉ dùng phiên giảng viên hiện có; không sửa data thật |
| VM router reproduction | 2 pass, 3 fail, exit1 | Stub renderer nhưng chạy dispatcher source nguyên bản; không chứng minh toàn DOM |
| Node toàn bộ `tests/frontend/*.test.js` | 81 pass, 0 fail, 0 skipped | Không bao phủ dispatch kết quả giảng viên; không thay E2E browser |
| Backend bộ course/auth/operations/file chọn lọc | 103 pass + 11 pass + 23 pass | Fixture SQLite; log và lệnh nằm trong evidence |
| Grading unit/API/IDOR/regrade-history chọn lọc | 58 pass | SQLite; không chứng minh concurrency SQL Server |
| Probe nghiệp vụ mới | Xác nhận N02/N04/N05/N06/N07/N09/N10/N11/N12/N13 | Script tái hiện, không phải regression tests đã sửa và xanh |
| `python scripts/repo_check.py` | PASS | Contract/files/Markdown; không kiểm tra semantic workflow |
| `ruff check src tests scripts` | PASS | Không phát hiện lỗi nghiệp vụ |
| `ruff format --check src tests scripts` | 265 files already formatted | Không phát hiện lỗi runtime |
| `mypy src` | No issues in 88 source files | Có note unused module config; static types không chứng minh runtime |
| Docker container state | web/db/clamav healthy tại lúc đọc | Không chứng minh sáu dependency service đều hoạt động |
| `flask db current`, `flask db heads`; đọc `sys.columns` | head khớp; avatar_url count1 | Không chạy upgrade/downgrade và không kiểm tra toàn schema drift |
| OCR CLI | FAIL: no valid LLM endpoint configured | Không có kết quả review Alibaba từ LLM; đã review thủ công đa file và đối chiếu bằng hai nhánh kiểm tra độc lập |
| `.venv/Scripts/python.exe -m pytest -p no:cacheprovider -q` toàn repository | **1540 passed in 1027.04s (17:07), exit0**; không failed/skipped trong summary | `TEST_DATABASE_URL=sqlite:///:memory:`; không dùng database live, không chứng minh SQL Server concurrency |

Mở endpoint JSON trực tiếp bằng tab phụ gặp `net::ERR_BLOCKED_BY_CLIENT`. Không suy lỗi này là backend 404/403. Bằng chứng live lấy từ click SPA và Network; API permission/grading dùng test client cô lập. Chưa chạy trình duyệt ở role sinh viên, từng sub-admin, mobile/touch, phúc khảo thật, upload/scan outage thật, email/worker thật, hoặc sửa/chấm/duyệt dữ liệu thật. Không cấp quyền, đổi mật khẩu, restore DB hay ship/release trong lượt này.

Full suite hiện đạt đúng 1540 như con số báo cáo đầu vào; đây là kết quả mới, độc lập với lượt cũ. Nó chứng minh các test hiện có chạy đạt trên SQLite hiện tại, **không bác bỏ các lỗi mới đã tái hiện**. Cần bổ sung regression tests cho các phản ví dụ trước khi xem suite xanh là gate đáng tin cho các nghiệp vụ này. Frontend 81 pass cũng không bao phủ ba route giảng viên đang fail. Không có sản phẩm nào được sửa trong lượt kiểm tra này.

## 7. Báo cáo hoàn thành theo hợp đồng A–G

### Phạm vi đánh giá UI theo Impeccable

| Chiều đánh giá | Kết quả có bằng chứng | Phần chưa đủ để chấm điểm |
|---|---|---|
| Accessibility | Source modal chi tiết thiếu lifecycle keyboard chuẩn (N20) | Chưa chạy Tab/Esc/focus/contrast trên màn hình bảng điểm do N01 |
| Performance | Query danh sách không giới hạn và access quan hệ từng row (N19) | Chưa đo latency/RAM/query count lớp lớn |
| Responsive | Error screen desktop đã quan sát | Chưa kiểm tra mobile/touch/zoom và bảng/modal thực |
| Theming | SPA có tokens warm/light/dark; views vẫn có nhiều class màu trực tiếp | Chưa đo contrast/computed colors các trạng thái gradebook; không chứng nhận AA |
| Implementation integrity | Fail ở luồng vào bảng điểm và dữ liệu học vụ không có nguồn (N01/N14–16) | Các màn hình/roles khác chưa kiểm tra toàn bộ |

Không gán tổng điểm UI/20 hoặc chứng nhận WCAG khi thiếu phép đo. Ưu tiên integrity, clarify/harden và keyboard trước polish; không redesign hệ thống trong tác vụ báo cáo.

**A. Phạm vi và nguồn:** hai báo cáo đầu vào, ảnh, source/spec/task và luồng giảng viên thật; đối chiếu toàn bộ 15 ID và ghi mọi phát hiện mới nêu trên.

**B. Tái sử dụng:** dùng API attempts/detail/pending/history hiện có, fixture pytest và VM Node, modal chung trong hướng giải pháp. Không đề xuất khôi phục Question Bank hoặc thêm framework/infrastructure.

**C. Thay đổi từng file:** tạo báo cáo danh mục này; tạo báo cáo giải pháp đi kèm; tạo thư mục evidence gồm baseline, log, script tái hiện và ghi chú browser. Không chỉnh các file sản phẩm/test có sẵn.

**D. Danh sách đơn giản hóa đề nghị:** REMOVE NOW các timeline/phúc khảo/proctoring/percentile không có nguồn khi triển khai bản sửa; SIMPLIFY NOW route bằng namespace và input contract rõ; KEEP auth/reauth/CSRF/history/scanner/audit; PONYTAIL performance tối ưu chỉ sau benchmark, nhưng pagination chuẩn vẫn cần theo OPS-001.

**E. Phần hoãn:** kiểm tra concurrency SQL Server, policy R01/R02, dependency outage và mọi role/browser chưa chạy; owner QA + backend/domain owner, rủi ro được mô tả từng mục, safeguard là không công bố release-ready; review trước bản phát hành sửa lỗi.

**F. Xác minh thực chạy:** bảng mục 6 và logs evidence; không cộng skipped vào passed hoặc cộng số lượt test trùng nhau thành số ca duy nhất.

**G. Rủi ro/tiếp theo:** chưa sửa lỗi sản phẩm. Triển khai theo báo cáo giải pháp, viết regression fail trước và nghiệm thu end-to-end từng bước. Không có phương pháp hữu hạn nào bảo đảm tuyệt đối không phát sinh bug; có thể giảm và kiểm soát rủi ro bằng invariant, test đúng và evidence.

Đã dùng 7 skill gồm: superpowers (using-superpowers, systematic-debugging, writing-plans, dispatching-parallel-agents, verification-before-completion), ponytail, task-observer, full-output-enforcement, open-code-review (CLI thiếu endpoint; review thủ công), impeccable, computer-use.
