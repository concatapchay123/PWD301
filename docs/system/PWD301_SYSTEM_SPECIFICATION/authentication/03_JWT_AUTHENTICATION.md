# JWT Authentication

REST API JWTs are short-lived access credentials associated with a persisted grant/version strategy. Claims include opaque subject/public user ID, token identifier, issued/expiry times and authorization version; permissions are re-evaluated server-side. Suspended/deactivated User or stale auth version rejects immediately.

Refresh-token use is a **DERIVED ARCHITECTURE DESIGN** only if the implementation needs long-lived API sessions; refresh credentials must be revocable and stored/handled more strongly than access tokens. Website AJAX does not use this mechanism.
