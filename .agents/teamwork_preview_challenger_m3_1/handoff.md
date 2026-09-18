# Handoff Report -- Milestone 3 Invariant Challenger (Invariants 13 & 14)

## 1. Observation
- **Scope & Mandate**:
  - Subagent: challenger_m3_1 (role: Milestone 3 Invariant Challenger).
  - Target Invariants:
    - Invariant 13 (Timing Lock -- BR-031): Assessment timing is server-authoritative and locked after publish.
    - Invariant 14 (Structural Freeze -- BR-030): Assessment question structure and assigned points are locked after first student start.
- **Observed Code Implementation**:
  - src/pwd301/services/assessment_service.py:665-707:
    - is_published = assessment.status == 'PUBLISHED' or assessment.published_at is not None
    - Mutating open_at, time_limit_minutes (or duration_minutes), attempt_limit (or max_attempts) raises AssessmentLockedError.
    - Shortening or maintaining close_at <= cur_close raises AssessmentLockedError.
    - Extending close_at > cur_close forward into future succeeds.
  - src/pwd301/services/assessment_service.py:648-662, 1220, 1275, 1323, 1432, 1491:
    - If assessment.first_attempt_started_at is not None:
      - Mutating assessment_type or random_question_count raises AssessmentLockedError.
      - create_section() and delete_section() raise AssessmentLockedError.
      - assign_question() raises AssessmentLockedError.
      - remove_question_assignment() raises AssessmentLockedError.
      - update_question_assignment() raises AssessmentLockedError.
  - src/pwd301/blueprints/instructor/routes.py:
    - line 1683: POST /assessments/<assessment_id>/questions/create:
      - Direct check if asm_obj.first_attempt_started_at is not None: raise AssessmentLockedError(...). Precedes payload parsing.
    - line 1872: POST /assessments/<assessment_id>/questions/<question_id>/edit:
      - Direct check if asm_obj.first_attempt_started_at is not None: raise AssessmentLockedError(...).
    - line 1650: POST /assessments/<assessment_id>/questions/<question_id>/remove & DELETE:
      - Calls remove_question_assignment(), catches and raises AssessmentLockedError.
    - line 2064: POST /assessments/<assessment_id>/import:
      - Direct check if asm_obj.first_attempt_started_at is not None: raise AssessmentLockedError(...).
  - src/pwd301/services/import_service.py:921-925:
    - In create_import_job(), validates if target_assessment.first_attempt_started_at is not None: raise AssessmentLockedError(...).
  - src/pwd301/__init__.py:310:
    - AssessmentLockedError: ('CONFLICT', 409) converts exception to HTTP 409 Conflict.
- **Empirical Execution Commands & Verbatim Results**:
  1. Adversarial Test Suite Execution:
     - Command: .venv/Scripts/python.exe -m pytest tests/test_m3_challenger_stress.py -v
     - Result: 14 passed in 4.36s (100% pass rate across 14 dedicated adversarial stress tests).
  2. Worker Integration Test Suite Execution:
     - Command: .venv/Scripts/python.exe -m pytest tests/test_m3_assessment_authoring.py -v
     - Result: 10 passed in 2.36s (100% pass rate).
  3. Regression Unit & API Assessment Suites Execution:
     - Command: .venv/Scripts/python.exe -m pytest tests/unit/test_assessment_service.py tests/api/test_assessment_api.py -v
     - Result: 20 passed in 5.52s (100% pass rate).
  4. Repository & Lint Checks:
     - Command: .venv/Scripts/python.exe scripts/repo_check.py
     - Result: Repository contract check complete (all checks passed).
     - Command: .venv/Scripts/python.exe -m ruff check src tests scripts
     - Result: All checks passed!
     - Command: .venv/Scripts/python.exe -m ruff format --check src tests scripts
     - Result: 218 files already formatted.
     - Command: .venv/Scripts/python.exe -m mypy src/pwd301
     - Result: Success: no issues found in 85 source files.

## 2. Logic Chain
1. **Invariant 13 (Timing Lock -- BR-031)**:
   - Observation: When an assessment is in DRAFT status, update_assessment() permits updating open_at, close_at, time_limit_minutes, and attempt_limit (	est_invariant_13_pre_publish_timing_mutations_allowed).
   - Observation: Once published (status == 'PUBLISHED'), attempting to modify open_at, time_limit_minutes, or attempt_limit via Web UI JSON or REST API PATCH returns HTTP 409 Conflict (	est_invariant_13_web_route_timing_lock_rejections, 	est_invariant_13_api_timing_lock_rejections_and_aliases).
   - Observation: Service-level parameter aliases (duration_minutes, max_attempts) are equally intercepted and raise AssessmentLockedError.
   - Observation: close_at forward extension into the future is permitted via Web and REST API (HTTP 200 OK), whereas shortening close_at backward is rejected with HTTP 409 Conflict (	est_invariant_13_close_at_forward_allowed_and_shorten_rejected).
   - Observation: Submitting unchanged timestamps during title updates does not trigger false positive locking (	est_invariant_13_identical_timestamp_resubmission_allowed).
   - Inference: Invariant 13 is fully enforced across all client contexts (Web UI, REST API, direct service).
2. **Invariant 14 (Structural Freeze -- BR-030)**:
   - Observation: Once a student starts an attempt (first_attempt_started_at is set), calling POST /instructor/assessments/<id>/questions/create returns HTTP 409 Conflict across all 4 question types: SINGLE_CHOICE, MULTIPLE_CHOICE, TRUE_FALSE, SHORT_ANSWER, as well as form-encoded data (	est_invariant_14_direct_authoring_all_types_rejected_post_attempt).
   - Observation: Direct in-place editing via POST /instructor/assessments/<id>/questions/<qid>/edit returns HTTP 409 Conflict across prompt content, points (JSON & Form), choices, accepted answers, and explanations, leaving underlying database values untouched (	est_invariant_14_in_place_question_editing_rejected_post_attempt).
   - Observation: Question removal via POST /remove and DELETE returns HTTP 409 Conflict (	est_invariant_14_question_removal_rejected_post_attempt).
   - Observation: Document import via POST /instructor/assessments/<id>/import returns HTTP 409 Conflict for both DOCX and PDF uploads, and import_service.create_import_job() raises AssessmentLockedError (	est_invariant_14_document_import_rejected_post_attempt).
   - Observation: Direct service mutations (assign_question, update_question_assignment, remove_question_assignment, create_section, delete_section, update_assessment for type or random count) all raise AssessmentLockedError (	est_invariant_14_service_level_structural_freezes).
   - Observation: REST API question routes (POST /api/assessments/<id>/questions, PATCH, DELETE) return HTTP 409 Conflict (	est_invariant_14_rest_api_structural_freeze).
   - Observation: Invariant 14 check precedes payload validation, ensuring that even intentionally malformed payloads trigger HTTP 409 Conflict rather than 400 Bad Request (	est_invariant_14_freeze_precedence_over_invalid_payload).
   - Observation: The freeze persists permanently after student attempts finish/submit (	est_invariant_14_freeze_permanence_after_attempt_completion).
   - Observation: Course manager isolation prevents unauthorized access (	est_invariant_authorization_and_isolation).
   - Inference: Invariant 14 is fully enforced at both the endpoint and service layers.

## 3. Caveats
- Cross-Subsystem Finding:
  - Base ValidationError from pwd301.services.exceptions was observed to not be registered in src/pwd301/__init__.py:EXCEPTION_STATUS_MAP. As a result, when peer tests submit malformed inputs to general endpoints, Flask raises unhandled 500 errors instead of 400 Bad Request.
  - This does NOT impact Invariant 13 or 14, as AssessmentLockedError is properly registered as ('CONFLICT', 409). This finding is noted for the auditor and worker.

## 4. Conclusion
- **Verdict: APPROVE**.
- Invariant 13 (Timing Lock -- BR-031) and Invariant 14 (Structural Freeze -- BR-030) are completely, correctly, and robustly enforced.
- All 14 dedicated adversarial stress tests in 	ests/test_m3_challenger_stress.py pass cleanly.
- Worker integration tests (10/10) and regression unit/API tests (20/20) pass with zero regressions.

## 5. Verification Method
- **Run Challenger Stress Suite**:
  `powershell
  .venv/Scripts/python.exe -m pytest tests/test_m3_challenger_stress.py -v
  `
- **Run Worker Integration Suite**:
  `powershell
  .venv/Scripts/python.exe -m pytest tests/test_m3_assessment_authoring.py -v
  `
- **Run Regressions**:
  `powershell
  .venv/Scripts/python.exe -m pytest tests/unit/test_assessment_service.py tests/api/test_assessment_api.py -v
  `
- **Run Static Checks**:
  `powershell
  .venv/Scripts/python.exe scripts/repo_check.py
  .venv/Scripts/python.exe -m ruff check src tests scripts
  .venv/Scripts/python.exe -m ruff format --check src tests scripts
  .venv/Scripts/python.exe -m mypy src/pwd301
  `
