# BRIEFING — 2026-09-14T12:36:30Z

## Mission
Investigate the UI templates and web route architecture for Milestone 3 (R3: Assessment Page Question Authoring, Direct Editing & Document Import).

## 🔒 My Identity
- Archetype: explorer
- Roles: Milestone 3 UI & Route Explorer
- Working directory: e:\PWD301\.agents\teamwork_preview_explorer_m3_2
- Original parent: 5f234e51-df3a-4989-b3f8-7adc52e9513d
- Milestone: Milestone 3 (R3)

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Inspect existing codebase, canonical database contracts, specs, and frontend-preview
- Respect AGENTS.md, PWD301 rules (CSRF protection, Flask session auth, role-based blueprints, etc.)
- Use skills: superpowers, task-observer, ponytail, full-output-enforcement, impeccable

## Current Parent
- Conversation ID: 5f234e51-df3a-4989-b3f8-7adc52e9513d
- Updated: 2026-09-14T12:36:30Z

## Investigation State
- **Explored paths**:
  - `frontend-preview/assets/js/views/instructor.js` (assessmentBuilder lines 709-943, questionEditor lines 507-605, blueprintBuilder)
  - `src/pwd301/templates/instructor/assessment_builder.html` (lines 1-464)
  - `src/pwd301/blueprints/instructor/routes.py` (assessment routes lines 1354-1650, question routes lines 1138-1305, import routes lines 1874-2033)
  - `src/pwd301/blueprints/api_assessments/routes.py` & `api_questions/routes.py`
  - `src/pwd301/services/assessment_service.py` (assign_question, update_question_assignment, _serialize_assessment)
  - `src/pwd301/services/question_bank_service.py` (create_question, update_question, valid question types & difficulties)
  - `src/pwd301/services/import_service.py` (create_import_job, process_import_job, commit_import_job)
  - `src/pwd301/models/file_import.py` (DocumentImportJob draft_assessment_id column)
  - `src/pwd301/models/question_bank.py` (Question, QuestionRevision, QuestionRevisionChoice, QuestionRevisionAcceptedAnswer)
- **Key findings**:
  1. `assessment_builder.html` currently only has "+ Thêm câu hỏi từ Ngân hàng" via modal `#addQuestionModal` and static table with "Gỡ bỏ".
  2. Missing direct "+ Tạo câu hỏi mới" modal for Single Choice, Multiple Choice, True/False, Short Answer.
  3. Missing in-place points editing and question content editing modal.
  4. Missing "Upload PDF/DOCX tạo đề tự động" import modal and empty state widget.
  5. In `blueprints/instructor/routes.py`:
     - Need `POST /instructor/assessments/<assessment_id>/questions/create`
     - Need `POST /instructor/assessments/<assessment_id>/questions/<question_id>/edit`
     - Need `POST /instructor/assessments/<assessment_id>/import`
     - Need `get_instructor_assessment_detail_route` to ensure `data["public_id"]` and `data["question_assignments"]` are properly provided to `assessment_builder.html`.
  6. In `import_service.py`:
     - `create_import_job` accepts `draft_assessment_id` but failed to assign it to `job.draft_assessment_id`.
     - `commit_import_job` must auto-assign imported questions to `draft_assessment_id` when present.
  7. Invariant 14 (Structural Freeze) and Invariant 13 (Timing Lock) enforcement verified across all endpoints.
- **Unexplored areas**: None, full end-to-end investigation complete.

## Key Decisions Made
- Provided complete UI/UX blueprint matching `frontend-preview` design system and `app.css`.
- Provided exact route definitions, parameter parsing, CSRF protection, and error handling for Worker M3.

## Artifact Index
- e:\PWD301\.agents\teamwork_preview_explorer_m3_2\BRIEFING.md
- e:\PWD301\.agents\teamwork_preview_explorer_m3_2\progress.md
- e:\PWD301\.agents\teamwork_preview_explorer_m3_2\handoff.md
