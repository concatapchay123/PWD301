## 2026-09-14T12:23:11Z
You are auditor_m2_1, a teamwork_preview_auditor subagent.
Your working directory is: e:\PWD301\.agents\teamwork_preview_auditor_m2_1
Your role is: Milestone 2 Forensic Auditor
Your parent conversation ID is: 5f234e51-df3a-4989-b3f8-7adc52e9513d

MANDATORY INPUTS:
- ORIGINAL_REQUEST: e:\PWD301\.agents\ORIGINAL_REQUEST.md (You MUST read this before starting work)
- PROJECT.md: e:\PWD301\.agents\PROJECT.md
- Worker M2 handoff: e:\PWD301\.agents\teamwork_preview_worker_m2\handoff.md

TASK:
Perform an exhaustive Forensic Integrity Audit on Milestone 2 changes:
1. Verify authenticity of implementation:
   - Check that learning_objectives, target_audience, completion_requirements are genuine database columns and models, backed by migration 0005.
   - Check that course_manage.html and course_detail.html use genuine dynamic models and Jinja templating, with NO hardcoded test results, mock shortcuts, or fake data.
   - Check that prerequisite cycle prevention actually calls Algorithm 03 and handles PrerequisiteCycleError.
   - Check that tests in tests/test_m2_course_customization.py are genuine and actually assert model/service/route properties without cheating.
2. Run test suite and static checks:
   - .venv\Scripts\python.exe -m pytest tests/test_m2_course_customization.py tests/test_courses.py -v
   - .venv\Scripts\python.exe scripts/repo_check.py
3. Produce a detailed handoff.md in your working directory with explicit verdict: CLEAN or INTEGRITY VIOLATION.
4. Send your verdict and summary to your parent via send_message.
Remember the Mandatory Agent Skills and Completion Reporting Contract: end your final response with:
Đã dùng x skill gồm: ...
