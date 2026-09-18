# Handoff Report — explorer_m3_2: Milestone 3 (R3) UI & Route Architecture

## 1. Observation

### 1.1 Existing Assessment Builder Template (`src/pwd301/templates/instructor/assessment_builder.html`)
- **Current Question Controls**:
  - Line 121–140: Three tabs exist: `#tab-questions` (Nội dung & Câu hỏi), `#tab-settings` (Thông số & Thời lượng), and `#tab-regrade` (Chấm lại & Đính chính).
  - Line 150–155: In `#tab-questions`, only a single button exists:
    ```html
    {% if not structure_locked %}
    <button class="btn btn-primary btn-sm d-flex align-items-center gap-2" data-bs-toggle="modal" data-bs-target="#addQuestionModal">
      <svg ...>...</svg>
      + Thêm câu hỏi từ Ngân hàng
    </button>
    {% endif %}
    ```
  - Lines 158–201: Questions table renders `assessment.question_assignments`.
    - Columns: `#`, `Nội dung câu hỏi`, `Độ khó`, `Điểm phân bổ`, `Thao tác`.
    - `Điểm phân bổ` is rendered as static text: `<span class="fw-bold text-primary">{{ q_item.points }}</span> điểm`.
    - `Thao tác` only has a removal form: `POST /instructor/assessments/{{ assessment.public_id }}/questions/{{ q_id }}/remove`.
    - There is **no in-place question edit button**, **no inline points editor**, **no "+ Tạo câu hỏi mới" direct authoring modal**, and **no "Upload PDF/DOCX tạo đề tự động" import modal or button**.
  - Lines 366–412: Modal `#addQuestionModal` only lists existing course questions from `available_questions` to assign into the exam.
  - Variable mismatch observation: In `get_instructor_assessment_detail_route` (`src/pwd301/blueprints/instructor/routes.py`: 1374–1380), `render_template` passes `assessment=data` (from `_serialize_assessment(full=True)`). `data` contains `"assessment_id"` and `"questions"`, but lacks `"public_id"` and `"question_assignments"`. In `assessment_builder.html`, line 50, 65, 72, 80, 190, 224, 349 access `assessment.public_id` (evaluating to empty string), and line 158, 172 check `assessment.question_assignments` (evaluating to empty/none). Fortunately, `asm_obj` is passed as well (`asm_obj=asm_obj`).

### 1.2 Existing Instructor Web Routes (`src/pwd301/blueprints/instructor/routes.py`)
- Lines 1354–1381: `GET /assessments/<assessment_id>` renders `instructor/assessment_builder.html`.
- Lines 1594–1621: `POST /assessments/<assessment_id>/questions` (`assign_instructor_question_route`) assigns an existing Question to an assessment with custom `points`.
- Lines 1624–1650: `POST /assessments/<assessment_id>/questions/<question_id>/remove` removes an assigned question.
- Lines 1874–1928: `POST /courses/<course_id>/imports` (`instructor_create_course_import`) uploads DOCX/PDF to create a course import job, but is course-scoped and does not bind to an active `draft_assessment_id`.
- **Missing Endpoints for M3 / R3**:
  - `POST /instructor/assessments/<assessment_id>/questions/create`: Direct creation of questions (Single Choice, Multiple Choice, True/False, Short Answer) with automatic assignment to the assessment.
  - `POST /instructor/assessments/<assessment_id>/questions/<question_id>/edit`: Direct in-place editing of question content, choices, explanation, or assigned points.
  - `POST /instructor/assessments/<assessment_id>/import`: Direct PDF/DOCX file upload to auto-generate and auto-assign questions to this specific assessment.

### 1.3 Service Layer Capabilities & Pipeline Gaps
- `src/pwd301/services/question_bank_service.py`:
  - Lines 313–520: `create_question()` cleanly supports all question types: `SINGLE_CHOICE`, `MULTIPLE_CHOICE`, `TRUE_FALSE`, `SHORT_ANSWER`, `ESSAY`, and difficulties `REMEMBER`, `UNDERSTAND`, `APPLY`.
  - Lines 1477–1550: `update_question()` handles updates: if the question is in use, it creates a new revision; if unused, it edits in place.
- `src/pwd301/services/assessment_service.py`:
  - Lines 1306–1380: `assign_question()` assigns a question to an assessment, enforcing that `first_attempt_started_at is None` (Structural Freeze - Invariant 14).
  - Lines 1468–1530: `update_question_assignment()` updates points/position on an assignment, enforcing `first_attempt_started_at is None`.
- `src/pwd301/services/import_service.py`:
  - Line 829: `create_import_job(actor, course_id, file_asset_id, draft_assessment_id=...)` accepts `draft_assessment_id`, BUT line 911–920 creates `DocumentImportJob(...)` without passing `draft_assessment_id`!
  - `DocumentImportJob` (`src/pwd301/models/file_import.py`: 614–622) has `draft_assessment_id = db.Column(sa.BigInteger, sa.ForeignKey("assessments.id", ...), nullable=True)`.
  - In `commit_import_job()` (`src/pwd301/services/import_service.py`: 1222–1325), when `job.draft_assessment_id` is present, it does not currently invoke `assign_question()` to automatically assign the imported questions to the target draft assessment.

### 1.4 Frontend Design Standards (`frontend-preview/assets/js/views/instructor.js`)
- Lines 709–943 (`assessmentBuilder`): Demonstrates lock state simulation and banners for Invariant 13 (Timing Lock) and Invariant 14 (Structural Freeze).
- Lines 507–605 (`questionEditor`): Shows form inputs for stem, question type (`single_choice`, `multi_select`, `short_answer`), difficulty, topic, and audit change reason.

---

## 2. Logic Chain

1. **Direct Question Authoring**:
   - Instructors on `instructor/assessment_builder.html` need to author questions on the fly without navigating away.
   - The "+ Tạo câu hỏi mới" button triggers `#createQuestionModal`.
   - The modal dynamically renders choice inputs for `SINGLE_CHOICE` (radio for 1 correct), `MULTIPLE_CHOICE` (checkboxes for multiple correct), `TRUE_FALSE` (True/False toggle), and `SHORT_ANSWER` (accepted answer text with match type).
   - On submission to `POST /instructor/assessments/<assessment_id>/questions/create`, the endpoint:
     - Enforces Invariant 14 (`if asm_obj.first_attempt_started_at is not None: raise AssessmentLockedError`).
     - Invokes `create_question()` on the course question bank with provenance `{"source_type": "MANUAL", "notes": f"Created directly from assessment {asm_obj.public_id}"}`.
     - Invokes `assign_question()` with the assigned points.
     - Flashes success and redirects back to `#tab-questions`.

2. **In-Place Question & Points Editing**:
   - Points editing: Instructors need quick adjustment of question points (e.g. 1.0 -> 2.0). An inline numeric form or quick-edit input on each question row posts to `/instructor/assessments/<assessment_id>/questions/<question_id>/edit`.
   - Content editing: An "Sửa câu hỏi" button opens `#editQuestionModal` pre-populated with stem, difficulty, choices, explanation, and points.
   - The route `POST /instructor/assessments/<assessment_id>/questions/<question_id>/edit`:
     - Checks Invariant 14 (Structural Freeze).
     - If points changed: calls `update_question_assignment(actor, assessment_id, question_id, {"points": points})`.
     - If content changed: calls `update_question(actor, question_id, payload)`.
     - Returns 200 / redirects with flash.

3. **Document Import Pipeline (PDF/DOCX)**:
   - "Upload PDF/DOCX tạo đề tự động" button triggers `#importDocumentModal`.
   - The modal accepts `.docx` and `.pdf` files and provides a checkbox `auto_commit` (default checked).
   - The route `POST /instructor/assessments/<assessment_id>/import`:
     - Checks Invariant 14 (`first_attempt_started_at is None`).
     - Calls `store_file_stream()` to save the file with `asset_type="IMPORT_SOURCE"`.
     - Calls `create_import_job(..., draft_assessment_id=asm_obj.id)`.
     - Calls `process_import_job()`.
     - If `auto_commit`: marks parsed questions as `ACCEPTED`, calls `commit_import_job()`.
   - Fixing `import_service.py`:
     - In `create_import_job`: assign `job.draft_assessment_id = target_assessment.id`.
     - In `commit_import_job`: if `job.draft_assessment_id` is set, iterate created questions and invoke `assign_question()` to link each question to the assessment.

4. **Security, CSRF & Template Data Binding**:
   - Ensure `get_instructor_assessment_detail_route` sets `data["public_id"] = str(asm_obj.public_id)`, `data["assessment_id"] = str(asm_obj.public_id)`, and `data["question_assignments"] = asm_obj.question_assignments`.
   - All forms include `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`.
   - Timing lock (`published_at is not None`) and structural freeze (`first_attempt_started_at is not None`) disable editing controls with descriptive tooltips and alert banners.

---

## 3. Caveats

1. **Legacy Test Suite Scope**:
   - Existing `tests/api/test_assessment_api.py` and `tests/unit/test_assessment_service.py` test JWT REST endpoints. The new endpoints are Web session endpoints on `instructor_bp` requiring Flask session authentication and CSRF tokens.
2. **File Size Limit for Documents**:
   - `store_file_stream` validates file formats (.docx, .pdf) and size limits (< 1 GB for videos, standard limit for documents).
3. **Question Type Mutations on In-Use Questions**:
   - Invariant 6 forbids changing the `question_type` of an in-use question once answered. The in-place editor must disable the `question_type` select if the question is already in use.

---

## 4. Conclusion & Actionable Implementation Plan for Worker M3

### File 1: `src/pwd301/services/import_service.py`
1. **Fix `create_import_job`**:
   - Lines 845–850: Resolve `draft_assessment_id` if provided:
     ```python
     target_assessment: Assessment | None = None
     if draft_assessment_id is not None:
         from pwd301.services.assessment_service import _resolve_assessment
         target_assessment = _resolve_assessment(draft_assessment_id, session=sess)
     ```
   - Line 911: Set `draft_assessment_id = target_assessment.id if target_assessment else None` on `DocumentImportJob`.
2. **Upgrade `commit_import_job`**:
   - After line 1320 (where `created_q` is created):
     ```python
     if job.draft_assessment_id is not None:
         from pwd301.models.assessment import Assessment, AssessmentQuestionAssignment
         from pwd301.services.assessment_service import assign_question
         draft_asm = sess.get(Assessment, job.draft_assessment_id)
         if draft_asm and draft_asm.first_attempt_started_at is None:
             existing_asm = (
                 sess.query(AssessmentQuestionAssignment)
                 .filter(
                     AssessmentQuestionAssignment.assessment_id == draft_asm.id,
                     AssessmentQuestionAssignment.question_id == created_q.id,
                 )
                 .first()
             )
             if existing_asm is None:
                 assign_question(
                     actor=actor,
                     assessment_id=draft_asm.id,
                     payload={"question_id": created_q.id, "points": points},
                     session=sess,
                 )
     ```

### File 2: `src/pwd301/blueprints/instructor/routes.py`
1. **Fix `get_instructor_assessment_detail_route`**:
   - Ensure `data["public_id"] = str(asm_obj.public_id)`
   - Ensure `data["assessment_id"] = str(asm_obj.public_id)`
   - Ensure `data["question_assignments"] = asm_obj.question_assignments`
2. **Add `POST /assessments/<assessment_id>/questions/create`**:
   ```python
   @instructor_bp.route("/assessments/<assessment_id>/questions/create", methods=["POST"])
   @instructor_required
   def create_assessment_question_route(assessment_id: str) -> Any:
       """Directly create and assign a question to an assessment."""
       actor = require_authenticated_actor()
       asm_obj = _resolve_assessment(assessment_id, session=db.session)
       if asm_obj is None:
           raise ResourceNotFoundError(f"Assessment '{assessment_id}' not found.")
       
       require_course_manager(actor, asm_obj.course_id, session=db.session)
       
       if asm_obj.first_attempt_started_at is not None:
           raise AssessmentLockedError("Cấu trúc đề thi đã bị khóa (Structural Freeze - Invariant 14).")
           
       payload = request.get_json(silent=True) or request.form.to_dict() or {}
       # Parse choices / accepted answers per question_type...
       # Call create_question(actor, asm_obj.course_id, payload, session=db.session)
       # Call assign_question(actor, asm_obj.id, {"question_id": question.id, "points": points}, session=db.session)
       # Flash success and redirect to get_instructor_assessment_detail_route
   ```
3. **Add `POST /assessments/<assessment_id>/questions/<question_id>/edit`**:
   ```python
   @instructor_bp.route("/assessments/<assessment_id>/questions/<question_id>/edit", methods=["POST"])
   @instructor_required
   def edit_assessment_question_route(assessment_id: str, question_id: str) -> Any:
       """Direct in-place editing of question content and/or assignment points."""
       actor = require_authenticated_actor()
       asm_obj = _resolve_assessment(assessment_id, session=db.session)
       if asm_obj is None:
           raise ResourceNotFoundError(f"Assessment '{assessment_id}' not found.")
           
       require_course_manager(actor, asm_obj.course_id, session=db.session)
       
       if asm_obj.first_attempt_started_at is not None:
           raise AssessmentLockedError("Cấu trúc đề thi và phân bổ điểm số đã bị khóa (Invariant 14).")
           
       payload = request.get_json(silent=True) or request.form.to_dict() or {}
       # If points in payload: update_question_assignment(...)
       # If content/stem/choices in payload: update_question(...)
       # Flash success and redirect
   ```
4. **Add `POST /assessments/<assessment_id>/import`**:
   ```python
   @instructor_bp.route("/assessments/<assessment_id>/import", methods=["POST"])
   @instructor_required
   def import_assessment_document_route(assessment_id: str) -> Any:
       """Upload DOCX/PDF to automatically generate and assign questions."""
       actor = require_authenticated_actor()
       asm_obj = _resolve_assessment(assessment_id, session=db.session)
       if asm_obj is None:
           raise ResourceNotFoundError(f"Assessment '{assessment_id}' not found.")
           
       require_course_manager(actor, asm_obj.course_id, session=db.session)
       if asm_obj.first_attempt_started_at is not None:
           raise AssessmentLockedError("Không thể import câu hỏi vào đề thi đã có sinh viên bắt đầu làm bài.")
           
       if "file" not in request.files:
           raise ValidationError("Vui lòng chọn file DOCX hoặc PDF để tải lên.")
       upload = request.files["file"]
       asset = store_file_stream(actor=actor, course_id=asm_obj.course_id, file_stream=upload.stream, filename=upload.filename, asset_type="IMPORT_SOURCE", session=db.session)
       job = create_import_job(actor=actor, course_id=asm_obj.course_id, file_asset_id=asset.id, draft_assessment_id=asm_obj.id, session=db.session)
       process_import_job(actor=actor, job_id=job.public_id, session=db.session)
       
       auto_commit = request.form.get("auto_commit", "true").lower() in ("true", "1", "yes")
       imported_count = 0
       if auto_commit:
           for iq in job.questions:
               if iq.review_state == "PENDING":
                   iq.review_state = "ACCEPTED"
           db.session.commit()
           commit_res = commit_import_job(actor=actor, job_id=job.public_id, session=db.session)
           imported_count = commit_res.get("imported_count", 0)
           
       flash(f"Đã trích xuất và gán thành công {imported_count} câu hỏi vào đề thi!", "success")
       return redirect(url_for("instructor.get_instructor_assessment_detail_route", assessment_id=assessment_id))
   ```

### File 3: `src/pwd301/templates/instructor/assessment_builder.html`
1. **Header Action Bar**:
   Add "+ Tạo câu hỏi mới" and "Upload PDF/DOCX tạo đề" buttons next to "+ Thêm câu hỏi từ Ngân hàng".
2. **Questions Table Enhancements**:
   - Fix loops to check both `asm_obj.question_assignments` and `assessment.questions`.
   - Add inline quick points edit input.
   - Add "Sửa" (Edit) button opening `#editQuestionModal`.
   - Disable all modifications if `structure_locked`.
3. **Modals to Insert**:
   - `#createQuestionModal`: Full question creator supporting Single Choice, Multiple Choice, True/False, Short Answer with dynamic JavaScript choice management.
   - `#editQuestionModal`: In-place editor.
   - `#importDocumentModal`: File drag-and-drop upload zone for DOCX and PDF with auto-commit option.

---

## 5. Verification Method

To independently verify Worker M3's implementation:

1. **Automated Test Command**:
   Run the dedicated Milestone 3 test suite:
   ```bash
   python -m pytest tests/test_m3_assessment_authoring.py -v
   ```
   And verify regression safety on existing suites:
   ```bash
   python -m pytest tests/unit/test_assessment_service.py tests/unit/test_import_service.py tests/api/test_assessment_api.py -v
   ```

2. **Inspect Files**:
   - Verify `src/pwd301/templates/instructor/assessment_builder.html` contains:
     - `#createQuestionModal` with Single Choice, Multiple Choice, True/False, Short Answer.
     - Inline points edit form and `#editQuestionModal`.
     - `#importDocumentModal` with drag-and-drop file input.
   - Verify `src/pwd301/blueprints/instructor/routes.py` registers:
     - `/assessments/<assessment_id>/questions/create`
     - `/assessments/<assessment_id>/questions/<question_id>/edit`
     - `/assessments/<assessment_id>/import`
   - Verify `src/pwd301/services/import_service.py` sets and auto-assigns `draft_assessment_id`.
