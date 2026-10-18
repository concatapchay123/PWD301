# Coverage Analysis — Iteration 08: Multi-Step Business Workflows: Course Lifecycle & Staging Drafts

## 1. Endpoints & Operations Covered

| Method | Endpoint | Subsystem / Role | Coverage Type | Verified Invariant |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/instructor/courses` | Instructor API | Functional & Boundary | Initial DRAFT course creation |
| `GET` | `/instructor/courses/<id>/publish-checklist` | Instructor API | Business Invariant | 5-criteria readiness calculation |
| `POST` | `/instructor/courses/<id>/files` | File Storage | Functional & Security | Authentic 16:9 PNG upload (`COURSE_IMAGE`) |
| `PUT` | `/instructor/courses/<id>` | Instructor API | Functional & Boundary | Metadata, SLOs, and cover asset binding |
| `POST` | `/instructor/courses/<id>/completion-rules` | Course Service | Business Invariant | Academic rule configuration (>= 50%) |
| `POST` | `/instructor/courses/<id>/learning-units` | Curriculum Engine | Functional & Staging | Pre-publish unit and post-publish draft unit |
| `POST` | `/instructor/courses/<id>/lessons` | Lesson Service | Functional & Staging | Lesson authoring with valid markdown |
| `POST` | `/instructor/courses/<id>/submit` | Workflow Engine | Business Invariant | DRAFT -> SUBMITTED_FOR_REVIEW |
| `GET` | `/admin/courses/<id>` | Admin Governance | Contract / Dossier | Full academic inspection dossier |
| `POST` | `/admin/courses/<id>/review` | Admin Governance | Workflow / RBAC | SUBMITTED_FOR_REVIEW -> APPROVED |
| `POST` | `/admin/courses/<id>/publish` | Admin Governance | Workflow / RBAC | APPROVED -> PUBLISHED transition |
| `GET` | `/student/catalog` / `/student/courses/` | Student Catalog | Visual / Discovery | Public catalog publication gate |
| `GET` | `/student/courses/<id>` | Student API | Data Isolation | Zero staging draft leakage |
| `POST` | `/instructor/courses/<id>/changeset/submit`| Staging Draft | Workflow Engine | Submission of staged curriculum changes |
| `GET` | `/admin/courses/<id>/changeset/diff` | Admin Governance | Inspection / Diff | Deep 5-category Before vs After diff |
| `POST` | `/admin/courses/<id>/changeset/approve`| Admin Governance | Atomic Review | Atomic all-or-nothing merge & review identity |

---

## 2. Browser Routes & UI Views Covered

- `#/instructor/dashboard`
- `#/instructor/courses/manage?id=...` (Course Studio)
- `#/admin/governance?tab=courses` (Admin Review Queue)
- `#/student/dashboard`
- `#/student/catalog` (Public Course Catalog)
