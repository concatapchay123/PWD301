# TASK-023 — Gemini Integration & Backend Rule Recommendation Engine

**Status:** COMPLETED  
**Assignee:** Principal Software Architect & Lead Fullstack Python/Flask Engineer  
**Depends on:** TASK-005, TASK-009  
**Completed Date:** 2026-09-10  

---

## Goal
Implement the **Gemini Integration & Backend Rule Recommendation Engine** for PWD301:
1. **Gemini Client & Resilience Engine (`src/pwd301/services/gemini_service.py`)**:
   - Seamless dual-mode: Real Gemini API client when configured with `GEMINI_API_KEY`, and deterministic, offline `MockGeminiClient` in testing/offline environments.
   - Comprehensive exception handling: Timeout, Quota Exceeded (HTTP 429), API Service Unavailable (HTTP 503), Malformed JSON response.
   - Telemetry and usage audit tracking into `ai_requests` table with bounded transactions and zero secrets logging.
2. **Algorithm 14: Hybrid Course Recommendation Engine (`src/pwd301/services/recommendation_service.py`)**:
   - Rule-based filtering: Exclude unenrolled/ineligible courses, active enrollments, completed courses, and archived courses. Enforce prerequisite completion.
   - Deterministic candidate ranking: Category matching (+30), natural difficulty progression (+20), cold-start beginner prioritization (+15), prerequisite completion (+25).
   - AI Explanation Enrichment: Enrich recommendations with 1–2 sentence Gemini explanations with graceful degradation to standard rule-based explanations on Gemini unavailability/quota limits.
3. **AI Question Drafting for Instructors (`src/pwd301/services/ai_service.py`)**:
   - Strictly authorized to instructors managing the course or system administrators.
   - Draft structured questions (SINGLE_CHOICE, MULTIPLE_CHOICE, TRUE_FALSE, SHORT_ANSWER, ESSAY) persisted in `ai_generated_question_drafts` in `PENDING` state.
4. **AI Conversation Lifecycle & 5-Minute Inactivity Rule (AI-003)**:
   - 300-second inactivity deadline (`AI_CHAT_INACTIVITY_SECONDS = 300`).
   - Inactivity marks session as `EXPIRED` (HTTP 409 `CONVERSATION_EXPIRED` on subsequent message attempt).
   - Automated purge engine removes raw chat messages from expired conversations to retain only minimal metadata.
5. **Security, ADR-002 Zero Internal PK Leakage & Prompt Injection Defense**:
   - Zero internal BIGINT IDs exposed: 100% public UUID identifiers (`conversation_id`, `message_id`, `draft_id`, `course_id`).
   - Deep prompt sanitization and injection detection ("ignore previous instructions", "system prompt reveal", etc.) rejecting malicious payloads with HTTP 400 `PROMPT_INJECTION_DETECTED`.
   - IDOR prevention on conversation access and strict RBAC on API endpoints.

---

## Source-of-Truth Documents Consulted
- `AGENTS.md` (Operational contract, Fail-closed invariants, Zero PK Leakage, CSRF protection)
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/13_AI_GEMINI_RAG.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/algorithms/14_COURSE_RECOMMENDATION_RULES.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/api/10_AI_API.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/security/06_AI_RAG_SECURITY.md`
- `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/007_ai_rag.sql`
- `docs/decisions/ADR-002-database-identifiers.md`

