# Kế Hoạch Hiện Thực Hóa: Thanh Trừng Workflow Cũ, Trình Soạn Thảo MS Word, Question Stepper Dán Ảnh, Môn Tiên Quyết Độc Lập & Deep Changeset Diff (TASK-084)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Xóa sạch toàn bộ logic, mô tả và thiết kế cũ lỗi thời của hệ thống soạn thảo và duyệt khóa học; xây dựng bộ công cụ soạn thảo MS Word Ribbon 2 hàng nút; khối câu hỏi tương tác phân trang (Question Stepper) có nút Lưu độc lập, hỗ trợ dán ảnh cho câu hỏi & đáp án, sửa triệt để lỗi điền khuyết và nối từ; làm lại cây đề cương học sinh (nút Play đang học và Lock khóa); thiết lập giao diện duyệt môn tiên quyết riêng biệt cho giảng viên kèm ràng buộc chỉ chọn môn đã xuất bản; và nâng cấp hệ thống đối chiếu thay đổi (Deep Changeset Diff) 5 phân nhóm chuẩn xác cho cả Giảng viên và Quản trị viên.

**Architecture:** Pure Headless REST API (JSON chuẩn `{"success": true/false, "data": ..., "error": ...}`) kết hợp Single-DOM SPA (Vanilla JS + Tailwind CSS + DOMPurify). Snapshot Manifest State Machine lưu trữ toàn bộ cây thay đổi của khóa học, Deep Tree Diff so sánh đa thực thể. Không tạo Jinja templates hay tệp preview giả lập.

**Tech Stack:** Python 3.12, Flask, SQLAlchemy, Microsoft SQL Server, Vanilla JS (ES6+), Tailwind CSS, DOMPurify, Pytest, Chrome DevTools.

**Spec:** Yêu cầu người dùng ngày 07/10/2026 và kết quả phỏng vấn làm rõ chi tiết qua skill `/grill-me`.

---

## Global Constraints

- **Pure Headless Backend**: Không sinh template Jinja `*.html` hay thư mục preview tĩnh giả lập. Mọi phản hồi API đều chuẩn hóa qua phong bì JSON.
- **Fail-Closed Security & Integrity**: Chỉ môn học `PUBLISHED` mới được phép làm môn tiên quyết. Môn của giảng viên khác bắt buộc qua luồng xét duyệt `PENDING_OWNER_APPROVAL`.
- **Zero Obsolete Workflows & Clean Memory**: Xóa bỏ triệt để và cấm tái hiện: chữ "Khối 1, 2...", UI hướng dẫn Markdown cũ, regex cắt xén quiz cũ, diff chỉ đếm độ dài ký tự, và bảng review Admin hiển thị "Không đặt" giả lập.
- **Impeccable UI Standards**: Ribbon chuẩn MS Word 2 hàng nút, tỷ lệ padding nút 2:1, bo góc lồng nhau chính xác, màu sắc tương phản WCAG AA >= 4.5:1, không dùng Pure Black/White.

## Review Focus

1. **Thanh trừng bộ nhớ & logic cũ:** Loại bỏ mọi tàn dư của logic đếm ký tự diff cũ, regex quiz cũ, và quy trình gán môn tiên quyết không kiểm soát trạng thái xuất bản.
2. **Khối câu hỏi tương tác (Điền khuyết & Nối từ):** Khi chuyển qua lại giữa các loại câu hỏi và nhập dữ liệu, câu hỏi không bao giờ bị nhảy về trắc nghiệm; đáp án điền khuyết và cặp nối từ được lưu và phục hồi chính xác 100%.
3. **Dán ảnh vào câu hỏi và đáp án:** Giảng viên có thể nhấn `Ctrl+V` để dán ảnh trực tiếp từ clipboard vào câu hỏi hoặc đáp án lựa chọn; ảnh được tải lên máy chủ và hiển thị thumbnail trực quan.
4. **Phê duyệt môn tiên quyết giữa các giảng viên:** Giảng viên A chọn môn của Giảng viên B thì môn đó rơi vào trạng thái chờ duyệt; Giảng viên B nhận thông báo và truy cập Menu "Duyệt môn tiên quyết" để bấm Chấp thuận hoặc Từ chối kèm lý do.
5. **Đối chiếu thay đổi (Deep Changeset Diff):** Cả Giảng viên và Admin đều xem được cây thay đổi chi tiết phân loại 5 nhóm: Cấu trúc & Thứ tự, Nội dung & Media, Câu hỏi tương tác, Bài kiểm tra, Tiêu chí hoàn thành & Ảnh bìa.

---

### Task 0: Thanh Trừng Toàn Diện Logic, Bộ Nhớ Cũ & Thiết Lập Bất Biến Vĩnh Viễn

**Files:**
- Modify: `tasks/CURRENT.md`
- Modify: `docs/system/PWD301_SYSTEM_SPECIFICATION/business/01_BUSINESS_RULE_CATALOG.md`
- Modify: `docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md`

**Interfaces:**
- Consumes: Yêu cầu của người dùng về việc xóa sạch mô tả và workflow cũ để tránh việc tái phát sinh lỗi trong tương lai.
- Produces: Bản bất biến quy trình mới khóa chặt vĩnh viễn các tiêu chuẩn: MS Word Ribbon, Question Stepper dán ảnh, Môn tiên quyết PUBLISHED có giao diện duyệt riêng, Deep Changeset Diff 5 nhóm.

- [ ] **Step 1: Viết tài liệu tuyên bố xóa bỏ (Decommissioning & Purge Declaration) trong `tasks/CURRENT.md`**
  Ghi nhận rõ ràng việc bãi bỏ vĩnh viễn:
  1. Cũ: Chữ "Khối 1, 2, 3...", "Khối 1: Nội dung văn bản (Markdown)" và UI hướng dẫn Markdown. Mới: Bỏ chữ "Khối", sửa thành "Nội dung bài học" với Ribbon MS Word 2 hàng.
  2. Cũ: Form câu hỏi trắc nghiệm cuộn dọc thô sơ, không dán được ảnh, lỗi điền khuyết/nối từ. Mới: Question Stepper phân trang, nút "Lưu câu hỏi" riêng, hỗ trợ dán ảnh đề bài & đáp án.
  3. Cũ: Gán môn tiên quyết tự do kể cả DRAFT, thiếu màn hình duyệt cho giảng viên. Mới: Chỉ chọn môn PUBLISHED, ưu tiên môn của mình lên đầu, menu riêng "Duyệt môn tiên quyết".
  4. Cũ: Diff chỉ đếm độ dài text và số câu hỏi, Admin review hiện "Không đặt" giả lập. Mới: Deep Manifest Snapshot so sánh 5 phân nhóm chi tiết lấy từ CSDL thực.
  5. Cũ: Cây bài học học sinh đánh số sai thứ tự, thiếu nút Play/Lock rõ ràng. Mới: Đánh số chuẩn xác, hiển thị rõ nút Play (đang học) và icon Lock (khóa).
- [ ] **Step 2: Cập nhật `01_BUSINESS_RULE_CATALOG.md` và `06_NON_NEGOTIABLE_INVARIANTS.md`**
  Bổ sung các quy tắc bất biến mới vào tài liệu đặc tả chuẩn của hệ thống.
- [ ] **Step 3: Commit**
  ```bash
  git add tasks/CURRENT.md docs/system/PWD301_SYSTEM_SPECIFICATION/
  git commit -m "docs(invariants): permanently purge obsolete authoring and diff workflows and record TASK-084 canonical invariants"
  ```

---

### Task 1: Backend Snapshot Changeset & Deep Tree Diff Engine (5 Phân Nhóm)

**Files:**
- Modify: `src/pwd301/models/course.py`
- Modify: `src/pwd301/services/lesson_service.py:3430-3620`
- Modify: `src/pwd301/blueprints/admin/routes.py:2180-2210`
- Modify: `src/pwd301/blueprints/instructor/routes.py`
- Test: `tests/api/test_course_changeset_deep_diff.py`

**Interfaces:**
- Consumes: `Course`, `LearningUnit`, `Lesson`, `Assessment`, `CourseCompletionRule`, `CoursePrerequisite`
- Produces: `get_course_changeset_diff(actor, course_id_or_req_id)` trả về JSON có cấu trúc 5 nhóm:
  `{ "curriculum_structure": [...], "content_blocks": [...], "interactive_quizzes": [...], "assessments": [...], "governance_rules": {...} }`
  kèm cờ loại thay đổi: `ADDED`, `REMOVED`, `MOVED`, `MODIFIED`.

- [ ] **Step 1: Viết failing test cho Deep Changeset Diff**
  Tạo `tests/api/test_course_changeset_deep_diff.py` kiểm tra:
  - Khi di chuyển bài học từ Chương 1 sang Chương 2: diff trả về mục `curriculum_structure` với hành động `MOVED` (kèm tên chương cũ và mới).
  - Khi đổi thứ tự bài học trong chương: diff trả về `curriculum_structure` với hành động `REORDERED` (vị trí cũ vs mới).
  - Khi thêm/xóa/sửa câu hỏi tương tác: diff trả về mục `interactive_quizzes` với danh sách câu hỏi cụ thể.
  - Khi sửa tiêu chí hoàn thành khóa học hoặc ảnh bìa: diff trả về mục `governance_rules` so sánh Before vs After thực tế.
- [ ] **Step 2: Chạy test để xác nhận test FAIL**
  `pytest tests/api/test_course_changeset_deep_diff.py -v`
- [ ] **Step 3: Hiện thực hóa Deep Manifest Snapshot và thuật toán Diff 5 nhóm trong `src/pwd301/services/lesson_service.py`**
  - Xóa bỏ hoàn toàn hàm tính diff đếm độ dài chuỗi cũ.
  - Thuật toán so sánh:
    1. So sánh `learning_units` (Thêm mới, Đổi tên, Xóa).
    2. So sánh `lessons` theo từng unit (Nhận diện chuyển chương nếu `unit_id` khác nhau, đổi thứ tự nếu `position` khác nhau, thêm mới nếu chưa có bản gốc, sửa nội dung nếu markdown/title khác).
    3. Trích xuất và so sánh `mini_quiz`: so khớp từng câu hỏi theo nội dung/ID để phân loại câu hỏi thêm mới, bị xóa hoặc sửa đáp án.
    4. So sánh `assessments`: bài kiểm tra chương và Final Test được tạo mới, cập nhật thời gian/điểm, hoặc gỡ bỏ.
    5. So sánh `completion_rules`: điểm GPA tối thiểu, % bài học, bài bắt buộc, cấp chứng chỉ.
    6. So sánh `cover_image_url` và metadata khóa học.
- [ ] **Step 4: Cập nhật route Admin & Instructor trả về chuẩn dữ liệu mới**
  Đảm bảo cả `/instructor/courses/<id>/changeset/diff` và `/admin/courses/<id>/changeset/diff` trả về đúng cấu trúc 5 nhóm.
- [ ] **Step 5: Chạy test xác nhận test PASS**
  `pytest tests/api/test_course_changeset_deep_diff.py -v`
- [ ] **Step 6: Commit**
  ```bash
  git add src/pwd301/ tests/api/test_course_changeset_deep_diff.py
  git commit -m "feat(diff): implement deep 5-category changeset diff engine for curriculum restructuring"
  ```

---

### Task 2: Backend & API Duyệt Môn Học Tiên Quyết Độc Lập Cho Giảng Viên

**Files:**
- Modify: `src/pwd301/models/course.py`
- Modify: `src/pwd301/services/enrollment_service.py:688-770`
- Modify: `src/pwd301/blueprints/instructor/routes.py`
- Test: `tests/api/test_prerequisite_approval_workflow.py`

**Interfaces:**
- Consumes: `CoursePrerequisite`, `User`, `Course`
- Produces: 
  - Ràng buộc: Chỉ môn `PUBLISHED` mới được gán tiên quyết.
  - Môn của chính mình: `approval_status = 'APPROVED'` (dùng luôn).
  - Môn giảng viên khác: `approval_status = 'PENDING_OWNER_APPROVAL'`.
  - Endpoints:
    * `GET /instructor/prerequisites/incoming-requests`: Lấy danh sách yêu cầu chờ duyệt.
    * `POST /instructor/prerequisites/incoming-requests/<id>/review`: Phê duyệt hoặc từ chối kèm ghi chú.
    * `GET /instructor/prerequisites/incoming-requests/count`: Đếm số yêu cầu chờ duyệt để hiển thị badge đỏ.

- [ ] **Step 1: Viết failing test cho luồng kiểm soát và phê duyệt môn tiên quyết**
  Tạo `tests/api/test_prerequisite_approval_workflow.py` kiểm tra:
  - Chọn môn DRAFT hoặc UNPUBLISHED làm môn tiên quyết -> Bị từ chối với lỗi 400.
  - Chọn môn của chính mình -> Tự động APPROVED.
  - Chọn môn của giảng viên khác -> Trạng thái PENDING_OWNER_APPROVAL, giảng viên chủ môn nhận được trong danh sách incoming-requests.
  - Giảng viên chủ môn gọi API review -> Cập nhật APPROVED hoặc REJECTED.
- [ ] **Step 2: Chạy test để xác nhận test FAIL**
  `pytest tests/api/test_prerequisite_approval_workflow.py -v`
- [ ] **Step 3: Cập nhật `src/pwd301/models/course.py` và `src/pwd301/services/enrollment_service.py`**
  - Bổ sung các cột vào `CoursePrerequisite`:
    * `approval_status`: VARCHAR(30) default `'APPROVED'`
    * `requested_by_user_id`: BIGINT NULL
    * `requested_at`: DATETIME2 NULL
    * `reviewed_at`: DATETIME2 NULL
    * `review_note`: NVARCHAR(500) NULL
  - Trong `add_course_prerequisite`:
    * Kiểm tra: `if prereq_course.status != "PUBLISHED": raise CourseValidationError("Chỉ có thể chọn môn học đã xuất bản (PUBLISHED) làm môn tiên quyết.")`.
    * Nếu `prereq_course.creator_user_id != course.creator_user_id`: đặt `approval_status = 'PENDING_OWNER_APPROVAL'`.
  - Hiện thực hàm `get_incoming_prerequisite_requests(instructor_user)` và `review_prerequisite_request(instructor_user, req_id, action, note)`.
- [ ] **Step 4: Khai báo các API routes trong `src/pwd301/blueprints/instructor/routes.py`**
  - `GET /instructor/prerequisites/incoming-requests`
  - `GET /instructor/prerequisites/incoming-requests/count`
  - `POST /instructor/prerequisites/incoming-requests/<int:link_id>/review`
- [ ] **Step 5: Chạy test xác nhận test PASS**
  `pytest tests/api/test_prerequisite_approval_workflow.py -v`
- [ ] **Step 6: Commit**
  ```bash
  git add src/pwd301/ tests/api/test_prerequisite_approval_workflow.py
  git commit -m "feat(prerequisites): enforce PUBLISHED requirement and build peer-instructor prerequisite approval workflow"
  ```

---

### Task 3: Giao Diện Duyệt Môn Tiên Quyết Riêng Biệt Cho Giảng Viên & Nâng Cấp Modal Chọn Môn

**Files:**
- Modify: `frontend/assets/js/router.js`
- Modify: `frontend/assets/js/api.js`
- Modify: `frontend/assets/js/views/instructor.js:4730-4860`
- Test: Syntax check `node --check`

**Interfaces:**
- Consumes: `ApiClient.getIncomingPrerequisiteRequests()`, `ApiClient.reviewPrerequisiteRequest()`, `ApiClient.getPrerequisiteRequestsCount()`
- Produces: 
  - Route mới: `#/instructor/prerequisites/requests` hiển thị trang chuyên dụng "Duyệt Yêu Cầu Môn Tiên Quyết".
  - Thanh điều hướng Giảng viên: Thêm nút "Duyệt môn tiên quyết" kèm badge đỏ đếm số lượng.
  - Modal chọn môn tiên quyết: Chỉ nạp môn `PUBLISHED`, ưu tiên "Khóa học của bạn" lên trên cùng kèm badge `[Môn của bạn]`.

- [ ] **Step 1: Bổ sung API client methods trong `frontend/assets/js/api.js`**
  - `getIncomingPrerequisiteRequests()`
  - `getPrerequisiteRequestsCount()`
  - `reviewPrerequisiteRequest(linkId, payload)`
- [ ] **Step 2: Thêm Route và Menu Item trong `frontend/assets/js/router.js` và Topbar Navigation**
  - Thêm menu item "Duyệt môn tiên quyết" trên thanh điều hướng Giảng viên kèm container badge `#badge-prereq-pending-count`.
  - Đăng ký route `#/instructor/prerequisites/requests` dẫn tới `InstructorView.renderPrerequisiteApprovalRequests(container)`.
- [ ] **Step 3: Xây dựng màn hình `renderPrerequisiteApprovalRequests` trong `frontend/assets/js/views/instructor.js`**
  - Bảng danh sách các yêu cầu: Tên khóa học yêu cầu, Giảng viên yêu cầu, Khóa học của bạn được chọn, Điểm GPA tối thiểu, Lý do, Ngày gửi, Trạng thái.
  - Cặp nút thao tác: Nút **[Chấp thuận]** (xanh lá) và **[Từ chối]** (đỏ) mở modal nhập lý do từ chối.
  - Bộ lọc trạng thái: [Tất cả] [Chờ duyệt] [Đã chấp thuận] [Đã từ chối].
- [ ] **Step 4: Nâng cấp Modal Chọn Môn Tiên Quyết trong Cài đặt học vụ**
  - Chỉ lọc những môn học có `status === 'PUBLISHED'`.
  - Gom nhóm: Đưa danh sách môn do chính giảng viên phụ trách lên đầu danh sách kèm nhãn `[Môn của bạn - Tự động áp dụng]`.
  - Các môn của giảng viên khác gắn nhãn `[Giảng viên khác - Cần gửi duyệt]`.
- [ ] **Step 5: Kiểm tra cú pháp JavaScript**
  `node --check frontend/assets/js/api.js && node --check frontend/assets/js/views/instructor.js`
- [ ] **Step 6: Commit**
  ```bash
  git add frontend/assets/js/
  git commit -m "feat(ui): add dedicated instructor prerequisite approval view and optimize selection modal"
  ```

---

### Task 4: Trình Soạn Thảo Bài Giảng Chuẩn Microsoft Word (Ribbon 2 Hàng Nút) & Dọn Sạch Nhãn Cũ

**Files:**
- Modify: `frontend/assets/js/views/instructor.js:1090-1165,1730-1785,2105-2140`
- Modify: `frontend/assets/js/ui.js`
- Test: Syntax check `node --check`

**Interfaces:**
- Consumes: Content bài học, `DOMPurify`
- Produces: 
  - Đổi các nhãn nút:
    * `+ Tạo bài kiểm tra chương` -> `+ Tạo bài kiểm tra`
    * `Thêm bài giảng vào chương này` -> `Thêm bài giảng`
    * Bỏ chữ `Khối 1, 2, 3...` trên tất cả block card.
    * Đổi `Khối 1: Nội dung văn bản (Markdown)` thành `Nội dung bài học`.
    * Xóa bỏ hoàn toàn UI `Định dạng Markdown • Thầy/Cô có thể dùng **in đậm**...`.
  - Ribbon Toolbar chuẩn Microsoft Word 2 hàng nút gồm 5 cụm:
    1. Clipboard (Paste, Cut, Copy, Format Painter)
    2. Font (Font Family, Font Size, Grow/Shrink, Case Aa, Clear Formatting, Bold, Italic, Underline, Strikethrough, Subscript, Superscript, Highlight, Font Color)
    3. Paragraph (Bullets, Numbering, Indent, Align Left/Center/Right/Justify, Line Spacing, Shading, Borders)
    4. Styles (Normal, Heading 1, Heading 2, Title, Subtitle)
    5. Editing (Find, Replace, Select All)
  - Vùng soạn thảo WYSIWYG `contenteditable` với phím tắt chuẩn Word (`Ctrl+B`, `Ctrl+I`, `Ctrl+U`, `Ctrl+Z`, `Ctrl+Y`).

- [ ] **Step 1: Thay đổi toàn bộ các nhãn text theo yêu cầu người dùng trong `frontend/assets/js/views/instructor.js`**
  - Dòng 1101: `Thêm bài giảng vào chương này` -> `Thêm bài giảng`.
  - Dòng 1156: `+ Tạo bài kiểm tra chương` -> `+ Tạo bài kiểm tra`.
  - Dòng 1732: `Nội dung văn bản (Markdown)` -> `Nội dung bài học`.
  - Dòng 2115: Thay `Khối ${idx + 1}: ${typeLabel}` bằng `${typeLabel}` (loại bỏ hoàn toàn chữ "Khối").
  - Xóa bỏ thẻ UI Markdown helper tại dòng 1754-1758.
- [ ] **Step 2: Xây dựng thành phần Microsoft Word Ribbon 2 hàng nút**
  - Xây dựng HTML/CSS cho thanh Ribbon với 5 cụm:
    * Hàng 1: Clipboard (Dán, Cắt, Sao chép, Sao chép định dạng) | Font Selection (Aptos, Inter, Arial, Times New Roman), Cỡ chữ (8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28, 36, 48, 72), Tăng/Giảm cỡ, Đổi kiểu chữ Aa, Xóa định dạng | Styles nhanh (Normal, Heading 1, Heading 2, Title, Subtitle).
    * Hàng 2: Bold (B), Italic (I), Underline (U), Gạch ngang chữ, Chỉ số dưới ($x_2$), Chỉ số trên ($x^2$), Màu nền chữ (Highlight), Màu chữ (Font Color) | Đoạn văn (Dấu đầu dòng, Đánh số, Giảm thụt lề, Tăng thụt lề, Căn trái, Căn giữa, Căn phải, Căn đều 2 bên, Giãn dòng 1.0/1.15/1.5/2.0, Màu nền đoạn, Viền) | Editing (Tìm kiếm, Thay thế, Chọn tất cả).
- [ ] **Step 3: Gắn các bộ xử lý hành động (Action Handlers) cho Ribbon**
  - Tích hợp `document.execCommand` / modern Selection API với các lệnh formatting chuẩn.
  - Xử lý Format Painter (lưu trạng thái định dạng từ đoạn được chọn và áp dụng vào đoạn tiếp theo).
  - Xử lý Find & Replace (tìm kiếm từ khóa trong bài và thay thế tự động).
  - Bắt các phím tắt bàn phím thông dụng: `Ctrl+B`, `Ctrl+I`, `Ctrl+U`, `Ctrl+Z`, `Ctrl+Y`.
- [ ] **Step 4: Khử khuẩn nội dung và lưu trữ**
  - Lấy `innerHTML` từ vùng soạn thảo, khử trùng qua `DOMPurify.sanitize`, đảm bảo lưu giữ HTML chuẩn cho bài học.
- [ ] **Step 5: Kiểm tra cú pháp JavaScript**
  `node --check frontend/assets/js/views/instructor.js`
- [ ] **Step 6: Commit**
  ```bash
  git add frontend/assets/js/views/instructor.js
  git commit -m "feat(editor): build Microsoft Word 2-row ribbon toolbar and clean legacy block labels"
  ```

---

### Task 5: Khối Câu Hỏi Tương Tác: Question Stepper, Dán Ảnh Đề Bài & Đáp Án, Sửa Lỗi Điền Khuyết & Nối Từ

**Files:**
- Modify: `frontend/assets/js/views/instructor.js:920-960,1920-2100,2400-2465`
- Modify: `frontend/assets/js/views/student.js:3840-4030`
- Modify: `src/pwd301/blueprints/instructor/routes.py` (upload ảnh câu hỏi)
- Test: Syntax check `node --check`

**Interfaces:**
- Consumes: Dữ liệu quiz từ bài giảng, Clipboard Image Paste Event (`clipboardData.items`)
- Produces: 
  - Khắc phục 100% bug chuyển thể loại câu hỏi: `data-active-qtype` được lưu chuẩn xác trên card, Điền khuyết và Nối từ không bao giờ bị reset về trắc nghiệm.
  - Question Stepper: Thanh điều hướng `[Câu 1] [Câu 2] [Câu 3] ... [+] Thêm câu hỏi` ở đầu khối câu hỏi.
  - Nút **"Lưu câu hỏi"** độc lập ngay tại khối.
  - Cho phép dán ảnh (Ctrl+V) hoặc chọn tệp tải lên cho:
    * Ảnh minh họa câu hỏi (`question_image_url`).
    * Ảnh minh họa từng đáp án lựa chọn (`options[i].image_url`).
  - Trải nghiệm học sinh:
    * Điền khuyết: Ô nhập input nằm tự nhiên trong dòng câu hỏi.
    * Nối từ: 2 cột thẻ bấm chọn cặp ghép theo màu sắc trực quan.

- [ ] **Step 1: Thêm endpoint upload ảnh câu hỏi/đáp án trong backend**
  - Endpoint `POST /instructor/courses/<course_id>/lessons/<lesson_id>/quiz-image`: Nhận tệp ảnh (PNG, JPG, WebP), lưu vào storage bài học và trả về URL ảnh.
- [ ] **Step 2: Sửa triệt để bug type mapping và lưu dữ liệu trong `frontend/assets/js/views/instructor.js`**
  - Sửa `scrapeBlocksFromDom`: Đọc `q_type` từ bộ nhớ đối tượng hoặc `card.querySelector('[data-active-qtype]').dataset.activeQtype` chuẩn xác.
  - Bảo toàn toàn bộ dữ liệu của từng loại:
    * Điền khuyết: lưu `blank_answer` và danh sách blanks.
    * Nối từ: lưu đầy đủ các cặp `pairs: [{left, right}]`.
  - Thêm nút **"Lưu câu hỏi"** ngay trong khối quiz card, cho phép giảng viên lưu ngay lập tức bài giảng mà không cần cuộn tìm nút lưu tổng.
- [ ] **Step 3: Xây dựng giao diện Question Stepper cho Giảng viên**
  - Thay vì cuộn dài, hiển thị thanh Stepper: các nút tròn/viên thuốc `[1] [2] [3] ... [+] Thêm câu hỏi` kèm nút xóa câu hỏi hiện tại.
  - Giảng viên bấm vào số câu nào thì chỉ hiển thị giao diện soạn thảo chi tiết của câu đó.
- [ ] **Step 4: Hiện thực hóa tính năng dán ảnh (Ctrl+V) và upload ảnh**
  - Lắng nghe sự kiện `paste` trên ô nhập đề bài: Nếu clipboard chứa ảnh (`item.type.indexOf('image') !== -1`), tự động chuyển thành Blob, gửi lên endpoint upload và chèn URL vào `block.question_image_url`, hiển thị preview ảnh ngay dưới đề bài.
  - Lắng nghe sự kiện `paste` trên từng ô nhập đáp án lựa chọn (hoặc cặp nối từ): Hỗ trợ dán ảnh cho từng đáp án riêng biệt.
  - Cung cấp nút chọn file ảnh thủ công cạnh ô dán ảnh.
- [ ] **Step 5: Tái thiết kế trải nghiệm làm bài của Học sinh trong `frontend/assets/js/views/student.js`**
  - Điền khuyết: Thay thế `[___]` bằng thẻ input `<input class="cisco-quiz-blank-input ...">` hiển thị đồng hàng (inline) với cỡ chữ và kiểu dáng đẹp mắt.
  - Nối từ: Thiết kế 2 cột thẻ (Cột A và Cột B). Học sinh nhấp 1 thẻ ở Cột A rồi nhấp 1 thẻ ở Cột B, hệ thống tự động gán cặp bằng màu sắc nổi bật (Xanh lá, Xanh dương, Cam, Tím...) và hiển thị huy hiệu đã ghép. Nhấp lại để hủy ghép.
  - Hiển thị ảnh minh họa câu hỏi và ảnh minh họa đáp án nếu có.
- [ ] **Step 6: Kiểm tra cú pháp JavaScript**
  `node --check frontend/assets/js/views/instructor.js && node --check frontend/assets/js/views/student.js`
- [ ] **Step 7: Commit**
  ```bash
  git add frontend/assets/js/ src/pwd301/
  git commit -m "feat(quiz): build question stepper, image paste support, and redesign fill-in and matching experience"
  ```

---

### Task 6: Cây Thư Mục Đề Cương Bài Học Phía Học Sinh (Play / Lock Trực Quan)

**Files:**
- Modify: `frontend/assets/js/views/student.js:2170-2260`
- Test: Syntax check `node --check`

**Interfaces:**
- Consumes: `activeItem`, `lesson._isCompleted`, `lesson._isUnlocked`
- Produces: 
  - Khắc phục lỗi hiển thị mã bài (đánh số chuẩn `1.1`, `1.2`, `2.1`, `2.2` theo đúng thứ tự chương).
  - Bài đang học: Hiển thị nổi bật với nút Play bo góc nền xanh dịu, text sáng, có active indicator rõ ràng.
  - Bài bị khóa: Hiển thị icon Lock với nền mờ và nhãn "Khóa" trực quan.

- [ ] **Step 1: Sửa logic sinh mã bài học theo cấu trúc chương**
  - Tính toán `displayCode`: lấy chỉ số chương thực tế `mIdx + 1` và chỉ số bài `lIdx + 1` để đảm bảo bài thuộc Chương 1 luôn là `1.1, 1.2`, bài thuộc Chương 2 luôn là `2.1, 2.2`.
- [ ] **Step 2: Nâng cấp giao diện hiển thị bài học trong `outline-accordion-list`**
  - **Bài đang học (`isCur`)**:
    Hiển thị dạng nút Play viên thuốc nổi bật:
    `<div class="p-2.5 rounded-xl bg-emerald-600 text-white font-bold shadow-xs flex items-center justify-between gap-2 text-xs select-none">`
    `<div class="flex items-center gap-2 min-w-0"><span class="material-symbols-outlined text-[18px]">play_circle</span><span>${displayCode} ${title}</span></div><span class="text-[10px] uppercase tracking-wider bg-white/20 px-2 py-0.5 rounded-md">Đang học</span></div>`
  - **Bài đã hoàn thành (`isDone`)**:
    Icon Checkmark xanh lá mềm mại kèm chữ đậm vừa.
  - **Bài chưa hoàn thành nhưng đã mở khóa**:
    Icon Circle xám nhạt, viền tinh tế, hover sáng.
  - **Bài bị khóa (`!isUnlocked`)**:
    Icon Lock xám, nền xám mờ (`opacity-60`), có nhãn "Khóa" ở góc phải. Khi nhấp vào, hiển thị toast nhắc nhở nhẹ nhàng.
- [ ] **Step 3: Kiểm tra cú pháp JavaScript**
  `node --check frontend/assets/js/views/student.js`
- [ ] **Step 4: Commit**
  ```bash
  git add frontend/assets/js/views/student.js
  git commit -m "feat(student-tree): polish syllabus tree with prominent Play button for active lesson and clear Lock badges"
  ```

---

### Task 7: Giao Diện Đối Chiếu Thay Đổi Cho Giảng Viên & Màn Hình Phê Duyệt Của Admin (Categorized Visual Tree Diff)

**Files:**
- Modify: `frontend/assets/js/views/instructor.js:3450-3600`
- Modify: `frontend/assets/js/views/admin.js:1920-2100`
- Test: Syntax check `node --check`

**Interfaces:**
- Consumes: Dữ liệu diff từ `GET /instructor/courses/<id>/changeset/diff` và `GET /admin/courses/<id>/changeset/diff`
- Produces: 
  - Modal Đối chiếu của Giảng viên: Hiển thị đầy đủ 5 tab/khối (Cấu trúc & Thứ tự, Nội dung & Media, Câu hỏi tương tác, Bài kiểm tra, Tiêu chí hoàn thành & Ảnh bìa) với các nhãn màu [Thêm], [Xóa], [Di chuyển], [Sửa đổi].
  - Màn hình duyệt của Admin: Cây đối chiếu phân loại động từ dữ liệu thật, loại bỏ toàn bộ các trường trống "Không đặt" giả lập.

- [ ] **Step 1: Xây dựng component Render Categorized Visual Diff dùng chung**
  - Viết hàm `renderCategorizedDiffHtml(diffData)`:
    * Nhóm 1 (Cấu trúc & Thứ tự): Liệt kê các chương được thêm/xóa/đổi tên; bài học di chuyển giữa các chương (ví dụ: `Bài "X" [Di chuyển]: Chương 1 -> Chương 2`); bài học đổi thứ tự (`Vị trí #1 -> #3`).
    * Nhóm 2 (Nội dung & Media): Liệt kê bài học có thêm/xóa video, tải lên tài liệu mới hoặc chỉnh sửa văn bản.
    * Nhóm 3 (Câu hỏi tương tác): Liệt kê từng câu hỏi thêm mới, câu hỏi xóa bỏ, câu hỏi sửa đổi.
    * Nhóm 4 (Bài kiểm tra / Đánh giá): Liệt kê bài kiểm tra chương hoặc Final Test được tạo mới, cập nhật thời gian/điểm, hoặc gỡ bỏ.
    * Nhóm 5 (Tiêu chí hoàn thành & Cài đặt): So sánh song song Before vs After của Điểm GPA tối thiểu, % tiến độ bài học, Bắt buộc học tất cả bài, Bắt buộc làm bài thi, Cấp chứng chỉ, Ảnh bìa khóa học.
- [ ] **Step 2: Nâng cấp Modal "Đối chiếu thay đổi giáo trình" của Giảng viên trong `instructor.js`**
  - Tích hợp `renderCategorizedDiffHtml`, hiển thị tổng số thay đổi theo từng nhóm với badge màu tương ứng.
- [ ] **Step 3: Nâng cấp Màn hình Duyệt Khóa học của Quản trị viên trong `admin.js`**
  - Thay thế khối "Đang tải đối chiếu giáo trình..." và các trường tĩnh bằng cây đối chiếu phân loại động lấy từ endpoint diff.
  - Hiển thị rõ ràng các nút hành động của Admin: **[Phê duyệt toàn bộ cập nhật]** (xanh lá) và **[Từ chối cập nhật]** (đỏ) kèm nhập lý do.
- [ ] **Step 4: Kiểm tra cú pháp JavaScript**
  `node --check frontend/assets/js/views/instructor.js && node --check frontend/assets/js/views/admin.js`
- [ ] **Step 5: Commit**
  ```bash
  git add frontend/assets/js/views/
  git commit -m "feat(diff-ui): render 5-category visual tree diff in instructor modal and admin review screen"
  ```

---

### Task 8: Kiểm Thử Toàn Diện & Xác Minh Thực Tế (E2E & Regressions)

**Files:**
- Run: `pytest tests/api/test_course_changeset_deep_diff.py tests/api/test_prerequisite_approval_workflow.py`
- Run: `python scripts/repo_check.py`
- Run: E2E Browser Testing via Chrome DevTools MCP trên running server `http://127.0.0.1:5000`

**Interfaces:**
- Consumes: Toàn bộ hệ thống Backend và Frontend đã được sửa đổi.
- Produces: Báo cáo kết quả kiểm thử thực nghiệm 100% không lỗi.

- [ ] **Step 1: Chạy toàn bộ các test suite mới**
  `pytest tests/api/test_course_changeset_deep_diff.py tests/api/test_prerequisite_approval_workflow.py -v`
- [ ] **Step 2: Chạy kiểm tra quy chuẩn tĩnh và linter**
  `ruff check src/ tests/` và `node --check frontend/assets/js/views/*.js`
- [ ] **Step 3: Khởi động server và xác minh trực quan trên trình duyệt thật (Chrome DevTools)**
  - Đăng nhập Giảng viên:
    * Kiểm tra giao diện soạn bài: nhãn "Tạo bài kiểm tra", "Thêm bài giảng", "Nội dung bài học", không có chữ "Khối", Ribbon MS Word 2 hàng hoạt động mượt mà.
    * Kiểm tra khối câu hỏi: chuyển đổi Điền khuyết và Nối từ không bị reset, dán ảnh câu hỏi/đáp án thành công, bấm "Lưu câu hỏi" thành công.
    * Kiểm tra menu "Duyệt môn tiên quyết" và modal chọn môn tiên quyết chỉ hiển thị môn PUBLISHED.
    * Kiểm tra modal "Đối chiếu thay đổi" hiển thị đầy đủ 5 phân nhóm có badge màu.
  - Đăng nhập Admin:
    * Vào màn hình duyệt khóa học: kiểm tra cây đối chiếu 5 phân nhóm hiển thị đúng dữ liệu thật, duyệt thành công.
  - Đăng nhập Học sinh:
    * Vào học khóa học: kiểm tra cây đề cương có nút Play nổi bật cho bài đang học, icon Lock cho bài bị khóa.
    * Kiểm tra làm bài tập điền khuyết (ô input nội dòng) và nối từ (thẻ màu) trực quan không lỗi.
- [ ] **Step 4: Chốt hoàn thành task**
