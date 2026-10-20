"""Course management and lifecycle service for PWD301.

Provides business logic for:
- Course creation and metadata updates with mass-assignment defense.
- Course state machine transitions:
  DRAFT -> SUBMITTED_FOR_REVIEW -> APPROVED -> PUBLISHED -> ARCHIVED -> TRASH.
- Strict authorization and IDOR prevention adhering to TASK-005.
- Ownership reassignment by Administrator with append-only AuditEvent logging.
- Application-level soft-delete and active prerequisite dependency validation.
- Conformance to canonical specs: 03_COURSE_MANAGEMENT.md, 04_COURSE_API.md,
  COURSE_STATE_MACHINE.md, and 05_DATA_DICTIONARY_COURSE.md.
"""

from __future__ import annotations

import datetime
import json
import logging
import uuid
from decimal import Decimal
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Session, scoped_session

from pwd301.extensions import db
from pwd301.models.course import (
    Course,
    CourseChangeRequest,
    CourseCompletionRule,
    CoursePrerequisite,
    Enrollment,
    Lesson,
)
from pwd301.models.identity import Role, User
from pwd301.models.notification_audit import AuditEvent, Notification, NotificationEvent
from pwd301.models.types import normalize_row_version, utc_now
from pwd301.services.authorization_service import (
    _resolve_course,
    _resolve_user,
    can_manage_course,
    can_view_course,
    require_course_manager,
)
from pwd301.services.exceptions import (
    ConflictError,
    CourseAlreadyExistsError,
    CourseDependencyError,
    CourseStateViolationError,
    CourseValidationError,
    ForbiddenError,
    InvalidRoleAssignmentError,
    ResourceNotFoundError,
    UserNotFoundError,
    ValidationError,
)

logger = logging.getLogger(__name__)


def get_course_thumbnail_asset(
    course: Course,
    session: Session | scoped_session[Any] | None = None,
) -> Any | None:
    """Return only a scanned, course-owned image suitable for display."""
    from pwd301.models.file_import import FileAsset

    if course.thumbnail_file_asset_id is None:
        return None
    sess = session if session is not None else db.session
    asset = sess.get(FileAsset, course.thumbnail_file_asset_id)
    if (
        asset is None
        or asset.course_id != course.id
        or asset.asset_type not in {"COURSE_IMAGE", "RESOURCE"}
        or asset.deleted_at is not None
        or asset.virus_scan_status != "CLEAN"
        or not asset.has_passed_malware_scan
        or (asset.mime_type or "").lower().split(";")[0].strip()
        not in {"image/jpeg", "image/jpg", "image/pjpeg", "image/png", "image/webp"}
    ):
        return None
    return asset


# Allowed difficulty values per database check constraint ck_courses_2
VALID_DIFFICULTIES = {"BEGINNER", "INTERMEDIATE", "ADVANCED"}

# Allowed course statuses per database check constraint ck_courses_1
VALID_STATUSES = {
    "DRAFT",
    "SUBMITTED_FOR_REVIEW",
    "APPROVED",
    "PUBLISHED",
    "ARCHIVED",
    "TRASH",
}

# State machine allowed transitions
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "DRAFT": {"SUBMITTED_FOR_REVIEW", "TRASH"},
    "SUBMITTED_FOR_REVIEW": {"APPROVED", "DRAFT"},
    "APPROVED": {"PUBLISHED", "DRAFT"},
    "PUBLISHED": {"ARCHIVED", "SUBMITTED_FOR_REVIEW", "TRASH"},
    "ARCHIVED": {"PUBLISHED", "TRASH"},
    "TRASH": {"ARCHIVED", "DRAFT", "PUBLISHED"},
}

# Mass-assignment safe writable metadata fields
UPDATABLE_FIELDS = {
    "title",
    "description",
    "learning_objectives",
    "target_audience",
    "completion_requirements",
    "category",
    "difficulty",
    "capacity",
    "storage_quota_bytes",
    "thumbnail_file_asset_id",
}


def _normalize_json_or_text(val: Any) -> str | None:
    """Normalize input value to JSON string if dict/list, or trimmed string."""
    if val is None:
        return None
    if isinstance(val, (list, dict)):
        return json.dumps(val, ensure_ascii=False)
    if isinstance(val, str):
        return val.strip()
    return str(val)


def _normalize_and_validate_slos(val: Any) -> str | None:
    """Normalize and validate learning objectives (SLOs), checking weight 0-100%."""
    if val is None:
        return None
    raw_list = val
    if isinstance(val, str):
        val_str = val.strip()
        if not val_str:
            return None
        if val_str.startswith("[") and val_str.endswith("]"):
            try:
                raw_list = json.loads(val_str)
            except Exception:
                pass
        else:
            return val_str
    if isinstance(raw_list, list):
        normalized: list[dict[str, Any] | str] = []
        for item in raw_list:
            if isinstance(item, dict):
                title = str(item.get("title") or item.get("name") or "").strip()
                desc = str(item.get("description") or "").strip()
                raw_weight = item.get("weight")
                clean_weight = None
                if raw_weight is not None and str(raw_weight).strip():
                    weight_str = str(raw_weight).replace("%", "").strip()
                    try:
                        w_num = float(weight_str)
                        if w_num < 0 or w_num > 100:
                            raise CourseValidationError(
                                f"Trọng số của chuẩn đầu ra '{title or 'SLO'}' không hợp lệ ({raw_weight}). Trọng số phải nằm trong khoảng từ 0% đến 100%."
                            )
                        clean_weight = f"{int(w_num)}%" if w_num.is_integer() else f"{w_num:.1f}%"
                    except ValueError as err:
                        raise CourseValidationError(
                            f"Trọng số của chuẩn đầu ra '{title or 'SLO'}' phải là số phần trăm hợp lệ (0-100%)."
                        ) from err
                normalized.append({
                    "title": title or "Chuẩn đầu ra môn học",
                    "description": desc,
                    "weight": clean_weight,
                })
            elif isinstance(item, str) and item.strip():
                normalized.append({"title": item.strip(), "description": "", "weight": None})
        return json.dumps(normalized, ensure_ascii=False)
    return _normalize_json_or_text(val)


def _record_audit_event(
    sess: Session | scoped_session[Any],
    actor: User,
    action: str,
    target_id: int,
    reason: str | None = None,
    before_json: str | None = None,
    after_json: str | None = None,
) -> AuditEvent:
    """Helper to record an append-only AuditEvent for course lifecycle actions."""
    actor_roles = ",".join(sorted(actor.role_codes)) if actor.role_codes else "UNKNOWN"
    audit_entry = AuditEvent(
        actor_user_id=actor.id,
        actor_roles_snapshot=actor_roles,
        action=action,
        target_type="COURSE",
        target_id=target_id,
        reason=reason,
        before_json=before_json,
        after_json=after_json,
        performed_as_admin=actor.is_admin,
        created_at=utc_now(),
    )
    sess.add(audit_entry)
    return audit_entry


def _course_notification_event_key(audit_entry: AuditEvent, recipient_user_id: int) -> uuid.UUID:
    """Return a deterministic notification key for one audited course transition and recipient."""
    if audit_entry.id is None:
        raise RuntimeError("Course notification event key requires a persisted audit event.")
    return uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"pwd301:course-audit:{audit_entry.id}:{audit_entry.action}:{recipient_user_id}",
    )


def flag_lesson_content(
    actor: User,
    course: Course,
    lesson: Lesson,
    reason: str,
    content_type: str = "bài học",
    idempotency_key: uuid.UUID | str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Persist a lesson flag, mandatory audit and owner notice atomically."""
    from pwd301.services.audit_service import record_audit_event
    from pwd301.services.notification_service import dispatch_notification, emit_event

    sess = session if session is not None else db.session
    normalized_reason = str(reason).strip()
    if len(normalized_reason) < 5:
        raise ValidationError("Lý do gắn cờ bắt buộc tối thiểu 5 ký tự.")

    normalized_content_type = str(content_type).strip() or "bài học"
    normalized_key: uuid.UUID | None = None
    if idempotency_key is not None:
        try:
            normalized_key = (
                idempotency_key
                if isinstance(idempotency_key, uuid.UUID)
                else uuid.UUID(str(idempotency_key).strip())
            )
        except (AttributeError, ValueError):
            raise ValidationError("X-Idempotency-Key must be a valid UUID.") from None

    notification_payload = {
        "course_id": str(course.public_id),
        "lesson_id": str(lesson.public_id),
        "reason": normalized_reason,
        "content_type": normalized_content_type,
        "action_url": f"#/instructor/courses/manage?id={course.public_id}",
    }

    if normalized_key is not None:
        existing_event = sess.query(NotificationEvent).filter_by(event_key=normalized_key).first()
        if existing_event is not None:
            if (
                existing_event.event_type != "COURSE_CONTENT_FLAGGED"
                or existing_event.actor_user_id != actor.id
                or existing_event.target_type != "LESSON"
                or existing_event.target_id != lesson.id
            ):
                raise ConflictError("X-Idempotency-Key is already used by another operation.")
            try:
                existing_payload = json.loads(existing_event.payload_json or "{}")
            except (TypeError, ValueError):
                existing_payload = None
            if existing_payload != notification_payload:
                raise ConflictError("X-Idempotency-Key was already used with different data.")

            existing_audit = (
                sess.query(AuditEvent)
                .filter_by(
                    actor_user_id=actor.id,
                    action="CONTENT_FLAGGED",
                    target_type="LESSON",
                    target_id=lesson.id,
                    reason=normalized_reason,
                )
                .order_by(AuditEvent.id.desc())
                .first()
            )
            existing_notification = (
                sess.query(Notification)
                .filter_by(
                    notification_event_id=existing_event.id,
                    recipient_user_id=course.owner_instructor_id,
                )
                .first()
                if course.owner_instructor_id
                else None
            )
            return {
                "audit": existing_audit,
                "notification": existing_notification,
                "idempotent_replay": True,
            }

    event = None
    if normalized_key is not None:
        event = emit_event(
            event_type="COURSE_CONTENT_FLAGGED",
            payload=notification_payload,
            actor_user_id=actor.id,
            target_type="LESSON",
            target_id=lesson.id,
            event_key=normalized_key,
            session=sess,
        )

    lesson.material_change_summary = f"[FLAGGED]: {normalized_reason}"[:500]
    audit = record_audit_event(
        actor=actor,
        action="CONTENT_FLAGGED",
        target_type="LESSON",
        target_id=lesson.id,
        reason=normalized_reason,
        performed_as_admin=True,
        after_state={
            "course_id": str(course.public_id),
            "lesson_id": str(lesson.public_id),
            "content_type": normalized_content_type,
            "reason": normalized_reason,
        },
        commit=False,
        session=sess,
    )

    notification = None
    if course.owner_instructor_id:
        notification, _ = dispatch_notification(
            recipient_user=course.owner_instructor_id,
            event_type="COURSE_CONTENT_FLAGGED",
            title=f"Nội dung bị gắn cờ: {lesson.title}",
            body=(
                f"Quản trị viên đã gắn cờ {normalized_content_type} '{lesson.title}' "
                f"trong khóa học '{course.title}'. Lý do: {normalized_reason}"
            ),
            action_url=f"#/instructor/courses/manage?id={course.public_id}",
            category="COURSE",
            payload=notification_payload,
            event=event,
            session=sess,
        )

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return {"audit": audit, "notification": notification, "idempotent_replay": False}


def _check_active_prerequisite_dependencies(
    sess: Session | scoped_session[Any],
    course_id: int,
    course_code: str,
) -> None:
    """Ensure a course is not referenced as a prerequisite by any active course.

    Invariants enforced (COURSE-005, COURSE-006):
    - Course referenced as prerequisite by an active Course cannot be archived or deleted
      until dependency is resolved.
    """
    dependent_courses = (
        sess.query(Course)
        .join(
            CoursePrerequisite,
            CoursePrerequisite.course_id == Course.id,
        )
        .filter(
            CoursePrerequisite.prerequisite_course_id == course_id,
            Course.deleted_at.is_(None),
            Course.status.in_(["DRAFT", "SUBMITTED_FOR_REVIEW", "APPROVED", "PUBLISHED"]),
        )
        .all()
    )

    if dependent_courses:
        dep_codes = ", ".join(c.course_code for c in dependent_courses)
        raise CourseDependencyError(
            f"Cannot archive or trash course '{course_code}': it is required as a prerequisite "
            f"by active course(s): {dep_codes}."
        )


def create_course(
    actor: User,
    data: dict[str, Any],
    session: Session | scoped_session[Any] | None = None,
) -> Course:
    """Create a new course with initial DRAFT status.

    Args:
        actor: The authenticated user initiating the creation (must be INSTRUCTOR or ADMIN).
        data: Dictionary of course creation attributes.
        session: Optional SQLAlchemy session.

    Returns:
        The newly created Course instance.

    Raises:
        ForbiddenError: If the actor is not an INSTRUCTOR or ADMIN.
        CourseValidationError: If required fields are missing or invalid.
        CourseAlreadyExistsError: If course_code or title already exists.
        InvalidRoleAssignmentError: If an assigned owner does not possess INSTRUCTOR role.
    """
    if not actor.is_active or not actor.has_any_role("INSTRUCTOR", "ADMIN"):
        raise ForbiddenError("Only instructors and administrators can create courses.")

    sess = session if session is not None else db.session

    # 1. Validate required fields
    raw_code = data.get("course_code")
    if not raw_code or not isinstance(raw_code, str) or not raw_code.strip():
        raise CourseValidationError("course_code is required and cannot be blank.")
    course_code = raw_code.strip()
    if len(course_code) > 50:
        raise CourseValidationError("course_code cannot exceed 50 characters.")

    raw_title = data.get("title")
    if not raw_title or not isinstance(raw_title, str) or not raw_title.strip():
        raise CourseValidationError("title is required and cannot be blank.")
    title = raw_title.strip()
    if len(title) > 200:
        raise CourseValidationError("title cannot exceed 200 characters.")

    # 2. Validate optional fields
    difficulty = data.get("difficulty")
    if difficulty is not None:
        if not isinstance(difficulty, str) or difficulty.upper() not in VALID_DIFFICULTIES:
            diffs = ", ".join(sorted(VALID_DIFFICULTIES))
            raise CourseValidationError(f"Invalid difficulty '{difficulty}'. Allowed: {diffs}.")
        difficulty = difficulty.upper()

    capacity = data.get("capacity")
    if capacity is not None:
        try:
            capacity = int(capacity)
            if capacity <= 0:
                raise ValueError
        except (ValueError, TypeError):
            raise CourseValidationError("capacity must be a positive integer.") from None

    storage_quota_bytes = data.get("storage_quota_bytes")
    if storage_quota_bytes is not None:
        try:
            storage_quota_bytes = int(storage_quota_bytes)
            if storage_quota_bytes <= 0:
                raise ValueError
        except (ValueError, TypeError):
            raise CourseValidationError("storage_quota_bytes must be a positive integer.") from None

    thumbnail_file_asset_id = data.get("thumbnail_file_asset_id")
    if thumbnail_file_asset_id is not None:
        raise CourseValidationError("Create the course before uploading its cover image.")

    # 3. Check uniqueness constraints (COURSE-001, COURSE-002)
    norm_code = course_code.strip().upper()
    existing_code = (
        sess.query(Course)
        .filter(
            Course.course_code_normalized == norm_code,
            Course.deleted_at.is_(None),
        )
        .first()
    )
    if existing_code is not None:
        raise CourseAlreadyExistsError(f"A course with code '{norm_code}' already exists.")

    norm_title = title.strip().lower()
    existing_title = (
        sess.query(Course)
        .filter(
            Course.title_normalized == norm_title,
            Course.deleted_at.is_(None),
        )
        .first()
    )
    if existing_title is not None:
        raise CourseAlreadyExistsError(f"A course with title '{title}' already exists.")

    # 4. Resolve course owner
    owner_instructor_id: int | None
    if actor.is_admin:
        requested_owner = data.get("owner_instructor_id")
        if requested_owner is not None:
            owner_user = _resolve_user(requested_owner, session=sess)
            if owner_user is None:
                raise UserNotFoundError(f"Owner user '{requested_owner}' not found.")
            if not owner_user.has_role("INSTRUCTOR"):
                raise InvalidRoleAssignmentError(
                    f"User '{owner_user.email}' does not possess the INSTRUCTOR role."
                )
            owner_instructor_id = owner_user.id
        else:
            owner_instructor_id = actor.id
    else:
        owner_instructor_id = actor.id

    now = utc_now()
    course = Course(
        course_code=course_code,
        course_code_normalized=norm_code,
        title=title,
        title_normalized=norm_title,
        description=data.get("description"),
        learning_objectives=_normalize_and_validate_slos(data.get("learning_objectives")),
        target_audience=data.get("target_audience"),
        completion_requirements=_normalize_json_or_text(data.get("completion_requirements")),
        category=data.get("category"),
        difficulty=difficulty,
        capacity=capacity,
        storage_quota_bytes=storage_quota_bytes,
        thumbnail_file_asset_id=thumbnail_file_asset_id,
        owner_instructor_id=owner_instructor_id,
        status="DRAFT",
        created_at=now,
        updated_at=now,
    )
    sess.add(course)
    try:
        sess.flush()
    except sa.exc.IntegrityError as exc:
        raise CourseAlreadyExistsError(
            f"A course with code '{course_code}' or title '{title}' already exists."
        ) from exc

    # Create default course completion rule per 05_DATA_DICTIONARY_COURSE.md
    completion_rule = CourseCompletionRule(
        course_id=course.id,
        require_all_required_lessons=True,
        require_required_assessments=True,
        minimum_progress_percent=Decimal("100.00"),
        updated_at=now,
    )
    sess.add(completion_rule)

    _record_audit_event(
        sess=sess,
        actor=actor,
        action="COURSE_CREATED",
        target_id=course.id,
        reason=data.get("reason"),
        after_json=json.dumps(
            {
                "course_code": course.course_code,
                "title": course.title,
                "status": course.status,
                "owner_instructor_id": course.owner_instructor_id,
            }
        ),
    )

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    from pwd301.services.realtime_service import emit_domain_event

    emit_domain_event(
        "course:created",
        {
            "course_id": str(course.public_id),
            "id": str(course.public_id),
            "course_code": course.course_code,
            "title": course.title,
            "status": course.status,
            "owner_instructor_id": course.owner_instructor_id,
        },
    )

    return course


def update_course(
    actor: User,
    course_id: Course | int | uuid.UUID | str,
    data: dict[str, Any],
    session: Session | scoped_session[Any] | None = None,
    is_approved_review: bool = False,
) -> Course | CourseChangeRequest:
    """Update editable course metadata with strict mass-assignment defense.

    Args:
        actor: Authenticated user (must be current course manager or admin).
        course_id: Course model instance or identifier.
        data: Dictionary of fields to update.
        session: Optional SQLAlchemy session.
        is_approved_review: Whether this update is being applied via approved change request.

    Returns:
        The updated Course instance.

    Raises:
        ResourceNotFoundError: If course does not exist.
        ForbiddenError: If actor lacks management rights (IDOR prevention).
        CourseValidationError: If metadata values are invalid.
        CourseAlreadyExistsError: If new title conflicts with an existing course.
    """
    sess = session if session is not None else db.session
    if is_approved_review:
        course = _resolve_course(course_id, session=sess)
        if course is None:
            raise ResourceNotFoundError("Course not found.")
    else:
        course = require_course_manager(actor, course_id, session=sess)

    if course.deleted_at is not None and not actor.is_admin:
        raise ForbiddenError("Cannot update a soft-deleted course.")

    from pwd301.services.course_workflow_service import ensure_course_authoring, should_stage

    if not is_approved_review:
        course = ensure_course_authoring(actor, course, session=sess)

    if course.status == "SUBMITTED_FOR_REVIEW" and not actor.is_admin and not is_approved_review:
        msg = (
            "Khóa học đang trong quá trình xét duyệt của Quản trị viên. "
            "Hãy rút lại yêu cầu xét duyệt nếu muốn chỉnh sửa."
        )
        raise CourseStateViolationError(msg)

    if not is_approved_review and should_stage(actor, course, sess):
        return queue_course_metadata_review(actor, course, data, session=sess)

    admin_override = bool(
        actor.is_admin
        and course.owner_instructor_id
        and actor.id != course.owner_instructor_id
        and course.status != "DRAFT"
        and not is_approved_review
    )
    clean_admin_reason = (data.get("reason") or "").strip()
    if admin_override and not clean_admin_reason:
        # If updating course thumbnail/cover, provide safe default admin reason
        if "thumbnail_file_asset_id" in data or set(data.keys()) <= {
            "thumbnail_file_asset_id",
            "row_version",
        }:
            clean_admin_reason = "Admin direct update of course cover image"
        else:
            raise CourseValidationError(
                "Admin direct edits to an Instructor-owned course require a reason."
            )

    if "row_version" in data and data["row_version"] is not None and course.row_version is not None:
        norm_client = normalize_row_version(data["row_version"])
        if norm_client is not None and norm_client != course.row_version:
            raise ConflictError("Course has been modified concurrently by another transaction.")

    before_state = {
        "title": course.title,
        "description": course.description,
        "learning_objectives": course.learning_objectives,
        "target_audience": course.target_audience,
        "course_code": course.course_code,
        "completion_requirements": course.completion_requirements,
        "category": course.category,
        "difficulty": course.difficulty,
        "capacity": course.capacity,
        "storage_quota_bytes": course.storage_quota_bytes,
        "thumbnail_file_asset_id": course.thumbnail_file_asset_id,
    }

    # Whitelist writable fields (defense against mass-assignment)
    if "title" in data:
        raw_title = data["title"]
        if not raw_title or not isinstance(raw_title, str) or not raw_title.strip():
            raise CourseValidationError("title cannot be empty.")
        title = raw_title.strip()
        if len(title) > 200:
            raise CourseValidationError("title cannot exceed 200 characters.")

        norm_title = title.lower()
        if norm_title != course.title_normalized:
            existing = (
                sess.query(Course)
                .filter(
                    Course.title_normalized == norm_title,
                    Course.id != course.id,
                    Course.deleted_at.is_(None),
                )
                .first()
            )
            if existing is not None:
                raise CourseAlreadyExistsError(f"A course with title '{title}' already exists.")
            course.title = title
            course.title_normalized = norm_title

    if "description" in data:
        course.description = data["description"]

    if "learning_objectives" in data:
        lo = data["learning_objectives"]
        course.learning_objectives = _normalize_and_validate_slos(lo)

    if "target_audience" in data:
        ta = data["target_audience"]
        course.target_audience = ta.strip() if isinstance(ta, str) else ta

    if "completion_requirements" in data:
        cr = data["completion_requirements"]
        course.completion_requirements = _normalize_json_or_text(cr)

    if "category" in data:
        cat = data["category"]
        course.category = cat.strip() if isinstance(cat, str) else cat

    if "difficulty" in data:
        diff = data["difficulty"]
        if diff is not None:
            if not isinstance(diff, str) or diff.upper() not in VALID_DIFFICULTIES:
                diffs = ", ".join(sorted(VALID_DIFFICULTIES))
                raise CourseValidationError(f"Invalid difficulty '{diff}'. Allowed: {diffs}.")
            course.difficulty = diff.upper()
        else:
            course.difficulty = None

    if "capacity" in data:
        cap = data["capacity"]
        if cap is not None:
            try:
                cap_int = int(cap)
                if cap_int <= 0:
                    raise ValueError
                course.capacity = cap_int
            except (ValueError, TypeError):
                raise CourseValidationError("capacity must be a positive integer.") from None
        else:
            course.capacity = None

    if "storage_quota_bytes" in data:
        quota = data["storage_quota_bytes"]
        if quota is not None:
            try:
                quota_int = int(quota)
                if quota_int <= 0:
                    raise ValueError
                course.storage_quota_bytes = quota_int
            except (ValueError, TypeError):
                raise CourseValidationError(
                    "storage_quota_bytes must be a positive integer."
                ) from None
        else:
            course.storage_quota_bytes = None

    if "thumbnail_file_asset_id" in data:
        thumb = data["thumbnail_file_asset_id"]
        if thumb is not None:
            from pwd301.models.file_import import FileAsset

            asset = None
            if isinstance(thumb, int) or (isinstance(thumb, str) and thumb.isdigit()):
                asset = sess.query(FileAsset).filter(FileAsset.id == int(thumb)).first()
            if asset is None:
                try:
                    asset_uuid = uuid.UUID(str(thumb))
                    asset = sess.query(FileAsset).filter(FileAsset.public_id == asset_uuid).first()
                except (ValueError, TypeError, AttributeError) as exc:
                    raise CourseValidationError(
                        "A valid cover image asset ID is required."
                    ) from exc
            clean_mime = (
                asset.mime_type.lower().split(";")[0].strip() if asset and asset.mime_type else ""
            )
            is_valid_image_mime = clean_mime in {
                "image/jpeg",
                "image/jpg",
                "image/pjpeg",
                "image/png",
                "image/webp",
            }
            if (
                asset is None
                or asset.course_id != course.id
                or asset.asset_type not in {"COURSE_IMAGE", "RESOURCE"}
                or asset.deleted_at is not None
                or asset.virus_scan_status != "CLEAN"
                or not asset.has_passed_malware_scan
                or not is_valid_image_mime
            ):
                raise CourseValidationError("Choose a clean image uploaded for this course.")
            else:
                course.thumbnail_file_asset_id = asset.id
        else:
            course.thumbnail_file_asset_id = None

    course.updated_at = utc_now()

    after_state = {
        "title": course.title,
        "description": course.description,
        "learning_objectives": course.learning_objectives,
        "target_audience": course.target_audience,
        "completion_requirements": course.completion_requirements,
        "category": course.category,
        "difficulty": course.difficulty,
        "capacity": course.capacity,
        "storage_quota_bytes": course.storage_quota_bytes,
        "thumbnail_file_asset_id": course.thumbnail_file_asset_id,
    }

    # Audit metadata changes
    audit_action = "COURSE_ADMIN_EDIT" if admin_override else "COURSE_UPDATED"
    audit_entry = _record_audit_event(
        sess=sess,
        actor=actor,
        action=audit_action,
        target_id=course.id,
        reason=clean_admin_reason if admin_override else data.get("reason"),
        before_json=json.dumps(before_state),
        after_json=json.dumps(after_state),
    )

    if admin_override:
        from pwd301.services.notification_service import dispatch_notification

        sess.flush()
        dispatch_notification(
            recipient_user=course.owner_instructor_id,
            event_type="SYSTEM_ADMIN_INTERVENTION",
            title=f"Quản trị viên đã chỉnh sửa khóa học {course.course_code}",
            body=(
                f"Quản trị viên đã cập nhật khóa học '{course.title}'. Lý do: {clean_admin_reason}"
            ),
            action_url=f"#/instructor/courses/manage?id={course.public_id}",
            category="SYSTEM",
            target_role="INSTRUCTOR",
            payload={
                "course_id": str(course.public_id),
                "action": "COURSE_ADMIN_EDIT",
                "reason": clean_admin_reason,
            },
            event_key=_course_notification_event_key(audit_entry, course.owner_instructor_id),
            session=sess,
        )

    if session is None and not is_approved_review:
        try:
            sess.commit()
        except sa.exc.IntegrityError as exc:
            sess.rollback()
            raise CourseAlreadyExistsError(
                "Course title conflicts with an existing active course."
            ) from exc
        except Exception:
            sess.rollback()
            raise

    from pwd301.services.realtime_service import emit_domain_event

    emit_domain_event(
        "course:updated",
        {
            "course_id": str(course.public_id),
            "id": str(course.public_id),
            "course_code": course.course_code,
            "title": course.title,
            "status": course.status,
            "owner_instructor_id": course.owner_instructor_id,
        },
    )

    return course


def queue_course_metadata_review(
    actor: User,
    course_id: Course | int | uuid.UUID | str,
    data: dict[str, Any],
    session: Session | scoped_session[Any] | None = None,
) -> CourseChangeRequest | Course:
    """Queue or upsert a course metadata change request for Admin review.

    Preserves published course metadata integrity while supporting autosave/idempotency.
    """
    sess = session if session is not None else db.session
    course = require_course_manager(actor, course_id, session=sess)

    if course.deleted_at is not None and not actor.is_admin:
        raise ForbiddenError("Cannot propose changes to a soft-deleted course.")

    # Whitelist & validate proposed metadata
    proposed: dict[str, Any] = {}
    if "course_code" in data:
        raw_code = data["course_code"]
        if not raw_code or not isinstance(raw_code, str) or not raw_code.strip():
            raise CourseValidationError("course_code cannot be empty.")
        code = raw_code.strip()
        if len(code) > 30:
            raise CourseValidationError("course_code cannot exceed 30 characters.")
        norm_code = code.upper()
        if norm_code != course.course_code_normalized:
            existing = (
                sess.query(Course)
                .filter(
                    Course.course_code_normalized == norm_code,
                    Course.id != course.id,
                    Course.deleted_at.is_(None),
                )
                .first()
            )
            if existing is not None:
                raise CourseAlreadyExistsError(f"A course with code '{code}' already exists.")
        proposed["course_code"] = code

    if "title" in data:
        raw_title = data["title"]
        if not raw_title or not isinstance(raw_title, str) or not raw_title.strip():
            raise CourseValidationError("title cannot be empty.")
        title = raw_title.strip()
        if len(title) > 200:
            raise CourseValidationError("title cannot exceed 200 characters.")
        norm_title = title.lower()
        if norm_title != course.title_normalized:
            existing = (
                sess.query(Course)
                .filter(
                    Course.title_normalized == norm_title,
                    Course.id != course.id,
                    Course.deleted_at.is_(None),
                )
                .first()
            )
            if existing is not None:
                raise CourseAlreadyExistsError(f"A course with title '{title}' already exists.")
        proposed["title"] = title

    if "description" in data:
        proposed["description"] = data["description"]

    if "learning_objectives" in data:
        proposed["learning_objectives"] = _normalize_and_validate_slos(data["learning_objectives"])

    if "target_audience" in data:
        ta = data["target_audience"]
        proposed["target_audience"] = ta.strip() if isinstance(ta, str) else ta

    if "completion_requirements" in data:
        proposed["completion_requirements"] = _normalize_json_or_text(
            data["completion_requirements"]
        )

    if "category" in data:
        cat = data["category"]
        proposed["category"] = cat.strip() if isinstance(cat, str) else cat

    if "difficulty" in data:
        diff = data["difficulty"]
        if diff is not None:
            if not isinstance(diff, str) or diff.upper() not in VALID_DIFFICULTIES:
                diffs = ", ".join(sorted(VALID_DIFFICULTIES))
                raise CourseValidationError(f"Invalid difficulty '{diff}'. Allowed: {diffs}.")
            proposed["difficulty"] = diff.upper()
        else:
            proposed["difficulty"] = None

    if "capacity" in data:
        cap = data["capacity"]
        if cap is not None:
            try:
                cap_int = int(cap)
                if cap_int <= 0:
                    raise CourseValidationError("capacity must be positive.")
                proposed["capacity"] = cap_int
            except (ValueError, TypeError):
                raise CourseValidationError("capacity must be an integer.") from None
        else:
            proposed["capacity"] = None

    if "storage_quota_bytes" in data:
        quota = data["storage_quota_bytes"]
        if quota is not None:
            try:
                quota_int = int(quota)
                if quota_int <= 0:
                    raise CourseValidationError("storage_quota_bytes must be positive.")
                proposed["storage_quota_bytes"] = quota_int
            except (ValueError, TypeError):
                raise CourseValidationError(
                    "storage_quota_bytes must be a positive integer."
                ) from None
        else:
            proposed["storage_quota_bytes"] = None

    if "thumbnail_file_asset_id" in data:
        thumb = data["thumbnail_file_asset_id"]
        if thumb is not None:
            from pwd301.models.file_import import FileAsset

            asset = None
            if isinstance(thumb, int) or (isinstance(thumb, str) and thumb.isdigit()):
                asset = sess.query(FileAsset).filter(FileAsset.id == int(thumb)).first()
            if asset is None:
                try:
                    asset_uuid = uuid.UUID(str(thumb))
                    asset = sess.query(FileAsset).filter(FileAsset.public_id == asset_uuid).first()
                except (ValueError, TypeError, AttributeError) as exc:
                    raise CourseValidationError(
                        "A valid cover image asset ID is required."
                    ) from exc
            if (
                asset is None
                or asset.course_id != course.id
                or asset.asset_type not in {"COURSE_IMAGE", "RESOURCE"}
                or asset.deleted_at is not None
                or asset.virus_scan_status != "CLEAN"
                or not asset.has_passed_malware_scan
            ):
                raise CourseValidationError(
                    "Cover image must be a clean, scanned COURSE_IMAGE asset from this course."
                )
            proposed["thumbnail_file_asset_id"] = asset.id
        else:
            proposed["thumbnail_file_asset_id"] = None

    from pwd301.services.course_workflow_service import (
        active_changeset,
        payload_for,
        working_changeset,
        write_payload,
    )

    existing = active_changeset(course.id, sess)
    if not proposed and existing is None:
        return course
    if existing is None and all(
        getattr(course, key, None) == value for key, value in proposed.items()
    ):
        return course
    req = working_changeset(actor, course, sess)
    payload = payload_for(req)
    metadata = dict(payload.get("course_metadata") or {})
    for key, value in proposed.items():
        current = getattr(course, key, None)
        equal = (
            value.strip() == current.strip()
            if isinstance(value, str) and isinstance(current, str)
            else value == current
        )
        if equal:
            metadata.pop(key, None)
        else:
            metadata[key] = value
    payload["course_metadata"] = metadata
    write_payload(req, payload, sess)
    sess.commit()
    return req


def get_course_detail(
    actor: User | None,
    course_id: Course | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> Course:
    """Retrieve course detail respecting visibility rules.

    Rules (03_RESOURCE_AUTHORIZATION_RULES.md):
    - PUBLISHED courses: visible to anyone.
    - DRAFT / ARCHIVED: visible only to current owner instructor and admin.
    - Soft-deleted: visible only to admin.

    Args:
        actor: Authenticated user or None (for anonymous visitor).
        course_id: Course instance or identifier.
        session: Optional SQLAlchemy session.

    Returns:
        The resolved Course instance.

    Raises:
        ResourceNotFoundError: If course does not exist.
        ForbiddenError: If actor lacks permission to view the course.
    """
    sess = session if session is not None else db.session
    course = _resolve_course(course_id, session=sess)
    if course is None:
        raise ResourceNotFoundError("Course not found.")

    if not can_view_course(actor, course, session=sess):
        raise ForbiddenError("You do not have permission to view this course.")

    return course


def change_course_status(
    actor: User,
    course_id: Course | int | uuid.UUID | str,
    new_status: str,
    reason: str | None = None,
    session: Session | scoped_session[Any] | None = None,
    require_thumbnail: bool = False,
) -> Course:
    """Transition course lifecycle state according to the Course State Machine.

    Transitions supported:
    - DRAFT -> SUBMITTED_FOR_REVIEW (Owner Instructor / Admin)
    - DRAFT -> TRASH (Owner Instructor / Admin)
    - SUBMITTED_FOR_REVIEW -> APPROVED (ADMIN ONLY)
    - SUBMITTED_FOR_REVIEW -> DRAFT (Admin reject with reason, or Instructor cancel)
    - APPROVED -> PUBLISHED (Owner Instructor / Admin)
    - APPROVED -> DRAFT (Admin reject / retract)
    - PUBLISHED -> ARCHIVED (Owner Instructor / Admin; dependency checked)
    - PUBLISHED -> SUBMITTED_FOR_REVIEW (Material change review request)
    - ARCHIVED -> PUBLISHED (Owner Instructor / Admin)
    - ARCHIVED -> TRASH (Owner Instructor / Admin; dependency checked)
    - TRASH -> ARCHIVED (Admin only restore)

    Args:
        actor: Authenticated user.
        course_id: Course instance or identifier.
        new_status: Desired target status.
        reason: Justification for transition (required for rejection/admin override).
        session: Optional SQLAlchemy session.
        require_thumbnail: Whether to strictly validate that the course has a thumbnail.

    Returns:
        The updated Course instance.

    Raises:
        ResourceNotFoundError: If course does not exist.
        ForbiddenError: If actor lacks permission for transition.
        CourseStateViolationError: If requested transition is invalid.
        CourseDependencyError: If archive/trash blocked by active prerequisites.
    """
    sess = session if session is not None else db.session
    course = _resolve_course(course_id, session=sess)
    if course is None:
        raise ResourceNotFoundError("Course not found.")

    course = (
        sess.query(Course)
        .filter(Course.id == course.id)
        .with_hint(Course, "WITH (UPDLOCK, HOLDLOCK)", dialect_name="mssql")
        .with_for_update()
        .populate_existing()
        .one()
    )
    target_status = new_status.strip().upper()
    if target_status not in VALID_STATUSES:
        raise CourseValidationError(f"Invalid course status: '{new_status}'.")

    current_status = course.status

    # Idempotent no-op is still an object-authorized action.
    if current_status == target_status:
        is_admin_reviewer = bool(
            actor.is_admin
            and (actor.is_primary_admin or actor.has_admin_permission("COURSE_REVIEW"))
        )
        if not (can_manage_course(actor, course, reason=reason, session=sess) or is_admin_reviewer):
            raise ForbiddenError("You do not have permission to manage this course.")
        return course

    # 1. Validate state machine transition graph
    allowed_next = ALLOWED_TRANSITIONS.get(current_status, set())
    if target_status not in allowed_next:
        raise CourseStateViolationError(
            f"Cannot transition course from '{current_status}' to '{target_status}'."
        )

    if (
        target_status == "SUBMITTED_FOR_REVIEW"
        and require_thumbnail
        and (not course.thumbnail_url or not str(course.thumbnail_url).strip())
    ):
        raise CourseValidationError(
            "Khóa học phải có ảnh bìa đại diện trước khi gửi xét duyệt xuất bản."
        )

    # 2. Check role and ownership authorization for this specific transition
    if target_status == "APPROVED":
        # Critical Invariant: Only Primary Admin or Admin with COURSE_REVIEW can approve courses
        if not actor.is_admin or not (
            actor.is_primary_admin or actor.has_admin_permission("COURSE_REVIEW")
        ):
            raise ForbiddenError(
                "Only administrators can approve courses (requires course review permission)."
            )
    elif current_status == "TRASH" and target_status in ("ARCHIVED", "DRAFT", "PUBLISHED"):
        # Restoring from trash requires primary admin or COURSE_REVIEW permission
        if not actor.is_admin or not (
            actor.is_primary_admin or actor.has_admin_permission("COURSE_REVIEW")
        ):
            raise ForbiddenError(
                "Only administrators can restore courses from TRASH (requires course review permission)."
            )
    else:
        # Standard management authorization (owner instructor or authorized admin reviewer)
        is_admin_reviewer = bool(
            actor.is_admin
            and (actor.is_primary_admin or actor.has_admin_permission("COURSE_REVIEW"))
        )
        if not (can_manage_course(actor, course, reason=reason, session=sess) or is_admin_reviewer):
            raise ForbiddenError("You do not have permission to manage this course.")

    # 3. Check active prerequisite dependencies and active enrollments before ARCHIVED or TRASH
    if target_status in ("ARCHIVED", "TRASH"):
        _check_active_prerequisite_dependencies(sess, course.id, course.course_code)
        if target_status == "TRASH" and not actor.is_admin:
            from pwd301.models.course import Enrollment

            active_enrollments = (
                sess.query(sa.func.count(Enrollment.id))
                .filter(
                    Enrollment.course_id == course.id,
                    Enrollment.status == "ACTIVE",
                )
                .scalar()
                or 0
            )
            if active_enrollments > 0:
                msg = (
                    f"Không thể chuyển khóa học vào thùng rác vì đang có "
                    f"{active_enrollments} học viên đang theo học."
                )
                raise CourseStateViolationError(msg)

    if current_status == "TRASH" and target_status == "DRAFT" and course.published_at is not None:
        raise CourseStateViolationError(
            "Cannot restore a previously published course to DRAFT status."
        )

    if current_status == "SUBMITTED_FOR_REVIEW" and target_status == "DRAFT" and actor.is_admin:
        clean_reason = (reason or "").strip()
        if len(clean_reason) < 5:
            raise CourseValidationError(
                "Lý do từ chối đề cương kiểm toán bắt buộc tối thiểu 5 ký tự."
            )

    if target_status == "SUBMITTED_FOR_REVIEW":
        # Validate that all attached resources across all active lessons are CLEAN
        for cles in course.lessons:
            if getattr(cles, "deleted_at", None) is None and getattr(cles, "status", "") != "TRASH":
                for cres in getattr(cles, "resources", []):
                    fa = cres.file_asset
                    if fa is not None and fa.virus_scan_status != "CLEAN":
                        res_name = (
                            cres.label or fa.display_name or fa.original_filename or "tệp đính kèm"
                        )
                        raise CourseValidationError(
                            f"Không thể gửi duyệt khóa học. Bài học '{cles.title}' chứa tệp đính kèm "
                            f"chưa an toàn hoặc đã bị cách ly ('{res_name}'). "
                            "Vui lòng gỡ bỏ hoặc thay thế tệp này trước khi gửi duyệt."
                        )
        thumb_asset = getattr(course, "thumbnail_file_asset", None)
        if thumb_asset and getattr(thumb_asset, "virus_scan_status", None) != "CLEAN":
            raise CourseValidationError(
                "Không thể gửi duyệt khóa học do ảnh đại diện khóa học chưa được xác thực an toàn."
            )

    if target_status in ("SUBMITTED_FOR_REVIEW", "APPROVED"):
        from pwd301.services.course_workflow_service import (
            course_asset_manifest,
            validate_submitted_assets,
        )

        validate_submitted_assets(course, course_asset_manifest(course, sess, lock=True), sess)

    before_state = {"status": current_status}
    now = utc_now()

    # 4. Apply transition mutations
    course.status = target_status
    course.updated_at = now

    if current_status == "TRASH" and target_status in ("ARCHIVED", "DRAFT", "PUBLISHED"):
        course.deleted_at = None
        course.deleted_by_user_id = None
        course.restore_until = None

    if target_status == "APPROVED":
        course.approved_at = now
        course.approved_by_user_id = actor.id

        # BUG-07: Ensure default completion rule is provisioned for legacy courses so publishing/approval succeeds
        from pwd301.services.completion_service import get_or_create_default_completion_rule

        get_or_create_default_completion_rule(course.id, session=sess)

        # Transition any unattached pending lessons to DRAFT
        from pwd301.models.course import Lesson

        pending_lessons = (
            sess.query(Lesson)
            .filter(
                Lesson.course_id == course.id,
                Lesson.status == "PENDING_APPROVAL",
                Lesson.change_request_id.is_(None),
                Lesson.deleted_at.is_(None),
            )
            .all()
        )
        for les in pending_lessons:
            les.status = "DRAFT"
            les.updated_at = now

        # BUG-07: Auto-synthesize or handle active COURSE_VERSION_CHANGESET for legacy / submitted courses
        from pwd301.models.course import CourseChangeRequest
        from pwd301.services.course_workflow_service import CHANGESET, active_changeset
        from pwd301.services.lesson_service import record_change_request_review

        active_cr = active_changeset(course.id, sess)
        if active_cr is not None:
            if active_cr.status in ("PENDING", "DRAFT"):
                active_cr.status = "APPROVED"
                active_cr.reviewed_by_user_id = actor.id
                active_cr.reviewed_at = now
                active_cr.applied_at = now
                active_cr.review_reason = reason or "Đã phê duyệt cùng khóa học."
                record_change_request_review(sess, actor, active_cr, "APPROVED")
        else:
            payload_data = {
                "action": CHANGESET,
                "course_id": str(course.public_id),
                "source": "legacy_course_approval_synthesis",
                "approved_by": actor.id,
                "reason": reason or "Phê duyệt khóa học tiền sử (legacy course approval)",
            }
            requested_by = course.owner_instructor_id or actor.id
            synthesized_cr = CourseChangeRequest(
                course_id=course.id,
                requested_by_user_id=requested_by,
                change_type=CHANGESET,
                target_type="COURSE",
                target_id=course.id,
                proposed_payload_json=json.dumps(payload_data, ensure_ascii=False),
                status="APPROVED",
                reviewed_by_user_id=actor.id,
                review_reason=reason or "Phê duyệt khóa học tiền sử (legacy course approval)",
                created_at=now,
                reviewed_at=now,
                applied_at=now,
            )
            synthesized_cr.course = course
            sess.add(synthesized_cr)
            sess.flush()
            record_change_request_review(sess, actor, synthesized_cr, "APPROVED")

    elif target_status == "PUBLISHED":
        if course.published_at is None:
            course.published_at = now

        # Ensure default completion rule exists
        from pwd301.services.completion_service import get_or_create_default_completion_rule

        get_or_create_default_completion_rule(course.id, session=sess)

        # Invariant: Auto-publish non-deleted draft lessons belonging to this course
        from pwd301.models.course import Lesson

        draft_lessons = (
            sess.query(Lesson)
            .filter(
                Lesson.course_id == course.id,
                Lesson.status.in_(["DRAFT", "PENDING_APPROVAL"]),
                Lesson.change_request_id.is_(None),
                Lesson.deleted_at.is_(None),
            )
            .all()
        )
        for les in draft_lessons:
            les.status = "PUBLISHED"
            if les.published_at is None:
                les.published_at = now
            les.updated_at = now

        import contextlib

        from pwd301.services.rag_service import auto_ingest_course_materials

        with contextlib.suppress(Exception):
            auto_ingest_course_materials(course, actor=actor, session=sess)
    elif target_status == "TRASH":
        course.deleted_at = now
        course.deleted_by_user_id = actor.id
        course.restore_until = now + datetime.timedelta(days=30)
    elif current_status == "SUBMITTED_FOR_REVIEW" and target_status == "DRAFT" and actor.is_admin:
        from pwd301.services.course_workflow_service import active_changeset, successor_draft
        from pwd301.services.lesson_service import record_change_request_review

        active_cr = active_changeset(course.id, sess)
        if active_cr is not None and active_cr.status == "PENDING":
            active_cr.status = "REJECTED"
            active_cr.reviewed_by_user_id = actor.id
            active_cr.reviewed_at = now
            active_cr.review_reason = reason
            record_change_request_review(sess, actor, active_cr, "REJECTED")
            sess.flush()
            successor_draft(actor, active_cr, sess)

    after_state = {"status": target_status}

    # 5. Record mandatory AuditEvent for critical lifecycle events
    action_map = {
        "APPROVED": "COURSE_APPROVED",
        "PUBLISHED": "COURSE_PUBLISHED",
        "TRASH": "COURSE_TRASHED",
        "ARCHIVED": (
            "COURSE_RESTORED_FROM_TRASH" if current_status == "TRASH" else "COURSE_ARCHIVED"
        ),
        "SUBMITTED_FOR_REVIEW": "COURSE_SUBMITTED_FOR_REVIEW",
        "DRAFT": (
            "COURSE_REJECTED"
            if current_status == "SUBMITTED_FOR_REVIEW" and actor.is_admin
            else "COURSE_RETRACTED_TO_DRAFT"
        ),
    }
    audit_action = action_map.get(target_status, f"COURSE_STATUS_TO_{target_status}")

    audit_entry = _record_audit_event(
        sess=sess,
        actor=actor,
        action=audit_action,
        target_id=course.id,
        reason=reason,
        before_json=json.dumps(before_state),
        after_json=json.dumps(after_state),
    )
    sess.flush()

    # 6. Dispatch in-app notifications to course owner instructor for Admin review outcomes
    if target_status == "APPROVED" and course.owner_instructor_id:
        try:
            from pwd301.services.notification_service import dispatch_notification

            dispatch_notification(
                recipient_user=course.owner_instructor_id,
                event_type="COURSE_APPROVED",
                title=f"Khóa học {course.course_code} đã được phê duyệt",
                body=(
                    f"Khóa học '{course.title}' ({course.course_code}) đã được "
                    "Quản trị viên phê duyệt. Bạn có thể xuất bản khóa học."
                ),
                action_url=f"#/instructor/courses/manage?id={course.public_id}",
                category="COURSE",
                target_role="INSTRUCTOR",
                payload={
                    "course_id": str(course.public_id),
                    "course_code": course.course_code,
                    "reason": reason or "",
                    "action_url": f"#/instructor/courses/manage?id={course.public_id}",
                },
                event_key=_course_notification_event_key(audit_entry, course.owner_instructor_id),
                session=sess,
            )
        except Exception as exc:
            logger.warning("Failed to dispatch course approval notification: %s", exc)

    elif (
        current_status == "SUBMITTED_FOR_REVIEW"
        and target_status == "DRAFT"
        and actor.is_admin
        and course.owner_instructor_id
    ):
        try:
            from pwd301.services.notification_service import dispatch_notification

            dispatch_notification(
                recipient_user=course.owner_instructor_id,
                event_type="COURSE_REJECTED",
                title=f"Khóa học {course.course_code} cần chỉnh sửa",
                body=(
                    f"Khóa học '{course.title}' ({course.course_code}) cần chỉnh sửa. "
                    f"Lý do: {reason}. Cập nhật khóa học rồi gửi duyệt lại."
                ),
                action_url=f"#/instructor/courses/manage?id={course.public_id}",
                category="COURSE",
                target_role="INSTRUCTOR",
                payload={
                    "course_id": str(course.public_id),
                    "course_code": course.course_code,
                    "reason": reason or "",
                    "action_url": f"#/instructor/courses/manage?id={course.public_id}",
                },
                event_key=_course_notification_event_key(audit_entry, course.owner_instructor_id),
                session=sess,
            )
        except Exception as exc:
            logger.warning("Failed to dispatch course rejection notification: %s", exc)

    elif target_status == "SUBMITTED_FOR_REVIEW":
        try:
            from pwd301.models.identity import Role, User
            from pwd301.services.notification_service import dispatch_notification

            admin_role = sess.query(Role).filter(Role.code == "ADMIN").first()
            if admin_role:
                admin_users = (
                    sess.query(User)
                    .filter(User.roles.contains(admin_role), User.status == "ACTIVE")
                    .all()
                )
                for adm in admin_users:
                    if adm.has_admin_permission("COURSE_REVIEW"):
                        dispatch_notification(
                            recipient_user=adm.id,
                            event_type="COURSE_SUBMITTED_FOR_REVIEW",
                            title=f"Khóa học {course.course_code} đã được gửi duyệt",
                            body=(
                                f"Giảng viên {actor.display_name} đã gửi khóa học "
                                f"'{course.title}' ({course.course_code}) để xét duyệt."
                            ),
                            action_url=f"#/admin/courses/review?id={course.public_id}",
                            category="COURSE",
                            target_role="ADMIN",
                            payload={
                                "course_id": str(course.public_id),
                                "course_code": course.course_code,
                                "action_url": f"#/admin/courses/review?id={course.public_id}",
                            },
                            event_key=_course_notification_event_key(audit_entry, adm.id),
                            session=sess,
                        )
        except Exception as exc:
            logger.warning("Failed to dispatch course submission notification to admins: %s", exc)

    if session is None:
        try:
            sess.commit()
        except Exception:
            sess.rollback()
            raise

    from pwd301.services.realtime_service import emit_domain_event

    course_event_payload = {
        "course_id": str(course.public_id),
        "id": str(course.public_id),
        "course_code": course.course_code,
        "title": course.title,
        "status": course.status,
        "owner_instructor_id": course.owner_instructor_id,
    }
    if target_status == "PUBLISHED":
        emit_domain_event("course:published", course_event_payload)
    elif target_status == "TRASH":
        emit_domain_event("course:trashed", course_event_payload)
    else:
        emit_domain_event("course:updated", course_event_payload)

    return course


def reassign_course_owner(
    admin_actor: User,
    course_id: Course | int | uuid.UUID | str,
    new_instructor_id: User | int | uuid.UUID | str | None,
    reason: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> Course:
    """Reassign course instructor ownership (Admin only).

    Invariants enforced (03_COURSE_MANAGEMENT.md, COURSE-003, COURSE-004):
    - Only ADMIN can reassign course owner.
    - Prior owner immediately loses current student detail access.
    - New owner (if not None) must exist and possess INSTRUCTOR role.
    - Course may temporarily have a NULL owner.
    - Reassignment must be permanently recorded in append-only AuditEvent.

    Args:
        admin_actor: The administrator executing the reassignment.
        course_id: Course instance or identifier.
        new_instructor_id: Target user instance, ID, or None (unassigned).
        reason: Justification for reassignment.
        session: Optional SQLAlchemy session.

    Returns:
        The updated Course instance.

    Raises:
        ForbiddenError: If actor is not an administrator.
        ResourceNotFoundError: If course does not exist.
        UserNotFoundError: If new instructor user does not exist.
        InvalidRoleAssignmentError: If target user lacks INSTRUCTOR role.
    """
    if not admin_actor.is_admin:
        raise ForbiddenError("Only administrators can reassign course ownership.")

    sess = session if session is not None else db.session
    course = _resolve_course(course_id, session=sess)
    if course is None:
        raise ResourceNotFoundError("Course not found.")

    target_user_id: int | None = None
    target_user_public_id: str | None = None
    if new_instructor_id is not None:
        target_user = _resolve_user(new_instructor_id, session=sess)
        if target_user is None:
            raise UserNotFoundError(f"Instructor user '{new_instructor_id}' not found.")
        if not target_user.has_role("INSTRUCTOR"):
            raise InvalidRoleAssignmentError(
                f"User '{target_user.email}' must have INSTRUCTOR role to own a course."
            )
        target_user_id = target_user.id
        target_user_public_id = str(target_user.public_id)

    old_owner_id = course.owner_instructor_id
    old_owner_public_id: str | None = None
    if old_owner_id:
        old_owner = sess.get(User, old_owner_id)
        if old_owner:
            old_owner_public_id = str(old_owner.public_id)
    now = utc_now()

    course.owner_instructor_id = target_user_id
    course.updated_at = now

    audit_entry = _record_audit_event(
        sess=sess,
        actor=admin_actor,
        action="COURSE_OWNER_REASSIGNED",
        target_id=course.id,
        reason=reason,
        before_json=json.dumps(
            {
                "owner_instructor_id": old_owner_id,
                "owner_instructor_public_id": old_owner_public_id,
            }
        ),
        after_json=json.dumps(
            {
                "owner_instructor_id": target_user_id,
                "owner_instructor_public_id": target_user_public_id,
            }
        ),
    )
    sess.flush()

    # Dual In-App Notifications for Former and New Course Owners
    if old_owner_id:
        try:
            from pwd301.services.notification_service import dispatch_notification

            dispatch_notification(
                recipient_user=old_owner_id,
                event_type="COURSE_OWNER_REASSIGNED",
                title=f"Bạn không còn phụ trách khóa học {course.course_code}",
                body=(f"Khóa học '{course.title}' đã được giao cho giảng viên khác."),
                category="COURSE",
                target_role="INSTRUCTOR",
                payload={
                    "course_id": str(course.public_id),
                    "course_code": course.course_code,
                    "reason": reason or "",
                },
                event_key=_course_notification_event_key(audit_entry, old_owner_id),
                session=sess,
            )
        except Exception as exc:
            logger.warning(
                "Failed to dispatch reassignment notification to previous owner %s: %s",
                old_owner_id,
                exc,
            )

    if target_user_id:
        try:
            from pwd301.services.notification_service import dispatch_notification

            dispatch_notification(
                recipient_user=target_user_id,
                event_type="COURSE_OWNER_REASSIGNED",
                title=f"Bạn được giao khóa học {course.course_code}",
                body=(f"Bạn đã được giao phụ trách khóa học '{course.title}'."),
                action_url=f"#/instructor/courses/manage?id={course.public_id}",
                category="COURSE",
                target_role="INSTRUCTOR",
                payload={
                    "course_id": str(course.public_id),
                    "course_code": course.course_code,
                    "reason": reason or "",
                },
                event_key=_course_notification_event_key(audit_entry, target_user_id),
                session=sess,
            )
        except Exception as exc:
            logger.warning(
                "Failed to dispatch reassignment notification to new owner %s: %s",
                target_user_id,
                exc,
            )

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    from pwd301.services.realtime_service import emit_domain_event

    emit_domain_event(
        "course:updated",
        {
            "course_id": str(course.public_id),
            "id": str(course.public_id),
            "course_code": course.course_code,
            "title": course.title,
            "status": course.status,
            "owner_instructor_id": course.owner_instructor_id,
        },
    )

    return course


def swap_course_owners(
    admin_actor: User,
    course_a_id: Course | int | uuid.UUID | str,
    course_b_id: Course | int | uuid.UUID | str,
    reason: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> tuple[Course, Course]:
    """Atomically swap the instructor owners of two courses (Admin only).

    Invariants enforced:
    - Only ADMIN can swap course owners.
    - Both courses must exist.
    - Cannot swap a course with itself.
    - At least one course must have an assigned owner to execute a meaningful swap.
    - If an owner is present, that user must exist, have INSTRUCTOR role, and not be suspended.
    - Both courses have their owners swapped in a single atomic transaction.
    - Append-only AuditEvent records the swap action with full before/after states.
    - Dispatches dual in-app notifications to affected instructors.
    """
    if not admin_actor.is_admin:
        raise ForbiddenError("Only administrators can swap course ownership.")

    sess = session if session is not None else db.session
    course_a = _resolve_course(course_a_id, session=sess)
    course_b = _resolve_course(course_b_id, session=sess)
    if course_a is None or course_b is None:
        raise ResourceNotFoundError("One or both courses not found.")

    if course_a.id == course_b.id:
        raise CourseValidationError("Cannot swap course ownership with itself.")

    owner_a_id = course_a.owner_instructor_id
    owner_b_id = course_b.owner_instructor_id

    if owner_a_id is None and owner_b_id is None:
        raise CourseValidationError(
            "At least one course must have an assigned instructor to perform a swap."
        )

    if owner_a_id == owner_b_id and owner_a_id is not None:
        raise CourseValidationError("Both courses are already owned by the same instructor.")

    if owner_a_id is not None:
        user_a = sess.get(User, owner_a_id)
        if user_a is None or not user_a.has_role("INSTRUCTOR") or user_a.is_suspended:
            raise InvalidRoleAssignmentError(
                f"Current owner of {course_a.course_code} is not an active instructor."
            )

    if owner_b_id is not None:
        user_b = sess.get(User, owner_b_id)
        if user_b is None or not user_b.has_role("INSTRUCTOR") or user_b.is_suspended:
            raise InvalidRoleAssignmentError(
                f"Current owner of {course_b.course_code} is not an active instructor."
            )

    now = utc_now()
    course_a.owner_instructor_id = owner_b_id
    course_a.updated_at = now
    course_b.owner_instructor_id = owner_a_id
    course_b.updated_at = now

    audit_entry = _record_audit_event(
        sess=sess,
        actor=admin_actor,
        action="COURSE_OWNER_SWAPPED",
        target_id=course_a.id,
        reason=reason,
        before_json=json.dumps(
            {
                "course_a": {
                    "id": course_a.id,
                    "code": course_a.course_code,
                    "owner_id": owner_a_id,
                },
                "course_b": {
                    "id": course_b.id,
                    "code": course_b.course_code,
                    "owner_id": owner_b_id,
                },
            }
        ),
        after_json=json.dumps(
            {
                "course_a": {
                    "id": course_a.id,
                    "code": course_a.course_code,
                    "owner_id": owner_b_id,
                },
                "course_b": {
                    "id": course_b.id,
                    "code": course_b.course_code,
                    "owner_id": owner_a_id,
                },
            }
        ),
    )
    sess.flush()

    try:
        from pwd301.services.notification_service import dispatch_notification

        if owner_a_id and owner_b_id:
            try:
                dispatch_notification(
                    recipient_user=owner_a_id,
                    event_type="COURSE_OWNER_REASSIGNED",
                    title=f"Hoán đổi phân công giảng dạy {course_a.course_code} ↔ {course_b.course_code}",
                    body=(
                        f"Bạn đã chuyển giao môn '{course_a.title}' và tiếp nhận môn '{course_b.title}'."
                    ),
                    action_url=f"#/instructor/courses/manage?id={course_b.public_id}",
                    category="COURSE",
                    target_role="INSTRUCTOR",
                    payload={
                        "course_from": str(course_a.public_id),
                        "course_to": str(course_b.public_id),
                        "reason": reason or "",
                    },
                    event_key=_course_notification_event_key(audit_entry, owner_a_id),
                    session=sess,
                )
            except Exception as exc:
                logger.warning(
                    "Failed to dispatch swap notification to instructor A %s: %s", owner_a_id, exc
                )

            try:
                dispatch_notification(
                    recipient_user=owner_b_id,
                    event_type="COURSE_OWNER_REASSIGNED",
                    title=f"Hoán đổi phân công giảng dạy {course_b.course_code} ↔ {course_a.course_code}",
                    body=(
                        f"Bạn đã chuyển giao môn '{course_b.title}' và tiếp nhận môn '{course_a.title}'."
                    ),
                    action_url=f"#/instructor/courses/manage?id={course_a.public_id}",
                    category="COURSE",
                    target_role="INSTRUCTOR",
                    payload={
                        "course_from": str(course_b.public_id),
                        "course_to": str(course_a.public_id),
                        "reason": reason or "",
                    },
                    event_key=_course_notification_event_key(audit_entry, owner_b_id),
                    session=sess,
                )
            except Exception as exc:
                logger.warning(
                    "Failed to dispatch swap notification to instructor B %s: %s", owner_b_id, exc
                )
    except ImportError:
        pass

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    from pwd301.services.realtime_service import emit_domain_event

    emit_domain_event(
        "course:updated",
        {
            "course_id": str(course.public_id),
            "id": str(course.public_id),
            "course_code": course.course_code,
            "title": course.title,
            "status": course.status,
            "owner_instructor_id": course.owner_instructor_id,
        },
    )

    return course_a, course_b


def publish_course(
    actor: User,
    course_id: Course | int | uuid.UUID | str,
    reason: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> Course:
    """Publish a course by transitioning it to PUBLISHED status."""
    return change_course_status(
        actor=actor,
        course_id=course_id,
        new_status="PUBLISHED",
        reason=reason,
        session=session,
    )


def trash_course(
    actor: User,
    course_id: Course | int | uuid.UUID | str,
    reason: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> Course:
    """Soft-delete a course by transitioning it to TRASH.

    Invariants enforced:
    - Sets deleted_at = utc_now() and status = 'TRASH'.
    - DB uses NO ACTION on FKs; application layer verifies prerequisite safety.
    - Never executes hard SQL DELETE.

    Args:
        actor: Authenticated user (owner instructor or admin).
        course_id: Course instance or identifier.
        reason: Optional deletion reason.
        session: Optional SQLAlchemy session.

    Returns:
        The soft-deleted Course instance.
    """
    return change_course_status(
        actor=actor,
        course_id=course_id,
        new_status="TRASH",
        reason=reason,
        session=session,
    )


def hard_delete_draft_course(
    actor: User,
    course_id: Course | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> bool:
    """Hard-delete an unpublished DRAFT course owned by the instructor.

    Invariants:
    - Only courses in status 'DRAFT' that have never been published (published_at is None)
      can be hard-deleted.
    - Cascades through unpublished child entities (lessons, units, completion rules, change requests).
    - Preserves safety: raises ForbiddenError if published or not owner/admin.
    """
    sess = session if session is not None else db.session
    course = require_course_manager(actor, course_id, session=sess)

    if course.published_at is not None or course.status != "DRAFT":
        raise ForbiddenError("Chỉ có thể xóa vĩnh viễn khóa học nháp chưa từng xuất bản.")

    cid = course.id

    from pwd301.models.assessment import (
        Assessment,
        AssessmentBlueprint,
        AssessmentQuestionAssignment,
        AssessmentQuestionPool,
        AssessmentSection,
    )
    from pwd301.models.course import (
        CourseChangeRequest,
        CourseCompletionRule,
        CourseCompletionSummary,
        CoursePrerequisite,
        LearningUnit,
        Lesson,
        LessonProgress,
        LessonProgressReceipt,
        LessonResource,
    )
    from pwd301.models.file_import import FileAsset

    # Delete draft assessments
    assessments = sess.query(Assessment).filter(Assessment.course_id == cid).all()
    for a in assessments:
        sess.query(AssessmentQuestionAssignment).filter(AssessmentQuestionAssignment.assessment_id == a.id).delete(synchronize_session=False)
        sess.query(AssessmentSection).filter(AssessmentSection.assessment_id == a.id).delete(synchronize_session=False)
        sess.query(AssessmentQuestionPool).filter(AssessmentQuestionPool.assessment_id == a.id).delete(synchronize_session=False)
        sess.query(AssessmentBlueprint).filter(AssessmentBlueprint.assessment_id == a.id).delete(synchronize_session=False)
        sess.delete(a)

    # Delete lessons and resources
    lessons = sess.query(Lesson).filter(Lesson.course_id == cid).all()
    for l in lessons:
        sess.query(LessonResource).filter(LessonResource.lesson_id == l.id).delete(synchronize_session=False)
        sess.query(LessonProgressReceipt).filter(LessonProgressReceipt.lesson_id == l.id).delete(synchronize_session=False)
        sess.query(LessonProgress).filter(LessonProgress.lesson_id == l.id).delete(synchronize_session=False)
        sess.delete(l)

    # Delete learning units
    sess.query(LearningUnit).filter(LearningUnit.course_id == cid).delete(synchronize_session=False)

    # Delete change requests & completion rules
    sess.query(CourseChangeRequest).filter(CourseChangeRequest.course_id == cid).delete(synchronize_session=False)
    sess.query(CourseCompletionRule).filter(CourseCompletionRule.course_id == cid).delete(synchronize_session=False)
    sess.query(CourseCompletionSummary).filter(CourseCompletionSummary.course_id == cid).delete(synchronize_session=False)
    sess.query(CoursePrerequisite).filter(sa.or_(CoursePrerequisite.course_id == cid, CoursePrerequisite.prerequisite_course_id == cid)).delete(synchronize_session=False)

    # Delete file assets associated with this course
    sess.query(FileAsset).filter(FileAsset.course_id == cid).delete(synchronize_session=False)

    # Delete the course itself
    sess.delete(course)
    sess.commit()
    return True



def list_courses(
    actor: User | None = None,
    status: str | None = None,
    category: str | None = None,
    difficulty: str | None = None,
    search: str | None = None,
    page: int = 1,
    per_page: int = 20,
    include_deleted: bool = False,
    session: Session | scoped_session[Any] | None = None,
) -> tuple[list[Course], int]:
    """Query courses catalog with pagination, filtering, and role scoping.

    Args:
        actor: Authenticated user or None.
        status: Optional status filter.
        category: Optional category filter.
        difficulty: Optional difficulty filter.
        search: Optional text search in title or code.
        page: 1-indexed page number.
        per_page: Items per page (capped at 100).
        include_deleted: If True and actor is Admin, includes soft-deleted courses.
        session: Optional SQLAlchemy session.

    Returns:
        Tuple of (courses_list, total_count).
    """
    sess = session if session is not None else db.session
    query = sess.query(Course)

    # Filter out soft-deleted records unless Admin explicitly requests them
    if not (include_deleted and actor is not None and actor.is_admin):
        query = query.filter(Course.deleted_at.is_(None))

    # Visibility scoping
    if actor is None or not actor.is_active:
        query = query.filter(Course.status == "PUBLISHED")
    elif actor.is_admin:
        if status:
            query = query.filter(Course.status == status.upper())
    elif actor.has_role("INSTRUCTOR"):
        # Instructors see published courses + their own courses
        if status:
            query = query.filter(
                Course.status == status.upper(),
                sa.or_(
                    Course.status == "PUBLISHED",
                    Course.owner_instructor_id == actor.id,
                ),
            )
        else:
            query = query.filter(
                sa.or_(
                    Course.status == "PUBLISHED",
                    Course.owner_instructor_id == actor.id,
                )
            )
    else:
        # Students see only published courses
        query = query.filter(Course.status == "PUBLISHED")

    if category:
        query = query.filter(Course.category.ilike(f"%{category.strip()}%"))

    if difficulty:
        query = query.filter(Course.difficulty == difficulty.upper())

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            sa.or_(
                Course.title.ilike(s),
                Course.course_code.ilike(s),
            )
        )

    total_count = query.count()
    limit = min(max(per_page, 1), 100)
    offset = max(page - 1, 0) * limit

    courses = query.order_by(Course.created_at.desc()).offset(offset).limit(limit).all()

    return courses, total_count


def get_faculty_workload_metrics(
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Calculate academic teaching workload and SLA metrics for all faculty members.

    Aggregates courses owned by active instructors, active student enrollment counts,
    and estimates academic teaching hours (60 hours per course base standard).

    Returns:
        dict containing:
        - total_faculty: total count of users with INSTRUCTOR role
        - instructors: list of faculty workload profiles
        - summary: aggregate statistics
    """
    sess = session if session is not None else db.session

    instructor_role = sess.query(Role).filter(Role.code == "INSTRUCTOR").first()
    if not instructor_role:
        return {
            "total_faculty": 0,
            "instructors": [],
            "summary": {
                "underload_count": 0,
                "standard_count": 0,
                "overload_count": 0,
                "total_assigned_courses": 0,
            },
        }

    # Query all users having the INSTRUCTOR role
    instructors = (
        sess.query(User)
        .filter(User.roles.contains(instructor_role))
        .order_by(User.display_name.asc(), User.email.asc())
        .all()
    )

    instructor_list: list[dict[str, Any]] = []
    underload_count = 0
    standard_count = 0
    overload_count = 0
    total_assigned_courses = 0

    # Batch load all managed (non-TRASH) courses for all faculty in 1 query
    instructor_ids = [ins.id for ins in instructors]
    courses_by_instructor: dict[int, list[Course]] = {ins_id: [] for ins_id in instructor_ids}
    all_course_ids: list[int] = []

    if instructor_ids:
        all_courses = (
            sess.query(Course)
            .filter(
                Course.owner_instructor_id.in_(instructor_ids),
                Course.status != "TRASH",
            )
            .order_by(Course.created_at.desc())
            .all()
        )
        for c in all_courses:
            if c.owner_instructor_id in courses_by_instructor:
                courses_by_instructor[c.owner_instructor_id].append(c)
            all_course_ids.append(c.id)

    # Batch load active student enrollment counts grouped by course in 1 query
    enrollment_counts_by_course: dict[int, int] = {}
    if all_course_ids:
        counts = (
            sess.query(Enrollment.course_id, sa.func.count(Enrollment.id))
            .filter(
                Enrollment.course_id.in_(all_course_ids),
                Enrollment.status == "ACTIVE",
            )
            .group_by(Enrollment.course_id)
            .all()
        )
        for cid, cnt in counts:
            enrollment_counts_by_course[cid] = int(cnt)

    for ins in instructors:
        courses = courses_by_instructor.get(ins.id, [])
        course_count = len(courses)
        total_assigned_courses += course_count

        active_students_count = sum(enrollment_counts_by_course.get(c.id, 0) for c in courses)

        estimated_hours = course_count * 60
        max_hours = 300
        workload_pct = min(100, round((estimated_hours / max_hours) * 100)) if max_hours else 0

        if course_count == 0:
            workload_status = "UNASSIGNED"
            underload_count += 1
        elif estimated_hours < 120:
            workload_status = "UNDERLOAD"
            underload_count += 1
        elif estimated_hours <= 240:
            workload_status = "STANDARD"
            standard_count += 1
        else:
            workload_status = "OVERLOAD"
            overload_count += 1

        instructor_list.append(
            {
                "user_id": str(ins.public_id),
                "email": ins.email,
                "display_name": ins.display_name or ins.email.split("@")[0],
                "status": ins.status,
                "assigned_courses_count": course_count,
                "active_students_count": active_students_count,
                "estimated_hours": estimated_hours,
                "max_hours": max_hours,
                "workload_pct": workload_pct,
                "workload_status": workload_status,
                "courses": [
                    {
                        "course_id": str(c.public_id),
                        "course_code": c.course_code,
                        "title": c.title,
                        "status": c.status,
                        "difficulty": c.difficulty,
                    }
                    for c in courses
                ],
            }
        )

    return {
        "total_faculty": len(instructors),
        "instructors": instructor_list,
        "summary": {
            "underload_count": underload_count,
            "standard_count": standard_count,
            "overload_count": overload_count,
            "total_assigned_courses": total_assigned_courses,
        },
    }


def get_course_last_rejection(
    course_id: int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any] | None:
    """Retrieve the most recent rejection details for a course from AuditEvent."""
    sess = session if session is not None else db.session
    course = _resolve_course(course_id, session=sess)
    if course is None:
        return None
    last_event = (
        sess.query(AuditEvent)
        .filter(
            AuditEvent.action == "COURSE_REJECTED",
            AuditEvent.target_id == course.id,
        )
        .order_by(AuditEvent.id.desc())
        .first()
    )
    if last_event is None:
        return None
    return {
        "reason": last_event.reason,
        "rejected_at": last_event.created_at.isoformat() if last_event.created_at else None,
        "actor_id": str(last_event.actor_user_id) if last_event.actor_user_id else None,
    }
