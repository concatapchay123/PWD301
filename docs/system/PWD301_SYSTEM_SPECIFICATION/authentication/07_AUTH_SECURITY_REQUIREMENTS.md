# Authentication Security Requirements

- Generic login/reset responses resist account enumeration.
- Session fixation prevented by identifier rotation after authentication/privilege change.
- CSRF on cookie-authenticated writes.
- Rate-limit repeated auth failures; record security events without secrets.
- Verification/reset tokens are random, hashed at rest, purpose-bound, expiring and one-use.
- Never put JWT/access token/session secret into logs, URLs or audit payload.
- Suspension is fail-closed across web/API.
- Authorization always follows authentication.
