# ITERATION 05 TEST SPECIFICATION

## Test Cases Detailed Specification

### TC-IT05-001: Vietnamese Unicode Diacritics Storage & Presentation Integrity
- **Preconditions:** Authenticated student on `#/student/settings`.
- **Steps:**
  1. Input `Nguyễn Thị Ánh Tuyết (Kỹ Sư Phần Mềm)` into `#settings-display-name`.
  2. Click `#btn-save-profile` and wait for API confirmation.
  3. Reload page and check `#topbar-user-name` and `#settings-display-name`.
- **Expected Result:** Full Vietnamese tone marks (`ễ`, `ị`, `Á`, `ế`, `ỹ`, `ư`, `ề`) are accurately preserved in database and rendered without mojibake or entity corruption.

### TC-IT05-002: Client-Side Empty Required Field Validation
- **Preconditions:** Authenticated student on `#/student/settings`.
- **Steps:**
  1. Clear `#settings-display-name` completely (empty string or single whitespace).
  2. Click `#btn-save-profile`.
- **Expected Result:** Form submission blocked; toast warning displayed ("Vui lòng nhập họ và tên hiển thị hợp lệ...") or browser prevents submit; zero corrupt records written to backend.

### TC-IT05-003: Email Format Boundary Validation
- **Preconditions:** Navigate to `#/auth` on registration tab.
- **Steps:**
  1. Enter invalid email formats: `not-an-email`, `user@`, `@domain.com`.
  2. Check HTML5 validity `:invalid` property.
- **Expected Result:** Browser flags field as invalid and prevents form submission.

### TC-IT05-004: Rapid Double-Submit Button Locking Protection
- **Preconditions:** Authenticated student on `#/student/settings`.
- **Steps:**
  1. Enter valid name in `#settings-display-name`.
  2. Rapidly click `#btn-save-profile` twice within 50ms.
  3. Check `saveBtn.disabled` property during in-flight network dispatch.
- **Expected Result:** Save button transitions to disabled state with loading indicator, preventing concurrent duplicate requests.

### TC-IT05-005: Extreme Input Length Boundary Handling
- **Preconditions:** Authenticated student on `#/student/settings`.
- **Steps:**
  1. Attempt to enter string with length 500 characters.
  2. Inspect input value length or submit payload.
- **Expected Result:** Input value is cleanly capped by `maxlength="100"` or backend validates length gracefully without 500 server crash.

### TC-IT05-006: Form Input XSS Sanitization & HTML Escape
- **Preconditions:** Authenticated student on `#/student/settings`.
- **Steps:**
  1. Enter `<script>window.__xss_detected=true;</script><img src=x onerror=window.__xss_detected=true>` into display name.
  2. Submit profile update.
  3. Inspect page DOM and check `window.__xss_detected`.
- **Expected Result:** Payload is HTML-escaped; `window.__xss_detected` remains `undefined`; zero script execution.
