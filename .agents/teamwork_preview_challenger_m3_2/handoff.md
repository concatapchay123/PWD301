# Handoff Report ? Milestone 3 Question Creation Types, Revision Branching & Document Import Challenger

**Agent**: `teamwork_preview_challenger_m3_2`  
**Working Directory**: `e:\PWD301\.agents\teamwork_preview_challenger_m3_2`  
**Target Milestone**: Milestone 3 (R3) Question Authoring, In-Place Editing & Document Import  
**Verdict**: **REQUEST_CHANGES**

---

## 1. Observation

### 1.1 Empirical Verification Test Suite
An independent adversarial test suite was authored in `tests/test_m3_challenger_question_import.py` (8 test functions) exercising question type validation, short answer matching, revision branching, valid document import, and invalid file edge cases.

Execution Command:
```powershell
.venv/Scripts/python.exe -m pytest tests/test_m3_challenger_question_import.py -v
```

Execution Results:
- `test_single_choice_validation_rejects_zero_or_multiple_correct`: **PASSED**
- `test_multiple_choice_validation_rejects_zero_correct`: **PASSED**
- `test_true_false_validation_requires_exactly_two_choices`: **PASSED**
- `test_short_answer_case_insensitivity_and_whitespace`: **PASSED**
- `test_question_revision_branching_preserves_historical_attempt`: **PASSED**
- `test_document_import_auto_assignment_to_draft_assessment`: **PASSED**
- `test_document_import_graceful_rejection_no_500_errors`: **FAILED**
- `test_direct_authoring_validation_error_no_500_errors`: **FAILED**

Overall Result: **6 PASSED, 2 FAILED in 2.42s**

### 1.2 Verbatim Error Logs for Detected Failure Modes

#### Failure A: Document Import Triggers HTTP 500 on Missing or Invalid File
When an instructor uploads a request with missing file or unsupported extension (.txt, .py):
```
[ERROR] [pwd301] Unhandled Exception: Vui l?ng ch?n file DOCX ho?c PDF ?? t?i l?n.
Traceback (most recent call last):
  File "E:\PWD301\.venv\Lib\site-packages\flask\app.py", line 917, in full_dispatch_request
    rv = self.dispatch_request()
  ...
  File "E:\PWD301\src\pwd301\blueprints\instructor\routes.py", line 2071, in import_assessment_document_route
    raise ValidationError("Vui l?ng ch?n file DOCX ho?c PDF ?? t?i l?n.")
pwd301.services.exceptions.ValidationError: Vui l?ng ch?n file DOCX ho?c PDF ?? t?i l?n.
```
HTTP Response returned to client:
- Status Code: `500 INTERNAL SERVER ERROR`
- Payload: `{"error": {"code": "INTERNAL_ERROR", "message": "An internal server error occurred. Please contact support."}}`

#### Failure B: Direct Question Creation Triggers HTTP 500 on Validation Errors
When an instructor submits empty question content (`content: "   "`) or negative points (`points: -1.0`):
```
[ERROR] [pwd301] Unhandled Exception: N?i dung c?u h?i kh?ng ???c ?? tr?ng.
Traceback (most recent call last):
  File "E:\PWD301\.venv\Lib\site-packages\flask\app.py", line 917, in full_dispatch_request
    rv = self.dispatch_request()
  ...
  File "E:\PWD301\src\pwd301\blueprints\instructor\routes.py", line 1702, in create_instructor_assessment_question_route
    raise ValidationError("N?i dung c?u h?i kh?ng ???c ?? tr?ng.")
pwd301.services.exceptions.ValidationError: N?i dung c?u h?i kh?ng ???c ?? tr?ng.
```
HTTP Response returned to client:
- Status Code: `500 INTERNAL SERVER ERROR`
- Payload: `{"error": {"code": "INTERNAL_ERROR", "message": "An internal server error occurred. Please contact support."}}`

### 1.3 Code Inspection Findings
- `src/pwd301/blueprints/instructor/routes.py`:
  - Line 1694: `raise ValidationError(...)` (invalid question type)
  - Line 1702: `raise ValidationError("N?i dung c?u h?i kh?ng ???c ?? tr?ng.")` (empty prompt)
  - Line 1718: `raise ValidationError("?i?m ph?n b? ph?i l? m?t s? l?n h?n 0.")` (negative or zero points on create)
  - Line 1897: `raise ValidationError("?i?m ph?n b? ph?i l? m?t s? l?n h?n 0.")` (negative or zero points on edit)
  - Line 2071: `raise ValidationError("Vui l?ng ch?n file DOCX ho?c PDF ?? t?i l?n.")` (missing file in upload)
  - Line 2075: `raise ValidationError("T?n file kh?ng h?p l?.")` (empty filename in upload)
  - Line 2079: `raise ValidationError("Ch? h? tr? ??nh d?ng t?i li?u Word (.docx) ho?c PDF (.pdf).")` (unsupported extension in upload)
- `src/pwd301/__init__.py`:
  - Lines 261-372: `DOMAIN_EXCEPTION_HANDLERS` dictionary registers specific subclasses (`QuestionValidationError`, `CourseValidationError`, `LessonValidationError`, `DocumentParsingError`, etc.).
  - `ValidationError` (`from pwd301.services.exceptions import ValidationError`) is **NOT** included in `DOMAIN_EXCEPTION_HANDLERS`.
  - As a consequence, whenever `ValidationError` is raised, Flask fails to find an exact matching handler in `DOMAIN_EXCEPTION_HANDLERS`, falling through to `@app.errorhandler(Exception)` at line 467, which logs `Unhandled Exception` and returns HTTP 500.

---

## 2. Logic Chain

1. **TASK Requirement Verification**:
   - The user task specification requires:
     > "Upload invalid/empty/corrupt file -> verify graceful rejection without 500 error."
   - And System Specification non-negotiable invariants mandate that client validation errors must be gracefully handled with HTTP 400 Bad Request and standardized error envelope (`code: VALIDATION_ERROR`).
2. **Discrepancy Traced to Exception Architecture**:
   - `DocumentParsingError` (raised when a file is corrupted, empty, or lacks question blocks) is registered in `DOMAIN_EXCEPTION_HANDLERS: ("PARSING_ERROR", 400)` and correctly returns HTTP 400.
   - However, preliminary validation in `import_assessment_document_route` (e.g. missing file payload, invalid extension) and `create_instructor_assessment_question_route` (empty content, invalid points) raises `ValidationError`.
   - Because `ValidationError` is not mapped in `DOMAIN_EXCEPTION_HANDLERS`, Flask treats it as an unexpected server crash, emitting a full traceback and returning HTTP 500.
3. **Confirmed Working Components**:
   - SINGLE_CHOICE validation (0 or >1 correct choices, <2 choices) delegates to `question_bank_service.create_question()`, which raises `QuestionValidationError` (registered -> HTTP 400).
   - MULTIPLE_CHOICE validation (0 correct choices in JSON or HTML form) raises `QuestionValidationError` (registered -> HTTP 400).
   - TRUE_FALSE validation (choice count != 2, or both true/false) raises `QuestionValidationError` (registered -> HTTP 400).
   - SHORT_ANSWER in `NORMALIZED` mode properly normalizes Unicode NFKC, strips leading/trailing whitespace, and ignores casing, awarding 100% points. In `EXACT` mode, case sensitivity is strictly enforced (0 points on case mismatch).
   - Question Revision Branching: When a question linked to an assessment with started attempts is edited via QuestionBank, `QuestionRevision` revision 2 is spawned with `is_current=True`, while `AttemptQuestion` preserves its frozen link to revision 1 (`source_question_revision_id`), content snapshot, and assigned points. In-place editing directly on the frozen assessment is blocked with HTTP 409 Conflict.
   - Document Import Pipeline: Valid DOCX and PDF files parse questions, persist them to the QuestionBank, and successfully auto-assign them to `draft_assessment_id` with `source_type='IMPORT'`.
4. **Conclusion Support**:
   - The functional implementations of question authoring, revision branching, and document import are well-constructed and verified.
   - However, the unhandled `ValidationError` bug directly breaks the acceptance criterion requiring graceful rejection of invalid uploads without 500 errors. Therefore, the required verdict is `REQUEST_CHANGES`.

---

## 3. Caveats

- `tests/test_m3_challenger_question_import.py` is permanently stored in `tests/` and passes repo-check, ruff linting, and mypy typechecking.
- As an empirical challenger, this agent did not modify any source code in `src/pwd301/` to preserve review independence.
- No other untested edge cases were identified in the Milestone 3 scope.

---

## 4. Conclusion

**Verdict**: **REQUEST_CHANGES**

### Actionable Remediation Required by Worker M3:
1. **Option A (Recommended Architectural Fix)**:
   In `src/pwd301/__init__.py`:
   - Import `ValidationError` from `pwd301.services.exceptions`.
   - Add `ValidationError: ("VALIDATION_ERROR", 400)` to `DOMAIN_EXCEPTION_HANDLERS`.
   - This ensures all existing and future uses of `ValidationError` in blueprints gracefully return HTTP 400 with code `VALIDATION_ERROR` instead of crashing with HTTP 500.
2. **Option B (Blueprint-Level Fix)**:
   In `src/pwd301/blueprints/instructor/routes.py`:
   - In `create_instructor_assessment_question_route` and `edit_instructor_assessment_question_route`: replace `raise ValidationError(...)` with `raise QuestionValidationError(...)`.
   - In `import_assessment_document_route`: replace `raise ValidationError(...)` with `raise DocumentParsingError(...)` or `raise FileValidationError(...)`.

Once the worker applies this remediation, both `test_document_import_graceful_rejection_no_500_errors` and `test_direct_authoring_validation_error_no_500_errors` will pass with 100% clean assertions.

---

## 5. Verification Method

To independently verify all findings and reproduce the bug:

```powershell
# 1. Run the challenger test suite demonstrating the 2 failures:
.venv/Scripts/python.exe -m pytest tests/test_m3_challenger_question_import.py -v

# 2. Directly verify the 500 error on invalid import file:
.venv/Scripts/python.exe -m pytest tests/test_m3_challenger_question_import.py::test_document_import_graceful_rejection_no_500_errors -v

# 3. Directly verify the 500 error on direct authoring validation:
.venv/Scripts/python.exe -m pytest tests/test_m3_challenger_question_import.py::test_direct_authoring_validation_error_no_500_errors -v

# 4. Verify passing tests (6 passing):
.venv/Scripts/python.exe -m pytest tests/test_m3_challenger_question_import.py -k "not no_500_errors" -v

# 5. Check linting and static checks:
.venv/Scripts/python.exe -m ruff check tests/test_m3_challenger_question_import.py
.venv/Scripts/python.exe -m mypy tests/test_m3_challenger_question_import.py
.venv/Scripts/python.exe scripts/repo_check.py
```

### Invalidation Conditions:
This finding is invalidated only if registering `ValidationError: ("VALIDATION_ERROR", 400)` or converting the raised exceptions to `QuestionValidationError` / `DocumentParsingError` causes any regression in existing test suites.
