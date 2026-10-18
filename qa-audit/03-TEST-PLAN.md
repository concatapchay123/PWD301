# PWD301 MASTER TEST PLAN & 20-ITERATION ROADMAP

**Document ID:** `QA-MTP-2026-10-18`  
**Standard:** ISO/IEC/IEEE 29119 Software Testing Standard  
**Lead QA Architect:** Principal QA Orchestrator  

---

## 1. 20-Iteration Scope Matrix

| Iteration | Title / Domain | Primary Invariant / Standard | Browser Engine | Status |
|---|---|---|---|---|
| **Iteration 01** | Smoke Testing & User Journeys | Root Reachability, Brand Logo, Critical Paths | Real Chrome 155 | **COMPLETED** |
| **Iteration 02** | Authentication & Session Lifecycle | Session Revocation, Remember-Me, Password Hash | Real Chrome 155 | **COMPLETED** |
| **Iteration 03** | Authorization & Sub-Admin RBAC | Primary vs Course Review vs Monitoring Admin | Real Chrome 155 | **COMPLETED** |
| **Iteration 04** | SPA Routing & Shell UI Components | Client Hash Routing, Shell Modals, No Console Errs | Real Chrome 155 | **COMPLETED** |
| **Iteration 05** | Form Validation & Unicode Support | Vietnamese Diacritics, Rapid Submissions | Real Chrome 155 | **COMPLETED** |
| **Iteration 06** | CRUD Data Persistence & Refresh | Read-After-Write Consistency, Draft Aggregation | Real Chrome 155 | **COMPLETED** |
| **Iteration 07** | Backend API Contracts & Envelopes | Pure Headless REST API, HTTP Status Localized Errs | Real Chrome 155 | **COMPLETED** |
| **Iteration 08** | Multi-Step Business Workflows | Staging Drafts, Changeset Atomic Diff Review | Real Chrome 155 | **COMPLETED** |
| **Iteration 09** | Files, Media DRM & Video 16:9 | 50MB Non-Archive Policy, 16:9 Viewport, HLS DRM | Real Chrome 155 | **COMPLETED** |
| **Iteration 10** | Database Transactions & Soft-Deletes | Atomic Commits, Referential Integrity, Soft-Deletes | Real Chrome 155 | **COMPLETED** |
| **Iteration 11** | Concurrency, Leasing & Idempotency | Algorithm 07 Single Active Editing Lease Fencing | Real Chrome 155 | **COMPLETED** |
| **Iteration 12** | Boundary Values & Corrupt States | Corrupt Tokens, Expired Leases, Prereq Cycles | Real Chrome 155 | **COMPLETED** |
| **Iteration 13** | Security Controls & Anti-Tamper | F12 Blackout Shield, Session Revoke, Anti-Capture | Real Chrome 155 | **COMPLETED** |
| **Iteration 14** | Network Resilience & Error Recovery | Offline/Online Transitions, API Timeout Handling | Real Chrome 155 | **COMPLETED** |
| **Iteration 15** | Responsive Viewports & WCAG AA | 320px to 1920px Viewports, Contrast Compliance | Real Chrome 155 | **COMPLETED** |
| **Iteration 16** | Performance & SPA Memory Leaks | Core Web Vitals (CLS/LCP), DOM Cleanup, psutil | Real Chrome 155 | **COMPLETED** |
| **Iteration 17** | Cascade Deletion & Notification RBAC | Trashing Lesson Purges FileAssets, Broadcast RBAC | Real Chrome 155 | **COMPLETED** |
| **Iteration 18** | Risk-Driven Exploratory & Adversarial | Strict Lifetime Enrollment, Anti-Seek Clamping, IDOR | Real Chrome 155 | **COMPLETED** |
| **Iteration 19** | Comprehensive Regression Suite | Re-verify DEFECT-IT10-001, DEFECT-IT16-001 | Real Chrome 155 | **COMPLETED** |
| **Iteration 20** | Independent Final QA Audit & Release | Release Gate Evaluation, Evidence Traceability | Real Chrome 155 | **COMPLETED** |
