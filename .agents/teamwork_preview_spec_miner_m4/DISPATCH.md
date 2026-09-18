## 2026-09-14T13:17:30Z
You are spec_miner_m4, a teamwork_preview_spec_miner subagent.
Your working directory is: e:\PWD301\.agents\teamwork_preview_spec_miner_m4
Your role is: Milestone 4 Specification Miner
Your parent conversation ID is: 5f234e51-df3a-4989-b3f8-7adc52e9513d

MANDATORY INPUTS:
- ORIGINAL_REQUEST: e:\PWD301\.agents\ORIGINAL_REQUEST.md (You MUST read this before starting work)
- PROJECT.md: e:\PWD301\.agents\PROJECT.md

TASK:
Mine authoritative specifications and invariants for Milestone 4 (R4: Multi-Format Lecture Authoring & Media Support):
1. Probe System Specifications:
   - docs/system/PWD301_SYSTEM_SPECIFICATION/domain/03_COURSE_LESSON_MANAGEMENT.md: lesson structure, lesson resources, video streaming requirements, resource types (VIDEO, DOCUMENT, SLIDES, CODE, LINK, etc.).
   - docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md:
     - Invariant 17: Video file limit < 1 GB.
     - Invariant on fail-closed file security: quarantined or unscanned files must NOT be accessible to students.
     - ADR-002: Public UUID exposure, no raw BigInt PK.
     - ADR-008: Fail-closed virus scanning and session-authenticated downloads.
2. Probe Database Architecture:
   - docs/database/PWD301_DATABASE_ARCHITECTURE/sql/002_course_learning.sql (lesson_resources table, columns, foreign keys, cascade delete).
   - docs/database/PWD301_DATABASE_ARCHITECTURE/05_DATA_DICTIONARY_COURSE.md
3. Extract precise validation rules: allowed MIME types, max sizes, resource type enum values, authorization constraints (instructor owns course, student actively enrolled).
4. Produce a detailed handoff.md in your working directory and communicate summary to parent via send_message.
Remember the Mandatory Agent Skills and Completion Reporting Contract: end your final response with:
Đã dùng x skill gồm: ...
