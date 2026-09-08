# BIGINT Internal IDs + Public UUIDs

**Status:** Accepted / derived from confirmed project rules.

## Decision

Relational PKs use BIGINT; externally exposed identifiers use UUID/GUID where designed.

## Why

Keeps joins/indexes conventional while avoiding predictable internal IDs at public boundaries.

## Canonical references

- [`docs/database/PWD301_DATABASE_ARCHITECTURE/21_ASSUMPTIONS_AND_DECISIONS.md`](../database/PWD301_DATABASE_ARCHITECTURE/21_ASSUMPTIONS_AND_DECISIONS.md)

## Change rule

Do not alter this ADR to change business behavior. Update the canonical specification first when an approved project decision changes.
