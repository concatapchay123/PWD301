# User Account Lifecycle

## Confirmed rules
- Registration creates one email-unique User; no username login.
- Email change activates only after new-email verification.
- Role upgrade does not replace User or learning history.
- Suspension immediately blocks session/JWT via account/auth version and revocation.
- Deletion starts with deactivate; PII may later anonymize while historical references remain.

## Primary persistence
`users`, `roles`, `user_roles`, `auth_sessions`, `jwt_token_grants`, `user_security_tokens`, `audit_events`, `notifications`.

## Implementation obligations
- Validate state and object authorization before mutation.
- Use service-owned transaction boundaries; do not rely on UI validation.
- Emit audit/notification/job side effects only according to documented event policy.
- Preserve historical evidence instead of rewriting past records.

## Failure semantics
State violations return a stable conflict/state error; authorization failures disclose no protected details; required-audit sensitive mutations roll back.

## Tests
Trace to `../testing/03_BUSINESS_RULE_TEST_MATRIX.md`, domain-specific integration tests and `../testing/11_END_TO_END_SCENARIOS.md`.
