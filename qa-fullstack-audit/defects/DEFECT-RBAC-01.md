# DEFECT-RBAC-01: Client-Side SPA Route Guard Missing for Admin Routes (Exposes Shell to Students)

- **Defect ID:** DEFECT-RBAC-01
- **Component:** SPA Client Router (`frontend/assets/js/router.js`)
- **Severity:** Medium (P2)
- **OWASP Classification:** API5:2023 - Broken Function Level Authorization / UI Security Inconsistency
- **Status:** VERIFIED / RESOLVED

---

## 1. Description
In the frontend Single-Page Application (SPA) router ([frontend/assets/js/router.js](file:///e:/PWD301/frontend/assets/js/router.js)), route resolution for admin views (`#/admin/*`, e.g. `#/admin/governance`, `#/admin/courses`) executes the Admin view renderer without validating whether the currently authenticated user's role permits admin access before mounting the layout.

When a logged-in student or instructor enters `#/admin/governance` directly in the browser URL bar:
1. The client-side router matches the route and executes `AdminView.render()`.
2. The Admin navigation shell, topbar, and governance table container are immediately mounted to the DOM.
3. Subsequent background REST API calls to `/admin/governance/summary` fail with HTTP 403 Forbidden as properly enforced by the backend `@admin_required` decorator.
4. An error toast "Bạn không có quyền truy cập" is displayed, but the empty admin shell layout remains visible on screen rather than instantly redirecting the unauthorized user to their role-appropriate dashboard (`#/student/dashboard`).

---

## 2. Security and User Experience Impact
- **Information Leakage via UI Structure:**
  Exposes administrative menu items, governance tabs, metrics containers, and administrative navigation architecture to non-admin actors.
- **Inconsistent Client State:**
  Leaves the SPA in an orphaned state with an admin shell layout active while the current user session is a Student or Instructor.
- **Violation of Zero-Trust UI Principles:**
  Frontend route dispatching should proactively guard role-restricted views (`beforeRouteEnter` guard), redirecting unauthorized users before DOM mounting.

---

## 3. Code Evidence
In [frontend/assets/js/router.js](file:///e:/PWD301/frontend/assets/js/router.js):
```javascript
dispatchRoute(route, params) {
    if (route.startsWith('/admin')) {
        // Missing proactive client-side role check:
        // if (this.currentRole !== 'ADMIN') {
        //     this.navigate(this.getDefaultRouteForRole(this.currentRole));
        //     return;
        // }
        AdminView.render(route, params);
    }
}
```

---

## 4. Verification and Reproduction Steps
1. Authenticate as a standard student: `mai.nguyen@example.com` / `StudentPass123!`.
2. Observe successful redirection to `#/student/dashboard`.
3. In the browser address bar, manually change hash to `#/admin/governance`.
4. Observe DOM layout renders `#admin-main-container` and admin navigation sidebar before the API 403 error toast appears.
5. Screenshot evidence captured: `qa-fullstack-audit/screenshots-annotated/ITER-03_TC-RBAC-001_STEP-01_VERTICAL_BLOCKED.png`.

---

## 5. Remediation Recommendation
Implement a centralized client-side navigation guard in [frontend/assets/js/router.js](file:///e:/PWD301/frontend/assets/js/router.js):
```javascript
beforeEach(to, from, next) {
    const requiredRole = this.getRequiredRole(to);
    if (requiredRole && this.currentUser?.role !== requiredRole) {
        UI.showToast("Bạn không có quyền truy cập trang này.", "error");
        return next(this.getDefaultRouteForRole(this.currentUser?.role || 'GUEST'));
    }
    next();
}
```
Ensure that if a non-admin attempts to access any `#/admin/*` route, they are immediately redirected to `#/student/dashboard` or `#/instructor/courses` with no partial admin shell DOM mounting.


---

## 6. Remediation Verification (PASSED)
- **Implemented Fix:** In [frontend/assets/js/router.js](file:///e:/PWD301/frontend/assets/js/router.js#L860-L895), `navigate` and `dispatchRoute` enforce defense-in-depth route guards checking `currentUser.role === 'ADMIN'`. Non-admin navigation attempts are redirected immediately to `#/student/dashboard` or `#/instructor/dashboard` with warning toast `ui.toast('Bạn không có quyền truy cập trang quản trị', 'warning')`.
- **Verification Evidence:** Executed in Iteration 03 on real Google Chrome browser (`run_fullstack_20_iterations_master.py`). Student navigated to `#/admin/governance`; client route guard trapped the navigation, redirected back to `#/student/dashboard`, and prevented mounting of admin DOM. Result: **PASSED**.
