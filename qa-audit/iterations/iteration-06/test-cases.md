# ITERATION 06 TEST SPECIFICATION

## Test Cases Detailed Specification

### TC-IT06-001: Idempotent Navigation on Manage/Create Routes
- **Preconditions:** Authenticated instructor on `#/instructor/dashboard`.
- **Steps:**
  1. Directly navigate to `#/instructor/courses/manage` without query parameter `id`.
  2. Observe route resolution and toast alerts.
- **Expected Result:** Router detects missing ID, shows toast notification ("Vui lòng chọn một khóa học từ danh sách để quản lý."), and safely redirects to `#/instructor/courses` with ZERO database record creation.

### TC-IT06-002: UI Course Creation via Instructor Studio Modal
- **Preconditions:** Authenticated instructor on `#/instructor/courses`.
- **Steps:**
  1. Click `#btn-add-course` to open `create-course-modal-form`.
  2. Fill Course Code `QA202` and Course Title `Kỹ Thuật Kiểm Thử Hiệu Năng QA202`.
  3. Click `#submit-create-course-btn`.
- **Expected Result:** Modal submits, shows success toast, and automatically routes the instructor into the Single-Page Studio (`#/instructor/courses/manage?id=<newCourseId>`).

### TC-IT06-003: Studio Header Render & Status Badge Verification
- **Preconditions:** Inside newly created course studio.
- **Steps:**
  1. Inspect studio header title, course code, and status badge.
- **Expected Result:** Title `Kỹ Thuật Kiểm Thử Hiệu Năng QA202` and Course Code `QA202` are displayed; status badge indicates `Bản nháp (Draft)`.

### TC-IT06-004: Learning Unit (Chapter) Creation in Single-Page Studio
- **Preconditions:** Course manage studio active.
- **Steps:**
  1. Dispatch chapter creation for `"Chương 1: Nguyên lý Kiểm thử Hiệu năng"`.
  2. Verify chapter is injected into curriculum outline.
- **Expected Result:** Chapter 1 appears in the curriculum tree without requiring full page reload.

### TC-IT06-005: Browser Refresh Resilience & Read-After-Write Consistency
- **Preconditions:** Course with Chapter 1 rendered.
- **Steps:**
  1. Execute `page.reload()` in Playwright.
  2. Wait for studio to re-mount.
- **Expected Result:** Course Title and Chapter 1 persist accurately from backend storage.

### TC-IT06-006: Duplicate Course Code Uniqueness Enforcement (409 Conflict)
- **Preconditions:** Authenticated instructor.
- **Steps:**
  1. Attempt to create another course with identical code `QA202`.
- **Expected Result:** Backend returns HTTP 409 Conflict (`A course with code 'QA202' already exists.`); duplicate insertion is safely blocked.
