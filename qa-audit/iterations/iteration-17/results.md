# Iteration 17 Execution Results: Cascade Deletions, Document Hub Integrity & Two-Tier Broadcast RBAC

**Iteration:** 17  
**Status:** COMPLETED (6/6 PASS, 0 Defects Discovered)  
**Execution Timestamp:** 2026-10-18T07:42:01Z  
**Run ID:** `FF8CA8`  
**Browser Engine:** Real Google Chrome 155 (`channel="chrome"`)  
**Lead Auditor:** AGENT 06 — End-to-End Business Workflow QA & AGENT 05 — Security & RBAC QA  

---

## 1. Test Execution Summary

| Test Case ID | Test Case Name | Status | Metrics / Measured Values | Evidence Artifact |
|---|---|---|---|---|
| **TC-IT17-001** | Cascade Attachment Deletion: Trashing Lesson Purges FileAsset from Document Hub | **PASS** | Course ID: `676440a5-93c3-444b-b9d8-ee8b62b6c2b8`. Pre-deletion files: 1; post-deletion files: 0. Trashing lesson cleanly cascades to linked `FileAsset` and `LessonResource` | `IT17_TC01_Cascade_Attachment_Deletion.png` |
| **TC-IT17-002** | Cascade LearningUnit Deletion & Curriculum Consistency | **PASS** | Unit ID: `8b10f556-40ad-41b4-bd1a-bb4547f8e7cc`. Soft-delete HTTP status: 200 OK. Curriculum integrity preserved without foreign key constraint violations | `IT17_TC02_Cascade_Learning_Unit_Deletion.png` |
| **TC-IT17-003** | Course Document Tree Hierarchy Verification | **PASS** | Hierarchical document contract verified. Tree returns standard items structure with active files; trashed items properly filtered out | `IT17_TC03_Document_Tree_Hierarchy.png` |
| **TC-IT17-004** | Two-Tier Broadcast Notification RBAC Enforcement (Primary vs System Monitoring vs Sub-Admin) | **PASS** | Primary Admin MAINTENANCE: 200 OK. Monitor Admin MAINTENANCE: 403 Forbidden. Monitor Admin SYSTEM: 200 OK. Course Review Admin SYSTEM: 403 Forbidden | `IT17_TC04_Two_Tier_Broadcast_RBAC.png` |
| **TC-IT17-005** | Event-Driven Notification Delivery into Student Inbox Feed | **PASS** | Broadcast published by Primary Admin; Student inbox feed immediately reflected notification ID `1004ff72-aaff-4106-beb6-a7a01e212363` with `is_read = False` | `IT17_TC05_Notification_Delivery.png` |
| **TC-IT17-006** | Notification Read State & Unread Counter Synchronization | **PASS** | Student unread count decremented from 22 to 21 upon marking read. `is_read = True` state persisted in SQL Server database | `IT17_TC06_Notification_Read_Sync.png` |

---

## 2. Key Findings & Empirical Observations

1. **Cascade Attachment Deletion & Document Hub Invariant (Section 4 & 10.3):**
   - Verified that when an Instructor trashes a Lesson containing attached resources (`upload_attachment` created `LessonResource` + `FileAsset`), the system automatically cascades the deletion.
   - The Course Document Hub (`GET /instructor/courses/<id>/files`) immediately reflected 0 files without manual detachment.
2. **Curriculum Unit Deletion Integrity:**
   - Trashing a `LearningUnit` executes cleanly via soft-deletion (`is_deleted = True` / `deleted_at`) preserving historical integrity while removing child references from the active student syllabus.
3. **Two-Tier Broadcast RBAC Validation (`src/pwd301/blueprints/admin/routes.py` lines 797–806):**
   - **Primary Admin (`ADMIN_PRIMARY`)**: Authorized to broadcast any category (`MAINTENANCE`, `SYSTEM`, `ACADEMIC`, etc.) $\rightarrow$ HTTP 200.
   - **System Monitoring Admin (`ADMIN_SYSTEM_MONITORING`)**: Locked strictly to `SYSTEM` category broadcasts. Attempting to broadcast `MAINTENANCE` is rejected with HTTP 403 Forbidden: `"Admin giám sát hệ thống chỉ được phép phát thông báo liên quan đến hệ thống."`.
   - **Course Review Admin (`ADMIN_COURSE_REVIEW`)**: Denied broadcast capabilities completely. Attempting to broadcast `SYSTEM` is rejected with HTTP 403 Forbidden: `"Bạn không có quyền phát thông báo toàn hệ thống."`.
4. **End-to-End Notification Lifecycle:**
   - Real-time delivery from Admin broadcast directly populates the Student notification collection (`GET /auth/notifications`).
   - Read state updates (`POST /auth/notifications/<id>/read`) atomically update `is_read: true` and decrement the aggregate unread badge counter.
