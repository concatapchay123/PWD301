# Iteration 17: Test Case Specifications

**Domain:** Cross-Module Integration, Cascade Deletions & Notification RBAC  
**Auditor Lead:** AGENT 06 — End-to-End Business Workflow QA  

---

### TC-IT17-001: Cascade Attachment Deletion: Trashing Lesson Purges FileAsset from Document Hub
- **Target Invariant:** Cascade Attachment Deletion & Document Hub Invariant (AGENTS.md).
- **Preconditions:** Instructor session (`instructor1@pwd301.local`), active course with a lesson.
- **Test Steps:**
  1. Upload a document file (e.g. `study_guide.pdf`) and attach to a draft/active lesson via `POST /instructor/courses/<course_id>/lessons/<lesson_id>/resources`.
  2. Verify the attached file is listed in Course Document Hub (`GET /api/courses/<course_id>/files`).
  3. Soft-delete the lesson via `DELETE /instructor/courses/<course_id>/lessons/<lesson_id>` or `POST /instructor/courses/<course_id>/lessons/<lesson_id>/delete`.
  4. Query Course Document Hub (`GET /api/courses/<course_id>/files`) again.
  5. Inspect SQL Server: Verify `LessonResource` entry is removed and `FileAsset.status == 'TRASH'`.
- **Pass Criteria:** File asset is removed from Course Document list immediately upon lesson deletion, and SQL Server `FileAsset.status` is updated to `'TRASH'`.

---

### TC-IT17-002: Cascade LearningUnit Deletion & Curriculum Consistency
- **Target Invariant:** LearningUnit Deletion Lifecycle & Orphan Prevention.
- **Preconditions:** Instructor session on draft course.
- **Test Steps:**
  1. Create a LearningUnit via `POST /instructor/courses/<course_id>/learning-units`.
  2. Create a Lesson assigned to this LearningUnit.
  3. Delete the LearningUnit via `DELETE /instructor/learning-units/<unit_id>`.
  4. Verify the LearningUnit is soft-deleted (`deleted_at IS NOT NULL`).
  5. Verify the course curriculum remains valid without database constraint crashes.
- **Pass Criteria:** LearningUnit successfully soft-deleted; zero foreign key violations or database integrity errors.

---

### TC-IT17-003: Course Document Tree Hierarchy Verification
- **Target Invariant:** Course Document Tree consistency between Instructor and Student views.
- **Preconditions:** Authenticated student view of an enrolled course.
- **Test Steps:**
  1. Query `GET /api/courses/<course_id>/files` as Student.
  2. Verify response includes file metadata (`display_name`, `file_size`, `mime_type`, `asset_id`, `download_url`).
  3. Assert no trashed or un-scanned files are exposed.
- **Pass Criteria:** Valid clean JSON list of active course documents, matching authorized files.

---

### TC-IT17-004: Two-Tier Broadcast Notification RBAC Enforcement
- **Target Invariant:** Two-Tier Broadcast Notification RBAC (AGENTS.md).
- **Preconditions:** Three authenticated admin contexts:
  - Primary Admin (`admin@pwd301.local`, `ADMIN_PRIMARY`)
  - System Monitoring Admin (`admin.monitor@pwd301.local`, `ADMIN_SYSTEM_MONITORING`)
  - Course Review Admin (`admin.course1@pwd301.local`, `ADMIN_COURSE_REVIEW`)
- **Test Steps:**
  1. **Primary Admin** posts broadcast with category `MAINTENANCE`: Assert HTTP 200 OK.
  2. **System Monitoring Admin** posts broadcast with category `MAINTENANCE`: Assert HTTP 403 Forbidden with exact message *"Admin giám sát hệ thống chỉ được phép phát thông báo liên quan đến hệ thống."*
  3. **System Monitoring Admin** posts broadcast with category `SYSTEM`: Assert HTTP 200 OK.
  4. **Course Review Admin** posts broadcast with category `SYSTEM`: Assert HTTP 403 Forbidden with message *"Bạn không có quyền phát thông báo toàn hệ thống."*
- **Pass Criteria:** 100% adherence to 2-tier broadcast authorization matrix across all tested categories and sub-roles.

---

### TC-IT17-005: Event-Driven Notification Delivery into Student Inbox Feed
- **Target Invariant:** Cross-Role Notification Delivery Lifecycle.
- **Preconditions:** Student session (`student1@pwd301.local`), Primary Admin session.
- **Test Steps:**
  1. Primary Admin broadcasts a targeted notification for role `STUDENT`: Title = `"THÔNG BÁO KIỂM THỬ IT17"`.
  2. Student fetches notifications: `GET /auth/notifications`.
  3. Search the student's notifications list for the broadcasted title.
  4. Assert the notification exists with unread status (`is_read == False` or `read == False`).
- **Pass Criteria:** Broadcasted notification delivered to student feed with full metadata and unread state.

---

### TC-IT17-006: Notification Read State & Unread Counter Synchronization
- **Target Invariant:** Realtime Inbox State & Unread Badge Accuracy.
- **Preconditions:** Student with an unread notification from TC-IT17-005.
- **Test Steps:**
  1. Fetch initial unread count: `GET /auth/notifications/unread-count`.
  2. Mark the test notification as read: `POST /auth/notifications/<notification_id>/read`.
  3. Fetch updated unread count: `GET /auth/notifications/unread-count`.
  4. Assert unread count decremented by 1.
  5. Fetch notifications list: Verify notification has `read: True` / `is_read: True`.
- **Pass Criteria:** Synchronous decrement of unread count, notification marked as read in database and response envelope.
