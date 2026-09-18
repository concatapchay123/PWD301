## 2026-09-14T05:35:43+07:00
Investigate codebase and specifications for R2: Deep Instructor Course Customization & Dynamic Student View:
- Learning objectives & skills gained (Mục tiêu và kỹ năng).
- Target audience & completion requirements (Mô tả và yêu cầu môn học).
- Course prerequisites (Điều kiện tiên quyết) with cycle prevention, using course_prerequisites schema.
- Curriculum & syllabus structure (Đề cương chương trình đào tạo).
- Dynamic rendering in student course detail page (student/course_detail.html) eliminating all hardcoded placeholder text.
Authoritative sources:
- docs/system/PWD301_SYSTEM_SPECIFICATION/ (04_COURSE_AND_LESSON_LIFECYCLE.md, 01_BUSINESS_RULE_CATALOG.md, 05_DATA_DICTIONARY_COURSE.md).
- docs/database/PWD301_DATABASE_ARCHITECTURE/ (courses, course_prerequisites, course_sections, lessons tables).
- frontend-preview/ (frontend-preview/views/student_course_detail.html and components.js).
- src/pwd301/models/course.py, enrollment.py.
- src/pwd301/services/course_service.py, enrollment_service.py.
- src/pwd301/blueprints/instructor/routes.py, student/routes.py.
- src/pwd301/templates/instructor/course_settings.html, student/course_detail.html.
- tests/ (tests/test_courses.py, tests/test_enrollments.py).
