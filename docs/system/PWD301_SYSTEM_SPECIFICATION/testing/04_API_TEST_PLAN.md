# API Test Plan

For every endpoint: success, missing/invalid input, unauthenticated, wrong role, wrong object ownership, not-found/enumeration policy, lifecycle conflict, serialization safe fields, pagination/filter bounds and correlation ID. Mutation tests include stale ROWVERSION, duplicate/retry behavior and side-effect outbox/audit expectations. Attempt endpoints add lease/deadline/offline sequence races.
