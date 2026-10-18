# ITERATION 01 — EXECUTION RESULTS

**Execution Date:** 2026-10-18  
**Iteration Target:** Smoke testing, environment health check, baseline user journeys  
**Browser Engine:** Google Chrome 155.0.4283.60 (Playwright sync API)  
**Viewport:** 1366 x 768  
**Live Target:** `http://localhost:5000` (Docker Container `pwd301_web`)  

---

## 1. Test Execution Summary

| Test Case ID | Test Case Name | Execution Status | Evidence Artifact | Empirical Notes |
|---|---|---|---|---|
| **TC-IT01-001** | Environment Health & Authentic Telemetry | **PASS** | HTTP GET Status 200 | Live server root responds HTTP 200 OK |
| **TC-IT01-002** | Landing Page Shell & PPTQ Brand Identity | **PASS** | `IT01_TC02_landing_auth_view.png` | PPTQ logo verified; Login form inputs mounted |
| **TC-IT01-003** | Student Login & Learning Dashboard | **PASS** | `IT01_TC03_student_dashboard.png` | `student1@pwd301.local` logged in; redirected to `#/student/dashboard` |
| **TC-IT01-004** | Course Catalog & Search Discovery | **PASS** | `IT01_TC04_course_catalog.png` | Navigated to `#/student/catalog`; search and filters functional |
| **TC-IT01-005** | Admin Login & System Governance | **PASS** | `IT01_TC05_admin_governance.png` | Logged out from student; `admin@pwd301.local` logged in; redirected to `#/admin/governance` |

---

## 2. Evidence Gallery (Iteration 01)
1. `qa-audit/iterations/iteration-01/evidence/IT01_TC02_landing_auth_view.png`
2. `qa-audit/iterations/iteration-01/evidence/IT01_TC03_student_dashboard.png`
3. `qa-audit/iterations/iteration-01/evidence/IT01_TC04_course_catalog.png`
4. `qa-audit/iterations/iteration-01/evidence/IT01_TC05_admin_governance.png`
