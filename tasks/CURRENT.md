# TASK-CORE-FIX: PWD301 Core Defect Remediation & System Upgrades

**Status:** COMPLETED  
**Completed At:** 2026-10-18  
**Scope:**
1. Fix Exam Creation & Publishing (`policy is not defined` at Step 4)
2. Sync Lesson Resources / Documents between Instructor Studio & Student View (Backend `LessonResource` persistence + Non-document image filtering)
3. Fix PDF Gradebook / Transcript Export (HTTP 500 `svglib` dependency & fail-safe fallback)
4. Standardize Student Navigation Buttons ("Quay lại" / "Tiếp theo") & Realtime Lesson Unlock (Eliminate floating chevrons, prevent button flickering, realtime unlock without F5)

---

## 1. Action Items Completed
- [x] **Step 1: Fix Exam Creation & Publishing (`instructor-exams.js`)**
  - Added `const policy = InstructorView.readExamPolicy(document);` before saving draft and building `asmPayload`.
  - Configured payload with all scoring policies, visibility rules, layout, and fullscreen security flags.
- [x] **Step 2: Sync Lesson Resources in Backend & Student Document Hub (`lesson_service.py`, `instructor/routes.py`, `student.js`)**
  - Updated `update_lesson` in `lesson_service.py` to persist `data["resources"]` to `LessonResource` join table.
  - Updated `update_lesson_route` in `instructor/routes.py` to preserve resources across staging drafts and diff checks.
  - Implemented `isStudyDocument` in `student.js` to strictly exclude non-document assets (PNG, JPG, JPEG, GIF, WEBP, SVG) from the Document Hub.
  - Rendered clean 1:1 Chapter $\rightarrow$ Lesson hierarchy in student view with authorized `data-download-asset` tokens.
- [x] **Step 3: Fix PDF Export for Student, Instructor, and Admin (`pdf_math_service.py`, Docker environment)**
  - Guarded `from svglib.svglib import svg2rlg` with safe `try/except ImportError` fallback.
  - Wrapped `math_paragraph` with safe fallback to `Paragraph` if rendering fails.
  - Installed `svglib==1.6.0` and dependencies in Docker container `pwd301_web`.
  - Verified 18/18 tests pass in `test_result_pdf_formatting.py` and `test_admin_diff_and_gradebook_pdf.py`.
  - Verified real PDF generation inside Docker container: 525,573 bytes (attempt) and 530,333 bytes (gradebook) with PPTQ branding & watermark.
- [x] **Step 4: Standardize Navigation & Realtime Lesson Unlocking (`student.js`)**
  - Removed floating navigation chevrons `#floating-prev-btn` and `#floating-next-btn`.
  - Standardized bottom bar: "Quay lại" disabled on lesson 1.1, active on subsequent lessons.
  - "Tiếp theo" always visible: disabled gray with toast when requirements incomplete, dynamic emerald active (`animate-fade-in`) when complete.
  - Removed 1-second interval timer that destroyed button DOM every 1000ms.
  - Enabled realtime sidebar outline and Next button unlocking without F5 on `onEnded` and quiz completion.
- [x] **Step 5: Empirical Verification & End-to-End Testing (`scripts/verify_4_core_fixes.py`)**
  - Verified Node syntax on JavaScript files: 0 syntax errors.
  - Verified container HTTP 200 on health and PDF service generation.
  - Local Pytest: 18/18 passed in `test_result_pdf_formatting.py` and `test_admin_diff_and_gradebook_pdf.py`.
  - Playwright Chrome Headless E2E:
    - [PASS] LessonResource DB persistence: 2 resources verified.
    - [PASS] PDF Attempt Result generated: 560,583 bytes -> `verification/fixes/verified_attempt_result.pdf`.
    - [PASS] PDF Assessment Gradebook generated: 565,392 bytes -> `verification/fixes/verified_gradebook.pdf`.
    - [PASS] Floating chevrons completely absent from DOM.
    - [PASS] Bottom "Quay lại" button on Lesson 1.1 correctly disabled (`opacity-50 cursor-not-allowed`).
    - [PASS] Bottom "Tiếp theo" button initially locked with requirements toast.
    - [PASS] Document Hub filtered: valid docs shown, `image1001.png` strictly excluded.
    - [PASS] Bottom "Tiếp theo" button dynamically transitions to active emerald green without F5.
    - [PASS] `InstructorView.readExamPolicy` verified functional with full policy dict.
- [x] **Step 6: Live Headed Chrome Interactive Verification via Chrome DevTools**
  - Resolved `normalizeExamBloom` difficulty mapping (`MEDIUM`, `EASY`, `HARD`, `DỄ`, `TRUNG BÌNH`, `KHÓ`) in `instructor-exams.js`.
  - Live Chrome Exam Wizard: Auto-assigned Key A, checked publish agreement, confirmed modal, and published assessment 110007 (`POST /publish` 200).
  - Live Chrome PDF Export: Clicked "Xuất bảng điểm PDF" on exam results page, successfully downloaded 530,552-byte PDF blob in Chrome.
  - Live Chrome Navigation: Verified bottom navigation locked state, toast feedback on click, zero floating chevrons, and 29 synchronized documents.
  - Captured live Chrome screenshots:
    - `verification/fixes/live_chrome_student_learning.png`
    - `verification/fixes/live_chrome_documents_tab_active.png`
    - `verification/fixes/live_chrome_bottom_nav_locked.png`
    - `verification/fixes/live_chrome_toast_requirement.png`
    - `verification/fixes/live_chrome_instructor_exam_wizard.png`
    - `verification/fixes/live_chrome_step4_before_publish.png`
    - `verification/fixes/live_chrome_step4_ready_to_publish.png`
    - `verification/fixes/live_chrome_confirm_publish_modal.png`
    - `verification/fixes/live_chrome_exam_published_dashboard.png`
    - `verification/fixes/live_chrome_instructor_exam_results_gradebook.png`

