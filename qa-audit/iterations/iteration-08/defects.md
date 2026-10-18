# Defect Log — Iteration 08: Multi-Step Business Workflows: Course Lifecycle & Staging Drafts

## 1. Defect Summary Table

| Defect ID | Severity | Status | Subsystem | Description | Root Cause / Note |
| :--- | :--- | :--- | :--- | :--- | :--- |
| *None* | N/A | CLOSED | N/A | No functional or business invariant defects discovered in Iteration 08 | All 6 test cases passed 100% |

---

## 2. Architectural Observations & Invariant Adherence

1. **Pre-flight Readiness Fail-Closed Invariant:**
   - The pre-flight checklist strictly enforces all 5 canonical criteria before submission (`cover_image`, `intro_video`, `course_info` with SLOs, `academic_settings`, and `curriculum`).
   - Bare or incomplete courses cannot bypass validation into the Admin review queue.

2. **Unified Staging Draft Invariant:**
   - Once a course is `PUBLISHED`, curriculum mutations do not directly overwrite live data.
   - The backend automatically wraps changes into a `COURSE_VERSION_CHANGESET` (`status="DRAFT"` / `status="PENDING"`).
   - Students enrolled or browsing the catalog are 100% isolated from unapproved staging edits.

3. **Review Identity & Optimistic Concurrency Invariant:**
   - Admin approval routes require exact match of `review_version` (SHA-256 fingerprint of the proposal).
   - Any concurrent modification by the instructor while under review immediately raises `ConflictError` (HTTP 409), preventing stale approvals.
