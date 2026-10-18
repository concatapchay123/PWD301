# ITERATION 04 TEST SPECIFICATION

## Test Cases Detailed Specification

### TC-IT04-001: Brand Identity & Topbar Chrome Render
- **Preconditions:** Student logged in on `http://localhost:5000/#/student/dashboard`.
- **Steps:**
  1. Inspect `#app-topbar` element.
  2. Verify PPTQ logo presence and visibility.
  3. Verify topbar user badge (`#topbar-role-badge`), user name (`#topbar-user-name`), and avatar initials (`#topbar-avatar-initials`).
- **Expected Result:** Brand logo, title "PPTQ LMS", user name, role badge "HỌC VIÊN", and avatar are rendered cleanly without visual regressions.

### TC-IT04-002: Dynamic Role Navigation Items Render
- **Preconditions:** Student logged in on `http://localhost:5000/#/student/dashboard`.
- **Steps:**
  1. Query `#topbar-navigation-items a`.
  2. Inspect text and href attributes of all rendered navigation links.
- **Expected Result:** Renders links: "Trang chủ" (`#/student/dashboard`), "Khám phá Khóa học" (`#/student/catalog`), "Khóa học của tôi" (`#/student/courses`), "Bài kiểm tra" (`#/student/assessments`).

### TC-IT04-003: Mobile Drawer Open/Close Interaction
- **Preconditions:** Resize browser viewport to 375x667 (Mobile).
- **Steps:**
  1. Verify `#topbar-mobile-menu-btn` is visible on mobile viewport.
  2. Click `#topbar-mobile-menu-btn`.
  3. Verify `#mobile-nav-drawer` removes `hidden` class and backdrop `#mobile-nav-backdrop` becomes visible.
  4. Click `#mobile-nav-close-btn`.
  5. Verify `#mobile-nav-drawer` adds `hidden` class.
- **Expected Result:** Mobile navigation drawer smoothly opens and closes, with correct ARIA attributes (`aria-expanded`).

### TC-IT04-004: Focus Exam Mode Shell Guard & AI Tutor Concealment
- **Preconditions:** Authenticated student navigates to `#student/attempt/test-attempt-id`.
- **Steps:**
  1. Force-navigate to `#/student/attempt/sample-attempt-id`.
  2. Check `document.body.classList.contains('fullscreen-focus-mode')`.
  3. Check `#floating-ai-container.classList.contains('hidden')`.
  4. Check `#console-course-progress-badge` existence in DOM.
- **Expected Result:** `fullscreen-focus-mode` class is active, floating AI container is hidden, and obsolete progress badge is completely absent from DOM.

### TC-IT04-005: Unknown Route Graceful Fallback (404 Handling)
- **Preconditions:** Authenticated student.
- **Steps:**
  1. Navigate to unknown hash `#/non-existent-random-route-999`.
  2. Wait 2 seconds for router resolution.
- **Expected Result:** Router catches unmapped path and redirects safely to `#/student/dashboard` without crash or white screen.

### TC-IT04-006: Browser History Stack Navigation Integrity
- **Preconditions:** Authenticated student on `#/student/dashboard`.
- **Steps:**
  1. Click or navigate to `#/student/catalog`.
  2. Click or navigate to `#/student/courses`.
  3. Execute `window.history.back()`.
  4. Verify URL returns to `#/student/catalog`.
  5. Execute `window.history.back()`.
  6. Verify URL returns to `#/student/dashboard`.
- **Expected Result:** History entries are cleanly preserved without infinite loops or trapped states.
