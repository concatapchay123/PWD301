# Handoff Report: R1 & R4 Investigation & Remediation Architecture
**Author**: Survey Explorer 1 (`teamwork_preview_explorer`)  
**Working Directory**: `e:\PWD301\.agents\teamwork_preview_explorer_survey_1`  
**Date**: 2026-09-13T22:42:00Z  
**Target Subsystems**:
- **R1**: File Upload, Virus Scanning & Secure Access Remediation
- **R4**: Multi-Format Lecture Authoring & Media Support

---

## 1. Observation

### 1.1 R1: File Asset Rendering Defect in Web UI
In `src/pwd301/templates/instructor/course_manage.html` (lines 370–397), the file listing table renders rows iterating over `file_assets`:
```html
370: <tr>
371:   <td>
372:     <div class="fw-bold text-slate-900">{{ fa.original_file_name or fa.file_name }}</div>
373:     <small class="text-muted">UUID: {{ fa.public_id }}</small>
374:   </td>
375:   <td>
376:     {% if fa.file_size_bytes %}
377:       {{ (fa.file_size_bytes / 1024 / 1024) | round(2) }} MB
378:     {% else %}
379:       —
380:     {% endif %}
381:   </td>
382:   <td><span class="badge bg-light text-dark border">{{ fa.mime_type or 'file' }}</span></td>
383:   <td>
384:     {% if fa.virus_scan_status == 'CLEAN' %}
385:       <span class="badge bg-success-subtle text-success border border-success-subtle">CLEAN (Đã quét an toàn)</span>
386:     {% elif fa.virus_scan_status == 'INFECTED' %}
387:       <span class="badge bg-danger-subtle text-danger border border-danger-subtle">INFECTED (Đã cách ly)</span>
388:     {% else %}
389:       <span class="badge bg-warning-subtle text-warning border border-warning-subtle">{{ fa.virus_scan_status or 'PENDING' }}</span>
390:     {% endif %}
391:   </td>
```
In `src/pwd301/blueprints/instructor/routes.py` (lines 289–293, 316–324):
```python
289:     file_assets = (
290:         db.session.query(FileAsset)
291:         .filter(FileAsset.course_id == course.id, FileAsset.deleted_at.is_(None))
292:         .order_by(FileAsset.created_at.desc())
293:         .all()
294:     )
...
316:     return render_template(
317:         "instructor/course_manage.html",
318:         course=course,
319:         lessons=lessons,
320:         file_assets=file_assets,
321:         assessments=assessments,
322:         questions_count=questions_count,
323:         active_tab=active_tab,
324:     )
```
In `src/pwd301/models/file_import.py` (lines 107–217), inspecting the `FileAsset` class definition reveals:
- Columns: `id`, `public_id`, `course_id`, `created_by_user_id`, `asset_type`, `display_name`, `status`, `retention_until`, `created_at`, `updated_at`, `row_version`, `deleted_at`, `restore_until`, `deleted_by_user_id`.
- Properties: Only `@property def filename(self) -> str: return self.display_name` and `@property def owner_id(self) -> int: return self.created_by_user_id`.
- Missing attributes on `FileAsset`: `original_file_name`, `file_name`, `file_size_bytes`, `mime_type`, and `virus_scan_status` DO NOT EXIST on the `FileAsset` model! They reside on the child `FileRevision` model (`original_filename`, `size_bytes`, `detected_mime_type`) or in `FileScanResult`.

### 1.2 R1: Why Uploaded Files Get Stuck in `PENDING` Status
1. **False Impression via Template Attribute Miss**: As shown in observation 1.1, because `fa.virus_scan_status` is always `None` on `FileAsset`, Jinja evaluates `{{ fa.virus_scan_status or 'PENDING' }}` at line 389 and outputs `PENDING` for EVERY uploaded file, even when `FileAsset.status == 'ACTIVE'` and `FileRevision.status == 'ACTIVE'`.
2. **Scanner Disconnect & Background Job Omission**:
   In `src/pwd301/services/file_service.py` (lines 537–582):
   ```python
   537:         else:
   538:             # Scanner error or timeout: fail-closed quarantine
   539:             asset = FileAsset(
   540:                 course_id=course.id,
   541:                 created_by_user_id=actor.id,
   542:                 asset_type=chosen_type,
   543:                 display_name=title or clean_filename,
   544:                 status="PENDING",
   545:             )
   ...
   558:                 status="QUARANTINED",
   559:                 quarantine_key=f"quarantine/{temp_filename}",
   560:                 rejection_reason=f"Scanner error: {main_verdict.details or 'Unavailable'}",
   ...
   581:             sess.commit()
   582:             return asset
   ```
   In `src/pwd301/services/background_job_service.py` (lines 276–287):
   ```python
   276:         elif job.job_type == "FILE_SCAN":
   277:             from pwd301.services.file_service import rescan_file_asset
   278: 
   279:             asset_id = payload.get("asset_id")
   280:             user_id = payload.get("user_id")
   281:             if asset_id and user_id:
   282:                 from pwd301.models.identity import User
   283: 
   284:                 actor = sess.get(User, user_id)
   285:                 if actor:
   286:                     rescan_file_asset(actor=actor, asset_id=asset_id, session=sess)
   ```
   Grepping for `FILE_SCAN` across the repository confirms: `enqueue_background_job` is NEVER called with `job_type="FILE_SCAN"` anywhere during or after file upload in `file_service.py` or route handlers!
   Furthermore, there is NO Web UI rescan route (`POST /instructor/courses/<course_id>/files/<asset_id>/rescan`). The only rescan route is `POST /api/files/<asset_id>/rescan` which requires JWT Bearer auth.

### 1.3 R1: 403 Forbidden on Web Session File Downloads
In `src/pwd301/blueprints/instructor/routes.py` (lines 689–695):
```python
689: @instructor_bp.route("/courses/<course_id>/files/<asset_id>/download", methods=["GET"])
690: @instructor_required
691: def download_course_file_route(course_id: str, asset_id: str) -> Any:
692:     """Download a course file asset."""
693:     actor = require_authenticated_actor()
694:     require_course_manager(actor, course_id, session=db.session)
695:     return redirect(url_for("api_files.download_file_api", asset_id=asset_id))
```
In `src/pwd301/blueprints/api_files/routes.py` (lines 46–61):
```python
46: @api_file_bp.route("/<asset_id>/download", methods=["GET"])
47: def download_file_api(asset_id: str) -> Response:
...
56:     actor = get_authenticated_actor()
...
59:     asset, blob, physical_path = get_file_for_download(
60:         actor, asset_id, revision_no=revision_no, session=db.session
61:     )
```
In `src/pwd301/services/authorization_service.py` (lines 102–107):
```python
102:     # 3. Web session authentication context
103:     # Invariant: Web session cookies must NEVER authenticate requests to CSRF-exempt
104:     # API endpoints (/api/*) to prevent Cross-Site Request Forgery (CSRF).
105:     # REST API clients must supply Bearer JWT.
106:     if has_request_context() and (request.path == "/api" or request.path.startswith("/api/")):
107:         return None
```
In `src/pwd301/services/file_service.py` (lines 926–927):
```python
926:     if actor is None or not actor.is_active:
927:         raise FileAccessDeniedError("Authentication required to download this file.")
```
In `src/pwd301/blueprints/student/routes.py`:
Grep search reveals zero download routes for students (`@student_bp.route("/courses/<course_id>/files/...")` does not exist).
Specification `docs/system/PWD301_SYSTEM_SPECIFICATION/api/09_FILE_IMPORT_API.md` explicitly states:
```markdown
### `GET /api/files/{file_id}/download`
- **Purpose:** Authorized file download
- **Authentication:** Session/JWT
- **Authorization:** Authorized resource viewer
```

### 1.4 R4: Lecture Authoring Media Support & Schema Gaps
In `src/pwd301/templates/instructor/course_manage.html` (`newLessonModal`, lines 234–275):
The form has fields for `title`, `estimated_duration_minutes`, `position`, `summary`, and `markdown_content` (`<textarea required>`). It contains NO `<input type="file">` for uploading PDF, DOCX, PPTX, or Video.
In `src/pwd301/blueprints/instructor/routes.py` (`create_lesson_route`, lines 563–591):
The endpoint only processes form strings (`request.form.to_dict()`) and passes them to `create_lesson()`. It does not inspect `request.files` or link files.
In `src/pwd301/services/lesson_service.py` (lines 154–162):
```python
154:     # Validate markdown_content
155:     markdown_content = data.get("markdown_content")
156:     if (
157:         not markdown_content
158:         or not isinstance(markdown_content, str)
159:         or not markdown_content.strip()
160:     ):
161:         raise LessonValidationError("Lesson markdown_content is required and cannot be empty.")
```
In `src/pwd301/models/course.py` (lines 392–515):
`Lesson` has relationships: `course`, `change_request`, `deleted_by`.
It has NO relationship to `LessonResource`!
In `src/pwd301/models/file_import.py` (lines 361–414):
`LessonResource` has:
`lesson = relationship("Lesson", foreign_keys=[lesson_id])`
`file_asset = relationship("FileAsset", foreign_keys=[file_asset_id])`

### 1.5 R4: Student Lecture Viewers & Resource Presentation
In `src/pwd301/templates/student/lesson.html`:
- Video Stage (lines 348–383): Contains a static container `<div class="udemy-video-stage" id="udemy-video-canvas">` with an overlay text `Trình phát bài giảng Full HD 1080p • Thời lượng ước tính: ...` and button `togglePlayState()`. It has NO `<video>` element, NO `<source>` tag, and cannot play any uploaded MP4 or WebM video.
- Tab 5 "Tài liệu đính kèm" (lines 544–570):
```html
548: <div class="list-group list-group-flush border rounded-3">
549:   <div class="list-group-item d-flex justify-content-between align-items-center p-3">
...
552:     <div class="fw-semibold text-slate-900" style="font-size: 14px;">Slide bài giảng: {{ lesson.title }}</div>
553:     <div class="text-caption text-muted">2.4 MB • Giáo trình chính khóa</div>
...
556:     <button type="button" class="btn btn-outline-secondary btn-sm px-3" onclick="alert('Đang chuẩn bị tệp tin tải xuống...')">Tải xuống ↓</button>
...
```
Tab 5 renders static hardcoded dummy data with `onclick="alert(...)"` instead of querying and listing the real resources attached to the lesson.
In `src/pwd301/blueprints/student/routes.py` (lines 253–284):
`get_student_lesson_route` passes `course`, `lesson`, `progress`, `all_lessons` to `student/lesson.html`. It never queries or passes `resources`.

---

## 2. Logic Chain

### 2.1 Why Files Appear Stuck in `PENDING` and Fail to Download
1. Observation 1.1 demonstrates that `course_manage.html` queries properties `original_file_name`, `file_size_bytes`, `mime_type`, and `virus_scan_status` directly from `FileAsset`.
2. Observation 1.1 demonstrates that `FileAsset` does not define these properties.
3. Therefore, Jinja falls back to `'PENDING'` for scan status, `—` for file size, and `'file'` for MIME type, creating a false-positive defect where all clean, active files appear permanently pending.
4. Observation 1.2 demonstrates that in actual scanner failure or timeout situations, `store_file_stream` sets `FileAsset.status = 'PENDING'` and `FileRevision.status = 'QUARANTINED'` but never enqueues a `FILE_SCAN` background job.
5. Therefore, un-scanned files stay quarantined with zero automatic recovery attempts.
6. Observation 1.3 demonstrates that when an Instructor clicks "Tải về", `download_course_file_route` redirects the browser to `/api/files/<asset_id>/download`.
7. Observation 1.3 demonstrates that `authorization_service.py` unconditionally forces `get_authenticated_actor()` to return `None` whenever `request.path.startswith("/api/")` for session-authenticated requests.
8. Observation 1.3 demonstrates that `get_file_for_download` raises `FileAccessDeniedError` (403 Forbidden) when `actor is None`.
9. Therefore, redirecting session users to `/api/files/<asset_id>/download` deterministically causes HTTP 403 Forbidden.
10. Furthermore, students have no download route in `student/routes.py` at all.

### 2.2 Why Multi-Format Lecture Media Cannot Be Authored or Viewed
1. Observation 1.4 demonstrates that `Lesson` model lacks a `resources` relationship to `LessonResource`.
2. Observation 1.4 demonstrates that `lesson_service.create_lesson` strictly enforces `markdown_content` to be non-empty string, preventing media-first lessons (e.g. video-only or slide-only lectures).
3. Observation 1.4 demonstrates that `newLessonModal` in `course_manage.html` and `create_lesson_route` in `instructor/routes.py` have no handling for multipart file uploads.
4. Observation 1.5 demonstrates that `student/lesson.html` has no HTML5 `<video>` element, no embedded document viewer, and uses hardcoded mock strings in the resources tab.
5. Observation 1.5 demonstrates that `student/routes.py` never passes `resources` to `student/lesson.html`.
6. Therefore, even if an instructor uploads a file and associates it with a lesson in the materials tab, the student cannot see it, stream it, or download it from the lesson viewer.

---

## 3. Caveats
- No changes should be made directly to production files during this survey phase (read-only investigation).
- Production ClamAV daemon is optional in development environments; the fallback heuristic scanner (`BuiltinHeuristicScanner`) handles standard test malware and header checks. In production with ClamAV enabled, the background job worker must be running (`python -m pwd301 worker` or similar runner) to process deferred `FILE_SCAN` jobs.
- Video file streaming requires HTTP Range header support (`206 Partial Content`), which Flask's `send_file(..., conditional=True)` provides natively when given a physical file path.

---

## 4. Conclusion & Concrete Remediation Architecture

### 4.1 Exact Schema and Model Capabilities (Fields Available vs Needed)

#### `FileAsset` (`src/pwd301/models/file_import.py`)
- **Available**: `id`, `public_id`, `course_id`, `created_by_user_id`, `asset_type`, `display_name`, `status`, `created_at`, `updated_at`, `deleted_at`, `current_revision`, `revisions`.
- **Needed Properties to Add**:
  - `@property def original_filename(self) -> str`: Returns `self.current_revision.original_filename if self.current_revision else self.display_name`.
  - `@property def original_file_name(self) -> str`: Alias for `original_filename`.
  - `@property def file_name(self) -> str`: Alias for `display_name`.
  - `@property def size_bytes(self) -> int`: Returns `self.current_revision.size_bytes if self.current_revision else 0`.
  - `@property def file_size_bytes(self) -> int`: Alias for `size_bytes`.
  - `@property def mime_type(self) -> str`: Returns `self.current_revision.detected_mime_type or self.current_revision.declared_mime_type if self.current_revision else 'application/octet-stream'`.
  - `@property def detected_mime_type(self) -> str`: Alias for `mime_type`.
  - `@property def virus_scan_status(self) -> str`:
    - Returns `'CLEAN'` if `self.status == 'ACTIVE'` or `(self.current_revision and self.current_revision.status == 'ACTIVE')`.
    - Returns `'INFECTED'` if `self.status == 'REJECTED'` or `(self.current_revision and self.current_revision.status == 'REJECTED')`.
    - Returns `'PENDING'` if `self.status == 'PENDING'` or `(self.current_revision and self.current_revision.status == 'QUARANTINED')`.
    - Returns `'BLOCKED'` if scan results contain `ERROR`.
  - `@property def is_video(self) -> bool`: Checks if `mime_type.startswith('video/')` or extension in `VIDEO_EXTENSIONS`.
  - `@property def is_pdf(self) -> bool`: Checks if `mime_type == 'application/pdf'` or extension == `'.pdf'`.

#### `Lesson` (`src/pwd301/models/course.py`)
- **Available**: `id`, `public_id`, `course_id`, `title`, `summary`, `markdown_content`, `position`, `estimated_duration_minutes`, `status`, `course`.
- **Needed Relationship to Add**:
  ```python
  resources = relationship(
      "LessonResource",
      foreign_keys="LessonResource.lesson_id",
      back_populates="lesson",
      cascade="all, delete-orphan",
      order_by="LessonResource.position",
  )
  ```
- **In `LessonResource` (`src/pwd301/models/file_import.py`)**:
  Ensure back-population:
  ```python
  lesson = relationship("Lesson", foreign_keys=[lesson_id], back_populates="resources")
  ```

---

### 4.2 Exact File Changes, Routes, Services, and Templates Needed

#### 1. `src/pwd301/services/authorization_service.py`
- **Location**: Lines 102–108 in `get_authenticated_actor()`.
- **Change**: Allow safe GET downloads on `/api/files/<asset_id>/download` to authenticate via Web session cookie:
  ```python
  is_safe_file_download = (
      request.method == "GET"
      and request.path.startswith("/api/files/")
      and request.path.endswith("/download")
  )
  if (
      has_request_context()
      and (request.path == "/api" or request.path.startswith("/api/"))
      and not is_safe_file_download
  ):
      return None
  ```
- **Rationale**: Completely complies with ADR-002 and `09_FILE_IMPORT_API.md` ("Authentication: Session/JWT") while strictly preserving anti-CSRF isolation on all state-changing `/api/*` routes.

#### 2. `src/pwd301/services/file_service.py`
- **Location 1**: In `store_file_stream` (lines 538–582).
  - When scanner error occurs and file is placed in `PENDING` / `QUARANTINED`, enqueue a `FILE_SCAN` background job:
    ```python
    from pwd301.services.background_job_service import enqueue_background_job
    enqueue_background_job(
        job_type="FILE_SCAN",
        payload={"asset_id": asset.id, "user_id": actor.id},
        session=sess,
    )
    ```
- **Location 2**: In `rescan_file_asset` (lines 1219–1330).
  - Ensure rescan handles heuristic scanner fallback cleanly when ClamAV is offline.
  - Return updated `FileAsset` with refreshed status (`ACTIVE` if clean, `REJECTED` if malware).

#### 3. `src/pwd301/services/lesson_service.py`
- **Location**: In `create_lesson` (lines 154–163).
  - Relax strict `markdown_content` requirement: If `markdown_content` is blank, default to an introductory summary `# {title}\n\n{summary or 'Nội dung bài học'}` when media or slides are attached.
  - Add helper function `attach_media_to_lesson(...)` or support `media_file` in lesson creation pipeline.

#### 4. `src/pwd301/blueprints/instructor/routes.py`
- **Fix 1 — Download Route**: Replace redirect with direct streaming in `download_course_file_route` (lines 689–696):
  ```python
  @instructor_bp.route("/courses/<course_id>/files/<asset_id>/download", methods=["GET"])
  @instructor_required
  def download_course_file_route(course_id: str, asset_id: str) -> Any:
      actor = require_authenticated_actor()
      asset, blob, physical_path = get_file_for_download(actor, asset_id, session=db.session)
      disposition = request.args.get("disposition", "attachment").lower()
      clean_filename = sanitize_filename(asset.original_filename or asset.display_name)
      return send_file(
          physical_path,
          mimetype=blob.detected_mime_type,
          as_attachment=(disposition == "attachment"),
          download_name=clean_filename,
          conditional=True,
      )
  ```
- **Fix 2 — Rescan Route**: Add `@instructor_bp.route("/courses/<course_id>/files/<asset_id>/rescan", methods=["POST"])` calling `rescan_file_asset(actor, asset_id)` and redirecting to materials tab with flash message.
- **Fix 3 — Lesson Media Attachment**: In `create_lesson_route` (lines 563–591), handle `request.files.get("media_file")`:
  If present, store stream using `store_file_stream`, then attach to lesson using `attach_resource_to_lesson`.
- **Fix 4 — Resource Management Routes**:
  - `POST /lessons/<lesson_id>/resources`: Attach file to lesson.
  - `POST /lessons/<lesson_id>/resources/<resource_id>/delete`: Detach resource.

#### 5. `src/pwd301/blueprints/student/routes.py`
- **Fix 1 — Student File Download Route**:
  ```python
  @student_bp.route("/courses/<course_id>/files/<asset_id>/download", methods=["GET"])
  @student_bp.route("/files/<asset_id>/download", methods=["GET"])
  @student_required
  def download_student_course_file_route(asset_id: str, course_id: str | None = None) -> Any:
      actor = require_authenticated_actor()
      asset, blob, physical_path = get_file_for_download(actor, asset_id, session=db.session)
      disposition = request.args.get("disposition", "attachment").lower()
      clean_filename = sanitize_filename(asset.original_filename or asset.display_name)
      return send_file(
          physical_path,
          mimetype=blob.detected_mime_type,
          as_attachment=(disposition == "attachment"),
          download_name=clean_filename,
          conditional=True,
      )
  ```
- **Fix 2 — Pass Resources in Lesson View**: In `get_student_lesson_route` (lines 253–285):
  Query active lesson resources:
  ```python
  resources = (
      sess.query(LessonResource)
      .join(FileAsset)
      .filter(
          LessonResource.lesson_id == lesson.id,
          FileAsset.status == "ACTIVE",
          FileAsset.deleted_at.is_(None),
      )
      .order_by(LessonResource.position.asc())
      .all()
  )
  video_resource = next((r for r in resources if r.file_asset and r.file_asset.is_video), None)
  doc_resources = [r for r in resources if r != video_resource]
  ```
  Pass `resources=resources`, `video_resource=video_resource`, `doc_resources=doc_resources` to `student/lesson.html`.

#### 6. `src/pwd301/templates/instructor/course_manage.html`
- **Materials Tab**:
  - Fix table columns (lines 370–397): Use `fa.original_filename or fa.display_name`, `fa.file_size_bytes`, `fa.mime_type`, and `fa.virus_scan_status`.
  - Display badge: `CLEAN (Đã quét an toàn)` for `CLEAN`, `INFECTED (Đã cách ly)` for `INFECTED`, `PENDING (Đang chờ quét)` for `PENDING`.
  - Add "Quét lại" (Rescan) button for files in `PENDING` status.
- **Curriculum Tab (`newLessonModal`)**:
  - Add file upload input `<input type="file" name="media_file" class="form-control" accept=".pdf,.docx,.pptx,.mp4,.webm">`.
  - Add helper hint: "Đính kèm video bài giảng (MP4/WebM < 1 GB) hoặc tài liệu slide (PDF, DOCX, PPTX)."
  - Make `markdown_content` textarea optional if file is attached.

#### 7. `src/pwd301/templates/student/lesson.html`
- **Video Stage**:
  - When `video_resource` is present:
    Render native HTML5 `<video id="udemy-html5-video" class="w-100 h-100" controls preload="metadata" playsinline>` with source URL `url_for('student.download_student_course_file_route', course_id=course.public_id, asset_id=video_resource.file_asset.public_id) ~ '?disposition=inline'`.
    Bind player controls (play/pause, seek, speed, volume, fullscreen) and sync playback time to the heartbeat progress updater.
  - When no video is present:
    Render a clean lecture header canvas with lesson title, duration, and slide preview button if a PDF is attached.
- **Document / Slide Preview**:
  - If a PDF resource is attached, provide a viewer tab or modal iframe for reading slides inline.
- **Tab 5 (Resources)**:
  - Replace hardcoded dummy entries with dynamic Jinja loop `{% for r in resources %}`.
  - Show real file name, size in MB, format badge (`PDF`, `DOCX`, `PPTX`, `VIDEO`), and active download link calling `student.download_student_course_file_route`.

---

## 5. Verification Method

### 5.1 Automated Test Execution
Run the test suites with the project Python environment:
```powershell
python -m pytest tests/api/test_file_api.py -v
python -m pytest tests/security/test_file_authorization_idor.py -v
python -m pytest tests/unit/test_file_service.py tests/unit/test_lesson_service.py -v
```

### 5.2 Specific Test Cases to Add in Test Suite
1. **`test_web_session_download_instructor_and_student`**:
   - Log in as instructor via Web session -> `GET /instructor/courses/<course_id>/files/<asset_id>/download` -> Returns HTTP 200 with file content and headers (`X-Content-Type-Options: nosniff`).
   - Log in as enrolled student via Web session -> `GET /student/courses/<course_id>/files/<asset_id>/download` -> Returns HTTP 200 with file content.
   - Verify HTTP Range request on video file (`Range: bytes=0-1023`) returns HTTP 206 Partial Content.
   - Log in as unenrolled student -> `GET /student/courses/<course_id>/files/<asset_id>/download` -> Returns HTTP 403 Forbidden.
2. **`test_file_asset_properties_and_rendering`**:
   - Verify `fa.original_filename`, `fa.file_size_bytes`, `fa.mime_type`, and `fa.virus_scan_status == 'CLEAN'` on clean uploads.
   - Verify `fa.virus_scan_status == 'INFECTED'` on EICAR upload.
3. **`test_lesson_media_upload_and_student_viewer`**:
   - Create lesson with attached MP4 video file -> Verify `LessonResource` created and linked.
   - Student GET `/student/courses/<course_id>/lessons/<lesson_id>` -> Verify response includes video source URL and attached resource items.
   - Create lesson with attached PDF slide -> Verify PDF resource listed in Tab 5.
4. **`test_virus_scan_error_enqueues_background_job_and_rescan`**:
   - Simulate scanner error during upload -> Verify file status is `PENDING`, `FILE_SCAN` job is enqueued in `background_jobs`.
   - Call rescan route -> Verify file transitions to `ACTIVE` once clean scan completes.

### 5.3 Invalidation Conditions
- Any change allowing session cookies on mutating REST routes (`POST /api/*`, `PUT /api/*`, etc.) is invalid and violates anti-CSRF invariants.
- Any change leaking internal `BigInt` PKs or physical file paths (`blobs/ab/cd/...`) in external endpoints or templates violates ADR-002 and ADR-008.
- Any change allowing students to download files from unpublished courses or quarantined revisions violates non-negotiable invariant 18 (fail-closed security).
