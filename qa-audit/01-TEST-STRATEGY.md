# PWD301 MASTER TEST STRATEGY & QUALITY ASSURANCE PROTOCOL

## 1. Executive Strategy Summary
This Master Test Strategy governs the comprehensive autonomous full-stack QA, defect discovery, real browser verification, and 20-iteration testing campaign for the PWD301 LMS platform.

**Core Principles:**
- **Zero-Guessing & Empirical Grounding:** No assertions without live execution evidence (screenshots, network traffic, console logs, database state).
- **Mandatory Real Browser Execution:** E2E user journeys and UI components are tested directly via real Chrome browser instances using Playwright and the Chrome DevTools protocol.
- **Fail-Closed Security & Integrity:** Rigorous verification of anti-tamper shields, role/sub-role isolation, CSRF validation, file security limits (50MB non-archive), and lease locking.
- **Iterative 20-Iteration Cycle:** Systematic progression from smoke testing to specialized concurrency, adversarial attacks, and regression closure.

---

## 2. Multi-Agent Organization & Role Matrix

| Agent ID | Specialized Role | Primary Focus & Deliverables | Execution Method |
|---|---|---|---|
| **AGENT 01** | **QA Orchestrator & Test Manager** | Campaign coordination, master plan, risk tracking, defect triage, final audit gate. | Test Harness & CLI Orchestration |
| **AGENT 02** | **Frontend & UI/UX QA** | SPA routes, forms, modals, visual hierarchy, mobile drawer, console errors, accessibility. | Real Chrome (Playwright) |
| **AGENT 03** | **Backend & API QA** | 432 REST API endpoints, JSON envelope consistency, HTTP codes, schema validation. | HTTP Integration Harness |
| **AGENT 04** | **Database & Data Integrity QA** | 77 MSSQL/SQLite tables, constraints, transactions, cascade soft-deletes, referential checks. | Direct ORM & DB Queries |
| **AGENT 05** | **Security & RBAC QA** | Auth boundaries, JWT/session revocation, IDOR/BOLA, DevTools blackout shield, CSRF. | Security Penetration Probes |
| **AGENT 06** | **End-to-End Business QA** | Course authoring lifecycle, Staging Drafts, single active editing lease, grading PDF. | Multi-Role Browser Journeys |
| **AGENT 07** | **Performance & Reliability QA**| Pacing engine, slow network, retry recovery, rapid double submissions, responsive views. | Network Throttling & Profiling |
| **AGENT 08** | **Independent Auditor & Regression**| Defect reproduction, evidence auditing, false-positive elimination, final sign-off. | Verification Reruns & Cross-Audits |

---

## 3. Testing Levels & Layers

### 3.1. Layer 1: Static Analysis & Repository Invariants
- Code linting, type-checking (`mypy`), syntax validation, and architectural rule compliance (`scripts/repo_check.py`).
- Pure Headless verification: zero legacy Jinja templates (`*.html` in `src/pwd301/templates/`), zero mock prototypes.

### 3.2. Layer 2: Real Browser E2E Testing (Playwright / Chromium)
- Real user interactions: Click, Type, Navigate, Scroll, Resize, Upload, Submit.
- Evidence collection: High-resolution annotated screenshots (`qa-audit/screenshots/`), browser console logs, and network interception.

### 3.3. Layer 3: Backend REST API Contract & Integration
- Standard JSON envelope: `{"success": true/false, "data": ..., "error": {"code": "...", "message": "..."}}`.
- Authorization enforcement: Role and resource ownership checks on every endpoint.

### 3.4. Layer 4: Database & State Consistency
- Read-after-write verification: State changes reflected in persistent storage and survive page refresh (F5).
- Atomic transitions: Course draft aggregation, exam lease takeover, cascade resource cleanup.

---

## 4. 20-Iteration Allocation Matrix

| Iteration | Primary Quality Focus | Key Target Modules |
|---|---|---|
| **01** | Smoke Testing, Environment Health & Critical Baseline | Live Server (Port 5000), Auth Check, Landing Page, Health Telemetry |
| **02** | Authentication & Session Lifecycle | Login, Logout, Remember-Me, Session Revocation, Password Policies |
| **03** | Authorization, RBAC & Sub-Admin Isolation | Student vs Instructor vs Primary Admin vs Sub-Admins (Governance) |
| **04** | SPA Routing, Dynamic Navigation & Shell Chrome | Topbar, Mobile Drawer, Focus Exam Mode, Dynamic Breadcrumbs |
| **05** | Form Validation, Unicode & Rapid Submission | Input boundaries, Vietnamese diacritics, duplicate POST handling |
| **06** | CRUD Workflows & Persistence | Course Creation, Lesson Editor, LocalStorage/Server Sync |
| **07** | Backend API Contracts & Schema Validation | JSON Envelopes, HTTP Statuses (200, 201, 202, 400, 401, 403, 404, 409) |
| **08** | Multi-Step Course Lifecycle & Staging Drafts | Draft -> Submission -> Admin Review -> Changeset Diff -> Publish |
| **09** | File Security, Attachments & Media Streaming | 50MB Non-Archive Policy, ClamAV fail-closed, YouTube 16:9, HLS DRM |
| **10** | Database Transactions & Referential Integrity | Cascade Trashing (Lesson -> Resource), Rollback on Error |
| **11** | Concurrency, Race Conditions & Lease Locking | Single Active Editing Lease (Algorithm 07), Concurrent Submissions |
| **12** | Boundary Values, Negative States & Corrupt Tokens | Expired Sessions, Prerequisite Cycles, Broken Payloads |
| **13** | Security Controls & Anti-Tamper Lockdown | DevTools Key Traps, View Source Traps, Blackout Shield, CSRF |
| **14** | Network Interruption & Timeout Resilience | Offline/Online recovery, retry policies, WebSocket/Polling fallbacks |
| **15** | Responsive Viewports & Accessibility | 320px to 1920px viewports, WCAG AA contrast, Theme Switching |
| **16** | Performance Indicators & Memory Analysis | Layout stability (CLS), Render timing (LCP), DOM leak checks |
| **17** | Cross-Module Integration & Cascading Effects | Document Tree Sync, Notification Broadcasts, Audit Logging |
| **18** | Risk-Driven Exploratory Testing & Clustering | Defect reproduction, edge cases, anomalous states |
| **19** | Full Regression Suite Verification | Retesting all identified defects, verifying non-regression |
| **20** | Independent Final Quality Audit & Gate Decision | Traceability sign-off, residual risk documentation, final verdict |
