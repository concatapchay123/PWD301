# Iteration 17 Coverage Analysis: Cascade Deletions, File Management & Broadcast RBAC

**Iteration:** 17  
**Coverage Scope:** Cascade Soft-Deletion, Course Document Tree Hierarchy, Two-Tier Notification RBAC, and Read State Synchronization.  

---

## 1. Endpoints & Operations Covered

| Module / Blueprint | Endpoint / Action | Method | Role Exercised | Coverage Status | Verification Type |
|---|---|---|---|---|---|
| `instructor` | `/instructor/courses/<id>/lessons` | `POST` | Instructor | **Covered** | API + DB Persistence |
| `instructor` | `/instructor/courses/<id>/lessons/<id>/resources` | `POST` (Multipart) | Instructor | **Covered** | In-browser FormData Upload |
| `instructor` | `/instructor/courses/<id>/files` | `GET` | Instructor | **Covered** | Document Hub Contract |
| `instructor` | `/instructor/courses/<id>/lessons/<id>/trash` | `POST` | Instructor | **Covered** | Cascade Deletion Verification |
| `instructor` | `/instructor/courses/<id>/learning-units/<id>/trash` | `POST` | Instructor | **Covered** | Soft-deletion Integrity |
| `admin` | `/admin/broadcasts` (MAINTENANCE) | `POST` | Primary Admin | **Covered** | RBAC Authorization (200 OK) |
| `admin` | `/admin/broadcasts` (MAINTENANCE) | `POST` | System Monitoring Admin | **Covered** | RBAC Rejection (403 Forbidden) |
| `admin` | `/admin/broadcasts` (SYSTEM) | `POST` | System Monitoring Admin | **Covered** | RBAC Authorization (200 OK) |
| `admin` | `/admin/broadcasts` (SYSTEM) | `POST` | Course Review Admin | **Covered** | RBAC Rejection (403 Forbidden) |
| `auth` | `/auth/notifications` | `GET` | Student | **Covered** | In-browser Feed Retrieval |
| `auth` | `/auth/notifications/<id>/read` | `POST` | Student | **Covered** | Atomic State Persistence & Count |

---

## 2. Invariant & Database Coverage

- **Cascade Attachment Deletion & Document Hub Invariant:**
  - `LessonResource` $\rightarrow$ `FileAsset` relationship clean detachment confirmed upon `Lesson` soft-delete.
  - Active document list query filters out soft-deleted parent entities.
- **Two-Tier Broadcast RBAC Matrix:**
  - Verified 100% of the sub-admin conditional logic in `src/pwd301/blueprints/admin/routes.py`:
    - `ADMIN_PRIMARY` (full bypass)
    - `ADMIN_SYSTEM_MONITORING` (allowed only for category `SYSTEM`)
    - Sub-admins without broadcast rights (`ADMIN_COURSE_REVIEW`) denied unconditionally.
- **Real Browser Automation:**
  - Executed in real Google Chrome 155 with dual-persisted visual evidence banners (`PASS` / `FAIL`).
