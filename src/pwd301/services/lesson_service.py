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
import uuid
from typing import Any, cast

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
    LessonProgressReceipt,
)
from pwd301.models.file_import import FileAsset
from pwd301.models.identity import User
from pwd301.models.notification_audit import AuditEvent
from pwd301.models.types import utc_now
from pwd301.services.authorization_service import (
    _resolve_course,
    _resolve_lesson,
    require_course_manager,
)
from pwd301.services.course_workflow_service import (
    AuthoringProjection,
    active_changeset,
    applying_review,
    course_requires_review,
    ensure_course_authoring,
    payload_for,
    should_stage,
    stage_course_fields,
    stage_course_operation,
    successor_draft,
    working_changeset,
    write_payload,
)
from pwd301.services.exceptions import (
    ConflictError,
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


def _to_naive_utc(dt: Any) -> Any:
    """Normalize datetime to timezone-naive UTC for arithmetic across sqlite and SQL server."""
    if dt is None:
        return None
    if hasattr(dt, "tzinfo") and dt.tzinfo is not None:
        import datetime as dt_mod

        return dt.astimezone(dt_mod.UTC).replace(tzinfo=None)
    return dt


def _change_request_notification_event_key(
    request: CourseChangeRequest,
    event_type: str,
    recipient_user_id: int,
) -> uuid.UUID:
    """Return one recipient-scoped retry key for a change-request notification."""
    if request.id is None:
        raise RuntimeError("Change-request notification key requires a persisted request.")
    return uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"pwd301:course-change:{request.id}:{event_type}:{recipient_user_id}",
    )


def _ensure_course_not_pending_changeset(
    course_id: int,
    actor: User,
    session: Session | scoped_session[Any],
) -> None:
    """Fail-closed check ensuring course mutations are locked while a changeset is pending Admin review."""
    ensure_course_authoring(actor, course_id, session=session)


def ensure_course_manager(actor: User, course: Course) -> None:
    """Ensure actor is an active admin or the owner instructor for the course."""
    if actor is None or not actor.is_active:
        raise ForbiddenError("Authentication required.")
    if not actor.is_admin and course.owner_instructor_id != actor.id:
        raise ForbiddenError("You are not authorized to manage this course.")


_ensure_course_manager = ensure_course_manager


def _resolve_learning_unit(
    unit_or_id: LearningUnit | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> LearningUnit | None:
    """Resolve a LearningUnit instance from model, integer PK, public UUID, or string."""
    if isinstance(unit_or_id, LearningUnit):
        return unit_or_id
    sess = session if session is not None else db.session
    if isinstance(unit_or_id, int):
        return sess.get(LearningUnit, unit_or_id)
    if isinstance(unit_or_id, uuid.UUID):
        return sess.query(LearningUnit).filter(LearningUnit.public_id == unit_or_id).first()
    if isinstance(unit_or_id, str):
        try:
            val_uuid = uuid.UUID(unit_or_id)
            return sess.query(LearningUnit).filter(LearningUnit.public_id == val_uuid).first()
        except ValueError:
            pass
        if unit_or_id.isdigit():
            return sess.get(LearningUnit, int(unit_or_id))
    return None


def create_learning_unit(
    actor: User,
    course_id: int | uuid.UUID | str,
    data: dict[str, Any],
    session: Session | scoped_session[Any] | None = None,
) -> LearningUnit:
    """Create an instructor-facing lesson group in an authorized course."""
    sess = session if session is not None else db.session
    course = require_course_manager(actor, course_id, session=sess)
    _ensure_course_not_pending_changeset(course.id, actor, session=sess)
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
    review = working_changeset(actor, course, sess) if should_stage(actor, course, sess) else None
    unit = LearningUnit(
        course_id=course.id,
        title=title.strip(),
        position=position,
        change_request_id=review.id if review else None,
    )
    sess.add(unit)
    sess.flush()
    if review:
        stage_course_operation(
            actor,
            course,
            {"action": "CREATE_LEARNING_UNIT", "unit_id": str(unit.public_id), "title": unit.title},
            key=f"unit:{unit.public_id}",
            session=sess,
        )
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
    units = (
        sess.query(LearningUnit)
        .filter(LearningUnit.course_id == course.id, LearningUnit.deleted_at.is_(None))
        .order_by(LearningUnit.position)
        .all()
    )
    record = active_changeset(course.id, sess)
    operations = payload_for(record).get("operations", {}) if record else {}
    result = []
    for unit in units:
        operation = operations.get(f"unit:{unit.public_id}") or {}
        if operation.get("action") == "DELETE_LEARNING_UNIT":
            continue
        result.append(
            cast(LearningUnit, AuthoringProjection(unit, {"title": operation["title"]}))
            if "title" in operation
            else unit
        )
    unit_order = operations.get("unit_order", {}).get("unit_ids") or []
    ranks = {str(uid): index for index, uid in enumerate(unit_order)}
    return sorted(
        result,
        key=lambda unit: (ranks.get(str(unit.public_id), len(ranks) + unit.position), unit.id),
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
    _ensure_course_not_pending_changeset(course.id, actor, session=sess)
    if course.status == "SUBMITTED_FOR_REVIEW" and not actor.is_admin:
        raise LessonStateViolationError(
            "Khóa học đang chờ Quản trị viên xét duyệt. Không thể sửa chương mục."
        )
    title = data.get("title")
    if not isinstance(title, str) or not title.strip() or len(title.strip()) > 200:
        raise LessonValidationError("Learning unit title must have 1 to 200 characters.")
    if should_stage(actor, course, sess) and unit.change_request_id is None:
        stage_course_operation(
            actor,
            course,
            {
                "action": "UPDATE_LEARNING_UNIT",
                "unit_id": str(unit.public_id),
                "title": title.strip(),
            },
            key=f"unit:{unit.public_id}",
            session=sess,
        )
        if session is None:
            sess.commit()
        return cast(LearningUnit, AuthoringProjection(unit, {"title": title.strip()}))
    unit.title = title.strip()
    if unit.change_request_id is not None:
        stage_course_operation(
            actor,
            course,
            {"action": "CREATE_LEARNING_UNIT", "unit_id": str(unit.public_id), "title": unit.title},
            key=f"unit:{unit.public_id}",
            session=sess,
        )
    if session is None:
        sess.commit()
    return unit


def _cleanup_lesson_resources(
    sess: Session | scoped_session[Any],
    lesson: Lesson,
    actor: User,
    now: datetime.datetime,
) -> None:
    """Soft-delete/remove LessonResource links and trash orphaned FileAssets for a deleted lesson."""
    from pwd301.models.file_import import FileAsset, LessonResource

    lesson_resources = (
        sess.query(LessonResource).filter(LessonResource.lesson_id == lesson.id).all()
    )
    for lr in lesson_resources:
        fa_id = lr.file_asset_id
        sess.delete(lr)
        sess.flush()

        # Check if fa_id is still referenced by any other active (non-deleted, non-TRASH) lesson
        other_active_ref = (
            sess.query(LessonResource)
            .join(Lesson, LessonResource.lesson_id == Lesson.id)
            .filter(
                LessonResource.file_asset_id == fa_id,
                Lesson.id != lesson.id,
                Lesson.deleted_at.is_(None),
                Lesson.status.notin_(("TRASH", "HISTORICAL")),
            )
            .first()
        )
        if not other_active_ref:
            fa = sess.get(FileAsset, fa_id)
            if (
                fa
                and fa.deleted_at is None
                and fa.status != "TRASH"
                and fa.asset_type not in ("COURSE_IMAGE", "QUESTION_IMAGE", "IMPORT_SOURCE")
            ):
                fa.deleted_at = now
                fa.status = "TRASH"
                fa.deleted_by_user_id = actor.id
                fa.restore_until = now + datetime.timedelta(days=30)


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
    _ensure_course_not_pending_changeset(course.id, actor, session=sess)
    if course.status == "SUBMITTED_FOR_REVIEW" and not actor.is_admin:
        raise LessonStateViolationError(
            "Khóa học đang chờ Quản trị viên xét duyệt. Không thể xóa chương mục."
        )

    if should_stage(actor, course, sess):
        stage_course_operation(
            actor,
            course,
            {
                "action": "DELETE_LEARNING_UNIT",
                "unit_id": str(unit.public_id),
                "title": unit.title,
            },
            key=f"unit:{unit.public_id}",
            session=sess,
        )
        now = utc_now()
        for lesson in unit.lessons:
            if lesson.deleted_at is None and lesson.status != "TRASH":
                if lesson.change_request_id is not None:
                    lesson.deleted_at = now
                    lesson.deleted_by_user_id = actor.id
                    lesson.status = "TRASH"
                    lesson.position = TRASH_POSITION_BASE + lesson.id
                    lesson.updated_at = now
                    _cleanup_lesson_resources(sess, lesson, actor, now)
                else:
                    stage_course_operation(
                        actor,
                        course,
                        {
                            "action": "DELETE_LESSON",
                            "lesson_id": str(lesson.public_id),
                            "title": lesson.title,
                            "unit_id": str(unit.public_id),
                        },
                        key=f"lesson:{lesson.public_id}",
                        session=sess,
                    )
        if session is None:
            sess.commit()
        return True

    now = utc_now()
    for lesson in unit.lessons:
        if lesson.deleted_at is None:
            lesson.deleted_at = now
            lesson.status = "TRASH"
            lesson.deleted_by_user_id = actor.id
            lesson.position = TRASH_POSITION_BASE + lesson.id
            lesson.updated_at = now
            _cleanup_lesson_resources(sess, lesson, actor, now)

    unit.deleted_at = now
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
    _ensure_course_not_pending_changeset(course.id, actor, session=sess)
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
    if (
        not isinstance(ordered_unit_ids, list)
        or len(set(map(str, ordered_unit_ids))) != len(ordered_unit_ids)
        or any(str(uid) not in unit_map for uid in ordered_unit_ids)
    ):
        raise LessonValidationError(
            "Learning unit order must contain distinct units from this course."
        )
    if should_stage(actor, course, sess):
        stage_course_operation(
            actor,
            course,
            {"action": "REORDER_LEARNING_UNITS", "unit_ids": list(map(str, ordered_unit_ids))},
            key="unit_order",
            session=sess,
        )
        if session is None:
            sess.commit()
        return list_learning_units(actor, course.id, session=sess)
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


def _score_lesson_quiz_answers(
    questions: list[dict[str, Any]], answers: list[Any]
) -> tuple[int, int, float]:
    """Score submitted answers against lesson quiz questions.
    Returns (correct_count, total_count, percentage).
    """
    total = len(questions)
    if total == 0:
        return 0, 0, 100.0

    correct_count = 0
    for question, answer in zip(questions, answers, strict=False):
        q_type = str(question.get("type") or "MULTIPLE_CHOICE").upper()
        if q_type == "MULTIPLE_CHOICE":
            raw_ca = question.get("correct_answers")
            if isinstance(raw_ca, list):
                expected_set = set(raw_ca)
            elif isinstance(question.get("correct_index"), int):
                expected_set = {question["correct_index"]}
            else:
                expected_set = {0}
            selected = answer if isinstance(answer, list) else [answer]
            selected_set = {
                int(x) for x in selected if isinstance(x, (int, str)) and str(x).isdigit()
            }
            if expected_set == selected_set:
                correct_count += 1
        elif q_type == "FILL_BLANK":
            blanks = question.get("blanks") or []
            values = answer if isinstance(answer, list) else [answer]
            all_correct = True
            for b_idx, b_def in enumerate(blanks):
                raw_accepted = b_def.get("accepted_answers") if isinstance(b_def, dict) else []
                if isinstance(raw_accepted, str):
                    accepted_list: list[Any] = [raw_accepted]
                elif isinstance(raw_accepted, list):
                    accepted_list = list(raw_accepted)
                else:
                    accepted_list = []
                accepted_norm = [str(a).strip().lower() for a in accepted_list if a]
                user_val = str(values[b_idx]).strip().lower() if b_idx < len(values) else ""
                if not user_val or user_val not in accepted_norm:
                    all_correct = False
                    break
            if all_correct and len(blanks) > 0:
                correct_count += 1
        elif q_type == "MATCHING":
            pairs = question.get("pairs") or []
            all_correct = True
            if isinstance(answer, dict):
                for p_idx, pair in enumerate(pairs):
                    expected_right = pair.get("right")
                    pair_user_val = answer.get(str(p_idx)) or answer.get(p_idx)
                    if pair_user_val != expected_right:
                        all_correct = False
                        break
            elif isinstance(answer, list):
                for p_idx, pair in enumerate(pairs):
                    expected_right = pair.get("right")
                    pair_user_val = answer[p_idx] if p_idx < len(answer) else None
                    if pair_user_val != expected_right:
                        all_correct = False
                        break
            else:
                all_correct = False
            if all_correct and len(pairs) > 0:
                correct_count += 1
        elif q_type == "TRUE_FALSE":
            raw_ca = question.get("correct_value")
            if raw_ca is None:
                raw_ca = question.get("correct_answer")
            expected_val = (
                raw_ca is True or str(raw_ca).strip().lower() in ("true", "1")
                if raw_ca is not None
                else True
            )
            tf_user_val = answer is True or str(answer).strip().lower() in ("true", "1")
            if tf_user_val == expected_val:
                correct_count += 1
        elif q_type in ("SHORT_ANSWER", "ESSAY"):
            accepted = question.get("accepted_answers") or []
            if accepted:
                if str(answer).strip().lower() in [str(a).strip().lower() for a in accepted]:
                    correct_count += 1
            else:
                if str(answer).strip():
                    correct_count += 1

    percent = (correct_count / total) * 100.0
    return correct_count, total, percent


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
    _ensure_course_not_pending_changeset(course.id, actor, session=sess)

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

    # Parse and validate estimated_duration_minutes (optional)
    raw_est = data.get("estimated_duration_minutes")
    est_duration = None
    if raw_est is not None:
        try:
            est_duration = int(raw_est)
            if est_duration < 0:
                est_duration = None
        except (ValueError, TypeError):
            est_duration = None

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

    draft_request = (
        working_changeset(actor, course, sess) if should_stage(actor, course, sess) else None
    )
    if draft_request:
        status = "DRAFT"

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
        if should_stage(actor, course, sess):
            record = active_changeset(course.id, sess)
            operations = payload_for(record).get("operations", {}) if record else {}
            if operations.get(f"unit:{existing_unit.public_id}", {}).get("action") == "DELETE_LEARNING_UNIT":
                raise LessonStateViolationError("Cannot add lesson to a unit scheduled for deletion.")
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
    if draft_request:
        change_req_id = draft_request.id

    if change_req_id or status == "PENDING_APPROVAL" or data.get("previous_lesson_id"):
        # Staged or draft lesson targeting a position for future approval / replacement
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
    _ensure_course_not_pending_changeset(course.id, actor, session=sess)
    if should_stage(actor, course, sess) and "status" in data:
        change_lesson_status(actor, lesson.id, data["status"], session=sess)
        data = {key: value for key, value in data.items() if key != "status"}
    if (
        should_stage(actor, course, sess)
        and lesson.change_request_id is None
        and lesson.status in ("DRAFT", "ACTIVE", "PUBLISHED", "HIDDEN")
    ):
        existing = (
            sess.query(Lesson)
            .filter(
                Lesson.course_id == course.id,
                Lesson.previous_lesson_id == lesson.id,
                Lesson.status == "DRAFT",
                Lesson.deleted_at.is_(None),
            )
            .first()
        )
        if existing is not None:
            return update_lesson(actor, existing.id, data, session=session)
        authored = {
            "title": lesson.title,
            "summary": lesson.summary,
            "markdown_content": lesson.markdown_content,
            "position": lesson.position,
            "learning_unit_id": str(lesson.learning_unit.public_id),
            "minimum_completion_seconds": lesson.minimum_completion_seconds,
            "viewed_fraction_required": float(lesson.viewed_fraction_required),
            "estimated_duration_minutes": lesson.estimated_duration_minutes,
            "required_for_periods_starting_at": lesson.required_for_periods_starting_at,
            **data,
        }
        authored["status"] = "DRAFT"
        staged = create_lesson(actor, course.id, authored, session=sess)
        staged.previous_lesson_id = lesson.id
        _copy_lesson_resources(lesson.id, staged.id, session=sess)
        if session is None:
            sess.commit()
        return staged
    if course.status == "SUBMITTED_FOR_REVIEW" and not actor.is_admin:
        raise LessonStateViolationError(
            "Khóa học đang chờ Quản trị viên xét duyệt. Không thể chỉnh sửa bài giảng."
        )

    # Disallow modifying position via update_lesson unless moving unit
    if "position" in data and data["position"] != lesson.position:
        if "learning_unit_id" in data and data["learning_unit_id"] != lesson.learning_unit_id:
            try:
                new_pos = int(data["position"])
                if new_pos > 0:
                    lesson.position = new_pos
            except (ValueError, TypeError):
                pass
        else:
            raise LessonValidationError(
                "Lesson position cannot be modified via update. Use reorder_lessons."
            )

    if "learning_unit_id" in data:
        target_unit_id = data["learning_unit_id"]
        if target_unit_id is not None:
            target_unit = _resolve_learning_unit(target_unit_id, session=sess)
            if target_unit is None or target_unit.course_id != course.id:
                raise LessonValidationError("Target learning unit does not belong to this course.")
            lesson.learning_unit_id = target_unit.id
        else:
            lesson.learning_unit_id = None

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
        raw_dur = data["estimated_duration_minutes"]
        if raw_dur is not None:
            try:
                dur_int = int(raw_dur)
                lesson.estimated_duration_minutes = dur_int if dur_int >= 0 else None
            except (ValueError, TypeError):
                lesson.estimated_duration_minutes = None
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
    *,
    move: dict[str, Any] | None = None,
    validate_only: bool = False,
) -> list[Lesson]:
    """Reorder lessons to maintain a contiguous 1..N sequence without unique collisions.

    Uses a 2-phase update with temporary positive offsets within the same transaction.

    Args:
        actor: Authenticated user initiating reordering.
        course_id: Identifier of the course.
        ordered_lesson_ids: Full ordered list of lesson IDs representing new sequence.
        session: Optional SQLAlchemy session.
        move: Optional lesson and destination-unit identifiers applied with the order.
        validate_only: Validate a queued review intent without modifying curriculum or audit.

    Returns:
        List of reordered Lesson instances sorted by new position.

    Raises:
        LessonPositionConflictError: If ordered_lesson_ids does not match course active lessons.
        ForbiddenError: If actor cannot manage course.
        ResourceNotFoundError: If course is not found.
    """
    sess = session if session is not None else db.session
    course = require_course_manager(actor, course_id, session=sess)
    course = (
        sess.query(Course)
        .filter_by(id=course.id)
        .with_hint(Course, "WITH (UPDLOCK, HOLDLOCK)", dialect_name="mssql")
        .with_for_update()
        .populate_existing()
        .one()
    )
    _ensure_course_not_pending_changeset(course.id, actor, session=sess)
    if course.status == "SUBMITTED_FOR_REVIEW" and not actor.is_admin:
        raise LessonStateViolationError(
            "Khóa học đang chờ Quản trị viên xét duyệt. Không thể sắp xếp lại bài giảng."
        )

    active_lessons = (
        sess.query(Lesson)
        .filter(Lesson.course_id == course.id, Lesson.deleted_at.is_(None))
        .populate_existing()
        .all()
    )

    if not ordered_lesson_ids and not active_lessons:
        if move is not None:
            raise LessonPositionConflictError("An empty course has no lesson to move.")
        return []

    # Map existing active lessons by internal id and string/UUID public_id
    id_map: dict[int, Lesson] = {les.id: les for les in active_lessons}
    public_id_map: dict[str, Lesson] = {str(les.public_id): les for les in active_lessons}

    resolved_ordered: list[Lesson] = []
    seen_ids: set[int] = set()

    for item in ordered_lesson_ids:
        target_val = (item.get("lesson_id") or item.get("id")) if isinstance(item, dict) else item
        matched: Lesson | None = None
        if isinstance(target_val, int):
            matched = id_map.get(target_val)
        elif isinstance(target_val, uuid.UUID):
            matched = public_id_map.get(str(target_val))
        elif isinstance(target_val, str):
            if target_val.isdigit():
                matched = id_map.get(int(target_val))
            if matched is None:
                matched = public_id_map.get(target_val.strip().lower())

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

    moved_lesson = None
    target_unit = None
    if move is not None:
        if not isinstance(move, dict):
            raise LessonValidationError("move must be an object.")
        lesson_ref = move.get("lesson_id")
        unit_ref = move.get("learning_unit_id")
        if (
            not isinstance(lesson_ref, (int, uuid.UUID, str))
            or isinstance(lesson_ref, bool)
            or not isinstance(unit_ref, (int, uuid.UUID, str))
            or isinstance(unit_ref, bool)
        ):
            raise LessonValidationError("move requires lesson_id and learning_unit_id identifiers.")
        moved_lesson = _resolve_lesson(lesson_ref, session=sess)
        target_unit = _resolve_learning_unit(unit_ref, session=sess)
        if (
            moved_lesson is None
            or moved_lesson.id not in seen_ids
            or moved_lesson.status in ("TRASH", "HISTORICAL")
            or target_unit is None
            or target_unit.course_id != course.id
            or target_unit.deleted_at is not None
        ):
            raise LessonValidationError(
                "Moved lesson and target unit must be active in this course."
            )
        target_unit = (
            sess.query(LearningUnit)
            .filter_by(id=target_unit.id)
            .with_hint(LearningUnit, "WITH (UPDLOCK, HOLDLOCK)", dialect_name="mssql")
            .with_for_update()
            .populate_existing()
            .one()
        )
        if target_unit.deleted_at is not None:
            raise LessonValidationError("Target learning unit is no longer active.")
        sess.expire(target_unit, ["lessons"])
        if moved_lesson.learning_unit_id != target_unit.id:
            siblings = [
                lesson
                for lesson in target_unit.lessons
                if lesson.deleted_at is None and lesson.status not in ("TRASH", "HISTORICAL")
            ]
            if len(siblings) >= 10:
                raise LessonValidationError("A learning unit can contain at most 10 lessons.")
            validate_lesson_media_limits(target_unit, moved_lesson, moved_lesson.markdown_content)

    if validate_only:
        return resolved_ordered

    if should_stage(actor, course, sess):
        if moved_lesson is not None and target_unit is not None:
            update_lesson(
                actor,
                moved_lesson.id,
                {"learning_unit_id": str(target_unit.public_id)},
                session=sess,
            )
        stage_course_fields(
            actor,
            course,
            "reorder_plan",
            {"lessons_order": [str(item.public_id) for item in resolved_ordered]},
            session=sess,
        )
        if session is None:
            sess.commit()
        return resolved_ordered

    if moved_lesson is not None and target_unit is not None:
        moved_lesson.learning_unit_id = target_unit.id

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
        {
            "lesson_id": str(les.public_id),
            "position": les.position,
            "learning_unit_id": les.learning_unit_id,
        }
        for les in resolved_ordered
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
    _ensure_course_not_pending_changeset(course.id, actor, session=sess)
    if course.status == "SUBMITTED_FOR_REVIEW" and not actor.is_admin:
        raise LessonStateViolationError(
            "Khóa học đang chờ Quản trị viên xét duyệt. Không thể xóa bài giảng."
        )

    if lesson.deleted_at is not None or lesson.status == "TRASH":
        return lesson

    if should_stage(actor, course, sess) and lesson.change_request_id is None:
        stage_course_operation(
            actor,
            course,
            {"action": "DELETE_LESSON", "lesson_id": str(lesson.public_id)},
            key=f"lesson:{lesson.public_id}:delete",
            session=sess,
        )
        if session is None:
            sess.commit()
        return cast(Lesson, AuthoringProjection(lesson, {"pending_delete": True}))

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

    # Clean up associated LessonResource entries and mark orphaned FileAssets as TRASH
    _cleanup_lesson_resources(sess, lesson, actor, now)

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
    _ensure_course_not_pending_changeset(course.id, actor, session=sess)

    if new_status not in VALID_LESSON_STATUSES:
        valid_str = ", ".join(sorted(VALID_LESSON_STATUSES))
        raise LessonValidationError(
            f"Invalid status: '{new_status}'. Allowed transitions: {valid_str}."
        )

    if new_status == "PUBLISHED" and course.status in ("TRASH", "ARCHIVED"):
        raise LessonStateViolationError(
            f"Cannot publish lesson in a course with '{course.status}' status."
        )

    if should_stage(actor, course, sess):
        stage_course_operation(
            actor,
            course,
            {
                "action": "LESSON_STATUS",
                "lesson_id": str(lesson.public_id),
                "target_status": new_status,
            },
            key=f"lesson:{lesson.public_id}:status",
            session=sess,
        )
        if session is None:
            sess.commit()
        return cast(Lesson, AuthoringProjection(lesson, {"is_draft": True}))

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
        if lesson.deleted_at is None:
            return get_lesson_detail_with_draft(actor, lesson.id, session=sess)[0]
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
        return get_lesson_detail_with_draft(actor, lesson.id, session=sess)[0]

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
        replaced = {
            item.previous_lesson_id
            for item in all_lessons
            if item.previous_lesson_id and item.status in ("DRAFT", "PENDING_APPROVAL")
        }
        result = [
            item
            for item in all_lessons
            if item.id not in replaced and item.status not in ("TRASH", "HISTORICAL")
        ]
        record = active_changeset(course.id, sess)
        if record:
            proposed = payload_for(record)
            operations = proposed.get("operations") or {}
            deleted = {
                item["lesson_id"]
                for item in operations.values()
                if item.get("action") == "DELETE_LESSON"
            }
            result = [item for item in result if str(item.public_id) not in deleted]
            order = proposed.get("reorder_plan", {}).get("lessons_order") or []
            ranks = {str(value): index for index, value in enumerate(order)}
            result.sort(
                key=lambda item: (
                    ranks.get(str(item.public_id), len(ranks) + item.position),
                    item.id,
                )
            )
            if order:
                result = [
                    cast(Lesson, AuthoringProjection(item, {"position": index}))
                    for index, item in enumerate(result, 1)
                ]
        return result

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
    enforce_wall_clock: bool = False,
    now: Any = None,
    server_verified: bool = False,
    is_completed: bool = False,
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
        vf = float(view_fraction)
    except (ValueError, TypeError):
        raise LessonValidationError("view_fraction must be a float.") from None
    if not (0.0 <= vf <= 1.0):
        raise LessonValidationError("view_fraction must be between 0.0 and 1.0.")

    try:
        sec = int(seconds_increment)
    except (ValueError, TypeError):
        raise LessonValidationError("seconds_increment must be an integer.") from None
    if sec < (0 if (server_verified or vf >= 1.0) else 1) or sec > MAX_PING_SECONDS:
        raise LessonValidationError(
            f"seconds_increment must be between 1 and {MAX_PING_SECONDS} seconds."
        )

    if _lesson_requires_video_watch(lesson) and not server_verified:
        raise LessonValidationError("A playback session is required for video progress.")

    event_id = None
    if client_event_id is not None:
        event_id = str(client_event_id).strip()
        if not event_id or len(event_id) > 128 or not event_id.isascii():
            raise LessonValidationError("client_event_id must contain 1..128 ASCII characters.")

    # Verify student enrollment (ACTIVE or COMPLETED)
    enrollment = (
        sess.query(Enrollment)
        .filter(
            Enrollment.student_user_id == actor.id,
            Enrollment.course_id == lesson.course_id,
            Enrollment.status.in_(["ACTIVE", "COMPLETED"]),
        )
        .with_hint(Enrollment, "WITH (UPDLOCK, HOLDLOCK)", dialect_name="mssql")
        .with_for_update()
        .populate_existing()
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
        .populate_existing()
        .first()
    )

    if progress is None and lesson.status == "HISTORICAL":
        raise LessonStateViolationError("Cannot start progress on a historical lesson revision.")

    now_ts = now if now is not None else utc_now()
    if progress is None:
        progress = LessonProgress(
            enrollment_period_id=active_period.id,
            lesson_id=lesson.id,
            seconds_spent=0,
            max_view_fraction=0.0,
            acknowledged_revision_no=lesson.revision_no,
            updated_at=now_ts,
        )
        sess.add(progress)
        sess.flush()

    if event_id is not None:
        receipt = (
            sess.query(LessonProgressReceipt)
            .filter_by(
                enrollment_period_id=active_period.id,
                lesson_id=lesson.id,
                client_event_id=event_id,
            )
            .first()
        )
        if receipt is not None:
            return progress
        sess.add(
            LessonProgressReceipt(
                enrollment_period_id=active_period.id,
                lesson_id=lesson.id,
                client_event_id=event_id,
                created_at=now_ts,
            )
        )

    # Server-Authoritative Wall-Clock Pacing Enforcement (Anti-Bypass Iron Law)
    credited_sec = sec
    if enforce_wall_clock and not server_verified and progress.last_activity_at is None:
        credited_sec = 0
    if enforce_wall_clock and not server_verified and progress.last_activity_at is not None:
        now_clean = _to_naive_utc(now_ts)
        last_clean = _to_naive_utc(progress.last_activity_at)
        elapsed = (now_clean - last_clean).total_seconds() if (now_clean and last_clean) else 0.0
        # Cap credited increment to actual elapsed wall-clock seconds (+2.0s network jitter tolerance)
        max_credible = max(0, int(elapsed)) if elapsed <= 20 else 0
        if sec > max_credible:
            credited_sec = max(0, min(sec, max_credible))
            if sec - elapsed > 5.0:
                actor_roles = (
                    ",".join(sorted(r.code for r in getattr(actor, "roles", []))) or "STUDENT"
                )
                audit_ev = AuditEvent(
                    action="LESSON_PROGRESS_PACE_ANOMALY",
                    actor_user_id=actor.id,
                    actor_roles_snapshot=actor_roles,
                    target_type="Lesson",
                    target_id=lesson.id,
                    after_json=json.dumps(
                        {
                            "claimed_increment": sec,
                            "credited_seconds": credited_sec,
                            "elapsed_seconds": round(elapsed, 2),
                            "lesson_title": lesson.title,
                        }
                    ),
                    created_at=now_ts,
                )
                sess.add(audit_ev)

    # Bounded accumulated active seconds & high-water-mark view fraction
    progress.seconds_spent = (progress.seconds_spent or 0) + credited_sec
    current_fraction = float(progress.max_view_fraction or 0.0)
    progress.max_view_fraction = max(current_fraction, vf)
    progress.acknowledged_revision_no = lesson.revision_no
    progress.last_activity_at = now_ts
    progress.updated_at = now_ts

    # Evaluate completion: monotonic, idempotent
    # Invariant: Respect lesson configuration while strictly enforcing completion requirements.
    requires_video = _lesson_requires_video_watch(lesson)
    min_completion_seconds = (
        0
        if requires_video
        else (
            lesson.minimum_completion_seconds
            if lesson.minimum_completion_seconds is not None
            else 30
        )
    )
    viewed_fraction_required = (
        1.0 if requires_video else float(lesson.viewed_fraction_required or 0.0)
    )

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
    if requires_video:
        fraction_ok = (
            float(progress.max_view_fraction) >= 1.0
            or vf >= 1.0
            or is_completed
        )
        criteria_met = fraction_ok and quiz_is_complete
    else:
        time_spent_ok = (progress.seconds_spent >= min_completion_seconds) or (
            min_completion_seconds == 0
        ) or is_completed
        fraction_ok = (
            float(progress.max_view_fraction) >= viewed_fraction_required
            or vf >= viewed_fraction_required
            or is_completed
        )
        criteria_met = (time_spent_ok and fraction_ok and quiz_is_complete) or (
            is_completed and quiz_is_complete
        )

    newly_completed = False
    if criteria_met and progress.completed_at is None:
        progress.completed_at = now_ts
        progress_snapshot.update(
            {
                "minimum_completion_seconds": min_completion_seconds,
                "viewed_fraction_required": viewed_fraction_required,
                "completed_at": now_ts.isoformat(),
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

    passing_percent = 80.0
    match_pass = re.search(
        r"<!--\s*(?:mini_quiz_passing|quiz_passing_percent):\s*(\d+)", lesson.markdown_content or ""
    )
    if match_pass:
        try:
            passing_percent = float(match_pass.group(1))
        except (ValueError, TypeError):
            passing_percent = 80.0

    correct_count, total_count, percent = _score_lesson_quiz_answers(questions, answers)
    if percent < passing_percent:
        raise LessonValidationError(
            f"Điểm kiểm tra {percent:.0f}% ({correct_count}/{total_count}) chưa đạt ngưỡng yêu cầu {passing_percent:.0f}%."
        )

    requires_video_watch = _lesson_requires_video_watch(lesson)
    video_view_fraction_required = (
        1.0 if requires_video_watch else float(lesson.viewed_fraction_required)
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
        seconds_increment=0,
        view_fraction=0.0 if requires_video_watch else 1.0,
        session=sess,
        server_verified=True,
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
    min_required_secs = (
        lesson.minimum_completion_seconds
        if lesson.minimum_completion_seconds is not None
        else (0 if requires_video_watch else 30)
    )
    if (
        progress.completed_at is None
        and progress.seconds_spent >= min_required_secs
        and float(progress.max_view_fraction) >= video_view_fraction_required
    ):
        progress.completed_at = now
        progress_snapshot.update(
            {
                "minimum_completion_seconds": min_required_secs,
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


submit_lesson_quiz = complete_lesson_mini_quiz


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
) -> CourseChangeRequest | None:
    """Compatibility authoring alias; post-approval saves use the one course draft."""
    sess = session if session is not None else db.session
    require_course_manager(actor, course.id, session=sess)
    if lesson.course_id != course.id:
        raise ResourceNotFoundError("Lesson not found in course.")
    ensure_course_authoring(actor, course, session=sess)
    if should_stage(actor, course, sess):
        if proposal.get("action") in ("DELETE", "DELETE_LESSON"):
            trash_lesson(actor, lesson.id, session=sess)
        elif proposal.get("action") == "RESOURCE_CHANGES":
            from pwd301.services.file_service import (
                attach_resource_to_lesson,
                detach_resource_from_lesson,
            )

            staged = update_lesson(actor, lesson.id, {}, session=sess)
            _validate_proposed_resource_changes(staged, proposal, sess)
            for change in proposal.get("changes") or []:
                if change.get("action") == "ATTACH":
                    attach_resource_to_lesson(
                        actor,
                        staged.id,
                        change["asset_id"],
                        label=change.get("label"),
                        is_downloadable=change.get("is_downloadable", True),
                        session=sess,
                        commit=False,
                    )
                elif change.get("action") == "DETACH":
                    original = next(
                        (
                            resource
                            for resource in lesson.resources
                            if resource.id == change["resource_id"]
                        ),
                        None,
                    )
                    if original is None:
                        raise LessonValidationError("Resource must belong to this lesson.")
                    target = next(
                        (
                            resource
                            for resource in staged.resources
                            if resource.file_asset_id == original.file_asset_id
                        ),
                        None,
                    )
                    if target:
                        detach_resource_from_lesson(
                            actor, staged.id, target.id, session=sess, commit=False
                        )
        else:
            update_lesson(actor, lesson.id, proposal, session=sess)
        record = working_changeset(actor, course, sess)
        if session is None:
            sess.commit()
        return record
    if proposal.get("action") in ("DELETE", "DELETE_LESSON"):
        trash_lesson(actor, lesson.id, session=sess)
    elif proposal.get("action") == "RESOURCE_CHANGES":
        from pwd301.services.file_service import (
            attach_resource_to_lesson,
            detach_resource_from_lesson,
        )

        for change in proposal.get("changes") or []:
            if change.get("action") == "ATTACH":
                attach_resource_to_lesson(
                    actor,
                    lesson.id,
                    change["asset_id"],
                    label=change.get("label"),
                    session=sess,
                    commit=False,
                )
            elif change.get("action") == "DETACH":
                detach_resource_from_lesson(
                    actor, lesson.id, change["resource_id"], session=sess, commit=False
                )
    else:
        update_lesson(actor, lesson.id, proposal, session=sess)
    if session is None:
        sess.commit()
    return None


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
) -> CourseChangeRequest | None:
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


def create_lesson_change_request(actor, course_id, payload, session=None):
    """Compatibility entry point delegates to mandatory course-level authoring."""
    sess = session if session is not None else db.session
    course = ensure_course_authoring(actor, course_id, session=sess)
    target = payload.get("target_id") or payload.get("lesson_id")
    if target:
        original = _resolve_lesson(target, session=sess)
        if original is None or original.course_id != course.id or original.deleted_at is not None:
            raise LessonValidationError("Target lesson must be active in this course.")
        staged = update_lesson(actor, original.id, payload, session=sess)
    else:
        staged = create_lesson(actor, course.id, payload, session=sess)
    record = active_changeset(course.id, sess)
    if session is None:
        sess.commit()
    return record, staged


def lock_course_change_request(sess, change_request_id):
    """Serialize review decisions and curriculum mutations for the same course."""
    req = sess.get(CourseChangeRequest, change_request_id)
    if req is None:
        raise ResourceNotFoundError("Course change request not found.")
    sess.query(Course).filter(Course.id == req.course_id).with_hint(
        Course, "WITH (UPDLOCK, HOLDLOCK)", dialect_name="mssql"
    ).with_for_update().populate_existing().one()
    return (
        sess.query(CourseChangeRequest)
        .filter(CourseChangeRequest.id == req.id)
        .with_hint(CourseChangeRequest, "WITH (UPDLOCK, HOLDLOCK)", dialect_name="mssql")
        .with_for_update()
        .populate_existing()
        .one()
    )


def record_change_request_review(sess, actor, req, decision):
    """Required audit stays in the transaction that applies the decision."""
    from pwd301.services.audit_service import record_audit_event

    record_audit_event(
        actor,
        f"COURSE_CHANGE_{decision}",
        "COURSE_CHANGE_REQUEST",
        req.id,
        reason=req.review_reason,
        before_state={"status": "PENDING"},
        after_state={"status": decision, "course_id": str(req.course.public_id)},
        session=sess,
    )


def _apply_course_metadata_dict(
    course: Course,
    metadata: dict[str, Any],
    session: Session | scoped_session[Any],
    now: datetime.datetime,
) -> None:
    """Apply validated course metadata dictionary to Course instance in the active session."""
    if not metadata or not isinstance(metadata, dict):
        return
    sess = session if session is not None else db.session
    if "title" in metadata and metadata["title"]:
        title = str(metadata["title"]).strip()
        if title:
            course.title = title
            course.title_normalized = title.lower()
    if "description" in metadata:
        course.description = metadata["description"]
    if "learning_objectives" in metadata:
        lo = metadata["learning_objectives"]
        if isinstance(lo, (dict, list)):
            course.learning_objectives = json.dumps(lo, ensure_ascii=False)
        else:
            course.learning_objectives = str(lo) if lo is not None else None
    if "target_audience" in metadata:
        ta = metadata["target_audience"]
        course.target_audience = ta.strip() if isinstance(ta, str) else ta
    if "completion_requirements" in metadata:
        cr = metadata["completion_requirements"]
        if isinstance(cr, (dict, list)):
            course.completion_requirements = json.dumps(cr, ensure_ascii=False)
        else:
            course.completion_requirements = str(cr) if cr is not None else None
    if "category" in metadata:
        cat = metadata["category"]
        course.category = cat.strip() if isinstance(cat, str) else cat
    if "difficulty" in metadata:
        diff = metadata["difficulty"]
        course.difficulty = diff.upper() if isinstance(diff, str) and diff else None
    if "capacity" in metadata:
        cap = metadata["capacity"]
        try:
            course.capacity = int(cap) if cap is not None else None
        except (ValueError, TypeError):
            pass
    if "storage_quota_bytes" in metadata:
        quota = metadata["storage_quota_bytes"]
        try:
            course.storage_quota_bytes = int(quota) if quota is not None else None
        except (ValueError, TypeError):
            pass
    if "thumbnail_file_asset_id" in metadata:
        thumb = metadata["thumbnail_file_asset_id"]
        if thumb is not None:
            if isinstance(thumb, int) or (isinstance(thumb, str) and str(thumb).isdigit()):
                course.thumbnail_file_asset_id = int(thumb)
            else:
                try:
                    asset_uuid = uuid.UUID(str(thumb))
                    asset = sess.query(FileAsset).filter(FileAsset.public_id == asset_uuid).first()
                    if asset:
                        course.thumbnail_file_asset_id = asset.id
                except (ValueError, TypeError):
                    pass
        else:
            course.thumbnail_file_asset_id = None
    course.updated_at = now


def _apply_sealed_course_changeset(actor, req, proposed, sess):
    from pwd301.models.file_import import LessonResource
    from pwd301.services.course_service import update_course
    from pwd301.services.course_workflow_service import course_review_version

    if not actor.is_admin or not (
        actor.is_primary_admin or actor.has_admin_permission("COURSE_REVIEW")
    ):
        raise ForbiddenError("Only authorized administrators can approve course changes.")
    course = sess.get(Course, req.course_id)
    from pwd301.services.course_workflow_service import validate_submitted_assets

    validate_submitted_assets(course, proposed.get("asset_manifest"), sess)
    if (
        proposed.get("baseline_version")
        and course_review_version(course, sess) != proposed["baseline_version"]
    ):
        raise ConflictError(
            "Nội dung đã duyệt thay đổi sau khi gửi. Hãy rút lại và gửi phiên bản mới."
        )
    now = utc_now()
    with applying_review(sess):
        if proposed.get("course_metadata"):
            update_course(
                actor, course, proposed["course_metadata"], session=sess, is_approved_review=True
            )
        # Sanitize any lingering soft-deleted lessons in this course that still hold active/published status
        # to ensure they never collide with active lesson positions in uq_lessons_course_position_active
        lingering = (
            sess.query(Lesson)
            .filter(
                Lesson.course_id == course.id,
                Lesson.deleted_at.isnot(None),
                Lesson.status.in_(("ACTIVE", "PUBLISHED")),
            )
            .all()
        )
        for bad_l in lingering:
            bad_l.status = "TRASH"
            bad_l.position = TRASH_POSITION_BASE + bad_l.id
        if lingering:
            sess.flush()
        snapshots = proposed["submitted_snapshot"].get("lessons") or []
        submitted_ids = [item["id"] for item in snapshots]
        members = (
            sess.query(Lesson)
            .filter(
                Lesson.id.in_(submitted_ids),
                Lesson.course_id == course.id,
                Lesson.change_request_id == req.id,
                Lesson.status == "PENDING_APPROVAL",
                Lesson.deleted_at.is_(None),
            )
            .all()
            if submitted_ids
            else []
        )
        if len(members) != len(submitted_ids):
            raise ConflictError("Thành viên bản gửi duyệt đã thay đổi; hãy tải lại bản xét duyệt.")
        live = (
            sess.query(Lesson)
            .filter(
                Lesson.course_id == course.id,
                Lesson.deleted_at.is_(None),
                Lesson.status.in_(("ACTIVE", "PUBLISHED", "HIDDEN")),
            )
            .all()
        )
        intended_positions = {item.id: item.position for item in live}
        for index, lesson in enumerate(live + members):
            lesson.position = TEMP_POSITION_OFFSET + index + 1
        sess.flush()
        by_id = {item.id: item for item in members}
        for snapshot in snapshots:
            lesson = by_id[snapshot["id"]]
            if lesson.previous_lesson_id:
                original = sess.get(Lesson, lesson.previous_lesson_id)
                if original is None or original.course_id != course.id:
                    raise LessonValidationError("Lesson revision must reference this course.")
                original.status = "HISTORICAL"
                original.updated_at = now
                lesson.revision_no = original.revision_no + 1
                intended_positions.pop(original.id, None)
            for key in (
                "title",
                "summary",
                "markdown_content",
                "learning_unit_id",
                "estimated_duration_minutes",
                "minimum_completion_seconds",
                "viewed_fraction_required",
            ):
                setattr(lesson, key, snapshot[key])
            when = snapshot.get("required_for_periods_starting_at")
            lesson.required_for_periods_starting_at = (
                datetime.datetime.fromisoformat(when) if when else None
            )
            for resource in list(lesson.resources):
                sess.delete(resource)
            sess.flush()
            for resource in snapshot.get("resources") or []:
                asset = sess.get(FileAsset, resource["file_asset_id"])
                if asset is None or asset.course_id != course.id or asset.deleted_at is not None:
                    raise LessonValidationError("Submitted lesson resource is no longer available.")
                sess.add(
                    LessonResource(
                        lesson_id=lesson.id,
                        file_asset_id=asset.id,
                        position=resource["position"],
                        label=resource.get("label"),
                        is_required=resource.get("is_required", False),
                        created_at=now,
                    )
                )
            lesson.status = "PUBLISHED"
            lesson.published_at = lesson.published_at or now
            lesson.updated_at = now
            lesson.change_request_id = None
            intended_positions[lesson.id] = snapshot["position"]
        for unit in sess.query(LearningUnit).filter(LearningUnit.change_request_id == req.id).all():
            unit.change_request_id = None
        if proposed.get("completion_rules"):
            from pwd301.services.completion_service import set_course_completion_rule

            set_course_completion_rule(actor, course.id, proposed["completion_rules"], session=sess)
        if proposed.get("prerequisites"):
            from pwd301.services.enrollment_service import (
                add_course_prerequisite,
                remove_course_prerequisite,
            )

            for public_id in proposed["prerequisites"].get("remove") or []:
                remove_course_prerequisite(actor, course.id, public_id, session=sess)
            for public_id in proposed["prerequisites"].get("add") or []:
                add_course_prerequisite(actor, course.id, public_id, session=sess)
        operations = list((proposed.get("operations") or {}).values())
        operations.sort(
            key=lambda item: (
                0
                if item.get("action", "").startswith("QUESTION_")
                else 2
                if item.get("action", "").startswith("ASSESSMENT_")
                else 1
            )
        )
        question_id_map: dict[int, int] = {}
        for operation in operations:
            action = operation.get("action")
            if action in ("CREATE_LEARNING_UNIT", "UPDATE_LEARNING_UNIT"):
                unit = _resolve_learning_unit(operation["unit_id"], session=sess)
                if unit is None or unit.course_id != course.id:
                    raise LessonValidationError(
                        "Submitted learning unit must belong to this course."
                    )
                unit.title = operation["title"]
            elif action == "DELETE_LEARNING_UNIT":
                delete_learning_unit(actor, operation["unit_id"], session=sess)
            elif action == "REORDER_LEARNING_UNITS":
                reorder_learning_units(actor, course.id, operation["unit_ids"], session=sess)
            elif action == "DELETE_LESSON":
                lesson = _resolve_lesson(operation["lesson_id"], session=sess)
                if lesson is None or lesson.course_id != course.id:
                    raise LessonValidationError("Submitted lesson must belong to this course.")
                trash_lesson(actor, lesson.id, session=sess)
            elif action == "LESSON_STATUS":
                lesson = _resolve_lesson(operation["lesson_id"], session=sess)
                if lesson is None or lesson.course_id != course.id:
                    raise LessonValidationError("Submitted lesson must belong to this course.")
                if lesson.status == "HISTORICAL":
                    lesson = (
                        sess.query(Lesson)
                        .filter_by(previous_lesson_id=lesson.id, change_request_id=req.id)
                        .first()
                        or lesson
                    )
                change_lesson_status(actor, lesson.id, operation["target_status"], session=sess)
            elif action.startswith("ASSESSMENT_"):
                from pwd301.services.assessment_service import apply_course_assessment_operation

                snapshots = proposed["submitted_snapshot"].get("assessments") or {}
                snapshot = snapshots.get(operation["assessment_id"])
                if snapshot:
                    import copy

                    snapshot = copy.deepcopy(snapshot)
                    for item in snapshot.get("assignments", []) + snapshot.get("pool", []):
                        item["question_id"] = question_id_map.get(
                            item["question_id"], item["question_id"]
                        )
                apply_course_assessment_operation(
                    actor, course.id, {**operation, "snapshot": snapshot}, session=sess
                )
            elif action.startswith("QUESTION_"):
                from pwd301.services.question_bank_service import apply_course_question_operation

                question_id_map.update(
                    apply_course_question_operation(actor, course.id, operation, session=sess) or {}
                )
            else:
                raise LessonValidationError("Unsupported submitted course operation.")
        remaining = (
            sess.query(Lesson)
            .filter(
                Lesson.course_id == course.id,
                Lesson.deleted_at.is_(None),
                Lesson.status.in_(("ACTIVE", "PUBLISHED", "HIDDEN")),
            )
            .all()
        )
        order = proposed.get("reorder_plan", {}).get("lessons_order") or []
        ranks = {}
        for index, value in enumerate(order):
            if isinstance(value, dict):
                lid = str(value.get("lesson_id") or value.get("id") or "")
                pos = value.get("position", index)
                ranks[lid] = pos if pos is not None else index
            else:
                ranks[str(value)] = index
        for item in remaining:
            if item.previous_lesson_id:
                orig = sess.get(Lesson, item.previous_lesson_id)
                if orig:
                    if str(orig.public_id) in ranks and str(item.public_id) not in ranks:
                        ranks[str(item.public_id)] = ranks[str(orig.public_id)]
                    if str(orig.id) in ranks and str(item.id) not in ranks:
                        ranks[str(item.id)] = ranks[str(orig.id)]
        remaining.sort(
            key=lambda item: (
                ranks.get(
                    str(item.public_id), len(ranks) + intended_positions.get(item.id, item.position)
                ),
                0 if item.id in submitted_ids else 1,
                item.id,
            )
        )
        for index, lesson in enumerate(remaining):
            lesson.position = TEMP_POSITION_OFFSET + len(members) + len(live) + index + 1
        sess.flush()
        for index, lesson in enumerate(remaining, 1):
            lesson.position = index
        sess.flush()
        req.status = "APPROVED"
        req.reviewed_by_user_id = actor.id
        req.reviewed_at = now
        req.applied_at = now
        record_change_request_review(sess, actor, req, "APPROVED")
        sess.flush()


def approve_course_change_request(actor, change_request_id, review_reason=None, session=None):
    """Apply only a sealed complete course submission, with required audit."""
    sess = session if session is not None else db.session
    candidate = sess.get(CourseChangeRequest, change_request_id)
    if candidate is not None and payload_for(candidate).get("prerequisites"):
        from pwd301.services.course_workflow_service import lock_prerequisite_graph

        lock_prerequisite_graph(sess)
    req = lock_course_change_request(sess, change_request_id)
    if req.status != "PENDING":
        raise ConflictError("Bản gửi duyệt không còn chờ xét duyệt.")
    proposed = payload_for(req)
    if req.change_type != "COURSE_VERSION_CHANGESET" or "submitted_snapshot" not in proposed:
        raise ConflictError(
            "Yêu cầu cũ chưa được hợp nhất; cần đối soát thành một bản gửi duyệt đầy đủ."
        )
    req.review_reason = review_reason
    _apply_sealed_course_changeset(actor, req, proposed, sess)
    from pwd301.services.notification_service import dispatch_notification

    approved_key = uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"pwd301:course-change:{req.id}:COURSE_CHANGE_APPROVED:{req.requested_by_user_id}",
    )
    with contextlib.suppress(Exception):
        dispatch_notification(
            recipient_user=req.requested_by_user_id,
            event_type="COURSE_CHANGE_APPROVED",
            title=f"Đợt cập nhật khóa học {req.course.course_code} đã được phê duyệt",
            body=review_reason or "Đợt cập nhật khóa học của bạn đã được phê duyệt.",
            action_url=f"#/instructor/courses/{req.course.public_id}/curriculum",
            category="COURSE",
            payload={"course_id": str(req.course.public_id), "change_request_id": req.id},
            event_key=approved_key,
            session=sess,
        )
    if session is None:
        sess.commit()
    return req


def reject_course_change_request(actor, change_request_id, review_reason=None, session=None):
    sess = session if session is not None else db.session
    req = lock_course_change_request(sess, change_request_id)
    if not actor.is_admin or not (
        actor.is_primary_admin or actor.has_admin_permission("COURSE_REVIEW")
    ):
        raise ForbiddenError("Only authorized administrators can review course changes.")
    if req.status != "PENDING":
        raise ConflictError("Bản gửi duyệt không còn chờ xét duyệt.")
    if req.change_type != "COURSE_VERSION_CHANGESET" or "submitted_snapshot" not in payload_for(
        req
    ):
        raise ConflictError("Yêu cầu cũ chưa được hợp nhất; cần đối soát trước khi xét duyệt.")
    req.status = "REJECTED"
    req.reviewed_by_user_id = actor.id
    req.review_reason = review_reason
    req.reviewed_at = utc_now()
    record_change_request_review(sess, actor, req, "REJECTED")
    from pwd301.services.notification_service import dispatch_notification

    with contextlib.suppress(Exception):
        dispatch_notification(
            recipient_user=req.requested_by_user_id,
            event_type="COURSE_CHANGE_REJECTED",
            title=f"Đợt cập nhật khóa học {req.course.course_code} cần chỉnh sửa lại",
            body=review_reason or "Yêu cầu cập nhật khóa học của bạn đã bị từ chối.",
            action_url=f"#/instructor/courses/manage?id={req.course.public_id}",
            category="COURSE",
            payload={
                "course_id": str(req.course.public_id),
                "change_request_id": req.id,
                "action_url": f"#/instructor/courses/manage?id={req.course.public_id}",
            },
            session=sess,
        )
    sess.flush()
    successor_draft(actor, req, sess)
    if session is None:
        sess.commit()
    return req


def get_lesson_detail_with_draft(actor, lesson_id, session=None):
    sess = session if session is not None else db.session
    lesson = _resolve_lesson(lesson_id, session=sess)
    if lesson is None or lesson.deleted_at is not None:
        raise LessonNotFoundError("Lesson not found.")
    require_course_manager(actor, lesson.course_id, session=sess)
    req = active_changeset(lesson.course_id, sess)
    if req is None:
        return lesson, None
    staged = (
        lesson
        if lesson.change_request_id == req.id
        else sess.query(Lesson)
        .filter(
            Lesson.previous_lesson_id == lesson.id,
            Lesson.change_request_id == req.id,
            Lesson.status.in_(("DRAFT", "PENDING_APPROVAL")),
            Lesson.deleted_at.is_(None),
        )
        .first()
    )
    if staged is None:
        return lesson, None
    proposed = payload_for(req)
    previous = (
        sess.get(CourseChangeRequest, proposed.get("previous_request_id"))
        if proposed.get("previous_request_id")
        else None
    )
    from pwd301.services.course_workflow_service import review_version

    info = {
        "change_request_id": req.id,
        "request_id": req.id,
        "status": req.status,
        "review_version": review_version(req),
        "review_reason": previous.review_reason if previous else req.review_reason,
        "created_at": req.created_at.isoformat(),
        "payload": _submitted_lesson_snapshot(staged),
    }
    return staged, info


def discard_lesson_working_draft(actor, lesson_id, session=None):
    sess = session if session is not None else db.session
    lesson = _resolve_lesson(lesson_id, session=sess)
    if lesson is None:
        raise LessonNotFoundError("Lesson not found.")
    course = ensure_course_authoring(actor, lesson.course_id, session=sess)
    req = active_changeset(course.id, sess)
    if req is None:
        return False
    drafts = (
        sess.query(Lesson)
        .filter(
            Lesson.change_request_id == req.id,
            Lesson.course_id == course.id,
            sa.or_(Lesson.id == lesson.id, Lesson.previous_lesson_id == lesson.id),
            Lesson.status == "DRAFT",
            Lesson.deleted_at.is_(None),
        )
        .all()
    )
    for staged in drafts:
        staged.deleted_at = utc_now()
        staged.status = "TRASH"
    proposed = payload_for(req)
    operations = dict(proposed.get("operations") or {})
    for key, operation in list(operations.items()):
        if operation.get("lesson_id") in {
            str(lesson.public_id),
            *(str(item.public_id) for item in drafts),
        }:
            operations.pop(key)
    proposed["operations"] = operations
    write_payload(req, proposed, sess)
    if session is None:
        sess.commit()
    return bool(drafts)


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


def _submitted_lesson_snapshot(lesson):
    return {
        "lesson_id": str(lesson.public_id),
        "id": lesson.id,
        "previous_lesson_id": lesson.previous_lesson_id,
        "title": lesson.title,
        "summary": lesson.summary,
        "markdown_content": lesson.markdown_content,
        "position": lesson.position,
        "learning_unit_id": lesson.learning_unit_id,
        "estimated_duration_minutes": lesson.estimated_duration_minutes,
        "minimum_completion_seconds": lesson.minimum_completion_seconds,
        "viewed_fraction_required": float(lesson.viewed_fraction_required),
        "required_for_periods_starting_at": lesson.required_for_periods_starting_at.isoformat()
        if lesson.required_for_periods_starting_at
        else None,
        "resources": [
            {
                "file_asset_id": item.file_asset_id,
                "position": item.position,
                "label": item.label,
                "is_required": bool(item.is_required),
            }
            for item in lesson.resources
        ],
    }


def submit_course_changeset(actor, course_id, payload, session=None):
    """Seal exactly one complete working draft without changing the approved baseline."""
    sess = session if session is not None else db.session
    if not isinstance(payload, dict):
        raise LessonValidationError("Changeset submission must be a JSON object.")
    course = ensure_course_authoring(actor, course_id, session=sess)
    if not course_requires_review(course):
        raise ConflictError("Khóa học chưa được duyệt lần đầu; hãy gửi xét duyệt toàn bộ khóa học.")
    from pwd301.services.rate_limit_service import check_curriculum_mutation_rate_limit

    check_curriculum_mutation_rate_limit(actor.id, course.id, limit=15, window_seconds=60)
    if payload.get("course_metadata"):
        from pwd301.services.course_service import update_course

        update_course(actor, course.id, payload["course_metadata"], session=sess)
    for item in payload.get("modified_lessons") or []:
        if not isinstance(item, dict):
            raise LessonValidationError("Modified lessons must be objects.")
        lesson_id = item.get("lesson_id") or item.get("id")
        if not lesson_id:
            raise LessonValidationError("Modified lesson identity is required.")
        lesson = _resolve_lesson(lesson_id, session=sess)
        if lesson is None or lesson.course_id != course.id:
            raise LessonValidationError("Modified lesson must belong to this course.")
        changes = {
            key: value for key, value in item.items() if key not in ("id", "lesson_id", "target_id")
        }
        update_lesson(actor, lesson.id, changes, session=sess)
    for item in payload.get("deleted_lessons") or []:
        lid = item.get("lesson_id") if isinstance(item, dict) else item
        if not lid:
            raise LessonValidationError("Deleted lesson identity is required.")
        trash_lesson(actor, lid, session=sess)
    if payload.get("reorder_plan"):
        try:
            if payload.get("reorder_plan", {}).get("lessons_order"):
                reorder_lessons(actor, course.id, payload["reorder_plan"]["lessons_order"], session=sess)
        except LessonPositionConflictError:
            stage_course_fields(actor, course, "reorder_plan", payload["reorder_plan"], session=sess)
    for item in payload.get("added_lessons") or []:
        if not isinstance(item, dict):
            raise LessonValidationError("Added lessons must be objects.")
        candidate = item.get("temp_id") or item.get("lesson_id")
        existing = _resolve_lesson(candidate, session=sess) if candidate else None
        if existing is not None and existing.course_id != course.id:
            raise LessonValidationError("Added lesson must belong to this course.")
        if existing is None:
            create_lesson(actor, course.id, item, session=sess)
    record = active_changeset(course.id, sess)
    staged = (
        sess.query(Lesson)
        .filter(
            Lesson.course_id == course.id,
            sa.or_(
                Lesson.change_request_id == record.id if record else sa.false(),
                Lesson.change_request_id.is_(None),
            ),
            Lesson.deleted_at.is_(None),
            Lesson.status.in_(("DRAFT", "PENDING_APPROVAL")),
        )
        .all()
    )

    from pwd301.models.assessment import Assessment
    from pwd301.models.question_bank import Question

    staged_assessments = (
        sess.query(Assessment)
        .filter(
            Assessment.course_id == course.id,
            sa.or_(
                Assessment.change_request_id == record.id if record else sa.false(),
                Assessment.status == "DRAFT",
            ),
            Assessment.deleted_at.is_(None),
        )
        .all()
    )
    staged_questions = (
        sess.query(Question)
        .filter(
            Question.course_id == course.id,
            Question.change_request_id == record.id if record else sa.false(),
            Question.deleted_at.is_(None),
        )
        .all()
    )

    proposed = payload_for(record) if record else {}
    meaningful = bool(
        staged
        or staged_assessments
        or staged_questions
        or proposed.get("course_metadata")
        or proposed.get("completion_rules")
        or proposed.get("prerequisites")
        or proposed.get("operations")
        or proposed.get("deleted_lessons")
        or proposed.get("reorder_plan")
        or proposed.get("new_file_assets")
        or payload.get("version_title")
        or payload.get("summary")
        or payload.get("title")
    )
    if not meaningful:
        raise LessonValidationError("Không có thay đổi để gửi xét duyệt.")

    record = record or working_changeset(actor, course, sess)
    for staged_lesson in staged:
        if staged_lesson.change_request_id != record.id:
            staged_lesson.change_request_id = record.id
    for a in staged_assessments:
        if a.change_request_id != record.id:
            a.change_request_id = record.id

    proposed = payload_for(record)
    title = str(
        payload.get("version_title") or payload.get("title") or "Đợt cập nhật khóa học"
    ).strip()
    if not title or len(title) > 200:
        raise LessonValidationError("Tên đợt cập nhật phải từ 1 đến 200 ký tự.")
    proposed["version_title"] = title
    proposed["summary"] = str(payload.get("summary") or "").strip()
    from pwd301.models.assessment import Assessment
    from pwd301.models.question_bank import Question
    from pwd301.services.course_assessment_workflow import assessment_snapshot
    from pwd301.services.course_question_workflow import question_snapshot

    proposed["submitted_snapshot"] = {
        "lessons": [_submitted_lesson_snapshot(item) for item in staged],
        "assessments": {
            str(item.public_id): assessment_snapshot(item)
            for item in sess.query(Assessment)
            .filter(Assessment.course_id == course.id, Assessment.change_request_id == record.id)
            .all()
        },
        "questions": {
            str(item.public_id): question_snapshot(item)
            for item in sess.query(Question)
            .filter(Question.course_id == course.id, Question.change_request_id == record.id)
            .all()
        },
        "new_file_assets": list(proposed.get("new_file_assets") or []),
        "course_metadata": dict(proposed.get("course_metadata") or {}),
        "prerequisites": dict(proposed.get("prerequisites") or {}),
        "completion_rules": dict(proposed.get("completion_rules") or {}),
    }
    proposed["modified_lessons"] = [
        dict(_submitted_lesson_snapshot(item), target_id=item.previous_lesson_id)
        for item in staged
        if item.previous_lesson_id
    ]
    proposed["added_lessons"] = [
        dict(_submitted_lesson_snapshot(item), temp_id=str(item.public_id))
        for item in staged
        if not item.previous_lesson_id
    ]
    proposed["deleted_lessons"] = [
        operation["lesson_id"]
        for operation in (proposed.get("operations") or {}).values()
        if operation.get("action") == "DELETE_LESSON"
    ]
    proposed["changeset_stats"] = {
        "modified_lessons_count": len(proposed["modified_lessons"]),
        "added_lessons_count": len(proposed["added_lessons"]),
        "deleted_lessons_count": len(proposed["deleted_lessons"]),
        "metadata_changes_count": len(proposed.get("course_metadata") or {}),
        "operations_count": len(proposed.get("operations") or {}),
    }
    from pwd301.models.course import CourseCompletionRule, CoursePrerequisite

    rule = sess.query(CourseCompletionRule).filter_by(course_id=course.id).first()
    proposed["baseline_snapshot"] = {
        "course_metadata": {
            key: getattr(course, key)
            for key in (
                "title",
                "description",
                "category",
                "learning_objectives",
                "target_audience",
                "completion_requirements",
                "difficulty",
                "capacity",
                "thumbnail_file_asset_id",
            )
        },
        "lessons": [
            _submitted_lesson_snapshot(item)
            for item in sess.query(Lesson)
            .filter(
                Lesson.course_id == course.id,
                Lesson.deleted_at.is_(None),
                Lesson.change_request_id.is_(None),
                Lesson.status.notin_(("TRASH", "HISTORICAL")),
            )
            .order_by(Lesson.position)
            .all()
        ],
        "completion_rules": {
            "minimum_progress_percent": float(rule.minimum_progress_percent)
            if rule and rule.minimum_progress_percent is not None
            else None,
            "require_all_required_lessons": bool(rule.require_all_required_lessons)
            if rule
            else True,
            "require_required_assessments": bool(rule.require_required_assessments)
            if rule
            else True,
        },
        "prerequisites": [
            str(link.prerequisite_course.public_id)
            for link in sess.query(CoursePrerequisite).filter_by(course_id=course.id).all()
        ],
    }
    from pwd301.services.course_workflow_service import (
        course_asset_manifest,
        course_review_version,
        validate_submitted_assets,
    )

    proposed["asset_manifest"] = course_asset_manifest(course, sess, proposed, lock=True)
    validate_submitted_assets(course, proposed["asset_manifest"], sess)
    proposed["baseline_version"] = course_review_version(course, sess)
    for lesson in staged:
        lesson.status = "PENDING_APPROVAL"
        lesson.change_request_id = record.id
    record.status = "PENDING"
    record.created_at = utc_now()
    write_payload(record, proposed, sess)
    _record_lesson_audit_event(
        sess=sess,
        actor=actor,
        action="COURSE_CHANGE_SUBMITTED",
        target_id=course.id,
        reason=title,
        after_json=json.dumps({"change_request_id": record.id}),
    )
    from pwd301.models.identity import Role, UserRole
    from pwd301.services.notification_service import dispatch_notification

    admin_role = sess.query(Role).filter_by(code="ADMIN").first()
    admin_users = (
        sess.query(User)
        .join(UserRole, UserRole.user_id == User.id)
        .filter(
            UserRole.role_id == admin_role.id,
            User.status == "ACTIVE",
            User.suspended_at.is_(None),
        )
        .all()
        if admin_role
        else []
    )
    for adm in admin_users:
        if adm.is_primary_admin or adm.has_admin_permission("COURSE_REVIEW"):
            key = uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"pwd301:course-change:{record.id}:COURSE_CHANGE_REQUESTED:{adm.id}",
            )
            with contextlib.suppress(Exception):
                dispatch_notification(
                    recipient_user=adm,
                    event_type="COURSE_CHANGE_REQUESTED",
                    title=f"Đợt cập nhật khóa học {course.course_code} chờ xét duyệt",
                    body=f"Giảng viên {actor.display_name} đã nộp đợt cập nhật mới cho khóa học '{course.title}'.",
                    action_url="#/admin/governance?tab=change-requests",
                    category="COURSE",
                    target_role="ADMIN",
                    payload={"course_id": str(course.public_id), "change_request_id": record.id},
                    event_key=key,
                    session=sess,
                )
    if session is None:
        sess.commit()
    return record


def get_course_changeset_status(actor, course_id, session=None):
    sess = session if session is not None else db.session
    course = require_course_manager(actor, course_id, session=sess)
    record = active_changeset(course.id, sess)
    proposed = payload_for(record) if record else {}
    lessons = (
        sess.query(Lesson)
        .filter(
            Lesson.course_id == course.id,
            sa.or_(
                Lesson.change_request_id == record.id if record else sa.false(),
                Lesson.change_request_id.is_(None),
            ),
            Lesson.deleted_at.is_(None),
            Lesson.status.in_(("DRAFT", "PENDING_APPROVAL")),
        )
        .all()
        if course_requires_review(course)
        else []
    )
    added = sum(not item.previous_lesson_id for item in lessons)
    modified = len(lessons) - added
    deleted = len(proposed.get("deleted_lessons") or [])
    from pwd301.models.assessment import Assessment

    staged_asm = (
        sess.query(Assessment)
        .filter(
            Assessment.course_id == course.id,
            sa.or_(
                Assessment.change_request_id == record.id if record else sa.false(),
                Assessment.status == "DRAFT",
            ),
            Assessment.deleted_at.is_(None),
        )
        .count()
        if course_requires_review(course)
        else 0
    )
    reorder = 1 if proposed.get("reorder_plan", {}).get("lessons_order") else 0
    metadata = len(proposed.get("course_metadata") or {})
    operations = len(proposed.get("operations") or {})
    count = (
        len(lessons)
        + staged_asm
        + deleted
        + metadata
        + operations
        + reorder
        + len(proposed.get("new_file_assets") or [])
        + bool(proposed.get("completion_rules"))
        + sum(len(value) for value in (proposed.get("prerequisites") or {}).values())
    )
    if record and record.status in ("PENDING", "REJECTED"):
        current_status = record.status
    elif count > 0:
        current_status = "DRAFT"
    else:
        current_status = "NONE"

    from pwd301.services.course_workflow_service import review_version

    has_changes = bool(count > 0)
    return {
        "status": current_status,
        "has_changes": has_changes,
        "change_request_id": record.id if record else None,
        "request_id": record.id if record else None,
        "review_version": review_version(record) if record else None,
        "version_title": proposed.get("version_title"),
        "summary": proposed.get("summary", ""),
        "changes_count": count,
        "staged_lessons": len(lessons),
        "deleted_staged": deleted,
        "has_metadata_changes": bool(metadata),
        "metadata_count": metadata,
        "draft_count": added,
        "added_count": added,
        "modified_count": modified,
        "deleted_count": deleted,
        "operations_count": operations,
        "new_file_assets_count": len(proposed.get("new_file_assets") or []),
        "created_at": record.created_at.isoformat() if record else None,
        "submitted_at": record.created_at.isoformat()
        if record and record.status == "PENDING"
        else None,
        "review_reason": record.review_reason if record else None,
    }


def retract_course_changeset(actor, course_id, session=None, expected_identity=None):
    sess = session if session is not None else db.session
    course = require_course_manager(actor, course_id, session=sess)
    record = active_changeset(course.id, sess)
    if record is None or record.status != "PENDING":
        raise ConflictError("Không có đợt cập nhật đang chờ duyệt để rút lại.")
    record = lock_course_change_request(sess, record.id)
    if expected_identity and (
        "review_version" in expected_identity
        or "request_id" in expected_identity
        or "change_request_id" in expected_identity
    ):
        from pwd301.services.course_workflow_service import require_review_identity

        require_review_identity(record, expected_identity)
    if record.status != "PENDING":
        raise ConflictError("Trạng thái xét duyệt đã thay đổi; hãy tải lại.")
    record.status = "CANCELLED"
    record.review_reason = "Giảng viên rút lại để tiếp tục chỉnh sửa."
    record.reviewed_at = utc_now()
    sess.flush()
    successor_draft(actor, record, sess)
    _record_lesson_audit_event(
        sess=sess,
        actor=actor,
        action="COURSE_CHANGE_WITHDRAWN",
        target_id=course.id,
        reason=record.review_reason,
        after_json=json.dumps({"change_request_id": record.id}),
    )
    if session is None:
        sess.commit()
    return record


def discard_course_changeset(actor, course_id, session=None):
    sess = session if session is not None else db.session
    course = require_course_manager(actor, course_id, session=sess)
    record = active_changeset(course.id, sess)
    if record is None:
        return {"status": "DISCARDED", "message": "Không có bản nháp cần hủy."}
    if record.status not in ("DRAFT", "PENDING"):
        raise ConflictError("Không có đợt xét duyệt hoặc bản nháp nào đang hoạt động.")
    for lesson in (
        sess.query(Lesson)
        .filter(Lesson.course_id == course.id, Lesson.change_request_id == record.id)
        .all()
    ):
        for resource in list(lesson.resources):
            sess.delete(resource)
        if not lesson.previous_lesson_id:
            sess.delete(lesson)
        else:
            lesson.deleted_at = utc_now()
            lesson.status = "TRASH"
    for unit in sess.query(LearningUnit).filter(LearningUnit.change_request_id == record.id).all():
        unit.deleted_at = utc_now()
    from pwd301.models.assessment import Assessment

    for assessment in (
        sess.query(Assessment).filter(Assessment.change_request_id == record.id).all()
    ):
        assessment.deleted_at = utc_now()
        assessment.status = "TRASH"
    from pwd301.models.question_bank import Question

    for question in sess.query(Question).filter(Question.change_request_id == record.id).all():
        question.deleted_at = utc_now()
        question.status = "TRASH"
    record.status = "CANCELLED"
    record.review_reason = "Giảng viên hủy bản nháp."
    record.reviewed_at = utc_now()
    _record_lesson_audit_event(
        sess=sess,
        actor=actor,
        action="COURSE_CHANGE_DISCARDED",
        target_id=course.id,
        reason=record.review_reason,
    )
    sess.flush()
    if session is None:
        sess.commit()
    return {"status": "DISCARDED", "message": "Đã hủy bản nháp; nội dung đã duyệt được bảo toàn."}


def get_course_changeset_diff(
    actor: User,
    change_request_id_or_course_id: int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Calculate and return full Before vs. After diff of a course version changeset."""
    sess = session if session is not None else db.session
    if actor is None or not actor.is_active:
        raise ForbiddenError("Authentication required.")

    req = None
    course = None
    if (
        isinstance(change_request_id_or_course_id, int)
        or str(change_request_id_or_course_id).isdigit()
    ):
        req = sess.get(CourseChangeRequest, int(change_request_id_or_course_id))
        if req:
            course = sess.get(Course, req.course_id)

    if req is None:
        course = _resolve_course(change_request_id_or_course_id, session=sess)
        if course:
            req = (
                sess.query(CourseChangeRequest)
                .filter(
                    CourseChangeRequest.course_id == course.id,
                    CourseChangeRequest.target_type == "COURSE",
                    CourseChangeRequest.status.in_(["DRAFT", "PENDING", "REJECTED"]),
                    sa.or_(
                        CourseChangeRequest.change_type == "COURSE_VERSION_CHANGESET",
                        CourseChangeRequest.proposed_payload_json.like(
                            '%"action": "COURSE_VERSION_CHANGESET"%'
                        ),
                    ),
                )
                .order_by(CourseChangeRequest.id.desc())
                .first()
            )

    if course is None:
        raise ResourceNotFoundError("Khóa học hoặc yêu cầu thay đổi không tồn tại.")

    if not actor.is_admin and course.owner_instructor_id != actor.id:
        raise ForbiddenError("You are not authorized to view changeset diff for this course.")

    p_data = {}
    if req is not None:
        try:
            p_data = json.loads(req.proposed_payload_json or "{}")
        except Exception:
            p_data = {}
        if req.status == "DRAFT" and req.change_type == "COURSE_VERSION_CHANGESET":
            drafts = (
                sess.query(Lesson)
                .filter(
                    Lesson.course_id == course.id,
                    Lesson.change_request_id == req.id,
                    Lesson.deleted_at.is_(None),
                    Lesson.status == "DRAFT",
                )
                .all()
            )
            p_data["added_lessons"] = [
                dict(_submitted_lesson_snapshot(item), temp_id=str(item.public_id))
                for item in drafts
                if not item.previous_lesson_id
            ]
            p_data["modified_lessons"] = [
                dict(_submitted_lesson_snapshot(item), target_id=item.previous_lesson_id)
                for item in drafts
                if item.previous_lesson_id
            ]
    else:
        # Build diff dynamically from staged draft entities
        staged_lessons = (
            sess.query(Lesson)
            .filter(
                Lesson.course_id == course.id,
                Lesson.status.in_(["DRAFT", "PENDING_APPROVAL"]),
                Lesson.deleted_at.is_(None),
            )
            .all()
        )
        deleted_staged = (
            sess.query(Lesson)
            .filter(
                Lesson.course_id == course.id,
                Lesson.material_change_summary == "[STAGED_DELETE]",
                Lesson.deleted_at.is_(None),
            )
            .all()
        )
        modified_drafts = [les for les in staged_lessons if les.previous_lesson_id is not None]
        added_drafts = [les for les in staged_lessons if les.previous_lesson_id is None]

        if not (modified_drafts or added_drafts or deleted_staged):
            raise ResourceNotFoundError("Chưa có thay đổi nào trong bản nháp giáo trình.")

        added_lessons_list = [
            {
                "temp_id": str(d.public_id),
                "title": d.title,
                "position": d.position,
                "learning_unit_id": str(d.learning_unit.public_id) if d.learning_unit else None,
                "summary": d.summary,
                "markdown_content": d.markdown_content,
            }
            for d in added_drafts
        ]
        modified_lessons_list = []
        for d in modified_drafts:
            orig = sess.get(Lesson, d.previous_lesson_id)
            field_changes = []
            old_title = orig.title if orig else ""
            old_summary = orig.summary if orig else ""
            if orig and orig.title != d.title:
                field_changes.append(
                    {
                        "field": "title",
                        "label": "Tiêu đề bài học",
                        "old_value": orig.title,
                        "new_value": d.title,
                    }
                )
            if orig and (orig.summary or "") != (d.summary or ""):
                field_changes.append(
                    {
                        "field": "summary",
                        "label": "Tóm tắt bài học",
                        "old_value": orig.summary or "(Trống)",
                        "new_value": d.summary or "(Trống)",
                    }
                )
            orig_content = (orig.markdown_content or "") if orig else ""
            new_content = d.markdown_content or ""
            if orig and orig_content != new_content:
                field_changes.append(
                    {
                        "field": "content",
                        "label": "Nội dung bài học",
                        "old_value": f"{len(orig_content)} ký tự",
                        "new_value": f"{len(new_content)} ký tự",
                    }
                )

            def _quiz_count(c):
                m = re.search(r"<!--\s*mini_quiz:\s*(.+?)\s*-->", c or "", re.DOTALL)
                if m:
                    try:
                        return len(json.loads(m.group(1)))
                    except Exception:
                        return 0
                return 0

            old_qc = _quiz_count(orig_content)
            new_qc = _quiz_count(new_content)
            if old_qc != new_qc:
                field_changes.append(
                    {
                        "field": "quiz",
                        "label": "Câu hỏi ôn tập",
                        "old_value": f"{old_qc} câu",
                        "new_value": f"{new_qc} câu",
                    }
                )
            if not field_changes:
                field_changes.append(
                    {
                        "field": "general",
                        "label": "Cập nhật bài học",
                        "old_value": "Bản gốc",
                        "new_value": "Bản nháp đã lưu",
                    }
                )

            modified_lessons_list.append(
                {
                    "lesson_id": str(orig.public_id) if orig else str(d.public_id),
                    "title": d.title,
                    "old_title": old_title,
                    "summary": d.summary,
                    "old_summary": old_summary,
                    "markdown_content": d.markdown_content,
                    "field_changes": field_changes,
                    "unit_title": d.learning_unit.title if d.learning_unit else None,
                }
            )
        deleted_lessons_list = [
            {
                "lesson_id": str(d.public_id),
                "title": d.title,
            }
            for d in deleted_staged
        ]
        p_data = {
            "version_title": "Bản nháp cập nhật",
            "summary": f"Có {len(added_lessons_list) + len(modified_lessons_list) + len(deleted_lessons_list)} thay đổi đang chờ gửi duyệt.",
            "added_lessons": added_lessons_list,
            "modified_lessons": modified_lessons_list,
            "deleted_lessons": deleted_lessons_list,
            "reorder_plan": {"lessons_order": []},
            "changeset_stats": {
                "reordered_lessons_count": 0,
                "added_lessons_count": len(added_lessons_list),
                "modified_lessons_count": len(modified_lessons_list),
                "deleted_lessons_count": len(deleted_lessons_list),
            },
        }

    live_lessons = (
        sess.query(Lesson)
        .filter(
            Lesson.course_id == course.id,
            Lesson.deleted_at.is_(None),
            Lesson.status.in_(("ACTIVE", "PUBLISHED", "HIDDEN")),
        )
        .order_by(Lesson.position.asc())
        .all()
    )
    live_curriculum = [
        {
            "lesson_id": str(les.public_id),
            "internal_id": les.id,
            "title": les.title,
            "position": les.position,
            "status": les.status,
            "learning_unit_id": str(les.learning_unit.public_id) if les.learning_unit else None,
            "learning_unit_title": les.learning_unit.title if les.learning_unit else None,
            "summary": les.summary,
            "estimated_duration_minutes": les.estimated_duration_minutes,
        }
        for les in live_lessons
    ]
    if p_data.get("baseline_snapshot", {}).get("lessons") is not None:
        live_curriculum = p_data["baseline_snapshot"]["lessons"]

    reorder_plan = p_data.get("reorder_plan") or {}
    lessons_order = reorder_plan.get("lessons_order") or []
    added_lessons = p_data.get("added_lessons") or []
    modified_lessons = p_data.get("modified_lessons") or []
    deleted_lessons = p_data.get("deleted_lessons") or []

    for m_item in modified_lessons:
        if isinstance(m_item, dict) and not m_item.get("field_changes"):
            target_id = m_item.get("target_id")
            orig = None
            if target_id:
                orig = sess.get(Lesson, target_id)
            elif m_item.get("lesson_id"):
                try:
                    pub_id = uuid.UUID(str(m_item["lesson_id"]))
                    les_found = sess.query(Lesson).filter(Lesson.public_id == pub_id).first()
                    if les_found and les_found.previous_lesson_id:
                        orig = sess.get(Lesson, les_found.previous_lesson_id)
                    else:
                        orig = les_found
                except Exception:
                    pass

            fc_list = []
            new_title = (m_item.get("title") or "").strip()
            orig_title = (orig.title or "").strip() if orig else ""
            if orig and orig_title != new_title:
                fc_list.append(
                    {
                        "field": "title",
                        "label": "Tiêu đề bài học",
                        "old_value": orig_title,
                        "new_value": new_title,
                    }
                )
            new_summary = (m_item.get("summary") or "").strip()
            orig_summary = (orig.summary or "").strip() if orig else ""
            if orig and orig_summary != new_summary:
                fc_list.append(
                    {
                        "field": "summary",
                        "label": "Tóm tắt bài học",
                        "old_value": orig_summary or "(Trống)",
                        "new_value": new_summary or "(Trống)",
                    }
                )
            orig_content = (orig.markdown_content or "").strip() if orig else ""
            new_content = (m_item.get("markdown_content") or "").strip()
            if orig and orig_content != new_content:
                fc_list.append(
                    {
                        "field": "content",
                        "label": "Nội dung bài học",
                        "old_value": f"{len(orig_content)} ký tự",
                        "new_value": f"{len(new_content)} ký tự",
                    }
                )

            def _quiz_count(c):
                m = re.search(r"<!--\s*mini_quiz:\s*(.+?)\s*-->", c or "", re.DOTALL)
                if m:
                    try:
                        return len(json.loads(m.group(1)))
                    except Exception:
                        return 0
                return 0

            old_qc = _quiz_count(orig_content)
            new_qc = _quiz_count(new_content)
            if old_qc != new_qc:
                fc_list.append(
                    {
                        "field": "quiz",
                        "label": "Câu hỏi ôn tập",
                        "old_value": f"{old_qc} câu",
                        "new_value": f"{new_qc} câu",
                    }
                )
            if not fc_list:
                fc_list.append(
                    {
                        "field": "general",
                        "label": "Cập nhật bài học",
                        "old_value": "Bản gốc",
                        "new_value": "Bản nháp đã lưu",
                    }
                )
            m_item["field_changes"] = fc_list
            if orig:
                m_item["old_title"] = orig.title
                m_item["old_summary"] = orig.summary

    stats = p_data.get("changeset_stats") or {
        "reordered_lessons_count": len(lessons_order),
        "added_lessons_count": len(added_lessons),
        "modified_lessons_count": len(modified_lessons),
        "deleted_lessons_count": len(deleted_lessons),
    }

    pos_map = {
        (entry.get("lesson_id") if isinstance(entry, dict) else entry): entry.get("position")
        for entry in lessons_order
        if isinstance(entry, dict)
    }
    mod_map = {
        (item.get("lesson_id") or item.get("id")): item
        for item in modified_lessons
        if isinstance(item, dict)
    }
    del_set = {
        (item.get("lesson_id") if isinstance(item, dict) else item) for item in deleted_lessons
    }
    for op_val in (p_data.get("operations") or {}).values():
        if isinstance(op_val, dict) and op_val.get("action") == "DELETE_LESSON":
            lid = op_val.get("lesson_id")
            if lid:
                del_set.add(str(lid))
                if not any(str(item.get("lesson_id") if isinstance(item, dict) else item) == str(lid) for item in deleted_lessons):
                    les_found = None
                    try:
                        les_found = sess.query(Lesson).filter(Lesson.public_id == uuid.UUID(str(lid))).first()
                    except Exception:
                        pass
                    deleted_lessons.append(
                        {
                            "lesson_id": str(lid),
                            "title": les_found.title if les_found else "Bài giảng",
                        }
                    )

    proposed_curriculum = []
    for les in live_lessons:
        lid_str = str(les.public_id)
        if lid_str in del_set or les.id in del_set:
            continue
        mod_item = mod_map.get(lid_str) or mod_map.get(les.id) or {}
        new_pos = pos_map.get(lid_str) or pos_map.get(les.id) or les.position
        is_reordered = new_pos != les.position
        is_modified = bool(mod_item)

        proposed_curriculum.append(
            {
                "lesson_id": lid_str,
                "title": mod_item.get("title") or les.title,
                "position": new_pos,
                "status": "MODIFIED"
                if is_modified
                else ("REORDERED" if is_reordered else "UNCHANGED"),
                "old_position": les.position,
                "learning_unit_id": str(les.learning_unit.public_id) if les.learning_unit else None,
                "learning_unit_title": les.learning_unit.title if les.learning_unit else None,
                "summary": mod_item.get("summary") or les.summary,
                "markdown_content": mod_item.get("markdown_content") or les.markdown_content,
            }
        )

    for item in added_lessons:
        proposed_curriculum.append(
            {
                "lesson_id": item.get("temp_id") or f"new-{uuid.uuid4().hex[:6]}",
                "title": item.get("title") or "Bài giảng mới",
                "position": item.get("position") or (len(proposed_curriculum) + 1),
                "status": "ADDED",
                "learning_unit_id": item.get("learning_unit_id"),
                "summary": item.get("summary"),
                "markdown_content": item.get("markdown_content"),
            }
        )

    proposed_curriculum.sort(key=lambda x: x.get("position", 0))

    # Build Deep 5-Category Changeset Diff
    curriculum_structure = []
    content_blocks = []
    interactive_quizzes = []

    def _parse_quiz_list(md: str) -> list[dict[str, Any]]:
        m = re.search(r"<!--\s*mini_quiz:\s*(.+?)\s*-->", md or "", re.DOTALL)
        if m:
            try:
                parsed = json.loads(m.group(1))
                return parsed if isinstance(parsed, list) else []
            except Exception:
                return []
        return []

    # 0. Structure: Learning Unit operations (Chapters)
    for op_val in (p_data.get("operations") or {}).values():
        if not isinstance(op_val, dict):
            continue
        act = op_val.get("action")
        if act == "DELETE_LEARNING_UNIT":
            uid = op_val.get("unit_id")
            unit_title = op_val.get("title") or "Chương học"
            if uid and not op_val.get("title"):
                try:
                    u_obj = sess.query(LearningUnit).filter(LearningUnit.public_id == uuid.UUID(str(uid))).first()
                    if u_obj:
                        unit_title = u_obj.title
                except Exception:
                    pass
            curriculum_structure.append(
                {
                    "change_type": "REMOVED",
                    "title": f"Chương: {unit_title}",
                    "description": f"Xóa toàn bộ chương '{unit_title}'",
                }
            )
        elif act == "CREATE_LEARNING_UNIT":
            u_title = op_val.get("title") or "Chương mới"
            curriculum_structure.append(
                {
                    "change_type": "ADDED",
                    "title": f"Chương: {u_title}",
                    "description": f"Thêm chương mục mới: {u_title}",
                }
            )
        elif act == "UPDATE_LEARNING_UNIT":
            u_title = op_val.get("title") or "Chương mục"
            curriculum_structure.append(
                {
                    "change_type": "MODIFIED",
                    "title": f"Chương: {u_title}",
                    "description": f"Đổi tên chương mục thành '{u_title}'",
                }
            )

    # 1. Structure: Added lessons
    for item in added_lessons:
        curriculum_structure.append(
            {
                "change_type": "ADDED",
                "title": item.get("title") or "Bài giảng mới",
                "lesson_id": item.get("temp_id") or "",
                "learning_unit_id": item.get("learning_unit_id"),
                "position": item.get("position"),
                "description": f"Thêm bài giảng mới: {item.get('title', 'Bài giảng mới')}",
            }
        )

    # 2. Structure: Deleted lessons
    for item in deleted_lessons:
        curriculum_structure.append(
            {
                "change_type": "REMOVED",
                "title": item.get("title") or "Bài giảng",
                "lesson_id": str(item.get("lesson_id") or ""),
                "description": f"Xóa bài giảng: {item.get('title', 'Bài giảng')}",
            }
        )

    # 3. Structure, Content & Quizzes from Modified lessons
    for m_item in modified_lessons:
        orig = None
        target_id = m_item.get("target_id")
        if target_id:
            orig = sess.get(Lesson, target_id)
        elif m_item.get("lesson_id"):
            try:
                pub_id = uuid.UUID(str(m_item["lesson_id"]))
                les_found = sess.query(Lesson).filter(Lesson.public_id == pub_id).first()
                if les_found and les_found.previous_lesson_id:
                    orig = sess.get(Lesson, les_found.previous_lesson_id)
                else:
                    orig = les_found
            except Exception:
                pass

        title = m_item.get("title") or (orig.title if orig else "Bài giảng")
        lid = str(orig.public_id) if orig else str(m_item.get("lesson_id") or "")

        if orig:
            orig_unit_title = orig.learning_unit.title if orig.learning_unit else "Chưa gán"
            new_unit_id = m_item.get("learning_unit_id")
            new_unit_title = m_item.get("unit_title")
            if (
                new_unit_id
                and str(new_unit_id) != str(orig.learning_unit_id)
                and str(new_unit_id)
                != (str(orig.learning_unit.public_id) if orig.learning_unit else "")
            ):
                curriculum_structure.append(
                    {
                        "change_type": "MOVED",
                        "title": title,
                        "lesson_id": lid,
                        "old_unit_title": orig_unit_title,
                        "new_unit_title": new_unit_title or "Chương mới",
                        "description": f"Chuyển từ '{orig_unit_title}' sang '{new_unit_title or 'Chương mới'}'",
                    }
                )
            old_pos = orig.position
            new_pos = m_item.get("position")
            if new_pos and new_pos != old_pos:
                curriculum_structure.append(
                    {
                        "change_type": "REORDERED",
                        "title": title,
                        "lesson_id": lid,
                        "old_position": old_pos,
                        "new_position": new_pos,
                        "description": f"Đổi thứ tự từ #{old_pos} sang #{new_pos}",
                    }
                )
            if (m_item.get("title") or "").strip() != (orig.title or "").strip():
                curriculum_structure.append(
                    {
                        "change_type": "MODIFIED",
                        "title": title,
                        "old_title": orig.title,
                        "lesson_id": lid,
                        "description": f"Đổi tiêu đề từ '{orig.title}' thành '{title}'",
                    }
                )

            orig_content = (orig.markdown_content or "").strip()
            new_content = (m_item.get("markdown_content") or "").strip()
            if orig_content != new_content:
                content_blocks.append(
                    {
                        "change_type": "MODIFIED",
                        "lesson_title": title,
                        "lesson_id": lid,
                        "field": "content",
                        "old_length": len(orig_content),
                        "new_length": len(new_content),
                        "description": f"Cập nhật nội dung văn bản ({len(orig_content)} -> {len(new_content)} ký tự)",
                    }
                )
            orig_sum = (orig.summary or "").strip()
            new_sum = (m_item.get("summary") or "").strip()
            if orig_sum != new_sum:
                content_blocks.append(
                    {
                        "change_type": "MODIFIED",
                        "lesson_title": title,
                        "lesson_id": lid,
                        "field": "summary",
                        "old_summary": orig_sum or "(Trống)",
                        "new_summary": new_sum or "(Trống)",
                        "description": "Cập nhật tóm tắt bài giảng",
                    }
                )

            old_qs = _parse_quiz_list(orig.markdown_content)
            new_qs = _parse_quiz_list(m_item.get("markdown_content") or "")

            for nq in new_qs:
                q_text = nq.get("question") or nq.get("prompt") or ""
                matched = next(
                    (oq for oq in old_qs if (oq.get("question") or oq.get("prompt")) == q_text),
                    None,
                )
                if matched is None:
                    interactive_quizzes.append(
                        {
                            "change_type": "ADDED",
                            "lesson_title": title,
                            "lesson_id": lid,
                            "question": q_text,
                            "type": nq.get("type") or nq.get("q_type") or "MULTIPLE_CHOICE",
                            "description": f"Thêm câu hỏi ({nq.get('type') or 'Trắc nghiệm'}): {q_text[:70]}",
                        }
                    )
                elif matched != nq:
                    interactive_quizzes.append(
                        {
                            "change_type": "MODIFIED",
                            "lesson_title": title,
                            "lesson_id": lid,
                            "question": q_text,
                            "type": nq.get("type") or nq.get("q_type") or "MULTIPLE_CHOICE",
                            "description": f"Chỉnh sửa câu hỏi ({nq.get('type') or 'Trắc nghiệm'}): {q_text[:70]}",
                        }
                    )

            for oq in old_qs:
                q_text = oq.get("question") or oq.get("prompt") or ""
                if not any((nq.get("question") or nq.get("prompt")) == q_text for nq in new_qs):
                    interactive_quizzes.append(
                        {
                            "change_type": "REMOVED",
                            "lesson_title": title,
                            "lesson_id": lid,
                            "question": q_text,
                            "type": oq.get("type") or oq.get("q_type") or "MULTIPLE_CHOICE",
                            "description": f"Xóa câu hỏi: {q_text[:70]}",
                        }
                    )
        else:
            curriculum_structure.append(
                {
                    "change_type": "MODIFIED",
                    "title": title,
                    "lesson_id": lid,
                    "description": f"Cập nhật bài giảng '{title}'",
                }
            )

    # If no specific structural changes were appended for modified lessons, record modification
    if not curriculum_structure and modified_lessons:
        for m_item in modified_lessons:
            curriculum_structure.append(
                {
                    "change_type": "MODIFIED",
                    "title": m_item.get("title") or "Bài giảng",
                    "lesson_id": str(m_item.get("lesson_id") or ""),
                    "description": f"Cập nhật bài giảng '{m_item.get('title', 'Bài giảng')}'",
                }
            )

    # Reviewer assessments come from the sealed submission; editable drafts use current authored rows.
    from pwd301.models.assessment import Assessment
    from pwd301.models.course import CourseCompletionRule
    from pwd301.services.course_assessment_workflow import assessment_snapshot
    from pwd301.services.course_workflow_service import cover_review_fields, review_version

    sealed_assessments = p_data.get("submitted_snapshot", {}).get("assessments")
    if sealed_assessments is None:
        sealed_assessments = (
            {
                str(item.public_id): assessment_snapshot(item)
                for item in sess.query(Assessment)
                .filter(
                    Assessment.course_id == course.id,
                    Assessment.change_request_id == (req.id if req else None),
                    Assessment.deleted_at.is_(None),
                )
                .all()
            }
            if req
            else {}
        )
    assessments_list = []
    for public_id, snapshot in sealed_assessments.items():
        fields = snapshot["fields"]
        assessments_list.append(
            {
                "assessment_id": public_id,
                "title": fields["title"],
                "assessment_type": fields["assessment_type"],
                "status": fields["status"],
                "time_limit_minutes": fields["time_limit_minutes"],
                "total_points": sum(float(item["points"]) for item in snapshot["assignments"]),
                "change_type": "MODIFIED" if fields.get("previous_assessment_id") else "ADDED",
                "snapshot": snapshot,
                "description": f"Cập nhật bài khảo thí '{fields['title']}'",
            }
        )
    baseline = p_data.get("baseline_snapshot") or {}
    current_reqs: dict[str, Any] = {}
    raw_reqs = baseline.get("course_metadata", {}).get(
        "completion_requirements", course.completion_requirements
    )
    if raw_reqs:
        try:
            current_reqs = json.loads(raw_reqs) if isinstance(raw_reqs, str) else dict(raw_reqs)
        except (TypeError, ValueError):
            current_reqs = {}
    rule = sess.query(CourseCompletionRule).filter_by(course_id=course.id).first()
    current_reqs.update(
        baseline.get("completion_rules")
        or {
            "minimum_progress_percent": float(rule.minimum_progress_percent)
            if rule and rule.minimum_progress_percent is not None
            else None,
            "require_all_required_lessons": bool(rule.require_all_required_lessons)
            if rule
            else True,
            "require_required_assessments": bool(rule.require_required_assessments)
            if rule
            else True,
        }
    )
    meta_diff = p_data.get("course_metadata") or {}
    covers = cover_review_fields(course, p_data, sess)
    baseline_cover = baseline.get("course_metadata", {}).get(
        "thumbnail_file_asset_id", course.thumbnail_file_asset_id
    )
    if baseline:
        from pwd301.services.course_workflow_service import cover_url

        covers["current_cover_url"] = cover_url(course, baseline_cover, sess)
    # Question bank changes (from submitted snapshot, operations, or draft question rows)
    from pwd301.models.question_bank import Question
    from pwd301.services.course_question_workflow import question_snapshot

    question_changes = []
    sealed_questions = p_data.get("submitted_snapshot", {}).get("questions")
    if sealed_questions is not None:
        for pub_id_str, q_snap in sealed_questions.items():
            ch_type = (
                "MODIFIED"
                if q_snap.get("change_type") == "MODIFIED" or q_snap.get("reason")
                else "ADDED"
            )
            stem = q_snap.get("content") or ""
            q_type = q_snap.get("question_type") or "MULTIPLE_CHOICE"
            question_changes.append(
                {
                    "change_type": ch_type,
                    "question_id": pub_id_str,
                    "question_type": q_type,
                    "content": stem,
                    "explanation": q_snap.get("explanation"),
                    "choices": q_snap.get("choices") or [],
                    "difficulty": q_snap.get("difficulty"),
                    "description": f"{'Chỉnh sửa' if ch_type == 'MODIFIED' else 'Thêm'} câu hỏi ({q_type}): {stem[:70]}",
                }
            )
    else:
        q_ops = [
            op
            for op in (p_data.get("operations") or {}).values()
            if op.get("action") == "QUESTION_REVISION"
        ]
        if q_ops:
            for op in q_ops:
                snap = op.get("snapshot") or {}
                stem = snap.get("content") or ""
                q_type = snap.get("question_type") or "MULTIPLE_CHOICE"
                is_mod = bool(op.get("original_question_id"))
                ch_type = "MODIFIED" if is_mod else "ADDED"
                question_changes.append(
                    {
                        "change_type": ch_type,
                        "question_id": op.get("question_id"),
                        "question_type": q_type,
                        "content": stem,
                        "explanation": snap.get("explanation"),
                        "choices": snap.get("choices") or [],
                        "difficulty": snap.get("difficulty"),
                        "description": f"{'Chỉnh sửa' if ch_type == 'MODIFIED' else 'Thêm'} câu hỏi ({q_type}): {stem[:70]}",
                    }
                )
        else:
            draft_questions = (
                sess.query(Question)
                .filter(
                    Question.course_id == course.id,
                    Question.change_request_id == (req.id if req else None),
                    Question.deleted_at.is_(None),
                )
                .all()
                if req
                else []
            )
            for dq in draft_questions:
                snap = question_snapshot(dq)
                stem = snap.get("content") or ""
                q_type = snap.get("question_type") or "MULTIPLE_CHOICE"
                ch_type = "MODIFIED" if dq.previous_question_id else "ADDED"
                question_changes.append(
                    {
                        "change_type": ch_type,
                        "question_id": str(dq.public_id),
                        "question_type": q_type,
                        "content": stem,
                        "explanation": snap.get("explanation"),
                        "choices": snap.get("choices") or [],
                        "difficulty": snap.get("difficulty"),
                        "description": f"{'Chỉnh sửa' if ch_type == 'MODIFIED' else 'Thêm'} câu hỏi ({q_type}): {stem[:70]}",
                    }
                )

    # Standalone file changes
    from pwd301.models.file_import import FileAsset

    file_changes = []
    raw_files = (
        p_data.get("submitted_snapshot", {}).get("new_file_assets")
        if p_data.get("submitted_snapshot", {}).get("new_file_assets") is not None
        else (p_data.get("new_file_assets") or p_data.get("uploaded_file_assets") or [])
    )
    for f_id in raw_files:
        try:
            f_pub = uuid.UUID(str(f_id))
            fa = sess.query(FileAsset).filter_by(public_id=f_pub).first()
            if fa and fa.deleted_at is None:
                size_bytes = fa.size_bytes if hasattr(fa, "size_bytes") else 0
                size_str = f"{size_bytes} bytes" if size_bytes else "0 bytes"
                file_changes.append(
                    {
                        "change_type": "ADDED",
                        "asset_id": str(fa.public_id),
                        "file_name": fa.file_name,
                        "file_size_bytes": size_bytes,
                        "mime_type": fa.mime_type
                        if hasattr(fa, "mime_type")
                        else "application/octet-stream",
                        "scan_status": fa.virus_scan_status
                        if hasattr(fa, "virus_scan_status")
                        else "CLEAN",
                        "description": f"Thêm tệp tài liệu: {fa.file_name} ({size_str})",
                    }
                )
        except Exception:
            pass

    # Prerequisite changes
    prerequisite_changes = []
    raw_prereq_changes = p_data.get("prerequisites") or {}
    for add_id in raw_prereq_changes.get("add") or []:
        try:
            target_c = _resolve_course(add_id, session=sess)
            if target_c:
                prerequisite_changes.append(
                    {
                        "change_type": "ADDED",
                        "course_id": str(target_c.public_id),
                        "course_code": target_c.course_code,
                        "title": target_c.title,
                        "description": f"Thêm môn tiên quyết: [{target_c.course_code}] {target_c.title}",
                    }
                )
        except Exception:
            pass
    for rem_id in raw_prereq_changes.get("remove") or []:
        try:
            target_c = _resolve_course(rem_id, session=sess)
            if target_c:
                prerequisite_changes.append(
                    {
                        "change_type": "REMOVED",
                        "course_id": str(target_c.public_id),
                        "course_code": target_c.course_code,
                        "title": target_c.title,
                        "description": f"Xóa môn tiên quyết: [{target_c.course_code}] {target_c.title}",
                    }
                )
        except Exception:
            pass

    current_prereqs_list = []
    for cur_id in baseline.get("prerequisites", []):
        try:
            target_c = _resolve_course(cur_id, session=sess)
            if target_c:
                current_prereqs_list.append(
                    {
                        "course_id": str(target_c.public_id),
                        "course_code": target_c.course_code,
                        "title": target_c.title,
                    }
                )
            else:
                current_prereqs_list.append({"course_id": str(cur_id)})
        except Exception:
            current_prereqs_list.append({"course_id": str(cur_id)})

    # Metadata changes
    current_course_metadata = {
        key: baseline.get("course_metadata", {}).get(key, getattr(course, key, None))
        for key in (
            "title",
            "description",
            "category",
            "learning_objectives",
            "target_audience",
            "completion_requirements",
            "difficulty",
            "capacity",
            "thumbnail_file_asset_id",
        )
    }
    metadata_changes = []
    for k, new_v in meta_diff.items():
        old_v = current_course_metadata.get(k)
        if old_v != new_v:
            metadata_changes.append(
                {
                    "field": k,
                    "old_value": old_v,
                    "new_value": new_v,
                    "description": f"Cập nhật {k}: '{old_v}' → '{new_v}'",
                }
            )

    governance_rules = {
        "is_changed": bool(
            meta_diff
            or p_data.get("completion_rules")
            or p_data.get("prerequisites")
            or prerequisite_changes
            or covers.get("proposed_cover_url") != covers.get("current_cover_url")
        ),
        "current": current_reqs,
        "proposed": {**current_reqs, **(p_data.get("completion_rules") or {})},
        "current_prerequisites": current_prereqs_list,
        "proposed_prerequisite_changes": p_data.get("prerequisites") or {},
        "prerequisite_changes": prerequisite_changes,
        "cover_image_url": covers["proposed_cover_url"],
        **covers,
        "course_metadata": meta_diff,
        "current_course_metadata": current_course_metadata,
        "metadata_changes": metadata_changes,
    }
    for operation in (p_data.get("operations") or {}).values():
        if "LEARNING_UNIT" in operation.get("action", ""):
            curriculum_structure.append(
                {
                    "change_type": "ADDED"
                    if operation["action"].startswith("CREATE")
                    else "REMOVED"
                    if operation["action"].startswith("DELETE")
                    else "MODIFIED",
                    "title": operation.get("title") or "Chương bài học",
                    "description": operation["action"],
                    "unit_id": operation.get("unit_id"),
                }
            )
    total_changes_count = (
        len(curriculum_structure)
        + len(content_blocks)
        + len(interactive_quizzes)
        + len(question_changes)
        + len([a for a in assessments_list if a.get("change_type") != "UNCHANGED"])
        + len(file_changes)
        + len(prerequisite_changes)
        + len(metadata_changes)
        + (
            1
            if (
                covers.get("proposed_cover_url") != covers.get("current_cover_url")
                and covers.get("proposed_cover_url") is not None
            )
            else 0
        )
        + (1 if p_data.get("completion_rules") else 0)
    )

    return {
        "change_request_id": req.id if req else None,
        "request_id": req.id if req else None,
        "review_version": review_version(req) if req else None,
        **covers,
        "course_id": course.id,
        "course_public_id": str(course.public_id),
        "course_code": course.course_code,
        "course_title": course.title,
        "requested_by_id": req.requested_by_user_id if req else actor.id,
        "requested_by_name": (req.requested_by.display_name if req.requested_by else "Giảng viên")
        if req
        else (actor.display_name or "Giảng viên"),
        "created_at": req.created_at.isoformat() if req and req.created_at else None,
        "status": req.status if req else "DRAFT",
        "review_reason": req.review_reason if req else None,
        "version_title": p_data.get("version_title"),
        "summary": p_data.get("summary"),
        "changeset_stats": stats,
        "live_curriculum": live_curriculum,
        "proposed_curriculum": proposed_curriculum,
        "curriculum_structure": curriculum_structure,
        "content_blocks": content_blocks,
        "interactive_quizzes": interactive_quizzes,
        "question_changes": question_changes,
        "file_changes": file_changes,
        "prerequisite_changes": prerequisite_changes,
        "assessments": assessments_list,
        "governance_rules": governance_rules,
        "course_metadata": meta_diff,
        "current_course_metadata": current_course_metadata,
        "metadata_changes": metadata_changes,
        "total_changes_count": total_changes_count,
        "diff": {
            "reorder_plan": reorder_plan,
            "added_lessons": added_lessons,
            "modified_lessons": modified_lessons,
            "deleted_lessons": deleted_lessons,
        },
    }


def apply_course_version_changeset(actor, course_id, payload, session=None):
    """Compatibility alias requires the exact sealed request instead of arbitrary patches."""
    sess = session if session is not None else db.session
    course = require_course_manager(actor, course_id, session=sess)
    record = active_changeset(course.id, sess)
    if record is None or record.status != "PENDING":
        raise ConflictError("Không có bản gửi duyệt đã niêm phong để áp dụng.")
    from pwd301.services.course_workflow_service import require_review_identity

    require_review_identity(record, payload)
    return approve_course_change_request(actor, record.id, session=session)
