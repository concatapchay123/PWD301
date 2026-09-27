# TASK-073 — Course Review, Lesson Media, Exam Images & Visual Clarity

**Status:** DONE

## Goal

Repair course approval and lesson draft/media workflows, preserve pasted question images through assessment creation, remove the real-time hardware section from the Admin UI, make modal backdrops visibly blur the page, and improve light/dark surface separation across the SPA.

## Capability map

| Module | Responsibility | Depends on |
|---|---|---|
| course-review | Correct pending-state actions and modal lifecycle | Existing course review API |
| lesson-authoring | Preserve lesson identity; support multi-file drop and up to five combined uploaded/YouTube videos | Existing LessonResource and file-scan lifecycle |
| exam-images | Convert pasted clipboard images to safe question resources and retain Moodle XML embedded images | Existing course upload and QuestionRevisionResource delivery |
| operations-ui | Remove real-time hardware display and polling while retaining service health and authorized telemetry API | Existing Admin health checks |
| modal-theme | Apply stronger blur to every in-app dialog and improve shared light/dark palette contrast | Existing SPA shell and design tokens |

Build order: course-review and lesson-authoring; exam-images; operations-ui; modal-theme; full verification.

## Source-of-truth documents

- `AGENTS.md`
- `README.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/CODING_AGENT_START_HERE.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/01_BUSINESS_RULE_CATALOG.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/03_COURSE_MANAGEMENT.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/04_LESSON_AND_PROGRESS.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/08_ASSESSMENT_ENGINE.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/11_FILE_MANAGEMENT.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/12_DOCX_PDF_IMPORT.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md`
- `docs/database/PWD301_DATABASE_ARCHITECTURE/09_DATA_DICTIONARY_FILES_IMPORT.md`
- `frontend/productive_clarity/DESIGN.md`

## Preconditions and boundaries

- Keep the Pure Headless REST API and its JSON contracts.
- Approval remains authorized and enforced by the backend; only `SUBMITTED_FOR_REVIEW` courses expose review actions.
- Pending, quarantined, or scanner-unavailable files remain inaccessible to learners. Keep the video upload size below 1 GB.
- Preserve existing lesson resources and historical assessment snapshots. No migration is planned; use current `LessonResource` rows and the existing markdown metadata compatibility path unless code/schema evidence proves a migration necessary.
- Keep the real `/admin/telemetry` API and its psutil-backed implementation because the repository operating invariant requires authentic hardware readings from telemetry endpoints. Remove its display, automatic refresh, and navigation entry from the Admin UI; keep service-health checks.
- Toast notifications remain visually separate and do not blur the page.
- Do not create templates, static frontends, or mock UI.

## Acceptance criteria

- A course in `SUBMITTED_FOR_REVIEW` displays approve/reject actions. Approval sends the canonical review API request, closes the detail modal, and refreshes the queue; a late detail response cannot reopen a dismissed modal, and load failures replace the spinner with a recoverable error state.
- Saving three new lesson drafts persists three distinct lesson IDs and their individual content. Autosave/manual writes for one lesson cannot race and replace another lesson's data.
- Instructors can select or drag multiple lesson documents/videos. All accepted documents attach to the selected lesson. At most five uploaded video resources plus YouTube links may be attached in total; the server rejects an over-limit change and preserves the current list.
- Pasting clipboard image data into exam authoring uploads it through the existing file security path and associates it with the intended question. Moodle XML embedded images are retained per question; broken or unsupported image references are visible for review instead of silently dropped. Only active, clean images are delivered to students.
- The Admin UI contains no CPU/RAM/host telemetry cards, live polling, or hardware-navigation affordance. Operational service-health panels remain and continue to work. The telemetry API remains authorized and psutil-backed.
- In-app dialogs use a clearly visible blurred backdrop, including custom authoring overlays; toast notifications do not. Native browser alert/confirm/prompt calls used as in-app dialogs are replaced with the shared dialog system.
- Shared light and dark tokens give canvas, card, raised surface, border, primary text and secondary text visibly distinct roles. Existing state colors and readable contrast remain intact across student, instructor and admin surfaces.
- Focused API/service/frontend regression checks pass; JavaScript syntax checks, repository checks, code review, and browser visual inspection are recorded with actual output.

## Required tests

- Course approval web/frontend lifecycle and existing Admin review API tests.
- Lesson creation identity, serialized autosave, multi-resource upload, five-video boundary (including mixed uploaded and YouTube), and preservation tests.
- Raw clipboard image marker/parser and Moodle XML embedded image parser tests, plus attempt delivery security coverage.
- Admin operations UI source/runtime coverage proving hardware polling is absent while service health remains.
- Dialog/backdrop and theme token tests plus light/dark browser inspection on Admin, Instructor, Student, and exam authoring screens.

## Reuse decisions

- Reuse course review service/routes, `LessonResource`, `store_file_stream`, the existing scan lifecycle, question upload routes, `QuestionRevisionResource`, and the student attempt serializer.
- Keep legacy singular `video_url` responses readable while adding a complete video list for the editor.
- Keep `ExamParser`'s stable image-marker syntax as the bridge from pasted/uploaded image assets to parsed questions.

## Deletion and simplification list

| Candidate | Classification | Reason | Action |
|---|---|---|---|
| Admin hardware KPI, hardware cards and periodic UI poll | REMOVE NOW | User requested removal; backend telemetry contract remains available | Remove from Admin UI only |
| Distinct modal-specific backdrop styles | SIMPLIFY NOW | A single shared backdrop treatment prevents modal collisions | Normalize to shared blur treatment |
| Existing operational service-health checks | KEEP | Needed for operations and specified by System Health | Preserve unchanged |
| New file-storage or question-image framework | REMOVE NOW | Existing file and revision-resource lifecycle is sufficient | Reuse current services/models |

## Ponytails / deferred debt

None planned. Any future deferral must record trigger, owner, risk, temporary safeguard, and review point.

## Completion report

### A. Scope and sources consulted
Completed the Admin course-review lifecycle, lesson draft identity and media authoring, question-image import and delivery, Admin hardware UI removal, shared dialog treatment, and light/dark surface contrast. Consulted the source-of-truth files listed above, `tasks/CURRENT.md`, `tasks/templates/TASK_TEMPLATE.md`, relevant service/routes/models/tests, and existing frontend patterns. No database migration was needed.

### B. Reuse decisions
Reused the course-review API and status model, existing lesson persistence and `LessonResource`/`FileAsset` upload and scan path, Moodle parser and course file upload endpoint, assessment question revision resources, and shared `UI.alert`/`UI.confirm`/`UI.prompt` dialogs. Kept `/admin/telemetry` and its psutil implementation; removed its Admin UI display and polling.

### C. Per-file changes
| Files | Changes |
|---|---|
| `frontend/assets/js/views/admin.js`, `frontend/assets/js/controllers.js` | Show review actions for `SUBMITTED_FOR_REVIEW`; fix detail loading/close race; remove hardware cards and polling/controller dispatch; use shared dialogs. |
| `frontend/assets/js/views/instructor.js`, `frontend/assets/js/views/student.js`, `src/pwd301/blueprints/instructor/routes.py`, `src/pwd301/blueprints/student/routes.py`, `src/pwd301/services/lesson_service.py`, `src/pwd301/services/file_service.py` | Serialize saves per lesson, retain distinct lesson IDs, support multiple file attachments and video links, enforce a combined five-video limit under lesson row locking, and serialize/play back the video list while preserving legacy singular fields. |
| `frontend/assets/js/views/instructor-exams.js`, `src/pwd301/services/moodle_exam_service.py`, `src/pwd301/blueprints/instructor/routes.py` | Preserve clipboard and embedded Moodle XML images, associate multiple image assets to questions, flag broken/unsupported images, and retain existing clean-file-only student delivery. |
| `frontend/assets/js/ui.js`, `frontend/index.html`, `frontend/assets/js/views/admin.js`, `frontend/assets/js/views/instructor.js`, `frontend/assets/js/views/instructor-exams.js` | Apply blurred modal backdrops (toasts remain unblurred), shared dialogs, and distinct light/dark surface tokens; dark mode keeps its lighter slate-400 mapping. |
| `tests/api/test_attempt_api.py`, `tests/api/test_lesson_video_integration.py`, `tests/api/test_assessment_question_images.py`, `tests/test_excel_moodle_exam_import.py`, `tests/test_moodle_exam_image_import.py`, `tests/frontend/admin_workflow_enhancements.test.js`, `tests/frontend/exam_parser_images.test.js`, `tests/frontend/instructor_lesson_authoring.test.js`, `tests/frontend/moodle_image_ui.test.js`, `tests/frontend/student_video_gate.test.js` | Added regression coverage for review status/lifecycle, image import and delivery, lesson save identity/media cap, multi-file resources, and learner video gating. |

### D. Deletion/simplification list
Removed Admin hardware metric widgets and refresh polling plus the now-unused controller dispatch. Reused one shared dialog/backdrop implementation in place of browser-native popups. Kept backend telemetry, system-health panels, and existing storage/question resource models. No new dependencies, tables, or abstractions were added.

### E. Ponytails
None.

### F. Verification actually run
| Check | Result |
|---|---|
| Focused modified frontend Node tests (`admin_workflow_enhancements`, `exam_parser_images`, `instructor_lesson_authoring`, `moodle_image_ui`, `student_video_gate`) | 27 passed, 0 failed. |
| Final focused Python feature modules (`test_lesson_video_integration`, `test_attempt_api`, `test_assessment_question_images`, `test_moodle_exam_image_import`, `test_excel_moodle_exam_import`) | 34 passed, 0 failed. |
| Earlier broader touched-module run including `test_admin_backend_completion` | 49 passed, 1 failed. The unrelated existing `test_admin_security_self_demotion_blocked` assertion expects different message wording; the admin route is unchanged. |
| Admin course-review API subset | 3 passed. |
| Moodle embedded-image parser test | 1 passed. |
| `scripts/repo_check.py` | Passed all repository contract checks. |
| JavaScript syntax checks for modified UI/controllers/views; Python `compileall` for modified modules; `git diff --check` | Passed. |
| SQL Server dialect compile for lesson locking query | Compiles to `WITH (UPDLOCK, ROWLOCK)`; no live SQL Server concurrency test was available in this run. |
| Browser inspection in temporary local preview | Verified Admin review queue/details modal, closing without a stuck loader, blurred modal backdrop, removed hardware cards, and light/dark surface separation. Did not submit approval against an existing course. |
| Open Code Review delegate | Preview identified 12 reviewable source files and 12 excluded test/docs files; source diffs reviewed. No high-severity findings left open. |
| Full repository verification script / live SQL Server integration | Not run; see remaining verification boundary. |

### G. Remaining risks / next step (only if necessary)
One unrelated admin self-demotion wording assertion remains failing in the broader selected suite. The SQL Server lock hint was validated by dialect compilation, not by a live concurrent SQL Server test. Course approval was verified through its queue/detail lifecycle and API subset; the browser did not approve a real queued course because that would change its live publication state.
