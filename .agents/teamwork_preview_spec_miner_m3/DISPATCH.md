## 2026-09-14T12:31:50Z

<USER_REQUEST>
You are spec_miner_m3, a teamwork_preview_spec_miner subagent.
Your working directory is: e:\PWD301\.agents\teamwork_preview_spec_miner_m3
Your role is: Milestone 3 Specification Miner
Your parent conversation ID is: 5f234e51-df3a-4989-b3f8-7adc52e9513d

MANDATORY INPUTS:
- ORIGINAL_REQUEST: e:\PWD301\.agents\ORIGINAL_REQUEST.md (You MUST read this before starting work)
- PROJECT.md: e:\PWD301\.agents\PROJECT.md

TASK:
Mine authoritative specifications for Milestone 3 (R3: Assessment Page Question Authoring, Direct Editing & Document Import):
1. Probe System Specification documents:
   - docs/system/PWD301_SYSTEM_SPECIFICATION/business/01_BUSINESS_RULE_CATALOG.md: Specifically BR-030 (structural freeze) and BR-031 (timing lock).
   - docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md: Invariant 13 (server-authoritative assessment timing locked after publish) and Invariant 14 (structural freeze after first student starts).
   - docs/system/PWD301_SYSTEM_SPECIFICATION/domain/04_ASSESSMENT_QUESTION_BANK.md: question types, choices, point assignments, bloom difficulties, historical question revision rules.
2. Mine Database Architecture:
   - docs/database/PWD301_DATABASE_ARCHITECTURE/sql/003_assessment_engine.sql
   - docs/database/PWD301_DATABASE_ARCHITECTURE/sql/005_file_import_rag.sql (DocumentImportJob fields, draft_assessment_id)
3. Extract precise invariant boundaries, error types, error messages, and validation rules that must be strictly enforced.
4. Produce a detailed handoff.md in your working directory and communicate summary to parent via send_message.
Remember the Mandatory Agent Skills and Completion Reporting Contract: end your final response with:
Đã dùng x skill gồm: ...
</USER_REQUEST>
