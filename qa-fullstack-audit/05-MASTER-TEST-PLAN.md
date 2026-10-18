# 05-MASTER TEST PLAN (20 STLC ITERATIONS)

## 1. Test Schedule & Iteration Breakdown

| Iteration | Title | Objective | Assigned Subagent | Status |
|---|---|---|---|---|
| **IT-01** | Smoke Testing & Baseline | Public health, brand cleanup, shell render | AGENT B (Frontend) | **COMPLETED** |
| **IT-02** | Authentication & Session | Session cookies, JWT, credentials, logout | AGENT C (Backend) | **COMPLETED** |
| **IT-03** | RBAC & Boundaries | Student, Instructor, Admin role access | AGENT C (Backend) | **COMPLETED** |
| **IT-04** | Navigation & Components | SPA routing, modals, tabs, toasts | AGENT B (Frontend) | **COMPLETED** |
| **IT-05** | Forms & Validation | Input sanitization, Vietnamese Unicode | AGENT B (Frontend) | **COMPLETED** |
| **IT-06** | CRUD & Persistence | Course/unit/lesson persistence, reload | AGENT D (Database) | **COMPLETED** |
| **IT-07** | API Contracts & Envelopes| JSON response envelope compliance | AGENT C (Backend) | **COMPLETED** |
| **IT-08** | Staging Drafts & Lifecycle | Changeset review, atomic publishing | AGENT C (Backend) | **COMPLETED** |
| **IT-09** | File Security & Video | ClamAV fail-closed, YouTube 16:9 | AGENT C & B | **COMPLETED** |
| **IT-10** | Database & Transactions | ACID checks, DEFECT-IT10-001 isolation | AGENT D (Database) | **COMPLETED** |
| **IT-11** | Concurrency & Leases | Algorithm 07 takeover & lease fencing | AGENT C (Backend) | **COMPLETED** |
| **IT-12** | Assessment & Anti-Leak | Exam security, scrubbed answer indices | AGENT C (Backend) | **COMPLETED** |
| **IT-13** | Anti-Tamper Security | F12 / DevTools traps, Blackout Shield | AGENT C (Security) | **COMPLETED** |
| **IT-14** | Resilience & Fallbacks | YouTube duration fallback, offline sync | AGENT C (Backend) | **COMPLETED** |
| **IT-15** | Responsive & WCAG AA | Mobile 375x667, Tablet 768x1024, Desktop | AGENT B (Frontend) | **COMPLETED** |
| **IT-16** | Performance Profiling | Latency budgets, DEFECT-IT16-001 | AGENT C (Backend) | **COMPLETED** |
| **IT-17** | Document Hub Sync | Cascade deletion of attachments | AGENT D (Database) | **COMPLETED** |
| **IT-18** | Lifetime Enrollment | Unenrollment permanently disabled (403) | AGENT C (Backend) | **COMPLETED** |
| **IT-19** | Full Regression Suite | Cross-module regression verification | AGENT A (Orchestrator)| **COMPLETED** |
| **IT-20** | Independent Audit | Final sign-off and Quality Gate verdict | AGENT H (Auditor) | **COMPLETED** |
