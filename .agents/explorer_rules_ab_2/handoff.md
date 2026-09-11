# Subsystem A & B Invariant and Business Rule Conformance Audit Report

**Author:** `explorer_rules_ab_2`  
**Date:** 2026-09-11T15:48:30Z  
**Scope:** Subsystem A (Authentication, Sessions, JWT, RBAC, Account Suspension, Password Management) and Subsystem B (Courses, Prerequisites, Lessons, Enrollments).  
**Authoritative Sources:**
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/01_BUSINESS_RULE_CATALOG.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md`
- `AGENTS.md` (Source of truth hierarchy & non-negotiable invariants)
- `docs/database/PWD301_DATABASE_ARCHITECTURE/` (04_DATA_DICTIONARY_IDENTITY.md, 05_DATA_DICTIONARY_COURSE.md, 13_CONSTRAINTS_AND_INVARIANTS.md)
- `docs/system/PWD301_SYSTEM_SPECIFICATION/api/12_ADMIN_API.md`
- Implementation code in `src/pwd301/`

---

## Executive Summary

A comprehensive audit of all 20 normative business rules spanning Subsystems A and B (`AUTH-001..006`, `COURSE-001..007`, `ENROLL-001..004`, `LESSON-001..004`) was conducted against the implementation in `src/pwd301/`.

The system exhibits strong foundational architecture:
- Core session vs JWT separation is cleanly partitioned with cross-context CSRF defenses (`authorization_service.py:92-98`).
- Password hashing uses Werkzeug adaptive hashing with constant-time dummy hashing against timing attacks (`user_service.py:217-236`).
- Course and enrollment models enforce database-level unique constraints (`uq_enrollments_student_user_id_course_id_2`, `ux_enrollment_period_active`, `uq_lessons_course_position_active`).
- Prerequisite DAG cycle detection is implemented using BFS traversal (`enrollment_service.py:676-703`).
- Course capacity is concurrency-safe using `UPDLOCK`/`with_for_update()` row locking (`enrollment_service.py:282-318`).
- 30-day post-departure retention purging with skeleton tombstones is implemented (`retention_service.py`).

However, **8 critical/moderate defects and specification deviations** were discovered where code diverges from the canonical specification:
1. **CRITICAL (High): `LESSON-003` Violation in `calculate_course_progress()`**: Denominator counts all published lessons without filtering by `required_for_periods_starting_at`, causing active students' progress to decrease when new lessons are added and blocking course completion.
2. **HIGH: `AUTH-005` Violation in Admin Suspension Routes**: `POST /api/admin/users/{user_id}/suspend` and `/admin/users/{user_id}/suspend` lack password re-authentication (`reauth`) and confirmation phrase checks (`CONFIRM_SUSPEND`).
3. **MEDIUM: `AUTH-001` Audit Gap in `apply_email_change_with_token()`**: Email changes succeed without recording a mandatory `AuditEvent`.
4. **MEDIUM: `AUTH-003` Divergence in `user_service.suspend_user()`**: Bypasses mandatory `AuditEvent`, omits reason validation, and lacks required `SecurityEvent` and user notification.
5. **MEDIUM: `COURSE-005` Lifecycle State Gap in `add_course_prerequisite()`**: Does not check whether the prerequisite course is soft-deleted or trashed/archived, allowing students to be permanently blocked.
6. **LOW: `AUTH-002` Session Cleanup Gap in `remove_role_from_user()`**: Fails to call `revoke_all_user_sessions()` and `revoke_all_user_tokens()`, leaving active session rows in the database.
7. **LOW: `COURSE-004` Notification Gap in `remove_role_from_user()`**: Revoking an instructor's role leaves their courses unmanaged without dispatching an alert or orphan audit.
8. **LOW: SQLite In-Memory Normalization Asymmetry in `User` Model**: `User` lacks `@sa.event.listens_for` listeners for `email_normalized`, unlike `Course`.

---

## Complete Business Rule to Implementation Traceability Matrix

| Rule ID | Spec Description | Implementation Location | Conformance Status | Severity / Finding |
|---|---|---|---|---|
| `AUTH-001` | Unique email login identifier, token-verified email change, change audit | `models/identity.py:47-52`, `services/user_service.py:42-83, 103-174`, `services/auth_token_service.py:338-410` | **PARTIAL** | **MEDIUM**: Email change succeeds without recording `AuditEvent`. |
| `AUTH-002` | Cumulative role hierarchy (Student→Instructor→Admin), valid closure, grant/revoke audit | `models/identity.py:154-177`, `services/user_service.py:469-693` | **PARTIAL** | **LOW**: `remove_role_from_user()` docstring promises session revocation, but does not call revocation functions. |
| `AUTH-003` | Immediate suspension revocation of all sessions and JWTs, single transaction, security + audit + notification | `services/audit_service.py:590-709`, `services/user_service.py:339-387`, `models/identity.py:126-129`, `__init__.py:581` | **PARTIAL** | **MEDIUM**: `user_service.suspend_user()` bypasses audit; suspension lacks `SecurityEvent` and notification. |
| `AUTH-004` | Browser session vs REST JWT, separate middleware, no JWT in localStorage | `services/session_auth_service.py`, `services/jwt_auth_service.py`, `services/authorization_service.py:55-108`, `__init__.py:822-837` | **CONFORMS** | No JWT in localStorage; cross-boundary CSRF prevented. |
| `AUTH-005` | Sensitive Admin action requires re-auth + phrase + reason | `models/identity.py:330`, `services/operations_service.py:1005`, `blueprints/api_admin/routes.py:484` | **VIOLATION** | **HIGH**: Re-authentication (`reauthenticated_at`) is completely unenforced; suspension lacks confirmation phrase. |
| `AUTH-006` | Admin cannot impersonate User; actor identity preserved | `services/authorization_service.py:55-108`, `__init__.py:623-654`, `models/notification_audit.py` | **CONFORMS** | No impersonation exists; actor snapshot captures true ID. |
| `COURSE-001` | Course code unique (normalized uppercase) | `models/course.py:53-57, 136-141`, `services/course_service.py:217-228` | **CONFORMS** | Filtered unique index `ux_courses_course_code_active` + service check. |
| `COURSE-002` | Course title unique (normalized lowercase) | `models/course.py:58-62, 142-148`, `services/course_service.py:229-240, 362-377` | **CONFORMS** | Filtered unique index `ux_courses_title_active` + service check. |
| `COURSE-003` | Course has 0/1 owner Instructor; verified role; reassign audit | `models/course.py:66-70`, `services/course_service.py:241-258, 637-710` | **CONFORMS** | FK owner nullable; verified INSTRUCTOR role; `COURSE_OWNER_REASSIGNED` audit logged. |
| `COURSE-004` | Instructor losing role does NOT delete Course; revoke/reassign service; audit+notification | `models/course.py:66-70`, `services/user_service.py:597-693`, `services/authorization_service.py:441` | **PARTIAL** | **LOW**: Courses remain orphaned without admin notification or orphan audit event. |
| `COURSE-005` | Prerequisite required and acyclic; DAG cycle validation; material change audit | `models/course.py:210-256`, `services/enrollment_service.py:636-734` | **PARTIAL** | **MEDIUM**: Cycle detection works, but does not prevent adding deleted/trashed courses as prerequisites. |
| `COURSE-006` | Active prerequisite blocks archive/delete | `services/course_service.py:109-140, 576-578` | **CONFORMS** | Reverse dependency check blocks transition to ARCHIVED or TRASH. |
| `COURSE-007` | Optional capacity cannot overbook; row lock + count before enrollment | `models/course.py:128`, `services/enrollment_service.py:282-318, 547-580` | **CONFORMS** | `with_for_update()` / `WITH (UPDLOCK, HOLDLOCK)` serializes concurrent enrollments. |
| `ENROLL-001` | Single logical Enrollment per User/Course; unique constraint; upsert transaction | `models/course.py:575-577`, `services/enrollment_service.py:251-280` | **CONFORMS** | `uq_enrollments_student_user_id_course_id_2` + seamless delegation to `re_enroll_student()`. |
| `ENROLL-002` | Re-enroll restarts from scratch in new period under same Enrollment | `models/course.py:656-677`, `services/enrollment_service.py:583-633` | **CONFORMS** | Creates new period (`period_no + 1`), resets progress cache to 0. |
| `ENROLL-003` | Prior completed Course satisfies prerequisite indefinitely | `models/course.py:795-865`, `services/enrollment_service.py:173-184`, `services/completion_service.py:488-518` | **CONFORMS** | `CourseCompletionSummary.prerequisite_eligible` checked and permanently preserved. |
| `ENROLL-004` | Leave >30d purge detail and stop future regrade; retain completion summary | `services/enrollment_service.py:428-433`, `services/retention_service.py:174-270` | **CONFORMS** | Retention due set to +30d; purge worker truncates progress, emits `EnrollmentEvent(DETAIL_PURGED)`. |
| `LESSON-001` | Lesson reorder does not lose completion; unique position contiguity | `models/course.py:467-475`, `services/lesson_service.py:442-550` | **CONFORMS** | Safe 2-phase offset reorder (`TEMP_POSITION_OFFSET = 100_000`) + audit log. |
| `LESSON-002` | Lesson completion requires min time + viewed most; bounded heartbeat | `models/course.py:415-426, 480-484`, `services/lesson_service.py:885-985` | **CONFORMS** | Anti-tampering bounds (1..60s, 0..1.0); monotonic `completed_at` persistence. |
| `LESSON-003` | New Lesson is supplementary ("Xem thêm") for existing period; progress compares start time | `models/course.py:427`, `services/completion_service.py:285-323, 434-440` | **VIOLATION** | **HIGH**: `calculate_course_progress()` ignores `required_for_periods_starting_at` in denominator, lowering existing progress. |
| `LESSON-004` | Material rewrite does not force completed student to re-study | `services/lesson_service.py:291-440`, `models/course.py:734-793` | **CONFORMS** | `update_lesson()` never modifies or unsets `LessonProgress.completed_at`. |

---

## 1. Observation

### Observation 1.1: `calculate_course_progress()` Ignores `required_for_periods_starting_at`
- **File:** `src/pwd301/services/completion_service.py`, Lines 285–323
- **Verbatim Code:**
```python
    total_published_lessons = (
        sess.query(sa.func.count(Lesson.id))
        .filter(
            Lesson.course_id == enrollment.course_id,
            Lesson.status == "PUBLISHED",
            Lesson.deleted_at.is_(None),
        )
        .scalar()
        or 0
    )

    if total_published_lessons == 0:
        enrollment.current_progress_percent = Decimal("0.00")
        enrollment.updated_at = utc_now()
        sess.flush()
        return 0.0

    completed_lessons = (
        sess.query(sa.func.count(LessonProgress.id))
        .join(Lesson, Lesson.id == LessonProgress.lesson_id)
        .filter(
            LessonProgress.enrollment_period_id == current_period.id,
            LessonProgress.completed_at.isnot(None),
            Lesson.course_id == enrollment.course_id,
            Lesson.status == "PUBLISHED",
            Lesson.deleted_at.is_(None),
        )
        .scalar()
        or 0
    )

    raw_pct = (completed_lessons / total_published_lessons) * 100.0
    pct = min(100.0, max(0.0, round(raw_pct, 2)))
```
- **Contrast with `evaluate_course_completion()` in same file (Lines 434–440):**
```python
        period_start = current_period.started_at
        required_lessons = [
            les
            for les in published_lessons
            if les.required_for_periods_starting_at is None
            or (period_start is not None and period_start >= les.required_for_periods_starting_at)
        ]
```
- **Specification Conflict:**
  - `01_BUSINESS_RULE_CATALOG.md:28` (`LESSON-003`): `Service logic: progress computation compares start time`.
  - `docs/database/PWD301_DATABASE_ARCHITECTURE/05_DATA_DICTIONARY_COURSE.md:430`: `Lesson mới không làm existing period tụt progress: required_for_periods_starting_at quyết định eligibility`.
  - In `calculate_course_progress()`, any newly published lesson is immediately included in `total_published_lessons`. For a student whose period started *before* the lesson was published, their progress drops (e.g. 5/5 = 100% drops to 5/6 = 83.33%). Then in `evaluate_course_completion()` line 395:
    `if rule.minimum_progress_percent is not None and current_pct < float(rule.minimum_progress_percent): return False, existing_summary`
    The student is blocked from completing the course even though the new lesson was only "Xem thêm" for their period.

### Observation 1.2: Admin Account Suspension Routes Lack Re-auth and Confirmation Phrase
- **Files:**
  - `src/pwd301/blueprints/api_admin/routes.py`, Lines 484–514
  - `src/pwd301/blueprints/admin/routes.py`, Lines 513–545
  - `src/pwd301/services/audit_service.py`, Lines 590–637
- **Verbatim Code in `api_admin/routes.py`:**
```python
@api_admin_bp.route("/users/<user_id>/suspend", methods=["POST"])
@jwt_required
@admin_required
def api_admin_suspend_user(user_id: str) -> tuple[Response, int] | Response:
    actor = require_authenticated_actor()
    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = payload.get("reason", "")

    user = suspend_user_account(
        admin_actor=actor,
        target_user_id=user_id,
        reason=reason,
        session=db.session,
    )
```
- **Specification Conflict:**
  - `docs/system/PWD301_SYSTEM_SPECIFICATION/api/12_ADMIN_API.md:5-15`:
    `POST /api/admin/users/{user_id}/suspend`
    `Authorization: Admin + reauth + reason/phrase policy`
    `Request: reason,confirmation`
    `Errors: REAUTH_REQUIRED / CONFIRMATION_MISMATCH`
  - `01_BUSINESS_RULE_CATALOG.md:13` (`AUTH-005`): `Sensitive Admin action reauth + phrase + reason... Service logic: reauth freshness + exact phrase... Audit: mandatory audit`.
  - `AuthSession.reauthenticated_at` exists in `src/pwd301/models/identity.py:330` but is never checked. Neither endpoint validates `reauth` freshness or verifies that `confirmation` matches `"CONFIRM_SUSPEND"`.

### Observation 1.3: `apply_email_change_with_token()` Lacks Mandatory `AuditEvent`
- **File:** `src/pwd301/services/auth_token_service.py`, Lines 383–408
- **Verbatim Code:**
```python
    user = sess.get(User, token_record.user_id)
    if user is None:
        raise UserNotFoundError(f"User with ID {token_record.user_id} not found.")

    token_record.consumed_at = utc_now()
    user.email = norm_new_email
    user.email_verified_at = utc_now()
    user.auth_version += 1
    user.updated_at = utc_now()

    from pwd301.services.jwt_auth_service import revoke_all_user_tokens
    from pwd301.services.session_auth_service import revoke_all_user_sessions

    revoke_all_user_sessions(user.id, session=sess)
    revoke_all_user_tokens(user.id, session=sess)

    try:
        sess.commit()
```
- **Specification Conflict:**
  - `01_BUSINESS_RULE_CATALOG.md:9` (`AUTH-001`): `Audit: email change audit`.
  - `06_NON_NEGOTIABLE_INVARIANTS.md:Invariant 22`: `Important audit is append-only; required-audit sensitive action fails if audit cannot persist.`
  - Changing primary identity (email) completes without any record added to `audit_events`.

### Observation 1.4: `user_service.suspend_user()` Bypasses Audit and Lacks `SecurityEvent` / Notification
- **File:** `src/pwd301/services/user_service.py`, Lines 339–387
- **Verbatim Code:**
```python
def suspend_user(
    user_id: int,
    reason: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> User:
...
    user.status = "SUSPENDED"
    user.suspended_at = now
    user.suspension_reason = reason
    user.auth_version += 1
    user.updated_at = now

    revoke_all_user_sessions(user.id, session=sess)
    revoke_all_user_tokens(user.id, session=sess)

    try:
        sess.commit()
```
- **Specification Conflict:**
  - `01_BUSINESS_RULE_CATALOG.md:11` (`AUTH-003`): `Audit: security + audit + notification`.
  - Two parallel suspension functions exist: `audit_service.suspend_user_account()` (which records audit) and `user_service.suspend_user()` (which does not). Neither emits a `SecurityEvent` row (`models/identity.py:484`) or dispatches a notification/email to the suspended user.

### Observation 1.5: `add_course_prerequisite()` Does Not Validate Prerequisite Lifecycle Status
- **File:** `src/pwd301/services/enrollment_service.py`, Lines 655–664
- **Verbatim Code:**
```python
    # 2. Resolve prerequisite course
    prereq_course = _resolve_course(prerequisite_course_id, session=sess)
    if prereq_course is None:
        raise CourseNotFoundError("Prerequisite course not found.")

    # 3. Prevent self-reference
    if course.id == prereq_course.id:
        raise CourseValidationError("A course cannot be a prerequisite of itself.")
```
- **Specification Conflict:**
  - `_resolve_course` resolves any course by PK/UUID, including soft-deleted ones (`deleted_at is not None`) or trashed/archived ones.
  - While `_check_active_prerequisite_dependencies` prevents archiving a course that is *already* a prerequisite, `add_course_prerequisite()` allows attaching a course that is *already* in `TRASH`, `ARCHIVED`, or soft-deleted as a prerequisite to an active course. Students can never fulfill prerequisites for trashed courses, creating a deadlock.

### Observation 1.6: `remove_role_from_user()` Omits Explicit Session/Token Revocation
- **File:** `src/pwd301/services/user_service.py`, Lines 608–612, 650–693
- **Verbatim Docstring:** `"- Increments user.auth_version by 1 and revokes tokens/sessions."`
- **Verbatim Implementation:**
```python
    after_roles = sorted(new_role_codes)
    user.auth_version += 1
    user.updated_at = now
...
    audit_entry = AuditEvent(...)
    sess.add(audit_entry)

    try:
        sess.commit()
```
- **Specification Conflict:**
  - In contrast to `change_password()`, `set_password()`, and `suspend_user()`, `remove_role_from_user()` omits calls to `revoke_all_user_sessions(user.id)` and `revoke_all_user_tokens(user.id)`. Active database session rows remain with `revoked_at IS NULL`.

### Observation 1.7: `COURSE-004` Missing Orphaned Course Notification on Role Revocation
- **File:** `src/pwd301/services/user_service.py`, Lines 650–693
- **Specification Conflict:**
  - `01_BUSINESS_RULE_CATALOG.md:18` (`COURSE-004`): `Instructor mất role không xóa Course... owner nullable... revoke/reassign service... audit+notification`.
  - When an instructor loses their INSTRUCTOR role, courses they owned remain associated with `owner_instructor_id = user.id`. The user can no longer manage them (`can_manage_course` returns False), but no notification is sent to administrators alerting them to reassign the orphaned courses.

### Observation 1.8: `User` Model Normalization Event Listener Asymmetry
- **File:** `src/pwd301/models/identity.py`, Lines 47–52 vs `src/pwd301/models/course.py`, Lines 197–208
- **Observation:** `Course` defines `@sa.event.listens_for(Course, "before_insert")` and `"before_update"` to guarantee that `course_code_normalized` and `title_normalized` are populated in Python memory regardless of database engine. `User` defines `email_normalized` as an SQL computed column without Python event listeners, resulting in `user.email_normalized` being `None` in memory before flush/refresh in non-SQL-Server environments.

---

## 2. Logic Chain

```
[Observation 1.1]
Lesson model includes `required_for_periods_starting_at`.
`evaluate_course_completion()` checks:
  period.started_at >= lesson.required_for_periods_starting_at
to determine if lesson is required for completion.
      │
      ▼
`calculate_course_progress()` computes progress percentage:
  progress = (completed_lessons / total_published_lessons) * 100.0
where `total_published_lessons` counts ALL published lessons without checking `required_for_periods_starting_at`.
      │
      ▼
When an instructor adds a new lesson to an active course, `total_published_lessons` increases for all existing students.
Existing students' progress drops (e.g. 100% -> 83.33%).
      │
      ▼
`evaluate_course_completion()` evaluates `current_pct < rule.minimum_progress_percent`.
Even though the student completed all required lessons for their period, the dropped progress percentage causes `evaluate_course_completion()` to return False.
      │
      ▼
[CONCLUSION 1]
Direct violation of `LESSON-003` and `05_DATA_DICTIONARY_COURSE.md:430`.
Severity: HIGH.

─────────────────────────────────────────────────────────────────────────────

[Observation 1.2]
`12_ADMIN_API.md` and `AUTH-005` mandate:
  - Sensitive admin action requires reauth freshness proof
  - Sensitive admin action requires confirmation phrase ("CONFIRM_SUSPEND")
  - Sensitive admin action requires mandatory reason
      │
      ▼
`api_admin_suspend_user()` and `admin_suspend_user()` extract `reason` from payload but do NOT validate `confirmation` phrase.
Neither endpoint verifies password re-authentication or inspects `AuthSession.reauthenticated_at`.
      │
      ▼
An administrator with a hijacked browser session or valid JWT can immediately suspend accounts without confirming password or typing the confirmation phrase.
      │
      ▼
[CONCLUSION 2]
Direct violation of `AUTH-005` and `12_ADMIN_API.md`.
Severity: HIGH.

─────────────────────────────────────────────────────────────────────────────

[Observation 1.3]
`AUTH-001` specifies: `Audit: email change audit`.
Invariant 22 specifies: `Important audit is append-only; required-audit sensitive action fails if audit cannot persist.`
      │
      ▼
`apply_email_change_with_token()` verifies token, mutates user.email, increments auth_version, and commits without creating an `AuditEvent`.
      │
      ▼
[CONCLUSION 3]
Audit trail gap for primary authentication credential alteration.
Severity: MEDIUM.

─────────────────────────────────────────────────────────────────────────────

[Observation 1.5]
`COURSE-005` & `COURSE-006` define active prerequisite relationships.
`add_course_prerequisite()` resolves prerequisite course via `_resolve_course()`.
`_resolve_course()` loads the course by ID/UUID without checking `deleted_at` or `status`.
      │
      ▼
A trashed or soft-deleted course can be attached as a prerequisite.
Students attempting to enroll in the dependent course cannot complete the trashed prerequisite.
      │
      ▼
[CONCLUSION 4]
Integrity gap in prerequisite graph management.
Severity: MEDIUM.
```

---

## 3. Caveats

1. **Test Suite Green Mirage**: All 94 unit tests for Subsystems A & B in `tests/unit/` pass. The existing tests pass because they assert existing behavior (e.g. `calculate_course_progress()` with static lesson sets, `suspend_user_account` without phrase checks) rather than testing boundary conditions defined in `12_ADMIN_API.md` or `LESSON-003`.
2. **Database Dialect Discrepancy**: The testing environment utilizes SQLite with mock concurrency hooks, whereas the production target is Microsoft SQL Server. SQLite does not compute persisted columns in Python memory prior to commit, which accentuates Observation 1.8.
3. **No Impersonation Confirmed**: Thorough search confirmed no impersonation feature exists in `src/pwd301/`. Multi-role switching is strictly limited to roles the authenticated user actually holds in the database, fully conforming to `AUTH-006`.
4. **Assessment / Grading Boundary**: Subsystem B lessons and courses interface with Subsystem C (Assessments & Question Bank). Assessment points and structure locking were spot-checked and found to conform to `ASSESS-001..003` (locked upon publish / first start).

---

## 4. Conclusion

The core business logic and database architecture for Subsystems A and B are fundamentally solid, but require remediation in 8 specific areas before reaching production certification.

### Priority Remediation Action Plan

| Rank | Defect ID | Rule ID | File & Lines | Severity | Recommended Fix |
|---|---|---|---|---|---|
| **1** | DEF-AB-01 | `LESSON-003` | `src/pwd301/services/completion_service.py:285-323` | **HIGH** | In `calculate_course_progress()`, filter `total_published_lessons` using `sa.or_(Lesson.required_for_periods_starting_at.is_(None), Lesson.required_for_periods_starting_at <= current_period.started_at)`. |
| **2** | DEF-AB-02 | `AUTH-005` | `src/pwd301/blueprints/api_admin/routes.py:484-514`, `blueprints/admin/routes.py:513-545` | **HIGH** | Require `confirmation == "CONFIRM_SUSPEND"` in suspend routes; add `@reauth_required` decorator verifying session re-authentication timestamp within 15 minutes. |
| **3** | DEF-AB-03 | `AUTH-001` | `src/pwd301/services/auth_token_service.py:387-408` | **MEDIUM** | In `apply_email_change_with_token()`, record `AuditEvent(action="USER_EMAIL_CHANGED", target_type="USER", target_id=user.id, before_json=..., after_json=...)` in the same transaction. |
| **4** | DEF-AB-04 | `AUTH-003` | `src/pwd301/services/user_service.py:339-387`, `services/audit_service.py:590-709` | **MEDIUM** | Unify `user_service.suspend_user()` with `audit_service.suspend_user_account()`; record `SecurityEvent(action_taken="REVOKE", event_type="ACCOUNT_SUSPENDED")`; enqueue user notification. |
| **5** | DEF-AB-05 | `COURSE-005` | `src/pwd301/services/enrollment_service.py:656-664` | **MEDIUM** | In `add_course_prerequisite()`, reject target courses where `prereq_course.deleted_at is not None` or `prereq_course.status in ("TRASH", "ARCHIVED")`. |
| **6** | DEF-AB-06 | `AUTH-002` | `src/pwd301/services/user_service.py:650-693` | **LOW** | Call `revoke_all_user_sessions(user.id, session=sess)` and `revoke_all_user_tokens(user.id, session=sess)` in `remove_role_from_user()` and `assign_role_to_user()`. |
| **7** | DEF-AB-07 | `COURSE-004` | `src/pwd301/services/user_service.py:650-693` | **LOW** | Check for active courses owned by target user when removing `INSTRUCTOR` role; record `COURSE_ORPHANED` audit and notify administrators. |
| **8** | DEF-AB-08 | `AUTH-001` | `src/pwd301/models/identity.py:47-52` | **LOW** | Add `@sa.event.listens_for(User, "before_insert")` and `"before_update"` to normalize `email_normalized = email.strip().lower()` in Python memory. |

---

## 5. Verification Method

### 5.1 Independent Test Commands

Execute the Subsystem A & B test suite to verify current baselines:
```powershell
.venv\Scripts\python.exe -m pytest tests/unit/test_user_service.py tests/unit/test_session_auth_service.py tests/unit/test_jwt_auth_service.py tests/unit/test_course_service.py tests/unit/test_lesson_service.py tests/unit/test_enrollment_service.py tests/unit/test_completion_service.py -v
```

### 5.2 Specific Reproduction Scenarios for Identified Defects

#### Scenario A: Reproduction of DEF-AB-01 (`LESSON-003` Progress Drop)
Create a test in `tests/unit/test_completion_service.py`:
1. Create a course with 2 published lessons (`Lesson 1`, `Lesson 2`).
2. Enroll Student A (`period_no = 1`, `started_at = T0`).
3. Student completes `Lesson 1` and `Lesson 2`. Call `calculate_course_progress()`. Progress is 100.00%.
4. Instructor publishes `Lesson 3` at `T1 > T0` with `required_for_periods_starting_at = T1`.
5. Call `calculate_course_progress()` for Student A.
   - **Expected (`LESSON-003`):** Progress remains 100.00% because `Lesson 3` is supplementary for periods started at `T0`.
   - **Actual Buggy Behavior:** Progress drops to 66.67% (`2 / 3 * 100`).
   - **Completion Blocked:** Calling `evaluate_course_completion()` fails because `66.67% < 100.00%`.

#### Scenario B: Reproduction of DEF-AB-02 (`AUTH-005` Missing Re-auth & Confirmation Phrase)
Create a test in `tests/api/test_admin_audit_api.py`:
1. Authenticate as Admin via JWT.
2. Send `POST /api/admin/users/{user_id}/suspend` with payload `{"reason": "test"}` (omitting `confirmation`).
   - **Expected (`12_ADMIN_API.md`):** Returns HTTP 400 with code `CONFIRMATION_MISMATCH` or `REAUTH_REQUIRED`.
   - **Actual Buggy Behavior:** Returns HTTP 200 and suspends the user immediately without confirmation or password challenge.

#### Scenario C: Reproduction of DEF-AB-03 (`AUTH-001` Missing Email Change Audit)
Create a test in `tests/unit/test_user_service.py`:
1. Generate an `EMAIL_CHANGE` token for a user.
2. Call `apply_email_change_with_token()`.
3. Query `sess.query(AuditEvent).filter(AuditEvent.action == "USER_EMAIL_CHANGED").first()`.
   - **Expected (`AUTH-001`):** AuditEvent exists with old and new email.
   - **Actual Buggy Behavior:** Returns None (no audit recorded).

### 5.3 Invalidation Conditions
This report's findings are invalidated only if:
- Specification in `docs/system/PWD301_SYSTEM_SPECIFICATION/` is officially amended to exempt `calculate_course_progress()` from `required_for_periods_starting_at` filtering.
- Re-authentication and confirmation phrase requirements in `12_ADMIN_API.md` are deprecated by product design.
