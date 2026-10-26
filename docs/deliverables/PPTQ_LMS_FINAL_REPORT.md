# ONLINE COURSE MANAGEMENT PLATFORM (PPTQ LMS)
## Final Report — PWD301 (Python Web Development)
**FPT University — Fall 2026 — Class IA2007 — Group 1**  
**Academic Supervisor:** Lê Tiến Dũng  
**Development Team:**
- SE203140 - Đặng Lý Quân
- SE201470 - Lại Vĩnh Phú
- SE204474 - Trần Đặng Hữu Thắng
- SE203815 - Phạm Nguyễn Hoàng Phúc

**Production Deployment:** https://pptq.id.vn/  
**Source Code Repository:** https://github.com/concatapchay123/PWD301

---

## ABSTRACT
With the rapid advancement of modern information technology, web-based learning and assessment platforms have become critical infrastructure for academic institutions and modern enterprises [1]. However, existing commercial and open-source learning management systems often present significant architectural shortcomings, including tightly coupled server-side templating engines, unverified client-side examination timers vulnerable to local tampering, and inadequate fail-open file handling mechanisms that expose systems to malware. To address these operational challenges, our engineering team designed and developed **PPTQ LMS**—a 100% custom-built, enterprise-grade Online Course Management and Assessment Platform engineered from the ground up for the PWD301 (Python Web Development) course at FPT University.

The PPTQ platform is architected around a high-performance **Modular Monolith with a Pure Headless REST API** powered by Python 3.11+ and Flask 3.x [2], decoupling server-side business logic from the user presentation layer. All domain data is managed through an enterprise-grade **Microsoft SQL Server 2022** database [3] structured around normalized relational entities enforcing ACID transactions, strict foreign key constraints, and optimistic concurrency controls. The client presentation layer utilizes a lightweight **Single-DOM Single-Page Application (SPA)** built in modern Vanilla JavaScript (ES2022+) and styled with Tailwind CSS alongside KaTeX mathematical typography, eliminating heavy frontend framework overhead while ensuring responsive client transitions.

Key architectural mechanisms implemented within PPTQ include:
1. **Server-Authoritative Online Examination Engine**: Enforces a Single Active Editing Lease algorithm (Algorithm 07) that strictly blocks secondary tab conflicts, coupled with client-side focus monitoring (blur and tab-switch telemetry).
2. **Anti-Forward Seek Video Pacing Engine**: Automated 5-second completion unlock and real-time lesson progression without page reload.
3. **Fail-Closed Antivirus Security Pipeline**: ClamAV daemon antivirus scanning coupled with a strict 50 MB Non-Archive Attachment Policy [7].
4. **Institutional AI Assistant ('Bạch Tuột')**: Powered by Google Gemini [6] with multi-key pool rotation, domain-grounded retrieval, and interactive question-level review explanations.

The platform is containerized via Docker Compose [4] and verified live on production at https://pptq.id.vn/.

*Keywords: Online Course Management System, Learning Management System, Flask, Python, Microsoft SQL Server, Docker Compose, Headless REST API, Server-Authoritative Assessment, AI Assistant, Single-DOM SPA.*

---

## I. INTRODUCTION

### 1.1. Background and Motivation
The digital transformation of global education has demonstrated that online learning systems are foundational environments for knowledge dissemination, competency assessment, and academic governance. Despite the proliferation of legacy platforms, institutional educators consistently face deep architectural and operational challenges. Traditional monoliths often tightly couple UI rendering templates with core business services, leading to maintainability bottlenecks, bloated page payloads, and severe security risks during concurrent exam sessions [1], [5].

Furthermore, academic integrity remains a vulnerable touchpoint in online education. Many existing solutions rely on client-side JavaScript timers for exam countdowns, which can be manipulated using browser developer tools, or permit unrestricted multi-tabbing that enables unmonitored collusion. Similarly, unverified file uploads represent a severe attack vector, where malicious archives or ransomware can be injected under the guise of study materials [5], [7].

Recognizing these critical systemic gaps, our team undertook the development of PPTQ: an Online Course Management and Assessment Platform. Developed as the final capstone for PWD301 – Python Web Development at FPT University, PPTQ was engineered 100% in-house from scratch. The project provides an empirical demonstration of how modern Python software engineering principles, rigorous database normalization, fail-closed security protocols, and human-centered interface design coalesce into a robust academic platform.

### 1.2. Project Objectives
#### 1.2.1. General Objective
The overarching objective of the project is to architect, develop, verify, and deploy a comprehensive, production-grade web application supporting online course management, curriculum organization, protected video learning, secure online examination, and AI-powered academic assistance across three distinct user roles: Students, Instructors, and System Administrators.

#### 1.2.2. Specific Objectives
- Engineer a modular, headless backend architecture using Python 3.11 and Flask 3.x, delivering standardized JSON REST API envelopes across all operational domains [2].
- Implement a high-performance Single-DOM Single-Page Application (SPA) delivering seamless navigation, instantaneous state updates, and WCAG AA accessibility compliance [8].
- Design and normalize an enterprise-grade database schema on Microsoft SQL Server 2022 comprising relational tables with strict foreign keys, BIGINT identities, public GUIDs, and UTC timestamps [3].
- Develop a server-authoritative online examination engine featuring the Single Active Editing Lease algorithm (Algorithm 07), real-time focus/tab-switch tracking, idempotent submissions, and automated grading.
- Implement an anti-forward seek video pacing engine with HLS streaming security and a 5-second completion unlock mechanism.
- Enforce a fail-closed file security architecture incorporating real-time ClamAV daemon antivirus scanning and a strict 50 MB Non-Archive Attachment Policy [7].
- Integrate 'Bạch Tuột'—an institutional AI Assistant powered by Google Gemini with multi-key pool rotation, retrieval-augmented grounding, and dedicated question-level review explanations [6].
- Execute comprehensive automated testing across unit, integration, and security test suites, orchestrating all services via multi-container Docker Compose [4].

### 1.3. Project Scope
The project scope encompasses the complete software development lifecycle, from domain modeling and API specification to containerized deployment. The functional boundaries are explicitly delineated across three core operational roles:
- **Student Domain**: Course discovery, permanent enrollment, structured learning view with protected video streaming, document downloads, interactive mini-quizzes, anti-cheat online examination, and academic gradebook transcript generation.
- **Instructor Domain**: Studio course creation, curriculum outline structuring (Chapters and Lessons), 50 MB document attachment uploads, exam authoring across standardized question formats (Single Choice, Multiple Choice, True/False), assessment scheduling, and unified staging changeset approvals.
- **Administrator Domain**: System-wide user account lifecycle governance (activation, suspension, and role assignment), course publication review and rejection workflows, fee governance with audit trail logging, and live hardware telemetry monitoring via `psutil`.

> **System Invariant**: PPTQ LMS is an independent, 100% custom-built platform engineered by Group 1. It contains zero legacy code from third-party commercial platforms and operates entirely on dedicated, containerized services.

### 1.4. Target Users
- **Students (Learners)**: Require an intuitive, distraction-free learning environment that tracks progress accurately, provides responsive video playback, protects their examination submissions against connectivity drops, and offers immediate academic support.
- **Instructors (Educators)**: Require a cohesive management studio to build rich modular curricula, author and manage examinations with customizable constraints (time limits, attempt limits, pass rates), and analyze student grading outcomes transparently.
- **System Administrators (Governance)**: Require granular role-based access control, real-time server health metrics, tamper-evident audit logs, and centralized course review workflows to guarantee institutional compliance.

### 1.5. Development Methodology
- **Phase 1 - Domain Modeling & Specification**: Defined canonical business rules, data dictionaries, state machines, and API contracts before authoring application code.
- **Phase 2 - Test-Driven Implementation (TDD Iron Law)**: Authored automated failing tests (unit, integration, and security boundaries) prior to implementing backend route handlers or services.
- **Phase 3 - Modular Monolith & Headless Separation**: Built discrete Flask blueprints with centralized error handling and request validation, strictly isolating business logic from presentation concerns.
- **Phase 4 - Verification Before Completion**: Executed automated test pipelines, real-browser Playwright suites, and security checks before marking features as complete.
- **Phase 5 - Multi-Container Orchestration**: Packaged the application, database, and security services into Docker Compose, validating production parity on https://pptq.id.vn/ [4].

---

## II. SYSTEM REQUIREMENTS ANALYSIS

### 2.1. Problem Overview
Modern educational environments require centralized platforms capable of managing complex educational hierarchies while maintaining strict data integrity. Key challenges that PPTQ was engineered to resolve include:
- **Data Fragmentation**: Consolidating disparate modules for identity, video streaming, document repository, and online examination assessments into a unified relational core.
- **Exam Integrity Vulnerabilities**: Eliminating client-side timer manipulation, concurrent multi-tab cheating, and unsaved progress loss during network interruptions.
- **Security & Malware Exposure**: Protecting institutional servers against malicious file uploads and zip-bomb attacks via automated fail-closed scanning [5], [7].
- **AI Reliability & Cost Control**: Preventing AI hallucination and service outages through retrieval grounding and multi-key API pool load balancing [6].

### 2.2. Functional Requirements
- **FR-01: User Authentication & Identity Lifecycle**: Secure registration, login via academic email, Werkzeug PBKDF2 password verification, Flask session cookie management with HttpOnly and SameSite=Lax flags, JWT issuance for external API consumers, and instantaneous session revocation upon suspension.
- **FR-02: Role-Based Access Control (RBAC)**: Strict server-side authorization enforcing object-level ownership checks across Student, Instructor, and Administrator roles.
- **FR-03: Course Lifecycle & Staging Drafts**: Unified staging draft aggregate allowing instructors to stage content modifications continuously and submit them atomically for administrative review.
- **FR-04: Hierarchical Curriculum Management**: Structuring learning content into multi-tiered Course -> LearningUnit (Chapter) -> Lesson hierarchies with drag-and-drop sequencing.
- **FR-05: Protected Video Learning & Pacing Engine**: Encrypted HLS video streaming with session-bound 12-hour DRM tokens, standard 16:9 responsive viewport, anti-forward seek restriction up to (Duration - 5s), 5-second completion unlock, and real-time next-lesson gate.
- **FR-06: Server-Authoritative Online Examination**: Fullscreen exam console, focus/tab-switch blur telemetry counter, Single Active Editing Lease algorithm (Algorithm 07), and server-managed UTC countdown timers.
- **FR-07: Grading, Regrading & Academic Transcripts**: Idempotent submission processing, automated question scoring, audit-trailed manual regrading, and official PDF gradebook generation with 'KHÔNG ĐẠT' / 'ĐẠT' evaluation labels.
- **FR-08: System Governance & Authentic Telemetry**: Real-time hardware telemetry (CPU, RAM, Disk) queried via `psutil`, course fee governance, and append-only audit event logging.
- **FR-09: Intelligent Octopus AI Assistant**: Domain-grounded question answering via Google Gemini, strict course-scope RAG retrieval, multi-key rotating pool, and interactive question-level review explanations [6].

### 2.3. Non-Functional Requirements
- **Security**: Defense-in-depth architecture adhering to OWASP Top 10 standards [5], strict CSRF token validation, input sanitization, and fail-closed ClamAV file scanning [7].
- **Data Integrity**: ACID transactions on Microsoft SQL Server 2022 [3], strict foreign keys, BIGINT internal keys, GUID public exposures, and rowversion concurrency tokens.
- **Usability**: Warm Editorial design system adhering to Jakob's, Hick's, and Miller's psychological laws, single-column forms, skeleton loading states, and WCAG AA contrast ratio (>= 4.5:1) [8].
- **Maintainability**: Modular Monolith architecture with clean blueprint separation, modular serialization schemas, and type-annotated domain logic.
- **Deployability**: Fully reproducible, multi-container Docker Compose deployment [4] guaranteeing zero configuration drift between development and production environments.
- **Performance & Reliability**: Sub-100ms API response latency for cached endpoints, automated container healthcheck probes, and high availability targets.

### 2.4. Role-Based Access Control Matrix
| Functional Capability | Student Role | Instructor Role | Administrator Role |
| :--- | :--- | :--- | :--- |
| User Registration & Profile Update | Self Only | Self Only | Full Management |
| Course Enrollment (Lifetime) | Self Enrolled | Assigned Courses | System-wide Override |
| Curriculum & Lesson Authoring | Read (Enrolled) | Create / Edit Owned | Review / Approve / Delete |
| Document Attachment Upload (<50MB) | Forbidden | Allowed (Owned) | Full Management |
| Video Pacing & Lesson Completion | Personal Tracker | Preview Mode | Audit / Inspection |
| Exam & Question Authoring | Forbidden | Create / Edit Owned | System-wide Oversight |
| Exam Creation & Scheduling | Forbidden | Create / Schedule Owned | Audit & Emergency Override |
| Exam Attempt & Submission | Allowed (Enrolled) | Preview Mode Only | Forbidden (Audit Only) |
| Score Regrading & Appeal | View & Request Appeal | Execute Regrade (Owned) | Final Arbitration |
| System Telemetry & Server Logs | Forbidden | Forbidden | Full Hardware Telemetry |

---

## III. SYSTEM DESIGN

### 3.1. Overall Architecture
PPTQ LMS is designed as a four-tier Modular Monolith combining monolithic deployment simplicity with strict headless API boundaries:
1. **Tier 1 - Presentation Layer**: Single-DOM SPA written in modern Vanilla JavaScript (ES2022+) styled with Tailwind CSS (via CDN), KaTeX math rendering, and Google Fonts. Communicates exclusively via asynchronous JSON fetch requests.
2. **Tier 2 - Security Gateway**: Host-level Caddy reverse proxy providing automatic HTTPS/TLS termination, rate-limiting, and security headers. Session state maintained via signed, HttpOnly cookies with CSRF tokens.
3. **Tier 3 - Application Core**: Flask Modular Monolith with blueprints [2] for Auth, Student Experience, Instructor Studio, Admin Governance, Assessment Engine, and AI Assistant.
4. **Tier 4 - Persistence & Containers**: Docker-managed multi-container architecture [4] comprising Microsoft SQL Server 2022 [3] (`db`), ClamAV daemon (`clamav`), background worker (`worker`), and Flask web API (`web`), with host hardware telemetry queried via `psutil`.

### 3.2. Database Design (Relational Architecture)
The database schema on Microsoft SQL Server 2022 [3] is organized into nine functional domains:
- **Identity & Access**: `users`, `roles`, `user_roles`, `auth_sessions`, `login_history`, `password_resets`, `permissions`, `role_permissions`.
- **Course & Curriculum**: `courses`, `learning_units`, `lessons`, `course_prerequisites`, `course_prices`, `categories`, `course_instructors`, `enrollments`, `lesson_resources`, `lesson_completions`, `video_trackers`, `course_versions`.
- **Assessment & Questions**: Question items, answer choices, revisions, matching pairs, and assessment section blueprints supporting single-choice, multiple-choice, and true/false evaluation.
- **Assessment Engine**: `assessments`, `assessment_sections`, `assessment_questions`, `assessment_policies`, `assessment_schedules`, `assessment_access_codes`, `grading_rules`, `regrade_policies`, `rubrics`, `rubric_criteria`.
- **Attempt & Regrading**: `assessment_attempts`, `attempt_answers`, `attempt_focus_events`, `assessment_results`, `assessment_result_history`, `regrade_items`, `score_histories`, `assessment_appeals`, `item_responses`, `attempt_questions`, `certificates`.
- **Files & Storage**: `file_assets`, `file_scans`, `quarantine_records`, `upload_sessions`, `storage_nodes`, `lesson_file_mappings`, `temp_uploads`.
- **AI RAG Knowledge**: `knowledge_chunks`, `chunk_embeddings`, `ai_chat_sessions`, `ai_messages`, `ai_feedback`, `grounding_references` [6].
- **Notification & Audit**: `audit_events`, `notifications`, `user_notifications`, `broadcast_announcements`, `audit_snapshots`, `system_alerts`, `email_outbox`, `webhook_subscriptions`.
- **Operations & Telemetry**: `database_backups`, `restore_history`, `system_health_metrics`, `telemetry_snapshots`, `background_jobs`, `maintenance_locks`.

### 3.3. User Interface Design
The user interface is governed by the Warm Editorial aesthetic system:
- **Jakob's Law**: Standardized topbar, sidebar, and breadcrumb navigation.
- **Hick's Law**: Clean single-column forms with explicit call-to-actions.
- **Miller's Law (7±2)**: Information chunking across course outlines and question navigation matrices.
- **Clean History Stack**: Dynamic routing using `history.replaceState` eliminates back-button navigation traps on form creation views.

---

## IV. TECHNOLOGIES AND DEPLOYMENT

### 4.1. Technology Stack Summary
- **Backend Language & Framework**: Python 3.11+, Flask 3.x [2], SQLAlchemy 2.0 ORM with `pyodbc` [3].
- **Database Engine**: Microsoft SQL Server 2022 (Docker Linux container `pwd301_db`, port 1433) [3].
- **Frontend Stack**: Vanilla JavaScript (ES2022+), Tailwind CSS CDN, KaTeX math typesetting, HTML5 APIs.
- **Security & Antivirus**: ClamAV Antivirus Daemon (port 3310) [7], Werkzeug PBKDF2 password hashing.
- **AI Engine**: Google Gemini API with multi-key rotation pool and RAG retrieval [6].
- **Containerization**: Docker & Docker Compose V2 [4] (4 services: `db`, `clamav`, `web`, `worker`).
- **Production Server**: Ubuntu 22.04 LTS host with Caddy reverse proxy at `https://pptq.id.vn/`.

---

## V. FEATURE IMPLEMENTATION

### 5.1. Authentication and Identity Governance
- **Session Authentication**: Secure, HttpOnly, SameSite=Lax cookies with CSRF defense for Web SPA.
- **JWT Authentication**: Short-lived Bearer tokens for external REST API endpoints.
- **Instant Revocation**: Account suspension or credential update immediately increments `auth_version`, invalidating active session cookies and cached tokens.

### 5.2. Course and Curriculum Management
- **50 MB Non-Archive Policy**: Strict rejection of `.zip`, `.rar`, `.7z` with standardized Vietnamese alert message.
- **Fail-Closed Antivirus**: Files pending scan or quarantined are blocked from student download [7].
- **Protected Video Streaming**: HLS streaming with 12-hour session DRM tokens, 16:9 responsive viewport, and anti-forward seek up to (Duration - 5s).
- **5-Second Seek Unlock**: Free scrubbing enabled in final 5 seconds; automatic lesson completion credit.
- **Real-Time Next Lesson Gate**: 'Tiếp theo' button dynamically lights up green (`bg-emerald-600`) upon completion without requiring page reload.

### 5.3. Server-Authoritative Online Examination Engine
- **Single Active Editing Lease (Algorithm 07)**: Only 1 active tab permitted per attempt via `lease_token_hash` and `lease_epoch`. Opening a second tab raises an `AttemptLeaseConflictError` (HTTP 409 Conflict); takeover is only allowed after expiry or explicit release.
- **Anti-Cheat Focus Tracking**: Fullscreen requested on start; window blur and fullscreen exit logged to `attempt_focus_events` table with telemetry timer.
- **Server UTC Countdown**: Eliminates local device clock manipulation vulnerabilities.
- **Idempotent Submission**: Retries and duplicate network requests never corrupt recorded exam scores.
- **Anti-Tamper Lockdown**: Opening DevTools / F12 triggers immediate session revocation and blackout security alert.
- **Official PDF Transcript**: Generates official PDF gradebook with bold red 'KHÔNG ĐẠT' for non-passing attempts.

### 5.4. Intelligent AI Assistant (Bạch Tuột)
- **Official Identity**: "Bạch Tuột, trợ lí AI của hệ thống PPTQ".
- **Interactive Assistant Touchpoints**:
  1. *Floating AI Tutor*: Greets students upon opening with 'Xin chào bạn! Mình là Bạch Tuột, trợ lí AI của hệ thống PPTQ. Mình có thể giúp được gì cho bạn?' providing contextual study guidance.
  2. *Instant Post-Exam Review ('Hỏi Bạch tuộc câu này')*: Embedded directly alongside assessment results (Figure D.9), enabling candidates to receive immediate, question-specific pedagogical explanations for why choices were correct or incorrect.
  3. *Dynamic Scope Guardrails*: Gracefully filters off-topic or adversarial prompts to keep interactions focused on academic coursework.
- **RAG Grounding**: Answers grounded strictly in active course syllabus; designed to avoid hallucination [6].
- **Defensive Prompt Filtering**: Sanitizes user queries to reject adversarial attempts to extract internal database records [5].

---

## VI. TESTING AND EVALUATION

### 6.1. Core Functional Test Execution Results
| Test ID | Test Scenario Description | Expected Result | Actual Result | Latency | Status | Notes & Observations |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-01** | User Login with Academic Email | Session cookie issued, redirect to role portal | Redirected, valid session cookie | 42ms | **Pass (100%)** | Werkzeug PBKDF2 verification verified |
| **TC-02** | Login with Invalid Password | HTTP 401, localized Vietnamese error envelope | HTTP 401 returned, error rendered | 28ms | **Pass (100%)** | Invalid attempt counter incremented (Brute-force defense) |
| **TC-03** | Student Accesses Admin Endpoint | HTTP 403 Forbidden, request blocked | HTTP 403 returned, audit logged | 15ms | **Pass (100%)** | RBAC guardrails functioning |
| **TC-04** | Course Outline & Catalog Navigation | Complete hierarchical curriculum returned | Hierarchy matches 3NF schema | 35ms | **Pass (100%)** | Hierarchy matches 3NF schema |
| **TC-05** | Online Exam Submission & Grading | Server scores answers, attempt locked | Idempotent submit, score recorded | 68ms | **Pass (100%)** | Lease successfully released |
| **TC-06** | PDF Gradebook Transcript Export | PDF downloaded, 'KHÔNG ĐẠT' rendered in red | PDF downloaded, valid watermark | 120ms | **Pass (100%)** | ReportLab generator active |
| **TC-07** | Octopus AI Knowledge Retrieval | Accurate lesson explanation, guardrails enforced | Accurate response, injection blocked | 850ms | **Pass (100%)** | Gemini pool active, Injection defense verified |
| **TC-08** | Docker Multi-Container Healthcheck | All core containers report Up (healthy) | All services healthy and running | N/A | **Pass (100%)** | Zero container crashes observed |

### 6.2. Test Coverage and Verification Summary
The test suite spans unit tests (`tests/unit/`), integration tests (`tests/integration/`), and end-to-end browser workflows (`tests/e2e/`), systematically validating business rules, database transactions, and security boundaries.

---

## VII. CONCLUSION AND FUTURE WORK
PPTQ LMS demonstrates that an in-house, Python/Flask-based architecture backed by Microsoft SQL Server 2022 and Docker Compose can deliver reliable performance, examination integrity, and modern educational UX. Operating live at https://pptq.id.vn/, the platform fulfills all technical requirements of the PWD301 curriculum at FPT University.

Future expansions will focus on automated multi-bitrate HLS video transcoding queues, WebRTC-based AI webcam proctoring, and cross-platform native mobile applications.

---

## REFERENCES
- [1] PWD301 Development Team, 'PPTQ LMS – Intelligent Enterprise Learning & Assessment Platform,' GitHub Repository, 2026. [Online]. Available: https://github.com/concatapchay123/PWD301.
- [2] Pallets Projects, 'Flask Documentation (Version 3.x),' Pallets, 2026. [Online]. Available: https://flask.palletsprojects.com/.
- [3] Microsoft Corporation, 'SQL Server 2022 Technical Documentation & Transact-SQL Reference,' Microsoft Learn, 2026. [Online]. Available: https://learn.microsoft.com/sql/sql-server/.
- [4] Docker Inc., 'Docker Compose Specification and Orchestration Guide,' Docker Docs, 2026. [Online]. Available: https://docs.docker.com/compose/.
- [5] OWASP Foundation, 'OWASP Top 10: The Ten Most Critical Web Application Security Risks,' OWASP Foundation, 2025. [Online]. Available: https://owasp.org/www-project-top-ten//.
- [6] Google DeepMind, 'Google Gemini API Developer Guide & Python SDK Documentation,' Google Cloud, 2026. [Online]. Available: https://ai.google.dev/.
- [7] ClamAV Open Source Community, 'ClamAV Antivirus Daemon Specification and Client Protocol,' ClamAV Documentation, 2026. [Online]. Available: https://www.clamav.net/.
- [8] W3C, 'Web Content Accessibility Guidelines (WCAG) 2.2,' World Wide Web Consortium, 2024. [Online]. Available: https://www.w3.org/TR/WCAG22/.

---

## APPENDICES

### Appendix A: Installation, Docker Orchestration, and Setup Guide

#### A.4. Service Status Verification
Verify container health using the `docker compose ps` command [4]. The operational status, healthcheck probes, and host port mappings across all four core containerized services are structured below:

| Service Name (Container) | Docker Image Source | Operational Health Status | Host Port Mappings |
| :--- | :--- | :--- | :--- |
| **pwd301_clamav** (`2f59f9a363d4`) | `clamav/clamav:latest` | **Up 9 hours (healthy)** | `0.0.0.0:3310 -> 3310/tcp` |
| **pwd301_db** (`f67cfa81fae7`) | `mcr.microsoft.com/mssql/server:2022-latest` | **Up 10 hours (healthy)** | `0.0.0.0:1433 -> 1433/tcp` |
| **pwd301_web** | `pwd301-web:latest` | **Up 45 minutes (healthy)** | `0.0.0.0:5000 -> 5000/tcp` |
| **pwd301_worker** | `pwd301-web:latest` | **Up 45 minutes (healthy)** | Internal Worker (No Host Port) |

*Table A.1: Docker Compose Multi-Container Operational Healthcheck Status and Service Topology.*

- **Appendix B**: Database Design, ERD Overview, and 9 Core Entity Data Dictionaries (`users`, `roles`, `courses`, `learning_units`, `lessons`, `questions`, `assessments`, `assessment_attempts`, `audit_events`).
- **Appendix C**: Test Cases, Concurrency Stress, and Invariant Verification Matrix.
- **Appendix D**: Illustrated User Manual with Photographic Production Evidence (Figures D.1 to D.9).
