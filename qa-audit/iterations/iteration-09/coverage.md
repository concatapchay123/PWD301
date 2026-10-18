# Coverage Analysis — Iteration 09: File Uploads, ClamAV Fail-Closed Scanning & YouTube 16:9 Player

## 1. Endpoints & Operations Covered

| Method | Endpoint | Subsystem / Role | Coverage Type | Verified Invariant |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/instructor/courses/<id>/files` | File Storage API | Boundary & Security | 50MB non-archive policy & EICAR malware block |
| `POST` | `/instructor/courses/<id>/lessons/<id>/resources` | Curriculum Engine | Functional | Attachment of clean PDF document |
| `GET` | `/student/files/<id>/download` | Student Download | Fail-Closed & Auth | Clean download allowed; quarantined denied |
| `POST` | `/student/courses/<id>/enroll` | Student Enrollment | Workflow | Student course enrollment |
| `GET` | `/student/courses/detail` | Course Console | Frontend E2E | Lesson video rendering & document list |
| `GET` | `/student/courses/<id>/lessons/<id>` | Lesson API | Contract | Multi-tier video URL resolution |

---

## 2. Browser Routes & UI Views Covered

- `#/instructor/courses/manage?id=...` (Course Studio file upload)
- `#/student/dashboard`
- `#/student/courses/detail?id=...&lesson_id=...` (Student Learning View with 16:9 Player)
