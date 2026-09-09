"""Lesson management, reordering, and completion tracking service for PWD301.

Provides business logic for:
- Lesson creation, position calculation, and safe shift operations.
- Lesson metadata update with mass-assignment defense.
- Safe 2-phase contiguous reordering avoiding UniqueConstraint(course_id, position) collisions.
- Application-level soft-delete (TRASH) and position re-compaction.
- State transitions (DRAFT, PUBLISHED, HIDDEN) and lifecycle checks.
- Resource-level authorization and IDOR prevention for instructors and students.
- Monotonic lesson completion tracking adhering to Algorithm 02 (anti-tampering, idempotent).
- Append-only AuditEvent logging for structural modifications and soft-deletes.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy.orm import Session, scoped_session

from pwd301.extensions import db
from pwd301.models.course import (
    CourseChangeRequest,
    Enrollment,
    EnrollmentPeriod,
    Lesson,
    LessonProgress,
)
from pwd301.models.identity import User
from pwd301.models.notification_audit import AuditEvent
from pwd301.models.types import utc_now
from pwd301.services.authorization_service import (
    _resolve_course,
    _resolve_lesson,
    require_course_manager,
)
from pwd301.services.exceptions import (
    ForbiddenError,
    LessonNotFoundError,
    LessonPositionConflictError,
    LessonProgressError,
    LessonStateViolationError,
    LessonValidationError,
    ResourceNotFoundError,
)

# Allowed lesson statuses per check constraint ck_lessons_5
VALID_LESSON_STATUSES = {
    "DRAFT",
    "ACTIVE",
    "PUBLISHED",
    "PENDING_APPROVAL",
    "ARCHIVED",
    "HIDDEN",
    "TRASH",
    "HISTORICAL",
}

# Mass-assignment safe writable lesson fields
UPDATABLE_LESSON_FIELDS = {
    "title",
    "summary",
    "markdown_content",
    "estimated_duration_minutes",
    "minimum_completion_seconds",
    "viewed_fraction_required",
    "status",
}

# Maximum ping interval permitted for anti-tampering (in seconds)
MAX_PING_SECONDS = 60

# Temporary offset used to prevent unique constraint collisions on (course_id, position)
# Satisfies CheckConstraint("position > 0", name="ck_lessons_1")
TEMP_POSITION_OFFSET = 1_000_000

# Base offset for soft-deleted (TRASH) lessons to prevent colliding with active 1..N positions
TRASH_POSITION_BASE = 10_000_000


def _record_lesson_audit_event(
    sess: Session | scoped_session[Any],
    actor: User,
    action: str,
    target_id: int,
    reason: str | None = None,
    before_json: str | None = None,
    after_json: str | None = None,
) -> AuditEvent:
    """Record an append-only AuditEvent for lesson structural or lifecycle actions."""
    actor_roles = ",".join(sorted(actor.role_codes)) if actor.role_codes else "UNKNOWN"
    audit_entry = AuditEvent(
        actor_user_id=actor.id,
        actor_roles_snapshot=actor_roles,
        action=action,
        target_type="LESSON",
        target_id=target_id,
        reason=reason,
        before_json=before_json,
        after_json=after_json,
        performed_as_admin=actor.is_admin,
        created_at=utc_now(),
    )
    sess.add(audit_entry)
    return audit_entry


def create_lesson(
    actor: User,
    course_id: int | uuid.UUID | str,
    data: dict[str, Any],
    session: Session | scoped_session[Any] | None = None,
) -> Lesson:
    """Create a new lesson in a course with safe position assignment.

    Args:
        actor: Authenticated user initiating the creation (Instructor or Admin).
        course_id: Internal ID or public UUID of the course.
        data: Creation payload.
        session: Optional SQLAlchemy session.

    Returns:
        The newly created Lesson instance.

    Raises:
        ForbiddenError: If actor is not authorized to manage the course.
        ResourceNotFoundError: If the course does not exist.
        LessonStateViolationError: If course is archived or trashed.
        LessonValidationError: If input validation fails.
    """
    sess = session if session is not None else db.session
    course = require_course_manager(actor, course_id, session=sess)

    if course.deleted_at is not None or course.status in ("TRASH", "ARCHIVED"):
        raise LessonStateViolationError(
            f"Cannot add lessons to archived or trashed course in '{course.status}' status."
        )

    # Validate title
    title = data.get("title")
    if not title or not isinstance(title, str) or not title.strip():
        raise LessonValidationError("Lesson title is required and cannot be empty.")
    clean_title = title.strip()
    if len(clean_title) > 200:
        raise LessonValidationError("Lesson title cannot exceed 200 characters.")

    # Validate markdown_content
    markdown_content = data.get("markdown_content")
    if (
        not markdown_content
        or not isinstance(markdown_content, str)
        or not markdown_content.strip()
    ):
        raise LessonValidationError("Lesson markdown_content is required and cannot be empty.")
    clean_markdown = markdown_content.strip()

    # Validate summary (optional)
    summary = data.get("summary")
    clean_summary = None
    if summary is not None:
        clean_summary = str(summary).strip()
        if len(clean_summary) > 1000:
            raise LessonValidationError("Lesson summary cannot exceed 1000 characters.")

    # Validate estimated_duration_minutes (optional)
    est_duration = data.get("estimated_duration_minutes")
    if est_duration is not None:
        try:
            est_duration = int(est_duration)
        except (ValueError, TypeError):
            raise LessonValidationError(
                "estimated_duration_minutes must be a valid integer."
            ) from None
        if est_duration <= 0:
            raise LessonValidationError("estimated_duration_minutes must be greater than zero.")

    # Validate minimum_completion_seconds
    min_completion_seconds = data.get("minimum_completion_seconds", 30)
    try:
        min_completion_seconds = int(min_completion_seconds)
    except (ValueError, TypeError):
        raise LessonValidationError("minimum_completion_seconds must be a valid integer.") from None
    if min_completion_seconds < 0:
        raise LessonValidationError("minimum_completion_seconds cannot be negative.")

    # Validate viewed_fraction_required
    viewed_fraction_required = data.get("viewed_fraction_required", 0.8000)
    try:
        viewed_fraction_required = float(viewed_fraction_required)
    except (ValueError, TypeError):
        raise LessonValidationError("viewed_fraction_required must be a float.") from None
    if not (0.0 <= viewed_fraction_required <= 1.0):
        raise LessonValidationError("viewed_fraction_required must be between 0.0 and 1.0.")

    # Validate status
    status = data.get("status", "DRAFT")
    if status not in VALID_LESSON_STATUSES:
        raise LessonValidationError(f"Invalid initial lesson status: {status}.")

    published_at = utc_now() if status in ("PUBLISHED", "ACTIVE") else None

    # Calculate position and shift if needed
    active_lessons = (
        sess.query(Lesson)
        .filter(Lesson.course_id == course.id, Lesson.deleted_at.is_(None))
        .order_by(Lesson.position.asc())
        .all()
    )
    max_position = len(active_lessons)
    requested_position = data.get("position")
    change_req_id = data.get("change_request_id")

    if change_req_id or status == "PENDING_APPROVAL":
        # Staged lesson targeting a position for future approval
        assigned_position = (
            int(requested_position) if requested_position is not None else (max_position + 1)
        )
    elif requested_position is None:
        assigned_position = max_position + 1
    else:
        try:
            req_pos = int(requested_position)
        except (ValueError, TypeError):
            raise LessonValidationError("Position must be a valid integer.") from None
        if req_pos <= 0:
            raise LessonValidationError("Position must be greater than zero.")
        if req_pos > max_position + 1:
            assigned_position = max_position + 1
        else:
            # Shift existing lessons with position >= req_pos
            # Phase 1: assign temporary non-colliding positions
            for les in active_lessons:
                if les.position >= req_pos:
                    les.position = les.position + TEMP_POSITION_OFFSET
            sess.flush()
            # Phase 2: assign shifted positions (+1)
            for les in active_lessons:
                if les.position > TEMP_POSITION_OFFSET:
                    les.position = (les.position - TEMP_POSITION_OFFSET) + 1
            sess.flush()
            assigned_position = req_pos

    lesson = Lesson(
        course_id=course.id,
        change_request_id=change_req_id,
        title=clean_title,
        summary=clean_summary,
        markdown_content=clean_markdown,
        position=assigned_position,
        estimated_duration_minutes=est_duration,
        minimum_completion_seconds=min_completion_seconds,
        viewed_fraction_required=viewed_fraction_required,
        status=status,
        published_at=published_at,
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    sess.add(lesson)
    sess.flush()

    # Append-only audit logging if course is published
    if course.status == "PUBLISHED":
        after_payload = json.dumps(
            {
                "lesson_id": lesson.id,
                "title": lesson.title,
                "position": lesson.position,
                "status": lesson.status,
            }
        )
        _record_lesson_audit_event(
            sess=sess,
            actor=actor,
            action="LESSON_CREATED",
            target_id=lesson.id,
            reason="Created new lesson in published course",
            after_json=after_payload,
        )

    if session is None:
        sess.commit()

    return lesson


def update_lesson(
    actor: User,
    lesson_id: int | uuid.UUID | str,
    data: dict[str, Any],
    session: Session | scoped_session[Any] | None = None,
) -> Lesson:
    """Update editable lesson fields with strict mass-assignment defense.

    Args:
        actor: Authenticated user initiating the update (Instructor or Admin).
        lesson_id: Identifier of the lesson.
        data: Dictionary of fields to update.
        session: Optional SQLAlchemy session.

    Returns:
        The updated Lesson instance.

    Raises:
        LessonNotFoundError: If lesson does not exist.
        ForbiddenError: If actor cannot manage the course.
        LessonValidationError: If mass assignment or validation violation occurs.
        LessonStateViolationError: If an invalid state change is attempted.
    """
    sess = session if session is not None else db.session
    lesson = _resolve_lesson(lesson_id, session=sess)
    if lesson is None:
        raise LessonNotFoundError("Lesson not found.")

    course = require_course_manager(actor, lesson.course_id, session=sess)

    # Disallow modifying position via update_lesson
    if "position" in data and data["position"] != lesson.position:
        raise LessonValidationError(
            "Lesson position cannot be modified via update. Use reorder_lessons."
        )

    before_snapshot = {
        "title": lesson.title,
        "summary": lesson.summary,
        "status": lesson.status,
        "estimated_duration_minutes": lesson.estimated_duration_minutes,
        "minimum_completion_seconds": lesson.minimum_completion_seconds,
        "viewed_fraction_required": float(lesson.viewed_fraction_required),
    }

    # Validate and apply writable fields
    if "title" in data:
        title = data["title"]
        if not title or not isinstance(title, str) or not title.strip():
            raise LessonValidationError("Lesson title cannot be empty.")
        clean_title = title.strip()
        if len(clean_title) > 200:
            raise LessonValidationError("Lesson title cannot exceed 200 characters.")
        lesson.title = clean_title

    if "markdown_content" in data:
        md = data["markdown_content"]
        if not md or not isinstance(md, str) or not md.strip():
            raise LessonValidationError("Lesson markdown_content cannot be empty.")
        lesson.markdown_content = md.strip()

    if "summary" in data:
        summary = data["summary"]
        if summary is not None:
            clean_sum = str(summary).strip()
            if len(clean_sum) > 1000:
                raise LessonValidationError("Lesson summary cannot exceed 1000 characters.")
            lesson.summary = clean_sum
        else:
            lesson.summary = None

    if "estimated_duration_minutes" in data:
        est = data["estimated_duration_minutes"]
        if est is not None:
            try:
                est = int(est)
            except (ValueError, TypeError):
                raise LessonValidationError(
                    "estimated_duration_minutes must be a valid integer."
                ) from None
            if est <= 0:
                raise LessonValidationError("estimated_duration_minutes must be greater than zero.")
            lesson.estimated_duration_minutes = est
        else:
            lesson.estimated_duration_minutes = None

    if "minimum_completion_seconds" in data:
        try:
            mcs = int(data["minimum_completion_seconds"])
        except (ValueError, TypeError):
            raise LessonValidationError(
                "minimum_completion_seconds must be a valid integer."
            ) from None
        if mcs < 0:
            raise LessonValidationError("minimum_completion_seconds cannot be negative.")
        lesson.minimum_completion_seconds = mcs

    if "viewed_fraction_required" in data:
        try:
            vfr = float(data["viewed_fraction_required"])
        except (ValueError, TypeError):
            raise LessonValidationError("viewed_fraction_required must be a valid float.") from None
        if not (0.0 <= vfr <= 1.0):
            raise LessonValidationError("viewed_fraction_required must be between 0.0 and 1.0.")
        lesson.viewed_fraction_required = vfr

    if "status" in data:
        new_status = data["status"]
        if new_status not in ("DRAFT", "PUBLISHED", "HIDDEN"):
            raise LessonValidationError(f"Invalid lesson status: {new_status}.")
        if new_status == "PUBLISHED" and course.status in ("TRASH", "ARCHIVED"):
            raise LessonStateViolationError(
                f"Cannot publish lesson in a course with '{course.status}' status."
            )
        if new_status == "PUBLISHED" and lesson.published_at is None:
            lesson.published_at = utc_now()
        lesson.status = new_status

    lesson.updated_at = utc_now()
    sess.flush()

    # Audit logging for published courses
    if course.status == "PUBLISHED":
        after_snapshot = {
            "title": lesson.title,
            "summary": lesson.summary,
            "status": lesson.status,
            "estimated_duration_minutes": lesson.estimated_duration_minutes,
            "minimum_completion_seconds": lesson.minimum_completion_seconds,
            "viewed_fraction_required": float(lesson.viewed_fraction_required),
        }
        _record_lesson_audit_event(
            sess=sess,
            actor=actor,
            action="LESSON_UPDATED",
            target_id=lesson.id,
            reason="Updated lesson metadata",
            before_json=json.dumps(before_snapshot),
            after_json=json.dumps(after_snapshot),
        )

    if session is None:
        sess.commit()

    return lesson


def reorder_lessons(
    actor: User,
    course_id: int | uuid.UUID | str,
    ordered_lesson_ids: list[int | uuid.UUID | str],
    session: Session | scoped_session[Any] | None = None,
) -> list[Lesson]:
    """Reorder lessons to maintain a contiguous 1..N sequence without unique collisions.

    Uses a 2-phase update with temporary positive offsets within the same transaction.

    Args:
        actor: Authenticated user initiating reordering.
        course_id: Identifier of the course.
        ordered_lesson_ids: Full ordered list of lesson IDs representing new sequence.
        session: Optional SQLAlchemy session.

    Returns:
        List of reordered Lesson instances sorted by new position.

    Raises:
        LessonPositionConflictError: If ordered_lesson_ids does not match course active lessons.
        ForbiddenError: If actor cannot manage course.
        ResourceNotFoundError: If course is not found.
    """
    sess = session if session is not None else db.session
    course = require_course_manager(actor, course_id, session=sess)

    active_lessons = (
        sess.query(Lesson).filter(Lesson.course_id == course.id, Lesson.deleted_at.is_(None)).all()
    )

    if not ordered_lesson_ids and not active_lessons:
        return []

    # Map existing active lessons by internal id and string/UUID public_id
    id_map: dict[int, Lesson] = {les.id: les for les in active_lessons}
    public_id_map: dict[str, Lesson] = {str(les.public_id): les for les in active_lessons}

    resolved_ordered: list[Lesson] = []
    seen_ids: set[int] = set()

    for item in ordered_lesson_ids:
        matched: Lesson | None = None
        if isinstance(item, int):
            matched = id_map.get(item)
        elif isinstance(item, uuid.UUID):
            matched = public_id_map.get(str(item))
        elif isinstance(item, str):
            if item.isdigit():
                matched = id_map.get(int(item))
            if matched is None:
                matched = public_id_map.get(item.strip().lower())

        if matched is None:
            raise LessonPositionConflictError(
                f"Lesson identifier '{item}' is not an active lesson in this course."
            )

        if matched.id in seen_ids:
            raise LessonPositionConflictError(
                f"Duplicate lesson identifier '{item}' provided in reorder list."
            )

        seen_ids.add(matched.id)
        resolved_ordered.append(matched)

    if len(seen_ids) != len(active_lessons):
        err_msg = (
            f"Reorder list contains {len(seen_ids)} lessons, "
            f"but course has {len(active_lessons)} active lessons."
        )
        raise LessonPositionConflictError(err_msg)

    # Safe 2-phase reordering to prevent UNIQUE (course_id, position) collisions
    # Phase 1: Assign temporary positive offset positions
    for idx, les in enumerate(active_lessons):
        les.position = TEMP_POSITION_OFFSET + idx + 1
    sess.flush()

    # Phase 2: Assign target contiguous positions 1..N
    for idx, les in enumerate(resolved_ordered):
        les.position = idx + 1
        les.updated_at = utc_now()
    sess.flush()

    # Append-only audit logging
    order_records = [{"lesson_id": les.id, "position": les.position} for les in resolved_ordered]
    order_snapshot = json.dumps(order_records)
    _record_lesson_audit_event(
        sess=sess,
        actor=actor,
        action="LESSON_REORDERED",
        target_id=course.id,
        reason="Reordered lessons sequence",
        after_json=order_snapshot,
    )

    if session is None:
        sess.commit()

    return resolved_ordered


def trash_lesson(
    actor: User,
    lesson_id: int | uuid.UUID | str,
    reason: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> Lesson:
    """Soft-delete a lesson to TRASH and compact positions of remaining lessons.

    Args:
        actor: Authenticated user initiating deletion.
        lesson_id: Identifier of the lesson.
        reason: Optional audit reason.
        session: Optional SQLAlchemy session.

    Returns:
        The soft-deleted Lesson instance.

    Raises:
        LessonNotFoundError: If lesson does not exist.
        ForbiddenError: If actor cannot manage the course.
    """
    sess = session if session is not None else db.session
    lesson = _resolve_lesson(lesson_id, session=sess)
    if lesson is None:
        raise LessonNotFoundError("Lesson not found.")

    course = require_course_manager(actor, lesson.course_id, session=sess)

    if lesson.deleted_at is not None or lesson.status == "TRASH":
        return lesson

    before_pos = lesson.position
    now = utc_now()
    lesson.deleted_at = now
    lesson.deleted_by_user_id = actor.id
    lesson.status = "TRASH"
    # Move position out of active 1..N range to prevent unique constraint collision
    lesson.position = TRASH_POSITION_BASE + lesson.id
    lesson.updated_at = now
    sess.flush()

    # Re-compact remaining active lessons to contiguous 1..(N-1)
    remaining_lessons = (
        sess.query(Lesson)
        .filter(Lesson.course_id == course.id, Lesson.deleted_at.is_(None))
        .order_by(Lesson.position.asc())
        .all()
    )

    # Phase 1: assign temporary offsets
    for idx, rem in enumerate(remaining_lessons):
        rem.position = TEMP_POSITION_OFFSET + idx + 1
    sess.flush()

    # Phase 2: assign clean contiguous 1..N
    for idx, rem in enumerate(remaining_lessons):
        rem.position = idx + 1
        rem.updated_at = now
    sess.flush()

    # Mandatory append-only AuditEvent
    _record_lesson_audit_event(
        sess=sess,
        actor=actor,
        action="LESSON_TRASHED",
        target_id=lesson.id,
        reason=reason or f"Soft-deleted lesson formerly at position {before_pos}",
        before_json=json.dumps({"position": before_pos, "status": "ACTIVE"}),
        after_json=json.dumps({"status": "TRASH", "deleted_at": now.isoformat()}),
    )

    if session is None:
        sess.commit()

    return lesson


def change_lesson_status(
    actor: User,
    lesson_id: int | uuid.UUID | str,
    new_status: str,
    reason: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> Lesson:
    """Change status of a lesson (DRAFT, PUBLISHED, HIDDEN).

    Args:
        actor: Authenticated user.
        lesson_id: Identifier of the lesson.
        new_status: Target status.
        reason: Optional audit reason.
        session: Optional SQLAlchemy session.

    Returns:
        The updated Lesson instance.

    Raises:
        LessonNotFoundError: If lesson not found.
        ForbiddenError: If unauthorized.
        LessonValidationError: If status is invalid.
        LessonStateViolationError: If course state prevents publishing.
    """
    sess = session if session is not None else db.session
    lesson = _resolve_lesson(lesson_id, session=sess)
    if lesson is None:
        raise LessonNotFoundError("Lesson not found.")

    course = require_course_manager(actor, lesson.course_id, session=sess)

    if new_status not in VALID_LESSON_STATUSES:
        valid_str = ", ".join(sorted(VALID_LESSON_STATUSES))
        raise LessonValidationError(
            f"Invalid status: '{new_status}'. Allowed transitions: {valid_str}."
        )

    if new_status == "PUBLISHED" and course.status in ("TRASH", "ARCHIVED"):
        raise LessonStateViolationError(
            f"Cannot publish lesson in a course with '{course.status}' status."
        )

    old_status = lesson.status
    lesson.status = new_status
    if new_status == "PUBLISHED" and lesson.published_at is None:
        lesson.published_at = utc_now()
    lesson.updated_at = utc_now()
    sess.flush()

    # Record AuditEvent when making public or hiding
    _record_lesson_audit_event(
        sess=sess,
        actor=actor,
        action="LESSON_STATUS_CHANGED",
        target_id=lesson.id,
        reason=reason or f"Changed lesson status from {old_status} to {new_status}",
        before_json=json.dumps({"status": old_status}),
        after_json=json.dumps({"status": new_status}),
    )

    if session is None:
        sess.commit()

    return lesson


def get_lesson_detail(
    actor: User | None,
    lesson_id: int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> Lesson:
    """Retrieve detailed lesson content adhering to role-based and enrollment guards.

    Rules:
    - Instructor managing this course / Admin: can read any status.
    - Student: must have an ACTIVE enrollment in this course, and lesson must be PUBLISHED.
    - Inactive / Soft-deleted: inaccessible to non-admins.

    Args:
        actor: The user requesting the lesson.
        lesson_id: Identifier of the lesson.
        session: Optional SQLAlchemy session.

    Returns:
        The Lesson instance.

    Raises:
        LessonNotFoundError: If lesson does not exist or is hidden/deleted.
        ForbiddenError: If actor lacks active enrollment or permissions.
    """
    sess = session if session is not None else db.session
    lesson = _resolve_lesson(lesson_id, session=sess)
    if lesson is None:
        raise LessonNotFoundError("Lesson not found.")

    course = _resolve_course(lesson.course_id, session=sess)
    if course is None:
        raise LessonNotFoundError("Course not found.")

    # Admin oversight
    if actor is not None and actor.is_active and actor.is_admin:
        return lesson

    # Soft-deleted lessons hidden from non-admins
    if lesson.deleted_at is not None:
        raise LessonNotFoundError("Lesson not found.")

    # Managing instructor
    if (
        actor is not None
        and actor.is_active
        and actor.has_role("INSTRUCTOR")
        and course.owner_instructor_id == actor.id
    ):
        return lesson

    # Student access guard:
    # Must be authenticated, course not deleted, lesson PUBLISHED, and student actively enrolled
    if actor is None or not actor.is_active:
        raise ForbiddenError("Authentication required to access lesson.")

    is_accessible = (
        lesson.status == "PUBLISHED"
        and course.deleted_at is None
        and course.status not in ("TRASH", "ARCHIVED")
    )
    if not is_accessible:
        raise ForbiddenError("You do not have permission to view this lesson.")

    enrollment = (
        sess.query(Enrollment)
        .filter(
            Enrollment.student_user_id == actor.id,
            Enrollment.course_id == course.id,
            Enrollment.status == "ACTIVE",
        )
        .first()
    )
    if enrollment is None:
        raise ForbiddenError("Active course enrollment required to view this lesson.")

    return lesson


def get_course_lessons(
    actor: User | None,
    course_id: int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> list[Lesson]:
    """Retrieve ordered lessons for a course scoped by caller permissions.

    Args:
        actor: The requesting actor.
        course_id: Identifier of the course.
        session: Optional SQLAlchemy session.

    Returns:
        List of Lesson instances ordered by position ascending.
    """
    sess = session if session is not None else db.session
    course = _resolve_course(course_id, session=sess)
    if course is None:
        raise ResourceNotFoundError("Course not found.")

    # Admin or managing instructor sees all non-deleted lessons
    if (
        actor is not None
        and actor.is_active
        and (
            actor.is_admin
            or (actor.has_role("INSTRUCTOR") and course.owner_instructor_id == actor.id)
        )
    ):
        return (
            sess.query(Lesson)
            .filter(Lesson.course_id == course.id, Lesson.deleted_at.is_(None))
            .order_by(Lesson.position.asc())
            .all()
        )

    # Others see only PUBLISHED lessons of active courses
    if course.deleted_at is not None or course.status in ("TRASH", "ARCHIVED"):
        return []

    return (
        sess.query(Lesson)
        .filter(
            Lesson.course_id == course.id,
            Lesson.status == "PUBLISHED",
            Lesson.deleted_at.is_(None),
        )
        .order_by(Lesson.position.asc())
        .all()
    )


def record_lesson_progress(
    actor: User,
    lesson_id: int | uuid.UUID | str,
    seconds_increment: int,
    view_fraction: float,
    session: Session | scoped_session[Any] | None = None,
) -> LessonProgress:
    """Record learning engagement heartbeat and evaluate monotonic completion (Algorithm 02).

    Inputs:
    - actor: The enrolled student.
    - seconds_increment: Active viewing delta (bounded anti-tampering: 1..60 seconds).
    - view_fraction: Observed scroll/content evidence ratio: [0.0, 1.0].

    Invariants enforced:
    - Student must have ACTIVE Enrollment and ACTIVE EnrollmentPeriod.
    - Lesson must be in PUBLISHED status.
    - Completion is monotonic: once completed_at is set, it cannot be cleared.
    - Derived cache (enrollment.current_progress_percent) is recomputed.

    Args:
        actor: Authenticated student.
        lesson_id: Identifier of the lesson.
        seconds_increment: Seconds of engagement observed in this ping interval.
        view_fraction: Cumulative content ratio observed.
        session: Optional SQLAlchemy session.

    Returns:
        The updated LessonProgress record.

    Raises:
        LessonNotFoundError: If lesson does not exist.
        ForbiddenError: If student is not actively enrolled.
        LessonStateViolationError: If lesson is not published.
        LessonValidationError: If ping parameters violate bounds.
        LessonProgressError: If no active enrollment period exists.
    """
    sess = session if session is not None else db.session

    if actor is None or not actor.is_active:
        raise ForbiddenError("Authentication required to record progress.")

    lesson = _resolve_lesson(lesson_id, session=sess)
    if lesson is None:
        raise LessonNotFoundError("Lesson not found.")

    if lesson.deleted_at is not None or lesson.status != "PUBLISHED":
        raise LessonStateViolationError(
            "Cannot record progress on an unpublished or deleted lesson."
        )

    # Anti-tampering validation
    try:
        sec = int(seconds_increment)
    except (ValueError, TypeError):
        raise LessonValidationError("seconds_increment must be an integer.") from None
    if sec <= 0 or sec > MAX_PING_SECONDS:
        raise LessonValidationError(
            f"seconds_increment must be between 1 and {MAX_PING_SECONDS} seconds."
        )

    try:
        vf = float(view_fraction)
    except (ValueError, TypeError):
        raise LessonValidationError("view_fraction must be a float.") from None
    if not (0.0 <= vf <= 1.0):
        raise LessonValidationError("view_fraction must be between 0.0 and 1.0.")

    # Verify student enrollment (ACTIVE or COMPLETED)
    enrollment = (
        sess.query(Enrollment)
        .filter(
            Enrollment.student_user_id == actor.id,
            Enrollment.course_id == lesson.course_id,
            Enrollment.status.in_(["ACTIVE", "COMPLETED"]),
        )
        .first()
    )
    if enrollment is None:
        raise ForbiddenError(
            "You must have an active enrollment in this course to record progress."
        )

    # Resolve active enrollment period
    active_period: EnrollmentPeriod | None = None
    if enrollment.current_period_id:
        active_period = sess.get(EnrollmentPeriod, enrollment.current_period_id)
        if active_period is not None and active_period.status not in ("ACTIVE", "COMPLETED"):
            active_period = None

    if active_period is None:
        active_period = (
            sess.query(EnrollmentPeriod)
            .filter(
                EnrollmentPeriod.enrollment_id == enrollment.id,
                EnrollmentPeriod.status.in_(["ACTIVE", "COMPLETED"]),
            )
            .order_by(EnrollmentPeriod.period_no.desc())
            .first()
        )

    if active_period is None:
        raise LessonProgressError("No active enrollment period found for this student.")

    # Find or create LessonProgress record
    progress = (
        sess.query(LessonProgress)
        .filter(
            LessonProgress.enrollment_period_id == active_period.id,
            LessonProgress.lesson_id == lesson.id,
        )
        .first()
    )

    now = utc_now()
    if progress is None:
        progress = LessonProgress(
            enrollment_period_id=active_period.id,
            lesson_id=lesson.id,
            seconds_spent=0,
            max_view_fraction=0.0,
            updated_at=now,
        )
        sess.add(progress)
        sess.flush()

    # Bounded accumulated active seconds & high-water-mark view fraction
    progress.seconds_spent = (progress.seconds_spent or 0) + sec
    current_fraction = float(progress.max_view_fraction or 0.0)
    progress.max_view_fraction = max(current_fraction, vf)
    progress.last_activity_at = now
    progress.updated_at = now

    # Evaluate completion: monotonic, idempotent
    min_completion_seconds = lesson.minimum_completion_seconds
    viewed_fraction_required = float(lesson.viewed_fraction_required)

    criteria_met = (
        progress.seconds_spent >= min_completion_seconds
        and float(progress.max_view_fraction) >= viewed_fraction_required
    )

    newly_completed = False
    if criteria_met and progress.completed_at is None:
        progress.completed_at = now
        progress.completion_rule_snapshot_json = json.dumps(
            {
                "minimum_completion_seconds": min_completion_seconds,
                "viewed_fraction_required": viewed_fraction_required,
                "completed_at": now.isoformat(),
            }
        )
        newly_completed = True

    # Update derived progress cache on Enrollment via Algorithm 01
    from pwd301.services.completion_service import (
        calculate_course_progress,
        evaluate_course_completion,
    )

    calculate_course_progress(enrollment.id, session=sess)

    # Immediately evaluate course completion when lesson completes
    if newly_completed:
        evaluate_course_completion(enrollment.id, session=sess)

    sess.flush()

    if session is None:
        sess.commit()

    return progress


def get_lesson_progress(
    actor: User,
    lesson_id: int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> LessonProgress | None:
    """Retrieve the current student's progress for a lesson.

    Args:
        actor: Authenticated student.
        lesson_id: Identifier of the lesson.
        session: Optional SQLAlchemy session.

    Returns:
        The LessonProgress instance or None if no engagement yet recorded.
    """
    sess = session if session is not None else db.session
    lesson = _resolve_lesson(lesson_id, session=sess)
    if lesson is None:
        raise LessonNotFoundError("Lesson not found.")

    enrollment = (
        sess.query(Enrollment)
        .filter(
            Enrollment.student_user_id == actor.id,
            Enrollment.course_id == lesson.course_id,
            Enrollment.status == "ACTIVE",
        )
        .first()
    )
    if enrollment is None or not enrollment.current_period_id:
        return None

    return (
        sess.query(LessonProgress)
        .filter(
            LessonProgress.enrollment_period_id == enrollment.current_period_id,
            LessonProgress.lesson_id == lesson.id,
        )
        .first()
    )


def create_lesson_change_request(
    actor: User,
    course_id: int | uuid.UUID | str,
    payload: dict[str, Any],
    session: Session | scoped_session[Any] | None = None,
) -> tuple[CourseChangeRequest, Lesson]:
    """Create a relational staged lesson change request (Defect 6).

    Creates a CourseChangeRequest and a corresponding Lesson in 'PENDING_APPROVAL' status,
    linked via change_request_id. Avoids JSON de-normalization while respecting the
    filtered unique index uq_lessons_course_position_active.
    """
    sess = session if session is not None else db.session
    course = require_course_manager(actor, course_id, session=sess)

    req = CourseChangeRequest(
        course_id=course.id,
        requested_by_user_id=actor.id,
        change_type=payload.get("change_type", "LESSON_STRUCTURE"),
        target_type="LESSON",
        target_id=payload.get("target_id"),
        proposed_payload_json=json.dumps(payload, default=str),
        status="PENDING",
        created_at=utc_now(),
    )
    sess.add(req)
    sess.flush()

    lesson_data = dict(payload)
    lesson_data["status"] = "PENDING_APPROVAL"
    lesson_data["change_request_id"] = req.id
    staged_lesson = create_lesson(actor, course.id, lesson_data, session=sess)
    req.target_id = staged_lesson.id
    sess.flush()
    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return req, staged_lesson


def approve_course_change_request(
    actor: User,
    change_request_id: int | uuid.UUID | str,
    review_reason: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> CourseChangeRequest:
    """Approve a course change request and promote staged lessons atomically (Defect 6).

    For any staged lesson linked to the request:
    - Retires any currently active/published lesson at the same position by
      setting status='HISTORICAL'.
    - Activates the staged lesson by setting status='PUBLISHED'.
    - Marks the change request APPROVED.
    All done within a single transaction without violating uq_lessons_course_position_active.
    """
    sess = session if session is not None else db.session

    req = sess.get(CourseChangeRequest, change_request_id)
    if req is None:
        raise ResourceNotFoundError("Course change request not found.")

    require_course_manager(actor, req.course_id, session=sess)

    if req.status != "PENDING":
        raise LessonStateViolationError(f"Cannot approve change request in '{req.status}' status.")

    now = utc_now()

    # Find staged lessons for this request
    staged_lessons = sess.query(Lesson).filter(Lesson.change_request_id == req.id).all()

    for staged in staged_lessons:
        # Check if there is an active/published lesson at the same position
        active_at_pos = (
            sess.query(Lesson)
            .filter(
                Lesson.course_id == req.course_id,
                Lesson.position == staged.position,
                Lesson.status.in_(["ACTIVE", "PUBLISHED"]),
                Lesson.id != staged.id,
                Lesson.deleted_at.is_(None),
            )
            .first()
        )
        if active_at_pos is not None:
            active_at_pos.status = "HISTORICAL"
            active_at_pos.updated_at = now
            sess.flush()

        staged.status = "PUBLISHED"
        if staged.published_at is None:
            staged.published_at = now
        staged.updated_at = now
        sess.flush()

    req.status = "APPROVED"
    req.reviewed_by_user_id = actor.id
    req.review_reason = review_reason
    req.reviewed_at = now
    req.applied_at = now
    sess.flush()

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return req


def reject_course_change_request(
    actor: User,
    change_request_id: int | uuid.UUID | str,
    review_reason: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> CourseChangeRequest:
    """Reject a course change request and trash its staged lessons."""
    sess = session if session is not None else db.session

    req = sess.get(CourseChangeRequest, change_request_id)
    if req is None:
        raise ResourceNotFoundError("Course change request not found.")

    require_course_manager(actor, req.course_id, session=sess)

    if req.status != "PENDING":
        raise LessonStateViolationError(f"Cannot reject change request in '{req.status}' status.")

    now = utc_now()
    staged_lessons = sess.query(Lesson).filter(Lesson.change_request_id == req.id).all()
    for staged in staged_lessons:
        staged.status = "TRASH"
        staged.deleted_at = now
        staged.updated_at = now

    req.status = "REJECTED"
    req.reviewed_by_user_id = actor.id
    req.review_reason = review_reason
    req.reviewed_at = now
    sess.flush()

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return req
