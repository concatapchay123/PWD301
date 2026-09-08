# Implementation Checklist

- [ ] Inspect/reuse existing code and dependencies.
- [ ] Identify business Rule IDs and acceptance criteria.
- [ ] Update model/migration without weakening DB invariants.
- [ ] Implement object authorization + validation.
- [ ] Implement transaction and rowversion/lease/idempotency requirements.
- [ ] Add audit/notification/job outbox as required.
- [ ] Add safe serialization/error handling/log redaction.
- [ ] Implement UI states/accessibility if visible.
- [ ] Add unit/integration/DB/security/concurrency tests.
- [ ] Run relevant test/lint/type/migration/build checks.
- [ ] Update traceability/docs.
- [ ] Report unrun checks/remaining risk.
