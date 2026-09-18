# Milestone 4 Backend & Data Contract Review Report (R4)

**Agent ID**: `reviewer_m4_1`  
**Working Directory**: `e:\PWD301\.agents\teamwork_preview_reviewer_m4_1`  
**Role**: Milestone 4 Backend & Data Contract Reviewer  
**Parent Conversation ID**: `5f234e51-df3a-4989-b3f8-7adc52e9513d`  
**Timestamp**: 2026-09-14T20:36:00Z  
**Verdict**: **APPROVE**  

---

## 1. Observation

1. **Model Synchronization & Relationships**:
   - `src/pwd301/models/course.py` (lines 540–566):
     ```python
     resources = relationship(
         "LessonResource",
         back_populates="lesson",
         cascade="all, delete-orphan",
         order_by="LessonResource.position",
     )

     @property
     def video_resource(self) -> LessonResource | None:
         """Return the primary attached video resource if one exists."""
         if not hasattr(self, "resources") or not self.resources:
             return None
         for res in self.resources:
             if getattr(res, "file_asset", None) and getattr(res.file_asset, "is_video", False):
                 return res
         return None

     @property
     def document_resources(self) -> list[LessonResource]:
         """Return attached document and supplementary resources (non-video)."""
         if not hasattr(self, "resources") or not self.resources:
             return []
         return [
             res
             for res in self.resources
             if getattr(res, "file_asset", None) and not getattr(res.file_asset, "is_video", False)
         ]
     ```
   - `src/pwd301/models/file_import.py` (lines 505–580):
     `LessonResource.lesson` establishes `relationship("Lesson", back_populates="resources", foreign_keys=[lesson_id])`.
     Added properties: `title`, `file_name`, `file_size_bytes`, `mime_type`, `is_video`, `is_pdf`, `resource_type`, `file_size_formatted`, and `public_id` generating ADR-002 compliant synthetic UUIDv5 (`uuid.uuid5(uuid.NAMESPACE_DNS, f"pwd301.lesson_resource.{self.id}")`). All properties safely handle `self.file_asset is None` without throwing exceptions.

2. **Instructor Route & Multipart Authoring**:
   - `src/pwd301/blueprints/instructor/routes.py` (lines 588–608): `_serialize_lesson` serializes resources with `[_serialize_lesson_resource(r) for r in les.resources]`.
   - `src/pwd301/blueprints/instructor/routes.py` (lines 611–701): `create_lesson_route` parses multipart files (`media_file`, `resource_files[]`, `resource_file`, `file`), defaults `markdown_content` to `# {title}\n\n{summary}` when blank and media is attached (eliminating mandatory manual typing), calls `store_file_stream`, and attaches resources via `attach_resource_to_lesson`.
   - `src/pwd301/blueprints/instructor/routes.py` (lines 704–782): Added `attach_lesson_resource_route` (`POST /courses/<course_id>/lessons/<lesson_id>/resources`) and `detach_lesson_resource_route` (`POST /courses/<course_id>/lessons/<lesson_id>/resources/<resource_id>/delete`), enforcing course ownership and returning sanitized flash or JSON responses.

3. **Student Route & Streaming Access**:
   - `src/pwd301/blueprints/student/routes.py` (lines 249–277): `_serialize_student_lesson` securely filters resources, only exposing those with `r.file_asset.status == "ACTIVE"` and `r.file_asset.virus_scan_status == "CLEAN"`.
   - `src/pwd301/blueprints/student/routes.py` (lines 280–360): `get_student_lesson_route` resolves `all_lessons`, `lesson_resources`, `video_resource`, and `doc_resource`, and passes them to `student/lesson.html`.
   - `src/pwd301/blueprints/student/routes.py` (lines 1334–1368): `download_student_course_file_route` calls `get_file_for_download` enforcing active enrollment, published lesson/course state, clean scan status, and serves via `send_file(..., conditional=True)` supporting HTTP 206 Partial Content range requests.

4. **Automated Verification Results (Independently Executed)**:
   - Command: `.venv\Scripts\python.exe -m pytest tests/test_m4_lecture_media.py -v`
     - Result: `16 passed in 11.09s`
   - Command: `.venv\Scripts\python.exe -m pytest tests/unit/test_lesson_service.py tests/api/test_lesson_api.py -v`
     - Result: `19 passed in 12.39s`
   - Command: `.venv\Scripts\python.exe -m ruff check src tests scripts`
     - Result: `All checks passed!`
   - Command: `.venv\Scripts\python.exe -m mypy src/pwd301`
     - Result: `Success: no issues found in 85 source files`
   - Command: `.venv\Scripts\python.exe scripts/repo_check.py`
     - Result: `[PASS] Repository contract check complete`

5. **Adversarial Security & Integrity Checks**:
   - `test_video_file_size_limit_enforcement`: Verified strict `< 1 GB` limit using `LimitingStream`; 1,000,000,000 bytes immediately raises `FileSizeLimitExceededError`.
   - `test_cross_course_resource_attachment_blocked`: Verified that attempting to attach a file from Course B to Course A raises `FileValidationError("File asset belongs to a different course than the lesson.")`.
   - `test_foreign_instructor_cannot_attach_or_detach_resource`: Verified IDOR protection with 403 Forbidden.
   - `test_fail_closed_security_unenrolled_student_blocked`: Verified 403 Forbidden for unenrolled students.
   - `test_fail_closed_security_draft_lesson_resource_blocked`: Verified 403 Forbidden when accessing resources on draft lessons.
   - `test_student_video_streaming_conditional_range`: Verified HTTP 206 Partial Content with `Range: bytes=0-100` and `Content-Range: bytes 0-100/4128`.
   - Zero hardcoded mock returns or facade implementations detected in source code.

---

## 2. Logic Chain

1. **Model Integrity**: `Lesson` and `LessonResource` previously lacked bidirectional synchronization (`back_populates`). Establishing `resources = relationship("LessonResource", back_populates="lesson", cascade="all, delete-orphan", order_by="LessonResource.position")` on `Lesson` and `lesson = relationship("Lesson", back_populates="resources")` on `LessonResource` allows clean navigation while enforcing `cascade="all, delete-orphan"` so orphaned resource join records are cleaned up when a lesson is deleted. `FileAsset` is referenced via `ForeignKey("file_assets.id", ondelete="RESTRICT")`, ensuring underlying file records are preserved in accordance with PWD301 invariants against broad cascade deletes.
2. **Authoring Ergonomics & Service Invariants**: Core validation in `create_lesson` requires non-empty `markdown_content`. By generating a clean fallback `# {title}\n\n{summary}` when `markdown_content` is omitted, the web route allows instructors to upload media without being blocked by service validation, satisfying Requirement R4 without compromising lower-level data constraints.
3. **Fail-Closed File Access (Invariant 18 & FILE-005)**: The download route `download_student_course_file_route` invokes `get_file_for_download`, which enforces the zero-trust authorization matrix: active actor, active enrollment in published course, published lesson status, clean scan status (`CLEAN`/`SAFE`), and rejection of `QUARANTINED`/`INFECTED` files with 403 Forbidden.
4. **HTML5 Streaming Readiness**: Serving media files with `send_file(..., conditional=True)` natively parses HTTP `Range` headers and returns HTTP 206 Partial Content, enabling standard browser HTML5 video scrub/seek operations without requiring specialized streaming daemons.

---

## 3. Caveats

1. **Adaptive Bitrate Streaming (HLS/DASH)**: Progressive download with HTTP 206 Partial Content is used for video playback. Transcoding to multi-bitrate HLS/DASH playlists is intentionally not implemented in this phase, consistent with scope discipline and PROJECT.md guidelines.
2. **Defensive UI on Quarantined Video**: If an attached video is in `QUARANTINED` status, the route passes it to `lesson.html` as `video_resource`, but the `<source>` stream request fails closed with HTTP 403. Tab 5 displays the status badge (`Đã cách ly`), but the video player frame remains black/unplayable. This is safe and compliant with fail-closed security, though in future UI polish a warning banner inside the video canvas could inform the student directly.

---

## 4. Conclusion

The Milestone 4 backend implementation and data contracts (F12, F13, F14) meet all acceptance criteria, maintain strict compliance with PWD301 security invariants, pass all unit, integration, and regression tests, and show zero integrity violations.

**Verdict**: **APPROVE**

---

## 5. Verification Method

To independently verify this assessment, execute the following commands in order:

```powershell
# 1. Milestone 4 Media Test Suite
.venv\Scripts\python.exe -m pytest tests/test_m4_lecture_media.py -v

# 2. Regression Lesson Services and API Suite
.venv\Scripts\python.exe -m pytest tests/unit/test_lesson_service.py tests/api/test_lesson_api.py -v

# 3. Static Quality & Type Checks
.venv\Scripts\python.exe -m ruff check src tests scripts
.venv\Scripts\python.exe -m mypy src/pwd301
.venv\Scripts\python.exe scripts/repo_check.py
```

*Invalidation Conditions*: Any failing test in `test_m4_lecture_media.py`, regression failure in `test_lesson_service.py` or `test_lesson_api.py`, type errors in `mypy`, or any leak of internal primary keys in REST API / templates.
