# TASK-077 — AI Assistant Cognitive Grounding, Memory Pruning, Automated RAG & Context Isolation Remediation

**Status:** DONE  
**Assignee:** Principal Systems Architect & Senior Full-Stack Engineer  
**Started Date:** 2026-10-01  
**Completed Date:** 2026-10-01  

---

## 1. Goal & Architectural Resolution Summary

Khắc phục triệt để và toàn diện toàn bộ 13 điểm khiếm khuyết được phát hiện của hệ thống AI Assistant ("Bạch tuộc trợ lí AI" / Octopus AI Assistant), bộ nhớ đệm hội thoại, quy trình nạp RAG và giao diện người dùng:

1. **Course Syllabus Grounding & Public Catalog Inquiries (Khắc phục "Mù Đề cương" & 403 Block)**:
   - Trước đây, khi học viên hỏi về một khóa học, AI chỉ nhận được `Context: COURSE, Course: <Title>` mà không có thông tin chi tiết về môn học, dẫn đến việc AI trả lời mơ hồ hoặc từ chối hỗ trợ.
   - Thêm `_build_course_outline_context(course)` trong `src/pwd301/services/ai_service.py` để trích xuất và nạp cấu trúc đề cương hoàn chỉnh: Mã môn, Tên môn, Danh mục, Cấp độ, Mô tả, Chuẩn đầu ra (SLO), và Cấu trúc các Chương/Bài học vào thẻ `<course_syllabus_outline>`.
   - Cập nhật `src/pwd301/blueprints/student/routes.py`: Cho phép học viên chưa ghi danh có thể trao đổi với AI về đề cương môn học công khai (`PUBLISHED`) từ Catalog mà không bị chặn bởi HTTP 403 `FORBIDDEN_NOT_ENROLLED`, trong khi vẫn bảo vệ nghiêm ngặt các bài giảng riêng tư và tài liệu RAG chi tiết.

2. **Tách biệt Kiến trúc Prompt & Bảo toàn Gợi ý Toàn cục (Prompt Architecture Separation)**:
   - Loại bỏ hoàn toàn việc nhồi nhét ngữ cảnh vào tiêu đề chỉ dẫn hệ thống `VAI TRÒ TRONG KHÓA HỌC / BÀI HỌC ({context})`.
   - Tách biệt rõ ràng giữa System Instruction tĩnh (Persona, Guardrails, Scope Policy) và Dữ liệu tham chiếu động được bọc trong khối thẻ `<reference_context>`.
   - Đảm bảo các đề xuất khóa học theo Algorithm 14 trên trang chính (`GLOBAL`) luôn được chuyển giao nguyên vẹn vào `<reference_context>` cho mô hình Gemini.

3. **Cơ chế Cửa sổ Trượt (Sliding Window), Khử Trùng Lặp & Cách ly Từ chối (Refusal Isolation)**:
   - Triệt tiêu hiện tượng "bãi rác thông tin" bằng cửa sổ trượt giới hạn tối đa 6 lượt hội thoại gần nhất (tối đa 12 tin nhắn).
   - Xây dựng bộ lọc `_is_refusal_content` loại bỏ các phản hồi từ chối an ninh/ngoài phạm vi và câu hỏi kích hoạt chúng khỏi bộ nhớ gửi cho LLM, ngăn chặn persona drift và vòng lặp từ chối.
   - Sửa lỗi Double-Append: Tin nhắn người dùng hiện tại chỉ được bổ sung duy nhất 1 lần ở cuối mảng lịch sử.

4. **Khắc phục Zombie Session Resurrection & Cách ly Ngữ cảnh Điều hướng**:
   - Khi client gửi `conversation_id: null` (hoặc chuỗi rỗng), backend chủ động xóa `session.pop("active_ai_conversation_id")` và khởi tạo phiên hội thoại mới tinh, không tái sinh phiên cũ từ cookie.
   - Khi người dùng chuyển sang khóa học hoặc bài học khác (`course_id` hoặc `lesson_id` thay đổi), phiên hội thoại tự động được làm mới để tránh rò rỉ ngữ cảnh (Context Bleed).

5. **Đường ống Nạp Tri thức RAG Tự động theo Vòng đời Nội dung (Automated RAG Pipeline)**:
   - Hiện thực hóa `auto_ingest_lesson_content` và `auto_ingest_course_materials` trong `src/pwd301/services/rag_service.py`.
   - Tự động kích hoạt nạp chunk tri thức vào RAG Knowledge Fortress khi:
     - Bài học được tạo hoặc cập nhật với trạng thái `PUBLISHED` (`create_lesson`, `update_lesson` trong `lesson_service.py`).
     - Khóa học được chuyển sang trạng thái `PUBLISHED` (`change_course_status` trong `course_service.py`).

6. **Sửa lỗi Phân tích Phản hồi AI trên NetAcad Learning Console**:
   - Cập nhật bộ bóc tách tin nhắn tại `frontend/assets/js/views/student.js:1895`: Bổ sung `res?.reply` và `res?.data?.reply` vào chuỗi fallback đa cấp, sửa lỗi luôn hiển thị "Xin lỗi bạn, mình chưa thể xử lý yêu cầu lúc này".
   - Nút "Làm mới hội thoại" (`#console-ai-new-chat-btn`) đặt `consoleConvId = null` và hiển thị thông báo toast xác nhận.

7. **Nâng cấp Floating AI Tutor & Khôi phục Tuyến đường Trợ lý AI**:
   - Thêm nút "Làm mới cuộc trò chuyện" (`#floating-ai-reset-btn`) trên thanh tiêu đề của Floating AI Drawer (`frontend/index.html` và `frontend/assets/js/ui.js`).
   - Tự động làm mới `FloatingAITutor.conversationId = null` khi chuyển đổi khóa học trong `openWithQuestion(prompt, courseId)`.
   - Cập nhật `frontend/assets/js/router.js`: Khôi phục route `#/student/ai-assistant` để hiển thị trang chuyên biệt `StudentView.renderAIAssistant`, chấm dứt việc tự động chuyển hướng về Dashboard.

---

## 2. Chi tiết Thay đổi Tệp tin

| Tệp tin | Loại thay đổi | Mô tả chi tiết |
|---|---|---|
| `src/pwd301/services/ai_service.py` | Backend Service | Thêm `_build_course_outline_context`, `_is_refusal_content`, sliding window 6 lượt, sửa double-append |
| `src/pwd301/services/gemini_service.py` | Backend Service | Chuẩn hóa System Instruction, tách riêng `<reference_context>`, giữ lại gợi ý khóa học |
| `src/pwd301/services/rag_service.py` | Backend Service | Thêm `auto_ingest_lesson_content` và `auto_ingest_course_materials` |
| `src/pwd301/services/lesson_service.py` | Backend Service | Hook auto-ingest khi tạo hoặc cập nhật bài giảng `PUBLISHED` |
| `src/pwd301/services/course_service.py` | Backend Service | Hook auto-ingest khi khóa học chuyển sang trạng thái `PUBLISHED` |
| `src/pwd301/blueprints/student/routes.py` | Backend Blueprint | Cho phép học viên hỏi đề cương khóa học công khai, fix session reset và context isolation |
| `src/pwd301/services/recommendation_service.py` | Backend Service | Bổ sung trường `id` song song với `course_id` cho tính tương thích giao diện |
| `frontend/assets/js/api.js` | Frontend API | Hỗ trợ gửi `conversation_id: null` và `lesson_id` |
| `frontend/assets/js/views/student.js` | Frontend View | Sửa fallback phân tích `res.reply` trên NetAcad console và chuẩn hóa tên Bạch tuộc AI |
| `frontend/assets/js/ui.js` | Frontend UI | Bổ sung nút Reset chat và cách ly `courseId` trong FloatingAITutor |
| `frontend/assets/js/router.js` | Frontend Router | Khôi phục route `#/student/ai-assistant` liên kết với `StudentView.renderAIAssistant` |
| `frontend/index.html` | Frontend Layout | Thêm nút `#floating-ai-reset-btn` trên header Floating AI Drawer |
| `tests/unit/test_ai_service.py` | Unit Tests | Thêm các test kiểm thử đề cương, sliding window 6 turns, cách ly refusal |
| `tests/unit/test_rag_service.py` | Unit Tests | Thêm test kiểm thử tự động ingest bài học khi publish |
| `tests/api/test_student_backend_completion.py` | API Tests | Thêm test hỏi đề cương không cần enrollment, reset session khi `conversation_id: null` |

---

## 3. Bằng chứng Xác minh Thực nghiệm (Verification Evidence)

Toàn bộ các bộ kiểm thử đã được chạy trực tiếp và đạt kết quả 100% xanh:

```
tests/unit/test_ai_service.py: 22 passed
tests/unit/test_rag_service.py: 6 passed
tests/api/test_ai_api.py: 8 passed
tests/api/test_student_backend_completion.py: 16 passed
Total: 52 passed in 26.86s
```

- **Repository Contract Check**: `python scripts/repo_check.py` -> PASS (All contract files exist, zero duplicate DDLs).
- **Ruff Code Linter**: `ruff check` trên tất cả các file chỉnh sửa -> All checks passed (0 errors).
- **JavaScript Syntax Validation**: `node -c frontend/assets/js/*.js` -> 0 errors, syntax valid.
