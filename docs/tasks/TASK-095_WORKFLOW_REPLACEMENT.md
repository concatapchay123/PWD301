# TASK-095 — Authoritative workflow replacement and end-to-end remediation

Status: IN_PROGRESS
Branch baseline: main, 838e8b5eee09f8c485102d6d2eba0a325765951d, clean.
User approved the complete replacement plan on 2026-10-15.

## Source of truth and scope

See [replacement contract](../system/PWD301_SYSTEM_SPECIFICATION/implementation/WORKFLOW_SUPERSESSION.md).
The approved user plan overrides contrary historical workflow descriptions.
No commit, push, live SQL migration, reset, or deployment is authorized by a test.

## Execution ledger

- Phase 0: contract and targeted supersession written; contradiction gate and final audit IN PROGRESS.
- Backend course lifecycle/migration: IN PROGRESS; focused lifecycle tests pass, question-bank and broad regression integration remain.
- Media access and Admin review UI: IN PROGRESS; actual isolated HTTP authorization/HLS transport checks pass, native browser decode remains.
- Assessment summary/disclosure/PDF: implemented with focused policy tests and Linux vector-PDF visual proof; final regression integration remains.
- Instructor and learner frontend: implemented with focused Node tests; actual academic modal inspected on desktop/mobile; matching and exam browser gates remain.
- Integrated SQL, browser and full verifier: IN PROGRESS. Dedicated `pwd301_test_task095_20261016` created on 2026-10-16; live `PWD301` untouched.
- Ruling: work in the clean current checkout on a dedicated codex branch. This
  preserves the existing container source mounts; no unrelated work is present.
- Ruling: reuse the existing course-change aggregate rather than creating a
  duplicate CourseVersionChangeset table. Shared routing may use one small service
  to avoid circular imports across the existing course/lesson/completion services.
- Ruling: preserve legacy published rows lacking approved_at as review-required;
  never fabricate timestamps or treat missing metadata as free-authoring consent.

- Ruling: prerequisite eligibility is course completion in the canonical junction; remove the old UI-only minimum-grade field, which has no persisted/evaluated threshold. Restore valid course selection without inventing a new business rule.
- Ruling: an approved referenced asset cannot be revised or trashed in place; upload a replacement and change the reference through the same course draft. This preserves approved and historical bytes. New/unreferenced draft assets remain mutable; pending submissions freeze all mutation paths.
- Ruling: this task includes question-bank mutation routes because changing a shared current QuestionRevision would bypass course-wide staging. Preserve original identities and historical attempts through staged revisions, promoted only at approval.

## Reuse and removal

KEEP: existing aggregate, crop, matching controller, ReportLab layout, file
authorization, course locks, snapshot/audit/lease/security invariants.
REMOVE NOW: per-feature approval creation, client opt-in staging, lossy queue
dedup, email video gate, fake question counts and regex math renderer.
SIMPLIFY NOW: shared lifecycle, assessment summary and detail disclosure gates.

## A. Scope and sources consulted

Canonical system/business/invariant/API docs, canonical course/assessment DDL,
repository agent contract, approved plan, current implementation and tests.

## B. Reuse decisions

Pending implementation evidence.

## C. Per-file changes

Pending final diff inventory.

## D. Deletion/simplification list

See the replacement register; statuses are not passes until proved.

## E. Ponytails

None accepted. Any necessary limitation must be explicitly recorded with trigger,
owner, risk, safeguard and review point.

## F. Verification actually run

- Initial complete SQLite regression snapshot (2026-10-16): **1660 passed, 389 failed, 47 errors, 100 skipped**, 1606.18 seconds. This is an integration failure, not acceptance. It predates later asset, approval-boundary, JWT, disclosure and fixture corrections. Domain owners are reconciling obsolete fixtures and investigating remaining failures without relaxing security gates.
- Real disposable SQL Server: migration upgrade/downgrade/upgrade passed; the new migration repairs the preceding applied migration's SQL Server DEFAULT reversal without editing that applied migration. Five concurrent lifecycle/graph/approval/unique-index tests passed. Target: `pwd301_test_task095_20261016`; the live database remains untouched.
- Actual isolated HTTP media matrix: 25 checks passed, including unverified/verified enrollment, raw video denial, authorized Range, covers and AES-128 HLS manifest/key/segment transport.
- Actual Edge DOM: matching selects two pairs with neutral SVG lines, clears and accepts keyboard controls; instructor academic editor has prerequisite candidates on desktop/mobile without horizontal overflow. HLS decoded actual 320×180 video with currentTime >1, readyState4 and no media/page error. Prior-lesson completion was seeded in the disposable fixture for this playback interaction; this is not proof of server pacing.
- Actual waiting rooms show 3 assigned questions, HIGHEST10 with active3/3 and LATEST0 with exhausted2/2, without a false prerequisite lock.
- Linux ReportLab/MathJax PDFs were rendered and visually inspected: visible vector formulas and released totals; hidden-detail PDF retains overall8.5/10/pass and leaves three detail columns empty.
- Repository contract and four documentation anti-regression tests passed at their checkpoint; frontend suite314 passed before subsequent focused additions. Fresh full verification remains required after integration.

Independent review has reproduced and driven fixes for staged resources leaking to learners, initial APPROVED-before-publish promotion, omitted asset revision/scan identity, assessment-row approval races, question explanation leakage, missing JWT commits and incomplete review presentation. No intermediate focused pass closes the full acceptance gate.

## G. Remaining risks

Live database must never be used for destructive pytest fixtures. Verify an
isolated pwd301_test_* SQL target and explicit disposable flag first. Browser and
production-font PDF proof are separate from mocked/Node tests.
