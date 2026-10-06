# Kế Hoạch Hiện Thực Hóa: Tinh Gọn & Hiện Đại Hóa Toàn Diện Curriculum Studio & Exam Studio (TASK-082)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Hiện đại hóa, xóa bỏ các rào cản UX/UI rườm rà và thống nhất luồng biên soạn bài học và đề thi: tích hợp cảnh báo ảnh bìa vào khu vực cover & chặn duyệt nếu thiếu ảnh bìa; tinh gọn thanh công cụ thêm nội dung (bổ sung khối câu hỏi đa thể loại: trắc nghiệm, điền khuyết, nối từ gọn gàng); loại bỏ hoàn toàn thời lượng ước tính; nâng cấp cây bài giảng với kéo thả (Drag & Drop) và thanh chỉnh độ rộng menu (Resizable Sidebar); tinh giản cấu hình phòng thi tự do; mở khóa thang điểm tùy biến, phân loại câu hỏi linh hoạt và liên kết đề thi trực tiếp vào bài học cụ thể.

**Architecture:** Tuân thủ triệt để kiến trúc Pure Headless REST API (trả phong bì chuẩn JSON) và Single-DOM SPA Frontend (Tailwind CSS, vanilla JS views với UI.js). Đảm bảo nguyên tắc Fail-Closed và bảo toàn 100% ràng buộc CSDL Microsoft SQL Server mà không phá vỡ tính tương thích ngược.

**Tech Stack:** Python 3.12, Flask, SQLAlchemy, Microsoft SQL Server, Vanilla JS (ES6+), Tailwind CSS, Pytest, Chrome DevTools.

**Spec:** Yêu cầu người dùng tại phiên làm việc ngày 07/10/2026 và kết quả phỏng vấn làm rõ chi tiết qua skill `/grill-me`.

## Global Constraints

- **Pure Headless Backend**: Tuyệt đối không sinh HTML template (Jinja) hoặc file static dư thừa. Tất cả API trả JSON chuẩn `{"success": true/false, "data": ..., "error": ...}`.
- **Fail-Closed & Safety**: Khóa học thiếu ảnh bìa bị chặn gửi duyệt xuất bản ở cả Frontend và Backend.
- **CSDL MSSQL Invariant**: Giữ cột `estimated_duration_minutes` nullable trên CSDL để bảo toàn dữ liệu lịch sử, nhưng loại bỏ hoàn toàn khỏi API, Service logic và giao diện.
- **UX & Accessibility**: Tỷ lệ padding nút bấm 2:1, màu sắc dịu chuẩn WCAG AA, không dùng Pure Black/White, giữ nút di chuyển bàn phím/touch song song với kéo thả Drag & Drop.
- **Zero Clutter**: Loại bỏ toàn bộ dấu `+` thừa trước nhãn chữ.

## Review Focus

1. **Khóa học thiếu ảnh bìa:** Khi bấm gửi duyệt xuất bản, hệ thống phải chặn ngay lập tức với thông báo rõ ràng; khi đã tải ảnh lên thành công, nút gửi duyệt phải mở lại bình thường.
2. **Kéo thả bài giảng giữa các chương:** Khi kéo thả một bài giảng từ Chương A sang Chương B, vị trí (`position`) và `learning_unit_id` phải được cập nhật chuẩn xác trên cả UI và CSDL.
3. **Thanh chỉnh độ rộng Sidebar:** Độ rộng tùy chỉnh của menu phải được lưu vào `localStorage` và duy trì ổn định khi chuyển trang hoặc tải lại trình duyệt.
4. **Không giới hạn thời gian / số lần thi:** Khi giảng viên để trống ô "Thời gian làm bài" hoặc "Số lần làm bài tối đa", hệ thống phải lưu `time_limit_minutes = null` và `attempt_limit = null`, cho phép học viên làm bài không giới hạn.
5. **Đề thi liên kết bài học:** Khi học viên học bài học đã liên kết đề thi, ở cuối bài giảng phải hiển thị thẻ làm bài kiểm tra củng cố với trạng thái rõ ràng.

---

### Task 0: Thanh Lọc Toàn Diện Logic Cũ, Bộ Nhớ Cũ & Cập Nhật Đặc Tả Chuẩn (Audit & Purge of Obsolete Workflows)

**Files:**
- Modify: `tasks/CURRENT.md`
- Modify: `docs/features/curriculum-studio.md` (nếu có hoặc tạo mới định hướng chuẩn)

**Interfaces:**
- Consumes: Yêu cầu tinh chỉnh mới từ phiên thảo luận /grill-me.
- Produces: Bản mô tả chuẩn xác, độc tôn (single source of truth) về workflow mới của Curriculum Studio và Exam Studio trong `tasks/CURRENT.md`.

- [ ] **Step 1: Xóa bỏ mọi ghi chú hoặc logic lỗi thời trong `tasks/CURRENT.md`**
  - Chuyển `Active task: None` thành `# Active task: TASK-082 — Curriculum & Exam Studio Full Streamlining & Modernization`.
  - Khai báo danh mục các điểm thay đổi bất biến: cấm khôi phục banner vàng ảnh bìa ngoài, cấm khôi phục dấu `+` trước chữ, cấm dùng `estimated_duration_minutes` trong bài giảng, cấm khóa thang điểm 10 cứng hoặc khóa Bloom cố định.
- [ ] **Step 2: Commit cập nhật thanh lọc bộ nhớ**
  ```bash
  git add tasks/CURRENT.md
  git commit -m "docs(task): initialize TASK-082 and purge obsolete workflow baselines"
  ```

---

### Task 1: Tích Hợp Cảnh Báo Ảnh Bìa Vào Khung Cover & Chặn Duyệt Xuất Bản (Gating & Cover Redesign)

**Files:**
- Modify: `frontend/assets/js/views/instructor.js:2317-2425`
- Modify: `src/pwd301/services/course_service.py`
- Modify: `src/pwd301/blueprints/instructor/routes.py`
- Test: `tests/api/test_course_workflow.py`

**Interfaces:**
- Consumes: `course.thumbnail_url`, `course.status`
- Produces: UI vùng ảnh bìa tự cảnh báo & trigger tải ảnh trực quan; API trả lỗi 400/422 nếu `thumbnail_url` rỗng khi gọi submit review.

- [ ] **Step 1: Viết test kiểm tra chặn gửi duyệt xuất bản khi khóa học chưa có ảnh bìa**
  ```python
  def test_submit_course_for_review_requires_thumbnail(client, instructor_token, draft_course_without_thumbnail):
      res = client.post(
          f"/instructor/courses/{draft_course_without_thumbnail.id}/submit-review",
          headers={"Authorization": f"Bearer {instructor_token}"}
      )
      assert res.status_code == 400
      assert "ảnh bìa" in res.json["error"]["message"].lower()
  ```
- [ ] **Step 2: Chạy test để xác nhận test fail**
  `pytest tests/api/test_course_workflow.py -k test_submit_course_for_review_requires_thumbnail -v`
- [ ] **Step 3: Triển khai backend validation trong `src/pwd301/services/course_service.py`**
  - Trong hàm `submit_course_for_review`, bổ sung kiểm tra:
    ```python
    if not course.thumbnail_url or not str(course.thumbnail_url).strip():
        raise CourseValidationError("Khóa học phải có ảnh bìa đại diện trước khi gửi Quản trị viên xét duyệt xuất bản.")
    ```
- [ ] **Step 4: Chỉnh sửa frontend trong `frontend/assets/js/views/instructor.js`**
  - Xóa bỏ hoàn toàn khối `<!-- Reminder Banner: Missing Cover Photo -->` (dòng 2318-2340).
  - Tích hợp trực tiếp vào khung ảnh bìa:
    + Nếu `!course.thumbnail_url`: Hiển thị placeholder có biểu tượng ảnh, badge nhạt: *"Chưa có ảnh bìa đại diện (Bắt buộc để xuất bản)"* và nút bấm trực tiếp *"Tải ảnh bìa ngay"*.
    + Nếu đã có `course.thumbnail_url`: Hiển thị ảnh bìa sắc nét kèm nút nhỏ *"Đổi ảnh bìa"* ở góc dưới.
  - Tại nút *"Gửi duyệt xuất bản"*, nếu `!course.thumbnail_url`: hiển thị tooltip/cảnh báo khi click và không cho gửi đi.
- [ ] **Step 5: Chạy test để xác nhận pass**
  `pytest tests/api/test_course_workflow.py -v`
- [ ] **Step 6: Commit**
  ```bash
  git add src/pwd301/services/course_service.py frontend/assets/js/views/instructor.js tests/api/test_course_workflow.py
  git commit -m "feat(course): integrate cover banner into media card and enforce thumbnail requirement for review"
  ```

---

### Task 2: Loại Bỏ Hoàn Toàn "Thời Lượng Ước Tính (Phút)" Hệ Thống (Eliminate Estimated Duration)

**Files:**
- Modify: `frontend/assets/js/views/instructor.js:985-1000,1708-1725`
- Modify: `src/pwd301/services/lesson_service.py`
- Modify: `src/pwd301/blueprints/instructor/routes.py`
- Modify: `src/pwd301/blueprints/api_lessons/routes.py`
- Test: `tests/api/test_lesson_api.py`

**Interfaces:**
- Consumes: Lesson payload không còn chứa `estimated_duration_minutes`
- Produces: API và Service bỏ qua trường này, không validate > 0; UI không còn bất kỳ ô nhập hoặc nhãn hiển thị nào liên quan đến thời lượng ước tính bài giảng.

- [ ] **Step 1: Viết test xác nhận lưu bài giảng không cần `estimated_duration_minutes`**
  ```python
  def test_create_update_lesson_without_duration(client, instructor_token, test_unit):
      payload = {"title": "Bài giảng mới không thời lượng", "markdown_content": "# Nội dung"}
      res = client.post(f"/instructor/units/{test_unit.id}/lessons", json=payload, headers={"Authorization": f"Bearer {instructor_token}"})
      assert res.status_code == 201
  ```
- [ ] **Step 2: Xác nhận test chạy và điều chỉnh backend**
  - Trong `src/pwd301/services/lesson_service.py`: Xóa bỏ việc bắt buộc validate `estimated_duration_minutes must be greater than zero`, chấp nhận `None` hoặc bỏ qua an toàn.
  - Trong `src/pwd301/blueprints/instructor/routes.py`: Xóa logic trích xuất `estimated_duration_minutes` khi tạo/cập nhật bài giảng.
- [ ] **Step 3: Chỉnh sửa frontend trong `frontend/assets/js/views/instructor.js`**
  - Xóa trường nhập `#input-lesson-duration` (dòng 1710-1718).
  - Xóa hiển thị `${l.estimated_duration_minutes || 15} phút` trên thẻ cây bài giảng (dòng 990).
  - Cập nhật hàm `scrapeBlocksFromDom` bỏ đọc `durationInput`.
- [ ] **Step 4: Chạy test kiểm chứng**
  `pytest tests/api/test_lesson_api.py -v`
- [ ] **Step 5: Commit**
  ```bash
  git add src/pwd301/services/lesson_service.py src/pwd301/blueprints/instructor/routes.py frontend/assets/js/views/instructor.js tests/api/test_lesson_api.py
  git commit -m "refactor(lesson): remove estimated duration field from UI, routes, and services"
  ```

---

### Task 3: Tinh Gọn Thanh Công Cụ & Thêm Khối "Câu Hỏi" Đa Thể Loại (Trắc Nghiệm, Điền Khuyết, Nối Từ)

**Files:**
- Modify: `frontend/assets/js/views/instructor.js:1339-1620,1745-1785`
- Modify: `frontend/assets/js/views/student.js`
- Test: `tests/frontend/lesson_quiz_blocks.test.js` hoặc API test tương thích

**Interfaces:**
- Consumes: Block object với `type: 'quiz'` hoặc `type: 'question'`
- Produces: 
  - Nút thêm nội dung sạch sẽ: `Bài học`, `Video`, `Tài liệu`, `Câu hỏi` (không có dấu `+`).
  - Giao diện khối câu hỏi gồm Segmented Switch: `Trắc nghiệm` | `Điền khuyết` | `Nối từ`.

- [ ] **Step 1: Viết test kiểm tra cấu trúc dữ liệu của khối câu hỏi đa thể loại**
- [ ] **Step 2: Tinh chỉnh thanh công cụ trong `frontend/assets/js/views/instructor.js`**
  - Đổi tiêu đề: `<span class="material-symbols-outlined text-[18px] text-primary">add_circle</span>` $\rightarrow$ loại bỏ icon `add_circle`, text đổi thành `"THÊM NỘI DUNG:"`.
  - Đổi các nút:
    + `+ Văn bản` $\rightarrow$ `"Bài học"` (icon `menu_book`)
    + `+ Video` $\rightarrow$ `"Video"` (icon `smart_display`)
    + `+ Tài liệu` $\rightarrow$ `"Tài liệu"` (icon `description`)
    + `+ Trắc nghiệm` $\rightarrow$ `"Câu hỏi"` (icon `quiz`)
- [ ] **Step 3: Thiết kế lại thẻ khối câu hỏi trong bài giảng**
  - Bổ sung thanh chọn phân đoạn (Segmented Control):
    ```html
    <div class="flex items-center gap-1 p-1 bg-slate-100 dark:bg-slate-800 rounded-xl max-w-fit mb-3">
      <button type="button" class="tab-q-type px-3 py-1 text-xs font-bold rounded-lg ...">Trắc nghiệm</button>
      <button type="button" class="tab-q-type px-3 py-1 text-xs font-bold rounded-lg ...">Điền khuyết</button>
      <button type="button" class="tab-q-type px-3 py-1 text-xs font-bold rounded-lg ...">Nối từ</button>
    </div>
    ```
  - Triển khai form nhập liệu tinh gọn tương ứng với từng loại:
    + **Trắc nghiệm**: Câu hỏi, danh sách đáp án, radio chọn đáp án đúng, nút thêm lựa chọn nhỏ gọn.
    + **Điền khuyết**: Đề bài có `[___]`, danh sách các từ đáp án tương ứng từng chỗ trống.
    + **Nối từ**: Các cặp ghép Vế trái $\leftrightarrow$ Vế phải (tối thiểu 2 cặp).
  - Tích hợp trường giải thích (optional) và nút xóa khối.
- [ ] **Step 4: Cập nhật hàm cào dữ liệu DOM `scrapeBlocksFromDom` và view sinh viên**
  - Đảm bảo khi lưu bài giảng, toàn bộ dữ liệu của 3 loại câu hỏi được đóng gói vào payload an toàn.
  - Đồng bộ `student.js` để hiển thị bài tập mini-quiz tương tác mượt mà cho sinh viên.
- [ ] **Step 5: Kiểm tra cú pháp JavaScript**
  `node --check frontend/assets/js/views/instructor.js`
- [ ] **Step 6: Commit**
  ```bash
  git add frontend/assets/js/views/instructor.js frontend/assets/js/views/student.js
  git commit -m "feat(lesson): redesign content addition bar and multi-type question blocks"
  ```

---

### Task 4: Hiện Đại Hóa Menu Cấu Trúc Bài Giảng: Xóa "Thêm Bài", Kéo Thả (Drag & Drop) & Tùy Chỉnh Độ Rộng (Resizable Sidebar)

**Files:**
- Modify: `frontend/assets/js/views/instructor.js:790-1120,2600-2640`
- Modify: `frontend/assets/js/api.js`
- Test: E2E reorder & layout verification

**Interfaces:**
- Consumes: Cấu trúc chương & bài học
- Produces:
  - Chỉ có nút "Thêm Chương" ở trên cùng.
  - Chức năng kéo thả (Drag & Drop) giữa các chương và trong cùng chương.
  - Thanh kéo Resizable Sidebar với tính năng lưu kích thước vào `localStorage`.

- [ ] **Step 1: Xóa nút "Thêm bài" trên thanh công cụ đầu danh mục**
  - Trong `instructor.js`, xóa nút `#btn-tree-add-lesson` ("Thêm Bài").
  - Mở rộng nút `"Thêm Chương"` chiếm toàn chiều rộng của thanh thao tác trên đầu cây bài giảng. Giảng viên thêm bài học trực tiếp qua nút `"Thêm bài giảng vào chương này"` ở từng chương.
- [ ] **Step 2: Triển khai thanh chia đôi điều chỉnh độ rộng (Resizable Sidebar)**
  - Chuyển layout sang flexbox/grid có splitter:
    ```html
    <div id="curriculum-studio-wrapper" class="flex flex-col lg:flex-row items-stretch gap-0 relative">
      <aside id="curriculum-sidebar-pane" style="width: var(--sidebar-width, 360px);" class="shrink-0 ...">...</aside>
      <div id="curriculum-sidebar-resizer" class="hidden lg:flex w-2.5 hover:w-3 cursor-col-resize items-center justify-center bg-transparent hover:bg-primary/20 transition-all z-20" title="Kéo để chỉnh độ rộng menu">
        <div class="w-1 h-8 bg-slate-300 dark:bg-slate-700 rounded-full"></div>
      </div>
      <main id="curriculum-editor-pane" class="flex-1 min-w-0 ...">...</main>
    </div>
    ```
  - Thêm logic JavaScript bắt sự kiện chuột (`mousedown`, `mousemove`, `mouseup`), giới hạn độ rộng từ 280px đến 600px.
  - Lưu giá trị độ rộng vào `localStorage.setItem('pwd301_curriculum_sidebar_width', width + 'px')` và khôi phục khi nạp view.
- [ ] **Step 3: Triển khai Kéo Thả (Drag & Drop) Chương & Bài Giảng**
  - Gắn thuộc tính `draggable="true"` vào các thẻ `.unit-tree-node` và `.lesson-tree-item`.
  - Xử lý các sự kiện `dragstart`, `dragover`, `drop`, `dragend`:
    + Cho phép kéo thả Chương để đổi thứ tự các chương (gọi `ApiClient.reorderLearningUnits`).
    + Cho phép kéo thả Bài giảng để đổi thứ tự trong cùng chương hoặc chuyển sang chương khác (cập nhật `learning_unit_id` và gọi API reorder bài giảng).
    + Hiển thị đường kẻ đánh dấu vị trí thả (drop indicator).
- [ ] **Step 4: Kiểm tra cú pháp JavaScript**
  `node --check frontend/assets/js/views/instructor.js`
- [ ] **Step 5: Commit**
  ```bash
  git add frontend/assets/js/views/instructor.js
  git commit -m "feat(curriculum): add drag-and-drop reordering, resizable sidebar with localStorage persistence"
  ```

---

### Task 5: Tinh Giản Cấu Hình Phòng Thi & Loại Bỏ Giới Hạn Cứng (Exam Settings Simplification)

**Files:**
- Modify: `frontend/assets/js/views/instructor-exams.js:3160-3290,3640-3660`
- Test: `tests/api/test_assessment_api.py`

**Interfaces:**
- Consumes: Config thời gian và số lần làm bài
- Produces: Ô tự nhập thời gian làm bài (trống = vô hạn), ô tự nhập số lần thi (trống = vô hạn), switch toggle ca thi, nhãn gọn gàng.

- [ ] **Step 1: Viết test kiểm tra tạo đề thi không giới hạn thời gian và số lần**
  ```python
  def test_create_assessment_unlimited_time_and_attempts(client, instructor_token, test_course):
      payload = {
          "title": "Đề thi tự do",
          "assessment_type": "QUIZ",
          "time_limit_minutes": None,
          "attempt_limit": None,
      }
      res = client.post(f"/instructor/courses/{test_course.id}/assessments", json=payload, headers={"Authorization": f"Bearer {instructor_token}"})
      assert res.status_code == 201
      data = res.json["data"]
      assert data["time_limit_minutes"] is None
      assert data["attempt_limit"] is None
  ```
- [ ] **Step 2: Chỉnh sửa giao diện cấu hình đề thi trong `frontend/assets/js/views/instructor-exams.js`**
  - Đổi *"Thời lượng làm bài (Phút)"* $\rightarrow$ `"Thời gian làm bài"`:
    + Xóa bỏ hoàn toàn cụm nút preset `15'`, `45'`, `60'`, `90'`, `120'`.
    + Giữ lại 1 ô `<input type="number">`, thêm placeholder: `"Để trống = không giới hạn thời gian"`.
  - Đổi *"Số lần làm bài tối đa"*:
    + Thay thẻ `<select>` bằng 1 ô `<input type="number" min="1">`, placeholder: `"Để trống = không giới hạn"`.
  - Đổi *"Xáo trộn ngẫu nhiên thứ tự câu hỏi và phương án đáp án cho mỗi thí sinh"* $\rightarrow$ `"Trộn câu hỏi và đáp án"`.
  - Đổi *"2. Thời gian giao & Hạn bài thi"* $\rightarrow$ `"Thời gian"`.
  - Đổi *"Kích hoạt ca thi theo giờ"* từ checkbox thường thành công tắc gạt (Toggle Switch UI).
- [ ] **Step 3: Cập nhật logic cào dữ liệu khi lưu đề thi**
  - Nếu ô thời gian hoặc số lần bị xóa trống, gửi `null` lên backend.
- [ ] **Step 4: Chạy test kiểm thử**
  `pytest tests/api/test_assessment_api.py -v`
- [ ] **Step 5: Commit**
  ```bash
  git add frontend/assets/js/views/instructor-exams.js tests/api/test_assessment_api.py
  git commit -m "feat(exam): simplify exam settings with unconstrained duration, attempts, and toggle switch"
  ```

---

### Task 6: Mở Khóa Thang Điểm, Phân Loại Câu Hỏi Linh Hoạt & Liên Kết Đề Thi Vào Bài Học (Academic Matrix & Lesson-Linked Assessment)

**Files:**
- Modify: `frontend/assets/js/views/instructor-exams.js:965-980,2970-3145,3660-3715`
- Modify: `frontend/assets/js/views/student.js`
- Modify: `src/pwd301/services/assessment_service.py`
- Modify: `src/pwd301/blueprints/instructor/routes.py`
- Test: `tests/api/test_lesson_linked_assessment.py`

**Interfaces:**
- Consumes: Target lesson ID, question classifications, custom total score
- Produces:
  - Nhập tổng thang điểm có nút chia đều + chỉnh điểm lẻ từng câu.
  - Phân loại (Nhận biết / Thông hiểu / Vận dụng) chỉnh sửa tự do bằng dropdown.
  - Cascading select: Môn học $\rightarrow$ Chương $\rightarrow$ Bài học khi chọn "Liên kết theo Bài học".
  - Hiển thị bài thi ở cuối bài học tương ứng cho sinh viên.

- [ ] **Step 1: Viết test kiểm tra đề thi liên kết theo bài học**
  ```python
  def test_lesson_linked_assessment_creation_and_retrieval(client, instructor_token, student_token, test_lesson):
      payload = {
          "title": "Kiểm tra củng cố bài học",
          "assessment_type": "QUIZ",
          "lesson_id": test_lesson.id
      }
      res = client.post(f"/instructor/courses/{test_lesson.course_id}/assessments", json=payload, headers={"Authorization": f"Bearer {instructor_token}"})
      assert res.status_code == 201
  ```
- [ ] **Step 2: Triển khai lưu trữ và liên kết bài học ở backend**
  - Cập nhật `create_assessment` trong `assessment_service.py` để chấp nhận `lesson_id` và gán vào các câu hỏi thuộc đề thi đó.
- [ ] **Step 3: Tinh chỉnh giao diện Ma trận học vụ trong `frontend/assets/js/views/instructor-exams.js`**
  - Đổi *"1. Xác định Bối cảnh & Phạm vi Học vụ (Academic Provenance)"* $\rightarrow$ `"Hình thức kiểm tra"`. Xóa nhãn phụ *"Hình thức tổ chức đề thi"*.
  - Thêm bộ chọn liên kết khi chọn radio `"Liên kết theo Bài học (Lesson-Linked)"`:
    + Tự động nạp danh sách Chương và Bài học của môn học đã chọn.
    + Cung cấp 2 dropdown liên hoàn: `Chọn Chương học` $\rightarrow$ `Chọn Bài học cụ thể`.
  - Đổi *"Phân bổ Mức độ Bloom"* $\rightarrow$ `"Phân loại"`:
    + Thay badge tĩnh trên từng câu hỏi thành dropdown `<select>` gồm 3 tùy chọn: `"Nhận biết"`, `"Thông hiểu"`, `"Vận dụng"`.
    + Cập nhật thống kê phân loại ở header ngay khi giảng viên thay đổi lựa chọn.
  - Nâng cấp *"Thang điểm tính toán"*:
    + Cho phép nhập số điểm tổng mong muốn (ví dụ 10.0đ hoặc 100đ).
    + Bổ sung nút bấm `"Chia đều điểm"` để tự động phân bổ đều điểm cho tất cả các câu hỏi trong đề, đồng thời vẫn cho phép sửa ô điểm của từng câu hỏi riêng lẻ.
- [ ] **Step 4: Hiển thị bài thi liên kết ở giao diện học viên (`student.js`)**
  - Khi học viên xem nội dung một bài học, nếu bài học đó có đề thi liên kết, hiển thị một thẻ hành động nổi bật ở cuối trang bài giảng:
    + Tên bài kiểm tra, số câu hỏi, thang điểm, nút CTA: `"Làm bài kiểm tra củng cố"`.
- [ ] **Step 5: Chạy test kiểm chứng**
  `pytest tests/api/test_lesson_linked_assessment.py -v`
- [ ] **Step 6: Commit**
  ```bash
  git add frontend/assets/js/views/instructor-exams.js frontend/assets/js/views/student.js src/pwd301/services/assessment_service.py
  git commit -m "feat(assessment): implement custom score distribution, flexible classification, and lesson-linked exam workflow"
  ```

---

### Task 7: Kiểm Thử Toàn Diện, Rà Soát Mã Nguồn & Xác Minh Trực Tiếp Trên Trình Duyệt Thật (Verification & Review)

**Files:**
- Test: Toàn bộ test suite backend và static checkers

- [ ] **Step 1: Chạy kiểm tra tĩnh và định dạng mã nguồn**
  ```powershell
  python scripts/repo_check.py
  ruff check src/ tests/
  node --check frontend/assets/js/views/instructor.js
  node --check frontend/assets/js/views/instructor-exams.js
  node --check frontend/assets/js/views/student.js
  ```
- [ ] **Step 2: Chạy kiểm thử tự động pytest toàn bộ các module liên quan**
  ```powershell
  pytest tests/api/test_course_workflow.py tests/api/test_lesson_api.py tests/api/test_assessment_api.py -v
  ```
- [ ] **Step 3: Khởi chạy server và xác minh trực quan qua trình duyệt (Chrome DevTools MCP)**
  - Kiểm tra vùng ảnh bìa và nút gửi duyệt khi có/không có ảnh bìa.
  - Thêm các khối nội dung bài học (Bài học, Video, Tài liệu, Câu hỏi đa dạng).
  - Thao tác kéo thả bài giảng và kéo dãn menu Cấu trúc bài giảng.
  - Kiểm tra luồng tạo đề thi với thời gian tự do, chia đều điểm, đổi phân loại câu hỏi và liên kết bài học.
- [ ] **Step 4: Commit và hoàn tất**
  ```bash
  git commit --allow-empty -m "chore: complete TASK-082 verification and end-to-end testing"
  ```
