# Project: PWD301 LMS Comprehensive Upgrade (Gen 9)

## Architecture
- **Platform Architecture**: Pure Headless Flask REST API backend with client-side Vanilla JS SPA, SQL Server database, and Chrome DevTools MCP browser verification.
- **Brand Identity & Document Design**: PPTQ brand logo across Topbar, Auth, Profile, and PDF Gradebook (Header + subtle centered watermark). Gradebook strictly outputs "KHÔNG ĐẠT" (bold red `#B91C1C`) for non-passing attempts; legacy term "HỎNG" is permanently forbidden.
- **Video Protection & Standard 16:9 Viewport**: Standard 16:9 full responsive viewport (`w-full aspect-video`, 100% width, 100% height, zero crop) across 4 touchpoints: Student learning view, Instructor preview modal, Course Hero intro trailer, and Admin Review modal. The legacy cropping style (`-22% top, 144% height`) is completely eliminated.
- **Pacing Engine & 5-Second Scrub Unlock**: Video completion is credited (`unlocked = true, videoWatched = true`) when remaining duration is <= 5 seconds (or video <= 5s), allowing free scrubbing in the final 5 seconds.
- **Realtime Lesson Completion Gate (No F5 Reload)**: Listens to `onEnded` event on both YouTube (`event.data === 0`) and HTML5 video. Next button immediately activates (`bg-emerald-600 cursor-pointer animate-fade-in`) and curriculum sidebar unlocks the next lesson without page reload.
- **Cascade Document Management**: Soft-deleting a lesson or learning unit cascades to `_cleanup_lesson_resources` and trashes orphaned `FileAsset` entries. Instructor Studio provides active lesson attached documents and a Course Document Tree modal mirroring student view.
- **Site-Wide Anti-Tamper Security Shield**: Global `VideoArmor.installGlobalShield()` across all authenticated routes. Confirmed DevTools / shortcut tampering triggers full-screen Blackout Shield ("🛡️ CẢNH BÁO AN NINH HỆ THỐNG"), server-side session revocation (`POST /auth/logout`), client token purge, and redirect to login.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| F1 | Spec & Documentation Cleansing | Purge legacy crop (-22% top, 144% height), 'HỎNG', and old scrub rules from AGENTS.md, tasks/CURRENT.md, and docs/system/ | M1 | Item 1 |
| F2 | PPTQ Logo Extraction & Replacement | Extract PPTQ logo from docx and replace old logo across Topbar, Auth, Profile, and PDF Gradebook Header/Watermark | M2 | Item 2 |
| F3 | 16:9 Clean Player Ratio Across 4 Views | Remove -22% top, 144% height across Student, Instructor, Hero Trailer, and Admin Review; restore clean 16:9 ratio | M3 | Item 3 |
| F4 | Admin Review YouTube Black Screen Fix | Mount YouTube player to `<div id="${playerId}-yt">` instead of iframe in Admin Review, allowing YT.Player to mount and hide poster shield | M3 | Item 3 |
| F5 | 5-Second Scrub Unlock (Backend & Frontend) | Credit video complete and unlock free scrubbing in the final 5 seconds in playback_service.py and student.js | M4 | Item 4 |
| F6 | Realtime onEnded Next Button Activation | Fire options.onEnded on YouTube state 0 and HTML5 ended to dynamically activate emerald green Next button without F5 | M5 | Item 5 |
| F7 | Cascade Document Cleanup | Soft-delete/trash attached resources on lesson/chapter deletion; filter deleted_at in file_service.py:list_course_files | M6 | Item 6 |
| F8 | Instructor Document Tree & Lesson Docs | Add active lesson attached document list and Course Document Tree modal in Instructor Studio | M6 | Item 6 |
| F9 | Gradebook PDF Terminology 'KHÔNG ĐẠT' | Replace 'HỎNG' with bold red 'KHÔNG ĐẠT' (#B91C1C) in result_pdf_service.py | M7 | Item 7 |
| F10 | Full-Page VideoArmor Security Shield | Upgrade VideoArmor to global shield with shortcut/DevTools trap, Blackout Shield, POST /auth/logout, and redirect | M8 | Item 8 |
| F11 | Chrome DevTools Browser Testing & 11 Screenshots | 11 annotated screenshot proofs covering all features on port 51095 fixture | M9 | Item 9 |
| F12 | Multi-Tier Quality Gates | 100% pass on repo_check.py, ruff, mypy, backend pytest, and frontend node test suite | M9 | Invariant |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Spec & Documentation Cleansing | Update `docs/system/` specifications and contract test assertions | none | PLANNED |
| M2 | PPTQ Logo Extraction & Integration | Verify and finalize PPTQ logo in Topbar, Auth, Profile, and PDF | none | PLANNED |
| M3 | 16:9 Ratio & Admin Review YouTube Fix | Remove crop styles across 4 views, fix Admin Review mount bug, update frontend tests | M1 | PLANNED |
| M4 | 5-Second Scrub Unlock | Update `playback_service.py` and `student.js` for 5s scrub unlock and completion | none | PLANNED |
| M5 | Realtime onEnded Next Lesson Activation | Wire `onEnded` event on YouTube and HTML5 in `student.js` | M4 | PLANNED |
| M6 | Cascade Document Cleanup & Instructor Tree | Backend file filter + Instructor Studio lesson doc card and Course Document Tree modal | none | PLANNED |
| M7 | Gradebook PDF Terminology 'KHÔNG ĐẠT' | Verify and lock 'KHÔNG ĐẠT' in `result_pdf_service.py` and gradebook tests | none | PLANNED |
| M8 | Full-Page VideoArmor Security Shield | Install global VideoArmor shield with server logout & redirect in `video-armor.js` and `router.js` | none | PLANNED |
| M9 | Browser Verification & 11 Screenshots | Execute 11-step browser verification loop on port 51095 with annotated screenshots and quality gates | M1-M8 | PLANNED |

## Code Layout
- `AGENTS.md`: Canonical operational contract for coding agents.
- `tasks/CURRENT.md`: Current execution scope tracking.
- `docs/system/PWD301_SYSTEM_SPECIFICATION/`: System specifications and business rules.
- `src/pwd301/services/playback_service.py`: Video playback leases, heartbeats, 5s scrub unlock.
- `src/pwd301/services/result_pdf_service.py`: Gradebook PDF generation with PPTQ logo & 'KHÔNG ĐẠT'.
- `src/pwd301/services/lesson_service.py`: Lesson & chapter deletion cascade.
- `src/pwd301/services/file_service.py`: Course file query filtering.
- `frontend/index.html`: Topbar brand logo.
- `frontend/assets/js/views/auth.js`: Login/Register brand logo & security alert banner.
- `frontend/assets/js/views/student.js`: Student player 16:9 ratio, 5s scrub unlock, onEnded next lesson.
- `frontend/assets/js/views/instructor.js`: Instructor preview 16:9 ratio, active lesson doc card & document tree modal.
- `frontend/assets/js/views/admin.js`: Admin Review 16:9 clean YouTube player mounting.
- `frontend/assets/js/components/video-armor.js`: Global site-wide security shield, DevTools trap & logout.
- `frontend/assets/js/router.js`: Global VideoArmor initialization on authenticated routes.
- `verification/`: Annotated screenshot evidence for the 11 verification steps.
