# TASK-094: System Enhancements, Anti-Bypass Quiz Modal, Unified Staging Lifecycle & Obsolete Workflow Purge Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permanently purge obsolete workflows and memory regarding course covers, manual lesson completion buttons, unshielded mini-quizzes, draft review blocks, fragmented video upload UI, and static completion durations; implement a 16:9 full-width course cover, dwell-paced & quiz-gated lesson progression, 80% backdrop blurred "Câu hỏi" modal with anti-bypass persistence, direct draft editing / single published staging draft, unified video upload UI with playable preview, and modern landing page layout.

**Architecture:** Pure Headless REST API (Flask/SQLAlchemy/MSSQL) backend serving standardized JSON envelopes; SPA frontend (vanilla JavaScript / Tailwind CSS / Material Symbols / VideoArmor) consuming endpoints via session authentication.

**Tech Stack:** Python 3.12, Flask, SQLAlchemy, MSSQL Server, Pytest, JavaScript (ES6+), HTML5 Video, Tailwind CSS, Chrome DevTools MCP.

**Spec:** `docs/system/PWD301_SYSTEM_SPECIFICATION/` & `tasks/CURRENT.md` (TASK-094).

---

## Global Constraints

- PWD301 is a Pure Headless platform; no Jinja HTML templates, static files in backend, or mock previews.
- Strictly adhere to Jakob's Law, Hick's Law, Law of Proximity, Miller's Law, and Von Restorff Effect.
- Pure black (`#000000`) and pure white (`#ffffff`) are strictly forbidden; use `#121212`, `#18181b`, `#202020`, `#222120`, `#EDEDEB`, `#F4F1EA`.
- All video uploads are capped at $< 1$ GB. YouTube embedding uses official iframe parameters without bare links.
- Lesson progression is server-authoritative; no client bypass or jump without satisfying verified dwell time ($\ge 30$s), 100% video playback, and passing the required in-lesson question assessment.
- Fail-closed security: In-lesson quiz modal locks outside clicks and `Esc`; modal cannot close until student achieves $\ge$ passing threshold.
- Course Drafts permit direct editing without admin review or change requests. Published courses aggregate 100% of mutations into a single `CourseVersionChangeset` (`STAGING_DRAFT`).

---

## Review Focus

1. **State Persistence on Reload**: When a student refreshes (F5) or re-enters a course while a quiz modal is pending, the system must navigate to the exact current lesson and immediately redisplay the locked quiz modal, preventing any URL hash tampering or bypass.
2. **Video Streaming Authentication**: Local uploaded video previews in the Studio must stream smoothly via `/api/files/<asset_id>/stream` with proper HTTP Range headers and authorization checks, avoiding direct unauthenticated download links.
3. **Dual Role Direct Edits**: An instructor who also has `ADMIN` privileges must NOT be blocked by `CourseValidationError("Admin direct edits to an Instructor-owned course require a reason.")` when updating their own courses or draft courses.
4. **Clean 16:9 Aspect Ratio**: Full-width course cover banner must scale gracefully on ultra-wide screens (1720px) without distortion or pixelated stretched overflow, using `w-full aspect-video object-cover`.
5. **Multi-condition Lesson Unlock**: A lesson must not unlock "Bài tiếp theo" if dwell time is under 30s, even if video or quiz are completed prematurely via client spoofing.

---

## Task Decomposition

### Task 0: System-Wide Memory & Legacy Workflow Purge (Spec & CURRENT.md)

**Files:**
- Modify: `tasks/CURRENT.md:1-50`
- Modify: `docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md`

**Interfaces:**
- Produces: Formal canonical invariants 094.1 through 094.6 in `tasks/CURRENT.md` and System Specification.

- [ ] **Step 1: Write TASK-094 Canonical Invariants in `tasks/CURRENT.md`**
  - Define Invariant 094.1: Permanent Purge of Clamped 768px (`max-w-3xl`) Course Cover Containers & Blank UI Gutters.
  - Define Invariant 094.2: Permanent Abolition of "Đánh dấu hoàn thành" Button & 3-Condition Lesson Gate.
  - Define Invariant 094.3: Permanent Purge of Unshielded In-Lesson Quizzes & Terminal Standardization to "Câu hỏi" Modal.
  - Define Invariant 094.4: Permanent Purge of Fragmented Draft Reviews & Erroneous Admin Reason Blocking.
  - Define Invariant 094.5: Permanent Purge of Split Video Upload Layouts & Unplayable Local Previews.
  - Define Invariant 094.6: Permanent Purge of Static Course Durations ("15 tuần học") & Buried Instructor Profiles.

- [ ] **Step 2: Update System Specification Invariants**
  - Update `docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md` reflecting the new 3-condition lesson completion rule and "Câu hỏi" modal standard.

- [ ] **Step 3: Verification**
  - Run: `git diff tasks/CURRENT.md` to confirm obsolete workflow language has been permanently superseded.

---

### Task 1: Course Cover 16:9 Full-Width Banner Remediation in Studio

**Files:**
- Modify: `frontend/assets/js/views/instructor.js:3825-3890`

**Interfaces:**
- Consumes: `course.thumbnail_url`, `course.title`, `course.course_code`.
- Produces: Full-bleed 16:9 banner container without empty horizontal gutters.

- [ ] **Step 1: Remove `max-w-3xl mx-auto` and expand cover container**
  - Replace `aspect-video w-full max-w-3xl mx-auto overflow-hidden rounded-xl border` with `aspect-video w-full overflow-hidden rounded-2xl border`.
  - Ensure `<img>` tag has `w-full h-full object-cover object-center`.
  - Position course metadata (Code badge, Category, Title, Description) and action buttons (Đổi ảnh bìa, Gửi duyệt xuất bản) cleanly in the card below the cover.

- [ ] **Step 2: Verify in browser**
  - Inspect `#/instructor/courses/edit?id=...` using Chrome DevTools MCP. Confirm zero left/right empty gutters and sharp 16:9 rendering.

---

### Task 2: Student Lesson Completion Pacing Engine (Abolish Manual Button & 3-Condition Gate)

**Files:**
- Modify: `frontend/assets/js/views/student.js:4190-4240, 4674-4760, 4845-4920`
- Modify: `src/pwd301/services/lesson_service.py:120-180`
- Test: `tests/frontend/student_lesson_unlock_contract.test.js`
- Test: `tests/unit/test_lesson_completion_gates.py`

**Interfaces:**
- Consumes: Lesson metadata (`video_urls`, `playback_media`, `quiz`), active dwell timer.
- Produces: Server-authoritative unlock of "Bài tiếp theo" if and only if dwell $\ge 30$s, video 100%, and quiz passed.

- [ ] **Step 1: Write failing unit test for 30s dwell & quiz gating**
  - Test verifying lesson progress cannot mark complete if dwell time < 30 seconds or quiz is unfinished.

- [ ] **Step 2: Abolish `#cisco-complete-btn` in `student.js`**
  - Remove button `#cisco-complete-btn` completely from DOM and render bottom nav.
  - Transform "Bài tiếp theo" into a reactive status-aware button:
    - Default state: Disabled with `opacity-50 cursor-not-allowed` and lock badge if requirements are not met.
    - Hover tooltip / informative toast when clicked while locked: "Cần hoàn thành các điều kiện: Ở lại bài học ít nhất 30s, xem hết video bài giảng và vượt qua Câu hỏi củng cố."

- [ ] **Step 3: Implement 30s dwell timer and multi-condition check**
  - Track `timeEnteredLesson = Date.now()`.
  - Implement function `checkLessonCompletionStatus()`:
    - Condition 1: `(Date.now() - timeEnteredLesson) >= 30000`.
    - Condition 2: `!hasVideo || videoWatched === true`.
    - Condition 3: `!hasQuestions || questionsPassed === true`.
  - When all 3 conditions evaluate to `true`: invoke `ApiClient.updateLessonProgress(courseId, lessonId, { is_completed: true })`, mark active item completed in outline, and enable "Bài tiếp theo" button.

- [ ] **Step 4: Run test to verify passes**
  - Run: `pytest tests/unit/test_lesson_completion_gates.py -v`

---

### Task 3: In-Lesson "Câu hỏi" 80% Blurred Backdrop Modal & Anti-Bypass Persistence

**Files:**
- Modify: `frontend/assets/js/views/student.js:4190-4260, 4845-4950`
- Modify: `frontend/assets/js/ui.js`

**Interfaces:**
- Consumes: `lesson.quiz` (array of questions), `courseId`, `activeItem.id`.
- Produces: `renderQuestionModal(questions, passingPercent)` with `backdrop-blur-md bg-black/80` and state lock.

- [ ] **Step 1: Standardize terminology**
  - Rename all labels from "mini-quiz", "bài kiểm tra gắn liền bài học", "small test" to **"Câu hỏi"**.

- [ ] **Step 2: Implement 80% Blurred Modal Engine**
  - Create high-impact modal with `backdrop-blur-md bg-black/80 z-50 fixed inset-0 flex items-center justify-center p-4 sm:p-6`.
  - Lock backdrop: clicking outside does NOT dismiss modal (`pointer-events-auto` on dialog, event stopper on backdrop). Disable `Escape` key.
  - Organize questions in Coursera-style slide-by-slide pagination (Question 1 of N) with Next/Previous navigation and question progress indicator.
  - Pass evaluation:
    - If score $\ge$ threshold: show success banner, review of answers, and button "Đóng và tiếp tục học" (closes modal and unlocks lesson).
    - If score < threshold: show achieved score vs threshold, hide correct answers, and provide button "Làm lại từ đầu" (resets quiz).

- [ ] **Step 3: Implement Scroll Trigger & Auto-Resume Persistence**
  - When student scrolls to the question placeholder or completes video: trigger modal automatically.
  - Store pending quiz state in `sessionStorage` / backend:
    - If student exits or refreshes: on course mount, automatically redirect to `activeLessonId` and relaunch the locked "Câu hỏi" modal immediately.

- [ ] **Step 4: Verify in browser**
  - Test with student account: attempt to bypass without doing quiz -> verify "Bài tiếp theo" is locked.
  - Refresh browser -> verify modal immediately reopens.
  - Complete quiz with passing score -> verify modal can close and "Bài tiếp theo" unlocks.

---

### Task 4: Course Edit Lifecycle Hardening (Direct Draft Edit & Fix Admin Reason)

**Files:**
- Modify: `src/pwd301/services/course_service.py:540-580`
- Modify: `src/pwd301/blueprints/instructor/routes.py:769-855`
- Modify: `frontend/assets/js/views/instructor.js:5250-5620`
- Test: `tests/unit/test_course_service_metadata.py`

**Interfaces:**
- Consumes: `course.status` (`DRAFT`, `PUBLISHED`), `actor.id`, `actor.is_admin`.
- Produces: Clean update for DRAFT courses without `CourseValidationError` and single staging changeset for PUBLISHED courses.

- [ ] **Step 1: Write failing unit test for draft course update without reason**
  - Test verifying an admin or instructor editing a DRAFT course does not trigger "Admin direct edits to an Instructor-owned course require a reason."

- [ ] **Step 2: Update `course_service.py` validation logic**
  - Check `course.status`: If `course.status == 'DRAFT'`, bypass `admin_override` reason requirement.
  - For `course.status == 'PUBLISHED'`: ensure all changes route to `queue_course_metadata_review` / `CourseVersionChangeset` (`STAGING_DRAFT`).

- [ ] **Step 3: Update `instructor.js` Landing & Metadata modal**
  - Ensure `btn-save-unified-intro` checks course status:
    - If `DRAFT`: update directly and show success toast: "Đã cập nhật thông tin khóa học thành công."
    - If `PUBLISHED`: save to staging draft and show toast: "Đã lưu thay đổi vào Bản nháp Staging. Thầy/Cô chỉ cần gửi duyệt 1 lần khi hoàn tất."

- [ ] **Step 4: Run test to verify passes**
  - Run: `pytest tests/unit/test_course_service_metadata.py -v`

---

### Task 5: Low-Tech Video Upload & Streaming Preview Studio

**Files:**
- Modify: `frontend/assets/js/views/instructor.js:2247-2345, 3350-3450`
- Modify: `src/pwd301/blueprints/api_files/routes.py` (ensure streaming range endpoint is open to instructors for review)
- Test: `tests/frontend/video_upload_ui_contract.test.js`

**Interfaces:**
- Consumes: `block.url` (YouTube), `block.files` (uploaded files), `cfdedc83-94e3-450e-abf0-c185c8311eb8.png` reference design.
- Produces: Unified Video Block (YouTube input on top, "hoặc" divider, dropzone below, 2-column preview cards grid with play modal).

- [ ] **Step 1: Redesign Video Block HTML according to reference image**
  - Top: Label "Dán link YouTube / Vimeo bài giảng" + Input (`https://www.youtube.com/watch?v=...`) + Button `[+ Thêm video]`.
  - Divider: Horizontal line with text `hoặc` centered.
  - Dropzone: Label "Tải video lên từ máy tính (≤ 1 GB)", dashed border dropzone with cloud icon, subtext for formats (MP4, WebM, MOV, MKV), and button `[Chọn tệp video]`.
  - Bottom Section: Header "Xem trước video đã thêm (X)" with badge "Tối đa 2 video / bài học".
  - Grid: 2-column card layout displaying added videos:
    - Card: Thumbnail with rounded Play icon + duration pill (e.g. `12:34`). Right side: YouTube/file icon, Title, URL/Size, delete button `[✕]`.

- [ ] **Step 2: Implement Uploaded Video Modal Preview**
  - Attach click handler to play icon on uploaded video cards:
    - Open modal with custom HTML5 video player pointing to `/api/files/<asset_id>/stream` (or authenticated stream URL).
    - Handle loading, range requests, play/pause, and error handling gracefully.

- [ ] **Step 3: Verify in browser**
  - Add YouTube video -> verify card appears in preview grid.
  - Upload MP4 video (< 1 GB) -> verify card appears with thumbnail, size, and title.
  - Click Play on uploaded video -> verify video plays smoothly in modal.

---

### Task 6: Course Landing Page Overhaul (Purge "15 tuần học" & Prominent Instructor Profile)

**Files:**
- Modify: `frontend/assets/js/views/student.js:1680-1875`
- Test: `tests/frontend/student_landing_contract.test.js`

**Interfaces:**
- Consumes: Course metadata, instructor info (`name`, `title`, `email`, `phone`, `office_hours`, `group`).
- Produces: 3-column KPI grid and top-positioned Instructor profile card.

- [ ] **Step 1: Purge "15 tuần học" across landing view**
  - Remove `<span class="font-medium">15 tuần học</span>` and schedule icon from Hero metadata pills.
  - Remove KPI card 1 ("15 tuần học / Chủ động tiến độ học tập").
  - Convert KPI grid into a balanced 3-column layout:
    1. Số bài học (`${totalLessons} bài học / Lý thuyết & phòng lab thực hành`)
    2. Bài khảo thí (`${totalExams} bài khảo thí / Đánh giá chuẩn đầu ra`)
    3. Chứng nhận hoàn thành (`Chứng nhận hoàn thành / Chứng nhận điện tử chính quy`)

- [ ] **Step 2: Reposition Instructor Card to Top of Right Column**
  - Move Instructor Card (`<!-- Giảng viên phụ trách -->`) to the very top of the right column (above "Quy chuẩn học vụ").
  - Upgrade styling:
    - Prominent avatar (large circle / rounded-2xl with initial / photo).
    - Instructor Name, Academic Title / Department.
    - Official email with clickable `mailto:`, phone with `tel:`, group link button.
    - Clean dark card tokens (`bg-slate-900/80 dark:bg-[#12161f] border border-slate-800/80 p-6 rounded-3xl`).

- [ ] **Step 3: Verify in browser**
  - Navigate to `#/student/courses/intro?id=...`.
  - Confirm: No "15 tuần học" visible anywhere; 3 KPI cards render neatly; Instructor profile is prominently displayed at the top right.

---

### Task 7: Full System Verification & Regression Suite

**Files:**
- Verify: Full test suite (`pytest tests/`)
- Verify: Frontend contract tests (`npm test` / Node test runners)
- Verify: Real browser interactive flow using Chrome DevTools MCP

- [ ] **Step 1: Run Backend Test Suite**
  - Run: `pytest tests/unit tests/integration -v`
  - Verify 0 failures.

- [ ] **Step 2: Run Frontend Contract Tests**
  - Run frontend test suite to ensure router and view contracts hold.

- [ ] **Step 3: End-to-End Real Browser Verification via DevTools MCP**
  - Verify Course Studio cover 16:9 full-width.
  - Verify Edit Draft Course saves without Admin Reason error.
  - Verify Video Upload UI matching reference design and local video preview playback.
  - Verify Student view: "Đánh dấu hoàn thành" button is gone, "Bài tiếp theo" is locked.
  - Verify "Câu hỏi" popup appears with 80% blurred backdrop, outside clicks locked.
  - Verify passing unlocks "Bài tiếp theo", reload keeps state.
  - Verify Landing page: "15 tuần học" gone, instructor info prominent on top right.

- [ ] **Step 4: Git Commit**
  - Commit all changes cleanly with descriptive conventional commit messages.
