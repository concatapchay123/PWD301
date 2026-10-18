# Iteration 19 Test Cases: Comprehensive Platform Regression Suite

| Test Case ID | Subsystem / Focus | Target Route / Action | Input Condition | Expected Result | Severity / Invariant |
|---|---|---|---|---|---|
| **TC-IT19-001** | Defect Regression | `POST /instructor/courses/<id>/trash` | Instructor trashes active draft course | Re-verifies `DEFECT-IT10-001`: Response raises HTTP 403 during serialization post-soft-delete | HIGH (P1) / Defect Re-verification |
| **TC-IT19-002** | Performance Regression | `GET /instructor/courses` | 5 consecutive calls measuring latency baseline ($\le 500\text{ms}$) | Re-verifies `DEFECT-IT16-001`: Latency exceeds budget due to N+1 query overhead in `_serialize_course` | MEDIUM (P2) / Defect Re-verification |
| **TC-IT19-003** | Anti-Tamper Security | DevTools Keyboard Trap (`F12`) | Authenticated user triggers DevTools key | Overlay `#global-security-blackout-shield` renders, `POST /auth/logout` called, session revoked | CRITICAL / Rule 10.8 Anti-Tamper Lockdown |
| **TC-IT19-004** | File Security | `POST /instructor/.../resources` | Multipart upload of `archive.zip` attachment | Rejected with HTTP 400 and exact Vietnamese error message: `"Hệ thống không hỗ trợ tệp nén..."` | CRITICAL / Rule 10.3 50MB Non-Archive Policy |
| **TC-IT19-005** | Exam Concurrency | `POST .../answers/<aq_id>` | Stale Tab 1 writes answer after Tab 2 takeover | Rejected with HTTP 409 Conflict (`LEASE_CONFLICT`), stale write fenced from SQL Server | CRITICAL / Single Active Editing Lease (Alg 07) |
| **TC-IT19-006** | Broadcast RBAC | `POST /admin/broadcasts` | System Monitoring Admin attempts non-SYSTEM broadcast | Rejected with HTTP 403 Forbidden: `"Admin giám sát hệ thống chỉ được phép phát thông báo liên quan đến hệ thống."` | HIGH / Two-Tier Broadcast RBAC |
