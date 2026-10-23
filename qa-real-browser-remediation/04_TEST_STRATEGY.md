# 04. TEST STRATEGY & 80-ITERATION EXECUTION LIFECYCLE

### Iteration Architecture (8 Blocks × 10 Iterations)
- **Block 1 (Iter 001–010)**: Discovery & Critical Journeys (Public portal, Auth, Student, Instructor, Admin, AI).
- **Block 2 (Iter 011–020)**: Forms, CRUD and Persistence (Curriculum, Lessons, Attachments, Assessments, Wallet).
- **Block 3 (Iter 021–030)**: Business Workflows (Staging changeset, Admin review, Video armor, Exams, Gradebook).
- **Block 4 (Iter 031–040)**: Frontend & UX Deep Investigation (Preload engine, Topbar, Modals, Contrast, CLS).
- **Block 5 (Iter 041–050)**: Backend, Integration & Data Integrity (JSON envelopes, ClamAV, HLS DRM, Telemetry).
- **Block 6 (Iter 051–060)**: Security & Permission Boundaries (RBAC, Sub-roles, Anti-tamper, Slot neutrality).
- **Block 7 (Iter 061–070)**: Reliability & Edge Cases (Double clicks, Multi-tab lease, Unicode, Lazy creation).
- **Block 8 (Iter 071–080)**: Full Regression & Official Exit Gate (Cross-module regression, Exit criteria evaluation).

### Strict Operating Invariants
1. Real Browser Interaction Mandatory: All tests driven via Playwright Chromium.
2. Zero Direct CLI Endpoint Calls: No `curl`, `requests`, or API scripts used to bypass browser.
3. Anti-Fabrication Law: Every iteration generates authentic screenshots, console logs, and network logs.
