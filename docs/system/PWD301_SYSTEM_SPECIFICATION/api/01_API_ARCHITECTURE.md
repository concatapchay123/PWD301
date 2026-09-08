# API Architecture

REST API is JSON, versioned by route prefix when implementation adopts versioning, and authenticated with JWT. Same-origin browser AJAX may use parallel JSON endpoints with Flask session + CSRF; it must not persist JWT in localStorage. Every endpoint uses object-level authorization, allow-listed input DTOs, standard errors, pagination for large lists and correlation IDs.

## Conventions
- Public IDs are UUID/GUID strings; internal BIGINT IDs remain server-internal.
- Timestamps are ISO-8601 UTC.
- List responses: `items`, `page`/cursor, `page_size`, `total` when affordable, filters/sort echoed when useful.
- Write responses include current `row_version`/ETag-equivalent where optimistic concurrency applies.
- Sensitive fields (password hashes, token material, correct-answer flags before visibility policy, storage keys) never serialize.
