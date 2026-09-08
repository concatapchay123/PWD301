# AJAX Interaction Rules

Same-origin AJAX uses Flask session credentials and CSRF header/token. Search fields debounce. Mutations use JSON error model and represent 409 conflict/lease/stale version explicitly. Answer saves carry stable client change ID + monotonic sequence and current lease token. Retry only operations documented as idempotent. Never store JWT in localStorage for website flows.
