---
id: 3
title: "Fail-Closed Antivirus Quarantine & Safe Media Streaming"
status: open
type: internal
skill: [open-code-review, superpowers]
proposes_skill: []
siblings_checked: "none"
area: "security/file-storage"
date: 2026-09-20
session_context: "Backfilled from 304 project conversation transcripts (2026-09-08 to 2026-09-20)"
parked_until: 
resolved: 
resolution: 
reference: 
---

**Issue:** File assets previously returned 'CLEAN' by default when ClamAV was unconfigured or when scan status was pending, violating the fail-closed invariant and allowing unverified uploads to be accessed by students.

**Suggested improvement:** Enforce strict fail-closed file security: unscanned or quarantined files remain strictly inaccessible (HTTP 403 / 423) to students until explicitly marked CLEAN by the background scanner. Reject files exceeding documented thresholds (e.g. video > 1 GB).

**Principle:** Security gates must fail closed: uninspected data is untrusted data and must never be released to end-users upon scanner absence, delay, or failure.
