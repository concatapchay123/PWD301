# AI chat scope and verification reconciliation — 2026-10-13

Status: named SYNC-035 UI lifecycle repaired; whole-system IN_PROGRESS.

## A. Scope and authority

Original synchronization audit, existing Course console and standalone Student AI controllers, session ownership, course/lesson context and current repository constraints. Preserve the original audit and unrelated work. Reuse the existing authorized AI endpoint, response parser and safe Markdown renderer; no provider or business contract change.

## B. Reuse decisions

Keep local controller state. Request generation, captured owner/role, route, lesson/course context and connected DOM scope determine which request may update the current conversation. No new dependency, endpoint, data store or polling service.

## C. Per-file changes

- `frontend/assets/js/views/student.js`: Course console captures its DOM root and scopes transcript/input/button lookup to it. New Chat resets generation, conversation and sending state immediately. Selecting a different unlocked item resets that chat context. A request removes only its own typing element; late success, error and finally callbacks cannot affect another generation, root, owner/role, route or lesson. Standalone chat serializes sending, permits a new request after explicit context switch and fences replies/errors/button release/focus against the same request scope.
- `tests/frontend/ai_console_scope.test.js`: six regressions execute actual controller code, covering New Chat plus overlapping responses, root replacement, owner/role/route/lesson change, standalone context switch, duplicate sends and late errors. No duplicate implementation used as the expected result.
- This report, closure ledger, progress and change manifest record exact verification boundaries.

## D. Deletion and simplification

Remove global timestamp-ID lookup for pending console typing indicators. Retain the actual element reference, avoiding collisions between old and new requests. Replace unconditional finally-side unlocking/focus with request ownership checks. No extra infrastructure or asset layer.

## E. Deferred work

No optional technical debt introduced. Actual Gemini/B2/SMTP/YouTube provider gates and unrelated audit requirements remain separate. The standalone UI has direct-handler regressions; native browser acceptance below exercises the Course console. No standalone native-browser certification claim.

## F. Actual verification

RED: actual native New Chat with a held real backend HTTP200 allowed the old reply into the new transcript (`browser-ai-console-product-red-20261013.log`). Three initial console Node regressions failed on actual assertions before the console repair. Two additional standalone regressions then failed before its repair. Early browser probes incorrectly expected503; those harness failures are not product RED evidence. The backend supplies a bounded local response with Gemini disabled.

GREEN: full frontend **278 passed, zero failed/skipped**, exit0 (`frontend-ai-scope-final-20261013.log`). Six new controller regressions pass. Original audit diff is empty; full worktree diff check passes with line-ending notices only.

Native browser: one clean New Chat acceptance passes (`browser-ai-console-green-20261013.log`). The expanded runner asserts and records three checks, exit0 (`browser-ai-console-verified-20261013.log`, `browser-ai-console-evidence.json`):

1. Held real HTTP200 cannot repopulate a new conversation.
2. Two held real HTTP200 requests: old completion leaves the new transcript and disabled send button unchanged; current completion removes its own indicator and enables its button.
3. Controlled invalid CSRF request header produces actual backend HTTP400; its late error cannot enter the new conversation.

The expanded Playwright runner also emits an asynchronous routing `CancelledError` callback diagnostic. All three acceptance assertions and its process complete successfully, but this is not a clean harness log. Preserve that limitation; the first single-case runner is clean. No provider response is fabricated and no Gemini connection is certified. Guarded browser DB_NAME, migration head and owned fixture course checked before use.

The previously active aggregate command is now terminal: **1928 passed, 100 skipped**, exit0, repository checks/compile/Ruff/format/mypy passed (`aggregate-after-atomic-move-20261013.log`). Its initial frontend gate predates the later chapter-matrix and AI changes. Python source did not change after this aggregate began; fresh frontend278 covers those JS changes. Do not count the100 skips as passes. A separate exact100-test SQL Server reconciliation passed100/0failed/0skipped in470.34s, exit0, against newly created `pwd301_test_complete_sql_gates_20261013`; actual target identity is checked, existing databases are refused, and disposable guard enabled. Final selected and PASSED node IDs match exactly100/100; selection and reconciliation JSON retained.

Fresh OCR delegate preview and rules retrieved for the source/test files. Host review checks root/owner/context isolation, generation ordering, captured typing element lifetime, stale success/error/finally effects, serialization, safe Markdown reuse and unchanged API contract. No unresolved defect found in this scoped review; no whole-system approval inferred.

## G. Remaining limits

Whole-system remediation remains active. The SQL skip reconciliation is complete; remaining per-ID/runtime/provider gates must be resolved individually. No commit, push, deployment, live database migration or restore performed.

## Superseding standalone native acceptance — 2026-10-13

Standalone native verification exposed and repaired a remaining detached staging-container Clear bug after genuine browser/callback RED. Two clean actual-HTTP native checks now pass, with full frontend285. This supersedes the preceding standalone-native pending limitation; Gemini certification remains outside local scope. Exact A–G evidence and harness corrections: SYNC_FINAL_NATIVE_AI_APPEAL_EVIDENCE_2026-10-13.md.
