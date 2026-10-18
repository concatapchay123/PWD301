# PWD301 REQUIREMENT TRACEABILITY MATRIX (RTM)

**Specification Authority:** `docs/system/PWD301_SYSTEM_SPECIFICATION/` & `AGENTS.md` (Operational Guardrails)

| Requirement / Invariant ID | Canonical Specification Reference | Iterations Exercised | Test Cases | Audit Status |
|---|---|---|---|---|
| **REQ-HEADLESS-01** | Rule 10.1: Pure Headless Backend & REST API | Iterations 01, 04, 07, 16, 20 | TC-IT07-001, TC-IT16-002, TC-IT20-003 | **VERIFIED COMPLIANT** |
| **REQ-AUTH-02** | Rule 10.8: Global Anti-Tamper & Blackout Shield | Iterations 02, 13, 19 | TC-IT02-004, TC-IT13-001, TC-IT19-003 | **VERIFIED COMPLIANT** |
| **REQ-FILE-03** | Rule 10.3: 50MB Non-Archive Attachment Policy | Iterations 09, 17, 19 | TC-IT09-001, TC-IT17-001, TC-IT19-004 | **VERIFIED COMPLIANT** |
| **REQ-VIDEO-04** | Rule 10.8: YouTube Standard 16:9 & HLS DRM | Iteration 09 | TC-IT09-002, TC-IT09-003, TC-IT09-004 | **VERIFIED COMPLIANT** |
| **REQ-EXAM-05** | Rule 10.3 / Alg 07: Single Active Editing Lease | Iterations 11, 12, 18, 19 | TC-IT11-001, TC-IT11-002, TC-IT19-005 | **VERIFIED COMPLIANT** |
| **REQ-EXAM-06** | Rule 10 Anti-Leak Exam Invariant | Iterations 12, 18 | TC-IT12-004, TC-IT18-006 | **VERIFIED COMPLIANT** |
| **REQ-PACING-07** | Rule 10.8 / Alg 04: Video Pacing & Wall-Clock Clamping | Iterations 09, 18 | TC-IT09-005, TC-IT18-002 | **VERIFIED COMPLIANT** |
| **REQ-ENROLL-08** | Rule 10.10: Strict Lifetime Enrollment Guarantee | Iteration 18 | TC-IT18-001 | **VERIFIED COMPLIANT** |
| **REQ-RBAC-09** | Two-Tier Broadcast Notification Governance | Iterations 03, 17, 19 | TC-IT03-004, TC-IT17-004, TC-IT19-006 | **VERIFIED COMPLIANT** |
| **REQ-TELEMETRY-10**| Rule 10.5: Authentic System Telemetry (`psutil`) | Iterations 01, 16, 20 | TC-IT01-001, TC-IT16-004, TC-IT20-001 | **VERIFIED COMPLIANT** |
| **REQ-TRASH-11** | Soft-delete & Cascade Detachment | Iterations 10, 17, 19 | TC-IT10-001, TC-IT17-001, TC-IT19-001 | **DEFECT-IT10-001 LOGGED** |
| **REQ-PERF-12** | Core API Response Latency Budget ($\le 500\text{ms}$) | Iterations 16, 19 | TC-IT16-001, TC-IT19-002 | **DEFECT-IT16-001 LOGGED** |
