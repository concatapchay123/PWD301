# TASK-071 — Learner Progress, Instructor Course Authoring, and Exam Interaction Repairs

**Status:** DONE
**Started Date:** 2026-09-26

## Goal

Repair the reported learner course progress, instructor course authoring, certificate evidence, assessment management, and exam composition problems. Preserve the Pure Headless API contract, course and file authorization, exam snapshots, and assessment history.

## Source-of-truth documents

- `README.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/CODING_AGENT_START_HERE.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/01_BUSINESS_RULE_CATALOG.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md`
- Domain-specific course, lesson, file, assessment, and attempt specifications
- `docs/database/PWD301_DATABASE_ARCHITECTURE/` and relevant file/assessment DDL
- `AGENTS.md`, `tasks/CURRENT.md`, `tasks/templates/TASK_TEMPLATE.md`

## Preconditions

- Keep pre-existing user changes intact and inspect overlapping diffs before editing.
- Keep student-visible lesson content and files publication- and scan-gated.
- Do not weaken server-side course, attempt, or file authorization.
- Do not introduce HTML templates, static frontend files, migrations, or dependencies without a concrete requirement.

## In scope

- Learner lesson-specific resources, video progress gating, lesson quiz completion, and published lesson visibility.
- Instructor registration certificate Drive links and evidence preview behavior.
- Instructor SLO/completion settings persistence, lesson creation/reordering, lesson duration field sizing, assessment trashing, and attempt comparison layout.
- Exam composer return routing, question image attachment, multiple-select delivery, and broken interaction delivery/authoring.
- Route/render flicker across role views where a reproducible cause is identified.

## Out of scope

- Replacing the frontend design system or changing system/business rules.
- Restoring a server-rendered UI or adding frontend preview prototypes.
- Claiming client-side video telemetry is cryptographic proof of viewing.

## Reuse / existing-code inspection

- Reuse existing Flask routes, course file uploads, `QuestionRevisionResource`, assessment snapshots, lesson progress, and attempt answer autosave.
- Reuse existing course and lesson serializers, assessment trash service, and SPA router.
- Keep schema changes out unless the canonical database contract proves they are needed.

## Planned changes

1. Make lesson completion depend on server-derived progress and required lesson quiz answers; hide unpublished lessons and unavailable files.
2. Persist and expose certificate Drive links safely and allow same-origin preview for supported evidence types.
3. Preserve entered academic settings, prevent duplicate lesson creation, and keep page order stable after reorder.
4. Add safe instructor assessment trash controls and correct attempt comparison stacking.
5. Repair exam composer navigation, image attachment/delivery, and interaction behavior within existing question types.
6. Identify and remove reproducible route or interaction flicker without destabilizing other role views.
7. Add focused regression coverage, review the full diff, and report remaining limits.

## Security / authorization impact

- Only course managers may attach question images; student delivery includes only active, clean, allowed image assets.
- Student lesson progress and quiz-completion APIs must validate ownership/enrollment, lesson publication, and completion requirements.
- Drive links must be HTTPS links to approved Google Drive/Docs hosts.
- Preserve attempt answer confidentiality and lease checks.

## Database / migration impact

- None planned. Existing file and attempt snapshot tables are reused.

## Concurrency / idempotency impact

- Lesson create requests must be single-flight in the browser.
- Attempt answer saves remain ordered and submit must wait for pending saves.

## Acceptance criteria

- Learners only see resources attached to the selected published lesson, and unavailable files remain hidden.
- Lesson video progress gates its mini-quiz; required quiz questions must all be answered before lesson/course completion is recorded.
- Certificate links validate, persist, and display; supported evidence files can preview in the admin UI.
- Instructor academic settings persist, draft lesson creation does not duplicate, and student listings exclude lesson drafts.
- Instructor assessment removal preserves historical attempt data; comparison UI stacks correctly.
- Exam composer navigation returns to its authoring route; question images attach safely; single- and multi-select answers save and resume correctly.
- Drag, fill-blank, and matching behavior is verified end-to-end or explicitly reported as incomplete with concrete limits.
- No reproducible route flicker remains in the affected flows, or any unresolved global flicker is documented.
- Relevant tests, JavaScript syntax checks, repository contract checks, and diff review are recorded with actual results.

## Required tests

- `tests/api/test_attempt_api.py`
- `tests/api/test_student_backend_completion.py`
- `tests/api/test_lesson_mini_quiz_api.py`
- `tests/api/test_instructor_application_web_flow.py`
- `tests/api/test_instructor_fixes_verification.py`
- Browser verification of affected instructor and learner views where demo data permits

## Verification commands

- `pytest tests/api/test_attempt_api.py tests/api/test_student_backend_completion.py tests/api/test_lesson_mini_quiz_api.py tests/api/test_instructor_application_web_flow.py tests/api/test_instructor_fixes_verification.py`
- `node --check` on modified frontend scripts
- `python scripts/repo_check.py`
- `git diff --check`
- Focused lint and manual review of changed lines; repository-wide lint failures must be distinguished from new findings.

## Deletion and simplification list

| Candidate | Classification | Reason | Action |
|---|---|---|---|
| Existing server-rendered or duplicate UI paths | KEEP | No new ones are introduced by this task | Preserve headless architecture |
| New framework/dependency for these fixes | REMOVE NOW | Existing services and browser APIs suffice | Do not add |

## Ponytails / deferred debt

- **Client-side video anti-seek limits:** Trigger: enforcement must resist a learner modifying browser code or request payloads. Owner: assessment/course platform maintainers. Risk: browser telemetry can be forged. Temporary safeguard: server derives completion from recorded progress and validates duration/fraction before accepting quiz completion. Review point: before relying on completion as a high-stakes credential.
- **Same-view async refresh transitions:** Trigger: a same-page action re-fetches a panel without changing the route. Owner: frontend maintainers. Risk: individual panels can still briefly show a loader after local mutations. Temporary safeguard: route-driven tab changes use the staging viewport, and lesson reordering updates its current list in place. Review point: audit remaining direct panel refresh calls after the router change ships.

## Completion report — progress snapshot (2026-09-26)

### A. Scope and sources consulted

Read the repository operating contract, current task history, project README, System Specification entry points, business rules, non-negotiable invariants, domain course/lesson/file/assessment/attempt references, and canonical database architecture/DDL before changes.

### B. Reuse decisions

Reused existing REST routes, lesson progress records, course serializers, course file upload, `question_revision_resources`, scan-gated file delivery, attempt answer snapshots, and the existing assessment trash service. No migration or dependency was added.

### C. Per-file changes so far

- `frontend/assets/js/api.js`: course file upload and assessment trash helpers.
- `frontend/assets/js/router.js`, `frontend/index.html`: render route destinations in an accessible hidden staging viewport, preserve the current screen during fetches, serialize rapid route changes to the newest hash, and bust the router asset cache.
- `frontend/assets/js/views/student.js`: lesson quiz/video gating, progress UI, route-driven course detail tabs, multi-select and text-answer exam controls, grouped drag/fill/matching answer controls, answer resume/autosave ordering, and question image rendering.
- `frontend/assets/js/views/instructor.js`: lesson single-flight create/reorder rendering, settings hydration/SLO persistence, assessment trash action, duration width, and modal stacking.
- `frontend/assets/js/views/instructor-exams.js`: composer return route, interaction preview behavior, per-blank preview grading, image upload/attachment and pending-upload guard.
- `frontend/assets/js/ui.js`, `frontend/assets/js/views/instructor-exams.js`: raw question syntax preserves each question's image asset ID; the manual editor uploads and attaches an image to the selected question without exposing its marker in the question stem.
- `frontend/assets/js/views/admin.js`: certificate Drive link display.
- `frontend/assets/js/views/admin.js`, `src/pwd301/blueprints/admin/routes.py`: authenticated DOCX/XLSX text preview, with bounded extraction and XLSX archive checks; original files remain downloadable.
- `src/pwd301/__init__.py`: same-origin framing for the exact evidence preview route.
- `src/pwd301/blueprints/api_courses/routes.py`, `src/pwd301/blueprints/instructor/routes.py`, `src/pwd301/blueprints/student/routes.py`: course setting serialization, question image association, lesson publication/resource filtering, and quiz completion route.
- `src/pwd301/services/attempt_service.py`, `src/pwd301/services/lesson_service.py`, `src/pwd301/services/user_service.py`: grouped interaction delivery/grading, lesson completion validation, and Drive URL validation. Grouped-choice markers are limited to the implemented drag and match controls; text fill uses its separate typed-answer marker.
- Focused API regression tests in the five files listed above, plus grouped interaction grading/delivery coverage in `tests/unit/test_grading_service.py` and `tests/api/test_attempt_api.py`; router and fill-preview behavior in `tests/frontend/`.

### D. Deletion/simplification list

No new dependency, migration, template, or static UI layer was added. Reorder refreshes now update the current list in place rather than replacing the entire course-management view. Route changes keep the current DOM visible until the destination render completes.

### E. Ponytails

See the client-side anti-seek item above.

### F. Verification actually run

- Focused task suite after including the legacy progress scenario: **59 passed** across the six relevant API test files and `tests/unit/test_grading_service.py` (`python -m pytest ... -q`, 71.90s). The legacy heartbeat fixture now supplies `view_fraction=1.0` when asserting video completion.
- Additional focused run of `tests/unit/test_grading_service.py` and `tests/api/test_attempt_api.py`: **24 passed**.
- Frontend regression tests: **8 passed** in the latest full run, including delayed route rendering, same-route refresh staging, rapid route changes, full-view video gate, image marker parsing, accepted fill variants, and per-blank answer groups. The fill-preview tests were confirmed RED before implementation.
- `node --check` on changed frontend scripts and the new router test: passed with no syntax output.
- `python scripts/repo_check.py`: passed; required contract files, canonical SQL DDL, balanced Markdown fences, and environment template checks succeeded.
- `rtk ruff check src/pwd301/blueprints/admin/routes.py`: passed after wrapping two long lines in the preview branch.
- `git diff --check`: passed; Git emitted only line-ending notices.
- Follow-up after the full run: DOCX evidence preview API **1 passed**; raw question image marker test **1 passed**; scoped Ruff and JavaScript syntax checks passed.
- Full repository verifier was invoked through a process-scoped PowerShell execution-policy bypass. Contract and compile checks passed; repository-wide Ruff/format and mypy reported existing findings in unrelated files. Full pytest collected **1,442**, with **1,440 passed and 2 failed**. The lesson-heartbeat failure was an outdated fixture omitting full-view evidence and passes after the fixture update; the AI model-fallback test passed when run alone, but its full-suite occurrence indicates an order-dependent test failure that remains outside this task.
- Focused Ruff F-rule scan: one pre-existing F841 at `src/pwd301/blueprints/instructor/routes.py:3433`, verified present in `HEAD`; no changed-code F findings. Repository-wide Ruff and format checks are not clean per the earlier verification snapshot and are not claimed as passing.
- Impeccable detector: 26 findings across the four scanned role views (21 gray-on-color, 4 palette, 1 side-tab); these are existing view-level styling patterns, and no detector finding mapped to the newly added upload guard or changed task controls.
- Browser inspection: the local authenticated instructor dashboard and course list rendered with updated assets. The interactive authoring preview visually rendered without overlapping panels; drag selection graded 3/3, matching graded 2/3 when one pair was omitted, and typed fill accepted both `JWT` and a two-blank `HTTP` / `Retrieval` combination. The seeded learner account has a `COMPLETED` enrollment; lesson detail follows the documented active-enrollment authorization rule, so that account could not exercise playback. I preserved that access boundary. Artificial route delay was covered by regression tests rather than browser throttling.

### G. Remaining risks / next step

Implementation and regression coverage are complete. Drag/drop, multiple-blank fill, and matching have answer controls, private answer keys, delivery metadata, and server grading for their underlying question types. Browser preview checks covered all three interaction controls, and API/unit tests cover answer-key privacy and grouped scoring, including cross-group rejection. Learner playback end-to-end remains unverified because the available seeded account has a `COMPLETED` enrollment, while the documented lesson-detail rule requires active enrollment; that access boundary remains intact. Route navigation stages student, instructor, and admin views, preserves the current screen while data loads, and discards obsolete renders; the reported reorder path updates in place. DOCX/XLSX preview extracts bounded text rather than reproducing layout or embedded images; original files remain downloadable. Video anti-seek is client-side and cannot prove viewing against a determined client.
