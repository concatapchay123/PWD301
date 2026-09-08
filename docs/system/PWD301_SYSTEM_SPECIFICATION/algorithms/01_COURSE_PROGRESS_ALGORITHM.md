# Course Progress Algorithm

**Source of truth:** `lesson_progress` plus required Assessment results/completion rules. `enrollments.current_progress_percent` is a recomputable cache.

1. Load current EnrollmentPeriod and Course completion rule.
2. Build required-learning baseline for that period. Lessons added later to an existing period are optional Xem thêm and do not reduce preserved progress/completed status.
3. Count required Lesson completions and required Assessment pass/completion conditions.
4. Compute bounded 0..100 percent according to configured weights/rule.
5. Never unset an already durable Course completion because lessons/rules later become stricter.
6. Update cache with rowversion; durable `course_completion_summaries` records prior completion.
