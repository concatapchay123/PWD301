# Milestone 4 Backend Architecture Exploration Report: Multi-Format Lecture Authoring & Media Support

## 1. Observation

### 1.1 Models & Database Schema
1. **`src/pwd301/models/course.py` (lines 424–547)**:
   - `class Lesson(Base)` is mapped to table `lessons`.
   - Columns: `id` (BigIntPK), `public_id` (GUID), `course_id` (ForeignKey `courses.id`), `title` (Unicode 200), `summary` (Unicode 1000), `markdown_content` (NVarCharMax, NOT NULL), `position` (Integer, CheckConstraint `position > 0`), `estimated_duration_minutes`, `status` (CheckConstraint `ck_lessons_5`), etc.
   - Current relationships on `Lesson` (lines 530–536):
     ```python
     course = relationship("Course", back_populates="lessons")
     change_request = relationship(
         "CourseChangeRequest",
         foreign_keys=[change_request_id],
         backref="staged_lessons",
     )
     deleted_by = relationship("User", foreign_keys=[deleted_by_user_id])
     ```
   - **Crucial observation**: `Lesson` **does not have** a `resources` relationship pointing to `LessonResource`.

2. **`src/pwd301/models/file_import.py` (lines 459–512)**:
   - `class LessonResource(Base)` is mapped to table `lesson_resources`.
   - Columns:
     - `id`: `BigIntPK`, primary key
     - `lesson_id`: `sa.BigInteger`, `sa.ForeignKey("lessons.id", name="fk_lesson_resources_lesson_id")`, `nullable=False`
     - `file_asset_id`: `sa.BigInteger`, `sa.ForeignKey("file_assets.id", name="fk_lesson_resources_file_asset_id")`, `nullable=False`
     - `position`: `sa.Integer`, default=1, `nullable=False`
     - `label`: `sa.Unicode(255)`, `nullable=True`
     - `is_required`: `sa.Boolean`, default=False, `nullable=False`
     - `created_at`: `UTCDateTime`, default=utc_now
   - Unique constraints:
     - `uq_lesson_resources_lesson_id_file_asset_id_1`: `UNIQUE (lesson_id, file_asset_id)`
     - `uq_lesson_resources_lesson_id_position_2`: `UNIQUE (lesson_id, position)`
     - `ck_lesson_resources_1`: `CHECK (position > 0)`
   - Existing relationships on `LessonResource` (lines 505–506):
     ```python
     lesson = relationship("Lesson", foreign_keys=[lesson_id])
     file_asset = relationship("FileAsset", foreign_keys=[file_asset_id])
     ```
   - `LessonResource` already implements property `public_id` returning synthetic UUIDv5 per ADR-002:
     ```python
     @property
     def public_id(self) -> uuid.UUID:
         return uuid.uuid5(uuid.NAMESPACE_DNS, f"pwd301.lesson_resource.{self.id}")
     ```
   - Database DDL in `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/006_files_import.sql` (lines 104–117) and data dictionary `09_DATA_DICTIONARY_FILES_IMPORT.md` (lines 339–385) confirm this schema is canonical. Foreign key on `lesson_id` and `file_asset_id` is `ON DELETE NO ACTION`.

3. **`src/pwd301/models/file_import.py` (`FileAsset`, lines 298–314)**:
   - `FileAsset` already defines helper properties:
     - `is_video`: checks `self.mime_type.startswith("video/")` or filename ends with `.mp4`, `.webm`, `.mkv`, `.mov`, `.avi`.
     - `is_pdf`: checks `self.mime_type == "application/pdf"` or filename ends with `.pdf`.
     - `virus_scan_status`: returns `CLEAN`, `INFECTED`, `PENDING`, or `BLOCKED`.

### 1.2 Lesson and File Services
1. **`src/pwd301/services/lesson_service.py` (lines 115–240, 797–870)**:
   - `create_lesson(actor, course_id, data, session=None)`: validates `title` (required, <= 200 chars), `markdown_content` (required, non-empty, tested explicitly in `tests/unit/test_lesson_service.py:180`), `summary`, `estimated_duration_minutes`, etc.
   - `update_lesson(actor, lesson_id, data, session=None)`: safely updates fields in `UPDATABLE_LESSON_FIELDS`.
   - `get_lesson_detail(actor, lesson_id, session=None)`: strictly checks authorization. For students, verifies active course enrollment and that lesson status is `PUBLISHED`.
   - Currently, `lesson_service.py` does not reference `LessonResource`.

2. **`src/pwd301/services/file_service.py` (lines 105–126, 175–235, 297–365, 1057–1160)**:
   - `LimitingStream` (line 105): wraps incoming binary streams and raises `FileSizeLimitExceededError` if read exceeds `max_bytes` (1,000,000,000 bytes = 1 GB).
   - `check_file_size_limit` (line 182): strictly enforces video files < 1 GB (`VIDEO_EXTENSIONS`), PDF <= 50 MB, DOCX <= 50 MB, PPTX <= 100 MB, Image <= 10 MB.
   - `detect_mime_type` (line 236): correctly identifies magic bytes for PNG, JPEG, GIF, PDF (`%PDF-`), DOCX/PPTX (OpenXML ZIP signature `PK\x03\x04`), WebP (`RIFF...WEBP`), and video MIME types.
   - `store_file_stream` (line 297): streams file to quarantine with `LimitingStream`, hashes SHA-256, deduplicates via `FileBlob` (Algorithm 12), and creates `FileAsset` and `FileRevision` in `ACTIVE` state with clean scan result.
   - `attach_resource_to_lesson` (lines 1057–1120): already implements attaching a `FileAsset` to a `Lesson`, verifying course match and auto-incrementing `position`.
   - `detach_resource_from_lesson` (lines 1123–1160): already implements detaching a resource by public UUID, internal ID, or asset public ID.
   - `_serialize_lesson_resource` (lines 1604–1616): serializes resource with `resource_id`, `lesson_id`, `title`, `label`, `file_asset`, `position`, `is_required`, `created_at`.

### 1.3 Routes & Blueprints
1. **`src/pwd301/blueprints/instructor/routes.py`**:
   - `create_lesson_route` (lines 603–631): currently parses JSON or form dict via `request.get_json() or request.form.to_dict()`. It completely ignores `request.files`! Multipart form file uploads are never processed when creating lessons.
   - `update_lesson_route` (lines 827–836): only accepts `PATCH` and `PUT` methods and JSON/form dict; does not support `POST` or file uploads.
   - `upload_course_file_route` (lines 649–707): currently accepts files for the course, and if `lesson_id` is supplied in the form, attaches it via `LessonResource`.
   - `_serialize_lesson` (lines 585–600): does not include attached `resources` in the output dictionary.

2. **`src/pwd301/blueprints/student/routes.py`**:
   - `get_student_lesson_route` (lines 267–299): loads lesson via `get_lesson_detail(actor, lesson_id)`, passes `lesson=lesson` to `student/lesson.html`.
   - `_serialize_student_lesson` (lines 247–264): does not include attached `resources` in the output dictionary.
   - `download_student_course_file_route` (lines 1273–1306):
     - Endpoints: `GET /student/courses/<course_id>/files/<asset_id>/download` and `GET /student/files/<asset_id>/download`.
     - Calls `get_file_for_download(actor, asset_id)` which enforces active enrollment, published course status, clean scan status, and published lesson status.
     - Uses `send_file(..., conditional=True)` which natively supports HTTP 206 Partial Content (essential for video streaming/scrubbing).

3. **Templates**:
   - `src/pwd301/templates/instructor/course_manage.html` (lines 235–275): `#newLessonModal` has `method="POST"` without `enctype="multipart/form-data"`. It only has inputs for title, duration, position, summary, markdown_content. No file inputs exist.
   - `src/pwd301/templates/student/lesson.html`:
     - Video player stage (lines 348–420) is a simulated mockup with static SVG overlay, lacking an actual `<video>` tag or dynamic stream source.
     - Tab 5 `#pane-resources` (lines 544–570) contains hardcoded dummy items ("Slide bài giảng", "Mã nguồn thực hành") with `alert('Đang chuẩn bị tệp tin tải xuống...')` instead of iterating over `lesson.resources`.

---

## 2. Logic Chain

1. **Model Bidirectionality & Encapsulation**:
   - `Lesson` in `course.py` lacks `resources = relationship(...)`. While `LessonResource` has `lesson = relationship("Lesson")`, SQLAlchemy cannot access `lesson.resources` directly without this relationship.
   - Adding `resources = relationship("LessonResource", back_populates="lesson", cascade="all, delete-orphan", order_by="LessonResource.position")` on `Lesson` and updating `LessonResource.lesson` to `back_populates="resources"` establishes clean ORM navigation.
   - Adding helper properties on `Lesson` (`video_resource`, `document_resources`) and on `LessonResource` (`title`, `is_video`, `is_pdf`, `file_size_formatted`, `resource_type`) allows clean, declarative template rendering without complex logic in Jinja.

2. **Validation Compatibility Invariant**:
   - Unit test `tests/unit/test_lesson_service.py:180` asserts that calling `create_lesson` with empty or whitespace markdown raises `LessonValidationError("markdown_content is required")`.
   - Therefore, `create_lesson` in `lesson_service.py` must NOT remove this validation.
   - Instead, the web authoring route `create_lesson_route` in `instructor/routes.py` should intelligently default `markdown_content` if the instructor provides media files or leaves markdown blank (e.g. `f"# {title}\n\n{summary or 'Nội dung bài giảng đa phương tiện.'}"`). This satisfies the backend validator while fulfilling the requirement that instructors are not forced to write manual markdown when attaching media.

3. **Multipart Ingestion in Instructor Portal**:
   - In `create_lesson_route`:
     - Parse `request.files` for `media_file` (primary video/slides) and `resource_files` (list of attachments).
     - First create the `Lesson` via `create_lesson`.
     - For `media_file` and each file in `resource_files`: invoke `store_file_stream`, then `attach_resource_to_lesson`.
     - In `_serialize_lesson`: include `"resources": [_serialize_lesson_resource(r) for r in les.resources]`.
   - Add web management endpoints:
     - `POST /instructor/courses/<course_id>/lessons/<lesson_id>/resources`: attach uploaded file to existing lesson.
     - `POST /instructor/courses/<course_id>/lessons/<lesson_id>/resources/<resource_id>/delete`: detach resource from lesson.

4. **Dynamic Student Lecture Experience**:
   - In `student/lesson.html`:
     - If `lesson.video_resource` exists (or first video in `lesson.resources`): render native HTML5 `<video controls class="w-100 h-100" preload="metadata" playsinline>` pointing to `url_for('student.download_student_course_file_route', course_id=course.public_id, asset_id=video_res.file_asset.public_id, disposition='inline')`.
     - If no video but a PDF document is attached: render a document preview card / embedded PDF viewer with online view and direct download actions.
     - In Tab 5 (`#pane-resources`): loop over `lesson.resources`, display file type badges, formatted sizes, and real download links to `url_for('student.download_student_course_file_route', course_id=course.public_id, asset_id=res.file_asset.public_id)`. If empty, display a clean empty-state notice.

---

## 3. Caveats

1. **Video Streaming & Seeking**: `send_file(..., conditional=True)` in `student/routes.py` relies on HTTP range headers (bytes=start-end) implemented by Werkzeug. For local files in development and standard WSGI servers, this works out-of-the-box. In production behind reverse proxies (Nginx), range requests should be preserved.
2. **Database Soft-Delete vs Hard-Delete**: SQL Server constraints have `ON DELETE NO ACTION`. Deleting a `Lesson` through the application uses soft-delete (`trash_lesson`), setting `status = 'TRASH'` and `deleted_at = utc_now()`. Attached `LessonResource` rows remain in the DB but are filtered out by `deleted_at` or `status` checks.
3. **No Database Migration Needed**: All tables (`lessons`, `lesson_resources`, `file_assets`, `file_revisions`, `file_blobs`) and columns already exist in SQL Server schema and Alembic migrations. This milestone requires only Python model relationships, route logic, service glue, and Jinja template upgrades.

---

## 4. Conclusion & Exact Implementation Plan for Worker M4

Worker M4 should execute the following focused steps:

### Step 1: Update Models (`src/pwd301/models/course.py` and `file_import.py`)
1. In `src/pwd301/models/course.py` on `Lesson`:
   - Add relationship:
     ```python
     resources = relationship(
         "LessonResource",
         back_populates="lesson",
         cascade="all, delete-orphan",
         order_by="LessonResource.position",
     )
     ```
   - Add helper properties:
     - `@property def video_resource(self) -> LessonResource | None`: returns first resource where `res.file_asset and res.file_asset.is_video`.
     - `@property def document_resources(self) -> list[LessonResource]`: returns list of resources where `res.file_asset and not res.file_asset.is_video`.
2. In `src/pwd301/models/file_import.py` on `LessonResource`:
   - Update `lesson` relationship to `back_populates="resources"`:
     ```python
     lesson = relationship("Lesson", back_populates="resources", foreign_keys=[lesson_id])
     ```
   - Add helper properties on `LessonResource`:
     - `title`: `self.label or (self.file_asset.display_name if self.file_asset else "Resource")`
     - `file_name`: `self.file_asset.original_filename if self.file_asset else ""`
     - `file_size_bytes`: `self.file_asset.size_bytes if self.file_asset else 0`
     - `mime_type`: `self.file_asset.mime_type if self.file_asset else "application/octet-stream"`
     - `is_video`: `bool(self.file_asset and self.file_asset.is_video)`
     - `is_pdf`: `bool(self.file_asset and self.file_asset.is_pdf)`
     - `resource_type`: returns `"VIDEO"`, `"PDF"`, `"DOCX"`, `"PPTX"`, or `"DOCUMENT"`.

### Step 2: Update Instructor Routes (`src/pwd301/blueprints/instructor/routes.py`)
1. In `create_lesson_route(course_id)`:
   - Handle multipart upload: read `request.files.get("media_file")` and `request.files.getlist("resource_files")` (also checking `"file"` and `"resource_file"`).
   - If form `markdown_content` is blank, default to:
     `payload["markdown_content"] = f"# {payload.get('title', 'Bài giảng')}\n\n{payload.get('summary') or 'Nội dung bài giảng đa phương tiện.'}"`
   - Create lesson via `create_lesson`.
   - If files are uploaded, iterate and call `store_file_stream` + `attach_resource_to_lesson`.
   - Update flash message to indicate attached media count.
2. In `_serialize_lesson(les)`:
   - Include `"resources": [_serialize_lesson_resource(r) for r in les.resources] if hasattr(les, "resources") and les.resources else []`.
3. Add routes for managing resources on existing lessons:
   - `POST /courses/<course_id>/lessons/<lesson_id>/resources`: upload & attach file.
   - `POST /courses/<course_id>/lessons/<lesson_id>/resources/<resource_id>/delete`: detach resource.

### Step 3: Update Student Routes (`src/pwd301/blueprints/student/routes.py`)
1. In `_serialize_student_lesson(les, p)`:
   - Include `"resources": [_serialize_lesson_resource(r) for r in les.resources if r.file_asset and r.file_asset.status == "ACTIVE" and r.file_asset.virus_scan_status == "CLEAN"]`.

### Step 4: Upgrade Templates
1. `src/pwd301/templates/instructor/course_manage.html`:
   - Add `enctype="multipart/form-data"` to `#newLessonModal`.
   - Remove `required` from `markdown_content` textarea in the modal.
   - Add file inputs:
     - Main lecture media: `<input type="file" name="media_file" class="form-control" accept=".mp4,.webm,.mov,.pdf,.docx,.pptx">`
     - Supplementary materials: `<input type="file" name="resource_files" class="form-control" multiple accept=".pdf,.docx,.pptx,.zip">`
   - In lessons table: show resource count badge and modal/form for attaching resources to existing lessons.
2. `src/pwd301/templates/student/lesson.html`:
   - Replace static video placeholder with native HTML5 `<video>` tag pointing to `url_for('student.download_student_course_file_route', course_id=course.public_id, asset_id=video_resource.file_asset.public_id, disposition='inline')` if video is attached.
   - Replace hardcoded dummy items in Tab 5 (`#pane-resources`) with dynamic loop over `lesson.resources`, displaying badges, file info, and working download links.

### Step 5: Test Coverage (`tests/unit/test_m4_lecture_media.py`)
- Unit/Integration tests verifying:
  1. Creating a lesson with attached video MP4 (< 1 GB) and verifying `LessonResource` and `FileAsset` link.
  2. Enforcing < 1 GB limit on video upload (raises 413 / `FileSizeLimitExceededError`).
  3. Student access to lesson video stream (`GET .../files/<id>/download?disposition=inline`) returning 200/206.
  4. Student downloading attached PDF/DOCX resources with valid authorization.
  5. Unenrolled student or non-published lesson download returns 403 Forbidden.

---

## 5. Verification Method

To verify the Milestone 4 backend implementation independently:
1. **Automated Unit & Integration Tests**:
   ```powershell
   pytest tests/unit/test_lesson_service.py tests/api/test_lesson_api.py tests/security/test_file_authorization_idor.py tests/unit/test_m4_lecture_media.py -v
   ```
2. **Repository Static Verification**:
   ```powershell
   python scripts/repo_check.py
   ```
3. **Invalidation Conditions**:
   - If `Lesson.resources` raises `InvalidRequestError` or `RelationshipError` during app initialization.
   - If uploading a 1 GB+ file fails to trigger `FileSizeLimitExceededError`.
   - If an unenrolled student can download lesson resources.
   - If clean uploaded files fail to render in the student lesson resources tab.
