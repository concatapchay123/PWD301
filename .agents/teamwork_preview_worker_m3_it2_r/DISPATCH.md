## 2026-09-14T13:03:42Z

You are worker_m3_it2_r, a teamwork_preview_worker subagent.
Your working directory is: e:\PWD301\.agents\teamwork_preview_worker_m3_it2_r
Your role is: Milestone 3 Worker (Iteration 2 Replacement)
Your parent conversation ID is: 5f234e51-df3a-4989-b3f8-7adc52e9513d

MANDATORY INPUTS:
- ORIGINAL_REQUEST: e:\PWD301\.agents\ORIGINAL_REQUEST.md (You MUST read this before starting work)
- PROJECT.md: e:\PWD301\.agents\PROJECT.md
- Challenger M3_2 Handoff: e:\PWD301\.agents\teamwork_preview_challenger_m3_2\handoff.md (CRITICAL BUG REPORT)

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

TASK:
Fix the defect discovered by challenger_m3_2 in Milestone 3:
1. Root Cause:
   In `src/pwd301/blueprints/instructor/routes.py`, `ValidationError` is raised when input is invalid (e.g. empty prompt, negative points, missing upload file, invalid file extension). But `ValidationError` was missing from `DOMAIN_EXCEPTION_HANDLERS` in `src/pwd301/__init__.py`. As a result, Flask treats it as an unhandled exception and crashes with HTTP 500 INTERNAL_ERROR instead of returning HTTP 400 with VALIDATION_ERROR envelope!
2. Remediation:
   - In `src/pwd301/__init__.py`:
     Import `ValidationError` from `pwd301.services.exceptions`.
     Register `ValidationError: ("VALIDATION_ERROR", 400)` in `DOMAIN_EXCEPTION_HANDLERS`.
   - In `src/pwd301/blueprints/instructor/routes.py`:
     In `create_instructor_assessment_question_route`, `edit_instructor_assessment_question_route`, and `import_assessment_document_route`:
     Ensure HTML form requests (when not JSON) handle `ValidationError` gracefully by flashing danger alert and redirecting to the assessment builder, while JSON requests cleanly return HTTP 400 via `DOMAIN_EXCEPTION_HANDLERS`.
3. Verification:
   Run the following verification commands:
   - .venv\Scripts\python.exe -m pytest tests/test_m3_challenger_question_import.py -v (All 8 tests must pass, especially test_document_import_graceful_rejection_no_500_errors and test_direct_authoring_validation_error_no_500_errors!)
   - .venv\Scripts\python.exe -m pytest tests/test_m3_assessment_authoring.py -v (All 10 tests must pass!)
   - .venv\Scripts\python.exe -m pytest tests/test_m3_challenger_stress.py -v (All 14 tests must pass!)
   - .venv\Scripts\python.exe -m ruff check src tests scripts
   - .venv\Scripts\python.exe -m mypy src/pwd301
   - .venv\Scripts\python.exe scripts/repo_check.py
4. Produce a detailed handoff.md in your working directory and report results via send_message.
Remember the Mandatory Agent Skills and Completion Reporting Contract: end your final response with:
Đã dùng x skill gồm: ...
