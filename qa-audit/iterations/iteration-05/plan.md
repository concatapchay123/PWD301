# ITERATION 05 TEST PLAN

**Iteration Focus:** Forms, Client/Server Input Validation, Vietnamese Unicode Diacritics, Length Boundaries & Rapid Double-Submit Protection  
**Responsible Agents:** AGENT 02 (Frontend & UI/UX QA), AGENT 03 (Backend & API QA), AGENT 04 (Database & Data Integrity QA), AGENT 08 (Independent Auditor)  
**Target Environment:** Local Live Stack (`http://localhost:5000`)  
**Browser Engine:** Google Chrome 155 via Playwright  
**Viewport:** 1366 x 768  

---

## 1. Objectives
1. Verify Vietnamese Unicode diacritics resilience (full tone markers like `ắ`, `ặ`, `ễ`, `ệ`, `ỹ`, `ồ`, `ở`) across input, API transmission, database persistence, and DOM rendering.
2. Verify client-side and server-side validation for empty or whitespace-only required fields.
3. Verify email format boundary enforcement (`:invalid` pseudo-class and error rejection).
4. Verify rapid double-submit protection (button disable state / in-flight request lock).
5. Verify oversized string boundaries (length > 255 or maxlength constraints, avoiding unhandled 500 errors).
6. Verify form input XSS containment (HTML escaping of script and event handler payloads).

---

## 2. Test Cases Overview
- `TC-IT05-001`: Vietnamese Unicode Diacritics Storage & Presentation Integrity
- `TC-IT05-002`: Client-Side Empty Required Field Validation
- `TC-IT05-003`: Email Format Boundary Validation
- `TC-IT05-004`: Rapid Double-Submit Button Locking Protection
- `TC-IT05-005`: Extreme Input Length Boundary Handling
- `TC-IT05-006`: Form Input XSS Sanitization & HTML Escape
