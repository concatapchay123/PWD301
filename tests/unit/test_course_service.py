"""Unit tests for Course Management Service, State Machine, Ownership, and Soft Delete."""

from __future__ import annotations

import io
import json
import uuid

import pytest
from flask import Flask
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import CourseCompletionRule, CoursePrerequisite
from pwd301.models.identity import Role, User
from pwd301.models.notification_audit import AuditEvent, Notification, NotificationEvent
from pwd301.services.course_service import (
    change_course_status,
    create_course,
    get_course_detail,
    get_course_thumbnail_asset,
    list_courses,
    reassign_course_owner,
    trash_course,
    update_course,
)
from pwd301.services.exceptions import (
    CourseAlreadyExistsError,
    CourseDependencyError,
    CourseStateViolationError,
    CourseValidationError,
    ForbiddenError,
    InvalidRoleAssignmentError,
    UserNotFoundError,
)
from pwd301.services.file_service import store_file_stream
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
    """Ensure canonical roles exist in test database."""
    sess: Session = db.session
    role_map: dict[str, Role] = {}
    for code, name in [
        ("STUDENT", "Student"),
        ("INSTRUCTOR", "Instructor"),
        ("ADMIN", "System Administrator"),
    ]:
        role = sess.query(Role).filter(Role.code == code).first()
        if role is None:
            role = Role(code=code, name=name)
            sess.add(role)
            sess.flush()
        role_map[code] = role
    sess.commit()
    return role_map


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create a verified student user."""
    return register_user("student_test@example.com", "Password@123", "Student User")


@pytest.fixture
def instructor_one(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Instructor One."""
    u = register_user("instructor_one@example.com", "Password@123", "Instructor One")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def instructor_two(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Instructor Two."""
    u = register_user("instructor_two@example.com", "Password@123", "Instructor Two")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create an Admin user."""
    u = register_user("admin_test@example.com", "Password@123", "Admin User")
    return assign_role_to_user(u.id, "ADMIN")


def test_create_course_success(app: Flask, instructor_one: User) -> None:
    """Test successful course creation with default DRAFT status."""
    data = {
        "course_code": "CS-101",
        "title": "Intro to Computer Science",
        "description": "Foundational programming course.",
        "category": "Computer Science",
        "difficulty": "BEGINNER",
        "capacity": 50,
        "storage_quota_bytes": 1073741824,
    }

    course = create_course(instructor_one, data)
    assert course.id is not None
    assert course.course_code == "CS-101"
    assert course.course_code_normalized == "CS-101"
    assert course.title == "Intro to Computer Science"
    assert course.title_normalized == "intro to computer science"
    assert course.status == "DRAFT"
    assert course.owner_instructor_id == instructor_one.id
    assert course.capacity == 50
    assert course.deleted_at is None

    # Check default completion rule was created
    sess: Session = db.session
    rule = sess.query(CourseCompletionRule).filter_by(course_id=course.id).first()
    assert rule is not None
    assert rule.require_all_required_lessons is True
    assert rule.require_required_assessments is True

    # Check AuditEvent
    audit = sess.query(AuditEvent).filter_by(action="COURSE_CREATED", target_id=course.id).first()
    assert audit is not None
    assert audit.actor_user_id == instructor_one.id


def test_create_course_validation_errors(
    app: Flask,
    instructor_one: User,
    student_user: User,
) -> None:
    """Test validation errors for required and constrained fields."""
    # Student cannot create course
    with pytest.raises(ForbiddenError):
        create_course(student_user, {"course_code": "BIO-101", "title": "Biology"})

    # Empty course_code
    with pytest.raises(CourseValidationError, match="course_code is required"):
        create_course(instructor_one, {"course_code": "", "title": "Biology"})

    # Empty title
    with pytest.raises(CourseValidationError, match="title is required"):
        create_course(instructor_one, {"course_code": "BIO-101", "title": ""})

    # Invalid difficulty
    with pytest.raises(CourseValidationError, match="Invalid difficulty"):
        create_course(
            instructor_one,
            {"course_code": "BIO-101", "title": "Biology", "difficulty": "EXTREME"},
        )

    # Invalid capacity
    with pytest.raises(CourseValidationError, match="capacity must be a positive integer"):
        create_course(
            instructor_one,
            {"course_code": "BIO-101", "title": "Biology", "capacity": -5},
        )

    # Invalid storage_quota_bytes
    with pytest.raises(
        CourseValidationError,
        match="storage_quota_bytes must be a positive integer",
    ):
        create_course(
            instructor_one,
            {"course_code": "BIO-101", "title": "Biology", "storage_quota_bytes": 0},
        )


def test_create_course_duplicate_code_and_title(app: Flask, instructor_one: User) -> None:
    """Test duplicate code and title rejection (COURSE-001, COURSE-002)."""
    create_course(instructor_one, {"course_code": "MATH-101", "title": "Calculus I"})

    # Duplicate code (case-insensitive)
    with pytest.raises(CourseAlreadyExistsError, match="code 'MATH-101' already exists"):
        create_course(instructor_one, {"course_code": "math-101", "title": "Calculus Different"})

    # Duplicate title (case-insensitive)
    with pytest.raises(CourseAlreadyExistsError, match="title 'CALCULUS I' already exists"):
        create_course(instructor_one, {"course_code": "MATH-102", "title": "CALCULUS I"})


def test_admin_create_course_owner_override(
    app: Flask,
    admin_user: User,
    instructor_one: User,
    student_user: User,
) -> None:
    """Test admin creating course with owner assignment."""
    # Admin assigns to instructor_one
    course = create_course(
        admin_user,
        {
            "course_code": "ENG-101",
            "title": "English Literature",
            "owner_instructor_id": instructor_one.id,
        },
    )
    assert course.owner_instructor_id == instructor_one.id

    # Admin assigning to non-existent user
    with pytest.raises(UserNotFoundError):
        create_course(
            admin_user,
            {
                "course_code": "ENG-102",
                "title": "English Literature II",
                "owner_instructor_id": 999999,
            },
        )

    # Admin assigning to student (lacks INSTRUCTOR role)
    with pytest.raises(InvalidRoleAssignmentError):
        create_course(
            admin_user,
            {
                "course_code": "ENG-103",
                "title": "English Literature III",
                "owner_instructor_id": student_user.id,
            },
        )


def test_update_course_metadata_and_mass_assignment(
    app: Flask,
    instructor_one: User,
    instructor_two: User,
) -> None:
    """Test updating course metadata, validating uniqueness, and mass assignment defense."""
    course = create_course(instructor_one, {"course_code": "HIST-101", "title": "World History"})

    # Updating metadata by owner
    updated = update_course(
        instructor_one,
        course.id,
        {
            "title": "Modern World History",
            "description": "1900 to present",
            "category": "History",
            "difficulty": "INTERMEDIATE",
            "capacity": 100,
            # Attempt mass-assignment of privileged fields
            "course_code": "HACKED-CODE",
            "status": "PUBLISHED",
            "owner_instructor_id": instructor_two.id,
        },
    )
    assert updated.title == "Modern World History"
    assert updated.description == "1900 to present"
    assert updated.difficulty == "INTERMEDIATE"
    assert updated.capacity == 100
    # Privileged fields MUST NOT have changed
    assert updated.course_code == "HIST-101"
    assert updated.status == "DRAFT"
    assert updated.owner_instructor_id == instructor_one.id


def test_course_thumbnail_accepts_only_clean_image_from_same_course(
    app: Flask, instructor_one: User
) -> None:
    course = create_course(instructor_one, {"course_code": "IMG-101", "title": "Image Course"})
    other = create_course(instructor_one, {"course_code": "IMG-102", "title": "Other Course"})
    image = store_file_stream(
        instructor_one,
        course.id,
        io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"a" * 64),
        "cover.png",
        "image/png",
        asset_type="COURSE_IMAGE",
        session=db.session,
    )
    updated = update_course(
        instructor_one,
        course.id,
        {"thumbnail_file_asset_id": str(image.public_id)},
        session=db.session,
    )
    assert updated.thumbnail_file_asset_id == image.id
    for scan in list(image.current_revision.scan_results):
        db.session.delete(scan)
    db.session.commit()
    assert get_course_thumbnail_asset(updated) is None
    with pytest.raises(CourseValidationError):
        update_course(
            instructor_one,
            course.id,
            {"thumbnail_file_asset_id": str(image.public_id)},
            session=db.session,
        )
    with pytest.raises(CourseValidationError):
        update_course(
            instructor_one,
            other.id,
            {"thumbnail_file_asset_id": str(image.public_id)},
            session=db.session,
        )


def test_get_course_detail_visibility(
    app: Flask,
    instructor_one: User,
    instructor_two: User,
    student_user: User,
    admin_user: User,
) -> None:
    """Test get_course_detail adhering to visibility rules (03_RESOURCE_AUTHORIZATION_RULES.md)."""
    course = create_course(instructor_one, {"course_code": "PHY-101", "title": "Physics I"})

    # 1. DRAFT status: owner and admin can view; other instructor and student denied
    assert get_course_detail(instructor_one, course.id).id == course.id
    assert get_course_detail(admin_user, course.id).id == course.id

    with pytest.raises(ForbiddenError):
        get_course_detail(instructor_two, course.id)

    with pytest.raises(ForbiddenError):
        get_course_detail(student_user, course.id)

    with pytest.raises(ForbiddenError):
        get_course_detail(None, course.id)

    # 2. Transition to PUBLISHED: everyone can view
    change_course_status(instructor_one, course.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin_user, course.id, "APPROVED")
    change_course_status(instructor_one, course.id, "PUBLISHED")

    assert get_course_detail(instructor_one, course.id).id == course.id
    assert get_course_detail(instructor_two, course.id).id == course.id
    assert get_course_detail(student_user, course.id).id == course.id
    assert get_course_detail(None, course.id).id == course.id


def test_course_state_machine_transitions(
    app: Flask,
    instructor_one: User,
    instructor_two: User,
    admin_user: User,
) -> None:
    """Test full valid lifecycle:
    DRAFT -> SUBMITTED -> APPROVED -> PUBLISHED -> ARCHIVED -> TRASH.
    """
    course = create_course(instructor_one, {"course_code": "CHEM-101", "title": "Chemistry I"})
    assert course.status == "DRAFT"

    # 1. DRAFT -> SUBMITTED_FOR_REVIEW
    change_course_status(instructor_one, course.id, "SUBMITTED_FOR_REVIEW")
    assert course.status == "SUBMITTED_FOR_REVIEW"

    # 2. SUBMITTED_FOR_REVIEW -> APPROVED (Admin only!)
    with pytest.raises(ForbiddenError, match="Only administrators can approve"):
        change_course_status(instructor_one, course.id, "APPROVED")

    change_course_status(
        admin_user,
        course.id,
        "APPROVED",
        reason="Content meets high quality standards.",
    )
    assert course.status == "APPROVED"
    assert course.approved_by_user_id == admin_user.id
    assert course.approved_at is not None

    # Check AuditEvent for approval
    sess: Session = db.session
    audit_approved = (
        sess.query(AuditEvent).filter_by(action="COURSE_APPROVED", target_id=course.id).first()
    )
    assert audit_approved is not None
    assert audit_approved.performed_as_admin is True

    # 3. APPROVED -> PUBLISHED
    change_course_status(instructor_one, course.id, "PUBLISHED")
    assert course.status == "PUBLISHED"
    assert course.published_at is not None

    audit_pub = (
        sess.query(AuditEvent).filter_by(action="COURSE_PUBLISHED", target_id=course.id).first()
    )
    assert audit_pub is not None

    # 4. PUBLISHED -> ARCHIVED
    change_course_status(instructor_one, course.id, "ARCHIVED", reason="Term ended")
    assert course.status == "ARCHIVED"

    # 5. ARCHIVED -> PUBLISHED (Restore)
    change_course_status(instructor_one, course.id, "PUBLISHED")
    assert course.status == "PUBLISHED"

    # 6. ARCHIVED -> TRASH
    change_course_status(instructor_one, course.id, "ARCHIVED")
    trash_course(instructor_one, course.id, reason="Obsolete syllabus")
    assert course.status == "TRASH"
    assert course.deleted_at is not None
    assert course.deleted_by_user_id == instructor_one.id

    # 7. TRASH -> ARCHIVED (Restore from trash requires Admin)
    with pytest.raises(ForbiddenError, match="Only administrators can restore"):
        change_course_status(instructor_one, course.id, "ARCHIVED")

    change_course_status(admin_user, course.id, "ARCHIVED", reason="Admin restoring course")
    assert course.status == "ARCHIVED"
    assert course.deleted_at is None
    assert course.deleted_by_user_id is None


def test_course_lifecycle_notifications_use_audit_scoped_event_keys(
    app: Flask,
    instructor_one: User,
    admin_user: User,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Each course lifecycle notification is keyed by its durable audit transition."""
    captured: list[dict[str, object]] = []

    def capture_notification(**kwargs: object) -> tuple[None, None]:
        captured.append(kwargs)
        return None, None

    monkeypatch.setattr(
        "pwd301.services.notification_service.dispatch_notification",
        capture_notification,
    )

    course = create_course(
        instructor_one,
        {"course_code": "NOTIF-KEY-101", "title": "Notification Key Course"},
    )

    change_course_status(instructor_one, course.id, "SUBMITTED_FOR_REVIEW")
    submission_call = next(
        item for item in captured if item["event_type"] == "COURSE_SUBMITTED_FOR_REVIEW"
    )
    submission_audit = (
        db.session.query(AuditEvent)
        .filter_by(action="COURSE_SUBMITTED_FOR_REVIEW", target_id=course.id)
        .order_by(AuditEvent.id.desc())
        .first()
    )
    assert submission_audit is not None
    assert submission_call["event_key"] == uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"pwd301:course-audit:{submission_audit.id}:COURSE_SUBMITTED_FOR_REVIEW:{admin_user.id}",
    )

    captured.clear()
    change_course_status(
        admin_user,
        course.id,
        "APPROVED",
        reason="Content meets the documented review standard.",
    )
    approval_call = next(item for item in captured if item["event_type"] == "COURSE_APPROVED")
    approval_audit = (
        db.session.query(AuditEvent)
        .filter_by(action="COURSE_APPROVED", target_id=course.id)
        .order_by(AuditEvent.id.desc())
        .first()
    )
    assert approval_audit is not None
    assert approval_call["event_key"] == uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"pwd301:course-audit:{approval_audit.id}:COURSE_APPROVED:{instructor_one.id}",
    )

    change_course_status(instructor_one, course.id, "PUBLISHED")
    change_course_status(instructor_one, course.id, "SUBMITTED_FOR_REVIEW")
    captured.clear()
    change_course_status(
        admin_user,
        course.id,
        "DRAFT",
        reason="Please add the missing assessment rubric details.",
    )
    rejection_call = next(item for item in captured if item["event_type"] == "COURSE_REJECTED")
    rejection_audit = (
        db.session.query(AuditEvent)
        .filter_by(action="COURSE_REJECTED", target_id=course.id)
        .order_by(AuditEvent.id.desc())
        .first()
    )
    assert rejection_audit is not None
    assert rejection_call["event_key"] == uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"pwd301:course-audit:{rejection_audit.id}:COURSE_REJECTED:{instructor_one.id}",
    )
    assert all(isinstance(item["event_key"], uuid.UUID) for item in captured)


def test_illegal_state_machine_transitions(
    app: Flask,
    instructor_one: User,
    admin_user: User,
) -> None:
    """Test that violating the state machine transition graph raises CourseStateViolationError."""
    course = create_course(instructor_one, {"course_code": "ART-101", "title": "Fine Arts"})

    # DRAFT cannot jump directly to PUBLISHED
    with pytest.raises(
        CourseStateViolationError,
        match="Cannot transition course from 'DRAFT' to 'PUBLISHED'",
    ):
        change_course_status(instructor_one, course.id, "PUBLISHED")

    # DRAFT cannot jump directly to APPROVED
    with pytest.raises(
        CourseStateViolationError,
        match="Cannot transition course from 'DRAFT' to 'APPROVED'",
    ):
        change_course_status(admin_user, course.id, "APPROVED")

    # DRAFT cannot jump directly to ARCHIVED
    with pytest.raises(CourseStateViolationError):
        change_course_status(instructor_one, course.id, "ARCHIVED")


def test_prerequisite_dependency_blocks_archive_and_trash(
    app: Flask,
    instructor_one: User,
    admin_user: User,
) -> None:
    """Test COURSE-005, COURSE-006: Course required as prerequisite cannot be archived/deleted."""
    sess: Session = db.session
    course_base = create_course(instructor_one, {"course_code": "CS-50", "title": "Basics of CS"})
    course_adv = create_course(instructor_one, {"course_code": "CS-150", "title": "Advanced CS"})

    # Setup base as prerequisite for advanced
    prereq = CoursePrerequisite(
        course_id=course_adv.id,
        prerequisite_course_id=course_base.id,
        created_by_user_id=instructor_one.id,
    )
    sess.add(prereq)
    sess.commit()

    # Publish course_base
    change_course_status(instructor_one, course_base.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin_user, course_base.id, "APPROVED")
    change_course_status(instructor_one, course_base.id, "PUBLISHED")

    # Attempting to archive course_base while course_adv is active (DRAFT) must be blocked
    with pytest.raises(
        CourseDependencyError,
        match="it is required as a prerequisite by active course",
    ):
        change_course_status(instructor_one, course_base.id, "ARCHIVED")

    # For a DRAFT course required as prerequisite, attempting to trash it is also blocked
    course_draft_base = create_course(
        instructor_one,
        {"course_code": "CS-60", "title": "Intro to Data"},
    )
    prereq2 = CoursePrerequisite(
        course_id=course_adv.id,
        prerequisite_course_id=course_draft_base.id,
        created_by_user_id=instructor_one.id,
    )
    sess.add(prereq2)
    sess.commit()

    with pytest.raises(
        CourseDependencyError,
        match="it is required as a prerequisite by active course",
    ):
        trash_course(instructor_one, course_draft_base.id)

    # Now trash the dependent course_adv (DRAFT -> TRASH)
    trash_course(instructor_one, course_adv.id)

    # Now archiving course_base succeeds because no active course depends on it
    change_course_status(instructor_one, course_base.id, "ARCHIVED")
    assert course_base.status == "ARCHIVED"

    # And trashing course_draft_base now succeeds
    trash_course(instructor_one, course_draft_base.id)
    assert course_draft_base.status == "TRASH"


def test_reassign_course_owner(
    app: Flask,
    instructor_one: User,
    instructor_two: User,
    student_user: User,
    admin_user: User,
) -> None:
    """Test admin ownership reassignment and append-only audit logging."""
    course = create_course(instructor_one, {"course_code": "SOC-101", "title": "Sociology"})

    # Non-admin cannot reassign owner
    with pytest.raises(ForbiddenError, match="Only administrators can reassign"):
        reassign_course_owner(instructor_one, course.id, instructor_two.id)

    # Reassigning to user without INSTRUCTOR role fails
    with pytest.raises(InvalidRoleAssignmentError):
        reassign_course_owner(admin_user, course.id, student_user.id)

    # Successful reassignment to instructor_two
    reassigned = reassign_course_owner(
        admin_actor=admin_user,
        course_id=course.id,
        new_instructor_id=instructor_two.id,
        reason="Instructor One is taking a sabbatical leave.",
    )
    assert reassigned.owner_instructor_id == instructor_two.id

    # Verify AuditEvent
    sess: Session = db.session
    audit = (
        sess.query(AuditEvent)
        .filter_by(action="COURSE_OWNER_REASSIGNED", target_id=course.id)
        .first()
    )
    assert audit is not None
    assert audit.actor_user_id == admin_user.id
    assert audit.performed_as_admin is True
    assert audit.reason == "Instructor One is taking a sabbatical leave."
    assert json.loads(audit.before_json)["owner_instructor_id"] == instructor_one.id
    assert json.loads(audit.after_json)["owner_instructor_id"] == instructor_two.id

    # Reassignment to None (unassigned course) is allowed
    reassigned_none = reassign_course_owner(
        admin_actor=admin_user,
        course_id=course.id,
        new_instructor_id=None,
        reason="Departed instructor, pending assignment.",
    )
    assert reassigned_none.owner_instructor_id is None


def test_reassign_course_owner_notifications_use_recipient_scoped_audit_keys(
    app: Flask,
    instructor_one: User,
    instructor_two: User,
    admin_user: User,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Owner reassignment fan-out uses one stable key per recipient."""
    captured: list[dict[str, object]] = []

    def capture_notification(**kwargs: object) -> tuple[None, None]:
        captured.append(kwargs)
        return None, None

    monkeypatch.setattr(
        "pwd301.services.notification_service.dispatch_notification",
        capture_notification,
    )

    course = create_course(
        instructor_one,
        {"course_code": "OWNER-KEY-101", "title": "Owner Key Course"},
    )
    reassign_course_owner(
        admin_actor=admin_user,
        course_id=course.id,
        new_instructor_id=instructor_two.id,
        reason="Instructor One is taking a sabbatical leave.",
    )

    assert len(captured) == 2
    audit = (
        db.session.query(AuditEvent)
        .filter_by(action="COURSE_OWNER_REASSIGNED", target_id=course.id)
        .order_by(AuditEvent.id.desc())
        .first()
    )
    assert audit is not None
    expected_keys = {
        instructor_one.id: uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"pwd301:course-audit:{audit.id}:COURSE_OWNER_REASSIGNED:{instructor_one.id}",
        ),
        instructor_two.id: uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"pwd301:course-audit:{audit.id}:COURSE_OWNER_REASSIGNED:{instructor_two.id}",
        ),
    }
    captured_by_recipient = {item["recipient_user"]: item for item in captured}
    assert captured_by_recipient[instructor_one.id]["event_key"] == expected_keys[instructor_one.id]
    assert captured_by_recipient[instructor_two.id]["event_key"] == expected_keys[instructor_two.id]
    assert expected_keys[instructor_one.id] != expected_keys[instructor_two.id]


def test_list_courses_pagination_and_filtering(
    app: Flask,
    instructor_one: User,
    instructor_two: User,
    student_user: User,
    admin_user: User,
) -> None:
    c1 = create_course(
        instructor_one,
        {"course_code": "BIO-101", "title": "General Biology", "category": "Bio"},
    )
    c2 = create_course(
        instructor_one,
        {"course_code": "BIO-201", "title": "Cell Biology", "category": "Bio"},
    )
    create_course(
        instructor_two,
        {"course_code": "CHEM-201", "title": "Organic Chemistry", "category": "Chem"},
    )

    # Publish c1
    change_course_status(instructor_one, c1.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin_user, c1.id, "APPROVED")
    change_course_status(instructor_one, c1.id, "PUBLISHED")

    # Student only sees published c1
    courses, total = list_courses(actor=student_user)
    assert total == 1
    assert courses[0].id == c1.id

    # Instructor One sees published c1 + their draft c2 (total 2)
    courses_i1, total_i1 = list_courses(actor=instructor_one)
    assert total_i1 == 2
    assert {c.id for c in courses_i1} == {c1.id, c2.id}

    # Admin sees all 3
    courses_admin, total_admin = list_courses(actor=admin_user)
    assert total_admin == 3

    # Filter by category
    courses_bio, total_bio = list_courses(actor=admin_user, category="Bio")
    assert total_bio == 2


def test_course_soft_delete_and_reuse_code(
    app: Flask,
    instructor_one: User,
) -> None:
    """Verify that a soft-deleted course's code can be reused by a new course (AC-01 / Item 3.2)."""
    course1 = create_course(
        instructor_one,
        {"course_code": "CS-101", "title": "Intro to CS 1"},
    )
    assert course1.status == "DRAFT"

    # Creating another active course with CS-101 must fail
    with pytest.raises(CourseAlreadyExistsError, match="already exists"):
        create_course(
            instructor_one,
            {"course_code": "cs-101", "title": "Another CS 1"},
        )

    # Soft-delete the course to TRASH
    trashed = trash_course(
        actor=instructor_one,
        course_id=course1.id,
        reason="Retiring old syllabus",
    )
    assert trashed.deleted_at is not None
    assert trashed.status == "TRASH"

    # Creating a new course with identical code 'CS-101' MUST SUCCEED because old one is deleted
    course2 = create_course(
        instructor_one,
        {"course_code": "CS-101", "title": "New Syllabus CS 1"},
    )
    assert course2.id != course1.id
    assert course2.course_code == "CS-101"
    assert course2.deleted_at is None


def test_audit_admin_course_edit_requires_reason_and_notifies_owner(
    app: Flask,
    instructor_one: User,
    admin_user: User,
) -> None:
    """Direct Admin edits of Instructor-owned courses are reasoned and notified."""
    course = create_course(
        instructor_one,
        {"course_code": "ADMIN-EDIT-1", "title": "Owned Course", "description": "Original"},
    )
    course.status = "PUBLISHED"
    db.session.commit()

    with pytest.raises(CourseValidationError, match="reason"):
        update_course(admin_user, course.id, {"description": "Unreasoned"})

    db.session.refresh(course)
    assert course.description == "Original"
    update_course(
        admin_user,
        course.id,
        {"description": "Reasoned", "reason": "Correct an approved catalog description"},
    )
    audit = (
        db.session.query(AuditEvent)
        .filter(AuditEvent.target_id == course.id, AuditEvent.action == "COURSE_ADMIN_EDIT")
        .one()
    )
    assert audit.reason == "Correct an approved catalog description"
    assert audit.performed_as_admin is True
    assert (
        db.session.query(Notification)
        .filter(Notification.recipient_user_id == instructor_one.id)
        .count()
        >= 1
    )
    expected_key = uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"pwd301:course-audit:{audit.id}:{audit.action}:{instructor_one.id}",
    )
    assert (
        db.session.query(NotificationEvent)
        .filter(NotificationEvent.event_key == expected_key)
        .one()
        .event_type
        == "SYSTEM_ADMIN_INTERVENTION"
    )


def test_audit_non_owner_cannot_repeat_course_transition(
    app: Flask,
    instructor_one: User,
    instructor_two: User,
    admin_user: User,
) -> None:
    """Idempotent state transitions still authorize the concrete course first."""
    course = create_course(
        instructor_one,
        {"course_code": "NOOP-AUTH-1", "title": "Private Course"},
    )
    change_course_status(instructor_one, course.id, "SUBMITTED_FOR_REVIEW")

    with pytest.raises(ForbiddenError):
        change_course_status(instructor_two, course.id, "SUBMITTED_FOR_REVIEW")
