# Iteration 14: Test Case Specifications

**Domain:** Browser Console Errors, Network Failure Recovery, Timeout Handling & Resilience  

---

### TC-IT14-001: Browser Console Error Audit on Student Portal Routes
- **Target Invariant:** Clean Console Mandate (Zero fatal JS exceptions).
- **Preconditions:** Real Google Chrome logged in as `student1@pwd301.local`.
- **Test Steps:**
  1. Attach listeners for `pageerror` and `console` (type `error`).
  2. Navigate through `#/student/dashboard`, `#/student/courses`, `#/student/assessments`, `#/student/profile`.
  3. Verify zero uncaught JavaScript exceptions or runtime crashes occurred.
- **Pass Criteria:** Zero `pageerror` events, zero uncaught syntax/type errors in student routes.

---

### TC-IT14-002: Browser Console Error Audit on Instructor Studio Routes
- **Target Invariant:** Clean Console Mandate (Zero fatal JS exceptions).
- **Preconditions:** Real Google Chrome logged in as `instructor1@pwd301.local`.
- **Test Steps:**
  1. Attach listeners for `pageerror` and `console` (type `error`).
  2. Navigate through `#/instructor/dashboard`, `#/instructor/courses`, `#/instructor/exams`.
  3. Verify zero uncaught JavaScript exceptions or runtime crashes occurred.
- **Pass Criteria:** Zero `pageerror` events across instructor routes.

---

### TC-IT14-003: Browser Console Error Audit on Admin Governance Routes
- **Target Invariant:** Clean Console Mandate (Zero fatal JS exceptions).
- **Preconditions:** Real Google Chrome logged in as `admin@pwd301.local`.
- **Test Steps:**
  1. Attach listeners for `pageerror` and `console` (type `error`).
  2. Navigate through `#/admin/governance`, `#/admin/courses`, `#/admin/users`.
  3. Verify zero uncaught JavaScript exceptions or runtime crashes occurred.
- **Pass Criteria:** Zero `pageerror` events across admin governance routes.

---

### TC-IT14-004: Network Failure Simulation & Client-Side Error Interception
- **Target Invariant:** Graceful Degradation & Network Failure Notification.
- **Preconditions:** Authenticated student on dashboard.
- **Test Steps:**
  1. Intercept network requests matching `/api/**` or `/student/**` to simulate network failure (abort `failed`).
  2. Attempt a user action (e.g., refresh course list via ApiClient).
  3. Assert client catches network error and returns/renders user-friendly Vietnamese failure message without crashing the SPA.
- **Pass Criteria:** Network drop caught gracefully, zero white-screen crashes, clear error message shown.

---

### TC-IT14-005: Delayed Response & High Latency Resilience (Skeleton / Loading State)
- **Target Invariant:** Loading States & Non-blocking UI.
- **Preconditions:** Authenticated student context.
- **Test Steps:**
  1. Intercept data endpoint and inject a 2500ms delay.
  2. Navigate to view and inspect DOM during transit.
  3. Assert skeleton loading placeholders or active loading spinners are present and UI is not frozen.
- **Pass Criteria:** Loading state rendered during high latency; UI resolves smoothly when data arrives.

---

### TC-IT14-006: Offline / Online Connectivity Transition & Auto-Recovery
- **Target Invariant:** Offline/Online Connectivity Handling.
- **Preconditions:** Authenticated student session.
- **Test Steps:**
  1. Dispatch `window.dispatchEvent(new Event('offline'))`.
  2. Verify offline banner or connection alert appears in UI.
  3. Dispatch `window.dispatchEvent(new Event('online'))`.
  4. Verify connection restored and banner dismisses or updates status.
- **Pass Criteria:** Offline and online transition events handled gracefully without requiring F5 reload.
