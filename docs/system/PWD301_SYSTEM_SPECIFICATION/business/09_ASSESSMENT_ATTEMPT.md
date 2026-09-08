# Assessment Attempt

## Confirmed rules
- Attempt generated on demand and freezes exact revision/text/choices/order/points.
- Deadline is server-authoritative min(start+limit, close).
- Only one live editor lease; stale owner takeover keeps same Attempt.
- MCQ saves immediately; text/essay debounced 1–2s.
- Late/offline stale writes cannot overwrite newer state or pass deadline.
- Submit retry returns same logical result.

## Primary persistence
`assessment_attempts`, `attempt_questions`, `attempt_choice_snapshots`, `attempt_answers`, `attempt_answer_events`, `assessment_results`.

## Implementation obligations
- Validate state and object authorization before mutation.
- Use service-owned transaction boundaries; do not rely on UI validation.
- Emit audit/notification/job side effects only according to documented event policy.
- Preserve historical evidence instead of rewriting past records.

## Failure semantics
State violations return a stable conflict/state error; authorization failures disclose no protected details; required-audit sensitive mutations roll back.

## Tests
Trace to `../testing/03_BUSINESS_RULE_TEST_MATRIX.md`, domain-specific integration tests and `../testing/11_END_TO_END_SCENARIOS.md`.
