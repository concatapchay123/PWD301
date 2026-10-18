# Iteration 17 Test Plan: Cross-Module Integration, Cascade Deletions & Notification RBAC

**Iteration:** 17  
**Domain:** Cross-Module Integration: Attachment Trashing Cascading to Document Hub, Learning Unit Lifecycles, Event-Driven Notifications & Two-Tier Broadcast RBAC  
**Auditor Lead:** AGENT 06 — End-to-End Business Workflow QA (Assisted by AGENT 04 Database QA & AGENT 05 Security/RBAC QA)  
**Browser Engine:** Real Google Chrome 155 via Playwright (`channel="chrome"`)  
**Backend:** Local Docker container `pwd301_web` (Flask REST API + SQL Server) on `http://localhost:5000`  
**Execution Objective:** Empirically verify cross-module data cascades when deleting lessons and learning units (ensuring associated `LessonResource` and orphaned `FileAsset` rows are soft-deleted and removed from Document Hub), validate the Two-Tier Broadcast Notification RBAC policy, and test event-driven delivery and read-state synchronization in the user inbox.

---

## 1. Scope & Invariants (AGENTS.md & System Specification)

1. **Cascade Attachment Deletion & Document Hub Invariant:**
   - Trashing a Lesson or LearningUnit automatically cleans up linked `LessonResource` entries and marks orphaned `FileAsset` records as `TRASH`, instantly removing them from the Course Document Hub (`GET /api/courses/<id>/files`).
2. **Cascade LearningUnit (Chapter) Deletion:**
   - Deleting a LearningUnit disassociates or cascades cleanly without foreign key / orphan violations in SQL Server.
3. **Course Document Tree Consistency:**
   - The Student Document Hub hierarchy mirrors the curriculum organization (learning units and lessons).
4. **Two-Tier Broadcast Notification RBAC:**
   - Primary Admin (`admin@pwd301.local`, `ADMIN_PRIMARY`): Authorized to broadcast across all categories (`SYSTEM`, `MAINTENANCE`, `ACADEMIC`, etc.).
   - System Monitoring Admin (`admin.monitor@pwd301.local`, `ADMIN_SYSTEM_MONITORING`): Strictly locked to `SYSTEM` broadcasts only. Broadcast attempts for other categories must return HTTP 403 Forbidden (`"Admin giám sát hệ thống chỉ được phép phát thông báo liên quan đến hệ thống."`).
   - Other Sub-Admins (e.g. `admin.course1@pwd301.local`, `ADMIN_COURSE_REVIEW`): Broadcast attempts must return HTTP 403 Forbidden (`"Bạn không có quyền phát thông báo toàn hệ thống."`).
5. **Event-Driven Notification Delivery:**
   - Broadcast and system notifications populate targeted users' inboxes (`/auth/notifications`) with correct metadata and unread indicators.
6. **Notification Read State Synchronization:**
   - Marking a notification as read (`POST /auth/notifications/<id>/read`) updates unread count (`GET /auth/notifications/unread-count`) and flags `read: True` immediately.

---

## 2. Test Execution Schedule (6 Test Cases)

- **TC-IT17-001:** Cascade Attachment Deletion: Trashing Lesson Purges FileAsset from Document Hub
- **TC-IT17-002:** Cascade LearningUnit Deletion & Curriculum Consistency
- **TC-IT17-003:** Course Document Tree Hierarchy Verification
- **TC-IT17-004:** Two-Tier Broadcast Notification RBAC Enforcement (Primary vs System Monitoring vs Sub-Admin)
- **TC-IT17-005:** Event-Driven Notification Delivery into Student Inbox Feed
- **TC-IT17-006:** Notification Read State & Unread Counter Synchronization
