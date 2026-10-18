# Master Test Plan — Iteration 08: Multi-Step Business Workflows: Course Lifecycle & Staging Drafts

## 1. Executive Summary & Iteration Target
- **Iteration ID:** `IT08`
- **Target Subsystem:** Course Authoring & Review Subsystem, Unified Staging Draft Engine, Admin Governance Workflow, Catalog Publishing Gate.
- **Focus Area:** Multi-step asynchronous workflows across Instructor, Admin, and Student roles:
  1. Pre-flight course publish readiness validation (fail-closed rejection when incomplete).
  2. End-to-end Course Submission (`DRAFT` -> `SUBMITTED_FOR_REVIEW`).
  3. Admin Review Queue (`#/admin/governance?tab=courses`) & Inspection Dossier.
  4. Course Approval & Publication (`SUBMITTED_FOR_REVIEW` -> `APPROVED` -> `PUBLISHED`).
  5. Unified Staging Draft Invariant: Post-publication curriculum modifications staged into `COURSE_VERSION_CHANGESET` without live student leakage.
  6. Atomic All-or-Nothing Changeset Diff Modal & Admin Approval.
- **Execution Mode:** Real Google Chrome (Playwright `channel="chrome"`), REST API validation, SQL Server state verification.

---

## 2. Multi-Agent Role Allocation
- **AGENT 01 (QA Orchestrator):** Test orchestration, lifecycle sequencing, multi-role handoff control.
- **AGENT 02 (Frontend & UI/UX QA):** Studio header status badges, locked UI inspection while under review, Admin Governance queue rendering, diff viewer modal rendering.
- **AGENT 03 (Backend & API QA):** Contract compliance for `/instructor/courses/<id>/submit`, `/admin/courses/<id>/review`, `/admin/courses/<id>/publish`, and `/courses/<id>/changeset/*`.
- **AGENT 04 (Database QA):** SQL Server verification of `course.status`, `course_change_request`, and curriculum referential integrity.
- **AGENT 05 (Security & RBAC QA):** Verification that instructors cannot self-approve courses and students cannot access draft/staged units.
- **AGENT 06 (Business Workflow QA):** End-to-end lifecycle verification, state transition rules, atomic review and rollback semantics.
- **AGENT 08 (Independent Auditor):** Verification of empirical evidence, annotated screenshots, and false-positive elimination.

---

## 3. Test Cases Inventory
1. `TC-IT08-001`: Pre-Flight Publish Readiness Validation (Fail-Closed Rejection when Incomplete)
2. `TC-IT08-002`: Complete Course Submission & Status Transition to `SUBMITTED_FOR_REVIEW`
3. `TC-IT08-003`: Admin Governance Queue & Course Inspection Dossier
4. `TC-IT08-004`: Admin Course Approval & Publication Transition (`APPROVED` -> `PUBLISHED`)
5. `TC-IT08-005`: Unified Staging Draft Invariant (Post-Publication Curriculum Isolation)
6. `TC-IT08-006`: Atomic All-or-Nothing Changeset Diff Modal & Admin Approval

---

## 4. Test Environment & Accounts
- **Host:** `http://localhost:5000`
- **Database:** Microsoft SQL Server on `localhost:1433`
- **Accounts:**
  - Instructor: `instructor1@pwd301.local` / `Password123!`
  - Admin: `admin@pwd301.local` / `Password123!`
  - Student: `student1@pwd301.local` / `Password123!`
