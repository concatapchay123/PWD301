# Defect Log — Iteration 09: File Uploads, ClamAV Fail-Closed Scanning & YouTube 16:9 Player

## 1. Defect Summary Table

| Defect ID | Severity | Status | Subsystem | Description | Root Cause / Note |
| :--- | :--- | :--- | :--- | :--- | :--- |
| *None* | N/A | CLOSED | N/A | No defects discovered in Iteration 09 | All 6 test cases passed 100% |

---

## 2. Invariant Adherence & Operational Verification

1. **Non-Archive Policy Invariant:**
   - Archives (.zip, .rar, .7z, .tar, .gz, .bz2, .xz, .iso) are strictly blocked with exact Vietnamese message:
     `"Hệ thống không hỗ trợ tệp nén (.zip, .rar, .7z...). Vui lòng tải trực tiếp tài liệu học tập (PDF, Word, Excel, CAD, 3D...)"`.
   - File magic bytes and extensions are checked before saving.

2. **Attachment Size Ceiling Invariant:**
   - Non-video documents and attachments are capped at 50,000,000 bytes (50 MB).
   - Early stream chunk limits prevent disk exhaustion.

3. **ClamAV Fail-Closed Invariant:**
   - EICAR test malware triggers immediate quarantine and HTTP 403 `FILE_INFECTED` rejection.
   - Non-clean/quarantined assets are never accessible to students.

4. **YouTube Standard 16:9 Viewport & Cover Poster Shield:**
   - 100% width and 100% height uncropped display (aspect ratio exactly 16:9).
   - Cover Poster Shield conceals player before playback.
