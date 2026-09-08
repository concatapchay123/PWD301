"""Unit tests for Student Enrollment Service, Capacity, Prerequisites & Re-enrollment."""

from __future__ import annotations

from datetime import timedelta

import pytest
from flask import Flask

from pwd301.extensions import db
from pwd301.models.course import (
    Course,
    CourseCompletionSummary,
    EnrollmentEvent,
    EnrollmentPeriod,
)
from pwd301.models.identity import Role, User
from pwd301.models.notification_audit import AuditEvent
from pwd301.models.types import utc_now
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.enrollment_service import (
    ENROLLMENT_DETAIL_RETENTION_DAYS,
    add_course_prerequisite,
    check_prerequisites_met,
    enroll_student,
    get_course_enrollments,
    get_course_prerequisites,
    get_student_enrollments,
    leave_course,
    re_enroll_student,
    remove_course_prerequisite,
)
from pwd301.services.exceptions import (
    CourseNotAvailableError,
    CourseValidationError,
    EnrollmentCapacityExceededError,
    EnrollmentPrerequisiteError,
    EnrollmentStateViolationError,
    PrerequisiteCycleError,
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
    """Create primary instructor user."""
    u = register_user("inst_enroll@example.com", "Password@123", "Enrollment Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create primary student user."""
    return register_user("stud_enroll_1@example.com", "Password@123", "Student One")


@pytest.fixture
def second_student(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create secondary student user."""
    return register_user("stud_enroll_2@example.com", "Password@123", "Student Two")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create administrator user."""
    u = register_user("admin_enroll@example.com", "Password@123", "Admin User")
    return assign_role_to_user(u.id, "ADMIN")


def _create_published_course(
    instructor: User,
    admin: User,
    code: str = "CS101",
    title: str = "Computer Science 101",
    capacity: int | None = None,
) -> Course:
    """Helper to create and publish a course."""
    data = {
        "course_code": code,
        "title": title,
        "description": "Introductory Course",
        "category": "Computer Science",
        "difficulty": "BEGINNER",
        "capacity": capacity,
    }
    course = create_course(instructor, data)
    course = change_course_status(instructor, course.id, "SUBMITTED_FOR_REVIEW")
    course = change_course_status(admin, course.id, "APPROVED")
    course = change_course_status(instructor, course.id, "PUBLISHED")
    db.session.commit()
    return course


def test_enroll_student_success_lifecycle(
    app: Flask,
    instructor_user: User,
    admin_user: User,
    student_user: User,
) -> None:
    """Verify successful initial enrollment creates Enrollment, Period 1, and Event."""
    course = _create_published_course(instructor_user, admin_user, code="CS101", title="CS 101")
    sess = db.session

    enrollment = enroll_student(actor=student_user, course_id=course.id, session=sess)
    sess.commit()

    assert enrollment.id is not None
    assert enrollment.student_user_id == student_user.id
    assert enrollment.course_id == course.id
    assert enrollment.status == "ACTIVE"
    assert float(enrollment.current_progress_percent) == 0.0
    assert enrollment.left_at is None
    assert enrollment.detail_retention_due_at is None
    assert enrollment.current_period_id is not None

    # Check period
    period = sess.get(EnrollmentPeriod, enrollment.current_period_id)
    assert period is not None
    assert period.period_no == 1
    assert period.status == "ACTIVE"
    assert period.started_at is not None
    assert period.left_at is None

    # Check event
    event = (
        sess.query(EnrollmentEvent)
        .filter_by(enrollment_id=enrollment.id, event_type="ENROLLED")
        .first()
    )
    assert event is not None
    assert event.period_id == period.id
    assert event.actor_user_id == student_user.id

    # Check first_student_enrolled_at on course
    sess.refresh(course)
    assert course.first_student_enrolled_at is not None


def test_enroll_student_unavailability(
    app: Flask,
    instructor_user: User,
    student_user: User,
) -> None:
    """Verify enrollment is rejected if course is not PUBLISHED (DRAFT, ARCHIVED, TRASH)."""
    sess = db.session

    # DRAFT Course
    draft_course = create_course(
        instructor_user,
        {"course_code": "DRAFT101", "title": "Draft Course"},
    )
    sess.commit()

    with pytest.raises(CourseNotAvailableError, match="not available for enrollment"):
        enroll_student(actor=student_user, course_id=draft_course.id, session=sess)


def test_enroll_student_already_active_raises(
    app: Flask,
    instructor_user: User,
    admin_user: User,
    student_user: User,
) -> None:
    """Verify attempting to enroll when already ACTIVE raises EnrollmentStateViolationError."""
    course = _create_published_course(instructor_user, admin_user, code="CS102", title="CS 102")
    sess = db.session

    enroll_student(actor=student_user, course_id=course.id, session=sess)
    sess.commit()

    with pytest.raises(EnrollmentStateViolationError, match="already enrolled"):
        enroll_student(actor=student_user, course_id=course.id, session=sess)


def test_enroll_student_capacity_limit(
    app: Flask,
    instructor_user: User,
    admin_user: User,
    student_user: User,
    second_student: User,
) -> None:
    """Verify enrollment capacity enforcement prevents enrolling beyond capacity limit."""
    course = _create_published_course(
        instructor_user, admin_user, code="CAP101", title="Capacity 1 Course", capacity=1
    )
    sess = db.session

    # First student enrolls successfully
    enroll_student(actor=student_user, course_id=course.id, session=sess)
    sess.commit()

    # Second student should be rejected
    with pytest.raises(
        EnrollmentCapacityExceededError, match="Course capacity of 1 has been reached"
    ):
        enroll_student(actor=second_student, course_id=course.id, session=sess)


def test_check_prerequisites_met_and_unmet(
    app: Flask,
    instructor_user: User,
    admin_user: User,
    student_user: User,
) -> None:
    """Verify check_prerequisites_met identifies satisfied vs unsatisfied prerequisites."""
    sess = db.session
    course_a = _create_published_course(instructor_user, admin_user, code="PRQ_A", title="Course A")
    course_b = _create_published_course(instructor_user, admin_user, code="PRQ_B", title="Course B")

    # Add A as prerequisite for B
    add_course_prerequisite(instructor_user, course_b.id, course_a.id, session=sess)
    sess.commit()

    # Student has not completed Course A
    eligible, missing = check_prerequisites_met(student_user.id, course_b.id, session=sess)
    assert eligible is False
    assert "Course A" in missing

    # Add durable completion summary for Course A
    summary = CourseCompletionSummary(
        student_user_id=student_user.id,
        course_id=course_a.id,
        ever_completed=True,
        prerequisite_eligible=True,
        updated_at=utc_now(),
    )
    sess.add(summary)
    sess.commit()

    eligible, missing = check_prerequisites_met(student_user.id, course_b.id, session=sess)
    assert eligible is True
    assert missing == []


def test_enroll_student_prerequisite_enforcement(
    app: Flask,
    instructor_user: User,
    admin_user: User,
    student_user: User,
) -> None:
    """Verify enroll_student blocks when prerequisite unmet and allows when met."""
    sess = db.session
    course_base = _create_published_course(
        instructor_user, admin_user, code="BASE101", title="Base Course"
    )
    course_adv = _create_published_course(
        instructor_user, admin_user, code="ADV101", title="Advanced Course"
    )

    add_course_prerequisite(instructor_user, course_adv.id, course_base.id, session=sess)
    sess.commit()

    # Rejected when prerequisite unmet
    with pytest.raises(
        EnrollmentPrerequisiteError, match="Prerequisite courses not completed: Base Course"
    ):
        enroll_student(actor=student_user, course_id=course_adv.id, session=sess)

    # Now satisfy prerequisite
    summary = CourseCompletionSummary(
        student_user_id=student_user.id,
        course_id=course_base.id,
        ever_completed=True,
        prerequisite_eligible=True,
    )
    sess.add(summary)
    sess.commit()

    # Should succeed now
    enrollment = enroll_student(actor=student_user, course_id=course_adv.id, session=sess)
    sess.commit()
    assert enrollment.status == "ACTIVE"


def test_prerequisite_dag_cycle_detection(
    app: Flask,
    instructor_user: User,
    admin_user: User,
) -> None:
    """Verify Algorithm 03 cycle detection prevents self, direct, and indirect dependency cycles."""
    sess = db.session
    course_a = _create_published_course(instructor_user, admin_user, code="DAG_A", title="Node A")
    course_b = _create_published_course(instructor_user, admin_user, code="DAG_B", title="Node B")
    course_c = _create_published_course(instructor_user, admin_user, code="DAG_C", title="Node C")

    # 1. Self-reference check: A requires A
    with pytest.raises(CourseValidationError, match="cannot be a prerequisite of itself"):
        add_course_prerequisite(instructor_user, course_a.id, course_a.id, session=sess)

    # 2. Setup A requires B
    add_course_prerequisite(instructor_user, course_a.id, course_b.id, session=sess)
    sess.commit()

    # 3. Direct cycle: B requires A (would create A -> B -> A)
    with pytest.raises(PrerequisiteCycleError, match="creates a cyclic dependency"):
        add_course_prerequisite(instructor_user, course_b.id, course_a.id, session=sess)

    # 4. Chain: B requires C (so A -> B -> C)
    add_course_prerequisite(instructor_user, course_b.id, course_c.id, session=sess)
    sess.commit()

    # 5. Indirect cycle: C requires A (would create A -> B -> C -> A)
    with pytest.raises(PrerequisiteCycleError, match="creates a cyclic dependency"):
        add_course_prerequisite(instructor_user, course_c.id, course_a.id, session=sess)


def test_remove_course_prerequisite_and_audit(
    app: Flask,
    instructor_user: User,
    admin_user: User,
) -> None:
    """Verify prerequisite removal and AuditEvent creation."""
    sess = db.session
    course_x = _create_published_course(instructor_user, admin_user, code="PRQ_X", title="Course X")
    course_y = _create_published_course(instructor_user, admin_user, code="PRQ_Y", title="Course Y")

    add_course_prerequisite(instructor_user, course_x.id, course_y.id, session=sess)
    sess.commit()

    prereqs_before = get_course_prerequisites(course_x.id, session=sess)
    assert len(prereqs_before) == 1

    removed = remove_course_prerequisite(instructor_user, course_x.id, course_y.id, session=sess)
    sess.commit()
    assert removed is True

    prereqs_after = get_course_prerequisites(course_x.id, session=sess)
    assert len(prereqs_after) == 0

    # Verify AuditEvent
    audit = (
        sess.query(AuditEvent)
        .filter_by(target_id=course_x.id, action="REMOVE_PREREQUISITE")
        .first()
    )
    assert audit is not None
    assert audit.actor_user_id == instructor_user.id


def test_leave_course_and_retention_window(
    app: Flask,
    instructor_user: User,
    admin_user: User,
    student_user: User,
) -> None:
    """Verify leave_course transitions to LEFT, calculates 30d retention, and logs event."""
    course = _create_published_course(
        instructor_user, admin_user, code="LV101", title="Leave Course"
    )
    sess = db.session

    enrollment = enroll_student(actor=student_user, course_id=course.id, session=sess)
    sess.commit()
    period_id = enrollment.current_period_id

    # Student withdraws
    before_leave = utc_now()
    left_enrollment = leave_course(
        actor=student_user,
        course_id=course.id,
        reason="Personal schedule conflict",
        session=sess,
    )
    sess.commit()

    assert left_enrollment.status == "LEFT"
    assert left_enrollment.left_at is not None
    left_at_aware = (
        left_enrollment.left_at.replace(tzinfo=before_leave.tzinfo)
        if left_enrollment.left_at.tzinfo is None
        else left_enrollment.left_at
    )
    assert left_at_aware >= before_leave - timedelta(seconds=2)
    assert left_enrollment.detail_retention_due_at is not None

    # Check that retention due at is approximately left_at + 30 days
    expected_due = left_enrollment.left_at + timedelta(days=ENROLLMENT_DETAIL_RETENTION_DAYS)
    diff = abs((left_enrollment.detail_retention_due_at - expected_due).total_seconds())
    assert diff < 2.0

    # Check period closed
    period = sess.get(EnrollmentPeriod, period_id)
    assert period is not None
    assert period.status == "LEFT"
    assert period.left_at is not None
    assert period.retention_due_at == left_enrollment.detail_retention_due_at

    # Check event
    event = (
        sess.query(EnrollmentEvent)
        .filter_by(enrollment_id=left_enrollment.id, event_type="LEFT")
        .first()
    )
    assert event is not None
    assert event.reason == "Personal schedule conflict"
    assert event.actor_user_id == student_user.id


def test_re_enroll_student_lifecycle(
    app: Flask,
    instructor_user: User,
    admin_user: User,
    student_user: User,
) -> None:
    """Verify re-enrollment reuses Enrollment, starts period 2, resets progress, and logs event."""
    course = _create_published_course(
        instructor_user, admin_user, code="RE101", title="Re-enroll Course"
    )
    sess = db.session

    # 1. First enrollment
    enrollment = enroll_student(actor=student_user, course_id=course.id, session=sess)
    original_enrollment_id = enrollment.id
    period_1_id = enrollment.current_period_id
    sess.commit()

    # 2. Student leaves
    leave_course(actor=student_user, course_id=course.id, session=sess)
    sess.commit()

    # 3. Student re-enrolls
    reenrolled = re_enroll_student(actor=student_user, course_id=course.id, session=sess)
    sess.commit()

    # Verify single logical enrollment maintained
    assert reenrolled.id == original_enrollment_id
    assert reenrolled.status == "ACTIVE"
    assert reenrolled.left_at is None
    assert reenrolled.detail_retention_due_at is None
    assert float(reenrolled.current_progress_percent) == 0.0

    # Verify new period_no = 2
    period_2_id = reenrolled.current_period_id
    assert period_2_id != period_1_id

    period_2 = sess.get(EnrollmentPeriod, period_2_id)
    assert period_2 is not None
    assert period_2.period_no == 2
    assert period_2.status == "ACTIVE"

    # Verify total 2 periods linked to this enrollment
    all_periods = sess.query(EnrollmentPeriod).filter_by(enrollment_id=original_enrollment_id).all()
    assert len(all_periods) == 2

    # Verify REENROLLED event
    re_event = (
        sess.query(EnrollmentEvent)
        .filter_by(enrollment_id=original_enrollment_id, event_type="REENROLLED")
        .first()
    )
    assert re_event is not None
    assert re_event.period_id == period_2_id


def test_get_student_enrollments_filtering(
    app: Flask,
    instructor_user: User,
    admin_user: User,
    student_user: User,
) -> None:
    """Verify get_student_enrollments returns all or filtered enrollments."""
    course_1 = _create_published_course(instructor_user, admin_user, code="F101", title="Filter 1")
    course_2 = _create_published_course(instructor_user, admin_user, code="F102", title="Filter 2")
    sess = db.session

    enroll_student(actor=student_user, course_id=course_1.id, session=sess)
    enroll_student(actor=student_user, course_id=course_2.id, session=sess)
    sess.commit()

    # Leave course 1
    leave_course(actor=student_user, course_id=course_1.id, session=sess)
    sess.commit()

    all_enr = get_student_enrollments(actor=student_user, session=sess)
    assert len(all_enr) == 2

    active_enr = get_student_enrollments(actor=student_user, status="ACTIVE", session=sess)
    assert len(active_enr) == 1
    assert active_enr[0].course_id == course_2.id

    left_enr = get_student_enrollments(actor=student_user, status="LEFT", session=sess)
    assert len(left_enr) == 1
    assert left_enr[0].course_id == course_1.id


def test_get_course_enrollments_pagination(
    app: Flask,
    instructor_user: User,
    admin_user: User,
    student_user: User,
    second_student: User,
) -> None:
    """Verify instructor can query paginated enrollments for their course."""
    course = _create_published_course(
        instructor_user, admin_user, code="PAG101", title="Pagination Course"
    )
    sess = db.session

    enroll_student(actor=student_user, course_id=course.id, session=sess)
    enroll_student(actor=second_student, course_id=course.id, session=sess)
    sess.commit()

    items, total = get_course_enrollments(
        actor=instructor_user,
        course_id=course.id,
        page=1,
        per_page=1,
        session=sess,
    )
    assert total == 2
    assert len(items) == 1
