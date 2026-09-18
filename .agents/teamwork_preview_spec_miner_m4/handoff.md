# Milestone 4 (R4: Multi-Format Lecture Authoring & Media Support) Specification Mining Report

## Executive Summary
This report establishes the authoritative specification, database schema, validation rules, security invariants, and interface contracts for **Milestone 4 (F12, F13, F14)** based on `docs/system/PWD301_SYSTEM_SPECIFICATION/`, `docs/database/PWD301_DATABASE_ARCHITECTURE/`, `frontend-preview/`, and existing service implementations.

---

## 1. Observation

### 1.1 Specification & Invariants Sources
1. **`docs/system/PWD301_SYSTEM_SPECIFICATION/business/11_FILE_MANAGEMENT.md` (lines 3-13)**:
   - *"Upload enters quarantine and is inaccessible until all required checks pass."*
   - *"Malware scanner failure/unavailable is fail-closed."*
   - *"Macro-enabled Office is forbidden; parser resource/decompression limits apply."*
   - *"Baseline sizes: image ~10 MB, PDF 50 MB, DOCX 50 MB, PPTX 100 MB, video < 1 GB."*
   - *"Primary persistence: `file_blobs`, `file_assets`, `file_revisions`, `file_scan_results`, `lesson_resources`, `question_revision_resources`."*
2. **`docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md` (lines 3, 5, 20-21)**:
   - **Invariant 3**: *"Role is not enough; authorize the concrete resource."*
   - **Invariant 18**: *"Unsafe/unscanned files cannot activate; scanner failure is fail-closed; video < 1 GB."*
   - **Invariant 19**: *"FileAsset has at most one ACTIVE revision; shared blob deletion respects references/recovery."*
3. **`docs/system/PWD301_SYSTEM_SPECIFICATION/business/01_BUSINESS_RULE_CATALOG.md`**:
   - `FILE-001`: *"Upload quarantine, fail-closed malware scan (activation requires PASS set)."*
   - `FILE-002`: *"Macro Office forbidden + parser resource limits."*
   - `FILE-003`: *"Physical dedup SHA-256."*
   - `FILE-005`: *"Authorized app route only; object permission check."*
4. **`docs/decisions/ADR-002-database-identifiers.md` & `ADR-008-file-physical-logical.md`**:
   - Relational PKs use `BIGINT`; externally exposed identifiers use `UUID/GUID`.
   - Content-hash deduplicated physical blobs are separated from logical assets/revisions/references.

### 1.2 Database Architecture Sources
1. **`docs/database/PWD301_DATABASE_ARCHITECTURE/sql/006_files_import.sql` (lines 104-119)**:
   ```sql
   CREATE TABLE lesson_resources (
       id BIGINT IDENTITY(1,1) NOT NULL,
       lesson_id BIGINT NOT NULL,
       file_asset_id BIGINT NOT NULL,
       position INT NOT NULL DEFAULT (1),
       label NVARCHAR(255) NULL,
       is_required BIT NOT NULL DEFAULT (0),
       created_at DATETIME2(3) NOT NULL DEFAULT (SYSUTCDATETIME()),
       CONSTRAINT pk_lesson_resources PRIMARY KEY (id),
       CONSTRAINT uq_lesson_resources_lesson_id_file_asset_id_1 UNIQUE (lesson_id, file_asset_id),
       CONSTRAINT uq_lesson_resources_lesson_id_position_2 UNIQUE (lesson_id, position),
       CONSTRAINT ck_lesson_resources_1 CHECK (position > 0),
       CONSTRAINT fk_lesson_resources_lesson_id FOREIGN KEY (lesson_id) REFERENCES lessons (id),
       CONSTRAINT fk_lesson_resources_file_asset_id FOREIGN KEY (file_asset_id) REFERENCES file_assets (id)
   );
   ```
2. **`docs/database/PWD301_DATABASE_ARCHITECTURE/09_DATA_DICTIONARY_FILES_IMPORT.md` (lines 339-386)**:
   - Table `lesson_resources`: links Lesson to logical `FileAsset`; access rights pass through Lesson and Course.
   - Unique constraints: `(lesson_id, file_asset_id)` and `(lesson_id, position)`.
   - Index: `ix_lesson_resources_lesson` on `(lesson_id, position)`.
   - Delete behavior: removes link only; asset and blob cleanup handled separately.

### 1.3 Codebase Findings
1. **`src/pwd301/models/course.py` (lines 424-546)**:
   - `Lesson` model maps to `lessons` table.
   - Missing relationship: `Lesson` does NOT currently define `resources = relationship("LessonResource", ...)` back-reference.
2. **`src/pwd301/models/file_import.py` (lines 459-512)**:
   - `LessonResource` model maps to `lesson_resources` table.
   - Defines `lesson = relationship("Lesson", foreign_keys=[lesson_id])` and `file_asset = relationship("FileAsset", foreign_keys=[file_asset_id])`.
   - Line 508-511 defines synthetic public UUIDv5 property: `public_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"pwd301.lesson_resource.{self.id}")` adhering to ADR-002.
3. **`src/pwd301/services/file_service.py`**:
   - Line 1057-1120: `attach_resource_to_lesson(actor, lesson_id, asset_id, is_downloadable=True, label=None, session=None)`:
     - Enforces instructor course ownership: `require_course_manager(actor, lesson.course_id)`.
     - Validates course isolation: `asset.course_id == lesson.course_id`.
     - Calculates `max(position) + 1` to guarantee uniqueness.
   - Line 1123-1160: `detach_resource_from_lesson(actor, lesson_id, resource_id, session=None)`:
     - Enforces course manager check and detaches `LessonResource` link.
   - Line 922-1054: `get_file_for_download(actor, asset_id, revision_no=None, session=None)`:
     - Strictly enforces: if student, course must be `PUBLISHED`, student must have `ACTIVE` enrollment, and attached lesson must be `PUBLISHED` (lines 974-987).
     - Fail-closed security checks: blocks quarantined, rejected, or infected files (lines 1018-1031).
   - Line 193-206 & 330-354: Video size limit strictly `< 1 GB` (`1_000_000_000` bytes); streams abort immediately via `LimitingStream` on overflow.
   - Line 60-94: Forbidden macro-enabled Office extensions (`.docm`, `.xlsm`, `.pptm`, etc.) and executables.
4. **`src/pwd301/blueprints/instructor/routes.py` (lines 603-631)**:
   - `POST /courses/<course_id>/lessons` currently only accepts JSON or standard URL-encoded form data (`title`, `estimated_duration_minutes`, `position`, `summary`, `markdown_content`). It does not process multipart file uploads (`request.files`).
5. **`src/pwd301/templates/instructor/course_manage.html` (lines 234-275)**:
   - Modal `#newLessonModal` lacks `enctype="multipart/form-data"` and lacks media upload inputs.
6. **`src/pwd301/templates/student/lesson.html` (lines 348-420 & 543-570)**:
   - Video player canvas (`#udemy-video-canvas`) is currently a static mock with SVG placeholder buttons, lacking an HTML5 `<video>` element with actual streaming source.
   - Tab 5 (`#pane-resources`) contains hardcoded Vietnamese mock downloads ("Slide bài giảng: 2.4 MB", "Mã nguồn thực hành: 5.8 MB") with dummy `alert(...)` handlers instead of iterating over `lesson.resources`.
7. **`frontend-preview/assets/js/views/student.js` (lines 950-985)**:
   - Canonical UI specification: lists `lesson.resources` with file icon, format badge, file title, size, and download button. If empty, displays fallback alert.

---

## 2. Logic Chain

1. **Requirement & User Intent**:
   - Milestone 4 mandates multi-format lecture authoring and media support. Instructors must be able to upload and attach media (video, PDF, DOCX, PPTX) to lessons, and students must be able to view and stream these materials seamlessly while strictly preserving platform security and invariant rules.
2. **Schema & Model Consistency**:
   - The database table `lesson_resources` already exists in `006_files_import.sql` with valid foreign keys and unique constraints.
   - The SQLAlchemy model `LessonResource` already exists in `file_import.py`.
   - To make resource handling idiomatic and efficient across Jinja templates and services, `Lesson` in `course.py` must declare a bidirectional relationship `resources = relationship("LessonResource", back_populates="lesson", cascade="all, delete-orphan", order_by="LessonResource.position")`, while updating `LessonResource.lesson` with `back_populates="resources"`.
3. **Storage & Validation Pipeline**:
   - `file_service.store_file_stream` already handles SHA-256 deduplication (Algorithm 12), file categorization, ClamAV scanning, and size enforcement.
   - Authoring routes (`POST /instructor/courses/<course_id>/lessons` and a dedicated resource attach route) can consume uploaded files through `store_file_stream`, set `asset_type="RESOURCE"`, and immediately bind them via `attach_resource_to_lesson`.
4. **Streaming & Partial Content**:
   - Both instructor download (`/instructor/courses/<course_id>/files/<asset_id>/download`) and student download (`/student/courses/<course_id>/files/<asset_id>/download`) use Flask's `send_file(..., conditional=True)`.
   - `conditional=True` natively implements HTTP 206 Partial Content (Range requests). This satisfies browser streaming requirements for HTML5 `<video>` tags without requiring third-party video streaming daemons.
5. **Zero-Trust Fail-Closed Security (Invariant 18 & FILE-005)**:
   - `get_file_for_download` ensures students cannot bypass quarantine or access draft content.
   - If a file is uploaded to a DRAFT lesson, students receive 403 Forbidden until the lesson is published.
   - If a file is quarantined or infected, students receive 403 `FILE_QUARANTINED` / `FILE_INFECTED`.
   - If an instructor attempts to attach an asset from another course, `FileValidationError` blocks the operation.

---

## 3. Specification Miner Tables

### Features Discovered
| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Authoring | F12.1: Multi-Format Media Upload on Lesson Creation | Instructor uploads lecture media (Video, PDF, DOCX, PPTX) concurrently with lesson creation. | Multipart form: `title`, `markdown_content`, `media_file` (optional), `resource_files[]` (optional) | 201 Created Lesson with bound `LessonResource` records | 400 Validation Error on missing title/content; 413 on size limit | `ORIGINAL_REQUEST.md` §R4, `PROJECT.md` §M4 |
| 2 | Authoring | F12.2: In-Place Resource Attachment to Existing Lesson | Dedicated route to upload and attach new learning resources to an existing lesson. | `POST /instructor/courses/<cid>/lessons/<lid>/resources`: file stream, label | 201 Created `LessonResource` | 404 Lesson Not Found; 403 Course Manager Required | `file_service.py:1057`, `PROJECT.md` §M4 |
| 3 | Authoring | F12.3: Lesson Resource Detachment | Instructor can remove a resource link from a lesson without deleting the underlying physical asset. | `POST /instructor/courses/<cid>/lessons/<lid>/resources/<rid>/delete` | 200 OK or 302 Redirect | 404 Resource Not Found; 403 Unauthorized | `file_service.py:1123` |
| 4 | Validation | F12.4: Video Size Exclusive Limit (< 1 GB) | Video file uploads must be strictly less than 1,000,000,000 bytes. | Binary stream / `content-length` | Accepted if < 1 GB | 413 `FileSizeLimitExceededError` if >= 1,000,000,000 bytes | Invariant 18, `file_service.py:194` |
| 5 | Validation | F12.5: Document Category Size Limits | Baseline sizes: Image <= 10 MB, PDF <= 50 MB, DOCX <= 50 MB, PPTX <= 100 MB. | File stream | Accepted if within limits | 413 `FileSizeLimitExceededError` | `11_FILE_MANAGEMENT.md`, `file_service.py:207` |
| 6 | Validation | F12.6: Dangerous & Macro Office Extension Blocking | Rejects executable scripts (`.exe`, `.sh`, `.bat`, `.py`) and macro-enabled Office (`.docm`, `.pptm`, `.xlsm`). | Filename extension | Accepted if not in blocklist | 400 `FileValidationError` | `11_FILE_MANAGEMENT.md`, `file_service.py:61` |
| 7 | Validation | F12.7: Anti-Path Traversal Filename Sanitization | Strips null bytes, directory traversal patterns (`../`), and invalid filename characters. | Raw filename string | Sanitized basename string | Fallback to `unnamed_file` if completely empty | `file_service.py:128` |
| 8 | Architecture | F13.1: Content-Hash SHA-256 Blob Deduplication | Deduplicates identical media files across lessons and courses using SHA-256 hash. | File byte stream | Reused or new `FileBlob` with incremented `reference_count` | Safe rollback on DB error | Algorithm 12, ADR-008, `006_files_import.sql:10` |
| 9 | Architecture | F13.2: Lesson-to-Resource Model Relationship | `Lesson.resources` bidirectional relationship with cascade deletion and position ordering. | `lesson.resources` property access | List of `LessonResource` objects | Empty list if no resources | `PROJECT.md` §M4, `course.py:530` |
| 10 | Architecture | F13.3: LessonResource Position Ordering | Manages 1-based contiguous ordering (`position > 0`) per lesson with uniqueness. | Integer position | Ordered sequence | Unique constraint violation if duplicate position attempted | `006_files_import.sql:114` |
| 11 | Architecture | F13.4: Course-Level Resource Isolation | Ensures attached `FileAsset.course_id == Lesson.course_id`. | Lesson ID, FileAsset ID | Attached link | 400 `FileValidationError("File asset belongs to a different course...")` | `file_service.py:1078` |
| 12 | Architecture | F13.5: Public UUIDv5 Masking (ADR-002) | Exposes synthetic UUIDv5 for `LessonResource` and UUIDv4 for `FileAsset` and `Lesson`. | Resource internal PK | UUID string | Zero `BIGINT` PK leakage | ADR-002, `file_import.py:508` |
| 13 | Student View | F14.1: HTML5 Video Streaming Player | Student lesson stage renders HTML5 `<video controls>` tag with source pointing to download route. | Lesson with attached video asset | Responsive HTML5 video player | Fallback text if browser unsupported | `ORIGINAL_REQUEST.md` §R4, `student/lesson.html:348` |
| 14 | Student View | F14.2: HTTP 206 Partial Content Streaming | Video streaming supports HTTP Range requests for instant scrubbing, seeking, and playback. | `Range: bytes=start-end` HTTP header | 206 Partial Content with `Content-Range` header | 416 Range Not Satisfiable on bad range | Flask `send_file(..., conditional=True)` |
| 15 | Student View | F14.3: Dynamic Learning Resources List (Tab 5) | Tab 5 dynamically displays attached PDF, DOCX, PPTX, and other files with metadata. | `lesson.resources` | Dynamic resource cards with title, size, format badge, download button | Empty state notice if 0 resources | `frontend-preview/assets/js/views/student.js:950`, `student/lesson.html:543` |
| 16 | Security | F-SEC.1: Fail-Closed Malware Scanning | Quarantined, infected, or unscanned files cannot be downloaded or streamed by students. | Student file request | File stream if CLEAN/SAFE | 403 `FileSecurityQuarantineError` / `FileInfectedError` | Invariant 18, `file_service.py:1018` |
| 17 | Security | F-SEC.2: Lesson & Course Publication Gate | Students can only access resources attached to PUBLISHED lessons in PUBLISHED courses. | Student file request | Authorized access | 403 `FileAccessDeniedError` if course or lesson is DRAFT | `file_service.py:958, 984` |
| 18 | Security | F-SEC.3: Active Enrollment Verification | Student must have an ACTIVE enrollment period in the course to download or view lesson media. | Student session + Course ID | Authorized access | 403 `FileAccessDeniedError("You are not actively enrolled...")` | `file_service.py:963` |
| 19 | Security | F-SEC.4: Managing Instructor Authorization | Only course managers (owner instructor or admin) can attach, detach, or modify lesson resources. | Instructor session + Course ID | Authorized access | 403 `ForbiddenError` if foreign instructor | `file_service.py:1071, 1135` |

---

### Edge Cases
| # | Feature | Input | Observed Behavior |
|---|---------|-------|-------------------|
| 1 | F12.4 | Video file size = 1,000,000,000 bytes (exactly 1 GB) | Aborted immediately with `FileSizeLimitExceededError` (413). Invariant 18 strictly mandates `< 1 GB`. |
| 2 | F12.4 | Video file size = 999,999,999 bytes | Accepted, streamed to quarantine, scanned, and activated. |
| 3 | F12.5 | PDF file size = 50,000,001 bytes (> 50 MB) | Rejected with `FileSizeLimitExceededError`. |
| 4 | F12.6 | Uploading PowerPoint Macro-Enabled presentation (`lecture.pptm`) | Rejected with `FileValidationError("File extension '.pptm' is forbidden for security.")`. |
| 5 | F12.6 | Uploading executable or script (`malware.exe`, `script.sh`, `tool.py`) | Rejected with `FileValidationError`. |
| 6 | F12.7 | Uploading filename with directory traversal (`../../../../etc/shadow.pdf`) | Sanitized to `shadow.pdf`. |
| 7 | F13.4 | Instructor attaches FileAsset from Course B to Lesson in Course A | Rejected with `FileValidationError("File asset belongs to a different course than the lesson.")`. |
| 8 | F-SEC.2 | Enrolled student requests resource attached exclusively to a DRAFT lesson | Rejected with 403 `FileAccessDeniedError("The lesson containing this resource is not yet published.")`. |
| 9 | F-SEC.2 | Lesson status changed from DRAFT to PUBLISHED | Student can immediately stream video and download attached resources. |
| 10 | F-SEC.1 | ClamAV scanner unavailable or throws engine error | File remains in `QUARANTINED` status; student request rejected with 403 `FileSecurityQuarantineError` (fail-closed). |
| 11 | F-SEC.1 | ClamAV detects malware in uploaded lecture slides | File marked `REJECTED`, moved to `quarantine/infected`, student request rejected with 403 `FileInfectedError`. |
| 12 | F13.1 | Two lessons in different courses upload the exact same 200 MB lecture video | Hash matches existing `FileBlob`; `reference_count` increments to 2; zero additional disk space consumed. |
| 13 | F13.3 | Attaching multiple resources to the same lesson | Sequential position assignment (`position = max_pos + 1`), preserving unique index `(lesson_id, position)`. |
| 14 | F14.2 | Student video player seeks to minute 15 of 45-minute video | Client sends `Range: bytes=...`; server responds with HTTP 206 and exact byte chunk, avoiding full download. |
| 15 | F14.3 | Lesson has 0 attached resources | Student Tab 5 displays friendly empty-state banner: "Bài học này không có tệp tin đính kèm bổ sung...". |

---

## 4. Caveats
1. **Model Import Order**: `Lesson` is in `src/pwd301/models/course.py` and `LessonResource` is in `src/pwd301/models/file_import.py`. Circular import prevention must be maintained when configuring the `resources` relationship (e.g. using string target `"LessonResource"`).
2. **Video Transcoding / HLS**: The current specification uses direct progressive download / Range requests with standard MP4/WebM files (`conditional=True`). Multi-bitrate HLS/DASH transcoding is intentionally out of scope for Milestone 4 (no ffmpeg background queue required yet).
3. **Frontend Preview Design Fidelity**: The UI in `src/pwd301/templates/student/lesson.html` should match the styling and UX of `frontend-preview/assets/js/views/student.js` (including file icons, badges, size formatting, and download action).

---

## 5. Conclusion
Milestone 4 requires four concrete implementation updates:
1. **Data Model**: Add `resources` relationship to `Lesson` in `src/pwd301/models/course.py` linking to `LessonResource(cascade="all, delete-orphan", order_by="LessonResource.position")`.
2. **Authoring Routes**: Update `POST /courses/<course_id>/lessons` in `instructor/routes.py` to handle multipart file uploads (`media_file`, `resource_files[]`) via `store_file_stream()` and `attach_resource_to_lesson()`, and add a dedicated endpoint to attach/detach resources on existing lessons.
3. **Instructor UI**: Update `newLessonModal` in `course_manage.html` with `enctype="multipart/form-data"` and file inputs for media and supplementary files.
4. **Student UI**: In `student/lesson.html`, replace the static canvas with an HTML5 `<video controls preload="metadata">` player streaming from the student download route when a video resource is attached, and render dynamic resource cards in Tab 5 ("Tài liệu đính kèm") with working download links.

---

## 6. Verification Method

To verify Milestone 4 implementation and test coverage:
1. **Existing Unit & Security Tests**:
   ```powershell
   pytest tests/security/test_file_authorization_idor.py tests/unit/test_file_service.py -v
   ```
2. **New Milestone 4 Test Suite**:
   Create and execute `tests/test_m4_lecture_media.py` validating:
   - Creating a lesson with attached video (< 1 GB) and verifying `LessonResource` creation.
   - Video upload >= 1 GB rejected with 413.
   - Dangerous/macro file upload rejected with 400.
   - Instructor course ownership enforcement (foreign instructor rejected with 403).
   - Cross-course file attachment rejected with `FileValidationError`.
   - Enrolled student video streaming via HTTP Range request returning HTTP 206.
   - Student blocked with 403 when downloading resource from DRAFT lesson.
   - Student blocked with 403 when file is in quarantine or infected.
   - Dynamic rendering of HTML5 video and Tab 5 resources in `student/lesson.html`.
3. **Repository Conformance Check**:
   ```powershell
   python scripts/repo_check.py
   ```
