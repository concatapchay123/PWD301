---
id: 2
title: "Single Active Editing Lease & Multi-Tab Takeover in High-Stakes Assessments"
status: open
type: internal
skill: [superpowers, open-code-review]
proposes_skill: []
siblings_checked: "none"
area: "assessment-engine/concurrency"
date: 2026-09-20
session_context: "Backfilled from 304 project conversation transcripts (2026-09-08 to 2026-09-20)"
parked_until: 
resolved: 
resolution: 
reference: 
---

**Issue:** High-stakes exam attempts are vulnerable to multi-tab desynchronization, duplicate submission races, and state corruption when students open assessments across multiple browser tabs or devices.

**Suggested improvement:** Implement Algorithm 07: Single Active Editing Lease with heartbeat renewal and explicit takeover semantics. A new lease invalidates previous tabs safely, autosave commits are ordered by sequence numbers, and submit actions are strictly idempotent.

**Principle:** Stateful student sessions in high-stakes workflows require server-authoritative lease ownership; client-side optimistic concurrency alone cannot prevent double-submission races.
