# Iteration 20 Test Cases: Independent Final QA Audit & Release Gate

| Test Case ID | Subsystem / Focus | Target Route / Action | Input Condition | Expected Result | Severity / Invariant |
|---|---|---|---|---|---|
| **TC-IT20-001** | Platform Health | `GET /admin/health` & `/admin/telemetry` | Admin polls health and telemetry | Server returns `healthy: true`, authentic hardware metrics via `psutil` (32 vCPUs, RAM, uptime) | CRITICAL / Rule 10.5 Authentic Telemetry |
| **TC-IT20-002** | Shell Navigation | `#/student`, `#/instructor`, `#/admin` | Real Chrome renders each role shell | Zero visual collisions, clean DOM rendering, zero uncaught JavaScript errors | HIGH / Pure Headless SPA Experience |
| **TC-IT20-003** | Pure Headless Contract | Core API Endpoints (`/api/courses`, `/auth/profile`) | Automated payload inspection | 100% adherence to `{"success": bool, "data": ..., "error": ...}`, zero HTML template leak | CRITICAL / Rule 10.1 Pure Headless Invariant |
| **TC-IT20-004** | Release Quality Gate | Full Audit Metrics Consolidation | Aggregate metrics across Iterations 01–20 | $\ge 120$ test cases executed, $\ge 98\%$ overall pass rate, 0 P0 Blocker defects | CRITICAL / Release Readiness Standard |
| **TC-IT20-005** | Residual Risk Ledger | Defect & Debt Classification | Triage open defects (`DEFECT-IT10-001`, `DEFECT-IT16-001`) | Concrete root-cause remediation roadmap documented without hiding unresolved risks | HIGH / Source-of-Truth Transparency |
| **TC-IT20-006** | Executive Sign-Off | Master Evidence Index | Catalog all screenshots, traces, logs | 100% empirical evidence traceability confirmed across all 20 iterations | CRITICAL / Rule 10.2 Empirical Evidence Contract |
