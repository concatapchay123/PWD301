# Lesson and Progress

## Confirmed rules
- Instructor-facing Bài học is a parent group above Lesson. Existing Lesson IDs and progress remain unchanged when the parent groups are introduced.
- Lessons are authored in a low-tech friendly, modular Vertical Block format (Text blocks, Video blocks, Document blocks, Interactive Quiz blocks) arranged freely by the instructor with simple Up/Down controls. Intrusive technical quota warnings are eliminated from the authoring surface.
- Lesson order is mutable globally; prior completion remains.
- Completion requires sequential block evaluation: text content strictly requires dwell time >= 60 seconds; video content strictly requires 100% video completion across all videos in the lesson; miniquiz requires passing score (default >= 80%). Complex reading-time or word-count calculations are permanently purged. The topbar progress percentage indicator (#console-course-progress-badge) is removed from the header entirely, and progress is shown only in course overview/outline.
- Direct download of raw lesson video files (.mp4, .webm) is forbidden for students; all internal video must be served via encrypted HLS (AES-128) with 12-hour (43,200s) DRM key token lifespan matching active student session.
- Video Protection & Clean Player Shell: Clean Player Shell for YouTube and uploaded media with container scaling (-14% top, 128% height), click shield overlay (pointer-events: none on iframe with transparent overlay), autoplay, mute, loop, zero external branding/controls, and visible watermark overlays on video are eliminated. Scrubbing frontier is enforced silently in the background; wall-clock pacing required. Client activity signals are not proof of attention.
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
