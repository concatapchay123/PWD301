# Handoff Report: Milestone 3 Backend Architecture Exploration
**Subagent**: `explorer_m3_1` (Milestone 3 Backend Architecture Explorer)  
**Parent Conversation ID**: `5f234e51-df3a-4989-b3f8-7adc52e9513d`  
**Date**: 2026-09-14  
**Target Milestone**: Milestone 3 (R3: Assessment Page Question Authoring, Direct Editing & Document Import)  

---

## 1. Observation

### 1.1 Existing Data Models
1. **Assessment & Question Assignment Models** (`src/pwd301/models/assessment.py`):
   - `Assessment` (lines 30–207):
     - Internal PK `id: BigIntPK`, public ID `public_id: GUID` (ADR-002).
     - Course scope `course_id: BigInt` (FK `courses.id`).
     - Invariant flags: `published_at: UTCDateTime` (Timing Lock — BR-031 / Invariant 13), `first_attempt_started_at: UTCDateTime` (Structural Freeze — BR-030 / Invariant 14).
     - Relationships: `question_assignments` to `AssessmentQuestionAssignment` with `cascade="all, delete-orphan"`, ordered by `position`.
   - `AssessmentQuestionAssignment` (lines 235–300):
     - Table `assessment_question_assignments`.
     - Fields: `assessment_id: BigInt`, `question_id: BigInt`, `section_id: BigInt` (nullable), `position: Integer`, `points: Numeric(9, 4)`, `is_mandatory: Boolean`, `shuffle_choices_override: Boolean`, `source_type: String(20)` (`MANUAL`, `BANK`, `IMPORT`, `AI`).
     - Unique constraint: `(assessment_id, question_id)`.

2. **Question & Revision Models** (`src/pwd301/models/question_bank.py`):
   - `Question` (lines 29–137):
     - `course_id: BigInt`, `lesson_id: BigInt` (nullable), `difficulty: String(20)` (`REMEMBER`, `UNDERSTAND`, `APPLY`), `status: String(20)` (`DRAFT`, `ACTIVE`, `RETIRED`, `TRASH`), `usage_count: BigInt`, `first_used_at: UTCDateTime`, `first_answered_at: UTCDateTime`.
     - Relationship: `revisions` to `QuestionRevision`, `current_revision` where `is_current == True`.
   - `QuestionRevision` (lines 139–285):
     - `question_id: BigInt`, `revision_no: Integer`, `is_current: Boolean`.
     - `question_type: String(24)` in (`SINGLE_CHOICE`, `MULTIPLE_CHOICE`, `TRUE_FALSE`, `SHORT_ANSWER`, `ESSAY`).
     - `content: NVarCharMax` (aliased as `prompt_markdown` or `stem`).
     - `explanation: NVarCharMax`.
     - `short_answer_match_mode: String(16)` in (`NORMALIZED`, `EXACT`).
     - `change_type: String(24)`, `change_reason: Unicode(1000)`.
     - `was_student_exposed: Boolean`, `was_used_for_grading: Boolean`.
     - Relationships: `choices` (`QuestionRevisionChoice`), `accepted_answers` (`QuestionRevisionAcceptedAnswer`).
   - `QuestionRevisionChoice` / `QuestionChoice` (lines 286–362):
     - `choice_key: GUID` (aliased as `public_id`), `content: NVarCharMax`, `is_correct: Boolean`, `position: Integer`, `is_fixed_position: Boolean`.

3. **Document Import Models** (`src/pwd301/models/file_import.py`):
   - `DocumentImportJob` (lines 586–704):
     - Table `document_import_jobs`.
     - Fields: `course_id: BigInt`, `source_file_asset_id: BigInt`, `requested_by_user_id: BigInt`.
     - **Already present in schema and model**:
       Line 614: `draft_assessment_id = db.Column(sa.BigInteger, sa.ForeignKey("assessments.id", name="fk_document_import_jobs_draft_assessment_id", ondelete="SET NULL"), nullable=True)`.
       Line 678: `draft_assessment = relationship("Assessment", foreign_keys=[draft_assessment_id])`.
     - `document_type: String(8)` (`DOCX`, `PDF`), `status: String(24)` (`QUEUED`, `PROCESSING`, `REVIEW_REQUIRED`, `COMPLETED`, `FAILED`, `CANCELLED`).
   - `ImportQuestion` (lines 705–750):
     - `import_job_id: BigInt`, `ordinal: Integer`, `detected_type: String(24)`, `content_text: NVarCharMax`, `choices_json: NVarCharMax`, `detected_answer_json: NVarCharMax`, `explanation_text: NVarCharMax`, `review_state: String(20)` (`READY`, `NEEDS_REVIEW`, `ACCEPTED`, `REJECTED`, `EDITED`), `approved_question_id: BigInt`.

### 1.2 Existing Service Logic
1. **Assessment Service** (`src/pwd301/services/assessment_service.py`):
   - `assign_question(actor, assessment_id, payload, session)` (lines 1306–1412):
     - Resolves assessment, validates actor is course manager (`require_course_manager`).
     - Structural freeze check: `if assessment.first_attempt_started_at is not None: raise AssessmentLockedError(...)`.
     - Validates `question.course_id == assessment.course_id`.
     - Checks duplicate assignment `uq_assessment_question_assignments_assessment_id_question_id_1`.
     - Validates positive `points` (defaults to 1.0).
     - Inserts `AssessmentQuestionAssignment(source_type=payload.get("source_type", "BANK"))`.
   - `remove_question_assignment(actor, assessment_id, question_id, session)` (lines 1415–1466):
     - Enforces `first_attempt_started_at is None`.
     - Deletes assignment and shifts subsequent positions.
   - `update_question_assignment(actor, assessment_id, question_id, payload, session)` (lines 1468–1540):
     - Enforces `first_attempt_started_at is None`.
     - Updates `points` and `position`.

2. **Question Bank Service** (`src/pwd301/services/question_bank_service.py`):
   - `create_question(actor, course_id, payload, session)` (lines 318–658):
     - Validates question type (`SINGLE_CHOICE`, `MULTIPLE_CHOICE`, `TRUE_FALSE`, `SHORT_ANSWER`, `ESSAY`), difficulty (`REMEMBER`, `UNDERSTAND`, `APPLY`), content, choices, accepted answers.
     - Creates `Question` (status `ACTIVE`) + `QuestionRevision` (revision 1) + choices/accepted answers.
     - Records append-only `AuditEvent(action="QUESTION_CREATED")`.
   - `is_question_in_use(question_or_id, session)` (lines 952–1040):
     - Returns `True` if question has appeared in any `AttemptQuestion`, or is assigned to a `PUBLISHED` assessment, or is in an assessment question pool of a `PUBLISHED` assessment, or `usage_count > 0`, or has student answers/exposure.
   - `update_question(actor, question_id, payload, session)` (lines 1477–1670):
     - If `is_question_in_use(question)` is True:
       - Raises `QuestionImmutableError` if attempting to change `question_type`.
       - If content/choices/answers are modified, automatically calls `create_question_revision(actor, question.id, payload)` with `change_reason`, creating a new revision (e.g. revision 2) while keeping historical revisions intact!
     - If question is NOT in use:
       - Updates current revision content, explanation, choices, and accepted answers in-place!

3. **Import Service** (`src/pwd301/services/import_service.py`):
   - `create_import_job(actor, course_id, file_asset_id, draft_assessment_id=None, session=None)` (lines 829–928):
     - Line 833 accepts `draft_assessment_id`, but **omitted saving it**: `job = DocumentImportJob(...)` at line 911 does NOT set `draft_assessment_id=...`!
   - `process_import_job(actor, job_id, session=None)` (lines 930–1079):
     - Parses DOCX or PDF into `ImportQuestion` instances with `review_state="READY"`.
   - `commit_import_job(actor, job_id, session=None)` (lines 1222–1338):
     - Iterates through `ImportQuestion` with `review_state == "ACCEPTED"`.
     - Calls `create_question(...)` for each question to save it into the Course Question Bank.
     - **Omitted auto-assigning**: Does NOT check `if job.draft_assessment_id` to link created questions to the draft assessment!

### 1.3 Web Routes and Templates
1. **Instructor Routes** (`src/pwd301/blueprints/instructor/routes.py`):
   - Has `POST /assessments/<assessment_id>/questions` (line 1594) which only assigns an existing `question_id`.
   - Has `POST /courses/<course_id>/imports` (line 1880) which creates course-level imports.
   - **Missing**:
     - `POST /instructor/assessments/<assessment_id>/questions/create`
     - `POST /instructor/assessments/<assessment_id>/questions/<question_id>/edit`
     - `POST /instructor/assessments/<assessment_id>/import`
2. **Assessment Builder Template** (`src/pwd301/templates/instructor/assessment_builder.html`):
   - Lines 150–155 only has button `+ Thêm câu hỏi từ Ngân hàng` opening `#addQuestionModal`.
   - Lines 188–198 in question table only has button `Gỡ bỏ` (unassign).
   - **Missing**:
     - `+ Tạo câu hỏi mới` button and modal with support for 4 question types (Single Choice, Multiple Choice, True/False, Short Answer), custom points, choices, and explanations.
     - `Sửa` (in-place edit) button and modal for each assigned question.
     - `Upload PDF/DOCX tạo đề tự động` button and upload modal.

---

## 2. Logic Chain

1. **Direct In-Page Question Creation**:
   - Step 1: Instructor on assessment builder submits a new question form to `POST /instructor/assessments/<assessment_id>/questions/create`.
   - Step 2: Route verifies actor manages `assessment.course_id` and verifies `assessment.first_attempt_started_at is None` (Structural Freeze BR-030).
   - Step 3: Route constructs payload:
     - `question_type`: `SINGLE_CHOICE`, `MULTIPLE_CHOICE`, `TRUE_FALSE`, `SHORT_ANSWER`.
     - `content`: question prompt/stem text.
     - `difficulty`: `REMEMBER`, `UNDERSTAND`, `APPLY` (defaults to `UNDERSTAND`).
     - `points`: Decimal points (e.g. 1.0, 2.0).
     - `explanation`: optional explanation markdown.
     - `choices`: parsed list of `{"content": ..., "is_correct": bool, "position": int}`.
     - `accepted_answers`: list of strings for Short Answer.
   - Step 4: Route calls `created_q = create_question(actor=actor, course_id=assessment.course_id, payload=q_payload, session=db.session)`.
   - Step 5: Route calls `assign_question(actor=actor, assessment_id=assessment.id, payload={"question_id": created_q.public_id, "points": points, "source_type": "MANUAL"}, session=db.session)`.
   - Step 6: Returns redirect with success flash (or JSON 201). This eliminates the need to navigate away to the Question Bank.

2. **In-Place Question Editing**:
   - Step 1: Instructor clicks "Sửa" on a question in the assessment question list and submits to `POST /instructor/assessments/<assessment_id>/questions/<question_id>/edit`.
   - Step 2: Route verifies `assessment.first_attempt_started_at is None`. If student attempts have begun, raising `AssessmentLockedError` is mandatory because assessment question structure and points are immutable (BR-030).
   - Step 3: If `points` changed, route calls `update_question_assignment(actor, assessment.id, question.id, {"points": points}, session=db.session)`.
   - Step 4: For question content, choices, or explanation:
     - Route calls `update_question(actor, question.id, payload, session=db.session)` with `change_reason = payload.get("change_reason") or "Direct edit from assessment builder"`.
     - Inside `update_question`, `is_question_in_use(question)` determines behavior:
       - If unused (only in draft assessment, no attempts): updates current revision in-place.
       - If in-use (already published in other assessments or previous attempts): automatically branches a new revision (`create_question_revision`) with `change_reason`, guaranteeing historical test stability and zero data loss.
   - Step 5: Returns redirect with success flash (or JSON 200).

3. **PDF/DOCX Document Import Pipeline**:
   - Step 1: Instructor uploads `.docx` or `.pdf` file on assessment builder via `POST /instructor/assessments/<assessment_id>/import`.
   - Step 2: Route stores the file stream as an `IMPORT_SOURCE` file asset via `store_file_stream(...)`.
   - Step 3: Route invokes `create_import_job(actor, course_id, file_asset_id, draft_assessment_id=assessment.id)`.
     - In `create_import_job` (`import_service.py`): persist `job.draft_assessment_id = draft_assessment.id`.
   - Step 4: Route invokes `process_import_job(actor, job.public_id)`.
   - Step 5: Route automatically sets `iq.review_state = "ACCEPTED"` for all parsed questions with state in `("READY", "ACCEPTED")`.
   - Step 6: Route calls `commit_import_job(actor, job.public_id)`.
     - In `commit_import_job` (`import_service.py`):
       When `job.draft_assessment_id` is set, after creating each question via `create_question(...)`, immediately call `assign_question(actor=actor, assessment_id=job.draft_assessment_id, payload={"question_id": created_q.id, "points": points, "source_type": "IMPORT"})`.
   - Step 7: Redirects with flash message: `Đã import thành công X câu hỏi từ tài liệu vào đề thi!`.

4. **Timing Lock and Structural Freeze Invariant Enforcement**:
   - Timing Lock (BR-031 / Invariant 13):
     - Trigger: `assessment.status == "PUBLISHED"` or `assessment.published_at is not None`.
     - Lock: `open_at`, `time_limit_minutes`, `attempt_limit` cannot be modified. `close_at` can only be extended forward.
     - Already enforced in `update_assessment` (`assessment_service.py:664–707`).
   - Structural Freeze (BR-030 / Invariant 14):
     - Trigger: `assessment.first_attempt_started_at is not None`.
     - Lock: No questions may be created, added, edited, removed, or have their points modified.
     - Enforced across `assign_question`, `remove_question_assignment`, `update_question_assignment`, and the new direct create, edit, and import endpoints.

---

## 3. Caveats

1. **Short Answer normalization**: In `question_bank_service.py:528`, short answer strings are normalized to lowercase. Ensure frontend authoring accepts comma-separated or multiline strings cleanly without trailing whitespace.
2. **File scanning in development vs production**: `store_file_stream` marks newly stored files as `CLEAN` in standard environments or enqueues `FILE_SCAN`. The import service checks `file_asset.status == "ACTIVE"` and `file_revision.status == "ACTIVE"`. Ensure `store_file_stream` creates the active revision properly (as fixed in M1).
3. **Question duplication handling on import**: If a document contains duplicate questions or duplicates existing questions in the bank, `detect_duplicates` flags them. Auto-approving questions on assessment import should accept questions with `review_state == 'READY'` while skipping or safely handling exact duplicate questions that fail `assign_question`.

---

## 4. Conclusion & Recommended Implementation Plan for Worker

The Worker should perform the following changes in order:

### Step 1: Update Import Service (`src/pwd301/services/import_service.py`)
1. In `create_import_job(actor, course_id, file_asset_id, draft_assessment_id=None, session=None)`:
   - Resolve `draft_assessment_id` using `_resolve_assessment(draft_assessment_id, session=sess)`.
   - If provided, verify `draft_assessment.course_id == course.id` and `draft_assessment.first_attempt_started_at is None`.
   - Assign `draft_assessment_id=draft_assessment.id if draft_assessment else None` when instantiating `DocumentImportJob`.
2. In `commit_import_job(actor, job_id, session=None)`:
   - If `job.draft_assessment_id` is set:
     - For each created question (`created_q`), call:
       ```python
       from pwd301.services.assessment_service import assign_question
       with contextlib.suppress(Exception):
           assign_question(
               actor=actor,
               assessment_id=job.draft_assessment_id,
               payload={
                   "question_id": created_q.id,
                   "points": points or 1.0,
                   "source_type": "IMPORT",
               },
               session=sess,
           )
       ```

### Step 2: Implement Assessment Endpoints in Instructor Blueprint (`src/pwd301/blueprints/instructor/routes.py`)
Add 3 new endpoints:
1. `POST /instructor/assessments/<assessment_id>/questions/create`:
   - Enforce `@instructor_required` and CSRF protection.
   - Check `assessment.first_attempt_started_at is None` (raises `AssessmentLockedError`).
   - Extract `question_type`, `content`, `difficulty`, `points`, `explanation`, `choices`, `accepted_answers`.
   - Call `create_question(...)` then `assign_question(...)`.
   - Return redirect with flash (HTML) or 201 JSON.
2. `POST /instructor/assessments/<assessment_id>/questions/<question_id>/edit`:
   - Enforce `@instructor_required` and CSRF protection.
   - Check `assessment.first_attempt_started_at is None`.
   - Update points via `update_question_assignment(...)`.
   - Update content/choices/answers via `update_question(...)` with default `change_reason="Direct edit from assessment builder"`.
   - Return redirect with flash (HTML) or 200 JSON.
3. `POST /instructor/assessments/<assessment_id>/import`:
   - Enforce `@instructor_required` and CSRF protection.
   - Check `assessment.first_attempt_started_at is None`.
   - Extract uploaded file (`request.files["file"]`).
   - Call `store_file_stream(..., asset_type="IMPORT_SOURCE")`.
   - Call `create_import_job(..., draft_assessment_id=assessment.id)`.
   - Call `process_import_job(...)`.
   - Auto-accept ready questions (`iq.review_state = "ACCEPTED"`).
   - Call `commit_import_job(...)`.
   - Return redirect with flash (HTML) or 201/202 JSON.

### Step 3: Implement UI in Assessment Builder (`src/pwd301/templates/instructor/assessment_builder.html`)
1. In the header action bar (or questions tab header):
   - Add button `+ Tạo câu hỏi mới` (opens `#createQuestionModal`).
   - Add button `Upload PDF/DOCX tạo đề tự động` (opens `#importDocumentModal`).
2. Add `#createQuestionModal`:
   - Form posting to `/instructor/assessments/{{ assessment.public_id }}/questions/create`.
   - Type selector: Single Choice, Multiple Choice, True/False, Short Answer.
   - Dynamic choice inputs with radio/checkbox for correct answers.
   - Accepted answer input for Short Answer.
   - Prompt textarea, explanation textarea, points input, difficulty selector.
3. In the questions table (`<tbody>`):
   - Add `Sửa` (Edit) button next to `Gỡ bỏ`.
   - Add edit modal / offcanvas or JS modal populated with question data that posts to `/instructor/assessments/{{ assessment.public_id }}/questions/{{ q_item.question.public_id }}/edit`.
4. Add `#importDocumentModal`:
   - Form posting to `/instructor/assessments/{{ assessment.public_id }}/import` with `enctype="multipart/form-data"`.
   - File input accepting `.docx, .pdf`.
   - Explanatory guide on format and automatic question assignment.

### Step 4: Write Comprehensive Integration Tests
Create `tests/api/test_m3_assessment_direct_authoring.py`:
- Test 1: Direct question creation on assessment with Single Choice, Multiple Choice, True/False, Short Answer.
- Test 2: In-place editing of question content & points; verify revision branching when question is in use.
- Test 3: PDF / DOCX upload to assessment with `draft_assessment_id` and auto-assignment.
- Test 4: Timing lock and structural freeze immutability enforcement.

---

## 5. Verification Method

To independently verify the implementation:

1. **Run automated unit tests for assessment service**:
   ```powershell
   pytest tests/unit/test_assessment_service.py -v
   ```
2. **Run automated unit tests for import service**:
   ```powershell
   pytest tests/unit/test_import_service.py -v
   ```
3. **Run new Milestone 3 integration tests**:
   ```powershell
   pytest tests/api/test_m3_assessment_direct_authoring.py -v
   ```
4. **Run full repository verification suite**:
   ```powershell
   pytest tests/ -k "assessment or import or question" -v
   ```
