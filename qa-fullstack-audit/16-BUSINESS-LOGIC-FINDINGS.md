# 16-BUSINESS LOGIC & WORKFLOW AUDIT FINDINGS

## 1. Course Publishing & Staging Draft Invariants
- **Atomic Admin Approval:** Verified that instructor edits are aggregated into a single `COURSE_VERSION_CHANGESET` draft. Admin approval publishes all modifications atomically.
- **Non-Bypassable Review:** Verified that instructors cannot directly transition a published course into public circulation without admin review.

---

## 2. Assessment Lifecycle & Grading Invariants
- **Locked Timing:** Server-authoritative assessment timers cannot be manipulated via client clocks.
- **Locked Question Structure:** Once the first student begins an attempt, the assessment structure and assigned points lock permanently.
- **Idempotent Submission:** Calling `POST /student/attempts/<id>/submit` multiple times returns identical results without double-counting scores.

---

## 3. Strict Lifetime Enrollment Invariant
- **Permanent Access:** Students enrolled in a course retain lifetime access. Calling `POST /student/courses/<id>/leave` is permanently blocked with HTTP 403 Forbidden.
