## 2026-09-13T22:55:22Z
You are Worker M1 Iteration 2 (teamwork_preview_worker).
Your working directory: e:\PWD301\.agents\teamwork_preview_worker_m1_it2
Original request file: e:\PWD301\.agents\ORIGINAL_REQUEST.md
Challenger 2 feedback report: e:\PWD301\.agents\teamwork_preview_challenger_m1_2\handoff.md
Previous worker report: e:\PWD301\.agents\teamwork_preview_worker_m1\handoff.md

Your mission: Remediate the 3 specific defects identified by Challenger 2 in Milestone 1:
1. CRITICAL: In `src/pwd301/services/file_service.py` (`rescan_file_asset` and `quarantine_override`):
   When activating a revision (`revision.status = "ACTIVE"`, `revision.is_current = True`), you MUST demote any existing active/current revision on `asset.revisions`:
   ```python
   for rev in asset.revisions:
       if rev.id != revision.id and (rev.is_current or rev.status == "ACTIVE"):
           rev.is_current = False
           rev.status = "REPLACED"
           rev.replaced_at = now
   ```
   This prevents violating unique partial indexes `uq_file_revisions_current` and `ux_file_revisions_active` on multi-revision files!
2. MEDIUM: In `src/pwd301/blueprints/instructor/routes.py` (`rescan_course_file_route`):
   Update line 730 condition from:
   `elif asset.status == "REJECTED":`
   to:
   `elif asset.virus_scan_status == "INFECTED" or asset.status == "REJECTED":`
   so that when malware is detected upon rescan, the instructor receives the danger flash alert rather than an info badge saying PENDING.
3. MEDIUM: In `src/pwd301/services/file_service.py`:
   In `store_file_stream` and `add_file_revision`, when calling `enqueue_background_job`, pass `run_async=False` or ensure `sess.flush()` / commit happens before thread dispatch to avoid `ObjectDeletedError` race conditions with concurrent test sandboxes.
4. Run all test suites to verify fix:
   - `pytest tests/test_m1_challenger_stress.py -v`
   - `pytest tests/test_m1_adversarial.py -v`
   - `pytest tests/test_m1_file_access.py tests/test_files.py -v`
   - `ruff check src/pwd301` and `mypy src/pwd301`
   Ensure 100% of tests pass with 0 errors!

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Apply Mandatory Agent Skills: superpowers (TDD, verification-before-completion), ponytail (minimal change, zero over-engineering), full-output-enforcement.
Document all changes and test outputs in `e:\PWD301\.agents\teamwork_preview_worker_m1_it2\handoff.md`.
Send message to parent when complete.
