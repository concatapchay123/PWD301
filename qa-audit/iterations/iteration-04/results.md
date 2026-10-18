# ITERATION 04 — EXECUTION RESULTS

**Execution Date:** 2026-10-18  
**Iteration Focus:** Frontend SPA Navigation, Component Shell, Dynamic Role Menus, Focus Exam Mode & History Stack  
**Browser Engine:** Google Chrome 155.0.4283.60 (Playwright sync API)  
**Viewport:** 1366 x 768 (Desktop) & 375 x 667 (Mobile Emulation)  
**Live Target:** `http://localhost:5000`  

---

## 1. Test Execution Summary

| Test Case ID | Test Case Name | Status | Evidence Artifact | Empirical Notes |
|---|---|---|---|---|
| **TC-IT04-001** | Topbar Brand Identity & PPTQ Logo Render | **PASS** | `IT04_TC01_topbar_brand_identity.png` | PPTQ brand logo, title "PPTQ LMS", user name "Lê Hoàng Long", role badge "HỌC VIÊN", and initials "LH" rendered |
| **TC-IT04-002** | Dynamic Role Navigation Items Render | **PASS** | `IT04_TC02_dynamic_nav_items.png` | 6 role links rendered dynamically in `#topbar-navigation-items`: Trang chủ, Khám phá Khóa học, Khóa học của tôi, Bài kiểm tra, Đăng ký Giảng viên, Cài đặt |
| **TC-IT04-003** | Mobile Drawer Open/Close Interaction | **PASS** | `IT04_TC03_mobile_drawer_opened.png` | Mobile button visible at 375x667; drawer and backdrop opened with `aria-expanded="true"`; closed cleanly on close button |
| **TC-IT04-004** | Focus Exam Mode Shell Guard & Anti-Leak Header | **PASS** | `IT04_TC04_focus_exam_mode_guard.png` | `fullscreen-focus-mode` applied; floating AI tutor hidden; `#console-course-progress-badge` permanently absent |
| **TC-IT04-005** | Unknown Route Graceful Fallback (404) | **PASS** | `IT04_TC05_unknown_route_fallback.png` | Navigating to unmapped hash route gracefully redirected to `#student/dashboard` with zero crash or white screen |
| **TC-IT04-006** | Browser History Stack Integrity | **PASS** | `IT04_TC06_browser_history_stack.png` | Clean traversal using `window.history.back()` from courses -> catalog -> dashboard without redirection loops |

---

## 2. Invariant & Structural Verification

### 2.1. Focus Exam Mode Shell Invariant (AGENTS.md Section 4 & 10)
- **Active Route Pattern:** `#/student/assessments/attempts/<id>`
- **Shell Adaptations:**
  - `document.body.classList.contains('fullscreen-focus-mode')` -> `True`
  - Floating AI Tutor Container (`#floating-ai-container`) -> `hidden` class strictly applied
  - Obsolete Header Progress Badge (`#console-course-progress-badge`) -> Verified completely removed from DOM
- **Anti-Leak Assurance:** No correct/incorrect visual indicators or distraction overlays are rendered during active exam session.

### 2.2. Anti-Tamper DevTools Defense Observation
- The system includes active security guards in `router.js` and `video-armor.js` detecting viewport dimension discrepancies (`outerWidth - innerWidth > 160`) as docked DevTools.
- When verified in real mobile environments, the viewport and screen metrics align naturally, while simulated test runs correctly calibrate frame outer dimensions to prevent false-alarm session lockdowns.

---

## 3. Evidence Gallery (Iteration 04)
1. `qa-audit/iterations/iteration-04/evidence/IT04_TC01_topbar_brand_identity.png`
2. `qa-audit/iterations/iteration-04/evidence/IT04_TC02_dynamic_nav_items.png`
3. `qa-audit/iterations/iteration-04/evidence/IT04_TC03_mobile_drawer_opened.png`
4. `qa-audit/iterations/iteration-04/evidence/IT04_TC04_focus_exam_mode_guard.png`
5. `qa-audit/iterations/iteration-04/evidence/IT04_TC05_unknown_route_fallback.png`
6. `qa-audit/iterations/iteration-04/evidence/IT04_TC06_browser_history_stack.png`
