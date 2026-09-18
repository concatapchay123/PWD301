# Forensic Audit Report — Milestone 3: Assessment Question Authoring, Direct Editing & Document Import

**Work Product**: Milestone 3 Work Products (`src/pwd301/services/import_service.py`, `src/pwd301/blueprints/instructor/routes.py`, `src/pwd301/templates/instructor/assessment_builder.html`, `tests/test_m3_assessment_authoring.py`)  
**Profile**: General Project (Development Mode per `ORIGINAL_REQUEST.md`)  
**Verdict**: **CLEAN**

---

## 1. Observation

### 1.1 Direct Source Code Observations
- **`src/pwd301/services/import_service.py`**:
  - Line 912-926 (`create_import_job`): Dynamically resolves `draft_assessment_id` via `_resolve_assessment()`, validates that `target_assessment.course_id == course.id`, enforces Invariant 14 (`if target_assessment.first_attempt_started_at is not None: raise AssessmentLockedError(...)`), and stores `draft_assessment_id=target_assessment.id`.
  - Line 1340-1353 (`commit_import_job`): Iterates over approved questions, calls `create_question()` to persist question entities, and conditionally invokes `assign_question(actor=actor, assessment_id=job.draft_assessment_id, payload={"question_id": created_q.id, "points": float(points) if points else 1.0, "source_type": "IMPORT"}, session=sess)`.
- **`src/pwd301/blueprints/instructor/routes.py`**:
  - Line 1672-1858 (`/assessments/<assessment_id>/questions/create`): Guards with `@instructor_required`, resolves assessment, validates `require_course_manager()`, checks Invariant 14 (`asm_obj.first_attempt_started_at is not None` -> `AssessmentLockedError` HTTP 409), validates question types (`SINGLE_CHOICE`, `MULTIPLE_CHOICE`, `TRUE_FALSE`, `SHORT_ANSWER`), choices, points, creates question via `create_question()`, and assigns via `assign_question()`.
  - Line 1861-2055 (`/assessments/<assessment_id>/questions/<question_id>/edit`): Enforces Invariant 14, modifies assigned points via `update_question_assignment()`, and updates content via `update_question()`, cleanly preserving revision history if already referenced.
  - Line 2056-2155 (`/assessments/<assessment_id>/import`): Enforces Invariant 14, uploads document via fail-closed `store_file_stream()`, initiates `create_import_job` bound to `draft_assessment_id=asm_obj.id`, processes questions via `process_import_job()`, auto-accepts, and invokes `commit_import_job()`.
- **`src/pwd301/services/assessment_service.py`**:
  - Line 664-706 (`update_assessment`): Enforces Invariant 13 (Timing Lock): Rejects changes to `open_at`, `time_limit_minutes`, and `attempt_limit` after publish (`AssessmentLockedError`), while strictly permitting forward extension of `close_at` (`new_close > cur_close`) and rejecting backward contraction.
- **`src/pwd301/templates/instructor/assessment_builder.html`**:
  - Line 100-112: Invariant 13 timing lock status badge and UI alerts.
  - Line 158-163: Direct action buttons `+ Tạo câu hỏi mới` (`#createQuestionModal`) and `Tải lên PDF/DOCX tạo đề` (`#importDocumentModal`).
  - Line 258-290: In-line point quick-edit form and full modal trigger `#editQuestionModal_{{ q_item.question.public_id }}` for each row.
  - Line 323-535: Dynamic modal dialogs `#createQuestionModal`, `#importDocumentModal`, and `#editQuestionModal_*` complete with CSRF protection, responsive field containers, and JavaScript helpers (`toggleQuestionTypeUI`, `addChoiceRow`, `removeChoiceRow`).
- **`tests/test_m3_assessment_authoring.py`**:
  - 10 authentic end-to-end integration test cases verifying question authoring for all 4 types, points/content editing, DOCX import, PDF import, Invariant 13 timing lock, and Invariant 14 structural freeze.

### 1.2 Verbatim Verification Tool Outputs

- **Pytest M3 Suite and Unit Tests**:
  ```
  .venv\Scripts\python.exe -m pytest tests/test_m3_assessment_authoring.py tests/unit/test_assessment_service.py tests/unit/test_import_service.py -v
  ============================= test session starts =============================
  platform win32 -- Python 3.12.10, pytest-8.4.2, pluggy-1.6.0 -- E:\PWD301\.venv\Scripts\python.exe
  cachedir: .pytest_cache
  rootdir: E:\PWD301
  configfile: pyproject.toml
  plugins: cov-6.3.0
  collecting ... collected 31 items

  tests/test_m3_assessment_authoring.py::test_direct_question_creation_single_choice PASSED [  3%]
  tests/test_m3_assessment_authoring.py::test_direct_question_creation_multiple_choice_form PASSED [  6%]
  tests/test_m3_assessment_authoring.py::test_direct_question_creation_true_false PASSED [  9%]
  tests/test_m3_assessment_authoring.py::test_direct_question_creation_short_answer PASSED [ 12%]
  tests/test_m3_assessment_authoring.py::test_inplace_question_content_and_points_edit PASSED [ 16%]
  tests/test_m3_assessment_authoring.py::test_inplace_points_quick_edit_form PASSED [ 19%]
  tests/test_m3_assessment_authoring.py::test_docx_document_import_and_auto_assignment PASSED [ 22%]
  tests/test_m3_assessment_authoring.py::test_pdf_document_import_and_auto_assignment PASSED [ 25%]
  tests/test_m3_assessment_authoring.py::test_timing_lock_invariant_enforcement PASSED [ 29%]
  tests/test_m3_assessment_authoring.py::test_structural_freeze_invariant_enforcement PASSED [ 32%]
  tests/unit/test_assessment_service.py::test_create_assessment_success PASSED [ 35%]
  tests/unit/test_assessment_service.py::test_create_assessment_validation_failures PASSED [ 38%]
  tests/unit/test_assessment_service.py::test_update_assessment_draft PASSED [ 41%]
  tests/unit/test_assessment_service.py::test_sections_crud_and_reorder PASSED [ 45%]
  tests/unit/test_assessment_service.py::test_fixed_question_assignment_and_removal PASSED [ 48%]
  tests/unit/test_assessment_service.py::test_cross_course_question_assignment_rejected PASSED [ 51%]
  tests/unit/test_assessment_service.py::test_publish_gate_validation_failures PASSED [ 54%]
  tests/unit/test_assessment_service.py::test_publish_gate_success PASSED  [ 58%]
  tests/unit/test_assessment_service.py::test_timing_freeze_invariant PASSED [ 61%]
  tests/unit/test_assessment_service.py::test_structural_freeze_invariant PASSED [ 64%]
  tests/unit/test_assessment_service.py::test_algorithm_05_blueprint_materialization_and_shortage_rollback PASSED [ 67%]
  tests/unit/test_assessment_service.py::test_assessment_lifecycle_cancellation PASSED [ 70%]
  tests/unit/test_assessment_service.py::test_trash_and_30_day_restore_policy PASSED [ 74%]
  tests/unit/test_import_service.py::TestDocumentParsing::test_parse_docx_all_five_question_types PASSED [ 77%]
  tests/unit/test_import_service.py::TestDocumentParsing::test_parse_docx_inline_choices PASSED [ 80%]
  tests/unit/test_import_service.py::TestDocumentParsing::test_parse_pdf_document PASSED [ 83%]
  tests/unit/test_import_service.py::TestDocumentParsing::test_parse_missing_answer_key_flags_needs_review PASSED [ 87%]
  tests/unit/test_import_service.py::TestDuplicateDetection::test_normalize_text_for_dedup PASSED [ 90%]
  tests/unit/test_import_service.py::TestDuplicateDetection::test_detect_duplicates_exact_and_fuzzy PASSED [ 93%]
  tests/unit/test_import_service.py::TestImportLifecycleAndCommit::test_full_import_workflow PASSED [ 96%]
  tests/unit/test_import_service.py::TestImportLifecycleAndCommit::test_cancel_import_job PASSED [100%]

  ============================= 31 passed in 8.71s ==============================
  ```

- **Repository Integrity Check**:
  ```
  .venv\Scripts\python.exe scripts/repo_check.py
  PWD301 repository check: E:\PWD301
  [PASS] Required repository contract files exist
  [PASS] No duplicate database architecture/SQL copy under System Specification
  [PASS] Canonical SQL Server DDL contains 71 CREATE TABLE statements
  [PASS] Markdown code fences are balanced
  [NOTE] .env exists locally; ensure it remains ignored by Git
  [PASS] Environment template exists
  [PASS] Repository contract check complete
  ```

- **Static Type Check (Mypy)**:
  ```
  .venv\Scripts\python.exe -m mypy src/pwd301
  pyproject.toml: note: unused section(s): module = ['flask_migrate.*', 'psutil.*']
  Success: no issues found in 85 source files
  ```

- **Linter (Ruff)**:
  ```
  .venv\Scripts\python.exe -m ruff check src tests scripts
  All checks passed!
  ```

- **API Regression Suite**:
  ```
  .venv\Scripts\python.exe -m pytest tests/api/test_assessment_api.py tests/api/test_question_bank_api.py tests/api/test_import_api.py -v
  ============================= 27 passed in 8.77s ==============================
  ```

---

## 2. Logic Chain

1. **Absence of Prohibited Patterns**:
   - *Hardcoded test results*: Inspected all new methods in `import_service.py`, `routes.py`, and `assessment_builder.html`. All parameters, points, content, and question options are extracted dynamically from request payloads or database models. Zero mock shortcuts or bypass strings exist.
   - *Facade implementations*: Routes do not stub return values. Every route runs comprehensive domain logic: authorization, course ownership checking, Invariant 14 validation, model instantiation, service orchestration, and database transaction commits.
   - *Fabricated verification outputs*: Verified workspace using file-pattern search for pre-existing log/result artifacts. No stale or fabricated test outputs exist.
   - *Self-certifying tests*: Tests instantiate isolated database fixtures and verify state through database query assertions, not against code-internal tautologies.
2. **Behavioral Integrity**:
   - `draft_assessment_id` in `DocumentImportJob` accurately links imported questions directly to assessments upon commit, with correct point values and provenance metadata.
   - Invariant 13 (Timing Lock) and Invariant 14 (Structural Freeze) are strictly enforced at both the service layer and route layer, returning HTTP 409 Conflict when violated.
   - UI templates in `assessment_builder.html` correctly provide full modal forms, CSRF tokens, and defensive states (disabling inputs upon lock).
   - All 31 M3 integration/unit tests and 27 API tests executed independently and passed with 100% success.
3. **Static Contract Compliance**:
   - `repo_check.py` passed with 0 errors.
   - Mypy verified 85 source files with 0 type errors.
   - Ruff verified formatting and linting with 0 issues.

---

## 3. Caveats
- No AI question generation was audited in M3 as that belongs to M4/M5 per project breakdown.
- Testing environment utilizes SQLite database in memory configured with MSSQL-compatible semantics, consistent with existing project unit test conventions.

---

## 4. Conclusion
- **Final Verdict**: **CLEAN**
- All Milestone 3 deliverables (F8: In-Page Question Authoring, F9: In-Place Question Editing, F10: PDF/DOCX Question Import, F11: Timing Lock & Structural Freeze) are authentically implemented with high engineering rigor.
- Zero integrity violations, zero regressions, and zero facade shortcuts detected.

---

## 5. Verification Method

To independently verify these results:

```powershell
# 1. Run M3 Integration and Unit Tests
.venv\Scripts\python.exe -m pytest tests/test_m3_assessment_authoring.py tests/unit/test_assessment_service.py tests/unit/test_import_service.py -v

# 2. Run API Regression Suite
.venv\Scripts\python.exe -m pytest tests/api/test_assessment_api.py tests/api/test_question_bank_api.py tests/api/test_import_api.py -v

# 3. Run Repository Checks and Linters
.venv\Scripts\python.exe scripts/repo_check.py
.venv\Scripts\python.exe -m mypy src/pwd301
.venv\Scripts\python.exe -m ruff check src tests scripts
```
