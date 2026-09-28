# PWD301 workflow and interface repair implementation plan

**Goal:** Implement and verify every capability in the [workflow specification](../specs/2026-09-27-pwd301-workflow-redesign.md).

**Architecture:** Keep the current Flask services and SPA routes. Put policy validation in services, expose only public UUIDs, and keep page state in the existing client modules. Extend the schema with additive migrations and backfill existing lessons without changing their IDs.

**Tech stack:** Flask, SQLAlchemy/Alembic, SQL Server, vanilla JavaScript, Tailwind utility classes, pytest, Node test runner.

## Work order

- [x] **Exam submission:** Reproduce the retry and pending-save failure paths; add regression tests; preserve one submission key per attempt; show actionable save failures and treat a committed submission as submitted.
- [x] **Monitoring:** Add schema/service/API and tests for per-assessment policy and per-attempt observations. Connect browser event capture and instructor review. Remove automatic sanction and unsupported screenshot/gesture claims.
- [x] **Exam authoring:** Test direct route access and forward step selection; enforce progression at the router; simplify the interactive editor and use the shared role topbar.
- [x] **Waiting room:** Replace the verbose room with a dedicated focused route and test open, upcoming, active, and exhausted states.
- [x] **Review and notifications:** Map action copy to its resource, add the admin course detail route, ensure completed review items leave pending lists, expose rejection reasons, and rebalance affected tables. Test permission and queue state.
- [x] **Course image:** Reuse FileAsset scan/authorization for thumbnail upload and delivery. Add a CSS fallback and test unsafe/foreign assets are rejected.
- [x] **Lesson parent:** Add the parent model and migration with safe backfill; implement caps and course ownership checks; extend APIs and student/instructor views; integrate the existing in-progress studio changes. Test legacy progress preservation and cap boundaries.
- [x] **Shared UI:** Expand avatars, simplify copy, remove the academic-safety/audit navigation entry, unify role topbars, and redesign dark tokens/dialog layering. Inspect desktop/mobile light/dark renders.
- [x] **Final review:** Run focused and aggregate checks, migration checks where available, Impeccable detector, line-level OCR review, and report results and remaining limits using the repository report format.

## Global checks

Use `rtk pytest ... -q` for Python suites and `node --test tests/frontend/*.test.js` for JavaScript suites. Run `./scripts/verify.ps1` once after the focused suites. Preserve the two pre-existing modified files and all current behavioral/security invariants. Do not claim unrun SQL Server or live browser checks passed.
