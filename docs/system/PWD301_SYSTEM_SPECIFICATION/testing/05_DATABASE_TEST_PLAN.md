# Database Test Plan

Use the validated `database/DATABASE_INTEGRITY_TEST_PLAN.md` as primary DB suite. Run migrations from zero, downgrade/upgrade where safe, constraint/FK/index/trigger tests, unique active revision/version tests, no historical cascade tests and seed idempotency. SQL Server—not SQLite—is required for final integration because ROWVERSION/filtered indexes/triggers are engine-specific.
