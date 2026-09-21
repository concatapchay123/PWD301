---
id: 4
title: "Real Operating System Hardware Telemetry vs Mock Metric Calculations"
status: open
type: internal
skill: [superpowers, ponytail]
proposes_skill: []
siblings_checked: "none"
area: "admin-monitoring/telemetry"
date: 2026-09-20
session_context: "Backfilled from 304 project conversation transcripts (2026-09-08 to 2026-09-20)"
parked_until: 
resolved: 
resolution: 
reference: 
---

**Issue:** Server hardware telemetry on the Admin Dashboard was generating calculated or mock values that did not reflect actual CPU, RAM, Disk, and Network utilization of the host machine or container, causing confusion during operations.

**Suggested improvement:** Integrate real OS telemetry via `psutil` with multi-platform support (Windows host and Linux Docker containers), caching metrics briefly to avoid CPU thrashing on repeated dashboard polling.

**Principle:** System monitoring dashboards must present authentic physical hardware telemetry; synthetic or simulated metrics undermine operational trust.
