# HANDOFF REPORT: Objective R2 — Student Portal Integration Survey & Architecture Mapping

- **Agent**: `teamwork_preview_explorer_survey5_2`
- **Working Directory**: `E:\PWD301\.agents\teamwork_preview_explorer_survey5_2`
- **Target Subsystem**: Student Portal (`src/pwd301/templates/student/`, `src/pwd301/blueprints/student/routes.py`, `frontend-preview/`)
- **Report Date**: 2026-09-16
- **Status**: Comprehensive Analysis Completed (Ready for Milestone 2 Implementation)

---

## 1. Observation

### 1.1 Verified File Paths and Ground Truth Mapping

From direct filesystem inspection of `frontend-preview/` and `src/pwd301/templates/student/`:

| # | Target Flask Template | Source Stitch Directory (`frontend-preview/`) | Route & Method | View Function (`blueprints/student/routes.py`) |
|---|---|---|---|---|
| 1 | `src/pwd301/templates/student/dashboard.html` | `stitch_pwd301_course_management_platform/stitch_pwd301_course_management_platform/pwd301_student_dashboard_variant_1_action_centric_master_flyout_notification_hub/code.html` | `GET /student/dashboard` | `dashboard()` (Line 53) |
| 2 | `src/pwd301/templates/student/my_learning.html` | `stitch_pwd301_course_management_platform/stitch_pwd301_course_management_platform/pwd301_student_course_hub_variant_1_integrated_master_workspace_contextual_tabs/code.html` | `GET /student/my-learning` | `my_learning()` (Line 749) |
| 3 | `src/pwd301/templates/student/course_detail.html` | `stitch_pwd301_course_management_platform/stitch_pwd301_course_management_platform/pwd301_public_catalog_detail_variant_2_full_page_academic_dossier/code.html` (Primary) & `..._variant_1_split_master_detail/code.html` | `GET /student/courses/<course_id>` | `student_course_detail(course_id)` (Line 1071) |
| 4 | `src/pwd301/templates/student/lesson.html` | `stitch_pwd301_course_management_platform/stitch_pwd301_course_management_platform/pwd301_lesson_reader_variant_1_3_column_academic_console_resource_vault/code.html` + Zen Reader tab from `..._variant_2_focus_zen_reader_slideout_companion/code.html` | `GET /student/courses/<course_id>/lessons/<lesson_id>` (Canonical)<br>`GET /student/lessons/<lesson_id>` (302 Redirect) | `get_student_lesson_route()` (Line 280)<br>`lesson_detail_redirect()` (Line 1054) |
| 5 | `src/pwd301/templates/student/assessment_detail.html` (Waiting Room) | `stitch_pwd301_course_management_platform/stitch_pwd301_course_management_platform/pwd301_assessment_hub_waiting_room_variant_2_dedicated_focus_waiting_room/code.html` (Dedicated) & `..._variant_1_dual_surface_master_console/code.html` (Surface B) | `GET /student/assessments/<assessment_id>` | `assessment_detail_view(assessment_id)` (Line 776) |
| 6 | `src/pwd301/templates/student/attempt.html` | `stitch_pwd301_course_management_platform/stitch_pwd301_course_management_platform/pwd301_assessment_attempt_variant_1_master_exam_console_contextual_navigator/code.html` | `GET /student/attempt/<attempt_id>` | `attempt_view(attempt_id)` (Line 64) |
| 7 | `src/pwd301/templates/student/result.html` | `stitch_pwd301_course_management_platform/stitch_pwd301_course_management_platform/pwd301_midterm_assessment_results_clean_minimalist_review_detail_drawer_1/code.html` & `pwd301_quiz_mini_test_results_variant_1_chu_n_i_chi_u_1_1_theo_m_u/code.html` | `GET /student/attempt/<attempt_id>/result` | `attempt_result_view(attempt_id)` (Line 840) |
| 8 | `src/pwd301/templates/student/ai_assistant.html` | `stitch_pwd301_course_management_platform/stitch_pwd301_course_management_platform/pwd301_student_contextual_ai_clean_minimalist_academic_workspace/code.html` | `GET /student/ai-assistant`<br>`POST /student/ai/chat` | `ai_assistant_view()` (Line 869)<br>`student_ai_chat()` (Line 888) |
| 9 | `src/pwd301/templates/student/become_instructor.html` | Card quy chuẩn hồ sơ ứng tuyển giảng viên (Stitch Dashboard Component lines 246-261 & Admin verification cockpit) | `GET /student/become-instructor`<br>`POST /student/become-instructor`<br>`POST /student/become-instructor/cancel` | `become_instructor_get()` (Line 1168)<br>`become_instructor_post()` (Line 1209)<br>`become_instructor_cancel()` (Line 1297) |

*(Note: In addition, `src/pwd301/templates/student/assessments.html` maps to Surface A of `pwd301_assessment_hub_waiting_room_variant_1_dual_surface_master_console` via route `GET /student/assessments`, view function `assessments_view()` line 760).*

---

### 1.2 Route Handlers & Context Variables Catalog

#### Screen 1: `student/dashboard.html`
- **Route**: `GET /student/dashboard`
- **Auth**: `@student_required`
- **Context Variables**:
  - `overview`: Dictionary returned by `get_student_learning_overview(actor, session)`:
    - `active_courses_count`: Integer count of active enrolled courses.
    - `completed_courses_count`: Integer count of completed courses.
    - `overall_average_progress_percent`: Float (0.0 to 100.0).
    - `active_courses`: List of dicts: `[{"course_id": str(UUID), "course_code": str, "course_title": str, "instructor_name": str, "progress_percent": float, "status": "ACTIVE", "lessons_count": int}]`.
    - `upcoming_assessments`: List of dicts: `[{"assessment_id": str(UUID), "attempt_id": str(UUID)|None, "course_id": str, "course_code": str, "course_title": str, "title": str, "assessment_type": str, "open_at": ISO8601|None, "close_at": ISO8601|None, "time_limit_minutes": int}]`.
    - `recent_results`: List of dicts: `[{"attempt_id": str(UUID), "assessment_title": str, "course_code": str, "raw_score": float, "max_score": float, "percent_score": float, "passed": bool, "graded_at": ISO8601}]`.
  - `current_user`: Global User object (`display_name`, `email`, `public_id`, `is_instructor`, `primary_role`).
- **Form Actions & POST Endpoints**: None directly on dashboard. Provides direct navigation URLs:
  - Continue Learning: `url_for('student.course_progress', course_id=c.course_id)`
  - View All Courses: `url_for('student.my_learning')`
  - View Assessments: `url_for('student.assessments_view')`
  - Resume Attempt: `url_for('student.attempt_view', attempt_id=a.attempt_id)`
  - Enter Waiting Room: `url_for('student.assessment_detail_view', assessment_id=a.assessment_id)`
  - View Result: `url_for('student.attempt_result_view', attempt_id=res.attempt_id)`
  - Apply to become Instructor: `url_for('student.become_instructor')`

#### Screen 2: `student/my_learning.html`
- **Route**: `GET /student/my-learning`
- **Auth**: `@student_required`
- **Context Variables**:
  - `overview`: Dictionary with `overview.enrollments` containing all enrollments (`enrollment_id`, `course_id`, `course_code`, `course_title`, `instructor_name`, `progress_percent`, `status`, `lessons_count`).
  - `current_user`: Global User object.
- **Form Actions & POST Endpoints**:
  - Leave Course: `POST /student/courses/<course_id>/leave` with `csrf_token()`.
  - Re-enroll: `POST /student/courses/<course_id>/re-enroll` with `csrf_token()`.
  - Enroll: `POST /student/courses/<course_id>/enroll` with `csrf_token()`.
  - Progress Resumption: `GET /student/courses/<course_id>/progress` (calculates first uncompleted lesson and redirects 302).

#### Screen 3: `student/course_detail.html`
- **Route**: `GET /student/courses/<course_id>`
- **Auth**: `@student_required`
- **Context Variables**:
  - `course`: `Course` model instance (`course_code`, `title`, `description`, `category`, `difficulty`, `capacity`, `learning_objectives_list`, `target_audience`, `completion_requirements_list`, `syllabus_modules`, `owner_instructor`).
  - `enrollment`: `Enrollment` model instance or `None`.
  - `prerequisites`: List of prerequisite `Course` objects.
  - `prereq_items`: List of dicts: `[{"course": Course, "is_satisfied": bool}]`.
  - `is_eligible`: Boolean indicating whether all prerequisite courses are completed.
  - `missing_titles`: List of strings (titles of unsatisfied prerequisites).
  - `active_count`: Integer count of actively enrolled students.
  - `is_full`: Boolean (`active_count >= course.capacity`).
  - `lessons`: List of published `Lesson` objects ordered by position.
- **Form Actions & POST Endpoints**:
  - Enroll Form: `POST {{ url_for('student.enroll', course_id=course.public_id) }}` with `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`.
  - Defensive UX: When `is_eligible == False`, submit button is disabled with text "Chưa đủ điều kiện", and prerequisite alert box displays "Ghi danh bị chặn do chưa đạt điều kiện tiên quyết". When `is_full == True`, displays capacity warning.

#### Screen 4: `student/lesson.html`
- **Route**: `GET /student/courses/<course_id>/lessons/<lesson_id>`
- **Auth**: `@student_required`
- **Context Variables**:
  - `course`: `Course` model instance.
  - `lesson`: `Lesson` model instance (`title`, `position`, `summary`, `markdown_content`, `estimated_duration_minutes`, `public_id`).
  - `progress`: `LessonProgress` model instance or `None` (`completed_at`, `time_spent_seconds`).
  - `all_lessons`: List of all `Lesson` model instances in the course for curriculum sidebar navigation.
  - `lesson_resources`: List of `LessonResource` models associated with this lesson (with eager-loaded `file_asset`).
  - `video_resource`: Single `LessonResource` with video MIME type/extension (or `None`).
  - `doc_resource`: Single `LessonResource` with PDF/Word document type (or `None`).
- **Interactive & Real-time Endpoints**:
  - Lesson Completion Toggle & Heartbeat: `POST /student/lessons/<lesson_id>/progress` with payload `{"completed": bool, "time_spent_seconds": int}` and header `X-CSRFToken`.
  - Authenticated Resource Download / Stream: `GET /student/courses/<course_id>/files/<asset_id>/download?disposition=inline` (or `attachment`).
  - Shortcut Redirect: `GET /student/lessons/<lesson_id>` redirects 302 to canonical course lesson route.

#### Screen 5: `student/assessment_detail.html` (Waiting Room)
- **Route**: `GET /student/assessments/<assessment_id>`
- **Auth**: `@student_required`
- **Context Variables**:
  - `assessment`: `Assessment` model instance (`public_id`, `title`, `description`, `time_limit_minutes`, `passing_percent`, `open_at`, `close_at`, `course_code`, `course`).
  - `active_attempt`: `AssessmentAttempt` model instance (if student currently has an attempt `IN_PROGRESS`).
  - `is_open`: Boolean (`open_at <= now <= close_at`).
  - `is_closed`: Boolean (`close_at is not None and now > close_at`).
  - `seconds_until_open`: Integer (seconds until `open_at`; `<= 0` if already open).
  - `current_timezone`: String (e.g. `'UTC+7 (Hà Nội)'`).
- **Form Actions & POST Endpoints**:
  - Start Exam Form: `POST {{ url_for('student.student_start_assessment', assessment_id=assessment.public_id) }}` with CSRF token `{{ csrf_token() }}`.
  - Returns 302 Redirect to `/student/attempt/<attempt_id>`. (If an attempt is already active, redirects directly to it).
- **Interactive & Real-time Requirements**:
  - Server UTC Countdown: Timer ticks every second down from `seconds_until_open`.
  - When reaching `00:00:00`, changes styling to success, updates hint text to "✓ Đã đến giờ thi!", and unlocks the submit button (`start-exam-btn.disabled = false`).

#### Screen 6: `student/attempt.html`
- **Route**: `GET /student/attempt/<attempt_id>`
- **Auth**: `@student_required`
- **Context Variables**:
  - `delivery`: Dictionary from `get_attempt_delivery()` containing:
    - `attempt_id`: Public UUID string of the attempt.
    - `assessment_title`: Assessment title.
    - `assessment_code`: Course code or exam code.
    - `remaining_seconds`: Server-calculated authoritative countdown seconds until exam time limit expires.
    - `lease_token`: Unique UUID lease token for single-device anti-cheat protection.
    - `lease_epoch`: Integer monotonic version of editing lease.
    - `questions`: List of delivered question items with randomized choices:
      - `attempt_question_id`: UUID string.
      - `question_type`: `'SINGLE_CHOICE'`, `'MULTIPLE_CHOICE'`, `'SHORT_ANSWER'`, `'ESSAY'`.
      - `points`: Decimal / float assigned points.
      - `content`: Question stem / markdown.
      - `choices`: List of `{"choice_key": str, "content": str, "position": int}`.
      - `current_answer`: Previously saved answer payload (for resumption).
- **Interactive & Real-time Endpoints**:
  - Autosave: `POST /student/attempt/<attempt_id>/answers/<attempt_question_id>`
    - Headers: `'Content-Type': 'application/json'`, `'X-CSRFToken': csrfToken`, `'X-Attempt-Lease-Token': leaseToken`.
    - Body: `{"client_sequence": N, "lease_token": leaseToken, "lease_epoch": leaseEpoch, "selected_choice_keys": [...], "answer_text": "..."}`.
  - Lease Renewal: `POST /student/attempt/<attempt_id>/lease/renew`.
  - Lease Takeover (Anti-cheat takeover): `POST /student/attempt/<attempt_id>/lease/takeover` with body `{"force": false}`.
  - Submit Attempt: `POST /student/attempt/<attempt_id>/submit` with body `{"lease_token": leaseToken}`.
  - **CRITICAL JAVASCRIPT REGEX CONTRACT**: Test `test_full_attempt_web_lifecycle` executes `re.search(r'leaseToken = "(.*?)"', resp.data.decode("utf-8"))`. The rendered HTML MUST include `leaseToken = "..."` literally!

#### Screen 7: `student/result.html`
- **Route**: `GET /student/attempt/<attempt_id>/result`
- **Auth**: `@student_required`
- **Context Variables**:
  - `result`: Dictionary returned by `get_attempt_result_for_student()` enriched with:
    - `assessment_title`: str
    - `assessment_code`: str
    - `attempt_number`: int
    - `raw_score`: float | None
    - `max_score`: float
    - `percent_score`: float | None
    - `passed`: bool
    - `status`: `'GRADED'`, `'PENDING_GRADING'`, `'SUBMITTED'`
    - `started_at`: ISO8601 string
    - `submitted_at`: ISO8601 string
    - `is_released`: bool (true if score status is `'RELEASED'`)
- **Navigation**:
  - Back to assessments: `url_for('student.assessments_view')`
  - Back to learning dashboard: `url_for('student.dashboard')`

#### Screen 8: `student/ai_assistant.html`
- **Route**: `GET /student/ai-assistant`
  - Currently in `routes.py`: Returns 302 Redirect to `/student/dashboard` to maintain compatibility with `test_student_ai_assistant_page` while launching the floating octopus mascot assistant.
- **Chat Endpoint**: `POST /student/ai/chat`
  - Headers: `'Content-Type': 'application/json'`, `'X-CSRFToken': csrfToken`.
  - Body: `{"message": str, "course_id": str|None, "lesson_id": str|None, "conversation_id": str|None}`.
  - Response: `{"status": "success", "reply": str, "conversation_id": str, "citations": [...]}`.

#### Screen 9: `student/become_instructor.html`
- **Routes**:
  - `GET /student/become-instructor`
  - `POST /student/become-instructor`
  - `POST /student/become-instructor/cancel`
- **Auth**: `@student_required`
- **Context Variables**:
  - `is_already_instructor`: Boolean (`current_user.is_instructor` or `is_admin`).
  - `application`: `InstructorApplication` model instance if submitted, or `None`.
  - Flash messages.
- **Form Actions**:
  - Submit Application: `POST /student/become-instructor` with fields `institution_name`, `faculty_department`, `institution_email`, `phone_number`, `specialization`, `experience_years`, `current_schedule`, `teaching_evidence`, `employment_contract`, `salary_proof`, `evidence_urls` and `csrf_token()`.
  - Cancel Application: `POST /student/become-instructor/cancel` with `csrf_token()`.

---

### 1.3 Verified Test Suite Baseline
Execution of `pytest` within `.venv`:
1. `tests/api/test_student_portal_ui.py`: **16 passed in 13.38s** (100% pass rate).
2. `tests/api/test_web_ui_flow_fixes.py` (Student flow subset): **6 passed in 6.47s** (100% pass rate).
3. `tests/e2e/test_student_lifecycle_e2e.py`: **1 passed in 0.94s** (100% pass rate).

Every assertion, locator, and contract in these tests has been cataloged to enforce strict zero-regression compliance during Milestone 2.

---

## 2. Logic Chain: Data Binding & UI Architecture

### 2.1 App Shell, Base Layout & Tailwind Integration
1. **Base Inheritance**: All student templates inherit from `base.html` (`{% extends "base.html" %}`). In the new architecture, `base.html` integrates Tailwind CSS CDN (`<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>`), Google Fonts (`Plus Jakarta Sans`, `Inter`, `JetBrains Mono`), and Material Symbols Outlined icons.
2. **Student Sidebar Contract**:
   - Sidebar width is fixed at `276px` (`w-[276px]`).
   - Must contain `id="app-sidebar"` (or `class="app-sidebar"`), `sidebar-toggle-btn`, `sidebar-collapse-btn`, and elements with `data-nav-label` attributes (`"Tổng quan"`, `"Khóa học của tôi"`, `"Bài kiểm tra"`) to fulfill `test_sidebar_sticky_and_collapse_controls`.
3. **Floating AI Octopus Mascot**:
   - Must contain `ai-fab-launcher`, `octopus_mascot.png`, `Trợ lý Bạch Tuộc AI`, `ai-online-badge`, `ai-chat-window`, `ai-chat-expand-btn`, `ai-expand-icon`, `ai-compress-icon`, `data-user-initials`, `data-user-name` in the global shell to fulfill `test_octopus_mascot_ai_launcher_and_dashboard_cleanup`.

### 2.2 Template-by-Template Conversion Strategy

```
[Stitch code.html]
       │
       ├──> Extract Component HTML structure (Bento grids, Tailwind classes, Material Symbols)
       │
       ├──> Replace hardcoded text with dynamic Jinja variables (from routes.py context)
       │
       ├──> Wrap form actions with Flask URL helpers & CSRF token:
       │      <form method="POST" action="{{ url_for(...) }}">
       │      <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
       │
       ├──> Retain exact DOM IDs, CSS helper classes, and JavaScript variables required by tests
       │
       └──> Assemble into src/pwd301/templates/student/<view>.html
```

---

## 3. Caveats & Risks

1. **JavaScript Variable Literal Matching in `attempt.html`**:
   - *Risk*: `tests/api/test_web_ui_flow_fixes.py` line 672 explicitly executes:
     `m = re.search(r'leaseToken = "(.*?)"', resp.data.decode("utf-8"))`
   - *Mitigation*: The rendered JavaScript in `student/attempt.html` must contain the exact string pattern `leaseToken = "{{ delivery.lease_token }}";`. Do not rename this variable or convert it into a pure dataset attribute without keeping the script declaration.
2. **AI Assistant Route Dual-Behavior (`ai_assistant.html`)**:
   - *Risk*: `tests/api/test_student_portal_ui.py` line 159 asserts that `GET /student/ai-assistant` returns `302` redirect to `/student/dashboard`. If `/student/ai-assistant` directly returns `200` rendering `student/ai_assistant.html`, `test_student_ai_assistant_page` will fail.
   - *Mitigation*:
     - Provide the new full-page Stitch workspace `student/ai_assistant.html` accessible via `GET /student/ai-assistant?workspace=1` or `/student/ai-workspace`.
     - When accessed as plain `GET /student/ai-assistant` without query flags, preserve the 302 redirect to `/student/dashboard` with an auto-launching prompt parameter so the floating AI widget pops up, satisfying the test contract.
3. **Prerequisite Warning Text Exact Matches**:
   - *Risk*: `test_course_detail_prerequisite_blocking_and_flash` asserts exact substrings in `course_detail.html`:
     - `"Ghi danh bị chặn do chưa đạt điều kiện tiên quyết"`
     - `"Chưa đủ điều kiện"`
     - Flash text containing `"Không thể ghi danh"` and `"tiên quyết"`.
   - *Mitigation*: In `student/course_detail.html`, preserve the exact warning strings inside the defensive banners.
4. **Lesson Reader DOM Element Identifiers**:
   - *Risk*: `test_enrollment_and_lesson_reader_flow` tests for `"lesson-progress-badge"` and `"/student/lessons/"` in `student/lesson.html`.
   - *Mitigation*: Maintain `<div class="lesson-progress-badge">` and lesson link formats `<a href="/student/courses/.../lessons/...">` with fallback references.
5. **Autosave Sequence Monotonicity**:
   - *Risk*: `TestAutosaveSequenceKeyCompatibility` validates that `save_attempt_answer` handles `client_sequence` monotonically without regressions.
   - *Mitigation*: Maintain the client-side `clientSequence = ++clientSequence` counter in the autosave fetch payload.

---

## 4. Concrete Implementation Plan for Milestone 2

### Phase 1: Core Navigation & Dashboard
1. **Screen 1 (`student/dashboard.html`)**:
   - Integrate `pwd301_student_dashboard_variant_1_action_centric_master_flyout_notification_hub`.
   - Bind `overview.active_courses`, `overview.active_courses_count`, `overview.completed_courses_count`, `overview.upcoming_assessments`, `overview.recent_results`.
   - Implement action-centric hero continue card and Flyout Notification Hub.
   - Embed Become Instructor invitation card for non-instructors.
   - Run `pytest tests/api/test_student_portal_ui.py -k "dashboard"` to verify.

### Phase 2: Course Catalog & Study Hub
2. **Screen 2 (`student/my_learning.html`)**:
   - Integrate `pwd301_student_course_hub_variant_1_integrated_master_workspace_contextual_tabs`.
   - Bind `overview.enrollments` with active/completed filters, course search bar, and progress metrics.
   - Connect leave course modal with `POST /student/courses/<course_id>/leave`.
3. **Screen 3 (`student/course_detail.html`)**:
   - Integrate `pwd301_public_catalog_detail_variant_2_full_page_academic_dossier`.
   - Bind `course.learning_objectives_list`, `target_audience`, `completion_requirements_list`, `prereq_items`, and sticky enrollment card.
   - Preserve prerequisite blocker banner and disabled enrollment button.

### Phase 3: Interactive Lesson Reader & Zen Workspace
4. **Screen 4 (`student/lesson.html`)**:
   - Integrate `pwd301_lesson_reader_variant_1_3_column_academic_console_resource_vault` (3 columns: Curriculum Outline, Main Reading & Video Stage, Resource Vault).
   - Integrate Zen Reader mode from `variant_2_focus_zen_reader_slideout_companion` as a toggleable distraction-free view (`#zen-reader-mode`).
   - Preserve HTML5 video player, PDF iframe viewer, and ClamAV virus scan status indicators (`CLEAN`, `SAFE`, `QUARANTINED`).
   - Bind progress completion toggle to `POST /student/lessons/<lesson_id>/progress`.

### Phase 4: Assessment Lifecycle (Waiting Room, Attempt, Results)
5. **Screen 5 (`student/assessment_detail.html`)**:
   - Integrate `pwd301_assessment_hub_waiting_room_variant_2_dedicated_focus_waiting_room`.
   - Connect real-time UTC server countdown timer, auto-enabling `start-exam-btn` when `seconds_until_open <= 0`.
   - Bind start exam form to `POST /student/assessments/<assessment_id>/start` with CSRF token.
6. **Screen 6 (`student/attempt.html`)**:
   - Integrate `pwd301_assessment_attempt_variant_1_master_exam_console_contextual_navigator`.
   - Connect central question canvas (single choice, multiple choice, short answer, essay) and question navigator palette.
   - Preserve `leaseToken = "..."` variable, debounced autosave (`POST /student/attempt/<id>/answers/<aq_id>`), lease takeover (`POST /student/attempt/<id>/lease/takeover`), and submit modal (`POST /student/attempt/<id>/submit`).
7. **Screen 7 (`student/result.html`)**:
   - Integrate `pwd301_midterm_assessment_results_clean_minimalist_review_detail_drawer_1`.
   - Bind `result.raw_score`, `result.max_score`, `result.percent_score`, `result.passed`, score release policy notice, and review breakdown.

### Phase 5: AI Workspace & Instructor Application
8. **Screen 8 (`student/ai_assistant.html`)**:
   - Implement `pwd301_student_contextual_ai_clean_minimalist_academic_workspace` for full-page AI workspace while preserving redirect on default GET for test compatibility.
   - Bind suggestion chips and chat interface to `POST /student/ai/chat`.
9. **Screen 9 (`student/become_instructor.html`)**:
   - Upgrade nomination card layout with Tailwind tokens.
   - Bind form fields, pending review card, and cancel action (`POST /student/become-instructor/cancel`).

---

## 5. Verification Method

To independently verify this survey and future implementations:

1. **Automated Unit & UI Tests**:
   ```powershell
   .venv\Scripts\python.exe -m pytest tests/api/test_student_portal_ui.py -v
   ```
   *Expected*: All 16 tests PASS.

2. **Web UI Flow & Anti-Cheat Regression Tests**:
   ```powershell
   .venv\Scripts\python.exe -m pytest tests/api/test_web_ui_flow_fixes.py -k "Student or Attempt or Lesson or Autosave or Assessment" -v
   ```
   *Expected*: All 6 tests PASS.

3. **End-to-End Lifecycle Scenario**:
   ```powershell
   .venv\Scripts\python.exe -m pytest tests/e2e/test_student_lifecycle_e2e.py -v
   ```
   *Expected*: All tests PASS.

4. **Static Code Quality Checks**:
   ```powershell
   .venv\Scripts\python.exe scripts/repo_check.py
   .venv\Scripts\python.exe -m ruff check src tests
   .venv\Scripts\python.exe -m mypy src
   ```

5. **Invalidation Conditions**:
   - Any test failure in `test_student_portal_ui.py` or `test_web_ui_flow_fixes.py`.
   - Missing `leaseToken` regex match in `student/attempt.html`.
   - Unmet prerequisite message mismatch in `student/course_detail.html`.
   - Missing `lesson-progress-badge` or `app-sidebar` elements.
