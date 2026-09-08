# Database Contract

This directory contains the **system-level view** of the database contract. It does not own a second schema copy.

## Canonical database source

The single editable/canonical Database Architecture for the repository is:

- [PWD301 Database Architecture](../../../database/PWD301_DATABASE_ARCHITECTURE/README.md)
- [Canonical SQL Server reference DDL](../../../database/PWD301_DATABASE_ARCHITECTURE/sql/README.md)
- [Canonical ERD](../../../database/PWD301_DATABASE_ARCHITECTURE/03_ERD.md)

The previous embedded `reference_architecture/` snapshot and duplicate `sql/` directory were intentionally removed when the documentation was integrated into the live repository. This prevents coding agents from editing one copy while leaving another copy stale.

## System-level database documents retained here

- [ERD.md](ERD.md) — system-facing ERD view.
- [DATA_DICTIONARY.md](DATA_DICTIONARY.md) — consolidated system-facing dictionary.
- [DATABASE_CONVENTIONS.md](DATABASE_CONVENTIONS.md) — conventions referenced by system specs.
- [DATABASE_INVARIANTS.md](DATABASE_INVARIANTS.md) — important database invariants.
- [INDEX_STRATEGY.md](INDEX_STRATEGY.md) — indexing/performance expectations.
- [RETENTION_MATRIX.md](RETENTION_MATRIX.md) — retention mapping.
- [MIGRATION_STRATEGY.md](MIGRATION_STRATEGY.md) — migration/seed expectations.
- [DATABASE_INTEGRITY_TEST_PLAN.md](DATABASE_INTEGRITY_TEST_PLAN.md) — database integrity testing expectations.

## Baseline

The validated canonical schema has **71 tables** and targets Microsoft SQL Server. It uses BIGINT internal primary keys, public UNIQUEIDENTIFIER values where defined, UTC DATETIME2(3), and ROWVERSION for selected optimistic-concurrency boundaries.

**Rule for coding agents:** schema/DDL changes belong in `docs/database/PWD301_DATABASE_ARCHITECTURE/` and in real application migrations. Do not create another schema copy under this System Specification directory.
