# DISPATCH: teamwork_preview_worker_m2_it2

Working Directory: E:\PWD301\.agents\teamwork_preview_worker_m2_it2
Parent: teamwork_preview_orchestrator_6 (ebbe1ae6-5ba3-416c-a025-e0178c543130)
Original Request: E:\PWD301\.agents\ORIGINAL_REQUEST.md
Scope Document: E:\PWD301\.agents\PROJECT.md
Reviewer 1 Report: E:\PWD301\.agents\teamwork_preview_reviewer_m2_6_1\handoff.md
Challenger 2 Report: E:\PWD301\.agents\teamwork_preview_challenger_m2_6_2\handoff.md

## MANDATORY INTEGRITY WARNING
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Objective
Remediate the two critical defects identified by Reviewer 1 and Challenger 2 in Milestone 2:

### 1. `src/pwd301/templates/student/course_detail.html`
- In the hero `<h1>`, ensure the class `course-hero-title` is present:
  `<h1 class="course-hero-title text-2xl lg:text-4xl font-extrabold tracking-tight text-white leading-tight">{{ clean_title }}</h1>`
- Restore Target Audience section rendering `course.target_audience_list` under heading `"Đối tượng tham gia phù hợp:"`.
- Restore Completion Requirements & Completion Rule section rendering `course.completion_requirements` and `course.completion_rule` criteria (threshold percentage `minimum_progress_percent`, `require_all_required_lessons`, `require_required_assessments`).
- Restore fallback text for empty metadata (`"Thông tin chi tiết môn học đang được giảng viên cập nhật."` and `"Sinh viên cần tham gia đầy đủ các bài giảng..."`).
- Inspect `tests/test_m2_course_customization.py` and `tests/test_m2_adversarial_edge_cases.py` to ensure 100% compliance with all assertions.

### 2. `src/pwd301/templates/student/lesson.html`
- Fix lines 84, 202, 207: replace non-existent route `url_for('student.download_lesson_file', ...)` with `url_for('student.download_student_course_file_route', course_id=course.public_id, file_id=resource.file_id)`.
- Fix line 194: change `asset.scan_status` to `asset.virus_scan_status` so clean scan badges render correctly.
- Ensure `tests/api/test_student_templates_stress_challenger.py` passes cleanly.

### 3. `tests/api/test_m2_s5_adversarial_challenger.py`
- Fix import: `from pwd301.models.file_import import LessonResource` (not from `pwd301.models.course`).
- Clean up unused imports and long lines so `.venv\Scripts\python.exe -m ruff check src tests` returns 0 errors.

## Verification Commands
Execute and ensure 100% pass:
```powershell
.venv\Scripts\python.exe -m pytest tests/test_m2_course_customization.py -v
.venv\Scripts\python.exe -m pytest tests/test_m2_adversarial_edge_cases.py -v
.venv\Scripts\python.exe -m pytest tests/api/test_student_templates_stress_challenger.py -v
.venv\Scripts\python.exe -m pytest tests/api/test_student_portal_ui.py -v
.venv\Scripts\python.exe -m pytest tests/api/test_web_ui_flow_fixes.py -v
.venv\Scripts\python.exe -m pytest tests/e2e/test_student_lifecycle_e2e.py -v
.venv\Scripts\python.exe -m ruff check src tests
.venv\Scripts\python.exe scripts/repo_check.py
```

Write your handoff report to `handoff.md` in your working directory and notify parent using `send_message`.
End your response with: `Đã dùng x skill gồm: ...`
