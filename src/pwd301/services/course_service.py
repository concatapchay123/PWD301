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
from pwd301.models.course import Course, CourseCompletionRule, CoursePrerequisite, Enrollment
from pwd301.models.identity import Role, User
from pwd301.models.notification_audit import AuditEvent
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
)

logger = logging.getLogger(__name__)

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
        try:
            thumbnail_file_asset_id = int(thumbnail_file_asset_id)
        except (ValueError, TypeError):
            raise CourseValidationError("thumbnail_file_asset_id must be an integer.") from None

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
        learning_objectives=_normalize_json_or_text(data.get("learning_objectives")),
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

    return course


def update_course(
    actor: User,
    course_id: Course | int | uuid.UUID | str,
    data: dict[str, Any],
    session: Session | scoped_session[Any] | None = None,
) -> Course:
    """Update editable course metadata with strict mass-assignment defense.

    Args:
        actor: Authenticated user (must be current course manager or admin).
        course_id: Course model instance or identifier.
        data: Dictionary of fields to update.
        session: Optional SQLAlchemy session.

    Returns:
        The updated Course instance.

    Raises:
        ResourceNotFoundError: If course does not exist.
        ForbiddenError: If actor lacks management rights (IDOR prevention).
        CourseValidationError: If metadata values are invalid.
        CourseAlreadyExistsError: If new title conflicts with an existing course.
    """
    sess = session if session is not None else db.session
    course = require_course_manager(actor, course_id, session=sess)

    if course.deleted_at is not None and not actor.is_admin:
        raise ForbiddenError("Cannot update a soft-deleted course.")

    if "row_version" in data and data["row_version"] is not None and course.row_version is not None:
        norm_client = normalize_row_version(data["row_version"])
        if norm_client is not None and norm_client != course.row_version:
            raise ConflictError("Course has been modified concurrently by another transaction.")

    before_state = {
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
        course.learning_objectives = _normalize_json_or_text(lo)

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
            try:
                course.thumbnail_file_asset_id = int(thumb)
            except (ValueError, TypeError):
                raise CourseValidationError("thumbnail_file_asset_id must be an integer.") from None
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
    _record_audit_event(
        sess=sess,
        actor=actor,
        action="COURSE_UPDATED",
        target_id=course.id,
        reason=data.get("reason"),
        before_json=json.dumps(before_state),
        after_json=json.dumps(after_state),
    )

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

    return course


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

    target_status = new_status.strip().upper()
    if target_status not in VALID_STATUSES:
        raise CourseValidationError(f"Invalid course status: '{new_status}'.")

    current_status = course.status

    # Idempotent no-op
    if current_status == target_status:
        return course

    # 1. Validate state machine transition graph
    allowed_next = ALLOWED_TRANSITIONS.get(current_status, set())
    if target_status not in allowed_next:
        raise CourseStateViolationError(
            f"Cannot transition course from '{current_status}' to '{target_status}'."
        )

    # 2. Check role and ownership authorization for this specific transition
    if target_status == "APPROVED":
        # Critical Invariant: Only ADMIN can approve courses
        if not actor.is_admin:
            raise ForbiddenError("Only administrators can approve courses.")
    elif current_status == "TRASH" and target_status in ("ARCHIVED", "DRAFT", "PUBLISHED"):
        # Restoring from trash requires ADMIN privilege
        if not actor.is_admin:
            raise ForbiddenError("Only administrators can restore courses from TRASH.")
    else:
        # Standard management authorization
        if not can_manage_course(actor, course, reason=reason, session=sess):
            raise ForbiddenError("You do not have permission to manage this course.")

    # 3. Check active prerequisite dependencies before ARCHIVED or TRASH
    if target_status in ("ARCHIVED", "TRASH"):
        _check_active_prerequisite_dependencies(sess, course.id, course.course_code)

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
    elif target_status == "PUBLISHED":
        if course.published_at is None:
            course.published_at = now
    elif target_status == "TRASH":
        course.deleted_at = now
        course.deleted_by_user_id = actor.id
        course.restore_until = now + datetime.timedelta(days=30)

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

    _record_audit_event(
        sess=sess,
        actor=actor,
        action=audit_action,
        target_id=course.id,
        reason=reason,
        before_json=json.dumps(before_state),
        after_json=json.dumps(after_state),
    )

    # 6. Dispatch in-app notifications to course owner instructor for Admin review outcomes
    if target_status == "APPROVED" and course.owner_instructor_id:
        try:
            from pwd301.services.notification_service import dispatch_notification

            dispatch_notification(
                recipient_user=course.owner_instructor_id,
                event_type="COURSE_APPROVED",
                title=f"Đề cương môn học {course.course_code} đã được phê duyệt",
                body=(
                    f"Đề cương môn học '{course.title}' ({course.course_code}) đã được "
                    "Quản trị viên phê duyệt. Khóa học đã sẵn sàng để xuất bản "
                    "hoặc cập nhật nội dung bài giảng."
                ),
                action_url=f"#/instructor/courses/manage?id={course.public_id}",
                category="COURSE",
                payload={
                    "course_id": str(course.public_id),
                    "course_code": course.course_code,
                    "reason": reason or "",
                    "action_url": f"#/instructor/courses/manage?id={course.public_id}",
                },
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
                title=f"Đề cương môn học {course.course_code} yêu cầu chỉnh sửa",
                body=(
                    f"Đề cương môn học '{course.title}' ({course.course_code}) đã bị "
                    f"Quản trị viên từ chối phê duyệt. Lý do kiểm toán: {reason}. "
                    "Vui lòng cập nhật đề cương và gửi lại thẩm định."
                ),
                action_url=f"#/instructor/courses/manage?id={course.public_id}",
                category="COURSE",
                payload={
                    "course_id": str(course.public_id),
                    "course_code": course.course_code,
                    "reason": reason or "",
                    "action_url": f"#/instructor/courses/manage?id={course.public_id}",
                },
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
                            title=f"Đề cương môn học {course.course_code} đã được gửi duyệt",
                            body=(
                                f"Giảng viên {actor.display_name} đã nộp đề cương khóa học "
                                f"'{course.title}' ({course.course_code}) để thẩm định xuất bản."
                            ),
                            action_url="#/admin/governance?tab=courses",
                            category="COURSE",
                            payload={
                                "course_id": str(course.public_id),
                                "course_code": course.course_code,
                                "action_url": "#/admin/governance?tab=courses",
                            },
                            session=sess,
                        )
        except Exception as exc:
            logger.warning("Failed to dispatch course submission notification to admins: %s", exc)

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

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

    _record_audit_event(
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

    # Dual In-App Notifications for Former and New Course Owners
    if old_owner_id:
        try:
            from pwd301.services.notification_service import dispatch_notification

            dispatch_notification(
                recipient_user=old_owner_id,
                event_type="COURSE_OWNER_REASSIGNED",
                title=f"Thông báo điều chuyển môn học {course.course_code}",
                body=(
                    f"Môn học {course.course_code} - '{course.title}' đã được chuyển giao/bàn giao "
                    f"trách nhiệm quản lý cho giảng viên khác theo quyết định của Quản trị viên."
                ),
                category="COURSE",
                payload={
                    "course_id": str(course.public_id),
                    "course_code": course.course_code,
                    "reason": reason or "",
                },
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
                title=f"Phân công phụ trách môn học {course.course_code}",
                body=(
                    f"Bạn đã được phân công tiếp nhận phụ trách quản lý môn học "
                    f"{course.course_code} - '{course.title}' từ Ban Quản trị học vụ."
                ),
                category="COURSE",
                payload={
                    "course_id": str(course.public_id),
                    "course_code": course.course_code,
                    "reason": reason or "",
                },
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

    return course


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

    for ins in instructors:
        # Get active/managed courses (non-TRASH)
        courses = (
            sess.query(Course)
            .filter(
                Course.owner_instructor_id == ins.id,
                Course.status != "TRASH",
            )
            .order_by(Course.created_at.desc())
            .all()
        )

        course_ids = [c.id for c in courses]
        course_count = len(courses)
        total_assigned_courses += course_count

        active_students_count = 0
        if course_ids:
            active_students_count = (
                sess.query(Enrollment)
                .filter(
                    Enrollment.course_id.in_(course_ids),
                    Enrollment.status == "ACTIVE",
                )
                .count()
            )

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
