## 2026-09-14T13:47:52Z

<USER_REQUEST>
You are explorer_m5_1, a teamwork_preview_explorer subagent.
Your working directory is: e:\PWD301\.agents\teamwork_preview_explorer_m5_1
Your role is: Milestone 5 AI Context & RAG Explorer
Your parent conversation ID is: 5f234e51-df3a-4989-b3f8-7adc52e9513d

MANDATORY INPUTS:
- ORIGINAL_REQUEST: e:\PWD301\.agents\ORIGINAL_REQUEST.md (You MUST read this before starting work)
- PROJECT.md: e:\PWD301\.agents\PROJECT.md

TASK:
Investigate AI context transmission, dynamic scoping, and grounded RAG citations for Milestone 5 (R5):
1. Client-Side Context Transmission:
   - src/pwd301/static/js/app_shell.js:
     - How is the AI chat widget initialized and how does it send messages?
     - How does it currently detect page route, page title, course ID, and lesson ID from the DOM or URL?
     - What payload does it send to the backend? Ensure it includes `page_route`, `page_title`, `course_id`, `lesson_id`.
2. Dynamic Conversation Scoping:
   - src/pwd301/blueprints/api_ai/routes.py:
     - Inspect the chat endpoint (e.g. `/api/v1/ai/chat` or similar).
     - How are conversation sessions created or retrieved?
     - How does it bind conversation scope? (If `lesson_id` -> scope LESSON; elif `course_id` -> scope COURSE; else -> GLOBAL).
3. Grounded Semantic RAG Citations:
   - src/pwd301/services/rag_service.py and src/pwd301/services/ai_chat_service.py:
     - How are RAG chunks retrieved for a course/lesson?
     - How are citations formatted? Requirement explicitly specifies `[Ref: <UUID>]` citations pointing to retrieved chunks/documents.
     - Verify pre-auth filtering (enrolled students only; published courses only; non-deleted chunks).
     - Verify 5-minute ephemeral chat retention policy.
4. Synthesize your findings and provide an exact technical implementation plan for Worker M5.
5. Produce a detailed handoff.md in your working directory and report results via send_message.
Remember the Mandatory Agent Skills and Completion Reporting Contract: end your final response with:
Đã dùng x skill gồm: ...
</USER_REQUEST>
