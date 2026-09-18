# BRIEFING — 2026-09-14T05:39:40+07:00

## Mission
Investigate R3 (Assessment Page Question Authoring, Direct Editing, Document Import & Freezes) and R5 (Context-Aware Grounded AI Assistant, RAG Citations, Course Recommendation).

## 🔒 My Identity
- Archetype: explorer
- Roles: investigation, synthesis
- Working directory: e:\PWD301\.agents\teamwork_preview_explorer_survey_3
- Original parent: 6b157767-36de-4944-8dcd-93cc1a5571d7
- Milestone: survey_r3_r5

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Do NOT edit files outside working directory
- Apply Superpowers, Ponytail, Task Observer, Full Output Enforcement, Impeccable
- Final mandatory report line: "Đã dùng x skill gồm: ..."
- Report delivery to handoff.md and send_message to parent (6b157767-36de-4944-8dcd-93cc1a5571d7)

## Current Parent
- Conversation ID: 6b157767-36de-4944-8dcd-93cc1a5571d7
- Updated: 2026-09-14T05:39:40+07:00

## Investigation State
- **Explored paths**:
  - `docs/system/PWD301_SYSTEM_SPECIFICATION/` (`01_BUSINESS_RULE_CATALOG.md`, `06_NON_NEGOTIABLE_INVARIANTS.md`, `08_ASSESSMENT_ENGINE.md`, `13_AI_GEMINI_RAG.md`, `14_COURSE_RECOMMENDATION_RULES.md`, `07_ASSESSMENT_API.md`, `09_FILE_IMPORT_API.md`, `10_AI_API.md`)
  - `docs/database/PWD301_DATABASE_ARCHITECTURE/` (`07_DATA_DICTIONARY_ASSESSMENT.md`, `06_DATA_DICTIONARY_QUESTION_BANK.md`, `10_DATA_DICTIONARY_AI_RAG.md`)
  - `src/pwd301/models/` (`assessment.py`, `question_bank.py`, `file_import.py`, `ai_rag.py`)
  - `src/pwd301/services/` (`assessment_service.py`, `question_bank_service.py`, `import_service.py`, `ai_service.py`, `rag_service.py`, `recommendation_service.py`, `gemini_service.py`)
  - `src/pwd301/blueprints/` (`instructor/routes.py`, `student/routes.py`, `api_assessments/routes.py`, `api_questions/routes.py`, `api_ai/routes.py`)
  - `src/pwd301/templates/instructor/assessment_builder.html`
  - `src/pwd301/static/js/app_shell.js`
  - `frontend-preview/assets/js/views/instructor.js`
  - `tests/` (`test_assessment_api.py`, `test_ai_api.py`, `test_rag_service.py`)
- **Key findings**:
  - Detailed in `handoff.md`:
    - R3: Missing "+ Tạo câu hỏi mới", in-place editing, and "Upload PDF/DOCX" modals in `assessment_builder.html`. `import_service.py:create_import_job` discards `draft_assessment_id`. Invariants 13 & 14 are strictly enforced by `assessment_service.py`.
    - R5: `app_shell.js` does not transmit location context (`page_route`, `page_title`, `course_id`, `lesson_id`). `/student/ai/chat` reuses session conversation without dynamic scope switching. `send_chat_message` bypasses `ask_course_rag`. Recommendation engine is implemented but not connected to chat responses.
- **Unexplored areas**: None for R3 & R5 survey scope.

## Key Decisions Made
- Fully documented exact file locations, lines, missing endpoints, UI modal structures, and test verification suite in `handoff.md`.

## Artifact Index
- `e:\PWD301\.agents\teamwork_preview_explorer_survey_3\handoff.md` — Comprehensive Survey Report for R3 & R5
- `e:\PWD301\.agents\teamwork_preview_explorer_survey_3\progress.md` — Liveness heartbeat
- `e:\PWD301\.agents\teamwork_preview_explorer_survey_3\DISPATCH.md` — Inbound message log
