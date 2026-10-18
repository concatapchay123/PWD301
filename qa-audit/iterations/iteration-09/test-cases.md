# Test Case Specifications — Iteration 09: File Uploads, ClamAV Fail-Closed Scanning & YouTube 16:9 Player

## Test Case Matrix

| ID | Title | Priority | Target Subsystem | Expected Outcome |
| :--- | :--- | :--- | :--- | :--- |
| `TC-IT09-001` | Strict Non-Archive Attachment Policy | Critical | File Upload Engine | HTTP 400 rejection with canonical Vietnamese message |
| `TC-IT09-002` | Strict 50MB Attachment Ceiling | High | File Upload Validation | Rejection of non-video uploads > 50,000,000 bytes |
| `TC-IT09-003` | ClamAV Fail-Closed Quarantine Defense | Critical | Antivirus & Download Gate | EICAR blocked; unscanned/infected files return HTTP 423 |
| `TC-IT09-004` | Clean Learning Document Upload & Access | High | Document Hub / Student View | Clean PDF attaches to lesson and downloads cleanly |
| `TC-IT09-005` | YouTube Standard 16:9 Full Viewport | High | Student Video Player | Aspect-video (16:9) viewport, 100% width/height, zero crop |
| `TC-IT09-006` | Cover Poster Shield & Custom Controls | High | Video Armor / UI Interaction | Poster shield conceals YouTube UI; custom scrubber functional |

---

### Detailed Test Specifications

#### TC-IT09-001: Strict Non-Archive Attachment Policy
- **Objective:** Verify that compressed archives (.zip, .rar, .7z, .tar, .gz, .bz2, .xz, .iso) are strictly forbidden for lesson attachments, returning the exact Vietnamese error message.
- **Steps:**
  1. Instructor generates a `.zip` archive containing sample files.
  2. Attempt to upload archive to lesson resources via `POST /instructor/courses/<id>/files` or lesson upload endpoint.
  3. Verify HTTP 400 is returned.
  4. Verify exact error message: `"Hệ thống không hỗ trợ tệp nén (.zip, .rar, .7z...). Vui lòng tải trực tiếp tài liệu học tập (PDF, Word, Excel, CAD, 3D...)"`.
- **Pass Criteria:** HTTP 400, exact Vietnamese error message matched.

#### TC-IT09-002: Strict 50MB Attachment Ceiling
- **Objective:** Verify that non-video document and CAD/3D attachments are capped at exactly 50 MB (`50_000_000` bytes).
- **Steps:**
  1. Instructor generates a simulated oversized document (51 MB / 51,000,000 bytes).
  2. Attempt upload as `RESOURCE` or lesson attachment.
  3. Verify upload is rejected fail-closed with HTTP 400 / 413.
  4. Verify error indicates the 50 MB limit exceeded.
- **Pass Criteria:** Rejection with HTTP 400 or 413, file not persisted in database.

#### TC-IT09-003: ClamAV Fail-Closed Quarantine Defense
- **Objective:** Verify ClamAV malware detection and complete denial of student download for any file in `PENDING`, `QUARANTINED`, or `INFECTED` status.
- **Steps:**
  1. Upload the standard EICAR anti-malware test signature (`X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*`).
  2. Verify backend flags file as `INFECTED` or rejects with `FileInfectedError`.
  3. Query download endpoint as Student (`GET /student/files/<id>/download`).
  4. Verify fail-closed defense: Student is strictly blocked (HTTP 423 Quarantine error).
- **Pass Criteria:** Malware quarantined/blocked, student cannot download unscanned or infected files.

#### TC-IT09-004: Clean Learning Document Upload & Access
- **Objective:** Verify that authentic clean learning documents (e.g. PDF/DOCX) pass scanning and are available in the student document list.
- **Steps:**
  1. Instructor uploads a clean PDF file (`asset_type="RESOURCE"`).
  2. Verify virus scan status is `CLEAN`.
  3. Attach resource to a lesson.
  4. Student visits lesson and downloads document.
  5. Verify HTTP 200 with valid PDF content stream.
- **Pass Criteria:** Upload succeeds, status `CLEAN`, download succeeds with HTTP 200.

#### TC-IT09-005: YouTube Standard 16:9 Full Viewport
- **Objective:** Verify that YouTube player uses standard 16:9 full responsive viewport (100% width, 100% height, zero crop) across the student learning view.
- **Steps:**
  1. Open a course lesson with YouTube video in Student browser context.
  2. Inspect `#player-viewport` / `[data-player-type="youtube"]`.
  3. Verify CSS classes contain `aspect-video` and iframe has `width: 100%; height: 100%`.
  4. Verify no negative offsets or cropping styles (`top: -22%` is completely absent).
- **Pass Criteria:** 16:9 aspect ratio confirmed, iframe uncropped and filling container.

#### TC-IT09-006: Cover Poster Shield & Custom Controls
- **Objective:** Verify that the Cover Poster Shield conceals the player before play, and transitions smoothly upon interaction.
- **Steps:**
  1. In Student view before playback, inspect `#...-poster-shield`.
  2. Verify poster shield is displayed with high z-index, blocking raw YouTube branding and red button.
  3. Click big play button `#...-big-play` or poster shield.
  4. Verify custom control bar (`#...-controls`) renders scrubber track, play/pause, and time display.
- **Pass Criteria:** Shield visible prior to play, custom control bar responsive to clicks.
