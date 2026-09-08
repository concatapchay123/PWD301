# Grading and Regrading

## Confirmed rules
- MCQ exact-set only; no partial credit.
- Short answer uses accepted answers with normalization unless exact mode.
- Essay manual; final may remain pending.
- Grade edits/history preserve old/new/reason/actor/time.
- Large regrade is background, resumable and idempotent.

## Primary persistence
`attempt_question_grades`, `attempt_question_grade_history`, `assessment_results`, `assessment_result_history`, `regrade_jobs`, `regrade_items`.

## Implementation obligations
- Validate state and object authorization before mutation.
- Use service-owned transaction boundaries; do not rely on UI validation.
- Emit audit/notification/job side effects only according to documented event policy.
- Preserve historical evidence instead of rewriting past records.

## Failure semantics
State violations return a stable conflict/state error; authorization failures disclose no protected details; required-audit sensitive mutations roll back.

## Tests
Trace to `../testing/03_BUSINESS_RULE_TEST_MATRIX.md`, domain-specific integration tests and `../testing/11_END_TO_END_SCENARIOS.md`.
