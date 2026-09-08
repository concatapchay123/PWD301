# Question Bank

## Confirmed rules
- Question belongs to exactly one Course and optional same-Course Lesson.
- Unused Question may edit in place; used important edits produce a new revision.
- Choices and accepted answers belong to revision.
- Question type locks after any Student answer.
- Duplicate creates independent Question.
- Deleted used Question leaves historical identity/revisions.

## Primary persistence
`questions`, `question_revisions`, `question_revision_choices`, `question_revision_accepted_answers`, `question_provenance`.

## Implementation obligations
- Validate state and object authorization before mutation.
- Use service-owned transaction boundaries; do not rely on UI validation.
- Emit audit/notification/job side effects only according to documented event policy.
- Preserve historical evidence instead of rewriting past records.

## Failure semantics
State violations return a stable conflict/state error; authorization failures disclose no protected details; required-audit sensitive mutations roll back.

## Tests
Trace to `../testing/03_BUSINESS_RULE_TEST_MATRIX.md`, domain-specific integration tests and `../testing/11_END_TO_END_SCENARIOS.md`.
