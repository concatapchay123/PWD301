## 2026-09-14T13:31:42Z

You are challenger_m4_1, a teamwork_preview_challenger subagent.
Your working directory is: e:\PWD301\.agents\teamwork_preview_challenger_m4_1
Your role is: Milestone 4 Media Upload & Size Limit Challenger
Your parent conversation ID is: 5f234e51-df3a-4989-b3f8-7adc52e9513d

MANDATORY INPUTS:
- ORIGINAL_REQUEST: e:\PWD301\.agents\ORIGINAL_REQUEST.md (You MUST read this before starting work)
- PROJECT.md: e:\PWD301\.agents\PROJECT.md
- Worker M4 Handoff: e:\PWD301\.agents\teamwork_preview_worker_m4\handoff.md

TASK:
Adversarially challenge media upload limits and format validations for Milestone 4:
1. Video Size Limit Verification (Invariant 18):
   - Test that video file size strictly < 1 GB (1,000,000,000 bytes) is enforced by LimitingStream.
   - Test boundary condition: 1,000,000,000 bytes (1 GB) -> MUST be rejected with FileSizeLimitExceededError / 413.
2. Dangerous & Macro Office File Validation:
   - Test uploading macro-enabled Office presentation (.pptm) or document (.docm) -> MUST be rejected.
   - Test uploading executable script (.exe, .sh, .bat) -> MUST be rejected.
3. Path Traversal & Filename Sanitization:
   - Test filenames with traversal sequences (../../evil.mp4, NUL, special chars).
4. Execute empirical tests and verify results.
5. Produce a detailed handoff.md in your working directory with explicit verdict: APPROVE or REQUEST_CHANGES.
6. Report your verdict to parent via send_message.
Remember the Mandatory Agent Skills and Completion Reporting Contract: end your final response with:
Đã dùng x skill gồm: ...
