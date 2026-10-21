# MASTER TEST PLAN (MTP) — PWD301 FULL-STACK QA CAMPAIGN

## 1. Test Objectives
1. Perform an exhaustive, empirical 20-iteration quality assurance campaign across Frontend SPA, Backend Flask REST APIs, Database Persistence (MSSQL), RBAC Boundaries, Realtime Communications (SSE), and Asynchronous Workflows.
2. Ensure 100% adherence to Non-Negotiable Architectural Invariants:
   - Pure Headless REST API (Standardized JSON Envelopes: `{"success": true/false, "data": ..., "error": ...}`).
   - Multi-Device Simultaneous Session Revocation (SSE `auth:concurrent_session_revoked` + 409 Conflict + Dual Blackout Modal).
   - Single Active Editing Lease Engine (Algorithm 07).
   - Strict 50MB Non-Archive Attachment Policy (Strict Vietnamese rejection for archives: *"Hệ thống không hỗ trợ tệp nén (.zip, .rar, .7z...). Vui lòng tải trực tiếp tài liệu học tập (PDF, Word, Excel, CAD, 3D...)"*).
   - Fail-Closed ClamAV virus scanning.
   - YouTube Standard 16:9 Viewport across all 4 touchpoints.
   - Pacing Engine & 5-Second Seek Unlock.
   - Realtime Next-Lesson Unlock Gate (No F5 reload).
   - Two-Tier Broadcast Notification RBAC.
   - Global Anti-Tamper Lockdown.
3. Capture empirical evidence for every single test case:
   - Original screenshot.
   - Annotated screenshot with exact defect coordinates or verification badges.
   - Full console logs (INFO, WARN, ERROR).
   - Full network traffic logs (URL, Method, Status, Duration, Payload).
   - Database row-level state verification in MSSQL.
   - Root-cause analysis and reproduction steps.

## 2. Test Execution Scope
### In-Scope Modules:
1. **Module 01: Authentication & Identity**:
   - Academic Email/Password authentication.
   - Multi-device concurrent login detection & simultaneous logout.
   - CSRF protection & session versioning (`auth_version`).
   - Profile update & 2-way avatar synchronization.
2. **Module 02: Course & Curriculum Management**:
   - Single-Page Studio curriculum editor.
   - Chapter (LearningUnit) and Lesson creation, reordering, and deletion.
   - Staging Draft Changeset generation and Admin atomic review/approval.
   - Cascade attachment deletion on unit/lesson removal.
3. **Module 03: Student Learning & Media Delivery**:
   - Course discovery catalog and enrollment.
   - Study console & chapter navigation outline.
   - YouTube 16:9 player and internal HLS fail-closed video delivery.
   - Anti-forward seek restriction up to (Duration - 5s).
   - Realtime completion unlock and next-lesson enablement without page reload.
4. **Module 04: Assessment & Exam Management**:
   - Question bank authoring (MCQ, essay, Bloom taxonomy matrix).
   - Fullscreen exam focus mode & Single Active Editing Lease takeover.
   - Anti-leak proctoring (clipboard clearing on PrintScreen, violation counters).
   - Server-authoritative timing, autosave debounce, and idempotent submission.
   - Official Gradebook PDF generation with "KHÔNG ĐẠT" (no legacy "HỎNG") and PPTQ watermark.
5. **Module 05: Administration & Governance**:
   - System monitoring & psutil authentic OS telemetry.
   - Two-tier broadcast notification RBAC.
   - Course moderation and staging changeset diff inspection.
6. **Module 06: Octopus AI Assistant**:
   - Official `octopus_ai_icon.png` avatar identity.
   - Modern Inset Pill chat layout & active Send button state.
   - Gemini Flash integration with 4096-token full generation (no cut-off).
   - Course-scoped RAG retrieval authorization.

## 3. Test Environment Specifications
- **Operating System:** Windows 11 Enterprise (Build 26100)
- **Web Server:** Gunicorn + Flask 3.x in Docker container `pwd301_web` (Port 5000)
- **Database Engine:** Microsoft SQL Server 2022 in Docker container `pwd301_db` (Port 1433)
- **Antivirus Engine:** ClamAV Daemon in Docker container `pwd301_clamav` (Port 3310)
- **Browser Automation:** Playwright Chromium 156.0.8078.4 (Headless / Headed)
- **Test Accounts:**
  - Student: `student1@pwd301.local` / `Password123!`
  - Student 2: `student2@pwd301.local` / `Password123!`
  - Instructor: `instructor1@pwd301.local` / `Password123!`
  - System Administrator: `admin@pwd301.local` / `Password123!`
