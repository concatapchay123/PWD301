# Execution Results — Iteration 08: Multi-Step Business Workflows: Course Lifecycle & Staging Drafts

**Execution Date:** 2026-10-18T06:10:32Z  
**Target Environment:** Local Docker Stack (`pwd301_web` on `http://localhost:5000`, Microsoft SQL Server on `localhost:1433`)  
**Execution Engine:** Real Google Chrome (Playwright `channel="chrome"`), REST API Envelopes, Database State  
**Total Test Cases:** 6  
**Passed:** 6 (100%)  
**Failed:** 0 (0%)  
**Blocked:** 0 (0%)  

---

## 1. Test Execution Summary

| Test Case ID | Test Case Name | Status | Evidence Screenshot | Execution Notes |
| :--- | :--- | :---: | :--- | :--- |
| `TC-IT08-001` | Pre-Flight Publish Readiness Validation (Fail-Closed Rejection) | **PASS** | `IT08_TC01_preflight_rejection.png` | Bare course rejected fail-closed with HTTP 400. `is_ready=False` (4 missing criteria). Status remained `DRAFT`. |
| `TC-IT08-002` | Complete Course Submission & Studio Lock | **PASS** | `IT08_TC02_course_submitted_locked.png` | 16:9 Cover uploaded (Asset `9104247d-8656-4e45-b1f6-74c98cdb663a`), metadata, SLOs, rule (80%), curriculum added. `is_ready=True`. Transitioned to `SUBMITTED_FOR_REVIEW`. |
| `TC-IT08-003` | Admin Governance Queue & Course Inspection Dossier | **PASS** | `IT08_TC03_admin_review_queue.png` | Course detected in Admin review queue DOM (`#admin-review-courses-queue`). Inspection dossier retrieved with status `SUBMITTED_FOR_REVIEW`. |
| `TC-IT08-004` | Admin Course Approval & Publication Transition | **PASS** | `IT08_TC04_course_published_catalog.png` | Admin approved (`APPROVED`) and published (`PUBLISHED`). Course verified live and visible in Student Catalog (`#/student/catalog`). |
| `TC-IT08-005` | Unified Staging Draft Invariant (Post-Publication Isolation) | **PASS** | `IT08_TC05_staging_draft_isolation.png` | Chapter 2 added to published course. System activated Staging Draft (`is_draft=True`, CR `130007`). Student view strictly isolated (0% leakage). |
| `TC-IT08-006` | Atomic All-or-Nothing Changeset Diff Modal & Admin Approval | **PASS** | `IT08_TC06_changeset_diff_approved.png` | Diff retrieved with review identity (`review_version=023019dd...`). Admin atomically approved changeset. Student curriculum merged Chapter 2 seamlessly. |

---

## 2. Detailed Empirical Verification Findings

### TC-IT08-001: Pre-Flight Publish Readiness Validation
- **Action:** Created bare course `FLOW_359186` (`50962764-07b6-4b59-8ce4-31174c6d53ca`) with only title and code.
- **Checklist Query:** `GET /instructor/courses/<id>/publish-checklist` confirmed `is_ready=False` with 4 missing criteria: cover image, trailer URL, authentic description with SLOs, and non-empty curriculum.
- **Submission Barrier:** `POST /instructor/courses/<id>/submit` returned HTTP 400 (`CourseValidationError`): *"Khóa học chưa đủ điều kiện xuất bản: Chưa có ảnh bìa khóa học. Vui lòng tải lên..."*.
- **Integrity Check:** `course.status` remained strictly `DRAFT`.

### TC-IT08-002: Complete Course Submission & Studio Lock
- **Action:** Generated and uploaded 16:9 Cover Image asset (`COURSE_IMAGE`), set trailer URL (`https://www.youtube.com/watch?v=dQw4w9WgXcQ`), description, 2 SLOs, completion rule (`minimum_progress_percent: 80.0`), Chapter 1, and Lesson 1.
- **Readiness Verification:** Pre-flight checklist returned `is_ready=True` (5/5 criteria passed).
- **Submission:** `POST /instructor/courses/<id>/submit` succeeded with HTTP 200, transitioning status to `SUBMITTED_FOR_REVIEW`.
- **UI Lock:** Verified Studio UI at `#/instructor/courses/manage?id=...` entered review lock state.

### TC-IT08-003: Admin Governance Queue & Course Inspection Dossier
- **Action:** Primary Admin authenticated and navigated to `#/admin/governance?tab=courses`.
- **DOM Verification:** `#admin-review-courses-queue` rendered course `FLOW_359186` with action button "Xem Khóa Học".
- **Dossier Contract:** `GET /admin/courses/<id>` returned comprehensive inspection dossier including curriculum breakdown, SLOs, and review version.

### TC-IT08-004: Admin Course Approval & Publication Transition
- **Action:** Admin reviewed and approved course (`POST /admin/courses/<id>/review` with `{"action": "approve"}`) -> transitioned to `APPROVED`.
- **Publication Gate:** Admin published course (`POST /admin/courses/<id>/publish`) -> transitioned to `PUBLISHED`.
- **Public Visibility:** Student logged in, navigated to `#/student/catalog`. Course `FLOW_359186` was rendered in catalog DOM.

### TC-IT08-005: Unified Staging Draft Invariant
- **Action:** Instructor added "Chương 2: Kiểm Thử Tự Động Nâng Cao & Mocking" to the PUBLISHED course.
- **Draft Aggregation:** Backend detected course is `PUBLISHED` and automatically routed changes to `COURSE_VERSION_CHANGESET` (`ChangeRequest` ID `130007`), returning `is_draft: True`.
- **Zero Leakage:** Querying `GET /student/courses/<id>` as student confirmed only Chapter 1 is visible; Chapter 2 was completely absent from student access.

### TC-IT08-006: Atomic All-or-Nothing Changeset Diff Modal & Admin Approval
- **Action:** Instructor submitted changeset for review (`POST /instructor/courses/<id>/changeset/submit`).
- **Diff Inspection:** Admin retrieved changeset diff via `GET /admin/courses/<id>/changeset/diff`. System returned full Before vs After comparison along with immutable `review_version` (`023019dd1799a99670cddb1530815d2c964975c98b6f228202191f31881ec924`).
- **Atomic Approval:** Admin approved changeset supplying `review_version` and `request_id: 130007`. Status changed to `APPROVED`.
- **Catalog Synchronization:** Student re-queried course curriculum; Chapter 2 was immediately and atomically available without orphaned records or curriculum corruption.
