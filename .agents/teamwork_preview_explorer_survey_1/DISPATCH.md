## 2026-09-13T22:35:43Z
You are Survey Explorer 1 (teamwork_preview_explorer).
Your working directory: e:\PWD301\.agents\teamwork_preview_explorer_survey_1
Original request file: e:\PWD301\.agents\ORIGINAL_REQUEST.md
Reference audit report: e:\PWD301\.agents\AUDIT_REPORT.md

Your mission: Investigate the codebase and specifications for:
1. R1: File Upload, Virus Scanning & Secure Access Remediation:
   - File asset rendering in Instructor & Student views: display_name, original_filename, size, MIME type, clean/quarantined scan status.
   - Why uploaded files get stuck in PENDING status; how virus scan background jobs / synchronous scan triggers work.
   - Web session authenticated download endpoints for Instructors and enrolled Students without 403 Forbidden errors (ADR-002, ADR-008 fail-closed).
2. R4: Multi-Format Lecture Authoring & Media Support:
   - Upload/attach PDF, DOCX, PPTX, MP4/WebM video (< 1GB) bound to LessonResource/FileAsset.
   - Student-facing lecture viewers for video streaming, slide/doc presentation, and downloads.

Authoritative sources to inspect:
- docs/system/PWD301_SYSTEM_SPECIFICATION/ (especially 09_FILE_STORAGE_AND_VIRUS_SCANNING.md, 04_COURSE_AND_LESSON_LIFECYCLE.md, 06_NON_NEGOTIABLE_INVARIANTS.md).
- docs/database/PWD301_DATABASE_ARCHITECTURE/ (file_assets, lesson_resources, lessons, courses tables).
- frontend-preview/ (reference UI for file lists and lesson viewer).
- src/pwd301/services/ (file_service.py, virus_scan_service.py, storage_service.py, lesson_service.py).
- src/pwd301/blueprints/ (api_files/routes.py, instructor/routes.py, student/routes.py).
- src/pwd301/templates/ (instructor and student templates for files and lessons).
- tests/ (tests/test_files.py, tests/test_lessons.py, etc.).

Deliverable:
Write a comprehensive report to e:\PWD301\.agents\teamwork_preview_explorer_survey_1\handoff.md detailing:
- Current state and root causes of existing defects for R1 & R4.
- Exact schema and model capabilities (fields available vs needed).
- Exact file changes, routes, services, and templates needed for R1 & R4.
- Test plan and verification commands for R1 & R4.
Send a message back to parent when complete.
