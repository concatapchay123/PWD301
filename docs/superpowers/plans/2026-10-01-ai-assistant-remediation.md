# Kế hoạch Khắc phục Triệt để Hệ thống Trợ lý AI (Octopus AI Assistant) — PWD301

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Trang bị "bộ não" tri thức thực thụ cho Trợ lý AI Bạch tuộc bằng cách tích hợp trực tiếp dữ liệu bài học (Lesson Markdown), tri thức RAG (Knowledge Chunks) và Engine gợi ý khóa học (Algorithm 14) vào luồng Chatbot, đồng thời sửa toàn bộ lỗi runtime và trải nghiệm trên Frontend.

**Architecture:** Kiến trúc Pure Headless REST API kết hợp Orchestrator tiêm ngữ cảnh (Context Injection) và RAG Scoped Retrieval. Giao diện Frontend Web SPA sử dụng session authentication kết nối đồng bộ giữa màn hình học bài (NetAcad Console), trang xem kết quả thi (Review Modal) và trang khám phá khóa học (Dashboard & Catalog Recommendations).

**Tech Stack:** Python 3.12, Flask, SQLAlchemy, SQL Server (DATETIME2(3), UUID ADR-002), Google Gemini 3.8 Flash, Vanilla ES6+ SPA (Tailwind CSS, Material Symbols).

**Spec:** `docs/system/PWD301_SYSTEM_SPECIFICATION/business/13_AI_GEMINI_RAG.md`, `docs/system/PWD301_SYSTEM_SPECIFICATION/algorithms/14_COURSE_RECOMMENDATION_RULES.md`, `docs/system/PWD301_SYSTEM_SPECIFICATION/api/10_AI_API.md`, và [ai_assistant_deep_audit_report.md](file:///C:/Users/LENOVO/.gemini/antigravity/brain/9cdd2bec-e650-4eac-a830-da08de8996f6/ai_assistant_deep_audit_report.md).

## Global Constraints

- PWD301 là Backend REST API thuần túy (Pure Headless); nghiêm cấm tạo lại template Jinja (`*.html` trong `src/pwd301/templates/`) hoặc mock preview.
- Tuân thủ ADR-002 Zero Internal PK Leakage: Mọi API ra ngoài đều dùng public UUID; cấm để lộ internal BIGINT ID.
- Nguyên tắc Fail-Closed cho tệp tin: Chỉ tài liệu sạch (`status == "ACTIVE"`, scan pass) mới được nạp vào RAG.
- 5-Minute Inactivity Lifecycle (AI-003): Các phiên hội thoại tự động hết hạn và giải phóng nội dung sau 300 giây không hoạt động.
- Trợ lý AI chỉ mang danh xưng duy nhất: **Bạch tuộc trợ lí AI** (Octopus AI Assistant). Xưng hô "mình", gọi người dùng là "bạn". Không nhận là "AI của môn PWD301".
- Web SPA dùng Session Authentication; REST API ngoài dùng JWT Bearer. Không lưu JWT trong `localStorage`.
- TDD Iron Law: Viết test fail trước khi viết code sản phẩm; kiểm thử thực nghiệm trước khi công bố hoàn thành.

## Review Focus

1. `context_type == "LESSON"`: Đảm bảo toàn bộ nội dung bài giảng Markdown được tiêm an toàn vào prompt mà không làm tràn context window của LLM.
2. `context_type == "COURSE"`: Đảm bảo `retrieve_relevant_chunks()` lọc đúng quyền truy cập (sinh viên phải ghi danh active mới được RAG giáo trình của môn).
3. `context_type == "GLOBAL"`: Đảm bảo khi sinh viên hỏi gợi ý khóa học, engine Algorithm 14 lấy dữ liệu khóa học thật từ CSDL, không để LLM hallucinate môn học ảo.
4. Lỗi runtime `FloatingAITutor`: Đảm bảo modal giải thích câu hỏi bài thi hiển thị mượt mà, truyền đúng câu hỏi và đáp án đã chọn/đáp án đúng mà không bị lỗi JavaScript.
5. Scope Classifier: Đảm bảo sinh viên hỏi các câu hỏi học tập có từ "vai trò", "thông tin tài khoản", "đáp án" không bị chặn oan uổng, trong khi các đòn tấn công Prompt Injection/SQLi thật vẫn bị chặn 100%.

---

## Task Structure

### Task 1: Sửa lỗi Fatal Bug `FloatingAITutor` trên Frontend & Tích hợp Modal Giải thích Câu hỏi Bài thi

**Files:**
- Modify: `frontend/assets/js/views/student.js:5036-5050`
- Modify: `frontend/assets/js/ui.js`
- Test: Kiểm tra click nút "Hỏi Bạch tuộc câu này" trên trang kết quả bài thi qua trình duyệt / script kiểm tra DOM.

**Steps:**
- [ ] 1.1: Tạo class / helper `FloatingAITutor` trong `frontend/assets/js/views/student.js` (hoặc `ui.js`) cung cấp phương thức `openWithQuestion(prompt, context = {})`.
- [ ] 1.2: Thiết kế giao diện Modal nổi (Slide-over drawer hoặc Modal Popup) hiển thị biểu tượng Bạch tuộc AI, nội dung câu hỏi thi đang xem xét, và khung chat kết nối trực tiếp đến `ApiClient.sendAIChat()`.
- [ ] 1.3: Gắn `FloatingAITutor.openWithQuestion()` vào sự kiện click của các nút `.ask-ai-question-btn` trong `renderAssessmentResults`.
- [ ] 1.4: Xử lý trạng thái gửi tin nhắn, typing animation và render phản hồi Markdown chuẩn xác có hỗ trợ KaTeX/công thức toán.
- [ ] 1.5: Xác minh trong trình duyệt: Nút bấm mở modal mượt mà, không còn lỗi `ReferenceError: FloatingAITutor is not defined`.

---

### Task 2: Tích hợp Trợ lý AI trực tiếp vào Không gian Học bài NetAcad (`renderCourseConsole`)

**Files:**
- Modify: `frontend/assets/js/views/student.js:1460-1550` (Header tabs và panel container)
- Modify: `frontend/assets/js/views/student.js:2100-2400` (Sync active lesson ID sang tab AI)

**Steps:**
- [ ] 2.1: Thêm nút Tab thứ 3 trên thanh điều hướng sidebar console: `tab-btn-ai` với icon `smart_toy` và nhãn `Bạch tuộc AI`.
- [ ] 2.2: Tạo panel giao diện `sidebar-panel-ai` nằm cạnh `sidebar-panel-outline` và `sidebar-panel-resources`.
- [ ] 2.3: Khi học viên chuyển giữa các bài giảng trong đề cương, tự động cập nhật `currentLessonId` và hiển thị huy hiệu bài học đang theo dõi (ví dụ: *"Đang hỗ trợ Bài 1.2: Cú pháp Python"*).
- [ ] 2.4: Tích hợp khung chat thu nhỏ (Compact Chat Stream) cho phép học viên đặt câu hỏi ngay tại chỗ, gửi kèm `course_id` và `lesson_id` tới endpoint `/student/ai/chat`.
- [ ] 2.5: Bổ sung các câu hỏi gợi ý nhanh theo nội dung bài học (Contextual Chips).
- [ ] 2.6: Kiểm tra chuyển đổi qua lại giữa các tab Đề cương, Tài liệu và AI mà không làm mất lịch sử hội thoại của bài học.

---

### Task 3: Kích hoạt Công cụ Gợi ý Khóa học (Algorithm 14) trên Frontend (Dashboard & Catalog)

**Files:**
- Modify: `src/pwd301/blueprints/student/routes.py` (Thêm endpoint session-based `GET /student/recommendations`)
- Modify: `frontend/assets/js/api.js` (Thêm method `ApiClient.getRecommendations(limit)`)
- Modify: `frontend/assets/js/views/student.js:155-215` (Dashboard Widget)
- Modify: `frontend/assets/js/views/student.js:574-650` (Catalog Top Section)
- Test: `tests/api/test_student_recommendations_endpoint.py`

**Steps:**
- [ ] 3.1: Viết test fail kiểm tra endpoint `GET /student/recommendations` yêu cầu đăng nhập sinh viên và trả về danh sách khóa học đề xuất kèm giải thích theo Algorithm 14.
- [ ] 3.2: Thêm route `GET /student/recommendations` vào `src/pwd301/blueprints/student/routes.py`, gọi hàm `generate_course_recommendations(actor=actor, limit=limit, session=db.session)` và trả về phong bì JSON chuẩn.
- [ ] 3.3: Thêm method `static async getRecommendations(limit = 4)` vào `frontend/assets/js/api.js`.
- [ ] 3.4: Bổ sung widget "Gợi ý lộ trình tiếp theo dành cho bạn" trên Dashboard sinh viên (`renderDashboard`), hiển thị các Course Card có badge độ khó, lý do đề xuất ("Phù hợp sau khi hoàn thành môn X") và nút "Xem chi tiết / Ghi danh".
- [ ] 3.5: Bổ sung section "Khóa học đề xuất cho bạn" nổi bật ở đầu trang Catalog (`renderCatalog`).
- [ ] 3.6: Chạy test xác nhận endpoint hoạt động và frontend render mượt mà.

---

### Task 4: Tinh chỉnh Bộ lọc Phạm vi & An toàn (Scope Classifier & Guardrails)

**Files:**
- Modify: `src/pwd301/services/scope_classifier.py:88-164` (Regex `_CONFIDENTIAL_SYSTEM_PATTERNS`)
- Modify: `src/pwd301/services/gemini_service.py:105-121` (Regex `_INJECTION_PATTERNS`)
- Modify: `src/pwd301/services/gemini_service.py:1107-1135` (Prompt nới lỏng code snippet)
- Test: `tests/unit/test_ai_scope_classifier.py` và `tests/security/test_ai_scope_enforcement.py`

**Steps:**
- [ ] 4.1: Viết test các câu hỏi học tập bị chặn nhầm trước đây (ví dụ: *"Học viên có vai trò gì trong đồ án?"*, *"Giải thích vì sao câu hỏi này đáp án đúng là C"*, *"Làm sao để đổi mật khẩu và thông tin tài khoản?"*). Đảm bảo test hiện tại fail (bị phân loại nhầm là vi phạm an ninh).
- [ ] 4.2: Tinh chỉnh Regex trong `_CONFIDENTIAL_SYSTEM_PATTERNS` để chỉ chặn các hành vi tấn công khai thác quyền (privilege escalation, xem danh sách user nội bộ khác, hack role admin), không chặn từ ngữ thảo luận học vụ thông thường.
- [ ] 4.3: Tinh chỉnh Regex trong `gemini_service.py` để không chặn câu hỏi giải thích đáp án bài thi khi học viên đang ôn tập.
- [ ] 4.4: Điều chỉnh System Prompt ở context GLOBAL: Cho phép viết các đoạn mã giải thích cú pháp cơ bản (ví dụ: vòng lặp, hàm, cấu trúc dữ liệu), chỉ từ chối khi có yêu cầu gia công toàn bộ dự án thương mại ngoài lề.
- [ ] 4.5: Chạy lại toàn bộ test suite security và classifier: Đảm bảo 112/112 test cũ vẫn pass và các test mới xác nhận không còn chặn nhầm.

---

### Task 5: Kết nối RAG Tri thức & Nội dung Bài học vào Luồng Chatbot Backend

**Files:**
- Modify: `src/pwd301/services/ai_service.py:650-862` ([`send_chat_message`](file:///e:/PWD301/src/pwd301/services/ai_service.py#L650-L862))
- Modify: `src/pwd301/services/gemini_service.py:1100-1175` ([`chat_response`](file:///e:/PWD301/src/pwd301/services/gemini_service.py#L1100-L1175))
- Test: `tests/unit/test_ai_chat_grounded.py`

**Steps:**
- [ ] 5.1: Viết test fail: Tạo cuộc hội thoại với `context_type: "LESSON"` và kiểm tra tin nhắn trả lời của AI có phản ánh nội dung kiến thức được định nghĩa trong bài học đó.
- [ ] 5.2: Viết test fail: Tạo cuộc hội thoại với `context_type: "COURSE"` và kiểm tra AI có tích hợp các đoạn trích dẫn `[Ref: chunk_id]` từ RAG của môn học.
- [ ] 5.3: Cập nhật hàm `send_chat_message()` trong `src/pwd301/services/ai_service.py`:
  - Khi `conv.context_type == "LESSON"`: Tải `lesson = sess.query(Lesson).get(conv.lesson_id)`. Trích xuất tiêu đề, tóm tắt và nội dung `lesson.markdown_content` đưa vào ngữ cảnh an toàn.
  - Khi `conv.context_type == "COURSE"`: Gọi `retrieve_relevant_chunks(actor=actor, course_id=conv.course.public_id, query_text=sanitized_content, top_k=3, session=sess)`. Nạp các chunk vào thẻ `<retrieved_context>` chuẩn an toàn `SEC-006` và lưu `AISourceUsage`.
  - Khi `conv.context_type == "GLOBAL"`: Nạp danh mục các khóa học đang mở và gọi `generate_course_recommendations` nếu câu hỏi có ý định tư vấn học tập.
- [ ] 5.4: Cập nhật `chat_response()` trong `gemini_service.py` để phân tách rõ ràng giữa Chỉ thị hệ thống, Dữ liệu ngữ cảnh giáo trình (Evidence) và Lịch sử hội thoại của học viên.
- [ ] 5.5: Chạy test unit và integration để xác nhận: AI trả lời dựa trên tài liệu bài học thực tế và có trích dẫn nguồn.

---

### Task 6: Kiểm thử Hồi quy Toàn diện (End-to-End Regression & Verification)

**Files:**
- Run: `./scripts/verify.ps1` hoặc chạy độc lập các test suites:
  - `tests/unit/test_ai_service.py`
  - `tests/unit/test_ai_scope_classifier.py`
  - `tests/security/test_ai_scope_enforcement.py`
  - `tests/security/test_ai_course_authorization.py`
  - `tests/api/test_ai_api.py`

**Steps:**
- [ ] 6.1: Chạy toàn bộ test suites liên quan đến AI và RAG để bảo đảm không xảy ra bất kỳ lỗi hồi quy nào.
- [ ] 6.2: Kiểm tra tuân thủ bất biến kiến trúc Headless (không có template Jinja, không có preview giả lập).
- [ ] 6.3: Kiểm tra tuân thủ ADR-002: Không lộ ID BigInt trong bất kỳ response JSON nào.
- [ ] 6.4: Xác minh thực nghiệm trên trình duyệt: Luồng học bài -> Mở tab AI hỏi bài -> Xem bài thi -> Bấm hỏi Bạch tuộc -> Xem gợi ý khóa học trên Dashboard.
