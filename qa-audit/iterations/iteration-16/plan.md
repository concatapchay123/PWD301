# Iteration 16 Test Plan: Performance Symptoms, Payload Efficiency, Layout Stability & Memory Leak Indicators

**Iteration:** 16  
**Domain:** Performance Symptoms, Payload Efficiency, LCP/CLS Layout Stability, Memory Leak Indicators  
**Auditor Lead:** AGENT 07 — Performance & Reliability QA (Assisted by AGENT 02 UI/UX QA & AGENT 03 Backend QA)  
**Browser Engine:** Real Google Chrome 155 via Playwright (`channel="chrome"`)  
**Backend:** Local Docker container `pwd301_web` (Flask REST API + SQL Server) on `http://localhost:5000`  
**Execution Objective:** Empirically measure core API response times, payload sizes, browser Core Web Vitals (LCP, CLS), server-side authentic telemetry (`psutil` Rule 10.5), SPA DOM/memory retention across route traversals, and database query latency.

---

## 1. Scope & Performance Invariants

1. **API Response Time Baseline:**
   - Core read endpoints (`/auth/me`, `/student/courses`, `/student/profile`, `/instructor/courses`, `/admin/health`, `/student/enrollments`) must respond within $\le 500\text{ms}$ under local conditions.
2. **Payload Efficiency:**
   - JSON envelopes must be concise and targeted, avoiding massive unpaginated megabyte payloads. All standard responses must be $\le 500\text{KB}$.
3. **Core Web Vitals & Layout Stability:**
   - Cumulative Layout Shift (CLS) $\le 0.1$ (Good threshold).
   - Largest Contentful Paint (LCP) $\le 2.5\text{s}$ (Good threshold).
4. **Authentic System Telemetry (Invariant 10.5):**
   - Telemetry from `/admin/health` must reflect genuine system metrics collected via `psutil` (CPU percent, memory percent, process uptime), never hardcoded or simulated values.
5. **SPA Memory & DOM Cleanup:**
   - Repeated route navigation across student views must unmount obsolete components and clean up DOM nodes without progressive leaks or unbounded DOM explosion.
6. **Database Connection Pool Overhead:**
   - Multi-join relational queries must execute cleanly without connection pooling stalls or timeout exceptions.

---

## 2. Test Execution Schedule (6 Test Cases)

- **TC-IT16-001:** Core API Response Time Baseline across Critical Endpoints ($\le 500\text{ms}$)
- **TC-IT16-002:** Payload Efficiency & JSON Envelope Size Audit ($\le 500\text{KB}$)
- **TC-IT16-003:** Core Web Vitals: Cumulative Layout Shift (CLS) & Largest Contentful Paint (LCP)
- **TC-IT16-004:** Server Resource Utilization & Authentic Telemetry Verification (psutil Rule 10.5)
- **TC-IT16-005:** Single Page App Memory Leak Indications under Repeated Route Traversal
- **TC-IT16-006:** Database Multi-Join Relational Query Overhead & Connection Pool Latency
