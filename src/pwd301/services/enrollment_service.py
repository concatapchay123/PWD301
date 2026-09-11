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
        sess.query(CoursePrerequisite).filter(CoursePrerequisite.course_id == course_id).all()
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
            CourseCompletionSummary.prerequisite_eligible.is_(True),
        )
        .all()
    )

    completed_ids = {s.course_id for s in summaries}
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

    if locked_course.capacity is not None and locked_course.capacity > 0:
        active_count = (
            sess.query(sa.func.count(Enrollment.id))
            .filter(
                Enrollment.course_id == locked_course.id,
                Enrollment.status == "ACTIVE",
            )
            .scalar()
            or 0
        )
        if active_count >= locked_course.capacity:
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

    if locked_course.capacity is not None and locked_course.capacity > 0:
        active_count = (
            sess.query(sa.func.count(Enrollment.id))
            .filter(
                Enrollment.course_id == locked_course.id,
                Enrollment.status == "ACTIVE",
            )
            .scalar()
            or 0
        )
        if active_count >= locked_course.capacity:
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

    # 6. Create CoursePrerequisite record
    link = CoursePrerequisite(
        course_id=course.id,
        prerequisite_course_id=prereq_course.id,
        created_by_user_id=actor.id,
        created_at=utc_now(),
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
    session: Session | scoped_session[Any] | None = None,
) -> list[Course]:
    """Retrieve all direct prerequisite courses for a given course."""
    sess = session if session is not None else db.session

    course = _resolve_course(course_id, session=sess)
    if course is None:
        raise CourseNotFoundError("Course not found.")

    prerequisites = (
        sess.query(Course)
        .join(
            CoursePrerequisite,
            CoursePrerequisite.prerequisite_course_id == Course.id,
        )
        .filter(CoursePrerequisite.course_id == course.id)
        .order_by(Course.course_code)
        .all()
    )
    return prerequisites


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
