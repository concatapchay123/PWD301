# TASK-097 — PWD301 Media & Completion Overhaul (Attachment Policy, Clean Player Shell, HLS DRM 12h, Sequential Completion Gate)

**Status:** VERIFIED
**Approved:** 2026-10-17
**Contract:** [AGENTS.md](../AGENTS.md), [WORKFLOW_SUPERSESSION](../docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/WORKFLOW_SUPERSESSION.md)
**Plan:** [plan.md](file:///C:/Users/LENOVO/.gemini/antigravity/brain/e45be8fb-6038-4262-b9fd-520f3234dc53/plan.md)

Active implementation scope & empirical verification evidence:
1. **R1. Purge Legacy Contracts and Specs**:
   - Eliminated all conflicting legacy specs, docs, and comments across `docs/`, `AGENTS.md`, and code.
   - Locked 4 core platform invariants: 50MB attachment limit, no archive files (`.zip`, `.rar`, `.7z` forbidden), Clean Player YouTube intro (autoplay, loop, no controls), sequential completion (dwell >= 60s, 100% video, miniquiz passing %), and elimination of `#console-course-progress-badge`.
   - Verified by empirical script: `python scripts/verify_m1_docs_invariants.py` -> 100% PASS across 327 active documentation files.
2. **R2. Backend Attachment Hardening (50MB Non-Archive Policy)**:
   - Whitelisted Word, PDF, Excel, PowerPoint, Text, AutoCAD (`.dwg`, `.dxf`), 3D models (`.obj`, `.fbx`, `.stl`, `.blend`, `.step`, `.stp`, `.gltf`, `.glb`).
   - Enforced strict 50,000,000 bytes limit in `file_service.py` and `scanner_service.py`.
   - Prohibited archives with exact Vietnamese message: `"Hệ thống không hỗ trợ tệp nén (.zip, .rar, .7z...). Vui lòng tải trực tiếp tài liệu học tập (PDF, Word, Excel, CAD, 3D...)"`.
   - Instructor file input accept list excludes archives; client-side pre-flight validation prevents archive selection and blocks >50MB files immediately.
   - Verified in real browser: [verify_t97_r2_attachment_policy.png](file:///e:/PWD301/verification/verify_t97_r2_attachment_policy.png)
3. **R3. Backend HLS DRM & Multi-Video Tracking**:
   - Extended DRM key token expiration to 43,200s (12 hours) matching user session duration in `video_drm_service.py`.
   - Tracked all video media independently via `MediaProgress`.
   - Multi-video lesson completion gate requires 100% watched threshold across all videos.
   - Verified by backend pytests: `tests/test_m3_t97_challenger2.py` & `tests/api/test_hls_stream_adversarial_challenge.py` -> 100% PASS.
4. **R4. Frontend Clean Player Shell YouTube Intro & Header Cleanup**:
   - Removed `#console-course-progress-badge` from header markup and no-oped `updateConsoleCourseProgressBadge` safely.
   - Clean Player Shell for hero trailer: container scaling (`top: -14%`, `height: 128%`, `pointer-events: none`), transparent shield overlay (`#hero-trailer-shield`), clean embed parameters (`autoplay=1&mute=1&loop=1&playlist=${ytId}&controls=0...`).
   - Verified in real browser: [verify_t97_r4_youtube_clean_shell.png](file:///e:/PWD301/verification/verify_t97_r4_youtube_clean_shell.png)
5. **R5. Frontend Local Video Playback & Sequential Completion Gate**:
   - Local video playback robust with `VideoArmor` silent watermark (`silentWatermark: true`), eliminating false-positive blackouts.
   - Sequential block evaluation:
     - Text content: dwell time >= 60 seconds (independent requirement).
     - Video content: 100% watched for all videos (silent background calculation).
     - Miniquiz: score >= instructor configured percentage (default 80%).
   - Next button `#cisco-next-btn`:
     - Incomplete: gray, disabled (`px-5 py-2.5 rounded-xl bg-slate-200 dark:bg-slate-800 text-slate-400 dark:text-slate-500 cursor-not-allowed select-none`), NO lock icon, NO "Đã khóa" text.
     - Complete: emerald green (`px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white cursor-pointer`).
   - Verified in real browser (Incomplete state): [verify_t97_r5_incomplete_next_btn.png](file:///e:/PWD301/verification/verify_t97_r5_incomplete_next_btn.png)
   - Verified in real browser (Complete state): [verify_t97_r5_complete_next_btn.png](file:///e:/PWD301/verification/verify_t97_r5_complete_next_btn.png)
6. **R6. Test Suites Execution & Verification**:
   - `python scripts/repo_check.py`: PASS (all repository contracts intact, exit code 0).
   - `node --test tests/frontend/*.test.js`: 347/347 PASS across all suites (0 failed, 0 skipped).
   - `pytest tests/test_m2_t97_challenger2.py tests/test_m3_t97_challenger2.py tests/test_m4_t97_challenger2.py tests/api/test_hls_stream_adversarial_challenge.py tests/unit/test_file_service.py tests/unit/test_video_drm_service.py`: 84/84 PASS (0 failed, 0 skipped).
