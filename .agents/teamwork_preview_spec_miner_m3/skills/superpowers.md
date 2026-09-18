---
name: superpowers
description: "Core skills library & software development methodology for coding agents: planning, TDD, debugging, code review, parallel execution, and delivery workflows."
---

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, ignore this skill.
</SUBAGENT-STOP>

<EXTREMELY-IMPORTANT>
If you think there is even a 1% chance a skill might apply to what you are doing, you ABSOLUTELY MUST invoke the skill.

IF A SKILL APPLIES TO YOUR TASK, YOU DO NOT HAVE A CHOICE. YOU MUST USE IT.

This is not negotiable. You cannot rationalize your way out of this.
</EXTREMELY-IMPORTANT>

## The Rule

**Invoke relevant or requested skills BEFORE any response or action** — including clarifying questions, exploring the codebase, or checking files. If it turns out wrong for the situation, you don't have to use it.

**Before entering plan mode:** if you haven't already brainstormed, invoke the brainstorming skill first.

Then announce "Using [skill] to [purpose]" and follow the skill exactly. If it has a checklist, create a todo per item.

## Skill Priority

When multiple skills apply, process skills come first — they set the approach, then implementation skills (frontend-design, etc.) carry it out. Brainstorming and systematic-debugging are Superpowers' most common process skills, but the rule holds for any of them.

- "Let's build X" → superpowers:brainstorming first, then implementation skills.
- "Fix this bug" → superpowers:systematic-debugging first, then domain skills.

## Red Flags

These thoughts mean STOP—you're rationalizing:

| Thought | Reality |
|---------|---------|
| "This is just a simple question" | Questions are tasks. Check for skills. |
| "I need more context first" | Skill check comes BEFORE clarifying questions. |
| "Let me explore the codebase first" | Skills tell you HOW to explore. Check first. |
| "I can check git/files quickly" | Files lack conversation context. Check for skills. |
| "Let me gather information first" | Skills tell you HOW to gather information. |
| "This doesn't need a formal skill" | If a skill exists, use it. |
| "I remember this skill" | Skills evolve. Read current version. |
| "This doesn't count as a task" | Action = task. Check for skills. |
| "The skill is overkill" | Simple things become complex. Use it. |
| "I'll just do this one thing first" | Check BEFORE doing anything. |
| "This feels productive" | Undisciplined action wastes time. Skills prevent this. |
| "I know what that means" | Knowing the concept ≠ using the skill. Invoke it. |

## Platform Adaptation

If your harness appears here, read its reference file for special instructions:

- Codex: `references/codex-tools.md`
- Pi: `references/pi-tools.md`
- Antigravity: `references/antigravity-tools.md`
- Hermes Agent: `references/hermes-tools.md`

## User Instructions

User instructions (CLAUDE.md, AGENTS.md, GEMINI.md, etc, direct requests) take precedence over skills, which in turn override default behavior. Only skip skill workflows or instructions when your human partner has explicitly told you to.

## Included Superpowers Skills

The Superpowers library installs 14 modular skills, each available independently:

1. **`brainstorming`** — Explore requirements, alternative designs, and edge cases before committing to a plan.
2. **`writing-plans`** — Create structured, bite-sized implementation plans with testable milestones.
3. **`executing-plans`** — Methodically execute approved plans with task checklists and progress tracking.
4. **`test-driven-development`** — The Iron Law of TDD: Write failing tests before any production code.
5. **`systematic-debugging`** — 4-phase root-cause investigation; no guessing or speculative fixes.
6. **`verification-before-completion`** — Confirm all requirements and tests pass with concrete evidence before declaring done.
7. **`dispatching-parallel-agents`** — Run independent tasks concurrently using subagents.
8. **`subagent-driven-development`** — Supervised worker agents with implementer, reviewer, and spec validation roles.
9. **`requesting-code-review`** — Package and request thorough code review before merging changes.
10. **`receiving-code-review`** — Process code review feedback systematically and objectively.
11. **`using-git-worktrees`** — Maintain pristine workspace isolation with git worktrees.
12. **`finishing-a-development-branch`** — Complete, verify, polish, and merge a development branch.
13. **`writing-skills`** — Author new robust agent skills following Anthropic & Superpowers best practices.
14. **`using-superpowers`** — Enforce proactive skill discovery and invocation discipline.
