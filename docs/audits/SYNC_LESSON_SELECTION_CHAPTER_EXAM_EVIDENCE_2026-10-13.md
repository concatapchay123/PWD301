# Lesson selection and native chapter exam evidence — 2026-10-13

Status: named SYNC-010/022/023/080 paths verified; whole-system IN_PROGRESS.

## A. Scope and authority

Original audit's historical late lesson GET, chapter-context hydration and chapter marker persistence; current SYNC-080. Inspected current selection generation/identity fences, native chapter assessment link, Hub/manual editor/matrix/settings callers, ExamStore, existing typed same-course backend validation and previous seeded authoring evidence. The prior seeded publication proved that an already-populated chapter draft could publish, but bypassed native matrix progression. This new acceptance closes that gap rather than treating the seeded path as equivalent.

## B. Reuse

Keep existing lesson selection fences: actual browser acceptance passes without another source repair. For exams, reuse existing chapter scope, chapter loader/selector, local draft store and authoring/publication endpoints. No new dependency, backend endpoint, table, migration or asset layer.

## C. Per-file changes

- `frontend/assets/js/views/instructor-exams.js`: matrix now offers the existing chapter scope explicitly; chapter mode shows the chapter selector and hides the lesson field. Chapter data loads for both chapter and lesson scopes. Progression preserves contextual scope, requires a chapter for chapter/lesson scopes and a lesson only for lesson scope, retaining the exact selected chapter. Explicit independent choice still clears linkage; fallback does not silently reset contextual course-final mode.
- `tests/frontend/exam_matrix_context.test.js`: invokes the real progression handler for contextual chapter, missing chapter, explicit independent choice/required lesson and course-final fallback.
- Evidence, ledger, progress and manifest updated. Ignored native runners use owned fixtures and real browser/SQL. Original audit preserved.

## D. Simplification

Remove the unconditional independent fallback that erased a supported chapter context. Share existing cascading chapter loader, without another data store or publication API. Three scope choices are visible radios in one column; chapter and lesson fields remain in one column. No new CTA or animation.

## E. Debt and unfinished gates

No optional debt added. Full current backend aggregate is running separately; its initial frontend gate predates this matrix source change. Fresh frontend272 and native acceptance below verify the current matrix, but the running command must not be called a terminal current-source aggregate pass. Other unresolved audit/provider gates remain separate.

## F. Actual verification

Lesson selection: **three actual browser checks**, exit0; `browser-lesson-selection-20261013.log`, JSON `browser-lesson-selection-evidence.json`:

1. Real first-lesson GET200 is held; a newer second-lesson read finishes first. Late success cannot replace title/content/URL/history; F5 keeps second lesson.
2. Older pending native request is aborted after a newer lesson loads. Late error cannot replace the newer editor or URL.
3. Latest selection transport failure renders unavailable state without acknowledging a new URL. F5 restores the last successful lesson, actual tree retry succeeds, and independent SQL contents remain unchanged.

Chapter workflow product RED: native course chapter link → manual method → typed question → matrix progression changed chapter_linked to independent; `browser-native-chapter-exam-red-20261013.log`. No ExamStore injection. Real-handler Node RED had three failures (chapter scope lost, missing chapter acknowledged, course-final scope reset) before product change; one explicit independent/lesson validation case already passed.

GREEN: **272 full frontend passed, zero failures/skips**, exit0; `native-chapter-matrix-frontend-green-20261013.log`. **Three final native chapter checks**, exit0; `browser-native-chapter-exam-verified-20261013.log`, JSON `browser-native-chapter-exam-evidence.json`:

- Native navigation/manual editing/matrix/F5 produce no Instructor write requests and zero assessments/questions in the owned course before explicit Publish. Local draft creation does not create a database draft merely by visiting routes.
- Actual chapter link hydrates exact course/chapter; typed question, matrix and F5 preserve them. Chapter radio is checked, chapter selector visible and lesson field hidden.
- Native Publish succeeds; independent SQL stores PUBLISHED with the exact chapter marker and one assignment. Course tree and F5 display the exam in that same chapter.

Final runner waits for actual chapter options to load before progressing. An earlier post-fix probe clicked while the async selector was still loading and correctly stayed on the matrix, then timed out expecting settings. That harness timing failure was corrected; final complete exit0 is the acceptance result. No ignored timeout is counted as passing.

Guarded target `pwd301_test_browser_sync_20261012`; actual DB_NAME, head `syncprogress20261011`, baseline fixture ownership checked. Unique course/unit/lessons created through services; actual password login and CSRF. Read-only ExamStore inspection only, no question/context seeding. Gemini disabled; no playback/provider claim.

Actual Edge screenshot `browser-native-chapter-matrix-20261013.png` inspected: selected chapter scope, readable chapter selector, hidden lesson field and one-column scope layout. Impeccable applied to this changed flow; no full WCAG certification claim.

OCR fresh preview/rules for the two changed source/test files. Host review checks explicit versus fallback modes, shared loader branches, chapter/lesson required fields, exact draft linkage, safe template values and no new backend write on navigation. Prior typed backend unit validation evidence remains separately scoped; no fresh Python repair or full SQL unit-suite claim in this increment. Repository/diff checks run after document updates.

## G. Limits

Course-final fallback has a Node handler regression, not a full native final-exam workflow claim. No claim about every async course-selector interleaving or all question types. Existing chapter publication evidence is supplemented, not used to conceal the matrix defect. No commit, push, deployment or live migration/restore. Whole-system remediation remains active.
