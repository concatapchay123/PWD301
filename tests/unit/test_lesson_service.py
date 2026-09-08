"""Unit tests for Lesson Service, Reordering, Positioning, and Completion Tracking."""

from __future__ import annotations

import json

import pytest
from flask import Flask

from pwd301.extensions import db
from pwd301.models.course import Course, Enrollment, EnrollmentPeriod, Lesson
from pwd301.models.identity import Role, User
from pwd301.models.notification_audit import AuditEvent
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.exceptions import (
    ForbiddenError,
    LessonPositionConflictError,
    LessonStateViolationError,
    LessonValidationError,
)
from pwd301.services.lesson_service import (
    change_lesson_status,
    create_lesson,
    get_lesson_detail,
    record_lesson_progress,
    reorder_lessons,
    trash_lesson,
    update_lesson,
)
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
    """Ensure canonical roles exist in test database."""
    sess = db.session
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
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Instructor User."""
    u = register_user("les_instructor@example.com", "Password@123", "Lesson Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Admin User."""
    u = register_user("les_admin@example.com", "Password@123", "Lesson Admin")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Student User."""
    return register_user("les_student@example.com", "Password@123", "Lesson Student")


@pytest.fixture
def course_sample(app: Flask, instructor_user: User) -> Course:
    """Create Course owned by instructor_user."""
    return create_course(
        instructor_user,
        {
            "course_code": "LES-101",
            "title": "Lesson Service Course",
            "description": "Course for testing lesson management.",
        },
    )


def test_create_lesson_auto_increment_position(
    app: Flask,
    instructor_user: User,
    course_sample: Course,
) -> None:
    """Test creating lessons auto-increments contiguous position starting from 1."""
    l1 = create_lesson(
        instructor_user,
        course_sample.id,
        {
            "title": "Lesson 1: Introduction",
            "markdown_content": "# Intro to course",
        },
    )
    assert l1.id is not None
    assert l1.position == 1
    assert l1.status == "DRAFT"
    assert l1.minimum_completion_seconds == 30
    assert float(l1.viewed_fraction_required) == 0.8

    l2 = create_lesson(
        instructor_user,
        course_sample.id,
        {
            "title": "Lesson 2: Core Concepts",
            "markdown_content": "# Core Concepts",
        },
    )
    assert l2.position == 2

    l3 = create_lesson(
        instructor_user,
        course_sample.id,
        {
            "title": "Lesson 3: Advanced Topics",
            "markdown_content": "# Advanced Topics",
        },
    )
    assert l3.position == 3


def test_create_lesson_with_specified_position_and_shift(
    app: Flask,
    instructor_user: User,
    course_sample: Course,
) -> None:
    """Test creating lesson at specific position shifts subsequent lessons cleanly."""
    create_lesson(
        instructor_user,
        course_sample.id,
        {"title": "First", "markdown_content": "# 1"},
    )
    create_lesson(
        instructor_user,
        course_sample.id,
        {"title": "Second", "markdown_content": "# 2"},
    )

    # Insert a new lesson at position 1
    inserted = create_lesson(
        instructor_user,
        course_sample.id,
        {"title": "Zero (inserted at 1)", "markdown_content": "# 0", "position": 1},
    )
    assert inserted.position == 1

    # Verify positions of all lessons are 1, 2, 3
    sess = db.session
    lessons = (
        sess.query(Lesson)
        .filter(Lesson.course_id == course_sample.id, Lesson.deleted_at.is_(None))
        .order_by(Lesson.position.asc())
        .all()
    )
    assert len(lessons) == 3
    assert [les.position for les in lessons] == [1, 2, 3]
    assert [les.title for les in lessons] == ["Zero (inserted at 1)", "First", "Second"]


def test_create_lesson_validation_failures(
    app: Flask,
    instructor_user: User,
    course_sample: Course,
) -> None:
    """Test validation constraints on lesson creation."""
    # Empty title
    with pytest.raises(LessonValidationError, match="title is required"):
        create_lesson(
            instructor_user,
            course_sample.id,
            {"title": "", "markdown_content": "Valid"},
        )

    # Empty markdown
    with pytest.raises(LessonValidationError, match="markdown_content is required"):
        create_lesson(
            instructor_user,
            course_sample.id,
            {"title": "Valid Title", "markdown_content": "   "},
        )

    # Negative duration
    with pytest.raises(LessonValidationError, match="greater than zero"):
        create_lesson(
            instructor_user,
            course_sample.id,
            {
                "title": "Title",
                "markdown_content": "Content",
                "estimated_duration_minutes": -5,
            },
        )

    # Invalid fraction > 1.0
    with pytest.raises(LessonValidationError, match="between 0.0 and 1.0"):
        create_lesson(
            instructor_user,
            course_sample.id,
            {
                "title": "Title",
                "markdown_content": "Content",
                "viewed_fraction_required": 1.5,
            },
        )

    # Invalid fraction < 0.0
    with pytest.raises(LessonValidationError, match="between 0.0 and 1.0"):
        create_lesson(
            instructor_user,
            course_sample.id,
            {
                "title": "Title",
                "markdown_content": "Content",
                "viewed_fraction_required": -0.1,
            },
        )


def test_create_lesson_blocked_on_archived_or_trashed_course(
    app: Flask,
    instructor_user: User,
    course_sample: Course,
) -> None:
    """Test cannot add lessons to archived course."""
    # Transition to ARCHIVED via state machine
    admin = register_user("arch_admin@example.com", "Password@123", "Arch Admin")
    admin = assign_role_to_user(admin.id, "ADMIN")

    change_course_status(instructor_user, course_sample.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin, course_sample.id, "APPROVED")
    change_course_status(instructor_user, course_sample.id, "PUBLISHED")
    change_course_status(instructor_user, course_sample.id, "ARCHIVED")

    with pytest.raises(LessonStateViolationError, match="archived or trashed"):
        create_lesson(
            instructor_user,
            course_sample.id,
            {"title": "Blocked Lesson", "markdown_content": "Blocked"},
        )


def test_update_lesson_whitelisted_fields(
    app: Flask,
    instructor_user: User,
    course_sample: Course,
) -> None:
    """Test updating lesson metadata with whitelisted fields."""
    lesson = create_lesson(
        instructor_user,
        course_sample.id,
        {"title": "Original Title", "markdown_content": "# Original Content"},
    )

    updated = update_lesson(
        instructor_user,
        lesson.id,
        {
            "title": "Updated Title",
            "summary": "Short summary",
            "markdown_content": "# Updated Content",
            "estimated_duration_minutes": 45,
            "minimum_completion_seconds": 60,
            "viewed_fraction_required": 0.9000,
        },
    )

    assert updated.title == "Updated Title"
    assert updated.summary == "Short summary"
    assert updated.markdown_content == "# Updated Content"
    assert updated.estimated_duration_minutes == 45
    assert updated.minimum_completion_seconds == 60
    assert float(updated.viewed_fraction_required) == 0.9


def test_update_lesson_disallow_position_mutation(
    app: Flask,
    instructor_user: User,
    course_sample: Course,
) -> None:
    """Test updating position via update_lesson is rejected."""
    lesson = create_lesson(
        instructor_user,
        course_sample.id,
        {"title": "Lesson 1", "markdown_content": "# 1"},
    )

    with pytest.raises(LessonValidationError, match="reorder_lessons"):
        update_lesson(
            instructor_user,
            lesson.id,
            {"position": 5},
        )


def test_reorder_lessons_success(
    app: Flask,
    instructor_user: User,
    course_sample: Course,
) -> None:
    """Test 2-phase reordering maintains contiguous 1..N order without constraint collision."""
    l1 = create_lesson(instructor_user, course_sample.id, {"title": "L1", "markdown_content": "#1"})
    l2 = create_lesson(instructor_user, course_sample.id, {"title": "L2", "markdown_content": "#2"})
    l3 = create_lesson(instructor_user, course_sample.id, {"title": "L3", "markdown_content": "#3"})

    # Reverse order: L3, L2, L1
    reordered = reorder_lessons(instructor_user, course_sample.id, [l3.id, l2.id, l1.id])
    assert len(reordered) == 3
    assert reordered[0].id == l3.id
    assert reordered[0].position == 1
    assert reordered[1].id == l2.id
    assert reordered[1].position == 2
    assert reordered[2].id == l1.id
    assert reordered[2].position == 3


def test_reorder_lessons_integrity_failures(
    app: Flask,
    instructor_user: User,
    course_sample: Course,
) -> None:
    """Test reordering fails when IDs list is invalid, incomplete, or contains duplicates."""
    l1 = create_lesson(instructor_user, course_sample.id, {"title": "L1", "markdown_content": "#1"})
    create_lesson(instructor_user, course_sample.id, {"title": "L2", "markdown_content": "#2"})

    # Incomplete list (missing second lesson)
    with pytest.raises(LessonPositionConflictError):
        reorder_lessons(instructor_user, course_sample.id, [l1.id])

    # Duplicate IDs
    with pytest.raises(LessonPositionConflictError, match="Duplicate"):
        reorder_lessons(instructor_user, course_sample.id, [l1.id, l1.id])

    # Foreign ID
    with pytest.raises(LessonPositionConflictError, match="not an active lesson"):
        reorder_lessons(instructor_user, course_sample.id, [l1.id, 999999])


def test_trash_lesson_and_recompact_positions(
    app: Flask,
    instructor_user: User,
    course_sample: Course,
) -> None:
    """Test soft-delete puts lesson in TRASH and compacts remaining positions."""
    l1 = create_lesson(instructor_user, course_sample.id, {"title": "L1", "markdown_content": "#1"})
    l2 = create_lesson(instructor_user, course_sample.id, {"title": "L2", "markdown_content": "#2"})
    l3 = create_lesson(instructor_user, course_sample.id, {"title": "L3", "markdown_content": "#3"})

    trashed = trash_lesson(instructor_user, l2.id, reason="Content obsolete")
    assert trashed.status == "TRASH"
    assert trashed.deleted_at is not None
    assert trashed.deleted_by_user_id == instructor_user.id

    sess = db.session
    active = (
        sess.query(Lesson)
        .filter(Lesson.course_id == course_sample.id, Lesson.deleted_at.is_(None))
        .order_by(Lesson.position.asc())
        .all()
    )
    assert len(active) == 2
    assert active[0].id == l1.id
    assert active[0].position == 1
    assert active[1].id == l3.id
    assert active[1].position == 2


def test_change_lesson_status(
    app: Flask,
    instructor_user: User,
    course_sample: Course,
) -> None:
    """Test transitions between DRAFT, PUBLISHED, and HIDDEN."""
    lesson = create_lesson(
        instructor_user,
        course_sample.id,
        {"title": "Status Lesson", "markdown_content": "# Content"},
    )
    assert lesson.status == "DRAFT"
    assert lesson.published_at is None

    # Publish
    published = change_lesson_status(instructor_user, lesson.id, "PUBLISHED")
    assert published.status == "PUBLISHED"
    assert published.published_at is not None

    # Hide
    hidden = change_lesson_status(instructor_user, lesson.id, "HIDDEN")
    assert hidden.status == "HIDDEN"

    # Draft
    draft = change_lesson_status(instructor_user, lesson.id, "DRAFT")
    assert draft.status == "DRAFT"


def test_get_lesson_detail_access_rules(
    app: Flask,
    instructor_user: User,
    student_user: User,
    course_sample: Course,
) -> None:
    """Test get_lesson_detail authorization for instructor and student."""
    sess = db.session
    lesson = create_lesson(
        instructor_user,
        course_sample.id,
        {"title": "Draft Lesson", "markdown_content": "# Secret"},
    )

    # 1. Instructor can read DRAFT lesson
    assert get_lesson_detail(instructor_user, lesson.id).id == lesson.id

    # 2. Student cannot read DRAFT lesson
    with pytest.raises(ForbiddenError):
        get_lesson_detail(student_user, lesson.id)

    # 3. Publish course and lesson
    admin = register_user("perm_admin@example.com", "Password@123", "Perm Admin")
    admin = assign_role_to_user(admin.id, "ADMIN")
    change_course_status(instructor_user, course_sample.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin, course_sample.id, "APPROVED")
    change_course_status(instructor_user, course_sample.id, "PUBLISHED")
    change_lesson_status(instructor_user, lesson.id, "PUBLISHED")

    # 4. Student not enrolled cannot view lesson
    with pytest.raises(ForbiddenError, match="Active course enrollment required"):
        get_lesson_detail(student_user, lesson.id)

    # 5. Enroll student
    enrollment = Enrollment(
        student_user_id=student_user.id,
        course_id=course_sample.id,
        status="ACTIVE",
    )
    sess.add(enrollment)
    sess.flush()
    period = EnrollmentPeriod(
        enrollment_id=enrollment.id,
        period_no=1,
        status="ACTIVE",
    )
    sess.add(period)
    sess.flush()
    enrollment.current_period_id = period.id
    sess.commit()

    # Now enrolled student can access
    detail = get_lesson_detail(student_user, lesson.id)
    assert detail.id == lesson.id


def test_record_lesson_progress_monotonic_completion(
    app: Flask,
    instructor_user: User,
    student_user: User,
    course_sample: Course,
) -> None:
    """Test Algorithm 02: monotonic progress tracking and idempotent completion."""
    sess = db.session

    # Publish course and lesson
    admin = register_user("prog_admin@example.com", "Password@123", "Prog Admin")
    admin = assign_role_to_user(admin.id, "ADMIN")
    change_course_status(instructor_user, course_sample.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin, course_sample.id, "APPROVED")
    change_course_status(instructor_user, course_sample.id, "PUBLISHED")

    lesson = create_lesson(
        instructor_user,
        course_sample.id,
        {
            "title": "Progress Lesson",
            "markdown_content": "# Content",
            "status": "PUBLISHED",
            "minimum_completion_seconds": 30,
            "viewed_fraction_required": 0.8000,
        },
    )

    # Enroll student
    enrollment = Enrollment(
        student_user_id=student_user.id,
        course_id=course_sample.id,
        status="ACTIVE",
    )
    sess.add(enrollment)
    sess.flush()
    period = EnrollmentPeriod(
        enrollment_id=enrollment.id,
        period_no=1,
        status="ACTIVE",
    )
    sess.add(period)
    sess.flush()
    enrollment.current_period_id = period.id
    sess.commit()

    # 1. First ping: 15s, 0.5 view fraction -> Not completed yet
    p1 = record_lesson_progress(
        actor=student_user,
        lesson_id=lesson.id,
        seconds_increment=15,
        view_fraction=0.50,
    )
    assert p1.seconds_spent == 15
    assert float(p1.max_view_fraction) == 0.50
    assert p1.completed_at is None

    # 2. Second ping: 20s, 0.85 view fraction -> Total 35s >= 30 and 0.85 >= 0.8 -> COMPLETED
    p2 = record_lesson_progress(
        actor=student_user,
        lesson_id=lesson.id,
        seconds_increment=20,
        view_fraction=0.85,
    )
    assert p2.seconds_spent == 35
    assert float(p2.max_view_fraction) == 0.85
    assert p2.completed_at is not None
    assert p2.completion_rule_snapshot_json is not None
    snapshot = json.loads(p2.completion_rule_snapshot_json)
    assert snapshot["minimum_completion_seconds"] == 30
    assert snapshot["viewed_fraction_required"] == 0.8

    # Verify Enrollment cache was updated
    sess.refresh(enrollment)
    assert float(enrollment.current_progress_percent) == 100.0

    # 3. Third ping: 10s, 0.90 view fraction -> Idempotent, completed_at not changed
    completed_time = p2.completed_at
    p3 = record_lesson_progress(
        actor=student_user,
        lesson_id=lesson.id,
        seconds_increment=10,
        view_fraction=0.90,
    )
    assert p3.seconds_spent == 45
    assert float(p3.max_view_fraction) == 0.90
    assert p3.completed_at == completed_time


def test_record_lesson_progress_anti_tampering(
    app: Flask,
    instructor_user: User,
    student_user: User,
    course_sample: Course,
) -> None:
    """Test anti-tampering bounds on ping increments."""
    lesson = create_lesson(
        instructor_user,
        course_sample.id,
        {
            "title": "Tamper Lesson",
            "markdown_content": "# Content",
            "status": "PUBLISHED",
        },
    )

    # Ping > 60 seconds
    with pytest.raises(LessonValidationError, match="between 1 and 60"):
        record_lesson_progress(
            actor=student_user,
            lesson_id=lesson.id,
            seconds_increment=120,
            view_fraction=0.5,
        )

    # Ping <= 0 seconds
    with pytest.raises(LessonValidationError, match="between 1 and 60"):
        record_lesson_progress(
            actor=student_user,
            lesson_id=lesson.id,
            seconds_increment=0,
            view_fraction=0.5,
        )

    # View fraction > 1.0
    with pytest.raises(LessonValidationError, match="between 0.0 and 1.0"):
        record_lesson_progress(
            actor=student_user,
            lesson_id=lesson.id,
            seconds_increment=10,
            view_fraction=1.5,
        )


def test_audit_event_logged_on_published_course_lesson_changes(
    app: Flask,
    instructor_user: User,
    course_sample: Course,
) -> None:
    """Test AuditEvents are recorded on published courses for lesson mutations."""
    sess = db.session
    admin = register_user("aud_admin@example.com", "Password@123", "Aud Admin")
    admin = assign_role_to_user(admin.id, "ADMIN")
    change_course_status(instructor_user, course_sample.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin, course_sample.id, "APPROVED")
    change_course_status(instructor_user, course_sample.id, "PUBLISHED")

    # 1. Create lesson in published course -> audit logged
    lesson = create_lesson(
        instructor_user,
        course_sample.id,
        {"title": "Audited Lesson", "markdown_content": "# Audited"},
    )
    audit1 = (
        sess.query(AuditEvent)
        .filter(AuditEvent.action == "LESSON_CREATED", AuditEvent.target_id == lesson.id)
        .first()
    )
    assert audit1 is not None

    # 2. Update lesson -> audit logged
    update_lesson(instructor_user, lesson.id, {"title": "Updated Audit Title"})
    audit2 = (
        sess.query(AuditEvent)
        .filter(AuditEvent.action == "LESSON_UPDATED", AuditEvent.target_id == lesson.id)
        .first()
    )
    assert audit2 is not None

    # 3. Trash lesson -> audit logged
    trash_lesson(instructor_user, lesson.id, reason="Testing audit")
    audit3 = (
        sess.query(AuditEvent)
        .filter(AuditEvent.action == "LESSON_TRASHED", AuditEvent.target_id == lesson.id)
        .first()
    )
    assert audit3 is not None
