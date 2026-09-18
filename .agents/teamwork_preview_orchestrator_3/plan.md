# Orchestration Plan — PWD301 Upgrade & Remediation (Orchestrator 3)

## Objective
Drive completion of Milestones M2 through M6 adhering strictly to AGENTS.md, docs/system/PWD301_SYSTEM_SPECIFICATION, docs/database/PWD301_DATABASE_ARCHITECTURE, and Mandatory Agent Skills.

---

## Phase Breakdown

### Step 1: Milestone 2 Verification Gate
- **Input**: Worker M2 implementation (`tests/test_m2_course_customization.py`, migration 0005, `course_manage.html`, `course_detail.html`, `course_service.py`, `course.py`).
- **Dispatch**:
  - Reviewer 1 & 2 (`teamwork_preview_reviewer`): Code review, contract conformance, zero hardcoded strings in templates, CSRF/auth verification.
  - Challenger 1 & 2 (`teamwork_preview_challenger`): Empirical challenge, cycle detection stress testing (A->B->A, A->B->C->A, A->A), invalid input edge cases.
  - Forensic Auditor (`teamwork_preview_auditor`): Static verification, diff analysis, authenticity audit (no dummy/facade implementations, no hardcoded test shortcuts).
- **Gate Evaluation**: Strict AND of all verdicts. On PASS -> Mark M2 DONE.

### Step 2: Milestone 3 (R3: Assessment Authoring, Editing & Import)
- **Scope**:
  - In-page question authoring for Single/Multiple Choice, True/False, Short Answer.
  - In-place question editing and points assignment.
  - PDF/DOCX question import directly into draft assessment via `draft_assessment_id`.
  - Timing lock (BR-031 / Invariant 13) and structural freeze (BR-030 / Invariant 14).
- **Iteration Loop**: Explorer -> Worker -> Reviewer -> Challenger -> Auditor -> Gate.

### Step 3: Milestone 4 (R4: Multi-Format Lecture Authoring & Viewers)
- **Scope**:
  - PDF, DOCX, PPTX, MP4/WebM video < 1GB bound to `LessonResource` and `FileAsset`.
  - Student lecture viewer (HTML5 video player, doc viewer, downloadable resources tab).
- **Iteration Loop**: Explorer -> Worker -> Reviewer -> Challenger -> Auditor -> Gate.

### Step 4: Milestone 5 (R5: Context-Aware AI & Recommendations)
- **Scope**:
  - `app_shell.js` transmits active route, title, course_id, lesson_id.
  - Auto-binding AI conversation context (LESSON -> COURSE -> GLOBAL).
  - Grounded RAG with citations `[Ref: <UUID>]`.
  - Smart course recommendation engine (Algorithm 14).
- **Iteration Loop**: Explorer -> Worker -> Reviewer -> Challenger -> Auditor -> Gate.

### Step 5: Milestone 6 (R6: Full Test Suite Pass & Adversarial Hardening)
- **Scope**:
  - Full pytest test suite execution across all modules.
  - Repository contract check (`scripts/repo_check.py`).
  - Adversarial hardening and regression audit.
- **Reporting**: Comprehensive final completion report to Sentinel.
