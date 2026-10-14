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
18. Unsafe/unscanned files cannot activate; scanner failure is fail-closed; video <1 GB.
19. FileAsset has at most one ACTIVE revision; shared blob deletion respects references/recovery.
20. RAG retrieves only currently authorized published content; archived/deleted/draft excluded.
21. Raw AI chat content purges after five minutes inactivity.
22. Important audit is append-only; required-audit sensitive action fails if audit cannot persist.
23. Admin override is explicit, reasoned and notified where required; no impersonation.
24. No broad cascade deletion of historical learning/assessment data.
25. Video DRM, Forensic Watermark & Zero-Trust Heartbeat: Enrolled students cannot download raw lesson video files (.mp4/.webm); all internal playback is served via encrypted HLS (AES-128) with short-lived tokens; internal HLS frames display dynamic forensic watermarks; YouTube identity is outside its unobscured iframe; DOM tampering triggers client blackout; and lesson completion strictly requires accumulated wall-clock heartbeat time on the server.
26. Strict Lifetime Enrollment (Ghi danh trọn đời): Course enrollment is permanent. Voluntary unenrollment / leave course is disabled (POST `/student/courses/<id>/leave` returns 403 Forbidden). Instructors cannot remove students from courses. Only Primary Admin may suspend or discipline student access.
27. Unified Staging Draft for Course Changes (Bản nháp tổng hợp toàn diện): All instructor updates on published courses (metadata, cover image, SLOs, syllabus, lessons, quizzes, resources) save into a unified staging draft (`STAGING_DRAFT` / `CourseVersionChangeset`). Fragmented piecemeal change requests are forbidden. Edits are submitted once for single all-or-nothing Admin review.
28. Anti-Leak Exam Security & Dynamic Progress: Real-time correct/incorrect indicators are strictly prohibited during active assessment attempts; drag-and-drop slots maintain neutral styling until submission; post-submission review renders granular green/red indicators with target answers. Course progress in student navigation is computed dynamically from actual completed lessons and never read from static mocks.
29. Two-Tier Broadcast Notification RBAC: Broadcast notifications to system users are restricted to two authorized tiers: Primary Admin (`ADMIN_PRIMARY`) may broadcast all categories; System Monitoring Admin (`ADMIN_SYSTEM_MONITORING`) is strictly restricted to `SYSTEM` broadcasts only (maintenance/infrastructure). All other sub-admins are denied broadcast permissions (HTTP 403).
30. Two-Mode Course Reassignment & Atomic Swap: Course ownership enforces single-instructor responsibility; courses may only be unassigned when the assigned instructor is suspended. Admin teaching reassignment strictly operates via two distinct modes: (1) Assigning unassigned courses, and (2) Transfer or atomic 2-way swap between two instructors, recorded in append-only AuditEvent.
31. Strict 20s Minimum Lesson Pacing & Header Cleanliness: Non-video lessons require a strict 20-second dwell time before the completion button activates; video lessons require 100% video playback. Reading-time calculations and word count pacing formulas are purged. The header progress gauge and in-lesson AI buttons are permanently decommissioned.
32. Anti-Defect Interactive Question Testing: Live preview test grading for interactive question authoring (Drag-and-Drop, Fill-in-the-Blank, Matching) verifies actual token text and values, eliminating false failure bugs caused by inner DOM icons, and provides immediate granular green/red visual highlighting.
33. Strict 16:9 Aspect Ratio Synchronization: Course cover images are locked to a strict 16:9 (`aspect-video` / 1280x720) ratio across crop modal, course editor preview, and student course exploration cards without height-clamping distortion.

