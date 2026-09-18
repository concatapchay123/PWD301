# Handoff Report: Milestone 4 Frontend & Viewer Exploration (R4)

**Agent ID**: `explorer_m4_2`  
**Working Directory**: `e:\PWD301\.agents\teamwork_preview_explorer_m4_2`  
**Target Milestone**: Milestone 4 — Multi-Format Lecture Authoring & Media Support (F12, F13, F14)  
**Timestamp**: 2026-09-14T13:21:20Z  

---

## 1. Observation

### 1.1. Instructor Lesson Authoring UI (`src/pwd301/templates/instructor/course_manage.html`)
- **Modal Location**: Lines 234–275. The modal ID is `#newLessonModal` (note: prompt referred to `#addLessonModal`, the actual modal in template is `#newLessonModal`).
- **Form Tag**:
  ```html
  <form method="POST" action="/instructor/courses/{{ course.public_id }}/lessons">
  ```
  - **Defect/Gap 1**: Missing `enctype="multipart/form-data"`. Any file inputs will not transmit binary streams to Flask unless multipart encoding is declared.
  - **Defect/Gap 2**: Missing file input fields. Currently only inputs are `title` (text, required), `estimated_duration_minutes` (number), `position` (number), `summary` (textarea), and `markdown_content` (textarea, required).
  - **Defect/Gap 3**: In the lessons list table (lines 185–221), there is no visual indicator or badge showing attached media or resources for a lesson, and there is no "Chỉnh sửa" (Edit) modal or button for lessons (only "Xem" and "Xóa").

### 1.2. Student Lesson Viewer (`src/pwd301/templates/student/lesson.html`)
- **Stage Canvas Area**: Lines 348–422 (`#udemy-video-canvas`).
  - Currently contains only simulated HTML/CSS mock controls: `#center-play-btn`, `#scrubber-track`, and mock text "Trình phát bài giảng Full HD 1080p • Thời lượng ước tính: ...".
  - **Defect/Gap 4**: There is **NO** `<video>` element rendered in the template. Video playback is completely mocked.
- **Tab 5 (Tài liệu đính kèm)**: Lines 448–450 and 544–570 (`#pane-resources`).
  - **Defect/Gap 5**: The tab header is hardcoded as `📁 Tài liệu đính kèm (3)`.
  - **Defect/Gap 6**: The resources list has 2 hardcoded static items (PDF and ZIP) with an inlined dummy click handler `onclick="alert('Đang chuẩn bị tệp tin tải xuống...')"` rather than real download links.
  - It is completely disconnected from database entities (`LessonResource` / `FileAsset`).

### 1.3. Backend Route & Model Contracts
- **Download Route Capability**:
  - Student download: `GET /student/courses/<course_id>/files/<asset_id>/download` (`src/pwd301/blueprints/student/routes.py:1273`).
  - Instructor download: `GET /instructor/courses/<course_id>/files/<asset_id>/download` (`src/pwd301/blueprints/instructor/routes.py:731`).
  - **Key Observation**: Both download endpoints check parameter `disposition = request.args.get("disposition", "attachment").lower()`. If `disposition == "inline"`, `send_file(..., as_attachment=False, conditional=True)` is called!
  - `conditional=True` enables HTTP range requests (`Range: bytes=...`), which is mandatory for video streaming, scrubbing, and seeking in HTML5 `<video>` tags.
  - For inline HTML5 `<video>` and PDF `<iframe>` viewing, passing `?disposition=inline` is required so browsers render media rather than prompting a file download dialog.
- **Model Relationship Gap**:
  - `src/pwd301/models/course.py` (`class Lesson`): Currently has NO `resources` relationship to `LessonResource`.
  - `src/pwd301/models/file_import.py` (`class LessonResource`): Currently has `lesson = relationship("Lesson", foreign_keys=[lesson_id])` without `back_populates`.

### 1.4. Canonical Frontend Preview Reference (`frontend-preview/assets/js/views/student.js`)
- Lines 560–640: Udemy 16:9 player stage split view with edge chevrons (`.udemy-edge-nav-btn prev/next`), play button overlay, and controls bar.
- Lines 642–675: Tabs bar with active state styles: `Nội dung bài học`, `Tổng quan & Mục tiêu`, `Hỏi đáp (Q&A)`, `Ghi chú`, `Tài liệu đính kèm (${resources.length})`.
- Lines 951–983: Resources tab rendering:
  - Header: `Tài liệu & Công cụ học tập đính kèm` + badge `${resources.length} tệp tin`.
  - List group item with icon, title, format badge (`r.type.toUpperCase()`), file size (`r.size`), and download button.
  - Empty state with clean informative message when no resources attached.

---

## 2. Logic Chain

1. **Lesson Authoring Multi-Format Upload**:
   - Instructors need to attach media (MP4, WebM, PDF, DOCX, PPTX) when creating lessons.
   - Adding `enctype="multipart/form-data"` to `#newLessonModal` enables browser binary uploads.
   - Adding `<input type="file" name="media_file" accept=".mp4,.webm,.pdf,.docx,.pptx">` allows selecting primary media (Video or Slide).
   - Adding `<input type="file" name="resource_files" multiple accept=".pdf,.docx,.pptx,.zip,.rar,.txt">` allows selecting multiple supplementary resources.
   - Updating `create_lesson_route` in `src/pwd301/blueprints/instructor/routes.py` to process `request.files` streams via `store_file_stream()` and creates `LessonResource` records.

2. **Student Video & Document Presentation**:
   - In `student/routes.py:get_student_lesson_route`, query `LessonResource` records for `lesson.id`.
   - Identify `video_resource` (MIME type starting with `video/` or extension `.mp4`/`.webm`) and `doc_resource` (PDF document).
   - In `student/lesson.html` stage canvas (`#udemy-video-canvas`):
     - **If `video_resource` exists**: render native HTML5 `<video controls playsinline preload="metadata">` with source `{{ url_for('student.download_student_course_file_route', course_id=course.public_id, asset_id=video_resource.file_asset.public_id) }}?disposition=inline`.
     - **If `doc_resource` exists and no video**: render an interactive PDF viewer container with toolbar and `<iframe src="...download?disposition=inline#toolbar=1">`.
     - **If office doc (.docx, .pptx)**: render presentation card with document title, size, clean scan badge, and download action.
     - **If no media attached**: retain presentation hero banner displaying lesson title, estimated duration, and quick button to jump to the markdown reading pane.

3. **Dynamic Resources List (Tab 5)**:
   - In `student/lesson.html`:
     - Set Tab title to `📁 Tài liệu đính kèm ({{ lesson_resources|length }})`.
     - In `#pane-resources`, iterate over `lesson_resources`:
       - Show format badge (PDF, DOCX, PPTX, VIDEO, ZIP, etc.).
       - Show resource label / filename.
       - Show formatted size in MB or KB (`file_asset.file_size_bytes`).
       - Show malware scan badge (`file_asset.virus_scan_status == 'CLEAN'`).
       - Provide "Tải xuống" button with direct authenticated download link.
       - For viewable formats (PDF / Video), provide an inline "Xem" button (`target="_blank"` with `?disposition=inline`).
     - Render empty state matching `frontend-preview` if `lesson_resources` is empty.

4. **Heartbeat & Video Progress Integration**:
   - Listen to `timeupdate` and `ended` events on `#lecture-html5-video`.
   - Compute `view_fraction = video.currentTime / video.duration` and pass with the 15-second heartbeat to `/student/lessons/<id>/progress`.
   - When video ends, automatically trigger `toggleLessonCompletion()`.

---

## 3. Caveats

- **Office File In-Browser Rendering**: Native `.docx` and `.pptx` files cannot be rendered inside an `iframe` without external third-party cloud viewers (e.g. Office 365 or Google Docs viewer), which require public internet exposure and violate air-gapped/local network constraints. Therefore, Office files must be presented defensively with structured preview cards and direct download buttons.
- **Video File Size Limit**: Video uploads must strictly obey the `< 1 GB` limit enforced by `MAX_CONTENT_LENGTH` and `LimitingStream`.
- **Active Enrollment & Quarantine Security**: Download endpoints are fail-closed. Unscanned or quarantined files (`virus_scan_status != 'CLEAN'`) will return 403 Forbidden.
- **Database Model Migration**: `Lesson.resources` relationship requires linking to `LessonResource`. No schema DDL migration is required because the `lesson_resources` table already exists in the schema; only the SQLAlchemy model relationship needs to be added.

---

## 4. Conclusion & Concrete Code Specifications

### 4.1. Model Changes: `src/pwd301/models/course.py` & `src/pwd301/models/file_import.py`

In `src/pwd301/models/course.py` under `class Lesson`:
```python
    # Milestone 4: Attached media resources relationship
    resources = relationship(
        "LessonResource",
        foreign_keys="LessonResource.lesson_id",
        back_populates="lesson",
        cascade="all, delete-orphan",
        order_by="LessonResource.position",
    )
```

In `src/pwd301/models/file_import.py` under `class LessonResource`:
```python
    lesson = relationship("Lesson", foreign_keys=[lesson_id], back_populates="resources")
    file_asset = relationship("FileAsset", foreign_keys=[file_asset_id])
```

---

### 4.2. Instructor Modal Changes: `src/pwd301/templates/instructor/course_manage.html`

Replace lines 237–273 with:
```html
          <form method="POST" action="/instructor/courses/{{ course.public_id }}/lessons" enctype="multipart/form-data">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
            <div class="modal-header">
              <h5 class="modal-title fw-bold" id="newLessonModalLabel">Thêm bài giảng mới</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body p-4">
              <div class="mb-3">
                <label class="form-label fw-semibold">Tiêu đề bài giảng <span class="text-danger">*</span></label>
                <input type="text" name="title" class="form-control" placeholder="Ví dụ: Bài 1 - Giới thiệu kiến trúc hệ thống..." required>
              </div>
              <div class="row g-3 mb-3">
                <div class="col-md-6">
                  <label class="form-label fw-semibold">Thời lượng ước tính (phút)</label>
                  <input type="number" name="estimated_duration_minutes" class="form-control" value="30" min="1" max="600">
                </div>
                <div class="col-md-6">
                  <label class="form-label fw-semibold">Thứ tự hiển thị (Position)</label>
                  <input type="number" name="position" class="form-control" value="{{ (lessons|length) + 1 }}" min="1">
                </div>
              </div>
              <div class="mb-3">
                <label class="form-label fw-semibold">Tóm tắt ngắn</label>
                <textarea name="summary" class="form-control" rows="2" placeholder="Tóm tắt mục tiêu chính của bài học..."></textarea>
              </div>
              <div class="mb-3">
                <label class="form-label fw-semibold">Nội dung bài học (Hỗ trợ Markdown) <span class="text-danger">*</span></label>
                <textarea name="markdown_content" class="form-control font-monospace" rows="6" placeholder="# Mục tiêu bài học&#10;&#10;Nội dung chi tiết giảng dạy..." required></textarea>
              </div>

              <!-- Media Upload Section (Milestone 4) -->
              <div class="card bg-light border-0 p-3 rounded-3">
                <h6 class="fw-bold text-slate-900 mb-2 d-flex align-items-center gap-2">
                  <i class="bi bi-paperclip text-primary"></i> Đa phương tiện & Tài liệu đính kèm
                </h6>
                <div class="mb-3">
                  <label class="form-label fw-semibold small mb-1">Tệp bài giảng chính (Video hoặc Slide)</label>
                  <input type="file" name="media_file" class="form-control form-control-sm" accept=".mp4,.webm,.pdf,.docx,.pptx">
                  <div class="form-text text-muted" style="font-size: 11.5px;">
                    Định dạng hỗ trợ: Video MP4/WebM (&lt; 1 GB) hoặc Slide PDF, Word DOCX, PowerPoint PPTX (&lt; 50 MB).
                  </div>
                </div>
                <div>
                  <label class="form-label fw-semibold small mb-1">Tài liệu tham khảo bổ sung (Tùy chọn)</label>
                  <input type="file" name="resource_files" class="form-control form-control-sm" multiple accept=".pdf,.docx,.pptx,.zip,.rar,.txt">
                  <div class="form-text text-muted" style="font-size: 11.5px;">
                    Có thể chọn nhiều tệp tin (Slide, tài liệu đọc, mã nguồn mẫu ZIP).
                  </div>
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-light" data-bs-dismiss="modal">Hủy</button>
              <button type="submit" class="btn btn-primary">Lưu bài giảng</button>
            </div>
          </form>
```

In the lessons table (`course_manage.html` lines 188–192), render media badges:
```html
                <td>
                  <div class="fw-bold text-slate-900 d-flex align-items-center gap-2">
                    <span>{{ les.title }}</span>
                    {% if les.resources %}
                      <span class="badge bg-primary-subtle text-primary border border-primary-subtle" style="font-size: 11px;">
                        <i class="bi bi-paperclip me-1"></i>{{ les.resources|length }} tệp
                      </span>
                    {% endif %}
                  </div>
                  <small class="text-muted">ID: {{ les.public_id }}</small>
                </td>
```

---

### 4.3. Instructor Backend Route Changes: `src/pwd301/blueprints/instructor/routes.py`

Update `create_lesson_route` (lines 605–631) to process `request.files`:
```python
    try:
        lesson = create_lesson(actor, course.id, payload)

        # Milestone 4: Process attached media files
        if request.files:
            media_file = request.files.get("media_file")
            if media_file and media_file.filename:
                m_asset = store_file_stream(
                    actor=actor,
                    course_id=course.id,
                    file_stream=media_file.stream,
                    filename=media_file.filename,
                    content_type=media_file.content_type,
                    asset_type="RESOURCE",
                    title=f"Bài giảng: {lesson.title}",
                    session=db.session,
                )
                m_res = LessonResource(
                    lesson_id=lesson.id,
                    file_asset_id=m_asset.id,
                    label=media_file.filename,
                    position=1,
                    is_required=True,
                )
                db.session.add(m_res)

            resource_files = request.files.getlist("resource_files")
            pos_offset = 2 if (media_file and media_file.filename) else 1
            for idx, r_file in enumerate(resource_files):
                if r_file and r_file.filename:
                    r_asset = store_file_stream(
                        actor=actor,
                        course_id=course.id,
                        file_stream=r_file.stream,
                        filename=r_file.filename,
                        content_type=r_file.content_type,
                        asset_type="RESOURCE",
                        title=r_file.filename,
                        session=db.session,
                    )
                    r_res = LessonResource(
                        lesson_id=lesson.id,
                        file_asset_id=r_asset.id,
                        label=r_file.filename,
                        position=pos_offset + idx,
                        is_required=False,
                    )
                    db.session.add(r_res)

            db.session.commit()

        if request.accept_mimetypes.accept_html and not request.is_json:
            flash(f"Bài giảng '{lesson.title}' đã được thêm thành công vào khóa học!", "success")
            return redirect(
                url_for("instructor.manage_course_hub", course_id=course.public_id, tab="lessons")
            )
        return jsonify(_serialize_lesson(lesson)), 201
```

---

### 4.4. Student Backend Route Changes: `src/pwd301/blueprints/student/routes.py`

In `get_student_lesson_route` (lines 284–297):
```python
    if request.accept_mimetypes.accept_html and not request.is_json:
        all_lessons = (
            sess.query(Lesson)
            .filter(Lesson.course_id == course.id, Lesson.deleted_at.is_(None))
            .order_by(Lesson.position.asc())
            .all()
        )
        
        # Milestone 4: Query lesson resources and classify primary media
        lesson_resources = (
            sess.query(LessonResource)
            .filter(LessonResource.lesson_id == lesson.id)
            .order_by(LessonResource.position.asc())
            .all()
        )
        video_resource = next(
            (
                r for r in lesson_resources
                if (
                    (r.file_asset.mime_type and r.file_asset.mime_type.startswith("video/"))
                    or (r.file_asset.original_filename and r.file_asset.original_filename.lower().endswith((".mp4", ".webm")))
                )
            ),
            None,
        )
        doc_resource = next(
            (
                r for r in lesson_resources
                if (
                    (r.file_asset.mime_type == "application/pdf")
                    or (r.file_asset.original_filename and r.file_asset.original_filename.lower().endswith(".pdf"))
                )
            ),
            None,
        )

        return render_template(
            "student/lesson.html",
            course=course,
            lesson=lesson,
            progress=progress,
            all_lessons=all_lessons,
            lesson_resources=lesson_resources,
            video_resource=video_resource,
            doc_resource=doc_resource,
        )
```

---

### 4.5. Student Viewer Template Changes: `src/pwd301/templates/student/lesson.html`

1. **Stage Area (`#udemy-video-canvas`, lines 348–422)**:
```html
      <!-- 16:9 Video & Media Canvas Screen -->
      <div class="udemy-video-stage" id="udemy-video-canvas">
        {% set prev_lesson = none %}
        {% set next_lesson = none %}
        {% for l in all_lessons %}
          {% if l.position == lesson.position - 1 %}
            {% set prev_lesson = l %}
          {% elif l.position == lesson.position + 1 %}
            {% set next_lesson = l %}
          {% endif %}
        {% endfor %}

        <!-- Edge Navigation Chevrons -->
        {% if prev_lesson %}
          <a href="{{ url_for('student.get_student_lesson_route', course_id=course.public_id, lesson_id=prev_lesson.public_id) }}" class="udemy-edge-nav-btn prev" title="Bài trước: {{ prev_lesson.title }}">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
          </a>
        {% endif %}
        {% if next_lesson %}
          <a href="{{ url_for('student.get_student_lesson_route', course_id=course.public_id, lesson_id=next_lesson.public_id) }}" class="udemy-edge-nav-btn next" title="Bài tiếp theo: {{ next_lesson.title }}">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
          </a>
        {% endif %}

        {% if video_resource %}
          <!-- HTML5 Video Player -->
          <div class="w-100 h-100 position-relative d-flex align-items-center justify-content-center bg-black">
            <video id="lecture-html5-video" class="w-100 h-100" controls playsinline preload="metadata" style="max-height: 520px; object-fit: contain; background: #000;">
              <source src="{{ url_for('student.download_student_course_file_route', course_id=course.public_id, asset_id=video_resource.file_asset.public_id) }}?disposition=inline" type="{{ video_resource.file_asset.mime_type or 'video/mp4' }}">
              Trình duyệt của bạn không hỗ trợ thẻ video HTML5. Vui lòng tải video về từ tab Tài liệu đính kèm.
            </video>
          </div>
        {% elif doc_resource %}
          <!-- Embedded PDF Slide Viewer -->
          <div class="w-100 h-100 d-flex flex-column bg-dark" style="min-height: 480px; max-height: 520px;">
            <div class="d-flex justify-content-between align-items-center px-3 py-2 bg-dark text-white border-bottom border-secondary small">
              <div class="d-flex align-items-center gap-2 text-truncate">
                <span class="badge bg-danger">PDF Slide</span>
                <span class="fw-semibold text-truncate">{{ doc_resource.label or doc_resource.file_asset.original_filename }}</span>
              </div>
              <div class="d-flex align-items-center gap-2">
                <a href="{{ url_for('student.download_student_course_file_route', course_id=course.public_id, asset_id=doc_resource.file_asset.public_id) }}" class="btn btn-sm btn-outline-light py-0 px-2" download title="Tải về slide">
                  <i class="bi bi-download me-1"></i>Tải về
                </a>
                <a href="{{ url_for('student.download_student_course_file_route', course_id=course.public_id, asset_id=doc_resource.file_asset.public_id) }}?disposition=inline" target="_blank" class="btn btn-sm btn-outline-light py-0 px-2" title="Mở trong tab mới">
                  <i class="bi bi-box-arrow-up-right me-1"></i>Mở toàn màn hình
                </a>
              </div>
            </div>
            <iframe src="{{ url_for('student.download_student_course_file_route', course_id=course.public_id, asset_id=doc_resource.file_asset.public_id) }}?disposition=inline#toolbar=1" class="w-100 flex-grow-1 border-0" style="min-height: 440px;" title="Tài liệu bài giảng"></iframe>
          </div>
        {% else %}
          <!-- Text / Reading Presentation Stage -->
          <div class="text-center position-relative px-3" style="z-index: 10;">
            <div class="mb-3 mx-auto d-flex align-items-center justify-content-center bg-primary text-white rounded-circle" style="width: 64px; height: 64px;">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path></svg>
            </div>
            <div class="text-white fw-bold" style="font-size: 1.25rem; text-shadow: 0 2px 8px rgba(0,0,0,0.85);">
              {{ lesson.title }}
            </div>
            <div class="text-slate-300 text-caption mt-1" style="font-size: 13px; text-shadow: 0 1px 4px rgba(0,0,0,0.8);">
              Bài giảng lý thuyết & Thực hành • Thời lượng ước tính: {{ lesson.estimated_duration_minutes or 30 }} phút
            </div>
            <button type="button" class="btn btn-light btn-sm mt-3 px-3 fw-semibold" onclick="switchPlayerTab('content')">
              Đọc nội dung bài học bên dưới ↓
            </button>
          </div>
        {% endif %}
      </div>
```

2. **Tab Header (lines 448–450)**:
```html
          <li>
            <button type="button" class="udemy-tab-btn" data-tab="resources" onclick="switchPlayerTab('resources')">
              📁 Tài liệu đính kèm ({{ lesson_resources|length }})
            </button>
          </li>
```

3. **Tab 5 Body (`#pane-resources`, lines 544–570)**:
```html
        <!-- Tab 5: Tài liệu đính kèm (Milestone 4 Dynamic Rendering) -->
        <div class="tab-pane-content d-none" id="pane-resources">
          <div style="max-width: 860px;">
            <div class="d-flex justify-content-between align-items-center mb-3">
              <h3 class="h5 fw-bold text-slate-900 mb-0">Tài liệu & Tệp tin học tập</h3>
              <span class="badge bg-primary-subtle text-primary fw-semibold">{{ lesson_resources|length }} tệp tin</span>
            </div>

            {% if lesson_resources %}
              <div class="list-group list-group-flush border rounded-3 shadow-xs">
                {% for res in lesson_resources %}
                  {% set fa = res.file_asset %}
                  {% set fn = (fa.original_filename or fa.display_name or 'tailieu')|lower %}
                  {% set mt = (fa.mime_type or '')|lower %}
                  <div class="list-group-item d-flex flex-column flex-sm-row justify-content-between align-items-start align-items-sm-center gap-3 p-3">
                    <div class="d-flex align-items-center gap-3">
                      {% if fn.endswith('.pdf') or 'pdf' in mt %}
                        <span class="badge bg-danger-subtle text-danger p-2 rounded fw-bold" style="font-size: 13px; min-width: 52px; text-align: center;">PDF</span>
                      {% elif fn.endswith(('.docx', '.doc')) or 'word' in mt %}
                        <span class="badge bg-primary-subtle text-primary p-2 rounded fw-bold" style="font-size: 13px; min-width: 52px; text-align: center;">DOCX</span>
                      {% elif fn.endswith(('.pptx', '.ppt')) or 'presentation' in mt or 'powerpoint' in mt %}
                        <span class="badge bg-warning-subtle text-warning p-2 rounded fw-bold" style="font-size: 13px; min-width: 52px; text-align: center;">PPTX</span>
                      {% elif fn.endswith(('.mp4', '.webm')) or 'video' in mt %}
                        <span class="badge bg-info-subtle text-info p-2 rounded fw-bold" style="font-size: 13px; min-width: 52px; text-align: center;">VIDEO</span>
                      {% elif fn.endswith(('.zip', '.rar', '.tar', '.gz')) or 'zip' in mt %}
                        <span class="badge bg-secondary-subtle text-secondary p-2 rounded fw-bold" style="font-size: 13px; min-width: 52px; text-align: center;">ZIP</span>
                      {% else %}
                        <span class="badge bg-light text-dark border p-2 rounded fw-bold" style="font-size: 13px; min-width: 52px; text-align: center;">FILE</span>
                      {% endif %}

                      <div>
                        <div class="fw-semibold text-slate-900" style="font-size: 14.5px;">
                          {{ res.label or fa.original_filename or fa.display_name }}
                        </div>
                        <div class="text-caption text-muted d-flex align-items-center gap-2 mt-0.5" style="font-size: 12px;">
                          {% if fa.file_size_bytes %}
                            {% if fa.file_size_bytes >= 1048576 %}
                              <span>{{ (fa.file_size_bytes / 1024 / 1024) | round(2) }} MB</span>
                            {% else %}
                              <span>{{ (fa.file_size_bytes / 1024) | round(1) }} KB</span>
                            {% endif %}
                          {% else %}
                            <span>Dung lượng không xác định</span>
                          {% endif %}
                          <span>•</span>
                          {% if fa.virus_scan_status == 'CLEAN' or fa.virus_scan_status == 'SAFE' %}
                            <span class="text-success"><i class="bi bi-shield-check me-1"></i>Đã quét an toàn</span>
                          {% elif fa.virus_scan_status == 'QUARANTINED' or fa.virus_scan_status == 'INFECTED' %}
                            <span class="text-danger"><i class="bi bi-shield-x me-1"></i>Đã cách ly</span>
                          {% else %}
                            <span class="text-warning"><i class="bi bi-clock-history me-1"></i>{{ fa.virus_scan_status or 'Đang kiểm tra' }}</span>
                          {% endif %}
                        </div>
                      </div>
                    </div>

                    <div class="d-flex align-items-center gap-2 ms-auto ms-sm-0">
                      {% if fn.endswith('.pdf') or 'pdf' in mt or fn.endswith(('.mp4', '.webm')) or 'video' in mt %}
                        <a href="{{ url_for('student.download_student_course_file_route', course_id=course.public_id, asset_id=fa.public_id) }}?disposition=inline" target="_blank" class="btn btn-outline-secondary btn-sm px-2.5 d-inline-flex align-items-center gap-1" title="Xem trực tiếp">
                          <i class="bi bi-eye"></i>
                          <span>Xem</span>
                        </a>
                      {% endif %}
                      <a href="{{ url_for('student.download_student_course_file_route', course_id=course.public_id, asset_id=fa.public_id) }}" class="btn btn-outline-primary btn-sm px-3 d-inline-flex align-items-center gap-1.5 fw-medium" download>
                        <i class="bi bi-download"></i>
                        <span>Tải xuống</span>
                      </a>
                    </div>
                  </div>
                {% endfor %}
              </div>
            {% else %}
              <div class="p-4 text-center bg-light rounded-3 text-muted">
                <i class="bi bi-folder-x fs-2 text-secondary mb-2 d-block"></i>
                Bài học này hiện chưa có tài liệu đính kèm bổ sung. Hãy theo dõi bài giảng và nội dung đọc bên dưới.
              </div>
            {% endif %}
          </div>
        </div>
```

4. **JavaScript Video Engagement Hook**:
Add to `extra_scripts` in `lesson.html`:
```javascript
    // Video progress engagement sync
    const html5Video = document.getElementById('lecture-html5-video');
    let videoProgressFraction = 0.0;
    if (html5Video) {
      html5Video.addEventListener('timeupdate', function () {
        if (html5Video.duration > 0) {
          videoProgressFraction = Math.max(videoProgressFraction, html5Video.currentTime / html5Video.duration);
        }
      });
      html5Video.addEventListener('ended', function () {
        if (typeof window.toggleLessonCompletion === 'function') {
          window.toggleLessonCompletion();
        }
      });
    }
```

---

## 5. Verification Method

To independently verify after Worker M4 applies these changes:
1. **Model & Relationship Verification**:
   ```bash
   python -c "from pwd301.models.course import Lesson; from pwd301.models.file_import import LessonResource; assert hasattr(Lesson, 'resources')"
   ```
2. **Pytest Verification**:
   ```bash
   pytest tests/unit/test_lesson_service.py tests/api/test_lesson_api.py -v
   ```
3. **End-to-End Lesson Media Upload & Viewer Test**:
   - Create a course as Instructor.
   - Post to `/instructor/courses/<course_id>/lessons` with multipart form data including `media_file` (`lecture.mp4` or `slides.pdf`).
   - Query `LessonResource` and verify record exists linked to `FileAsset` and `Lesson`.
   - Access `GET /student/courses/<course_id>/lessons/<lesson_id>` as enrolled student and verify:
     - If video: `<video id="lecture-html5-video">` exists with `?disposition=inline`.
     - Tab 5 renders `📁 Tài liệu đính kèm (1)`.
     - Download link renders `/student/courses/<course_id>/files/<asset_id>/download`.
     - Clicking download returns status 200 with appropriate mime type and binary content.
