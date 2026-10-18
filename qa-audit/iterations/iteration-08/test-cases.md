# Test Case Specifications — Iteration 08: Multi-Step Business Workflows: Course Lifecycle & Staging Drafts

## Test Case Matrix

| ID | Title | Priority | Target Subsystem | Expected Outcome |
| :--- | :--- | :--- | :--- | :--- |
| `TC-IT08-001` | Pre-Flight Publish Readiness Validation | Critical | Instructor Authoring API | HTTP 400 rejection listing missing criteria; course remains DRAFT |
| `TC-IT08-002` | Complete Course Submission & Studio Lock | High | Course Workflow Engine | Transitions to SUBMITTED_FOR_REVIEW; Studio locks editing |
| `TC-IT08-003` | Admin Governance Queue & Inspection Dossier | High | Admin Governance SPA | Course appears in queue; full inspection dossier loads |
| `TC-IT08-004` | Course Approval & Publication Gate | Critical | Admin Review / Catalog | Transitions to APPROVED then PUBLISHED; visible in student catalog |
| `TC-IT08-005` | Unified Staging Draft Invariant | Critical | Curriculum Changeset Engine | Edits stage in COURSE_VERSION_CHANGESET; live catalog unaffected |
| `TC-IT08-006` | Atomic All-or-Nothing Changeset Diff & Approval | Critical | Changeset Review Subsystem | Diff renders Before vs After; approval applies changes atomically |

---

### Detailed Test Specifications

#### TC-IT08-001: Pre-Flight Publish Readiness Validation
- **Objective:** Verify that `POST /instructor/courses/<id>/submit` strictly validates the 5 canonical readiness criteria (16:9 Cover Image, Intro Trailer URL, Description >= 20 chars with SLOs, Academic completion rule >= 50%, Non-empty Curriculum) before allowing submission.
- **Steps:**
  1. Instructor creates a new course with basic details only (no cover, no trailer, no completion rule, empty curriculum).
  2. Instructor requests pre-flight checklist via `GET /instructor/courses/<id>/publish-checklist`.
  3. Instructor attempts submission via `POST /instructor/courses/<id>/submit`.
  4. Verify HTTP 400 is returned with error message containing missing criteria.
  5. Verify `course.status` remains `DRAFT`.
- **Pass Criteria:** HTTP 400, `is_ready == False`, course status is strictly `DRAFT`.

#### TC-IT08-002: Complete Course Submission & Studio Lock
- **Objective:** Verify that when all 5 criteria are fulfilled, course submission transitions to `SUBMITTED_FOR_REVIEW` and Course Studio UI locks modifications.
- **Steps:**
  1. Populate the course with authentic thumbnail URL, trailer URL, description (>= 20 chars), learning objectives, completion rule (minimum_progress_percent: 80.0), a learning unit, and a lesson with markdown content.
  2. Verify pre-flight checklist passes (`is_ready == True`).
  3. Submit course via `POST /instructor/courses/<id>/submit`.
  4. Open Course Studio at `#/instructor/courses/manage?id=<id>`.
  5. Verify header badge displays "Chờ duyệt (In Review)" and editing actions are locked.
- **Pass Criteria:** HTTP 200, status `SUBMITTED_FOR_REVIEW`, UI lock confirmed.

#### TC-IT08-003: Admin Governance Queue & Course Inspection Dossier
- **Objective:** Verify that the submitted course appears in the Admin review queue and the inspection dossier displays all required academic metadata.
- **Steps:**
  1. Authenticate as Primary Admin (`admin@pwd301.local`).
  2. Navigate in real Chrome to `#/admin/governance?tab=courses`.
  3. Verify `#admin-review-courses-queue` displays the submitted course.
  4. Fetch inspection dossier via `GET /admin/courses/<id>`.
  5. Verify curriculum structure, lessons, and review version match submitted state.
- **Pass Criteria:** Course listed in queue, inspection dossier returns status 200 with full lesson/curriculum data.

#### TC-IT08-004: Course Approval & Publication Gate
- **Objective:** Verify administrative course approval and publication lifecycle transitions.
- **Steps:**
  1. Admin executes approval via `POST /admin/courses/<id>/review` with `{"action": "approve"}`.
  2. Verify course status transitions to `APPROVED`.
  3. Admin publishes course via `POST /admin/courses/<id>/publish` with reason.
  4. Verify course status transitions to `PUBLISHED`.
  5. Query Student Catalog (`GET /student/courses/` and view `#/student/catalog`).
  6. Verify course is live, discoverable, and enrollable.
- **Pass Criteria:** Status `PUBLISHED`, visible in Student Catalog, HTTP 200 responses.

#### TC-IT08-005: Unified Staging Draft Invariant
- **Objective:** Verify that after publication, instructor edits do not overwrite the live curriculum directly, but are automatically aggregated into a `COURSE_VERSION_CHANGESET`.
- **Steps:**
  1. Instructor edits the published course: adds a new Learning Unit ("Chương 2: Tự Động Hóa QA") and a new Lesson.
  2. Verify backend response flags `is_draft: true` and associates changes with a `change_request_id`.
  3. Check Student Catalog and course detail from student perspective.
  4. Verify student view only sees the approved live curriculum (Chương 1), with zero leakage of Chương 2.
- **Pass Criteria:** `COURSE_VERSION_CHANGESET` active, live student curriculum completely isolated from unapproved staging draft.

#### TC-IT08-006: Atomic All-or-Nothing Changeset Diff & Approval
- **Objective:** Verify the Admin Side-by-Side Diff modal and atomic approval/merge of the staged changeset.
- **Steps:**
  1. Request changeset diff via `GET /admin/courses/<id>/changeset/diff`.
  2. Verify diff payload returns structured comparison showing added unit/lesson.
  3. Admin submits atomic approval via `POST /admin/courses/<id>/changeset/approve`.
  4. Verify changeset status becomes `APPROVED` / applied.
  5. Verify student view now reflects the updated curriculum with Chương 2 seamlessly merged.
- **Pass Criteria:** Diff payload verified, atomic merge completed without orphaned records or curriculum corruption.
