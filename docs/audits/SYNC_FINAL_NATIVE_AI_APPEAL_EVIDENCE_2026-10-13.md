# Native standalone AI and appeal acceptance — 2026-10-13

Status: named local native acceptance passed for SYNC-035 and SYNC-037. Existing SQL concurrency acceptance remains distinct. Final Python aggregate is tracked separately.

## A. Scope and sources

Original synchronization audit, canonical assessment/history rules, actual Student AI and result controllers, staging viewport lifecycle in router.js, existing UI.refreshCurrentRoute, appeal HTTP routes and SQL audit records. All mutations use guarded disposable database `pwd301_test_browser_sync_20261012`; identity/head/owned fixture checked before use. No production account, email transport, provider credentials or live restore involved.

## B. Reuse

Standalone clear now uses the existing route refresh helper. The router moves rendered children from its staging container into the live viewport and detaches the staging container. Captured child roots still support request ownership, but that staging container cannot be a later rerender target. No router rewrite, new component or cache layer added.

Appeal acceptance reuses current create/publish/enroll/start/submit services to create a unique owned graded fixture. Setup creates the assessment/result through application services; it does not claim native Student exam entry or answer submission. Native result-page actions then use unchanged appeal routes and independently inspected SQL.

## C. Per-file changes

- `frontend/assets/js/views/student.js`: after invalidating generation/conversation, standalone Clear calls UI.refreshCurrentRoute instead of rendering into the detached captured staging container.
- `tests/frontend/ai_console_scope.test.js`: actual clear callback regression checks that it refreshes the active route and does not call the old captured renderer. Existing six controller regressions remain intact.
- This document and ledger/progress/manifest: exact native and failing-product evidence, retained provider boundaries.

## D. Simplification

One existing helper replaces one stale direct renderer call. No new application abstraction, dependency, schema or polling. Existing safe Markdown, owner/course/route/generation checks and serialized sending remain unchanged.

## E. Deferred gates

Actual Gemini remains a server/provider gate. Native AI responses come from the actual local backend with Gemini disabled; responses are held and released, never fabricated. SMTP is explicitly deferred by user. No optional debt added.

## F. Verification actually run

Product RED: native standalone Clear left the old connected transcript and user message on screen, then old completion removed its typing indicator. Diagnostic identified unchanged connected old root. Source investigation traced detached staging viewport. Actual callback Node RED: expected one route refresh, received zero; six other tests passed. After the one-line repair: focused Node7 pass; full frontend285 pass, zero fail/skip.

Clean standalone native runner exit0, two checks (`browser-ai-standalone-clean-final-20261013.log` and `browser-ai-standalone-local-evidence-20261013.json`):

1. Native Clear replaces connected transcript; held genuine HTTP200 cannot enter the new root; current controls remain enabled.
2. Enter while sending produces no duplicate request. Native course switch admits a new request; the old reply cannot append or enable its button; the current real HTTP200 completes its own request. Old typing element is allowed to remove itself.

Initial wrong route caused a harness timeout; corrected to the existing /student/ai-assistant route. After fixing Clear, an early context assertion incorrectly compared text including an old typing element that is legitimately removed. Final harness compares the current transcript excluding that owned old indicator, checks current disabled state and waits for each held route to finish before closing. These harness failures are not additional product regressions. Final run is clean, unlike the older console run's asynchronous routing diagnostic; that older limitation is retained in its report.

Clean appeal native runner exit0, three checks (`browser-appeal-local-20261013.log`, `browser-appeal-local-evidence-20261013.json`):

1. Native submit with controlled invalid CSRF yields actual HTTP400; note/dialog/retry retained, independent SQL shows zero appeal events.
2. Retry produces actual HTTP201 held after SQL commit. Exactly one appeal exists; UI has no optimistic pending label before ACK. Releasing ACK and F5 both show persisted pending status.
3. Actual public ApiClient duplicate request returns409; independent SQL count remains one. This sequential duplicate check does not replace the separate two-request SQL concurrency test.

Fresh OCR rules retrieved for student.js; host review checks generation invalidation before async refresh, connected root ownership, read-only route entry and retained context sending rules. No unresolved issue found in this scoped change. Full current Python/SQL reconciliation is reported separately and is not implied by these five native assertions.

## G. Limits

Loopback application and disposable SQL fixtures only. No Gemini transport certification, SMTP send, real B2 acceptance, full assessment-flow certification or deployment. Existing original audit remains unchanged.

Đã dùng 5 skill gồm: superpowers (test-driven-development, systematic-debugging, verification-before-completion), ponytail, task-observer, full-output-enforcement, open-code-review-delegate.
