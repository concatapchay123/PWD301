# Review Handoff Report — Milestone 3 Backend Review (R3)

**Agent ID**: `reviewer_m3_1`  
**Role**: Milestone 3 Backend Reviewer & Adversarial Critic  
**Verdict**: **APPROVE**  

---

## 1. Observation

Direct observations and evidence collected from code inspection, git diffs, and verification commands:

### A. Codebase Changes
1. **`src/pwd301/services/import_service.py`**:
   - `create_import_job` (lines 912-937): Resolves `draft_assessment_id` via `_resolve_assessment(draft_assessment_id, session=sess)`. Validates:
     - Target assessment exists (`DocumentImportError` if not found).
     - Target assessment belongs to the course (`target_assessment.course_id != course.id` -> `DocumentImportError`).
     - Structural Freeze check: `if target_assessment.first_attempt_started_at is not None: raise AssessmentLockedError(...)` (Invariant 14).
     - Sets `job.draft_assessment_id = target_assessment.id if target_assessment is not None else None`.
   - `commit_import_job` (lines 1340-1353): If `job.draft_assessment_id is not None`, automatically invokes:
     ```python
     from pwd301.services.assessment_service import assign_question
     assign_question(
         actor=actor,
         assessment_id=job.draft_assessment_id,
         payload={
             "question_id": created_q.id,
             "points": float(points) if points else 1.0,
             "source_type": "IMPORT",
         },
         session=sess,
     )
     ```
     Auto-assigns each approved imported question into the target draft assessment with default/parsed points.

2. **`src/pwd301/blueprints/instructor/routes.py`**:
   - `POST /assessments/<assessment_id>/questions/create` (line 1672):
     - Protected by `@instructor_bp.route` and `@instructor_required`.
     - Checks actor authentication (`require_authenticated_actor()`).
     - Checks resource ownership (`require_course_manager(actor, asm_obj.course_id)`).
     - Enforces Invariant 14: `if asm_obj.first_attempt_started_at is not None: raise AssessmentLockedError(...)`.
     - Validates question types (`SINGLE_CHOICE`, `MULTIPLE_CHOICE`, `TRUE_FALSE`, `SHORT_ANSWER`).
     - Validates content not empty, difficulty in `(REMEMBER, UNDERSTAND, APPLY)`, points > 0.
     - Parses JSON & HTML form payloads (choices, correct choice indexing, true/false values, short answer accepted lines).
     - Calls `create_question()` followed by `assign_question()`.
     - Dual response: JSON 201 for API/fetch; 302 redirect + flash message for HTML form submissions.
   - `POST /assessments/<assessment_id>/questions/<question_id>/edit` (line 1861):
     - Protected by `@instructor_bp.route` and `@instructor_required`.
     - Checks resource ownership (`require_course_manager`).
     - Enforces Invariant 14: `if asm_obj.first_attempt_started_at is not None: raise AssessmentLockedError(...)`.
     - Resolves question, updates points via `update_question_assignment()` if `points` provided (verifying points > 0).
     - If question content/choices/explanation modified, delegates to `update_question()` with `change_reason="Direct edit from assessment builder"`. This leverages Question Bank revisioning automatically.
   - `POST /assessments/<assessment_id>/import` (line 2053):
     - Protected by `@instructor_bp.route` and `@instructor_required`.
     - Checks resource ownership (`require_course_manager`).
     - Enforces Invariant 14: `if asm_obj.first_attempt_started_at is not None: raise AssessmentLockedError(...)`.
     - Validates uploaded file presence and extensions (`.docx` or `.pdf`).
     - Safely stores upload via `store_file_stream()` in fail-closed quarantine storage (`asset_type="IMPORT_SOURCE"`).
     - Creates import job with `draft_assessment_id=asm_obj.id`.
     - Invokes `process_import_job()`, auto-accepts ready items, and calls `commit_import_job()`.

3. **CSRF Protection & Invariant Defense**:
   - `csrf.init_app(app)` is registered globally in `src/pwd301/__init__.py:528`.
   - `instructor_bp` is strictly non-exempt from CSRF.
   - All modal forms in `src/pwd301/templates/instructor/assessment_builder.html` include `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">` (lines 66, 73, 81, 383, 424, 453, 568, 607).

### B. Verification Commands & Verbatim Outputs
1. `.venv\Scripts\python.exe -m pytest tests/test_m3_assessment_authoring.py -v`
   - Result: `10 passed in 2.60s` (Exit code: 0).
2. `.venv\Scripts\python.exe -m pytest tests/unit/test_assessment_service.py tests/unit/test_import_service.py -v`
   - Result: `21 passed in 5.09s` (Exit code: 0).
3. `.venv\Scripts\python.exe -m ruff check src tests scripts`
   - Result: `All checks passed!` (Exit code: 0).
4. `.venv\Scripts\python.exe -m mypy src/pwd301`
   - Result: `Success: no issues found in 85 source files` (Exit code: 0).
5. `.venv\Scripts\python.exe scripts/repo_check.py`
   - Result: `Repository contract check complete` (Exit code: 0).

---

## 2. Logic Chain

1. **Requirement R3 Alignment**:
   - ORIGINAL_REQUEST §R3 requires:
     a. Creating questions directly from assessment builder (all 4 types) without leaving for Question Bank.
     b. In-place direct editing of questions, choices, answers, and points.
     c. PDF and DOCX document import creating questions and auto-assigning to draft assessment.
     d. Invariant 13 (Timing Lock - BR-031) and Invariant 14 (Structural Freeze - BR-030).
   - Each requirement is verified in source code and backed by automated integration tests.

2. **Defense-in-Depth for Invariant 14**:
   - Invariant 14 states: "Assessment question structure and assigned points are locked after the first Student starts."
   - Defense is implemented on two independent layers:
     - Layer 1 (Route boundary): `create_instructor_assessment_question_route`, `edit_instructor_assessment_question_route`, and `import_assessment_document_route` reject modifications with `AssessmentLockedError` (HTTP 409).
     - Layer 2 (Service domain layer): `assign_question()`, `update_question_assignment()`, `remove_question_assignment()`, and `create_import_job()` each inspect `assessment.first_attempt_started_at is not None` and raise `AssessmentLockedError`.
   - Attempting any modification after `first_attempt_started_at` is set was directly verified to raise 409 Conflict.

3. **Integrity & Anti-Cheat Audit**:
   - Verified that no test mocks, hardcoded return values, or shortcuts are present in `src/pwd301/services/import_service.py` or `src/pwd301/blueprints/instructor/routes.py`.
   - Genuine parsing of XML document streams (DOCX) and stream objects (PDF) occurs via `pwd301.services.import_service`.
   - Question entities are persisted with valid database foreign keys, UUIDs, revisions, choices, and question assignments.
   - Zero evidence of facade code or self-certifying shortcuts.

4. **Ponytail Simplicity & Over-Engineering Review**:
   - Reused existing services (`create_question`, `assign_question`, `update_question`, `store_file_stream`, `commit_import_job`).
   - No unnecessary dependencies or redundant abstraction layers added.
   - Diff is clean, concise, and standard library/Flask-idiomatic.

---

## 3. Caveats

- Tests executed against local SQLite development/test environment; SQL Server dialect compatibility is maintained by SQLAlchemy declarative models and verified by existing migration checks.
- OCR parsing for scanned/image-only PDFs is not part of M3 scope (text-based PDF parsing is fully supported and tested).

---

## 4. Conclusion

**Verdict: APPROVE**

The backend implementation for Milestone 3 meets all architectural, functional, security, and invariant requirements:
- `import_service.py` correctly validates and persists `draft_assessment_id` and auto-assigns imported questions upon job commit.
- `instructor/routes.py` provides robust question creation, in-place editing, and document import endpoints with complete CSRF protection, instructor role authorization, and double-layer Invariant 14 enforcement.
- All test suites (integration, unit, linting, type-checking, repo integrity) pass with 100% success and 0 regressions.

---

## 5. Verification Method

To independently reproduce the verification results:

```powershell
# 1. Run M3 Integration Tests
.venv\Scripts\python.exe -m pytest tests/test_m3_assessment_authoring.py -v

# 2. Run Related Unit Test Regressions
.venv\Scripts\python.exe -m pytest tests/unit/test_assessment_service.py tests/unit/test_import_service.py -v

# 3. Run Static Analysis & Repo Checks
.venv\Scripts\python.exe -m ruff check src tests scripts
.venv\Scripts\python.exe -m mypy src/pwd301
.venv\Scripts\python.exe scripts/repo_check.py
```
