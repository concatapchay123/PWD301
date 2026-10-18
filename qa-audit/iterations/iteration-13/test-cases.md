# Iteration 13: Test Case Specifications

**Domain:** Security Control Verification: Anti-tamper Blackout Shield, DevTools Traps, Session Revocation, CSRF & XSS  

---

### TC-IT13-001: Anti-Tamper DevTools Shortcut Trap (F12 / Ctrl+Shift+I) & Full-Screen Blackout Shield
- **Target Invariant:** Invariant 10.8 (Global Anti-Tamper & Security Lockdown).
- **Preconditions:** Authenticated student logged into real Chrome browser at `#/student/dashboard`.
- **Test Steps:**
  1. Trigger keyboard event `F12` (or `Ctrl+Shift+I`).
  2. Verify that `#global-security-blackout-shield` is immediately mounted in DOM.
  3. Verify header displays `"🛡️ CẢNH BÁO AN NINH HỆ THỐNG"`.
  4. Verify reason badge displays `"PHÁT HIỆN CÔNG CỤ DEVTOOLS / MÃ NGUỒN"`.
  5. Verify that `POST /auth/logout` was automatically dispatched to revoke the server-side session.
- **Pass Criteria:** Blackout shield overlays screen with $z$-index 999999, session revoked on server, and client credentials wiped.

---

### TC-IT13-002: View Source & Screen Capture Key Interception (Ctrl+U / PrintScreen)
- **Target Invariant:** Invariant 10.8 (Screen Capture & Source Code Inspection Block).
- **Preconditions:** Authenticated student on course learning or assessment view.
- **Test Steps:**
  1. Trigger keydown event with `Ctrl+U`.
  2. Verify violation detected with reason `"VIEW_SOURCE_ATTEMPT"` and blackout shield triggered.
  3. Verify clipboard cleared (`VideoArmor._clearClipboardStatic()`).
  4. Trigger `PrintScreen` (key 44). Verify violation classified as `"SCREEN_CAPTURE_ATTEMPT"`.
- **Pass Criteria:** Shortcuts blocked, clipboard wiped, lockdown triggered.

---

### TC-IT13-003: Right-Click Context Menu Suppression on Authenticated Surfaces
- **Target Invariant:** Invariant 10.8 (Context Menu Inspection Prevention).
- **Preconditions:** Authenticated user loaded on student or instructor dashboard.
- **Test Steps:**
  1. Dispatch `contextmenu` event on the document / body.
  2. Assert `event.defaultPrevented == true`.
- **Pass Criteria:** Right-click contextmenu event default is strictly prevented.

---

### TC-IT13-004: State-Changing CSRF Token Enforcement (Fail-Closed 400 CSRF_ERROR)
- **Target Invariant:** Session-authenticated state-changing Web/AJAX requests require CSRF protection.
- **Preconditions:** Valid session cookie on `student1@pwd301.local`.
- **Test Steps:**
  1. Dispatch state-changing request (e.g. `POST /auth/profile`) with valid session cookie but `X-CSRFToken` omitted.
  2. Assert response status code is **HTTP 400 Bad Request**.
  3. Assert error code is `"CSRF_ERROR"`.
- **Pass Criteria:** Unprotected state-changing request rejected with HTTP 400 `CSRF_ERROR`.

---

### TC-IT13-005: XSS Payload Sanitization & HTML Output Escaping
- **Target Invariant:** Pure Headless REST API and Client Sanitization (No HTML injection).
- **Preconditions:** Authenticated instructor updating profile or course fields.
- **Test Steps:**
  1. Submit profile update carrying malicious payloads: `<script>alert('XSS')</script>`, `<img src=x onerror=alert(1)>`, `"><svg onload=alert(1)>`.
  2. Fetch profile and verify stored data does not execute scripts.
  3. In real Chrome DOM, assert rendered markup escapes special characters (`&lt;script&gt;` or stripped textContent).
- **Pass Criteria:** Payloads neutralized, zero script execution, clean string encoding.

---

### TC-IT13-006: Sensitive System Secret & Internal Credential Leak Defense
- **Target Invariant:** Zero exposure of internal technical IDs, connection strings, Gemini API keys, or raw SQL stack traces.
- **Preconditions:** Authenticated and unauthenticated endpoints tested across multiple status codes (400, 401, 403, 404, 409, 500).
- **Test Steps:**
  1. Inspect error responses across `ApiClient` requests.
  2. Assert zero instances of `AIzaSy...` (Gemini API key pattern), `Server=...;Password=...` (DB connection strings), `bcrypt`/`argon2` password hashes, or internal server paths.
- **Pass Criteria:** Zero internal secrets or sensitive infrastructure configurations exposed in responses.
