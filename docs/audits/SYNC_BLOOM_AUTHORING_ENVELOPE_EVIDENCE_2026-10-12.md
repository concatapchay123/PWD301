# Bloom rejection and authoring acknowledgement — 2026-10-12

## A. Scope and source contracts

SYNC-024 canonical Bloom preservation/rejection and the dependent SYNC-079 authoring/publish retry path. Consulted original audit, existing canonical assessment authoring contract and allowed REMEMBER/UNDERSTAND/APPLY model constraints. The original report is unchanged. Goal remains IN_PROGRESS for all other outstanding requirements.

## B. Reuse and C. Per-file changes

`frontend/assets/js/api.js`: the existing atomic authoring endpoint returns `{success, data, error}`. Its wrapper previously returned the entire envelope while Publish Studio read `response.questions` and `response.authoring_token`. An actual valid browser publication saved on the server, then failed with “Invalid authoring acknowledgement”. The wrapper now returns `response.data`, retaining compatibility with an already unwrapped response. Existing shared request/auth/CSRF/error handling is reused.

`tests/frontend/exam_authoring_atomic.test.js`: added a realistic enveloped acknowledgement test, which failed before the wrapper fix and passed after it. The existing helper-only Bloom test could not catch this integration defect.

`tests/api/test_instructor_backend_remediation.py`: expanded rejection to ANALYZE/EVALUATE/CREATE. A valid first question followed by unsupported input must return 400 without changing the assessment title, adding assignments or creating a question.

Evidence documents and per-ID ledger updated; browser and guarded SQL runners/logs are retained in the ignored task output directory. No dependency, endpoint, migration or duplicate service added.

## D. Simplification and E. Deferred scope

Reused the standard JSON payload instead of weakening Publish Studio's identity/acknowledgement checks. No speculative abstraction, deletion or new shortcut. Previous browser evidence alone was insufficient to prove the current wrapper; it is supplemented by the fresh runs below.

## F. Executed verification

- Node RED: realistic authoring envelope fails the new wrapper contract test before the product fix. Current full frontend GREEN: **255 passed / zero failed or skipped**, exit 0; `frontend-bloom-envelope-green.log`.
- Guarded SQL Server API selection: **3 passed / 32 deselected in 9.27s**, exit 0. Target `pwd301_test_bloom_sync_20261012`, actual DB_NAME and head `syncprogress20261011` verified before fixture use; `sqlserver-bloom-sync.log`. Deselected cases are not counted as passes.
- Actual Edge/Flask/independent SQL: **four Bloom checks passed**, exit 0; `browser-bloom-final-current.log` and `browser-bloom-evidence.json`. Each unsupported level is preserved in the draft across F5, actual publish confirmation displays the rejection, zero instructor mutation requests are sent and SQL assessment/question/assignment counts remain unchanged. Correcting the retained draft to APPLY then publishing succeeds; independent SQL confirms PUBLISHED/APPLY.
- Fresh affected browser regression: **three checks passed**, exit 0; `browser-publish-envelope-current.log`. Server publish commits before the response is dropped; durable question/assessment checkpoints survive reload; retry recovers the same published assessment with one assignment. Composite academic save/F5 also passes in that runner. Checks overlap existing scopes and must not be summed as independent features.
- Global Ruff check, format **340 Python files**, mypy **96 source files**, compileall, repository and diff checks pass. OCR delegation preview/rules were generated; host review inspected the two-line wrapper normalization against the server envelope, shared failure handling and stable publish identity guards.

Probe limitations/corrections: the new backend test initially omitted its local Question import; a probe query initially looked for difficulty on QuestionRevision instead of Question. The recovery fixture initially omitted explicit matrix confirmation after editing the question. These were corrected harness errors and are not product RED phases. The wrapper/envelope mismatch was a separately observed real product failure and has its own failing test.

## G. Remaining limits

Only these authoring/Bloom/retry requirements are verified here. This is not a final current-source aggregate, external provider gate, sustained-load proof or deployment-readiness claim. No commit, push, deployment or live database change.
