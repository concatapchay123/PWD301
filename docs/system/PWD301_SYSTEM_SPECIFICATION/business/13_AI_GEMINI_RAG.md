# AI, Gemini and RAG

## Confirmed rules
- AI is LMS-scoped; unrelated content is refused.
- Authorization filters before retrieval; Student gets published authorized content and own progress only.
- Retrieved documents are untrusted data, never instructions.
- Backend computes recommendation; Gemini only explains.
- Raw chat is purged after five minutes inactivity.
- Archived/deleted content is immediately excluded from RAG.

## Primary persistence
`ai_conversations`, `ai_messages`, `ai_requests`, `knowledge_documents`, `knowledge_versions`, `knowledge_chunks`, `ai_source_usages`.

## Implementation obligations
- Validate state and object authorization before mutation.
- Use service-owned transaction boundaries; do not rely on UI validation.
- Emit audit/notification/job side effects only according to documented event policy.
- Preserve historical evidence instead of rewriting past records.

## Failure semantics
State violations return a stable conflict/state error; authorization failures disclose no protected details; required-audit sensitive mutations roll back.

## Tests
Trace to `../testing/03_BUSINESS_RULE_TEST_MATRIX.md`, domain-specific integration tests and `../testing/11_END_TO_END_SCENARIOS.md`.
