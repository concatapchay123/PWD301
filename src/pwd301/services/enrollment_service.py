"""Course enrollment lifecycle, capacity, prerequisites, and re-enrollment service.

Implements:
- Single logical Enrollment per Student/Course invariant
  (uq_enrollments_student_user_id_course_id_2).
- EnrollmentPeriod lifecycle management (started_at, left_at, retention_due_at).
- Concurrency-safe capacity enforcement using database row locking (with_for_update).
- Prerequisite evaluation against durable CourseCompletionSummary (Algorithm 03).
- Dependency graph cycle detection using reachability traversal (Algorithm 03).
- Course departure (LEFT) with 30-day detailed retention window.
- Re-enrollment (REENROLLED) reusing existing Enrollment and opening a new period.
- Append-only EnrollmentEvent and AuditEvent logging.
- Resource-level authorization and IDOR prevention.
"""

import contextlib
import json
import logging
import uuid
from datetime import timedelta
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Session, scoped_session

from pwd301.extensions import db
from pwd301.models.course import (
    Course,
    CourseCompletionSummary,
    CoursePrerequisite,
    Enrollment,
    EnrollmentEvent,
    EnrollmentPeriod,
)
from pwd301.models.identity import User
from pwd301.models.notification_audit import AuditEvent
from pwd301.models.types import utc_now
from pwd301.services.authorization_service import (
    _resolve_course,
    _resolve_user,
    require_course_manager,
)
from pwd301.services.exceptions import (
    AccountNotActiveError,
    CourseNotAvailableError,
    CourseNotFoundError,
    CourseValidationError,
    EnrollmentCapacityExceededError,
    EnrollmentNotFoundError,
    EnrollmentPrerequisiteError,
    EnrollmentStateViolationError,
    ForbiddenError,
    PrerequisiteCycleError,
    UserNotFoundError,
)

logger = logging.getLogger(__name__)

# Standard retention window for detailed learning data after course withdrawal (in days)
ENROLLMENT_DETAIL_RETENTION_DAYS = 30

# Allowed enrollment statuses per check constraint ck_enrollments_1
VALID_ENROLLMENT_STATUSES = {
    "ACTIVE",
    "LEFT",
    "COMPLETED",
    "RETENTION_PENDING",
    "DETAIL_PURGED",
}

# Allowed period statuses per check constraint ck_enrollment_periods_2
VALID_PERIOD_STATUSES = {"ACTIVE", "LEFT", "COMPLETED", "PURGED"}

# Allowed enrollment event types per check constraint ck_enrollment_events_1
VALID_EVENT_TYPES = {"ENROLLED", "LEFT", "REENROLLED", "COMPLETED", "DETAIL_PURGED"}


def _resolve_enrollment(
    enrollment_or_id: Enrollment | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> Enrollment | None:
    """Resolve an Enrollment instance from model, integer PK, public UUID, or string."""
    if isinstance(enrollment_or_id, Enrollment):
        return enrollment_or_id

    sess = session if session is not None else db.session
    if isinstance(enrollment_or_id, int):
        return sess.get(Enrollment, enrollment_or_id)

    if isinstance(enrollment_or_id, uuid.UUID):
        return sess.query(Enrollment).filter(Enrollment.public_id == enrollment_or_id).first()

    if isinstance(enrollment_or_id, str):
        try:
            val_uuid = uuid.UUID(enrollment_or_id)
            return sess.query(Enrollment).filter(Enrollment.public_id == val_uuid).first()
        except ValueError:
            pass
        if enrollment_or_id.isdigit():
            return sess.get(Enrollment, int(enrollment_or_id))

    return None


def _record_enrollment_event(
    sess: Session | scoped_session[Any],
    enrollment_id: int,
    event_type: str,
    period_id: int | None = None,
    actor_user_id: int | None = None,
    reason: str | None = None,
) -> EnrollmentEvent:
    """Append an immutable event record to enrollment_events."""
    event = EnrollmentEvent(
        enrollment_id=enrollment_id,
        period_id=period_id,
        event_type=event_type,
        actor_user_id=actor_user_id,
        reason=reason,
        created_at=utc_now(),
    )
    sess.add(event)
    return event


def _record_prerequisite_audit_event(
    sess: Session | scoped_session[Any],
    actor: User,
    action: str,
    course_id: int,
    prerequisite_course_id: int,
    reason: str | None = None,
) -> AuditEvent:
    """Record an append-only AuditEvent for course prerequisite modifications."""
    actor_roles = ",".join(sorted(actor.role_codes)) if actor.role_codes else "UNKNOWN"
    audit_entry = AuditEvent(
        actor_user_id=actor.id,
        actor_roles_snapshot=actor_roles,
        action=action,
        target_type="COURSE_PREREQUISITE",
        target_id=course_id,
        reason=reason,
        before_json=None,
        after_json=(
            f'{{"course_id": {course_id}, "prerequisite_course_id": {prerequisite_course_id}}}'
        ),
        performed_as_admin=actor.is_admin,
        created_at=utc_now(),
    )
    sess.add(audit_entry)
    return audit_entry


def check_prerequisites_met(
    student_user_id: int,
    course_id: int,
    session: Session | scoped_session[Any] | None = None,
) -> tuple[bool, list[str]]:
    """Evaluate whether a student has satisfied all direct prerequisites of a course.

    Adheres to Algorithm 03: Prerequisite Evaluation.
    Checks durable `course_completion_summaries` records where `prerequisite_eligible == True`
    or `ever_completed == True`.

    Returns:
        (is_eligible, missing_course_titles)
    """
    sess = session if session is not None else db.session

    prereq_links = (
        sess.query(CoursePrerequisite)
        .filter(
            CoursePrerequisite.course_id == course_id,
            CoursePrerequisite.approval_status == "APPROVED",
        )
        .all()
    )
    if not prereq_links:
        return True, []

    prereq_ids = [link.prerequisite_course_id for link in prereq_links]

    # Find durable completion summaries where prerequisite_eligible is True
    summaries = (
        sess.query(CourseCompletionSummary)
        .filter(
            CourseCompletionSummary.student_user_id == student_user_id,
            CourseCompletionSummary.course_id.in_(prereq_ids),
            CourseCompletionSummary.prerequisite_eligible == True,
        )
        .all()
    )

    completed_ids = {s.course_id for s in summaries}
    completed_enrs = (
        sess.query(Enrollment.course_id)
        .filter(
            Enrollment.student_user_id == student_user_id,
            Enrollment.course_id.in_(prereq_ids),
            Enrollment.status == "COMPLETED",
        )
        .all()
    )
    for ce in completed_enrs:
        completed_ids.add(ce[0])

    missing_ids = [pid for pid in prereq_ids if pid not in completed_ids]

    if not missing_ids:
        return True, []

    missing_courses = sess.query(Course).filter(Course.id.in_(missing_ids)).all()
    missing_titles = [c.title for c in missing_courses]
    return False, missing_titles


def enroll_student(
    actor: User,
    course_id: int | uuid.UUID | str,
    student_id: int | uuid.UUID | str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> Enrollment:
    """Enroll a student into a published course.

    Invariants enforced:
    - Actor authorization: Students may only enroll themselves unless caller is Administrator.
    - Active account check: Inactive / suspended users cannot enroll.
    - Course availability: Only PUBLISHED and non-deleted courses accept enrollments.
    - Prerequisite evaluation: All prerequisites must be satisfied (Algorithm 03).
    - Capacity control: Prevents over-enrollment via row locking (with_for_update).
    - Single logical Enrollment: If student previously left (LEFT/DETAIL_PURGED), delegates
      to re_enroll_student rather than duplicating records.
    - Append-only EnrollmentEvent logging.
    """
    sess = session if session is not None else db.session

    # 1. Resolve target student
    if student_id is None:
        target_student = actor
    else:
        resolved = _resolve_user(student_id, session=sess)
        if resolved is None:
            raise UserNotFoundError("Student not found.")
        target_student = resolved

    # 2. Authorization check
    if not actor.is_admin and actor.id != target_student.id:
        raise ForbiddenError("Students may only enroll themselves.")

    if not target_student.is_active or not actor.is_active:
        raise AccountNotActiveError("Inactive or suspended accounts cannot enroll in courses.")

    # 3. Resolve course
    course = _resolve_course(course_id, session=sess)
    if course is None:
        raise CourseNotFoundError("Course not found.")

    # 4. Check course status
    if course.deleted_at is not None or course.status != "PUBLISHED":
        raise CourseNotAvailableError(
            f"Course is not available for enrollment (status: {course.status})."
        )

    # 5. Check prerequisites
    is_eligible, missing_titles = check_prerequisites_met(
        target_student.id, course.id, session=sess
    )
    if not is_eligible:
        missing_str = ", ".join(missing_titles)
        raise EnrollmentPrerequisiteError(f"Prerequisite courses not completed: {missing_str}")

    # 6. Check existing enrollment record
    existing_enrollment = (
        sess.query(Enrollment)
        .filter(
            Enrollment.student_user_id == target_student.id,
            Enrollment.course_id == course.id,
        )
        .first()
    )

    if existing_enrollment is not None:
        if existing_enrollment.status == "ACTIVE":
            # Native idempotency: already enrolled, return current enrollment safely
            existing_enrollment._is_new = False
            return existing_enrollment

        re_enroll_statuses = ("LEFT", "DETAIL_PURGED", "COMPLETED", "RETENTION_PENDING")
        if existing_enrollment.status in re_enroll_statuses:
            # Seamless re-enrollment flow reuses the existing Enrollment record
            reenrolled = re_enroll_student(
                actor=actor,
                course_id=course.id,
                student_id=target_student.id,
                session=sess,
            )
            reenrolled._is_new = False
            return reenrolled

        raise EnrollmentStateViolationError(
            f"Cannot enroll student with current enrollment status: {existing_enrollment.status}."
        )

    # 7. Concurrency & Capacity check with database row locking (ADR-002 / SQL Server UPDLOCK)
    bind = sess.get_bind()
    dialect_name = getattr(bind.dialect, "name", "") if bind is not None else ""

    if dialect_name == "sqlite":
        # In SQLite (used in multi-threaded concurrency tests), immediately acquire write lock
        # via atomic row update to serialize concurrent transactions at the database level
        sess.execute(
            sa.update(Course).where(Course.id == course.id).values(updated_at=Course.updated_at)
        )

    course_q = sess.query(Course).filter(Course.id == course.id)
    try:
        if dialect_name == "mssql":
            course_q = course_q.with_hint(Course, "WITH (UPDLOCK, HOLDLOCK)")
        else:
            course_q = course_q.with_for_update()
    except Exception:
        course_q = course_q.with_for_update()
    locked_course = course_q.first()
    if locked_course is None:
        raise CourseNotFoundError("Course not found.")

    # Capacity check: Prevent over-enrollment if course capacity is set
    if locked_course.capacity is not None:
        active_enrollment_count = (
            sess.query(sa.func.count(Enrollment.id))
            .filter(
                Enrollment.course_id == locked_course.id,
                Enrollment.status == "ACTIVE",
            )
            .scalar()
            or 0
        )
        if active_enrollment_count >= locked_course.capacity:
            raise EnrollmentCapacityExceededError(
                f"Course capacity of {locked_course.capacity} has been reached."
            )

    # 8. Create new Enrollment and EnrollmentPeriod (period_no = 1)
    now = utc_now()
    enrollment = Enrollment(
        student_user_id=target_student.id,
        course_id=locked_course.id,
        status="ACTIVE",
        current_progress_percent=0,
        enrolled_at=now,
        created_at=now,
        updated_at=now,
    )
    sess.add(enrollment)
    sess.flush()

    period = EnrollmentPeriod(
        enrollment_id=enrollment.id,
        period_no=1,
        started_at=now,
        status="ACTIVE",
        created_at=now,
    )
    sess.add(period)
    sess.flush()

    enrollment.current_period_id = period.id

    # 9. Update first_student_enrolled_at if first enrollment ever
    if locked_course.first_student_enrolled_at is None:
        locked_course.first_student_enrolled_at = now

    # 10. Record append-only event
    _record_enrollment_event(
        sess=sess,
        enrollment_id=enrollment.id,
        period_id=period.id,
        event_type="ENROLLED",
        actor_user_id=actor.id,
    )
    sess.flush()

    try:
        from pwd301.services.notification_service import dispatch_notification

        if locked_course.owner_instructor_id:
            dispatch_notification(
                recipient_user=locked_course.owner_instructor_id,
                event_type="STUDENT_ENROLLED",
                title="Học viên mới tham gia khóa học",
                body=f"Học viên {target_student.display_name} vừa đăng ký tham gia khóa học '{locked_course.title}'.",
                action_url=f"#/instructor/courses/manage?id={locked_course.public_id}",
                category="COURSE",
                target_role="INSTRUCTOR",
                event_key=uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"pwd301:enrollment:{enrollment.id}:STUDENT_ENROLLED:INSTRUCTOR",
                ),
                session=sess,
            )

        dispatch_notification(
            recipient_user=target_student.id,
            event_type="STUDENT_ENROLLED",
            title="Đăng ký khóa học thành công",
            body=f"Bạn đã đăng ký thành công khóa học '{locked_course.title}'. Bắt đầu học ngay hôm nay!",
            action_url=f"#/student/courses/detail?id={locked_course.public_id}",
            category="COURSE",
            target_role="STUDENT",
            event_key=uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"pwd301:enrollment:{enrollment.id}:STUDENT_ENROLLED:STUDENT",
            ),
            session=sess,
        )
    except Exception as exc:
        logger.warning("Failed to dispatch STUDENT_ENROLLED notification: %s", exc)

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    enrollment._is_new = True
    return enrollment


def leave_course(
    actor: User,
    course_id: int | uuid.UUID | str,
    student_id: int | uuid.UUID | str | None = None,
    reason: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> Enrollment:
    """Withdraw a student from an enrolled course.

    Invariants enforced:
    - Only the enrolled student or an Administrator may withdraw.
    - Current enrollment status must be ACTIVE.
    - Closes current EnrollmentPeriod (status='LEFT', left_at=utc_now()).
    - Retention guarantee: Sets detail_retention_due_at = utc_now() + 30 days.
      Data is NOT hard-deleted.
    - Records append-only EnrollmentEvent(event_type='LEFT').
    """
    sess = session if session is not None else db.session

    # 1. Resolve student
    if student_id is None:
        target_student = actor
    else:
        resolved = _resolve_user(student_id, session=sess)
        if resolved is None:
            raise UserNotFoundError("Student not found.")
        target_student = resolved

    # 2. Authorization check
    if not actor.is_admin and actor.id != target_student.id:
        raise ForbiddenError("You do not have permission to withdraw this student.")

    # 3. Resolve course
    course = _resolve_course(course_id, session=sess)
    if course is None:
        raise CourseNotFoundError("Course not found.")

    # 4. Find enrollment
    enrollment = (
        sess.query(Enrollment)
        .filter(
            Enrollment.student_user_id == target_student.id,
            Enrollment.course_id == course.id,
        )
        .first()
    )
    if enrollment is None:
        raise EnrollmentNotFoundError("Enrollment record not found for this course.")

    if enrollment.status == "LEFT":
        # Native idempotency: already left, return current record safely
        return enrollment

    if enrollment.status != "ACTIVE":
        raise EnrollmentStateViolationError(
            f"Cannot leave course: enrollment status is '{enrollment.status}', expected 'ACTIVE'."
        )

    # 5. Transition to LEFT with 30-day retention window
    now = utc_now()
    retention_due = now + timedelta(days=ENROLLMENT_DETAIL_RETENTION_DAYS)

    # Close period
    if enrollment.current_period_id is not None:
        current_period = sess.get(EnrollmentPeriod, enrollment.current_period_id)
        if current_period is not None and current_period.status == "ACTIVE":
            current_period.status = "LEFT"
            current_period.left_at = now
            current_period.retention_due_at = retention_due

    enrollment.status = "LEFT"
    enrollment.left_at = now
    enrollment.detail_retention_due_at = retention_due
    enrollment.updated_at = now

    # 6. Record append-only event
    _record_enrollment_event(
        sess=sess,
        enrollment_id=enrollment.id,
        period_id=enrollment.current_period_id,
        event_type="LEFT",
        actor_user_id=actor.id,
        reason=reason,
    )
    sess.flush()

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return enrollment


def re_enroll_student(
    actor: User,
    course_id: int | uuid.UUID | str,
    student_id: int | uuid.UUID | str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> Enrollment:
    """Re-enroll a student into a course after having previously left.

    Invariants enforced:
    - Reuses existing Enrollment record (preserves single logical enrollment invariant).
    - Checks course availability (PUBLISHED, not deleted).
    - Re-evaluates prerequisites and checks course capacity with row locking.
    - Creates a new EnrollmentPeriod with incremented period_no (last_period_no + 1).
    - Resets active progress cache (current_progress_percent = 0).
    - Clears left_at and detail_retention_due_at.
    - Records append-only EnrollmentEvent(event_type='REENROLLED').
    """
    sess = session if session is not None else db.session

    # 1. Resolve student
    if student_id is None:
        target_student = actor
    else:
        resolved = _resolve_user(student_id, session=sess)
        if resolved is None:
            raise UserNotFoundError("Student not found.")
        target_student = resolved

    # 2. Authorization check
    if not actor.is_admin and actor.id != target_student.id:
        raise ForbiddenError("Students may only re-enroll themselves.")

    if not target_student.is_active or not actor.is_active:
        raise AccountNotActiveError("Inactive or suspended accounts cannot enroll in courses.")

    # 3. Resolve course
    course = _resolve_course(course_id, session=sess)
    if course is None:
        raise CourseNotFoundError("Course not found.")

    if course.deleted_at is not None or course.status != "PUBLISHED":
        raise CourseNotAvailableError(
            f"Course is not available for re-enrollment (status: {course.status})."
        )

    # 4. Find existing enrollment
    enrollment = (
        sess.query(Enrollment)
        .filter(
            Enrollment.student_user_id == target_student.id,
            Enrollment.course_id == course.id,
        )
        .first()
    )
    if enrollment is None:
        # Fall back to initial enrollment
        return enroll_student(
            actor=actor,
            course_id=course.id,
            student_id=target_student.id,
            session=sess,
        )

    if enrollment.status == "ACTIVE":
        # Native idempotency: already active, return current record safely
        return enrollment

    re_enroll_statuses = ("LEFT", "DETAIL_PURGED", "COMPLETED", "RETENTION_PENDING")
    if enrollment.status not in re_enroll_statuses:
        raise EnrollmentStateViolationError(
            f"Cannot re-enroll student with current enrollment status: '{enrollment.status}'."
        )

    # 5. Re-evaluate prerequisites
    is_eligible, missing_titles = check_prerequisites_met(
        target_student.id, course.id, session=sess
    )
    if not is_eligible:
        missing_str = ", ".join(missing_titles)
        raise EnrollmentPrerequisiteError(f"Prerequisite courses not completed: {missing_str}")

    # 6. Concurrency & Capacity check with database row locking (ADR-002 / SQL Server UPDLOCK)
    bind = sess.get_bind()
    dialect_name = getattr(bind.dialect, "name", "") if bind is not None else ""

    if dialect_name == "sqlite":
        # In SQLite (used in multi-threaded concurrency tests), immediately acquire write lock
        # via atomic row update to serialize concurrent transactions at the database level
        sess.execute(
            sa.update(Course).where(Course.id == course.id).values(updated_at=Course.updated_at)
        )

    course_q = sess.query(Course).filter(Course.id == course.id)
    try:
        if dialect_name == "mssql":
            course_q = course_q.with_hint(Course, "WITH (UPDLOCK, HOLDLOCK)")
        else:
            course_q = course_q.with_for_update()
    except Exception:
        course_q = course_q.with_for_update()
    locked_course = course_q.first()
    if locked_course is None:
        raise CourseNotFoundError("Course not found.")

    # Capacity check: Prevent over-enrollment if course capacity is set
    if locked_course.capacity is not None:
        active_enrollment_count = (
            sess.query(sa.func.count(Enrollment.id))
            .filter(
                Enrollment.course_id == locked_course.id,
                Enrollment.status == "ACTIVE",
            )
            .scalar()
            or 0
        )
        if active_enrollment_count >= locked_course.capacity:
            raise EnrollmentCapacityExceededError(
                f"Course capacity of {locked_course.capacity} has been reached."
            )

    # 7. Determine next period_no
    last_period_no = (
        sess.query(sa.func.max(EnrollmentPeriod.period_no))
        .filter(EnrollmentPeriod.enrollment_id == enrollment.id)
        .scalar()
        or 0
    )
    next_period_no = last_period_no + 1

    # 8. Create new active EnrollmentPeriod
    now = utc_now()
    new_period = EnrollmentPeriod(
        enrollment_id=enrollment.id,
        period_no=next_period_no,
        started_at=now,
        status="ACTIVE",
        created_at=now,
    )
    sess.add(new_period)
    sess.flush()

    # 9. Reactivate Enrollment
    enrollment.status = "ACTIVE"
    enrollment.enrolled_at = now
    enrollment.left_at = None
    enrollment.detail_retention_due_at = None
    enrollment.current_period_id = new_period.id
    enrollment.current_progress_percent = 0
    enrollment.updated_at = now

    if locked_course.first_student_enrolled_at is None:
        locked_course.first_student_enrolled_at = now

    # 10. Record append-only event
    _record_enrollment_event(
        sess=sess,
        enrollment_id=enrollment.id,
        period_id=new_period.id,
        event_type="REENROLLED",
        actor_user_id=actor.id,
    )
    sess.flush()

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return enrollment


def add_course_prerequisite(
    actor: User,
    course_id: int | uuid.UUID | str,
    prerequisite_course_id: int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> CoursePrerequisite:
    """Add a required prerequisite course with DAG cycle validation.

    Invariants enforced:
    - Authorization: Course owner Instructor or Admin only (require_course_manager).
    - Self-reference forbidden: A course cannot be its own prerequisite.
    - DAG validation (Algorithm 03): Adding A -> B is rejected if B already reaches A.
    - Append-only AuditEvent logging.
    """
    sess = session if session is not None else db.session

    # 1. Permission check
    course = require_course_manager(actor, course_id, session=sess)

    # 2. Resolve prerequisite course
    prereq_course = _resolve_course(prerequisite_course_id, session=sess)
    if prereq_course is None:
        raise CourseNotFoundError("Prerequisite course not found.")

    # 2b. Invariant: Only PUBLISHED courses can be added as prerequisites
    if prereq_course.status != "PUBLISHED":
        raise CourseValidationError(
            f"Chỉ có thể chọn khóa học đã được xuất bản (PUBLISHED) làm môn tiên quyết. "
            f"Khóa học '{prereq_course.title}' hiện có trạng thái '{prereq_course.status}'."
        )

    # 3. Prevent self-reference
    if course.id == prereq_course.id:
        raise CourseValidationError("A course cannot be a prerequisite of itself.")

    # 4. Check if relation already exists (idempotent)
    existing = (
        sess.query(CoursePrerequisite)
        .filter_by(
            course_id=course.id,
            prerequisite_course_id=prereq_course.id,
        )
        .first()
    )
    if existing is not None:
        return existing

    # 5. DAG Cycle Detection (Algorithm 03)
    # If we add edge: course -> prereq_course (meaning course requires prereq_course),
    # a cycle would occur if prereq_course already transitively requires course.
    # We traverse the prerequisite graph starting from prereq_course.id.
    visited: set[int] = set()
    queue: list[int] = [prereq_course.id]

    while queue:
        curr_id = queue.pop(0)
        if curr_id == course.id:
            raise PrerequisiteCycleError(
                f"Adding prerequisite '{prereq_course.title}' to '{course.title}' "
                f"creates a cyclic dependency in the prerequisite graph."
            )
        if curr_id in visited:
            continue
        visited.add(curr_id)

        # Find all prerequisites of curr_id (what curr_id requires)
        child_links = (
            sess.query(CoursePrerequisite.prerequisite_course_id)
            .filter(CoursePrerequisite.course_id == curr_id)
            .all()
        )
        for (next_prereq_id,) in child_links:
            if next_prereq_id not in visited:
                queue.append(next_prereq_id)

    # 6. Determine approval status based on ownership
    is_own_course = (prereq_course.owner_instructor_id == actor.id) or getattr(actor, "is_admin", False)
    now = utc_now()
    initial_status = "APPROVED" if is_own_course else "PENDING_APPROVAL"

    link = CoursePrerequisite(
        course_id=course.id,
        prerequisite_course_id=prereq_course.id,
        created_by_user_id=actor.id,
        created_at=now,
        approval_status=initial_status,
        requested_by_user_id=actor.id if not is_own_course else None,
        requested_at=now if not is_own_course else None,
        reviewed_at=now if is_own_course else None,
        reviewed_by_user_id=actor.id if is_own_course else None,
        review_note="Tự động phê duyệt vì là môn học của cùng giảng viên phụ trách." if is_own_course else None,
    )
    sess.add(link)

    # 7. Record AuditEvent
    _record_prerequisite_audit_event(
        sess=sess,
        actor=actor,
        action="ADD_PREREQUISITE",
        course_id=course.id,
        prerequisite_course_id=prereq_course.id,
        reason=(
            f"Added prerequisite {prereq_course.course_code} ({prereq_course.id}) "
            f"to {course.course_code} ({course.id})"
        ),
    )
    sess.flush()

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return link


def remove_course_prerequisite(
    actor: User,
    course_id: int | uuid.UUID | str,
    prerequisite_course_id: int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> bool:
    """Remove a prerequisite dependency from a course.

    Invariants enforced:
    - Authorization: Course owner Instructor or Admin only.
    - Append-only AuditEvent logging.
    """
    sess = session if session is not None else db.session

    course = require_course_manager(actor, course_id, session=sess)
    prereq_course = _resolve_course(prerequisite_course_id, session=sess)
    if prereq_course is None:
        raise CourseNotFoundError("Prerequisite course not found.")

    link = (
        sess.query(CoursePrerequisite)
        .filter_by(
            course_id=course.id,
            prerequisite_course_id=prereq_course.id,
        )
        .first()
    )
    if link is None:
        return False

    sess.delete(link)

    _record_prerequisite_audit_event(
        sess=sess,
        actor=actor,
        action="REMOVE_PREREQUISITE",
        course_id=course.id,
        prerequisite_course_id=prereq_course.id,
        reason=(
            f"Removed prerequisite {prereq_course.course_code} ({prereq_course.id}) "
            f"from {course.course_code} ({course.id})"
        ),
    )
    sess.flush()

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return True


def get_course_prerequisites(
    course_id: Course | int | uuid.UUID | str,
    only_approved: bool = True,
    session: Session | scoped_session[Any] | None = None,
) -> list[Course]:
    """Retrieve all direct prerequisite courses for a given course."""
    sess = session if session is not None else db.session

    course = _resolve_course(course_id, session=sess)
    if course is None:
        raise CourseNotFoundError("Course not found.")

    query = (
        sess.query(Course)
        .join(
            CoursePrerequisite,
            CoursePrerequisite.prerequisite_course_id == Course.id,
        )
        .filter(CoursePrerequisite.course_id == course.id)
    )
    if only_approved:
        query = query.filter(CoursePrerequisite.approval_status == "APPROVED")
    return query.order_by(Course.course_code).all()


def get_incoming_prerequisite_requests(
    actor: User,
    status: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> list[dict[str, Any]]:
    """Retrieve incoming prerequisite requests for courses owned by actor."""
    sess = session if session is not None else db.session
    if actor is None or not actor.is_active:
        raise ForbiddenError("Authentication required.")

    query = (
        sess.query(CoursePrerequisite)
        .join(Course, CoursePrerequisite.prerequisite_course_id == Course.id)
    )
    if not getattr(actor, "is_admin", False):
        query = query.filter(Course.owner_instructor_id == actor.id)

    if status:
        query = query.filter(CoursePrerequisite.approval_status == status)

    links = query.order_by(CoursePrerequisite.created_at.desc()).all()
    results = []
    seen_pairs = set()
    for link in links:
        req_course = link.course
        target_course = link.prerequisite_course
        req_inst = req_course.owner_instructor if req_course else None
        seen_pairs.add((req_course.id, target_course.id))
        results.append({
            "id": f"{req_course.id}_{target_course.id}",
            "requesting_course_id": str(req_course.public_id),
            "requesting_course_code": req_course.course_code,
            "requesting_course_title": req_course.title,
            "requesting_instructor_id": str(req_inst.public_id) if req_inst else None,
            "requesting_instructor_name": req_inst.display_name if req_inst else "Giảng viên",
            "requesting_instructor_email": req_inst.email if req_inst else "",
            "prerequisite_course_id": str(target_course.public_id),
            "prerequisite_course_code": target_course.course_code,
            "prerequisite_course_title": target_course.title,
            "approval_status": link.approval_status,
            "requested_at": link.requested_at.isoformat() if link.requested_at else (link.created_at.isoformat() if link.created_at else None),
            "reviewed_at": link.reviewed_at.isoformat() if link.reviewed_at else None,
            "review_note": link.review_note or "",
        })

    # Also check CourseChangeRequest records
    from pwd301.models.course import CourseChangeRequest

    cr_query = (
        sess.query(CourseChangeRequest)
        .join(Course, CourseChangeRequest.target_id == Course.id)
        .filter(CourseChangeRequest.change_type == "PREREQUISITE")
    )
    if not getattr(actor, "is_admin", False):
        cr_query = cr_query.filter(Course.owner_instructor_id == actor.id)
    if status:
        cr_query = cr_query.filter(CourseChangeRequest.status == status)

    for cr in cr_query.order_by(CourseChangeRequest.created_at.desc()).all():
        pair = (cr.course_id, cr.target_id)
        if pair not in seen_pairs:
            seen_pairs.add(pair)
            req_c = sess.get(Course, cr.course_id)
            target_c = sess.get(Course, cr.target_id)
            if req_c and target_c:
                req_inst = req_c.owner_instructor
                p_data = {}
                if cr.proposed_payload_json:
                    with contextlib.suppress(Exception):
                        p_data = json.loads(cr.proposed_payload_json)
                results.append({
                    "id": f"{req_c.id}_{target_c.id}",
                    "requesting_course_id": str(req_c.public_id),
                    "requesting_course_code": req_c.course_code,
                    "requesting_course_title": req_c.title,
                    "requesting_instructor_id": str(req_inst.public_id) if req_inst else None,
                    "requesting_instructor_name": req_inst.display_name if req_inst else "Giảng viên",
                    "requesting_instructor_email": req_inst.email if req_inst else "",
                    "prerequisite_course_id": str(target_c.public_id),
                    "prerequisite_course_code": target_c.course_code,
                    "prerequisite_course_title": target_c.title,
                    "approval_status": "PENDING_APPROVAL" if cr.status == "PENDING" else cr.status,
                    "requested_at": cr.created_at.isoformat() if cr.created_at else None,
                    "reviewed_at": cr.reviewed_at.isoformat() if cr.reviewed_at else None,
                    "review_note": cr.review_reason or p_data.get("reason", ""),
                })

    return results


def count_incoming_prerequisite_requests(
    actor: User,
    session: Session | scoped_session[Any] | None = None,
) -> int:
    """Return count of PENDING_APPROVAL prerequisite requests targeting courses owned by actor."""
    sess = session if session is not None else db.session
    if actor is None or not actor.is_active:
        return 0

    incoming = get_incoming_prerequisite_requests(actor, status="PENDING_APPROVAL", session=sess)
    # Also include status='PENDING'
    incoming_pending = get_incoming_prerequisite_requests(actor, status="PENDING", session=sess)
    all_reqs = {r["id"] for r in incoming + incoming_pending}
    return len(all_reqs)


def review_prerequisite_request(
    actor: User,
    requesting_course_id: int | uuid.UUID | str,
    prerequisite_course_id: int | uuid.UUID | str,
    action: str,
    note: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> CoursePrerequisite:
    """Approve or reject a prerequisite request targeting an actor-owned course."""
    sess = session if session is not None else db.session
    if actor is None or not actor.is_active:
        raise ForbiddenError("Authentication required.")

    act_upper = action.strip().upper()
    if act_upper not in ("APPROVE", "REJECT", "APPROVED", "REJECTED"):
        raise CourseValidationError("Hành động xét duyệt phải là APPROVE hoặc REJECT.")
    new_status = "APPROVED" if "APPROVE" in act_upper else "REJECTED"

    req_course = _resolve_course(requesting_course_id, session=sess)
    target_course = _resolve_course(prerequisite_course_id, session=sess)
    if not req_course or not target_course:
        raise CourseNotFoundError("Khóa học không tồn tại.")

    if not getattr(actor, "is_admin", False) and target_course.owner_instructor_id != actor.id:
        raise ForbiddenError("Bạn không có quyền duyệt yêu cầu tiên quyết cho khóa học này.")

    from pwd301.models.course import CourseChangeRequest

    now = utc_now()
    review_msg = note.strip() if note else ("Đã phê duyệt" if new_status == "APPROVED" else "Từ chối liên kết")

    # Update any corresponding CourseChangeRequest
    cr = (
        sess.query(CourseChangeRequest)
        .filter_by(
            course_id=req_course.id,
            change_type="PREREQUISITE",
            target_id=target_course.id,
            status="PENDING",
        )
        .first()
    )
    if cr is not None:
        cr.status = new_status
        cr.reviewed_at = now
        cr.reviewed_by_user_id = actor.id
        cr.review_reason = review_msg
        if new_status == "APPROVED":
            cr.applied_at = now

    link = (
        sess.query(CoursePrerequisite)
        .filter_by(
            course_id=req_course.id,
            prerequisite_course_id=target_course.id,
        )
        .first()
    )

    if link is None:
        if new_status == "APPROVED":
            link = CoursePrerequisite(
                course_id=req_course.id,
                prerequisite_course_id=target_course.id,
                created_by_user_id=actor.id,
                created_at=now,
                approval_status="APPROVED",
                requested_by_user_id=cr.requested_by_user_id if cr else None,
                requested_at=cr.created_at if cr else now,
                reviewed_at=now,
                reviewed_by_user_id=actor.id,
                review_note=review_msg,
            )
            sess.add(link)
        else:
            # For REJECTED when no link existed, create link with REJECTED status so it's tracked
            link = CoursePrerequisite(
                course_id=req_course.id,
                prerequisite_course_id=target_course.id,
                created_by_user_id=actor.id,
                created_at=now,
                approval_status="REJECTED",
                requested_by_user_id=cr.requested_by_user_id if cr else None,
                requested_at=cr.created_at if cr else now,
                reviewed_at=now,
                reviewed_by_user_id=actor.id,
                review_note=review_msg,
            )
            sess.add(link)
    else:
        link.approval_status = new_status
        link.reviewed_at = now
        link.reviewed_by_user_id = actor.id
        link.review_note = review_msg

    _record_prerequisite_audit_event(
        sess=sess,
        actor=actor,
        action=f"PREREQUISITE_{new_status}",
        course_id=req_course.id,
        prerequisite_course_id=target_course.id,
        reason=f"Giảng viên {actor.display_name} đã {new_status} yêu cầu môn tiên quyết. Ghi chú: {review_msg}",
    )
    sess.flush()
    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return link


def get_student_enrollments(
    actor: User,
    student_id: int | uuid.UUID | str | None = None,
    status: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> list[Enrollment]:
    """Retrieve enrollments for a student, enforcing IDOR protection.

    Rules:
    - Students may view only their own enrollments.
    - Administrators have platform-wide oversight.
    """
    sess = session if session is not None else db.session

    if student_id is None:
        target_student = actor
    else:
        resolved = _resolve_user(student_id, session=sess)
        if resolved is None:
            raise UserNotFoundError("Student not found.")
        target_student = resolved

    if not actor.is_admin and actor.id != target_student.id:
        raise ForbiddenError("You are not authorized to view this student's enrollments.")

    query = sess.query(Enrollment).filter(Enrollment.student_user_id == target_student.id)
    if status is not None:
        query = query.filter(Enrollment.status == status)

    return query.order_by(Enrollment.enrolled_at.desc()).all()


def get_course_enrollments(
    actor: User,
    course_id: int | uuid.UUID | str,
    status: str | None = None,
    page: int = 1,
    per_page: int = 20,
    session: Session | scoped_session[Any] | None = None,
) -> tuple[list[Enrollment], int]:
    """Retrieve paginated student enrollments for a managed course.

    Rules:
    - Instructors may only access student data for courses they currently manage.
    - Administrators have platform-wide oversight.
    """
    sess = session if session is not None else db.session

    course = require_course_manager(actor, course_id, session=sess)

    query = sess.query(Enrollment).filter(Enrollment.course_id == course.id)
    if status is not None:
        query = query.filter(Enrollment.status == status)

    total = query.count()
    items = (
        query.order_by(Enrollment.enrolled_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return items, total
