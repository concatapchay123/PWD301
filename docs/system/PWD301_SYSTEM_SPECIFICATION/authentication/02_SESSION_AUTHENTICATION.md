# Session Authentication

## Login
Normalize email, load User, generic failure for unknown/wrong password, verify active status, verify password hash, rotate session identifier, create/update `auth_sessions`, then establish Flask-Login identity.

## Logout/revocation
Logout revokes current session. Suspension/password/security revocation can revoke all active sessions and increment auth version in one transaction.

## Cookie/CSRF
Use Secure + HttpOnly + appropriate SameSite, session expiration/idle policy, CSRF token for forms and JSON AJAX. Never accept user/role IDs from the client as authority.
