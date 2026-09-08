# Session and Token Revocation

Account suspension transaction: set User suspended → increment auth version/revocation epoch → revoke active `auth_sessions` → revoke active `jwt_token_grants` → write required audit/security event → enqueue mandatory notification. Middleware checks current account status/version so a missed per-token update cannot preserve access.
