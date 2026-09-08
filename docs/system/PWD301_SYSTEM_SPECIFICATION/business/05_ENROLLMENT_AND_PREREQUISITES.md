# Enrollment and Prerequisites

## Confirmed rules
- One logical Enrollment per Student/Course and at most one active period.
- Enroll checks Course availability, capacity and every prerequisite transactionally.
- Re-enroll restarts active progress but prior completion summary remains.
- Leave starts 30-day detailed-retention window.
- No rejoin after 30 days permits detail purge and excludes purged period from future regrade.
- Prerequisite graph cycles are forbidden.

## Primary persistence
`enrollments`, `enrollment_periods`, `enrollment_events`, `course_completion_summaries`, `course_prerequisites`.

## Implementation obligations
- Validate state and object authorization before mutation.
- Use service-owned transaction boundaries; do not rely on UI validation.
- Emit audit/notification/job side effects only according to documented event policy.
- Preserve historical evidence instead of rewriting past records.

## Failure semantics
State violations return a stable conflict/state error; authorization failures disclose no protected details; required-audit sensitive mutations roll back.

## Tests
Trace to `../testing/03_BUSINESS_RULE_TEST_MATRIX.md`, domain-specific integration tests and `../testing/11_END_TO_END_SCENARIOS.md`.
