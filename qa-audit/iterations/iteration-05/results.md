# ITERATION 05 — EXECUTION RESULTS

**Execution Date:** 2026-10-18  
**Iteration Focus:** Forms, Client/Server Input Validation, Vietnamese Unicode Diacritics, Length Boundaries & Rapid Double-Submit Protection  
**Browser Engine:** Google Chrome 155.0.4283.60 (Playwright sync API)  
**Viewport:** 1366 x 768  
**Live Target:** `http://localhost:5000`  

---

## 1. Test Execution Summary

| Test Case ID | Test Case Name | Status | Evidence Artifact | Empirical Notes |
|---|---|---|---|---|
| **TC-IT05-001** | Vietnamese Unicode Diacritics Storage & Presentation | **PASS** | `IT05_TC01_vietnamese_unicode_integrity.png` | Stored `Nguyễn Thị Ánh Tuyết (Kỹ Sư Phần Mềm)`; 100% round-trip preservation in DB, input field, and topbar |
| **TC-IT05-002** | Client-Side Empty Required Field Validation | **PASS** | `IT05_TC02_empty_field_validation.png` | Whitespace-only display name rejected with localized toast warning: *"Vui lòng nhập họ và tên hiển thị hợp lệ (tối thiểu 2 ký tự)."* |
| **TC-IT05-003** | Email Format Boundary Validation | **PASS** | `IT05_TC03_email_format_boundary.png` | Malformed email string flagged invalid by HTML5 validity check (`checkValidity() === false`) |
| **TC-IT05-004** | Rapid Double-Submit Button Locking Protection | **PASS** | `IT05_TC04_double_submit_locking.png` | Submit button immediately disabled upon first click (`disabledImmediately: True`) with spinning loading text |
| **TC-IT05-005** | Extreme Input Length Boundary Handling | **PASS** | `IT05_TC05_length_boundary_handling.png` | Client input capped at 100 chars; backend API returned HTTP 400 (`VALIDATION_ERROR: Tên hiển thị phải từ 2 đến 150 ký tự.`), zero 500 crash |
| **TC-IT05-006** | Form Input XSS Sanitization & HTML Escape | **PASS** | `IT05_TC06_xss_sanitization_defense.png` | Injected `<script>` tags escaped to `&lt;script&gt;`; `window.__xss_detected` remained `undefined` (zero execution) |

---

## 2. Invariant & Security Verification

### 2.1. Vietnamese Unicode Character Integrity
- The system correctly supports Vietnamese UTF-8 multi-byte characters across SQL Server (`NVARCHAR`), Flask REST serialization, and SPA DOM rendering.
- Tested compound tone marks (`Nguyễn Thị Ánh Tuyết`) remained identical before and after page reloads, showing no character loss or mojibake corruption.

### 2.2. Defense-in-Depth Form Validation & XSS Sanitization
- Form inputs feature dual-layer defense:
  1. Client-layer validation prevents empty submits and caps input length via HTML attributes and active event guards.
  2. Server-layer schema validation enforces bounds (2 to 150 characters) and returns standardized HTTP 400 JSON envelopes.
- XSS injection attempts are completely neutralized by `UI.escapeHtml()`, rendering tags as harmless text nodes without DOM script evaluation.

---

## 3. Evidence Gallery (Iteration 05)
1. `qa-audit/iterations/iteration-05/evidence/IT05_TC01_vietnamese_unicode_integrity.png`
2. `qa-audit/iterations/iteration-05/evidence/IT05_TC02_empty_field_validation.png`
3. `qa-audit/iterations/iteration-05/evidence/IT05_TC03_email_format_boundary.png`
4. `qa-audit/iterations/iteration-05/evidence/IT05_TC04_double_submit_locking.png`
5. `qa-audit/iterations/iteration-05/evidence/IT05_TC05_length_boundary_handling.png`
6. `qa-audit/iterations/iteration-05/evidence/IT05_TC06_xss_sanitization_defense.png`
