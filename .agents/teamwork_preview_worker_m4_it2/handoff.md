# Milestone 4 Remediation Handoff Report: Transaction Atomicity in Lesson File Uploads

**Agent ID**: `worker_m4_it2`  
**Role**: Milestone 4 Worker (Iteration 2 Remediation)  
**Parent Conversation ID**: `5f234e51-df3a-4989-b3f8-7adc52e9513d`  
**Timestamp**: 2026-09-14T20:45:45Z  
**Verdict**: **REMEDIATION_COMPLETE**

---

## 1. Observation

### A. Defect Reproduction
Execution of `.venv\Scripts\python.exe -m pytest tests/test_m4_challenger_media_limits.py -v` prior to remediation reproduced the exact atomicity failures identified in Challenger M4_1 report:
- `test_instructor_create_lesson_rejects_dangerous_media_file` failed with `assert 1 == 0`
- `test_instructor_create_lesson_rejects_dangerous_resource_files` failed with `assert 1 == 0`
- `test_instructor_create_lesson_html_flow_ghost_lesson_defect` failed with `assert 1 == 0`
3 failed, 74 passed out of 77 tests.

### B. Root Cause in Code
In `src/pwd301/blueprints/instructor/routes.py:633`, `create_lesson_route` previously called `lesson = create_lesson(actor, course.id, payload)` before processing `request.files` through `store_file_stream`.
Because `create_lesson` defaults `session=None`, it executed `sess.commit()`. When `store_file_stream` later checked `validate_file_metadata(clean_filename, content_type)` and raised `FileValidationError` on dangerous or macro extensions (`.sh`, `.pptm`, `.bat`), the error was caught by the route exception handler, but the committed `Lesson` record remained orphaned in the database.

### C. Implemented Fix
In `src/pwd301/blueprints/instructor/routes.py`:
1. Imported `validate_file_metadata` from `pwd301.services.file_service`.
2. Added pre-validation in `create_lesson_route` before calling `create_lesson`:
   - Iterates through `request.files.get("media_file")` and `request.files.getlist(key)` for `key` in `("resource_files", "resource_file", "file")`.
   - Strips and sanitizes filenames using `sanitize_filename`.
   - Validates each file against `validate_file_metadata(clean_fn, getattr(f, "content_type", None))`.
   - If validation fails, `FileValidationError` is raised immediately before `create_lesson` is ever executed.
3. Added a cleanup guard around multipart file storage:
   - If an unexpected error occurs during `store_file_stream` or `attach_resource_to_lesson`, the catch block rolls back the active session, deletes the newly created lesson (`db.session.delete(l_to_del); db.session.commit()`), and re-raises the original exception.

---

## 2. Logic Chain

1. **Pre-Validation Prevents Orphan Creation**:
   - In both JSON and HTML routes, pre-validation executes before `create_lesson`.
   - For malicious or macro files (e.g. `exploit.sh`, `dangerous.pptm`, `trojan.bat`), `validate_file_metadata` raises `FileValidationError`.
   - Because `create_lesson` is never reached, `Lesson` count before and after the request remains strictly identical (`lessons_after == lessons_before`).
   - For HTML flows, the outer `except Exception as exc:` catches `FileValidationError`, displays the danger flash `'Lỗi tạo bài giảng: ...'`, and redirects to `instructor.manage_course_hub` with 0 orphan lessons.
   - For JSON/API flows, `FileValidationError` bubbles to Flask exception handlers and returns HTTP 400 `VALIDATION_ERROR`.

2. **Cleanup Guard Guarantees Atomicity on Subsequent Errors**:
   - If pre-validation passes but file storage fails (e.g. storage error or size limit violation), the inner `except Exception:` block catches the failure.
   - It performs `db.session.rollback()` to reset any invalid transaction state, queries `l_to_del = db.session.get(Lesson, lesson.id)`, deletes `l_to_del`, and commits the deletion.
   - This ensures that under any failure condition during file upload, zero ghost lessons remain in the database.

3. **Zero Regressions on Valid Uploads and Existing Flows**:
   - Valid uploads (e.g. `.mp4`, `.pdf`, `.docx`, `.pptx`) pass pre-validation, create the lesson, store the file stream, and attach the resource normally.
   - Form-only lesson creations (no files attached) bypass the file validation and storage blocks cleanly.

---

## 3. Caveats

- **File Stream Content vs. Metadata**: Pre-validation inspects file metadata (filename and declared content type). Stream content validation (MIME sniffing and category size limits) remains securely inside `store_file_stream` and `LimitingStream`; if those fail during streaming, the cleanup guard handles lesson deletion.
- **Dedicated Resource Endpoint**: The endpoint `POST /courses/<course_id>/lessons/<lesson_id>/resources` attaches resources to pre-existing lessons and is unaffected by this remediation.

---

## 4. Conclusion

**Verdict: REMEDIATION_COMPLETE**

The transaction atomicity defect in `create_lesson_route` has been resolved. Pre-validation eliminates ghost lesson creation on malicious or macro file uploads, and the cleanup guard guarantees database consistency in unexpected post-creation file storage failures.

All 77 adversarial challenger tests, 16 lecture media tests, 11 streaming gate tests, and 26 core lesson API/unit tests pass with 100% green status. `ruff`, `mypy`, and `repo_check` pass cleanly with zero errors.

---

## 5. Verification Method

### Automated Commands Executed and Verified:
1. **Adversarial Media Limits Test Suite**:
   `.venv\Scripts\python.exe -m pytest tests/test_m4_challenger_media_limits.py -v`
   Result: 77 passed in 11.21s (100% pass, specifically `test_instructor_create_lesson_rejects_dangerous_media_file`, `test_instructor_create_lesson_rejects_dangerous_resource_files`, `test_instructor_create_lesson_html_flow_ghost_lesson_defect`)

2. **Lecture Media Suite**:
   `.venv\Scripts\python.exe -m pytest tests/test_m4_lecture_media.py -v`
   Result: 16 passed in 10.96s

3. **Streaming Gates and Security**:
   `.venv\Scripts\python.exe -m pytest tests/test_m4_challenger_streaming_gates.py -v`
   Result: 11 passed in 7.36s

4. **Lesson Core API and Unit Tests**:
   `.venv\Scripts\python.exe -m pytest tests/api/test_lesson_api.py tests/security/test_lesson_idor.py tests/unit/test_lesson_service.py -v`
   Result: 26 passed in 17.04s

5. **Static Checks and Linters**:
   `.venv\Scripts\python.exe -m ruff check src tests scripts` (All checks passed!)
   `.venv\Scripts\python.exe -m mypy src/pwd301` (Success: no issues found in 85 source files)
   `.venv\Scripts\python.exe scripts/repo_check.py` (Repository contract check complete: All PASS)

### Invalidation Conditions:
- Any lesson creation failure resulting in `Lesson.query.count() > 0` after upload rejection.
- Any regression in `.mp4` video streaming or multi-format resource attachments.
