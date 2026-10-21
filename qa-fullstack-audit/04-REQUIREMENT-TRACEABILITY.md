# REQUIREMENT TRACEABILITY MATRIX (RTM)

## 1. Traceability Mapping Protocol
Each business requirement from `PWD301_SYSTEM_SPECIFICATION` and `AGENTS.md` is strictly traced across Architecture, Routes, API Endpoints, Database Tables, Test Cases, Execution Evidence, and Defect Identifiers.

| Req ID | Requirement Description | Affected Routes | Backend API Endpoints | Target Tables | Target Test Cases |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **REQ-AUTH-01** | Unique Email Login & Session Management | `#/auth` | `POST /auth/login`, `POST /auth/logout`, `GET /auth/session` | `User`, `AuthSession` | TC-SMOKE-001, TC-AUTH-001 |
| **REQ-AUTH-02** | Simultaneous Multi-Device Logout (SSE + 409) | `#/auth`, all protected | `POST /auth/login`, `GET /api/realtime/stream` | `User`, `AuthSession` | TC-AUTH-002, TC-AUTH-003 |
| **REQ-AUTH-03** | Two-Way Avatar Synchronization | `#/student/settings` | `PUT /auth/profile`, `GET /auth/profile` | `User` | TC-AUTH-006, TC-CRUD-005 |
| **REQ-RBAC-01** | Student/Instructor/Admin Role Enforcement | `#/student/*`, `#/instructor/*`, `#/admin/*` | All role-scoped endpoints | `Role`, `UserRole` | TC-RBAC-001 to 006 |
| **REQ-RBAC-02** | Two-Tier Broadcast Notification RBAC | `#/admin/operations` | `POST /admin/notifications/broadcast` | `SystemNotification` | TC-SEC-001, TC-SEC-002 |
| **REQ-CRS-01** | Single-Page Studio & Curriculum CRUD | `#/instructor/courses/:id/manage` | `POST/PUT /api/courses`, `/api/lessons` | `Course`, `LearningUnit`, `Lesson` | TC-CRUD-001 to 004 |
| **REQ-CRS-02** | Unified Staging Draft Changeset Diff | `#/admin/change-requests/review` | `POST /instructor/courses/:id/staging/submit`, `/admin/staging/review` | `CourseVersionChangeset` | TC-STATE-001 to 004 |
| **REQ-CRS-03** | Cascade Attachment Deletion & Document Hub | `#/instructor/courses/:id/manage`, `#/student/courses/:id` | `DELETE /api/lessons/:id`, `/api/learning-units/:id` | `LessonResource`, `FileAsset` | TC-CASC-001, TC-CASC-002 |
| **REQ-MED-01** | Strict 50MB Non-Archive Attachment Policy | `#/instructor/courses/:id/manage` | `POST /api/files/upload`, `/api/courses/:id/resources` | `FileAsset`, `LessonResource` | TC-MEDIA-001 to 004 |
| **REQ-MED-02** | YouTube Standard 16:9 Player Viewport | `#/student/courses/:id/lessons/:id` | `GET /api/lessons/:id/playback` | `PlaybackSession` | TC-MEDIA-005, TC-RESP-003 |
| **REQ-MED-03** | Pacing Engine & 5-Second Seek Unlock | `#/student/courses/:id/lessons/:id` | `POST /api/lessons/:id/heartbeat` | `PlaybackHeartbeat`, `LessonProgress` | TC-E2E-002, TC-E2E-003 |
| **REQ-MED-04** | Realtime Next-Lesson Unlock Gate | `#/student/courses/:id/lessons/:id` | `POST /api/lessons/:id/complete` | `LessonProgress`, `CourseEnrollment` | TC-E2E-004, TC-UI-004 |
| **REQ-EXAM-01** | Single Active Editing Lease Engine | `#/student/assessments/attempts/:id` | `POST /api/assessments/attempts/:id/heartbeat`, `/takeover` | `AssessmentAttempt`, `AttemptLease` | TC-CONC-001 to 003 |
| **REQ-EXAM-02** | Anti-Leak Exam Proctoring & Lockdown | `#/student/assessments/attempts/:id` | `POST /api/assessments/attempts/:id/proctor` | `ProctoringEvent` | TC-SEC-004, TC-SEC-005 |
| **REQ-EXAM-03** | Bloom Taxonomy Matrix & Idempotent Submission | `#/instructor/exams/matrix`, `#/student/assessments/*` | `POST /api/assessments/attempts/:id/submit` | `Assessment`, `AssessmentSubmission` | TC-STATE-005, TC-API-005 |
| **REQ-SEC-01** | Global Anti-Tamper & Security Lockdown | Global client runtime | `POST /auth/logout` | `AuthSession` | TC-SEC-006, TC-EXP-004 |
| **REQ-AI-01** | Octopus AI Assistant Identity & 4096-Token Expansion | Global floating pill / Study tab | `POST /api/ai/chat` | `AiChatMessage`, `AiVectorIndex` | TC-UI-005, TC-API-006 |
| **REQ-OPS-01** | Authentic Telemetry (psutil OS Stats) | `#/admin/operations` | `GET /admin/health`, `GET /admin/telemetry` | `SystemMetric` | TC-SMOKE-005, TC-API-004 |
