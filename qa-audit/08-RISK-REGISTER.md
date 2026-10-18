# PWD301 RISK REGISTER

| Risk ID | Risk Description | Severity | Likelihood | Impact Area | Mitigation & Testing Strategy | Status |
|---|---|---|---|---|---|---|
| **RSK-01** | DevTools detection failure under certain browser zoom or headless modes | High | Low | Security & DRM | Verify outerWidth delta, debugger timing delta, and keyboard trap coverage | ACTIVE |
| **RSK-02** | Staging Draft divergence: Admin approving changeset while Instructor performs concurrent edits | High | Medium | Course Lifecycle | Verify optimistic locking, revision locking, and all-or-nothing atomic approvals | ACTIVE |
| **RSK-03** | Lease hijacking during high-stakes exam attempts | Critical | Low | Assessment Engine | Verify Single Active Editing Lease takeover rules (Algorithm 07) & token validation | ACTIVE |
| **RSK-04** | File quarantine bypass for malicious or oversized attachments | High | Low | File Security | Verify ClamAV fail-closed scanning & strict 50MB non-archive file ceiling | ACTIVE |
| **RSK-05** | YouTube pacing engine bypass via external scripting or frame modification | Medium | Medium | Learning Pacing | Verify anti-seek frontier enforcement up to (Duration - 5s) and server progress sync | ACTIVE |
| **RSK-06** | Cross-tenant or cross-role unauthorized access (IDOR) on private course assets | High | Low | Authorization | Verify resource-level ownership validation on all `/api/courses` and `/instructor` endpoints | ACTIVE |
| **RSK-07** | Sub-Admin privilege escalation in Admin Governance | High | Low | Admin RBAC | Verify Primary Admin vs Sub-Admin (Course Review, Instructor Review, System Monitoring) tabs | ACTIVE |
