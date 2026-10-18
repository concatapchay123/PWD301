# Iteration 11: Defect Report

## Summary of Defects Discovered in Iteration 11
- **Total Defects Discovered:** 0
- **Critical (P0):** 0
- **High (P1):** 0
- **Medium (P2):** 0
- **Low (P3):** 0

---

## Concurrency & Invariant Observations
1. **Algorithm 07 (Single Active Editing Lease):** Robust enforcement of SHA-256 token hashing, lease epochs, heartbeat renewals, and takeover fencing. Stale window answer persistence was strictly rejected with HTTP 409 Conflict without split-brain corruption.
2. **Submission Idempotency:** Simultaneous duplicate submission requests carrying identical idempotency keys resolved concurrently with HTTP 200 and exactly 1 `AssessmentResult` in Microsoft SQL Server.
3. **Optimistic Concurrency Guards:** Course review and changeset fingerprinting reliably blocked stale approvals with HTTP 409 Conflict.
4. **Row Lock Capacity Control:** SQL Server `WITH (UPDLOCK, HOLDLOCK)` successfully serialized concurrent enrollments and prevented over-enrollment on full courses.
