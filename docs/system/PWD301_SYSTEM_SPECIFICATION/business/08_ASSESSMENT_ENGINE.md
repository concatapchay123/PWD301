# Assessment Engine

## Confirmed rules
- Types practice/quiz/midterm/final/placement.
- Open/close/time limit, attempt limit, scoring/release/visibility/pass policies are configurable.
- Blueprint can filter lesson/topic/difficulty/type/count; shortage blocks publish.
- Mandatory/fixed and random pool selection can coexist; question and choice shuffle optional.
- Timing freezes after publish; structure and points freeze after first Student start.

## Primary persistence
`assessments`, `assessment_sections`, `assessment_question_assignments`, `assessment_blueprints`, `assessment_blueprint_rules`, `assessment_question_pool`.

## TASK-090 review and academic PDF contract

- `NEVER`: released total score only; the result API returns an empty question list.
- `CORRECT_WRONG_ONLY`: question outcome and the student's selection; choice correctness is supplied only for selected choices. Unselected answer keys and explanations are withheld.
- `IMMEDIATE`: full review after the score is released, using the historical question/choice snapshot. Correct, incorrect and missed correct choices appear inline; detached A/B/C/D status controls are removed.
- Existing `AFTER_CLOSE` and `AFTER_ALL_ATTEMPTS` delay semantics remain supported. The backend's `answers_visible` decision controls disclosure; clients cannot infer permission from a selected policy alone.
- Individual and class PDFs use Unicode fonts and readable authorized answer text. Missing data remains explicit; UUIDs never substitute for academic names or candidate answers. Integer scores omit trailing zeros and fractions display at most two decimals. Signature location is `Thành phố Hồ Chí Minh`; the proctoring label is `Có giám sát nâng cao`.

## Implementation obligations
- Validate state and object authorization before mutation.
- Use service-owned transaction boundaries; do not rely on UI validation.
- Emit audit/notification/job side effects only according to documented event policy.
- Preserve historical evidence instead of rewriting past records.

## Failure semantics
State violations return a stable conflict/state error; authorization failures disclose no protected details; required-audit sensitive mutations roll back.

## Tests
Trace to `../testing/03_BUSINESS_RULE_TEST_MATRIX.md`, domain-specific integration tests and `../testing/11_END_TO_END_SCENARIOS.md`.
