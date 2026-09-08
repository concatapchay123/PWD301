# PWD301 Vibecode Bootstrap Supplement

This file documents the **supplemental repository harness** added on top of `PWD301_CLEAN_STRUCTURE.zip`.

It intentionally does **not** replace or regenerate:

- root `README.md`;
- `docs/system/PWD301_SYSTEM_SPECIFICATION/`;
- `docs/database/PWD301_DATABASE_ARCHITECTURE/`.

Those remain the canonical knowledge/specification artifacts.

## Package summary

- Supplement files: **95**
- Existing clean-structure files overwritten: **0**
- Canonical database copies added: **0**

## What this supplement adds

- coding-agent operating rules (`AGENTS.md`);
- repository metadata/configuration;
- Python dependency/tooling manifests;
- docs routing/index layer;
- lightweight ADR/navigation files;
- feature routing files;
- task/backlog workflow;
- reusable coding-agent prompt templates;
- setup/test/lint/verify scripts;
- source/test/migration/instance skeleton;
- CI baseline;
- repository contract tests preventing accidental reintroduction of duplicate DB snapshots.

## First coding task

After merging this supplement with the clean structure, begin with `tasks/CURRENT.md` (`TASK-001 — Project Foundation & Flask Bootstrap`). Do not skip directly to AI/UI feature work.

## Canonical paths

- System: `docs/system/PWD301_SYSTEM_SPECIFICATION/`
- Database: `docs/database/PWD301_DATABASE_ARCHITECTURE/`
- Agent rules: `AGENTS.md`
- Current task: `tasks/CURRENT.md`
- Aggregate verification: `scripts/verify.ps1` or `scripts/verify.sh`

## Intentionally not generated

`LICENSE` is not generated because choosing a software license is a legal/project-owner decision, not a vibecoding prerequisite.

JWT/Gemini/background-job implementation libraries are intentionally not preselected where the project specification did not lock the technology.
