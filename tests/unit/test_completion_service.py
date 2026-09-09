"""Unit and integration tests for Course Progress Engine and Completion Rules (TASK-009)."""

from __future__ import annotations

import pytest
from flask import Flask
from flask.testing import FlaskClient

from pwd301.extensions import db
from pwd301.models.course import (
    Course,
    CourseCompletionSummary,
    EnrollmentEvent,
    Lesson,
)
from pwd301.models.identity import Role, User
from pwd301.models.notification_audit import AuditEvent
from pwd301.services.completion_service import (
    calculate_course_progress,
    evaluate_course_completion,
    get_or_create_default_completion_rule,
    set_course_completion_rule,
)
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.enrollment_service import (
    add_course_prerequisite,
    check_prerequisites_met,
    enroll_student,
    leave_course,
)
from pwd301.services.exceptions import CompletionRuleValidationError
from pwd301.services.lesson_service import create_lesson, record_lesson_progress
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
    u = register_user("inst_comp@example.com", "Password@123", "Completion Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def other_instructor(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create secondary instructor user."""
    u = register_user("other_inst_comp@example.com", "Password@123", "Other Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create primary student user."""
    return register_user("stud_comp_1@example.com", "Password@123", "Completion Student")


@pytest.fixture
def second_student(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create secondary student user."""
    return register_user("stud_comp_2@example.com", "Password@123", "Second Student")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create administrator user."""
    u = register_user("admin_comp@example.com", "Password@123", "Completion Admin")
    return assign_role_to_user(u.id, "ADMIN")


def _create_published_course(
    instructor: User,
    admin: User,
    code: str = "COMP101",
    title: str = "Completion Course",
) -> Course:
    """Helper to create and publish a test course."""
    data = {
        "course_code": code,
        "title": title,
        "description": "Completion Test Course",
        "category": "Testing",
        "difficulty": "BEGINNER",
    }
    course = create_course(instructor, data)
    course = change_course_status(instructor, course.id, "SUBMITTED_FOR_REVIEW")
    course = change_course_status(admin, course.id, "APPROVED")
    course = change_course_status(instructor, course.id, "PUBLISHED")
    db.session.commit()
    return course


def _create_published_lesson(
    instructor: User,
    course: Course,
    title: str = "Test Lesson",
    position: int = 1,
) -> Lesson:
    """Helper to create and publish a lesson with standard completion criteria."""
    data = {
        "title": title,
        "markdown_content": "# Content for " + title,
        "position": position,
        "minimum_completion_seconds": 10,
        "viewed_fraction_required": 0.8,
        "status": "PUBLISHED",
    }
    lesson = create_lesson(instructor, course.id, data)
    db.session.commit()
    return lesson


# ==============================================================================
# Unit Tests
# ==============================================================================


def test_default_completion_rule_creation(
    app: Flask,
    instructor_user: User,
    admin_user: User,
) -> None:
    """Verify default completion rule is created with standard defaults."""
    course = _create_published_course(instructor_user, admin_user, "RULE101", "Rule Test 101")
    rule = get_or_create_default_completion_rule(course.id)

    assert rule.course_id == course.id
    assert rule.require_all_required_lessons is True
    assert rule.require_required_assessments is True
    assert float(rule.minimum_progress_percent) == 100.00


def test_set_course_completion_rule_valid(
    app: Flask,
    instructor_user: User,
    admin_user: User,
) -> None:
    """Verify managing instructor can update completion rule with AuditEvent logging."""
    course = _create_published_course(instructor_user, admin_user, "RULE102", "Rule Test 102")

    payload = {
        "require_all_required_lessons": False,
        "require_required_assessments": False,
        "minimum_progress_percent": 75.50,
        "reason": "Relaxing requirements for pilot cohort",
    }
    updated = set_course_completion_rule(instructor_user, course.id, payload)
    db.session.commit()

    assert updated.require_all_required_lessons is False
    assert updated.require_required_assessments is False
    assert float(updated.minimum_progress_percent) == 75.50
    assert updated.updated_by_user_id == instructor_user.id

    # Verify AuditEvent
    audit = (
        db.session.query(AuditEvent)
        .filter(
            AuditEvent.target_type == "COURSE_COMPLETION_RULE",
            AuditEvent.target_id == course.id,
            AuditEvent.action == "COMPLETION_RULE_UPDATED",
        )
        .first()
    )
    assert audit is not None
    assert audit.actor_user_id == instructor_user.id
    assert audit.reason == "Relaxing requirements for pilot cohort"


def test_set_course_completion_rule_invalid_percent(
    app: Flask,
    instructor_user: User,
    admin_user: User,
) -> None:
    """Verify rejection of invalid minimum_progress_percent (< 0 or > 100 or non-numeric)."""
    course = _create_published_course(instructor_user, admin_user, "RULE103", "Rule Test 103")

    with pytest.raises(CompletionRuleValidationError, match="between 0.00 and 100.00"):
        set_course_completion_rule(instructor_user, course.id, {"minimum_progress_percent": -5.0})

    with pytest.raises(CompletionRuleValidationError, match="between 0.00 and 100.00"):
        set_course_completion_rule(instructor_user, course.id, {"minimum_progress_percent": 105.0})

    with pytest.raises(CompletionRuleValidationError, match="valid numeric value"):
        set_course_completion_rule(
            instructor_user, course.id, {"minimum_progress_percent": "invalid"}
        )


def test_calculate_course_progress_empty_course(
    app: Flask,
    instructor_user: User,
    admin_user: User,
    student_user: User,
) -> None:
    """Verify that a course without published lessons yields 0.00% without ZeroDivisionError."""
    course = _create_published_course(instructor_user, admin_user, "EMPTY101", "Empty Course")
    enrollment = enroll_student(student_user, course.id)
    db.session.commit()

    progress = calculate_course_progress(enrollment.id)
    assert progress == 0.00
    assert float(enrollment.current_progress_percent) == 0.00


def test_calculate_course_progress_incremental(
    app: Flask,
    instructor_user: User,
    admin_user: User,
    student_user: User,
) -> None:
    """Verify progress increments monotonically (1/4 = 25%, 2/4 = 50%, etc.)."""
    course = _create_published_course(instructor_user, admin_user, "PROG101", "Progress Course")
    l1 = _create_published_lesson(instructor_user, course, "Lesson 1", 1)
    l2 = _create_published_lesson(instructor_user, course, "Lesson 2", 2)
    l3 = _create_published_lesson(instructor_user, course, "Lesson 3", 3)
    l4 = _create_published_lesson(instructor_user, course, "Lesson 4", 4)

    enrollment = enroll_student(student_user, course.id)
    db.session.commit()

    # Initial progress: 0.0%
    assert calculate_course_progress(enrollment.id) == 0.00

    # Complete Lesson 1 -> 25.0%
    record_lesson_progress(student_user, l1.id, seconds_increment=15, view_fraction=0.9)
    db.session.commit()
    db.session.refresh(enrollment)
    assert float(enrollment.current_progress_percent) == 25.00

    # Complete Lesson 2 -> 50.0%
    record_lesson_progress(student_user, l2.id, seconds_increment=15, view_fraction=0.9)
    db.session.commit()
    db.session.refresh(enrollment)
    assert float(enrollment.current_progress_percent) == 50.00

    # Complete Lesson 3 -> 75.0%
    record_lesson_progress(student_user, l3.id, seconds_increment=15, view_fraction=0.9)
    db.session.commit()
    db.session.refresh(enrollment)
    assert float(enrollment.current_progress_percent) == 75.00

    # Complete Lesson 4 -> 100.0%
    record_lesson_progress(student_user, l4.id, seconds_increment=15, view_fraction=0.9)
    db.session.commit()
    db.session.refresh(enrollment)
    assert float(enrollment.current_progress_percent) == 100.00


def test_calculate_course_progress_ignores_other_periods(
    app: Flask,
    instructor_user: User,
    admin_user: User,
    student_user: User,
) -> None:
    """Verify progress calculation only counts completions in the student's current period."""
    course = _create_published_course(instructor_user, admin_user, "PER101", "Period Course")
    l1 = _create_published_lesson(instructor_user, course, "Lesson 1", 1)
    _create_published_lesson(instructor_user, course, "Lesson 2", 2)

    enrollment = enroll_student(student_user, course.id)
    db.session.commit()

    # Complete lesson 1 in period 1
    record_lesson_progress(student_user, l1.id, seconds_increment=15, view_fraction=0.9)
    db.session.commit()
    assert calculate_course_progress(enrollment.id) == 50.00

    # Student leaves and re-enrolls -> opens Period 2
    leave_course(student_user, course.id)
    db.session.commit()

    from pwd301.services.enrollment_service import re_enroll_student

    enrollment = re_enroll_student(student_user, course.id)
    db.session.commit()

    # In period 2, progress resets to 0.0% (does not count lesson 1 completed in period 1)
    assert calculate_course_progress(enrollment.id) == 0.00
    assert float(enrollment.current_progress_percent) == 0.00


def test_evaluate_course_completion_success(
    app: Flask,
    instructor_user: User,
    admin_user: User,
    student_user: User,
) -> None:
    """Verify full completion marks Enrollment COMPLETED and upserts CourseCompletionSummary."""
    course = _create_published_course(instructor_user, admin_user, "EVAL101", "Eval Course 101")
    l1 = _create_published_lesson(instructor_user, course, "L1", 1)

    enrollment = enroll_student(student_user, course.id)
    db.session.commit()

    # Complete lesson
    record_lesson_progress(student_user, l1.id, seconds_increment=15, view_fraction=0.9)
    db.session.commit()

    # Evaluate completion
    completed, summary = evaluate_course_completion(enrollment.id)
    db.session.commit()

    assert completed is True
    assert summary is not None
    assert summary.ever_completed is True
    assert summary.prerequisite_eligible is True
    assert summary.first_completed_at is not None
    assert summary.latest_completed_at is not None

    db.session.refresh(enrollment)
    assert enrollment.status == "COMPLETED"
    assert enrollment.completed_at is not None

    period = enrollment.current_period
    assert period is not None
    assert period.status == "COMPLETED"
    assert period.completed_at is not None

    # Verify EnrollmentEvent(event_type='COMPLETED')
    event = (
        db.session.query(EnrollmentEvent)
        .filter(
            EnrollmentEvent.enrollment_id == enrollment.id,
            EnrollmentEvent.event_type == "COMPLETED",
        )
        .first()
    )
    assert event is not None

    # Verify AuditEvent(action='COURSE_COMPLETED')
    audit = (
        db.session.query(AuditEvent)
        .filter(
            AuditEvent.target_type == "COURSE",
            AuditEvent.target_id == course.id,
            AuditEvent.action == "COURSE_COMPLETED",
        )
        .first()
    )
    assert audit is not None


def test_evaluate_course_completion_not_yet_met(
    app: Flask,
    instructor_user: User,
    admin_user: User,
    student_user: User,
) -> None:
    """Verify completion is False when required lessons or progress threshold remain incomplete."""
    course = _create_published_course(instructor_user, admin_user, "EVAL102", "Eval Course 102")
    l1 = _create_published_lesson(instructor_user, course, "L1", 1)
    _create_published_lesson(instructor_user, course, "L2", 2)

    enrollment = enroll_student(student_user, course.id)
    db.session.commit()

    # Complete only 1 of 2 lessons
    record_lesson_progress(student_user, l1.id, seconds_increment=15, view_fraction=0.9)
    db.session.commit()

    completed, summary = evaluate_course_completion(enrollment.id)
    assert completed is False

    db.session.refresh(enrollment)
    assert enrollment.status == "ACTIVE"


def test_evaluate_course_completion_idempotent(
    app: Flask,
    instructor_user: User,
    admin_user: User,
    student_user: User,
) -> None:
    """Verify repeated evaluate_course_completion calls return (True, summary)
    without duplicate events.
    """
    course = _create_published_course(instructor_user, admin_user, "IDEM101", "Idempotent Course")
    l1 = _create_published_lesson(instructor_user, course, "L1", 1)

    enrollment = enroll_student(student_user, course.id)
    db.session.commit()

    record_lesson_progress(student_user, l1.id, seconds_increment=15, view_fraction=0.9)
    db.session.commit()

    c1, s1 = evaluate_course_completion(enrollment.id)
    db.session.commit()
    assert c1 is True

    # Count events
    event_count_1 = (
        db.session.query(EnrollmentEvent)
        .filter(
            EnrollmentEvent.enrollment_id == enrollment.id,
            EnrollmentEvent.event_type == "COMPLETED",
        )
        .count()
    )

    # Call again
    c2, s2 = evaluate_course_completion(enrollment.id)
    db.session.commit()
    assert c2 is True
    assert s1.id == s2.id

    event_count_2 = (
        db.session.query(EnrollmentEvent)
        .filter(
            EnrollmentEvent.enrollment_id == enrollment.id,
            EnrollmentEvent.event_type == "COMPLETED",
        )
        .count()
    )
    assert event_count_1 == event_count_2 == 1


def test_durable_prerequisite_eligibility(
    app: Flask,
    instructor_user: User,
    admin_user: User,
    student_user: User,
) -> None:
    """Verify that CourseCompletionSummary retains prerequisite_eligible=True
    permanently even after student leaves.
    """
    course_a = _create_published_course(instructor_user, admin_user, "DUR101", "Durable Course A")
    l1 = _create_published_lesson(instructor_user, course_a, "L1", 1)

    enrollment = enroll_student(student_user, course_a.id)
    db.session.commit()

    # Complete Course A
    record_lesson_progress(student_user, l1.id, seconds_increment=15, view_fraction=0.9)
    db.session.commit()

    db.session.refresh(enrollment)
    assert enrollment.status == "COMPLETED"

    summary = (
        db.session.query(CourseCompletionSummary)
        .filter(
            CourseCompletionSummary.student_user_id == student_user.id,
            CourseCompletionSummary.course_id == course_a.id,
        )
        .first()
    )
    assert summary is not None
    assert summary.prerequisite_eligible is True
    assert summary.ever_completed is True

    # Student re-enrolls then withdraws/leaves Course A
    enroll_student(student_user, course_a.id)
    leave_course(student_user, course_a.id)
    db.session.commit()

    db.session.refresh(enrollment)
    assert enrollment.status == "LEFT"

    # Durable summary is preserved!
    db.session.refresh(summary)
    assert summary.prerequisite_eligible is True
    assert summary.ever_completed is True


# ==============================================================================
# Integration / Hook Tests
# ==============================================================================


def test_lesson_heartbeat_triggers_auto_completion(
    app: Flask,
    instructor_user: User,
    admin_user: User,
    student_user: User,
) -> None:
    """Verify that completing the last lesson via record_lesson_progress
    immediately triggers course completion.
    """
    course = _create_published_course(instructor_user, admin_user, "HOOK101", "Hook Course")
    l1 = _create_published_lesson(instructor_user, course, "L1", 1)

    enrollment = enroll_student(student_user, course.id)
    db.session.commit()

    assert enrollment.status == "ACTIVE"
    assert float(enrollment.current_progress_percent) == 0.00

    # Ping lesson heartbeat to completion threshold
    progress = record_lesson_progress(student_user, l1.id, seconds_increment=15, view_fraction=0.9)
    db.session.commit()

    assert progress.completed_at is not None

    # Enrollment and Period automatically marked COMPLETED!
    db.session.refresh(enrollment)
    assert enrollment.status == "COMPLETED"
    assert float(enrollment.current_progress_percent) == 100.00

    summary = (
        db.session.query(CourseCompletionSummary)
        .filter(
            CourseCompletionSummary.student_user_id == student_user.id,
            CourseCompletionSummary.course_id == course.id,
        )
        .first()
    )
    assert summary is not None
    assert summary.prerequisite_eligible is True


def test_enrollment_prerequisite_honors_durable_summary(
    app: Flask,
    instructor_user: User,
    admin_user: User,
    student_user: User,
) -> None:
    """Verify student who completed course A and then left can enroll in Course B requiring A."""
    course_a = _create_published_course(instructor_user, admin_user, "PREREQ101", "Prereq Course A")
    course_b = _create_published_course(instructor_user, admin_user, "ADV201", "Advanced Course B")

    # Set Course A as prerequisite for Course B
    add_course_prerequisite(instructor_user, course_b.id, course_a.id)
    db.session.commit()

    l1 = _create_published_lesson(instructor_user, course_a, "L1", 1)

    # Student enrolls and completes Course A
    enroll_student(student_user, course_a.id)
    record_lesson_progress(student_user, l1.id, seconds_increment=15, view_fraction=0.9)
    db.session.commit()

    # Student re-enrolls in Course A then withdraws/leaves
    enroll_student(student_user, course_a.id)
    leave_course(student_user, course_a.id)
    db.session.commit()

    # Prerequisite check for Course B passes because
    # CourseCompletionSummary.prerequisite_eligible is True
    is_met, missing = check_prerequisites_met(student_user.id, course_b.id)
    assert is_met is True
    assert missing == []

    # Student successfully enrolls in Course B!
    enrollment_b = enroll_student(student_user, course_b.id)
    db.session.commit()
    assert enrollment_b.status == "ACTIVE"


def test_web_instructor_completion_rules_routes(
    client: FlaskClient,
    instructor_user: User,
    admin_user: User,
) -> None:
    """Verify Web UI routes for instructor completion rules."""
    course = _create_published_course(instructor_user, admin_user, "WEB101", "Web Course 101")
    with client.session_transaction() as sess:
        sess["_user_id"] = str(instructor_user.id)
        sess["auth_source"] = "SESSION"

    # GET
    resp = client.get(f"/instructor/courses/{course.public_id}/completion-rules")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["course_id"] == str(course.public_id)
    assert data["minimum_progress_percent"] == 100.0

    # POST
    resp_post = client.post(
        f"/instructor/courses/{course.public_id}/completion-rules",
        json={"minimum_progress_percent": 90.0, "require_all_required_lessons": True},
    )
    assert resp_post.status_code == 200
    data_post = resp_post.get_json()
    assert data_post["minimum_progress_percent"] == 90.0


def test_web_student_course_completion_route(
    client: FlaskClient,
    instructor_user: User,
    admin_user: User,
    student_user: User,
) -> None:
    """Verify Web UI route for student course completion status."""
    course = _create_published_course(instructor_user, admin_user, "WEB102", "Web Course 102")
    enroll_student(student_user, course.id)
    db.session.commit()

    with client.session_transaction() as sess:
        sess["_user_id"] = str(student_user.id)
        sess["auth_source"] = "SESSION"

    resp = client.get(f"/student/courses/{course.public_id}/completion")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["course_id"] == str(course.public_id)
    assert data["student_id"] == str(student_user.public_id)
    assert data["ever_completed"] is False
    assert data["current_status"] == "ACTIVE"
