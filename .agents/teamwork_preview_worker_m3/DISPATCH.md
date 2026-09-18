## Dispatch for worker_m3
Working directory: e:\PWD301\.agents\teamwork_preview_worker_m3
Role: Milestone 3 Worker (Implementation & Test)

## 2026-09-14T12:37:05Z
You are worker_m3, a teamwork_preview_worker subagent.
Your working directory is: e:\PWD301\.agents\teamwork_preview_worker_m3
Your role is: Milestone 3 Worker (Implementation & Test)
Your parent conversation ID is: 5f234e51-df3a-4989-b3f8-7adc52e9513d

MANDATORY INPUTS:
- ORIGINAL_REQUEST: e:\PWD301\.agents\ORIGINAL_REQUEST.md (You MUST read this before starting work)
- PROJECT.md: e:\PWD301\.agents\PROJECT.md
- Explorer M3 Backend Handoff: e:\PWD301\.agents\teamwork_preview_explorer_m3_1\handoff.md
- Explorer M3 UI Handoff: e:\PWD301\.agents\teamwork_preview_explorer_m3_2\handoff.md
- Spec Miner M3 Handoff: e:\PWD301\.agents\teamwork_preview_spec_miner_m3\handoff.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

WRITE OWNERSHIP (Exclusively owned files for this milestone):
- src/pwd301/services/import_service.py
- src/pwd301/blueprints/instructor/routes.py
- src/pwd301/templates/instructor/assessment_builder.html
- tests/test_m3_assessment_authoring.py

TASK:
Implement Milestone 3 (R3: Assessment Page Question Authoring, Direct Editing & Document Import):

1. **Update Import Service (`src/pwd301/services/import_service.py`)**:
   - In `create_import_job(...)`: resolve `draft_assessment_id`, verify course and structural freeze (`first_attempt_started_at is None`), and persist `draft_assessment_id` onto `DocumentImportJob`.
   - In `commit_import_job(...)`: when `job.draft_assessment_id` is set, after creating each approved question via `create_question()`, call `assign_question(actor=actor, assessment_id=job.draft_assessment_id, payload={"question_id": created_q.id, "points": 1.0, "source_type": "IMPORT"}, session=sess)` to automatically assign it into the draft assessment.

2. **Add Assessment Routes (`src/pwd301/blueprints/instructor/routes.py`)**:
   - In `get_instructor_assessment_detail_route`: ensure `data["public_id"]`, `data["assessment_id"]`, and `data["question_assignments"]` are properly provided to the template context.
   - Add `POST /assessments/<assessment_id>/questions/create`:
     - Enforce `@instructor_required`, CSRF check, and structural freeze (`first_attempt_started_at is None`, raise `AssessmentLockedError` if locked).
     - Extract `question_type` (SINGLE_CHOICE, MULTIPLE_CHOICE, TRUE_FALSE, SHORT_ANSWER), `content`, `difficulty`, `points`, `explanation`, `choices`, `accepted_answers`.
     - Call `create_question(actor=actor, course_id=asm_obj.course_id, payload=q_payload, session=db.session)`.
     - Call `assign_question(actor=actor, assessment_id=asm_obj.id, payload={"question_id": created_q.id, "points": points, "source_type": "MANUAL"}, session=db.session)`.
     - Flash success message and redirect back to assessment builder `#tab-questions`.
   - Add `POST /assessments/<assessment_id>/questions/<question_id>/edit`:
     - Enforce `@instructor_required`, CSRF check, and structural freeze (`first_attempt_started_at is None`).
     - Update points via `update_question_assignment()` if points are modified.
     - Update content, choices, explanation, or accepted answers via `update_question()` (with default `change_reason="Direct edit from assessment builder"`).
     - Flash success message and redirect back.
   - Add `POST /assessments/<assessment_id>/import`:
     - Enforce `@instructor_required`, CSRF check, and structural freeze (`first_attempt_started_at is None`).
     - Handle uploaded `.docx` or `.pdf` file via `store_file_stream(..., asset_type="IMPORT_SOURCE")`.
     - Create import job via `create_import_job(..., draft_assessment_id=asm_obj.id)`.
     - Process import job via `process_import_job(...)`.
     - Auto-accept ready questions and call `commit_import_job(...)`.
     - Flash success message with count of imported questions and redirect back.

3. **Upgrade Assessment Builder Template (`src/pwd301/templates/instructor/assessment_builder.html`)**:
   - Action buttons in `#tab-questions`: Add `+ Tạo câu hỏi mới` (opens `#createQuestionModal`) and `Upload PDF/DOCX tạo đề tự động` (opens `#importDocumentModal`).
   - Add `#createQuestionModal`: Form with type selector (Single Choice, Multiple Choice, True/False, Short Answer), dynamic choice rows with correct answer radio/checkbox, accepted answers input for short answer, prompt, explanation, difficulty, points, and CSRF token.
   - Questions table: Add inline quick points editor and `Sửa` (Edit) button opening `#editQuestionModal` pre-populated with question data.
   - Add `#importDocumentModal`: Form posting to `/instructor/assessments/{{ assessment.public_id }}/import` with drag-and-drop file input for `.docx` and `.pdf`, and CSRF token.
   - Defensive UX: Disable buttons and forms if `structure_locked` (first attempt started) or `timing_locked` (published), displaying informative alert banners per Invariants 13 & 14.

4. **Write Comprehensive Integration Tests (`tests/test_m3_assessment_authoring.py`)**:
   - Test direct in-page creation for all 4 types: SINGLE_CHOICE, MULTIPLE_CHOICE, TRUE_FALSE, SHORT_ANSWER.
   - Test in-place question content editing and point editing.
   - Test PDF and DOCX upload to assessment with `draft_assessment_id` and auto-assignment.
   - Test Invariant 13 (Timing Lock): editing timing fields on published assessment is rejected; forward close_at extension allowed.
   - Test Invariant 14 (Structural Freeze): creating, editing, removing questions or points after `first_attempt_started_at` is rejected with 409 `AssessmentLockedError`.

5. **Run Verification Commands**:
   - .venv\Scripts\python.exe -m pytest tests/test_m3_assessment_authoring.py -v
   - .venv\Scripts\python.exe -m pytest tests/unit/test_assessment_service.py tests/unit/test_import_service.py -v
   - .venv\Scripts\python.exe -m ruff check src tests scripts
   - .venv\Scripts\python.exe -m ruff format --check src tests scripts
   - .venv\Scripts\python.exe -m mypy src/pwd301
   - .venv\Scripts\python.exe scripts/repo_check.py

6. Write a complete handoff.md in your working directory and report results to parent via send_message.
Remember the Mandatory Agent Skills and Completion Reporting Contract: end your final response with:
Đã dùng x skill gồm: ...
