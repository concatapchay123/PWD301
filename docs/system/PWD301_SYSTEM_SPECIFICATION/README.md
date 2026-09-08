# PWD301 System Specification

This directory is the **development Single Source of Truth** for PWD301 Topic 9 — Online Course Management Platform. It consolidates confirmed business rules, authentication/authorization, UI flows, service transactions, APIs, algorithms, database architecture, security, operations and test/acceptance requirements so coding agents do not need to reinvent business behavior.

## Technology baseline
- Python 3.11+ / Flask / Flask-SQLAlchemy / Flask-WTF / Flask-Login / Flask-Migrate(Alembic).
- Microsoft SQL Server.
- Jinja2 + Bootstrap 5 + AJAX/Fetch.
- REST endpoints authenticated with JWT; browser AJAX uses the Flask session + CSRF, not localStorage JWT.
- Docker deployment; private file storage; background workers for heavyweight work; Gemini only through backend.

## Recommended reading order
1. [CODING_AGENT_START_HERE.md](CODING_AGENT_START_HERE.md)
2. [00_MASTER_SYSTEM_SPEC.md](00_MASTER_SYSTEM_SPEC.md)
3. [business/01_BUSINESS_RULE_CATALOG.md](business/01_BUSINESS_RULE_CATALOG.md)
4. [implementation/06_NON_NEGOTIABLE_INVARIANTS.md](implementation/06_NON_NEGOTIABLE_INVARIANTS.md)
5. Relevant business/workflow/algorithm document
6. [database/README.md](database/README.md) and database contract
7. Relevant API document
8. [testing/02_ACCEPTANCE_CRITERIA.md](testing/02_ACCEPTANCE_CRITERIA.md)
9. Relevant test plan/traceability

## Major domain map
Identity/Auth → Course/Learning → Question Bank → Assessment → Attempt/Grading/Regrade → Files/Import → AI/RAG → Notification/Audit → Operations.

## Key invariants
1. Object-level authorization is mandatory; role alone is insufficient.
2. Suspended accounts cannot keep session/JWT access.
3. One active logical enrollment per Student/Course; prerequisites and capacity are transaction-safe.
4. Exposed/graded QuestionRevision history is preserved.
5. Attempt snapshot is historical evidence and is never rewritten by later corrections.
6. Server time is authoritative; closing time is a hard deadline.
7. Only one active editing lease per Attempt; stale owner may be taken over without a new Attempt.
8. Submit and background retries are idempotent.
9. Assessment timing freezes after publish; structure/points freeze after first start.
10. File activation is fail-closed; official video limit is **< 1 GB**.
11. RAG retrieval is authorization-filtered and excludes archived/deleted/draft content.
12. Important audit records are append-only; required-audit sensitive mutations fail if audit cannot persist.

## Database reuse
The validated 71-table database architecture is maintained once as the canonical source at [../../database/PWD301_DATABASE_ARCHITECTURE/README.md](../../database/PWD301_DATABASE_ARCHITECTURE/README.md). System-level database wrappers remain under [database/](database/), but duplicated SQL/reference snapshots were intentionally removed from this live repository to prevent source-of-truth drift.

## Classification labels
- **CONFIRMED BUSINESS RULE**: locked by Plan Mode/source of truth.
- **DERIVED ARCHITECTURE DESIGN**: implementation design chosen to realize rules.
- **CONFIGURABLE DEFAULT**: safe default that may be tuned without changing business semantics.
- **ASSUMPTION**: necessary gap; must not be misreported as user-confirmed.

## Validation status
See [FINAL_SYSTEM_REVIEW.md](FINAL_SYSTEM_REVIEW.md) and [ARTIFACT_MANIFEST.md](ARTIFACT_MANIFEST.md). Runtime SQL Server execution and Mermaid rendering are reported truthfully as executed or not executed; static validation is not represented as runtime validation.
