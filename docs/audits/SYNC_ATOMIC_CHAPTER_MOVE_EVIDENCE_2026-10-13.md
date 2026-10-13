# Atomic chapter move evidence — 2026-10-13

Status: named cross-unit move/ordering repair verified; whole-system remediation IN_PROGRESS. Supersedes OPEN_CROSS_UNIT_ATOMIC in the preceding ordering report.

## A. Scope and source of truth

SYNC-020 and related historical SYNC-012. Original audit, current closure ledger and previous actual native-drag RED; canonical Course database contract requires transactional global ordering and retains Lesson ID when changing groups. Existing CourseChangeRequest structural review remains authority for published changes. Inspected course API, move/reorder callers, review/serialization, chapter caps and existing transaction helpers.

## B. Reuse

Extend the existing course-wide reorder POST with optional placement intent instead of composing updateLesson PATCH and a second order POST. Reuse caller-owned session, two-phase positive-offset ordering, course parent lock, object resolvers, chapter media validation, structural review queue and Admin review endpoint. No new dependency, endpoint, migration, table or UI asset layer.

## C. Per-file changes

- `src/pwd301/services/lesson_service.py`: optional `move` and read-only validation mode for queued intent; lock/refresh course and refresh active lessons; validate the complete course order, same-course active lesson and destination, typed identifiers, ten-lesson and seven-video chapter caps. Destination lock/recheck preserves admission. Apply parent and order in one transaction, preserving lesson identity/content; record placement in the ordering audit.
- `src/pwd301/blueprints/instructor/routes.py`: validate before queueing; compose move/order under explicit commit/rollback for draft courses. Published courses queue both in one existing structural intent. Exact retry returns the same pending request; different intent conflicts instead of silently returning an earlier request. Store readable lesson/source/destination names for review, reusing the existing local unit resolver.
- `src/pwd301/blueprints/admin/routes.py`: apply the optional placement in the same order/review transaction; explicit rollback on mutation and required review audit/commit failure retains PENDING and curriculum.
- `frontend/assets/js/api.js`: optional move payload in the existing reorder POST.
- `frontend/assets/js/views/instructor.js`: both cross-chapter drop targets use one move/order request; within-chapter and cross-chapter pending outcomes restore the authoritative tree and show review status, with no applied-success message.
- `frontend/assets/js/views/admin.js`: review shows escaped lesson/source/destination names and an ordered title list, rather than hiding placement intent or exposing raw technical IDs.
- `tests/api/test_atomic_lesson_move.py`: eleven regression cases for actual placement/order, controlled mutation/audit failure, published queue/retry/conflict/review failure/recovery, foreign/deleted/missing/historical/incomplete targets/orders, chapter child/media limits and readable metadata.
- `tests/frontend/lesson_course_order.test.js` and `tests/frontend/course_review_regression.test.js`: real handler pending snapshot outcome, one-request wrapper and readable/escaped review order.
- `docs/system/PWD301_SYSTEM_SPECIFICATION/api/04_COURSE_API.md`: document the composed request and pending/applied distinction. Evidence/ledger/progress/manifest updated. Original audit unchanged.

## D. Deletion and simplification

Removed two preliminary move PATCH calls and their split transaction boundary. Reuse one existing POST; no blind compensating move-back. KEEP global complete-order validation and published approval. Removed a redundant resolver import caught by Ruff/mypy because the route module already defines the reused resolver.

## E. Debt and unfinished work

No optional infrastructure debt added. Full current-source aggregate and exact SQL reconciliation of the newer skip set remain unfinished, as do other explicitly unverified audit gates. This scoped repair does not establish whole-system completion.

## F. Actual verification

RED: actual native drag committed placement before an aborted second request, making SQL disagree with snapshot rollback; `browser-cross-unit-atomic-red-20261013.log`. Five new API cases failed before backend changes, including ignored placement and foreign target being acknowledged. Required Admin audit failure additionally reproduced retained dirty placement before explicit rollback. Readable review metadata API failed with missing lesson_title before repair. Review Node harness initially lacked button objects; corrected harness then failed on missing review summary before UI repair. These setup failures are not product RED claims.

GREEN:

- **50 affected SQLite tests passed**, exit0, 38.00 seconds; `atomic-move-affected-final-20261013.log` (new API, lesson authoring, changeset defense and lesson service).
- **49 affected SQL tests passed, zero skips**, exit0, 145.28 seconds; `sqlserver-atomic-lesson-move-20261013.log`. This earlier selection predates readable review metadata and the last additional cap case; not a current full-source pass.
- **11 final SQL move tests passed, zero skips**, exit0, 40.55 seconds; `sqlserver-atomic-lesson-move-final-20261013.log`. Covers current move/review metadata, exact pending retry/conflict, rollback and limits. Selections overlap; do not sum them.
- **268 full frontend tests passed, zero failures/skips**, exit0; `atomic-move-review-frontend-final-20261013.log`.
- **Seven actual browser checks passed**, exit0; `browser-atomic-move-review-final-20261013.log`, JSON `browser-lesson-order-evidence.json`:
  1. Within-chapter move in a multi-chapter course preserves global SQL order and F5.
  2. Failed within-chapter reorder preserves committed SQL and tree/F5.
  3. Cross-chapter native drag sends one POST; transport abort leaves placement untouched and restores tree.
  4. Restored native drag commits parent/order in one POST; SQL/F5 retain the same Lesson ID.
  5. Legal course publication followed by native drag returns202; original placement survives tree/F5 until review.
  6. Separate Admin session opens the exact review and sees readable lesson/source/destination and proposed order before approval.
  7. Actual Admin API wrapper applies the pending request; independent SQL and Instructor F5 agree. This step uses the real wrapper/HTTP, not a claim about clicking the approval button.

Browser target `pwd301_test_browser_sync_20261012`; SQL target `pwd301_test_quick_add_retry_20261012`. Actual DB_NAME and migration head `syncprogress20261011` checked before fixtures; baseline browser ownership verified; new owned course/chapters/lessons use services and publication uses legal transitions. Real password sessions, CSRF enabled, Gemini disabled; no provider call. An additional detached fixture reference was corrected by capturing the public unit ID inside its live context before final acceptance.

OCR delegate preview/rules produced for nine changed source/test files. Host review covers this increment's transactions, stable identity, same-course/deletion checks, caps, pending retry semantics, explicit rollback, one-request callers and XSS-safe readable review. Existing unrelated edits are not claimed freshly reviewed here. Ruff/format/types and repository/diff checks are executed again by the current aggregate; an intermediate duplicate resolver import failed lint/types and was removed before that aggregate started. No failed check is counted as passed.

## G. Limits

No claim about every possible concurrent editor/network/provider interleaving. The prior aggregate failed with 1913 passed/100 skipped/four failures; those failures have targeted current repair evidence, but only a terminal fresh full aggregate can replace that result. Current aggregate is tracked separately; no completion claim while it is running. No commit, push, deployment or live migration/restore. Whole-system goal remains active.
