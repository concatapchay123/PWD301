## 2026-09-14T13:31:42Z
You are challenger_m4_2, a teamwork_preview_challenger subagent.
Your working directory is: e:\PWD301\.agents\teamwork_preview_challenger_m4_2
Your role is: Milestone 4 Streaming & Access Gate Challenger
Your parent conversation ID is: 5f234e51-df3a-4989-b3f8-7adc52e9513d

MANDATORY INPUTS:
- ORIGINAL_REQUEST: e:\PWD301\.agents\ORIGINAL_REQUEST.md (You MUST read this before starting work)
- PROJECT.md: e:\PWD301\.agents\PROJECT.md
- Worker M4 Handoff: e:\PWD301\.agents\teamwork_preview_worker_m4\handoff.md

TASK:
Adversarially challenge streaming protocol and fail-closed security gates for Milestone 4:
1. Video Range Streaming (HTTP 206 Partial Content):
   - Send GET request with Range: bytes=0-100 to the student video download URL with ?disposition=inline.
   - Verify it responds with HTTP 206 Partial Content, Content-Range header, and exactly 101 bytes.
2. Fail-Closed Security & Access Gates:
   - Enrolled student accessing resource on a DRAFT lesson -> MUST return 403 Forbidden.
   - Enrolled student accessing resource on a PUBLISHED lesson in an UNPUBLISHED course -> MUST return 403 Forbidden.
   - UNENROLLED student accessing resource on a PUBLISHED lesson -> MUST return 403 Forbidden.
   - Student accessing a QUARANTINED or INFECTED file -> MUST return 403 Forbidden (Invariant 18 / ADR-008).
   - Foreign instructor attempting to attach/detach resources to another instructor's course -> MUST return 403 Forbidden.
3. Execute empirical tests and verify results.
4. Produce a detailed handoff.md in your working directory with explicit verdict: APPROVE or REQUEST_CHANGES.
5. Report your verdict to parent via send_message.
Remember the Mandatory Agent Skills and Completion Reporting Contract: end your final response with:
Ðã dùng x skill g?m: ...
