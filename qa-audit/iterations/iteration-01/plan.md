# ITERATION 01 — PLAN & SCOPE DEFINITION

## 1. Objectives & Focus
Iteration 01 establishes the foundational smoke tests, environment health checks, and critical baseline user journeys on the live environment:
- Verify active system containers (Web Port 5000, Database Port 1433, ClamAV Port 3310).
- Launch real Chrome browser via Playwright.
- Verify Landing Page (`#/auth`) and PPTQ Brand Identity.
- Verify Student authentication journey and Dashboard rendering.
- Verify Course Catalog and search filtering interaction.
- Verify Admin authentication journey and System Governance overview.

## 2. In-Scope Modules
- Frontend Shell (`index.html`, `router.js`, `api.js`, `ui.js`)
- Authentication (`auth.js`, `/auth/login`, `/auth/logout`)
- Student Dashboard (`student.js`, `#/student/dashboard`)
- Course Catalog (`student.js`, `#/student/catalog`, `/api/courses`)
- Admin Governance (`admin.js`, `#/admin/governance`)
- Core Health Telemetry (`/admin/health`, `psutil`)

## 3. Out-of-Scope Modules
- Course editing and staging draft authoring (scheduled for Iteration 06 & 08).
- Exam assessment taking and single-lease locking (scheduled for Iteration 11).
- Deep security penetration and fuzzing (scheduled for Iteration 13).

## 4. Test Environment & Accounts
- Base URL: `http://localhost:5000`
- Browser: Google Chrome (Headless, 1366x768 viewport)
- Test Accounts:
  - Student: `student1@pwd301.local` / `Password123!`
  - Admin: `admin@pwd301.local` / `Password123!`
