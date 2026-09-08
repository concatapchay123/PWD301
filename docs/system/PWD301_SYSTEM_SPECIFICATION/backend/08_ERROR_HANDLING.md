# Error Handling

Controllers map domain exceptions to the API/HTML error model. Validation=400/422, unauthenticated=401, unauthorized=403/404 policy, missing=404, stale/state/lease/idempotency conflict=409, expired deadline=409/410 domain choice, rate limited=429, external dependency=503, unexpected=500 with correlation ID. Never leak stack traces, SQL, secrets or protected object details.
