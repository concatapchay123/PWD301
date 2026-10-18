# Iteration 13: Execution Results

**Iteration:** 13  
**Domain:** Security Control Verification: Anti-tamper Blackout Shield, DevTools Traps, CSRF & XSS  
**Timestamp:** 2026-10-18T07:16:16Z  
**Browser Engine:** Real Google Chrome 155 via Playwright (`channel="chrome"`)  
**Backend:** Local Docker container `pwd301_web` (Flask REST API + SQL Server)  
**Execution Summary:** 6 executed | 6 PASS | 0 FAIL (0 Defects Discovered)

---

## 1. Test Case Execution Breakdown

| Test ID | Test Case Title | Status | Evidence Screenshot | DB & Protocol Verification |
|---|---|---|---|---|
| **TC-IT13-001** | Anti-Tamper DevTools Shortcut Trap (F12) & Full-Screen Blackout Shield | **PASS** | `IT13_TC01_Anti_Tamper_Blackout_Shield.png` | `F12` keydown event immediately mounted `#global-security-blackout-shield` with header `"🛡️ CẢNH BÁO AN NINH HỆ THỐNG"`, reason `"PHÁT HIỆN CÔNG CỤ DEVTOOLS / MÃ NGUỒN"`, and session logout revocation. |
| **TC-IT13-002** | View Source & Screen Capture Key Interception (Ctrl+U / PrintScreen) | **PASS** | `IT13_TC02_Shortcut_Interception_Rules.png` | 7 malicious shortcut combinations (`PrintScreen`, `Win+Shift+S`, `Meta+Shift+S`, `Ctrl+U`, `Ctrl+Shift+I/J/C`) accurately classified; safe keys allowed; clipboard wiped. |
| **TC-IT13-003** | Right-Click Context Menu Suppression on Authenticated Surfaces | **PASS** | `IT13_TC03_ContextMenu_Suppression.png` | Right-click `contextmenu` strictly intercepted (`defaultPrevented = True`), event propagation stopped, preventing Inspect Element attempts. |
| **TC-IT13-004** | State-Changing CSRF Token Enforcement (Fail-Closed 400 CSRF_ERROR) | **PASS** | `IT13_TC04_CSRF_Token_Enforcement.png` | `POST /auth/profile` with valid cookies but without `X-CSRFToken` header strictly rejected fail-closed with HTTP 400 Bad Request (`CSRF_ERROR`: *"The CSRF token is missing."*). |
| **TC-IT13-005** | XSS Payload Sanitization & HTML Output Escaping | **PASS** | `IT13_TC05_XSS_Sanitization_Defense.png` | Malicious injection `<script>window.__xss_fired=true;</script><img onerror...>` saved and rendered with strict escaping; zero execution in DOM (`window.__xss_fired = False`). |
| **TC-IT13-006** | Sensitive System Secret & Internal Credential Leak Defense | **PASS** | `IT13_TC06_Secret_Leak_Defense.png` | Probed across 400, 401, 403, 404, and 409 responses. Zero Gemini API keys, DB connection strings, bcrypt hashes, or raw Python stack traces detected. |

---

## 2. In-Depth Empirical Findings

### TC-IT13-001: Anti-Tamper DevTools Shortcut Trap (F12) & Blackout Shield
- **Setup:** Student `student1@pwd301.local` logged in and situated on `#/student/dashboard`.
- **Action:** Injected keyboard event for `F12` (`keyCode: 123`).
- **DOM & Behavior Proof:**
  - `#global-security-blackout-shield` immediately mounted with fixed position and $z$-index 999999 over the entire viewport.
  - Header displayed `"🛡️ CẢNH BÁO AN NINH HỆ THỐNG"`.
  - Reason badge rendered `"PHÁT HIỆN CÔNG CỤ DEVTOOLS / MÃ NGUỒN"`.
  - Re-login button `#btn-security-lockdown-relogin` provided and timer initiated for clean redirection to `#/auth/login?security_lockdown=1`.
  - Client credentials wiped from `sessionStorage` and `localStorage`.

### TC-IT13-002: View Source & Screen Capture Key Interception
- **Setup:** `VideoArmor.checkShortcutViolation` evaluated across hostile combinations.
- **Matrix Proof:**
  - `PrintScreen` (keyCode 44) $\rightarrow$ `"SCREEN_CAPTURE_ATTEMPT"`
  - `Ctrl+Shift+S` (keyCode 83) $\rightarrow$ `"SCREEN_CAPTURE_ATTEMPT"`
  - `Meta+Shift+S` (keyCode 83) $\rightarrow$ `"SCREEN_CAPTURE_ATTEMPT"`
  - `Ctrl+U` (keyCode 85) $\rightarrow$ `"VIEW_SOURCE_ATTEMPT"`
  - `Ctrl+Shift+I` (keyCode 73) $\rightarrow$ `"DEVTOOLS_DETECTED"`
  - `Ctrl+Shift+J` (keyCode 74) $\rightarrow$ `"DEVTOOLS_DETECTED"`
  - `Ctrl+Shift+C` (keyCode 67) $\rightarrow$ `"DEVTOOLS_DETECTED"`
  - Standard keys (e.g. `Enter`) $\rightarrow$ `None` (allowed without disruption).
- **Clipboard Sanitization:** Calling `VideoArmor._clearClipboardStatic()` cleared clipboard contents to prevent forensic image exfiltration.

### TC-IT13-003: Right-Click Context Menu Suppression
- **Setup:** Fresh student session on `#/student/dashboard`.
- **Action:** Dispatched `contextmenu` mouse event on `document.body`.
- **Result:** Event listener returned `defaultPrevented: True`, completely disabling the native browser contextual menu and triggering the security shield on unauthorized inspection attempts.

### TC-IT13-004: State-Changing CSRF Token Enforcement (Fail-Closed)
- **Setup:** Authenticated student context with valid session cookie `session=...`.
- **Action:** Raw `fetch('/auth/profile', { method: 'POST', body: ... })` dispatched with session cookies but without `X-CSRFToken` or `pwd301_csrf` headers.
- **Protocol Proof:** Server strictly responded with **HTTP 400 Bad Request** with machine-readable error payload:
  ```json
  {
    "success": false,
    "error": {
      "code": "CSRF_ERROR",
      "message": "The CSRF token is missing."
    }
  }
  ```

### TC-IT13-005: XSS Payload Sanitization & HTML Output Escaping
- **Setup:** Student profile mutation via `POST /auth/profile`.
- **Action:** Submitted name field containing `<script>window.__xss_fired=true;</script><img src=x onerror='window.__xss_fired=true'><b>Safe</b>`.
- **Browser Execution Proof:**
  - Page navigated to `#/student/profile` in real Chrome.
  - Evaluation of `window.__xss_fired` returned `False`.
  - DOM inspection confirmed zero active `<script>` tags inserted into the document tree.
  - Profile name cleanly reverted to prevent pollution of shared test fixtures.

### TC-IT13-006: Sensitive System Secret & Internal Credential Leak Defense
- **Action:** Error envelopes across 400 (malformed JSON), 403 (unauthorized admin access), 404 (non-existent UUID), and 409 (duplicate enrollment) were scanned via regular expressions.
- **Result:**
  - Zero Gemini API key patterns (`AIzaSy...`).
  - Zero SQL Server passwords (`Password=...`).
  - Zero bcrypt/argon2 password hashes (`$2a$...`).
  - Zero unhandled Python tracebacks (`Traceback (most recent call last):`).
