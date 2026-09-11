# Progress — explorer_rules_ab_2

- Last visited: 2026-09-11T15:52:00Z
- Status: Completed deep audit of Subsystems A (Auth/Identity/RBAC) and B (Courses/Lessons/Enrollments). Handoff report finalized.
- Findings:
  1. LESSON-003 Invariant Violation: `calculate_course_progress` in `completion_service.py` ignores `required_for_periods_starting_at`, causing existing periods' progress to drop when new lessons are added. (HIGH)
  2. AUTH-005 Invariant Violation: Admin sensitive actions (e.g. account suspension in `api_admin/routes.py` and `admin/routes.py`) lack password re-authentication (`reauth`) and confirmation phrase checks. (HIGH)
  3. AUTH-001 Audit Gap: `apply_email_change_with_token` in `auth_token_service.py` fails to record an `AuditEvent` on email change. (MEDIUM)
  4. AUTH-003 Audit & Security Gap: `user_service.suspend_user()` bypasses audit event and reason validation; suspension lacks SecurityEvent and notification. (MEDIUM)
  5. COURSE-005 Integrity Gap: `add_course_prerequisite` does not validate that prerequisite course is non-deleted and not trashed/archived. (MEDIUM)
  6. AUTH-002 Session Revocation Gap: `remove_role_from_user` fails to call `revoke_all_user_sessions` and `revoke_all_user_tokens`. (LOW)
  7. COURSE-004 Notification Gap: Role revocation of an instructor leaves courses orphaned without notification or orphan audit. (LOW)
  8. AUTH-001 In-memory Normalization Gap: `User` model lacks Python `before_insert`/`before_update` listeners for `email_normalized`. (LOW)
- Next: Completed. Findings reported to parent orchestrator.

