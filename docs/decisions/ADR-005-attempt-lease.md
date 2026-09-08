# Lease Instead of Permanent DB Lock

**Status:** Accepted / derived from confirmed project rules.

## Decision

One editor lease with heartbeat/expiry controls active attempt editing.

## Why

Prevents multi-tab edits without holding long-lived database locks during an exam.

## Canonical references

- [`docs/system/PWD301_SYSTEM_SPECIFICATION/algorithms/07_ATTEMPT_LEASE_ALGORITHM.md`](../system/PWD301_SYSTEM_SPECIFICATION/algorithms/07_ATTEMPT_LEASE_ALGORITHM.md)

## Change rule

Do not alter this ADR to change business behavior. Update the canonical specification first when an approved project decision changes.
