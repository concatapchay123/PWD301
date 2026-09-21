---
id: 5
title: "AI Assistant Zero-Trust Guardrails, Prompt Injection Defense & Scope Bounding"
status: open
type: internal
skill: [superpowers, open-code-review]
proposes_skill: []
siblings_checked: "none"
area: "ai-assistance/security"
date: 2026-09-20
session_context: "Backfilled from 304 project conversation transcripts (2026-09-08 to 2026-09-20)"
parked_until: 
resolved: 
resolution: 
reference: 
---

**Issue:** The AI chatbot ('Bạch tuộc AI') previously answered arbitrary out-of-scope questions (e.g. general HTML coding on the homepage), hallucinated nonexistent courses (e.g. claiming to cite 'giáo trình PWD301'), and was vulnerable to prompt injection extracting internal account details and architectural credentials.

**Suggested improvement:** Implement hybrid dual-layer defense: a deterministic regex/keyword gatekeeper filtering out-of-scope and adversarial prompts, paired with strict system prompt boundaries enforcing the 'Bạch tuộc AI' persona and forbidding disclosure of internal system credentials or account information.

**Principle:** Autonomous LLM endpoints embedded in domain software must be bounded by deterministic input sanitization and zero-trust security layers; models must never be trusted with raw credential context.
