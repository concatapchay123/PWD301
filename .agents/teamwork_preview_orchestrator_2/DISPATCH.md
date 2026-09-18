## 2026-09-14T05:35:12+07:00
You are the Project Orchestrator (teamwork_preview_orchestrator) for PWD301.

Working directory: e:\PWD301\.agents\teamwork_preview_orchestrator_2
Project workspace: e:\PWD301
Original request file: e:\PWD301\.agents\ORIGINAL_REQUEST.md
Reference audit report: e:\PWD301\.agents\AUDIT_REPORT.md

Your mission: Execute comprehensive upgrade and bug remediation for the PWD301 LMS platform covering:
- R1: File Upload, Virus Scanning & Secure Access Remediation (fix display_name, original_filename, size, MIME type, clean/quarantined status, unstick PENDING status, fix authenticated session downloads for Instructors/Students without 403, maintain ADR-002 and ADR-008 fail-closed).
- R2: Deep Instructor Course Customization & Dynamic Student View (Learning objectives & skills, target audience & requirements, course prerequisites with cycle prevention, curriculum/syllabus structure, and dynamic rendering in student course detail without hardcoded placeholders).
- R3: Assessment Page Question Authoring, Direct Editing & Document Import (In-page creation for Single/Multiple Choice, True/False, Short Answer with custom points/choices/explanations; in-place editing; automatic question generation/import from PDF and DOCX; strict enforcement of timing lock BR-031 and structural freeze BR-030).
- R4: Multi-Format Lecture Authoring & Media Support (Upload/attach PDF, DOCX, PPTX, MP4/WebM video < 1GB bound to LessonResource/FileAsset; student-facing lecture viewer for videos, slides/docs, and downloadable resources).
- R5: Context-Aware, Grounded AI Assistant & Smart Course Recommendation (Client-side app_shell.js sending active route, page title, course_id, lesson_id; auto-binding conversation context; grounded RAG with citations [Ref: <UUID>]; catalog-aware course recommendation engine).

Contract requirements:
- Strictly adhere to AGENTS.md, docs/system/PWD301_SYSTEM_SPECIFICATION, and docs/database/PWD301_DATABASE_ARCHITECTURE.
- Follow Mandatory Agent Skills & Completion Reporting: apply superpowers (TDD, systematic debugging, verification before completion), task-observer, ponytail (minimal change, zero over-engineering), full-output-enforcement, and impeccable for UI/UX templates.
- Ensure all automated tests (pytest / ./scripts/verify.ps1) pass with zero regressions.
- Maintain your plan.md, progress.md, and BRIEFING.md in e:\PWD301\.agents\teamwork_preview_orchestrator_2.
- When all requirements are implemented and verified, report completion to the Sentinel.
