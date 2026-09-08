# Assessment Engine

## Confirmed rules
- Types practice/quiz/midterm/final/placement.
- Open/close/time limit, attempt limit, scoring/release/visibility/pass policies are configurable.
- Blueprint can filter lesson/topic/difficulty/type/count; shortage blocks publish.
- Mandatory/fixed and random pool selection can coexist; question and choice shuffle optional.
- Timing freezes after publish; structure and points freeze after first Student start.

## Primary persistence
`assessments`, `assessment_sections`, `assessment_question_assignments`, `assessment_blueprints`, `assessment_blueprint_rules`, `assessment_question_pool`.

## Implementation obligations
- Validate state and object authorization before mutation.
- Use service-owned transaction boundaries; do not rely on UI validation.
- Emit audit/notification/job side effects only according to documented event policy.
- Preserve historical evidence instead of rewriting past records.

## Failure semantics
State violations return a stable conflict/state error; authorization failures disclose no protected details; required-audit sensitive mutations roll back.

## Tests
Trace to `../testing/03_BUSINESS_RULE_TEST_MATRIX.md`, domain-specific integration tests and `../testing/11_END_TO_END_SCENARIOS.md`.
