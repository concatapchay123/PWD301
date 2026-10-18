# Iteration 13 Test Plan: Security Controls, Anti-Tamper Blackout Shield & Defense-in-Depth

**Iteration:** 13  
**Domain:** Security Control Verification: Anti-tamper Blackout Shield, DevTools Traps, Session Revocation, CSRF & XSS  
**Auditor Lead:** AGENT 05 — Security & RBAC QA  
**Browser Engine:** Real Google Chrome 155 via Playwright (`channel="chrome"`)  
**Backend:** Local Docker container `pwd301_web` (Flask REST API + SQL Server)  
**Execution Objective:** Empirically verify the multi-tier security shields across client-side anti-tamper traps, server-side session revocation, CSRF token fail-closed enforcement, XSS escaping, and zero-exposure of system secrets.

---

## 1. Scope & Security Invariants

1. **Global Anti-Tamper & Security Lockdown (Invariant 10.8):**
   - Multi-tier protection across all authenticated pages.
   - When DevTools opening or unauthorized source code inspection is confirmed (`F12`, `Ctrl+Shift+I/J/C`, `Ctrl+U`, debugger traps):
     - The system immediately overlays the full-screen Blackout Shield (`#global-security-blackout-shield` with `"🛡️ CẢNH BÁO AN NINH HỆ THỐNG"`).
     - Calls server-side session revocation (`POST /auth/logout`).
     - Clears client credentials and navigates to `#/auth/login?security_lockdown=1`.
2. **Context Menu Suppression:**
   - Right-click (`contextmenu`) is prevented to thwart Inspect Element attempts.
3. **State-Changing CSRF Protection:**
   - All state-changing requests (`POST`, `PUT`, `PATCH`, `DELETE`) without valid `X-CSRFToken` are rejected fail-closed with HTTP 400 `CSRF_ERROR`.
4. **XSS & Output Sanitization:**
   - Malicious HTML/JS injection payloads (`<script>`, `<img onerror>`) are escaped and neutralized.
5. **Sensitive Secret & Data Leak Defense:**
   - Zero disclosure of Gemini API keys, SQL connection strings, password hashes, or internal technical stack traces in API responses.

---

## 2. Test Execution Schedule (6 Test Cases)

- **TC-IT13-001:** Anti-Tamper DevTools Shortcut Trap (F12 / Ctrl+Shift+I) & Full-Screen Blackout Shield
- **TC-IT13-002:** View Source & Screen Capture Key Interception (Ctrl+U / PrintScreen)
- **TC-IT13-003:** Right-Click Context Menu Suppression on Authenticated Surfaces
- **TC-IT13-004:** State-Changing CSRF Token Enforcement (Fail-Closed 400 CSRF_ERROR)
- **TC-IT13-005:** XSS Payload Sanitization & HTML Output Escaping
- **TC-IT13-006:** Sensitive System Secret & Internal Credential Leak Defense
