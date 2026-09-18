## 2026-09-13T23:05:22Z
You are Worker M2 (teamwork_preview_worker).
Your working directory: e:\PWD301\.agents\teamwork_preview_worker_m2
Original request file: e:\PWD301\.agents\ORIGINAL_REQUEST.md
Reference audit report: e:\PWD301\.agents\AUDIT_REPORT.md
Survey handoff report: e:\PWD301\.agents\teamwork_preview_explorer_survey_2\handoff.md

Your mission: Implement Milestone 2 (R2: Deep Instructor Course Customization & Dynamic Student View):
1. Database Schema & Migration:
   - Create Alembic migration `alembic/versions/0005_add_course_customization_fields.py`:
     - Add `learning_objectives`: `NVARCHAR(MAX)` NULL.
     - Add `target_audience`: `NVARCHAR(MAX)` NULL.
     - Add `completion_requirements`: `NVARCHAR(MAX)` NULL.
   - Synchronize `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/002_course_learning.sql` and `05_DATA_DICTIONARY_COURSE.md` to preserve zero drift with the canonical database architecture.
2. Model Expansion (`src/pwd301/models/course.py`):
   - Add columns `learning_objectives`, `target_audience`, `completion_requirements` to `Course`.
   - Add helper properties:
     - `learning_objectives_list`: returns `list[str]`. If JSON array, parse it; if multiline string, split by newline and strip; if empty, return empty list `[]`.
     - `target_audience_list`: returns `list[str]`. If JSON array, parse it; if multiline string, split by newline and strip; if empty, return empty list `[]`.
3. Service Layer (`src/pwd301/services/course_service.py`):
   - In `update_course()`, expand the allowed updatable fields whitelist to include `learning_objectives`, `target_audience`, and `completion_requirements`.
   - Capture these fields in `before_state` and `after_state` for `AuditEvent` logging.
4. Instructor Blueprint & Routes (`src/pwd301/blueprints/instructor/routes.py`):
   - In `manage_course_hub`:
     - Query `prerequisites = get_course_prerequisites(course.id, session=db.session)`.
     - Query `available_courses`: published/approved active courses excluding `course.id` and existing prerequisites.
     - Query `completion_rule = get_course_completion_rule(course.id, session=db.session)` (or `course.completion_rule`).
     - Pass `prerequisites` and `available_courses` to `instructor/course_manage.html`.
   - In prerequisite routes (`/courses/<course_id>/prerequisites`):
     - Support HTML form submissions (form data `prerequisite_course_id`).
     - On `add_course_prerequisite_route`: call `add_course_prerequisite()`. Catch `PrerequisiteCycleError` and flash error alert ("Không thể thêm môn tiên quyết do tạo thành chu trình phụ thuộc vòng tròn (Cycle detected)."); on success flash success alert and redirect to `manage_course_hub(course_id, tab="settings")`.
     - On `remove_course_prerequisite_route`: support form POST/DELETE and redirect with flash message.
5. Templates:
   - `src/pwd301/templates/instructor/course_manage.html` (Tab 5 Settings):
     - Add textarea inputs for `learning_objectives`, `target_audience`, and `completion_requirements`.
     - Add a dedicated "Môn học tiên quyết (Prerequisites)" card listing current prerequisites with remove forms, and a dropdown of `available_courses` with an "Thêm điều kiện tiên quyết" button.
   - `src/pwd301/templates/student/course_detail.html`:
     - Replace lines 121-137 (hardcoded objectives) with dynamic loop over `course.learning_objectives_list`.
     - Replace lines 196-200 (hardcoded audience) with dynamic loop over `course.target_audience_list`.
     - Replace lines 201-205 (hardcoded completion requirements) with dynamic rendering of `course.completion_requirements` and rules from `course.completion_rule` (minimum progress percent, required lessons, required assessments).
     - Replace all other static placeholder text so that 100% of the course details are driven by database models.
6. Automated Tests:
   - Write comprehensive tests in `tests/test_m2_course_customization.py`:
     - Test saving and updating course objectives, audience, and completion requirements.
     - Test `learning_objectives_list` and `target_audience_list` properties with JSON and multiline text.
     - Test web form prerequisite addition and removal.
     - Test DAG cycle prevention blocking circular prerequisites and flashing danger error.
     - Test student course detail HTML view renders dynamic customized values with zero hardcoded placeholders.
   - Run tests: `pytest tests/test_m2_course_customization.py tests/test_courses.py tests/test_enrollments.py -v`.
   - Run `ruff check src/pwd301` and `mypy src/pwd301`. Ensure 100% pass!
