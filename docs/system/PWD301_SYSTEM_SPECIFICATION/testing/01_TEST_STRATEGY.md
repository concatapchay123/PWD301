# Test Strategy

Use layered testing: pure unit tests for algorithms/policies; model/constraint tests; service+SQL Server integration transactions; API auth/validation/error tests; concurrency races; security negative tests; worker retry/idempotency; and end-to-end actor workflows. Critical business rules must have at least one automated test and historical/concurrency rules need integration tests, not mocks only.
