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

import json
import uuid
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Session, scoped_session

from pwd301.extensions import db
from pwd301.models.course import Course, CourseCompletionRule, CoursePrerequisite
from pwd301.models.identity import User
from pwd301.models.notification_audit import AuditEvent
from pwd301.models.types import utc_now
from pwd301.services.authorization_service import (
    _resolve_course,
    _resolve_user,
    can_manage_course,
    can_view_course,
    require_course_manager,
)
from pwd301.services.exceptions import (
    CourseAlreadyExistsError,
    CourseDependencyError,
    CourseStateViolationError,
    CourseValidationError,
    ForbiddenError,
    InvalidRoleAssignmentError,
    ResourceNotFoundError,
    UserNotFoundError,
)

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
    "PUBLISHED": {"ARCHIVED", "SUBMITTED_FOR_REVIEW"},
    "ARCHIVED": {"PUBLISHED", "TRASH"},
    "TRASH": {"ARCHIVED"},
}

# Mass-assignment safe writable metadata fields
UPDATABLE_FIELDS = {
    "title",
    "description",
    "category",
    "difficulty",
    "capacity",
    "storage_quota_bytes",
    "thumbnail_file_asset_id",
}


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
    sess.flush()

    # Create default course completion rule per 05_DATA_DICTIONARY_COURSE.md
    completion_rule = CourseCompletionRule(
        course_id=course.id,
        require_all_required_lessons=True,
        require_required_assessments=True,
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

    before_state = {
        "title": course.title,
        "description": course.description,
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
        "category": course.category,
        "difficulty": course.difficulty,
        "capacity": course.capacity,
        "storage_quota_bytes": course.storage_quota_bytes,
        "thumbnail_file_asset_id": course.thumbnail_file_asset_id,
    }

    # Audit metadata changes if published or explicitly modified by admin
    if course.status == "PUBLISHED" or actor.is_admin:
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
    elif current_status == "TRASH" and target_status == "ARCHIVED":
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

    before_state = {"status": current_status}
    now = utc_now()

    # 4. Apply transition mutations
    course.status = target_status
    course.updated_at = now

    if target_status == "APPROVED":
        course.approved_at = now
        course.approved_by_user_id = actor.id
    elif target_status == "PUBLISHED":
        if course.published_at is None:
            course.published_at = now
    elif target_status == "TRASH":
        course.deleted_at = now
        course.deleted_by_user_id = actor.id
    elif current_status == "TRASH" and target_status == "ARCHIVED":
        course.deleted_at = None
        course.deleted_by_user_id = None

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
    if new_instructor_id is not None:
        target_user = _resolve_user(new_instructor_id, session=sess)
        if target_user is None:
            raise UserNotFoundError(f"Instructor user '{new_instructor_id}' not found.")
        if not target_user.has_role("INSTRUCTOR"):
            raise InvalidRoleAssignmentError(
                f"User '{target_user.email}' must have INSTRUCTOR role to own a course."
            )
        target_user_id = target_user.id

    old_owner_id = course.owner_instructor_id
    now = utc_now()

    course.owner_instructor_id = target_user_id
    course.updated_at = now

    _record_audit_event(
        sess=sess,
        actor=admin_actor,
        action="COURSE_OWNER_REASSIGNED",
        target_id=course.id,
        reason=reason,
        before_json=json.dumps({"owner_instructor_id": old_owner_id}),
        after_json=json.dumps({"owner_instructor_id": target_user_id}),
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
