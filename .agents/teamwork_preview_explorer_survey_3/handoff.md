# Handoff Report: R3 (Assessment Authoring & Document Import) & R5 (Context-Aware Grounded AI & Recommendations)

- **Date**: 2026-09-14
- **Agent**: Survey Explorer 3 (`teamwork_preview_explorer`)
- **Working Directory**: `e:\PWD301\.agents\teamwork_preview_explorer_survey_3`
- **Target Subsystems**:
  - **R3**: Assessment Page Question Authoring, In-Place Editing, PDF/DOCX Document Import, Timing Lock (BR-031 / Invariant 13), Structural Freeze (BR-030 / Invariant 14).
  - **R5**: Context-Aware AI Assistant (`app_shell.js`), Dynamic Scoping, Grounded Semantic RAG (`[Ref: <UUID>]`), Course Catalog Knowledge & Recommendation Engine (Algorithm 14).

---

## 1. Observation

### 1.1 Source-of-Truth Specifications & Invariants
- **`docs/system/PWD301_SYSTEM_SPECIFICATION/business/01_BUSINESS_RULE_CATALOG.md`**:
  - `QBANK-001`: Question belongs to exactly one Course, optional Lesson (`questions.course_id`, `questions.lesson_id`).
  - `QBANK-002`: Unused Question edited in-place; used Question requires new `QuestionRevision` with monotonic sequence.
  - `QBANK-003`: Choices and accepted answers versioned with `QuestionRevision` (`question_revision_choices`, `question_revision_accepted_answers`).
  - `QBANK-004`: Question type cannot change after first student answer (`questions.first_answered_at IS NOT NULL`).
  - `ASSESS-001`: Timing parameters (`open_at`, `close_at`, `time_limit_minutes`, `attempt_limit`) locked after publish (Invariant 13). `close_at` can only be extended forward.
  - `ASSESS-002` & `ASSESS-003`: Assessment structure (assigned questions) and points locked after first student start (`first_attempt_started_at IS NOT NULL`) (Invariant 14).
  - `IMPORT-001` & `IMPORT-002`: Import drafts parsed from documents; answer keys unconfirmed until instructor verification; duplicates flagged without auto-merging.
  - `AI-001` & `AI-002`: RAG retrieves only authorized published course content; draft/archived/deleted sources excluded immediately.
  - `AI-003`: Raw AI conversation purged after 5 minutes of inactivity (`expires_at = last_activity_at + 5m`).
  - `AI-005`: Backend computes course recommendations via Algorithm 14; Gemini only explains.
  - `AI-006`: AI answers cite grounded sources using `[Ref: <UUID>]` and persist telemetry in `ai_requests` and `ai_source_usages`.
- **`docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md`**:
  - Invariant 13: "Assessment timing locked after publish."
  - Invariant 14: "Assessment structure/assigned points locked after first Student start."
  - Invariant 20: "RAG retrieves only currently authorized published content; archived/deleted/draft excluded."
  - Invariant 21: "Raw AI chat content purges after five minutes inactivity."

---

### 1.2 R3 Current Implementation State & Gap Analysis

#### A. Direct Question Authoring & In-Place Editing on Assessment Page
- **Template Inspection (`src/pwd301/templates/instructor/assessment_builder.html`)**:
  - Lines 150-156:
    ```html
    {% if not structure_locked %}
    <button class="btn btn-primary btn-sm d-flex align-items-center gap-2" data-bs-toggle="modal" data-bs-target="#addQuestionModal">
      + Thêm câu hỏi từ Ngân hàng
    </button>
    {% endif %}
    ```
    *Finding*: Only links existing questions from Question Bank. Missing direct authoring button (`+ Tạo câu hỏi mới`) and modal for authoring Single Choice, Multiple Choice, True/False, Short Answer with custom points, choices, and explanations directly on the assessment page.
  - Lines 172-200:
    Table rows render `#`, `Nội dung câu hỏi`, `Độ khó`, `Điểm phân bổ`, and a form submitting to `/instructor/assessments/{{ assessment.public_id }}/questions/{{ q_id }}/remove`.
    *Finding*: Missing an in-place "Chỉnh sửa" (Edit) action/modal to modify question prompt, choices, correct flag, explanation, and points directly on the assessment page.

- **Backend Route Inspection (`src/pwd301/blueprints/instructor/routes.py`)**:
  - Lines 1461-1490:
    ```python
    @instructor_bp.route("/assessments/<assessment_id>/questions", methods=["POST"])
    @instructor_required
    def assign_instructor_question_route(assessment_id: str) -> Any:
        actor = require_authenticated_actor()
        payload = request.get_json(silent=True) or request.form.to_dict() or {}
        assignment = assign_question(actor, assessment_id, payload, session=db.session)
        ...
    ```
    *Finding*: Assumes `payload["question_id"]` already exists in the course Question Bank.
  - Lines 1010-1041:
    `POST /courses/<course_id>/questions` (`create_course_question_route`) calls `create_question(actor, course_id, payload)`.
  - Lines 1091-1101:
    `PATCH / PUT /questions/<question_id>` (`update_question_route`) calls `update_question(actor, question_id, payload)`.

- **Service Layer Inspection**:
  - `src/pwd301/services/assessment_service.py`:
    - Line 1306 (`assign_question`): Checks `assessment.first_attempt_started_at is not None` -> raises `AssessmentLockedError`. Revalidates `question.course_id == assessment.course_id`. Sets `source_type` ('MANUAL', 'BANK', 'IMPORT', 'AI').
    - Line 1415 (`remove_question_assignment`): Checks `assessment.first_attempt_started_at is not None` -> raises `AssessmentLockedError`.
    - Line 1468 (`update_question_assignment`): Updates points and position; checks `assessment.first_attempt_started_at is not None` -> raises `AssessmentLockedError`.
  - `src/pwd301/services/question_bank_service.py`:
    - Line 313 (`create_question`): Fully supports `SINGLE_CHOICE`, `MULTIPLE_CHOICE`, `TRUE_FALSE`, `SHORT_ANSWER`, `ESSAY` with choices, accepted answers, points, Bloom difficulty, and audit logging.
    - Line 952 (`is_question_in_use`): Evaluates if question has appeared in student attempts, published assessment assignments, or exposed revisions.
    - Line 1477 (`update_question`): If unused, updates current revision in-place (content, choices, answers). If in-use, requires `change_reason` and generates a new revision via `create_question_revision`.

#### B. Document Import Pipeline (PDF & DOCX)
- **Model Inspection (`src/pwd301/models/file_import.py`)**:
  - Lines 516-524:
    ```python
    draft_assessment_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "assessments.id",
            name="fk_document_import_jobs_draft_assessment_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    ```
    *Finding*: The canonical DB schema has `draft_assessment_id` foreign key on `document_import_jobs`.
- **Service Inspection (`src/pwd301/services/import_service.py`)**:
  - Line 829 (`create_import_job`):
    ```python
    def create_import_job(
        actor: User,
        course_id: int | uuid.UUID | str,
        file_asset_id: int | uuid.UUID | str,
        draft_assessment_id: int | uuid.UUID | str | None = None,
        session: Session | scoped_session[Any] | None = None,
    ) -> DocumentImportJob:
    ```
    *Critical Bug/Omission*: Lines 911-920 instantiate `job = DocumentImportJob(...)` but omit `draft_assessment_id=...`! The passed argument is discarded and never saved to the database.
  - Line 1222 (`commit_import_job`):
    Iterates through accepted questions, calls `create_question(...)` into Question Bank, sets `job.status = 'COMPLETED'`.
    *Critical Omission*: It does not assign the created questions to `job.draft_assessment` when `job.draft_assessment_id` is present.
- **Web UI & Route Inspection (`src/pwd301/blueprints/instructor/routes.py`)**:
  - Lines 1745-1793 (`POST /courses/<course_id>/imports`):
    Accepts direct multipart file upload (`request.files["file"]`), stores it as `FileAsset` (`asset_type="IMPORT_SOURCE"`), calls `create_import_job` and `process_import_job`.
    *Finding*: Does not accept or pass `draft_assessment_id`. No endpoint exists under `/instructor/assessments/<assessment_id>/import`.
  - `src/pwd301/templates/instructor/assessment_builder.html`:
    Has no button or modal for "Upload PDF/DOCX tạo đề tự động".

#### C. Timing Lock & Structural Freeze Invariant Enforcement
- **Timing Lock (BR-031 / Invariant 13)**:
  - `src/pwd301/services/assessment_service.py:640-705` (`update_assessment`):
    Once `assessment.published_at IS NOT NULL`:
    `open_at`, `time_limit_minutes`, and `attempt_limit` cannot be changed.
    `close_at` cannot be removed or moved earlier into the past.
  - `src/pwd301/templates/instructor/assessment_builder.html:257, 266, 286`:
    Renders warning banner (lines 100-108) and disables `time_limit_minutes`, `attempt_limit`, `open_at` when `timing_locked`.
- **Structural Freeze (BR-030 / Invariant 14)**:
  - Once `assessment.first_attempt_started_at IS NOT NULL`:
    `assign_question`, `remove_question_assignment`, `update_question_assignment`, and `configure_blueprint` all raise `AssessmentLockedError`.
  - `src/pwd301/templates/instructor/assessment_builder.html:110-118`:
    Renders red alert card explaining structural freeze and directing instructor to QuestionCorrection & Regrade engine. Disables remove button.

---

### 1.3 R5 Current Implementation State & Gap Analysis

#### A. Client-Side Context Transmission (`app_shell.js`)
- **Inspection (`src/pwd301/static/js/app_shell.js`)**:
  - Lines 415-427:
    ```javascript
    const payload = { message: text };
    if (this._activeConversationId) {
      payload.conversation_id = this._activeConversationId;
    }

    fetch('/student/ai/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken()
      },
      body: JSON.stringify(payload)
    })
    ```
    *Finding*: `app_shell.js` only transmits `{ message: text, conversation_id }`.
    *Omission*: Does NOT detect or transmit `page_route` (`window.location.pathname`), `page_title` (`document.title`), `course_id`, or `lesson_id`.

#### B. Dynamic Conversation Scoping
- **Inspection (`src/pwd301/blueprints/student/routes.py:830-863`)**:
  ```python
  conv_id = payload.get("conversation_id") or session.get("active_ai_conversation_id")
  if conv_id:
      conv = get_conversation(actor=actor, conversation_id=conv_id, session=db.session)
  ```
  *Finding*: If a student chats on the dashboard, `session["active_ai_conversation_id"]` contains a `GLOBAL` conversation. When navigating to `/student/courses/<course_id>` or `/student/lessons/<lesson_id>`, the endpoint reuses the old `GLOBAL` conversation instead of dynamically switching to a `COURSE` or `LESSON` scoped conversation.

#### C. Grounded Semantic RAG against Lesson Text & Files with Citations `[Ref: <UUID>]`
- **Inspection (`src/pwd301/services/rag_service.py`)**:
  - Lines 752-930 (`retrieve_relevant_chunks`): Retrieves top-k chunks from `knowledge_chunks` filtered by authorized `course_id`, excluding draft, archived, or deleted content.
  - Lines 1077-1104 (`_format_context_boundary_blocks`): Encloses chunks in strict security delimiters `<retrieved_context>[Ref: <chunk_uuid>] ...</retrieved_context>`.
  - Lines 1106-1266 (`ask_course_rag`): Executes query over course knowledge, invokes `GeminiClient.answer_rag_query`, parses `[Ref: <UUID>]` citations, and persists source records in `ai_source_usages`.
- **Inspection (`src/pwd301/services/ai_service.py` & `src/pwd301/blueprints/student/routes.py`)**:
  - In `student_ai_chat` (line 890) and `send_chat_message` (`ai_service.py:784`):
    Calls `client.chat_response(messages=history, context=context_str)`.
    *Critical Gap*: `send_chat_message` does NOT invoke `retrieve_relevant_chunks` or `ask_course_rag` when the conversation is scoped to a course or lesson! Students chatting in a course receive generic LLM text rather than grounded answers with `[Ref: <UUID>]` citations pointing to lesson resources.

#### D. Course Catalog Knowledge & Smart Recommendation Engine
- **Inspection (`src/pwd301/services/recommendation_service.py`)**:
  - Lines 80-290 (`generate_course_recommendations`): Implements Algorithm 14:
    - Filters student's completed and active courses.
    - Validates prerequisite graph satisfaction via `_check_prerequisites_met`.
    - Scores candidate courses: Category match (+30), Difficulty progression (+20), Skill reinforcement (+10), Prerequisite satisfied (+25), Cold-start beginner friendly (+30).
    - Uses deterministic sorting (score DESC, title ASC).
    - Enriches with Gemini explanation with fallback to rule-based explanation strings.
- **Inspection (`src/pwd301/services/gemini_service.py`)**:
  - In `MockGeminiClient.chat_response` (lines 386-397):
    When asked about courses or "đây là khóa học gì" in course context or asked for course recommendations on the main page, returns hardcoded generic greeting without mentioning specific course names or catalog recommendations.
  - In `RealGeminiClient.chat_response` (lines 834-865):
    Has instructions defining the roles on GLOBAL and COURSE, but does not receive the active course catalog metadata or active course details in the prompt context.

---

## 2. Logic Chain

```
Observation 1: assessment_builder.html only has "+ Thêm câu hỏi từ Ngân hàng" (#addQuestionModal).
Observation 2: question_bank_service.py has create_question() and update_question() with in-place revision logic.
Observation 3: assessment_service.py has assign_question() and update_question_assignment().
------------------------------------------------------------------------------------------------------
-> Logic Step 1: Instructors currently cannot author new questions or edit existing question text
   without leaving the assessment builder page and navigating to the separate Question Bank.
   To fulfill R3, assessment_builder.html needs "+ Tạo câu hỏi mới" and in-place question editing,
   backed by an endpoint that calls create_question + assign_question atomically (or updates question revision + assignment points).

Observation 4: DocumentImportJob has draft_assessment_id column in database schema.
Observation 5: import_service.py:create_import_job accepts draft_assessment_id in function signature but discards it at line 911.
Observation 6: import_service.py:commit_import_job creates questions in the Question Bank but does not assign them to draft_assessment_id.
------------------------------------------------------------------------------------------------------
-> Logic Step 2: The DB model was designed to link import jobs directly to draft assessments, but the
   service implementation was never completed. Passing draft_assessment_id, persisting it to DocumentImportJob,
   and adding auto-assignment in commit_import_job (or assessment import endpoint) directly completes
   the "Upload PDF/DOCX tạo đề tự động" requirement.

Observation 7: assessment_service.py strictly guards all mutation endpoints against first_attempt_started_at.
Observation 8: assessment_builder.html sets disabled on timing inputs when timing_locked.
------------------------------------------------------------------------------------------------------
-> Logic Step 3: Timing Lock (BR-031 / Invariant 13) and Structural Freeze (BR-030 / Invariant 14) are
   already rigorously enforced in the service layer. New direct question creation, editing, and import
   actions on the assessment builder must check `not structure_locked` in the UI and rely on
   assessment_service.py's existing `AssessmentLockedError` checks.

Observation 9: app_shell.js sends only { message, conversation_id }.
Observation 10: student/routes.py reuses session["active_ai_conversation_id"] across all pages.
------------------------------------------------------------------------------------------------------
-> Logic Step 4: The widget is currently page-unaware. When a student enters a course or lesson,
   the AI remains trapped in the old GLOBAL conversation. Transmitting page_route, page_title, course_id,
   lesson_id from app_shell.js and auto-switching conversation scope in the backend resolves location awareness.

Observation 11: rag_service.py implements ask_course_rag() with [Ref: <UUID>] citations and ai_source_usages persistence.
Observation 12: student/routes.py:student_ai_chat only calls send_chat_message() and skips rag_service.
------------------------------------------------------------------------------------------------------
-> Logic Step 5: The complete RAG retrieval and citation engine exists in rag_service.py, but is disconnected
   from the student floating chat endpoint. Hooking course/lesson-scoped chat into RAG retrieval provides
   instant grounded answers with citations.

Observation 13: recommendation_service.py implements Algorithm 14 with full scoring & Gemini explanation.
Observation 14: MockGeminiClient and RealGeminiClient lack catalog context when asked for course recommendations.
------------------------------------------------------------------------------------------------------
-> Logic Step 6: Connecting recommendation_service.py into chat for recommendation queries ("gợi ý khóa học")
   and injecting course details for "đây là khóa học gì" satisfies the catalog knowledge requirement.
```

---

## 3. Detailed Architecture & Proposed Implementation Plan

### 3.1 R3: Assessment Page Authoring, Direct Editing & Document Import

#### 1. Endpoints Architecture:
- **Direct Question Authoring**:
  - Route: `POST /instructor/assessments/<assessment_id>/questions/create` (or `POST /api/assessments/<assessment_id>/questions/create`)
  - Flow:
    1. Authenticate instructor and verify course ownership.
    2. Check Structural Freeze (`assessment.first_attempt_started_at is not None` -> 409 `AssessmentLockedError`).
    3. Validate payload (`question_type`, `content`, `choices`, `points`, `explanation`, `difficulty`).
    4. Call `create_question(actor, assessment.course_id, question_payload, session=sess)`.
    5. Call `assign_question(actor, assessment.id, {"question_id": str(q.public_id), "points": points, "source_type": "MANUAL"}, session=sess)`.
    6. Return serialized assignment + question with HTTP 201.
- **In-Place Question Editing**:
  - Route: `POST /instructor/assessments/<assessment_id>/questions/<question_id>/edit` (or `PATCH /instructor/questions/<question_id>`)
  - Flow:
    1. Verify course ownership.
    2. Check Structural Freeze on assessment points (`update_question_assignment` enforces Invariant 14).
    3. Call `update_question(actor, question_id, question_payload, session=sess)`:
       - If unused, edits current revision in-place.
       - If in-use, requires reason and generates new revision (ADR-003 / QBANK-002).
    4. If points changed, update `AssessmentQuestionAssignment.points`.
    5. Return updated question and assignment with HTTP 200.
- **Document Import directly on Assessment**:
  - Route: `POST /instructor/assessments/<assessment_id>/import`
  - Flow:
    1. Verify course ownership and check `first_attempt_started_at is None`.
    2. Accept uploaded PDF or Word (.docx) file from `request.files["file"]`.
    3. Store as `FileAsset` (`asset_type="IMPORT_SOURCE"`).
    4. Run malware scan (fail-closed check).
    5. Call `create_import_job(actor, assessment.course_id, asset.id, draft_assessment_id=assessment.id)`.
    6. Call `process_import_job(actor, job.public_id)` -> parses blocks into `ImportQuestion` drafts.
    7. Auto-accept clean detected questions and call `commit_import_job(actor, job.public_id)`.
    8. Assign each imported question to `assessment` via `assign_question(..., source_type="IMPORT")`.
    9. Flash success message with count of imported questions and redirect back to assessment builder.

#### 2. UI Elements in `assessment_builder.html`:
- Add action buttons in the header of Tab 1:
  - `+ Tạo câu hỏi mới` -> triggers `#createQuestionModal`.
  - `Upload PDF/DOCX tạo đề tự động` -> triggers `#importDocumentModal`.
  - Both buttons wrapped in `{% if not structure_locked %}`.
- `#createQuestionModal`:
  - Question Type dropdown (`SINGLE_CHOICE`, `MULTIPLE_CHOICE`, `TRUE_FALSE`, `SHORT_ANSWER`).
  - Question stem (content) textarea with markdown preview.
  - Dynamic choice builder:
    - Choice content input, correct toggle (radio for single choice / true-false; checkbox for multiple choice).
    - Add/remove choice rows.
  - Bloom difficulty selector (`REMEMBER`, `UNDERSTAND`, `APPLY`).
  - Points input (default 1.0, step 0.5).
  - Explanation textarea.
- `#editQuestionModal`:
  - Populated via JavaScript when clicking "Chỉnh sửa" on a question row.
  - Allows editing question content, choices, answers, and points.
- `#importDocumentModal`:
  - File input accepting `.pdf, .docx, application/pdf, application/vnd.openxmlformats-officedocument.wordprocessingml.document`.
  - Explanatory note on supported formats and automatic question extraction.
  - Submit button with upload progress indicator.

---

### 3.2 R5: Context-Aware Grounded AI & Course Recommendations

#### 1. Client-Side Location Detection & Transmission (`app_shell.js`):
- Enhance `app_shell.js`:
  ```javascript
  function getActiveContext() {
    const path = window.location.pathname;
    let courseId = document.querySelector('meta[name="active-course-id"]')?.content || null;
    let lessonId = document.querySelector('meta[name="active-lesson-id"]')?.content || null;

    if (!courseId) {
      const courseMatch = path.match(/\/courses\/([0-9a-fA-F-]+)/);
      if (courseMatch) courseId = courseMatch[1];
    }
    if (!lessonId) {
      const lessonMatch = path.match(/\/lessons\/([0-9a-fA-F-]+)/);
      if (lessonMatch) lessonId = lessonMatch[1];
    }

    return {
      page_route: path,
      page_title: document.title,
      course_id: courseId,
      lesson_id: lessonId
    };
  }
  ```
- In `sendFloatingAIMessage()`:
  Include `getActiveContext()` fields in payload sent to `/student/ai/chat`.

#### 2. Dynamic Conversation Scoping in Backend:
- In `src/pwd301/blueprints/student/routes.py:student_ai_chat`:
  - Read `course_id`, `lesson_id`, `page_route`, `page_title` from payload.
  - Determine `desired_context_type = "LESSON" if lesson_id else ("COURSE" if course_id else "GLOBAL")`.
  - Compare `desired_context_type` and `course_id` with `conv`:
    If `conv is None` or `conv.context_type != desired_context_type` or (conv.course and str(conv.course.public_id) != str(course_id)):
      - Automatically create or switch to a scoped conversation for that course/lesson.
      - Update `session["active_ai_conversation_id"] = str(new_conv.public_id)`.

#### 3. Grounded Semantic RAG Retrieval:
- In `src/pwd301/services/ai_service.py:send_chat_message`:
  - When `conv.context_type in ("COURSE", "LESSON")` and `conv.course_id`:
    - Call `retrieve_relevant_chunks(actor, conv.course_id, sanitized_content, top_k=3, session=sess)`.
    - If relevant chunks exist:
      - Format chunks using `_format_context_boundary_blocks(retrieved_items)`.
      - Pass `retrieved_chunks_context` into `client.chat_response(...)` (or `client.answer_rag_query(...)`).
      - Parse citations `[Ref: <UUID>]` from the response.
      - Persist `AISourceUsage` records linked to `ai_requests`.
- In `app_shell.js`:
  - Render citation badges:
    `[Ref: <UUID>]` rendered as clickable pill showing source lesson title and snippet.

#### 4. Course Catalog Knowledge & Recommendation Engine:
- In `src/pwd301/services/ai_service.py` / `gemini_service.py`:
  - Intent classification:
    - If user query on course page matches `"đây là khóa học gì"` / `"môn học này là gì"`:
      - Extract course title, code, description, objectives, and prerequisites from `conv.course`.
      - Formulate accurate pedagogical response describing the current course.
    - If user query on main page / GLOBAL matches `"gợi ý khóa học"` / `"nên học môn gì"` / `"recommend courses"`:
      - Call `generate_course_recommendations(actor, limit=3, session=sess)`.
      - Format recommended courses with title, code, difficulty, and reasons into the assistant response.

---

## 4. Caveats

1. **Active Attempt Concurrency**:
   - In accordance with Invariant 14 (`BR-030`), once the first student starts an attempt on an assessment (`first_attempt_started_at is not None`), question assignments and points are locked. Sponsoring instructors who need to fix questions on an active exam must use `QuestionCorrection` and trigger background regrading (`Algorithm 11`), not direct assessment editing.
2. **File Formats for Document Import**:
   - `import_service.py` supports PDF and DOCX documents (pure text, structured blocks with numbering `Câu 1:` / `Question 1:` and option letters `A.`, `B.`, `C.`, `D.`). Scanned image PDFs without OCR are out of scope for the native text extractor and will yield 0 parsed question blocks.
3. **Gemini Client Mode**:
   - In testing and offline development environments without live Gemini API keys, `MockGeminiClient` is used. All response synthesis, citation formatting, and recommendation logic must function deterministically in `MockGeminiClient` as well as in `RealGeminiClient`.

---

## 5. Conclusion

- **R3**: The platform already has robust domain services for Question Bank (`question_bank_service.py`), Assessment Questions (`assessment_service.py`), and Document Import (`import_service.py`), including strong Timing Lock and Structural Freeze invariants. The primary missing links are:
  1. The UI authoring and in-place editing components on `instructor/assessment_builder.html`.
  2. The assessment-scoped direct authoring endpoint and direct document import endpoint.
  3. Connecting `draft_assessment_id` through `import_service.py:create_import_job` and auto-assigning imported questions upon completion.
- **R5**: The platform has a complete RAG indexing, chunking, and retrieval engine (`rag_service.py`) and an Algorithm 14 Course Recommendation Engine (`recommendation_service.py`). The primary missing links are:
  1. `app_shell.js` extracting and transmitting active page context (`page_route`, `page_title`, `course_id`, `lesson_id`).
  2. Dynamic conversation scope switching in `student/routes.py:student_ai_chat` (stopping session stickiness to GLOBAL).
  3. Wiring RAG retrieval and citation extraction into the conversational chat pipeline for course/lesson scopes.
  4. Wiring Course Catalog knowledge and recommendation engine into the AI Assistant for catalog-aware and recommendation responses.

---

## 6. Verification Method

### 6.1 Automated Verification Commands
Execute the following verification commands from the project root (`e:\PWD301`):

```powershell
# 1. Verify Repository Contracts
python scripts/repo_check.py

# 2. Verify Assessment Service & API Tests
python -m pytest tests/api/test_assessment_api.py tests/unit/test_assessment_service.py tests/security/test_assessment_timezone_security.py -v

# 3. Verify Question Bank & Revision Tests
python -m pytest tests/api/test_question_bank_api.py tests/api/test_question_revision_api.py tests/unit/test_question_bank_service.py -v

# 4. Verify Document Import Tests
python -m pytest tests/api/test_import_api.py tests/unit/test_import_service.py -v

# 5. Verify AI, RAG & Recommendation Tests
python -m pytest tests/api/test_ai_api.py tests/unit/test_ai_service.py tests/unit/test_rag_service.py tests/security/test_ai_scope_enforcement.py -v

# 6. Combined R3 & R5 Test Suite
python -m pytest tests/api/test_assessment_api.py tests/unit/test_assessment_service.py tests/api/test_import_api.py tests/unit/test_import_service.py tests/api/test_ai_api.py tests/unit/test_ai_service.py tests/unit/test_rag_service.py -v
```

### 6.2 Manual & Programmatic Acceptance Verification
1. **Assessment Direct Authoring & In-Place Editing**:
   - Create a draft assessment.
   - Click "+ Tạo câu hỏi mới", fill in Single Choice question, save -> verify question appears in table and total points increment.
   - Click "Chỉnh sửa" on a question -> change choice text and points -> verify updated in DB and UI.
   - Start a student attempt on the assessment -> reload assessment builder -> verify structural freeze banner is displayed and add/edit/remove buttons are disabled.
2. **Assessment Document Import**:
   - Upload sample DOCX / PDF with questions from assessment page -> verify questions are parsed and assigned directly to the assessment.
3. **Context-Aware AI Assistant & Citations**:
   - Open `/student/courses/<course_id>` -> open AI chat -> ask "đây là khóa học gì" -> verify AI identifies the exact course title and code.
   - Ask a question about course lesson material -> verify AI answer contains citation `[Ref: <UUID>]` and citation badge rendered.
   - Navigate to `/` (home) -> ask "gợi ý cho tôi khóa học phù hợp" -> verify AI recommends courses based on student profile and catalog.
