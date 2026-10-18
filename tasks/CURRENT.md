# TASK-100 — PWD301 Comprehensive System Overhaul, YouTube 16:9 Standard, PPTQ Branding, Realtime Unlock & Global Security Lockdown

**Status:** COMPLETED  
**Approved:** 2026-10-18  
**Contract:** [AGENTS.md](../AGENTS.md), [WORKFLOW_SUPERSESSION](../docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/WORKFLOW_SUPERSESSION.md)  
**Plan:** `C:\Users\LENOVO\.gemini\antigravity\brain\bb27fb23-4d33-4f80-ade3-3d700a4211a2\plan.md`  

## Objective & Invariant Supersession
- **YouTube Standard 16:9 Viewport**: Completely eliminates all -22% top, 144% height cropping geometry. YouTube videos display 100% full view standard 16:9 without any lost details across: Student Learning Console, Teacher Preview, Hero Intro Trailer, and Admin Review.
- **Admin Review YouTube Preview**: Fixes the black screen bug in Admin Change Request Review (`_getCleanYouTubeShellHtml` and `setupReviewerVideoPlayer`) to reliably mount and control YouTube playback.
- **5-Second Seek Unlock**: Maintains anti-seek from 00:00 to (Duration - 5s). Automatically credits lesson video completion and unlocks free scrubbing across the final 5 seconds (or for videos <= 5s).
- **Realtime Lesson Completion Gate (No F5 Reload)**: Connects `onEnded` event on YouTube and HTML5 videos. Dynamically flips the Next button from gray to active emerald green and unlocks the next lesson in the outline immediately without requiring page refresh (F5).
- **Cascade Attachment Deletion & Instructor Document Tree**: Trashing a Lesson or Chapter automatically soft-deletes/trashes attached resources and removes them from the Course Document list. The Instructor Single-Page Studio displays attached documents for the active lesson plus a Course Document Tree drawer matching the student view.
- **PDF Gradebook "KHÔNG ĐẠT" & PPTQ Brand Identity**: Replaces "HỎNG" with "KHÔNG ĐẠT" (bold red) in the official gradebook PDF. Replaces all legacy logos with the new PPTQ logo across Topbar, Login, User Profile, and PDF Header, with a subtle semi-transparent PPTQ logo background watermark.
- **Global Anti-Tamper Blackout Shield & Session Revocation**: When DevTools opening or unauthorized code inspection is detected on any authenticated page, the system immediately overlays the Blackout Shield, revokes the server session via `POST /auth/logout`, clears client tokens, and redirects to `#/auth/login` with an explicit security termination notice.
- **Browser Verification Loop (Max 20 Rounds)**: Real browser verification with high-resolution annotated proof screenshots for each milestone.

## Milestones & Execution Checklist
- [x] **M0. Spec & Legacy Documentation Cleanup**
  - Updated `AGENTS.md` (Section 4 & Section 10.8) removing -22% crop geometry, old "HỎNG" status, and obsolete rules.
  - Reset `tasks/CURRENT.md` to TASK-100 scope.
- [x] **M1. PPTQ Branding System & PDF Watermark**
  - Extracted PPTQ dark & light logos from docx to `frontend/assets/img/`.
  - Replaced legacy logos on Topbar (`index.html`, `router.js`), Login/Register (`auth.js`), Profile (`student.js`, `instructor.js`).
  - Updated `result_pdf_service.py`: added PPTQ logo to header, added watermark background, replaced "HỎNG" -> "KHÔNG ĐẠT".
- [x] **M2. YouTube Standard 16:9 Viewport & Admin Review Fix**
  - Removed all `-22% top, 144% height` cropping across `student.js`, `instructor.js`, and `admin.js`.
  - Fixed `AdminView._getCleanYouTubeShellHtml` and `setupReviewerVideoPlayer` to mount `#${playerId}-yt` and reliably play YouTube videos without black screen.
- [x] **M3. Pacing Engine & 5-Second Seek Unlock**
  - Updated `student.js` to unlock seek and credit video completion when currentTime >= duration - 5s.
  - Updated `playback_service.py` to accept and credit positions in the final 5s without pacing anomalies.
- [x] **M4. Realtime Next Lesson Gate (No F5 Reload)**
  - Wired `onEnded` event in `setupCustomVideoPlayer` for YouTube state 0 and HTML5 ended.
  - Dynamically unlocked Next button and outline without F5.
- [x] **M5. Cascade Attachment Deletion & Instructor Document Tree**
  - Updated `lesson_service.py` to trash attached resources when lesson/chapter is deleted.
  - Added attached documents list and course document tree in `instructor.js`.
- [x] **M6. Global Security Shield & Session Revocation**
  - Upgraded `video-armor.js` to `SystemSecurityShield` on all authenticated routes in `router.js`.
  - Overlaid Blackout Shield, revoked server session, and redirected to `#/auth/login` on DevTools detection.
- [x] **M7. Browser Verification Loop (Max 20 Rounds)**
  - Executed Playwright real browser verification script on system Chrome (`scripts/run_20_rounds_comprehensive_audit.py`).
  - Successfully passed **20/20 rounds (100%)** of multi-tier visual, functional, security, responsiveness, and regression checks.
  - Captured and verified 20 annotated proof screenshots in `verification/rounds_20/`.

## Verification Artifacts Summary (20/20 Rounds Comprehensive Audit)
1. `verification/rounds_20/round_01_hero_trailer_16_9.png` — Hero Trailer uncropped 16:9 (`aspect-video`, 0% crop)
2. `verification/rounds_20/round_02_topbar_login_pptq_logo.png` — PPTQ logo on Topbar & Login form
3. `verification/rounds_20/round_03_student_profile_pptq.png` — PPTQ brand identity on Student Profile
4. `verification/rounds_20/round_04_gradebook_pdf_khong_dat.png` — Official Gradebook PDF with "KHÔNG ĐẠT", Header & Watermark
5. `verification/rounds_20/round_05_admin_review_youtube_preview.png` — Admin Review YouTube preview uncropped without black screen
6. `verification/rounds_20/round_06_5s_seek_unlock.png` — Student 5-second seek unlock and completion trigger
7. `verification/rounds_20/round_07_realtime_next_lesson_unlock.png` — Realtime Next Lesson button unlock without F5 reload
8. `verification/rounds_20/round_08_instructor_attached_docs.png` — Instructor Lesson attached documents management panel
9. `verification/rounds_20/round_09_instructor_course_doc_tree.png` — Instructor Course Document Tree hierarchy
10. `verification/rounds_20/round_10_security_devtools_lockdown.png` — Global Security Blackout Shield on DevTools key traps
11. `verification/rounds_20/round_11_security_view_source_trap.png` — Anti-inspect traps for Ctrl+U and Context Menu
12. `verification/rounds_20/round_12_security_screen_capture_trap.png` — Screen capture traps (PrintScreen, Snipping Tool) & Clipboard wipe
13. `verification/rounds_20/round_13_security_session_revoked.png` — Server session revocation (`/auth/logout`) and security redirect
14. `verification/rounds_20/round_14_mobile_viewport_375x667.png` — Mobile Viewport (375x667) responsive layout
15. `verification/rounds_20/round_15_tablet_viewport_768x1024.png` — Tablet Viewport (768x1024) responsive layout
16. `verification/rounds_20/round_16_desktop_viewport_1920x1080.png` — Full HD Desktop (1920x1080) responsive layout
17. `verification/rounds_20/round_17_dark_theme_contrast.png` — Dark Mode / Light Mode WCAG AA contrast verification
18. `verification/rounds_20/round_18_file_security_policy.png` — Strict 50MB file size ceiling and non-archive policy rejection
19. `verification/rounds_20/round_19_cascade_attachment_delete.png` — Cascade soft-delete of attached resources on lesson deletion
20. `verification/rounds_20/round_20_final_comprehensive_pass.png` — Comprehensive contract regression & specification pass (100%)
