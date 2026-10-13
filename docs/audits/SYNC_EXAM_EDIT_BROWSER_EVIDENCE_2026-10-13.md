# Exam editing browser evidence — 2026-10-13

Status: SYNC-007/008/025 named runtime gates verified; whole-system work IN_PROGRESS.

## A. Scope and source of truth

Original audit historical requirements SYNC-007 (nested question hydration/editing), SYNC-008 (canonical attempt limit) and SYNC-025 (real accepted short answers). Inspected the current closure ledger, existing authoring/Quick Add evidence, assessment detail/serialization/settings routes, question serializer, canonical assignment model and actual frontend callers. Reuse the guarded browser environment and legal service-created draft assessment.

## B. Reuse decisions

Existing source safeguards worked under this acceptance run. No new source repair, dependency, UI layer or migration is needed for these tested paths. The runner uses the real login, CSRF, native HTTP, DOM forms, SQL Server and F5 rather than mocking the API or seeding the ExamStore question under test.

## C. Per-file changes

This evidence file, closure ledger, progress report and manifest record the new runtime proof. Ignored runner `browser_exam_edit_verify.py` extends existing browser verification with native actions and independent SQL assertions; application source is unchanged in this increment.

During the concurrent aggregate, `tests/api/test_admin_audit_api.py::test_admin_unsuspend_user_flow` failed because its initial suspend request omitted mandatory reauthentication and confirmation phrase and never checked its response. It consequently tested an already-active no-op and incorrectly expected an unsuspend audit event. The test now supplies the established credentials/phrase and asserts successful SUSPENDED state before unsuspending. Product authorization and idempotent no-op audit behavior are preserved. This supporting test fixture is the only additional source/test edit in this increment.

## D. Simplification

KEEP existing serializers, Quick Add validation and settings mapping. No replacement CRUD abstraction or speculative fix.

## E. Debt and unfinished work

No new deferred debt. These seven checks are overlapping path acceptance, not seven independent features. Broader current-source aggregate is running separately and not counted as a pass here. External providers and remaining per-ID gates are not certified.

## F. Actual verification

`browser-exam-edit-complete-20261013.log`: **seven browser checks passed**, process exit 0. `browser-exam-edit-evidence.json` records the exact results:

1. SHORT_ANSWER with empty accepted alternatives remains in the form, produces no create request and leaves SQL assignments empty.
2. Actual Quick Add creates two alternatives; F5 reads one correct short-answer question with two accepted alternatives.
3. Settings PATCH stores attempt_limit=3; independent SQL and reloaded input agree.
4. Clearing the limit stores SQL NULL and remains blank after F5; no coercion to one.
5. Opening Studio from real assessment detail hydrates the same public question identity, exact stem/type and both accepted alternatives. F5 retains them and the unlimited configuration.
6. Actual question-edit POST persists 2.25 assigned points; independent SQL and F5 agree.
7. Confirmation and DELETE remove only the assessment assignment; SQL retains the bank question and F5 contains no assigned question.

Guard: acknowledged disposable target `pwd301_test_browser_sync_20261012`; actual DB_NAME and migration head `syncprogress20261011` checked, baseline course code `SYNC-BROWSER-101` verified. New assessment fixture belongs to the actual Instructor. Edge headless, actual password login, CSRF enabled, Gemini disabled. No live database mutation or provider call.

Three harness errors were corrected before the final complete run: waiting for PUT instead of the actual settings PATCH; case-sensitive UUID comparison against SQL Server's uppercase UNIQUEIDENTIFIER representation; querying AttemptQuestion's points_assigned name on AssessmentQuestionAssignment, whose canonical column is points. These are probe failures, not product defects. Intermediate successful checks were not substituted for the final complete exit-0 run.

OCR delegate engineering/rules from the prior authoring/Quick Add review remain source-review evidence; this increment does not claim a fresh independent review of all source files. The supporting test review is recorded below.

Aggregate diagnosis RED: one failure/one pass with `-x`, `admin-audit-aggregate-diagnosis-20261013.log`. After correcting the real fixture precondition, the whole Admin audit module has **6 SQLite passed** (3.57 seconds) and **6 SQL Server passed, zero skips** (14.07 seconds), both exit 0. SQL target `pwd301_test_attempt_admission_sync_20261013` verified by actual DB_NAME/head before destructive fixtures. Logs: `admin-audit-fixture-green-20261013.log`, `sqlserver-admin-audit-current-20261013.log`. OCR fresh preview/rules generated and the supporting test change reviewed for real transition coverage and preserved security requirements; no unresolved finding. Ruff, format, diff and repository checks pass. The ongoing aggregate contains the pre-correction failure and cannot be labeled passing even if all subsequent tests succeed; a fresh full run is required after it reaches terminal state.

## G. Limits

No claim about all question types or every concurrency interleaving. Existing separate atomic authoring and lease/race evidence remains separately scoped. No commit, push, deployment or live migration. Whole-system remediation remains IN_PROGRESS.
