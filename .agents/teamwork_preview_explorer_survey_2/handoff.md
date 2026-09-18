# Handoff Report: R2 Deep Instructor Course Customization & Dynamic Student View

**Agent**: `teamwork_preview_explorer` (Survey Explorer 2)  
**Date**: 2026-09-14  
**Working Directory**: `e:\PWD301\.agents\teamwork_preview_explorer_survey_2`  
**Mission**: Comprehensive codebase and architectural survey for Requirement R2:
- Learning objectives & skills gained (Mục tiêu và kỹ năng).
- Target audience & completion requirements (Mô tả và yêu cầu môn học).
- Course prerequisites (Điều kiện tiên quyết) with cycle prevention, using `course_prerequisites` schema.
- Curriculum & syllabus structure (Đề cương chương trình đào tạo).
- Dynamic rendering in student course detail page (`student/course_detail.html`) eliminating all hardcoded placeholder text.

---

## 1. Observation

### 1.1 Model & Schema Current State
1. **`Course` Model (`src/pwd301/models/course.py:35-150`) & Table `courses` (`docs/database/PWD301_DATABASE_ARCHITECTURE/sql/002_course_learning.sql:10-44`)**:
   - Existing fields:
     - `id`: `BIGINT IDENTITY(1,1) PRIMARY KEY`
     - `public_id`: `UNIQUEIDENTIFIER NOT NULL DEFAULT NEWSEQUENTIALID()`
     - `course_code` & `course_code_normalized`: `NVARCHAR(50)`
     - `title` & `title_normalized`: `NVARCHAR(200)`
     - `description`: `NVARCHAR(MAX) NULL`
     - `category`: `NVARCHAR(100) NULL`
     - `difficulty`: `VARCHAR(20) NULL` (`BEGINNER`, `INTERMEDIATE`, `ADVANCED`)
     - `owner_instructor_id`: `BIGINT NULL FK users(id)`
     - `thumbnail_file_asset_id`: `BIGINT NULL FK file_assets(id)`
     - `status`: `VARCHAR(32) NOT NULL DEFAULT 'DRAFT'`
     - `capacity`: `INT NULL`
     - `storage_quota_bytes`: `BIGINT NULL`
     - `published_at`, `approved_at`, `approved_by_user_id`, `first_student_enrolled_at`, `created_at`, `updated_at`, `row_version`, `deleted_at`, `restore_until`, `deleted_by_user_id`.
   - **Missing Fields**:
     - `learning_objectives`: **NOT present**.
     - `target_audience`: **NOT present**.
     - `completion_requirements`: **NOT present** on `Course`.

2. **`CoursePrerequisite` Model (`src/pwd301/models/course.py:215-262`) & Table `course_prerequisites` (`002_course_learning.sql:57-68`)**:
   - Composite Primary Key: `(course_id, prerequisite_course_id)`.
   - Foreign Keys:
     - `course_id REFERENCES courses(id)`
     - `prerequisite_course_id REFERENCES courses(id)`
     - `created_by_user_id REFERENCES users(id)`
   - Check Constraint `ck_course_prerequisites_1`: `course_id <> prerequisite_course_id`.
   - Index `ix_course_prereq_reverse`: `(prerequisite_course_id, course_id)`.
   - Relationships on `Course`:
     - `prerequisite_links`: Links where `Course` is the dependent course (`course_id`).
     - `dependent_links`: Links where `Course` is the prerequisite (`prerequisite_course_id`).

3. **`CourseCompletionRule` Model (`src/pwd301/models/course.py:263-315`) & Table `course_completion_rules` (`002_course_learning.sql:70-83`)**:
   - Primary Key: `course_id REFERENCES courses(id)`.
   - Fields:
     - `require_all_required_lessons`: `BIT NOT NULL DEFAULT 1`
     - `require_required_assessments`: `BIT NOT NULL DEFAULT 1`
     - `minimum_progress_percent`: `DECIMAL(5,2) NULL` (0..100)
     - `updated_by_user_id`, `updated_at`, `row_version`.

4. **`Lesson` Model (`src/pwd301/models/course.py:388-510`) & Table `lessons` (`002_course_learning.sql:111-143`)**:
   - Fields: `id`, `public_id`, `course_id`, `title`, `summary`, `markdown_content`, `position`, `estimated_duration_minutes`, `minimum_completion_seconds`, `viewed_fraction_required`, `status`.
   - Note: There is **NO `course_sections` table** in the canonical architecture (confirmed by `scripts/repo_check.py` 71 tables and `002_course_learning.sql`). Lessons are flatly ordered within a course by `position` (1..N).

### 1.2 Service Layer Current State
1. **Course Service (`src/pwd301/services/course_service.py:349-450`)**:
   - `update_course(actor, course_id, data, session)`:
     - Whitelist of updatable fields: only `title`, `description`, `category`, `difficulty`, `capacity`, `storage_quota_bytes`, `thumbnail_file_asset_id`.
     - Fields `learning_objectives`, `target_audience`, `completion_requirements` are **currently ignored / dropped** by the whitelist.
2. **Enrollment Service (`src/pwd301/services/enrollment_service.py:636-812`)**:
   - `add_course_prerequisite(actor, course_id, prerequisite_course_id, session)`:
     - Enforces `require_course_manager(actor, course_id)`.
     - Checks self-reference (`course.id == prereq_course.id`).
     - Implements Algorithm 03 DAG cycle detection using BFS graph reachability: traverses from `prereq_course.id` to check if `course.id` is reachable. If reachable, raises `PrerequisiteCycleError`.
     - Records append-only `AuditEvent(action="ADD_PREREQUISITE")`.
   - `remove_course_prerequisite(actor, course_id, prerequisite_course_id, session)`:
     - Removes link, records `AuditEvent(action="REMOVE_PREREQUISITE")`.
   - `get_course_prerequisites(course_id, session)`:
     - Returns `list[Course]` that are direct prerequisites of `course_id`.
   - `check_prerequisites_met(student_user_id, course_id, session)`:
     - Validates student's durable `CourseCompletionSummary` for all prerequisites.

### 1.3 Blueprints & Web Routes Current State
1. **Instructor Blueprint (`src/pwd301/blueprints/instructor/routes.py`)**:
   - `manage_course_hub` (lines 258-324):
     - Queries `lessons`, `file_assets`, `assessments`, `questions_count`.
     - **Does NOT query or pass** `prerequisites` to `instructor/course_manage.html`.
     - **Does NOT query or pass** `available_courses` (candidate prerequisites) to the template.
   - `update_course_route` (lines 327-368):
     - Handles `POST /courses/<course_id>`, delegates to `update_course()`.
   - `list_course_prerequisites_route` (line 856), `add_course_prerequisite_route` (line 867), `remove_course_prerequisite_route` (line 902):
     - Exist as JSON API routes under `/courses/<course_id>/prerequisites`.
     - **Do NOT support HTML form submissions** (they only return `jsonify(...)` and do not flash/redirect to `manage_course_hub`).
2. **Student Blueprint (`src/pwd301/blueprints/student/routes.py:994-1074`)**:
   - `student_course_detail(course_id)`:
     - Resolves `course`, `enrollment`, `prerequisites`, `prereq_items`, `is_eligible`, `active_count`, `is_full`, `lessons`.
     - Passes these into `student/course_detail.html`.

### 1.4 Templates Current State & Hardcoded Content
1. **`src/pwd301/templates/instructor/course_manage.html:668-718`**:
   - Tab 5 (`active_tab == 'settings'`):
     - Contains form with only `title`, `description`, `category`, `difficulty`, `capacity`.
     - **Zero UI** for `learning_objectives`, `target_audience`, `completion_requirements`.
     - **Zero UI** for managing prerequisites (`course_prerequisites`).
2. **`src/pwd301/templates/student/course_detail.html`**:
   - Lines 121-137: Hardcoded 4 learning objective items:
     - *"Nắm vững nguyên lý và kiến trúc phân tầng chuẩn mực trong phát triển ứng dụng Web an toàn."*
     - *"Làm chủ kỹ thuật thiết kế CSDL, bảo toàn tính toàn vẹn và tối ưu truy vấn trên SQL Server."*
     - *"Triển khai cơ chế xác thực, phân quyền đa cấp RBAC và phòng chống các lỗ hổng OWASP hàng đầu."*
     - *"Sẵn sàng tham gia các dự án thực tế, vượt qua các kỳ kiểm tra đánh giá năng lực học kỳ."*
   - Lines 196-200: Hardcoded target audience:
     - *"Sinh viên chuyên ngành Kỹ thuật Phần mềm, Hệ thống Thông tin và An toàn Thông tin."*
     - *"Lập trình viên muốn củng cố kiến thức chuyên sâu về kiến trúc máy chủ và cơ sở dữ liệu."*
   - Lines 201-205: Hardcoded completion requirement paragraph:
     - *"Sinh viên cần đạt tỷ lệ hoàn thành tối thiểu 80% khối lượng bài giảng và vượt qua các bài thi kiểm tra giữa kỳ, thực hành lab để đủ điều kiện xét hoàn thành môn."*
   - Line 93: Hardcoded rating *"Đánh giá: 4.9 / 5.0"*.
   - Line 105: Hardcoded language *"Ngôn ngữ: Tiếng Việt"*.
   - Line 145: Static caption *"Đầy đủ tài liệu & mã nguồn đi kèm"*.

---

## 2. Logic Chain

### 2.1 Storage & Schema Logic
1. *Premise*: R2 requires deep instructor customization of:
   - Learning objectives & skills gained
   - Target audience & completion requirements
   - Course prerequisites
   - Curriculum & syllabus structure
2. *Premise*: In `courses` table, only `description` is currently available for text. Storing objectives, audience, and completion rules bundled inside `description` would require arbitrary text delimiters, making structured editing and rendering fragile.
3. *Premise*: The canonical database architecture `PWD301_DATABASE_ARCHITECTURE` uses Microsoft SQL Server `NVARCHAR(MAX)` for long-form / JSON text.
4. *Inference*: The clean, robust, and extensible approach is to add three columns to `courses`:
   - `learning_objectives`: `NVARCHAR(MAX) NULL`
   - `target_audience`: `NVARCHAR(MAX) NULL`
   - `completion_requirements`: `NVARCHAR(MAX) NULL`
5. *Inference*: On the `Course` model, implement helper properties:
   - `learning_objectives_list`: Parses JSON array if valid, or splits multiline text into `list[str]`.
   - `target_audience_list`: Parses JSON array if valid, or splits multiline text into `list[str]`.
   This ensures that whether the instructor enters one item per line in a textarea or submits structured JSON via an API/AJAX call, the template consistently receives a sanitized list of strings.

### 2.2 Prerequisite Management & Cycle Detection Logic
1. *Premise*: The schema `course_prerequisites` already exists and Algorithm 03 DAG cycle detection is already implemented in `enrollment_service.py:add_course_prerequisite()`.
2. *Premise*: Instructors currently have NO way to manage prerequisites through the Web UI (`course_manage.html`), and the existing route `add_course_prerequisite_route` only returns JSON.
3. *Inference*:
   - In `instructor/routes.py`, enhance `manage_course_hub` to query:
     a) `current_prereqs = get_course_prerequisites(course.id, session=db.session)`
     b) `available_courses`: Published/approved courses excluding `course.id` and existing prerequisites.
   - Update `add_course_prerequisite_route` and `remove_course_prerequisite_route` to support both JSON and HTML form submissions:
     - On HTML POST: If cycle detected (`PrerequisiteCycleError`), flash danger message and redirect back to `manage_course_hub(course_id, tab="settings")`.
     - If success: flash success message and redirect back.
   - In `instructor/course_manage.html` (Settings tab), render a dedicated "Môn học tiên quyết (Prerequisites)" section with:
     - Current prerequisite badges with remove buttons.
     - A dropdown selector of `available_courses` with an "Thêm điều kiện tiên quyết" button.

### 2.3 Dynamic Student Course Detail View Logic
1. *Premise*: In `student/course_detail.html`, lines 121-137, 196-205 contain static Vietnamese placeholder strings.
2. *Inference*:
   - In "Mục tiêu và kỹ năng": Loop over `course.learning_objectives_list`. If empty, render a clean default derived from course category and title, with 0 hardcoded static course-specific claims.
   - In "Đối tượng tham gia": Loop over `course.target_audience_list`. Only display the block if items exist.
   - In "Quy định và điều kiện hoàn thành": Render `course.completion_requirements` (if set) and dynamic bullets derived from `course.completion_rule`:
     - Minimum progress percentage (e.g. `{{ course.completion_rule.minimum_progress_percent }}%`).
     - Required lessons rule (`require_all_required_lessons`).
     - Required assessments rule (`require_required_assessments`).
   - In Curriculum/Syllabus: Render dynamic lesson count, dynamic lessons sequence from `lessons`, dynamic lesson summaries, and attached resources indicator.

---

## 3. Caveats

1. **Database Migration Synchronization**:
   - `scripts/repo_check.py` asserts that the canonical SQL Server DDL contains 71 `CREATE TABLE` statements. Adding columns to `courses` does not change the table count.
   - However, according to AGENTS.md rule 6, all DB changes must be accompanied by an Alembic migration (`0005_add_course_customization_fields.py`) and reflected in `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/002_course_learning.sql` and `05_DATA_DICTIONARY_COURSE.md` to maintain zero drift.
2. **Course Sections (Modules)**:
   - There is no `course_sections` table in PWD301 canonical DDL. "Curriculum & Syllabus Structure" refers to the ordered sequence of `Lesson` objects (positions 1..N) within a course. Introducing a new `course_sections` table would violate the 71-table constraint.
3. **Change Requests for Published Courses**:
   - Under `03_COURSE_MANAGEMENT.md`, modifying material properties of an already PUBLISHED course requires review (`course_change_requests`) unless modified by Admin or treated as non-structural metadata update. Course settings updates currently allow direct metadata edits for DRAFT/PUBLISHED with audit logging (`COURSE_UPDATED`).

---

## 4. Conclusion

The implementation path for Requirement R2 consists of five concrete, cohesive steps:

### Step 1: Database & Model Expansion
1. Create Alembic migration `0005_add_course_customization_fields.py`:
   - Add `learning_objectives` (`NVARCHAR(MAX)` NULL).
   - Add `target_audience` (`NVARCHAR(MAX)` NULL).
   - Add `completion_requirements` (`NVARCHAR(MAX)` NULL).
2. Update `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/002_course_learning.sql` and `05_DATA_DICTIONARY_COURSE.md`.
3. In `src/pwd301/models/course.py`:
   - Add columns `learning_objectives`, `target_audience`, `completion_requirements` to `Course`.
   - Add helper properties `learning_objectives_list` and `target_audience_list` on `Course`.

### Step 2: Course Service & Whitelist Expansion
1. In `src/pwd301/services/course_service.py:update_course`:
   - Expand updatable fields to include `learning_objectives`, `target_audience`, and `completion_requirements`.
   - Sanitize and strip strings before updating.
   - Record them in `before_state` and `after_state` for `AuditEvent` logging.

### Step 3: Instructor Blueprint & Route Enhancements
1. In `src/pwd301/blueprints/instructor/routes.py:manage_course_hub`:
   - Fetch `current_prereqs = get_course_prerequisites(course.id, session=db.session)`.
   - Fetch `available_courses`: active courses excluding `course.id` and existing prerequisites.
   - Fetch `completion_rule = get_or_create_default_completion_rule(course.id, session=db.session)`.
   - Pass `prerequisites`, `available_courses`, `completion_rule` to `instructor/course_manage.html`.
2. In `add_course_prerequisite_route` (`/courses/<course_id>/prerequisites`):
   - Add dual support for HTML form POST: handle `PrerequisiteCycleError` with `flash(..., "danger")` and redirect to `manage_course_hub(course_id, tab="settings")`.
   - On success, flash message and redirect.
3. In `remove_course_prerequisite_route` (`/courses/<course_id>/prerequisites/<prereq_id>/delete`):
   - Add HTML form POST redirect with flash confirmation.

### Step 4: Template Overhaul
1. In `src/pwd301/templates/instructor/course_manage.html`:
   - In Tab 5 (`tab == 'settings'`):
     - Add textarea for "Mục tiêu và kỹ năng (Learning Objectives)" (one item per line).
     - Add textarea for "Đối tượng tham gia (Target Audience)" (one item per line).
     - Add textarea for "Mô tả quy định hoàn thành (Completion Requirements)".
     - Add Course Completion Rule inputs (`minimum_progress_percent`, `require_all_required_lessons`, `require_required_assessments`).
     - Add dedicated "Môn học tiên quyết (Prerequisites)" management section with list of current prerequisites (with remove buttons) and "+ Thêm môn tiên quyết" select box.
2. In `src/pwd301/templates/student/course_detail.html`:
   - Replace lines 115-138 with dynamic iteration over `course.learning_objectives_list`.
   - Replace lines 196-205 with dynamic `course.target_audience_list` and dynamic completion rules from `course.completion_requirements` and `course.completion_rule`.
   - Eliminate hardcoded ratings and strings; ensure 100% data-driven rendering.

### Step 5: Test Suite Expansion
1. Unit tests in `tests/unit/test_course_service.py`:
   - Test saving and retrieving `learning_objectives`, `target_audience`, and `completion_requirements`.
   - Test list-parsing property methods.
2. Integration / Web flow tests in `tests/api/test_instructor_course_web_flow.py`:
   - Instructor updates course customization fields via web POST.
   - Instructor adds valid prerequisite via web form.
   - Instructor attempts to add cyclic prerequisite -> verify 400/flash error with cycle detection message.
   - Student visits course detail -> verify customized objectives, audience, and completion rules are rendered in the HTML body.

---

## 5. Verification Method

To independently verify these findings:

1. **Verify Existing Prerequisite Cycle Detection**:
   ```powershell
   pytest tests/unit/test_enrollment_service.py -k "test_prerequisite_dag_cycle_detection" -v
   ```
2. **Inspect Current Course Manage Form**:
   ```powershell
   python -c "
   with open('src/pwd301/templates/instructor/course_manage.html', encoding='utf-8') as f:
       content = f.read()
       print('learning_objectives in manage:', 'learning_objectives' in content)
       print('prerequisites in manage:', 'prerequisite' in content)
   "
   ```
   *Expected Output*: Both return `False`.
3. **Inspect Hardcoded Items in Student Course Detail**:
   ```powershell
   python -c "
   with open('src/pwd301/templates/student/course_detail.html', encoding='utf-8') as f:
       content = f.read()
       print('Hardcoded objective present:', 'Nắm vững nguyên lý' in content)
       print('Hardcoded audience present:', 'Sinh viên chuyên ngành Kỹ thuật' in content)
   "
   ```
   *Expected Output*: Both return `True`.
4. **Run Static Repository Check**:
   ```powershell
   python scripts/repo_check.py
   ```
   *Expected Output*: `[PASS] Repository contract check complete`.
