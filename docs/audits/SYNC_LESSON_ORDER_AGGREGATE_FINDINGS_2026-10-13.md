# Lesson ordering and current aggregate findings — 2026-10-13

Status: IN_PROGRESS. Within-chapter order repaired; cross-chapter atomic move remains OPEN.

## A. Scope and authority

Historical SYNC-020 optimistic move/rollback, related SYNC-012 placement and current aggregate regressions. Inspected original audit/closure ledger, current Instructor tree handlers, existing reorder route/service, assignment/lease authority and Algorithm 07, Admin audit and maintenance middleware. Database course lesson positions are global; reorder_lessons requires the complete active course order.

## B. Reuse

Reuse existing course-wide reorder endpoint/service, snapshot rollback and native tree controls. No new infrastructure or dependencies. Preserve configured lease, durable fail-closed maintenance, suspension confirmation and idempotent Quick Add acknowledgement.

## C. Per-file changes

- `frontend/assets/js/views/instructor.js`: four lesson-order payload sites now flatten the complete current course tree rather than submitting only the source/destination chapter's IDs. This fixes valid moves within a chapter of a multi-chapter course; cross-chapter two-request composition is still insufficient.
- `tests/frontend/lesson_course_order.test.js`: invokes the real move-down handler against a two-chapter fixture and requires all course IDs plus unchanged sibling chapter.
- `src/pwd301/blueprints/instructor/routes.py`: locked assessments reject new/unknown Quick Add requests before invalid question-payload validation. A stable ID already assigned to this assessment can reach existing exact replay validation, retaining lost-ACK recovery after the first student starts; later mutation guard remains.
- `tests/api/test_student_exam_backend_remediation.py`: obsolete full-exam lease assertion replaced with canonical independently configurable thirty-second lease and retained sixty-minute exam deadline. Test renamed accordingly.
- `tests/security/test_security_remediation.py`: ProxyFix test uses guarded app fixture; its separate SQLite app initializes maintenance schema before the real request and disposes only that private in-memory schema. Migrated disposable SQL schema is prepared by the shared fixture. No maintenance bypass or fake middleware response.
- Evidence, ledger, manifest and progress record exact partial closure and aggregate results. Original audit untouched.

## D. Simplification

Replace incomplete order lists using existing tree data. KEEP backend complete-set validation and transactional ordering. Do not weaken leases or maintenance fail-closed handling to satisfy obsolete tests.

## E. Required work remains

**OPEN_CROSS_UNIT_ATOMIC:** native drag first commits `updateLesson(learning_unit_id)` then makes a separate reorder request. If the second request fails, snapshot rollback misrepresents the already-committed placement. Actual browser/SQL assertion fails after the within-chapter repair; `browser-cross-unit-atomic-red-20261013.log`. Need one atomic move/order transaction, preserving published-course review and returned draft/review identity; do not merely compensate by blindly moving back or showing unconditional success. This is required unfinished work, not optional debt.

## F. Actual verification

Current aggregate `scripts/verify.ps1`, explicit `sqlite:///:memory:`, terminal exit 1: **1913 passed, 100 skipped, 4 failed**, 1135.17 seconds. Log `aggregate-current-20261013.log`. Compile, lint/format/types and frontend gates reached before pytest, but the whole verifier failed. The failures were:

1. Unsuspend fixture omitted mandatory suspension password/confirmation and never asserted its unsuccessful precondition. Corrected earlier; Admin module SQLite6/SQL6 pass in its dedicated evidence.
2. Lease test demanded an exam-length editing lease, contrary to configurable Algorithm 07. Corrected canonical test; full deadline remains.
3. Separate ProxyFix app lacked tables; middleware correctly denied unknown maintenance authority503. Corrected schema fixture, preserving real middleware.
4. New-question invalid payload returned400 before structural-freeze409. Repaired admission precedence while preserving exact idempotent replays.

Fresh affected backend selection: **73 passed**, exit0, 72.87 seconds; `aggregate-failures-affected-green-20261013.log`. Focused three regressions pass, exit0, 2.10 seconds. Current frontend: **265 passed, zero failures/skips**, exit0; `lesson-course-order-frontend-green-20261013.log`.

Within-chapter product RED: actual native move-down POST receives409 for two IDs when course has three; `browser-lesson-order-product-red-20261013.log`. Node real-handler RED precedes source change. GREEN browser: **two checks**, exit0; `browser-lesson-order-complete-20261013.log`:

- Real move stores full course order; independent SQL and F5 agree, sibling chapter untouched.
- Aborted reorder restores the tree, SQL order remains unchanged and F5 agrees.

Cross-unit native drag RED separately confirms SQL placement already moved while the failed second request causes UI rollback. Do not count that path as passing. Browser target `pwd301_test_browser_sync_20261012`, actual DB_NAME/migration head/baseline fixture ownership verified. Unique course/chapters/lessons created through legal services; actual Instructor login, CSRF and HTTP. Initial detached fixture reference and error-toast phrase mismatch were harness errors corrected before the corresponding final product assertion/run.

Ruff/format pass (341 files), mypy96 pass; OCR fresh preview/rules for this increment. Host review examines all five changed source/test files, payload completeness, sibling preservation, replay admission, schema lifecycle and security retention. Cross-unit composition is an unresolved finding explicitly above. Full repository/diff checks pass after evidence updates.

Guarded affected SQL rerun is terminal exit0: **43 passed, zero skips**, 152.04 seconds; `sqlserver-aggregate-repairs-20261013.log`. Includes real Quick Add HTTP/SQL retry/freeze/fault/precision cases, full Instructor backend remediation API and the three aggregate regressions named above. Actual DB_NAME `pwd301_test_quick_add_retry_20261012` and migration head `syncprogress20261011` verified before fixtures. Overlaps earlier selections; do not sum them. Does not prove cross-unit move atomicity.

## G. Limits

No fresh aggregate pass. The 100 skipped tests require current-source SQL set reconciliation; the older66 reconciliation cannot cover this newer set automatically. Published move/approval and stale selection remain separate runtime requirements. No commit, push, deployment, live migration or live database mutation. Whole-system goal remains active.
