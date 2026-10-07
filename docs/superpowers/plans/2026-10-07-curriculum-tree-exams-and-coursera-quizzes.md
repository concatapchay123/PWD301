# Kế Hoạch Hiện Thực Hóa: Tích Hợp Bài Kiểm Tra Vào Cây Bài Học, Mini-Quiz Chuẩn Coursera, Tinh Gọn Gửi Duyệt & Chuẩn Hóa Darkmode (TASK-083)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Hoàn thiện và tinh gọn toàn diện trải nghiệm giảng viên và học viên: sửa lỗi preview học viên, xóa bỏ thanh nháp trùng lặp để chuyển sang cặp nút "Gửi duyệt cập nhật" & "Xem thay đổi" kèm modal đối chiếu Before/After chi tiết; nhúng trực tiếp Bài kiểm tra từng chương và Final Test vào cây bài học có điều kiện mở khóa tuần tự (bãi bỏ hoàn toàn khối bài thi cũ); nâng cấp mini-quiz theo chuẩn phân trang Coursera có điểm chuẩn đạt và cơ chế làm lại từ đầu; chuẩn hóa mã màu Dark Mode (loại bỏ màu tím lệch tông) và trang bị tính năng kéo thả tự do vị trí Bạch tuộc AI.

**Architecture:** Pure Headless REST API (JSON chuẩn `{"success": true/false, "data": ..., "error": ...}`) kết hợp Single-DOM SPA (Vanilla JS + Tailwind CSS tokens). Không tạo file tĩnh/template thừa. Fail-closed trong bảo mật bài thi và tiến độ học tập.

**Tech Stack:** Python 3.12, Flask, SQLAlchemy, Microsoft SQL Server, Vanilla JS (ES6+), Tailwind CSS, Pytest, Chrome DevTools.

**Spec:** Yêu cầu người dùng ngày 07/10/2026 và kết quả phỏng vấn làm rõ chi tiết qua skill `/grill-me`.

## Global Constraints

- **Pure Headless Backend**: Không sinh template Jinja `*.html` hay tệp preview giả lập. Mọi phản hồi API tuân thủ envelope JSON chuẩn.
- **Fail-Closed Unlocking**: Bài kiểm tra chương chỉ mở khi hoàn thành 100% bài học của chương đó; Final Test chỉ mở khi hoàn thành 100% bài học toàn khóa VÀ nằm trong khung giờ thi hợp lệ (`open_at` <= now <= `close_at`).
- **Zero Obsolete Workflows**: Cấm tái hiện thanh nháp dưới `#curriculum-draft-bar`, cấm khôi phục khối "Bài thi & Đánh giá" ở đáy trang soạn khóa học, cấm dùng màu tím `#1A1827` trong dark mode.
- **Impeccable UI Compliance**: Tỷ lệ padding nút 2:1, bo góc lồng nhau chính xác, màu sắc tương phản WCAG AA >= 4.5:1, không dùng Pure Black/White.

## Review Focus

1. **Lỗi góc nhìn học viên (`les is not defined`):** Học viên chưa ghi danh bấm vào xem trước bài giảng trong đề cương khóa học phải tải thông tin bài học mượt mà mà không gặp lỗi JavaScript.
2. **Khóa mở bài thi tuần tự:** Khi học viên chưa học xong các bài trong chương, mục "Bài kiểm tra" của chương đó phải ở trạng thái khóa (hiển thị biểu tượng ổ khóa và tooltip giải thích); chỉ khi hoàn thành bài cuối cùng thì bài kiểm tra mới tự động mở khóa.
3. **Modal xem chi tiết thay đổi Before/After:** Khi giảng viên bấm "Xem thay đổi", modal phải liệt kê cụ thể các thay đổi thực tế (Tiêu đề cũ -> mới, tóm tắt, số khối nội dung thay đổi, số câu hỏi thay đổi) thay vì chỉ hiện dòng thông báo chung chung "Đã sửa Chương 1".
4. **Mini-quiz dạng phân trang Coursera:** Khi bài giảng có từ 2 câu hỏi trở lên, giao diện phải tách từng câu riêng biệt dạng slide, có nút "Quay lại" / "Tiếp theo". Khi nộp bài nếu trượt điểm chuẩn (ví dụ < 80%), hệ thống không được để lộ đáp án đúng mà chỉ thông báo điểm và cung cấp nút "Làm lại từ đầu" đưa học sinh về Câu 1.
5. **Kéo thả Bạch tuộc AI:** Nút Bạch tuộc AI góc dưới màn hình có thể dùng chuột kéo thả di chuyển tới bất kỳ vị trí mong muốn nào mà không bị giật lag, không bay ra ngoài mép màn hình, và lưu lại tọa độ vị trí.

---

### Task 1: Sửa Lỗi Góc Nhìn Học Viên & Xây Dựng Logic Mở Khóa Bài Kiểm Tra Trong Cây Bài Học

**Files:**
- Modify: `frontend/assets/js/views/student.js:2540-2565,1435-1510`
- Test: `tests/frontend/student_preview_and_gating.test.js` hoặc API test tương thích

**Interfaces:**
- Consumes: `activeItem.data`, `activeItem.type`, `lesson.progress.is_completed`, `assessment.open_at`, `assessment.close_at`
- Produces: 
  - Khắc phục triệt để lỗi `les is not defined` khi preview bài học chưa ghi danh.
  - Hàm kiểm tra mở khóa: `isUnitExamUnlocked(unit, studentProgress)` và `isFinalExamUnlocked(course, studentProgress)`.

- [ ] **Step 1: Viết test kiểm tra an toàn null khi render preview bài học chưa ghi danh**
- [ ] **Step 2: Sửa lỗi `les is not defined` trong `frontend/assets/js/views/student.js`**
  - Tại dòng 2551: Thay thế `les.summary || les.description` bằng `activeItem.data?.summary || activeItem.data?.description || course.description || '...'`.
- [ ] **Step 3: Xây dựng hàm kiểm tra điều kiện mở khóa bài kiểm tra**
  - Bài kiểm tra chương K: Kiểm tra toàn bộ bài học thuộc chương K đều có `is_completed === true`.
  - Final Test: Kiểm tra toàn bộ bài học của tất cả các chương trong khóa học đều có `is_completed === true`, đồng thời thời gian hiện tại nằm trong khoảng `open_at` đến `close_at` (nếu có cấu hình).
- [ ] **Step 4: Kiểm tra cú pháp JavaScript**
  `node --check frontend/assets/js/views/student.js`
- [ ] **Step 5: Commit**
  ```bash
  git add frontend/assets/js/views/student.js
  git commit -m "fix(student): resolve un-enrolled syllabus preview null reference and build exam gating logic"
  ```

---

### Task 2: Xóa Bỏ Thanh Nháp Dưới, Đặt Cặp Nút Duyệt Lên Header & Chi Tiết Hóa Modal Đối Chiếu Before/After

**Files:**
- Modify: `frontend/assets/js/views/instructor.js:2880-3000,3400-3458`
- Modify: `src/pwd301/services/lesson_service.py:3432-3665`
- Test: `tests/api/test_changeset_diff_details.py`

**Interfaces:**
- Consumes: `get_course_changeset_diff(actor, course_id)`
- Produces: 
  - Backend diff trả về cấu trúc chi tiết: `{ lesson_id, title, old_title, summary_changed, content_changed, blocks_diff, quiz_diff, ... }`.
  - Header khóa học chứa 2 nút chuẩn: `"Gửi duyệt cập nhật"` và `"Xem thay đổi"`.
  - Modal "Đối chiếu thay đổi giáo trình" hiển thị thẻ chi tiết Before/After cho từng bài học.

- [ ] **Step 1: Viết test backend kiểm tra chi tiết Before vs. After trong `get_course_changeset_diff`**
  ```python
  def test_get_course_changeset_diff_detailed_fields(client, instructor_token, course_with_draft_modifications):
      res = client.get(f"/instructor/courses/{course_with_draft_modifications.id}/changeset/diff", headers={"Authorization": f"Bearer {instructor_token}"})
      assert res.status_code == 200
      data = res.json["data"]
      modified = data["diff"]["modified_lessons"]
      assert len(modified) > 0
      assert "field_changes" in modified[0] or "old_title" in modified[0]
  ```
- [ ] **Step 2: Nâng cấp `get_course_changeset_diff` trong `src/pwd301/services/lesson_service.py`**
  - So sánh bài nháp với bài gốc (`orig = sess.get(Lesson, d.previous_lesson_id)`):
    + So sánh tiêu đề: `old_title` vs `new_title`.
    + So sánh tóm tắt: `old_summary` vs `new_summary`.
    + So sánh nội dung: số ký tự hoặc sự thay đổi của nội dung bài học.
    + So sánh số lượng câu hỏi trắc nghiệm nếu có `<!-- mini_quiz: [...] -->`.
- [ ] **Step 3: Chỉnh sửa frontend trong `frontend/assets/js/views/instructor.js`**
  - Xóa bỏ hoàn toàn khối `<!-- STICKY DRAFT ACTION BAR -->` (`#curriculum-draft-bar`, dòng 2901-2999).
  - Đổi nút `"Gửi duyệt đợt cập nhật"` ở trên header thành `"Gửi duyệt cập nhật"`.
  - Khi có bản nháp (`changesetStatus.has_changes`): Đặt nút `"Xem thay đổi"` nằm ngay cạnh nút `"Gửi duyệt cập nhật"` trên thanh tiêu đề.
  - Thiết kế lại Modal "Đối chiếu thay đổi giáo trình":
    + Thẻ bài học mới: Hiện huy hiệu "Mới tạo", tiêu đề, tóm tắt.
    + Thẻ bài học sửa: Hiện rõ từng mục thay đổi (Tiêu đề: `A` $\rightarrow$ `B`, Tóm tắt: đã sửa, Nội dung bài giảng: đã cập nhật, Câu hỏi ôn tập: X câu).
    + Thẻ bài học xóa: Hiện huy hiệu "Đánh dấu xóa", tên bài học gạch ngang.
- [ ] **Step 4: Chạy test backend và kiểm tra cú pháp JS**
  ```bash
  pytest tests/api/test_changeset_diff_details.py -v
  node --check frontend/assets/js/views/instructor.js
  ```
- [ ] **Step 5: Commit**
  ```bash
  git add src/pwd301/services/lesson_service.py frontend/assets/js/views/instructor.js tests/api/test_changeset_diff_details.py
  git commit -m "feat(curriculum): consolidate update review buttons into header and enhance granular diff modal"
  ```

---

### Task 3: Nhúng Bài Kiểm Tra & Final Test Vào Cây Bài Học, Bãi Bỏ Khối Bài Thi Cũ

**Files:**
- Modify: `frontend/assets/js/views/instructor.js:950-1075,3065-3165`
- Modify: `frontend/assets/js/views/student.js:1430-1550,2300-2450`
- Test: `tests/frontend/curriculum_tree_exams.test.js`

**Interfaces:**
- Consumes: `currentUnits`, `assessments`, `course`
- Produces:
  - Loại bỏ hoàn toàn Section 2: "Bài thi & Đánh giá" khỏi giao diện soạn khóa học (`instructor.js`).
  - Trong cây bài học (cả Instructor và Student):
    * Cuối mỗi Chương có mục "Bài kiểm tra" riêng.
    * Đáy cây bài học có mục "Final Test" riêng.
  - Phía Giảng viên: Có nút "Tạo bài kiểm tra" ở từng chương và "Thiết lập Final Test" ở cuối cây.
  - Phía Học viên: Hiển thị trạng thái khóa/mở và liên kết làm bài.

- [ ] **Step 1: Xóa khối cũ trong `frontend/assets/js/views/instructor.js`**
  - Xóa bỏ Section 2: `<!-- SECTION 2: BÀI THI & KIỂM TRA -->` (dòng 3067-3165) và `#course-assessments-stack`.
- [ ] **Step 2: Thêm mục "Bài kiểm tra" vào cuối mỗi Chương trong cây bài học giảng viên**
  - Trong hàm `renderTree()`, ở cuối mỗi `.unit-tree-node`:
    + Tìm bài kiểm tra tương ứng với chương này (theo `assessment.learning_unit_id` hoặc bài kiểm tra thuộc chương).
    + Nếu đã có bài kiểm tra: Hiển thị card bài kiểm tra nhỏ gọn (Tiêu đề, số câu, thời lượng, nút Sửa đề thi / Bảng điểm).
    + Nếu chưa có bài kiểm tra: Hiển thị nút bấm viền nét đứt: `"+ Tạo bài kiểm tra cho chương này"`.
- [ ] **Step 3: Thêm khối "Final Test" vào đáy cây bài học giảng viên**
  - Ở dưới cùng của danh sách các Chương:
    + Thêm khối riêng biệt: `Final Test (Bài thi kết thúc môn)`.
    + Nếu đã có đề Final: Hiển thị thông tin đề thi, thời gian mở/đóng ca thi, nút Bảng điểm & Quản lý đề.
    + Nếu chưa có đề Final: Hiển thị nút `"+ Thiết lập Final Test"`.
- [ ] **Step 4: Đồng bộ hiển thị cây bài học ở góc nhìn học viên (`student.js`)**
  - Trong cây điều hướng học tập của học viên:
    + Mỗi chương hiển thị danh sách bài học, và mục cuối cùng là "Bài kiểm tra". Nếu chưa học xong các bài trong chương, hiển thị icon khóa kèm nhãn "Cần hoàn thành các bài học trong chương".
    + Ở cuối cây bài học toàn khóa: Hiển thị mục "Final Test". Nếu chưa hoàn thành 100% bài học hoặc chưa tới giờ thi, hiển thị icon khóa kèm chú thích điều kiện mở.
- [ ] **Step 5: Kiểm tra cú pháp JavaScript**
  ```bash
  node --check frontend/assets/js/views/instructor.js
  node --check frontend/assets/js/views/student.js
  ```
- [ ] **Step 6: Commit**
  ```bash
  git add frontend/assets/js/views/instructor.js frontend/assets/js/views/student.js
  git commit -m "feat(curriculum): embed chapter assessments and final test into tree and decommission standalone section"
  ```

---

### Task 4: Nâng Cấp Câu Hỏi Nhỏ Trong Bài (Mini-Quiz) Chuẩn Phân Trang Coursera & Điểm Chuẩn Đạt

**Files:**
- Modify: `frontend/assets/js/views/instructor.js:1800-1880,2100-2160`
- Modify: `frontend/assets/js/views/student.js:3000-3080,3550-3810`
- Test: `tests/frontend/coursera_quiz_pagination.test.js`

**Interfaces:**
- Consumes: `lesson.quiz` (array), `lesson.quiz_passing_percent`
- Produces:
  - Giảng viên cấu hình được % điểm đạt (mặc định 80%, dải 50% - 100%).
  - Học viên xem câu hỏi theo dạng slide từng câu (khi có >= 2 câu hỏi), có nút "Quay lại" / "Tiếp theo", chỉ số câu.
  - Chấm điểm: Nếu không đạt điểm chuẩn, không hiển thị đáp án đúng, hiện nút "Làm lại từ đầu" đưa về Câu 1.

- [ ] **Step 1: Bổ sung cấu hình Điểm chuẩn đạt trong Studio bài giảng (`instructor.js`)**
  - Trong khu vực câu hỏi ôn tập, bổ sung ô nhập: `Tỷ lệ đạt yêu cầu (%)` (mặc định 80, range 50 - 100).
  - Lưu giá trị này vào payload bài giảng khi bấm Lưu bài.
- [ ] **Step 2: Nâng cấp giao diện hiển thị Mini-Quiz phân trang trong `student.js`**
  - Nếu `lesson.quiz.length >= 2`:
    + Render container có thanh tiến trình / bước (Step pill indicators: `1`, `2`, ...).
    + Chỉ hiển thị 1 câu hỏi tại một thời điểm (`currentQuizIndex`).
    + Nút điều hướng: `Quay lại` (disabled ở câu 1) và `Tiếp theo` (ở các câu giữa).
    + Ở câu cuối cùng: Hiển thị nút `Kiểm tra đáp án / Nộp bài`.
  - Nếu `lesson.quiz.length === 1`: Giữ nguyên dạng 1 câu trực tiếp.
- [ ] **Step 3: Triển khai logic chấm điểm và làm lại từ đầu**
  - Tính điểm: `percent = (correctCount / totalQuestions) * 100`.
  - Ngưỡng đạt: `passingPercent = lesson.quiz_passing_percent || 80`.
  - Nếu `percent >= passingPercent`:
    + Báo "Chúc mừng! Bạn đã vượt qua bài ôn tập".
    + Hiển thị giải thích chi tiết cho từng câu.
    + Đánh dấu bài học hoàn thành (`setLessonCompleted()`).
  - Nếu `percent < passingPercent`:
    + Báo "Chưa đạt: Bạn trả lời đúng X/Y câu (Z%). Cần tối thiểu [passingPercent]% để vượt qua bài học".
    + KHÔNG hiển thị đáp án đúng hay giải thích chi tiết.
    + Hiển thị nút `"Làm lại từ đầu"`: khi bấm, xóa toàn bộ câu trả lời, reset về Câu 1 (`currentQuizIndex = 0`) để học sinh làm lại.
- [ ] **Step 4: Kiểm tra cú pháp JavaScript**
  ```bash
  node --check frontend/assets/js/views/instructor.js
  node --check frontend/assets/js/views/student.js
  ```
- [ ] **Step 5: Commit**
  ```bash
  git add frontend/assets/js/views/instructor.js frontend/assets/js/views/student.js
  git commit -m "feat(quiz): implement Coursera-style paginated mini-quiz with passing score gating and retry flow"
  ```

---

### Task 5: Chuẩn Hóa Bảng Màu Dark Mode & Kéo Thả Tự Do Bạch Tuộc AI

**Files:**
- Modify: `frontend/assets/js/views/instructor.js:964,2069,2074-2108`
- Modify: `frontend/index.html:715-725`
- Modify: `frontend/assets/js/ui.js:2200-2315`
- Test: Chrome DevTools visual verification

**Interfaces:**
- Consumes: Tailwind dark tokens, DOM mouse drag events
- Produces:
  - Triệt tiêu toàn bộ mã màu `#1A1827`, thay bằng `#18181b` / `#202020` / `#2E2D2B`.
  - Nút Bạch tuộc AI tiệp màu tối, có thể kéo thả di chuyển vị trí tự do trên màn hình (`mousedown`, `mousemove`, `mouseup`).

- [ ] **Step 1: Chuẩn hóa màu sắc Dark Mode trong `instructor.js`**
  - Đổi các class `dark:bg-[#1A1827]` ở `.unit-tree-node` thành `dark:bg-[#18181b]`.
  - Đổi nền thanh "THÊM NỘI DUNG" thành `dark:bg-[#18181b] border-[#E8E6DF] dark:border-[#2E2D2B]`.
  - Các nút `Bài học`, `Video`, `Tài liệu`, `Câu hỏi` dùng `dark:bg-[#202020] hover:dark:bg-[#262626] border-[#E8E6DF] dark:border-[#2E2D2B]`.
- [ ] **Step 2: Chuẩn hóa giao diện nút Bạch tuộc AI trong `frontend/index.html`**
  - Tại dòng 719: Đổi `dark:bg-[#EDEDEB] text-[#FAF9F5] dark:text-[#191919] border border-[#37352F] dark:border-[#FAF9F5]` thành `dark:bg-[#202020] text-white border border-[#E8E6DF] dark:border-[#3E3D3A] shadow-md`.
  - Đảm bảo không còn viền trắng hoặc nền trắng chói trong dark mode.
- [ ] **Step 3: Thêm tính năng kéo thả (Draggable) cho nút Bạch tuộc AI**
  - Trong `frontend/assets/js/ui.js`:
    + Lắng nghe sự kiện kéo chuột trên launcher button `#floating-ai-launcher`.
    + Khi kéo (drag): Cập nhật vị trí `left` / `top` (hoặc `right` / `bottom`) theo con trỏ chuột, giới hạn không cho bay ra ngoài viewport (`clamp`).
    + Phân biệt giữa hành động nhấp chuột (click để mở cửa sổ chat) và thao tác kéo thả (drag di chuyển).
    + Lưu vị trí cuối cùng vào `localStorage.setItem('pwd301_ai_button_pos', ...)` để duy trì vị trí khi reload trang.
- [ ] **Step 4: Kiểm tra cú pháp JavaScript**
  ```bash
  node --check frontend/assets/js/views/instructor.js
  node --check frontend/assets/js/ui.js
  ```
- [ ] **Step 5: Commit**
  ```bash
  git add frontend/assets/js/views/instructor.js frontend/index.html frontend/assets/js/ui.js
  git commit -m "feat(ui): standardize dark mode palette and enable draggable positioning for AI assistant launcher"
  ```

---

### Task 6: Kiểm Thử Toàn Diện, Linter, Pytest & Xác Minh Trực Quan Trình Duyệt

**Files:**
- Test: Toàn bộ test suite liên quan và scripts kiểm tra tĩnh

- [ ] **Step 1: Chạy kiểm tra tĩnh repo contract và syntax**
  ```powershell
  python scripts/repo_check.py
  ruff check src/ tests/
  node --check frontend/assets/js/views/instructor.js
  node --check frontend/assets/js/views/student.js
  node --check frontend/assets/js/ui.js
  ```
- [ ] **Step 2: Chạy kiểm thử tự động pytest**
  ```powershell
  pytest tests/api/test_lesson_api.py tests/api/test_course_workflow.py tests/api/test_assessment_api.py -v
  ```
- [ ] **Step 3: Khởi chạy server và xác minh trực quan qua Chrome DevTools MCP**
  - Kiểm tra xem trước bài học ở góc nhìn học viên không còn lỗi `les is not defined`.
  - Kiểm tra nút "Gửi duyệt cập nhật" và "Xem thay đổi" trên header.
  - Mở modal xem thay đổi kiểm tra bảng Before/After chi tiết.
  - Kiểm tra màu sắc Dark Mode ở thanh công cụ và danh sách chương.
  - Thao tác kéo thả nút Bạch tuộc AI di chuyển trên màn hình.
  - Làm thử mini-quiz phân trang từng câu và test cơ chế trượt làm lại từ đầu.
  - Kiểm tra khóa/mở bài kiểm tra theo tiến độ học chương và giờ thi Final Test.
- [ ] **Step 4: Báo cáo kết quả kiểm thử thực nghiệm**
