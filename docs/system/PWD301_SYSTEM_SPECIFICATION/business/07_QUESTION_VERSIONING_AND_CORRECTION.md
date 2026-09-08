# Question Versioning and Correction

## Confirmed rules
- Student not yet started gets latest valid revision.
- Started Attempt keeps frozen snapshot.
- Correct-answer-only change triggers eligible automatic regrade.
- Text/choice change gives full-credit policy to affected earlier attempts and never rewrites snapshot.
- Every exposed/graded revision is retained indefinitely.

## Primary persistence
`question_revisions`, `question_corrections`, `attempt_questions`, `regrade_jobs`, `regrade_items`.

## Implementation obligations
- Validate state and object authorization before mutation.
- Use service-owned transaction boundaries; do not rely on UI validation.
- Emit audit/notification/job side effects only according to documented event policy.
- Preserve historical evidence instead of rewriting past records.

## Failure semantics
State violations return a stable conflict/state error; authorization failures disclose no protected details; required-audit sensitive mutations roll back.

## Tests
Trace to `../testing/03_BUSINESS_RULE_TEST_MATRIX.md`, domain-specific integration tests and `../testing/11_END_TO_END_SCENARIOS.md`.
