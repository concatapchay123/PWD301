## 2026-09-13T22:35:43Z

You are Survey Explorer 3 (teamwork_preview_explorer).
Your working directory: e:\PWD301\.agents\teamwork_preview_explorer_survey_3
Original request file: e:\PWD301\.agents\ORIGINAL_REQUEST.md
Reference audit report: e:\PWD301\.agents\AUDIT_REPORT.md

Your mission: Investigate the codebase and specifications for:
1. R3: Assessment Page Question Authoring, Direct Editing & Document Import:
   - In Assessment Builder (instructor/assessment_builder.html): direct question creation (Single Choice, Multiple Choice, True/False, Short Answer) with custom points/choices/explanations.
   - In-place editing of question content, choices, correct answers.
   - Automatic question generation/import by uploading PDF and Word (.docx) files directly from assessment page into import_service.
   - Strict enforcement of Assessment Timing Lock (BR-031 / Invariant 13) and Structural Freeze (BR-030 / Invariant 14) once student attempts have commenced.
2. R5: Context-Aware, Grounded AI Assistant & Smart Course Recommendation:
   - Client-side app_shell.js sending active page route, page title, course_id, lesson_id on interaction.
   - Dynamic conversation scoping to active course/lesson context (not defaulting to GLOBAL).
   - Grounded semantic RAG against lesson text and attached file content with citations [Ref: <UUID>].
   - Course catalog knowledge and recommendation engine.

Authoritative sources to inspect:
- docs/system/PWD301_SYSTEM_SPECIFICATION/ (05_ASSESSMENT_AND_EXAM_ENGINE.md, 07_AI_TUTOR_AND_RAG_PIPELINE.md, 01_BUSINESS_RULE_CATALOG.md, 06_NON_NEGOTIABLE_INVARIANTS.md).
- docs/database/PWD301_DATABASE_ARCHITECTURE/ (assessments, questions, question_choices, ai_conversations, ai_messages).
- frontend-preview/ (assessment builder, AI chat widget).
- src/pwd301/services/ (assessment_service.py, question_bank_service.py, import_service.py, ai_chat_service.py, rag_service.py).
- src/pwd301/blueprints/ (instructor/routes.py, api_assessments/routes.py, api_questions/routes.py, api_ai/routes.py).
- src/pwd301/templates/instructor/assessment_builder.html.
- src/pwd301/static/js/app_shell.js.
- tests/ (test_assessments.py, test_ai.py, test_rag.py).

Deliverable:
Write a comprehensive report to e:\PWD301\.agents\teamwork_preview_explorer_survey_3\handoff.md detailing:
- Current state, routes, and services for R3 & R5.
- Exact endpoints, UI elements, and import pipeline connections for direct question authoring and PDF/DOCX import.
- Exact mechanism for app_shell.js context transmission, RAG grounding citations [Ref: <UUID>], and course catalog recommendation engine.
- Test plan and verification commands for R3 & R5.
Send a message back to parent when complete.
