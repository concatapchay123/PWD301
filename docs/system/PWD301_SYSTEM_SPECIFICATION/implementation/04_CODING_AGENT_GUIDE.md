# Coding Agent Guide

Before changing code: search repository for existing implementation/dependencies; read the relevant business rule, invariant, workflow, algorithm, DB contract, API and tests. Reuse existing code first. Implement the smallest correct reversible change. Do not invent business rules, bypass audit/security, weaken validation, introduce JWT localStorage, replace SQL Server, or add distributed infrastructure without explicit need. Run targeted tests plus lint/type/build/migration checks available; report every unrun check.

When ambiguity remains after docs + code + traceability, classify it as confirmed/derived/configurable/assumption before choosing. Only genuine business-behavior ambiguity needs User decision.
