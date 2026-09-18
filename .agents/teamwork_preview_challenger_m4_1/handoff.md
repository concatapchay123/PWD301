# Milestone 4 Challenger Report: Media Upload & Size Limit Validation

**Agent ID**: `challenger_m4_1`  
**Working Directory**: `e:\PWD301\.agents\teamwork_preview_challenger_m4_1`  
**Role**: Milestone 4 Media Upload & Size Limit Challenger  
**Parent Conversation ID**: `5f234e51-df3a-4989-b3f8-7adc52e9513d`  
**Timestamp**: 2026-09-14T13:40:00Z  
**Verdict**: **REQUEST_CHANGES**

---

## 1. Observation

An empirical adversarial test suite containing 77 automated test cases was constructed and executed in `tests/test_m4_challenger_media_limits.py`.

### A. Size Limits & Invariant 18 (< 1 GB limit = strictly < 1,000,000,000 bytes) — PASSED
- `LimitingStream` (`src/pwd301/services/file_service.py:105-125`):
  - Stream with exactly 999,999,999 bytes: succeeds without raising error (`test_limiting_stream_sub_1gb_passes`).
  - Stream reaching exactly 1,000,000,000 bytes (1 GB boundary): strictly aborts and raises `FileSizeLimitExceededError("File stream exceeded maximum limit of 1000000000 bytes.")` (`test_limiting_stream_exact_1gb_boundary_raises_413_error`).
  - Stream with 1,000,000,001 bytes: raises `FileSizeLimitExceededError`.
  - Single read(-1): immediately raises `FileSizeLimitExceededError`.
- `check_file_size_limit` (`src/pwd301/services/file_service.py:182-234`):
  - 0 bytes: raises `FileValidationError("Uploaded file is empty (0 bytes).")`.
  - Video 999,999,999 bytes: passes.
  - Video 1,000,000,000 bytes: raises `FileSizeLimitExceededError("Video file exceeds maximum allowed limit of 1000000000 bytes (strictly < 1 GB).")`.
  - PDF boundary: 50,000,000 bytes passes; 50,000,001 bytes raises `FileSizeLimitExceededError`.
  - DOCX boundary: 50,000,000 bytes passes; 50,000,001 bytes raises `FileSizeLimitExceededError`.
  - PPTX boundary: 100,000,000 bytes passes; 100,000,001 bytes raises `FileSizeLimitExceededError`.
- `store_file_stream` (`src/pwd301/services/file_service.py:323-602`):
  - When 1,000,000,000 bytes stream is passed, raises `FileSizeLimitExceededError` and unlinks quarantine temporary file `upload_*.tmp` without disk leaks.

### B. Dangerous & Macro Office File Validation — SERVICE PASSED, ROUTE ATOMICITY FAILED
- Direct validation (`validate_file_metadata` and `store_file_stream`):
  - Macro-enabled Office presentation (`.pptm`, `.potm`): strictly rejected with `FileValidationError` (`test_store_file_stream_rejects_macro_office_presentation`).
  - Macro-enabled Office document (`.docm`, `.dotm`): strictly rejected with `FileValidationError` (`test_store_file_stream_rejects_macro_office_document`).
  - Macro-enabled Excel workbook (`.xlsm`, `.xltm`): strictly rejected with `FileValidationError`.
  - Executable scripts (`.exe`, `.sh`, `.bat`, `.cmd`, `.bash`, `.py`, `.js`, `.vbs`, `.msi`, `.scr`): strictly rejected with `FileValidationError` (`test_store_file_stream_rejects_executable_scripts`).
  - Case-insensitivity: `.PPTM`, `.DOCM`, `.XLSM`, `.EXE`, `.BAT`, `.SH`, `.PHP`, `.CMD` strictly rejected.
  - Spoofed MIME type: `malware.exe` uploaded with `Content-Type: video/mp4` strictly rejected.
  - Dedicated resource attachment endpoint (`POST /instructor/courses/<cid>/lessons/<lid>/resources`): blocks `.docm` and does not attach resource (`test_instructor_attach_resource_route_rejects_macro_document`).

- **CRITICAL DEFECT OBSERVED in `create_lesson_route`** (`src/pwd301/blueprints/instructor/routes.py:632-702`):
  ```python
  632: try:
  633:     lesson = create_lesson(actor, course.id, payload)
  634:     attached_count = 0
  ...
  640:     m_asset = store_file_stream(
  641:         actor=actor,
  642:         course_id=course.id,
  643:         file_stream=media_file.stream,
  644:         filename=media_file.filename,
  ...
  695: except Exception as exc:
  696:     if request.accept_mimetypes.accept_html and not request.is_json:
  697:         flash(f"Lỗi tạo bài giảng: {str(exc)}", "danger")
  698:         return redirect(url_for("instructor.manage_course_hub", course_id=course.public_id, tab="lessons"))
  699:     raise
  ```
  Inside `src/pwd301/services/lesson_service.py:304-309`:
  ```python
  304: if session is None:
  305:     try:
  306:         sess.commit()
  307:     except Exception:
  308:         sess.rollback()
  309:         raise
  ```
  When an instructor submits a lesson creation request with an invalid/dangerous file (`media_file="exploit.sh"`, `media_file="trojan.bat"`, or `resource_files=["dangerous.pptm"]`), `create_lesson` is called first without `session=db.session`, so it commits the lesson immediately to the database.
  When `store_file_stream` subsequently rejects the dangerous file on line 321 (`validate_file_metadata`), an error is returned (HTTP 400 in API mode; danger flash in HTML mode).
  **However, the committed `Lesson` is never deleted or rolled back.** An empty orphan lesson remains permanently in the course.

  Verbatim test failures:
  ```
  FAILED tests/test_m4_challenger_media_limits.py::TestDangerousAndMacroFileValidation::test_instructor_create_lesson_rejects_dangerous_media_file
  AssertionError: assert lessons_after == lessons_before (assert 1 == 0)

  FAILED tests/test_m4_challenger_media_limits.py::TestDangerousAndMacroFileValidation::test_instructor_create_lesson_rejects_dangerous_resource_files
  AssertionError: assert lessons_after == lessons_before (assert 1 == 0)

  FAILED tests/test_m4_challenger_media_limits.py::TestDangerousAndMacroFileValidation::test_instructor_create_lesson_html_flow_ghost_lesson_defect
  AssertionError: assert lessons_after == lessons_before (assert 1 == 0)
  ```

### C. Path Traversal & Filename Sanitization — PASSED
- `sanitize_filename` (`src/pwd301/services/file_service.py:128-150`):
  - Traversal patterns (`../../evil.mp4`, `..\\..\\evil.mp4`, `....//....//evil.mp4`, `../../../../../../etc/passwd`, `C:\\Windows\\System32\\calc.exe`) successfully stripped to basename only (`evil.mp4`, `passwd`, `calc.exe`).
  - Null bytes (`evil\x00.mp4`, `evil.mp4\x00.exe`) cleanly stripped. `exploit.mp4\x00.exe` resolves to `exploit.mp4.exe` and is blocked by extension validation.
  - Hazardous characters (`<>:"/\\|?*;`) stripped.
  - Dot-only and whitespace-only (`.`, `..`, `...`, `"   "`, `""`) safely default to `"unnamed_file"`.
  - Windows reserved names (`NUL.mp4`, `CON.mp4`, `AUX.mp4`) are supported without filesystem collisions.
  - Physical blob storage: Blobs are stored strictly by content hash `storage/blobs/ab/cd/<sha256>`, ensuring user filenames can never escape blob storage or alter server filesystem structure.

---

## 2. Logic Chain

1. **Strict Invariant 18 & Size Limit Verification**:
   - `LimitingStream` wraps incoming streams with `self._bytes_read >= self._max_bytes`.
   - When a 1,000,000,000-byte stream is read, the condition `1_000_000_000 >= 1_000_000_000` evaluates to `True` on the 1,000,000,000th byte and immediately aborts with `FileSizeLimitExceededError`.
   - When 999,999,999 bytes are read, the condition evaluates to `False`, allowing the stream to be consumed.
   - Thus, Invariant 18 (strictly < 1 GB) is mathematically and empirically enforced.

2. **Blocklist Integrity**:
   - `DANGEROUS_EXTENSIONS` contains 29 dangerous extensions including macro Office formats (`.pptm`, `.potm`, `.docm`, `.dotm`, `.xlsm`, `.xltm`) and executables (`.exe`, `.sh`, `.bat`, `.cmd`, `.py`, `.js`, etc.).
   - `validate_file_metadata` converts extensions via `Path(filename).suffix.lower()`, ensuring case-insensitive blocking.
   - Files with spoofed MIME types are stopped by extension checks.

3. **Transaction Atomicity Failure in Lesson Creation**:
   - In `create_lesson_route`, line 633 calls `lesson = create_lesson(actor, course.id, payload)`.
   - `create_lesson` defaults `session=None`, executing `sess.commit()`.
   - Uploaded files (`media_file` and `resource_files`) are only validated during `store_file_stream` (lines 640-675), *after* the lesson is committed.
   - If any attached file is rejected (dangerous extension, macro file, or 0 bytes), an exception is raised and caught on line 695.
   - In API mode, it re-raises `FileValidationError` (400). In HTML mode, it flashes an error and redirects (302).
   - In both cases, the transaction that created `Lesson` was already committed. No rollback can undo an already committed transaction.
   - Result: an orphaned, empty lesson exists in the database. When the instructor returns to the course manage page, they see the lesson that they were told failed to be created.
   - This violates database transactional integrity and UI expectation.

---

## 3. Caveats

- The defect does not allow malicious code execution because the malicious file itself is correctly rejected and not stored.
- The defect is an atomicity/database consistency bug where failed creation attempts leave residual orphan lessons.
- The dedicated endpoint `POST /courses/<course_id>/lessons/<lesson_id>/resources` is not affected by this bug because it operates on an already existing lesson.

---

## 4. Conclusion

**Verdict: REQUEST_CHANGES**

Worker M4 must fix the atomicity defect in `create_lesson_route` (`src/pwd301/blueprints/instructor/routes.py`):
1. **Pre-validate all uploaded files before touching the database**:
   Inspect all filenames in `request.files.get("media_file")` and `request.files.getlist("resource_files")` (and related keys) against `sanitize_filename` and `validate_file_metadata` *before* calling `create_lesson`.
   If any file fails, abort immediately with `FileValidationError` so that no `Lesson` is ever created.
2. **Handle post-creation failure cleanup**:
   If an unexpected error occurs while storing files (e.g. `store_file_stream` fails mid-stream or storage error), ensure the route cleans up the newly created `lesson` before returning the error.

Once Worker M4 applies this fix, all 77 tests in `tests/test_m4_challenger_media_limits.py` will pass with 100% green status.

---

## 5. Verification Method

To reproduce the bug and verify the fix:

```powershell
# 1. Run the challenger test suite exposing the atomicity failures:
.venv\Scripts\python.exe -m pytest tests/test_m4_challenger_media_limits.py -v

# 2. Inspect failing tests:
# - test_instructor_create_lesson_rejects_dangerous_media_file
# - test_instructor_create_lesson_rejects_dangerous_resource_files
# - test_instructor_create_lesson_html_flow_ghost_lesson_defect

# 3. Verify static quality:
.venv\Scripts\python.exe -m ruff check tests/test_m4_challenger_media_limits.py
.venv\Scripts\python.exe -m mypy src/pwd301
.venv\Scripts\python.exe scripts/repo_check.py
```

