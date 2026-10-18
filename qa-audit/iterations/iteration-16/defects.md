# Iteration 16 Defect Report

**Iteration:** 16  
**Defects Discovered:** 1  
**Defects Verified Fixed:** 0  

---

### Defect Details

| Defect ID | Severity | Category | Title | Status |
|---|---|---|---|---|
| **DEFECT-IT16-001** | Medium (P2) | Performance / N+1 Latency | `GET /instructor/courses` response latency ($728.2\text{ms}$) exceeds $500\text{ms}$ budget due to N+1 query serialization | OPEN |

#### Summary & Impact
During TC-IT16-001, `/instructor/courses` required $728.2\text{ms}$ on average across 5 warmed-up runs. Profiling identified cascading lazy-load queries inside `_serialize_course(c, summary=True)` for each course in the list (`c.lessons`, `c.enrollments`, `c.owner_instructor`, `effective_course`, and `course_review_version`). 

Full documentation and remediation steps are recorded in `qa-audit/defects/DEFECT-IT16-001.md`.
