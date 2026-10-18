# Iteration 12: Defect Report

**Iteration:** 12  
**Domain:** Boundary Values, Negative Tests, Invalid States & Prerequisite Cycles  
**Defects Discovered:** 0  
**Status:** ALL TESTS PASSED  

---

## 1. Summary of Defect Discovery

During Iteration 12, comprehensive negative, boundary, and invalid state scenarios were executed against the PWD301 REST API and real Chrome SPA. All boundary conditions, DAG cycles, leasing invariants, and state machine transitions operated fail-closed:

1. **DAG Cycle Defense (Algorithm 03):** Both direct circular dependencies ($A \rightarrow B \rightarrow A$) and reflexive self-dependencies ($A \rightarrow A$) were rejected with proper HTTP 409 / 400 envelopes and descriptive Vietnamese error messages. Zero invalid relationships entered SQL Server `CoursePrerequisite`.
2. **Leasing Invariants (Algorithm 07):** Both expired leases and corrupted/tampered lease tokens were rejected with HTTP 409 Conflict. Browser-side takeovers correctly increment `lease_epoch` and fence out stale writes.
3. **Client Sequencing:** Out-of-order/stale client sequences ($5 \le 10$) were rejected with HTTP 409 `STALE_ANSWER` and correctly persisted as audit rejection events in `attempt_answer_events`.
4. **State Machine Integrity:** Illegal direct status transitions ($DRAFT \rightarrow PUBLISHED$) were blocked with HTTP 409 `STATE_VIOLATION`.
5. **Boundary Defense:** Out-of-bounds percentages ($> 100\%$), negative grades ($< 0$), negative capacities ($\le 0$), and oversized titles ($> 200$ chars) were blocked with HTTP 400 Bad Request.

---

## 2. Active Defect Registry Status

| Defect ID | Title | Severity | Invariant Affected | Status |
|---|---|---|---|---|
| **DEFECT-IT10-001** | Unhandled `ZeroDivisionError` in `verify_assessment_result_integrity` on zero-point exams | High (P1) | Algorithm 08 / Assessment Result Integrity | **OPEN** |

*No new defects were identified in Iteration 12.*
