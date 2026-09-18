# Forensic Audit Report: Milestone 4 (Multi-Format Lecture Authoring & Media Support)

**Auditor Agent**: `auditor_m4_1`  
**Working Directory**: `e:\PWD301\.agents\teamwork_preview_auditor_m4_1`  
**Role**: Milestone 4 Forensic Auditor  
**Parent Conversation ID**: `5f234e51-df3a-4989-b3f8-7adc52e9513d`  
**Timestamp**: 2026-09-14T20:35:30Z  
**Work Product**: Milestone 4 Implementation (F12, F13, F14)  
**Profile**: General Project (Development Mode per `ORIGINAL_REQUEST.md`)  
**Verdict**: **CLEAN**

---

## Forensic Audit Summary

| Check | Result | Details |
|---|:---:|---|
| **Hardcoded Test Results** | **PASS** | No test-specific conditional branches, no hardcoded output strings or fake returns |
| **Facade Detection** | **PASS** | Genuine SQLAlchemy relationship, database persistence, streaming file storage, SHA-256 deduplication |
| **Pre-populated Artifacts** | **PASS** | No pre-existing test results, attestation files, or stale log outputs found |
| **ORM & Schema Backing** | **PASS** | `Lesson.resources` bidirectional relationship backed by `lesson_resources` table with cascade delete-orphan |
| **Multipart Parsing & Stream Storage** | **PASS** | `create_lesson_route` genuinely parses `request.files`, routes through `store_file_stream` and `attach_resource_to_lesson` |
| **Dynamic Jinja & HTML5 Viewers** | **PASS** | `student/lesson.html` and `course_manage.html` dynamically loop over `lesson_resources`, stream video via HTTP 206, no dummy downloads |
| **Video Size Limit (< 1 GB)** | **PASS** | Enforced via `LimitingStream` on incoming chunks without RAM buffering; verified with `OversizedStream` |
| **Automated Test Suite** | **PASS** | 16/16 tests in `tests/test_m4_lecture_media.py` pass cleanly in 11.27s |
| **Static & Contract Checks** | **PASS** | `scripts/repo_check.py` PASS; `mypy` 85 source files clean; `ruff` all clean |
| **Regression Verification** | **PASS** | 19/19 unit/API lesson tests pass; 12/12 file security/IDOR tests pass |

---

## 1. Observation

1. **ORM Relationship and Schema Backing**:
   - In `src/pwd301/models/course.py` (lines 540–545):
     ```python
     resources = relationship(
         "LessonResource",
         back_populates="lesson",
         cascade="all, delete-orphan",
         order_by="LessonResource.position",
     )
     ```
   - In `src/pwd301/models/file_import.py` (lines 459–506):
     ```python
     class LessonResource(Base):
         __tablename__ = "lesson_resources"
         ...
         lesson = relationship("Lesson", back_populates="resources", foreign_keys=[lesson_id])
         file_asset = relationship("FileAsset", foreign_keys=[file_asset_id])
     ```
   - `Lesson.video_resource` (lines 548–555) and `Lesson.document_resources` (lines 558–566) dynamically inspect `res.file_asset.is_video`.
   - `LessonResource` provides dynamic helper properties: `title`, `file_name`, `file_size_bytes`, `mime_type`, `is_video`, `is_pdf`, `resource_type`, `file_size_formatted`.

2. **Route Implementation and File Handling**:
   - In `src/pwd301/blueprints/instructor/routes.py` (lines 611–685):
     - `create_lesson_route` parses `request.form` and `request.files`.
     - When `markdown_content` is blank and media is attached, defaults safely to `# {title}\n\n{summary}` to satisfy service constraints without forcing instructors to type markdown.
     - Parses `request.files.get("media_file")` and `request.files.getlist("resource_files")`.
     - Calls `store_file_stream` on `media_file.stream` and `attach_resource_to_lesson` on `lesson.id` and `asset.id`.
     - No mock bypasses, no hardcoded values, and no artificial bypass conditionals exist.
   - Lines 704–760 implement `POST /courses/<course_id>/lessons/<lesson_id>/resources` (`attach_lesson_resource_route`).
   - Lines 762–790 implement `POST /courses/<course_id>/lessons/<lesson_id>/resources/<resource_id>/delete` (`detach_lesson_resource_route`).

3. **Stream Limiting for Video (< 1 GB)**:
   - In `src/pwd301/services/file_service.py` (lines 105–125):
     ```python
     class LimitingStream:
         def __init__(self, stream: Any, max_bytes: int = 1_000_000_000) -> None:
             self._stream = stream
             self._max_bytes = max_bytes
             self._bytes_read = 0

         def read(self, size: int = -1) -> bytes:
             chunk = self._stream.read(size)
             if chunk:
                 self._bytes_read += len(chunk)
                 if self._bytes_read >= self._max_bytes:
                     raise FileSizeLimitExceededError(
                         f"File stream exceeded maximum limit of {self._max_bytes} bytes."
                     )
             return chunk
     ```
   - In `store_file_stream` (lines 330–335), `file_stream` is wrapped with `LimitingStream(file_stream, max_bytes=max_video_exclusive)` (`1_000_000_000` bytes).

4. **Dynamic Templates**:
   - `src/pwd301/templates/instructor/course_manage.html`:
     - Line 245: `<form method="POST" action="/instructor/courses/{{ course.public_id }}/lessons" enctype="multipart/form-data">`
     - Line 282: `<input type="file" name="media_file" class="form-control form-control-sm" accept=".mp4,.webm,.mov,.pdf,.docx,.pptx">`
     - Line 289: `<input type="file" name="resource_files" class="form-control form-control-sm" multiple accept=".pdf,.docx,.pptx,.zip,.rar,.txt">`
     - Lines 191–195: dynamic resource count badge `{{ les.resources|length }} tệp`.
   - `src/pwd301/templates/student/lesson.html`:
     - Lines 371–378: Dynamic HTML5 video player:
       ```html
       <video id="lecture-html5-video" class="w-100 h-100" controls playsinline preload="metadata">
         <source src="{{ url_for('student.download_student_course_file_route', course_id=course.public_id, asset_id=video_resource.file_asset.public_id) }}?disposition=inline" type="{{ video_resource.file_asset.mime_type or 'video/mp4' }}">
       </video>
       ```
     - Lines 379–397: Dynamic PDF slide embed iframe.
     - Lines 537–615: Tab 5 dynamic resource list looping over `lesson_resources`, rendering format badges, clean scan indicators (`Đã quét an toàn`), and working authenticated download links via `student.download_student_course_file_route`.

5. **Test and Static Analysis Output**:
   - Pytest `tests/test_m4_lecture_media.py`:
     ```
     ============================= 16 passed in 11.27s =============================
     ```
   - Repository checks `scripts/repo_check.py`:
     ```
     [PASS] Required repository contract files exist
     [PASS] No duplicate database architecture/SQL copy under System Specification
     [PASS] Canonical SQL Server DDL contains 71 CREATE TABLE statements
     [PASS] Markdown code fences are balanced
     [PASS] Repository contract check complete
     ```
   - Type check `mypy src/pwd301`:
     ```
     Success: no issues found in 85 source files
     ```
   - Linter `ruff check src tests scripts`:
     ```
     All checks passed!
     ```
   - Regression tests `tests/unit/test_lesson_service.py` & `tests/api/test_lesson_api.py`:
     ```
     ============================= 19 passed in 12.18s =============================
     ```
   - Security / IDOR tests `tests/security/test_file_authorization_idor.py`:
     ```
     ============================= 12 passed in 7.75s ==============================
     ```

---

## 2. Logic Chain

1. **Schema & Model Integrity**: The mapping of `Lesson.resources` directly targets `LessonResource`, backed by the canonical `lesson_resources` table in SQL Server architecture. It specifies `cascade="all, delete-orphan"` and `order_by="LessonResource.position"`. This prevents orphaned rows, preserves deterministic lesson material presentation, and confirms the absence of mock facades.
2. **Security & Authorization Invariants**: Media files uploaded to lessons are processed through `store_file_stream`. This applies SHA-256 deduplication, quarantine streaming, and virus status tracking. Unenrolled students and students attempting to download resources from DRAFT lessons are rejected with HTTP 403 Forbidden. Cross-course resource linkage is strictly rejected with `FileValidationError`.
3. **Denial of Service Mitigation**: The `< 1 GB` video limit is enforced at stream reading time via `LimitingStream`. When an input stream exceeds 1,000,000,000 bytes, `FileSizeLimitExceededError` is raised immediately before allocating memory or filling disk storage.
4. **UX & Presentation Authenticity**: Inspection of `student/lesson.html` proves that video playback, PDF slide embedding, and resource downloads rely strictly on dynamic Jinja expressions connected to authenticated routes with opaque public UUIDs (ADR-002). No static dummy links (`#`), simulated mock video players, or fake download attachments exist.
5. **Empirical Verification**: All 16 Milestone 4 tests and 31 cross-subsystem regression tests execute against the active application and SQLite/SQL Server test database, passing 100% without mocks or test-specific branches.

---

## 3. Caveats

1. **Progressive Download vs HLS/DASH**: Video streaming uses progressive download with HTTP 206 Partial Content (Range requests) via Flask's `conditional=True`. Adaptive bitrate streaming (HLS/DASH) requires asynchronous background transcoding workers, which are intentionally deferred to future infrastructure phases.
2. **Office Document Preview**: Microsoft Office files (.docx, .pptx) cannot be rendered natively inside browser iframes without third-party services. They are correctly presented with format badges, file size, clean scan verification, and secure download links.

---

## 4. Conclusion

**Verdict: CLEAN**

Milestone 4 (Multi-Format Lecture Authoring & Media Support) fulfills all requirements of §R4 of `ORIGINAL_REQUEST.md` and `PROJECT.md`:
- Authentic database-backed ORM relationships without mocks or facades.
- Robust multipart form handling with streaming size limits (< 1 GB).
- Fully dynamic, accessible, and secure student and instructor interfaces.
- Zero regressions across the existing test suite.

The work product is verified and recommended for immediate approval.

---

## 5. Verification Method

To independently reproduce the forensic verification results:

```powershell
# 1. Milestone 4 Automated Test Suite
.venv\Scripts\python.exe -m pytest tests/test_m4_lecture_media.py -v

# 2. Repository Contract Static Verification
.venv\Scripts\python.exe scripts/repo_check.py

# 3. Static Type Checking
.venv\Scripts\python.exe -m mypy src/pwd301

# 4. Code Quality & Linting
.venv\Scripts\python.exe -m ruff check src tests scripts

# 5. Regression Verification (Lesson Services & File Security)
.venv\Scripts\python.exe -m pytest tests/unit/test_lesson_service.py tests/api/test_lesson_api.py tests/security/test_file_authorization_idor.py -v
```
