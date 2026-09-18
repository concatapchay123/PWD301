# BRIEFING — 2026-09-14T05:40:00+07:00

## Mission
Investigate R2: Deep Instructor Course Customization & Dynamic Student View (learning objectives, skills gained, target audience, completion requirements, prerequisites with cycle prevention, curriculum/syllabus, and 100% dynamic rendering in student course detail).

## 🔒 My Identity
- Archetype: explorer
- Roles: codebase investigation, specification analysis, architecture synthesis
- Working directory: e:\PWD301\.agents\teamwork_preview_explorer_survey_2
- Original parent: 6b157767-36de-4944-8dcd-93cc1a5571d7
- Milestone: Survey & Investigation for R2

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Adhere to System Specification and Database Architecture as canonical sources of truth
- Check frontend-preview as canonical UI reference
- Provide thorough, concrete recommendations with exact file paths, line numbers, and snippets

## Current Parent
- Conversation ID: 6b157767-36de-4944-8dcd-93cc1a5571d7
- Updated: 2026-09-14T05:40:00+07:00

## Investigation State
- **Explored paths**:
  - `docs/system/PWD301_SYSTEM_SPECIFICATION/` (business rules COURSE-001..007, ENROLL-001..004, Algorithm 03 PREREQUISITE_EVALUATION).
  - `docs/database/PWD301_DATABASE_ARCHITECTURE/` (002_course_learning.sql, 05_DATA_DICTIONARY_COURSE.md).
  - `frontend-preview/assets/js/views/` (student.js lines 228-371, instructor.js lines 190-270).
  - Models: `src/pwd301/models/course.py` (Course, CoursePrerequisite, CourseCompletionRule, Lesson).
  - Services: `src/pwd301/services/course_service.py`, `enrollment_service.py`, `lesson_service.py`.
  - Blueprints: `src/pwd301/blueprints/instructor/routes.py`, `student/routes.py`.
  - Templates: `src/pwd301/templates/instructor/course_manage.html`, `student/course_detail.html`.
  - Tests: `tests/unit/test_enrollment_service.py`, `tests/api/test_instructor_course_web_flow.py`.
- **Key findings**:
  - `Course` model currently lacks `learning_objectives`, `target_audience`, and `completion_requirements`.
  - Adding these 3 fields as `NVARCHAR(MAX) NULL` with helper list properties on `Course` cleanly enables JSON or multiline string input.
  - `CoursePrerequisite` table and DAG cycle detection algorithm already exist in `enrollment_service.py:add_course_prerequisite()` (tested and passed in `test_prerequisite_dag_cycle_detection`).
  - Instructor `course_manage.html` (tab=settings) currently lacks prerequisite selection UI and course customization textareas; backend routes `/courses/<course_id>/prerequisites` currently only return JSON and need HTML form/flash/redirect support.
  - `student/course_detail.html` has hardcoded placeholder items in lines 121-137, 196-205 that must be replaced by dynamic model properties.
- **Unexplored areas**: None for R2 scope.

## Key Decisions Made
- Recommended migration `0005_add_course_customization_fields.py` to add `learning_objectives`, `target_audience`, and `completion_requirements` to `courses`.
- Recommended dual (HTML form & JSON) response handling in instructor prerequisite routes.
- Fully documented 5-step implementation plan and verification commands in `handoff.md`.

## Artifact Index
- DISPATCH.md — dispatch log
- BRIEFING.md — persistent situational awareness
- progress.md — liveness heartbeat
- handoff.md — final comprehensive survey report
