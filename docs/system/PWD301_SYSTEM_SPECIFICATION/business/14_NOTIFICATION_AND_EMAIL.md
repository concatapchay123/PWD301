# Notification and Email

## Confirmed rules
- In-app notifications have read/unread.
- Important events can email; security categories cannot be disabled.
- Email failure never rolls back primary business action; outbox retry is idempotent.
- Assessment reminders, role/suspension and score-change notifications are supported.
- Low-value old notifications may clean up; audit facts remain separate.

## Primary persistence
`notification_events`, `notifications`, `notification_preferences`, `email_deliveries`.

## Implementation obligations
- Validate state and object authorization before mutation.
- Use service-owned transaction boundaries; do not rely on UI validation.
- Emit audit/notification/job side effects only according to documented event policy.
- Preserve historical evidence instead of rewriting past records.

## Failure semantics
State violations return a stable conflict/state error; authorization failures disclose no protected details; required-audit sensitive mutations roll back.

## Tests
Trace to `../testing/03_BUSINESS_RULE_TEST_MATRIX.md`, domain-specific integration tests and `../testing/11_END_TO_END_SCENARIOS.md`.

## Notification event catalog
| Event | Recipient | In-app | Email | Mandatory? | Dedupe boundary | Retention |
|---|---|---:|---:|---|---|---|
| ACCOUNT_SUSPENDED | affected User | ✓ | ✓ | Security mandatory | event+recipient | ordinary UI cleanup; audit/security durable |
| ROLE_CHANGED | affected User | ✓ | ✓ | important | event+recipient | normal notification retention |
| ASSESSMENT_REMINDER | eligible Student | ✓ | configurable | optional category | assessment+student+reminder window | cleanup after usefulness |
| ASSESSMENT_GRADED | Student | ✓ | configurable | optional | result+recipient | normal |
| SCORE_CHANGED_AFTER_REGRADE | Student | ✓ | important | important | result history/version+recipient | normal; score history durable |
| COURSE_ADMIN_EDITED | Instructor owner | ✓ | important | important | audit/change+recipient | normal; audit durable |
| FILE_REJECTED | uploader/Instructor | ✓ | configurable | operational | file revision+recipient | normal |
| SYSTEM_SECURITY_ALERT | Admin | ✓ | configured mandatory path | security | alert+window | operations policy |

Retries use persisted `email_deliveries`; failure does not rollback the originating business action.
