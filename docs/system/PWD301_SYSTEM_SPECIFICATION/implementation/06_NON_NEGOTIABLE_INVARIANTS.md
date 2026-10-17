# Non-Negotiable Invariants

1. No JWT in localStorage for website AJAX.
2. Suspended/deactivated User cannot continue active session/JWT.
3. Role is not enough; authorize the concrete resource.
4. One active EnrollmentPeriod per Student/Course logical Enrollment; capacity/prerequisite are race-safe.
5. Prerequisite cycles forbidden; active dependency blocks archive/delete.
6. Exposed/graded QuestionRevision is historical and retained.
7. Question type cannot change after a Student has answered.
8. Attempt snapshot is immutable historical evidence.
9. Server time is authoritative; close time is hard boundary.
10. One active editing lease; stale owner takeover keeps same Attempt.
11. Late/stale offline answer cannot overwrite newer or pass deadline.
12. Submit is idempotent; one logical result.
13. Assessment timing locked after publish.
14. Assessment structure/assigned points locked after first Student start.
15. Legitimate Question corrections remain possible through revision/regrade.
16. Grade/result changes append history; historical answers/snapshots not rewritten.
17. Detail purge after >30 days no-rejoin excludes that period from future regrade but preserves compact completion/prerequisite summary.
18. Unsafe/unscanned files cannot activate; scanner failure is fail-closed; strict 50MB non-archive attachment policy (archives .zip/.rar/.7z strictly forbidden); video <1 GB.
19. FileAsset has at most one ACTIVE revision; shared blob deletion respects references/recovery.
20. RAG retrieves only currently authorized published content; archived/deleted/draft excluded.
21. Raw AI chat content purges after five minutes inactivity.
22. Important audit is append-only; required-audit sensitive action fails if audit cannot persist.
23. Admin override is explicit, reasoned and notified where required; no impersonation.
24. No broad cascade deletion of historical learning/assessment data.
25. Video Protection & YouTube Clean Player Shell v2: Enrolled students cannot download raw lesson video files (.mp4/.webm); all internal playback is served via encrypted HLS (AES-128) with 12-hour (43,200s) DRM key token lifespan matching active student session. Clean Player Shell v2 for YouTube and uploaded media: container scaling (-14% top, 128% height in aspect-video overflow-hidden container), click shield overlay (pointer-events: none on iframe with transparent overlay), mandatory Cover Poster/Backdrop Shield concealing 100% of YouTube red play button and thumbnail before play (revealing video only upon PLAYING state), and zero YouTube branding. Universal application across 4 touchpoints: Student learning view, Course Hero intro trailer (autoplay, mute, loop on page load with floating mute/unmute and expand buttons), Trailer Lightbox modal (clean cropped shell instead of raw iframe), and Reviewer/Instructor preview modals (`renderReviewerCoursePreview`, `openVideoModal`, `mountTrailerPreview` clean cropped shell instead of raw iframe). `YT.Player` uses `youtube-nocookie.com` without conflicting `origin` parameter, eliminating Error 153. Resilient Playback Fallback: if YOUTUBE_API_KEY is not configured or Google Data API encounters issues, backend gracefully falls back to oEmbed / client reported duration / lesson duration / safe default (1800s, min 300s) without raising LessonValidationError to block students, and reconciles duration on the first heartbeat. Visible watermark overlays on video and seek-lock indicator badges are eliminated from UI. Scrubbing frontier is enforced silently in the background; wall-clock pacing required; lesson completion strictly requires accumulated wall-clock heartbeat time on the server.
26. Strict Lifetime Enrollment (Ghi danh trọn đời): Course enrollment is permanent. Voluntary unenrollment / leave course is disabled (POST `/student/courses/<id>/leave` returns 403 Forbidden). Instructors cannot remove students from courses. Only Primary Admin may suspend or discipline student access.
27. After first approval every legal instructor course change uses the existing COURSE_VERSION_CHANGESET/DRAFT aggregate (semantic STAGING_DRAFT). All instructor mutations freeze while submitted; withdraw before editing. See WORKFLOW_SUPERSESSION.md.
28. Anti-Leak Exam Security & Header Navigation: Real-time correct/incorrect indicators are strictly prohibited during active assessment attempts; drag-and-drop slots maintain neutral styling until submission; post-submission review renders granular green/red indicators with target answers. #console-course-progress-badge is removed from the header entirely; header displays only title and exit navigation. Course progress is displayed only in course outline/overview, eliminating obsolete header badge dynamic calculation.
29. Two-Tier Broadcast Notification RBAC: Broadcast notifications to system users are restricted to two authorized tiers: Primary Admin (`ADMIN_PRIMARY`) may broadcast all categories; System Monitoring Admin (`ADMIN_SYSTEM_MONITORING`) is strictly restricted to `SYSTEM` broadcasts only (maintenance/infrastructure). All other sub-admins are denied broadcast permissions (HTTP 403).
30. Two-Mode Course Reassignment & Atomic Swap: Course ownership enforces single-instructor responsibility; courses may only be unassigned when the assigned instructor is suspended. Admin teaching reassignment strictly operates via two distinct modes: (1) Assigning unassigned courses, and (2) Transfer or atomic 2-way swap between two instructors, recorded in append-only AuditEvent.
31. Sequential Lesson Completion Gate & Manual Button Abolition: The manual "Đánh dấu hoàn thành" button is permanently purged. Lessons evaluate blocks sequentially from top to bottom. A lesson marks complete and unlocks "Bài tiếp theo" if and only if ALL THREE conditions are satisfied: (1) Text content dwell time >= 60 seconds; (2) 100% watched for all videos in the lesson; (3) Miniquiz passing score >= instructor configured percentage (default 80%). The Next button is gray/disabled (bg-slate-200 text-slate-400 cursor-not-allowed) when incomplete, and transitions to emerald green/enabled (bg-emerald-600 text-white cursor-pointer) when complete.
32. Anti-Defect Interactive Question Testing: Live preview test grading for interactive question authoring (Drag-and-Drop, Fill-in-the-Blank, Matching) verifies actual token text and values, eliminating false failure bugs caused by inner DOM icons, and provides immediate granular green/red visual highlighting.
33. Strict 16:9 Aspect Ratio Synchronization: Course cover images are locked to a strict 16:9 (`aspect-video` / 1280x720) ratio across crop modal, course editor preview, and student course exploration cards without height-clamping distortion.
34. Fail-Closed 80% Backdrop Blurred "Câu hỏi" Modal with Anti-Bypass Lock: All in-lesson mini-quizzes are standardized to "Câu hỏi" and triggered as a high-impact modal with 80% blurred backdrop (`backdrop-blur-md bg-black/80`). Outside clicks and Esc are locked. Students must pass to close the modal and unlock next lesson. Unfinished state persists across reload/navigation, blocking any bypass.
35. Full-Width 16:9 Course Cover Banner: Course cover containers in Studio are full-width (`w-full aspect-video rounded-2xl border`), removing `max-w-3xl` restrictions and eliminating all blank side margins.
36. Never-approved courses permit direct validated authoring before submission. Ever-approved includes APPROVED/PUBLISHED/ARCHIVED or trustworthy historical approval, including legacy published rows missing approved_at; this boundary cannot return to free authoring.

37. Media access does not require email verification; authentication, enrollment, authorization, scan safety and learner raw-video denial remain enforced.
38. Hiding assessment details preserves released total/pass and empties three PDF detail cells. Backend summary governs counts, state and configured earned score. See WORKFLOW_SUPERSESSION.md.
