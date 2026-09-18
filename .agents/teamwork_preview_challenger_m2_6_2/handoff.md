# HANDOFF REPORT: Milestone 2 — Empirical Challenge of Student Portal Templates

- **Agent**: `teamwork_preview_challenger_m2_6_2`
- **Working Directory**: `E:\PWD301\.agents\teamwork_preview_challenger_m2_6_2`
- **Parent**: `teamwork_preview_orchestrator_6` (Conversation ID: `ebbe1ae6-5ba3-416c-a025-e0178c543130`)
- **Target Subsystem**: Student Portal Templates (`src/pwd301/templates/student/`)
- **Worker Handoff Challenged**: `E:\PWD301\.agents\teamwork_preview_worker_m2_s5\handoff.md`
- **Final Verdict**: **REQUEST_CHANGES** (1 Critical Regression, 1 Functional Defect)

---

## 1. Observation

### 1.1 Empirical Defect 1: Jinja2 BuildError (HTTP 500) on Student Lesson Page
Direct execution of web client GET to `/student/courses/<course_id>/lessons/<lesson_id>` for an enrolled student on any lesson with an attached file resource (e.g. CS101 Lesson 1) results in an unhandled server crash:

```text
[2026-09-16 13:00:05,218] ERROR in __init__: Unhandled Exception: Could not build url for endpoint 'student.download_lesson_file' with values ['asset_id', 'course_id']. Did you mean 'student.download_student_course_file_route' instead?
Traceback (most recent call last):
  ...
  File "E:\PWD301\src\pwd301\templates\student\lesson.html", line 202, in block 'content'
    <a href="{{ url_for('student.download_lesson_file', course_id=course.public_id, asset_id=asset.public_id) }}?disposition=attachment" ...
  File "E:\PWD301\.venv\Lib\site-packages\werkzeug\routing\map.py", line 901, in build
    raise BuildError(endpoint, values, method, self)
werkzeug.routing.exceptions.BuildError: Could not build url for endpoint 'student.download_lesson_file' with values ['asset_id', 'course_id']. Did you mean 'student.download_student_course_file_route' instead?
STATUS: 500
```

- **Defective Lines in `src/pwd301/templates/student/lesson.html`**:
  - Line 84:
    `<source src="{{ url_for('student.download_lesson_file', course_id=course.public_id, asset_id=video_resource.file_asset.public_id) }}?disposition=inline" type="{{ video_resource.file_asset.mime_type or 'video/mp4' }}">`
  - Line 202:
    `<a href="{{ url_for('student.download_lesson_file', course_id=course.public_id, asset_id=asset.public_id) }}?disposition=attachment" ...>`
  - Line 207:
    `<a href="{{ url_for('student.download_lesson_file', course_id=course.public_id, asset_id=asset.public_id) }}?disposition=inline" target="_blank" ...>`
- **Actual Route Definition in `src/pwd301/blueprints/student/routes.py` (Line 1336-1339)**:
  ```python
  @student_bp.route("/courses/<course_id>/files/<asset_id>/download", methods=["GET"])
  @student_bp.route("/files/<asset_id>/download", methods=["GET"])
  @student_required
  def download_student_course_file_route(asset_id: str, course_id: str | None = None) -> Any:
  ```
  The endpoint registered by Flask is `student.download_student_course_file_route`, NOT `student.download_lesson_file`.

### 1.2 Empirical Defect 2: ClamAV Clean Scan Badge Attribute Mismatch
- **Inspection in `src/pwd301/templates/student/lesson.html` (Line 194)**:
  ```jinja2
  {% if asset.scan_status == 'SAFE' or asset.scan_status == 'CLEAN' %}
    <span class="text-emerald-600 font-semibold">• ClamAV: Sạch</span>
  {% endif %}
  ```
- **Inspection in `src/pwd301/models/file_import.py` (Line 275)**:
  `FileAsset` model defines `@property def virus_scan_status(self) -> str:` which evaluates to `'CLEAN'`, `'INFECTED'`, `'PENDING'`, `'BLOCKED'`. It has **no** attribute named `scan_status`.
- **Consequence**: `asset.scan_status` evaluates to `Undefined` in Jinja2, preventing the clean scan badge (`• ClamAV: Sạch`) from ever rendering on verified clean assets.

### 1.3 Baseline and Stress Test Execution Results
Executed in project environment `.venv`:
1. `tests/api/test_student_portal_ui.py`: **16/16 PASSED** in 13.72s.
2. `tests/e2e/test_student_lifecycle_e2e.py`: **1/1 PASSED** in 0.98s.
3. `tests/api/test_student_templates_stress_challenger.py`: **9/9 PASSED** in 8.05s.
   - Verified empty course enrollments (`overview.enrollments = []`) renders clean empty state.
   - Verified 0% progress displays without division-by-zero or NaN.
   - Verified prerequisite DAG blocks ineligible students with exact Vietnamese defensive strings (`"Ghi danh bị chặn do chưa đạt điều kiện tiên quyết"` and `"Chưa đủ điều kiện"`).
   - Verified assessment waiting room states (`is_open == False`, `is_closed == True`).
   - Verified empirical reproduction of Jinja2 `BuildError` (HTTP 500) and scan status attribute mismatch.

---

## 2. Logic Chain

1. **Observation 1.1** demonstrates that `src/pwd301/templates/student/lesson.html` (lines 84, 202, 207) explicitly constructs URLs targeting `student.download_lesson_file`.
2. Inspection of `src/pwd301/blueprints/student/routes.py` (line 1339) proves no endpoint named `download_lesson_file` exists on `student_bp`; the view function is named `download_student_course_file_route`.
3. Flask's URL routing engine raises `werkzeug.routing.exceptions.BuildError` whenever `url_for` cannot resolve an endpoint.
4. When an enrolled student requests the HTML representation of a lesson that has an attached document or video (such as CS101 Lesson 1 in demo seed), line 202 of `lesson.html` triggers this exception during template rendering, resulting in an immediate **HTTP 500 Internal Server Error**.
5. The worker's previous test suite (`test_student_portal_ui.py`) missed this defect because `test_student_lesson_shortcut_redirect` and `test_smart_lesson_resumption_redirects_to_uncompleted_lesson` only tested 302 redirects with `follow_redirects=False` and never rendered `lesson.html` with an enrolled student and real attachments.
6. **Observation 1.2** demonstrates that `lesson.html` tests `asset.scan_status` while the model only provides `virus_scan_status`.
7. Because of the critical HTTP 500 crash in production student flows, the milestone cannot be approved in its current state.

---

## 3. Caveats

- All other 9 student templates (`dashboard.html`, `my_learning.html`, `course_detail.html`, `assessment_detail.html`, `attempt.html`, `result.html`, `ai_assistant.html`, `become_instructor.html`, `assessments.html`) render cleanly across tested edge cases.
- Per the role constraints of Empirical Challenger, no production implementation files in `src/` were altered. The fix must be applied by a worker.

---

## 4. Conclusion & Actionable Recommendations

**Verdict**: **REQUEST_CHANGES**

### Required Worker Fixes:
1. **Fix URL Endpoint in `src/pwd301/templates/student/lesson.html`**:
   Replace:
   `url_for('student.download_lesson_file', course_id=course.public_id, asset_id=...)`
   With:
   `url_for('student.download_student_course_file_route', course_id=course.public_id, asset_id=...)`
   (or add an endpoint alias `endpoint="download_lesson_file"` in `src/pwd301/blueprints/student/routes.py`).
2. **Fix Virus Scan Status in `src/pwd301/templates/student/lesson.html` (Line 194)**:
   Replace:
   `{% if asset.scan_status == 'SAFE' or asset.scan_status == 'CLEAN' %}`
   With:
   `{% if asset.virus_scan_status == 'CLEAN' or asset.scan_status == 'SAFE' %}`

---

## 5. Verification Method

To independently verify these findings:

1. **Execute Empirical Challenge Test Suite**:
   ```powershell
   .venv\Scripts\python.exe -m pytest tests/api/test_student_templates_stress_challenger.py -v
   ```
   *Expected*: All 9 tests pass, specifically confirming the 500 error on `test_lesson_file_download_endpoint_build_error_in_template`.

2. **Run Standard UI Regression Suites**:
   ```powershell
   .venv\Scripts\python.exe -m pytest tests/api/test_student_portal_ui.py -v
   .venv\Scripts\python.exe -m pytest tests/e2e/test_student_lifecycle_e2e.py -v
   ```

3. **Verify Line Formatting & Static Checks**:
   ```powershell
   .venv\Scripts\python.exe -m ruff check tests/api/test_student_templates_stress_challenger.py
   ```
