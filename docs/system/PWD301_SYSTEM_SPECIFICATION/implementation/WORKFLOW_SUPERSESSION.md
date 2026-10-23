# Workflow replacement contract — 2026-10-15

Status: USER APPROVED; IMPLEMENTATION IN PROGRESS. This is the authoritative
replacement contract for the workflows below. A previous task marked completed
is historical evidence, not evidence that this contract has been implemented.

## Course governance

1. A never-approved course permits direct instructor authoring until initial
   submission. Initial pending review freezes all instructor mutations; withdraw
   before editing. Validation, ownership and file safety always apply.
2. After first approval every legal instructor change belongs to exactly one
   course aggregate: `CourseChangeRequest(change_type=COURSE_VERSION_CHANGESET,
   status=DRAFT)`, semantically `STAGING_DRAFT`. This is the existing persistence
   model, not a second table or a `CourseVersionChangeset` Python class.
3. Metadata, cover, outcomes, curriculum, lessons, resources, questions,
   assessment settings, completion rules and prerequisites use the same gate in
   session and JWT APIs. Clients cannot opt out with `as_draft` or legacy routes.
4. Ever-approved includes approved_at, trustworthy approval history and existing
   APPROVED/PUBLISHED/ARCHIVED state. Legacy published rows missing approved_at
   require staging; do not invent an approval date or downgrade to free authoring.
5. The instructor reads the effective draft; students read approved content.
   Creating/navigating to an editor never creates a draft without an explicit save.
6. Submission seals a complete version and its referenced asset versions. Pending
   review freezes changes. Approval applies exactly that version in one audited
   transaction; reject/withdraw retains history and restores the complete editable
   proposal. Keep referenced assets; recheck current file safety at approval.
7. Review actions identify the displayed request and expected version. Stale
   approve/reject/withdraw returns 409. Serialize prerequisite graph changes and
   revalidate cycles/dependencies during approval, not just draft validation.
8. Queue rows represent actual initial submissions and aggregate updates. Never
   hide unmerged sibling proposals to pretend a course has one complete request.

## Learning media and interaction

- Email verification is not a video or course-file access condition. Authentication,
  active enrollment, object authorization, suspension, scanning and HLS protection
  remain mandatory. Learners cannot fetch raw video via download or Range preview.
- Production playback needs working FFmpeg, authenticated HLS manifests/segments/
  keys, official YouTube IFrame API and meaningful recoverable playback errors.
  Browser protection is best effort and cannot guarantee blocking screen recording.
- Matching uses the same presentation/controller contract for preview and learners,
  with stable choice keys, working SVG, selection/reassignment/clear and restored
  answers. Active exams never receive correctness/answer keys or grading colors.
- Course covers use the existing 1280x720 crop, 16:9 on every surface including
  initial/updated Admin review. Review displays the proposed authorized asset.

## Assessment presentation and result disclosure

- Backend owns attempts, resumability, timing, blocking reason, actual assigned
  question count and completion. An attempt limit is not completion or a
  prerequisite failure. A final assessment does not require its own completion.
- Display earned score under the label `Điểm`, using FIRST/LATEST/HIGHEST/AVERAGE
  over valid graded attempts. Zero is a real score. Keep best_attempt_id meaning
  highest and respect score-release policy on every list, detail and history API.
- `allow_student_view_results=false` hides selections, correctness, per-question
  scores, feedback and explanations, but keeps released total score and pass/fail.
  Explicit NEVER retains its stricter no-question-detail contract. Release timing
  has priority. Instructor/Admin review remains independently authorized.
- The PDF retains question stems where permitted and leaves selected-answer,
  result and question-score cells genuinely empty when details are hidden.
- ReportLab layout is retained. Render supported TeX offline to self-contained
  MathJax SVG and import with svglib; do not substitute partial regex math.
  Bound inputs/process resources, reject unsafe external content and render with
  production fonts. Invalid math must not silently become corrupt transcript text.

## Replacement register and verification ledger

| ID | Superseded behavior / locations | Disposition and replacement | Verification gate | Status |
|---|---|---|---|---|
| WF01 | Per-feature/lesson approval; opt-in as_draft; course/lesson/completion services | Replace with mandatory one-course aggregate after first approval | API lifecycle, pending freeze, concurrent submit, rollback | PENDING |
| WF02 | Only current PUBLISHED gates review; old CURRENT/invariants/memory | Replace with monotonic ever-approved boundary | APPROVED and legacy published-with-null-marker cases | PENDING |
| WF03 | Metadata lost on withdraw/reject, live reviewer diff, promoting unrelated drafts | Replace with complete successor draft and sealed submission | Reload, withdraw/resubmit, stale Admin tab, exact member approval | PENDING |
| WF04 | Queue dedup hides proposals; old cover URL and capped aspect ratio | Remove lossy filtering; accurate queue and proposed 16:9 asset | Multiple courses/changes, counts, browser cover inspection | PENDING |
| WF05 | Hidden prerequisites and incorrect academic metadata keys | Reuse academic editor and canonical completion/prerequisite services | Persist/reload, cycle, same aggregate | PENDING |
| WF06 | Email-gated media and raw Range learner bypass | Remove email gate; retain authorization and deny raw video | Unverified enrolled HLS/YouTube; raw stream denied; reviewer 206 | PENDING |
| WF07 | Divergent matching markup, text/key restore mismatch | Shared renderer/controller contract, neutral live exams | Real DOM interaction, autosave/restore, authorized review | PENDING |
| WF08 | Fake 30/0 counts, can_start=false means prerequisite, threshold shown as score | Backend summary/count/scoring policy | Active/closed/exhausted/prerequisite, 0 score, FIRST/LATEST/HIGHEST/AVERAGE | PENDING |
| WF09 | Hidden-details toggle hides total or leaks history; PDF dash cells | Released totals retained, detail masking everywhere, empty cells | Web/JWT disclosure matrix and rendered PDF | PENDING |
| WF10 | Partial regex LaTeX, local-only rendering assumptions | Offline MathJax SVG to ReportLab | Nested fractions/roots/integrals/matrices; Linux visual proof | PENDING |
| WF11 | Center logo box and email placeholder / footer text on Login | Clean minimalist login with PPTQ logo at top-left corner, empty email placeholder, removed footer text | Visual check, DOM verification | PENDING |
| WF12 | Course metadata locked to small modal on intro page | Inline editing + double-click directly on Course Header with staging auto-save | Double click, form inputs, auto-save network check | PENDING |
| WF13 | No clipboard image paste in lesson Word editor | Paste event intercept, ClamAV fail-closed upload, inline <img> insertion | Clipboard paste event, ClamAV scan, inline render | PENDING |
| WF14 | Fragmented vertical stack of quiz block cards | Single Miniquiz session card with Question Stepper tabs [Câu 1..N] and [+] button | Multi-quiz add, tab switching, delete question/session | PENDING |
| WF15 | [SUPERSEDED by WF23] Tolerated multi-device concurrent sessions | Superseded by Single Active Device Takeover (WF23): second login succeeds immediately (200 OK), evicts previous device politely | Single Active Device Takeover, polite eviction modal, 0ms SSE push | VERIFIED |
| WF16 | Course preview inside small popup modal | Direct preview in new browser tab (_blank) mirroring student learning view 100% | window.open, student reader route, full content render | PENDING |
| WF17 | Auto-logout on screenshot/contextmenu everywhere | Only warn + record violation count during exams; free contextmenu/screenshots during study; logout reserved for DevTools/scraping | Exam anti-cheat events, study page screenshot, DevTools lockdown | PENDING |
| WF18 | Browser native alert/confirm/prompt for course deletion | Dedicated system Danger Modal with 2FA requirement (Course Code + "XÁC NHẬN XÓA") and Admin Audit Reason input | Real browser interaction, 2FA validation, DOM audit | PENDING |
| WF19 | Broken DELETE route (405 Method Not Allowed) on courses | Symmetrical REST DELETE endpoint on /courses/<id> and /courses/<id>/trash for Instructor and Admin | API test, Network 200, Course trashed | PENDING |
| WF20 | Admin course list showing drafts and desynchronized instructor names | Rename section to "Quản lý khóa học", filter out all DRAFT courses, sync instructor name with owner_instructor_name | Admin table DOM check, 0 drafts shown, correct names | PENDING |
| WF21 | F5 reload required for state synchronization (autosave, review, notif) | Unified Server-Sent Events (SSE /api/events/stream) + Frontend Reactive EventBus; autosave unlocks review/diff in 0ms without F5; Admin receives instant review push without F5 | SSE stream, 0ms in-session unlock, cross-role push proof | PENDING |
| WF22 | Floating AI launcher overlapping chat drawer header | Auto-hide launcher on chat open; restore launcher at exact previous coordinates on chat close [X] | Visual inspection, DOM display check, coordinate persistence | PENDING |
| WF23 | Asymmetric/silent multi-device login revocation | Single Active Device Takeover: Second login succeeds immediately (200 OK); active previous device (last_seen <= 5m) receives SSE auth:concurrent_session_revoked with polite informational modal; idle sessions (> 5m) silently revoked in DB; persistent session cookie (7d/30d) by default | Real browser 2-device takeover test, SSE event received, polite modal proof | PENDING |
| WF24 | Generic robot AI icon, truncated 1024-token responses, crude send button | Official Octopus AI avatar (`octopus_ai_icon.png`), 4096 maxOutputTokens, all-parts text concatenation, pedagogical structure, modern inset pill send button | Visual chat inspection, long response verification, 0 truncation | PENDING |
| WF25 | Desynchronized avatar between Settings and Topbar with divergent storage | Single source of truth DB avatar (`PUT /auth/profile`), unified retrieval logic across Topbar and Settings, instant 0-F5 sync | Settings-Topbar comparison, random avatar save, visual proof | PENDING |
| WF26 | Trashed/deleted courses appearing in student enrolled/dashboard/exam views | 100% concealment of TRASH/deleted courses across all student endpoints (`/student/courses`, `/student/my-learning`, `/student/dashboard`, `/student/assessments`) | API and Student UI DOM inspection, 0 deleted courses shown | PENDING |
| WF27 | Appeal submission 500 error (`AttributeError: score/total_score`) and missing evidence upload | Safe extraction via `attempt.result.raw_score` + optional evidence file upload (PNG/JPG/WEBP/PDF <= 10MB) stored via `FileAsset`, viewable by Instructor | Appeal submit 201 Created, evidence upload, instructor review link | PENDING |
| WF28 | Fullscreen overlay lock and viewport disparity logout (`outerWidth - innerWidth > 160`) on exam zoom | Completely removed fullscreen overlay & viewport difference check; unrestricted browser zoom in/out without lock or session termination | Browser zoom test 125%/150%/200%, zero lock overlay, zero logout | PENDING |
| WF29 | Obsolete generic AI greeting and verbose refusal templates | Canonical identity: "Bạch Tuột, trợ lí AI của hệ thống PPTQ" + 3 standardized responses (greeting, off-scope refusal, insult apology) | Chat expand check, off-topic query check, insult apology check | VERIFIED |
| WF30 | Fragmented notification broadcast modals, duplicate toast popups, un-scoped local avatar leak (`pwd301_avatar`), YouTube-only trailer without upload, lack of hard delete & 15-day cleanup, missing completion certificate | Dedicated Admin Notification Center (`#/admin/notifications`) with 2-block horizontal layout (Broadcast form & history table with system-wide hard delete); 15-day auto-cleanup; 1500ms toast debounce/dedup; machine video trailer upload (.mp4/.webm < 1GB) with public 16:9 stream; isolated avatar storage by user ID; Landscape A4 Course Completion Certificate PDF + UI completion review mode & outline download button | Real-browser Playwright 40-round STLC audit with screenshots, API tests, PDF generation verification | VERIFIED |
| WF31 | Legacy free/direct enrollment ('Giới thiệu' & 'Ghi danh' buttons), topbar 'Cài đặt tài khoản' shortcut, course creation without price, absence of student balance & PayOS payment gateway, lack of financial sub-admin role | Replaced by: (1) PayOS VietQR payment gateway with auto-balance update & 12-char description (PPTQ + UserCode + TxCode); (2) Course Card with eye-catching Price Tag + single 'Mua ngay' button (opens course intro if not enrolled); (3) Two purchase options: Wallet balance OR direct PayOS QR; (4) Hover Preload DOM for instant zero-latency page transitions; (5) Removed Topbar 'Cài đặt tài khoản' shortcut across all roles; (6) ADMIN_FINANCIAL sub-role with cashflow dashboard, audit logs, deposit verification, and balance revoke with automatic enrollment cancellation; (7) Primary Admin topbar quick access to cashflow management | Real-browser Playwright 40-100 round STLC audit with step screenshots, unit/integration test suites | PENDING |
| WF32 | Obsolete student dashboard course recommendations (Algorithm 14 on home page), miniature unscannable payment QR (192px without zoom), and missing Admin course price modification with Audit Log & Instructor notification in 'Quản lý khóa học' | Replaced permanently by: (1) 100% removal of 'Gợi ý khóa học tiếp theo' from student home dashboard (keeping course catalog discovery intact); (2) High-contrast, large-format 288px-320px VietQR payment display (`w-72 sm:w-80`) with hover badge and interactive Lightbox modal zoom (`UI.showQrLightbox`); (3) Admin course price modification modal (`UI.showCoursePriceEditModal`) in 'Quản lý khóa học' with price presets, live formatting preview, mandatory audit reason, append-only `AuditEvent` (`COURSE_PRICE_UPDATED`), and automated notification (`SYSTEM_ADMIN_INTERVENTION`) dispatched to the course owner instructor | Real-browser Playwright 40-round STLC audit with screenshot evidence, unit/integration pricing tests, DOM inspection | VERIFIED |
| KEEP | Attempt snapshots, locked published exam timing/structure, auth, scanning, enrollment, audit, existing unrelated limits | Retain; no history purge or weakened security | Existing regression suite | PENDING |

All affected source branches are removed/replaced under a failing regression test
before being marked VERIFIED. Compatibility endpoints must call the replacement
gate and cannot revive fragmented writes. Applied migrations and historical audit
data are retained; they are not normative descriptions for future work.

## Retrieval and memory corrections

Active docs, old plans and local retrieval indexes must point here rather than
retain actionable contrary instructions. Historical evidence stays in Git.
Codex memory corrections are submitted via
`C:/Users/LENOVO/.codex/memories/extensions/ad_hoc/notes/` only. The obsolete claims
in MEMORY.md's PWD301 course-authoring group (per-lesson queue_lesson_review and
lesson-state approval boundary) are superseded by WF01-WF03; unrelated neighboring
rules remain valid. A correction note is not proof of ingestion. Report its actual
state and keep this repository contract authoritative if retrieval returns old text.

Memory correction: note submitted at `extensions/ad_hoc/notes/2026-10-15-091500-pwd301-workflow-supersession.md`. On 2026-10-16, the current MEMORY.md registry was read and its affected entries explicitly mark the old per-lesson workflow historical and state the replacement aggregate/freeze rules. This verifies those registry corrections, not deletion of all historical rollout content or future retrieval behavior. Runtime and final behavior verification remain in progress.
