# Task Execution System

`tasks/` prevents coding agents from treating the whole project as one uncontrolled prompt.

- `BACKLOG.md` — ordered work not yet started.
- `CURRENT.md` — **the only task an agent may actively implement** unless the user explicitly changes scope.
- `DONE.md` — completed tasks and verification summary.
- `templates/` — required task formats.

## Status flow

`BACKLOG -> READY -> IN_PROGRESS -> VERIFYING -> DONE`

A task may be `BLOCKED` with an explicit blocker. Do not mark `DONE` with failing required checks.

## Rule

Finishing one task does not authorize starting the next task automatically.
