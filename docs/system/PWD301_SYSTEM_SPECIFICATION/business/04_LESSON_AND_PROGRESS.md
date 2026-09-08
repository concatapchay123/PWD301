# Lesson and Progress

## Confirmed rules
- Lesson order is mutable globally; prior completion remains.
- Completion requires meaningful minimum time and viewed-most evidence.
- Progress cache is derived; lesson_progress/results are authoritative.
- Material rewrite does not reset completed students.
- New lesson is optional Xem thêm for existing periods/completed learners.

## Primary persistence
`lessons`, `lesson_progress`, `enrollments`, `enrollment_periods`, `course_completion_rules`.

## Implementation obligations
- Validate state and object authorization before mutation.
- Use service-owned transaction boundaries; do not rely on UI validation.
- Emit audit/notification/job side effects only according to documented event policy.
- Preserve historical evidence instead of rewriting past records.

## Failure semantics
State violations return a stable conflict/state error; authorization failures disclose no protected details; required-audit sensitive mutations roll back.

## Tests
Trace to `../testing/03_BUSINESS_RULE_TEST_MATRIX.md`, domain-specific integration tests and `../testing/11_END_TO_END_SCENARIOS.md`.
