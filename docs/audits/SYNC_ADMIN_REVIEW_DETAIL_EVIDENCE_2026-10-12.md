# Admin review detail and unavailable reads — 2026-10-12

## A. Scope and observed defects

Addresses SYNC-050 and SYNC-055 against the original synchronization audit, the canonical Admin API and existing course-review permissions. The original audit remains unchanged. No commit, push, deployment or live database migration.

The existing frontend sent `request_id` for exact review detail, but the backend ignored it and returned the pending queue. A genuine browser probe could not retrieve an independently confirmed APPROVED request. Ten new API cases failed before the product repair: four completed states, five invalid identifiers and a missing request.

The real browser also showed that successful queue retry left its previous unavailable notice displayed. A new Node test failed before that repair. Two more Node tests showed APPLIED and CANCELLED details mislabeled as rejected; both failed before the label correction.

## B. Reuse and C. Per-file changes

- `src/pwd301/blueprints/admin/routes.py`: reuse existing authenticated `COURSE_REVIEW` authorization, serializer and query. Exact positive BIGINT request IDs bypass queue status filtering; invalid input returns 400, missing ID 404. Aggregate queue behavior stays pending-only. No new endpoint, service, table or dependency.
- `frontend/assets/js/views/admin.js`: remove the stale unavailable notice only after both authoritative queue reads succeed; render accurate labels for all five canonical request states. Preserve existing controls and error/retry workflow.
- `tests/api/test_admin_change_requests_review.py`: terminal-state detail isolation, pending queue preservation, invalid/missing identity and non-Admin rejection.
- `tests/frontend/sync_admin_remediation.test.js`: successful queue recovery removes its prior failure notice.
- `tests/frontend/course_review_regression.test.js`: APPLIED/CANCELLED label checks; correct two DOM fixtures so unrelated selectors return null instead of the review box.
- `tests/api/test_admin_subroles_and_enhancements.py`: remove one obsolete manual account cleanup that violated the SQL AuthSession FK. Shared guarded test teardown performs cleanup; no production constraint is weakened.
- Canonical Admin API, closure ledger, progress and manifest: document exact detail semantics and evidence boundaries.

## D. Simplification and E. Deferred scope

Removed redundant, invalid manual test cleanup. Added no speculative abstraction. Remaining synchronization findings stay tracked independently. No new deferred implementation shortcut.

## F. Executed verification

- API RED: **10 failed / 12 deselected**, original missing exact-detail behavior. SQLite API GREEN: **22 passed in 29.26s**, before the two additional authorization cases.
- Guarded SQL Server selection: **28 passed in 94.95s**, no skips, exit 0. Target `pwd301_test_review_detail_sync_20261012`, verified actual DB_NAME and migration head `syncprogress20261011` before fixtures. Includes all terminal/invalid/missing-detail cases and six subrole/API tests. The first SQL run had 27 passed/one failure from the obsolete manual test cleanup described above.
- Additional two unique authorization cases passed on the same guarded SQL target: **2 passed / 22 deselected in 5.74s**, exit 0. An initial runner listed the file twice, giving four overlapping executions; duplicate counts must not be treated as four unique cases. The corrected focused terminal log is `sqlserver-review-permission-sync.log`.
- Current full frontend: **254 passed, zero failed/skipped**. Log `frontend-review-detail-final.log`. Initial broad run had two mock-selector failures; corrected fixtures model native DOM selector behavior.
- Actual Edge/Flask/SQL browser runner: **five checks passed**, exit 0. Log `browser-review-catalog-green.log`, evidence `browser-review-read-evidence.json`. Admin transport failure preserves previously loaded rows, actual retry reloads the server and removes the error. Approved request direct URL and F5 succeed while aggregate queue transport is deliberately unavailable. Separate Student login plus failed my-learning read produces an unavailable catalog with no false enrollment buttons; actual retry restores a course confirmed in the authoritative enrollment response.
- Global compileall, Ruff check/format **340 Python files**, mypy **96 source files**, repository contract and diff checks pass. OCR delegation preview/rules were generated; host review checked authorization before identity lookup, bound SQL parameters, BIGINT limits, queue isolation, escaped status output and notice recovery.

Browser setup initially tried to find a completed request in the deliberately pending-only aggregate and assumed one historical fixture course would still be shown in the catalog. Those probe assumptions were corrected using independent SQL and the actual enrollment response. They are not counted as product RED phases. The exact backend omission and stale retry notice were product failures and were separately reproduced before repair.

## G. Limits

These gates prove this review/read scope only. Browser direct revisit uses a real APPROVED request; other terminal labels have Node coverage and exact detail reads have SQL API coverage. SMTP, B2, ClamAV, external AI/video providers, sustained load and the final aggregate across all latest repairs remain separate gates. No whole-system completion or deployment-readiness claim.
