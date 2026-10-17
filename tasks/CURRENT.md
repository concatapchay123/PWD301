# TASK-099 — PWD301 Clean Player Shell v3, Pause Fix, Global Anti-Tamper Blackout Shield & Ambient Hero Trailer

**Status:** COMPLETED  
**Approved:** 2026-10-18  
**Completed:** 2026-10-18  
**Contract:** [AGENTS.md](../AGENTS.md), [WORKFLOW_SUPERSESSION](../docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/WORKFLOW_SUPERSESSION.md)  
**Plan:** `C:\Users\LENOVO\.gemini\antigravity\brain\53c4b2f3-e19f-4b21-84c2-abfc718b1605\plan_video_clean_shell_v3_and_security.md`  

## Objective & Invariant Supersession
- **Clean Player Shell v3**: Scaled geometry (`top: -22%`, `left: -5%`, `width: 110%`, `height: 144%`), `pointer-events: none` on iframe, transparent Click Shield, and Poster Shield concealing 100% of YouTube red button until `PLAYING` (state 1).
- **Single Event Listener (Pause Fix)**: Eliminates duplicate `onclick` registration in `student.js`, ensuring crisp, instant Play/Pause toggle.
- **Global Anti-Tamper & Blackout Shield**: Intercepts F12, Ctrl+Shift+I/J/C, Ctrl+U, PrintScreen, Win+Shift+S, disables right-click `contextmenu`, and uses DevTools console/debugger traps to trigger Blackout Shield with red warning and restore button across Student Learning Console and Exam Taking views.
- **Ambient Hero Trailer (Zero-Button Invariant)**: Pure ambient autoplay muted loop on Course Detail page; eliminates all buttons ("Bật tiếng", "Phóng to", big play button) and eliminates click-to-modal expansion.
- **Browser Verification Loop (Max 20 Rounds)**: Real browser verification with high-res annotated screenshots for each milestone.

## Milestones & Execution Checklist

- [x] **M1. Spec & Outdated Documentation Cleansing**
  - Updated `AGENTS.md` (Section 4 & Section 10.8) to supersede old -14% crop, trailer buttons, and old devtools rules.
  - Verified repository integrity via `python scripts/repo_check.py` (Passed 100%).

- [x] **M2. Core Video Player & Pause Fix (Student Console)**
  - Fixed double-click toggle bug in `setupCustomVideoPlayer` (`student.js`): removed `el.onclick = wrapped;`, retaining single `listen(el, 'click', wrapped)`.
  - Upgraded geometry to Clean Player Shell v3 (`top: -22%`, `left: -5%`, `width: 110%`, `height: 144%`).
  - Concealed YouTube red play button 100% under Poster Shield before play (`z-[15] z-15 bg-slate-950`).
  - Unit test verification in `tests/frontend/student_video_playback.test.js` (Passed 100%).

- [x] **M3. Instructor & Reviewer Clean Player Shell v3 Unification**
  - Upgraded `InstructorView.openVideoModal` (`instructor.js`) to Clean Player Shell v3 with custom controls (Play/Pause, Mute, Speed, Fullscreen).
  - Upgraded `AdminView._getCleanYouTubeShellHtml` and `renderReviewerCoursePreview` (`admin.js`) to Clean Player Shell v3.
  - Unit test verification in `tests/frontend/reviewer_course_preview.test.js` (Passed 100%).

- [x] **M4. Ambient Hero Trailer Revamp (Course Detail)**
  - Revamped `#course-hero-media-box` to Clean Player Shell v3 ambient loop (`autoplay=1&mute=1&loop=1`).
  - Removed "Bật tiếng", "Phóng to", big play buttons, and click-to-modal expansion (`openTrailerLightbox` removed).

- [x] **M5. Global Anti-Tamper & Blackout Shield Implementation**
  - Upgraded `video-armor.js` with F12, Ctrl+Shift+I/J/C, Ctrl+U, PrintScreen, Win+Shift+S, Meta+Shift+S, contextmenu interception, and DevTools timing detection.
  - Implemented Blackout Shield with red warning "🛡️ CẢNH BÁO AN NINH BẢN QUYỀN", media pausing, clipboard clearing, and "Khôi phục và Tiếp tục học" button.
  - Connected VideoArmor to Student Learning Console (`student.js`) and Exam Taking views (`exam-store.js` / `student.js`).
  - Unit test verification in `tests/frontend/video_armor.test.js` and `tests/frontend/video_armor_adversarial_challenge.test.js` (Passed 100%).

- [x] **M6. Real Browser Automation & Annotated Screenshot Verification Loop (Max 20 Rounds)**
  - Real browser Playwright script `scripts/verify_comprehensive_video_and_security.py` executed with Chrome.
  - Verified 5/5 touchpoints with high-res annotated proof screenshots:
    1. `verification/verify_hero_trailer_ambient_loop.png` (181.83 KB, 1920x1080)
    2. `verification/verify_student_poster_shield_unplayed.png` (115.22 KB, 1920x1080)
    3. `verification/verify_student_player_play_pause.png` (161.34 KB, 1920x1080)
    4. `verification/verify_teacher_preview_clean_shell.png` (189.95 KB, 1440x950)
    5. `verification/verify_anti_tamper_blackout_shield.png` (137.96 KB, 1920x1080)
