# Refactor Without Behavior Change

Read `AGENTS.md`. Refactoring must preserve externally observable behavior and all documented invariants.

- Inspect usages/tests before editing.
- Prefer deletion/simplification over new abstraction.
- Do not combine a broad feature change with refactoring unless required.
- Do not change schema/API/business behavior merely to make code prettier.
- Run regression tests, lint and type checks.
- Provide explicit `REMOVE NOW / SIMPLIFY NOW / KEEP / PONYTAIL` findings.
