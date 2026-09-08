# Open Issues

No blocking business-rule contradictions remain.

| ID | Item | Current safe interpretation | Impact | Blocking? |
|---|---|---|---|---|
| OI-001 | Exact Lesson minimum time/viewed-most threshold | Configurable server-side values; completion requires both signals | Tuning/UX | No |
| OI-002 | Attempt lease/heartbeat durations | Configurable bounded lease validated by network/concurrency tests | Reliability tuning | No |
| OI-003 | Worker/queue technology | Keep persisted job semantics; choose simplest stack compatible with repo | Implementation | No |
| OI-004 | Exact password hash cost/session/JWT TTL/rate limits | Security configuration using current library guidance and environment | Deployment tuning | No |
| OI-005 | Storage warning/quota default numbers | Configurable; hard limits from business/file policy remain | Operations tuning | No |
| OI-006 | Mermaid runtime rendering | Static QA can validate source; render in CI/editor when renderer available | Documentation tooling | No |
| OI-007 | SQL Server runtime DDL execution | Must run migrations/integration suite on actual dev/test SQL Server before deployment | Environment validation | No for specification package |
