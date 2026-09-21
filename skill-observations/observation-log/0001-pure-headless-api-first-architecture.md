---
id: 1
title: "Pure Headless API-First Architecture vs Monolithic Template Drift"
status: open
type: internal
skill: [ponytail, superpowers]
proposes_skill: []
siblings_checked: "none"
area: "architecture/backend-frontend-boundary"
date: 2026-09-20
session_context: "Backfilled from 304 project conversation transcripts (2026-09-08 to 2026-09-20)"
parked_until: 
resolved: 
resolution: 
reference: 
---

**Issue:** During development, attempts to bundle Jinja2 templates, static CSS/JS, and Stitch preview screens directly into Flask led to UI state desynchronization, asset rot, CSRF session mismatches, and maintenance overhead. The user explicitly ordered the complete elimination of Jinja templates and legacy frontend mockups.

**Suggested improvement:** Enforce Pure Headless REST API architecture. Backend exclusively serves machine-readable JSON envelopes with standardized schemas. Decouple frontend completely to independent SPA/clients consuming REST/Session APIs.

**Principle:** A backend must not attempt to be a mediocre template server when API-first headless contracts provide clean separation of concerns, zero UI template lag, and independent testability.
