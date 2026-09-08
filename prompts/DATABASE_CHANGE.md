# Database Change

Before editing models/migrations, read:

- `AGENTS.md`;
- canonical `docs/database/PWD301_DATABASE_ARCHITECTURE/` documents and relevant SQL;
- related business rules and transaction/concurrency documentation.

Requirements:

- SQL Server compatible;
- do not create a second schema source of truth;
- preserve historical data and documented delete semantics;
- use migrations/backfills safely;
- add constraint/model/service/migration tests as applicable;
- validate upgrade and, where reasonable, downgrade behavior;
- document any intentional divergence from reference DDL with rationale.
