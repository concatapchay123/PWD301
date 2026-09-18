# Plan — Orchestrator 4 (Milestones 4, 5, 6)

## Overview
Advance PWD301 LMS platform to complete Milestones M4, M5, and M6:
- Milestone 4: Multi-Format Lecture Authoring & Media Support (R4)
- Milestone 5: Context-Aware Grounded AI Assistant & Smart Recommendations (R5)
- Milestone 6: Full Test Suite Verification & Adversarial Hardening (R6)

## Milestone 4 Execution Plan (R4)
1. **Exploration**:
   - Explorer 1 (Backend Architecture): Inspect `Lesson`, `LessonResource`, `FileAsset`, `lesson_service.py`, `file_service.py` (`store_file_stream`, `LimitingStream` for video < 1GB), instructor lesson routes in `src/pwd301/blueprints/instructor/routes.py`.
   - Explorer 2 (Frontend & Viewers): Inspect `src/pwd301/templates/instructor/course_manage.html` (lesson modal/form), `src/pwd301/templates/student/lesson.html` (HTML5 video player, PDF/Doc viewer, downloadable resources in Tab 5), and `frontend-preview/assets/js/views/student.js`.
2. **Implementation**:
   - Dispatch Worker M4 with exclusive write ownership:
     - `src/pwd301/services/lesson_service.py`
     - `src/pwd301/blueprints/instructor/routes.py`
     - `src/pwd301/blueprints/student/routes.py`
     - `src/pwd301/templates/student/lesson.html`
     - `src/pwd301/templates/instructor/course_manage.html`
     - `tests/test_m4_lecture_media.py`
   - Include Mandatory Integrity Warning.
3. **Verification Gate**:
   - Reviewer 1 (Backend & Data Contracts)
   - Reviewer 2 (Frontend & Player/Viewer UX)
   - Challenger 1 (Media Size Limits < 1GB, format restrictions, fail-closed quarantine)
   - Challenger 2 (Resource Lifecycle & Student Enrollment Access)
   - Forensic Auditor (Integrity Forensics)
4. **Gate Evaluation**:
   - All criteria pass -> Mark M4 DONE in `PROJECT.md`. Proceed to Milestone 5.
