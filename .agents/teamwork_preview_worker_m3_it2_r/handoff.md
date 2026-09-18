# Handoff Report — Milestone 3 (Iteration 2 Replacement) Worker

**Agent**: `worker_m3_it2_r` (`teamwork_preview_worker_m3_it2_r`)  
**Parent Agent ID**: `5f234e51-df3a-4989-b3f8-7adc52e9513d`  
**Working Directory**: `e:\PWD301\.agents\teamwork_preview_worker_m3_it2_r`  
**Target Milestone**: Milestone 3 Assessment Question Authoring & Document Import Bug Remediation  
**Status**: COMPLETE / READY FOR AUDITOR & REVIEWER  

---

## 1. Observation

### 1.1 Root Cause Symptoms & Verbatim Errors
Prior to remediation, executing `pytest tests/test_m3_challenger_question_import.py -v` produced 2 failing tests:

1. `test_document_import_graceful_rejection_no_500_errors`:
   ```
   [ERROR] [pwd301] Unhandled Exception: Vui lòng chọn file DOCX hoặc PDF để tải lên.
   Traceback (most recent call last):
     File "E:\PWD301\src\pwd301\blueprints\instructor\routes.py", line 2071, in import_assessment_document_route
       raise ValidationError("Vui lòng chọn file DOCX hoặc PDF để tải lên.")
   pwd301.services.exceptions.ValidationError: Vui lòng chọn file DOCX hoặc PDF để tải lên.
   AssertionError: Missing file caused 500 Internal Server Error!
   assert 500 != 500
   ```

2. `test_direct_authoring_validation_error_no_500_errors`:
   ```
   [ERROR] [pwd301] Unhandled Exception: Nội dung câu hỏi không được để trống.
   Traceback (most recent call last):
     File "E:\PWD301\src\pwd301\blueprints\instructor\routes.py", line 1702, in create_instructor_assessment_question_route
       raise ValidationError("Nội dung câu hỏi không được để trống.")
   pwd301.services.exceptions.ValidationError: Nội dung câu hỏi không được để trống.
   AssertionError: Empty content caused 500 Internal Server Error!
   assert 500 != 500
   ```

3. `test_document_import_graceful_rejection_no_500_errors` (Case 6 — Prose document with no questions):
   When an instructor uploaded a DOCX file containing purely prose text (`"Introduction to Computer Science."`), `parse_question_blocks` in `src/pwd301/services/import_service.py` failed to reject the non-question text, instead interpreting it as an `ESSAY` question and returning HTTP 201 Created instead of raising `DocumentParsingError("No question structures could be identified in the document.")` and returning HTTP 400 Bad Request.

### 1.2 Exact Code Inspection
- In `src/pwd301/__init__.py`:
  `ValidationError` was defined in `src/pwd301/services/exceptions.py` (line 186) as `class ValidationError(ServiceError)`, but was absent from `DOMAIN_EXCEPTION_HANDLERS`. Consequently, any raised `ValidationError` fell through to `@app.errorhandler(Exception)`, logging `Unhandled Exception` and returning HTTP 500 Internal Server Error.
  Furthermore, `_is_api_or_json_request()` did not check `not request.accept_mimetypes.accept_html`, causing non-HTML multipart/API requests to receive an HTML error response rather than JSON.
- In `src/pwd301/blueprints/instructor/routes.py`:
  - `create_instructor_assessment_question_route` (lines 1689-1860)
  - `edit_instructor_assessment_question_route` (lines 1891-2064)
  - `import_assessment_document_route` (lines 2092-2166)
  lacked try/except blocks to gracefully intercept `ValidationError` (and `DocumentParsingError`) on browser form submissions (`request.accept_mimetypes.accept_html and not request.is_json`) to flash danger notifications and redirect back to the assessment builder.
- In `src/pwd301/services/import_service.py`:
  `_parse_single_block` (lines 407-638) lacked a guard to distinguish question structures from arbitrary prose text, leading to non-question paragraphs being treated as questions.

---

## 2. Logic Chain

1. **Central Exception Registration**:
   By importing `ValidationError` in `src/pwd301/__init__.py` and registering `ValidationError: ("VALIDATION_ERROR", 400)` in `DOMAIN_EXCEPTION_HANDLERS`, Flask centrally maps all instances of `ValidationError` to HTTP 400 Bad Request with standardized error envelope `{"error": {"code": "VALIDATION_ERROR", "message": ...}}`.
2. **Accept Header Content Negotiation**:
   Updating `_is_api_or_json_request()` to return `True` when `not request.accept_mimetypes.accept_html` guarantees that programmatic, test-client, and multipart POST requests receive JSON errors as expected by API consumers and integration tests, while browser clients requesting HTML continue receiving HTML error pages or redirects.
3. **Graceful Web UI Experience**:
   In `src/pwd301/blueprints/instructor/routes.py`:
   Wrapping `create_instructor_assessment_question_route`, `edit_instructor_assessment_question_route`, and `import_assessment_document_route` in `try ... except (ValidationError, DocumentParsingError) as exc` blocks:
   - When `request.accept_mimetypes.accept_html and not request.is_json` is `True`: flashes `flash(f"Lỗi: {str(exc)}", "danger")` and redirects (HTTP 302) to `url_for("instructor.get_instructor_assessment_detail_route", assessment_id=str(asm_obj.public_id), _anchor="tab-questions")`.
   - When `request.is_json` or programmatic (e.g. `client.post(..., data={}, content_type="multipart/form-data")`): re-raises `exc`, allowing `DOMAIN_EXCEPTION_HANDLERS` to cleanly return HTTP 400 JSON.
4. **Document Import Pattern Recognition**:
   In `src/pwd301/services/import_service.py`:
   In `_parse_single_block`, checking if the block contains at least one question indicator (`has_header`, `choices`, `detected_answers`, `explicit_type`, `diff_match`, or `pts_match`). If none are present, the block is recognized as non-question prose/preamble and returns `None`. When an uploaded document contains no question blocks, `parsed_drafts` is empty, triggering `DocumentParsingError("No question structures could be identified in the document.")` at line 1005, which cleanly returns HTTP 400 Bad Request.
5. **Empirical Validation**:
   Executing the full Milestone 3 test suite (`tests/test_m3_challenger_question_import.py`, `tests/test_m3_assessment_authoring.py`, `tests/test_m3_challenger_stress.py`) resulted in 33 passed tests with 0 failures, 0 regressions, and 100% clean linter/type checks.

---

## 3. Caveats

- No architectural breaking changes were made: internal BIGINT primary keys remain hidden (ADR-002), timing lock (BR-031) and structural freeze (BR-030) remain strictly enforced.
- HTML form error redirect relies on Flask session flash messaging; browser sessions require cookie persistence across redirects (standard behavior for Flask-Login session authentication).
- No caveats regarding regressions; all pre-existing tests continue to pass.

---

## 4. Conclusion

The defects identified by `challenger_m3_2` have been fully resolved:
- `ValidationError` is registered in `DOMAIN_EXCEPTION_HANDLERS: ("VALIDATION_ERROR", 400)` in `src/pwd301/__init__.py`.
- HTML form validation errors in question creation, in-place editing, and document import gracefully flash danger alerts and redirect to the assessment builder, while JSON/API requests return HTTP 400 Bad Request.
- Prose-only documents without question patterns are gracefully rejected with HTTP 400 Bad Request and the exact message "No question structures could be identified in the document.".
- All 33 Milestone 3 tests pass cleanly.

---

## 5. Verification Method

To independently reproduce and verify all results:

```powershell
# 1. Run all 9 challenger tests (must pass 9/9):
.venv\Scripts\python.exe -m pytest tests/test_m3_challenger_question_import.py -v

# 2. Run all 10 assessment authoring tests (must pass 10/10):
.venv\Scripts\python.exe -m pytest tests/test_m3_assessment_authoring.py -v

# 3. Run all 14 challenger stress tests (must pass 14/14):
.venv\Scripts\python.exe -m pytest tests/test_m3_challenger_stress.py -v

# 4. Run combined 33-test suite:
.venv\Scripts\python.exe -m pytest tests/test_m3_challenger_question_import.py tests/test_m3_assessment_authoring.py tests/test_m3_challenger_stress.py -v

# 5. Static and contract checks:
.venv\Scripts\python.exe -m ruff check src tests scripts
.venv\Scripts\python.exe -m mypy src/pwd301
.venv\Scripts\python.exe scripts/repo_check.py
```

### Invalidation Conditions:
This remediation is invalidated if any of the 33 Milestone 3 tests fail or if any endpoint returns HTTP 500 on client validation errors.
