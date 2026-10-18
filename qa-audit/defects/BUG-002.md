# DEFECT-IT16-001: Instructor Courses Endpoint Latency Exceeds 500ms Baseline Due to Unoptimized N+1 Queries in Serialization

- **Defect ID:** DEFECT-IT16-001  
- **Discovered In:** Iteration 16 (TC-IT16-001)  
- **Component:** Backend REST API (`src/pwd301/blueprints/instructor/routes.py`) / Instructor Course Management  
- **Severity:** Medium (P2)  
- **Category:** Performance / N+1 Query & Serialization Latency  
- **Status:** OPEN  

---

## 1. Description
During Iteration 16 Performance Baseline benchmarking (TC-IT16-001), `GET /instructor/courses` consistently exhibited an average response latency of **728.2ms** (min: 696.9ms, max: 802.2ms), significantly exceeding the system quality gate threshold of **$\le 500\text{ms}$**. In contrast, all student and administrative endpoints completed in 9ms to 57ms (e.g. `/auth/profile`: 9.5ms, `/api/courses`: 55.1ms, `/admin/health`: 16.5ms).

Empirical trace profiling revealed that the bottleneck occurs inside `my_courses()` in `src/pwd301/blueprints/instructor/routes.py`:
```python
courses = assigned_query.order_by(Course.created_at.desc()).all()
serialized = [_serialize_course(c, summary=True) for c in courses]
```
For every course returned by `assigned_query`, `_serialize_course(c, summary=True)` triggers a cascade of individual un-eager-loaded queries:
1. `effective_course(c, actor, db.session)`: executes a query against `course_version_changesets`.
2. `get_course_thumbnail_asset(c)`: executes a query against `file_assets`.
3. `c.lessons`: lazy-loads all lessons associated with the course.
4. `c.owner_instructor`: lazy-loads user record.
5. `c.enrollments`: lazy-loads all enrollment records.
6. `getattr(e.student, "status", None)`: lazy-loads the `User` record for *every* individual student enrollment.
7. `course_requires_review(c)`: re-queries `course_version_changesets`.
8. `course_review_version(original_course, db.session)`: queries course version tables.

When an instructor manages multiple courses with enrollments and lessons, this loop results in 40–80 sequential round-trip queries over the SQL Server connection pool, multiplying latency by $10\times$ compared to standard endpoints.

---

## 2. Reproduction Steps
1. Authenticate as an Instructor (`instructor1@pwd301.local`).
2. Dispatch a `GET` request to `/instructor/courses` over HTTP.
3. Record high-resolution elapsed time:
   ```python
   t0 = time.perf_counter()
   res = session.get("http://localhost:5000/instructor/courses")
   latency = (time.perf_counter() - t0) * 1000
   print(f"Status: {res.status_code}, Latency: {latency:.1f}ms")
   ```
4. Observe that response latency measures between **696ms and 802ms** across 5 consecutive warmed-up invocations.

---

## 3. Empirical Evidence
- **Benchmark Run ID:** `B6E2CA`
- **Sample Metrics (5 Iterations):**
  - Sample 1: 721.4ms
  - Sample 2: 708.9ms
  - Sample 3: 696.9ms
  - Sample 4: 711.7ms
  - Sample 5: 802.2ms
  - **Arithmetic Mean:** $728.22\text{ms}$
- **Budget Threshold:** $\le 500.0\text{ms}$
- **Delta:** $+228.22\text{ms}$ ($+45.6\%$ over budget).
- **Screenshot Evidence:** `qa-audit/iterations/iteration-16/evidence/IT16_TC01_API_Response_Latency.png`

---

## 4. Root Cause Analysis
SQLAlchemy query execution in `my_courses` does not apply eager-loading (`joinedload`, `selectinload`, or `subqueryload`) for course relationships (`lessons`, `enrollments`, `enrollments.student`, `owner_instructor`, `thumbnail_asset`). 

Furthermore, `_serialize_course(c, summary=True)` is shared between single-course detail endpoints and multi-course listing endpoints. In a listing context with `summary=True`, full enrollment-by-enrollment student status inspection (`getattr(e.student, "status", None)`) should be replaced by a single aggregated SQL count (`SELECT course_id, COUNT(*) FROM enrollments WHERE status = 'ACTIVE' GROUP BY course_id`), eliminating $O(N \times M)$ queries.

---

## 5. Recommended Remediation
1. **Aggregated Enrollment Count:** Instead of iterating through `c.enrollments` and lazy-loading `e.student`, compute active enrollment counts in a single batch query:
   ```python
   counts = db.session.query(
       Enrollment.course_id, func.count(Enrollment.id)
   ).filter(
       Enrollment.course_id.in_([c.id for c in courses]),
       Enrollment.status == "ACTIVE"
   ).group_by(Enrollment.course_id).all()
   enrollment_map = dict(counts)
   ```
2. **Eager Loading on `assigned_query`:**
   ```python
   assigned_query = db.session.query(Course).options(
       selectinload(Course.lessons),
       joinedload(Course.owner_instructor)
   ).filter(...)
   ```
3. **Dedicated Lightweight Summary Serializer:** For listing views, avoid invoking `effective_course` and `course_review_version` unless staging draft flags are explicitly requested by query parameters.
