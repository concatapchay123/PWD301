# Handoff Report -- Milestone 3 (R3): Assessment Question Authoring, Direct Editing & Document Import

## 1. Observation
- **Requirement & Scope**:
  - Implement Milestone 3 (R3) for PWD301: Direct question creation from assessment builder page, direct in-place question content & points editing, PDF/DOCX document import with automatic assignment to draft assessment, and strict enforcement of Invariant 13 (Timing Lock -- BR-031) and Invariant 14 (Structural Freeze -- BR-030).
  - Exclusively owned files:
    - `src/pwd301/services/import_service.py`
    - `src/pwd301/blueprints/instructor/routes.py`
    - `src/pwd301/templates/instructor/assessment_builder.html`
    - `tests/test_m3_assessment_authoring.py`
- **Observed Codebase State**:
  - `src/pwd301/models/FileImport.py`: `DocumentImportJob` has `draft_assessment_id = Column(BigInteger, ForeignKey('Assessments.id'), nullable=True)`.
  - `src/pwd301/services/import_service.py:107`: `create_import_job` accepted `target_assessment_id: int | None = None` but did not persist or validate it against course ownership or structural freeze.
  - `src/pwd301/services/import_service.py:284`: `commit_import_job` created questions into the question bank and set `item.created_question_id`, but did not assign them to `draft_assessment_id`.
  - `src/pwd301/blueprints/instructor/routes.py:165`: `get_instructor_assessment_detail_route` assembled `data = {**asm_dict, ...}` which lacked `public_id`, `assessment_id`, and `question_assignments` keys expected by template contexts.
  - `src/pwd301/templates/instructor/assessment_builder.html`: Questions tab lacked in-page question creation UI, direct in-place editing UI, document import trigger, and defensive UX badges for frozen/locked states.
- **Verification Commands Executed & Verbatim Results**:
  - Command: `.venv/Scripts/python.exe -m pytest tests/test_m3_assessment_authoring.py -v`
    Result: 10 passed in 2.46s (all 10 integration tests passed).
  - Command: `.venv/Scripts/python.exe -m pytest tests/unit/test_assessment_service.py tests/unit/test_import_service.py -v`
    Result: 21 passed in 4.47s.
  - Command: `.venv/Scripts/python.exe -m pytest tests/api/test_assessment_api.py tests/api/test_question_bank_api.py tests/api/test_import_api.py -v`
    Result: 27 passed in 8.43s.
  - Command: `.venv/Scripts/python.exe -m ruff check src tests scripts`
    Result: All checks passed!
  - Command: `.venv/Scripts/python.exe -m ruff format --check src tests scripts`
    Result: 216 files already formatted.
  - Command: `.venv/Scripts/python.exe -m mypy src/pwd301`
    Result: Success: no issues found in 85 source files.
  - Command: `.venv/Scripts/python.exe scripts/repo_check.py`
    Result: Repository check clean.

## 2. Logic Chain
1. **Direct Question Authoring**:
   - Instructors building assessments in `assessment_builder.html` require the ability to create questions directly without navigating away to the question bank.
   - `src/pwd301/blueprints/instructor/routes.py` was extended with `POST /assessments/<assessment_id>/questions/create`.
   - Before authoring, it validates the actor, ensures course ownership, and asserts that `asm.first_attempt_started_at is None` (Invariant 14).
   - It parses payload data (supporting JSON and form-encoded submissions) for `SINGLE_CHOICE`, `MULTIPLE_CHOICE`, `TRUE_FALSE`, and `SHORT_ANSWER`.
   - It invokes `question_bank_service.create_question()` followed by `assessment_service.assign_question()`, binding the new question to the assessment with the specified point value.
2. **Direct In-Place Editing**:
   - Instructors need to modify points and question details directly from the assessment builder.
   - Route `POST /assessments/<assessment_id>/questions/<question_id>/edit` validates structural freeze (`AssessmentLockedError` HTTP 409 if attempt started).
   - If `points` is provided, it calls `assessment_service.update_question_assignment()`.
   - If question content (prompt, choices, accepted answers, explanation) is modified, it delegates to `question_bank_service.update_question()` with `change_reason='Direct edit from assessment builder'`.
   - Because `update_question` automatically detects `is_question_in_use()` and branches a new `QuestionRevision`, historical assessment attempts preserve question presentation integrity while the draft assessment references the latest revision.
3. **Assessment-Level Document Import & Auto-Assignment**:
   - In `src/pwd301/services/import_service.py`:
     - In `create_import_job`, `draft_assessment_id` is resolved, validated to ensure course ownership and that `target_assessment.first_attempt_started_at is None`, and stored in `job.draft_assessment_id`.
     - In `commit_import_job`, after creating questions and assigning `item.created_question_id`, the method checks if `job.draft_assessment_id` is set. If present, it executes `assign_question(actor, job.draft_assessment_id, payload={'question_id': created_q.id, 'points': points or 1.0, 'source_type': 'IMPORT'}, session=sess)` for every imported question.
   - In `src/pwd301/blueprints/instructor/routes.py`, `POST /assessments/<assessment_id>/import` handles multipart uploads for `.docx` and `.pdf`, creates the import job bound to the assessment, processes questions, automatically approves valid items, and commits the job, instantly populating the draft assessment with imported questions.
4. **Invariant 13 & 14 Enforcement**:
   - Invariant 13 (Timing Lock): Once published (`status == 'PUBLISHED'`), attempts, open time, and time limit cannot be modified. `close_at` can only be extended forward. This was verified via `assessment_service.update_assessment()` and dedicated test assertions.
   - Invariant 14 (Structural Freeze): Once a student starts an attempt (`first_attempt_started_at is not None`), question assignments, point allocations, and question structure are locked. All creation, editing, and document import routes explicitly guard against this and raise `AssessmentLockedError`, returning HTTP 409 Conflict.
5. **Defensive UI/UX in Assessment Builder**:
   - Added dynamic modal `#createQuestionModal` with tabbed/selectable interfaces for Single Choice, Multiple Choice, True/False, and Short Answer.
   - Added `#importDocumentModal` with drag-and-drop file upload zone.
   - Added inline quick-point edit forms and `#editQuestionModal_*` for each question row.
   - Provided visual badges and disabled form controls when `timing_locked` or `structure_locked` is active.

## 3. Caveats
- AI-based question generation features belong to Milestone 4 / RAG subsystem and are purposefully omitted here per Ponytail YAGNI.
- Testing uses an in-memory SQLite database mimicking MSSQL constraints; production MSSQL behavior was confirmed via existing schema compatibility tests.
- File storage for imports leverages `store_file_stream` fail-closed local quarantine storage as required by Invariant 17.

## 4. Conclusion
- Milestone 3 (R3) requirements have been implemented and validated with 0 regressions.
- All 10 dedicated integration tests in `tests/test_m3_assessment_authoring.py` pass.
- All 21 related unit tests and 27 API tests pass cleanly.
- Codebase passes all Ruff linting, formatting, Mypy type-checking, and repository integrity checks.
- Work is complete and ready for independent verification by teamwork_preview_auditor.

## 5. Verification Method
- **Run M3 Tests**:
  ```powershell
  .venv/Scripts/python.exe -m pytest tests/test_m3_assessment_authoring.py -v
  ```
- **Run Related Unit and API Regressions**:
  ```powershell
  .venv/Scripts/python.exe -m pytest tests/unit/test_assessment_service.py tests/unit/test_import_service.py tests/api/test_assessment_api.py tests/api/test_question_bank_api.py tests/api/test_import_api.py -v
  ```
- **Run Lint, Format, and Type Checking**:
  ```powershell
  .venv/Scripts/python.exe -m ruff check src tests scripts
  .venv/Scripts/python.exe -m ruff format --check src tests scripts
  .venv/Scripts/python.exe -m mypy src/pwd301
  .venv/Scripts/python.exe scripts/repo_check.py
  ```
- **Files to Inspect**:
  - `src/pwd301/services/import_service.py`
  - `src/pwd301/blueprints/instructor/routes.py`
  - `src/pwd301/templates/instructor/assessment_builder.html`
  - `tests/test_m3_assessment_authoring.py`
