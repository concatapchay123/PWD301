## 2026-09-14T13:22:41Z

You are worker_m4, a teamwork_preview_worker subagent.
Your working directory is: e:\PWD301\.agents\teamwork_preview_worker_m4
Your role is: Milestone 4 Worker (Implementation & Test)
Your parent conversation ID is: 5f234e51-df3a-4989-b3f8-7adc52e9513d

MANDATORY INPUTS:
- ORIGINAL_REQUEST: e:\PWD301\.agents\ORIGINAL_REQUEST.md (You MUST read this before starting work)
- PROJECT.md: e:\PWD301\.agents\PROJECT.md
- Explorer M4 Backend Handoff: e:\PWD301\.agents\teamwork_preview_explorer_m4_1\handoff.md
- Explorer M4 Frontend Handoff: e:\PWD301\.agents\teamwork_preview_explorer_m4_2\handoff.md
- Spec Miner M4 Handoff: e:\PWD301\.agents\teamwork_preview_spec_miner_m4\handoff.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

WRITE OWNERSHIP (Exclusively owned files for this milestone):
- src/pwd301/models/course.py
- src/pwd301/models/file_import.py
- src/pwd301/blueprints/instructor/routes.py
- src/pwd301/blueprints/student/routes.py
- src/pwd301/templates/instructor/course_manage.html
- src/pwd301/templates/student/lesson.html
- tests/test_m4_lecture_media.py

TASK:
Implement Milestone 4 (R4: Multi-Format Lecture Authoring & Media Support):

1. **Update Models (`src/pwd301/models/course.py` & `src/pwd301/models/file_import.py`)**:
   - In `Lesson` (`course.py`):
     - Add `resources = relationship("LessonResource", back_populates="lesson", cascade="all, delete-orphan", order_by="LessonResource.position")`
     - Add properties:
       - `video_resource`: returns first resource where `res.file_asset and res.file_asset.is_video`
       - `document_resources`: returns list of resources where `res.file_asset and not res.file_asset.is_video`
   - In `LessonResource` (`file_import.py`):
     - Update `lesson` relationship to `back_populates="resources"`
     - Add helper properties: `title`, `file_name`, `file_size_bytes`, `mime_type`, `is_video`, `is_pdf`, `resource_type`, `file_size_formatted`

2. **Update Instructor Routes (`src/pwd301/blueprints/instructor/routes.py`)**:
   - In `create_lesson_route`:
     - Process `request.files`: handle `media_file` and `resource_files` (also `resource_file` / `file`).
     - If form `markdown_content` is blank, default to `# {title}\n\n{summary or 'Nội dung bài giảng đa phương tiện.'}` so instructors are not forced to type markdown when uploading media.
     - Call `create_lesson(actor, course.id, payload)`.
     - For uploaded media and resources: call `store_file_stream(actor=actor, course_id=course.id, file_stream=..., filename=..., content_type=..., asset_type="RESOURCE", title=..., session=db.session)` and `attach_resource_to_lesson(actor=actor, lesson_id=lesson.id, asset_id=asset.id, is_downloadable=True, label=..., session=db.session)`.
     - Flash success message and redirect to course management lessons tab.
   - Update `_serialize_lesson` to include `"resources": [_serialize_lesson_resource(r) for r in les.resources] if hasattr(les, "resources") and les.resources else []`.
   - Add routes:
     - `POST /courses/<course_id>/lessons/<lesson_id>/resources`: attach file to existing lesson.
     - `POST /courses/<course_id>/lessons/<lesson_id>/resources/<resource_id>/delete`: detach resource from lesson.

3. **Update Student Routes (`src/pwd301/blueprints/student/routes.py`)**:
   - In `get_student_lesson_route`:
     - Query `lesson_resources`, `video_resource`, `doc_resource`.
     - Pass `lesson_resources`, `video_resource`, `doc_resource` to `student/lesson.html`.
   - In `_serialize_student_lesson`: include `"resources": [_serialize_lesson_resource(r) for r in les.resources if r.file_asset and r.file_asset.status == "ACTIVE" and r.file_asset.virus_scan_status == "CLEAN"]`.

4. **Upgrade Templates**:
   - In `src/pwd301/templates/instructor/course_manage.html`:
     - Add `enctype="multipart/form-data"` to `#newLessonModal`.
     - Add file inputs:
       - `media_file` (`accept=".mp4,.webm,.mov,.pdf,.docx,.pptx"`)
       - `resource_files` (`multiple accept=".pdf,.docx,.pptx,.zip,.rar,.txt"`)
     - Remove `required` from `markdown_content` textarea in the modal.
     - In the lessons table: display badge with resource count when `les.resources` is present.
   - In `src/pwd301/templates/student/lesson.html`:
     - Stage area (`#udemy-video-canvas`):
       - If `video_resource`: render responsive HTML5 `<video controls playsinline preload="metadata">` with source `{{ url_for('student.download_student_course_file_route', course_id=course.public_id, asset_id=video_resource.file_asset.public_id) }}?disposition=inline`.
       - Else if `doc_resource`: render PDF slide embed / viewer with `?disposition=inline`.
       - Else: clean presentation banner for reading lessons.
     - Tab Header: update badge to `📁 Tài liệu đính kèm ({{ lesson_resources|length }})`.
     - Tab 5 (`#pane-resources`): dynamic loop over `lesson_resources` showing format badge, title, size, clean scan badge, view button, and download link. If empty, clean empty-state message.

5. **Write Comprehensive Tests (`tests/test_m4_lecture_media.py`)**:
   - Test lesson creation with attached MP4 video (< 1 GB) and verify `LessonResource` and `FileAsset` linkages.
   - Test lesson creation with attached PDF, DOCX, PPTX resources.
   - Test video size limit enforcement (< 1 GB limit with LimitingStream).
   - Test student video streaming endpoint returning 200/206 with `conditional=True`.
   - Test student downloading attached PDF/DOCX resources with active enrollment.
   - Test fail-closed security: unenrolled student or DRAFT lesson resource download returns 403 Forbidden.
   - Test resource detachment by instructor.

6. **Run Verification Commands**:
   - .venv\Scripts\python.exe -m pytest tests/test_m4_lecture_media.py -v
   - .venv\Scripts\python.exe -m pytest tests/unit/test_lesson_service.py tests/api/test_lesson_api.py tests/security/test_file_authorization_idor.py -v
   - .venv\Scripts\python.exe -m ruff check src tests scripts
   - .venv\Scripts\python.exe -m mypy src/pwd301
   - .venv\Scripts\python.exe scripts/repo_check.py

7. Produce a detailed handoff.md in your working directory and report results via send_message.
