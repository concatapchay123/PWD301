# Project: PWD301 Media & Completion Overhaul

## Architecture
- **Platform Architecture**: Pure Headless Flask REST API backend with client-side Vanilla JS SPA, SQL Server database, and Chrome DevTools MCP browser verification.
- **File Management & Security**: Fail-closed upload pipeline. Strict 50MB (50,000,000 bytes) attachment ceiling for non-video files. Strict non-archive policy (.zip, .rar, .7z forbidden). Support for documents, CAD (.dwg, .dxf), and 3D models.
- **Video DRM & Playback**: AES-128 HLS stream delivery. 12-hour (43,200s) DRM key token lifespan matching active student sessions. Independent per-video progress tracking via `MediaProgress`. Silent 100% completion requirement across all videos in a lesson.
- **Frontend Video Player & Completion Gate**:
  - Clean Player Shell for hero YouTube intro: container scaling (-14% top, 128% height), click-shield overlay, autoplay, mute, loop, no external controls/branding.
  - Header cleanup: eliminate `#console-course-progress-badge`.
  - Local video: independent trackers for supplementary videos, robust VideoArmor without false-positive blackouts.
  - Sequential completion gate: 60s dwell time for text, 100% video watch, miniquiz passing %. Next button gray/disabled -> emerald green/enabled.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| F1 | Purge Legacy Specs & Invariants | Remove obsolete dynamic header progress rules from AGENTS.md, docs, and code; lock 50MB non-archive invariant, Clean Player hero intro invariant, and sequential completion invariant | M1 | ORIGINAL_REQUEST R1 |
| F2 | Archive Rejection Policy | Block archives (.zip, .rar, .7z, .tar, .gz, .bz2, .xz, .iso) in `scanner_service.py` and `file_service.py` with exact Vietnamese error message | M2 | ORIGINAL_REQUEST R2 |
| F3 | CAD & 3D Model Support | Whitelist and validate AutoCAD (.dwg, .dxf) and 3D files (.obj, .fbx, .stl, .blend, .step, .gltf, .glb) | M2 | ORIGINAL_REQUEST R2 |
| F4 | 50MB Attachment Ceiling | Enforce strict 50,000,000 bytes limit across backend file upload endpoints, config, and stream checkers | M2 | ORIGINAL_REQUEST R2 |
| F5 | Draft & Staging Resource Upload Fix | Prevent `is_identical` from soft-deleting staged draft lessons with new resources in `instructor/routes.py`, fix frontend lesson ID sync | M2 | ORIGINAL_REQUEST R2 |
| F6 | 12-Hour DRM Key Token Lifespan | Extend DRM key token expiration from 60s to 43,200s in `video_drm_service.py` and `student/routes.py` | M3 | ORIGINAL_REQUEST R3 |
| F7 | Independent Multi-Video Tracking | Track each video in a lesson independently via `MediaProgress` and fix `playback_service.py` to aggregate all video frontiers | M3 | ORIGINAL_REQUEST R3 |
| F8 | Silent 100% Video Completion | Require all videos in a lesson to reach 100% (within 0.5s tolerance) for video completion and quiz unlock, with no visible % badge | M3 | ORIGINAL_REQUEST R3 |
| F9 | Header Progress Badge Elimination | Remove `#console-course-progress-badge` and update functions in `frontend/assets/js/views/student.js` | M4 | ORIGINAL_REQUEST R4 |
| F10 | Clean Player Shell for Hero Trailer | YouTube trailer container scaling, negative margins, click shield, autoplay, mute, loop, no controls/buttons/branding in `student.js` | M4 | ORIGINAL_REQUEST R4 |
| F11 | Instructor Upload UI Hardening | Update button label to "Tải tệp đính kèm (PDF, Word, Excel, PPT, CAD, 3D...)", update accept list, client-side reject archives & >50MB files in `instructor.js` | M4 | ORIGINAL_REQUEST R4 |
| F12 | Local & Supplementary Video Fix | Attach independent trackers to supplementary videos, fix VideoArmor sub-pixel opacity checks to prevent false blackouts | M5 | ORIGINAL_REQUEST R5 |
| F13 | Sequential Completion Gate | Enforce 60s dwell time for text, 100% video watch, miniquiz passing % in `student.js` | M5 | ORIGINAL_REQUEST R5 |
| F14 | Next Button State Machine | Gray and disabled (no lock icon/text) when incomplete; emerald green and enabled when complete | M5 | ORIGINAL_REQUEST R5 |
| F15 | Chrome DevTools Real Browser Verification | Execute 20-round verification loop (R01-R20) via Chrome DevTools MCP with annotated screenshots | M6 | ORIGINAL_REQUEST R6 |
| F16 | Multi-Tier Quality Gates | 100% pass on `repo_check.py`, `ruff`, `mypy`, backend pytest, and frontend node test suite | M6 | ORIGINAL_REQUEST R6 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Purge Legacy Contracts and Specs | Update `AGENTS.md`, `docs/`, `config.py` comments to lock 50MB non-archive invariant, Clean Player hero intro, sequential completion, and header cleanup | none | DONE |
| M2 | Backend Attachment Hardening | Implement archive blocking, CAD/3D support, 50MB ceiling, and fix draft/staging resource upload in `file_service.py`, `scanner_service.py`, `instructor/routes.py`, `config.py` | none | DONE |
| M3 | Backend HLS DRM & Multi-Video Tracking | Extend DRM token to 12h, implement independent multi-video tracking and silent 100% completion in `video_drm_service.py`, `playback_service.py`, `lesson_service.py`, `student/routes.py` | none | DONE |
| M4 | Frontend Clean Player Shell & Header Cleanup | Eliminate `#console-course-progress-badge`, implement Clean Player Shell for hero trailer, update instructor upload UI in `student.js` and `instructor.js` | M1 | DONE |
| M5 | Frontend Local Video & Sequential Gate | Fix supplementary video trackers and VideoArmor, implement 60s dwell, 100% video, quiz passing % sequential gate, Next button transitions in `student.js` | M3, M4 | DONE |
| M6 | Chrome DevTools Browser Verification & Gates | 20-round browser verification loop with annotated screenshots and complete repository static/unit test checks | M1, M2, M3, M4, M5 | DONE |

## Code Layout
- `AGENTS.md`: Canonical operational contract for coding agents.
- `docs/system/PWD301_SYSTEM_SPECIFICATION/`: System specifications and business rules.
- `docs/database/PWD301_DATABASE_ARCHITECTURE/`: Canonical database documentation and DDL.
- `src/pwd301/config.py`: Application configuration and size limits.
- `src/pwd301/services/file_service.py`: File storage, document validation, and resource attachments.
- `src/pwd301/services/scanner_service.py`: MIME type validation, magic byte checking, malware scanning.
- `src/pwd301/services/video_drm_service.py`: AES-128 DRM encryption and token generation/verification.
- `src/pwd301/services/playback_service.py`: Video playback leases, heartbeats, and progress aggregation.
- `src/pwd301/services/lesson_service.py`: Lesson completion criteria and quiz prerequisites.
- `src/pwd301/blueprints/instructor/routes.py`: Instructor API routes (resource upload, lesson update).
- `src/pwd301/blueprints/student/routes.py`: Student API routes (lesson detail, HLS key serving, playback heartbeat).
- `frontend/assets/js/views/student.js`: Student console view, video player, sequential completion gate.
- `frontend/assets/js/views/instructor.js`: Instructor course editor view, attachment upload.
- `frontend/assets/js/components/video-armor.js`: Video protection overlay and DOM tamper detection.
- `tests/unit/test_file_service.py`: Unit tests for file validation and limits.
- `tests/unit/test_video_drm_service.py`: Unit tests for DRM key tokens.
- `tests/unit/test_playback_sessions.py`: Unit tests for playback heartbeats and multi-video tracking.
- `tests/api/test_instructor_routes.py`: Integration tests for resource upload and staging draft preservation.

## Interface Contracts

### Instructor Upload API
- `POST /instructor/courses/<course_id>/lessons/<lesson_id>/resources`:
  - Request: `multipart/form-data` with `file` and optional `title`.
  - Max size: 50,000,000 bytes.
  - Allowed types: Word, PDF, Excel, PowerPoint, text, AutoCAD (`.dwg`, `.dxf`), 3D/render (`.obj`, `.fbx`, `.stl`, `.blend`, `.step`, `.gltf`, `.glb`).
  - Forbidden types: `.zip`, `.rar`, `.7z`, `.tar`, `.gz`, `.bz2`, `.xz`, `.iso`.
  - Error response on archive: HTTP 400 Bad Request `{"success": false, "error": "Hệ thống không hỗ trợ tệp nén (.zip, .rar, .7z...). Vui lòng tải trực tiếp tài liệu học tập (PDF, Word, Excel, CAD, 3D...)"}`.
  - Error response on >50MB: HTTP 413 Payload Too Large.
  - Success response: HTTP 201 Created `{"success": true, "data": {"id": <resource_id>, "lesson_id": <staged_or_draft_lesson_id>, "title": ..., "file_name": ..., "size_bytes": ...}}`.

### Student Lesson Playback & DRM API
- `GET /student/courses/<course_id>/lessons/<lesson_id>/video/<asset_id>/key?token=<token>`:
  - Token validity: 43,200 seconds (12 hours) from generation.
  - Requires authenticated enrolled student session.
  - Response: 16-byte raw AES-128 key.
- `POST /student/courses/<course_id>/lessons/<lesson_id>/playback/heartbeat`:
  - Request: `{"lease_id": ..., "media_id": ..., "sequence": ..., "position": ..., "rate": ..., "wall_clock_elapsed": ...}`.
  - Response: `{"success": true, "data": {"session_id": ..., "media_id": ..., "frontier": ..., "duration": ..., "is_video_complete": <bool>, "all_videos_complete": <bool>, "is_completed": <bool>}}`.
  - Invariant: `all_videos_complete` is `true` if and only if EVERY video associated with the lesson has `frontier >= duration - 0.5`.

### Sequential Completion Gate Interface (Frontend)
- Inputs:
  - `hasText`: boolean (`lesson.markdown_content && lesson.markdown_content.trim()`).
  - `dwellElapsed`: number (`seconds_spent`). Required: >= 60 seconds.
  - `hasVideo`: boolean. Required: `all_videos_complete === true` (100% watched).
  - `hasMiniQuiz`: boolean. Required: `score >= (lesson.quiz_passing_percent || 80)`.
- Outputs:
  - `isLessonRequirementsMet()`: `dwellOk && videoOk && quizOk`.
  - `#cisco-next-btn`:
    - `meetsAll === false`: `disabled = true`, classes `bg-slate-200 text-slate-400 cursor-not-allowed`, NO lock icon, NO "Đã khóa" text.
    - `meetsAll === true`: `disabled = false`, classes `bg-emerald-600 text-white cursor-pointer`.
