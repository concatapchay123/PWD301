# 03. SYSTEM INVENTORY & COMPONENT CATALOG

### 1. Frontend SPA Modules
- `frontend/assets/js/router.js`: Hash router, DOM Hover Preload Engine, RBAC route guards.
- `frontend/assets/js/ui.js`: Editorial design components, modals, toasts, topbar, security shield.
- `frontend/assets/js/api.js`: Client API layer, CSRF token management, JSON envelope processing.
- `frontend/assets/js/realtime.js`: SSE listener, telemetry sync, realtime lesson unlock.
- `frontend/assets/js/exam-store.js`: Single active editing lease, monotonic autosave queue.
- `frontend/assets/js/components/video-armor.js`: 16:9 viewport, YouTube clean player, 5s seek unlock.
- `frontend/assets/js/views/auth.js`: Auth & account lifecycle, CapsLock detection.
- `frontend/assets/js/views/student.js`: Student dashboard, catalog, learning screen, wallet, gradebook.
- `frontend/assets/js/views/instructor.js`: Instructor studio, curriculum builder, document tree drawer.
- `frontend/assets/js/views/instructor-exams.js`: Assessment builder, question bank.
- `frontend/assets/js/views/admin.js`: Governance dashboard, course approvals, cashflow, audit logs.

### 2. Backend Domain Services & Blueprints
- `src/pwd301/blueprints/auth/`: Session login, logout, account management.
- `src/pwd301/blueprints/student/`: Student courses, enrollments, learning progress.
- `src/pwd301/blueprints/instructor/`: Instructor curriculum editing, staging draft management.
- `src/pwd301/blueprints/admin/`: Admin governance, approvals, user roles, cashflow ledger.
- `src/pwd301/blueprints/api_payments/`: PayOS integration, webhook handler, wallet topup.
- `src/pwd301/blueprints/api_assessments/`: Exam taking, single lease, autosave, grading.
- `src/pwd301/blueprints/api_ai/`: Octopus AI assistant, pedagogical RAG, prompt defenses.
