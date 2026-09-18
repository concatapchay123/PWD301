# Orchestration Plan: PWD301 LMS Comprehensive Upgrade & Remediation

## Objective
Implement and verify all 5 core requirements from ORIGINAL_REQUEST.md (2026-09-13):
1. **R1**: File Upload, Virus Scanning & Secure Access Remediation
2. **R2**: Deep Instructor Course Customization & Dynamic Student View
3. **R3**: Assessment Page Question Authoring, Direct Editing & Document Import
4. **R4**: Multi-Format Lecture Authoring & Media Support
5. **R5**: Context-Aware, Grounded AI Assistant & Smart Course Recommendation
6. **E2E / Full Verification**: Ensure 100% test pass (pytest / ./scripts/verify.ps1) and zero regressions.

## Orchestration Phases
- **Phase 0: Comprehensive Survey (Exploration)**
  - Explorer 1: Deep dive into R1 (Files/Scanning/Downloads) & R4 (Lecture Media/LessonResource/Streaming).
  - Explorer 2: Deep dive into R2 (Course Customization/Prerequisites/Syllabus/Dynamic Student View).
  - Explorer 3: Deep dive into R3 (Assessment Question Authoring/In-place Edit/PDF-DOCX Import) & R5 (Context-aware AI/RAG/Recommendation).
  - Synthesize findings into `PROJECT.md` with full architecture, feature inventory, milestone plan, and interface contracts.

- **Phase 1: Milestone Execution (Iterative Direct Loop per Milestone)**
  - For each Milestone (M1 -> M5):
    - Explorer: Analyze exact implementation path, affected files, tests.
    - Worker: Implement changes, write tests, verify build & test pass.
    - Reviewer 1 & 2: Review correctness, spec adherence, invariants, security.
    - Challenger 1 & 2: Stress test, edge cases, regression check.
    - Forensic Auditor: Integrity check, no hardcoding, no facades.
    - Gate evaluation: Strict PASS required before advancing.

- **Phase 2: E2E Testing & Final Acceptance**
  - Verify all automated test suites (`pytest`, `scripts/repo_check.py`, `ruff`, `mypy`).
  - Final audit verification.
  - Completion report to Sentinel.
