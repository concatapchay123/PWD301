# ITERATION 02 — PLAN & SCOPE DEFINITION

## 1. Objectives & Focus
Iteration 02 evaluates Authentication, Registration, and Session Lifecycle resilience:
- Valid new student account registration via UI form.
- Duplicate email conflict handling (409 Conflict rejection).
- Password complexity policy enforcement (< 8 characters rejection).
- Negative authentication: wrong password (401 Unauthorized with normalized Vietnamese messaging).
- Security adversarial probe: SQL Injection payload in login input (`' OR '1'='1' --`).
- Session termination & revocation: `POST /auth/logout` and subsequent direct URL guard.

## 2. In-Scope Modules & Endpoints
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`
- Frontend Auth View (`frontend/assets/js/views/auth.js`)
- Auth API Client (`frontend/assets/js/api.js`)
- Single-Page Shell Guard (`frontend/assets/js/router.js`)

## 3. Risk Targets
- SQL Injection authentication bypass.
- Plaintext password exposure in client storage.
- Session lingering or back-button re-entry after explicit logout.
