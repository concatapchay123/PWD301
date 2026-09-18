## 2026-09-14T12:49:23Z
You are challenger_m3_1, a teamwork_preview_challenger subagent.
Your working directory is: e:\PWD301\.agents\teamwork_preview_challenger_m3_1
Your role is: Milestone 3 Invariant Challenger
Your parent conversation ID is: 5f234e51-df3a-4989-b3f8-7adc52e9513d

MANDATORY INPUTS:
- ORIGINAL_REQUEST: e:\PWD301\.agents\ORIGINAL_REQUEST.md (You MUST read this before starting work)
- PROJECT.md: e:\PWD301\.agents\PROJECT.md
- Worker M3 Handoff: e:\PWD301\.agents\teamwork_preview_worker_m3\handoff.md

TASK:
Adversarially challenge Invariants 13 & 14 for Milestone 3:
1. Invariant 13 (Timing Lock - BR-031):
   - Publish an assessment (status == 'PUBLISHED').
   - Attempt to modify open_at, time_limit_minutes, attempt_limit -> MUST be rejected with AssessmentLockedError / 409.
   - Extend close_at forward into the future -> MUST be allowed.
   - Shorten close_at -> MUST be rejected.
2. Invariant 14 (Structural Freeze - BR-030):
   - Simulate a started student attempt (set first_attempt_started_at).
   - Attempt to create question via POST /assessments/<assessment_id>/questions/create -> MUST be rejected (409).
   - Attempt to edit question content or points via POST /assessments/<assessment_id>/questions/<question_id>/edit -> MUST be rejected (409).
   - Attempt to remove question via POST /assessments/<assessment_id>/questions/<question_id>/remove -> MUST be rejected (409).
   - Attempt to import document via POST /assessments/<assessment_id>/import -> MUST be rejected (409).
3. Execute empirical tests and verify results.
4. Produce a detailed handoff.md in your working directory with explicit verdict: APPROVE or REQUEST_CHANGES.
5. Report your verdict to parent via send_message.
