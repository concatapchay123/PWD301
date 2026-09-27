# TASK-073 Workflow Repairs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the five TASK-073 capabilities while preserving the headless API, file-security lifecycle, and assessment history.

**Architecture:** Keep existing backend services and models as the source of truth. Extend lesson/resource and question-image contracts compatibly, keep telemetry endpoints intact while removing hardware telemetry from the Admin experience, and use shared dialog and theme tokens for consistent visual behavior.

**Tech Stack:** Flask, SQLAlchemy, vanilla JavaScript SPA, Tailwind CDN, Node built-in test runner, pytest.

**Spec:** `tasks/TASK-073.md`

## Global Constraints

- Video upload limit remains `< 1 GB`.
- Student-visible files must be active and clean; scanner failure remains fail-closed.
- Question/attempt historical snapshots remain immutable.
- REST responses remain machine-readable JSON.
- Admin telemetry API remains psutil-backed; hardware telemetry UI polling is removed.
- No dependency or database migration unless current schema evidence requires it.

---

### Task 1: Course Review Modal Lifecycle

**Files:** `frontend/assets/js/views/admin.js`; frontend/API tests.

- [ ] Add a failing frontend test for `SUBMITTED_FOR_REVIEW` showing decision actions.
- [ ] Add failing coverage for successful review closing the modal and refreshing the queue.
- [ ] Add failing coverage for failed detail fetch and late response after dismissal.
- [ ] Fix status gating and request lifecycle; render failure in the modal and guard stale async completion.
- [ ] Run the focused frontend and existing course review API tests.

### Task 2: Lesson Draft Identity and Serialized Saves

**Files:** `frontend/assets/js/views/instructor.js`; `frontend/assets/js/router.js` only if route identity evidence requires it; lesson/frontend tests.

- [ ] Reproduce three separate new-lesson draft saves and capture each returned lesson ID.
- [ ] Add a failing regression test for distinct IDs and saved content.
- [ ] Add failing coverage for overlapping autosave/manual save of the same lesson.
- [ ] Serialize writes for the current lesson and ensure a created ID is bound to only that editor instance.
- [ ] Run focused lesson service/API/frontend tests.

### Task 3: Multi-File Lesson Resources and Five-Video Limit

**Files:** `frontend/assets/js/views/instructor.js`; `src/pwd301/blueprints/instructor/routes.py`; `src/pwd301/blueprints/api_lessons/routes.py` if used by the editor; `src/pwd301/services/lesson_service.py`; relevant tests.

- [ ] Add failing tests for multi-file attachment and drag/drop selection.
- [ ] Add failing service/API tests for exactly five videos, mixed uploaded/YouTube media, and rejection of a sixth.
- [ ] Implement sequential upload of the dropped files and attach each accepted resource to the chosen lesson.
- [ ] Serialize YouTube link lists compatibly with existing `video_url`; retain uploaded videos as `LessonResource` items.
- [ ] Enforce the combined limit server-side and preserve fail-closed scan behavior and `< 1 GB` upload limit.
- [ ] Run focused API, service, and frontend tests.

### Task 4: Pasted Exam Images and Moodle XML Resources

**Files:** `frontend/assets/js/ui.js`; `frontend/assets/js/views/instructor-exams.js`; `src/pwd301/services/moodle_exam_service.py`; `src/pwd301/blueprints/instructor/routes.py`; import/question frontend and API tests.

- [ ] Add failing parser coverage for more than one image marker on a question.
- [ ] Add failing frontend coverage for clipboard image upload and marker placement at the current question caret.
- [ ] Add failing Moodle XML cases for embedded base64 images, valid `@@PLUGINFILE@@` references and broken references.
- [ ] Preserve safe embedded image data per question and expose unsupported/broken resources for review.
- [ ] Attach parsed image IDs through the existing question revision resource path; reject cross-course or unsafe images.
- [ ] Run parser/import/API and assessment delivery security tests.

### Task 5: Remove Hardware Telemetry from Admin UI

**Files:** `frontend/assets/js/views/admin.js`; dead legacy controller only if confirmed unused; frontend/Admin tests.

- [ ] Add failing coverage that operations UI retains health checks and has no CPU/RAM widgets or recurring telemetry calls.
- [ ] Remove hardware KPI/cards, timer, refresh control, and unused frontend telemetry call path.
- [ ] Preserve `/admin/telemetry`, psutil collection, authorization, service-health matrix, backup/jobs/audit.
- [ ] Run focused Admin operations API/frontend tests.

### Task 6: Shared Modal Blur and Theme Separation

**Files:** `frontend/index.html`; `frontend/assets/js/ui.js`; `frontend/assets/js/router.js`; direct overlay/dialog call sites; frontend tests.

- [ ] Add failing tests for modal backdrop blur, toast exemption, and distinct light/dark semantic token values.
- [ ] Inventory custom overlays and native browser dialogs; replace in-app native dialogs with the shared UI dialog system.
- [ ] Increase shared and custom overlay blur consistently without changing toast behavior.
- [ ] Separate canvas/card/raised/border/text values in light and dark palettes while preserving state colors.
- [ ] Run frontend checks and visually inspect student, instructor, admin, review, lesson, exam and modal screens in both themes.

### Task 7: Final Review and Evidence

**Files:** changed files; `tasks/TASK-073.md`; `tasks/CURRENT.md`.

- [ ] Run focused tests for every changed capability and the repository verification command.
- [ ] Run JS syntax checks, `python scripts/repo_check.py`, and `git diff --check`.
- [ ] Run Open Code Review delegation preview/rules and inspect every changed file.
- [ ] Inspect the SPA in browser at desktop/mobile sizes and both themes; fix the defects found in one bounded pass.
- [ ] Update graphify after the milestone and complete the task/report evidence.
