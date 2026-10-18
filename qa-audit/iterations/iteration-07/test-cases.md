# ITERATION 07 TEST SPECIFICATION

## Test Cases Detailed Specification

### TC-IT07-001: Standard JSON Success Envelope Verification
- **Target Endpoint:** `GET /admin/health`
- **Steps:**
  1. Send GET request to `http://localhost:5000/admin/health`.
  2. Inspect response headers and JSON body.
- **Expected Result:** HTTP 200 OK; `Content-Type: application/json`; Body contains authentic telemetry with `status: healthy` or `success: true`.

### TC-IT07-002: Standard JSON Error Envelope Structure & Correlation ID
- **Target Endpoint:** `GET /api/nonexistent-route-endpoint-xyz`
- **Steps:**
  1. Send GET request to non-existent route.
  2. Inspect response envelope schema.
- **Expected Result:** HTTP 404 Not Found; `success: false`; `error` object includes `code` (e.g. `RESOURCE_NOT_FOUND` / `NOT_FOUND`), `message`, and non-empty `correlation_id`.

### TC-IT07-003: HTTP 400 Bad Request & Field Errors Schema
- **Target Endpoint:** `POST /auth/register`
- **Steps:**
  1. Send POST request with empty payload `{}` and valid CSRF token.
  2. Inspect response status and error object.
- **Expected Result:** HTTP 400 Bad Request; `code: VALIDATION_ERROR` or similar; `field_errors` dictionary populated.

### TC-IT07-004: HTTP 401 Unauthorized Authentication Boundary
- **Target Endpoint:** `GET /student/dashboard` (without session cookie)
- **Steps:**
  1. Send request without any authentication cookies or bearer tokens.
  2. Inspect HTTP status code and redirect/error behavior.
- **Expected Result:** HTTP 401 Unauthorized or redirect to `/auth`; JSON response when requesting API formats.

### TC-IT07-005: HTTP 403 Forbidden on Cross-Role Access
- **Target Endpoint:** `GET /admin/users` (with Student authenticated session)
- **Steps:**
  1. Authenticate as student `student1@pwd301.local`.
  2. Send GET request to `/admin/users`.
- **Expected Result:** HTTP 403 Forbidden; `error.code: FORBIDDEN`; localized Vietnamese message.

### TC-IT07-006: Pure Headless Invariant (Zero HTML Leakage)
- **Target Endpoints:** Sample of 10 disparate API endpoints across blueprints.
- **Steps:**
  1. Send requests across `auth`, `student`, `instructor`, `admin`, `api_courses`.
  2. Verify `Content-Type` strictly starts with `application/json`.
  3. Verify body does not contain `<!DOCTYPE html>`, `<html>`, or Jinja templates.
- **Expected Result:** 100% pure headless responses across all error and success outcomes.
