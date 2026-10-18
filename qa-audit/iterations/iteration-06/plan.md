# ITERATION 06 TEST PLAN

**Iteration Focus:** CRUD Workflows, Persistence, Refresh Resilience & Draft Aggregation vs Published State  
**Responsible Agents:** AGENT 02 (Frontend & UI/UX QA), AGENT 03 (Backend & API QA), AGENT 04 (Database & Data Integrity QA), AGENT 06 (E2E Business Workflow QA), AGENT 08 (Independent Auditor)  
**Target Environment:** Local Live Stack (`http://localhost:5000`)  
**Browser Engine:** Google Chrome 155 via Playwright  
**Viewport:** 1366 x 768  

---

## 1. Objectives
1. Verify Idempotent Navigation & Lazy Creation Invariant (Section 10.7): visiting creation routes without deliberate user submit causes zero side-effects.
2. Verify full UI Course creation workflow via modal and redirection into Single-Page Studio (`#/instructor/courses/manage?id=...`).
3. Verify Learning Unit (Chapter) authoring and real-time tree injection in Studio outline.
4. Verify browser refresh resilience and read-after-write consistency (page reload preserves drafts).
5. Verify duplicate course code 409 Conflict rejection in database and API layer.

---

## 2. Test Cases Overview
- `TC-IT06-001`: Idempotent Navigation on Manage/Create Routes (Zero Side-Effects)
- `TC-IT06-002`: UI Course Creation via Instructor Studio Modal
- `TC-IT06-003`: Studio Header Render & Status Badge Verification (`DRAFT`)
- `TC-IT06-004`: Learning Unit (Chapter) Creation in Single-Page Studio
- `TC-IT06-005`: Browser Refresh Resilience & Read-After-Write Consistency
- `TC-IT06-006`: Duplicate Course Code Uniqueness Enforcement (409 Conflict)
