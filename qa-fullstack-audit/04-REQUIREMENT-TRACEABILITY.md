# 04-REQUIREMENT TRACEABILITY MATRIX (RTM)

## Mapping System Requirements & Invariants to Verification Evidence

| Req ID | System Requirement / Invariant | Source Specification | Testing Iteration | Verification Evidence | Status |
|---|---|---|---|---|---|
| **REQ-01** | Pure Headless Backend & REST JSON Envelopes | AGENTS.md § 10.1 | Iteration 01, 07 | IT01_health_status.json, IT07_api_contract.json | **PASS** |
| **REQ-02** | Brand Cleanliness (0 Logo Images, PPTQ LMS text) | TASK-BRAND-CLEANUP | Iteration 01, 19 | IT01_Home_Guest.png (0 img logo verified) | **PASS** |
| **REQ-03** | Dual Auth: Session Cookies (Web) & JWT Bearer (API) | SPEC-AUTH-01 | Iteration 02 | IT02_Login_Form.png, IT02_auth_session.json | **PASS** |
| **REQ-04** | Role-Based Access Control (Student / Instructor / Admin) | SPEC-RBAC-01 | Iteration 03 | IT03_Admin_Dashboard.png, IT03_rbac_matrix.json | **PASS** |
| **REQ-05** | Single Active Editing Lease (Algorithm 07) | AGENTS.md § 10.3 | Iteration 11 | IT11_lease_concurrency.json (409 Conflict verified) | **PASS** |
| **REQ-06** | Assessment Anti-Leak Security & Scrubbed Answers | AGENTS.md § 4 | Iteration 12 | IT12_anti_leak_evidence.json | **PASS** |
| **REQ-07** | Strict 50MB Attachment Limit & Archive Rejection | AGENTS.md § 10.3 | Iteration 09 | IT09_file_security.json | **PASS** |
| **REQ-08** | YouTube Standard 16:9 Uncropped Viewport | AGENTS.md § 10.8 | Iteration 09 | IT09_YouTube_16x9_Student.png | **PASS** |
| **REQ-09** | Global Anti-Tamper Shield & Session Revocation | AGENTS.md § 10.8 | Iteration 13 | IT13_AntiTamper_BlackoutShield.png | **PASS** |
| **REQ-10** | 3-Tier Resilient YouTube Duration Fallback | AGENTS.md § 10.8 | Iteration 14 | IT14_network_resilience.json (1800s default) | **PASS** |
| **REQ-11** | Strict Lifetime Enrollment (Unenrollment Locked) | AGENTS.md § 10.10 | Iteration 18 | IT18_lifetime_enrollment.json (HTTP 403) | **PASS** |
| **REQ-12** | Cascade Attachment Deletion & Document Hub Sync | AGENTS.md § 4 | Iteration 17 | IT17_integration_evidence.json | **PASS** |
| **REQ-13** | Course Staging Drafts & Changeset Review | AGENTS.md § 4 | Iteration 08 | IT08_staging_drafts.json | **PASS** |
| **REQ-14** | Performance Latency Budget (< 500ms) | SPEC-PERF-01 | Iteration 16 | IT16_performance_profile.json (DEFECT-IT16-001) | **DEFECT** |
| **REQ-15** | Course Soft-Delete & Trash Lifecycle | SPEC-COURSE-01 | Iteration 10 | IT10_defect_replication.json (DEFECT-IT10-001) | **DEFECT** |
