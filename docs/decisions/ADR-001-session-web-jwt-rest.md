# Session Web + JWT REST Split

**Status:** Accepted / derived from confirmed project rules.

## Decision

Web UI and AJAX use Flask session auth; REST API uses JWT.

## Why

Avoids exposing JWT to browser localStorage while preserving the rubric/API requirement.

## Canonical references

- [`docs/system/PWD301_SYSTEM_SPECIFICATION/authentication/01_AUTHENTICATION_ARCHITECTURE.md`](../system/PWD301_SYSTEM_SPECIFICATION/authentication/01_AUTHENTICATION_ARCHITECTURE.md)

## Change rule

Do not alter this ADR to change business behavior. Update the canonical specification first when an approved project decision changes.
