# Mini-quiz authored threshold and persistence — 2026-10-13

Status: named SYNC-030 acceptance verified; whole-system IN_PROGRESS.

## A. Scope and authority

Historical SYNC-030, current server-authoritative mini-quiz completion, Student delivery, native Course console and persistence after reload. Inspected existing mini-quiz scoring, both supported metadata spellings, Student serializer, completion API and existing regression fixtures. Preserve authorization, authored thresholds and existing server time/video gates.

## B. Reuse

Use the existing serializer and quiz completion API. Reuse the scoring service's already-supported `mini_quiz_passing` and `quiz_passing_percent` names in delivery. Keep existing UI retry, CSRF refresh and completion hydration. No new helper, dependency, endpoint, schema, migration or frontend asset.

## C. Per-file changes

- `src/pwd301/blueprints/student/routes.py`: Student lesson serializer recognizes both supported metadata names, retaining the existing displayed50–100 range. Previously alias50/100 delivered80, causing the UI to disagree with the server and refuse a score the server would accept.
- `tests/unit/test_sync_course_remediation.py`: four delivery cases cover both spellings at50/100 using actual serialization; two alias cases fail before repair.
- Evidence report, ledger, progress and manifest updated. Native runners and logs remain ignored runtime artifacts; original audit unchanged.

## D. Simplification

Extend the existing regular expression to match the server's supported spellings; do not duplicate scoring or add another threshold store. No deletion of safeguards.

## E. Deferred work

No optional debt introduced. These fixtures intentionally use zero required seconds and no video to isolate quiz acceptance; they do not certify video pacing or minimum-duration completion. Existing timing/video policies were not altered. Raw malformed/out-of-range imported metadata is outside these valid authored50/100 cases.

## F. Actual verification

RED: four serializer cases yielded2failed/2passed before product repair (`quiz-threshold-delivery-red-20261013.log`). Native alias50 rendered80 and failed the authored-threshold assertion (`browser-mini-quiz-product-red-20261013.log`), after canonical50 already passed. Earlier browser probe used the previously rendered lesson before async route resolution completed; its timeout is harness evidence, not the product RED. Final runner waits for the exact requested lesson body identity.

GREEN: whole affected course synchronization module **28 passed** on SQLite,25.40s (`quiz-threshold-sqlite-green-20261013.log`). The same affected module passed28 on guarded migrated SQL Server in89.59s, zero failed/skipped, terminal exit0 (`sqlserver-quiz-threshold-20261013.log`). The SQL runner checks actual DB_NAME and migration head before destructive pytest fixtures. Fresh Ruff check passes, format342files passes, mypy96sourcefiles passes and compileall passes. Frontend source was unchanged by this repair; previous full278 remains its separately scoped gate, not a fresh entire-backend result.

Native Edge **six checks passed**, terminal exit0 (`browser-mini-quiz-final-20261013.log`, `browser-mini-quiz-evidence.json`):

1. Zero correct answers under50% send no quiz completion write and persist no completion; retry remains available.
2. Real backend400 from a controlled invalid CSRF request header leaves SQL incomplete, reports unsaved results and enables native retry with the same answers. Existing ApiClient CSRF refresh/retry produces more than one rejected request; final harness checks the actual rejected count rather than assuming one attempt.
3. Canonical50: one of two correct answers succeeds through real POST; independent SQL stores completion and quiz acknowledgement; F5 restores authoritative saved state.
4. Alias50: same native behavior, correct50% display, SQL and F5.
5. Strict100: native50% attempt sends no completion write. A direct call through the real ApiClient completion wrapper returns a server validation error naming100%; independent SQL remains incomplete.
6. Strict100: native two-correct retry succeeds, persists SQL acknowledgement and F5 state.

The CSRF fault is applied only at the request boundary; no completion response, service, score or SQL write is mocked. Courses/lessons are unique owned fixtures created through existing services, published through existing workflow, then enrolled through the service. Guarded DB_NAME, migration head `syncprogress20261011` and baseline fixture ownership checked before execution. No production/live records touched. Final runner has no exception diagnostic.

OCR delegate preview and resolved rules retrieved for both changed files. Host review confirms both patterns match the same valid metadata as scoring, canonical behavior/clamping preserved, no new write in serialization, authorization unchanged, real serializer tests and truthful fixture limits. No unresolved defect found in this scoped change.

## G. Remaining gates

The earlier aggregate1928/100skip and exact SQL100/0skip precede this Python repair. Do not present them as a newly executed full current-source aggregate. This increment has affected-module, browser and static evidence; remaining audit/runtime/provider gates stay active. No commit, push, deployment, live migration or restore performed.
