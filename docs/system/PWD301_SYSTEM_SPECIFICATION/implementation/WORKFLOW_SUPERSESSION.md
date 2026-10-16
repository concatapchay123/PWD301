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
