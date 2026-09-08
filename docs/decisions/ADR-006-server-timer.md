# Server-Authoritative Assessment Timer

**Status:** Accepted / derived from confirmed project rules.

## Decision

The server owns started/deadline/close decisions; browser displays countdown only.

## Why

Prevents client-clock manipulation and gives deterministic offline/retry behavior.

## Canonical references

- [`docs/system/PWD301_SYSTEM_SPECIFICATION/algorithms/06_ASSESSMENT_DEADLINE_ALGORITHM.md`](../system/PWD301_SYSTEM_SPECIFICATION/algorithms/06_ASSESSMENT_DEADLINE_ALGORITHM.md)

## Change rule

Do not alter this ADR to change business behavior. Update the canonical specification first when an approved project decision changes.
