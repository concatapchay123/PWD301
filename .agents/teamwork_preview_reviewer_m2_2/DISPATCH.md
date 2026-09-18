## Dispatch for reviewer_m2_2
Working directory: e:\PWD301\.agents\teamwork_preview_reviewer_m2_2
Role: Milestone 2 Frontend Reviewer

## 2026-09-14T12:23:11Z
You are reviewer_m2_2, a teamwork_preview_reviewer subagent.
Your working directory is: e:\PWD301\.agents\teamwork_preview_reviewer_m2_2
Your role is: Milestone 2 Frontend Reviewer
Your parent conversation ID is: 5f234e51-df3a-4989-b3f8-7adc52e9513d

MANDATORY INPUTS:
- ORIGINAL_REQUEST: e:\PWD301\.agents\ORIGINAL_REQUEST.md (You MUST read this before starting work)
- PROJECT.md: e:\PWD301\.agents\PROJECT.md
- Worker M2 handoff: e:\PWD301\.agents\teamwork_preview_worker_m2\handoff.md

TASK:
Review the frontend UI & templates for Milestone 2 (R2: Deep Instructor Course Customization & Dynamic Student View):
1. Review src/pwd301/templates/instructor/course_manage.html:
   - Settings tab textareas for learning_objectives, target_audience, completion_requirements.
   - Prerequisites management section: list of prerequisites with remove forms, dropdown of available courses, add prerequisite form, CSRF token presence.
2. Review src/pwd301/templates/student/course_detail.html:
   - Dynamic rendering of course.learning_objectives_list, course.target_audience_list, course.completion_requirements.
   - Dynamic rendering of completion_rule thresholds.
   - Confirm complete removal of hardcoded Vietnamese placeholders.
3. Run tests verifying rendering:
   - .venv\Scripts\python.exe -m pytest tests/test_m2_course_customization.py -v
   - .venv\Scripts\python.exe -m pytest tests/test_courses.py -v
4. Produce a detailed handoff.md in your working directory with explicit verdict: APPROVE or REQUEST_CHANGES.
5. Send your verdict and summary to your parent via send_message.
Remember the Mandatory Agent Skills and Completion Reporting Contract: end your final response with:
Đã dùng x skill gồm: ...
