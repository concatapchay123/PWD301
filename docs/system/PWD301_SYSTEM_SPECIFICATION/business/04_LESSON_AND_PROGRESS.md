# Lesson and Progress

## Confirmed rules
- Instructor-facing Bài học is a parent group above Lesson. Existing Lesson IDs and progress remain unchanged when the parent groups are introduced.
- Lessons are authored in a low-tech friendly, modular Vertical Block format (Text blocks, Video blocks, Document blocks, Interactive Quiz blocks) arranged freely by the instructor with simple Up/Down controls. Intrusive technical quota warnings are eliminated from the authoring surface.
- Lesson order is mutable globally; prior completion remains.
- Completion requires sequential block evaluation: text content strictly requires dwell time >= 60 seconds; video content strictly requires 100% video completion across all videos in the lesson; miniquiz requires passing score (default >= 80%). Complex reading-time or word-count calculations are permanently purged. The topbar progress percentage indicator (#console-course-progress-badge) is removed from the header entirely, and progress is shown only in course overview/outline.
- Direct download of raw lesson video files (.mp4, .webm) is forbidden for students; all internal video must be served via encrypted HLS (AES-128) with 12-hour (43,200s) DRM key token lifespan matching active student session.
- Video Protection & YouTube Standard 16:9 Player: Standard 16:9 full responsive viewport (100% width, 100% height, zero crop, preserving all video details) across all 4 touchpoints: Student learning view (primary and supplementary videos), Instructor preview modal (`openVideoModal`), Course Hero intro trailer (`#course-hero-media-box`), and Admin Review modal/pane (`renderReviewerCoursePreview`). Mandatory Cover Poster/Backdrop Shield conceals the player before user play interaction, revealing video only upon `PLAYING` state, with zero YouTube branding. Single event listener invariant eliminates play/pause toggle conflicts. `YT.Player` uses `youtube-nocookie.com` without conflicting `origin` parameter, eliminating Error 153. Resilient Playback Fallback: if YOUTUBE_API_KEY is not configured or Google Data API encounters issues, backend gracefully falls back to 3-tier duration fallback (oEmbed / client reported duration / lesson duration / safe default 1800s, min 300s) without raising LessonValidationError to block students, and reconciles duration on the first heartbeat. Pacing Engine & 5-Second Seek Unlock: Anti-forward seek restriction is strictly enforced from 00:00 up to (Duration - 5s). When video reaches the final 5 seconds (currentTime >= Duration - 5s, or video duration <= 5s), the system automatically credits video completion (`is_video_complete = true`, `unlocked = true`) and allows free scrubbing through the last 5 seconds to duration. Realtime Lesson Completion Gate (No F5 Reload): Lessons evaluate completion upon video end (`onEnded` event on YouTube state 0 and HTML5 ended) and miniquiz completion; Next button dynamically transitions from disabled gray (`bg-slate-200 text-slate-400 cursor-not-allowed`) to active emerald green (`bg-emerald-600 text-white cursor-pointer animate-fade-in`) and sidebar outline unlocks next lesson without requiring page refresh (F5). Client activity signals are not proof of attention.
- Progress cache is derived; lesson_progress/results are authoritative.
- Material rewrite does not reset completed students.
- New lesson is optional Xem thêm for existing periods/completed learners.

## Primary persistence
`learning_units`, `lessons`, `lesson_progress`, `enrollments`, `enrollment_periods`, `course_completion_rules`.

## Implementation obligations
- Validate state and object authorization before mutation.
- Use service-owned transaction boundaries; do not rely on UI validation.
- Emit audit/notification/job side effects only according to documented event policy.
- Preserve historical evidence instead of rewriting past records.

## Failure semantics
State violations return a stable conflict/state error; authorization failures disclose no protected details; required-audit sensitive mutations roll back.

## Tests
Trace to `../testing/03_BUSINESS_RULE_TEST_MATRIX.md`, domain-specific integration tests and `../testing/11_END_TO_END_SCENARIOS.md`.
