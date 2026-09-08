# Data Lifecycle and Retention

## Confirmed rules
- Use soft delete/trash/archive before hard delete where history exists.
- Course/Lesson/Question/Assessment have ~30-day recovery when applicable.
- Historical attempt/grade/revision evidence is not broad-cascade deleted.
- Enrollment detail may purge after 30 days without rejoin; compact completion summary remains.
- Important audit retained indefinitely; old audit may move archival storage.
- AI raw chat purged after five minutes inactivity.

## Primary persistence
`enrollment_periods`, `course_completion_summaries`, `question_revisions`, `assessment_attempts`, `audit_events`, `ai_conversations`.

## Implementation obligations
- Validate state and object authorization before mutation.
- Use service-owned transaction boundaries; do not rely on UI validation.
- Emit audit/notification/job side effects only according to documented event policy.
- Preserve historical evidence instead of rewriting past records.

## Failure semantics
State violations return a stable conflict/state error; authorization failures disclose no protected details; required-audit sensitive mutations roll back.

## Tests
Trace to `../testing/03_BUSINESS_RULE_TEST_MATRIX.md`, domain-specific integration tests and `../testing/11_END_TO_END_SCENARIOS.md`.
