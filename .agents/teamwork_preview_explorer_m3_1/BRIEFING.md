# BRIEFING — 2026-09-14T12:35:00Z

## Mission
Investigate the backend architecture for Milestone 3 (R3: Assessment Page Question Authoring, Direct Editing & Document Import).

## 🔒 My Identity
- Archetype: explorer
- Roles: Milestone 3 Backend Architecture Explorer
- Working directory: e:\PWD301\.agents\teamwork_preview_explorer_m3_1
- Original parent: 5f234e51-df3a-4989-b3f8-7adc52e9513d
- Milestone: Milestone 3 (R3)

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Inspect models, services, blueprints, schemas, and tests
- Respect historical revisions, structural freeze, and security rules

## Current Parent
- Conversation ID: 5f234e51-df3a-4989-b3f8-7adc52e9513d
- Updated: 2026-09-14T12:35:00Z

## Investigation State
- **Explored paths**:
  - `src/pwd301/models/assessment.py`: Assessment, AssessmentQuestionAssignment, AssessmentSection
  - `src/pwd301/models/question_bank.py`: Question, QuestionRevision, QuestionRevisionChoice, QuestionRevisionAcceptedAnswer
  - `src/pwd301/models/file_import.py`: DocumentImportJob, ImportQuestion
  - `src/pwd301/services/assessment_service.py`: assign_question, remove_question_assignment, update_question_assignment, update_assessment
  - `src/pwd301/services/question_bank_service.py`: create_question, update_question, is_question_in_use
  - `src/pwd301/services/import_service.py`: create_import_job, process_import_job, commit_import_job
  - `src/pwd301/blueprints/instructor/routes.py`: assessment builder & import routes
  - `src/pwd301/templates/instructor/assessment_builder.html`: UI assessment builder
- **Key findings**:
  1. `DocumentImportJob` model already has `draft_assessment_id` column and FK in SQL Server schema & Alembic migration 0001, but `create_import_job` omitted saving it to the instance, and `commit_import_job` omitted auto-assigning questions when `job.draft_assessment_id` is set.
  2. Question creation & revision lifecycle is already mature in `question_bank_service.py` (`create_question` and `update_question` with `is_question_in_use` revision branching), so the assessment builder routes can directly reuse these services without duplication.
  3. Missing routes to implement:
     - `POST /instructor/assessments/<assessment_id>/questions/create`
     - `POST /instructor/assessments/<assessment_id>/questions/<question_id>/edit`
     - `POST /instructor/assessments/<assessment_id>/import`
  4. Assessment builder template needs 3 UI elements: "+ Tạo câu hỏi mới" modal, in-place edit modal/actions, and "Upload PDF/DOCX tạo đề" modal.
- **Unexplored areas**: None for M3 architecture.

## Key Decisions Made
- Reused existing services (`create_question`, `assign_question`, `update_question`, `update_question_assignment`, `create_import_job`, `process_import_job`, `commit_import_job`) adhering to Ponytail minimal-change principle.
- Formulated exact implementation guide and verification commands for Worker.

## Artifact Index
- DISPATCH.md — Recorded initial instructions
- BRIEFING.md — Persistent context & state
- progress.md — Liveness heartbeat
- handoff.md — Complete 5-component handoff report
