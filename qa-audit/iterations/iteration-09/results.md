# Execution Results — Iteration 09: File Uploads, ClamAV Fail-Closed Scanning & YouTube 16:9 Player

**Execution Date:** 2026-10-18T06:18:29Z  
**Target Environment:** Local Docker Stack (`pwd301_web` on `http://localhost:5000`, ClamAV Daemon on `localhost:3310`, SQL Server on `localhost:1433`)  
**Execution Engine:** Real Google Chrome (Playwright `channel="chrome"`), REST API Envelopes, ClamAV Malware Scanner  
**Total Test Cases:** 6  
**Passed:** 6 (100%)  
**Failed:** 0 (0%)  
**Blocked:** 0 (0%)  

---

## 1. Test Execution Summary

| Test Case ID | Test Case Name | Status | Evidence Screenshot | Execution Notes |
| :--- | :--- | :---: | :--- | :--- |
| `TC-IT09-001` | Strict Non-Archive Attachment Policy (Rejection of .zip, .rar, .7z) | **PASS** | `IT09_TC01_archive_rejection.png` | Compressed archives (.zip, .rar) rejected with HTTP 400 and exact canonical Vietnamese message: *"Hệ thống không hỗ trợ tệp nén (.zip, .rar, .7z...). Vui lòng tải trực tiếp tài liệu học tập (PDF, Word, Excel, CAD, 3D...)"*. |
| `TC-IT09-002` | Strict 50MB Attachment Ceiling Enforcement | **PASS** | `IT09_TC02_size_ceiling_50mb.png` | 51MB document upload rejected fail-closed during streaming with HTTP 413: *"File stream exceeded maximum limit of 50000001 bytes."* |
| `TC-IT09-003` | ClamAV Fail-Closed Quarantine Defense (Malware Containment) | **PASS** | `IT09_TC03_clamav_quarantine.png` | EICAR anti-malware signature detected by ClamAV daemon. Rejected with HTTP 403 (`FILE_INFECTED`) and quarantined fail-closed. |
| `TC-IT09-004` | Clean Learning Document Upload & Access | **PASS** | `IT09_TC04_clean_document_attached.png` | Clean PDF uploaded (`eea6e0ab-954d-426d-ba43-42911b43ab39`), scan status `CLEAN`. Student downloaded clean PDF with HTTP 200. |
| `TC-IT09-005` | YouTube Standard 16:9 Full Viewport & Aspect Ratio Verification | **PASS** | `IT09_TC05_youtube_16_9_viewport.png` | Real DOM dimensions verified: Width 766px, Height 430.875px. Aspect ratio 1.778:1 (exact 16:9). No cropping, uncropped viewport. |
| `TC-IT09-006` | Cover Poster Shield & Custom Control Bar Interaction | **PASS** | `IT09_TC06_poster_shield_custom_controls.png` | Cover Poster Shield verified concealing player before user play interaction (`z-index: 15`). Custom editorial controls (scrubber, play/mute) active. |

---

## 2. Detailed Empirical Verification Findings

### TC-IT09-001: Strict Non-Archive Attachment Policy
- **Action:** Uploaded `curriculum_bundle.zip` (containing PK magic bytes) and `project_assets.rar` to `POST /instructor/courses/<id>/files`.
- **Response Verification:** Backend rejected both uploads with HTTP 400 (`FileValidationError`).
- **Exact Vietnamese Translation:** The returned error message strictly matched:
  `"Hệ thống không hỗ trợ tệp nén (.zip, .rar, .7z...). Vui lòng tải trực tiếp tài liệu học tập (PDF, Word, Excel, CAD, 3D...)"`.

### TC-IT09-002: Strict 50MB Attachment Ceiling Enforcement
- **Action:** Streamed a 51MB (`53,477,376` bytes) payload declaring `application/pdf` to `POST /instructor/courses/<id>/files`.
- **Stream Protection:** `LimitingStream` and early streaming chunk validation detected size exceeding `50,000,000` bytes.
- **Fail-Closed Result:** Stream aborted immediately with HTTP 413, preventing disk exhaustion.

### TC-IT09-003: ClamAV Fail-Closed Quarantine Defense
- **Action:** Uploaded standard EICAR anti-malware test signature (`X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*`).
- **Antivirus Detection:** Local ClamAV daemon intercepted the signature. Backend threw `FileInfectedError` (HTTP 403):
  *"Tệp 'eicar_malware_test.pdf' bị từ chối do phát hiện mã độc hoặc cấu trúc nguy hiểm. Hệ thống đã tự động chặn tải lên và cách ly tệp này."*
- **Quarantine Isolation:** File was isolated directly to quarantine; student download barrier verified fail-closed.

### TC-IT09-004: Clean Learning Document Upload & Access
- **Action:** Uploaded clean `%PDF-1.4` document. ClamAV daemon passed file with `virus_scan_status: "CLEAN"`.
- **Student Download:** Enrolled student requested `GET /student/files/<id>/download`. Response returned HTTP 200 with `%PDF` binary header stream.

### TC-IT09-005: YouTube Standard 16:9 Full Viewport & Aspect Ratio Verification
- **Action:** Student navigated in Chrome to `#/student/courses/detail?id=...&lesson_id=...`.
- **DOM Inspection:** `#cisco-stream-player-container` was located. Viewport bounding rect: `width: 766px`, `height: 430.875px`.
- **Mathematical Ratio:** `766 / 430.875 = 1.7777777777777777` (deviation from `16/9` = `0.000%`).
- **Zero-Crop Invariant:** Iframe uses 100% width and 100% height without negative margin cropping (`top: -22%` completely absent).

### TC-IT09-006: Cover Poster Shield & Custom Control Bar Interaction
- **Action:** Verified Cover Poster Shield (`#cisco-stream-player-poster-shield`) covered the player with `z-index: 15`, blocking native YouTube red play buttons.
- **Interaction:** Triggered play via `#cisco-stream-player-poster-shield`.
- **Control Bar:** Custom editorial controls rendered scrubber track (`#cisco-stream-player-progress-track`), play button (`#cisco-stream-player-play-btn`), and mute button.
