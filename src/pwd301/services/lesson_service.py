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

import contextlib
import datetime
import json
import re
import time
import uuid
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Session, scoped_session

from pwd301.extensions import db
from pwd301.models.course import (
    Course,
    CourseChangeRequest,
    Enrollment,
    EnrollmentPeriod,
    LearningUnit,
    Lesson,
    LessonProgress,
)
from pwd301.models.file_import import FileAsset
from pwd301.models.identity import Role, User
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


def create_learning_unit(
    actor: User,
    course_id: int | uuid.UUID | str,
    data: dict[str, Any],
    session: Session | scoped_session[Any] | None = None,
) -> LearningUnit:
    """Create an instructor-facing lesson group in an authorized course."""
    sess = session if session is not None else db.session
    course = require_course_manager(actor, course_id, session=sess)
    if course.deleted_at is not None or course.status in ("TRASH", "ARCHIVED"):
        raise LessonStateViolationError("Cannot add a learning unit to this course.")
    if course.status == "SUBMITTED_FOR_REVIEW" and not actor.is_admin:
        raise LessonStateViolationError(
            "Khóa học đang chờ Quản trị viên xét duyệt. Không thể thêm chương mục mới."
        )
    title = data.get("title")
    if not isinstance(title, str) or not title.strip() or len(title.strip()) > 200:
        raise LessonValidationError("Learning unit title must have 1 to 200 characters.")
    position = (
        sess.query(sa.func.max(LearningUnit.position))
        .filter(LearningUnit.course_id == course.id)
        .scalar()
        or 0
    ) + 1
    unit = LearningUnit(course_id=course.id, title=title.strip(), position=position)
    sess.add(unit)
    sess.flush()
    if session is None:
        sess.commit()
    return unit


def list_learning_units(
    actor: User,
    course_id: int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> list[LearningUnit]:
    sess = session if session is not None else db.session
    course = require_course_manager(actor, course_id, session=sess)
    return (
        sess.query(LearningUnit)
        .filter(LearningUnit.course_id == course.id, LearningUnit.deleted_at.is_(None))
        .order_by(LearningUnit.position)
        .all()
    )


def update_learning_unit(
    actor: User,
    unit_id: uuid.UUID | str,
    data: dict[str, Any],
    session: Session | scoped_session[Any] | None = None,
) -> LearningUnit:
    sess = session if session is not None else db.session
    try:
        public_id = uuid.UUID(str(unit_id))
    except (TypeError, ValueError, AttributeError):
        raise LessonValidationError("Invalid learning unit ID.") from None
    unit = sess.query(LearningUnit).filter(LearningUnit.public_id == public_id).first()
    if unit is None or unit.deleted_at is not None:
        raise ResourceNotFoundError("Learning unit not found.")
    course = require_course_manager(actor, unit.course_id, session=sess)
    if course.status == "SUBMITTED_FOR_REVIEW" and not actor.is_admin:
        raise LessonStateViolationError(
            "Khóa học đang chờ Quản trị viên xét duyệt. Không thể sửa chương mục."
        )
    title = data.get("title")
    if not isinstance(title, str) or not title.strip() or len(title.strip()) > 200:
        raise LessonValidationError("Learning unit title must have 1 to 200 characters.")
    unit.title = title.strip()
    if session is None:
        sess.commit()
    return unit


def delete_learning_unit(
    actor: User,
    unit_id: uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> bool:
    """Soft delete a learning unit and disassociate its lessons."""
    sess = session if session is not None else db.session
    try:
        public_id = uuid.UUID(str(unit_id))
    except (TypeError, ValueError, AttributeError):
        raise LessonValidationError("Invalid learning unit ID.") from None
    unit = sess.query(LearningUnit).filter(LearningUnit.public_id == public_id).first()
    if unit is None or unit.deleted_at is not None:
        raise ResourceNotFoundError("Learning unit not found.")
    course = require_course_manager(actor, unit.course_id, session=sess)
    if course.status == "SUBMITTED_FOR_REVIEW" and not actor.is_admin:
        raise LessonStateViolationError(
            "Khóa học đang chờ Quản trị viên xét duyệt. Không thể xóa chương mục."
        )

    for lesson in unit.lessons:
        if lesson.deleted_at is None:
            lesson.deleted_at = utc_now()
            lesson.updated_at = utc_now()

    unit.deleted_at = utc_now()
    from pwd301.models.course import CourseChangeRequest

    pending_crs = (
        sess.query(CourseChangeRequest)
        .filter(
            CourseChangeRequest.course_id == unit.course_id,
            CourseChangeRequest.target_id == unit.id,
            CourseChangeRequest.status == "PENDING",
        )
        .all()
    )
    for pcr in pending_crs:
        pcr.status = "CANCELLED"
    sess.flush()

    # Re-compact remaining active learning units to contiguous positions
    remaining_units = (
        sess.query(LearningUnit)
        .filter(LearningUnit.course_id == unit.course_id, LearningUnit.deleted_at.is_(None))
        .order_by(LearningUnit.position.asc(), LearningUnit.id.asc())
        .all()
    )
    for idx, rem in enumerate(remaining_units, start=1):
        rem.position = idx
        rem.updated_at = utc_now()
    sess.flush()

    if session is None:
        sess.commit()
    return True


def reorder_learning_units(
    actor: User,
    course_id: int | uuid.UUID | str,
    ordered_unit_ids: list[str],
    session: Session | scoped_session[Any] | None = None,
) -> list[LearningUnit]:
    """Reorder learning units within an authorized course."""
    sess = session if session is not None else db.session
    course = require_course_manager(actor, course_id, session=sess)
    if course.status == "SUBMITTED_FOR_REVIEW" and not actor.is_admin:
        raise LessonStateViolationError(
            "Khóa học đang chờ Quản trị viên xét duyệt. Không thể sắp xếp lại chương mục."
        )
    units = (
        sess.query(LearningUnit)
        .filter(LearningUnit.course_id == course.id, LearningUnit.deleted_at.is_(None))
        .all()
    )
    unit_map = {str(u.public_id): u for u in units}
    position = 1
    reordered: list[LearningUnit] = []
    for uid in ordered_unit_ids:
        u = unit_map.get(str(uid))
        if u and u not in reordered:
            u.position = position
            position += 1
            reordered.append(u)
    for u in units:
        if u not in reordered:
            u.position = position
            position += 1
            reordered.append(u)

    if session is None:
        sess.commit()
    return reordered


def _external_video_count(markdown_content: str | None) -> int:
    content = markdown_content or ""
    match = re.search(r"<!--\s*video_urls:\s*(\[.*?\])\s*-->", content, re.DOTALL)
    if match:
        try:
            urls = json.loads(match.group(1))
        except (TypeError, ValueError):
            raise LessonValidationError("Invalid video link list.") from None
        if not isinstance(urls, list) or any(not isinstance(url, str) for url in urls):
            raise LessonValidationError("Invalid video link list.")
        return len(urls)
    return len(re.findall(r"<!--\s*video_url:\s*\S+?\s*-->", content))


def validate_lesson_media_limits(
    unit: LearningUnit,
    lesson: Lesson | None,
    markdown_content: str,
    added_uploaded_video: int = 0,
    added_documents: int = 0,
) -> None:
    """Enforce child and parent caps against persisted media and proposed changes."""
    external_count = _external_video_count(markdown_content)
    resources = list(lesson.resources) if lesson is not None else []
    uploaded_count = sum(1 for resource in resources if resource.is_video)
    document_count = len(resources) - uploaded_count
    child_videos = external_count + uploaded_count + added_uploaded_video
    if child_videos > 2:
        raise LessonValidationError("A lesson can contain at most 2 videos.")
    if document_count + added_documents > 5:
        raise LessonValidationError("A lesson can contain at most 5 documents.")
    unit_videos = child_videos
    for sibling in unit.lessons:
        if (
            sibling is lesson
            or sibling.deleted_at is not None
            or sibling.status in ("TRASH", "HISTORICAL")
        ):
            continue
        unit_videos += _external_video_count(sibling.markdown_content)
        unit_videos += sum(1 for resource in sibling.resources if resource.is_video)
    if unit_videos > 7:
        raise LessonValidationError("A learning unit can contain at most 7 videos.")


def _lesson_mini_quiz(lesson: Lesson) -> list[dict[str, Any]]:
    match = re.search(r"<!--\s*mini_quiz:\s*(.+?)\s*-->", lesson.markdown_content or "", re.DOTALL)
    if match is None:
        return []
    try:
        questions = json.loads(match.group(1))
    except (TypeError, ValueError):
        return []
    if not isinstance(questions, list) or any(
        not isinstance(question, dict) for question in questions
    ):
        return []
    return questions


def _lesson_quiz_answers_complete(questions: list[dict[str, Any]], answers: list[Any]) -> bool:
    if len(answers) != len(questions):
        return False

    for question, answer in zip(questions, answers, strict=True):
        question_type = str(question.get("type") or "MULTIPLE_CHOICE").upper()
        if question_type == "MULTIPLE_CHOICE":
            options = question.get("options") or question.get("choices") or []
            if not isinstance(options, list) or not options:
                return False
            multi = (
                bool(question.get("allow_multiple"))
                or len(question.get("correct_answers") or []) > 1
            )
            selected = answer if isinstance(answer, list) else [answer]
            if not selected or (not multi and len(selected) != 1):
                return False
            if any(
                isinstance(index, bool)
                or not isinstance(index, int)
                or index < 0
                or index >= len(options)
                for index in selected
            ):
                return False
        elif question_type == "FILL_BLANK":
            blanks = question.get("blanks") or []
            if not isinstance(blanks, list):
                return False
            if not blanks:
                blanks = re.findall(r"\[_{2,}\]", str(question.get("question") or ""))
            values = answer if isinstance(answer, list) else [answer]
            if len(values) != len(blanks) or any(
                not isinstance(value, str) or not value.strip() for value in values
            ):
                return False
        elif question_type == "MATCHING":
            pairs = question.get("pairs") or []
            if not isinstance(pairs, list) or not pairs:
                return False
            if isinstance(answer, dict):
                values = list(answer.values())
                if len(answer) != len(pairs):
                    return False
            elif isinstance(answer, list):
                values = answer
                if len(values) != len(pairs):
                    return False
            else:
                return False
            if not values or any(value is None or str(value).strip() == "" for value in values):
                return False
        elif question_type == "TRUE_FALSE":
            if not isinstance(answer, bool) and str(answer).lower() not in ("true", "false"):
                return False
        elif question_type in ("SHORT_ANSWER", "ESSAY"):
            if answer is None or (isinstance(answer, str) and not answer.strip()):
                return False
        else:
            return False

    return True


def _lesson_requires_video_watch(lesson: Lesson) -> bool:
    if re.search(r"<!--\s*video_urls:\s*\[\s*\"", lesson.markdown_content or ""):
        return True
    if re.search(r"<!--\s*video_url:\s*\S+?\s*-->", lesson.markdown_content or ""):
        return True
    return any(
        bool(getattr(resource.file_asset, "is_video", False))
        for resource in lesson.resources
        if resource.file_asset is not None
    )


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

# Sliding cache of recent client_event_ids to prevent double-counting on network retries
_RECENT_CLIENT_EVENT_IDS: dict[str, float] = {}


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
    if course.status == "SUBMITTED_FOR_REVIEW" and not actor.is_admin:
        raise LessonStateViolationError(
            "Khóa học đang chờ Quản trị viên xét duyệt. Không thể thêm bài giảng mới."
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

    # Validate required_for_periods_starting_at (optional)
    req_for_periods = data.get("required_for_periods_starting_at")
    if req_for_periods is not None:
        if isinstance(req_for_periods, str):
            try:
                norm_str = req_for_periods.replace("Z", "+00:00")
                req_for_periods = datetime.datetime.fromisoformat(norm_str)
            except ValueError as err:
                raise LessonValidationError(
                    "required_for_periods_starting_at must be a valid ISO datetime."
                ) from err
        elif not isinstance(req_for_periods, datetime.datetime):
            raise LessonValidationError(
                "required_for_periods_starting_at must be a datetime or ISO string."
            )

    learning_unit_id = data.get("learning_unit_id")
    if (
        learning_unit_id is None
        or learning_unit_id == ""
        or str(learning_unit_id).lower() in ("undefined", "null", "none")
    ):
        # Legacy clients or draft creations create a one-child group while retaining the Lesson ID.
        unit = create_learning_unit(actor, course.id, {"title": clean_title}, session=sess)
    else:
        existing_unit = None
        try:
            public_unit_id = uuid.UUID(str(learning_unit_id))
            existing_unit = (
                sess.query(LearningUnit)
                .filter(LearningUnit.public_id == public_unit_id)
                .with_hint(LearningUnit, "WITH (UPDLOCK, HOLDLOCK)", dialect_name="mssql")
                .with_for_update()
                .first()
            )
        except (TypeError, ValueError, AttributeError):
            if str(learning_unit_id).isdigit():
                existing_unit = (
                    sess.query(LearningUnit)
                    .filter(LearningUnit.id == int(learning_unit_id))
                    .with_hint(LearningUnit, "WITH (UPDLOCK, HOLDLOCK)", dialect_name="mssql")
                    .with_for_update()
                    .first()
                )
            else:
                raise LessonValidationError("Invalid learning unit ID.") from None
        if (
            existing_unit is None
            or existing_unit.course_id != course.id
            or existing_unit.deleted_at is not None
        ):
            raise LessonValidationError("Learning unit does not belong to this course.")
        unit = existing_unit
        child_count = (
            sess.query(sa.func.count(Lesson.id))
            .filter(
                Lesson.learning_unit_id == unit.id,
                Lesson.deleted_at.is_(None),
                Lesson.status.notin_(("TRASH", "HISTORICAL")),
            )
            .scalar()
            or 0
        )
        if child_count >= 10:
            raise LessonValidationError("A learning unit can contain at most 10 lessons.")

    validate_lesson_media_limits(unit, None, clean_markdown)

    # Calculate position and shift if needed
    active_lessons = (
        sess.query(Lesson)
        .filter(
            Lesson.course_id == course.id,
            Lesson.deleted_at.is_(None),
            Lesson.status.notin_(("TRASH", "HISTORICAL")),
        )
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
        learning_unit_id=unit.id,
        change_request_id=change_req_id,
        title=clean_title,
        summary=clean_summary,
        markdown_content=clean_markdown,
        position=assigned_position,
        estimated_duration_minutes=est_duration,
        minimum_completion_seconds=min_completion_seconds,
        viewed_fraction_required=viewed_fraction_required,
        required_for_periods_starting_at=req_for_periods,
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
                "lesson_id": str(lesson.public_id),
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

    if lesson.status == "PUBLISHED" and course.status == "PUBLISHED":
        from pwd301.services.rag_service import auto_ingest_lesson_content

        with contextlib.suppress(Exception):
            auto_ingest_lesson_content(lesson, actor=actor, session=sess)

    if session is None:
        try:
            sess.commit()
        except Exception:
            sess.rollback()
            raise

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
    if course.status == "SUBMITTED_FOR_REVIEW" and not actor.is_admin:
        raise LessonStateViolationError(
            "Khóa học đang chờ Quản trị viên xét duyệt. Không thể chỉnh sửa bài giảng."
        )

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
        if lesson.learning_unit is not None:
            unit = (
                sess.query(LearningUnit)
                .filter(LearningUnit.id == lesson.learning_unit_id)
                .with_hint(LearningUnit, "WITH (UPDLOCK, HOLDLOCK)", dialect_name="mssql")
                .with_for_update()
                .one()
            )
            sess.expire(unit, ["lessons"])
            validate_lesson_media_limits(unit, lesson, md.strip())
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

    if "required_for_periods_starting_at" in data:
        req_for_periods = data["required_for_periods_starting_at"]
        if req_for_periods is not None:
            if isinstance(req_for_periods, str):
                try:
                    norm_str = req_for_periods.replace("Z", "+00:00")
                    req_for_periods = datetime.datetime.fromisoformat(norm_str)
                except ValueError as err:
                    raise LessonValidationError(
                        "required_for_periods_starting_at must be a valid ISO datetime."
                    ) from err
            elif not isinstance(req_for_periods, datetime.datetime):
                raise LessonValidationError(
                    "required_for_periods_starting_at must be a datetime or ISO string."
                )
        lesson.required_for_periods_starting_at = req_for_periods

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

    if lesson.status == "PUBLISHED" and course.status == "PUBLISHED":
        from pwd301.services.rag_service import auto_ingest_lesson_content

        with contextlib.suppress(Exception):
            auto_ingest_lesson_content(lesson, actor=actor, session=sess)

    if session is None:
        try:
            sess.commit()
        except Exception:
            sess.rollback()
            raise

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
    if course.status == "SUBMITTED_FOR_REVIEW" and not actor.is_admin:
        raise LessonStateViolationError(
            "Khóa học đang chờ Quản trị viên xét duyệt. Không thể sắp xếp lại bài giảng."
        )

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
    order_records = [
        {"lesson_id": str(les.public_id), "position": les.position} for les in resolved_ordered
    ]
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
        try:
            sess.commit()
        except Exception:
            sess.rollback()
            raise

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
    if course.status == "SUBMITTED_FOR_REVIEW" and not actor.is_admin:
        raise LessonStateViolationError(
            "Khóa học đang chờ Quản trị viên xét duyệt. Không thể xóa bài giảng."
        )

    if lesson.deleted_at is not None or lesson.status == "TRASH":
        return lesson

    before_pos = lesson.position
    now = utc_now()
    lesson.deleted_at = now
    lesson.deleted_by_user_id = actor.id
    lesson.status = "TRASH"
    lesson.restore_until = now + datetime.timedelta(days=30)
    # Move position out of active 1..N range to prevent unique constraint collision
    lesson.position = TRASH_POSITION_BASE + lesson.id
    lesson.updated_at = now
    sess.flush()

    # Re-compact remaining active lessons to contiguous 1..(N-1)
    remaining_lessons = (
        sess.query(Lesson)
        .filter(
            Lesson.course_id == course.id,
            Lesson.deleted_at.is_(None),
            Lesson.status.notin_(("TRASH", "HISTORICAL")),
        )
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
        try:
            sess.commit()
        except Exception:
            sess.rollback()
            raise

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
    now = utc_now()
    if new_status == "PUBLISHED" and lesson.published_at is None:
        lesson.published_at = now

    # Invariant: Restoring from TRASH clears deleted_at, restore_until, and re-integrates position
    if old_status == "TRASH" and new_status in ("PUBLISHED", "ACTIVE", "DRAFT"):
        lesson.deleted_at = None
        lesson.deleted_by_user_id = None
        lesson.restore_until = None
        if lesson.position >= TEMP_POSITION_OFFSET:
            max_pos = (
                sess.query(sa.func.max(Lesson.position))
                .filter(
                    Lesson.course_id == course.id,
                    Lesson.deleted_at.is_(None),
                    Lesson.position < TEMP_POSITION_OFFSET,
                )
                .scalar()
                or 0
            )
            lesson.position = max_pos + 1

    lesson.updated_at = now
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
        try:
            sess.commit()
        except Exception:
            sess.rollback()
            raise

    return lesson


def restore_lesson(
    actor: User,
    lesson_id: int | uuid.UUID | str,
    target_status: str = "PUBLISHED",
    reason: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> Lesson:
    """Restore a lesson from TRASH back to PUBLISHED, ACTIVE, or DRAFT."""
    sess = session if session is not None else db.session
    lesson = _resolve_lesson(lesson_id, session=sess)
    if lesson is None:
        raise LessonNotFoundError("Lesson not found.")

    if lesson.status != "TRASH":
        raise LessonStateViolationError(
            f"Cannot restore lesson in '{lesson.status}' status. "
            "Only TRASH lessons can be restored."
        )

    if target_status not in ("PUBLISHED", "ACTIVE", "DRAFT"):
        raise LessonValidationError(
            f"Invalid restore target status '{target_status}'. Must be PUBLISHED, ACTIVE, or DRAFT."
        )

    return change_lesson_status(
        actor=actor,
        lesson_id=lesson.id,
        new_status=target_status,
        reason=reason or "Restored lesson from TRASH",
        session=sess,
    )


def _has_in_flight_progress(
    session: Session | scoped_session[Any], student_user_id: int, lesson_id: int
) -> bool:
    """Check if student has an existing progress record on this lesson revision."""
    return (
        session.query(LessonProgress)
        .join(EnrollmentPeriod, LessonProgress.enrollment_period_id == EnrollmentPeriod.id)
        .join(Enrollment, EnrollmentPeriod.enrollment_id == Enrollment.id)
        .filter(
            Enrollment.student_user_id == student_user_id,
            LessonProgress.lesson_id == lesson_id,
        )
        .first()
        is not None
    )


def get_lesson_detail(
    actor: User | None,
    lesson_id: int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> Lesson:
    """Retrieve detailed lesson content adhering to role-based and enrollment guards.

    Rules:
    - Instructor managing this course / Admin: can read any status.
    - Student: must have an ACTIVE enrollment in this course, and lesson must be PUBLISHED
      (or HISTORICAL if student already has active in-flight progress on it).
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
    # Must be authenticated, course not deleted,
    # lesson PUBLISHED (or HISTORICAL for in-flight learners),
    # and student actively enrolled
    if actor is None or not actor.is_active:
        raise ForbiddenError("Authentication required to access lesson.")

    has_history = False
    if lesson.status == "HISTORICAL" and actor is not None and getattr(actor, "id", None):
        has_history = _has_in_flight_progress(sess, actor.id, lesson.id)

    is_accessible = (
        (lesson.status == "PUBLISHED" or has_history)
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
            Enrollment.status.in_(["ACTIVE", "COMPLETED"]),
        )
        .first()
    )
    if enrollment is None:
        raise ForbiddenError("Active course enrollment required to view this lesson.")

    # If course specifies sequential learning, active students must complete prior lessons first
    if enrollment.status == "ACTIVE" and course.completion_requirements:
        try:
            req_dict = json.loads(course.completion_requirements)
            if isinstance(req_dict, dict) and req_dict.get("enforce_sequential_learning"):
                all_lessons = (
                    sess.query(Lesson)
                    .filter(
                        Lesson.course_id == course.id,
                        Lesson.status == "PUBLISHED",
                        Lesson.deleted_at.is_(None),
                    )
                    .order_by(Lesson.position.asc(), Lesson.id.asc())
                    .all()
                )
                prior_ids = []
                for les in all_lessons:
                    if les.id == lesson.id:
                        break
                    prior_ids.append(les.id)

                if prior_ids and enrollment.current_period_id:
                    completed_count = (
                        sess.query(sa.func.count(LessonProgress.id))
                        .filter(
                            LessonProgress.enrollment_period_id == enrollment.current_period_id,
                            LessonProgress.lesson_id.in_(prior_ids),
                            LessonProgress.completed_at.isnot(None),
                        )
                        .scalar()
                        or 0
                    )
                    if completed_count < len(prior_ids):
                        raise LessonStateViolationError(
                            "Previous lessons must be completed first in this course."
                        )
        except (ValueError, TypeError):
            pass

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
        all_lessons = (
            sess.query(Lesson)
            .filter(Lesson.course_id == course.id, Lesson.deleted_at.is_(None))
            .order_by(Lesson.position.asc(), Lesson.id.desc())
            .all()
        )
        active_positions = {
            l.position
            for l in all_lessons
            if l.status in ("ACTIVE", "PUBLISHED", "PENDING_APPROVAL", "DRAFT")
        }
        return [
            l
            for l in all_lessons
            if l.status != "HISTORICAL" or l.position not in active_positions
        ]

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
    client_event_id: str | None = None,
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

    if lesson.deleted_at is not None or lesson.status not in ("PUBLISHED", "HISTORICAL"):
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
        now_ts = utc_now()
        active_period = EnrollmentPeriod(
            enrollment_id=enrollment.id,
            period_no=1,
            started_at=enrollment.enrolled_at or now_ts,
            status="ACTIVE" if enrollment.status == "ACTIVE" else "COMPLETED",
            created_at=now_ts,
        )
        sess.add(active_period)
        sess.flush()
        enrollment.current_period_id = active_period.id
        sess.flush()

    # Find or create LessonProgress record
    progress = (
        sess.query(LessonProgress)
        .filter(
            LessonProgress.enrollment_period_id == active_period.id,
            LessonProgress.lesson_id == lesson.id,
        )
        .first()
    )

    if progress is None and lesson.status == "HISTORICAL":
        raise LessonStateViolationError("Cannot start progress on a historical lesson revision.")

    now = utc_now()
    if progress is None:
        progress = LessonProgress(
            enrollment_period_id=active_period.id,
            lesson_id=lesson.id,
            seconds_spent=0,
            max_view_fraction=0.0,
            acknowledged_revision_no=lesson.revision_no,
            updated_at=now,
        )
        sess.add(progress)
        sess.flush()

    # Deduplicate client_event_id to prevent double-counting on network retries (Algorithm 02)
    if client_event_id is not None:
        cid_str = str(client_event_id).strip()
        curr_ts = time.time()
        if len(_RECENT_CLIENT_EVENT_IDS) > 5000:
            expired_keys = [k for k, ts in _RECENT_CLIENT_EVENT_IDS.items() if curr_ts - ts > 600]
            for k in expired_keys:
                _RECENT_CLIENT_EVENT_IDS.pop(k, None)

        dedup_key = f"{active_period.id}:{lesson.id}:{cid_str}"
        if dedup_key in _RECENT_CLIENT_EVENT_IDS:
            # Replay/duplicate event: do not increment seconds, update last_activity_at only
            progress.last_activity_at = now
            sess.flush()
            return progress
        _RECENT_CLIENT_EVENT_IDS[dedup_key] = curr_ts

    # Bounded accumulated active seconds & high-water-mark view fraction
    progress.seconds_spent = (progress.seconds_spent or 0) + sec
    current_fraction = float(progress.max_view_fraction or 0.0)
    progress.max_view_fraction = max(current_fraction, vf)
    progress.acknowledged_revision_no = lesson.revision_no
    progress.last_activity_at = now
    progress.updated_at = now

    # Evaluate completion: monotonic, idempotent
    min_completion_seconds = lesson.minimum_completion_seconds
    requires_video = _lesson_requires_video_watch(lesson)
    viewed_fraction_required = (
        0.90 if requires_video else float(lesson.viewed_fraction_required)
    )

    # When video is watched (>= 90%), automatically satisfy minimum duration requirement
    if requires_video and float(progress.max_view_fraction) >= 0.90:
        if min_completion_seconds > 0 and (progress.seconds_spent or 0) < min_completion_seconds:
            progress.seconds_spent = min_completion_seconds

    progress_snapshot: dict[str, Any] = {}
    if progress.completion_rule_snapshot_json:
        try:
            parsed_snapshot = json.loads(progress.completion_rule_snapshot_json)
            if isinstance(parsed_snapshot, dict):
                progress_snapshot = parsed_snapshot
        except (TypeError, ValueError):
            progress_snapshot = {}

    quiz_is_configured = re.search(r"<!--\s*mini_quiz:", lesson.markdown_content or "") is not None
    quiz_is_complete = not quiz_is_configured or bool(
        progress_snapshot.get("mini_quiz_completed_at")
    )
    criteria_met = (
        progress.seconds_spent >= min_completion_seconds
        and float(progress.max_view_fraction) >= viewed_fraction_required
        and quiz_is_complete
    )

    newly_completed = False
    if criteria_met and progress.completed_at is None:
        progress.completed_at = now
        progress_snapshot.update(
            {
                "minimum_completion_seconds": min_completion_seconds,
                "viewed_fraction_required": viewed_fraction_required,
                "completed_at": now.isoformat(),
            }
        )
        progress.completion_rule_snapshot_json = json.dumps(progress_snapshot)
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
        try:
            sess.commit()
        except Exception:
            sess.rollback()
            raise

    return progress


def complete_lesson_mini_quiz(
    actor: User,
    lesson_id: int | uuid.UUID | str,
    answers: list[Any],
    session: Session | scoped_session[Any] | None = None,
) -> LessonProgress:
    """Record that an enrolled student answered every question in a lesson mini-quiz."""
    sess = session if session is not None else db.session
    lesson = _resolve_lesson(lesson_id, session=sess)
    if lesson is None:
        raise LessonNotFoundError("Lesson not found.")
    if lesson.deleted_at is not None or lesson.status != "PUBLISHED":
        raise LessonStateViolationError("Cannot complete a quiz in an unpublished lesson.")

    questions = _lesson_mini_quiz(lesson)
    quiz_marker_exists = re.search(r"<!--\s*mini_quiz:", lesson.markdown_content or "") is not None
    if not quiz_marker_exists or not questions:
        raise LessonValidationError("This lesson has no valid quiz to complete.")
    if not _lesson_quiz_answers_complete(questions, answers):
        raise LessonValidationError("Answer every lesson quiz question before completing it.")

    requires_video_watch = _lesson_requires_video_watch(lesson)
    video_view_fraction_required = (
        0.90 if requires_video_watch else float(lesson.viewed_fraction_required)
    )
    existing_progress = get_lesson_progress(actor, lesson_id, session=sess)
    video_watch_complete = bool(
        existing_progress
        and float(existing_progress.max_view_fraction) >= video_view_fraction_required
    )
    if requires_video_watch and not video_watch_complete:
        raise LessonStateViolationError("Watch the lesson video before answering its quiz.")

    progress = record_lesson_progress(
        actor=actor,
        lesson_id=lesson_id,
        seconds_increment=1,
        view_fraction=0.0 if requires_video_watch else 1.0,
        session=sess,
    )
    now = utc_now()
    progress_snapshot: dict[str, Any] = {}
    if progress.completion_rule_snapshot_json:
        try:
            parsed_snapshot = json.loads(progress.completion_rule_snapshot_json)
            if isinstance(parsed_snapshot, dict):
                progress_snapshot = parsed_snapshot
        except (TypeError, ValueError):
            progress_snapshot = {}

    if not progress_snapshot.get("mini_quiz_completed_at"):
        progress_snapshot["mini_quiz_completed_at"] = now.isoformat()
        progress_snapshot["mini_quiz_question_count"] = len(questions)

    newly_completed = False
    if (
        progress.completed_at is None
        and progress.seconds_spent >= lesson.minimum_completion_seconds
        and float(progress.max_view_fraction) >= video_view_fraction_required
    ):
        progress.completed_at = now
        progress_snapshot.update(
            {
                "minimum_completion_seconds": lesson.minimum_completion_seconds,
                "viewed_fraction_required": video_view_fraction_required,
                "completed_at": now.isoformat(),
            }
        )
        newly_completed = True

    progress.completion_rule_snapshot_json = json.dumps(progress_snapshot)
    if newly_completed:
        from pwd301.services.completion_service import (
            calculate_course_progress,
            evaluate_course_completion,
        )

        enrollment = (
            sess.query(Enrollment)
            .filter(
                Enrollment.student_user_id == actor.id,
                Enrollment.course_id == lesson.course_id,
                Enrollment.status.in_(["ACTIVE", "COMPLETED"]),
            )
            .first()
        )
        if enrollment is not None:
            calculate_course_progress(enrollment.id, session=sess)
            evaluate_course_completion(enrollment.id, session=sess)

    sess.flush()
    if session is None:
        try:
            sess.commit()
        except Exception:
            sess.rollback()
            raise
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
            Enrollment.status.in_(["ACTIVE", "COMPLETED"]),
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


def queue_lesson_review(
    actor: User,
    course: Course,
    lesson: Lesson,
    change_type: str,
    proposal: dict[str, Any],
    session: Session | scoped_session[Any] | None = None,
) -> CourseChangeRequest:
    """Retain one pending review per lesson action and notify reviewers once."""
    sess = session if session is not None else db.session
    require_course_manager(actor, course.id, session=sess)
    if lesson.course_id != course.id:
        raise ResourceNotFoundError("Lesson not found in course.")
    # Serialize proposals for one lesson before checking for an existing review.
    sess.query(Lesson).filter(Lesson.id == lesson.id).with_hint(
        Lesson, "WITH (UPDLOCK, HOLDLOCK)", dialect_name="mssql"
    ).with_for_update().one()
    pending = (
        sess.query(CourseChangeRequest)
        .filter_by(
            course_id=course.id,
            requested_by_user_id=actor.id,
            change_type=change_type,
            target_type="LESSON",
            target_id=lesson.id,
            status="PENDING",
        )
        .order_by(CourseChangeRequest.id.desc())
        .first()
    )
    if pending is not None:
        try:
            current = json.loads(pending.proposed_payload_json or "{}")
        except (TypeError, ValueError):
            current = {}
        if not isinstance(current, dict):
            current = {}
        if proposal.get("action") == current.get("action") == "RESOURCE_CHANGES":
            changes = current.get("changes", [])
            if not isinstance(changes, list):
                changes = []
            for change in proposal.get("changes", []):
                if change not in changes:
                    changes.append(change)
            proposal = {**proposal, "changes": changes}
        if proposal.get("action") == "RESOURCE_CHANGES":
            _validate_proposed_resource_changes(lesson, proposal, sess)
        pending.proposed_payload_json = json.dumps({**current, **proposal}, default=str)
        sess.commit()
        return pending

    if proposal.get("action") == "RESOURCE_CHANGES":
        _validate_proposed_resource_changes(lesson, proposal, sess)
    review = CourseChangeRequest(
        course_id=course.id,
        requested_by_user_id=actor.id,
        change_type=change_type,
        target_type="LESSON",
        target_id=lesson.id,
        proposed_payload_json=json.dumps(proposal, default=str),
        status="PENDING",
        created_at=utc_now(),
    )
    sess.add(review)
    sess.flush()

    from pwd301.services.notification_service import dispatch_notification

    action = "xóa" if proposal.get("action") == "DELETE" else "sửa"
    admin_users = sess.query(User).filter(User.roles.any(Role.code == "ADMIN")).all()
    for admin in admin_users:
        if not admin.has_admin_permission("COURSE_REVIEW"):
            continue
        with contextlib.suppress(Exception):
            dispatch_notification(
                recipient_user=admin,
                event_type="LESSON_CHANGE_REQUEST",
                title=f"Yêu cầu {action} bài giảng: {lesson.title}",
                body=(
                    f"Giảng viên {actor.display_name} gửi yêu cầu {action} bài giảng "
                    f"'{lesson.title}' trong khóa học '{course.title}'."
                ),
                action_url=f"#/admin/change-requests/review?id={review.id}",
                category="COURSE",
                session=sess,
            )
    sess.commit()
    return review


def _validate_proposed_resource_changes(
    lesson: Lesson,
    proposal: dict[str, Any],
    sess: Session | scoped_session[Any],
) -> None:
    """Check media caps against the resources Admin would actually publish."""
    remaining = {resource.id: resource.file_asset for resource in lesson.resources}
    added: dict[int, FileAsset] = {}
    for change in proposal.get("changes", []):
        if change.get("action") == "DETACH":
            remaining.pop(change["resource_id"], None)
        elif change.get("action") == "ATTACH":
            asset = sess.get(FileAsset, change["asset_id"])
            if asset is not None and asset.id not in (item.id for item in remaining.values()):
                added[asset.id] = asset
    assets = [*remaining.values(), *added.values()]
    uploaded_videos = sum(asset.is_video for asset in assets)
    if uploaded_videos + _external_video_count(lesson.markdown_content) > 2:
        raise LessonValidationError("A lesson can contain at most 2 videos.")
    if len(assets) - uploaded_videos > 5:
        raise LessonValidationError("A lesson can contain at most 5 documents.")
    if lesson.learning_unit is not None:
        unit_videos = uploaded_videos + _external_video_count(lesson.markdown_content)
        for sibling in lesson.learning_unit.lessons:
            if (
                sibling.id == lesson.id
                or sibling.deleted_at is not None
                or sibling.status == "TRASH"
            ):
                continue
            unit_videos += _external_video_count(sibling.markdown_content)
            unit_videos += sum(resource.is_video for resource in sibling.resources)
        if unit_videos > 7:
            raise LessonValidationError("A learning unit can contain at most 7 videos.")


def queue_lesson_resource_change(
    actor: User,
    course: Course,
    lesson: Lesson,
    action: str,
    *,
    asset: FileAsset | None = None,
    resource_id: int | uuid.UUID | str | None = None,
    label: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> CourseChangeRequest:
    """Keep published Lesson resource links unchanged until Admin review."""
    sess = session if session is not None else db.session
    if action == "ATTACH":
        if (
            asset is None
            or asset.course_id != course.id
            or asset.asset_type != "RESOURCE"
            or asset.status != "ACTIVE"
            or asset.deleted_at is not None
        ):
            raise LessonValidationError("Only an active resource in this course can be proposed.")
        clean_label = (label or asset.display_name).strip()
        if not clean_label or len(clean_label) > 255:
            raise LessonValidationError("Resource label must have 1 to 255 characters.")
        change = {"action": "ATTACH", "asset_id": asset.id, "label": clean_label}
    elif action == "DETACH":
        resource = next(
            (
                item
                for item in lesson.resources
                if str(item.id) == str(resource_id)
                or str(item.public_id) == str(resource_id)
                or (
                    item.file_asset is not None
                    and str(item.file_asset.public_id) == str(resource_id)
                )
            ),
            None,
        )
        if resource is None:
            raise ResourceNotFoundError("Lesson resource link not found.")
        change = {"action": "DETACH", "resource_id": resource.id}
    else:
        raise LessonValidationError("Invalid Lesson resource change.")
    return queue_lesson_review(
        actor,
        course,
        lesson,
        "OTHER",
        {"action": "RESOURCE_CHANGES", "changes": [change]},
        session=sess,
    )


def _copy_lesson_resources(
    source_lesson_id: int | uuid.UUID | str,
    target_lesson_id: int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> None:
    """Copy all active resources from source lesson to target lesson if not already present."""
    from pwd301.models.file_import import LessonResource

    sess = session if session is not None else db.session
    src_lid = None
    if isinstance(source_lesson_id, int):
        src_lid = source_lesson_id
    else:
        src_obj = _resolve_lesson(source_lesson_id, session=sess)
        if src_obj:
            src_lid = src_obj.id

    tgt_lid = None
    if isinstance(target_lesson_id, int):
        tgt_lid = target_lesson_id
    else:
        tgt_obj = _resolve_lesson(target_lesson_id, session=sess)
        if tgt_obj:
            tgt_lid = tgt_obj.id

    if not src_lid or not tgt_lid or src_lid == tgt_lid:
        return

    source_resources = (
        sess.query(LessonResource)
        .filter(LessonResource.lesson_id == src_lid)
        .order_by(LessonResource.position.asc())
        .all()
    )
    for res in source_resources:
        exists = (
            sess.query(LessonResource)
            .filter(
                LessonResource.lesson_id == tgt_lid,
                LessonResource.file_asset_id == res.file_asset_id,
            )
            .first()
        )
        if not exists:
            new_res = LessonResource(
                lesson_id=tgt_lid,
                file_asset_id=res.file_asset_id,
                position=res.position,
                label=res.label,
                is_required=res.is_required,
                created_at=utc_now(),
            )
            sess.add(new_res)
    sess.flush()


def create_lesson_change_request(
    actor: User,
    course_id: int | uuid.UUID | str,
    payload: dict[str, Any],
    session: Session | scoped_session[Any] | None = None,
) -> tuple[CourseChangeRequest, Lesson]:
    """Create or upsert a relational staged lesson change request (Defect 6 & 7).

    Creates or updates a CourseChangeRequest and a corresponding Lesson in 'PENDING_APPROVAL' status,
    linked via change_request_id. Avoids JSON de-normalization while respecting the
    filtered unique index uq_lessons_course_position_active.
    """
    sess = session if session is not None else db.session
    course = require_course_manager(actor, course_id, session=sess)
    original_target_id = payload.get("target_id") or payload.get("lesson_id")
    if original_target_id is not None:
        if isinstance(original_target_id, str):
            try:
                original_target_id = int(original_target_id)
            except (ValueError, TypeError):
                try:
                    target_u = uuid.UUID(original_target_id)
                    found_target = sess.query(Lesson).filter(Lesson.public_id == target_u).first()
                    if found_target:
                        original_target_id = found_target.id
                except (ValueError, TypeError):
                    pass

    # Autosave Deduplication & Idempotency: Check if there is already a PENDING request for this lesson
    if original_target_id:
        existing_req = (
            sess.query(CourseChangeRequest)
            .filter_by(
                course_id=course.id,
                target_type="LESSON",
                target_id=original_target_id,
                status="PENDING",
            )
            .first()
        )
        if existing_req:
            staged = (
                sess.query(Lesson)
                .filter(Lesson.change_request_id == existing_req.id)
                .first()
            )
            if staged:
                for field in (
                    "title",
                    "summary",
                    "markdown_content",
                    "estimated_duration_minutes",
                    "minimum_completion_seconds",
                    "viewed_fraction_required",
                ):
                    if field in payload and payload[field] is not None:
                        setattr(staged, field, payload[field])
                staged.updated_at = utc_now()
                existing_req.proposed_payload_json = json.dumps(payload, default=str)
                existing_req.created_at = utc_now()
                # Ensure existing resources are also synchronized
                _copy_lesson_resources(original_target_id, staged.id, session=sess)
                try:
                    sess.commit()
                except Exception:
                    sess.rollback()
                    raise
                return existing_req, staged

    req = CourseChangeRequest(
        course_id=course.id,
        requested_by_user_id=actor.id,
        change_type=payload.get("change_type", "LESSON_STRUCTURE"),
        target_type="LESSON",
        target_id=original_target_id,
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
    if original_target_id:
        _copy_lesson_resources(original_target_id, staged_lesson.id, session=sess)
    else:
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
    - If new lesson insertion (CREATE_LESSON): shifts existing active lessons at or after
      staged.position downwards by 1.
    - If editing existing lesson: retires the previous revision at the same position
      by setting status='HISTORICAL'.
    - Activates the staged lesson by setting status='PUBLISHED'.
    - Marks the change request APPROVED.
    All done within a single transaction without violating uq_lessons_course_position_active.
    """
    sess = session if session is not None else db.session

    req = sess.get(CourseChangeRequest, change_request_id)
    if req is None:
        raise ResourceNotFoundError("Course change request not found.")

    is_admin_reviewer = bool(
        actor.is_admin and (actor.is_primary_admin or actor.has_admin_permission("COURSE_REVIEW"))
    )
    from pwd301.services.authorization_service import can_manage_course
    if not (can_manage_course(actor, req.course_id, session=sess) or is_admin_reviewer):
        raise ForbiddenError("Bạn không có quyền thẩm định yêu cầu thay đổi khóa học này.")

    if req.status != "PENDING":
        raise LessonStateViolationError(f"Cannot approve change request in '{req.status}' status.")

    now = utc_now()
    p_data = json.loads(req.proposed_payload_json or "{}") if req.proposed_payload_json else {}
    is_create_lesson = p_data.get("action") == "CREATE_LESSON"

    # Find staged lessons for this request
    staged_lessons = sess.query(Lesson).filter(Lesson.change_request_id == req.id).all()

    for staged in staged_lessons:
        if is_create_lesson:
            # Shift existing active lessons at or after this position downwards by 1
            # Phase 1: assign temporary non-colliding positions (+10000)
            subsequent = (
                sess.query(Lesson)
                .filter(
                    Lesson.course_id == req.course_id,
                    Lesson.position >= staged.position,
                    Lesson.status.in_(["ACTIVE", "PUBLISHED"]),
                    Lesson.id != staged.id,
                    Lesson.deleted_at.is_(None),
                )
                .all()
            )
            for sub in subsequent:
                sub.position += 10000
            sess.flush()

            # Phase 2: assign final shifted positions (-10000 + 1)
            for sub in subsequent:
                sub.position = (sub.position - 10000) + 1
                sub.updated_at = now
            sess.flush()
            staged.revision_no = 1
        else:
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
                staged.revision_no = (active_at_pos.revision_no or 1) + 1
                staged.previous_lesson_id = active_at_pos.id
                staged.material_change_summary = (
                    review_reason or "Nội dung cập nhật đã được Admin phê duyệt."
                )
                _copy_lesson_resources(active_at_pos.id, staged.id, session=sess)
                sess.flush()
            elif req.target_id:
                _copy_lesson_resources(req.target_id, staged.id, session=sess)
                sess.flush()
            else:
                staged.revision_no = 1

        staged.status = "PUBLISHED"
        if staged.published_at is None:
            staged.published_at = now
        staged.updated_at = now
        sess.flush()

    if p_data.get("action") == "CREATE_LEARNING_UNIT" and req.target_id:
        from pwd301.models.course import LearningUnit
        target_u = sess.get(LearningUnit, req.target_id)
        if target_u:
            for les in target_u.lessons:
                if les.deleted_at is None and les.status in ("DRAFT", "PENDING_APPROVAL"):
                    les.status = "PUBLISHED"
                    if les.published_at is None:
                        les.published_at = now
                    les.updated_at = now
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

    is_admin_reviewer = bool(
        actor.is_admin and (actor.is_primary_admin or actor.has_admin_permission("COURSE_REVIEW"))
    )
    from pwd301.services.authorization_service import can_manage_course
    if not (can_manage_course(actor, req.course_id, session=sess) or is_admin_reviewer):
        raise ForbiddenError("Bạn không có quyền thẩm định yêu cầu thay đổi khóa học này.")

    if req.status != "PENDING":
        raise LessonStateViolationError(f"Cannot reject change request in '{req.status}' status.")

    now = utc_now()
    p_data = json.loads(req.proposed_payload_json or "{}") if req.proposed_payload_json else {}
    staged_lessons = sess.query(Lesson).filter(Lesson.change_request_id == req.id).all()
    for staged in staged_lessons:
        staged.status = "TRASH"
        staged.deleted_at = now
        staged.updated_at = now

    if p_data.get("action") == "CREATE_LEARNING_UNIT" and req.target_id:
        from pwd301.models.course import LearningUnit
        target_u = sess.get(LearningUnit, req.target_id)
        if target_u:
            target_u.deleted_at = now
            for les in target_u.lessons:
                les.status = "TRASH"
                les.deleted_at = now
                les.updated_at = now
            sess.flush()

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


def get_lesson_detail_with_draft(
    actor: User,
    lesson_id: int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> tuple[Lesson, dict[str, Any] | None]:
    """Retrieve lesson detail along with active working draft from rejected or pending requests."""
    sess = session if session is not None else db.session
    lesson = _resolve_lesson(lesson_id, session=sess)
    if lesson is None or lesson.deleted_at is not None:
        raise LessonNotFoundError("Lesson not found.")

    require_course_manager(actor, lesson.course_id, session=sess)

    # Find the latest pending or rejected change request for this lesson
    # (direct target or staged lesson at same position)
    change_req = (
        sess.query(CourseChangeRequest)
        .filter(
            CourseChangeRequest.course_id == lesson.course_id,
            CourseChangeRequest.target_type == "LESSON",
            CourseChangeRequest.status.in_(["PENDING", "REJECTED"]),
        )
        .filter(
            sa.or_(
                CourseChangeRequest.target_id == lesson.id,
                CourseChangeRequest.id.in_(
                    sess.query(Lesson.change_request_id).filter(
                        Lesson.course_id == lesson.course_id,
                        Lesson.position == lesson.position,
                        Lesson.change_request_id.is_not(None),
                    )
                ),
            )
        )
        .order_by(CourseChangeRequest.id.desc())
        .first()
    )

    draft_info: dict[str, Any] | None = None
    if change_req is not None:
        try:
            payload = json.loads(change_req.proposed_payload_json or "{}")
        except Exception:
            payload = {}
        draft_info = {
            "change_request_id": change_req.id,
            "status": change_req.status,
            "review_reason": change_req.review_reason,
            "created_at": change_req.created_at.isoformat() if change_req.created_at else None,
            "reviewed_at": change_req.reviewed_at.isoformat() if change_req.reviewed_at else None,
            "payload": payload,
        }

    return lesson, draft_info


def discard_lesson_working_draft(
    actor: User,
    lesson_id: int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> bool:
    """Discard an active working draft (PENDING or REJECTED) by marking it CANCELLED."""
    sess = session if session is not None else db.session
    lesson = _resolve_lesson(lesson_id, session=sess)
    if lesson is None:
        try:
            cr_id = int(str(lesson_id))
            cr = sess.get(CourseChangeRequest, cr_id)
            if cr and cr.target_type == "LESSON" and cr.target_id:
                lesson = sess.get(Lesson, cr.target_id)
            elif cr:
                st = sess.query(Lesson).filter(Lesson.change_request_id == cr.id).first()
                if st:
                    lesson = st
        except (ValueError, TypeError):
            pass
    if lesson is None or lesson.deleted_at is not None:
        raise LessonNotFoundError("Lesson not found.")

    require_course_manager(actor, lesson.course_id, session=sess)

    change_reqs = (
        sess.query(CourseChangeRequest)
        .filter(
            CourseChangeRequest.course_id == lesson.course_id,
            CourseChangeRequest.target_type == "LESSON",
            CourseChangeRequest.status.in_(["PENDING", "REJECTED"]),
        )
        .filter(
            sa.or_(
                CourseChangeRequest.target_id == lesson.id,
                CourseChangeRequest.id.in_(
                    sess.query(Lesson.change_request_id).filter(
                        Lesson.course_id == lesson.course_id,
                        Lesson.position == lesson.position,
                        Lesson.change_request_id.is_not(None),
                    )
                ),
            )
        )
        .all()
    )
    if not change_reqs:
        return False

    now = utc_now()
    for req in change_reqs:
        req.status = "CANCELLED"
        req.review_reason = "Discarded by instructor"
        req.reviewed_at = now
        staged_lessons = sess.query(Lesson).filter(Lesson.change_request_id == req.id).all()
        for staged in staged_lessons:
            staged.status = "TRASH"
            staged.deleted_at = now
            staged.updated_at = now

    sess.flush()
    if session is None:
        sess.commit()
    return True


def opt_in_newer_lesson_revision(
    actor: User,
    lesson_id: int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> tuple[Lesson, LessonProgress]:
    """Allow student to opt-in to latest published lesson revision with monotonic carry-over."""
    sess = session if session is not None else db.session
    if actor is None or not actor.is_active:
        raise ForbiddenError("Authentication required.")

    current_lesson = _resolve_lesson(lesson_id, session=sess)
    if current_lesson is None or current_lesson.deleted_at is not None:
        raise LessonNotFoundError("Lesson not found.")

    # Find the latest PUBLISHED lesson at the same course and position
    latest_lesson = (
        sess.query(Lesson)
        .filter(
            Lesson.course_id == current_lesson.course_id,
            Lesson.position == current_lesson.position,
            Lesson.status.in_(["ACTIVE", "PUBLISHED"]),
            Lesson.deleted_at.is_(None),
        )
        .first()
    )
    if latest_lesson is None:
        raise LessonNotFoundError("No published revision found for this lesson.")

    enrollment = (
        sess.query(Enrollment)
        .filter(
            Enrollment.student_user_id == actor.id,
            Enrollment.course_id == current_lesson.course_id,
            Enrollment.status.in_(["ACTIVE", "COMPLETED"]),
        )
        .first()
    )
    if enrollment is None:
        raise ForbiddenError("Active course enrollment required.")

    active_period = None
    if enrollment.current_period_id:
        active_period = sess.get(EnrollmentPeriod, enrollment.current_period_id)
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
        raise LessonProgressError("No active enrollment period found.")

    # Get old progress if exists
    old_progress = (
        sess.query(LessonProgress)
        .filter(
            LessonProgress.enrollment_period_id == active_period.id,
            LessonProgress.lesson_id == current_lesson.id,
        )
        .first()
    )

    # Get or create progress for latest lesson
    target_progress = (
        sess.query(LessonProgress)
        .filter(
            LessonProgress.enrollment_period_id == active_period.id,
            LessonProgress.lesson_id == latest_lesson.id,
        )
        .first()
    )
    now = utc_now()
    if target_progress is None:
        target_progress = LessonProgress(
            enrollment_period_id=active_period.id,
            lesson_id=latest_lesson.id,
            seconds_spent=old_progress.seconds_spent if old_progress else 0,
            max_view_fraction=old_progress.max_view_fraction if old_progress else 0.0,
            completed_at=old_progress.completed_at if old_progress else None,
            completion_rule_snapshot_json=old_progress.completion_rule_snapshot_json
            if old_progress
            else None,
            acknowledged_revision_no=latest_lesson.revision_no,
            updated_at=now,
        )
        sess.add(target_progress)
    else:
        # Carry over completion if old progress was completed and target was not
        if old_progress and old_progress.completed_at and not target_progress.completed_at:
            target_progress.completed_at = old_progress.completed_at
            target_progress.completion_rule_snapshot_json = (
                old_progress.completion_rule_snapshot_json
            )
        target_progress.acknowledged_revision_no = latest_lesson.revision_no
        target_progress.updated_at = now

    sess.flush()
    if session is None:
        sess.commit()

    return latest_lesson, target_progress
