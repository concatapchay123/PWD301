# PWD301 LMS — Frontend Architecture, Component & SPA Audit Findings

**Audit Scope:** Single Page Application (SPA) Engine, Client Router, Component Layer, UI Architecture, Brand Identity Compliance, State Management & Security Shields  
**Target Codebase:** `frontend/index.html`, `frontend/assets/js/router.js`, `frontend/assets/js/ui.js`, `frontend/assets/js/api.js`, `frontend/assets/js/views/*.js`, `frontend/assets/js/components/*.js`  
**Evaluation Standard:** Production SPA Reliability, Warm Editorial Design System Fidelity, OWASP Client Security Standards, Enterprise Multi-Role UX Integrity  
**Audit Status:** COMPLETE — Exhaustive Documentation (Zero Placeholders)

---

## 1. Executive Summary & Architectural Overview

The frontend architecture of the PWD301 Learning Management System represents an enterprise-grade, zero-dependency, vanilla ES6 Single Page Application (SPA). Unlike bloated modern client stacks reliant on multi-megabyte React, Angular, or Vue virtual DOM runtimes, PWD301 leverages high-performance native browser primitives, a deterministic single-DOM mounting canvas (`#app-viewport`), and a micro-progress transition engine.

```mermaid
flowchart TD
    subgraph Browser Engine
        DOM[Window / Document]
        History[Hash History Listener]
    end

    subgraph App Core Shell
        Router[AppRouter Master Controller]
        SecShield[Global Security Shield & Anti-Tamper]
        Staging[Route Staging Viewport aria-hidden=true inert]
        TopBar[Warm Editorial Topbar & Multi-Role Switcher]
        MobileDrawer[Slide-over Responsive Drawer]
    end

    subgraph Views Layer
        Auth[AuthView - Lifecycle & Demo Presets]
        Student[StudentView - Catalog / 3-Col Reader / Exam Suite]
        Instructor[InstructorView - Studio / Multi-Format Exam Hub]
        Admin[AdminView - 4-Tab Governance / Operations Cockpit]
    end

    subgraph Support Infrastructure
        UI[UI Class - Modals / Toasts / Drawers / ExamParser]
        API[ApiClient - CSRF / Re-Auth / Error Normalization]
        VA[VideoArmor - Dynamic Canvas Forensic Watermark]
        AI[Floating AI Assistant - Draggable Octopus Widget]
    end

    History -->|hashchange| Router
    Router --> SecShield
    Router -->|renderRoute| Staging
    Staging -->|replaceChildren| DOM
    Router --> TopBar
    Router --> MobileDrawer
    Router --> Auth
    Router --> Student
    Router --> Instructor
    Router --> Admin
    Views Layer --> UI
    Views Layer --> API
    Views Layer --> VA
    Views Layer --> AI
```

### Core Architecture Metrics
- **SPA Routing Model:** Hash-based deterministic routing (`#/student/...`, `#/instructor/...`, `#/admin/...`, `#/auth`) with query-string decomposition via `URLSearchParams`.
- **DOM Reconciliation:** Double-buffered staging viewport (`createRouteStagingViewport` -> `commitRouteStagingViewport`) using native `replaceChildren()` to completely eliminate layout thrashing and white flash (FOUC).
- **Styling Framework:** Tailwind CSS CDN engine augmented by custom Warm Editorial Design System tokens (`#FAF9F5` light canvas, `#191919` dark canvas, Notion-like warm charcoal slate palette).
- **Third-Party CDN Integrations:** DOMPurify 3.1.6 (Safe HTML sanitizer), HLS.js 1.5.8 (Encrypted video streaming playback), KaTeX 0.16.11 (Visual mathematical formula rendering).
- **Brand Identity Compliance:** 100% Textual branding compliance (`PPTQ LMS`); exactly 0 brand logo images exist across the entire client application.

---

## 2. Application Shell & State Management

### 2.1 Single-DOM Viewport Mounting Architecture
All view rendering is encapsulated within `<main id="app-viewport" class="spa-viewport flex-1 overflow-y-auto relative bg-[#FAF9F5] dark:bg-[#191919]">`.
- **Elimination of Visual Jitter:** Before rendering complex DOM trees, `AppRouter.createRouteStagingViewport()` instantiates an off-screen staging container with `aria-hidden="true"` and `inert=true`.
- **Atomic Route Commit:** Once view asynchronous data fetches resolve, `AppRouter.commitRouteStagingViewport()` performs an atomic swap via `this.viewport.replaceChildren(...renderedContent)`, ensuring screen readers and users never perceive unstyled or intermediate partial DOM states.
- **Micro-Progress Bar:** During asynchronous data fetching across views, `UI.startMicroLoading()` and `UI.stopMicroLoading()` manipulate `#top-micro-loader-bar` at the very top of the viewport (2.5px height, ease-out transition), providing subtle Notion/GitHub-style visual feedback.

### 2.2 Navigation Shell & Multi-Role Perspective Switcher
The application shell header (`#app-topbar`, 56px height) dynamically adjusts depending on user authentication status, role, and active route:
1. **Brand Anchor:** Minimalist textual logo (`PPTQ LMS`) linked to `#/'`.
2. **Dynamic Center Navigation:** `#topbar-navigation-items` renders responsive pills based on the active role (`STUDENT`, `INSTRUCTOR`, `ADMIN`). For admin users, badge counts for pending course reviews and instructor applications update via periodic background polling (`fetchAdminPendingCounts()`).
3. **Multi-Role Dropdown:** `#topbar-avatar-btn` exposes a dropdown allowing multi-role faculty/administrators to instantly switch active perspectives without requiring re-authentication.
4. **Theme Switcher:** `#topbar-theme-toggle` alternates between Warm Editorial Light (`#FAF9F5`) and Dark Charcoal (`#191919`), synchronizing with `localStorage.getItem('theme')` and pre-paint head scripts.
5. **Notification Bell:** `#topbar-notifications-btn` with unread notification badge, live dropdown popover, and deep-link routing.

### 2.3 Mobile Navigation Drawer
For screen viewports below 768px (`< md`), the center desktop navigation is hidden (`hidden md:flex`), and a dedicated hamburger button (`#topbar-mobile-menu-btn`) activates:
- `#mobile-nav-backdrop`: Fixed semi-transparent backdrop (`bg-[#222120]/30 backdrop-blur-sm`).
- `#mobile-nav-drawer`: 288px width (`w-72`) slide-over panel displaying role-tailored links, online status indicator, and version badge.
- Keyboard accessible: Closes automatically on `Escape` keypress or navigation click.

### 2.4 Modal, Drawer & Toast Stack Engine
- **Modal Stack Manager (`UI._modalStack`):** Supports recursive and stacked modal dialogs. If a modal is spawned on top of an existing modal, the parent modal is temporarily hidden and pushed onto `_modalStack`. Closing the active layer seamlessly restores the preceding modal.
- **Clean Alert/Confirmation Dialogs:** `UI.confirm()` provides clean, macOS-inspired confirmation prompts with keyboard shortcuts (`Enter` to confirm, `Escape` to dismiss).
- **Floating Toast System:** `#toast-container` fixed at top-right (`z-[9999]`), rendering auto-dismissing cards with severity colors (info, success, warning, danger) and custom countdown progress bars.

---

## 3. SPA Routing & Route Guards

### 3.1 Hash Navigation & Route Mapping
The router parses the hash fragment using `parseHash()` to isolate route paths from query parameters:

| Route Path | View Controller | Access Guard | Primary Description |
|---|---|---|---|
| `#/auth` / `#/login` | `AuthView.render()` | Public | Authentication portal with demo auto-fill & caps-lock warning |
| `#/student/dashboard` | `StudentView.renderDashboard()` | `STUDENT` | Learning overview, active course cards, upcoming exams |
| `#/student/catalog` | `StudentView.renderCatalog()` | `STUDENT` | Course discovery catalog with debounced keyword search & level filters |
| `#/student/courses` | `StudentView.renderMyLearning()` | `STUDENT` | Enrolled courses matrix with progress meters |
| `#/student/courses/:id` | `StudentView.renderCourseConsole()` | `STUDENT` | Unified 3-column learning console (lessons, outline, resources) |
| `#/student/assessments` | `StudentView.renderAssessmentsList()` | `STUDENT` | Exam directory, status badges (Not Started, In Progress, Submitted) |
| `#/student/assessments/waiting-room` | `StudentView.renderWaitingRoom()` | `STUDENT` | UTC-synchronized exam waiting room countdown |
| `#/student/assessments/attempts/:id` | `StudentView.renderAttemptConsole()` | `STUDENT` | Fullscreen focus mode exam taking console with anti-cheat |
| `#/student/assessments/attempts/:id/results` | `StudentView.renderAttemptResults()` | `STUDENT` | Detailed scoring breakdown, question feedback & explanations |
| `#/student/ai-assistant` | `StudentView.renderAIAssistant()` | `STUDENT` | Dedicated full-page AI academic tutor chat interface |
| `#/student/become-instructor` | `StudentView.renderBecomeInstructor()` | `STUDENT` | Instructor application submission form with CV file upload |
| `#/instructor/dashboard` | `InstructorView.renderDashboard()` | `INSTRUCTOR` | Teaching analytics, active course status, enrollment counts |
| `#/instructor/courses` | `InstructorView.renderCourses()` | `INSTRUCTOR` | Course management workspace with creation wizard |
| `#/instructor/courses/:id/manage` | `InstructorView.renderCourseManage()` | `INSTRUCTOR` | Curriculum builder, unit organizer, lesson content editor |
| `#/instructor/exams` | `InstructorView.renderExamsHub()` | `INSTRUCTOR` | Soạn đề thi Studio, assessment configuration hub |
| `#/instructor/exams/:step` | `InstructorExams` Wizard | `INSTRUCTOR` | 4-step sequential exam generator (Editor, Interactive, Excel, Moodle, Matrix, Settings) |
| `#/instructor/prerequisite-requests` | `InstructorView.renderPrerequisiteApprovalRequests()` | `INSTRUCTOR` | Student prerequisite waiver request review queue |
| `#/admin/governance` | `AdminView.renderGovernance()` | `ADMIN` | 4-tab governance command center (Users, Courses, Faculty, Audit) |
| `#/admin/courses/review` | `AdminView.renderCourseReviewPage()` | `ADMIN` | Side-by-side curriculum diff inspector for course approval |
| `#/admin/operations` | `AdminView.renderOperations()` | `ADMIN` | Infrastructure cockpit: worker health, DB sandbox & backups |

### 3.2 Granular RBAC & Sub-Role Permissions
- **Automatic Multi-Role Perspective Switching:** If a faculty member or administrator navigates directly to a student route, `AppRouter` invokes `ApiClient.switchRole()` automatically to align backend session state with the UI context.
- **Admin Sub-Role Segmentation:** `AdminView` enforces sub-role restrictions:
  - `ADMIN_COURSE_REVIEW`: Restricted strictly to course queue and change request diffs.
  - `ADMIN_INSTRUCTOR_REVIEW`: Restricted to instructor applicant vetting.
  - `ADMIN_TEACHING_ASSIGNMENT`: Restricted to instructor workload and course assignment.
  - `ADMIN_SYSTEM_MONITORING`: Directed straight to `#admin/operations` and immutable audit logs.
  - `ADMIN_PRIMARY`: Full, unconstrained super-admin authority across all 4 governance tabs and operations cockpit.

### 3.3 Fullscreen Focus Mode
When navigating to exam attempt or waiting room routes (`#/student/assessments/attempts/...` or `.../waiting-room`):
- `AppRouter.applyRouteChrome()` adds the `.fullscreen-focus-mode` class to `document.body`.
- `#app-topbar` is completely hidden (`display: none !important;`).
- `#floating-ai-container` (Octopus AI launcher) is hidden and closed to prevent examination distractions or academic dishonesty.
- Screen real-estate is 100% dedicated to the assessment environment.

---

## 4. Client-Side Security & Anti-Tamper Architecture

### 4.1 Global Anti-Tamper Security Shield (`initGlobalSecurityShield`)
PWD301 implements a hardened browser security shield executed at application bootstrap:
1. **Shortcut Interception:** Captures and suppresses Developer Tools shortcuts (`F12`, `Ctrl+Shift+I`, `Ctrl+Shift+J`, `Ctrl+Shift+C`), Page Source inspection (`Ctrl+U`), and screen capture shortcuts (`PrintScreen`, `Win+Shift+S`).
2. **Context Menu Prevention:** Blocks right-click context menus across all non-input elements (`window.addEventListener('contextmenu', ...)`).
3. **Debugger Timing & Dimension Heuristics:**
   - Detects devtools breakpoints via `debugger` execution timing delta (`delta > 100ms`).
   - Detects docked DevTools panels by measuring window dimensional variance (`window.outerWidth - window.innerWidth > 160px`).
4. **Emergency Lockdown Protocol (`triggerGlobalSecurityLockdown`):**
   - Renders a fullscreen blackout shield (`#global-security-blackout-shield`, `z-[999999]`).
   - Immediately pauses all HTML5 `<video>` and `<audio>` elements.
   - Flushes the system clipboard via `navigator.clipboard.writeText('')`.
   - Dispatches a session revocation API request (`ApiClient.logout()`).
   - Clears `sessionStorage` and `localStorage` security tokens and redirects the user to login with security flags.

### 4.2 Dynamic Forensic Video Watermarking (`VideoArmor`)
- Embedded in video streaming lessons (`VideoArmor.installGlobalShield()`).
- Renders dynamic canvas overlay watermarks containing student name, user ID, client IP address, and cryptographic micro-timestamps.
- Continuously shifts coordinates across video viewports to defeat screen recording tools and illicit video redistributions.

### 4.3 CSRF Architecture & Error Normalization
- `ApiClient` automatically extracts CSRF tokens from cookies (`pwd301_csrf` or `csrf_token`), document `<meta name="csrf-token">`, or preflight calls to `/auth/login`.
- Automatically attaches `X-CSRFToken` to all mutative requests (`POST`, `PUT`, `PATCH`, `DELETE`).
- Error messages are normalized via `formatApiErrorMessage()`, with automatic fallback to Vietnamese error strings if backend returns generic English codes.

---

## 5. View Component Inspections

### 5.1 Authentication Suite (`AuthView`)
- Clean, centered card architecture on Warm Editorial canvas (`#FAF9F5`).
- **Caps-Lock Warning Indicator:** Dynamically detects `event.getModifierState('CapsLock')` and renders warning banners to prevent failed password attempts.
- **Quick-Fill Demo Account Presets:** In demo environments, provides 1-click credential buttons (`.seed-acc-btn`) for Student, Instructor, and Admin personas, facilitating rapid functional validation without manual password typing.

### 5.2 Student Learning Console (`StudentView`)
- **3-Column Resizable Lesson Reader:**
  - Column 1: Collapsible unit/lesson curriculum outline with completion checkmarks.
  - Column 2: Core content area with HLS video player, DOMPurify-sanitized lecture text, and KaTeX mathematical formula rendering.
  - Column 3: Interactive student workspace containing personal notes drawer and lesson Q&A discussions.
- **Interactive Exam Attempt Console:**
  - Supports 6 question interaction modalities: Single Choice, Multiple Choice, Drag-and-Drop Matching, Fill-in-the-Blank, Mathematical Formula Input, and Essay.
  - Live auto-save background synchronization with visual indicators (`Đã lưu`, `Đang lưu...`).
  - Question quick-navigator grid with color-coded status (Answered, Unanswered, Flagged for Review).

### 5.3 Soạn Đề Thi Studio (`InstructorExams`)
- **4-Step Guided Wizard:**
  - Step 1: Basic Information (Title, course assignment, duration, passing score, shuffle rules).
  - Step 2: Content Ingestion via 4 interchangeable modalities:
    - *WYSIWYG Markdown/Syntax Editor* (Supports PWD301 standard question syntax).
    - *Interactive Form Builder* (Structured visual builder with live preview).
    - *Excel Spreadsheet Bulk Import* (.xlsx parser with schema validation).
    - *Moodle XML Import* (Standards-compliant XML question bank parser).
  - Step 3: Exam Matrix Generator (Bloom's taxonomy distribution: Nhận biết, Thông hiểu, Vận dụng, Vận dụng cao).
  - Step 4: Security & Proctoring Settings (Anti-cheat strictness, IP restrictions, randomized question orders).

### 5.4 Admin Governance & Operations Cockpit (`AdminView`)
- **Governance Command Center (4 Tabs):**
  - Tab 1: User Management Matrix with role toggles, session termination buttons, and account suspension modals.
  - Tab 2: Course Review Queue with side-by-side visual diffs comparing pending draft modifications against approved live content.
  - Tab 3: Faculty Reassignment & Teaching Workload balancing matrix.
  - Tab 4: Immutable Audit Trail with cryptographic SHA-256 block chain verification validating system event integrity.
- **Operations & Security Cockpit:**
  - Service Health Matrix (Database, Redis, Worker daemons, ClamAV).
  - Database Backup Sandbox ("Never Overwrite Live Database" guarded restore workflows).
  - Maintenance Window Engine with live user notification broadcasts.

---

## 6. Brand Compliance & Visual Identity Audit

### 6.1 Audit Criteria & Findings
The design specification requires strict brand compliance: exactly **0 logo images** and exclusively **PPTQ LMS** textual branding.

| Check Item | Inspection Target | Code Reference | Compliance Status | Details |
|---|---|---|---|---|
| **Logo Images** | Header / Navbar | `frontend/index.html` lines 492–496 | **PASS (100%)** | Zero `<img>` or `<svg>` logo files. Header uses pure CSS text. |
| **Mobile Drawer Brand** | Navigation Drawer | `frontend/index.html` line 597 | **PASS (100%)** | Pure textual `<span>PPTQ LMS</span>` lockup. |
| **Brand Text String** | Typography & Hierarchy | `Plus Jakarta Sans`, font-bold, tracking-tight | **PASS (100%)** | Consistent across desktop and mobile shells. |
| **Octopus Asset Check** | AI Tutor Avatar | `frontend/assets/img/octopus_ai_icon.png?v=2` | **PASS (Compliant)** | Used strictly as feature avatar for AI Tutor; not a brand logo. |
| **Third-Party Templates** | Meta / Footers | `index.html` lines 6, 607 | **PASS (100%)** | Zero template placeholders, generic Bootstrap, or theme author credits. |

---

## 7. Frontend Findings & Actionable Remediation Matrix

| ID | Module / Component | Severity | Issue Description | Recommended Remediation |
|---|---|---|---|---|
| **FE-01** | `index.html` (Line 5) | **Medium** | `user-scalable=no, maximum-scale=1.0` prevents mobile users with visual impairments from zooming standard educational pages. | Dynamically enable zoom (`user-scalable=yes, maximum-scale=5.0`) on standard views; restrict zoom exclusively during `#/.../attempt` proctoring mode. |
| **FE-02** | `ui.js` (`UI.openModal`) | **Medium** | Modal dialogs lack keyboard tab-focus trapping; pressing `Tab` can navigate to background elements hidden beneath the modal backdrop. | Implement active focus trap in `openModal()` by intercepting `Tab` key to cycle within focusable elements of `.modal-dialog`. |
| **FE-03** | `ui.js` (`UI.closeModal`) | **Low** | Upon modal dismissal, focus is not programmatically returned to the button or trigger element that initiated the modal. | Store `document.activeElement` prior to modal launch and invoke `.focus()` on the originating trigger upon close. |
| **FE-04** | `router.js` (`applyRouteChrome`) | **Low** | Desktop topbar navigation items scroll horizontally on narrow tablets (768px-850px) without visual fade affordance. | Add subtle horizontal gradient mask (`mask-image: linear-gradient(...)`) to indicate horizontal scrollability when overflow occurs. |
| **FE-05** | `student.js` (Math Formulas) | **Low** | KaTeX rendered formulas do not all expose plain-text `aria-label` alternatives for assistive screen readers. | Configure KaTeX with `output: 'htmlAndMathml'` to ensure built-in screen reader accessibility. |

---
*Report compiled autonomously following deep static code inspection of all frontend assets.*
