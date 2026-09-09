# TASK-016 — Assessment Grading Engine & Manual Essay Evaluation

**Status:** DONE  
**Assignee:** Principal Software Architect & Lead Fullstack Python/Flask Engineer  
**Depends on:** TASK-015  

---

## 1. Goal / Problem Statement
Implement the complete Assessment Grading Engine & Manual Essay Evaluation workflow in strict compliance with **Algorithm 10 (Grading Algorithm)**, **Business Domain 10 (Grading & Regrading)**, **Attempt API Specification**, **ADR-002 (Internal BIGINT Masking)**, and canonical database constraints:
1. **Objective Auto-Grading Engine**:
   - `SINGLE_CHOICE`: Exactly 1 selected choice matching `is_correct == True` awards 100% `points_assigned`; incorrect or unselected awards 0.
   - `TRUE_FALSE`: Exactly 1 selected choice matching `is_correct == True` awards 100% `points_assigned`; incorrect or unselected awards 0.
   - `MULTIPLE_CHOICE`: All-or-nothing exact set equality (`selected_choice_keys == correct_choice_keys`). Partial match or extraneous wrong choices award 0.
   - `SHORT_ANSWER`: Case-insensitive and whitespace-normalized matching against `QuestionRevisionAcceptedAnswer` entries via Unicode NFKC normalization. Correct awards 100% `points_assigned`; non-matching awards 0.
2. **Attempt Lifecycle Status Transitions**:
   - **Pure Objective Assessments**: Submitting an attempt automatically grades all questions, transitions attempt status immediately to `GRADED` with `graded_at = utc_now()`, and computes `AssessmentResult` (`FINAL` or `RELEASED` based on score release policy).
   - **Mixed / Essay Assessments**: Submitting an attempt evaluates objective questions immediately (`AUTO_GRADED`), marks essay questions as `PENDING` (`awarded_points = 0`, `grading_rule = 'MANUAL'`), transitions attempt to `PENDING_GRADING`, and creates `AssessmentResult` with `status = 'PENDING'`.
3. **Manual Essay Evaluation Workflow**:
   - Instructor/admin grading endpoints (`POST /instructor/attempts/<id>/grades/<qid>` and `POST /api/attempts/<id>/grades/<qid>`).
   - Strict score bounds check: $0 \le \text{awarded\_points} \le \text{points\_assigned}$ (raises `MaxPointsExceededError` on breach).
   - Attempt state check: grading an in-progress attempt raises 409 `AttemptNotSubmittedError`.
   - Audit trail: appends `AttemptQuestionGradeHistory` with `reason_code = 'MANUAL_REVISION'` (satisfying DDL constraint `ck_attempt_question_grade_history_2`).
   - Auto-finalization: when the last pending essay question is graded, the attempt automatically finalizes to `GRADED` with `graded_at = utc_now()`, and `AssessmentResult` is recalculated to `FINAL` or `RELEASED`.
4. **Aggregate Result & Policies**:
   - `AssessmentResult`: aggregates `raw_score`, `max_score`, `percent_score = (raw_score / max_score) * 100`, and `passed = percent_score >= passing_percent`.
   - Score release policies: `IMMEDIATE`, `AFTER_CLOSE`, and `INSTRUCTOR_RELEASE` (scores hidden with `score_status: "SCORE_HIDDEN"` until released).
   - Instructor score release endpoint: `POST /api/assessments/<id>/release-scores` transitions results from `FINAL` to `RELEASED` and records append-only `AuditEvent`.
   - Answer visibility policies: `IMMEDIATE`, `AFTER_CLOSE`, `AFTER_ALL_ATTEMPTS`, and `NEVER` (hiding question explanations and choice feedback).
5. **Course Completion Engine Integration**:
   - Recalculates course completion (`recalculate_course_completion`) when a student passes an assessment marked with `is_required_for_completion == True` (Criterion 3).
6. **ADR-002 BigInt Masking & Zero-Trust IDOR**:
   - Zero internal database integer PKs/FKs disclosed in JSON responses across all grading and result endpoints. UUIDv4 public identifiers only.
   - Enforce fail-closed authorization: peer students cannot view each other's results (403), non-course instructors cannot view or grade attempts (403), students cannot grade essays (403).

---

## 2. Key Architecture Decisions & Invariants
- **Direct Query Persistence Guarantee**:
  Because answers and grades can be inserted/updated across distinct service functions or sub-transactions, in-memory relationship caches (e.g. `aq.current_answer`, `aq.current_grade`) can lag. The grading engine resolves child entities through direct session queries (`sess.query(AttemptQuestionGrade).filter(...)`) ensuring 100% persistence fidelity.
- **Strict Database Constraint Adherence**:
  - `AttemptQuestionGradeHistory.reason_code`: Canonical check constraint `ck_attempt_question_grade_history_2` mandates `('INITIAL', 'AUTO_REGRADE', 'FULL_CREDIT', 'MANUAL_REVISION')`. The manual essay service records `'MANUAL_REVISION'`.
  - `AssessmentResultHistory.reason_code`: Canonical check constraint `ck_assessment_result_history_2` mandates `('INITIAL', 'REGRADE', 'MANUAL', 'CORRECTION')`. Manual essay grading transitions record `'MANUAL'`.
- **Course Completion Recalculation**:
  Completing a required assessment triggers `recalculate_course_completion(student_user_id, course_id, session=sess)`. Criterion 3 checks that every published, non-deleted assessment with `is_required_for_completion == True` has at least one passed `GRADED` attempt.
- **ADR-002 Masking Across All Entities**:
  Every dictionary returned by `_serialize_attempt_grade` and `_serialize_assessment_result` uses public UUIDv4 identifiers (`attempt_id`, `assessment_id`, `attempt_question_id`) and omits internal integer primary keys.

---

## 3. Files Changed / Created
- `src/pwd301/services/exceptions.py`:
  - Added `GradingError(ServiceError)`
  - Added `ScoreReleasePolicyError(ForbiddenError, GradingError)` (HTTP 403)
  - Added `MaxPointsExceededError(ValidationError, GradingError)` (HTTP 400)
  - Added `AttemptNotSubmittedError(StateViolationError, GradingError)` (HTTP 409)
  - Added `AttemptNotSubmitedError = AttemptNotSubmittedError` (alias)
- `src/pwd301/__init__.py`:
  - Registered centralized Flask exception handlers for `MaxPointsExceededError`, `GradingError`, `AttemptNotSubmittedError`, and `ScoreReleasePolicyError`.
- `src/pwd301/services/completion_service.py`:
  - Implemented Criterion 3 (`require_required_assessments`) in `evaluate_course_completion`.
  - Implemented `recalculate_course_completion(student_user_id, course_id, session=None)`.
- `src/pwd301/services/assessment_service.py`:
  - Added `release_assessment_scores(actor, assessment_id, session=None)`.
  - Added support for `passing_score` as alias for `passing_percent`.
- `src/pwd301/services/attempt_service.py`:
  - Implemented `grade_attempt_objective_questions`: objective evaluation for all four types, essay pending status, and status transitions.
  - Implemented `calculate_attempt_result`: score aggregation, passing check, score release policy check, and `AssessmentResultHistory` tracking.
  - Implemented `grade_essay_question`: instructor essay evaluation, bounds check, audit history, and attempt auto-finalization.
  - Implemented `get_attempt_result_for_student`: score release masking (`SCORE_HIDDEN`) and answer visibility masking (`show_answers`).
  - Implemented `list_pending_grading_attempts` and `get_attempt_grading_detail` for instructors.
- `src/pwd301/blueprints/api_assessments/routes.py`:
  - Added `POST /api/assessments/<assessment_id>/release-scores`.
- `src/pwd301/blueprints/api_attempts/routes.py`:
  - Added `GET /api/attempts/<attempt_id>/result`.
  - Added `POST /api/attempts/<attempt_id>/grades/<attempt_question_id>`.
  - Updated `_extract_lease_token` to accept both `X-Attempt-Lease-Token` and `X-Lease-Token`.
- `src/pwd301/blueprints/instructor/routes.py`:
  - Added `GET /instructor/assessments/<assessment_id>/grading/pending`.
  - Added `GET /instructor/attempts/<attempt_id>/grading`.
  - Added `POST /instructor/attempts/<attempt_id>/grades/<attempt_question_id>`.
- `src/pwd301/services/__init__.py`:
  - Exported new grading exceptions and functions in `__all__`.
- `tests/unit/test_grading_service.py`:
  - 7 unit tests covering single choice, true/false boolean matching, multiple choice exact match, short answer normalization/exact match, mixed attempt pending transition, manual essay bounds/audit history, and course completion recalculation.
- `tests/security/test_grading_idor.py`:
  - 9 security & IDOR negative tests verifying fail-closed Zero-Trust protection (peer student 403, non-owner instructor 403, student grading 403, non-owner score release 403, `AFTER_CLOSE` policy, `INSTRUCTOR_RELEASE` policy, `NEVER` answer visibility, `AFTER_CLOSE` answer visibility, ADR-002 BigInt masking).
- `tests/api/test_grading_api.py`:
  - 5 end-to-end integration tests verifying pure objective flow, mixed essay flow, invalid bounds validation, dual HTML/JSON instructor support, and regrade history audit trail.

---

## 4. Verification Commands & Results

| Verification Gate | Command | Result |
|---|---|---|
| **1. Repository Contract** | `.venv/Scripts/python scripts/repo_check.py` | **PASS** (all 71 DDL tables, markdown fences balanced) |
| **2. Code Linting** | `.venv/Scripts/ruff check <modified_and_new_files>` | **PASS** (0 errors, all imports sorted) |
| **3. Code Formatting** | `.venv/Scripts/ruff format --check <modified_and_new_files>` | **PASS** (all 15 files formatted cleanly) |
| **4. Type Checking** | `.venv/Scripts/mypy src` | **PASS** (Success: no issues found in 58 source files) |
| **5. Task-016 Test Suite** | `.venv/Scripts/pytest tests/unit/test_grading_service.py tests/security/test_grading_idor.py tests/api/test_grading_api.py -v` | **PASS** (21/21 passed in 18.48s) |
| **6. Full Regression Suite** | `.venv/Scripts/python -m pytest` | **PASS** (449/449 passed in 250.41s) |

---

## 5. Security & Invariant Verification Summary
- **Zero-Trust IDOR Protection**: Only enrolled students can access their own attempt results; peers and unauthorized instructors receive 403 Forbidden. Manual grading endpoints are strictly restricted to course managers and system administrators.
- **ADR-002 Compliance**: Verified in `test_adr002_bigint_masking_in_grading_and_results` and across all integration tests that zero internal integer database PKs/FKs (`id`, `student_user_id`, `assessment_id`, etc.) leak in JSON payloads.
- **Score Release Policies**: Student attempts with `AFTER_CLOSE` or `INSTRUCTOR_RELEASE` return `score_status: "SCORE_HIDDEN"` until the respective conditions are satisfied.
- **Audit Logging**: Every manual essay grading operation creates an immutable `AttemptQuestionGradeHistory` record with `reason_code = 'MANUAL_REVISION'`, and instructor score releases create an immutable `AuditEvent`.

---

## 6. Known Limitations & Deferred Work
- **Regrading Engine & Worker**: Automatic regrading of submitted attempts upon question revisions/corrections, regrade job scheduling, and correction rule application are deferred to **TASK-017 (Regrading + Score History)**.

---

## 7. Recommended Next Action
- Proceed to **TASK-017 — Regrading Engine & Score History**:
  - Implement bulk and single-attempt regrading triggered by question corrections (`QuestionCorrection`).
  - Implement background/synchronous `RegradeJob` and `RegradeItem` processing via `regrade_worker.py`.
  - Audit all score modifications in `AssessmentResultHistory` and `AttemptQuestionGradeHistory`.
