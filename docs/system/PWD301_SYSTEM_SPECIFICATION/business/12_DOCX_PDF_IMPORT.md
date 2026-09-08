# DOCX/PDF Import

## Confirmed rules
- Import always creates draft/review workflow.
- High-confidence parsed questions may proceed to draft; ambiguous items are flagged.
- No answer key means no official answer; AI may suggest but Instructor must explicitly confirm.
- Images are extracted, security checked and linked; broken images flag review.
- Duplicates only warn; never auto-merge.

## Primary persistence
`document_import_jobs`, `import_questions`, `import_duplicate_candidates`, `import_question_resources`, `ai_generated_question_drafts`.

## Implementation obligations
- Validate state and object authorization before mutation.
- Use service-owned transaction boundaries; do not rely on UI validation.
- Emit audit/notification/job side effects only according to documented event policy.
- Preserve historical evidence instead of rewriting past records.

## Failure semantics
State violations return a stable conflict/state error; authorization failures disclose no protected details; required-audit sensitive mutations roll back.

## Tests
Trace to `../testing/03_BUSINESS_RULE_TEST_MATRIX.md`, domain-specific integration tests and `../testing/11_END_TO_END_SCENARIOS.md`.
