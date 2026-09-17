# Thiết kế Kỹ thuật: Khắc phục Điểm yếu Backend & Đồng bộ Hợp đồng 100% Frontend-Backend (Full Parity)

- **Ngày ban hành:** 2026-09-17
- **Tác giả:** Principal Systems Architect & Lead Fullstack Systems Engineer
- **Trạng thái:** BẢN THẢO CHỜ PHÊ DUYỆT (SPECIFICATION REVIEW)
- **Tài liệu nguồn kiểm chiếu (Source of Truth):**
  - `docs/system/PWD301_SYSTEM_SPECIFICATION/`
  - `docs/database/PWD301_DATABASE_ARCHITECTURE/`
  - `AGENTS.md` (Operational Contract & Invariants)

---

## 1. Mục tiêu & Bối cảnh (Problem Statement & Scope)

Hệ thống Single-DOM SPA của PWD301 đã chuyển đổi sang kiến trúc thuần Headless Backend phục vụ API JSON envelopes. Tuy nhiên, qua quá trình rà soát và phỏng vấn trực tiếp (`/grill-me`), phát hiện 4 nhóm yếu điểm lớn giữa Backend và Frontend:
1. **Lỗi kết nối "lệch" (Mismatched contracts & undefined API calls)**:
   - `ApiClient.getEnrolledCourses()` được gọi tại `frontend/assets/js/views/student.js:3149` nhưng không tồn tại trong `api.js` (gây lỗi `TypeError` khi nạp môn học vào Context Selector của Trợ lý AI Gemini).
   - `ApiClient.getCourses()` được gọi tại `controllers.js:135` nhưng không có trong `api.js`.
   - `router.js` điều hướng sidebar Admin với `tab=courses` và `tab=applications`, nhưng `AdminView.renderGovernance` chỉ xử lý `tab-users`, `tab-review`, `tab-reassign`, `tab-security` khiến việc nhấp menu không mở đúng tab/hàng đợi mong muốn.
2. **Dữ liệu mẫu (Mock data) còn sót lại trong giao diện**:
   - `InstructorView.renderExtendedQuestionStudio` còn chứa 4 câu hỏi trắc nghiệm/code cứng (`PWD301-Q-024`, `PWD301-Q-018`, `PWD301-Q-035`, `PWD301-Q-041`) và các chỉ số giả (`discrimination_index`, `facility_value`).
   - `InstructorView.renderTabReviews` chứa đánh giá 5 sao và nhận xét sinh viên giả lập, trong khi CSDL chuẩn PWD301 không thiết kế bảng lưu review khóa học.
3. **Chức năng Backend đã có nhưng Frontend chưa kết nối**:
   - Quản lý Điều kiện tiên quyết (`GET/POST /instructor/courses/<course_id>/prerequisites` & `DELETE .../<prereq_id>`).
   - Quản lý Quy chuẩn hoàn thành khóa học (`GET/POST/PUT /instructor/courses/<course_id>/completion-rules`).
   - Quản lý Vòng đời câu hỏi trong Ngân hàng câu hỏi: Chỉnh sửa tạo revision mới (`POST /questions/<question_id>/revisions`), xem lịch sử sửa đổi (`GET /questions/<question_id>/revisions`), và chuyển vào thùng rác/khôi phục (`POST /questions/<question_id>/trash` & `POST /questions/<question_id>/restore`).
4. **Lỗi ghi đè nội dung trong Trình soạn thảo bài giảng (Lesson Authoring Studio)**:
   - Khi chỉnh sửa bài giảng hiện có, `authoringBlocks` giữ nguyên 3 khối mặc định thay vì phân tích cú pháp từ `markdown_content`. Khi lưu, `serializeBlocksToMarkdown()` làm mất sạch nội dung gốc của bài giảng.
   - Khối tài nguyên chỉ nhập tên tệp tĩnh thay vì cho phép tải tệp thực và quét mã độc qua ClamAV (`POST .../resources`).

---

## 2. Kiến trúc Giải pháp Chi tiết (Detailed Architecture)

### 2.1. Chuẩn hóa Tầng API Client (`frontend/assets/js/api.js`)
Bổ sung đầy đủ 100% các phương thức bị thiếu, bảo đảm CSRF token tự động và xử lý lỗi đồng nhất:
- `ApiClient.getEnrolledCourses()`: Alias chuẩn hóa trỏ tới `/student/my-learning` (hoặc `/student/enrollments`).
- `ApiClient.getCourses(params)`: Alias chuẩn hóa trỏ tới `getCatalogCourses(params)`.
- **Prerequisites Management**:
  - `ApiClient.getCoursePrerequisites(courseId)`: `GET /instructor/courses/${courseId}/prerequisites`
  - `ApiClient.addCoursePrerequisite(courseId, data)`: `POST /instructor/courses/${courseId}/prerequisites` (body: `{ required_course_id, min_grade_point, reason }`)
  - `ApiClient.deleteCoursePrerequisite(courseId, prereqId)`: `DELETE /instructor/courses/${courseId}/prerequisites/${prereqId}`
- **Completion Rules Management**:
  - `ApiClient.getCourseCompletionRules(courseId)`: `GET /instructor/courses/${courseId}/completion-rules`
  - `ApiClient.updateCourseCompletionRules(courseId, data)`: `POST /instructor/courses/${courseId}/completion-rules`
- **Question Lifecycle & Revision Management**:
  - `ApiClient.getQuestionDetail(questionId)`: `GET /instructor/questions/${questionId}`
  - `ApiClient.updateQuestion(questionId, data)`: `PATCH /instructor/questions/${questionId}`
  - `ApiClient.trashQuestion(questionId, reason = '')`: `POST /instructor/questions/${questionId}/trash`
  - `ApiClient.restoreQuestion(questionId)`: `POST /instructor/questions/${questionId}/restore`
  - `ApiClient.getQuestionRevisions(questionId)`: `GET /instructor/questions/${questionId}/revisions`
  - `ApiClient.createQuestionRevision(questionId, data)`: `POST /instructor/questions/${questionId}/revisions`

### 2.2. Hồ sơ Học vụ & Quản lý Đề cương Khóa học (`renderTabAcademic` & `renderTabReviews`)
1. **Loại bỏ triệt để Tab "Reviews"**:
   - Xóa bỏ nút Tab `Reviews` và phương thức `renderTabReviews`.
   - Bảo đảm tuân thủ nguyên tắc tối giản (YAGNI) và khớp 100% với kiến trúc CSDL SQL Server.
2. **Tái cấu trúc Tab "Hồ sơ Học vụ" (`renderTabAcademic`) thành 3 khối thẻ thống nhất**:
   - **Khối 1: Chuẩn đầu ra môn học (ABET SLOs)**:
     - Hiển thị danh sách SLOs hiện có từ `course.learning_objectives`.
     - Cho phép Giảng viên thêm mới, chỉnh sửa và xóa từng SLO trực tiếp trên giao diện.
     - Lưu cập nhật thông qua `ApiClient.updateCourse(courseId, { learning_objectives: [...] })`.
   - **Khối 2: Ma trận Điều kiện Tiên quyết (Prerequisites)**:
     - Tải danh sách điều kiện tiên quyết thực tế qua `ApiClient.getCoursePrerequisites(courseId)`.
     - Modal thêm môn tiên quyết: Chọn từ danh sách môn học của trường (`ApiClient.getInstructorCourses()` hoặc Catalog), thiết lập điểm GPA/grade point tối thiểu (thang điểm 4.0/10.0), ghi rõ căn cứ học vụ.
     - Nút xóa điều kiện tiên quyết gọi `ApiClient.deleteCoursePrerequisite(courseId, prereqId)`.
   - **Khối 3: Quy chuẩn Hoàn thành Khóa học (Completion Rules)**:
     - Tải quy tắc hiện hành qua `ApiClient.getCourseCompletionRules(courseId)`.
     - Form cấu hình trực quan: % Chuyên cần tối thiểu (`min_attendance_percent`), Điểm trung bình khảo thí tối thiểu (`min_assessment_score`), Bắt buộc hoàn thành bài thi cuối kỳ (`require_final_exam`).
     - Nút lưu cấu hình gửi tới `ApiClient.updateCourseCompletionRules(courseId, data)`.

### 2.3. Ngân hàng Câu hỏi Nâng cao Live 100% (`renderExtendedQuestionStudio`)
1. **Loại bỏ hoàn toàn 4 câu hỏi mẫu hardcode**:
   - Dữ liệu câu hỏi được truy vấn 100% từ `ApiClient.getQuestions(courseId, { per_page: 100 })`.
   - Khi chưa có câu hỏi trong CSDL, hiển thị Empty State chuẩn với 3 hành động: Tạo câu hỏi thủ công, Dùng AI Gemini soạn câu hỏi theo chuẩn Bloom, hoặc Soạn đề Azota.
2. **Ngăn kéo Lịch sử Phiên bản (Revision Drawer)**:
   - Thêm nút "Lịch sử sửa đổi" trên mỗi thẻ câu hỏi.
   - Mở Drawer bên phải tải toàn bộ danh sách `QuestionRevision` qua `ApiClient.getQuestionRevisions(questionId)`.
   - Hiển thị mốc thời gian, người cập nhật, số thứ tự revision và nội dung đối chiếu.
3. **Thao tác Thùng rác & Khôi phục (Trash / Restore)**:
   - Thêm nút chuyển vào thùng rác gọi `ApiClient.trashQuestion(questionId, 'Giảng viên lưu trữ')`.
   - Bộ lọc trạng thái câu hỏi: Tất cả / Sẵn sàng (Active) / Đã lưu trữ (Trash).
   - Với câu hỏi trong thùng rác: Hiển thị nút "Khôi phục" gọi `ApiClient.restoreQuestion(questionId)`.
4. **Chỉnh sửa câu hỏi (Edit Question Modal)**:
   - Mở modal điền sẵn dữ liệu hiện tại của câu hỏi (Stem, Choices, Difficulty, Points, Explanation).
   - Khi lưu, tạo `QuestionRevision` mới thông qua `ApiClient.createQuestionRevision(questionId, payload)` bảo đảm bất biến lịch sử khảo thí theo quy chuẩn ABET.

### 2.4. Khắc phục Trình soạn thảo Bài giảng (Lesson Authoring Studio)
1. **Đồng bộ 2 chiều (Bidirectional Sync: Markdown <-> Blocks)**:
   - Xây dựng bộ phân tích cú pháp Markdown sang Blocks (`parseMarkdownToBlocks(markdown)`):
     - Nhận diện các thẻ đề mục (`## Heading` -> Paragraph Block).
     - Nhận diện các thẻ trích dẫn (`> [!NOTE]` / `> [!TIP]` -> Callout Block).
     - Nhận diện câu hỏi trắc nghiệm giữa bài (`### [Kiểm tra nhanh]` -> Quiz Block).
     - Nhận diện tệp đính kèm (`✓ **Tệp đính kèm**:` -> Resource Block).
   - Khi nạp bài giảng có sẵn (`lessonId`): Phân tích cú pháp `markdown_content` vào `authoringBlocks` thay vì dùng 3 khối mặc định.
   - Khi chuyển từ Chế độ Nâng cao (Markdown) sang Chế độ Cơ bản (Blocks): Phân tích tự động nội dung textarea vào `authoringBlocks`.
   - Khi chuyển từ Chế độ Cơ bản sang Chế độ Nâng cao hoặc khi Lưu: Serialize `authoringBlocks` thành Markdown chuẩn.
2. **Đính kèm Tệp Tài liệu Thật qua ClamAV**:
   - Khối tài nguyên cho phép chọn tệp từ máy tính (`<input type="file">`).
   - Tải tệp lên qua `ApiClient.attachLessonResource(courseId, lessonId, formData)` với quét virus ClamAV tự động.

### 2.5. Khắc phục Lệch Routing Quản trị viên (`Admin Governance Navigation`)
- Cập nhật `AdminView.renderGovernance(container, activeTab)` để xử lý mượt mà:
  - Nếu `activeTab === 'courses'` -> Tự động kích hoạt `tab-review` và chọn phân khúc Hàng đợi Khóa học.
  - Nếu `activeTab === 'applications'` -> Tự động kích hoạt `tab-review` và chọn phân khúc Hàng đợi Ứng tuyển Giảng viên.
  - Nếu `activeTab === 'users'` -> Kích hoạt `tab-users`.
  - Nếu `activeTab === 'reassign'` -> Kích hoạt `tab-reassign`.
  - If `activeTab === 'security'` -> Kích hoạt `tab-security`.

---

## 3. Kế hoạch Kiểm thử & Xác minh (Verification Plan)

### 3.1. Bài kiểm thử Tự động (Automated Integration Tests)
Tạo tệp kiểm thử `tests/api/test_backend_frontend_parity.py` bao quát 100%:
- Kiểm thử các phương thức mới trong `frontend/assets/js/api.js`.
- Kiểm thử luồng Prerequisites API (Tạo, Lấy danh sách, Xóa điều kiện tiên quyết).
- Kiểm thử luồng Completion Rules API (Lấy cấu hình, Cập nhật cấu hình).
- Kiểm thử luồng Question Revision, Trash, và Restore API.
- Kiểm thử tính toàn vẹn của Frontend JavaScript (`node --check` trên toàn bộ tệp assets/js).

### 3.2. Chạy Toàn bộ Bộ công cụ Kiểm thử Dự án
- `ruff check src/ tests/`
- `ruff format --check src/ tests/`
- `mypy src/`
- `pytest tests/api/test_backend_frontend_parity.py`
- Tổng kiểm tra `./scripts/verify.ps1` (hoặc lệnh pytest liên quan).

### 3.3. Kiểm thử Trực quan trên Trình duyệt (Chrome DevTools)
- Đăng nhập quyền Giảng viên: Kiểm tra Course Manage (Tab Academic: SLOs CRUD, Prerequisites, Completion Rules; xác nhận Tab Reviews đã ẩn).
- Kiểm tra Ngân hàng câu hỏi: Xác nhận không còn 4 câu hỏi hardcode, kiểm tra mở Revision Drawer và xóa/khôi phục câu hỏi.
- Kiểm tra Lesson Studio: Mở bài giảng có sẵn, kiểm tra nội dung bài giảng không bị đè bởi khối mặc định.
- Đăng nhập quyền Admin: Nhấp các menu sidebar (Kiểm duyệt Khóa học, Hồ sơ Giảng viên) xác nhận chuyển đúng tab.
