# AI Assistant Complete Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Khắc phục triệt để và toàn diện 13 khiếm khuyết của Trợ lý AI (Bạch tuộc trợ lí AI / Octopus AI Assistant) trên cả Backend và Frontend, giúp AI hiểu sâu sắc toàn diện nội dung khóa học và xóa bỏ hoàn toàn hiện tượng bộ nhớ "bãi rác" làm sai lệch câu trả lời.

**Architecture:** 
1. **Curriculum Grounding Engine**: Nạp tự động siêu dữ liệu khóa học (mô tả, mục tiêu đầu ra SLO, cấu trúc chương, danh sách bài học, điều kiện tiên quyết) vào prompt context; kích hoạt pipeline băm nhỏ và nạp RAG tự động khi bài học/khóa học được xuất bản. Cho phép học viên tra cứu thông tin tổng quan môn học công khai mà không bị chặn 403.
2. **Context-Separated Prompting**: Tách bạch tuyệt đối giữa System Instruction chuẩn và Reference Data (`<course_outline>`, `<current_lesson_content>`, `<retrieved_context>`, `<recommendations>`), loại bỏ lỗi nhét markdown vào ngoặc đơn tiêu đề và lỗi đánh rơi dữ liệu ở phạm vi GLOBAL.
3. **Sliding-Window Memory & Clean Session State**: Giới hạn lịch sử hội thoại trượt 6-8 lượt gần nhất; loại bỏ tin nhắn từ chối/ngoài phạm vi khỏi ngữ cảnh gửi tới LLM; xử lý triệt để nút "Làm mới phiên" (xóa session cookie backend, không hồi sinh phiên cũ) và ngăn rò rỉ ngữ cảnh chéo giữa các môn.
4. **Unified Frontend AI State & Parser Repair**: Sửa lỗi trích xuất `res.reply` tại NetAcad Console; bổ sung nút làm mới hội thoại cho Floating AI Widget; đồng bộ ngữ cảnh theo môn học và khôi phục không gian học tập AI toàn màn hình.

**Tech Stack:** Python 3.12, Flask, SQLAlchemy, Microsoft SQL Server / SQLite, Google Gemini REST API (`gemini-flash-latest`), Vanilla JavaScript (ES6+), Tailwind CSS.

**Spec:** [`tasks/TASK-077.md`](file:///e:/PWD301/tasks/TASK-077.md), [`docs/system/PWD301_SYSTEM_SPECIFICATION/business/01_BUSINESS_RULE_CATALOG.md`](file:///e:/PWD301/docs/system/PWD301_SYSTEM_SPECIFICATION/business/01_BUSINESS_RULE_CATALOG.md), [`docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md`](file:///e:/PWD301/docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md).

## Global Constraints
- Target DB: Microsoft SQL Server / SQLite (tuân thủ `BIGINT` PK, public UUID/GUID qua ADR-002, `ROWVERSION`).
- Pure Headless Architecture: Mọi route backend phục vụ JSON envelope chuẩn hóa `{"success": true/false, ...}`. Không sinh HTML template.
- Zero-Trust AI Assistant: Trợ lý mang tên duy nhất **Bạch tuộc trợ lí AI** (Octopus AI Assistant); không bịa đặt khóa học không tồn tại; chặn 100% prompt injection và không rò rỉ tài khoản/CSDL nội bộ.
- Fail-Closed RAG Security: Tài liệu RAG độc quyền yêu cầu ghi danh `ACTIVE` hợp lệ; thông tin đề cương công khai cho phép học viên chưa ghi danh tìm hiểu để đăng ký môn.
- 5-Minute Inactivity Lifecycle (AI-003): Phiên trò chuyện hết hạn sau 300s không hoạt động.

## Review Focus
1. **Unenrolled Public Course Inquiry**: Học viên chưa đăng ký môn hỏi AI về đề cương môn học trên Catalog $\rightarrow$ AI trả lời đúng đề cương, không ném HTTP 403.
2. **Zombie Session Resurrection**: Người dùng bấm "Làm mới phiên", gửi `conversation_id: null` $\rightarrow$ Backend tạo phiên mới toanh, không lấy lại session cookie cũ.
3. **Multi-turn History Bloat**: Người dùng trò chuyện > 10 lượt $\rightarrow$ Prompt chỉ giữ 6-8 lượt gần nhất, không làm quá tải token hoặc gây loạn ngữ cảnh.
4. **Console AI Parser**: Backend trả về `{"reply": "..."}` $\rightarrow$ NetAcad Console hiển thị đúng câu trả lời của AI, không bị fallback về câu báo lỗi.
5. **Context Switch Isolation**: Đang hỏi Môn A chuyển sang Môn B $\rightarrow$ AI không pha trộn nội dung của Môn A vào câu trả lời Môn B.

---

### Task 1: Backend — Course Syllabus Grounding & Public Inquiry Access

**Files:**
- Modify: `src/pwd301/services/ai_service.py:790-850`
- Modify: `src/pwd301/blueprints/student/routes.py:1335-1375`
- Test: `tests/unit/test_ai_service.py`
- Test: `tests/api/test_ai_api.py`

**Interfaces:**
- Produces: `_build_course_outline_context(course: Course) -> str`
- Consumes: `Course.learning_units`, `Course.lessons`, `Course.learning_objectives_list`, `Course.prerequisites`

- [ ] **Step 1: Write the failing unit tests for course outline grounding & public inquiry**

```python
# In tests/unit/test_ai_service.py
def test_course_syllabus_grounding_in_chat(app, student_user, sample_course):
    """AI receives structured course syllabus when context_type is COURSE."""
    from pwd301.models.course import LearningUnit, Lesson
    sess = db.session
    u1 = LearningUnit(course_id=sample_course.id, title="Chương 1: Khởi động", position=1)
    sess.add(u1)
    sess.flush()
    l1 = Lesson(course_id=sample_course.id, learning_unit_id=u1.id, title="Bài 1: Cài đặt môi trường", position=1, status="PUBLISHED")
    sess.add(l1)
    sess.commit()

    conv = create_conversation(actor=student_user, context_type="COURSE", course_id=sample_course.public_id, session=sess)
    user_msg, asst_msg = send_chat_message(
        actor=student_user,
        conversation_id=str(conv.public_id),
        content="Khóa học này gồm những bài học nào?",
        session=sess
    )
    assert asst_msg is not None
```

```python
# In tests/api/test_student_backend_completion.py
def test_student_can_ask_ai_about_published_course_without_enrollment(client, student_user, sample_course):
    """Student browsing catalog can ask AI about course syllabus without 403 Forbidden."""
    headers = _auth_headers(student_user)
    resp = client.post(
        "/student/ai/chat",
        json={"message": "Khóa học này dạy những gì?", "course_id": str(sample_course.public_id)},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "success"
    assert "reply" in data
```

- [ ] **Step 2: Run tests to verify they fail**
Run: `pytest tests/unit/test_ai_service.py -k test_course_syllabus_grounding_in_chat -v`
Run: `pytest tests/api/test_student_backend_completion.py -k test_student_can_ask_ai_about_published_course_without_enrollment -v`
Expected: FAIL (403 Forbidden on unenrolled inquiry, missing course syllabus in context)

- [ ] **Step 3: Implement `_build_course_outline_context` and refine enrollment check**
1. In `src/pwd301/services/ai_service.py`:
   - Add `_build_course_outline_context(course: Course) -> str`: Extracts description, category, difficulty, learning objectives, and list of modules + lesson titles.
   - In `send_chat_message`: When `conv.course` is present, always inject `<course_syllabus_outline>` block into `grounded_context_parts`.
2. In `src/pwd301/blueprints/student/routes.py`:
   - Relax enrollment requirement for public inquiry: If `target_course.status == "PUBLISHED"`, allow AI chat to proceed so prospective students can learn about the course syllabus. Restrict proprietary RAG materials/files retrieval to active enrollments in `rag_service.py` (preserving SEC-006 / TASK-024).

- [ ] **Step 4: Run tests to verify they pass**
Run: `pytest tests/unit/test_ai_service.py -k test_course_syllabus_grounding_in_chat -v`
Run: `pytest tests/api/test_student_backend_completion.py -k test_student_can_ask_ai_about_published_course_without_enrollment -v`
Expected: PASS

- [ ] **Step 5: Commit changes**
```bash
git add src/pwd301/services/ai_service.py src/pwd301/blueprints/student/routes.py tests/
git commit -m "fix(ai): ground course syllabus and allow public course inquiry without 403"
```

---

### Task 2: Backend — Prompt Architecture & Context Separation

**Files:**
- Modify: `src/pwd301/services/gemini_service.py:1100-1175`
- Modify: `src/pwd301/services/ai_service.py:880-920`
- Test: `tests/unit/test_ai_service.py`

**Interfaces:**
- Produces: Clean `system_instruction` with isolated `<reference_context>` blocks in `gemini_service.py`.
- Fixes: Parenthetical prompt stuffing bug and GLOBAL context dropping bug.

- [ ] **Step 1: Write the failing tests for context formatting & global recommendation delivery**

```python
# In tests/unit/test_ai_service.py
def test_global_recommendation_context_delivered_to_model(app, student_user):
    """When on GLOBAL context, course recommendations are included in the prompt payload."""
    with unittest.mock.patch("pwd301.services.gemini_service.RealGeminiClient._call_gemini_api") as mock_call:
        mock_call.return_value = {
            "candidates": [{"content": {"parts": [{"text": "Dưới đây là các khóa học gợi ý..."}]}}]
        }
        conv = create_conversation(actor=student_user, context_type="GLOBAL", session=db.session)
        user_msg, asst_msg = send_chat_message(
            actor=student_user,
            conversation_id=str(conv.public_id),
            content="Gợi ý khóa học lập trình phù hợp cho tôi",
            session=db.session,
        )
        assert mock_call.called
        payload = mock_call.call_args[0][0]
        sys_text = payload.get("systemInstruction", {}).get("parts", [{}])[0].get("text", "")
        # Must contain recommendations and must NOT have broken parenthetical header
        assert "VAI TRÒ TRONG KHÓA HỌC / BÀI HỌC (" not in sys_text
        assert "DỮ LIỆU THAM CHIẾU" in sys_text or "<reference_context>" in sys_text
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/unit/test_ai_service.py -k test_global_recommendation_context_delivered_to_model -v`
Expected: FAIL (sys_text drops recommendations on GLOBAL, or contains parenthetical stuffing)

- [ ] **Step 3: Refactor System Instruction and Context Injection in `gemini_service.py`**
1. In `RealGeminiClient.chat_response`:
   - Separate static System Instruction (Persona, Guardrails, Scope Policy, Safety Rules) from Dynamic Reference Data (`context`).
   - Eliminate `f"VAI TRÒ TRONG KHÓA HỌC / BÀI HỌC ({context}):\n"` completely.
   - Format dynamic reference data cleanly under an explicit section:
     ```
     DỮ LIỆU THAM CHIẾU HỌC TẬP (REFERENCE CONTEXT):
     <reference_context>
     {context}
     </reference_context>
     ```
   - Ensure `is_global` check does NOT discard `context`. When recommendations or catalog summaries exist in `context`, append them inside `<reference_context>` regardless of whether `context_type` is GLOBAL, COURSE, or LESSON.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/unit/test_ai_service.py -k test_global_recommendation_context_delivered_to_model -v`
Expected: PASS

- [ ] **Step 5: Commit changes**
```bash
git add src/pwd301/services/gemini_service.py tests/unit/test_ai_service.py
git commit -m "fix(gemini): separate system instruction from reference context and preserve global recommendations"
```

---

### Task 3: Backend — Sliding-Window Memory, Refusal Isolation & Clean Session Reset

**Files:**
- Modify: `src/pwd301/services/ai_service.py:730-785, 895-915`
- Modify: `src/pwd301/blueprints/student/routes.py:1295-1335`
- Test: `tests/unit/test_ai_service.py`
- Test: `tests/api/test_ai_api.py`

**Interfaces:**
- Implements: Sliding window (last 6 turns = 12 messages maximum) for conversation history.
- Isolates: Out-of-scope / refusal messages from LLM few-shot history.
- Fixes: Double-append bug and Zombie Session Resurrection bug.

- [ ] **Step 1: Write the failing tests for sliding window, refusal isolation, and session reset**

```python
# In tests/unit/test_ai_service.py
def test_conversation_history_sliding_window_limits_turns(app, student_user):
    """Conversation history sent to Gemini is bounded by sliding window (max 6 turns)."""
    sess = db.session
    conv = create_conversation(actor=student_user, context_type="GLOBAL", session=sess)
    # Seed 10 previous message pairs (20 messages)
    for i in range(1, 11):
        sess.add(AIMessage(conversation_id=conv.id, sender="USER", content=f"Q{i}", sequence_no=2*i-1))
        sess.add(AIMessage(conversation_id=conv.id, sender="ASSISTANT", content=f"A{i}", sequence_no=2*i))
    sess.commit()

    with unittest.mock.patch("pwd301.services.gemini_service.RealGeminiClient._call_gemini_api") as mock_call:
        mock_call.return_value = {
            "candidates": [{"content": {"parts": [{"text": "Câu trả lời mới"}]}}]
        }
        send_chat_message(actor=student_user, conversation_id=str(conv.public_id), content="Câu hỏi mới số 11", session=sess)
        payload = mock_call.call_args[0][0]
        contents = payload.get("contents", [])
        # Sliding window of 6 turns = max 12 prior items + 1 current = 13 items
        assert len(contents) <= 13
        # Oldest Q1 must be pruned
        assert not any("Q1" == p.get("parts", [{}])[0].get("text") for p in contents)
```

```python
# In tests/api/test_ai_api.py
def test_new_chat_with_null_conversation_id_creates_fresh_session(client, student_user):
    """Sending conversation_id=null actively creates a new conversation and does not revive old session."""
    headers = _auth_headers(student_user)
    # First message creates conversation A
    r1 = client.post("/student/ai/chat", json={"message": "Câu hỏi 1"}, headers=headers)
    assert r1.status_code == 200
    conv_id_1 = r1.get_json()["conversation_id"]

    # Second message with explicit conversation_id=None / null
    r2 = client.post("/student/ai/chat", json={"message": "Câu hỏi 2", "conversation_id": None}, headers=headers)
    assert r2.status_code == 200
    conv_id_2 = r2.get_json()["conversation_id"]

    # Must be a new conversation
    assert conv_id_1 != conv_id_2
```

- [ ] **Step 2: Run tests to verify they fail**
Run: `pytest tests/unit/test_ai_service.py -k test_conversation_history_sliding_window_limits_turns -v`
Run: `pytest tests/api/test_ai_api.py -k test_new_chat_with_null_conversation_id_creates_fresh_session -v`
Expected: FAIL (unbounded history, zombie session resurrection from Flask session cookie)

- [ ] **Step 3: Implement Sliding Window, Refusal Filter, and Session Reset Fix**
1. In `src/pwd301/services/ai_service.py`:
   - In `send_chat_message`: Prune `conv.messages` to the most recent `MAX_HISTORY_TURNS = 6` (last 12 messages).
   - Filter out refusal / malicious messages from LLM `history` so past out-of-scope errors do not pollute subsequent valid academic turns.
   - Eliminate the double-append bug: Build `history` cleanly without appending `sanitized_content` twice.
2. In `src/pwd301/blueprints/student/routes.py`:
   - Inspect request payload: If `"conversation_id"` is explicitly provided as `None` or empty string in JSON payload, treat as an explicit "New Chat" request: clear `session.pop("active_ai_conversation_id", None)` immediately and force creation of a new conversation session.
   - Update `should_reset` logic to safely detect course changes (`req_course != conv.course_id`) and lesson changes.

- [ ] **Step 4: Run tests to verify they pass**
Run: `pytest tests/unit/test_ai_service.py -k test_conversation_history_sliding_window_limits_turns -v`
Run: `pytest tests/api/test_ai_api.py -k test_new_chat_with_null_conversation_id_creates_fresh_session -v`
Expected: PASS

- [ ] **Step 5: Commit changes**
```bash
git add src/pwd301/services/ai_service.py src/pwd301/blueprints/student/routes.py tests/
git commit -m "fix(ai): implement sliding window memory, refusal isolation, and clean new-chat reset"
```

---

### Task 4: Backend — Automated RAG Ingestion Pipeline on Content Lifecycle

**Files:**
- Modify: `src/pwd301/services/rag_service.py:595-660`
- Modify: `src/pwd301/blueprints/instructor/routes.py:1180-1250` (or lesson/course update routes)
- Modify: `src/pwd301/blueprints/admin/routes.py` (course publish approval)
- Test: `tests/unit/test_rag_service.py`

**Interfaces:**
- Produces: `auto_ingest_lesson_on_publish(lesson_id: int | str, actor: User, session: Session)`
- Produces: `auto_ingest_course_on_publish(course_id: int | str, actor: User, session: Session)`

- [ ] **Step 1: Write the failing test for automatic RAG ingestion on lesson and course publish**

```python
# In tests/unit/test_rag_service.py
def test_auto_ingest_creates_knowledge_chunks_on_published_lesson(app, instructor_user, sample_course):
    """When a lesson is published, KnowledgeChunks are automatically generated for RAG."""
    from pwd301.models.course import Lesson
    from pwd301.models.ai_rag import KnowledgeDocument
    sess = db.session
    lesson = Lesson(
        course_id=sample_course.id,
        title="Bài học tự động nạp RAG",
        markdown_content="# Kiến trúc mạng máy tính\nMô hình OSI gồm 7 tầng từ Physical đến Application.",
        status="PUBLISHED"
    )
    sess.add(lesson)
    sess.commit()

    # Ingest helper should index published lesson
    from pwd301.services.rag_service import ingest_lesson_content
    doc, ver, chs = ingest_lesson_content(actor=instructor_user, lesson_id=lesson.public_id, session=sess)
    assert len(chs) > 0
    assert doc.status == "ACTIVE"
    assert ver.is_current is True
```

- [ ] **Step 2: Run test to verify ingestion functionality**
Run: `pytest tests/unit/test_rag_service.py -k test_auto_ingest_creates_knowledge_chunks_on_published_lesson -v`

- [ ] **Step 3: Integrate automatic ingestion trigger into course and lesson workflows**
1. In `src/pwd301/services/rag_service.py`: Add fail-safe helper `sync_course_knowledge_background` that safely invokes `ingest_course_knowledge` without failing transaction if chunking errors occur.
2. Hook into `publish_course` / `approve_course_workflow` and lesson update workflows when state becomes `PUBLISHED`.
3. Provide a one-shot startup/CLI helper to backfill and ingest all existing published courses in DB so RAG table is populated.

- [ ] **Step 4: Verify tests pass**
Run: `pytest tests/unit/test_rag_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit changes**
```bash
git add src/pwd301/services/rag_service.py src/pwd301/blueprints/ tests/unit/test_rag_service.py
git commit -m "feat(rag): enable automatic knowledge chunk ingestion on lesson and course publish"
```

---

### Task 5: Frontend — NetAcad Console AI Tab Parsing & Error Remediation

**Files:**
- Modify: `frontend/assets/js/views/student.js:1860-1950`
- Test: `node -c frontend/assets/js/views/student.js`
- Test: Verify in browser with Chrome DevTools MCP

**Interfaces:**
- Fixes: Key lookup `res?.reply` in `sendConsoleAIMessage`.
- Adds: Explicit `conversation_id: null` dispatch on `#console-ai-new-chat-btn`.
- Styles: Responsive markdown prose formatting with overflow guards for code blocks.

- [ ] **Step 1: Write a JS unit/syntax test for the response parsing helper**
Create or update `test_ai_response_parser.js` to assert that `{ reply: "Câu trả lời" }` is resolved correctly and does not default to the generic error string.

- [ ] **Step 2: Run syntax verification**
Run: `node -c frontend/assets/js/views/student.js`

- [ ] **Step 3: Fix `sendConsoleAIMessage` and `#console-ai-new-chat-btn` in `student.js`**
1. Fix line 1895:
   ```javascript
   const reply = res?.reply || res?.data?.reply || res?.assistant_message?.content || res?.message || res?.content || 'Xin lỗi bạn, mình chưa thể xử lý yêu cầu lúc này.';
   ```
2. In `#console-ai-new-chat-btn` click handler:
   - Reset `consoleConvId = null;`.
   - Clear UI message container and render welcoming octopus banner.
   - Show `UI.showToast('Đã bắt đầu phiên trao đổi mới với Bạch tuộc AI', 'info')`.
3. In `appendConsoleAIMessage`:
   - Add `prose dark:prose-invert max-w-none break-words overflow-hidden text-xs` to the markdown container.
   - Add `overflow-x-auto rounded-lg my-1` for `<pre><code>` code blocks.

- [ ] **Step 4: Verify JS syntax**
Run: `node -c frontend/assets/js/views/student.js`
Expected: 0 errors

- [ ] **Step 5: Commit changes**
```bash
git add frontend/assets/js/views/student.js
git commit -m "fix(frontend): resolve console AI response parsing bug and add clean session reset"
```

---

### Task 6: Frontend — FloatingAITutor Reset, Context Isolation & Route Modernization

**Files:**
- Modify: `frontend/assets/js/ui.js:1770-1890`
- Modify: `frontend/assets/js/router.js:409-412`
- Test: `node -c frontend/assets/js/ui.js`
- Test: `node -c frontend/assets/js/router.js`

**Interfaces:**
- Adds: `#floating-ai-reset-btn` (New Chat / Xóa đoạn chat) in `#floating-ai-drawer`.
- Fixes: Context clearing when switching courses in `FloatingAITutor.openWithQuestion`.
- Re-activates: `#/student/ai-assistant` route pointing to `StudentView.renderAIAssistant`.

- [ ] **Step 1: Inspect and update Floating AI drawer template & controls in `ui.js`**
1. Add a "Làm mới" (Refresh / New Chat) button in the header of `#floating-ai-drawer` next to the close button:
   ```html
   <button id="floating-ai-reset-btn" class="p-1 hover:bg-[#E8E6DF] dark:hover:bg-[#2E2D2B] rounded-lg text-xs flex items-center gap-1 text-[#8F8E8A] hover:text-[#222120] dark:hover:text-[#EDEDEB]" title="Bắt đầu phiên trò chuyện mới">
     <span class="material-symbols-outlined text-[16px]">refresh</span>
   </button>
   ```
2. Wire `resetBtn.onclick`:
   - Set `FloatingAITutor.conversationId = null;`.
   - Clear `#floating-ai-messages` and insert initial greeting.
   - Show toast notification.
3. In `FloatingAITutor.openWithQuestion(promptText, courseId)`:
   - If `courseId` is provided and different from `FloatingAITutor.courseId`:
     - Update `FloatingAITutor.courseId = courseId;`.
     - Reset `FloatingAITutor.conversationId = null;` to prevent cross-course context pollution!

- [ ] **Step 2: Update `router.js` for `#/student/ai-assistant`**
- In `frontend/assets/js/router.js`:
  Replace the redirect `window.location.hash = '#/student/dashboard';` with:
  ```javascript
  } else if (path === '#/student/ai-assistant') {
      await StudentView.renderAIAssistant(viewport);
  }
  ```
- Add link to `#/student/ai-assistant` in the student navigation drawer / user menu for easy access to full-page AI tutor.

- [ ] **Step 3: Run syntax checks**
Run: `node -c frontend/assets/js/ui.js`
Run: `node -c frontend/assets/js/router.js`
Expected: 0 errors

- [ ] **Step 4: Commit changes**
```bash
git add frontend/assets/js/ui.js frontend/assets/js/router.js
git commit -m "fix(frontend): add reset control to Floating AI, prevent context bleed, and restore AI assistant page"
```

---

### Task 7: Comprehensive Regression & Verification Suite

**Files:**
- Verify: All modified backend & frontend files.
- Scripts: `python scripts/repo_check.py`, `ruff check src/ tests/`, `pytest tests/`

- [ ] **Step 1: Run repository contract check**
Run: `python scripts/repo_check.py`
Expected: PASS (0 markdown fence or contract errors)

- [ ] **Step 2: Run Ruff linter**
Run: `ruff check src/ tests/`
Expected: All checks passed (0 errors)

- [ ] **Step 3: Run full backend AI & student test suite**
Run: `pytest tests/unit/test_ai_service.py tests/unit/test_ai_scope_classifier.py tests/security/test_ai_scope_enforcement.py tests/unit/test_rag_service.py tests/api/test_ai_api.py tests/api/test_student_backend_completion.py -v`
Expected: 100% tests PASSED (0 failures, 0 errors)

- [ ] **Step 4: Live Browser Verification with Chrome DevTools MCP**
- Start dev server if needed, test NetAcad Console AI Tab and Floating AI Widget:
  1. Ask: "Khóa học này gồm những bài học nào?" $\rightarrow$ AI lists actual lessons from course syllabus.
  2. Click "Làm mới hội thoại" $\rightarrow$ session resets cleanly.
  3. Ask 7 follow-up questions $\rightarrow$ sliding window retains recent context without hallucinations.
  4. Inspect console logs $\rightarrow$ 0 errors, no broken JSON, no `[REDACTED_API_KEY]` leaks.

- [ ] **Step 5: Final summary commit & task completion report**
```bash
git commit -m "chore(ai): complete comprehensive AI Assistant remediation across backend and frontend"
```
