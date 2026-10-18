# ITERATION 06 — EXECUTION RESULTS

**Execution Date:** 2026-10-18  
**Iteration Focus:** CRUD Workflows, Persistence, Refresh Resilience & Draft Aggregation vs Published State  
**Browser Engine:** Google Chrome 155.0.4283.60 (Playwright sync API)  
**Viewport:** 1366 x 768  
**Live Target:** `http://localhost:5000`  

---

## 1. Test Execution Summary

| Test Case ID | Test Case Name | Status | Evidence Artifact | Empirical Notes |
|---|---|---|---|---|
| **TC-IT06-001** | Idempotent Navigation on Manage Route | **PASS** | `IT06_TC01_idempotent_navigation.png` | Navigating to `#/instructor/courses/manage` without `id` safely redirects to `#/instructor/courses` with zero DB writes |
| **TC-IT06-002** | UI Course Creation via Studio Modal | **PASS** | `IT06_TC02_ui_course_creation.png` | Created course `QA_E2C4A3` via modal; automatically navigated to Single-Page Studio (`id=1b75d76e...`) |
| **TC-IT06-003** | Studio Header Render & Status Badge | **PASS** | `IT06_TC03_studio_header_render.png` | Studio header rendered course title, code, and status badge `Bản nháp (Draft)` |
| **TC-IT06-004** | Learning Unit (Chapter) Creation in Studio | **PASS** | `IT06_TC04_chapter_creation.png` | Created Chapter 1 (*"Chương 1: Nguyên lý Kiểm thử Hiệu năng Hệ thống"*); rendered in curriculum tree |
| **TC-IT06-005** | Browser Refresh Resilience & Read-After-Write | **PASS** | `IT06_TC05_refresh_resilience.png` | Full browser reload confirmed 100% persistence of Course and Chapter 1 without data loss |
| **TC-IT06-006** | Duplicate Course Code 409 Conflict Enforcement | **PASS** | `IT06_TC06_duplicate_code_conflict.png` | Duplicate code rejected with HTTP 409 Conflict (*"Dữ liệu bị trùng lặp hoặc xung đột trạng thái."*) |

---

## 2. Invariant & Architecture Verification

### 2.1. Idempotent Navigation & Lazy Creation Invariant (AGENTS.md Section 10.7)
- **Rule:** Every navigation method for create/manage views must be side-effect free. No records may be written to the database solely because a user loaded a URL.
- **Verification:** Verified that requesting `#instructor/courses/manage` without an explicit entity ID does not trigger draft instantiation. The router displays an informational toast and redirects to the safe parent list.

### 2.2. Single-Page Studio & Draft Aggregation (AGENTS.md Section 4 & 10)
- In the Instructor Single-Page Studio, learning units and lessons are authored within the course draft aggregate.
- Content changes persist cleanly to SQL Server backend and survive hard browser reloads (`read-after-write consistency`).
- Unique constraints on `course_code` are strictly enforced at the SQL Server schema level, returning standardized HTTP 409 JSON responses without application crashes.

---

## 3. Evidence Gallery (Iteration 06)
1. `qa-audit/iterations/iteration-06/evidence/IT06_TC01_idempotent_navigation.png`
2. `qa-audit/iterations/iteration-06/evidence/IT06_TC02_ui_course_creation.png`
3. `qa-audit/iterations/iteration-06/evidence/IT06_TC03_studio_header_render.png`
4. `qa-audit/iterations/iteration-06/evidence/IT06_TC04_chapter_creation.png`
5. `qa-audit/iterations/iteration-06/evidence/IT06_TC05_refresh_resilience.png`
6. `qa-audit/iterations/iteration-06/evidence/IT06_TC06_duplicate_code_conflict.png`
