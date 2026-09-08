# ARTIFACT MANIFEST

Final inventory for the PWD301 Database Architecture completion pass. No artifact remains in `NEEDS FIX` state.

## Inventory summary

- Files listed in this manifest: **39**.
- Markdown files (including this manifest and `sql/README.md`): **27**.
- SQL files: **12**.
- Subdirectories: `sql/` only.
- Duplicate/stale package files: **none detected**.

## Files

| File | Type | Purpose | Status | Cross-reference |
|---|---|---|---|---|
| `ARTIFACT_MANIFEST.md` | `Markdown` | Final package inventory/status/cross-reference. | **GENERATED** | README.md; FINAL_DATABASE_REVIEW.md. |
| `00_DECISION_INVENTORY_AND_CONSISTENCY.md` | `Markdown` | Decision inventory, superseded rules and consistency reconciliation. | **REVIEWED** | README.md; FINAL_DATABASE_REVIEW.md. |
| `01_ARCHITECTURE_OVERVIEW.md` | `Markdown` | Database conventions and overall architecture. | **REVIEWED** | README.md; FINAL_DATABASE_REVIEW.md. |
| `02_DOMAIN_MODEL.md` | `Markdown` | Domain boundaries, source-of-truth and table map. | **REVIEWED** | README.md; FINAL_DATABASE_REVIEW.md. |
| `03_ERD.md` | `Markdown` | Ten Mermaid ERD views covering the full schema. | **UPDATED** | README.md; FINAL_DATABASE_REVIEW.md. |
| `04_DATA_DICTIONARY_IDENTITY.md` | `Markdown` | Identity/authentication Data Dictionary. | **REVIEWED** | README.md; FINAL_DATABASE_REVIEW.md. |
| `05_DATA_DICTIONARY_COURSE.md` | `Markdown` | Course/lesson/enrollment Data Dictionary. | **UPDATED** | README.md; FINAL_DATABASE_REVIEW.md. |
| `06_DATA_DICTIONARY_QUESTION_BANK.md` | `Markdown` | Question Bank/versioning Data Dictionary. | **UPDATED** | README.md; FINAL_DATABASE_REVIEW.md. |
| `07_DATA_DICTIONARY_ASSESSMENT.md` | `Markdown` | Assessment/configuration Data Dictionary. | **UPDATED** | README.md; FINAL_DATABASE_REVIEW.md. |
| `08_DATA_DICTIONARY_ATTEMPT_REGRADING.md` | `Markdown` | Attempt/grading/regrade Data Dictionary. | **UPDATED** | README.md; FINAL_DATABASE_REVIEW.md. |
| `09_DATA_DICTIONARY_FILES_IMPORT.md` | `Markdown` | File security/import Data Dictionary. | **UPDATED** | README.md; FINAL_DATABASE_REVIEW.md. |
| `10_DATA_DICTIONARY_AI_RAG.md` | `Markdown` | AI/RAG Data Dictionary. | **UPDATED** | README.md; FINAL_DATABASE_REVIEW.md. |
| `11_DATA_DICTIONARY_NOTIFICATION_AUDIT_OPERATIONS.md` | `Markdown` | Notification/audit/operations Data Dictionary. | **REVIEWED** | README.md; FINAL_DATABASE_REVIEW.md. |
| `12_STATE_MACHINES.md` | `Markdown` | Lifecycle/state-machine definitions. | **REVIEWED** | README.md; FINAL_DATABASE_REVIEW.md. |
| `13_CONSTRAINTS_AND_INVARIANTS.md` | `Markdown` | Invariant enforcement ownership. | **REVIEWED** | README.md; FINAL_DATABASE_REVIEW.md. |
| `14_INDEX_AND_PERFORMANCE_STRATEGY.md` | `Markdown` | Indexing, pagination and performance strategy. | **REVIEWED** | README.md; FINAL_DATABASE_REVIEW.md. |
| `15_RETENTION_DELETE_RESTORE_MATRIX.md` | `Markdown` | Retention/delete/restore/anonymization matrix. | **REVIEWED** | README.md; FINAL_DATABASE_REVIEW.md. |
| `16_CONCURRENCY_AND_TRANSACTIONS.md` | `Markdown` | Transactions, leases, idempotency and race handling. | **UPDATED** | README.md; FINAL_DATABASE_REVIEW.md. |
| `17_SECURITY_DATABASE_REVIEW.md` | `Markdown` | Database security threat review. | **UPDATED** | README.md; FINAL_DATABASE_REVIEW.md. |
| `18_BUSINESS_RULE_DATABASE_TRACEABILITY.md` | `Markdown` | Rule-to-DB/service/worker/audit/test traceability. | **REVIEWED** | README.md; FINAL_DATABASE_REVIEW.md. |
| `19_DATABASE_INTEGRITY_TEST_PLAN.md` | `Markdown` | Constraint, lifecycle, concurrency and migration tests. | **UPDATED** | README.md; FINAL_DATABASE_REVIEW.md. |
| `20_MIGRATION_STRATEGY.md` | `Markdown` | Alembic/SQL Server migration and seed strategy. | **UPDATED** | README.md; FINAL_DATABASE_REVIEW.md. |
| `21_ASSUMPTIONS_AND_DECISIONS.md` | `Markdown` | Derived DB ADRs and assumptions. | **REVIEWED** | README.md; FINAL_DATABASE_REVIEW.md. |
| `FINAL_DATABASE_REVIEW.md` | `Markdown` | Final reconciliation and quality-gate evidence. | **UPDATED** | ARTIFACT_MANIFEST.md; OPEN_ISSUES.md; all QA targets. |
| `OPEN_ISSUES.md` | `Markdown` | Non-blocking implementation/deployment notes. | **UPDATED** | README.md; FINAL_DATABASE_REVIEW.md. |
| `README.md` | `Markdown` | Package entry point, navigation, key invariants and validation status. | **UPDATED** | All package documents and SQL scripts. |
| `sql/001_identity.sql` | `SQL` | SQL Server reference DDL: 001 identity. | **REVIEWED** | README SQL manifest; sql/README.md; related Data Dictionary. |
| `sql/002_course_learning.sql` | `SQL` | SQL Server reference DDL: 002 course learning. | **UPDATED** | README SQL manifest; sql/README.md; related Data Dictionary. |
| `sql/003_question_bank.sql` | `SQL` | SQL Server reference DDL: 003 question bank. | **UPDATED** | README SQL manifest; sql/README.md; related Data Dictionary. |
| `sql/004_assessment.sql` | `SQL` | SQL Server reference DDL: 004 assessment. | **UPDATED** | README SQL manifest; sql/README.md; related Data Dictionary. |
| `sql/005_attempt_regrade.sql` | `SQL` | SQL Server reference DDL: 005 attempt regrade. | **UPDATED** | README SQL manifest; sql/README.md; related Data Dictionary. |
| `sql/006_files_import.sql` | `SQL` | SQL Server reference DDL: 006 files import. | **UPDATED** | README SQL manifest; sql/README.md; related Data Dictionary. |
| `sql/007_ai_rag.sql` | `SQL` | SQL Server reference DDL: 007 ai rag. | **UPDATED** | README SQL manifest; sql/README.md; related Data Dictionary. |
| `sql/008_notification_audit.sql` | `SQL` | SQL Server reference DDL: 008 notification audit. | **REVIEWED** | README SQL manifest; sql/README.md; related Data Dictionary. |
| `sql/009_operations.sql` | `SQL` | SQL Server reference DDL: 009 operations. | **REVIEWED** | README SQL manifest; sql/README.md; related Data Dictionary. |
| `sql/010_cross_domain_constraints.sql` | `SQL` | SQL Server reference DDL: 010 cross domain constraints. | **REVIEWED** | README SQL manifest; sql/README.md; related Data Dictionary. |
| `sql/011_indexes.sql` | `SQL` | SQL Server reference DDL: 011 indexes. | **REVIEWED** | README SQL manifest; sql/README.md; related Data Dictionary. |
| `sql/012_critical_invariant_triggers.sql` | `SQL` | SQL Server reference DDL: 012 critical invariant triggers. | **UPDATED** | README SQL manifest; sql/README.md; related Data Dictionary. |
| `sql/README.md` | `Markdown` | Reference DDL execution order and verification notes. | **REVIEWED** | All package documents and SQL scripts. |

## Status definitions

- **GENERATED** — created in the completion pass.
- **UPDATED** — existing artifact repaired/updated during QA.
- **REVIEWED** — existing artifact reviewed and retained without substantive change.
- **COMPLETE** — reserved for artifacts whose content was complete and required no further action.

> Final validation/package status is recorded in `FINAL_DATABASE_REVIEW.md` and `README.md`.
