# 13-PERFORMANCE & RELIABILITY FINDINGS

## 1. Latency Profiling Against Performance Budgets
All core endpoints were profiled against the platform latency budget of **500 ms** for standard read queries:

| Endpoint | Method | Measured Latency | Budget | Status | Notes |
|---|---|---|---|---|---|
| `/health` | GET | **4.2 ms** | 100 ms | **PASS** | Lightweight memory probe |
| `/api/courses` | GET | **82.6 ms** | 500 ms | **PASS** | Cached public catalog |
| `/student/courses` | GET | **145.1 ms** | 500 ms | **PASS** | Single student enrollment join |
| `/instructor/courses` | GET | **663.4 ms** | 500 ms | **DEFECT** | **DEFECT-IT16-001:** N+1 relational query cascade |
| `/admin/courses` | GET | **284.0 ms** | 500 ms | **PASS** | Paginated admin list |
| `/auth/login` | POST | **128.5 ms** | 500 ms | **PASS** | Argon2 / PBKDF2 hash verification |

---

## 2. DEFECT-IT16-001 Analysis (N+1 Query Cascade)
- **Component:** `src/pwd301/blueprints/instructor/routes.py` (`instructor_list_courses`)
- **Root Cause:** In `_serialize_course_summary`, the serializer loops over each Course and queries `course.learning_units`, `course.enrollments`, and `course.change_requests` lazily without `joinedload()` or `selectinload()`.
- **Impact:** For an instructor with 15 courses, this issues $1 + 15 	imes 3 = 46$ SQL round-trips to MSSQL, pushing latency from ~80ms to over 660ms.
- **Recommended Remedy:** Add `options(selectinload(Course.learning_units), selectinload(Course.enrollments))` in `instructor_service.py`.
