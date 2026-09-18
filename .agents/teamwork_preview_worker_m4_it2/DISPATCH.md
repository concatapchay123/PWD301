## 2026-09-14T13:40:29Z

You are worker_m4_it2, a teamwork_preview_worker subagent.
Your working directory is: e:\PWD301\.agents\teamwork_preview_worker_m4_it2
Your role is: Milestone 4 Worker (Iteration 2 Remediation)
Your parent conversation ID is: 5f234e51-df3a-4989-b3f8-7adc52e9513d

MANDATORY INPUTS:
- ORIGINAL_REQUEST: e:\PWD301\.agents\ORIGINAL_REQUEST.md (You MUST read this before starting work)
- PROJECT.md: e:\PWD301\.agents\PROJECT.md
- Challenger M4_1 Handoff: e:\PWD301\.agents\teamwork_preview_challenger_m4_1\handoff.md (CRITICAL BUG REPORT)

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

WRITE OWNERSHIP (Exclusively owned files for this remediation):
- src/pwd301/blueprints/instructor/routes.py

TASK:
Fix the transaction atomicity defect discovered by challenger_m4_1 in Milestone 4:

1. Root Cause:
   In src/pwd301/blueprints/instructor/routes.py inside create_lesson_route (around line 633):
   lesson = create_lesson(actor, course.id, payload) is executed BEFORE validating uploaded files (media_file and esource_files).
   Because create_lesson commits the new Lesson immediately to the database, when subsequent file validation in store_file_stream rejects dangerous/macro files (.sh, .exe, .pptm, .docm, etc.) or empty files, the error is caught and flashed/returned, but the ghost Lesson remains permanently in the database!

2. Remediation:
   In src/pwd301/blueprints/instructor/routes.py:
   - In create_lesson_route:
     a. Pre-validate all uploaded files BEFORE calling create_lesson:
        Gather all uploaded files from equest.files.get( media_file) and equest.files.getlist(resource_files) (also checking ile, esource_file).
        For each file that has a ilename:
        Call alidate_file_metadata(filename=f.filename, mime_type=f.content_type). If any file fails validation, raise/flash FileValidationError immediately BEFORE creating the lesson.
     b. Cleanup guard:
        Wrap the file storage loop in a 	ry...except block after lesson = create_lesson(...).
        If an unexpected error occurs during file storage, delete the created lesson (db.session.delete(lesson); db.session.commit()) before re-raising or flashing the error, ensuring zero ghost lessons are ever left in the database.

3. Verification Commands:
   Run the following verification commands to verify the fix:
   - .venv\Scripts\python.exe -m pytest tests/test_m4_challenger_media_limits.py -v (All 77 tests must pass 100%, specifically test_instructor_create_lesson_rejects_dangerous_media_file, test_instructor_create_lesson_rejects_dangerous_resource_files, and test_instructor_create_lesson_html_flow_ghost_lesson_defect!)
   - .venv\Scripts\python.exe -m pytest tests/test_m4_lecture_media.py -v (All 16 tests must pass!)
   - .venv\Scripts\python.exe -m pytest tests/test_m4_challenger_streaming_gates.py -v (All 11 tests must pass!)
   - .venv\Scripts\python.exe -m ruff check src tests scripts
   - .venv\Scripts\python.exe -m mypy src/pwd301
   - .venv\Scripts\python.exe scripts/repo_check.py

4. Produce a detailed handoff.md in your working directory and report results to parent via send_message.
Remember the Mandatory Agent Skills and Completion Reporting Contract: end your final response with:
Đã dùng x skill gồm: ...
