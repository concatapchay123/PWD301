# MASTER TEST STRATEGY & RISK-BASED METHODOLOGY

## 1. Strategy Overview
The PWD301 Quality Assurance Campaign is conducted under an empirical, evidence-driven, multi-agent protocol adhering strictly to the Software Testing Life Cycle (STLC). Testing combines automated browser control (Chromium 156.0.8078.4), real-time feedback listening (UI, network, console, backend logs, database state), exploratory boundary analysis, and rigorous independent auditing.

## 2. Multi-Agent Orchestration Architecture
```
                                +-----------------------------------+
                                |    MASTER QA ORCHESTRATOR         |
                                |    (Campaign Strategy & Gates)    |
                                +-----------------------------------+
                                                  |
         +----------------------------------------+----------------------------------------+
         |                                        |                                        |
+------------------+                    +--------------------+                   +--------------------+
|   AGENT B        |                    |   AGENT C          |                   |   AGENT E          |
|   Frontend QA    |                    |   Backend & API QA |                   |   Security & RBAC  |
|   (Browser E2E)  |                    |   (Contracts & DB) |                   |   (Access Control) |
+------------------+                    +--------------------+                   +--------------------+
         |                                        |                                        |
         +----------------------------------------+----------------------------------------+
                                                  |
                                        +--------------------+
                                        |   AGENT H          |
                                        |   Independent      |
                                        |   Quality Auditor  |
                                        +--------------------+
```

## 3. The 18-Phase Execution Life Cycle per Iteration
Every iteration strictly performs all 18 phases:
1. **Phase 01 — Previous Iteration Review**: Assess open defects, regressions, coverage gaps.
2. **Phase 02 — Risk-Based Planning**: Select priority requirements and edge cases.
3. **Phase 03 — Requirement Analysis**: Map expected system behavior to confirmed specification.
4. **Phase 04 — Test Case Design**: Formulate executable test cases with preconditions and assertions.
5. **Phase 05 — Test Data Preparation**: Seed test fixtures, credentials, and courses.
6. **Phase 06 — Environment Verification**: Verify web container, MSSQL, and browser readiness.
7. **Phase 07 — Real Browser Interaction**: Execute real browser actions (navigation, forms, clicks).
8. **Phase 08 — Live Visual Observation**: Inspect layout, element visibility, toasts, modals, and responsive states.
9. **Phase 09 — Live Feedback Listening**: Listen to console logs, network requests/responses, and runtime exceptions.
10. **Phase 10 — Backend Verification**: Inspect server logs and route handler execution.
11. **Phase 11 — Database Verification**: Verify data persistence, foreign keys, row state in MSSQL.
12. **Phase 12 — Expected vs Actual Analysis**: Compare results and categorize (PASS / FAIL / BLOCKED).
13. **Phase 13 — Defect Triage**: Log and classify defects by severity and priority.
14. **Phase 14 — Reproduction & Root Cause Analysis**: Reproduce bugs and identify root causes.
15. **Phase 15 — Regression & Cross-Module Validation**: Run regression checks on related modules.
16. **Phase 16 — Evidence Packaging**: Store original screenshots, annotated screenshots, and logs.
17. **Phase 17 — Independent Audit**: Independent auditor verifies evidence and validates results.
18. **Phase 18 — Quality Gate & Next Iteration Decision**: Update coverage metrics and advance to next iteration.

## 4. The 20 Iterations Matrix
| Iteration | Domain & Focus | Target Test Cases |
| :---: | :--- | :--- |
| **01** | Smoke Testing & Core SPA Navigation | TC-SMOKE-001 to 005 |
| **02** | Authentication, Sessions & Multi-Device Logout | TC-AUTH-001 to 006 |
| **03** | RBAC, Ownership & Unauthorized Role Access | TC-RBAC-001 to 006 |
| **04** | Frontend UI Components, Modals & Drawers | TC-UI-001 to 006 |
| **05** | Form Validation, Negative Inputs & Sanitization | TC-FORM-001 to 006 |
| **06** | Course Curriculum CRUD & Data Persistence | TC-CRUD-001 to 006 |
| **07** | REST API Contracts & Standardized Envelope | TC-API-001 to 006 |
| **08** | End-to-End Student Learning & Next Lesson Gate | TC-E2E-001 to 006 |
| **09** | 50MB Attachment & Non-Archive Rejection Policy | TC-MEDIA-001 to 006 |
| **10** | Database Referential Integrity & Cascades | TC-DB-001 to 006 |
| **11** | Concurrency, Double Submit & Race Conditions | TC-CONC-001 to 006 |
| **12** | State Transitions & Staging Draft Changeset | TC-STATE-001 to 006 |
| **13** | Two-Tier Broadcast RBAC & Security Lockdown | TC-SEC-001 to 006 |
| **14** | Network Interruption & 3-Tier Fallback | TC-NET-001 to 006 |
| **15** | Responsive Viewports & Accessibility (WCAG AA) | TC-RESP-001 to 006 |
| **16** | Browser Runtime, Console Errors & Memory Health | TC-PERF-001 to 006 |
| **17** | Cross-Module Cascades (Document Hub & Gradebook) | TC-CASC-001 to 006 |
| **18** | Intensive Exploratory & Edge-Case Testing | TC-EXP-001 to 006 |
| **19** | Critical Regression Across Roles | TC-REGR-001 to 006 |
| **20** | Full-System Audit, Quality Gate & Release Verdict | TC-AUDIT-001 to 006 |

## 5. Exit Criteria & Quality Gates
1. All 20 STLC iterations executed with real browser actions and empirical verification.
2. 100% of discovered defects logged with reproduction steps, visual evidence, and root-cause analysis.
3. No fabricated evidence, false passes, or unverified claims.
4. Final Quality Verdict reflects true system health without sugar-coating.
