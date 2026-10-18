# Iteration 16: Test Case Specifications

**Domain:** Performance Symptoms, Payload Efficiency, LCP/CLS Layout Stability, Memory Leak Indicators  
**Auditor Lead:** AGENT 07 — Performance & Reliability QA  

---

### TC-IT16-001: Core API Response Time Baseline across Critical Endpoints (<= 500ms)
- **Target Invariant:** Performance Reliability & HTTP Baseline Latency.
- **Preconditions:** Authenticated sessions for Student, Instructor, and Admin.
- **Endpoints Tested:**
  - `GET /auth/me`
  - `GET /student/courses`
  - `GET /student/profile`
  - `GET /instructor/courses`
  - `GET /student/enrollments`
  - `GET /admin/health`
- **Test Steps:**
  1. Dispatch 3 warm-up requests and 5 timed requests per endpoint.
  2. Record HTTP status code, minimum latency, maximum latency, and average latency.
  3. Verify all endpoints respond with HTTP 200 and average latency $\le 500\text{ms}$.
- **Pass Criteria:** 100% HTTP 200 OK, average latency $< 500\text{ms}$ across all endpoints.

---

### TC-IT16-002: Payload Efficiency & JSON Envelope Size Audit (<= 500KB)
- **Target Invariant:** Headless API Payload Optimization & Network Footprint.
- **Preconditions:** Backend serving course catalogs, profiles, and health data.
- **Test Steps:**
  1. Capture raw byte size of response body across endpoints (`/student/courses`, `/instructor/courses`, `/admin/health`, `/auth/me`).
  2. Inspect JSON response schema to ensure pagination or lean serialization without unnecessary deep nested models.
  3. Verify each response payload $\le 500\text{KB}$.
- **Pass Criteria:** All audited JSON envelopes are $< 500\text{KB}$ with compact serialization.

---

### TC-IT16-003: Core Web Vitals: Cumulative Layout Shift (CLS) & Largest Contentful Paint (LCP)
- **Target Invariant:** Frontend Visual Stability & Modern Web Standards (CWV).
- **Preconditions:** Real Google Chrome 155 with Playwright, authenticated as student.
- **Test Steps:**
  1. Inject PerformanceObserver to collect `layout-shift` entries and `largest-contentful-paint` entries.
  2. Navigate to `#/student/dashboard` and wait for data rendering.
  3. Navigate to `#/student/courses` and wait for course cards to render.
  4. Aggregate cumulative layout shift score and LCP render time.
- **Pass Criteria:** Cumulative Layout Shift (CLS) $\le 0.1$, Largest Contentful Paint (LCP) $\le 2.5\text{s}$.

---

### TC-IT16-004: Server Resource Utilization & Authentic Telemetry Verification (psutil Rule 10.5)
- **Target Invariant:** Authentic Telemetry Invariant (Rule 10.5).
- **Preconditions:** Admin session authenticated with Primary Admin credentials.
- **Test Steps:**
  1. Call `GET /admin/health` with valid Admin session cookie.
  2. Extract telemetry fields (`cpu_percent`, `memory_percent`, `process_stats`, `disk` if present).
  3. Assert numeric types and verify values reflect authentic runtime state rather than static mock literals (e.g. dynamic memory allocation $> 0$ and $< 100$).
  4. Query secondary sample 1 second later to verify reading variations.
- **Pass Criteria:** Telemetry sourced authentically from OS (`psutil`), dynamic variations confirmed, 0 synthetic mock constants.

---

### TC-IT16-005: Single Page App Memory Leak Indications under Repeated Route Traversal
- **Target Invariant:** Client-Side SPA Resource Management & Router Cleanliness.
- **Preconditions:** Real Google Chrome running student session.
- **Test Steps:**
  1. Measure initial DOM node count (`document.getElementsByTagName('*').length`) and JS heap size if supported.
  2. Perform 15 sequential route transitions between `#/student/dashboard`, `#/student/courses`, and `#/student/profile`.
  3. Measure post-traversal DOM node count and JS heap.
  4. Calculate net growth delta.
- **Pass Criteria:** DOM node count stabilizes to baseline ($\pm 20\%$ variance) on returning to the same route, confirming proper unmounting and zero unbounded element accumulation.

---

### TC-IT16-006: Database Multi-Join Relational Query Overhead & Connection Pool Latency
- **Target Invariant:** Database Connection Pool Stability & Complex Query Response.
- **Preconditions:** Course with learning units and lessons, active enrollments.
- **Test Steps:**
  1. Perform repeated multi-join data requests (e.g. course learning outline and user attempts).
  2. Measure execution time across 5 consecutive queries.
  3. Assert that connection pooling remains healthy with zero timeout errors and average query execution latency $< 300\text{ms}$.
- **Pass Criteria:** 100% queries complete successfully without pool exhaustion; average latency $< 300\text{ms}$.
