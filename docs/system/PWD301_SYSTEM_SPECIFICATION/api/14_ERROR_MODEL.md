# API Error Model

```json
{
  "error": {
    "code": "LEASE_CONFLICT",
    "message": "This attempt is being edited in another active tab.",
    "field_errors": {},
    "correlation_id": "..."
  }
}
```

| Category | Typical HTTP | Notes |
|---|---:|---|
| VALIDATION_ERROR | 400/422 | field-safe details |
| AUTHENTICATION_REQUIRED | 401 | no secret detail |
| AUTHORIZATION_DENIED | 403/404 | enumeration-safe policy |
| RESOURCE_NOT_FOUND | 404 | opaque resource lookup |
| CONFLICT / STATE_VIOLATION | 409 | stale version, locked config |
| LEASE_CONFLICT | 409 | second active tab |
| DEADLINE_EXPIRED | 409/410 | server deadline wins |
| IDEMPOTENCY_CONFLICT | 409 | same key with different payload |
| RATE_LIMITED | 429 | retry metadata if safe |
| EXTERNAL_SERVICE_UNAVAILABLE | 503 | Gemini/scanner dependency policy |
| FILE_REJECTED | 400/422 | safe reason category |
| INTERNAL_ERROR | 500 | correlation ID only |
