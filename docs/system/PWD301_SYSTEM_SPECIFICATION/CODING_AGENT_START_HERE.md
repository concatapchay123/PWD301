# Coding Agent — Start Here

This package is the authoritative implementation specification.

## Before coding
1. Read `README.md`.
2. Read `00_MASTER_SYSTEM_SPEC.md`.
3. Read `business/01_BUSINESS_RULE_CATALOG.md`.
4. Read `implementation/06_NON_NEGOTIABLE_INVARIANTS.md`.
5. Read relevant feature/workflow/algorithm files.
6. Read `database/README.md` + relevant Data Dictionary/invariants/SQL.
7. Read relevant API specification.
8. Read acceptance criteria/test plan/traceability.
9. Inspect the existing repository before adding code.

## Mandatory working rules
Reuse existing code/dependencies; smallest correct change; do not invent business behavior; do not silently change database invariants; preserve security/audit/accessibility/validation; keep migrations reversible/safe; run relevant tests; report checks not run.

## Ambiguity protocol
Search this documentation → repository → traceability. If still unresolved, distinguish a tunable implementation default from a business decision. Do not ask again about a rule already documented.
