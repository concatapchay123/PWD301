# Audit and Admin Actions

## Confirmed rules
- Important Admin/Instructor actions are append-only audit.
- Audit correction creates a new event; events are not edited/deleted.
- Required audit failure blocks sensitive/destructive action.
- Admin content override requires reason and Instructor notification.
- Extremely sensitive operations require password re-auth + phrase + reason.
- Admin cannot impersonate another User to act.

## Primary persistence
`audit_events`, `auth_sessions`, `notification_events`, `security_events`.

## Implementation obligations
- Validate state and object authorization before mutation.
- Use service-owned transaction boundaries; do not rely on UI validation.
- Emit audit/notification/job side effects only according to documented event policy.
- Preserve historical evidence instead of rewriting past records.

## Failure semantics
State violations return a stable conflict/state error; authorization failures disclose no protected details; required-audit sensitive mutations roll back.

## Tests
Trace to `../testing/03_BUSINESS_RULE_TEST_MATRIX.md`, domain-specific integration tests and `../testing/11_END_TO_END_SCENARIOS.md`.

## Audit event catalog
| Event | Actor | Reason required | Re-auth | Phrase | Blocking if audit unavailable |
|---|---|---:|---:|---:|---:|
| USER_SUSPEND | Admin | ✓ | ✓ | ✓ | ✓ |
| USER_ROLE_CHANGE | Admin | ✓ | policy | policy | ✓ |
| COURSE_REASSIGN | Admin | ✓ | policy | — | ✓ |
| COURSE_ADMIN_EDIT | Admin | ✓ | policy | — | ✓ |
| QUESTION_CORRECTION | Instructor/Admin | ✓ | Admin override policy | — | ✓ for required audit |
| ASSESSMENT_PUBLISH | Instructor/Admin | as policy | — | — | ✓ when audit required |
| ASSESSMENT_CANCEL | Instructor/Admin | ✓ | policy | policy if destructive | ✓ |
| MANUAL_GRADE_CHANGE | Instructor/Admin | ✓ | Admin override policy | — | ✓ |
| FILE_DELETE | Instructor/Admin | ✓ for historical/sensitive | policy | policy | ✓ when destructive |
| DATA_RESTORE | Admin | ✓ | ✓ | ✓ | ✓ |
| BACKUP_TRIGGER | Admin | reason for manual | policy | — | ✓ when designated sensitive |

`before/after` metadata is allow-listed and redacted; secrets/raw tokens/passwords are forbidden.
