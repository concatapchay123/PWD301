# ITERATION 04 TEST PLAN

**Iteration Focus:** Frontend SPA Navigation, Component Shell, Dynamic Role Menus, Focus Exam Mode & History Stack  
**Responsible Agents:** AGENT 02 (Frontend & UI/UX QA), AGENT 06 (E2E Business Workflow QA), AGENT 08 (Independent Auditor)  
**Target Environment:** Local Live Stack (`http://localhost:5000`)  
**Browser Engine:** Google Chrome 155 via Playwright  
**Viewport:** 1366x768 (Desktop) & 375x667 (Mobile Emulation)  

---

## 1. Objectives
1. Verify PPTQ brand identity logo, typography, and topbar user info rendering.
2. Verify role-based dynamic menu injection in desktop navigation (`#topbar-navigation-items`).
3. Verify mobile navigation drawer (`#mobile-nav-drawer`, `#topbar-mobile-menu-btn`, `#mobile-nav-close-btn`).
4. Verify Focus Exam Mode invariants:
   - Body class `fullscreen-focus-mode` applied on attempt routes.
   - Floating AI tutor (`#floating-ai-container`) hidden.
   - Obsolete header progress badge (`#console-course-progress-badge`) permanently absent.
5. Verify unknown route / 404 resilience and graceful fallback to role home.
6. Verify clean browser history navigation (Back/Forward navigation without redirect traps).

---

## 2. Test Cases Overview
- `TC-IT04-001`: Brand Identity & Topbar Chrome Render
- `TC-IT04-002`: Dynamic Role Navigation Items Render
- `TC-IT04-003`: Mobile Drawer Open/Close Interaction (375x667)
- `TC-IT04-004`: Focus Exam Mode Shell Guard & AI Tutor Concealment
- `TC-IT04-005`: Unknown Route Graceful Fallback (404 Handling)
- `TC-IT04-006`: Browser History Stack Navigation Integrity
