# TASK-024 — RAG Knowledge Lifecycle, Semantic Retrieval & AI Security Fortress

**Status:** COMPLETED  
**Assignee:** Principal Software Architect & Lead Fullstack Python/Flask Engineer  
**Depends on:** TASK-023  
**Completed Date:** 2026-09-10  

---

## Goal
Implement the **RAG Knowledge Lifecycle, Semantic Retrieval & AI Security Fortress** for PWD301:
1. **RAG Service & Knowledge Chunking (`src/pwd301/services/rag_service.py`)**:
   - Adaptive sliding-window token chunking with sentence boundary preservation, SHA-256 content hashing (`text_hash`), and overlap controls.
   - Lesson content ingestion: strictly published lessons indexed with idempotent re-ingestion and version invalidation (ADR-009 & `KNOWLEDGE_STATE_MACHINE.md`).
   - Fail-closed course file ingestion: strictly `ACTIVE` files with virus scan result `PASS` and existing storage blobs; unscanned or quarantined files immediately rejected with `FileSecurityQuarantineError`.
   - Batch course ingestion orchestrating lessons and verified file assets.
2. **Pre-Retrieval Authorization & Hybrid Retrieval**:
   - Strict resource-level authorization before vector search: Students require active course enrollment (`Enrollment.status == 'ACTIVE'`); Instructors must manage the course; Admins permitted; Guests/unauthenticated rejected.
   - Archived and trashed course exclusion: courses in non-published or archived states immediately return zero chunks.
   - Hybrid lexical-semantic relevance scoring with cosine similarity embeddings.
3. **SEC-006 AI Security Fortress & Context Boundary Isolation**:
   - Context boundary isolation: all retrieved context wrapped in `<retrieved_context>` tags as untrusted data.
   - Grounded synthesis: AI answers cite verifiable evidence `[Ref: <UUID>]` mapping back to specific `KnowledgeChunk` and `KnowledgeDocument`.
   - Prompt injection defense: adversarial inputs targeting context or model instructions rejected with HTTP 400 `PROMPT_INJECTION_DETECTED`.
   - End-to-end source tracking into `ai_source_usages` and `ai_requests` with bounded transactions and zero secrets logging.
4. **ADR-002 Zero Internal PK Leakage**:
   - 100% public UUID identifiers (`source_id`, `chunk_id`, `usage_id`, `ai_request_id`, `course_id`, `lesson_id`).
   - Zero internal BIGINT IDs exposed across all API payloads and response models.
5. **REST API Endpoints (`src/pwd301/blueprints/api_ai/routes.py`)**:
   - `POST /api/ai/courses/<course_id>/ingest` (Instructor/Admin)
   - `POST /api/ai/lessons/<lesson_id>/ingest` (Instructor/Admin)
   - `POST /api/ai/courses/<course_id>/query` (Enrolled Student / Course Instructor / Admin)
   - `GET /api/ai/courses/<course_id>/sources` (Instructor/Admin)
   - `DELETE /api/ai/sources/<source_id>` (Instructor/Admin)

---

## Source-of-Truth Documents Consulted
- `AGENTS.md` (Operational contract, Fail-closed invariants, Zero PK Leakage, CSRF protection)
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/13_AI_GEMINI_RAG.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/security/06_AI_RAG_SECURITY.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/api/10_AI_API.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/architecture/KNOWLEDGE_STATE_MACHINE.md`
- `docs/decisions/ADR-002-database-identifiers.md`
- `docs/decisions/ADR-009-knowledge-indexing-pipeline.md`
- `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/007_ai_rag.sql`

